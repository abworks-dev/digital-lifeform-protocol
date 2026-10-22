"""Offline topic-routing checks for the two explicit platform guides.

Only navigation labels, links and preserved headings are tested, not semantic
coverage, current platform policy, model behavior or real platform operations.
"""
import unittest
from unittest.mock import patch

import test_douyin_delivery as navigation


TOPICS = [
    "账号方案、接入与主页", "内容发布与日常运营", "安全维护与事件", "协作权限与退出",
    "账号生命周期", "权利、投诉与隐私", "规则影响复核", "规则与证据",
]
ENTRIES = ["platforms/xiaohongshu/README.md", "platforms/douyin/README.md"]
DOCUMENTS = [
    "platforms/README.md", *ENTRIES,
    "platforms/xiaohongshu/guide.md", "platforms/xiaohongshu/lifecycle.md",
    "platforms/xiaohongshu/security.md", "platforms/xiaohongshu/collaboration.md",
    "platforms/xiaohongshu/rights-and-privacy.md", "platforms/xiaohongshu/policy-review.md",
    "platforms/douyin/guide.md", "platforms/douyin/security.md",
    "platforms/douyin/collaboration.md", "platforms/douyin/lifecycle.md",
    "platforms/douyin/rights-and-privacy.md", "platforms/douyin/policy-review.md",
    "docs/ROADMAP.md", "tests/README.md",
]


def table(path, section):
    """Read only the simple, pipe-free-cell table used by these explicit pages."""
    text = (navigation.ROOT / path).read_text(encoding="utf-8")
    section_text = text.split("## " + section + "\n", 1)[1].split("\n##", 1)[0]
    return [[cell.strip() for cell in line.strip().strip("|").split("|")]
            for line in section_text.splitlines() if line.startswith("|")]


class PlatformNavigationTests(unittest.TestCase):
    def test_shared_topics_match_platform_order(self):
        shared = table("platforms/README.md", "统一专题导航与职责")
        self.assertEqual([row[0] for row in shared[2:]], TOPICS)
        for path in ENTRIES:
            with self.subTest(path=path):
                rows = table(path, "任务导航")
                self.assertEqual(rows[0], ["专题", "阅读入口", "当前覆盖", "未覆盖／待核实"])
                self.assertEqual([row[0] for row in rows[2:]], TOPICS)
                self.assertTrue(all(len(row) == 4 and all(row) for row in rows[2:]))

    def test_each_topic_routes_to_existing_content(self):
        for path in ENTRIES:
            for row in table(path, "任务导航")[2:]:
                with self.subTest(path=path, topic=row[0]):
                    self.assertTrue(navigation.INLINE.search(row[1]), row)
        with patch.object(navigation, "DOCUMENTS", DOCUMENTS):
            counts, problems = navigation.check_navigation()
        self.assertEqual(counts["documents"], len(DOCUMENTS))
        self.assertEqual(problems, [])

    def test_douyin_existing_section_headings_remain(self):
        text = (navigation.ROOT / "platforms/douyin/guide.md").read_text(encoding="utf-8")
        for heading in [
            "## 建档与唯一主档", "### 本人创建与主页检查单", "## 发布前检查",
            "## 安全与恢复条件", "## 协作与退出", "## 更名转型暂停恢复与注销",
            "## 冒用搬运投诉与隐私", "## 规则变化复核",
        ]:
            self.assertIn(heading + "\n", text)

    def test_topic_files_align_and_legacy_sections_redirect_once(self):
        expected = ["guide.md", "guide.md", "security.md", "collaboration.md",
                    "lifecycle.md", "rights-and-privacy.md", "policy-review.md", "rules.md"]
        for path in ENTRIES:
            files = sorted(p.name for p in (navigation.ROOT / path).parent.glob("*.md"))
            self.assertEqual(files, sorted({"README.md", *expected}))
            for row, filename in zip(table(path, "任务导航")[2:], expected):
                with self.subTest(path=path, topic=row[0]):
                    links = list(navigation.INLINE.finditer(row[1]))
                    self.assertTrue(links, row)
                    targets = [(m.group(1) or m.group(2)).split("#")[0] for m in links]
                    self.assertEqual(targets[0], filename)
                    # Existing cross-topic routes are intentional, not duplicate ownership.
                    allowed = {filename}
                    if path == ENTRIES[0] and row[0] == TOPICS[0]:
                        allowed.add("lifecycle.md")
                    if path == ENTRIES[0] and row[0] == TOPICS[2]:
                        allowed.add("guide.md")
                    self.assertTrue(set(targets) <= allowed, row)
        text = (navigation.ROOT / "platforms/douyin/guide.md").read_text(encoding="utf-8")
        redirects = {
            "安全与恢复条件": "security.md", "协作与退出": "collaboration.md",
            "更名转型暂停恢复与注销": "lifecycle.md",
            "冒用搬运投诉与隐私": "rights-and-privacy.md", "规则变化复核": "policy-review.md",
        }
        for heading, filename in redirects.items():
            section = text.split("## " + heading + "\n", 1)[1].split("\n## ", 1)[0]
            links = [m.group(1) or m.group(2) for m in navigation.INLINE.finditer(section)]
            self.assertEqual(links, [filename + "#" + heading])
            self.assertIn("不维护第二份正文", section)
            destination = (navigation.ROOT / "platforms/douyin" / filename).read_text(encoding="utf-8")
            self.assertIn("## " + heading + "\n", destination)

    def test_douyin_migrated_topics_retain_explicit_boundaries(self):
        # Selected literal regressions, not a semantic completeness/permission proof.
        checks = {
            "security.md": ["3–7个工作日", "不是全部找回／申诉的SLA", "更不自动恢复撤回／过期委托"],
            "collaboration.md": ["不能把“我批准了”当平台许可", "用户批准、平台许可、实际技术权限",
                                 "本地 revoked 不证明平台权限解除"],
            "lifecycle.md": ["不可登录不改成 proposed", "申请≠展示生效", "同手机号新号不恢复旧内容",
                             "十五个工作日反馈／回复", "逝者事项不等于交接"],
            "rights-and-privacy.md": ["侵权通知转送被举报方", "核查后十五个工作日内反馈投诉举报",
                                      "验证身份后十五个工作日内回复", "不能撤回撤销申请", "不建隐藏映射"],
            "policy-review.md": ["不覆盖旧批次", "不改机器报告来制造通过", "HTTP 200、哈希不变不是现行证明",
                                 "不滚动核验日期", "呼吁／鼓励改为硬禁"],
        }
        for filename, literals in checks.items():
            text = (navigation.ROOT / "platforms/douyin" / filename).read_text(encoding="utf-8")
            with self.subTest(filename=filename):
                self.assertIn("rules.md", text)
                self.assertIn("unknown", text)
                for literal in literals:
                    self.assertIn(literal, text)

    def test_xiaohongshu_legacy_navigation_headings_remain(self):
        text = (navigation.ROOT / "platforms/xiaohongshu/guide.md").read_text(encoding="utf-8")
        for heading in [
            "### 7.1 旧号接入与历史检查", "### 7.2 恢复条件变化、商务诈骗与安全失陷",
            "### 7.3 协作权限及退出", "### 7.4 更名、转型、暂停、恢复与注销",
            "### 7.5 冒用、作品搬运与投诉隐私", "### 7.6 规则变化对现有账号的影响复核",
        ]:
            self.assertIn(heading + "\n", text)


if __name__ == "__main__":
    unittest.main()
