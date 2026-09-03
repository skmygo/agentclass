# ONNX 匯出上線：同一個模型，推論快幾百倍、不綁 Python
# 不需要 GPU——molab 免費 CPU 環境即可全程執行（不連任何外部服務）。
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "marimo",
#     "skl2onnx",
#     "onnxruntime",
#     "onnx",
#     "scikit-learn",
#     "pandas",
#     "numpy",
#     "matplotlib",
#     "mlflow>=3.0",
# ]
# ///
import marimo

__generated_with = "0.23.16"
app = marimo.App(width="medium", app_title="ONNX 匯出上線：同一個模型，推論快幾百倍")


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    # 🚀 ONNX 匯出上線：同一個模型，推論快幾百倍、不綁 Python

    上一課把模型包成 API 送上線之後，你會發現一件不太舒服的事：
    **那台伺服器裡跑的其實是一個 Python 物件。**
    它是 `pickle`（或 skops）存下來的 scikit-learn 模型，
    載回來需要一模一樣的 Python 版本、一模一樣的 scikit-learn 版本；
    每一筆預測都要走過一長串 Python 函式呼叫，單筆延遲以**毫秒**計。

    這一課換一種存法：把同一個訓練好的模型**匯出成 ONNX**。

    - **ONNX** 是「模型的通用交換格式」——它存的不是 Python 物件，是一張**運算圖**
      （輸入是什麼形狀、經過哪些算子、輸出是什麼）。
    - **onnxruntime** 是執行這張圖的引擎，有 Python／C++／C#／Java／JavaScript 各種版本。
      模型一旦是 ONNX，跑它的人**不必是 Python**。

    這份 notebook 會把「同一個 RandomForest」用兩種格式各跑一次，全部量給你看：

    1. 為什麼要換格式：pickle 綁 Python、綁版本，而且單筆很慢
    2. 轉換：`to_onnx` 的三個要點（範例輸入決定型別、`zipmap=False`、opset）
    3. 對答案：`InferenceSession` 怎麼跑，以及**換格式不能換答案**要怎麼驗
    4. 速度：500 列與單筆的延遲對照，並解釋為什麼差這麼多
    5. 上線：`.onnx` 存進 MLflow、包成一個推論函式，以及**型別與形狀合約**的兩個真實錯誤
    6. 互動：自己拉批次大小，當場量 onnxruntime 與 scikit-learn 的延遲

    > **先講清楚，免得你把數字套錯地方**：本課所有數字都是**CPU、小型表格模型**（12 個特徵、100 棵樹）跑出來的。
    > 深度學習模型或跑在 GPU 上時，加速比例完全是另一回事（常見是 1–3 倍，而不是幾百倍），
    > 因為那時候的瓶頸是矩陣運算本身，不是 Python 的呼叫開銷。
    > 每次執行的毫秒數也會浮動——**看倍數，不要看絕對值**。
    """
    )
    return


@app.cell
def _():
    import html
    import logging
    import pickle
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
    import onnx
    import onnxruntime as ort
    import pandas as pd
    from skl2onnx import to_onnx
    from sklearn.datasets import make_classification
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import roc_auc_score
    from sklearn.model_selection import train_test_split

    logging.getLogger("mlflow").setLevel(logging.ERROR)
    warnings.filterwarnings("ignore")

    WORK = Path(tempfile.gettempdir()) / "onnx-lesson"
    shutil.rmtree(WORK, ignore_errors=True)
    WORK.mkdir(parents=True, exist_ok=True)

    print("onnxruntime", ort.__version__, "| onnx", onnx.__version__)
    print("工作目錄:", WORK)
    return (
        LogisticRegression,
        Path,
        RandomForestClassifier,
        WORK,
        html,
        make_classification,
        mlflow,
        mo,
        np,
        onnx,
        ort,
        pd,
        pickle,
        plt,
        roc_auc_score,
        time,
        to_onnx,
        train_test_split,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 1️⃣ pickle 的三個代價

    先看看「上線的模型」現在是什麼樣子。我們沿用整個系列的那份流失資料
    （2000 筆、12 個特徵 `f0`–`f11`、切成 train 1500／test 500），
    訓練一個 100 棵樹的 RandomForest，然後照最常見的做法 `pickle` 存起來。

    這個檔案有三個你上線後才會痛的代價：

    | 代價 | 症狀 |
    |---|---|
    | **綁 Python** | 只有 Python 讀得回來。前端、行動裝置、Java 服務想直接跑？做不到，只能再包一層 API |
    | **綁版本** | 用 scikit-learn 1.7 存的檔，在 1.4 的機器上 `load` 可能直接爆，或更糟——**不報錯但算錯** |
    | **慢** | 每一筆預測都要穿過一整層 Python 物件與函式呼叫，單筆延遲以毫秒計 |

    第三點最容易被忽略：批次算 500 列的時候均攤下來很便宜，
    但線上 API 是**一次來一筆**——那時候你付的是「單筆」的價錢，不是「每列」的價錢。
    """
    )
    return


