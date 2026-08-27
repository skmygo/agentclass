# 就緒訊號解耦：無圖課成立（data-ready-selector）

## Why

純瀏覽器課的右欄就緒偵測與冒煙測試都靠 iframe 內 img/canvas 計數——工程偵測手段
反向禁止了「沒有圖表的課」這一整類課程型態（純文字推理課、純互動元件課的就緒訊號會失效）。
這是技術外溢成教學形式：偵測機制是沙盒的牆，不該決定課能不能沒有圖。

## What Changes

- `/shared/lesson.js` 就緒偵測新增替代訊號：`<body data-ready-selector="<css>">` 宣告後，
  改以「iframe 內出現符合元素」判定就緒；未宣告時維持原本 `data-ready-figures` 圖表計數，
  **既有課程行為完全不變**。
- 冒煙測試模板（`smoke-test.mjs`）新增 `READY_SELECTOR` 常數，與頁面宣告同一訊號；
  未設定時維持 `MIN_FIGURES` 圖表計數。
- spec 新增「載入就緒提示」requirement：明文規定就緒機制不得強制課程內容包含特定型態輸出。
- make-lesson skill（SKILL.md／site.md／engineering.md／page.html 模板）同步：
  「每課至少一張圖」由工程強制降為教學建議。

## Impact

- `content/shared/lesson.js`（改共用＝改全站；預設路徑不變，需全站冒煙）
- `.claude/skills/make-lesson/assets/templates/smoke-test.mjs`、`page.html`
- `openspec/specs/interactive-lesson/spec.md`、make-lesson references
