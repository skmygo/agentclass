# ONNX 課的錯誤原文蒐集（測驗題用）：型別／形狀／轉換參數的四種真實錯誤
# /// script
# requires-python = ">=3.11"
# dependencies = ["skl2onnx", "onnxruntime", "onnx", "scikit-learn", "numpy"]
# ///
import warnings

import numpy as np
import onnx
import onnxruntime as ort
from skl2onnx import to_onnx
from sklearn.datasets import make_classification
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

warnings.filterwarnings("ignore")


def show(tag, fn):
    try:
        out = fn()
        print(f"[{tag}] 沒報錯 → {str(out)[:200]}")
    except Exception as e:  # noqa: BLE001
        print(f"[{tag}] {type(e).__name__}: {str(e)[:300]}")
    print("-" * 70)


print("onnxruntime", ort.__version__, "onnx", onnx.__version__)
X, y = make_classification(n_samples=2000, n_features=12, n_informative=6, random_state=0)
X_tr, X_te, y_tr, _ = train_test_split(X.astype(np.float32), y, test_size=0.25, random_state=0)
rf = RandomForestClassifier(n_estimators=100, max_depth=8, random_state=0).fit(X_tr, y_tr)

onx = to_onnx(rf, X_tr[:1], options={id(rf): {"zipmap": False}})
sess = ort.InferenceSession(onx.SerializeToString(), providers=["CPUExecutionProvider"])
in_name = sess.get_inputs()[0].name

show("float64 餵進去", lambda: sess.run(None, {in_name: X_te.astype(np.float64)}))
show("少一欄", lambda: sess.run(None, {in_name: X_te[:, :11]}))
show("一維陣列（忘了 reshape）", lambda: sess.run(None, {in_name: X_te[0]}))
show("輸入名稱打錯", lambda: sess.run(None, {"input": X_te}))
show("to_onnx 沒給範例輸入", lambda: to_onnx(rf))
show("未 fit 的模型", lambda: to_onnx(RandomForestClassifier(), X_tr[:1]))

# zipmap 沒關：probabilities 變成 list of dict
onx_zip = to_onnx(rf, X_tr[:1])
sess_zip = ort.InferenceSession(onx_zip.SerializeToString(), providers=["CPUExecutionProvider"])
zip_out = sess_zip.run(None, {sess_zip.get_inputs()[0].name: X_te[:2]})
print("[zipmap 沒關] outputs:", [o.name for o in sess_zip.get_outputs()])
print("[zipmap 沒關] probabilities[0] =", zip_out[1][0], "type:", type(zip_out[1]).__name__)
show("zipmap 沒關再當 ndarray 切欄", lambda: np.asarray(zip_out[1])[:, 1])
print("[zipmap 關掉] probabilities[0] =", sess.run(None, {in_name: X_te[:2]})[1][0])
print("-" * 70)

print("checker:", onnx.checker.check_model(onx) or "check_model 通過（回 None）")
node_types = {}
for node in onx.graph.node:
    node_types[node.op_type] = node_types.get(node.op_type, 0) + 1
print("節點型別統計:", node_types)
print("opset:", [(o.domain or "''", o.version) for o in onx.opset_import])
