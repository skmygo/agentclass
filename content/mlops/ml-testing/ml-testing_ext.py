# ML 測試：用 pytest 幫模型寫行為測試——「AUC 0.968」不是驗收，測試才是
# 不需要 GPU——molab 免費 CPU 環境即可全程執行（全部在記憶體與暫存資料夾裡跑，不連任何伺服器）。
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "marimo",
#     "pytest",
#     "scikit-learn",
#     "pandas",
#     "numpy",
#     "matplotlib",
#     "mlflow>=3.0",
#     "hypothesis",
# ]
# ///
import marimo

__generated_with = "0.23.16"
app = marimo.App(width="medium", app_title="ML 測試：用 pytest 幫模型寫行為測試")


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    # 🧪 ML 測試：用 pytest 幫模型寫行為測試

    ## 一個沒有人會反對的數字

    「這一版 AUC 0.968，比上一版好，可以上線了嗎？」

    幾乎每個團隊的模型驗收都停在這裡：一個數字，過門檻就發車。但那個數字沒有告訴你——

    - 輸入多了一點量測雜訊，預測會不會整個翻掉？
    - 對某一群客戶（例如某個地區、某個方案）是不是特別不準？
    - 把「使用量」調高，流失機率反而**下降**？（模型學到了跟常識相反的關係）
    - 少送一個欄位時，它會炸掉，還是默默用錯的形狀算出一個答案？

    這四件事，AUC 一個都測不到。而它們正是模型上線之後最常出事的地方。

    ## 軟體有單元測試，模型呢？

    寫程式的人不會說「這支程式我跑過一次沒噴錯，可以上線了」——他們寫測試。
    測試不是為了證明程式對，是為了**把「我相信它應該怎樣」寫成會自動跑的斷言**，
    以後任何人改任何一行，這些信念都會被重新檢查一次。

    模型完全一樣，只是「應該怎樣」的內容不同：

    | | 軟體單元測試 | 模型行為測試 |
    |---|---|---|
    | 測什麼 | 函式的輸入 → 輸出 | 模型的輸入 → 預測 |
    | 誰會讓它變 | 有人改了程式碼 | 有人**重訓**了模型（資料也算） |
    | 通過的意思 | 這些行為還在 | 這些信念還成立 |
    | 沒過怎麼辦 | 不准 merge | **不准註冊、不准晉升 champion** |

    ML 的測試金字塔跟軟體的形狀一樣，只是每一層換了主角：

    ```text
              ┌──────────────────────┐
              │  管線／整合測試        │  第 5 課：訓練→評估→閘門→註冊真的跑得完
              ├──────────────────────┤
              │  模型行為測試          │  ← 本課
              ├──────────────────────┤
              │  資料測試              │  第 9 課：pandera 合約，壞資料進不了管線
              └──────────────────────┘
    ```

    第 9 課守的是「進來的資料長得對」，本課守的是「**訓練出來的模型行為對**」，
    第 5 課的品質閘則是把兩者接進自動化管線。這一課會把第 5 課那個
    「AUC ≥ 0.95」的單一數字，擴成一整套 10 條測試。

    ## 這份 notebook 帶你做完

    1. 準備：同一份流失資料、一個 champion、兩個「壞掉的模型」，以及在 notebook 裡跑 pytest 的方法
    2. **合約測試**：輸出形狀與範圍、少一欄要炸、決定性——跟第 2 課的 signature 對照
    3. **表現測試**：最低 AUC、不能比上一版退步、切片（子群）不能特別差
    4. **行為測試**：不變性、方向性、最低功能（黃金樣本）——CheckList 三件套
    5. 全部一起跑：10 條測試、一個 exit code
    6. 讓測試失敗：換上兩個壞模型，看紅的分別是哪幾條
    7. 放進流程：exit code 當閘門、`-k` / mark 選測試、CI 的 YAML、測試結果寫進 MLflow
    8. 互動：挑一個模型、挑要跑哪幾類測試，真的跑一次 pytest

    全部在你自己的執行環境裡跑，**不連任何伺服器、不需要 GPU**：資料是隨機產生的假客戶。
    從第一格往下全部執行即可（首次安裝套件約 1–2 分鐘）。
    """
    )
    return


@app.cell
def _():
    import contextlib
    import io
    import json
    import logging
    import os
    import pickle
    import shutil
    import sys
    import tempfile
    import textwrap
    import time
    import warnings
    from pathlib import Path

    import marimo as mo
    import matplotlib.pyplot as plt
    import numpy as np
    import pandas as pd
    import pytest
    import sklearn

    warnings.filterwarnings("ignore")
    logging.getLogger("mlflow").setLevel(logging.ERROR)
    return (
        Path,
        contextlib,
        io,
        json,
        mo,
        np,
        os,
        pd,
        pickle,
        plt,
        pytest,
        shutil,
        sklearn,
        sys,
        tempfile,
        textwrap,
        time,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 1️⃣ 準備：一個 champion、兩個壞模型、一個工作資料夾

    測試要有東西可以測。這一節做三件事：

    1. **資料與模型**：沿用整個系列的流失預測資料（2000 位客戶、12 個特徵 `f0`–`f11`），
       訓練一個 `RandomForest` 當 champion，另外故意訓練兩個壞模型當「對照組」——
       第 6 節會用同一套測試去撞它們。
    2. **把測試要用的東西存成檔案**：模型、測試集、上一版的指標、幾筆黃金樣本。
       這一步很重要：**測試檔應該是一支獨立的程式**，它從磁碟載入模型與資料，
       不依賴 notebook 的變數——因為 CI 上跑測試的機器沒有你的 notebook。
    3. **一個 `run_tests()`**：在 notebook 裡呼叫 `pytest.main()`，把 pytest 的輸出接回來印出來。

    工作資料夾放在系統暫存區（`ml-testing-lesson`），每次從頭跑會先清空——重跑數字才一致。
    """
    )
    return


@app.cell
def _(Path, mo, pytest, shutil, sklearn, tempfile):
    WORK = Path(tempfile.gettempdir()) / "ml-testing-lesson"
    shutil.rmtree(WORK, ignore_errors=True)
    (WORK / "models").mkdir(parents=True)

    # pytest.ini：註冊自訂 mark（第 7 節會用 @pytest.mark.slow），
    # 順便讓 pytest 把這個資料夾當成 rootdir，輸出裡的路徑才會短。
    (WORK / "pytest.ini").write_text(
        "[pytest]\nmarkers =\n    slow: 跑得久的測試（重訓、全量資料）\n"
    )
    mo.md(
        f"工作資料夾：`{WORK}`　·　本次執行環境："
        f"pytest {pytest.__version__}、scikit-learn {sklearn.__version__}"
    )
    return (WORK,)


