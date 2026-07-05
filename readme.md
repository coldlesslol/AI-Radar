---
project: TechRadar
abbr: RADAR
number: 12
type: Index
author: Cowork
status: stable
date: 2026-06-29
milestone: 2026-07-05 建设期收尾归档（核心功能全上线 + 每日自愈稳定）
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

## 当前焦点（2026-07-05 晚 · 信源统一重构，已上线）
归档后当日又完成一轮用户驱动的重构（说明项目仍在演进，非硬冻结）：
- ✅ **统一公司总表** `pipeline/lib/companies.py`：投资标的 = 财报 = 企业新闻监控，同一套基准。一家标的自动带齐 股价+财报+企业新闻；在标的基础上补充"关注·未持仓"。
- ✅ 覆盖：股价 19 · SEC 财报 10（补 ARM/Oracle）· A股/港股财报 8（雅虎财务页）· 企业监控 26 · AI 媒体 2（新智元/机器之心分离）· **DeepSeek** 入监控。每个投资标的都有新闻监控（原仅 2）。
- ✅ **付费墙过滤** `pipeline/lib/paywall.py`：只砍"硬墙"外链（财新/WSJ/FT/彭博/The Information/日经/经济学人/Barron's），计费墙站（MIT TR 等）保留——不再整媒体误杀；实测 `isAccessibleForFree` 不可靠，故用硬墙名单。全链路清理含历史遗留。
- ✅ **NaN 崩溃根治**：沪深300 `price:NaN` 破坏 stocks.json → 前端全挂；pull_stocks 剔除 NaN + 单只重试 3 轮，`write_json` `allow_nan=False` 兜底。
- ✅ dev 监控清单 tab 加**完整信源总览**（新闻信源全表 + 企业信源 26 + 非文章数据源）。
- 线上已验证：digest 62 条无 caixin / 股价无 NaN / 港股"财务报表"链接 / DeepSeek feed 200 / devlog 总览。

## 🏁 建设期收尾归档（2026-07-05，节点参考）
> 注：此归档为当日早间节点；随后又做了上方"信源统一重构"，项目实际持续演进中。
本项目核心功能建设到此达成里程碑，转入以运维为主 + 按需迭代：
- ✅ 核心功能全部上线：三大 tab（要闻/模型榜单/投资）+ 操作台 + 32 信源 + Claude 打分管线 + P1 纸墨视觉。
- ✅ **每日自愈稳定**：10:00 launchd → 拉数据 → claude 打分 → 提交推送 → Pages 部署，全链路无人工干预（07-05 已验证）。
- ✅ 开发日志已在 `web/devlog.html` 补全至 07-05（含四故障排查全程）。
- ➡️ 后续「每日更新 + 排查日志管理」由**用户另起的独立任务**承接；本 readme/task/work-log 作为建设期存档冻结在此里程碑。
- ⚠️ 唯一长期须知：GitHub Pages 部署偶发 flaky（GitHub 侧，非配置可修），线上没更新时看 Actions 最新 run，failure 则 re-run。

## 当前焦点（2026-07-04）
- ✅ **今晚故障已全部修复并上线**（根地址可开 + 今日数据 + 今日 digest 全绿）：https://coldlesslol.github.io/AI-Radar/web/index.html
- ⚠️ 运维须知：**GitHub Pages 后端偶发慢/瞬时失败**（"Deployment failed, try again later"），且 `deploy-pages` timeout 硬顶 600000ms(10min) 改不动——**唯一解是重跑**；重跑可用凭据经 API 触发（`actions/runs/{id}/rerun`），或 GitHub UI Re-run，或等次日 daily。
- ✅ 每日 daily job 已健康：CLI 补装完整 + `run_daily.sh` 每步容错 + 显式 PATH，10:00 自动拉数据+打分+部署。
- （历史，仍有效）信源 P1/P2/P3、投资 tab 19 股+5 大盘、操作台、模型&榜单小卡 —— 见下方 07-03 焦点条目。

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
