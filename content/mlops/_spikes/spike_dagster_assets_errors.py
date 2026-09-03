# Dagster 軟體定義資產「新手會犯的錯」spike：收集真實錯誤訊息當測驗題素材
# 用法：uv run --script content/mlops/_spikes/spike_dagster_assets_errors.py
# /// script
# requires-python = ">=3.11"
# dependencies = ["dagster>=1.10", "pandas", "numpy"]
# ///
import traceback

import dagster as dg
import numpy as np
import pandas as pd

print("dagster", dg.__version__)
QUIET = {"loggers": {"console": {"config": {"log_level": "WARNING"}}}}


def show(title, fn):
    print("\n" + "=" * 78)
    print("##", title)
    print("=" * 78)
    try:
        out = fn()
        print("(沒有例外) ->", out)
    except Exception as e:
        print("EXC TYPE:", type(e).__module__ + "." + type(e).__name__)
        print("EXC STR:")
        print(str(e))
        print("--- traceback 末 3 行 ---")
        print("".join(traceback.format_exception(type(e), e, e.__traceback__)[-3:]))


# ── 共用的正常資產 ──────────────────────────────────────────────────────
@dg.asset
def raw_orders() -> pd.DataFrame:
    rng = np.random.default_rng(0)
    n = 500
    amount = rng.gamma(2.0, 300, n).round(0)
    amount = np.where(rng.random(n) < 0.03, -amount, amount)
    return pd.DataFrame({
        "order_id": range(n),
        "customer": rng.integers(1, 60, n),
        "amount": amount,
        "returned": rng.random(n) < 0.08,
    })


@dg.asset
def clean_orders(raw_orders: pd.DataFrame) -> pd.DataFrame:
    return raw_orders[raw_orders["amount"] > 0].copy()


# ── 1. 兩個同名資產放進同一份 Definitions ────────────────────────────────
def case_duplicate():
    @dg.asset(name="clean_orders")
    def clean_orders_a() -> pd.DataFrame:
        return pd.DataFrame({"a": [1]})

    @dg.asset(name="clean_orders")
    def clean_orders_b() -> pd.DataFrame:
        return pd.DataFrame({"b": [1]})

    defs = dg.Definitions(assets=[clean_orders_a, clean_orders_b])
    # 有些版本要 resolve 才會檢查
    return defs.resolve_all_job_defs() if hasattr(defs, "resolve_all_job_defs") else defs.get_all_job_defs()


show("1. Definitions 裡兩個同名資產（clean_orders x2）", case_duplicate)


# ── 2. 下游參數名打錯（clean_order 少了 s）── 上游找不到 ─────────────────
def case_param_typo():
    @dg.asset
    def customer_features(clean_order: pd.DataFrame) -> pd.DataFrame:   # 打錯：少了 s
        return clean_order.head()

    return dg.materialize([raw_orders, clean_orders, customer_features], run_config=QUIET)


show("2. 下游參數名打錯 clean_order（正確是 clean_orders）", case_param_typo)


# ── 2b. 同上，但在 Definitions 載入時就爆？ ──────────────────────────────
def case_param_typo_defs():
    @dg.asset
    def customer_features2(clean_order: pd.DataFrame) -> pd.DataFrame:
        return clean_order.head()

    defs = dg.Definitions(assets=[raw_orders, clean_orders, customer_features2])
    return defs.resolve_all_job_defs() if hasattr(defs, "resolve_all_job_defs") else defs.get_all_job_defs()


show("2b. 同樣打錯，但只建 Definitions（載入時會不會擋）", case_param_typo_defs)


# ── 3. materialize 只給下游、沒給上游、也沒有 instance/storage ───────────
def case_missing_upstream():
    @dg.asset
    def customer_features3(clean_orders: pd.DataFrame) -> pd.DataFrame:
        return clean_orders.head()

    return dg.materialize([customer_features3], run_config=QUIET)


show("3. materialize 只給下游（上游不在清單、沒 instance）", case_missing_upstream)


# ── 3b. 給了 instance，但上游從來沒實體化過 ─────────────────────────────
def case_missing_upstream_instance():
    @dg.asset
    def customer_features4(clean_orders: pd.DataFrame) -> pd.DataFrame:
        return clean_orders.head()

    inst = dg.DagsterInstance.ephemeral()
    return dg.materialize([raw_orders, clean_orders, customer_features4],
                          selection=[customer_features4], instance=inst, run_config=QUIET)


