import marimo

__generated_with = "0.23.16"
app = marimo.App(width="medium", app_title="微調入門：LoRA 與 SFT、DPO（實驗場）")


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    # 🧪 微調入門：LoRA 與 SFT、DPO（實驗場）

    這是本課的**實驗場**。左側教學讀到哪，就回到這裡動手做——
    每一格程式碼都可以**直接修改、立即重跑**（點格子右上的 ▶，或按 `Ctrl+Enter`）。
    改壞了也沒關係：重新整理頁面就會回到原版。

    真正的微調要在有 GPU 的機器上跑；這裡不訓練模型，而是把 **LoRA 的每一個參數**
    ——`r`、`lora_alpha`、`target_modules`——算給你看，讓你知道自己在調什麼。
    """
    )
    return


@app.cell
def _():
    import marimo as mo
    return (mo,)


@app.cell
def _():
    # 科學套件與工具集中在這格 import
    import json
    from html import escape

    import matplotlib.pyplot as plt
    import numpy as np
    return escape, json, np, plt


@app.cell
def _():
    # 課程語義色：W（凍結的教科書）藍、adapter（便利貼）橘、好的綠、差的紅
    C_W = "#3D6B8F"
    C_LORA = "#E0913C"
    C_GOOD = "#55A868"
    C_BAD = "#C44E52"
    return C_BAD, C_GOOD, C_LORA, C_W


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 1️⃣ 便利貼有多小：參數量計算器

    Transformer 每一層都有好幾個 `d × d` 的方陣 W。**全參數微調**要更新整個 W；
    **LoRA** 把 W 凍結，另外掛兩個小矩陣 `B(d×r)` 與 `A(r×d)`，只訓練這兩個。

    拉拉看下面兩根拉桿——注意右邊那張圖的 y 軸是**對數刻度**，不然 LoRA 那根柱子會矮到看不見。
    記憶體那欄是粗估：每個**可訓練**參數在訓練時還要多帶梯度與優化器狀態（這裡以 3 份 fp32 計）。
    """
    )
    return


@app.cell
def _(mo):
    dim_slider = mo.ui.slider(
        start=512, stop=8192, step=512, value=4096,
        label="模型維度 d（W 是 d×d）", show_value=True,
    )
    rank_slider = mo.ui.slider(
        start=1, stop=64, step=1, value=16,
        label="LoRA rank r", show_value=True,
    )
    mo.vstack([dim_slider, rank_slider])
    return dim_slider, rank_slider


@app.cell
def _(C_LORA, C_W, dim_slider, plt, rank_slider):
    d_dim = dim_slider.value
    r_rank = rank_slider.value
    full_params = d_dim * d_dim          # 全參數微調：整個 W
    lora_trainable = 2 * d_dim * r_rank  # LoRA：B(d×r) + A(r×d)
    shrink = full_params / lora_trainable
    STATE_BYTES = 12  # 梯度 + 兩份優化器狀態，各 fp32（4 bytes）

    _fig, _axes = plt.subplots(1, 2, figsize=(8.2, 3.5))
    _names = ["Full FT", f"LoRA r={r_rank}"]
    _colors = [C_W, C_LORA]

    _vals = [full_params, lora_trainable]
    _axes[0].bar(_names, _vals, color=_colors, edgecolor="#1C2B33", linewidth=1.2)
    _axes[0].set_yscale("log")
    _axes[0].set_ylabel("trainable params (log)")
    _axes[0].set_title(f"One d x d layer, d={d_dim}")
    for _i, _v in enumerate(_vals):
        _axes[0].text(_i, _v * 1.5, f"{_v:,}", ha="center", fontsize=9, fontweight="bold")
    _axes[0].set_ylim(top=max(_vals) * 12)

    _mem = [v * STATE_BYTES / 2**20 for v in _vals]
    _axes[1].bar(_names, _mem, color=_colors, edgecolor="#1C2B33", linewidth=1.2)
    _axes[1].set_yscale("log")
    _axes[1].set_ylabel("grad + optimizer state (MiB, log)")
    _axes[1].set_title(f"LoRA is {shrink:.0f}x smaller")
    for _i, _v in enumerate(_mem):
        _axes[1].text(_i, _v * 1.5, f"{_v:,.1f}", ha="center", fontsize=9, fontweight="bold")
    _axes[1].set_ylim(top=max(_mem) * 12)

    _fig.tight_layout()
    _fig
    return STATE_BYTES, d_dim, full_params, lora_trainable, r_rank, shrink


