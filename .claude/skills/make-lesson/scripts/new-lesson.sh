#!/usr/bin/env bash
# 建課 scaffold：把模板複製與機械代換一次做完，讓創作只剩「lesson.py 內容」與「page 內容區」。
#
# 用法（repo 根目錄執行）：
#   bash .claude/skills/make-lesson/scripts/new-lesson.sh <id> "<課名>" <topic-slug> "<主題名>" [--gpu]
# 例：
#   bash .claude/skills/make-lesson/scripts/new-lesson.sh clustering "分群：沒有答案也能找出結構" ml-basics "學基礎機器學習"
#
#   <id>          課程英文 slug（= lessons/<id>/ 與網址 /<id>/）
#   <課名>        進 page <title>/h1、lesson.py app_title/h1、smoke-test H1_TEXT
#   <topic-slug>  主題 slug（主題頁不存在時只提醒、不代建——新主題照 site.md 手動起）
#   <主題名>      進 header 主題連結與課末「回主題」文字
#   --gpu         雙軌課：保留 page 的 [GPU] 區塊並建 <id>_gpu.py；預設純瀏覽器課（剝除全部 [GPU] 區塊）
#
# 做完的事：四件套複製＋代換、GPU 區塊處理、build.sh 加該課、uv sync。
# 不做的事（留給你創作/接線）：lesson.py 內容、page 內容區、主題頁課卡、首頁課數、前一課的「下一課」。
set -euo pipefail

if [ $# -lt 4 ]; then
  grep '^#' "$0" | head -16; exit 1
fi

ID="$1"; TITLE="$2"; TOPIC="$3"; TOPIC_NAME="$4"; GPU="${5:-}"
SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
TPL="$SKILL_DIR/assets/templates"
ROOT="$(git -C "$SKILL_DIR" rev-parse --show-toplevel)"
DEST="$ROOT/lessons/$ID"

[ -d "$DEST" ] && { echo "✗ lessons/$ID 已存在，先處理掉再跑" >&2; exit 1; }
[[ "$ID" =~ ^[a-z0-9-]+$ ]] || { echo "✗ id 只能小寫英數與連字號：$ID" >&2; exit 1; }

# molab 網址用的 owner/repo（GPU 課才會出現在頁面上）
OWNER_REPO="$(git -C "$ROOT" remote get-url origin | sed -E 's#\.git$##; s#.*[:/]([^/]+/[^/]+)$#\1#')"

mkdir -p "$DEST/page"

# 1) pyproject（marimo 已釘版，勿改成 >=：版本飄移會害 assets 無法共用）
sed "s/LESSON_ID/$ID/" "$TPL/pyproject.toml" > "$DEST/pyproject.toml"

# 2) lesson.py：代換課名
sed "s/課程標題/$TITLE/g" "$TPL/lesson.py" > "$DEST/lesson.py"

# 3) smoke-test：H1_TEXT 直接填好（MIN_FIGURES 寫完 notebook 後記得改）
sed "s/課程標題/$TITLE/g" "$TPL/smoke-test.mjs" > "$DEST/smoke-test.mjs"

# 4) page：代換 id / 主題 / 課名 / owner-repo；純瀏覽器課剝除 [GPU] 區塊
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
fi > "$DEST/page/index.html"

# 4.5) 生成自檢：剝除邏輯誤傷（如模板 prose 出現字面標記）要在這裡炸，不能默默出貨
for must in "</head>" "<style>" "nb-status" "splitter.js" "READY_FIGURES"; do
  grep -qF "$must" "$DEST/page/index.html" || {
    echo "✗ page 生成不完整（缺 $must）——檢查模板的 GPU 標記配對" >&2; exit 1; }
done

# 5) GPU 軌道 notebook（雙軌課）
if [ "$GPU" = "--gpu" ]; then
  sed "s/課程標題/$TITLE/g" "$TPL/lesson_gpu.py" > "$DEST/${ID}_gpu.py"
fi

# 6) build.sh 加該課（插在最後一個 build_lesson / gpu cp 之後）
BUILD="$ROOT/scripts/build.sh"
n="$(grep -nE '^(build_lesson |cp "\$ROOT/lessons/)' "$BUILD" | tail -1 | cut -d: -f1)"
if [ "$GPU" = "--gpu" ]; then
  sed -i "${n}a build_lesson $ID\ncp \"\$ROOT/lessons/$ID/${ID}_gpu.py\" \"\$DIST/$ID/\"" "$BUILD"
else
  sed -i "${n}a build_lesson $ID" "$BUILD"
fi

# 7) 裝依賴
(cd "$DEST" && uv sync -q)

echo "✓ lessons/$ID 骨架就緒（build.sh 已加課、uv sync 完成）"
[ -d "$ROOT/site/$TOPIC" ] || echo "⚠ site/$TOPIC/ 不存在：新主題請照 site.md 從 topic 模板手動建"
cat <<EOF
接下來輪到你（全部用 Edit 改，別整檔重寫）：
  1. lessons/$ID/lesson.py       — 課程內容（emoji 章節錨點、圖當 cell 最後運算式、圖內文字英文）
  2. lessons/$ID/page/index.html — hero／各 section／練習卡／endnav／READY_FIGURES／語義色
  3. lessons/$ID/smoke-test.mjs  — MIN_FIGURES 改成實際圖數
  4. wiring — 主題頁課卡、首頁主題卡課數、前一課的「下一課」連結
EOF
