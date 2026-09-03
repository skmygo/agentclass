# 模型上線：從 pyfunc 到 REST API（線上推論 vs 批次評分）
# 不需要 GPU——molab 免費 CPU 環境即可全程執行（伺服器起在 notebook 自己的機器上，不連任何外部服務）。
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "marimo",
#     "mlflow>=3.0",
#     "scikit-learn",
#     "pandas",
#     "numpy",
#     "matplotlib",
#     "fastapi",
#     "uvicorn",
#     "httpx",
# ]
# ///
import marimo

__generated_with = "0.23.16"
app = marimo.App(width="medium", app_title="模型上線：從 pyfunc 到 REST API")


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    # ⚡ 模型上線：從 pyfunc 到 REST API

    上一課結束時，Registry 裡有一個 `models:/churn-clf@champion`。
    **然後呢？** 模型待在 Registry 裡不會替公司賺到任何一塊錢——它要被「用」，才叫上線。

    「上線」不是一件事，是**三種形態**，成本與延遲差好幾個數量級：

    - **批次評分**：每天半夜把整張客戶表跑一次，結果寫回資料庫。最便宜。
    - **線上 API**：每一筆請求即時算一次，毫秒內回答。最貴，但可以即時。
    - **嵌入式**：模型跟著應用程式走，在同一個行程裡呼叫，連網路都不用。

    這份 notebook 把三種都做出來、都量時間，讓你用**自己跑出來的數字**決定該選哪一種：

    1. 上線的三種形態：延遲、成本、更新難度的取捨
    2. 打包給上線用：`signature`、`input_example`、`pyfunc_predict_fn`
    3. 批次評分：一次 500 列，量它的每列成本
    4. 線上 API 方法一——自己包 FastAPI：**模型載一次 vs 每次請求都載**（差 10 倍）
    5. 線上 API 方法二——`mlflow models serve`：`/ping`、`/version`、`/invocations` 與四種 payload 寫法
    6. 換版不停機：alias 移了，跑著的 API 什麼時候才知道？
    7. 上線前檢查清單：用 `serving_input_example.json` 做冒煙、監控該記什麼
    8. 互動：拉批次列數與請求筆數，看每列成本怎麼變；切 alias，看 API 重載前後

    **不需要 GPU**，molab 免費 CPU 環境從第一格往下全部執行即可（首次安裝套件約 1–2 分鐘）。
    伺服器都起在這台機器的 `127.0.0.1` 上，不對外，也不連任何外部服務。

    > 這份 notebook 印出的每個毫秒數字都是**當下這台機器**跑出來的，
    > 跟本文引用的範圍不會完全一樣——看**倍數關係**，不要看絕對值。
    """
    )
    return


@app.cell
def _():
    import json
    import logging
    import os
    import shutil
    import socket
    import subprocess
    import sys
    import tempfile
    import threading
    import time
    import warnings
    from pathlib import Path

    import httpx
    import marimo as mo
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import mlflow
    import pandas as pd
    import uvicorn
    from fastapi import FastAPI
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
        FastAPI,
        LogisticRegression,
        MlflowClient,
        Path,
        RandomForestClassifier,
        httpx,
        infer_signature,
        json,
        make_classification,
        mlflow,
        mo,
        os,
        pd,
        plt,
        roc_auc_score,
        shutil,
        socket,
        subprocess,
        sys,
        tempfile,
        threading,
        time,
        train_test_split,
        uvicorn,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 0️⃣ 準備：同一份資料，Registry 裡已經有一個 champion

    沿用前幾課的模擬「客戶流失」資料（2000 筆、12 個特徵 `f0`–`f11`，train 1500／test 500）。
    紀錄簿一樣是一個 SQLite 檔——**Model Registry 需要資料庫後端**，純資料夾模式沒有註冊與 alias。

    等一下每一節都會用到兩個小工具，先在這裡定義：

    - `free_port()`：跟作業系統要一個「現在沒人用」的 port。**不要在教學程式裡寫死 port**——
      同一台機器上可能同時有別的東西在跑，寫死的下場是 `OSError(98, 'Address already in use')`。
    - `bench()`：對同一個網址打 N 次，回傳最快／中位／最慢的毫秒數。
      單次計時在有 GC、有排程的機器上毫無意義，**延遲永遠看分佈**。
    """
    )
    return


@app.cell
def _(Path, make_classification, mlflow, mo, pd, shutil, tempfile, train_test_split):
    WORK = Path(tempfile.gettempdir()) / "model-serving-lesson"
    shutil.rmtree(WORK, ignore_errors=True)
    WORK.mkdir(parents=True)
    mlflow.set_tracking_uri(f"sqlite:///{WORK / 'mlflow.db'}")
    mlflow.create_experiment("churn-serving", artifact_location=str(WORK / "artifacts"))
    mlflow.set_experiment("churn-serving")

    _X, _y = make_classification(n_samples=2000, n_features=12, n_informative=6, random_state=0)
    FEATURES = [f"f{i}" for i in range(12)]
    X_train, X_test, y_train, y_test = train_test_split(
        pd.DataFrame(_X, columns=FEATURES), _y, test_size=0.25, random_state=0
    )
    mo.md(
        f"工作目錄 `{WORK}`；tracking `{mlflow.get_tracking_uri()}`；"
        f"train **{len(X_train)}** 筆／test **{len(X_test)}** 筆，欄位 `{FEATURES[0]}`…`{FEATURES[-1]}`"
    )
    return FEATURES, WORK, X_test, X_train, y_test, y_train


