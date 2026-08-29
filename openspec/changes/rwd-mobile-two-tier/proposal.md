# 全站 RWD 兩級制：手機/平板可讀可玩，桌機行為不變

## Why

課程頁的雙欄對照本質上是桌面版面；現有的窄螢幕降級（≤980px 上下疊、82vh iframe）
是「做了但從未被任何自動驗證碰過」的狀態——iframe 夾在長頁中間有捲動陷阱、
header 不換行、WASM 進頁就拉幾十 MB、900–960px 寬的 matplotlib 點陣圖縮到不可讀。
但 app 模式課（genai-intro、local-llm 的教學模擬）的受眾恰恰最可能拿手機點連結進來：
右欄只是滑桿＋下拉＋圖表，完全有條件在手機上完整可玩。2026-08-06 的舊決策
「不做手機版最佳化」在 app 模式課出現後已不成立。

## What Changes

- **兩級制手機體驗**：app 模式課＝手機上完整可互動（正式支援目標）；
  edit 模式課＝教學頁完整可讀＋「動手部分建議用電腦」提示卡＋「仍要載入」按鈕（不擋路、不保證好用）。
- **980px 斷點一條線**：≥981px 雙欄＋splitter 完全不變（桌機零改動）；
  ≤980px 以**底部固定「教學｜實作」切換列**取代現有上下疊降級（含 iOS safe-area 處理），預設落在教學。
- **WASM lazy load（僅 ≤980px）**：iframe 不再進頁就載。app 課首次切到實作 tab 即載入；
  edit 課按了提示卡的「仍要載入」才載入；≥981px 維持進頁即載。
- 教學文內「開始實作」類連結在 ≤980px 改為切 tab＋觸發載入（取代 scrollIntoView）。
- 外部軌課實作 tab 照常顯示 molab 導流面板（不加提示卡），面板 note 補一行「molab 編輯器在手機體驗有限」。
- 共用殼修正：header 窄螢幕收斂、`.wrap` 手機縮 padding、清掉 `#lesson` 窄螢幕 min-width 殘留。
- **app 課超標圖表回修**：figsize 寬 ≥9 的圖與 1×2 並排 subplot 改為寬 ≤6.5／上下疊＋調字級；
  其餘靠捏合縮放。edit 課的圖不動。動過的 lesson.py 重跑雙層驗證。
- **驗證納入手機 viewport（390×844）**：smoke 流程加「課程頁在手機 viewport」檢查
  （現在只測 notebook 本體），preview-shots 支援手機尺寸截圖。
- **make-lesson skill 全套回寫**：site.md（RWD 規範＋新課圖表鐵律「figsize 寬 ≤6.5、
  禁 1×2 並排 subplot」＋文案不得有桌機假設）、engineering.md（手機驗證步驟）、
  page.html / page_ext.html 模板內建 tab 結構、驗證腳本模板加手機 viewport。
- spec 現有條文的「桌面寬度」隱含假設改寫，補窄螢幕 Scenario。

## Capabilities

### New Capabilities

（無）

### Modified Capabilities

- `interactive-lesson`：
  - 「左右對照版面」擴充為「≥981px 雙欄；≤980px 底部 tab 切換」，
    現有僅存在於 CSS、未入 spec 的上下疊降級被 tab 制取代並正式入 spec。
  - 載入行為新增條件分支：≤980px lazy load（app 課切 tab 即載；edit 課提示卡確認後載）。
  - 兩級制手機體驗成為 requirement（app 課手機完整可互動；edit 課可讀＋提示）。
  - app 課圖表新增可讀性約束（figsize 寬 ≤6.5、禁 1×2 並排 subplot）。
  - 發布前驗證新增手機 viewport（390×844）課程頁檢查。
  - 既有 Scenario 中「桌面寬度」措辭改為明示斷點條件。

## Impact

- `content/shared/`：lesson.css、lesson.js、splitter.js（改共用＝改全站，需全站冒煙）
- `content/genai-intro/*`、`content/local-llm/*` 中超標圖表所在的 lesson.py（各課重跑
  CPython export＋WASM 冒煙雙層驗證）
- 外部軌課頁（llm-apps 10 堂 `index.html`＋`page_ext.html` 模板）：note 一行；
  tab 列由 splitter.js 注入（外部軌頁已引 splitter.js，毋須補 script）
- `.claude/skills/make-lesson/`：SKILL.md（如需）、references/site.md、references/engineering.md、
  assets/templates/（page.html、page_ext.html、smoke-test.mjs、smoke-test-ext.mjs）、
  scripts/preview-shots.mjs、scripts/smoke-all.sh
- 部署：一次 deploy 全站；上線後線上冒煙＋git push
