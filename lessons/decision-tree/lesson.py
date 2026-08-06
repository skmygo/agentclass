import marimo

__generated_with = "0.23.16"
app = marimo.App(width="medium", app_title="決策樹互動實驗室")


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    # 🌳 決策樹互動實驗室

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
    import matplotlib.pyplot as plt
    import numpy as np
    import pandas as pd
    from sklearn.datasets import load_iris
    from sklearn.metrics import accuracy_score
    from sklearn.model_selection import train_test_split
    from sklearn.tree import DecisionTreeClassifier, plot_tree
    return (
        DecisionTreeClassifier,
        accuracy_score,
        load_iris,
        np,
        plot_tree,
        plt,
        train_test_split,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 1️⃣ 認識資料：鳶尾花（Iris）

    150 朵鳶尾花，每朵量了 4 個特徵（花萼/花瓣的長與寬，單位 cm），
    分屬 3 個品種（setosa / versicolor / virginica）。
    我們的任務：**用 4 個數字，猜出是哪個品種**。
    """
    )
    return


@app.cell
def _(load_iris):
    iris = load_iris(as_frame=True)
    df = iris.frame.copy()
    feature_names = list(iris.feature_names)
    target_names = list(iris.target_names)
    df["species"] = df["target"].map(dict(enumerate(target_names)))
    df
    return df, feature_names, target_names


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 2️⃣ 用兩個特徵看資料

    挑兩個特徵畫散佈圖。試著找出：**哪一組特徵最能把三種顏色分開？**
    （提示：花瓣 petal 比花萼 sepal 有用得多——這正是決策樹自己也會發現的事。）
    """
    )
    return


@app.cell
def _(feature_names, mo):
    feat_x = mo.ui.dropdown(
        options=feature_names, value=feature_names[2], label="X 軸特徵"
    )
    feat_y = mo.ui.dropdown(
        options=feature_names, value=feature_names[3], label="Y 軸特徵"
    )
    mo.hstack([feat_x, feat_y], justify="start", gap=2)
    return feat_x, feat_y


@app.cell
def _(df, feat_x, feat_y, plt, target_names):
    _colors = ["#4C72B0", "#DD8452", "#55A868"]
    _fig, _ax = plt.subplots(figsize=(7, 5))
    for _i, _name in enumerate(target_names):
        _sub = df[df["species"] == _name]
        _ax.scatter(
            _sub[feat_x.value], _sub[feat_y.value],
            c=_colors[_i], label=_name, alpha=0.8, edgecolors="white", s=55,
        )
    _ax.set_xlabel(feat_x.value)
    _ax.set_ylabel(feat_y.value)
    _ax.legend(title="species")
    _ax.set_title("Iris scatter")
    _fig.tight_layout()
    _fig
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 3️⃣ 一刀切下去：Gini 不純度

    決策樹每個節點都在問同一個問題：「**在哪個特徵的哪個值切一刀，能把類別分得最乾淨？**」
    「乾淨程度」用 **Gini 不純度**衡量：$\text{Gini} = 1 - \sum_k p_k^2$，
    全是同一類 = 0（最純），三類均勻混合 ≈ 0.667（最不純）。

    下面親手當一次決策樹：挑一個特徵、拖動閾值，看你這一刀切完的**加權 Gini** 是多少。
    試著找到讓加權 Gini 最小的位置——那就是決策樹會選的切點。
    """
    )
    return


@app.cell
def _(feature_names, mo):
    gini_feature = mo.ui.dropdown(
        options=feature_names, value=feature_names[2], label="切分特徵"
    )
    return (gini_feature,)


@app.cell
def _(df, gini_feature, mo):
    _vals = df[gini_feature.value]
    gini_threshold = mo.ui.slider(
        start=float(_vals.min()), stop=float(_vals.max()), step=0.05,
        value=round(float(_vals.median()), 2), label="切分閾值",
        show_value=True, full_width=True,
    )
    mo.vstack([gini_feature, gini_threshold])
    return (gini_threshold,)


@app.cell
def _(df, gini_feature, gini_threshold, mo, np):
    def gini_impurity(labels):
        """Gini = 1 - Σ p_k²"""
        if len(labels) == 0:
            return 0.0
        _, counts = np.unique(labels, return_counts=True)
        p = counts / counts.sum()
        return float(1 - (p**2).sum())

    _feat, _t = gini_feature.value, gini_threshold.value
    _left = df[df[_feat] <= _t]["target"]
    _right = df[df[_feat] > _t]["target"]
    _gl, _gr = gini_impurity(_left), gini_impurity(_right)
    _n = len(df)
    gini_weighted = len(_left) / _n * _gl + len(_right) / _n * _gr

    mo.md(
        f"""
    | | 左組（≤ {_t:.2f}） | 右組（> {_t:.2f}） |
    |---|---|---|
    | 樣本數 | {len(_left)} | {len(_right)} |
    | Gini | {_gl:.3f} | {_gr:.3f} |

    **加權 Gini = {gini_weighted:.3f}** &nbsp;（切分前整組的 Gini = {gini_impurity(df["target"]):.3f}）
    """
    )
    return (gini_impurity,)


@app.cell
def _(df, gini_feature, gini_threshold, plt, target_names):
    _colors = ["#4C72B0", "#DD8452", "#55A868"]
    _fig, _ax = plt.subplots(figsize=(7, 3.2))
    for _i, _name in enumerate(target_names):
        _ax.hist(
            df[df["species"] == _name][gini_feature.value],
            bins=24, alpha=0.65, color=_colors[_i], label=_name,
        )
    _ax.axvline(gini_threshold.value, color="#C44E52", lw=2.5, ls="--",
                label=f"threshold = {gini_threshold.value:.2f}")
    _ax.set_xlabel(gini_feature.value)
    _ax.set_ylabel("count")
    _ax.legend(fontsize=8)
    _fig.tight_layout()
    _fig
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 4️⃣ 訓練一棵真正的決策樹

    手動找切點太累了——`DecisionTreeClassifier` 會在**每個節點**自動掃過所有特徵、
    所有切點，挑加權 Gini 最小的那一刀，然後對切出的兩半**遞迴**做同樣的事。

    兩個最重要的煞車（超參數）交給你：

    - **max_depth**：樹最多長幾層
    - **min_samples_leaf**：每片葉子至少要有幾個樣本

    先把 max_depth 拉到 1 看「只切一刀」的樹長什麼樣，再慢慢加深。
    """
    )
    return


