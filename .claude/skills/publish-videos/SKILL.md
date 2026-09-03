---
name: publish-videos
description: 把 video/data/ 裡的課程錄影（.mp4）全部上傳到「一輩子只跟AI學」YouTube 頻道、嵌進對應課程頁教學欄的開頭、build 與冒煙後 commit／部署／push，一次做完。只要使用者提到上傳影片、發佈錄影、mp4 放好了、把影片接到課程、重錄某課的影片、更新或替換課程影片、影片怎麼上線，就用這個 skill，即使他沒說出 skill 名稱、即使只想做其中一段（只上傳、只嵌入、只部署、補播放清單）。
---

# publish-videos：影片放好 → 跑一次 → 全部上線

三支腳本接力：`plan.py`（對課程、產 metadata、前置檢查）→ `publish.py`（上傳、寫 `VIDEO`、page-fill）
→ `ship.sh`（build、冒煙、commit、deploy、push、線上驗證）。你負責跑它們、替每支影片想 tags、
把計畫給使用者確認一次、解讀失敗、最後回報。**格式由程式與 `video/config.json` 決定，不由對話決定**——
這是使用者要求「之後每次格式都一樣」的保證，所以不要手寫標題／說明、不要手改 index.html。

`page_content.py` 裡的 `VIDEO` 常數是唯一真相：有它＝已上傳＋已嵌入。因此 `video/data/` 每次清空重放
都沒關係、中途失敗直接從第 1 步重跑（完成的課自動跳過）、重錄才需要 `--replace`。

## 流程

所有指令在 repo 根執行。

**1. 建計畫＋前置檢查**

```bash
python3 .claude/skills/publish-videos/scripts/plan.py            # 重錄某課：加 --replace <課程id>
```

檔名規則 `NN-<課程id>.mp4`（`01litellm-basics.mp4` 這種也行）；去掉前置數字後必須等於
`content/<topic>/<id>/` 的目錄名。plan.py 會一次驗完：檔名對得到課、課有 `page_content.py`、
標題與說明合 YouTube 限制、git 工作樹乾淨、YouTube token 可用（不開瀏覽器）。**任何一項不過就停在
還沒上傳的狀態**，把錯誤照實轉告使用者並停下——不要自己猜檔名該對哪一課、不要幫忙 stash 別人的改動。
exit 0 才往下。

**2. 替每支「上傳／重傳」的影片想 tags**

讀該課 `page_content.py` 的 TITLE／DESCRIPTION（計畫表已印出），寫 3–8 個：

- 具體技術名詞優先（FastMCP、MCP、Qdrant、RAG、Tool Calling、LoRA…），中英皆可、每個 ≤30 字
- 不要泛詞（教學、AI、程式）、不要跟固定 tags 重複——固定的（「AI 互動教室」＋主題 tags）程式會補上
- 不含逗號與 `<>`

```bash
python3 .claude/skills/publish-videos/scripts/plan.py tags <課程id> "FastMCP" "MCP" "OAuth 2.1" "Token 驗證"
```

若 `page_content.py` 有 `VIDEO_TAGS = [...]`，plan 會直接採用，不用再填。

**3. 印完整計畫，請使用者確認一次**

```bash
python3 .claude/skills/publish-videos/scripts/plan.py show      # exit 0 才算計畫完整
```

把表（檔名 → 課程、標題、tags、隱私、要上傳幾支／跳過幾支）原樣給使用者看，問一句「照這樣上傳？」。
上傳會佔 YouTube 配額、產生真的影片，所以要這一道；使用者回 yes 之後**全程不再問**。
使用者要改標題／說明格式 → 改 `video/config.json` 的模板再從第 1 步重跑，不要只改這一次。

**4. 上傳＋嵌入**

```bash
python3 .claude/skills/publish-videos/scripts/publish.py
```

逐支：上傳（private，設定檔決定）→ 加進該主題的播放清單（沒有就建、照課程順序插入）→
`VIDEO` 寫進 `page_content.py` → 重跑 page-fill。中途失敗會印已完成幾支；修好後從第 1 步重跑即可。

