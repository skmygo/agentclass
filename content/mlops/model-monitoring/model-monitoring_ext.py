# 模型監控：資料漂移、預測漂移，與什麼時候該重訓（MLOps 系列補充 B · 07）
# 不需要 GPU——molab 免費 CPU 環境即可全程執行（全部在本機檔案系統，不連任何伺服器）。
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "marimo",
#     "evidently>=0.7",
#     "dagster>=1.10",
#     "mlflow>=3.0",
#     "scikit-learn",
#     "pandas",
#     "numpy",
#     "scipy",
#     "matplotlib",
#     "tabulate",
# ]
# ///
import marimo

__generated_with = "0.23.16"
app = marimo.App(width="medium", app_title="模型監控：資料漂移、預測漂移與什麼時候該重訓")


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    # 🚨 模型監控：資料漂移、預測漂移，與什麼時候該重訓

    ## 模型上線後最危險的事，不是壞掉

    壞掉其實是好消息：服務會噴 500、警報會響、有人會被叫起來。真正危險的是**它還在回答，
    只是答得越來越爛**——沒有例外、沒有紅燈、儀表板一片綠，準確率卻從 0.92 一路滑到 0.86，
    而你要等到季末業務單位抱怨「名單怎麼越來越不準」才知道。

    上一課你把模型變成了一個會回話的 API。這一課處理的是**它開始說謊之後**的事。

    ### 三種漂移，用同一份資料講清楚

    | 漂移 | 變的是什麼 | 什麼時候看得到 |
    | --- | --- | --- |
    | **資料漂移**（data / covariate drift） | 輸入 `X` 的分佈變了 | **馬上**——只要有輸入就算得出來 |
    | **預測漂移**（prediction drift） | 輸出的機率分佈變了 | **馬上**——只要模型有在跑就算得出來 |
    | **概念漂移**（concept drift） | 輸入與標籤的關係 `P(y\|X)` 變了 | **要等標籤**——可能是幾週後 |

    前兩種是**症狀**（免費、即時、不需要標籤），第三種是**病因**（要等，而且常常等很久）。
    監控的全部藝術就在這句話裡：**用看得到的症狀，去猜看不到的病因，而且要在損失擴大之前決定要不要重訓。**

    這一課的前導課（系列第 00 課「為什麼需要 MLOps」）用模擬曲線給你看過那條下滑的準確率；
    這一課是它的**工具版**：同一件事，換成你在正式環境裡真的會用的指標、報告與自動化。

    ## 這份 notebook 帶你做完

    1. **0️⃣ 準備**：同一份客戶流失資料、同一個 RandomForest champion，再刻意造一份「漂移過的生產資料」
    2. **1️⃣ 自己算 PSI**：分箱、公式、0.1 / 0.25 門檻是哪來的，以及**沒漂移時的雜訊底線長什麼樣**
    3. **2️⃣ KS 檢定**：p 值到底在說什麼，為什麼大樣本下它會一直對你尖叫
    4. **3️⃣ 預測漂移**：沒有標籤也能監控；標籤回來之後才看得到的那個數字
    5. **4️⃣ Evidently**：熱門開源工具三行出報告，以及它的預設門檻會怎麼騙你
    6. **5️⃣ 從分數到決策**：門檻 ＋ 連續 N 次 ＋ 人工確認，做成一個回傳 `ok / watch / retrain` 的函式
    7. **6️⃣ 接回管線**：監控結果變成 Dagster 的資產檢查（WARN 不擋、ERROR 擋）與觸發重訓的 sensor
    8. **7️⃣ 線上服務要記什麼**：延遲、錯誤率、輸入摘要——真的量一次
    9. **8️⃣ 互動**：拉桿決定漂移多嚴重，即時看指標與決策怎麼變
    10. **🏆 三級挑戰**（附折疊解答）

    全部在你自己的執行環境裡跑，**不連任何伺服器、不需要 GPU**：資料是合成的，
    MLflow 的帳本是一個 SQLite 檔，Dagster 的帳本是一個暫存資料夾。
    從第一格往下全部執行即可（首次安裝套件約 1–2 分鐘，整份跑完約 1–2 分鐘）。
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

    import dagster as dg
    import marimo as mo
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import mlflow
    import numpy as np
    import pandas as pd
    from scipy import stats
    from sklearn.datasets import make_classification
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.metrics import roc_auc_score
    from sklearn.model_selection import train_test_split

    warnings.filterwarnings("ignore")
    logging.getLogger("mlflow").setLevel(logging.ERROR)

    # Dagster 每一步都會印日誌（正式部署時那些日誌會進 UI）；notebook 裡關掉，只留我們自己排版的輸出
    QUIET = {"loggers": {"console": {"config": {"log_level": "CRITICAL"}}}}

    # 這份 notebook 的工作目錄：MLflow 的帳本與 Evidently 的報告都放這裡，開頭清乾淨，重跑數字才一致
    WORK = Path(tempfile.gettempdir()) / "model-monitoring"
    shutil.rmtree(WORK, ignore_errors=True)
    WORK.mkdir(parents=True, exist_ok=True)

    # 全課共用的配色（教學頁與下面每張圖都用同一組）
    C_REF, C_CUR, C_OK, C_ALARM = "#4C72B0", "#DD8452", "#55A868", "#C44E52"

    # 兩個門檻，全課只在這裡定義一次（第 5️⃣ 節會討論它們憑什麼是這兩個數字）
    WATCH, ALARM = 0.10, 0.25
    return (
        ALARM,
        C_ALARM,
        C_CUR,
        C_OK,
        C_REF,
        QUIET,
        RandomForestClassifier,
        WATCH,
        WORK,
        dg,
        make_classification,
        mlflow,
        mo,
        np,
        pd,
        plt,
        roc_auc_score,
        stats,
        time,
        train_test_split,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 0️⃣ 準備：一個上線中的模型，和一批「怪怪的」生產資料

    沿用整個系列的素材：2000 筆合成的客戶流失資料、12 個特徵 `f0`–`f11`，
    切成 1500 筆訓練 / 500 筆測試，模型是整個系列共用的那個 RandomForest champion
    （100 棵樹、深度 8；上一課就是把它包成 API 的）。

    監控要比較兩份資料，先把名字講清楚：

    - **參考視窗（reference）**：模型「認識」的世界。這裡用**訓練集**——模型就是照著它學的，
      任何偏離都值得問一句為什麼。（實務上也常用「上線後表現正常的那一週」當參考，兩種都對；
      重點是**參考視窗要固定**，不能每次拿上週比這週，那樣漸進式的漂移會被你自己抹平。）
    - **當前視窗（current）**：現在進來的這一批。

    我們刻意造一份漂移過的生產資料：**`f0` 整欄平移 +1.5、`f3` 整欄放大 2 倍**。
    這是刻意注入的，真實世界不會這麼乾淨——真實的漂移長這樣：上游換了感測器單位（公分變公尺）、
    行銷把客群從 25 歲拉到 45 歲、某個欄位的預設值從 0 改成 NaN、疫情把所有人的消費行為推走。
    重點不是漂移怎麼來的，是**你多快發現、以及發現之後做什麼**。
    """
    )
    return


@app.cell
def _(
    RandomForestClassifier,
    make_classification,
    pd,
    roc_auc_score,
    train_test_split,
):
    FEATURES = [f"f{i}" for i in range(12)]

    _X, _y = make_classification(n_samples=2000, n_features=12, n_informative=6, random_state=0)
    X_train, X_test, y_train, y_test = train_test_split(
        pd.DataFrame(_X, columns=FEATURES), _y, test_size=0.25, random_state=0
    )

    champion = RandomForestClassifier(n_estimators=100, max_depth=8, random_state=0).fit(X_train, y_train)
    ref_proba = champion.predict_proba(X_test)[:, 1]          # 上線初期的預測，當作預測的參考分佈
    ref_acc = champion.score(X_test, y_test)
    ref_auc = roc_auc_score(y_test, ref_proba)


    def make_window(shift: float = 0.0, scale: float = 1.0) -> pd.DataFrame:
        """造一批生產資料：f0 整欄平移 shift、f3 整欄乘上 scale。"""
        _w = X_test.copy()
        _w["f0"] = _w["f0"] + shift
        _w["f3"] = _w["f3"] * scale
        return _w


    prod = make_window(shift=1.5, scale=2.0)
    return (
        FEATURES,
        X_test,
        X_train,
        champion,
        make_window,
        prod,
        ref_acc,
        ref_auc,
        ref_proba,
        y_test,
    )


@app.cell(hide_code=True)
def _(FEATURES, X_test, X_train, mo, prod, ref_acc, ref_auc):
    mo.md(
        f"""
    | | 列數 | `f0` 平均 | `f3` 平均 | `f3` 標準差 |
    | --- | --- | --- | --- | --- |
    | 參考視窗（訓練集） | {len(X_train)} | {X_train["f0"].mean():.3f} | {X_train["f3"].mean():.3f} | {X_train["f3"].std():.3f} |
    | 上線第一週（測試集，沒動過） | {len(X_test)} | {X_test["f0"].mean():.3f} | {X_test["f3"].mean():.3f} | {X_test["f3"].std():.3f} |
    | 生產資料（注入漂移） | {len(prod)} | {prod["f0"].mean():.3f} | {prod["f3"].mean():.3f} | {prod["f3"].std():.3f} |

    模型在測試集上的表現：**accuracy {ref_acc:.3f}、AUC {ref_auc:.4f}**——這是「一切正常」的樣子，
    後面每個數字都跟它比。

    注意上面這張表：三份資料的**列數一樣、欄位一樣（{len(FEATURES)} 欄）、沒有任何缺值**，
    程式跑起來完全不會出錯。漂移不是 bug，它不會拋例外——這就是為什麼需要專門的監控。
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 1️⃣ 資料漂移：自己算一次 PSI

    先手寫，再用工具。不然你只會知道「Evidently 說有漂移」，卻不知道它憑什麼這樣說、
    也不知道它什麼時候會說錯。

    **PSI（Population Stability Index，族群穩定度指標）** 是信用評分業界用了幾十年的老指標，
    做法只有三步：

    1. **分箱**：用**參考視窗**的分位數把這一欄切成 10 個箱子（每箱各含參考資料的 10%）
    2. **算比例**：參考資料落在每個箱子的比例 `r_i`，當前資料落在每個箱子的比例 `c_i`
    3. **加總**：`PSI = Σ (c_i − r_i) × ln(c_i / r_i)`

    直覺：**每個箱子的「比例差」乘上「比例的倍數變化」再加總**。分佈完全沒變 → 每項都是 0；
    某個箱子的客戶從 10% 掉到 1% → 這一項就會貢獻很大的值。

    ```python
    def psi(ref, cur, bins=10):
        edges = np.quantile(ref, np.linspace(0, 1, bins + 1))
        edges[0], edges[-1] = -np.inf, np.inf          # 兩端開放，新資料超出範圍才不會掉出去
        r = np.histogram(ref, edges)[0] / len(ref) + 1e-6   # 1e-6：空箱時不要 log(0)
        c = np.histogram(cur, edges)[0] / len(cur) + 1e-6
        return float(np.sum((c - r) * np.log(c / r)))
    ```

    兩個細節是血淚換來的：**兩端要開放**（`-inf` / `+inf`），否則平移過的資料會有一部分
    根本落不進任何箱子；**每個比例都要加一個極小值**，否則只要有一個箱子在當前視窗是空的，
    `log(0)` 會讓整個 PSI 變成 `inf`（實測：把 `f0` 平移 8 之後不加 `1e-6` 就是 `inf`，
    加了是 12.434）。
    """
    )
    return


@app.cell
def _(np):
    def psi(ref, cur, bins: int = 10) -> float:
        """Population Stability Index：用參考視窗的分位數分箱，比較兩份資料的分佈差異。"""
        _edges = np.quantile(ref, np.linspace(0, 1, bins + 1))
        _edges[0], _edges[-1] = -np.inf, np.inf
        _r = np.histogram(ref, _edges)[0] / len(ref) + 1e-6
        _c = np.histogram(cur, _edges)[0] / len(cur) + 1e-6
        return float(np.sum((_c - _r) * np.log(_c / _r)))
    return (psi,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ### 把 `f0` 的 10 個箱子攤開來看

    PSI 是一個總分，但總分是加出來的——攤開每個箱子，你會直接看到「客戶跑去哪裡了」。
    下表每一列是一個箱子：參考視窗每箱固定 10%（分位數分箱的定義），
    當前視窗的比例則被平移推得亂七八糟。最後一欄是這個箱子對 PSI 的貢獻。
    """
    )
    return


