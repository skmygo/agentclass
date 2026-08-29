# design：rwd-mobile-two-tier

## Context

動機見 proposal.md；行為契約見本 change 的 specs delta。現況關鍵事實：

- 版面骨架全在 `/shared/`：`lesson.css`（flex 雙欄、`#lesson` min-width 380px、≤980px 上下疊＋`#lab` 82vh）、`splitter.js`（Pointer Events 拖曳、≤980px 自我隱藏、注入自己的 style）、`lesson.js`（就緒輪詢、180s 超時、golab 連結窄螢幕 scrollIntoView）。
- 18 堂純瀏覽器課的 `index.html` 都是靜態 `<iframe id="nb-frame" src="nb/index.html">`——進頁即載。
- `page_ext.html`（外部軌模板）**不引 `lesson.js`**；外部軌課 10 堂（llm-apps 全部）。
- app 課判別已有現成訊號：`<body data-nb-mode="app">`（15 堂）；純瀏覽器課無此屬性＝edit 模式。
- 圖表全站為 matplotlib 靜態 PNG（預設 100dpi），figsize 寬 ≥9 者約 11–12 處、1×2 subplot 若干，集中在 app 課。
- 驗證腳本（smoke-test 模板、smoke-all、preview-shots）皆單一桌機 viewport，且只測 notebook 本體不測課程頁窄螢幕。

## Goals / Non-Goals

**Goals:**

- 桌機（≥981px）行為 bit-for-bit 不變（splitter、比例記憶、進頁即載全部照舊）。
- 窄螢幕改動全部收在 `/shared/` 與課程頁的機械性標記調整，不動 `page_content.py` 內容正本。
- 驗證管線從此強制手機 viewport 檢查（新課建課即擋）。

**Non-Goals:**

- 不做平板第三種版面（純 980px 斷點制）。
- 不最佳化 edit 課在手機上的編輯體驗（提示卡＋仍要載入即為完成態）。
- 不回修 figsize 寬 6.5–9 之間的既有圖（靠瀏覽器縮放）。
- 不做 PWA／離線／無 JS 降級。

## Decisions

### D1：tab 切換列由 `splitter.js` 注入，不改 28 個 index.html 的骨架

`splitter.js` 已經是「版面管理者」（注入自己的 style、擁有 980px matchMedia），把窄螢幕的底部切換列與 `body[data-view="lesson|lab"]` 切換邏輯放進去，所有課程頁（含外部軌，前提見 D6）零標記改動即得新版面。備選：把切換列寫進模板＋sed 28 個檔——被否決，違反「骨架在 /shared/」的站規，且未來每課都要多維護一段重複標記。

### D2：隱藏的 pane 用 `visibility:hidden` 疊放，不用 `display:none`

窄螢幕下 `#lesson`／`#lab` 為同尺寸疊放的滿版捲動容器（body 維持 overflow hidden，高度用 `100dvh` 對抗 iOS 網址列），切換只翻 `visibility`＋`pointer-events`。理由：`display:none` 會摧毀 layout——教學區捲動位置歸零、iframe 內 marimo 可能重排；`visibility` 保捲動狀態、保 WASM 執行狀態，正好滿足 spec「切回教學時捲動狀態保持」。切換列固定於底部、`padding-bottom: env(safe-area-inset-bottom)`。

### D3：lazy load 靠「iframe 出廠不帶 src」＋共用 JS 擇時升格

markup 的 `src` 一存在瀏覽器就開載，JS 事後攔不住，所以把 18 堂課＋模板的 iframe 改為 `data-src`（一次性 sed，機械替換）。載入時機由 `lesson.js` 決定：

- 進頁時 `matchMedia("(min-width:981px)")` 成立 → 立即把 `data-src` 升格為 `src`（桌機行為不變）。
- 窄螢幕 → 等 `splitter.js` 發出的 `lab-shown` 事件：`data-nb-mode="app"` → 直接升格；edit 課 → 先渲染提示卡，按「仍要載入」才升格。
- 就緒輪詢與 180s 超時計時 SHALL 從升格那一刻起算（不然學員讀教學 3 分鐘後切過來就直接看到「載入比平常久」）。
- 寬→窄 resize：已載入者維持已載入；窄→寬（平板轉橫）：若未載入立即升格。單向升格、不解除安裝。

代價：無 JS 時桌機也不載 notebook——本站本來就整站依賴 JS（marimo 即 JS），接受。

### D4：職責分工——`splitter.js` 管「看哪個」，`lesson.js` 管「載不載」

外部軌課有 tab 需求但無 iframe、無就緒輪詢；純瀏覽器課兩者皆有。故：視圖切換（切換列、`data-view`、golab 連結窄螢幕改切 view）在 `splitter.js`；載入決策（D3）與提示卡在 `lesson.js`，兩者以 DOM 事件解耦。golab 連結現行的 scrollIntoView 分支改為 dispatch 切換事件。

