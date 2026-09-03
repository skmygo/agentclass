# 第 05 課（壓軸 mlops-pipeline）錯誤訊息實測：測驗題與 notebook 的錯誤原文一律取自這裡的輸出。
# 跑法：uv run --script content/mlops/_spikes/spike_mlops_pipeline_errors.py
# /// script
# requires-python = ">=3.11"
# dependencies = ["dagster>=1.10", "mlflow>=3.0", "pandas", "numpy", "scikit-learn"]
# ///
import logging
import os
import tempfile
import warnings
from pathlib import Path

import dagster as dg
import mlflow
import numpy as np
import pandas as pd
from mlflow import MlflowClient
from mlflow.models import infer_signature
from sklearn.datasets import make_classification
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

warnings.filterwarnings("ignore")
logging.getLogger("mlflow").setLevel(logging.ERROR)
QUIET = {"loggers": {"console": {"config": {"log_level": "CRITICAL"}}}}
WORK = Path(tempfile.mkdtemp(prefix="mlops-pipeline-err-"))
os.chdir(WORK)  # MLflow 3.15 的預設 tracking uri 是「cwd 的 mlflow.db」——別讓忘了 setup() 的示範髒了 repo
MODEL_NAME = "churn-clf"
TRACKING = f"sqlite:///{WORK}/pipeline.db"


def show(title: str, err: BaseException) -> None:
    print(f"\n=== {title}")
    print(f"{type(err).__name__}: {str(err)[:900]}")


class MlflowResource(dg.ConfigurableResource):
    tracking_uri: str
    experiment: str

    def setup(self):
        mlflow.set_tracking_uri(self.tracking_uri)
        if mlflow.get_experiment_by_name(self.experiment) is None:
            mlflow.create_experiment(self.experiment, artifact_location=str(WORK / "artifacts"))
        mlflow.set_experiment(self.experiment)


RES = {"mlflow_res": MlflowResource(tracking_uri=TRACKING, experiment="churn-pipeline")}


def frame() -> pd.DataFrame:
    X, y = make_classification(n_samples=2000, n_features=12, n_informative=6, random_state=0)
    df = pd.DataFrame(X, columns=[f"f{i}" for i in range(12)])
    df["label"] = y
    return df


# ── 1. 資產內忘了呼叫 setup()：run 靜靜寫進「別的地方」（必須第一個跑）────────
@dg.asset
def forgot_setup(mlflow_res: MlflowResource) -> str:
    # 少了 mlflow_res.setup()：這個 process 的 tracking uri 還是 MLflow 的預設值
    with mlflow.start_run(run_name="forgot") as r:
        mlflow.log_param("k", 1)
    return r.info.run_id


print("=== 1. 資產內忘了 mlflow_res.setup()（這個 process 還沒有人設過 tracking uri）")
print("   MLflow 3.15 的預設 tracking uri =", mlflow.get_tracking_uri())
_r0 = dg.materialize([forgot_setup], resources=RES, run_config=QUIET, raise_on_error=False)
print("   Dagster success =", _r0.success, "→ 沒有任何錯誤，run id", str(_r0.asset_value("forgot_setup"))[:8])
mlflow.set_tracking_uri(TRACKING)
RES["mlflow_res"].setup()
print("   但管線的 tracking 裡有幾個 run：", len(mlflow.search_runs(experiment_names=["churn-pipeline"])))
print("   cwd 多出來的東西：", sorted(p.name for p in WORK.iterdir()))

# 2b. 同一個錯誤的另一種現形方式：experiment 已被設成管線那個 id，tracking 卻換了資料庫
_exp_id = mlflow.get_experiment_by_name("churn-pipeline").experiment_id
mlflow.set_tracking_uri(f"sqlite:///{WORK}/another.db")
try:
    with mlflow.start_run():
        pass
except Exception as e:  # noqa: BLE001
    show(f"1b. experiment 停在 id={_exp_id}、tracking 卻指到另一個資料庫", e)
finally:
    while mlflow.active_run():
        mlflow.end_run()


# ── 2. 資產要 resource，materialize 卻沒給 ────────────────────────────────
@dg.asset
def needs_resource(mlflow_res: MlflowResource) -> str:
    mlflow_res.setup()
    return mlflow.get_tracking_uri()


try:
    dg.materialize([needs_resource], run_config=QUIET)
except Exception as e:  # noqa: BLE001
    show("2. materialize 忘了給 resources={'mlflow_res': ...}", e)

# 給了就正常
_ok = dg.materialize([needs_resource], resources=RES, run_config=QUIET)
print("   給了 resources 之後：success =", _ok.success, "| tracking =", _ok.asset_value("needs_resource")[:24], "...")


# ── 3. alias 指到不存在的版本 / 讀不存在的 alias ──────────────────────────
mlflow.set_tracking_uri(TRACKING)
client = MlflowClient()
try:
    client.get_model_version_by_alias(MODEL_NAME, "champion")
except Exception as e:  # noqa: BLE001
    show("3. 還沒有任何 champion 就去讀它（品質閘第一次跑的處境）", e)

