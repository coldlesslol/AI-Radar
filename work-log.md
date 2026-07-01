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
