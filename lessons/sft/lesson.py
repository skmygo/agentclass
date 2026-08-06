import marimo

__generated_with = "0.23.16"
app = marimo.App(width="medium", app_title="SFT 微調實驗室")


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    # 🔧 SFT 微調實驗室

    這是本課的**實驗場**。左側教學讀到哪，就回到這裡動手做——
    每一格程式碼都可以**直接修改、立即重跑**。改壞了重新整理就復原。

    壓軸是第 6️⃣ 節：你會在瀏覽器裡**親手 SFT 一個迷你語言模型**，
    看著它從「只會瞎接話」變成「會回答問題」。
    """
    )
    return


@app.cell
def _():
    import marimo as mo
    return (mo,)


@app.cell
def _():
    import matplotlib.pyplot as plt
    import numpy as np
    return np, plt


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 1️⃣ SFT 站在訓練管線的哪裡

    一個聊天助理的誕生通常分三步：

    1. **預訓練（Pretraining）**——海量文本上學「接下一個字」。產物是 base model：
       知識淵博，但只會**續寫**，不會**對話**。
    2. **SFT（Supervised Fine-Tuning，監督式微調）**——用「指令 → 理想回答」的
       示範資料繼續訓練，教它**聽懂指令、用助理的格式回話**。⬅ 本課主角
    3. **偏好對齊（RLHF / DPO…）**——再用人類偏好把回答調得更好。

    關鍵認知：**SFT 不是重新訓練，是在 base model 上「補課」**——
    資料量常常只有預訓練的百萬分之一，卻能徹底改變模型的行為方式。
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 2️⃣ 指令資料長什麼樣

    SFT 的原料就是一堆「怎麼問、該怎麼答」的示範。下面是本課自帶的迷你資料集
    （待會兒第 6️⃣ 節就用它微調模型）：
    """
    )
    return


@app.cell
def _():
    # 迷你指令資料集：q = 指令 / a = 理想回答（全小寫英文，讓迷你模型好學）
    sft_pairs = [
        ("what color is the sky?", "blue."),
        ("what color is grass?", "green."),
        ("what color is snow?", "white."),
        ("what color is the sun?", "yellow."),
        ("how many legs has a cat?", "four."),
        ("how many legs has a bird?", "two."),
        ("how many days in a week?", "seven."),
        ("is fire hot or cold?", "hot."),
        ("is ice hot or cold?", "cold."),
        ("what do cats say?", "meow."),
        ("what do dogs say?", "woof."),
        ("what do cows say?", "moo."),
        ("where do fish live?", "in water."),
        ("where do birds sleep?", "in trees."),
        ("what shines at night?", "the moon."),
        ("what falls from clouds?", "rain."),
    ]
    sft_pairs
    return (sft_pairs,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    真實世界的 SFT 資料在訓練前會先套上 **chat template**——
    用特殊記號標出誰在說話。以 Qwen 系列為例，一筆資料會變成：

    ```text
    <|im_start|>user
    what color is the sky?<|im_end|>
    <|im_start|>assistant
    blue.<|im_end|>
    ```

    模型學會這套格式後，推論時只要餵到 `<|im_start|>assistant`，
    它就知道「輪到我用助理的身分回話了」。
    本課的迷你模型用簡化版模板 `q: 問題\na: 回答\n\n`——概念完全相同，
    只是短到字元級小模型也學得動。
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 3️⃣ Tokenization：模型眼中沒有「字」，只有編號

    訓練前文字要先切成 token 換成整數編號。本課的迷你模型用最簡單的
    **字元級**切法（一個字元 = 一個 token）；真實 LLM 用 BPE 子詞
    （常見字整塊、罕見字拆小塊，詞表數萬到數十萬）。

    在下面輸入框打字，看文字變成編號——**不在詞表裡的字元會變 `⟨unk⟩`**
    （試試打中文：迷你詞表只收了英文小寫，這正是「詞表覆蓋率」問題的縮影）：
    """
    )
    return


@app.cell
def _(mo):
    tok_input = mo.ui.text(
        value="the sky is blue", label="想編碼的文字", full_width=True
    )
    tok_input
    return (tok_input,)


@app.cell
def _(mo, tok_input, vocab):
    _chips = []
    for _ch in tok_input.value.lower():
        if _ch in vocab:
            _chips.append(
                f'<span style="display:inline-block;margin:2px;padding:3px 8px;'
                f'border-radius:6px;background:#EAF3EC;border:1px solid #55A868;'
                f'font-family:monospace">{"␣" if _ch == " " else _ch}'
                f'<sub style="color:#52646E"> {vocab[_ch]}</sub></span>'
            )
        else:
            _chips.append(
                '<span style="display:inline-block;margin:2px;padding:3px 8px;'
                'border-radius:6px;background:#FBEFE8;border:1px solid #C44E52;'
                'font-family:monospace">⟨unk⟩</span>'
            )
    mo.Html("<div>" + "".join(_chips) + "</div>")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 4️⃣ Loss Masking：只在「回答」上學

    SFT 最重要的技術細節：一筆訓練資料裡**問題和回答都在**，
    但我們只希望模型學「怎麼回答」，不希望它浪費力氣學「怎麼出題」。

    做法：算損失（loss）時，把**問題部分的 token 遮起來**（mask，實務上是把
    label 設成 -100），只有**回答部分**的預測錯誤會回傳梯度。
    下面把一筆資料的每個字元著色——灰色不算 loss、綠色才算：
    """
    )
    return


