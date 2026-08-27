# 網站結構與頁面規範

## 資訊架構

**檔案一棵樹（content/），網址兩層扁平**——課程實體放在主題目錄下，
但課程網址永遠在根層：課換主題、主題改名，已分享出去的課程連結都不會斷。

```
content/index.html                →  /              首頁（主題列表）
content/<topic>/index.html        →  /<topic>/      主題頁（課程列表）
content/<topic>/<lesson-id>/      →  /<lesson-id>/  課程（index.html 教學頁 + notebook .py + smoke-test.mjs + NOTES.md）
                                     /<lesson-id>/nb/   marimo WASM notebook（純瀏覽器課；build.sh 產）
                                     外部軌課無 nb/：notebook 是 <id>_ext.py，在 molab 執行
content/shared/                   →  /shared/       全站共用（lesson.css/lesson.js/topic.css/splitter.js/gate.js + WASM assets）
```

- **course id 全站唯一**（網址在根層），scaffold 與 build.sh 都會擋重複。
- 主題與課程 slug 用簡短英文（如 `ml-basics`、`clustering`）。
- build.sh **自動發現** `content/*/*/lesson.py`——新課不用改 build.sh。

## 共用骨架（重要：頁面只寫內容）

- 課程頁版面（CSS）與行為（golab 捲動、就緒輪詢、分頁切換）都在
  `/shared/lesson.css` 與 `/shared/lesson.js`，**全站一份**；課程頁只放內容、
  課程語義色覆蓋、hero 專屬樣式與互動 JS。
- 純瀏覽器課：就緒門檻用 `<body data-ready-figures="N">` 宣告（N = notebook 圖表數，至少 1）。
- 外部軌課：**不引 `/shared/lesson.js`**（那是內嵌 notebook 的行為，外部課用不到，
  引了反而在無 `#nb-frame` 的頁面產生 console 噪音）；右欄 `#molab-panel` 的
  版型樣式在共用 lesson.css。
- 首頁與主題頁共用 `/shared/topic.css`。
- **改共用檔＝改全站**，動之前想清楚；課程專屬需求寫在該課頁面的 `<style>`/inline script。

## 導覽鏈（每一環都要能點）

首頁 → 主題頁 → 課程頁 →（下一課 → …）→ 回主題 → 品牌回首頁

新增一堂課的 wiring 清單（scaffold 印的待辦就是這份）：

1. 課程卡插進主題頁的 `.lessons`，**依課程順序排**（第 1 課在最上；新課通常是
   最後一課，插在主線最下面；補充系列獨立成區、排在主線之後照系列順序）。
   首頁的**主題卡**維持越新越上（沒有該主題就先建主題頁、主題卡插首頁最上面）
2. 課程頁 header：品牌連結（`href="/"`）＋「‹ 回主題」連結（`href="/<topic>/"`）
3. 課末放導覽區：**下一課**（同主題內有的話）與**回主題**
4. **回頭補鏈**：新課上線後，同主題的前一課要補「下一課 →」指向新課
5. 主題卡上的課程數字（`TOPIC · N 門課`）同步更新

## 主題密碼閘（可選）

某些主題可設進入密碼（輕量防路人，**不是安全機制**——repo 公開、純前端、devtools 可繞過，設計如此）。
實作是 `/shared/gate.js` 的不透明覆蓋層：內容照常載入（notebook 順便暖機、冒煙測試的可見性檢查不受影響），
輸入一次同主題全部頁面解鎖（localStorage）。

- 上鎖＝該**主題頁＋該主題每一堂課程頁**的 `<head>`（緊接 css link 之後）各加一行：

  ```html
  <script src="/shared/gate.js" data-gate="<topic-slug>" data-hash="<sha256(密碼) hex>"></script>
  ```

- hash 這樣算（明碼不進 repo）：`python3 -c "import hashlib;print(hashlib.sha256('密碼'.encode()).hexdigest())"`
- 這行在 page-fill 的替換區之外，重跑 page-fill 不會弄掉。
- **在已上鎖主題新增課程時，新課的 index.html 也要加這行**（照抄同主題其他課的即可）；
  主題有無上鎖看主題頁 `<head>` 有沒有 gate.js。

## 課程頁必備（工程底線）

以下全部已內建在模板＋共用骨架，從 scaffold 起手就不會漏。

兩種課共通：

- `/shared/lesson.css`、`/shared/splitter.js` 引用
- 「下載 .py」入口（學員帶得走）
- 窄螢幕（≤980px）上下疊降級、`prefers-reduced-motion`、`:focus-visible`（都在共用 CSS）
- `lang="zh-Hant"`、有意義的 `<title>`（課名 · AI 互動教室）、meta description
- 影片（選配）：YouTube 非公開 + `youtube-nocookie.com` 嵌入，版型在 page 模板的 `.video-box` 區塊

純瀏覽器課（`assets/templates/page.html`）另有：

- `/shared/lesson.js` 引用（golab 捲動、就緒輪詢）
- 「單獨開啟實驗場 ↗」入口
- 右欄載入狀態提示（`#nb-status`）；左頁第一節在等待時間內讀得完
- `<body data-ready-figures="N">`（就緒門檻＝notebook 圖表數）

外部軌課（`assets/templates/page_ext.html`）另有：

- 右欄常駐 molab 導流面板（`#molab-panel`）：執行步驟＋三個行動按鈕
  （新分頁開 notebook / 登入 molab / 下載 .py）
