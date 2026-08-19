import marimo

__generated_with = "0.23.16"
app = marimo.App(width="medium", app_title="分群：沒有答案也能找出結構（實驗場）")


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    # 🧪 分群：沒有答案也能找出結構（實驗場）

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
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler
    return KMeans, StandardScaler, np, plt


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 1️⃣ 沒有標籤的資料：90 位顧客

    一間咖啡店匯出了 90 位會員的**每月來店次數**和**平均單筆消費**。
    跟前兩課不一樣：這次**沒有任何答案**——沒人告訴我們誰是哪一種顧客。
    先用眼睛看：你覺得這裡面有幾種人？
    """
    )
    return


@app.cell
def _(np):
    rng = np.random.default_rng(11)
    _casual = np.column_stack([   # 偶爾路過的散客
        rng.normal(3, 1.1, 30),
        rng.normal(90, 18, 30),
    ])
    _regular = np.column_stack([  # 天天報到的常客
        rng.normal(12, 2.5, 30),
        rng.normal(110, 22, 30),
    ])
    _big = np.column_stack([      # 少來但一次買整袋豆子的豪客
        rng.normal(6, 1.6, 30),
        rng.normal(260, 35, 30),
    ])
    X = np.vstack([_casual, _regular, _big])
    X = X[rng.permutation(len(X))]  # 洗牌：資料裡沒有任何順序線索
    return (X,)


@app.cell
def _(X, plt):
    _fig, _ax = plt.subplots(figsize=(7, 4.5))
    _ax.scatter(X[:, 0], X[:, 1], c="#9AA7AE", alpha=0.85, edgecolors="white")
    _ax.set_xlabel("visits per month")
    _ax.set_ylabel("avg spend per visit (NT$)")
    _ax.set_title("90 customers, no labels")
    _ax.grid(alpha=0.3)
    _fig.tight_layout()
    _fig
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 2️⃣ K-means：猜中心、分邊、再修正

    K-means 只做三件事，重複到不再變動：**隨便放 k 個中心點 →
    每個點歸給最近的中心 → 中心移到自己那群的平均位置**。

    拉動 k 看結果（**X** 是每群的中心）：

    - **k = 3**：三群跟你眼睛看到的幾乎一樣——機器沒看過任何答案。
    - **k = 2**：兩種人被硬併成一群。
    - **k 太大**：真實的群被硬切碎——K-means 你要幾群它就給幾群，**不會回嘴**。

    （來店次數是個位數、消費是幾百塊——程式裡先把兩者拉到同一個尺度再量距離，
    不然分群會被消費金額一個人說了算。）
    """
    )
    return


@app.cell
def _(mo):
    k_slider = mo.ui.slider(start=2, stop=8, step=1, value=3,
                            label="k（要機器分成幾群）", show_value=True)
    k_slider
    return (k_slider,)


@app.cell
def _(KMeans, StandardScaler, X, k_slider, plt):
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    _km = KMeans(n_clusters=k_slider.value, n_init=10, random_state=0)
    _labels = _km.fit_predict(X_scaled)
    _centers = scaler.inverse_transform(_km.cluster_centers_)
    _colors = ["#4C72B0", "#DD8452", "#55A868", "#C44E52",
               "#8172B3", "#937860", "#DA8BC3", "#8C8C8C"]
    _fig, _ax = plt.subplots(figsize=(7, 4.5))
    for _i in range(k_slider.value):
        _ax.scatter(X[_labels == _i, 0], X[_labels == _i, 1],
                    c=_colors[_i], alpha=0.85, edgecolors="white",
                    label=f"cluster {_i + 1}")
    _ax.scatter(_centers[:, 0], _centers[:, 1], marker="X", s=220,
                c="#1C2B33", zorder=5, label="centers")
    _ax.set_xlabel("visits per month")
    _ax.set_ylabel("avg spend per visit (NT$)")
    _ax.set_title(f"k-means with k = {k_slider.value}")
    _ax.legend(loc="upper right", fontsize=9)
    _fig.tight_layout()
    _fig
    return (X_scaled,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 3️⃣ 手肘法：k 到底該選多少

    K-means 不會告訴你 k 選錯了，但有個線索：**群內距離總和**（inertia，
    每個點到自己中心的距離平方和）。k 越大它一定越小——
    重點是**變小的速度**：

    - k 從 1 → 2 → 3：大幅下降（每加一群都真的切中一種人）。
    - k = 3 之後：下降突然變平緩（再加的群只是在切碎真實的群）。

    折線像手肘一樣彎的位置，就是資料自己說出來的群數。
    """
    )
    return


@app.cell
def _(KMeans, X_scaled, np, plt):
    _ks = np.arange(1, 10)
    _inertias = [
        KMeans(n_clusters=int(_k), n_init=10, random_state=0).fit(X_scaled).inertia_
        for _k in _ks
    ]
    _fig, _ax = plt.subplots(figsize=(7, 4.5))
    _ax.plot(_ks, _inertias, "o-", c="#4C72B0")
    _ax.axvline(3, color="#C44E52", linestyle="--", alpha=0.7)
    _ax.annotate("the elbow", (3, _inertias[2]),
                 xytext=(4.4, _inertias[1]), color="#C44E52",
                 arrowprops={"arrowstyle": "->", "color": "#C44E52"})
    _ax.set_xlabel("k (number of clusters)")
    _ax.set_ylabel("inertia (within-cluster distance)")
    _ax.set_title("the elbow method")
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

    1. **LEVEL 1**：把 `my_k` 改成 6，印出每群人數——被切碎的是哪一群？
    2. **LEVEL 2**：回到 1️⃣ 把豪客群改成只有 5 個人（`rng.normal(260, 35, 5)`，
       記得洗牌那行不用動），手肘還看得出 3 嗎？小群很容易被 K-means 忽略。
    3. **LEVEL 3**：回到 1️⃣ 加入第四群「你設計的顧客」，先猜手肘會移到哪，
       再跑 3️⃣ 驗證。

    做完記得：**點左側教學頁的「下載 .py」把你的版本帶走**，
    在自己電腦用 `uvx marimo edit lesson.py` 就能繼續玩。
    """
    )
    return


@app.cell
def _(KMeans, X_scaled, np):
    # ===== 你的實驗區 =====
    # 改 my_k，或整段重寫！
    my_k = 3
    my_labels = KMeans(n_clusters=my_k, n_init=10, random_state=0).fit_predict(X_scaled)
    for g, cnt in zip(*np.unique(my_labels, return_counts=True), strict=True):
        print(f"cluster {g + 1}：{cnt} 人")
    return


if __name__ == "__main__":
    app.run()
