#!/usr/bin/env bash
# 建課 scaffold：把模板複製與機械代換一次做完，讓創作只剩「lesson.py 內容」與「頁面內容區」。
#
# 用法（repo 根目錄執行）：
#   bash .claude/skills/make-lesson/scripts/new-lesson.sh <id> "<課名>" <topic-slug> "<主題名>" [--gpu]
# 例：
#   bash .claude/skills/make-lesson/scripts/new-lesson.sh clustering "分群：沒有答案也能找出結構" ml-basics "學基礎機器學習"
#
#   <id>          課程英文 slug（= content/<topic>/<id>/ 目錄名 與 網址 /<id>/，全站唯一）
#   <課名>        進 page <title>/h1、lesson.py app_title/h1、smoke-test H1_TEXT
#   <topic-slug>  主題 slug（主題頁不存在時只提醒、不代建——新主題照 site.md 手動起）
#   <主題名>      進 header 主題連結與課末「回主題」文字
#   --gpu         雙軌課：保留 page 的 [GPU] 區塊並建 <id>_gpu.py；預設純瀏覽器課（剝除全部 [GPU] 區塊）
#
# 做完的事：三件套複製＋代換、GPU 區塊處理、root uv sync。
# 不用做的事：build.sh（自動發現課程）、pyproject（全站共用 repo 根的一份）。
# 留給你創作/接線：lesson.py 內容、頁面內容區、主題頁課卡、首頁課數、前一課的「下一課」。
set -euo pipefail

if [ $# -lt 4 ]; then
  grep '^#' "$0" | head -17; exit 1
fi

ID="$1"; TITLE="$2"; TOPIC="$3"; TOPIC_NAME="$4"; GPU="${5:-}"
SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
TPL="$SKILL_DIR/assets/templates"
ROOT="$(git -C "$SKILL_DIR" rev-parse --show-toplevel)"
DEST="$ROOT/content/$TOPIC/$ID"

[ -d "$DEST" ] && { echo "✗ content/$TOPIC/$ID 已存在，先處理掉再跑" >&2; exit 1; }
[[ "$ID" =~ ^[a-z0-9-]+$ ]] || { echo "✗ id 只能小寫英數與連字號：$ID" >&2; exit 1; }
[[ "$TOPIC" =~ ^[a-z0-9-]+$ ]] || { echo "✗ topic slug 只能小寫英數與連字號：$TOPIC" >&2; exit 1; }
# 課程網址在根層（/<id>/），id 必須全站唯一
if compgen -G "$ROOT/content/*/$ID/lesson.py" > /dev/null; then
  echo "✗ 課程 id 已被其他主題使用：$ID" >&2; exit 1
fi

# molab 網址用的 owner/repo（GPU 課才會出現在頁面上）
OWNER_REPO="$(git -C "$ROOT" remote get-url origin | sed -E 's#\.git$##; s#.*[:/]([^/]+/[^/]+)$#\1#')"

mkdir -p "$DEST"

# 1) lesson.py：代換課名
sed "s/課程標題/$TITLE/g" "$TPL/lesson.py" > "$DEST/lesson.py"

# 2) smoke-test：H1_TEXT 直接填好（MIN_FIGURES 寫完 notebook 後記得改）
sed "s/課程標題/$TITLE/g" "$TPL/smoke-test.mjs" > "$DEST/smoke-test.mjs"

# 3) 教學頁：代換 id / 主題 / 課名 / owner-repo；純瀏覽器課剝除 [GPU] 區塊
#    （awk 處理同一行開閉的標記，sed 的範圍刪除會在這種行上吃掉後面整段）
sed -e "s/LESSON_ID/$ID/g" \
    -e "s/TOPIC_SLUG/$TOPIC/g" \
    -e "s/主題名稱/$TOPIC_NAME/g" \
    -e "s/課程主標題/$TITLE/" \
    -e "s/課程標題/$TITLE/" \
    -e "s#OWNER/REPO#$OWNER_REPO#g" \
    "$TPL/page.html" |
if [ "$GPU" = "--gpu" ]; then
  cat
else
  awk '/\[GPU\]/ && /\[\/GPU\]/ { next }
       /\[GPU\]/  { skip=1; next }
       /\[\/GPU\]/ { skip=0; next }
       !skip'
fi > "$DEST/index.html"

# 3.5) 生成自檢：剝除邏輯誤傷（如模板 prose 出現字面標記）要在這裡炸，不能默默出貨
for must in "</head>" "lesson.css" "lesson.js" "splitter.js" "nb-status" "data-ready-figures"; do
  grep -qF "$must" "$DEST/index.html" || {
    echo "✗ 教學頁生成不完整（缺 $must）——檢查模板的 GPU 標記配對" >&2; exit 1; }
done

# 4) GPU 軌道 notebook（雙軌課）
if [ "$GPU" = "--gpu" ]; then
  sed "s/課程標題/$TITLE/g" "$TPL/lesson_gpu.py" > "$DEST/${ID}_gpu.py"
fi

# 5) 確保全站共用 venv 就緒（pyproject 在 repo 根，全部課同一份）
(cd "$ROOT" && uv sync -q)

echo "✓ content/$TOPIC/$ID 骨架就緒（build.sh 會自動發現本課，不用改）"
[ -f "$ROOT/content/$TOPIC/index.html" ] || echo "⚠ content/$TOPIC/index.html 不存在：新主題請照 site.md 從 topic 模板手動建"
cat <<EOF
接下來輪到你（頁面用 Edit 改內容區，別整檔重寫）：
  1. content/$TOPIC/$ID/lesson.py    — 課程內容（emoji 章節錨點、圖當 cell 最後運算式、圖內文字英文）
  2. content/$TOPIC/$ID/index.html   — hero／各 section／練習卡／endnav／data-ready-figures／語義色
  3. content/$TOPIC/$ID/smoke-test.mjs — MIN_FIGURES 改成實際圖數
  4. wiring — 主題頁課卡、首頁主題卡課數、前一課的「下一課」連結
EOF
