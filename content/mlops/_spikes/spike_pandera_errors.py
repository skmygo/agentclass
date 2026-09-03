# data-validation 課的「真實錯誤原文」spike：測驗題與教學頁引用的每一條訊息都從這裡撞出來。
# 跑法：uv run --script content/mlops/_spikes/spike_pandera_errors.py
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandera>=0.20", "pandas", "numpy", "pyyaml"]
# ///
import warnings

import numpy as np
import pandas as pd
import pandera
import pandera.pandas as pa

warnings.filterwarnings("ignore")
pd.set_option("display.width", 200)


def head(title: str) -> None:
    print("\n" + "=" * 78)
    print("##", title)
    print("=" * 78)


def show(fn) -> None:
    """跑一段會噴 schema 錯的程式，把類別名與原文完整印出來。"""
    try:
        fn()
        print("  (沒有噴錯)")
    except (pa.errors.SchemaError, pa.errors.SchemaErrors) as e:
        print(f"  [{type(e).__name__}]")
        print("  " + str(e).replace("\n", "\n  "))
    except Exception as e:  # noqa: BLE001
        print(f"  [{type(e).__name__}] {e}")


# ─────────────────────────────────────────────────────────────────────────────
# 課程資料：前五欄與 spike_pandera.py 完全同序同種子，數字才對得上
# ─────────────────────────────────────────────────────────────────────────────
rng = np.random.default_rng(0)
n = 500
orders = pd.DataFrame(
    {
        "order_id": range(n),
        "customer": rng.integers(1, 60, n),
        "amount": rng.gamma(2, 300, n).round(0),
        "returned": rng.random(n) < 0.08,
        "country": rng.choice(["TW", "JP", "US"], n),
    }
)
orders["refund"] = np.where(orders["returned"], orders["amount"], 0.0)
orders["sku"] = [f"{c}-{i % 9000 + 1000}" for c, i in zip(orders["country"], range(n), strict=True)]
orders["ordered_at"] = pd.Timestamp("2026-08-01") + pd.to_timedelta(rng.integers(0, 30, n), unit="D")

head("0 · 環境與資料")
print("pandera", pandera.__version__, "| pandas", pd.__version__, "| numpy", np.__version__)
print(orders.dtypes.to_string())
print("rows:", len(orders), "| 退貨筆數:", int(orders["returned"].sum()), "| 客戶數:", orders["customer"].nunique())
print("每國筆數:", orders["country"].value_counts().to_dict())
print(orders.head(3).to_string())

schema = pa.DataFrameSchema(
    {
        "order_id": pa.Column(int, pa.Check.ge(0), unique=True),
        "customer": pa.Column(int, pa.Check.between(1, 59)),
        "amount": pa.Column(float, pa.Check.gt(0), nullable=False),
        "returned": pa.Column(bool),
        "country": pa.Column(str, pa.Check.isin(["TW", "JP", "US"])),
    },
    checks=pa.Check(lambda d: len(d) >= 400, error="at least 400 rows"),
)

head("1 · 乾淨資料通過（validate 原樣回傳）")
ok = schema.validate(orders[["order_id", "customer", "amount", "returned", "country"]])
print("回傳型別:", type(ok).__name__, "| 列數:", len(ok), "| 與輸入相同物件?", ok is not orders)

# ─────────────────────────────────────────────────────────────────────────────
head("2 · SchemaError（不 lazy：只報第一個）vs SchemaErrors（lazy：全部）")
# ─────────────────────────────────────────────────────────────────────────────
bad = orders[["order_id", "customer", "amount", "returned", "country"]].copy()
bad.loc[0, "amount"] = -50
bad.loc[1, "country"] = "XX"
bad.loc[2, "customer"] = 99
bad.loc[3, "amount"] = np.nan

print("\n--- validate(bad) 不 lazy ---")
show(lambda: schema.validate(bad))

print("\n--- validate(bad, lazy=True) ---")
try:
    schema.validate(bad, lazy=True)
except pa.errors.SchemaErrors as e:
    fc = e.failure_cases
    print("  failure_cases 欄位:", list(fc.columns))
    print("  筆數:", len(fc))
    print("  " + fc[["schema_context", "column", "check", "failure_case", "index"]].to_string().replace("\n", "\n  "))
    print("\n  e.message 的 key:", list(e.message.keys()))
    print("  str(e) 前 6 行:")
    print("  " + "\n  ".join(str(e).splitlines()[:6]))

# ─────────────────────────────────────────────────────────────────────────────
head("3 · 逐一撞每種違約（都用 lazy=True 看 failure_cases）")
# ─────────────────────────────────────────────────────────────────────────────
base = orders[["order_id", "customer", "amount", "returned", "country"]]