@app.cell
def _(httpx, socket, time):
    def free_port():
        """跟作業系統要一個沒人在用的 port：bind 到 0 讓它挑一個，記下來再關掉。"""
        _s = socket.socket()
        _s.bind(("127.0.0.1", 0))
        _p = _s.getsockname()[1]
        _s.close()
        return _p

    def bench(url, payload, n=20, warmup=3):
        """對同一個網址打 n 次，回傳 (最快, 中位, 最慢) 毫秒。前 warmup 次不計（暖機）。"""
        for _ in range(warmup):
            httpx.post(url, json=payload, timeout=120)
        _ts = []
        for _ in range(n):
            _t0 = time.perf_counter()
            httpx.post(url, json=payload, timeout=120)
            _ts.append((time.perf_counter() - _t0) * 1000)
        _ts.sort()
        return _ts[0], _ts[len(_ts) // 2], _ts[-1]

    def wait_up(url, timeout_s=90):
        """輪詢一個網址直到它回應（或放棄），回傳等了幾秒；起伺服器之後一定要等。"""
        _t0 = time.perf_counter()
        while time.perf_counter() - _t0 < timeout_s:
            try:
                httpx.get(url, timeout=1)
                return time.perf_counter() - _t0
            except Exception:  # noqa: BLE001 — 還沒起來就是連不上，繼續等
                time.sleep(0.2)
        return None

    return bench, free_port, wait_up


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 1️⃣ 上線是什麼：三種形態，先選對再談怎麼做

    很多人一聽到「模型上線」就直接開始寫 REST API——那是最貴的一種，而且常常沒必要。
    先問一個問題：**答案什麼時候需要？**

    | | 批次評分 | 線上 API | 嵌入式 |
    |---|---|---|---|
    | 答案什麼時候要 | 明天早上就好 | 這一秒 | 這一秒，而且不能連網 |
    | 怎麼跑 | 排程（每天／每小時）跑一支腳本，結果寫回資料庫 | 一台一直開著的伺服器，收 HTTP 請求 | 模型檔跟著 App 一起發佈，在同一個行程裡呼叫 |
    | 一列的成本 | **最低**（一次算幾十萬列，攤下來趨近於零） | 高（每筆都要付一次網路＋序列化＋推論） | 最低（沒有網路） |
    | 要維運什麼 | 一個排程 | 伺服器、擴縮、健康檢查、監控、版本切換 | App 的發版流程 |
    | 換模型多快 | 下一次排程就生效 | 一行 alias ＋ 重載（本課第 6 節） | 要等使用者更新 App |
    | 典型場景 | 每日流失名單、隔夜信用評分、推薦候選預算 | 交易反詐、即時定價、對話系統 | 手機相機特效、離線裝置、資料庫 UDF |

    這三種**不是互斥的**。真實系統常常是：批次算好大部分、線上 API 只處理「批次沒算過的新客戶」。

    **選擇的判準只有一條**：如果「昨天算好的答案」就夠用，就別為了即時性去付一台伺服器 24 小時的錢
    ——那台伺服器要監控、要擴縮、要值班，而排程壞掉只是明天的報表晚一點。

    這一課三種都做：3️⃣ 批次、4️⃣ 與 5️⃣ 線上 API 的兩種做法。
    嵌入式其實你已經會了——第 3 節那個 `load_model` 之後直接 `predict` 的寫法，
    放進手機 App 或 Spark UDF 裡就是嵌入式，**差別只在它沒有網路那一層**。
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 2️⃣ 打包給上線用：signature、input_example、pyfunc_predict_fn

    上一課學過 `log_model` 會產生一個資料夾。這一節要看的是：**其中哪些東西是為了「上線」而存在的。**

    ### `signature`：模型與呼叫端之間的合約

    上一課它幫你擋掉「少一欄」的輸入。這一課你會看到它更狠的用途——
    `mlflow models serve` 會**把 signature 直接變成 REST API 的輸入驗證**：
    少一欄、型別錯的請求根本進不到模型，伺服器回 HTTP 400 並告訴呼叫端哪裡錯。
    你一行驗證程式都不用寫。

    ### `input_example`：上線的第一份冒煙測資

    給了 `input_example`，MLflow 會在模型資料夾裡多存一個 **`serving_input_example.json`**——
    那是一份**可以直接 POST 給伺服器的 payload**。部署完第一件事就是拿它打一次，
    有回應代表「模型 × 環境 × API 格式」三件事同時是對的。第 7 節會真的這樣做。

    ### `pyfunc_predict_fn="predict_proba"`：讓 pyfunc 回機率

    pyfunc 是部署工具唯一認得的介面，但它只有一個 `predict`。
    sklearn 分類器的 `predict` 回**類別**（0/1），可是流失預測要的是**機率**（好排序、好調門檻）。
    `log_model(..., pyfunc_predict_fn="predict_proba")` 就是在說：
    「這個模型被當成 pyfunc 呼叫時，請去呼叫 `predict_proba`。」
    之後不管是 `pyfunc.predict()`、`/invocations`，回來的都是每一列兩個數字 `[P(不流失), P(流失)]`。

    下面訓兩個模型註冊成兩版，`champion` 指向比較強的 RandomForest——這就是上一課的結尾狀態。
    """
    )
    return


@app.cell
def _(
    LogisticRegression,
    MlflowClient,
    RandomForestClassifier,
    X_test,
    X_train,
    infer_signature,
    mlflow,
    roc_auc_score,
    y_test,
    y_train,
):
    MODEL_NAME = "churn-clf"
    client = MlflowClient()

    def log_and_register(estimator, run_name):
        """訓練 → log_model（帶 signature／input_example／predict_proba）→ 註冊成新版本。"""
        estimator.fit(X_train, y_train)
        _sig = infer_signature(X_train, estimator.predict_proba(X_train))   # 輸出是 (n, 2) 的機率矩陣
        with mlflow.start_run(run_name=run_name):
            _info = mlflow.sklearn.log_model(
                estimator,
                name="churn_model",
                signature=_sig,
                input_example=X_train.head(2),          # → 資料夾裡的 serving_input_example.json
                pyfunc_predict_fn="predict_proba",      # → pyfunc 的 predict 改叫 predict_proba
            )
            _auc = roc_auc_score(y_test, estimator.predict_proba(X_test)[:, 1])
            mlflow.log_metric("eval_auc", _auc)
        _mv = mlflow.register_model(_info.model_uri, MODEL_NAME)
        return _info, int(_mv.version), _auc

    v1_info, v1_ver, v1_auc = log_and_register(LogisticRegression(max_iter=1000), "v1-logreg")
    v2_info, v2_ver, v2_auc = log_and_register(
        RandomForestClassifier(n_estimators=100, max_depth=8, random_state=0), "v2-rf-depth8"
    )
    client.set_registered_model_alias(MODEL_NAME, "champion", v2_ver)   # 線上那一版
    return (
        MODEL_NAME,
        client,
        log_and_register,
        v1_auc,
        v1_info,
        v1_ver,
        v2_auc,
        v2_info,
        v2_ver,
    )


@app.cell
def _(MODEL_NAME, WORK, json, mlflow, mo, os, v1_auc, v2_auc, v2_info, v2_ver):
    MODEL_DIR = mlflow.artifacts.download_artifacts(v2_info.model_uri, dst_path=str(WORK / "champion-files"))
    SERVING_EXAMPLE = json.loads((WORK / "champion-files" / "serving_input_example.json").read_text())
    _cols = SERVING_EXAMPLE["dataframe_split"]["columns"]
    _row0 = [round(v, 4) for v in SERVING_EXAMPLE["dataframe_split"]["data"][0][:4]]

    mo.md(
        f"""
    註冊完成：v{1} LogisticRegression（eval_auc **{v1_auc:.4f}**）、
    v{v2_ver} RandomForest depth 8（eval_auc **{v2_auc:.4f}**），`@champion` → **v{v2_ver}**。

    champion 那一版的模型資料夾裡有 {len(os.listdir(MODEL_DIR))} 個檔案：

    ```text
    {"  ".join(sorted(os.listdir(MODEL_DIR)))}
    ```

    其中 `serving_input_example.json` 就是**現成的 REST payload**——信封是 `dataframe_split`，
    裡面 `columns` 有 {len(_cols)} 欄、`data` 是 {len(SERVING_EXAMPLE["dataframe_split"]["data"])} 列
    （第一列前 4 個值：`{_row0}`…）。第 5 節你會看到 `/invocations` 吃的就是這個形狀，
    第 7 節會拿它當上線冒煙測資。

    `signature` 的輸出段是 `Tensor('float64', (-1, 2))`——這就是 `pyfunc_predict_fn="predict_proba"`
    的效果：每一列回**兩個**數字。註冊的名字是 `{MODEL_NAME}`。
    """
    )
    return MODEL_DIR, SERVING_EXAMPLE


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 3️⃣ 批次評分：最便宜的上線方式

    批次評分長什麼樣子？就這三行：

    ```python
    model = mlflow.pyfunc.load_model("models:/churn-clf@champion")
    scores = model.predict(all_customers)          # 一次算完整張表
    all_customers.assign(prob=scores[:, 1]).to_csv("today.csv")
    ```

    **沒有伺服器、沒有 API、沒有健康檢查**——一支腳本，掛到排程上就上線了。
    模型換版？下一次排程自動載到新的 `@champion`。這是維運成本最低的一種上線。

    下面對整張 test 表（500 列）跑一次並計時，同時跟「一次只算一列」對照。
    注意看**每列成本**：同樣的模型、同樣的機器，差別只在「一次餵幾列」。
    """
    )
    return


