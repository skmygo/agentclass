# Dagster 軟體定義資產：管線不是一串任務，是一張資料地圖
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
app = marimo.App(width="medium", app_title="Dagster 軟體定義資產：管線不是一串任務，是一張資料地圖")


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    # 🧱 Dagster 軟體定義資產：管線不是一串任務，是一張資料地圖

    ## 先講一個很常見的早上

    你的模型每天早上要用一份「客戶特徵表」。它是這樣來的：凌晨 2 點 cron 跑
    `download_orders.py`，2 點 10 分跑 `clean.py`，2 點 20 分跑 `build_features.py`。
    今天早上你發現模型預測怪怪的，於是開始問：

    - 那張特徵表是**什麼時候**算出來的？（不知道，只知道 cron 有跑）
    - 它用的訂單資料是**哪一批**？（不知道）
    - 清資料那步是不是把太多列丟掉了？（不知道，日誌沖掉了）
    - 我只想重算特徵，不想重抓一次原始資料——可以嗎？（腳本是一整串的，不行）

    這四個問題全部有同一個根源：**你的管線記錄的是「跑了哪些腳本」，不是「產出了哪些資料」。**

    ## Dagster 換的那個角度

    傳統排程工具（cron、Airflow 的 DAG）想的是**任務（task）**：「先跑 A、再跑 B」。
    出問題時你只知道「B 失敗了」，卻不知道 B 產出的那張表現在是舊的、還是壞的、誰在用它。

    **Dagster** 把主角換成**資產（asset）**——這是本課最重要的一個詞：

    > **資產＝一份「存在於某處、有人會用」的東西**（一張資料表、一個模型檔、一份報表、一個
    > 向量索引），加上「它是怎麼算出來的」那個函式。

    你只宣告每個資產的上游是誰，Dagster 自動把它們連成一張圖——
    **管線不是你手寫的，是從資產之間的依賴推出來的**。於是上面四個問題各自有了答案：
    每次算完都留下時間、列數、你想記的任何中繼資料；你可以只點某一個資產重算，
    上游從上次的結果載回來；資料品質不合格時，下游根本不會開始跑。

    這種「每次執行都留下這份資料是什麼時候、用什麼算出來的」的紀錄，就是 MLOps 講的**血緣
    （lineage）**——上一課你把最好的模型放進 Registry，這一課補上「那份訓練資料是誰算的」。

    ## 這份 notebook 帶你做完

    1. 第一個資產：`@asset` 一個函式、`materialize()` 讓它「實體化」
    2. 依賴自動成圖：參數名＝上游資產名；畫出血緣圖（順便看名字打錯會怎樣）
    3. 中繼資料與日誌：每次實體化都留下列數、預覽、任何你想記的東西
    4. `deps`：只表達順序、不傳資料的依賴（以及它最容易踩的一個坑）
    5. 資料存在哪：IO manager——換掉它，資產程式一個字不改；只重算下游
    6. 資產檢查（asset check）：資料品質閘門，`blocking=True` 擋住下游
    7. `Definitions` 與 `dagster dev`：把資產、檢查、資源收成一份，UI 長什麼樣
    8. 互動：拉高門檻，看檢查從綠變紅、下游被擋

    全部在你自己的執行環境裡跑，**不連任何伺服器、不需要 GPU**：資料是隨機產生的假訂單，
    Dagster 的「帳本」是一個暫存資料夾。從第一格往下全部執行即可
    （首次安裝套件約 1–2 分鐘）。
    """
    )
    return


@app.cell
def _():
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
    return Path, QUIET, dg, mo, np, pd, plt, shutil, tempfile


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 1️⃣ 第一個資產：`@asset` 一個函式

    ### 為什麼是「函式」

    在腳本世界裡，「訂單資料」是一個檔案路徑，而「怎麼產生它」寫在某支 `.py` 的某幾行裡，
    兩者沒有任何正式的關聯——檔案被人覆蓋了、產生它的程式改了，都沒人知道。
    Dagster 要求你把這兩件事**綁在一起宣告**：一個資產就是一個 Python 函式加上 `@dg.asset`。

    - **函式名＝資產名**（Dagster 內部叫 `AssetKey`，就是這份資料在全公司的唯一名字）
    - **回傳值＝資產的內容**（DataFrame、模型物件、一個路徑字串……都可以）
    - `description`、`group_name` 是給人看的：說明與分組，之後在 UI 上會用到

    這裡的 `raw_orders` 模擬「從交易系統撈下來的訂單」：500 筆，欄位有訂單編號、客戶編號、
    金額、是否退貨；其中約 3% 的金額是負的（退款紀錄混進來了），等一下清資料會用到。
    真實世界這個函式裡會是一句 SQL 或一個 API 呼叫——形狀完全一樣。

    ### 實體化（materialize）是什麼意思

    宣告資產不會產生任何資料，就像寫好食譜不等於做出菜。
    **實體化**＝真的去執行那個函式、把結果存起來、並記下一筆「materialization 事件」
    （時間、哪個 run、附帶的中繼資料）。`dg.materialize([raw_orders])` 就是在這個 process
    裡做這件事，回傳的 `result` 可以用 `asset_value("資產名")` 把值拿回來看。

    正式部署時你不會自己呼叫 `materialize()`——UI 上按 Materialize、排程、感測器都會做這件事
    （下一課的主題）。在 notebook 裡直接呼叫它，是為了讓你看得見每一步發生什麼。
    """
    )
    return


@app.cell
def _(dg, np, pd):
    @dg.asset(description="模擬的原始訂單（含退款負值）", group_name="raw")
    def raw_orders() -> pd.DataFrame:
        rng = np.random.default_rng(0)
        n = 500
        amount = rng.gamma(2.0, 300, n).round(0)
        amount = np.where(rng.random(n) < 0.03, -amount, amount)          # 3% 是退款
        return pd.DataFrame({
            "order_id": range(n),
            "customer": rng.integers(1, 60, n),
            "amount": amount,
            "returned": rng.random(n) < 0.08,
        })

    return (raw_orders,)