@app.cell
def _(mo):
    max_depth = mo.ui.slider(
        start=1, stop=8, step=1, value=3, label="max_depth（樹深）",
        show_value=True,
    )
    min_samples_leaf = mo.ui.slider(
        start=1, stop=20, step=1, value=1,
        label="min_samples_leaf（葉最少樣本）", show_value=True,
    )
    mo.hstack([max_depth, min_samples_leaf], justify="start", gap=2)
    return max_depth, min_samples_leaf


@app.cell
def _(
    DecisionTreeClassifier,
    accuracy_score,
    df,
    feature_names,
    max_depth,
    min_samples_leaf,
    train_test_split,
):
    X_train, X_test, y_train, y_test = train_test_split(
        df[feature_names], df["target"],
        test_size=0.3, random_state=42, stratify=df["target"],
    )
    clf = DecisionTreeClassifier(
        max_depth=max_depth.value,
        min_samples_leaf=min_samples_leaf.value,
        random_state=42,
    ).fit(X_train, y_train)
    train_acc = accuracy_score(y_train, clf.predict(X_train))
    test_acc = accuracy_score(y_test, clf.predict(X_test))
    return X_test, X_train, clf, test_acc, train_acc, y_test, y_train


@app.cell
def _(mo, test_acc, train_acc):
    mo.hstack(
        [
            mo.stat(value=f"{train_acc:.1%}", label="訓練集準確率", bordered=True),
            mo.stat(value=f"{test_acc:.1%}", label="測試集準確率", bordered=True),
            mo.stat(value=f"{train_acc - test_acc:+.1%}", label="差距（過擬合訊號）",
                    bordered=True),
        ],
        justify="start", gap=1,
    )
    return


