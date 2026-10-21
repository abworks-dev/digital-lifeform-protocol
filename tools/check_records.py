#!/usr/bin/env python3
"""Read-only, explicitly scoped checks for RECORDS.md's experimental MC01–MC07.

Python 3.11+, standard library only. This is NOT a YAML or Markdown implementation.
Frontmatter supports flat text scalars, quoted text, comments, and links lists.
Unsupported constructs are reported, never evaluated or treated as fully checked.
Only explicitly supplied files are opened; references do not expand the scope.
"""
from __future__ import annotations

import sys

sys.dont_write_bytecode = True

import argparse
from collections import Counter, defaultdict
from datetime import date
import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import stat
import unicodedata
from urllib.parse import unquote, urlsplit

VERSION = "0.1.0"
TYPES = {"profile", "identity", "project", "account", "delegation", "decision", "review"}
STATUSES = {"draft", "confirmed", "retired"}
REQUIRED = ("id", "type", "title", "status", "source", "updated", "links")
LIMITATIONS = [
    "Only explicitly listed files are read; no discovery, recursion, reference following, or network access.",
    "Frontmatter is a restricted flat text-scalar/list subset, not general YAML; plain null/~ are empty, while booleans/numbers are text without YAML type inference; unsupported syntax is unchecked.",
    "Markdown support is limited to simple inline links, angle destinations, ATX/setext headings and simple slugs; unsupported syntax is unchecked.",
    "Body semantics, factual accuracy, real consent, authorization, privacy, and external operations are not checked.",
    "ID uniqueness is limited to the listed record set; closed_set affects only missing record-ID references.",
    "Templates are placeholders, not actual records; document/Skill frontmatter is not record metadata.",
    "Path checks reject observed symlinks/reparse points but are not an OS sandbox against concurrent filesystem replacement.",
]
MESSAGES = {
    "empty_scope": "No explicit input files were supplied.",
    "invalid_root": "The root must be an existing readable directory without link components.",
    "invalid_path": "Input must be a nonempty root-relative path without parent traversal.",
    "path_link": "A symbolic link or filesystem reparse point is not an authorized input.",
    "path_outside": "The input cannot be resolved inside the supplied root.",
    "missing_path": "The explicitly listed input does not exist.",
    "not_file": "The explicitly listed input is not a regular file.",
    "read_failed": "The explicitly listed input could not be read as UTF-8 text.",
    "conflicting_kind": "The same input was assigned more than one input kind.",
    "path_alias": "Multiple explicit paths identify the same physical input; the alias was not counted twice.",
    "missing_frontmatter": "Record frontmatter must begin on the first line.",
    "unterminated_frontmatter": "The frontmatter closing delimiter is missing.",
    "duplicate_key": "A frontmatter key occurs more than once.",
    "unsupported_syntax": "Frontmatter syntax is outside the supported flat text-scalar/list subset.",
    "missing_field": "A required public field is missing.",
    "empty_field": "A public field is empty rather than explicitly known or unknown.",
    "unknown_field": "A public field is explicitly unknown and requires human review.",
    "invalid_id": "The record ID must be a nonempty known text scalar.",
    "duplicate_id": "The record ID is duplicated within the explicitly listed record set.",
    "invalid_type": "The record type is not one of the seven supported public types.",
    "invalid_status": "The record status is not draft, confirmed, or retired.",
    "missing_confirmation": "A confirmed record requires this confirmation field.",
    "invalid_confirmer": "A confirmed record requires a nonempty known confirmation subject.",
    "invalid_confirmation_date": "A confirmed record requires a valid known YYYY-MM-DD confirmation date.",
    "public_confirmer": "A confirmed public example must use the fictional confirmation subject.",
    "invalid_date": "The populated date must be a valid calendar date in YYYY-MM-DD form.",
    "unknown_date": "The date is explicitly unknown and has not been validated as a date.",
    "invalid_links": "Links must be an inline or block list of known nonempty text IDs, or an empty list.",
    "invalid_link": "A links entry must be a nonempty known text ID.",
    "ambiguous_target": "A referenced ID has multiple targets in the listed record set.",
    "missing_target": "A referenced ID is absent from the declared closed record set.",
    "out_of_scope": "The reference target is outside the explicit readable input set and was not inspected.",
    "external_target": "An external target was not accessed or checked.",
    "invalid_target": "The local navigation target cannot be safely checked as a scoped relative path.",
    "missing_anchor": "The anchor is absent from the supported headings in the explicitly listed target.",
    "unsupported_markdown": "Markdown syntax is outside the supported simple navigation/heading subset.",
    "placeholder": "Template metadata is a placeholder and is not counted as an actual record.",
}