@app.cell(hide_code=True)
def _(STATE_BYTES, d_dim, full_params, lora_trainable, mo, r_rank, shrink):
    mo.md(
        f"""
    **d = {d_dim}、r = {r_rank}** 時，一層的帳是這樣：

    - 全參數微調要更新 **{full_params:,}** 個參數，訓練時光是梯度與優化器狀態就要
      **{full_params * STATE_BYTES / 2**20:,.0f} MiB**——而這只是**一層的一個矩陣**。
    - LoRA 只訓練 **{lora_trainable:,}** 個（B 加 A），對應
      **{lora_trainable * STATE_BYTES / 2**20:,.1f} MiB**。
    - 縮小 **{shrink:.0f} 倍**。r 減半、倍數就加倍——這條線性關係是你調 `r` 時最直接的成本感。

    W 凍結不動，所以它完全不佔訓練記憶體那一份帳；存下來的 adapter 也只有 B 與 A，
    幾 MB 的檔案就能寄給同事——這就是「便利貼」的實際重量。
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 2️⃣ 力道拉桿：W′ = W + (α / r) · B · A

    ΔW 不是「裸加」回去的，前面有一個 **α / r** 的縮放係數。兩根拉桿一起玩：

    - **α 越大 → 越強**（係數的分子）
    - **r 越小 → 越強**（係數的分母）

    左圖是不同 α 之下、力道隨 r 的變化曲線，空心圈是你現在選的組合；右圖把幾個常見設定並排比較。
    注意曲線不是直直往下掉：係數是 α/r，但 B·A 本身是 r 個小矩陣疊起來的，r 越大它自己越大——
    兩邊抵銷之後，實際力道大約隨 **α / √r** 變化。這正是「rank 改變時幅度自動調、不會參數多就更新猛」的意思。
    """
    )
    return


@app.cell
def _(mo):
    alpha_slider = mo.ui.slider(
        start=1, stop=64, step=1, value=16,
        label="lora_alpha α", show_value=True,
    )
    rank2_slider = mo.ui.slider(
        start=1, stop=64, step=1, value=16,
        label="rank r", show_value=True,
    )
    mo.vstack([alpha_slider, rank2_slider])
    return alpha_slider, rank2_slider


@app.cell
def _(np):
    TOY_DIM = 256  # 玩具尺寸：真實 d=4096 的矩陣在瀏覽器裡太肥，行為一樣

    def delta_w(alpha, rank, dim=TOY_DIM, seed=0):
        """回傳 (α/r)·B·A —— 一次隨機初始化之後的更新量（固定 seed 才能公平比較）。"""
        _g = np.random.default_rng(seed)
        _B = _g.normal(0, 0.02, (dim, rank))
        _A = _g.normal(0, 0.02, (rank, dim))
        return (alpha / rank) * (_B @ _A)

    def strength(alpha, rank):
        return float(np.linalg.norm(delta_w(alpha, rank)))
    return TOY_DIM, delta_w, strength


