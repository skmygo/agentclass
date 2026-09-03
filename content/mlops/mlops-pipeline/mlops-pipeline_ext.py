# Dagster × MLflow：一條會自己訓練、評估、把關、上線的管線（MLOps 系列壓軸）
# 不需要 GPU——molab 免費 CPU 環境即可全程執行（全部在本機檔案系統，不連任何伺服器）。
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "marimo",
#     "dagster>=1.10",
#     "mlflow>=3.0",
#     "scikit-learn",
#     "pandas",
#     "numpy",
#     "matplotlib",
#     "tabulate",
# ]
# ///
import marimo

__generated_with = "0.23.16"
app = marimo.App(width="medium", app_title="Dagster × MLflow：一條會自己訓練、評估、把關、上線的管線")


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    # 🏁 Dagster × MLflow：一條會自己訓練、評估、把關、上線的管線

    ## 這是系列的壓軸：把四堂課的零件接起來

    前四課你各學會一個零件，但它們現在還是四個分開的東西。先回頭看看，
    「沒有管線的日子」到底是哪四件事在痛：

    | 手動流程的痛 | 那一課給的答案 |
    | --- | --- |
    | 上週 AUC 0.95、今天 0.92，當時參數是什麼沒人記得 | **第 1 課**：每次訓練記成一個 MLflow run |
    | 最好的那個 run 存在某人的筆電上，上不了線 | **第 2 課**：Registry 給名字與版本，alias 一行切換線上版 |
    | 那份訓練資料是誰、什麼時候、用什麼算出來的？ | **第 3 課**：`@asset` 把資料與產生它的程式綁在一起 |
    | 誰來按下「執行」？半夜要有人守著嗎？ | **第 4 課**：排程、感測器、自動化條件 |

    這一課要做的事只有一件：**把它們接成一條線，而且讓這條線自己會擋人。**

    ## 我們要蓋的東西

    ```
    churn_data ──▶ train_test ──▶ trained_model ──▶ model_metrics ──▶ registered_champion
       資料           切分            訓練＋記進        一行評估          註冊新版 ＋
     （可注入漂移）                    MLflow run       8 個指標          移動 @champion
                                                          │
                                                          └─▶ quality_gate（品質閘）
                                                              AUC ≥ 0.95 而且不輸現任 champion
                                                              擋下來 → 下游整個不跑
    ```

    最右邊那個 `registered_champion` 就是「上線」：服務端永遠載
    `models:/churn-clf@champion`，這條線決定那個 alias 指到哪一版。
    中間那個 `quality_gate` 是本課的主角——**它是一個資產檢查（asset check），不是一個
    `if`**，差別在哪裡，第 5️⃣ 節會講到你以後再也不想用 `if` 寫閘門。

    ## 這份 notebook 帶你做完

    1. **MLflow 當 Dagster resource**：連線設定用注入的，換環境不改程式
    2. **資料資產**：`churn_data`（可以注入資料漂移）→ `train_test`
    3. **訓練資產**：在資產裡開 MLflow run，兩邊互相記下對方的 id（雙向可追溯）
    4. **評估資產**：`mlflow.models.evaluate` 一行，指標掛成 Dagster 中繼資料
    5. **品質閘**：blocking 的 `@asset_check`——為什麼閘門不能寫成 `if`
    6. **上線資產**：註冊新版、補記評估指標、移動 `champion` alias
    7. **跑四次，看四種劇情**：第一次上線 / 弱模型被擋 / 更強的晉升 / 資料漂移被擋
    8. **追溯**：從線上模型一路查回是哪一次 Dagster run 訓的，再反查回去
    9. **自動化收尾**：job ＋ 排程 ＋ 感測器 ＋ 自動化條件，收成一份 `Definitions`
    10. **互動**：拉桿選深度與漂移，按一下跑整條線，看閘門開或關

    全部在你自己的執行環境裡跑，**不連任何伺服器、不需要 GPU**：資料是合成的，
    MLflow 的帳本是一個 SQLite 檔，Dagster 的帳本是一個暫存資料夾。
    從第一格往下全部執行即可（首次安裝套件約 1–2 分鐘，之後五次管線執行合計約 1 分鐘上下）。
    """
    )
    return


@app.cell
def _():
    import datetime as dt
    import logging
    import shutil
    import tempfile
    import warnings
    from concurrent.futures import ThreadPoolExecutor
    from pathlib import Path

    import dagster as dg
    import marimo as mo
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import mlflow
    import numpy as np
    import pandas as pd
    from mlflow import MlflowClient
    from mlflow.exceptions import MlflowException
    from mlflow.models import infer_signature
    from sklearn.datasets import make_classification
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import train_test_split

    warnings.filterwarnings("ignore")
    logging.getLogger("mlflow").setLevel(logging.ERROR)

    # Dagster 每一步都會印日誌（正式部署時那些日誌會進 UI）；notebook 裡關掉，只留我們自己排版的輸出
    QUIET = {"loggers": {"console": {"config": {"log_level": "CRITICAL"}}}}

    # 這份 notebook 的工作目錄：MLflow 的資料庫與 artifacts 都放這裡，開頭清乾淨，重跑數字才一致
    WORK = Path(tempfile.gettempdir()) / "mlops-pipeline"
    shutil.rmtree(WORK, ignore_errors=True)
    WORK.mkdir(parents=True, exist_ok=True)

    TRACKING_URI = f"sqlite:///{WORK}/mlflow.db"   # Registry 只有資料庫後端才有（第 2 課踩過）
    EXPERIMENT = "churn-pipeline"
    MODEL_NAME = "churn-clf"                       # Registry 裡的名字，跟第 2 課同一個
    MIN_AUC = 0.95                                 # 品質閘的絕對門檻（挑戰題會請你改它）

    print("工作目錄：", WORK)
    print("tracking ：", TRACKING_URI)
    print("dagster  ：", dg.__version__, "| mlflow：", mlflow.__version__)
    return (
        EXPERIMENT,
        MIN_AUC,
        MODEL_NAME,
        MlflowClient,
        MlflowException,
        QUIET,
        RandomForestClassifier,
        ThreadPoolExecutor,
        TRACKING_URI,
        WORK,
        dg,
        dt,
        infer_signature,
        LogisticRegression,
        make_classification,
        mlflow,
        mo,
        np,
        pd,
        plt,
        train_test_split,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 1️⃣ MLflow 當成 Dagster 的 resource

    ### 為什麼「連線設定」不能寫死在資產裡

    第 4 課講過 **resource（資源）**：資產需要的「外部世界」——資料庫連線、S3 憑證、
    API 端點——不要寫死在函式裡，而是宣告成資源、由外面注入。

    MLflow 的 tracking server 正是這種東西。你的筆電上它是一個 SQLite 檔，
    正式環境是 `https://mlflow.公司內網`，CI 上又是另一個。如果每個資產裡都寫
    `mlflow.set_tracking_uri("sqlite:///…")`，換環境就要改程式碼——而且要改好幾處、
    改漏一處就會有 run 寫到錯的地方（第 5️⃣ 節結尾會看到這個錯有多安靜）。

    ### 這個 resource 做兩件事

    ```python
    class MlflowResource(dg.ConfigurableResource):
        tracking_uri: str
        experiment: str

        def setup(self):
            mlflow.set_tracking_uri(self.tracking_uri)     # 帳本記在哪
            ...
            mlflow.set_experiment(self.experiment)         # run 歸到哪個實驗
    ```

    `ConfigurableResource` 是 Pydantic 模型：欄位就是設定，型別會被檢查。
    每個需要 MLflow 的資產只要在參數列寫 `mlflow_res: MlflowResource`，Dagster 執行時
    自動把 `Definitions` 裡註冊的那一份塞進來。要換環境？改一行 `Definitions`，
    資產程式一個字都不用動。

    `artifact_location` 這裡也一併指定：MLflow 的模型檔案預設會落在你當下的工作目錄，
    我們把它們統一放進暫存資料夾，免得管線在專案裡到處拉屎。
    """
    )
    return


