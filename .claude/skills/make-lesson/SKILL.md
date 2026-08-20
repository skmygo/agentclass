---
name: make-lesson
description: 讀取參考資料（notebook、文章、教材、資料集、網址皆可），產出一堂「AI 互動教室」互動課程並上線。觸發時機：使用者要新開一堂課、把某份教材/主題做成課、重做或大改既有課程。產出＝左教學頁＋右實作區的課程（Pyodide 可跑→內嵌 marimo WASM notebook；跑不了→唯一一份 molab notebook），並自動接進 首頁→主題→課程 的網站結構。
---

# make-lesson：產一堂 AI 互動教室的課

把一份參考資料變成一堂可上線的互動課。你負責教學創作，本 skill 只固定**工程管線與網站結構**；教學法、章節安排、互動設計、文案語氣、視覺發揮完全自由。

## 兩份必讀 reference

- `references/engineering.md` — 工程底線：定軌 spike、marimo/Pyodide 管線、WASM 限制與踩坑、外部軌（molab）機制、驗證、部署。**動手寫 notebook 之前先讀完**，坑都是實測踩出來的。
- `references/site.md` — 網站結構與頁面規範：導覽鏈、排序規則、課程頁必備元素、禁止事項、品質建議清單。

行為契約在 `openspec/specs/interactive-lesson/spec.md`，產出必須滿足全部 requirement。

## 鐵律：先寫程式定軌，一課只做一版程式

**課程程式先於文案**：動筆寫教學之前，先把課程核心程式在 CPython 寫出來跑通
（`uv run python` 小腳本），同時用 `pyodide-spike.mjs` 實測所需套件裝不裝得進瀏覽器。
定軌二選一，**不做「瀏覽器迷你版＋外部真實版」兩套程式**：

- **Pyodide 裝得起、瀏覽器算力夠** → **純瀏覽器課**：notebook 內嵌右欄，即改即跑。
- **裝不起（無 WASM wheel）／需要 GPU／需要真網路** → **外部軌課**（scaffold `--external`）：
  直接放棄瀏覽器版，唯一一份 notebook `<id>_ext.py` 在 molab 執行。
  **大量解說寫進 notebook 的 md cells，讓它自成完整教材**；左頁照樣完整教學
  （概念、圖解、真實碼展示、賣點），右欄是常駐的 molab 導流面板，沒有內嵌 notebook。

## 起手：scaffold 一鍵建骨架（別手動複製模板）

```bash
bash .claude/skills/make-lesson/scripts/new-lesson.sh <id> "<課名>" <topic-slug> "<主題名>" [--external]
# 例（純瀏覽器課）：bash .claude/skills/make-lesson/scripts/new-lesson.sh clustering "分群：沒有答案也能找出結構" ml-basics "學基礎機器學習"
# 例（外部軌課）  ：bash .claude/skills/make-lesson/scripts/new-lesson.sh finetune "微調你的第一個 LLM" ai-engineering "學 AI 工程" --external
```

script 做完（不用再做）：`content/<topic>/<id>/` 三件套（notebook、index.html、
smoke-test.mjs）從 `assets/templates/` 複製並代換好 id／課名／主題／molab 網址、
生成自檢已跑、root `uv sync` 已跑（純瀏覽器課）。**build.sh 與 pyproject 都不用碰**
（build 自動發現兩種課；瀏覽器課依賴共用 repo 根的 uv 專案，外部課用 PEP 723）。
只有新開主題才需要手動 `cp assets/templates/topic.html content/<topic-slug>/index.html`。

**scaffold 之後一律用 Edit 改內容區，不要整檔重寫**——版面骨架與共用行為在
`/shared/lesson.css`／`lesson.js`（全站一份，別為單一課去改它）。你真正要動的：
hero（含開場互動 JS）、各 section、練習卡、endnav、頁內 `<style>` 的語義色與 hero 樣式；
純瀏覽器課另有 `<body data-ready-figures="N">`（N＝notebook 圖表數，至少 1）、
外部軌課另有 molab 面板的執行步驟。模板內「必改／勿刪／自由發揮」都有註解標記。

