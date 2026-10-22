# 可靠性复跑（第二批，实验版）

目标：另一位执行者在同一公开基线下，能重跑检查器与故障样例，比较退出码、诊断、文件不变性与恢复结果。只用合成数据和[公开虚构台账](../examples/creator-ledger/README.md)，不读私人目录，不联网、不安装宿主。业务语义仍以[记录约定](../docs/RECORDS.md)及[维护流程](../workflows/maintain-creator-ledger.md)为准。

## 1. 环境与两个复跑命令

需要 Python **3.11+** 标准库，无 pip 依赖。先核对实际解释器版本，在仓库根目录执行；`python` 替换为本机可信解释器路径即可。`-B` 避免生成字节码缓存。本项目不附自动安装器。

```text
python --version
python -B -m unittest discover -s tests -v
python -B tests/replay_scenarios.py
```

- 单元测试使用系统临时目录生成输入、保存副本和注入故障，退出时清理自己创建的临时目录；**测试程序会写测试副本，检查器本身不写**。
- 第二条命令成功退出 0；遇到不支持创建符号链接或硬链接的系统，会明确 skip 对应真实文件别名探针，不能写成全部通过。用例数和实际 skip 见本次输出，不固定推断其他机器结果。
- 第三条输出稳定 JSON，无时间戳/临时绝对路径。其全部内容由[预期结果](fixtures/replay-expected.json)逐项比较；这项比较也包含在单元测试中。不把“失败样例得到预期非零码”误认为测试失败。
- 不自动更新预期结果。若结果不同，先读差异：是代码缺陷、平台限制还是公开基线改变？批准变更后另行审阅预期，不用重生成 golden 掩盖回归。
- 报告记录解释器/系统、框架提交或未提交状态、checker 版本、命令、退出码、skip、场景 JSON 是否相同。源文件指纹用 LF 规范化 UTF-8，避免 Git 换行转换造成不可比；无变更断言仍在**本次实际文件的字节、mtime_ns 和目录清单**上比较。

## 2. 直接使用只读检查器

[检查器](../tools/check_records.py)要求显式根目录和逐文件白名单；没有默认发现、递归、沿 ID 或链接补读、联网、自动修复、报告落盘选项。根目录只供路径解释，不表示获准扫描整个目录。

```text
python -B tools/check_records.py --root . --record examples/creator-ledger/identity.md --record examples/creator-ledger/account-existing.md --record examples/creator-ledger/account-proposed.md --record examples/creator-ledger/decision-rename.md --closed-set --public-examples --baseline creator-ledger-2026-10-21 --format json
```

此命令的公开四记录基线预期：退出 **0**，`error=0, warning=1, unchecked=0`；提醒来自草稿确认日期的 unknown，不代表有效日期。`--baseline` 只是调用者标签，工具不替你验证版本；源内容指纹另由复跑程序输出。

输入分类：`--record` 是实际记录；`--template` 是未填写模板（不计实际 ID）；`--document` 是导航/Skill（不按业务 frontmatter 校验）。三者均可重复。`--closed-set` 只声明**记录 ID 引用集合**封闭，不把整个根目录变成已授权输入。输入缺失/解析不完整时，即使声明封闭也不能确定缺目标，相关引用保持未检查。

| 退出码 | 含义 |
|---|---|
| 0 | 本次支持范围无错误、无未检查；可以有 unknown/模板提醒，不证明内容真实或整个工作空间通过 |
| 1 | 有确定性规则错误；仍须阅读报告中并存的提醒与未检查项 |
| 2 | 没有确定规则错误，但输入/语法/范围不足，或命令行参数错误；**不是通过** |

JSON 含 `checker/version`、调用者基线、显式 `scope`、`closed_set`、按位置排序的诊断、三类计数及限制。诊断不回显字段值、正文或绝对根路径；调用者仍不能把秘密放入文件名/基线标签。工具不是秘密扫描器，也不是强制沙箱；系统 atime、审计、杀毒或模型/会话留存不在字节/mtime 断言保证内。

