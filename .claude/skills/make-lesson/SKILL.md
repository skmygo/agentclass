---
name: make-lesson
description: 讀取參考資料（notebook、文章、教材、資料集、網址皆可），產出一堂或一系列「AI 互動教室」互動課程並上線。觸發時機：使用者要新開一堂課、把某份教材/主題做成課、重做或大改既有課程、換掉課程用的模型／資料重驗。產出＝左教學頁＋右實作區的課程（Pyodide 可跑→內嵌 marimo WASM notebook；跑不了→唯一一份 molab notebook），並自動接進 首頁→主題→課程 的網站結構。
---

# make-lesson：產一堂 AI 互動教室的課

把一份參考資料變成一堂可上線的互動課。你負責教學創作，本 skill 只固定**工程管線與網站結構**；教學法、章節安排、互動設計、文案語氣、視覺發揮完全自由。

## 兩份必讀 reference

- `references/engineering.md` — 工程底線：定軌 spike、marimo/Pyodide 管線、WASM 限制與踩坑、外部軌（molab）機制、驗證、部署。**動手寫 notebook 之前先讀完**，坑都是實測踩出來的。
- `references/site.md` — 網站結構與頁面規範：導覽鏈、排序規則、課程頁必備元素、禁止事項、教學品質準則（含「非決定性輸出怎麼寫」「挑戰要附解答」）。

行為契約在 `openspec/specs/interactive-lesson/spec.md`，產出必須滿足全部 requirement。

## 鐵律：先寫程式定軌，一課只做一版程式

**課程程式先於文案**：動筆寫教學之前，先把課程核心程式在 CPython 寫出來跑通
（spike 腳本放 `content/<topic>/_spikes/spike_*.py`，PEP 723 檔頭、`uv run --script` 可跑；
build.sh 不會部署它，但它是之後「換模型／換資料重驗」的起點，**留在 repo 裡**），
同時用 `pyodide-spike.mjs` 實測所需套件裝不裝得進瀏覽器。定軌二選一，**不做兩套程式**：

- **Pyodide 裝得起、瀏覽器算力夠** → **純瀏覽器課**：notebook 內嵌右欄，即改即跑。
- **裝不起（無 WASM wheel）／需要 GPU／需要真網路** → **外部軌課**（scaffold `--external`）：
  唯一一份 notebook `<id>_ext.py` 在 molab 執行。**大量解說寫進 notebook 的 md cells，
  讓它自成完整教材**；左頁照樣完整教學，右欄是常駐的 molab 導流面板。
  預設純 CPU；真的要 GPU 才加 `--gpu`。

## 起手：scaffold 一鍵建骨架（別手動複製模板）

```bash
bash .claude/skills/make-lesson/scripts/new-lesson.sh <id> "<課名>" <topic-slug> "<主題名>" [--external [--gpu]]
```

script 做完（不用再做）：`content/<topic>/<id>/` 三件套從 `assets/templates/` 複製並代換好
id／課名／主題／molab 網址、CPU/GPU 二選一、生成自檢已跑、root `uv sync` 已跑（純瀏覽器課）。
**build.sh 與 pyproject 都不用碰**。只有新開主題才需要手動
`cp assets/templates/topic.html content/<topic-slug>/index.html`。

## 寫頁面：內容放 `page_content.py`，用 page-fill 填進骨架

版面骨架與共用行為在 `/shared/lesson.css`／`lesson.js`（全站一份，別為單一課去改它）。
課程頁你真正要寫的只有內容區——**寫在 `content/<topic>/<id>/page_content.py`**
（TITLE／DESCRIPTION／STYLE／WRAP／SCRIPT／NB／PANEL_STEPS 純字串常數），然後：

```bash
python3 .claude/skills/make-lesson/scripts/page-fill.py content/<topic>/<id>
```

它只替換 title／meta／`<style>`／`.wrap` 內容／面板步驟／hero script，骨架不動、可重跑、
會自檢骨架契約。**page_content.py 是頁面內容的正本**（不部署）：模型換了、數字變了，
改常數重跑；小修直接 Edit index.html 也行，但記得同步回 page_content.py。
純瀏覽器課另有 `<body data-ready-figures="N">`（N＝notebook 圖表數，至少 1）。

## 流程

1. **消化參考資料**：提煉這堂課要教會學員的事、找出最有戲劇性的「aha 時刻」當課程主軸。
   參考資料含內網或私人資訊時放 `ref_data/`（已 gitignore，repo 是公開的）。