@app.cell
def _(
    LogisticRegression,
    RandomForestClassifier,
    WORK,
    make_classification,
    np,
    pd,
    pickle,
    roc_auc_score,
    train_test_split,
):
    _X, _y = make_classification(
        n_samples=2000, n_features=12, n_informative=6, random_state=0
    )
    COLS = [f"f{i}" for i in range(12)]
    _Xtr, _Xte, y_train, y_test = train_test_split(
        _X.astype(np.float32), _y, test_size=0.25, random_state=0
    )
    # 一律用 float32：ONNX 的預設張量型別就是 float32，訓練時就統一可以少一個坑
    X_train = _Xtr.astype(np.float32)
    X_test = _Xte.astype(np.float32)

    rf = RandomForestClassifier(n_estimators=100, max_depth=8, random_state=0).fit(
        X_train, y_train
    )
    logreg = LogisticRegression(max_iter=1000).fit(X_train, y_train)

    PKL = WORK / "rf.pkl"
    PKL.write_bytes(pickle.dumps(rf))

    print(f"train {X_train.shape} / test {X_test.shape}  dtype={X_train.dtype}")
    print(f"RandomForest  AUC = {roc_auc_score(y_test, rf.predict_proba(X_test)[:, 1]):.4f}")
    print(f"LogisticRegression AUC = {roc_auc_score(y_test, logreg.predict_proba(X_test)[:, 1]):.4f}")
    print(f"\npickle 檔案大小: {PKL.stat().st_size / 1024:.0f} KB   （{PKL.name}）")
    pd.DataFrame(X_test[:3], columns=COLS).round(3)
    return COLS, PKL, X_test, X_train, logreg, rf, y_test


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 2️⃣ 轉換：`to_onnx` 的三個要點

    `skl2onnx` 把一個 **已經 fit 過** 的 scikit-learn 模型翻譯成 ONNX 運算圖。
    整件事只有一行，但那一行裡有三個一定要懂的東西：

    ```python
    from skl2onnx import to_onnx

    onx = to_onnx(
        rf,                                    # 已經 fit 過的模型
        X_train[:1],                           # ① 範例輸入：決定輸入的型別與欄數
        options={id(rf): {"zipmap": False}},   # ② 機率用 ndarray 回，不要 list of dict
    )
    ```

    **① 範例輸入決定了合約。** 轉換器不會去猜你的資料長什麼樣，它從這一筆範例讀出
    「12 個欄位、`float32`」，把這個形狀**寫死進圖裡**。所以範例的 dtype 就是你之後餵資料時**必須**用的 dtype
    ——這裡給 `float32`，上線時餵 `float64` 就會被擋（第 5 節有錯誤原文）。
    忘了給範例輸入的話會直接告訴你：`NotImplementedError: Initial types must be specified.`

    **② `zipmap=False` 是幾乎每次都要加的一行。** sklearn 分類器轉出來的預設行為，
    會把機率包成「每列一個 `{類別: 機率}` 字典」（那個算子叫 ZipMap）。
    它看起來友善，但拿到的是 Python 的 list of dict，不能直接切欄、也不好傳給別的語言。
    關掉之後 `probabilities` 就是乾淨的 `(n, 2)` ndarray。

    **③ opset 是「算子的版本號」。** 執行端的 onnxruntime 版本太舊、不認得你用的 opset，就會載不起來
    ——跨團隊交付時要一起講清楚（`target_opset=` 可以指定）。

    轉完之後看三樣東西：**graph 的 inputs／outputs** 是你的對外合約，**檔案大小**則是意外的收穫。
    """
    )
    return


@app.cell
def _(PKL, WORK, X_train, onnx, rf, time, to_onnx):
    _t0 = time.perf_counter()
    onx = to_onnx(rf, X_train[:1], options={id(rf): {"zipmap": False}})
    convert_s = time.perf_counter() - _t0

    ONNX_PATH = WORK / "rf.onnx"
    ONNX_PATH.write_bytes(onx.SerializeToString())

    def _shape(v):
        return [d.dim_value or d.dim_param or "?" for d in v.type.tensor_type.shape.dim]

    print(f"轉換耗時: {convert_s:.2f} s")
    print("\n--- graph 合約 ---")
    for _i in onx.graph.input:
        print(f"  input  {_i.name:16s} shape={_shape(_i)}  (elem_type 1 = float32)")
    for _o in onx.graph.output:
        print(f"  output {_o.name:16s} shape={_shape(_o)}")
    print("  opset:", [(o.domain or "ai.onnx（預設）", o.version) for o in onx.opset_import])
    print("  節點:", {n.op_type: 1 for n in onx.graph.node})

    _onnx_kb = ONNX_PATH.stat().st_size / 1024
    _pkl_kb = PKL.stat().st_size / 1024
    print("\n--- 檔案大小 ---")
    print(f"  rf.onnx  {_onnx_kb:7.0f} KB")
    print(f"  rf.pkl   {_pkl_kb:7.0f} KB   → ONNX 是 pickle 的 {_onnx_kb / _pkl_kb:.2f} 倍")
    print(f"\nonnx.checker.check_model → {onnx.checker.check_model(onx)}（回 None 就是通過）")
    return ONNX_PATH, onx


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    輸入那一欄的第一維是空字串（動態維度），意思是「幾列都可以」；第二維 12 是寫死的。
    輸出有兩個：`label`（預測類別）與 `probabilities`（(n, 2) 機率）——這就是 `zipmap=False` 換來的乾淨形狀。

    檔案小是因為 ONNX 存的是「這棵森林的判斷規則」本身（一個 `TreeEnsembleClassifier` 算子把 100 棵樹全吃下去），
    而 pickle 要把 100 個 Python 物件連同 numpy 陣列與所有屬性都序列化進去。
    整個 RandomForest 在圖裡**只有一個節點**——這也是它跑得快的原因：沒有 100 次 Python 層的樹走訪。

    ## 3️⃣ 對答案：換格式，不換答案

    這是上線前**一定要做**的一件事，而且很多人漏掉：
    轉換是「翻譯」，翻譯有可能翻錯（不支援的參數被靜靜忽略、機率的欄序顛倒、float32 的捨入）。
    所以每次轉完，**用同一批資料跑兩邊、逐筆比對**，寫成一個可以重複跑的函式。

    ```python
    sess = ort.InferenceSession(str(ONNX_PATH), providers=["CPUExecutionProvider"])
    label, proba = sess.run(None, {sess.get_inputs()[0].name: X_test})
    ```

    - `InferenceSession` 是「載入並準備好這張圖」，只做一次（跟上一課的「模型載一次 vs 每次載」同一個道理）。
    - `sess.run(None, {輸入名: 陣列})`：第一個參數 `None` 表示「所有輸出都要」，回來的是一個 list，
      順序就是 graph outputs 的順序。
    - 輸入是 **dict**，key 是圖裡的輸入名字（這裡是 `X`）——名字打錯會得到
      `ValueError: Required inputs (['X']) are missing from input feed (['input']).`
    """
    )
    return


