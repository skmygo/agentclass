#!/usr/bin/env bash
# 單課迷你 dist：平行寫課時，不跑全站 build（18+ 課 WASM export、10 分鐘以上）也能對
# **單一純瀏覽器課**做完整冒煙（WASM notebook ＋ 教學頁 ＋ quiz ＋ 手機段）。
# 行為與 build.sh 對單課做的事一致：lesson-mode 判模式、--mode run/edit、auto_instantiate 後處理；
# 差別只在 assets 不抽共用（留在 nb/assets，相對路徑照樣可用）。
#
# 用法（repo 根執行）：
#   bash .claude/skills/make-lesson/scripts/mini-dist.sh <topic> <id> <outdir>
#   python3 -m http.server <port> -d <outdir>          # 用 run_in_background 另起，curl 200 再往下
#   node content/<topic>/<id>/smoke-test.mjs http://127.0.0.1:<port>/<id>/nb/index.html
# 平行子代理各用自己的 <outdir>（帶課名）與 port，互不干擾。
set -euo pipefail
ROOT="$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
[ $# -eq 3 ] || { grep '^#' "$0" | head -12; exit 1; }
TOPIC="$1"; ID="$2"; OUT="$3"
SRC="$ROOT/content/$TOPIC/$ID"
[ -f "$SRC/lesson.py" ] || { echo "✗ $SRC/lesson.py 不存在（外部軌課用 verify-ext.sh，不需要 mini-dist）" >&2; exit 1; }

mode="edit"
[ -f "$ROOT/content/$TOPIC/lesson-mode" ] && mode="$(tr -d '[:space:]' < "$ROOT/content/$TOPIC/lesson-mode")"
[ -f "$SRC/lesson-mode" ] && mode="$(tr -d '[:space:]' < "$SRC/lesson-mode")"
case "$mode" in
  edit) export_mode="edit" ;;
  app)  export_mode="run"
        grep -q '<body[^>]*data-nb-mode="app"' "$SRC/index.html" \
          || { echo "✗ $ID 是 app 模式，但 index.html 的 <body> 缺 data-nb-mode=\"app\"" >&2; exit 1; } ;;
  *) echo "✗ lesson-mode 只能是 app 或 edit（讀到「$mode」）" >&2; exit 1 ;;
esac

rm -rf "$OUT"
mkdir -p "$OUT/$ID"
cp -r "$ROOT/content/shared" "$OUT/shared"
cp "$SRC/index.html" "$SRC/lesson.py" "$OUT/$ID/"
(cd "$ROOT" && uv run marimo export html-wasm "$SRC/lesson.py" -o "$OUT/$ID/nb" --mode "$export_mode" -f)
sed -i 's/"auto_instantiate": false/"auto_instantiate": true/' "$OUT/$ID/nb/index.html"
echo "✓ mini-dist 完成：$OUT（$ID，mode=$export_mode）"
echo "  下一步：python3 -m http.server <port> -d $OUT   然後   node content/$TOPIC/$ID/smoke-test.mjs http://127.0.0.1:<port>/$ID/nb/index.html"
