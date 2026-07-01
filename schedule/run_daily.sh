#!/bin/bash
# TechRadar 每日全量数据更新
# 顺序：OpenRouter 榜单 → RSS 新闻 → 股票 → Claude 打分摘要
# 用法：bash schedule/run_daily.sh（从项目根目录执行）

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
PYTHON="$PROJECT_DIR/pipeline/.venv/bin/python"
PIPELINE="$PROJECT_DIR/pipeline"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }

log "=== TechRadar 每日更新开始 ==="

log "1/4 OpenRouter 榜单..."
cd "$PIPELINE" && "$PYTHON" pull_openrouter.py

log "2/4 RSS 新闻（Techmeme / 量子位 / HN）..."
"$PYTHON" pull_rss.py

log "3/4 股票数据..."
"$PYTHON" pull_stocks.py

log "4/4 GitHub Trending + HuggingFace..."
"$PYTHON" pull_github_trending.py
"$PYTHON" pull_huggingface.py

log "5/5 Claude 打分 + 中文摘要..."
"$PYTHON" pull_score.py

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
