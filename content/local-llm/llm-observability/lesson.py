import marimo

__generated_with = "0.23.16"
app = marimo.App(width="medium", app_title="可觀測性與監控：看見你的 LLM（實驗場）")


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    # 🧪 可觀測性與監控：看見你的 LLM（實驗場）

    這是本課的**實驗場**。左側教學讀到哪，就回到這裡動手做——
    每個實驗都有**滑桿與選項**可以拉，拉完右邊立刻重算——
    所有數字都是當場算出來的，不是預錄的畫面。

    本課分兩半：**1️⃣2️⃣ 請求層**（一條 trace 裡發生了什麼、錢花在誰身上）、
    **3️⃣4️⃣5️⃣ 機器層**（告警什麼時候該叫、VRAM 該怎麼判讀）。
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
    ## 1️⃣ 一條 trace 攤開：到底慢在哪一步

    一次「請求」在 agent 時代不是一件事，是一棵樹：規劃 → 檢索 → 呼叫工具 → 生成。
    trace 就是把這棵樹連同每一步的起訖時間記下來。

    判讀 trace 的第一個技巧是分清楚**兩種時間**：

    - **總時長（duration）**：這個 span 從開始到結束的牆鐘時間，**包含所有子步驟**
    - **自身時間（self time）**：總時長扣掉直接子步驟的時間，才是「這一層自己花掉的」

    只看總時長，最上層的 `rag_answer` 永遠是最慢的那個（它包住全部），這句話沒有資訊量。
    **self time 最大的那一步，才是真正的兇手。**（下面每條 trace 的時間軸是教學合成的，
    但 self time 的算法跟你在 MLflow／Langfuse UI 上看到的完全一樣。）

    換一條 trace 看看，注意最慢的那一步怎麼跳動：
    """
    )
    return


@app.cell
def _(mo):
    trace_pick = mo.ui.dropdown(
        options={
            "① 順利的一次 RAG 問答": "ok",
            "② 一樣的問題，突然變慢了": "slow_retrieve",
            "③ 又慢了一次，但慢的地方不一樣": "slow_generate",
            "④ agent 卡在重試迴圈裡": "retry_loop",
        },
        value="① 順利的一次 RAG 問答",
        label="選一條 trace",
    )
    trace_pick
    return (trace_pick,)


@app.cell
def _():
    # 一條 trace ＝ 前序排列的 span 清單：(深度, 名稱, 類型, 起 ms, 迄 ms, 這一步成功嗎)
    TRACES = {
        "ok": [
            (0, "rag_answer", "CHAIN", 0, 1850, True),
            (1, "retrieve", "RETRIEVER", 20, 380, True),
            (2, "embeddings", "LLM", 30, 360, True),
            (1, "generate", "LLM", 400, 1840, True),
        ],
        "slow_retrieve": [
            (0, "rag_answer", "CHAIN", 0, 3210, True),
            (1, "retrieve", "RETRIEVER", 20, 1880, True),
            (2, "embeddings", "LLM", 30, 300, True),
            (2, "vector_search", "TOOL", 310, 1870, True),
            (1, "generate", "LLM", 1900, 3200, True),
        ],
        "slow_generate": [
            (0, "rag_answer", "CHAIN", 0, 9240, True),
            (1, "retrieve", "RETRIEVER", 20, 390, True),
            (2, "embeddings", "LLM", 30, 370, True),
            (1, "generate", "LLM", 410, 9230, True),
            (2, "queue_wait", "TOOL", 420, 7620, True),
            (2, "decode", "LLM", 7630, 9220, True),
        ],
        "retry_loop": [
            (0, "agent_run", "CHAIN", 0, 8600, True),
            (1, "llm_plan #1", "LLM", 0, 1180, False),
            (1, "list_allowed_directraries", "TOOL", 1190, 1260, False),
            (1, "llm_plan #2", "LLM", 1270, 2560, False),
            (1, "list_allowed_directraries", "TOOL", 2570, 2640, False),
            (1, "llm_plan #3", "LLM", 2650, 4090, True),
            (1, "list_allowed_directories", "TOOL", 4100, 4230, True),
            (1, "llm_plan #4", "LLM", 4240, 5860, True),
            (1, "read_file", "TOOL", 5870, 6020, True),
            (1, "llm_plan #5", "LLM", 6030, 8580, True),
        ],
    }

    def self_times(spans):
        """self time = 總時長 − 直接子步驟的時長總和（spans 需為前序排列）。

        數學上有個好用的自我檢查：所有 span 的 self time 加起來 == 根 span 的總時長。
        """
        out = []
        for i, s in enumerate(spans):
            child = 0
            for j in range(i + 1, len(spans)):
                if spans[j][0] <= s[0]:
                    break
                if spans[j][0] == s[0] + 1:
                    child += spans[j][4] - spans[j][3]
            out.append((s[4] - s[3]) - child)
        return out

    return TRACES, self_times


@app.cell
def _(TRACES, plt, self_times, trace_pick):
    _spans = TRACES[trace_pick.value]
    _self = self_times(_spans)
    _kind_color = {
        "CHAIN": "#8C8C8C",
        "RETRIEVER": "#4C72B0",
        "LLM": "#DD8452",
        "TOOL": "#55A868",
    }
    _slowest = max(range(len(_spans)), key=lambda i: _self[i])

    _fig, _ax = plt.subplots(figsize=(7.4, 0.52 * len(_spans) + 1.4))
    for _i, (_d, _name, _kind, _s0, _s1, _ok) in enumerate(_spans):
        _y = len(_spans) - 1 - _i
        _ax.barh(
            _y,
            _s1 - _s0,
            left=_s0,
            height=0.6,
            color="#C44E52" if not _ok else _kind_color[_kind],
            edgecolor="#2B2B2B",
            linewidth=1.0,
            hatch="//" if not _ok else None,
        )
        _ax.text(
            _s1 + 90,
            _y,
            f"{_self[_i]} ms self" + ("  <-- slowest" if _i == _slowest else ""),
            va="center",
            fontsize=9,
            fontweight="bold" if _i == _slowest else "normal",
            color="#C44E52" if _i == _slowest else "#444444",
        )

    # 等寬字型 + 右側補空白：ytick 標籤預設靠右對齊，補齊等長後縮排才看得出樹狀層級
    _labels = ["  " * _s[0] + _s[1] for _s in _spans]
    _w = max(len(x) for x in _labels)
    _ax.set_yticks(range(len(_spans)))
    _ax.set_yticklabels(
        [x.ljust(_w) for x in _labels][::-1], fontsize=9.5, family="monospace"
    )
    _ax.set_xlabel("time since request start (ms)")
    _ax.set_xlim(0, _spans[0][4] * 1.42)
    _ax.set_title(f"trace waterfall - total {_spans[0][4]} ms", fontsize=11)
    _ax.grid(axis="x", alpha=0.3)
    _fig.tight_layout()

    slow_name = _spans[_slowest][1]
    slow_self = _self[_slowest]
    trace_total = _spans[0][4]
    wasted_ms = sum(s[4] - s[3] for s in _spans if not s[5])
    self_sum = sum(_self)
    _fig
    return self_sum, slow_name, slow_self, trace_total, wasted_ms


@app.cell(hide_code=True)
def _(mo, self_sum, slow_name, slow_self, trace_total, wasted_ms):
    _lines = [
        (
            f"**總時長 {trace_total} ms**，self time 最大的一步是 "
            f"`{slow_name}`（{slow_self} ms，佔 {slow_self / trace_total:.0%}）。"
        ),
        (
            f"自我檢查：所有 span 的 self time 加起來 = **{self_sum} ms**，"
            f"剛好等於根 span 的總時長 {trace_total} ms ✓"
        ),
    ]
    if wasted_ms:
        _lines.append(
            f"⚠️ 這條 trace 有失敗的步驟（紅色斜線）：**{wasted_ms} ms、"
            f"佔全程 {wasted_ms / trace_total:.0%} 的時間與 token 完全白燒**——"
            "工具名被模型拼錯了，前兩輪規劃全部作廢。狀態碼還是 200，日誌不會告訴你這件事。"
        )
    if slow_name == "queue_wait":
        _lines.append(
            "🔑 注意這一步：trace 只告訴你「**等了 7.2 秒**」，卻不會告訴你**為什麼要等**。"
            "答案在另一層——機器層的儀表板上（vLLM 的排隊數與 KV cache 使用率）。"
            "這就是兩層監控缺一不可的地方，往下走 3️⃣。"
        )
    mo.md("\n\n".join(_lines))
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 2️⃣ 錢花在誰身上：把成本歸戶

    trace 除了時間，還記了每次呼叫的 token 用量。有了 token 就能算錢，
    有了 user / model / 功能路由這些標籤，就能回答**「正在流血的是哪一條」**。

    下面這批 trace 紀錄是教學合成的（600 筆請求），
    但**計價公式與歸戶的 group-by 就是你在真的可觀測性平台裡做的事**。
    換個分組維度看看，猜猜看哪一組最貴：
    """
    )
    return


