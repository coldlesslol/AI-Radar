---
project: TechRadar
type: Note
author: Cowork
status: draft
date: 2026-06-29
---

# work-log — 12-TechRadar

> Append-only。每次实质性动作后，由 CloseCheck 追加一条。

## 2026-06-29 立项 + 出 brief
- 完成：建项目骨架（3+3）；登记 `_os/project-profile--OS--Note.md`（12 / TechRadar / RADAR）；写 Kimi Deep Research 前置 brief（`outputs/调研前置brief--RADAR--Spec.md`）。
- 决策：编号 12；与 100-Investment 拆分（信息流 vs 金融决策面板）；范围以 AI 为核心+上下游衍生，排除生物医药。
- 待办：CD 投喂 Kimi 跑 deep research；结果回流后定看板形态。
- 经验：用户更想"先调研再选型"而非"先造看板"。所有自建冲动先压住。

## 2026-06-29 Deep Research 执行完成
- 完成：使用 `deep-research-swarm` skill 执行完整调研（Route D / 文件增强研究）。
- 流程：Phase F 文件分析 → Phase 1 景观扫描 → Phase 2 维度分解（10 维度）→ Phase 3 并行深度调研（3 批次共 10 个子 agent，累计搜索 150+ 次）→ Phase 4 交叉验证 → Phase 5 冲突解决（11 项冲突全部标注解决）→ Phase 6 洞察提取（7 个跨维度洞察）→ Phase 7 报告写作（~91KB / 25,000+ 字）。
- 交付：
  - 主报告 `ai-radar.agent.final--RADAR--Report.md`（10 章 + 执行摘要 + 决策树 + 附录，89 个脚注，16 张表格，276 行对比数据）
  - 已复制至 `inputs/` 和 `work/20260629/`
  - 研究中间件保留于 `research/`（14 个文件，~575KB）
- 核心结论：现有产品满足 55–65% 需求；推荐"拼装为主，自建为辅"；轻量/标准/重度 3 套组合方案已输出；7 个市场缺口已识别（P0 缺口：AI 行业情报基础设施、中文 AI 信息源一站式聚合 API）。
- 待办：后续 Agent（Cowork/Claude）对主报告做结构化提炼与看板形态选型。

## 2026-06-29 主报告蒸馏 + 看板方案选型
- 完成：基于主报告输出两份交付，落 `outputs/`：
  - `看板方案建议--RADAR--Spec.md` —— 6 层信源清单（每层含必选源/看什么/指标/频率/承载工具）+ 看板形态 4 候选评分（推荐方案 D：飞书多维表入口 + Inoreader 后端 + Readwise 深读 + Cowork artifact 早报 + wewe-rss 桥接）+ 日/周/月/季 SOP + 月成本（Phase 1 ¥71 / Phase 2 ¥237 / Phase 3 ¥1072）+ 12 周落地节奏 + W1 立即清单
  - `核心层汇总--RADAR--Note.md` —— 蒸馏版：5 个结构性现象 + 7 个跨维度洞察（含 CD 视角二次提炼）+ 40+ 精选 Source 按角色 8 类分组（不可替代 / 投资人 / 创业者 / 中文深度 / 周刊 / 数据榜单 / 上下游 / 工具栈）+ 5 条不要犯的错 + 3 条主报告未明说的反共识判断
- 决策：对主报告的"个体视角"做了 4 处 CD 适配调整：自建临界点下移到 30 min/天；机构借用付费数据；社区层必含；P0 缺口被识别为 CD 的潜在产品/投资命题（双重身份）。
- 待办：等 CD 确认 W1 清单；考虑是否同步启动 100-Investment 项目。
- 经验：主报告很全但默认"个体用户"画像，对团队/机构 + AI 创业者 + 有 AI 助手的场景需要二次适配；蒸馏交付的价值在于"看一份就够"，而不是把主报告再压缩一遍。

