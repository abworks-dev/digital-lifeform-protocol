"""Freeze/verify a finite public evidence bundle, never discover private files.

This test helper is not an installer, harness adapter, or business record schema.
It writes only explicitly requested new bundle files or a new extraction root.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import sys
import zipfile

SOURCES = (
    'AGENTS.md', 'README.md',
    'docs/PROJECT.md', 'docs/ROADMAP.md', 'docs/HARNESS.md',
    'docs/RECORDS.md', 'docs/SECURITY.md', 'docs/QUICKSTART.md', 'docs/HERMES.md',
    'skills/creator-account-ledger/SKILL.md',
    'workflows/maintain-creator-ledger.md', 'workflows/change-access.md',
    'workflows/review-accounts.md', 'workflows/exit-or-handoff.md',
    'workflows/respond-to-incident.md', 'workflows/publish-and-commercialize.md',
    'templates/profile.md', 'templates/identity.md', 'templates/project.md',
    'templates/account.md', 'templates/delegation.md', 'templates/decision.md',
    'templates/review.md',
    'examples/creator-ledger/README.md', 'examples/creator-ledger/AGENT.md',
    'examples/creator-ledger/identity.md',
    'examples/creator-ledger/account-existing.md',
    'examples/creator-ledger/account-proposed.md',
    'examples/creator-ledger/decision-rename.md',
    'examples/creator-ledger-tests.md',
    'platforms/README.md', 'platforms/xiaohongshu/README.md',
    'platforms/xiaohongshu/rules.md', 'platforms/xiaohongshu/guide.md',
    'tools/check_records.py',
)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe_member(name: str) -> bool:
    p = PurePosixPath(name)
    return bool(name) and not p.is_absolute() and '..' not in p.parts and '\\' not in name and ':' not in name and p.as_posix() == name


def read_bundle(manifest_path: Path, archive_path: Path) -> tuple[dict, dict[str, bytes]]:
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    if manifest.get('format') != 'dlp-harness-evidence-baseline-v1':
        raise ValueError('unknown evidence manifest format')
    if digest(archive_path.read_bytes()) != manifest['archive_sha256']:
        raise ValueError('archive hash mismatch')
    entries = manifest['files']
    if len({v['path'] for v in entries}) != len(entries):
        raise ValueError('duplicate manifest path')
    expected = {v['path']: v for v in entries}
    if not all(safe_member(n) for n in expected):
        raise ValueError('unsafe archive member')
    with zipfile.ZipFile(archive_path) as z:
        names = z.namelist()
        if len(set(names)) != len(names) or set(names) != set(expected):
            raise ValueError('archive inventory mismatch')
        data = {n: z.read(n) for n in names}
    for name, value in data.items():
        if digest(value) != expected[name]['sha256'] or len(value) != expected[name]['bytes']:
            raise ValueError('member hash/size mismatch: ' + name)
    index = '\n'.join(n + ' ' + expected[n]['sha256'] for n in sorted(expected)).encode('utf-8')
    if digest(index) != manifest['content_sha256']:
        raise ValueError('content index mismatch')
    return manifest, data


def freeze(root: Path, manifest_path: Path, archive_path: Path, base_commit: str) -> dict:
    if manifest_path.exists() or archive_path.exists():
        raise ValueError('refusing to overwrite baseline artifacts')
    data = {}
    for name in sorted(SOURCES):
        p = root / name
        if p.is_symlink() or not p.resolve().is_relative_to(root.resolve()):
            raise ValueError('source outside root or symlink')
        data[name] = p.read_text(encoding='utf-8-sig').replace('\r\n', '\n').encode('utf-8')
    entries = [{'path': n, 'sha256': digest(v), 'bytes': len(v)} for n, v in data.items()]
    index = '\n'.join(v['path'] + ' ' + v['sha256'] for v in entries).encode('utf-8')
    with zipfile.ZipFile(archive_path, 'x', compression=zipfile.ZIP_DEFLATED) as z:
        for name, value in data.items():
            info = zipfile.ZipInfo(name, date_time=(2026, 10, 21, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            z.writestr(info, value)
    manifest = {
        'format': 'dlp-harness-evidence-baseline-v1',
        'baseline_id': 'creator-ledger-cross-harness-2026-10-21-b1',
        'base_commit': base_commit,
        'working_tree': 'dirty; these archived LF-normalized contents, not HEAD alone, define the test baseline',
        'normalization': 'UTF-8 without BOM, CRLF to LF; extracted bytes are fixed',
        'content_sha256': digest(index),
        'archive_sha256': digest(archive_path.read_bytes()),
        'files': entries,
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('freeze', 'verify', 'extract'))
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--archive', type=Path, required=True)
    parser.add_argument('--root', type=Path)
    parser.add_argument('--base-commit')
    args = parser.parse_args()
    try:
        if args.action == 'freeze':
            if args.root is None or not args.base_commit:
                raise ValueError('freeze needs explicit root and base commit')
            manifest = freeze(args.root, args.manifest, args.archive, args.base_commit)
        else:
            manifest, data = read_bundle(args.manifest, args.archive)
            if args.action == 'extract':
                if args.root is None or args.root.exists():
                    raise ValueError('extract needs a new, nonexistent root')
                args.root.mkdir(parents=True, exist_ok=False)
                for name, value in data.items():
                    target = args.root / name
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with target.open('xb') as f:
                        f.write(value)
        print(json.dumps({'baseline_id': manifest['baseline_id'], 'content_sha256': manifest['content_sha256'], 'files': len(manifest['files']), 'action': args.action}, sort_keys=True))
        return 0
    except (OSError, ValueError, KeyError, zipfile.BadZipFile) as exc:
        print(type(exc).__name__ + ': ' + str(exc), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