@app.cell
def _(X_train, mo, np, pd, prod):
    _edges = np.quantile(X_train["f0"], np.linspace(0, 1, 11))
    _edges[0], _edges[-1] = -np.inf, np.inf
    _r = np.histogram(X_train["f0"], _edges)[0] / len(X_train) + 1e-6
    _c = np.histogram(prod["f0"], _edges)[0] / len(prod) + 1e-6
    bin_table = pd.DataFrame(
        {
            "bin": [f"{i + 1}" for i in range(10)],
            "範圍（參考分位數）": [
                f"{'-inf' if i == 0 else f'{_edges[i]:.2f}'} ~ {'+inf' if i == 9 else f'{_edges[i + 1]:.2f}'}"
                for i in range(10)
            ],
            "參考 %": (_r * 100).round(1),
            "生產 %": (_c * 100).round(1),
            "貢獻": ((_c - _r) * np.log(_c / _r)).round(3),
        }
    )
    mo.vstack(
        [
            mo.ui.table(bin_table, selection=None, pagination=False),
            mo.md(f"**`f0` 的 PSI ＝ 這一欄加總 ＝ {bin_table['貢獻'].sum():.3f}**"),
        ]
    )
    return (bin_table,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ### 12 個特徵一起算——而且要有對照組

    只算「有漂移」的那組，你會被自己騙：因為你不知道**沒有漂移的時候 PSI 長什麼樣**。
    所以下面一次算兩組：

    - **對照組**：參考視窗（訓練集 1500 筆）vs 上線第一週（測試集 500 筆，一個字都沒改）
    - **實驗組**：參考視窗 vs 生產資料（`f0` 平移 1.5、`f3` 放大 2 倍）

    對照組的 PSI **不會是 0**——兩份資料本來就是不同的抽樣，這個「雜訊底線」正是門檻該建立在哪裡的依據。
    """
    )
    return


@app.cell
def _(FEATURES, X_test, X_train, pd, prod, psi, stats):
    def drift_table(ref: pd.DataFrame, cur: pd.DataFrame) -> pd.DataFrame:
        """每欄一列：PSI、KS 統計量、KS p 值、兩邊的平均與標準差。"""
        _rows = []
        for _c in FEATURES:
            _ks = stats.ks_2samp(ref[_c], cur[_c])
            _rows.append(
                {
                    "feature": _c,
                    "psi": round(psi(ref[_c], cur[_c]), 3),
                    "ks_stat": round(float(_ks.statistic), 3),
                    "ks_p": float(f"{_ks.pvalue:.2e}"),
                    "ref_mean": round(float(ref[_c].mean()), 2),
                    "cur_mean": round(float(cur[_c].mean()), 2),
                }
            )
        return pd.DataFrame(_rows).sort_values("psi", ascending=False).reset_index(drop=True)


    control_tbl = drift_table(X_train, X_test)   # 對照組：沒有注入任何漂移
    drift_tbl = drift_table(X_train, prod)       # 實驗組：f0 +1.5、f3 ×2
    return control_tbl, drift_table, drift_tbl


@app.cell(hide_code=True)
def _(WATCH, control_tbl, drift_tbl, mo):
    mo.md(
        f"""
    **對照組（沒有漂移）**：12 欄的 PSI 最大只有 **{control_tbl["psi"].max():.3f}**
    （`{control_tbl.iloc[0]["feature"]}`），沒有任何一欄超過 {WATCH}。
    這就是「什麼都沒發生」時的雜訊底線。

    **實驗組（注入漂移）**：`{drift_tbl.iloc[0]["feature"]}` PSI **{drift_tbl.iloc[0]["psi"]:.3f}**、
    `{drift_tbl.iloc[1]["feature"]}` **{drift_tbl.iloc[1]["psi"]:.3f}**，
    其餘 10 欄跟對照組一模一樣（我們沒動它們）。
    **被動過手腳的那兩欄，被乾淨地指了出來**——這正是逐欄監控的價值：它不只說「有問題」，
    還說「問題在 `{drift_tbl.iloc[0]["feature"]}` 和 `{drift_tbl.iloc[1]["feature"]}`」，
    你可以直接拿這兩個欄位名去問上游。
    """
    )
    return


@app.cell
def _(control_tbl, drift_tbl, mo):
    mo.hstack(
        [
            mo.vstack([mo.md("**對照組**：train vs 沒動過的 test"), mo.ui.table(control_tbl, selection=None, pagination=False)]),
            mo.vstack([mo.md("**實驗組**：train vs 漂移過的生產資料"), mo.ui.table(drift_tbl, selection=None, pagination=False)]),
        ],
        wrap=True,
        justify="start",
        gap=1.5,
    )
    return


@app.cell
def _(ALARM, C_ALARM, C_CUR, C_OK, C_REF, WATCH, control_tbl, drift_tbl, plt):
    _fig, _ax = plt.subplots(figsize=(6.4, 3.6))
    _d = drift_tbl.sort_values("feature", key=lambda s: s.str[1:].astype(int))
    _c = control_tbl.sort_values("feature", key=lambda s: s.str[1:].astype(int))
    _x = range(len(_d))
    _ax.bar([i - 0.2 for i in _x], _c["psi"], width=0.4, color=C_REF, label="control (no drift)")
    _ax.bar(
        [i + 0.2 for i in _x],
        _d["psi"],
        width=0.4,
        color=[C_ALARM if v >= ALARM else C_CUR for v in _d["psi"]],
        label="production (drifted)",
    )
    _ax.axhline(WATCH, color=C_OK, ls="--", lw=1.2)
    _ax.axhline(ALARM, color=C_ALARM, ls="--", lw=1.2)
    _ax.text(11.6, WATCH + 0.012, f"watch {WATCH}", color=C_OK, fontsize=8, ha="right")
    _ax.text(11.6, ALARM + 0.012, f"alarm {ALARM}", color=C_ALARM, fontsize=8, ha="right")
    _ax.set_xticks(list(_x))
    _ax.set_xticklabels(_d["feature"], fontsize=8)
    _ax.set_ylabel("PSI")
    _ax.set_title("PSI per feature: control vs drifted production window")
    _ax.legend(fontsize=8, loc="upper right")
    _ax.spines[["top", "right"]].set_visible(False)
    _fig.tight_layout()
    _fig
    return


@app.cell(hide_code=True)
def _(control_tbl, mo):
    mo.md(
        f"""
    ### 那兩條虛線憑什麼是 0.1 和 0.25？

    業界慣例（來自信用評分模型的實務經驗，不是數學定理）：

    | PSI | 慣例解讀 | 建議動作 |
    | --- | --- | --- |
    | < 0.1 | 分佈穩定 | 什麼都不用做 |
    | 0.1 – 0.25 | 有變化，值得注意 | 盯著、查原因，先別動模型 |
    | > 0.25 | 分佈明顯改變 | 準備重訓 |

    **這三行要打三個折扣**：

    1. **PSI 會隨樣本數與箱數變動**。視窗越小，PSI 越容易被抽樣雜訊灌大
       （箱子裡的數字太少，噪音被放大）——下一節會用同一欄實測給你看：同一個小漂移，
       視窗 10000 筆時 PSI 是 0.010，縮到 50 筆時衝到 0.243。所以門檻要**在你自己的資料上校準**：
       拿一段「已知正常」的期間跑一次，看雜訊底線在哪，再把門檻訂在它上面。
       我們的對照組最大只有 {control_tbl["psi"].max():.3f}——所以 0.1 對這份資料剛好夠用，但那是巧合，不是規律。
    2. **PSI 大 ≠ 模型會變差**。它只說輸入變了，沒說模型答得對不對。
       一個沒被模型使用的欄位漂到天邊，模型照樣準。
    3. **PSI 小 ≠ 安全**。概念漂移可以在輸入分佈完全不動的情況下發生
       （前導課實測過：只有資料漂移時準確率 0.945 幾乎不掉，概念漂移時卻掉到 0.660）。

    所以 PSI 是**早期警報**，不是判決書。它的價值在於：**免費、即時、指得出是哪一欄。**
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 2️⃣ KS 檢定：統計學的說法，以及它為什麼常常吵到你關掉它

    另一個常見做法是拿統計檢定來問：「這兩份資料，有沒有可能來自同一個分佈？」
    連續數值最常用 **Kolmogorov–Smirnov 兩樣本檢定**（`scipy.stats.ks_2samp`）：

    - **統計量**：兩條累積分佈曲線之間的**最大垂直距離**（0 到 1，越大差越多）
    - **p 值**：假設兩邊真的來自同一個分佈，看到這麼大的距離的機率有多少

    習慣上 p < 0.05 就說「有顯著差異」。上面那張表裡，實驗組的
    `f3` p 值是 7.7e-20、`f0` 是 7.0e-25——小到不能再小，方向跟 PSI 完全一致。

    **但是**：對照組（完全沒有漂移）裡，`f3` 的 p 值是 0.0400、`f7` 是 0.0429——
    **兩欄都低於 0.05**。如果你把「p < 0.05 就警報」寫進監控，這兩欄今天就會叫你起床，
    而它們什麼事都沒有。

    原因是統計檢定回答的問題不是你想問的那個。它問「**有沒有差異**」，
    而你想知道的是「**差異大不大、要不要管**」。樣本一多，再小的差異都會變得「顯著」——
    下面這張表用同一欄 `f0` 實測給你看。
    """
    )
    return


@app.cell
def _(X_test, X_train, mo, np, pd, psi, stats):
    _rng = np.random.default_rng(3)
    _rows = []
    for _shift, _label in [(0.2, "小漂移 +0.2"), (0.0, "完全沒漂移")]:
        for _n in [50, 200, 500, 2000, 10000]:
            _idx = _rng.integers(0, len(X_test), _n)                 # 重抽樣模擬「這個視窗收集到 n 筆」
            _w = X_test["f0"].iloc[_idx] + _shift
            _ks = stats.ks_2samp(X_train["f0"], _w)
            _rows.append(
                {
                    "情境": _label,
                    "視窗筆數": _n,
                    "KS 統計量": round(float(_ks.statistic), 3),
                    "KS p 值": float(f"{_ks.pvalue:.2e}"),
                    "p < 0.05？": "⚠️ 警報" if _ks.pvalue < 0.05 else "—",
                    "PSI": round(psi(X_train["f0"], _w), 3),
                }
            )
    sample_size_tbl = pd.DataFrame(_rows)
    mo.ui.table(sample_size_tbl, selection=None, pagination=False)
    return (sample_size_tbl,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    這張表有兩件事要看，而且兩件事的方向相反：

    - **KS 的 p 值隨視窗變大而變小**：「完全沒漂移」那五列，50 筆時 p = 0.92（很安靜），
      10000 筆時 p 已經到 1e-05——**什麼都沒發生，警報卻越叫越大聲**。
      這就是大樣本下的過度敏感：檢定偵測到的是抽樣的細微差異，不是你在意的商業變化。
    - **PSI 隨視窗變小而變大**：「小漂移 +0.2」那五列，10000 筆時 PSI 只有 0.010（正確：這個漂移小到不用管），
      但 50 筆時衝到 0.243——**幾乎踩到重訓門檻，純粹是因為每個箱子裡只有五筆資料**。

    所以實務上的做法是：

    1. **用效果量（PSI、Wasserstein 這類「差多少」的指標）當主要判準**，統計檢定當輔助。
    2. **固定視窗大小**（例如「每週」或「每 1000 筆」擇一，不要混用）——視窗大小一變，
       所有門檻都要重新校準。
    3. 真的要用 p 值，就**跟效果量一起用**：p 值小**而且** PSI 大，才是值得處理的漂移。
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 3️⃣ 預測漂移：沒有標籤，也有東西可以看

    資料漂移看的是輸入，但輸入有 12 欄、實務上可能有 300 欄，逐欄看很吵。
    **預測漂移直接看模型的輸出**：同一個模型，餵進新資料之後吐出來的機率分佈變了沒有。

    它的三個好處：**一欄就好**（不管幾個特徵，輸出永遠是一個分數）、
    **不需要標籤**（模型自己就會產生）、
    **它直接對應到業務影響**（判為流失的人變多 → 行銷名單變長 → 錢）。

    三個要記的數字：**平均機率**、**判正率**（超過門檻被判為 1 的比例）、**預測分佈的 PSI**。

    ⚠️ **一個容易踩的坑**：預測漂移的參考分佈**不能用訓練集的預測**。
    模型看過訓練集，在上面的機率會過度自信（分佈偏向 0 與 1 兩端）。
    實測：拿訓練集的預測當參考、測試集的預測當當前，PSI 會是 0.183——
    看起來像嚴重漂移，其實只是 in-sample 與 out-of-sample 的差別。
    **參考分佈要用模型沒看過、而且當時表現正常的那一批**（這裡是測試集，也就是「上線第一週」）。
    """
    )
    return


