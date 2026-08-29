import marimo

__generated_with = "0.23.16"
app = marimo.App(width="medium", app_title="Prompt Caching：連續對話的錢怎麼算（實驗場）")


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    # 🧪 Prompt Caching：連續對話的錢怎麼算（實驗場）

    這是本課的**實驗場**。左側教學讀到哪，就回到這裡動手做——
    每個實驗都有**滑桿與選項**可以拉，拉完右邊立刻重算——
    所有數字都是當場算出來的，不是預錄的畫面。

    這裡沒有任何網路呼叫：**帳單是照公開費率一筆一筆真算出來的**——
    每一個金額都是這幾格當場乘出來的，拉桿一動就重算。
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
    ## 1️⃣ 五種價錢：先把費率表放進程式裡

    連續對話會用到的價目只有五種。這張表是本課**唯一的費率來源**，
    後面每一筆金額都是拿它乘出來的。

    （示範用的是官方公開定價的其中一組；價格會調整，實際以官方定價頁為準。）
    """
    )
    return


@app.cell
def _(mo):
    # ===== 費率（每百萬 tokens，美元）=====
    BASE_IN = 10.0    # 一般輸入：沒被快取到的部分
    WRITE_5M = 12.5   # 快取寫入（5 分鐘 TTL）：新內容第一次進快取
    WRITE_1H = 20.0   # 快取寫入（1 小時 TTL）
    CACHE_HIT = 1.0   # 快取命中：重複讀取已快取的前綴
    OUTPUT = 50.0     # 模型產生的回答
    MTOK = 1_000_000

    mo.md(
        rf"""
    | 項目 | 每 MTok | 什麼時候付 |
    |---|---:|---|
    | Base Input | \${BASE_IN:.2f} | 沒被快取的一般輸入 |
    | Cache Write（5 分鐘） | \${WRITE_5M:.2f} | 新內容第一次寫入快取 |
    | Cache Write（1 小時） | \${WRITE_1H:.2f} | 改用長 TTL 時的寫入 |
    | **Cache Hit** | **\${CACHE_HIT:.2f}** | 重複讀取已快取的內容 |
    | Output | \${OUTPUT:.2f} | 模型產生的回答 |

    兩個決定一切的比值：**命中只要一般輸入的 1/{BASE_IN / CACHE_HIT:.0f}**，
    而寫入比一般輸入貴 {WRITE_5M / BASE_IN - 1:.0%}——貴的那一次，會被之後每一次命中賺回來。
    """
    )
    return BASE_IN, CACHE_HIT, MTOK, OUTPUT, WRITE_1H, WRITE_5M


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 2️⃣ 每輪只付三種錢：把一段對話跑成一張帳單

    連續對話的規則其實只有三行：

    - **舊內容**（之前所有對話歷史）：上一輪已經寫進快取了 → 走 **Cache Hit**
    - **新內容**（這一輪新增的問題）：第一次出現 → 付 **Cache Write**
    - **輸出**（模型的回答）：跟快取無關 → 照常計費

    對話歷史**只增不改**——每一輪都是在上一輪後面接東西，前面那一大段一個字都沒動。
    這正好就是「共用前綴」的定義，所以連續對話天然吃得到快取，不需要你做任何設定。

    下面的 `run_chat()` 是本課的計費引擎，後面每張圖都由它算出來。
    `breaks` 參數先不用管，第 5️⃣ 節才會用到。
    """
    )
    return


