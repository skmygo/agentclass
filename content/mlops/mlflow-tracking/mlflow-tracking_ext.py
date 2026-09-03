# MLflow 實驗追蹤：每一次訓練都留下證據
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
app = marimo.App(width="medium", app_title="MLflow 實驗追蹤：每一次訓練都留下證據")


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    # 🧾 MLflow 實驗追蹤：每一次訓練都留下證據

    上週你訓了一個模型，AUC 0.95。今天重跑一次，0.92。
    當時的 `max_depth` 是多少？用的是哪一版資料？哪一個 commit？——沒有人記得。

    **MLflow Tracking** 就是訓練的「紀錄簿」：每跑一次訓練＝一個 **run**，
    run 裡自動留下四種東西：

    | 種類 | 是什麼 | 例子 |
    |---|---|---|
    | **params** | 你設定的 | `max_depth=8`、`model=rf` |
    | **metrics** | 你量出來的（可以有 step） | `auc=0.968`、每一輪的 `loss` |
    | **tags** | 你貼的標籤（也有自動的） | `stage=baseline`、`mlflow.user` |
    | **artifacts** | 任何檔案 | 圖表、混淆矩陣、模型本身、資料快照 |

    幾週後只要一句 `search_runs("metrics.auc > 0.96")`，就能把當時的參數、圖、模型全部翻出來。

    這份 notebook 帶你做完：

    1. 第一個 run：params / metrics / tags 四行搞定
    2. artifacts：把圖、JSON、文字檔一起存進 run；看看磁碟上長什麼樣
    3. 有 step 的指標：訓練曲線怎麼記、怎麼取回來畫
    4. `autolog()`：一行自動記錄 19 個參數、7 個訓練指標、4 張圖和模型
    5. 掃參數：parent / nested runs
    6. 查詢與比較：`search_runs` 回傳一張 DataFrame，篩選、排序、畫圖
    7. 重現與介面：自動標籤、`mlflow ui`、刪除與還原

    從第一格往下全部執行即可（首次安裝套件約 1–2 分鐘）。
    所有紀錄都寫在本機一個暫存資料夾，不會連到任何伺服器。
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

    import marimo as mo
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import mlflow
    import numpy as np
    import pandas as pd
    from mlflow import MlflowClient
    from sklearn.datasets import make_classification
    from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import (
        accuracy_score,
        f1_score,
        log_loss,
        roc_auc_score,
        roc_curve,
    )
    from sklearn.model_selection import train_test_split

    # MLflow 建表、序列化格式等提示會蓋掉教學輸出，關小聲；真的出錯還是會噴
    logging.getLogger("mlflow").setLevel(logging.ERROR)
    warnings.filterwarnings("ignore")
    return (
        GradientBoostingClassifier,
        LogisticRegression,
        MlflowClient,
        Path,
        RandomForestClassifier,
        accuracy_score,
        f1_score,
        log_loss,
        make_classification,
        mlflow,
        mo,
        np,
        pd,
        plt,
        roc_auc_score,
        roc_curve,
        shutil,
        tempfile,
        train_test_split,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 0️⃣ 準備：一份資料、一本空的紀錄簿

    資料是模擬的「客戶流失」二元分類：2000 筆、12 個匿名特徵 `f0`–`f11`，標籤 1＝流失。
    不用在意特徵的意義，我們要學的是**怎麼記錄**，不是怎麼建模。

    紀錄簿放哪裡由 `mlflow.set_tracking_uri()` 決定。這裡用一個 SQLite 檔（`mlflow.db`）
    ——不用架任何伺服器，而且之後第 2 課的 Model Registry 也需要資料庫後端
    （舊教學常見的純資料夾模式 `./mlruns` 從來不支援 Registry，MLflow 3.15 起更進入維護模式、
    預設直接報錯要你改用 sqlite）。正式環境換成
    `http://mlflow.your-company.com` 這種 tracking server 網址，其餘程式一個字不用改。

    每次從頭執行都會清掉舊紀錄，讓下面的數字跟解說對得上。
    """
    )
    return


@app.cell
def _(Path, make_classification, mlflow, mo, pd, shutil, tempfile, train_test_split):
    WORK = Path(tempfile.gettempdir()) / "mlflow-lesson"
    shutil.rmtree(WORK, ignore_errors=True)   # 從頭來：舊紀錄清掉
    WORK.mkdir(parents=True)

    mlflow.set_tracking_uri(f"sqlite:///{WORK / 'mlflow.db'}")        # 紀錄簿＝一個 SQLite 檔
    mlflow.create_experiment("churn-demo", artifact_location=str(WORK / "artifacts"))
    experiment = mlflow.set_experiment("churn-demo")                  # 之後的 run 都歸這個實驗

    _X, _y = make_classification(
        n_samples=2000, n_features=12, n_informative=6, random_state=0, class_sep=1.0
    )
    FEATURES = [f"f{i}" for i in range(12)]
    X_train, X_test, y_train, y_test = train_test_split(
        pd.DataFrame(_X, columns=FEATURES), _y, test_size=0.25, random_state=0
    )
    mo.md(
        f"""
    - tracking URI：`{mlflow.get_tracking_uri()}`
    - experiment：**{experiment.name}**（id={experiment.experiment_id}），artifacts 存在 `{experiment.artifact_location}`
    - 資料：train {len(X_train)} 筆 / test {len(X_test)} 筆，流失率 {_y.mean():.1%}
    """
    )
    return FEATURES, WORK, X_test, X_train, experiment, y_test, y_train


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 1️⃣ 第一個 run：params、metrics、tags

    `with mlflow.start_run():` 開一個 run，區塊內任何 `log_*` 都記進這個 run，離開區塊自動結束
    （狀態 FINISHED；中途例外則 FAILED）。三個最常用的動作：

    - `log_param("C", 1.0)`：**設定值**，一個 run 內同名只能記一次（改了會報錯——參數就是不該中途變）
    - `log_metric("auc", 0.95)`：**量測值**，同名可以記很多次（配合 `step` 就是曲線）
    - `set_tag("stage", "baseline")`：**標籤**，之後篩選用

    跑完用 `mlflow.get_run(run_id)` 把整個 run 讀回來看看裡面有什麼。
    """
    )
    return


