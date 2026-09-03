# Feast 特徵倉：訓練與上線用同一份特徵（point-in-time join、ttl、materialize、online store）
# 不需要 GPU——molab 免費 CPU 環境即可全程執行（全部跑在 notebook 自己的機器上，不連任何外部服務）。
# /// script
# requires-python = ">=3.11,<3.14"
# dependencies = [
#     "marimo",
#     "feast>=0.50",
#     "pandas",
#     "numpy",
#     "pyarrow",
#     "scikit-learn",
#     "mlflow>=3.0",
#     "matplotlib",
#     "tabulate",
# ]
# ///
import marimo

__generated_with = "0.23.16"
app = marimo.App(width="medium", app_title="Feast 特徵倉：訓練與上線用同一份特徵")


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    # ⚡ Feast 特徵倉：訓練與上線用同一份特徵

    上一課你把模型的每一次呼叫都記了下來。這一課往回退一步，處理一個**在模型之前**就會出事的地方：
    **特徵是怎麼算出來的。**

    兩個經典災難，幾乎每個做過上線的人都遇過：

    - **訓練／上線不一致（training-serving skew）**：訓練時是資料科學家用 pandas 算「近 30 天訂單數」，
      上線時是後端工程師用 SQL 再寫一次。兩段程式、兩個人、兩種時區假設、兩種 null 處理——
      模型在離線很準，上線就是差一截，而且**沒有任何錯誤訊息**。
    - **資料洩漏（data leakage）**：訓練資料裡混進了「當時還不知道」的未來資訊。
      最常見的形式沒那麼戲劇化——只是 join 的時候順手拿了「這位客戶最新的一筆特徵」。

    特徵倉（feature store）給的是兩個承諾：

    1. **同一份定義**：訓練拿特徵與上線拿特徵，走的是同一個定義、同一份程式。
    2. **point-in-time 正確**：每一筆訓練樣本只拿得到「事件發生那一刻」已經存在的特徵值。

    這份 notebook 用 [Feast](https://docs.feast.dev/)（開源特徵倉，全程跑在本機檔案與 SQLite 上）把兩個承諾做出來：

    1. 兩個災難：手寫 join 有多容易寫錯（實測有多少列拿到了未來的值）
    2. Feast 的三個定義：Entity、FeatureView、Field，以及 `feature_store.yaml` 那幾行
    3. 離線：`get_historical_features` 的 point-in-time join，跟手寫版對答案
    4. `ttl`：太舊的特徵不給——而 Feast 的做法比你想的更狠
    5. 訓練：把 join 出來的特徵餵給模型，記到 MLflow
    6. 上線：`materialize` 推進 online store、毫秒級 `get_online_features`、**同一份定義**
    7. 特徵服務與版本：`FeatureService`、加欄位再 `apply`、on-demand 特徵
    8. 互動：選一位客戶、拉事件時間，看 point-in-time 拿到哪一筆
    9. 常見錯誤原文速查

    **不需要 GPU**，molab 免費 CPU 環境從第一格往下全部執行即可（首次安裝套件約 1–2 分鐘）。
    整份 notebook 的 Feast 操作加起來不到一秒——慢的只有裝套件。

    > 資料是模擬的、亂數有固定種子，所以**次數與筆數每次跑都一樣**；
    > 只有日期會跟著你執行的當天走，毫秒數會跟著你的機器走。
    """
    )
    return


@app.cell
def _():
    import contextlib
    import datetime as dt
    import io
    import logging
    import re
    import shutil
    import sqlite3
    import tempfile
    import textwrap
    import time
    import warnings
    from pathlib import Path

    import marimo as mo
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import mlflow
    import numpy as np
    import pandas as pd
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import accuracy_score, roc_auc_score

    # Feast 與 MLflow 的日誌都很吵，教學輸出會被蓋掉
    logging.getLogger("feast").setLevel(logging.ERROR)
    logging.getLogger("mlflow").setLevel(logging.ERROR)
    warnings.filterwarnings("ignore")
    return (
        LogisticRegression,
        Path,
        RandomForestClassifier,
        accuracy_score,
        contextlib,
        dt,
        io,
        mlflow,
        mo,
        np,
        pd,
        plt,
        re,
        roc_auc_score,
        shutil,
        sqlite3,
        tempfile,
        textwrap,
        time,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 0️⃣ 準備：一張每日快照表，一張事件表

    特徵倉的世界只有兩種表，先把它們的角色分清楚——**這是本課最重要的一組名詞**：

    | | **快照表（特徵來源）** | **事件表（entity dataframe）** |
    |---|---|---|
    | 一列代表 | 某位客戶在**某一天**的樣子 | 某一次**真的發生過的事**（要預測的那一刻） |
    | 誰在寫 | 每天半夜的批次工作 | 業務系統（推播、下單、進線） |
    | 有什麼欄位 | 客戶 id、時間戳、特徵值 | 客戶 id、時間戳、**標籤** |
    | 誰在用 | Feast 的 source | 你丟給 Feast 的查詢 |

    本課的故事：一家電商每天半夜跑一次批次，把每位客戶「近 30 天的訂單數／金額／退貨率」寫成一列快照。
    行銷系統會不定時對客戶發「續約提醒」推播，30 天後回頭看這位客戶有沒有流失——那就是標籤。

    - **快照表** `customer_daily`：20 位客戶 × 10 天。
      其中 3 位客戶有**斷線**（上游管線壞掉那幾天沒收到資料）——這不是為了刁難你，
      真實的特徵表一定有洞，而它正是第 4 節 `ttl` 要處理的東西。
    - **事件表** `promo_events`：360 次推播，散落在這 10 天裡，每一筆帶著 `churn` 標籤。

    先建工作目錄。所有東西（parquet、registry、online store、MLflow 的 SQLite）都放在暫存資料夾裡，
    開頭先清空，**重跑數字才會一樣**。
    """
    )
    return


@app.cell
def _(Path, dt, shutil, tempfile):
    WORK = Path(tempfile.gettempdir()) / "feast-lesson"
    shutil.rmtree(WORK, ignore_errors=True)
    (WORK / "data").mkdir(parents=True)

    # 所有時間都相對「現在」算，所以你今天跑、明天跑，結構完全一樣
    NOW = dt.datetime.now(dt.UTC).replace(minute=0, second=0, microsecond=0)

    def snap_ts(day: int) -> dt.datetime:
        """第 day 天（0–9）那次批次的時間戳；day 9 就是現在，也就是最新的一筆快照。"""
        return NOW - dt.timedelta(days=9 - day)

    return NOW, WORK, snap_ts


@app.cell
def _(WORK, np, pd, snap_ts):
    # 3 位客戶的上游管線斷線：那幾天沒有快照（真實特徵表一定有洞）
    GAPS = {7: [4, 5, 6], 13: [2, 3], 19: [6, 7, 8]}

    _rng = np.random.default_rng(7)
    _base_orders = _rng.integers(1, 12, size=20)  # 每位客戶的基準訂單數
    _trend = _rng.normal(0, 0.55, size=20)  # 每天的漂移（有人越買越多，有人正在流失）
    _base_ret = _rng.uniform(0.02, 0.22, size=20)

    _rows = []
    for _cid in range(1, 21):
        _i = _cid - 1
        for _d in range(10):
            if _d in GAPS.get(_cid, []):
                continue
            _n = max(0, round(float(_base_orders[_i] + _trend[_i] * _d + _rng.normal(0, 0.7))))
            _tot = max(0.0, float(round(_n * _rng.uniform(180, 420) + _rng.normal(0, 60), 2)))
            _ret = float(round(min(0.6, max(0.0, _base_ret[_i] + 0.012 * _d + _rng.normal(0, 0.02))), 4))
            _rows.append(
                {
                    "customer_id": _cid,
                    "event_timestamp": snap_ts(_d),
                    "n_orders_30d": _n,
                    "total_30d": _tot,
                    "return_rate": _ret,
                }
            )

    snapshots = pd.DataFrame(_rows)
    snapshots["n_orders_30d"] = snapshots["n_orders_30d"].astype("int64")
    snapshots["total_30d"] = snapshots["total_30d"].astype("float32")
    snapshots["return_rate"] = snapshots["return_rate"].astype("float32")

    # Feast 的檔案來源吃 parquet；時間戳一定要**帶時區**（這裡是 UTC）
    PARQUET = WORK / "data" / "customer_daily.parquet"
    snapshots.to_parquet(PARQUET)
    return GAPS, PARQUET, snapshots


