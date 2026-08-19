import marimo

__generated_with = "0.23.16"
app = marimo.App(width="medium", app_title="迴歸：畫一條最不冤枉的線（實驗場）")


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    # 🧪 迴歸：畫一條最不冤枉的線（實驗場）

    這是本課的**實驗場**。左側教學讀到哪，就回到這裡動手做——
    每一格程式碼都可以**直接修改、立即重跑**（點格子右上的 ▶，或按 `Ctrl+Enter`）。
    改壞了也沒關係：重新整理頁面就會回到原版。
    """
    )
    return


@app.cell
def _():
    import marimo as mo
    return (mo,)


@app.cell
def _():
    # 科學套件集中在這格 import
    import matplotlib.pyplot as plt
    import numpy as np
    from sklearn.linear_model import LinearRegression
    from sklearn.metrics import mean_squared_error
    from sklearn.model_selection import train_test_split
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import MinMaxScaler, PolynomialFeatures
    return (
        LinearRegression,
        MinMaxScaler,
        PolynomialFeatures,
        make_pipeline,
        mean_squared_error,
        np,
        plt,
        train_test_split,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 1️⃣ 先看資料：氣溫 vs 手搖飲銷量

    一個飲料攤記了 48 天的**當日最高溫**和**冰飲銷量**。
    點分佈明顯有趨勢（越熱賣越多），但不是完美的直線——
    天氣之外還有很多我們沒記到的因素（假日、雨天、隔壁在施工…），這就是**雜訊**。
    """
    )
    return


@app.cell
def _(np):
    rng = np.random.default_rng(7)
    temp = np.sort(rng.uniform(14, 36, 48))          # 當日最高溫 (°C)
    sales = 0.32 * (temp - 14) ** 2 + 18 + rng.normal(0, 9, 48)  # 冰飲銷量 (杯)
    return sales, temp


@app.cell
def _(plt, sales, temp):
    _fig, _ax = plt.subplots(figsize=(7, 4.5))
    _ax.scatter(temp, sales, c="#1C2B33", alpha=0.75)
    _ax.set_xlabel("daily high temp (C)")
    _ax.set_ylabel("iced drinks sold (cups)")
    _ax.set_title("48 days at a drink stand")
    _ax.grid(alpha=0.3)
    _fig.tight_layout()
    _fig
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 2️⃣ 最小平方法：錯得最少的那條線

    每個點到曲線的垂直距離就是模型「冤枉」的量（灰色細線）。
    **最小平方法**找的是讓這些冤枉的平方總和最小的模型。

    拉動「彎曲程度」（多項式次數）：

    - **次數 = 1**（直線）：系統性猜錯——最冷和最熱的日子都猜得太低、
      中段又猜得太高，灰線的方向有規律，代表模型**太簡單**。
    - **次數 = 2、3**：曲線貼上趨勢，冤枉明顯變小。
    - **次數拉到 12 以上**：曲線開始為了每一個點扭來扭去——先記住這個畫面，
      下一節拆穿它。
    """
    )
    return


@app.cell
def _(mo):
    degree_slider = mo.ui.slider(start=1, stop=15, step=1, value=1,
                                 label="彎曲程度（多項式次數）", show_value=True)
    degree_slider
    return (degree_slider,)


@app.cell
def _(
    LinearRegression,
    MinMaxScaler,
    PolynomialFeatures,
    degree_slider,
    make_pipeline,
    mean_squared_error,
    np,
    plt,
    sales,
    temp,
):
    _model = make_pipeline(MinMaxScaler(),
                           PolynomialFeatures(degree_slider.value),
                           LinearRegression())
    _model.fit(temp.reshape(-1, 1), sales)
    _pred = _model.predict(temp.reshape(-1, 1))
    _mse = mean_squared_error(sales, _pred)
    _grid = np.linspace(temp.min(), temp.max(), 200).reshape(-1, 1)
    _fig, _ax = plt.subplots(figsize=(7, 4.5))
    _ax.vlines(temp, sales, _pred, color="#9AA7AE", linewidth=1, alpha=0.8)
    _ax.scatter(temp, sales, c="#1C2B33", alpha=0.75, zorder=3)
    _ax.plot(_grid, _model.predict(_grid), c="#4C72B0", linewidth=2.5, zorder=4)
    _ax.set_xlabel("daily high temp (C)")
    _ax.set_ylabel("iced drinks sold (cups)")
    _ax.set_ylim(sales.min() - 25, sales.max() + 25)
    _ax.set_title(f"degree = {degree_slider.value}  |  mean squared error = {_mse:.0f}")
    _ax.grid(alpha=0.3)
    _fig.tight_layout()
    _fig
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 3️⃣ 過擬合現形：太會背，反而不會考

    上面的誤差是**訓練誤差**——模型看著答案算出來的分數，次數越高只會越低。
    真正的考驗是**沒看過的資料**：把 48 天拆成 36 天訓練、12 天當考題，
    每個次數都考一次：

    - **訓練誤差**（藍）：一路下降——模型越彎，越能把看過的點背起來。
    - **測試誤差**（紅）：先降後升——貼近真實趨勢時最低，
      開始背雜訊之後反而越考越差。這就是**過擬合**。

    挑模型不是挑「訓練分數最高的」，是挑**紅線最低的那個彎度**。
    """
    )
    return


