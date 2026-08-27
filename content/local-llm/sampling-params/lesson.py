import marimo

__generated_with = "0.23.16"
app = marimo.App(width="medium", app_title="取樣參數：模型怎麼挑下一個字（實驗場）")


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    # 🧪 取樣參數：模型怎麼挑下一個字（實驗場）

    這是本課的**實驗場**。左側教學讀到哪，就回到這裡動手做——
    每一格程式碼都可以**直接修改、立即重跑**（點格子右上的 ▶，或按 `Ctrl+Enter`）。
    改壞了也沒關係：重新整理頁面就會回到原版。

    這裡沒有真的語言模型：本課的重點是**取樣那一層**，
    它拿到的只是一排數字（logits）。所以我們直接給一排數字，
    把 `temperature`／`top_p`／`penalty` 的公式**原封不動算給你看**。
    """
    )
    return


@app.cell
def _():
    import marimo as mo
    return (mo,)


@app.cell
def _():
    # 科學套件集中在這格 import，回傳給全 notebook 用
    import matplotlib.pyplot as plt
    import numpy as np
    return np, plt


@app.cell
def _(np):
    # ── 全 notebook 共用的常數與唯一的核心函式 ──────────────────
    # 「今天天氣真___」的五個候選字。
    # 圖表標籤一律英文（瀏覽器裡的 matplotlib 沒有中文字型）：
    #   good=好　not bad=不錯　hot=熱　cold=冷　quantum=量子
    TOKENS = ["good", "not bad", "hot", "cold", "quantum"]

    # 模型真正吐出來的是 logit（未正規化的分數，可正可負）。
    # 這裡挑一組 logit，讓 T=1 時的機率落在 47% / 26% / 16% / 10% / 0.5%。
    LOGITS = np.log(np.array([0.45, 0.25, 0.15, 0.10, 0.005]))

    # 語義色：藍＝模型原始分佈、橘＝被參數改過的分佈、綠＝留下來的、紅＝被砍/被罰的
    BLUE, ORANGE, GREEN, RED = "#4C72B0", "#DD8452", "#55A868", "#C44E52"


    def softmax_t(logits, temperature):
        """把 logits 變成機率：P(token) ∝ exp(logit / T)。T 在分母，這是整堂課的關鍵。"""
        z = logits / max(temperature, 1e-6)
        z = z - z.max()  # 整排平移不改變結果，只是避免 exp 爆掉
        p = np.exp(z)
        return p / p.sum()

    return BLUE, GREEN, LOGITS, ORANGE, RED, TOKENS, softmax_t


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 1️⃣ 一顆不公平的骰子

    模型看到「今天天氣真」之後，**不會挑一個字**——它給每個候選字一個機率。
    真正挑字的是後面那一步：**照這組機率擲一次骰子**。

    這顆骰子五個面，但面積差很多：`good` 佔 47%，`quantum` 只佔 0.52%。
    拉動下面的次數，看看擲出來的實際次數怎麼慢慢貼近理論機率——
    順便盯著 `quantum`：**擲 200 次可能一次都不出現，擲 2000 次它就會冒出來十幾次**。
    這就是「模型偶爾講怪話」的來源：機率小不等於不會發生，只是要等。
    """
    )
    return


@app.cell
def _(mo):
    n_draws = mo.ui.slider(
        start=100, stop=3000, step=100, value=200,
        label="擲幾次骰子", show_value=True,
    )
    n_draws
    return (n_draws,)