def lazy_cases(df, sch=schema, label=""):
    print(f"\n--- {label} ---")
    try:
        sch.validate(df, lazy=True)
        print("  通過")
    except pa.errors.SchemaErrors as e:
        fc = e.failure_cases
        print("  " + fc[["schema_context", "column", "check", "failure_case", "index"]].head(6).to_string().replace("\n", "\n  "))
    except pa.errors.SchemaError as e:
        print(f"  [SchemaError] {e}")


# 3a 型別不符：int 欄來了 float
d = base.copy()
d["order_id"] = d["order_id"].astype(float)
lazy_cases(d, label="3a 型別不符（order_id 變 float64）")
print("  不 lazy 的訊息：")
show(lambda: schema.validate(d))

# 3b unique 重複
d = base.copy()
d.loc[10, "order_id"] = 0
lazy_cases(d, label="3b order_id 重複（unique=True）")
print("  不 lazy 的訊息：")
show(lambda: schema.validate(d))

# 3c nullable=False 缺值
d = base.copy()
d.loc[5, "amount"] = np.nan
lazy_cases(d, label="3c amount 缺值（nullable=False）")
print("  不 lazy 的訊息：")
show(lambda: schema.validate(d))

# 3d isin 新類別
d = base.copy()
d.loc[7, "country"] = "KR"
lazy_cases(d, label="3d country 出現新類別 KR（isin）")
print("  不 lazy 的訊息：")
show(lambda: schema.validate(d))

# 3e 欄位改名（上游把 amount 改叫 total）
d = base.rename(columns={"amount": "total"})
lazy_cases(d, label="3e 欄位改名 amount → total")
print("  不 lazy 的訊息：")
show(lambda: schema.validate(d))

# 3f 表級檢查失敗（列數不足）
lazy_cases(base.head(100), label="3f 只剩 100 列（表級 checks: at least 400 rows）")
print("  不 lazy 的訊息：")
show(lambda: schema.validate(base.head(100)))

# 3g 多欄同時壞：failure_cases 的排序
d = base.copy()
d.loc[0, "amount"] = -50
d.loc[1, "country"] = "XX"
d.loc[2, "customer"] = 99
d.loc[3, "amount"] = np.nan
d.loc[4, "order_id"] = 0
lazy_cases(d, label="3g 五種違約一次來")

# ─────────────────────────────────────────────────────────────────────────────
head("4 · coerce：自動轉型與轉型失敗")
# ─────────────────────────────────────────────────────────────────────────────
coerce_schema = pa.DataFrameSchema(
    {
        "order_id": pa.Column(int, pa.Check.ge(0)),
        "amount": pa.Column(float, pa.Check.gt(0)),
    },
    coerce=True,
)
str_df = pd.DataFrame({"order_id": ["1", "2", "3"], "amount": ["12.5", "99", "3"]})
print("輸入 dtypes:", dict(str_df.dtypes.astype(str)))
out = coerce_schema.validate(str_df)
print("coerce 後 dtypes:", dict(out.dtypes.astype(str)))
print("值:", out.to_dict("list"))

print("\n--- coerce 轉不動：'abc' → int ---")
show(lambda: coerce_schema.validate(pd.DataFrame({"order_id": ["1", "abc"], "amount": ["1.0", "2.0"]})))

print("\n--- 沒開 coerce，字串欄對上 int 宣告 ---")
no_coerce = pa.DataFrameSchema({"order_id": pa.Column(int)})
show(lambda: no_coerce.validate(pd.DataFrame({"order_id": ["1", "2"]})))

print("\n--- coerce 失敗在 lazy 模式下的 failure_cases ---")
try:
    coerce_schema.validate(pd.DataFrame({"order_id": ["1", "abc"], "amount": ["1.0", "2.0"]}), lazy=True)
except pa.errors.SchemaErrors as e:
    print(e.failure_cases[["schema_context", "column", "check", "failure_case", "index"]].to_string())

# ─────────────────────────────────────────────────────────────────────────────
head("5 · strict：多出來的欄位")
# ─────────────────────────────────────────────────────────────────────────────
strict_schema = pa.DataFrameSchema(
    {"order_id": pa.Column(int), "amount": pa.Column(float)},
    strict=True,
)
extra = base[["order_id", "amount"]].copy()
extra["note"] = "hi"
extra["internal_debug_flag"] = 1
print("--- strict=True 遇到多兩欄（不 lazy）---")
show(lambda: strict_schema.validate(extra))
print("\n--- strict=True 遇到多兩欄（lazy=True）---")
try:
    strict_schema.validate(extra, lazy=True)
except pa.errors.SchemaErrors as e:
    print(e.failure_cases[["schema_context", "column", "check", "failure_case", "index"]].to_string())
print("\n--- strict='filter'：多的欄位直接砍掉 ---")
filtered = pa.DataFrameSchema({"order_id": pa.Column(int), "amount": pa.Column(float)}, strict="filter").validate(extra)
print("  剩下欄位:", list(filtered.columns))