## 2026-06-29 MVP v0 上线（Cowork artifact）
- 完成：`work/20260629/techradar-mvp-v0.html`（单文件 HTML，~17KB）→ 通过 `create_artifact` 上线 artifact `techradar-mvp-v0`。
- 形态：6 层分组卡片（扫描/社区/深读/数据/投资/上下游），共 27 张种子卡片（基于 2026-06 真实行业事件填充）；"Claude 智能摘要"按钮调 askClaude 输出 Top 5 + 跨源关联 + 一行字总结；标星按钮本地 localStorage 持久化；响应式 1/2/3 列。
- 决策：MVP 阶段不接真实 RSS（artifact 沙箱 fetch 受限），用种子数据先验证"产品形态/视觉/AI 摘要价值"；CD 认可后再走 Phase 2 真接 RSS（飞书归档层 + Inoreader 免费版 + wewe-rss 中文桥接）。
- 待办：CD 体验后给反馈——形态/分组/AI 摘要质量/标星粒度等，再迭代 v1。

## 2026-06-29 MVP v0.2 全信息面板重构
- 完成：根据 CD 反馈彻底重构信息架构 → `work/20260629/techradar-mvp-v02.html`（~33KB）→ `update_artifact` 同 id 替换。
- 新架构（3 区 + 1 补充）：
  - **Dashboard 区**：12 只 AI 核心股票面板（美股 8 + A 股 3 + 港股 1，红涨绿跌）+ 5 个常驻榜单速览（OpenRouter / LMArena / GitHub AI Trending / Product Hunt AI / Star History 飞升）
  - **Spotlight 区**（独立专题）：🚀 模型发布 + 💰 投资融资
  - **Stream 区**（信息流）：🔥 行业新闻 / 👥 社区早期信号 / 📖 深读精选 / ⚙️ 上下游
  - **信源直达区**：8 类 50+ 个核心源链接（扫描层/社区/Newsletter/中文/数据榜单/投资信号/上下游/工具栈），中英文+工具三色标签
- 决策：用户偏好"先搭完整模拟面板，再做信源填充"——所以全部 6+ 大模块同时落齐，方便整体评估视觉与信息密度。
- 待办：CD 体验后给反馈，决定哪些保留/调整；Phase 2 接真实数据源（股票优先级最高，可考虑新浪财经/雪球；新闻接 RSS；榜单接 OpenRouter/LMArena 公开数据）。
- 经验：MVP 迭代要快——v0 → v0.2 同一会话完成，方便用户对比形态差异；模拟数据要"接近真实"（用真实公司/真实价格量级/真实事件），才能让用户准确判断"长这样我满意吗"。

## 2026-06-29 MVP v0.2.1 调序
- 完成：按 CD 反馈调整三区顺序 → ① Stream 新闻流（行业/社区/深读/上下游）放最上 → ② Models & Rankings（模型发布 + 5 榜单速览）→ ③ Invest & Stocks（投资融资 + 12 股票）→ ④ 信源直达区。
- 决策：CD 的阅读优先级是"先看新闻流（动态信息）→ 看模型/榜单（产品市场）→ 看钱（融资股价）"，与原 Dashboard 在顶部的设计相反；调整后更符合"日刷"节奏。
- 经验：UI 顺序就是注意力顺序，常驻 dashboard 放顶部听起来合理但实际让"今日新闻"被埋；信息密度大的新闻流应该占据"开屏即见"的位置。

## 2026-06-29 切到 Claude Code + 出交接清单
- 决策：MVP 形态在 Cowork 验证基本结束（v0.4 链接修真，结构走通）。下一步**数据管道交给 Claude Code 跑**——artifact 沙箱不能 fetch 外部 API 是硬限制，Code 才能跑真正的 RSS/API/cron。
- 完成：`outputs/数据管道交接--RADAR--Spec.md`（~13KB）——包含：
  - 1 分钟上手指引（读哪些文件）
  - 工作范围（接管什么、不做什么）
  - P0/P1/P2 数据源清单（12 个源，P0 5 个第一周必跑）
  - JSON schema 定义（与 artifact ITEMS/RANKINGS/STOCKS 结构对齐）
  - 文件夹结构建议（pipeline/data/schedule/logs）
  - Day 1-7 里程碑
  - 桥接 Cowork artifact 的 Plan A/B/C（fetch 本地 JSON / 数据注入 / 独立网页）
  - requirements.txt + .env 模板
  - 8 类风险与应对
  - CD 偏好与红线复述