def _diag(report: dict, file: str, line: int, rule: str, code: str,
          level: str = "error") -> None:
    item = {"file": file, "line": line, "rule": rule, "code": code,
            "level": level, "message": MESSAGES[code]}
    if item not in report["diagnostics"]:
        report["diagnostics"].append(item)


def _relative(raw: object) -> str | None:
    if not isinstance(raw, str) or not raw or "\x00" in raw:
        return None
    text = raw.replace("\\", "/")
    win = PureWindowsPath(text)
    path = PurePosixPath(text)
    if win.drive or win.root or path.is_absolute() or ".." in path.parts:
        return None
    if not path.parts or any(":" in part for part in path.parts):
        return None
    return path.as_posix()


def _linked(path: Path) -> bool:
    info = path.lstat()
    return stat.S_ISLNK(info.st_mode) or bool(getattr(info, "st_file_attributes", 0) & 0x400)


def _root_path(root: Path) -> Path | None:
    try:
        absolute = Path(os.path.abspath(root))
        for component in reversed((absolute, *absolute.parents)):
            if _linked(component):
                return None
        return absolute if absolute.is_dir() else None
    except (OSError, ValueError, TypeError):
        return None


def _input_path(root: Path, rel: str) -> tuple[Path | None, str | None]:
    current = root
    try:
        for component in PurePosixPath(rel).parts:
            current = current / component
            if _linked(current):
                return None, "path_link"
        if not current.resolve().is_relative_to(root.resolve()):
            return None, "path_outside"
        if not stat.S_ISREG(current.stat().st_mode):
            return None, "not_file"
        return current, None
    except FileNotFoundError:
        return None, "missing_path"
    except (OSError, ValueError):
        return None, "read_failed"


def _comment(text: str) -> str:
    """Remove whitespace-led comments, respecting the two supported quote forms."""
    quote = None
    index = 0
    while index < len(text):
        char = text[index]
        if quote == '"' and char == "\\":
            index += 2
            continue
        if quote == "'" and text[index:index + 2] == "''":
            index += 2
            continue
        if quote:
            if char == quote:
                quote = None
        elif char in "'\"":
            quote = char
        elif char == "#" and (index == 0 or text[index - 1].isspace()):
            return text[:index].rstrip()
        index += 1
    return text.rstrip()


class Unsupported(ValueError):
    """A construct cannot be interpreted by the documented safe subset."""


def _scalar(raw: str) -> str | None:
    text = _comment(raw).strip()
    if not text or text in ("null", "Null", "NULL", "~"):
        return None
    if text.startswith('"'):
        try:
            # JSON's quoted-string escapes are an explicit subset of YAML's.
            value = json.loads(text)
        except (ValueError, RecursionError) as exc:
            raise Unsupported from exc
        if not isinstance(value, str):
            raise Unsupported
        return value
    if text.startswith("'"):
        if len(text) < 2 or not text.endswith("'"):
            raise Unsupported
        middle = text[1:-1]
        if "'" in middle.replace("''", ""):
            raise Unsupported
        return middle.replace("''", "'")
    if text[0] in "[]{}&*!|>@`%\"" or text in ("---", "..."):
        raise Unsupported
    if text.startswith(("- ", "? ", ": ")) or re.search(r":\s", text):
        raise Unsupported
    # No YAML implicit typing: all accepted scalars are text, including dates/IDs.
    return text


