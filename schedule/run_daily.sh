#!/bin/bash
# TechRadar 每日全量数据更新
# 顺序：OpenRouter 榜单 → RSS 新闻 → 股票 → SEC 财报 → Claude 打分摘要
# 用法：bash schedule/run_daily.sh（从项目根目录执行）

# 注意：不用 set -e。单个信源的瞬时网络抖动不应中止整条管线
# （2026-07-03 openrouter DNS 失败曾导致整天零更新）。每步独立容错。
set -uo pipefail

# launchd 的 PATH 极精简，默认找不到 ~/.local/bin 里的 claude CLI，
# 导致 pull_score 的 shutil.which("claude") 失败。显式补上。
export PATH="$HOME/.local/bin:/opt/homebrew/bin:$PATH"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
PYTHON="$PROJECT_DIR/pipeline/.venv/bin/python"
PIPELINE="$PROJECT_DIR/pipeline"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }

# 单步容错：失败只记警告并继续，不中止后续信源
step() { "$PYTHON" "$1" || log "警告：$1 失败（$?），跳过，继续后续步骤"; }

log "=== TechRadar 每日更新开始 ==="
cd "$PIPELINE"

log "1/7 OpenRouter 榜单...";            step pull_openrouter.py
log "2/7 RSS 新闻（含企业/研报）...";      step pull_rss.py
log "3/7 股票数据...";                    step pull_stocks.py
log "4/7 GitHub Trending...";            step pull_github_trending.py
log "5/7 HuggingFace Trending...";       step pull_huggingface.py
log "6/7 SEC 财报...";                    step pull_filings.py
log "7/7 Claude 打分 + 中文摘要...";       step pull_score.py

log "=== 完成 ==="

# 自动推送数据到 GitHub（触发 Pages 重新部署）
cd "$PROJECT_DIR"
if git rev-parse --git-dir > /dev/null 2>&1; then
  git add data/
  git diff --cached --quiet || git commit -m "data: daily update $(date '+%Y-%m-%d')"
  git push origin main && log "数据已推送到 GitHub" || log "警告：git push 失败，请检查网络或权限"
else
  log "（跳过 git push：尚未初始化 git 仓库）"
fi
