"""Experimental source review aid, not a policy verifier. Offline unless --fetch.

Only explicitly named UTF-8 files are read. No baseline rotation or rule updates.
Normalization ignores whitespace and Jina envelope metadata (before Markdown Content).
Heuristics can miss shells and misclassify legitimate short/error-related documents.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import ipaddress
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

MIN_BODY_CHARS = 80
MAX_FETCH_BYTES = 2_000_000
FETCH_TIMEOUT = 20


def validate_url(url, allow_public_query=False):
    parts = urlsplit(url)
    if parts.scheme != 'https' or not parts.hostname or parts.username or parts.password:
        raise ValueError('URL must be public HTTPS without credentials')
    host = parts.hostname.lower().rstrip('.')
    if '.' not in host or host.endswith(('.localhost', '.local', '.internal', '.test', '.invalid')) or host == 'localhost':
        raise ValueError('URL must have a public hostname')
    try:
        ipaddress.ip_address(host)
    except ValueError:
        pass
    else:
        raise ValueError('IP literal URLs are not allowed')
    if (parts.query and not allow_public_query) or parts.fragment:
        raise ValueError('Query requires --allow-public-query; fragments are not allowed')
    if parts.port not in (None, 443):
        raise ValueError('Only HTTPS default port is allowed')
    return url


def fetch_text(url, allow_public_query=False):
    """Jina reader status is NOT evidence of the origin's HTTP status."""
    validate_url(url, allow_public_query)
    request = Request('https://r.jina.ai/' + url, headers={'Accept': 'text/plain'})
    with urlopen(request, timeout=FETCH_TIMEOUT) as response:
        status = response.status
        raw = response.read(MAX_FETCH_BYTES + 1)
    if status != 200:
        raise ValueError('reader HTTP status ' + str(status))
    if len(raw) > MAX_FETCH_BYTES:
        raise ValueError('reader response exceeds byte limit')
    return raw.decode('utf-8-sig'), status


def inspect_text(text, url):
    raw_hash = hashlib.sha256(text.encode('utf-8')).hexdigest()
    text = text.lstrip('\ufeff').replace('\r\n', '\n').replace('\r', '\n')
    envelope, marker, body = text.partition('Markdown Content:')
    if not marker:
        envelope, body = '', text
    sources = re.findall(r'^URL Source:\s*(\S+)\s*$', envelope, re.M)
    reasons = []
    if sources and any(source != url for source in sources):
        reasons.append('url-mismatch')
    # Only strip known transport metadata in an envelope, never policy body lines.
    normalized = re.sub(r'\s+', ' ', body).strip()
    errors = r'(?:HTTP(?:/\d(?:\.\d)?)?\s+(?:error\s+)?[45]\d\d\b|Error\s*[:(]\s*[45]\d\d\b|(?:^|\n)\s*(?:404 Not Found|403 Forbidden|502 Bad Gateway)\b|Warning:.*(?:[45]\d\d|error)|(?:^|\n)\s*(?:Access Denied|Forbidden|Bad Gateway)\s*$)'
    if re.search(errors, text, re.I | re.M):
        reasons.append('http-error-text')
    if re.search(r'just a moment|checking your browser|enable javascript|verify you are human|captcha|sign in to continue|请开启.{0,8}javascript|访问验证|安全验证|未找到相关内容|登录后查看|请先登录', body, re.I):
        reasons.append('shell-or-challenge')
    links = re.findall(r'\[[^\]]*\]\([^)]*\)', body)
    prose = re.sub(r'\[[^\]]*\]\([^)]*\)', '', body)
    if len(links) >= 5 and len(re.sub(r'\s', '', prose)) < MIN_BODY_CHARS:
        reasons.append('navigation-only')
    if len(re.sub(r'\s', '', normalized)) < MIN_BODY_CHARS:
        reasons.append('body-too-short')
    return {'raw_text_sha256': raw_hash,
            'sha256': hashlib.sha256(normalized.encode('utf-8')).hexdigest(),
            'normalized_chars': len(normalized), 'reasons': reasons,
            'url_evidence': 'matched-envelope' if sources and not 'url-mismatch' in reasons else ('mismatched-envelope' if sources else 'not-provided')}


def compare(source, url, current, baseline=None):
    now = inspect_text(current, url)
    old = inspect_text(baseline, url) if baseline is not None else None
    if now['reasons']:
        status = 'unreadable'
    elif old is None:
        status = 'baseline-needed'
    elif old['reasons']:
        status = 'unreadable'
    elif old['sha256'] != now['sha256']:
        status = 'review-required'
    else:
        status = 'unchanged-not-current'
    return {'source': source, 'url': url, 'status': status, 'current': now,
            'baseline': old, 'origin_http_status': 'unknown',
            'authority_updated': False, 'requires_human_review': True}


def exclusive_write(path, text):
    with Path(path).open('x', encoding='utf-8', newline='') as stream:
        stream.write(text)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True)
    parser.add_argument('--url', required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--input', type=Path, help='explicit UTF-8 capture; no network')
    mode.add_argument('--fetch', action='store_true', help='explicitly authorize anonymous Jina network request')
    parser.add_argument('--allow-public-query', action='store_true', help='confirm URL query is public and may appear in report and be sent to Jina with --fetch')
    parser.add_argument('--baseline', type=Path)
    parser.add_argument('--report', type=Path, help='new path only; never overwrite')
    parser.add_argument('--capture', type=Path, help='new raw capture path only')
    args = parser.parse_args(argv)
    written = []
    try:
        validate_url(args.url, args.allow_public_query)
        outputs = [p for p in (args.report, args.capture) if p is not None]
        inputs = [p for p in (args.input, args.baseline) if p is not None]
        if len({p.resolve() for p in outputs}) != len(outputs):
            raise ValueError('output paths must differ')
        for path in outputs:
            if path.exists() or path.is_symlink() or any(path.resolve() == p.resolve() for p in inputs):
                raise ValueError('refusing existing or input/baseline output path: ' + str(path))
        baseline = args.baseline.read_text(encoding='utf-8-sig') if args.baseline else None
        if args.fetch:
            try:
                current, reader_status = fetch_text(args.url, args.allow_public_query)
            except (OSError, ValueError) as exc:
                report = {'source': args.source, 'url': args.url, 'status': 'fetch-failed',
                          'error': str(exc), 'reader_http_status': 'failed-or-unknown',
                          'origin_http_status': 'unknown', 'authority_updated': False}
                current = None
            else:
                report = compare(args.source, args.url, current, baseline)
                report['reader_http_status'] = reader_status
        else:
            with args.input.open(encoding='utf-8', newline='') as stream:
                current = stream.read()
            report = compare(args.source, args.url, current, baseline)
            report['reader_http_status'] = 'not-observed'
        report['checked_at_utc'] = datetime.now(timezone.utc).isoformat()
        report['normalization_version'] = 'body-whitespace-jina-envelope-v1'
        report['output_write_semantics'] = 'exclusive, capture then report; not transactional; earlier output may remain on later failure'
        serialized = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
        if args.capture and current is not None:
            exclusive_write(args.capture, current)
            written.append(str(args.capture))
        if args.report:
            exclusive_write(args.report, serialized)
            written.append(str(args.report))
        sys.stdout.write(serialized)
        return 0
    except (OSError, ValueError) as exc:
        sys.stderr.write(str(exc) + '\n')
        if written:
            sys.stderr.write('Partial outputs remain (not transactional): ' + ', '.join(written) + '\n')
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
