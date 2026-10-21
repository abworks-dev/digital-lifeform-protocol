"""Deterministic checker tests; run with python -B -m unittest discover -s tests -v."""
import contextlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from support import CHECKER, ROOT, put, record_text, snapshot

CASES = json.loads((ROOT / "tests/fixtures/cases.json").read_text(encoding="utf-8"))


class CheckerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="dlp-check-test-")
        self.root = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)

    def run_check(self, records=None, **kw):
        return CHECKER.check(self.root, records or [], kw.pop("templates", []), kw.pop("documents", []), **kw)

    def write_base(self, name="record.md", **changes):
        fields = dict(CASES["base"], **changes)
        put(self.root, name, record_text(fields))
        return name

    def assert_rule(self, report, rule, level):
        self.assertIn((rule, level), {(d["rule"], d["level"]) for d in report["diagnostics"]}, report)

    def test_declared_valid_and_failure_fixtures(self):
        for case in CASES["cases"]:
            with self.subTest(case=case["name"]):
                fields = dict(CASES["base"], **case.get("overrides", {}))
                for key in case.get("remove", []):
                    fields.pop(key, None)
                put(self.root, "record.md", record_text(fields))
                before = snapshot(self.root)
                report = self.run_check(["record.md"], closed_set=case.get("closed", True), public_examples=case.get("public", False))
                self.assertEqual(CHECKER.exit_code(report), case["exit"], report)
                for rule, level in case["expected"]:
                    self.assert_rule(report, rule, level)
                self.assertEqual(snapshot(self.root), before)

    def test_unique_links_closed_set(self):
        a = self.write_base("a.md", id="account-a", links=["identity-b"])
        b = self.write_base("b.md", id="identity-b", type="identity", links=["account-a"])
        report = self.run_check([a, b], closed_set=True)
        self.assertEqual(CHECKER.exit_code(report), 0, report)

    def test_duplicate_ids_and_ambiguous_reference(self):
        a = self.write_base("a.md", id="account-duplicate")
        b = self.write_base("b.md", id="account-duplicate")
        c = self.write_base("c.md", id="identity-c", links=["account-duplicate"])
        report = self.run_check([a, b, c], closed_set=True)
        self.assert_rule(report, "MC02", "error")
        self.assert_rule(report, "MC06", "error")

    def test_nickname_does_not_merge_records(self):
        a = self.write_base("a.md", id="account-a", title="同名")
        b = self.write_base("b.md", id="account-b", title="同名")
        self.assertEqual(CHECKER.exit_code(self.run_check([a, b], closed_set=True)), 0)

    def test_id_has_no_new_naming_regex(self):
        self.write_base(id="内部 ID / 合成测试")
        self.assertEqual(CHECKER.exit_code(self.run_check(["record.md"], closed_set=True)), 0)

    def test_templates_and_skill_are_not_records(self):
        template = self.write_base("template.md", id="unknown", updated="unknown")
        put(self.root, "skill.md", "---\nname: sample-skill\ndescription: fictional\n---\n# 导航\n")
        report = self.run_check(templates=[template], documents=["skill.md"], closed_set=True)
        self.assertEqual(CHECKER.exit_code(report), 0, report)
        self.assert_rule(report, "MC01", "warning")

    def test_block_list_comments_crlf_and_bom(self):
        text = record_text(CASES["base"]).replace('links: []', 'links: # none\n  # comment\n')
        put(self.root, "record.md", "\ufeff" + text.replace("\n", "\r\n"))
        # An empty YAML links value is NOT []: must not silently pass it.
        report = self.run_check(["record.md"], closed_set=True)
        self.assertNotEqual(CHECKER.exit_code(report), 0)
        text = record_text(dict(CASES["base"], links=["identity-b"]))
        text = text.replace('links: ["identity-b"]', 'links:\n  - "identity-b" # comment')
        put(self.root, "record.md", "\ufeff" + text.replace("\n", "\r\n"))
        self.write_base("b.md", id="identity-b", type="identity")
        report = self.run_check(["record.md", "b.md"], closed_set=True)
        self.assertEqual(CHECKER.exit_code(report), 0, report)

    def test_quoted_scalars_and_literal_hash(self):
        text = record_text(CASES["base"]).replace('title: "虚构检查样例"', "title: 'it''s # a title' # comment")
        put(self.root, "record.md", text)
        self.assertEqual(CHECKER.exit_code(self.run_check(["record.md"], closed_set=True)), 0)

    def test_duplicate_key_is_error(self):
        put(self.root, "record.md", record_text(CASES["base"]).replace('type: "account"', 'type: "account"\ntype: "identity"'))
        report = self.run_check(["record.md"])
        self.assert_rule(report, "PARSE", "error")
        self.assertEqual(CHECKER.exit_code(report), 1)

    def test_unsupported_yaml_never_passes(self):
        for value in ["|\n  long text", "&source anchor", "*source", "{nested: value}", "!!str value"]:
            with self.subTest(value=value):
                put(self.root, "record.md", record_text(CASES["base"]).replace('source: "fictional-user"', 'source: ' + value))
                report = self.run_check(["record.md"])
                self.assert_rule(report, "PARSE", "unchecked")
                self.assertNotEqual(CHECKER.exit_code(report), 0)

    def test_missing_frontmatter_and_closing_marker(self):
        for text in ["# Not a record\n", "---\nid: x\n"]:
            put(self.root, "record.md", text)
            self.assertNotEqual(CHECKER.exit_code(self.run_check(["record.md"])), 0)

    def test_empty_scope_and_missing_input(self):
        self.assertEqual(CHECKER.exit_code(self.run_check()), 2)
        self.assertEqual(CHECKER.exit_code(self.run_check(["absent.md"])), 2)

    def test_closed_claim_with_unread_input_is_not_proof_of_missing_id(self):
        self.write_base(links=["account-unread"])
        report = self.run_check(["record.md", "unread.md"], closed_set=True)
        self.assert_rule(report, "MC06", "unchecked")
        self.assertFalse(any(d["rule"] == "MC06" and d["code"] == "missing_target" for d in report["diagnostics"]), report)

    def test_closed_claim_with_unsupported_id_remains_incomplete(self):
        self.write_base(links=["account-unread"])
        put(self.root, "unread.md", record_text(CASES["base"]).replace('id: "account-fixture"', 'id: &alias account-unread'))
        report = self.run_check(["record.md", "unread.md"], closed_set=True)
        self.assert_rule(report, "MC06", "unchecked")
        self.assertFalse(any(d["rule"] == "MC06" and d["code"] == "missing_target" for d in report["diagnostics"]), report)

    def test_input_paths_do_not_escape_or_scan(self):
        self.write_base()
        for path in ["../outside.md", str(self.root / "record.md"), ".", "sub/../record.md"]:
            with self.subTest(path=path):
                self.assertEqual(CHECKER.exit_code(self.run_check([path])), 2)

    def test_symbolic_link_is_not_followed(self):
        target = self.root / "target.md"
        target.write_text(record_text(CASES["base"]), encoding="utf-8")
        link = self.root / "link.md"
        try:
            link.symlink_to(target)
        except (OSError, NotImplementedError):
            self.skipTest("OS did not permit creation of test symlink")
        report = self.run_check(["link.md"])
        self.assertEqual(CHECKER.exit_code(report), 2)

    def test_physical_alias_is_not_duplicate_record(self):
        self.write_base()
        try:
            (self.root / "alias.md").hardlink_to(self.root / "record.md")
        except (OSError, NotImplementedError):
            self.skipTest("OS did not permit creation of a test hard link")
        report = self.run_check(["record.md", "alias.md"], closed_set=True)
        self.assertEqual(CHECKER.exit_code(report), 2, report)
        self.assertFalse(any(d["rule"] == "MC02" and d["code"] == "duplicate_id" for d in report["diagnostics"]))

    def test_error_precedence_over_incomplete_input(self):
        self.write_base(type="not-a-type")
        report = self.run_check(["record.md", "absent.md"])
        self.assertGreater(report["summary"]["error"], 0)
        self.assertGreater(report["summary"]["unchecked"], 0)
        self.assertEqual(CHECKER.exit_code(report), 1)

    def test_invalid_utf8_is_incomplete_not_exception(self):
        (self.root / "record.md").write_bytes(b"\xff\xfeinvalid")
        self.assertEqual(CHECKER.exit_code(self.run_check(["record.md"])), 2)

    def test_navigation_explicit_scope_and_anchors(self):
        put(self.root, "a.md", "# Start\n[ok](<b.md#标题>)\n")
        put(self.root, "b.md", "# 标题\n")
        report = self.run_check(documents=["a.md", "b.md"])
        self.assertEqual(CHECKER.exit_code(report), 0, report)
        put(self.root, "a.md", "[broken](b.md#absent)\n")
        self.assert_rule(self.run_check(documents=["a.md", "b.md"]), "MC07", "error")

    def test_external_and_out_of_scope_links_are_unchecked(self):
        put(self.root, "a.md", "[outside](b.md)\n[web](https://example.invalid/)\n")
        put(self.root, "b.md", "# Must not be read\n")
        original = CHECKER.os.open
        reads = []
        def observe(path, *args, **kw):
            reads.append(Path(path).name)
            return original(path, *args, **kw)
        with patch.object(CHECKER.os, "open", observe):
            report = self.run_check(documents=["a.md"])
        self.assertEqual(reads, ["a.md"])
        self.assert_rule(report, "MC07", "unchecked")
        self.assertEqual(CHECKER.exit_code(report), 2)

    def test_code_fence_links_are_not_navigation(self):
        put(self.root, "a.md", "# Header\n```markdown\n[not navigation](absent.md)\n```\n")
        self.assertEqual(CHECKER.exit_code(self.run_check(documents=["a.md"])), 0)

    def test_reference_style_markdown_not_silently_passed(self):
        put(self.root, "a.md", "[label][ref]\n\n[ref]: missing.md\n")
        report = self.run_check(documents=["a.md"])
        self.assert_rule(report, "MC07", "unchecked")

    def test_repeat_determinism_and_diagnostic_redaction(self):
        marker = "SYNTHETIC-NOT-A-SECRET-DO-NOT-ECHO"
        self.write_base(type=marker)
        before = snapshot(self.root)
        first = self.run_check(["record.md"], baseline="fixture-v1")
        second = self.run_check(["record.md"], baseline="fixture-v1")
        self.assertEqual(first, second)
        self.assertNotIn(marker, json.dumps(first))
        self.assertEqual(before, snapshot(self.root))
        self.assertEqual(first["baseline"], "fixture-v1")

    def test_cli_json_and_exit_codes(self):
        self.write_base()
        command = [sys.executable, "-B", str(ROOT / "tools/check_records.py"), "--root", str(self.root), "--record", "record.md", "--closed-set", "--format", "json"]
        before = snapshot(self.root)
        result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["summary"]["error"], 0)
        self.assertEqual(before, snapshot(self.root))
        result = subprocess.run(command + ["--record", "absent.md"], capture_output=True, text=True, encoding="utf-8", check=False)
        self.assertEqual(result.returncode, 2)
        result = subprocess.run([sys.executable, "-B", str(ROOT / "tools/check_records.py")], capture_output=True, text=True, encoding="utf-8", check=False)
        self.assertEqual(result.returncode, 2)


if __name__ == "__main__":
    unittest.main()
