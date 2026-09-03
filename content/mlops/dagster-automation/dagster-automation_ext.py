# Dagster 自動化：誰來按下那個「執行」？（排程、感測器、分割、自動化條件、重試）
# 不需要 GPU——molab 免費 CPU 環境即可全程執行（全部在本機檔案系統，不連任何伺服器）。
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "marimo",
#     "dagster>=1.10",
#     "pandas",
#     "numpy",
#     "matplotlib",
#     "tabulate",
# ]
# ///
import marimo

__generated_with = "0.23.16"
app = marimo.App(width="medium", app_title="Dagster 自動化：排程、感測器、分割與自動化條件")


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    # ⚡ Dagster 自動化：誰來按下那個「執行」？

    ## 上一課的結尾，就是這一課的開頭

    上一課你學會了用 `@asset` 宣告資產、讓 Dagster 從依賴推出一張圖，然後——
    **你自己呼叫 `materialize()`**。那是手動按下執行。

    但真實世界不會有人每天凌晨 2 點坐在電腦前按按鈕，也不會有人盯著 SFTP 目錄看客戶的
    CSV 什麼時候到，更不會有人在上游資料表更新後記得去重算下游的 12 張特徵表。
    這一課回答被留下來的那個問題：**誰來按？什麼時候按？按下去要跑哪一段？失敗了誰重試？**

    ## Dagster 的三種答案（這堂課全部做過一次）

    | 觸發方式 | 一句話 | 典型情境 |
    |---|---|---|
    | **排程 schedule** | 時間到就跑 | 「每天凌晨 2 點重算特徵表」 |
    | **感測器 sensor** | 有事情發生才跑 | 「客戶把 CSV 丟進來就處理」 |
    | **自動化條件 AutomationCondition** | 資產自己說什麼時候該更新 | 「上游一更新我就跟著更新」 |

    前兩種都要先有一個 **job**（要一起跑的資產打包成一包）；第三種不用 job，
    條件寫在資產上。三種都由 Dagster 的 **daemon** 在背後定時評估——這一課我們不起 daemon，
    改用 `evaluate_tick()` 與 `evaluate_automation_conditions()`，**在 notebook 裡直接問它
    「這個時刻你會發出什麼？」**，看得比 UI 還清楚。

    ## 這份 notebook 帶你做完

    1. **資源與設定**：`ConfigurableResource`（環境）與 `dg.Config`（這一次執行的參數）
    2. **job**：`define_asset_job` 把資產打包成可以被觸發的單位
    3. **排程**：cron 語法、時區陷阱、`RunRequest`（附帶 run_key／run_config／tags）
    4. **分割 partitions**：把資產切成一天一片，補跑（backfill）缺掉的那幾天
    5. **感測器**：用 `cursor` 記住「看過什麼」，只對新東西發 run；資產感測器
    6. **宣告式自動化**：`AutomationCondition.eager()` / `.on_cron()`，資產自己決定
    7. **失敗處理**：`RetryPolicy` 重試、超過上限怎麼收場、失敗通知
    8. **收成 `Definitions` ＋ `dagster dev`**：daemon 在做什麼、UI 上怎麼開關

    全程在你自己的執行環境跑，**不連任何伺服器、不需要 GPU**：訂單是隨機產生的假資料，
    Dagster 的「帳本」是一個暫存資料夾。從第一格往下全部執行即可（首次安裝套件約 1–2 分鐘）。
    """
    )
    return


@app.cell
def _():
    import datetime as dt
    import json
    import logging
    import shutil
    import tempfile
    import warnings
    from pathlib import Path

    import dagster as dg
    import marimo as mo
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    import pandas as pd

    warnings.filterwarnings("ignore")
    logging.getLogger("dagster").setLevel(logging.WARNING)
    # Dagster 每一步都會印 DEBUG 日誌（dagster dev 的 UI 會幫你整理這些）；notebook 裡關小聲，只留警告與錯誤
    QUIET = {"loggers": {"console": {"config": {"log_level": "WARNING"}}}}

    WORK = Path(tempfile.gettempdir()) / "dagster-automation-lesson"
    shutil.rmtree(WORK, ignore_errors=True)          # 重跑時清乾淨，數字才一致
    for _sub in ("dev", "prod", "inbox", "play"):
        (WORK / _sub).mkdir(parents=True)
    # 這份 notebook 的「今天」：用 UTC 日期，跟 Dagster 分割（partition）的時間軸一致
    TODAY = dt.datetime.now(dt.UTC).date()
    return Path, QUIET, TODAY, WORK, dg, dt, json, mo, np, pd, plt


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 1️⃣ 資源與設定：把「環境」和「這一次的參數」抽出資產

    ### 為什麼需要

    資產函式裡遲早會出現這種東西：資料庫連線字串、S3 bucket 名稱、輸出目錄、API endpoint。
    如果直接寫死在函式裡，你會得到兩個麻煩：

    - **同一份程式在 dev 與 prod 要指到不同地方**——難道要準備兩份程式碼？
    - **每次執行想換一個參數**（今天只抓 100 筆試試）——難道要改程式碼再存檔？

    Dagster 把這兩件事分成兩個東西，名字很好記：

    | | 是什麼 | 什麼時候決定 | 怎麼寫 |
    |---|---|---|---|
    | **resource（資源）** | 外部世界的接點：連線、路徑、client | **部署時**（dev/prod 各一份） | `class X(dg.ConfigurableResource)` |
    | **config（設定）** | 這一次執行的參數 | **每次執行**（排程／感測器可以帶著給） | `class Y(dg.Config)` |

    資產怎麼拿到它們？跟上一課的上游資產一樣，**寫成參數就會被餵進來**：
    型別是 `dg.Config` 子類別的參數叫 `config`，型別是資源類別的參數名要對應資源的 key。

    ### 這一格在做什麼

    `FeatureStore` 是一個假的「特徵倉庫」——真實世界它可能是 S3、Postgres、Snowflake；
    這裡就是一個目錄，`write()` 把 DataFrame 存成 CSV。`IngestConfig` 則是這次要抓幾筆、
    用哪個隨機種子。`orders` 資產同時用到兩者，而它自己**完全不知道**資料會落在哪個目錄。
    """
    )
    return


@app.cell
def _(Path, dg, np, pd):
    class FeatureStore(dg.ConfigurableResource):
        """特徵倉庫（模擬）：真實世界可能是 S3／資料庫，這裡是一個目錄。"""

        root: str

        def write(self, name: str, df: pd.DataFrame) -> str:
            p = Path(self.root) / f"{name}.csv"
            p.parent.mkdir(parents=True, exist_ok=True)
            df.to_csv(p, index=False)
            return str(p)

    class IngestConfig(dg.Config):
        n_rows: int = 500        # 這一次要抓幾筆訂單
        seed: int = 0            # 這一次的隨機種子

    @dg.asset(description="從交易系統撈訂單（模擬）", group_name="raw")
    def orders(context: dg.AssetExecutionContext, config: IngestConfig, store: FeatureStore) -> pd.DataFrame:
        rng = np.random.default_rng(config.seed)
        df = pd.DataFrame({
            "order_id": range(config.n_rows),
            "amount": rng.gamma(2.0, 300, config.n_rows).round(0),
        })
        path = store.write("orders", df)                       # ← 存到哪由 resource 決定
        context.log.info(f"wrote {len(df)} rows to {path}")
        # 中繼資料的 key 別用 "path"：IO manager 會用同名 key 記它自己的存檔位置，你寫的會被蓋掉
        context.add_output_metadata({"rows": len(df), "csv": path, "total": float(df["amount"].sum())})
        return df

    return FeatureStore, IngestConfig, orders


