# Spike: 決策樹互動教學課（左教學 / 右 marimo）

## Why

要做一系列「AI 生成、純網址分享」的教學課：左邊是詳細教學解說、右邊是學員可以自己改自己跑的 marimo notebook（瀏覽器內 WASM 執行，零登入零安裝）。在把整套流程固化成可複用的 skill 之前，先用「機器學習決策樹」這一課把整條管線走通一次，踩出實際的坑（Pyodide 載入時間、matplotlib 在 WASM 的表現、Cloudflare Pages 部署細節），spike 的結論將決定未來 skill 的形狀。

## What Changes

- 新增第一課 `decision-tree/`：marimo 教學 notebook（sklearn 決策樹，含互動參數）+ 左右分欄教學頁
- 建立單課製作管線：本機 CPython 跑通 → `marimo export html-wasm --mode edit` → 本機 WASM 冒煙驗證 → 部署 Cloudflare Pages
- 產出可分享的公開網址（一個站，未來多課共存於子路徑）
- 記錄 spike 過程踩到的坑與結論（餵給未來的 skill change）

## Capabilities

### New Capabilities

- `interactive-lesson`: 互動教學課的行為——左右分欄（左：教學解說長頁；右：內嵌 marimo notebook）、學員在瀏覽器內即改即跑（WASM edit mode、無帳號、互相隔離）、可下載 `.py` 帶走、純靜態部署以網址分享。

### Modified Capabilities

（無——全新專案，沒有既有 spec。）

## Impact

- 新目錄：`lessons/decision-tree/`（notebook 原始碼 + 教學頁 + build 產物）
- 依賴：uv/uvx（已裝）、marimo（uvx 隨用隨取）、Playwright 或瀏覽器工具做冒煙驗證
- 部署：Cloudflare Pages（動 infra 前先讀 homelab-infra skill 的 infra.md）
- 不影響任何既有系統；spike 失敗的最壞情況是結論「WASM 方案不可行、需改架構」
