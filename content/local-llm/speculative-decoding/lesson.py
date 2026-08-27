import marimo

__generated_with = "0.23.16"
app = marimo.App(width="medium", app_title="投機解碼：先猜後驗（實驗場）")


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    # 🧪 投機解碼：先猜後驗（實驗場）

    左邊講的是**為什麼**，這裡是**算給你看**。

    投機解碼只有兩個旋鈕：草稿**猜得準不準**（接受率 α）、**一次猜幾個字**（K）。
    這兩個數字一旦定了，「每輪能賺幾個字」「端到端快幾倍」「什麼時候該關掉」
    全部都是算得出來的——下面每個結論都同時給**理論公式**與**蒙地卡羅真抽**，
    兩邊對得上，你才該相信它。

    每一格程式碼都可以**直接修改、立即重跑**（點格子右上的 ▶，或按 `Ctrl+Enter`）。
    改壞了重新整理頁面就回到原版。
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
def _():
    # ── 全 notebook 共用的常數 ──────────────────────────────
    # 顏色語義（和左邊教學頁一致）：草稿＝橘、大模型＝藍、接受＝綠、拒絕／回滾＝紅
    C_DRAFT = "#DD8452"
    C_TARGET = "#4C72B0"
    C_OK = "#55A868"
    C_NO = "#C44E52"
    C_GREY = "#52646E"

    N_SIM = 30_000     # 蒙地卡羅輪數（拉桿一動就重跑，別開太大）

    # 4️⃣ 併發模型用的三個成本參數（正規化，T_MEM = 1）
    T_MEM = 1.00       # 一次前向要把整份權重從 HBM 搬過來的時間
    T_FLOP = 0.04      # 每個序列、每個位置的實際計算時間
    D_COST = 0.06      # 草稿模型跑一步 ≈ 大模型的 6%
    return C_DRAFT, C_GREY, C_NO, C_OK, C_TARGET, D_COST, N_SIM, T_FLOP, T_MEM