@app.cell
def _(dt, np, pd, snapshots, snap_ts):
    def hand_pit(cid, ts, ttl_days=None, table=None):
        """手寫的 point-in-time 查詢：拿「ts 之前」最後一筆快照。ttl_days 給了就再檢查新鮮度。"""
        _t = snapshots if table is None else table
        _s = _t[(_t.customer_id == cid) & (_t.event_timestamp <= ts)]
        if _s.empty:
            return None
        _r = _s.sort_values("event_timestamp").iloc[-1]
        if ttl_days is not None and (ts - _r.event_timestamp) > dt.timedelta(days=ttl_days):
            return None
        return _r

    _erng = np.random.default_rng(21)
    _ev = []
    for _ in range(360):
        _cid = int(_erng.integers(1, 21))
        _d = int(_erng.integers(1, 9))  # 第 1–8 天（第 0 天之前沒有快照可查）
        _ts = snap_ts(_d) + dt.timedelta(hours=float(_erng.uniform(1, 23)))
        _r = hand_pit(_cid, _ts)
        # 標籤由「事件當下」的特徵決定：退貨率高、訂單少的客戶比較容易流失
        _z = -0.32 * (_r.n_orders_30d - 5) + 9.0 * (_r.return_rate - 0.12) - 0.0012 * (_r.total_30d - 1400)
        _ev.append(
            {"customer_id": _cid, "event_timestamp": _ts, "churn": int(_erng.random() < 1 / (1 + np.exp(-_z)))}
        )

    events = pd.DataFrame(_ev).sort_values("event_timestamp").reset_index(drop=True)
    return events, hand_pit


@app.cell(hide_code=True)
def _(GAPS, PARQUET, WORK, events, mo, snapshots):
    mo.md(
        f"""
    工作目錄 `{WORK}`

    **快照表**：{len(snapshots)} 列（滿版會是 200 列，3 位客戶斷線 {GAPS}，少了 {200 - len(snapshots)} 列）
    ，存成 `{PARQUET.name}`

    {snapshots.head(4).to_markdown(index=False)}

    **事件表**：{len(events)} 筆推播，流失率 {events.churn.mean():.1%}

    {events.head(4).to_markdown(index=False)}

    注意快照表的 `event_timestamp` 是 **tz-aware（UTC）** 的：`{snapshots.event_timestamp.dtype}`。
    這件事等一下會變成一個很痛的坑。
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 1️⃣ 災難現場：一行 join，60% 的訓練資料都錯了

    要做訓練集，你得把「事件」跟「特徵」接起來。最直覺的寫法是這樣——

    ```python
    latest = (snapshots.sort_values("event_timestamp")
              .groupby("customer_id").tail(1)            # 每位客戶最新的一筆
              .set_index("customer_id")[FEATURE_COLS])
    train = events.join(latest, on="customer_id")        # 一行搞定
    ```

    這行 join 有一個致命的假設：**「最新的一筆」對每一個事件都適用。**
    但事件發生在 8 天前，「最新的一筆」是今天早上才算出來的——
    你等於在告訴模型「這位客戶 8 天後的退貨率是 0.20」，然後要它預測 8 天前的事。

    模型上線之後拿不到這種資訊（未來還沒發生），所以它學到的那套規則在上線時**根本不存在**。
    這就是**資料洩漏**最常見、最不起眼、也最難抓的形式：不是誰把答案欄位放進特徵，
    而是 join 的時候少寫了一個時間條件。

    正確的做法叫 **point-in-time join**：一筆一筆問「這個事件發生的那一刻，這位客戶最新的快照是哪一筆？」
    下面把兩種寫法都做出來，然後數數看差多少。
    """
    )
    return


@app.cell
def _(events, hand_pit, pd, snap_ts, snapshots):
    FEATURE_COLS = ["n_orders_30d", "total_30d", "return_rate"]

    # 寫法 A（錯的）：每位客戶最新的一筆，無視事件時間
    _latest = (
        snapshots.sort_values("event_timestamp").groupby("customer_id").tail(1).set_index("customer_id")[FEATURE_COLS]
    )
    naive_join = events.join(_latest, on="customer_id")

    # 寫法 B（對的，但要自己顧）：一筆一筆做 point-in-time 查詢
    _hits = [hand_pit(_r.customer_id, _r.event_timestamp) for _r in events.itertuples()]
    hand_join = events.copy()
    for _c in FEATURE_COLS:
        hand_join[_c] = [None if _h is None else _h[_c] for _h in _hits]
    hand_join["snapshot_ts"] = [None if _h is None else _h["event_timestamp"] for _h in _hits]

    # 兩種寫法差在哪
    _same = naive_join["n_orders_30d"].values == hand_join["n_orders_30d"].values
    N_DIFF = int((~_same).sum())
    _gaps = (naive_join["n_orders_30d"].astype(float) - hand_join["n_orders_30d"].astype(float)).abs()
    GAP_MAX = int(_gaps.max())
    # 那行 join 一律拿「最新的一筆」（第 9 天），所以特徵值來自事件之後這麼多天
    FUTURE_DAYS = (snap_ts(9) - events["event_timestamp"]).dt.total_seconds() / 86400
    FRESH_H = (events["event_timestamp"] - hand_join["snapshot_ts"]).dt.total_seconds() / 3600
    WORST = (
        pd.DataFrame(
            {
                "customer_id": events.customer_id,
                "event_timestamp": events.event_timestamp,
                "pit_orders": hand_join.n_orders_30d,
                "naive_orders": naive_join.n_orders_30d,
                "pit_ret": hand_join.return_rate,
                "naive_ret": naive_join.return_rate,
                "future_days": FUTURE_DAYS.round(1),
            }
        )
        .assign(gap=lambda d: (d.naive_orders - d.pit_orders).abs())
        .sort_values("gap", ascending=False)
        .head(3)
    )
    return FEATURE_COLS, FRESH_H, FUTURE_DAYS, GAP_MAX, N_DIFF, WORST, hand_join, naive_join


@app.cell(hide_code=True)
def _(FRESH_H, FUTURE_DAYS, GAP_MAX, N_DIFF, WORST, events, mo):
    mo.md(
        f"""
    **兩種寫法的差距**（{len(events)} 筆事件）：

    | | 值 |
    |---|---|
    | 拿到不一樣的 `n_orders_30d` 的事件 | **{N_DIFF} / {len(events)}（{N_DIFF / len(events):.0%}）** |
    | 最大差距 | {GAP_MAX} 筆訂單 |
    | 特徵值來自事件之後最多幾天 | **{FUTURE_DAYS.max():.1f} 天** |
    | 正確做法拿到的特徵有多新（小時） | 最新 {FRESH_H.min():.0f} ／ 中位 {FRESH_H.median():.0f} ／ 最舊 {FRESH_H.max():.0f} |

    差最多的三筆長這樣：

    {WORST.to_markdown(index=False)}

    看第一列：這位客戶在事件當天的快照是 `pit_orders` 筆訂單、退貨率 `pit_ret`；
    但那行 join 給模型的是 `naive_orders` 筆、退貨率 `naive_ret`——那是**事件之後好幾天**才算出來的數字，
    正好記錄了「這位客戶後來不買了」。模型看到這種特徵當然學得很開心，上線時卻永遠拿不到。

    也不是每一筆都錯得這麼誇張：多數客戶的訂單數這幾天沒什麼變化，
    所以那行 join **在 {len(events) - N_DIFF} 筆事件上剛好是對的**——
    這正是它可怕的地方，錯誤是散在資料裡的，不會集中成一個看得出來的症狀。
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    下面這張圖把「特徵值來自事件之後幾天」畫出來。紅色是**值真的不一樣**的那些事件——
    離事件越遠的快照，錯得越離譜。
    """
    )
    return


