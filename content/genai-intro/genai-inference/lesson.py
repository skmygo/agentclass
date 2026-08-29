import marimo

__generated_with = "0.23.16"
app = marimo.App(width="medium", app_title="推理加速：KV Cache、量化與 vLLM（實驗場）")


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    # 🧪 推理加速：KV Cache、量化與 vLLM（實驗場）

    這是本課的**實驗場**。左側教學讀到哪，就回到這裡動手做——
    每個實驗都有**滑桿與選項**可以拉，拉完右邊立刻重算——
    所有數字都是當場算出來的，不是預錄的畫面。

    這一課的名詞聽起來最「工程」，但每個都能算給你看：**KV Cache** 有多大、
    **量化**丟掉多少精度、**投機解碼**快在哪、**連續批次**省下什麼、
    **MoE** 為什麼大而不貴。全部都是真的算，不是示意圖。
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


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 1️⃣ KV Cache：先算它有多大

    自迴歸生成每走一步都要「回頭看」前面所有 token 的 Key/Value——
    不存起來就得每步重算一遍。存起來的這塊記憶體叫 **KV cache**，
    大小完全由模型架構決定，公式一行：

    ```
    每 token 位元組 = 2（K 和 V） × 層數 × KV head 數 × head 維度 × 每個數的位元組
    ```

    8B 級 GQA 模型（32 層 × 8 KV head × 128 維 × fp16）算出來是 **128 KB/token**。
    拉下面的桿子，看「上下文長度 × 同時在線人數」把它吹成多大：
    """
    )
    return


@app.cell
def _(mo):
    kv_users = mo.ui.slider(start=1, stop=32, step=1, value=1,
                            label="同時在線人數（各佔一份上下文）", show_value=True)
    kv_dtype = mo.ui.dropdown(
        options={"fp16 / bf16（2 bytes）": 2, "fp8（1 byte，KV 量化）": 1},
        value="fp16 / bf16（2 bytes）", label="KV 存成什麼型別")
    mo.vstack([kv_users, kv_dtype])
    return kv_dtype, kv_users


@app.cell
def _(kv_dtype, kv_users, np, plt):
    _kv_per_tok = 2 * 32 * 8 * 128 * kv_dtype.value  # bytes/token（8B 級 GQA）
    _ctx = np.array([2048, 8192, 32768, 131072])
    _gb = _ctx * kv_users.value * _kv_per_tok / 1024**3
    _labels = ["2k", "8k", "32k", "128k"]
    _colors = ["#4C72B0" if g <= 8 else "#DD8452" if g <= 24 else "#C44E52" for g in _gb]
    _fig, _ax = plt.subplots(figsize=(7.0, 3.9))
    _bars = _ax.bar(_labels, _gb, color=_colors, edgecolor="#1C2B33", linewidth=1.1, zorder=3)
    for _i, _g in enumerate(_gb):
        _ax.text(_i, _g * 1.15, f"{_g:.2f} GB" if _g < 10 else f"{_g:.0f} GB",
                 ha="center", fontsize=10, fontweight="bold")
    _ax.axhline(24, color="#C44E52", linestyle="--", linewidth=1.5, zorder=2)
    _ax.text(3.4, 24 * 1.1, "RTX 4090 (24 GB)", ha="right", fontsize=9,
             color="#C44E52", fontweight="bold")
    _ax.set_yscale("log")
    _ax.set_ylim(_gb.min() * 0.4, max(_gb.max(), 30) * 4)
    _ax.set_ylabel("KV cache (GB, log)")
    _ax.set_title(f"KV cache = context x {kv_users.value} user(s) x {_kv_per_tok//1024} KB/token")
    _ax.grid(axis="y", alpha=0.3, zorder=0)
    _fig.tight_layout()
    _fig
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    預設值下 128k 上下文就是 **16 GB**——還沒算模型權重（8B fp16 要 15 GB）。
    這就是「窗越大越貴」的物理原因。

    更麻煩的是：每個請求的長度不一樣、還會邊聊邊長，KV 該怎麼擺？
    早期引擎替每個請求**預留最長長度**的連續空間，大部分位置空著——浪費率可達九成。
    **PagedAttention**（vLLM 的核心）借作業系統「分頁」的概念，把 KV 切成小塊、
    要用才配一塊，浪費率大降。這也是為什麼「用 vLLM」常常就是吞吐翻倍的第一步。

    ## 2️⃣ 量化：把 fp16 壓成 int4，丟掉多少？

    **量化（quantization）**把每個權重從 16 bit 浮點數壓成 8 bit 或 4 bit 整數，
    模型檔直接砍半、砍四分之三（8B：fp16 15 GB → int8 7.5 GB → int4 3.7 GB）。
    代價是**捨入誤差**。下面用 4096 個真權重（尺度 0.02 的常態分布）真的量化一次，
    量三種做法的平均誤差——重點在「離群值」開關：LLM 權重裡真的有少數特別大的值。
    """
    )
    return