@app.cell
def _(C_BAD, C_LORA, C_W, alpha_slider, plt, rank2_slider, strength):
    a_now = alpha_slider.value
    r_now = rank2_slider.value
    base_strength = strength(16, 16)   # 基準：α=16, r=16
    now_strength = strength(a_now, r_now)

    _ranks = [1, 2, 4, 8, 16, 32, 64]
    _fig2, _ax2 = plt.subplots(1, 2, figsize=(8.2, 3.5))

    for _alpha, _c, _ls in [(8, C_W, ":"), (16, C_LORA, "-"), (32, C_BAD, "--")]:
        _ax2[0].plot(
            _ranks, [strength(_alpha, _r) for _r in _ranks],
            marker="o", markersize=4, color=_c, linestyle=_ls, label=f"alpha={_alpha}",
        )
    _ax2[0].scatter([r_now], [now_strength], s=140, facecolor="none",
                    edgecolor="#1C2B33", linewidth=2, zorder=5, label="your setting")
    _ax2[0].set_xscale("log", base=2)
    _ax2[0].set_xticks(_ranks)
    _ax2[0].set_xticklabels([str(_r) for _r in _ranks])
    _ax2[0].set_xlabel("rank r")
    _ax2[0].set_ylabel("||delta W||")
    _ax2[0].set_title("Update strength ~ alpha / sqrt(r)")
    _ax2[0].legend(fontsize=8)
    _ax2[0].grid(alpha=0.25)

    _labels = ["a=16\nr=16", f"a={a_now}\nr={r_now}", "a=32\nr=16", "a=16\nr=4"]
    _vals2 = [base_strength, now_strength, strength(32, 16), strength(16, 4)]
    _bars = _ax2[1].bar(_labels, _vals2,
                        color=[C_W, "#1C2B33", C_BAD, C_LORA],
                        edgecolor="#1C2B33", linewidth=1.2)
    _ax2[1].axhline(base_strength, color=C_W, linestyle=":", linewidth=1.5)
    _ax2[1].set_ylabel("||delta W||")
    _ax2[1].set_title("vs baseline (alpha=16, r=16)")
    for _b, _v in zip(_bars, _vals2):
        _ax2[1].text(_b.get_x() + _b.get_width() / 2, _v * 1.02,
                     f"{_v / base_strength:.2f}x", ha="center", fontsize=9, fontweight="bold")
    _ax2[1].set_ylim(top=max(_vals2) * 1.22)

    _fig2.tight_layout()
    _fig2
    return a_now, base_strength, now_strength, r_now


@app.cell
def _(a_now, base_strength, mo, now_strength, np, r_now):
    # B 初始化為零：掛上 adapter 的那一刻，ΔW 逐格都是 0（下面直接驗給你看）
    _B0 = np.zeros((256, r_now))
    _A0 = np.random.default_rng(1).normal(0, 0.02, (r_now, 256))
    _max_at_step0 = float(np.abs((a_now / r_now) * (_B0 @ _A0)).max())

    mo.md(
        f"""
    你選的是 **α = {a_now}、r = {r_now}** → 縮放係數 α/r = **{a_now / r_now:.3f}**，
    力道 ‖ΔW‖ = **{now_strength:.4f}**，是基準（α=16, r=16, ‖ΔW‖={base_strength:.4f}）的
    **{now_strength / base_strength:.2f} 倍**。

    再看一件很重要的事：**B 一開始是零矩陣**。所以掛上 adapter 的第一步，
    不管 α 和 r 設多少，ΔW 每一格都是 0——
    上面用你現在的設定實際算了一次，`max|ΔW| = {_max_at_step0:.1f}`。

    這代表 adapter 掛上去的當下，模型行為與原本**完全一致**，之後才從 0 慢慢長出來。
    也因為更新量從零開始、又被 α/r 壓著，LoRA **不需要額外的正規化層**——
    W 已經帶著預訓練時的正規化，α/r 就足以控制力道。

    > 怕把模型練壞？**α 小、r 大**，更新最溫和。
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 3️⃣ 為什麼可以假設 ΔW 是低秩的

    LoRA 的整個賭注只有一句話：**微調帶來的更新量 ΔW 是低秩的**——
    它只往少數幾個方向動，所以用 `B×A` 這種「r 個方向」的形狀就描述得完。

    下面拿兩個 64×64 的矩陣對照：一個是**有結構的更新**（少數幾個方向疊起來，
    加上一點雜訊——這是教學用的合成矩陣，真實模型的 ΔW 沒辦法在瀏覽器裡算，但味道就是這樣），
    另一個是**純亂數矩陣**。左圖是它們的奇異值（每個方向有多重要），右圖是「只留前 r 個方向」的還原誤差。

    拉動下面的拉桿，看你需要幾個方向才夠。
    """
    )
    return


