# 資料驗證：用 pandera 幫資料寫合約——壞資料進不了管線
# 不需要 GPU——molab 免費 CPU 環境即可全程執行（全部在記憶體裡跑，不連任何伺服器）。
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "marimo",
#     "pandera>=0.20",
#     "dagster>=1.10",
#     "pandas",
#     "numpy",
#     "pyyaml",
#     "tabulate",
# ]
# ///
import marimo

__generated_with = "0.23.16"
app = marimo.App(width="medium", app_title="資料驗證：用 pandera 幫資料寫合約")


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    # 📋 資料驗證：用 pandera 幫資料寫合約

    ## 先講一個沒有錯誤訊息的災難

    週一早上，模型的預測全都偏低。你翻日誌——沒有例外、沒有 traceback、每一步都是綠的，
    排程準時跑完，報表準時寄出。查了三個小時才發現：上游系統上週改版，訂單金額的單位
    從「元」改成「分」，於是每一筆金額都變成原本的 100 倍；模型照樣算，只是算錯。

    這種故障有一個共同的樣子：**程式沒壞，資料變了。**常見的變法就那幾種——

    | 上游做了什麼 | 你的程式會怎樣 |
    |---|---|
    | 欄位改名（`amount` → `total`） | `KeyError`，至少會炸（這是最幸運的一種） |
    | 單位變了（元 → 分） | 照算，答案全錯，沒有任何訊息 |
    | 多了一批 `NaN` | 平均值悄悄偏移，或某些列被靜靜丟掉 |
    | 類別欄多了一個新值（多開一個國家） | one-hot 出現沒見過的欄，或被當成未知值 |
    | 主鍵重複（重跑一次抓取，資料進兩遍） | 每個客戶被算兩次，指標整體膨脹 |

    除了第一種，其他全都**不會拋例外**。你的管線會很開心地把錯的答案算完、存好、發出去。

    ## 資料驗證＝在入口簽一份合約

    上一課（模型監控）處理的是「模型上線之後」——用統計量看輸入分佈有沒有慢慢飄走。
    這一課處理更前面的一步：**資料剛進管線的那一刻**。做法不是統計，是**合約**：

    > 把「這份資料應該長什麼樣」寫成程式碼——欄位、型別、範圍、可不可以是空的、
    > 允許哪些值、欄與欄之間的關係——**每一批資料進來都對一次**。
    > 不合約就擋下來，並且說清楚是哪一列、哪一欄、違反哪一條。

    這件事有一個很划算的性質：**寫合約的成本是一次性的，收益是每一批資料。**
    而且它把「安靜的錯誤」變成「吵鬧的錯誤」——一個會擋住管線、指名道姓的錯誤訊息，
    永遠比一份看起來正常但其實是錯的報表便宜。

    `pandera` 就是做這件事的套件：語法像 pydantic，但主角是 DataFrame。

    ## 這份 notebook 帶你做完

    1. 第一份合約：`DataFrameSchema` 逐欄宣告型別、範圍、唯一、可否為空、允許值
    2. 讓它失敗：`validate()` 只報第一個 vs `lazy=True` 一次列出全部違約
    3. 六種上游變化，一次撞完——每一種的 `check` 名稱與真實錯誤原文
    4. 表級檢查與自訂檢查：欄間關係、分組、逐列判定、正規表達式
    5. `DataFrameModel`：class 寫法、`coerce` 自動轉型、`strict` 擋多餘欄位
    6. 型別與時間的陷阱：時區、字串日期、分類欄
    7. 合約進版控：`infer_schema` 起手、`to_yaml` / `from_yaml` 當設定檔
    8. 接進管線：Dagster 的 `@asset_check(blocking=True)`，壞資料擋住下游訓練
    9. 互動：挑一種破壞方式，看合約怎麼回應

    全部在你自己的執行環境裡跑，**不連任何伺服器、不需要 GPU**：資料是隨機產生的假訂單。
    從第一格往下全部執行即可（首次安裝套件約 1–2 分鐘）。
    """
    )
    return


@app.cell
def _():
    import logging
    import warnings

    import dagster as dg
    import marimo as mo
    import numpy as np
    import pandas as pd
    import pandera.pandas as pa

    warnings.filterwarnings("ignore")
    logging.getLogger("dagster").setLevel(logging.WARNING)
    # Dagster 每一步都會印日誌；notebook 裡關小聲（第 8 節會用到）
    QUIET = {"loggers": {"console": {"config": {"log_level": "CRITICAL"}}}}
    return QUIET, dg, mo, np, pa, pd


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 1️⃣ 第一份合約：逐欄宣告「應該長什麼樣」

    ### 先有資料

    這是一份假的訂單表，500 筆——形狀跟你每天早上從資料倉庫撈下來的那張表一樣：

    | 欄位 | 意思 | 應該長什麼樣 |
    |---|---|---|
    | `order_id` | 訂單編號 | 整數、不重複、不為負 |
    | `customer` | 客戶編號 | 整數，公司只有 59 位客戶 |
    | `amount` | 金額（元） | 浮點數、必須大於 0、不可以是空的 |
    | `returned` | 是否退貨 | 布林 |
    | `country` | 出貨國家 | 只會是 TW／JP／US 三選一 |

    右邊那一欄——「應該長什麼樣」——就是**合約的內容**。它現在只存在於你的腦袋裡
    （或某份沒人更新的文件裡）；接下來要把它寫成程式碼。
    """
    )
    return