@app.cell
def _(np, pd):
    from sklearn.datasets import make_classification
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import accuracy_score, roc_auc_score
    from sklearn.model_selection import train_test_split

    _X, _y = make_classification(
        n_samples=2000, n_features=12, n_informative=6, random_state=0
    )
    COLS = [f"f{i}" for i in range(12)]
    X_tr, X_te, y_tr, y_te = train_test_split(
        pd.DataFrame(_X, columns=COLS), _y, test_size=0.25, random_state=0
    )

    # 上一版：邏輯迴歸（第 1 課的 baseline）——「不能比上一版退步」要比的就是它
    prev_model = LogisticRegression(max_iter=1000).fit(X_tr, y_tr)
    PREV = {
        "model": "logreg-v1",
        "accuracy": round(float(accuracy_score(y_te, prev_model.predict(X_te))), 4),
        "auc": round(float(roc_auc_score(y_te, prev_model.predict_proba(X_te)[:, 1])), 4),
    }

    # 這一版的候選：champion（正常）＋兩個壞模型（第 6 節的對照組）
    MODELS = {
        "champion": RandomForestClassifier(
            n_estimators=100, max_depth=8, random_state=0
        ).fit(X_tr, y_tr),
        "shallow": RandomForestClassifier(
            n_estimators=100, max_depth=1, random_state=0
        ).fit(X_tr, y_tr),
        "shuffled": RandomForestClassifier(
            n_estimators=100, max_depth=8, random_state=0
        ).fit(X_tr, np.random.default_rng(42).permutation(y_tr)),
    }
    SCORE = {
        _n: {
            "auc": float(roc_auc_score(y_te, _m.predict_proba(X_te)[:, 1])),
            "acc": float(accuracy_score(y_te, _m.predict(X_te))),
        }
        for _n, _m in MODELS.items()
    }
    return COLS, MODELS, PREV, SCORE, X_te, X_tr, y_te, y_tr


@app.cell(hide_code=True)
def _(PREV, SCORE, X_te, X_tr, mo):
    mo.md(
        f"""
    訓練集 {len(X_tr)} 列、測試集 {len(X_te)} 列。上一版 **{PREV["model"]}**：
    accuracy {PREV["accuracy"]:.4f}、AUC {PREV["auc"]:.4f}。這一版的三個候選：

    | 模型 | 怎麼來的 | AUC | accuracy |
    |---|---|---|---|
    | **champion** | RandomForest，100 棵樹、深度 8 | {SCORE["champion"]["auc"]:.4f} | {SCORE["champion"]["acc"]:.4f} |
    | **shallow** | 同樣 100 棵樹，但深度只有 **1**（每棵樹只問一個問題） | {SCORE["shallow"]["auc"]:.4f} | {SCORE["shallow"]["acc"]:.4f} |
    | **shuffled** | 同樣的設定，但訓練前把**標籤打亂**（模型什麼都學不到） | {SCORE["shuffled"]["auc"]:.4f} | {SCORE["shuffled"]["acc"]:.4f} |

    先記住一件事：**這三個模型的 `predict_proba` 都跑得動、都回合法的機率。**
    程式沒有任何錯誤，只有行為不一樣——這正是模型測試存在的理由。
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ### 把測試要用的東西存成檔案

    測試檔待會會去讀這些檔案。特別看兩樣東西：

    - **`baseline.json`**：上一版的指標。「不能比上一版退步」要有東西可以比，
      而那個東西必須跟著版本走——實務上它來自 MLflow（`get_model_version_by_alias("champion")`
      那一版的 `eval_auc`），這裡先簡化成一個 JSON 檔。
    - **`golden_churn.csv` / `golden_stay.csv`**：黃金樣本。
      挑法很關鍵——**用領域規則挑，不是用模型挑**：我們拿「真的流失了，而且 `f2` 很高、`f3` 很低」
      （`f2`、`f3` 是這份資料裡最強的兩個訊號）當「教科書等級的流失客戶」。
      如果用「模型最有把握的那幾筆」來挑，那測試就變成了「模型同意自己」，永遠會過。
    """
    )
    return


@app.cell
def _(COLS, MODELS, PREV, WORK, X_te, X_tr, json, mo, np, pickle, y_te):
    for _name, _m in MODELS.items():
        (WORK / "models" / f"{_name}.pkl").write_bytes(pickle.dumps(_m))

    X_te.assign(label=y_te).to_csv(WORK / "test.csv", index=False)
    (WORK / "baseline.json").write_text(json.dumps(PREV, ensure_ascii=False, indent=2))

    # 方向性測試要用「訓練時看到的分佈」當格點，不能拿測試集現算
    (WORK / "quantiles.json").write_text(
        json.dumps(
            {
                _c: [float(_v) for _v in np.quantile(X_tr[_c], [0.05, 0.25, 0.5, 0.75, 0.95])]
                for _c in ("f2", "f3")
            },
            indent=2,
        )
    )

    # 黃金樣本：領域規則＝真實標籤 ＋ 兩個主訊號都站在同一邊
    _f2_hi, _f2_lo = np.quantile(X_tr["f2"], 0.8), np.quantile(X_tr["f2"], 0.2)
    _f3_hi, _f3_lo = np.quantile(X_tr["f3"], 0.8), np.quantile(X_tr["f3"], 0.2)
    _churn = X_te[(y_te == 1) & (X_te["f2"].values > _f2_hi) & (X_te["f3"].values < _f3_lo)]
    _stay = X_te[(y_te == 0) & (X_te["f2"].values < _f2_lo) & (X_te["f3"].values > _f3_hi)]
    _churn.to_csv(WORK / "golden_churn.csv", index=False)
    _stay.to_csv(WORK / "golden_stay.csv", index=False)
    ARTIFACTS = sorted(_p.name for _p in WORK.iterdir())
    GOLDEN_N = (len(_churn), len(_stay))
    mo.md(
        f"""
    工作資料夾裡現在有：`{"`、`".join(ARTIFACTS)}`（外加 `models/` 三個 `.pkl`），
    欄位共 {len(COLS)} 個。黃金樣本挑到 **{GOLDEN_N[0]} 位典型流失客戶**、
    **{GOLDEN_N[1]} 位典型續約客戶**。
    """
    )
    return ARTIFACTS, GOLDEN_N


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ### `conftest.py`：三個測試檔共用的 fixture

    `conftest.py` 是 pytest 的慣例檔名：放在測試資料夾裡，裡面的 fixture **自動被同資料夾的所有測試檔看見**，
    不用 import。我們把「載入模型」「載入測試集」放進去，三個測試檔就都能直接把 `model`、`X`、`y` 當參數要。

    兩個設計決定值得說明：

    - **`scope="session"`**：這個 fixture 在一次 pytest 執行裡只算一次。
      模型反序列化、讀 CSV 都不便宜，10 條測試各載一次會慢 10 倍。
    - **模型名字從環境變數來**（`MODEL_UNDER_TEST`）：測試檔本身不寫死要測誰。
      CI 上就是這樣做的——同一套測試，換一個環境變數（實務上是換一個 model URI）就能測另一版。
    """
    )
    return


@app.cell
def _(ARTIFACTS, WORK, mo, textwrap):
    _ = ARTIFACTS  # 確保資料檔先寫好、conftest 後寫（cell 執行順序）
    CONFTEST = WORK / "conftest.py"
    CONFTEST.write_text(
        textwrap.dedent('''
        """三個測試檔共用的 fixture。"""
        import os
        import pickle
        from pathlib import Path

        import pandas as pd
        import pytest

        HERE = Path(__file__).parent

        @pytest.fixture(scope="session")
        def model():
            """要被測的那一版模型。CI 上換個環境變數就換一版。"""
            name = os.environ.get("MODEL_UNDER_TEST", "champion")
            return pickle.loads((HERE / "models" / f"{name}.pkl").read_bytes())

        @pytest.fixture(scope="session")
        def data():
            return pd.read_csv(HERE / "test.csv")

        @pytest.fixture(scope="session")
        def X(data):
            return data.drop(columns="label")

        @pytest.fixture(scope="session")
        def y(data):
            return data["label"].to_numpy()
        ''')
    )
    mo.md(f"寫好 `{CONFTEST.name}`（{len(CONFTEST.read_text().splitlines())} 行）。")
    return (CONFTEST,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ### `run_tests()`：在 notebook 裡跑 pytest

    平常你會在終端機打 `pytest`。在 notebook 裡，`pytest.main([...])` 做同一件事，
    回傳的是 **exit code**（0＝全過、1＝有測試失敗）。三個細節：

    - **`contextlib.redirect_stdout`**：pytest 把報告印到 stdout，要接住才能排版顯示。
    - **`-p no:cacheprovider`**：不要在工作資料夾留下 `.pytest_cache`；
      **`-p no:warnings`**：關掉警告摘要（notebook 環境會先匯入一堆套件，
      pytest 會為此發出跟你的測試無關的提醒，蓋掉真正該看的東西）。
    - **清 `sys.modules`**：Python 匯入過的模組會被快取。
      **同一個檔名、改了內容再跑，pytest 會拿到舊的那一份**——實測：把 `test_cache.py`
      從一個必過的測試改成一個必敗的測試，不清快取重跑仍然是 `1 passed`、exit code 0；
      清掉之後才變成 `1 failed`。在 notebook 這種「同一個 process 反覆跑」的環境裡，
      這是最容易讓你懷疑人生的坑。

    另外把 `COLUMNS` 釘成固定值，pytest 的報告寬度才不會隨環境變來變去。
    """
    )
    return