@app.cell
def _(LogisticRegression, X_test, X_train, accuracy_score, mlflow, roc_auc_score, y_test, y_train):
    with mlflow.start_run(run_name="logreg-baseline") as baseline_run:
        C = 1.0
        mlflow.log_param("model", "logreg")
        mlflow.log_param("C", C)

        _clf = LogisticRegression(C=C, max_iter=1000).fit(X_train, y_train)
        _proba = _clf.predict_proba(X_test)[:, 1]
        baseline_auc = roc_auc_score(y_test, _proba)
        baseline_acc = accuracy_score(y_test, _proba > 0.5)

        mlflow.log_metrics({"auc": baseline_auc, "accuracy": baseline_acc})
        mlflow.set_tag("stage", "baseline")

    baseline_run_id = baseline_run.info.run_id
    return baseline_acc, baseline_auc, baseline_run_id


@app.cell
def _(baseline_run_id, mlflow, mo):
    _run = mlflow.get_run(baseline_run_id)
    _auto_tags = {k: v for k, v in _run.data.tags.items() if k.startswith("mlflow.")}
    mo.md(
        f"""
    run **{_run.info.run_name}**（id `{_run.info.run_id[:8]}…`，狀態 {_run.info.status}）

    - params：`{_run.data.params}`
    - metrics：`{ {k: round(v, 4) for k, v in _run.data.metrics.items()} }`
    - 你貼的 tag：`stage={_run.data.tags["stage"]}`
    - MLflow 自動貼的 tag：`{sorted(_auto_tags)}`

    自動標籤裡有 `mlflow.source.name`（哪個檔案跑的）、`mlflow.user`（誰跑的）；在 git repo 裡跑還會多一個
    `mlflow.source.git.commit`——這就是「重現」的線索：**誰、用哪份程式、什麼設定、得到什麼結果**。
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 2️⃣ artifacts：把圖、JSON、文字檔一起存進 run

    數字之外，run 還能掛**任何檔案**：

    - `log_figure(fig, "roc.png")`：matplotlib 圖直接存
    - `log_dict({...}, "features.json")`：Python dict 存成 JSON
    - `log_text("...", "notes.md")`：一段文字
    - `log_artifact("path/to/file")`：磁碟上任何現成檔案（資料快照、設定檔、模型權重）

    這一格重訓一次 baseline（同樣設定）並把 ROC 曲線、特徵清單、備註一起掛上去，
    然後用 `list_artifacts` 把清單讀回來。
    """
    )
    return