## 流程

1. **消化參考資料**：提煉這堂課要教會學員的事、找出最有戲劇性的「aha 時刻」當課程主軸。參考資料含內網或私人資訊時放 `ref_data/`（已 gitignore，repo 是公開的）。
2. **先寫程式，實測定軌**：
   - 核心程式用 `uv run python` 小腳本寫出來跑通——左頁之後引用的每個數字與方向性宣稱（「k=1 準確率必是 100%」「手肘在 3」）都在這步驗證，量化宣稱寫反比少一個互動更傷（實測踩過）。
   - `node .claude/skills/make-lesson/scripts/pyodide-spike.mjs <套件...>` 實測 Pyodide 裝不裝得起（別用猜的）；任一 FAIL 或需要 GPU／真網路 → 外部軌課，**不要 mock 依賴鏈硬上**（實測過深不見底）。
3. **scaffold（上面那行指令）→ 創作**：
   - 純瀏覽器課：寫 `lesson.py` 與 `index.html` 內容區。
   - 外部軌課：寫 `<id>_ext.py`（唯一的程式版本——解說寫好寫滿，學員只帶這份檔案也能學完）與 `index.html` 內容區（左頁教學＋右欄 molab 面板）。
4. **接進網站**（site.md 的 wiring 清單）：主題頁課卡、首頁主題卡的課數、上一課的「下一課」連結。
5. **驗證**（依軌道分流，準則見 engineering.md）：
   - 純瀏覽器課（雙層）：`uv run marimo export html content/<topic>/<id>/lesson.py -o check.html`（CPython 全 cell）→ `scripts/build.sh`（盯檔案數與 assets 警告）→ dist 根目錄起 server（`python3 -m http.server 8787 -d dist`）跑 `node content/<topic>/<id>/smoke-test.mjs http://127.0.0.1:8787/<id>/nb/index.html`
   - 外部軌課：`uv run marimo export html --sandbox content/<topic>/<id>/<id>_ext.py -o check_ext.html`（自動建 PEP 723 環境、全 cell 執行；GPU cell 要能無 GPU 優雅降級）→ `scripts/build.sh` → 同上起 server 跑 `node content/<topic>/<id>/smoke-test.mjs http://127.0.0.1:8787/<id>/`（頁面完整性＋入口連結）
   - wiring 自檢：`grep -o '/<id>/' dist/<topic-slug>/index.html` 有中、首頁課數已更新
6. **給使用者預覽**：server 開著＋`node .claude/skills/make-lesson/scripts/preview-shots.mjs / /<topic-slug>/ /<id>/` 截圖（純瀏覽器課會自動等 notebook 跑完才截），等確認再部署。
7. **部署**：`npx wrangler pages deploy dist --project-name=agentclass`（憑證見 homelab-infra skill），部署後線上驗證。外部軌課記得 **git push**（molab 直讀 GitHub main，不 push 連結是死的），並請使用者在 molab 實跑一次全量驗證。
8. **記錄**：新踩的坑寫進該課 `NOTES.md`；管線層級的新發現回寫本 skill 的 references 或 scripts（課程會被刪，skill 不會——**知識只有寫回 skill 才留得住**）。

## 唯一不可妥協的四件事

1. **教學與程式一致**：左頁說的每個行為、每個數字，notebook 都要真的存在且為真。
2. **一課一版程式**：定軌後只寫一份 notebook；發現走錯軌就換軌重寫，不是加一版。
3. **驗證過才上線**：純瀏覽器課 WASM 冒煙沒過不部署；外部軌課 sandbox 全跑＋頁面冒煙沒過不部署。
4. **課程頁不寫平台系統說明**（哪些算、哪些不算見 site.md）。