@app.cell
def _(
    LinearRegression,
    MinMaxScaler,
    PolynomialFeatures,
    make_pipeline,
    mean_squared_error,
    np,
    plt,
    sales,
    temp,
    train_test_split,
):
    temp_tr, temp_te, sales_tr, sales_te = train_test_split(
        temp.reshape(-1, 1), sales, test_size=12, random_state=3
    )
    degrees = np.arange(1, 13)
    train_err, test_err = [], []
    for _d in degrees:
        _m = make_pipeline(MinMaxScaler(), PolynomialFeatures(_d), LinearRegression())
        _m.fit(temp_tr, sales_tr)
        train_err.append(mean_squared_error(sales_tr, _m.predict(temp_tr)))
        test_err.append(mean_squared_error(sales_te, _m.predict(temp_te)))
    _fig, _ax = plt.subplots(figsize=(7, 4.5))
    _ax.plot(degrees, train_err, "o-", c="#4C72B0", label="train error")
    _ax.plot(degrees, test_err, "o-", c="#C44E52", label="test error")
    _ax.set_yscale("log")
    _ax.set_xlabel("polynomial degree")
    _ax.set_ylabel("mean squared error (log scale)")
    _ax.set_title("memorizing vs. generalizing")
    _ax.legend()
    _ax.grid(alpha=0.3)
    _fig.tight_layout()
    _fig
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 4️⃣ 你的實驗區

    下面這格是你的，改完按 ▶ 重跑。建議挑戰（由易到難）：

    1. **LEVEL 1**：把 `my_degree` 改成 15，看預測值在資料範圍邊緣飛到哪去。
    2. **LEVEL 2**：用 40°C（資料裡最熱只有 36°C）問模型銷量——
      次數 2 和次數 12 的答案差多少？哪個你敢拿去備料？
    3. **LEVEL 3**：回到 1️⃣ 把雜訊 `rng.normal(0, 9, 48)` 的 9 改成 25，
      再看 3️⃣ 的紅線最低點移到哪——雜訊越大，模型該越簡單還是越彎？

    做完記得：**點左側教學頁的「下載 .py」把你的版本帶走**，
    在自己電腦用 `uvx marimo edit lesson.py` 就能繼續玩。
    """
    )
    return


@app.cell
def _(
    LinearRegression,
    MinMaxScaler,
    PolynomialFeatures,
    make_pipeline,
    np,
    sales,
    temp,
):
    # ===== 你的實驗區 =====
    # 改 my_degree 和 ask_temp，或整段重寫！
    my_degree = 2
    ask_temp = 30.0
    my_model = make_pipeline(MinMaxScaler(),
                             PolynomialFeatures(my_degree),
                             LinearRegression())
    my_model.fit(temp.reshape(-1, 1), sales)
    my_pred = my_model.predict(np.array([[ask_temp]]))[0]
    print(f"次數 {my_degree} 的模型說：{ask_temp}°C 那天大約賣 {my_pred:.0f} 杯")
    return


if __name__ == "__main__":
    app.run()