@app.cell
def _(FeatureStore, QUIET, WORK, dg, mo, orders):
    _rows = []
    for _env, _n, _seed in [("dev", 20, 0), ("prod", 500, 7)]:
        _res = dg.materialize(
            [orders],
            resources={"store": FeatureStore(root=str(WORK / _env))},                      # 部署時決定
            run_config={**QUIET, "ops": {"orders": {"config": {"n_rows": _n, "seed": _seed}}}},   # 每次執行決定
        )
        _meta = {
            k: v.value
            for k, v in _res.get_asset_materialization_events()[0].step_materialization_data.materialization.metadata.items()
        }
        _rows.append({
            "resource": f"FeatureStore(root=…/{_env})",
            "config": f"n_rows={_n}, seed={_seed}",
            "rows": _meta["rows"],
            "total": round(_meta["total"]),
            "csv 落點": _meta["csv"].replace(str(WORK), "…"),
        })
    env_rows = _rows
    mo.vstack([
        mo.md(
            "同一個 `orders` 函式跑兩次：**程式碼一個字都沒改**，換的只是外面給的資源與設定——"
            "第一次寫進 dev 目錄抓 20 筆，第二次寫進 prod 目錄抓 500 筆。"
        ),
        mo.ui.table(env_rows, selection=None),
        mo.md(
            "`run_config` 的形狀值得記一下：`{\"ops\": {\"<資產名>\": {\"config\": {…}}}}`。"
            "等一下排程與感測器要「帶著參數觸發」，帶的就是這個字典——"
            "**它們不是呼叫你的函式，是遞一張寫好參數的單子給 Dagster**。"
        ),
    ])
    return (env_rows,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 2️⃣ job：把「要一起跑的資產」打包成可以被觸發的單位

    排程與感測器不會說「請實體化 `orders` 和 `orders_report`」，它們說的是
    **「請跑 `nightly_job`」**。job 就是這層包裝：一個名字 ＋ 一組資產選擇（selection）。

    ```python
    nightly_job = dg.define_asset_job("nightly_job", selection=dg.AssetSelection.assets("orders").downstream())
    ```

    `AssetSelection` 是一套小小的選取語法，常用的幾種：

    | 寫法 | 選到誰 |
    |---|---|
    | `selection=[orders, orders_report]` | 就這兩個 |
    | `AssetSelection.assets("orders").downstream()` | `orders` 以及它下游的全部 |
    | `AssetSelection.groups("features")` | 某個 group 的全部 |
    | `selection="*"`（預設） | 全部資產 |

    好處是**選擇會自己長大**：之後新增的下游資產只要接在 `orders` 後面，
    半夜那一跑就自動包含它，你不用回頭改排程。

    下面順手把 `orders_report` 加進來（吃 `orders` 的下游資產），
    再用 `Definitions.resolve_job_def(...).execute_in_process(...)` 真的把 job 跑一次——
    這正是排程與感測器發出 `RunRequest` 之後，Dagster 在背後做的事。
    """
    )
    return


@app.cell
def _(dg, pd):
    @dg.asset(group_name="report", description="今天這批訂單的摘要")
    def orders_report(context: dg.AssetExecutionContext, orders: pd.DataFrame) -> dg.MaterializeResult:
        big = int((orders["amount"] > 1000).sum())
        context.log.info(f"{len(orders)} orders, {big} big ones")
        return dg.MaterializeResult(
            metadata={"orders": len(orders), "big_orders": big, "total": float(orders["amount"].sum())}
        )

    return (orders_report,)


@app.cell
def _(FeatureStore, QUIET, WORK, dg, mo, orders, orders_report):
    nightly_job = dg.define_asset_job(
        "nightly_job",
        selection=dg.AssetSelection.assets("orders").downstream(),      # orders ＋ 它的下游
    )
    defs_jobs = dg.Definitions(
        assets=[orders, orders_report],
        jobs=[nightly_job],
        resources={"store": FeatureStore(root=str(WORK / "prod"))},
    )
    _res = defs_jobs.resolve_job_def("nightly_job").execute_in_process(
        run_config={**QUIET, "ops": {"orders": {"config": {"n_rows": 120, "seed": 3}}}},
    )
    job_assets = [ev.asset_key.to_user_string() for ev in _res.get_asset_materialization_events()]
    mo.md(
        f"""
    `nightly_job` 跑起來了：success = **{_res.success}**，這一跑實體化了 `{job_assets}`——
    `orders_report` 是被 `.downstream()` 一起選進來的，我們沒有在 job 裡點過它的名字。

    小提醒：`Definitions` 是「這個專案有哪些東西」的目錄。job 要能被解析出來，它用到的資產與
    **資源都必須在同一份 `Definitions` 裡**——少給 `store`，Dagster 會直接說
    `resource with key 'store' required by op 'orders' was not provided`，而不是等到跑一半才炸。
    """
    )
    return defs_jobs, job_assets, nightly_job


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 3️⃣ 排程 schedule：時間到就跑

    ### cron 五個欄位

    Dagster 的排程用標準 cron 字串，五個欄位由左到右是**分 時 日 月 週**：

    | cron | 意思 |
    |---|---|
    | `0 2 * * *` | 每天 02:00 |
    | `*/15 * * * *` | 每 15 分鐘 |
    | `30 8 * * 1-5` | 平日（週一到週五）08:30 |
    | `0 3 * * 1` | 每週一 03:00 |
    | `0 0 1 * *` | 每月 1 號 00:00 |

    寫錯不會安靜地失敗：Dagster 在**定義的當下**就檢查（等一下實測給你看）。

    ### 那個一定要踩一次的時區陷阱

    `ScheduleDefinition` 不寫 `execution_timezone` 時，預設是 **UTC**——
    `"0 2 * * *"` 對台北的人來說是**早上 10 點**跑，不是凌晨 2 點。
    所以本課所有排程都明寫 `execution_timezone="Asia/Taipei"`。

    ### `evaluate_tick`：在 notebook 裡問排程「這個時刻你會發什麼？」

    正式環境是 daemon 每隔一段時間檢查「現在有沒有到 cron 時刻」，到了就送出
    **`RunRequest`**（一張「請跑這個 job」的單子）給 Dagster 去開 run。
    在 notebook 裡我們可以直接指定一個時刻問它：

    ```python
    tick = my_schedule.evaluate_tick(dg.build_schedule_context(scheduled_execution_time=某個時刻))
    tick.run_requests      # 這個時刻會送出的單子
    ```

    注意 `evaluate_tick` 是**「假設 cron 時刻到了」**去執行排程函式，不會再幫你檢查那個時刻
    符不符合 cron——cron 什麼時候到是 daemon 的事，排程函式的責任是「決定這一跑要帶什麼」。
    """
    )
    return


