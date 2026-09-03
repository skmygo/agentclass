# Optuna 自動調參：讓超參數搜尋自己跑（每個 trial 都留在 MLflow）
# 不需要 GPU——molab 免費 CPU 環境即可全程執行（全部寫在本機暫存資料夾，不連任何伺服器）。
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "marimo",
#     "optuna>=4.0",
#     "mlflow>=3.0",
#     "scikit-learn",
#     "pandas",
#     "numpy",
#     "matplotlib",
# ]
# ///
import marimo

__generated_with = "0.23.16"
app = marimo.App(width="medium", app_title="Optuna 自動調參：讓超參數搜尋自己跑")


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    # 🎛️ Optuna 自動調參：讓超參數搜尋自己跑

    第 1 課你用一個 `for` 迴圈掃了 `max_depth` 的四個值，挑出最好的那個。
    那一招在**一個**超參數上很好用。問題是模型從來不只有一個旋鈕：

    | 超參數的數量 | 每個試 5 個值 | 一次評估 3 秒的話 |
    |---|---|---|
    | 1 個 | 5 種組合 | 15 秒 |
    | 2 個 | 25 種 | 1 分鐘多 |
    | 4 個 | 625 種 | 半小時 |
    | 6 個 | 15625 種 | 13 小時 |

    這叫**組合爆炸**。而且更氣人的是：那 15625 次裡，一大半在第一眼就看得出沒希望
    ——`max_depth=2` 那一整排怎麼配都不會贏，你卻還是老老實實跑完了。

    **Optuna 做兩件事**：

    1. **聰明地挑下一組**——把看過的每個結果拿來更新「哪裡可能更好」的猜測（TPE 取樣器）。
    2. **早點放棄沒希望的**——訓練到一半就看得出會輸，直接砍掉這個 trial（pruning）。

    這份 notebook 帶你做完：

    | 節 | 做什麼 |
    |---|---|
    | 1️⃣ | 手動格點的代價：兩個超參數就是 40 次訓練，先把真實的分數地形畫出來 |
    | 2️⃣ | 三個名詞：`study`／`trial`／`objective`，用一個一眼看得懂的函式認識 |
    | 3️⃣ | 真實任務：四個超參數、25 個 trial，每個 trial 一個 MLflow nested run |
    | 4️⃣ | TPE 真的比亂猜好嗎？一場誠實的對照（結果可能跟你想的不一樣） |
    | 5️⃣ | 參數重要度 → 縮小空間再跑第二輪，這才是調參真正的流程 |
    | 6️⃣ | Pruning：分段回報中間分數，沒希望的提早砍掉 |
    | 7️⃣ | 跟 MLflow 對帳：`search_runs` 撈出整組 trial |
    | 8️⃣ | 續跑與分散式：`storage="sqlite:///optuna.db"` |
    | 9️⃣ | 實驗場：自己選 trial 數、取樣器、要不要 pruner |

    從第一格往下全部執行即可（首次安裝套件約 1–2 分鐘，之後整份跑完約 2 分鐘——
    這一課真的在訓練幾百棵森林，慢是應該的）。
    """
    )
    return


@app.cell
def _():
    import logging
    import shutil
    import tempfile
    import time
    import warnings
    from pathlib import Path

    import marimo as mo
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import mlflow
    import numpy as np
    import optuna
    import pandas as pd
    from sklearn.datasets import make_classification
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.metrics import roc_auc_score
    from sklearn.model_selection import cross_val_score, train_test_split

    # MLflow 的建表提示與 Optuna 每個 trial 一行的 INFO 會蓋掉教學輸出，關小聲；真的出錯還是會噴
    warnings.filterwarnings("ignore")
    logging.getLogger("mlflow").setLevel(logging.ERROR)
    optuna.logging.set_verbosity(optuna.logging.WARNING)

    # 圖表的語義色：藍＝TPE／聰明取樣、橘＝隨機或格點、綠＝目前最佳、紅＝被砍掉
    C_TPE, C_RAND, C_BEST, C_PRUNE = "#4C72B0", "#DD8452", "#55A868", "#C44E52"
    return (
        C_BEST,
        C_PRUNE,
        C_RAND,
        C_TPE,
        Path,
        RandomForestClassifier,
        cross_val_score,
        make_classification,
        mlflow,
        mo,
        np,
        optuna,
        pd,
        plt,
        roc_auc_score,
        shutil,
        tempfile,
        time,
        train_test_split,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 0️⃣ 準備：一份資料、一個評分函式、一本空的紀錄簿

    資料跟這個系列前面幾課完全一樣：模擬的「客戶流失」二元分類，2000 筆、12 個匿名特徵
    `f0`–`f11`，切成 1500 筆訓練 / 500 筆測試。數字對得上，你才好跟前面的課互相印證。

    **調參的評分要用交叉驗證，不能用測試集。** 測試集只准在最後看一次。
    你如果拿測試集當搜尋目標，跑幾十個 trial 之後選出來的「最佳參數」，其實是
    「最會迎合這 500 筆的參數」——那個好看的分數不會出現在正式環境。
    所以這一課的 `cv_auc()` 是**只用訓練集的 3-fold 交叉驗證 ROC-AUC 平均**。

    MLflow 一樣寫在暫存資料夾裡的 sqlite（不連任何伺服器）；每次重跑 notebook 都先清空，
    數字才一致。
    """
    )
    return


