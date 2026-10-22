# 抖音未决规则与公告正文续核

实际查阅：2026-10-22（Asia/Shanghai）。范围：中国大陆抖音普通个人内容账号及其内容发布／互动；非 TikTok，不把一般规范变成企业、电商、直播、星图专项准入。首次捕获仍未获用户批准为基线；旧批审阅和失败报告不改写。

## 关键结果

- 从官方公开前端实际使用的只读端点取得《抖音网络暴力治理规范（2026版）》13条、《抖音社区热点信息和账号治理规则（试行）》24条全部文字；不再只依赖首页标题。
- 《抖音内容标识使用规范》正文明确 **2026-05-11最新修订生效**；2.1(4)要求含营销推广商品或服务的内容添加“内容含营销推广信息”。这补到普通创作者的一般内容标识依据，**不等于法律广告显著标明“广告”，也不等于商业准入**。具体合作产品资格、利益关系边界、当前按钮仍须另核。
- 前轮超时的 article/15868 本轮 Jina 已成功读到正文；另取得2026 AI治理公告与营销创作提示。AI批量低质、仿冒、造假、绕标识等是特定治理对象，不扩写为多账号或AI创作普禁。
- 父层从主协议入口实际读取到此前缺少的日期、导语和尾部；单列 DY-S15，不把此前 CDN 候选倒认定为当前主站 canonical，也不伪造前轮已全文读取。

## 方法、查询、失败与排除

使用 agent-reach 搜索／web 路由（父层 doctor 已跑，web=Jina，无授权平台登录态）；阅读其 search/web 指引。未读取 Cookie／浏览器、未登录、安装、付费、上传私人材料或执行任何平台动作。新目录用于保留本次真实不同读取历史；沿用 txt/json 忽略惯例，不建 manifest/schema。

1. Exa仅重试一次查询 `site:trust.douyin.com "抖音网络暴力治理规范（2026版）"`，返回 HTTP429。错误核心原文：`You've hit Exa's free MCP rate limit.`；未完成有效检索，不解释为没有该规则，不配置新Key或绕额度。
2. 按既有后备使用 Bing：`site:trust.douyin.com "抖音网络暴力治理规范"`、`site:trust.douyin.com "抖音社区热点信息和账号治理规则"`。结果仍未给出可用正文链接；摘要只作候选，不作条款证据。
3. 原站首页是应用壳（单次 HTTP200，不是全文成功，也未见需登录正文）；只读取其明确引用的公开静态前端片段。静态资源根路径为 `https://lf3-webcast.bytetos.com/obj/webcast-new/goofy_deploy_edenx/ife/douyin-trust/`；相关主包 `static/js/main.287854e5.js` 与文章页 `static/js/async/article/(publishId)/page.09fd993c.js` 明确使用 GET `/thematic/api/trust/layout`（公开 `tab` 参数）及 GET `/thematic/api/trust/article`（公开 `id` 参数）。首页／安全／文章静态片段只用于理解公开文章读取和映射，不声称做过前端完整安全审计。
4. 只取两个公开布局 `https://trust.douyin.com/thematic/api/trust/layout?tab=main` 与 `https://trust.douyin.com/thematic/api/trust/layout?tab=community_rules`；标题和文章ID从返回布局明确匹配。随后仅取下表已列的6篇文章，**没有枚举／扫描ID、猜认证私有接口或绕过验证**。
5. 对5篇新文章，保存 API 原始 JSON；按官方文章前端的 UTF-8 Base64 内容方式解码，检查仅有 `_deltas["0"]`，逐项提取 `ops[].insert` 的全部文字。原始响应、解码富文本和派生正文分开，不把派生文本伪装为 Jina capture。article/15868 另有成功 Jina capture及API响应；3张内嵌图未读取。未核原页面视觉排版或客户端UI。
6. 次要协作补查（Bing）：误写 `site.douyin.com "子账号" "协作" "个人"`（不是站点过滤，排除）；纠正 `site:douyin.com "子账号" "协作" "个人"`、`site:douyin.com "创作者中心" "成员管理"`，另 `site:trust.douyin.com "营销推广信息"`。返回 Facebook／知乎／Discord／营销百科等明显不相关结果，不当作有效命中、无规则结论或官方角色许可，不继续扩展搜索。
7. 本轮 article/15868 的旧超时未复现；旧批错误 `The read operation timed out` 仍原样保留。没有本轮新的验证码／登录失败可报告。源站壳页、搜索失败和无关结果仍算读取限制，不因后续成功消除。agent-reach check-update：v1.5.0，已是最新；没有更新／安装。

## 自包含来源台账