@app.cell
def _(np):
    # 每百萬 token 的單價（USD）——換成你自己的價目表
    PRICE = {
        "local-8b": (0.04, 0.04),
        "cloud-small": (0.15, 0.60),
        "cloud-large": (3.00, 15.00),
    }

    def make_requests(n=600, seed=11):
        rng = np.random.default_rng(seed)
        # 三條功能路由：聊天（量大、帶對話歷史）、RAG 查詢（自架小模型）、夜間批次摘要（少量、超長 prompt）
        route = rng.choice(
            ["chat", "rag-search", "nightly-summary"], size=n, p=[0.62, 0.35, 0.03]
        )
        model = np.where(
            route == "chat",
            "cloud-small",
            np.where(route == "rag-search", "local-8b", "cloud-large"),
        )
        base_in = {"chat": 3000, "rag-search": 2500, "nightly-summary": 20000}
        base_out = {"chat": 300, "rag-search": 400, "nightly-summary": 1200}
        tok_in = np.array(
            [max(50, rng.normal(base_in[r], base_in[r] * 0.25)) for r in route]
        )
        tok_out = np.array(
            [max(10, rng.normal(base_out[r], base_out[r] * 0.3)) for r in route]
        )
        # 夜間批次跑在服務帳號底下，其餘分給四位使用者
        user = np.where(
            route == "nightly-summary",
            "svc:batch-job",
            rng.choice(["amy", "bob", "carol", "dave"], size=n),
        )
        cost = np.array(
            [
                tok_in[i] / 1e6 * PRICE[model[i]][0] + tok_out[i] / 1e6 * PRICE[model[i]][1]
                for i in range(n)
            ]
        )
        return {
            "route": route,
            "model": model,
            "user": user,
            "tok_in": tok_in,
            "tok_out": tok_out,
            "cost": cost,
        }

    reqs = make_requests()
    return PRICE, make_requests, reqs


