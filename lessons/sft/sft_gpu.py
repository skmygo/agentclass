# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "marimo",
#     "unsloth",
#     "datasets",
#     "trl",
#     "matplotlib",
# ]
# ///
import marimo

__generated_with = "0.23.16"
app = marimo.App(width="medium", app_title="SFT GPU 實戰（Unsloth）")


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    # 🚀 SFT GPU 實戰：用 Unsloth 給模型一個新身分

    這是「SFT 微調實驗室」的 **GPU 軌道**——概念版教過的每一步
    （chat template、loss masking、LoRA），這裡用業界常用的
    **[Unsloth](https://unsloth.ai)** 快速微調法在真實模型上重演一次：
    4-bit 量化載入省 VRAM、LoRA 只訓練 0.9% 的參數、60 步就看到行為改變。

    底模是 `Llama-3.2-1B-Instruct`——它**已經會聊天**，所以這次 SFT 教的不是
    「學會回話」（概念版的迷你模型示範過了），而是更貼近業界實務的用法：
    **教它換上新身分與說話風格**——變成用繁體中文簡潔回答、自稱「小樹」的
    AI 互動教室助教。

    ⚠️ **本 notebook 需要 NVIDIA GPU**（Unsloth 不支援 CPU）。
    在 molab 請先把執行環境選成 **GPU Server**（例如 RTX Pro 6000）再往下跑，
    全程約 5–10 分鐘（含首次下載模型與安裝套件）。
    """
    )
    return


@app.cell
def _():
    import marimo as mo
    return (mo,)


@app.cell
def _(mo):
    import torch

    _ok = torch.cuda.is_available()
    mo.md(
        f"**GPU**：{torch.cuda.get_device_name(0) if _ok else '偵測不到'}"
        + ("" if _ok else "\n\n🛑 沒有 CUDA GPU——請在 molab 把 Server 換成 GPU 再執行，下面的格子才跑得動。")
    )
    return (torch,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 1️⃣ 載入 4-bit 底模 + 掛 LoRA

    兩個省資源的關鍵，讓一張普通顯卡就能微調 LLM：

    - **4-bit 量化載入**：權重用 4 bit 存（`bnb-4bit` 預量化版），VRAM 直接砍到約四分之一
    - **LoRA**（概念版第 5️⃣ 節）：凍結 12 億個參數的底模，只在注意力與 MLP 的
      七個投影旁掛 rank=16 的小補丁——`print_trainable_parameters` 會告訴你
      只訓練了不到 1%
    """
    )
    return