@app.cell
def _(ONNX_PATH, X_test, np, ort, rf):
    sess = ort.InferenceSession(str(ONNX_PATH), providers=["CPUExecutionProvider"])
    IN = sess.get_inputs()[0].name
    onnx_label, onnx_proba = sess.run(None, {IN: X_test})
    onnx_proba = np.asarray(onnx_proba)

    def assert_same(sk_model, session, in_name, X, atol=1e-5):
        """換格式不換答案：機率誤差在容許範圍內、且類別完全一致才回 True。"""
        _lab, _pr = session.run(None, {in_name: X})
        _pr = np.asarray(_pr)
        max_diff = float(np.abs(_pr - sk_model.predict_proba(X)).max())
        agree = float((np.asarray(_lab) == sk_model.predict(X)).mean())
        ok = max_diff < atol and agree == 1.0
        print(
            f"  機率最大差異 {max_diff:.2e}（門檻 {atol:.0e}）｜類別一致率 {agree:.1%}"
            f"  → {'✅ 通過' if ok else '❌ 不一致，先別上線'}"
        )
        return ok

    print(f"輸入名稱: {IN}｜輸出: {[o.name for o in sess.get_outputs()]}")
    print(f"label {np.asarray(onnx_label).shape} | probabilities {onnx_proba.shape}\n")
    print("ONNX vs scikit-learn（500 列 test set）")
    _same_ok = assert_same(rf, sess, IN, X_test)
    print(f"\n第 0 筆：ONNX {onnx_proba[0].round(6)}  ｜  sklearn {rf.predict_proba(X_test[:1])[0].round(6)}")
    return IN, assert_same, sess


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    差異落在 `1e-7` 這個量級，而類別 100% 一致。
    這個差不是 bug，是 **float32 的捨入**：ONNX 圖用 32 位元浮點數算，sklearn 內部是 64 位元。
    對「機率大於 0.5 就判正」這種用法完全無關痛癢，但你要知道它存在——
    如果你的閾值卡在 0.500000 附近、或下游要拿機率做精算，就要自己決定容許值。

    **把 `assert_same()` 放進 CI**：每次重訓、每次升 skl2onnx／onnxruntime 版本都跑一次。
    它抓得到的是最可怕的那種故障——**沒有任何錯誤訊息，只是答案悄悄不一樣了**。

    ## 4️⃣ 速度：批次差 10 倍上下，單筆差幾百倍
    """
    )
    return


@app.cell
def _(IN, X_test, logreg, np, pd, rf, sess, time, to_onnx, ort):
    def bench(fn, n, warmup=5):
        for _ in range(warmup):
            fn()
        _t0 = time.perf_counter()
        for _ in range(n):
            fn()
        return (time.perf_counter() - _t0) / n * 1000  # ms

    _one = X_test[:1]
    _onx_lr = to_onnx(logreg, X_test[:1], options={id(logreg): {"zipmap": False}})
    sess_lr = ort.InferenceSession(
        _onx_lr.SerializeToString(), providers=["CPUExecutionProvider"]
    )
    _in_lr = sess_lr.get_inputs()[0].name

    ROWS = [
        ("RandomForest", "500 列一次", bench(lambda: rf.predict_proba(X_test), 30),
         bench(lambda: sess.run(None, {IN: X_test}), 30)),
        ("RandomForest", "單筆", bench(lambda: rf.predict_proba(_one), 300),
         bench(lambda: sess.run(None, {IN: _one}), 300)),
        ("LogisticRegression", "單筆", bench(lambda: logreg.predict_proba(_one), 300),
         bench(lambda: sess_lr.run(None, {_in_lr: _one}), 300)),
    ]
    lat = pd.DataFrame(ROWS, columns=["模型", "情境", "sklearn_ms", "onnx_ms"])
    lat["加速倍數"] = (lat["sklearn_ms"] / lat["onnx_ms"]).round(0).astype(int)

    for _m, _c, _sk, _ox, _x in lat.itertuples(index=False):
        print(f"{_m:20s} {_c:10s}  sklearn {_sk:8.3f} ms  ｜  onnxruntime {_ox:7.3f} ms  → 快 {_x} 倍")
    print(
        f"\n每列成本：500 列批次時 onnxruntime 每列 {ROWS[0][3] / 500 * 1000:.1f} µs，"
        f"單筆時每列 {ROWS[1][3] * 1000:.1f} µs"
    )
    return bench, lat, sess_lr


@app.cell(hide_code=True)
def _(lat, np, plt):
    _fig, _ax = plt.subplots(figsize=(6.2, 3.0))
    _y = np.arange(len(lat))
    _ax.barh(_y + 0.19, lat["sklearn_ms"], height=0.36, color="#C44E52", label="scikit-learn")
    _ax.barh(_y - 0.19, lat["onnx_ms"], height=0.36, color="#55A868", label="onnxruntime")
    for _i, (_sk, _ox) in enumerate(zip(lat["sklearn_ms"], lat["onnx_ms"])):
        _ax.text(_sk * 1.15, _i + 0.19, f"{_sk:.2f} ms", va="center", fontsize=8)
        _ax.text(_ox * 1.15, _i - 0.19, f"{_ox:.3f} ms", va="center", fontsize=8)
    _ax.set_yticks(_y)
    _ax.set_yticklabels([f"{m}\n{c}" for m, c in zip(lat["模型"], lat["情境"])], fontsize=8)
    _ax.set_xscale("log")
    _ax.set_xlabel("latency per call (ms, log scale)")
    _ax.set_xlim(0.005, 60)
    _ax.legend(fontsize=8, loc="lower right")
    _ax.grid(axis="x", alpha=0.25)
    _ax.set_title("same model, two runtimes", fontsize=10)
    plt.tight_layout()
    _ax
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    橫軸是 **log 刻度**——不用 log 的話，onnxruntime 的單筆長條會短到看不見。

    **為什麼差這麼多？** 兩件事加起來：

    1. **Python 物件的開銷**：`rf.predict_proba(一筆)` 要建 numpy 陣列、跑輸入檢查、
       在 Python 層迴圈走訪 100 棵樹再平均。這些固定成本跟資料量幾乎無關，
       所以**一筆和五百筆花的時間差不多**——單筆時它們就是全部的成本。
    2. **編譯好的算子**：onnxruntime 那邊，整座森林是一個 C++ 寫好的 `TreeEnsembleClassifier`，
       圖在 `InferenceSession` 建立時就規劃好了記憶體與執行順序。一次呼叫只是把資料丟進去。

    所以請注意這個關鍵區別：
    **批次 500 列只快 10 倍上下，單筆卻快好幾百倍。**
    加速的來源主要是「每次呼叫的固定成本」，量大的時候會被均攤掉。
    上一課的線上 API 之所以最該換 ONNX，就是因為它永遠在付單筆的價錢。

    > 再提醒一次：這是 CPU、12 特徵、100 棵樹的樹模型。
    > 換成大型神經網路、或跑在 GPU 上，瓶頸變成矩陣乘法本身，
    > ONNX 帶來的通常是 1–3 倍，不是幾百倍。**自己量過再對外報數字。**

    ## 5️⃣ 上線：存進 MLflow、包成函式、守住合約
    """
    )
    return


