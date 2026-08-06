# Spike 踩坑紀錄 — sft（2026-08-06）

## GPU notebook 改版 2：底模換 Llama-3.2-1B-Instruct（2026-08-06 更晚）

使用者要求對齊參考教材的模型並解決「回答不可控」。底模從 Qwen2.5-0.5B **base** 換成
`unsloth/Llama-3.2-1B-Instruct-bnb-4bit`（**instruct**）：

- **教學故事轉向**（更貼業界實務）：instruct 模型已會聊天，SFT 教的是「換身分與說話
  風格」（通用助理 → 繁中簡答的小樹），不再是「從續寫到會回話」——那個轉變由概念版
  迷你模型負責示範，兩軌分工反而更清楚。
- **回答可控的根本解**：instruct 模型受過完整對話訓練，會乖乖吐 `<|eot_id|>` 收尾，
  不像 base 常亂開幻覺新回合；保險絲（特殊記號硬切）仍保留。
- tokenizer 有 chat template 了 → 回到 `apply_chat_template` 標準寫法；
  `train_on_responses_only` 換 Llama 3 的記號（`<|start_header_id|>user/assistant<|end_header_id|>\n\n`）。
- LoRA 按參考教材掛七個投影（q/k/v/o + gate/up/down），r=16 → 可訓練 ≈1,127 萬（0.9%）。
- 左頁同步：LoRA 圖數字（12.4 億凍結／1,127 萬可訓練）、對照表（Llama 3 template、
  `<|eot_id|>`）、GPU 區塊故事線全部更新。
- 教訓：**教學用 SFT demo 選 instruct 底模比 base 省事得多**——模板現成、收尾可靠；
  base 模型的「學會回話」戲劇性交給瀏覽器內的迷你模型演就好。

## GPU notebook 改版：手寫迴圈 → Unsloth（2026-08-06 稍晚）

依使用者參考教材（`ref_data/06_unsloth-finetune-tutorial.ipynb`）把 `sft_gpu.py` 從
「transformers + peft 手寫訓練迴圈」改為 **Unsloth 配方**：4-bit 預量化底模
（`unsloth/Qwen2.5-0.5B-bnb-4bit`）+ `get_peft_model`（r=16, q/k/v/o,
`use_gradient_checkpointing="unsloth"`）+ trl `SFTTrainer` 60 步 +
`train_on_responses_only`（一行 loss masking，保住左頁第 4 節的教學連結）。
不接 MLflow（`report_to="none"`）。

- 代價：**Unsloth 不支援 CPU**，舊版「無 GPU 自動縮小規模」路徑移除，notebook 變
  GPU-only；本機（無 GPU）驗證降為結構層級（`import sft_gpu` 驗 marimo 格式與語法，
  16 cells 註冊 OK），實際執行驗證只能在 molab GPU 上做。
- molab 上舊 notebook（nb_9AyV73Kck4g89rx9E27mrF）內容需以新版取代重測；
  Unsloth 於 molab 的 pip 安裝相容性（PEP 723 deps）以該次實測為準。
- 教學故事不變：模型續用 Qwen2.5-0.5B base、資料續用 50 筆小樹、左頁 r=16/q,k,v,o/
  2.16M（0.44%）等數字全部仍為真。
- **坑（molab 實跑踩到）**：`unsloth/Qwen2.5-0.5B-bnb-4bit`（base）的 tokenizer
  **沒有 chat_template**，呼叫 `apply_chat_template` 直接
  `ValueError: Cannot use chat template functions...`。修法＝手寫
  `<|im_start|>` 模板字串（`<|im_start|>`/`<|im_end|>` 特殊 token 在 Qwen base
  詞表裡都在，只是沒附 template）。通則：**用 base 模型做 SFT 教學時一律手寫模板**，
  順便跟教學內容對齊。
- **坑（molab 實跑踩到 2）**：SFT 後模型答完常「亂開幻覺新回合」——不吐 `<|im_end|>`
  收尾而是直接生成 `<|im_start|>user…` 自問自答，只等 im_end 的停止條件擋不住。
  修法＝`generate` 的 `eos_token_id` 給**清單** `[im_end, im_start]` ＋解碼後在第一個
  特殊記號處硬切（雙保險）。另：對比輸出別用 markdown 表格（模型輸出含換行會把表
  弄壞），用 HTML 卡片 + `white-space:pre-wrap` + `html.escape`。

> 延續 `lessons/decision-tree/NOTES.md` 的管線；本檔只記第二課的新發現。

## 管線沿用結果

第一課的管線（uv → lesson.py → 雙層驗證 → build.sh 組裝 → wrangler 部署）完整複用，
無新增工程成本。WASM 就緒時間與第一課相同（~24 秒）。雙軌架構（瀏覽器概念 + molab GPU）
首次落地。

## 新踩的坑

1. **`mo.vstack([fig, mo.md(...)])` 裡的裸 matplotlib figure 在 WASM 不渲染**
   （marimo 0.23.16；CPython export 下也一樣不算 img）。規範：**圖一律當 cell 的
   最後運算式**，說明文字拆到下一個 cell（要共用數值就 return 變數）。