# 先真的註冊一版，才有 v1 可以玩
RES["mlflow_res"].setup()
_df = frame()
_tr, _te = train_test_split(_df, test_size=0.25, random_state=0)
_X, _y = _tr.drop(columns="label"), _tr["label"]
_clf = RandomForestClassifier(n_estimators=100, max_depth=8, random_state=0).fit(_X, _y)
with mlflow.start_run(run_name="err-spike"):
    _info = mlflow.sklearn.log_model(
        _clf, name="churn_model", signature=infer_signature(_X, _clf.predict_proba(_X)[:, 1])
    )
_mv = mlflow.register_model(_info.model_uri, MODEL_NAME)
client.set_registered_model_alias(MODEL_NAME, "champion", _mv.version)
print("\n   註冊好了：version", _mv.version, "| aliases =", client.get_model_version(MODEL_NAME, _mv.version).aliases)

try:
    client.set_registered_model_alias(MODEL_NAME, "champion", "99")
except Exception as e:  # noqa: BLE001
    show("4. alias 指到不存在的 version 99", e)

try:
    mlflow.pyfunc.load_model(f"models:/{MODEL_NAME}@chapmion")  # 打錯字
except Exception as e:  # noqa: BLE001
    show("5. 載入時 alias 打錯字", e)


# ── 6. gate 比得到 champion 嗎：忘了把 eval_auc 補記到訓練 run 上 ─────────
_champ = client.get_model_version_by_alias(MODEL_NAME, "champion")
_champ_run = mlflow.get_run(_champ.run_id)
print("\n=== 6. champion 訓練 run 的 metrics（沒有 log_metric 補記時）")
print("   metrics =", dict(_champ_run.data.metrics), "→ .get('eval_auc', 0.0) =", _champ_run.data.metrics.get("eval_auc", 0.0))
client.log_metric(_champ.run_id, "eval_auc", 0.9684)
print("   補記之後 =", dict(mlflow.get_run(_champ.run_id).data.metrics))


# ── 7. blocking asset check 失敗時的 run 結果與錯誤 ──────────────────────
@dg.asset
def metrics_asset() -> dict:
    return {"roc_auc": 0.8641}


@dg.asset_check(asset=metrics_asset, blocking=True)
def quality_gate(metrics_asset: dict) -> dg.AssetCheckResult:
    return dg.AssetCheckResult(passed=metrics_asset["roc_auc"] >= 0.95, metadata={"auc": metrics_asset["roc_auc"]})


@dg.asset(deps=[metrics_asset])
def downstream_deploy() -> str:
    return "deployed"


_r = dg.materialize([metrics_asset, quality_gate, downstream_deploy], run_config=QUIET, raise_on_error=False)
print("\n=== 7. blocking check 失敗（raise_on_error=False）")
print("   success =", _r.success)
print("   materialized =", [e.asset_key.to_user_string() for e in _r.get_asset_materialization_events()])
print("   checks =", {e.check_name: e.passed for e in _r.get_asset_check_evaluations()})
try:
    dg.materialize([metrics_asset, quality_gate, downstream_deploy], run_config=QUIET, raise_on_error=True)
except Exception as e:  # noqa: BLE001
    show("7b. 同一件事，raise_on_error=True 的例外", e)

# 檢查沒放進清單 → 靜靜不跑
_r2 = dg.materialize([metrics_asset, downstream_deploy], run_config=QUIET, raise_on_error=False)
print("\n=== 8. 忘了把 quality_gate 放進 materialize 清單")
print("   success =", _r2.success, "| checks =", _r2.get_asset_check_evaluations())
print("   materialized =", [e.asset_key.to_user_string() for e in _r2.get_asset_materialization_events()])


# ── 9. 資產內開了 run 卻沒關（巢狀）──────────────────────────────────────
RES["mlflow_res"].setup()
try:
    mlflow.start_run(run_name="outer")
    mlflow.start_run(run_name="inner")
except Exception as e:  # noqa: BLE001
    show("9. 同一個 process 內 start_run 沒關又開一個", e)
finally:
    while mlflow.active_run():
        mlflow.end_run()


# ── 10. evaluate 餵錯欄位名 ─────────────────────────────────────────────
try:
    with mlflow.start_run(run_name="bad-eval"):
        mlflow.models.evaluate(_info.model_uri, _te, targets="churn", model_type="classifier")
except Exception as e:  # noqa: BLE001
    show("10. evaluate 的 targets 欄位名打錯", e)
finally:
    while mlflow.active_run():
        mlflow.end_run()

# ── 11. config 欄位型別錯 ───────────────────────────────────────────────
class TrainConfig(dg.Config):
    max_depth: int = 8


@dg.asset
def cfg_asset(config: TrainConfig) -> int:
    return config.max_depth


try:
    dg.materialize(
        [cfg_asset],
        run_config={**QUIET, "ops": {"cfg_asset": {"config": {"max_depth": "deep"}}}},
        raise_on_error=True,
    )
except Exception as e:  # noqa: BLE001
    show("11. run_config 給錯型別（max_depth='deep'）", e)

print("\n=== 版本")
print("   mlflow", mlflow.__version__, "| dagster", dg.__version__, "| numpy", np.__version__)
print("   work dir:", WORK)
