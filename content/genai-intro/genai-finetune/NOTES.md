# genai-finetune（補充 B）NOTES

微調工具實戰：Unsloth、TRL 與託管微調。延伸主線 genai-training（概念）；LoRA 原理在 local-llm/lora-basics，本課不重教。
純瀏覽器 app 課：右欄**重播與重算**本機實測紀錄（numpy＋matplotlib），學員零安裝、零 key、零服務。

## 素材來源（全部實測，2026-09-24）

- 硬體：本機 RTX 4090 24 GB（驅動 580、CUDA 13.0）。**與常駐 vLLM／index-tts 共用**：其他行程占約 13.3 GB、
  GPU 使用率常駐約 45%。每個訓練行程用 `--mem-cap-gb 9.5`（`torch.cuda.set_per_process_memory_fraction`）限額。
- 模型：`unsloth/Qwen3-1.7B-bnb-4bit`（主實驗，兩個工具吃同一份 NF4 權重）；VRAM 校準點另用
  `unsloth/Qwen3-0.6B-bnb-4bit`、`unsloth/Qwen3-4B-bnb-4bit`、`Qwen/Qwen3-1.7B`（LoRA bf16）、`Qwen/Qwen3-0.6B`（全參數）。
- 沒有用到任何區網服務（LLM／embedding）——資料由程式模板產生，學員在免費 T4 上也能完整重現。
- 兩個環境（Unsloth 釘版，裝不進同一個）：
  - TRL 原生：trl 1.13.0、peft 0.21.0、transformers 5.17.0、torch 2.14.0、bitsandbytes 0.50.2、datasets 5.0.1、accelerate 1.15.0
  - Unsloth：unsloth 2026.9.11、unsloth_zoo 2026.9.7、trl 0.24.0、peft 0.21.0、transformers 5.5.0、torch 2.12.1、xformers 0.0.35、triton 3.7.1、datasets 4.3.0
- 工具生態與價格（WebSearch／WebFetch／PyPI，2026-09-24）：TRL 1.13.0（09-10）、Unsloth 2026.9.11（09-23；
  Desktop 2026-08 beta）、Axolotl 0.19.0（09-10）、LLaMA-Factory 0.9.5（05-30）、torchtune README「no longer actively
  maintained, wound down in 2025」、OpenAI 微調文件「winding down…no longer accessible to new users」、RFT 只支援 o4-mini、
  Together ≤16B SFT $0.34–0.38／M、DPO $0.84–0.94／M、每 job 最低 $4 起、Fireworks LoRA SFT ≤16B $0.50／M、
  Tinker Qwen3-8B train $0.44／M。Colab 免費版最長 12 小時、不保證 GPU（官方 FAQ）；Kaggle 時數只寫「每週有免費 GPU 時數」（官方文件頁抓不到，沒寫數字）。
  Fireworks 全參數價格沒查證到，頁面只寫「另有價目」。

## 跑法（repo 根；env：`FT_MEM_CAP_GB`、`FT_WORKDIR`，都有預設）

```bash
S=content/genai-intro/_spikes; R=<結果目錄>
uv run --script $S/spike_genai_finetune_data.py                     # 資料統計＋範例（純標準庫）
uv run --script $S/spike_genai_finetune.py --eval-base --out $R/r_trl_1.json          # TRL＋PEFT（含訓練前評分）
uv run --script $S/spike_genai_finetune_unsloth.py --out $R/r_uns_1.json              # Unsloth
LONG="--long-ctx 1500 --max-length 2048 --skip-eval"                                  # 長資料情境
uv run --script $S/spike_genai_finetune.py $LONG --out $R/r_trl_long.json
uv run --script $S/spike_genai_finetune_unsloth.py $LONG --out $R/r_uns_long.json
# VRAM 校準點（--max-steps 20 --skip-eval）：0.6B／4B QLoRA 短＋長、1.7B --mode lora16 --model Qwen/Qwen3-1.7B、
#   0.6B --mode full --model Qwen/Qwen3-0.6B --optim adamw_torch
uv run --script $S/spike_genai_finetune_errors.py --out errors.json                   # 測驗用的真實錯誤
python3 $S/spike_genai_finetune_collect.py --results $R --inject                      # 注入 lesson.py 與 page_content.py
python3 .claude/skills/make-lesson/scripts/page-fill.py content/genai-intro/genai-finetune
```

- 每個情境 TRL／Unsloth 各跑 3 次（檔案 mtime 決定第幾次，複製結果時用 `cp -p`）。collect 以內容分類，
  hero 重播「倍數居中」的那一對（不挑最好看的）。
- 注入標記：lesson.py 的 `# <FT_DATA>`；page_content.py 的 `const HERO = /*<HERO>*/`、`<!--<BA>-->`、`<!--<MASK>-->`、`<!--<CAL>-->`。
  **標記字串不要再出現在別處**（實錄：docstring 裡寫了 `/*<HERO>*/`，非貪婪 regex 從 docstring 一路吃到 SCRIPT，差點把整頁換掉；已改成錨定 `const HERO = `）。
