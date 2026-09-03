# 候選課 spike：資料驗證——pandera schema、lazy 驗證、跟 Dagster asset check 接起來
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandera>=0.20", "dagster>=1.10", "pandas", "numpy"]
# ///
import warnings
import numpy as np, pandas as pd, pandera.pandas as pa, dagster as dg
warnings.filterwarnings("ignore")
print("pandera", pa.__version__ if hasattr(pa, "__version__") else __import__("pandera").__version__)
rng = np.random.default_rng(0); n = 500
df = pd.DataFrame({"order_id": range(n), "customer": rng.integers(1, 60, n), "amount": rng.gamma(2, 300, n).round(0), "returned": rng.random(n) < 0.08, "country": rng.choice(["TW", "JP", "US"], n)})
schema = pa.DataFrameSchema({
    "order_id": pa.Column(int, pa.Check.ge(0), unique=True),
    "customer": pa.Column(int, pa.Check.between(1, 59)),
    "amount": pa.Column(float, pa.Check.gt(0), nullable=False),
    "returned": pa.Column(bool),
    "country": pa.Column(str, pa.Check.isin(["TW", "JP", "US"])),
}, checks=pa.Check(lambda d: len(d) >= 400, error="at least 400 rows"))
print("clean ok rows:", len(schema.validate(df)))
bad = df.copy(); bad.loc[0, "amount"] = -50; bad.loc[1, "country"] = "XX"; bad.loc[2, "customer"] = 99; bad.loc[3, "amount"] = np.nan
try:
    schema.validate(bad, lazy=True)
except pa.errors.SchemaErrors as e:
    fc = e.failure_cases
    print("failure cases:", len(fc)); print(fc[["column", "check", "failure_case", "index"]].to_string())
try:
    schema.validate(bad)
except pa.errors.SchemaError as e:
    print("first error only:", str(e).splitlines()[0][:150])
# DataFrameModel style
class Orders(pa.DataFrameModel):
    order_id: int = pa.Field(ge=0, unique=True)
    amount: float = pa.Field(gt=0)
    country: str = pa.Field(isin=["TW", "JP", "US"])
    class Config:
        coerce = True
print("model validate ok:", len(Orders.validate(df)))
# dagster asset check with pandera
@dg.asset
def orders() -> pd.DataFrame:
    return bad
@dg.asset_check(asset=orders, blocking=True)
def orders_schema(orders: pd.DataFrame) -> dg.AssetCheckResult:
    try:
        schema.validate(orders, lazy=True); return dg.AssetCheckResult(passed=True)
    except pa.errors.SchemaErrors as e:
        fc = e.failure_cases
        return dg.AssetCheckResult(passed=False, severity=dg.AssetCheckSeverity.ERROR, metadata={"n_failures": len(fc), "table": dg.MetadataValue.md(fc[["column", "check", "failure_case"]].head(10).to_markdown(index=False))})
r = dg.materialize([orders, orders_schema], run_config={"loggers": {"console": {"config": {"log_level": "CRITICAL"}}}}, raise_on_error=False)
ev = r.get_asset_check_evaluations()[0]
print("dagster check passed:", ev.passed, "n_failures:", ev.metadata["n_failures"].value)