@app.cell
def _(mo, sft_pairs):
    _q, _a = sft_pairs[0]
    _formatted = f"q: {_q}\na: {_a}\n"
    _answer_start = _formatted.index("a: ") + 3
    _chips = []
    for _i, _ch in enumerate(_formatted):
        _shown = {" ": "␣", "\n": "⏎"}.get(_ch, _ch)
        if _i >= _answer_start and _ch != "\n":
            _style = "background:#EAF3EC;border:1.5px solid #55A868;color:#1C2B33"
        else:
            _style = "background:#F0F0F0;border:1px solid #C8C8C8;color:#9AA3A8"
        _chips.append(
            f'<span style="display:inline-block;margin:2px;padding:3px 7px;'
            f'border-radius:6px;font-family:monospace;{_style}">{_shown}</span>'
        )
    mo.Html(
        "<div>" + "".join(_chips) + "</div>"
        '<p style="font-size:13px;color:#52646E">灰＝masked（不算 loss）·'
        "綠＝計算 loss 的目標（模型真正在學的部分）</p>"
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    第 6️⃣ 節的實驗有一個「**遮不遮問題**」的開關，你可以親自驗證這件事的影響。

    ## 5️⃣ LoRA：不動原模型，外掛小補丁

    全參數微調要更新**所有**權重——0.5B 模型就是 5 億個數字，顯卡吃不消。
    **LoRA** 的解法：原權重 $W$ 凍結不動，旁邊掛一對小矩陣 $B \cdot A$
    （秩為 $r$），只訓練這對小矩陣：

    $$W' = W + B \cdot A,\quad B \in \mathbb{R}^{d \times r},\ A \in \mathbb{R}^{r \times d},\ r \ll d$$

    拉動 $r$，看 0.5B 級模型（以 Qwen2.5-0.5B 的尺寸為例）要訓練的參數量差多少：
    """
    )
    return


@app.cell
def _(mo):
    lora_rank = mo.ui.slider(
        start=1, stop=64, step=1, value=16, label="LoRA rank r",
        show_value=True,
    )
    lora_rank
    return (lora_rank,)


@app.cell
def _(lora_rank, plt):
    # Qwen2.5-0.5B 量級：d_model=896、24 層，對 q/k/v/o 四個投影掛 LoRA
    _d, _layers, _proj = 896, 24, 4
    full_trainable = 494_000_000              # 全參數微調（整個模型）
    lora_trainable = 2 * _d * lora_rank.value * _proj * _layers

    _fig, _ax = plt.subplots(figsize=(7, 3))
    _bars = _ax.barh(
        ["full fine-tune", f"LoRA (r={lora_rank.value})"],
        [full_trainable, lora_trainable], color=["#C8C8C8", "#55A868"],
    )
    _ax.set_xscale("log")
    _ax.set_xlabel("trainable parameters (log scale)")
    for _b, _v in zip(_bars, [full_trainable, lora_trainable]):
        _ax.text(_v * 1.3, _b.get_y() + _b.get_height() / 2,
                 f"{_v:,}", va="center", fontsize=9)
    _ax.set_xlim(1e5, 5e9)
    _fig.tight_layout()
    _fig
    return full_trainable, lora_trainable


@app.cell(hide_code=True)
def _(full_trainable, lora_trainable, mo):
    mo.md(
        f"LoRA 只需訓練 **{lora_trainable:,}** 個參數，是全參數微調的 "
        f"**{lora_trainable / full_trainable:.2%}**——"
        "這就是筆電等級的卡也能微調 LLM 的原因。"
    )
    return


@app.cell
def _(np, plt):
    # 為什麼低秩夠用？——對一個「本質上低秩」的更新矩陣，小 r 就能重建得很好
    _rng = np.random.default_rng(0)
    _true_rank = 8
    _dW = (_rng.normal(size=(64, _true_rank)) @ _rng.normal(size=(_true_rank, 64)))
    _u, _s, _vt = np.linalg.svd(_dW)
    _ranks = np.arange(1, 33)
    _errs = [
        float(np.linalg.norm(_dW - (_u[:, :r] * _s[:r]) @ _vt[:r, :]) / np.linalg.norm(_dW))
        for r in _ranks
    ]
    _fig, _ax = plt.subplots(figsize=(7, 3.2))
    _ax.plot(_ranks, _errs, "o-", color="#4C72B0")
    _ax.axvline(_true_rank, color="#C44E52", ls="--", lw=2,
                label=f"true rank = {_true_rank}")
    _ax.set_xlabel("LoRA rank r")
    _ax.set_ylabel("reconstruction error")
    _ax.set_title("Low-rank is enough (if the update is low-rank)")
    _ax.grid(alpha=0.3)
    _ax.legend()
    _fig.tight_layout()
    _fig
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    紅線處誤差歸零：更新矩陣的「本質秩」只有 8，$r \geq 8$ 就能完整重建。
    SFT 要教的行為改變（格式、語氣、聽指令）經驗上就是低秩的——
    所以小小的 $r$ 通常夠用。

    ## 6️⃣ 招牌實驗：親手 SFT 一個迷你語言模型

    接下來的模型**完全在你的瀏覽器裡**用 numpy 訓練（約 1.1 萬個參數、
    字元級、8 字元上下文的小神經網路）。流程完全對應真實 LLM：

    1. **預訓練**：在一段通用英文短句語料上學「接下一個字」（載入時已自動跑完）
    2. **SFT**：從預訓練權重出發，在第 2️⃣ 節那 16 筆 QA 資料上微調
    3. **對比**：同一個問題，看 base 模型 vs SFT 後模型的回應

    先看預訓練的成果：
    """
    )
    return


