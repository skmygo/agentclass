# Spike 踩坑紀錄 — decision-tree（2026-08-06）

> 目的：這份是 spike 的實測結論，未來把管線固化成 skill 時的第一手輸入。

## 管線總結（已走通）

```
uv init + uv add marimo scikit-learn matplotlib pandas numpy   （marimo 0.23.16）
→ 寫 lesson.py（marimo 純 .py 格式）
→ 第一層驗證：uv run marimo export html lesson.py -o check.html   （CPython headless 全 cell 執行）
→ uv run marimo export html-wasm lesson.py -o nb --mode edit
→ sed 補 auto_instantiate（見坑 1）
→ 第二層驗證：headless Playwright 開 WASM 版（smoke-test.mjs）
→ scripts/build.sh 組裝 dist/（教學頁 + nb/ + lesson.py + 根頁）
→ npx wrangler pages deploy dist --project-name=agentclass   （direct upload，713 檔 4.5 秒）
```

成品：https://agentclass.pages.dev/decision-tree/

## 坑（按嚴重度排序）

1. **marimo 0.23.16 的 `export html-wasm` 把 `auto_instantiate: false` 烙進產物**
   —— 症狀：頁面渲染正常但所有 Python cell 停在「待執行」，永遠不自動跑。
   專案 `pyproject.toml` 設 `[tool.marimo.runtime] auto_instantiate = true` 後
   `marimo config show` 有吃到，但 **export 不理會專案層設定**（疑似只讀 user config）。
   解法：匯出後 `sed -i 's/"auto_instantiate": false/"auto_instantiate": true/' nb/index.html`
   （已進 build.sh）。skill 化時每次升版 marimo 要重驗這行為。

2. **本機 CPython 跑通 ≠ WASM 跑通，雙層驗證缺一不可**
   —— 本次雖然沒踩到套件不相容（sklearn/matplotlib/pandas 在 Pyodide 都有 wheel），
   但坑 1 正是「只有瀏覽器實測才會發現」的類型。冒煙判準：圖表 `<img>/<canvas>` 數量
   ≥ 預期、頁面文字無 Traceback、console 無 error。

3. **Pyodide 載入時間實測**：本機 ~23s、Cloudflare Pages ~25s（含下載
   sklearn/matplotlib/pandas wheels）。教學頁必須有載入狀態提示；本次做法＝右欄頂部
   狀態列輪詢 iframe 內 `img/canvas` 數量，就緒後變綠（同源 iframe 才可行）。

4. **matplotlib 在 Pyodide 沒有 CJK 字型** —— 圖內中文會變豆腐。
   規範：圖表標籤/圖例一律英文，中文解說走 marimo markdown 與左側教學頁。

5. **Claude-in-Chrome 不能拿來測本機 port** —— 使用者的 Chrome 可能在別台機器
   （本次 127.0.0.1 與開發機的內網 IP:8787 都開不到，外網正常）。
   本機驗證一律用主機上的 headless Playwright。

6. Playwright 細節：
   - `text=中文標題` 會撈到隱藏的 `<title>` → 等 `h1:has-text(...)` + `state:"visible"`
   - `waitForFunction(fn, arg, options)` —— options 是第三參數，放錯位置逾時會默默變 30s
   - marimo 在內部容器捲動：驗證捲動要量目標元素 `getBoundingClientRect()`，
     不是 `contentWindow.scrollY`；`scrollIntoView()` 本身有效

7. headless chromium 沒 emoji 字型，截圖裡 emoji 是豆腐 —— 假警報，真瀏覽器正常。

## 可沿用的設計事實

- **左右同源 iframe 整合**：左頁按鈕以 notebook md 標題內的 `1️⃣`~`7️⃣` emoji 當錨點，
  `contentDocument` 找 heading → `scrollIntoView()`，教學段落 ↔ notebook cell 一一對應。
- **「下載 .py」**＝把 `lesson.py` 原檔 cp 進 dist 同層，`<a download>` 即可。
- **調色盤即語義**：左頁與 notebook 圖表共用同三色（#4C72B0/#DD8452/#55A868 = 三品種、
  #C44E52 = 切分線），學員在兩側看到的顏色永遠同義。
- wrangler direct upload 不需 GitHub repo，適合 spike；正式化可再評估 push-to-deploy。
- Pages 單檔上限 25MB：marimo WASM 產物最大單檔 4.7MB，安全。
- `marimo export html-wasm` 有 `--include-cloudflare` 旗標（產 wrangler 設定），本次未用。

## 未做 / 留給 skill 化的事

- 手機版只有基本上下疊降級；雙欄對照本質是桌面場景
- 左頁「深連結到某節」（`#s4` 錨點存在但未在 UI 曝光）
- ~~smoke-test.mjs 的 playwright 依賴是借別的專案的安裝，skill 化時要自帶~~
  （2026-08-19 已完成：repo 根目錄 package.json 自帶 playwright devDependency）
- 多課 index 目前手寫；課多了應由 build.sh 從 lessons/*/meta 生成
- 練習題沒有解答頁；可考慮 notebook 內折疊解答 cell 的慣例
