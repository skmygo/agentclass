# Tasks — add-sft-lesson

## 6. GPU notebook 改用 Unsloth 方法（依使用者參考教材 ref_data/06_unsloth-finetune-tutorial.ipynb）

- [x] 6.1 重寫 `sft_gpu.py`：Unsloth FastLanguageModel（4-bit 預量化 Qwen2.5-0.5B base）+ LoRA r=16 q/k/v/o + SFTTrainer 60 步 + `train_on_responses_only` 一行 loss masking + 前後對比 + 存 adapter；不接 MLflow；GPU-only（Unsloth 不支援 CPU）
- [x] 6.2 左頁同步：GPU 軌道文案改 Unsloth、對照表加「微調方法」列、移除「無 GPU 自動縮小規模」的過時後備說明；本機結構驗證（16 cells 註冊無誤）
- [x] 6.3 【需使用者】molab 上以新版 `sft_gpu.py` 重測——踩出兩坑（base tokenizer 無 chat_template、答完亂開幻覺回合），迭代後改用 Llama-3.2-1B-Instruct 底模跑通；新連結 nb_CaYVVFxPTd5ngkZYYjZBjb 已回填重部署

## 5. 內嵌 molab GPU 分頁（方案 C，後續擴充）

- [x] 5.1 右欄改為 tab 列〔🧪 互動實驗｜⚡ GPU 軌道〕：切換不影響 WASM 狀態、golab 自動切回；GPU 軌道區塊同步更新
- [x] 5.2 本機驗證（tab 切換、狀態保留、零錯誤）→ 部署
- [x] 5.3 已登入 molab 的瀏覽器實測站內編輯——**不成立**（SameSite cookie 使登入態進不了 iframe、預覽內容拒絕嵌套渲染、Run it now 無效），依 spec 降級 scenario 改為站內導流面板，結論已寫入 NOTES 與 design

## 1. 軌道 A：SFT 概念 notebook（瀏覽器）

- [x] 1.1 建 `lessons/sft/` 與 uv 環境，寫 `lesson.py`：指令資料格式與 chat template → tokenization → loss masking 視覺化（prompt 遮、response 算 loss）→ LoRA 低秩分解參數帳（互動調 rank）→ numpy 迷你 LM「預訓練 vs SFT 後」行為對比實驗（無需降級：WASM 實測即時重訓 1–2 秒）
- [x] 1.2 雙層驗證：CPython headless 全 cell 無錯 + WASM 匯出後 Playwright 冒煙（4/4 圖、零錯誤、24 秒就緒）

## 2. 軌道 B：GPU notebook

- [x] 2.1 寫 `sft_gpu.py`：transformers + peft 手寫訓練迴圈（小 base 模型 + LoRA + 內嵌繁中迷你指令資料集），教學註解對齊軌道 A 概念；本機無 GPU，以 CPU FAST 模式（8 筆/1 epoch）75 秒走通全流程，全量驗證待 molab
- [x] 2.2 【硬節點·需使用者】把 `sft_gpu.py` 上傳 molab、實測登入 → fork → 選 RTX Pro 6000 → 執行全程——使用者實測完整跑通，分享連結 nb_9AyV73Kck4g89rx9E27mrF

## 3. 課程頁與整合

- [x] 3.1 寫左側教學頁（教學法自由發揮，內容嚴格對照軌道 A notebook），含 GPU 軌道導流區塊（molab 步驟說明、額度誠實註記、下載 sft_gpu.py 後備入口；連結先佔位）
- [x] 3.2 擴充 `scripts/build.sh` 與根頁課程列表納入第二課；整站本機驗證（含第一課無回歸）
- [x] 3.3 回填 molab 分享連結（依 2.2 結果），重建 dist 並重部署，線上確認連結生效

## 4. 部署與交付

- [x] 4.1 部署 Cloudflare Pages，線上冒煙（兩課皆測；SFT 首測撞 CDN 冷資產重試即過）
- [x] 4.2 寫 `lessons/sft/NOTES.md`（numpy LM 效能、vstack 圖不渲染、結束符教訓等；molab 實測數據待 2.2 後補），交付網址