@app.cell
def _(QUIET, dg, mo, raw_orders):
    _res = dg.materialize([raw_orders], run_config=QUIET)
    _df = _res.asset_value("raw_orders")
    mo.vstack(
        [
            mo.md(
                f"`materialize([raw_orders])` → success = **{_res.success}**，run id `{_res.run_id[:8]}`；"
                f"資產內容是 {len(_df)} 列的 DataFrame，其中 {int((_df.amount < 0).sum())} 筆金額為負。前 5 列："
            ),
            mo.ui.table(_df.head().to_dict("records"), selection=None),
        ]
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 2️⃣ 依賴自動成圖：參數名＝上游資產名

    ### 為什麼不用自己排順序

    Airflow 那類工具你要手寫 `a >> b >> c`。管線小的時候沒問題；等到有 40 個資料表、
    互相交叉引用，那串箭頭就會跟真實的依賴慢慢對不上——有人加了一張表忘了接線，
    某天它就用到了昨天的舊資料。

    Dagster 不讓你手寫順序。要說「`clean_orders` 是從 `raw_orders` 算出來的」，
    只要把 `raw_orders` 寫成函式的**參數**：

    ```python
    @dg.asset
    def clean_orders(raw_orders: pd.DataFrame) -> pd.DataFrame:   # 參數名＝上游資產名
        ...
    ```

    Dagster 看參數名就知道上游是誰，執行時自動把上游的值餵進來。再往下 `customer_features`
    吃 `clean_orders`，三個資產就連成一條線。你**沒有寫任何「先跑誰再跑誰」**，
    圖是從程式碼推出來的——程式怎麼寫，圖就是什麼樣，不會對不上。

    ### 這一格順便出現的三個東西

    - **`context: dg.AssetExecutionContext`**：可選的第一個參數，拿來寫日誌、掛中繼資料（下一節）。
    - **`config: CleanConfig`**：可選的設定參數。繼承 `dg.Config` 宣告欄位與預設值，
      執行時可以從外面覆蓋（第 8️⃣ 節的拉桿就是在改它），不用改程式碼。
    - **`group_name`**：把資產分組（raw／clean／features），UI 上會分區塊顯示。
    """
    )
    return


@app.cell
def _(dg, pd):
    class CleanConfig(dg.Config):
        min_amount: float = 0.0          # 8️⃣ 互動會用到：低於這個金額的訂單當雜訊丟掉

    @dg.asset(group_name="clean")
    def clean_orders(context: dg.AssetExecutionContext, config: CleanConfig, raw_orders: pd.DataFrame) -> pd.DataFrame:
        df = raw_orders[raw_orders["amount"] > config.min_amount].copy()
        context.log.info(f"kept {len(df)} / {len(raw_orders)} rows (min_amount={config.min_amount})")
        context.add_output_metadata({
            "rows": len(df),
            "dropped": len(raw_orders) - len(df),
            "preview": dg.MetadataValue.md(df.head(3).to_markdown(index=False)),
        })
        return df

    @dg.asset(group_name="features")
    def customer_features(clean_orders: pd.DataFrame) -> pd.DataFrame:
        g = clean_orders.groupby("customer").agg(
            n_orders=("order_id", "count"), total=("amount", "sum"), return_rate=("returned", "mean")
        )
        return g.reset_index()

    return CleanConfig, clean_orders, customer_features


@app.cell
def _(QUIET, clean_orders, customer_features, dg, mo, raw_orders):
    res_chain = dg.materialize([raw_orders, clean_orders, customer_features], run_config=QUIET)
    _feat = res_chain.asset_value("customer_features")
    _order = [ev.asset_key.to_user_string() for ev in res_chain.get_asset_materialization_events()]
    mo.vstack(
        [
            mo.md(
                f"一次實體化三個資產，執行順序由依賴推出：`{' → '.join(_order)}`。"
                f"`customer_features` 有 {len(_feat)} 位客戶，前 5 位："
            ),
            mo.ui.table(_feat.head().round(3).to_dict("records"), selection=None),
        ]
    )
    return (res_chain,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ### 畫出血緣圖

    `dagster dev` 的 UI 會把這張圖畫出來；在 notebook 裡我們直接從定義讀圖：
    每個資產的 `parent_keys` 就是它的上游。下面用 mermaid 畫（節點顏色＝group）。
    """
    )
    return


@app.cell
def _(dg, mo):
    def lineage_mermaid(defs: dg.Definitions) -> str:
        graph = defs.resolve_asset_graph() if hasattr(defs, "resolve_asset_graph") else defs.get_asset_graph()
        keys = graph.all_asset_keys if hasattr(graph, "all_asset_keys") else graph.get_all_asset_keys()
        lines = ["graph LR"]
        palette = {"raw": "#4C72B0", "clean": "#DD8452", "features": "#55A868", "default": "#8172B3"}
        for k in sorted(keys, key=lambda k: k.to_user_string()):
            node = graph.get(k)
            name = k.to_user_string()
            lines.append(f'  {name}["{name}"]')
            if getattr(node, "is_executable", True):          # 有程式可以算的資產：填色＝group
                fill = palette.get(getattr(node, "group_name", None), palette["default"])
                lines.append(f"  style {name} fill:{fill},color:#fff,stroke:#1C2B33")
            else:                                             # 圖上有名字、但沒有人負責算它（外部資產）
                lines.append(f"  style {name} fill:#fff,color:#C44E52,stroke:#C44E52,stroke-dasharray: 5 5")
            for p in node.parent_keys:
                lines.append(f"  {p.to_user_string()} --> {name}")
        return "\n".join(lines)

    return (lineage_mermaid,)