@app.cell
def _(IN, ONNX_PATH, WORK, mlflow, onx, rf, sess, np, X_test):
    mlflow.set_tracking_uri(f"sqlite:///{WORK / 'mlflow.db'}")
    try:
        _exp = mlflow.create_experiment("onnx-export", artifact_location=str(WORK / "artifacts"))
    except Exception:  # noqa: BLE001
        _exp = mlflow.get_experiment_by_name("onnx-export").experiment_id
    mlflow.set_experiment(experiment_id=_exp)

    with mlflow.start_run(run_name="rf-onnx") as run:
        mlflow.log_params({"n_estimators": 100, "max_depth": 8, "runtime": "onnxruntime"})
        try:
            info = mlflow.onnx.log_model(onx, name="model_onnx")
            how = f"mlflow.onnx.log_model → {info.model_uri}"
        except Exception as _e:  # noqa: BLE001  沒有 onnx flavor 時的退路：當成純檔案存
            mlflow.log_artifact(str(ONNX_PATH), artifact_path="model_onnx")
            how = f"log_artifact（fallback: {type(_e).__name__}）"
        mlflow.log_metric("onnx_kb", ONNX_PATH.stat().st_size / 1024)
    print("run_id:", run.info.run_id)
    print("模型存法:", how)

    def predict_proba_onnx(session, in_name, rows):
        """上線用的推論函式：只做三件事——轉 float32、跑圖、取正類機率。"""
        X = np.asarray(rows, dtype=np.float32)
        if X.ndim == 1:
            X = X.reshape(1, -1)
        return np.asarray(session.run(None, {in_name: X})[1])[:, 1]

    print("\npredict_proba_onnx(前 3 列) =", predict_proba_onnx(sess, IN, X_test[:3]).round(4))
    print("sklearn 對照            =", rf.predict_proba(X_test[:3])[:, 1].round(4))
    return (predict_proba_onnx,)