### 支持的解析子集

- UTF-8（可带 BOM）、LF/CRLF、平面 frontmatter 文本值、单引号及 JSON 兼容双引号、行尾注释、links 的 `[]`/单行列表/块列表。
- plain `null`/`~` 和空值为空，不当 unknown；未加引号的布尔/数字按**文本子集**处理，不做完整 YAML 隐式类型推断。日期须满足既有规则。复杂 YAML、标签、锚/别名、多行值或重复键不会默许通过。
- 导航仅支持简单 Markdown 行内链接/尖括号目标、简单 ATX/setext 标题及重复标题后缀；代码块/行内代码不作链接。复杂或引用式 Markdown 明示未检查，外部目标不访问，未列入输入的本地目标也不读取。完整渲染器兼容不是目标。
- 已观察到的符号链接、Windows reparse point、越根路径和物理文件别名会被拒绝或标输入问题；并发替换路径等竞态不能靠这个工具提供 OS 级隔离。

## 3. 有效与失败样例

[样例数据](fixtures/cases.json)包含 18 个声明式输入：有效 draft/confirmed、unknown 提醒、缺字段/空值、非法 ID/type/status、确认缺失、非法日历日/日期格式、公开确认主体不符、links 不是列表、unknown ID、闭集断引用、开集范围不足。测试将每个样例在新临时目录展开成实际 Markdown，再比较退出码和规则等级；样例文件是**测试生成说明**，不是新业务 schema。

[检查器测试](test_check_records.py)另覆盖双向可定位引用、重复 ID、同名不同 ID、不新增 ID 正则、模板/Skill 分类、BOM/CRLF/引号、重复键与不支持语法、输入拒绝、导航/锚点、显式范围之外不调用文件读取、稳定报告、诊断脱敏、CLI 与无变更。每项有可观察断言，而不是让模型自称通过。

## 4. 故障与恢复场景

执行角色：本地测试者；起点：每个场景各自复制同一四记录基线到独立临时目录。步骤与判据由[复跑程序](replay_scenarios.py)执行，[回归测试](test_reliability.py)比较固定输出。全部写操作只在测试副本中，**参考写入器不是产品的维护引擎或事务实现**。

| 场景 | 目的、操作步骤 | 可观察预期 |
|---|---|---|
| R01 重复冲突 | 复制一个相同 ID 的主档 → 运行闭集检查 → 比较文件 | MC02 错误、checker 退出 1，检查前后字节/mtime/清单不变，不合并 |
| R02 并发冲突 | 记录前置哈希 → 另一测试动作追加正文 → 参考动作核对哈希 | 先前提议已过时，参考动作不保存 decision/主档，并发修改保留；不宣称宿主已实现哈希守卫 |
| R03 部分失败 | 允许参考动作保存 decision → 在主档写入点注入 OSError → 从实际文件恢复 | 已写/未写分列，主档字节仍是旧值、新决定仍在、不报全部完成、不自动回滚。结构可以通过，场景判据仍识别未完成 |
| R04 无变更 | 对四记录重复检查并读取名称 → 比较报告、内容/mtime/清单 | 相同报告、退出 0、所有文件无变更；批准目标不能变成当前观察 |
| R05 新进程恢复 | 保存参考变更 → 启动不带历史的新 Python 解释器 → 只读固定文件 | 恢复当前名称、旧历史、reported/unknown 和拟议号；三份保护文件不变。**不是宿主重启测试** |
| R06 漏反向链接回归 | 参考动作刻意漏主档到新 decision 的反向 links → 检查并读文件 | MC 结构仍可能退出 0；样例专用断言必须识别变更未闭环，不用通用 schema 虚报已能检测所有反向链接 |
| R07 陈旧说明回归 | 更新观察却保留矛盾品牌进展句 → 检查并读文件 | 样例专用断言识别陈旧说明；不擅改未获准字段，保护历史与其他主档 |

