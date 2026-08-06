# Design — add-sft-lesson

## Context

動機見 proposal.md。既有事實：第一課管線已走通（`lessons/decision-tree/NOTES.md` 有完整踩坑）；Pyodide 無 torch/transformers，真實 SFT 不可能在瀏覽器內跑；使用者已確認 molab 登入後可選 Server（RTX Pro 6000）。主 spec `interactive-lesson` 要求課程純靜態、無帳號、教學與程式一致、雙層驗證。

## Goals / Non-Goals

**Goals**

- 學員不開 GPU 也能在瀏覽器內真正理解 SFT 的機制（不是只看圖說故事）
- GPU 軌道一鍵導流到 molab，步驟清楚到第一次用 molab 的學員能自己完成
- 雙軌架構定型，成為日後 GPU 課的模板

**Non-Goals**

- 不自架多人 GPU notebook 服務（與純靜態初衷衝突；molab 已解決）
- 不教 RLHF/DPO/全參數微調（只點名它們與 SFT 的關係，留給後續課）
- 不處理 molab 的計費/額度問題（屬學員自己的帳號體系；頁面誠實註明）
- 不做訓練進度回傳本站（本站不經手學員執行狀態）

## Decisions

1. **雙軌切分原則：概念歸瀏覽器、算力歸 molab**
   - 軌道 A（WASM）教機制：資料格式 → chat template → tokenization → loss masking → LoRA 參數帳 → numpy 迷你 LM 的「預訓練 vs SFT 後」行為對比。全部 numpy/純 Python 可跑，維持既有 spec 的瀏覽器內可跑要求。
   - 軌道 B（GPU）給真實感：同一套概念在真模型上再走一遍，學員親眼看 loss 下降與生成行為改變。
   - 替代方案「整課只做 molab」被否決：違反主 spec 的零帳號核心教學要求，且 molab 掛掉課就死。

2. **軌道 A 的招牌實驗：numpy 迷你字元級語言模型**
   - 內建一個預先在通用小語料「預訓練」好的迷你模型（權重直接寫在 notebook 內或即時快速訓練），學員按下「SFT」在指令格式小資料集上微調幾百步，前後對比生成結果——在瀏覽器裡體驗「同一個模型、餵格式化資料後行為改變」這件 SFT 最核心的事。
   - 規模以瀏覽器可承受為準（參數量 ~1e4–1e5 級、訓練秒級~十秒級）；若 apply 時實測太慢，降級為「權重烙死 + 只跑推論對比」，SFT 過程改為預錄 loss 曲線資料重播。此降級不影響 spec 符合性。

3. **軌道 B notebook（`sft_gpu.py`）技術棧：transformers + peft、手寫訓練迴圈**
   - 不用 TRL 的 SFTTrainer——它把 loss masking 等教學重點全藏起來；手寫迴圈每一步都對應軌道 A 教過的概念（collate、masking、LoRA 注入、AdamW step）。
   - 基底模型選 ~0.5B 的 base（非 instruct）小模型（預設 `Qwen/Qwen2.5-0.5B`，apply 時可視 molab 下載速度調整），SFT 後從「續寫」變「聽指令」，對比最戲劇化。
   - 資料集：課內自帶 100–300 筆繁中迷你指令資料（notebook 內生成或內嵌），單卡數分鐘可完成，學員等得起。

4. **molab 整合機制：外開新分頁 + 連結回填，不 iframe**
   - molab 有登入流程且極可能設 X-Frame-Options，iframe 不可行也不該試。
   - 學員流程：課頁按鈕（新分頁）→ molab 登入 → fork 成自己的副本 → Server 選 GPU（RTX Pro 6000）→ Run。左頁附截圖式步驟說明（文字為主）。
   - molab 無公開 API 可程式化發布 → **notebook 由使用者登入上傳一次、把分享連結回填**，這是 tasks 裡的硬節點。連結先以佔位符進版，回填後重新部署。
   - 後備路徑：「下載 sft_gpu.py」永遠可用（spec 的外部服務不可用 scenario）。