@app.cell
def _(np):
    # 兩個對照矩陣（固定 seed，重跑結果一樣）
    _g3 = np.random.default_rng(7)
    _t = np.linspace(0, 1, 64)
    _u = [np.sin(np.pi * _t), np.cos(2 * np.pi * _t), np.sin(3 * np.pi * _t), _t - 0.5]
    _v = [np.cos(np.pi * _t), np.sin(2 * np.pi * _t), _t**2 - 0.3, np.cos(4 * np.pi * _t)]
    _w = [1.0, 0.55, 0.3, 0.15]

    M_task = sum(_wi * np.outer(_ui, _vi) for _wi, _ui, _vi in zip(_w, _u, _v))
    M_task = M_task / np.linalg.norm(M_task)
    M_task = M_task + (0.05 / 64) * _g3.normal(size=(64, 64))  # 約 5% 相對雜訊

    M_rand = _g3.normal(size=(64, 64))
    M_rand = M_rand / np.linalg.norm(M_rand)

    S_task = np.linalg.svd(M_task, compute_uv=False)
    S_rand = np.linalg.svd(M_rand, compute_uv=False)

    def rank_error(M, rank):
        """只留前 rank 個奇異方向重建，回傳相對誤差。"""
        _U, _S, _Vt = np.linalg.svd(M)
        _Mr = (_U[:, :rank] * _S[:rank]) @ _Vt[:rank]
        return float(np.linalg.norm(M - _Mr) / np.linalg.norm(M))
    return M_rand, M_task, S_rand, S_task, rank_error


@app.cell
def _(mo):
    svd_rank = mo.ui.slider(
        start=1, stop=32, step=1, value=4,
        label="只留前 r 個方向", show_value=True,
    )
    svd_rank
    return (svd_rank,)


@app.cell
def _(C_LORA, C_W, M_rand, M_task, S_rand, S_task, plt, rank_error, svd_rank):
    r_svd = svd_rank.value
    err_task = rank_error(M_task, r_svd)
    err_rand = rank_error(M_rand, r_svd)

    _fig3, _ax3 = plt.subplots(1, 2, figsize=(8.2, 3.5))
    _ax3[0].plot(range(1, 33), S_task[:32] / S_task[0], marker="o", markersize=3,
                 color=C_LORA, label="structured update")
    _ax3[0].plot(range(1, 33), S_rand[:32] / S_rand[0], marker="s", markersize=3,
                 color=C_W, label="random matrix")
    _ax3[0].set_yscale("log")
    _ax3[0].set_xlabel("singular value index")
    _ax3[0].set_ylabel("relative magnitude (log)")
    _ax3[0].set_title("How fast the directions die out")
    _ax3[0].legend(fontsize=8)
    _ax3[0].grid(alpha=0.25)

    _rs = list(range(1, 33))
    _ax3[1].plot(_rs, [rank_error(M_task, _r) for _r in _rs], color=C_LORA, label="structured update")
    _ax3[1].plot(_rs, [rank_error(M_rand, _r) for _r in _rs], color=C_W, label="random matrix")
    _ax3[1].axvline(r_svd, color="#1C2B33", linestyle=":", linewidth=1.5)
    _ax3[1].scatter([r_svd, r_svd], [err_task, err_rand], s=60, zorder=5,
                    color=["#1C2B33", "#1C2B33"])
    _ax3[1].set_xlabel("rank r kept")
    _ax3[1].set_ylabel("relative reconstruction error")
    _ax3[1].set_title(f"r={r_svd}: {err_task:.1%} vs {err_rand:.1%}")
    _ax3[1].legend(fontsize=8)
    _ax3[1].grid(alpha=0.25)

    _fig3.tight_layout()
    _fig3
    return err_rand, err_task, r_svd


