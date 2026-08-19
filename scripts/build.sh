#!/usr/bin/env bash
# 組裝整站 dist/：每課 = /<lesson>/（教學頁）+ /<lesson>/nb/（marimo WASM）+ /<lesson>/lesson.py
#
# marimo export 出來的 698 個 assets 每課完全相同（檔名含 content hash），
# 全部抽到 /shared/assets/ 共用：
#   共用前 每課 713 檔 → Cloudflare Pages 免費版 20,000 檔上限約 28 課就撞牆
#   共用後 首課 713 檔，之後每課約 15 檔 → 上千課才撞牆，順便省掉每課 27MB 重複上傳
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DIST="$ROOT/dist"

PAGES_FILE_LIMIT=20000     # Pages 免費版單次 deployment 檔案數上限
PAGES_MAX_FILE_MIB=25      # Pages 單檔大小上限

rm -rf "$DIST"
mkdir -p "$DIST"

# 把該課的 nb/assets 併進 /shared/assets/，並改寫 index.html 的引用路徑。
# assets 內部（JS chunk 互相 import、CSS 的 url()、wasm 載入）全是 ./ 相對路徑，
# 整包搬走後仍在同一層，所以只有 index.html 需要改。
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

build_lesson() {
  local id="$1"
  local src="$ROOT/lessons/$id"
  echo "── building lesson: $id"
  mkdir -p "$DIST/$id"
  (cd "$src" && uv run marimo export html-wasm lesson.py -o "$DIST/$id/nb" --mode edit -f)
  # marimo 0.23 預設 auto_instantiate=false，且 export 不吃專案設定 → 後處理強制開啟自動執行
  sed -i 's/"auto_instantiate": false/"auto_instantiate": true/' "$DIST/$id/nb/index.html"
  share_assets "$DIST/$id/nb" "$id"
  cp "$src/page/index.html" "$DIST/$id/index.html"
  cp "$src/lesson.py" "$DIST/$id/lesson.py"
}

build_lesson decision-tree
build_lesson classification
build_lesson regression
build_lesson clustering
build_lesson fastmcp

# site/ 整包併入：首頁（主題列表）、主題頁、shared/ 共用前端資源
cp -r "$ROOT/site/." "$DIST/"

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