def _inline_list(raw: str) -> list[str]:
    text = _comment(raw).strip()
    if not text.startswith("[") or not text.endswith("]"):
        raise Unsupported
    inner = text[1:-1]
    if not inner.strip():
        return []
    parts, start, quote, index = [], 0, None, 0
    while index < len(inner):
        char = inner[index]
        if quote == '"' and char == "\\":
            index += 2
            continue
        if quote == "'" and inner[index:index + 2] == "''":
            index += 2
            continue
        if quote:
            if char == quote:
                quote = None
        elif char in "'\"":
            quote = char
        elif char in "[]{}":
            raise Unsupported
        elif char == ",":
            parts.append(inner[start:index])
            start = index + 1
        index += 1
    if quote:
        raise Unsupported
    parts.append(inner[start:])
    if not parts[-1].strip() and len(parts) > 1:
        parts.pop()  # A single trailing comma is supported.
    if any(not part.strip() for part in parts):
        raise Unsupported
    return [_scalar(part) for part in parts]


def _frontmatter(lines: list[str], file: str, report: dict) -> tuple[dict, dict, int, bool]:
    values, positions = {}, {}
    if not lines or lines[0].lstrip("\ufeff").strip() != "---":
        _diag(report, file, 1, "PARSE", "missing_frontmatter", "unchecked")
        return values, positions, 0, False
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    if end is None:
        _diag(report, file, 1, "PARSE", "unterminated_frontmatter", "unchecked")
        return values, positions, len(lines), False
    complete, current, list_indent = True, None, None
    for index in range(1, end):
        raw, lineno = lines[index], index + 1
        clean = _comment(raw)
        if not clean.strip():
            continue
        pair = re.fullmatch(r"([A-Za-z_][A-Za-z0-9_-]*):(?:[ \t]+(.*)|())", clean)
        if pair:
            key, value = pair.group(1), pair.group(2) or ""
            current, list_indent = None, None
            if key in positions:
                _diag(report, file, lineno, "PARSE", "duplicate_key")
                complete = False
                continue
            positions[key] = lineno
            try:
                if key == "links":
                    if not value.strip():
                        values[key] = None
                        current = key
                    elif value.lstrip().startswith("["):
                        values[key] = _inline_list(value)
                    else:
                        values[key] = _scalar(value)
                else:
                    values[key] = _scalar(value)
            except Unsupported:
                _diag(report, file, lineno, "PARSE", "unsupported_syntax", "unchecked")
                complete = False
            continue
        item = re.fullmatch(r"( *)- (.*)", clean)
        if current == "links" and item:
            indent = len(item.group(1))
            if list_indent is None:
                list_indent = indent
            try:
                if indent != list_indent:
                    raise Unsupported
                value = _scalar(item.group(2))
                if values["links"] is None:
                    values["links"] = []
                values["links"].append(value)
            except Unsupported:
                _diag(report, file, lineno, "PARSE", "unsupported_syntax", "unchecked")
                complete = False
            continue
        _diag(report, file, lineno, "PARSE", "unsupported_syntax", "unchecked")
        complete, current = False, None
    return values, positions, end + 1, complete


def _known(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip()) and value.strip() != "unknown"


def _date(value: object) -> bool:
    if not isinstance(value, str) or not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value):
        return False
    try:
        date.fromisoformat(value)
        return True
    except ValueError:
        return False


def _record(file: str, values: dict, positions: dict, complete: bool,
            report: dict, public: bool) -> None:
    required = REQUIRED + (("confirmed_by", "confirmed_at") if values.get("status") == "confirmed" else ())
    for key in required:
        line = positions.get(key, 1)
        if key not in positions:
            if complete:
                _diag(report, file, line, "MC01", "missing_field")
        elif key not in values:
            continue  # The parser has already marked an unsupported field.
        elif values[key] is None or values[key] == "":
            _diag(report, file, line, "MC01", "empty_field")
        elif values[key] == "unknown":
            _diag(report, file, line, "MC01", "unknown_field", "warning")
    if "id" in values and not _known(values["id"]):
        _diag(report, file, positions["id"], "MC02", "invalid_id")
    for key, choices, code in (("type", TYPES, "invalid_type"), ("status", STATUSES, "invalid_status")):
        if key in values and values[key] not in choices:
            _diag(report, file, positions[key], "MC03", code)
    confirmed = values.get("status") == "confirmed"
    if confirmed:
        for key in ("confirmed_by", "confirmed_at"):
            if key not in positions and complete:
                _diag(report, file, 1, "MC04", "missing_confirmation")
        if "confirmed_by" in values:
            if not _known(values["confirmed_by"]):
                _diag(report, file, positions["confirmed_by"], "MC04", "invalid_confirmer")
            elif public and values["confirmed_by"] != "fictional-user":
                _diag(report, file, positions["confirmed_by"], "MC04", "public_confirmer")
        if "confirmed_at" in values and not _date(values["confirmed_at"]):
            _diag(report, file, positions["confirmed_at"], "MC04", "invalid_confirmation_date")
    for key in ("updated", "confirmed_at"):
        if key not in values:
            continue
        value, line = values[key], positions[key]
        if value == "unknown":
            if key != "confirmed_at" or not confirmed:
                _diag(report, file, line, "MC05", "unknown_date", "warning")
        elif key == "confirmed_at" and (value is None or value == "") and not confirmed:
            continue  # An optional, unfilled confirmation field.
        elif not _date(value):
            _diag(report, file, line, "MC05", "invalid_date")
    if "links" in values:
        links, line = values["links"], positions["links"]
        if not isinstance(links, list):
            _diag(report, file, line, "MC06", "invalid_links")
        else:
            for target in links:
                if not _known(target):
                    _diag(report, file, line, "MC06", "invalid_link")


