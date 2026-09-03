# MLflow Models 與 Model Registry：從最好的 run 到線上那一版
# 不需要 GPU——molab 免費 CPU 環境即可全程執行（全部在本機檔案系統，不連任何伺服器）。
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "marimo",
#     "mlflow>=3.0",
#     "scikit-learn",
#     "pandas",
#     "numpy",
#     "matplotlib",
# ]
# ///
import marimo

__generated_with = "0.23.16"
app = marimo.App(width="medium", app_title="MLflow Models 與 Model Registry：從最好的 run 到線上那一版")


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    # 📦 MLflow Models 與 Model Registry：從最好的 run 到線上那一版

    上一課你有了一本紀錄簿，知道哪個 run 最好。但「最好的 run」離「線上那一版」還差三件事：

    1. **模型要能被別人載入**——不是一個只有你電腦上才能 unpickle 的檔案，而是**模型＋輸入輸出規格＋環境需求**打包在一起。這是 **MLflow Model**。
    2. **要有一個大家都認得的名字與版本**——「客服流失模型 v3」，而不是「那個 run id 開頭 9a4d 的」。這是 **Model Registry**。
    3. **上線那一版要能一行切換**——今天 v3 當家、明天回滾 v2，服務程式不用改。這是 **alias**（`@champion`）。

    這份 notebook 帶你做完：

    1. MLflow Model 是什麼：`log_model` 打包了哪些檔案、`MLmodel` 說明書、flavor
    2. Signature 是合約：載回來推論；少一欄、型別錯會發生什麼
    3. Registry：註冊、版本、alias、晉升、回滾
    4. 評估：`mlflow.models.evaluate` 一行產出 8 個指標＋5 張圖，兩個版本並排
    5. 自訂 pyfunc：把前後處理跟模型包成一個部署單位
    6. 資料版本：`log_input` 讓 run 記得「用哪份資料訓的」
    7. 互動：切 alias、拉門檻，看線上模型的預測怎麼變

    從第一格往下全部執行即可（首次安裝套件約 1–2 分鐘）。
    """
    )
    return


@app.cell
def _():
    import logging
    import os
    import pickle
    import shutil
    import tempfile
    import warnings
    from pathlib import Path

    import marimo as mo
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import mlflow
    import numpy as np
    import pandas as pd
    from mlflow import MlflowClient
    from mlflow.models import infer_signature
    from sklearn.datasets import make_classification
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import roc_auc_score
    from sklearn.model_selection import train_test_split

    logging.getLogger("mlflow").setLevel(logging.ERROR)
    warnings.filterwarnings("ignore")
    return (
        LogisticRegression,
        MlflowClient,
        Path,
        RandomForestClassifier,
        infer_signature,
        make_classification,
        mlflow,
        mo,
        np,
        os,
        pd,
        pickle,
        plt,
        roc_auc_score,
        shutil,
        tempfile,
        train_test_split,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 0️⃣ 準備：同一份資料、一本新的紀錄簿

    跟上一課一樣的模擬「客戶流失」資料（2000 筆、12 個特徵 `f0`–`f11`），這次特徵有名字——
    **signature 會用到欄位名**。紀錄簿一樣是 SQLite；Model Registry **需要資料庫後端**，
    純資料夾模式（`./mlruns`）會在 `register_model` 時報錯。
    """
    )
    return