@app.cell
def _(
    FEATURES,
    LogisticRegression,
    X_test,
    X_train,
    mlflow,
    mo,
    plt,
    roc_auc_score,
    roc_curve,
    y_test,
    y_train,
):
    with mlflow.start_run(run_name="logreg-with-artifacts") as artifacts_run:
        mlflow.log_params({"model": "logreg", "C": 1.0})
        _clf = LogisticRegression(C=1.0, max_iter=1000).fit(X_train, y_train)
        _proba = _clf.predict_proba(X_test)[:, 1]
        mlflow.log_metric("auc", roc_auc_score(y_test, _proba))
        mlflow.set_tag("stage", "baseline")

        # 1) 一張圖
        _fpr, _tpr, _ = roc_curve(y_test, _proba)
        _fig, _ax = plt.subplots(figsize=(4.8, 4.0))
        _ax.plot(_fpr, _tpr, color="#4C72B0", lw=2, label=f"logreg AUC={roc_auc_score(y_test, _proba):.3f}")
        _ax.plot([0, 1], [0, 1], "--", color="#999", lw=1)
        _ax.set_xlabel("false positive rate")
        _ax.set_ylabel("true positive rate")
        _ax.set_title("ROC curve (logged as artifact)")
        _ax.legend(loc="lower right")
        _fig.tight_layout()
        mlflow.log_figure(_fig, "plots/roc.png")
        plt.close(_fig)

        # 2) 一個 dict → JSON；3) 一段文字
        mlflow.log_dict({"features": FEATURES, "target": "churn"}, "features.json")
        mlflow.log_text("baseline 只用預設值，之後拿它當比較基準。", "notes.md")

    artifacts_run_id = artifacts_run.info.run_id
    _listing = [
        (a.path, a.is_dir) for a in mlflow.artifacts.list_artifacts(run_id=artifacts_run_id)
    ] + [(a.path, a.is_dir) for a in mlflow.artifacts.list_artifacts(run_id=artifacts_run_id, artifact_path="plots")]
    mo.md(
        "這個 run 的 artifacts：\n\n"
        + "\n".join(f"- `{p}`{'／' if d else ''}" for p, d in _listing)
        + f"\n\n取回檔案：`mlflow.artifacts.download_artifacts(run_id=\"{artifacts_run_id[:8]}…\", artifact_path=\"plots/roc.png\")`，"
        "回傳本機路徑。JSON 可直接 `mlflow.artifacts.load_dict(...)`。"
    )
    return (artifacts_run_id,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ### 磁碟上長什麼樣

    MLflow 不神秘：**中繼資料（params／metrics／tags）在 SQLite，檔案在 artifacts 資料夾**。
    路徑是 `artifacts/<experiment_id>/<run_id>/artifacts/...`——
    下面把目前的目錄樹列出來。之後你若把 tracking 換成遠端伺服器，
    artifacts 通常會落在 S3／MinIO 這類物件儲存，結構一樣。
    """
    )
    return


@app.cell
def _(WORK, mo):
    def _tree(root, prefix=""):
        _lines = []
        _items = sorted(root.iterdir(), key=lambda p: (not p.is_dir(), p.name))
        for _i, _p in enumerate(_items):
            _last = _i == len(_items) - 1
            _name = _p.name if len(_p.name) < 40 else _p.name[:8] + "…"   # run id 縮短
            _lines.append(f"{prefix}{'└── ' if _last else '├── '}{_name}{'/' if _p.is_dir() else ''}")
            if _p.is_dir():
                _lines += _tree(_p, prefix + ("    " if _last else "│   "))
        return _lines

    disk_tree = "\n".join([WORK.name + "/"] + _tree(WORK))
    mo.md(f"```text\n{disk_tree}\n```")
    return (disk_tree,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 3️⃣ 有 step 的指標：訓練曲線

    `log_metric(key, value, step=n)` 同一個 key 記很多次，就是一條曲線。
    這裡用 Gradient Boosting：它每加一棵樹就是一「輪」，`staged_predict_proba` 能取出每一輪的預測，
    我們把每一輪的 train / test log-loss 都記下來（150 輪 → 300 個點）。

    取回來用 `MlflowClient().get_metric_history(run_id, key)`，每個點有 `step`、`value`、`timestamp`。
    看下圖：test loss 在某一輪之後就不再下降——**這張圖是紀錄簿自己長出來的**，
    不是你訓練時另外存的。
    """
    )
    return