@app.cell
def _(clean_orders, customer_features, dg, lineage_mermaid, mo, raw_orders):
    defs_v1 = dg.Definitions(assets=[raw_orders, clean_orders, customer_features])
    mo.mermaid(lineage_mermaid(defs_v1))
    return (defs_v1,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ### 名字就是契約：打錯會怎樣

    既然「參數名＝上游資產名」，那參數名打錯一個字會發生什麼事？
    下面故意把 `clean_orders` 寫成 `clean_order`（少一個 s），然後試著實體化。

    重點不是「會出錯」，而是**什麼時候出錯**：Dagster 在**組圖的時候**就擋下來了——
    還沒有執行任何一個資產函式、沒有半筆資料被寫出去，而且它會告訴你「你是不是想打這個」。
    這跟腳本世界很不一樣：腳本要跑到那一行才炸，前面已經寫壞的東西收不回來。
    """
    )
    return


@app.cell
def _(QUIET, clean_orders, dg, mo, pd, raw_orders):
    def _typo_demo():
        @dg.asset
        def customer_features(clean_order: pd.DataFrame) -> pd.DataFrame:   # ← 少了 s
            return clean_order.head()

        try:
            dg.materialize([raw_orders, clean_orders, customer_features], run_config=QUIET)
        except Exception as e:  # noqa: BLE001 — 教學用：要把錯誤原文印出來給學員看
            return type(e).__name__, str(e)
        return "（沒有錯）", ""

    _cls, _msg = _typo_demo()
    _block = _msg.strip().replace("\t", "    ").replace("\n", "\n    ")   # 對齊周圍縮排，md 才不會亂
    mo.md(
        f"""
    Dagster 丟出 **`{_cls}`**：

    ```text
    {_block}
    ```

    最後那行 `Did you mean one of the following?` 是 Dagster 幫你比對過現有資產名之後的建議。
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 3️⃣ 中繼資料與日誌：每次實體化都留下證據

    ### 為什麼需要這個

    回到開頭那個早上：「清資料那步是不是把太多列丟掉了？」——要回答這種問題，
    光有「跑成功了」是不夠的，你需要**每一次執行的隨身紀錄**。

    **中繼資料（metadata）**就是這個：跟著這一次實體化一起存下來的小抄。
    `clean_orders` 裡做了兩件事：

    - `context.log.info(...)` 寫**日誌**——給人當下讀的，事後會被沖掉。
    - `context.add_output_metadata({...})` 掛**中繼資料**——**永久跟著這次 materialization**，
      這裡記了列數、丟掉幾筆、前三列預覽。

    中繼資料可以是數字、字串、markdown、JSON、URL、檔案路徑……
    數字類在 UI 裡會自動畫成時間序列——「今天的列數突然剩一半」一眼就看得到，
    不用等到模型爛掉才回頭查。`dg.MetadataValue.md(...)` 是明確指定型別的寫法
    （純數字與字串可以直接寫，Dagster 會自己判斷）。

    從剛才的執行結果把 materialization 事件讀回來看——這就是 UI 上顯示的那些東西：
    """
    )
    return


@app.cell
def _(mo, res_chain):
    _rows = []
    for _ev in res_chain.get_asset_materialization_events():
        _mat = _ev.step_materialization_data.materialization
        _meta = {k: (v.value if hasattr(v, "value") else str(v)) for k, v in _mat.metadata.items()}
        _rows.append({
            "asset": _mat.asset_key.to_user_string(),
            "metadata keys": ", ".join(_meta) or "—",
            "rows": _meta.get("rows", "—"),
            "dropped": _meta.get("dropped", "—"),
        })
    clean_meta = next(r for r in _rows if r["asset"] == "clean_orders")
    mo.vstack(
        [
            mo.ui.table(_rows, selection=None),
            mo.md(
                f"`clean_orders` 這次留下 **{clean_meta['rows']} 列**、丟掉 **{clean_meta['dropped']} 筆**退款——"
                "這兩個數字每次執行都會存，之後可以畫成趨勢。"
            ),
        ]
    )
    return (clean_meta,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 4️⃣ `deps`：只表達順序、不傳資料

    ### 為什麼需要第二種依賴

    第 2️⃣ 節的依賴（寫成參數）同時做了兩件事：**排順序** ＋ **把上游的值搬進來**。
    但不是每個下游都需要上游的值：

    - 「把報表寄出去」只要等 `customer_features` 算完就好，它自己會去讀資料倉儲。
    - 上游是一張 300 GB 的表，下游是一句 `CREATE TABLE ... AS SELECT`——
      資料全程留在資料庫裡，沒必要搬進 Python 記憶體。

    這時用 `deps=[...]`：**有順序、有血緣，但不傳值**。函式簽名裡不會出現上游的名字。
    這種資產通常回傳 `dg.MaterializeResult(metadata=...)`——「我做完了，這是我的紀錄」，
    但沒有資料要交給下一棒。

    `deps` 的元素可以是**資產函式物件**（`deps=[customer_features]`）或**字串**
    （`deps=["customer_features"]`）。下一格會看到：這兩種寫法的安全性差很多。
    """
    )
    return


@app.cell
def _(customer_features, dg):
    @dg.asset(deps=[customer_features], group_name="features", description="寄報表（模擬）")
    def feature_report() -> dg.MaterializeResult:
        # 真實世界這裡會去讀 warehouse、產 PDF、寄信；Dagster 只保證它在 customer_features 之後跑
        return dg.MaterializeResult(metadata={"recipients": 3, "status": "sent (simulated)"})

    return (feature_report,)