@app.cell
def _(TODAY, dg, dt, mo, nightly_job):
    nightly_schedule = dg.ScheduleDefinition(
        name="nightly_2am",
        job=nightly_job,
        cron_schedule="0 2 * * *",
        execution_timezone="Asia/Taipei",
    )
    _default_tz = dg.ScheduleDefinition(name="_tz_probe", job=nightly_job, cron_schedule="0 2 * * *").execution_timezone
    _tick = nightly_schedule.evaluate_tick(
        dg.build_schedule_context(scheduled_execution_time=dt.datetime.combine(TODAY, dt.time(2, 0)))
    )
    _rr = _tick.run_requests[0]
    sched_default_tz = _default_tz
    mo.md(
        f"""
    最陽春的排程：給它一個 job ＋ 一個 cron，`{TODAY} 02:00` 這個 tick 送出
    **{len(_tick.run_requests)} 張 RunRequest**，內容是：

    - `run_key` = `{_rr.run_key}`（沒指定就是 None——每一跑都是新的一跑）
    - `run_config` = `{_rr.run_config}`（沒指定就是空的，資產用 `Config` 的預設值）
    - `tags` = `{_rr.tags}`（Dagster 自動貼上是哪個排程送來的）

    另外實測一件事：同樣的排程**不寫** `execution_timezone` 時，這一欄是 **`{_default_tz}`**
    ——沒有指定就以 UTC 解讀（`build_schedule_from_partitioned_job` 幫你產生的排程更直接，
    4️⃣ 節你會看到它印出 `UTC`）。這就是上面說的陷阱：你以為的凌晨 2 點，會變成台北的早上 10 點。
    """
    )
    return nightly_schedule, sched_default_tz


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ### 讓排程帶著參數：`@schedule` 裝飾器

    只給 job 與 cron 的排程每天做一模一樣的事。想「依日期決定這一跑的參數」，
    就改用 `@dg.schedule` 寫一個函式，回傳自己組的 `RunRequest`：

    - **`run_key`**：這一跑的身分證。**同一個排程送出相同 `run_key` 的單子，Dagster 只會開一次 run**
      ——daemon 補評估、重啟、時鐘回撥都不會害你跑兩次。日期字串是最常見的 run_key。
    - **`run_config`**：就是 1️⃣ 節那個 `{"ops": {…}}` 字典，把參數帶進這一跑。
    - **`tags`**：貼在 run 上的標籤，之後在 UI 上篩選、對帳用。

    下面這個排程平日抓 200 筆、週末抓 50 筆（真實世界的「週末量少」），
    我們拿昨天與今天兩個 tick 問它，看它送出的單子有什麼不同。
    """
    )
    return


@app.cell
def _(QUIET, TODAY, dg, dt, mo, nightly_job):
    @dg.schedule(
        name="nightly_sized",
        job=nightly_job,
        cron_schedule="0 2 * * *",
        execution_timezone="Asia/Taipei",
    )
    def nightly_sized(context: dg.ScheduleEvaluationContext):
        day = context.scheduled_execution_time.strftime("%Y-%m-%d")
        n_rows = 200 if context.scheduled_execution_time.weekday() < 5 else 50      # 週末量少
        return dg.RunRequest(
            run_key=day,                                          # 同一天只會開一次 run
            run_config={**QUIET, "ops": {"orders": {"config": {"n_rows": n_rows, "seed": 1}}}},
            tags={"day": day, "trigger": "schedule"},
        )

    _rows = []
    for _d in [TODAY - dt.timedelta(days=1), TODAY]:
        _t = nightly_sized.evaluate_tick(
            dg.build_schedule_context(scheduled_execution_time=dt.datetime.combine(_d, dt.time(2, 0)))
        )
        _rr = _t.run_requests[0]
        _rows.append({
            "tick 時刻": f"{_d} 02:00",
            "星期": "一二三四五六日"[_d.weekday()],
            "run_key": _rr.run_key,
            "run_config 的 n_rows": _rr.run_config["ops"]["orders"]["config"]["n_rows"],
            "tags": str(_rr.tags),
        })
    sched_rows = _rows
    mo.vstack([
        mo.ui.table(sched_rows, selection=None),
        mo.md(
            "兩個 tick、兩張不同的單子。`run_key` 用日期字串是排程的標準寫法——"
            "**這一天的這一跑只會有一次**，不管 daemon 重評估幾次。"
        ),
    ])
    return nightly_sized, sched_rows


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ### cron 寫錯會怎樣

    Dagster 在**建立排程物件的當下**就驗證 cron 字串，不會等到半夜才發現排程從來沒跑過。
    下面故意把「小時」寫成 25：
    """
    )
    return


@app.cell
def _(dg, mo, nightly_job):
    try:
        dg.ScheduleDefinition(name="typo", job=nightly_job, cron_schedule="0 25 * * *")
        _msg = "（居然沒報錯？）"
    except Exception as _e:  # noqa: BLE001 - 教學：要把 Dagster 的原始訊息完整秀出來
        _msg = f"{type(_e).__name__}: {_e}"
    bad_cron_error = _msg
    mo.md(
        f"""
    ```text
    {bad_cron_error}
    ```

    寫成 `"every night"` 這種人話也是同一句錯誤（Dagster 只認 5 個欄位的標準 cron）。
    時區打錯（`Asia/Taipe`）則會是 `DagsterInvalidDefinitionError: Invalid execution timezone Asia/Taipe`。
    這類錯誤全部在**載入定義時**就爆，所以 `dagster dev` 一開就會告訴你，不會靜靜地失效。
    """
    )
    return (bad_cron_error,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 4️⃣ 分割 partitions：把資產切成「一天一片」

    ### 為什麼需要

    `orders` 是「一整包訂單」。但真實的資料是**一天一天長出來的**，於是你會遇到：

    - 昨天的資料上游修正了，我只想**重算昨天那一片**，不想重算整張表。
    - 排程掛了三天，我要**補跑**那三天（backfill），而且要知道哪幾天缺。
    - 每天的量、每天的品質，我想**分天比較**。

    Dagster 的答案是 **partition（分割）**：資產不再是一個整體，而是一組以 key 命名的片
    （日期、地區、客戶⋯⋯）。`DailyPartitionsDefinition(start_date=...)` 是最常見的一種，
    partition key 就是 `YYYY-MM-DD` 字串。

    ```python
    daily_parts = dg.DailyPartitionsDefinition(start_date="2026-09-01")

    @dg.asset(partitions_def=daily_parts)
    def daily_orders(context) -> pd.DataFrame:
        day = context.partition_key          # ← 這一跑負責哪一片
        ...
    ```

    實體化時要指定是哪一片：`dg.materialize([daily_orders], partition_key="2026-09-03")`。
    忘了給會得到 `DagsterInvariantViolationError: Cannot access partition_key for a non-partitioned run`；
    給了一個不存在的日期（早於 start_date，或還沒發生的未來）則是
    `DagsterUnknownPartitionError: Could not find a partition with key ...`。

    下面用「今天往前 7 天」當分割起點，所以你不論哪一天執行，都會有 7 片可以玩。
    """
    )
    return


@app.cell
def _(TODAY, dg, dt, np, pd):
    PART_START = TODAY - dt.timedelta(days=7)
    daily_parts = dg.DailyPartitionsDefinition(start_date=PART_START.isoformat())

    @dg.asset(partitions_def=daily_parts, group_name="raw", description="每天一片的訂單")
    def daily_orders(context: dg.AssetExecutionContext) -> pd.DataFrame:
        day = context.partition_key                                   # 這一跑負責的那一片
        rng = np.random.default_rng(int(day.replace("-", "")))         # 同一天永遠算出同一份資料
        df = pd.DataFrame({"day": day, "amount": rng.gamma(2.0, 300, 20).round(0)})
        context.add_output_metadata({"day": day, "rows": len(df), "total": float(df["amount"].sum())})
        return df

    return PART_START, daily_orders, daily_parts


@app.cell
def _(QUIET, dg, daily_orders, daily_parts, mo):
    part_instance = dg.DagsterInstance.ephemeral()          # 這一節專用的帳本：誰跑過哪一片，記在它裡面
    all_keys = daily_parts.get_partition_keys()             # 到「現在」為止，所有已經完整的片

    def run_partition(key: str, how: str) -> dict:
        """跑某一片，順便把它留下的中繼資料撈出來。"""
        res = dg.materialize([daily_orders], partition_key=key, instance=part_instance, run_config=QUIET)
        mat = res.get_asset_materialization_events()[0].step_materialization_data.materialization
        meta = {k: v.value for k, v in mat.metadata.items()}
        return {"day": key, "rows": meta["rows"], "total": float(meta["total"]), "how": how}

    part_rows = [run_partition(_key, "scheduled") for _key in all_keys[:3]]   # 假裝排程只跑了最早三天就掛了
    done_first = sorted(part_instance.get_materialized_partitions(dg.AssetKey("daily_orders")))
    missing_first = [k for k in all_keys if k not in done_first]
    mo.md(
        f"""
    分割定義從 `{all_keys[0]}` 開始，到目前為止共 **{len(all_keys)} 片**：
    `{all_keys}`（今天還沒過完，所以今天不算一片）。

    我們讓「排程」只跑了前三片就掛掉：

    - 已實體化：`{done_first}`
    - **缺**：`{missing_first}` ← 這就是要補跑（backfill）的部分
    """
    )
    return all_keys, done_first, missing_first, part_instance, part_rows, run_partition


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ### 補跑（backfill）就是「把缺的片一片一片跑掉」

    UI 上你會框選一段日期按 Backfill，Dagster 幫你開一連串 run；程式裡就是一個迴圈。
    重點是**你有辦法知道哪幾片缺**——`instance.get_materialized_partitions(...)` 就是那份名單。
    這件事在「一整包」的資產上做不到：整張表只有「跑過」與「沒跑過」，沒有「哪幾天沒跑」。
    """
    )
    return