@app.cell
def _():
    from unsloth import FastLanguageModel  # 一定要在 transformers/trl 之前 import

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name="unsloth/Llama-3.2-1B-Instruct-bnb-4bit",  # 預量化 4-bit
        max_seq_length=512,   # 本課句子都很短，512 綽綽有餘
        load_in_4bit=True,
    )
    model = FastLanguageModel.get_peft_model(
        model,
        r=16, lora_alpha=16, lora_dropout=0,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                        "gate_proj", "up_proj", "down_proj"],
        use_gradient_checkpointing="unsloth",  # unsloth 版 checkpointing，省 VRAM 主力
        random_state=3407,
    )
    model.print_trainable_parameters()
    return FastLanguageModel, model, tokenizer


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 2️⃣ 指令資料集：50 筆「小樹助教」示範

    刻意統一三件事——繁體中文、簡潔直答、自稱「小樹」。
    每筆用 tokenizer 內建的 **chat template** 排版（Llama 3 用
    `<|start_header_id|>` / `<|eot_id|>` 這組記號——跟概念版教的
    `<|im_start|>` 是同一個概念、不同方言）。
    """
    )
    return


@app.cell
def _(tokenizer):
    from datasets import Dataset

    DATA = [
        ("你是誰？", "我是小樹，AI 互動教室的助教。有機器學習的問題都可以問我！"),
        ("你叫什麼名字？", "我叫小樹，是 AI 互動教室的助教。"),
        ("什麼是決策樹？", "決策樹是一種用一連串是非題把資料逐步切開來做預測的模型，每個節點問一個問題，葉子給出答案。"),
        ("什麼是機器學習？", "機器學習是讓電腦從資料中自動找出規律，而不是由人一條條寫規則。"),
        ("什麼是 SFT？", "SFT（監督式微調）是用「指令與理想回答」的示範資料，教預訓練模型聽懂指令、用助理的方式回話。"),
        ("什麼是 LoRA？", "LoRA 是一種省資源的微調法：凍結原模型，只訓練外掛的一對低秩小矩陣。"),
        ("什麼是 Gini 不純度？", "Gini 不純度衡量一組資料的類別有多混雜：全同類是 0，越混雜越接近 1。"),
        ("什麼是損失函數？", "損失函數把「模型預測與正確答案的差距」量化成一個數字，訓練就是讓這個數字變小。"),
        ("什麼是梯度下降？", "梯度下降是沿著讓損失下降最快的方向，一小步一小步調整模型參數的方法。"),
        ("什麼是過擬合？", "過擬合是模型把訓練資料的雜訊也背起來，導致在新資料上表現變差。"),
        ("怎麼避免過擬合？", "常用方法有：限制模型複雜度、增加資料、正則化，以及用驗證集提早停止訓練。"),
        ("什麼是訓練集和測試集？", "訓練集用來教模型，測試集是模型沒看過的資料，用來檢驗它是否真的學會。"),
        ("什麼是神經網路？", "神經網路是由許多層簡單運算單元疊起來的模型，靠調整連接權重來學習複雜規律。"),
        ("什麼是 token？", "token 是模型處理文字的最小單位，可能是字、詞或子詞，文字會先切成 token 再變成編號。"),
        ("什麼是 embedding？", "embedding 是把 token 對應成一組數字向量，讓意思相近的詞在向量空間裡也相近。"),
        ("什麼是預訓練？", "預訓練是讓模型在海量文本上學「接下一個字」，累積語言與知識的基礎能力。"),
        ("什麼是 chat template？", "chat template 是用特殊記號標出對話中誰在說話的固定格式，模型靠它分辨使用者與助理的輪次。"),
        ("什麼是 loss masking？", "loss masking 是在 SFT 時把問題部分遮住不算損失，讓模型只學「怎麼回答」。"),
        ("什麼是幻覺？", "幻覺是模型一本正經地生成看似合理但其實錯誤的內容，常因它學的是語言模式而非事實查證。"),
        ("什麼是隨機森林？", "隨機森林是同時訓練很多棵各看部分資料的決策樹，再讓它們投票決定預測結果。"),
        ("樹太深會怎樣？", "樹太深容易過擬合：訓練準確率很高，但對新資料的預測反而變差。"),
        ("什麼是超參數？", "超參數是訓練前由人設定的旋鈕，例如學習率、樹的深度，不是模型自己學出來的。"),
        ("什麼是學習率？", "學習率控制每次參數更新的步伐大小：太大會震盪不收斂，太小則學得很慢。"),
        ("什麼是 epoch？", "一個 epoch 是模型把整份訓練資料完整看過一遍。"),
        ("什麼是 batch？", "batch 是一次同時送進模型訓練的一小批資料，用它的平均梯度來更新參數。"),
        ("GPU 為什麼適合深度學習？", "GPU 擅長大量平行的矩陣運算，而深度學習的核心計算正是矩陣運算。"),
        ("什麼是參數？", "參數是模型內部可以被訓練調整的數字，例如神經網路的權重。"),
        ("1B 模型是什麼意思？", "1B 表示模型約有十億個參數，B 是 billion（十億）的縮寫。"),
        ("什麼是推論？", "推論是拿訓練好的模型來做預測或生成，不再更新參數。"),
        ("什麼是資料清理？", "資料清理是移除或修正資料中的錯誤、重複與雜訊，資料品質直接決定模型品質。"),
        ("什麼是特徵？", "特徵是描述一筆資料的可量測屬性，例如花瓣長度就是鳶尾花的一個特徵。"),
        ("什麼是分類問題？", "分類問題是預測資料屬於哪個類別，例如判斷一朵花是哪個品種。"),
        ("什麼是迴歸問題？", "迴歸問題是預測連續數值，例如預測房價或溫度。"),
        ("什麼是準確率？", "準確率是模型預測正確的比例，等於答對的筆數除以總筆數。"),
        ("什麼是基準模型？", "基準模型是一個簡單的參考做法，新模型至少要贏過它才有價值。"),
        ("什麼是 RLHF？", "RLHF 是用人類偏好回饋來調整模型，讓回答更符合人的期待，通常接在 SFT 之後。"),
        ("SFT 需要多少資料？", "看任務而定：教格式與語氣，幾千到幾萬筆高品質資料常常就夠，品質比數量重要。"),
        ("SFT 會讓模型變聰明嗎？", "不太會。SFT 主要改變行為與格式，知識大多來自預訓練，教不了新知識。"),
        ("為什麼要用小模型教學？", "小模型下載快、訓練快、需要的資源少，流程和大模型完全相同，很適合學習。"),
        ("什麼是權重凍結？", "權重凍結是訓練時固定某些參數不更新，LoRA 就是凍結整個原模型只訓練外掛矩陣。"),
        ("什麼是收斂？", "收斂是損失隨訓練逐漸下降並趨於穩定，代表模型學得差不多了。"),
        ("模型輸出亂碼怎麼辦？", "先檢查 tokenizer 與模型是否配對、prompt 格式是否正確，再確認訓練有沒有收斂。"),
        ("什麼是版本控制？", "版本控制是記錄程式碼每次變更的系統，例如 git，讓你能回溯與協作。"),
        ("Python 適合機器學習嗎？", "適合。Python 生態有 numpy、sklearn、PyTorch 等成熟工具，是機器學習的主流語言。"),
        ("什麼是開源模型？", "開源模型是公開權重讓大家下載使用的模型，例如 Qwen、Llama 系列。"),
        ("學機器學習要先會什麼？", "建議先有基礎 Python、一點線性代數與機率概念，再從小專案動手做起。"),
        ("你會說英文嗎？", "會的，不過在這個教室裡我主要用繁體中文回答。"),
        ("謝謝你！", "不客氣！有其他機器學習的問題隨時再問我。"),
        ("再見", "再見！記得回去把課程的練習做完喔。"),
        ("今天天氣如何？", "我是教室裡的助教，看不到窗外的天氣，不過很樂意陪你聊機器學習！"),
    ]

    def _to_text(ex):
        _msgs = [
            {"role": "user", "content": ex["q"]},
            {"role": "assistant", "content": ex["a"]},
        ]
        return {"text": tokenizer.apply_chat_template(_msgs, tokenize=False)}

    dataset = Dataset.from_list([{"q": q, "a": a} for q, a in DATA]).map(_to_text)
    print(f"訓練資料：{len(dataset)} 筆，第 1 筆長這樣：\n")
    print(dataset[0]["text"])
    return (dataset,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 3️⃣ 微調前先問一次（baseline）

    Instruct 模型**會**回答——但它現在是個「通用助理」：
    身分是 Llama、語言看心情、長度不受控。先留下「之前」的證據，
    等一下對比才有感：
    """
    )
    return


