# tasks：rwd-mobile-two-tier

## 1. 早期風險驗證（D 風險條第一項）

- [x] 1.1 用 preview-shots／Playwright 以 390×844 對現況 kv-cache 課截圖，確認 marimo `width="medium"` 內容欄在手機全寬的實際渲染（內距、元件是否溢出），把結論記進本 change 或 NOTES；若發現 marimo 層硬傷，回頭修 design 再繼續

## 2. 共用殼：版面與切換（splitter.js / lesson.css）

- [x] 2.1 `splitter.js` 加窄螢幕視圖管理：注入底部「教學｜實作」切換列、`body[data-view]` 切換、golab 連結窄螢幕改 dispatch 切換事件並發 `lab-shown`；桌機分支不動。驗證：390×844 開任一課見切換列、可來回切換；1280px 寬無切換列且 splitter 拖曳如常
- [x] 2.2 `lesson.css` 窄螢幕重寫：移除上下疊（`main{flex-direction:column}`、`#lab{height:82vh}`），改為 `#lesson`／`#lab` 以 `100dvh` 疊放＋`visibility` 切換、切換列樣式＋`env(safe-area-inset-bottom)`、`.wrap` 手機縮 padding、清 `#lesson` 窄螢幕 min-width 殘留。驗證：390×844 無橫向溢出（`scrollWidth ≤ innerWidth`）、切回教學捲動位置保持
- [x] 2.3 header 窄螢幕收斂（縮 padding／字級／短字，必要時允許兩行）。驗證：390px 截圖上 5 個導覽元素完整可見可點

## 3. 共用殼：lazy load 與兩級制（lesson.js＋標記）

- [x] 3.1 18 堂純瀏覽器課 `index.html`＋模板 `page.html` 的 iframe `src` 機械替換為 `data-src`。驗證：`grep -rL 'data-src' content/*/*/index.html` 對純瀏覽器課零漏網
- [x] 3.2 `lesson.js` 載入決策：≥981px 進頁即升格 `data-src`→`src`；窄螢幕等 `lab-shown`（app 課直接升格；edit 課渲染提示卡「建議用電腦操作」＋「仍要載入」按鈕，按下才升格）；就緒輪詢與 180s 超時從升格起算；窄→寬 resize 單向升格。驗證：手機 viewport 停在教學區時 DevTools network 無 nb 資產請求；切實作區後照常載入至就緒
- [x] 3.3 外部軌：確認 `page_ext.html` 與 10 堂外部軌 `index.html` 引入 `splitter.js`（缺則補）；面板 note 逐課補「molab 編輯器在手機體驗有限、建議以電腦操作」並同步模板。驗證：手機 viewport 開外部軌課，實作 tab 直接見 molab 面板（無提示卡）＋note 文字
- [x] 3.4 `bash scripts/build.sh` 全站重組通過（含防呆與 Pages 檢核），本機起 server 後桌機全站冒煙（`smoke-all.sh`）全綠——確認桌機行為零回歸

## 4. app 課超標圖表回修（D7）

- [x] 4.1 盤點 15 堂 app 課 lesson.py 的 figsize 寬 ≥9 與 `subplots(1, 2)` 全清單（含行號），列入本 change 目錄備查。驗證：`grep -n` 結果與清單一致
- [x] 4.2 逐課回修：1×2 改 2×1 上下堆疊、寬壓 ≤6.5、調字級保桌機可讀；每支動過的 lesson.py 跑 `uv run marimo export html check.html`（CPython 全 cell）＋該課單課 WASM 冒煙。驗證：清單上每課雙層驗證輸出全綠，`grep` 全站 app 課再無 figsize 寬 ≥9 與 `subplots(1, 2)`
- [x] 4.3 動過圖的課以桌機＋390×844 各截一張圖表段落確認可讀性（人工目視）。驗證：截圖存本 change 目錄或臨時目錄過目

## 5. 驗證管線：手機 viewport（D8）

- [x] 5.1 `smoke-all.sh` 加 390×844 全課結構檢查（無橫向溢出、切換列存在、切實作區後內容符合課程型態：app＝iframe 載入、edit＝提示卡、ext＝面板＋note 斷言）＋抽樣全載（app、edit 各一堂走完切 tab→載入→就緒）。驗證：本機跑 `smoke-all.sh --build` 全綠；故意把一課弄出橫向溢出可被抓到後還原
- [x] 5.2 單課 smoke 模板 `smoke-test.mjs`／`smoke-test-ext.mjs` 加手機 viewport 檢查（結構＋該課全載）。驗證：以既有課實跑新模板通過
- [x] 5.3 `preview-shots.mjs` 加 viewport 參數（如 `--vp 390x844`）。驗證：同一頁桌機與手機兩張截圖成功產出

## 6. make-lesson skill 回寫

- [x] 6.1 `references/site.md`：RWD 頁面規範（980 斷點、底部切換列、lazy load、兩級制、外部軌 note）、新課圖表鐵律（figsize 寬 ≤6.5、禁 1×2 並排 subplot）、文案禁桌機假設（「拖動分隔線」等）；改掉舊「≤980 上下疊降級」描述。驗證：文件內無過時描述殘留
- [x] 6.2 `references/engineering.md`：手機驗證步驟（viewport、指令、通過標準）。驗證：照文件指令可從零跑通一次手機冒煙
- [x] 6.3 模板（`page.html`、`page_ext.html`）與 `new-lesson.sh` 同步新結構（data-src、ext 頁 script 引入、note 佔位）。驗證：`new-lesson.sh` scaffold 一堂丟棄用測試課，直接通過 5.2 的新單課冒煙後刪除
- [x] 6.4 SKILL.md 若流程步驟有變（驗證清單多手機一項）同步更新。驗證：SKILL.md 驗證章節與 engineering.md 一致

## 7. 上線與收尾

- [x] 7.1 `npx wrangler pages deploy dist --project-name=agentclass` 部署，跑 `smoke-all.sh --base https://agentclass.pages.dev` 線上冒煙全綠
- [x] 7.2 `git add -A && git commit && git push`（外部軌 molab 直讀 GitHub main，push 為上線的一部分）。驗證：remote main 含本次 commit
- [x] 7.3 openspec 收尾：`openspec validate` 通過後 sync specs、archive 本 change（連同待歸檔的 app-mode-lessons 一併確認是否 archive）。驗證：`openspec list` 無殘留未歸檔完成項