# ─────────────────────────────────────────────────────────────────────────────
head("6 · 自訂檢查：表級 lambda、element_wise、groupby、regex")
# ─────────────────────────────────────────────────────────────────────────────
rich = pa.DataFrameSchema(
    {
        "order_id": pa.Column(int, unique=True),
        "customer": pa.Column(int),
        "amount": pa.Column(float, pa.Check.gt(0)),
        "refund": pa.Column(float, pa.Check.ge(0)),
        "returned": pa.Column(bool),
        "country": pa.Column(str, pa.Check.isin(["TW", "JP", "US"])),
        "sku": pa.Column(str, pa.Check.str_matches(r"^[A-Z]{2}-\d{4}$")),
        "ordered_at": pa.Column(pa.DateTime, pa.Check.le(pd.Timestamp("2026-09-30"))),
    },
    checks=[
        pa.Check(lambda d: d["refund"] <= d["amount"], error="refund 不可超過 amount"),
        pa.Check(lambda d: d.groupby("country").size().min() >= 100, error="每個國家至少 100 筆"),
    ],
)
print("完整 schema 驗乾淨資料:", len(rich.validate(orders)), "列通過")

print("\n--- 欄間關係壞掉：refund > amount ---")
d = orders.copy()
d.loc[0, "refund"] = d.loc[0, "amount"] + 1
show(lambda: rich.validate(d))

print("\n--- 分組檢查壞掉：塞一個只有 3 筆的新國家（但 isin 也會一起噴）---")
d = orders.copy()
d.loc[:2, "country"] = "KR"
try:
    rich.validate(d, lazy=True)
except pa.errors.SchemaErrors as e:
    print(e.failure_cases[["schema_context", "column", "check", "failure_case", "index"]].to_string())

print("\n--- 正規表達式：sku 格式跑掉 ---")
d = orders.copy()
d.loc[0, "sku"] = "tw-1"
show(lambda: rich.validate(d))

print("\n--- element_wise=True：一列一列跑的檢查 ---")
ew = pa.DataFrameSchema({"amount": pa.Column(float, pa.Check(lambda v: v % 1 == 0, element_wise=True, error="金額必須是整數元"))})
print("  整數金額通過:", len(ew.validate(orders[["amount"]])))
d = orders[["amount"]].copy()
d.loc[0, "amount"] = 12.34
show(lambda: ew.validate(d))

print("\n--- pandera 原生 groupby 檢查（Column 層）---")
try:
    gb = pa.DataFrameSchema(
        {
            "country": pa.Column(str),
            "amount": pa.Column(float, pa.Check(lambda g: all(len(s) >= 100 for s in g.values()), groupby="country", error="每國至少 100 筆")),
        }
    )
    print("  通過:", len(gb.validate(orders[["country", "amount"]])))
    d = orders[["country", "amount"]].copy()
    d.loc[:2, "country"] = "KR"
    show(lambda: gb.validate(d))
except Exception as e:  # noqa: BLE001
    print(f"  [{type(e).__name__}] {e}")

print("\n--- 未來日期 ---")
d = orders.copy()
d.loc[0, "ordered_at"] = pd.Timestamp("2027-01-01")
show(lambda: rich.validate(d))

# ─────────────────────────────────────────────────────────────────────────────
head("7 · DataFrameModel（class 寫法）")
# ─────────────────────────────────────────────────────────────────────────────


class Orders(pa.DataFrameModel):
    order_id: int = pa.Field(ge=0, unique=True)
    customer: int = pa.Field(in_range={"min_value": 1, "max_value": 59})
    amount: float = pa.Field(gt=0, nullable=False)
    returned: bool
    country: str = pa.Field(isin=["TW", "JP", "US"])

    class Config:
        coerce = True
        strict = True

    @pa.check("amount", name="整數元")
    def amount_is_whole(cls, s: pd.Series) -> pd.Series:  # noqa: N805
        return s % 1 == 0

    @pa.dataframe_check(error="退貨率不可超過 30%")
    def return_rate(cls, df: pd.DataFrame) -> bool:  # noqa: N805
        return df["returned"].mean() <= 0.30


print("class 版驗乾淨資料:", len(Orders.validate(base)), "列")
print("\n--- class 版 lazy 驗髒資料 ---")
try:
    Orders.validate(bad, lazy=True)
except pa.errors.SchemaErrors as e:
    print(e.failure_cases[["schema_context", "column", "check", "failure_case", "index"]].to_string())

print("\n--- Config.strict=True 遇到多一欄 ---")
d = base.copy()
d["internal_debug_flag"] = 1
show(lambda: Orders.validate(d))