### D5：edit 課提示卡是 `#lab` 內的一層，不是覆蓋全頁

提示卡由 `lesson.js` 在窄螢幕首次進實作區時渲染進 `#nb-status` 區（沿用既有狀態區塊），文案短句：「本課的動手部分是直接改程式碼，建議用電腦操作」＋按鈕「我知道，仍要載入」。按下即走 D3 升格流程，狀態區轉為現行載入中提示。桌機永不出現提示卡。

### D6：外部軌頁補引 `splitter.js` 的依賴確認

D1 的前提是外部軌頁也載入 `splitter.js`——實作第一步驗證 `page_ext.html` 與 10 堂現役外部軌 `index.html` 是否已引（實測全數已引，毋須補）。molab 面板的「手機體驗有限」note 是 `page_content.py` 層的文案（外部軌課的面板文案正本在各課 `index.html`／模板），逐課補一行並同步模板。

### D7：圖表回修只動 app 課的超標圖，逐課重驗

盤點 15 堂 app 課 lesson.py 中 figsize 寬 ≥9 與 `subplots(1, 2)`：1×2 改 2×1 上下堆疊、寬壓到 ≤6.5、必要時調 fontsize/labelsize 維持桌機可讀。**每支動過的 lesson.py 走該課完整雙層驗證**（CPython export＋單課 WASM 冒煙）。桌機右欄約 500–800px，6.5×100dpi=650px 的圖在兩端都成立。edit 課（ml-basics 等）即使有超標圖也不動——不在手機支援目標內。

### D8：手機冒煙＝全站結構檢查＋抽樣全載

WASM cell 執行結果與 viewport 無關（同一 runtime），手機新增的風險在版面與載入流程。故 390×844 冒煙分兩層：

- **全課結構檢查**（快）：無橫向溢出（`scrollWidth ≤ innerWidth`）、切換列存在、切到實作區後內容符合課程型態（app＝iframe 開始載；edit＝提示卡；ext＝molab 面板）。
- **抽樣全載**（慢）：每次全站冒煙抽 app 課與 edit 課各一堂在手機 viewport 走完「切 tab → 載入 → 就緒」全程，覆蓋 lazy load 端到端。

單課 smoke-test 模板則對「該課」同時跑桌機（現行）＋手機（結構＋全載）兩個 viewport——新課逐課全檢，存量靠全站抽樣。`preview-shots.mjs` 加 viewport 參數（如 `--vp 390x844`）供人工審圖。

### D9：header 窄螢幕收斂採「縮」不採「藏」

52px header 在 390px 塞 5 個元素：縮 padding／字級、工具連結只留 icon 或短字，允許 wrap 成兩行為底線；不做漢堡選單（多一層互動不值得）。實作後以 390px 截圖驗收「導覽元素完整可及」。

## Risks / Trade-offs

- [marimo `width="medium"` 的內容欄在 375–390px 的實際渲染未經實測，可能有內距浪費或元件溢出] → 實作早期先拿 kv-cache 一堂在手機 viewport 截圖驗證，發現 marimo 層問題再評估是否需在 nb 端 CSS 微調（風險隔離在單一驗證步驟，不影響整體方案）。
- [`visibility` 疊放下 iframe 在部分行動瀏覽器仍可能觸發重排或計時器節流] → 抽樣全載冒煙會抓到；退路是切換時不動 iframe、只翻 `#lesson`。
- [18 檔 sed `src`→`data-src` 屬機械修改但面廣] → build 後全站冒煙（桌機層）本來就會逐課驗載入，改壞即現形。
- [外部軌課 index.html 的面板 note 逐課手改，易漏] → smoke 的 ext 結構檢查加「note 文字存在」斷言。
- [舊分享連結的使用者在手機上習慣了上下疊] → 新版面是嚴格升級（舊版有捲動陷阱），無需相容措施。
- [1×2 改 2×1 會讓部分對照圖在桌機變高、右欄需多捲動] → 屬可接受代價；逐課重驗時人工看桌機截圖把關。

## Migration Plan

1. 共用殼（lesson.css / splitter.js / lesson.js）＋ iframe data-src sed ＋ 外部軌頁補引 script → `build.sh` → 本機全站冒煙（桌機＋手機雙 viewport）。
2. app 課超標圖逐課回修＋逐課雙層驗證。
3. make-lesson skill 回寫（模板、site.md、engineering.md、驗證腳本）。
4. 一次 deploy 全站 → 線上冒煙 → `git push`（外部軌 molab 直讀 GitHub main）。
5. 回滾策略：純靜態站，`git revert` 後重跑 build＋deploy 即回前一版。

## Open Questions

（無——手機 viewport 下 marimo 內容欄的實測結果只影響「是否需要 nb 端微調」的實作細節，不影響方案與任務拆分。）