@app.cell
def _(all_keys, dg, missing_first, mo, part_instance, part_rows, run_partition):
    part_rows_all = sorted(
        part_rows + [run_partition(_key, "backfill") for _key in missing_first],
        key=lambda r: r["day"],
    )
    done_all = sorted(part_instance.get_materialized_partitions(dg.AssetKey("daily_orders")))
    mo.vstack([
        mo.md(
            f"補跑完成，`daily_orders` 現在有 **{len(done_all)} / {len(all_keys)} 片**——"
            "每一片都是獨立的一次 run，各自留下自己的中繼資料："
        ),
        mo.ui.table(part_rows_all, selection=None),
    ])
    return done_all, part_rows_all


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ### 每一片留下的中繼資料，可以直接拿來畫圖

    每次實體化都掛了 `day` / `rows` / `total`，所以「每天的總額」不用重算，
    從帳本裡讀事件就有。下圖藍色是排程跑的三片、橘色是我們補跑的那幾片。
    """
    )
    return


@app.cell
def _(part_rows_all, plt):
    from matplotlib.patches import Patch

    _fig, _ax = plt.subplots(figsize=(6.2, 3.2))
    _colors = ["#DD8452" if r["how"] == "backfill" else "#4C72B0" for r in part_rows_all]
    _ax.bar([r["day"][5:] for r in part_rows_all], [r["total"] for r in part_rows_all], color=_colors)
    _ax.set_title("daily_orders: total amount per partition")
    _ax.set_xlabel("partition key (MM-DD)")
    _ax.set_ylabel("total amount")
    _ax.legend(handles=[Patch(color="#4C72B0", label="scheduled"), Patch(color="#DD8452", label="backfill")])
    _fig.tight_layout()
    _fig
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ### 分割 ＋ 排程＝「每天跑昨天那一片」

    有了分割資產，排程就不必自己算日期：`build_schedule_from_partitioned_job(job, hour_of_day=3)`
    會產生一個排程，**在每天指定的時刻，送出「處理上一片」的 RunRequest**。

    ```python
    daily_job = dg.define_asset_job("daily_orders_job", selection=[daily_orders], partitions_def=daily_parts)
    daily_schedule = dg.build_schedule_from_partitioned_job(daily_job, hour_of_day=3)
    ```

    注意它送出的 `RunRequest` 帶的是 **`partition_key`**（不是 run_config）——
    Dagster 用它決定這一跑負責哪一片。下面連問三個日期的 03:00 tick：
    """
    )
    return


@app.cell
def _(TODAY, daily_orders, daily_parts, dg, dt, mo):
    daily_job = dg.define_asset_job("daily_orders_job", selection=[daily_orders], partitions_def=daily_parts)
    daily_schedule = dg.build_schedule_from_partitioned_job(daily_job, hour_of_day=3)
    _rows = []
    for _d in [TODAY - dt.timedelta(days=2), TODAY - dt.timedelta(days=1), TODAY]:
        _t = daily_schedule.evaluate_tick(
            dg.build_schedule_context(scheduled_execution_time=dt.datetime.combine(_d, dt.time(3, 0)))
        )
        _rows.append({
            "tick 時刻": f"{_d} 03:00",
            "送出的 partition_key": [r.partition_key for r in _t.run_requests],
        })
    psched_rows = _rows
    mo.vstack([
        mo.md(
            f"排程名稱 `{daily_schedule.name}`、cron `{daily_schedule.cron_schedule}`、"
            f"時區 `{daily_schedule.execution_timezone}`（沒指定時區就是 UTC，記得改）："
        ),
        mo.ui.table(psched_rows, selection=None),
        mo.md("每個 tick 都往回拿**前一天**那一片——這就是「每天凌晨 3 點結算昨天」的標準寫法。"),
    ])
    return daily_job, daily_schedule, psched_rows


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ### 🎛️ 互動：挑一個日期，看排程會發哪一片

    選一個日期（等於問「那天凌晨 3 點的 tick」），下面會真的去問一次
    `daily_schedule.evaluate_tick(...)`，並回報那一片在帳本裡實體化了沒有。
    """
    )
    return


@app.cell
def _(PART_START, TODAY, dt, mo):
    tick_date = mo.ui.date(
        start=PART_START + dt.timedelta(days=1),
        stop=TODAY,
        value=TODAY.isoformat(),
        label="模擬哪一天的 03:00 tick",
    )
    tick_go = mo.ui.run_button(label="問排程")
    mo.hstack([tick_date, tick_go], wrap=True, justify="start")
    return tick_date, tick_go


@app.cell
def _(daily_schedule, dg, done_all, dt, mo, tick_date, tick_go):
    mo.stop(not tick_go.value, mo.md("*選好日期後按「問排程」。*"))

    _t = daily_schedule.evaluate_tick(
        dg.build_schedule_context(scheduled_execution_time=dt.datetime.combine(tick_date.value, dt.time(3, 0)))
    )
    _keys = [r.partition_key for r in _t.run_requests]
    _key = _keys[0] if _keys else None
    mo.callout(
        mo.md(
            f"""
    **{tick_date.value} 03:00 的 tick** → 送出 {len(_t.run_requests)} 張 RunRequest，
    負責的 partition 是 **`{_key}`**（前一天）。

    這一片目前在帳本裡：**{"已經實體化過了" if _key in done_all else "還沒有資料"}**。
    """
        ),
        kind="info" if _key in done_all else "warn",
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 5️⃣ 感測器 sensor：有事情發生才跑

    ### 為什麼需要

    排程回答「時間到了嗎」，但很多事情**不看時間**：客戶什麼時候把檔案丟上來、
    上游團隊什麼時候補完資料、某個 API 什麼時候出現新資料。你當然可以「每 5 分鐘檢查一次」，
    這正是感測器在做的事——只是它幫你處理了最麻煩的部分：**怎麼記得哪些已經處理過了**。

    ### `cursor`：感測器唯一的記憶

    daemon 預設每 30 秒呼叫一次感測器函式。函式只能回答兩件事：
    **要跑什麼（`RunRequest`）**，或**為什麼不跑（`SkipReason`）**。
    但函式是無狀態的，怎麼知道上次看到哪裡了？答案是 `context.cursor`——
    一個**由你自己決定內容的字串**，Dagster 幫你存起來，下次原封不動還給你。

    - 檔案感測器：cursor 存「已經處理過的檔名清單」（本例）或「上次的最大 mtime」
    - 資料庫感測器：cursor 存「上次讀到的最大 id」
    - API 感測器：cursor 存「上次的 updated_at」

    另一個防重複的機制是 **`run_key`**：Dagster 記得同一個感測器發過哪些 run_key，
    **同一個 run_key 只會開一次 run**。cursor 讓你不用重掃，run_key 是最後一道保險。
    `dg.RunRequest()` 不給 run_key 的話，`run_key` 就是 `None`——每一 tick 都開新的一跑，
    這通常不是你要的。

    下面用一個工廠函式產生「盯著某個資料夾的感測器」（真實專案也常這樣做，
    一個工廠產出多個環境的感測器），然後連問三次 tick。
    """
    )
    return


