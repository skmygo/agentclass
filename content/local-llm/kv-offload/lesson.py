import marimo

__generated_with = "0.23.16"
app = marimo.App(width="medium", app_title="KV Cache 分層：LMCache 與 SSD 卸載（實驗場）")


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    # 🧪 KV Cache 分層：LMCache 與 SSD 卸載（實驗場）

    這是本課的**實驗場**。左側教學讀到哪，就回到這裡動手做——
    每個實驗都有**滑桿與選項**可以拉，拉完右邊立刻重算——
    所有數字都是當場算出來的，不是預錄的畫面。

    這一課的算盤只有兩筆帳：**KV 有多大**（決定放得下哪一層），
    **載回來比重算快多少**（決定值不值得）。兩筆都在下面真的算。
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
    from matplotlib.patches import Patch
    return Patch, np, plt


@app.cell
def _():
    # ── 三層儲存的頻寬量級（GB/s）。想換成自己機器實測的值就改這裡 ──
    BW_GPU = 1500.0   # HBM：GPU 自己的 KV pool，本來就在上面，不用搬
    BW_CPU = 50.0     # DDR：LMCACHE_LOCAL_CPU 收的地方
    BW_SSD = 6.0      # PCIe NVMe：LMCACHE_LOCAL_DISK，本課主角
    HEAD_DIM = 128    # 每個 attention head 的維度，Llama / Qwen 這一系幾乎都是 128
    return BW_CPU, BW_GPU, BW_SSD, HEAD_DIM


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 1️⃣ 先算清楚：你的 KV 有多大

    每一個 token 的 KV 大小完全由架構決定，跟你問什麼無關：

    ```
    每 token 位元組 = 2（K 和 V） × 層數 × KV head 數 × head 維度 × 每個數的位元組
    ```

    拉下面三根桿子換成你自己模型的規格。預設值是 **8B 級 GQA 模型**
    （32 層 / 8 個 KV head / fp16），算出來剛好是常被引用的那個數字。
    """
    )
    return


@app.cell
def _(mo):
    n_layers = mo.ui.slider(start=8, stop=80, step=1, value=32,
                            label="層數", show_value=True)
    n_kv_heads = mo.ui.slider(start=1, stop=64, step=1, value=8,
                              label="KV head 數（GQA 會遠小於 Q head 數）", show_value=True)
    kv_dtype = mo.ui.dropdown(
        options={"fp16 / bf16（2 bytes）": 2, "fp8（1 byte，KV 量化）": 1},
        value="fp16 / bf16（2 bytes）",
        label="KV 存成什麼型別",
    )
    mo.vstack([n_layers, n_kv_heads, kv_dtype])
    return kv_dtype, n_kv_heads, n_layers


@app.cell
def _(HEAD_DIM, kv_dtype, n_kv_heads, n_layers):
    kv_bytes_per_token = 2 * n_layers.value * n_kv_heads.value * HEAD_DIM * kv_dtype.value
    kv_kb_per_token = kv_bytes_per_token / 1024
    kv_gb_per_token = kv_bytes_per_token / 1024**3
    return kv_bytes_per_token, kv_gb_per_token, kv_kb_per_token


@app.cell(hide_code=True)
def _(kv_kb_per_token, mo, n_kv_heads, n_layers):
    mo.md(
        f"""
    **每 token 的 KV ＝ {kv_kb_per_token:.0f} KB**
    （2 × {n_layers.value} 層 × {n_kv_heads.value} 個 KV head × 128 維 × 型別位元組）。

    這個數字乘上「上下文長度 × 同時服務的人數」就是你要找地方放的東西。
    下面用兩根桿子設定你機器的兩道門檻，看六個典型場景各自落在哪一層。
    """
    )
    return


@app.cell
def _(mo):
    vram_free = mo.ui.slider(start=2, stop=80, step=1, value=10,
                             label="扣掉模型權重後，快取還能用的 VRAM (GB)", show_value=True)
    cpu_ram = mo.ui.slider(start=8, stop=512, step=8, value=64,
                           label="這台機器的 CPU RAM (GB)", show_value=True)
    mo.vstack([vram_free, cpu_ram])
    return cpu_ram, vram_free


@app.cell
def _(Patch, cpu_ram, kv_bytes_per_token, np, plt, vram_free):
    _labels = ["2k\nx1", "8k\nx1", "32k\nx1", "8k\nx10", "128k\nx1", "1M\nx1"]
    _tokens = np.array([2048, 8192, 32768, 81920, 131072, 1_000_000], dtype=float)
    _gb = _tokens * kv_bytes_per_token / 1024**3
    _v, _c = float(vram_free.value), float(cpu_ram.value)
    _tier = np.where(_gb < _v, 0, np.where(_gb < _c, 1, 2))
    _palette = ["#4C72B0", "#DD8452", "#55A868"]
    _fig, _ax = plt.subplots(figsize=(7.2, 4.4))
    _ax.bar(_labels, _gb, color=[_palette[t] for t in _tier],
            edgecolor="#1C2B33", linewidth=1.1, zorder=3)
    for _i, _g in enumerate(_gb):
        _ax.text(_i, _g * 1.18, f"{_g:.2f}" if _g < 1 else f"{_g:.0f}",
                 ha="center", fontsize=10, fontweight="bold", zorder=4)
    _ax.axhline(_v, color="#4C72B0", linestyle="--", linewidth=1.6, zorder=2)
    _ax.axhline(_c, color="#DD8452", linestyle="--", linewidth=1.6, zorder=2)
    _ax.text(5.45, _v, f" free VRAM {_v:.0f}GB", va="bottom", ha="right",
             fontsize=9, color="#4C72B0", fontweight="bold")
    _ax.text(5.45, _c, f" CPU RAM {_c:.0f}GB", va="bottom", ha="right",
             fontsize=9, color="#DD8452", fontweight="bold")
    _ax.set_yscale("log")
    _ax.set_ylim(_gb.min() * 0.35, max(_gb.max(), _c) * 6)
    _ax.set_ylabel("KV cache needed (GB, log)")
    _ax.set_title("context x concurrency -> which tier has to hold it")
    _ax.grid(axis="y", alpha=0.3, zorder=0)
    _ax.legend(handles=[Patch(facecolor=_palette[0], edgecolor="#1C2B33", label="fits in VRAM"),
                        Patch(facecolor=_palette[1], edgecolor="#1C2B33", label="needs CPU RAM tier"),
                        Patch(facecolor=_palette[2], edgecolor="#1C2B33", label="needs SSD tier")],
               fontsize=9, loc="upper left")
    _fig.tight_layout()
    _fig
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    預設值下有件事值得停下來看：**128k 上下文只要 16 GB，10 個人各 8k 也才 10 GB**——
    VRAM 放不下沒錯，但一台 64 GB RAM 的個人機，**CPU 那一層根本用不完**。
    真正把 CPU RAM 也擠爆的是最右邊那根：百萬級上下文，或人數再乘上去。

    先記住這個結論，第 4️⃣ 節會把它做成一個判斷器。

    ## 2️⃣ 拿 IO 換計算：載回 vs 重算

    同一段前綴第二次出現時，你有兩個選擇：

    - **重算**：全量 prefill，時間 ＝ `前綴長度 ÷ prefill 吞吐`
    - **載回**：從 CPU RAM 或 SSD 把算好的 KV 搬回 GPU，時間 ＝ `KV 大小 ÷ 該層頻寬`

    兩條線都跟前綴長度成正比，所以誰快誰慢從第一個 token 就決定了。
    下面把你引擎的 prefill 吞吐填進去（vLLM 啟動後壓一次長 prompt 就量得到）：
    """
    )
    return


