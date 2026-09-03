# Dagster 自動化 spike：resources/config、partitions、schedules、sensors、AutomationCondition、retries、job
# /// script
# requires-python = ">=3.11"
# dependencies = ["dagster>=1.10", "pandas", "numpy"]
# ///
import datetime as dt
import json
import tempfile
from pathlib import Path

import dagster as dg
import pandas as pd
import numpy as np

print("dagster", dg.__version__)
WORK = Path(tempfile.mkdtemp(prefix="dagster-lesson-"))

# 1) resource + config
class FakeWarehouse(dg.ConfigurableResource):
    root: str
    def write(self, name: str, df: pd.DataFrame) -> str:
        p = Path(self.root) / f"{name}.csv"; df.to_csv(p, index=False); return str(p)

class TrainConfig(dg.Config):
    n_rows: int = 100
    seed: int = 0

@dg.asset
def sales(context: dg.AssetExecutionContext, config: TrainConfig, warehouse: FakeWarehouse) -> pd.DataFrame:
    rng = np.random.default_rng(config.seed)
    df = pd.DataFrame({"amount": rng.gamma(2, 100, config.n_rows)})
    context.log.info(f"wrote {warehouse.write('sales', df)}")
    return df

res = dg.materialize([sales], resources={"warehouse": FakeWarehouse(root=str(WORK))}, run_config={"ops": {"sales": {"config": {"n_rows": 7, "seed": 1}}}})
print("resource run:", res.success, len(res.asset_value("sales")))

# 2) partitions
daily = dg.DailyPartitionsDefinition(start_date="2026-09-01")

@dg.asset(partitions_def=daily)
def daily_sales(context: dg.AssetExecutionContext) -> pd.DataFrame:
    day = context.partition_key
    rng = np.random.default_rng(int(day.replace("-", "")))
    df = pd.DataFrame({"day": day, "amount": rng.gamma(2, 100, 5)})
    context.add_output_metadata({"day": day, "total": float(df.amount.sum())})
    return df

inst = dg.DagsterInstance.ephemeral()
for day in ["2026-09-01", "2026-09-02"]:
    r = dg.materialize([daily_sales], partition_key=day, instance=inst)
    print("partition", day, r.success)
print("partition keys (first 3):", daily.get_partition_keys(current_time=dt.datetime(2026, 9, 4))[:3])  # noqa: DTZ001
mats = inst.get_materialized_partitions(dg.AssetKey("daily_sales"))
print("materialized partitions:", sorted(mats))

# 3) schedule
job = dg.define_asset_job("nightly_job", selection=[sales])
sched = dg.ScheduleDefinition(job=job, cron_schedule="0 2 * * *", execution_timezone="Asia/Taipei")
ctx = dg.build_schedule_context(scheduled_execution_time=dt.datetime(2026, 9, 4, 2, 0))  # noqa: DTZ001
tick = sched.evaluate_tick(ctx)
print("schedule run requests:", len(tick.run_requests), tick.run_requests[0].run_config if tick.run_requests else None)

@dg.schedule(job=job, cron_schedule="0 2 * * *")
def nightly_with_config(context: dg.ScheduleEvaluationContext):
    day = context.scheduled_execution_time.strftime("%Y-%m-%d")
    return dg.RunRequest(run_key=day, run_config={"ops": {"sales": {"config": {"n_rows": 3, "seed": 7}}}}, tags={"day": day})
tick2 = nightly_with_config.evaluate_tick(ctx)
print("custom schedule:", tick2.run_requests[0].run_key, tick2.run_requests[0].tags)

# partitioned schedule
pjob = dg.define_asset_job("daily_job", selection=[daily_sales], partitions_def=daily)
psched = dg.build_schedule_from_partitioned_job(pjob, hour_of_day=3)
print("partitioned schedule cron:", psched.cron_schedule)
ptick = psched.evaluate_tick(dg.build_schedule_context(scheduled_execution_time=dt.datetime(2026, 9, 4, 3, 0)))  # noqa: DTZ001
print("partitioned schedule → partition:", ptick.run_requests[0].partition_key if ptick.run_requests else None)

