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
STATUS_TMP="${TMPDIR:-/tmp}/techradar_run_status.$$"
CRITICAL_FAILED=0
PUSH_STATUS="not_attempted"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }

# 单步容错：失败会记录到 run_status.json；critical 步骤失败时阻断自动 push。
: > "$STATUS_TMP"
step() {
  local key="$1"
  local script="$2"
  local criticality="${3:-optional}"
  "$PYTHON" "$script"
  local rc=$?
  local status="ok"
  if [ "$rc" -ne 0 ]; then
    status="error"
    log "警告：$script 失败（$rc），跳过，继续后续步骤"
    if [ "$criticality" = "critical" ]; then
      CRITICAL_FAILED=1
      log "关键步骤失败：将跳过自动 git push，避免推送混合状态数据"
    fi
  fi
  printf '%s\t%s\t%s\t%s\t%s\n' "$key" "$script" "$criticality" "$status" "$rc" >> "$STATUS_TMP"
  return 0
}

log "=== TechRadar 每日更新开始 ==="
cd "$PIPELINE"

log "1/7 OpenRouter 榜单...";            step "openrouter" "pull_openrouter.py" "optional"
log "2/7 RSS 新闻（含企业/研报）...";      step "rss" "pull_rss.py" "optional"
log "3/7 股票数据...";                    step "stocks" "pull_stocks.py" "optional"
log "4/7 GitHub Trending...";            step "github_trending" "pull_github_trending.py" "optional"
log "5/7 HuggingFace Trending...";       step "huggingface_trending" "pull_huggingface.py" "optional"
log "6/7 SEC 财报...";                    step "filings" "pull_filings.py" "optional"
log "7/7 Claude 打分 + 中文摘要...";       step "score" "pull_score.py" "critical"

log "=== 完成 ==="

# 写出 run_status.json，并重建 _index.json，避免总索引保留已删除数据源。
if [ "$CRITICAL_FAILED" -eq 1 ]; then
  PUSH_STATUS="blocked_critical_failure"
else
  PUSH_STATUS="eligible"
fi
"$PYTHON" "$PIPELINE/write_run_status.py" "$STATUS_TMP" "$PUSH_STATUS" "$CRITICAL_FAILED" || log "警告：run_status.json 写入失败"
"$PYTHON" "$PIPELINE/rebuild_index.py" || { log "警告：_index.json 重建失败，跳过自动 push"; CRITICAL_FAILED=1; }

# 自动推送数据到 GitHub（触发 Pages 重新部署）；关键步骤失败时不推送。
cd "$PROJECT_DIR"
if [ "$CRITICAL_FAILED" -eq 1 ]; then
  log "跳过 git push：存在关键失败，保留本地数据供排查"
elif git rev-parse --git-dir > /dev/null 2>&1; then
  git add data/
  git diff --cached --quiet || git commit -m "data: daily update $(date '+%Y-%m-%d')"
  git push origin main && log "数据已推送到 GitHub" || log "警告：git push 失败，请检查网络或权限"
else
  log "（跳过 git push：尚未初始化 git 仓库）"
fi

rm -f "$STATUS_TMP"