@app.cell
def _(mo):
    prefill_tps = mo.ui.slider(start=200, stop=20000, step=200, value=2000,
                               label="你的 prefill 吞吐（tokens/秒）", show_value=True)
    prefill_tps
    return (prefill_tps,)


@app.cell
def _(BW_CPU, BW_SSD, kv_gb_per_token, np, plt, prefill_tps):
    _x = np.linspace(0, 64000, 400)
    _t_prefill = _x / prefill_tps.value
    _t_ssd = _x * kv_gb_per_token / BW_SSD
    _t_cpu = _x * kv_gb_per_token / BW_CPU
    _fig, _ax = plt.subplots(figsize=(7.2, 4.4))
    _ax.fill_between(_x, _t_ssd, _t_prefill, where=_t_prefill >= _t_ssd,
                     color="#55A868", alpha=0.15, zorder=1)
    _ax.plot(_x, _t_prefill, color="#C44E52", linewidth=2.6, label="recompute (prefill)", zorder=3)
    _ax.plot(_x, _t_ssd, color="#55A868", linewidth=2.4, label="load back from SSD", zorder=3)
    _ax.plot(_x, _t_cpu, color="#DD8452", linewidth=2.4, label="load back from CPU RAM", zorder=3)
    _at10k = 10000 / prefill_tps.value - 10000 * kv_gb_per_token / BW_SSD
    _ax.axvline(10000, color="#9AA7AE", linestyle=":", linewidth=1.4, zorder=2)
    _ax.annotate(f"at 10k tokens: SSD reuse saves {_at10k:.2f}s",
                 xy=(10000, 10000 / prefill_tps.value),
                 xytext=(13000, 10000 / prefill_tps.value * 1.05),
                 fontsize=10, fontweight="bold", color="#1C2B33")
    _ax.set_xlabel("shared prefix length (tokens)")
    _ax.set_ylabel("time to have the KV ready (s)")
    _ax.set_title("both scale linearly - the gap is what you bank")
    _ax.legend(fontsize=9)
    _ax.grid(alpha=0.3)
    _fig.tight_layout()
    _fig
    return


