# Tasks

- [x] `content/shared/gate.js`：覆蓋層密碼閘（SHA-256、localStorage、同群組一次解鎖、不動 body 可見性）
- [x] `content/llm-apps/index.html`：主線 01→06 在上、補充 A→D 在後；`<head>` 掛 gate
- [x] llm-apps 10 堂課程頁 `<head>` 掛 gate（page-fill 替換區之外，重跑不會弄掉）
- [x] `content/ml-basics/index.html`：排序註解改為課程順序（卡片原本就照順序）
- [x] spec：排序句改寫＋新增「主題密碼閘（可選）」requirement
- [x] make-lesson skill `site.md`：wiring 排序規則改寫、新增「主題密碼閘」章節
- [x] `content/llm-apps/NOTES.md`：記錄本主題已上鎖＋新課要照抄 gate 行
- [x] `bash scripts/build.sh` ＋ 全站冒煙 ＋ gate 行為 Playwright 驗證（錯誤密碼擋、正確密碼過、解鎖後跨課程頁通行）