@app.cell
def _(BLUE, LOGITS, ORANGE, TOKENS, n_draws, np, plt, softmax_t):
    _p = softmax_t(LOGITS, 1.0)
    _rng = np.random.default_rng(42)
    _draws = _rng.choice(len(TOKENS), size=n_draws.value, p=_p)
    _counts = np.bincount(_draws, minlength=len(TOKENS))
    _emp = _counts / n_draws.value

    _x = np.arange(len(TOKENS))
    _fig, _ax = plt.subplots(figsize=(7.4, 4.0))
    _ax.bar(_x - 0.2, _p, width=0.4, color=BLUE, label="model probability")
    _ax.bar(_x + 0.2, _emp, width=0.4, color=ORANGE,
            label=f"observed in {n_draws.value} rolls")
    for _i in _x:
        _ax.text(_i - 0.2, _p[_i] + 0.006, f"{_p[_i]:.1%}",
                 ha="center", fontsize=8.5, color=BLUE)
        _ax.text(_i + 0.2, _emp[_i] + 0.006, str(_counts[_i]),
                 ha="center", fontsize=8.5, color=ORANGE)
    _ax.set_xticks(_x)
    _ax.set_xticklabels(TOKENS)
    _ax.set_ylabel("probability / share")
    _ax.set_title("An unfair 5-sided die: theory vs actual rolls")
    _ax.legend(loc="upper right")
    _ax.grid(axis="y", alpha=0.3)
    _fig.tight_layout()
    _fig
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 2️⃣ temperature：把骰子壓尖或壓平

    只有一條公式，記住 **T 在分母**就夠了：

    $$P(\text{token}) \;\propto\; \exp\!\left(\frac{\text{logit}}{T}\right)$$

    - **T 小** ⇒ logit 差距被**放大** ⇒ 分佈變尖 ⇒ 幾乎只選第一名（保守、可重現）
    - **T 大** ⇒ logit 差距被**抹平** ⇒ 分佈變平 ⇒ 冷門字也有機會（有創意、每次不同）

    拉桿在下面。灰色虛線是 T=1 的原始分佈，橘色是現在這個 T——
    看的是**同一組 logit**，只是被同一個分母除過。三個值一定要拉去看：

    | T | 你會看到 | 適合 |
    |---|---|---|
    | 0.2 | `good` 吃掉 94.6%，其他幾乎歸零 | 抽取、分類、寫程式 |
    | 1.0 | 模型原本的想法 | 一般對話 |
    | 2.0 | `quantum` 從 0.5% 爬到 3.6%（七倍） | 創作、腦力激盪 |
    """
    )
    return


@app.cell
def _(mo):
    temperature = mo.ui.slider(
        start=0.05, stop=2.0, step=0.05, value=1.0,
        label="temperature (T)", show_value=True,
    )
    temperature
    return (temperature,)


@app.cell
def _(BLUE, LOGITS, ORANGE, TOKENS, np, plt, softmax_t, temperature):
    _p1 = softmax_t(LOGITS, 1.0)
    _pt = softmax_t(LOGITS, temperature.value)

    _x = np.arange(len(TOKENS))
    _fig, _ax = plt.subplots(figsize=(7.4, 4.0))
    _ax.bar(_x, _p1, width=0.62, facecolor="none", edgecolor=BLUE,
            linestyle="--", linewidth=1.4, label="T = 1.0 (original)")
    _ax.bar(_x, _pt, width=0.44, color=ORANGE,
            label=f"T = {temperature.value:.2f}")
    for _i in _x:
        _ax.text(_i, _pt[_i] + 0.012, f"{_pt[_i]:.1%}", ha="center",
                 fontsize=9, color=ORANGE, fontweight="bold")
    _ax.set_xticks(_x)
    _ax.set_xticklabels(TOKENS)
    _ax.set_ylim(0, 1.05)
    _ax.set_ylabel("probability")
    _ax.set_title(f"softmax(logit / T)  —  top-1 = {_pt.max():.1%}")
    _ax.legend(loc="upper right")
    _ax.grid(axis="y", alpha=0.3)
    _fig.tight_layout()
    _fig
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 3️⃣ top_p：把長尾直接砍掉

    temperature 是**改機率**，`top_p`（核採樣 / nucleus sampling）是**改名單**：

    1. 把候選字**照機率由大到小排序**
    2. 一路**累加**，累積機率**第一次跨過 p** 的那個字為止都留著
    3. 名單外的字**丟棄**（機率變成 0，不是變小——是抽不到了）
    4. 留下來的重新歸一化，在這個「核」裡面擲骰子

    T=1 時累積是 `0.471 → 0.733 → 0.890 → 0.995 → 1.0`。所以 `top_p=0.9` 會留下
    good / not bad / hot / cold 四個，**`quantum` 出局**。注意 `hot` 累積到 0.890
    只差 0.01 就跨過門檻——把 top_p 拉到 0.88，連 `cold` 都會被砍掉。

    下面給你**兩根**拉桿，正是為了讓你親眼看到那句實務建議的道理：
    **temperature 和 top_p 擇一調就好**。兩個都動，很難預測結果——
    T 拉高讓 `quantum` 變大，top_p 又立刻把它砍掉，兩個參數在互相抵銷。
    """
    )
    return


