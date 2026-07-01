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

## 当前焦点
- ✅ 调研已完成，主报告 + 蒸馏交付齐备。
- 待 CD 确认 W1 落地清单（Inoreader Pro 注册、Twitter 列表、飞书 base 三张表）。
- 看板形态选型已给出推荐：**混合方案 D**（飞书多维表入口 + Inoreader 扫描后端 + Readwise 深读 + Cowork artifact 早报 + wewe-rss 中文桥接）。

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
