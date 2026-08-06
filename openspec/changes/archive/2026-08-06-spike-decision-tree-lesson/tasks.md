# Tasks — spike-decision-tree-lesson

## 1. Notebook（事實先行）

- [x] 1.1 建 `lessons/decision-tree/` 目錄與 uv 環境，寫 `lesson.py`：sklearn 決策樹教學 notebook（資料集探索 → 不純度概念 → 訓練與樹視覺化 → 互動調參 max_depth 等 → 過擬合觀察 → 練習 cell）
- [x] 1.2 本機第一層驗證：headless 執行全部 cell 無錯（CPython）
- [x] 1.3 【硬節點】使用者本機驗收 notebook（`uvx marimo edit` 開給使用者看，或部署預覽後一起看）——使用者於部署版驗收通過（以 /opsx:archive 表示接受）

## 2. WASM 匯出與冒煙

- [x] 2.1 `marimo export html-wasm --mode edit` 匯出，本機 http.server 起站
- [x] 2.2 第二層驗證：瀏覽器實開 WASM 版，Pyodide 載入完成、全部 cell 執行無錯、互動元件可動；記錄首次載入時間與踩到的坑

## 3. 教學頁（左側，AI 自由發揮）

- [x] 3.1 設計並實作左側教學解說頁（單檔 HTML，互動圖解自由設計），內容嚴格對照 notebook 實際 cell
- [x] 3.2 組裝左右分欄：iframe 嵌入 `nb/`、載入中狀態提示、「下載 .py」入口、極簡根路徑課程列表
- [x] 3.3 整站本機驗證：左右對照可用、深連結 / 捲動行為正常

## 4. 部署與交付

- [x] 4.1 讀 homelab-infra skill 的 infra.md，確認 Cloudflare Pages 部署方式後部署 `dist/`
- [x] 4.2 線上冒煙：公開網址實測 WASM 執行正常
- [x] 4.3 寫 spike 踩坑紀錄 `lessons/decision-tree/NOTES.md`（載入時間、套件、MIME、iframe 行為等實測結論，餵未來 skill change），向使用者交付網址
