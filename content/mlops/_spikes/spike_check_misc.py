# 零碎確認：dagster 日誌靜音、automation 條件評估、mlflow schema 錯誤全文、alias 讀法
# /// script
# requires-python = ">=3.11"
# dependencies = ["dagster>=1.10", "mlflow>=3.0", "pandas", "numpy", "scikit-learn"]
# ///
import logging, tempfile
from pathlib import Path
import dagster as dg
import pandas as pd
logging.getLogger("dagster").setLevel(logging.WARNING)

@dg.asset
def a() -> int:
    return 1
@dg.asset(automation_condition=dg.AutomationCondition.eager())
def b(a: int) -> int:
    return a + 1
defs = dg.Definitions(assets=[a, b])
inst = dg.DagsterInstance.ephemeral()
from dagster import evaluate_automation_conditions
ev = evaluate_automation_conditions(defs=defs, instance=inst)
print("eval0 requested:", ev.total_requested)
dg.materialize([a], instance=inst, run_config={"loggers": {"console": {"config": {"log_level": "WARNING"}}}})
print("--- after quiet materialize")
ev2 = evaluate_automation_conditions(defs=defs, instance=inst, cursor=ev.cursor)
print("eval1 requested:", ev2.total_requested, [x for x in dir(ev2) if not x.startswith("_")]); print("requested b:", ev2.get_num_requested(dg.AssetKey("b")), ev2.get_requested_partitions(dg.AssetKey("b")))
# 用 instance 跑 b（模擬 daemon 執行 run request）
r = dg.materialize([a, b], instance=inst, selection=[b])
print("b value:", r.asset_value("b"))
ev3 = evaluate_automation_conditions(defs=defs, instance=inst, cursor=ev2.cursor)
print("eval2 requested:", ev3.total_requested)
# eager 的條件描述
cond = dg.AutomationCondition.eager()
print("eager label:", cond.get_label() if hasattr(cond, "get_label") else None)
print("eager repr:", cond.description if hasattr(cond, "description") else cond)
# 記錄 run 事件到 instance 後怎麼查
runs = inst.get_runs()
print("runs on instance:", len(runs), [x.status.value for x in runs])
mat = inst.get_latest_materialization_event(dg.AssetKey("b"))
print("latest b materialization run:", mat.run_id[:8] if mat else None)
# 這裡再做一次「不靜音」看 log 是不是 stderr
print("---- mlflow")
import mlflow
from mlflow.models import infer_signature
from sklearn.linear_model import LogisticRegression
W = Path(tempfile.mkdtemp())
mlflow.set_tracking_uri(f"sqlite:///{W}/m.db")
mlflow.create_experiment("e", artifact_location=str(W / "art")); mlflow.set_experiment("e")
X = pd.DataFrame({"f0": [0.0, 1.0, 2.0, 3.0], "f1": [1.0, 0.0, 1.0, 0.0]}); y = [0, 1, 0, 1]
m = LogisticRegression().fit(X, y)
with mlflow.start_run():
    info = mlflow.sklearn.log_model(m, name="mdl", signature=infer_signature(X, m.predict(X)))
p = mlflow.pyfunc.load_model(info.model_uri)
try:
    p.predict(X.drop(columns=["f1"]))
except Exception as e:
    print("MISSING COL ERR:", str(e)[-400:])
try:
    p.predict(X.assign(f1=["a", "b", "c", "d"]))
except Exception as e:
    print("TYPE ERR:", str(e)[-500:])
mv = mlflow.register_model(info.model_uri, "mdl-reg")
c = mlflow.MlflowClient()
c.set_registered_model_alias("mdl-reg", "champion", mv.version)
print("get_model_version aliases:", c.get_model_version("mdl-reg", mv.version).aliases)
print("search_model_versions aliases:", [v.aliases for v in c.search_model_versions("name='mdl-reg'")])
print("registered:", c.get_registered_model("mdl-reg").aliases)
# 沒有 signature 的模型會警告？
with mlflow.start_run():
    try:
        info2 = mlflow.sklearn.log_model(m, name="nosig")
        print("no-signature log ok, signature:", info2.signature)
    except Exception as e:
        print("nosig err", e)
