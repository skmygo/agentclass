# 候選課 spike：模型可解釋性——SHAP TreeExplainer（全域重要度、單筆解釋、依賴圖）＋ sklearn permutation importance
# /// script
# requires-python = ">=3.11"
# dependencies = ["shap>=0.46", "scikit-learn", "pandas", "numpy", "matplotlib"]
# ///
import time, warnings
import numpy as np, pandas as pd, shap
from sklearn.datasets import make_classification
from sklearn.ensemble import RandomForestClassifier
from sklearn.inspection import permutation_importance
from sklearn.model_selection import train_test_split
warnings.filterwarnings("ignore")
print("shap", shap.__version__)
X, y = make_classification(n_samples=2000, n_features=12, n_informative=6, random_state=0)
cols=[f"f{i}" for i in range(12)]; Xdf=pd.DataFrame(X, columns=cols)
Xtr, Xte, ytr, yte = train_test_split(Xdf, y, test_size=0.25, random_state=0)
rf = RandomForestClassifier(n_estimators=100, max_depth=8, random_state=0).fit(Xtr, ytr)
t0=time.time(); ex = shap.TreeExplainer(rf); sv = ex.shap_values(Xte.head(300)); print("tree shap 300 rows:", round(time.time()-t0,2), "s", type(sv), getattr(sv,'shape',None) if not isinstance(sv,list) else [a.shape for a in sv])
vals = sv[:, :, 1] if not isinstance(sv, list) else sv[1]
imp = pd.Series(np.abs(vals).mean(0), index=cols).sort_values(ascending=False)
print("global mean|shap| top5:", imp.head(5).round(4).to_dict())
print("expected_value:", ex.expected_value)
i=0; row = pd.Series(vals[i], index=cols).sort_values(key=abs, ascending=False)
print("row0 prob:", round(rf.predict_proba(Xte.head(1))[0,1],3), "| base", round(float(np.atleast_1d(ex.expected_value)[-1]),3), "| top contributions:", row.head(4).round(3).to_dict(), "| sum check", round(float(np.atleast_1d(ex.expected_value)[-1] + vals[i].sum()),3))
t0=time.time(); pi = permutation_importance(rf, Xte, yte, n_repeats=5, random_state=0, scoring="roc_auc"); print("permutation importance:", round(time.time()-t0,1), "s", pd.Series(pi.importances_mean, index=cols).sort_values(ascending=False).head(5).round(4).to_dict())
print("rf builtin importance top5:", pd.Series(rf.feature_importances_, index=cols).sort_values(ascending=False).head(5).round(4).to_dict())
# Explanation API
t0=time.time(); expl = ex(Xte.head(100)); print("Explanation obj:", expl.shape, round(time.time()-t0,2), "s")
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
shap.summary_plot(vals, Xte.head(300), show=False, plot_size=(6.2, 4)); plt.savefig("/tmp/shap_summary.png"); print("summary plot ok")
plt.figure(); shap.plots.waterfall(expl[0, :, 1], show=False); plt.savefig("/tmp/shap_waterfall.png", bbox_inches="tight"); print("waterfall ok")