# 4) sensor
INBOX = WORK / "inbox"; INBOX.mkdir()
@dg.sensor(job=job, minimum_interval_seconds=30)
def new_file_sensor(context: dg.SensorEvaluationContext):
    seen = set(json.loads(context.cursor)) if context.cursor else set()
    files = sorted(p.name for p in INBOX.glob("*.csv"))
    new = [f for f in files if f not in seen]
    for f in new:
        yield dg.RunRequest(run_key=f, run_config={"ops": {"sales": {"config": {"n_rows": 2}}}}, tags={"file": f})
    if not new:
        yield dg.SkipReason("no new files")
    context.update_cursor(json.dumps(sorted(seen | set(new))))

sctx = dg.build_sensor_context(instance=inst)
r0 = new_file_sensor.evaluate_tick(sctx)
print("sensor empty inbox:", r0.run_requests, r0.skip_message)
(INBOX / "a.csv").write_text("x"); (INBOX / "b.csv").write_text("y")
sctx2 = dg.build_sensor_context(instance=inst, cursor=r0.cursor)
r1 = new_file_sensor.evaluate_tick(sctx2)
print("sensor 2 files:", [rr.run_key for rr in r1.run_requests], "cursor", r1.cursor)
sctx3 = dg.build_sensor_context(instance=inst, cursor=r1.cursor)
r2 = new_file_sensor.evaluate_tick(sctx3)
print("sensor again:", r2.run_requests, r2.skip_message)

# asset sensor
@dg.asset_sensor(asset_key=dg.AssetKey("sales"), job=job)
def on_sales(context, asset_event):
    return dg.RunRequest(run_key=context.cursor)
print("asset_sensor defined:", on_sales.name)

# 5) AutomationCondition
@dg.asset(automation_condition=dg.AutomationCondition.eager())
def report(sales: pd.DataFrame) -> int:
    return len(sales)
@dg.asset(automation_condition=dg.AutomationCondition.on_cron("0 6 * * *"))
def cron_report(sales: pd.DataFrame) -> int:
    return len(sales)
print("eager condition:", dg.AutomationCondition.eager().get_label() if hasattr(dg.AutomationCondition.eager(), "get_label") else dg.AutomationCondition.eager())
defs = dg.Definitions(assets=[sales, report, cron_report, daily_sales], jobs=[job, pjob], schedules=[sched, nightly_with_config, psched], sensors=[new_file_sensor, on_sales], resources={"warehouse": FakeWarehouse(root=str(WORK))})
try:
    from dagster import evaluate_automation_conditions
    inst2 = dg.DagsterInstance.ephemeral()
    ev = evaluate_automation_conditions(defs=defs, instance=inst2)
    print("automation eval (nothing materialized):", ev.total_requested)
    dg.materialize([sales], instance=inst2, resources={"warehouse": FakeWarehouse(root=str(WORK))})
    ev2 = evaluate_automation_conditions(defs=defs, instance=inst2, cursor=ev.cursor)
    print("automation eval after sales:", ev2.total_requested, [rr.asset_selection for rr in ev2.run_requests])
except Exception as e:
    import traceback; traceback.print_exc()

# 6) retries + failure hook
@dg.asset(retry_policy=dg.RetryPolicy(max_retries=2, delay=0.1))
def flaky(context: dg.AssetExecutionContext) -> int:
    if context.retry_number < 2:
        raise RuntimeError(f"transient failure (attempt {context.retry_number})")
    return 42
rr = dg.materialize([flaky], raise_on_error=False)
print("flaky success:", rr.success, rr.asset_value("flaky") if rr.success else None)
retries = [e for e in rr.all_events if e.event_type_value in ("STEP_UP_FOR_RETRY", "STEP_RESTARTED")]
print("retry events:", [e.event_type_value for e in retries])

# 7) run status sensor / asset checks blocking
@dg.asset
def model_metric() -> float:
    return 0.71
@dg.asset_check(asset=model_metric, blocking=True)
def good_enough(model_metric: float) -> dg.AssetCheckResult:
    return dg.AssetCheckResult(passed=model_metric >= 0.8, severity=dg.AssetCheckSeverity.ERROR, metadata={"auc": model_metric})
@dg.asset(deps=[model_metric])
def deploy() -> str:
    return "deployed"
rb = dg.materialize([model_metric, good_enough, deploy], raise_on_error=False)
print("blocking check run success:", rb.success, "deploy materialized:", [e.asset_key.to_user_string() for e in rb.get_asset_materialization_events()])
