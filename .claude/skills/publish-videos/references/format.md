# publish-videos 格式規格

## 檔名 → 課程

- 放在 `video/data/`，副檔名 `.mp4`／`.mov`／`.mkv`／`.webm`。
- 規則：`<課程id>.mp4` 或 `NN-<課程id>.mp4`（`NN<課程id>.mp4` 也接受）。前置數字只決定上傳順序。
- 去掉前綴後必須**完全等於** `content/<topic>/<id>/` 目錄名（course id 全站唯一，所以不用寫主題）。
- 一課一支；兩個檔對到同一課 → 整批停。
- 課程必須有 `page_content.py`（`TITLE`、`DESCRIPTION`）。

## metadata（全部由 `video/config.json` 的模板產生）

| 欄位 | 來源 | 例 |
|---|---|---|
| 標題 | `title_template`：`{title}｜{site_name}` | `FastMCP 4：把函式變成 AI 工具，一發請求不用握手｜AI 互動教室` |
| 說明 | `description_template`：`{description}` ＋ 課程／主題／首頁三個連結 | 見下 |
| tags | 模型填的 3–8 個 ＋ `base_tags` ＋ `topic_tags[topic]` | `FastMCP, MCP, …, AI 互動教室, LLM 應用開發, Python` |
| 分類 | `category`（27＝Education） | |
| 語言 | `language`（zh-Hant，defaultLanguage 與 defaultAudioLanguage 同值） | |
| 隱私 | `privacy`（private；審核通過後改 public） | |
| 兒童內容 | 固定 false | |

說明範例：

```
用 FastMCP 4.0 beta 蓋 MCP 工具伺服器：……

▶ 互動課程（瀏覽器內直接實作）：https://class.itsmygo.uk/fastmcp4/
▶ 主題「學 LLM 應用開發」：https://class.itsmygo.uk/llm-apps/
▶ AI 互動教室首頁：https://class.itsmygo.uk/
```

模板可用的變數：`{title}` `{description}`（課程正本）、`{lesson_url}` `{topic_url}` `{site_url}`、
`{topic_name}`（主題頁 `<title>` 去掉「· AI 互動教室」）、`{site_name}`。

硬限制（plan.py 先擋）：標題 ≤100 字、說明 ≤5000 字、標題與說明不含 `<` `>`、tags 總長 ≤500。

## tags 規則

- 3–8 個、每個 ≤30 字、不含逗號與 `<>`、不與固定 tags 重複、彼此不重複。
- 由模型依課程內容填（`plan.py tags <id> ...`），或課程在 `page_content.py` 宣告 `VIDEO_TAGS = [...]` 直接採用。
- 固定 tags：`base_tags`（全站）＋ `topic_tags[topic]`（主題），程式接在後面。

## 播放清單

- 每主題一個，標題 `playlist_title_template`：`{topic_name}｜{site_name}`；標題是唯一鍵，同名就沿用。
- 隱私 `playlist_privacy`（public：清單本身公開，裡面的私人影片別人看不到，影片公開後就直接可見）。
- id 記在 `config.json` 的 `playlists[topic]`（第一次建立時自動寫入，可版控）。
- 插入位置依主題頁課程順序（`upload.py --playlist-order`），所以晚補的課也會排對。
- 剛建立的清單與剛插入的項目要幾秒才查得到：`upload.py` 遇 404 會等候重試；publish.py 每批結尾跑 `--playlist-sort` 依課程順序整理一次，最終順序不靠插入時的計算。

## 嵌入

- `publish.py` 把 `VIDEO = "https://youtu.be/<id>"` 寫進 `page_content.py`（有就換、沒有就插在 DESCRIPTION 下一行），
  再跑 make-lesson 的 `page-fill.py`：影片區塊插在 hero `</h1>` 之後（spec「課程影片（可選）」）。
- 嵌入是 `youtube-nocookie.com/embed/<id>`、`loading="lazy"`、16:9 `.video-box`（樣式在 shared/lesson.css）。

## 紀錄與暫存

- `video/uploaded.jsonl`：每次上傳一行（檔名、id、網址、時間），可版控；upload.py 用它擋同檔名重傳（`--force` 覆蓋）。
- `video/.plan.json`、`video/.publish-result.json`：本次流程的暫存，已 gitignore。
- `video/config.json`：格式與播放清單 id，可版控——**改格式改這裡**。

## 配額

videos.insert 每個 GCP 專案每日 100 次；其他呼叫共用 10,000 點／日（playlistItems.insert 50、playlists.insert 50、
list 1）。一批十支影片約 600 點，遠低於上限。

## 已知限制

- 未通過 YouTube API 合規審核的專案，API 上傳的影片一律鎖私人（設 public 也沒用）。
- OAuth 同意畫面停在「測試」→ refresh token 七天到期，plan 會提前偵測並要求 `--login`。
- ml-basics 三堂舊式頁（無 page_content.py）不能自動嵌入。