@app.cell
def _(
    GradientBoostingClassifier,
    MlflowClient,
    X_test,
    X_train,
    log_loss,
    mlflow,
    np,
    roc_auc_score,
    y_test,
    y_train,
):
    N_ROUNDS = 150
    with mlflow.start_run(run_name="gbdt-curve") as curve_run:
        mlflow.log_params({"model": "gbdt", "n_estimators": N_ROUNDS, "learning_rate": 0.1, "max_depth": 3})
        _gb = GradientBoostingClassifier(n_estimators=N_ROUNDS, learning_rate=0.1, max_depth=3, random_state=0)
        _gb.fit(X_train, y_train)
        for _step, (_ptr, _pte) in enumerate(
            zip(_gb.staged_predict_proba(X_train), _gb.staged_predict_proba(X_test)), start=1
        ):
            mlflow.log_metric("train_logloss", log_loss(y_train, _ptr[:, 1]), step=_step)
            mlflow.log_metric("test_logloss", log_loss(y_test, _pte[:, 1]), step=_step)
        mlflow.log_metric("auc", roc_auc_score(y_test, _gb.predict_proba(X_test)[:, 1]))
        mlflow.set_tag("stage", "curve")

    curve_run_id = curve_run.info.run_id
    _client = MlflowClient()
    curve_train = np.array([(h.step, h.value) for h in _client.get_metric_history(curve_run_id, "train_logloss")])
    curve_test = np.array([(h.step, h.value) for h in _client.get_metric_history(curve_run_id, "test_logloss")])
    best_round = int(curve_test[np.argmin(curve_test[:, 1]), 0])
    return N_ROUNDS, best_round, curve_run_id, curve_test, curve_train


@app.cell
def _(best_round, curve_test, curve_train, plt):
    _fig, _ax = plt.subplots(figsize=(6.2, 3.8))
    _ax.plot(curve_train[:, 0], curve_train[:, 1], color="#4C72B0", lw=2, label="train log-loss")
    _ax.plot(curve_test[:, 0], curve_test[:, 1], color="#DD8452", lw=2, label="test log-loss")
    _ax.axvline(best_round, color="#C44E52", ls="--", lw=1.2, label=f"best test @ round {best_round}")
    _ax.set_xlabel("boosting round (step)")
    _ax.set_ylabel("log-loss")
    _ax.set_title("Curves rebuilt from get_metric_history()")
    _ax.legend()
    _ax.spines[["top", "right"]].set_visible(False)
    _fig.tight_layout()
    _fig
    return


@app.cell
def _(best_round, curve_test, curve_train, mo):
    mo.md(
        f"""
    test log-loss 最低點在第 **{best_round}** 輪（{curve_test[best_round - 1, 1]:.3f}），
    之後 train loss 繼續掉到 {curve_train[-1, 1]:.3f}、test 卻回升到 {curve_test[-1, 1]:.3f}——
    典型的過擬合訊號。沒有逐步紀錄，你只會看到最後一輪的數字。
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 4️⃣ `autolog()`：一行，什麼都幫你記

    手動 `log_param` 很快就會漏——所以 MLflow 對常見框架（scikit-learn、PyTorch、XGBoost、
    LightGBM、transformers、OpenAI…）都有 **autolog**：

    ```python
    mlflow.sklearn.autolog()
    ```

    之後每一次 `.fit()` 都自動變成一個 run：**估計器的全部超參數**、**訓練集上的指標**、
    幾張診斷圖、還有**模型本身**（含環境需求，第 2 課會用到）。
    下面訓一個 RandomForest，但**一行 `log_*` 都不寫**，看它記了什麼。
    測試集指標 autolog 不知道（它只看得到 `fit`），所以自己補兩行 `log_metric`。
    """
    )
    return


@app.cell
def _(RandomForestClassifier, X_test, X_train, accuracy_score, mlflow, roc_auc_score, y_test, y_train):
    mlflow.sklearn.autolog(silent=True)          # 打開自動記錄

    with mlflow.start_run(run_name="rf-autolog") as autolog_run:
        _rf = RandomForestClassifier(n_estimators=100, max_depth=6, random_state=0).fit(X_train, y_train)
        _proba = _rf.predict_proba(X_test)[:, 1]
        mlflow.log_metric("auc", roc_auc_score(y_test, _proba))            # 測試集要自己補
        mlflow.log_metric("accuracy", accuracy_score(y_test, _proba > 0.5))
        mlflow.set_tag("stage", "autolog")

    mlflow.sklearn.autolog(disable=True)         # 關掉，後面的 run 回到手動（比較好對照）
    autolog_run_id = autolog_run.info.run_id
    return (autolog_run_id,)


