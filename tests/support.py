"""Test-only helpers. No installation, network, private paths or production writes."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("dlp_check_records", ROOT / "tools/check_records.py")
CHECKER = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = CHECKER
SPEC.loader.exec_module(CHECKER)


def record_text(fields, body=""):
    """Emit the documented flat subset, not a general YAML serializer."""
    lines = ["---"]
    for key, value in fields.items():
        lines.append(f"{key}: {json.dumps(value, ensure_ascii=False)}")
    return "\n".join(lines + ["---", "", body, ""])


def put(root, name, text):
    target = root / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8", newline="\n")
    return target


def snapshot(root):
    """Byte + nanosecond mtime + inventory oracle, ONLY for generated test roots."""
    return {p.relative_to(root).as_posix(): (hashlib.sha256(p.read_bytes()).hexdigest(), p.stat().st_mtime_ns)
            for p in sorted(root.rglob("*")) if p.is_file()}


def digest_files(paths):
    return {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in paths}
