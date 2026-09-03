import marimo

__generated_with = "0.23.16"
app = marimo.App(width="medium", app_title="為什麼需要 MLOps：模型會過期（實驗場）")


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    # 🧪 為什麼需要 MLOps：模型會過期（實驗場）

    這是本課的**實驗場**。教學讀到哪，就回到這裡動手——
    每一段都有**滑桿**可以拉，拉完立刻重跑整個 24 個月的模擬，圖表當場重畫。

    這裡沒有任何網路呼叫，也沒有預錄的畫面：每個月的資料是當場生成的、
    每一次重訓都是真的訓練一顆 logistic regression、每一個準確率都是當場算出來的。
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
    from functools import lru_cache

    import matplotlib.pyplot as plt
    import numpy as np
    from sklearn.linear_model import LogisticRegression
    return LogisticRegression, lru_cache, np, plt


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 1️⃣ 模型上線那天，就開始過期

    這是一間公司的 24 個月。第 0 個月訓練好一顆模型（判斷客戶會不會流失）、上線，
    **然後再也沒有動過它**。每個月有 300 位新客戶進來，模型逐一判斷，月底對答案，
    算出那個月的準確率。

    模型完全沒有變。變的是**世界**——客戶的組成、市場的規則、什麼樣的人會流失，
    都在慢慢移動。下面這條線就是它的下場：
    """
    )
    return


@app.cell
def _(LogisticRegression, lru_cache, np):
    MONTHS = 24     # 模擬 24 個月
    N = 300         # 每個月進來 300 位客戶
    D = 6           # 每位客戶 6 個特徵

    # 語義色：紅＝不重訓、藍＝定期重訓、綠＝監控觸發、橘＝標籤遲到、紫＝資料漂移
    C_NONE, C_PER, C_MON, C_LATE = "#C44E52", "#4C72B0", "#55A868", "#DD8452"
    C_FLAT, C_DATA = "#9A9A9A", "#8172B3"

    @lru_cache(maxsize=64)
    def world(drift=0.12, shift=0.0, seed=0):
        """生一個 24 個月的世界。

        drift：概念漂移——決定「會不會流失」的權重向量每個月旋轉一點點，
               規則本身在變（答案改了），但進來的客戶長相沒變。
        shift：資料漂移——客戶的特徵整體平移，進來的人變了，
               但「什麼樣的人會流失」這條規則沒變。
        """
        rng = np.random.default_rng(seed)
        months = []
        for m in range(MONTHS):
            theta = drift * m
            w = np.array([np.cos(theta), np.sin(theta), 0.5, -0.5, 0.3, 0.0])
            X = rng.normal(0, 1, (N, D)) + shift * m / MONTHS
            y = ((X @ w + 0.3 * rng.normal(0, 1, N)) > 0).astype(int)
            months.append((X, y))
        return months

    def train(month_data):
        return LogisticRegression().fit(*month_data)

    @lru_cache(maxsize=256)
    def run(strategy="none", drift=0.12, k=3, thr=0.85, delay=0, shift=0.0):
        """跑完 24 個月，回傳（每個月的準確率, 重訓發生在哪幾個月）。

        strategy：none＝不重訓／periodic＝每 k 個月重訓／monitor＝準確率低於 thr 才重訓
        delay：標籤晚幾個月才到——第 m 個月只知道第 m-delay 個月的準確率，
               而且要重訓也只有第 m-delay 個月的資料有標籤可以用。
        """
        months = world(drift, shift)
        model = train(months[0])
        accs, retrains = [], []
        for m in range(1, MONTHS):
            X, y = months[m]
            accs.append(model.score(X, y))          # 這個月服役中的模型表現
            if strategy == "periodic" and m % k == 0:
                model = train(months[m])
                retrains.append(m)
            elif strategy == "monitor":
                seen = m - delay                     # 目前看得到的最新月份
                if seen >= 1 and accs[seen - 1] < thr:
                    model = train(months[seen])      # 只有這個月的資料有標籤
                    retrains.append(m)
        return tuple(accs), tuple(retrains)

    @lru_cache(maxsize=8)
    def delay_table(drift=0.12, thr=0.85, span=7):
        """標籤延遲 0…span-1 個月各跑一次，回傳（延遲, 平均準確率, 重訓次數）。"""
        rows = []
        for d in range(span):
            accs, retrains = run("monitor", drift=drift, thr=thr, delay=d)
            rows.append((d, float(np.mean(accs)), len(retrains)))
        return tuple(rows)

    XM = np.arange(1, MONTHS)   # 圖表的 x 軸：上線後第 1…23 個月
    return (
        C_DATA,
        C_FLAT,
        C_LATE,
        C_MON,
        C_NONE,
        C_PER,
        MONTHS,
        XM,
        delay_table,
        run,
        world,
    )


@app.cell
def _(C_NONE, XM, np, plt, run):
    none_accs = np.array(run("none")[0])

    _fig, _ax = plt.subplots(figsize=(6.4, 3.7))
    _ax.plot(XM, none_accs, "o-", color=C_NONE, lw=2.2, ms=4.5, label="never retrained")
    _ax.axhline(0.85, ls="--", lw=1.2, color="#8C8C8C")
    _ax.text(1.0, 0.862, "acceptable level 0.85", fontsize=8.5, color="#6B6B6B")
    _ax.annotate(
        f"month 1: {none_accs[0]:.2f}",
        xy=(1, none_accs[0]), xytext=(2.2, 0.98), fontsize=9,
        arrowprops={"arrowstyle": "->", "color": "#6B6B6B", "lw": 1},
    )
    _ax.annotate(
        f"month 23: {none_accs[-1]:.2f}",
        xy=(23, none_accs[-1]), xytext=(15.5, 0.40), fontsize=9,
        arrowprops={"arrowstyle": "->", "color": "#6B6B6B", "lw": 1},
    )
    _ax.set_xlabel("months after launch")
    _ax.set_ylabel("accuracy of that month")
    _ax.set_title("Same model, changing world")
    _ax.set_ylim(0.33, 1.03)
    _ax.set_xticks([1, 4, 8, 12, 16, 20, 23])
    _ax.grid(alpha=0.3)
    _fig.tight_layout()
    _fig
    return (none_accs,)


@app.cell(hide_code=True)
def _(mo, none_accs):
    _pick = [1, 6, 12, 18, 23]
    _rows = "\n".join(
        f"    | 第 {_m} 個月 | {none_accs[_m - 1]:.2f} |" for _m in _pick
    )
    mo.md(
        rf"""
    | 上線後 | 那個月的準確率 |
    |---|---:|
{_rows}

    第 1 個月 **{none_accs[0]:.2f}**，第 23 個月 **{none_accs[-1]:.2f}**，
    24 個月的平均是 **{none_accs.mean():.3f}**——一個丟銅板的模型是 0.50。

    注意這段期間發生了什麼事：**沒有**。沒有當機、沒有噴錯誤、沒有半夜的告警簡訊。
    它每天都活著、每天照常回答，只是答案越來越常是錯的。
    這是機器學習系統最危險的失敗方式：**它會安靜地爛掉**。
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 2️⃣ 世界怎麼變：兩種漂移

    「世界變了」有兩種完全不同的變法，分清楚它們，你才知道要監控什麼：

    - **資料漂移**：進來的**資料**變了，但「什麼答案才對」的規則沒變。
      像是考卷的題型分佈變了（以前一半代數一半幾何，現在九成幾何），解題方法還是同一套。
    - **概念漂移**：**規則本身**變了。同一張考卷、同一題，標準答案改了。

    下面三個世界跑同一件事——訓練一次、之後不重訓——差別只在世界怎麼變。
    上半張圖是每個月的準確率，下半張圖是**進來的資料本身**（第一個特徵的月平均）：
    """
    )
    return


@app.cell
def _(C_DATA, C_FLAT, C_NONE, MONTHS, XM, np, plt, run, world):
    _worlds = [
        ("world does not change", {"drift": 0.0}, C_FLAT, "-"),
        ("data drift only", {"drift": 0.0, "shift": 1.5}, C_DATA, "-"),
        ("concept drift", {"drift": 0.12}, C_NONE, "-"),
    ]
    drift_stats = {}
    _fig, _axes = plt.subplots(2, 1, figsize=(6.4, 6.4))
    for _name, _kw, _color, _ls in _worlds:
        _accs = np.array(run("none", **_kw)[0])
        _months = world(_kw.get("drift", 0.0), _kw.get("shift", 0.0))
        _f0 = [float(_months[_m][0][:, 0].mean()) for _m in range(MONTHS)]
        _pos = [float(_months[_m][1].mean()) for _m in range(MONTHS)]
        drift_stats[_name] = (_accs.mean(), _accs[-1], _f0[0], _f0[-1], _pos[0], _pos[-1])
        _lw, _alpha = (4.0, 0.45) if _color == C_FLAT else (2.2, 1.0)
        _axes[0].plot(XM, _accs, "-", color=_color, lw=_lw, alpha=_alpha, label=_name)
        _axes[1].plot(
            np.arange(MONTHS), _f0, "-", color=_color, lw=_lw, alpha=_alpha, label=_name
        )
    _axes[0].set_xlabel("months after launch")
    _axes[0].set_ylabel("accuracy")
    _axes[0].set_title("Accuracy: only concept drift hurts")
    _axes[0].set_ylim(0.33, 1.03)
    _axes[0].legend(fontsize=8.5, loc="lower left")
    _axes[0].grid(alpha=0.3)
    _axes[1].set_xlabel("month")
    _axes[1].set_ylabel("mean of feature 1")
    _axes[1].set_title("The incoming data: only data drift is visible here")
    _axes[1].legend(fontsize=8.5, loc="upper left")
    _axes[1].grid(alpha=0.3)
    _fig.tight_layout()
    _fig
    return (drift_stats,)


@app.cell(hide_code=True)
def _(drift_stats, mo):
    _n = drift_stats["world does not change"]
    _d = drift_stats["data drift only"]
    _c = drift_stats["concept drift"]
    mo.md(
        rf"""
    | 世界 | 平均準確率 | 進來的資料有沒有變 |
    |---|---:|---|
    | 完全不變 | {_n[0]:.3f} | 沒有（特徵均值 {_n[2]:+.2f} → {_n[3]:+.2f}） |
    | **只有資料漂移** | **{_d[0]:.3f}** | 變很多（特徵均值 {_d[2]:+.2f} → {_d[3]:+.2f}，流失比例 {_d[4]:.0%} → {_d[5]:.0%}） |
    | **概念漂移** | **{_c[0]:.3f}** | 幾乎沒變（特徵均值 {_c[2]:+.2f} → {_c[3]:+.2f}） |

    兩個很違反直覺、但你一定要記住的結果：

    **一、只有資料漂移時，準確率沒掉**（{_d[0]:.3f}，甚至比世界完全不變的 {_n[0]:.3f} 還高一點）。
    因為規則沒變，模型學到的那條線還是對的，只是進來的人整批移到了它的一側。
    **準確率沒掉，不代表沒事**——這個模型正在服務一群跟訓練時完全不一樣的客戶，
    而它從沒被檢查過在這群人身上準不準。

    **二、概念漂移時，資料看起來一切正常。**下半張圖的紅線幾乎是平的——
    你盯著輸入資料看到天亮也看不出異狀，準確率卻已經腰斬。

    這兩件事合起來，決定了你要監控什麼：

    - 資料漂移**不需要標籤**就看得見（比對輸入分佈，今天就能算）——它是早期警訊。
    - 概念漂移**只有拿到標籤、算出準確率**才會現形——所以你必須有地方**持續記錄每個月的準確率**。

    第二點就是這個系列第 1 課要解決的事。先看沒有它會怎樣：
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 3️⃣ 三種策略：不重訓／定期重訓／監控觸發

    知道模型會過期之後，只剩一個問題：**什麼時候重訓？** 三種做法：

    | 策略 | 做法 | 白話 |
    |---|---|---|
    | **不重訓** | 訓練一次，永遠不動 | 「它上線的時候很準啊」 |
    | **定期重訓** | 每 k 個月重訓一次，不管準不準 | 「每季固定跑一次」 |
    | **監控觸發** | 準確率掉到門檻以下才重訓 | 「掉了再說」 |

    三根滑桿：**世界變得多快**（概念漂移的速度）、**多久重訓一次**、**準確率門檻**。
    拉動任何一根，三條曲線與下面的表格會整組重算。三角形標記＝那個月做了一次重訓。
    """
    )
    return


@app.cell
def _(mo):
    drift_s = mo.ui.slider(
        start=0.0, stop=0.13, step=0.01, value=0.12,
        label="世界變得多快（概念漂移速度）", show_value=True,
    )
    k_s = mo.ui.slider(
        start=1, stop=12, step=1, value=3, label="定期重訓：每幾個月一次", show_value=True
    )
    thr_s = mo.ui.slider(
        start=0.70, stop=0.95, step=0.05, value=0.85,
        label="監控觸發：準確率門檻", show_value=True,
    )
    mo.vstack([drift_s, mo.hstack([k_s, thr_s], justify="start", gap=2, wrap=True)])
    return drift_s, k_s, thr_s


@app.cell
def _(C_MON, C_NONE, C_PER, XM, drift_s, k_s, np, plt, run, thr_s):
    cmp_drift = round(drift_s.value, 2)
    cmp_k = int(k_s.value)
    cmp_thr = round(thr_s.value, 2)
    cmp_runs = {
        "none": run("none", drift=cmp_drift),
        "periodic": run("periodic", drift=cmp_drift, k=cmp_k),
        "monitor": run("monitor", drift=cmp_drift, thr=cmp_thr),
    }

    _fig, _ax = plt.subplots(figsize=(6.4, 4.2))
    for _key, _color, _label in [
        ("none", C_NONE, "never retrained"),
        ("periodic", C_PER, f"every {cmp_k} months"),
        ("monitor", C_MON, f"retrain when acc < {cmp_thr:.2f}"),
    ]:
        _accs, _retrains = cmp_runs[_key]
        _ax.plot(XM, _accs, "-", color=_color, lw=2.2, label=_label)
        if _retrains:
            _ax.plot(
                list(_retrains), [1.005] * len(_retrains), "v",
                color=_color, ms=6.5, clip_on=False,
            )
    _ax.axhline(cmp_thr, ls="--", lw=1.1, color=C_MON, alpha=0.6)
    _ax.set_xlabel("months after launch")
    _ax.set_ylabel("accuracy of that month")
    _ax.set_title("Three strategies, same world (triangles = a retrain)")
    _ax.set_ylim(0.33, 1.03)
    _ax.set_xticks([1, 4, 8, 12, 16, 20, 23])
    _ax.legend(fontsize=8.5, loc="lower left")
    _ax.grid(alpha=0.3)
    _fig.tight_layout()
    _fig
    return cmp_drift, cmp_k, cmp_runs, cmp_thr


@app.cell(hide_code=True)
def _(cmp_drift, cmp_k, cmp_runs, cmp_thr, mo, np):
    _labels = {
        "none": "不重訓",
        "periodic": f"定期重訓（每 {cmp_k} 個月）",
        "monitor": f"監控觸發（門檻 {cmp_thr:.2f}）",
    }
    _base = float(np.mean(cmp_runs["none"][0]))
    _rows = []
    for _key in ["none", "periodic", "monitor"]:
        _accs, _retrains = cmp_runs[_key]
        _mean = float(np.mean(_accs))
        _gain = (
            f"{(_mean - _base) / len(_retrains) * 100:+.1f} 個百分點"
            if _retrains
            else "—"
        )
        _rows.append(
            f"    | {_labels[_key]} | {_mean:.3f} | {min(_accs):.3f} | "
            f"{len(_retrains)} 次 | {_gain} |"
        )
    _table = "\n".join(_rows)
    _mon_mean = float(np.mean(cmp_runs["monitor"][0]))
    _per_mean = float(np.mean(cmp_runs["periodic"][0]))
    _mon_n = len(cmp_runs["monitor"][1])
    _per_n = len(cmp_runs["periodic"][1])
    _verdict = (
        f"目前這組設定下，**監控觸發用 {_mon_n} 次重訓拿到 {_mon_mean:.3f}**，"
        f"定期重訓用 {_per_n} 次拿到 {_per_mean:.3f}。"
        if _mon_n <= _per_n
        else f"目前這組設定下，**監控觸發反而做了 {_mon_n} 次重訓**（定期重訓只做 {_per_n} 次）"
        f"——門檻拉太高，等於每個月都在重訓。"
    )
    mo.md(
        rf"""
    世界變化速度 {cmp_drift:.2f}：

    | 策略 | 平均準確率 | 最低的一個月 | 重訓次數 | 每次重訓平均買到 |
    |---|---:|---:|---:|---:|
{_table}

    {_verdict}

    **重訓次數就是成本**——算力、工程師的時間、每一次上線的風險。
    所以這張表要一起看兩欄：拿到多少準確率，付出多少次重訓。
    把門檻拉到 0.95 試試，你會看到它變成「每個月都重訓」；
    拉到 0.70，它幾乎不動，但平均掉得很難看。
    **門檻太高＝天天重訓，太低＝掉到很慘才救**——中間那個甜蜜點在你自己的成本結構裡。
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 4️⃣ 標籤總是遲到

    上一段的「監控觸發」偷藏了一個很甜的假設：**這個月準不準，這個月月底就知道**。

    真實世界很少這樣。你要等客戶真的解約、等帳單真的逾期、等病人真的回診，
    答案才會揭曉——標籤晚幾個月是常態。而標籤遲到會**同時**造成兩件事：

    1. **警報遲到**：第 12 個月的準確率，你第 15 個月才知道，那時已經爛了三個月。
    2. **教材也過期**：要重訓，只有「有標籤」的資料能用。你手上最新的有標籤資料也是三個月前的
       ——重訓出來的模型**一出生就落後三個月**。

    拉這根滑桿，看兩件事一起發生（上半張圖）；下半張圖是每一種延遲的平均成績（灰線是「每 6 個月固定重訓」的水準）：
    """
    )
    return


@app.cell
def _(mo):
    delay_s = mo.ui.slider(
        start=0, stop=6, step=1, value=3, label="標籤晚幾個月才拿到", show_value=True
    )
    delay_s
    return (delay_s,)


@app.cell
def _(C_FLAT, C_LATE, C_MON, C_NONE, XM, delay_s, delay_table, np, plt, run):
    lag = int(delay_s.value)
    lag_fast = run("monitor", delay=0)
    lag_slow = run("monitor", delay=lag)
    lag_per6 = run("periodic", k=6)
    lag_rows = delay_table()

    _fig, _axes = plt.subplots(2, 1, figsize=(6.4, 6.6))
    _axes[0].plot(XM, run("none")[0], "-", color=C_NONE, lw=1.6, alpha=0.55,
                  label="never retrained")
    _axes[0].plot(XM, lag_fast[0], "-", color=C_MON, lw=2.2, label="labels arrive at once")
    _axes[0].plot(XM, lag_slow[0], "-", color=C_LATE, lw=2.2,
                  label=f"labels {lag} months late")
    _axes[0].set_xlabel("months after launch")
    _axes[0].set_ylabel("accuracy of that month")
    _axes[0].set_title("Monitoring with late labels")
    _axes[0].set_ylim(0.33, 1.03)
    _axes[0].set_xticks([1, 4, 8, 12, 16, 20, 23])
    _axes[0].legend(fontsize=8.5, loc="lower left")
    _axes[0].grid(alpha=0.3)

    _ds = [_r[0] for _r in lag_rows]
    _means = [_r[1] for _r in lag_rows]
    _counts = [_r[2] for _r in lag_rows]
    _colors = [C_LATE if _d == lag else "#D9CFC4" for _d in _ds]
    _bars = _axes[1].bar(_ds, _means, color=_colors, edgecolor="#7A6E62", linewidth=0.8)
    for _d, _m, _c in zip(_ds, _means, _counts):
        _axes[1].text(_d, _m + 0.006, f"{_c}x", ha="center", fontsize=8.5, color="#4A4A4A")
    _axes[1].axhline(float(np.mean(lag_per6[0])), ls="--", lw=1.3, color=C_FLAT)
    _axes[1].text(
        6.45, float(np.mean(lag_per6[0])) + 0.008,
        f"blind retrain every 6 months ({len(lag_per6[1])}x)",
        fontsize=8.5, color="#6B6B6B", ha="right",
    )
    _axes[1].set_xlabel("how many months late the labels are")
    _axes[1].set_ylabel("mean accuracy")
    _axes[1].set_title("Late labels: worse results, more retrains (Nx = retrain count)")
    _axes[1].set_ylim(0.70, 0.95)
    _axes[1].grid(alpha=0.3, axis="y")
    _fig.tight_layout()
    _fig
    return lag, lag_fast, lag_per6, lag_rows, lag_slow


@app.cell(hide_code=True)
def _(lag, lag_fast, lag_per6, lag_rows, lag_slow, mo, np):
    _fast_m = float(np.mean(lag_fast[0]))
    _slow_m = float(np.mean(lag_slow[0]))
    _per_m = float(np.mean(lag_per6[0]))
    _table = "\n".join(
        f"    | 晚 {_d} 個月 | {_m:.3f} | {_c} 次 |" for _d, _m, _c in lag_rows
    )
    _now = (
        "標籤即時到位——這是上一段的理想狀況。"
        if lag == 0
        else (
            f"標籤晚 {lag} 個月：平均準確率從 **{_fast_m:.3f}** 掉到 **{_slow_m:.3f}**，"
            f"重訓次數卻從 {len(lag_fast[1])} 次變成 **{len(lag_slow[1])} 次**——又慢又忙。"
        )
    )
    _lose = (
        f"而且看下半張圖的灰線：延遲 {lag} 個月的監控觸發（{_slow_m:.3f}）"
        f"**已經輸給什麼都不看、每 6 個月固定重訓一次**（{_per_m:.3f}，只做 "
        f"{len(lag_per6[1])} 次重訓）。"
        if _slow_m < _per_m
        else f"目前它還贏過「每 6 個月固定重訓一次」（{_per_m:.3f}，"
        f"{len(lag_per6[1])} 次重訓）——把滑桿再往右拉，看它什麼時候輸掉。"
    )
    mo.md(
        rf"""
    | 標籤延遲 | 平均準確率 | 重訓次數 |
    |---|---:|---:|
{_table}

    {_now}

    {_lose}

    為什麼延遲會讓重訓**變多**？因為每次重訓用的都是過期教材，模型一出生就落後，
    很快又跌破門檻，於是再重訓一次——**追著自己的影子跑**。

    所以真實專案的第一個問題往往不是「要用什麼演算法」，而是
    **「我的標籤多久會到？」**——這個數字決定了你的監控值不值得做、
    決定了你該不該乾脆改用定期重訓，也決定了你要不要花錢去買更快的標籤
    （人工抽樣標註、找代理指標）。
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 5️⃣ 「監控觸發」要真的跑起來，需要五個零件

    到這裡你已經知道正確答案長什麼樣：**持續看著準確率，該重訓的時候重訓，
    而且要確定新模型真的比舊的好**。

    這句話講起來一秒，做起來需要五樣東西——每一樣就是這個系列的一課：

    | 你需要 | 沒有它會發生什麼 | 這個系列的哪一課 |
    |---|---|---|
    | 每次訓練的設定與指標**留得下紀錄、查得回來** | 你根本不知道是第幾個月開始掉的，也不知道當時用了什麼參數 | **01 MLflow 實驗追蹤** |
    | 模型有**版本**，新舊能比較，能一行換上去、換錯能退回 | 重訓出一顆新模型，但不敢換，因為不知道它比舊的好還壞 | **02 MLflow Models 與 Registry** |
    | 「取資料 → 訓練 → 評估」是一張**看得懂的圖**，不是散落的腳本 | 誰先誰後靠人腦記，換人接手就斷掉 | **03 Dagster 軟體定義資產** |
    | 有東西會在**對的時間按下重訓**（排程、或偵測到就觸發） | 監控會響，但沒有人按 | **04 Dagster 自動化：排程與感測** |
    | 上線前有**品質閘**，比舊版差就擋下來 | 重訓反而把線上弄壞——重訓不保證變好 | **05 Dagster × MLflow 管線** |

    最後一列特別值得留意：**這堂課的模擬對重訓太仁慈了**——這裡的重訓永遠成功、
    永遠拿得到乾淨的新資料、訓出來永遠不比舊的差。真實世界三件事都不保證。
    所以完整的自動重訓，最後一步一定是「**先擋下來，通過才換上去**」。

    「MLOps」這個詞聽起來很大，但它要解決的就是上面這五件事。
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 6️⃣ 換你動手

    下面四根滑桿是你的實驗區，把前面所有旋鈕放在一起：世界變化速度、定期重訓的週期、
    監控觸發的門檻、標籤延遲。三個挑戰（做完再打開下面的折疊解答對答案）：

    1. **LEVEL 1**：把「世界變得多快」拉到 **0**（世界完全不變），其他不動。
       三條線會變成什麼樣子？三種策略各重訓了幾次？誰做了白工？
    2. **LEVEL 2**：世界變化速度放回 **0.12**、標籤延遲 **0**，
       把準確率門檻從 **0.95** 一格一格拉到 **0.70**，記下每一格的平均準確率與重訓次數。
       多花 19 次重訓，平均準確率買到幾個百分點？
    3. **LEVEL 3**：把標籤延遲拉到 **6**，然後只調「多久重訓一次」，
       找出一個能**贏過**這個延遲六個月的監控觸發的定期重訓設定。
       怎麼驗證你贏了？看表格的兩欄——平均準確率更高、重訓次數更少。

    做完別忘了：教學頁上的「**下載 .py**」可以把這份模擬帶走，
    在自己電腦用 `uvx marimo edit lesson.py` 打開，資料怎麼生、模型怎麼訓全部攤在那裡。
    """
    )
    return


@app.cell
def _(mo):
    my_drift = mo.ui.slider(
        start=0.0, stop=0.13, step=0.01, value=0.12,
        label="世界變得多快", show_value=True,
    )
    my_k = mo.ui.slider(
        start=1, stop=12, step=1, value=3, label="每幾個月定期重訓", show_value=True
    )
    my_thr = mo.ui.slider(
        start=0.70, stop=0.95, step=0.05, value=0.85, label="監控觸發門檻", show_value=True
    )
    my_delay = mo.ui.slider(
        start=0, stop=6, step=1, value=0, label="標籤晚幾個月", show_value=True
    )
    mo.vstack(
        [
            mo.md("**你的實驗區**——四根滑桿，24 個月的模擬會整組重跑。"),
            mo.hstack([my_drift, my_k], justify="start", gap=2, wrap=True),
            mo.hstack([my_thr, my_delay], justify="start", gap=2, wrap=True),
        ]
    )
    return my_delay, my_drift, my_k, my_thr


@app.cell
def _(C_MON, C_NONE, C_PER, XM, my_delay, my_drift, my_k, my_thr, plt, run):
    my_cfg = (
        round(my_drift.value, 2), int(my_k.value),
        round(my_thr.value, 2), int(my_delay.value),
    )
    my_runs = {
        "none": run("none", drift=my_cfg[0]),
        "periodic": run("periodic", drift=my_cfg[0], k=my_cfg[1]),
        "monitor": run("monitor", drift=my_cfg[0], thr=my_cfg[2], delay=my_cfg[3]),
    }

    _fig, _ax = plt.subplots(figsize=(6.4, 4.2))
    for _key, _color, _label in [
        ("none", C_NONE, "never retrained"),
        ("periodic", C_PER, f"every {my_cfg[1]} months"),
        ("monitor", C_MON, f"acc < {my_cfg[2]:.2f}, labels {my_cfg[3]} months late"),
    ]:
        _accs, _retrains = my_runs[_key]
        _ax.plot(XM, _accs, "-", color=_color, lw=2.2, label=_label)
        if _retrains:
            _ax.plot(
                list(_retrains), [1.005] * len(_retrains), "v",
                color=_color, ms=6.5, clip_on=False,
            )
    _ax.set_xlabel("months after launch")
    _ax.set_ylabel("accuracy of that month")
    _ax.set_title(f"Your world (drift {my_cfg[0]:.2f})")
    _ax.set_ylim(0.33, 1.03)
    _ax.set_xticks([1, 4, 8, 12, 16, 20, 23])
    _ax.legend(fontsize=8.5, loc="lower left")
    _ax.grid(alpha=0.3)
    _fig.tight_layout()
    _fig
    return my_cfg, my_runs


@app.cell(hide_code=True)
def _(mo, my_cfg, my_runs, np):
    _names = {
        "none": "不重訓",
        "periodic": f"定期重訓（每 {my_cfg[1]} 個月）",
        "monitor": f"監控觸發（門檻 {my_cfg[2]:.2f}、標籤晚 {my_cfg[3]} 個月）",
    }
    _rows = "\n".join(
        f"    | {_names[_k]} | {float(np.mean(my_runs[_k][0])):.3f} | "
        f"{min(my_runs[_k][0]):.3f} | {len(my_runs[_k][1])} 次 |"
        for _k in ["none", "periodic", "monitor"]
    )
    _best = max(
        ["periodic", "monitor"], key=lambda _k: float(np.mean(my_runs[_k][0]))
    )
    _win = float(np.mean(my_runs[_best][0]))
    _other = "monitor" if _best == "periodic" else "periodic"
    _lose = float(np.mean(my_runs[_other][0]))
    mo.md(
        rf"""
    | 策略 | 平均準確率 | 最低的一個月 | 重訓次數 |
    |---|---:|---:|---:|
{_rows}

    這組設定下平均準確率較高的是 **{_names[_best]}**（{_win:.3f} vs {_lose:.3f}）——
    但別只看這一欄，**重訓次數那一欄才是帳單**。
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.accordion(
        {
            "💡 LEVEL 1 參考解答": mo.md(
                r"""
    把世界變化速度拉到 0，三條線都變成一條在 0.92 上下抖動的水平線。表格會長這樣
    （其餘維持預設：每 3 個月重訓、門檻 0.85、標籤不延遲）：

    | 策略 | 平均準確率 | 重訓次數 |
    |---|---:|---:|
    | 不重訓 | 0.926 | 0 次 |
    | 定期重訓（每 3 個月） | 0.922 | 7 次 |
    | 監控觸發（門檻 0.85） | 0.926 | 0 次 |

    做白工的是**定期重訓**：世界根本沒變，它照樣重訓了 7 次，
    平均準確率還微微低了一點點（每次重訓只用當月那 300 筆資料，運氣不好就抽到比較難的一批）。

    這就是「監控觸發」存在的理由——**它會在該省的時候自己安靜下來**。
    但別忘了它的前提：你得真的有在量準確率。沒有紀錄，你連「世界沒變」都不知道。
    """
            ),
            "💡 LEVEL 2 參考解答": mo.md(
                r"""
    門檻從 0.95 一路拉到 0.70（世界變化速度 0.12、標籤延遲 0）：

    | 門檻 | 平均準確率 | 重訓次數 |
    |---|---:|---:|
    | 0.95 | 0.916 | 23 次 |
    | 0.90 | 0.903 | 7 次 |
    | 0.85 | 0.889 | 4 次 |
    | 0.80 | 0.870 | 3 次 |
    | 0.75 | 0.849 | 2 次 |
    | 0.70 | 0.829 | 2 次 |

    從 0.85 到 0.95：重訓次數 **4 → 23 次**（模擬總共只有 23 個月，等於**每個月都在重訓**），
    平均準確率只買到 **2.7 個百分點**。多花 19 次重訓換 2.7 個百分點，划不划算？
    這題沒有標準答案，答案在你的成本表裡：一次重訓要多少錢與多少人力、
    準確率掉 1 個百分點你要賠多少。

    順帶一提，門檻 0.95 的 23 次重訓，成績（0.916）跟「每 1 個月定期重訓」一模一樣——
    **門檻拉到極限，監控觸發就退化成定期重訓**，還多花了監控的力氣。
    """
            ),
            "💡 LEVEL 3 提示與驗證": mo.md(
                r"""
    標籤延遲 6 個月的監控觸發：平均 **0.796**，做了 **14 次**重訓。

    只調「每幾個月定期重訓」，很快就會找到贏它的設定：

    | 定期重訓 | 平均準確率 | 重訓次數 |
    |---|---:|---:|
    | 每 6 個月 | 0.867 | 3 次 |
    | 每 3 個月 | 0.900 | 7 次 |
    | 每 1 個月 | 0.916 | 23 次 |

    **每 6 個月重訓一次就贏了**：準確率高 7 個百分點，重訓次數只有它的五分之一。

    怎麼驗證你真的贏了：表格要同時滿足兩件事——平均準確率更高、重訓次數更少。
    只有一項贏不算，那只是換了個位置花錢。

    帶得走的結論：**標籤越慢，監控觸發越沒有價值**。
    當標籤要等半年，與其精雕細琢門檻，不如把力氣花在兩件事上——
    想辦法更快拿到標籤（人工抽樣標註、找一個提早看得到的代理指標），
    或是乾脆改用簡單可靠的定期重訓，把省下來的力氣拿去做品質閘，
    確保每次重訓上線的模型不會比舊的差。

    最後一個給你自己的問題（沒有標準答案，但值得寫下來）：
    **你手上的專案，標籤多久會到？** 你會發現這個數字決定了後面所有的設計。
    """
            ),
        }
    )
    return


if __name__ == "__main__":
    app.run()