@app.cell
def _(QUIET, dg, json, nightly_job):
    def make_inbox_sensor(name: str, folder):
        """產生一個「資料夾出現新 CSV 就跑 nightly_job」的感測器。"""

        @dg.sensor(name=name, job=nightly_job, minimum_interval_seconds=30)
        def _sensor(context: dg.SensorEvaluationContext):
            seen = set(json.loads(context.cursor)) if context.cursor else set()
            files = sorted(p.name for p in folder.glob("*.csv"))
            new = [f for f in files if f not in seen]
            for f in new:
                yield dg.RunRequest(                                   # 一個新檔案 = 一張單子
                    run_key=f,                                         # 同一個檔案只會開一次 run
                    run_config={**QUIET, "ops": {"orders": {"config": {"n_rows": 30}}}},
                    tags={"file": f, "trigger": "sensor"},
                )
            if not new:
                yield dg.SkipReason(f"no new files (已看過 {len(seen)} 個)")
            context.update_cursor(json.dumps(sorted(seen | set(new))))   # 把記憶存回去

        return _sensor

    return (make_inbox_sensor,)


@app.cell
def _(WORK, dg, make_inbox_sensor, mo):
    INBOX = WORK / "inbox"
    inbox_sensor = make_inbox_sensor("inbox_sensor", INBOX)

    _rows = []
    _cursor = None
    _scripts = [
        ("① 第一次 tick（inbox 是空的）", []),
        ("② 客戶丟了兩個檔案進來", ["batch_a.csv", "batch_b.csv"]),
        ("③ 再問一次（沒有新檔案）", []),
        ("④ 又來一個新檔案", ["batch_c.csv"]),
    ]
    for _label, _new_files in _scripts:
        for _f in _new_files:
            (INBOX / _f).write_text("amount\n100\n")
        _tick = inbox_sensor.evaluate_tick(dg.build_sensor_context(cursor=_cursor))
        _cursor = _tick.cursor
        _rows.append({
            "tick": _label,
            "RunRequest": [r.run_key for r in _tick.run_requests] or "—",
            "SkipReason": _tick.skip_message or "—",
            "cursor（存回去的記憶）": _cursor,
        })
    sensor_rows = _rows
    mo.vstack([
        mo.ui.table(sensor_rows, selection=None),
        mo.md(
            "第 ③ 次 tick 的 inbox 裡明明有兩個檔案，感測器卻說 skip——因為 cursor 記得它們都看過了。"
            "**沒有 cursor 的感測器會在每次 tick 重新發一次全部的單子**，靠 run_key 去重雖然擋得住重複的 run，"
            "但每 30 秒重掃整個資料夾的成本是你自己在付。"
        ),
    ])
    return INBOX, inbox_sensor, sensor_rows


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ### 資產感測器：上游資產一有新的實體化就觸發

    「盯檔案」是盯外面的世界；還有一種常見需求是**盯自己人**：上游資產一有新的 materialization，
    就跑下游那個 job。`@dg.asset_sensor` 幫你把 cursor 那段寫好了——
    它的 cursor 存的是事件的 storage id，你只要決定「有新事件時要送什麼單子」。

    ```python
    @dg.asset_sensor(asset_key=dg.AssetKey("orders"), job=report_job)
    def on_orders(context, asset_event):                      # asset_event 是那筆事件紀錄
        mat = asset_event.dagster_event.event_specific_data.materialization
        yield dg.RunRequest(run_key=f"{mat.asset_key.to_user_string()}-{asset_event.run_id[:8]}")
    ```
    """
    )
    return


@app.cell
def _(QUIET, FeatureStore, WORK, dg, mo, orders, orders_report):
    report_job = dg.define_asset_job("report_job", selection=[orders_report])

    @dg.asset_sensor(asset_key=dg.AssetKey("orders"), job=report_job)
    def on_orders(context: dg.SensorEvaluationContext, asset_event):
        mat = asset_event.dagster_event.event_specific_data.materialization      # 這次是哪個資產更新了
        yield dg.RunRequest(
            run_key=f"{mat.asset_key.to_user_string()}-{asset_event.run_id[:8]}",
            tags={"trigger": "asset_sensor"},
        )

    _inst = dg.DagsterInstance.ephemeral()
    _rows = []
    _cursor = None
    for _label, _do_materialize in [
        ("① orders 還沒被實體化過", False),
        ("② 有人（排程／手動）實體化了 orders", True),
        ("③ 再問一次", False),
    ]:
        if _do_materialize:
            dg.materialize(
                [orders],
                instance=_inst,
                resources={"store": FeatureStore(root=str(WORK / "prod"))},
                run_config={**QUIET, "ops": {"orders": {"config": {"n_rows": 10}}}},
            )
        _tick = on_orders.evaluate_tick(dg.build_sensor_context(instance=_inst, cursor=_cursor))
        _cursor = _tick.cursor
        _rows.append({
            "tick": _label,
            "RunRequest": [r.run_key for r in _tick.run_requests] or "—",
            "SkipReason": (_tick.skip_message or "—")[:70],
            "cursor": _cursor,
        })
    asset_sensor_rows = _rows
    mo.vstack([
        mo.ui.table(asset_sensor_rows, selection=None),
        mo.md("cursor 從 `None` 變成一個數字（事件的 storage id）——它就是「我讀到第幾筆事件了」。"),
    ])
    return asset_sensor_rows, on_orders, report_job


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ### 🎛️ 互動：自己排一次 tick

    先選「inbox 現在有哪些檔案」，再選「cursor 裡已經看過哪些」，按下去會真的跑一次感測器函式。
    試試看：**inbox 有 3 個、cursor 記得 2 個 → 只會發 1 張單子**；
    把 cursor 清空 → 3 張都發（這就是 cursor 掉了會發生的事）。
    """
    )
    return


@app.cell
def _(mo):
    PLAY_FILES = ["batch_a.csv", "batch_b.csv", "batch_c.csv"]
    play_inbox = mo.ui.multiselect(options=PLAY_FILES, value=PLAY_FILES, label="inbox 現在有的檔案")
    play_seen = mo.ui.multiselect(options=PLAY_FILES, value=PLAY_FILES[:2], label="cursor 裡已看過的檔案")
    play_go = mo.ui.run_button(label="跑一次 tick")
    mo.hstack([play_inbox, play_seen, play_go], wrap=True, justify="start")
    return PLAY_FILES, play_go, play_inbox, play_seen


