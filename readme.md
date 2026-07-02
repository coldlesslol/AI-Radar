---
project: TechRadar
abbr: RADAR
number: 12
type: Index
author: Cowork
status: draft
date: 2026-06-29
---

# 12-TechRadar / 行业看板（科技雷达）

## 一句话
以 AI 为核心、覆盖上下游衍生的前沿信息与动态追踪看板，服务于行业从业者吸收信息、发现投资与产品机会。

## 范围
- **核心**：AI 模型 / Agent / 平台产品 / 消费级 AI 产品 / 各行业+AI 业务创新 / 追踪类榜单
- **上下游**：算力、芯片、内存、电力、光伏、机器人、具身智能等
- **排除**：生物医药

## 与 100-Investment 的关系
TechRadar = 信息流追踪（行业动态、产品、趋势）；100-Investment = 金融决策面板（二级市场标的、指标、交易）。两边互相引用，不互相混入。

## 当前焦点（2026-07-03）
- ✅ **全部已上线**（GitHub Pages 部署已恢复正常）：https://coldlesslol.github.io/AI-Radar/web/index.html
- ✅ 信源扩展 P1/P2/P3：企业动态监控（智谱/月之暗面/百度/字节/MiniMax/新智元/机器之心/Mistral/Runway/Cohere 共 10 家 Google News RSS）；SEC EDGAR 财报（8 家美股 10-K/10-Q）；深度分析研报（SemiAnalysis/Latent Space/Interconnects/Ahead of AI/Import AI/腾讯研究院/McKinsey）
- ✅ 投资 tab 重构：19 只核心标的（含腾讯 0700 / 智谱 2513 / MiniMax 0100 / SpaceX SPCX，均已上市）+ 大盘行情 5 指数（扁平化卡片，含 QQQ）+ 财报两级下拉 + 研报分页（时效×评分×中文加权，最多 30 条 / 5 页）
- ✅ 操作台（devlog ⚙）：本地 API（`pipeline/api_server.py`:8766）读写 `config/user-config.json`，加股票/信源自动联动行情+RSS+财报+打分白名单，无需改代码
- ✅ 模型 & 榜单：3 数据大卡（OpenRouter/GitHub/HuggingFace）+ 6 入口小卡右侧竖排
- ⚠️ 部署根因已记档：`github-pages` 环境的 protection rule 导致 `deploy-pages` 超时失败（Timeout aborting），已删除该规则；并加 `.nojekyll` + `cancel-in-progress:false` 加固
- 后续：P2 文章页排版 / P3 动效；操作台 `api_server.py` 建议加入 launchd 常驻；新股 MiniMax/SPCX 历史数据短（1/14 天），随交易日累积自动补齐

## 最新交付
- `outputs/调研前置brief--RADAR--Spec.md` —— Kimi Deep Research 任务书
- `inputs/ai-radar.agent.final--RADAR--Report.md` + `work/20260629/...` —— 主报告（~91KB / 25,000+ 字）
- `research/` —— 研究中间件（14 个文件，~575KB）
- `outputs/看板方案建议--RADAR--Spec.md` —— 信源 6 层清单 + 看板形态选型 + 维护 SOP + 12 周落地节奏
- `outputs/核心层汇总--RADAR--Note.md` —— 蒸馏版：5 现象 + 7 洞察 + 40+ Source 按角色分类
- `work/20260629/techradar-mvp-v04.html` —— Cowork artifact MVP v0.4（三 tab + 真实信源入口 + 股票曲线 + AI 摘要）
- **`outputs/数据管道交接--RADAR--Spec.md`** —— Claude Code 接手数据管道的执行清单（数据源 / schema / 文件结构 / 第一周里程碑 / 桥接 Plan A-C）

## 结构
- `inputs/` — 用户提供的原始材料（口述记录、参考链接）
- `work/` — 过程草稿（按日期分桶）
- `outputs/` — 对外可用交付（brief、调研报告归档、看板方案）