@app.cell
def _(EXPERIMENT, TRACKING_URI, WORK, dg, mlflow):
    class MlflowResource(dg.ConfigurableResource):
        """把「MLflow 記在哪、歸到哪個實驗」變成可注入的設定。"""

        tracking_uri: str
        experiment: str

        def setup(self) -> None:
            mlflow.set_tracking_uri(self.tracking_uri)
            if mlflow.get_experiment_by_name(self.experiment) is None:
                mlflow.create_experiment(self.experiment, artifact_location=str(WORK / "artifacts"))
            mlflow.set_experiment(self.experiment)

    MLFLOW_RES = MlflowResource(tracking_uri=TRACKING_URI, experiment=EXPERIMENT)
    RESOURCES = {"mlflow_res": MLFLOW_RES}

    MLFLOW_RES.setup()   # notebook 自己要查 Registry 時也用得到，先設一次
    print("experiment：", mlflow.get_experiment_by_name(EXPERIMENT).experiment_id, "|", EXPERIMENT)
    print("artifacts ：", WORK / "artifacts")
    return MLFLOW_RES, MlflowResource, RESOURCES


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 2️⃣ 資料資產：`churn_data` → `train_test`

    ### 一個 Config 欄位，就是這條管線的三個旋鈕

    ```python
    class TrainConfig(dg.Config):
        model: str = "rf"        # rf | logreg
        max_depth: int = 8       # 森林的深度
        drift: float = 0.0       # 模擬資料漂移：把特徵加上噪音
    ```

    `dg.Config`（第 4 課）是「這一次執行的參數」：不是資源（環境），也不是程式碼。
    同一份程式碼，`run_config` 給不同的值就是不同的實驗——**而且那些值會被記進
    run 的紀錄裡**，不會像改程式碼那樣改完就消失。

    `drift` 是本課的劇情裝置。真實世界的資料漂移是「上游換了感測器」「行銷活動改變了
    客群組成」；這裡用最單純的形式模擬：**在每個特徵上加高斯噪音**。標籤沒變、
    程式沒變、參數沒變，但模型學到的那條界線對不上新資料了——第 7️⃣ 節的第四次執行
    就是靠它把 AUC 打下來的。

    ### 兩個資產，一條依賴

    `train_test` 的參數名是 `churn_data`——第 3 課的規則：**參數名＝上游資產名**。
    你沒有寫任何「先跑誰再跑誰」，圖是從程式碼推出來的。
    """
    )
    return


@app.cell
def _(dg, make_classification, np, pd, train_test_split):
    class TrainConfig(dg.Config):
        model: str = "rf"
        max_depth: int = 8
        drift: float = 0.0

    @dg.asset(group_name="data", description="合成的客戶流失資料（drift > 0 時注入資料漂移）")
    def churn_data(context: dg.AssetExecutionContext, config: TrainConfig) -> pd.DataFrame:
        X, y = make_classification(n_samples=2000, n_features=12, n_informative=6, random_state=0)
        df = pd.DataFrame(X, columns=[f"f{i}" for i in range(12)])
        if config.drift > 0:
            rng = np.random.default_rng(1)
            df = df + rng.normal(0, config.drift, df.shape)     # 漂移＝特徵被噪音推走
        df["label"] = y
        context.add_output_metadata({"rows": len(df), "drift": config.drift})
        return df

    @dg.asset(group_name="data", description="固定切分（random_state=0），四次執行才比得起來")
    def train_test(context: dg.AssetExecutionContext, churn_data: pd.DataFrame) -> dict:
        tr, te = train_test_split(churn_data, test_size=0.25, random_state=0)
        context.add_output_metadata({"train_rows": len(tr), "test_rows": len(te)})
        return {"train": tr, "test": te}

    return TrainConfig, churn_data, train_test


@app.cell
def _(QUIET, churn_data, dg, mo):
    # 先單獨算一次資料資產，看看 drift 到底把資料推走多少（下面兩行是同一個資產、兩種 config）
    def _peek(drift: float) -> dict:
        _r = dg.materialize(
            [churn_data],
            run_config={**QUIET, "ops": {"churn_data": {"config": {"drift": drift}}}},
            raise_on_error=False,
        )
        _df = _r.asset_value("churn_data")
        return {
            "drift": drift,
            "rows": len(_df),
            "f0 平均": round(float(_df["f0"].mean()), 3),
            "f0 標準差": round(float(_df["f0"].std()), 3),
            "流失率": round(float(_df["label"].mean()), 3),
        }

    mo.vstack(
        [
            mo.md("同一個 `churn_data` 資產、兩種 `drift` 設定——**標籤沒變、列數沒變，變的是特徵的分布**："),
            mo.ui.table([_peek(0.0), _peek(1.5)], selection=None),
        ]
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 3️⃣ 訓練資產：在資產裡開一個 MLflow run

    ### 這一格是整條管線的縫合處

    第 1 課你手動 `with mlflow.start_run():`，第 3 課你手動 `@dg.asset`。
    把它們疊在一起就是這一格——但真正的關鍵是**兩邊互相記下對方的 id**：

    ```python
    with mlflow.start_run(run_name=f"dagster-{context.run_id[:8]}") as run:
        mlflow.log_params({..., "dagster_run": context.run_id})   # MLflow 這邊記住 Dagster
        info = mlflow.sklearn.log_model(clf, name="churn_model", signature=..., input_example=...)
        mlflow.set_tag("dagster.asset", "trained_model")

    context.add_output_metadata({"mlflow_run": run.info.run_id, "model_uri": info.model_uri})
    #                            ↑ Dagster 這邊記住 MLflow
    ```

    這叫**雙向可追溯**，而且兩個方向的用途完全不同：

    - **MLflow → Dagster**：有人看到線上模型怪怪的，從 Registry 查到那個 run，
      再從 `dagster_run` 參數查到「是哪一次執行、那次用的資料長什麼樣」。
    - **Dagster → MLflow**：資料工程師在 Dagster 這邊看到某次執行，
      能直接跳到那次訓練的指標與模型檔案。

    只記單向的話，總有一天你會站在錯的那一邊。

    ### 順手做對的兩件小事

    - **`signature=infer_signature(...)`**：第 2 課的合約。少一欄的輸入會被擋在模型外面，
      而不是進到 sklearn 裡爆出一個看不懂的錯。
    - **回傳 `info.model_uri`**：資產的「內容」是一個字串（`models:/m-…`），不是模型物件本身。
      模型檔案已經在 MLflow 那裡了，管線裡傳的是它的地址——下游要用就自己載。
    """
    )
    return