@app.cell
def _(Path, WORK, contextlib, io, os, pytest, sys, time):
    class TestCollector:
        """一個極小的 pytest plugin：把每條測試的結果收起來，之後畫圖與寫進 MLflow 都要用。"""

        def __init__(self):
            self.results = {}

        def pytest_runtest_logreport(self, report):
            if report.when == "call":
                self.results[report.nodeid] = report.outcome

    def run_tests(*args, model="champion"):
        """在 notebook 內跑一次 pytest，回傳（報告文字、exit code、逐條結果、耗時）。"""
        os.environ["MODEL_UNDER_TEST"] = model
        os.environ["COLUMNS"] = "100"
        for _name, _mod in list(sys.modules.items()):  # 清掉上一輪快取的測試模組
            _file = getattr(_mod, "__file__", None)
            if _file and str(WORK) in _file:
                del sys.modules[_name]

        collector = TestCollector()
        buf = io.StringIO()
        t0 = time.time()
        with contextlib.redirect_stdout(buf):
            code = pytest.main(
                [
                    "-q",
                    "-p", "no:cacheprovider",   # 不要留下 .pytest_cache
                    "-p", "no:warnings",        # 關掉警告摘要（marimo 先匯入的套件會產生無關的提醒）
                    "--tb=short",
                    *[str(a) for a in args],
                ],
                plugins=[collector],
            )
        # 只是把冗長的暫存路徑縮掉（相對路徑要先換，否則會被絕對路徑那次吃掉），其餘輸出一字不改
        rel = os.path.relpath(WORK, Path.cwd())
        text = buf.getvalue().replace(rel + "/", "").replace(str(WORK) + "/", "")
        return text, int(code), collector.results, time.time() - t0
    return (run_tests,)


@app.cell
def _(mo):
    def report(out, code, elapsed, note=""):
        """把 pytest 的原始輸出排版成一塊 code block ＋一行結論。"""
        verdict = "✅ 全部通過" if code == 0 else "⛔ 有測試沒過"
        tail = f"　{note}" if note else ""
        return mo.md(
            f"```text\n{out.strip()}\n```\n\n"
            f"**exit code {code}** — {verdict}（0＝全綠，非 0＝有問題），耗時 {elapsed:.2f} 秒{tail}"
        )
    return (report,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 2️⃣ 第一組：合約測試——「介面沒變」

    最基本、也最容易被跳過的一組：**模型的輸入輸出介面**。三條：

    1. **形狀與範圍**：`predict_proba` 要回 `(n, 2)`，每個值在 `[0, 1]`，每列相加等於 1。
       聽起來廢話，但只要有人把模型換成迴歸器、或在後處理裡多做一次正規化，這條就會紅。
    2. **少一欄要炸**：故意丟掉 `f11` 再 `predict`，**期待它拋例外**。
       這是「吵鬧的失敗」比「安靜的錯誤」好——如果模型少一欄還能算出答案，那答案一定是錯的。
    3. **決定性**：同樣的輸入跑兩次，結果必須一模一樣。
       樹模型天生決定性，但只要有人在推論路徑加了取樣、dropout、或忘了固定亂數種子，這條就會紅。

    ### 這跟第 2 課的 signature 是什麼關係？

    `signature` 是 MLflow 在 `log_model` 時**自動記錄**的輸入輸出結構，上線時變成 API 的輸入驗證。
    合約測試跟它有重疊，但角色不同：

    | | signature（第 2 課） | 合約測試（本課） |
    |---|---|---|
    | 誰寫的 | MLflow 自動推論 | 你自己決定 |
    | 管什麼 | 欄位名稱與型別 | 任何你想承諾的介面性質（範圍、決定性、要不要炸） |
    | 什麼時候擋 | 呼叫模型的當下 | **重訓完、還沒註冊之前** |

    一句話：**signature 是自動的合約，測試是你額外的承諾。**

    順帶一提，sklearn 對欄位很嚴格——少一欄、多一欄、順序不同都會拋 `ValueError`，
    但**訊息不一樣**（`yet now missing` / `unseen at fit time` / `must be in the same order`）。
    所以 `pytest.raises` 要加上 `match=`，不然任何一種 `ValueError` 都算它過。
    """
    )
    return


@app.cell
def _(CONFTEST, WORK, mo, textwrap):
    _ = CONFTEST
    F_CONTRACT = WORK / "test_contract.py"
    F_CONTRACT.write_text(
        textwrap.dedent('''
        """合約測試：模型的輸入輸出介面沒有變。"""
        import numpy as np
        import pytest


        def test_output_shape_and_range(model, X):
            p = model.predict_proba(X)
            assert p.shape == (len(X), 2), f"形狀是 {p.shape}，期待 {(len(X), 2)}"
            assert ((p >= 0) & (p <= 1)).all(), "有機率跑出 [0, 1] 之外"
            assert np.allclose(p.sum(axis=1), 1.0), "每列兩個機率相加不等於 1"


        def test_missing_column_raises(model, X):
            """少一欄不可以默默算出答案——要炸，而且要炸在正確的地方。"""
            with pytest.raises(ValueError, match="feature names"):
                model.predict(X.drop(columns="f11"))


        def test_deterministic(model, X):
            first = model.predict_proba(X.head(100))
            second = model.predict_proba(X.head(100))
            assert (first == second).all(), "同樣的輸入跑兩次，結果不一樣"
        ''')
    )
    mo.md(f"寫好 `{F_CONTRACT.name}`：3 條合約測試。")
    return (F_CONTRACT,)


@app.cell
def _(F_CONTRACT, report, run_tests):
    _out, _code, _res, _t = run_tests(F_CONTRACT)
    report(_out, _code, _t, note="這一組跟模型好不好完全無關——它只問「介面還在不在」。")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 3️⃣ 第二組：表現測試——把品質閘寫成測試

    第 5 課的管線裡有一個 `quality_gate`：AUC ≥ 0.95 就放行。那是**一個數字的門檻**。
    這一節把它擴成三條測試，每一條回答一個不同的問題：

    | 測試 | 問的問題 | 門檻 |
    |---|---|---|
    | `test_min_auc` | 夠不夠好？ | AUC ≥ 0.95 |
    | `test_no_regression_vs_baseline` | 有沒有**退步**？ | accuracy ≥ 上一版 − 0.02 |
    | `test_slice_not_much_worse` | 有沒有**某一群人特別慘**？ | 切片 accuracy ≥ 整體 − 0.05 |

    第二條比第一條重要得多。絕對門檻只保證「不會爛到不能用」，
    但真正常見的事故是「這一版比上一版差一點，卻因為還在門檻之上而被放行」——
    連續三次各退 1%，半年後你就換了一個明顯更差的模型，而且每一次都合規。

    第三條是最容易被忽略、也最容易上新聞的一條。整體 accuracy 是一個平均數，
    平均數會把某一群人的災難藏起來。所以要**先實測**：把測試集切成幾群，
    看哪一群跟整體差最多——這份資料實測最慘的是 `f3 > 1` 那 208 位客戶。

    > **切片怎麼挑？** 挑「你會被追究責任」的那些群：不同地區、不同方案、新客戶 vs 老客戶、
    > 資料量最少的那一群。切片測試的門檻通常比整體寬鬆（子群樣本少、波動大），
    > 但**必須有**——沒有它，你永遠不知道自己的平均數是誰在扛。
    """
    )
    return