def _body(lines: list[str], start: int, file: str | None = None,
          report: dict | None = None) -> list[tuple[int, str]]:
    """Skip fences; flag potentially navigable indentation whose context is ambiguous."""
    result, fence = [], None
    for index in range(start, len(lines)):
        text = lines[index]
        opening = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)$", text)
        if fence:
            if re.fullmatch(r" {0,3}" + re.escape(fence[0]) + "{" + str(fence[1]) + r",}\s*", text):
                fence = None
            continue
        if opening:
            fence = (opening.group(1)[0], len(opening.group(1)))
            continue
        # Indented code versus a nested list requires a fuller Markdown parser.
        if text.startswith(("    ", "\t")):
            if report is not None and any(char in text for char in "[]<>"):
                _diag(report, file, index + 1, "MC07", "unsupported_markdown", "unchecked")
            continue
        result.append((index + 1, text))
    return result


def _slug(text: str) -> str:
    text = re.sub(r"\s+#+\s*$", "", text.strip()).lower()
    text = text.replace("*", "").replace("`", "")
    text = "".join(char for char in text
                   if char in "-_" or not unicodedata.category(char).startswith(("P", "S", "C")))
    return re.sub(r"\s", "-", text)


def _headings(body: list[tuple[int, str]]) -> tuple[set[str], bool]:
    anchors, counts, complex_heading = set(), defaultdict(int), False
    for index, (_, text) in enumerate(body):
        match = re.match(r"^ {0,3}#{1,6}\s+(.*)$", text)
        heading = match.group(1) if match else None
        if heading is None and index + 1 < len(body):
            next_line, next_text = body[index + 1]
            if next_line == body[index][0] + 1 and re.fullmatch(r" {0,3}(?:=+|-+)\s*", next_text) and text.strip():
                heading = text.strip()
        if heading is None:
            continue
        if any(char in heading for char in "[]<>&\\"):
            complex_heading = True
            continue
        slug = _slug(heading)
        candidate, suffix = slug, counts[slug]
        if suffix:
            candidate = f"{slug}-{suffix}"
        while candidate in anchors:
            suffix += 1
            candidate = f"{slug}-{suffix}"
        counts[slug] = suffix + 1
        anchors.add(candidate)
    return anchors, complex_heading


def _navigation_target(file: str, line: int, target: str, loaded: dict,
                       headings: dict, report: dict) -> None:
    if target.startswith("//") or re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", target):
        _diag(report, file, line, "MC07", "external_target", "unchecked")
        return
    try:
        parsed = urlsplit(target)
        if parsed.query:
            raise ValueError
        path, anchor = unquote(parsed.path), unquote(parsed.fragment)
        if "\x00" in path or "\\" in path or path.startswith("/") or PureWindowsPath(path).drive:
            raise ValueError
        pieces = list(PurePosixPath(file).parent.parts)
        if path:
            for part in path.split("/"):
                if part in ("", "."):
                    continue
                if part == "..":
                    if not pieces:
                        raise ValueError
                    pieces.pop()
                else:
                    if ":" in part:
                        raise ValueError
                    pieces.append(part)
            dest = "/".join(pieces)
        else:
            dest = file
    except ValueError:
        _diag(report, file, line, "MC07", "invalid_target", "unchecked")
        return
    # Deliberately no exists/stat/open here: even target existence is scoped.
    if dest not in loaded:
        _diag(report, file, line, "MC07", "out_of_scope", "unchecked")
        return
    if anchor:
        anchors, complex_heading = headings[dest]
        if anchor not in anchors:
            code = "unsupported_markdown" if complex_heading else "missing_anchor"
            _diag(report, file, line, "MC07", code, "unchecked" if complex_heading else "error")


