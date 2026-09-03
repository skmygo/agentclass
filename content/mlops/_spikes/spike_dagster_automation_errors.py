# Dagster 自動化「真實錯誤訊息」spike：cron 寫錯、partition 不存在、忘了給 resource、config key 打錯、
# schedule/sensor 少 job、非分割資產給 partition_key、automation 結果物件的屬性、job 執行方式。
# 測驗題的錯誤輸出一律從這裡抄（不杜撰）。用法：uv run --script spike_dagster_automation_errors.py
# /// script
# requires-python = ">=3.11"
# dependencies = ["dagster>=1.10", "pandas", "numpy"]
# ///
import datetime as dt
import logging
import warnings
from pathlib import Path
import tempfile

import dagster as dg
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
logging.getLogger("dagster").setLevel(logging.CRITICAL)
QUIET = {"loggers": {"console": {"config": {"log_level": "CRITICAL"}}}}
WORK = Path(tempfile.mkdtemp(prefix="dagster-err-"))
print("dagster", dg.__version__)


def show(tag, fn):
    print(f"\n===== {tag} =====")
    try:
        out = fn()
        print("OK ->", out)
    except Exception as e:  # noqa: BLE001 - spike 就是要看每種例外的原文
        print(f"{type(e).__name__}: {str(e)[:900]}")


class Warehouse(dg.ConfigurableResource):
    root: str

    def write(self, name: str, df: pd.DataFrame) -> str:
        p = Path(self.root) / f"{name}.csv"
        df.to_csv(p, index=False)
        return str(p)


class IngestConfig(dg.Config):
    n_rows: int = 100
    seed: int = 0


@dg.asset
def orders(context: dg.AssetExecutionContext, config: IngestConfig, warehouse: Warehouse) -> pd.DataFrame:
    rng = np.random.default_rng(config.seed)
    df = pd.DataFrame({"amount": rng.gamma(2, 100, config.n_rows).round(0)})
    context.log.info(warehouse.write("orders", df))
    return df


daily = dg.DailyPartitionsDefinition(start_date="2026-09-01")


@dg.asset(partitions_def=daily)
def daily_orders(context: dg.AssetExecutionContext) -> pd.DataFrame:
    day = context.partition_key
    rng = np.random.default_rng(int(day.replace("-", "")))
    return pd.DataFrame({"day": day, "amount": rng.gamma(2, 100, 5)})


job = dg.define_asset_job("nightly_job", selection=[orders])
pjob = dg.define_asset_job("daily_job", selection=[daily_orders], partitions_def=daily)

# 1) 忘了給 resource
show("missing resource", lambda: dg.materialize([orders], run_config=QUIET).success)

# 2) config key 打錯
show(
    "bad config key",
    lambda: dg.materialize(
        [orders],
        resources={"warehouse": Warehouse(root=str(WORK))},
        run_config={**QUIET, "ops": {"orders": {"config": {"n_row": 7}}}},
    ).success,
)

# 3) config 型別錯
show(
    "bad config type",
    lambda: dg.materialize(
        [orders],
        resources={"warehouse": Warehouse(root=str(WORK))},
        run_config={**QUIET, "ops": {"orders": {"config": {"n_rows": "七"}}}},
    ).success,
)

# 4) cron 寫錯
show("bad cron", lambda: dg.ScheduleDefinition(job=job, cron_schedule="0 25 * * *").name)
show("bad cron 2", lambda: dg.ScheduleDefinition(job=job, cron_schedule="every night").name)
show("bad timezone", lambda: dg.ScheduleDefinition(job=job, cron_schedule="0 2 * * *", execution_timezone="Asia/Taipe").name)

# 5) schedule 沒有 job
show("schedule without job", lambda: dg.ScheduleDefinition(cron_schedule="0 2 * * *").name)


def _decl_sched_no_job():
    @dg.schedule(cron_schedule="0 2 * * *")
    def sched_no_job(context):
        return dg.RunRequest(run_key="x")

    return sched_no_job.name


show("@schedule without job (define)", _decl_sched_no_job)

# 6) partition 不存在 / 少給 / 多給
show(
    "partition key out of range",
    lambda: dg.materialize([daily_orders], partition_key="2026-08-30", run_config=QUIET).success,
)
show("partitioned asset without partition_key", lambda: dg.materialize([daily_orders], run_config=QUIET).success)
show(
    "partition_key on non-partitioned asset",
    lambda: dg.materialize(
        [orders],
        partition_key="2026-09-01",
        resources={"warehouse": Warehouse(root=str(WORK))},
        run_config=QUIET,
    ).success,
)

# 7) build_schedule_from_partitioned_job 用在沒有分割的 job
show("build_schedule_from_partitioned_job on unpartitioned", lambda: dg.build_schedule_from_partitioned_job(job, hour_of_day=3).name)