@app.cell
def _(IN, X_test, html, mo, sess):
    def _err(tag, fn):
        try:
            fn()
            return f"[{tag}] （沒報錯）"
        except Exception as e:  # noqa: BLE001
            return f"[{tag}] {type(e).__name__}:\n{str(e).strip()}"

    _msgs = [
        _err("餵 float64", lambda: sess.run(None, {IN: X_test.astype("float64")})),
        _err("少一欄（11 欄）", lambda: sess.run(None, {IN: X_test[:, :11]})),
        _err("忘了 reshape（一維）", lambda: sess.run(None, {IN: X_test[0]})),
    ]
    mo.Html("<pre>" + html.escape("\n\n".join(_msgs)) + "</pre>")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    這三個錯誤就是 ONNX 的**合約**在說話，而且它們是**好消息**：

    - **型別錯**（`Unexpected input data type. Actual: (tensor(double)) , expected: (tensor(float))`）——
      pandas 的 `.values` 預設是 `float64`，直接丟進去必炸。推論函式裡固定寫
      `np.asarray(rows, dtype=np.float32)` 就一勞永逸。
    - **欄數錯**（`Got invalid dimensions for input: X … index: 1 Got: 11 Expected: 12`）——
      上游少送一個特徵，這裡當場擋下來。pickle 的 sklearn 模型在同樣情況下可能**照算不誤**，
      算出一個沒有意義的機率，而且沒有人會發現。
    - **維度錯**（`Invalid rank for input: X Got: 1 Expected: 2`）——單筆推論忘了 `reshape(1, -1)`，
      這是線上服務最常見的第一個 bug。

    **上線的三種接法**（都用同一個 `.onnx` 檔）：

    1. **接上一課的 FastAPI**：把 handler 裡的 `model.predict` 換成這一課的 `predict_proba_onnx`，
      `InferenceSession` 在服務啟動時建立一次。程式碼幾乎沒變，單筆延遲少一個數量級。
    2. **交給別的語言**：C++／Java／C# 都有 onnxruntime，讀同一個檔、輸出同一個答案——
      模型不再需要一台 Python 伺服器才能存在。
    3. **搬進瀏覽器**：`onnxruntime-web` 可以直接在使用者的瀏覽器裡跑這張圖（本課不實作），
      資料完全不離開裝置。

    不管走哪一條，都記得把 `.onnx` 跟訓練它的 run 綁在一起（上面 `mlflow.onnx.log_model` 那步），
    否則三個月後沒有人知道線上那個檔案是誰、什麼時候、用哪份資料訓出來的。

    ## 6️⃣ 互動：自己拉批次大小，當場量
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    n_rows = mo.ui.slider(1, 500, value=1, step=1, label="每次送幾列", show_value=True)
    which = mo.ui.radio(["RandomForest", "LogisticRegression"], value="RandomForest", inline=True)
    run_btn = mo.ui.run_button(label="量一次延遲")
    mo.vstack([mo.hstack([n_rows, which], wrap=True, justify="start"), run_btn])
    return n_rows, run_btn, which


