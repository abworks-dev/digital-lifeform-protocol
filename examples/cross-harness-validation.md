# 第三批：跨宿主分项验证报告

执行日期：2026-10-21（Asia/Shanghai）。只用公开框架与 fictional-user、虚构平台、示例域名。正式对照为 **DeepSeek Harness 0.2.1-rc.2** 与 **Codex CLI 0.144.6**；Claude Code 2.1.225 另作发现/启动探针。结果不构成兼容认证或安全隔离证明，也不修改[旧走查](creator-ledger-validation.md)与[第二批报告](reliability-validation.md)。

## 1. 固定的究竟是哪一份框架

- 基线 ID：`creator-ledger-cross-harness-2026-10-21-b1`。
- Git 参考提交：`41e054795b2a0902a71a4d43aea21f999dc400d4`；工作树有未提交内容，**不能只 checkout 此提交重现本次测试**。
- [清单](../tests/fixtures/harness-baseline.json)明确列出 35 个公开文件及逐文件 SHA-256/长度；[冻结压缩包](../tests/fixtures/harness-baseline.zip)保留实际测试字节。UTF-8 去 BOM、CRLF 规范化为 LF 后冻结，解包字节固定；这不是发布版本、私有记录格式或升级协议。
- 内容索引 SHA-256：`a9e9399b68fef9a6f47f4643be2a09d8cd96740613864c6b9c32b7f972954716`。
- 压缩包 SHA-256：`ffc20058d639b10a4d208cc33031d0fa4872dc63b02ab006368be5f752baffd7`。
- 每轮独立解包为 `framework`，复制六份公开案例文件为 `records`；写入轮与只读轮分开。不把本报告及后续矩阵修改塞回旧基线，不为更新文档而重生成基线。

## 2. 环境与加载方式分别记录

| 标识 | 确切版本与依据 | 模型/数据边界 | 加载与运行限制 |
|---|---|---|---|
| H02 | DSH：正在运行的 Windows 应用文件版本 `0.2.1-rc.2`；ProductVersion 为 `0.2.1.0`，两者不混写 | 宿主上下文声明 gpt-6.1-sol；未独立核验实际路由、历史/缓存/提供商保留 | 原生文件工具；独立、不继承维护上下文的子执行者。不是关闭重启 GUI。当前策略声明 danger-full-access；没有权限隔离探针 |
| H03 | Codex：原生 `codex --version` 报 `codex-cli 0.144.6`；现有 npm 命令入口 | 沿用原生已配置推理认证；未读取凭据。事件未充分登记实际模型/服务，记 unknown | Windows；`exec --ignore-user-config --ignore-rules -c project_doc_max_bytes=0 --skip-git-repo-check --ephemeral --json -`；只读轮请求 read-only，保存轮请求 workspace-write，但实际补丁被只读策略拒绝 |
| H04 | Claude：原生 `claude --version` 及 init 事件均为 `2.1.225` | init 报 `claude-opus-5[1m]`，但认证失败前未完成业务推理；不能据此认证模型可用 | 发现轮只启用 Read/Skill、project 设置源、禁 hooks/记忆/MCP；显式轮用 safe-mode、仅 Read。未修改全局配置或迁移认证 |

原生 CLI 请求使用既有推理通道，是本次模型调用，不等于“离线测试”。未调用网页/平台工具，不能据此声称不外发或零留存。CLI 启动仍可读取自己的原生认证和必要配置；本项目没有复制或导出它们。全局 Skill 元数据也可能进入宿主上下文，项目路径白名单不是上下文隔离机制。

### 安装、发现、激活、显式读取不是同一项

- **安装**：未安装/升级任何宿主，未写用户/全局 Skill 目录。只在新临时测试根分别复制同字节入口至 Codex 的 `.agents/skills/creator-account-ledger/SKILL.md`、Claude 的 `.claude/skills/creator-account-ledger/SKILL.md`。这是项目局部发现布局，不是产品安装器；依赖仍在明确的 `framework` 根，复制单文件不使 Skill 自包含。
- **Codex 发现**：[原生事件摘录](../tests/fixtures/codex-discovery-evidence.json)保存枚举自报、项目内路径实际读取及 C01 回答。没有先用目录扫描搜到目标；但没有独立的原生技能清单事件或专用激活回执，激活实质为文件读取，故“自动枚举/激活”仅记**受限**，不升级为完整通过。出现 Skill 描述受上下文预算缩短的警告，也补读了报告为截断的核心文件。
- **Claude 发现**：[init 摘录](../tests/fixtures/claude-discovery-evidence.json)的目标 Skill 枚举为 true；随后 `Not logged in · Please run /login`，exit 1、无业务工具执行。只证明该局部布局被枚举，不证明激活、依赖加载或业务通过。
- **Claude 显式读取**：[safe-mode 摘录](../tests/fixtures/claude-explicit-evidence.json)不枚举目标 Skill，启动后报 `401 This API key has expired`，exit 1，未执行 Read。认证是本实例限制，不据此判断该版本不支持文件读取，也不重试/更换凭据。
- **DSH**：没有安装或测试项目 Skill 自动发现。明确提供框架入口后主动 read；读取文件时宿主还自动附带了框架维护者指令，执行者未用它扩大业务内容读取。“主动读取遵守范围”不能写成“上下文只有白名单”。