@app.cell
def _(FUTURE_DAYS, hand_join, naive_join, np, plt):
    _bins = np.arange(0, 8)
    _diff = naive_join["n_orders_30d"].values != hand_join["n_orders_30d"].values
    _days = FUTURE_DAYS.values.astype(int)
    _same_cnt = [int(((_days == _b) & ~_diff).sum()) for _b in _bins]
    _diff_cnt = [int(((_days == _b) & _diff).sum()) for _b in _bins]

    _fig, _ax = plt.subplots(figsize=(6.2, 3.1))
    _ax.bar(_bins, _same_cnt, color="#B9BDC6", label="same value (leak had no effect)")
    _ax.bar(_bins, _diff_cnt, bottom=_same_cnt, color="#C44E52", label="different value (leaked)")
    _ax.set_xlabel("feature value came from N days AFTER the event")
    _ax.set_ylabel("number of training rows")
    _ax.set_title('"take the latest snapshot" join: how far into the future', fontsize=10)
    _ax.set_ylim(0, max(_s + _d for _s, _d in zip(_same_cnt, _diff_cnt, strict=False)) * 1.42)
    _ax.legend(fontsize=8, loc="upper left", framealpha=1.0)
    _ax.spines[["top", "right"]].set_visible(False)
    _fig.tight_layout()
    _fig
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ### 那用 `merge_asof` 就好了吧？

    pandas 確實有一個現成的工具做這件事：

    ```python
    asof = pd.merge_asof(
        events.sort_values("event_timestamp"),        # ← 兩邊都必須先排序，否則直接報錯
        snapshots.sort_values("event_timestamp"),
        on="event_timestamp",
        by="customer_id",                             # ← 忘了它，會拿到別人的特徵
        direction="backward",                         # ← 忘了它，預設會往後找（洩漏）
        tolerance=pd.Timedelta(days=3),               # ← 忘了它，會拿到 3 個月前的特徵
    )
    ```

    這段是對的。問題不在寫不寫得出來，在於**這段程式住在哪裡**：

    - 它住在資料科學家的 notebook 裡。上線的後端工程師看不到它，
      他會照著規格文件用 SQL 再寫一次——`direction`、`tolerance`、時區處理有一個沒對上，就是 skew。
    - 半年後要加一個特徵，這段要改；訓練管線、上線服務、批次評分腳本各有一份，改漏一個就出事。
    - 它沒有名字。沒有人能問「`n_orders_30d` 是誰定義的、算多久、什麼時候更新」。

    **特徵倉不是因為 join 難寫才存在，是因為 join 的定義需要一個唯一的家。**
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ### 順帶一個會讓你整批資料默默錯掉的坑：時區

    快照表的時間戳如果**沒有帶時區**（naive datetime），Feast 與 pandas 都會把它當成 UTC——
    不報錯、不警告。如果那些時間其實是台北時間，整張表就往後跑了 8 小時，
    每一次 point-in-time 查詢都可能拿到前一天的快照。實測一下差多少：
    """
    )
    return


@app.cell
def _(dt, events, hand_join, hand_pit, snapshots):
    # 假裝當初存檔的人把「台北時間」直接存成沒有時區的字串，讀的人當成 UTC
    _tz_table = snapshots.copy()
    _tz_table["event_timestamp"] = _tz_table["event_timestamp"] + dt.timedelta(hours=8)
    _tz_hits = [hand_pit(_r.customer_id, _r.event_timestamp, table=_tz_table) for _r in events.itertuples()]
    _tz_vals = [None if _h is None else _h["n_orders_30d"] for _h in _tz_hits]
    _ok = hand_join["n_orders_30d"].tolist()
    TZ_DIFF = sum(1 for _a, _b in zip(_ok, _tz_vals) if _a != _b)
    TZ_NONE = sum(1 for _v in _tz_vals if _v is None)
    return TZ_DIFF, TZ_NONE


@app.cell(hide_code=True)
def _(TZ_DIFF, TZ_NONE, events, mo):
    mo.md(
        f"""
    差 8 小時的結果：**{TZ_DIFF} / {len(events)} 筆事件拿到不一樣的特徵值**
    （其中 {TZ_NONE} 筆變成完全查不到）。

    沒有例外、沒有警告、模型照樣訓練得出來、AUC 照樣有數字——只是全部建立在錯的特徵上。
    這也是為什麼本課的快照表從第一行就堅持 **tz-aware（UTC）**：
    時區不是格式問題，是**資料正確性問題**。
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 2️⃣ Feast 的三個定義：誰、什麼、從哪來

    Feast 把「特徵是什麼」拆成三個東西，加起來就是一份**可以被別人讀、被版本控管、被兩邊共用**的定義：

    | 定義 | 回答的問題 | 本課的例子 |
    |---|---|---|
    | **Entity** | 特徵是「誰」的？ | 客戶（join key 是 `customer_id`） |
    | **FeatureView** | 一組特徵、從哪張表來、多久算過期 | `customer_daily`，來源是那張 parquet，`ttl=3 天` |
    | **Field** | 每個特徵叫什麼、什麼型別 | `n_orders_30d: Int64`、`return_rate: Float32` |

    另外還有一個檔案 `feature_store.yaml`，講的是**基礎設施**：東西存在哪裡。
    它只有三個角色，但這三個角色是理解特徵倉的關鍵：

    | 角色 | 存什麼 | 誰在讀 | 本課用什麼 | 正式環境常見 |
    |---|---|---|---|---|
    | **registry** | 定義本身（Entity／FeatureView／Field） | 所有人 | 一個本機檔案 `registry.db` | S3／GCS 上的一個檔，或 SQL registry |
    | **offline store** | 完整的歷史（每一天每一位客戶） | 訓練、批次評分 | 那張 parquet | BigQuery／Snowflake／Redshift／Spark |
    | **online store** | **只有每位客戶最新的一筆** | 線上服務 | 一個 SQLite 檔 | Redis／DynamoDB／Bigtable |

    看懂這張表就看懂特徵倉了：**同一份定義（registry），兩個資料倉庫**。
    離線那邊要「查得到過去任何一刻」，所以慢而全；線上那邊只要「現在最新值、毫秒內回答」，所以快而薄。
    """
    )
    return


@app.cell
def _(WORK, textwrap):
    _YAML = textwrap.dedent("""
        project: churn                       # 命名空間：同一個 registry 可以放好幾個專案
        provider: local                      # 跑在本機（正式環境會是 aws / gcp / 自訂）
        registry: data/registry.db           # 定義存在哪（相對於這個資料夾）
        online_store:
          type: sqlite                       # 線上取特徵用的快取（正式環境常換成 redis）
          path: data/online.db
        entity_key_serialization_version: 3  # 新專案用 3；照抄就好
    """).lstrip()
    (WORK / "feature_store.yaml").write_text(_YAML)
    FS_YAML = _YAML
    return (FS_YAML,)


@app.cell
def _(PARQUET, dt):
    from feast import (
        Entity,
        FeatureService,
        FeatureStore,
        FeatureView,
        Field,
        FileSource,
        ValueType,
    )
    from feast.types import Float32, Float64, Int64

    customer = Entity(
        name="customer",
        join_keys=["customer_id"],  # 事件表裡要有這個欄位，Feast 才知道怎麼對
        value_type=ValueType.INT64,
        description="一位電商客戶",
    )

    daily_source = FileSource(
        path=str(PARQUET),  # 給絕對路徑最安全（相對路徑是相對於 repo_path）
        timestamp_field="event_timestamp",  # 「這一列是什麼時候算出來的」
    )

    customer_daily = FeatureView(
        name="customer_daily",
        entities=[customer],
        ttl=dt.timedelta(days=3),  # 超過 3 天沒更新的快照，就當它不存在
        schema=[
            Field(name="n_orders_30d", dtype=Int64),
            Field(name="total_30d", dtype=Float32),
            Field(name="return_rate", dtype=Float32),
        ],
        source=daily_source,
        online=True,  # 這組特徵要推到 online store 給線上服務用
    )
    return (
        Entity,
        FeatureService,
        FeatureStore,
        FeatureView,
        Field,
        FileSource,
        Float32,
        Float64,
        Int64,
        customer,
        customer_daily,
        daily_source,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    定義寫好了，但它們現在還只是 Python 物件。`store.apply()` 把它們**寫進 registry**——
    從這一刻起，這些定義就不屬於某個人的 notebook 了，任何人只要指向同一個 registry 就讀得到。

    很多教學文件會告訴你在終端機下 `feast apply`。在 notebook 裡直接用 Python API 就好
    （順帶一提：`python -m feast` 是跑不起來的，它沒有 `__main__`——
    CLI 的名字是 `feast`，而 `store.apply()` 做的事跟它一模一樣）。
    """
    )
    return


@app.cell
def _(FeatureStore, WORK, customer, customer_daily, time):
    store = FeatureStore(repo_path=str(WORK))  # 讀 WORK/feature_store.yaml

    _t0 = time.perf_counter()
    store.apply([customer, customer_daily])  # ← 等同 CLI 的 `feast apply`
    APPLY_MS = (time.perf_counter() - _t0) * 1000
    applied = True  # 給下游 cell 當「已經 apply 過了」的訊號
    return APPLY_MS, applied, store


@app.cell(hide_code=True)
def _(APPLY_MS, WORK, mo, store):
    _fv = store.get_feature_view("customer_daily")
    _reg = WORK / "data" / "registry.db"
    mo.md(
        f"""
    `apply()` 花了 **{APPLY_MS:.0f} ms**，registry 檔案 `{_reg.name}` 現在有 **{_reg.stat().st_size} bytes**。
    這麼小是因為它只存**定義**，不存資料。

    | registry 裡有什麼 | |
    |---|---|
    | entities | `{[_e.name for _e in store.list_entities()]}` |
    | feature views | `{[_v.name for _v in store.list_feature_views()]}` |
    | `customer_daily` 的 ttl | `{_fv.ttl}` |
    | `customer_daily` 的欄位 | `{sorted(_f.name for _f in _fv.schema)}` |
    | 來源 | `{_fv.source.path}` |

    注意 `schema` 裡多了一個 `customer_id`——Feast 會自動把 entity 的 join key 併進去。
    另外**欄位順序跟你宣告的不一樣**（registry 內部是無序的），寫程式時不要靠順序取值。
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 3️⃣ 離線：`get_historical_features` 的 point-in-time join

    現在把整張事件表丟給 Feast。你要給它兩樣東西：

    - **entity dataframe**：至少要有 join key（`customer_id`）與一個叫 **`event_timestamp`** 的欄位。
      其他欄位（例如標籤 `churn`）會原封不動被帶回來——所以直接把事件表丟進去就好。
    - **要哪些特徵**：`"feature_view:feature"` 的字串清單。

    Feast 會對**每一列**分別去找「那一刻最新的快照」。這就是第 1 節你手寫的那件事，
    差別在於：這次它是一個**有名字的定義**，訓練跟上線都會走同一份。
    """
    )
    return