@app.cell
def _(S_task, err_rand, err_task, mo, np, r_svd):
    _energy4 = float((S_task[:4] ** 2).sum() / (S_task**2).sum())
    mo.md(
        f"""
    只留前 **{r_svd}** 個方向時：有結構的更新誤差只有 **{err_task:.1%}**，
    純亂數矩陣卻還有 **{err_rand:.1%}**。

    差別在左圖：有結構的矩陣，奇異值幾格就掉到地板
    （前 4 個方向就吃下 **{_energy4:.1%}** 的能量，前 6 個是 {np.round(S_task[:6] / S_task[0], 3).tolist()}）；
    亂數矩陣的奇異值幾乎一樣高，你留多少個方向都還原不了它。

    **LoRA 賭的就是「微調的更新比較像左邊那條線」**——實務上這個賭注多半成立，
    所以 r 用 **8 或 16** 就夠用，不必給到幾百。反過來說，如果你的任務真的要模型
    大改（學一整個新領域），那就是這個假設開始吃緊的時候，r 要往上加。
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 4️⃣ target_modules：便利貼要貼在哪幾頁

    一個 Transformer layer 裡不只一個線性層。`target_modules` 決定你在哪幾個矩陣上掛 adapter，
    參數量差很多：

    ```python
    model = FastLanguageModel.get_peft_model(
        model,
        r=16, lora_alpha=16, lora_dropout=0,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                        "gate_proj", "up_proj", "down_proj"],   # ← 這一行
        use_gradient_checkpointing="unsloth",
        random_state=3407,
    )
    ```

    下面用 `d=4096`、MLP 中間層 `4d`、32 層來算三種常見選法。
    注意 `gate_proj`／`up_proj` 是 `d → 4d` 的大矩陣、`down_proj` 是 `4d → d`——
    這三個一掛上去，參數量就會跳一階。
    """
    )
    return


@app.cell
def _(mo):
    tm_rank = mo.ui.slider(
        start=1, stop=128, step=1, value=16,
        label="rank r", show_value=True,
    )
    tm_rank
    return (tm_rank,)


@app.cell
def _(C_GOOD, C_LORA, C_W, plt, tm_rank):
    TM_D = 4096
    TM_FF = 4 * TM_D
    TM_LAYERS = 32
    r_tm = tm_rank.value

    MODULES = {
        "q_proj": (TM_D, TM_D), "k_proj": (TM_D, TM_D),
        "v_proj": (TM_D, TM_D), "o_proj": (TM_D, TM_D),
        "gate_proj": (TM_FF, TM_D), "up_proj": (TM_FF, TM_D), "down_proj": (TM_D, TM_FF),
    }
    PRESETS = {
        "q,v only": ["q_proj", "v_proj"],
        "all attention": ["q_proj", "k_proj", "v_proj", "o_proj"],
        "all-linear": list(MODULES),
    }

    def adapter_params(shape, rank):
        """一個 out×in 的線性層掛 LoRA 要幾個參數：A(r×in) + B(out×r)。"""
        _out, _in = shape
        return rank * _in + _out * rank

    dense_per_layer = sum(_o * _i for _o, _i in MODULES.values())
    preset_params = {
        _name: sum(adapter_params(MODULES[_m], r_tm) for _m in _sel)
        for _name, _sel in PRESETS.items()
    }

    _fig4, _ax4 = plt.subplots(figsize=(8.2, 3.2))
    _names4 = list(preset_params)
    _vals4 = [preset_params[_n] * TM_LAYERS for _n in _names4]
    _bars4 = _ax4.barh(_names4, _vals4, color=[C_W, C_GOOD, C_LORA],
                       edgecolor="#1C2B33", linewidth=1.2)
    for _b, _n, _v in zip(_bars4, _names4, _vals4):
        _ax4.text(_v * 1.02, _b.get_y() + _b.get_height() / 2,
                  f"{_v:,}  ({preset_params[_n] / dense_per_layer:.2%} of layer weights)",
                  va="center", fontsize=9)
    _ax4.set_xlim(right=max(_vals4) * 1.75)
    _ax4.set_xlabel(f"trainable params over {TM_LAYERS} layers (r={r_tm}, d={TM_D})")
    _ax4.set_title("Where you stick the sticky notes")
    _fig4.tight_layout()
    _fig4
    return MODULES, TM_LAYERS, adapter_params, dense_per_layer, preset_params, r_tm