@app.cell
def _(Path, make_classification, mlflow, mo, pd, shutil, tempfile, train_test_split):
    WORK = Path(tempfile.gettempdir()) / "mlflow-registry-lesson"
    shutil.rmtree(WORK, ignore_errors=True)
    WORK.mkdir(parents=True)
    mlflow.set_tracking_uri(f"sqlite:///{WORK / 'mlflow.db'}")
    mlflow.create_experiment("churn-models", artifact_location=str(WORK / "artifacts"))
    mlflow.set_experiment("churn-models")

    _X, _y = make_classification(n_samples=2000, n_features=12, n_informative=6, random_state=0)
    FEATURES = [f"f{i}" for i in range(12)]
    X_train, X_test, y_train, y_test = train_test_split(
        pd.DataFrame(_X, columns=FEATURES), _y, test_size=0.25, random_state=0
    )
    mo.md(
        f"tracking URI `{mlflow.get_tracking_uri()}`；train {len(X_train)} 筆／test {len(X_test)} 筆，"
        f"欄位 `{FEATURES[0]}`…`{FEATURES[-1]}`"
    )
    return FEATURES, WORK, X_test, X_train, y_test, y_train


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 1️⃣ MLflow Model：模型＋規格＋環境，一個資料夾

    `mlflow.sklearn.log_model(model, name=..., signature=..., input_example=...)` 不只是存 pickle。
    它產生一個**資料夾**，裡面有：

    - `MLmodel`：說明書（YAML）——這個模型有哪些 **flavor**、輸入輸出 **signature**、用哪個 Python／套件版本
    - `model.skops`（或 `model.pkl`）：模型本體
    - `requirements.txt`／`python_env.yaml`／`conda.yaml`：重建環境用
    - `input_example.json`：一筆範例輸入，部署時拿來冒煙

    **flavor** 是「這個模型可以用哪些方式載入」：`sklearn` flavor 載回來是原生的 scikit-learn 物件；
    `python_function`（pyfunc）flavor 是**統一介面**——不管底層是 sklearn、PyTorch 還是 XGBoost，
    都是 `load_model(uri).predict(DataFrame)`。部署工具只認 pyfunc，所以幾乎每個 flavor 都附帶它。

    MLflow 3 把模型升格成一級公民：每次 `log_model` 產生一個 **LoggedModel**（id `m-…`），
    有自己的 URI `models:/m-…`，指標可以直接掛在模型上，不必再翻 run。
    """
    )
    return


@app.cell
def _(LogisticRegression, X_test, X_train, infer_signature, mlflow, roc_auc_score, y_test, y_train):
    v1_model = LogisticRegression(max_iter=1000).fit(X_train, y_train)
    v1_signature = infer_signature(X_train, v1_model.predict_proba(X_train)[:, 1])   # 輸入：12 欄 double；輸出：一個 double

    with mlflow.start_run(run_name="v1-logreg") as v1_run:
        v1_info = mlflow.sklearn.log_model(
            v1_model,
            name="churn_model",
            signature=v1_signature,
            input_example=X_train.head(3),
        )
        v1_auc = roc_auc_score(y_test, v1_model.predict_proba(X_test)[:, 1])
        mlflow.log_metric("auc", v1_auc)
    return v1_auc, v1_info, v1_model, v1_run, v1_signature


@app.cell
def _(Path, WORK, mlflow, mo, os, v1_info, v1_signature):
    _dir = mlflow.artifacts.download_artifacts(v1_info.model_uri, dst_path=str(WORK / "download-v1"))
    _mlmodel = (Path(_dir) / "MLmodel").read_text()
    _keep = [ln for ln in _mlmodel.splitlines() if not ln.startswith(("saved_input_example_info", "  artifact_path: input", "  pandas_orient", "  serving_input_path", "  type: dataframe", "signature:", "  inputs:", "  outputs:", "  params:"))]
    mo.md(
        f"""
    - `model_uri`：`{v1_info.model_uri}`（LoggedModel id `{v1_info.model_id}`）
    - flavors：`{list(v1_info.flavors)}`
    - 資料夾內容：`{sorted(os.listdir(_dir))}`

    signature（`infer_signature` 從訓練資料推出來的）：

    ```text
    {v1_signature}
    ```

    `MLmodel` 說明書（節錄，signature 那段省略）：

    ```yaml
    {chr(10).join(_keep)}
    ```
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 2️⃣ Signature 是合約：載回來推論，餵錯資料會怎樣

    `mlflow.pyfunc.load_model(uri)` 載回統一介面，`.predict(DataFrame)` 推論。
    因為有 signature，MLflow 在呼叫模型**之前**先對輸入把關（schema enforcement）：

    - 少一欄 → 直接拒絕，告訴你缺哪欄
    - 型別不對（例如某欄變成字串）→ 直接拒絕，告訴你哪欄轉不過去
    - 多一欄 → 靜靜地忽略（只取 signature 裡有的欄位）

    沒有 signature 的模型什麼都吃，錯誤會延後到 scikit-learn 內部才爆，訊息難懂得多。
    **這就是為什麼 `log_model` 一定要給 signature**——它是模型與呼叫端之間的合約。
    """
    )
    return


@app.cell
def _(X_test, mlflow, mo, v1_info):
    v1_pyfunc = mlflow.pyfunc.load_model(v1_info.model_uri)
    _ok = v1_pyfunc.predict(X_test.head(3))

    def _try(df):
        try:
            v1_pyfunc.predict(df)
            return "（沒有報錯）"
        except Exception as e:  # noqa: BLE001 — 教學目的：把 MLflow 的 schema 錯誤原文顯示給學員
            _msg = str(e)
            return _msg[_msg.rfind("Error:"):] if "Error:" in _msg else _msg[-200:]

    schema_missing = _try(X_test.head(3).drop(columns=["f11"]))
    schema_type = _try(X_test.head(3).assign(f1=["a", "b", "c"]))
    schema_extra = _try(X_test.head(3).assign(extra=1.0))
    mo.md(
        f"""
    - 正常輸入 3 筆 → `{_ok}`
    - **少一欄**（拿掉 `f11`）→ `{schema_missing}`
    - **型別錯**（`f1` 變成字串）→ `{schema_type}`
    - **多一欄**（加 `extra`）→ {schema_extra}
    """
    )
    return schema_missing, schema_type, v1_pyfunc


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 3️⃣ Model Registry：名字、版本、alias

    Registry 是「有名字的模型」的目錄。一個 **registered model**（如 `churn-clf`）底下有很多 **version**
    （1、2、3…），每個 version 指向某個 LoggedModel。**alias** 是貼在 version 上的可移動標籤：
    `champion` 指向線上那版、`challenger` 指向候選——服務程式永遠載 `models:/churn-clf@champion`，
    要換版就把 alias 移過去，程式一行不改。

    舊版 MLflow 用固定的 stage（Staging／Production／Archived）做這件事；
    現在 stage 已標記為 deprecated，**用 alias**（名字自己取、一個 version 可以有多個）。

    下面：註冊 v1 → 訓一個 RandomForest 當 v2 註冊 → 貼 alias → 用 alias 載入 → 晉升。
    """
    )
    return