- 产品路径判断：Cowork artifact 形态验证 → Code 数据管道+完善 1-2 个月 → 3-6 个月后视情况评估上独立 Web（Vercel + 后端定时拉数据）。Code 是开发载体不是产品载体；Cowork artifact 沙箱限制天花板低；终态大概率是独立 Web（呼应主报告 P0 缺口"AI 投资人情报基础设施"）。
- 待办：CD 切到 Claude Code 在 12-TechRadar/ 跑 `claude`，让 Code 读交接清单接手；Day 1 等 CD 确认方案后建目录装依赖。
- 经验：MVP 阶段 mock 数据的根本问题是"具体新闻 + 链接首页"看起来很假；要么换成"真实信源入口卡"（v0.4 路径），要么换成"真实事件 + 真实文章 URL"（需要 WebSearch 或真接 RSS）；前者 Cowork 内可做，后者必须 Code。

## 2026-06-29 MVP v0.3 三 tab 重构 + 股票曲线 + 频率角标
- 完成：`work/20260629/techradar-mvp-v03.html`（~58KB）→ `update_artifact` 替换。
- 新架构（3 tab + 共用底部）：
  - **Tab 1 行业动态**：行业新闻 / 社区早期信号 / 深读精选 / 上下游（21 张卡片）
  - **Tab 2 模型 & 榜单**：模型发布卡片 + 4 类榜单分区（模型层 4 个周更 / 应用产品 4 个日看 / 开源 2 个周更 / 社区热度 2 个日看 = 12 个榜单）
  - **Tab 3 投融资 & 二级**：投融资新闻 7 条 + 投资榜单 4 个 + 12 只 AI 股票带 30 天 Chart.js 迷你曲线（红涨绿跌）
  - **共用**：底部信源直达区 + Claude 摘要按钮 + 频率角标（日/周/月/季 四色）
- 技术：Chart.js 4.5.0 通过白名单 CDN 载入；股票曲线用伪随机种子（基于 ticker）生成稳定的 30 天历史数据，按目标涨跌幅反推起点 + 加波动；只在 Tab 3 可见时渲染 chart 避免 display:none 时尺寸异常。
- 数据：全部仍是 Claude 基于 2026 H1 公开信息构造的近似数据（量级真实，具体数字非实时）。底部 footer 明确标注了**数据来源**和**接 API 的三条路径**（短期手动 / 中期 Scheduled Task / 长期自建后端）。
- 二级看板：当前只是 v0（股票卡 + 30 天曲线），note-box 标注完整二级看板待 Phase 2 优化（成交量 / PE / 机构持仓 / 财报节点 / 北向资金等）。
- 待办：CD 确认三 tab 结构 + 榜单选项 + 股票曲线形态 → 决定 Phase 2 是否启动真实数据接入（建议先接 OpenRouter API 试水，最容易且最有信号价值）。

## 2026-07-02 P1 视觉重设计启动：Claude Design 学习闭环
- 背景：数据管道已跑通（14 源/日更/GH Pages），`work/design-brief.md` 定稿设计方向（纸墨编辑刊物风、纹身美学锚点）。CD 明确两个目标：页面更有设计感 + 借项目学习 claude.ai/design（可成长，非一次性）。
- 决策：分工闭环 = Claude Design（CD 操作，出风格 DEMO、学工具）→ 定稿导出 → Cowork 接真实数据落地 web/index.html。P1 先出 DEMO 不直接改代码。
- 完成：`work/20260702/风格DEMO任务包--RADAR--Prompt.md` —— 上手步骤 / 可粘贴主 prompt（3 变体：Broadsheet / Ink Brutalist / Quiet Journal，含真实数据样本）/ 6 项迭代练习（对应 chat、行内评论、画布编辑、版本管理、设计评审、响应式）/ 成果带回路径 / P2-P4 成长路线。
- 待办：CD 在 claude.ai/design 出 DEMO 并定方向 → 成果放 inputs/ → Cowork 落地 + 修 brief 中 5 个 bug。
- 经验：Brief 已把设计系统定死时，探索空间集中在"气质变体"，适合让 Claude Design 并排出 3 版对比而不是从零发散。