show("3b. selection 只選下游，但上游在這個 instance 從沒算過", case_missing_upstream_instance)


# ── 4. asset check 的參數名不是資產名 ───────────────────────────────────
def case_check_param():
    @dg.asset_check(asset=clean_orders)
    def enough_rows(df: pd.DataFrame) -> dg.AssetCheckResult:      # 應該叫 clean_orders
        return dg.AssetCheckResult(passed=len(df) >= 400)

    return dg.materialize([raw_orders, clean_orders, enough_rows], run_config=QUIET)


show("4. asset_check 的參數名寫成 df（不是資產名 clean_orders）", case_check_param)


# ── 5. deps 用字串、名字打錯 ────────────────────────────────────────────
def case_deps_typo():
    @dg.asset(deps=["clean_order"])       # 打錯：正確是 clean_orders
    def feature_report() -> dg.MaterializeResult:
        return dg.MaterializeResult(metadata={"status": "sent"})

    return dg.materialize([raw_orders, clean_orders, feature_report], run_config=QUIET)


show("5. deps=[\"clean_order\"] 字串打錯", case_deps_typo)


# ── 5b. deps 打錯但只建 Definitions ─────────────────────────────────────
def case_deps_typo_defs():
    @dg.asset(deps=["clean_order"])
    def feature_report2() -> dg.MaterializeResult:
        return dg.MaterializeResult(metadata={"status": "sent"})

    defs = dg.Definitions(assets=[raw_orders, clean_orders, feature_report2])
    return defs.resolve_all_job_defs() if hasattr(defs, "resolve_all_job_defs") else defs.get_all_job_defs()


show("5b. deps 打錯，只建 Definitions", case_deps_typo_defs)


# ── 6. materialize(asset_checks=...) 這個參數不存在 ─────────────────────
def case_asset_checks_kwarg():
    @dg.asset_check(asset=clean_orders)
    def chk(clean_orders: pd.DataFrame) -> dg.AssetCheckResult:
        return dg.AssetCheckResult(passed=True)

    return dg.materialize([raw_orders, clean_orders], asset_checks=[chk], run_config=QUIET)


show("6. materialize(..., asset_checks=[...]) 參數不存在", case_asset_checks_kwarg)


# ── 7. 資產丟例外時，錯誤物件裡的原因文字長什麼樣（notebook 要顯示它）──
print("\n" + "=" * 78)
print("## 7. 資產丟例外：error.message / error.cause / error.stack")
print("=" * 78)


@dg.asset
def broken_asset() -> int:
    raise ValueError("boom: upstream schema changed")


@dg.asset(deps=[broken_asset])
def after_broken() -> int:
    return 1


_r = dg.materialize([broken_asset, after_broken], run_config=QUIET, raise_on_error=False)
_fail = next(ev for ev in _r.all_events if ev.is_step_failure)
_err = _fail.event_specific_data.error
print("success:", _r.success)
print("materialized:", [ev.asset_key.to_user_string() for ev in _r.get_asset_materialization_events()])
print("--- error.message ---")
print(repr(_err.message))
print("--- error.cause ---")
print(repr(_err.cause))
print("--- error.cls_name ---")
print(repr(getattr(_err, "cls_name", None)))
print("--- error.stack (末 5 行) ---")
for line in (_err.stack or [])[-5:]:
    print(repr(line))
print("--- 抽原始例外的候選寫法 ---")
cand = [ln.strip() for ln in _err.message.strip().splitlines() if "ValueError" in ln]
print("message 內含 ValueError 的行：", cand)
stack_lines = [ln.strip() for ln in (_err.stack or []) if "ValueError" in ln]
print("stack 內含 ValueError 的行：", stack_lines)

print("--- SerializableErrorInfo.to_string() ---")
print(_err.to_string() if hasattr(_err, "to_string") else "(無 to_string)")
print("--- step failure event 的 .message ---")
print(repr(getattr(_fail, "message", None)))


# ── 8. deps 字串打錯不報錯：那到底發生了什麼？ ──────────────────────────
print("\n" + "=" * 78)
print("## 8. deps 打錯字串的「沉默後果」")
print("=" * 78)


