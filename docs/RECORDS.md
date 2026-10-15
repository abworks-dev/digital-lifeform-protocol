# 最小记录约定 v0.1-draft

实验约定，不是稳定协议。使用 UTF-8 Markdown；一条记录一个文件。ID 在私有工作空间内唯一，重命名文件不改变 ID。引用使用 ID，不靠显示名猜测对象。

## 所有记录的字段

- id：如 identity-professional，非空、唯一，不含真实联系方式。
- type：profile / identity / project / account / delegation / decision / review。
- title：可读名称。
- status：draft / confirmed / retired。草稿不得作为已确认事实。
- source：用户明确陈述或证据位置；无来源写 unknown。
- updated：YYYY-MM-DD。
- confirmed_by、confirmed_at：confirmed 时必须记录确认主体和日期。公开示例只能写 fictional-user，不能冒充真实确认。
- links：关联记录 ID 列表，无则 []。

未知值写 unknown，不用空白暗示已知。建议与事实放在不同小节。status 表示记录的确认/维护状态，不等于账号是否活跃；账号另用 operational_state。

## 类型字段

| 类型 | 必要内容 |
|---|---|
| profile | 目标、约束、隐私偏好、数据外发偏好 |
| identity | 角色、受众、公开关联偏好 |
| project | 目标、阶段、负责身份 |
| account | 平台、用途、实际所有者、管理者、角色、项目、operational_state |
| delegation | 委托主体、代理、资源、允许动作、禁止动作、条件、到期日、撤销方式、active/revoked/expired |
| decision | 问题、选项、理由、确认结果、受影响记录 |
| review | 范围、发现、待确认变更、复核日期 |

## 确认和撤销

用户确认草稿后才转 confirmed；修改所有权、公开关联、关键权限时重新形成待确认变更，保留旧决定。retired 记录不删除，仍可被历史引用。委托撤销需明确记录 revoked；日期过期即不得继续执行。文本状态不是实际权限控制，运行环境必须另行执行限制。

模板中的 Agent 只允许提出建议；写入私有记录还需用户授权。不得依靠仓库内容自行授权外部动作。

## 委托的价值交付试验字段

委托模板新增目标、交付物、允许输入与外发边界、预算/停止条件、验收标准/验收人、升级条件和人工协作。它们先用于案例验证，暂不升级为所有记录的强制必填字段。unknown 不构成执行许可；预算或外发边界不明确时，不执行会消耗费用或暴露私人数据的动作。