@app.cell
def _(QUIET, clean_orders, customer_features, dg, feature_report, mo, raw_orders):
    _res = dg.materialize([raw_orders, clean_orders, customer_features, feature_report], run_config=QUIET)
    _last = _res.get_asset_materialization_events()[-1].step_materialization_data.materialization
    mo.md(
        f"`feature_report` 排在最後（`{_last.asset_key.to_user_string()}`），metadata = "
        f"`{ {k: v.value for k, v in _last.metadata.items()} }`——它沒有回傳資料，但一樣是圖上的一個節點。"
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ### ⚠️ `deps` 打錯字，Dagster 不會擋你

    第 2️⃣ 節打錯參數名，Dagster 在組圖時就攔下來了。但 `deps` 用**字串**打錯，
    行為完全不同——因為字串在 Dagster 眼裡是一個合法的資產名，只是「這份 Definitions
    裡沒有人負責算它」。這種節點叫**外部資產**（external asset）：圖上有它的位置，
    但它由 Dagster 之外的東西產生（別的團隊、別的工具、手動上傳）。

    所以 `deps=["clean_order"]` 不會報錯，只會靜靜地變成「依賴一個永遠不會被算的東西」。
    下面把它跑起來看後果——注意 run **是成功的**，而執行順序已經壞掉了：
    """
    )
    return


@app.cell
def _(QUIET, clean_orders, dg, lineage_mermaid, mo, raw_orders):
    def _deps_typo_demo():
        @dg.asset(deps=["clean_order"], group_name="features")     # ← 少了 s，不會報錯
        def mail_report() -> dg.MaterializeResult:
            return dg.MaterializeResult(metadata={"status": "sent"})

        defs = dg.Definitions(assets=[raw_orders, clean_orders, mail_report])
        res = dg.materialize([raw_orders, clean_orders, mail_report], run_config=QUIET)
        return defs, res.success, [ev.asset_key.to_user_string() for ev in res.get_asset_materialization_events()]

    _defs_typo, _typo_ok, _typo_order = _deps_typo_demo()
    mo.vstack(
        [
            mo.md(
                f"""
    - run success = **{_typo_ok}**（沒有任何錯誤訊息）
    - 實際執行順序：`{' → '.join(_typo_order)}`——報表**沒有等 `clean_orders`**
    - 圖上多了一個虛線節點 `clean_order`：Dagster 認得這個名字，但沒有人負責算它

    這是最難抓的那種 bug：什麼都沒壞，只是報表用到的資料比你以為的舊。
    **能傳函式物件就別傳字串**（`deps=[clean_orders]`）——打錯字時 Python 自己就會
    `NameError`，連 Dagster 都不用出手。真的要用字串（跨檔案、上游是別人的資產），
    就在 `Definitions` 建好後檢查圖上有沒有意料之外的外部資產。
    """
            ),
            mo.mermaid(lineage_mermaid(_defs_typo)),
        ]
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 5️⃣ 資料存在哪：IO manager

    ### 一個你可能還沒注意到的問題

    `clean_orders` `return df` 之後、`customer_features` 拿到 `clean_orders` 之前——
    這中間誰把 DataFrame 存下來、又是誰讀回來的？你的資產函式裡沒有任何一行
    `to_csv`／`read_csv`。

    答案是 **IO manager**（輸入輸出管理員）：一個負責「資產算完往哪存、下游要用時從哪讀」
    的小元件。預設的 `fs_io_manager` 把每個資產 pickle 成一個檔案，放進 storage 目錄。

    分開的好處很實際：今天存本機 pickle、明天要改存 Parquet 到 S3、後天團隊要求寫進
    Snowflake——**換掉 IO manager 就好，每一個資產函式都不用改一個字**。
    「算什麼」與「存哪裡」是兩件事，Dagster 讓它們分開演化。

    ### 順便認識 `DagsterInstance`

    **instance**是 Dagster 的「帳本」：run 紀錄、事件、中繼資料、還有 storage 都放在裡面。
    前面幾格沒指定，Dagster 每次都開一個用完就丟的暫時帳本（所以資料不會累積）。
    下面用一個**固定的** `DagsterInstance.ephemeral()` 存起來，才看得到檔案落在哪、
    也才能做「只重算下游」。正式部署時 instance 是一個真的資料庫，跨執行都在。
    """
    )
    return


@app.cell
def _(Path, QUIET, clean_orders, dg, mo, raw_orders):
    instance = dg.DagsterInstance.ephemeral()          # 本 notebook 專用的「帳本」：run 紀錄、事件、storage 都在裡面
    _res = dg.materialize([raw_orders, clean_orders], instance=instance, run_config=QUIET)
    _storage = Path(instance.storage_directory())
    _files = sorted(str(p.relative_to(_storage)) for p in _storage.rglob("*") if p.is_file())
    _tree = ("\n    ").join(_files)                    # 對齊周圍縮排，md 才不會把整段當程式碼
    mo.md(
        f"""
    預設 IO manager 把資產存在 `{_storage}`：

    ```text
    {_tree}
    ```

    一個資產一個 pickle 檔（檔名＝資產名，沒有副檔名）。下游要用時，IO manager
    再從這裡讀回來——這就是為什麼你的資產函式從來不用管檔案。
    """
    )
    return (instance,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ### 自己寫一個：存 CSV

    IO manager 只要回答兩個問題，所以它比想像中小：
    **`handle_output`**（資產算完了，存去哪）與 **`load_input`**（下游要用了，從哪讀）。
    繼承 `dg.ConfigurableIOManager` 還可以宣告設定欄位（這裡是 `root`：檔案放哪個資料夾），
    建立時像一般物件那樣傳進去。

    寫好之後用 `resources={"io_manager": ...}` 換掉預設的——**只有這一行變**，
    三個資產函式一個字都沒動：
    """
    )
    return


@app.cell
def _(Path, dg, pd):
    class CsvIOManager(dg.ConfigurableIOManager):
        root: str

        def _path(self, context) -> Path:
            return Path(self.root) / f"{context.asset_key.to_user_string()}.csv"

        def handle_output(self, context, obj: pd.DataFrame) -> None:      # 資產算完 → 存
            self._path(context).parent.mkdir(parents=True, exist_ok=True)
            obj.to_csv(self._path(context), index=False)

        def load_input(self, context) -> pd.DataFrame:                     # 下游要用 → 讀
            return pd.read_csv(self._path(context))

    return (CsvIOManager,)


@app.cell
def _(CsvIOManager, Path, QUIET, clean_orders, customer_features, dg, mo, raw_orders, shutil, tempfile):
    CSV_ROOT = Path(tempfile.gettempdir()) / "dagster-lesson-csv"
    shutil.rmtree(CSV_ROOT, ignore_errors=True)
    _res = dg.materialize(
        [raw_orders, clean_orders, customer_features],
        resources={"io_manager": CsvIOManager(root=str(CSV_ROOT))},   # 只換這一行
        run_config=QUIET,
    )
    _files = sorted(p.name for p in CSV_ROOT.iterdir())
    mo.md(
        f"""
    換成 `CsvIOManager` 之後，同樣三個資產、同樣的函式，落地變成 `{_files}`（在 `{CSV_ROOT}`），
    success = {_res.success}。`customer_features` 讀進來的 `clean_orders` 是從 CSV 載回的——
    資產程式完全不知道這件事。
    """
    )
    return (CSV_ROOT,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ### 只重算下游：回答開頭那個「可以嗎」

    開頭問過：「我只想重算特徵，不想重抓一次原始資料——可以嗎？」腳本世界的答案是不行
    （腳本是一整串的）。有了資產與 storage，答案是可以：

    `selection=[customer_features]` 表示「這次只執行這一個資產」；它的上游 `clean_orders`
    不重跑，由 IO manager 從上次的結果**載回來**。事件裡的 `LOADED_INPUT` 就是載入的證據。
    大型管線裡「改了特徵工程、原始資料抓一次要 40 分鐘」就是靠這個省下來的。

    （UI 上這件事就是點某個資產按 Materialize；`selection` 也吃字串與萬用語法，
    例如 `"clean_orders*"` ＝ 它和它所有下游。）
    """
    )
    return