@app.cell(hide_code=True)
def _(BW_SSD, kv_gb_per_token, mo, prefill_tps):
    _saved = 10000 / prefill_tps.value - 10000 * kv_gb_per_token / BW_SSD
    mo.md(
        f"""
    綠色那塊面積就是省下的時間。注意它的形狀：**兩條線都是直線**，
    所以前綴拉長不會讓「快幾倍」變好，只會讓「省幾秒」變大——
    目前的設定下，一段 10k 的前綴每命中一次省 **{_saved:.2f} 秒**，
    換成 40k 的長文件就是四倍的絕對時間。

    真正決定「快幾倍」的是斜率比，也就是下一節。

    ## 3️⃣ 什麼時候賺：加速比與損益平衡

    把兩條線相除，長度就消掉了：

    ```
    加速比 = 重算時間 / 載回時間 = 該層頻寬 / (prefill 吞吐 × 每 token 的 KV)
    ```

    所以只有兩件事會讓你賺：**計算越重**（prefill 吞吐越低）、**KV 越小**
    （GQA、KV 量化）。這也是為什麼量化模型反而更划算——反量化讓 prefill 變重，
    KV 又相對小，分子分母同時往好的方向走。
    """
    )
    return


@app.cell
def _(BW_CPU, BW_SSD, kv_gb_per_token, np, plt, prefill_tps):
    _tps = np.logspace(np.log10(100), np.log10(200000), 300)
    _r_ssd = BW_SSD / (_tps * kv_gb_per_token)
    _r_cpu = BW_CPU / (_tps * kv_gb_per_token)
    _here = BW_SSD / (prefill_tps.value * kv_gb_per_token)
    _breakeven = BW_SSD / kv_gb_per_token
    _fig, _ax = plt.subplots(figsize=(7.2, 4.4))
    _ax.plot(_tps, _r_cpu, color="#DD8452", linewidth=2.4, label="CPU RAM tier")
    _ax.plot(_tps, _r_ssd, color="#55A868", linewidth=2.6, label="SSD tier")
    _ax.axhline(1.0, color="#C44E52", linestyle="--", linewidth=1.6)
    _ax.text(120, 1.08, "1.0x = break even (recompute is just as fast)",
             fontsize=9, color="#C44E52", fontweight="bold")
    _ax.plot([prefill_tps.value], [_here], "o", color="#1C2B33", markersize=9, zorder=5)
    _ax.annotate(f"you: {_here:.0f}x ceiling", xy=(prefill_tps.value, _here),
                 xytext=(prefill_tps.value * 1.3, _here * 1.5),
                 fontsize=10, fontweight="bold")
    _ax.set_xscale("log")
    _ax.set_yscale("log")
    _ax.set_xlabel("prefill throughput (tokens/s)  ->  cheaper compute")
    _ax.set_ylabel("upper-bound speedup (x)")
    _ax.set_title(f"bandwidth-only ceiling - SSD ties recompute at {_breakeven:,.0f} tok/s")
    _ax.legend(fontsize=9)
    _ax.grid(alpha=0.3, which="both")
    _fig.tight_layout()
    _fig
    return


@app.cell(hide_code=True)
def _(BW_SSD, kv_gb_per_token, mo, prefill_tps):
    _ceiling = BW_SSD / (prefill_tps.value * kv_gb_per_token)
    mo.md(
        f"""
    /// warning | 這條曲線是**上限**，不是預測

    模型裡只有頻寬。真實世界還要扣掉 chunk 查表、PCIe 搬運、引擎排程、
    OS page cache 命不命中——一份公開實測（RTX 4090、vLLM + LMCache 0.5.0、2026-07）
    量到的是 **0.6B bf16 → 1.1x、1.7B FP8 → 1.2x、4B-AWQ → 2.3x**，
    遠低於純頻寬算出來的上限（目前這組設定下是 {_ceiling:.0f}x）。

    模型告訴你**誰有機會贏、方向往哪走**；要知道**實際贏多少**，只能自己量。
    ///

    ## 4️⃣ 你需要 SSD 層嗎

    把前面兩筆帳合起來就是一個判斷器。它問三件事：
    前綴會不會重複用、KV 有多大、你機器的兩道門檻在哪。
    """
    )
    return