2. **先寫程式，實測定軌**：spike 腳本跑通核心程式——左頁之後引用的每個數字與方向性宣稱
   都在這步驗證（量化宣稱寫反比少一個互動更傷）；`pyodide-spike.mjs <套件...>` 實測，
   任一 FAIL 或需 GPU／真網路 → 外部軌，**不要 mock 依賴鏈硬上**。
   **會打 LLM／外部 API 的課**：輸出是非決定性的——多跑幾次再寫文案，寫範圍不寫點估計；
   模型名、`max_tokens` 等集中成一格常數（`CHAT_MODEL`），全 notebook 只引用它。
3. **scaffold → 創作**：
   - 純瀏覽器課：寫 `lesson.py` 與 `page_content.py`。
   - 外部軌課：寫 `<id>_ext.py`（唯一的程式版本——解說寫好寫滿，學員只帶這份檔案也能學完）
     與 `page_content.py`（左頁教學＋右欄 molab 面板）。
   - 挑戰題**附折疊解答**（模板已有 `mo.accordion` 格）：LEVEL 1/2 給完整程式碼與預期輸出，
     LEVEL 3 給方向與「怎麼驗證自己做對了」。
   - 外部軌課的 hero 互動沒有內嵌 Python 可用 → 用**實測紀錄做可重播的互動**（選問題→
     播放 trace／答案），文案註明「內容是 notebook 的實測紀錄」。
4. **接進網站**（site.md 的 wiring 清單）：主題頁課卡、首頁主題卡的課數、上一課的「下一課」連結。
5. **驗證**（依軌道分流，準則見 engineering.md）：
   - 純瀏覽器課（雙層）：`uv run marimo export html content/<topic>/<id>/lesson.py -o check.html`
     （CPython 全 cell）→ `bash .claude/skills/make-lesson/scripts/smoke-all.sh --build`（WASM 冒煙）
   - 外部軌課：`bash .claude/skills/make-lesson/scripts/verify-ext.sh <topic> <id> [關鍵字...]`
     （sandbox 全 cell ＋ 渲染輸出掃描，關鍵字給了就印出左頁要引用的數字）→ `smoke-all.sh --build`
   - wiring 自檢：`grep -o '/<id>/' dist/<topic-slug>/index.html` 有中、首頁課數已更新
6. **給使用者預覽**：`node .claude/skills/make-lesson/scripts/preview-shots.mjs / /<topic-slug>/ "/<id>/@#hero-按鈕"`
   （`@selector` 會先點再截，驗 hero 互動真的會動），等確認再部署。
7. **部署**：`npx wrangler pages deploy dist --project-name=agentclass`（憑證見 homelab-infra skill），
   然後 `smoke-all.sh --base https://agentclass.pages.dev` 線上冒煙（CDN 冷資產會自動重試一次）。
   外部軌課記得 **git push**（molab 直讀 GitHub main，不 push 連結是死的），並請使用者在 molab 實跑一次。
8. **記錄**：新踩的坑寫進該課 `NOTES.md`（一個系列可以共用主題層的 `content/<topic>/NOTES.md`）；
   管線層級的新發現回寫本 skill 的 references 或 scripts（課程會被刪，skill 不會——
   **知識只有寫回 skill 才留得住**）。

## 換模型／換資料重驗（系列課常見）

不是從頭做：`_spikes/` 改常數重跑 → 行為或數字有變的地方改 `<id>_ext.py` 與 `page_content.py`
→ `verify-ext.sh` → `page-fill.py` → `smoke-all.sh --build` → 預覽 → 部署＋push。
重驗時特別盯：模型會不會把參數／搜尋詞翻成英文、推理型 `max_tokens` 夠不夠、
agent 的「要不要用工具」判斷是否還成立——這些都是實測過會隨模型改變的行為。

## 唯一不可妥協的五件事

1. **教學與程式一致**：左頁說的每個行為、每個數字，notebook 都要真的存在且為真。
   非決定性輸出寫範圍與方向，並讓學員知道「你跑出來的數字會不同」。
2. **一課一版程式**：定軌後只寫一份 notebook；發現走錯軌就換軌重寫，不是加一版。
3. **驗證過才上線**：純瀏覽器課 WASM 冒煙沒過不部署；外部軌課 sandbox 全跑＋頁面冒煙沒過不部署。
4. **課程頁不寫平台系統說明**（哪些算、哪些不算見 site.md）。
5. **寫進 repo 的才算存在**：spike 腳本、page_content.py、NOTES——對話裡的東西會消失。