@app.cell
def _(MODULES, TM_LAYERS, adapter_params, dense_per_layer, mo, preset_params, r_tm):
    _mlp = sum(adapter_params(MODULES[_m], r_tm) for _m in ("gate_proj", "up_proj", "down_proj"))
    _attn = sum(adapter_params(MODULES[_m], r_tm) for _m in ("q_proj", "k_proj", "v_proj", "o_proj"))
    mo.md(
        f"""
    r = {r_tm} 時，一層的帳（總權重 {dense_per_layer:,}）：

    - `["q_proj","v_proj"]`：**{preset_params["q,v only"]:,}**／層
      ——原論文做法，最少修改、最省資源。
    - attention 全掛（q,k,v,o）：**{preset_params["all attention"]:,}**／層——效果好一些，但 MLP 完全沒動。
    - `"all-linear"`：**{preset_params["all-linear"]:,}**／層
      ——主流做法。光是 MLP 那三個投影就佔 **{_mlp:,}**，比 attention 四個投影加起來（{_attn:,}）還多。

    整個模型（{TM_LAYERS} 層）的可訓練參數是上面數字乘以 {TM_LAYERS}。
    **怎麼選**：資料多、要學新知識 → `all-linear`（MLP 對知識儲存很重要，可調空間最大）；
    資料少、只想調語氣風格 → `q_proj, v_proj` 就夠。
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 5️⃣ 餵什麼資料：SFT 一問一答，DPO 一好一壞

    LoRA 決定「改哪些權重」，**資料**決定「往哪個方向改」。兩條主線路：

    - **SFT**（監督式微調）：給標準答案，讓模型模仿 → `prompt` + `response`
    - **DPO**（直接偏好最佳化）：給好壞對比，讓模型偏向較好的 → `prompt` + `chosen` + `rejected`

    下面這格把兩種 JSONL 各印一行真的出來（每行一筆，訓練腳本直接讀）。
    """
    )
    return