@app.cell
def _(
    LogisticRegression,
    MlflowResource,
    RandomForestClassifier,
    dg,
    infer_signature,
    mlflow,
    pd,
    TrainConfig,
):
    @dg.asset(group_name="model", description="訓練模型，並把這次訓練記成一個 MLflow run")
    def trained_model(
        context: dg.AssetExecutionContext,
        config: TrainConfig,
        mlflow_res: MlflowResource,
        train_test: dict,
    ) -> str:
        mlflow_res.setup()                       # 注入的連線設定：這一行決定 run 寫到哪裡
        _tr: pd.DataFrame = train_test["train"]
        _X, _y = _tr.drop(columns="label"), _tr["label"]
        clf = (
            RandomForestClassifier(n_estimators=100, max_depth=config.max_depth, random_state=0)
            if config.model == "rf"
            else LogisticRegression(max_iter=1000)
        )
        with mlflow.start_run(run_name=f"dagster-{context.run_id[:8]}") as run:
            mlflow.log_params(
                {"model": config.model, "max_depth": config.max_depth, "drift": config.drift,
                 "dagster_run": context.run_id}
            )
            clf.fit(_X, _y)
            info = mlflow.sklearn.log_model(
                clf,
                name="churn_model",
                signature=infer_signature(_X, clf.predict_proba(_X)[:, 1]),
                input_example=_X.head(3),
            )
            mlflow.set_tag("dagster.asset", "trained_model")

        context.add_output_metadata({"mlflow_run": run.info.run_id, "model_uri": info.model_uri})
        context.log.info(f"trained {config.model} → {info.model_uri}")
        return info.model_uri

    return (trained_model,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 4️⃣ 評估資產：一行 evaluate，指標同時進兩本帳

    第 2 課的 `mlflow.models.evaluate` 一行就產出 8 個指標與 5 張圖，全部記進當前的 run。
    這裡多做一件事：把其中幾個指標用 `add_output_metadata` **也**掛到 Dagster 的中繼資料上。

    為什麼要重複記？因為兩本帳的讀者不同。MLflow 的指標是給「比較實驗」用的
    （20 個 run 排序找最好的那個）；Dagster 的中繼資料是給「看管線」用的——
    在資產圖上一眼看到「這份 `model_metrics` 上次算出來 AUC 是多少」，
    不必跳到另一個系統。`dg.MetadataValue.float(...)` 讓它以數字型別存下來，
    UI 上還會畫出歷次的趨勢。

    注意這個資產同時吃 `trained_model`（一個 URI 字串）與 `train_test`（切好的資料），
    參數名各自對到上游——**評估用的是 test 那一半，訓練資產從來沒看過它**。
    """
    )
    return


@app.cell
def _(MlflowResource, dg, mlflow):
    @dg.asset(group_name="model", description="在 test 上評估模型，指標同時記進 MLflow 與 Dagster")
    def model_metrics(
        context: dg.AssetExecutionContext,
        mlflow_res: MlflowResource,
        trained_model: str,
        train_test: dict,
    ) -> dict:
        mlflow_res.setup()
        _te = train_test["test"]
        with mlflow.start_run(run_name="evaluate"):
            _res = mlflow.models.evaluate(trained_model, _te, targets="label", model_type="classifier")
        _keep = ("roc_auc", "accuracy_score", "f1_score", "recall_score", "precision_score")
        metrics = {k: float(v) for k, v in _res.metrics.items() if k in _keep}
        context.add_output_metadata({k: dg.MetadataValue.float(v) for k, v in metrics.items()})
        return metrics

    return (model_metrics,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 5️⃣ 品質閘：為什麼它是一個 asset check，不是一個 `if`

    ### 先看規則本身

    ```python
    @dg.asset_check(asset=model_metrics, blocking=True,
                    description="品質閘：AUC 必須 ≥ 0.95 而且不輸目前 champion")
    def quality_gate(mlflow_res: MlflowResource, model_metrics: dict) -> dg.AssetCheckResult:
        ...
        ok = auc >= MIN_AUC and auc >= champion_auc
        return dg.AssetCheckResult(passed=ok, metadata={"auc": ..., "champion_auc": ..., "min_auc": ...})
    ```

    兩道條件缺一不可：**絕對門檻**（不管以前多爛，低於 0.95 就是不准上線）
    ＋**相對門檻**（不能比現在線上那版還差）。第一次執行時 Registry 是空的，
    讀 champion 會拋 `Registered Model with name=churn-clf not found`——
    所以那裡包了 `try/except`，把「還沒有 champion」當成 `champion_auc = 0.0`。

    ### 那為什麼不寫成 `if`？

    你當然可以在 `registered_champion` 開頭寫 `if auc < 0.95: return "skip"`。
    但那樣做，你會失去四件事：

    | | 寫成 `if` | 寫成 blocking asset check |
    | --- | --- | --- |
    | 這次到底過了沒 | 埋在日誌裡，要翻 | 一筆**檢查結果**存進帳本，UI 上紅叉綠勾 |
    | 為什麼沒過 | 要自己 print | `metadata` 帶著 auc／champion_auc／門檻，永久保存 |
    | 下游會不會跑 | 你要自己在每個下游再判一次 | `blocking=True` 直接擋住**所有**下游 |
    | 整次執行算成功嗎 | 算成功（你自己 return 了） | run 標記為**失敗**，該叫的人會被叫 |

    最後一項最關鍵：閘門擋下來時，這次執行**必須**是失敗的。
    如果它算成功，你的監控就永遠不會響——一條「安靜地什麼都沒做」的管線，
    比一條會壞掉的管線危險得多。

    ### 一個容易漏掉的細節

    `dg.materialize()` **沒有** `asset_checks=` 參數：檢查要跟資產放在同一個 list 裡。
    忘了放的話，Dagster 不會提醒你——它只是靜靜地不跑那個檢查，然後 run 顯示成功。
    """
    )
    return


@app.cell
def _(MIN_AUC, MODEL_NAME, MlflowClient, MlflowException, MlflowResource, dg, mlflow, model_metrics):
    @dg.asset_check(
        asset=model_metrics,
        blocking=True,
        description=f"品質閘：AUC 必須 ≥ {MIN_AUC} 而且不輸目前的 champion",
    )
    def quality_gate(mlflow_res: MlflowResource, model_metrics: dict) -> dg.AssetCheckResult:
        mlflow_res.setup()
        _client = MlflowClient()
        try:
            _champ = _client.get_model_version_by_alias(MODEL_NAME, "champion")
            champion_auc = mlflow.get_run(_champ.run_id).data.metrics.get("eval_auc", 0.0)
        except MlflowException:                # 還沒有任何 champion：第一次執行的處境
            champion_auc = 0.0
        auc = model_metrics["roc_auc"]
        return dg.AssetCheckResult(
            passed=bool(auc >= MIN_AUC and auc >= champion_auc),
            severity=dg.AssetCheckSeverity.ERROR,   # ERROR ＋ blocking＝擋死下游、run 算失敗
            metadata={"auc": auc, "champion_auc": champion_auc, "min_auc": MIN_AUC},
        )

    return (quality_gate,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 6️⃣ 上線資產：註冊、補記指標、移動 alias

    這是整條線的最後一站，只有閘門放行才會執行到。三件事：

    ```python
    mv = mlflow.register_model(trained_model, MODEL_NAME)               # 1. 註冊成新版本
    client.log_metric(src_run, "eval_auc", model_metrics["roc_auc"])    # 2. 把評估 AUC 補記到訓練 run
    client.set_registered_model_alias(MODEL_NAME, "champion", mv.version)  # 3. 移動 alias＝上線
    client.set_model_version_tag(MODEL_NAME, mv.version, "dagster_run", context.run_id)
    ```

    **第 2 步是很多人會漏掉的一步。** 評估是在 `model_metrics` 那個資產裡做的，
    當時開的是另一個名叫 `evaluate` 的 run；而下一次執行時，品質閘要問的是
    「**現任 champion 當初考幾分**」——它拿到的是 champion 版本指向的**訓練 run**。
    如果沒把 `eval_auc` 補記到那個 run 上，閘門讀到的永遠是 `0.0`，
    相對門檻等於形同虛設：任何 AUC ≥ 0.95 的模型都能把 champion 換掉，包含比現任差的。

    這種錯誤不會報錯、不會噴紅字，只會讓你的品質閘默默失效——**最貴的 bug 都長這樣。**

    第 3 步之後，線上服務端那行 `mlflow.pyfunc.load_model("models:/churn-clf@champion")`
    一個字都不用改，下次載入就是新版。這就是第 2 課 alias 的用途，只是現在按下它的
    不是你的手，是管線。
    """
    )
    return


@app.cell
def _(MODEL_NAME, MlflowClient, MlflowResource, dg, mlflow):
    @dg.asset(group_name="deploy", description="註冊新版本並把 champion alias 移過去（＝上線）")
    def registered_champion(
        context: dg.AssetExecutionContext,
        mlflow_res: MlflowResource,
        trained_model: str,
        model_metrics: dict,
    ) -> str:
        mlflow_res.setup()
        client = MlflowClient()
        mv = mlflow.register_model(trained_model, MODEL_NAME)
        src_run = client.get_model_version(MODEL_NAME, mv.version).run_id
        client.log_metric(src_run, "eval_auc", model_metrics["roc_auc"])     # 讓下一次的閘門比得到
        client.set_registered_model_alias(MODEL_NAME, "champion", mv.version)
        client.set_model_version_tag(MODEL_NAME, mv.version, "dagster_run", context.run_id)
        context.add_output_metadata(
            {"version": int(mv.version), "auc": dg.MetadataValue.float(model_metrics["roc_auc"])}
        )
        return f"models:/{MODEL_NAME}@champion -> v{mv.version}"

    return (registered_champion,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ### 把五個資產與一個檢查收成一張圖

    第 3 課的 `Definitions` 是「這個專案有哪些東西」的清單。現在它收得比較多：
    五個資產、一個檢查、一份資源。下面把血緣圖畫出來——
    藍＝資料、橘＝模型、綠＝上線，虛線紅框是掛在 `model_metrics` 上的品質閘。
    """
    )
    return


