# MLflow Models / Registry spike：signature、log_model、pyfunc 自訂模型、register、alias、載回推論、evaluate
# /// script
# requires-python = ">=3.11"
# dependencies = ["mlflow>=3.0", "scikit-learn", "pandas", "matplotlib", "numpy"]
# ///
import os
import pickle
import tempfile
from pathlib import Path

import mlflow
import pandas as pd
from mlflow import MlflowClient
from mlflow.models import infer_signature
from sklearn.datasets import make_classification
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split

WORK = Path(tempfile.mkdtemp(prefix="mlflow-registry-"))
mlflow.set_tracking_uri(f"sqlite:///{WORK}/mlflow.db")
exp_id = mlflow.create_experiment("churn-registry", artifact_location=str(WORK / "artifacts"))
mlflow.set_experiment("churn-registry")

X, y = make_classification(n_samples=2000, n_features=12, n_informative=6, random_state=0)
cols = [f"f{i}" for i in range(12)]
Xdf = pd.DataFrame(X, columns=cols)
Xtr, Xte, ytr, yte = train_test_split(Xdf, y, test_size=0.25, random_state=0)

# 1) signature + log_model
lr = LogisticRegression(max_iter=1000).fit(Xtr, ytr)
sig = infer_signature(Xtr, lr.predict_proba(Xtr)[:, 1])
print("signature:", sig)
with mlflow.start_run(run_name="v1-logreg") as r1:
    info1 = mlflow.sklearn.log_model(lr, name="churn_model", signature=sig, input_example=Xtr.head(3))
    mlflow.log_metric("auc", roc_auc_score(yte, lr.predict_proba(Xte)[:, 1]))
print("model_uri:", info1.model_uri, "model_id:", info1.model_id)
print("flavors:", list(info1.flavors))
# 2) 載回 pyfunc 推論
loaded = mlflow.pyfunc.load_model(info1.model_uri)
print("pyfunc predict:", loaded.predict(Xte.head(3)))
try:
    loaded.predict(Xte.head(3).drop(columns=["f11"]))
except Exception as e:
    print("schema err:", type(e).__name__, str(e)[:300])
# 3) 磁碟上的模型目錄
mdir = mlflow.artifacts.download_artifacts(info1.model_uri, dst_path=str(WORK / "dl"))
print("model dir files:", sorted(os.listdir(mdir)))
print(open(os.path.join(mdir, "MLmodel")).read()[:900])

# 4) 註冊 + alias
mv1 = mlflow.register_model(info1.model_uri, "churn-clf")
print("registered:", mv1.name, "version", mv1.version, mv1.status)
rf = RandomForestClassifier(n_estimators=100, max_depth=8, random_state=0).fit(Xtr, ytr)
with mlflow.start_run(run_name="v2-rf") as r2:
    info2 = mlflow.sklearn.log_model(rf, name="churn_model", signature=infer_signature(Xtr, rf.predict_proba(Xtr)[:, 1]), input_example=Xtr.head(3))
    auc2 = roc_auc_score(yte, rf.predict_proba(Xte)[:, 1])
    mlflow.log_metric("auc", auc2)
mv2 = mlflow.register_model(info2.model_uri, "churn-clf")
c = MlflowClient()
c.set_registered_model_alias("churn-clf", "champion", mv1.version)
c.set_registered_model_alias("churn-clf", "challenger", mv2.version)
c.set_model_version_tag("churn-clf", mv2.version, "validated", "false")
c.update_model_version("churn-clf", mv2.version, description="RandomForest depth 8")
for v in c.search_model_versions("name='churn-clf'"):
    print("version", v.version, "aliases", v.aliases, "tags", v.tags, "run", v.run_id[:8], "status", v.status)
champ = mlflow.pyfunc.load_model("models:/churn-clf@champion")
print("champion predicts:", champ.predict(Xte.head(2)))
print("champion metadata run_id:", champ.metadata.run_id, "flavor:", list(champ.metadata.flavors.keys()))
c.set_registered_model_alias("churn-clf", "champion", mv2.version)
print("after promote:", c.get_model_version_by_alias("churn-clf", "champion").version)
try:
    c.transition_model_version_stage("churn-clf", mv1.version, "Production")
    print("stage api still works")
except Exception as e:
    print("stage err:", type(e).__name__, str(e)[:160])
try:
    mlflow.pyfunc.load_model("models:/churn-clf@nope")
except Exception as e:
    print("bad alias err:", type(e).__name__, str(e)[:200])

# 5) 自訂 pyfunc：前處理 + 門檻
class ChurnWrapper(mlflow.pyfunc.PythonModel):
    def __init__(self, threshold=0.5):
        self.threshold = threshold
    def load_context(self, context):
        with open(context.artifacts["sk_model"], "rb") as f:
            self.model = pickle.load(f)
    def predict(self, context, model_input, params=None):
        thr = (params or {}).get("threshold", self.threshold)
        p = self.model.predict_proba(model_input)[:, 1]
        return pd.DataFrame({"prob": p, "churn": (p >= thr).astype(int)})

pk = WORK / "rf.pkl"
pk.write_bytes(pickle.dumps(rf))
sig3 = infer_signature(Xtr.head(3), pd.DataFrame({"prob": [0.1], "churn": [0]}), params={"threshold": 0.5})
print("sig3:", sig3)
with mlflow.start_run(run_name="v3-wrapper"):
    info3 = mlflow.pyfunc.log_model(name="churn_model", python_model=ChurnWrapper(0.5), artifacts={"sk_model": str(pk)}, signature=sig3, input_example=Xtr.head(3), pip_requirements=["scikit-learn", "pandas"])
w = mlflow.pyfunc.load_model(info3.model_uri)
print(w.predict(Xte.head(3)))
print(w.predict(Xte.head(3), params={"threshold": 0.9}))

# 6) evaluate
eval_df = Xte.copy(); eval_df["label"] = yte
with mlflow.start_run(run_name="eval-v2"):
    res = mlflow.models.evaluate(info2.model_uri, eval_df, targets="label", model_type="classifier")
print("eval metrics:", {k: round(v, 3) for k, v in res.metrics.items() if isinstance(v, float)})
print("eval artifacts:", list(res.artifacts))
print("registered models:", [(m.name, [a for a in m.aliases]) for m in c.search_registered_models()])
lm = mlflow.get_logged_model(info2.model_id)
print("logged model:", lm.name, lm.model_id, lm.status, {m.key: round(m.value,3) for m in lm.metrics} if lm.metrics else None)