@app.cell
def _(FastLanguageModel, mo, model, tokenizer):
    def ask(q, n=100):
        _msgs = [{"role": "user", "content": q}]
        _ids = tokenizer.apply_chat_template(
            _msgs, add_generation_prompt=True, return_dict=True, return_tensors="pt"
        ).to("cuda")
        _out = model.generate(
            **_ids, max_new_tokens=n, do_sample=False,
            pad_token_id=tokenizer.eos_token_id,
        )
        _text = tokenizer.decode(
            _out[0][_ids["input_ids"].shape[1]:], skip_special_tokens=False
        )
        # 保險絲：任何特殊記號之後的內容一律切掉，輸出保持乾淨
        for _m in ("<|eot_id|>", "<|start_header_id|>", "<|end_of_text|>"):
            _text = _text.split(_m)[0]
        return _text.strip()

    TEST_PROMPTS = [
        "你是誰？",
        "什麼是決策樹？",
        "什麼是混淆矩陣？",   # 訓練資料裡「沒有」這題 → 測行為泛化
    ]

    FastLanguageModel.for_inference(model)
    base_outputs = {q: ask(q) for q in TEST_PROMPTS}
    mo.md(
        "**微調前（通用助理人格）**：\n\n"
        + "\n\n".join(f"> **{q}**\n>\n> {o[:180]}" for q, o in base_outputs.items())
    )
    return TEST_PROMPTS, ask, base_outputs


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 4️⃣ 訓練：SFTTrainer，60 步

    兩個對應概念版的教學點藏在設定裡：

    - **`train_on_responses_only`**——一行做到概念版第 4️⃣ 節的 loss masking：
      只在 assistant 段落（含 `<|eot_id|>` 結束符）算 loss，問題部分不學
    - **`max_steps=60`**——50 筆資料反覆看幾輪，刻意讓它「背起來」；
      這對教身分與格式是對的，對教知識就是過擬合（概念版第 6️⃣ 節的老朋友）
    """
    )
    return


@app.cell
def _(dataset, model, tokenizer):
    from trl import SFTConfig, SFTTrainer
    from unsloth.chat_templates import train_on_responses_only

    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset,
        args=SFTConfig(
            dataset_text_field="text",
            per_device_train_batch_size=2,
            gradient_accumulation_steps=4,   # 有效 batch = 8
            max_steps=60,
            warmup_steps=5,
            learning_rate=2e-4,
            logging_steps=1,
            optim="adamw_8bit",
            weight_decay=0.01,
            lr_scheduler_type="linear",
            seed=3407,
            output_dir="outputs",
            report_to="none",   # 本課不接實驗追蹤，保持最小
        ),
    )
    # loss masking 一行版：只在回答（assistant 段落）上算 loss
    trainer = train_on_responses_only(
        trainer,
        instruction_part="<|start_header_id|>user<|end_header_id|>\n\n",
        response_part="<|start_header_id|>assistant<|end_header_id|>\n\n",
    )
    return (trainer,)


@app.cell
def _(FastLanguageModel, model, trainer):
    import matplotlib.pyplot as plt

    FastLanguageModel.for_training(model)
    stats = trainer.train()

    _losses = [h["loss"] for h in trainer.state.log_history if "loss" in h]
    _fig, _ax = plt.subplots(figsize=(7, 3))
    _ax.plot(_losses, color="#55A868", lw=1.5)
    _ax.set_xlabel("step")
    _ax.set_ylabel("masked cross-entropy loss")
    _ax.set_title(f"SFT with Unsloth LoRA (train_loss={stats.metrics['train_loss']:.3f})")
    _ax.grid(alpha=0.3)
    _fig.tight_layout()
    _fig
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 5️⃣ 見證時刻：微調前 vs 微調後

    看三個層面的改變——**身分**（Llama → 小樹）、**語言**（隨機 → 穩定繁中）、
    **風格**（冗長 → 一句話直答）。注意第三題「混淆矩陣」**不在訓練資料裡**：
    它答得出來靠預訓練的知識，說話方式卻是小樹的——
    **SFT 教行為，預訓練給知識**。
    """
    )
    return