@app.cell
def _(dg):
    def pipeline_mermaid(defs: dg.Definitions) -> str:
        """把 Definitions 的資產圖畫成 mermaid（節點顏色＝group，虛線紅框＝asset check）。"""
        graph = defs.resolve_asset_graph() if hasattr(defs, "resolve_asset_graph") else defs.get_asset_graph()
        keys = graph.get_all_asset_keys() if hasattr(graph, "get_all_asset_keys") else graph.all_asset_keys
        palette = {"data": "#4C72B0", "model": "#DD8452", "deploy": "#55A868"}
        lines = ["graph LR"]
        for k in sorted(keys, key=lambda k: k.to_user_string()):
            node = graph.get(k)
            name = k.to_user_string()
            lines.append(f'  {name}["{name}"]')
            lines.append(
                f"  style {name} fill:{palette.get(node.group_name, '#8172B3')},color:#fff,stroke:#1C2B33"
            )
            for p in node.parent_keys:
                lines.append(f"  {p.to_user_string()} --> {name}")
            for c in getattr(node, "check_keys", []):
                lines.append(f'  {c.name}{{{{"{c.name}"}}}}')
                lines.append(f"  style {c.name} fill:#fff,color:#C44E52,stroke:#C44E52,stroke-dasharray: 4 4")
                lines.append(f"  {name} -.-> {c.name}")
        return "\n".join(lines)

    return (pipeline_mermaid,)


@app.cell
def _(
    RESOURCES,
    churn_data,
    dg,
    mo,
    model_metrics,
    pipeline_mermaid,
    quality_gate,
    registered_champion,
    train_test,
    trained_model,
):
    PIPELINE = [churn_data, train_test, trained_model, model_metrics, registered_champion]
    CHECKS = [quality_gate]

    defs = dg.Definitions(assets=PIPELINE, asset_checks=CHECKS, resources=RESOURCES)
    mo.vstack(
        [
            mo.md(
                f"`Definitions` 收了 **{len(list(defs.assets))} 個資產**、"
                f"**{len(list(defs.asset_checks))} 個檢查**、"
                f"**{len(RESOURCES)} 份資源**（`mlflow_res`）。"
            ),
            mo.mermaid(pipeline_mermaid(defs)),
        ]
    )
    return CHECKS, PIPELINE, defs


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 7️⃣ 跑四次，看四種劇情

    接下來連跑四次，每次只改 `run_config` 裡的參數——程式碼一個字都不動。
    每次跑完會印三塊東西：

    1. **這次執行成功了嗎、實體化了哪些資產**（閘門擋下來時 `registered_champion` 會消失）
    2. **品質閘的中繼資料**：這次的 auc、現任 champion 的 auc、絕對門檻
    3. **Registry 目前長什麼樣**：哪些版本、`@champion` 指到誰

    先讀劇本再往下跑，會比較有感覺：

    | 執行 | 設定 | 預期 |
    | --- | --- | --- |
    | run 1 | RandomForest depth 8 | Registry 空的 → 只要過 0.95 就上線，成為 v1 |
    | run 2 | LogisticRegression | 分數不差，但**輸給現任 champion** → 被擋 |
    | run 3 | RandomForest depth 16 | 比 v1 好一點點 → 晉升 v2 |
    | run 4 | depth 16 ＋ drift 1.5 | 模型沒變差，是**資料變了** → 被絕對門檻擋下 |

    `raise_on_error=False` 讓失敗的執行回傳結果物件而不是拋例外，
    這樣我們才能把「為什麼失敗」排版出來給你看。
    """
    )
    return


@app.cell
def _(
    CHECKS,
    MLFLOW_RES,
    MODEL_NAME,
    MlflowClient,
    MlflowException,
    PIPELINE,
    QUIET,
    RESOURCES,
    dg,
    mlflow,
    mo,
):
    instance = dg.DagsterInstance.ephemeral()   # 這份 notebook 的 Dagster 帳本：四次執行都記在它裡面

    def run_pipeline(model: str = "rf", max_depth: int = 8, drift: float = 0.0):
        """跑一次完整管線（資產＋檢查），設定只透過 run_config 傳，不改程式碼。"""
        cfg = {"model": model, "max_depth": max_depth, "drift": drift}
        return dg.materialize(
            PIPELINE + CHECKS,                                  # 檢查要跟資產放同一個 list
            resources=RESOURCES,
            instance=instance,
            run_config={**QUIET, "ops": {a: {"config": cfg} for a in ("churn_data", "trained_model")}},
            raise_on_error=False,
        )

    def registry_rows() -> list[dict]:
        """目前 Registry 的樣子：每個版本是誰訓的、考幾分、alias 在誰身上。"""
        MLFLOW_RES.setup()
        client = MlflowClient()
        rows = []
        try:
            versions = client.search_model_versions(f"name='{MODEL_NAME}'")
        except MlflowException:                                   # 還沒有任何版本
            return rows
        for v in sorted(versions, key=lambda v: int(v.version)):
            mv = client.get_model_version(MODEL_NAME, v.version)      # search 回來的不帶 aliases，要再查一次
            run = mlflow.get_run(mv.run_id)
            rows.append(
                {
                    "version": int(mv.version),
                    "model": run.data.params.get("model", "—"),
                    "max_depth": run.data.params.get("max_depth", "—"),
                    "eval_auc": round(run.data.metrics.get("eval_auc", float("nan")), 4),
                    "alias": "@champion" if "champion" in mv.aliases else "",
                    "dagster_run": (mv.tags.get("dagster_run") or "")[:8],
                }
            )
        return rows

    def report(res, title: str):
        """把一次執行的結果排版成：狀態卡 ＋ 閘門中繼資料 ＋ Registry 現況。"""
        mats = [e.asset_key.to_user_string() for e in res.get_asset_materialization_events()]
        checks = [
            {"check": e.check_name, "passed": "✅ 通過" if e.passed else "❌ 擋下",
             **{k: (round(v.value, 4) if isinstance(v.value, float) else v.value) for k, v in e.metadata.items()}}
            for e in res.get_asset_check_evaluations()
        ]
        deployed = "registered_champion" in mats
        return mo.vstack(
            [
                mo.callout(
                    mo.md(
                        f"**{title}** — 執行結果 **{'成功' if res.success else '失敗'}**，"
                        f"實體化了 {len(mats)} 個資產<br>`{mats}`<br>"
                        + ("**champion 換人了。**" if deployed else "**沒有任何東西上線**（下游被閘門擋住）。")
                    ),
                    kind="success" if res.success else "danger",
                ),
                mo.md("品質閘的中繼資料："),
                mo.ui.table(checks, selection=None),
                mo.md("Registry 現況："),
                mo.ui.table(registry_rows() or [{"（Registry 還是空的）": "—"}], selection=None),
            ]
        )

    return instance, registry_rows, report, run_pipeline


@app.cell
def _(report, run_pipeline):
    res1 = run_pipeline(model="rf", max_depth=8)
    report(res1, "run 1 · RandomForest depth 8（Registry 還是空的）")
    return (res1,)


@app.cell
def _(report, res1, run_pipeline):
    _prev = res1.success                       # 引用 run 1 的結果，確保這一格排在它後面
    res2 = run_pipeline(model="logreg")
    report(res2, "run 2 · LogisticRegression（分數不差，但輸給現任 champion）")
    return (res2,)


@app.cell
def _(report, res2, run_pipeline):
    _prev = res2.success
    res3 = run_pipeline(model="rf", max_depth=16)
    report(res3, "run 3 · RandomForest depth 16（比 v1 好一點點）")
    return (res3,)


@app.cell
def _(report, res3, run_pipeline):
    _prev = res3.success
    res4 = run_pipeline(model="rf", max_depth=16, drift=1.5)
    report(res4, "run 4 · 同一個模型設定，但資料漂移了（drift 1.5）")
    return (res4,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ### 四次執行擺在一起看

    下圖把四次的 AUC 畫成長條：綠色＝閘門放行、紅色＝被擋。
    虛線是絕對門檻 0.95，灰色階梯是「當時現任 champion 的分數」——
    **一個模型要上線，長條必須同時高過虛線與階梯。**

    看懂這張圖，你就看懂了這條管線在做什麼判斷。
    """
    )
    return


