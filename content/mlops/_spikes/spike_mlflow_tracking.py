# MLflow 實驗追蹤 spike：sqlite 後端、log_param/metric/artifact、autolog、nested runs、search_runs
# /// script
# requires-python = ">=3.11"
# dependencies = ["mlflow>=3.0", "scikit-learn", "pandas", "matplotlib", "numpy"]
# ///
import tempfile
import time
from pathlib import Path

import mlflow
import numpy as np
import pandas as pd
from sklearn.datasets import make_classification
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score
from sklearn.model_selection import train_test_split

print("mlflow", mlflow.__version__)
WORK = Path(tempfile.mkdtemp(prefix="mlflow-lesson-"))
mlflow.set_tracking_uri(f"sqlite:///{WORK}/mlflow.db")
print("tracking uri:", mlflow.get_tracking_uri())
exp = mlflow.set_experiment("churn-demo")
print("experiment:", exp.experiment_id, exp.name, exp.artifact_location)

X, y = make_classification(n_samples=2000, n_features=12, n_informative=6, random_state=0, class_sep=1.0)
Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.25, random_state=0)

# 1) 手動記錄
with mlflow.start_run(run_name="logreg-baseline") as run:
    C = 1.0
    mlflow.log_param("model", "logreg")
    mlflow.log_param("C", C)
    m = LogisticRegression(C=C, max_iter=1000).fit(Xtr, ytr)
    p = m.predict_proba(Xte)[:, 1]
    acc = accuracy_score(yte, p > 0.5)
    auc = roc_auc_score(yte, p)
    mlflow.log_metrics({"accuracy": acc, "auc": auc})
    mlflow.set_tag("stage", "baseline")
    # 逐步 metric（step）
    for step in range(5):
        mlflow.log_metric("fake_loss", 1 / (step + 1), step=step)
    mlflow.log_dict({"features": [f"f{i}" for i in range(12)]}, "features.json")
    mlflow.log_text("hello artifact", "notes.txt")
    print("run_id:", run.info.run_id, "acc", round(acc, 4), "auc", round(auc, 4))
    print("artifact uri:", mlflow.get_artifact_uri())

# 2) autolog
mlflow.sklearn.autolog(log_models=True)
with mlflow.start_run(run_name="rf-autolog") as run2:
    rf = RandomForestClassifier(n_estimators=100, max_depth=6, random_state=0).fit(Xtr, ytr)
    pr = rf.predict_proba(Xte)[:, 1]
    mlflow.log_metric("test_auc", roc_auc_score(yte, pr))
    mlflow.log_metric("test_accuracy", accuracy_score(yte, pr > 0.5))
mlflow.sklearn.autolog(disable=True)
r2 = mlflow.get_run(run2.info.run_id)
print("autolog params:", sorted(r2.data.params)[:8], "...", len(r2.data.params))
print("autolog metrics:", sorted(r2.data.metrics))
print("autolog tags keys:", [k for k in r2.data.tags if not k.startswith("mlflow.")])
arts = mlflow.artifacts.list_artifacts(run_id=run2.info.run_id)
print("autolog artifacts:", [a.path for a in arts])

# 3) nested runs sweep
t0 = time.time()
with mlflow.start_run(run_name="rf-sweep") as parent:
    for depth in [2, 4, 8, 16]:
        with mlflow.start_run(run_name=f"depth={depth}", nested=True):
            mlflow.log_param("max_depth", depth)
            mlflow.log_param("model", "rf")
            mm = RandomForestClassifier(n_estimators=60, max_depth=depth, random_state=0).fit(Xtr, ytr)
            pp = mm.predict_proba(Xte)[:, 1]
            mlflow.log_metrics({"accuracy": accuracy_score(yte, pp > 0.5), "auc": roc_auc_score(yte, pp), "f1": f1_score(yte, pp > 0.5)})
print("sweep took", round(time.time() - t0, 1), "s")

# 4) search_runs
df = mlflow.search_runs(experiment_names=["churn-demo"], filter_string="metrics.auc > 0.5", order_by=["metrics.auc DESC"])
cols = [c for c in df.columns if c in ("run_id", "tags.mlflow.runName", "params.max_depth", "params.model", "metrics.auc", "metrics.accuracy", "status")]
print(df[cols].to_string())
print("all columns count:", len(df.columns))
print("total runs:", len(mlflow.search_runs(experiment_names=["churn-demo"])))

# 5) 磁碟上長什麼樣
for pth in sorted(WORK.rglob("*"))[:40]:
    print("  ", pth.relative_to(WORK))
# 6) client
from mlflow import MlflowClient
c = MlflowClient()
hist = c.get_metric_history(run.info.run_id, "fake_loss")
print("metric history:", [(h.step, round(h.value, 3)) for h in hist])
print("experiments:", [e.name for e in c.search_experiments()])
# logged models (MLflow 3)
try:
    lms = mlflow.search_logged_models(experiment_ids=[exp.experiment_id])
    print("logged models:", type(lms), getattr(lms, "shape", None))
    print(lms[[c for c in lms.columns if c in ("model_id", "name", "source_run_id")]].to_string() if hasattr(lms, "columns") else lms)
except Exception as e:
    print("search_logged_models err:", e)
