# 課 07（model-monitoring）測驗題用的「真實錯誤訊息」撞牆腳本。
# 跑法：uv run --script content/mlops/_spikes/spike_monitoring_errors.py
# 每一段都刻意寫錯，把 Evidently / PSI / KS 的真實反應原文印出來（測驗題與教學頁只引用這裡的原文）。
# /// script
# requires-python = ">=3.11"
# dependencies = ["evidently>=0.7", "scikit-learn", "pandas", "numpy", "scipy"]
# ///
import traceback
import warnings

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split

warnings.filterwarnings("ignore")
COLS = [f"f{i}" for i in range(12)]
X, y = make_classification(n_samples=2000, n_features=12, n_informative=6, random_state=0)
Xdf = pd.DataFrame(X, columns=COLS)
Xtr, Xte, _ytr, _yte = train_test_split(Xdf, y, test_size=0.25, random_state=0)
prod = Xte.copy()
prod["f0"] = prod["f0"] + 1.5
prod["f3"] = prod["f3"] * 2.0


def show(title: str, fn) -> None:
    print(f"\n{'=' * 78}\n== {title}\n{'=' * 78}")
    try:
        out = fn()
        print("（沒有拋錯）→", out)
    except Exception:  # noqa: BLE001 — 就是要看原文
        traceback.print_exc()


from evidently import BinaryClassification, DataDefinition, Dataset, Report  # noqa: E402
from evidently.metrics import ValueDrift  # noqa: E402
from evidently.presets import DataDriftPreset  # noqa: E402

DEF = DataDefinition(numerical_columns=COLS)
ref_ds = Dataset.from_pandas(Xtr, data_definition=DEF)
cur_ds = Dataset.from_pandas(prod, data_definition=DEF)

def psi_naive(ref, cur, bins=10):
    edges = np.quantile(ref, np.linspace(0, 1, bins + 1))
    edges[0], edges[-1] = -np.inf, np.inf
    r = np.histogram(ref, edges)[0] / len(ref)
    c = np.histogram(cur, edges)[0] / len(cur)
    return float(np.sum((c - r) * np.log(c / r)))


def psi_safe(ref, cur, bins=10, eps=1e-6):
    edges = np.quantile(ref, np.linspace(0, 1, bins + 1))
    edges[0], edges[-1] = -np.inf, np.inf
    r = np.histogram(ref, edges)[0] / len(ref) + eps
    c = np.histogram(cur, edges)[0] / len(cur) + eps
    return float(np.sum((c - r) * np.log(c / r)))


# ── 1. 直接把 DataFrame 丟給 Report.run（忘了包成 Dataset）
def _raw_df():
    _snap = Report([DataDriftPreset()]).run(prod, Xtr)
    _m = _snap.dict()["metrics"]
    return [(x["metric_name"], x["value"]) for x in _m[:3]]


show("1. Report.run() 直接吃 pandas DataFrame（沒包成 Dataset）", _raw_df)

# ── 2. 沒有宣告欄位型別（空的 DataDefinition）
def _no_def():
    _d = DataDefinition()
    _snap = Report([DataDriftPreset()]).run(
        Dataset.from_pandas(prod, data_definition=_d), Dataset.from_pandas(Xtr, data_definition=_d)
    )
    return [m["metric_name"] for m in _snap.dict()["metrics"]]


show("2. DataDefinition() 什麼都沒宣告", _no_def)

# ── 3. 把數值欄宣告成類別欄
def _wrong_type():
    _d = DataDefinition(categorical_columns=COLS)
    _snap = Report([DataDriftPreset()]).run(
        Dataset.from_pandas(prod, data_definition=_d), Dataset.from_pandas(Xtr, data_definition=_d)
    )
    _m = _snap.dict()["metrics"]
    return [(x["metric_name"], x["value"]) for x in _m[:3]]


show("3. 數值欄宣告成 categorical_columns", _wrong_type)

# ── 4. 生產資料少一欄（上游改了 schema）
def _missing_col():
    _cur = prod.drop(columns=["f11"])
    return Report([DataDriftPreset()]).run(Dataset.from_pandas(_cur, data_definition=DEF), ref_ds)


show("4. 生產資料少了 f11 欄", _missing_col)

# ── 5. 欄位型別在生產端變成字串
def _str_col():
    _cur = prod.copy()
    _cur["f1"] = _cur["f1"].round(2).astype(str)
    return Report([ValueDrift(column="f1")]).run(Dataset.from_pandas(_cur, data_definition=DEF), ref_ds)


show("5. 生產資料的 f1 變成字串欄", _str_col)

