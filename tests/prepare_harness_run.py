"""Prepare a NEW fictional harness test workspace; never install/run a harness.

The project-level Skill copy is only made inside the new temporary test root.
No user/global skill directories, configuration, credentials, or network access.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys
sys.dont_write_bytecode = True
from harness_baseline import read_bundle


def prepare(root: Path, host: str, mode: str, manifest: Path, archive: Path, prompts: Path, recovery: Path | None = None) -> dict:
    if root.exists():
        raise ValueError('refusing to overwrite an existing test root')
    if host not in ('codex', 'claude', 'dsh') or mode not in ('discovery', 'explicit', 'write'):
        raise ValueError('unknown host or test mode')
    baseline, data = read_bundle(manifest, archive)
    inputs = json.loads(prompts.read_text(encoding='utf-8'))
    if recovery is not None:
        inputs['recovery'] = json.loads(recovery.read_text(encoding='utf-8'))['recovery']
    if mode == 'discovery' and host == 'dsh':
        raise ValueError('DSH discovery has no tested project-directory convention; use explicit mode')
    root.mkdir(parents=True, exist_ok=False)
    for name, value in data.items():
        target = root / 'framework' / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(value)
    prefix = 'examples/creator-ledger/'
    for name, value in data.items():
        if name.startswith(prefix):
            target = root / 'records' / name[len(prefix):]
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(value)
    if mode == 'discovery':
        directory = '.agents' if host == 'codex' else '.claude'
        target = root / directory / 'skills/creator-account-ledger/SKILL.md'
        target.parent.mkdir(parents=True)
        target.write_bytes(data['skills/creator-account-ledger/SKILL.md'])
    control = root / '.harness-control'
    control.mkdir()
    for kind in ('discovery', 'explicit', 'write', 'recovery'):
        (control / (kind + '-prompt.txt')).write_text(inputs[kind].replace('ROOT', str(root.resolve())), encoding='utf-8')
    before = {}
    for p in sorted(root.rglob('*')):
        if p.is_file() and '.harness-control' not in p.relative_to(root).parts:
            before[p.relative_to(root).as_posix()] = {'sha256': hashlib.sha256(p.read_bytes()).hexdigest(), 'mtime_ns': p.stat().st_mtime_ns}
    result = {'format': 'dlp-harness-run-v1', 'baseline_id': baseline['baseline_id'], 'content_sha256': baseline['content_sha256'], 'host': host, 'mode': mode, 'before': before, 'notice': 'Control files are test inputs, not user authorization or production configuration. Native host launch/credentials must be checked separately.'}
    (control / 'before.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return result


def inspect(root: Path) -> dict:
    before = json.loads((root / '.harness-control/before.json').read_text(encoding='utf-8'))
    if before.get('format') != 'dlp-harness-run-v1':
        raise ValueError('not a prepared fictional test root')
    current = {}
    for p in sorted(root.rglob('*')):
        if p.is_file() and '.harness-control' not in p.relative_to(root).parts:
            current[p.relative_to(root).as_posix()] = {'sha256': hashlib.sha256(p.read_bytes()).hexdigest(), 'mtime_ns': p.stat().st_mtime_ns}
    old = before['before']
    changed = sorted(n for n in old.keys() & current.keys() if old[n] != current[n])
    return {'baseline_id': before['baseline_id'], 'host': before['host'], 'mode': before['mode'], 'added': sorted(current.keys() - old.keys()), 'removed': sorted(old.keys() - current.keys()), 'changed_bytes_or_mtime': changed, 'unchanged': len(old.keys() & current.keys()) - len(changed), 'notice': 'Only this explicitly prepared synthetic workspace was inspected; no claim about host histories or global state.'}


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('action', choices=('prepare', 'inspect'))
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--host', choices=('codex', 'claude', 'dsh'))
    p.add_argument('--mode', choices=('discovery', 'explicit', 'write'))
    fixtures = Path(__file__).resolve().parent / 'fixtures'
    p.add_argument('--manifest', type=Path, default=fixtures / 'harness-baseline.json')
    p.add_argument('--archive', type=Path, default=fixtures / 'harness-baseline.zip')
    p.add_argument('--prompts', type=Path, default=fixtures / 'harness-prompts.json')
    p.add_argument('--recovery-input', type=Path, default=fixtures / 'harness-recovery-v2.json')
    a = p.parse_args()
    try:
        if a.action == 'prepare':
            if not a.host or not a.mode:
                p.error('prepare requires --host and --mode')
            value = prepare(a.root, a.host, a.mode, a.manifest, a.archive, a.prompts, a.recovery_input)
            value = {k: v for k, v in value.items() if k != 'before'}
        else:
            value = inspect(a.root)
        print(json.dumps(value, ensure_ascii=True, indent=2))
        return 0
    except (OSError, ValueError, KeyError) as exc:
        print(type(exc).__name__ + ': ' + str(exc), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