# 8) sensor 沒有 job
def _decl_sensor_no_job():
    @dg.sensor()
    def sensor_no_job(context):
        return dg.RunRequest(run_key="a")

    return dg.Definitions(assets=[orders], sensors=[sensor_no_job]).resolve_all_job_defs()


show("sensor without job", _decl_sensor_no_job)

# 9) RunRequest 沒有 run_key
@dg.sensor(job=job)
def sensor_no_run_key(context):
    yield dg.RunRequest()   # 每次 tick 都發一筆、沒有去重鑰匙


_t = sensor_no_run_key.evaluate_tick(dg.build_sensor_context())
print("\n===== RunRequest without run_key =====")
print("run_requests:", len(_t.run_requests), "run_key:", _t.run_requests[0].run_key)

# 10) evaluate_automation_conditions 的結果物件
@dg.asset(automation_condition=dg.AutomationCondition.eager())
def report(orders: pd.DataFrame) -> int:
    return len(orders)


@dg.asset(automation_condition=dg.AutomationCondition.on_cron("0 6 * * *"))
def cron_report(orders: pd.DataFrame) -> int:
    return len(orders)


defs = dg.Definitions(
    assets=[orders, report, cron_report, daily_orders],
    jobs=[job, pjob],
    resources={"warehouse": Warehouse(root=str(WORK))},
)
inst = dg.DagsterInstance.ephemeral()
ev0 = dg.evaluate_automation_conditions(defs=defs, instance=inst)
print("\n===== automation conditions =====")
print("eval0 total_requested:", ev0.total_requested)
dg.materialize(
    [orders], instance=inst, resources={"warehouse": Warehouse(root=str(WORK))}, run_config=QUIET
)
ev1 = dg.evaluate_automation_conditions(defs=defs, instance=inst, cursor=ev0.cursor)
print("eval1 total_requested:", ev1.total_requested, "report:", ev1.get_num_requested(dg.AssetKey("report")),
      "cron_report:", ev1.get_num_requested(dg.AssetKey("cron_report")))
show("result.run_requests", lambda: ev1.run_requests)
print("result attrs:", [a for a in dir(ev1) if not a.startswith("_")])
dg.materialize([orders, report], instance=inst, selection=[report],
               resources={"warehouse": Warehouse(root=str(WORK))}, run_config=QUIET)
ev2 = dg.evaluate_automation_conditions(defs=defs, instance=inst, cursor=ev1.cursor)
print("eval2 total_requested:", ev2.total_requested)

# on_cron 在跨過 cron 時刻後會不會被 requested？（用 evaluate_time）
try:
    ev3 = dg.evaluate_automation_conditions(
        defs=defs, instance=inst, cursor=ev2.cursor, evaluation_time=dt.datetime(2026, 9, 5, 6, 30)  # noqa: DTZ001
    )
    print("eval3 (evaluation_time 09-05 06:30) total_requested:", ev3.total_requested,
          "cron_report:", ev3.get_num_requested(dg.AssetKey("cron_report")))
except Exception as e:  # noqa: BLE001
    print("evaluation_time not supported:", type(e).__name__, str(e)[:300])

# 11) job 怎麼真的跑起來
print("\n===== running a job =====")
print("Definitions methods:", [a for a in dir(defs) if "job" in a.lower()])
show(
    "resolve_job_def + execute_in_process",
    lambda: defs.resolve_job_def("nightly_job").execute_in_process(
        run_config={**QUIET, "ops": {"orders": {"config": {"n_rows": 5}}}}, instance=inst
    ).success,
)

# 12) 排程 tick 的 run_request 屬性
print("\n===== schedule tick =====")
sched = dg.ScheduleDefinition(job=job, cron_schedule="0 2 * * *", execution_timezone="Asia/Taipei")
tick = sched.evaluate_tick(dg.build_schedule_context(scheduled_execution_time=dt.datetime(2026, 9, 4, 2, 0)))  # noqa: DTZ001
rr = tick.run_requests[0]
print("run_key:", rr.run_key, "tags:", rr.tags, "job_name:", rr.job_name)
psched = dg.build_schedule_from_partitioned_job(pjob, hour_of_day=3)
print("psched name/cron:", psched.name, psched.cron_schedule, "tz:", psched.execution_timezone)
for d in ["2026-09-02", "2026-09-03", "2026-09-04"]:
    _tick = psched.evaluate_tick(
        dg.build_schedule_context(scheduled_execution_time=dt.datetime.fromisoformat(f"{d}T03:00:00"))
    )
    print("  tick", d, "03:00 -> partition", [r.partition_key for r in _tick.run_requests])