@app.cell
def _(BASE_IN, CACHE_HIT, MTOK, OUTPUT, WRITE_5M):
    def run_chat(n_rounds, sys_tok, q_tok, a_tok, cached=True, breaks=None, write_rate=None):
        """模擬一段連續對話的帳單，回傳每一輪的明細。

        sys_tok / q_tok / a_tok：系統提示、每輪問題、每輪回答的 token 數
        cached=False：完全不用快取，每輪整段歷史都以 Base Input 計價
        breaks={輪次: 額外 token}：這一輪前綴被動過（換模型／改工具／TTL 過期）
                                  → 整段歷史失效，必須重新寫入快取
        """
        write_rate = WRITE_5M if write_rate is None else write_rate
        breaks = breaks or {}
        rows, hist = [], 0  # hist = 目前已經在快取裡的前綴長度
        for i in range(1, n_rounds + 1):
            extra = breaks.get(i)
            new = (sys_tok + q_tok) if i == 1 else q_tok
            if extra is not None:
                new += extra  # 例如新增的工具定義，會長在系統提示層
            if not cached:
                inp = hist + new
                row = {"round": i, "hit": 0, "write": 0, "base": inp,
                       "cost": inp / MTOK * BASE_IN + a_tok / MTOK * OUTPUT}
            else:
                broken = extra is not None and i > 1
                write = (hist + new) if broken else new
                hit = 0 if broken else hist
                row = {"round": i, "hit": hit, "write": write, "base": 0,
                       "cost": write / MTOK * write_rate
                               + hit / MTOK * CACHE_HIT
                               + a_tok / MTOK * OUTPUT}
            rows.append(row)
            hist += new + a_tok  # 這輪的新內容與回答，下一輪就成了「舊歷史」

        return rows

    def total(rows):
        return sum(r["cost"] for r in rows)
    return run_chat, total


@app.cell(hide_code=True)
def _(BASE_IN, CACHE_HIT, MTOK, OUTPUT, WRITE_5M, mo, run_chat, total):
    # 經典情境：系統提示 10K、每輪問 1K、每輪答 2K，連續聊三輪
    _c = run_chat(3, 10_000, 1_000, 2_000)
    _p = run_chat(3, 10_000, 1_000, 2_000, cached=False)
    _lines = []
    for _r in _c:
        _hit_s = (
            rf"{_r['hit'] // 1000}K → \${_r['hit'] / MTOK * CACHE_HIT:.3f}" if _r["hit"] else "—"
        )
        _lines.append(
            rf"    | 第 {_r['round']} 輪 | {_hit_s} "
            rf"| {_r['write'] // 1000}K → \${_r['write'] / MTOK * WRITE_5M:.4f} "
            rf"| 2K → \${2_000 / MTOK * OUTPUT:.3f} | **\${_r['cost']:.4f}** |"
        )
    _table = "\n".join(_lines)
    mo.md(
        rf"""
    | 輪次 | 命中 \${CACHE_HIT:.0f}/MTok | 寫入 \${WRITE_5M:.2f}/MTok | 輸出 \${OUTPUT:.0f}/MTok | 小計 |
    |---|---|---|---|---:|
{_table}

    **三輪總計 \${total(_c):.4f}**，同一段對話完全不用快取要 **\${total(_p):.4f}**——
    省 {1 - total(_c) / total(_p):.0%}。

    看第 3 輪：{_c[2]['hit'] // 1000}K 的對話歷史只花了
    \${_c[2]['hit'] / MTOK * CACHE_HIT:.3f}（同樣這些 token 走一般輸入要
    \${_c[2]['hit'] / MTOK * BASE_IN:.2f}）。而且第 2、3 輪的小計幾乎一樣——
    **每輪成本趨於固定**，這是快取最舒服的地方：聊得再久，下一輪要花多少你都猜得到。
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 3️⃣ 拉桿：什麼時候省最多？

    三根拉桿，馬上看到「用快取 vs 不用快取」的累計帳單怎麼岔開。
    先猜再拉，看你的直覺準不準：

    - **系統提示拉長**（工具說明書、專案規範、長 prompt）→ 省更多還是更少？
    - **輪數拉長** → 省的比例會停在哪？把輪數拉到 1 呢？
    - **回答拉長** → 對「省的比例」是幫忙還是扯後腿？
    """
    )
    return


@app.cell
def _(mo):
    sys_slider = mo.ui.slider(
        start=0, stop=50, step=1, value=10, label="系統提示（K tokens）", show_value=True
    )
    rounds_slider = mo.ui.slider(
        start=1, stop=30, step=1, value=3, label="對話輪數", show_value=True
    )
    out_slider = mo.ui.slider(
        start=1, stop=8, step=1, value=2, label="每輪回答（K tokens）", show_value=True
    )
    mo.vstack([sys_slider, rounds_slider, out_slider])
    return out_slider, rounds_slider, sys_slider


