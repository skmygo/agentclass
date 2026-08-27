import marimo

__generated_with = "0.23.16"
app = marimo.App(width="medium", app_title="Prompt Caching：連續對話的錢怎麼算（實驗場）")


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    # 🧪 Prompt Caching：連續對話的錢怎麼算（實驗場）

    這是本課的**實驗場**。左側教學讀到哪，就回到這裡動手做——
    每一格程式碼都可以**直接修改、立即重跑**（點格子右上的 ▶，或按 `Ctrl+Enter`）。
    改壞了也沒關係：重新整理頁面就會回到原版。

    這裡沒有任何網路呼叫：**帳單是照公開費率一筆一筆真算出來的**，
    所以你可以把費率改成自己方案的數字，整份 notebook 立刻跟著變。
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

    連續對話會用到的價目只有五種。下面這格是本課**唯一的費率來源**——
    想換成自己方案的數字，改這一格就好，後面所有金額與圖表都會跟著重算。

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
    _fig, _axes = plt.subplots(1, 2, figsize=(9.6, 4.0))
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

    上面看的是總額，這裡把它拆開。左圖是每輪的 **input token 數量**，
    右圖是每輪的**花費**——同一段對話，兩張圖的形狀完全不一樣：

    左邊的綠色（已快取的歷史）越疊越高，右邊卻幾乎貼在地上。
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
    _fig, _axes = plt.subplots(1, 2, figsize=(9.6, 4.0))
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

    下面這格是你的，改完按 ▶ 重跑。建議挑戰（由易到難）：

    1. **LEVEL 1**：把 `my_write` 改成 `WRITE_1H`（1 小時 TTL，\$20/MTok），
       看三輪總價變多少、還省不省。長 TTL 是免費的嗎？
    2. **LEVEL 2**：把 `my_sys` 從 10K 改成 2K，再改成 40K，各跑 3 輪與 20 輪。
       「省的比例」對哪個參數比較敏感——系統提示長度，還是輪數？
    3. **LEVEL 3**：估一次你自己的用量——你平常一個工作階段大概聊幾輪、
       系統提示（含工具說明）多長？用 `breaks=` 算出「乖乖聊完」與
       「中間換兩次模型」的差額，並且說得出那筆差額是怎麼來的。

    做完記得：**點左側教學頁的「下載 .py」把你的版本帶走**，
    在自己電腦用 `uvx marimo edit lesson.py` 就能繼續玩。
    """
    )
    return


@app.cell
def _(WRITE_1H, WRITE_5M, run_chat, total):
    # ===== 你的實驗區 =====
    my_sys = 10_000       # 系統提示長度
    my_rounds = 3         # 聊幾輪
    my_write = WRITE_5M   # 想試 1 小時 TTL 就改成 WRITE_1H

    my_cached = run_chat(my_rounds, my_sys, 1_000, 2_000, write_rate=my_write)
    my_plain = run_chat(my_rounds, my_sys, 1_000, 2_000, cached=False)
    for _r in my_cached:
        print(f"第 {_r['round']} 輪：命中 {_r['hit']:>6} / 寫入 {_r['write']:>6} → ${_r['cost']:.4f}")
    print(f"\n{my_rounds} 輪總計：用快取 ${total(my_cached):.4f}、"
          f"不用快取 ${total(my_plain):.4f} → 省 {1 - total(my_cached) / total(my_plain):.1%}")
    print(f"（目前寫入價 ${my_write:.2f}/MTok；1 小時 TTL 是 ${WRITE_1H:.2f}/MTok）")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.accordion(
        {
            "💡 LEVEL 1 參考解答": mo.md(
                r"""
    ```python
    my_write = WRITE_1H   # 20.0
    ```

    三輪總計從 **\$0.4915 變成 \$0.5890**，省的比例從 32% 掉到 **18%**。

    長 TTL 不是免費的：寫入單價變成一般輸入的 2 倍，等於預付一筆「保留費」。
    什麼時候划算？當你**離開超過 5 分鐘還會回來**——不然下一輪就是整段重寫，
    那筆重寫比多付的保留費貴得多。把 `my_rounds` 拉到 10 再比一次，差距會縮小很多，
    因為命中的次數變多了。
    """
            ),
            "💡 LEVEL 2 參考解答": mo.md(
                r"""
    ```python
    for my_sys in (2_000, 10_000, 40_000):
        for my_rounds in (3, 20):
            c = total(run_chat(my_rounds, my_sys, 1_000, 2_000))
            p = total(run_chat(my_rounds, my_sys, 1_000, 2_000, cached=False))
            print(f"sys={my_sys // 1000}K n={my_rounds}: 省 {1 - c / p:.0%}")
    ```

    跑出來會是這樣：

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
    做法：先用 `run_chat(n, sys, 1_000, 2_000)` 算「乖乖聊完」，
    再用 `breaks={a: 0, b: 0}` 算「在第 a、b 輪換模型」，兩者相減。

    **怎麼驗證自己做對了**：差額應該等於
    「換模型當下的歷史長度 ×（寫入價 − 命中價）」。

    以第 5️⃣ 節的 12 輪情境驗算：在第 4 輪換一次模型多付 \$0.218，
    而第 4 輪開始前的歷史正好是 19K，
    `19_000 / 1e6 * (12.5 - 1) = 0.2185`——對上了。
    每多換一次模型，就多付一筆「當下歷史 × \$11.5/MTok」，
    而歷史只會越來越長，所以越晚換越貴。

    做完之後值得想一件事：這筆錢跟「選錯模型」比起來是大是小？
    快取省的是零頭，**選對模型省的是大頭**——但零頭是你不用動腦就能省下的。
    """
            ),
        }
    )
    return


if __name__ == "__main__":
    app.run()
