# 第 05 課壓軸 spike：Dagster 資產管線 × MLflow——訓練資產記 run、評估資產、asset check 當品質閘、通過才移 champion alias
# /// script
# requires-python = ">=3.11"
# dependencies = ["dagster>=1.10", "mlflow>=3.0", "pandas", "numpy", "scikit-learn"]
# ///
import logging, tempfile, warnings
from pathlib import Path

import dagster as dg
import mlflow
import numpy as np
import pandas as pd
from mlflow import MlflowClient
from mlflow.models import infer_signature
from sklearn.datasets import make_classification
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split

warnings.filterwarnings("ignore")
logging.getLogger("mlflow").setLevel(logging.ERROR)
QUIET = {"loggers": {"console": {"config": {"log_level": "WARNING"}}}}
WORK = Path(tempfile.mkdtemp(prefix="mlops-pipeline-"))
MODEL_NAME = "churn-clf"


class MlflowResource(dg.ConfigurableResource):
    tracking_uri: str
    experiment: str

    def setup(self):
        mlflow.set_tracking_uri(self.tracking_uri)
        if mlflow.get_experiment_by_name(self.experiment) is None:
            mlflow.create_experiment(self.experiment, artifact_location=str(WORK / "artifacts"))
        mlflow.set_experiment(self.experiment)


class TrainConfig(dg.Config):
    model: str = "rf"          # rf | logreg
    max_depth: int = 8
    drift: float = 0.0         # 模擬資料漂移：把特徵加噪音


@dg.asset(group_name="data")
def churn_data(config: TrainConfig) -> pd.DataFrame:
    X, y = make_classification(n_samples=2000, n_features=12, n_informative=6, random_state=0)
    df = pd.DataFrame(X, columns=[f"f{i}" for i in range(12)])
    if config.drift > 0:
        rng = np.random.default_rng(1)
        df = df + rng.normal(0, config.drift, df.shape)
    df["label"] = y
    return df


@dg.asset(group_name="data")
def train_test(churn_data: pd.DataFrame) -> dict:
    tr, te = train_test_split(churn_data, test_size=0.25, random_state=0)
    return {"train": tr, "test": te}


@dg.asset(group_name="model")
def trained_model(context: dg.AssetExecutionContext, config: TrainConfig, mlflow_res: MlflowResource, train_test: dict) -> str:
    mlflow_res.setup()
    tr = train_test["train"]; X, y = tr.drop(columns="label"), tr["label"]
    clf = RandomForestClassifier(n_estimators=100, max_depth=config.max_depth, random_state=0) if config.model == "rf" else LogisticRegression(max_iter=1000)
    with mlflow.start_run(run_name=f"dagster-{context.run_id[:8]}") as run:
        mlflow.log_params({"model": config.model, "max_depth": config.max_depth, "dagster_run": context.run_id})
        clf.fit(X, y)
        info = mlflow.sklearn.log_model(clf, name="churn_model", signature=infer_signature(X, clf.predict_proba(X)[:, 1]), input_example=X.head(3))
        mlflow.set_tag("dagster.asset", "trained_model")
    context.add_output_metadata({"mlflow_run": run.info.run_id, "model_uri": info.model_uri})
    return info.model_uri


@dg.asset(group_name="model")
def model_metrics(context: dg.AssetExecutionContext, mlflow_res: MlflowResource, trained_model: str, train_test: dict) -> dict:
    mlflow_res.setup()
    te = train_test["test"]
    with mlflow.start_run(run_name="evaluate"):
        res = mlflow.models.evaluate(trained_model, te, targets="label", model_type="classifier")
    m = {k: float(v) for k, v in res.metrics.items() if k in ("roc_auc", "accuracy_score", "f1_score", "recall_score")}
    context.add_output_metadata({k: dg.MetadataValue.float(v) for k, v in m.items()})
    return m


@dg.asset_check(asset=model_metrics, blocking=True, description="品質閘：AUC 必須 ≥ 0.95 而且不輸目前 champion")
def quality_gate(mlflow_res: MlflowResource, model_metrics: dict) -> dg.AssetCheckResult:
    mlflow_res.setup()
    client = MlflowClient()
    try:
        champ = client.get_model_version_by_alias(MODEL_NAME, "champion")
        champ_run = mlflow.get_run(champ.run_id)
        champ_auc = champ_run.data.metrics.get("eval_auc", 0.0)
    except Exception:
        champ_auc = 0.0
    auc = model_metrics["roc_auc"]
    ok = auc >= 0.95 and auc >= champ_auc
    return dg.AssetCheckResult(passed=ok, severity=dg.AssetCheckSeverity.ERROR, metadata={"auc": auc, "champion_auc": champ_auc, "min_auc": 0.95})


@dg.asset(group_name="deploy", deps=[model_metrics])
def registered_champion(context: dg.AssetExecutionContext, mlflow_res: MlflowResource, trained_model: str, model_metrics: dict) -> str:
    mlflow_res.setup()
    client = MlflowClient()
    mv = mlflow.register_model(trained_model, MODEL_NAME)
    # 把評估 AUC 也記到訓練 run 上，之後 gate 才比得到
    src_run = client.get_model_version(MODEL_NAME, mv.version).run_id
    client.log_metric(src_run, "eval_auc", model_metrics["roc_auc"])
    client.set_registered_model_alias(MODEL_NAME, "champion", mv.version)
    client.set_model_version_tag(MODEL_NAME, mv.version, "dagster_run", context.run_id)
    context.add_output_metadata({"version": int(mv.version), "auc": model_metrics["roc_auc"]})
    return f"models:/{MODEL_NAME}@champion -> v{mv.version}"


ASSETS = [churn_data, train_test, trained_model, model_metrics, quality_gate, registered_champion]
RES = {"mlflow_res": MlflowResource(tracking_uri=f"sqlite:///{WORK}/mlflow.db", experiment="churn-pipeline")}
inst = dg.DagsterInstance.ephemeral()

def run(**cfg):
    rc = {**QUIET, "ops": {a: {"config": cfg} for a in ("churn_data", "trained_model")}} if cfg else QUIET
    r = dg.materialize(ASSETS, resources=RES, instance=inst, run_config=rc, raise_on_error=False)
    mats = [e.asset_key.to_user_string() for e in r.get_asset_materialization_events()]
    checks = {e.check_name: (e.passed, {k: v.value for k, v in e.metadata.items()}) for e in r.get_asset_check_evaluations()}
    print("success", r.success, "| materialized", mats, "| checks", checks)
    return r

print("=== run 1: rf depth 8（第一次，沒有 champion）")
run()
print("=== run 2: logreg（比 champion 弱 → gate 擋）")
run(model="logreg", max_depth=8)
print("=== run 3: rf depth 16（更好 → 晉升 v2）")
run(model="rf", max_depth=16)
print("=== run 4: rf depth 16 + drift 1.5（資料漂移 → AUC 掉 → gate 擋）")
run(model="rf", max_depth=16, drift=1.5)
c = MlflowClient(); mlflow.set_tracking_uri(RES["mlflow_res"].tracking_uri)
print("registry:", [(v.version, c.get_model_version(MODEL_NAME, v.version).aliases) for v in c.search_model_versions(f"name='{MODEL_NAME}'")])
print("runs:", len(mlflow.search_runs(experiment_names=["churn-pipeline"])))
# partitions + schedule sketch
daily = dg.DailyPartitionsDefinition(start_date="2026-09-01")
job = dg.define_asset_job("train_job", selection=ASSETS[:4] + [ASSETS[5]])
print("job ok:", job.name)