@app.cell
def _(np, out_slider, plt, rounds_slider, run_chat, sys_slider):
    sim_n = rounds_slider.value
    sim_sys = sys_slider.value * 1000
    sim_a = out_slider.value * 1000
    sim_cached = run_chat(sim_n, sim_sys, 1_000, sim_a)
    sim_plain = run_chat(sim_n, sim_sys, 1_000, sim_a, cached=False)

    _x = np.arange(1, sim_n + 1)
    _cc = np.cumsum([r["cost"] for r in sim_cached])
    _pc = np.cumsum([r["cost"] for r in sim_plain])
    _fig, _axes = plt.subplots(2, 1, figsize=(6.4, 7.0))
    _axes[0].plot(_x, _pc, "o-", c="#C44E52", label="no cache")
    _axes[0].plot(_x, _cc, "o-", c="#55A868", label="with prompt caching")
    _axes[0].fill_between(_x, _cc, _pc, color="#55A868", alpha=0.15)
    _axes[0].set_xlabel("conversation round")
    _axes[0].set_ylabel("cumulative cost (USD)")
    _axes[0].set_title(
        f"total ${_pc[-1]:.3f} -> ${_cc[-1]:.3f}   (save {1 - _cc[-1] / _pc[-1]:.0%})"
    )
    _axes[0].legend()
    _axes[0].grid(alpha=0.3)
    _axes[1].plot(_x, [r["cost"] for r in sim_plain], "o-", c="#C44E52", label="no cache")
    _axes[1].plot(
        _x, [r["cost"] for r in sim_cached], "o-", c="#55A868", label="with prompt caching"
    )
    _axes[1].set_xlabel("conversation round")
    _axes[1].set_ylabel("cost of this round (USD)")
    _axes[1].set_title("per-round cost: rising vs. flat")
    _axes[1].set_ylim(bottom=0)
    _axes[1].legend()
    _axes[1].grid(alpha=0.3)
    _fig.tight_layout()
    _fig
    return sim_a, sim_cached, sim_n, sim_plain, sim_sys


@app.cell(hide_code=True)
def _(OUTPUT, mo, sim_cached, sim_n, sim_plain, sim_sys, total):
    _c, _p = total(sim_cached), total(sim_plain)
    _verdict = (
        f"省 {1 - _c / _p:.0%}"
        if _c < _p
        else f"**反而貴 {_c / _p - 1:.0%}**——只聊這麼幾輪就結束，"
        "寫入的溢價還沒被任何一次命中賺回來"
    )
    mo.md(
        rf"""
    系統提示 {sim_sys // 1000}K、聊 {sim_n} 輪：不用快取 \${_p:.3f}、用快取 \${_c:.3f} → {_verdict}。

    三個方向自己拉一次就記得住：**系統提示越長、輪數越多，省得越兇**
    （長前綴每輪都要被重新計價一次，快取就是專門吃這種重複）；
    **回答拉長反而讓比例縮水**，因為輸出那 \${OUTPUT:.0f}/MTok 不受快取影響——
    快取省的是 input，不是 output。
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 4️⃣ 錢到底花在哪：token 很多，錢很少

    上面看的是總額，這裡把它拆開。上圖是每輪的 **input token 數量**，
    下圖是每輪的**花費**——同一段對話，兩張圖的形狀完全不一樣：

    上面的綠色（已快取的歷史）越疊越高，下面那張卻幾乎貼在地上。
    這就是本課的核心：**舊歷史佔掉絕大多數 token，卻只佔一點點錢**。
    聊到後面，帳單的主角會變成藍色的輸出。
    """
    )
    return


