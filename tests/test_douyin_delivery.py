"""Delivery-specific offline checks; not a platform or authorization verifier.

Only the explicit public delivery and the synthetic demo directory are inspected.
Navigation checks inline Markdown links and simple headings (MC07 slug approximation),
not a browser renderer, external URLs, HTML or a general Markdown grammar.
"""
from pathlib import Path
import re
import sys
import unittest
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import check_records as checker

RECORDS = [
    "examples/douyin-ledger/account-proposed.md",
    "examples/douyin-ledger/decision-confirm-proposal.md",
    "examples/douyin-ledger/review-proposal.md",
]
DOCUMENTS = [
    "README.md", "docs/PROJECT.md", "docs/ROADMAP.md", "platforms/README.md",
    "workflows/maintain-creator-ledger.md", "workflows/publish-and-commercialize.md",
    "skills/creator-account-ledger/SKILL.md",
    "platforms/douyin/README.md", "platforms/douyin/rules.md", "platforms/douyin/guide.md",
    "platforms/douyin/security.md", "platforms/douyin/collaboration.md",
    "platforms/douyin/lifecycle.md", "platforms/douyin/rights-and-privacy.md",
    "platforms/douyin/policy-review.md",
    "examples/douyin-ledger/README.md", *RECORDS, "examples/douyin-validation.md",
    "evidence/platform-sources/2026-10-22-douyin/review.md", "tests/README.md",
]
INLINE = re.compile(r'(?<!!)\[[^\]\n]+\]\((?:<([^>]+)>|([^\s)]+))\)')


def body(path):
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    start = 0
    if lines and lines[0] == "---":
        start = lines.index("---", 1) + 1
    return checker._body(lines, start)


def check_navigation():
    """Do not recurse: targets are opened only to check the requested heading."""
    counts = {"documents": len(DOCUMENTS), "local_links": 0, "anchors": 0,
              "external_skipped": 0}
    problems = []
    for name in DOCUMENTS:
        path = ROOT / name
        for line, text in body(path):
            for match in INLINE.finditer(text):
                raw = match.group(1) or match.group(2)
                url = urlsplit(raw)
                if url.scheme or url.netloc:
                    counts["external_skipped"] += 1
                    continue
                counts["local_links"] += 1
                target = (path.parent / unquote(url.path)).resolve() if url.path else path
                try:
                    target.relative_to(ROOT)
                except ValueError:
                    problems.append((name, line, "outside-public-root", raw))
                    continue
                if not target.is_file():
                    problems.append((name, line, "missing-file", raw))
                    continue
                if url.fragment:
                    counts["anchors"] += 1
                    headings, _ = checker._headings(body(target))
                    if unquote(url.fragment) not in headings:
                        problems.append((name, line, "missing-anchor", raw))
    return counts, problems


class DouyinDeliveryTests(unittest.TestCase):
    def test_explicit_synthetic_records_mc_subset(self):
        report = checker.check(ROOT, RECORDS, [], [], closed_set=True,
                               public_examples=True, baseline="douyin-demo-2026-10-22")
        self.assertEqual(report["summary"], {"error": 0, "warning": 0, "unchecked": 0},
                         report["diagnostics"])

    def test_plan_confirmation_does_not_create_platform_facts(self):
        account = (ROOT / RECORDS[0]).read_text(encoding="utf-8")
        for literal in ("status: confirmed", "confirmed_by: fictional-user",
                        "confirmed_at: 2026-10-22", "存在情况: proposed",
                        "operational_state: preparing", "平台账号 ID: unknown",
                        "主页: unknown", "当前名称: unknown", "实际所有者: unknown",
                        "身份 ID: unknown"):
            self.assertIn(literal, account)
        self.assertIn("reported", account)
        self.assertIn("独立平台验证为 unknown", account)
        self.assertIn("暂不商业化", account)
        self.assertIn("不创建 identity 记录或隐藏映射", account)

    def test_demo_has_one_main_record_and_review_retains_uncertainty(self):
        demo = ROOT / "examples/douyin-ledger"
        files = sorted(p.name for p in demo.glob("*.md"))
        self.assertEqual(files, ["README.md", "account-proposed.md",
                                 "decision-confirm-proposal.md", "review-proposal.md"])
        texts = [(ROOT / name).read_text(encoding="utf-8") for name in RECORDS]
        self.assertEqual(sum("\ntype: account\n" in text for text in texts), 1)
        self.assertIn("decision-douyin-demo-confirm-proposal", texts[0].split("---")[1])
        self.assertIn("account-douyin-demo-proposed", texts[1].split("---")[1])
        for token in ("account-douyin-demo-proposed", "decision-douyin-demo-confirm-proposal",
                      "proposed", "preparing", "reported", "unknown"):
            self.assertIn(token, texts[2])

    def test_changed_delivery_navigation(self):
        self.assertEqual(sorted(path.name for path in (ROOT / "platforms").glob("*.md")),
                         ["README.md"])
        for platform in ("xiaohongshu", "douyin"):
            self.assertTrue((ROOT / "platforms" / platform / "README.md").is_file())
        _, problems = check_navigation()
        self.assertEqual(problems, [])


if __name__ == "__main__":
    unittest.main()