@app.cell
def _(F_CONTRACT, WORK, mo, textwrap):
    _ = F_CONTRACT
    F_PERF = WORK / "test_performance.py"
    F_PERF.write_text(
        textwrap.dedent('''
        """表現測試：夠好、沒退步、沒有哪一群特別慘。"""
        import json
        from pathlib import Path

        from sklearn.metrics import accuracy_score, roc_auc_score

        HERE = Path(__file__).parent


        def test_min_auc(model, X, y):
            """絕對門檻：低於這條線的模型不准上線。"""
            auc = roc_auc_score(y, model.predict_proba(X)[:, 1])
            assert auc >= 0.95, f"AUC {auc:.4f} 低於上線門檻 0.95"


        def test_no_regression_vs_baseline(model, X, y):
            """相對門檻：跟上一版比，不准退步超過 2 個百分點。"""
            prev = json.loads((HERE / "baseline.json").read_text())
            acc = accuracy_score(y, model.predict(X))
            floor = prev["accuracy"] - 0.02
            assert acc >= floor, (
                f"accuracy {acc:.4f} 比上一版（{prev['model']} {prev['accuracy']:.4f}）"
                f"退步超過 2 個百分點，下限 {floor:.4f}"
            )


        def test_slice_not_much_worse(model, X, y):
            """切片門檻：某一群客戶不可以比整體差太多。"""
            mask = (X["f3"] > 1).to_numpy()
            overall = accuracy_score(y, model.predict(X))
            sliced = accuracy_score(y[mask], model.predict(X[mask]))
            assert sliced >= overall - 0.05, (
                f"切片 f3>1（{mask.sum()} 位客戶）accuracy {sliced:.4f}，"
                f"比整體 {overall:.4f} 低了 {overall - sliced:.4f}"
            )
        ''')
    )
    mo.md(f"寫好 `{F_PERF.name}`：3 條表現測試。")
    return (F_PERF,)