@app.cell(hide_code=True)
def _(IN, X_test, bench, logreg, n_rows, np, rf, run_btn, sess, sess_lr, which):
    if run_btn.value:
        _k = int(n_rows.value)
        _batch = np.tile(X_test, (max(1, _k // 500 + 1), 1))[:_k].astype(np.float32)
        _reps = 200 if _k <= 10 else 30
        if which.value == "RandomForest":
            _model, _s, _name = rf, sess, IN
        else:
            _model, _s, _name = logreg, sess_lr, sess_lr.get_inputs()[0].name
        measured = {
            "rows": _k,
            "model": which.value,
            "sk": bench(lambda: _model.predict_proba(_batch), _reps),
            "ox": bench(lambda: _s.run(None, {_name: _batch}), _reps),
        }
    else:
        measured = None
    return (measured,)


@app.cell(hide_code=True)
def _(measured, mo, plt):
    mo.stop(
        measured is None,
        mo.md("☝️ 拉好列數與模型，按 **量一次延遲** ——數字是這台機器**當下**跑出來的。"),
    )

    _fig, _ax = plt.subplots(figsize=(6.2, 2.4))
    _vals = [measured["sk"], measured["ox"]]
    _ax.barh(["scikit-learn", "onnxruntime"], _vals, color=["#C44E52", "#55A868"], height=0.5)
    for _i, _v in enumerate(_vals):
        _ax.text(_v * 1.15, _i, f"{_v:.3f} ms", va="center", fontsize=9)
    _ax.set_xscale("log")
    _ax.set_xlim(min(_vals) * 0.4, max(_vals) * 12)
    _ax.set_xlabel("latency per call (ms, log scale)")
    _ax.set_title(
        f"{measured['model']} — {measured['rows']} rows/call"
        f"  →  {measured['sk'] / measured['ox']:.0f}x faster",
        fontsize=10,
    )
    _ax.grid(axis="x", alpha=0.25)
    plt.tight_layout()
    _ax
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    把列數從 1 拉到 500，看那個倍數怎麼縮小——**這就是本課最重要的一張圖**。
    ONNX 省的是每次呼叫的固定成本，批次越大越均攤，加速比就越不驚人。
    你的服務是「一次一筆」還是「一次一批」，決定了換 ONNX 值不值得。

    ## 🏆 換你動手

    三題由淺到深。先自己寫，卡住再展開解答。
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    **LEVEL 1 — 轉一個 LogisticRegression 並對答案。**
    用 `to_onnx` 把 `logreg` 轉出來、建一個 session，然後呼叫本課的 `assert_same()`。
    它的檔案大小跟 RandomForest 的 `.onnx` 差多少？為什麼？

    **LEVEL 2 — 檢查一張陌生的圖。**
    別人丟給你一個 `.onnx`，你要在載入之前知道它安不安全、長什麼樣。
    用 `onnx.load()` 讀進來，跑 `onnx.checker.check_model()`，
    再列出 graph 裡**每種節點型別各有幾個**、以及 opset 版本。
    RandomForest 那張圖有幾個節點？（答案可能會嚇你一跳。）

    **LEVEL 3 — 執行緒數對延遲的影響。**
    `ort.SessionOptions()` 有一個 `intra_op_num_threads`，控制單一算子內部用幾條執行緒。
    建三個 session（1、2、預設）測**單筆**與 **500 列**的延遲，畫成表格。
    猜猜看：單筆的情況下，執行緒開多會變快還是變慢？
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
    onx_lr = to_onnx(logreg, X_train[:1], options={id(logreg): {"zipmap": False}})
    (WORK / "logreg.onnx").write_bytes(onx_lr.SerializeToString())
    s_lr = ort.InferenceSession(str(WORK / "logreg.onnx"), providers=["CPUExecutionProvider"])
    assert_same(logreg, s_lr, s_lr.get_inputs()[0].name, X_test)
    ```

    你應該看到機率最大差異在 `1e-7` 這個量級、類別 100% 一致（跟 RandomForest 同一個原因：float32 捨入）。

    **檔案大小差很多**：LogisticRegression 的 ONNX 只有幾 KB，RandomForest 是幾百 KB。
    因為線性模型要存的只有 12 個係數加一個截距，而森林要存 100 棵樹的**每一個分支條件**。
    這也解釋了為什麼線性模型的加速倍數比較小（幾十倍而不是幾百倍）——
    它原本在 sklearn 裡就只是一次矩陣乘法，Python 開銷占比沒那麼誇張。
    """
            ),
            "💡 LEVEL 2 參考解答": mo.md(
                r"""
    ```python
    m = onnx.load(str(ONNX_PATH))
    onnx.checker.check_model(m)          # 通過就安靜地回 None，壞掉才拋例外

    from collections import Counter
    print(Counter(n.op_type for n in m.graph.node))
    print([(o.domain or "ai.onnx", o.version) for o in m.opset_import])
    ```

    輸出會像這樣（實測）：

    ```text
    Counter({'TreeEnsembleClassifier': 1})
    [('ai.onnx.ml', 1), ('ai.onnx', 22)]
    ```

    **整個 100 棵樹的森林在圖裡只有一個節點。** 樹的結構全部放在那個算子的屬性裡
    （分支特徵、閾值、葉節點的值都是長長的陣列），由 onnxruntime 用編譯好的 C++ 一次走完
    ——這正是第 4 節那個倍數的來源。

    `ai.onnx.ml` 是機器學習專用的算子集合（樹、SVM、標準化那些），
    `ai.onnx` 才是通用的張量運算。執行端兩個都要支援才載得起來。
    """
            ),
            "💡 LEVEL 3 提示與驗證法": mo.md(
                r"""
    ```python
    def make_sess(threads):
        so = ort.SessionOptions()
        if threads:
            so.intra_op_num_threads = threads
        return ort.InferenceSession(str(ONNX_PATH), so, providers=["CPUExecutionProvider"])

    for t in (1, 2, None):                      # None ＝ 交給 onnxruntime 自己決定
        s = make_sess(t)
        nm = s.get_inputs()[0].name
        one = bench(lambda: s.run(None, {nm: X_test[:1]}), 300)
        big = bench(lambda: s.run(None, {nm: X_test}), 30)
        print(f"threads={str(t):>4}  單筆 {one:.3f} ms   500 列 {big:.3f} ms")
    ```

    **怎麼判斷你做對了**：三件事要同時成立。

    1. **單筆時，執行緒多不會比較快，常常還更慢**——一筆資料的工作量太小，
       開執行緒、分派、等它們收工的成本超過省下來的計算。線上 API 這種一次一筆的場景，
       `intra_op_num_threads = 1` 往往是最好的設定。
    2. **500 列時多執行緒才可能有幫助**，而且效果看你的機器有幾顆核心
       （molab 免費環境核心數少，可能三種設定差不多——那也是有效的觀察，寫下來就好）。
    3. 不管怎麼調，`assert_same()` 都要照過。**調效能不可以改變答案**，
       這是所有效能優化的第一條紅線。

    延伸一步：跑多個服務行程時更要把 `intra_op_num_threads` 設成 1，
    否則每個行程都以為整台機器是自己的、各自開滿執行緒，互相搶 CPU 反而全部變慢
    ——這是推論服務最常見的效能反模式之一。
    """
            ),
        }
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 📌 帶走這幾句

    - **ONNX 是格式，onnxruntime 是引擎。** 前者讓模型不綁 Python，後者讓它跑得快。
    - **`to_onnx` 的範例輸入就是合約**：dtype 用 `float32`、欄數寫死進圖裡；`zipmap=False` 幾乎一定要加。
    - **轉完一定要對答案**：`assert_same()` 進 CI，float32 的 `1e-7` 差異可以接受，
      類別不一致或誤差跳到 `1e-2` 就是翻譯出錯了。
    - **加速主要來自每次呼叫的固定成本**：單筆場景（線上 API）收益最大，大批次會被均攤掉。
    - **合約錯誤是好消息**：型別／欄數／維度當場擋下來，好過 pickle 那種靜靜算錯。
    - **數字要自己量**：CPU 小樹模型幾百倍，GPU 深度模型可能只有 1–3 倍。
    """
    )
    return


if __name__ == "__main__":
    app.run()
