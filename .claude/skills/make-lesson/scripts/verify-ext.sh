#!/usr/bin/env bash
# 外部軌 notebook 一鍵驗證：sandbox 全 cell 執行 → 渲染輸出掃描 → 有錯就 exit 1。
#
# 用法（任何 cwd 都行，會自己 cd 到 repo 根）：
#   bash .claude/skills/make-lesson/scripts/verify-ext.sh <topic> <id> [關鍵字 ...]
#   例：bash .claude/skills/make-lesson/scripts/verify-ext.sh llm-apps rag-zh "沒 RAG" "手冊裡沒有寫"
#
# 為什麼要這支：`uv run marimo export` 必須在 repo 根執行（背景工作若 cd 到別處會
# "Failed to spawn: marimo" 默默失敗）；而且 export 的 HTML 看不到渲染結果，要讀
# __marimo__/session/*.json——這裡把三步綁在一起，關鍵字給了就順便印出左頁要引用的數字。
set -euo pipefail
[ $# -ge 2 ] || { grep '^#' "$0" | head -12; exit 1; }
TOPIC="$1"; ID="$2"; shift 2
ROOT="$(cd "$(dirname "$0")/../../../.." && pwd)"
NB="$ROOT/content/$TOPIC/$ID/${ID}_ext.py"
[ -f "$NB" ] || { echo "✗ 找不到 $NB" >&2; exit 1; }
OUT="${TMPDIR:-/tmp}/check_ext_${ID}.html"
LOG="${TMPDIR:-/tmp}/check_ext_${ID}.log"

echo "── export --sandbox: content/$TOPIC/$ID/${ID}_ext.py"
t0=$(date +%s)
if ! (cd "$ROOT" && uv run marimo export html --sandbox "$NB" -o "$OUT" >"$LOG" 2>&1); then
  echo "✗ export 失敗，log 尾端："; tail -20 "$LOG"; exit 1
fi
echo "   ok（$(( $(date +%s) - t0 ))s，log：$LOG）"
echo "── 渲染輸出掃描"
python3 "$ROOT/.claude/skills/make-lesson/scripts/nb-outputs.py" "$NB" "$@"