@app.cell
def _(mo, np, pd):
    rng = np.random.default_rng(0)
    N_ORDERS = 500

    orders = pd.DataFrame(
        {
            "order_id": range(N_ORDERS),
            "customer": rng.integers(1, 60, N_ORDERS),
            "amount": rng.gamma(2, 300, N_ORDERS).round(0),
            "returned": rng.random(N_ORDERS) < 0.08,
            "country": rng.choice(["TW", "JP", "US"], N_ORDERS),
        }
    )

    mo.vstack(
        [
            mo.md(
                f"**{len(orders)} 筆訂單**：{orders['customer'].nunique()} 位客戶、"
                f"退貨 {int(orders['returned'].sum())} 筆（{orders['returned'].mean():.1%}）、"
                f"金額 {orders['amount'].min():.0f}–{orders['amount'].max():.0f} 元。"
                f"每國筆數：{orders['country'].value_counts().to_dict()}"
            ),
            mo.ui.table(orders.head(5).to_dict("records"), selection=None),
        ]
    )
    return N_ORDERS, orders, rng


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ### 把那一欄寫成程式碼

    `DataFrameSchema` 就是一本字典：**欄位名 → 這一欄的規矩**。每一欄用 `pa.Column` 宣告，
    第一個參數是型別，後面接你要的檢查：

    - `pa.Check.ge(0)`／`gt(0)`／`between(1, 59)`／`isin([...])`——內建的常用檢查
    - `unique=True`——這一欄不可以有重複值（主鍵）
    - `nullable=False`——不可以有空值（**這是預設值**，寫出來是為了讓讀的人知道你想過了）

    （第一行的 `import pandera.pandas as pa` 也值得看一眼：網路上很多範例寫
    `import pandera as pa`，實測還能用，但會噴 `FutureWarning: Importing pandas-specific
    classes and functions from the top-level pandera module will be removed in a future
    version of pandera.`——新程式一律用子模組那條路徑。）

    最後那個 `checks=`（注意是複數、放在整張表那一層）是**表級檢查**：它拿到的是整個
    DataFrame，可以檢查「列數夠不夠」「欄與欄的關係對不對」這種單看一欄看不出來的事。
    這裡先放一條最實用的：**至少要有 400 列**——上游只回傳一半資料，是非常常見的故障。

    ### validate 通過會發生什麼

    `schema.validate(df)` **通過就把資料原樣回傳**（內容一模一樣，只是一個新物件）。
    這個設計是故意的：它可以直接串在你的函式管道裡，
    `df = schema.validate(load_orders())`——驗證變成資料流的一站，而不是額外一句 if。
    """
    )
    return


@app.cell
def _(mo, orders, pa):
    order_schema = pa.DataFrameSchema(
        {
            "order_id": pa.Column(int, pa.Check.ge(0), unique=True),
            "customer": pa.Column(int, pa.Check.between(1, 59)),
            "amount": pa.Column(float, pa.Check.gt(0), nullable=False),
            "returned": pa.Column(bool),
            "country": pa.Column(str, pa.Check.isin(["TW", "JP", "US"])),
        },
        checks=pa.Check(lambda d: len(d) >= 400, error="at least 400 rows"),
    )

    validated = order_schema.validate(orders)

    mo.md(
        f"""
        ✅ **通過**：{len(validated)} 列。

        - 回傳型別：`{type(validated).__name__}`
        - 內容與輸入相同：`{validated.equals(orders)}`
        - 是同一個物件：`{validated is orders}`（所以拿回傳值繼續用，不要用原本那個變數）
        """
    )
    return order_schema, validated


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 2️⃣ 讓它失敗：一次一個，還是一次全部？

    合約寫得對不對，看它「通過」是看不出來的——**要看它擋不擋得住壞資料**。
    所以現在故意弄壞四筆，每一筆對應真實世界的一種意外：

    | 列 | 弄壞什麼 | 真實世界的對應 |
    |---|---|---|
    | 0 | `amount` 改成 −50 | 退款紀錄混進訂單表 |
    | 1 | `country` 改成 `"XX"` | 上游多開一個國家／代碼寫錯 |
    | 2 | `customer` 改成 99 | 測試帳號的資料流進正式表 |
    | 3 | `amount` 改成 `NaN` | 欄位遺失、join 沒對上 |

    ### 預設的 validate：只報第一個

    直接 `validate(bad_orders)` 會拋 **`SchemaError`**（單數），而且**只講它撞到的第一個問題**。
    這在開發時很方便（訊息短、一眼看完），但在生產環境會讓你陷入「修一個、跑一次、
    再炸下一個」的循環——四個問題就要跑四輪。
    """
    )
    return


@app.cell
def _(mo, np, order_schema, orders, pa):
    bad_orders = orders.copy()
    bad_orders.loc[0, "amount"] = -50
    bad_orders.loc[1, "country"] = "XX"
    bad_orders.loc[2, "customer"] = 99
    bad_orders.loc[3, "amount"] = np.nan

    try:
        order_schema.validate(bad_orders)
        first_error = "（沒有噴錯）"
    except pa.errors.SchemaError as e:
        first_error = str(e)

    mo.vstack(
        [
            mo.md("**`order_schema.validate(bad_orders)`** ——不加任何參數："),
            mo.md(f"""```\n{first_error}\n```"""),
            mo.md(
                "只講了 `customer` 那一筆。另外三個問題還在資料裡，"
                "但你要先修好這一個、再跑一次才會看到下一個。"
            ),
        ]
    )
    return bad_orders, first_error


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ### `lazy=True`：一次收集全部

    加一個參數 `lazy=True`，pandera 就會**把所有欄位都驗完再一起報**，拋的是
    **`SchemaErrors`**（複數）。這兩個類別名字只差一個 s，是本課最容易搞混的地方：

    | | 什麼時候拋 | 內容 |
    |---|---|---|
    | `SchemaError`（單數） | `lazy=False`（預設） | 第一個撞到的問題，訊息是一句人話 |
    | `SchemaErrors`（複數） | `lazy=True` | 全部問題，`e.failure_cases` 是一張表 |

    `e.failure_cases` 是這一課最該記住的東西——**一張 DataFrame**，每一列是一筆違約：

    - `schema_context`：出事的層級（`Column` 是某一欄，`DataFrameSchema` 是整張表）
    - `column`：哪一欄
    - `check`：違反哪一條（名稱是 pandera 產生的字串，等一下你會在錯誤訊息裡一直看到它）
    - `failure_case`：**那個壞掉的值本身**
    - `index`：**哪一列**（原始 DataFrame 的索引，可以直接拿去 `df.loc[...]` 撈出來看）

    有了這張表，你就能做三件單一錯誤訊息做不到的事：一次修完、把它存成報表寄給上游、
    以及——第 8 節會做的——把它掛在管線的檢查結果上。
    """
    )
    return


@app.cell
def _(bad_orders, mo, order_schema, pa):
    try:
        order_schema.validate(bad_orders, lazy=True)
        lazy_cases = None
    except pa.errors.SchemaErrors as e:
        lazy_cases = e.failure_cases

    mo.vstack(
        [
            mo.md(
                f"**`validate(bad_orders, lazy=True)`** → `SchemaErrors`，"
                f"`failure_cases` 共 **{len(lazy_cases)} 筆**"
                f"（欄位：`{'`, `'.join(lazy_cases.columns)}`）："
            ),
            mo.ui.table(lazy_cases.astype(str).to_dict("records"), selection=None),
            mo.md(
                "四筆全在。`index` 那一欄直接告訴你去看第 0、1、2、3 列——"
                "把這張表寄給上游，對方不用問「你說的壞資料是哪一筆」。"
            ),
        ]
    )
    return (lazy_cases,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 3️⃣ 六種上游變化，一次撞完

    現在把開場那張表裡的每一種變化都真的做一次，看合約分別回什麼。
    重點不是背訊息，是**建立一個對應**：看到某個 `check` 名稱，就知道上游發生了什麼事。

    特別注意最後兩種，它們跟前面四種不一樣：

    - **欄位改名**：`schema_context` 是 `DataFrameSchema` 不是 `Column`，`check` 是
      `column_in_dataframe`——因為問題不在某一欄的值，是**那一欄根本不見了**。
      這是唯一一種「不驗證也會炸」的變化，但合約讓它在入口就炸，而不是在第 40 行的
      `df["amount"] * 1.05` 才炸。
    - **列數不足**：`column` 是空的，`check` 是你自己寫的那句 `at least 400 rows`——
      表級檢查的失敗長這樣。
    """
    )
    return