@app.cell
def _(plt, res1, res2, res3, res4):
    def _row(res, label):
        _ev = next(iter(res.get_asset_check_evaluations()))
        _m = {k: v.value for k, v in _ev.metadata.items()}
        return {"label": label, "auc": _m["auc"], "champ": _m["champion_auc"], "passed": _ev.passed}

    _rows = [
        _row(res1, "1 · rf d8"),
        _row(res2, "2 · logreg"),
        _row(res3, "3 · rf d16"),
        _row(res4, "4 · drift 1.5"),
    ]
    _fig, _ax = plt.subplots(figsize=(6.4, 3.4))
    _x = range(len(_rows))
    _ax.bar(
        _x,
        [r["auc"] for r in _rows],
        color=["#55A868" if r["passed"] else "#C44E52" for r in _rows],
        width=0.58,
    )
    _ax.step(
        [-0.5, *[i + 0.5 for i in _x]],
        [_rows[0]["champ"], *[r["champ"] for r in _rows]],
        where="pre",
        color="#8899A6",
        lw=1.6,
        label="champion AUC at the time",
    )
    _ax.axhline(0.95, ls="--", lw=1.4, color="#1C2B33", label="min_auc = 0.95")
    for _i, _r in enumerate(_rows):
        _ax.text(_i, _r["auc"] + 0.004, f"{_r['auc']:.4f}", ha="center", fontsize=9)
    _ax.set_xticks(list(_x))
    _ax.set_xticklabels([r["label"] for r in _rows], fontsize=9)
    _ax.set_ylim(0.80, 1.0)
    _ax.set_ylabel("test ROC AUC")
    _ax.set_title("Four runs through the quality gate")
    _ax.legend(loc="lower left", fontsize=8)
    _ax.spines[["top", "right"]].set_visible(False)
    _fig
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ### 停下來想一下 run 4

    run 4 的模型設定跟 run 3 **一模一樣**——同樣的森林、同樣的深度、同樣的種子。
    程式碼沒動、參數沒動，AUC 卻掉了一大截。變的只有資料。

    這正是真實世界最常見的模型事故：沒有人改壞任何東西，是世界變了。
    如果沒有這道閘門，這個模型會安安靜靜地被推上線，然後你會在兩週後從業務端聽到
    「最近的名單怎麼都不準」。**閘門的價值不在於它擋下的那些模型，
    而在於你不必再靠運氣。**
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 8️⃣ 追溯：從線上模型查回那一次執行

    半夜有人問你：「現在線上跑的模型到底是誰、什麼時候、用什麼資料訓的？」
    有了雙向的 id，這題是三跳就到底的查詢：

    ```
    Registry 的 @champion  ──▶  MLflow run  ──▶  dagster_run 參數  ──▶  Dagster 那次執行
                                                                            │
                     ◀── materialization 的 mlflow_run 中繼資料 ◀────────────┘
    ```

    下面這一格把兩個方向都跑一次：先從 Registry 往回查到 Dagster 的 run id，
    再用那個 run id 去 Dagster 的帳本裡把當時 `trained_model` 留下的中繼資料撈出來，
    最後確認兩邊指的是**同一個 MLflow run**。

    在正式環境裡，這兩跳都是 UI 上的一個連結；能自己用 API 走一遍，
    你就知道那個連結底下是什麼。
    """
    )
    return


@app.cell
def _(MLFLOW_RES, MODEL_NAME, MlflowClient, dg, instance, mlflow, mo, res4):
    _prev = res4.success
    MLFLOW_RES.setup()
    _client = MlflowClient()

    # ── 方向一：Registry → MLflow → Dagster ──────────────────────────────
    _champ = _client.get_model_version_by_alias(MODEL_NAME, "champion")
    _champ_run = mlflow.get_run(_champ.run_id)
    _dagster_run_id = _champ_run.data.params["dagster_run"]
    _dg_run = instance.get_run_by_id(_dagster_run_id)

    # ── 方向二：Dagster 的帳本 → 當時那次 materialization 的中繼資料 → MLflow ──
    _records = instance.fetch_materializations(dg.AssetKey("trained_model"), limit=10).records
    _match = next((r for r in _records if r.run_id == _dagster_run_id), None)
    _meta = {k: v.value for k, v in _match.asset_materialization.metadata.items()} if _match else {}

    _same = _meta.get("mlflow_run") == _champ.run_id
    mo.vstack(
        [
            mo.md(
                f"""
    **方向一 · 從線上那一版往回查**

    | 問題 | 答案 |
    | --- | --- |
    | `models:/{MODEL_NAME}@champion` 是哪一版？ | **v{_champ.version}** |
    | 它是哪個 MLflow run 產出的？ | `{_champ.run_id[:12]}…` |
    | 那次用了什麼設定？ | `{ {k: v for k, v in _champ_run.data.params.items() if k != 'dagster_run'} }` |
    | 考了幾分（eval_auc）？ | **{_champ_run.data.metrics.get('eval_auc', float('nan')):.4f}** |
    | 是哪一次 Dagster 執行訓的？ | `{_dagster_run_id[:12]}…`（版本 tag 也記了：`{_champ.tags.get('dagster_run', '')[:12]}…`） |
    | 那次執行的狀態？ | **{_dg_run.status.value}** |

    **方向二 · 從 Dagster 的帳本往前查**

    `trained_model` 這個資產在帳本裡有 **{len(_records)} 次**實體化紀錄；
    找出 run id 是 `{_dagster_run_id[:8]}…` 的那一次，它當時掛的中繼資料是：

    - `mlflow_run` = `{_meta.get('mlflow_run', '—')[:12]}…`
    - `model_uri` = `{_meta.get('model_uri', '—')}`
    """
            ),
            mo.callout(
                mo.md(
                    f"兩個方向指到同一個 MLflow run：**{_same}** — 這條線上的每一份東西，"
                    "都可以在三十秒內回答「你是怎麼來的」。"
                ),
                kind="success" if _same else "warn",
            ),
        ]
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 9️⃣ 自動化收尾：讓這條線自己跑

    到目前為止，每一次執行都是你按的（`run_pipeline(...)`）。第 4 課的三種零件現在派上用場——
    它們要回答的是同一個問題的三種版本：**誰來按？**

    ### 先把資產打包成 job

    ```python
    train_job = dg.define_asset_job("nightly_train", selection=dg.AssetSelection.all())
    ```

    排程與感測器不會直接觸發「資產」，它們觸發的是 **job**（一組要一起跑的資產）。
    `AssetSelection.all()` 選全部；真實專案裡常見的是只選一部分
    （例如資料資產一天更新一次、訓練一週跑一次）。
    """
    )
    return