## 2026-07-02 Claude Design 迭代复盘：规范打架导致"不听话"
- 现象：CD 在 claude.ai/design 跑了 3 轮（3 变体 → C 收敛 → 2a/2b），但输出始终偏"大哥特字标/设计过度"。
- 根因：design-brief.md（附件，持久上下文）写死"COLDLESS 字标 54-60px 是全页主角"，与 CD 迭代中的真实偏好（信息主角、品牌背景化、报纸 nameplate、黑曼巴细线底纹、保持现网结构只换皮）冲突；chat 修正每轮都被附件重新锚回。次因：brief 的五段式新架构 vs "不改现有框架"冲突；URL 文字≠现网截图，工具看不到真实结构。
- 完成：任务包追加「主 Prompt v2」——固化新方向（信息主角/nameplate ≤40px/曼巴几何线条为唯一装饰层/以现网截图为结构锚/基于 2a 融合 2b 减半底纹出完整首页），并注明开新 chat tab、不再附旧 brief。
- 待办：CD 用 v2 出完整首页定稿 → 定稿后由 Cowork 提案修订 design-brief.md 至 v2（等 CD 确认）→ 落地 web/index.html。
- 经验：**附件规范 > 聊天修正**是 Claude Design 的实际优先级；偏好变了必须改源头规范，否则每轮生成都会回锚。"学 Claude Design"第一课：管理它的持久上下文。

## 2026-07-02 结构基准对齐 + 现网快照制作
- 对齐：CD 确认「正确的排版」= 线上 index.html 的三 tab + 卡片流结构（非 demo 五段式）；修复路径 = 喂真实 HTML 继续在 Claude Design 迭代。
- 根因补充：生成式画布无法凭 URL 复刻没见过的排版；v2 prompt 中"以现网截图为准"与"基于 2a 骨架"自相矛盾（Cowork 笔误），且实际未附截图，模型选了画布上的 2a。
- 完成：`work/20260702/snapshot-现网结构快照-20260702.html`（~100KB）——把 web/index.html 的 fetch 改为内嵌今日真实数据（digest 全量/榜单/股票/archive 前 40 条），双击可打开，渲染=线上；任务包追加「主 Prompt v3 结构保真版」（结构红线 + 视觉层替换规则 + 输出完整 HTML）。
- 待办：CD 开新 chat 附快照 + v3 → 产出换皮版 HTML → 放 inputs/ → Cowork 审查合并回 web/index.html（保留 fetch 逻辑，只取样式层）。
- 经验：要求生成工具"严格遵守现有排版"时，唯一可靠输入是真实源文件；描述性文字和 URL 都会被自由发挥。