## 3. 共用任务与实际结果

完整合成输入见[原始输入](../tests/fixtures/harness-prompts.json)，恢复补正见[v2 输入](../tests/fixtures/harness-recovery-v2.json)。场景取自[C 系列](creator-ledger-tests.md)，不另定业务 schema。下表“通过”仅指该次语义/文件判据，不是整个宿主通过。

| 项目 | DSH 0.2.1-rc.2 | Codex CLI 0.144.6 |
|---|---|---|
| 显式入口、三份核心依赖实际读取 | 完成；独立执行者报告 native read，证据为会话摘录与文件核对，不附完整原始工具流 | 完成；[命令/原答摘录](../tests/fixtures/codex-explicit-evidence.json)逐文件成功，无主动扩链 |
| C01 名称、批准与平台结果、第二号 | 通过：O1 旧名/2026-10-20/reported；新名获批不等于平台完成；第二号 proposed | 同样通过 |
| C03 无账号纯方案 | 通过：仅对话，ID/主页/所有者 unknown | 同样通过 |
| C05 用户报告但无保存许可 | 通过不保存与 reported/unknown 判据；提议仅为草案 | 同样通过；两边提议中有向旧 decision 追加事件的说法，未执行；不据此验证正式写入历史策略 |
| C06 拒绝身份关联 | 通过不建隐藏映射、不保存/公开的判据 | 同样通过 |
| C04 确认后的本地保存 | 名称字段、新 decision、双向 links 与重读通过；41→42 文件，只增新决定、改主档，其他40份不变。执行者额外枚举了整个合成 framework 的路径，故**最小路径枚举边界不判全通过** | **保存未完成**。请求 workspace-write，但实际路由错误为 `patch rejected: writing is blocked by read-only sandbox; rejected by user approval settings`；没有绕过。41份文件均未变，不能因原生进程 exit 0 视为任务成功 |
| 新执行者/新进程恢复 v1 | 读到新主档与决定，正确恢复 O2；但简称路径导致四份核心读取失败，**完整接入恢复不通过** | 新原生进程读到旧值与新决定缺失，正确报告未闭环；有目录枚举/策略拒绝，不判最小读取范围全通过 |
| 恢复 v2 | 独立新执行者10份 read 全成功（控制输入+四核心+五记录），恢复 O2、新决定、旧历史和 unknown；无主动扩读/写入。通过本次已保存文件恢复判据，非应用重启 | [新原生进程摘录](../tests/fixtures/codex-recovery-v2-evidence.json)：四核心/四旧记录可读，新决定缺失如实报告；正确恢复旧值与未闭环，不宣称保存成功。但“第二号是否已创建：没有”的措辞应收紧为“无创建证据”，不能据草案证明平台绝不存在；仅记受限，不判完整通过 |
| C02 完整同名/冲突多轮、C08 宿主部分写入故障 | 未执行 | 未执行；写入全被拒不是“decision 已写、主档失败”的 C08 |
| 宿主整体重启、审批拒绝探针、越界读写、记忆/同步/外发隔离 | 未执行 | 未执行；一次补丁拒绝不能证明全部工具隔离 |

### 独立文件观察与已保存样本

[文件观察](../tests/fixtures/harness-file-results.json)比较各合成根的完整文件清单、SHA-256 和 mtime_ns：两个显式只读根各41份不变，Codex发现根42份不变，Claude两根分别42/41份不变，Codex保存根41份不变；DSH保存根只新增新决定、修改主档。它不检查宿主外的会话数据库、日志、缓存或系统 atime。

