"""Reduce explicitly named native CLI event files to public, fictional evidence.

No directory discovery, configuration/credential access, or network. The output
omits authentication metadata, IDs, arbitrary system fields, and tool-result
bodies; review the resulting answers/commands before publishing. Not a general
secret scrubber. Pass only the synthetic test event files, never private logs.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--host', choices=('codex', 'claude'), required=True)
    p.add_argument('--events', type=Path, required=True)
    p.add_argument('--run-root', required=True)
    p.add_argument('--home-prefix', required=True)
    p.add_argument('--exit-code', type=int, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    if a.out.exists():
        p.error('refusing to overwrite an existing evidence file')
    raw = a.events.read_bytes()
    replacements = []
    for source, target in [(a.run_root, '<run-root>'), (a.home_prefix, '<user-home>')]:
        replacements.extend([(source.replace('\\', '\\\\'), target), (source, target), (source.replace('\\', '/'), target)])

    def clean(value):
        if isinstance(value, str):
            for source, target in replacements:
                value = value.replace(source, target)
            return value
        if isinstance(value, list):
            return [clean(v) for v in value]
        if isinstance(value, dict):
            return {k: clean(v) for k, v in value.items()}
        return value

    kept = []
    for line in raw.decode('utf-8-sig').splitlines():
        if not line.strip():
            continue
        e = json.loads(line)
        if a.host == 'codex':
            if e.get('type') == 'item.completed':
                item = e['item']; kind = item.get('type')
                if kind in ('agent_message', 'error'):
                    kept.append({'kind': kind, 'text': item.get('text', item.get('message', ''))})
                elif kind == 'command_execution':
                    output = item.get('aggregated_output', '')
                    kept.append({'kind': kind, 'command': item.get('command'), 'exit_code': item.get('exit_code'), 'status': item.get('status'), 'output_sha256': hashlib.sha256(output.encode()).hexdigest(), 'output_chars': len(output), 'truncation_notice': 'truncated' in output.lower()})
                elif kind == 'file_change':
                    kept.append({'kind': kind, 'status': item.get('status'), 'changes': item.get('changes', [])})
            elif e.get('type') in ('error', 'turn.failed'):
                kept.append({'kind': e['type'], 'error': e.get('error', e.get('message'))})
        else:
            if e.get('type') == 'system' and e.get('subtype') == 'init':
                kept.append({'kind': 'init', 'cwd': e.get('cwd'), 'version': e.get('claude_code_version'), 'model_reported': e.get('model'), 'tools': e.get('tools'), 'target_skill_enumerated': 'creator-account-ledger' in e.get('skills', []), 'plugins_count': len(e.get('plugins', [])), 'mcp_count': len(e.get('mcp_servers', [])), 'analytics_disabled_reported': e.get('analytics_disabled')})
            elif e.get('type') == 'assistant':
                for c in e.get('message', {}).get('content', []):
                    if c.get('type') == 'text':
                        kept.append({'kind': 'assistant_text', 'text': c.get('text')})
                    elif c.get('type') == 'tool_use':
                        kept.append({'kind': 'tool_use', 'name': c.get('name'), 'input': c.get('input')})
            elif e.get('type') == 'result':
                kept.append({'kind': 'result', 'is_error': e.get('is_error'), 'terminal_reason': e.get('terminal_reason'), 'result': e.get('result'), 'num_turns': e.get('num_turns'), 'duration_api_ms': e.get('duration_api_ms'), 'permission_denials': e.get('permission_denials', []), 'total_cost_usd': e.get('total_cost_usd')})
    result = {'format': 'dlp-native-harness-evidence-v1', 'host': a.host, 'native_exit_code': a.exit_code, 'raw_events_sha256': hashlib.sha256(raw).hexdigest(), 'events': clean(kept), 'omissions': ['raw authentication/system metadata', 'session/message identifiers', 'tool result bodies', 'unselected events; consult run report for evidence limitations']}
    a.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'host': a.host, 'events_kept': len(kept), 'native_exit_code': a.exit_code}, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