以下主体均为官方抖音平台／抖音安全与信任中心；独立法律实体全称在这些公告中未给出则为 unknown。全部实际查阅日为2026-10-22。除明确的正文日期，API `publish_date` 只记官方字段，不假装正文另有该日期；更新、生效 unknown 不补为发布日。每行的URL和范围是本次实际所读，不表示穷尽全部现行规则。

| 编号／具体官方URL | 产品、账号、动作 | 发布／更新／生效及实际范围 | 支撑、限制与复核触发 |
| --- | --- | --- | --- |
| DY-S09 [网暴2026](https://trust.douyin.com/article/40861774235813614)；读取 [公开文章响应](https://trust.douyin.com/thematic/api/trust/article?id=40861774235813614) | 抖音所有用户发布视频、音频、文字、图像及互动；本指南只取大陆普通号 | 正文末句发布实施2026-03-23；字段publish_date同日；独立更新unknown。全13条文字及附则 | 第4条综合指向性／危害性／规模化，合理社会监督须审慎考量；第5条AI批量、编造、开盒、多号等实施／协助／扩大网暴是严重情节；第7条禁侮辱诽谤威胁侵隐私／拉踩引战等；8–12处置、复核、举报和保护。并非多号普禁、评论负面即网暴或申诉保证。涉及他人、争议互动、被网暴／处罚时复核 |
| DY-S10 [热点规则](https://trust.douyin.com/article/15753)；[公开响应](https://trust.douyin.com/thematic/api/trust/article?id=15753) | 抖音所有参与热点传播／讨论的账号；身份核验和变现限制另有条件 | publish_date字段2025-05-27；正文“自发布之日起试行生效”（据字段关联为同日，正文无独立数字日期）；更新unknown。前言至总结全部文字／24条 | 第17条发布社会热点需来源、时间、地点；第10条以当事人或亲友身份发文要求证明，非所有评论者实名材料要求；13条仅争议当事人事件周期暂停含星图商单／广告等变现，14–16违法违规主体治理。并非普通号普遍不得变现。热点内容、身份声明、争议涨粉／变现及处置时复核 |
| DY-S11 [AI滥用专项（一）](https://trust.douyin.com/article/15868)；[公开响应](https://trust.douyin.com/thematic/api/trust/article?id=15868) | 抖音AI内容账号／视频；小程序备案条款只适用于小程序，不压给普通作者 | publish_date字段2025-06-13；更新／生效unknown。Jina全部提取文字，3图未读；API补标题／字段日期 | 1–6类：小程序备案、未经授权形象、伪造形象对口型、夸大惊悚低俗、转售AI账号／秘籍不当获利、教绕审核和主动标识。文中旧按钮仅文中路径；不能代替更新的DY-S02／12。AI仿冒、内容制作、教程或账号交易问题时复核 |
| DY-S12 [内容标识规范](https://trust.douyin.com/article/7151778480801102)；[公开响应](https://trust.douyin.com/thematic/api/trust/article?id=7151778480801102) | 抖音创作者／用户发布作品的一般自主声明，未限企业或星图；本指南取大陆普通号 | 正文首次发布实施2023-09-08；最新修订生效2026-05-11；publish_date字段2026-05-11，不倒写为首次发布。第一章至附则全部文字／含3问 | 2.1五类：AI、个人观点见解、转载、营销推广商品／服务、虚构演绎；2.2真实性准确性合法性、补正限制传播和屡次处罚。Q2正确加标不因此限流，但其他违法违规不豁免；非账号不限流、增长或推荐权重保证。Q3“添加自主声明”是文中路径，1.1已提醒实际显示名称为准。发布上述内容、产品按钮或规则改变时复核 |
| DY-S13 [2026 AI管理公告](https://trust.douyin.com/article/98871770975704696)；[公开响应](https://trust.douyin.com/thematic/api/trust/article?id=98871770975704696) | 抖音用AI工具创作／发布内容账号 | publish_date字段2026-02-13；更新／独立生效unknown；全文4段文字 | 未主动声明AI视频将限制传播；疑似AI标签不替代主动声明；重点治理伪造事件／人物、渲染冲突、侵害未老、AI矩阵批量低质内容。不是AI工具或多账号一律禁止。AI成分、矩阵批量／仿冒或处罚时复核 |
| DY-S14 [真诚分享抵制低质营销提示](https://trust.douyin.com/article/161774333316618)；[公开响应](https://trust.douyin.com/thematic/api/trust/article?id=161774333316618) | 抖音营销创作者／账号；含商品品牌服务推荐展示、测评、引导交易／下载 | publish_date字段2026-03-24；更新／生效unknown；全文导言、4项和末段 | 原文“呼吁”使用平台官方合作推广渠道；不当方式含联系方式引私下交易及优惠话术引向非官方风险应用；鼓励原创亲身体验、动态实用和自然表达，不能把“不鼓励”全部写硬禁。多次违规引流警告／限流／限制投稿，长期低质营销流量限制。未给普通号合作资格／角色细则。营销内容、站外渠道／交易前复核 |
| DY-S15 [主协议入口补读](https://www.douyin.com/agreements/?id=6773906068725565448)；工具最终 [带同id的官方draft](https://www.douyin.com/draft/douyin_agreement/douyin_agreement_user.html?id=6773906068725565448) | 北京抖音科技有限公司（曾用名北京微播视界科技有限公司）及关联方；本次大陆普通个人号；企业机构优先企业协议，非专项放行 | 父层本次匿名web_fetch独立读取标题／导语、1.1–16.4全部提取文字；正文更新2026-02-13、生效2026-02-20；独立发布unknown | 1.1补规则组成／企业优先，14.8平台AI输出风险非创作者免标，15修订通知，16法律／争议／不构成代理等；3.4仍本人使用、3.12六个月可冻结回收非自动注销。工具最终URL／200不是逐跳网络日志或CDN canonical认证。主入口版本通知或注册／协作／发布／商业／争议前复核 |

## 本地材料与机器检查

- 本批 API 响应、5篇解码富文本与文字为 `article-<id>-origin.json`、`article-<id>-decoded.json`、`article-<id>-body.txt`；AI候选另为 `ai-15868-origin.json`、`ai-15868-decoded.json`、`ai-15868.txt/json`。公开布局为 `layout-main.json`、`layout-community_rules.json`；前端阅读片段保存为 `frontend-main.txt`、`frontend-home.txt`、`frontend-safety.txt`、`frontend-article.txt`。以上原始/派生材料被Git忽略，不强制公开第三方全文。
- 5篇文章 API 单次源站 HTTP200、有标题／日期／正文；这个观察仅指公开数据端点，**不假装 article 页面服务端已返回完整HTML**。机器离线报告仍原样 `origin_http_status: unknown`、`reader_http_status: not-observed`、`url_evidence: not-provided`；原始来源对应由上表、布局及API人工链路承担，不伪造Jina信封或改写机器状态。
- 对5份明确解码文字，以当前未改动的工具运行：`python -B tools/check_source_changes.py --source DY-FOLLOWUP-<id> --url https://trust.douyin.com/article/<id> --input <本目录/article-id-body.txt> --report <本目录/article-id-inspection.json>`。均 `baseline-needed`、`authority_updated:false`、`inspection_version:challenge-context-v2`、无reasons/warnings；不是现行／适用性或批准认证。未设baseline、未轮转旧捕获。AI候选Jina报告为reader200、matched-envelope、baseline-needed，同版本；此前旧误报没有自动重写。
- 父层补读摘要为 `parent-mapping-observation.txt`，明确是人工观察摘要、不是本工具capture／机器报告；父层报告的完整提取不能冒充本子任务另存原始全文。主入口缺段本次补核，与前轮不完整事实同时保留。

## 未决明细与落地

1. **已收窄**：一般营销内容自主声明有DY-S12直接依据，不再写“完全没找到平台营销标识”；但它不定义所有赠品／佣金／自有课程情况、不证明普通号可接任意商单，也不取代法律广告可识别性要求。本人按具体产品另核资格、官方合作路径、广告标识、交易、售后及税费。
2. **仍unknown**：普通号当前团队角色是否存在及权限／邀请／退出条件；企业、电商、直播、星图等专项角色和完整细则；注册数量、改名频次、纯构思／文字润色AI边界；任何具体账号通知、真实资格、现UI和办理结果。搜索无关／失败不是“不存在”证据。
3. **保护边界**：网暴判定是综合评估；热点当事人／亲友证明与争议变现限制有触发条件；不扩大到所有用户身份证明、多号普禁、热点一律不能讨论或普通个人号一律不得商业化。投诉、申诉、反馈均无本批通用时限／成功保证。
4. 最小更新只落三份现有抖音主档（保留旧编号与历史锚点，新增DY-S09–15），不改旧review、父层／小红书／tests／工具，不建角色表或运行时。无提交／推送；产品实测与一切平台动作均未执行。

## 交付静态核对

- 已跑 `python -B -m unittest discover -s tests -p test_douyin_delivery.py -v`：现有4项均通过；不是平台测试。
- 三份抖音主档与本审阅的本地链接目标、行尾空白检查通过；规则来源编号DY-S01–15唯一且顺序连续。`git diff --check`无差异错误；其本身不覆盖未跟踪文件，故上述4份另作检查。
- 收尾观察HEAD为 `82fbc69`，本子任务未创建提交；本批审阅及抖音目录仍为未跟踪工作树内容，其余会话改动未暂存／回写。没有后台任务或未收集job。