@app.cell
def _(MODEL_NAME, X_test, WORK, mlflow, mo, pd, time, y_test):
    batch_model = mlflow.pyfunc.load_model(f"models:/{MODEL_NAME}@champion")

    _t0 = time.perf_counter()
    _reloaded = mlflow.pyfunc.load_model(f"models:/{MODEL_NAME}@champion")
    LOAD_MS = (time.perf_counter() - _t0) * 1000

    batch_model.predict(X_test.head(8))          # 暖機（第一次呼叫含一些延遲初始化）

    _t0 = time.perf_counter()
    batch_proba = batch_model.predict(X_test)    # ← 一次 500 列
    BATCH_MS = (time.perf_counter() - _t0) * 1000

    _t0 = time.perf_counter()
    for _i in range(50):                         # ← 一次 1 列，做 50 次
        batch_model.predict(X_test.iloc[[_i]])
    ONEBYONE_MS = (time.perf_counter() - _t0) * 1000 / 50

    scores_df = X_test.assign(prob=batch_proba[:, 1].round(4), actual=y_test)
    _csv = WORK / "scores_today.csv"
    scores_df[["prob", "actual"]].to_csv(_csv)

    mo.vstack(
        [
            mo.md(
                f"""
    - `load_model` 花了 **{LOAD_MS:.0f} ms**（每次載入都要付一次——記住這個數字，第 4 節會用到）
    - 一次 **500 列**：{BATCH_MS:.1f} ms 總計 → 每列 **{BATCH_MS / len(X_test):.3f} ms**
    - 一次 **1 列**（跑 50 次取平均）：每列 **{ONEBYONE_MS:.2f} ms**
    - 每列成本相差約 **{ONEBYONE_MS / (BATCH_MS / len(X_test)):.0f} 倍**

    為什麼？模型推論的固定開銷（DataFrame 建構、schema 檢查、走訪 100 棵樹的 Python 呼叫）
    幾乎跟列數無關，一次算越多列就攤得越薄。**這就是批次便宜的全部原因。**

    結果寫進 `{_csv.name}`（{len(scores_df)} 列），前幾列：
                """
            ),
            mo.ui.table(
                scores_df[["prob", "actual"]].head(5).reset_index().rename(columns={"index": "customer"}).to_dict("records"),
                selection=None,
            ),
        ]
    )
    return BATCH_MS, LOAD_MS, ONEBYONE_MS, batch_model, batch_proba, scores_df


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 4️⃣ 線上 API 方法一：自己包一個 FastAPI

    批次不夠用的時候——例如「客戶正在跟客服講電話，現在就要知道他的流失風險」——才需要線上 API。

    自己包的好處是**你完全控制介面**：欄位名稱、回傳格式、驗證、認證、記錄，全都照你的規矩來。
    程式很短：

    ```python
    model = mlflow.pyfunc.load_model("models:/churn-clf@champion")   # ← 啟動時載入，一次

    @api.post("/predict")
    def predict(rows: list[dict]):
        proba = model.predict(pd.DataFrame(rows))
        return {"prob": [float(p[1]) for p in proba]}
    ```

    **這裡有一個新手最常犯、而且上線之後才會痛的錯**：把 `load_model` 寫進 `predict` 裡面。
    看起來很合理（「這樣就永遠是最新的模型」），但每一個請求都要重新讀檔、反序列化、重建模型物件
    ——你剛剛量到的那 `load_model` 幾百毫秒，會加在**每一筆請求**上。

    下面同時開兩個端點來證明這件事：`/predict` 模型載一次、`/predict_slow` 每次請求都載，
    其他程式碼一模一樣。順便加上 `/health`（回目前模型版本）與 `/reload`（第 6 節用）。

    伺服器用 uvicorn 跑在**背景執行緒**（`daemon=True`，notebook 關掉它就跟著結束），
    port 用 `free_port()` 現要一個。
    """
    )
    return


@app.cell
def _(
    FastAPI,
    MODEL_NAME,
    batch_model,
    client,
    free_port,
    mlflow,
    mo,
    pd,
    threading,
    uvicorn,
    wait_up,
):
    MODEL_URI = f"models:/{MODEL_NAME}@champion"
    SERVED = {"model": batch_model, "version": int(client.get_model_version_by_alias(MODEL_NAME, "champion").version)}
    api = FastAPI(title="churn-api")

    @api.post("/predict")
    def api_predict(rows: list[dict]):
        """正確做法：用啟動時載好的那一份模型。"""
        _proba = SERVED["model"].predict(pd.DataFrame(rows))
        return {"prob": [round(float(_p[1]), 4) for _p in _proba], "model_version": SERVED["version"]}

    @api.post("/predict_slow")
    def api_predict_slow(rows: list[dict]):
        """反例：每一個請求都重新 load_model。功能一樣，代價差一個數量級。"""
        _m = mlflow.pyfunc.load_model(MODEL_URI)
        _proba = _m.predict(pd.DataFrame(rows))
        return {"prob": [round(float(_p[1]), 4) for _p in _proba]}

    @api.get("/health")
    def api_health():
        """健康檢查：不只回「我活著」，還要回「我身上是哪一版模型」。"""
        return {"status": "ok", "model_uri": MODEL_URI, "model_version": SERVED["version"]}

    @api.post("/reload")
    def api_reload():
        """去 Registry 看 alias 現在指向哪一版；變了才重載（第 6 節）。"""
        _now = int(client.get_model_version_by_alias(MODEL_NAME, "champion").version)
        if _now == SERVED["version"]:
            return {"reloaded": False, "model_version": _now}
        SERVED["model"] = mlflow.pyfunc.load_model(MODEL_URI)
        SERVED["version"] = _now
        return {"reloaded": True, "model_version": _now}

    API_PORT = free_port()
    API_URL = f"http://127.0.0.1:{API_PORT}"
    _server = uvicorn.Server(uvicorn.Config(api, host="127.0.0.1", port=API_PORT, log_level="error"))
    threading.Thread(target=_server.run, daemon=True).start()
    API_UP = wait_up(f"{API_URL}/health")

    mo.md(
        f"自包 API 在 **`{API_URL}`** 聽候（"
        + (f"{API_UP:.2f} 秒就緒" if API_UP is not None else "⚠️ 沒起來")
        + f"）；載的是 `{MODEL_URI}` → v{SERVED['version']}。"
    )
    return API_PORT, API_UP, API_URL, MODEL_URI, SERVED, api


@app.cell
def _(API_URL, X_test, bench, httpx, mo):
    ONE_ROW = X_test.head(1).to_dict("records")            # FastAPI 端點收的是 [{欄名: 值, ...}]
    THREE_ROWS = X_test.head(3).to_dict("records")

    api_resp = httpx.post(f"{API_URL}/predict", json=THREE_ROWS, timeout=60).json()
    api_health_resp = httpx.get(f"{API_URL}/health", timeout=10).json()

    FAST_MIN, FAST_MED, FAST_MAX = bench(f"{API_URL}/predict", ONE_ROW, n=30)
    SLOW_MIN, SLOW_MED, SLOW_MAX = bench(f"{API_URL}/predict_slow", ONE_ROW, n=8, warmup=1)

    mo.md(
        f"""
    `POST /predict` 三筆客戶 → `{api_resp}`
    `GET /health` → `{api_health_resp}`

    | 端點 | 差別 | 最快 | 中位 | 最慢 |
    |---|---|---|---|---|
    | `/predict` | 模型**載一次** | {FAST_MIN:.1f} ms | **{FAST_MED:.1f} ms** | {FAST_MAX:.1f} ms |
    | `/predict_slow` | **每次請求都** `load_model` | {SLOW_MIN:.1f} ms | **{SLOW_MED:.1f} ms** | {SLOW_MAX:.1f} ms |

    同樣的模型、同樣的答案，延遲差 **{SLOW_MED / FAST_MED:.0f} 倍**。
    這台機器沒有別的負載；正式環境同時有幾十個請求進來時，差距只會更大
    ——因為每個請求都在重複做同一件昂貴的事，還互相搶 CPU 與磁碟。

    **記住這條規則：模型在啟動時載入一次，請求只做推論。**
    「換版怎麼辦？」是第 6 節的題目，不是把 `load_model` 搬進 handler 的理由。
    """
    )
    return (
        FAST_MAX,
        FAST_MED,
        FAST_MIN,
        ONE_ROW,
        SLOW_MAX,
        SLOW_MED,
        SLOW_MIN,
        THREE_ROWS,
        api_health_resp,
        api_resp,
    )


@app.cell
def _(BATCH_MS, FAST_MED, ONEBYONE_MS, SLOW_MED, X_test, plt):
    _labels = ["batch\n(500 rows)", "batch\n(1 row)", "online API\n(load once)", "online API\n(load each req)"]
    _values = [BATCH_MS / len(X_test), ONEBYONE_MS, FAST_MED, SLOW_MED]
    _colors = ["#4C72B0", "#4C72B0", "#DD8452", "#C44E52"]

    _fig, _ax = plt.subplots(figsize=(6.2, 3.6))
    _bars = _ax.bar(_labels, _values, color=_colors)
    _ax.set_yscale("log")
    _ax.set_ylabel("ms per row (log scale)")
    _ax.set_title("Cost of one prediction, four ways (this machine, this run)")
    _ax.grid(axis="y", alpha=0.3)
    for _b, _v in zip(_bars, _values):
        _ax.text(_b.get_x() + _b.get_width() / 2, _v * 1.25, f"{_v:.3g}", ha="center", fontsize=9)
    _ax.set_ylim(min(_values) / 3, max(_values) * 4)
    _fig.tight_layout()
    _fig
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    上圖是對數刻度——**四根長條之間差了好幾個數量級**。
    最左邊是批次評分的每列成本，最右邊是「每個請求都載模型」的線上 API。
    同一個模型，做同一件事，成本差幾千倍，差別全在你怎麼把它接起來。

    ## 5️⃣ 線上 API 方法二：`mlflow models serve`

    自己包很自由，但也代表**每一個模型都要有人寫一支服務程式**。
    MLflow 內建了一個標準伺服器，一行指令就能把任何 Registry 裡的模型變成 REST API：

    ```bash
    mlflow models serve -m models:/churn-clf@champion -p 5001 --env-manager local
    ```

    `--env-manager local` 表示「直接用目前這個 Python 環境」。
    不加的話 MLflow 會照模型資料夾裡的 `requirements.txt` **建一個乾淨的虛擬環境**再跑
    ——那才是正式部署該做的（環境跟著模型走，不會因為你這台機器裝了別的版本而算錯），
    代價是啟動要多花好幾分鐘裝套件。課堂上用 `local` 省時間。

    它給你三個端點，都是業界慣例：

    | 端點 | 做什麼 | 誰在用 |
    |---|---|---|
    | `GET /ping` | 活著就回 200 | 負載平衡器、Kubernetes 的健康檢查 |
    | `GET /version` | 回 MLflow 版本字串 | 排查「伺服器到底跑哪一版」 |
    | `POST /invocations` | 推論 | 你的應用程式 |

    下面用**子行程**把它跑起來（`sys.executable -m mlflow ...`），
    並把 `MLFLOW_TRACKING_URI` 傳進去——**子行程不會繼承 Python 裡 `set_tracking_uri` 的設定**，
    忘了傳它就會去找預設位置，然後告訴你 `Registered model alias champion not found.`
    """
    )
    return


