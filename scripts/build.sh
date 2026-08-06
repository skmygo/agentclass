#!/usr/bin/env bash
# 組裝整站 dist/：每課 = /<lesson>/（教學頁）+ /<lesson>/nb/（marimo WASM）+ /<lesson>/lesson.py
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DIST="$ROOT/dist"

rm -rf "$DIST"
mkdir -p "$DIST"

build_lesson() {
  local id="$1"
  local src="$ROOT/lessons/$id"
  echo "── building lesson: $id"
  mkdir -p "$DIST/$id"
  (cd "$src" && uv run marimo export html-wasm lesson.py -o "$DIST/$id/nb" --mode edit -f)
  # marimo 0.23 預設 auto_instantiate=false，且 export 不吃專案設定 → 後處理強制開啟自動執行
  sed -i 's/"auto_instantiate": false/"auto_instantiate": true/' "$DIST/$id/nb/index.html"
  cp "$src/page/index.html" "$DIST/$id/index.html"
  cp "$src/lesson.py" "$DIST/$id/lesson.py"
}

build_lesson decision-tree
build_lesson sft
# sft 課附 GPU notebook 原始檔（下載入口）
cp "$ROOT/lessons/sft/sft_gpu.py" "$DIST/sft/sft_gpu.py"

cp "$ROOT/site/index.html" "$DIST/index.html"

echo "── dist ready: $DIST"
du -sh "$DIST"