def _navigation(file: str, body: list[tuple[int, str]], loaded: dict,
                headings: dict, report: dict) -> None:
    inline = re.compile(r"(?<!!)\[([^\[\]\n]*)\]\((<[^<>\n]*>|[^\s()<>]*)\)")
    angle = re.compile(r"<([^<>\s]+)>")
    for line, text in body:
        text = re.sub(r"(`+)(.*?)\1", lambda m: " " * len(m.group(0)), text)
        text = re.sub(r"\\[\\`*{}\[\]()#+.!_<>]", " ", text)
        def replace(match: re.Match) -> str:
            dest = match.group(2)
            if dest.startswith("<"):
                dest = dest[1:-1]
            _navigation_target(file, line, dest, loaded, headings, report)
            return " " * len(match.group(0))
        remaining = inline.sub(replace, text)
        def replace_angle(match: re.Match) -> str:
            dest = match.group(1)
            if re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", dest) or "@" in dest:
                _diag(report, file, line, "MC07", "external_target", "unchecked")
                return " " * len(match.group(0))
            if dest.startswith("#") or ".md" in dest.lower() or "/" in dest:
                _navigation_target(file, line, dest, loaded, headings, report)
                return " " * len(match.group(0))
            return match.group(0)
        remaining = angle.sub(replace_angle, remaining)
        if "[" in remaining or "]" in remaining or re.search(r"<\s*/?[A-Za-z][^>]*>", remaining):
            _diag(report, file, line, "MC07", "unsupported_markdown", "unchecked")