@app.cell
def _(MODEL_URI, free_port, httpx, mlflow, mo, os, subprocess, sys, time):
    SERVE_PORT = free_port()
    SERVE_URL = f"http://127.0.0.1:{SERVE_PORT}"
    serve_proc = subprocess.Popen(   # 指令列固定，參數都是本地產生的
        [
            sys.executable, "-m", "mlflow", "models", "serve",
            "-m", MODEL_URI,
            "-p", str(SERVE_PORT),
            "--host", "127.0.0.1",
            "--env-manager", "local",
        ],
        env={**os.environ, "MLFLOW_TRACKING_URI": mlflow.get_tracking_uri()},   # ← 一定要傳
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    SERVE_UP = None
    _t0 = time.perf_counter()
    while time.perf_counter() - _t0 < 180:
        try:
            if httpx.get(f"{SERVE_URL}/ping", timeout=1).status_code == 200:
                SERVE_UP = time.perf_counter() - _t0
                break
        except Exception:  # noqa: BLE001 — 還在啟動就是連不上
            time.sleep(0.5)

    mo.md(
        f"`mlflow models serve` 在 **`{SERVE_URL}`** "
        + (
            f"就緒（等了 **{SERVE_UP:.1f} 秒**——它要載模型、建 Flask app、起 waitress／gunicorn，"
            "比自包的執行緒慢得多，所以**正式環境不要靠重啟來換模型**）。"
            if SERVE_UP is not None
            else "⚠️ 沒起來（看下面的 log 尾段）。"
        )
    )
    return SERVE_PORT, SERVE_UP, SERVE_URL, serve_proc


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ### `/invocations` 的四種 payload 寫法

    `mlflow models serve` 不吃「裸的 JSON 陣列」——**一定要有信封**，
    告訴它你送的是哪種形狀。四個信封名稱擇一：

    - `dataframe_split`：`{"columns": [...], "data": [[...], ...]}`——最常用，欄名與資料分開，省頻寬
    - `dataframe_records`：`[{"f0": 1.2, ...}, ...]`——每列一個物件，最好讀、最像一般 REST API
    - `inputs`：`{"f0": [...], "f1": [...]}`——欄名對值清單
    - `instances`：純 2D 陣列 `[[...], ...]`——**這個模型不吃**，因為 signature 要欄名（下面會看到錯誤原文）

    下面把六種請求（四種寫法 ＋ 兩種壞掉的）一次打完，看伺服器怎麼回。
    """
    )
    return


@app.cell
def _(FEATURES, SERVE_UP, SERVE_URL, X_test, httpx, mo):
    def probe(label, payload):
        _r = httpx.post(f"{SERVE_URL}/invocations", json=payload, timeout=120)
        return {"寫法": label, "HTTP": _r.status_code, "回應（截斷）": _r.text[:150]}

    if SERVE_UP is None:
        invocation_rows = []
        invocation_bad = "（伺服器沒起來，這一節跳過）"
    else:
        _split = X_test.head(2).to_dict("split")
        _split.pop("index", None)                       # index 留著其實也會過，但慣例是拿掉
        invocation_rows = [
            probe("dataframe_split", {"dataframe_split": _split}),
            probe("dataframe_split（保留 index）", {"dataframe_split": X_test.head(2).to_dict("split")}),
            probe("dataframe_records", {"dataframe_records": X_test.head(2).to_dict("records")}),
            probe("inputs", {"inputs": {_c: X_test.head(2)[_c].tolist() for _c in FEATURES}}),
            probe("instances（無欄名）", {"instances": X_test.head(2).values.tolist()}),
            probe("沒有信封（裸 list）", X_test.head(2).to_dict("records")),
        ]
        _miss = httpx.post(
            f"{SERVE_URL}/invocations",
            json={"dataframe_records": X_test.head(1).drop(columns=["f11"]).to_dict("records")},
            timeout=120,
        )
        _type = httpx.post(
            f"{SERVE_URL}/invocations",
            json={"dataframe_split": {"columns": FEATURES, "data": [["x", *X_test.head(1).values[0, 1:].tolist()]]}},
            timeout=120,
        )
        _envelope = next(r for r in invocation_rows if r["寫法"].startswith("沒有信封"))["回應（截斷）"]
        _miss_txt = f"{_miss.text[:64]}\n  … （中間是整份 schema，略）…\n{_miss.text[-160:]}"
        invocation_bad = (
            f"**少一欄 `f11`** → HTTP {_miss.status_code}\n\n"
            f"```json\n{_miss_txt}\n```\n\n"
            f"**型別錯（`f0` 送字串）** → HTTP {_type.status_code}\n\n"
            f"```json\n{_type.text[:330]}\n```\n\n"
            f"**沒有信封** → HTTP 400\n\n```json\n{_envelope}\n```"
        )

    mo.vstack([mo.ui.table(invocation_rows, selection=None), mo.md(invocation_bad)])
    return invocation_bad, invocation_rows, probe


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    看懂上面那三段錯誤，你就懂了 `mlflow models serve` 的價值：

    - `SCHEMA_ENFORCEMENT_FAILED` ＋ `Model is missing inputs ['f11'].`
      ——**signature 變成了 API 的輸入驗證**。呼叫端少送一欄，在進到模型之前就被擋下，
      而且錯誤訊息直接指名缺哪一欄。你一行驗證程式都沒寫。
    - `Failed to convert column f0 to type 'float64'`——型別把關同理。
    - `The input must be a JSON dictionary with exactly one of the input fields
      {'dataframe_split', 'inputs', 'dataframe_records', 'instances'}. Received a list.`
      ——連「信封放錯」都講得清清楚楚。（那四個名字的順序每次不同，因為它是 Python 的 set。）

    自己包的 FastAPI 要達到同樣的品質，你得自己寫 schema、自己回 400、自己寫錯誤訊息。
    **這就是取捨**：`mlflow models serve` 給你標準與嚴謹，自包給你自由。

    ### 收尾：子行程一定要自己收

    背景執行緒會跟著 notebook 一起結束，但**子行程不會**——不收它，
    它會一直占著那個 port 跑下去（在 molab 上就是一直吃你的 CPU 配額）。
    `terminate()` 送出結束訊號，`communicate(timeout=...)` 等它真的走掉並收回輸出。
    """
    )
    return