@app.cell
def _(F_PERF, report, run_tests):
    _out, _code, _res, _t = run_tests(F_PERF)
    report(_out, _code, _t, note="champion 三條都過；第 6 節換成壞模型時，這一組會是最先紅的。")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 4️⃣ 第三組：行為測試——CheckList 的三件事

    2020 年 Ribeiro 等人的論文《Beyond Accuracy: Behavioral Testing of NLP Models with CheckList》
    提出一組到今天還在用的分類。原本講的是 NLP，但換個主角完全成立：

    | 類型 | 白話 | 這份資料的例子 |
    |---|---|---|
    | **不變性**（invariance） | 改了**不該影響結果**的東西，預測就不該變 | 每個特徵加一點量測雜訊，預測要幾乎不動 |
    | **方向性**（directional） | 改了**該往某方向影響**的東西，預測就要往那個方向動 | `f2` 調高 → 流失機率要上升；`f3` 調高 → 要下降 |
    | **最低功能**（minimum functionality） | 幾筆「連新人都不會答錯」的樣本，一定要對 | 教科書等級的流失客戶，機率不能低於 0.7 |

    ### 不變性：怎麼定義「不該影響結果」

    這裡用 `sigma = 0.01` 的高斯雜訊——大約是量測誤差的等級，
    小到人類會說「這根本是同一位客戶」。門檻設 98% 的預測不變。

    **但這條測試有一個陷阱**：一個什麼都不學的模型，不變性會滿分。
    實測 `shallow`（深度 1）的一致率是 **1.0000**，比 champion 的 0.9980 還「穩」——
    因為它幾乎對所有人都給同一個答案。所以不變性**不能單獨看**，
    它只有跟表現測試放在一起才有意義。

    ### 方向性：先實測，再寫斷言

    「`f2` 調高，流失機率應該上升」這句話從哪來？**不能用猜的。**
    做法是畫**部分依賴**：把整欄 `f2` 換成訓練分佈的 P05/P25/P50/P75/P95，
    看平均預測機率怎麼走。下圖是三個模型的實測曲線。
    """
    )
    return


@app.cell
def _(MODELS, X_te, X_tr, np, plt):
    _grid_q = [0.05, 0.25, 0.5, 0.75, 0.95]
    _fig, _axes = plt.subplots(2, 1, figsize=(6.2, 5.8), sharex=False)
    _styles = {"champion": ("#4C72B0", "-", "o"), "shallow": ("#DD8452", "--", "s"),
               "shuffled": ("#C44E52", ":", "^")}
    PD_CURVES = {}
    for _ax, _col, _want in zip(_axes, ("f2", "f3"), ("expect UP", "expect DOWN")):
        _qs = np.quantile(X_tr[_col], _grid_q)
        for _name, _m in MODELS.items():
            _curve = [float(_m.predict_proba(X_te.assign(**{_col: _q})[X_te.columns])[:, 1].mean())
                      for _q in _qs]
            PD_CURVES[(_col, _name)] = _curve
            _c, _ls, _mk = _styles[_name]
            _ax.plot(_qs, _curve, _ls, marker=_mk, color=_c, label=_name, linewidth=2, markersize=5)
        _ax.set_title(f"partial dependence of {_col}  ({_want})", fontsize=11)
        _ax.set_xlabel(f"{_col} value (P05 - P95 of training data)", fontsize=9)
        _ax.set_ylabel("mean P(churn)", fontsize=9)
        _ax.set_ylim(0, 1)
        _ax.grid(alpha=0.25)
        _ax.legend(fontsize=8)
    _fig.tight_layout()
    _fig
    return (PD_CURVES,)


@app.cell(hide_code=True)
def _(PD_CURVES, mo):
    mo.md(
        f"""
    上圖 `f2`：champion 從 {PD_CURVES[("f2", "champion")][0]:.3f} 一路爬到
    {PD_CURVES[("f2", "champion")][-1]:.3f}（**單調上升、總共動了
    {PD_CURVES[("f2", "champion")][-1] - PD_CURVES[("f2", "champion")][0]:+.3f}**）；
    下圖 `f3`：champion 從 {PD_CURVES[("f3", "champion")][0]:.3f} 掉到
    {PD_CURVES[("f3", "champion")][-1]:.3f}。方向清楚、幅度夠大——**這才可以寫成斷言**。

    再看兩個壞模型：`shallow` 的兩條曲線幾乎是平的（`f2` 只動了
    {PD_CURVES[("f2", "shallow")][-1] - PD_CURVES[("f2", "shallow")][0]:+.3f}），
    `shuffled` 則是上上下下的鋸齒。所以方向性測試要寫**兩個**斷言：
    **① 方向不能中途反轉**（抓 `shuffled` 這種亂走的），
    **② 總幅度要夠大**（抓 `shallow` 這種「方向沒錯但根本沒反應」的）。
    只寫其中一個都會漏。

    ### 最低功能：黃金樣本

    最後一條最像人工驗收：挑幾筆「一定要對」的樣本，每次重訓都拿出來問一次。
    這裡用第 1 節挑好的樣本，門檻是**典型流失客戶的機率不得低於 0.70、
    典型續約客戶不得高於 0.30**——注意不是「分類對就好」：
    一個把所有人都猜 0.51 的模型分類全對，但它其實什麼都不知道。
    """
    )
    return


@app.cell
def _(F_PERF, WORK, mo, textwrap):
    _ = F_PERF
    F_BEHAV = WORK / "test_behavior.py"
    F_BEHAV.write_text(
        textwrap.dedent('''
        """行為測試：不變性、方向性、最低功能（CheckList 三件套）。"""
        import json
        from pathlib import Path

        import numpy as np
        import pandas as pd
        import pytest

        HERE = Path(__file__).parent


        def test_invariance_to_noise(model, X):
            """加上量測等級的雜訊，預測不該翻掉。"""
            base = model.predict(X)
            noise = np.random.default_rng(0).normal(0, 0.01, X.shape)
            agree = float((base == model.predict(X + noise)).mean())
            assert agree >= 0.98, f"加了 sigma=0.01 的雜訊後只有 {agree:.4f} 的預測沒變"


        @pytest.mark.parametrize("col,sign", [("f2", +1), ("f3", -1)])
        def test_directional(model, X, col, sign):
            """f2 調高 → 流失機率上升；f3 調高 → 下降。方向與幅度都要對。"""
            grid = json.loads((HERE / "quantiles.json").read_text())[col]
            curve = np.array(
                [model.predict_proba(X.assign(**{col: q})[X.columns])[:, 1].mean() for q in grid]
            )
            monotone = bool((np.diff(curve) * sign >= 0).all())
            assert monotone, f"{col} 往預期方向動時，機率中途反轉：{curve.round(3)}"
            move = float((curve[-1] - curve[0]) * sign)
            assert move >= 0.20, f"{col} 從 P05 拉到 P95，流失機率只動了 {move:.3f}"


        def test_golden_samples(model):
            """幾筆教科書等級的樣本，一定要答對，而且要有把握。"""
            churn = pd.read_csv(HERE / "golden_churn.csv")
            stay = pd.read_csv(HERE / "golden_stay.csv")
            worst_churn = float(model.predict_proba(churn)[:, 1].min())
            best_stay = float(model.predict_proba(stay)[:, 1].max())
            assert worst_churn >= 0.70, (
                f"{len(churn)} 位典型流失客戶裡，最低機率只有 {worst_churn:.4f}"
            )
            assert best_stay <= 0.30, (
                f"{len(stay)} 位典型續約客戶裡，最高機率高到 {best_stay:.4f}"
            )
        ''')
    )
    mo.md(f"寫好 `{F_BEHAV.name}`：3 個測試函式、4 條測試（方向性 `parametrize` 成兩條）。")
    return (F_BEHAV,)


@app.cell
def _(F_BEHAV, report, run_tests):
    _out, _code, _res, _t = run_tests(F_BEHAV)
    report(_out, _code, _t, note="注意 pytest 把 parametrize 展開成 test_directional[f2-1] 與 [f3--1] 兩條。")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 5️⃣ 全部一起跑：10 條測試、一個 exit code

    三個檔案、10 條測試。這就是每次重訓之後要跑的東西——
    **一個指令、一個 exit code、一份可以貼進 PR 的報告**。

    在終端機上等價於：

    ```bash
    cd /tmp/ml-testing-lesson
    MODEL_UNDER_TEST=champion pytest -q --tb=short
    ```
    """
    )
    return


@app.cell
def _(F_BEHAV, F_CONTRACT, F_PERF):
    SUITE = [F_CONTRACT, F_PERF, F_BEHAV]
    return (SUITE,)


