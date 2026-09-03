# 第 06 課（model-serving）診斷素材 spike：把「上線時真的會遇到的錯」跑出真實原文，
# 供教學頁的錯誤診斷題與 notebook 的錯誤示範引用（不可杜撰錯誤訊息）。
#     uv run --script content/mlops/_spikes/spike_model_serving_errors.py
# /// script
# requires-python = ">=3.11"
# dependencies = ["mlflow>=3.0", "scikit-learn", "pandas", "numpy", "fastapi", "uvicorn", "httpx"]
# ///
import logging
import os
import socket
import subprocess
import sys
import tempfile
import threading
import time
import warnings
from pathlib import Path

import httpx
import mlflow
import pandas as pd
import uvicorn
from fastapi import FastAPI
from mlflow.models import infer_signature
from sklearn.datasets import make_classification
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

warnings.filterwarnings("ignore")
logging.getLogger("mlflow").setLevel(logging.ERROR)


def rule(title):
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


def free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


WORK = Path(tempfile.mkdtemp(prefix="serving-errors-"))
mlflow.set_tracking_uri(f"sqlite:///{WORK}/mlflow.db")
mlflow.create_experiment("serving-errors", artifact_location=str(WORK / "art"))
mlflow.set_experiment("serving-errors")
print("mlflow", mlflow.__version__, "| work dir", WORK)

X, y = make_classification(n_samples=2000, n_features=12, n_informative=6, random_state=0)
COLS = [f"f{i}" for i in range(12)]
X_train, X_test, y_train, y_test = train_test_split(
    pd.DataFrame(X, columns=COLS), y, test_size=0.25, random_state=0
)
rf = RandomForestClassifier(n_estimators=100, max_depth=8, random_state=0).fit(X_train, y_train)
with mlflow.start_run(run_name="rf"):
    INFO = mlflow.sklearn.log_model(
        rf,
        name="churn_model",
        signature=infer_signature(X_train, rf.predict_proba(X_train)),
        input_example=X_train.head(2),
        pyfunc_predict_fn="predict_proba",
    )
MV = mlflow.register_model(INFO.model_uri, "churn-clf")
client = mlflow.MlflowClient()
client.set_registered_model_alias("churn-clf", "champion", MV.version)

# ─────────────────────────────────────────────────────────────────────────────
rule("1) alias 打錯：載入端 / serve 子行程各自的訊息")
try:
    mlflow.pyfunc.load_model("models:/churn-clf@production")
except Exception as e:  # noqa: BLE001 — 教學目的：印出原文
    print("load_model  →", str(e).strip().splitlines()[-1])

_p = free_port()
_bad = subprocess.run(  # noqa: S603
    [sys.executable, "-m", "mlflow", "models", "serve", "-m", "models:/churn-clf@production",
     "-p", str(_p), "--env-manager", "local", "--host", "127.0.0.1"],
    env={**os.environ, "MLFLOW_TRACKING_URI": mlflow.get_tracking_uri()},
    capture_output=True, text=True, timeout=180, check=False,
)
print("mlflow models serve → returncode", _bad.returncode)
print("stderr 尾段:", " | ".join(x for x in (_bad.stdout + _bad.stderr).strip().splitlines()[-3:]))

# ─────────────────────────────────────────────────────────────────────────────
rule("2) port 被占用：uvicorn / OSError 的原文")
BUSY = free_port()
_hold = socket.socket()
_hold.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
_hold.bind(("127.0.0.1", BUSY))
_hold.listen(1)
try:
    socket.socket().bind(("127.0.0.1", BUSY))
except OSError as e:
    print("socket.bind →", repr(e))
_hold.close()

# ─────────────────────────────────────────────────────────────────────────────
rule("3) 自包 FastAPI：載一次 vs 每次請求都 load_model（延遲對照）")
MODEL_URI = "models:/churn-clf@champion"
_state = {"model": mlflow.pyfunc.load_model(MODEL_URI)}
app = FastAPI()


@app.post("/predict")
def _predict(rows: list[dict]):
    return {"prob": [float(v[1]) for v in _state["model"].predict(pd.DataFrame(rows))]}


@app.post("/predict_slow")
def _predict_slow(rows: list[dict]):
    m = mlflow.pyfunc.load_model(MODEL_URI)  # 反例：每個請求都重新載入模型
    return {"prob": [float(v[1]) for v in m.predict(pd.DataFrame(rows))]}


PORT_A = free_port()
threading.Thread(
    target=lambda: uvicorn.run(app, host="127.0.0.1", port=PORT_A, log_level="error"), daemon=True
).start()
for _ in range(100):
    try:
        httpx.post(f"http://127.0.0.1:{PORT_A}/predict", json=X_test.head(1).to_dict("records"), timeout=2)
        break
    except Exception:  # noqa: BLE001, S110
        time.sleep(0.1)