- header 的「開啟實戰 notebook ↗」入口
- 面板步驟依 scaffold 的 `--gpu` 有無自動二選一（預設純 CPU：寫「免費 CPU 環境即可」、無「選 GPU Server」步驟）

## 禁止：平台系統說明文字

課程頁**不寫**技術腳註對學員解釋平台怎麼運作。反例（曾出現、已移除，不要再寫）：

> 「右欄 Python 由 marimo + Pyodide (WebAssembly) 驅動，完全在你的瀏覽器內執行；
> GPU 軌道於 molab（marimo 官方雲）以你自己的帳號執行，本站不經手任何帳號與資料。
> 灰色＝masked、綠色＝計算 loss，這套色彩語義在左右兩欄與 GPU notebook 中一致。」

判斷準則：**學員做事需要知道的，用自然口吻融入教學文案；學員不需要知道的，不寫。**

- ✅ 可以：「首次載入約 30–60 秒，正好夠你讀完第 1 節」「程式改壞了重新整理就復原」
- ❌ 不要：解釋 Pyodide/WASM/marimo 是什麼、宣告隱私政策式聲明、
  用文字宣告色彩語義（顏色的一致性用設計本身傳達，學員自然感受到）

## 好課程網站的品質清單（建議，非硬性——自由發揮的起點）

- **課卡文案是賣點不是摘要**：一句話讓人想點進去（「把混亂切成秩序」優於「決策樹介紹」）
- **開場即互動**：第一屏就有可以動手的東西，別用三段文字暖場
- **每節都有行動點**：讀完一段就有「到右邊做」的具體任務，讀與做交替
- **數字都是真的**：圖表、範例、準確率全部來自真實執行結果，不畫示意圖唬人
- **挑戰與練習**：給分級挑戰（先做得到 → 有點難 → 開放式），notebook 內**附折疊解答**（模板已有 `mo.accordion` 格）
- **佔位課卡**：規劃中的課用虛線框＋降透明度＋「即將開課」，不可點（版型見 `assets/templates/topic.html` 的 `.card.soon`）
- **色彩即語義**：一個概念一個顏色，左頁、圖表、notebook 全站一致（用設計傳達，不用文字宣告）
- **深連結**：章節有 `#s1` 式錨點，方便討論時指到某一節
- **帶得走**：學員能下載 .py 在自己環境延續（這也是對「本站沒有帳號」的補償設計）

### 外部軌課／LLM 課的教學準則（llm-apps 系列實測）

- **非決定性輸出寫範圍，不寫點估計**：「沒 RAG 矇對 0–2 題、有 RAG 7 題全對」「多數 2–5 秒、偶爾
  10–30 秒」。點估計（「111 個 chunk」「top_k 自己給 5」）下一次跑就不成立，還得回頭改頁面。
  同時讓學員知道「你跑出來的數字會不同，看方向」。
- **行為宣稱要標環境**：模型換了行為就變（tool 參數翻成英文、要不要查工具、遵不遵守 schema）。
  文案寫「實測（nemotron-3.5-lightning）…」，NOTES 記日期與模型，換模型時知道哪些句子要重驗。
- **挑戰附折疊解答**：只給題目不給解答，自學的人卡住就走了。LEVEL 1/2 給完整可貼的程式碼與預期
  輸出；LEVEL 3 給方向＋「怎麼驗證自己做對了」。用 notebook 的 `mo.accordion`（模板已有）。
- **外部軌的 hero 用實測紀錄做可重播互動**：沒有內嵌 Python，但可以把 notebook 的真實 trace／
  回答做成「選問題→播放」的小機器，文案註明「內容是 notebook 的實測紀錄」。比靜態示意圖誠實、
  比 live 打 API 穩定。（若 API 有開 CORS 也可考慮 live 呼叫，但要有失敗時的降級畫面。）
- **等待體驗要設計**：LLM 課一格可能等 5–30 秒。md 先說「這格會等一下、等的時候看什麼」；
  學員互動觸發的呼叫包 try/except → callout（429／5xx 不要變 Traceback）；主線示範格可以直接呼叫。
- **系列課的節奏**：每課開頭一句接上一課（「上一課你手寫了說明書…」）、結尾一句預告下一課；
  壓軸課把前面每一課的零件各用一次並標出「這是第 N 課的…」。課卡文案寫 aha 不寫摘要。
- **工具說明書就是教材**：FastMCP docstring、system prompt 的一句話會改變模型行為（「query 請用
  繁體中文」讓 agent 不再用英文搜中文手冊）——把「改一句話、行為就變」做成課堂上的對照，
  比講原理有效。
- **新手課的深度取捨**：同一系列裡「最新改版」（FastMCP 4 無狀態協定）放在會用之後，
  用側錄／對照表讓學員「看見」差別，不展開規格細節；細節放 notebook 末節「知道有就好」。

## 版型與自由度

- 版面骨架與紙感 token 在 `/shared/lesson.css`／`topic.css`，全站一致維持
  「同一間教室」的體感；**課程專屬的語義色（頁內 `<style>` 覆蓋 `--c1…--cut`）、
  互動設計、章節結構、教學法、文案語氣完全自由**，不必模仿既有課的寫法。
- 模板：課程頁 `assets/templates/page.html`、主題頁 `assets/templates/topic.html`。
  首頁 `content/index.html` 是常設檔案，直接編輯。
