#!/usr/bin/env bash
# 組裝整站 dist/：自動發現兩種課，不需手動維護課程清單。
#   純瀏覽器課：content/<topic>/<id>/lesson.py     → WASM 匯出 + 教學頁
#   外部軌課  ：content/<topic>/<id>/<id>_ext.py   → 教學頁 + notebook 原檔（無 WASM）
# 一課只能一版程式（兩者並存＝錯誤）；<id>_gpu.py 是舊雙軌課的遺留尾綴，僅隨附複製。
# 純瀏覽器課的互動模式由 lesson-mode 檔決定（課程層 > 主題層 > 預設 edit）：
#   edit＝程式碼可見可改；app＝隱藏程式碼只留互動（marimo --mode run）
#
# URL 映射（檔案擺在主題下，但課程網址永遠在根層——分享連結不因搬主題而斷）：
#   content/index.html            → /
#   content/<topic>/index.html    → /<topic>/
#   content/<topic>/<id>/         → /<id>/（教學頁 index.html + notebook .py [+ nb/]）
#   content/shared/               → /shared/（骨架 CSS/JS + 共用 WASM assets）
#
# marimo export 出來的 698 個 assets 每課完全相同（檔名含 content hash），
# 全部抽到 /shared/assets/ 共用：共用前每課 713 檔、共用後每課約 15 檔。
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DIST="$ROOT/dist"

PAGES_FILE_LIMIT=20000     # Pages 免費版單次 deployment 檔案數上限
PAGES_MAX_FILE_MIB=25      # Pages 單檔大小上限

BASE_URL="https://agentclass.pages.dev"   # sitemap / og:url 的正準網址（custom domain class.itsmygo.uk 亦可達）
ANALYTICS_TOKEN="11cad570f5524f4eae0e02816497b0f9"   # Cloudflare Web Analytics beacon token；留空＝不注入
                           # （dashboard → Analytics & Logs → Web Analytics → Add a site 取得；
                           #   token 本來就會公開出現在頁面 HTML，不是秘密）

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

LESSON_IDS=()   # 供 sitemap 使用（兩種課的 id 都收）
TOPIC_SLUGS=()

# ── 外部軌課：唯一一份 notebook 在 molab 執行，這裡只放教學頁與 .py 原檔
#   （放在瀏覽器課迴圈之前，「一課兩版」的防呆才會先攔到、訊息才準確）
for ext_py in "$ROOT"/content/*/*/*_ext.py; do
  [ -e "$ext_py" ] || continue
  dir="$(dirname "$ext_py")"
  id="$(basename "$dir")"
  echo "── external lesson: $id"
  if [ -f "$dir/lesson.py" ]; then
    echo "   ✗ $id 同時有 lesson.py 與 $(basename "$ext_py")——一課只能一版程式（瀏覽器或外部）" >&2
    exit 1
  fi
  if [ "$(basename "$ext_py")" != "${id}_ext.py" ]; then
    echo "   ✗ 外部 notebook 檔名必須是 ${id}_ext.py：$(basename "$ext_py")" >&2
    exit 1
  fi
  if [ -d "$DIST/$id" ]; then
    echo "   ✗ 課程 id 重複：$id（課程網址在根層，id 必須全站唯一）" >&2
    exit 1
  fi
  mkdir -p "$DIST/$id"
  cp "$dir/index.html" "$DIST/$id/index.html"
  cp "$ext_py" "$DIST/$id/"
  LESSON_IDS+=("$id")
done