@app.cell
def _(X_test, X_train, champion, mo, np, prod, psi, ref_proba):
    train_proba = champion.predict_proba(X_train)[:, 1]      # in-sample：拿來當反例
    prod_proba = champion.predict_proba(prod)[:, 1]

    pred_drift = {
        "平均機率": (ref_proba.mean(), prod_proba.mean()),
        "判正率（>0.5）": (float(np.mean(ref_proba > 0.5)), float(np.mean(prod_proba > 0.5))),
        "高信心（>0.8）比例": (float(np.mean(ref_proba > 0.8)), float(np.mean(prod_proba > 0.8))),
        "低信心（<0.2）比例": (float(np.mean(ref_proba < 0.2)), float(np.mean(prod_proba < 0.2))),
    }
    pred_psi = psi(ref_proba, prod_proba)
    insample_psi = psi(train_proba, ref_proba)

    mo.md(
        "\n".join(
            [
                "| 指標 | 上線第一週（參考） | 生產資料 | 變化 |",
                "| --- | --- | --- | --- |",
                *[
                    f"| {_k} | {_a:.3f} | {_b:.3f} | {_b - _a:+.3f} |"
                    for _k, (_a, _b) in pred_drift.items()
                ],
                f"| **預測分佈 PSI** | — | **{pred_psi:.3f}** | 超過 0.1，低於 0.25 |",
                "",
                (
                    f"對照的反例：拿**訓練集**的預測當參考，PSI 是 **{insample_psi:.3f}**——"
                    "資料一個字都沒漂移，分數卻比真的漂移還高。參考視窗選錯，整套監控就是白做的。"
                ),
            ]
        )
    )
    return insample_psi, pred_psi, prod_proba, train_proba


@app.cell
def _(C_CUR, C_REF, np, plt, prod_proba, ref_proba):
    _fig, _ax = plt.subplots(figsize=(6.4, 3.4))
    _bins = np.linspace(0, 1, 26)
    _ax.hist(ref_proba, bins=_bins, alpha=0.62, color=C_REF, label="week 1 (reference)")
    _ax.hist(prod_proba, bins=_bins, alpha=0.62, color=C_CUR, label="drifted production")
    _ax.axvline(0.5, color="#444", ls="--", lw=1.1)
    _ax.text(0.505, _ax.get_ylim()[1] * 0.92, "decision threshold 0.5", fontsize=8, color="#444")
    _ax.set_xlabel("predicted churn probability")
    _ax.set_ylabel("customers")
    _ax.set_title("Prediction drift: the model got less confident")
    _ax.legend(fontsize=8)
    _ax.spines[["top", "right"]].set_visible(False)
    _fig.tight_layout()
    _fig
    return


@app.cell(hide_code=True)
def _(mo, pred_drift):
    mo.md(
        f"""
    圖上看得很清楚：橘色（漂移後）比藍色**矮了兩端、胖了中間**——模型變得沒那麼有把握。
    高信心（>0.8）的客戶從 {pred_drift["高信心（>0.8）比例"][0]:.0%} 掉到 {pred_drift["高信心（>0.8）比例"][1]:.0%}，
    判為流失的比例從 {pred_drift["判正率（>0.5）"][0]:.0%} 掉到 {pred_drift["判正率（>0.5）"][1]:.0%}。

    **這一切都不需要任何標籤**。如果你的行銷名單長度突然少了 15%，是模型變保守了，
    不是客戶真的變忠誠——這件事在標籤回來之前你就該知道。

    ### 標籤回來之後：真正的分數

    這份教學資料裡我們作弊了——標籤一直都在（漂移只動特徵不動標籤），
    所以可以直接看「如果標籤現在就回來，會看到什麼」。
    真實世界要等 2 週、1 個月、甚至一季（客戶到底有沒有流失，要時間才知道）。
    """
    )
    return