@app.cell
def _(SERVE_URL, httpx, invocation_rows, mo, serve_proc):
    _ping = httpx.get(f"{SERVE_URL}/ping", timeout=5) if invocation_rows else None
    _version = httpx.get(f"{SERVE_URL}/version", timeout=5) if invocation_rows else None
    _p = f"HTTP {_ping.status_code}，body `{_ping.text!r}`" if _ping is not None else "（跳過）"
    _v = f"`{_version.text}`" if _version is not None else "（跳過）"

    serve_proc.terminate()
    try:
        SERVE_LOG = serve_proc.communicate(timeout=15)[0] or ""
    except Exception:  # noqa: BLE001 — 收不掉就強制殺，不能讓它留下來
        serve_proc.kill()
        SERVE_LOG = ""

    mo.md(
        f"""
    - `GET /ping` → {_p}（**body 是空的**——健康檢查只看狀態碼，別去解析它）
    - `GET /version` → {_v}（MLflow 自己的版本，不是模型版本；模型版本要自己做，像第 4 節的 `/health`）
    - 伺服器已關閉（`terminate()` → `communicate()`），回傳碼 `{serve_proc.returncode}`。log 尾段：

    ```text
    {" | ".join(SERVE_LOG.strip().splitlines()[-3:]) or "（無輸出）"}
    ```

    要再玩一次的話，從「起 `mlflow models serve`」那一格重新執行即可（會自動要一個新的 port）。
    """
    )
    return (SERVE_LOG,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 6️⃣ 換版不停機：alias 移了，API 什麼時候知道？

    上一課學到「晉升＝把 `champion` 移到新版本，服務程式一行不用改」。
    這句話有一個沒說出口的前提：**服務程式要重新載入模型，才會看到新的 alias。**

    因為第 4 節那條規則——模型在啟動時載入一次——跑著的行程裡是一個**已經載好的物件**，
    它不會因為資料庫裡一列 alias 改了就自己變身。三種做法：

    | 做法 | 怎麼觸發 | 停機 | 適合 |
    |---|---|---|---|
    | 重啟服務 | 部署流程重跑（`mlflow models serve` 只能這樣） | 有（本課實測起一次要好幾秒） | 有多台機器做輪流更新時可接受 |
    | 主動觸發 `POST /reload` | 晉升流程的最後一步去打這個端點 | 無 | 你自己包的 API；換版時機明確 |
    | 定時輪詢 | 背景每 N 秒問 Registry，版本變了才重載 | 無 | 多台機器、不想讓晉升流程知道有誰在跑 |

    下面訓一個更強的 v3 註冊、把 `champion` 移過去，然後**故意先不重載**，看 API 回什麼。
    """
    )
    return


@app.cell
def _(
    API_URL,
    MODEL_NAME,
    ONE_ROW,
    RandomForestClassifier,
    client,
    httpx,
    log_and_register,
    mo,
    v2_ver,
):
    v3_info, v3_ver, v3_auc = log_and_register(
        RandomForestClassifier(n_estimators=200, max_depth=16, random_state=0), "v3-rf-depth16"
    )
    client.set_registered_model_alias(MODEL_NAME, "champion", v3_ver)   # 晉升：champion → v3

    _registry_ver = client.get_model_version_by_alias(MODEL_NAME, "champion").version
    before_health = httpx.get(f"{API_URL}/health", timeout=10).json()
    before_pred = httpx.post(f"{API_URL}/predict", json=ONE_ROW, timeout=30).json()

    mo.md(
        f"""
    v{v3_ver} 已註冊（RandomForest depth 16，eval_auc **{v3_auc:.4f}**，前一版 v{v2_ver}）
    且 Registry 的 `@champion` 已經指向 **v{_registry_ver}**。

    但是跑著的 API 完全沒感覺：

    - `GET /health` → `{before_health}`
    - `POST /predict` → `{before_pred}`

    **同一個 URI、同一行載入程式碼，拿到的還是舊模型**——因為那個模型物件早在啟動時就載好了。
    這不是 bug，是設計：如果每個請求都去問一次 Registry，你就回到 `/predict_slow` 的世界了。

    （順帶一提：`get_model_version_by_alias(...).version` 回的是 **int**，
    不是字串——拿去跟 `"3"` 比對會永遠不相等，這種靜默的比較失敗最難查。）
    """
    )
    return before_health, before_pred, v3_auc, v3_info, v3_ver


@app.cell
def _(API_URL, ONE_ROW, before_pred, httpx, mo):
    reload_resp = httpx.post(f"{API_URL}/reload", timeout=120).json()
    after_health = httpx.get(f"{API_URL}/health", timeout=10).json()
    after_pred = httpx.post(f"{API_URL}/predict", json=ONE_ROW, timeout=30).json()
    reload_again = httpx.post(f"{API_URL}/reload", timeout=120).json()

    mo.vstack(
        [
            mo.md(
                f"""
    打一次 `POST /reload`：

    - 回應 `{reload_resp}`
    - `GET /health` → `{after_health}`
    - 同一位客戶的機率：重載前 **{before_pred["prob"][0]}** → 重載後 **{after_pred["prob"][0]}**
    - 再打一次 `/reload` → `{reload_again}`（版本沒變就不重載——**這很重要**：
      重載期間那個行程會多吃一份記憶體，還會有幾百毫秒的延遲尖峰，不該白做）
                """
            ),
            mo.md(
                r"""
    `/reload` 的完整邏輯只有四行，重點是那個 `if`：

    ```python
    @api.post("/reload")
    def reload():
        now = int(client.get_model_version_by_alias("churn-clf", "champion").version)
        if now == SERVED["version"]:
            return {"reloaded": False, "model_version": now}      # ← 沒變就別動
        SERVED["model"] = mlflow.pyfunc.load_model(MODEL_URI)     # 換上新的
        SERVED["version"] = now
        return {"reloaded": True, "model_version": now}
    ```

    要做成**定時輪詢**版本也是同一段邏輯，只是改由背景執行緒每 N 秒呼叫一次：

    ```python
    def poller(every=30):
        while True:
            time.sleep(every)
            try:
                api_reload()          # 版本沒變就是一次便宜的資料庫查詢
            except Exception as e:
                log.warning("reload check failed: %s", e)   # ← 絕不能讓它弄掉服務
    threading.Thread(target=poller, daemon=True).start()
    ```

    兩個實務細節：**換版要留紀錄**（哪一秒從 v2 換到 v3，之後查指標異常時第一個要對的就是它）；
    **回滾走同一條路**（alias 指回去、再打一次 `/reload`），所以這條路平常就要是通的。

    至於 `mlflow models serve`：它沒有 reload 端點，換版只能重啟行程
    ——這也是「標準伺服器」與「自己包」的另一個取捨點。
                """
            ),
        ]
    )
    return after_health, after_pred, reload_again, reload_resp


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 7️⃣ 上線前檢查清單

    模型能載入 ≠ 模型能上線。上線前這四件事，每一件都是有人半夜被叫起來換來的：

    **1. 用模型自己帶的範例輸入做冒煙**
    `mlflow.models.validate_serving_input(model_uri, payload)` 會模擬「伺服器收到這份 JSON」的完整路徑
    ——反序列化、schema 驗證、呼叫模型——但**不用真的起伺服器**。
    payload 直接用模型資料夾裡的 `serving_input_example.json`，那是 `input_example` 自動生出來的。
    一句話：**部署前先在本機跑一次，別讓 400 在正式環境才出現。**

    **2. 打一次真的服務**，用同一份範例輸入（本機起、CI 裡起都行）。
    「模型能載入」跟「服務能回應」中間還隔著一層 HTTP 與 JSON 序列化。

    **3. 對答案**：同一批輸入，批次算出來的機率跟 API 回來的要一樣。
    不一樣就代表兩邊的前處理不同步——這是線上／離線不一致最常見的來源。

    **4. 版本要看得見**：`/health` 回目前的模型版本（第 4 節做了）。
    沒有這個，出事時你連「當時線上跑的是哪一版」都答不出來。

    下面把 1、2、3 一次跑完。
    """
    )
    return


