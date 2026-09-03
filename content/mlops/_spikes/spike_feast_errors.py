# feature-store 課的錯誤原文 spike：把新手一定會撞的錯誤一次撞完，原文抄進課程與測驗題。
# 跑法：uv run --script content/mlops/_spikes/spike_feast_errors.py
# /// script
# requires-python = ">=3.11,<3.14"
# dependencies = ["feast>=0.50", "pandas", "numpy", "pyarrow"]
# ///
import datetime as dt
import logging
import shutil
import subprocess
import sys
import tempfile
import textwrap
import traceback
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

logging.getLogger("feast").setLevel(logging.ERROR)
warnings.filterwarnings("ignore")

W = Path(tempfile.gettempdir()) / "feast-errors-spike"
shutil.rmtree(W, ignore_errors=True)
(W / "data").mkdir(parents=True)

NOW = dt.datetime.now(dt.UTC).replace(minute=0, second=0, microsecond=0)
DAY0 = (NOW - dt.timedelta(days=9)).replace(hour=3)
rng = np.random.default_rng(0)
rows = [
    {
        "customer_id": c,
        "event_timestamp": DAY0 + dt.timedelta(days=d),
        "n_orders_30d": int(rng.integers(0, 15)),
        "total_30d": float(rng.gamma(2, 300)),
        "return_rate": float(rng.random() * 0.2),
    }
    for c in range(1, 6)
    for d in range(10)
]
snaps = pd.DataFrame(rows)
snaps["total_30d"] = snaps["total_30d"].astype("float32")
snaps["return_rate"] = snaps["return_rate"].astype("float32")
PARQ = W / "data" / "customer_daily.parquet"
snaps.to_parquet(PARQ)

(W / "feature_store.yaml").write_text(
    textwrap.dedent("""
    project: churn
    provider: local
    registry: data/registry.db
    online_store:
      type: sqlite
      path: data/online.db
    entity_key_serialization_version: 3
""").lstrip()
)


def shot(title, fn):
    print(f"\n=== {title} " + "=" * max(0, 66 - len(title)))
    try:
        out = fn()
        print("（沒有丟例外）→", out)
    except Exception:  # noqa: BLE001 — 這支腳本就是要看例外原文
        print(traceback.format_exc().strip().splitlines()[-1])
        print("--- 完整最後幾行 ---")
        print("\n".join(traceback.format_exc().strip().splitlines()[-6:]))


import feast  # noqa: E402
from feast import Entity, FeatureStore, FeatureView, Field, FileSource  # noqa: E402
from feast.types import Float32, Float64, Int64  # noqa: E402

print("feast", feast.__version__, "| python", sys.version.split()[0])

# ── 0. python -m feast ────────────────────────────────────────────────────
_p = subprocess.run(
    [sys.executable, "-m", "feast", "apply"], capture_output=True, text=True, cwd=W, check=False
)
print("\n=== 0. python -m feast apply（很多教學這樣寫）" + "=" * 24)
print("exit", _p.returncode, "|", (_p.stderr or _p.stdout).strip().splitlines()[-1])

store = FeatureStore(repo_path=str(W))
entity_df = pd.DataFrame(
    {"customer_id": [1, 2], "event_timestamp": [NOW - dt.timedelta(days=2), NOW - dt.timedelta(days=1)]}
)
FEATS = ["customer_daily:n_orders_30d", "customer_daily:return_rate"]

# ── 1. apply 之前就查 ─────────────────────────────────────────────────────
shot("1. apply 之前就 get_historical_features", lambda: store.get_historical_features(entity_df, FEATS).to_df())
shot("1b. apply 之前 list_feature_views", lambda: [fv.name for fv in store.list_feature_views()])