2. **迷你 LM 的三個 bug，全部同構於真實 SFT 的經典錯誤**（已修，並寫進教材當教學點）：
   - 生成 prompt 停在 `a:`，但 `a: ` 的空格被 mask → 第一個字就 OOD 出軌。
     規範：**生成起點必須落在訓練目標的起點上**（prompt 含空格）。
   - 上下文窗 CTX=8 裝不下問題關鍵字（cats/dogs 落窗外）→ 模型分不出問題。CTX=16 解。
   - **回合結束符沒算 loss** → 模型答對但不會「停」。對應真實 SFT 必須把
     `<|im_end|>` 納入 loss。這條已寫進兩個 notebook 的教材文字。

3. **numpy 迷你 LM 在 WASM 的效能可行**：1500 步預訓練 + 800 步 SFT，
   拉滑桿即時重訓約 1–2 秒。關鍵是 embedding 梯度用 `np.add.at` 向量化，
   不能用 per-sample Python 迴圈。

4. **剛部署完立刻打線上冒煙會撞 CDN 冷資產**（首測 h1 逾時，重試即 PASS）。
   規範：deploy 後等 30–60 秒再冒煙，或失敗先重試一次。

5. `float(tensor_requires_grad)` 會噴 UserWarning，用 `float(x.detach())`。

## sft_gpu.py 驗證狀態

- 本機無 GPU（.217 是 Dokploy 主機）。CPU FAST 模式（自動縮小：8 筆資料、1 epoch、
  batch 2）**75 秒走通全流程**：Qwen2.5-0.5B 載入（494M 參數）、LoRA 掛載
  （2.16M 可訓練 = 0.44%）、訓練、前後對比生成。
- FAST 模式偵測寫在 notebook 內（無 CUDA 自動降級），也保護誤用 CPU 的學員。
- **全量驗證待 molab**（使用者操作）：上傳 → 選 RTX Pro 6000 → Run all，
  預估 5–10 分鐘（含模型下載）。結果（額度、下載時間、訓練時間、fork 行為）回填本檔。

## molab 整合機制（已就緒，待回填）

- 課頁 GPU 區塊的主按鈕 href 是 `MOLAB_LINK_PLACEHOLDER`；前端 JS 偵測到佔位符
  自動降級為「連結準備中」不可點，後備按鈕（下載 sft_gpu.py / molab 首頁）永遠可用。
- **回填流程**：拿到分享連結後
  `sed -i 's|MOLAB_LINK_PLACEHOLDER|<link>|' lessons/sft/page/index.html`
  → `scripts/build.sh` → `wrangler pages deploy`。
- `sft_gpu.py` 帶 PEP 723 inline dependencies（marimo sandbox / molab 可自動裝依賴）。

## molab iframe 嵌入實測（2026-08-06，結論：不可行）

嘗試把 molab notebook 直接 iframe 進課程頁右欄（「登入後回站內編輯」構想），實測失敗：

1. **HTTP header 沒擋**（無 X-Frame-Options / frame-ancestors）——iframe 能載入 molab 外殼，
   到此為止都是好消息。
2. **登入態進不了 iframe**：同一個 Chrome 已登入 molab，iframe 內仍顯示 Sign In。
   原因是 SameSite cookie 保護（跨站框架不送 session cookie），**與第三方 cookie 設定無關、
   Chrome 也一樣**——比原先預估（只有 Safari 擋）更糟。
3. **唯讀預覽內容在 iframe 裡渲染失敗**（破檔案圖示；同連結單獨開啟正常）——
   molab 預覽的內層框架拒絕被嵌套。
4. 「Run it now」在 iframe 內點擊無反應。

處置：GPU 分頁改為**站內導流面板**（保留 tab 結構；內容＝步驟＋「新分頁開啟 notebook /
登入 / 下載」行動按鈕）。若未來 molab 官方提供 embed 模式，可再換回真嵌入。

其他觀察：Cloudflare Pages production 別名切換有 CDN 傳播延遲（同一時間 curl 拿新版、
另一台瀏覽器拿舊版數分鐘），部署後驗證要用 deployment 專屬網址或等待。

## molab 實測結果（2026-08-06）

- 使用者將 `sft_gpu.py` 上傳 molab、以 GPU（RTX Pro 6000 選項）**完整跑通全程**。
- 分享連結（最終版，Unsloth + Llama-3.2-1B-Instruct）：
  https://molab.marimo.io/notebooks/nb_CaYVVFxPTd5ngkZYYjZBjb
  （初版 transformers+peft 為 nb_9AyV73Kck4g89rx9E27mrF，已棄用）。
  課頁 GPU 區塊與右欄 GPU 分頁的按鈕均已指向新連結並重部署。
- 雙軌架構驗證完成：瀏覽器軌（WASM）與 GPU 軌（molab）皆可用，
  molab 端無需本站任何後端配合。
- 未記錄的細節（GPU 額度上限、模型下載耗時、實際訓練時長）：學員實跑時如回報再補。