@app.cell
def _(mo, order_schema, orders, pa):
    def _break(kind, df):
        """回傳一份被弄壞的資料。"""
        d = df.copy()
        if kind == "型別變了（int → float）":
            d["order_id"] = d["order_id"].astype(float)
        elif kind == "主鍵重複（抓兩次）":
            d.loc[10, "order_id"] = 0
        elif kind == "多了缺值（NaN）":
            d.loc[5, "amount"] = float("nan")
        elif kind == "類別多一個新值（KR）":
            d.loc[7, "country"] = "KR"
        elif kind == "欄位改名（amount → total）":
            d = d.rename(columns={"amount": "total"})
        elif kind == "只回傳 100 列":
            d = d.head(100)
        return d

    def _cases(df):
        """跑一次 lazy 驗證，回傳 (failure_cases, 不 lazy 的第一句訊息)。"""
        try:
            order_schema.validate(df, lazy=True)
            fc = None
        except pa.errors.SchemaErrors as e:
            fc = e.failure_cases
        try:
            order_schema.validate(df)
            msg = "（通過）"
        except (pa.errors.SchemaError, pa.errors.SchemaErrors) as e:
            msg = str(e).splitlines()[0]
        return fc, msg

    KINDS = [
        "型別變了（int → float）",
        "主鍵重複（抓兩次）",
        "多了缺值（NaN）",
        "類別多一個新值（KR）",
        "欄位改名（amount → total）",
        "只回傳 100 列",
    ]

    break_rows = []
    for _kind in KINDS:
        _fc, _msg = _cases(_break(_kind, orders))
        _row = _fc.iloc[0]
        break_rows.append(
            {
                "上游做了什麼": _kind,
                "schema_context": _row["schema_context"],
                "column": str(_row["column"]),
                "check": _row["check"],
                "failure_case": str(_row["failure_case"]),
                "index": str(_row["index"]),
                "筆數": len(_fc),
            }
        )
        break_rows[-1]["不 lazy 的訊息"] = _msg

    mo.vstack(
        [
            mo.ui.table(break_rows, selection=None),
            mo.md(
                "六種變化，六種 `check` 名稱。把這張表存起來——"
                "以後半夜看到管線紅了，第一眼看 `check` 就知道要去問上游什麼問題。"
            ),
        ]
    )
    return KINDS, break_rows


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 4️⃣ 表級檢查與自訂檢查：一欄看不出來的事

    到目前為止的檢查都在「一欄之內」。但真實的資料規則常常跨欄：

    - 退款金額不可以超過訂單金額（`refund <= amount`）
    - 每個國家至少要有 100 筆，不然這批資料可能只抓到一部分
    - 訂單編號要符合 `國碼-四位數` 的格式
    - 訂單日期不可以是未來

    這些都靠 `pa.Check` 加上一個你自己寫的函式。有兩個地方可以放：

    | 放在哪 | 函式拿到什麼 | 適合 |
    |---|---|---|
    | `pa.Column(..., pa.Check(fn))` | **那一欄**的 Series | 單欄規則 |
    | `DataFrameSchema(..., checks=pa.Check(fn))` | **整張表**的 DataFrame | 跨欄規則、整批規則 |

    ### 一個決定「錯誤訊息有多好用」的細節

    自訂函式**回傳什麼**，決定了 pandera 能不能告訴你「哪一列壞掉」：

    - **回傳布林 Series**（每列一個 True/False）→ pandera 逐列判定，
      `failure_case` 會是**壞掉的那一列**、`index` 有值
    - **回傳單一 bool**（例如 `.all()` 或比大小）→ pandera 只知道整批不合格，
      `failure_case` 是 `False`、`index` 是空的

    兩種都對，但**能寫成 Series 就寫成 Series**——出事時你會很感謝當初多想了那三秒。

    （一個實測到的小意外：表級檢查回傳 Series 時，pandera 會把**壞掉那一列的每一欄各記一筆**
    `failure_case`。八欄的表壞一列，`failure_cases` 就是 8 列、`index` 全部是 `0`——
    看起來很多，其實講的是同一列。看 `index` 不要看筆數。）
    """
    )
    return


@app.cell
def _(N_ORDERS, mo, orders, pd, rng):
    # 加三欄，讓跨欄／格式／時間的規則有東西可以驗
    rich_orders = orders.copy()
    rich_orders["refund"] = (rich_orders["returned"] * rich_orders["amount"]).astype(float)
    rich_orders["sku"] = [
        f"{c}-{i % 9000 + 1000}" for c, i in zip(rich_orders["country"], range(N_ORDERS), strict=True)
    ]
    rich_orders["ordered_at"] = pd.Timestamp("2026-08-01") + pd.to_timedelta(
        rng.integers(0, 30, N_ORDERS), unit="D"
    )

    mo.vstack(
        [
            mo.md(
                "多了三欄：`refund`（退貨才有金額）、`sku`（`國碼-四位數`）、"
                "`ordered_at`（2026-08-01 起 30 天內）。"
            ),
            mo.ui.table(rich_orders.head(4).to_dict("records"), selection=None),
        ]
    )
    return (rich_orders,)


@app.cell
def _(mo, pa, pd, rich_orders):
    rich_schema = pa.DataFrameSchema(
        {
            "order_id": pa.Column(int, unique=True),
            "customer": pa.Column(int, pa.Check.between(1, 59)),
            "amount": pa.Column(float, pa.Check.gt(0)),
            "refund": pa.Column(float, pa.Check.ge(0)),
            "returned": pa.Column(bool),
            "country": pa.Column(str, pa.Check.isin(["TW", "JP", "US"])),
            # 正規表達式：整串必須是「兩個大寫字母 - 四位數字」
            "sku": pa.Column(str, pa.Check.str_matches(r"^[A-Z]{2}-\d{4}$")),
            # 時間欄：不可以是未來的日期
            "ordered_at": pa.Column(pa.DateTime, pa.Check.le(pd.Timestamp("2026-09-30"))),
        },
        checks=[
            # 回傳 Series → 逐列判定，出事時知道是哪一列
            pa.Check(lambda d: d["refund"] <= d["amount"], error="refund 不可超過 amount"),
            # 回傳 bool → 整批判定，只知道這批不合格
            pa.Check(lambda d: d.groupby("country").size().min() >= 100, error="每個國家至少 100 筆"),
        ],
    )

    mo.md(f"✅ 完整合約驗乾淨資料：**{len(rich_schema.validate(rich_orders))} 列通過**。")
    return (rich_schema,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ### 一條一條弄壞，看訊息怎麼變

    下面五種破壞各對應上面一條規則。特別看第一條與第二條的差別：
    退款超額那條指得出「第 0 列、整列的值」，每國筆數那條只回一個 `False`——
    這就是剛剛說的「回傳 Series vs 回傳 bool」。
    """
    )
    return