@app.cell
def _(WORK, dg, json, make_inbox_sensor, mo, play_go, play_inbox, play_seen):
    mo.stop(not play_go.value, mo.md("*選好之後按「跑一次 tick」。*"))

    _folder = WORK / "play"
    for _p in _folder.glob("*.csv"):
        _p.unlink()
    for _f in play_inbox.value:
        (_folder / _f).write_text("amount\n100\n")

    _sensor = make_inbox_sensor("play_sensor", _folder)
    _tick = _sensor.evaluate_tick(
        dg.build_sensor_context(cursor=json.dumps(sorted(play_seen.value)) if play_seen.value else None)
    )
    _requests = [r.run_key for r in _tick.run_requests]
    mo.callout(
        mo.md(
            f"""
    - inbox：`{sorted(play_inbox.value)}`
    - 進去時的 cursor：`{json.dumps(sorted(play_seen.value)) if play_seen.value else None}`
    - **送出的 RunRequest：`{_requests or "沒有"}`**
    - SkipReason：`{_tick.skip_message or "—"}`
    - 出來時的 cursor：`{_tick.cursor}`
    """
        ),
        kind="success" if _requests else "neutral",
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 6️⃣ 宣告式自動化：不寫 job，資產自己說什麼時候該更新

    ### 為什麼還要第三種

    排程與感測器都是**由外往內推**：「這個時刻／這件事發生時，去跑那包資產」。
    管線一大就會變成這樣——20 個排程、8 個感測器，每加一個資產都要想「它該掛在哪個 job 上」，
    而且很容易寫出「上游還沒跑完，下游的排程時間就到了」的競態。

    **宣告式自動化（declarative automation）** 反過來：條件寫在資產上，
    資產自己說「我什麼時候該是新的」，剩下的交給 daemon。

    ```python
    @dg.asset(automation_condition=dg.AutomationCondition.eager())      # 上游一更新，我就跟著更新
    def orders_alert(): ...

    @dg.asset(automation_condition=dg.AutomationCondition.on_cron("0 6 * * *"))   # 每天 6 點、等上游備妥才更新
    def daily_report(): ...
    ```

    | 條件 | 意思 |
    |---|---|
    | `AutomationCondition.eager()` | 上游有新資料（或我從來沒被算過）就更新我 |
    | `AutomationCondition.on_cron(cron)` | 每個 cron 週期更新我一次，**但要等所有上游在這個週期內更新完** |
    | `AutomationCondition.on_missing()` | 只在「還沒有資料」時補上 |
    | 自己組合 | 條件是可以用 `&`、`|`、`~` 疊起來的積木 |

    ### 在 notebook 裡看它怎麼想

    正式環境是 daemon 定時評估這些條件、把結果變成 run。我們用
    `dg.evaluate_automation_conditions(defs=..., instance=..., cursor=...)` 手動評估一次，
    回傳的結果物件有 `total_requested`、`get_num_requested(key)`、`cursor`
    （**注意：它沒有 `run_requests` 屬性**，取用會直接 AttributeError）。

    評估要**串起來**：每次把上一次的 `cursor` 傳進去，Dagster 才知道「上次評估之後又發生了什麼」。

    下一格先包一個小工具 `evaluate_conditions(...)`：這個函式內部會呼叫 `asyncio.run()`，
    而 notebook 的 cell 本來就跑在一個事件迴圈裡，直接呼叫會得到
    `RuntimeError: asyncio.run() cannot be called from a running event loop`
    ——丟到另一個執行緒跑就好（寫成一般的 `.py` 腳本時不需要這層）。
    """
    )
    return


@app.cell
def _(dg):
    from concurrent.futures import ThreadPoolExecutor

    def evaluate_conditions(**kwargs):
        """在 notebook（事件迴圈）裡安全地評估自動化條件——丟到另一個執行緒跑。"""
        with ThreadPoolExecutor(max_workers=1) as pool:
            return pool.submit(lambda: dg.evaluate_automation_conditions(**kwargs)).result()

    return (evaluate_conditions,)


@app.cell
def _(dg):
    @dg.asset(
        deps=["orders"],
        group_name="report",
        automation_condition=dg.AutomationCondition.eager(),
        description="上游 orders 一更新就跟著更新的警示表",
    )
    def orders_alert() -> dg.MaterializeResult:
        return dg.MaterializeResult(metadata={"note": "alert refreshed"})

    return (orders_alert,)


@app.cell
def _(FeatureStore, QUIET, WORK, dg, evaluate_conditions, mo, orders, orders_alert):
    defs_eager = dg.Definitions(
        assets=[orders, orders_alert],
        resources={"store": FeatureStore(root=str(WORK / "prod"))},
    )
    _inst = dg.DagsterInstance.ephemeral()
    _rows = []

    _r0 = evaluate_conditions(defs=defs_eager, instance=_inst)
    _rows.append({
        "第幾次評估": "① 什麼都還沒實體化",
        "total_requested": _r0.total_requested,
        "orders_alert 被請求": _r0.get_num_requested(dg.AssetKey("orders_alert")),
    })

    dg.materialize(
        [orders],
        instance=_inst,
        resources={"store": FeatureStore(root=str(WORK / "prod"))},
        run_config={**QUIET, "ops": {"orders": {"config": {"n_rows": 40}}}},
    )
    _r1 = evaluate_conditions(defs=defs_eager, instance=_inst, cursor=_r0.cursor)
    _rows.append({
        "第幾次評估": "② orders 剛被實體化",
        "total_requested": _r1.total_requested,
        "orders_alert 被請求": _r1.get_num_requested(dg.AssetKey("orders_alert")),
    })

    dg.materialize(
        [orders, orders_alert],
        instance=_inst,
        selection=[orders_alert],                                   # 模擬 daemon 把上面那個請求變成一次 run
        resources={"store": FeatureStore(root=str(WORK / "prod"))},
        run_config=QUIET,
    )
    _r2 = evaluate_conditions(defs=defs_eager, instance=_inst, cursor=_r1.cursor)
    _rows.append({
        "第幾次評估": "③ orders_alert 也跑完了",
        "total_requested": _r2.total_requested,
        "orders_alert 被請求": _r2.get_num_requested(dg.AssetKey("orders_alert")),
    })

    eager_rows = _rows
    mo.vstack([
        mo.ui.table(eager_rows, selection=None),
        mo.md(
            "這三行就是 `eager()` 的全部：上游一動 → 請求更新下游；下游跟上了 → 不再請求。"
            "**我們沒有寫任何 job、任何排程**。正式環境裡，第 ② 步的那個請求會由 daemon 直接變成一個 run。"
        ),
    ])
    return defs_eager, eager_rows


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ### `on_cron` 沒有你想的那麼像排程

    `on_cron("0 6 * * *")` 不是「每天 6 點跑我」，而是
    **「每天 6 點之後，等所有上游在這個週期內更新過了，才跑我」**。
    差別就是資料工程最常見的競態：排程時間到了、上游卻還沒好，於是你用舊資料算出一份新報表。

    下面把時鐘捏在手上跑一次（用「每分鐘」的 cron 才能在 notebook 裡演完），
    每一步都往前撥一點時間、串著 cursor 評估。看 **第 ③ 步**：cron 時刻明明過了，卻不請求——
    因為上游是**上一個週期**更新的。
    """
    )
    return


@app.cell
def _(dg):
    @dg.asset(group_name="raw")
    def raw_ping() -> int:
        return 1

    @dg.asset(
        automation_condition=dg.AutomationCondition.on_cron("* * * * *"),
        group_name="report",
        description="示範用：每個 cron 週期更新一次，但要等上游先更新",
    )
    def ping_report(raw_ping: int) -> int:
        return raw_ping + 1

    return ping_report, raw_ping