@app.cell
def _(np):
    # ── 三個核心函式：一個真抽、兩個理論式 ──────────────────
    def accepted_lengths(alpha, k, n=30_000, seed=7):
        """蒙地卡羅：跑 n 輪，回傳每輪「連續猜對幾個字」（0 到 k）。

        草稿一旦猜錯，後面就從錯的字接下去猜，整段都會被丟掉——
        所以只要找出每輪第一個沒中的位置就好。
        """
        rng = np.random.default_rng(seed)
        hit = rng.random((n, k)) < alpha
        return np.where(hit.all(axis=1), k, np.argmin(hit, axis=1))

    def expected_tokens(alpha, k):
        """理論值：每輪期望產出 = α + α² + … + α^K + 1。

        那個 +1 是大模型在驗證的同時順手給的字：全中時它是 bonus token，
        被拒時它是修正字——所以最壞情況也還有 1 個，等同不加速。
        """
        return sum(alpha**i for i in range(1, k + 1)) + 1

    def speedup(alpha, k, draft_cost):
        """端到端加速比 ≈ 每輪產出 ÷ (1 次大模型前向 + K 次草稿前向)。"""
        return expected_tokens(alpha, k) / (1 + k * draft_cost)
    return accepted_lengths, expected_tokens, speedup


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 1️⃣ 每輪能賺幾個字

    大模型驗一次，能往前推進幾個字？拉拉看這兩個旋鈕：

    - **α（接受率）**＝草稿猜的字通過大模型檢查的機率。它由草稿模型的品質決定。
    - **K**＝每輪猜幾個字，也就是 vLLM 的 `num_speculative_tokens`。

    藍線是公式算的，綠圈是真的抽 30,000 輪骰子跑出來的——兩者疊在一起，
    表示這條「先猜後驗」的帳沒有唬人。
    """
    )
    return


@app.cell
def _(mo):
    alpha = mo.ui.slider(
        start=0.30, stop=0.95, step=0.05, value=0.85,
        label="α 草稿命中率", show_value=True,
    )
    k = mo.ui.slider(
        start=1, stop=12, step=1, value=5,
        label="K 每輪猜幾個字", show_value=True,
    )
    mo.vstack([alpha, k])
    return alpha, k


@app.cell
def _(
    C_DRAFT,
    C_GREY,
    C_OK,
    C_TARGET,
    N_SIM,
    accepted_lengths,
    alpha,
    expected_tokens,
    k,
    np,
    plt,
):
    ks_grid = np.arange(1, 13)
    theory_curve = np.array(
        [expected_tokens(alpha.value, int(_kk)) for _kk in ks_grid]
    )
    sim_curve = np.array(
        [accepted_lengths(alpha.value, int(_kk), N_SIM).mean() + 1 for _kk in ks_grid]
    )
    e_now = expected_tokens(alpha.value, k.value)

    _fig, _ax = plt.subplots(figsize=(7, 4.2))
    _ax.plot(
        ks_grid, theory_curve, color=C_TARGET, lw=2.5,
        label="theory:  1 + alpha + ... + alpha^K",
    )
    _ax.scatter(
        ks_grid, sim_curve, s=46, facecolor="white", edgecolor=C_OK, lw=2, zorder=3,
        label=f"Monte Carlo ({N_SIM:,} rounds)",
    )
    _ax.plot(
        [k.value], [e_now], marker="*", ms=20, color=C_DRAFT, zorder=4,
        label=f"your setting: K={k.value} -> {e_now:.2f} tokens",
    )
    _ax.axhline(1.0, color=C_GREY, ls=":", lw=1.5)
    _ax.text(
        0.9, 1.06, "no speculation = 1 token per forward pass",
        fontsize=9, color=C_GREY,
    )
    _ax.set_xlabel("K  (draft tokens guessed per round)")
    _ax.set_ylabel("tokens produced per round")
    _ax.set_title(f"acceptance rate alpha = {alpha.value:.2f}")
    _ax.set_xticks(ks_grid)
    _ax.set_ylim(0, 13.5)
    _ax.grid(alpha=0.3)
    _ax.legend(loc="upper left", fontsize=9)
    _fig.tight_layout()
    _fig
    return e_now, sim_curve


@app.cell(hide_code=True)
def _(N_SIM, alpha, e_now, k, mo, sim_curve):
    mo.md(
        f"""
    **α = {alpha.value:.2f}、K = {k.value}**：理論每輪產出 **{e_now:.2f}** 個字，
    {N_SIM:,} 輪蒙地卡羅實際跑出 **{sim_curve[k.value - 1]:.2f}**——公式和真抽對得上。

    這一輪裡大模型只做了 **1 次前向**，所以它的前向次數直接省下 **{e_now:.1f} 倍**。
    注意曲線的形狀：K 越大越賺，但**越後面越平**（每多猜一個字，
    要它有用的前提是前面全中，機率是 α 的連乘）。這就是「猜太多沒有用」的來源，
    3️⃣ 會把草稿的成本加進來，看它什麼時候從賺變賠。
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 2️⃣ 一輪一輪看：接受長度的分布

    平均值會騙人。同樣「平均每輪 4 個字」，可能是每輪都穩穩 4 個，
    也可能是一半全中一半全滅。實際的分布長這樣——**先猜再看**：
    α=0.85、K=5 時，最常見的情況是「全中」還是「只中一兩個」？
    """
    )
    return


@app.cell
def _(C_NO, C_OK, N_SIM, accepted_lengths, alpha, k, np, plt):
    _acc = accepted_lengths(alpha.value, k.value, N_SIM)
    _share = np.bincount(_acc, minlength=k.value + 1) / N_SIM
    _xs = np.arange(k.value + 1)
    acc_mean = float(_acc.mean())

    _fig, _ax = plt.subplots(figsize=(7, 4))
    _ax.bar(
        _xs, _share, color=[C_NO] + [C_OK] * k.value,
        edgecolor="#1C2B33", lw=1.2,
    )
    for _x, _s in zip(_xs, _share):
        _ax.text(_x, _s + 0.012, f"{_s:.0%}", ha="center", fontsize=9)
    _ax.annotate(
        "rejected at the 1st guess\n(still +1 correct token)",
        xy=(0, _share[0]), xytext=(0.35, max(_share) * 0.72),
        fontsize=9, color=C_NO,
        arrowprops={"arrowstyle": "->", "color": C_NO},
    )
    _ax.set_xlabel("draft tokens accepted in one round")
    _ax.set_ylabel("share of rounds")
    _ax.set_title(
        f"alpha = {alpha.value:.2f}, K = {k.value}   "
        f"(mean accepted = {acc_mean:.2f}, produced = {acc_mean + 1:.2f})"
    )
    _ax.set_xticks(_xs)
    _ax.set_ylim(0, max(_share) * 1.25)
    _ax.grid(alpha=0.25, axis="y")
    _fig.tight_layout()
    _fig
    return (acc_mean,)


@app.cell(hide_code=True)
def _(acc_mean, alpha, k, mo):
    mo.md(
        f"""
    在預設那組設定下，分布是**兩頭高**的：最右邊那根（全中 {k.value} 個）在 α 夠高時通常最粗，
    因為「連對 K 次」一點都不稀奇；最左邊的紅柱是「第一個字就被拒」，
    機率固定是 1−α = **{1 - alpha.value:.0%}**。目前這組設定平均接受
    **{acc_mean:.2f}** 個草稿字。

    紅柱是這堂課最重要的一根：**它不是零，但也不是負的**。第一格就被拒的那一輪，
    大模型仍然吐出一個它自己認證過的正確字——這一輪等同沒加速，
    但也**沒有比不加速更慢**（除了草稿那點成本）。投機解碼沒有「猜錯就倒退」這回事：
    每一輪的起點永遠是驗證過的乾淨前綴，所以錯誤不會累積。

    把 α 拉到最低（0.30）再看一次：紅柱變成最粗的一根（70% 的輪次第一個字就被拒），
    平均接受不到半個字——賺得少，但不會賠。
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 3️⃣ 草稿不是免費的：最佳 K 在哪

    1️⃣ 的曲線只算了「賺多少字」，沒算「草稿花多少時間」。
    K 個草稿字要草稿模型自回歸跑 K 次（EAGLE 這類方法就卡在這），
    所以每輪的成本是 `1 次大模型前向 + K 次草稿前向`：

    ```
    加速比 ≈ 每輪產出 / (1 + K × 草稿單步成本)
    ```

    分子是**遞減**的（α 連乘），分母是**線性**成長的——所以一定有一個最佳 K，
    而且草稿模型越貴，那個最佳點越靠左。
    """
    )
    return


@app.cell
def _(C_DRAFT, C_GREY, C_NO, C_OK, C_TARGET, alpha, k, np, plt, speedup):
    _ks = np.arange(1, 21)
    _costs = [0.03, 0.06, 0.15, 0.30]
    _colors = [C_TARGET, C_OK, C_DRAFT, C_NO]

    best_ks = {}
    _fig, _ax = plt.subplots(figsize=(7, 4.2))
    for _c, _color in zip(_costs, _colors):
        _y = np.array([speedup(alpha.value, int(_kk), _c) for _kk in _ks])
        _best = int(np.argmax(_y))
        best_ks[_c] = int(_ks[_best])
        _ax.plot(
            _ks, _y, lw=2.2, color=_color,
            label=f"draft cost {_c:.0%}  ->  best K = {_ks[_best]} ({_y[_best]:.2f}x)",
        )
        _ax.plot([_ks[_best]], [_y[_best]], marker="o", ms=8, color=_color, zorder=3)
    _ax.axhline(1.0, color=C_GREY, ls=":", lw=1.5)
    _ax.text(1.2, 1.05, "1.0x = no faster than plain decoding", fontsize=9, color=C_GREY)
    _ax.axvline(k.value, color="#1C2B33", ls="--", lw=1.2)
    _ax.text(k.value + 0.2, 0.15, f"your K = {k.value}", fontsize=9, rotation=90)
    _ax.set_xlabel("K  (draft tokens guessed per round)")
    _ax.set_ylabel("end-to-end speedup")
    _ax.set_title(f"acceptance rate alpha = {alpha.value:.2f}")
    _ax.set_xticks(_ks[::2])
    _ax.set_ylim(0, None)
    _ax.grid(alpha=0.3)
    _ax.legend(loc="lower right", fontsize=8.5)
    _fig.tight_layout()
    _fig
    return (best_ks,)


@app.cell(hide_code=True)
def _(alpha, best_ks, mo, speedup):
    mo.md(
        f"""
    四條線都是同一個 α（**{alpha.value:.2f}**），差別只在草稿多貴。圓點是各自的最佳 K：

    | 草稿單步成本 | 最佳 K | 誰長這樣 |
    | --- | --- | --- |
    | 3% | **{best_ks[0.03]}** | n-gram、EAGLE head 這種極輕量草稿 |
    | 6% | **{best_ks[0.06]}** | 同家族的小模型（例如 8B 配 0.6B） |
    | 15% | **{best_ks[0.15]}** | 草稿選太大了 |
    | 30% | **{best_ks[0.30]}** | 草稿幾乎跟大模型一樣貴，已經沒什麼好賺 |

    **草稿越貴，最佳點越往左**——而且不只是賺少而已，會直接倒賠：
    α = 0.60、草稿 30% 時最佳 K 只剩 1；照抄別人的 K = 5 就掉到
    **{speedup(0.60, 5, 0.30):.2f}x**（比不開還慢），硬拉到 12 更是
    **{speedup(0.60, 12, 0.30):.2f}x**。

    這就是為什麼 DFlash 那類方法要把草稿做成「一次前向吐一整塊」：
    分母的 `K × 草稿成本` 被壓成常數，最佳 K 才推得回右邊。
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 4️⃣ 併發一上來，帳就翻了

    前面三節都在算「一個人用」的情況。多人共用同一張卡時，帳完全不一樣：

    - 一次前向的時間 ≈ `搬權重的時間` + `併發數 × 每個序列的計算時間`
    - 搬權重的成本**不隨人數增加**（大家共用同一份權重），計算成本**隨人數線性長**
    - 投機解碼把每個序列的計算量乘上 (K+1) 倍——低併發時那些算力本來就閒著，
      高併發時它是在跟別的使用者搶名額

    下面是一個**教學用的簡化模型**（只保留上面三行的關係，方便看趨勢；
    真實系統的曲線要用 `vllm bench serve` 掃出來）：
    """
    )
    return


@app.cell
def _(
    C_DRAFT,
    C_GREY,
    C_TARGET,
    D_COST,
    T_FLOP,
    T_MEM,
    alpha,
    expected_tokens,
    k,
    np,
    plt,
):
    _conc = np.array([1, 2, 4, 8, 16, 32, 64, 128])
    _tau = expected_tokens(alpha.value, k.value)

    _t_off = T_MEM + _conc * T_FLOP
    _t_on = T_MEM * (1 + k.value * D_COST) + _conc * (k.value + 1) * T_FLOP
    _pu_off, _pu_on = 1.0 / _t_off, _tau / _t_on
    _tot_off, _tot_on = _conc * _pu_off, _conc * _pu_on

    _fig, (_a1, _a2) = plt.subplots(1, 2, figsize=(9.4, 4.1))
    for _ax, _off, _on, _t in (
        (_a1, _pu_off, _pu_on, "per-user speed"),
        (_a2, _tot_off, _tot_on, "total throughput"),
    ):
        _ax.plot(_conc, _off, "o-", color=C_TARGET, lw=2.2, label="speculation OFF")
        _ax.plot(_conc, _on, "s-", color=C_DRAFT, lw=2.2, label="speculation ON")
        _ax.set_xscale("log", base=2)
        _ax.set_xticks(_conc)
        _ax.set_xticklabels(_conc)
        _ax.set_xlabel("concurrent users")
        _ax.set_ylabel("tokens / s  (normalized)")
        _ax.set_title(_t)
        _ax.grid(alpha=0.3)
        _ax.legend(fontsize=9)

    _cross = np.where(_tot_on < _tot_off)[0]
    if len(_cross):
        _a2.axvline(_conc[_cross[0]], color=C_GREY, ls="--", lw=1.3)
        _a2.text(
            _conc[_cross[0]] * 1.08, max(_tot_off) * 0.35,
            f"ON loses from\n{_conc[_cross[0]]} users up",
            fontsize=9, color=C_GREY,
        )
    _fig.suptitle(
        f"simplified model: alpha={alpha.value:.2f}, K={k.value}, "
        f"draft cost={D_COST:.0%}, compute cost per seq={T_FLOP}",
        fontsize=10,
    )
    _fig.tight_layout()
    _fig
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    左圖（每個人的速度）幾乎永遠是開著比較快——**使用者的體感就是這張圖**。
    右圖（總產能）才是老闆看的：低併發時開著也贏，但過了交叉點之後，
    同一張卡服務所有人的總產能反而**掉下去**。

    兩張圖說的是同一件事：投機解碼買的是**per-user 速度**，付的是**算力**。
    算力免費（低併發）時它是白拿的；算力稀缺（高併發）時你是在拿別人的名額換自己的速度。

    把 K 拉到 12 再看右圖：交叉點會往左移——猜越多，越早開始拖垮總吞吐。
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 5️⃣ 練習：換你動手

    下面這格是你的實驗區，改完按 ▶ 重跑。三個挑戰：

    1. **LEVEL 1**：把 1️⃣ 的 α 從 0.40 拉到 0.95（K 固定 5），
       記下每輪期望產出各是多少。
    2. **LEVEL 2**：α = 0.85、草稿成本 6% 時，**最佳 K 是多少**？
       用 `speedup()` 掃 K = 1…20 找出最大值。
    3. **LEVEL 3**：4️⃣ 的 `T_FLOP`（每個序列的計算單價）如果變成 0.01
       （換一張算力更強的卡），交叉點會往左還是往右移？先猜，再改常數驗證。

    做完記得：**點右上角下載按鈕（或左側教學頁的「下載 .py」）把你的版本帶走**，
    在自己電腦用 `uvx marimo edit lesson.py` 就能繼續玩。
    """
    )
    return