@app.cell
def _(autolog_run_id, mlflow, mo):
    _run = mlflow.get_run(autolog_run_id)
    _params = _run.data.params
    _metrics = _run.data.metrics
    _arts = [a.path for a in mlflow.artifacts.list_artifacts(run_id=autolog_run_id)]
    autolog_counts = (len(_params), len([m for m in _metrics if m.startswith("training_")]), len(_arts))
    mo.md(
        f"""
    autolog 幫這個 run 記了：

    - **{autolog_counts[0]} 個 params**（估計器的每一個超參數）：`{", ".join(sorted(_params)[:6])}, …`
    - **{autolog_counts[1]} 個 training_ 指標**：`{", ".join(sorted(m for m in _metrics if m.startswith("training_")))}`
    - **{autolog_counts[2]} 個 artifacts**：`{", ".join(_arts)}`
    - tags：`estimator_name={_run.data.tags.get("estimator_name")}`
    - 外加一個 **logged model**（`models/` 之下，這裡沒列進 artifacts 清單）——第 2 課會把它註冊、載回來推論

    注意 `training_roc_auc` 是**訓練集**上的（{_metrics.get("training_roc_auc", float("nan")):.3f}），
    自己補的測試集 `auc` 是 {_metrics.get("auc", float("nan")):.3f}——兩個都在，才看得出過擬合。
    """
    )
    return (autolog_counts,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 5️⃣ 掃參數：parent run ＋ nested runs

    調參時一次會跑很多組。把它們塞成同一層會很亂——MLflow 的做法是
    **一個 parent run 代表這次掃描，每一組參數是一個 `nested=True` 的子 run**。
    UI 裡會摺成一組；查詢時用 `tags.mlflow.parentRunId` 就能撈出整組。

    下面掃 RandomForest 的 `max_depth ∈ {2, 4, 8, 16}`（每棵 60 樹），四個子 run。
    """
    )
    return


@app.cell
def _(RandomForestClassifier, X_test, X_train, accuracy_score, f1_score, mlflow, roc_auc_score, y_test, y_train):
    DEPTHS = [2, 4, 8, 16]
    sweep_rows = []
    with mlflow.start_run(run_name="rf-depth-sweep") as sweep_run:
        mlflow.set_tag("stage", "sweep")
        mlflow.log_param("n_estimators", 60)
        for _depth in DEPTHS:
            with mlflow.start_run(run_name=f"depth={_depth}", nested=True) as _child:
                mlflow.log_params({"model": "rf", "max_depth": _depth, "n_estimators": 60})
                _rf = RandomForestClassifier(n_estimators=60, max_depth=_depth, random_state=0).fit(X_train, y_train)
                _proba = _rf.predict_proba(X_test)[:, 1]
                _m = {
                    "auc": roc_auc_score(y_test, _proba),
                    "accuracy": accuracy_score(y_test, _proba > 0.5),
                    "f1": f1_score(y_test, _proba > 0.5),
                }
                mlflow.log_metrics(_m)
                mlflow.set_tag("stage", "sweep")
                sweep_rows.append({"run": _child.info.run_name, "run_id": _child.info.run_id[:8], **{k: round(v, 4) for k, v in _m.items()}})
    sweep_run_id = sweep_run.info.run_id
    return DEPTHS, sweep_rows, sweep_run_id


@app.cell
def _(mlflow, mo, sweep_rows, sweep_run_id):
    _children = mlflow.search_runs(
        experiment_names=["churn-demo"],
        filter_string=f"tags.mlflow.parentRunId = '{sweep_run_id}'",
        order_by=["params.max_depth ASC"],
    )
    mo.vstack(
        [
            mo.md(
                f"parent run `{sweep_run_id[:8]}…` 底下用 `tags.mlflow.parentRunId` 撈到 **{len(_children)} 個子 run**："
            ),
            mo.ui.table(sweep_rows, selection=None),
        ]
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 6️⃣ 查詢與比較：`search_runs` 就是你的 UI

    `mlflow.search_runs()` 回傳一張 **pandas DataFrame**：一列一個 run，欄位是
    `params.*`、`metrics.*`、`tags.*` 加上 run_id、狀態、時間。它支援一個小型的查詢語言：

    ```python
    mlflow.search_runs(
        experiment_names=["churn-demo"],
        filter_string="metrics.auc > 0.95 and params.model = 'rf' and tags.stage != 'autolog'",
        order_by=["metrics.auc DESC"],
        max_results=10,
    )
    ```

    先把目前實驗裡**所有 run** 列出來（parent run 沒有 metrics，所以 auc 是 NaN）：
    """
    )
    return


