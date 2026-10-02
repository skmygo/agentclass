---
name: publish-videos
description: 把 video/ 裡的課程錄影（.mp4）全部上傳到「一輩子只跟AI學」YouTube 頻道（公開）、嵌進對應課程頁教學欄的開頭、build 與冒煙後 commit／部署／push，一次做完。只要使用者提到上傳影片、發佈錄影、mp4 放好了、把影片接到課程、重錄某課的影片、更新或替換課程影片、影片怎麼上線，就用這個 skill，即使他沒說出 skill 名稱、即使只想做其中一段（只上傳、只嵌入、只部署、補播放清單）。
---

# publish-videos：影片放好 → 跑一次 → 全部上線

三支腳本接力：`plan.py`（對課程、產 metadata、前置檢查）→ `publish.py`（上傳、寫 `VIDEO`、page-fill、讀回隱私）
→ `ship.sh`（build、冒煙、commit、deploy、push、線上驗證）。你負責跑它們、替每支影片想 tags、
把計畫給使用者看、解讀失敗、最後回報。**格式由程式與本 skill 的 `config.json` 決定，不由對話決定**——
這是使用者要求「之後每次格式都一樣」的保證，所以不要手寫標題／說明、不要手改 index.html。

`page_content.py` 裡的 `VIDEO` 常數是唯一真相：有它＝已上傳＋已嵌入。因此 `video/` 每次清空重放
都沒關係（設定在 skill 目錄，不在 `video/`）、中途失敗直接從第 1 步重跑（完成的課自動跳過）、重錄才需要 `--replace`。

上傳核心是 **youtube-upload plugin 的 `upload.py`**（repo 裡不再放一份）：憑證跟著 plugin，在
`~/.config/youtube-upload/`，裝好 plugin 就能用，不必設任何環境變數、不必把金鑰複製進 repo。
路徑用 `python3 .claude/skills/publish-videos/scripts/plan.py uploader` 查（下面記作 `$UP`）；
plugin 不在預設位置時用 `YT_UPLOAD=<upload.py 路徑>` 指定。

## 流程

所有指令在 repo 根執行。

**1. 建計畫＋前置檢查**

```bash
python3 .claude/skills/publish-videos/scripts/plan.py --topic <主題>    # 重錄某課：加 --replace <課程id>
```

影片放 `video/`（`video/data/` 也會掃）。檔名去掉前綴（`NN-`、`NN`、`LNN-`）後：

- 等於課程目錄名 → 那一課（`08-genai-rag.mp4` → `genai-rag`）；
- 否則當**簡稱**：剛好只有一課的 id 以 `-<簡稱>` 結尾 → 那一課（`L00-why.mp4` → `mlops-why`、`L01-tracking.mp4` → `mlflow-tracking`）。

`--topic <主題目錄名>` 讓對課只在那個主題裡找——使用者說了是哪個主題的影片就加上，簡稱才不會撞到別的主題；
沒說就省略（全站找，撞名會停）。plan.py 會一次驗完：檔名對得到課、課有 `page_content.py`、
標題與說明合 YouTube 限制、git 工作樹乾淨、YouTube token 可用（不開瀏覽器）。**任何一項不過就停在
還沒上傳的狀態**，把錯誤照實轉告使用者並停下——對課規則是確定性的，對不到就是對不到：
不要自己猜檔名該對哪一課、不要幫忙改檔名、不要幫忙 stash 別人的改動。exit 0 才往下。

**2. 替每支「上傳／重傳」的影片想 tags**

讀該課 `page_content.py` 的 TITLE／DESCRIPTION（計畫表已印出標題；說明全文用
`python3 -c "import runpy;print(runpy.run_path('content/<topic>/<id>/page_content.py')['DESCRIPTION'])"`），寫 3–8 個：

- 具體技術名詞優先（FastMCP、MCP、Qdrant、RAG、Tool Calling、LoRA…），中英皆可、每個 ≤30 字
- 不要泛詞（教學、AI、程式）、不要跟固定 tags 重複——固定的（「AI 互動教室」＋主題 tags）程式會補上
- 不含逗號與 `<>`

```bash
python3 .claude/skills/publish-videos/scripts/plan.py tags <課程id> "FastMCP" "MCP" "OAuth 2.1" "Token 驗證"
```

若 `page_content.py` 有 `VIDEO_TAGS = [...]`，plan 會直接採用，不用再填。
新主題第一次發影片時，順手在 `config.json` 的 `topic_tags` 加上該主題的 1–2 個固定 tags（加完要 commit 再重跑第 1 步）。

**3. 印完整計畫給使用者看**

```bash
python3 .claude/skills/publish-videos/scripts/plan.py show      # exit 0 才算計畫完整
```

把表（檔名 → 課程、標題、tags、隱私、要上傳幾支／跳過幾支）原樣給使用者看。標了「（簡稱對應）」的列
是靠檔名結尾對到課的，特別值得看一眼對不對。

- 使用者**已經明說**直接跑／自動上傳／不用確認 → 貼出表就繼續，不要再問。
- 否則問一句「照這樣上傳？」，回 yes 之後**全程不再問**。上傳是公開的、會佔 YouTube 配額，所以預設要這一道。

使用者要改標題／說明格式 → 改 `config.json` 的模板再從第 1 步重跑，不要只改這一次。

**4. 上傳＋嵌入**

```bash
python3 .claude/skills/publish-videos/scripts/publish.py
```