@app.cell
def _(mo, pa, pd, rich_orders, rich_schema):
    def _try(df):
        try:
            rich_schema.validate(df)
            return "（通過）"
        except (pa.errors.SchemaError, pa.errors.SchemaErrors) as e:
            return str(e)

    _d1 = rich_orders.copy()
    _d1.loc[0, "refund"] = _d1.loc[0, "amount"] + 1

    # US 只抓到 50 筆（上游分頁抓一半就斷了）
    _d2 = pd.concat(
        [rich_orders[rich_orders["country"] != "US"], rich_orders[rich_orders["country"] == "US"].head(50)]
    )

    _d3 = rich_orders.copy()
    _d3.loc[0, "sku"] = "tw-1"

    _d4 = rich_orders.copy()
    _d4.loc[0, "ordered_at"] = pd.Timestamp("2027-01-01")

    broken_msgs = [
        ("① 退款超過訂單金額（表級，回傳 Series）", _try(_d1)),
        ("② 某國筆數不足（表級，回傳 bool）", _try(_d2)),
        ("③ sku 格式跑掉", _try(_d3)),
        ("④ 訂單日期在未來", _try(_d4)),
    ]

    mo.vstack(
        [mo.md(f"**{_t}**\n\n```\n{_m}\n```") for _t, _m in broken_msgs]
    )
    return (broken_msgs,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ### `element_wise=True`：一格一格跑

    還有一種寫法：`element_wise=True` 讓你的函式**一次只拿到一個值**（而不是整條 Series）。
    寫起來最直覺，代價是**慢**——它是 Python 迴圈，不是向量化運算。
    規則能用向量化寫就用向量化，`element_wise` 留給「真的沒辦法向量化」的邏輯
    （例如呼叫某個現成的驗證函式）。

    下面這條規則是「金額必須是整數元」——公司的系統不收小數。
    """
    )
    return


@app.cell
def _(mo, pa, rich_orders):
    whole_amount = pa.DataFrameSchema(
        {
            "amount": pa.Column(
                float,
                pa.Check(lambda v: v % 1 == 0, element_wise=True, error="金額必須是整數元"),
            )
        }
    )

    _ok = len(whole_amount.validate(rich_orders[["amount"]]))

    _d = rich_orders[["amount"]].copy()
    _d.loc[0, "amount"] = 12.34
    try:
        whole_amount.validate(_d)
        _msg = "（通過）"
    except pa.errors.SchemaError as e:
        _msg = str(e)

    mo.md(
        f"""
        乾淨資料 **{_ok} 列通過**；把第 0 列改成 12.34 之後：

        ```
        {_msg}
        ```

        注意訊息裡的 `failure cases: 12.34`——`element_wise` 的好處就是它知道是哪一個值。
        """
    )
    return (whole_amount,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 5️⃣ `DataFrameModel`：像 pydantic 那樣寫合約

    同一份合約有第二種寫法：繼承 `pa.DataFrameModel`，用**型別註記**宣告欄位。
    如果你用過 pydantic 或 dataclass，這個形狀會很熟悉。

    三個新東西：

    - **`pa.Field(...)`**：欄位層的檢查搬到這裡（`ge`、`gt`、`isin`、`unique`、`nullable`…）
    - **`class Config`**：整張表的開關。這一課會用到最重要的兩個：
      - `coerce = True`——**自動轉型**。上游把數字存成字串（CSV 讀進來最常見）時，
        pandera 會先幫你轉成宣告的型別再驗；轉不動才報錯。
      - `strict = True`——**多出來的欄位要不要擋**。預設是不擋（多的欄位放行），
        開了就會要求「資料的欄位集合必須跟合約完全一致」。
    - **`@pa.check("欄名")` / `@pa.dataframe_check`**：自訂檢查寫成方法，
      比 lambda 好讀、可以取名字、錯誤訊息裡會顯示那個名字

    ### 兩種寫法怎麼選

    | | `DataFrameSchema`（字典） | `DataFrameModel`（class） |
    |---|---|---|
    | 形狀 | 一個物件，可以在執行時組出來 | 一個類別，寫死在程式碼裡 |
    | 適合 | 欄位是動態的（設定檔、依日期生成） | 欄位固定，全公司共用同一份定義 |
    | 好處 | 可以塞進 dict、迴圈、`to_yaml` | 型別註記可當函式簽名 `DataFrame[Orders]`，編輯器會補全 |
    | 轉換 | `Orders.to_schema()` 隨時轉成字典版 | — |

    **它們是同一個東西的兩張臉**——`Orders.to_schema()` 就會得到一個 `DataFrameSchema`。
    團隊裡選一種寫，別兩種混著用。
    """
    )
    return