@app.cell
def _(mo):
    group_by = mo.ui.dropdown(
        options={"依功能路由": "route", "依模型": "model", "依使用者": "user"},
        value="依功能路由",
        label="成本歸戶到",
    )
    group_by
    return (group_by,)


@app.cell
def _(group_by, np, plt, reqs):
    _key = np.array(reqs[group_by.value])
    _names = sorted(set(_key.tolist()))
    _cost = np.array([reqs["cost"][_key == n].sum() for _names_i, n in enumerate(_names)])
    _cnt = np.array([int((_key == n).sum()) for n in _names])
    _order = np.argsort(-_cost)
    _names = [_names[i] for i in _order]
    _cost, _cnt = _cost[_order], _cnt[_order]

    _fig, (_a1, _a2) = plt.subplots(2, 1, figsize=(6.4, 1.1 * len(_names) + 3.4))
    _y = np.arange(len(_names))[::-1]
    _a1.barh(_y, _cost, color="#C44E52", edgecolor="#2B2B2B", height=0.6)
    for _i, _c in enumerate(_cost):
        _a1.text(_c, _y[_i], f"  ${_c:.2f}", va="center", fontsize=9.5, fontweight="bold")
    _a1.set_yticks(_y)
    _a1.set_yticklabels(_names, fontsize=10)
    _a1.set_xlim(0, _cost.max() * 1.42)
    _a1.set_title("cost (USD)", fontsize=11)
    _a1.grid(axis="x", alpha=0.3)

    _a2.barh(_y, _cnt, color="#4C72B0", edgecolor="#2B2B2B", height=0.6)
    for _i, _n in enumerate(_cnt):
        _a2.text(_n, _y[_i], f"  {_n}", va="center", fontsize=9.5)
    _a2.set_yticks(_y)
    _a2.set_yticklabels(_names, fontsize=10)
    _a2.set_xlim(0, _cnt.max() * 1.35)
    _a2.set_title("requests", fontsize=11)
    _a2.grid(axis="x", alpha=0.3)
    _fig.tight_layout()

    top_name = _names[0]
    top_share = float(_cost[0] / _cost.sum())
    top_reqshare = float(_cnt[0] / _cnt.sum())
    total_cost = float(_cost.sum())
    _fig
    return top_name, top_reqshare, top_share, total_cost