@app.cell
def _(MlflowClient):
    MODEL_NAME = "churn-clf"
    client = MlflowClient()
    return MODEL_NAME, client


@app.cell
def _(MODEL_NAME, RandomForestClassifier, X_test, X_train, client, infer_signature, mlflow, roc_auc_score, v1_info, y_test, y_train):
    mv1_ = mlflow.register_model(model_uri=v1_info.model_uri, name=MODEL_NAME)      # → version 1

    v2_model = RandomForestClassifier(n_estimators=100, max_depth=8, random_state=0).fit(X_train, y_train)
    with mlflow.start_run(run_name="v2-rf") as v2_run:
        v2_info = mlflow.sklearn.log_model(
            v2_model,
            name="churn_model",
            signature=infer_signature(X_train, v2_model.predict_proba(X_train)[:, 1]),
            input_example=X_train.head(3),
        )
        v2_auc = roc_auc_score(y_test, v2_model.predict_proba(X_test)[:, 1])
        mlflow.log_metric("auc", v2_auc)
    mv2_ = mlflow.register_model(model_uri=v2_info.model_uri, name=MODEL_NAME)      # → version 2

    client.set_registered_model_alias(MODEL_NAME, "champion", mv1_.version)         # 線上：v1
    client.set_registered_model_alias(MODEL_NAME, "challenger", mv2_.version)       # 候選：v2
    client.update_model_version(MODEL_NAME, mv2_.version, description="RandomForest, depth 8, 100 trees")
    client.set_model_version_tag(MODEL_NAME, mv2_.version, "validated", "false")
    return mv1_, mv2_, v2_auc, v2_info, v2_model, v2_run