@app.cell
def _(sft_pairs):
    # 語料：預訓練 = 通用短句；SFT = 模板化 QA（q:/a: 格式）
    pretrain_text = (
        "the sun is bright and the sky is wide. "
        "a cat sat on the warm stone and the dog ran in the grass. "
        "rain falls on the trees and the river runs to the sea. "
        "birds sing in the morning and the moon shines at night. "
        "the fish swim in cold water and the wind moves the clouds. "
        "we walk on the road and see the green hills far away. "
        "fire is hot and ice is cold. snow is white and grass is green. "
        "the little bird has two legs and the old cat has four legs. "
        "seven days make a week and the sun rises every day. "
        "the water in the sea is deep and the light of the sun is warm. "
    ) * 3

    sft_text = "".join(f"q: {q}\na: {a}\n\n" for q, a in sft_pairs) * 6

    # 答案遮罩：只有 "a: " 之後（含換行前）的字元是「要學的目標」
    answer_mask = []
    _in_answer = False
    _i = 0
    while _i < len(sft_text):
        if sft_text[_i : _i + 3] == "a: ":
            answer_mask += [False, False, False]
            _in_answer = True
            _i += 3
            continue
        if sft_text[_i] == "\n" and _in_answer:
            # 回合結束符（換行）也要算 loss——對應真實 SFT 把 <|im_end|> 納入目標，
            # 否則模型學會回答卻學不會「停」
            answer_mask.append(True)
            _in_answer = False
            _i += 1
            continue
        answer_mask.append(_in_answer)
        _i += 1
    return answer_mask, pretrain_text, sft_text


