#!/usr/bin/env bash
# 建課 scaffold：把模板複製與機械代換一次做完，讓創作只剩「notebook 內容」與「頁面內容區」。
#
# 用法（repo 根目錄執行）：
#   bash .claude/skills/make-lesson/scripts/new-lesson.sh <id> "<課名>" <topic-slug> "<主題名>" [--external [--gpu]]
# 例：
#   bash .claude/skills/make-lesson/scripts/new-lesson.sh clustering "分群：沒有答案也能找出結構" ml-basics "學基礎機器學習"
#
#   <id>          課程英文 slug（= content/<topic>/<id>/ 目錄名 與 網址 /<id>/，全站唯一）
#   <課名>        進 page <title>/h1、notebook app_title/h1、smoke-test H1_TEXT
#   <topic-slug>  主題 slug（主題頁不存在時只提醒、不代建——新主題照 site.md 手動起）
#   <主題名>      進 header 主題連結與課末「回主題」文字
#   --external    外部軌課（Pyodide 跑不了：需 GPU / 無 WASM wheel / 需真網路）：
#                 唯一一份 notebook <id>_ext.py 在 molab 執行，頁面右欄是導流面板、
#                 無內嵌 notebook。定軌先跑 pyodide-spike.mjs 實測，不要用猜的。
#                 課程只做一版程式——不做「瀏覽器迷你版＋外部真實版」雙版本。
#                 預設是純 CPU 課（面板寫「免費 CPU 環境即可」、不留 GPU 檢查 cell）；
#   --gpu         真的需要 GPU 的外部軌課才加：保留面板的「選 GPU Server」步驟與 GPU 檢查 cell。
#
# 做完的事：三件套複製＋代換、生成自檢、root uv sync（純瀏覽器課）。
# 不用做的事：build.sh（自動發現兩種課）、pyproject（全站共用 repo 根的一份）。
# 留給你創作/接線：notebook 內容、頁面內容區、主題頁課卡、首頁課數、前一課的「下一課」。
set -euo pipefail