@app.cell
def _(mo):
    t_nuc = mo.ui.slider(
        start=0.05, stop=2.0, step=0.05, value=1.0,
        label="temperature", show_value=True,
    )
    top_p = mo.ui.slider(
        start=0.30, stop=1.0, step=0.01, value=0.9,
        label="top_p", show_value=True,
    )
    mo.hstack([t_nuc, top_p], justify="start", gap=2)
    return t_nuc, top_p


@app.cell
def _(GREEN, LOGITS, RED, TOKENS, np, plt, softmax_t, t_nuc, top_p):
    _p = softmax_t(LOGITS, t_nuc.value)
    _order = np.argsort(_p)[::-1]
    _sorted_p = _p[_order]
    _cum = np.cumsum(_sorted_p)
    # 累積第一次跨過 top_p 的位置也要留下 → 保留 k 個
    _k = int(np.searchsorted(_cum, top_p.value) + 1)
    _k = min(_k, len(_p))

    _kept = np.zeros(len(_p), dtype=bool)
    _kept[:_k] = True
    _renorm = np.where(_kept, _sorted_p / _sorted_p[:_k].sum(), 0.0)
    _labels = [TOKENS[i] for i in _order]
    _colors = [GREEN if _kept[i] else RED for i in range(len(_p))]
    _x = np.arange(len(_p))

    _fig, (_a1, _a2) = plt.subplots(1, 2, figsize=(9.6, 4.0))
    _a1.bar(_x, _sorted_p, color=_colors, width=0.55)
    _a1.plot(_x, _cum, color="#52646E", marker="o", linewidth=1.6,
             markersize=5, label="cumulative")
    _a1.axhline(top_p.value, color=RED, linestyle="--", linewidth=1.4,
                label=f"top_p = {top_p.value:.2f}")
    for _i in _x:
        _a1.text(_i, _cum[_i] + 0.035, f"{_cum[_i]:.3f}", ha="center",
                 fontsize=8, color="#52646E")
    _a1.set_xticks(_x)
    _a1.set_xticklabels(_labels, rotation=18, ha="right")
    _a1.set_ylim(0, 1.18)
    _a1.set_ylabel("probability")
    _a1.set_title(f"sorted + cumulative  (keep {_k} of {len(_p)})")
    _a1.legend(loc="lower right", fontsize=8.5)
    _a1.grid(axis="y", alpha=0.3)

    _a2.bar(_x, _renorm, color=_colors, width=0.55)
    for _i in _x:
        _a2.text(_i, _renorm[_i] + 0.02, f"{_renorm[_i]:.1%}", ha="center",
                 fontsize=8.5)
    _a2.set_xticks(_x)
    _a2.set_xticklabels(_labels, rotation=18, ha="right")
    _a2.set_ylim(0, 1.05)
    _a2.set_title("what you actually roll (renormalized)")
    _a2.grid(axis="y", alpha=0.3)
    _fig.tight_layout()
    _fig
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 4️⃣ penalty：在 logit 上直接扣分

    前兩個參數只看「這一步」。penalty 是唯一**會回頭看已經寫過什麼**的參數：

    $$\text{logit}' = \text{logit} \;-\; \text{freq\_penalty} \times (\text{出現次數}) \;-\; \text{pres\_penalty} \times (\text{出現過嗎，0 或 1})$$

    換一個場景：模型正在寫餐廳評論，八個候選詞，已經寫出
    **「很棒」×3、「不錯」×1、「推薦」×1**（圖上標成 `(x3)`）。兩種扣法差在哪：

    - **frequency_penalty**：按**次數**累加。「很棒」出現 3 次 → 扣 `3 × penalty`。
      出現越多次扣越重，**專治複讀機**。常用 0.3 ~ 0.7。
    - **presence_penalty**：出現過就扣**一次**（0/1）。出現 1 次和 10 次**扣一樣多**。
      它鼓勵的是「換沒講過的詞」，不是懲罰次數。常用 0.3 ~ 0.6，預設 0。

    把 frequency 拉到 0.5，「很棒」從 42.0% 掉到 16.6%；改成 presence 0.5，
    只掉到 35.2%——**同樣的數字，扣法不同，力道差一倍以上**。
    再把 frequency 拉到 2.0 看看：「很棒」剩 0.3%，`tasty`／`good service`
    這些本來冷門的詞硬被推上第一——這就是「penalty 開太高會開始說怪話」。
    """
    )
    return


@app.cell
def _(np):
    # 餐廳評論的八個候選詞（圖表用英文；very good=很棒 nice=不錯 recommend=推薦
    # tasty=好吃 good service=服務好 nice place=環境佳 good value=價格實惠 will return=會再來）
    GEN_TOKENS = ["very good", "nice", "recommend", "tasty",
                  "good service", "nice place", "good value", "will return"]
    GEN_BASE = np.array([0.42, 0.16, 0.12, 0.10, 0.08, 0.06, 0.04, 0.02])
    GEN_LOGITS = np.log(GEN_BASE)
    # 已經寫過的歷史：很棒 x3、不錯 x1、推薦 x1
    HISTORY = np.array([3.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0])
    return GEN_BASE, GEN_LOGITS, GEN_TOKENS, HISTORY


@app.cell
def _(mo):
    freq_pen = mo.ui.slider(
        start=0.0, stop=2.0, step=0.1, value=0.5,
        label="frequency_penalty", show_value=True,
    )
    pres_pen = mo.ui.slider(
        start=0.0, stop=2.0, step=0.1, value=0.5,
        label="presence_penalty", show_value=True,
    )
    mo.hstack([freq_pen, pres_pen], justify="start", gap=2)
    return freq_pen, pres_pen


@app.cell
def _(
    BLUE,
    GEN_BASE,
    GEN_LOGITS,
    GEN_TOKENS,
    HISTORY,
    ORANGE,
    freq_pen,
    np,
    plt,
    pres_pen,
    softmax_t,
):
    _penalized = (
        GEN_LOGITS
        - freq_pen.value * HISTORY
        - pres_pen.value * (HISTORY > 0)
    )
    _p_after = softmax_t(_penalized, 1.0)

    _labels = [
        f"{t}\n(x{int(c)})" if c > 0 else t
        for t, c in zip(GEN_TOKENS, HISTORY)
    ]
    _x = np.arange(len(GEN_TOKENS))
    _fig, _ax = plt.subplots(figsize=(9.6, 4.2))
    _ax.bar(_x - 0.2, GEN_BASE, width=0.4, color=BLUE, label="before penalty")
    _ax.bar(_x + 0.2, _p_after, width=0.4, color=ORANGE, label="after penalty")
    for _i in _x:
        _ax.text(_i - 0.2, GEN_BASE[_i] + 0.006, f"{GEN_BASE[_i]:.0%}",
                 ha="center", fontsize=8, color=BLUE)
        _ax.text(_i + 0.2, _p_after[_i] + 0.006, f"{_p_after[_i]:.0%}",
                 ha="center", fontsize=8, color=ORANGE)
    _ax.set_xticks(_x)
    _ax.set_xticklabels(_labels, fontsize=8.5)
    _ax.set_ylabel("probability")
    _ax.set_title(
        f"logit' = logit - {freq_pen.value:.1f}*count - {pres_pen.value:.1f}*seen"
        f"   |   'very good': {GEN_BASE[0]:.1%} -> {_p_after[0]:.1%}"
    )
    _ax.legend(loc="upper right")
    _ax.grid(axis="y", alpha=0.3)
    _fig.tight_layout()
    _fig
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 5️⃣ 真的寫一段：複讀機修好了嗎

    上一節只算了「下一步」。penalty 的威力要**連續寫下去**才看得出來——
    因為出現次數會一直累積，扣分也一直變重。

    下面這格真的跑生成迴圈：每一步照 penalty 後的分佈抽一個詞、把次數加上去、
    再算下一步。同時跑 **200 條長度 20 的序列**取平均，看兩個指標：

    - **最常出現字佔比**：20 個詞裡，最愛用的那個詞佔幾成 → **越低越不跳針**
    - **相異用字數**：八個詞用到幾個 → **越高用詞越多樣**

    四種設定同時跑（frequency / presence 用你上面那兩根拉桿的值）。
    預設值（各 0.5）跑出來大概是這樣——**注意 frequency 和 presence 壓的不是同一件事**：

    | 設定 | 最常出現字佔比 | 相異用字數 |
    |---|---|---|
    | 無 penalty | 約 0.43 | 約 6.2 / 8 |
    | frequency 0.5 | **約 0.26** | 約 7.4 / 8 |
    | presence 0.5 | 約 0.40（幾乎沒動） | 約 6.8 / 8 |
    | 兩個都開 0.5 | 約 0.25 | 約 7.7 / 8 |

    frequency 把「最愛用的詞」壓掉四成；presence 幾乎沒碰它，但把用字撐開了。
    這正是課本那兩句話的實際長相：**frequency 專治複讀機，presence 鼓勵換話題。**
    """
    )
    return


