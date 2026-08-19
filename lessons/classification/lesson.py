import marimo

__generated_with = "0.23.16"
app = marimo.App(width="medium", app_title="分類：教機器做判斷（實驗場）")


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    # 🧪 分類：教機器做判斷（實驗場）

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
    from sklearn.neighbors import KNeighborsClassifier
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler
    return KNeighborsClassifier, StandardScaler, make_pipeline, np, plt


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 1️⃣ 先看資料：120 顆果實

    橘子（orange）和葡萄柚（grapefruit）各 60 顆，每顆量了**重量**和**直徑**。
    人眼一看就知道大概怎麼分——分類要做的，就是讓機器也學會這件事。
    注意中間那塊曖昧地帶：有些橘子長得特別大、有些葡萄柚特別小。
    """
    )
    return


@app.cell
def _(np):
    rng = np.random.default_rng(42)
    n_each = 60
    # 橘子偏小偏輕、葡萄柚偏大偏重，兩群故意留一點重疊
    orange = np.column_stack([
        rng.normal(140, 25, n_each),   # 重量 (g)
        rng.normal(7.0, 0.8, n_each),  # 直徑 (cm)
    ])
    grapefruit = np.column_stack([
        rng.normal(220, 35, n_each),
        rng.normal(9.5, 1.0, n_each),
    ])
    X = np.vstack([orange, grapefruit])
    y = np.array([0] * n_each + [1] * n_each)  # 0 = orange, 1 = grapefruit
    return X, y


@app.cell
def _(X, plt, y):
    _fig, _ax = plt.subplots(figsize=(7, 4.5))
    _ax.scatter(X[y == 0, 0], X[y == 0, 1], c="#DD8452", edgecolors="white",
                alpha=0.85, label="orange")
    _ax.scatter(X[y == 1, 0], X[y == 1, 1], c="#C44E52", edgecolors="white",
                alpha=0.85, label="grapefruit")
    _ax.set_xlabel("weight (g)")
    _ax.set_ylabel("diameter (cm)")
    _ax.set_title("120 fruits, 2 kinds")
    _ax.legend()
    _ax.grid(alpha=0.3)
    _fig.tight_layout()
    _fig
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 2️⃣ k-NN：讓鄰居投票

    最直覺的分類法：一顆新果實進來，找出跟它**最像的 k 顆**（距離最近的鄰居），
    讓它們投票，多數決。拉動下面的 k，看分界線怎麼變：

    - **k = 1**：訓練準確率一定是 100%（每顆果實最近的鄰居就是它自己）——
      但分界線歪七扭八，這叫**背答案**。
    - **k 變大**：分界線越來越平滑，個別怪果實的影響被稀釋掉。

    （重量的數字是幾百、直徑只有個位數——程式裡先把兩者拉到同一個尺度再量距離，
    不然投票會被重量一個人說了算。）
    """
    )
    return


@app.cell
def _(mo):
    k_slider = mo.ui.slider(start=1, stop=31, step=2, value=5,
                            label="k（找幾個鄰居投票）", show_value=True)
    k_slider
    return (k_slider,)