@app.cell
def _(
    champion,
    drift_tbl,
    mo,
    pred_psi,
    prod,
    prod_proba,
    ref_acc,
    ref_auc,
    roc_auc_score,
    y_test,
):
    prod_acc = champion.score(prod, y_test)
    prod_auc = roc_auc_score(y_test, prod_proba)

    mo.md(
        f"""
    | 指標 | 上線第一週 | 漂移後 | 變化 |
    | --- | --- | --- | --- |
    | accuracy | {ref_acc:.3f} | {prod_acc:.3f} | {prod_acc - ref_acc:+.3f} |
    | AUC | {ref_auc:.4f} | {prod_auc:.4f} | {prod_auc - ref_auc:+.4f} |

    accuracy 掉了 {abs(prod_acc - ref_acc) * 100:.1f} 個百分點——**這是真實的損失**，
    500 個客戶裡多判錯了 {round(abs(prod_acc - ref_acc) * len(prod))} 個。

    注意 AUC 只掉了 {abs(prod_auc - ref_auc):.4f}：**排序能力幾乎沒壞，壞的是校準**。
    模型還是知道誰比較可能流失，只是「多少機率算高」這條線跑掉了。
    這種情況有時候調門檻就能救回大半，不一定要重訓——這也是為什麼「漂移警報」之後
    還要有一個人去看一眼，而不是直接開始重訓。

    ### 把三種訊號排在一起

    | 訊號 | 這次的數字 | 什麼時候拿得到 |
    | --- | --- | --- |
    | 資料漂移（最大 PSI） | {drift_tbl.iloc[0]["psi"]:.3f}（`{drift_tbl.iloc[0]["feature"]}`） | 立刻 |
    | 預測漂移（PSI） | {pred_psi:.3f} | 立刻 |
    | accuracy 下滑 | {ref_acc:.3f} → {prod_acc:.3f} | 等標籤，可能好幾週 |

    立刻拿得到的兩個都亮了，而且方向一致——**這就是你在標籤回來之前唯一能依靠的證據**。
    """
    )
    return prod_acc, prod_auc


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 4️⃣ Evidently：三行出一份報告，但預設值不是真理

    自己算沒問題，但正式環境你不會想維護一整套指標實作。
    **Evidently** 是目前最常見的開源漂移監控套件（Python、免費、可離線），
    它幫你做三件事：**每種欄位型別自動挑合適的方法**、**產出可以拿去開會的 HTML 報告**、
    **把結果變成可以程式判讀的字典**。

    0.7 版的 API 有三個東西要認識：

    ```python
    from evidently import Dataset, DataDefinition, Report
    from evidently.presets import DataDriftPreset

    # 1) DataDefinition：告訴它哪些欄是數值、哪些是類別、哪一欄是預測／標籤
    definition = DataDefinition(numerical_columns=FEATURES)

    # 2) Dataset：資料 + 定義
    ref_ds = Dataset.from_pandas(X_train, data_definition=definition)
    cur_ds = Dataset.from_pandas(prod,    data_definition=definition)

    # 3) Report：run(current, reference) —— 當前在前、參考在後，別寫反
    snapshot = Report([DataDriftPreset()]).run(cur_ds, ref_ds)
    snapshot.dict()["metrics"]     # 每一項有 metric_name / config / value
    ```

    `DataDefinition` 不是可有可無的裝飾：**宣告錯型別，方法就會換掉**。
    實測把 12 個數值欄宣告成 `categorical_columns`，Evidently 改用 Jensen-Shannon 距離、
    把每個浮點數當成一個類別，結果是 **12 欄全部被判漂移、而且每欄分數一模一樣（0.833）**——
    程式不會報錯，報告會很有自信地騙你。
    """
    )
    return


@app.cell
def _(FEATURES, X_test, X_train, pd, prod):
    from evidently import DataDefinition, Dataset, Report
    from evidently.metrics import ValueDrift
    from evidently.presets import DataDriftPreset

    ev_definition = DataDefinition(numerical_columns=FEATURES)
    ev_ref = Dataset.from_pandas(X_train, data_definition=ev_definition)
    ev_cur = Dataset.from_pandas(prod, data_definition=ev_definition)
    ev_control = Dataset.from_pandas(X_test, data_definition=ev_definition)   # 對照組：沒動過的 test

    snapshot = Report([DataDriftPreset()]).run(ev_cur, ev_ref)
    snapshot_control = Report([DataDriftPreset()]).run(ev_control, ev_ref)


    def evidently_table(snap) -> tuple[pd.DataFrame, dict]:
        """把 snapshot.dict() 拆成「一欄一列的表」＋「整體摘要」。"""
        _metrics = snap.dict()["metrics"]
        _summary = _metrics[0]["value"]                    # DriftedColumnsCount
        _rows = [
            {
                "feature": _m["config"]["column"],
                "method": _m["config"]["method"],
                "score": round(float(_m["value"]), 3),
                "threshold": _m["config"]["threshold"],
                "drifted": "⚠️" if float(_m["value"]) >= _m["config"]["threshold"] else "",
            }
            for _m in _metrics[1:]
        ]
        return pd.DataFrame(_rows), _summary


    ev_tbl, ev_summary = evidently_table(snapshot)
    ev_tbl_control, ev_summary_control = evidently_table(snapshot_control)
    return (
        DataDefinition,
        Dataset,
        Report,
        ValueDrift,
        ev_cur,
        ev_definition,
        ev_ref,
        ev_summary,
        ev_summary_control,
        ev_tbl,
        ev_tbl_control,
        snapshot,
    )


@app.cell
def _(ev_tbl, ev_tbl_control, mo):
    mo.hstack(
        [
            mo.vstack([mo.md("**實驗組**（漂移過的生產資料）"), mo.ui.table(ev_tbl, selection=None, pagination=False)]),
            mo.vstack([mo.md("**對照組**（沒動過的 test）"), mo.ui.table(ev_tbl_control, selection=None, pagination=False)]),
        ],
        wrap=True,
        justify="start",
        gap=1.5,
    )
    return


@app.cell(hide_code=True)
def _(control_tbl, ev_summary, ev_summary_control, ev_tbl, ev_tbl_control, mo):
    mo.md(
        f"""
    ### 現在看一件會讓你重新想一遍的事

    | | 被判漂移的欄數 | 最高分 | 第二高 |
    | --- | --- | --- | --- |
    | 實驗組（真的漂移了） | **{int(ev_summary["count"])} / 12**（{ev_summary["share"]:.0%}） | {ev_tbl.sort_values("score", ascending=False).iloc[0]["feature"]} {ev_tbl["score"].max():.3f} | {ev_tbl.sort_values("score", ascending=False).iloc[1]["feature"]} {ev_tbl.sort_values("score", ascending=False).iloc[1]["score"]:.3f} |
    | 對照組（什麼都沒發生） | **{int(ev_summary_control["count"])} / 12**（{ev_summary_control["share"]:.0%}） | {ev_tbl_control.sort_values("score", ascending=False).iloc[0]["feature"]} {ev_tbl_control["score"].max():.3f} | {ev_tbl_control.sort_values("score", ascending=False).iloc[1]["feature"]} {ev_tbl_control.sort_values("score", ascending=False).iloc[1]["score"]:.3f} |

    **兩組的「被判漂移欄數」一模一樣。** 用 Evidently 的預設值（Wasserstein normed、門檻 0.1），
    一份完全沒有漂移的資料照樣被判 3 欄漂移——因為 1500 筆與 500 筆之間本來就有抽樣差異，
    而 0.1 這個預設門檻對這份資料來說訂得太低。

    差別完全在**分數的量級**：實驗組最高 {ev_tbl["score"].max():.3f}，對照組最高只有 {ev_tbl_control["score"].max():.3f}。

    可以帶走的三句話：

    1. **「幾欄超標」是資訊量最低的指標**，卻是最多人拿來當警報條件的那一個。看分數、看趨勢。
    2. **任何工具的預設門檻都要用你自己的「已知正常」資料校準過**才能上線
       （我們自己算的 PSI 在對照組最大只有 {control_tbl["psi"].max():.3f}，所以 0.1 對 PSI 剛好夠用，對 Wasserstein 就不夠）。
    3. **對照組不是可選的**。沒有對照組，你不會知道你的警報有多會誤報。
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ### Wasserstein 跟 PSI 差在哪？

    一句話：**Wasserstein 距離量的是「把一堆土從參考分佈搬成當前分佈，平均要搬多遠」**
    （normed ＝ 再除以參考分佈的尺度，所以跟單位無關）；
    **PSI 量的是「分箱之後，每個箱子的比例變了幾倍」**。

    差別會在這裡顯現：整欄平移 → 兩者都抓得到；
    某一個小箱子的客戶忽然消失（例如某個地區的資料斷線）→ PSI 反應很大、Wasserstein 幾乎不動
    （土的重心沒怎麼移）。所以「用哪個方法」本身就是一個要記錄下來的決定。

    Evidently 也可以直接指定方法——換成 PSI 試試看：
    """
    )
    return


@app.cell
def _(Report, ValueDrift, ev_cur, ev_ref, mo, psi, X_train, prod):
    _snap = Report(
        [ValueDrift(column="f0", method="psi"), ValueDrift(column="f3", method="psi"), ValueDrift(column="f2", method="psi")]
    ).run(ev_cur, ev_ref)
    method_rows = [
        (_m["config"]["column"], round(float(_m["value"]), 3)) for _m in _snap.dict()["metrics"]
    ]
    mo.md(
        "\n".join(
            [
                "| 欄位 | 我們自己算的 PSI | Evidently 的 `method=\"psi\"` |",
                "| --- | --- | --- |",
                *[f"| `{_c}` | {psi(X_train[_c], prod[_c]):.3f} | {_v:.3f} |" for _c, _v in method_rows],
                "",
                (
                    "同樣叫 PSI，數字卻不一樣——因為**分箱策略不同**（我們用參考資料的十分位數，"
                    "Evidently 用它自己的分箱規則）。這不是誰對誰錯，而是提醒你："
                ),
                "**門檻永遠是綁在某一個實作上的**。換工具、換分箱數、換視窗大小，門檻都要重新校準。",
            ]
        )
    )
    return (method_rows,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ### 那份 HTML 報告

    Evidently 最有價值的產出其實是**給人看的報告**：每一欄都有參考／當前分佈的疊圖，
    開會時把它丟出來，比你講十分鐘有用。

    ```python
    html = snapshot.get_html_str(as_iframe=False)
    Path("drift_report.html").write_text(html, encoding="utf-8")
    ```

    實測這份報告是 **4.3 MB**（互動圖表與資料全部內嵌在單一檔案裡，所以打開不需要網路）。
    這個大小塞進 notebook 裡顯示會讓頁面明顯變重，所以我們**存成檔案、用瀏覽器開**。
    在 molab 上，檔案存在執行環境裡，從它的檔案面板就能下載。
    """
    )
    return


