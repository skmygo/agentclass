import marimo

__generated_with = "0.23.16"
app = marimo.App(width="medium", app_title="引擎選型：Ollama vs vLLM（實驗場）")


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    # 🧪 引擎選型：Ollama vs vLLM（實驗場）

    左邊讀到哪，就回到這裡動手——每個實驗都有**滑桿與選項**可以拉。

    這裡不會真的起一個 LLM 服務——我們把兩個引擎**管記憶體的規則**寫成程式，
    真的算給你看。所有百分比、倍數都是這幾格當場算出來的，拉桿一動就重算。
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


@app.cell
def _():
    # 全 notebook 共用的常數。上面三個是規則，下面四個是引用的實測值
    # （實測：RTX 4090、Llama 3.1 8B Q4_K_M、閒置後第一次請求）
    BLOCK = 16          # PagedAttention 的一個 block 幾個 token
    OLLAMA_VRAM = 6.4   # GB
    VLLM_VRAM = 8.2     # GB
    COLD_TTFT = 8.3     # 秒：Ollama 冷啟動的首 token 延遲（vLLM 是 0.4 秒）

    C_SLOT = "#DD8452"   # 橘＝slot 固定分配（Ollama / llama.cpp）
    C_PAGE = "#4C72B0"   # 藍＝PagedAttention（vLLM）
    C_WASTE = "#D9DEE2"  # 灰＝被配走、卻沒真的用到的記憶體
    return BLOCK, COLD_TTFT, C_PAGE, C_SLOT, C_WASTE, OLLAMA_VRAM, VLLM_VRAM


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 1️⃣ 包廂制 vs 拼桌制：同一批請求，兩種配法

    兩個引擎拿到的是**同一批請求**——差別只在怎麼把 KV cache 的記憶體發下去：

    - **Ollama（llama.cpp）**：啟動時就切好固定大小的 slot，一個請求佔一整格。
      `llama-server -c 4096 -np 2` 就是「總 context 4096、切 2 個 slot」。
      請求只用 300 個 token？剩下的一樣被綁著，誰也拿不走。
    - **vLLM（PagedAttention）**：記憶體切成 16 個 token 一塊的小 block，用多少拿多少，
      最後一塊沒填滿才有零頭。

    拉下面的拉桿換一批請求，看兩邊的利用率怎麼跑。
    """
    )
    return


@app.cell
def _(mo):
    n_req = mo.ui.slider(
        1, 24, 1, value=8, label="同時在跑的請求數", show_value=True
    )
    mean_len = mo.ui.slider(
        50, 3800, 50, value=400, label="請求平均長度（tokens）", show_value=True
    )
    spread = mo.ui.slider(
        0, 100, 5, value=60, label="長度離散度（%）", show_value=True
    )
    ctx_slot = mo.ui.dropdown(
        options={"2048": 2048, "4096": 4096, "8192": 8192},
        value="4096",
        label="每個 slot 的 context（llama-server -c）",
    )
    seed = mo.ui.slider(
        0, 30, 1, value=7, label="換一批請求（隨機種子）", show_value=True
    )
    mo.vstack([n_req, mean_len, spread, ctx_slot, seed])
    return ctx_slot, mean_len, n_req, seed, spread


@app.cell
def _(ctx_slot, mean_len, n_req, np, seed, spread):
    # 抽一批請求的實際長度：常態分佈、砍在 [16, slot context] 之間
    _rng = np.random.default_rng(seed.value)
    _raw = _rng.normal(mean_len.value, mean_len.value * spread.value / 100.0, n_req.value)
    req_lens = np.clip(np.rint(_raw), 16, ctx_slot.value).astype(int)
    return (req_lens,)


@app.cell
def _(BLOCK, ctx_slot, np, req_lens):
    # 兩制各自「配出去」多少 token 的空間——這就是全課的核心公式
    used_tokens = int(req_lens.sum())
    slot_alloc = int(len(req_lens) * ctx_slot.value)               # 一請求一整格
    paged_alloc = int((np.ceil(req_lens / BLOCK) * BLOCK).sum())   # 進位到 block
    slot_util = used_tokens / slot_alloc
    paged_util = used_tokens / paged_alloc
    return paged_alloc, paged_util, slot_alloc, slot_util, used_tokens


@app.cell
def _(
    BLOCK,
    C_PAGE,
    C_SLOT,
    C_WASTE,
    ctx_slot,
    np,
    paged_util,
    plt,
    req_lens,
    slot_util,
):
    # 灰色＝配出去的空間，彩色＝真正用到的。灰色露出來的部分就是浪費
    _idx = np.arange(len(req_lens))
    _paged = (np.ceil(req_lens / BLOCK) * BLOCK).astype(int)
    _fig, _axes = plt.subplots(2, 1, figsize=(6.4, 6.8), sharey=True)

    _axes[0].bar(_idx, ctx_slot.value, color=C_WASTE)
    _axes[0].bar(_idx, req_lens, color=C_SLOT)
    _axes[0].set_title(
        f"Ollama / llama.cpp - fixed slots\nutilization = {slot_util:.1%}",
        fontsize=10.5,
        fontweight="bold",
    )
    _axes[0].set_ylabel("KV tokens allocated")

    _axes[1].bar(_idx, _paged, color=C_WASTE)
    _axes[1].bar(_idx, req_lens, color=C_PAGE)
    _axes[1].set_title(
        f"vLLM / PagedAttention - {BLOCK}-token blocks\nutilization = {paged_util:.1%}",
        fontsize=10.5,
        fontweight="bold",
    )

    for _ax in _axes:
        _ax.set_xlabel("request #")
        _ax.set_xticks(_idx)
        _ax.grid(axis="y", alpha=0.3)
        _ax.set_axisbelow(True)
    _fig.tight_layout()
    _fig
    return


@app.cell(hide_code=True)
def _(mo, paged_alloc, paged_util, req_lens, slot_alloc, slot_util, used_tokens):
    mo.md(
        f"""
    這批請求真正需要 **{used_tokens:,} tokens** 的 KV cache。

    | | 配出去的空間 | 利用率 | 浪費掉 |
    | --- | --- | --- | --- |
    | slot 固定分配 | {slot_alloc:,} tokens | **{slot_util:.1%}** | {slot_alloc - used_tokens:,} tokens |
    | PagedAttention | {paged_alloc:,} tokens | **{paged_util:.1%}** | {paged_alloc - used_tokens:,} tokens |

    同一批 {len(req_lens)} 個請求，slot 制要 **{slot_alloc / paged_alloc:.1f} 倍**的記憶體才裝得下。

    現在把「請求平均長度」拉到最右邊（接近 slot context）——兩邊的差距會塌下來。
    這就是重點：**slot 制不是比較笨，是它假設每個請求都會用滿**。請求越短、長度越參差，
    它賠得越多。
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ### 這件事真正的代價：能同時服務幾個人

    利用率只是帳面數字。把它換成「同一塊 VRAM 能同時裝下幾個請求」，
    才看得出為什麼 vLLM 敢說自己高並發。下面固定一個 KV cache 預算，
    掃過各種請求平均長度，算兩制各能同時塞幾個請求。
    """
    )
    return


@app.cell
def _(mo):
    budget = mo.ui.slider(
        8, 128, 8, value=48,
        label="留給 KV cache 的預算（千 tokens）", show_value=True,
    )
    budget
    return (budget,)


@app.cell
def _(BLOCK, budget, ctx_slot, np, seed, spread):
    # slot 制：能開幾個 slot 只跟 context 設定有關，跟請求多短完全無關
    # paged 制：一個一個塞，塞到預算用完為止
    _rng = np.random.default_rng(seed.value + 1000)
    _cap = budget.value * 1000
    means = np.arange(100, 3701, 100)
    slot_fit = np.full(len(means), _cap // ctx_slot.value, dtype=float)
    paged_fit = np.zeros(len(means))
    for _i, _m in enumerate(means):
        _lens = np.clip(
            np.rint(_rng.normal(_m, _m * spread.value / 100.0, 800)), 16, ctx_slot.value
        )
        _cum = np.cumsum(np.ceil(_lens / BLOCK) * BLOCK)
        paged_fit[_i] = int((_cum <= _cap).sum())
    return means, paged_fit, slot_fit


@app.cell
def _(C_PAGE, C_SLOT, budget, ctx_slot, means, paged_fit, plt, slot_fit):
    _fig2, _ax2 = plt.subplots(figsize=(6.5, 3.9))
    _ax2.plot(means, slot_fit, color=C_SLOT, lw=3, label="fixed slots (Ollama)")
    _ax2.plot(means, paged_fit, color=C_PAGE, lw=3, label="PagedAttention (vLLM)")
    _ax2.fill_between(means, slot_fit, paged_fit, where=(paged_fit >= slot_fit),
                      color=C_PAGE, alpha=0.10)
    _ax2.set_yscale("log")
    _ax2.set_xlabel("mean request length (tokens)")
    _ax2.set_ylabel("concurrent requests served (log)")
    _ax2.set_title(
        f"KV budget {budget.value}k tokens, slot context {ctx_slot.value}",
        fontsize=10.5, fontweight="bold",
    )
    _ax2.legend(fontsize=9.5)
    _ax2.grid(alpha=0.3)
    _ax2.set_axisbelow(True)
    _fig2.tight_layout()
    _fig2
    return


@app.cell(hide_code=True)
def _(budget, ctx_slot, means, mo, paged_fit, slot_fit):
    _i_short = 3   # 平均 400 tokens
    _i_long = len(means) - 1
    mo.md(
        f"""
    橘線是**一條水平線**——這就是包廂制：slot 開幾個由 `-c` 跟 `-np` 決定，
    請求短不短它一點都不在乎。{budget.value}k 的預算配 {ctx_slot.value} 的 context，
    永遠只有 **{int(slot_fit[0])} 個位子**。

    藍線會隨請求變短一路往上衝：平均 {int(means[_i_short])} tokens 時能同時服務
    **{int(paged_fit[_i_short])} 個**請求（{paged_fit[_i_short] / max(slot_fit[0], 1):.0f} 倍）；
    等到請求長到 {int(means[_i_long])} tokens，藍線就掉下來貼近橘線了。

    順著看下去就懂了：**continuous batching 要能隨時插入、移出請求，前提是記憶體能動態分配**。
    PagedAttention 提供的正是這個能力——高並發不是另一項功能，是同一件事的結果。
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 2️⃣ 常駐與卸載：VRAM 的兩種脾氣

    第二個差異跟記憶體多寡無關，跟**什麼時候佔著**有關：

    - **Ollama**：第一次推理才把模型搬進 GPU，閒置預設 5 分鐘就卸載、把 VRAM 還你。
      （`OLLAMA_KEEP_ALIVE=-1` 可以叫它永久常駐。）
    - **vLLM**：啟動就把權重＋KV cache 空間全部預配好，一直佔著——換來穩定的高吞吐。

    代價寫在實測裡（RTX 4090、Llama 3.1 8B Q4_K_M、閒置後第一次請求）：
    Ollama 冷啟動首 token 要 **8.3 秒**，vLLM 是 **0.4 秒**；但暖機之後兩者穩態速度
    幾乎一樣（138 vs 142 tokens/s）。**差別只在冷啟動。**

    下面模擬一段時間內零星進來的請求（到達時間用指數分佈抽，是教學用的模型不是實測），
    看你的使用節奏會不會一直踩到冷啟動。
    """
    )
    return


@app.cell
def _(mo):
    gap_min = mo.ui.slider(
        0.5, 30.0, 0.5, value=8.0,
        label="兩次請求的平均間隔（分鐘）", show_value=True,
    )
    keep_alive = mo.ui.slider(
        1, 30, 1, value=5,
        label="Ollama 閒置卸載門檻（分鐘，預設 5）", show_value=True,
    )
    window_h = mo.ui.slider(
        1, 8, 1, value=4, label="模擬時長（小時）", show_value=True
    )
    mo.vstack([gap_min, keep_alive, window_h])
    return gap_min, keep_alive, window_h


@app.cell
def _(gap_min, keep_alive, np, window_h):
    _win = window_h.value * 60.0
    _rng = np.random.default_rng(11)
    _ts = np.cumsum(_rng.exponential(gap_min.value, int(_win / gap_min.value * 4) + 40))
    arrivals = _ts[_ts < _win]
    # 距上一次請求超過門檻 → 模型已經被卸載 → 這一發是冷啟動（第一發一定是冷的）
    is_cold = np.diff(arrivals, prepend=-1e9) > keep_alive.value
    # Ollama 什麼時候佔著 VRAM：任一請求之後的 keep_alive 分鐘內
    grid_t = np.arange(0, _win, 0.25)
    _last = np.searchsorted(arrivals, grid_t, side="right") - 1
    ollama_on = (_last >= 0) & (
        (grid_t - arrivals[np.clip(_last, 0, None)]) <= keep_alive.value
    )
    return arrivals, grid_t, is_cold, ollama_on


@app.cell
def _(
    C_PAGE,
    C_SLOT,
    OLLAMA_VRAM,
    VLLM_VRAM,
    arrivals,
    grid_t,
    is_cold,
    ollama_on,
    plt,
):
    _fig3, _ax3 = plt.subplots(figsize=(6.5, 3.9))
    _ax3.fill_between(
        grid_t, 0, ollama_on * OLLAMA_VRAM, step="post",
        color=C_SLOT, alpha=0.35, label=f"Ollama held ({OLLAMA_VRAM} GB when loaded)",
    )
    _ax3.axhline(
        VLLM_VRAM, color=C_PAGE, lw=3,
        label=f"vLLM held ({VLLM_VRAM} GB, always)",
    )
    _ax3.scatter(
        arrivals[~is_cold], [0.55] * int((~is_cold).sum()),
        marker="o", s=26, color=C_PAGE, zorder=5, label="warm request",
    )
    _ax3.scatter(
        arrivals[is_cold], [0.55] * int(is_cold.sum()),
        marker="X", s=70, color="#C44E52", zorder=6, label="cold start (+8.3 s)",
    )
    _ax3.set_xlabel("minutes")
    _ax3.set_ylabel("VRAM held (GB)")
    _ax3.set_ylim(0, VLLM_VRAM * 1.25)
    _ax3.set_title("Who is holding the GPU, and when", fontsize=10.5, fontweight="bold")
    _ax3.legend(fontsize=8.5, ncol=2, loc="upper right")
    _ax3.grid(alpha=0.3)
    _ax3.set_axisbelow(True)
    _fig3.tight_layout()
    _fig3
    return


@app.cell(hide_code=True)
def _(
    COLD_TTFT,
    OLLAMA_VRAM,
    VLLM_VRAM,
    arrivals,
    is_cold,
    mo,
    ollama_on,
    window_h,
):
    _n = len(arrivals)
    _c = int(is_cold.sum())
    mo.md(
        f"""
    這 {window_h.value} 小時裡進來 **{_n} 個請求**，其中 **{_c} 個踩到冷啟動
    （{_c / max(_n, 1):.0%}）**，光是等模型上車就多花了 **{_c * COLD_TTFT:.0f} 秒**。
    同一段時間 Ollama 平均只佔著 **{ollama_on.mean() * OLLAMA_VRAM:.1f} GB**
    （{ollama_on.mean():.0%} 的時間有載入），vLLM 從頭到尾佔滿 **{VLLM_VRAM} GB**。

    這就是「兩種脾氣」的完整交易條件，沒有誰對誰錯：

    - 把「平均間隔」拉到 1 分鐘（像真的有人在用的產品）→ 冷啟動幾乎歸零，
      Ollama 也一直佔著 VRAM，兩邊的差別瞬間變小。
    - 拉到 20 分鐘（你自己偶爾問一句）→ 幾乎**每一發都是冷啟動**，
      但你的 GPU 有八成時間是空的，可以拿去跑別的東西。

    第一種情境該用 vLLM，第二種該用 Ollama——不是因為誰比較快，是因為**你願意用閒置的 VRAM 換什麼**。
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 3️⃣ 拆解「34.2×」：總量不是每個人的體感

    引擎的行銷圖上常常會有一根很高的柱子配一個很大的倍數。這一節把一個真實的例子拆開，
    引用的是一份公開的吞吐對照（Ollama 跑 Q4_K_M 4-bit、vLLM 跑 BF16 16-bit，
    第三根柱子是 **32 個人同時打**時整台機器的總吞吐 1606.78 tokens/s，
    標題數字 34.2×、第 1 對第 2 根是 4.6×）。

    下面把「總吞吐」除以人數，換算成**一個使用者實際感受到的速度**。
    """
    )
    return


@app.cell
def _():
    # 引用的數字（第 1 根柱子由「總量 1606.78 ÷ 標題倍數 34.2」反推）
    BATCH_TOTAL = 1606.78   # tokens/s：32 併發時整台機器加起來的總吞吐
    BATCH_N = 32
    HEADLINE_X = 34.2       # 行銷標題上的倍數
    SINGLE_X = 4.6          # 第 1 根 vs 第 2 根（都是單請求）

    ollama_single = BATCH_TOTAL / HEADLINE_X
    vllm_single = ollama_single * SINGLE_X
    per_user_batch = BATCH_TOTAL / BATCH_N
    per_user_gain = per_user_batch / ollama_single
    return (
        BATCH_N,
        BATCH_TOTAL,
        HEADLINE_X,
        ollama_single,
        per_user_batch,
        per_user_gain,
        vllm_single,
    )


@app.cell
def _(
    BATCH_N,
    BATCH_TOTAL,
    C_PAGE,
    C_SLOT,
    HEADLINE_X,
    ollama_single,
    per_user_batch,
    per_user_gain,
    plt,
    vllm_single,
):
    _labels = ["Ollama\nQ4_K_M\n1 request", "vLLM\nBF16\n1 request", f"vLLM\nBF16\n{BATCH_N} requests"]
    _colors = [C_SLOT, C_PAGE, C_PAGE]
    _fig4, _ax4 = plt.subplots(2, 1, figsize=(6.4, 7.2))

    _tot = [ollama_single, vllm_single, BATCH_TOTAL]
    _ax4[0].bar(_labels, _tot, color=_colors)
    _ax4[0].set_title(f"machine total: the {HEADLINE_X}x headline", fontsize=10.5, fontweight="bold")
    _ax4[0].set_ylabel("tokens / s")
    for _i, _v in enumerate(_tot):
        _ax4[0].text(_i, _v * 1.02, f"{_v:.0f}", ha="center", fontsize=9, fontweight="bold")

    _pu = [ollama_single, vllm_single, per_user_batch]
    _ax4[1].bar(_labels, _pu, color=_colors)
    _ax4[1].set_title(f"per user: only {per_user_gain:.2f}x", fontsize=10.5, fontweight="bold")
    _ax4[1].set_ylabel("tokens / s per user")
    for _i, _v in enumerate(_pu):
        _ax4[1].text(_i, _v * 1.02, f"{_v:.0f}", ha="center", fontsize=9, fontweight="bold")

    for _ax in _ax4:
        _ax.tick_params(axis="x", labelsize=8)
        _ax.grid(axis="y", alpha=0.3)
        _ax.set_axisbelow(True)
    _fig4.tight_layout()
    _fig4
    return


@app.cell(hide_code=True)
def _(
    BATCH_N,
    HEADLINE_X,
    mo,
    ollama_single,
    per_user_batch,
    per_user_gain,
    vllm_single,
):
    mo.md(
        f"""
    下面那張圖（per user）就是全課最該記住的一句話：**{HEADLINE_X}× 是機器的，不是你的。**

    - 第三根柱子除以 {BATCH_N} 個人 → 每人 **{per_user_batch:.0f} tokens/s**，
      對上 Ollama 的 {ollama_single:.0f} tokens/s，只有 **{per_user_gain:.2f}×**。
    - 而且第 1 對第 2 根的 {vllm_single / ollama_single:.1f}× 也不能全算在引擎頭上：
      兩者**精度不同**（Q4_K_M 4-bit vs BF16 16-bit）。理論上 4-bit 更省記憶體、更該快，
      實際卻慢——那是量化實作與 kernel 的差別，不是單純「引擎比較快」。

    所以看到大倍數，先問三句：**幾個人同時打？兩邊精度一不一樣？倍數是總量還是單人？**
    這三句問完，多數行銷圖就會回到它該有的大小。

    也別因此覺得 vLLM 被戳破了——**吞吐本來就是它的賣點**。
    32 個人同時打還能維持每人 {per_user_batch:.0f} tokens/s，這是 slot 制做不到的事；
    只是它換來的是**服務更多人**，不是「讓你一個人快 34 倍」。
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 4️⃣ 換你動手

    三個挑戰，由易到難。前兩個用 1️⃣ 的拉桿就做得完，第三個用下面的實驗區。

    1. **LEVEL 1**：把上面 1️⃣ 的「請求平均長度」拉到 3800、「長度離散度」拉到 0，
       看兩制的利用率變成幾 %。想一句話解釋為什麼差距不見了。
    2. **LEVEL 2**：其他拉桿不動，把 1️⃣ 的「請求平均長度」從最左邊一路往右拉，
       盯著表格下面那句「slot 制要 X 倍的記憶體」——找出這個倍數掉到 **2× 以下**的平均長度。
    3. **LEVEL 3**：加進 **prefix caching**——每個請求前面都掛著同一段 system prompt，
       PagedAttention 可以讓所有請求**共用**那幾塊 block，slot 制的每一格都得自己存一份。
       用下面的實驗區把前綴拉長、把人數拉多，看兩制的「服務倍率」往哪邊跑。

    做完記得：**點左側教學頁的「下載 .py」把這份 notebook 帶走**，
    在自己電腦用 `uvx marimo edit lesson.py` 打開，每一格程式碼都能改。
    """
    )
    return


@app.cell
def _(mo):
    my_prefix = mo.ui.slider(
        0, 2000, 100, value=800, label="共用 system prompt 長度（token）", show_value=True
    )
    my_n = mo.ui.slider(1, 24, 1, value=5, label="同時在跑幾個請求", show_value=True)
    my_body = mo.ui.slider(
        50, 2000, 50, value=460, label="每個請求自己的部分（平均 token）", show_value=True
    )
    mo.vstack(
        [
            mo.md(
                "**你的實驗區**——每個請求都掛著同一段 system prompt。"
                "slot context 沿用 1️⃣ 的設定。"
            ),
            my_prefix,
            my_n,
            my_body,
        ]
    )
    return my_body, my_n, my_prefix


@app.cell
def _(BLOCK, ctx_slot, mo, my_body, my_n, my_prefix, np):
    _pf, _n = my_prefix.value, my_n.value
    _rng = np.random.default_rng(3)
    _body = np.clip(
        np.rint(_rng.normal(my_body.value, my_body.value * 0.6, _n)),
        16,
        ctx_slot.value - _pf,
    ).astype(int)

    _logical = int(_body.sum()) + _pf * _n                       # 邏輯上每個請求都看得到整段前綴
    _slot = _n * ctx_slot.value                                  # 一請求一整格，前綴各存一份
    _paged = int(np.ceil(_pf / BLOCK) * BLOCK) + int(
        (np.ceil(_body / BLOCK) * BLOCK).sum()
    )                                                            # 前綴整批只存一份

    mo.md(
        f"""
    {_n} 個請求、每人掛 **{_pf:,}** token 的共用前綴，邏輯上要服務 **{_logical:,} tokens** 的 KV。

    | | 真的配出去 | 每配置 1 token 服務到 |
    | --- | --- | --- |
    | slot 固定分配 | {_slot:,} tokens | **{_logical / _slot:.2f}** |
    | PagedAttention（前綴共用） | {_paged:,} tokens | **{_logical / _paged:.2f}** |

    前綴每拉長 100，paged 制只多存 100（**整批一份**），slot 制的每一格都得自己存一份。
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.accordion(
        {
            "💡 LEVEL 1 參考解答": mo.md(
                r"""
    把 1️⃣ 的拉桿設成「平均長度 3800、離散度 0、context 4096」，你會看到
    **slot 利用率跳到 92% 左右、paged 約 99%**——兩邊幾乎一樣了。

    一句話解釋：**slot 制的浪費＝配額減去實際用量**。當每個請求都快用滿一整格，
    那個減法就趨近於零。所以 slot 制不是「總是很爛」，是它**押注在「請求都會用滿」上**——
    押對了就沒事，押錯（短請求、長度參差）才賠。這也解釋了為什麼個人使用的體感差不多、
    一上到多人服務就差很多。
    """
            ),
            "💡 LEVEL 2 參考解答": mo.md(
                r"""
    其他拉桿保持預設（8 個請求、離散度 60%、context 4096、種子 7），
    只拉「請求平均長度」，那句「slot 制要 X 倍的記憶體」會這樣走：

    | 平均長度 | 200 | 400 | 600 | 1000 | 1500 | 2000 | **2200** | 3000 | 3800 |
    | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
    | slot / paged | 21.1× | 10.8× | 7.2× | 4.4× | 2.9× | 2.2× | **1.99×** | 1.6× | 1.3× |

    一路往右下滑：短請求時 slot 制要多花 **20 倍**記憶體，**平均長度 2200 左右跨過 2× 這條線**
    （大約是 context 的一半），到 3800（接近 context 上限）只剩 1.3 倍。
    （換個種子數字會略有出入，方向不變。）

    這條線就是選型的分水嶺：**短而多的請求（聊天、agent 的小步驟）差最多；
    長而滿的請求（整份文件塞進去）差最少**。
    """
            ),
            "💡 LEVEL 3 提示": mo.md(
                r"""
    關鍵在「每配置 1 token 服務到幾個 token」這一欄：**超過 1 就代表同一塊記憶體被多個請求共用**。

    怎麼驗證自己做對了（預設 5 個請求、每人自己的部分平均 460）：

    1. 把前綴從 0 拉到 800：paged 制的配置量只多了 **800**（2,256 → 3,056），
       **不管幾個請求都只多這一份**——這就是「跨請求重用相同前綴 block」。
       slot 制的數字**一動也不動**，因為前綴本來就吃在每一格自己的 4096 裡。
    2. 前綴 800 不動，把人數從 5 拉到 20：paged 制的服務倍率從 **2.05 爬到 2.55**
       （多出來的前綴需求幾乎不花錢），slot 制反而從 0.31 掉到 **0.30**。人越多差越大。
    3. 反過來想一個 slot 制也不吃虧的情況：把人數拉到 1、前綴拉到 0——
       共用前綴無事可做，兩制只剩「格子有沒有用滿」的差別。

    做完你就懂了 vLLM 那句「長 system prompt 重複使用 → 自動 Prefix Caching 大降 TTFT」
    背後在講什麼：**能共享，是因為記憶體是一塊一塊發的**。
    """
            ),
        }
    )
    return


if __name__ == "__main__":
    app.run()