def check(root: Path, records: list[str], templates: list[str], documents: list[str],
          closed_set: bool = False, public_examples: bool = False,
          baseline: str = "unknown") -> dict:
    """Return a deterministic, redacted report; never write or widen input scope."""
    report = {"checker": {"name": "check_records", "version": VERSION},
              "baseline": baseline, "scope": [], "closed_set": bool(closed_set),
              "summary": {"error": 0, "warning": 0, "unchecked": 0},
              "diagnostics": [], "limitations": list(LIMITATIONS)}
    inputs, conflicts = {}, set()
    invalid_record_input = False
    for kind, paths in (("record", records), ("template", templates), ("document", documents)):
        for raw in paths:
            rel = _relative(raw)
            if rel is None:
                invalid_record_input |= kind == "record"
                _diag(report, "<input>", 0, "INPUT", "invalid_path", "unchecked")
                continue
            if rel in inputs and inputs[rel] != kind:
                conflicts.add(rel)
                _diag(report, rel, 0, "INPUT", "conflicting_kind", "unchecked")
            else:
                inputs[rel] = kind
    report["scope"] = [{"file": file, "kind": kind} for file, kind in sorted(inputs.items())]
    if not report["scope"]:
        _diag(report, "<scope>", 0, "INPUT", "empty_scope", "unchecked")
    root_path = _root_path(root)
    if root_path is None:
        _diag(report, "<root>", 0, "INPUT", "invalid_root", "unchecked")
    loaded, metadata, headings = {}, {}, {}
    reliable_records, physical_inputs = set(), {}
    for file, kind in sorted(inputs.items()):
        if root_path is None or file in conflicts:
            continue
        path, problem = _input_path(root_path, file)
        if problem:
            _diag(report, file, 0, "INPUT", problem, "unchecked")
            continue
        try:
            # O_NOFOLLOW protects the final component where the platform supports it.
            fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
            with os.fdopen(fd, "r", encoding="utf-8-sig") as stream:
                info = os.fstat(stream.fileno())
                identity = (info.st_dev, info.st_ino) if info.st_ino else os.path.normcase(str(path.resolve()))
                if identity in physical_inputs:
                    _diag(report, file, 0, "INPUT", "path_alias", "unchecked")
                    continue
                physical_inputs[identity] = file
                lines = stream.read().splitlines()
        except (OSError, UnicodeError, ValueError):
            _diag(report, file, 0, "INPUT", "read_failed", "unchecked")
            continue
        start = 0
        if kind in ("record", "template"):
            values, positions, start, complete = _frontmatter(lines, file, report)
            if kind == "record":
                metadata[file] = (values, positions)
                if complete and _known(values.get("id")):
                    reliable_records.add(file)
                _record(file, values, positions, complete, report, public_examples)
            else:
                _diag(report, file, 1, "MC01", "placeholder", "warning")
        elif lines and lines[0].strip() == "---":
            closing = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
            if closing is None:
                _diag(report, file, 1, "MC07", "unsupported_markdown", "unchecked")
                start = len(lines)
            else:
                start = closing + 1
        body = _body(lines, start, file, report)
        loaded[file] = body
        headings[file] = _headings(body)
        if headings[file][1]:
            _diag(report, file, 1, "MC07", "unsupported_markdown", "unchecked")
    ids = defaultdict(list)
    for file, (values, positions) in metadata.items():
        if _known(values.get("id")):
            ids[values["id"]].append(file)
    for files in ids.values():
        if len(files) > 1:
            for file in files:
                _diag(report, file, metadata[file][1]["id"], "MC02", "duplicate_id")
    closed_visible = (closed_set and not invalid_record_input
                      and all(file in reliable_records for file, kind in inputs.items() if kind == "record"))
    for file, (values, positions) in metadata.items():
        if isinstance(values.get("links"), list):
            for target in values["links"]:
                if not _known(target):
                    continue
                matches = ids.get(target, [])
                if len(matches) > 1:
                    _diag(report, file, positions["links"], "MC06", "ambiguous_target")
                elif not matches:
                    _diag(report, file, positions["links"], "MC06",
                          "missing_target" if closed_visible else "out_of_scope",
                          "error" if closed_visible else "unchecked")
    for file, body in loaded.items():
        _navigation(file, body, loaded, headings, report)
    report["diagnostics"].sort(key=lambda item: (item["file"], item["line"], item["rule"], item["code"]))
    counts = Counter(item["level"] for item in report["diagnostics"])
    report["summary"] = {level: counts[level] for level in ("error", "warning", "unchecked")}
    return report


def exit_code(report: dict) -> int:
    """Errors take precedence over incomplete checking; warnings alone pass."""
    if report["summary"]["error"]:
        return 1
    return 2 if report["summary"]["unchecked"] else 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path, help="Explicit root; never auto-scanned.")
    parser.add_argument("--record", action="append", default=[], metavar="RELPATH")
    parser.add_argument("--template", action="append", default=[], metavar="RELPATH")
    parser.add_argument("--document", action="append", default=[], metavar="RELPATH")
    parser.add_argument("--closed-set", action="store_true", help="Declare only the record-ID reference set closed.")
    parser.add_argument("--public-examples", action="store_true")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--baseline", default="unknown", help="User-supplied baseline label; not verified.")
    args = parser.parse_args(argv)
    report = check(args.root, args.record, args.template, args.document,
                   args.closed_set, args.public_examples, args.baseline)
    if args.format == "json":
        print(json.dumps(report, ensure_ascii=True, indent=2))
    else:
        print(f"check_records {VERSION}; baseline: " + json.dumps(report["baseline"], ensure_ascii=True))
        print(f"closed_set: {str(report['closed_set']).lower()}")
        for item in report["scope"]:
            print("scope: " + json.dumps(item, ensure_ascii=True, sort_keys=True))
        for item in report["diagnostics"]:
            print(json.dumps(item, ensure_ascii=True, sort_keys=True))
        print("summary: " + json.dumps(report["summary"], sort_keys=True))
        for limitation in report["limitations"]:
            print("limitation: " + limitation)
    return exit_code(report)


if __name__ == "__main__":
    raise SystemExit(main())