@app.cell
def _(escape, json, mo):
    sft_row = {
        "prompt": "用一句話介紹台北",
        "response": "台北是融合傳統與現代的臺灣首都。",
    }
    dpo_row = {
        "prompt": "用一句話介紹台北",
        "chosen": "台北是融合傳統與現代的臺灣首都。",
        "rejected": "台北就是個城市。",
    }
    _style = (
        "font-family:ui-monospace,Menlo,Consolas,monospace;font-size:12.5px;"
        "white-space:pre-wrap;word-break:break-all;background:#F0F4EE;"
        "border-radius:8px;padding:10px 12px;line-height:1.7;margin:6px 0 14px"
    )
    _cards = (
        "<div><b>train_sft.jsonl</b>（一問一答，只有正確示範）"
        f"<div style='{_style}'>{escape(json.dumps(sft_row, ensure_ascii=False))}</div></div>"
        "<div><b>train_dpo.jsonl</b>（偏好三元組，標的是相對好壞）"
        f"<div style='{_style}'>{escape(json.dumps(dpo_row, ensure_ascii=False))}</div></div>"
    )
    mo.Html(_cards)
    return dpo_row, sft_row


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ### β：把模型拉住的那條橡皮筋

    DPO 訓練時做兩件事：**拉高 chosen 的機率、壓低 rejected 的機率**，
    同時用一個**參考模型**（通常就是 SFT 完的那個模型）把你拉住，不讓模型為了討好偏好資料而跑太遠。
    `DPOConfig(beta=0.1)` 的 `beta` 就是那條橡皮筋的硬度。

    下面用一個極簡的教學模型讓你看見它：假設同一個 prompt 有四個候選回覆，
    參考模型原本給它們的機率是左邊那組柱子，人類偏好分數 R1 最高、R4 最低（就是那句「嗯。」）。
    拉動 β——

    - **β 小**（橡皮筋鬆）：機率幾乎全押到 R1，離參考模型很遠
    - **β 大**（橡皮筋硬）：分布只微微傾斜，模型幾乎沒動

    （真實 DPO 是在整段回覆的 token 機率上算，數值不會跟這裡一樣；要看的是**方向**。）
    """
    )
    return


@app.cell
def _(mo):
    beta_slider = mo.ui.slider(
        start=0.05, stop=2.0, step=0.05, value=0.5,
        label="beta β（橡皮筋硬度）", show_value=True,
    )
    beta_slider
    return (beta_slider,)


@app.cell
def _(C_BAD, C_GOOD, C_W, beta_slider, np, plt):
    REPLIES = ["R1\nchosen", "R2", "R3", "R4\nrejected"]
    PREF_SCORE = np.array([1.0, 0.6, 0.2, 0.0])   # 人類偏好分數
    P_REF = np.array([0.20, 0.30, 0.25, 0.25])    # 參考模型（SFT 後）的分布

    def tilted(beta):
        """偏好把分布往高分方向傾斜，β 越大傾斜越少（貼著參考模型）。"""
        _w = P_REF * np.exp(PREF_SCORE / beta)
        return _w / _w.sum()

    def drift(beta):
        """離參考模型多遠（KL）。"""
        _p = tilted(beta)
        return float(np.sum(_p * np.log(_p / P_REF)))

    beta_now = beta_slider.value
    p_new = tilted(beta_now)

    _fig5, _ax5 = plt.subplots(1, 2, figsize=(8.2, 3.5))
    _x = np.arange(4)
    _ax5[0].bar(_x - 0.2, P_REF, width=0.4, color=C_W,
                edgecolor="#1C2B33", linewidth=1.2, label="reference model")
    _ax5[0].bar(_x + 0.2, p_new, width=0.4,
                color=[C_GOOD, C_GOOD, C_BAD, C_BAD],
                edgecolor="#1C2B33", linewidth=1.2, label=f"after DPO (beta={beta_now:.2f})")
    _ax5[0].set_xticks(_x)
    _ax5[0].set_xticklabels(REPLIES, fontsize=8)
    _ax5[0].set_ylabel("probability")
    _ax5[0].set_title("chosen up, rejected down")
    _ax5[0].legend(fontsize=8)

    _betas = np.arange(0.05, 2.01, 0.05)
    _ax5[1].plot(_betas, [drift(_b) for _b in _betas], color=C_BAD)
    _ax5[1].scatter([beta_now], [drift(beta_now)], s=90, zorder=5, color="#1C2B33")
    _ax5[1].set_xlabel("beta")
    _ax5[1].set_ylabel("drift from reference (KL)")
    _ax5[1].set_title("bigger beta = shorter leash")
    _ax5[1].grid(alpha=0.25)

    _fig5.tight_layout()
    _fig5
    return P_REF, beta_now, drift, p_new


@app.cell
def _(P_REF, beta_now, drift, mo, p_new):
    mo.md(
        f"""
    β = **{beta_now:.2f}** 時：chosen 的機率 {P_REF[0]:.2f} → **{p_new[0]:.2f}**，
    rejected 的機率 {P_REF[3]:.2f} → **{p_new[3]:.2f}**，離參考模型的距離（KL）是 **{drift(beta_now):.3f}**。
    把 β 拉到 0.05 再看一次，你會看到分布整個塌到 R1 上——那就是「跑太遠」的樣子。

    最少幾百筆偏好對就能看到效果；重點不是量，是 **chosen / rejected 的差距要反映你在意的品質面向**。
    順序也別搞反：**先 SFT 打底，再收偏好對做 DPO**——沒有基本能力，偏好對齊也調不出好結果。

    ```python
    # DPO 最簡訓練（TRL）：pip install trl transformers datasets
    from datasets import load_dataset
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from trl import DPOConfig, DPOTrainer

    model_name = "Qwen/Qwen2.5-0.5B-Instruct"   # 先做過 SFT 的模型
    model = AutoModelForCausalLM.from_pretrained(model_name)
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    dataset = load_dataset("json", data_files="train_dpo.jsonl", split="train")

    config = DPOConfig(output_dir="dpo-out", beta=0.1)
    trainer = DPOTrainer(model=model, args=config,
                         train_dataset=dataset, processing_class=tokenizer)
    trainer.train()   # 沒指定 ref model 時，TRL 會自動複製一份當參考模型
    ```
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 6️⃣ 練習：換你動手

    下面這格是你的實驗區，改完按 ▶ 重跑。建議挑戰（由易到難）：

    1. **LEVEL 1**：把 1️⃣ 的 `r` 從 16 拉到 8，看縮小倍數變成幾倍；再把 `d` 拉到 8192，
       看全參數微調那根柱子跑到哪裡去。
    2. **LEVEL 2**：在 2️⃣ 找出一組 `(α, r)`，讓**力道跟基準（α=16, r=16）幾乎一樣**，
       但**可訓練參數是基準的 4 倍**。下面實驗區的 `my_alpha` / `my_rank` 可以直接算給你看。
    3. **LEVEL 3**：把 3️⃣ 那個「有結構的更新」改得更難壓縮（例如把 `_w` 四個權重都改成 1.0，
       或把雜訊從 `0.05/64` 加大十倍），再看 r=4 的誤差怎麼變——這對「該用多大的 r」意味著什麼？

    做完記得：**點右上角下載按鈕（或左側教學頁的「下載 .py」）把你的版本帶走**，
    在自己電腦用 `uvx marimo edit lesson.py` 就能繼續玩。
    """
    )
    return


@app.cell
def _(strength):
    # ===== 你的實驗區 =====
    # 改這兩個數字，跟基準（α=16, r=16）比比看力道與參數量
    my_alpha = 16
    my_rank = 16

    _base = strength(16, 16)
    _mine = strength(my_alpha, my_rank)
    print(f"α={my_alpha}, r={my_rank}")
    print(f"  力道 ‖ΔW‖ = {_mine:.4f}  （基準的 {_mine / _base:.2f} 倍）")
    print(f"  可訓練參數 = 基準的 {my_rank / 16:.2f} 倍")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.accordion(
        {
            "💡 LEVEL 1 參考解答": mo.md(
                r"""
    `r = 8` → 可訓練參數 `2 × 4096 × 8 = 65,536`，縮小 **256 倍**
    （r 減半、倍數加倍）。

    `d = 8192` 時全參數微調變成 `8192² = 67,108,864` 個參數、
    梯度＋優化器狀態約 **768 MiB**——而 LoRA（r=16）只有 `2 × 8192 × 16 = 262,144` 個、
    約 3 MiB。**模型越大，這個比例只會越誇張。**
    """
            ),
            "💡 LEVEL 2 參考解答": mo.md(
                r"""
    答案是 **α = 32、r = 64**。貼進上面的實驗區：

    ```python
    my_alpha = 32
    my_rank = 64
    ```

    你會看到力道 ≈ 基準的 **0.99 倍**（實質相同），但可訓練參數是基準的 **4 倍**。

    原理：力道大約隨 `α / √r` 走，r 從 16 變 64（√ 變 2 倍），α 也乘 2 就抵銷回來；
    而參數量是 `2·d·r`，直接跟著 r 變 4 倍。
    **這就是「參數多不等於更新猛」的實際樣子**——想更用力請調 α，不是無腦加 r。
    """
            ),
            "💡 LEVEL 3 提示": mo.md(
                r"""
    方向：把 3️⃣ 建矩陣那格的 `_w = [1.0, 0.55, 0.3, 0.15]` 改成 `[1.0, 1.0, 1.0, 1.0]`，
    奇異值不再快速衰減，前幾個方向吃下的能量變少；把雜訊改成 `(0.5 / 64)` 更明顯——
    雜訊本身是滿秩的，怎麼壓都壓不掉。

    **怎麼驗證你做對了**：看右圖橘線在 r=4 的誤差。原本約 4.6%，改完應該明顯上升；
    如果它幾乎沒動，代表你改的權重沒有真的讓方向變多（例如只改了雜訊卻改太小）。

    **意味著什麼**：ΔW 越「不低秩」，同樣的 r 就還原得越差 → 任務越是要模型學一整套新東西，
    r 就得往上加（或改用 `all-linear` 讓可調空間變大）。反過來，只是調語氣的任務，
    r=8 甚至更小都綽綽有餘。
    """
            ),
        }
    )
    return


if __name__ == "__main__":
    app.run()