# ── 6. 參考／生產顛倒：Evidently 的 PSI 對稱、自寫「用參考分位數分箱」的 PSI 不對稱
def _swapped():
    _a = Report([ValueDrift(column="f3", method="psi")]).run(cur_ds, ref_ds).dict()["metrics"][0]["value"]
    _b = Report([ValueDrift(column="f3", method="psi")]).run(ref_ds, cur_ds).dict()["metrics"][0]["value"]
    _c = psi_safe(Xtr["f3"], prod["f3"])
    _d = psi_safe(prod["f3"], Xtr["f3"])
    return (
        f"evidently run(cur, ref)={_a:.3f} / run(ref, cur)={_b:.3f}（對稱）"
        f" || 自寫 psi(ref=train, cur=prod)={_c:.3f} / 寫反 psi(ref=prod, cur=train)={_d:.3f}"
    )


show("6. 參考／生產寫反", _swapped)

# ── 7. 自寫 PSI：分箱有空箱 → 除以零
def _empty_bin():
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        _v = psi_naive(Xtr["f0"], Xte["f0"] + 8.0)  # 平移到參考分佈之外 → 前面幾個箱全空
        _msgs = [f"{x.category.__name__}: {x.message}" for x in w]
    return f"psi_naive={_v} warnings={_msgs} | psi_safe={psi_safe(Xtr['f0'], Xte['f0'] + 8.0):.3f}"


show("7. PSI 遇到空箱（沒加 epsilon）", _empty_bin)

# ── 8. 自寫 PSI：常數欄（所有分位數相同）
def _constant_psi():
    _ref = pd.Series(np.zeros(1500))
    _cur = pd.Series(np.zeros(500))
    return f"psi_safe(常數 vs 常數)={psi_safe(_ref, _cur)} / psi_naive={psi_naive(_ref, _cur)}"


show("8. PSI 對常數欄", _constant_psi)

# ── 9. KS 對常數欄／小視窗
def _ks_edge():
    _c1 = stats.ks_2samp(np.zeros(1500), np.zeros(500))
    _c2 = stats.ks_2samp(np.zeros(1500), np.zeros(500) + 1)
    _small = stats.ks_2samp(Xtr["f0"], (Xte["f0"] + 1.5).head(20))
    _big = stats.ks_2samp(Xtr["f0"], Xte["f0"])
    return (
        f"常數 vs 常數 stat={_c1.statistic} p={_c1.pvalue} | 常數 vs 另一個常數 stat={_c2.statistic} p={_c2.pvalue:.3g}"
        f" | 20 筆視窗（真的漂移 1.5）p={_small.pvalue:.4f} | 沒漂移的 500 筆 f0 p={_big.pvalue:.4f}"
    )


show("9. KS 檢定的邊界情況", _ks_edge)

# ── 10. ClassificationPreset 少宣告 classification
def _cls_no_def():
    _cur = prod.copy()
    _cur["target"] = _yte
    _cur["pred"] = _yte
    from evidently.presets import ClassificationPreset

    return Report([ClassificationPreset()]).run(Dataset.from_pandas(_cur, data_definition=DEF), None)


show("10. ClassificationPreset 但 DataDefinition 沒宣告 classification", _cls_no_def)


def _cls_ok():
    from evidently.presets import ClassificationPreset

    _d = DataDefinition(
        numerical_columns=COLS,
        classification=[BinaryClassification(target="target", prediction_labels="pred")],
    )
    _cur = prod.copy()
    _cur["target"] = _yte
    _cur["pred"] = _yte
    _snap = Report([ClassificationPreset()]).run(Dataset.from_pandas(_cur, data_definition=_d), None)
    return [(m["metric_name"], m["value"]) for m in _snap.dict()["metrics"][:2]]


show("10b. 正確宣告 classification 後", _cls_ok)


# ── 11. 對照組：完全沒注入漂移的 test 集，Evidently 預設門檻判幾欄漂移？
def _control():
    _cur0 = Dataset.from_pandas(Xte, data_definition=DEF)
    _m = Report([DataDriftPreset()]).run(_cur0, ref_ds).dict()["metrics"]
    _cnt = _m[0]["value"]
    _over = [(x["config"]["column"], round(x["value"], 3)) for x in _m[1:] if x["value"] >= 0.1]
    _all = {x["config"]["column"]: round(x["value"], 3) for x in _m[1:]}
    return f"DriftedColumnsCount={_cnt} 超標欄={_over} 全部={_all}"


show("11. 對照組（train vs 未漂移的 test）：Evidently 預設門檻的誤判", _control)
