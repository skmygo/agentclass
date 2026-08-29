# 模擬課改 app 模式：右欄隱藏程式碼，只留互動

## Why

純瀏覽器課原本一律以 marimo edit 模式匯出（`build.sh` 寫死 `--mode edit`），
右欄把 20–34 格 Python 原始碼全攤在學員面前。這對**真的在教 Python 套件用法**的課
（ml-basics 用 scikit-learn 訓練模型）是教材本體；但對**用 numpy/matplotlib 做教學模擬**的課
（local-llm 8 課、genai-intro 7 課——右欄沒有真的大模型，是十六維玩具注意力層、
計費模擬、取樣模擬）程式碼不是教學標的：學員要學的是「拉滑桿看 KV cache 怎麼長大」，
不是「這個 for 迴圈怎麼寫」。攤開的模擬程式碼讓畫面變成一份看不懂的原始碼，
還會誤導學員以為右邊在跑真的推論。

工程手段（export 模式）原本反向決定了教學呈現，且全站只有一個選擇。

## What Changes

- `build.sh` 新增**互動模式**開關：課程目錄或主題目錄放 `lesson-mode` 檔（`app` | `edit`），
  課程層優先、主題層次之、**預設 `edit`（既有行為不變）**；`app` 走
  `marimo export html-wasm --mode run`，程式碼與編輯器 UI 不出現，互動元件與輸出照常。
  兩項一致性防呆：app 課的頁面必須宣告 `data-nb-mode="app"`，反之亦然。
- `/shared/lesson.js` 就緒文案依 `<body data-nb-mode="app">` 切換（app 模式不講「每一格都能改」）。
- 教學內容連動（15 課）：開場白、「你的實驗區」自由編碼區、挑戰題與折疊解答裡的
  程式碼指示，全部改寫為互動元件（滑桿／下拉／輸入框）可完成的操作，數字重新實算。
- spec 的「學員可改可跑且互相隔離」放寬為兩種互動模式，並訂出選擇準則。
- make-lesson skill 寫入判準與 `--app` scaffold 旗標。

## Impact

- `scripts/build.sh`、`content/shared/lesson.js`（改共用＝改全站，已全站冒煙）
- app 模式課 15 堂：`content/local-llm/*`（8）、`content/genai-intro/*`（7）
- edit 模式維持不變：`content/ml-basics/*`（3，真的在跑 scikit-learn）；外部軌課不受影響
- `.claude/skills/make-lesson/`（SKILL.md、references、page.html 模板、new-lesson.sh）
- `openspec/specs/interactive-lesson/spec.md`
