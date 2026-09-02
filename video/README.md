# video/ — 用程式上傳影片到 YouTube 頻道

`upload.py` 用 YouTube Data API v3 把 `data/` 裡的影片傳到自己的頻道
（[UCxwORIgu1LL5uGqQWmxmdLA](https://www.youtube.com/channel/UCxwORIgu1LL5uGqQWmxmdLA)）。
單檔 PEP 723 腳本，`uv run` 會自己裝依賴，**不動 repo 根的 `pyproject.toml`**、也不會被 `build.sh` 部署。

```
video/
├── upload.py              上傳程式
├── README.md              本檔
├── client_secret.json     OAuth 用戶端憑證（自己下載放這裡，已 gitignore）
├── token.json             第一次登入後自動產生（已 gitignore）
└── data/
    ├── 01litellm-basics.mp4    影片（*.mp4 已 gitignore，repo 是公開的）
    ├── 01litellm-basics.json   同名 sidecar：標題／說明／tags／privacy（可進版控）
    └── uploaded.jsonl          上傳紀錄：檔名 → video id／網址（防重複上傳）
```

## 一次性設定（約 5 分鐘）

1. 開 <https://console.cloud.google.com/>，建一個專案（或用現有的）。
2. **API 和服務 → 程式庫** → 搜「YouTube Data API v3」→ 啟用。
3. **API 和服務 → OAuth 同意畫面**：
   - User type 選 **External**，填 app 名稱與聯絡信箱，其他留空即可。
   - **Test users** 加上要上傳的那個 Google 帳號（不加會被擋 `access_denied`）。
4. **API 和服務 → 憑證 → 建立憑證 → OAuth 用戶端 ID** → 應用程式類型選 **電腦版應用程式**
   → 建立 → **下載 JSON**，存成 `video/client_secret.json`。
5. 第一次跑 `upload.py` 會開瀏覽器要你登入並允許；登入時**選對頻道**
   （若有品牌帳號，Google 會多一個「選擇帳戶／頻道」畫面）。程式會核對登入頻道 id，選錯會直接停。

## 上傳

```bash
# 先看會送出什麼（不登入、不上傳）
uv run video/upload.py video/data/01litellm-basics.mp4 --dry-run

# 正式上傳：metadata 讀同名 sidecar（data/01litellm-basics.json）
uv run video/upload.py video/data/01litellm-basics.mp4

# 命令列覆蓋 sidecar
uv run video/upload.py video/data/01litellm-basics.mp4 --privacy unlisted --playlist-id PLxxxx
```

成功後印出 `https://youtu.be/<id>` 與 Studio 編輯連結，並寫一行到 `data/uploaded.jsonl`；
同一個檔名再傳會被擋，確定要重傳加 `--force`。所有選項：`uv run video/upload.py -h`。

### 這台機器沒桌面／瀏覽器在別台電腦

```bash
# 在自己的電腦開隧道（port 與 --port 一致，預設 8090）
ssh -L 8090:localhost:8090 sk@<這台機器>

# 在這台機器
uv run video/upload.py video/data/01litellm-basics.mp4 --no-browser
```

程式印出授權網址 → 貼到自己電腦的瀏覽器登入 → Google 導回 `localhost:8090` → 經隧道回到這裡完成。
token 存好後之後就不需要再做這段。

## 上傳後放進課程頁

影片網址寫進該課 `page_content.py`（`NB` 下一行），重跑 page-fill 就會嵌在教學欄標題之後：

```python
VIDEO = "https://youtu.be/<id>"  # 課程影片（YouTube；video/upload.py 上傳）
```

```bash
python3 .claude/skills/make-lesson/scripts/page-fill.py content/<topic>/<id>
bash scripts/build.sh && npx wrangler pages deploy dist --project-name=agentclass
```

## 要知道的限制

- **未審核專案上傳的影片會被鎖成私人。** Google 規定 2020-07-28 之後建立、沒通過
  [API compliance audit](https://support.google.com/youtube/contact/yt_api_form) 的 API 專案，
  用 `videos.insert` 上傳的影片一律「私人（鎖定）」——就算指定 `unlisted`／`public` 也一樣，Studio 也改不了。
  要公開有兩條路：填上面那張表申請審核（免費，通常數天到數週），或需要公開的那支改在 Studio 手動上傳。
  `--privacy` 預設就是 `private`。
- **配額**（2026 現行制）：`videos.insert` 自己一桶，每個專案每日 100 次；其他呼叫共用每日 10,000 點
  （縮圖 50、加播放清單 50、查頻道 1）。個人上課影片完全用不完，用完等太平洋時間午夜重置。
- **token 七天到期**：OAuth 同意畫面停在「測試」狀態時，refresh token 七天失效，到時會要你重新登入一次。
  不想每週登入：同意畫面按「發佈應用程式」（不用送驗證，只是登入時多一個「未經驗證」警告頁，按進階→繼續）。
- **自訂縮圖**（`--thumbnail`）要頻道先在 <https://www.youtube.com/verify> 完成電話驗證，否則 403。
- 標題 ≤100 字、說明 ≤5000 字、標題與說明不能含 `<` `>`，程式會在本機先擋。

## Sidecar 欄位

```json
{
  "title": "必填（沒有就用檔名）",
  "description": "說明，可多行（\\n）；課程連結一律用 https://class.itsmygo.uk/<id>/",
  "tags": ["逗號分隔的字串陣列"],
  "category": "27",
  "privacy": "private | unlisted | public",
  "language": "zh-Hant",
  "playlist_id": "PL...（選填）",
  "thumbnail": "相對於影片所在目錄的路徑（選填）",
  "made_for_kids": false
}
```