@app.cell
def _(GEN_LOGITS, np):
    def run_generation(freq_penalty, presence_penalty, temperature=1.0,
                       n_seq=200, n_step=20, seed=7):
        """真的跑生成迴圈：n_seq 條序列同時往前走（向量化，瀏覽器裡才夠快）。

        每一步：logit' = logit - freq*count - pres*(count>0) → softmax → 抽一個詞。
        回傳 (序列矩陣, 次數矩陣)。
        """
        rng = np.random.default_rng(seed)
        vocab = len(GEN_LOGITS)
        counts = np.zeros((n_seq, vocab))
        seqs = np.zeros((n_seq, n_step), dtype=int)
        for step in range(n_step):
            lg = (
                GEN_LOGITS[None, :]
                - freq_penalty * counts
                - presence_penalty * (counts > 0)
            )
            z = lg / max(temperature, 1e-6)
            z = z - z.max(axis=1, keepdims=True)
            p = np.exp(z)
            p /= p.sum(axis=1, keepdims=True)
            # 每一列用自己的機率抽一個：累積機率 + 一個亂數，全部向量化
            pick = np.minimum((np.cumsum(p, axis=1) < rng.random((n_seq, 1))).sum(axis=1), vocab - 1)
            seqs[:, step] = pick
            counts[np.arange(n_seq), pick] += 1
        return seqs, counts


    def gen_stats(seqs, counts):
        """(最常出現字佔比, 相異用字數) 的平均。"""
        n_step = seqs.shape[1]
        return counts.max(axis=1).mean() / n_step, (counts > 0).sum(axis=1).mean()

    return gen_stats, run_generation


