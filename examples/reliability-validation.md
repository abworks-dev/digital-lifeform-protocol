# 第二批可靠性验证报告

日期：2026-10-21。对象：[只读检查器](../tools/check_records.py)、[测试与复跑入口](../tests/README.md)及公开虚构台账。此报告追加第二批证据，不改写[旧走查报告](creator-ledger-validation.md)，不把参考测试升级为生产维护、安全或兼容认证。

## 1. 环境与基线

- 实际解释器：CPython **3.12.14**，MSC v.1944 64 bit AMD64；Windows 11 / 10.0.26300。独立执行者另记录 PowerShell 7.6.7。早期任务说明曾误称指定解释器为 3.11.9，实测后纠正；本报告不算作 Python 3.11 验证。
- Git HEAD：`41e054795b2a0902a71a4d43aea21f999dc400d4`，叠加现存及本批未提交/未跟踪工作树；HEAD **不能单独定位本批源码**。未提交、推送或创建发布版本。
- 检查器：`check_records 0.1.0`；Python 标准库，无新增 pip 依赖。最低版本声明 3.11+，本次完整套件只在上述实际版本执行，未做版本矩阵。
- 执行宿主：DeepSeek Harness Web GUI；宿主精确版本和实际提供商/模型路由未独立核验。不据上下文声明认证模型版本。
- 只读公开文件；写操作仅在系统临时目录中的合成副本。未读取真人台账或凭据，未联网、安装/配置宿主、启动服务或操作真实平台。

公开四记录的 LF 规范化 UTF-8 指纹由[固定预期](../tests/fixtures/replay-expected.json)的 `seed_sha256_lf_utf8` 保存；旧报告指纹另在[历史证据锁定](../tests/fixtures/historical-evidence.json)。跨系统换行转换与本机字节不变性分开判断。

本次源码字节 SHA-256（不是已发布版本；可用于辨别收到的工作树是否相同）：

| 文件 | SHA-256 |
|---|---|
| [检查器](../tools/check_records.py) | `827333e0ae32050edac046ee0b71f56b12d0313bc28ba900bd644f3931111620` |
| [复跑程序](../tests/replay_scenarios.py) | `07dab3355fdd5bc7fae59450795d052cc2bbfc2bb2f1196e644eaefd87cf37c7` |
| [检查器测试](../tests/test_check_records.py) | `4a1686057d183162c9db48df6990582dd4ea28e1f654006402a1f40b0f5f83e7` |
| [可靠性测试](../tests/test_reliability.py) | `1f05af45e50732c7376a5c94b58578de0e5a174936948373a72f1a96827e3f7b` |
| [测试支持](../tests/support.py) | `74b1140c9a253eff7a470bcbd654c028f565271e23203d24010ae84e61179622` |
| [声明样例](../tests/fixtures/cases.json) | `9f2c8bb37776d251557b276b8bf626b9bb546135cf0efda973c41302868f2359` |
| [固定预期](../tests/fixtures/replay-expected.json) | `5c64fc8529d0d78f9243170e4f1682683d3d5aca1979a2cc351dfbc44838a08f` |

## 2. 父执行者与独立执行者复跑

两位执行者分别从仓库根目录，用同一指定解释器执行下列命令；`python` 表示各自已核实的解释器，不要求系统 PATH 中同名程序恰好正确。

```text
python --version
python -B -m unittest discover -s tests -v
python -B tests/replay_scenarios.py
python -B tools/check_records.py --root . --record examples/creator-ledger/identity.md --record examples/creator-ledger/account-existing.md --record examples/creator-ledger/account-proposed.md --record examples/creator-ledger/decision-rename.md --closed-set --public-examples --baseline creator-ledger-2026-10-21 --format json
```

| 项目 | 父执行者最终结果 | 独立执行者最终结果 |
|---|---|---|
| 单元/回归套件 | 退出 0；28 方法，27 通过、1 skip | 同左；未修改源码、预期或样例 |
| 独立复跑 JSON | 退出 0；7 场景，固定预期比较通过 | 退出 0；额外捕获 CLI stdout 后解析比较，`CLI_JSON_EQUALS_FIXED_EXPECTED=True`，7 场景 |
| 四主档直接检查 | 退出 0；error 0 / warning 1 / unchecked 0 | 相同退出码、计数与诊断 |
| 旧报告保护 | 固定指纹断言通过 | 相同断言通过；另审阅旧失败/未执行段落仍在 |

唯一 skip：`test_symbolic_link_is_not_followed`，原因原文 `OS did not permit creation of test symlink`。本机硬链接别名探针实际通过；**不把符号链接探针写成已执行通过**。四主档唯一提醒为拟议草稿的 `confirmed_at: unknown`，规则 MC05 / `unknown_date`；这不是有效确认日期或平台已存在的证明。

18 个声明式输入作为 subtests 运行，不把它们另加成 18 个测试方法。标准输出、错误输出和工具事件留在本次会话；本仓库提供可重跑源码、固定预期与汇总，不附完整独立环境镜像或全部原始会话导出。

## 3. 七场景的实际含义