@app.cell
def _(mo):
    q_outlier = mo.ui.switch(value=False, label="加入一個離群值（把其中一個權重改成 0.5）")
    q_outlier
    return (q_outlier,)


@app.cell
def _(np, plt, q_outlier):
    _rng = np.random.default_rng(0)
    _w = _rng.normal(0, 0.02, 4096).astype(np.float32)
    if q_outlier.value:
        _w[100] = 0.5

    def _absmax(x, bits, group=None):
        qmax = 2 ** (bits - 1) - 1
        if group:
            xs = x.reshape(-1, group)
            s = np.abs(xs).max(axis=1, keepdims=True) / qmax
            return (np.round(xs / s) * s).ravel()
        s = np.abs(x).max() / qmax
        return np.round(x / s) * s

    _errs = [
        ("int8 whole-tensor", np.abs(_absmax(_w, 8) - _w).mean(), "#4C72B0"),
        ("int4 whole-tensor", np.abs(_absmax(_w, 4) - _w).mean(), "#C44E52"),
        ("int4 group-128", np.abs(_absmax(_w, 4, group=128) - _w).mean(), "#55A868"),
    ]
    _fig, _ax = plt.subplots(figsize=(7.0, 3.7))
    _names = [e[0] for e in _errs]
    _vals = [e[1] for e in _errs]
    _ax.bar(_names, _vals, color=[e[2] for e in _errs],
            edgecolor="#1C2B33", linewidth=1.1, zorder=3)
    for _i, _v in enumerate(_vals):
        _ax.text(_i, _v * 1.08, f"{_v:.6f}", ha="center", fontsize=10, fontweight="bold")
    _ax.set_ylabel("mean abs error (weight scale 0.02)")
    _ax.set_title("one outlier wrecks whole-tensor int4 -> group-wise fixes it"
                  if q_outlier.value else "no outlier: int4 error is small and benign")
    _ax.grid(axis="y", alpha=0.3, zorder=0)
    _fig.tight_layout()
    _fig
    return


@app.cell(hide_code=True)
def _(mo, q_outlier):
    _msg = (
        "打開離群值之後：int4 全張量的誤差跳了約 **5 倍**（0.0028 → 0.0149）——"
        "一個 0.5 的權重把整條量化刻度撐大，其他 4095 個小權重全被犧牲。"
        "而 **128 個一組**分開量化（綠色）幾乎不受影響：災難被隔離在那一組裡。"
        if q_outlier.value else
        "目前沒有離群值，int4 的誤差看起來無害。**把上面的開關打開**，"
        "看一個離群值怎麼毀掉整張量的量化。"
    )
    mo.md(
        f"""
    {_msg}

    這就是 **GPTQ／AWQ／GGUF** 這些主流量化格式都做「分組量化」的原因
    （常見 32～128 個權重一組，各存各的縮放係數）。
    你在 Ollama 模型名看到的 `q4_K_M` 就是 GGUF 的 4-bit 分組量化變體。

    ## 3️⃣ 投機解碼：小模型先猜、大模型批次驗證

    自迴歸是串行的——但**驗證可以平行**。投機解碼（speculative decoding）讓一個
    小模型先連猜 k 個 token，大模型**一次前向**把 k 個全部驗完：猜對的照單全收，
    猜錯的從錯的那格重來。平均每輪能收下幾個，取決於小模型的**接受率 α**：
    """
    )
    return


