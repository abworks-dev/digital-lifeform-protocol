# 抖音公开来源首次审阅｜2026-10-22

本批仅匿名公开调研。查阅时区 Asia/Shanghai；机器 UTC 时间为 2026-10-21T16:06:38–16:08:18，对应本地 2026-10-22。没有覆盖 2026-10-21 旧批次、改写旧审阅或启用调度；**候选基线，用户未批准**。未处理私人材料。

## 来源与人工结论

具体 URL、发布主体、产品／地区／账号／动作、版本／生效／查阅日期、判断和复核触发集中维护在 [抖音规则与证据](../../../platforms/douyin/rules.md)，本页仅记录这次工具结果和人工差异，不复制另一套权威规则。

| 来源 | 机器报告 | 人工实际读取 | 限制与处理 |
| --- | --- | --- | --- |
| DY-S01 用户协议 | baseline-needed | 连续提取 1.2–14.7，非全文 | 缺导语、日期、1.1 及结尾；可支撑限定条款，不证明整份现行；搜索日期未采纳为正文事实 |
| DY-S02 AI 公告 | baseline-needed | 完整提取正文及五问 Q&A | 三张内嵌图片未读；2025-09-01 试行生效可读，当前 UI 未测 |
| DY-S03 社区公约 | baseline-needed | 指定段落：总则／倡导、商业相关、第 21／23／25、32–39 项、附则 | 未逐字精读所有章节；附则生效日 2022-09-13 不代表 2026 所有修订现行 |
| DY-S04 注销须知 | **unreadable / shell-or-challenge** | 完整提取的“重要”至第 7 条正文 | 1.1 的“账号安全验证”疑似触发启发式误报；保留原报告，不重写成通过。实际流程、日期和账号条件仍 unknown |

没有网络访问失败、登录页或验证码；有提取不完整、图片未读和机器判读异常。商业利益披露普通号细则经两次定向官方搜索未取得适用完整一手正文；不借 TikTok、第三方教程、小红书或专项平台规则补齐许可。

所有报告 `origin_http_status: unknown`、`authority_updated: false`、`requires_human_review: true`。reader 200、无错误返回或哈希不变不证明现行；首次抓取不会自行成为已批准基线。**本次没有可用的已批准历史文本做有效性或版本变更比较**。

## 命令与本地材料

经 agent-reach 搜索路径 `mcporter call exa.web_search_exa query="…" numResults=5` 发现候选，再用仓库现有工具逐个显式 URL 抓取。以下为等价复跑形式（原抓取未传 `-B`）；`<url>` 分别取规则页四项公开 URL（均含公开查询参数），没有从私人文档发现链接：

```powershell
python -B tools/check_source_changes.py --source <source-id> --url <url> --allow-public-query --fetch --capture evidence/platform-sources/2026-10-22-douyin/<stem>.txt --report evidence/platform-sources/2026-10-22-douyin/<stem>.json
```

| source-id | stem | 报告生成退出码 |
| --- | --- | --- |
| douyin-user-agreement-20261022-r1 | user-agreement-r1 | 0 |
| douyin-ai-label-20261022-r1 | ai-label-r1 | 0 |
| douyin-community-20261022-r1 | community-r1 | 0 |
| douyin-delete-notice-20261022-r1 | delete-notice-r1 | 0，仍为 unreadable，不等于规则通过 |

原始 txt 和机器 json 仅在本批本地目录，已逐一由 `git check-ignore` 确认忽略；本页不以可版本化链接强制要求它们在其他克隆存在。不新增 manifest、数据库、外部归档或自动备份。工具独占创建输出、先 capture 后 report，非事务；本批八份输出均存在。不会将第三方全文加入 Git 或自动公开。

## 审阅后下一步

- 可支持本人手动的方案、主档、内容／AI 基础检查及生命周期边界；不能支持注册／发布／商业交易／协作权限／恢复／注销结果声明。
- 高影响动作前本人重新核对完整适用正文、当前账号条件和产品入口；缺失部分保持 unknown；来源变更应人工审阅后再决定更新文档。
- 检测器假阳性作为局限保留。本轮不为单个关键词改通用工具，避免扩大误读风险；若后续多来源证明必要，再增独立回归证据评估最小修正。