@app.cell
def _(SUITE, report, run_tests):
    _out, _code, _res, _t = run_tests(*SUITE)
    report(_out, _code, _t, note="10 條全綠，exit code 0——這一版可以進 Registry。")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 6️⃣ 讓它失敗：同一套測試，兩個壞模型

    綠燈很好看，但**一套從來沒有紅過的測試，你不知道它會不會紅**。
    現在把 `MODEL_UNDER_TEST` 換成兩個故意做壞的模型，看看紅的是哪幾條——
    重點不是「幾條紅」，是**紅的是不同的幾條**。

    - **`shallow`**：深度 1 的樹。它是個「有點笨但正常」的模型——AUC 0.89，
      該有的行為都有，只是弱。
    - **`shuffled`**：訓練前把標籤打亂。它是個「看起來正常但完全沒學到東西」的模型——
      這是實務上最可怕的一種故障（特徵與標籤接錯、join 錯 key、時間對齊錯）。
    """
    )
    return


@app.cell
def _(SUITE, report, run_tests):
    _out, _code, _res, _t = run_tests(*SUITE, model="shallow")
    RES_SHALLOW = _res
    report(_out, _code, _t, note="表現三條全紅、方向性兩條全紅、黃金樣本紅——但不變性是綠的。")
    return (RES_SHALLOW,)


@app.cell
def _(SUITE, report, run_tests):
    _out, _code, _res, _t = run_tests(*SUITE, model="shuffled")
    RES_SHUFFLED = _res
    report(_out, _code, _t, note="這一次不變性紅了，切片測試卻是綠的——原因在下面。")
    return (RES_SHUFFLED,)


@app.cell
def _(RES_SHALLOW, RES_SHUFFLED, SUITE, np, plt, run_tests):
    _out0, _code0, _res_champ, _t0 = run_tests(*SUITE)
    ALL_RESULTS = {"champion": _res_champ, "shallow": RES_SHALLOW, "shuffled": RES_SHUFFLED}
    _names = [k.split("::")[-1] for k in _res_champ]
    _grid = np.array(
        [[1 if ALL_RESULTS[_m][_k] == "passed" else 0 for _k in _res_champ]
         for _m in ("champion", "shallow", "shuffled")]
    )
    _fig2, _ax2 = plt.subplots(figsize=(6.4, 4.4))
    _ax2.imshow(_grid.T, cmap="RdYlGn", vmin=0, vmax=1, aspect="auto")
    _ax2.set_xticks(range(3))
    _ax2.set_xticklabels(["champion", "shallow", "shuffled"], fontsize=10)
    _ax2.set_yticks(range(len(_names)))
    _ax2.set_yticklabels(_names, fontsize=8.5, family="monospace")
    for _i in range(_grid.shape[0]):
        for _j in range(_grid.shape[1]):
            _ax2.text(_i, _j, "PASS" if _grid[_i, _j] else "FAIL",
                      ha="center", va="center", fontsize=8, fontweight="bold")
    _ax2.set_title("same 10 tests, three models", fontsize=11)
    _fig2.tight_layout()
    _fig2
    return (ALL_RESULTS,)


@app.cell(hide_code=True)
def _(ALL_RESULTS, mo):
    _n_pass = {_m: sum(_v == "passed" for _v in _r.values()) for _m, _r in ALL_RESULTS.items()}
    mo.md(
        f"""
    通過數：champion **{_n_pass["champion"]}/10**、shallow **{_n_pass["shallow"]}/10**、
    shuffled **{_n_pass["shuffled"]}/10**。兩個壞模型都是 6 條紅，但**紅的不是同一組**：

    | 測試 | shallow | shuffled | 為什麼 |
    |---|---|---|---|
    | 三條合約測試 | 綠 | 綠 | **合約測試抓不到爛模型**——介面對不代表答案對 |
    | `test_slice_not_much_worse` | 🔴 紅 | 綠 | shuffled 對每一群都一樣爛，**切片跟整體沒有落差** |
    | `test_invariance_to_noise` | 綠 | 🔴 紅 | shallow 幾乎不隨輸入變（1.0000），shuffled 的決策邊界是噪音（0.9740） |
    | `test_directional` ×2 | 🔴 紅（幅度不足） | 🔴 紅（中途反轉） | 同一條測試、**兩種不同的失敗訊息** |
    | `test_golden_samples` | 🔴 紅 | 🔴 紅 | 兩個都對「教科書客戶」沒有把握 |

    這張表就是本課最重要的一句話：**沒有任何一種測試能單獨守住模型。**
    合約測試放過了兩個垃圾模型；切片測試放過了 shuffled；不變性測試放過了 shallow，
    而且還給了它滿分。要靠**一整組彼此互補的測試**，才會在不同的故障模式下各自亮紅燈。

    這也是為什麼「測試就是把 code review 的直覺自動化」——
    資深同事看模型時腦子裡跑的就是這幾條：「這數字比上一版好嗎」「哪一群比較差」
    「把這個特徵推高會怎樣」「我隨手挑幾個案例看看」。
    寫成 pytest 之後，這些直覺就不再依賴那位同事今天有沒有空。
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 7️⃣ 放進流程：exit code 就是那道閘門

    測試寫完只是一半。它要**擋得住東西**，才算上線。

    ### exit code 的意思（實測）

    | code | 意思 | 什麼時候會出現 |
    |---|---|---|
    | `0` | 全部通過 | 正常 |
    | `1` | 有測試失敗 | 你希望它擋下來的那種 |
    | `2` | 收集階段就出錯、直接中斷 | `parametrize` 的參數對不上、import 失敗 |
    | `5` | **一條測試都沒跑到** | 檔名沒有 `test_` 前綴、`-k` 打錯字 |

    `5` 是最危險的一個：CI 腳本如果只寫 `if [ $? -eq 1 ]` 判斷失敗，
    那「一條都沒跑」會被當成成功放行。**判準要寫 `-ne 0`。**

    ### 選測試：`-k` 與 mark

    ```bash
    pytest -q -k "directional or golden"    # 名字比對，選幾條來跑
    pytest -q -m "not slow"                 # 依 mark 過濾，跳過慢的
    pytest -q --collect-only                # 只列出會跑哪些，不執行
    pytest -q --tb=line                     # 每個失敗只印一行（CI log 最好讀）
    ```

    慢的測試（例如「用完整資料重訓一次再比較」）掛上 `@pytest.mark.slow`，
    平常 PR 只跑快的、每晚跑全部。mark 要在 `pytest.ini` 註冊，
    不然只會得到一行 `PytestUnknownMarkWarning: Unknown pytest.mark.slwo - is this a typo?`
    ——而且**測試照跑、照過**，你不會發現自己打錯字。
    """
    )
    return


@app.cell
def _(SUITE, report, run_tests):
    _out, _code, _res, _t = run_tests("-k", "directional or golden", *SUITE)
    report(_out, _code, _t, note="-k 選了 3 條、跳過 7 條；沒選到的算 deselected，不是失敗。")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ### 接進 CI：GitHub Actions

    這段不用執行，直接放進 `.github/workflows/model-tests.yml` 就會動。
    重點在最後兩步的順序——**測試綠了才准註冊**：

    ```yaml
    name: model-tests
    on: [push, pull_request]

    jobs:
      test:
        runs-on: ubuntu-latest
        steps:
          - uses: actions/checkout@v4
          - uses: astral-sh/setup-uv@v5
          - name: 跑模型測試（慢的留給夜間排程）
            env:
              MODEL_UNDER_TEST: candidate
            run: uv run pytest tests/ -q --tb=short -m "not slow"
          - name: 只有全綠才註冊並移動 champion alias
            run: uv run python scripts/promote.py
    ```

    GitHub Actions 的預設行為就是「前一步非 0 就中斷」，所以不用自己寫判斷——
    `pytest` 的 exit code 直接變成閘門。這跟第 5 課 Dagster 的
    `@asset_check(blocking=True)` 是同一件事的兩種寫法：
    **一個在管線裡擋、一個在 CI 裡擋，通常兩個都要有。**

    ### 測試結果寫進 MLflow

    測試通過與否，跟 AUC 一樣是這一版模型的性質，應該跟著 run 一起留下來。
    下面把「通過幾條、失敗清單、exit code」寫進 MLflow：
    """
    )
    return