@app.cell
def _(QUIET, clean_orders, customer_features, dg, instance, mo, raw_orders):
    _sub = dg.materialize(
        [raw_orders, clean_orders, customer_features],
        selection=[customer_features],          # 只算這個；上游從 storage 載回
        instance=instance,
        run_config=QUIET,
    )
    _ran = [ev.asset_key.to_user_string() for ev in _sub.get_asset_materialization_events()]
    _loaded = [ev for ev in _sub.all_events if ev.event_type_value == "LOADED_INPUT"]

    _star = dg.materialize(
        [raw_orders, clean_orders, customer_features],
        selection="clean_orders*",              # 它自己＋所有下游
        instance=instance,
        run_config=QUIET,
    )
    _star_ran = [ev.asset_key.to_user_string() for ev in _star.get_asset_materialization_events()]
    mo.md(
        f"""
    - `selection=[customer_features]` → 只實體化了 `{_ran}`；事件裡有 {len(_loaded)} 筆
      `LOADED_INPUT`——`clean_orders` 是**載回來**的，不是重算的。
    - `selection="clean_orders*"`（它自己＋所有下游）→ 實體化了 `{_star_ran}`，
      `raw_orders` 這次不用重抓。
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ### 但上游得**真的算過**才行

    「只重算下游」有一個前提：上游的結果要**存在這個 instance 的 storage 裡**。
    換一台機器、換一個 storage 目錄、或那個資產從來沒被實體化過，載入就會失敗。

    這是新手最常撞的一堵牆——尤其是在本機試 `dagster dev`、資料還沒跑過就直接點
    最下游的資產。下面故意用一個**全新的空 instance** 重現它：
    """
    )
    return


@app.cell
def _():
    def failure_reason(result):
        """把 run 的第一個失敗步驟拆成（外層錯誤, 最底層的原始例外）。

        Dagster 會把你的原始例外包起來，收在 `error.cause` 裡（有時包好幾層）——
        一路往下走到底，才是真正的原因。
        """
        fail = next((ev for ev in result.all_events if ev.is_step_failure), None)
        if fail is None:
            return "（這次沒有失敗的步驟）", ""
        err = fail.event_specific_data.error
        node = err
        while getattr(node, "cause", None) is not None:      # 往下走到最底層
            node = node.cause
        outer = [ln for ln in (err.message or "").strip().splitlines() if ln.strip()]
        root = [ln for ln in (node.message or "").strip().splitlines() if ln.strip()]
        return (outer[0] if outer else "?"), (root[-1] if root else "（沒有更底層的原因）")

    return (failure_reason,)


@app.cell
def _(QUIET, clean_orders, customer_features, dg, failure_reason, mo, raw_orders):
    _fresh = dg.DagsterInstance.ephemeral()             # 全新的空帳本，什麼都沒算過
    _miss = dg.materialize(
        [raw_orders, clean_orders, customer_features],
        selection=[customer_features],                  # 直接要最下游
        instance=_fresh,
        run_config=QUIET,
        raise_on_error=False,
    )
    _outer, _root = failure_reason(_miss)
    mo.md(
        f"""
    - run success = **{_miss.success}**
    - 外層：`{_outer}`
    - 真正的原因：`{_root}`

    Dagster 沒有「自動幫你補跑上游」——它只做你叫它做的事。所以要嘛把上游一起放進這次
    `materialize`（不給 `selection`，整條線跑一次），要嘛指到一個已經有這些資料的 instance。
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 6️⃣ 資產檢查：資料品質閘門

    ### 為什麼「跑成功」不等於「資料是對的」

    上游今天改了一個欄位定義，你的清理邏輯照跑不誤，只是留下的列數從 478 變成 12。
    程式沒有拋任何例外、run 是綠的、模型照樣訓完上線——三天後才有人發現預測全歪。

    **資產檢查（asset check）**就是把「資料應該長什麼樣」寫成程式碼，掛在資產上：

    ```python
    @dg.asset_check(asset=clean_orders)
    def no_negative_amount(clean_orders):                 # 參數就是那個資產的值
        return dg.AssetCheckResult(passed=..., metadata={...})
    ```

    它跟單元測試很像，差別是**測的是資料不是程式**，而且**每次資產實體化後自動跑**，
    結果跟資產一起記錄：UI 上資產旁邊就是一個綠勾或紅叉，還看得到歷次的變化。

    ### 兩個獨立的旋鈕：`severity` 與 `blocking`

    新手最容易混在一起的兩件事，其實是分開設定的：

    - **`severity`（有多嚴重）**寫在結果上：`AssetCheckResult(severity=...)`，
      **預設就是 `ERROR`**；覺得只是「怪怪的但不致命」就降成 `dg.AssetCheckSeverity.WARN`。
      它只影響這筆紀錄長什麼樣（UI 上紅字還是黃字）。
    - **`blocking`（擋不擋下游）**寫在裝飾器上：`@dg.asset_check(..., blocking=True)`。
      **這個才會擋路**——`clean_orders` 沒通過，`customer_features` 就不執行，整個 run 失敗。

    非 blocking 的檢查失敗只會留下一筆紅色紀錄，下游照跑；blocking 的檢查失敗才是真的踩煞車。
    後者正是 MLOps 要的那句話：**資料不對，就不要拿去訓模型**。
    壞資料造成的損害不是「跑失敗」，而是「跑成功了但結果是錯的」——後者昂貴得多。

    下面兩個檢查：`no_negative_amount`（清完不該有負值，WARN、不擋路）、
    `enough_rows`（至少 400 列，ERROR ＋ blocking）。注意**檢查要跟資產放進同一個清單**才會執行
    （`materialize()` 沒有 `asset_checks=` 這個參數；忘了放的話它不會跑、也不會提醒你）。
    """
    )
    return


