# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 這個 repo 是什麼

「AI 互動教室」——純靜態的互動課程網站，部署在 Cloudflare Pages（<https://agentclass.pages.dev>）。
每一課是「左教學頁 ＋ 右實作區」：右邊要嘛是內嵌的 marimo WASM notebook（Pyodide，瀏覽器內執行），
要嘛是導向 molab（marimo 官方雲）的面板。**沒有後端、沒有帳號、沒有資料庫**——只有 `content/` 的原始碼
與 `scripts/build.sh` 組出來的 `dist/`。

## 建課一律走 make-lesson skill

新開／重做／大改課程、換模型換資料重驗 → 用 `make-lesson` skill，別手動複製模板、別手動改 `build.sh`。

- `.claude/skills/make-lesson/SKILL.md` — 流程與鐵律
- `.claude/skills/make-lesson/references/engineering.md` — 工程底線（定軌、marimo/Pyodide 坑、molab、驗證、Pages 上限）
- `.claude/skills/make-lesson/references/site.md` — 網站結構、頁面規範、教學品質準則
- `openspec/specs/interactive-lesson/spec.md` — 課程的行為契約（產出必須滿足全部 requirement）

管線層級的新發現要**回寫 skill 的 references／scripts**；課程層級的坑寫該課或該主題的 `NOTES.md`
（課程會被刪，skill 不會）。

## 常用指令

```bash
uv sync                                   # 全站共用的 Python 環境（repo 根一個 venv）
bash scripts/build.sh                     # 組 dist/（自動發現所有課，含防呆與 Pages 上限檢核）
bash .claude/skills/make-lesson/scripts/smoke-all.sh --build          # build + 起 server + 全站冒煙 + 收 server
bash .claude/skills/make-lesson/scripts/smoke-all.sh --base https://agentclass.pages.dev   # 線上冒煙
node content/<topic>/<id>/smoke-test.mjs http://127.0.0.1:8787/<id>/  # 單課冒煙（純瀏覽器課網址是 /<id>/nb/index.html）
ruff check .                              # lint（全域 ruff，設定在 ruff.toml）
npx wrangler pages deploy dist --project-name=agentclass              # 部署（憑證見 homelab-infra skill）
```

建課／驗課（皆在 repo 根執行）：

```bash
bash .claude/skills/make-lesson/scripts/new-lesson.sh <id> "<課名>" <topic> "<主題名>" [--external [--gpu]]
python3 .claude/skills/make-lesson/scripts/page-fill.py content/<topic>/<id>     # page_content.py → index.html
uv run marimo export html content/<topic>/<id>/lesson.py -o check.html           # 純瀏覽器課：CPython 全 cell 驗證
bash .claude/skills/make-lesson/scripts/verify-ext.sh <topic> <id> [關鍵字...]   # 外部軌課：sandbox 全 cell + 輸出掃描
node .claude/skills/make-lesson/scripts/preview-shots.mjs / /<topic>/ "/<id>/@#hero-按鈕"   # 預覽截圖
node .claude/skills/make-lesson/scripts/pyodide-spike.mjs <套件...>              # 定軌：套件裝不裝得進瀏覽器
```

本機只有 `python3`（沒有 `python`）——用 `python` 跑 page-fill 會**靜默失敗**、index.html 不更新。

## 架構

**檔案一棵樹（`content/`），網址兩層扁平**——課程實體放在主題目錄下，但課程網址永遠在根層，
所以課換主題、主題改名都不會弄斷已分享的連結：

```
content/index.html             → /              首頁（主題卡，越新越上，卡上有課數）
content/<topic>/index.html     → /<topic>/      主題頁（課卡）
content/<topic>/<id>/          → /<id>/         課程頁 index.html + notebook .py [+ nb/]
content/<topic>[/<id>]/lesson-mode （不部署）      互動模式 app|edit，沒有這個檔＝edit
content/shared/                → /shared/       lesson.css / lesson.js / topic.css / splitter.js + 共用 WASM assets
content/<topic>/_spikes/       （不部署）       定軌用 PEP 723 腳本，換模型重驗的起點
```

一課只能有一版可執行程式，`build.sh` 依檔名自動判軌並防呆（兩者並存直接 exit 1）：

- **純瀏覽器課** `lesson.py` → build 時 `marimo export html-wasm` 進 `dist/<id>/nb/`
- **外部軌課** `<id>_ext.py` → 只複製教學頁與 .py 原檔；notebook 在 molab 直讀 GitHub main 執行

純瀏覽器課另有**互動模式**（`lesson-mode` 檔，課程層 > 主題層 > 預設 `edit`）：
`edit`＝程式碼可見可改（程式碼本身是教材，如 ml-basics 教 scikit-learn）；
`app`＝隱藏程式碼只留互動（右欄是教學模擬，如 local-llm／genai-intro，走 `--mode run`）。
app 模式課的教學頁要有 `<body data-nb-mode="app">`，兩邊不一致 build 會擋；
**文案與挑戰題不能叫學員改程式碼**（判準與寫法見 make-lesson skill）。

`build.sh` 另外處理：`auto_instantiate` 後處理（marimo 0.23 export 不吃專案設定）、把每課 698 個
相同的 marimo assets 抽到 `/shared/assets/` 共用（不共用的話 dist 會從 28M 膨脹到 112M）、
course id 重複檢查、`404.html`（關掉 Pages 的 SPA fallback）、Pages 檔案數／單檔大小檢核。
**新增課程不需要動 `build.sh` 或 `pyproject.toml`。**

課程頁的內容正本是 `content/<topic>/<id>/page_content.py`（純字串常數），用 `page-fill.py` 填進
`index.html` 的內容區；骨架（版面與行為）在 `/shared/`。直接 Edit `index.html` 可以，但要同步回
`page_content.py`。

## 這個 repo 的硬性約束

- **course id 全站唯一**（網址在根層），scaffold 與 build 都會擋。
- **改 `content/shared/` ＝ 改全站**：課程專屬樣式寫在該課頁面的 `<style>`／inline script。
- **marimo 全站釘同一版**（根 `pyproject.toml` 的 `marimo==0.23.16`）：版本一飄，export assets hash
  就對不上、共用機制失效。升版要一次升全站並重跑雙層驗證。
- **repo 是公開的**（molab 直讀 GitHub main）：含內網／私人資訊的參考教材放 `ref_data/`（已 gitignore），
  部署前掃過 API key 零外洩。
- **驗證過才上線**：純瀏覽器課要 CPython export ＋ WASM 冒煙雙層都過；外部軌課要 `verify-ext.sh` ＋ 頁面冒煙。
- **外部軌課上線後要 `git push`**，否則 molab 連結是舊的／死的。
- ruff 對 marimo cell 報 B018／PLR1711 是**假警報**（最後運算式＝渲染輸出、return 收尾＝marimo 產生），
  `ruff.toml` 已 per-file ignore——不要去「修」格式。
- 本機驗證一律用 repo 根的 headless Playwright（`npm install`），**不要用 claude-in-chrome 測 localhost**
  （使用者的 Chrome 可能在別台機器）。

## OpenSpec

行為契約在 `openspec/specs/`，變更提案走 `openspec/changes/`（完成後 archive）。
改動課程網站的**可觀察行為**（版面、導覽、載入體驗、課程型態）時先看 spec；純內容創作不需要提案。