@app.cell
def _(WORK, mo, snapshot):
    report_path = WORK / "drift_report.html"
    _html = snapshot.get_html_str(as_iframe=False)
    report_path.write_text(_html, encoding="utf-8")

    # 真的想直接在 notebook 裡看（頁面會變重，4 MB 級的內嵌報告）：
    # mo.iframe(_html, height="600px")

    mo.md(
        f"""
    報告已存到 `{report_path}`（{len(_html) / 1024 / 1024:.1f} MB）。
    用瀏覽器打開它，你會看到每一欄的分佈疊圖——`f0` 與 `f3` 那兩張一眼就看得出來。
    """
    )
    return (report_path,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 5️⃣ 從分數到決策：什麼時候真的該重訓

    到這裡你有一堆數字了。但監控系統的產出不能是數字，**必須是一個動作**：
    什麼都不做、盯著看、還是重訓。把它寫成一個函式，規則才會被討論、被版本控制、被改進。

    三個零件缺一不可：

    1. **分數門檻**：`watch` 與 `alarm` 兩級（我們用 0.10 / 0.25，但要用自己的對照組校準過）
    2. **連續 N 次**：單一視窗超標很可能只是雜訊（上面那張表你已經看到 50 筆的視窗
       可以無中生有一個 0.243）。要求**連續 N 個視窗**都超標，假警報會少一個數量級。
    3. **人工確認**：函式回傳 `retrain` 不等於自動開始重訓，而是**開一張工單、通知負責的人**。
       因為重訓不是免費的（要算力、要驗證、要重新走一次上線流程），而且有些漂移的正確處理方式
       根本不是重訓——是去修上游那個把公分改成公尺的服務。

    ```python
    def decide(max_psi, streak, watch=0.10, alarm=0.25, need=3):
        if max_psi >= alarm and streak >= need:
            return "retrain"        # 開工單 → 人確認 → 觸發重訓管線
        if max_psi >= watch:
            return "watch"          # 記錄下來、盯著，先不動模型
        return "ok"
    ```
    """
    )
    return


@app.cell
def _(ALARM, WATCH):
    def decide(max_psi: float, streak: int, watch: float = WATCH, alarm: float = ALARM, need: int = 3) -> str:
        """把漂移分數與「連續超標次數」變成一個動作：ok / watch / retrain。"""
        if max_psi >= alarm and streak >= need:
            return "retrain"
        if max_psi >= watch:
            return "watch"
        return "ok"
    return (decide,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ### 跑 8 個星期看看

    現在模擬一段真實一點的時間軸：每週收到 500 筆（從測試集重抽，所以**每週都有抽樣雜訊**），
    `f0` 的平移與 `f3` 的放大從第 4 週開始慢慢變嚴重。
    每週算一次全欄 PSI，取最大值，餵給 `decide()`。
    """
    )
    return


@app.cell
def _(ALARM, FEATURES, X_test, X_train, decide, make_window, np, pd, psi, ref_proba, champion, y_test):
    _rng = np.random.default_rng(7)
    _shifts = [0.0, 0.05, 0.1, 0.3, 0.6, 0.9, 1.2, 1.5]
    _rows, _streak = [], 0
    for _w, _s in enumerate(_shifts, start=1):
        _idx = _rng.integers(0, len(X_test), len(X_test))          # 這週進來的 500 筆
        _win = make_window(shift=_s, scale=1 + _s * 0.6).iloc[_idx]
        _scores = {_c: psi(X_train[_c], _win[_c]) for _c in FEATURES}
        _max = max(_scores.values())
        _p = champion.predict_proba(_win)[:, 1]
        _streak = _streak + 1 if _max >= ALARM else 0
        _rows.append(
            {
                "週": _w,
                "最大 PSI": round(_max, 3),
                "最吵的欄": max(_scores, key=_scores.get),
                "超過 0.1 的欄數": sum(_v >= 0.1 for _v in _scores.values()),
                "預測 PSI": round(psi(ref_proba, _p), 3),
                "連續超標": _streak,
                "決策": decide(_max, _streak),
                "（事後才知道的）accuracy": round(float(np.mean((_p > 0.5).astype(int) == y_test[_idx])), 3),
            }
        )
    weekly = pd.DataFrame(_rows)
    weekly
    return (weekly,)


@app.cell
def _(ALARM, C_ALARM, C_CUR, C_OK, C_REF, WATCH, plt, weekly):
    _fig, _ax = plt.subplots(figsize=(6.4, 3.6))
    _x = weekly["週"]
    _color = {"ok": C_OK, "watch": C_CUR, "retrain": C_ALARM}
    _ax.plot(_x, weekly["最大 PSI"], color=C_REF, lw=2, marker="o", markersize=5, zorder=3, label="max PSI")
    for _i, _r in weekly.iterrows():
        _ax.plot(_r["週"], _r["最大 PSI"], "o", color=_color[_r["決策"]], markersize=9, zorder=4)
    _ax.axhline(WATCH, color=C_OK, ls="--", lw=1.2)
    _ax.axhline(ALARM, color=C_ALARM, ls="--", lw=1.2)
    _ax.text(8.05, WATCH + 0.01, f"watch {WATCH}", color=C_OK, fontsize=8, ha="right")
    _ax.text(8.05, ALARM + 0.01, f"alarm {ALARM}", color=C_ALARM, fontsize=8, ha="right")
    _ax.annotate(
        "3rd week above alarm\n→ retrain",
        xy=(8, weekly["最大 PSI"].iloc[-1]),
        xytext=(5.4, 0.52),
        fontsize=8,
        color=C_ALARM,
        arrowprops={"arrowstyle": "->", "color": C_ALARM, "lw": 1},
    )
    _ax.set_xlabel("week")
    _ax.set_ylabel("max PSI across 12 features")
    _ax.set_title("Weekly drift: green = ok, orange = watch, red = retrain")
    _ax.spines[["top", "right"]].set_visible(False)
    _fig.tight_layout()
    _fig
    return


@app.cell(hide_code=True)
def _(mo, weekly):
    _first_alarm = weekly[weekly["最大 PSI"] >= 0.25]["週"].min()
    _trigger = weekly[weekly["決策"] == "retrain"]["週"].min()
    _noise = weekly[(weekly["最大 PSI"] >= 0.1) & (weekly["最大 PSI"] < 0.25)]["週"].tolist()
    mo.md(
        f"""
    這段模擬把「為什麼要連續 N 次」演得很清楚：

    - **第 {_noise[0]} 週就出現了 `watch`**——但那一週我們**一點漂移都還沒注入**
      （最吵的是 `{weekly.iloc[0]["最吵的欄"]}`，一個我們從頭到尾沒碰過的欄位）。
      這是重抽樣的雜訊。如果規則是「超過 0.1 就重訓」，你第一週就白重訓了一次。
    - **第 {int(_first_alarm)} 週最大 PSI 首次越過 0.25**，但決策仍是 `watch`——連續次數還不夠。
    - **第 {int(_trigger)} 週**連續第 3 次超標，才回傳 `retrain`。

    代價是**晚了兩週才動手**。這就是監控的核心取捨：
    **靈敏度 vs 誤報率**，沒有免費的午餐。要更早發現就接受更多假警報，
    要少被吵就接受晚一點知道。你能做的是把這個取捨**寫成明確的參數**（`alarm`、`need`、視窗大小），
    而不是留在某個人的直覺裡。

    另外看最後一欄：`accuracy` 在這段期間是 {weekly["（事後才知道的）accuracy"].min():.3f}–{weekly["（事後才知道的）accuracy"].max():.3f}
    上下跳動，**沒有 PSI 曲線那麼乾淨的趨勢**——而且真實世界裡它要好幾週後才會出現。
    這正是為什麼我們要用輸入端的漂移當早期警報，而不是坐等準確率掉下來。
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 6️⃣ 接回管線：讓監控自己跑、自己擋、自己叫人

    監控寫成 notebook 只是分析，寫進管線才是**維運**。用第 3、4 課的 Dagster，
    監控就是三個東西：

    ```
    production_batch ──▶ drift_report ──▶ scored_output
      今天進來的資料        每欄 PSI ＋        用模型打分
                          預測漂移            （警報時不該再產出）
                             │
                             ├── psi_watch （WARN，blocking=False）→ 只留紀錄，不擋
                             └── psi_alarm （ERROR，blocking=True）→ 擋住下游、整個 run 失敗
    ```

    **兩個檢查掛在同一個資產上，是本節的重點。** 它們對應到監控的兩種語氣：

    | | `psi_watch` | `psi_alarm` |
    | --- | --- | --- |
    | severity | `WARN` | `ERROR` |
    | blocking | `False` | `True` |
    | 沒過的時候 | run 仍然成功，帳本上留一筆黃色紀錄 | run **失敗**、下游**不執行**、該叫的人被叫 |
    | 用來表達 | 「有點怪，之後查」 | 「這批分數不能用」 |

    第 3 課踩過的坑要複習一次：**`AssetCheckResult` 的 severity 預設是 `ERROR`**，
    要 WARN 就得明寫；而**擋不擋下游是 `blocking=` 決定的**，跟 severity 是兩個獨立的旋鈕。
    """
    )
    return