@app.cell
def _(
    Path,
    RandomForestClassifier,
    cross_val_score,
    make_classification,
    mlflow,
    mo,
    pd,
    shutil,
    tempfile,
    train_test_split,
):
    WORK = Path(tempfile.gettempdir()) / "optuna-hpo"
    shutil.rmtree(WORK, ignore_errors=True)
    WORK.mkdir(parents=True)

    mlflow.set_tracking_uri(f"sqlite:///{WORK}/mlflow.db")
    EXPERIMENT = "churn-hpo"
    mlflow.create_experiment(EXPERIMENT, artifact_location=str(WORK / "artifacts"))
    mlflow.set_experiment(EXPERIMENT)

    _X, _y = make_classification(
        n_samples=2000, n_features=12, n_informative=6, random_state=0
    )
    _Xdf = pd.DataFrame(_X, columns=[f"f{i}" for i in range(12)])
    X_train, X_test, y_train, y_test = train_test_split(
        _Xdf, _y, test_size=0.25, random_state=0
    )


    def cv_auc(**params):
        """一組超參數 → 3-fold 交叉驗證的 ROC-AUC 平均（只用訓練集）。"""
        model = RandomForestClassifier(random_state=0, **params)
        return cross_val_score(model, X_train, y_train, cv=3, scoring="roc_auc").mean()


    mo.md(
        f"""
    訓練集 **{X_train.shape[0]} 列 × {X_train.shape[1]} 欄**、測試集 **{X_test.shape[0]} 列**；
    紀錄簿在 `{WORK}/mlflow.db`，實驗名 `{EXPERIMENT}`。

    這一課只有一個評分函式：`cv_auc(n_estimators=…, max_depth=…, …)`——
    給它一組參數，回傳一個「越大越好」的數字。接下來所有的搜尋，都是在問它問題。
    """
    )
    return EXPERIMENT, WORK, X_test, X_train, cv_auc, y_test, y_train


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 1️⃣ 手動格點的代價：先把地形畫出來

    先用最笨、最誠實的方法：**格點搜尋**（grid search）——把兩個超參數的每一種組合都跑一次。
    `max_depth` 取 8 個值、`min_samples_leaf` 取 5 個值，就是 **40 次**訓練（每次還含 3 折）。

    畫出來的這張圖是這一課的地圖：**顏色越深＝分數越高**。盯著它問自己三個問題——

    1. 高分區在哪裡？它佔整張圖的幾分之幾？
    2. 兩個軸，哪一個動起來對分數的影響大？
    3. 如果只准你試 10 次，你會試哪 10 格？

    下一格要跑 40 次訓練，大約十幾秒。
    """
    )
    return


@app.cell
def _(C_BEST, cv_auc, np, plt, time):
    GRID_DEPTHS = [2, 4, 6, 8, 10, 12, 14, 16]
    GRID_LEAVES = [1, 3, 5, 7, 10]

    _t0 = time.perf_counter()
    grid_scores = np.array(
        [
            [
                cv_auc(
                    n_estimators=60,
                    max_depth=_d,
                    min_samples_leaf=_l,
                    max_features="sqrt",
                )
                for _l in GRID_LEAVES
            ]
            for _d in GRID_DEPTHS
        ]
    )
    grid_seconds = time.perf_counter() - _t0
    grid_best_ij = np.unravel_index(grid_scores.argmax(), grid_scores.shape)

    _fig, _ax = plt.subplots(figsize=(6.4, 3.5))
    _im = _ax.imshow(grid_scores.T, cmap="YlGnBu", aspect="auto", origin="lower")
    for _i in range(len(GRID_DEPTHS)):
        for _j in range(len(GRID_LEAVES)):
            _v = grid_scores[_i, _j]
            _ax.text(
                _i,
                _j,
                f"{_v:.3f}"[1:],
                ha="center",
                va="center",
                fontsize=7.5,
                color="#fff" if _v > grid_scores.mean() else "#1C2B33",
            )
    _ax.plot(
        grid_best_ij[0], grid_best_ij[1], "o", ms=18, mfc="none", mec=C_BEST, mew=2.5
    )
    _ax.set_xticks(range(len(GRID_DEPTHS)), [str(_d) for _d in GRID_DEPTHS])
    _ax.set_yticks(range(len(GRID_LEAVES)), [str(_l) for _l in GRID_LEAVES])
    _ax.set_xlabel("max_depth")
    _ax.set_ylabel("min_samples_leaf")
    _ax.set_title("Grid search: 40 forests, one score each (cv_auc)")
    _fig.colorbar(_im, ax=_ax, shrink=0.85)
    _fig.tight_layout()
    _fig
    return GRID_DEPTHS, GRID_LEAVES, grid_best_ij, grid_scores, grid_seconds


@app.cell(hide_code=True)
def _(GRID_DEPTHS, GRID_LEAVES, grid_best_ij, grid_scores, grid_seconds, mo):
    _rows_gain = grid_scores.max(axis=1).max() - grid_scores.max(axis=1).min()
    _cols_gain = grid_scores[3:].max(axis=0).max() - grid_scores[3:].max(axis=0).min()
    mo.md(
        f"""
    40 格跑完花了 **{grid_seconds:.0f} 秒**。最好的一格是
    **max_depth={GRID_DEPTHS[grid_best_ij[0]]}、min_samples_leaf={GRID_LEAVES[grid_best_ij[1]]}**
    （cv_auc **{grid_scores.max():.4f}**），最差的一格 **{grid_scores.min():.4f}**。

    看得出三件事：

    - **地形很不平均**：`max_depth` 從 2 走到 8 分數一路往上，過了 10 之後幾乎躺平。
      最左邊那兩排無論 `min_samples_leaf` 怎麼配都追不上——**10 格的預算丟進水裡**。
    - **兩個軸的份量差很多**：橫著走（換 `max_depth`）最好與最差差 **{_rows_gain:.4f}**；
      在夠深的那半邊直著走（換 `min_samples_leaf`）只差 **{_cols_gain:.4f}**，大約是五分之一。
      第 5️⃣ 節會把這個直覺變成一個可以算出來的數字。
    - **格點沒有記憶**：它跑第 40 格的時候，知道的跟跑第 1 格時一樣多。前面 39 次的結果，
      完全沒有拿來決定下一格去哪裡。

    而這還只是**兩個**超參數、每個只取幾個值。真實情況是四個、六個，還有連續值——
    格點根本掃不完。接下來就是 Optuna 上場的地方。
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 2️⃣ 三個名詞：study、trial、objective

    Optuna 的全部語彙只有三個字。先在一個一眼看得懂的函式上認識它們：

    - **objective（目標函式）**——你寫的一個函式，收一個 `trial`、回傳一個分數。
      裡面做兩件事：用 `trial.suggest_*` 說明「這個參數可以在哪個範圍挑」，然後回傳分數。
    - **trial（試驗）**——一次嘗試。它既是「這次用了哪組參數」的紀錄，也是你向 Optuna
      **索取**參數的入口：`trial.suggest_float("x", -10, 10)` 就是在問「這次給我什麼值？」
    - **study（搜尋）**——一整輪搜尋。它記著所有 trial、決定下一個 trial 試什麼、
      最後告訴你 `best_params`。

    下面這個 objective 找的是 (x − 2)² 的最小值——答案當然是 `x = 2`，
    重點是**看 20 個 trial 各自落在哪裡**。
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ```python
    def toy_objective(trial):
        x = trial.suggest_float("x", -10, 10)   # 「x 可以在 -10 到 10 之間挑」
        return (x - 2) ** 2                     # 回傳分數（這一題越小越好）

    study = optuna.create_study(direction="minimize")
    study.optimize(toy_objective, n_trials=20)
    study.best_params        # → {'x': 接近 2 的某個數}
    ```
    """
    )
    return


@app.cell
def _(C_BEST, C_TPE, np, optuna, plt):
    def toy_objective(trial):
        x = trial.suggest_float("x", -10, 10)
        return (x - 2) ** 2


    toy_study = optuna.create_study(
        direction="minimize", sampler=optuna.samplers.TPESampler(seed=0)
    )
    toy_study.optimize(toy_objective, n_trials=20)
    toy_xs = [_t.params["x"] for _t in toy_study.trials]
    toy_ys = [_t.value for _t in toy_study.trials]

    _fig, _ax = plt.subplots(figsize=(6.3, 3.4))
    _curve = np.linspace(-10, 10, 300)
    _ax.plot(_curve, (_curve - 2) ** 2, color="#C9D2C6", lw=2, zorder=1)
    _ax.scatter(
        toy_xs, toy_ys, s=95, c=C_TPE, zorder=3, edgecolor="#fff", linewidth=1.2
    )
    for _i, (_x, _y) in enumerate(zip(toy_xs, toy_ys)):
        _ax.annotate(
            str(_i + 1),
            (_x, _y),
            fontsize=7.5,
            color="#fff",
            ha="center",
            va="center",
            zorder=4,
        )
    _ax.axvline(2, color=C_BEST, ls="--", lw=1.5, zorder=2)
    _ax.text(2.5, 95, "true minimum  x = 2", color=C_BEST, fontsize=9)
    _ax.set_xlabel("x  (what trial.suggest_float returned)")
    _ax.set_ylabel("objective value  (lower is better)")
    _ax.set_title("20 trials, numbered in the order Optuna tried them")
    _ax.spines[["top", "right"]].set_visible(False)
    _fig.tight_layout()
    _fig
    return toy_objective, toy_study, toy_xs, toy_ys


@app.cell(hide_code=True)
def _(mo, toy_study, toy_xs):
    _near = sum(1 for _x in toy_xs if abs(_x - 2) < 1)
    mo.md(
        f"""
    20 個 trial 之後：`best_params` 是 **x = {toy_study.best_params["x"]:.3f}**、
    `best_value` **{toy_study.best_value:.4f}**——在一個寬度 20 的範圍裡，
    誤差 {abs(toy_study.best_params["x"] - 2):.3f}。20 個點裡有 {_near} 個落在正確答案 ±1 之內。

    但你八成也發現了：**點並沒有乖乖地一路收斂到 2**，後半段照樣有點跑到 −8、+9 去。
    這不是壞掉，是設計：

    - **TPE 不是梯度下降**。它把看過的 trial 分成「比較好的一群」與「比較差的一群」，
      分別去猜它們的分佈長什麼樣，然後挑一個「落在好的那群裡的機率相對高」的位置。
      這個機制天生會保留一定比例的**探索**——不然遇到有兩個谷的地形，它會死在第一個谷裡。
    - **前 10 個 trial 根本還沒開始學**。Optuna 預設 `n_startup_trials=10`：
      前 10 次是純隨機暖身，因為沒有資料就沒得學。

    所以看搜尋有沒有進展，要看的是「**目前為止的最佳**」這條會往上（或往下）走的線，
    不是單一個點的位置。下一節開始，每張圖都會有這條線。

    順帶一提，這也預告了一件事：**trial 只有十幾個的時候，TPE 跟隨機亂猜是沒有差別的**
    ——第 4️⃣ 節會把這句話量給你看。
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 3️⃣ 真實任務：四個超參數、25 個 trial、25 個 MLflow run

    換成真的東西。RandomForest 四個旋鈕，順便把三種 `suggest_*` 各示範一次：

    | 參數 | 寫法 | 為什麼這樣寫 |
    |---|---|---|
    | `n_estimators` | `suggest_int("n_estimators", 20, 200, step=20)` | 樹多 1 棵沒有意義，`step=20` 讓它只挑 20/40/…/200，搜尋空間小 10 倍 |
    | `max_depth` | `suggest_int("max_depth", 2, 16)` | 每一個整數都可能有差，不設 step |
    | `min_samples_leaf` | `suggest_int("min_samples_leaf", 1, 10)` | 同上 |
    | `max_features` | `suggest_categorical("max_features", ["sqrt", "log2", None])` | 選項之間沒有大小順序，只能列舉 |

    還有一個這裡用不到、但你遲早會用到的：**`suggest_float("lr", 1e-5, 1e-1, log=True)`**。
    學習率、正規化強度這種參數，「0.001 → 0.01」跟「0.01 → 0.1」是同一個等級的改變，
    但在線性尺度上後者的距離大 10 倍——`log=True` 讓取樣在**數量級上**均勻。
    不加的話，你的搜尋會有九成落在 0.01 以上那一段，等於沒搜到小的那頭。

    每個 trial 在 MLflow 開一個 **nested run**（`nested=True`）：參數、分數、trial 編號全部記進去；
    整輪搜尋自己是一個 **parent run**，記下最後的最佳參數。
    第 1 課的 parent／nested 結構，在這裡剛好就是「一次搜尋／一個 trial」。
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ```python
    def objective(trial):
        params = {
            "n_estimators": trial.suggest_int("n_estimators", 20, 200, step=20),
            "max_depth": trial.suggest_int("max_depth", 2, 16),
            "min_samples_leaf": trial.suggest_int("min_samples_leaf", 1, 10),
            "max_features": trial.suggest_categorical("max_features", ["sqrt", "log2", None]),
        }
        with mlflow.start_run(run_name=f"trial-{trial.number}", nested=True):
            mlflow.log_params(params)
            mlflow.set_tag("optuna_trial", trial.number)
            score = cv_auc(**params)
            mlflow.log_metric("cv_auc", score)
            trial.set_user_attr("mlflow_run_id", mlflow.active_run().info.run_id)
        return score          # ← Optuna 只看這一個數字
    ```
    """
    )
    return


@app.cell
def _(cv_auc, mlflow, mo, optuna, time):
    N_TRIALS = 25


    def objective(trial):
        params = {
            "n_estimators": trial.suggest_int("n_estimators", 20, 200, step=20),
            "max_depth": trial.suggest_int("max_depth", 2, 16),
            "min_samples_leaf": trial.suggest_int("min_samples_leaf", 1, 10),
            "max_features": trial.suggest_categorical(
                "max_features", ["sqrt", "log2", None]
            ),
        }
        with mlflow.start_run(run_name=f"trial-{trial.number}", nested=True):
            mlflow.log_params(params)
            mlflow.set_tag("optuna_trial", trial.number)
            score = cv_auc(**params)
            mlflow.log_metric("cv_auc", score)
            trial.set_user_attr("mlflow_run_id", mlflow.active_run().info.run_id)
        return score


    _t0 = time.perf_counter()
    study = optuna.create_study(
        study_name="rf-tpe",
        direction="maximize",
        sampler=optuna.samplers.TPESampler(seed=0),
    )
    with mlflow.start_run(run_name="optuna-tpe-25") as _parent:
        study.optimize(objective, n_trials=N_TRIALS)
        mlflow.log_params({f"best_{_k}": _v for _k, _v in study.best_params.items()})
        mlflow.log_metric("best_cv_auc", study.best_value)
        mlflow.set_tag("sampler", "TPESampler(seed=0)")
        parent_run_id = _parent.info.run_id
    tpe_seconds = time.perf_counter() - _t0

    mo.md(
        f"""
    **{N_TRIALS} 個 trial 跑完，花了 {tpe_seconds:.0f} 秒**（每個 trial 一次 3 折交叉驗證）。

    - `study.best_value` = **{study.best_value:.4f}**
    - `study.best_params` = `{study.best_params}`
    - 最佳的是第 **{study.best_trial.number}** 號 trial（編號從 0 開始）
    - MLflow 那邊：parent run `{parent_run_id[:8]}…` 底下掛了 {N_TRIALS} 個 nested run
    """
    )
    return N_TRIALS, objective, parent_run_id, study, tpe_seconds


@app.cell(hide_code=True)
def _(mo, study):
    _cols = [
        "number",
        "value",
        "params_n_estimators",
        "params_max_depth",
        "params_min_samples_leaf",
        "params_max_features",
    ]
    trials_df = study.trials_dataframe()
    _sorted = trials_df[_cols].sort_values("value", ascending=False).round(4)
    mo.vstack(
        [
            mo.md("**依分數排序的前 5 名**（`study.trials_dataframe()` 就是一張 pandas 表）："),
            mo.ui.table(_sorted.head(5), selection=None),
            mo.md("**倒數 3 名**——看看它們輸在哪個參數上："),
            mo.ui.table(_sorted.tail(3), selection=None),
        ]
    )
    return (trials_df,)


@app.cell
def _(C_BEST, C_TPE, np, plt, study):
    _vals = [_t.value for _t in study.trials]
    _cum = np.maximum.accumulate(_vals)
    _fig, _ax = plt.subplots(figsize=(6.3, 3.5))
    _ax.scatter(
        range(len(_vals)), _vals, s=55, c=C_TPE, zorder=3, edgecolor="#fff", linewidth=1
    )
    _ax.step(range(len(_cum)), _cum, where="post", color=C_BEST, lw=2.2, zorder=2)
    _ax.annotate(
        f"best {_cum[-1]:.4f}",
        (len(_cum) - 1, _cum[-1]),
        textcoords="offset points",
        xytext=(-6, 8),
        ha="right",
        fontsize=9,
        color=C_BEST,
        fontweight="bold",
    )
    _ax.set_xlabel("trial number")
    _ax.set_ylabel("cv_auc")
    _ax.set_title("Every trial (dots) and the best so far (line)")
    _ax.spines[["top", "right"]].set_visible(False)
    _fig.tight_layout()
    _fig
    return


@app.cell(hide_code=True)
def _(mo, np, study):
    _vals = [_t.value for _t in study.trials]
    _worst_i = int(np.argmin(_vals))
    _late = _vals[10:]
    mo.md(
        f"""
    這張圖有兩層資訊，別只看線：

    - **綠色階梯線＝目前為止的最佳。** 它只會往上，而且越走越平——這就是「什麼時候可以停」
      的依據：連續十幾個 trial 都推不動它，再跑下去的期望值就很低了。
    - **藍點＝每個 trial 的真實分數。** 點的**分佈**才是重點：第 10 號之後，
      最差的一個 trial 也有 **{min(_late):.4f}**，而前 10 個裡最差的是 **{min(_vals[:10]):.4f}**。
      這就是 TPE 學到「該去哪裡」的樣子——**它不是每一發都更好，它是不再往爛區丟**。

    整場最差的是第 {_worst_i} 號 trial（{min(_vals):.4f}），參數
    `{study.trials[_worst_i].params}`——`max_depth` 太小的森林，其他旋鈕怎麼轉都救不回來。
    跟第 1️⃣ 節那張地形圖說的是同一件事。
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 4️⃣ TPE 真的比亂猜好嗎？

    「聰明地挑下一組」聽起來很棒，但值得懷疑。所以直接量：同一個 objective、同一個搜尋空間、
    同樣 25 個 trial，只把取樣器換成 **`RandomSampler`**（純隨機亂挑）。

    ```python
    optuna.create_study(direction="maximize", sampler=optuna.samplers.RandomSampler(seed=0))
    ```

    先猜一下再往下跑：你覺得兩邊的最佳值會差多少？
    """
    )
    return


@app.cell
def _(cv_auc, optuna, time):
    def objective_plain(trial):
        """跟第 3️⃣ 節同一個目標函式，只是不記 MLflow——對照組要乾淨。"""
        return cv_auc(
            n_estimators=trial.suggest_int("n_estimators", 20, 200, step=20),
            max_depth=trial.suggest_int("max_depth", 2, 16),
            min_samples_leaf=trial.suggest_int("min_samples_leaf", 1, 10),
            max_features=trial.suggest_categorical(
                "max_features", ["sqrt", "log2", None]
            ),
        )


    _t0 = time.perf_counter()
    rnd_study = optuna.create_study(
        direction="maximize", sampler=optuna.samplers.RandomSampler(seed=0)
    )
    rnd_study.optimize(objective_plain, n_trials=25)
    rnd_seconds = time.perf_counter() - _t0
    return objective_plain, rnd_seconds, rnd_study


@app.cell
def _(C_RAND, C_TPE, np, plt, rnd_study, study):
    tpe_vals = [_t.value for _t in study.trials]
    rnd_vals = [_t.value for _t in rnd_study.trials]

    _fig, _ax = plt.subplots(figsize=(6.3, 3.6))
    _ax.scatter(range(len(tpe_vals)), tpe_vals, s=26, c=C_TPE, alpha=0.5, zorder=2)
    _ax.scatter(range(len(rnd_vals)), rnd_vals, s=26, c=C_RAND, alpha=0.5, zorder=2)
    _ax.step(
        range(len(tpe_vals)),
        np.maximum.accumulate(tpe_vals),
        where="post",
        color=C_TPE,
        lw=2.4,
        label="TPESampler",
        zorder=3,
    )
    _ax.step(
        range(len(rnd_vals)),
        np.maximum.accumulate(rnd_vals),
        where="post",
        color=C_RAND,
        lw=2.4,
        label="RandomSampler",
        zorder=3,
    )
    _ax.axvspan(-0.5, 9.5, color="#EEF1EC", zorder=0)
    _ax.text(4.5, min(rnd_vals) + 0.002, "TPE is still random here\n(n_startup_trials=10)",
             ha="center", fontsize=8, color="#52646E")
    _ax.set_xlabel("trial number")
    _ax.set_ylabel("cv_auc  (dots) / best so far (lines)")
    _ax.set_title("Same budget, same space, different sampler")
    _ax.legend(loc="lower right", fontsize=9)
    _ax.spines[["top", "right"]].set_visible(False)
    _fig.tight_layout()
    _fig
    return rnd_vals, tpe_vals


@app.cell(hide_code=True)
def _(mo, np, rnd_study, rnd_vals, study, tpe_vals):
    _same10 = tpe_vals[:10] == rnd_vals[:10]
    _t_late, _r_late = tpe_vals[10:], rnd_vals[10:]
    _rnd_best_i = int(np.argmax(rnd_vals))
    mo.md(
        f"""
    | | TPESampler | RandomSampler |
    |---|---|---|
    | 最佳 cv_auc | **{study.best_value:.4f}** | **{rnd_study.best_value:.4f}** |
    | 25 個 trial 的平均 | {np.mean(tpe_vals):.4f} | {np.mean(rnd_vals):.4f} |
    | 第 10 號之後最差的一次 | **{min(_t_late):.4f}** | **{min(_r_late):.4f}** |
    | 前 10 個 trial 是否一模一樣 | {'是' if _same10 else '否'} | {'是' if _same10 else '否'} |

    三個結論，其中一個大概不是你預期的：

    **① 前 10 個 trial 兩邊完全相同。** 不是巧合：TPE 的暖身期就是拿隨機取樣器在跑，
    種子也一樣，所以兩條線在第 10 號之前完全重疊。**這是「小規模時 TPE ≈ 隨機」最硬的證據。**

    **② 這一局，最佳值是隨機贏。** {rnd_study.best_value:.4f} 對 {study.best_value:.4f}
    ——隨機在第 {_rnd_best_i} 號 trial 矇到一個好組合。這種事會發生，而且很常發生：
    25 個 trial 對四維空間來說太少，運氣的份量還很重。
    （如果你重跑的結果反過來是 TPE 贏，那正好說明同一件事：這種規模的勝負，
    有一大半是運氣。）
    （我們另外用 seed 1／2／3 各重跑過一輪，TPE 是 0.9716／0.9720／0.9717，
    隨機是 0.9716／0.9704／0.9684——**TPE 兩勝一平，加上這局的一敗**。這才是誠實的比數。）

    **③ 但 trial 的「品質」差很多。** 第 10 號之後，TPE 最差的一次是 {min(_t_late):.4f}，
    隨機最差的是 {min(_r_late):.4f}——隨機還在往 `max_depth=2` 那種爛區丟，TPE 已經不去了。
    平均分數 {np.mean(tpe_vals):.4f} 對 {np.mean(rnd_vals):.4f} 也是同一件事。

    **所以 TPE 的價值到底是什麼？** 不是「保證找到更好的答案」，而是
    **「同樣的預算，浪費得比較少」**。這件事在下面三種情況下會被放大到無法忽視：
    trial 數多（幾百次以上）、搜尋空間大（十幾個超參數）、單次評估很貴（訓練一次要好幾小時）。
    你的問題如果是「四個參數、跑 20 次就夠」，老實說隨機搜尋也很好用——
    真正划算的是下一節那件事：**用第一輪的結果把空間縮小，再跑第二輪**。
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ### 一個免費的模擬器：拿第 1️⃣ 節的 40 格來比

    上面那場對照，兩輪加起來跑了幾十秒——因為每個 trial 都要真的訓練一片森林。
    但第 1️⃣ 節已經把 40 格的分數**全部算過一遍了**——直接拿它當查表函式，
    取樣器的比較就變成**零成本**（毫秒級），而且分數全是真的。

    這次的對手換成「**照順序掃的格點**」：`for max_depth: for min_samples_leaf:`，
    也就是絕大多數人手寫巢狀迴圈時的樣子。
    """
    )
    return


@app.cell
def _(GRID_DEPTHS, GRID_LEAVES, grid_scores, mo, np, optuna):
    def lookup_objective(trial):
        _d = trial.suggest_categorical("max_depth", GRID_DEPTHS)
        _l = trial.suggest_categorical("min_samples_leaf", GRID_LEAVES)
        return float(grid_scores[GRID_DEPTHS.index(_d), GRID_LEAVES.index(_l)])


    lookup_study = optuna.create_study(
        direction="maximize", sampler=optuna.samplers.TPESampler(seed=0)
    )
    lookup_study.optimize(lookup_objective, n_trials=25)
    lookup_tpe_seq = [
        (GRID_DEPTHS.index(_t.params["max_depth"]), GRID_LEAVES.index(_t.params["min_samples_leaf"]))
        for _t in lookup_study.trials
    ]
    lookup_tpe_best = np.maximum.accumulate([_t.value for _t in lookup_study.trials])
    lookup_grid_best = np.maximum.accumulate(
        [grid_scores[_k // len(GRID_LEAVES), _k % len(GRID_LEAVES)] for _k in range(40)]
    )

    _rows = [
        {
            "試了幾次": _n,
            "TPE 目前最佳": f"{lookup_tpe_best[_n - 1]:.4f}",
            "格點順序掃 目前最佳": f"{lookup_grid_best[_n - 1]:.4f}",
        }
        for _n in (5, 10, 15, 20, 25)
    ]
    mo.vstack(
        [
            mo.ui.table(_rows, selection=None),
            mo.md(
                f"TPE 造訪過 **{len(set(lookup_tpe_seq))}** 個不同的格子（25 次裡有重複——"
                "它會回頭把好的區域再確認一遍）。"
            ),
        ]
    )
    return lookup_grid_best, lookup_objective, lookup_study, lookup_tpe_best, lookup_tpe_seq


@app.cell(hide_code=True)
def _(grid_scores, lookup_grid_best, lookup_tpe_best, mo):
    mo.md(
        f"""
    這張表把「Optuna 到底值不值得」講得比什麼都清楚：

    - **第 5 次**：TPE 已經站在 {lookup_tpe_best[4]:.4f}，格點還在 {lookup_grid_best[4]:.4f}
      ——因為巢狀迴圈的第一層是 `max_depth`，它把前 5 次全花在最淺、也最爛的那一排上。
    - **第 15 次**：TPE {lookup_tpe_best[14]:.4f}，格點 {lookup_grid_best[14]:.4f}。
    - **第 25 次**：格點終於掃到那一格，反而**贏了** {lookup_grid_best[24]:.4f} vs {lookup_tpe_best[24]:.4f}。

    最後那一行不是我們寫壞了，是這個實驗最重要的一句話：
    **空間小到掃得完的時候，格點最後一定會贏——因為它會把每一格都看過。**
    Optuna 的價值不在「終點」，在**「同樣的預算下，你現在手上有多好的答案」**：
    這張地形只有 40 格，真實任務動輒幾萬、幾百萬格，你永遠掃不到終點，
    能拿到的就只有「跑完預算那一刻手上的最佳」。

    （全場最高的一格是 {grid_scores.max():.4f}。TPE 這 25 次沒踩到它，
    但它一路都在那一格的鄰居上打轉——差距 {grid_scores.max() - lookup_tpe_best[24]:.4f}。）
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 5️⃣ 參數重要度：下一輪該把力氣花在哪

    跑完一輪，最有價值的產物**不是那組最佳參數**，是「**哪個旋鈕真的重要**」。
    Optuna 可以直接算給你：

    ```python
    evaluator = optuna.importance.FanovaImportanceEvaluator(seed=0)
    optuna.importance.get_param_importances(study, evaluator=evaluator)
    ```

    它的做法（fANOVA）是：拿你跑過的所有 trial 當訓練資料，訓練一個「參數 → 分數」的小模型，
    再問這個模型「分數的變異，有多少可以歸給每個參數」。輸出加起來是 1。

    `seed=0` 很重要——這個評估器本身是隨機的，不給種子的話同一個 study 每次算出來會差幾個百分點。
    """
    )
    return


@app.cell
def _(C_TPE, mo, optuna, plt, study):
    param_importance = optuna.importance.get_param_importances(
        study, evaluator=optuna.importance.FanovaImportanceEvaluator(seed=0)
    )
    _names = list(param_importance)[::-1]
    _vals = [float(param_importance[_n]) for _n in _names]

    _fig, _ax = plt.subplots(figsize=(6.0, 2.9))
    _ax.barh(_names, _vals, color=C_TPE, height=0.6)
    for _n, _v in zip(_names, _vals):
        _ax.text(_v + 0.012, _n, f"{_v:.3f}", va="center", fontsize=9)
    _ax.set_xlim(0, 1.08)
    _ax.set_xlabel("share of the score variance explained (fANOVA)")
    _ax.set_title("Which knob actually matters?")
    _ax.spines[["top", "right"]].set_visible(False)
    _fig.tight_layout()
    mo.vstack([_fig])
    return (param_importance,)


@app.cell(hide_code=True)
def _(mo, param_importance):
    _top = next(iter(param_importance))
    _rest = list(param_importance)[1:]
    mo.md(
        f"""
    **`{_top}` 一個人吃掉 {param_importance[_top]:.0%} 的變異**，
    其餘三個（{"、".join(f"`{_p}`" for _p in _rest)}）加起來不到
    {sum(param_importance[_p] for _p in _rest):.0%}。

    這正是第 1️⃣ 節那張地形圖的數字版：橫著走影響大、直著走影響小。
    重要度的用途不是拿來炫耀，是**決定下一輪怎麼搜**：

    | 重要度告訴你 | 下一輪就 |
    |---|---|
    | 某個參數獨大 | 把它的範圍**縮到最佳值附近**、取樣密一點 |
    | 某個參數幾乎是 0 | **固定成常數**，把省下來的預算讓給重要的那個 |
    | 某個參數的最佳值**貼在範圍邊界** | 把邊界**往外推**——真正的最佳可能在你的範圍之外 |

    ⚠️ 兩個必要的警告：

    - **重要度是估計，不是物理常數。** 它是從你跑過的 trial 推出來的，
      而那些 trial 又是 TPE 挑的（集中在高分區）——所以它回答的是
      「**在我搜過的那一帶**，哪個參數影響大」，不是「這個模型的宇宙真理」。
    - **換一個評估器，答案可能完全不同。** 同一個 study 換成
      `PedAnovaImportanceEvaluator()`，這裡算出來排第一的會變成 `min_samples_leaf`。
      把它當「下一輪往哪裡搜」的線索，不要當定論。
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ### 照著重要度跑第二輪

    第一輪的四個參數裡，只有一個真的重要。那就照上面那張表做：
    `max_features` 直接**固定成 `"sqrt"`**（第一輪前幾名清一色是它），
    `max_depth` 縮到 8–14、`min_samples_leaf` 縮到 1–4、`n_estimators` 下限拉高到 40。

    空間小了，同樣的 trial 數就能搜得更密——**這一輪只跑 10 個 trial**。
    """
    )
    return


@app.cell
def _(cv_auc, mlflow, mo, optuna, study, time, tpe_seconds):
    def objective_round2(trial):
        return cv_auc(
            n_estimators=trial.suggest_int("n_estimators", 40, 200, step=20),
            max_depth=trial.suggest_int("max_depth", 8, 14),
            min_samples_leaf=trial.suggest_int("min_samples_leaf", 1, 4),
            max_features="sqrt",
        )


    _t0 = time.perf_counter()
    study2 = optuna.create_study(
        study_name="rf-tpe-round2",
        direction="maximize",
        sampler=optuna.samplers.TPESampler(seed=0),
    )
    with mlflow.start_run(run_name="optuna-tpe-round2"):
        study2.optimize(objective_round2, n_trials=10)
        mlflow.log_params({f"best_{_k}": _v for _k, _v in study2.best_params.items()})
        mlflow.log_metric("best_cv_auc", study2.best_value)
        mlflow.set_tag("round", "2")
    round2_seconds = time.perf_counter() - _t0

    mo.md(
        f"""
    | | trial 數 | 耗時 | 最佳 cv_auc | 最佳參數 |
    |---|---|---|---|---|
    | 第一輪（大空間） | 25 | {tpe_seconds:.0f} 秒 | {study.best_value:.4f} | `{study.best_params}` |
    | **第二輪（縮小後）** | **10** | **{round2_seconds:.0f} 秒** | **{study2.best_value:.4f}** | `{study2.best_params}` |

    **少了 15 個 trial、少花一半以上的時間，分數卻更高（+{study2.best_value - study.best_value:.4f}）。**
    更值得看的是分佈：第二輪 10 個 trial 裡有
    **{sum(1 for _t in study2.trials if _t.value > study.best_value)} 個**比第一輪跑 25 次的最佳
    （{study.best_value:.4f}）還高，最差的一個也有 {min(_t.value for _t in study2.trials):.4f}
    ——因為它們全都落在好區裡。

    這就是調參真正的流程，而且它是一個**迴圈**：

    > 大範圍粗搜 → 看重要度與最佳值的位置 → 縮小／平移範圍、固定不重要的參數 → 再搜一輪。

    別把它想成「跑一次 200 個 trial」。**兩輪各 25 次，幾乎永遠贏過一輪 50 次**，
    因為第二輪的每一次都花在對的地方。
    """
    )
    return objective_round2, round2_seconds, study2


@app.cell(hide_code=True)
def _(mo, optuna, param_importance, study2):
    _imp2 = optuna.importance.get_param_importances(
        study2, evaluator=optuna.importance.FanovaImportanceEvaluator(seed=0)
    )
    _line = "、".join(f"`{_k}` {float(_v):.2f}" for _k, _v in _imp2.items())
    _top1 = next(iter(param_importance))
    mo.md(
        f"""
    再算一次第二輪的重要度，會看到一件很值得記住的事：{_line}
    ——**`{_top1}` 不再獨大了**。

    這不代表它突然變得不重要，而是：重要度衡量的是「**在你搜過的範圍裡**，
    這個參數造成多少分數差異」。第二輪的 `max_depth` 只在 8–14 之間跑，
    那一段本來就平坦（回去看第 1️⃣ 節的地形圖），差異自然就小了。

    所以重要度是**一個相對於當前搜尋空間的量**。把它當成「下一步該往哪裡走」的方向盤，
    不要當成「這個模型的參數排行榜」。
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ### 最後一次：動測試集

    整堂課到現在，`X_test` 一次都沒有被碰過——現在是它唯一該登場的時候。
    拿第二輪的最佳參數在**完整訓練集**上訓練一次，在測試集上評一次分。

    這個數字不是拿來繼續調參的（一調就作廢了），它只回答一個問題：
    **我在交叉驗證上看到的分數，可信嗎？**
    """
    )
    return


@app.cell
def _(
    RandomForestClassifier,
    X_test,
    X_train,
    mlflow,
    mo,
    roc_auc_score,
    study2,
    y_test,
    y_train,
):
    _final = RandomForestClassifier(
        random_state=0, max_features="sqrt", **study2.best_params
    ).fit(X_train, y_train)
    test_auc = roc_auc_score(y_test, _final.predict_proba(X_test)[:, 1])
    with mlflow.start_run(run_name="final-best-model"):
        mlflow.log_params(study2.best_params)
        mlflow.log_metric("cv_auc", study2.best_value)
        mlflow.log_metric("test_auc", test_auc)
        mlflow.set_tag("stage", "final")

    mo.md(
        f"""
    | | 分數 |
    |---|---|
    | 搜尋時看到的（訓練集 3 折交叉驗證） | {study2.best_value:.4f} |
    | **測試集（只看這一次）** | **{test_auc:.4f}** |

    兩個數字相差 {abs(test_auc - study2.best_value):.4f}——**很接近，就是好消息**：
    代表這一輪搜尋沒有擬合到交叉驗證的切分方式，那個 0.97 是真的。

    反過來說，如果測試分數比搜尋分數低很多（例如差 0.02 以上），
    那通常是**搜尋擬合了驗證資料**：跑了幾百個 trial 之後，「最佳參數」開始迎合
    交叉驗證切分裡的雜訊。這種時候該做的不是再多跑幾百個 trial，而是換更穩的評估
    （折數多一點、或重複幾次不同切分取平均）。

    這個 run 也記進 MLflow 了——接下來要 `log_model`、註冊進 Registry、走第 6 課的上線流程，
    都是第 2 課教過的事。**HPO 的產物就是一組參數，它要接回原本的管線才有價值。**
    """
    )
    return (test_auc,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 6️⃣ Pruning：沒希望的 trial 不用跑完

    到目前為止，每個 trial 都是「訓練完 → 給一個分數」。但很多模型其實可以**邊訓練邊報分數**：
    GBDT 每加一輪樹、神經網路每跑完一個 epoch、隨機森林每多長一批樹——中間都有一個暫時的成績。

    有了中間分數，就可以做一件很划算的事：**跟別人比，比輸太多就直接放棄。**

    做法只要在 objective 裡加兩行：

    ```python
    for step in (1, 2, 3):
        ...訓練到這個階段、算出 score...
        trial.report(score, step)          # ① 回報「我現在幾分」
        if trial.should_prune():           # ② 問 pruner「我還有救嗎」
            raise optuna.TrialPruned()     #    沒救就自首，這個 trial 標成 PRUNED
    ```

    `MedianPruner` 的判準很直白：**在同一個階段，你比其他 trial 的中位數還差，就砍。**
    （`n_startup_trials=5` 是「前 5 個 trial 一律跑完」——沒有樣本就沒有中位數可以比。）

    這一節把森林拆成三段（先長 1/3 的樹、再 2/3、再全部），每一段報一次分數。
    ⚠️ 分數用的是**從訓練集再切出來的 375 列驗證集**（不是交叉驗證，也不是測試集），
    所以**這一節的數字不能跟前面幾節比大小**——它是另一把尺。
    """
    )
    return