**5. build、冒煙、commit、deploy、push**

```bash
COMMIT_TRAILER=$'Co-Authored-By: Claude <noreply@anthropic.com>\nClaude-Session: <本 session 的網址>' \
  bash .claude/skills/publish-videos/scripts/ship.sh
```

只冒煙受影響的課（桌機＋手機），因為這條線不碰 `shared/`。冒煙失敗會停在未 commit：讀失敗輸出、
修 `page_content.py`（不是 index.html）、重跑 page-fill 與 ship.sh。deploy 後會 curl 正式網域確認每課
有新的 iframe；看不到多半是邊緣快取，過幾秒再 curl 一次即可。

**6. 回報**

```
上傳 N 支（跳過 M 支已有影片）：
- <課程id> → https://youtu.be/<id> → https://class.itsmygo.uk/<id>/
播放清單：https://www.youtube.com/playlist?list=<id>
commit <hash>，已部署並 push。影片目前 private，公開請到 YouTube Studio 設定（或改 config 的 privacy）。
```

## 常見失敗與處理

| 現象 | 原因 | 做法 |
|---|---|---|
| plan：`YouTube 授權不可用` | token 七天到期（OAuth 同意畫面停在測試）或被撤銷 | `uv run video/upload.py --login`（沒桌面加 `--no-browser`，README 有 ssh -L 說明）；登入要選 kuan9924501@gmail.com 的頻道。完成後從第 1 步重跑 |
| plan：`不是任何課程目錄名` | 檔名打錯或課還沒建 | 請使用者改檔名；不要猜 |
| plan：`沒有 page_content.py` | ml-basics 三堂舊式手寫頁 | 告知需先遷成 page_content.py（make-lesson skill），這次跳過 |
| plan：git 工作樹有改動 | 別的工作沒 commit | 請使用者處理，不要代為 stash／commit |
| publish：HTTP 403 quota | videos.insert 每日 100 次 | 隔天（太平洋時間午夜後）重跑第 1 步 |
| publish：HTTP 401/403 其他 | 帳號／頻道不符 | `uv run video/upload.py --check-auth` 看登入頻道 |
| ship：冒煙 ✗ | 該課頁面壞了 | 看輸出；通常是 page_content.py 問題，不是影片 |
| ship：線上驗證 ✗ | CDN 快取 | 等幾秒再 `curl https://class.itsmygo.uk/<id>/ \| grep embed` |

## 特殊情況

- **重錄替換**：`plan.py --replace <id>`。新影片上傳、`VIDEO` 換成新網址，舊影片留在 YouTube（回報時提醒使用者自行刪除或設私人）。
- **只補播放清單**（例如早期上傳未入清單）：`uv run video/upload.py --add-existing <video_id> --playlist-title "<主題名>｜AI 互動教室" --playlist-order <該主題影片 id 課程順序，逗號分隔>`。
- **清單順序亂了**（連續加入時 YouTube 查詢有幾秒延遲，位置可能算錯；publish.py 每批結尾已自動整理）：`uv run video/upload.py --playlist-sort --playlist-id <PL…> --playlist-order <課程順序的影片 id>`。
- **要改成公開**：審核通過後把 `video/config.json` 的 `privacy` 改 `public`；已上傳的到 Studio 改。
- **測試管線不想真的上傳**：只能在另一個 worktree／副本裡做 `plan.py --dry-run` → tags → `publish.py` → `ship.sh`（dry-run 會用假 id 寫進 page_content.py，且 ship 只做到 build＋冒煙）。真實 repo 不要 dry-run。

## 不要做的事

- 不手寫標題／說明、不直接編輯 index.html、不 commit mp4（已 gitignore）。
- 不把影片設 public／unlisted 繞過設定檔——未審核的 API 專案上傳的影片會被 YouTube 鎖成私人，設了也沒用。
- 使用者沒確認計畫前不跑 publish.py；沒跑過冒煙不 deploy。

格式細節（檔名、模板欄位、tags 規則、設定檔每個鍵）見 `references/format.md`；底層上傳工具見 `video/README.md`。