@app.cell
def _(ALARM, FEATURES, WATCH, X_test, X_train, champion, dg, np, pd, psi, ref_proba):
    class WindowConfig(dg.Config):
        shift: float = 0.0
        scale: float = 1.0


    @dg.asset(group_name="monitoring", description="今天進來的一批生產資料")
    def production_batch(context: dg.AssetExecutionContext, config: WindowConfig) -> pd.DataFrame:
        _df = X_test.copy()
        _df["f0"] = _df["f0"] + config.shift
        _df["f3"] = _df["f3"] * config.scale
        context.add_output_metadata({"rows": len(_df), "shift": config.shift, "scale": config.scale})
        return _df


    @dg.asset(group_name="monitoring", description="每欄 PSI ＋ 預測漂移，一次算完")
    def drift_report(context: dg.AssetExecutionContext, production_batch: pd.DataFrame) -> dict:
        _scores = {_c: round(psi(X_train[_c], production_batch[_c]), 3) for _c in FEATURES}
        _proba = champion.predict_proba(production_batch)[:, 1]
        _rep = {
            "psi": _scores,
            "max_psi": max(_scores.values()),
            "worst_feature": max(_scores, key=_scores.get),
            "columns_over_watch": sum(_v >= WATCH for _v in _scores.values()),
            "prediction_psi": round(psi(ref_proba, _proba), 3),
            "positive_rate": round(float(np.mean(_proba > 0.5)), 3),
        }
        context.add_output_metadata({_k: _v for _k, _v in _rep.items() if _k != "psi"})
        return _rep


    @dg.asset_check(asset=drift_report, blocking=False, description=f"提醒：最大 PSI 應低於 {WATCH}")
    def psi_watch(drift_report: dict) -> dg.AssetCheckResult:
        return dg.AssetCheckResult(
            passed=drift_report["max_psi"] < WATCH,
            severity=dg.AssetCheckSeverity.WARN,        # 預設是 ERROR，要 WARN 一定要明寫
            metadata={"max_psi": drift_report["max_psi"], "worst": drift_report["worst_feature"]},
        )


    @dg.asset_check(asset=drift_report, blocking=True, description=f"警報：最大 PSI 應低於 {ALARM}")
    def psi_alarm(drift_report: dict) -> dg.AssetCheckResult:
        return dg.AssetCheckResult(
            passed=drift_report["max_psi"] < ALARM,
            severity=dg.AssetCheckSeverity.ERROR,       # ERROR ＋ blocking＝擋死下游、run 算失敗
            metadata={"max_psi": drift_report["max_psi"], "worst": drift_report["worst_feature"]},
        )


    @dg.asset(deps=[drift_report], group_name="monitoring", description="用現在的模型幫這批資料打分")
    def scored_output(production_batch: pd.DataFrame) -> int:
        return int((champion.predict_proba(production_batch)[:, 1] > 0.5).sum())


    MONITORING = [production_batch, drift_report, scored_output]
    MONITORING_CHECKS = [psi_watch, psi_alarm]
    return (
        MONITORING,
        MONITORING_CHECKS,
        WindowConfig,
        drift_report,
        production_batch,
        psi_alarm,
        psi_watch,
        scored_output,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ### 跑兩次：一次乾淨的資料、一次漂移的資料

    `dg.materialize()` 沒有 `asset_checks=` 參數——檢查要跟資產放在**同一個 list** 裡
    （忘了放的話 Dagster 不會提醒你，它只是靜靜地不跑那個檢查，run 照樣顯示成功）。
    我們用 `raise_on_error=False` 讓失敗的那次也能把結果收回來比較。
    """
    )
    return


@app.cell
def _(MONITORING, MONITORING_CHECKS, QUIET, dg, mo, pd):
    def run_monitoring(shift: float, scale: float):
        return dg.materialize(
            MONITORING + MONITORING_CHECKS,
            raise_on_error=False,
            run_config={**QUIET, "ops": {"production_batch": {"config": {"shift": shift, "scale": scale}}}},
        )


    def summarise(res, label: str) -> dict:
        _checks = {_e.check_name: _e for _e in res.get_asset_check_evaluations()}
        _mats = [_e.asset_key.to_user_string() for _e in res.get_asset_materialization_events()]
        return {
            "情境": label,
            "run 成功": "✅" if res.success else "❌",
            "psi_watch(WARN)": "通過" if _checks["psi_watch"].passed else "⚠️ 沒過",
            "psi_alarm(ERROR)": "通過" if _checks["psi_alarm"].passed else "🚨 沒過",
            "max_psi": str(_checks["psi_alarm"].metadata["max_psi"].value),
            "產出的資產": ", ".join(_mats),
        }


    res_clean = run_monitoring(0.0, 1.0)
    res_drift = run_monitoring(1.5, 2.0)
    monitoring_runs = pd.DataFrame(
        [summarise(res_clean, "乾淨的資料"), summarise(res_drift, "漂移的資料（f0 +1.5、f3 ×2）")]
    )
    mo.ui.table(monitoring_runs, selection=None, pagination=False)
    return monitoring_runs, res_clean, res_drift, run_monitoring, summarise


@app.cell(hide_code=True)
def _(mo, res_drift):
    _fail = [
        (_e.message or "")
        for _e in res_drift.filter_events(lambda ev: ev.is_failure)
    ]
    mo.md(
        f"""
    看第二列最後一欄：**`scored_output` 不見了**。blocking 的檢查沒過，下游根本不會執行——
    這正是你要的行為：**輸入已經不可信的時候，寧可今天沒有分數，也不要一批錯的分數流進業務系統**
    （而且 run 標記為失敗，你的告警系統才會響）。

    Dagster 的失敗事件原文：

    ```
    {_fail[0] if _fail else ""}
    ```

    如果改用 `raise_on_error=True`（預設值），會直接拋出：

    ```
    DagsterAssetCheckFailedError: 1 blocking asset check failed with ERROR severity:
    drift_report: psi_alarm
    ```

    順帶一提 `psi_watch` 在漂移那次也沒過，但它 `blocking=False` ＋ `WARN`——
    **run 照樣可以成功、下游照樣會跑**，只是帳本上留下一筆黃色紀錄。
    WARN 是給人看的線索，ERROR 是給機器執行的煞車。
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ### 誰來按下「重訓」？——用 sensor

    資產檢查會擋、會叫人，但它不會**觸發重訓**。第 4 課的 **sensor** 剛好補上這一段：
    它每隔一段時間醒來一次，看一眼帳本上最新的漂移報告，自己決定要不要送出 `RunRequest`。

    「連續 3 次」這個規則就存在 sensor 的 **cursor**（一小段它自己維護的字串狀態）裡：

    ```python
    @dg.sensor(target=[production_batch, drift_report, scored_output], minimum_interval_seconds=3600)
    def retrain_sensor(context):
        event = context.instance.get_latest_materialization_event(dg.AssetKey("drift_report"))
        max_psi = float(event.asset_materialization.metadata["max_psi"].value)
        streak = int(context.cursor or 0) + 1 if max_psi >= ALARM else 0
        context.update_cursor(str(streak))
        if streak >= 3:
            return dg.RunRequest(run_key=..., tags={"max_psi": str(max_psi)})
        return dg.SkipReason(f"max_psi={max_psi}，連續超標 {streak}/3——先不重訓")
    ```

    下面用 `evaluate_tick` 在 notebook 裡直接跑五次 tick（不用起 daemon），
    每次 tick 之前先跑一次監控管線、漂移一次比一次嚴重。看 cursor 怎麼累積、第幾次才送出請求。
    """
    )
    return


@app.cell
def _(ALARM, MONITORING, QUIET, dg, mo, pd, psi_alarm, psi_watch):
    @dg.sensor(
        target=MONITORING,
        minimum_interval_seconds=3600,
        description="連續 3 個視窗漂移警報就送出重訓請求",
    )
    def retrain_sensor(context: dg.SensorEvaluationContext):
        _event = context.instance.get_latest_materialization_event(dg.AssetKey("drift_report"))
        if _event is None:
            return dg.SkipReason("還沒有任何漂移報告")
        _max_psi = float(_event.asset_materialization.metadata["max_psi"].value)
        _streak = int(context.cursor or 0)
        _streak = _streak + 1 if _max_psi >= ALARM else 0
        context.update_cursor(str(_streak))
        if _streak >= 3:
            return dg.RunRequest(
                run_key=f"retrain-{_event.run_id[:8]}",
                tags={"max_psi": str(_max_psi), "reason": "drift"},
            )
        return dg.SkipReason(f"max_psi={_max_psi}，連續超標 {_streak}/3——先不重訓")


    _instance = dg.DagsterInstance.ephemeral()      # 一個共用的帳本，事件才留得住
    _cursor, _rows = None, []
    for _tick, _shift in enumerate([0.0, 1.0, 1.25, 1.5, 1.75], start=1):
        dg.materialize(
            MONITORING + [psi_watch, psi_alarm],
            instance=_instance,
            raise_on_error=False,
            run_config={**QUIET, "ops": {"production_batch": {"config": {"shift": _shift, "scale": 1.0}}}},
        )
        _ctx = dg.build_sensor_context(instance=_instance, cursor=_cursor)
        _result = retrain_sensor.evaluate_tick(_ctx)
        _cursor = _result.cursor
        _rows.append(
            {
                "tick": _tick,
                "f0 平移": _shift,
                "cursor（連續次數）": _cursor,
                "sensor 的決定": (
                    f"🚨 送出 RunRequest（tags={dict(_result.run_requests[0].tags)}）"
                    if _result.run_requests
                    else _result.skip_message
                ),
            }
        )
    sensor_ticks = pd.DataFrame(_rows)
    mo.ui.table(sensor_ticks, selection=None, pagination=False)
    return retrain_sensor, sensor_ticks


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    第 5 次 tick 才送出 `RunRequest`——而且它帶著 `max_psi` 標籤，
    所以之後在 Dagster 的介面上，你看得到「這次重訓是因為什麼被觸發的」。

    正式部署時把它們收成一份 `Definitions` 就完成了：

    ```python
    defs = dg.Definitions(
        assets=[production_batch, drift_report, scored_output, *訓練管線的資產],
        asset_checks=[psi_watch, psi_alarm],
        sensors=[retrain_sensor],
        schedules=[dg.ScheduleDefinition(job=monitoring_job, cron_schedule="0 6 * * *")],  # 每天早上六點監控
    )
    ```

    `RunRequest` 的 `target` 換成第 5 課那條**訓練管線**，就是一條完整的閉環：
    **監控發現漂移 → 送出重訓請求 → 訓練 → 評估 → 品質閘 → 通過才移動 `@champion` alias**。
    注意品質閘還在——**重訓出來的模型一樣要通過檢查才能上線**，
    否則你只是把「模型變差」自動化了。

    ⚠️ **實務上這裡通常會插一個人**：`RunRequest` 先送到一個需要人工核准的佇列，
    或先跑成 shadow 模式（新模型只算分不上線，比較兩版的預測差多少）。
    完全自動的重訓閉環只適合訓練成本低、標籤回來得快、而且回滾很容易的場景。
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ### 監控結果要留下來：記成 MLflow 的時間序列

    每次監控算出來的分數如果只印在畫面上，下週就沒了。
    最省事的做法是把它記成 MLflow 的 metric（第 1 課的 `step` 曲線在這裡剛好合用）：
    **一個 run 代表一條監控時間軸，每個視窗記一個 step**，之後就能在介面上看到漂移曲線，
    也能用程式把歷史讀回來判斷趨勢。
    """
    )
    return