@app.cell
def _(mo):
    sd_alpha = mo.ui.slider(start=0.5, stop=0.95, step=0.05, value=0.8,
                            label="接受率 α（小模型每個 token 被大模型認可的機率）", show_value=True)
    sd_alpha
    return (sd_alpha,)


@app.cell
def _(np, plt, sd_alpha):
    _K = 4
    _a_grid = np.linspace(0.5, 0.95, 100)
    _closed = (1 - _a_grid ** (_K + 1)) / (1 - _a_grid)
    # 蒙地卡羅在目前 α 互驗（教學模型：每 token 獨立以 α 接受）
    _rng = np.random.default_rng(1)
    _acc = _rng.random((20000, _K)) < sd_alpha.value
    _n_acc = np.where(_acc.all(axis=1), _K, np.argmin(_acc, axis=1))
    _mc = float((_n_acc + 1).mean())
    _here = (1 - sd_alpha.value ** (_K + 1)) / (1 - sd_alpha.value)
    _fig, _ax = plt.subplots(figsize=(7.0, 3.9))
    _ax.plot(_a_grid, _closed, color="#55A868", linewidth=2.6, zorder=3,
             label="expected tokens per big-model pass (k=4)")
    _ax.axhline(1.0, color="#C44E52", linestyle="--", linewidth=1.5, zorder=2)
    _ax.text(0.505, 1.06, "1.0 = plain autoregressive", fontsize=9,
             color="#C44E52", fontweight="bold")
    _ax.plot([sd_alpha.value], [_mc], "o", color="#1C2B33", markersize=9, zorder=5)
    _ax.annotate(f"Monte-Carlo check: {_mc:.2f}", xy=(sd_alpha.value, _mc),
                 xytext=(sd_alpha.value - 0.16, _mc + 0.5),
                 fontsize=10, fontweight="bold")
    _ax.set_xlabel("acceptance rate (alpha)")
    _ax.set_ylabel("tokens produced per verification")
    _ax.set_title(f"alpha={sd_alpha.value:.2f} -> {_here:.2f} tokens per pass")
    _ax.legend(fontsize=9, loc="upper left")
    _ax.grid(alpha=0.3)
    _fig.tight_layout()
    _fig
    return


@app.cell(hide_code=True)
def _(mo, sd_alpha):
    _here = (1 - sd_alpha.value ** 5) / (1 - sd_alpha.value)
    mo.md(
        f"""
    α = {sd_alpha.value:.2f} 時每次大模型前向平均產出 **{_here:.2f} 個 token**
    （曲線是封閉式期望、黑點是兩萬次蒙地卡羅——兩者對得上，這是教學模型：
    真實系統的接受率會隨內容波動）。小模型跟大模型越「像」、文字越可預測
    （程式碼、格式化輸出），α 越高、賺越多；天馬行空的創意寫作 α 低，就不划算。

    **關鍵性質：輸出分布不變。**大模型只收「自己也會這樣選」的 token，
    所以這是免費的加速——不像量化有精度代價。

    ## 4️⃣ Continuous Batching：別讓 GPU 等人

    GPU 一次算一批（batch）最划算。但**靜態批次**要等整批全部生成完才換下一批——
    先寫完的請求佔著位子空轉，利用率被最長的那個請求拖垮。
    **連續批次（continuous batching）**每生成一步都檢查：誰完成了就送走、
    空位馬上補新請求。下面是一個排程模擬（教學模型：8 個槽位、
    請求長度 20–200 隨機、佇列滿載）：
    """
    )
    return


