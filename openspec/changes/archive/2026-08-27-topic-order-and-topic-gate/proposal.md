# 主題頁改課程順序排列 ＋ 主題密碼閘（可選）

## Why

- 主題頁原規則「越新越上」是從首頁沿用的，但課程是有順序的教材（llm-apps 六堂主線一條管線、
  ml-basics 三塊基石）：學員到主題頁是要「照順序上」，最新的課排最上反而把第 1 課壓到最底。
- 部分主題（先是 llm-apps）只想給知道密碼的學員看，但整站是公開 repo ＋ 純靜態託管，
  不要帳號、不要後端——需要的是「不主動曝光」的輕量閘，不是安全防護。

## What Changes

- **排序**：首頁主題卡維持越新越上；主題頁課程卡改為課程順序（第 1 課在最上），
  補充系列獨立成區、排在主線之後照系列順序。llm-apps 主題頁重排；ml-basics 原本就照順序，僅更新註解。
- **密碼閘**：新增 `/shared/gate.js`——不透明覆蓋層＋SHA-256 比對＋localStorage 記住解鎖，
  同主題輸入一次全通。要上鎖的主題在主題頁與每堂課程頁 `<head>` 各掛一行 `<script data-gate data-hash>`。
  內容照常於底下載入（notebook 暖機、冒煙測試可見性檢查不受影響）；devtools 可繞過屬預期。
- llm-apps 全系列（主題頁＋10 課）上鎖。
- 規範回寫：spec「網站導覽結構」排序句改寫、新增「主題密碼閘（可選）」requirement；
  make-lesson skill `site.md` 的 wiring 清單與新章節「主題密碼閘」。

## Impact

- 改 `content/shared/`（新增 gate.js，未掛 script 的頁面零影響）
- `content/llm-apps/index.html` 重排＋上鎖；該主題 10 堂課 `<head>` 各加一行
- `openspec/specs/interactive-lesson/spec.md`、make-lesson skill `site.md`、llm-apps `NOTES.md`
- 不動 build.sh、page-fill、模板；密碼明碼不進 repo（只放 hash）