@app.cell(hide_code=True)
def _(mo, top_name, top_reqshare, top_share, total_cost):
    mo.md(
        f"""
    這 600 筆請求總共花掉 **${total_cost:.2f}**。最貴的一組是 **`{top_name}`**：
    只佔 **{top_reqshare:.0%} 的請求數**，卻吃掉 **{top_share:.0%} 的錢**。

    「請求數少、花費大」是成本失控最典型的樣子——長 prompt、貴模型、或一個沒人看見的重試迴圈。
    平均延遲、錯誤率這些指標都看不出它；**只有把 token 歸戶到路由／模型／使用者才會現形**。
    切換上面的分組維度，你會看到同一筆錢從三個角度指向同一個嫌犯。
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 3️⃣ 機器層：告警什麼時候該叫

    請求層看完，換另一半。機器層的問題長這樣：**GPU 的剩餘 VRAM 掉到多低、持續多久，才值得半夜叫醒你？**

    告警規則只有兩個旋鈕：

    - **門檻**：低於多少算異常（`< 1.5GB`）
    - **`for:`**：這個條件要**持續多久**才算數（`for: 5m`）

    `for:` 是告警品質的關鍵。沒有它，VRAM 抖一下就叫；叫了幾次沒事之後，
    大家就會開始忽略告警——這叫告警疲乏（alert fatigue），是監控自殺的第一步。

    下面是一段合成的 24 小時剩餘 VRAM 時序（15 秒一個點，跟 Prometheus 的抓取頻率一樣）：
    裡面藏了 **3 次無害的短暫抖動**（1／2／4 分鐘）和 **1 次真事件**（連續 12 分鐘的低水位）。
    轉兩個旋鈕，看誤報怎麼消失、代價是什麼：
    """
    )
    return


@app.cell
def _(np):
    STEP_S = 15  # Prometheus 每 15 秒 pull 一輪

    def make_vram_series(jitter_mins=(1, 2, 4), event_min=12, seed=7):
        """合成一段 24h 的剩餘 VRAM 時序（GB）。回傳 (序列, 真事件起, 真事件迄)。"""
        rng = np.random.default_rng(seed)
        n = 24 * 60 * 60 // STEP_S
        v = 4.0 + rng.normal(0, 0.15, n)
        for start, mins in zip((900, 1800, 4200), jitter_mins):
            v[start : start + int(mins * 60 / STEP_S)] = 1.15
        ev0 = 3000
        ev1 = ev0 + int(event_min * 60 / STEP_S)
        v[ev0:ev1] = 1.05
        return v, ev0, ev1

    def firing_points(below, need):
        """回傳每一段「連續低於門檻」達 need 個取樣點時的觸發索引（向量化）。"""
        idx = np.flatnonzero(below)
        if idx.size == 0:
            return np.array([], dtype=int)
        brk = np.flatnonzero(np.diff(idx) > 1)
        starts = np.concatenate(([idx[0]], idx[brk + 1]))
        ends = np.concatenate((idx[brk], [idx[-1]]))
        keep = (ends - starts + 1) >= need
        return starts[keep] + need - 1

    def evaluate_rule(v, ev0, ev1, threshold, for_min):
        """把一組（門檻, for:）套上去，算出誤報數／有沒有抓到真事件／偵測延遲。"""
        need = max(1, round(for_min * 60 / STEP_S))
        fires = firing_points(v < threshold, need)
        in_event = (fires >= ev0) & (fires < ev1)
        return {
            "fires": fires,
            "n_fires": int(fires.size),
            "false_alarms": int((~in_event).sum()),
            "detected": bool(in_event.any()),
            "delay_min": (
                float((fires[in_event][0] - ev0) * STEP_S / 60) if in_event.any() else None
            ),
        }

    vram, EV0, EV1 = make_vram_series()
    return EV0, EV1, STEP_S, evaluate_rule, make_vram_series, vram


@app.cell
def _(mo):
    th_slider = mo.ui.slider(
        start=0.5, stop=4.2, step=0.1, value=1.5, label="告警門檻（剩餘 VRAM < ? GB）", show_value=True
    )
    for_slider = mo.ui.slider(
        start=0.0, stop=15.0, step=0.25, value=5.0, label="for:（持續幾分鐘才算數）", show_value=True
    )
    mo.vstack([th_slider, for_slider])
    return for_slider, th_slider


