# 候選課 spike：ONNX 匯出上線——skl2onnx 轉換、onnxruntime 推論、跟 sklearn 對答案、延遲比較、模型檔大小
# /// script
# requires-python = ">=3.11"
# dependencies = ["skl2onnx", "onnxruntime", "onnx", "scikit-learn", "pandas", "numpy"]
# ///
import time, tempfile, warnings
from pathlib import Path
import numpy as np, pandas as pd, onnx, onnxruntime as ort
from skl2onnx import to_onnx
from sklearn.datasets import make_classification
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
warnings.filterwarnings("ignore")
print("onnxruntime", ort.__version__, "onnx", onnx.__version__)
X, y = make_classification(n_samples=2000, n_features=12, n_informative=6, random_state=0)
Xtr, Xte, ytr, yte = train_test_split(X.astype(np.float32), y, test_size=0.25, random_state=0)
rf = RandomForestClassifier(n_estimators=100, max_depth=8, random_state=0).fit(Xtr, ytr)
W = Path(tempfile.mkdtemp())
t0=time.time(); onx = to_onnx(rf, Xtr[:1], options={id(rf): {"zipmap": False}}); print("convert:", round(time.time()-t0,2), "s")
p = W/"rf.onnx"; p.write_bytes(onx.SerializeToString()); import pickle; pk = W/"rf.pkl"; pk.write_bytes(pickle.dumps(rf))
print("sizes: onnx", p.stat().st_size, "pkl", pk.stat().st_size)
m = onnx.load(str(p)); print("opset:", [(o.domain, o.version) for o in m.opset_import][:3], "inputs:", [(i.name, [d.dim_value or d.dim_param for d in i.type.tensor_type.shape.dim]) for i in m.graph.input], "outputs:", [o.name for o in m.graph.output])
sess = ort.InferenceSession(str(p), providers=["CPUExecutionProvider"])
name = sess.get_inputs()[0].name
t0=time.time(); label, proba = sess.run(None, {name: Xte}); print("ort 500 rows:", round((time.time()-t0)*1000,2), "ms", "| proba shape", np.asarray(proba).shape)
t0=time.time(); sk = rf.predict_proba(Xte); print("sklearn 500 rows:", round((time.time()-t0)*1000,2), "ms")
print("max |diff| proba:", float(np.abs(np.asarray(proba)[:,1]-sk[:,1]).max()), "label agree:", float((np.asarray(label)==rf.predict(Xte)).mean()))
def bench(fn, n=200):
    t0=time.time(); [fn() for _ in range(n)]; return (time.time()-t0)/n*1000
one = Xte[:1]
print(f"single-row latency: ort {bench(lambda: sess.run(None, {name: one})):.3f} ms | sklearn {bench(lambda: rf.predict_proba(one)):.3f} ms")
lr = LogisticRegression(max_iter=1000).fit(Xtr, ytr); onx2 = to_onnx(lr, Xtr[:1], options={id(lr): {"zipmap": False}}); s2 = ort.InferenceSession(onx2.SerializeToString()); 
print(f"logreg single-row: ort {bench(lambda: s2.run(None, {s2.get_inputs()[0].name: one})):.3f} ms | sklearn {bench(lambda: lr.predict_proba(one)):.3f} ms")
# float64 input error
try:
    sess.run(None, {name: Xte.astype(np.float64)})
except Exception as e:
    print("dtype err:", type(e).__name__, str(e)[:160])
try:
    sess.run(None, {name: Xte[:, :11]})
except Exception as e:
    print("shape err:", type(e).__name__, str(e)[:160])