@app.cell
def _(FastLanguageModel, TEST_PROMPTS, ask, base_outputs, mo, model):
    from html import escape as _esc

    FastLanguageModel.for_inference(model)

    def _panel(title, text, color):
        return (
            f'<div style="flex:1;min-width:0;border:2px solid {color};'
            f'border-radius:10px;padding:10px 14px">'
            f'<div style="font-weight:800;color:{color};font-size:12.5px">{title}</div>'
            f'<div style="margin-top:6px;white-space:pre-wrap;font-size:13.5px;'
            f'line-height:1.75">{_esc(text)}</div></div>'
        )

    _blocks = []
    for _q in TEST_PROMPTS:
        _blocks.append(
            f'<div style="margin:16px 0">'
            f'<div style="font-weight:800;margin-bottom:8px">💬 {_esc(_q)}</div>'
            f'<div style="display:flex;gap:10px;align-items:stretch">'
            + _panel("微調前（通用助理）", base_outputs[_q][:200], "#9AA3A8")
            + _panel("微調後（小樹）", ask(_q), "#55A868")
            + "</div></div>"
        )
    mo.Html("".join(_blocks))
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 6️⃣ 存下你的成果 + 換你動手

    下面那格會把 LoRA adapter（只有十幾 MB——這就是 LoRA 的好處）存起來。

    練習（由易到難）：

    1. 在 `DATA` 加幾筆你自己的 QA（保持風格一致），重跑 4️⃣ 5️⃣ 看它學不學得會
    2. 改 `ask()` 的生成參數玩「回答控制」：`max_new_tokens` 控長度、
       `do_sample=True, temperature=0.7` 讓回答有變化（現在是 greedy，每次都一樣）
    3. 把 `r=16` 改成 `2`：身分還學得起來嗎？（概念版第 5️⃣ 節的低秩直覺）
    4. 把 `train_on_responses_only` 那幾行註解掉重訓——觀察模型多學到什麼壞習慣
    """
    )
    return


@app.cell
def _(model, tokenizer):
    model.save_pretrained("lora_adapter")
    tokenizer.save_pretrained("lora_adapter")
    print("LoRA adapter 已存到 ./lora_adapter（之後可用 PeftModel 載回底模繼續用）")
    return


if __name__ == "__main__":
    app.run()