@app.cell
def _(dg, dt, mo, QUIET):
    train_job = dg.define_asset_job("nightly_train", selection=dg.AssetSelection.all())

    nightly_schedule = dg.ScheduleDefinition(
        name="nightly_train_schedule",
        job=train_job,
        cron_schedule="0 3 * * *",            # 每天凌晨三點
        execution_timezone="Asia/Taipei",     # 不寫的話預設是 UTC——第 4 課的時區陷阱
        run_config=QUIET,
    )

    _tick = nightly_schedule.evaluate_tick(
        dg.build_schedule_context(
            scheduled_execution_time=dt.datetime.combine(dt.date(2026, 9, 5), dt.time(3, 0))
        )
    )
    mo.md(
        f"""
    `nightly_train_schedule` 在 2026-09-05 03:00 這個 tick 會送出
    **{len(_tick.run_requests)} 張 RunRequest**（一張「請跑這個 job」的單子），
    job 名稱 `{train_job.name}`、時區 `{nightly_schedule.execution_timezone}`。

    `evaluate_tick()` 是在問排程：「假設那個時刻到了，你會發什麼？」——
    不用啟動任何背景服務就看得到答案。
    """
    )
    return nightly_schedule, train_job


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ### 排程之外：新資料一到就重訓

    每天凌晨三點跑，代表最壞的情況下新資料要等 24 小時才會被用到。
    **感測器（sensor）**換一種問法：不是「時間到了嗎」，而是「有事情發生嗎」。

    下面這個感測器盯著一個「收件匣」資料夾，用 **cursor** 記住上次看到幾個檔案——
    cursor 是感測器唯一的記憶，沒有它就會每一 tick 都把同一批資料重跑一次。
    三個 tick 依序示範：沒有新檔案 → 放進一個新檔案 → 同一批資料不重複觸發。
    """
    )
    return


@app.cell
def _(QUIET, WORK, dg, instance, mo, train_job):
    INBOX = WORK / "inbox"
    INBOX.mkdir(exist_ok=True)

    @dg.sensor(name="new_data_sensor", job=train_job, minimum_interval_seconds=30)
    def new_data_sensor(context: dg.SensorEvaluationContext):
        seen = int(context.cursor) if context.cursor else 0
        files = sorted(INBOX.glob("*.csv"))
        if len(files) > seen:
            context.update_cursor(str(len(files)))
            yield dg.RunRequest(run_key=f"batch-{len(files)}", run_config=QUIET)
        else:
            yield dg.SkipReason(f"沒有新資料（已處理 {seen} 批）")

    _t0 = new_data_sensor.evaluate_tick(dg.build_sensor_context(instance=instance, cursor=None))
    (INBOX / "2026-09-05.csv").write_text("customer,amount\n1,300\n")      # 新資料進來了
    _t1 = new_data_sensor.evaluate_tick(dg.build_sensor_context(instance=instance, cursor=_t0.cursor))
    _t2 = new_data_sensor.evaluate_tick(dg.build_sensor_context(instance=instance, cursor=_t1.cursor))

    mo.ui.table(
        [
            {"tick": "1 · 收件匣是空的", "RunRequest": [r.run_key for r in _t0.run_requests] or "—",
             "SkipReason": _t0.skip_message or "—", "cursor": _t0.cursor or "—"},
            {"tick": "2 · 放進一個新檔案", "RunRequest": [r.run_key for r in _t1.run_requests] or "—",
             "SkipReason": _t1.skip_message or "—", "cursor": _t1.cursor or "—"},
            {"tick": "3 · 沒有更新的檔案", "RunRequest": [r.run_key for r in _t2.run_requests] or "—",
             "SkipReason": _t2.skip_message or "—", "cursor": _t2.cursor or "—"},
        ],
        selection=None,
    )
    return (new_data_sensor,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ### 第三種：資產自己說什麼時候該更新

    排程與感測器都是「從外面推」。**自動化條件（AutomationCondition）**反過來——
    寫在資產自己身上：「我的上游一更新，我就該重算」。這裡掛兩個：

    ```python
    @dg.asset(automation_condition=dg.AutomationCondition.eager())
    def data_profile(churn_data: pd.DataFrame) -> dict: ...          # 有新資料就重出資料剖析

    @dg.asset(automation_condition=dg.AutomationCondition.eager())
    def champion_scorecard(registered_champion: str) -> str: ...     # champion 換人就重出成績單
    ```

    下面在一本**乾淨的帳本**上跑一次管線（用預設設定 rf depth 8，它會輸給現在的 champion
    而被閘門擋下），然後連問三個 tick。三件事值得盯：

    1. **第一個 tick 一定是 0**：評估器要先有一個基準，之後才知道「什麼是新的」。正式環境的
       daemon 一直在跑、基準早就有了；在 notebook 裡要自己先打一次基準 tick，
       否則你會看到「明明剛跑完卻沒人舉手」而以為壞掉了。
    2. **`data_profile` 舉手**：它的上游 `churn_data` 剛更新過。
    3. **`champion_scorecard` 不動**：它的上游 `registered_champion` 被閘門擋住、這次根本沒有產出。
       **閘門擋下的不只是這一次執行的下游，連自動化都跟著停在那裡**——這是品質閘最容易被低估的一面。

    一個 notebook 專屬的小手續（第 4 課也踩過）：`evaluate_automation_conditions()` 內部會呼叫
    `asyncio.run()`，而 notebook 的格子本來就跑在事件迴圈裡，直接呼叫會得到
    `RuntimeError: asyncio.run() cannot be called from a running event loop`
    ——丟到另一個執行緒跑就好。寫成一般的 `.py` 腳本時不需要這一層。
    """
    )
    return