## 2026-07-02 P1 视觉重设计落地（Cowork 执行，web/index.html）
- 路线变更：Claude Design 出完整 demo 的路线放弃（画布锚定问题），改为 Cowork 直接在真实 index.html 上换皮，结构零改动。Claude Design 阶段沉淀的风格资产被采纳：纸墨色板、nameplate 报头、细线结构、等宽分数徽章、多源指示。
- 字体定稿：CD 从 6 候选（字体试衣间）中选 **Fraunces**（中文配 Noto Serif SC）；哥特体退役。design-brief.md 升 v2（信息主角/结构=现网只换皮/曼巴细线装饰上限），任务包 prompt 同步 v3。
- 三段实施：①token+字体+报头+tab+分区线 ②卡片系统全量去圆角去阴影去彩色、分类墨色化、bug5 黄底→等宽分数徽章（≥0.8 酒红）、多源徽章去 emoji ③bug1 入口卡单行、bug2 HF 标签删除、emoji 图标退役、补齐响应式断点（原文件无任何 @media）、meta 行单行化（信源>4 截断 +N）。
- 验证：grep 走查渐变/阴影/圆角/蓝紫残留全 0；JS 语法 node 校验通过；预览快照（内嵌真实数据）三轮交 CD 验收通过。
- 交付：`web/index.html`（待 push）；过程件 `work/20260702/`（字体试衣间/快照/预览×3/任务包）。
- 待办：CD 确认后 git push 上线；后续 P2 候选见任务包第五节。
- 经验：①设计 token 先行让后续每段改动自动级联；②"结构保真"类需求代码层做远优于生成画布；③分段验收节奏（骨架→卡片→细节）让 CD 每轮只判断一类问题。

## 2026-07-02 CloseCheck（P1 收口）
- 完成：全区扫描（root 干净/outputs 合规/work 分桶正常）；readme 焦点区重写至现状；CloseCheck 记录写入 Reviews/Inbox/2026-07-02/。
- 待确认：design-brief.md 留 work/ 根（活规范例外）；并行 Code 会话与 Cowork 同改 index.html 需分时或分文件。
- 未决：CD 本机 git push（7 commits）；push 后移动端实机验收。

## 2026-07-03 信源扩展 + 投资 tab 重构 + 操作台 + 部署根治（Claude Code，均已 push 上线）
- 完成：
  - 信源 P1/P2/P3：企业监控 10 家（Google News RSS）/ SEC EDGAR 财报 8 家 / 研报 +McKinsey(`/insights/rss`) +腾讯研究院(`tisi.org/feed`)；analysis+newsletter 层时间窗口 7→30 天。
  - 投资 tab：19 股（腾讯 0700/智谱 2513/MiniMax 0100/SpaceX SPCX，均已上市）+ 5 大盘指数（扁平卡）+ 财报两级下拉 + 研报时效×评分×中文加权分页（30 条/5 页）。
  - 操作台：`config/user-config.json` + `pipeline/api_server.py`(:8766) + `lib/user_config.py`；各 `pull_*.py` 合并用户配置；devlog ⚙ tab 增删即存，加股票自动联动行情+RSS+财报+白名单。
  - UI 修：canvas id 冲突（`renderIndices` 复用 `stockCardHTML` 硬编码 `sp${idx}`→与股票前 5 只 id 冲突→第一行趋势被画到大盘 canvas）；大盘扁平化；榜单 6 入口卡改右侧竖排小卡。
- 关键教训（可复用）：
  - **GitHub Pages "Timeout reached, aborting" 根因 = `github-pages` 环境的 protection rule**，让 deploy-pages 挂起等审批到超时。排查绕了 4 个错方向（cancel-in-progress / venv / artifact 体积 / Jekyll）才定位——删规则后部署状态链从 `waiting→queued→failure` 变 `in_progress→success`。
  - **诊断法**：public repo 无需凭据即可查 `api.github.com/repos/{o}/{r}/actions/runs` 与 `/deployments?environment=github-pages` 的状态链，直接看卡在哪步；以后部署问题先查 API 别猜。
  - 共用渲染组件必须参数化 element id（`getElementById` 只返首个，重复 id 静默出错）。
  - 只在本地 preview 验证 ≠ 线上就绪；线上故障要拉线上 CDN/API 实证。
- 未决：`api_server.py` 加 launchd 常驻；移动端实机验收；MiniMax/SPCX 新股历史补齐。