@app.cell
def _(CACHE_HIT, MTOK, OUTPUT, WRITE_5M, np, plt, sim_a, sim_cached):
    _x = np.arange(1, len(sim_cached) + 1)
    _hit_t = np.array([r["hit"] for r in sim_cached]) / 1000.0
    _wr_t = np.array([r["write"] for r in sim_cached]) / 1000.0
    _hit_c = np.array([r["hit"] for r in sim_cached]) / MTOK * CACHE_HIT
    _wr_c = np.array([r["write"] for r in sim_cached]) / MTOK * WRITE_5M
    _out_c = np.full(len(sim_cached), sim_a / MTOK * OUTPUT)
    _fig, _axes = plt.subplots(2, 1, figsize=(6.4, 7.0))
    _axes[0].bar(_x, _hit_t, color="#55A868", label="cached history (hit)")
    _axes[0].bar(_x, _wr_t, bottom=_hit_t, color="#DD8452", label="new content (write)")
    _axes[0].set_xlabel("conversation round")
    _axes[0].set_ylabel("input tokens (K)")
    _axes[0].set_title("input tokens: the history keeps growing")
    _axes[0].legend(fontsize=8)
    _axes[0].grid(alpha=0.3, axis="y")
    _axes[1].bar(_x, _hit_c, color="#55A868", label="hit")
    _axes[1].bar(_x, _wr_c, bottom=_hit_c, color="#DD8452", label="write")
    _axes[1].bar(_x, _out_c, bottom=_hit_c + _wr_c, color="#4C72B0", label="output")
    _axes[1].set_xlabel("conversation round")
    _axes[1].set_ylabel("cost of this round (USD)")
    _axes[1].set_title("cost: the history is almost free")
    _axes[1].legend(fontsize=8)
    _axes[1].grid(alpha=0.3, axis="y")
    _fig.tight_layout()
    _fig
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 5️⃣ 真正貴的是「讓前綴改變」

    快取綁在**一模一樣的前綴**上。前綴一改，後面全部作廢，下一輪要整段重新寫入。
    三件事會改到前綴，而它們在帳單上的效果**完全一樣**：

    - **中途換模型**：快取跟模型綁定，換一次＝整段重讀
    - **對話中增減工具 / MCP**：工具定義住在系統提示層，一變前綴就換了（而且還變長）
    - **閒置超過 TTL**：沒人動它，但快取自己過期了

    差別不在單次代價，在**你控不控制得了、會發生幾次**。
    下面選一種情況，跟「乖乖聊到底」和「完全不用快取」擺在一起比：
    """
    )
    return


@app.cell
def _(mo):
    break_kind = mo.ui.dropdown(
        options={
            "只發生一次（換模型／TTL 過期）": "once",
            "中途加一個工具（系統提示 +2K）": "tool",
            "每輪都換模型比較答案": "every",
        },
        value="只發生一次（換模型／TTL 過期）",
        label="這段對話發生了什麼",
    )
    break_at = mo.ui.slider(
        start=2, stop=11, step=1, value=4, label="發生在第幾輪", show_value=True
    )
    mo.vstack([break_kind, break_at])
    return break_at, break_kind


@app.cell
def _(break_at, break_kind, np, plt, run_chat):
    BREAK_N = 12  # 這一節固定：聊 12 輪、系統提示 10K、每輪問 1K 答 2K
    _k = min(break_at.value, BREAK_N)
    if break_kind.value == "every":
        _breaks = {i: 0 for i in range(2, BREAK_N + 1)}
        _label = "switch model every round"
    elif break_kind.value == "tool":
        _breaks = {_k: 2_000}
        _label = f"add a tool at round {_k}"
    else:
        _breaks = {_k: 0}
        _label = f"prefix broken at round {_k}"

    good = run_chat(BREAK_N, 10_000, 1_000, 2_000)
    broken = run_chat(BREAK_N, 10_000, 1_000, 2_000, breaks=_breaks)
    nocache = run_chat(BREAK_N, 10_000, 1_000, 2_000, cached=False)

    _x = np.arange(1, BREAK_N + 1)
    _fig, _ax = plt.subplots(figsize=(8.6, 4.4))
    _ax.plot(_x, np.cumsum([r["cost"] for r in nocache]), "o-", c="#C44E52",
             label="no cache at all")
    _ax.plot(_x, np.cumsum([r["cost"] for r in broken]), "o-", c="#DD8452", label=_label)
    _ax.plot(_x, np.cumsum([r["cost"] for r in good]), "o-", c="#55A868",
             label="never touch the prefix")
    _ax.set_xlabel("conversation round")
    _ax.set_ylabel("cumulative cost (USD)")
    _ax.set_title("12 rounds, 10K system prompt")
    _ax.legend()
    _ax.grid(alpha=0.3)
    _fig.tight_layout()
    _fig
    return broken, good, nocache


@app.cell(hide_code=True)
def _(broken, good, mo, nocache, total):
    _d = total(broken) - total(good)
    _vs = (
        rf"比**完全不用快取**（\${total(nocache):.3f}）還貴 "
        rf"{total(broken) / total(nocache) - 1:.0%}"
        if total(broken) > total(nocache)
        else rf"仍比完全不用快取（\${total(nocache):.3f}）便宜"
    )
    mo.md(
        rf"""
    乖乖聊到底 **\${total(good):.3f}** → 這個情況 **\${total(broken):.3f}**（多付 \${_d:.3f}），{_vs}。

    把選單切到「**每輪都換模型比較答案**」看一次：橘線會爬到紅線**上面**去。
    原因很單純——每輪都失效的話，你每一輪都在付比一般輸入還貴 25% 的寫入價，
    卻一次命中都沒吃到。這就是「換來換去比不用快取還貴」的算式版本。

    相對地，「只發生一次」的代價是**一次性**的：多付那一筆之後，
    曲線的斜率就跟綠線平行了。閒置過期沒那麼可怕，反覆改前綴才可怕。
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 6️⃣ 你的實驗區

    下面四根拉桿就是你的實驗區。建議挑戰（由易到難）：

    1. **LEVEL 1**：把「寫入 TTL」換成 **1 小時（\$20/MTok）**，
       看三輪總價變多少、還省不省。長 TTL 是免費的嗎？
    2. **LEVEL 2**：把「系統提示長度」從 10K 拉到 2K，再拉到 40K，
       每次都用 3 輪與 20 輪各看一遍。「省的比例」對哪個參數比較敏感——
       系統提示長度，還是輪數？
    3. **LEVEL 3**：估一次你自己的用量——你平常一個工作階段大概聊幾輪、
       系統提示（含工具說明）多長？把拉桿設成你的數字，再把「中途換模型」
       拉到 2 次，看那筆差額有多大，並且說得出它是怎麼來的。

    做完記得：**點左側教學頁的「下載 .py」把這份 notebook 帶走**，
    在自己電腦用 `uvx marimo edit lesson.py` 打開，每一格程式碼都能改。
    """
    )
    return


@app.cell
def _(WRITE_1H, WRITE_5M, mo):
    my_sys = mo.ui.slider(
        1_000, 50_000, 1_000, value=10_000, label="系統提示長度（token）", show_value=True
    )
    my_rounds = mo.ui.slider(1, 20, 1, value=3, label="聊幾輪", show_value=True)
    my_write = mo.ui.dropdown(
        options={"5 分鐘（$12.50/MTok）": WRITE_5M, "1 小時（$20.00/MTok）": WRITE_1H},
        value="5 分鐘（$12.50/MTok）",
        label="寫入 TTL",
    )
    my_breaks = mo.ui.slider(0, 3, 1, value=0, label="中途換幾次模型", show_value=True)
    mo.vstack(
        [
            mo.md("**你的實驗區**——每輪問題 1,000 token、回答 2,000 token，其餘由你決定。"),
            mo.hstack([my_sys, my_rounds], justify="start", gap=2, wrap=True),
            mo.hstack([my_write, my_breaks], justify="start", gap=2, wrap=True),
        ]
    )
    return my_breaks, my_rounds, my_sys, my_write


@app.cell
def _(mo, my_breaks, my_rounds, my_sys, my_write, run_chat, total):
    _n, _b = my_rounds.value, my_breaks.value
    # 換模型的輪次：在對話中平均分佈（第 1 輪換沒有意義，本來就要整段寫入）
    _at = sorted({_r for _i in range(_b) if (_r := round(_n * (_i + 1) / (_b + 1))) >= 2})
    _kw = dict(sys_tok=my_sys.value, q_tok=1_000, a_tok=2_000)
    _cached = total(run_chat(_n, write_rate=my_write.value, **_kw))
    _plain = total(run_chat(_n, cached=False, **_kw))
    _broken = total(
        run_chat(_n, write_rate=my_write.value, breaks={_r: 0 for _r in _at}, **_kw)
    )

    _extra = (
        f"\n\n在第 {'、'.join(str(_r) for _r in _at)} 輪換模型：總計 **\\${_broken:.4f}**，"
        f"比乖乖聊完多付 **\\${_broken - _cached:.4f}**"
        if _at
        else "\n\n（把「中途換模型」拉大，看看前綴作廢要付多少。）"
    )
    mo.md(
        f"""
    系統提示 {my_sys.value:,} token、聊 {_n} 輪、寫入 TTL {my_write.selected_key}：

    | | {_n} 輪總計 |
    | --- | --- |
    | 用快取 | **\\${_cached:.4f}** |
    | 完全不用快取 | \\${_plain:.4f} |
    | 省下 | **{1 - _cached / _plain:.1%}** |
    {_extra}
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.accordion(
        {
            "💡 LEVEL 1 參考解答": mo.md(
                r"""
    把「寫入 TTL」換成 1 小時：三輪總計從 **\$0.4915 變成 \$0.5890**，
    省的比例從 32% 掉到 **18%**。

    長 TTL 不是免費的：寫入單價變成一般輸入的 2 倍，等於預付一筆「保留費」。
    什麼時候划算？當你**離開超過 5 分鐘還會回來**——不然下一輪就是整段重寫，
    那筆重寫比多付的保留費貴得多。把「聊幾輪」拉到 10 再比一次：
    省的比例是 **57% 對 53%**，差距縮小很多——因為寫入只付一次，命中的次數卻變多了。
    """
            ),
            "💡 LEVEL 2 參考解答": mo.md(
                r"""
    六種組合各拉一次（系統提示 2K／10K／40K × 聊 3 輪／20 輪），
    「省下」那一列會是這樣：

    | 系統提示 | 聊 3 輪 | 聊 20 輪 |
    |---|---:|---:|
    | 2K | 22% | 65% |
    | 10K | 32% | 68% |
    | 40K | 43% | 74% |

    **輪數的影響遠大於系統提示長度。**系統提示只是一段固定的前綴，
    對話歷史卻是每輪都在長大的那一段——聊得越久，被重複計價的東西越多，
    快取吃掉的比例就越高。所以最有效的省錢動作不是把系統提示壓短，
    是**別動不動就開一個新對話**。
    """
            ),
            "💡 LEVEL 3 提示": mo.md(
                r"""
    做法：把「中途換模型」從 0 拉到 1、再拉到 2，看多付了多少。
    （換模型的輪次會平均分佈在對話中間。）

    **怎麼驗證自己做對了**：差額應該等於
    「換模型當下的歷史長度 ×（寫入價 − 命中價）」。

    拿系統提示 10K、聊 12 輪來驗算：換 1 次會落在第 6 輪，多付 **\$0.2875**。
    而第 6 輪開始前的歷史正好是 25K（11K ＋ 4 輪 ×3K），
    `25_000 / 1e6 * (12.5 - 1) = 0.2875`——對上了。
    換 2 次（第 4、8 輪）就是 **\$0.5750**，剛好兩倍。

    每換一次模型，就多付一筆「當下歷史 × \$11.5/MTok」，
    而歷史只會越來越長，所以**越晚換越貴**。

    做完之後值得想一件事：這筆錢跟「選錯模型」比起來是大是小？
    快取省的是零頭，**選對模型省的是大頭**——但零頭是你不用動腦就能省下的。
    """
            ),
        }
    )
    return


if __name__ == "__main__":
    app.run()