@app.cell
def _(MODEL_NAME, client, mo, mv1_, mv2_, v1_auc, v2_auc):
    def registry_table():
        _rows = []
        for _v in sorted(client.search_model_versions(f"name='{MODEL_NAME}'"), key=lambda v: int(v.version)):
            _full = client.get_model_version(MODEL_NAME, _v.version)      # search 結果不帶 aliases，要單獨取
            _rows.append({
                "version": _full.version,
                "aliases": ", ".join(_full.aliases) or "—",
                "description": _full.description or "—",
                "tags": str(_full.tags) if _full.tags else "—",
                "run": _full.run_id[:8],
                "status": _full.status,
            })
        return _rows

    mo.vstack(
        [
            mo.md(
                f"registered model **{MODEL_NAME}**：v{mv1_.version} 是 LogisticRegression（AUC {v1_auc:.4f}），"
                f"v{mv2_.version} 是 RandomForest（AUC {v2_auc:.4f}）——挑戰者比較強，但線上還是 v1："
            ),
            mo.ui.table(registry_table(), selection=None),
        ]
    )
    return (registry_table,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ### 用 alias 載入，然後晉升

    服務端只認 `models:/churn-clf@champion`。晉升＝把 `champion` 移到 v2；回滾＝移回 v1。
    一個 alias 同時只能指一個 version，指到不存在的 alias 會報錯（下面示範）。
    """
    )
    return


@app.cell
def _(MODEL_NAME, X_test, client, mlflow, mo, mv2_, registry_table):
    _before = mlflow.pyfunc.load_model(f"models:/{MODEL_NAME}@champion")
    _before_ver = client.get_model_version_by_alias(MODEL_NAME, "champion").version

    client.set_registered_model_alias(MODEL_NAME, "champion", mv2_.version)       # 晉升：champion → v2
    client.delete_registered_model_alias(MODEL_NAME, "challenger")
    client.set_model_version_tag(MODEL_NAME, mv2_.version, "validated", "true")

    champion = mlflow.pyfunc.load_model(f"models:/{MODEL_NAME}@champion")
    _after_ver = client.get_model_version_by_alias(MODEL_NAME, "champion").version
    try:
        mlflow.pyfunc.load_model(f"models:/{MODEL_NAME}@nope")
        alias_error = "（沒有報錯）"
    except Exception as e:  # noqa: BLE001 — 教學目的：顯示 alias 不存在的原文
        alias_error = str(e)

    mo.vstack(
        [
            mo.md(
                f"""
    - 晉升前 `@champion` → v{_before_ver}（run `{_before.metadata.run_id[:8]}`），前 3 筆預測 `{_before.predict(X_test.head(3))}`
    - `set_registered_model_alias("{MODEL_NAME}", "champion", {mv2_.version})` 之後 → v{_after_ver}（run `{champion.metadata.run_id[:8]}`），
      **同一行載入程式**拿到的已是 RandomForest，預測 `{champion.predict(X_test.head(3))}`
    - 載入不存在的 alias：`{alias_error}`
    """
            ),
            mo.ui.table(registry_table(), selection=None),
        ]
    )
    return alias_error, champion


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 4️⃣ 評估：`mlflow.models.evaluate` 一行搞定

    晉升不該憑感覺。`mlflow.models.evaluate(model_uri, data, targets=, model_type="classifier")`
    對一個已記錄的模型跑完整評估：accuracy、precision、recall、F1、log-loss、ROC AUC、PR AUC…
    加上 ROC／PR／lift／校準曲線與混淆矩陣，**全部記進當前 run 的 metrics 與 artifacts**。
    兩個版本各跑一次，指標就能並排。
    """
    )
    return


@app.cell
def _(X_test, mlflow, pd, v1_info, v2_info, y_test):
    eval_df = X_test.copy()
    eval_df["label"] = y_test

    eval_results = {}
    for _tag, _info in [("v1-logreg", v1_info), ("v2-rf", v2_info)]:
        with mlflow.start_run(run_name=f"eval-{_tag}"):
            _res = mlflow.models.evaluate(_info.model_uri, eval_df, targets="label", model_type="classifier")
        eval_results[_tag] = _res

    EVAL_KEYS = ["accuracy_score", "precision_score", "recall_score", "f1_score", "log_loss", "roc_auc", "precision_recall_auc"]
    eval_table = pd.DataFrame(
        {tag: {k: round(res.metrics[k], 3) for k in EVAL_KEYS} for tag, res in eval_results.items()}
    )
    eval_artifacts = list(eval_results["v2-rf"].artifacts)
    return EVAL_KEYS, eval_artifacts, eval_df, eval_results, eval_table