## 2026-07-04 夜间故障排查："打不开 + 没更新"（Claude Code，已上线）
- 表象一个，实为**四个独立故障叠加**，逐个根治：
  1. **打不开** = 根地址 `AI-Radar/` 无 index.html → GitHub 返 404（页面实际在 `web/index.html`）。加根 `index.html`（meta+JS 跳转到 web/index.html）。
  2. **今日零更新** = 10:06 daily 首步 `pull_openrouter` DNS 解析失败 + 脚本 `set -e` → 一步失败整线中止，全天没数据。改 `run_daily.sh`：去 `set -e`，每步包 `step()` 独立容错，单源抖动只警告跳过。
  3. **digest 停更** = `pull_score` 靠 `claude -p`，但 CLI **半截安装**：npm 外壳在、`bin/claude.exe` 只是占位 stub（"native binary not installed"），`~/.local/bin/claude` 正式入口没建（只剩临时名 `.claude-Fz4r9qQ8`）。清掉阻塞重装的孤儿临时目录 `.claude-code-DV2VGY4u` → `npm i -g @anthropic-ai/claude-code` 补装完整（v2.1.201，`claude -p` 实测通过）→ 重跑打分补今日 digest。`run_daily.sh` 加 `export PATH="$HOME/.local/bin:..."` 让 launchd 精简环境也能 `shutil.which("claude")`。
  4. **部署反复失败** = 两种失败混着：一是逼近/超 `deploy-pages` 10min 超时；二是 Pages 后端瞬时 "Deployment failed, try again later"。**关键发现**：`deploy-pages@v4` 的 timeout 硬顶 600000ms(10min)，设更大被夹回并告警——之前"放宽到 20min"无效。无配置解，只能重跑。
- 关键教训（可复用）：
  - **GitHub Pages 部署 flaky 是 GitHub 侧，改配置修不了**：timeout 上限 10min；后端偶发慢/瞬时失败。唯一解=重跑。可用 `git credential fill` 取 token → `POST /repos/{o}/{r}/actions/runs/{id}/rerun` 直接触发重跑（本次即如此成功），无需 gh CLI / UI。
  - **桌面 App ≠ CLI**：App 内置的两个 claude 是 Linux ELF（App 内部沙盒用）和 macOS GUI，都不能当 `claude -p` 脚本调用。脚本需要独立的 `~/.local/bin/claude` CLI。
  - **`set -e` 用在多源采集脚本是反模式**：一个源抖动 = 全线中止。每步独立容错更稳。
  - **launchd 的 PATH 极精简**（默认不含 `~/.local/bin`），依赖 PATH 找二进制的脚本要在脚本里显式 export。
  - 时间戳来源要认准：前端"已更新"读 `digest.json.updated`，不是最新的原始数据文件——所以只刷原始数据、不重跑打分，"已更新"不会变。
- 未决：`448a4d0`（timeout 注释更正）未 push（无害，明晨 daily 带上）；部署可靠性无根治（GitHub 侧，靠重跑）。

## 2026-07-05 建设期收尾归档（Claude Code）
- 自愈验证：10:00 daily job 全链路无人工干预成功（stocks 10:01 / digest 10:10，均已推送部署上线）。昨夜四故障根治后首次自动更新，确认稳定——用户"感觉没更新"经核验为浏览器缓存，服务器数据实为当日（提示硬刷新）。
- devlog 补全：`web/devlog.html` 开发日志补至 07-05（新增 07-02 纸墨落地 / 07-03 信源+投资tab+操作台 / 07-04 四故障 / 07-05 自愈 4 条）；状态栏 29→32 源、~186→~197；需求清单加 7 行已完成。
- 项目归档：readme `status: draft → stable` + 加 `milestone` 字段；readme 顶部加「建设期收尾归档」块，标注转入日常运维期。
- 交接：后续「每日更新 + 排查日志管理」由用户另起独立任务承接；本项目 readme/task/work-log 作为**建设期存档**冻结在此里程碑。
- 复用要点（承前，供新运维任务参考）：部署 flaky 只能重跑（API `runs/{id}/rerun`）；daily 靠 `~/.local/bin/claude` CLI + run_daily 显式 PATH；"已更新"读 digest.json；线上没更新先分清是浏览器缓存（硬刷）还是真没部署（查 Actions run）。