@app.cell
def _(clean_orders, dg, pd):
    @dg.asset_check(asset=clean_orders, description="清完不該再有負金額")   # 沒有 blocking＝不擋路
    def no_negative_amount(clean_orders: pd.DataFrame) -> dg.AssetCheckResult:
        bad = int((clean_orders["amount"] < 0).sum())
        return dg.AssetCheckResult(
            passed=bad == 0, severity=dg.AssetCheckSeverity.WARN, metadata={"bad_rows": bad}
        )

    @dg.asset_check(asset=clean_orders, blocking=True, description="太少列＝上游抓壞了，不要往下算")
    def enough_rows(clean_orders: pd.DataFrame) -> dg.AssetCheckResult:
        n = len(clean_orders)
        return dg.AssetCheckResult(
            passed=n >= 400, severity=dg.AssetCheckSeverity.ERROR, metadata={"rows": n, "min_rows": 400}
        )

    return enough_rows, no_negative_amount


@app.cell
def _(QUIET, clean_orders, customer_features, dg, enough_rows, mo, no_negative_amount, raw_orders):
    _res = dg.materialize(
        [raw_orders, clean_orders, customer_features, no_negative_amount, enough_rows],   # 檢查跟資產放同一個清單
        run_config=QUIET,
    )
    check_rows_ok = [
        {
            "check": ev.check_name,
            "asset": ev.asset_key.to_user_string(),
            "passed": "✅" if ev.passed else "❌",
            "severity": str(getattr(getattr(ev, "severity", None), "value", getattr(ev, "severity", "—"))),
            "metadata": str({k: v.value for k, v in ev.metadata.items()}),
        }
        for ev in _res.get_asset_check_evaluations()
    ]
    mo.vstack(
        [
            mo.md(f"正常情況：run success = **{_res.success}**，兩個檢查都過，`customer_features` 照常實體化。"),
            mo.ui.table(check_rows_ok, selection=None),
        ]
    )
    return (check_rows_ok,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ### 閘門在哪裡關上

    `min_amount` 這個設定越高、留下的訂單越少。先畫出「門檻 → 留下幾列」這條曲線，
    看 `enough_rows` 的 400 列底線會在哪裡被踩破（虛線是底線，點線是等一下要用的 800）：
    """
    )
    return


@app.cell
def _(np, plt, res_chain):
    _raw = res_chain.asset_value("raw_orders")
    _thr = np.arange(0, 1550, 50)
    _kept = np.array([int((_raw["amount"] > t).sum()) for t in _thr])
    gate_at = int(_thr[_kept < 400][0])                      # 第一個守不住的門檻
    kept_800 = int(_kept[_thr == 800][0])
    _fig, _ax = plt.subplots(figsize=(6.2, 3.0))
    _ax.plot(_thr, _kept, color="#DD8452", lw=2, label="rows kept")
    _ax.axhline(400, color="#C44E52", ls="--", lw=1.4, label="enough_rows min (400)")
    _ax.axvline(800, color="#4C72B0", ls=":", lw=1.4, label="min_amount = 800")
    _ax.set_xlabel("min_amount")
    _ax.set_ylabel("rows in clean_orders")
    _ax.set_title("Where the blocking check starts to fail")
    _ax.legend(fontsize=8)
    _fig.tight_layout()
    _fig
    return gate_at, kept_800


@app.cell(hide_code=True)
def _(gate_at, kept_800, mo):
    mo.md(
        f"""
    曲線第一次掉到 400 以下是 `min_amount = {gate_at}`；本課接下來用的
    `min_amount = 800` 只留下 **{kept_800} 列**，離底線很遠。

    ### 讓它失敗看看

    把 `min_amount` 調到 800（透過 `run_config` 傳給第 2️⃣ 節那個 `CleanConfig`）：
    `enough_rows` 失敗、run 失敗、`customer_features` **不會執行**。
    `raise_on_error=False` 是「別丟例外給我，把結果物件給我」——這樣才看得到 Dagster 怎麼說。
    """
    )
    return


@app.cell
def _(QUIET, clean_orders, customer_features, dg, enough_rows, mo, no_negative_amount, raw_orders):
    _res = dg.materialize(
        [raw_orders, clean_orders, customer_features, no_negative_amount, enough_rows],
        run_config={**QUIET, "ops": {"clean_orders": {"config": {"min_amount": 800}}}},
        raise_on_error=False,
    )
    _materialized = [ev.asset_key.to_user_string() for ev in _res.get_asset_materialization_events()]
    _rows_blocked = [
        {
            "check": ev.check_name,
            "passed": "✅" if ev.passed else "❌",
            "severity": str(getattr(getattr(ev, "severity", None), "value", getattr(ev, "severity", "—"))),
            "metadata": str({k: v.value for k, v in ev.metadata.items()}),
        }
        for ev in _res.get_asset_check_evaluations()
    ]
    _fail = next(ev for ev in _res.all_events if ev.is_step_failure)
    blocked_error = _fail.event_specific_data.error.message.strip()
    _block = blocked_error.replace("\n", "\n    ")          # 對齊周圍縮排
    mo.vstack(
        [
            mo.md(
                f"""
    - run success = **{_res.success}**
    - 實體化的資產：`{_materialized}`——**沒有 `customer_features`**（下游真的被擋住了）
    - Dagster 的錯誤訊息：

    ```text
    {_block}
    ```

    訊息把「幾個 blocking 檢查失敗、是哪個資產的哪個檢查」都講清楚了。
    下表是這次兩個檢查的結果：`no_negative_amount` 照樣執行也照樣通過（清完確實沒有負值），
    只是它不 blocking；**踩下煞車的是 `enough_rows`**。
    """
            ),
            mo.ui.table(_rows_blocked, selection=None),
        ]
    )
    return (blocked_error,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ### 資產本身壞掉呢？

    檢查失敗是「資料不對」；資產函式丟例外是「程式壞了」（上游 schema 變了、API 掛了、
    憑證過期）。兩者 Dagster 的處理一樣：這一步標記失敗、**下游不執行**、
    這個資產在圖上維持「上一次成功的樣子」——不會被半成品覆蓋掉。

    差別在錯誤訊息的形狀：Dagster 會把你的原始例外**包起來**，外層是它自己的
    `DagsterExecutionStepExecutionError`（告訴你是哪個 op 出事），原始例外收在
    `error.cause` 裡。用前面那個 `failure_reason()` 一路走到最底層，就是真正的原因。
    """
    )
    return