- 第 3 節對照卡的題目由 collect 的 `BA_INDEX = 2` 決定；它會 assert 那題兩個工具輸出一字不差（課文這樣寫）。

## 踩到的坑（都已處理）

1. **Unsloth 2026.9.11 釘 `trl<=0.24.0`、`transformers<=5.5.0`**：跟 trl 1.13 裝不進同一環境（uv 原文錯誤已放進教學頁）。
2. **TRL 0.24 ＋ Qwen3 的 prompt／completion 格式**（在 Unsloth 環境不 import unsloth 的對照組）：每筆噴
   `Mismatch between tokenized prompt and the start of tokenized prompt+completion`，loss masking 失效（起始 loss 5.1、整段都在學），
   訓練後生成還撞 `RuntimeError: expected scalar type Float but found BFloat16`；長資料版直接 OOM（Tried to allocate 5.52 GiB）。
   → 放棄「同環境不同工具」的對照組，課程比的是實務上的兩個選擇：Unsloth（它釘的舊 TRL）vs 最新 TRL＋PEFT。
3. **TRL 的 `padding_free=True`**：沒開 packing 時 `ValueError: When padding_free=True without packing, max_length is not enforced…`，
   並警告只有 Flash Attention 系列可靠支援。沒裝 flash-attn，沒繼續追。
4. **預量化 bnb 權重在 fp16 路徑（T4）**：量化設定寫 bf16 運算 → PEFT 建出的 LoRA 也是 bf16 → fp16 AMP 的 GradScaler 報
   `NotImplementedError: "_amp_foreach_non_finite_check_and_unscale_cuda" not implemented for 'BFloat16'`（測驗 Q2）。
   修法已寫進 spike：Linear4bit 的 `compute_dtype` 改 fp16、可訓練參數轉 fp32；修後 `--fp16` 39/40。Unsloth `--fp16` 一次過。
5. **`torch.cuda.is_bf16_supported()` 在 T4（7.5）會回 True**（預設 `including_emulation=True`，能建 bf16 張量就算）——
   spike 改用 `get_device_capability()[0] >= 8` 判斷。沒有 T4 可實測，只有在 4090 用 `--fp16` 模擬精度路徑。
6. Unsloth 自動 padding-free：loss 起點不同（2.62 vs TRL 2.86）、`<|im_end|>` 後的換行不訓練；終點一樣。
7. **時間很吵、VRAM 很穩**：長資料每步中位數比 TRL÷Unsloth ＝ 3.3／1.6／1.7；第 1 次長資料 Unsloth 在第 40 步、TRL 在第 46 步
   各自跳檔（其他服務負載在變）。峰值 VRAM 每次相同（短資料 TRL 2.180／2.180／2.188）。
8. 全參數 1.7B 的 OOM 案例：錯誤訊息顯示當下 GPU 只剩 98.75 MiB——9.5 GB 上限＋CUDA context 約 0.5 GiB，
   跟其他服務的餘量只差一點。共用 GPU 的限額要留更大的餘裕。
9. 本機沒有全域 `ruff`：用 `uvx ruff`（0.16.8）跑，讀 repo 根的 ruff.toml。

## 換模型／改版要重驗的句子

重跑 spike → collect（會印全部摘要）→ 逐句對：

- 教學頁 s2 結果表（VRAM 2.18→2.00、4.09→2.49；時間範圍 21–23／18–21、168–200／78–124；倍數 1.3–1.4、1.6–3.3；loss 終點）、
  4B 長資料 8.16／4.34、「暖機約 1–2.7 秒、總時間差 3–27%」、hero 的「三次範圍 1.6–3.3 倍」。
- s3：0／23／39 題、6 題包 ```json 框、急件錯 11 題全是誤判成急、132→17 tokens、唯一錯題 #06（MeshLink AX 5G）。
- s4：TRL 第一筆 61／45 tokens；Llama 3.2 的 `assistant_only_loss` 錯誤原文。
- s5 CAL 表由 collect 生成；註腳「1.7B 全參數 OOM」。s6：價格與日期、fp16 修正後 39/40。
- 測驗：Q1（8.16→4.34、4B 全參數約 37 GiB）、Q2（fp16 錯誤原文）、Q3（6、11、115 tokens、17 張錯單）、Q4（Unsloth 標記錯誤原文）、
  Q5（8B QLoRA 估算 7.8／11.3 GiB、全參數約 80 GiB）。
- 實驗場：1️⃣ 決策文案的「1.6–3.3 倍」、2️⃣ 的跳檔說明（第 40／46 步）、3️⃣ 結論條列、5️⃣ 估算公式（Q4＝0.516、全參數 8 bytes 由 0.6B 校準、
  活化值基底＝token×層×MLP 寬度，4B TRL 長資料低估約 7%）、6️⃣ 價目、7️⃣ 解答（L1 的 3.3／1.6／1.7 與秒數、L2 的 24.9／14.2／17.7／14.1 GiB）。
- 工具版本表與「查證日 2026-09-24」全部要重查。