@app.cell
def _(EV0, EV1, STEP_S, evaluate_rule, for_slider, np, plt, th_slider, vram):
    _res = evaluate_rule(vram, EV0, EV1, th_slider.value, for_slider.value)
    _t = np.arange(vram.size) * STEP_S / 3600.0

    _fig, _ax = plt.subplots(figsize=(7.6, 3.6))
    _ax.axvspan(
        EV0 * STEP_S / 3600,
        EV1 * STEP_S / 3600,
        color="#C44E52",
        alpha=0.12,
        label="real incident",
    )
    _ax.plot(_t, vram, color="#4C72B0", linewidth=0.8)
    _ax.axhline(th_slider.value, color="#C44E52", linestyle="--", linewidth=1.6, label="threshold")
    if _res["n_fires"]:
        _ft = _res["fires"] * STEP_S / 3600.0
        _ax.plot(
            _ft,
            np.full(_ft.size, th_slider.value),
            "v",
            color="#C44E52",
            markersize=11,
            markeredgecolor="#2B2B2B",
            label=f"alert fires ({_res['n_fires']})",
        )
    _ax.set_xlabel("hours")
    _ax.set_ylabel("free VRAM (GB)")
    _ax.set_ylim(0.6, 4.8)
    _ax.set_title(
        f"threshold < {th_slider.value:.1f} GB, for: {for_slider.value:g}m", fontsize=11
    )
    _ax.legend(loc="lower right", fontsize=8.5)
    _ax.grid(alpha=0.3)
    _fig.tight_layout()

    rule_res = _res
    _fig
    return (rule_res,)


@app.cell(hide_code=True)
def _(for_slider, mo, rule_res, th_slider):
    _delay = rule_res["delay_min"]
    _verdict = (
        "🎯 **剛剛好**：誤報清光了，真事件也還抓得到。"
        if rule_res["false_alarms"] == 0 and rule_res["detected"]
        else (
            "🔕 **`for:` 太長了**：真事件持續 12 分鐘，你的規則要求得更久——"
            "這條告警永遠不會叫（漏報）。"
            if not rule_res["detected"]
            else f"📣 **還在誤報**：{rule_res['false_alarms']} 次告警是無害的抖動造成的。"
            "把 `for:` 拉長到超過最長抖動的長度（本例 4 分鐘）試試。"
        )
    )
    mo.md(
        f"""
    | | 值 |
    |---|---|
    | 規則 | `free_vram < {th_slider.value:.1f}GB` `for: {for_slider.value:g}m` |
    | 總告警次數 | **{rule_res["n_fires"]}** |
    | 其中誤報（抖動造成） | **{rule_res["false_alarms"]}** |
    | 抓到真事件？ | **{"是" if rule_res["detected"] else "沒有（漏報）"}** |
    | 偵測延遲 | **{f"{_delay:.2f} 分鐘" if _delay is not None else "—"}** |

    {_verdict}

    注意這裡的代價：**`for:` 每拉長一分鐘，你就晚一分鐘知道出事**。
    所以門檻不能設在「已經死了」的水位，要設在「該去看一眼」的水位——**告警要留反應時間**。
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 4️⃣ `for:` 該設多久：把取捨掃出來

    上一格你是用手轉旋鈕試。既然評估規則已經寫成函式，那就把所有 `for:` 值掃一遍，
    讓取捨曲線自己講話（門檻用上面那根拉桿的值）：
    """
    )
    return


@app.cell
def _(EV0, EV1, evaluate_rule, np, plt, th_slider, vram):
    _grid = np.arange(0, 15.01, 0.25)
    _fa, _delay, _miss = [], [], []
    for _f in _grid:
        _r = evaluate_rule(vram, EV0, EV1, th_slider.value, _f)
        _fa.append(_r["false_alarms"])
        _delay.append(_r["delay_min"] if _r["detected"] else np.nan)
        _miss.append(not _r["detected"])

    _fa = np.array(_fa)
    _delay = np.array(_delay, dtype=float)
    _miss = np.array(_miss)

    _fig, _ax = plt.subplots(figsize=(7.6, 3.6))
    _ax.step(_grid, _fa, where="post", color="#C44E52", linewidth=2, label="false alarms")
    _ax.set_xlabel("for:  (minutes)")
    _ax.set_ylabel("false alarms", color="#C44E52")
    _ax.set_ylim(-0.3, max(3.4, _fa.max() + 0.4))
    _ax.grid(alpha=0.3)

    _ax2 = _ax.twinx()
    _ax2.plot(_grid, _delay, color="#4C72B0", linewidth=2, label="detection delay")
    _ax2.set_ylabel("detection delay (min)", color="#4C72B0")

    if _miss.any():
        _ax.axvspan(_grid[_miss][0], _grid[-1], color="#8C8C8C", alpha=0.18)
        _ax.text(
            _grid[_miss][0] + 0.2,
            max(3.4, _fa.max() + 0.4) * 0.72,
            "missed\n(for: longer than\nthe incident)",
            fontsize=9,
            color="#444444",
        )

    _clean = _grid[_fa == 0]
    sweet_for = float(_clean[0]) if _clean.size else None
    if sweet_for is not None and not _miss[_grid == sweet_for][0]:
        _ax.axvline(sweet_for, color="#55A868", linestyle=":", linewidth=2)
        _ax.text(sweet_for + 0.15, 0.15, f"first quiet: {sweet_for:g}m", fontsize=9, color="#55A868")
    _ax.set_title(f"trade-off at threshold < {th_slider.value:.1f} GB", fontsize=11)
    _fig.tight_layout()
    _fig
    return (sweet_for,)