@app.cell
def _(ALL_RESULTS, SUITE, WORK, mo, run_tests):
    import mlflow

    mlflow.set_tracking_uri(f"sqlite:///{WORK}/mlflow.db")
    _client = mlflow.MlflowClient()
    _exp = mlflow.get_experiment_by_name("ml-testing")   # 重跑這一格也不會炸
    _exp_id = (
        _exp.experiment_id
        if _exp
        else mlflow.create_experiment(
            "ml-testing", artifact_location=(WORK / "mlartifacts").as_uri()
        )
    )
    MLFLOW_RUNS = {}
    for _model in ("champion", "shallow", "shuffled"):
        _out, _code, _res, _t = run_tests(*SUITE, model=_model)
        _short = {_k.split("::")[-1]: _v for _k, _v in _res.items()}
        _failed = sorted(_k for _k, _v in _short.items() if _v != "passed")
        with mlflow.start_run(experiment_id=_exp_id, run_name=f"tests-{_model}") as _run:
            mlflow.log_metric("tests_passed", sum(_v == "passed" for _v in _short.values()))
            mlflow.log_metric("tests_failed", len(_failed))
            mlflow.set_tag("tests_green", str(_code == 0))
            mlflow.log_dict(
                {"model": _model, "exit_code": _code, "failed": _failed, "results": _short},
                "tests/summary.json",
            )
            MLFLOW_RUNS[_model] = _run.info.run_id

    _rows = "\n".join(
        f"| `{_m}` | {_client.get_run(_r).data.metrics['tests_passed']:.0f} | "
        f"{_client.get_run(_r).data.metrics['tests_failed']:.0f} | "
        f"`{_client.get_run(_r).data.tags['tests_green']}` |"
        for _m, _r in MLFLOW_RUNS.items()
    )
    mo.md(
        f"""
    | run | tests_passed | tests_failed | tag `tests_green` |
    |---|---|---|---|
    {_rows}

    三個 run 都留在 `mlflow.db` 裡。之後任何人問「上線那一版當時測試過了嗎」，
    答案在 run 上，不在誰的記憶裡。
    """
    )
    return MLFLOW_RUNS, mlflow


@app.cell
def _(MLFLOW_RUNS, json, mlflow, mo):
    _loaded = mlflow.artifacts.load_dict(f"runs:/{MLFLOW_RUNS['shallow']}/tests/summary.json")
    _pretty = json.dumps(_loaded, ensure_ascii=False, indent=2)
    mo.md(
        f"""
    把 `shallow` 那一次的失敗清單讀回來（`mlflow.artifacts.load_dict`）：

    ```json
{_pretty}
    ```

    這就是「模型的驗收紀錄」——比一行 `AUC: 0.8903` 有用得多，因為它說得出**哪裡不行**。
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 8️⃣ 互動：挑一個模型、挑要跑哪幾類

    這是把前面七節縮成一個面板：選一個模型、勾要跑的測試類別，按下去真的跑一次 pytest。
    每次注意三件事：

    1. **哪幾條紅**——不同的壞法會亮不同的燈
    2. **`E AssertionError:` 那一行**——那是你半夜第一眼會看到的字串，寫得好不好差很多
    3. **底部的 exit code 與判決**——這一版能不能進 Registry，就看這個數字
    """
    )
    return


@app.cell
def _(mo):
    pick_model = mo.ui.dropdown(
        options={
            "champion（正常，深度 8）": "champion",
            "shallow（深度只有 1）": "shallow",
            "shuffled（標籤被打亂）": "shuffled",
        },
        value="shallow（深度只有 1）",
        label="要測哪一版",
    )
    pick_groups = mo.ui.multiselect(
        options=["合約", "表現", "行為"],
        value=["合約", "表現", "行為"],
        label="跑哪幾類測試",
    )
    run_it = mo.ui.run_button(label="跑一次 pytest")
    mo.hstack([pick_model, pick_groups, run_it], wrap=True, justify="start")
    return pick_groups, pick_model, run_it