@app.cell
def _(BLUE, GREEN, ORANGE, RED, freq_pen, gen_stats, np, plt, pres_pen, run_generation):
    _setups = [
        ("no penalty", 0.0, 0.0, BLUE),
        (f"frequency {freq_pen.value:.1f}", freq_pen.value, 0.0, ORANGE),
        (f"presence {pres_pen.value:.1f}", 0.0, pres_pen.value, GREEN),
        ("both", freq_pen.value, pres_pen.value, RED),
    ]
    _shares, _distincts, _names, _cols = [], [], [], []
    for _name, _fp, _pp, _col in _setups:
        _s, _c = run_generation(_fp, _pp)
        _share, _dist = gen_stats(_s, _c)
        _shares.append(_share)
        _distincts.append(_dist)
        _names.append(_name)
        _cols.append(_col)

    _x = np.arange(len(_setups))
    _fig, (_a1, _a2) = plt.subplots(1, 2, figsize=(9.6, 4.0))
    _a1.bar(_x, _shares, color=_cols, width=0.6)
    for _i in _x:
        _a1.text(_i, _shares[_i] + 0.008, f"{_shares[_i]:.3f}", ha="center", fontsize=9)
    _a1.axhline(_shares[0], color=BLUE, linestyle=":", linewidth=1.2)
    _a1.set_xticks(_x)
    _a1.set_xticklabels(_names, rotation=14, ha="right", fontsize=8.5)
    _a1.set_ylim(0, 0.55)
    _a1.set_ylabel("share of most-used word")
    _a1.set_title("repetition (lower = less broken record)")
    _a1.grid(axis="y", alpha=0.3)

    _a2.bar(_x, _distincts, color=_cols, width=0.6)
    for _i in _x:
        _a2.text(_i, _distincts[_i] + 0.06, f"{_distincts[_i]:.2f}", ha="center", fontsize=9)
    _a2.axhline(_distincts[0], color=BLUE, linestyle=":", linewidth=1.2)
    _a2.set_xticks(_x)
    _a2.set_xticklabels(_names, rotation=14, ha="right", fontsize=8.5)
    _a2.set_ylim(0, 8.6)
    _a2.set_ylabel("distinct words used (of 8)")
    _a2.set_title("variety (higher = more diverse)")
    _a2.grid(axis="y", alpha=0.3)
    _fig.tight_layout()
    _fig
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ### 掃一遍：兩種扣法的力道差多少

    上面是三個點，下面是把 penalty 從 0 掃到 1.5 的完整曲線。
    左圖看得最清楚：**frequency 一路往下俯衝、presence 幾乎是條水平線**。
    因為 presence 對「已經出現過的字」通通只扣一次，
    寫得越長、大家都出現過之後，它就等於沒扣——這也是為什麼它不是治跳針的藥。
    """
    )
    return


@app.cell
def _(GREEN, ORANGE, gen_stats, np, plt, run_generation):
    _pens = np.arange(0.0, 1.51, 0.15)
    _f_share, _f_dist, _p_share, _p_dist = [], [], [], []
    for _pen in _pens:
        _s1, _c1 = run_generation(float(_pen), 0.0)
        _s2, _c2 = run_generation(0.0, float(_pen))
        _a, _b = gen_stats(_s1, _c1)
        _c, _d = gen_stats(_s2, _c2)
        _f_share.append(_a)
        _f_dist.append(_b)
        _p_share.append(_c)
        _p_dist.append(_d)

    _fig, (_a1, _a2) = plt.subplots(1, 2, figsize=(9.6, 3.9))
    _a1.plot(_pens, _f_share, color=ORANGE, marker="o", linewidth=2,
             label="frequency_penalty")
    _a1.plot(_pens, _p_share, color=GREEN, marker="s", linewidth=2,
             label="presence_penalty")
    _a1.axvspan(0.3, 0.7, color=ORANGE, alpha=0.10)
    _a1.set_xlabel("penalty value")
    _a1.set_ylabel("share of most-used word")
    _a1.set_title("repetition (shaded = common range 0.3-0.7)")
    _a1.set_ylim(0.1, 0.48)
    _a1.legend(fontsize=9)
    _a1.grid(alpha=0.3)

    _a2.plot(_pens, _f_dist, color=ORANGE, marker="o", linewidth=2,
             label="frequency_penalty")
    _a2.plot(_pens, _p_dist, color=GREEN, marker="s", linewidth=2,
             label="presence_penalty")
    _a2.set_xlabel("penalty value")
    _a2.set_ylabel("distinct words used (of 8)")
    _a2.set_title("variety")
    _a2.set_ylim(5.8, 8.2)
    _a2.legend(fontsize=9)
    _a2.grid(alpha=0.3)
    _fig.tight_layout()
    _fig
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 6️⃣ 速查表 ＋ 換你動手

    一句話總結整堂課：**模型輸出的是機率分佈，四個參數都只是在改這顆骰子的挑法。**

    | 參數 | 改的是 | 常用值 | 什麼時候調 |
    |---|---|---|---|
    | `temperature` | 機率（分佈壓尖／壓平） | 0：抽取／分類／程式<br>0.7~1.0：創作 | 幾乎每個任務都先設它 |
    | `top_p` | 名單（砍掉長尾候選字） | 預設即可（0.9~1.0） | 與 temperature 擇一調，別同時大改 |
    | `frequency_penalty` | logit（按出現次數累加扣分） | 0.3 ~ 0.7 | 長文複讀、跳針時再開 |
    | `presence_penalty` | logit（出現過就扣一次） | 0.3 ~ 0.6 | 希望話題／用詞更多元時 |

    ---

    ### 挑戰（由易到難）

    **LEVEL 1**：把下面實驗區的 `my_T` 改成 `0.05` 和 `2.0`，
    各記下 `quantum` 的機率。差幾個數量級？

    **LEVEL 2**：寫一個 `nucleus(probs, p)` 函式，回傳 top_p 截斷並重新歸一化後的分佈。
    用 T=1 的分佈驗證：`top_p=0.9` 時 `quantum` 應該**恰好是 0**，其餘四個相加為 1。

    **LEVEL 3**：驗證「presence penalty 寫越長越無效」。
    把 `run_generation` 的 `n_step` 從 20 拉到 80，分別算**前 20 步**與**後 60 步**的
    最常出現字佔比。先猜：哪一種 penalty 的兩個數字會幾乎一樣？

    做完記得：**點右上角下載按鈕（或左側教學頁的「下載 .py」）把你的版本帶走**，
    在自己電腦用 `uvx marimo edit lesson.py` 就能繼續玩。
    """
    )
    return