@app.cell(hide_code=True)
def _(mo, sweet_for, th_slider):
    mo.md(
        f"""
    紅線（誤報）往下掉是階梯狀的——**每一階都是某一次抖動的長度**。
    藍線（偵測延遲）則是直線上升：`for:` 設多久，你就晚多久知道。

    在門檻 `< {th_slider.value:.1f}GB` 之下，第一個誤報歸零的 `for:` 是
    **{f"{sweet_for:g} 分鐘" if sweet_for is not None else "（這個門檻下沒有任何值能讓誤報歸零）"}**——
    比最長的那次抖動（4 分鐘）多一點點。這就是實務上 `for:` 的定法：
    **量一下你系統真實的抖動有多長，取比它稍長的值**，而不是拍腦袋寫 5 分鐘。

    灰色區是漏報區：`for:` 超過事件本身的長度，這條規則就等於不存在。
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 5️⃣ 看「剩多少」，不是看「用多少」

    最後一個機器層的判讀技巧，來自一次真實的容量事故（RTX 4090 24GB、2026-07）：
    某天 A 機的 VRAM **只剩 862 MiB**，最重要的語音合成服務隨時可能 CUDA OOM；
    而 B 機「看起來也快滿了」，卻其實非常安全。差別在於服務要 VRAM 的**方式**不同：

    | 類型 | 代表 | 行為 | 風險 |
    |---|---|---|---|
    | **預留制** | vLLM | 啟動時鎖一塊，之後不再長 | 跑起來就穩 |
    | **動態制** | PyTorch 類服務（TTS、影像） | 用多少要多少，長文本突然要更多 | 餘裕不夠 → 隨時 OOM |

    **判讀規則：卡上有動態制服務時，看「剩多少」而不是「用多少」。**
    下面拉一下「動態制服務的峰值還可能再吃掉多少」，再打開那個開關看看當天的解法：
    """
    )
    return


@app.cell
def _(mo):
    peak_slider = mo.ui.slider(
        start=0.5, stop=3.0, step=0.1, value=1.5,
        label="動態制服務的峰值增量（GB）", show_value=True,
    )
    move_switch = mo.ui.switch(value=False, label="把向量嵌入服務搬到 B 機")
    mo.vstack([peak_slider, move_switch])
    return move_switch, peak_slider


@app.cell
def _(move_switch, np, peak_slider, plt):
    TOTAL_GB = 24.0
    _emb = 3.24
    # A 機：有動態制服務（語音合成）；B 機：全預留制
    _a = [("TTS (dynamic)", 9.4), ("OCR vLLM (reserved)", 8.2), ("system/other", 2.3)]
    _b = [("LLM vLLM (reserved)", 11.5), ("ASR vLLM (reserved)", 5.2), ("system/other", 1.1)]
    if move_switch.value:
        _b.insert(2, ("Embeddings (reserved)", _emb))
    else:
        _a.insert(2, ("Embeddings (reserved)", _emb))

    _colors = {
        "TTS (dynamic)": "#DD8452",
        "OCR vLLM (reserved)": "#4C72B0",
        "LLM vLLM (reserved)": "#4C72B0",
        "ASR vLLM (reserved)": "#6E93C4",
        "Embeddings (reserved)": "#55A868",
        "system/other": "#B0B0B0",
    }
    free_a = TOTAL_GB - sum(v for _, v in _a)
    free_b = TOTAL_GB - sum(v for _, v in _b)

    _fig, _ax = plt.subplots(figsize=(7.6, 3.2))
    for _row, (_segs, _free) in enumerate([(_a, free_a), (_b, free_b)]):
        _x = 0.0
        for _name, _v in _segs:
            _ax.barh(_row, _v, left=_x, height=0.5, color=_colors[_name],
                     edgecolor="#2B2B2B", linewidth=1.0)
            if _v > 1.6:
                _ax.text(_x + _v / 2, _row, f"{_v:g}", ha="center", va="center",
                         fontsize=8.5, color="#FFFFFF", fontweight="bold")
            _x += _v
        _ax.barh(_row, _free, left=_x, height=0.5, color="#FFFFFF",
                 edgecolor="#2B2B2B", linewidth=1.0)
        if _row == 0:  # 只有 A 機有動態制服務，峰值還會再長
            _risky = _free < peak_slider.value
            _ax.barh(_row, peak_slider.value, left=_x, height=0.28,
                     color="#C44E52" if _risky else "#55A868", alpha=0.45,
                     hatch="//", edgecolor="#C44E52" if _risky else "#55A868")
            _ax.text(0.3, _row + 0.36,
                     f"free {_free:.2f} GB  " + ("-> peak overflows: OOM risk" if _risky
                                                 else "-> headroom covers the peak"),
                     va="center", fontsize=9, fontweight="bold",
                     color="#C44E52" if _risky else "#55A868")
        else:
            _ax.text(0.3, _row + 0.36, f"free {_free:.2f} GB  -> nothing grows: stable",
                     va="center", fontsize=9, color="#55A868")

    _ax.axvline(TOTAL_GB, color="#2B2B2B", linewidth=2)
    _ax.text(TOTAL_GB + 0.25, 1.62, "24 GB limit", ha="left", fontsize=8.5, color="#2B2B2B")
    _ax.set_yticks([0, 1])
    _ax.set_yticklabels(["Machine A\n(dynamic svc)", "Machine B\n(all reserved)"], fontsize=9)
    _ax.set_ylim(-0.55, 1.85)
    _ax.set_xlim(0, TOTAL_GB + 3.4)
    _ax.set_xlabel("VRAM (GB)")
    _ax.set_title("hatched = what the dynamic service may still grab at peak", fontsize=10)
    _ax.grid(axis="x", alpha=0.25)
    _fig.tight_layout()

    used_a = float(TOTAL_GB - free_a)
    used_b = float(TOTAL_GB - free_b)
    free_a_gb, free_b_gb = float(free_a), float(free_b)
    a_safe = bool(np.float64(free_a) >= peak_slider.value)
    _fig
    return a_safe, free_a_gb, free_b_gb, used_a, used_b


