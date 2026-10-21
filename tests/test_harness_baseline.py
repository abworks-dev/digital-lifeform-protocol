"""Offline checks of the third-batch evidence snapshot, not live harness tests."""
from pathlib import Path
import json
import subprocess
import sys
import tempfile
import unittest

from harness_baseline import read_bundle

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / 'tests/fixtures/harness-baseline.json'
ARCHIVE = ROOT / 'tests/fixtures/harness-baseline.zip'
HELPER = ROOT / 'tests/harness_baseline.py'


class EvidenceBaselineTests(unittest.TestCase):
    def test_frozen_bundle_inventory_and_hashes(self):
        manifest, data = read_bundle(MANIFEST, ARCHIVE)
        self.assertEqual(35, len(data))
        self.assertEqual('creator-ledger-cross-harness-2026-10-21-b1', manifest['baseline_id'])
        self.assertIn('skills/creator-account-ledger/SKILL.md', data)
        self.assertIn(b'reported', data['examples/creator-ledger/account-existing.md'])

    def test_extract_exact_bytes_and_refuse_existing_root(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / 'new'
            cmd = [sys.executable, '-B', str(HELPER), 'extract', '--manifest', str(MANIFEST), '--archive', str(ARCHIVE), '--root', str(target)]
            first = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(0, first.returncode, first.stderr)
            _, data = read_bundle(MANIFEST, ARCHIVE)
            for name, value in data.items():
                self.assertEqual(value, (target / name).read_bytes())
            second = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(2, second.returncode)
            self.assertIn('new, nonexistent root', second.stderr)

    def test_tampered_archive_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / 'changed.zip'
            target.write_bytes(ARCHIVE.read_bytes() + b'changed')
            with self.assertRaisesRegex(ValueError, 'archive hash mismatch'):
                read_bundle(MANIFEST, target)

    def test_unsafe_manifest_member_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            manifest = json.loads(MANIFEST.read_text(encoding='utf-8'))
            manifest['files'][0]['path'] = '../outside.md'
            target = Path(temp) / 'unsafe.json'
            target.write_text(json.dumps(manifest), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'unsafe archive member'):
                read_bundle(target, ARCHIVE)

    def test_freeze_does_not_overwrite_artifacts(self):
        with tempfile.TemporaryDirectory() as temp:
            manifest = Path(temp) / 'manifest.json'
            manifest.write_bytes(b'protected')
            archive = Path(temp) / 'archive.zip'
            result = subprocess.run([sys.executable, '-B', str(HELPER), 'freeze', '--root', str(ROOT), '--base-commit', 'test', '--manifest', str(manifest), '--archive', str(archive)], capture_output=True, text=True)
            self.assertEqual(2, result.returncode)
            self.assertEqual(b'protected', manifest.read_bytes())
            self.assertFalse(archive.exists())


if __name__ == '__main__':
    unittest.main()