@app.cell
def _(bad_orders, mo, orders, pa, pd):
    class Orders(pa.DataFrameModel):
        order_id: int = pa.Field(ge=0, unique=True)
        customer: int = pa.Field(in_range={"min_value": 1, "max_value": 59})
        amount: float = pa.Field(gt=0, nullable=False)
        returned: bool
        country: str = pa.Field(isin=["TW", "JP", "US"])

        class Config:
            coerce = True  # 字串數字自動轉型
            strict = True  # 多出來的欄位一律擋下

        @pa.check("amount", name="整數元")
        def amount_is_whole(cls, s: pd.Series) -> pd.Series:
            return s % 1 == 0

        @pa.dataframe_check(error="退貨率不可超過 30%")
        def return_rate(cls, df: pd.DataFrame) -> bool:
            return df["returned"].mean() <= 0.30

    _ok = len(Orders.validate(orders))

    try:
        Orders.validate(bad_orders, lazy=True)
        _fc = None
    except pa.errors.SchemaErrors as e:
        _fc = e.failure_cases

    mo.vstack(
        [
            mo.md(
                f"class 版驗乾淨資料：**{_ok} 列通過**；驗同一份髒資料："
                f"**{len(_fc)} 筆違約**——跟第 2 節字典版的結果一模一樣。"
            ),
            mo.ui.table(
                _fc[["schema_context", "column", "check", "failure_case", "index"]]
                .astype(str)
                .to_dict("records"),
                selection=None,
            ),
        ]
    )
    return (Orders,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ### `coerce` 與 `strict` 各擋掉什麼

    這兩個開關解決的是完全不同的問題，但都很常在真實管線裡救命：

    - **`coerce`**：從 CSV／JSON 讀進來的欄位常常整欄是字串。沒開 `coerce`，
      `pa.Column(int)` 對上字串欄會直接拒絕；開了就先轉再驗，**轉不動才報錯**——
      而且轉不動的時候，它會告訴你是**哪一個值**轉不動。
    - **`strict`**：上游偷偷多送一欄，通常不會弄壞什麼——直到有人寫了
      `df.to_sql(...)` 或 `pd.get_dummies(df)`。`strict=True` 讓「多一欄」也變成違約；
      `strict="filter"` 則是更務實的第三條路：**把不在合約裡的欄位直接砍掉**，
      下游只會看到你宣告過的欄位。
    """
    )
    return


@app.cell
def _(Orders, mo, orders, pa):
    # coerce：整欄字串自動轉回數字
    _str_df = orders.copy()
    _str_df["order_id"] = _str_df["order_id"].astype(str)
    _str_df["amount"] = _str_df["amount"].astype(str)
    _coerced = Orders.validate(_str_df)

    # coerce 轉不動
    _abc = orders.head(3).copy()
    _abc["amount"] = _abc["amount"].astype(str)
    _abc.loc[0, "amount"] = "abc"
    try:
        Orders.validate(_abc)
        _coerce_err = "（通過）"
    except (pa.errors.SchemaError, pa.errors.SchemaErrors) as e:
        _coerce_err = str(e)

    # strict：多一欄
    _extra = orders.copy()
    _extra["internal_debug_flag"] = 1
    try:
        Orders.validate(_extra)
        _strict_err = "（通過）"
    except (pa.errors.SchemaError, pa.errors.SchemaErrors) as e:
        _strict_err = str(e)

    # strict="filter"：多的欄位直接砍掉
    _filtered = pa.DataFrameSchema(
        {"order_id": pa.Column(int), "amount": pa.Column(float)}, strict="filter"
    ).validate(_extra)

    mo.vstack(
        [
            mo.md(
                f"**`coerce = True`**：`order_id` 與 `amount` 整欄變成字串送進來，"
                f"`{dict(_str_df[['order_id', 'amount']].dtypes.astype(str))}` → "
                f"`{dict(_coerced[['order_id', 'amount']].dtypes.astype(str))}`，"
                f"{len(_coerced)} 列通過。"
            ),
            mo.md("**把其中一個值改成 `\"abc\"`**（轉不動）："),
            mo.md(f"""```\n{_coerce_err}\n```"""),
            mo.md("**`strict = True`** 遇到多一欄 `internal_debug_flag`："),
            mo.md(f"""```\n{_strict_err}\n```"""),
            mo.md(
                f"**`strict=\"filter\"`** 則是安靜地砍掉多的欄位，"
                f"回傳只剩 `{list(_filtered.columns)}`——"
                "適合「我只要我宣告過的欄位」的下游。"
            ),
        ]
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 6️⃣ 型別與時間：最容易寫錯的一節

    型別是合約裡最基本的一條，也是最常寫不對的一條。三個真實會撞到的坑：

    ### 坑一：時間欄的時區

    `pa.DateTime` 是**沒有時區**的時間。資料庫撈出來的欄位常常是**帶時區**的
    （`datetime64[..., UTC]`），拿去對 `pa.DateTime` 會直接被拒絕。
    更討厭的是：把宣告改寫成 `"datetime64[ns, UTC]"` 也可能還是不過——因為 pandas 的
    時間單位不只 `ns`（新版預設是 `us`），宣告寫死單位就綁死了 pandas 版本。

    **實務解法：開 `coerce=True`**，讓 pandera 幫你把欄位轉成宣告的型別，
    而不是要求上游剛好給你那個型別。

    ### 坑二：字串日期

    從 CSV 讀進來的日期是字串。合約寫 `pa.DateTime`、資料是 `str` → 直接不過。
    一樣：`coerce=True` 讓它先轉。**這其實是好事**——轉不動的日期
    （`"2026-13-45"`、`"N/A"`）會在入口就被指名，而不是變成 `NaT` 之後靜靜影響統計。

    ### 坑三：分類欄

    `country` 存成 `category` 省記憶體，但合約寫 `str` 就會被拒絕。
    分類欄要嘛宣告 `pa.Category`，要嘛開 `coerce`。
    `pa.Category` 搭 `Check.isin([...])` 是類別欄最完整的寫法：
    **同時管住「型別」與「允許值」**。
    """
    )
    return


@app.cell
def _(mo, orders, pa, pd):
    def _msg(schema, df):
        try:
            return f"✅ {len(schema.validate(df))} 列通過"
        except (pa.errors.SchemaError, pa.errors.SchemaErrors) as e:
            return f"❌ {str(e).splitlines()[0]}"

    _naive = pd.DataFrame({"ts": pd.to_datetime(["2026-08-01", "2026-08-02"])})
    _tz = pd.DataFrame({"ts": pd.to_datetime(["2026-08-01T00:00:00Z", "2026-08-02T00:00:00Z"])})
    _text = pd.DataFrame({"ts": ["2026-08-01", "2026-08-02"]})
    _cat = orders[["country"]].astype({"country": "category"})

    dtype_rows = [
        {
            "資料": f"沒有時區的時間（{_naive['ts'].dtype}）",
            "合約寫法": "pa.Column(pa.DateTime)",
            "結果": _msg(pa.DataFrameSchema({"ts": pa.Column(pa.DateTime)}), _naive),
        },
        {
            "資料": f"帶時區的時間（{_tz['ts'].dtype}）",
            "合約寫法": "pa.Column(pa.DateTime)",
            "結果": _msg(pa.DataFrameSchema({"ts": pa.Column(pa.DateTime)}), _tz),
        },
        {
            "資料": f"帶時區的時間（{_tz['ts'].dtype}）",
            "合約寫法": 'pa.Column("datetime64[ns, UTC]")',
            "結果": _msg(pa.DataFrameSchema({"ts": pa.Column("datetime64[ns, UTC]")}), _tz),
        },
        {
            "資料": f"帶時區的時間（{_tz['ts'].dtype}）",
            "合約寫法": 'pa.Column("datetime64[ns, UTC]", coerce=True)',
            "結果": _msg(
                pa.DataFrameSchema({"ts": pa.Column("datetime64[ns, UTC]", coerce=True)}), _tz
            ),
        },
        {
            "資料": "字串日期",
            "合約寫法": "pa.Column(pa.DateTime)",
            "結果": _msg(pa.DataFrameSchema({"ts": pa.Column(pa.DateTime)}), _text),
        },
        {
            "資料": "字串日期",
            "合約寫法": "pa.Column(pa.DateTime, coerce=True)",
            "結果": _msg(pa.DataFrameSchema({"ts": pa.Column(pa.DateTime, coerce=True)}), _text),
        },
        {
            "資料": "category 欄",
            "合約寫法": "pa.Column(str)",
            "結果": _msg(pa.DataFrameSchema({"country": pa.Column(str)}), _cat),
        },
        {
            "資料": "category 欄",
            "合約寫法": 'pa.Column(pa.Category, Check.isin([...]))',
            "結果": _msg(
                pa.DataFrameSchema(
                    {"country": pa.Column(pa.Category, pa.Check.isin(["TW", "JP", "US"]))}
                ),
                _cat,
            ),
        },
    ]

    mo.vstack(
        [
            mo.ui.table(dtype_rows, selection=None),
            mo.md(
                "看第 3 列與第 4 列：同樣的資料、同樣的宣告，差別只有 `coerce=True`。"
                "**型別的宣告是給人看的意圖，`coerce` 才是務實的執行策略。**"
            ),
        ]
    )
    return (dtype_rows,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 7️⃣ 合約進版控：`infer_schema` 起手，YAML 收工

    ### 從零開始寫合約很痛，所以別從零開始

    一張三十欄的表，要一欄一欄想「型別是什麼、範圍多少」會寫到放棄。
    `pa.infer_schema(df)` **看一眼資料，直接生一份草稿**：型別照抄、數值欄補上
    觀察到的最小最大值。

    **它產出的東西不能直接用**——因為它把「這一批資料剛好的樣子」寫成了規矩。
    等一下你會看到它給 `order_id` 的規則是 `less_than_or_equal_to: 499.0`：
    這批剛好 500 筆，所以最大的訂單編號是 499。明天第 501 筆訂單進來就違約了。

    正確用法是：**用它省下打字的力氣，然後人工把每一條規則改成「業務上真正的規矩」**。
    無意義的界線刪掉、真正的界線寫進去（金額必須大於 0、國家只有那三個）。
    """
    )
    return


@app.cell
def _(mo, orders, pa):
    inferred = pa.infer_schema(orders)
    inferred_yaml = inferred.to_yaml()

    mo.vstack(
        [
            mo.md("`pa.infer_schema(orders).to_yaml()` 的前 22 行："),
            mo.md(f"""```yaml\n{chr(10).join(inferred_yaml.splitlines()[:22])}\n```"""),
            mo.md(
                "型別全對，範圍全部是「這批資料的最小最大值」。"
                "`order_id` 那條 `less_than_or_equal_to: 499.0` 就是典型的「只對今天成立」的規則。"
            ),
        ]
    )
    return inferred, inferred_yaml


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ### 合約應該進版控

    合約是程式碼，本來就該進 git。但把它寫成 `.py` 有個限制：只有 Python 讀得懂。
    `schema.to_yaml()` 把合約變成一份**設定檔**——

    - 可以 code review：PR 上看得到「這次把 `country` 多加了一個 `KR`」
    - 資料工程、分析、後端可以共用同一份定義，不必都寫 Python
    - 可以按環境載不同的合約（測試環境放寬、正式環境收緊）

    `pa.DataFrameSchema.from_yaml(...)` 載回來就是一份完整的 schema，驗證行為一模一樣。

    ### 一個一定要知道的限制

    **表級的 `checks=` 不會被寫進 YAML。**下面會親手驗證這件事：
    存出來的 YAML 最後一行是 `checks: null`，那條「至少 400 列」消失了。
    原因不難理解——那是一個 Python lambda，沒辦法用 YAML 表達。

    所以真實專案的合約通常是**兩層**：欄位規則走 YAML（好 review、好共用），
    跨欄與整批的規則留在程式碼裡。**知道哪一半沒被存進去，比記住這個限制更重要。**
    """
    )
    return