@app.cell
def _(clf, feature_names, plot_tree, plt, target_names):
    _fig, _ax = plt.subplots(figsize=(12, 6.5))
    plot_tree(
        clf, feature_names=feature_names, class_names=target_names,
        filled=True, rounded=True, ax=_ax, fontsize=8,
    )
    _ax.set_title("The trained decision tree")
    _fig.tight_layout()
    _fig
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    讀樹的方法：每個節點顯示「切分條件 / gini / 樣本數 / 各類數量」。
    注意看**根節點選了哪個特徵**——跟你在第 2️⃣ 節散佈圖上的觀察一致嗎？

    ## 5️⃣ 決策邊界：樹是怎麼「看」平面的

    用你在第 2️⃣ 節選的兩個特徵（回上面換選項，這裡會跟著變）訓練一棵同參數的樹，
    把整個平面的預測結果塗色。決策樹的邊界永遠是**軸對齊的矩形切割**——
    因為每一刀都只問「某特徵 ≤ 某值？」。把 max_depth 調大，看格子怎麼越切越碎。
    """
    )
    return


@app.cell
def _(
    DecisionTreeClassifier,
    df,
    feat_x,
    feat_y,
    max_depth,
    min_samples_leaf,
    np,
    plt,
    target_names,
):
    _colors = ["#4C72B0", "#DD8452", "#55A868"]
    _fx, _fy = feat_x.value, feat_y.value
    _X2 = df[[_fx, _fy]].to_numpy()
    _y = df["target"].to_numpy()
    _clf2d = DecisionTreeClassifier(
        max_depth=max_depth.value,
        min_samples_leaf=min_samples_leaf.value,
        random_state=42,
    ).fit(_X2, _y)

    _x0 = np.linspace(_X2[:, 0].min() - 0.3, _X2[:, 0].max() + 0.3, 300)
    _x1 = np.linspace(_X2[:, 1].min() - 0.3, _X2[:, 1].max() + 0.3, 300)
    _xx, _yy = np.meshgrid(_x0, _x1)
    _zz = _clf2d.predict(np.c_[_xx.ravel(), _yy.ravel()]).reshape(_xx.shape)

    _fig, _ax = plt.subplots(figsize=(7, 5))
    _ax.contourf(_xx, _yy, _zz, alpha=0.25, levels=2, colors=_colors)
    for _i, _name in enumerate(target_names):
        _m = _y == _i
        _ax.scatter(_X2[_m, 0], _X2[_m, 1], c=_colors[_i], label=_name,
                    edgecolors="white", s=45)
    _ax.set_xlabel(_fx)
    _ax.set_ylabel(_fy)
    _ax.set_title(f"Decision boundary (max_depth={max_depth.value})")
    _ax.legend()
    _fig.tight_layout()
    _fig
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 6️⃣ 過擬合：樹越深越好嗎？

    把每種深度都訓練一次，比較訓練集與測試集的準確率。
    你會看到經典的分岔：**訓練準確率一路升，測試準確率先升後平（甚至掉頭）**——
    樹太深時，它背下了訓練資料的雜訊，而不是學到規律。
    """
    )
    return


@app.cell
def _(
    DecisionTreeClassifier,
    X_test,
    X_train,
    accuracy_score,
    np,
    plt,
    y_test,
    y_train,
):
    _depths = np.arange(1, 11)
    _tr, _te = [], []
    for _d in _depths:
        _m = DecisionTreeClassifier(max_depth=int(_d), random_state=42).fit(
            X_train, y_train
        )
        _tr.append(accuracy_score(y_train, _m.predict(X_train)))
        _te.append(accuracy_score(y_test, _m.predict(X_test)))

    _fig, _ax = plt.subplots(figsize=(7, 4))
    _ax.plot(_depths, _tr, "o-", color="#4C72B0", label="train accuracy")
    _ax.plot(_depths, _te, "s-", color="#C44E52", label="test accuracy")
    _ax.set_xlabel("max_depth")
    _ax.set_ylabel("accuracy")
    _ax.set_xticks(_depths)
    _ax.set_ylim(0.6, 1.02)
    _ax.grid(alpha=0.3)
    _ax.legend()
    _ax.set_title("Overfitting: train vs test accuracy")
    _fig.tight_layout()
    _fig
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 7️⃣ 練習：換你動手

    下面這格是你的實驗區，改完按 ▶ 重跑。建議挑戰（由易到難）：

    1. 把 `criterion` 改成 `"entropy"`（資訊增益），準確率有變嗎？樹長得一樣嗎？
    2. 只用 **sepal** 的兩個特徵訓練，測試準確率掉到多少？（呼應第 2️⃣ 節的觀察）
    3. 把 `load_wine()` 換進來（13 個特徵、3 種酒），這棵樹還好用嗎？

    做完記得：**點右上角下載按鈕（或左側教學頁的「下載 .py」）把你的版本帶走**，
    在自己電腦用 `uvx marimo edit lesson.py` 就能繼續玩。
    """
    )
    return


@app.cell
def _(DecisionTreeClassifier, accuracy_score, df, feature_names, train_test_split):
    # ===== 你的實驗區 =====
    # 試著修改下面的參數，或整段重寫！
    my_features = feature_names            # 練習 2：改成只留 sepal 的兩欄
    my_criterion = "gini"                  # 練習 1：改成 "entropy"

    _Xtr, _Xte, _ytr, _yte = train_test_split(
        df[my_features], df["target"],
        test_size=0.3, random_state=42, stratify=df["target"],
    )
    my_tree = DecisionTreeClassifier(
        criterion=my_criterion, max_depth=3, random_state=42
    ).fit(_Xtr, _ytr)

    print(f"特徵：{my_features}")
    print(f"criterion={my_criterion}")
    print(f"測試集準確率：{accuracy_score(_yte, my_tree.predict(_Xte)):.1%}")
    return


if __name__ == "__main__":
    app.run()
