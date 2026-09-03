# 測驗題用：檔案模式（./mlruns）呼叫 register_model 的真實錯誤
# /// script
# requires-python = ">=3.11"
# dependencies = ["mlflow>=3.0", "scikit-learn", "pandas", "matplotlib", "numpy"]
# ///
import tempfile, logging, os
import mlflow
logging.getLogger("mlflow").setLevel(logging.ERROR)
d = tempfile.mkdtemp(); os.chdir(d)
mlflow.set_tracking_uri(f"file:{d}/mlruns")
from sklearn.linear_model import LogisticRegression
import numpy as np
m = LogisticRegression().fit(np.random.rand(20, 3), np.random.randint(0, 2, 20))
with mlflow.start_run():
    info = mlflow.sklearn.log_model(m, name="m")
try:
    mlflow.register_model(info.model_uri, "x")
except Exception as e:
    print("REGISTER ERR:", type(e).__name__, "|", str(e)[:500])
try:
    mlflow.pyfunc.load_model("models:/x@champion")
except Exception as e:
    print("LOAD ALIAS ERR (file store):", type(e).__name__, "|", str(e)[:300])