@app.cell
def _(mlflow, mo):
    all_runs = mlflow.search_runs(experiment_names=["churn-demo"], order_by=["start_time ASC"])
    SHOW_COLS = ["tags.mlflow.runName", "params.model", "params.max_depth", "metrics.auc", "metrics.accuracy", "tags.stage", "status"]
    runs_view = all_runs[[c for c in SHOW_COLS if c in all_runs.columns]].copy()
    runs_view.columns = [c.split(".")[-1] for c in runs_view.columns]
    runs_view = runs_view.round(4)
    mo.vstack(
        [
            mo.md(f"實驗裡共 **{len(all_runs)} 個 run**、DataFrame 有 {all_runs.shape[1]} 欄（下面只挑 {len(runs_view.columns)} 欄顯示）："),
            mo.ui.table(runs_view.fillna("").to_dict("records"), selection=None),
        ]
    )
    return SHOW_COLS, all_runs, runs_view


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ### 動手查：改條件，看結果

    下面的輸入框直接餵給 `filter_string`，排序下拉餵 `order_by`。試試：

    - `metrics.auc > 0.96`
    - `params.model = 'rf' and metrics.auc > 0.95`
    - `tags.stage = 'sweep'`
    - `attributes.run_name LIKE 'depth%'`（前綴比對）

    寫錯語法會直接看到 MLflow 的錯誤訊息（例如少了引號）——那也是學習的一部分。
    """
    )
    return


@app.cell
def _(mo):
    q_filter = mo.ui.text(value="metrics.auc > 0.95", label="filter_string", full_width=True)
    q_order = mo.ui.dropdown(
        options=["metrics.auc DESC", "metrics.auc ASC", "metrics.accuracy DESC", "start_time DESC"],
        value="metrics.auc DESC",
        label="order_by",
    )
    mo.hstack([q_filter, q_order], wrap=True, justify="start")
    return q_filter, q_order


@app.cell
def _(SHOW_COLS, mlflow, mo, q_filter, q_order):
    try:
        _df = mlflow.search_runs(
            experiment_names=["churn-demo"], filter_string=q_filter.value, order_by=[q_order.value]
        )
        _view = _df[[c for c in SHOW_COLS if c in _df.columns]].round(4).fillna("")
        _view.columns = [c.split(".")[-1] for c in _view.columns]
        query_result = mo.vstack(
            [mo.md(f"`{q_filter.value}` → **{len(_df)} 個 run**"), mo.ui.table(_view.to_dict("records"), selection=None)]
        )
    except Exception as _e:  # noqa: BLE001 — 查詢語法錯誤要顯示給學員，不能讓 notebook 炸掉
        query_result = mo.callout(mo.md(f"MLflow 不接受這個查詢：\n\n```\n{str(_e)[:400]}\n```"), kind="warn")
    query_result
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ### 比較：DataFrame 就能畫

    因為 `search_runs` 回傳 DataFrame，「比較不同 run」就是普通的 pandas + matplotlib：
    把 sweep 的四個子 run 抓出來，畫 AUC 對 `max_depth`。
    """
    )
    return


@app.cell
def _(all_runs, pd, plt):
    _sweep = all_runs[all_runs["tags.stage"].eq("sweep") & all_runs["params.max_depth"].notna()].copy()
    _sweep["depth"] = pd.to_numeric(_sweep["params.max_depth"])
    _sweep = _sweep.sort_values("depth")
    _fig, _ax = plt.subplots(figsize=(6.0, 3.6))
    _ax.plot(_sweep["depth"], _sweep["metrics.auc"], "o-", color="#DD8452", lw=2, label="test AUC")
    _ax.plot(_sweep["depth"], _sweep["metrics.accuracy"], "s--", color="#4C72B0", lw=1.5, label="test accuracy")
    for _d, _a in zip(_sweep["depth"], _sweep["metrics.auc"]):
        _ax.annotate(f"{_a:.3f}", (_d, _a), textcoords="offset points", xytext=(0, 7), ha="center", fontsize=9)
    _ax.set_xscale("log", base=2)
    _ax.set_xticks(list(_sweep["depth"]))
    _ax.set_xticklabels([str(int(d)) for d in _sweep["depth"]])
    _ax.set_xlabel("max_depth")
    _ax.set_ylabel("score")
    _ax.set_title("Compare runs straight from search_runs()")
    _ax.legend(loc="lower right")
    _ax.spines[["top", "right"]].set_visible(False)
    _fig.tight_layout()
    _fig
    return