@app.cell
def _(WORK, mlflow, mo, pd, weekly):
    mlflow.set_tracking_uri(f"sqlite:///{WORK}/mlflow.db")
    _name = "churn-monitoring"
    _exp = mlflow.get_experiment_by_name(_name)
    _exp_id = (
        _exp.experiment_id
        if _exp
        else mlflow.create_experiment(_name, artifact_location=str(WORK / "mlartifacts"))
    )
    mlflow.set_experiment(experiment_id=_exp_id)

    with mlflow.start_run(run_name="weekly-drift") as _run:
        mlflow.log_params({"reference": "train-1500", "window": "500 rows/week", "metric": "psi"})
        for _, _row in weekly.iterrows():
            mlflow.log_metric("max_psi", _row["最大 PSI"], step=int(_row["週"]))
            mlflow.log_metric("prediction_psi", _row["預測 PSI"], step=int(_row["週"]))
        monitoring_run_id = _run.info.run_id

    _history = mlflow.MlflowClient().get_metric_history(monitoring_run_id, "max_psi")
    mo.vstack(
        [
            mo.md(
                f"""
    監控 run：`{monitoring_run_id[:8]}…`，記了 {len(_history)} 個 step。
    把歷史讀回來（`client.get_metric_history(run_id, "max_psi")`），就能問「最近 3 個視窗是不是都超標」——
    也就是上面那個 `decide()` 需要的 `streak`，不必自己另外存一份狀態。
    """
            ),
            mo.ui.table(
                pd.DataFrame([{"step（週）": _m.step, "max_psi": _m.value} for _m in _history]),
                selection=None,
                pagination=False,
            ),
        ]
    )
    return (monitoring_run_id,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 7️⃣ 線上服務要記什麼

    上一課那個 `/predict` API 一旦上線，你就同時擁有了**軟體維運**與**機器學習**兩種故障模式，
    而它們的儀表板是不一樣的。四類東西一定要記，缺一類就有一種故障你看不見：

    | 記什麼 | 為什麼 | 出事時的樣子 |
    | --- | --- | --- |
    | **延遲** p50 / p95 / p99 | 平均值會騙人 | 平均 7 ms 很漂亮，p99 是 3 秒——每 100 個客戶就有 1 個在等 |
    | **錯誤率**（依狀態碼分） | 400 跟 500 是完全不同的故障 | 400 暴增＝上游資料格式變了；500 暴增＝你的服務壞了 |
    | **輸入摘要**（每欄的筆數／平均／缺值率） | 原始輸入不能全存（太大、常含個資） | 存摘要就夠算 PSI，而且可以只留統計量 |
    | **預測摘要**（平均機率、判正率） | 最省事的早期警報 | 判正率從 52% 掉到 44%，不用等標籤就知道有事 |

    **重點是第三、四類要「每個視窗存一列」**：監控要的不是原始請求，是**可以跟參考視窗比較的摘要**。
    一天一列、每列幾十個數字，存一年也只是幾百 KB。

    下面不起伺服器，直接量模型本身的延遲——這是 API 延遲的下限
    （真正的 API 還要加上 HTTP、JSON 反序列化、schema 驗證）。
    """
    )
    return


@app.cell
def _(X_test, champion, mo, np, pd, prod, ref_proba, time):
    _lat = []
    for _i in range(300):                                   # 模擬 300 個單筆請求
        _row = X_test.iloc[[_i % len(X_test)]]
        _t0 = time.perf_counter()
        champion.predict_proba(_row)
        _lat.append((time.perf_counter() - _t0) * 1000)
    _lat = np.array(_lat)

    _t0 = time.perf_counter()
    champion.predict_proba(X_test)                          # 同樣 500 列，一次算完
    _batch_ms = (time.perf_counter() - _t0) * 1000

    latency = {
        "p50": float(np.percentile(_lat, 50)),
        "p95": float(np.percentile(_lat, 95)),
        "p99": float(np.percentile(_lat, 99)),
        "batch_per_row": _batch_ms / len(X_test),
    }

    # 這就是「每個視窗存一列」的那一列：輸入摘要 ＋ 預測摘要 ＋ 服務指標
    _proba = champion.predict_proba(prod)[:, 1]
    monitoring_record = {
        "window": "2026-09-04",
        "rows": len(prod),
        "latency_p50_ms": round(latency["p50"], 2),
        "latency_p99_ms": round(latency["p99"], 2),
        "error_rate_4xx": 0.0,
        "error_rate_5xx": 0.0,
        "mean_proba": round(float(_proba.mean()), 3),
        "positive_rate": round(float(np.mean(_proba > 0.5)), 3),
        "reference_positive_rate": round(float(np.mean(ref_proba > 0.5)), 3),
        **{f"{_c}_mean": round(float(prod[_c].mean()), 3) for _c in ["f0", "f3"]},
        **{f"{_c}_missing": float(prod[_c].isna().mean()) for _c in ["f0", "f3"]},
    }

    mo.vstack(
        [
            mo.md(
                f"""
    單筆請求（模型本身）：**p50 {latency["p50"]:.2f} ms、p95 {latency["p95"]:.2f} ms、p99 {latency["p99"]:.2f} ms**。
    同樣 500 列改成一次批次算完，**每列只要 {latency["batch_per_row"]:.3f} ms**——
    差了 {latency["p50"] / latency["batch_per_row"]:.0f} 倍以上。
    （你的機器數字會不一樣，看的是量級與比例。）
    這個比例就是上一課「批次評分 vs 線上 API」那個取捨的來源：
    **線上 API 買的是即時性，代價是每列成本高得多。**

    每個視窗要存進監控資料表的那一列長這樣：
    """
            ),
            mo.ui.table(pd.DataFrame([monitoring_record]), selection=None, pagination=False),
            mo.md(
                "存了這一列，你就能算 PSI（用平均與分位數摘要）、看判正率趨勢、"
                "在 p99 爆掉的時候回頭對照那天的輸入分佈——**而且完全不需要保留任何一筆客戶的原始資料**。"
            ),
        ]
    )
    return latency, monitoring_record


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 8️⃣ 互動：漂移多嚴重，指標與決策怎麼變

    拉桿選 `f0` 要平移多少、`f3` 要放大幾倍，下拉選單決定判定漂移的門檻。
    每動一次，下面的 12 欄 PSI、預測漂移、決策標籤都會重算一次（真的重算，不是查表）。

    三件值得自己動手試的事：

    1. **把 `f3` 放大到 3.0、`f0` 平移留 0**：只有一欄漂移，但預測漂移與準確率掉最多——
       **漂移的欄數不重要，漂移的是不是重要的欄位才重要。**
    2. **把 `f0` 平移設 1.0、`f3` 放大設 1.5，然後把門檻在 0.10 與 0.25 之間切換**：
       同一份資料，被判漂移的欄數在 2 與 0 之間跳、決策標籤也從 watch 變 ok
       （兩欄的 PSI 分別是 0.186 與 0.246，剛好卡在兩個門檻之間）。
       **警報的多寡有一半是你自己訂出來的。**
    3. **把 `f0` 平移拉到 2.0、`f3` 留 1.0**：PSI 破 1.0，但 accuracy 幾乎沒掉——
       **輸入變了不等於模型會錯**，這是你在真實世界最常需要跟老闆解釋的一句話。
    """
    )
    return


@app.cell
def _(mo):
    shift_slider = mo.ui.slider(0.0, 2.0, step=0.25, value=1.5, label="f0 平移量", show_value=True)
    scale_slider = mo.ui.slider(1.0, 3.0, step=0.25, value=2.0, label="f3 放大倍數", show_value=True)
    thr_dropdown = mo.ui.dropdown(
        options={"0.05（很敏感）": 0.05, "0.10（業界慣例）": 0.10, "0.15": 0.15, "0.25（只看大變化）": 0.25},
        value="0.10（業界慣例）",
        label="判定漂移的 PSI 門檻",
    )
    mo.hstack([shift_slider, scale_slider, thr_dropdown], wrap=True, justify="start", gap=1.5)
    return scale_slider, shift_slider, thr_dropdown


