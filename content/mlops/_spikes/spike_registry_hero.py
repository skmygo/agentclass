# hero 用：v1（logreg）與 v2（rf depth8 n100）對 test 前 4 筆的機率（跟 notebook 同 seed）
# /// script
# requires-python = ">=3.11"
# dependencies = ["mlflow>=3.0", "scikit-learn", "pandas", "matplotlib", "numpy"]
# ///
import pandas as pd
from sklearn.datasets import make_classification
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
X, y = make_classification(n_samples=2000, n_features=12, n_informative=6, random_state=0)
cols=[f"f{i}" for i in range(12)]
Xtr, Xte, ytr, yte = train_test_split(pd.DataFrame(X, columns=cols), y, test_size=0.25, random_state=0)
v1 = LogisticRegression(max_iter=1000).fit(Xtr, ytr); v2 = RandomForestClassifier(n_estimators=100, max_depth=8, random_state=0).fit(Xtr, ytr)
h = Xte.head(8)
print("idx", list(h.index)); print("actual", list(yte[:8]))
print("v1", [round(p,3) for p in v1.predict_proba(h)[:,1]]); print("v2", [round(p,3) for p in v2.predict_proba(h)[:,1]])