@app.cell
def _(all_runs, mo):
    _best = all_runs.dropna(subset=["metrics.auc"]).sort_values("metrics.auc", ascending=False).iloc[0]
    best_run_name = _best["tags.mlflow.runName"]
    best_run_auc = float(_best["metrics.auc"])
    mo.md(
        f"""
    目前 AUC 最高的 run：**{best_run_name}**（{best_run_auc:.4f}）。
    下一步你可能想「把它標成候選」——`MlflowClient().set_tag(run_id, "candidate", "true")` 就好，
    run 結束後一樣可以改 tag（params 不行）。真的要「上線」它，是第 2 課 Model Registry 的事。
    """
    )
    return best_run_auc, best_run_name


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 7️⃣ 你自己的 run：拉桿、按鈕、看紀錄簿長大

    到目前為止的 run 都是我幫你設計的。下面拉兩支拉桿，按一下按鈕就會**真的訓練一次並記成一個新 run**
    ——再回到上面 6️⃣ 的查詢框，你的 run 就在裡面（tag `stage = 'yours'`）。
    多按幾次，看紀錄簿長大。
    """
    )
    return


@app.cell
def _(mo):
    my_depth = mo.ui.slider(1, 20, value=5, label="max_depth", show_value=True)
    my_trees = mo.ui.slider(10, 300, step=10, value=100, label="n_estimators", show_value=True)
    my_button = mo.ui.run_button(label="訓練並記錄一個 run")
    mo.hstack([my_depth, my_trees, my_button], wrap=True, justify="start")
    return my_button, my_depth, my_trees


@app.cell
def _(
    RandomForestClassifier,
    X_test,
    X_train,
    accuracy_score,
    mlflow,
    mo,
    my_button,
    my_depth,
    my_trees,
    roc_auc_score,
    y_test,
    y_train,
):
    mo.stop(not my_button.value, mo.md("*還沒有你的 run——調好拉桿按一下按鈕。*"))

    with mlflow.start_run(run_name=f"yours-d{my_depth.value}-t{my_trees.value}") as _mine:
        mlflow.log_params({"model": "rf", "max_depth": my_depth.value, "n_estimators": my_trees.value})
        _rf = RandomForestClassifier(
            n_estimators=my_trees.value, max_depth=my_depth.value, random_state=0
        ).fit(X_train, y_train)
        _proba = _rf.predict_proba(X_test)[:, 1]
        _auc = roc_auc_score(y_test, _proba)
        mlflow.log_metrics({"auc": _auc, "accuracy": accuracy_score(y_test, _proba > 0.5)})
        mlflow.set_tag("stage", "yours")

    _n_mine = len(mlflow.search_runs(experiment_names=["churn-demo"], filter_string="tags.stage = 'yours'"))
    mo.callout(
        mo.md(
            f"記下 run **{_mine.info.run_name}**：AUC **{_auc:.4f}**。你的 run 目前有 {_n_mine} 個。"
            "回到 6️⃣ 的查詢框輸入 `tags.stage = 'yours'` 就看得到它們。"
        ),
        kind="success",
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 8️⃣ 重現、介面、整理

    **重現一個 run**：它的 params 全在紀錄裡（`run.data.params`），程式來源在 `mlflow.source.name`，
    git commit 在 `mlflow.source.git.commit`（在 git repo 內執行才有）。再加上第 2 課會學的
    `log_input(dataset)` 記資料版本，就湊齊了「同樣的程式＋同樣的資料＋同樣的設定」。

    **圖形介面**：本課全程用程式讀紀錄簿，但 MLflow 附一個網頁 UI，在你自己的電腦上：

    ```bash
    mlflow ui --backend-store-uri sqlite:///路徑/mlflow.db --port 5000
    ```

    打開 <http://localhost:5000> 就能點選 run、並排比較、看曲線、下載 artifacts——
    它讀的就是同一個 SQLite 檔。團隊共用時改跑 `mlflow server`（同一個指令多加儲存設定），
    大家的程式只要 `set_tracking_uri("http://那台機器:5000")`。

    **整理**：`MlflowClient().delete_run(run_id)` 是軟刪除（`restore_run` 可還原；
    `search_runs(run_view_type=ViewType.DELETED_ONLY)` 能看到），`mlflow gc` 才真的清掉磁碟。
    下面示範刪掉再還原。
    """
    )
    return