@app.cell
def _(mo):
    cb_seed = mo.ui.slider(start=0, stop=9, step=1, value=0,
                           label="換一批隨機請求（seed）", show_value=True)
    cb_seed
    return (cb_seed,)


@app.cell
def _(cb_seed, np, plt):
    _SLOTS, _STEPS = 8, 400
    _rng = np.random.default_rng(cb_seed.value)
    _lengths = _rng.integers(20, 200, 1000)

    def _run(continuous):
        q = list(_lengths)
        slot = [0] * _SLOTS
        busy = total = 0
        for _t in range(_STEPS):
            if continuous or all(s == 0 for s in slot):
                for i in range(_SLOTS):
                    if slot[i] == 0 and q:
                        slot[i] = int(q.pop(0))
            busy += sum(1 for s in slot if s > 0)
            total += _SLOTS
            slot = [max(0, s - 1) for s in slot]
        return busy / total

    _us, _uc = _run(False), _run(True)
    _fig, _ax = plt.subplots(figsize=(7.0, 3.4))
    _ax.barh(["static batching", "continuous batching"], [_us * 100, _uc * 100],
             color=["#C44E52", "#55A868"], edgecolor="#1C2B33", linewidth=1.1, zorder=3)
    for _i, _u in enumerate([_us, _uc]):
        _ax.text(_u * 100 - 2, _i, f"{_u:.0%}", ha="right", va="center",
                 fontsize=12, fontweight="bold", color="white")
    _ax.set_xlim(0, 105)
    _ax.set_xlabel("GPU slot utilization (%)")
    _ax.set_title("same requests, same GPU - only the scheduler differs")
    _ax.grid(axis="x", alpha=0.3, zorder=0)
    _fig.tight_layout()
    _fig
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    多換幾個 seed：靜態批次穩定卡在六成上下，連續批次在佇列滿載時逼近 100%。
    這跟 **Flash Attention** 是兩層不同的優化：Flash Attention 在 **kernel 層**
    重排注意力計算的記憶體存取（不搬進搬出慢吞吞的顯存中繼站），
    連續批次在**排程層**填滿空位——兩個一起用，才有 vLLM 那種吞吐量。

    ## 5️⃣ MoE：參數很多，每次只用一點

    **MoE（Mixture of Experts）**把每層的 FFN 換成一排「專家」，
    每個 token 由路由器挑 2 個專家處理——**總參數很大、每個 token 實際過的參數很小**。
    用 Mixtral 8x7B 的真實架構算一次帳：
    """
    )
    return


@app.cell
def _():
    # Mixtral 8x7B 參數帳（真實架構規格：32 層、hidden 4096、8 個專家、top-2）
    V, H, L, INTER, NKV = 32000, 4096, 32, 14336, 8
    attn = H * H + 2 * H * (NKV * 128) + H * H
    expert = 3 * H * INTER          # gate/up/down 三塊
    router = H * 8
    per_layer_total = attn + 8 * expert + router + 2 * H
    per_layer_active = attn + 2 * expert + router + 2 * H
    total = V * H + L * per_layer_total + H + V * H
    active = V * H + L * per_layer_active + H + V * H
    print(f"總參數        : {total/1e9:.1f}B（要放進記憶體的量）")
    print(f"每 token 啟用 : {active/1e9:.1f}B（每一步實際計算的量）")
    print(f"啟用比例      : {active/total:.0%} —— 大而不貴的祕密")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    46.7B 的模型、每個 token 只算 12.9B——**記憶體照 46.7B 付、計算照 12.9B 付**。
    DeepSeek-V3 把這招推到 671B 總參數／每 token 只啟用 37B（公開規格），
    再配上自家的 **MLA**（把 KV 先壓進低秩空間再展開，KV cache 大幅縮小）——
    一次解掉「算力」與「KV 記憶體」兩個瓶頸。

    ## 6️⃣ 你的實驗區

    下面是你的實驗區。挑戰在左頁「換你動手」，做完再開解答對照。
    """
    )
    return


