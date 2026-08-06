# 第二課：LLM 的 SFT（監督式微調）— 雙軌課程

## Why

AI 互動教室要出第二課「LLM 的 SFT 概念」。SFT 的核心概念（資料格式、chat template、loss masking、LoRA）可以在瀏覽器內互動教學，但**真實的模型微調需要 torch 與 GPU，Pyodide/WASM 跑不了**——這是現有「純瀏覽器」架構第一次遇到的能力邊界。使用者已確認 marimo 官方雲（molab）登入後可選 Server 執行、有 RTX Pro 6000 可用，需要一個把 GPU 執行整合進現有系統的乾淨作法。

## What Changes

- 建立**雙軌課程架構**（本課首次採用，日後所有需要 GPU 的課沿用）：
  - **軌道 A（瀏覽器，不變的既有架構）**：左教學頁 + 右 WASM notebook，互動教 SFT 概念——指令資料格式、chat template、tokenization、loss masking 視覺化、LoRA 低秩分解的參數帳、以及一個 numpy 實作的迷你語言模型「先預訓練後 SFT」的行為對比實驗
  - **軌道 B（GPU，外部執行）**：獨立的 `sft_gpu.py` marimo notebook（transformers + peft，小模型 LoRA SFT），學員經 molab 開啟：登入自己帳號 → fork → Server 選 GPU（RTX Pro 6000）→ 執行；課頁提供顯眼的導流入口與步驟說明
- 新增 `lessons/sft/`（lesson.py、sft_gpu.py、page/、NOTES.md）
- 頁殼新增「GPU 軌道」導流元件（molab 為外部新分頁開啟，不 iframe）
- `scripts/build.sh` 與根頁課程列表納入第二課，重新部署 agentclass.pages.dev

## Capabilities

### New Capabilities

（無）

### Modified Capabilities

- `interactive-lesson`: 新增「GPU 延伸軌道」需求——當課程內容需要瀏覽器無法提供的算力（GPU）時，課程頁 SHALL 提供外部 GPU 執行路徑（學員自有帳號、明確步驟），且核心概念教學仍 SHALL 維持瀏覽器內可跑；既有「純網址分享、無後端」等需求不變（GPU 在學員自己的 molab 帳號執行，本站仍是純靜態）。

## Impact

- 新目錄 `lessons/sft/`；`scripts/build.sh`、`site/index.html` 小幅擴充
- 新外部依賴：molab（marimo 官方雲）——課頁只放連結與說明，不引入任何本站後端；學員 GPU 用量計費/額度屬於 molab 帳號體系，非本站控制
- 需要使用者參與的節點：GPU notebook 上傳 molab、實測 RTX Pro 6000、回填分享連結（無 API 可自動化，需登入操作）
- 本機驗證：GPU notebook 先在本機驗證（依本機 GPU 可用性決定全量或縮小規模），WASM 概念課沿用既有雙層驗證管線