@app.cell
def _(mo, bad_orders, order_schema, orders, pa):
    yaml_text = order_schema.to_yaml()
    schema_from_yaml = pa.DataFrameSchema.from_yaml(yaml_text)

    def _n_fail(sch, df):
        try:
            sch.validate(df, lazy=True)
            return 0
        except pa.errors.SchemaErrors as e:
            return len(e.failure_cases)

    _a1, _b1 = _n_fail(order_schema, bad_orders), _n_fail(schema_from_yaml, bad_orders)
    _a2, _b2 = _n_fail(order_schema, orders.head(100)), _n_fail(schema_from_yaml, orders.head(100))

    yaml_rows = [
        {"驗什麼": "四筆壞資料的 500 列", "原本的 schema": _a1, "YAML 載回來的": _b1, "一致": _a1 == _b1},
        {"驗什麼": "乾淨但只有 100 列", "原本的 schema": _a2, "YAML 載回來的": _b2, "一致": _a2 == _b2},
    ]

    mo.vstack(
        [
            mo.md(f"""```yaml\n{yaml_text.strip()}\n```"""),
            mo.md("**同一份資料、兩份 schema，違約數對照：**"),
            mo.ui.table(yaml_rows, selection=None),
            mo.md(
                "欄位規則完整保留（第一列一致）；表級的「至少 400 列」不見了"
                "（第二列：原本擋得住，YAML 版放行）。"
                "最後一行 `checks: null` 就是證據。"
            ),
        ]
    )
    return schema_from_yaml, yaml_rows, yaml_text


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 8️⃣ 接進管線：合約變成擋得住下游的閘門

    到這裡合約已經很完整了，但它還只是「你手動跑的一個函式」。
    最後一步是把它接進管線，讓它**自動在每一批資料進來時執行**，而且——

    > **不合格的資料，下游根本不准開始跑。**

    第 3 課用過的 Dagster `@asset_check(blocking=True)` 就是為這件事存在的。
    這一節把 pandera 塞進去：

    ```python
    @dg.asset_check(asset=raw_orders, blocking=True)
    def orders_contract(raw_orders):
        try:
            order_schema.validate(raw_orders, lazy=True)
            return dg.AssetCheckResult(passed=True, metadata={"violations": 0})
        except pa.errors.SchemaErrors as e:
            fc = e.failure_cases
            return dg.AssetCheckResult(passed=False, metadata={
                "violations": len(fc),
                "failures": dg.MetadataValue.md(fc.to_markdown(index=False)),
            })
    ```

    三個關鍵：

    - **`blocking=True`**：檢查沒過，run 直接失敗、下游資產一步都不跑。
      改成 `False` 的話，檢查照樣變紅、但下游照跑——那叫「警告」，不叫閘門。
    - **`lazy=True`**：這裡一定要 lazy。維運的人要的是「這批資料有哪些問題」，
      不是「第一個問題是什麼」。
    - **`MetadataValue.md(...)`**：把 `failure_cases` 轉成 markdown 表格掛在檢查結果上。
      Dagster 的 UI 會直接把它畫出來——**半夜看板的人不用開 notebook 就知道哪一欄壞了**。

    下面跑兩次同一條管線（乾淨一次、壞資料一次），比較三件事：
    run 成功了嗎、檢查過了嗎、`customer_summary` 有沒有被算出來。
    """
    )
    return


@app.cell
def _(QUIET, bad_orders, dg, mo, order_schema, orders, pa, pd):
    class FeedConfig(dg.Config):
        corrupt: bool = False  # True 就把「上游送來壞資料」的那一批餵進管線

    @dg.asset(description="從交易系統撈下來的當日訂單")
    def raw_orders(config: FeedConfig) -> pd.DataFrame:
        return bad_orders.copy() if config.corrupt else orders.copy()

    @dg.asset_check(asset=raw_orders, blocking=True, description="訂單必須符合 pandera 合約")
    def orders_contract(raw_orders: pd.DataFrame) -> dg.AssetCheckResult:
        try:
            order_schema.validate(raw_orders, lazy=True)
            return dg.AssetCheckResult(passed=True, metadata={"violations": 0})
        except pa.errors.SchemaErrors as e:
            fc = e.failure_cases
            return dg.AssetCheckResult(
                passed=False,
                metadata={
                    "violations": len(fc),
                    "failures": dg.MetadataValue.md(
                        fc[["column", "check", "failure_case", "index"]].to_markdown(index=False)
                    ),
                },
            )

    @dg.asset(description="下游：各國營收彙總（合約沒過就不該跑）")
    def customer_summary(raw_orders: pd.DataFrame) -> pd.DataFrame:
        return raw_orders.groupby("country")["amount"].sum().reset_index()

    PIPELINE = [raw_orders, orders_contract, customer_summary]

    def run_pipeline(corrupt: bool):
        return dg.materialize(
            PIPELINE,
            run_config={**QUIET, "ops": {"raw_orders": {"config": {"corrupt": corrupt}}}},
            raise_on_error=False,
        )

    run_clean = run_pipeline(corrupt=False)
    run_dirty = run_pipeline(corrupt=True)

    def _summary(res, label):
        ev = res.get_asset_check_evaluations()[0]
        mats = [e.asset_key.to_user_string() for e in res.get_asset_materialization_events()]
        return {
            "這一批": label,
            "run.success": res.success,
            "檢查過了嗎": "✅" if ev.passed else "❌",
            "violations": ev.metadata["violations"].value,
            "實體化的資產": ", ".join(mats),
        }

    pipeline_rows = [_summary(run_clean, "乾淨資料"), _summary(run_dirty, "壞資料")]
    _c, _d = pipeline_rows
    mo.vstack(
        [
            mo.md(
                f"**乾淨那一批**：`run.success = {_c['run.success']}`，"
                f"違約 {_c['violations']} 筆，實體化了 `{_c['實體化的資產']}`。  \n"
                f"**壞掉那一批**：`run.success = {_d['run.success']}`，"
                f"違約 {_d['violations']} 筆，實體化了 `{_d['實體化的資產']}`。"
            ),
            mo.ui.table(pipeline_rows, selection=None),
        ]
    )
    return (
        FeedConfig,
        PIPELINE,
        customer_summary,
        orders_contract,
        pipeline_rows,
        raw_orders,
        run_clean,
        run_dirty,
        run_pipeline,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ### 看懂上面那張表

    - **乾淨那一批**：run 成功，`raw_orders` 與 `customer_summary` 都被算出來。
    - **壞掉那一批**：run **失敗**，而且 `customer_summary` **不在實體化清單裡**——
      閘門關上了，下游一步都沒跑。這正是 `blocking=True` 的全部意義：
      壞資料不會變成壞報表、壞模型、壞決策。

    下面是這次失敗留下的兩樣東西：Dagster 的失敗訊息，
    以及掛在檢查上的 `failure_cases` markdown 表格（UI 上就是這張表）。
    """
    )
    return


