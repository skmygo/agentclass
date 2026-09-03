# 測驗題用的真實錯誤訊息：同 run 改 param、filter_string 少引號、log_artifact 不存在的檔
# /// script
# requires-python = ">=3.11"
# dependencies = ["dagster>=1.10", "mlflow>=3.0", "pandas", "numpy", "scikit-learn"]
# ///
import tempfile, logging
from pathlib import Path
import mlflow
logging.getLogger("mlflow").setLevel(logging.ERROR)
W = Path(tempfile.mkdtemp()); mlflow.set_tracking_uri(f"sqlite:///{W}/m.db")
mlflow.create_experiment("e", artifact_location=str(W/"art")); mlflow.set_experiment("e")
with mlflow.start_run() as r:
    mlflow.log_param("max_depth", 4)
    try:
        mlflow.log_param("max_depth", 8)
    except Exception as e:
        print("PARAM ERR:", type(e).__name__, "|", str(e)[:400])
    try:
        mlflow.log_artifact("config.yaml")
    except Exception as e:
        print("ARTIFACT ERR:", type(e).__name__, "|", str(e)[:300])
    mlflow.log_metric("auc", 0.9)
for q in ["metrics.auc > 0.95 and params.model = rf", "auc > 0.9", "metrics.auc > 0.9 and tags.stage == 'sweep'"]:
    try:
        df = mlflow.search_runs(experiment_names=["e"], filter_string=q)
        print("OK:", q, len(df))
    except Exception as e:
        print("QUERY ERR:", q, "|", type(e).__name__, "|", str(e)[:400])
# 沒有 set_experiment 直接 start_run → Default experiment
# start_run 內再 start_run 不加 nested
with mlflow.start_run():
    try:
        with mlflow.start_run():
            pass
    except Exception as e:
        print("NESTED ERR:", type(e).__name__, "|", str(e)[:400])