@app.cell
def _(KNeighborsClassifier, StandardScaler, X, k_slider, make_pipeline, np, plt, y):
    knn = make_pipeline(StandardScaler(),
                        KNeighborsClassifier(n_neighbors=k_slider.value))
    knn.fit(X, y)
    _acc = knn.score(X, y)
    _xx, _yy = np.meshgrid(
        np.linspace(X[:, 0].min() - 20, X[:, 0].max() + 20, 160),
        np.linspace(X[:, 1].min() - 0.8, X[:, 1].max() + 0.8, 160),
    )
    _zz = knn.predict(np.column_stack([_xx.ravel(), _yy.ravel()])).reshape(_xx.shape)
    _fig, _ax = plt.subplots(figsize=(7, 4.5))
    _ax.contourf(_xx, _yy, _zz, levels=[-0.5, 0.5, 1.5],
                 colors=["#F7E3CF", "#F3D4D5"])
    _ax.scatter(X[y == 0, 0], X[y == 0, 1], c="#DD8452", edgecolors="white",
                alpha=0.85, label="orange")
    _ax.scatter(X[y == 1, 0], X[y == 1, 1], c="#C44E52", edgecolors="white",
                alpha=0.85, label="grapefruit")
    _ax.set_xlabel("weight (g)")
    _ax.set_ylabel("diameter (cm)")
    _ax.set_title(f"k = {k_slider.value}  |  training accuracy = {_acc:.0%}")
    _ax.legend(loc="upper left")
    _fig.tight_layout()
    _fig
    return (knn,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 3️⃣ 考考它：一顆新果實

    自己捏一顆果實出來——調它的重量和直徑，看模型（用你上面選的 k）怎麼判。
    把它推進兩群中間的曖昧地帶，觀察投票什麼時候翻盤。
    """
    )
    return


@app.cell
def _(mo):
    w_slider = mo.ui.slider(start=80, stop=320, step=5, value=178,
                            label="新果實的重量 (g)", show_value=True)
    d_slider = mo.ui.slider(start=4.5, stop=12.5, step=0.1, value=8.2,
                            label="新果實的直徑 (cm)", show_value=True)
    mo.vstack([w_slider, d_slider])
    return d_slider, w_slider


@app.cell
def _(X, d_slider, k_slider, knn, np, plt, w_slider, y):
    _pt = np.array([[w_slider.value, d_slider.value]])
    _pred = knn.predict(_pt)[0]
    _votes = round(knn.predict_proba(_pt)[0][_pred] * k_slider.value)
    _name = "ORANGE" if _pred == 0 else "GRAPEFRUIT"
    _fig, _ax = plt.subplots(figsize=(7, 4.5))
    _ax.scatter(X[y == 0, 0], X[y == 0, 1], c="#DD8452", edgecolors="white",
                alpha=0.55, label="orange")
    _ax.scatter(X[y == 1, 0], X[y == 1, 1], c="#C44E52", edgecolors="white",
                alpha=0.55, label="grapefruit")
    _ax.scatter(_pt[0, 0], _pt[0, 1], marker="*", s=420,
                c="#DD8452" if _pred == 0 else "#C44E52",
                edgecolors="#1C2B33", linewidths=1.5, zorder=5, label="your fruit")
    _ax.set_xlabel("weight (g)")
    _ax.set_ylabel("diameter (cm)")
    _ax.set_title(f"model says: {_name}  ({_votes}/{k_slider.value} votes)")
    _ax.legend(loc="upper left")
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

    1. **LEVEL 1**：把 `my_k` 改成 1，確認訓練準確率真的變 100%。
    2. **LEVEL 2**：把 `my_k` 一路調大（21、41、61…），準確率怎麼變？
       想想 k = 120（全部果實都投票）時模型會變成什麼。
    3. **LEVEL 3**：回到 1️⃣ 把兩群的中心改得更近（例如橘子 160g、葡萄柚 200g），
       重疊變多之後，最好的 k 還是原來那個嗎？

    做完記得：**點左側教學頁的「下載 .py」把你的版本帶走**，
    在自己電腦用 `uvx marimo edit lesson.py` 就能繼續玩。
    """
    )
    return


@app.cell
def _(KNeighborsClassifier, StandardScaler, X, make_pipeline, y):
    # ===== 你的實驗區 =====
    # 改 my_k，或整段重寫！
    my_k = 5
    my_model = make_pipeline(StandardScaler(),
                             KNeighborsClassifier(n_neighbors=my_k))
    my_model.fit(X, y)
    print(f"k = {my_k:>3} 的訓練準確率：{my_model.score(X, y):.1%}")
    return


if __name__ == "__main__":
    app.run()