@app.cell
def _(
    RandomForestClassifier,
    X_train,
    optuna,
    roc_auc_score,
    train_test_split,
    y_train,
):
    X_fit, X_val, y_fit, y_val = train_test_split(
        X_train, y_train, test_size=0.25, random_state=1
    )
    STAGE_TRIALS = 15


    def staged_objective(trial):
        _n = trial.suggest_int("n_estimators", 30, 300, step=30)
        _d = trial.suggest_int("max_depth", 2, 16)
        _leaf = trial.suggest_int("min_samples_leaf", 1, 10)
        _score = 0.0
        for _step in (1, 2, 3):                       # 先長 1/3 的樹，再 2/3，再全部
            _part = max(5, _n * _step // 3)
            _m = RandomForestClassifier(
                n_estimators=_part,
                max_depth=_d,
                min_samples_leaf=_leaf,
                max_features="sqrt",
                random_state=0,
            ).fit(X_fit, y_fit)
            _score = roc_auc_score(y_val, _m.predict_proba(X_val)[:, 1])
            trial.report(_score, _step)               # ① 回報中間分數
            if trial.should_prune():                  # ② 問 pruner 還有沒有救
                raise optuna.TrialPruned()
        return _score
    return STAGE_TRIALS, X_fit, X_val, staged_objective, y_fit, y_val


@app.cell
def _(STAGE_TRIALS, optuna, staged_objective, time):
    _t0 = time.perf_counter()
    study_nop = optuna.create_study(
        direction="maximize",
        sampler=optuna.samplers.TPESampler(seed=0),
        pruner=optuna.pruners.NopPruner(),          # NopPruner ＝ 完全不砍
    )
    study_nop.optimize(staged_objective, n_trials=STAGE_TRIALS)
    nop_seconds = time.perf_counter() - _t0

    _t0 = time.perf_counter()
    study_pruned = optuna.create_study(
        direction="maximize",
        sampler=optuna.samplers.TPESampler(seed=0),
        pruner=optuna.pruners.MedianPruner(n_startup_trials=5, n_warmup_steps=0),
    )
    study_pruned.optimize(staged_objective, n_trials=STAGE_TRIALS)
    pruned_seconds = time.perf_counter() - _t0

    n_pruned = sum(
        _t.state == optuna.trial.TrialState.PRUNED for _t in study_pruned.trials
    )
    return n_pruned, nop_seconds, pruned_seconds, study_nop, study_pruned


@app.cell
def _(C_BEST, C_PRUNE, optuna, plt, study_pruned):
    _fig, _ax = plt.subplots(figsize=(6.3, 3.6))
    for _t in study_pruned.trials:
        _steps = sorted(_t.intermediate_values)
        _vals = [_t.intermediate_values[_s] for _s in _steps]
        _is_pruned = _t.state == optuna.trial.TrialState.PRUNED
        _ax.plot(
            _steps,
            _vals,
            "-o" if not _is_pruned else "--x",
            color=C_PRUNE if _is_pruned else C_BEST,
            lw=1.6,
            ms=7 if _is_pruned else 5,
            alpha=0.9 if _is_pruned else 0.75,
        )
    _ax.plot([], [], "-o", color=C_BEST, label="ran to the end")
    _ax.plot([], [], "--x", color=C_PRUNE, label="pruned after step 1")
    _ax.set_xticks([1, 2, 3], ["1/3 of trees", "2/3 of trees", "all trees"])
    _ax.set_xlabel("reporting step")
    _ax.set_ylabel("validation AUC")
    _ax.set_title("MedianPruner cuts the ones already behind")
    _ax.legend(loc="lower right", fontsize=9)
    _ax.spines[["top", "right"]].set_visible(False)
    _fig.tight_layout()
    _fig
    return


@app.cell(hide_code=True)
def _(
    STAGE_TRIALS,
    mo,
    n_pruned,
    nop_seconds,
    pruned_seconds,
    study_nop,
    study_pruned,
):
    mo.md(
        f"""
    | {STAGE_TRIALS} 個 trial | 耗時 | 被砍掉 | 最佳驗證 AUC |
    |---|---|---|---|
    | `NopPruner()`（不砍） | {nop_seconds:.1f} 秒 | 0 | {study_nop.best_value:.4f} |
    | **`MedianPruner()`** | **{pruned_seconds:.1f} 秒** | **{n_pruned} 個** | **{study_pruned.best_value:.4f}** |

    **省下 {(1 - pruned_seconds / nop_seconds) * 100:.0f}% 的時間，最佳值一模一樣。**
    圖上那些紅色虛線就是被砍掉的 trial——它們在只長了 1/3 棵樹的時候就已經落在中位數之下，
    再長完剩下 2/3 也追不回來，於是 Optuna 直接讓它們退場。

    幾件實務上會咬人的事：

    - **pruning 只對「能分段回報」的模型有意義。** 你的 objective 如果是一個
      `cross_val_score(...)` 就結束（像第 3️⃣ 節那樣），中間沒有任何可回報的分數，
      pruner 就沒有東西可砍。要嘛改成「一折報一次」，要嘛就別用。
    - **不要把 pruning 想成免費的。** 它是在賭「現在落後的，最後也贏不了」。
      對於**先慢後快**的訓練曲線（有些學習率排程就是這樣），這個賭注會輸——
      這時候把 `n_warmup_steps` 調大，讓每個 trial 至少跑幾步再開始評判。
    - **被砍掉的 trial 不是白跑的。** 它照樣進 study，TPE 也會參考它們的中間分數；
      在 `trials_dataframe()` 裡它們的 `state` 是 `PRUNED`、`value` 是空的。
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 7️⃣ 跟 MLflow 對帳：`search_runs` 撈出整組 trial

    第 3️⃣ 節每個 trial 都開了一個 nested run。現在用第 1 課學的 `search_runs`，
    用 `tags.mlflow.parentRunId` 把整組撈回來，**跟 Optuna 自己的紀錄對答案**：

    ```python
    mlflow.search_runs(
        experiment_names=["churn-hpo"],
        filter_string=f"tags.mlflow.parentRunId = '{parent_run_id}'",
        order_by=["metrics.cv_auc DESC"],
    )
    ```
    """
    )
    return


@app.cell
def _(EXPERIMENT, mlflow, mo, parent_run_id, study):
    child_runs = mlflow.search_runs(
        experiment_names=[EXPERIMENT],
        filter_string=f"tags.mlflow.parentRunId = '{parent_run_id}'",
        order_by=["metrics.cv_auc DESC"],
    )
    _view = child_runs[
        [
            "tags.mlflow.runName",
            "metrics.cv_auc",
            "params.n_estimators",
            "params.max_depth",
            "params.min_samples_leaf",
            "params.max_features",
        ]
    ].head(5)
    _match = (
        child_runs.iloc[0]["tags.mlflow.runName"] == f"trial-{study.best_trial.number}"
    )
    mo.vstack(
        [
            mo.md(f"parent run 底下撈到 **{len(child_runs)} 個子 run**，依 `cv_auc` 由高到低："),
            mo.ui.table(_view.round(5), selection=None),
            mo.md(
                f"MLflow 排第一的是 `{child_runs.iloc[0]['tags.mlflow.runName']}`，"
                f"Optuna 的 `best_trial.number` 是 **{study.best_trial.number}** → "
                f"**{'對得上 ✅' if _match else '對不上 ⚠️'}**"
            ),
        ]
    )
    return (child_runs,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    兩邊都記，是不是多此一舉？不是——**它們記的東西不一樣，缺一個都會痛**：

    | | Optuna 的 study | MLflow 的 run |
    |---|---|---|
    | 記什麼 | 參數、分數、狀態、取樣器要用的分佈資訊 | 參數、指標、標籤、**任何檔案**（模型、圖、資料快照） |
    | 給誰看 | 演算法（決定下一個 trial） | 人（比較、翻舊帳、交接） |
    | 跨次搜尋 | 一個 study 一次搜尋 | 同一個 experiment 裡，**這個月的搜尋跟上個月的並排** |
    | 能不能存模型 | 不能 | 能（第 2 課的 `log_model`，直接接到 Registry） |

    實務上的分工很清楚：**Optuna 負責找，MLflow 負責記。**
    最佳那組參數在 MLflow 裡有一個 run id，你可以順手 `log_model` 把冠軍模型也存進去，
    第 2 課的 Registry、第 6 課的上線流程就全部接得上了。

    順帶一提，官方有一個 `optuna-integration` 套件，裡面的 `MLflowCallback` 可以
    一行掛上去自動記：

    ```python
    from optuna_integration.mlflow import MLflowCallback
    study.optimize(objective, n_trials=25, callbacks=[MLflowCallback(metric_name="cv_auc")])
    ```

    我們這一課故意手寫，因為手寫你會看見「**一個 trial ＝ 一個 nested run**」這件事，
    而且要記什麼、run 叫什麼名字、要不要順便存模型，全部由你決定。
    知道有這個 callback 就好，等你的記錄需求穩定下來再換過去。
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 8️⃣ 續跑與分散式：把 study 存進資料庫

    到目前為止的 study 都活在記憶體裡——**notebook 一關就沒了**。
    調參動輒跑幾小時，這顯然不行。加兩個參數就解決：

    ```python
    study = optuna.create_study(
        study_name="rf-hpo",
        storage="sqlite:///optuna.db",   # ← 每個 trial 一存檔
        direction="maximize",
        load_if_exists=True,             # ← 已經有同名的就接著跑，沒有就新建
    )
    ```

    下面示範「先跑 5 個 → 關掉 → 重新開一個 study 物件接著跑 5 個」。
    注意第二次是**全新的 `create_study` 呼叫**，卻看得到前 5 個 trial。
    """
    )
    return


@app.cell
def _(WORK, mo, objective_plain, optuna, time):
    OPTUNA_DB = f"sqlite:///{WORK}/optuna.db"

    _t0 = time.perf_counter()
    resume_a = optuna.create_study(
        study_name="rf-resume",
        storage=OPTUNA_DB,
        direction="maximize",
        sampler=optuna.samplers.TPESampler(seed=0),
        load_if_exists=True,
    )
    resume_a.optimize(objective_plain, n_trials=5)
    _first_n, _first_best = len(resume_a.trials), resume_a.best_value

    # ── 假裝這裡關掉了 notebook、換一台機器、隔天才回來 ──
    resume_b = optuna.create_study(
        study_name="rf-resume",
        storage=OPTUNA_DB,
        direction="maximize",
        sampler=optuna.samplers.TPESampler(seed=0),
        load_if_exists=True,
    )
    _reopened_n, _reopened_best = len(resume_b.trials), resume_b.best_value
    resume_b.optimize(objective_plain, n_trials=5)
    _resume_seconds = time.perf_counter() - _t0
    _summaries = optuna.get_all_study_summaries(storage=OPTUNA_DB)

    mo.md(
        f"""
    | 步驟 | study 裡有幾個 trial | 目前最佳 |
    |---|---|---|
    | 第一次 `optimize(n_trials=5)` | {_first_n} | {_first_best:.4f} |
    | **重新 `create_study(...)` 打開（還沒跑）** | **{_reopened_n}** | **{_reopened_best:.4f}** |
    | 再 `optimize(n_trials=5)` | {len(resume_b.trials)} | {resume_b.best_value:.4f} |

    整段 {_resume_seconds:.0f} 秒。資料庫檔案
    `{WORK}/optuna.db` 目前 **{(WORK / "optuna.db").stat().st_size / 1024:.0f} KB**，
    裡面有 {len(_summaries)} 個 study（`optuna.get_all_study_summaries(storage=…)` 列得出來）。
    """
    )
    return OPTUNA_DB, resume_a, resume_b


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    `n_trials=5` 是「**這一次再跑 5 個**」，不是「總共要有 5 個」——這是最多人誤會的一個參數。
    另外三件相關的事：

    - **`load_if_exists=True` 一定要加。** 不加的話，同名 study 撞上去會直接
      `DuplicatedStudyError`；而寫個 `optuna.delete_study()` 去「解決」它，
      等於把昨天跑了三小時的結果刪光。
    - **這就是分散式搜尋。** 多台機器（或多個行程）用**同一個 storage**、同一個 `study_name`
      各自 `study.optimize(...)`，就是分散式：每台都把結果寫回同一個資料庫，
      也都讀得到別台的結果，TPE 的建議因此越來越準。
      正式一點的做法是把 sqlite 換成 PostgreSQL／MySQL——sqlite 的檔案鎖在多寫入者下會卡住。
    - **`optuna-dashboard` 讀的就是這個檔。** `pip install optuna-dashboard` 之後
      `optuna-dashboard sqlite:///optuna.db`，瀏覽器就有互動式的重要度圖、平行座標圖、
      等高線圖可以看。（跟 `mlflow ui` 一樣，本課不開伺服器。）
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 9️⃣ 實驗場：自己跑一輪

    三個旋鈕，按下去真的會跑：

    - **trial 數**——搜尋的預算。
    - **取樣器**——TPE（會學）或 Random（純亂猜）。記得前 10 個 trial 兩者一樣。
    - **pruner**——要不要砍掉沒希望的 trial。

    用的是第 6️⃣ 節那個**會分段回報**的 objective（不然 pruner 沒有東西可砍），
    所以分數是驗證集 AUC，跟第 3️⃣–5️⃣ 節的 cv_auc 不同尺。
    每一輪都會在 MLflow 開一個新的 parent run，trial 照樣一個一個記進去。

    值得試的三組對照：

    1. 同樣 20 個 trial，**TPE vs Random**——看「最差的 trial」差多少（不是看最佳值）。
    2. 同樣設定，**pruner 開 vs 關**——看耗時與被砍數。
    3. trial 數從 5 拉到 40——看「目前最佳」那條線什麼時候變平。

    ⚠️ 40 個 trial 大約要跑 25–30 秒，按下去之後耐心等一下。
    """
    )
    return


@app.cell
def _(mo):
    play_trials = mo.ui.slider(
        5, 40, step=5, value=20, label="n_trials", show_value=True
    )
    play_sampler = mo.ui.dropdown(
        options=["TPE", "Random"], value="TPE", label="取樣器"
    )
    play_pruner = mo.ui.dropdown(
        options=["MedianPruner", "不用 pruner"], value="MedianPruner", label="pruner"
    )
    play_go = mo.ui.run_button(label="跑一輪")
    mo.hstack(
        [play_trials, play_sampler, play_pruner, play_go], wrap=True, justify="start"
    )
    return play_go, play_pruner, play_sampler, play_trials


@app.cell
def _(
    mlflow,
    mo,
    optuna,
    play_go,
    play_pruner,
    play_sampler,
    play_trials,
    staged_objective,
    time,
):
    if not play_go.value:
        play_study = None
        play_out = mo.md("*選好三個旋鈕，按「跑一輪」——這裡會出現結果。*")
    else:
        _sampler = (
            optuna.samplers.TPESampler(seed=0)
            if play_sampler.value == "TPE"
            else optuna.samplers.RandomSampler(seed=0)
        )
        _pruner = (
            optuna.pruners.MedianPruner(n_startup_trials=5, n_warmup_steps=0)
            if play_pruner.value == "MedianPruner"
            else optuna.pruners.NopPruner()
        )
        _t0 = time.perf_counter()
        play_study = optuna.create_study(
            direction="maximize", sampler=_sampler, pruner=_pruner
        )
        with mlflow.start_run(run_name=f"play-{play_sampler.value}-{play_trials.value}"):

            def _wrapped(trial):
                with mlflow.start_run(run_name=f"trial-{trial.number}", nested=True):
                    _s = staged_objective(trial)
                    mlflow.log_params(trial.params)
                    mlflow.log_metric("val_auc", _s)
                    return _s

            play_study.optimize(_wrapped, n_trials=play_trials.value)
            mlflow.log_metric("best_val_auc", play_study.best_value)
        _secs = time.perf_counter() - _t0
        _pruned = sum(
            _t.state == optuna.trial.TrialState.PRUNED for _t in play_study.trials
        )
        _done = [
            _t.value
            for _t in play_study.trials
            if _t.state == optuna.trial.TrialState.COMPLETE
        ]
        play_out = mo.md(
            f"""
    **{play_sampler.value} ＋ {play_pruner.value}，{play_trials.value} 個 trial，{_secs:.1f} 秒**

    | | |
    |---|---|
    | 最佳驗證 AUC | **{play_study.best_value:.4f}**（第 {play_study.best_trial.number} 號 trial） |
    | 跑完的 trial | {len(_done)} 個，最差的一個 {min(_done):.4f} |
    | 被 pruner 砍掉 | {_pruned} 個 |
    | 平均每個 trial | {_secs / play_trials.value:.2f} 秒 |
    """
        )
    play_out
    return play_out, play_study


@app.cell
def _(C_BEST, C_PRUNE, C_TPE, mo, np, optuna, play_study, plt):
    mo.stop(
        play_study is None,
        mo.md("*跑一輪之後，這裡會畫出每個 trial 的落點與「目前最佳」。*"),
    )

    _done = [
        _t for _t in play_study.trials if _t.state == optuna.trial.TrialState.COMPLETE
    ]
    _cut = [
        _t for _t in play_study.trials if _t.state == optuna.trial.TrialState.PRUNED
    ]
    _fig, _ax = plt.subplots(figsize=(6.3, 3.4))
    _ax.scatter(
        [_t.number for _t in _done],
        [_t.value for _t in _done],
        s=55,
        c=C_TPE,
        zorder=3,
        label="completed",
    )
    if _cut:
        _ax.scatter(
            [_t.number for _t in _cut],
            [max(_t.intermediate_values.values()) for _t in _cut],
            s=60,
            marker="x",
            c=C_PRUNE,
            zorder=3,
            label="pruned (best step so far)",
        )
    _ax.step(
        [_t.number for _t in _done],
        np.maximum.accumulate([_t.value for _t in _done]),
        where="post",
        color=C_BEST,
        lw=2.2,
        zorder=2,
        label="best so far",
    )
    _ax.set_xlabel("trial number")
    _ax.set_ylabel("validation AUC")
    _ax.set_title("Your run")
    _ax.legend(loc="lower right", fontsize=9)
    _ax.spines[["top", "right"]].set_visible(False)
    _fig.tight_layout()
    _fig
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 🏆 延伸挑戰

    1. **LEVEL 1**：把 `criterion`（`"gini"` / `"entropy"`）加進第 3️⃣ 節的搜尋空間，
       重跑 25 個 trial，再算一次重要度——它會排到第幾名？兩種 criterion 的平均分數差多少？
    2. **LEVEL 2**：改成**多目標**搜尋：AUC 越高越好、樹越少越好
       （`directions=["maximize", "minimize"]`）。這時候 `study.best_trial` 會炸掉，
       要改用 `study.best_trials`——它回傳的是一整條 **Pareto 前緣**。
       找出「AUC 只掉一點點、樹卻少很多」的那一組。
    3. **LEVEL 3**：把這一課的搜尋包成第 5 課那條 Dagster 管線裡的**一個資產**：
       `best_params` 成為下游訓練資產的輸入，品質閘照舊。
       （這一題不用真的裝 dagster，先把資產的邊界與 metadata 設計出來。）

    先自己試，卡住再展開下面的參考解答。
    帶得走：下載本檔後 `uvx marimo edit --sandbox optuna-hpo_ext.py`，在自己電腦繼續玩。
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
    def objective_l1(trial):
        return cv_auc(
            n_estimators=trial.suggest_int("n_estimators", 20, 200, step=20),
            max_depth=trial.suggest_int("max_depth", 2, 16),
            min_samples_leaf=trial.suggest_int("min_samples_leaf", 1, 10),
            max_features=trial.suggest_categorical("max_features", ["sqrt", "log2", None]),
            criterion=trial.suggest_categorical("criterion", ["gini", "entropy"]),
        )

    s1 = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(seed=0))
    s1.optimize(objective_l1, n_trials=25)
    print(s1.best_value, s1.best_params)
    print(optuna.importance.get_param_importances(
        s1, evaluator=optuna.importance.FanovaImportanceEvaluator(seed=0)))

    for c in ("gini", "entropy"):
        vals = [t.value for t in s1.trials if t.params["criterion"] == c]
        print(c, len(vals), round(sum(vals) / len(vals), 4), round(max(vals), 4))
    ```

    實測（Optuna 4.9，同一份資料、25 個 trial）：

    ```text
    best 0.9723  {'n_estimators': 80, 'max_depth': 11, 'min_samples_leaf': 1,
                  'max_features': 'sqrt', 'criterion': 'entropy'}
    importance   max_depth 0.683 / min_samples_leaf 0.266 / max_features 0.026
                 / n_estimators 0.024 / criterion 0.001
    gini      9 次   平均 0.9625   最佳 0.9715
    entropy  16 次   平均 0.9684   最佳 0.9723
    ```

    `criterion` 的重要度是 **0.001**，穩穩墊底——多開這個維度，等於把一部分 trial
    拿去回答一個沒人在乎的問題。重要度低的參數就該固定成常數（第 5️⃣ 節那張表的第二列）。

    但這裡有一個**很容易讀錯的陷阱**：entropy 的平均分數比 gini 高 0.006，
    看起來像「entropy 比較好」——不是。**TPE 給了 entropy 16 次、gini 只有 9 次**，
    因為它早期覺得 entropy 有戲就一直往那邊丟。兩組的樣本量與參數分佈都不一樣，
    這不是公平的 A/B 比較。想真的比 gini 對 entropy，要固定其他參數各跑一次，
    或者用 `RandomSampler`（它才會兩邊均分）。**取樣器有偏，統計就不能亂讀。**

    另外注意：加了一個參數之後，`max_depth` 的重要度從 0.88 掉到 0.68、
    `min_samples_leaf` 從 0.07 升到 0.27——同一個模型、同一份資料，只因為這批 trial
    落點不同。這正是第 5️⃣ 節說的「重要度是估計，不是物理常數」。
    """
            ),
            "💡 LEVEL 2 參考解答": mo.md(
                r"""
    ```python
    def objective_l2(trial):
        n = trial.suggest_int("n_estimators", 20, 200, step=20)
        auc = cv_auc(
            n_estimators=n,
            max_depth=trial.suggest_int("max_depth", 2, 16),
            min_samples_leaf=trial.suggest_int("min_samples_leaf", 1, 10),
            max_features="sqrt",
        )
        return auc, n                      # ← 回傳「兩個」數字

    s2 = optuna.create_study(
        directions=["maximize", "minimize"],           # AUC 越大越好、樹越少越好
        sampler=optuna.samplers.TPESampler(seed=0),
    )
    s2.optimize(objective_l2, n_trials=25)

    s2.best_trial          # ← 這一行會炸
    for t in sorted(s2.best_trials, key=lambda t: t.values[1]):
        print(f"trial {t.number}: auc {t.values[0]:.4f}  trees {int(t.values[1])}  {t.params}")
    ```

    `best_trial` 在多目標 study 上的真實錯誤訊息是：

    ```text
    RuntimeError: A single best trial cannot be retrieved from a multi-objective study.
    Consider using Study.best_trials to retrieve a list containing the best trials.
    ```

    ——完全合理：兩個互相衝突的目標，本來就沒有「唯一的最佳」。
    `best_trials` 給你的是 **Pareto 前緣**：這條線上的每一個 trial，
    都**沒有辦法在不犧牲另一個目標的前提下再改善**。

    實測 25 個 trial 得到 4 個 Pareto 點（你的數字會不同）：

    ```text
    trial 15: auc 0.9636  trees  20   {'max_depth': 11, 'min_samples_leaf': 2}
    trial 21: auc 0.9680  trees  40   {'max_depth': 10, 'min_samples_leaf': 2}
    trial 16: auc 0.9690  trees  60   {'max_depth': 11, 'min_samples_leaf': 4}
    trial  4: auc 0.9711  trees 120   {'max_depth': 15, 'min_samples_leaf': 1}
    ```

    從 20 棵樹到 120 棵樹，樹多了 **6 倍**，AUC 只多 **0.0075**。
    **要選哪一個是產品問題，不是演算法問題**——第 6 課量過，推論成本幾乎跟樹的數量成正比；
    如果那條線上有延遲預算，那個「只差 0.0075、卻少了六倍的樹」的點往往才是正解。
    多目標搜尋的價值就在這裡：它不幫你決定，它把**可以決定的選項**整理好給你。
    """
            ),
            "💡 LEVEL 3 提示": mo.md(
                r"""
    第 5 課的管線是 `churn_data → train_test → trained_model → model_metrics →
    quality_gate → registered_champion`。搜尋要插在 `train_test` 之後、`trained_model` 之前：

    ```python
    @dg.asset
    def best_params(train_test) -> dict:
        study = optuna.create_study(
            study_name="rf-hpo",
            storage="sqlite:///optuna.db",     # ← 資產要能重跑，狀態就不能只在記憶體裡
            direction="maximize",
            load_if_exists=True,
        )
        study.optimize(objective, n_trials=25)
        return study.best_params               # 下游 trained_model(best_params) 直接吃
    ```

    設計時要想清楚的四件事：

    1. **邊界**：搜尋是**一個**資產（產出一組參數），不是一個 trial 一個資產。
       Dagster 管的是「資料產物」，25 個 trial 是這個資產內部的事。
    2. **metadata**：`context.add_output_metadata({"best_cv_auc": dg.MetadataValue.float(...),
       "n_trials": ..., "mlflow_parent_run": ...})`——不然在 UI 上看不出這次搜尋跑得好不好。
       注意別用 `"path"` 當 key（會被 IO manager 蓋掉）。
    3. **重跑要便宜**：`storage=` ＋ `load_if_exists=True` 讓資產重跑時接續而不是從頭；
       想要「每次都重新搜」就換 `study_name`（例如帶上 partition key）。
    4. **加一個 asset check**：`best_cv_auc` 低於門檻就 blocking 擋下——
       搜出來的東西太爛，就不該讓下游浪費時間去訓練、註冊。

    **怎麼驗證你設計對了**：把管線畫成圖，問自己三個問題——
    (a) 只重跑 `trained_model` 時，會不會意外重跑整輪搜尋？
    (b) 搜尋掛掉時，`quality_gate` 有沒有可能拿到上一次的舊參數卻以為是新的？
    (c) MLflow 裡看得出「這個 champion 是哪一次搜尋、第幾號 trial 生出來的」嗎？
    三題都答得出來，這個資產就設計好了。
    """
            ),
        }
    )
    return


if __name__ == "__main__":
    app.run()