@app.cell
def _(np, pretrain_text, sft_text):
    # ── 迷你字元級語言模型（純 numpy）────────────────────────
    CTX = 16           # 上下文長度：看前 16 個字元（要裝得下問題的關鍵字）
    EMB, HID = 16, 64  # 嵌入維度 / 隱藏層寬度

    chars = sorted(set(pretrain_text + sft_text))
    vocab = {c: i for i, c in enumerate(chars)}
    V = len(chars)

    def encode(s):
        return [vocab[c] for c in s.lower() if c in vocab]

    def init_params(seed=1):
        r = np.random.default_rng(seed)
        return {
            "E": r.normal(0, 0.08, (V, EMB)),
            "W1": r.normal(0, 0.08, (CTX * EMB, HID)),
            "b1": np.zeros(HID),
            "W2": r.normal(0, 0.08, (HID, V)),
            "b2": np.zeros(V),
        }

    def forward(p, X):
        e = p["E"][X].reshape(len(X), -1)          # [B, CTX*EMB]
        h = np.tanh(e @ p["W1"] + p["b1"])         # [B, HID]
        logits = h @ p["W2"] + p["b2"]             # [B, V]
        return e, h, logits

    def train(p, text, steps, lr=0.35, batch=64, seed=2, target_mask=None):
        """SGD 訓練；target_mask[i]=False 的位置不計 loss（= loss masking）"""
        p = {k: v.copy() for k, v in p.items()}
        ids = np.array([vocab[c] for c in text])
        ok = np.arange(CTX, len(ids))
        if target_mask is not None:
            ok = ok[np.array(target_mask)[CTX:]]   # 只在答案字元上學
        r = np.random.default_rng(seed)
        losses = []
        for _ in range(steps):
            pos = r.choice(ok, size=batch)
            X = np.stack([ids[i - CTX : i] for i in pos])
            y = ids[pos]
            e, h, logits = forward(p, X)
            z = logits - logits.max(1, keepdims=True)
            probs = np.exp(z) / np.exp(z).sum(1, keepdims=True)
            losses.append(float(-np.log(probs[np.arange(batch), y] + 1e-9).mean()))
            d = probs
            d[np.arange(batch), y] -= 1
            d /= batch
            gW2 = h.T @ d
            gb2 = d.sum(0)
            dh = (d @ p["W2"].T) * (1 - h * h)
            gW1 = e.T @ dh
            gb1 = dh.sum(0)
            de = (dh @ p["W1"].T).reshape(batch, CTX, EMB)
            p["W2"] -= lr * gW2
            p["b2"] -= lr * gb2
            p["W1"] -= lr * gW1
            p["b1"] -= lr * gb1
            np.add.at(p["E"], X.reshape(-1), -lr * de.reshape(-1, EMB))
        return p, losses

    def generate(p, prompt, n=60, temp=0.6, seed=7):
        r = np.random.default_rng(seed)
        ids = encode(prompt)
        ids = ([vocab[" "]] * CTX + ids)[-max(CTX, len(ids) + CTX):]
        out = []
        for _ in range(n):
            X = np.array([ids[-CTX:]])
            _, _, logits = forward(p, X)
            z = logits[0] / temp
            z -= z.max()
            probs = np.exp(z) / np.exp(z).sum()
            nxt = int(r.choice(len(probs), p=probs))
            ids.append(nxt)
            out.append(chars[nxt])
            if chars[nxt] == "\n":
                break  # 回合結束符＝迷你版 <|im_end|>
        return "".join(out)
    return encode, generate, init_params, train, vocab


@app.cell
def _(init_params, plt, pretrain_text, train):
    # 預訓練：通用語料、不遮罩（每個字元都是學習目標）
    params_base, pretrain_losses = train(
        init_params(), pretrain_text, steps=1500, seed=3
    )
    _fig, _ax = plt.subplots(figsize=(7, 3))
    _ax.plot(pretrain_losses, color="#4C72B0", lw=1)
    _ax.set_xlabel("pretraining step")
    _ax.set_ylabel("cross-entropy loss")
    _ax.set_title("Pretraining: learning to predict the next character")
    _ax.grid(alpha=0.3)
    _fig.tight_layout()
    _fig
    return (params_base,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    loss 有下降 = 模型學會了這批語料的統計規律。現在做 SFT——
    兩個旋鈕都會**即時重新訓練**（在你的瀏覽器裡，約 1–2 秒）：

    - **SFT 步數**：拉到 0 = 完全沒微調的 base 模型
    - **Loss masking**：關掉它，模型會把力氣分去學「怎麼出題」（第 4️⃣ 節的概念驗證）
    """
    )
    return


@app.cell
def _(mo):
    sft_steps = mo.ui.slider(
        start=0, stop=1200, step=100, value=800, label="SFT 步數",
        show_value=True,
    )
    mask_on = mo.ui.switch(value=True, label="Loss masking（只在回答上算 loss）")
    mo.hstack([sft_steps, mask_on], justify="start", gap=2)
    return mask_on, sft_steps


@app.cell
def _(answer_mask, mask_on, mo, params_base, plt, sft_steps, sft_text, train):
    if sft_steps.value > 0:
        params_sft, sft_losses = train(
            params_base, sft_text, steps=sft_steps.value, lr=0.25, seed=4,
            target_mask=answer_mask if mask_on.value else None,
        )
        _fig, _ax = plt.subplots(figsize=(7, 3))
        _ax.plot(sft_losses, color="#55A868", lw=1)
        _ax.set_xlabel("SFT step")
        _ax.set_ylabel("cross-entropy loss")
        _ax.set_title(
            f"SFT ({sft_steps.value} steps, masking "
            f"{'ON' if mask_on.value else 'OFF'})"
        )
        _ax.grid(alpha=0.3)
        _fig.tight_layout()
        _out = _fig
    else:
        params_sft = params_base
        _out = mo.md("SFT 步數 = 0：右邊的「SFT 後」就是原始 base 模型。")
    _out
    return (params_sft,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""**見證時刻**——同一個問題，base vs SFT 後：""")
    return


