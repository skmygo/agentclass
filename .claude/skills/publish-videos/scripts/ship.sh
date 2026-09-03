#!/usr/bin/env bash
# publish-videos 第 3 步：build → 只冒煙受影響的課 → commit → deploy → push → 線上驗證。
#
# 用法（repo 根執行，先跑 publish.py）：
#   bash .claude/skills/publish-videos/scripts/ship.sh              # 全套
#   bash .claude/skills/publish-videos/scripts/ship.sh --no-deploy  # 只 build＋冒煙＋commit
#   COMMIT_TRAILER=$'Co-Authored-By: ...\nClaude-Session: ...' bash ship.sh   # commit 訊息尾巴
#
# 為什麼只冒煙受影響的課：這條線只改 page_content.py／index.html 與 video/ 的設定，不碰 shared/，
# 其他課的輸出位元組不變；全站冒煙（含 WASM 課）要十分鐘，留給改共用檔的時候。
# dry-run 的結果（假 id）絕不 commit，build＋冒煙後就停。
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../../../.." && pwd)"
cd "$ROOT"
DEPLOY=1
for a in "$@"; do case "$a" in --no-deploy) DEPLOY=0;; *) echo "不認識的參數：$a" >&2; exit 1;; esac; done

RESULT=video/.publish-result.json
[ -f "$RESULT" ] || { echo "✗ 沒有 $RESULT，先跑 publish.py" >&2; exit 1; }
read -r DRY IDS FILES SUMMARY < <(python3 - <<'PY'
import json
r = json.load(open("video/.publish-result.json"))
items = r["items"]
ids = ",".join(i["lesson_id"] for i in items)
files = " ".join(f'{i["page_content"]} {i["index_html"]}' for i in items)
topics = sorted({i["topic"] for i in items})
summary = f"{'+'.join(topics)} {len(items)} 支"
print("1" if r["dry_run"] else "0", ids or "-", files or "-", summary.replace(" ", "_"))
PY
)
[ "$IDS" = "-" ] && { echo "沒有要出貨的課程。"; exit 0; }
echo "── 受影響課程：$IDS"

echo "── build ＋ 冒煙（只跑受影響的課，桌機＋手機）"
bash .claude/skills/make-lesson/scripts/smoke-all.sh --build --only "$IDS"

if [ "$DRY" = "1" ]; then
  echo "── dry-run：build 與冒煙通過。不 commit、不部署（page_content.py 裡是假 id）。"
  exit 0
fi

echo "── commit"
# shellcheck disable=SC2086
git add $FILES video/config.json video/uploaded.jsonl
MSG="$(python3 - <<'PY'
import json, os
r = json.load(open("video/.publish-result.json"))
items = r["items"]
topics = sorted({i["topic"] for i in items})
head = f"課程影片：{'、'.join(topics)} 上傳 {len(items)} 支並嵌入課程頁（{', '.join(i['lesson_id'] for i in items)}）"
body = "\n".join(f"- {i['lesson_id']}: {i['url']}" + ("（重傳，取代舊影片）" if i["status"] == "replace" else "") for i in items)
trailer = os.environ.get("COMMIT_TRAILER", "").strip()
print(head + "\n\n" + body + ("\n\n" + trailer if trailer else ""))
PY
)"
git commit -q -F - <<< "$MSG"
echo "✓ $(git log --oneline -1)"

[ "$DEPLOY" = "1" ] || { echo "── --no-deploy：到 commit 為止。"; exit 0; }

PROJECT="$(python3 -c 'import json;print(json.load(open("video/config.json"))["pages_project"])')"
SITE="$(python3 -c 'import json;print(json.load(open("video/config.json"))["site_url"].rstrip("/"))')"
echo "── deploy（Cloudflare Pages project $PROJECT）"
npx wrangler pages deploy dist --project-name="$PROJECT" 2>&1 | grep -E 'Success|Deployment complete|Error|error' || true
echo "── git push"
git push

echo "── 線上驗證（$SITE）"
fail=0
python3 -c 'import json;[print(i["lesson_id"], i["video_id"]) for i in json.load(open("video/.publish-result.json"))["items"]]' | while read -r lid vid; do
  ok=0
  for _ in 1 2 3 4 5 6; do
    if curl -sS -m 20 -H 'Cache-Control: no-cache' "$SITE/$lid/?v=$RANDOM" | grep -q "youtube-nocookie.com/embed/$vid"; then ok=1; break; fi
    sleep 5
  done
  if [ $ok = 1 ]; then echo "✓ $SITE/$lid/ 有 $vid"; else echo "✗ $SITE/$lid/ 還看不到 $vid（快取？稍後再 curl 一次）"; fi
done
echo "── 完成"
