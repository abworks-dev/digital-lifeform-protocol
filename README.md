# Digital Lifeform Protocol

> 让 AI 理解数字世界里的你，并在你授权的边界内协作。

**面向 AI 超级个体的数字身份、资产与 Agent 委托实验规范及工作空间模板。**

当前是**文件与指令组成的手动实验版，不是自动管理应用**：已有记录约定、模板、工作流、虚构案例、Skill 入口和显式文件范围的[只读检查器与可靠性复跑](tests/README.md)，优先完善自媒体账号台账。尚无稳定协议、安装器、自动账号操作或兼容认证；Protocol 表达研究方向，不代表行业标准。历史验证见[旧走查报告](examples/creator-ledger-validation.md)，第二批工具与回归证据另见[可靠性报告](examples/reliability-validation.md)。

## 从这里开始

**日常用法：首次显式接入 → 打开自己的工作空间 → 直接告诉 Agent 要做什么。** 用户不必记住 T1–T5 或每次列出要读的文档；Agent 按入口选择流程、追问缺口并展示待确认变更。

第一次使用：从[快速开始的接入入口](docs/QUICKSTART.md#0-首次显式接入以后直接提任务)发起，先只检查并展示接入方案；也可先做下方虚构只读练习。可以从任意能访问框架和目标空间的会话发起，更推荐目标私人工作空间；不要求在公开框架仓库中操作。只有对话能力时可手动提供完整相关文本，但不声称本地接入或保存完成。

**不自动全局启用。** 克隆仓库、打开目录或读取一次文件不安装用户级 Skill；会话手动读取通常仅当次生效。持久入口只在明确获准的目标工作空间、实际支持并加载它的宿主中生效；其他空间/宿主不自动继承。一次接入不是永久授权，也不把完整内容创作、自动运营或强制安全控制变成已实现能力。

| 我想做什么 | 最少准备什么 | 本次会得到什么 |
|---|---|---|
| [T1 制定账号方案](workflows/maintain-creator-ledger.md#t1-账号方案) | 目标、拟用平台、资源与隐私约束；未知可直说 | 复用/另建/不创建的方案与缺口，不是注册结果 |
| [T2 盘点已有账号](workflows/maintain-creator-ledger.md#t2-已有账号盘点) | 用户清单或获准总览、主档文件 | 范围内账号、身份与用途、来源及冲突，不是自动搜索所有账号 |
| [T3 查询某个账号](workflows/maintain-creator-ledger.md#t3-单项查询) | 具体问题、ID/线索和获准主档 | 带来源、日期与未知项的回答，默认不写 |
| [T4 提议或保存变更](workflows/maintain-creator-ledger.md#t4-记录变更) | 目标 ID、拟改事项和依据 | 字段差异与 decision 草案；逐项获准后才保存 |
| [T5 复核、交接或退出检查](workflows/maintain-creator-ledger.md#t5-复核交接与退出检查) | 检查类型、对象/范围、触发原因 | 风险、未闭环项与人工清单，不是平台撤权或注销 |

五条任务的完整输入、读取、输出、确认点和完成条件，以[台账维护流程](workflows/maintain-creator-ledger.md#1-五条核心任务的输入与输出)为准。框架如何加载、路径与工具如何核对，见[最小接入契约](docs/HARNESS.md)。

**默认只在对话交付。** 需要保存时，Agent 先列出具体文件、字段、前后值和依据，再分别请求内容确认与保存授权。认可方案不等于允许写入，允许写入不等于允许注册、登录、发布或公开身份关联。真实资料只放独立私有工作空间，使用前先明确模型、历史和同步的[数据边界](docs/SECURITY.md)；不要提供密码、Token、Cookie 或恢复码。

## 为什么做

一个人同时是开发者、创作者和经营者，但身份、平台账号、项目资产和 AI 授权往往散落各处。本项目尝试把这些关系变成可理解、可审阅、可迁移的记录与流程，让人和 Agent 共同维护，而不是反复从零解释。

这里的 Digital Lifeform 是组织个人数字存在的愿景隐喻，不是意识、人格复制或数字永生的技术主张。人始终是决策主体，Agent 是受约束的代理；人的身份与 Agent 身份必须分开建模。

## 为谁服务

第一批用户：借助 AI 完成跨角色价值交付的独立开发者、创作者及个体经营者。本项目将其视为 AI 超级个体的目标用户，不以工具数量、Agent 数量、收入或是否注册公司作为门槛。

## 组织 AI 协作，而不是收集工具

个人目标 → 项目 → 身份 → 数字资产 → Agent 委托 → 交付与验收。本人保留关键判断与责任，也可以选择交给专业人士或暂不执行。本项目只提供轻量记录与流程，不保证商业成功。

## 首个应用

优先实现**自媒体身份与账号管理台账**：单一账号主档、身份关系、变更历史与 Agent 维护入口，先跑通盘点、查询、建档、变更和复核，再按真实需要连接作品、发布与经营。2026-10-21 用户确认此实施优先级；字段仍为实验设计，不包含真实账号迁移或外部操作授权。

台账支持已有账号盘点，也支持尚未注册的筹备方案；本轮另补平台创建与健康运营的通用手动指南子集，先完善小红书，不代表完整创作者启动系统已交付或验证。

此前“职业身份 + 自媒体 + 网店”的综合账号体系仍作为较广案例方向保留，不在本次同时扩建。不是鼓励注册更多小号，也不是规避平台规则。

- [日常维护流程](workflows/maintain-creator-ledger.md)
- [Skill 入口与加载说明](skills/creator-account-ledger/SKILL.md)
- [静态虚构台账](examples/creator-ledger/README.md)
- [场景验收与验证范围](examples/creator-ledger-tests.md)

## 按需深入

不用一次读完下列文档。P0 治理、依赖、授权闭环与规则证据为可选试验；P1 退出、事件和商业化为人工检查草案，不表示运行验收已通过。

### 核心与接入

- [快速开始](docs/QUICKSTART.md)
- [最小记录约定](docs/RECORDS.md)及[机器可检查规则边界](docs/RECORDS.md#机器可检查规则边界草案)
- [最小接入契约与分项能力矩阵](docs/HARNESS.md)
- [固定基线的跨宿主验证](examples/cross-harness-validation.md)：DSH `0.2.1-rc.2` / Codex CLI `0.144.6`；安装发现、显式读取和保存限制分别记录，不宣称全兼容。
- [Hermes 接入指南](docs/HERMES.md)
- [安全与隐私边界](docs/SECURITY.md)
- [虚构接入验收集](examples/acceptance-tests.md)
- [完整虚构案例](examples/solo-builder.md)
- [账号共用与拆分方法](handbook/share-or-separate.md)

### 治理与平台参考

- [账号治理与依赖字段](docs/RECORDS.md#账号治理与依赖)
- [授权变更闭环](workflows/change-access.md)
- [定期与事件复核](workflows/review-accounts.md)
- [规则与证据记录](docs/RECORDS.md#规则与证据)
- [停用、交接与退出检查](workflows/exit-or-handoff.md)
- [事件处置检查](workflows/respond-to-incident.md)
- [发布与商业化检查](workflows/publish-and-commercialize.md)
- [平台指南目录](platforms/README.md)：一平台一文件夹，区分规则证据与创建、健康运营建议。
- [小红书平台指南](platforms/xiaohongshu/README.md)：[规则与证据](platforms/xiaohongshu/rules.md)及[本人创建与健康运营手动指南](platforms/xiaohongshu/guide.md)。这是创作者从零启动的通用手动指南子集，不是登录/API 工具、自动运营或养号防封保证；原平台参考保留兼容入口。

### 维护本项目

- [定位与边界](docs/PROJECT.md)
- [分阶段方向与验收](docs/ROADMAP.md)
- [Agent 协作约定](AGENTS.md)
- [贡献说明](CONTRIBUTING.md)

## 交付形态

计划采用公开方法、模板、虚构案例与可验证约定，配合用户独立保存的私有工作空间。Agent 运行环境由用户选择；仓库本身不会运行模型、定时任务或外部账号操作。

## 独立性与许可状态

本项目是独立实验，与现有 Lifeform、Second Me、LifeOS 等项目无隶属、合作或背书关系。品牌与商标尚未完成正式清查。暂不以 DLP 作为主要对外简称。

本项目自行创作的代码、文档、模板与 Agent 指令统一采用 [MIT License](LICENSE)。用户填写的私人资料不因使用模板而自动获得本项目的 MIT 授权；第三方材料遵循各自许可。许可证不代表品牌清查通过或任何关联背书。公开仓库：https://github.com/abworks-dev/digital-lifeform-protocol 。当前为实验性文档版本，尚未发布稳定版。
