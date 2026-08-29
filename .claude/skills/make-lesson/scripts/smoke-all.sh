#!/usr/bin/env bash
# 全站冒煙一鍵版：起 dist server → 自動發現每一課的 smoke-test.mjs 並用正確的 URL 跑 → 收 server。
#
# 用法（任何 cwd 都行）：
#   bash .claude/skills/make-lesson/scripts/smoke-all.sh            # 跑全部（dist 要先 build）
#   bash .claude/skills/make-lesson/scripts/smoke-all.sh --build    # 先 scripts/build.sh 再跑
#   bash .claude/skills/make-lesson/scripts/smoke-all.sh --base https://agentclass.pages.dev   # 打線上（部署後）
#
# URL 規則：純瀏覽器課 /<id>/nb/index.html、外部軌課 /<id>/（外部課沒有 nb/）。
# 線上冒煙第一次失敗多半是 CDN 冷資產——會自動重試一次。
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/../../../.." && pwd)"
PORT=8787; BASE=""; BUILD=0
while [ $# -gt 0 ]; do
  case "$1" in
    --build) BUILD=1;;
    --base) BASE="$2"; shift;;
    *) echo "不認識的參數：$1" >&2; exit 1;;
  esac; shift
done
[ $BUILD -eq 1 ] && (cd "$ROOT" && bash scripts/build.sh | tail -3)

server_pid=""
if [ -z "$BASE" ]; then
  [ -d "$ROOT/dist" ] || { echo "✗ 沒有 dist/，先 --build" >&2; exit 1; }
  python3 -m http.server "$PORT" -d "$ROOT/dist" >/dev/null 2>&1 &
  server_pid=$!
  for _ in $(seq 1 30); do curl -s -o /dev/null "http://127.0.0.1:$PORT/" && break; sleep 0.2; done
  BASE="http://127.0.0.1:$PORT"
fi
trap '[ -n "$server_pid" ] && kill "$server_pid" 2>/dev/null' EXIT

pass=0; fail=0; failed=()
mobile_specs=()
for smoke in "$ROOT"/content/*/*/smoke-test.mjs; do
  dir="$(dirname "$smoke")"; id="$(basename "$dir")"
  if [ -f "$dir/lesson.py" ]; then
    url="$BASE/$id/nb/index.html"
    mode="edit"
    if [ -f "$dir/lesson-mode" ]; then mode="$(cat "$dir/lesson-mode")"
    elif [ -f "$(dirname "$dir")/lesson-mode" ]; then mode="$(cat "$(dirname "$dir")/lesson-mode")"; fi
    [ "$mode" = "app" ] && mobile_specs+=("${id}:app") || mobile_specs+=("${id}:edit")
  else
    url="$BASE/$id/"
    mobile_specs+=("${id}:ext")
  fi
  result="$(cd "$ROOT" && node "$smoke" "$url" 2>&1 | tail -1)"
  if [ "$result" != "RESULT: PASS" ]; then
    result="$(cd "$ROOT" && node "$smoke" "$url" 2>&1 | tail -1)"   # 線上 CDN 冷資產／首載慢：重試一次
  fi
  if [ "$result" = "RESULT: PASS" ]; then pass=$((pass+1)); echo "✓ $id"; else fail=$((fail+1)); failed+=("$id"); echo "✗ $id — $result"; fi
done
echo "── smoke: $pass pass / $fail fail${failed:+（${failed[*]}）}"

# 手機 viewport（390×844）：全課結構檢查 + app/edit 各一堂抽樣全載（見 mobile-smoke.mjs）
mfail=0
(cd "$ROOT" && node .claude/skills/make-lesson/scripts/mobile-smoke.mjs "$BASE" "${mobile_specs[@]}") || mfail=1
[ $fail -eq 0 ] && [ $mfail -eq 0 ]