customer = Entity(name="customer", join_keys=["customer_id"])
src = FileSource(path=str(PARQ), timestamp_field="event_timestamp")
customer_daily = FeatureView(
    name="customer_daily",
    entities=[customer],
    ttl=dt.timedelta(days=3),
    schema=[
        Field(name="n_orders_30d", dtype=Int64),
        Field(name="total_30d", dtype=Float32),
        Field(name="return_rate", dtype=Float32),
    ],
    source=src,
    online=True,
)
store.apply([customer, customer_daily])
print("\napplied:", [fv.name for fv in store.list_feature_views()])

# ── 2. 還沒 materialize 就取線上特徵 ──────────────────────────────────────
shot(
    "2. 還沒 materialize 就 get_online_features",
    lambda: store.get_online_features(features=FEATS, entity_rows=[{"customer_id": 1}]).to_dict(),
)

# ── 3. 特徵名寫錯 ────────────────────────────────────────────────────────
shot(
    "3. 特徵名寫錯 customer_daily:nope",
    lambda: store.get_historical_features(entity_df, ["customer_daily:nope"]).to_df(),
)
shot(
    "3b. feature view 名寫錯 custommer_daily:n_orders_30d",
    lambda: store.get_historical_features(entity_df, ["custommer_daily:n_orders_30d"]).to_df(),
)
shot("3c. 忘了冒號（只寫欄名）", lambda: store.get_historical_features(entity_df, ["n_orders_30d"]).to_df())

# ── 4. entity_df 缺 event_timestamp ──────────────────────────────────────
shot(
    "4. entity_df 沒有 event_timestamp 欄",
    lambda: store.get_historical_features(pd.DataFrame({"customer_id": [1, 2]}), FEATS).to_df(),
)
shot(
    "4b. 時間欄叫別的名字（timestamp）",
    lambda: store.get_historical_features(
        pd.DataFrame({"customer_id": [1, 2], "timestamp": [NOW, NOW]}), FEATS
    ).to_df(),
)
shot(
    "4c. join key 名字錯（cust_id）",
    lambda: store.get_historical_features(
        pd.DataFrame({"cust_id": [1, 2], "event_timestamp": [NOW, NOW]}), FEATS
    ).to_df(),
)

# ── 5. timestamp 沒有時區 ────────────────────────────────────────────────
shot(
    "5. entity_df 的 event_timestamp 是 naive（沒時區）",
    lambda: store.get_historical_features(
        pd.DataFrame({"customer_id": [1, 2], "event_timestamp": [NOW.replace(tzinfo=None)] * 2}), FEATS
    ).to_df(),
)


def naive_source():
    _n = snaps.copy()
    _n["event_timestamp"] = _n["event_timestamp"].dt.tz_localize(None)
    _p = W / "data" / "naive.parquet"
    _n.to_parquet(_p)
    _fv = FeatureView(
        name="naive_daily",
        entities=[customer],
        ttl=dt.timedelta(days=3),
        schema=[Field(name="n_orders_30d", dtype=Int64)],
        source=FileSource(path=str(_p), timestamp_field="event_timestamp"),
        online=True,
    )
    store.apply([customer, _fv])
    return store.get_historical_features(entity_df, ["naive_daily:n_orders_30d"]).to_df().to_string(index=False)


shot("5b. 來源 parquet 的 event_timestamp 沒有時區", naive_source)

# ── 6. ttl 太短：不是 NaN，是整列消失 ────────────────────────────────────
old_df = pd.DataFrame(
    {
        "customer_id": [1, 1, 1],
        "event_timestamp": [NOW - dt.timedelta(days=k) for k in (0, 5, 20)],
    }
)
res = store.get_historical_features(old_df, FEATS).to_df()
print("\n=== 6. 事件時間超過 ttl（entity_df 3 列）" + "=" * 30)
print("  進去 3 列，出來", len(res), "列；isna 總數", int(res[["n_orders_30d", "return_rate"]].isna().sum().sum()))
print(res.to_string(index=False))