ONE = X_test.head(1).to_dict("records")


def bench(path, n):
    ts = []
    for _ in range(n):
        t0 = time.perf_counter()
        httpx.post(f"http://127.0.0.1:{PORT_A}{path}", json=ONE, timeout=60)
        ts.append((time.perf_counter() - t0) * 1000)
    ts.sort()
    return ts[0], ts[len(ts) // 2], ts[-1]


print("/predict      (模型載一次)   min/中位/max ms: %.1f / %.1f / %.1f" % bench("/predict", 30))
print("/predict_slow (每次都載)     min/中位/max ms: %.1f / %.1f / %.1f" % bench("/predict_slow", 10))

# ─────────────────────────────────────────────────────────────────────────────
rule("4) mlflow models serve 的 /invocations：四種 payload 寫法與三種錯誤")
PORT_B = free_port()
t_up = time.time()
proc = subprocess.Popen(  # noqa: S603
    [sys.executable, "-m", "mlflow", "models", "serve", "-m", MODEL_URI,
     "-p", str(PORT_B), "--env-manager", "local", "--host", "127.0.0.1"],
    env={**os.environ, "MLFLOW_TRACKING_URI": mlflow.get_tracking_uri()},
    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
)
UP = False
for _ in range(120):
    try:
        if httpx.get(f"http://127.0.0.1:{PORT_B}/ping", timeout=1).status_code == 200:
            UP = True
            break
    except Exception:  # noqa: BLE001, S110
        time.sleep(0.5)
print(f"serve 起來了嗎：{UP}（等了 {time.time() - t_up:.1f} 秒）")

if UP:
    def post(label, payload):
        r = httpx.post(f"http://127.0.0.1:{PORT_B}/invocations", json=payload, timeout=60)
        print(f"\n── {label} → HTTP {r.status_code}")
        print(r.text[:900])

    _split = X_test.head(2).to_dict("split")
    _split.pop("index", None)
    post("dataframe_split（拿掉 index）", {"dataframe_split": _split})
    post("dataframe_split（保留 index）", {"dataframe_split": X_test.head(2).to_dict("split")})
    post("dataframe_records", {"dataframe_records": X_test.head(2).to_dict("records")})
    post("inputs（欄名 → 值清單）", {"inputs": {c: X_test.head(2)[c].tolist() for c in COLS}})
    post("instances（純 2D 陣列、沒有欄名）", {"instances": X_test.head(2).values.tolist()})
    post("沒有信封（直接送 records list）", X_test.head(2).to_dict("records"))
    post("dataframe_records 少一欄 f11", {"dataframe_records": X_test.head(1).drop(columns=["f11"]).to_dict("records")})
    post("dataframe_split 型別錯（f0 變字串）",
         {"dataframe_split": {"columns": COLS, "data": [["x"] + X_test.head(1).values[0, 1:].tolist()]}})
    print("\n/ping →", repr(httpx.get(f"http://127.0.0.1:{PORT_B}/ping").text),
          "| /version →", repr(httpx.get(f"http://127.0.0.1:{PORT_B}/version").text))

proc.terminate()
try:
    proc.communicate(timeout=10)
except Exception:  # noqa: BLE001
    proc.kill()

# ─────────────────────────────────────────────────────────────────────────────
rule("5) 換版不重載：alias 移了，載一次的服務還在用舊模型")
_v2 = RandomForestClassifier(n_estimators=100, max_depth=2, random_state=0).fit(X_train, y_train)
with mlflow.start_run(run_name="rf-depth2"):
    _info2 = mlflow.sklearn.log_model(
        _v2, name="churn_model",
        signature=infer_signature(X_train, _v2.predict_proba(X_train)),
        input_example=X_train.head(2), pyfunc_predict_fn="predict_proba",
    )
_mv2 = mlflow.register_model(_info2.model_uri, "churn-clf")
client.set_registered_model_alias("churn-clf", "champion", _mv2.version)
_alias_v = client.get_model_version_by_alias("churn-clf", "champion").version
print(f"Registry 的 @champion 現在是 v{_alias_v}（型別 {type(_alias_v).__name__}）")
print("已載入的服務仍回 v1 的機率：", httpx.post(f"http://127.0.0.1:{PORT_A}/predict", json=ONE, timeout=30).json())
_state["model"] = mlflow.pyfunc.load_model(MODEL_URI)  # ← 這就是 /reload 要做的事
print("重載之後：                  ", httpx.post(f"http://127.0.0.1:{PORT_A}/predict", json=ONE, timeout=30).json())

print("\nDONE")