@app.cell(hide_code=True)
def _(a_safe, free_a_gb, free_b_gb, mo, move_switch, peak_slider, used_a, used_b):
    mo.md(
        f"""
    - **A 機**：用掉 {used_a:.2f} GB、**剩 {free_a_gb:.2f} GB**；卡上有動態制服務，峰值還可能再吃
      {peak_slider.value:g} GB → {"✅ **餘裕夠**，撐得住峰值" if a_safe else "🔴 **餘裕不夠，隨時 OOM**"}
    - **B 機**：用掉 {used_b:.2f} GB、剩 {free_b_gb:.2f} GB——用量看起來更兇，
      但**全部是預留制**：啟動時就鎖好了，之後不會再長，✅ 跑起來就穩

    {"當天的解法就是這個開關：把向量嵌入服務搬去 B 機，A 機的餘裕從 0.86 GB 變成 4.10 GB。"
     "由此也長出一條配置鐵律——**新的 GPU 服務一律排到沒有動態制服務的那台**。"
     if move_switch.value else
     "把上面的開關打開，看看當天實際是怎麼救回來的。"}

    監控要做的，就是**把這段人肉分析變成 24 小時自動的**：
    剩餘 VRAM 隨時看得到，低於門檻持續一段時間就推播到手機。
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 6️⃣ 換你動手

    **LEVEL 1**　把 3️⃣ 的 `for:` 拉到 0／2／5／13 分鐘四個位置（門檻固定 1.5 GB），
    記下每一種的告警次數、誤報數與偵測延遲，確認你在圖上看到的行為。

    **LEVEL 2**　你的機器抖動比較長：用下面的實驗區把抖動換成 **2／5／8 分鐘**
    （真事件仍是 12 分鐘），找出「誤報歸零又不漏報」的最小 `for:`。
    想想看這對你的 on-call 意味著什麼。

    **LEVEL 3**　回到 1️⃣ 把四條 trace 逐條看過，找出每一條 self time 最大的那一步，
    並說得出它為什麼慢。自我驗證：**所有 span 的 self time 加總，必須剛好等於根 span 的總時長**。
    （想把自己的慢請求加進來比對，就把 .py 下載回去，`TRACES` 就在裡面。）

    做完記得：**點左側教學頁的「下載 .py」把這份 notebook 帶走**，
    在自己電腦用 `uvx marimo edit lesson.py` 打開，每一格程式碼都能改。
    """
    )
    return


