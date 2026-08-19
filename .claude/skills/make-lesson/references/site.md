# 網站結構與頁面規範

## 資訊架構

**檔案一棵樹（content/），網址兩層扁平**——課程實體放在主題目錄下，
但課程網址永遠在根層：課換主題、主題改名，已分享出去的課程連結都不會斷。

```
content/index.html                →  /              首頁（主題列表）
content/<topic>/index.html        →  /<topic>/      主題頁（課程列表）
content/<topic>/<lesson-id>/      →  /<lesson-id>/  課程（index.html 教學頁 + lesson.py + smoke-test.mjs + NOTES.md）
                                     /<lesson-id>/nb/   marimo WASM notebook（build.sh 產）
content/shared/                   →  /shared/       全站共用（lesson.css/lesson.js/topic.css/splitter.js + WASM assets）
```

- **course id 全站唯一**（網址在根層），scaffold 與 build.sh 都會擋重複。
- 主題與課程 slug 用簡短英文（如 `ml-basics`、`clustering`）。
- build.sh **自動發現** `content/*/*/lesson.py`——新課不用改 build.sh。

## 共用骨架（重要：頁面只寫內容）

- 課程頁版面（CSS）與行為（golab 捲動、就緒輪詢、GPU 分頁）都在
  `/shared/lesson.css` 與 `/shared/lesson.js`，**全站一份**；課程頁只放內容、
  課程語義色覆蓋、hero 專屬樣式與互動 JS。
- 就緒門檻用 `<body data-ready-figures="N">` 宣告（N = notebook 圖表數，至少 1）。
- 首頁與主題頁共用 `/shared/topic.css`。
- **改共用檔＝改全站**，動之前想清楚；課程專屬需求寫在該課頁面的 `<style>`/inline script。

## 導覽鏈（每一環都要能點）

首頁 → 主題頁 → 課程頁 →（下一課 → …）→ 回主題 → 品牌回首頁

新增一堂課的 wiring 清單（scaffold 印的待辦就是這份）：

1. 課程卡插進主題頁的 `.lessons` **最上面**（越新越上；沒有該主題就先建主題頁、
   主題卡插首頁最上面）
2. 課程頁 header：品牌連結（`href="/"`）＋「‹ 回主題」連結（`href="/<topic>/"`）
3. 課末放導覽區：**下一課**（同主題內有的話）與**回主題**
4. **回頭補鏈**：新課上線後，同主題的前一課要補「下一課 →」指向新課
5. 主題卡上的課程數字（`TOPIC · N 門課`）同步更新

## 課程頁必備（工程底線）

以下全部已內建在 `assets/templates/page.html`＋共用骨架，從 scaffold 起手就不會漏：

- `/shared/lesson.css`、`/shared/lesson.js`、`/shared/splitter.js` 三個引用
- 「下載 .py」與「單獨開啟實驗場 ↗」入口
- 右欄載入狀態提示（`#nb-status`）；左頁第一節在等待時間內讀得完
- `<body data-ready-figures="N">`（就緒門檻＝notebook 圖表數）
- 窄螢幕（≤980px）上下疊降級、`prefers-reduced-motion`、`:focus-visible`（都在共用 CSS）
- `lang="zh-Hant"`、有意義的 `<title>`（課名 · AI 互動教室）、meta description
- 影片（選配）：YouTube 非公開 + `youtube-nocookie.com` 嵌入，版型在 page 模板的 `.video-box` 區塊

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
- **挑戰與練習**：給分級挑戰（先做得到 → 有點難 → 開放式），可考慮 notebook 內折疊解答
- **佔位課卡**：規劃中的課用虛線框＋降透明度＋「即將開課」，不可點（版型見 `assets/templates/topic.html` 的 `.card.soon`）
- **色彩即語義**：一個概念一個顏色，左頁、圖表、notebook 全站一致（用設計傳達，不用文字宣告）
- **深連結**：章節有 `#s1` 式錨點，方便討論時指到某一節
- **帶得走**：學員能下載 .py 在自己環境延續（這也是對「本站沒有帳號」的補償設計）

## 版型與自由度

- 版面骨架與紙感 token 在 `/shared/lesson.css`／`topic.css`，全站一致維持
  「同一間教室」的體感；**課程專屬的語義色（頁內 `<style>` 覆蓋 `--c1…--cut`）、
  互動設計、章節結構、教學法、文案語氣完全自由**，不必模仿既有課的寫法。
- 模板：課程頁 `assets/templates/page.html`、主題頁 `assets/templates/topic.html`。
  首頁 `content/index.html` 是常設檔案，直接編輯。