print("\n--- @pa.check 自訂檢查被觸發（金額有小數）---")
d = base.copy()
d.loc[0, "amount"] = 12.34
show(lambda: Orders.validate(d))

print("\n--- @pa.dataframe_check 被觸發（退貨率飆到 100%）---")
d = base.copy()
d["returned"] = True
show(lambda: Orders.validate(d))

print("\n--- Config.coerce 讓字串欄自動轉型 ---")
d = base.copy()
d["order_id"] = d["order_id"].astype(str)
d["amount"] = d["amount"].astype(str)
out = Orders.validate(d)
print("  coerce 後:", dict(out.dtypes.astype(str)))

print("\n--- DataFrameModel 轉回 DataFrameSchema ---")
print("  ", type(Orders.to_schema()).__name__, "| 欄位:", list(Orders.to_schema().columns))

# ─────────────────────────────────────────────────────────────────────────────
head("8 · infer_schema：從資料推 schema")
# ─────────────────────────────────────────────────────────────────────────────
inferred = pa.infer_schema(base)
print(repr(inferred)[:1400])
print("\n--- inferred.to_yaml() 前 30 行 ---")
print("\n".join(inferred.to_yaml().splitlines()[:30]))

# ─────────────────────────────────────────────────────────────────────────────
head("9 · to_yaml / from_yaml：把合約存成設定檔")
# ─────────────────────────────────────────────────────────────────────────────
y = schema.to_yaml()
print(y)
back = pa.DataFrameSchema.from_yaml(y)
print("from_yaml 後欄位:", list(back.columns))
print("兩邊 failure_cases 一致?")
fc_a = None
fc_b = None
try:
    schema.validate(bad, lazy=True)
except pa.errors.SchemaErrors as e:
    fc_a = e.failure_cases
try:
    back.validate(bad, lazy=True)
except pa.errors.SchemaErrors as e:
    fc_b = e.failure_cases
print("  原 schema:", len(fc_a), "筆 | YAML 載回:", len(fc_b), "筆 | 內容相同:", fc_a.equals(fc_b))
print("  注意：表級 checks 有沒有跟著存進 YAML？", "checks:" in y.split("columns:")[0])

# ─────────────────────────────────────────────────────────────────────────────
head("10 · 其他型別：Category / 時區")
# ─────────────────────────────────────────────────────────────────────────────
cat_df = base.copy()
cat_df["country"] = cat_df["country"].astype("category")
cat_schema = pa.DataFrameSchema({"country": pa.Column(pa.Category, pa.Check.isin(["TW", "JP", "US"]))})
print("Category 欄通過:", len(cat_schema.validate(cat_df[["country"]])))
print("\n--- 用 str 宣告去驗 category 欄 ---")
show(lambda: pa.DataFrameSchema({"country": pa.Column(str)}).validate(cat_df[["country"]]))

print("\n--- naive datetime 對上 pa.DateTime ---")
naive = pd.DataFrame({"ts": pd.to_datetime(["2026-08-01", "2026-08-02"])})
print("  dtype:", naive["ts"].dtype, "| 通過:", len(pa.DataFrameSchema({"ts": pa.Column(pa.DateTime)}).validate(naive)))

print("\n--- tz-aware 對上 pa.DateTime（沒宣告時區）---")
tz_df = pd.DataFrame({"ts": pd.to_datetime(["2026-08-01T00:00:00Z", "2026-08-02T00:00:00Z"])})
print("  dtype:", tz_df["ts"].dtype)
show(lambda: pa.DataFrameSchema({"ts": pa.Column(pa.DateTime)}).validate(tz_df))
print("\n--- 明寫 datetime64[ns, UTC] ---")
show(lambda: pa.DataFrameSchema({"ts": pa.Column("datetime64[ns, UTC]")}).validate(tz_df))
print("\n--- 明寫 pa.DateTime(unit='us', tz='UTC') ---")
show(lambda: print("  通過:", len(pa.DataFrameSchema({"ts": pa.Column(pa.DateTime(unit="us", tz="UTC"))}).validate(tz_df)), "列"))
print("\n--- coerce=True 讓時區自己對齊 ---")
show(lambda: print("  通過:", len(pa.DataFrameSchema({"ts": pa.Column("datetime64[ns, UTC]", coerce=True)}).validate(tz_df)), "列"))
print("\n--- 字串日期沒轉型就驗 ---")
show(lambda: pa.DataFrameSchema({"ts": pa.Column(pa.DateTime)}).validate(pd.DataFrame({"ts": ["2026-08-01", "2026-08-02"]})))
print("\n--- 字串日期 + coerce=True ---")
show(lambda: print("  通過:", len(pa.DataFrameSchema({"ts": pa.Column(pa.DateTime, coerce=True)}).validate(pd.DataFrame({"ts": ["2026-08-01", "2026-08-02"]}))), "列"))

head("完成")