@app.cell
def _(F_BEHAV, F_CONTRACT, F_PERF, mo, pick_groups, pick_model, run_it, run_tests):
    mo.stop(not run_it.value, mo.md("*挑好模型與類別，按「跑一次 pytest」。*"))

    _files = {"合約": F_CONTRACT, "表現": F_PERF, "行為": F_BEHAV}
    _chosen = [_files[_g] for _g in ("合約", "表現", "行為") if _g in pick_groups.value]
    if not _chosen:
        _panel = mo.callout(mo.md("**一類都沒選**——pytest 沒有東西可跑。"), kind="warn")
    else:
        _out, _code, _res, _t = run_tests(*_chosen, model=pick_model.value)
        _lines = []
        for _k, _v in _res.items():
            _file, _name = _k.split("::")
            _icon = "✅" if _v == "passed" else "❌"
            _lines.append(f"| {_icon} | `{_name}` | `{_file}` |")
        _table = "| | 測試 | 檔案 |\n|---|---|---|\n" + "\n".join(_lines)
        _n_fail = sum(_v != "passed" for _v in _res.values())
        _verdict = mo.callout(
            mo.md(
                f"**exit code {_code}** — "
                + (
                    "✅ 全部通過，這一版可以註冊並晉升 champion。"
                    if _code == 0
                    else f"⛔ {_n_fail} 條沒過，管線在這裡停住，**不會註冊**。"
                )
            ),
            kind="success" if _code == 0 else "danger",
        )
        _panel = mo.vstack(
            [
                _verdict,
                mo.md(_table),
                mo.md(f"pytest 的原始輸出（{_t:.2f} 秒）："),
                mo.md(f"```text\n{_out.strip()}\n```"),
            ]
        )
    _panel
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 🏆 延伸挑戰

    1. **LEVEL 1**：加一條**校準測試**——模型的平均預測機率，跟實際的正例比率不能差超過 0.05。
       （提示：`model.predict_proba(X)[:, 1].mean()` 對上 `y.mean()`。）
       寫完先對 champion 跑一次確認會過，再對另外兩個模型跑跑看——
       想一想：這條測試分辨得出好壞模型嗎？為什麼？
    2. **LEVEL 2**：把 `test_slice_not_much_worse` 改成 `parametrize` 三個切片
       （`f1 > 1`、`f0 < -1`、`f3 > 1`），讓報告能一眼看出**是哪一群客戶出事**。
       跑 champion 應該三條全綠；跑 `shallow` 應該只有一條紅。
    3. **LEVEL 3**：用 `hypothesis` 寫一條**屬性測試**——不是你挑輸入，是讓它在
       訓練資料的值域內隨機生成幾百筆客戶，每一筆都要滿足「機率在 `[0, 1]`、兩個機率相加為 1」。
       *怎麼驗證自己做對了*：它應該在 2 秒內跑完幾百個例子並通過；
       如果紅了，先讀 hypothesis 印出的 `Falsifying example`——它會把**最小的**反例縮給你看。

    先自己試，卡住再展開下面的提示與參考解答。
    帶得走：下載本檔後 `uvx marimo edit --sandbox 檔名.py`
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
    加進 `test_performance.py`：

    ```python
    def test_calibration(model, X, y):
        # 平均預測機率要貼近實際的正例比率
        mean_pred = float(model.predict_proba(X)[:, 1].mean())
        actual = float(y.mean())
        assert abs(mean_pred - actual) <= 0.05, (
            f"平均預測機率 {mean_pred:.4f}，實際正例比率 {actual:.4f}，差 {abs(mean_pred - actual):.4f}"
        )
    ```

    實測（測試集實際正例比率 0.5280）：

    | 模型 | 平均預測機率 | 差距 | 結果 |
    |---|---|---|---|
    | champion | 0.5070 | 0.0210 | ✅ 過 |
    | shallow | 0.4925 | 0.0355 | ✅ 過 |
    | shuffled | 0.4914 | 0.0366 | ✅ 過 |

    **三個都過**——這就是這題真正要你看到的事。`shuffled` 什麼都沒學到，
    但它的平均機率照樣接近 0.5，而這份資料的正例比率剛好也接近 0.5。

    校準測的是「**機率這個數字能不能當數字用**」（說 0.7 的那群人，是不是真的有七成流失），
    跟「排序能力好不好」（AUC）是兩個獨立的軸。一個模型可以排序很準但機率全部偏高，
    也可以像 `shuffled` 這樣機率平均值很誠實、但完全沒有鑑別力。

    **所以校準測試不能取代表現測試，反過來也不行。**
    要更嚴格的版本，就不要只比整體平均，改成分箱比對（把預測機率切成 10 段，
    每一段的平均預測值 vs 該段的實際比率）——那就是校準曲線，`shuffled` 會立刻現形。
    """
            ),
            "💡 LEVEL 2 參考解答": mo.md(
                r"""
    ```python
    import pytest

    SLICES = {
        "f1>1": lambda X: (X["f1"] > 1).to_numpy(),
        "f0<-1": lambda X: (X["f0"] < -1).to_numpy(),
        "f3>1": lambda X: (X["f3"] > 1).to_numpy(),
    }


    @pytest.mark.parametrize("slice_name", list(SLICES))
    def test_slice_not_much_worse(model, X, y, slice_name):
        mask = SLICES[slice_name](X)
        overall = accuracy_score(y, model.predict(X))
        sliced = accuracy_score(y[mask], model.predict(X[mask]))
        assert sliced >= overall - 0.05, (
            f"切片 {slice_name}（{mask.sum()} 位客戶）accuracy {sliced:.4f}，"
            f"比整體 {overall:.4f} 低了 {overall - sliced:.4f}"
        )
    ```

    實測結果（整體 accuracy：champion 0.9160、shallow 0.8260）：

    | 切片 | 客戶數 | champion | shallow |
    |---|---|---|---|
    | `f1>1` | 258 | 0.8837（差 0.0323）✅ | 0.7868（差 0.0392）✅ |
    | `f0<-1` | 270 | 0.9000（差 0.0160）✅ | 0.7889（差 0.0371）✅ |
    | `f3>1` | 208 | 0.9038（差 0.0122）✅ | 0.7452（差 0.0808）❌ |

    報告會長成 `test_slice_not_much_worse[f3>1] FAILED`——**測試名字直接說出是哪一群客戶**，
    這正是 `parametrize` 比「在一條測試裡寫迴圈」好的地方：
    迴圈版只要第一個切片就 `assert` 失敗，後面兩個根本不會被檢查，你也不知道到底幾群有問題。

    順帶一個 `parametrize` 的坑（實測）：參數清單裡如果混進一個字串
    （`[("f2", +1), ("f3", -1), "f9"]`），pytest **不會報錯**——
    它會把 `"f9"` 當成序列拆開成 `col='f'`、`sign='9'`，然後給你一條莫名其妙的
    `test_directional[f-9]`。少接一個參數才會直接中斷：
    `In test_x.py::test_directional: function uses no argument 'sign'`（exit code 2）。
    """
            ),
            "💡 LEVEL 3 提示": mo.md(
                r"""
    方向（新增 `test_property.py`）：

    ```python
    import json, pickle
    from pathlib import Path

    import pandas as pd
    from hypothesis import given, settings, strategies as st

    HERE = Path(__file__).parent
    MODEL = pickle.loads((HERE / "models" / "champion.pkl").read_bytes())
    BOUNDS = json.loads((HERE / "bounds.json").read_text())     # 你要先存訓練資料的 min/max
    COLS = list(BOUNDS["lo"])

    row = st.fixed_dictionaries(
        {c: st.floats(min_value=BOUNDS["lo"][c], max_value=BOUNDS["hi"][c], allow_nan=False)
         for c in COLS}
    )


    @settings(max_examples=200, deadline=None)
    @given(r=row)
    def test_proba_always_valid(r):
        p = MODEL.predict_proba(pd.DataFrame([r])[COLS])[0]      # ← 注意 [COLS]
        assert p.shape == (2,)
        assert 0.0 <= p[1] <= 1.0
        assert abs(p.sum() - 1.0) < 1e-9
    ```

    **怎麼驗證自己做對了**：`200` 個例子應該在 **2 秒內**跑完並通過
    （實測 max_examples=50 約 1.0 秒、200 約 1.8 秒）。

    **而這題真正的收穫，是把 `[COLS]` 拿掉再跑一次。**實測它會在 0.2 秒內就紅：

    ```text
    Falsifying example: test_proba_always_valid(
        r={'f0': 0.0, 'f1': 0.0, ..., 'f9': 0.0, 'f11': 0.0, 'f10': 0.0},
    )
    ValueError: The feature names should match those that were passed during fit.
    Feature names must be in the same order as they were in fit.
    ```

    看那個縮到最小的反例：所有值都是 `0.0`（hypothesis 把數值縮到最簡），
    唯一「不簡單」的地方是 **`f11` 排在 `f10` 前面**——它精準地指出了唯一的病因。
    `st.fixed_dictionaries` 產生的 dict 鍵順序不保證，`pd.DataFrame([r])` 就照那個順序建欄位，
    而 sklearn 對欄位順序是**嚴格**的。

    這就是屬性測試的價值：你寫的是「**性質**」（機率永遠合法），
    它去找反例；而它找到的第一個問題，往往不是你原本想測的那個。

    進階：把 `min_value` / `max_value` 拿掉（允許極端值與 `inf`），看看模型在
    訓練分佈外會發生什麼——然後決定那是「模型的 bug」還是「呼叫端該擋的輸入」。
    這個決定本身就是一份合約。
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

    1. **一個 AUC 不是驗收**：它測不到雜訊敏感度、子群落差、與常識相反的關係、介面破損。
    2. **模型測試分三組，缺一不可**——合約（介面沒變）、表現（夠好、沒退步、沒有哪群特別慘）、
       行為（不變性／方向性／最低功能）。實測證明：任何一組單獨都放過了垃圾模型。
    3. **門檻要先實測再寫**：方向性看部分依賴曲線、切片先找出真的有落差的那一群、
       黃金樣本用領域規則挑（不要用模型自己挑，那只是讓它同意自己）。
    4. **斷言訊息就是事故當下的第一句話**：`assert auc >= 0.95` 只會印一個數字，
       `assert auc >= 0.95, f"AUC {auc:.4f} 低於上線門檻 0.95"` 才是給人看的。
    5. **exit code 就是閘門**：`0` 過、`1` 有失敗、`2` 收集就爆、`5` 一條都沒跑到。
       CI 判準寫 `-ne 0`，不然「一條都沒跑」會被當成成功。
    6. **測試結果跟著 run 走**（`log_dict` 進 MLflow）：半年後有人問「上線那版測試過了嗎」，
       答案要在 Registry 裡，不在誰的記憶裡。

    這是 MLOps 補充系列的最後一堂。回頭看整條線：
    第 1–2 課把訓練變成有紀錄、有版本的東西；第 3–5 課把它自動化並加上品質閘；
    補充系列則各自補上一塊——上線、監控、調參、資料合約、追蹤、特徵、資料版本，
    以及這一課的**模型驗收**。它們合起來就是一句話：
    **讓「這個模型可以上線」變成一件有人能檢查、機器能重跑的事。**
    """
    )
    return


if __name__ == "__main__":
    app.run()
