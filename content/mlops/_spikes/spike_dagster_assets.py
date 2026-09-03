# Dagster 軟體定義資產 spike：@asset、deps、materialize、metadata、asset_check、IO manager、Definitions
# /// script
# requires-python = ">=3.11"
# dependencies = ["dagster>=1.10", "pandas", "scikit-learn", "numpy"]
# ///
import dagster as dg
import pandas as pd
import numpy as np

print("dagster", dg.__version__)


@dg.asset(description="原始訂單資料（模擬）", group_name="raw")
def raw_orders() -> pd.DataFrame:
    rng = np.random.default_rng(0)
    n = 500
    return pd.DataFrame({
        "order_id": range(n),
        "amount": rng.gamma(2.0, 300, n).round(0),
        "customer": rng.integers(1, 60, n),
        "returned": rng.random(n) < 0.08,
    })


@dg.asset(group_name="clean")
def clean_orders(context: dg.AssetExecutionContext, raw_orders: pd.DataFrame) -> pd.DataFrame:
    df = raw_orders[raw_orders["amount"] > 0].copy()
    context.log.info(f"kept {len(df)} / {len(raw_orders)} rows")
    context.add_output_metadata({"rows": len(df), "preview": dg.MetadataValue.md(df.head().to_markdown())})
    return df


@dg.asset(group_name="features")
def customer_features(clean_orders: pd.DataFrame) -> pd.DataFrame:
    g = clean_orders.groupby("customer").agg(n_orders=("order_id", "count"), total=("amount", "sum"), return_rate=("returned", "mean"))
    return g.reset_index()


@dg.asset(deps=[customer_features], group_name="features")
def feature_report(context: dg.AssetExecutionContext) -> dg.MaterializeResult:
    # deps 只表達順序，不接收資料
    return dg.MaterializeResult(metadata={"note": "report built", "n": 3})


@dg.asset_check(asset=clean_orders)
def no_negative_amount(clean_orders: pd.DataFrame) -> dg.AssetCheckResult:
    bad = int((clean_orders["amount"] < 0).sum())
    return dg.AssetCheckResult(passed=bad == 0, metadata={"bad_rows": bad})


defs = dg.Definitions(assets=[raw_orders, clean_orders, customer_features, feature_report], asset_checks=[no_negative_amount])

res = dg.materialize([raw_orders, clean_orders, customer_features, feature_report, no_negative_amount])
print("success:", res.success)
print("clean rows:", len(res.asset_value("clean_orders")))
print("features:", res.asset_value("customer_features").head(3).to_string())
for ev in res.get_asset_materialization_events():
    md = ev.step_materialization_data.materialization
    print("materialized:", md.asset_key.to_user_string(), {k: (v.value if hasattr(v, 'value') else v) for k, v in md.metadata.items() if k in ("rows", "n", "note")})
for ev in res.get_asset_check_evaluations():
    print("check:", ev.asset_key.to_user_string(), ev.check_name, ev.passed, ev.metadata)

# 資產圖
job = defs.resolve_implicit_global_asset_job_def() if hasattr(defs, "resolve_implicit_global_asset_job_def") else defs.get_implicit_global_asset_job_def()
graph = defs.resolve_asset_graph() if hasattr(defs, "resolve_asset_graph") else defs.get_asset_graph()
for k in graph.all_asset_keys if hasattr(graph, "all_asset_keys") else graph.get_all_asset_keys():
    node = graph.get(k)
    print("node", k.to_user_string(), "<-", [p.to_user_string() for p in node.parent_keys], "group", node.group_name)

# IO manager: 預設 fs_io_manager 存哪？
inst = dg.DagsterInstance.ephemeral()
res2 = dg.materialize([raw_orders, clean_orders], instance=inst)
print("storage:", inst.storage_directory())
import os
for root, dirs, files in os.walk(inst.storage_directory()):
    for f in files:
        print("  ", os.path.relpath(os.path.join(root, f), inst.storage_directory()))
# 只 materialize 下游、上游從 instance 載回
# 用 defs 的 job 選擇子集
sub = dg.materialize([raw_orders, clean_orders, customer_features], instance=inst, selection=[customer_features])
print("subset success:", sub.success, [e.asset_key.to_user_string() for e in sub.get_asset_materialization_events()])
# 失敗的 run
@dg.asset
def bad_asset() -> int:
    raise ValueError("boom: schema changed")
r = dg.materialize([bad_asset], raise_on_error=False)
print("bad run success:", r.success)
fails = [e for e in r.all_events if e.is_step_failure]
print("failure msg:", fails[0].event_specific_data.error.message.strip().splitlines()[-1] if fails else None)