5. **本機驗證策略（軌道 B）**
   - apply 時先探測本機 GPU（nvidia-smi）；有則全量驗證 `sft_gpu.py`，無則以縮小規模（更小模型/更少步數）在 CPU 走通程式路徑，並在 NOTES 標注「全量驗證於 molab 完成」。
   - 軌道 A 沿用既有雙層驗證（CPython headless + WASM Playwright 冒煙），smoke 判準沿用第一課腳本模式。

6. **頁殼沿用第一課，新增「GPU 軌道」區塊元件**
   - 左頁最後一節為 GPU 軌道（入口按鈕 + 步驟 + 誠實的額度/計費註記）；右欄仍是軌道 A 的 WASM notebook。頂列新增「GPU 版 notebook ↗」入口。
   - 樣式沿用第一課的設計 token（色板、字級、按鈕語彙），視覺上是同一套系統的第二課。

7. **（延伸）右欄內嵌 molab 分頁——「外開登入、回站內跑」**
   - 實測 molab notebook 頁未送 `X-Frame-Options`/`frame-ancestors`，header 層允許 iframe。
   - 登入必然外開（OAuth 拒絕 iframe）；登入後 iframe 內的 molab session 屬第三方
     cookie——Chrome 預設可用，Safari/無痕會擋。因此定位為**漸進增強**：右欄 tab 列
     〔互動實驗｜molab GPU〕，molab 分頁附登入指引＋重新載入＋外開後備；成功＝站內
     直接編輯 GPU notebook，失敗＝退回既有外開流程，價值不歸零。
   - 用**兩個 iframe 切換顯示**而非換 src：保住 WASM notebook 的學員狀態；molab
     iframe 首次切換才載入（不逼所有學員吃 molab 資源）。
   - 跨域 iframe 無法偵測內容成敗（contentDocument 不可讀），不做自動偵測，
     以明確的指引文案與手動重載代替。
   - **實測結論（2026-08-06，已依此調整實作）**：molab iframe 嵌入在三個層面失敗——
     ① 已登入的 molab session 進不了 iframe（SameSite cookie，Chrome 亦然，非僅
     Safari）②唯讀預覽的內容區在被嵌入時渲染失敗（內層預覽框架拒絕嵌套）
     ③「Run it now」在 iframe 內點擊無效。因此 GPU 分頁改為**站內導流面板**
     （tab 結構保留，內容為步驟指引＋外開/登入/下載行動按鈕，不再 iframe molab）——
     即 spec「內嵌 GPU 分頁的降級」scenario 的常駐形態。

## Risks / Trade-offs

- [molab GPU 對免費/一般帳號的可用性與額度不明] → 頁面誠實註明「GPU 供應與額度依 molab 帳號方案而定」；後備 = 下載 .py 自跑；apply 時使用者實測結果記入 NOTES
- [0.5B 模型在 molab 下載耗時] → 選小模型、資料小、步數少；必要時 apply 時換更小基底
- [numpy 迷你 LM 在低階裝置太慢] → 決策 2 的預錄降級路徑
- [molab UI 改版導致步驟說明過時] → 說明寫「意圖層級」（登入/fork/選 GPU/執行）不寫死按鈕字樣與位置
- [學員誤以為要付費才能上課] → 課頁明確標示 GPU 軌道是「選配延伸」，核心課程零成本

## Migration Plan

純新增（新課目錄 + build 擴充 + 重部署），不動第一課。回滾 = 從 build 移除第二課重新部署。

## Open Questions

- molab 分享連結的最終形式（fork 按鈕行為、是否需 public link）——使用者上傳時實測後回填，不影響架構
- 軌道 B 基底模型最終選擇（下載速度 vs 效果）——apply 時實測定案