@app.cell
def _(
    API_URL,
    MODEL_NAME,
    MODEL_URI,
    SERVING_EXAMPLE,
    after_health,
    httpx,
    mlflow,
    mo,
    pd,
):
    _split = SERVING_EXAMPLE["dataframe_split"]
    _example_df = pd.DataFrame(_split["data"], columns=_split["columns"])

    try:                                      # 1) 不起伺服器的離線冒煙
        _validated = mlflow.models.validate_serving_input(MODEL_URI, SERVING_EXAMPLE)
        smoke_offline = f"通過，回傳 shape {getattr(_validated, 'shape', len(_validated))}"
    except Exception as _e:  # noqa: BLE001 — 教學：冒煙失敗要看得到原文
        smoke_offline = f"失敗：{_e}"

    smoke_online = httpx.post(         # 2) 同一份範例輸入打真的服務
        f"{API_URL}/predict", json=_example_df.to_dict("records"), timeout=60
    ).json()

    # 3) 批次 vs 線上對答案——這裡重新載入 champion，**不能**沿用第 3 節那個 batch_model：
    #    它載的是換版前的 v2。拿不同版本互比，只會得到一個假的「不一致」警報。
    _batch_now = mlflow.pyfunc.load_model(MODEL_URI)
    smoke_batch = [round(float(_p[1]), 4) for _p in _batch_now.predict(_example_df)]
    smoke_match = smoke_batch == smoke_online["prob"]

    mo.md(
        f"""
    服務端目前載著 v{after_health["model_version"]}：

    1. `validate_serving_input(champion_uri, serving_input_example.json)` → **{smoke_offline}**
    2. 同一份 payload 打自包 API → `{smoke_online}`
    3. 批次算的機率 `{smoke_batch}` vs API 回的 `{smoke_online["prob"]}` →
       **{"一致 ✓" if smoke_match else "不一致 ✗（要查前處理）"}**

    `models:/{MODEL_NAME}@champion` 現在是 v{smoke_online["model_version"]}，
    **{"三項都過，可以放行" if smoke_match else "第 3 項沒過——放行前先查前處理"}**。

    第 3 項有個陷阱值得記住：這裡是**重新載入 champion** 再比，而不是沿用第 3 節那個
    `batch_model`——它載的是換版前的 v2。拿兩個不同版本互比，你會得到一個假的「不一致」警報，
    然後花半天去查根本不存在的前處理問題。**對答案的前提是兩邊真的是同一版。**

    ### 上線之後：監控要記什麼

    上線不是終點，是**開始有資料可以看**的那一刻。四類東西一定要記，缺一類就會有一種故障你看不見：

    | 記什麼 | 為什麼 | 出事時的樣子 |
    |---|---|---|
    | **延遲**（p50／p95／p99） | 平均值會騙人 | 平均 20 ms 很漂亮，p99 是 3 秒——每 100 個客戶就有 1 個在等 |
    | **錯誤率**（依狀態碼分） | 400 跟 500 是完全不同的故障 | 400 暴增＝上游資料格式變了；500 暴增＝你的服務壞了 |
    | **輸入分佈** | 資料會漂移，而且沒人會通知你 | 模型還在回答，只是答得越來越不準 |
    | **預測分佈** | 最省事的早期警報 | 判為流失的比例從 5% 跳到 30%，不用等標籤就知道有事 |

    前兩類是**軟體維運**，任何 API 都要有。後兩類是**機器學習特有**的——模型不會拋例外，
    它只會安靜地越答越爛。這正是**下一課「模型監控」**要處理的事。
    """
    )
    return smoke_batch, smoke_match, smoke_offline, smoke_online


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 8️⃣ 互動：自己量一次

    ### 批次列數 × 單筆請求數：每列成本

    拉桿選「批次一次餵幾列」與「線上 API 打幾次」，按按鈕真的量一次。
    看那一欄**每列成本**——它會告訴你「這個工作負載到底該用哪一種上線方式」。
    """
    )
    return


@app.cell
def _(mo):
    rows_slider = mo.ui.slider(10, 500, step=10, value=200, label="批次一次餵幾列", show_value=True)
    reqs_slider = mo.ui.slider(1, 30, step=1, value=10, label="線上 API 打幾次（每次 1 列）", show_value=True)
    measure_btn = mo.ui.run_button(label="量一次")
    mo.hstack([rows_slider, reqs_slider, measure_btn], wrap=True, justify="start")
    return measure_btn, reqs_slider, rows_slider


@app.cell
def _(
    API_URL,
    ONE_ROW,
    X_test,
    batch_model,
    httpx,
    measure_btn,
    mo,
    reqs_slider,
    rows_slider,
    time,
):
    mo.stop(not measure_btn.value, mo.md("*調好兩個拉桿，按「量一次」。*"))

    _n_rows = rows_slider.value
    _n_reqs = reqs_slider.value
    batch_model.predict(X_test.head(4))                      # 暖機
    _t0 = time.perf_counter()
    batch_model.predict(X_test.head(_n_rows))
    _batch_ms = (time.perf_counter() - _t0) * 1000

    httpx.post(f"{API_URL}/predict", json=ONE_ROW, timeout=60)
    _t0 = time.perf_counter()
    for _ in range(_n_reqs):
        httpx.post(f"{API_URL}/predict", json=ONE_ROW, timeout=60)
    _api_ms = (time.perf_counter() - _t0) * 1000

    _rows = [
        {
            "方式": f"批次評分（{_n_rows} 列一次）",
            "總耗時": f"{_batch_ms:.1f} ms",
            "算了幾列": _n_rows,
            "每列成本": f"{_batch_ms / _n_rows:.3f} ms",
        },
        {
            "方式": f"線上 API（{_n_reqs} 次，每次 1 列）",
            "總耗時": f"{_api_ms:.1f} ms",
            "算了幾列": _n_reqs,
            "每列成本": f"{_api_ms / _n_reqs:.3f} ms",
        },
    ]
    mo.vstack(
        [
            mo.ui.table(_rows, selection=None),
            mo.md(
                f"每列成本相差約 **{(_api_ms / _n_reqs) / (_batch_ms / _n_rows):.0f} 倍**。"
                "把批次列數拉小、請求數拉大再量一次——列數越少，批次的優勢越小；"
                "**批次的便宜完全來自「一次算很多」**，一次只算十列的批次跟線上 API 差不了多少。"
            ),
        ]
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ### 切 alias：API 什麼時候看到新模型

    下拉選一個版本、按「移 alias」——`@champion` 真的會被移過去，但 API 還沒感覺；
    再按「重載 API」才會換上新模型。這就是第 6 節那條路，只是換你按。
    """
    )
    return