@app.cell
def _(mo):
    ctx_len = mo.ui.dropdown(
        options={"2k": 2048, "8k": 8192, "32k": 32768, "128k": 131072,
                 "256k": 262144, "1M": 1_000_000},
        value="128k",
        label="單一請求的上下文長度",
    )
    concurrency = mo.ui.slider(start=1, stop=64, step=1, value=1,
                               label="同時在線、各自佔一份長上下文的人數", show_value=True)
    has_reuse = mo.ui.switch(value=True, label="這段長前綴會被重複使用（RAG 固定知識、共用 system prompt、多輪 agent）")
    mo.vstack([ctx_len, concurrency, has_reuse])
    return concurrency, ctx_len, has_reuse


@app.cell
def _(
    concurrency,
    cpu_ram,
    ctx_len,
    has_reuse,
    kv_bytes_per_token,
    mo,
    vram_free,
):
    _kv = ctx_len.value * concurrency.value * kv_bytes_per_token / 1024**3
    _v, _c = float(vram_free.value), float(cpu_ram.value)
    if not has_reuse.value:
        _color, _head = "#C44E52", "先別急著開任何卸載層"
        _body = ("每次都是全新的 prompt，就沒有東西可以複用——快取層對這種流量完全無效，"
                 "每一發都是冷啟動全量 prefill。先確認你的流量真的有重複前綴，再談要放哪一層。")
    elif _kv < _v:
        _color, _head = "#4C72B0", "VRAM 就裝得下，什麼都不用開"
        _body = (f"這些 KV 只要 {_kv:.2f} GB，比你留給快取的 {_v:.0f} GB VRAM 還小。"
                 "vLLM 內建的 prefix cache 已經在做這件事，而且是在最快的那一層。")
    elif _kv < _c:
        _color, _head = "#DD8452", "開 CPU 層就好（LMCACHE_LOCAL_CPU）"
        _body = (f"需要 {_kv:.1f} GB：VRAM 放不下，但這台機器的 {_c:.0f} GB CPU RAM 綽綽有餘。"
                 "個人／小團隊場景多半停在這一站——CPU RAM 比 SSD 快一個數量級，"
                 "裝得下就沒有理由再往下丟。")
    else:
        _color, _head = "#55A868", "這才輪到 SSD 層（LMCACHE_LOCAL_DISK）"
        _body = (f"需要 {_kv:.0f} GB，CPU RAM 的 {_c:.0f} GB 也吃不下了。"
                 "走到這一格通常代表你在跑多人共用、長上下文的伺服器——"
                 "這正是分層儲存被設計出來要解的場景。")
    mo.Html(
        f"""
    <div style="border:2px solid {_color};border-radius:14px;padding:16px 18px;font-family:system-ui,sans-serif">
      <div style="font-size:12px;letter-spacing:.08em;font-weight:800;color:{_color};margin-bottom:6px">
        KV 需求 {_kv:.2f} GB ／ 可用 VRAM {_v:.0f} GB ／ CPU RAM {_c:.0f} GB
      </div>
      <div style="font-size:18px;font-weight:800;margin-bottom:8px">{_head}</div>
      <div style="font-size:14px;line-height:1.75">{_body}</div>
    </div>
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    多試幾組：把人數拉到 20、上下文選 128k，就會看到判斷從橘色翻成綠色——
    **人數才是把 CPU RAM 擠爆的主因**，不是單一請求有多長。

    ## 5️⃣ 你的實驗區

    這一課所有的拉桿都在上面，下面這張卡把它們的當前值收在一起。建議挑戰（由易到難）：

    1. **LEVEL 1**：把 1️⃣ 的「KV 存成什麼型別」改成 fp8，看 128k 的需求掉到多少、
       4️⃣ 的判斷會不會從「開 CPU 層」翻回「VRAM 就裝得下」。
    2. **LEVEL 2**：3️⃣ 圖表標題上那個「SSD ties recompute at N tok/s」就是**損益平衡吞吐**
       （頻寬 ÷ 每 token 的 KV）。為什麼這個純頻寬上限幾乎永遠大於 1，
       實測卻只有 1.1–2.3x？差額跑到哪去了？
    3. **LEVEL 3**：把上面每一根拉桿都換成你自己服務的真實數字（模型層數與 KV head 數看
       config、prefill 吞吐壓一次長 prompt 量），看 4️⃣ 的判斷器怎麼說；
       再用你量到的實際加速比回推「你真正吃到了標稱頻寬的幾成」。

    做完記得：**點左側教學頁的「下載 .py」把這份 notebook 帶走**，
    在自己電腦用 `uvx marimo edit lesson.py` 打開，每一格程式碼都能改。
    """
    )
    return