@app.cell
def _(QUIET, dg, failure_reason, mo):
    @dg.asset
    def broken_asset() -> int:
        raise ValueError("boom: upstream schema changed")

    @dg.asset(deps=[broken_asset])
    def after_broken() -> int:
        return 1

    _res = dg.materialize([broken_asset, after_broken], run_config=QUIET, raise_on_error=False)
    _outer, broken_root = failure_reason(_res)
    mo.md(
        f"""
    - success = **{_res.success}**；實體化了 `{[ev.asset_key.to_user_string() for ev in _res.get_asset_materialization_events()]}`（空的——
      `broken_asset` 沒算成功，`after_broken` 根本沒開始）
    - 外層（Dagster 包的）：`{_outer}`
    - 最底層的原因（你的例外）：`{broken_root}`

    在 UI 上這兩層都看得到，日誌裡還有完整的 traceback 指到你程式的那一行。
    """
    )
    return after_broken, broken_asset, broken_root


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 7️⃣ `Definitions` 與 `dagster dev`

    到目前為止我們一直在 notebook 裡手動呼叫 `materialize()`——那是為了讓每一步看得見。
    真正部署時，你把資產、檢查、資源、（下一課的）排程與感測器收進一個 **`Definitions`**
    物件，那就是「這個專案有哪些東西」的唯一入口：

    ```bash
    dagster dev -f my_pipeline.py      # 開 http://localhost:3000
    ```

    UI 會畫出資產圖（跟下面這張一樣，另外標了每個資產的最近實體化時間、metadata 趨勢、
    檢查狀態），你可以點任何資產按 **Materialize**、只重算某個子集、看每次 run 的日誌。
    你在 notebook 裡看到的東西，UI 上都有——只是不用自己寫程式去讀。

    `Definitions` 也是 Dagster 做整體檢查的地方：**資產名重複、依賴斷掉**都在這裡擋下來，
    載入失敗會直接告訴你哪裡有問題（下一格示範資產名撞名的樣子）。
    """
    )
    return


@app.cell
def _(dg, mo, pd):
    def _duplicate_demo():
        @dg.asset(name="clean_orders")               # 兩個人各自寫了一個 clean_orders
        def a() -> pd.DataFrame:
            return pd.DataFrame({"x": [1]})

        @dg.asset(name="clean_orders")
        def b() -> pd.DataFrame:
            return pd.DataFrame({"y": [1]})

        try:
            _d = dg.Definitions(assets=[a, b])
            _d.resolve_all_job_defs() if hasattr(_d, "resolve_all_job_defs") else _d.get_all_job_defs()
        except Exception as e:  # noqa: BLE001 — 教學用：要把錯誤原文印出來給學員看
            return f"{type(e).__name__}: {e}"
        return "（沒有錯）"

    mo.md(
        f"""
    資產名撞名時 Dagster 說的話：

    ```text
    {_duplicate_demo()}
    ```

    資產名是**全域唯一**的識別碼（就像資料表名），撞名不是警告而是錯誤——
    否則「這份資料是誰算的」就有兩個答案了。真實專案裡常用
    `dg.AssetKey(["marketing", "clean_orders"])` 這種多層命名把它們分開。
    """
    )
    return


@app.cell
def _(
    CsvIOManager,
    CSV_ROOT,
    clean_orders,
    customer_features,
    dg,
    enough_rows,
    feature_report,
    lineage_mermaid,
    mo,
    no_negative_amount,
    raw_orders,
):
    defs = dg.Definitions(
        assets=[raw_orders, clean_orders, customer_features, feature_report],
        asset_checks=[no_negative_amount, enough_rows],
        resources={"io_manager": CsvIOManager(root=str(CSV_ROOT))},
    )
    _job = defs.resolve_implicit_global_asset_job_def() if hasattr(defs, "resolve_implicit_global_asset_job_def") else defs.get_implicit_global_asset_job_def()
    mo.vstack(
        [
            mo.md(
                f"`Definitions` 收了 {len(list(defs.assets))} 個資產、{len(list(defs.asset_checks))} 個檢查；"
                f"隱含的全域 job 叫 `{_job.name}`。血緣圖："
            ),
            mo.mermaid(lineage_mermaid(defs)),
        ]
    )
    return (defs,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 8️⃣ 互動：拉高門檻，看閘門關上

    把前面所有東西串起來玩一次。拉桿改的是 `CleanConfig.min_amount`——一個設定值，
    不是程式碼；按按鈕就重新實體化整條線（三個資產＋兩個檢查）。

    建議這樣玩：
    **0 → 400 → 700 → 800 → 1200**，每次注意兩件事：
    留下的列數（`enough_rows` 的 `rows`）、以及**實體化清單裡還有沒有 `customer_features`**。
    閘門一關上，下游就從清單裡消失——這就是 `blocking=True` 在做的事。
    """
    )
    return


@app.cell
def _(mo):
    gate_min = mo.ui.slider(0, 1500, step=50, value=0, label="min_amount", show_value=True)
    gate_button = mo.ui.run_button(label="重新實體化")
    mo.hstack([gate_min, gate_button], wrap=True, justify="start")
    return gate_button, gate_min