@app.cell
def _(QUIET, dg, dt, evaluate_conditions, mo, ping_report, raw_ping):
    defs_cron = dg.Definitions(assets=[raw_ping, ping_report])
    _inst = dg.DagsterInstance.ephemeral()
    # 把基準時刻對齊到「下一個整分 + 5 秒」，這樣每一步落在哪個 cron 週期是確定的
    _T = dt.datetime.now(dt.UTC).replace(second=0, microsecond=0) + dt.timedelta(minutes=1, seconds=5)
    _steps = [
        (0, None, "① 第一次評估：什麼都還沒發生"),
        (1, "raw_ping", "② 上游剛更新（同一個 cron 週期內）"),
        (61, None, "③ 跨過一個 cron 時刻，但上游是上一個週期更新的"),
        (121, None, "④ 再跨一個 cron 時刻，上游還是沒有新東西"),
        (122, "raw_ping", "⑤ 上游在這個週期內更新了"),
        (181, None, "⑥ 再跨一個 cron 時刻，上游沒有新東西"),
    ]
    _cursor = None
    _rows = []
    for _off, _mat, _label in _steps:
        if _mat == "raw_ping":
            dg.materialize([raw_ping], instance=_inst, run_config=QUIET)
        _r = evaluate_conditions(
            defs=defs_cron, instance=_inst, cursor=_cursor, evaluation_time=_T + dt.timedelta(seconds=_off)
        )
        _cursor = _r.cursor
        _rows.append({
            "步驟": _label,
            "評估時刻": f"T+{_off}s",
            "評估前先實體化": _mat or "—",
            "ping_report 被請求": _r.get_num_requested(dg.AssetKey("ping_report")),
        })
    oncron_rows = _rows
    mo.vstack([
        mo.ui.table(oncron_rows, selection=None),
        mo.md(
            "只有第 ⑤ 步被請求：**cron 時刻已經過了（③④ 那兩個 tick）＋上游在這之後更新了**，兩個條件同時成立。"
            "所以 `on_cron` 的真正語意是「**每個週期最多更新我一次，而且保證用的是這個週期的新資料**」——"
            "它會等上游，排程不會。"
        ),
    ])
    return defs_cron, oncron_rows


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 7️⃣ 失敗了怎麼辦：重試與通知

    自動化最現實的一件事：**沒有人在看的時候，東西一定會壞**。網路抖一下、資料庫連線被回收、
    上游 API 回 503。這種「再試一次就好」的失敗，不該讓整條管線停到早上。

    `RetryPolicy` 就是掛在資產上的重試規則：

    ```python
    @dg.asset(retry_policy=dg.RetryPolicy(max_retries=2, delay=0.2))    # delay 單位是秒
    def flaky_train(context) -> int:
        if context.retry_number < 2:      # 第 0、1 次故意失敗
            raise RuntimeError(...)
        return 42
    ```

    `context.retry_number` 是「這是第幾次重試」（第一次執行是 0）。
    重試在事件流裡會留下 `STEP_UP_FOR_RETRY` → `STEP_RESTARTED` 這一對事件，
    UI 上看得到「重試了幾次才成功」——**不要用 try/except 把它藏起來**，
    那會讓你以為系統很健康。
    """
    )
    return


@app.cell
def _(QUIET, dg, mo):
    @dg.asset(retry_policy=dg.RetryPolicy(max_retries=2, delay=0.2), group_name="report")
    def flaky_train(context: dg.AssetExecutionContext) -> int:
        if context.retry_number < 2:                      # 模擬「前兩次連線失敗」
            raise RuntimeError(f"connection reset (attempt {context.retry_number})")
        return 42

    _res = dg.materialize([flaky_train], run_config=QUIET, raise_on_error=False)
    retry_events = [
        e.event_type_value
        for e in _res.all_events
        if e.event_type_value in ("STEP_START", "STEP_UP_FOR_RETRY", "STEP_RESTARTED", "STEP_SUCCESS", "STEP_FAILURE")
    ]
    _up = next(e for e in _res.all_events if e.event_type_value == "STEP_UP_FOR_RETRY")
    retry_message = _up.message
    mo.md(
        f"""
    - run success = **{_res.success}**，資產的值 = **{_res.asset_value("flaky_train")}**
    - 事件序列：`{retry_events}`
    - 第一次重試時 Dagster 說：`{retry_message}`

    重試了兩次才成功，而且**這件事被記錄下來了**——run 是綠的，但你看得到它抖過。
    """
    )
    return flaky_train, retry_events, retry_message


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ### 重試也救不回來的時候

    `max_retries` 用完還是失敗，這一步就是失敗——run 失敗、下游不跑。
    這時你要的是**有人被通知**，那就是 run failure sensor：

    ```python
    @dg.run_failure_sensor                      # 放進 Definitions 的 sensors，由 daemon 監看
    def alert_on_failure(context):
        send_slack(f"{context.failure_event.message}")     # 這裡換成你的通知管道
    ```

    它是一種特別的感測器：不產生 run，只在有 run 失敗時被叫起來做事（發 Slack、開 ticket）。
    Dagster 也內建 `make_slack_on_run_failure_sensor` 這類現成的。
    """
    )
    return