@app.cell
def _(
    BW_SSD,
    concurrency,
    cpu_ram,
    ctx_len,
    kv_bytes_per_token,
    kv_gb_per_token,
    mo,
    prefill_tps,
    vram_free,
):
    _need = ctx_len.value * concurrency.value * kv_gb_per_token
    _tier = (
        "VRAM"
        if _need < vram_free.value
        else "CPU RAM"
        if _need < cpu_ram.value
        else "SSD"
    )
    _breakeven = BW_SSD / kv_gb_per_token
    mo.md(
        f"""
    **你目前這台機器**（上面所有拉桿的當前值）：

    | | |
    | --- | --- |
    | 每 token 的 KV | **{kv_bytes_per_token / 1024:.0f} KB** |
    | {ctx_len.selected_key} 上下文 × {concurrency.value} 人 | **{_need:.2f} GB** → 放在 **{_tier}** |
    | SSD 損益平衡吞吐 | **{_breakeven:,.0f} tokens/s** |
    | 你的 prefill 吞吐 | {prefill_tps.value:,} tokens/s |
    | 純頻寬算出來的加速比 | **{_breakeven / prefill_tps.value:.1f}x** |

    最後一列是**上限**，不是你會拿到的數字——實測只有 1.1–2.3x。
    差額在哪？那正是 LEVEL 2 的題目。
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.accordion(
        {
            "💡 LEVEL 1 參考解答": mo.md(
                r"""
    把 1️⃣ 的「KV 存成什麼型別」選成 **fp8（1 byte，KV 量化）**。

    每 token 的 KV 從 128 KB 掉到 **64 KB**，128k 上下文的需求從 16 GB 掉到 **8 GB**——
    比預設的 10 GB 可用 VRAM 還小，4️⃣ 的判斷器會從橘色（開 CPU 層）翻回藍色（VRAM 就裝得下）。

    這就是為什麼「要不要卸載」不該是第一個問題：**先看能不能把 KV 變小**
    （GQA、KV 量化、縮短上下文），常常整個問題就消失了。
    """
            ),
            "💡 LEVEL 2 參考解答": mo.md(
                r"""
    損益平衡點是「加速比 ＝ 1」的那個吞吐：**SSD 頻寬 ÷ 每 token 的 KV**。
    預設設定（8B 級 GQA、fp16、每 token 128 KB、SSD 6 GB/s）算出來是
    `6.0 / (128/1024/1024) = 49,152 tokens/s`——3️⃣ 的圖標題與總結卡上都是這個數字。

    要 prefill 快到每秒五萬個 token，重算才追得上從 SSD 載回——一般服務離這個數字很遠，
    所以**純頻寬上限幾乎永遠大於 1**。但實測只有 1.1–2.3x，差額全在頻寬以外：
    chunk 的查表與組裝、KV 從主機記憶體搬進 GPU 的 PCIe 傳輸、引擎的排程與批次、
    以及 OS page cache 命不命中（第二次跑常常比第一次快，因為根本沒碰到碟）。

    實務上的用法是反過來的：**用實測加速比回推你真正吃到了多少頻寬**，
    再決定要不要換更快的碟、還是先去修別的瓶頸。
    """
            ),
            "💡 LEVEL 3 提示": mo.md(
                r"""
    三個數字要自己量，不要猜：

    - **層數與 KV head 數**：模型的 `config.json` 看 `num_hidden_layers`、
      `num_key_value_heads`、`head_dim`（沒有 `head_dim` 就用 `hidden_size / num_attention_heads`）。
    - **prefill 吞吐**：送一發夠長的 prompt（例如 8k）、`max_tokens=1`，
      量 TTFT，用 `prompt 長度 / TTFT` 當估計值。
    - **SSD 頻寬**：`fio` 跑循序讀，或最陽春的 `dd` 讀一個大檔——
      重點是**別用規格書上的數字**，實際落地的常常只有一半。

    怎麼知道自己做對了：把量到的加速比除以模型算出的上限，
    得到一個 0–1 的「有效頻寬折扣」。如果它低到 0.05，代表 95% 的時間花在搬運以外的地方，
    這時候換更快的 SSD 完全沒有用——瓶頸不在那裡。
    """
            ),
        }
    )
    return


if __name__ == "__main__":
    app.run()