| 场景 | 实际观测 | 不能据此声称 |
|---|---|---|
| R01 重复 ID | checker 退出 1；检查前后文件不变 | 自动合并或完整 C02 多轮澄清已实现 |
| R02 并发冲突 | 顺序模拟先修改正文，参考动作发现前置哈希不同；两个目标均未写，并发字节保留 | 产品/宿主已有哈希守卫、真实竞态安全或事务 |
| R03 部分失败 | decision 写入后，在主档 `write_text` 入口注入 OSError；已写/未写分列，旧主档保留；checker 可退出 0，但 `local_name_links_closed=false` | 结构通过等于全部保存，或真实磁盘满/ACL/写到一半故障已测 |
| R04 无变更 | 两次报告相同；普通文件字节哈希、mtime_ns、相对文件清单不变；批准目标未覆盖当前观察 | atime、空目录、系统审计/杀毒、模型历史均无变化 |
| R05 新进程 | 实际启动新 Python 解释器，从文件恢复名称与历史；保护文件不变 | 真实 Agent Harness 关闭重启、记忆/缓存关闭或跨宿主兼容 |
| R06 漏反链回归 | checker 仍可退出 0；样例专用判据发现缺主档到新决定的反向 links，局部变更未闭环 | MC06 已能检查全部业务反向依赖 |
| R07 陈旧正文回归 | `local_name_links_closed=true` 与 `stale_description=true` 同时出现；不静默修复 | 名称/引用闭合就代表所有正文同步或平台更名完成 |

[参考写入与恢复代码](../tests/replay_scenarios.py)只服务固定夹具：顺序写入不是产品维护引擎；恢复 oracle 的名称正则、反链匹配和固定陈旧短语不是通用语义判断。其 `reported` / 平台 `unknown` 输出是该夹具的固定预期，不证明任意正文证据能被自动解析。真正的语义解释另由下述独立 Agent 只读检查。

## 4. 无继承上下文的文件恢复

初轮分别给两个独立、不继承父聊天历史的执行者五文件白名单，只提供主规范及[统一问题](../tests/README.md#5-不带聊天历史的-agent-检查人工复跑)，不提供 expected、恢复代码或旧回答：

- **部分状态快照**：执行者指出旧主档仍为“纸舟整理札记”/O1，而独立 O2 已记录新名“纸舟数字整理”；主档名称/来源和反向 links 尚未更新，不能说全部保存。它明确区分最新报告与主档当前值、reported 与平台 unknown，第二号只有 proposed 方案。
- **陈旧说明快照**：执行者读到主档名称/观察已为新名/O2、双向 links 已在，同时指出“新名未成为当前观察”的陈旧句和元数据来源仍指 O1；没有把局部更新称为所有正文/平台全部完成，也未改未获准字段。

该盲读暴露了初始**合成夹具**两处额外歧义：O2 正文没有明示报告日期、参考动作未同步主档 frontmatter source。父执行者仅修正夹具生成器并加断言，保留初始快照、旧公开案例及旧报告。另将过宽的 oracle 键 `change_complete` 改成 `local_name_links_closed`，并修正无效 UTF-8 测试原先误用的字面反斜杠字节。固定预期只同步键名，R03 未完成、R06 漏反链、R07 陈旧、四基准指纹和 reported/unknown 不变；独立执行者审阅后重跑确认未借重写预期掩盖原缺陷。

最终纠正后的两个新合成快照，另由不继承上述回答的新执行者复读，业务依据仍严格限于每案五文件：

| 最终输入 | 新执行者原答要点 | 父执行者核对 |
|---|---|---|
| partial | 最新报告为 2026-10-21 reported 新名；O2 已在，旧主档仍指 O1 且缺反向链接；不能称整项保存/平台更名成功 | 与实际文件一致；五文件字节、mtime_ns、相对文件清单前后相同 |
| stale | O2 名称、来源和双向 links 已保存；指出矛盾陈旧句，保留旧核对日适用范围；不称整份正文或平台闭环 | 与实际文件一致；五文件同项不变 |

两案均将平台独立验证/生效时间保留 unknown，第二号仅 proposed、无创建证据；没有以“无证据”证明平台上绝对不存在。初轮两份五文件快照也复核为字节/mtime/清单不变，总计四个独立快照、20 个文件。执行者声明与工具事件未见写入、联网或扩读；这仍不是系统强制只读的证明。

这些是**同一宿主中的无继承上下文文件恢复**，不是关闭再启动整个宿主、记忆/缓存清理、自动 Skill 发现或跨宿主测试。初始快照与最终纠正后的生成器分别记录，不混写成相同输入。

## 5. 收尾静态检查

- 本批更新的 8 份入口/规范/测试文档中，123 个本地文件链接目标存在；这项检查不验证全部锚点、外部网址或正文语义。MC07 的受支持导航/锚点行为另由单元测试验证。
- `git diff --check` 无错误；原工作树的 LF/CRLF 转换提示仍在，不视为失败。现存未提交工作保留；旧报告指纹断言通过，未以本轮结果覆盖历史。

## 6. 尚未验证与完成边界

- 未执行：真实宿主重启/自动 Skill 发现、强制读写权限、真实写到一半/终止/磁盘或权限故障、第二宿主、真实账号/平台核验、私人接入、真人独立试用及长期维护成本。
- C02 同平台可靠 ID 的完整多轮消歧、全套 C01–C10 / A / PG 未因此全部通过；旧报告中的未执行项保留原文，由各自后续证据补充，而非改写过去。
- 检查器只对显式输入、受支持解析和确定性规则给出结果；不读未列入目标、不检查真实授权/隐私/平台事实，不建立业务 schema 稳定承诺。退出 0 不是语义或安全认证。
- 本批交付：可独立复跑的只读工具、正反样例、故障/无变更/恢复回归、固定预期与诚实分层的结果。自动维护、安装器、运行监控、事务、迁移或外部账号动作仍未提供。
