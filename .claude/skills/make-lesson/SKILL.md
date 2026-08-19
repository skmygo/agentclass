---
name: make-lesson
description: 讀取參考資料（notebook、文章、教材、資料集、網址皆可），產出一堂「AI 互動教室」互動課程並上線。觸發時機：使用者要新開一堂課、把某份教材/主題做成課、重做或大改既有課程。產出＝左教學頁＋右 marimo WASM notebook 的課程（必要時附 molab GPU 軌道），並自動接進 首頁→主題→課程 的網站結構。
---

# make-lesson：產一堂 AI 互動教室的課

把一份參考資料變成一堂可上線的互動課。你負責教學創作，本 skill 只固定**工程管線與網站結構**；教學法、章節安排、互動設計、文案語氣、視覺發揮完全自由。

## 兩份必讀 reference

- `references/engineering.md` — 工程底線：marimo/Pyodide 管線、WASM 限制與踩坑、GPU 軌道（molab）機制、雙層驗證、部署。**動手寫 lesson.py 之前先讀完**，坑都是實測踩出來的。
- `references/site.md` — 網站結構與頁面規範：導覽鏈、排序規則、課程頁必備元素、禁止事項、品質建議清單。

行為契約在 `openspec/specs/interactive-lesson/spec.md`，產出必須滿足全部 requirement。

## 起手：scaffold 一鍵建骨架（別手動複製模板）

```bash
bash .claude/skills/make-lesson/scripts/new-lesson.sh <id> "<課名>" <topic-slug> "<主題名>" [--gpu]
# 例：bash .claude/skills/make-lesson/scripts/new-lesson.sh clustering "分群：沒有答案也能找出結構" ml-basics "學基礎機器學習"
```

script 做完（不用再做）：四件套從 `assets/templates/` 複製並代換好 id／課名／主題／molab 網址、
純瀏覽器課已剝除全部 `[GPU]` 區塊（`--gpu` 才保留＋建 `<id>_gpu.py`）、smoke-test 的
`H1_TEXT` 已填、build.sh 已加該課、`uv sync` 已跑。只有新開主題才需要手動
`cp assets/templates/topic.html site/<topic-slug>/index.html`。

**scaffold 之後一律用 Edit 改內容區，不要整檔重寫**——page 的版面骨架（CSS、狀態列、
golab／輪詢 JS、splitter 引入）是全站一致的固定資產，整檔重寫既燒 token 又容易弄掉
「勿刪」元素。你真正要動的只有：hero（含開場互動 JS）、各 section、練習卡、endnav、
`READY_FIGURES`、語義色 token。模板內「必改／勿刪／自由發揮」都有註解標記。

## 流程

1. **消化參考資料**：提煉這堂課要教會學員的事、找出最有戲劇性的「aha 時刻」當課程主軸。參考資料含內網或私人資訊時放 `ref_data/`（已 gitignore，repo 是公開的）。
2. **決定軌道**（判斷準則見 engineering.md）：
   - 套件在 Pyodide 有 wheel、瀏覽器算力夠 → **純瀏覽器課**
   - 需要 GPU / torch / 大模型 → **雙軌課**：核心概念一律做成瀏覽器內可跑的迷你版，真實版走 molab GPU 外部連結。GPU 是延伸不是前提。
3. **scaffold（上面那行指令）→ 創作**：寫 `lesson.py` 內容與 page 內容區。左頁引用的每個數字與方向性宣稱（「k=1 準確率必是 100%」「直線兩端猜太低」「手肘在 3」），**先用 `uv run python` 小腳本驗過再寫進文案**——量化宣稱寫反，比少一個互動更傷（實測踩過：凸型資料配直線的殘差方向寫反）。
4. **接進網站**（site.md 的 wiring 清單）：主題頁課卡、首頁主題卡的課數、上一課的「下一課」連結（build.sh 那行 scaffold 已加）。
5. **雙層驗證**：
   - `uv run marimo export html lesson.py -o check.html`（CPython 全 cell 執行）
   - `scripts/build.sh`——盯輸出：檔案數應約「既有＋每課 ~15 檔」；出現「assets 與共用版本不一致」警告＝marimo 版本飄了，回頭釘版重來，別帶著獨立 assets 上線
   - dist **根目錄**起 server（`python3 -m http.server 8787 -d dist`），`node smoke-test.mjs http://127.0.0.1:8787/<id>/nb/index.html`（別只 serve nb 目錄：assets 走 `/shared/` 絕對路徑）
   - wiring 自檢：`grep -o '/<id>/' dist/<topic-slug>/index.html` 有中、首頁課數已更新
6. **給使用者預覽**：server 開著＋`node .claude/skills/make-lesson/scripts/preview-shots.mjs / /<topic-slug>/ /<id>/` 截圖（課程頁會自動等 notebook 全跑完才截），等確認再部署。
7. **部署**：`npx wrangler pages deploy dist --project-name=agentclass`（憑證見 homelab-infra skill），部署後線上驗證。
8. **記錄**：新踩的坑寫進該課 `NOTES.md`；管線層級的新發現回寫本 skill 的 references 或 scripts（課程會被刪，skill 不會——**知識只有寫回 skill 才留得住**）。

## 唯一不可妥協的三件事

1. **教學與程式一致**：左頁說的每個行為、每個數字，右邊 notebook 都要真的存在且為真。
2. **驗證過才上線**：WASM 冒煙沒過不部署。
3. **課程頁不寫平台系統說明**（哪些算、哪些不算見 site.md）。