@app.cell
def _(MlflowClient, artifacts_run_id, mlflow, mo):
    from mlflow.entities import ViewType

    _client = MlflowClient()
    _client.delete_run(artifacts_run_id)
    _deleted = mlflow.search_runs(experiment_names=["churn-demo"], run_view_type=ViewType.DELETED_ONLY)
    _n_active_after_delete = len(mlflow.search_runs(experiment_names=["churn-demo"]))
    _client.restore_run(artifacts_run_id)
    _n_active_after_restore = len(mlflow.search_runs(experiment_names=["churn-demo"]))
    mo.md(
        f"""
    - `delete_run` 之後：active {_n_active_after_delete} 個、deleted {len(_deleted)} 個
      （被刪的是 `{_deleted["tags.mlflow.runName"].iloc[0]}`，狀態 `{_deleted["status"].iloc[0]}`——資料還在，只是被標成 deleted）
    - `restore_run` 之後：active 回到 {_n_active_after_restore} 個
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 🏆 延伸挑戰

    1. **LEVEL 1**：再跑一個 LogisticRegression，但 `class_weight="balanced"`，記成 run 並補上 `recall` 指標。
       用 `search_runs` 把兩個 logreg run 並排比：balanced 的 recall 應該比 baseline 高、accuracy 略低。
    2. **LEVEL 2**：把「AUC > 0.96 而且 model = rf」的 run 全部貼上 `candidate = true` 的 tag，
       再用 `tags.candidate = 'true'` 查回來確認。提示：`search_runs` 拿 run_id，`MlflowClient().set_tag`。
    3. **LEVEL 3**：把你自己手上任何一支訓練腳本（或 notebook 的一段）包成 run：
       至少一個 param、一個 metric、一個 artifact（圖或設定檔）。
       怎麼驗證：`search_runs` 找得到它、`list_artifacts` 列得出檔案、`mlflow ui` 打開看得到。

    先自己試，卡住再展開下面的提示與參考解答。
    帶得走：下載本檔後 `uvx marimo edit --sandbox mlflow-tracking_ext.py`
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
    from sklearn.metrics import recall_score

    with mlflow.start_run(run_name="logreg-balanced"):
        mlflow.log_params({"model": "logreg", "C": 1.0, "class_weight": "balanced"})
        clf = LogisticRegression(C=1.0, class_weight="balanced", max_iter=1000).fit(X_train, y_train)
        proba = clf.predict_proba(X_test)[:, 1]
        mlflow.log_metrics({
            "auc": roc_auc_score(y_test, proba),
            "accuracy": accuracy_score(y_test, proba > 0.5),
            "recall": recall_score(y_test, proba > 0.5),
        })
        mlflow.set_tag("stage", "challenge")

    mlflow.search_runs(
        experiment_names=["churn-demo"],
        filter_string="params.model = 'logreg'",
    )[["tags.mlflow.runName", "params.class_weight", "metrics.auc", "metrics.accuracy", "metrics.recall"]]
    ```

    這份資料兩類數量接近（流失率約 50%），所以 balanced 的差異會很小——
    你應該看到 recall 只差零點零幾、AUC 幾乎相同。把 `make_classification` 的 `weights=[0.9, 0.1]`
    改成不平衡資料再試，差距就會拉開。
    """
            ),
            "💡 LEVEL 2 參考解答": mo.md(
                r"""
    ```python
    client = MlflowClient()
    hits = mlflow.search_runs(
        experiment_names=["churn-demo"],
        filter_string="metrics.auc > 0.96 and params.model = 'rf'",
    )
    for run_id in hits["run_id"]:
        client.set_tag(run_id, "candidate", "true")

    mlflow.search_runs(experiment_names=["churn-demo"], filter_string="tags.candidate = 'true'")[
        ["tags.mlflow.runName", "params.max_depth", "metrics.auc"]
    ]
    ```

    以本課預設的 run 來說，命中的是 sweep 裡 `depth=8`、`depth=16` 兩個子 run（AUC 0.967／0.969）；
    如果你在 7️⃣ 按過按鈕，你自己的高分 run 也會進來。
    """
            ),
            "💡 LEVEL 3 提示": mo.md(
                r"""
    最小可行版本只要三件事：

    ```python
    mlflow.set_tracking_uri("sqlite:///mlflow.db")      # 或你團隊的 tracking server
    mlflow.set_experiment("my-project")
    with mlflow.start_run():
        mlflow.log_params(config)                        # 你的設定 dict
        ...訓練...
        mlflow.log_metric("val_score", score)
        mlflow.log_artifact("config.yaml")               # 或 log_figure / log_dict
    ```

    陷阱：(1) 同一個 param 在同一個 run 記兩次會報錯——迴圈裡的東西用 metric 或 nested run；
    (2) `log_artifact` 要給**已存在的檔案路徑**；(3) 用框架訓練的話先試 `autolog()`，通常比手寫完整。
    驗證方式：新開一個 Python 直譯器，`set_tracking_uri` 指到同一個 db，`search_runs` 找得到、
    `download_artifacts` 拿得到檔案，就是真的存進去了。
    """
            ),
        }
    )
    return


if __name__ == "__main__":
    app.run()