@app.cell
def _(mo):
    my_jitter = mo.ui.dropdown(
        options={
            "1／2／4 分鐘（預設那台）": (1, 2, 4),
            "2／5／8 分鐘": (2, 5, 8),
            "3／7／12 分鐘": (3, 7, 12),
        },
        value="2／5／8 分鐘",
        label="這台機器的抖動有多長",
    )
    my_th = mo.ui.slider(
        0.5, 4.2, 0.1, value=1.5, label="告警門檻（剩餘 VRAM < ? GB）", show_value=True
    )
    my_for = mo.ui.slider(
        0.0, 15.0, 0.25, value=5.0, label="for:（持續幾分鐘才算數）", show_value=True
    )
    mo.vstack(
        [
            mo.md("**你的實驗區**——換一台抖動更長的機器，同一組規則還守得住嗎？"),
            my_jitter,
            mo.hstack([my_th, my_for], justify="start", gap=2, wrap=True),
        ]
    )
    return my_for, my_jitter, my_th


@app.cell
def _(evaluate_rule, make_vram_series, mo, my_for, my_jitter, my_th):
    _v, _e0, _e1 = make_vram_series(jitter_mins=my_jitter.value)
    _r = evaluate_rule(_v, _e0, _e1, my_th.value, my_for.value)
    _delay = f"{_r['delay_min']:.1f} 分鐘" if _r["detected"] else "——沒抓到"
    _verdict = (
        "✅ 誤報 0、真事件也抓到了——這組規則過關。"
        if _r["false_alarms"] == 0 and _r["detected"]
        else "❌ 真事件漏掉了：`for:` 已經比事件本身還長。"
        if not _r["detected"]
        else f"⚠️ 還有 {_r['false_alarms']} 次誤報：半夜會被吵醒 {_r['false_alarms']} 次。"
    )
    mo.md(
        f"""
    抖動 {my_jitter.selected_key}、門檻 {my_th.value:.1f} GB、`for: {my_for.value:g}m`：

    | 告警次數 | 誤報 | 抓到真事件 | 偵測延遲 |
    | --- | --- | --- | --- |
    | {_r["n_fires"]} | **{_r["false_alarms"]}** | {"是" if _r["detected"] else "否"} | {_delay} |

    {_verdict}
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.accordion(
        {
            "💡 LEVEL 1 參考解答": mo.md(
                r"""
    門檻固定 1.5 GB，把 `for:` 拉到四個位置，3️⃣ 的表格會這樣走：

    | `for:` | 總告警 | 誤報 | 抓到真事件 |
    |---|---|---|---|
    | 0m | 4 | 3 | 是（延遲 0） |
    | 2m | 3 | 2 | 是 |
    | 5m | 1 | **0** | 是（延遲 4.75 分鐘） |
    | 13m | 0 | 0 | **沒有（漏報）** |

    `for:2m` 時 2 分鐘與 4 分鐘那兩次抖動還是叫了；`for:13m` 誤報歸零，
    但真事件也一起漏掉——**規則比事件還長，等於沒裝**。
    """
            ),
            "💡 LEVEL 2 參考解答": mo.md(
                r"""
    實驗區選「2／5／8 分鐘」，門檻留在 1.5 GB，把 `for:` 一格一格往右推
    （每格 15 秒），第一個同時滿足「誤報 0」與「抓到真事件」的位置就是答案。

    答案是 **8.25 分鐘**（比最長的那次 8 分鐘抖動多一格）。
    代價就寫在同一列：偵測延遲也跟著變成整整 8 分鐘。

    對 on-call 的意義：**抖動越長，你能保證的「發現速度」就越差**。
    這時候與其一直拉長 `for:`，不如回頭修抖動本身（例如把那個會週期性佔用 VRAM 的批次工作錯開），
    或改用「連續 N 次取樣中有 M 次超標」這類更聰明的條件。
    """
            ),
            "💡 LEVEL 3 提示": mo.md(
                r"""
    1️⃣ 逐條切過去，self time 最長的那一步分別是：

    | trace | 冠軍 | self time |
    |---|---|---|
    | ok | `generate` | 1,440 ms |
    | slow_retrieve | `vector_search` | 1,560 ms |
    | slow_generate | `queue_wait` | **7,200 ms** |

    每一條的 self time 全部加起來，都剛好等於根 span 的總時長
    （1,850／3,210／9,240 ms）——**這個等式是你檢查 trace 有沒有寫壞的免費工具**。
    不相等的常見原因有兩個：子 span 的時間超出父 span 的範圍（起訖抄錯），
    或是層級寫錯（把孫子寫成兒子）。

    找到最慢的一步之後，再問自己第二個問題：**這一步慢，是它自己的問題，還是機器層的問題？**
    像 `queue_wait` 這種，trace 只會告訴你「等了很久」，原因得回機器層的儀表板找。
    """
            ),
        }
    )
    return


if __name__ == "__main__":
    app.run()