@dg.asset(deps=["clean_order"])           # 打錯
def report_typo() -> dg.MaterializeResult:
    return dg.MaterializeResult(metadata={"status": "sent"})


@dg.asset(deps=[clean_orders])            # 正確
def report_ok() -> dg.MaterializeResult:
    return dg.MaterializeResult(metadata={"status": "sent"})


_defs_typo = dg.Definitions(assets=[raw_orders, clean_orders, report_typo, report_ok])
_graph = _defs_typo.resolve_asset_graph() if hasattr(_defs_typo, "resolve_asset_graph") else _defs_typo.get_asset_graph()
_keys = _graph.all_asset_keys if hasattr(_graph, "all_asset_keys") else _graph.get_all_asset_keys()
print("圖上所有節點：", sorted(k.to_user_string() for k in _keys))
for k in sorted(_keys, key=lambda k: k.to_user_string()):
    node = _graph.get(k)
    print("  ", k.to_user_string(), "<- parents", [p.to_user_string() for p in node.parent_keys],
          "| executable:", getattr(node, "is_executable", "?"))
_r8 = dg.materialize([raw_orders, clean_orders, report_typo, report_ok], run_config=QUIET)
print("success:", _r8.success)
print("執行順序：", [ev.asset_key.to_user_string() for ev in _r8.get_asset_materialization_events()])

# 只跑打錯的那個報表：會不會等 clean_orders？
_r8b = dg.materialize([raw_orders, clean_orders, report_typo], selection=[report_typo],
                      run_config=QUIET, raise_on_error=False)
print("只選 report_typo：success", _r8b.success,
      [ev.asset_key.to_user_string() for ev in _r8b.get_asset_materialization_events()])


# ── 9. asset_check 參數名寫成 df，真的拿得到資產嗎？ ────────────────────
print("\n" + "=" * 78)
print("## 9. asset_check 參數名不是資產名：值有沒有進來")
print("=" * 78)


@dg.asset_check(asset=clean_orders)
def rows_check(df: pd.DataFrame) -> dg.AssetCheckResult:      # 參數名亂取
    return dg.AssetCheckResult(passed=len(df) >= 400, metadata={"rows": len(df), "type": type(df).__name__})


_r9 = dg.materialize([raw_orders, clean_orders, rows_check], run_config=QUIET)
for ev in _r9.get_asset_check_evaluations():
    print("check:", ev.check_name, ev.passed, {k: v.value for k, v in ev.metadata.items()})


# ── 10. 兩個 check 同名（掛不同資產也算撞名嗎） ─────────────────────────
def case_dup_check():
    @dg.asset_check(asset=clean_orders, name="enough_rows")
    def c1(clean_orders: pd.DataFrame) -> dg.AssetCheckResult:
        return dg.AssetCheckResult(passed=True)

    @dg.asset_check(asset=clean_orders, name="enough_rows")
    def c2(clean_orders: pd.DataFrame) -> dg.AssetCheckResult:
        return dg.AssetCheckResult(passed=True)

    return dg.Definitions(assets=[raw_orders, clean_orders], asset_checks=[c1, c2])


show("10. 兩個同名 asset_check 掛在同一個資產", case_dup_check)


# ── 11. 忘了把 check 放進 materialize 的清單 ────────────────────────────
print("\n" + "=" * 78)
print("## 11. check 沒放進 materialize 清單：靜靜地不執行")
print("=" * 78)


@dg.asset_check(asset=clean_orders, blocking=True)
def never_runs(clean_orders: pd.DataFrame) -> dg.AssetCheckResult:
    return dg.AssetCheckResult(passed=False, severity=dg.AssetCheckSeverity.ERROR)


_r11 = dg.materialize([raw_orders, clean_orders], run_config=QUIET, raise_on_error=False)
print("沒放 check：success", _r11.success, "| check 評估數", len(_r11.get_asset_check_evaluations()))
_r11b = dg.materialize([raw_orders, clean_orders, never_runs], run_config=QUIET, raise_on_error=False)
print("有放 check：success", _r11b.success, "| check 評估數", len(_r11b.get_asset_check_evaluations()))
_f11 = [ev for ev in _r11b.all_events if ev.is_step_failure]
if _f11:
    print("錯誤訊息：", _f11[0].event_specific_data.error.message.strip())

print("\n=== 全部 case 跑完 ===")