@app.cell
def _(MODEL_NAME, client, mo):
    _versions = sorted(
        (int(_v.version) for _v in client.search_model_versions(f"name='{MODEL_NAME}'")),
    )
    pick_ver = mo.ui.dropdown(
        options={f"version {_v}": _v for _v in _versions},
        value=f"version {_versions[0]}",
        label="把 @champion 移到",
    )
    move_btn = mo.ui.run_button(label="移 alias")
    reload_btn = mo.ui.run_button(label="重載 API")
    mo.hstack([pick_ver, move_btn, reload_btn], wrap=True, justify="start")
    return move_btn, pick_ver, reload_btn


@app.cell
def _(API_URL, MODEL_NAME, ONE_ROW, client, httpx, mo, move_btn, pick_ver, reload_btn):
    mo.stop(
        not (move_btn.value or reload_btn.value),
        mo.md("*選一個版本後按「移 alias」，再按「重載 API」看差別。*"),
    )
    if move_btn.value:
        client.set_registered_model_alias(MODEL_NAME, "champion", pick_ver.value)
    if reload_btn.value:
        httpx.post(f"{API_URL}/reload", timeout=120)

    _registry = int(client.get_model_version_by_alias(MODEL_NAME, "champion").version)
    _health = httpx.get(f"{API_URL}/health", timeout=10).json()
    _pred = httpx.post(f"{API_URL}/predict", json=ONE_ROW, timeout=30).json()
    _same = _registry == _health["model_version"]

    mo.md(
        f"""
    - Registry 的 `@champion` → **v{_registry}**
    - API 身上載著的 → **v{_health["model_version"]}** {"（一致 ✓）" if _same else "（**還沒重載** — 按「重載 API」）"}
    - 同一位客戶的流失機率 → **{_pred["prob"][0]}**

    每一版的機率都不一樣，因為它們是不同的模型。
    「Registry 說的」跟「API 身上的」在重載之前**本來就會不一致**——
    這正是 `/health` 要回版本號的理由：不然你只能猜。
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 🏆 延伸挑戰

    1. **LEVEL 1**：`/health` 現在只回版本號。把它加上「模型是什麼時候載進來的」與「已經服務幾筆請求」
       ——線上排查時這兩個數字幾乎每次都會用到。
    2. **LEVEL 2**：改用 `dataframe_records` 信封重打 `/invocations`，並且**故意少送一欄**，
       把 HTTP 狀態碼與錯誤訊息裡的 `error_class` 印出來。
       （提示：伺服器已經在第 5 節收掉了，要先重新起一台。）
    3. **LEVEL 3**：`mlflow models build-docker` 可以把模型包成 Docker 映像。
       不用真的 build（molab 沒有 Docker），改成**自己手寫**那個 Dockerfile：
       要裝什麼、模型檔怎麼進去、`CMD` 怎麼寫、健康檢查指到哪裡。
       想想「環境跟著模型走」在 Dockerfile 裡具體是哪一行。

    先自己試，卡住再展開下面的提示與參考解答。
    帶得走：下載本檔後 `uvx marimo edit --sandbox model-serving_ext.py`
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
    在 `SERVED` 這個 dict 裡多存兩個欄位，`/predict` 每次加一：

    ```python
    import datetime as dt

    SERVED["loaded_at"] = dt.datetime.now(dt.UTC).isoformat(timespec="seconds")
    SERVED["served"] = 0

    @api.get("/health")
    def api_health():
        return {
            "status": "ok",
            "model_uri": MODEL_URI,
            "model_version": SERVED["version"],
            "loaded_at": SERVED["loaded_at"],          # 這一版是什麼時候上的
            "requests_served": SERVED["served"],       # 從載入到現在服務了幾筆
        }
    ```

    `/predict` 裡加一行 `SERVED["served"] += 1`，`/reload` 成功時把兩個值都重設。
    你應該看到類似
    `{"status": "ok", "model_version": 3, "loaded_at": "2026-09-04T…", "requests_served": 41}`。

    為什麼有用：指標在某個時間點變差時，`loaded_at` 讓你一眼確認「是不是那次換版造成的」；
    `requests_served` 則能揭穿「這台其實沒收到流量」這種負載平衡器設定錯誤。
    （正式環境請用 Prometheus 這類指標系統，這裡的計數器只是最小示範，多執行緒下並不精確。）
    """
            ),
            "💡 LEVEL 2 參考解答": mo.md(
                r"""
    ```python
    import json, os, subprocess, sys, time, httpx

    port = free_port()
    proc = subprocess.Popen(
        [sys.executable, "-m", "mlflow", "models", "serve", "-m", MODEL_URI,
         "-p", str(port), "--host", "127.0.0.1", "--env-manager", "local"],
        env={**os.environ, "MLFLOW_TRACKING_URI": mlflow.get_tracking_uri()},
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
    )
    url = f"http://127.0.0.1:{port}"
    while True:                                  # 等它起來（實測要好幾秒）
        try:
            if httpx.get(f"{url}/ping", timeout=1).status_code == 200:
                break
        except Exception:
            time.sleep(0.5)

    ok = httpx.post(f"{url}/invocations",
                    json={"dataframe_records": X_test.head(2).to_dict("records")}, timeout=60)
    bad = httpx.post(f"{url}/invocations",
                     json={"dataframe_records": X_test.head(1).drop(columns=["f11"]).to_dict("records")},
                     timeout=60)
    print(ok.status_code, ok.text[:80])
    print(bad.status_code, json.loads(bad.text)["error_class"])

    proc.terminate(); proc.communicate(timeout=15)
    ```

    你應該看到：

    ```text
    200 {"predictions": [[0.25…, 0.74…], [0.92…, 0.07…]]}
    400 SCHEMA_ENFORCEMENT_FAILED
    ```

    `dataframe_records` 是每列一個物件，比 `dataframe_split` 好讀、也比較像一般的 REST API；
    代價是欄名重複出現，資料量大時明顯比較耗頻寬。
    兩種伺服器都收，選哪個看你的呼叫端方便。
    """
            ),
            "💡 LEVEL 3 提示": mo.md(
                r"""
    `mlflow models build-docker -m models:/churn-clf@champion -n churn-api` 產出的映像，
    本質上就是把「模型資料夾 ＋ 它的 `requirements.txt` ＋ `mlflow models serve`」封在一起。
    自己寫的話大概是這個骨架：

    ```dockerfile
    FROM python:3.11-slim

    # 1) 先裝依賴（這一層很少變，Docker 會快取）
    COPY model/requirements.txt /opt/model/requirements.txt
    RUN pip install --no-cache-dir -r /opt/model/requirements.txt mlflow

    # 2) 模型資料夾整包進去——「環境跟著模型走」就是這兩步：
    #    requirements.txt 是模型自己帶的，不是你手寫的
    COPY model/ /opt/model/

    # 3) 伺服器
    EXPOSE 8080
    ENV MLFLOW_DISABLE_ENV_CREATION=true
    CMD ["mlflow", "models", "serve", "-m", "/opt/model", \
         "-h", "0.0.0.0", "-p", "8080", "--env-manager", "local"]

    HEALTHCHECK --interval=30s --timeout=3s CMD python -c \
      "import urllib.request;urllib.request.urlopen('http://127.0.0.1:8080/ping')"
    ```

    `model/` 用 `mlflow.artifacts.download_artifacts("models:/churn-clf@champion", dst_path="model")` 拿。
    映像裡用 `--env-manager local` 是對的——**環境已經是照模型的 requirements 建好的那一份**，
    不需要在容器裡再建一次。

    **怎麼驗證你寫對了**（有 Docker 的機器上）：

    1. `docker build -t churn-api .` 能過，且 `docker run -p 8080:8080 churn-api` 之後
       `curl localhost:8080/ping` 回 200。
    2. 拿 `serving_input_example.json` 打 `/invocations`，回來的機率**跟本機批次算的一致**
       ——這是第 7 節的第 3 項檢查，跨環境時更該做。
    3. `docker run --network none …` 斷網也要能起來：能起來才代表環境真的封在映像裡，
       沒有偷偷在啟動時上網裝東西。

    陷阱：`COPY` 進去的模型資料夾如果少了 `MLmodel`，`mlflow models serve` 會找不到模型
    ——一定要複製**整個資料夾**，不是只複製那個 `.skops`／`.pkl`。
    """
            ),
        }
    )
    return


if __name__ == "__main__":
    app.run()