if [ $# -lt 4 ]; then
  grep '^#' "$0" | head -21; exit 1
fi

ID="$1"; TITLE="$2"; TOPIC="$3"; TOPIC_NAME="$4"; MODE="${5:-}"; GPU="${6:-}"
SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
TPL="$SKILL_DIR/assets/templates"
ROOT="$(git -C "$SKILL_DIR" rev-parse --show-toplevel)"
DEST="$ROOT/content/$TOPIC/$ID"

[ -d "$DEST" ] && { echo "✗ content/$TOPIC/$ID 已存在，先處理掉再跑" >&2; exit 1; }
[[ "$ID" =~ ^[a-z0-9-]+$ ]] || { echo "✗ id 只能小寫英數與連字號：$ID" >&2; exit 1; }
[[ "$TOPIC" =~ ^[a-z0-9-]+$ ]] || { echo "✗ topic slug 只能小寫英數與連字號：$TOPIC" >&2; exit 1; }
[ -z "$MODE" ] || [ "$MODE" = "--external" ] || { echo "✗ 不認識的參數：$MODE（只有 --external）" >&2; exit 1; }
[ -z "$GPU" ] || { [ "$GPU" = "--gpu" ] && [ "$MODE" = "--external" ]; } || { echo "✗ --gpu 只能接在 --external 後面" >&2; exit 1; }
# 課程網址在根層（/<id>/），id 必須全站唯一（兩種課都算）
if compgen -G "$ROOT/content/*/$ID" > /dev/null; then
  echo "✗ 課程 id 已被其他主題使用：$ID" >&2; exit 1
fi

# molab 網址用的 owner/repo（外部軌課的頁面與 notebook 連結）
OWNER_REPO="$(git -C "$ROOT" remote get-url origin | sed -E 's#\.git$##; s#.*[:/]([^/]+/[^/]+)$#\1#')"

mkdir -p "$DEST"

subst_page() {  # $1=模板檔
  sed -e "s/LESSON_ID/$ID/g" \
      -e "s/TOPIC_SLUG/$TOPIC/g" \
      -e "s/主題名稱/$TOPIC_NAME/g" \
      -e "s/課程主標題/$TITLE/" \
      -e "s/課程標題/$TITLE/" \
      -e "s#OWNER/REPO#$OWNER_REPO#g" \
      "$1"
}

if [ "$MODE" = "--external" ]; then
  # ── 外部軌課：<id>_ext.py（唯一的程式版本）＋ 導流頁 ＋ 頁面冒煙
  sed "s/課程標題/$TITLE/g" "$TPL/lesson_ext.py" > "$DEST/${ID}_ext.py"
  sed -e "s/課程標題/$TITLE/g" -e "s/LESSON_ID/$ID/g" \
      "$TPL/smoke-test-ext.mjs" > "$DEST/smoke-test.mjs"
  subst_page "$TPL/page_ext.html" > "$DEST/index.html"
  if [ "$GPU" = "--gpu" ]; then
    # GPU 課：留 GPU 步驟與檢查 cell，拿掉「免費 CPU 即可」字樣與標記
    sed -i -e 's#<!--CPU-ONLY-->.*<!--/CPU-ONLY-->##' -e 's#<!--GPU-ONLY-->##; s#<!--/GPU-ONLY-->##' "$DEST/index.html"
    sed -i -e '/^# --GPU-CELL-START--/d' -e '/^# --GPU-CELL-END--/d' "$DEST/${ID}_ext.py"
  else
    # 純 CPU 課（預設）：拿掉 GPU 步驟整行與 GPU 檢查 cell 整格，留「免費 CPU 即可」
    sed -i -e '/<!--GPU-ONLY-->/d' -e 's#<!--CPU-ONLY-->##; s#<!--/CPU-ONLY-->##' "$DEST/index.html"
    sed -i '/^# --GPU-CELL-START--/,/^# --GPU-CELL-END--/d' "$DEST/${ID}_ext.py"
  fi

  # 生成自檢：頁面必備元素缺一不可，不能默默出貨
  for must in "</head>" "lesson.css" "splitter.js" "molab.marimo.io" "${ID}_ext.py"; do
    grep -qF "$must" "$DEST/index.html" || {
      echo "✗ 教學頁生成不完整（缺 $must）" >&2; exit 1; }
  done
  grep -q "GPU-ONLY\|CPU-ONLY\|GPU-CELL" "$DEST/index.html" "$DEST/${ID}_ext.py" && {
    echo "✗ GPU/CPU 標記沒清乾淨" >&2; exit 1; }
  python3 -c "import ast,sys; ast.parse(open(sys.argv[1]).read())" "$DEST/${ID}_ext.py" || {
    echo "✗ ${ID}_ext.py 語法不合法（GPU cell 移除出錯？）" >&2; exit 1; }
else
  # ── 純瀏覽器課：lesson.py ＋ 內嵌 notebook 頁 ＋ WASM 冒煙
  sed "s/課程標題/$TITLE/g" "$TPL/lesson.py" > "$DEST/lesson.py"
  sed "s/課程標題/$TITLE/g" "$TPL/smoke-test.mjs" > "$DEST/smoke-test.mjs"
  subst_page "$TPL/page.html" > "$DEST/index.html"

  for must in "</head>" "lesson.css" "lesson.js" "splitter.js" "nb-status" "data-ready-figures"; do
    grep -qF "$must" "$DEST/index.html" || {
      echo "✗ 教學頁生成不完整（缺 $must）" >&2; exit 1; }
  done

  # 全站共用 venv 就緒（pyproject 在 repo 根；外部軌課用 PEP 723 sandbox，不需要）
  (cd "$ROOT" && uv sync -q)
fi

echo "✓ content/$TOPIC/$ID 骨架就緒（build.sh 會自動發現本課，不用改）"
[ -f "$ROOT/content/$TOPIC/index.html" ] || echo "⚠ content/$TOPIC/index.html 不存在：新主題請照 site.md 從 topic 模板手動建"
if [ "$MODE" = "--external" ]; then
  cat <<EOF
接下來輪到你（頁面用 Edit 改內容區，別整檔重寫）：
  1. content/$TOPIC/$ID/${ID}_ext.py — 課程內容（唯一的程式版本：大量 md 解說、自成完整教材、
     emoji 章節錨點；PEP 723 依賴）
  2. content/$TOPIC/$ID/page_content.py — 寫 TITLE/DESCRIPTION/STYLE/WRAP/SCRIPT/NB 常數，然後
     python3 .claude/skills/make-lesson/scripts/page-fill.py content/$TOPIC/$ID 填進 index.html
     （小修也可直接 Edit index.html；但正本以 page_content.py 為準，改完重跑 page-fill）
  3. content/$TOPIC/$ID/smoke-test.mjs — H1_TEXT 確認與頁面 h1 一致
  4. wiring — 主題頁課卡、首頁主題卡課數、前一課的「下一課」連結
驗證：bash .claude/skills/make-lesson/scripts/verify-ext.sh $TOPIC $ID [左頁要引用的關鍵字...]
冒煙：bash .claude/skills/make-lesson/scripts/smoke-all.sh --build
EOF
else
  cat <<EOF
接下來輪到你（頁面用 Edit 改內容區，別整檔重寫）：
  1. content/$TOPIC/$ID/lesson.py    — 課程內容（emoji 章節錨點、圖當 cell 最後運算式、圖內文字英文）
  2. content/$TOPIC/$ID/index.html   — hero／各 section／練習卡／endnav／data-ready-figures／語義色
  3. content/$TOPIC/$ID/smoke-test.mjs — MIN_FIGURES 改成實際圖數
  4. wiring — 主題頁課卡、首頁主題卡課數、前一課的「下一課」連結
EOF
fi