@app.cell
def _(QUIET, dg, mo):
    @dg.asset(retry_policy=dg.RetryPolicy(max_retries=1, delay=0.1), group_name="report")
    def always_bad(context: dg.AssetExecutionContext) -> int:
        raise RuntimeError(f"upstream API is down (attempt {context.retry_number})")

    @dg.run_failure_sensor
    def alert_on_failure(context) -> None:
        # 真實世界：send_slack(context.failure_event.message)
        return None

    _res = dg.materialize([always_bad], run_config=QUIET, raise_on_error=False)
    _fail = next(e for e in _res.all_events if e.event_type_value == "STEP_FAILURE")
    fail_message = str(_fail.event_specific_data.error.message).strip().splitlines()[-1]
    fail_events = [
        e.event_type_value
        for e in _res.all_events
        if e.event_type_value in ("STEP_UP_FOR_RETRY", "STEP_RESTARTED", "STEP_FAILURE")
    ]
    mo.md(
        f"""
    - run success = **{_res.success}**
    - 事件序列：`{fail_events}`（重試 1 次，然後放棄）
    - Dagster 的最後一句話：`{fail_message}`
    - `alert_on_failure` 的型別是 `{type(alert_on_failure).__name__}`——它會被 daemon 監看，
      任何 run 失敗都會叫到它。

    順帶一提：資產檢查（上一課的 `@asset_check`）失敗時走的是另一條路——
    那是「資料不對」，不該重試；重試是給「暫時性故障」的。
    """
    )
    return alert_on_failure, always_bad, fail_events, fail_message


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 8️⃣ 收成一份 `Definitions`，交給 `dagster dev`

    到目前為止每個零件都是分開示範的。真正部署時，把它們收進**一個 `Definitions`**：

    ```python
    defs = dg.Definitions(
        assets=[...],        # 資產（含分割資產、帶自動化條件的資產）
        jobs=[...],          # 打包好的執行單位
        schedules=[...],     # 時間到就跑
        sensors=[...],       # 有事情發生才跑（含 run failure sensor）
        resources={...},     # 這個環境的接點
    )
    ```

    然後：

    ```bash
    dagster dev -f pipeline.py      # 開 http://localhost:3000，同時起 webserver 與 daemon
    ```

    **daemon 是這一課的隱形主角**：它是那個「一直醒著」的行程，負責

    - 每隔一段時間看排程的 cron 到了沒 → 到了就送 `RunRequest` 去開 run
    - 預設每 30 秒呼叫一次每個感測器 → 拿回 `RunRequest` 或 `SkipReason`
    - 評估所有資產的 `AutomationCondition` → 把該更新的資產變成 run
    - 監看 run 狀態 → 觸發 run failure sensor

    在 UI 上每個排程與感測器都有一個開關（預設是關的，要自己打開），
    也看得到每一次 tick 的紀錄：發了幾張單、skip 的理由是什麼。
    **本課用 `evaluate_tick` 看到的東西，就是 UI 上那些 tick 紀錄的內容。**
    """
    )
    return


@app.cell
def _(
    FeatureStore,
    WORK,
    alert_on_failure,
    daily_job,
    daily_orders,
    daily_schedule,
    dg,
    inbox_sensor,
    mo,
    nightly_job,
    nightly_schedule,
    nightly_sized,
    on_orders,
    orders,
    orders_alert,
    orders_report,
    report_job,
):
    defs = dg.Definitions(
        assets=[orders, orders_report, orders_alert, daily_orders],
        jobs=[nightly_job, report_job, daily_job],
        schedules=[nightly_schedule, nightly_sized, daily_schedule],
        sensors=[inbox_sensor, on_orders, alert_on_failure],
        resources={"store": FeatureStore(root=str(WORK / "prod"))},
    )
    _job_names = sorted(j.name for j in defs.resolve_all_job_defs())      # 解析成功＝所有資源、資產、job 都對得上
    defs_summary = {
        "assets": len(list(defs.assets)),
        "jobs": len(list(defs.jobs)),
        "schedules": len(list(defs.schedules)),
        "sensors": len(list(defs.sensors)),
    }
    mo.vstack([
        mo.md(
            f"""
    `Definitions` 解析成功（這一步就是 `dagster dev` 啟動時做的檢查）：
    {defs_summary["assets"]} 個資產、{defs_summary["jobs"]} 個 job、{defs_summary["schedules"]} 個排程、
    {defs_summary["sensors"]} 個感測器。Dagster 解析出來的 job 名單是 `{_job_names}`
    ——`__ASSET_JOB` 是它自動幫全部資產準備的隱含 job（UI 上按 Materialize 就是跑它）。
    """
        ),
        mo.mermaid(
            """
    graph LR
      S1["schedule nightly_2am<br/>0 2 * * * (Asia/Taipei)"] --> J1["job nightly_job"]
      S2["schedule nightly_sized<br/>帶 run_config"] --> J1
      S3["schedule daily_orders_job_schedule<br/>0 3 * * * → 前一天那片"] --> J3["job daily_orders_job"]
      N1["sensor inbox_sensor<br/>cursor = 看過的檔名"] --> J1
      N2["asset_sensor on_orders"] --> J2["job report_job"]
      J1 --> A1["orders"]
      J1 --> A2["orders_report"]
      J2 --> A2
      J3 --> A3["daily_orders (7 片)"]
      A1 -. "AutomationCondition.eager()" .-> A4["orders_alert"]
      style S1 fill:#4C72B0,color:#fff,stroke:#1C2B33
      style S2 fill:#4C72B0,color:#fff,stroke:#1C2B33
      style S3 fill:#4C72B0,color:#fff,stroke:#1C2B33
      style N1 fill:#DD8452,color:#fff,stroke:#1C2B33
      style N2 fill:#DD8452,color:#fff,stroke:#1C2B33
      style A4 fill:#55A868,color:#fff,stroke:#1C2B33
    """
        ),
    ])
    return defs, defs_summary


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ### 三種觸發方式，怎麼選

    | | 排程 schedule | 感測器 sensor | AutomationCondition |
    |---|---|---|---|
    | 觸發來源 | 時鐘（cron） | 你寫的檢查邏輯（每 30 秒被呼叫） | 資產自己的條件 |
    | 要不要 job | 要 | 要 | **不用** |
    | 記憶 | `run_key`（同一天只跑一次） | `cursor` ＋ `run_key` | daemon 的評估 cursor |
    | 最適合 | 「每天固定時間」 | 「外部世界發生了什麼」 | 「跟著上游走」的下游資產 |
    | 常見陷阱 | 時區預設 UTC；上游還沒好就跑 | 忘了更新 cursor、忘了給 run_key | 以為 `on_cron` 是排程 |

    實務上三種會**混用**：入口資產（要去外面撈資料的那幾個）用排程或感測器觸發，
    中下游那一大片用 `AutomationCondition.eager()` 自己跟上。這樣你要維護的排程只有幾個，
    而不是幾十個。
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 🏆 延伸挑戰

    1. **LEVEL 1**：寫一個「每週一早上 9 點」的排程，帶 `run_config` 把 `n_rows` 設成 1000，
       用 `evaluate_tick` 確認它送出的 `run_key` 與 `n_rows` 是你要的。
    2. **LEVEL 2**：把 `inbox_sensor` 的 cursor 從「檔名清單」改成「上次看到的最大 mtime」，
       並讓它一次最多送 2 張單子（避免一口氣塞爆）。用連續三次 tick 驗證行為。
    3. **LEVEL 3**：把 `daily_orders` 接上 `AutomationCondition.on_cron("0 3 * * *")`，
       再加一個吃它的下游 `daily_summary`（用 `eager()`），
       用 `evaluate_automation_conditions` 串著 cursor 評估，觀察分割資產是「哪幾片」被請求
       （提示：`result.get_requested_partitions(dg.AssetKey("daily_orders"))`）。

    先自己試，卡住再展開下面的參考解答。
    帶得走：下載本檔後 `uvx marimo edit --sandbox dagster-automation_ext.py` 在自己電腦繼續玩；
    把 8️⃣ 節那格 `Definitions` 抄成一支 `pipeline.py`，就能 `dagster dev -f pipeline.py` 開 UI
    （記得在 UI 上把排程與感測器的開關打開，預設是關的）。
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.accordion(
        {
            "💡 LEVEL 1 參考解答": mo.md(
                r"""
    ```python
    @dg.schedule(name="weekly_big", job=nightly_job, cron_schedule="0 9 * * 1", execution_timezone="Asia/Taipei")
    def weekly_big(context: dg.ScheduleEvaluationContext):
        day = context.scheduled_execution_time.strftime("%Y-%m-%d")
        return dg.RunRequest(
            run_key=f"weekly-{day}",
            run_config={**QUIET, "ops": {"orders": {"config": {"n_rows": 1000}}}},
            tags={"cadence": "weekly"},
        )

    _t = weekly_big.evaluate_tick(dg.build_schedule_context(
        scheduled_execution_time=dt.datetime.combine(TODAY, dt.time(9, 0))))
    rr = _t.run_requests[0]
    rr.run_key, rr.run_config["ops"]["orders"]["config"]["n_rows"], rr.tags
    ```

    預期輸出像 `('weekly-2026-09-08', 1000, {'cadence': 'weekly', 'dagster/schedule_name': 'weekly_big'})`
    ——`dagster/schedule_name` 是 Dagster 自動貼的。注意 `evaluate_tick` 不會檢查你給的時刻是不是週一，
    cron 由 daemon 負責；要驗 cron 本身寫對沒，最直接的辦法是故意寫錯（`0 9 * * 8`）看它報不報錯。
    """
            ),
            "💡 LEVEL 2 參考解答": mo.md(
                r"""
    ```python
    @dg.sensor(name="inbox_mtime_sensor", job=nightly_job, minimum_interval_seconds=30)
    def inbox_mtime_sensor(context: dg.SensorEvaluationContext):
        last = float(context.cursor) if context.cursor else 0.0
        files = sorted(INBOX.glob("*.csv"), key=lambda p: p.stat().st_mtime)
        new = [p for p in files if p.stat().st_mtime > last][:2]        # 一次最多 2 個
        for p in new:
            yield dg.RunRequest(run_key=p.name, tags={"file": p.name})
        if not new:
            yield dg.SkipReason(f"no files newer than {last}")
        if new:
            context.update_cursor(str(new[-1].stat().st_mtime))         # 只推進到這批的最後一個
    ```

    驗證方式：一口氣丟 5 個檔案，然後連跑三次 tick——應該看到 2 張、2 張、1 張，第四次 skip。
    這裡有個真實世界的坑：mtime 相同（同一秒寫入多個檔）時會漏檔，
    所以正式環境常用「mtime + 已處理檔名」的複合 cursor（存成 JSON），
    或直接用檔名排序當 cursor。
    """
            ),
            "💡 LEVEL 3 提示": mo.md(
                r"""
    ```python
    @dg.asset(partitions_def=daily_parts, automation_condition=dg.AutomationCondition.on_cron("0 3 * * *"))
    def daily_orders_auto(context) -> int: ...

    @dg.asset(partitions_def=daily_parts, deps=[daily_orders_auto],
              automation_condition=dg.AutomationCondition.eager())
    def daily_summary(context) -> int: ...

    defs_p = dg.Definitions(assets=[daily_orders_auto, daily_summary])
    inst = dg.DagsterInstance.ephemeral()
    r = evaluate_conditions(defs=defs_p, instance=inst)      # notebook 裡用 6️⃣ 節那個包裝
    r.total_requested, r.get_requested_partitions(dg.AssetKey("daily_orders_auto"))
    ```

    怎麼知道自己做對了：`get_requested_partitions` 回傳的是**一組 partition key**，
    不是一個布林值——分割資產的自動化是「哪幾片該更新」，一次評估可能請求好幾片
    （例如剛開張、七片都缺）。第一次評估後把 `r.cursor` 傳進下一次評估，
    再實體化其中一片，觀察下一輪剩下哪幾片。
    這也是 `total_requested` 為什麼是數字而不是布林值的原因。
    """
            ),
        }
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 下一課

    你現在有了會自己動的管線：時間到會跑、檔案來了會跑、上游更新下游會跟上、壞了會重試會通知。
    第 05 課 **mlops-pipeline** 把這一課的自動化與前兩課的 MLflow 接在一起——
    訓練資產 → 評估資產 → **資產檢查當品質閘門** → 通過了才把新模型的 `champion` alias 移過去，
    一條「模型自己上線、不合格就自己擋下」的完整管線。
    """
    )
    return


if __name__ == "__main__":
    app.run()
