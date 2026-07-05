---
project: TechRadar
type: Spec
author: Cowork
status: stable
date: 2026-06-29
milestone: 2026-07-05 建设期收尾归档
---

# task — 12-TechRadar

> 🏁 **2026-07-05 建设期收尾归档**：核心功能全上线、每日自愈稳定，开发建设期到此冻结。
> 「每日更新 + 排查日志管理」转入**用户另起的独立任务**。以下为建设期存档，未决项供新任务承接。

## 当前：信源扩展 + 投资 tab 重构 + 操作台（owner: Claude Code，2026-07-03，全部已上线）
1. ✅ P1/P2/P3 信源：10 家企业 Google News 监控 / SEC EDGAR 财报 / 7 家深度研报（含 McKinsey、腾讯研究院）
2. ✅ 投资 tab：19 股（腾讯/智谱/MiniMax/SpaceX 已上市纳入）+ 5 大盘指数扁平卡 + 财报下拉 + 研报时效排序分页
3. ✅ 操作台：`config/user-config.json` + `api_server.py`(:8766) + devlog ⚙ tab，加股票/信源自动全链路联动
4. ✅ 部署故障根治：删 `github-pages` protection rule（deploy-pages 超时根因）+ `.nojekyll` + `cancel-in-progress:false`
5. ✅ UI 修复：股票 canvas id 冲突（第一行趋势）/ 大盘扁平化 / 榜单入口小卡竖排

## 当前：今晚故障修复（owner: Claude Code，2026-07-04，已上线）
"打不开 + 没更新" = 四个独立故障叠加，逐个根治：
1. ✅ 打不开：根地址无 index.html(404) → 加根跳转 `index.html`
2. ✅ digest 停更：claude CLI 半截安装(核心二进制没下完) → 补装完整(v2.1.201) + `run_daily.sh` 显式 PATH，重跑打分补今日 digest
3. ✅ 今日零更新：openrouter 首步 DNS 抖 + `set -e` 拖垮全线 → `run_daily.sh` 改每步独立容错(step 函数，去 -e)
4. ✅ 部署反复失败：确认 timeout 硬顶 10min 改不动、Pages 后端偶发瞬时失败 → 经 API 触发 re-run 成功上线

## 待办 / 待确认（2026-07-04）
- `448a4d0`（deploy timeout 注释更正，纯文档）本地未 push——明晨 daily 会顺带带上，或随手 push
- **部署可靠性无根治**：Pages 后端 flaky 是 GitHub 侧，只能重跑；若哪天线上没更新，先看 Actions 最新 run 是否 failure，failure 就 re-run
- 操作台 `api_server.py` 是否加入 launchd 常驻（现需手动启动才能在 devlog 存配置）
- 移动端实机验收（响应式已写，未真机测）
- 新股 MiniMax(0100)/SPCX 历史数据短，观察后续交易日是否自动补满 30 天
- P1 视觉的 P2 文章页排版 / P3 动效（见 `work/20260702/风格DEMO任务包--RADAR--Prompt.md` 第五节）

## 历史阶段（已完成）
1. ✅ 调研主报告 + 结构化提炼 + 看板方案 + 核心层汇总，全部齐备
2. ✅ Cowork MVP v0.4 形态验证：三 tab + 真实信源入口 + 股票曲线 + AI 摘要
3. **🔄 切到 Claude Code 接手数据管道**：
   - 读 `outputs/数据管道交接--RADAR--Spec.md`
   - 第一步给 CD 看方案（建 4 个目录 + 装 6 个 Python 包），等确认
   - Day 1-7 跑通 P0 5 个数据源（OpenRouter / Techmeme RSS / 量子位 RSS / HN / 股票）
   - Day 6 测试 Cowork artifact 桥接（Plan A/B/C 选型）
4. ⏸ 暂缓项：Inoreader Pro 注册 / 飞书 base 搭建（先等数据管道跑通再判断要不要）

## 等待确认
- W1 清单是否按方案 D 执行？
- 是否同步启动 100-Investment 项目（金融决策面板配套）？
- 是否独立评估「AI 投资人情报基础设施」作为产品/投资命题（详见核心层汇总 洞察 3）？

## 阻塞
- 无。

## 后续候选
- W5–W6：Readwise Reader + 飞书多维表搭建
- W7–W8：wewe-rss Docker 部署 + Cowork artifact 早报原型
- W11–W12：季度复盘 + Phase 3 升级评估
- 与 100-Investment 的数据联动接口（飞书共享视图）
- 季度信源检修 SOP + Scheduled Task