@app.cell
def _(LOGITS, TOKENS, softmax_t):
    # ===== 你的實驗區 =====
    # 這裡可以拿到整堂課的零件：TOKENS / LOGITS / softmax_t /
    # GEN_TOKENS / GEN_LOGITS / run_generation / gen_stats
    my_T = 0.7

    for _tok, _prob in zip(TOKENS, softmax_t(LOGITS, my_T)):
        print(f"{_tok:>9} : {_prob:.4f}")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.accordion(
        {
            "💡 LEVEL 1 參考解答": mo.md(
                r"""
    ```python
    my_T = 0.05   # 再跑一次改成 2.0
    ```

    你應該看到：

    | T | good | quantum |
    |---|---|---|
    | 0.05 | 1.0000 | 0.0000 |
    | 0.70 | 0.5687 | 0.0009 |
    | 2.00 | 0.3449 | 0.0364 |

    從 T=0.05 到 T=2.0，`quantum` 的機率跨了**四個數量級以上**
    （0.05 時小到浮點數印不出來，2.0 時是 3.6%）。
    同一組 logit、同一個模型，只是分母換了。
    """
            ),
            "💡 LEVEL 2 參考解答": mo.md(
                r"""
    ```python
    import numpy as np

    def nucleus(probs, p):
        order = np.argsort(probs)[::-1]
        cum = np.cumsum(probs[order])
        k = min(int(np.searchsorted(cum, p) + 1), len(probs))   # 跨過門檻的那個也留
        keep = order[:k]
        out = np.zeros_like(probs)
        out[keep] = probs[keep] / probs[keep].sum()
        return out

    base = softmax_t(LOGITS, 1.0)
    q = nucleus(base, 0.9)
    for tok, v in zip(TOKENS, q):
        print(f"{tok:>9} : {v:.4f}")
    print("sum =", q.sum())
    ```

    預期輸出：

    ```
         good : 0.4737
      not bad : 0.2632
          hot : 0.1579
         cold : 0.1053
      quantum : 0.0000
    sum = 1.0
    ```

    重點是 `quantum` **恰好是 0**、不是 0.0001——top_p 是砍名單不是壓機率。
    順帶一試：把 `p` 改成 `0.88`，`cold` 也會變成 0（因為 `hot` 的累積 0.890 剛好跨過門檻）。
    """
            ),
            "💡 LEVEL 3 提示與解答": mo.md(
                r"""
    ```python
    import numpy as np

    def half_shares(fp, pp, n_step=80, cut=20):
        seqs, _ = run_generation(fp, pp, n_step=n_step)
        out = []
        for part in (seqs[:, :cut], seqs[:, cut:]):
            n = part.shape[1]
            out.append(np.mean([np.bincount(r, minlength=8).max() for r in part]) / n)
        return out

    for name, fp, pp in (("none", 0, 0), ("freq 0.5", 0.5, 0), ("pres 0.5", 0, 0.5)):
        early, late = half_shares(fp, pp)
        print(f"{name:>9}: 前20步={early:.3f}  後60步={late:.3f}")
    ```

    跑出來：

    ```
         none: 前20步=0.429  後60步=0.423
     freq 0.5: 前20步=0.257  後60步=0.160
     pres 0.5: 前20步=0.399  後60步=0.420
    ```

    答案是 **presence**：它的後 60 步（0.420）幾乎回到完全沒開 penalty 的水準（0.423）。
    原因就是公式本身——八個詞都出現過之後，每個詞都被扣同樣的 `1 × pres_penalty`，
    整排平移不改變 softmax 結果，等於沒扣。frequency 相反：次數一直累加，
    寫越長壓得越重（0.257 → 0.160）。

    **實務結論**：長文跳針要靠 `frequency_penalty`；`presence_penalty` 的舞台是
    短一點的內容、你希望它「別繞著同一批詞打轉」的時候。
    """
            ),
        }
    )
    return


if __name__ == "__main__":
    app.run()