@app.cell
def _(applied, events, store, time):
    FEATURE_REFS = [
        "customer_daily:n_orders_30d",
        "customer_daily:total_30d",
        "customer_daily:return_rate",
    ]

    _t0 = time.perf_counter()
    training_df = store.get_historical_features(
        entity_df=events,  # 客戶 id ＋ event_timestamp ＋ 標籤
        features=FEATURE_REFS,
    ).to_df()
    HIST_MS = (time.perf_counter() - _t0) * 1000
    _ = applied
    return FEATURE_REFS, HIST_MS, training_df


@app.cell(hide_code=True)
def _(HIST_MS, events, hand_join, mo, training_df):
    # 跟第 1 節手寫的版本對答案（用 key 對，不能用位置——回傳的列順序跟 entity_df 不同）
    _hand = hand_join.set_index(["customer_id", "event_timestamp"])
    _feast = training_df.set_index(["customer_id", "event_timestamp"])
    _joined = _feast.join(_hand[["n_orders_30d"]], rsuffix="_hand")
    _agree = (_joined["n_orders_30d"] == _joined["n_orders_30d_hand"]).mean()

    mo.md(
        f"""
    {HIST_MS:.0f} ms，回來 **{len(training_df)} 列**，欄位 `{list(training_df.columns)}`。

    {training_df.head(4).to_markdown(index=False)}

    **跟手寫版對答案：一致率 {_agree:.1%}**——Feast 做的就是你剛剛手寫的那件事，一模一樣。

    但有兩件事要盯著看：

    1. **進去 {len(events)} 列，出來 {len(training_df)} 列。**
       少了 {len(events) - len(training_df)} 列，而且 `isna()` 全都是 0——
       它們不是變成 NaN，是**整列消失了**。下一節解釋。
    2. **回傳的列順序跟你丟進去的不一樣。**
       不要用 `.values` 或 `reset_index()` 去對齊兩張表，一律用 join key 對——
       這種靜默錯位比報錯難查一百倍。
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 4️⃣ `ttl`：太舊的特徵不給——而且它不是給你 NaN

    `ttl=timedelta(days=3)` 的意思是：**一筆快照從它被算出來那一刻起，只「有效」3 天。**
    事件發生時如果最近的一筆快照已經超過 3 天沒更新，Feast 就當這位客戶當時沒有特徵。

    這個設定不是可有可無的細節，它在回答一個很重要的問題：
    **「上游壞掉沒有更新資料時，模型該用舊值硬撐，還是該知道自己不知道？」**

    - `ttl` 太長：上游停更一週，模型還在用一週前的行為預測今天，而且完全不知道自己在用舊資料。
    - `ttl` 太短：正常的更新延遲（批次晚跑一小時）就讓大量樣本沒有特徵。
    - 合理的起點：**你的更新週期 × 2～3**。本課是每天更新，所以 `ttl` 給 3 天。

    這裡有一個**你一定要親眼看過一次**的行為：ttl 到期時，Feast 的檔案 offline store
    **不是把特徵填成 NaN，而是把整列從結果裡拿掉**。訓練集靜靜地少了幾筆，
    `isna()` 檢查不出來、`shape` 你也不會每次都看。下面用同一位客戶的三個事件時間示範：
    """
    )
    return


@app.cell
def _(FEATURE_REFS, dt, pd, snap_ts, store, training_df):
    # 客戶 7 在第 4–6 天斷線：最後一筆快照停在第 3 天
    _probe = pd.DataFrame(
        {
            "customer_id": [7, 7, 7],
            "event_timestamp": [
                snap_ts(3) + dt.timedelta(hours=2),  # 快照剛出爐 2 小時
                snap_ts(5) + dt.timedelta(hours=2),  # 快照已經 2 天又 2 小時舊
                snap_ts(6) + dt.timedelta(hours=12),  # 快照已經 3 天又 12 小時舊 → 超過 ttl
            ],
        }
    )
    ttl_probe = store.get_historical_features(entity_df=_probe, features=FEATURE_REFS).to_df()
    _ = training_df  # 先跑完上一節的查詢再跑這一格
    return (ttl_probe,)


@app.cell(hide_code=True)
def _(events, mo, training_df, ttl_probe):
    mo.md(
        f"""
    丟進去 3 列，回來 **{len(ttl_probe)} 列**：

    {ttl_probe.to_markdown(index=False)}

    第三個事件（快照已經 3 天半沒更新）就這樣不見了。整份訓練集也是同一回事：
    {len(events)} 筆事件進去、{len(training_df)} 筆出來，
    **{len(events) - len(training_df)} 筆被 ttl 吃掉**，而且沒有任何訊息。

    所以請養成一個習慣：**`get_historical_features` 之後永遠比對筆數**。

    ```python
    got = store.get_historical_features(entity_df=events, features=REFS).to_df()
    if len(got) != len(events):
        raise ValueError(f"少了 {{len(events) - len(got)}} 筆：檢查 ttl 與上游更新狀況")
    ```

    這一行檢查的價值不只是抓 bug——**少掉的那些列本身就是訊號**：
    它們是「上游資料在那段時間壞掉」的客戶，而那通常也是最該被關注的客戶。
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    下面這張圖把整件事畫在一條時間軸上（就是那位斷線的客戶 7）：
    圓點是每天的快照，中間那段空白是上游壞掉的三天。
    """
    )
    return