@app.cell
def _(
    CHECKS,
    PIPELINE,
    QUIET,
    RESOURCES,
    ThreadPoolExecutor,
    dg,
    mo,
    pd,
    registered_champion,
):
    @dg.asset(
        group_name="deploy",
        description="有新資料就重出的資料剖析",
        automation_condition=dg.AutomationCondition.eager(),
    )
    def data_profile(churn_data: pd.DataFrame) -> dict:
        return {"rows": len(churn_data), "churn_rate": round(float(churn_data["label"].mean()), 3)}

    @dg.asset(
        group_name="deploy",
        description="champion 換人就重出一份成績單",
        automation_condition=dg.AutomationCondition.eager(),
    )
    def champion_scorecard(registered_champion: str) -> str:
        return f"scorecard for {registered_champion}"

    _defs_auto = dg.Definitions(
        assets=[*PIPELINE, data_profile, champion_scorecard], asset_checks=CHECKS, resources=RESOURCES
    )
    _inst_auto = dg.DagsterInstance.ephemeral()      # 乾淨的帳本：這一節的評估不受前面四次執行影響

    def _evaluate(**kwargs):
        # 在 notebook（事件迴圈）裡安全地評估自動化條件：丟到另一個執行緒跑
        with ThreadPoolExecutor(max_workers=1) as pool:
            return pool.submit(lambda: dg.evaluate_automation_conditions(**kwargs)).result()

    _t0 = _evaluate(defs=_defs_auto, instance=_inst_auto)                       # 基準 tick
    _run = dg.materialize(
        PIPELINE + CHECKS, resources=RESOURCES, instance=_inst_auto, run_config=QUIET, raise_on_error=False
    )
    _t1 = _evaluate(defs=_defs_auto, instance=_inst_auto, cursor=_t0.cursor)    # 管線跑完之後
    _t2 = _evaluate(defs=_defs_auto, instance=_inst_auto, cursor=_t1.cursor)    # 沒有新事件了

    _mats = [e.asset_key.to_user_string() for e in _run.get_asset_materialization_events()]
    _rows = [
        {
            "tick": label,
            "data_profile": t.get_num_requested(dg.AssetKey("data_profile")),
            "champion_scorecard": t.get_num_requested(dg.AssetKey("champion_scorecard")),
            "總共要求": t.total_requested,
        }
        for label, t in (("0 · 基準", _t0), ("1 · 管線跑完之後", _t1), ("2 · 沒有新事件", _t2))
    ]
    mo.vstack(
        [
            mo.md(
                f"這一次管線**{'通過閘門' if _run.success else '被閘門擋下'}**，"
                f"實體化的資產是 `{_mats}`。三個 tick 各自要求了幾次實體化："
            ),
            mo.ui.table(_rows, selection=None),
            mo.callout(
                mo.md(
                    "`data_profile` 的上游是剛更新過的 `churn_data`，所以它舉手；"
                    "`champion_scorecard` 的上游 `registered_champion` 被閘門擋住、這次沒有產出，"
                    "所以它安靜。**你沒有寫任何排程，它們自己知道該不該動。**"
                ),
                kind="info",
            ),
        ]
    )
    return champion_scorecard, data_profile


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ### 全部收成一份 `Definitions`

    最後把所有東西收進同一份宣告：五個管線資產＋兩個自動更新的衍生資產、一個檢查、
    一份資源、一個 job、一個排程、一個感測器。

    這份 `Definitions` 就是「這條管線的全部」。在自己的專案裡把它存成 `definitions.py`，
    然後 `dagster dev`——瀏覽器打開就是資產圖、每個資產的實體化歷史、
    檢查的紅叉綠勾、排程與感測器的開關。**這一格之後，這條線就不需要你了。**
    """
    )
    return


@app.cell
def _(
    CHECKS,
    PIPELINE,
    RESOURCES,
    champion_scorecard,
    data_profile,
    dg,
    mo,
    new_data_sensor,
    nightly_schedule,
    pipeline_mermaid,
    train_job,
):
    production_defs = dg.Definitions(
        assets=[*PIPELINE, data_profile, champion_scorecard],
        asset_checks=CHECKS,
        resources=RESOURCES,
        jobs=[train_job],
        schedules=[nightly_schedule],
        sensors=[new_data_sensor],
    )
    mo.vstack(
        [
            mo.md(
                f"""
    | 收了什麼 | 數量 | 內容 |
    | --- | --- | --- |
    | 資產 | {len(list(production_defs.assets))} | `churn_data` → `train_test` → `trained_model` → `model_metrics` → `registered_champion`，外加 `data_profile`／`champion_scorecard` |
    | 資產檢查 | {len(list(production_defs.asset_checks))} | `quality_gate`（blocking） |
    | 資源 | {len(RESOURCES)} | `mlflow_res` |
    | job／排程／感測器 | {len(list(production_defs.jobs))} / {len(list(production_defs.schedules))} / {len(list(production_defs.sensors))} | `nightly_train`、每天 03:00、收件匣感測器 |
    """
            ),
            mo.mermaid(pipeline_mermaid(production_defs)),
        ]
    )
    return (production_defs,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 🔟 互動：自己跑一次這條線

    拉桿選森林深度與資料漂移，按下按鈕就跑一次完整管線（資產＋檢查），
    然後看兩件事：**閘門過了沒**、**champion 換人了沒**。

    幾個值得試的組合（括號裡是實測 AUC，前提是你還沒把 champion 換掉——現任是 0.9698 的 v2）：

    - **深度 2、漂移 0**（0.9297）：模型太淺，連 0.95 都摸不到——**絕對門檻**擋。
    - **深度 4、漂移 0**（0.9551）：過了 0.95，卻輸給現任 champion——**相對門檻**擋。
      這兩個被擋的理由完全不同，看閘門 metadata 裡的 `min_auc` 與 `champion_auc` 就知道是誰擋的。
    - **深度 12、漂移 0**（0.9725）：比現任更好 → 通過，Registry 多一版、champion 換人。
    - **深度 16 以上、漂移 0**（0.9698）：跟現任打平——`>=` 的比較讓它剛好過關，
      想想看你的團隊要不要接受「打平就換」。
    - **深度 16、漂移 0.25**（0.9739）：**噪音反而讓分數更好看**——所以閘門看的是分數，
      不是「有沒有漂移」；真正該監控漂移的地方在管線的另一端（那是另一堂課的題目）。
    - **深度 16、漂移 0.75 以上**（0.9366 以下）：資料變得太多，什麼模型都救不回來。

    注意這是**真的在跑**：閘門放行時，Registry 會多一版、`@champion` 真的會移過去，
    下一次執行的相對門檻也會跟著提高。你在跟自己剛剛的成績賽跑。
    """
    )
    return


@app.cell
def _(mo):
    depth_slider = mo.ui.slider(2, 24, step=2, value=8, label="max_depth", show_value=True)
    drift_slider = mo.ui.slider(0.0, 2.0, step=0.25, value=0.0, label="drift", show_value=True)
    go_button = mo.ui.run_button(label="跑一次管線")
    mo.hstack([depth_slider, drift_slider, go_button], wrap=True, justify="start")
    return depth_slider, drift_slider, go_button


