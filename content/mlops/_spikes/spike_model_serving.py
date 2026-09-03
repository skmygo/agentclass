# 第 06 課候選 spike：模型上線——pyfunc 包進 FastAPI（uvicorn thread）＋ `mlflow models serve` 子行程 /invocations
# /// script
# requires-python = ">=3.11"
# dependencies = ["mlflow>=3.0", "scikit-learn", "pandas", "numpy", "fastapi", "uvicorn", "httpx"]
# ///
import logging, socket, subprocess, sys, tempfile, threading, time, warnings
from pathlib import Path
import httpx, mlflow, pandas as pd, uvicorn
from fastapi import FastAPI
from mlflow.models import infer_signature
from sklearn.datasets import make_classification
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
warnings.filterwarnings("ignore"); logging.getLogger("mlflow").setLevel(logging.ERROR)
WORK = Path(tempfile.mkdtemp(prefix="serving-"))
mlflow.set_tracking_uri(f"sqlite:///{WORK}/mlflow.db")
mlflow.create_experiment("serving", artifact_location=str(WORK / "art")); mlflow.set_experiment("serving")
X, y = make_classification(n_samples=2000, n_features=12, n_informative=6, random_state=0)
cols = [f"f{i}" for i in range(12)]
Xtr, Xte, ytr, yte = train_test_split(pd.DataFrame(X, columns=cols), y, test_size=0.25, random_state=0)
rf = RandomForestClassifier(n_estimators=100, max_depth=8, random_state=0).fit(Xtr, ytr)
with mlflow.start_run():
    info = mlflow.sklearn.log_model(rf, name="m", signature=infer_signature(Xtr, rf.predict_proba(Xtr)[:, 1]), input_example=Xtr.head(2), pyfunc_predict_fn="predict_proba")
mlflow.register_model(info.model_uri, "churn-clf")
mlflow.MlflowClient().set_registered_model_alias("churn-clf", "champion", 1)

def free_port():
    s = socket.socket(); s.bind(("127.0.0.1", 0)); p = s.getsockname()[1]; s.close(); return p

# A) 自己包 FastAPI
model = mlflow.pyfunc.load_model("models:/churn-clf@champion")
app = FastAPI()
@app.post("/predict")
def predict(rows: list[dict]):
    df = pd.DataFrame(rows)
    p = model.predict(df)
    return {"prob": [float(v[1]) for v in p], "model": "churn-clf@champion"}
port_a = free_port()
th = threading.Thread(target=lambda: uvicorn.run(app, host="127.0.0.1", port=port_a, log_level="error"), daemon=True); th.start()
for _ in range(50):
    try: httpx.get(f"http://127.0.0.1:{port_a}/docs", timeout=1); break
    except Exception: time.sleep(0.2)
r = httpx.post(f"http://127.0.0.1:{port_a}/predict", json=Xte.head(3).to_dict("records"), timeout=10)
print("A fastapi:", r.status_code, r.json())
t0 = time.time(); n = 50
for _ in range(n): httpx.post(f"http://127.0.0.1:{port_a}/predict", json=Xte.head(1).to_dict("records"), timeout=10)
print(f"A latency per request ~{(time.time()-t0)/n*1000:.1f} ms")

# B) mlflow models serve（local env）
port_b = free_port()
proc = subprocess.Popen([sys.executable, "-m", "mlflow", "models", "serve", "-m", "models:/churn-clf@champion", "-p", str(port_b), "--env-manager", "local", "--host", "127.0.0.1"],
                        env={**__import__("os").environ, "MLFLOW_TRACKING_URI": mlflow.get_tracking_uri()}, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
ok = False
for _ in range(120):
    try:
        if httpx.get(f"http://127.0.0.1:{port_b}/ping", timeout=1).status_code == 200: ok = True; break
    except Exception: time.sleep(0.5)
print("B serve up:", ok, "after", _ * 0.5, "s")
if ok:
    payload = {"dataframe_split": Xte.head(3).to_dict("split")}
    payload["dataframe_split"].pop("index", None)
    r = httpx.post(f"http://127.0.0.1:{port_b}/invocations", json=payload, timeout=30)
    print("B invocations:", r.status_code, str(r.json())[:200])
    bad = {"dataframe_split": {"columns": cols[:-1], "data": Xte.head(1).values[:, :-1].tolist()}}
    r2 = httpx.post(f"http://127.0.0.1:{port_b}/invocations", json=bad, timeout=30)
    print("B missing col:", r2.status_code, r2.text[:300])
    r3 = httpx.get(f"http://127.0.0.1:{port_b}/version", timeout=5); print("B version:", r3.text[:60])
proc.terminate()
try: out = proc.communicate(timeout=10)[0]
except Exception: proc.kill(); out = ""
print("B log tail:", out[-300:].replace("\n", " | "))
# C) batch scoring
t0 = time.time(); p = model.predict(Xte); print(f"C batch 500 rows in {(time.time()-t0)*1000:.1f} ms, shape {p.shape}")
