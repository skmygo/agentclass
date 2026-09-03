# 候選課 spike：Feast 特徵倉——file offline store + sqlite online store，定義 entity/feature view，get_historical_features / materialize / get_online_features
# /// script
# requires-python = ">=3.11"
# dependencies = ["feast>=0.50", "pandas", "numpy", "pyarrow"]
# ///
import os, subprocess, sys, tempfile, textwrap, time
from datetime import datetime, timedelta, timezone
from pathlib import Path
import numpy as np, pandas as pd
import feast
print("feast", feast.__version__)
W = Path(tempfile.mkdtemp(prefix="feast-")); os.chdir(W)
(W / "data").mkdir()
rng = np.random.default_rng(0)
now = datetime.now(timezone.utc).replace(microsecond=0)
rows = []
for cid in range(1, 21):
    for d in range(10):
        ts = now - timedelta(days=d)
        rows.append({"customer_id": cid, "event_timestamp": ts, "n_orders_30d": int(rng.integers(0, 15)), "total_30d": float(rng.gamma(2, 300)), "return_rate": float(rng.random() * 0.2)})
df = pd.DataFrame(rows); df.to_parquet("data/customer_stats.parquet")
Path("feature_store.yaml").write_text(textwrap.dedent('''
    project: churn
    registry: data/registry.db
    provider: local
    online_store:
      type: sqlite
      path: data/online.db
    entity_key_serialization_version: 3
'''))
Path("features.py").write_text(textwrap.dedent('''
    from datetime import timedelta
    from feast import Entity, FeatureView, Field, FileSource
    from feast.types import Float32, Int64
    customer = Entity(name="customer", join_keys=["customer_id"])
    src = FileSource(path="data/customer_stats.parquet", timestamp_field="event_timestamp")
    customer_stats = FeatureView(
        name="customer_stats", entities=[customer], ttl=timedelta(days=3),
        schema=[Field(name="n_orders_30d", dtype=Int64), Field(name="total_30d", dtype=Float32), Field(name="return_rate", dtype=Float32)],
        source=src, online=True,
    )
'''))
t0 = time.time()
from feast import FeatureStore
# apply via CLI-equivalent
sys.path.insert(0, str(W)); import features as F
store = FeatureStore(repo_path=".")
store.apply([F.customer, F.customer_stats])          # 等同 CLI `feast apply`
print("applied; entities:", [e.name for e in store.list_entities()])
print("feature views:", [fv.name for fv in store.list_feature_views()])
# point-in-time join
entity_df = pd.DataFrame({"customer_id": [1, 2, 3], "event_timestamp": [now - timedelta(days=2), now - timedelta(days=5), now]})
hist = store.get_historical_features(entity_df=entity_df, features=["customer_stats:n_orders_30d", "customer_stats:total_30d"]).to_df()
print("historical:\n", hist.to_string())
# materialize to online
store.materialize_incremental(end_date=now + timedelta(seconds=1))
online = store.get_online_features(features=["customer_stats:n_orders_30d", "customer_stats:return_rate"], entity_rows=[{"customer_id": 1}, {"customer_id": 2}]).to_dict()
print("online:", online)
print("elapsed", round(time.time() - t0, 1), "s")