@app.cell
def _(mo):
    ask = mo.ui.text(
        value="what color is the sky?", label="你的問題（英文小寫）",
        full_width=True,
    )
    ask
    return (ask,)


@app.cell
def _(ask, generate, mo, params_base, params_sft):
    _prompt = f"q: {ask.value}\na: "
    _before = generate(params_base, _prompt, n=50)
    _after = generate(params_sft, _prompt, n=50)

    def _panel(title, text, color):
        return mo.Html(
            f'<div style="border:2px solid {color};border-radius:10px;'
            f'padding:10px 14px;min-height:90px">'
            f'<div style="font-weight:800;color:{color};font-size:13px">{title}</div>'
            f'<pre style="margin:6px 0 0;white-space:pre-wrap;font-size:13px">'
            f"q: {ask.value}\na: {text}</pre></div>"
        )

    mo.hstack(
        [
            _panel("BASE（只會續寫）", _before, "#9AA3A8"),
            _panel("SFT 後（學會回答）", _after, "#55A868"),
        ],
        widths="equal", gap=1,
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    幾個值得動手驗證的觀察：

    - 問**訓練過**的問題（如 `what color is grass?`）：SFT 後幾乎每次答對
    - 問**沒訓練過但同格式**的問題（如 `what color is the sea?`）：它會用正確
      格式答，但內容可能亂掰——**SFT 教的是「行為」，不是「知識」**，
      知識主要來自預訓練。這也是幻覺（hallucination）的縮影
    - SFT 後的模型**答完會自己停**——因為我們把「答案後的換行」也算進 loss，
      它就是迷你版的 `<|im_end|>` 結束符。沒學結束符的模型會答對然後一路瞎講
      （這是真實 SFT 常見的 bug，本課開發時也踩了一次）
    - 把 **SFT 步數拉到 0**：右欄退化成瞎接話的 base 模型
    - 關掉 **loss masking** 再看：模型會開始自己「出題」，因為它把學習力
      分給了問題部分

    ## 7️⃣ 練習：換你動手

    1. 在第 2️⃣ 節的 `sft_pairs` 加 3–5 筆你自己的 QA（記得用小寫英文），
       重跑後測試模型學不學得會
    2. 把 SFT 的學習率 `lr=0.25` 改大（如 1.0）觀察 loss 曲線會發生什麼事
    3. 思考題：如果 SFT 資料裡混進了錯誤答案（如 `the sky is green.`），
       模型會怎樣？——這就是為什麼 SFT 資料品質比數量重要

    ---

    ### 🚀 想跑真的？GPU 軌道

    這裡的迷你模型是概念教具。**真實版**（transformers + peft、0.5B 模型、
    LoRA、真的 loss masking）在本課的 GPU notebook `sft_gpu.py`——
    回到左側教學頁最後一節，跟著步驟在 molab 用雲端 GPU 跑一遍。
    """
    )
    return


@app.cell
def _(encode, generate, params_sft):
    # ===== 你的實驗區 =====
    # 例：直接用程式呼叫 SFT 後的模型
    my_prompt = "q: what do cats say?\na: "
    print(my_prompt + generate(params_sft, my_prompt, n=40))
    print(f"(詞表大小 = {len(encode('abcdefghijklmnopqrstuvwxyz .?:,'))} 個已知字元)")
    return


if __name__ == "__main__":
    app.run()
