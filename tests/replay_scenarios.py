"""Test-only fault/recovery laboratory, NOT an account-maintenance runtime.

Only generated temporary copies are written. --recover-root is an internal
fresh-process probe reading fixed fictional filenames, never discovering data.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from unittest.mock import patch

sys.dont_write_bytecode = True
from support import CHECKER, ROOT, put, record_text, snapshot

SEED = ROOT / "examples/creator-ledger"
FILES = ["identity.md", "account-existing.md", "account-proposed.md", "decision-rename.md"]
ACCOUNT = "account-existing.md"
NEW_FILE = "decision-name-observation.md"
NEW_ID = "decision-creator-ledger-name-observation"
ACCOUNT_ID = "account-creator-ledger-existing"
OLD_NAME = "纸舟整理札记"
NEW_NAME = "纸舟数字整理"
STALE = "新名未成为当前观察"


def seed(root):
    for name in FILES:
        shutil.copyfile(SEED / name, root / name)


def check_copy(root):
    names = FILES + ([NEW_FILE] if (root / NEW_FILE).is_file() else [])
    return CHECKER.check(root, names, [], [], closed_set=True, public_examples=True, baseline="creator-ledger-2026-10-21")


def new_decision():
    return record_text({"id": NEW_ID, "type": "decision", "title": "虚构名称观察 O2", "status": "confirmed",
                        "source": "fictional-user 的合成报告", "updated": "2026-10-21", "confirmed_by": "fictional-user",
                        "confirmed_at": "2026-10-21", "links": [ACCOUNT_ID]},
                       "# 已确认事实（测试合成）\n\n观察 O2: fictional-user 报告显示纸舟数字整理。\n报告日期: 2026-10-21（合成输入明确提供，不是平台生效日）\n证据质量: reported\n平台独立核实: unknown\n平台生效时间: unknown\n获准范围: 新建本决定与主档名称观察、来源及 links；不改身份、所有者或拟议号。\n")


def account_after(text, backlink=True, stale=False):
    # Exact fixture-specific mutation; not a general Markdown writer.
    text = text.replace('source: "fictional-user 的案例陈述；名称观察见 decision-creator-ledger-rename 的观察 O1"',
                        'source: "fictional-user 的案例陈述；当前观察见 ' + NEW_ID + ' 的 O2，旧 O1 保留在历史决定"', 1)
    text = text.replace("当前名称: " + OLD_NAME + "。", "当前名称: " + NEW_NAME + "。", 1)
    start = text.index("名称来源与时点:")
    end = text.index("\n", start)
    text = text[:start] + "名称来源与时点: " + NEW_ID + " 的观察 O2；2026-10-21 fictional-user 报告，reported；平台独立核实和生效时间 unknown。" + text[end:]
    if backlink:
        text = text.replace("  - decision-creator-ledger-rename\n", "  - decision-creator-ledger-rename\n  - " + NEW_ID + "\n", 1)
    if stale:
        # Recreate the old report's drift mechanism; never rewrite its old copy.
        text += "\n品牌进展旧说明: " + STALE + "（刻意合成的陈旧描述，未获准自动改写）。\n"
    return text


def approved_fixture_write(root, expected_hash, omit_backlink=False, stale=False):
    """REFERENCE TEST ACTION ONLY. Hash guard + sequential writes, no transaction."""
    target = root / ACCOUNT
    if hashlib.sha256(target.read_bytes()).hexdigest() != expected_hash:
        return {"state": "conflict", "written": [], "unwritten": [NEW_FILE, ACCOUNT]}
    (root / NEW_FILE).write_text(new_decision(), encoding="utf-8", newline="\n")
    try:
        target.write_text(account_after(target.read_text(encoding="utf-8"), not omit_backlink, stale), encoding="utf-8", newline="\n")
    except OSError:
        return {"state": "partial", "written": [NEW_FILE], "unwritten": [ACCOUNT]}
    return {"state": "saved", "written": [NEW_FILE, ACCOUNT], "unwritten": []}


def recover(root):
    """Fixture oracle, NOT the checker or an Agent. Reads disk, not chat memory."""
    account = (root / ACCOUNT).read_text(encoding="utf-8")
    header = account.split("---", 2)[1]
    current = re.search(r"^当前名称: (.+?)[。]?\s*$", account, re.M).group(1).rstrip("。")
    saved = (root / NEW_FILE).is_file()
    reciprocal = NEW_ID in re.findall(r"^\s+-\s+(.+?)\s*$", header, re.M)
    return {"current_name": current, "new_decision_saved": saved, "account_references_new_decision": reciprocal,
            "local_name_links_closed": saved and reciprocal and current == NEW_NAME,
            "stale_description": STALE in account,
            "old_history_preserved": (root / "decision-rename.md").read_bytes() == (SEED / "decision-rename.md").read_bytes(),
            "proposed_account_still_proposed": "存在情况: proposed" in (root / "account-proposed.md").read_text(encoding="utf-8"),
            "platform_independent_verification": "unknown", "evidence_quality": "reported"}


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def scenario(name):
    with tempfile.TemporaryDirectory(prefix="dlp-replay-") as tmp:
        root = Path(tmp)
        seed(root)
        original = snapshot(root)
        original_hash = original[ACCOUNT][0]
        if name == "R01_duplicate_conflict":
            shutil.copyfile(root / ACCOUNT, root / "duplicate.md")
            before = snapshot(root)
            report = CHECKER.check(root, FILES + ["duplicate.md"], [], [], closed_set=True, public_examples=True)
            require(any(d["rule"] == "MC02" and d["level"] == "error" for d in report["diagnostics"]), "duplicate not detected")
            require(before == snapshot(root), "conflict check wrote files")
            return {"id": name, "passed": True, "checker_exit": CHECKER.exit_code(report), "unchanged": True}
        if name == "R02_concurrent_change":
            with (root / ACCOUNT).open("a", encoding="utf-8") as handle:
                handle.write("\n并发修改: 虚构第三方更新，必须保留。\n")
            before = snapshot(root)
            outcome = approved_fixture_write(root, original_hash)
            require(outcome["state"] == "conflict" and before == snapshot(root), "concurrent change overwritten")
            return {"id": name, "passed": True, **outcome, "concurrent_bytes_preserved": True}
        if name == "R03_partial_failure":
            original_write = Path.write_text
            def injected_write(path, *args, **kwargs):
                if path == root / ACCOUNT:
                    raise OSError("injected fixture account write failure")
                return original_write(path, *args, **kwargs)
            with patch.object(Path, "write_text", injected_write):
                outcome = approved_fixture_write(root, original_hash)
            recovered = recover(root)
            require(outcome["state"] == "partial" and (root / ACCOUNT).read_bytes() == (SEED / ACCOUNT).read_bytes(), "partial state misreported")
            require(recovered["new_decision_saved"] and not recovered["local_name_links_closed"], "false success")
            return {"id": name, "passed": True, **outcome, "checker_exit": CHECKER.exit_code(check_copy(root)), "recovered": recovered}
        if name == "R04_noop":
            first = check_copy(root)
            second = check_copy(root)
            recovered = recover(root)
            require(original == snapshot(root) and first == second, "no-op changed bytes/mtime/inventory or report")
            require(recovered["current_name"] == OLD_NAME and not recovered["local_name_links_closed"], "approval confused with observation")
            return {"id": name, "passed": True, "checker_exit": CHECKER.exit_code(first), "unchanged_bytes_mtime_inventory": True, "repeat_report_equal": True, "current_name": recovered["current_name"]}
        if name in {"R05_fresh_process", "R06_missing_backlink", "R07_stale_description"}:
            outcome = approved_fixture_write(root, original_hash, omit_backlink=name == "R06_missing_backlink", stale=name == "R07_stale_description")
            require(outcome["state"] == "saved", "fixture setup failed")
            before = snapshot(root)
            report = check_copy(root)
            require(CHECKER.exit_code(report) == 0, "structural fixture should be valid")
            require('当前观察见 ' + NEW_ID in (root / ACCOUNT).read_text(encoding="utf-8").split("---", 2)[1], "saved fixture retained stale frontmatter source")
            require('报告日期: 2026-10-21' in (root / NEW_FILE).read_text(encoding="utf-8"), "observation report date was not explicit")
            if name == "R05_fresh_process":
                result = subprocess.run([sys.executable, "-B", str(Path(__file__).resolve()), "--recover-root", str(root)], capture_output=True, text=True, encoding="utf-8", check=False)
                require(result.returncode == 0, "fresh interpreter probe failed: " + result.stderr)
                recovered = json.loads(result.stdout)
                require(recovered == recover(root) and recovered["local_name_links_closed"], "fresh process did not reconstruct state")
            else:
                recovered = recover(root)
                if name == "R06_missing_backlink":
                    require(not recovered["account_references_new_decision"] and not recovered["local_name_links_closed"], "missing backlink regression hidden")
                else:
                    require(recovered["local_name_links_closed"] and recovered["stale_description"], "stale description regression hidden")
            require(before == snapshot(root), "recovery/check silently repaired fixture")
            protected = ["identity.md", "account-proposed.md", "decision-rename.md"]
            require(all(original[p] == snapshot(root)[p] for p in protected), "protected file changed")
            return {"id": name, "passed": True, "checker_exit": CHECKER.exit_code(report), "recovered": recovered, "read_probe_unchanged": True, "protected_files_unchanged": True}
        raise ValueError("Unknown scenario")


SCENARIOS = ["R01_duplicate_conflict", "R02_concurrent_change", "R03_partial_failure", "R04_noop", "R05_fresh_process", "R06_missing_backlink", "R07_stale_description"]


def run_all():
    return {"format": "dlp-reliability-replay-v1", "baseline": "creator-ledger-2026-10-21",
            "seed_sha256_lf_utf8": {name: hashlib.sha256((SEED / name).read_text(encoding="utf-8-sig").encode("utf-8")).hexdigest() for name in FILES},
            "scenarios": [scenario(name) for name in SCENARIOS],
            "limits": ["Test-only reference writes and injected OSError; not a production writer or real disk/permission failure.",
                       "Fresh Python process is not a restarted Agent Harness session.",
                       "Backlinks and stale prose use fixture-specific oracles, not MC schema validation."]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--recover-root", type=Path, help="Internal fresh-process probe: fixed fictional filenames only")
    modes.add_argument("--prepare-session", type=Path, help="Create a NEW isolated fictional fixture directory; refuses existing paths")
    parser.add_argument("--state", choices=["partial", "saved", "stale"], default="partial", help="State for --prepare-session only")
    args = parser.parse_args()
    if args.prepare_session:
        root = args.prepare_session.absolute()
        # Exclusive creation, no parent creation, deletion, overwriting or migration.
        try:
            root.mkdir(exist_ok=False)
        except OSError:
            parser.error("Fixture destination must be new and its parent must already be writable; existing paths are never overwritten")
        seed(root)
        expected_hash = hashlib.sha256((root / ACCOUNT).read_bytes()).hexdigest()
        if args.state == "partial":
            (root / NEW_FILE).write_text(new_decision(), encoding="utf-8", newline="\n")
        else:
            approved_fixture_write(root, expected_hash, stale=args.state == "stale")
        result = {"prepared_root": str(root), "files": FILES + [NEW_FILE], "fixture_state": args.state,
                  "note": "Synthetic files only; give a fresh Agent the file allowlist, not expected answers or prior chat."}
    else:
        result = recover(args.recover_root) if args.recover_root else run_all()
    print(json.dumps(result, ensure_ascii=True, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