@app.cell
def _(mo, run_dirty):
    _fail = [
        e.event_specific_data.error.message.strip()
        for e in run_dirty.all_events
        if e.event_type_value == "STEP_FAILURE"
    ]
    _ev = run_dirty.get_asset_check_evaluations()[0]

    mo.vstack(
        [
            mo.md("**run 的失敗訊息**："),
            mo.md(f"""```\n{_fail[0]}\n```"""),
            mo.md(f"**檢查的 severity**：`{_ev.severity}`（`AssetCheckResult` 的預設值就是 ERROR）"),
            mo.md("**掛在檢查上的 `failures` metadata**（Dagster UI 會直接畫成表格）："),
            mo.md(_ev.metadata["failures"].value),
        ]
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ### 擋下來之後呢？三種收尾，選一種寫進你的管線

    合約擋下壞資料只是第一步——**管線停在那裡沒人管，就只是換一種方式壞掉**。
    三種常見收尾：

    | 做法 | 怎麼做 | 適合 |
    |---|---|---|
    | **擋住＋通知** | `blocking=True`，檢查失敗觸發通知，人工判斷 | 資料錯了會出人命的場景（金流、醫療） |
    | **丟掉壞的列** | `DataFrameSchema(..., drop_invalid_rows=True)` ＋ `lazy=True`，違約的列直接不要 | 壞資料比例低、少幾列不影響結論（本課的資料丟掉 1 列剩 499 列） |
    | **隔離區** | 檢查改 `blocking=False`，壞的列寫進另一張表，好的列繼續走 | 每天都會有一點髒資料，但不能停線 |

    沒有標準答案，但**一定要選一個**——最糟的是沒想過，然後在半夜臨時決定。
    這三種都建立在同一件事上：你知道**確切是哪幾列、違反哪一條**。
    這就是為什麼前面要花那麼多篇幅講 `failure_cases`。
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 9️⃣ 互動：挑一種破壞方式，看合約怎麼回應

    下拉選單挑一種「上游出的意外」，按按鈕跑一次 `lazy=True` 驗證。
    每次注意三件事：

    1. **`check` 那一欄**——這是你半夜第一眼會看到的字串
    2. **`index` 有沒有值**——有值代表你能直接 `df.loc[index]` 撈出那幾列
    3. **上面的判決**——擋下（管線停住）還是放行（下游繼續）

    「全部一起來」那一項最接近真實世界：意外從來不會一次只來一個。
    """
    )
    return


@app.cell
def _(mo):
    break_kind = mo.ui.dropdown(
        options=[
            "不破壞（乾淨資料）",
            "負金額（退款混進來）",
            "新國家（KR）",
            "缺值（amount 變 NaN）",
            "重複 order_id（抓了兩次）",
            "欄位改名（amount → total）",
            "只回傳 100 列",
            "全部一起來",
        ],
        value="負金額（退款混進來）",
        label="上游這次出的意外",
    )
    break_button = mo.ui.run_button(label="送進合約驗一次")
    mo.hstack([break_kind, break_button], wrap=True, justify="start")
    return break_button, break_kind


@app.cell
def _(break_button, break_kind, mo, np, order_schema, orders, pa):
    mo.stop(not break_button.value, mo.md("*挑一種意外，按「送進合約驗一次」。*"))

    _d = orders.copy()
    _k = break_kind.value
    if _k in ("負金額（退款混進來）", "全部一起來"):
        _d.loc[0, "amount"] = -50
    if _k in ("新國家（KR）", "全部一起來"):
        _d.loc[1, "country"] = "KR"
    if _k in ("缺值（amount 變 NaN）", "全部一起來"):
        _d.loc[3, "amount"] = np.nan
    if _k in ("重複 order_id（抓了兩次）", "全部一起來"):
        _d.loc[10, "order_id"] = 0
    if _k in ("欄位改名（amount → total）", "全部一起來"):
        _d = _d.rename(columns={"amount": "total"})
    if _k in ("只回傳 100 列", "全部一起來"):
        _d = _d.head(100)

    try:
        order_schema.validate(_d, lazy=True)
        _fc = None
    except pa.errors.SchemaErrors as e:
        _fc = e.failure_cases

    if _fc is None:
        _verdict = mo.callout(
            mo.md(f"✅ **放行**：{len(_d)} 列全部符合合約，下游可以開始跑。"), kind="success"
        )
        _table = mo.md("*（沒有違約，`failure_cases` 是空的）*")
    else:
        _verdict = mo.callout(
            mo.md(
                f"⛔ **擋下**：{len(_fc)} 筆違約——"
                f"`{'`、`'.join(sorted(set(_fc['check'].astype(str))))}`。"
                "管線在這裡停住，下游一步都不跑。"
            ),
            kind="danger",
        )
        _table = mo.ui.table(
            _fc[["schema_context", "column", "check", "failure_case", "index"]]
            .astype(str)
            .head(12)
            .to_dict("records"),
            selection=None,
        )

    mo.vstack([_verdict, _table])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 🏆 延伸挑戰

    1. **LEVEL 1**：在 `order_schema` 的表級 `checks=` 再加一條「退貨率不可超過 15%」
       （本課資料實測是 8.4%，所以乾淨資料要能通過）。加完先驗乾淨資料確認通過，
       再把 `returned` 整欄設成 `True`，確認它擋得下來。
    2. **LEVEL 2**：用 `DataFrameModel` 把**第 4 節那份 8 欄的 `rich_schema`** 整份重寫
       （`refund`、`sku`、`ordered_at` 都要），並在 `Config` 加上 `strict = True`。
       然後拿**第 1 節那份 5 欄的 `orders`** 去驗——想想看，這次會是「多欄位」還是「少欄位」的錯？
    3. **LEVEL 3**：把 `rich_schema` 存成 YAML 檔、在另一個 cell 用 `from_yaml` 載回來，
       驗同一份資料，比對兩邊的 `failure_cases` 是否完全一致。
       *驗證方式*：先用「有欄位違約」的資料比一次（應該一致），
       再用「只有表級規則違約」的資料比一次——第 7 節的結論會在這裡再現。

    先自己試，卡住再展開下面的提示與參考解答。
    帶得走：下載本檔後 `uvx marimo edit --sandbox 檔名.py`
    在自己電腦繼續玩（依賴會自動安裝）。
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.accordion(
        {
            "💡 LEVEL 1 參考解答": mo.md(
                r"""
    ```python
    strict_schema = pa.DataFrameSchema(
        order_schema.columns,                      # 欄位規則整份沿用
        checks=[
            pa.Check(lambda d: len(d) >= 400, error="at least 400 rows"),
            pa.Check(lambda d: d["returned"].mean() <= 0.15, error="退貨率不可超過 15%"),
        ],
    )

    print(len(strict_schema.validate(orders)))          # 500（實測退貨率 8.4%，通過）

    all_returned = orders.copy()
    all_returned["returned"] = True
    try:
        strict_schema.validate(all_returned)
    except pa.errors.SchemaError as e:
        print(e)
    ```

    你應該看到類似這樣的訊息（表級檢查、回傳的是單一 bool，所以沒有列號）：

    ```
    DataFrameSchema 'None' failed series or dataframe validator 1: <Check <lambda>: 退貨率不可超過 15%>
    ```

    注意結尾的 `validator 1`——它是 `checks` 清單裡的**第幾條**（從 0 開始）。
    這也是為什麼每條自訂檢查都該給 `error=`：不然訊息裡只會有一個 `<lambda>`。
    """
            ),
            "💡 LEVEL 2 參考解答": mo.md(
                r"""
    ```python
    class RichOrders(pa.DataFrameModel):
        order_id: int = pa.Field(unique=True)
        customer: int = pa.Field(in_range={"min_value": 1, "max_value": 59})
        amount: float = pa.Field(gt=0)
        refund: float = pa.Field(ge=0)
        returned: bool
        country: str = pa.Field(isin=["TW", "JP", "US"])
        sku: str = pa.Field(str_matches=r"^[A-Z]{2}-\d{4}$")
        ordered_at: pa.typing.Series[pa.typing.DateTime]

        class Config:
            coerce = True
            strict = True

        @pa.dataframe_check(error="refund 不可超過 amount")
        def refund_le_amount(cls, df):
            return df["refund"] <= df["amount"]

    print(len(RichOrders.validate(rich_orders)))     # 500，通過

    RichOrders.validate(orders)                      # 只有 5 欄的那份
    ```

    答案是**少欄位**，不是多欄位——訊息會像這樣（`column_in_dataframe`，
    跟第 3 節「欄位改名」撞到的是同一條）：

    ```
    column 'refund' not in dataframe. Columns in dataframe: ['order_id', 'customer', 'amount', 'returned', 'country']
    ```

    `strict=True` 管的是「**資料多送了合約沒有的欄位**」；
    「資料少了合約要求的欄位」不管你開不開 strict，本來就會被擋。
    很多人以為 `strict` 是「嚴格模式，兩邊都管」——它只管一個方向。
    """
            ),
            "💡 LEVEL 3 提示": mo.md(
                r"""
    方向：

    ```python
    from pathlib import Path

    Path("rich_schema.yaml").write_text(rich_schema.to_yaml())
    back = pa.DataFrameSchema.from_yaml(Path("rich_schema.yaml").read_text())

    def n_fail(sch, df):
        try:
            sch.validate(df, lazy=True); return 0
        except pa.errors.SchemaErrors as e:
            return len(e.failure_cases)
    ```

    **怎麼驗證自己做對了**——要比兩次，兩次的結論不一樣才算做完：

    1. 拿**只違反欄位規則**的資料比（例如把第 2 列的 `customer` 改成 99）：
       兩邊都是 **1 筆**，`failure_cases` 用 `.equals()` 比是 `True`——完全一致。
    2. 拿**只違反表級規則**的資料比（把第 0 列的 `refund` 改成比 `amount` 大 1）：
       原本的 schema 抓到 **8 筆**（同一列的八個欄位各記一筆，`index` 全是 0），
       YAML 載回來的那份 **0 筆**——直接放行。

    選破壞方式時要小心「連坐」：把 `country` 改成 `KR` 看起來只違反 `isin`，
    但它同時讓「每個國家至少 100 筆」也不成立（KR 只有 1 筆），
    於是原本的 schema 抓到 2 筆、YAML 版 1 筆——比出來不一致，卻不是你想驗的那件事。

    第二次的差異就是本課的重點結論：`to_yaml()` 存不下表級的 `checks=`
    （存出來的 YAML 最後一行是 `checks: null`），因為那是 Python 函式。
    所以「合約進版控」實務上是兩層：欄位規則走 YAML，跨欄規則留在程式碼裡，
    而且**要在文件裡寫清楚哪一半在哪裡**。

    進階：`rich_schema` 裡的 `sku` 用了正規表達式——去看看它有沒有被存進 YAML
    （提示：欄位層的內建檢查都存得下來，只有你自己寫的函式存不下來）。
    """
            ),
        }
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 📌 帶走這幾句

    1. **管線最常見的故障不是程式 bug，是上游資料悄悄變了**——而且大部分變化不會拋例外。
    2. **合約寫一次，每一批資料驗一次**：`DataFrameSchema` 逐欄宣告型別、範圍、唯一、
       可否為空、允許值，加上表級的跨欄與整批規則。
    3. **生產環境一律 `lazy=True`**：`failure_cases` 給你「哪一列、哪一欄、違反哪一條」，
       一次修完，而不是修一個炸一個。
    4. **`coerce` 是務實的執行策略**：型別宣告是意圖，`coerce` 讓上游的字串數字、
       時區差異不會變成「合約太嚴格所以大家都不用」。
    5. **合約要進版控**（`to_yaml`），但要知道表級 `checks` 存不進去。
    6. **接進管線才算完成**：`@asset_check(blocking=True)` ＋ `failure_cases` 當 metadata，
       壞資料在入口就被擋住，下游一步都不跑。

    下一課是 **MLflow Tracing**——這一課守的是「資料進來時」，
    下一課要看的是「LLM 應用跑起來之後，每一步到底發生了什麼」。
    """
    )
    return


if __name__ == "__main__":
    app.run()