@app.cell
def _(np, plt, snapshots):
    _c7 = snapshots[snapshots.customer_id == 7].sort_values("event_timestamp")
    _idx = np.array([9 - (_c7.event_timestamp.max() - _t).days for _t in _c7.event_timestamp])
    _series = np.full(10, np.nan)  # 缺的那三天留 NaN，線才會斷開
    _series[_idx] = _c7.n_orders_30d.to_numpy()
    _lo, _hi = np.nanmin(_series), np.nanmax(_series)
    _top = _hi + (_hi - _lo) * 0.42
    _event = 6.5

    _fig, _ax = plt.subplots(figsize=(6.4, 3.3))
    _ax.axvspan(3.5, 6.5, color="#9AA0A6", alpha=0.09)
    _ax.text(5.0, _lo + (_hi - _lo) * 0.62, "no data\n(pipeline down)", ha="center", fontsize=8, color="#6b7178")
    _ax.plot(range(10), _series, "o-", color="#4C72B0", lw=1.8, ms=7)
    _ax.axvline(_event, color="#C44E52", ls="--", lw=1.6)
    _ax.text(_event + 0.12, _lo + (_hi - _lo) * 0.05, "event", color="#C44E52", fontsize=9)

    _ttl_y = _hi + (_hi - _lo) * 0.20
    _ax.annotate(
        "",
        xy=(3.5, _ttl_y),
        xytext=(6.5, _ttl_y),
        arrowprops={"arrowstyle": "|-|", "color": "#55A868", "lw": 1.4},
    )
    _ax.text(5.0, _ttl_y + (_hi - _lo) * 0.05, "ttl = 3 days", ha="center", fontsize=8.5, color="#3d7a4d")

    _ax.annotate(
        "last snapshot before the event\n3.5 days old -> outside ttl -> row dropped",
        xy=(3, _series[3]),
        xytext=(0.0, _hi + (_hi - _lo) * 0.02),
        fontsize=8,
        color="#4C72B0",
        arrowprops={"arrowstyle": "->", "color": "#4C72B0"},
    )
    _ax.annotate(
        '"take the latest" join\nwould use this value\n(2.5 days after the event)',
        xy=(9, _series[9]),
        xytext=(6.62, _lo + (_hi - _lo) * 0.42),
        fontsize=8,
        color="#DD8452",
        arrowprops={"arrowstyle": "->", "color": "#DD8452"},
    )
    _ax.set_xlabel("day index (9 = now)")
    _ax.set_ylabel("n_orders_30d")
    _ax.set_title("customer 7: what each join strategy picks", fontsize=10)
    _ax.set_xticks(range(10))
    _ax.set_ylim(_lo - (_hi - _lo) * 0.18, _top)
    _ax.spines[["top", "right"]].set_visible(False)
    _fig.tight_layout()
    _fig
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 5️⃣ 訓練：把 join 出來的特徵餵給模型

    現在手上有一份 point-in-time 正確的訓練集了，接下來就是老套路：切訓練／測試、訓練、記到 MLflow。

    切法用**時間切**而不是隨機切：測試集是「比較晚發生的事件」。
    隨機切在時間序列資料上本身就是一種洩漏——你會用未來的事件訓練、預測過去的事件。

    為了讓你看到差別，這裡訓練**兩個**模型，用完全一樣的事件、完全一樣的演算法，只差在特徵怎麼來：

    - `pit`：Feast 的 point-in-time join（正確）
    - `leaky`：第 1 節那行「拿最新一筆」的 join（洩漏）

    兩個都在**同一批測試事件、同一份 point-in-time 特徵**上評估——因為那才是上線時的樣子。
    """
    )
    return


@app.cell
def _(
    FEATURE_COLS,
    LogisticRegression,
    RandomForestClassifier,
    WORK,
    accuracy_score,
    mlflow,
    naive_join,
    roc_auc_score,
    snap_ts,
    training_df,
):
    mlflow.set_tracking_uri(f"sqlite:///{WORK / 'mlflow.db'}")
    if not mlflow.get_experiment_by_name("feature-store"):
        mlflow.create_experiment("feature-store", artifact_location=str(WORK / "artifacts"))
    mlflow.set_experiment("feature-store")

    # 洩漏版：同一批事件，但特徵換成「每位客戶最新的一筆」
    _keys = ["customer_id", "event_timestamp"]
    _pit = training_df.set_index(_keys).sort_index()
    _leak = naive_join.set_index(_keys).sort_index().loc[_pit.index]

    SPLIT_TS = snap_ts(6)

    def _split(df):
        _tr = df[df.index.get_level_values("event_timestamp") < SPLIT_TS]
        _te = df[df.index.get_level_values("event_timestamp") >= SPLIT_TS]
        return _tr[FEATURE_COLS], _tr.churn, _te[FEATURE_COLS], _te.churn

    Xtr, ytr, Xte, yte = _split(_pit)
    Xtr_leak, ytr_leak, _, _ = _split(_leak)

    SCORES = {}
    for _name, _make in [
        ("logreg", lambda: LogisticRegression(max_iter=1000)),
        ("rf", lambda: RandomForestClassifier(n_estimators=100, max_depth=4, random_state=0)),
    ]:
        for _kind, _Xtr, _ytr in [("pit", Xtr, ytr), ("leaky", Xtr_leak, ytr_leak)]:
            _m = _make().fit(_Xtr, _ytr)
            _proba = _m.predict_proba(Xte)[:, 1]  # ← 測試集一律用 point-in-time 特徵
            SCORES[(_name, _kind)] = {
                "auc": roc_auc_score(yte, _proba),
                "acc": accuracy_score(yte, _m.predict(Xte)),
            }
            with mlflow.start_run(run_name=f"{_name}-{_kind}"):
                mlflow.log_params({"model": _name, "features": _kind, "n_train": len(_Xtr), "n_test": len(Xte)})
                mlflow.log_metrics(SCORES[(_name, _kind)])
                if _kind == "pit":
                    mlflow.sklearn.log_model(_m, name=f"churn-{_name}", input_example=_Xtr.head(2))
            if _name == "logreg" and _kind == "pit":
                churn_model = _m

    N_TRAIN, N_TEST = len(Xtr), len(Xte)
    return N_TEST, N_TRAIN, SCORES, SPLIT_TS, Xte, churn_model, yte


@app.cell(hide_code=True)
def _(N_TEST, N_TRAIN, SCORES, mo, yte):
    _rows = "\n".join(
        f"    | {_n} | {SCORES[(_n, 'pit')]['auc']:.4f} | {SCORES[(_n, 'leaky')]['auc']:.4f} | "
        f"{SCORES[(_n, 'pit')]['auc'] - SCORES[(_n, 'leaky')]['auc']:+.4f} |"
        for _n in ("logreg", "rf")
    )
    mo.md(
        f"""
    訓練集 **{N_TRAIN}** 筆、測試集 **{N_TEST}** 筆（測試集流失率 {yte.mean():.1%}）。
    兩份特徵、兩個演算法，四次訓練都記進了 MLflow：

    | 演算法 | point-in-time 特徵 AUC | 洩漏特徵 AUC | 差 |
    |---|---|---|---|
{_rows}

    **差距沒有你想像的大——這正是重點。**

    洩漏不會讓模型當場崩潰，它讓模型學到一個「上線時不存在的世界」，然後你會發現：
    離線評估的每一個數字看起來都很正常，沒有任何指標會跳出來說「你的特徵是未來來的」。
    你只會在上線之後看到模型比預期差一點，然後開始調參數、換演算法、加特徵——
    而真正的問題在 join 的那一行。

    （順帶一提：本課的洩漏是「拿到同一位客戶幾天後的行為」，屬於比較溫和的一種。
    真正致命的版本是**特徵欄位本身就是答案的結果**——例如拿「客訴結案原因」去預測客訴會不會發生；
    那種洩漏會讓離線分數高到不真實，反而比較容易被發現。**越像這一課這種、越難發現。**）
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 6️⃣ 上線：`materialize` ＋ `get_online_features`

    模型訓練好了，現在客服系統打電話來：「客戶 7 正在線上，他會不會流失？」
    你有 **50 毫秒**可以回答。

    那張 parquet 是查不動的——它為「查得到過去任何一刻」而生，不是為了毫秒級查詢。
    所以特徵倉有第二個倉庫：**online store**，裡面只放**每位客戶最新的一筆**。

    `materialize` 就是把資料從 offline 推到 online 的動作：

    - `materialize(start_date, end_date)`：算某一段區間，全量重建時用。
    - `materialize_incremental(end_date)`：**從上次做到哪裡接著做**（Feast 自己記水位）。
      這是排程每天要跑的那一行。

    這件事**必須排程**——特徵倉不會自己更新。接上第 4 課學的 schedule：
    每天批次算完快照之後，跟著跑一次 `materialize_incremental`。
    沒排程的下場是 online store 停在某一天，線上服務拿著三個月前的特徵繼續回答，而且不會報錯。
    """
    )
    return


@app.cell
def _(NOW, WORK, contextlib, dt, io, re, sqlite3, store, ttl_probe):
    _buf = io.StringIO()
    with contextlib.redirect_stdout(_buf):
        store.materialize_incremental(end_date=NOW + dt.timedelta(minutes=1))
    MAT_LOG = re.sub(r"\x1b\[[0-9;]*m", "", _buf.getvalue()).strip()  # 把終端機色碼拿掉

    _db = WORK / "data" / "online.db"
    ONLINE_BYTES = _db.stat().st_size
    _conn = sqlite3.connect(_db)
    ONLINE_TABLES = [_r[0] for _r in _conn.execute("select name from sqlite_master where type='table'")]
    ONLINE_ROWS = next(iter(_conn.execute(f"select count(*) from {ONLINE_TABLES[0]}")))[0]
    _conn.close()
    materialized = True
    _ = ttl_probe
    return MAT_LOG, ONLINE_BYTES, ONLINE_ROWS, ONLINE_TABLES, materialized


@app.cell(hide_code=True)
def _(MAT_LOG, ONLINE_BYTES, ONLINE_ROWS, ONLINE_TABLES, mo):
    mo.md(
        f"""
    ```
    {MAT_LOG}
    ```

    online store（`online.db`）現在 **{ONLINE_BYTES:,} bytes**，裡面只有一張表 `{ONLINE_TABLES[0]}`
    （命名規則是 `專案名_特徵視圖名`），共 **{ONLINE_ROWS} 列** ＝ 20 位客戶 × 3 個特徵。

    對照一下：offline 那張 parquet 有 192 列 × 3 個特徵的**完整歷史**；
    online 只留每位客戶的**最新一筆**。這就是兩個倉庫存在的理由——
    它們存的是同一份定義下的同一種特徵，但為完全不同的查詢模式而生。
    """
    )
    return


@app.cell
def _(FEATURE_REFS, materialized, store, time):
    # 第一次呼叫要開連線、載 registry，比較慢；之後才是真正的線上延遲
    _t0 = time.perf_counter()
    online_first = store.get_online_features(features=FEATURE_REFS, entity_rows=[{"customer_id": 7}]).to_dict()
    COLD_MS = (time.perf_counter() - _t0) * 1000

    _lat = []
    for _cid in range(1, 21):
        _t = time.perf_counter()
        store.get_online_features(features=FEATURE_REFS, entity_rows=[{"customer_id": _cid}])
        _lat.append((time.perf_counter() - _t) * 1000)
    _lat.sort()
    LAT = (_lat[0], _lat[len(_lat) // 2], _lat[-1])

    _t = time.perf_counter()
    online_all = store.get_online_features(
        features=FEATURE_REFS, entity_rows=[{"customer_id": _c} for _c in range(1, 21)]
    ).to_dict()
    BATCH_MS = (time.perf_counter() - _t) * 1000

    # 查一個不存在的客戶會發生什麼事？
    online_missing = store.get_online_features(features=FEATURE_REFS, entity_rows=[{"customer_id": 999}]).to_dict()
    _ = materialized
    return BATCH_MS, COLD_MS, LAT, online_all, online_first, online_missing


@app.cell(hide_code=True)
def _(BATCH_MS, COLD_MS, LAT, mo, online_first, online_missing):
    mo.md(
        f"""
    客戶 7 的線上特徵：`{online_first}`

    | 量測 | 毫秒 |
    |---|---|
    | 第一次呼叫（含開連線） | {COLD_MS:.1f} |
    | 之後單筆（20 次）最快／中位／最慢 | {LAT[0]:.2f} ／ {LAT[1]:.2f} ／ {LAT[2]:.2f} |
    | 一次拿 20 位客戶 | {BATCH_MS:.2f} |

    熱起來之後每次不到一毫秒——這就是 online store 的意義。
    （這是 SQLite 跑在本機的數字，你的機器會不一樣；正式環境換成 Redis 之後多的是網路來回的時間，
    重點是**數量級**：offline 查詢是幾十毫秒起跳，online 是**次毫秒**。）

    再看一個一定要知道的行為——查一個 online store 裡沒有的客戶：

    ```
    {online_missing}
    ```

    **不會報錯，回給你 `None`。** 這在正式環境是最常見的線上事故之一：
    新註冊的客戶還沒被 materialize 進來、或是某位客戶的上游斷線超過 ttl，
    你的服務就會拿到一排 `None` 然後在下一行 `predict()` 炸掉——
    或更糟，被某個 `fillna(0)` 默默補成 0，模型照樣給出一個看起來很正常的分數。
    **線上取完特徵一定要檢查 `None`，並且決定好「拿不到特徵時要回什麼」。**
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ### 兩個承諾的驗收

    現在把兩件事一次做完：**用線上特徵做推論**，並且**證明線上與離線拿到的是同一份東西**。

    第二件事就是特徵倉存在的全部理由。做法是拿同一批客戶、同一個時間點（現在），
    分別走 `get_historical_features`（訓練那條路）與 `get_online_features`（上線那條路），
    然後比對每一個值。
    """
    )
    return


@app.cell
def _(FEATURE_COLS, FEATURE_REFS, NOW, churn_model, materialized, online_all, pd, store):
    # 用線上特徵做推論：欄位順序必須跟訓練時一致
    _online_df = pd.DataFrame(online_all)[["customer_id", *FEATURE_COLS]]
    _proba = churn_model.predict_proba(_online_df[FEATURE_COLS])[:, 1]
    online_scores = _online_df.assign(churn_prob=_proba.round(4)).sort_values("churn_prob", ascending=False)

    # 同一批客戶、同一個時刻，走離線那條路
    _entity_now = pd.DataFrame({"customer_id": list(range(1, 21)), "event_timestamp": [NOW] * 20})
    _offline_now = store.get_historical_features(entity_df=_entity_now, features=FEATURE_REFS).to_df()
    _cmp = _offline_now.merge(pd.DataFrame(online_all), on="customer_id", suffixes=("_offline", "_online"))
    AGREE = {_c: bool((_cmp[f"{_c}_offline"] == _cmp[f"{_c}_online"]).all()) for _c in FEATURE_COLS}
    N_CMP = len(_cmp)
    _ = materialized
    return AGREE, N_CMP, online_scores


@app.cell(hide_code=True)
def _(AGREE, N_CMP, mo, online_scores):
    mo.md(
        f"""
    最該打電話的五位客戶（用**線上特徵**即時算出來的流失機率）：

    {online_scores.head(5).to_markdown(index=False)}

    **離線 vs 線上對答案**（{N_CMP} 位客戶、同一個時刻）：`{AGREE}`

    三個特徵**每一位客戶都完全相同**。這不是碰巧——兩條路讀的是同一份 registry 定義、
    同一個 `customer_daily`，只是一個從 parquet 撈歷史、一個從 SQLite 撈最新值。

    這就是「同一份定義」的具體樣子：你沒有寫第二份特徵計算程式，
    所以**根本沒有機會**寫出跟訓練不一致的版本。
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 7️⃣ 特徵服務與版本：一個模型該吃哪幾個特徵？

    上線之後你會遇到這個問題：v1 模型吃 3 個特徵，v2 加了兩個新特徵。
    線上服務怎麼知道現在該拿哪幾個？把特徵清單寫死在服務程式裡，換模型就要改程式、重新部署。

    **`FeatureService` 就是把「一組特徵」取個名字**，讓模型跟特徵清單一起版本化：
    服務程式只認得 `store.get_feature_service("churn_v1")`，換模型＝換那個名字。
    """
    )
    return


@app.cell
def _(FeatureService, customer, customer_daily, materialized, store):
    churn_v1 = FeatureService(
        name="churn_v1",
        features=[customer_daily[["n_orders_30d", "return_rate"]]],  # 只挑兩個
        description="第一版流失模型用的特徵",
    )
    churn_v2 = FeatureService(name="churn_v2", features=[customer_daily])  # 整組都要

    store.apply([customer, customer_daily, churn_v1, churn_v2])
    _svc = store.get_feature_service("churn_v1")
    SVC_NAMES = [_s.name for _s in store.list_feature_services()]
    SVC_FEATURES = [(_p.name, [_f.name for _f in _p.features]) for _p in _svc.feature_view_projections]
    SVC_ONLINE = store.get_online_features(features=_svc, entity_rows=[{"customer_id": 7}]).to_dict()
    svc_applied = True
    _ = materialized
    return SVC_FEATURES, SVC_NAMES, SVC_ONLINE, svc_applied


@app.cell(hide_code=True)
def _(SVC_FEATURES, SVC_NAMES, SVC_ONLINE, mo):
    mo.md(
        f"""
    registry 裡的 feature services：`{SVC_NAMES}`，
    其中 `churn_v1` 綁的是 `{SVC_FEATURES}`。

    `get_online_features` 與 `get_historical_features` 都可以直接吃一個 feature service
    （把 `features=[...]` 換成 `features=store.get_feature_service("churn_v1")`）：

    ```
    {SVC_ONLINE}
    ```

    回來的正好是那兩個特徵。**線上服務的程式碼裡從此不需要出現任何特徵名稱**——
    只需要知道它服務的是哪個模型版本。
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ### 加一個特徵欄位：改定義 → `apply` → **重新 materialize**

    現在上游多算了一個「平均客單價」`avg_amount`。三個步驟：
    parquet 多一欄 → FeatureView 的 `schema` 多一個 `Field` → 再 `apply` 一次。

    但這裡藏著一個會讓你 debug 一整個下午的坑，下面刻意示範一次。
    """
    )
    return


@app.cell
def _(
    Field,
    Float32,
    Int64,
    NOW,
    PARQUET,
    WORK,
    contextlib,
    customer,
    daily_source,
    dt,
    io,
    snap_ts,
    snapshots,
    store,
    svc_applied,
    FeatureView,
):
    _s2 = snapshots.copy()
    _s2["avg_amount"] = (_s2.total_30d / _s2.n_orders_30d.clip(lower=1)).astype("float32")
    _s2.to_parquet(PARQUET)  # 來源多了一欄

    customer_daily_v2 = FeatureView(
        name="customer_daily",  # 同一個名字＝改定義，不是新開一個
        entities=[customer],
        ttl=dt.timedelta(days=3),
        schema=[
            Field(name="n_orders_30d", dtype=Int64),
            Field(name="total_30d", dtype=Float32),
            Field(name="return_rate", dtype=Float32),
            Field(name="avg_amount", dtype=Float32),  # 新的
        ],
        source=daily_source,
        online=True,
    )
    store.apply([customer, customer_daily_v2])

    # 離線立刻就有（它每次都重讀來源）
    NEW_OFFLINE = store.get_historical_features(
        entity_df=snapshots[["customer_id", "event_timestamp"]].tail(3),
        features=["customer_daily:avg_amount"],
    ).to_df()

    # 線上呢？先照平常那樣 materialize_incremental
    with contextlib.redirect_stdout(io.StringIO()):
        store.materialize_incremental(end_date=NOW + dt.timedelta(minutes=1))
    NEW_ONLINE_INC = store.get_online_features(
        features=["customer_daily:avg_amount"], entity_rows=[{"customer_id": 7}]
    ).to_dict()

    # 再全量重做一次
    with contextlib.redirect_stdout(io.StringIO()):
        store.materialize(start_date=snap_ts(0) - dt.timedelta(days=1), end_date=NOW + dt.timedelta(minutes=1))
    NEW_ONLINE_FULL = store.get_online_features(
        features=["customer_daily:avg_amount"], entity_rows=[{"customer_id": 7}]
    ).to_dict()

    REG_BYTES = (WORK / "data" / "registry.db").stat().st_size
    v2_applied = True
    _ = svc_applied
    return (
        NEW_OFFLINE,
        NEW_ONLINE_FULL,
        NEW_ONLINE_INC,
        REG_BYTES,
        customer_daily_v2,
        v2_applied,
    )


@app.cell(hide_code=True)
def _(NEW_OFFLINE, NEW_ONLINE_FULL, NEW_ONLINE_INC, REG_BYTES, mo):
    mo.md(
        f"""
    **離線**（重讀 parquet）馬上就有新欄位：

    {NEW_OFFLINE.to_markdown(index=False)}

    **線上**跑完 `materialize_incremental` 之後：

    ```
    {NEW_ONLINE_INC}
    ```

    `None`。不是壞掉——`materialize_incremental` 的意思是「從上次的水位接著做」，
    而上次已經做到「現在」了，所以它認為沒有新資料要推，**新欄位一列都沒補**。
    唯一的解法是全量重做：

    ```
    {NEW_ONLINE_FULL}
    ```

    **加了特徵欄位之後，一定要跑一次全量 `materialize`。**
    這個坑之所以難，是因為它完全沉默：離線測試都對、`apply` 沒報錯、
    `materialize_incremental` 也「成功」了，只有線上服務拿到一排 `None`。

    registry 現在是 **{REG_BYTES} bytes**（一開始只有一個 feature view 時是 1 千多）。
    它長大的原因是多了兩個 feature service 與一個欄位——**它存的一直都只有定義**。
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ### On-demand 特徵：有些東西不該存，該現算

    `avg_amount` 其實有點浪費——它是 `total_30d / n_orders_30d` 算出來的，
    存一份等於多一個「可能跟另外兩欄不同步」的地方。

    這種「從別的特徵推導出來、而且很便宜」的東西，Feast 有一個專門的機制：
    **on-demand feature view**——定義一個函式，查詢時**當場算**，離線與線上都會自動套用同一個函式。
    這是「同一份定義」原則的極致：連轉換邏輯都只有一份。
    """
    )
    return


@app.cell
def _(Field, Float64, customer, customer_daily_v2, pd, store, v2_applied):
    from feast.on_demand_feature_view import on_demand_feature_view

    @on_demand_feature_view(
        sources=[customer_daily_v2],
        schema=[Field(name="amount_per_order", dtype=Float64)],
    )
    def order_ratio(inputs: pd.DataFrame) -> pd.DataFrame:
        """查詢時當場算：平均每張訂單的金額。"""
        _out = pd.DataFrame()
        _out["amount_per_order"] = inputs["total_30d"] / inputs["n_orders_30d"].clip(lower=1)
        return _out

    store.apply([customer, customer_daily_v2, order_ratio])
    ODFV_NAMES = [_v.name for _v in store.list_on_demand_feature_views()]
    ODFV_ONLINE = store.get_online_features(
        features=["customer_daily:total_30d", "customer_daily:n_orders_30d", "order_ratio:amount_per_order"],
        entity_rows=[{"customer_id": 7}],
    ).to_dict()
    odfv_applied = True
    return ODFV_NAMES, ODFV_ONLINE, odfv_applied


@app.cell(hide_code=True)
def _(ODFV_NAMES, ODFV_ONLINE, mo):
    mo.md(
        f"""
    registry 裡的 on-demand feature views：`{ODFV_NAMES}`

    ```
    {ODFV_ONLINE}
    ```

    `amount_per_order` 沒有存在任何地方，是查詢的當下用另外兩個特徵算出來的。

    兩個實測踩到的細節：

    - **宣告的型別必須跟函式實際回傳的一致**。`total / n_orders` 在 pandas 是 `float64`，
      你如果宣告 `Float32`，`apply` 會直接擋下來（錯誤原文在下一節）。
    - 這個函式會被序列化存進 registry（所以別人不用拿到你的原始碼也能執行它）——
      也因此**函式裡不要引用外部變數**，只用 `inputs` 的欄位。

    什麼時候用 on-demand、什麼時候老老實實存一欄？判準是**算它要多久**：
    四則運算、取 log、算比值 → on-demand；要掃三個月的訂單表 → 乖乖批次算好存起來。
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 8️⃣ 互動：時間旅行，看 point-in-time 拿到哪一筆

    選一位客戶、把事件時間拉到某一天，看三件事：

    - **point-in-time 拿到的那一筆**（訓練時模型會看到的）
    - **online store 的最新值**（今天上線服務會拿到的）
    - 兩者差多少——**差距就是那行「拿最新一筆」的 join 會塞給模型的未來資訊**

    客戶 7、13、19 是上游斷線的那三位，把時間拉到他們斷線的那幾天，
    就會看到 point-in-time 直接查不到（超過 ttl）。
    """
    )
    return


@app.cell
def _(mo):
    ui_customer = mo.ui.dropdown(
        options={f"客戶 {_c}": _c for _c in range(1, 21)}, value="客戶 7", label="選一位客戶"
    )
    ui_day = mo.ui.slider(1, 9, value=6, label="事件發生在第幾天（9＝現在）", show_value=True)
    mo.hstack([ui_customer, ui_day], wrap=True, justify="start", gap=1.5)
    return ui_customer, ui_day


@app.cell(hide_code=True)
def _(
    FEATURE_COLS,
    FEATURE_REFS,
    NOW,
    dt,
    mo,
    odfv_applied,
    pd,
    snap_ts,
    store,
    ui_customer,
    ui_day,
):
    _cid = ui_customer.value
    _ts = min(snap_ts(ui_day.value) + dt.timedelta(hours=12), NOW)
    _pit = store.get_historical_features(
        entity_df=pd.DataFrame({"customer_id": [_cid], "event_timestamp": [_ts]}), features=FEATURE_REFS
    ).to_df()
    _now = store.get_online_features(features=FEATURE_REFS, entity_rows=[{"customer_id": _cid}]).to_dict()

    _now_flat = {_k: _v[0] for _k, _v in _now.items()}
    if len(_pit) == 0:
        _body = f"""
    ### 客戶 {_cid}，事件時間 `{_ts:%m-%d %H:%M}`

    **point-in-time 查不到特徵**——這位客戶最近的一筆快照已經超過 `ttl`（3 天）了。
    Feast 沒有給你 NaN，而是把這一列從結果裡整列拿掉：進去 1 列，回來 {len(_pit)} 列。

    上線那邊倒是照樣有值（online store 存的是**最新**的一筆，跟事件時間無關）：
    `{_now_flat}`

    這正是為什麼「拿最新一筆」的 join 特別危險：**它永遠給得出答案。**
        """
    else:
        _row = _pit.iloc[0]
        _lines = "\n".join(
            f"    | `{_c}` | {_row[_c]:,.4g} | {_now[_c][0]:,.4g} | {(_now[_c][0] - _row[_c]) / max(abs(_row[_c]), 1e-9):+.0%} |"
            for _c in FEATURE_COLS
        )
        _body = f"""
    ### 客戶 {_cid}，事件時間 `{_ts:%m-%d %H:%M}`

    | 特徵 | point-in-time（訓練時看得到） | online 最新值（今天） | 差 |
    |---|---|---|---|
{_lines}

    「online 最新值」那一欄，就是「拿最新一筆」的 join 會塞進訓練資料的值。
    把滑桿往左拉（事件越早），兩欄的差距就越大——**離事件越遠的快照，洩漏得越多**。
        """
    _ = odfv_applied
    mo.md(_body)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 9️⃣ 錯誤原文速查

    下面每一則都是實測撞出來的原文（Feast 0.66）。看過一次，之後在正式環境撞到就能一秒定位。
    完整的重現腳本在課程 repo 的 `content/mlops/_spikes/spike_feast_errors.py`。

    | 你做了什麼 | Feast 說什麼 |
    |---|---|
    | 還沒 `apply` 就查 | `FeatureViewNotFoundException: Feature view customer_daily does not exist in project churn` |
    | feature view 名字打錯 | 同上，把名字換成你打錯的那個 |
    | 特徵名打錯 `customer_daily:nope` | `KeyError: 'Feature nope not found in projection customer_daily'` |
    | 忘了冒號，只寫欄名 | `ValueError: Invalid feature reference 'n_orders_30d'. Expected format: '<feature_view>:<feature>'…` |
    | entity_df 沒有 `event_timestamp` 欄 | `ValueError: Please provide an entity_df with a column named event_timestamp representing the time of events.` |
    | join key 欄名打錯（`cust_id`） | `KeyError: 'customer_id'`（pandas 的 merge 直接爆） |
    | `entity_rows` 的 key 打錯 | `KeyError: "Missing join key values for keys: ['customer_id']…"` |
    | `feature_store.yaml` 少了 `project` | `FeastConfigError: 1 validation error for RepoConfig / project / Field required` |
    | 資料夾裡沒有 `feature_store.yaml` | `FileNotFoundError: [Errno 2] No such file or directory: '…/feature_store.yaml'` |
    | on-demand 宣告 `Float32` 但回傳 `float64` | `SpecifiedFeaturesNotPresentError: Explicitly specified features […FLOAT32…] not found in inferred list of features […FLOAT64…]` |
    | `python -m feast apply` | `No module named feast.__main__; 'feast' is a package and cannot be directly executed` |

    另外三個**不會報錯**、但更該記住的行為（沉默才是最貴的）：

    | 你做了什麼 | 實際發生的事 |
    |---|---|
    | 還沒 `materialize` 就取線上特徵 | 每個特徵回 `None`，**不報錯** |
    | 查一個不存在的客戶 | 每個特徵回 `None`，**不報錯** |
    | 時間戳沒有時區 | 被當成 UTC，**不報錯**——資料是台北時間的話整批差 8 小時 |
    | 事件時間超過 `ttl` | 那一列從結果裡**整列消失**，不是 NaN |
    | 加欄位後只跑 `materialize_incremental` | 新欄位在線上一直是 `None`，要全量 `materialize` 才補得上 |
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 🏆 延伸挑戰

    1. **LEVEL 1**：再加一個特徵欄位 `orders_per_day`（`n_orders_30d / 30`），
       走完完整的四步：改來源 parquet → `schema` 加 `Field` → `apply` → **全量** `materialize`。
       驗收：`get_online_features` 拿得到值而不是 `None`。
    2. **LEVEL 2**：把 `customer_daily` 的 `ttl` 改成 1 天再 `apply`，重跑
       `get_historical_features`，數數看訓練集少了幾筆，並找出「是哪些客戶的哪些事件」被吃掉。
       想一想：如果你的批次工作偶爾會晚兩小時跑完，`ttl` 該給多少？
    3. **LEVEL 3**：做一個「請求當下才知道的特徵」——例如購物車金額。
       用 `RequestSource` ＋ on-demand feature view 算出「這次購物車金額 ÷ 這位客戶的平均客單價」，
       線上查詢時把 `cart_amount` 一起放進 `entity_rows`。
       這是特徵倉最實用的模式之一：**存起來的歷史特徵 × 這一秒才發生的事**。

    先自己試，卡住再展開下面的參考解答。

    帶得走：下載本檔後 `uvx marimo edit --sandbox feature-store_ext.py`
    就能在自己電腦繼續玩（依賴會自動安裝）。
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.accordion(
        {
            "💡 LEVEL 1 參考解答": mo.md(
                r"""
    四步一步都不能少，**第四步是最多人漏掉的那一步**：

    ```python
    # 1. 來源多一欄
    s3 = snapshots.copy()
    s3["orders_per_day"] = (s3.n_orders_30d / 30).astype("float32")
    s3["avg_amount"] = (s3.total_30d / s3.n_orders_30d.clip(lower=1)).astype("float32")
    s3.to_parquet(PARQUET)

    # 2+3. schema 加一個 Field，再 apply（名字不變＝改定義）
    fv3 = FeatureView(
        name="customer_daily", entities=[customer], ttl=dt.timedelta(days=3),
        schema=[Field(name="n_orders_30d", dtype=Int64),
                Field(name="total_30d", dtype=Float32),
                Field(name="return_rate", dtype=Float32),
                Field(name="avg_amount", dtype=Float32),
                Field(name="orders_per_day", dtype=Float32)],
        source=daily_source, online=True)
    store.apply([customer, fv3])

    # 4. 全量 materialize（只跑 incremental 的話線上會是 None）
    store.materialize(start_date=snap_ts(0) - dt.timedelta(days=1),
                      end_date=NOW + dt.timedelta(minutes=1))

    store.get_online_features(features=["customer_daily:orders_per_day"],
                              entity_rows=[{"customer_id": 7}]).to_dict()
    ```

    你應該看到 `{'customer_id': [7], 'orders_per_day': [0.1]}` 這樣的值（客戶 7 最新是 3 筆訂單 ÷ 30）。
    如果拿到 `None`，回去看第 4 步是不是只跑了 `materialize_incremental`。
    """
            ),
            "💡 LEVEL 2 參考解答": mo.md(
                r"""
    ```python
    fv_short = FeatureView(
        name="customer_daily", entities=[customer],
        ttl=dt.timedelta(days=1),          # ← 只改這一行
        schema=[Field(name="n_orders_30d", dtype=Int64),
                Field(name="total_30d", dtype=Float32),
                Field(name="return_rate", dtype=Float32)],
        source=daily_source, online=True)
    store.apply([customer, fv_short])

    short = store.get_historical_features(entity_df=events, features=FEATURE_REFS).to_df()
    print(len(events), "->", len(short))

    # 是哪些事件被吃掉了？
    got = set(zip(short.customer_id, short.event_timestamp))
    lost = [(r.customer_id, r.event_timestamp) for r in events.itertuples()
            if (r.customer_id, r.event_timestamp) not in got]
    print(sorted({c for c, _ in lost}))
    ```

    實測：`ttl=3 天` 時 360 筆事件回來 356 筆；改成 **`ttl=1 天` 只剩 341 筆**（再少 15 筆）。
    被吃掉的全部集中在**上游斷線的那三位客戶**（7、13、19）——因為只有他們的快照會隔超過一天。

    至於「批次偶爾晚兩小時」該給多少：`ttl` 要蓋得住**更新週期 ＋ 最壞的延遲**。
    每天更新、最壞晚 2 小時 → 26 小時就夠，但留一點餘裕給補跑，
    所以 2–3 天是個合理的起點。給 1 天等於「批次只要晚一分鐘，全部特徵作廢」。
    """
            ),
            "💡 LEVEL 3 提示": mo.md(
                r"""
    關鍵字是 **`RequestSource`**：它宣告「這些欄位不在任何一張表裡，是呼叫的當下才傳進來的」。

    ```python
    from feast import RequestSource
    from feast.types import Float64

    cart = RequestSource(name="cart", schema=[Field(name="cart_amount", dtype=Float64)])

    @on_demand_feature_view(sources=[customer_daily_v2, cart],
                            schema=[Field(name="cart_vs_avg", dtype=Float64)])
    def cart_check(inputs: pd.DataFrame) -> pd.DataFrame:
        out = pd.DataFrame()
        out["cart_vs_avg"] = inputs["cart_amount"] / (
            inputs["total_30d"] / inputs["n_orders_30d"].clip(lower=1))
        return out

    store.apply([customer, customer_daily_v2, cart_check])
    store.get_online_features(
        features=["customer_daily:total_30d", "cart_check:cart_vs_avg"],
        entity_rows=[{"customer_id": 7, "cart_amount": 1500.0}],   # ← 請求資料跟 entity 一起傳
    ).to_dict()
    ```

    **怎麼驗證自己做對了**：

    1. 手算一次。客戶 7 的線上特徵是 `total_30d / n_orders_30d`，
       拿 1500 除以它，應該跟 `cart_vs_avg` 一模一樣。
    2. 故意**不要**傳 `cart_amount`，你應該看到
       `RequestDataNotFoundInEntityRowsException: Required request data source features ['cart_amount']
       not found in the entity rows, but required by feature views`
       ——這個錯誤就是 Feast 在幫你把「線上服務忘了傳參數」變成一個明確的錯誤，
       而不是一個靜靜算錯的數字。
    3. 想想這對 skew 的意義：購物車金額這種「這一秒才存在」的東西**不可能**事先算好存起來，
       但它跟歷史特徵的組合方式仍然只有一份定義——這正是特徵倉真正的價值。
    """
            ),
        }
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ---

    ## 收尾：你其實只學了三個動作

    整堂課的 Feast 操作只有三個：

    | 動作 | 什麼時候做 | 誰在做 |
    |---|---|---|
    | `store.apply([...])` | 定義改了 | CI／資料工程師 |
    | `store.get_historical_features(...)` | 要訓練、要批次評分 | 訓練管線 |
    | `store.materialize_incremental(...)` ＋ `get_online_features(...)` | 每天排程 ＋ 每一次線上請求 | 排程／線上服務 |

    剩下的全是紀律：

    - 時間戳一律 **tz-aware**。
    - `get_historical_features` 之後**比對筆數**（ttl 會靜靜吃掉列）。
    - 線上取完特徵**檢查 `None`**，並想好拿不到時要回什麼。
    - 加欄位之後跑**全量** `materialize`。
    - 特徵定義進版控，跟模型程式碼放在一起——它跟模型一樣需要 code review。

    特徵倉不是一個很厲害的資料庫，它是一個**紀律的容器**：
    把「特徵怎麼算」這件事從三份不同的程式碼，收斂成一份有名字、有版本、兩邊共用的定義。
    """
    )
    return


if __name__ == "__main__":
    app.run()