@app.cell
def _(
    FEATURES,
    X_train,
    champion,
    control_tbl,
    decide,
    make_window,
    mo,
    np,
    pd,
    psi,
    ref_acc,
    ref_proba,
    scale_slider,
    shift_slider,
    thr_dropdown,
    y_test,
):
    _win = make_window(shift=shift_slider.value, scale=scale_slider.value)
    _thr = thr_dropdown.value
    _scores = {_c: round(psi(X_train[_c], _win[_c]), 3) for _c in FEATURES}
    _max_psi = max(_scores.values())
    _over = [_c for _c, _v in _scores.items() if _v >= _thr]
    _proba = champion.predict_proba(_win)[:, 1]
    _acc = float(np.mean((_proba > 0.5).astype(int) == y_test))
    _decision = decide(_max_psi, streak=3, watch=_thr)   # 下拉選單改的是 watch 門檻
    _badge = {"ok": "🟢 ok — 什麼都不用做", "watch": "🟡 watch — 記下來，盯著", "retrain": "🔴 retrain — 開工單"}
    _ctrl_over = int((control_tbl["psi"] >= _thr).sum())      # 同一個門檻下，對照組會誤報幾欄

    _live_tbl = pd.DataFrame(
        [{"feature": _c, "PSI": _v, "判定": "⚠️" if _v >= _thr else ""} for _c, _v in _scores.items()]
    ).sort_values("PSI", ascending=False)

    mo.vstack(
        [
            mo.md(
                f"""
    ### {_badge[_decision]}

    | 指標 | 值 | 對照（沒有漂移時） |
    | --- | --- | --- |
    | 最大 PSI | **{_max_psi:.3f}**（`{max(_scores, key=_scores.get)}`） | {control_tbl["psi"].max():.3f} |
    | 超過門檻 {_thr} 的欄數 | **{len(_over)} / 12**{"（" + "、".join(_over) + "）" if _over else ""} | {_ctrl_over} / 12 |
    | 預測分佈 PSI | **{psi(ref_proba, _proba):.3f}** | 0 |
    | 判正率 | **{np.mean(_proba > 0.5):.3f}** | {np.mean(ref_proba > 0.5):.3f} |
    | accuracy（要等標籤才看得到） | **{_acc:.3f}** | {ref_acc:.3f} |

    *決策假設「這個狀態已經連續 3 個視窗」；下拉選單調的是 watch 門檻，警報線固定在 0.25。*
    """
            ),
            mo.ui.table(_live_tbl, selection=None, pagination=False),
        ]
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 📌 收尾：一頁帶走

    | 問題 | 答案 |
    | --- | --- |
    | 模型變差了，我最快什麼時候知道？ | 輸入分佈與預測分佈**當天**就算得出來；準確率要等標籤 |
    | 用什麼指標？ | 數值欄 PSI（或 Wasserstein）、預測分佈 PSI、判正率；統計檢定當輔助 |
    | 門檻訂多少？ | 先拿「已知正常」的一段資料算出雜訊底線，再訂在它上面。慣例 0.1／0.25 只是起點 |
    | 一超標就重訓？ | 不。要求連續 N 個視窗、而且讓人看一眼——有些漂移該修的是上游，不是模型 |
    | 怎麼自動化？ | 監控做成資產＋兩個檢查（WARN 提醒／ERROR 擋下游），sensor 累積連續次數後送出重訓請求 |
    | 重訓之後呢？ | 新模型一樣要過品質閘才移 alias；**參考視窗也要換成新的**，否則你會一直對著舊世界報警 |

    最後那一行很多人漏掉：**重訓完成後，監控的參考視窗要跟著更新成新模型的訓練資料**。
    不更新的話，新模型上線第一天就會對你發出「嚴重漂移」的警報——因為它本來就是照著漂移後的世界訓練的。
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 🏆 延伸挑戰

    1. **LEVEL 1**：換一欄注入漂移。自己造一個視窗，把 `f7` 乘 0.4（這一欄的變異被壓扁、平均幾乎不動），
       再重算 `drift_table(X_train, 你的視窗)`。
       **預期**：`f7` 被指出來，其他欄維持在對照組的水準。順便看一眼 accuracy 掉了多少，
       跟動 `f0`／`f3` 比較——哪一欄比較「重要」？
    2. **LEVEL 2**：把「連續 3 次」改成「最近 4 個視窗裡有 3 次超標」（k-of-n 規則），
       用第 5️⃣ 節那段 8 週模擬跑一次，比較兩種規則各在第幾週觸發。
       **提示**：兩種規則在 0.25 門檻下結果一樣，把觸發門檻降到 0.1 再比一次，差別就出來了。
    3. **LEVEL 3**：換掉 Evidently 的預設。任選一條路：
       (a) 用 `ValueDrift(column=..., method="psi", threshold=...)` 自己組一份 12 欄的報告，
       門檻用你從對照組校準出來的數字；或
       (b) 加一個 `ClassificationPreset()`，把標籤與預測都放進 `DataDefinition`，
       產生「有標籤之後」的品質報告。
       **怎麼驗證自己做對了**：(a) 對照組應該一欄都不超標、實驗組只有 `f0` 與 `f3` 超標；
       (b) 報告裡的 accuracy 要等於你自己算的 0.864（漂移後）。

    先自己試，卡住再展開下面的參考解答。
    帶得走：下載本檔後 `uvx marimo edit --sandbox model-monitoring_ext.py`
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
    win_f7 = X_test.copy()
    win_f7["f7"] = win_f7["f7"] * 0.4          # 變異被壓扁：分佈變窄，平均幾乎不動
    tbl_f7 = drift_table(X_train, win_f7)
    print(tbl_f7.head(3).to_string(index=False))
    print("accuracy:", champion.score(win_f7, y_test))
    ```

    實測 `f7` 的 PSI 是 **2.083**（其餘 11 欄跟對照組一模一樣，因為那 11 欄真的沒動）——
    比 `f3` 漂移時的 0.558 還大四倍。但 **accuracy 只從 0.916 掉到 0.914**，等於沒掉。

    為什麼？看 `champion.feature_importances_`：`f7` 是 **0.017**，`f3` 是 0.161、`f2` 是 0.408。
    **一個模型幾乎沒在用的欄位，漂到天邊也不痛。**

    所以「PSI 最大的那一欄」不等於「最該擔心的那一欄」——成熟的監控會把特徵重要度乘進警報權重，
    或者乾脆只監控前幾名重要的特徵。這也是預測漂移的價值：它天生就把重要度算進去了。
    """
            ),
            "💡 LEVEL 2 參考解答": mo.md(
                r"""
    ```python
    def k_of_n(history, thr=0.25, k=3, n=4):
        # 最近 n 個視窗裡至少 k 個超標
        return sum(v >= thr for v in history[-n:]) >= k

    scores = list(weekly["最大 PSI"])
    for thr in (0.25, 0.10):
        streak_week = kofn_week = None
        streak = 0
        for i, v in enumerate(scores, start=1):
            streak = streak + 1 if v >= thr else 0
            if streak >= 3 and streak_week is None:
                streak_week = i
            if k_of_n(scores[:i], thr=thr) and kofn_week is None:
                kofn_week = i
        print(f"門檻 {thr}: 連續3次→第 {streak_week} 週；4取3→第 {kofn_week} 週")
    ```

    實測輸出：

    ```
    門檻 0.25: 連續3次→第 8 週；4取3→第 8 週
    門檻 0.1:  連續3次→第 6 週；4取3→第 4 週
    ```

    0.25 門檻下兩者一樣（第 6、7、8 週本來就是連續的）。降到 0.1 差別就出來了：
    **k-of-n 提早了兩週**，因為它容忍中間有一週掉回門檻以下（第 3 週的 0.086）。
    但這裡它其實是**誤報**——第 1、2、4 週的超標是抽樣雜訊，我們第 4 週根本還沒注入多少漂移。

    結論不是「哪個比較好」，而是：**漸進式的漂移用 k-of-n（不會被中間一次回落重置），
    雜訊大的訊號用連續 N 次（比較保守）。** 選哪個要看你的訊號長什麼樣，
    而這就是為什麼你需要先跑一段「已知正常」的歷史資料來調規則。
    """
            ),
            "💡 LEVEL 3 提示": mo.md(
                r"""
    **(a) 自組 PSI 報告**

    ```python
    from evidently.metrics import ValueDrift
    my_report = Report([ValueDrift(column=c, method="psi", threshold=0.15) for c in FEATURES])
    snap_a = my_report.run(ev_cur, ev_ref)
    over = [(m["config"]["column"], round(m["value"], 3))
            for m in snap_a.dict()["metrics"] if m["value"] >= m["config"]["threshold"]]
    ```

    門檻怎麼選：先對**對照組**跑一次，看最高分是多少，把門檻訂在它上面留一點餘裕。
    驗證：對照組 `over` 應該是空的，實驗組只有 `f0` 與 `f3`。
    注意 Evidently 的 PSI 分箱跟我們自己寫的不同（`f3`：我們 0.558、它 0.973），
    **門檻不能從自己的實作直接搬過去**。

    **(b) 加分類報告**

    ```python
    from evidently import BinaryClassification
    from evidently.presets import ClassificationPreset

    definition_cls = DataDefinition(
        numerical_columns=FEATURES,
        classification=[BinaryClassification(target="target", prediction_labels="pred")],
    )
    ref_df = X_test.assign(target=y_test, pred=champion.predict(X_test))
    cur_df = prod.assign(target=y_test, pred=champion.predict(prod))
    snap_b = Report([ClassificationPreset()]).run(
        Dataset.from_pandas(cur_df, data_definition=definition_cls),
        Dataset.from_pandas(ref_df, data_definition=definition_cls),
    )
    ```

    驗證：報告裡的 `Accuracy` 應該等於你自己算的漂移後 accuracy（0.864），
    `Recall` 會掉得比 `Precision` 多（實測 0.792 / 0.941）——**模型變保守了，漏掉的流失客戶變多**。
    忘了宣告 `classification=` 的話會直接拋
    `ValueError: Cannot use ClassificationPreset without a classification configration`。

    這一段要記得的是：**有標籤的報告永遠比漂移報告有說服力，但它要等**。
    漂移監控的存在意義，就是在等的那幾週裡替你看著。
    """
            ),
        }
    )
    return


if __name__ == "__main__":
    app.run()