复跑 JSON 的 `local_name_links_closed` **只表示样例内名称、决定存在与反向引用闭合**，不表示所有正文已同步，更不表示平台更名完成。R07 即使此值为 true，仍必须同时报告 `stale_description=true`。合成 O2 明示报告日期，参考变更同步获准的主档来源；旧公开案例与旧报告保持原文。

R06/R07 来自[旧报告的实际缺陷](../examples/creator-ledger-validation.md#发现修正及剩余限制)，只重现机制，不改旧副本或旧报告。R02 对应“写前观察并核对”保护；旧报告的宿主“未重读而拒绝编辑”并非本项目通用机制，**未声称复现了该宿主控制**。[历史证据指纹](fixtures/historical-evidence.json)锁定旧报告文本；追加新结果不抹掉旧的失败/未执行记载。

## 5. 不带聊天历史的 Agent 检查（人工复跑）

新进程测试不能代替 Agent 会话检查。下列步骤可由另一位测试者对新建独立会话/不继承上下文的执行者复跑；不需真实台账或账号。先确认该 Agent 对合成副本只读，允许的核心规范也逐项指定。

1. 测试者选一个**尚不存在**的临时目录，用下列命令建立副本；此模式明确会写测试夹具，遇到已有路径拒绝覆盖。`<new-directory>` 要替换为实际路径，不能照抄占位符。`--state` 可选 `partial`、`saved`、`stale`，每次使用不同新目录。

   ```text
   python -B tests/replay_scenarios.py --prepare-session <new-directory> --state partial
   ```

2. 保存五个固定文件的哈希/mtime。新建无旧聊天历史的 Agent，只给实际根路径、五文件白名单、[记录约定](../docs/RECORDS.md)及[维护流程](../workflows/maintain-creator-ledger.md)。不要给旧回答、预期答案或自动恢复程序输出；不要沿外部链接扩读。
3. 使用同一提问：**“只根据这五个文件，当前名称最近观察是什么、依据和日期是什么？更名变更是否完成？哪些已保存、哪些尚未闭环？第二个号是否已存在？区分本地事实、平台事实、未知和矛盾。不要修改或修复文件。”**
4. 测试者将回答与该副本的实际文件及独立的 `--recover-root <directory>` 结果对照，人工核对来源。`recover` 是固定样例专用 oracle，不是通用语义检查器，不证明模型真实遵循范围。
5. 比较前后哈希/mtime、保留工具事件、回答和人工评分：partial 不得宣称主档已更新；saved 不把 reported 升成平台 verified；stale 必须指出矛盾且不擅改。旧决定和拟议号仍须正确解释。失败按实际记载，不能改输入或预期来宣布通过。

新子代理可验证“无继承上下文的文件恢复”，**不等于关闭再启动宿主、关闭记忆/缓存或跨宿主兼容**。宿主版本、实际模型路由、安全控制未知时明确标未知。C02 同平台可靠 ID/同名的完整多轮澄清、真实故障与全套 A/PG 及跨宿主验收仍另测；本批不能把这些升级为通过。

## 第三批：固定基线与原生宿主复测

[跨宿主报告](../examples/cross-harness-validation.md)提供两宿主版本、逐项结果、发现/显式读取分离、原始失败与 v2 恢复补正。离线核验冻结包：

```text
python -B tests/harness_baseline.py verify --manifest tests/fixtures/harness-baseline.json --archive tests/fixtures/harness-baseline.zip
python -B tests/prepare_harness_run.py prepare --root <new-run> --host codex --mode explicit
python -B tests/prepare_harness_run.py inspect --root <new-run>
```

`<new-run>` 必须替换成不存在的合成临时目录。准备程序写副本/控制输入，inspect 只读此明确测试根；不安装或运行宿主、不改全局配置。每种模式、宿主用独立根，详情以报告为准。[输入 v1](fixtures/harness-prompts.json)及失败保留，[恢复 v2](fixtures/harness-recovery-v2.json)补齐逐文件路径；CLI准备程序默认在恢复控制文件采用 v2。单测只检查包、准备/观察逻辑与已记录合成产物，不自动复跑付费模型，也不把单测成功当作新一轮宿主通过。

## 来源链接与正文变化检测（第三阶段）

[检测工具](../tools/check_source_changes.py)使用 Python 3.11+ 标准库，默认显式离线输入；只有传入 `--fetch` 才请求匿名 Jina Reader，不读取浏览器/账号/凭据。它输出待审 JSON，不改权威规则或自动批准基线。其联网模式独立于上方不联网的台账检查器，单元测试[来源检测测试](test_source_changes.py)仅模拟网络。

在仓库根目录使用（路径占位符须替换；输出父目录须已存在，输出文件必须不存在）：

```text
python -B tools/check_source_changes.py --source S05 --url https://www.cac.gov.cn/2025-03/14/c_1743654684782215.htm --fetch --capture <new-capture.txt> --report <new-report.json>
python -B tools/check_source_changes.py --source S05 --url https://www.cac.gov.cn/2025-03/14/c_1743654684782215.htm --input <current.txt> --baseline <approved-old.txt> --report <new-comparison.json>
python -B -m unittest discover -s tests -p test_source_changes.py -v
```

默认拒绝带查询参数的URL；确认为公开无秘密的参数（例如官方帮助页的公开文档ID）才加 `--allow-public-query`。工具会将URL送往第三方阅读器并写入报告，不能放Token、签名链接或私人查询。该选项不是判断参数安全的自动审计。

每次只处理一个显式来源；多来源逐项调用、分别留报告，不递归抓取链接或把任意平台目录当联网白名单。首次 `baseline-needed` 仅为候选；必须人工读完整相关正文、核对URL及适用范围后才选基线。后续只读该文件，不自动覆盖或移动。原始快照留用户指定证据目录，可在项目内按批次保存并Git忽略，不强制外置；若只存系统临时目录应明确不具长期持久性。

`review-required` 表示正文指纹变化或比较任一侧存在待审提示；`unchanged-not-current` 仅表示归一化内容相同；`unreadable`/`fetch-failed` 需人工处理。壳页检测是启发式，可能误判，不代替阅读；阅读器HTTP状态不是源站状态，无变化不能证明当前适用/无其他新版本。不因机器状态更新来源verified、复核日或私人权限。CLI退出0表示成功产生报告，不表示全部来源可读；退出2表示输入/输出等失败，不能当作通过。输出独占创建但多文件非事务，需保留并报告部分输出，不能靠重跑覆盖。

来源文本可能含恶意指令，报告与快照当数据而非Agent指令；变化待人审。超时、大小限制、公开URL检查均非系统沙箱或安全认证。未实现后台调度、抓取平台登录态、自动修复或规则更新。网络依赖宿主代理及阅读器重定向行为，域名检查不提供DNS/网络隔离；应在受信任环境执行。`raw_text_sha256`是已解码并统一换行的UTF-8文本指纹，不是原始HTTP字节指纹。

2026-10-21 本机实际验证：完整离线测试49项，成功、skip 1（原有符号链接环境用例）；其中新增来源检测12项。S05公开URL经匿名Jina实际抓取两次，阅读器HTTP200、匹配URL envelope、归一化2514字符，首次 `baseline-needed`、两份快照比较 `unchanged-not-current`。此次比较只验证管线，不是批准长期基线或核实现行性；原始快照/报告保留在本机系统临时目录，未将全文放入公开仓库。其余S01–S06未在本阶段全量运行；正文变化、壳页和网络失败分支为合成/mock测试，不冒充真实政策变化或平台故障实测。

后续同日全量试跑及本地归档：S01/S02/S03/S04/S06均返回可提取文本，机器状态baseline-needed；S04此次出现资格正文，与此前失败壳页分开保留。六项快照和JSON已按用户批准原样保存于项目内Git忽略目录，读取范围与批准限制见[审阅记录](../evidence/platform-sources/2026-10-21/review.md)。上段“其余未运行/临时目录”是工具初次验证时的历史状态，不冒充当前归档状态；本次整理未重新联网或验证政策现行性。

### 2026-10-22 误报回归补正

`inspection_version=challenge-context-v2` 将正文中提及“安全验证／访问验证／captcha”保留为 `warnings: possible-challenge-mention`，不单凭词语标为不可读；正常验证章节标题加实质正文也只提示待审；仅验证标题而缺实质正文、明确挑战指令及短正文仍阻断。首次仍是带提示的 `baseline-needed`，比较任一侧有此提示则 `review-required`，即使指纹相同也不静默当作无变化；不是自动放行或认可来源。归一化算法未变，`normalization_version` 保持 v1。其他壳页启发式仍可能误判，需人审，旧报告不重写。

来源单测增加正常长协议中的中英术语、真实挑战式标题／指令、基线一侧提示及 CLI 版本字段；全部离线合成/mock，不冒充重新抓取真实政策。此次15项来源测试通过；全量60项中59通过、1符号链接环境跳过，冻结35文件基线核验通过。报告落盘前首次回归有2项缺文件导航失败，落盘后复跑消除，未改预期。独立审阅发现标题误报后又补充正常安全验证章节的反例。最小建设链路的实际模型验证另见[新号验证记录](../examples/creator-start-validation.md)，不是单测自动运行 Agent。

## 6. 记录结果

本批实际命令、独立执行、限制与未完成宿主测试见[可靠性报告](../examples/reliability-validation.md)。旧报告原文不改；报告是测试证据，不是稳定协议、安全认证或真实平台核验。

## 7. 抖音第二平台交付检查（2026-10-22）

[本轮独立报告](../examples/douyin-validation.md)记录新一轮两平台七组实际模型回答、保留的措辞瑕疵、三轮虚构方案／实际工具保存／复核。它不继承小红书旧通过数，也不把下面的离线检查当作自动重跑模型。

```text
python -B -m unittest discover -s tests -p test_douyin_delivery.py -v
python -B tools/check_records.py --root . --record examples/douyin-ledger/account-proposed.md --record examples/douyin-ledger/decision-confirm-proposal.md --record examples/douyin-ledger/review-proposal.md --closed-set --public-examples --baseline douyin-demo-2026-10-22 --format json
```

[交付检查](test_douyin_delivery.py)复用现有检查器，不增平台 schema。四项检查仅覆盖：三份显式合成记录的 MC 子集、方案确认仍 proposed／preparing 及关键 unknown、此合成目录仅一份主档与决定／复核引用、17 份新改 Markdown 的直接行内链接／简单标题锚点。链接检查只额外打开明确指向的公开目标核存在／标题，不递归遍历；外部 URL 跳过，代码块忽略。复杂 Markdown、HTML、引用式链接、真实浏览器渲染及外部现行性不在检查承诺中；标题 slug 沿用 MC07 近似规则。业务正文的字面量断言只适用于本案例，不是通用语义核验；测试不调用模型、不联网或操作平台，也不为旧报告修复本机缺失证据链接。

## 8. 两平台统一导航检查（2026-10-22）

[共同专题职责](../platforms/README.md#统一专题导航与职责)只统一找任务的方法，平台覆盖与证据分别维护。[导航检查](test_platform_navigation.py)的四项离线测试核对：八类专题顺序与四列表头、每项有内容入口且指定 12 份文档的直接链接／简单锚点存在、抖音原章节及小红书旧导航标题保留。复用上节静态链接函数，不递归扫描或联网；简单表格解析仅适合当前导航写法，不是通用 Markdown 解析器。标题存在不证明任务语义、授权、现行性或平台能力。

```text
python -B -m unittest discover -s tests -p test_platform_navigation.py -v
```

改动前对 10 份平台文档的静态检查发现小红书六处 `README.md#共同边界` 断锚点，已改为平台总览的共同边界，不恢复已移除的旧兼容页。现行入口新增交叉链接与覆盖缺口，但没有补核平台规则或改写历史模型／保存验证；本轮不新增模型行为测试或虚构业务保存测试，也不办理平台动作。

本轮 Python 3.11.9 实际复跑：全量 57 项，56 通过、1 跳过（`OS did not permit creation of test symlink`），退出 0；新增导航 4 项均通过。R01–R07 保持原固定预期、冻结基线 35 文件核验通过，均退出 0，未改 golden 或历史报告。指定 12 份文档的 207 个本地链接、56 个锚点无缺失；`git diff --check` 退出 0，仅有 Git 换行提醒。以上均为离线检查，不升级平台覆盖或真实结果。

## 9. 两平台多轮官方研究补充（2026-10-22）

本批是[专题官方研究与审阅](../evidence/platform-sources/2026-10-22-deep-common/review.md)，不是新的平台执行／模型能力验收。两平台分别沿入口重读、正文关联、后续版本／专项缺口搜索三轮补充；[小红书来源](../evidence/platform-sources/2026-10-22-deep-xiaohongshu/review.md)与[抖音来源](../evidence/platform-sources/2026-10-22-deep-douyin/review.md)保留实际范围、日期、失败和机器误报。共同五项依据另由只读子代理逐项对照本地捕获，未发现实质不支持；按其非阻断建议补明信息内容流广告的可识别要求。这是文本证据交叉审阅，不是独立源站鉴真或法律结论认证。

回归沿用第 1、第三批、第 7 节命令，不修改预期、冻结包或历史失败。本轮不增加通用校验器或平台 schema，也不为文档结论编造模型通过数。对本批 16 份明确指定文档，复用[现有静态函数](test_douyin_delivery.py)并替换本次 `DOCUMENTS` 白名单（见共同审阅中的复现命令）；仅检查直接行内本地链接及简单标题锚点、跳过外部 URL，不递归验证全仓库历史证据，局限同第 7 节。

本批实际复跑（Python 3.11.9）：全量 57 项，56 通过、1 跳过，退出 0；跳过仍是 `OS did not permit creation of test symlink`。R01–R07 符合原固定预期、冻结基线 35 文件及既有内容哈希核验通过，均退出 0；没有改测试代码、golden 或冻结包。指定 16 份文档的 218 个本地链接、53 个锚点无缺失，30 个外部链接跳过；`git diff --check` 退出 0，仅有 Git 的 LF→CRLF 提示。未执行的模型业务行为／工具保存／真实平台测试保持未执行，不继承旧通过数。

## 10. 未确认正文续核（2026-10-22）

本轮继续核实[小红书未确认项](../evidence/platform-sources/2026-10-22-followup-xiaohongshu/review.md)与[抖音未确认项](../evidence/platform-sources/2026-10-22-followup-douyin/review.md)。证据层为匿名实际网页／公开页面数据读取及正文对照，不是客户端功能实测、当前账号资格认证或平台结果。父层另对抖音主协议和新内容标识、热点、网暴正文，小红书恢复可读的企业小程序与交易导流正文逐项回读；具体差异和剩余 unknown 见各来源记录。新路径成功不抹去前轮超时、壳页、缺段，媒体转述不升级为官方正文。

沿用离线测试、R01–R07可靠性复跑及冻结包核验命令；本轮不改测试代码、预期或冻结包。首次复跑当前工作树（已含此前来源工具 v2 补正）：Python 3.11.9，全量60项中59通过、1跳过（`OS did not permit creation of test symlink`），退出0；R01–R07均符合原固定预期，冻结35文件与既有内容哈希核验通过，均退出0。来源工具及其测试文件在本次命令前后SHA256相同；这不是对并发编辑的通用锁定保证。

续核链接检查复用现有静态函数，白名单为平台总览、两平台11份文档、两份新审阅及本页，共15份；不递归扫描仓库或私人材料。可在仓库根目录将下列 Python 经标准输入交给 `python -B -` 执行：

```python
import json, sys
sys.path.insert(0, 'tests')
import test_douyin_delivery as nav
nav.DOCUMENTS = ['platforms/README.md', 'tests/README.md'] + [
    'platforms/xiaohongshu/' + name + '.md' for name in
    ('README', 'rules', 'guide', 'security', 'collaboration', 'lifecycle',
     'rights-and-privacy', 'policy-review')
] + ['platforms/douyin/' + name + '.md' for name in ('README', 'rules', 'guide')] + [
    'evidence/platform-sources/2026-10-22-followup-' + name + '/review.md'
    for name in ('xiaohongshu', 'douyin')
]
counts, problems = nav.check_navigation()
print(json.dumps({'counts': counts, 'problems': problems}, ensure_ascii=False))
raise SystemExit(bool(problems))
```

只核直接行内本地链接及简单标题锚点；外部URL跳过，HTML、复杂Markdown与真实浏览器渲染不在保证内。模型业务行为、工具保存与真实平台动作本轮未执行；旧验证不自动继承为新规则适用通过。

最终文档落盘后的复跑：60项中59通过、1同因跳过，4.597秒；R01–R07符合原预期，冻结35文件核验通过（内容SHA256仍为`a9e9399b68fef9a6f47f4643be2a09d8cd96740613864c6b9c32b7f972954716`）。上述15份文档的251个本地链接、59个锚点无缺失，83个外部链接跳过；各命令及`git diff --check`均退出0，只有全树既有LF→CRLF警告。未跟踪的两份新审阅文本已分别读取；两批Git未忽略清单只含各自审阅，公开原始txt/json未列入。检索失败、页面壳及来源内日期/额度冲突见新审阅，不把离线测试通过当成这些事项已解决。

并行状态补记：研究期间共享工作树HEAD从`9fd5f5b`变为`82fbc69`，并检测到来源测试文件相对首次复跑哈希变化；本轮父/子任务未执行暂存、提交或推送，保留外部变更。收尾再次运行全量测试，60项59通过1同因跳过、4.733秒，退出0；此次命令前后HEAD均`82fbc69`，主来源工具及其测试文件各自SHA256保持相同。这里只确认该窗口与所述文件，不承诺跨会话锁定或把并行工具改动归为本次规则研究实现。

## 11. 抖音专题拆分与离线回归（2026-10-22）

本轮仅文档职责迁移、导航及静态／离线回归，不沿用上节60项历史结果。接手HEAD为`82fbc69a422b454b472cf838e81e80fe4b71b4ee`；已有未提交来源补读、平台导航及四篇抖音专题草稿，均不归为本轮新建。未暂存、提交或推送；不修改小红书内容、旧审阅或冻结包。

[原指南](../platforms/douyin/guide.md)五段按原文字逐段比对后迁入[安全](../platforms/douyin/security.md)、[协作](../platforms/douyin/collaboration.md)、[生命周期](../platforms/douyin/lifecycle.md)、[权利隐私](../platforms/douyin/rights-and-privacy.md)、[规则复核](../platforms/douyin/policy-review.md)，旧标题保留为单向导航；前三个建档／主页／发布入口不变。规则来源仍唯一维护于[证据页](../platforms/douyin/rules.md)；其中本地忽略摘要的链接改指版本化审阅说明，不强制纳入原始全文。

测试白名单只补五个专题，保留原有方案不等于账号事实、唯一主档、unknown和旧标题断言；新增同序专题文件路由、旧入口单向迁移及迁移后关键边界字面回归。它们不是完整语义或平台资格验证。

环境：Python 3.11.9；`platform.platform()`为`Windows-10-10.0.26300-SP0`。命令在仓库根目录执行，以`-B`禁用字节码写入；本轮日志及对比快照只留于忽略的本地目录，不纳入Git。

```text
python -B -m unittest discover -s tests -v
python -B tests/replay_scenarios.py
python -B tests/harness_baseline.py verify --manifest tests/fixtures/harness-baseline.json --archive tests/fixtures/harness-baseline.zip
git diff --check
```

本次实际结果（非继承历史）：

- 全量单元测试：**62项，61通过、0失败、1跳过**，首跑4.567秒、最终复跑4.478秒，均退出0。唯一跳过为`test_symbolic_link_is_not_followed`，原因为`OS did not permit creation of test symlink`；不称真实符号链接隔离通过。
- 可靠性复跑：R01–R07全部符合原预期，退出0；R01的检查器退出1及故障注入中的partial／conflict是预期场景，不是复跑失败。测试副本写入／模拟OSError不等于真实平台、生产保存器或新宿主保存测试。
- 冻结基线：35文件验证通过，退出0，内容SHA256为`a9e9399b68fef9a6f47f4643be2a09d8cd96740613864c6b9c32b7f972954716`；未修改冻结manifest或archive。
- 显式导航检查：在交付白名单上再补两平台八文档，`python -B -`运行下段只读代码，30文档、499本地链接、149锚点无缺文件／缺锚点，48外部URL跳过不访问。全部9个原指南标题保留；五段原正文与迁入目标再次逐字比对一致，不只比文件数。
- 新增／未跟踪文件：八份抖音文档与两份交付／导航测试均逐个运行`git diff --no-index --check -- NUL <file>`并检查尾随空白及文件结尾；10份无空白诊断。每项退出1来自`--no-index`隐含的差异退出码（空设备与非空文件不同），不是测试通过码；同时要求诊断为空、独立空白检查通过。仅有LF→CRLF提示。

导航检查可复现输入（复用现有检查器，不新增扫描器）：

```python
import sys
sys.path.insert(0, 'tests')
import test_douyin_delivery as nav
names = ('README', 'rules', 'guide', 'security', 'collaboration', 'lifecycle',
         'rights-and-privacy', 'policy-review')
nav.DOCUMENTS = list(dict.fromkeys(nav.DOCUMENTS + [
    f'platforms/{platform}/{name}.md'
    for platform in ('xiaohongshu', 'douyin') for name in names
]))
counts, problems = nav.check_navigation()
print(counts, problems)
raise SystemExit(bool(problems))
```

过程中的失败与修正也保留：首次迁移脚本因末段分隔词写错而在写前退出；修正后写回被工作区沙箱拒绝，ACL技能加载亦失败（ENOENT），同一命令获准重跑后成功，最后再次逐字复核。首次定向导航测试6项中2项失败（3个子断言）：新断言错误要求小红书所有交叉链接都落同一文件，另有权利页缺英文unknown字样；现保留主入口归属校验、显式允许其原有两种跨专题链接，并将权利页未核验项注明unknown。未删除或放宽原有边界断言；交付定向命令因前项非零当次未执行，后续已在全量中实际通过。首次`git diff --check`检出本节编辑时的EOF空行，续写后修正；最终结果另记。

局限：行内本地链接和简单标题近似检查不覆盖复杂Markdown、HTML、浏览器渲染或外部URL可达性；字面断言不证明语义完备、来源现行或账号资格。未新增联网研究、模型业务测试、工具保存测试或真实注册、发布、协作、申诉、投诉、恢复、注销操作；没有增长／不限流／申诉成功／恢复保证。历史失败、冲突和unknown均不因离线通过而升级。

最终差异核对按接手快照而非单看Git总diff：本轮修改8个已有文件，仅新建规则复核专题；四篇既有专题中安全、协作、生命周期正文未改，权利页补身份关联边界。小红书、旧证据、工具及冻结文件与接手哈希一致。首次比对脚本误将Git仍列出的接手既有删除路径当作新增候选而断言失败；补上现存文件过滤后通过，未恢复、删除或改写该路径。最终`git diff --check`与单独新增文件空白检查均无错误，暂存区仍为空、HEAD未变；本轮到此交用户审阅，不自动提交或推送。