@app.cell
def _(depth_slider, drift_slider, go_button, mo, registry_rows, run_pipeline):
    mo.stop(not go_button.value, mo.md("*選好 `max_depth` 與 `drift`，按「跑一次管線」。*"))

    _before = {r["version"]: r["alias"] for r in registry_rows()}
    _champ_before = next((v for v, a in _before.items() if a), None)
    _res = run_pipeline(model="rf", max_depth=depth_slider.value, drift=drift_slider.value)
    _rows = registry_rows()
    _champ_after = next((r["version"] for r in _rows if r["alias"]), None)

    _ev = next(iter(_res.get_asset_check_evaluations()))
    _m = {k: v.value for k, v in _ev.metadata.items()}
    _verdict = (
        f"champion：v{_champ_before} → **v{_champ_after}**（換人了）"
        if _champ_after != _champ_before
        else f"champion 仍然是 **v{_champ_after}**（沒有換）"
    )
    mo.vstack(
        [
            mo.callout(
                mo.md(
                    f"`max_depth={depth_slider.value}`、`drift={drift_slider.value}` → "
                    f"AUC **{_m['auc']:.4f}**（門檻 {_m['min_auc']}，現任 champion {_m['champion_auc']:.4f}）<br>"
                    f"品質閘 **{'✅ 通過' if _ev.passed else '❌ 擋下'}** ｜ {_verdict}"
                ),
                kind="success" if _ev.passed else "danger",
            ),
            mo.ui.table(_rows, selection=None),
        ]
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 🏆 延伸挑戰

    1. **LEVEL 1 · 把門檻拉高**：把 `MIN_AUC` 改成 `0.97`，重建一個空的 Registry，
       再跑一次 run 1（rf depth 8，AUC 約 0.968）。它應該再也上不了線——
       **確認 `registered_champion` 從實體化清單裡消失了**。
    2. **LEVEL 2 · 加第二道閘**：再寫一個 blocking 檢查 `recall_gate`（recall ≥ 0.9），
       跟 `quality_gate` 掛在同一個資產上。用 LogisticRegression 跑一次
       （它的 recall 約 0.86）看它被哪一道擋下來——注意**兩個檢查都要放進
       `materialize` 的清單裡**，漏掉的那個會靜靜地不執行。
    3. **LEVEL 3 · 一天一片**：把 `churn_data` 改成分割資產
       （`dg.DailyPartitionsDefinition(start_date="2026-09-01")`），讓每天只訓當天的資料。
       方向：資產加 `partitions_def=`、在函式裡用 `context.partition_key` 決定資料範圍、
       job 也要帶同一個 `partitions_def`，再用第 4 課的
       `build_schedule_from_partitioned_job(job, hour_of_day=3)` 產生排程。
       **怎麼驗證自己做對了**：`materialize(..., partition_key="2026-09-02")` 跑得起來、
       MLflow 那邊多一個參數記著是哪一片、`daily_schedule.evaluate_tick(...)` 送出的
       `RunRequest` 帶的是 `partition_key` 而不是 run_config。

    先自己試，卡住再展開下面的參考解答。
    帶得走：下載本檔後 `uvx marimo edit --sandbox mlops-pipeline_ext.py`
    在自己電腦繼續玩（依賴會自動安裝）。
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.accordion(
        {
            "💡 LEVEL 1 參考解答": mo.md(
                r"""
    門檻是 `quality_gate` 讀的常數，改了要**重新定義那個檢查**（marimo 會自動重跑下游的格子）。
    Registry 要清空才看得到「第一次上線」的處境，最乾淨的做法是換一個模型名字：

    ```python
    MIN_AUC = 0.97                      # 原本 0.95
    MODEL_NAME = "churn-clf-strict"     # 換個名字＝一個乾淨的 Registry

    res = run_pipeline(model="rf", max_depth=8)
    print(res.success, [e.asset_key.to_user_string() for e in res.get_asset_materialization_events()])
    ```

    你應該看到：`False`、清單裡只有 `churn_data`／`train_test`／`trained_model`／`model_metrics`，
    **沒有 `registered_champion`**；檢查的中繼資料是 `auc≈0.968、min_auc=0.97`。
    模型沒有變差，是你把標準提高了——這一格的重點是體會「門檻是一個決策，不是一個常識」。
    """
            ),
            "💡 LEVEL 2 參考解答": mo.md(
                r"""
    ```python
    @dg.asset_check(asset=model_metrics, blocking=True, description="recall 不得低於 0.9")
    def recall_gate(model_metrics: dict) -> dg.AssetCheckResult:
        recall = model_metrics["recall_score"]
        return dg.AssetCheckResult(
            passed=bool(recall >= 0.9),
            severity=dg.AssetCheckSeverity.ERROR,
            metadata={"recall": recall, "min_recall": 0.9},
        )

    res = dg.materialize(
        PIPELINE + [quality_gate, recall_gate],      # ← 兩個檢查都要放進來
        resources=RESOURCES, instance=instance,
        run_config={**QUIET, "ops": {a: {"config": {"model": "logreg"}} for a in ("churn_data", "trained_model")}},
        raise_on_error=False,
    )
    for e in res.get_asset_check_evaluations():
        print(e.check_name, e.passed, {k: v.value for k, v in e.metadata.items()})
    ```

    LogisticRegression 的 recall 約 0.86 → `recall_gate` 擋下（`quality_gate` 也會擋，
    因為它輸給現任 champion）。想看**只有 recall 被擋**的情形，把 `MODEL_NAME` 換成新名字
    讓 Registry 淨空，這樣 `quality_gate` 只剩絕對門檻 0.95（logreg 的 AUC 約 0.951 剛好過）。

    把其中一個檢查從清單裡拿掉再跑一次：run 照樣「成功」，那道閘門靜靜地沒執行——
    這就是第 5️⃣ 節說的「Dagster 不會提醒你」。
    """
            ),
            "💡 LEVEL 3 提示": mo.md(
                r"""
    三個地方要一起改，少一個就會出現「分割資產不能被非分割的 job 選到」這類錯誤：

    ```python
    daily = dg.DailyPartitionsDefinition(start_date="2026-09-01")

    @dg.asset(partitions_def=daily, group_name="data")
    def churn_data(context: dg.AssetExecutionContext, config: TrainConfig) -> pd.DataFrame:
        day = context.partition_key                  # "2026-09-02"
        seed = int(day.replace("-", "")) % 10_000    # 讓每一片資料真的不一樣
        ...

    # 下游資產也要帶同一個 partitions_def，job 同理
    daily_job = dg.define_asset_job("daily_train", selection=..., partitions_def=daily)
    daily_schedule = dg.build_schedule_from_partitioned_job(daily_job, hour_of_day=3)
    ```

    **怎麼驗證自己做對了**（三個都要成立）：

    1. `dg.materialize([...], partition_key="2026-09-02", ...)` 跑得起來，
       而不給 `partition_key` 會直接報錯。
    2. MLflow 那邊：把 `context.partition_key` 也 `log_param` 進去，
       在 run 列表裡看得到每一片是分開記的。
    3. `daily_schedule.evaluate_tick(dg.build_schedule_context(scheduled_execution_time=...))`
       送出的 `RunRequest` 帶的是 `partition_key`（第 4 課實測：03:00 的 tick 處理的是**前一天**那片），
       不是 run_config。

    陷阱提醒：品質閘讀的 champion 是**全域**的一份，分割之後你要先想清楚
    「每一片各自跟誰比」——這個設計問題沒有標準答案，正是它值得當 LEVEL 3 的原因。
    """
            ),
        }
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 📌 系列總結：四堂課的零件，各自站在哪裡

    | 課 | 你學到的零件 | 在這條線上的位置 |
    | --- | --- | --- |
    | **01** MLflow 實驗追蹤 | run、params、metrics、tags | `trained_model` 裡的 `start_run` 與 `log_params`——每次訓練都留下證據 |
    | **02** Models 與 Registry | `log_model`、signature、register、alias、`evaluate` | `trained_model` 打包模型、`model_metrics` 一行評估、`registered_champion` 移動 `@champion` |
    | **03** 軟體定義資產 | `@asset`、依賴成圖、中繼資料、asset check | 整條資產鏈，以及擋在中間的 `quality_gate` |
    | **04** Dagster 自動化 | resource、Config、job、排程、感測器、自動化條件 | `MlflowResource` 注入設定、`TrainConfig` 給參數、`nightly_train` ＋ 排程 ＋ 感測器負責「誰來按」 |

    ### 這條線真正改變的事

    一開始那四個問題，現在都有了不需要靠記性的答案：

    - 「當時參數是什麼？」→ 每一版都查得到，連是哪一次執行訓的都查得到。
    - 「最好的那版怎麼上線？」→ 閘門放行時 alias 自己移過去，服務端一個字不用改。
    - 「資料是誰算的？」→ 血緣圖上一路往上游看。
    - 「誰來按執行？」→ 排程、感測器、自動化條件，三選一或全都要。

    而最重要的那件事，是**它會擋人**：run 2 的弱模型與 run 4 的漂移資料，
    都沒有走到最後一步。一條會自己跑的管線很容易做，
    **一條會自己說「不」的管線，才是 MLOps。**

    ### 接下來

    這條線還有很多可以長的東西：模型上線之後怎麼提供服務、怎麼監控線上資料漂移、
    超參數搜尋怎麼接進來、資料品質怎麼在進管線前就驗好。
    課程主題頁上會陸續放出這些課——先把這條線搬進你自己的專案，
    換成你真的在用的資料，會比任何一堂課都學得多。
    """
    )
    return


if __name__ == "__main__":
    app.run()