@app.cell
def _(expected_tokens, speedup):
    # ===== 你的實驗區 =====
    # 改這三個數字，看它們怎麼決定一切
    my_alpha = 0.85
    my_k = 5
    my_draft_cost = 0.06

    print(f"每輪期望產出 : {expected_tokens(my_alpha, my_k):.2f} tokens")
    print(f"端到端加速比 : {speedup(my_alpha, my_k, my_draft_cost):.2f}x")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.accordion(
        {
            "💡 LEVEL 1 參考解答": mo.md(
                r"""
    直接拉 1️⃣ 的滑桿就看得到，也可以一次印出來：

    ```python
    for a in (0.40, 0.60, 0.85, 0.95):
        print(f"alpha={a}: {expected_tokens(a, 5):.2f} tokens/round")
    ```

    你應該看到 **1.66 → 2.38 → 4.15 → 5.30**。
    α 從 0.40 到 0.95，每輪產出翻了 3 倍多——
    **接受率才是主旋鈕**，這也是 Medusa → EAGLE → DSpark 一路在改的東西。
    """
            ),
            "💡 LEVEL 2 參考解答": mo.md(
                r"""
    ```python
    best = max(range(1, 21), key=lambda kk: speedup(0.85, kk, 0.06))
    for kk in range(1, 21):
        mark = "  <-- best" if kk == best else ""
        print(f"K={kk:2d}: {speedup(0.85, kk, 0.06):.3f}x{mark}")
    ```

    你應該看到最佳 **K = 9，加速比 ≈ 3.48x**。注意 K = 6 就已經有 3.33x 了——
    最後那 3 個字只多換到 4% 速度，卻讓每輪多燒 3 次草稿前向與 3 個 batch 名額。
    **實務上寧可選曲線開始變平的那個 K，不是最高點的那個 K。**
    """
            ),
            "💡 LEVEL 3 提示": mo.md(
                r"""
    方向：`T_FLOP` 是「每個序列每個位置的計算時間」，它變小＝這張卡的算力更充裕，
    所以算力要更晚才會被塞滿。改常數那格的 `T_FLOP = 0.04` → `0.01` 再看 4️⃣ 右圖。

    怎麼驗證自己做對了：交叉點（虛線）應該往**右**移，甚至跑出 128 以外消失
    （代表在這個範圍內開著永遠不虧）。反過來把 `T_FLOP` 調大到 0.12，
    交叉點會往左衝到很小的併發數——**同一組 α 與 K，換一張卡結論就會反過來**，
    這就是為什麼左邊教學頁一直說「高併發務必自己實測 on/off」。
    """
            ),
        }
    )
    return


if __name__ == "__main__":
    app.run()
