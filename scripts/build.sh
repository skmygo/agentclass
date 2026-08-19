#!/usr/bin/env bash
# 組裝整站 dist/：自動發現 content/<topic>/<lesson>/lesson.py，不需手動維護課程清單。
#
# URL 映射（檔案擺在主題下，但課程網址永遠在根層——分享連結不因搬主題而斷）：
#   content/index.html            → /
#   content/<topic>/index.html    → /<topic>/
#   content/<topic>/<id>/         → /<id>/（教學頁 index.html + lesson.py + nb/）
#   content/shared/               → /shared/（骨架 CSS/JS + 共用 WASM assets）
#
# marimo export 出來的 698 個 assets 每課完全相同（檔名含 content hash），
# 全部抽到 /shared/assets/ 共用：共用前每課 713 檔、共用後每課約 15 檔。
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DIST="$ROOT/dist"

PAGES_FILE_LIMIT=20000     # Pages 免費版單次 deployment 檔案數上限
PAGES_MAX_FILE_MIB=25      # Pages 單檔大小上限

rm -rf "$DIST"
mkdir -p "$DIST"

# 把該課的 nb/assets 併進 /shared/assets/，並改寫 index.html 的引用路徑。
# assets 內部全是 ./ 相對路徑，整包搬走後仍在同一層，所以只有 index.html 需要改。
share_assets() {
  local nb="$1" id="$2"
  local shared="$DIST/shared/assets"

  if [ ! -d "$shared" ]; then
    mkdir -p "$DIST/shared"
    mv "$nb/assets" "$shared"
  elif diff -q <(ls "$nb/assets" | sort) <(ls "$shared" | sort) >/dev/null 2>&1; then
    rm -rf "$nb/assets"
  else
    # marimo 版本或依賴不同會導致 hash 不同，此時共用會直接壞掉 → 這課退回獨立 assets
    echo "   ⚠️  assets 與共用版本不一致（marimo 版本不同？）→ $id 保留獨立 assets，未共用"
    return 0
  fi

  sed -i 's|"\./assets/|"/shared/assets/|g' "$nb/index.html"
  if grep -q '"\./assets/' "$nb/index.html"; then
    echo "   ✗ $id 的 index.html 仍有未改寫的 ./assets/ 引用" >&2
    exit 1
  fi
}

# ── 自動發現並編譯每一課（全部課共用 repo 根的 uv 專案／venv）
for lesson_py in "$ROOT"/content/*/*/lesson.py; do
  dir="$(dirname "$lesson_py")"
  id="$(basename "$dir")"
  echo "── building lesson: $id"
  if [ -d "$DIST/$id" ]; then
    echo "   ✗ 課程 id 重複：$id（課程網址在根層，id 必須全站唯一）" >&2
    exit 1
  fi
  mkdir -p "$DIST/$id"
  (cd "$ROOT" && uv run marimo export html-wasm "$lesson_py" -o "$DIST/$id/nb" --mode edit -f)
  # marimo 0.23 預設 auto_instantiate=false，且 export 不吃專案設定 → 後處理強制開啟自動執行
  sed -i 's/"auto_instantiate": false/"auto_instantiate": true/' "$DIST/$id/nb/index.html"
  share_assets "$DIST/$id/nb" "$id"
  cp "$dir/index.html" "$DIST/$id/index.html"
  cp "$dir/lesson.py" "$DIST/$id/lesson.py"
  # 雙軌課：GPU notebook 一併放上（頁面的「下載 <id>_gpu.py」連結用）
  [ -f "$dir/${id}_gpu.py" ] && cp "$dir/${id}_gpu.py" "$DIST/$id/"
done

# ── 首頁、主題頁、shared/（骨架 CSS/JS 併進已含 WASM assets 的 /shared/）
cp "$ROOT/content/index.html" "$DIST/index.html"
mkdir -p "$DIST/shared"
cp -r "$ROOT/content/shared/." "$DIST/shared/"
for topic_index in "$ROOT"/content/*/index.html; do
  topic="$(basename "$(dirname "$topic_index")")"
  [ "$topic" = "shared" ] && continue
  mkdir -p "$DIST/$topic"
  cp "$topic_index" "$DIST/$topic/index.html"
done

# 根目錄放 404.html 會關掉 Pages 的 SPA fallback（缺檔回 index.html + 200），
# 缺檔改回真 404 —— 否則瀏覽器抓不到的 JS 會拿到 HTML，噴難懂的 module MIME 錯誤
cat > "$DIST/404.html" <<'EOF'
<!doctype html>
<meta charset="utf-8">
<title>404 - AI 互動教室</title>
<p>找不到這個頁面。<a href="/">回首頁</a></p>
EOF

# ── 部署前檢核：撞到 Pages 上限的話，先在這裡失敗比部署到一半失敗好 debug
files=$(find "$DIST" -type f | wc -l)
oversized=$(find "$DIST" -type f -size +${PAGES_MAX_FILE_MIB}M)

echo
echo "── dist ready: $DIST"
echo "   大小：$(du -sh "$DIST" | cut -f1)"
echo "   檔案數：$files / $PAGES_FILE_LIMIT（Pages 免費版上限）"

if [ -n "$oversized" ]; then
  echo "   ✗ 有超過 ${PAGES_MAX_FILE_MIB}MiB 的檔案，Pages 會拒絕：" >&2
  echo "$oversized" >&2
  exit 1
fi

if [ "$files" -gt "$PAGES_FILE_LIMIT" ]; then
  echo "   ✗ 檔案數超過 Pages 上限" >&2
  exit 1
fi