逐支：上傳（隱私由 `config.json` 的 `privacy` 決定，目前 **public**）→ 加進該主題的播放清單（沒有就建、照課程順序插入）→
`VIDEO` 寫進 `page_content.py` → 重跑 page-fill；整批結束後整理清單順序、讀回每支在 YouTube 上的實際隱私。
中途失敗會印已完成幾支；修好後從第 1 步重跑即可。放背景跑時別接 `| tail`（輸出會等到結束才出來）。

**5. build、冒煙、commit、deploy、push**

```bash
COMMIT_TRAILER=$'Co-Authored-By: Claude <noreply@anthropic.com>\nClaude-Session: <本 session 的網址>' \
  bash .claude/skills/publish-videos/scripts/ship.sh
```

只冒煙受影響的課（桌機＋手機），因為這條線不碰 `shared/`。冒煙失敗會停在未 commit：讀失敗輸出、
修 `page_content.py`（不是 index.html）、重跑 page-fill 與 ship.sh。deploy 後會 curl 正式網域確認每課
有新的 iframe；看不到多半是邊緣快取，過幾秒再 curl 一次即可。沒登入 wrangler 的機器要先設
`CLOUDFLARE_API_TOKEN`／`CLOUDFLARE_ACCOUNT_ID`。

**6. 回報**

```
上傳 N 支（跳過 M 支已有影片）：
- <課程id> → https://youtu.be/<id> → https://class.itsmygo.uk/<id>/
播放清單：https://www.youtube.com/playlist?list=<id>
commit <hash>，已部署並 push。影片隱私＝config 的 `privacy`（目前 public），並已讀回 YouTube 確認。
```

## 常見失敗與處理

| 現象 | 原因 | 做法 |
|---|---|---|
| plan：`找不到 youtube-upload plugin 的 upload.py` | 這台沒裝 plugin | 裝 sk-work-plugins 的 youtube-upload plugin，或 `YT_UPLOAD=<路徑>` |
| plan：`YouTube 授權不可用` | token 被撤銷／失效（exit 3），或只是網路／SSL 暫時錯誤（exit 1） | 先 `uv run "$UP" --check-auth` 看是哪種：網路問題重跑就好；exit 3 才 `uv run "$UP" --login`（沒桌面加 `--no-browser`，照 youtube-upload skill 的 ssh -L 說明），登入要選「一輩子只跟AI學」頻道。完成後從第 1 步重跑 |
| plan：`不是任何課程目錄名，也不是哪一課 id 的結尾` | 檔名打錯或課還沒建 | 請使用者改檔名；不要猜 |
| plan：`簡稱 … 對到不只一課` | 簡稱在多個課／主題重複 | 加 `--topic`；同主題內還撞就請使用者把檔名改成完整課程 id |
| plan：`沒有 page_content.py` | 課程頁是舊式手寫頁（目前全站已無） | 告知需先遷成 page_content.py（make-lesson skill），這次跳過 |
| plan：git 工作樹有改動 | 別的工作沒 commit | 請使用者處理，不要代為 stash／commit |
| publish：HTTP 403 quota | videos.insert 每日 100 次 | 隔天（太平洋時間午夜後）重跑第 1 步 |
| publish：HTTP 401/403 其他 | 帳號／頻道不符 | `uv run "$UP" --check-auth` 看登入頻道 |
| publish：`⚠ 讀回有異常` | YouTube 把隱私改掉（API 審核出問題）或影片處理失敗 | 照實回報；`uv run "$UP" --status <id,…>` 再讀一次 |
| ship：冒煙 ✗ | 該課頁面壞了 | 看輸出；通常是 page_content.py 問題，不是影片 |
| ship：線上驗證 ✗ | CDN 快取 | 等幾秒再 `curl https://class.itsmygo.uk/<id>/ \| grep embed` |

## 特殊情況

- **重錄替換**：`plan.py --replace <id>`。新影片上傳、`VIDEO` 換成新網址，舊影片留在 YouTube（回報時提醒使用者自行刪除或設私人）。
- **只補播放清單**（例如早期上傳未入清單）：`uv run "$UP" --add-existing <video_id> --playlist-title "<主題名>｜AI 互動教室" --playlist-order <該主題影片 id 課程順序，逗號分隔>`。
- **清單順序亂了**（連續加入時 YouTube 查詢有幾秒延遲，位置可能算錯；publish.py 每批結尾已自動整理）：`uv run "$UP" --playlist-sort --playlist-id <PL…> --playlist-order <課程順序的影片 id>`。
- **隱私**：`config.json` 的 `privacy` 說了算，**目前是 `public`**——這個 API 專案的 compliance audit 已通過，
  上傳後讀回仍是 public。publish.py 結尾會自動讀回；被打回 private 才是審核出問題。
- **測試管線不想真的上傳**：只能在另一個 worktree／副本裡做 `plan.py --dry-run` → tags → `publish.py` → `ship.sh`（dry-run 會用假 id 寫進 page_content.py，且 ship 只做到 build＋冒煙）。真實 repo 不要 dry-run。

## 不要做的事

- 不手寫標題／說明、不直接編輯 index.html、不 commit 影片（`video/` 的影片已 gitignore）。
- 不在單支上用 `--privacy` 繞過設定檔：格式與隱私一律由 `config.json` 決定，要改就改設定檔再重跑第 1 步。
- 計畫沒給使用者看過不跑 publish.py；沒跑過冒煙不 deploy。
- 不把 YouTube 憑證複製進 repo：憑證只在 `~/.config/youtube-upload/`（repo 是公開的）。

格式細節（檔名、模板欄位、tags 規則、設定檔每個鍵）見 `references/format.md`；底層上傳工具見 youtube-upload skill。
