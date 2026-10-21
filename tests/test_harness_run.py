"""Offline checks of test preparation, not native harness compatibility tests."""
import json
from pathlib import Path
import tempfile
import unittest
import sys
sys.dont_write_bytecode = True
from prepare_harness_run import prepare, inspect

FIXTURES = Path(__file__).resolve().parent / 'fixtures'


class HarnessRunTests(unittest.TestCase):
    def make(self, root, host='codex', mode='explicit'):
        return prepare(root, host, mode, FIXTURES / 'harness-baseline.json', FIXTURES / 'harness-baseline.zip', FIXTURES / 'harness-prompts.json')

    def test_preparation_and_no_change_inspection(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t) / 'run'
            result = self.make(root)
            self.assertEqual(41, len(result['before']))
            self.assertEqual([], inspect(root)['changed_bytes_or_mtime'])
            self.assertEqual([], inspect(root)['added'])
            self.assertNotIn('ROOT', (root / '.harness-control/explicit-prompt.txt').read_text(encoding='utf-8'))
            with self.assertRaises(ValueError):
                self.make(root)

    def test_only_project_local_discovery_copy(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t) / 'run'
            self.make(root, host='claude', mode='discovery')
            self.assertEqual((root / 'framework/skills/creator-account-ledger/SKILL.md').read_bytes(), (root / '.claude/skills/creator-account-ledger/SKILL.md').read_bytes())
            with self.assertRaises(ValueError):
                self.make(Path(t) / 'other', host='dsh', mode='discovery')
            self.assertFalse((Path(t) / 'other').exists())

    def test_inspection_reports_changes_without_repair(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t) / 'run'
            self.make(root)
            p = root / 'records/account-existing.md'
            p.write_bytes(p.read_bytes() + b'\nsynthetic change\n')
            (root / 'records/new.md').write_text('fictional', encoding='utf-8')
            (root / 'records/AGENT.md').unlink()
            result = inspect(root)
            self.assertEqual(['records/account-existing.md'], result['changed_bytes_or_mtime'])
            self.assertEqual(['records/new.md'], result['added'])
            self.assertEqual(['records/AGENT.md'], result['removed'])
            self.assertEqual(result, inspect(root))

    def test_saved_dsh_artifacts_are_scoped_synthetic_records(self):
        from support import CHECKER
        with tempfile.TemporaryDirectory() as t:
            root = Path(t) / 'run'
            self.make(root, host='dsh', mode='write')
            for name in ('account-existing.md', 'decision-name-observation.md'):
                (root / 'records' / name).write_bytes((FIXTURES / 'harness-dsh-saved' / name).read_bytes())
            records = ['records/' + name for name in ('identity.md', 'account-existing.md', 'account-proposed.md', 'decision-rename.md', 'decision-name-observation.md')]
            report = CHECKER.check(root, records, [], [], closed_set=True, public_examples=True)
            # Public <run-root>/<control-input> redactions are deliberately not
            # treated as supported Markdown navigation or silently waived.
            self.assertEqual(2, CHECKER.exit_code(report))
            self.assertEqual({'error': 0, 'warning': 1, 'unchecked': 4}, report['summary'])
            text = (root / 'records/account-existing.md').read_text(encoding='utf-8')
            self.assertIn('当前名称: 纸舟数字整理。', text)
            self.assertIn('decision-creator-ledger-name-observation', text)
            self.assertIn('reported', text)
            self.assertIn('unknown', text)
            evidence = json.loads((FIXTURES / 'harness-file-results.json').read_text(encoding='utf-8'))
            self.assertEqual(['records/decision-name-observation.md'], evidence['results']['dsh-write']['added'])
            self.assertEqual(['records/account-existing.md'], evidence['results']['dsh-write']['changed_bytes_or_mtime'])
            self.assertEqual([], evidence['results']['codex-write']['changed_bytes_or_mtime'])


if __name__ == '__main__':
    unittest.main()
