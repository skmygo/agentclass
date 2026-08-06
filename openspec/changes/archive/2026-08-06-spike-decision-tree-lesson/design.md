# Design — spike-decision-tree-lesson

## Context

動機見 proposal.md。環境事實：本機有 `uv`/`uvx`（marimo 隨用隨取，不需全域安裝）；部署目標 Cloudflare Pages（動 infra 前先讀 homelab-infra skill 的 `references/infra.md`）；探索階段已確認 Pyodide 官方支援 numpy / pandas / scikit-learn / matplotlib，決策樹題目在 WASM 可行。

## Goals / Non-Goals

**Goals**

- 走通「本機驗證 → WASM 匯出 → 冒煙測試 → Cloudflare Pages 部署」整條管線，產出一個可分享網址
- 左側教學品質做到「能真的教會人決策樹」，教學法由 AI 自由設計（這是未來 skill 的明確原則：skill 只管工程與正確性底線，不管教學法）
- 沉澱踩坑紀錄，作為未來 skill change 的輸入

**Non-Goals**

- 不做帳號 / 進度追蹤 / 任何後端
- 不在本 change 內寫 skill（spike 結論出來後另開 change）
- 不做手機版最佳化（雙欄對照本質上是桌面場景；小螢幕給可用的降級即可）
- 不做多課 index 首頁的完整設計（給最簡單的入口即可）

## Decisions

1. **右側執行方式：自家 host 的 `marimo export html-wasm --mode edit` + iframe**
   - 替代方案：marimo islands（實驗性，未來再說）、iframe marimo.app（依賴外部服務、程式碼塞 URL 難維護）。
   - edit mode 而非 run mode：學員要能改程式碼，這是明確需求。

2. **左側教學頁：單檔靜態 HTML（無 build step）**
   - 替代方案：Vite + React。spike 階段引入 build 鏈得不償失；教學互動圖解用原生 JS/SVG/CSS 足夠。若未來某課的互動複雜度真的需要 React，skill 化時再升級頁殼。
   - 「像 react 類型」的體驗（元件化、互動圖解）用手寫元件達成，交付物仍是純靜態。

3. **目錄與網址結構：一站多課**
   - repo：`lessons/decision-tree/`（`lesson.py` + `page/` 教學頁源 + `dist/` 組裝產物）
   - 網址：`/<lesson>/` 教學頁、`/<lesson>/nb/` WASM notebook、根路徑放極簡課程列表
   - 部署單位是整個 `dist/` 站，未來加課即加子目錄重新部署。

4. **notebook 先行**：先寫 `lesson.py` 在本機 CPython 跑通並由使用者驗收，再寫左側解說對照它。解說描述的一切行為必須在 notebook 裡真實存在（spec「教學內容與程式碼一致」）。

5. **雙層驗證的落地**
   - 第一層：`uvx marimo export html lesson.py`（headless 執行全部 cell，CPython 環境驗證）
   - 第二層：`python -m http.server` 起本機站 → 用瀏覽器自動化開 WASM 版，等待 Pyodide 載入完成，檢查無 cell 錯誤、關鍵輸出存在。
   - Playwright 若專案內沒有現成環境，用 Claude 的瀏覽器工具人工代跑同等檢查即可（spike 階段允許；skill 化時固化成腳本）。

6. **「下載 .py」入口**：教學頁放固定連結指向 `/decision-tree/lesson.py`（原始檔隨 dist 一起部署）。marimo edit mode 介面本身也有匯出能力，兩個途徑並存。

## Risks / Trade-offs

- [Pyodide 首次載入慢（數十 MB）] → 教學頁在 iframe 載入期間顯示明確的「環境準備中」說明，並把這件事寫進學員可見的文案；載入時間實測數字記進踩坑紀錄
- [本機 CPython 跑通但 WASM 掛掉（套件差異）] → 這正是第二層驗證存在的理由；決策樹所用套件已確認在 Pyodide 支援清單內
- [matplotlib 在 WASM 的後端行為可能與本機不同] → spike 實測；必要時改用 marimo 原生繪圖或調整 matplotlib 用法
- [Cloudflare Pages 對 `.wasm`/特殊檔案的 MIME 或大小限制] → marimo 官方文件明列支援 Cloudflare Pages 部署；實測為準，問題記錄之
- [iframe 與外層頁的捲動/焦點互搶] → spike 實測調整；最壞情況右側加「全螢幕開啟」連結繞過

## Migration Plan

全新靜態站，無遷移。回滾 = Cloudflare Pages 回滾到前一個 deployment 或下架 project。

## Open Questions

- 左右欄寬比例、左側是否需要「跳到第 N 格」的深連結——實作時依實際觀感定，不影響架構
- 多課 index 的資訊架構——下一個 change（skill 化）再定
