"""Offline and mocked-network regression tests for the experimental review aid."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch, MagicMock

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('source_changes', ROOT / 'tools/check_source_changes.py')
CHECK = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECK)
URL = 'https://example.com/rules'
BODY = 'A substantive synthetic policy sentence for offline review, with conditions and scope. ' * 4


def envelope(body=BODY, date='2026-01-01', url=URL):
    return 'Title: Rules\nURL Source: ' + url + '\nPublished Time: ' + date + '\n\nMarkdown Content:\n' + body


class SourceChangesTests(unittest.TestCase):
    def test_first(self):
        self.assertEqual(CHECK.compare('s', URL, BODY)['status'], 'baseline-needed')

    def test_unchanged_not_current(self):
        result = CHECK.compare('s', URL, BODY, BODY)
        self.assertEqual(result['status'], 'unchanged-not-current')
        self.assertFalse(result['authority_updated'])
        self.assertEqual(result['origin_http_status'], 'unknown')

    def test_changed(self):
        self.assertEqual(CHECK.compare('s', URL, BODY + 'New clause.', BODY)['status'], 'review-required')

    def test_unreadable(self):
        for text in ['short', 'HTTP 403 Forbidden\n' + BODY, 'Just a moment\n' + BODY,
                     'Warning: Target URL returned error 404\n' + envelope(),
                     envelope(url='https://example.com/other'), 'Access Denied\n' + BODY]:
            with self.subTest(text=text):
                self.assertEqual(CHECK.compare('s', URL, text, BODY)['status'], 'unreadable')
        self.assertEqual(CHECK.compare('s', URL, BODY, 'bad')['status'], 'unreadable')

    def test_crlf_and_whitespace(self):
        self.assertEqual(CHECK.compare('s', URL, '  ' + BODY.replace(' ', '\r\n\t'), BODY)['status'], 'unchanged-not-current')

    def test_metadata_changes(self):
        self.assertEqual(CHECK.compare('s', URL, envelope(date='2026-10-21'), envelope())['status'], 'unchanged-not-current')
        self.assertEqual(CHECK.compare('s', URL, envelope(BODY + '\nPublished Time: changed'), envelope())['status'], 'review-required')

    def run_main(self, args):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = CHECK.main(args)
        return code, out.getvalue(), err.getvalue()

    def test_read_only_and_explicit_report_capture(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            current, baseline = root / 'input.txt', root / 'baseline.txt'
            current.write_bytes(envelope().replace('\n', '\r\n').encode())
            baseline.write_text(envelope(), encoding='utf-8')
            before = {p.name: p.read_bytes() for p in root.iterdir()}
            args = ['--source', 's', '--url', URL, '--input', str(current), '--baseline', str(baseline)]
            code, out, _ = self.run_main(args)
            self.assertEqual(code, 0)
            self.assertEqual(json.loads(out)['status'], 'unchanged-not-current')
            self.assertEqual(before, {p.name: p.read_bytes() for p in root.iterdir()})
            report, capture = root / 'report.json', root / 'capture.txt'
            code, out, _ = self.run_main(args + ['--report', str(report), '--capture', str(capture)])
            self.assertEqual(code, 0)
            self.assertEqual(capture.read_bytes(), current.read_bytes())
            self.assertEqual(json.loads(report.read_text(encoding='utf-8')), json.loads(out))
            for target in [current, baseline, report, capture]:
                saved = target.read_bytes()
                code, _, _ = self.run_main(args + ['--report', str(target)])
                self.assertEqual(code, 2)
                self.assertEqual(target.read_bytes(), saved)
            code, _, _ = self.run_main(args + ['--report', str(root / 'same'), '--capture', str(root / 'same')])
            self.assertEqual(code, 2)
            self.assertFalse((root / 'same').exists())

    def test_fetch_mock_and_failure(self):
        response = MagicMock()
        response.status = 200
        response.read.return_value = envelope().encode()
        response.__enter__.return_value = response
        with patch.object(CHECK, 'urlopen', return_value=response) as mocked:
            code, out, _ = self.run_main(['--source', 's', '--url', URL, '--fetch'])
            self.assertEqual(code, 0)
            self.assertEqual(json.loads(out)['reader_http_status'], 200)
            self.assertEqual(mocked.call_args.args[0].full_url, 'https://r.jina.ai/' + URL)
            self.assertEqual(mocked.call_args.kwargs['timeout'], CHECK.FETCH_TIMEOUT)
        with patch.object(CHECK, 'urlopen', side_effect=OSError('offline')):
            code, out, _ = self.run_main(['--source', 's', '--url', URL, '--fetch'])
            self.assertEqual(code, 0)
            self.assertEqual(json.loads(out)['status'], 'fetch-failed')

    def test_public_query_requires_explicit_confirmation(self):
        url = URL + '?document=public'
        with self.assertRaises(ValueError):
            CHECK.validate_url(url)
        self.assertEqual(CHECK.validate_url(url, True), url)

    def test_chinese_shell_and_navigation(self):
        for body in [BODY + '未找到相关内容', BODY + '请先登录',
                     '\n'.join('[Navigation](https://example.com/path)' for _ in range(15))]:
            self.assertEqual(CHECK.compare('s', URL, body)['status'], 'unreadable')

    def test_fetch_size_limit(self):
        response = MagicMock()
        response.__enter__.return_value = response
        response.status = 200
        response.read.return_value = b'x' * (CHECK.MAX_FETCH_BYTES + 1)
        with patch.object(CHECK, 'urlopen', return_value=response):
            with self.assertRaisesRegex(ValueError, 'byte limit'):
                CHECK.fetch_text(URL)

    def test_reject_unsafe_urls_without_network(self):
        with patch.object(CHECK, 'urlopen') as mocked:
            for url in ['http://example.com', 'https://localhost', 'https://127.0.0.1',
                        'https://[::1]', 'https://user:pass@example.com', 'https://x.local',
                        'https://example.com:8443']:
                with self.subTest(url=url):
                    code, _, _ = self.run_main(['--source', 's', '--url', url, '--fetch'])
                    self.assertEqual(code, 2)
            mocked.assert_not_called()


if __name__ == '__main__':
    unittest.main()