# ── 純瀏覽器課：自動發現並編譯（全部課共用 repo 根的 uv 專案／venv）
for lesson_py in "$ROOT"/content/*/*/lesson.py; do
  dir="$(dirname "$lesson_py")"
  id="$(basename "$dir")"
  # 互動模式：課程層 lesson-mode > 主題層 lesson-mode > 預設 edit
  #   edit＝程式碼可見可改（程式碼本身就是教材，例如 ml-basics 教 scikit-learn）
  #   app ＝隱藏程式碼與編輯器，只留說明／互動元件／輸出（右欄是教學模擬的課）
  lesson_mode="edit"
  [ -f "$(dirname "$dir")/lesson-mode" ] && lesson_mode="$(tr -d '[:space:]' < "$(dirname "$dir")/lesson-mode")"
  [ -f "$dir/lesson-mode" ] && lesson_mode="$(tr -d '[:space:]' < "$dir/lesson-mode")"
  case "$lesson_mode" in
    edit) export_mode="edit" ;;
    app)  export_mode="run"  ;;
    *) echo "   ✗ $id 的 lesson-mode 只能是 app 或 edit（讀到「$lesson_mode」）" >&2; exit 1 ;;
  esac
  echo "── building lesson: $id [$lesson_mode]"
  if [ -d "$DIST/$id" ]; then
    echo "   ✗ 課程 id 重複：$id（課程網址在根層，id 必須全站唯一）" >&2
    exit 1
  fi
  # app 模式課的教學頁要宣告 data-nb-mode="app"，就緒文案才不會叫學員去改格子
  # （只比對 <body> 標籤本身——模板註解裡也有這個字串，全檔 grep 會誤傷 edit 課）
  if [ "$lesson_mode" = "app" ] && ! grep -q '<body[^>]*data-nb-mode="app"' "$dir/index.html"; then
    echo "   ✗ $id 是 app 模式，但 index.html 的 <body> 缺 data-nb-mode=\"app\"" >&2
    exit 1
  fi
  if [ "$lesson_mode" = "edit" ] && grep -q '<body[^>]*data-nb-mode="app"' "$dir/index.html"; then
    echo "   ✗ $id 的 index.html 宣告 data-nb-mode=\"app\"，但沒有對應的 lesson-mode 檔" >&2
    exit 1
  fi
  mkdir -p "$DIST/$id"
  (cd "$ROOT" && uv run marimo export html-wasm "$lesson_py" -o "$DIST/$id/nb" --mode "$export_mode" -f)
  # marimo 0.23 預設 auto_instantiate=false，且 export 不吃專案設定 → 後處理強制開啟自動執行
  sed -i 's/"auto_instantiate": false/"auto_instantiate": true/' "$DIST/$id/nb/index.html"
  share_assets "$DIST/$id/nb" "$id"
  cp "$dir/index.html" "$DIST/$id/index.html"
  cp "$dir/lesson.py" "$DIST/$id/lesson.py"
  # 舊雙軌課遺留：<id>_gpu.py 一併放上（頁面的下載連結用）；新課不再產生這種檔
  [ -f "$dir/${id}_gpu.py" ] && cp "$dir/${id}_gpu.py" "$DIST/$id/"
  LESSON_IDS+=("$id")
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
  TOPIC_SLUGS+=("$topic")
done

# 根目錄放 404.html 會關掉 Pages 的 SPA fallback（缺檔回 index.html + 200），
# 缺檔改回真 404 —— 否則瀏覽器抓不到的 JS 會拿到 HTML，噴難懂的 module MIME 錯誤
cat > "$DIST/404.html" <<'EOF'
<!doctype html>
<meta charset="utf-8">
<title>404 - AI 互動教室</title>
<p>找不到這個頁面。<a href="/">回首頁</a></p>
EOF

# ── sitemap.xml / robots.txt（搜尋引擎需要知道全站有哪些頁）
today=$(date +%Y-%m-%d)
{
  echo '<?xml version="1.0" encoding="UTF-8"?>'
  echo '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
  echo "  <url><loc>$BASE_URL/</loc><lastmod>$today</lastmod></url>"
  for t in "${TOPIC_SLUGS[@]}"; do
    echo "  <url><loc>$BASE_URL/$t/</loc><lastmod>$today</lastmod></url>"
  done
  for l in "${LESSON_IDS[@]}"; do
    echo "  <url><loc>$BASE_URL/$l/</loc><lastmod>$today</lastmod></url>"
  done
  echo '</urlset>'
} > "$DIST/sitemap.xml"
cat > "$DIST/robots.txt" <<EOF
User-agent: *
Allow: /
Sitemap: $BASE_URL/sitemap.xml
EOF

# ── Cloudflare Web Analytics（免 cookie）：token 有填才注入。
#    只注入「頁面」（首頁／主題頁／課程頁），不注入 nb/ 的 notebook iframe——
#    每次開課 iframe 都會載入，注入會重複計數。
if [ -n "$ANALYTICS_TOKEN" ]; then
  beacon="<script type=\"module\" src=\"https://static.cloudflareinsights.com/beacon.min.js\" data-cf-beacon='{\"token\": \"$ANALYTICS_TOKEN\"}'></script>"
  for page in "$DIST/index.html" "$DIST"/*/index.html; do
    sed -i "s|</body>|$beacon\n</body>|" "$page"
  done
  echo "   analytics beacon 已注入全部頁面"
fi

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