@app.cell
def _(eval_artifacts, eval_table, mo):
    mo.vstack(
        [
            mo.md("兩個版本的評估指標（同一份 test 資料）："),
            mo.ui.table(eval_table.reset_index().rename(columns={"index": "metric"}).to_dict("records"), selection=None),
            mo.md(f"另外自動存了 {len(eval_artifacts)} 個圖表 artifacts：`{eval_artifacts}`。下面把 v2 的混淆矩陣讀回來看："),
        ]
    )
    return


@app.cell
def _(eval_results, plt):
    import matplotlib.image as _mpimg

    _cm = eval_results["v2-rf"].artifacts["confusion_matrix"]
    _fig, _ax = plt.subplots(figsize=(4.6, 4.2))
    _ax.imshow(_mpimg.imread(_cm.uri.replace("file://", "")))
    _ax.axis("off")
    _ax.set_title("confusion_matrix artifact of v2-rf (from evaluate)")
    _fig.tight_layout()
    _fig
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 5️⃣ 自訂 pyfunc：把前後處理跟模型包成一個部署單位

    真實模型很少「餵 DataFrame 就出機率」——前面要清資料、後面要用門檻轉成決策。
    這些邏輯若散在服務程式裡，換模型時就會對不上。MLflow 的做法：繼承 `mlflow.pyfunc.PythonModel`，
    把前後處理寫進 `predict`，模型檔案透過 `artifacts` 一起打包。

    下面的 `ChurnWrapper`：輸出機率＋依門檻決定的 `churn` 欄，門檻可以在呼叫時用 `params` 覆蓋
    （signature 的 `params` 段宣告了 `threshold`，預設 0.5）。
    """
    )
    return


@app.cell
def _(WORK, X_train, infer_signature, mlflow, pd, pickle, v2_model):
    class ChurnWrapper(mlflow.pyfunc.PythonModel):
        def __init__(self, threshold=0.5):
            self.threshold = threshold

        def load_context(self, context):                      # 載入時：把打包的模型檔讀回來
            with open(context.artifacts["sk_model"], "rb") as f:
                self.model = pickle.load(f)

        def predict(self, context, model_input, params=None):  # 推論：前處理 → 模型 → 後處理
            thr = (params or {}).get("threshold", self.threshold)
            cols = [c for c in model_input.columns if c.startswith("f")]
            proba = self.model.predict_proba(model_input[cols].fillna(0.0))[:, 1]
            return pd.DataFrame({"prob": proba, "churn": (proba >= thr).astype(int)})

    _pkl = WORK / "rf.pkl"
    _pkl.write_bytes(pickle.dumps(v2_model))
    wrapper_signature = infer_signature(
        X_train.head(3), pd.DataFrame({"prob": [0.1], "churn": [0]}), params={"threshold": 0.5}
    )
    with mlflow.start_run(run_name="v3-wrapper"):
        v3_info = mlflow.pyfunc.log_model(
            name="churn_model",
            python_model=ChurnWrapper(0.5),
            artifacts={"sk_model": str(_pkl)},       # 打包進模型資料夾
            signature=wrapper_signature,
            input_example=X_train.head(3),
            pip_requirements=["scikit-learn", "pandas"],
        )
    return ChurnWrapper, v3_info, wrapper_signature


@app.cell
def _(X_test, mlflow, mo, v3_info, wrapper_signature):
    wrapper = mlflow.pyfunc.load_model(v3_info.model_uri)
    _default = wrapper.predict(X_test.head(4))
    _strict = wrapper.predict(X_test.head(4), params={"threshold": 0.9})
    mo.md(
        f"""
    signature 多了 params 段：`{str(wrapper_signature).splitlines()[-1].strip()}`

    同樣 4 筆輸入——預設門檻 0.5 判 churn 的有 **{int(_default["churn"].sum())}** 筆；
    `params={{"threshold": 0.9}}` 之後只剩 **{int(_strict["churn"].sum())}** 筆（機率 `{_default["prob"].round(3).tolist()}`）。
    門檻是業務決策，不該烙在模型裡——用 params 讓呼叫端調，模型與規則都留在同一個包裝內。
    """
    )
    return (wrapper,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 6️⃣ 資料版本：`log_input` 讓 run 記得用哪份資料

    重現要「同樣的程式＋同樣的設定＋**同樣的資料**」。`mlflow.data.from_pandas(df, source=..., name=...)`
    把 DataFrame 變成一個 dataset 物件（自動算 **digest**：內容指紋），`mlflow.log_input(dataset, context="training")`
    記進 run。之後看 run 的 `inputs` 就知道它用的資料指紋；資料換了、指紋就不同——
    兩個 run 指標不一樣時，先看是不是資料變了。
    """
    )
    return