@app.cell
def _(
    QUIET,
    clean_orders,
    customer_features,
    dg,
    enough_rows,
    gate_button,
    gate_min,
    mo,
    no_negative_amount,
    raw_orders,
):
    mo.stop(not gate_button.value, mo.md("*調好 min_amount 後按「重新實體化」。*"))

    _res = dg.materialize(
        [raw_orders, clean_orders, customer_features, no_negative_amount, enough_rows],
        run_config={**QUIET, "ops": {"clean_orders": {"config": {"min_amount": gate_min.value}}}},
        raise_on_error=False,
    )
    _mats = [ev.asset_key.to_user_string() for ev in _res.get_asset_materialization_events()]
    _kept = next(
        (
            ev.step_materialization_data.materialization.metadata["rows"].value
            for ev in _res.get_asset_materialization_events()
            if ev.asset_key.to_user_string() == "clean_orders"
        ),
        "—",
    )
    _rows = [
        {"check": ev.check_name, "passed": "✅" if ev.passed else "❌", "rows": ev.metadata.get("rows", ev.metadata.get("bad_rows")).value}
        for ev in _res.get_asset_check_evaluations()
    ]
    mo.vstack(
        [
            mo.callout(
                mo.md(
                    f"min_amount = {gate_min.value} → `clean_orders` 留下 **{_kept}** 列 → "
                    f"run **{'成功' if _res.success else '失敗'}**<br>實體化：`{_mats}`"
                ),
                kind="success" if _res.success else "danger",
            ),
            mo.ui.table(_rows, selection=None),
        ]
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 📌 回到開頭那個早上

    | 那時問不出答案的問題 | 現在的答案 |
    | --- | --- |
    | 特徵表什麼時候算的？ | 每次實體化都是一筆事件，時間、run id 都在 |
    | 用了哪一批資料、留下幾列？ | `add_output_metadata` 的中繼資料跟著那次實體化永久保存 |
    | 只重算特徵可以嗎？ | `selection=[customer_features]`，上游由 IO manager 載回 |
    | 資料壞掉會怎樣？ | blocking 的 asset check 直接擋住下游，模型不會拿到爛資料 |

    這四件事都不是靠「更小心一點」得到的，而是靠**換一種宣告方式**：
    你描述的是「有哪些資產、它們從誰來」，執行順序、重算範圍、血緣紀錄由 Dagster 推導。

    下一課會補上剩下的那一半：**這些資產什麼時候該重算**——排程、感測器、分割與自動化條件。
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 🏆 延伸挑戰

    1. **LEVEL 1**：加一個資產 `top_customers`：吃 `customer_features`，回傳 `total` 最高的 5 位。
       實體化整條線，確認它出現在血緣圖上、metadata 記了 5 列。
    2. **LEVEL 2**：幫 `customer_features` 加一個 `blocking=True` 的檢查：`return_rate` 必須在 0–1 之間且沒有 NaN。
       故意在 `raw_orders` 塞一筆 `returned=None` 看它擋不擋得住。
    3. **LEVEL 3**：把 `CsvIOManager` 改成**依資產決定格式**：DataFrame 存 CSV、其他型別存 pickle
       （提示：`handle_output` 裡看 `isinstance(obj, pd.DataFrame)`，`load_input` 看檔案副檔名）。
       驗證：`feature_report` 這種回傳 `MaterializeResult` 的資產不會經過 IO manager，
       而 `top_customers`（DataFrame）會變成 CSV。

    先自己試，卡住再展開下面的提示與參考解答。
    帶得走：下載本檔後 `uvx marimo edit --sandbox dagster-assets_ext.py`
    在自己電腦繼續玩（依賴會自動安裝）；把 `Definitions` 那格存成 `.py` 就能 `dagster dev -f` 開 UI。
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
    @dg.asset(group_name="features")
    def top_customers(context: dg.AssetExecutionContext, customer_features: pd.DataFrame) -> pd.DataFrame:
        top = customer_features.nlargest(5, "total")
        context.add_output_metadata({"rows": len(top), "top1": int(top.iloc[0]["customer"])})
        return top

    res = dg.materialize([raw_orders, clean_orders, customer_features, top_customers], run_config=QUIET)
    res.asset_value("top_customers")
    ```

    你應該看到 5 列、`total` 由大到小；把 `top_customers` 加進 `Definitions` 的 assets 後，
    血緣圖多一個節點掛在 `customer_features` 下面。
    """
            ),
            "💡 LEVEL 2 參考解答": mo.md(
                r"""
    ```python
    @dg.asset_check(asset=customer_features, blocking=True)
    def return_rate_valid(customer_features: pd.DataFrame) -> dg.AssetCheckResult:
        rr = customer_features["return_rate"]
        bad = int(rr.isna().sum() + ((rr < 0) | (rr > 1)).sum())
        return dg.AssetCheckResult(passed=bad == 0, severity=dg.AssetCheckSeverity.ERROR,
                                   metadata={"bad_rows": bad})
    ```

    正常資料會過。要讓它失敗，最簡單是在 `raw_orders` 回傳前加一行
    `df.loc[0, "returned"] = None`（`returned` 欄變成 object 型別、`mean()` 會把 None 當缺值→ 某位客戶的
    return_rate 變 NaN），或直接在 `customer_features` 回傳前把某列 `return_rate` 設成 1.5。
    失敗時 run 的 success 是 False、錯誤訊息是 `1 blocking asset check failed with ERROR severity: customer_features: return_rate_valid`。
    """
            ),
            "💡 LEVEL 3 提示": mo.md(
                r"""
    ```python
    def handle_output(self, context, obj):
        if isinstance(obj, pd.DataFrame):
            obj.to_csv(self._path(context, "csv"), index=False)
        else:
            with open(self._path(context, "pkl"), "wb") as f:
                pickle.dump(obj, f)

    def load_input(self, context):
        p_csv, p_pkl = self._path(context, "csv"), self._path(context, "pkl")
        return pd.read_csv(p_csv) if p_csv.exists() else pickle.load(open(p_pkl, "rb"))
    ```

    （`_path` 多收一個副檔名參數。）驗證方式：實體化後列出 root 目錄——DataFrame 資產是 `.csv`、
    LEVEL 1 若回傳的是 list 就會是 `.pkl`；`feature_report` 沒有檔案，因為 `MaterializeResult` 沒有輸出值，
    IO manager 根本不會被呼叫。
    """
            ),
        }
    )
    return


if __name__ == "__main__":
    app.run()
