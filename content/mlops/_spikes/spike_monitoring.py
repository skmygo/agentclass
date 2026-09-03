# 候選課 spike：模型監控——特徵漂移（PSI / KS）、預測漂移、Evidently 報告
# /// script
# requires-python = ">=3.11"
# dependencies = ["evidently>=0.7", "scikit-learn", "pandas", "numpy", "scipy"]
# ///
import time, warnings
import numpy as np, pandas as pd
from scipy import stats
from sklearn.datasets import make_classification
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
warnings.filterwarnings("ignore")
X, y = make_classification(n_samples=2000, n_features=12, n_informative=6, random_state=0)
cols = [f"f{i}" for i in range(12)]
Xdf = pd.DataFrame(X, columns=cols)
Xtr, Xte, ytr, yte = train_test_split(Xdf, y, test_size=0.25, random_state=0)
rf = RandomForestClassifier(n_estimators=100, max_depth=8, random_state=0).fit(Xtr, ytr)
rng = np.random.default_rng(1)
prod = Xte.copy(); prod["f0"] = prod["f0"] + 1.5; prod["f3"] = prod["f3"] * 2.0   # 生產資料：f0 平移、f3 放大
def psi(ref, cur, bins=10):
    edges = np.quantile(ref, np.linspace(0, 1, bins + 1)); edges[0], edges[-1] = -np.inf, np.inf
    r = np.histogram(ref, edges)[0] / len(ref) + 1e-6; c = np.histogram(cur, edges)[0] / len(cur) + 1e-6
    return float(np.sum((c - r) * np.log(c / r)))
rows = [{"feature": c, "psi": round(psi(Xtr[c], prod[c]), 3), "ks_p": round(stats.ks_2samp(Xtr[c], prod[c]).pvalue, 4)} for c in cols]
print(pd.DataFrame(rows).sort_values("psi", ascending=False).head(5).to_string())
p_ref = rf.predict_proba(Xte)[:, 1]; p_prod = rf.predict_proba(prod)[:, 1]
print(f"prediction drift: mean prob ref {p_ref.mean():.3f} → prod {p_prod.mean():.3f}; positive rate {np.mean(p_ref>0.5):.3f} → {np.mean(p_prod>0.5):.3f}; PSI {psi(p_ref, p_prod):.3f}")
print(f"accuracy ref {rf.score(Xte, yte):.3f} → prod (labels unchanged) {rf.score(prod, yte):.3f}")
t0 = time.time()
try:
    from evidently import Report
    from evidently.presets import DataDriftPreset
    from evidently import Dataset, DataDefinition
    ref_ds = Dataset.from_pandas(Xtr, data_definition=DataDefinition(numerical_columns=cols))
    cur_ds = Dataset.from_pandas(prod, data_definition=DataDefinition(numerical_columns=cols))
    rep = Report([DataDriftPreset()])
    snap = rep.run(cur_ds, ref_ds)
    d = snap.dict()
    metrics = d["metrics"]
    print("evidently top keys:", list(d.keys()), "n metrics:", len(metrics))
    print("metric[0] keys:", list(metrics[0].keys()))
    for m in metrics[:14]:
        print("  ", m["metric_name"], "|", {k: v for k, v in m["config"].items() if k in ("column", "method", "threshold")}, "→", str(m["value"])[:60])
    html = snap.get_html_str() if hasattr(snap, "get_html_str") else None
    print("html length:", len(html) if html else None, "in", round(time.time()-t0, 1), "s")
except Exception as e:
    import traceback; traceback.print_exc()