@app.cell
def _(LogisticRegression, X_train, mlflow, mo, y_train):
    _train_df = X_train.assign(label=y_train)
    train_dataset = mlflow.data.from_pandas(_train_df, source="make_classification(seed=0)", name="churn-train", targets="label")
    with mlflow.start_run(run_name="v1-with-dataset") as _r:
        mlflow.log_input(train_dataset, context="training")
        _m = LogisticRegression(max_iter=1000).fit(X_train, y_train)
        mlflow.log_metric("train_acc", _m.score(X_train, y_train))

    _inputs = mlflow.get_run(_r.info.run_id).inputs.dataset_inputs
    _ds = _inputs[0].dataset
    dataset_digest = _ds.digest
    mo.md(
        f"""
    run `{_r.info.run_name}` 的 inputs：dataset **{_ds.name}**（digest `{dataset_digest}`，
    {_ds.source_type}，{len(_train_df)} 列 × {_train_df.shape[1]} 欄），context = `{_inputs[0].tags[0].value if _inputs[0].tags else "training"}`。
    把訓練資料任何一格改掉，digest 就會不同。
    """
    )
    return dataset_digest, train_dataset


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 7️⃣ 互動：切版本、拉門檻

    服務端載的是 `models:/churn-clf@champion`。下面用下拉選 alias 或版本、拉門檻，
    看同一批客戶的預測怎麼變——這就是「線上那一版」被一行 alias 控制的感覺。
    這裡用原生 flavor（`mlflow.sklearn.load_model`）載入，因為要 `predict_proba` 拿機率；
    alias 與版本 URI 對兩種 flavor 都通用。
    """
    )
    return


@app.cell
def _(MODEL_NAME, client, mo):
    _versions = sorted(client.search_model_versions(f"name='{MODEL_NAME}'"), key=lambda v: int(v.version))
    _opts = {f"models:/{MODEL_NAME}@champion": f"models:/{MODEL_NAME}@champion"}
    for _v in _versions:
        _opts[f"models:/{MODEL_NAME}/{_v.version}"] = f"models:/{MODEL_NAME}/{_v.version}"
    pick_uri = mo.ui.dropdown(options=_opts, value=f"models:/{MODEL_NAME}@champion", label="載入哪個模型")
    pick_thr = mo.ui.slider(0.1, 0.9, step=0.05, value=0.5, label="門檻", show_value=True)
    mo.hstack([pick_uri, pick_thr], wrap=True, justify="start")
    return pick_thr, pick_uri


@app.cell
def _(X_test, mlflow, mo, pd, pick_thr, pick_uri, y_test):
    _m = mlflow.sklearn.load_model(pick_uri.value)          # 原生 flavor 才有 predict_proba；alias 一樣能用
    _n = 8
    _prob = pd.Series(_m.predict_proba(X_test.head(_n))[:, 1]).round(3)
    _pred = (_prob >= pick_thr.value).astype(int)
    _rows = [
        {"customer": int(i), "prob": float(pr), "pred": int(pd_), "actual": int(a), "hit": "✓" if pd_ == a else "✗"}
        for i, pr, pd_, a in zip(X_test.head(_n).index, _prob, _pred, y_test[:_n])
    ]
    mo.vstack(
        [
            mo.md(
                f"`{pick_uri.value}` → 載到 **{type(_m).__name__}**；門檻 {pick_thr.value:.2f}，"
                f"前 {_n} 位客戶判流失 {int(_pred.sum())} 位、答對 {sum(r['hit'] == '✓' for r in _rows)} 位"
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

    1. **LEVEL 1**：用 `mlflow.sklearn.load_model("models:/churn-clf/2")` 以**原生 flavor** 載回 v2，
       印出 `feature_importances_` 最高的三個特徵。pyfunc 介面做不到這件事——想想為什麼還需要它。
    2. **LEVEL 2**：訓一個 GradientBoosting 當 v3 註冊，`evaluate` 之後寫一段「自動晉升」邏輯：
       只有 `roc_auc` 高於目前 champion 才把 alias 移過去，否則貼 tag `rejected=true`。
    3. **LEVEL 3**：把 `ChurnWrapper` 改成能吃「缺欄位」的輸入（缺的補 0、多的忽略、欄位順序任意），
       仍然保有 signature。怎麼驗證：拿掉一欄 `predict` 不再報錯、多一欄結果不變、欄位打亂結果不變。

    先自己試，卡住再展開下面的提示與參考解答。
    帶得走：下載本檔後 `uvx marimo edit --sandbox mlflow-registry_ext.py`
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
    ```python
    native = mlflow.sklearn.load_model("models:/churn-clf/2")     # 原生 RandomForestClassifier
    imp = pd.Series(native.feature_importances_, index=FEATURES).sort_values(ascending=False)
    imp.head(3)
    ```

    你應該看到三個 `f` 開頭的欄位與它們的重要度（合計約 0.4–0.6；`make_classification` 只有 6 個 informative 特徵）。
    pyfunc 只有 `predict`——它的價值在**部署端不用知道底層框架**；分析、解釋、微調要原生 flavor。
    """
            ),
            "💡 LEVEL 2 參考解答": mo.md(
                r"""
    ```python
    from sklearn.ensemble import GradientBoostingClassifier

    gb = GradientBoostingClassifier(n_estimators=150, max_depth=3, random_state=0).fit(X_train, y_train)
    with mlflow.start_run(run_name="v3-gbdt"):
        info3 = mlflow.sklearn.log_model(gb, name="churn_model",
                                         signature=infer_signature(X_train, gb.predict_proba(X_train)[:, 1]))
        res3 = mlflow.models.evaluate(info3.model_uri, eval_df, targets="label", model_type="classifier")
    mv3 = mlflow.register_model(info3.model_uri, MODEL_NAME)

    champ_ver = client.get_model_version_by_alias(MODEL_NAME, "champion").version
    champ_auc = eval_results["v2-rf"].metrics["roc_auc"]          # 目前 champion 的評估結果
    if res3.metrics["roc_auc"] > champ_auc:
        client.set_registered_model_alias(MODEL_NAME, "champion", mv3.version)
        print("promoted to", mv3.version)
    else:
        client.set_model_version_tag(MODEL_NAME, mv3.version, "rejected", "true")
        print("rejected:", res3.metrics["roc_auc"], "<=", champ_auc)
    ```

    本課資料上 GBDT 的 roc_auc 與 RandomForest 很接近（都在 0.96–0.97），哪邊勝出可能只差千分之幾——
    正好提醒你：晉升門檻通常要加一個「至少好多少」的邊際，不然每次重訓都在換版。
    """
            ),
            "💡 LEVEL 3 提示": mo.md(
                r"""
    關鍵在 `predict` 開頭把輸入「整形」成模型要的樣子：

    ```python
    def predict(self, context, model_input, params=None):
        X = model_input.reindex(columns=self.feature_names, fill_value=0.0)   # 缺的補 0、多的丟掉、順序固定
        ...
    ```

    `feature_names` 在 `__init__` 存下來（或從 artifacts 讀一個 JSON）。
    陷阱：signature 若把 12 欄都標成 required，MLflow 在進到你的 `predict` **之前**就會擋掉缺欄位的輸入——
    要嘛用 `infer_signature` 時給一個含缺值的範例讓欄位變 optional，要嘛 signature 只宣告輸出與 params。
    驗證：三種輸入（少欄、多欄、亂序）的 `prob` 都跟原始輸入一致。
    """
            ),
        }
    )
    return


if __name__ == "__main__":
    app.run()