DSH 实际输出公开副本：[主档](../tests/fixtures/harness-dsh-saved/account-existing.md)、[新决定](../tests/fixtures/harness-dsh-saved/decision-name-observation.md)。新决定中的临时绝对路径替换为 `<run-root>` / `<control-input>`，仅此为公开脱敏；真实测试副本未修改，主档差异及其原始哈希留在文件观察中。现有 frontmatter 的旧 source 未获准修改，最新字段来源在 O2 正文明确记录；不能把 frontmatter 单一历史指针当作全部当前证据。公开脱敏副本的元数据检查为 error 0 / warning 1 / unchecked 4、exit 2：四处 `<run-root>` / `<control-input>` 不属检查器支持的 Markdown 导航语法；保留未覆盖，不把它改成静默成功。

DSH 两轮执行和初轮恢复的证据为父代理收到的完整会话回答、工具调用清单及独立文件复验；公开报告只保留摘要，**没有提供独立可重放的全部 DSH 原始事件流**。Codex/Claude 公开的是选定事件，不是全部原始日志；[提取工具](../tests/collect_harness_evidence.py)省略身份/认证元数据、会话ID与工具正文，并替换临时根和用户目录前缀。原始流 SHA-256 作为来源指纹，不可凭哈希恢复省略内容；工具也不是通用秘密清洗器。

## 4. 复跑：先冻结、再逐项取证

以下是可独立执行的测试准备，不会安装宿主或自动调用模型。需要 Python 3.11+；新目录必须不存在，且应在私人资料和公开 Git 目录之外。

```text
python -B tests/harness_baseline.py verify --manifest tests/fixtures/harness-baseline.json --archive tests/fixtures/harness-baseline.zip
python -B tests/prepare_harness_run.py prepare --root <new-run> --host codex --mode explicit
python -B tests/prepare_harness_run.py inspect --root <new-run>
```

1. 每个宿主、每种模式各建新根；`--host` 可为 codex/claude/dsh；`--mode` 可为 discovery/explicit/write。DSH discovery 没有已测目录约定，辅助程序明确拒绝，不猜一个安装路径。
2. 准备程序只解包已核验基线、复制虚构记录、在 discovery 模式建立项目局部入口，并在 `.harness-control` 写明示输入和 before 指纹；不配置宿主。实际本轮早期使用了等价的一次性准备命令，控制文件位于各根之外；后续辅助程序把控制文件集中在此子目录，inspect 不把控制文件算业务结果。
3. 将相应 `*-prompt.txt` 内容作为唯一任务输入，运行已有且版本已核实的宿主；不要给旧回答、expected或兄弟根。保存命令、实际权限摘要、工具事件、回答、退出码。DSH 用不继承维护上下文的新执行者；Codex使用新的原生 `exec` 进程。不要把两者统称为应用重启。
4. 原生 Codex 公共参数见环境表；只读模式加 `--sandbox read-only`，保存模式请求 `--sandbox workspace-write`。**参数不是有效权限的证明**，遇到本轮这种拒绝就记录未完成，不换工具/提权绕过。普通用户应按本机帮助核对参数，不自动复用个人配置。
5. 发现轮只在项目目录提供入口，由宿主提供目录元数据，不把人工先读取文件算自动发现；显式轮不提供项目 Skill 布局，直接读取框架入口。Claude发现/显式两种限制组合见上文，认证失败保持失败，不需为复跑提供秘密。
6. 保存后再次运行 inspect，独立检查目标字段、旧决定、未知项和双向 links。新建只读会话，使用 **v2 recovery** 输入，不继承临时保存授权；辅助程序默认将 v2 合并到恢复控制文件，原 v1 输入和失败记录保留。
7. 逐项人工评分后再更新矩阵。只读检查器结构通过不能代替语义完成；exit 0不能代替保存成功。实际模型、宿主设置、工具或基线变化均需重新验证。

离线辅助程序和基线的自动化检查纳入 `python -B -m unittest discover -s tests -v`。父代理与另一位只读执行者独立复跑均为 37 项、36 成功、1 跳过（Windows未允许创建测试符号链接）；冻结包35文件核验通过，旧报告指纹仍通过。父代理另查本轮六份文档的128个本地链接目标与28个锚点，无错误；`git diff --check` 通过，保留既有LF/CRLF提示。这些单测不是重新调用两个宿主；原生模型结果是本日期的观察样本。

## 5. 限制与下一步

已形成固定字节基线、两个明确版本的实际业务对照、分项结果及发现/显式读取分离证据；**没有形成“两宿主全部任务兼容通过”结论**。仍需按真实需求补齐可写 Codex 环境（另行核对权限而非绕过）、C02/C08、真正宿主重启、安装/发现完整回执、强制隔离与独立公开事件导出。真人/私人接入、全局配置、安装与服务生命周期变更不在本轮范围。
