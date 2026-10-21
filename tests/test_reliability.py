"""Replay coverage and immutable historical evidence."""
import hashlib
import json
from pathlib import Path
import unittest
import subprocess
import sys
import tempfile

from support import ROOT, snapshot
from replay_scenarios import run_all


class ReliabilityTests(unittest.TestCase):
    def test_prepare_session_refuses_overwrite(self):
        with tempfile.TemporaryDirectory(prefix="dlp-session-test-") as tmp:
            root = Path(tmp) / "new-session"
            command = [sys.executable, "-B", str(ROOT / "tests/replay_scenarios.py"), "--prepare-session", str(root), "--state", "partial"]
            first = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", check=False)
            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertEqual(len(json.loads(first.stdout)["files"]), 5)
            before = snapshot(root)
            again = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", check=False)
            self.assertEqual(again.returncode, 2)
            self.assertEqual(before, snapshot(root))

    def test_replay_matches_published_fixture_oracle(self):
        expected = json.loads((ROOT / "tests/fixtures/replay-expected.json").read_text(encoding="utf-8"))
        self.assertEqual(run_all(), expected)

    def test_old_report_preserved(self):
        expected = json.loads((ROOT / "tests/fixtures/historical-evidence.json").read_text(encoding="utf-8"))
        for name, digest in expected["sha256"].items():
            with self.subTest(file=name):
                self.assertEqual(hashlib.sha256((ROOT / name).read_text(encoding="utf-8-sig").encode("utf-8")).hexdigest(), digest,
                                 "Historical evidence changed; append a new report instead of rewriting the old one")


if __name__ == "__main__":
    unittest.main()