@app.cell
def _(mo):
    my_model = mo.ui.dropdown(
        options={"8B 級（8.03B 參數、32 層）": (8.03e9, 32), "70B 級（70.6B 參數、80 層）": (70.6e9, 80)},
        value="8B 級（8.03B 參數、32 層）",
        label="模型大小",
    )
    my_quant = mo.ui.dropdown(
        options={"fp16（2 bytes）": 2.0, "int8（1 byte）": 1.0, "int4（0.5 byte）": 0.5},
        value="int4（0.5 byte）",
        label="權重量化",
    )
    my_vram = mo.ui.slider(
        4, 96, 2, value=12, label="你的顯卡有多少 VRAM（GB）", show_value=True
    )
    mo.vstack(
        [
            mo.md("**你的實驗區**——你的卡裝得下哪個組合？裝下之後還剩多少 KV 空間？"),
            mo.hstack([my_model, my_quant], justify="start", gap=2, wrap=True),
            my_vram,
        ]
    )
    return my_model, my_quant, my_vram


@app.cell
def _(mo, my_model, my_quant, my_vram):
    _params, _layers = my_model.value
    _weights = _params * my_quant.value / 1024**3
    _free = my_vram.value - _weights
    _kv_kb = 2 * _layers * 8 * 128 * 2 / 1024        # GQA 8 組 KV head、head_dim 128、fp16
    _ctx = _free * 0.8 * 1024**2 / _kv_kb if _free > 0 else 0
    mo.md(
        f"""
    | | |
    | --- | --- |
    | 權重佔用 | **{_weights:.1f} GB** ／ 你有 {my_vram.value} GB |
    | 裝得下嗎 | **{"裝得下，還剩 %.1f GB" % _free if _free > 0 else "裝不下，差 %.1f GB" % -_free}** |
    | 剩餘空間能放多少 KV | **{_ctx:,.0f} tokens**（每 token {_kv_kb:.0f} KB，八成折算） |

    權重是**入場費**，KV 才是隨用量長大的那一塊——先看裝不裝得下，再看還剩多少位子給上下文。
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.accordion(
        {
            "💡 LEVEL 1 參考解答": mo.md(
                r"""
    12 GB 的卡跑 8B 級，量化下拉三次：

    | 量化 | 權重 | 12 GB 裝得下？ | 剩餘可放 KV |
    |---|---|---|---|
    | fp16 | 14.96 GB | **裝不下**（差 2.96 GB） | — |
    | int8 | 7.48 GB | 裝得下，剩 4.5 GB | 29,632 tokens |
    | int4 | 3.74 GB | 裝得下，剩 8.3 GB | **54,138 tokens** |

    順序值得記：**先量化、再談卸載**——量化把需求直接變小，
    常常整個「裝不下」的問題就消失了。
    """
            ),
            "💡 LEVEL 2 參考解答": mo.md(
                r"""
    把 3️⃣ 的 α 拉到 0.95：每輪期望 4.52 個 token（k=4 時上限是 5）。
    但注意分母——投機解碼的收益是「省下大模型的串行步數」，
    小模型自己也要花時間猜。如果小模型不夠小（比如用 7B 幫 8B 猜），
    猜的成本吃掉驗的收益，帳就不划算了。實務上草稿模型通常比目標模型小一個數量級以上。
    """
            ),
            "💡 LEVEL 3 提示": mo.md(
                r"""
    「壓 KV」的三條路其實你都學過了：

    1. **KV 量化**（1️⃣ 的 fp8 選項）：型別砍半 → KV 砍半
    2. **GQA**：KV head 數少於 Q head 數（8B 級是 32 個 Q head 共用 8 組 KV）——
       公式裡的「KV head 數」就是它省的
    3. **MLA**（5️⃣）：連 KV 本身都先壓進低秩空間

    驗證方法：把 1️⃣ 的公式各代一次，算 128k 上下文在三種做法下的 GB 數，
    看誰省最多、各付出什麼代價（精度／架構改動）。
    """
            ),
        }
    )
    return


if __name__ == "__main__":
    app.run()