# ── 7. 線上取特徵：查不到的 entity ───────────────────────────────────────
store.materialize_incremental(end_date=NOW)
print("\n=== 7. materialize 之後 " + "=" * 45)
print("  存在的客戶：", store.get_online_features(features=FEATS, entity_rows=[{"customer_id": 1}]).to_dict())
print("  不存在的客戶 999：", store.get_online_features(features=FEATS, entity_rows=[{"customer_id": 999}]).to_dict())
shot(
    "7b. entity_rows 的 key 寫錯（cust_id）",
    lambda: store.get_online_features(features=FEATS, entity_rows=[{"cust_id": 1}]).to_dict(),
)

# ── 8. 加欄位之後 materialize_incremental 不補舊資料 ─────────────────────
_s2 = snaps.copy()
_s2["avg_amount"] = (_s2.total_30d / _s2.n_orders_30d.clip(lower=1)).astype("float32")
_s2.to_parquet(PARQ)
fv2 = FeatureView(
    name="customer_daily",
    entities=[customer],
    ttl=dt.timedelta(days=3),
    schema=[
        Field(name="n_orders_30d", dtype=Int64),
        Field(name="total_30d", dtype=Float32),
        Field(name="return_rate", dtype=Float32),
        Field(name="avg_amount", dtype=Float32),
    ],
    source=src,
    online=True,
)
store.apply([customer, fv2])
store.materialize_incremental(end_date=NOW)
print("\n=== 8. 加欄位 → apply → materialize_incremental " + "=" * 22)
print(
    "  incremental 之後：",
    store.get_online_features(features=["customer_daily:avg_amount"], entity_rows=[{"customer_id": 1}]).to_dict(),
)
store.materialize(start_date=DAY0 - dt.timedelta(days=1), end_date=NOW)
print(
    "  全量 materialize 之後：",
    store.get_online_features(features=["customer_daily:avg_amount"], entity_rows=[{"customer_id": 1}]).to_dict(),
)

# ── 9. on-demand feature view 的 dtype 不符 ──────────────────────────────
from feast.on_demand_feature_view import on_demand_feature_view  # noqa: E402


def odfv_wrong_dtype():
    @on_demand_feature_view(sources=[fv2], schema=[Field(name="amount_per_order", dtype=Float32)])
    def bad_ratio(inputs: pd.DataFrame) -> pd.DataFrame:
        out = pd.DataFrame()
        out["amount_per_order"] = inputs["total_30d"] / inputs["n_orders_30d"].clip(lower=1)  # → float64
        return out

    return store.apply([customer, fv2, bad_ratio])


shot("9. ODFV 宣告 Float32 但回傳 float64", odfv_wrong_dtype)


def odfv_ok():
    @on_demand_feature_view(sources=[fv2], schema=[Field(name="amount_per_order", dtype=Float64)])
    def good_ratio(inputs: pd.DataFrame) -> pd.DataFrame:
        out = pd.DataFrame()
        out["amount_per_order"] = inputs["total_30d"] / inputs["n_orders_30d"].clip(lower=1)
        return out

    store.apply([customer, fv2, good_ratio])
    return store.get_online_features(
        features=["customer_daily:total_30d", "good_ratio:amount_per_order"], entity_rows=[{"customer_id": 1}]
    ).to_dict()


shot("9b. ODFV 宣告 Float64（正確）", odfv_ok)

# ── 10. feature_store.yaml 少了必填欄位 ─────────────────────────────────
def bad_yaml():
    w2 = W / "bad"
    (w2 / "data").mkdir(parents=True, exist_ok=True)
    (w2 / "feature_store.yaml").write_text("registry: data/registry.db\nprovider: local\n")
    return FeatureStore(repo_path=str(w2)).list_feature_views()


shot("10. feature_store.yaml 少了 project", bad_yaml)


def no_yaml():
    w3 = W / "noyaml"
    w3.mkdir(parents=True, exist_ok=True)
    return FeatureStore(repo_path=str(w3))


shot("10b. 資料夾裡沒有 feature_store.yaml", no_yaml)
print("\n完成。")
