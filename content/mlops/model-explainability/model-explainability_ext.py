# 模型可解釋性：上線前要能說出「為什麼」（SHAP、permutation importance、內建重要度）
# 不需要 GPU——molab 免費 CPU 環境即可全程執行（全部跑在 notebook 自己的機器上，不連任何外部服務）。
# /// script
# requires-python = ">=3.12,<3.14"
# dependencies = [
#     "marimo",
#     "shap>=0.52",
#     "numba>=0.61",
#     "scikit-learn",
#     "pandas",
#     "numpy",
#     "matplotlib",
#     "mlflow>=3.0",
# ]
# ///
# 為什麼要釘 numba：shap 依賴 numba，而通用解析（要同時滿足所有 Python 版本）不釘的話會
# 退回 numba 0.53 —— 那個版本沒有新 Python 的輪子，會現場編譯然後失敗。
# shap 0.52 起 shap_values 回傳三維陣列 (n, 特徵, 類別)；更早的版本回傳 list，本課的
# [:, :, 1] 寫法就對不上，所以下限釘在 0.52。
import marimo

__generated_with = "0.23.16"
app = marimo.App(width="medium", app_title="模型可解釋性：上線前要能說出為什麼")


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    # ⚡ 模型可解釋性：上線前要能說出「為什麼」

    上一課你替模型寫了測試，讓一個爛模型在紅字裡現形。這一課處理的是**測試也答不出來的問題**。

    模型評審會上，AUC 0.9684 投影在牆上，然後：

    - 業務主管問：「它憑什麼說這位客戶會流失？我要打電話過去，總得說個理由。」
    - 法遵同事問：「有沒有用到不該用的欄位？我們簽的合約寫了不得以地區作為拒絕依據。」
    - 你自己心裡也有一個問題：「上一版跟這一版，模型的想法有沒有變？」

    **AUC 一個都答不出來。** 它是一個總分，總分不會告訴你分數是怎麼來的。

    可解釋性要回答的是兩個層次的問題：

    | 層次 | 問題長什麼樣 | 誰在問 |
    |---|---|---|
    | **全域（global）** | 整體來說，哪些特徵在決定這個模型的輸出？ | 模型審核、法遵、監控 |
    | **局部（local）** | **這一筆**為什麼被判成 0.986？ | 客戶、客服、申訴處理 |

    而 SHAP 用一句白話講完就是：

    > **把「這一筆的預測」跟「平均」之間的差距，公平地分給每一個特徵。**

    「公平」不是形容詞，是有數學定義的（合作賽局理論的 Shapley value）。實務上你只要記住一個檢查：
    **基準 ＋ 所有特徵的貢獻 ＝ 這一筆的預測值**，一分不多一分不少。這一課會親手驗這條等式。

    這份 notebook 會做完這些事：

    1. 資料與 champion 模型（跟這系列前面每一課同一份，數字對得上）
    2. 三種全域重要度：RF 內建、permutation、mean|SHAP| —— 為什麼排名會不一樣
    3. SHAP 值是什麼：`TreeExplainer`、`expected_value`、加總＝預測
    4. 局部解釋：waterfall、蜂群圖、依賴圖
    5. 上線前審核：把解釋報告掛成 MLflow artifact，跟 champion 一起版本化
    6. 監控：什麼時候重要度會變、什麼時候不會（跟第 7 課的漂移對照）
    7. 合規：禁用欄位檢查函式（以及它為什麼會被繞過）
    8. 對客戶說明：把 waterfall 變成三句中文
    9. 限制與其他模型：`KernelExplainer`、`LinearExplainer`、相關特徵分攤
    10. 互動：挑一位客戶，看他的 waterfall 與三句解釋
    11. 🏆 三級挑戰（附折疊解答）＋ 常見錯誤原文速查

    **不需要 GPU**，molab 免費 CPU 環境從第一格往下全部執行即可（首次安裝套件約 1–2 分鐘）。
    所有計算加起來不到半分鐘，最慢的一格是第 9 節的 `KernelExplainer`（5–6 秒，那正是它的教學點）。

    > 資料是模擬的、亂數種子固定，所以**你跑出來的數字會跟這裡一模一樣**；
    > 只有秒數會跟著你的機器走。
    """
    )
    return


@app.cell
def _():
    import html
    import logging
    import shutil
    import tempfile
    import time
    import warnings
    from pathlib import Path

    import marimo as mo
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import mlflow
    import numpy as np
    import pandas as pd
    import shap
    from sklearn.datasets import make_classification
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.inspection import permutation_importance
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import roc_auc_score
    from sklearn.model_selection import train_test_split

    # SHAP 與 MLflow 的提示訊息會蓋掉教學輸出
    logging.getLogger("mlflow").setLevel(logging.ERROR)
    logging.getLogger("shap").setLevel(logging.ERROR)
    warnings.filterwarnings("ignore")

    WORK = Path(tempfile.gettempdir()) / "mlops-explainability"
    shutil.rmtree(WORK, ignore_errors=True)
    WORK.mkdir(parents=True, exist_ok=True)

    print(f"shap {shap.__version__} · mlflow {mlflow.__version__} · 工作目錄 {WORK}")
    return (
        LogisticRegression,
        Path,
        RandomForestClassifier,
        WORK,
        html,
        make_classification,
        mlflow,
        mo,
        np,
        pd,
        permutation_importance,
        plt,
        roc_auc_score,
        shap,
        time,
        train_test_split,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 1️⃣ 資料與 champion 模型

    跟這系列前面每一課同一份資料：2000 位客戶、12 個特徵 `f0`–`f11`、流失率 50%，
    切成 train 1500 / test 500。模型是已經在 Registry 裡當 champion 的那一版
    ——`RandomForestClassifier(n_estimators=100, max_depth=8)`，測試集 AUC **0.9684**。

    **為什麼要用 test 集來解釋，而不是 train 集？**
    因為你要解釋的是「模型面對**沒看過的客戶**時怎麼想」。拿訓練資料算重要度，會混進模型
    背下來的東西——第 2 節的 permutation importance 會親眼看到這個差別。

    > 特徵叫 `f0`…`f11` 是刻意的：真實專案裡它們會叫「近 90 天登入次數」「合約剩餘月數」。
    > 名字換掉不影響任何一行程式，但會讓「解釋」這件事突然變得有意義——第 8 節會示範。
    """
    )
    return


@app.cell
def _(
    RandomForestClassifier,
    make_classification,
    pd,
    roc_auc_score,
    train_test_split,
):
    X_all, y_all = make_classification(
        n_samples=2000, n_features=12, n_informative=6, random_state=0
    )
    FEATS = [f"f{i}" for i in range(12)]
    X_df = pd.DataFrame(X_all, columns=FEATS)
    Xtr, Xte, ytr, yte = train_test_split(X_df, y_all, test_size=0.25, random_state=0)

    rf = RandomForestClassifier(n_estimators=100, max_depth=8, random_state=0).fit(Xtr, ytr)
    proba_te = rf.predict_proba(Xte)[:, 1]
    AUC = roc_auc_score(yte, proba_te)

    print(f"train {Xtr.shape} / test {Xte.shape} · 流失率 {y_all.mean():.1%}")
    print(f"champion RandomForest(depth=8) 測試集 AUC = {AUC:.4f}")
    print(f"測試集預測機率：平均 {proba_te.mean():.4f}、最低 {proba_te.min():.4f}、最高 {proba_te.max():.4f}")
    return AUC, FEATS, Xte, Xtr, proba_te, rf, yte, ytr


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 2️⃣ 三種全域重要度：同一個模型，三種答案

    「哪些特徵最重要」聽起來是一個問題，其實是三個。三種算法問的問題不一樣，
    所以答案不一樣是**正常的**，不是誰算錯了。

    ### ① RF 內建 `feature_importances_`：這個特徵讓樹分得多乾淨

    隨機森林建樹時每次分裂都會挑一個特徵，記下「這一刀讓不純度（Gini）降低了多少」。
    把每個特徵在所有樹上的降幅加總、再除以總和，就是內建重要度——所以**它加起來一定等於 1**，
    是一份「佔比」，講不出「重要多少」的絕對量。

    它有兩個著名的毛病：

    - **偏愛切得動的特徵**：連續值與高基數類別（客戶編號、郵遞區號）可以切出很多刀，
      每刀都貢獻一點降幅，加起來就不低了——即使它跟答案完全無關。這一節會用一欄純亂數親眼看。
    - **只看訓練過程**：它是建樹時記下來的帳，跟「模型在新資料上準不準」沒有直接關係。

    ### ② `permutation_importance`：打亂這一欄，分數掉多少

    把某一欄的值在列之間隨機洗牌（破壞它與答案的關係），其他欄不動，重算一次分數，
    看掉了多少。掉越多＝越重要。這種算法有兩個關鍵性質：

    - **跟指標綁定**：你用 `scoring="roc_auc"` 得到的是「對排序能力的貢獻」，
      用 `scoring="accuracy"` 得到的是「對分類正確率的貢獻」——排名可能不同。
    - **它衡量的是「有沒有用」，不是「有沒有被用到」**。這句話是本節的重點，第 ③ 種會對照。

    ### ③ mean|SHAP|：這個特徵平均把預測推動多遠

    把每一筆的 SHAP 值取絕對值再平均。單位是**預測機率**——`f2` 的 0.2137 就是
    「平均而言，f2 這一欄把這位客戶的流失機率推動了 0.21」。三種裡面只有它有這麼直觀的單位。

    它衡量的是**模型怎麼想**，跟答案對不對無關——就算模型完全學歪了，SHAP 照樣忠實地告訴你它在想什麼。
    """
    )
    return


@app.cell
def _(FEATS, pd, plt, rf):
    imp_builtin = pd.Series(rf.feature_importances_, index=FEATS).sort_values()

    plt.close("all")
    _fig, _ax = plt.subplots(figsize=(6.2, 3.2))
    _ax.barh(imp_builtin.index, imp_builtin.values, color="#4C72B0")
    _ax.set_title("(1) RF built-in feature_importances_  (sums to 1.0)")
    _ax.set_xlabel("share of total impurity decrease")
    _fig.tight_layout()
    _fig
    return (imp_builtin,)


@app.cell
def _(FEATS, Xte, imp_builtin, mo, pd, permutation_importance, rf, time, yte):
    _t0 = time.time()
    perm_res = permutation_importance(
        rf, Xte, yte, n_repeats=5, random_state=0, scoring="roc_auc"
    )
    perm_secs = time.time() - _t0
    imp_perm = pd.Series(perm_res.importances_mean, index=FEATS)
    imp_perm_std = pd.Series(perm_res.importances_std, index=FEATS)

    mo.md(
        f"""
    `permutation_importance(scoring="roc_auc", n_repeats=5)` 花了 **{perm_secs:.1f} 秒**
    （5 次洗牌 × 12 欄 = 60 次重新預測）。前三名：
    **f2 {imp_perm["f2"]:.4f}**（打亂它 AUC 掉 0.24）、
    **f3 {imp_perm["f3"]:.4f}**、**f9 {imp_perm["f9"]:.4f}**；
    重複 5 次的標準差分別是 {imp_perm_std["f2"]:.4f}／{imp_perm_std["f3"]:.4f}／{imp_perm_std["f9"]:.4f}
    ——**排名靠後的幾欄，重要度比它自己的標準差還小，那就別去解讀順序**。

    對照內建重要度：f2 是 {imp_builtin["f2"]:.4f}（佔比），單位完全不同，只有排名可以比。
    """
    )
    return imp_perm, imp_perm_std, perm_secs


@app.cell
def _(imp_perm, plt):
    _s = imp_perm.sort_values()
    plt.close("all")
    _fig2, _ax2 = plt.subplots(figsize=(6.2, 3.2))
    _ax2.barh(_s.index, _s.values, color="#DD8452")
    _ax2.axvline(0, color="#999", lw=0.8)
    _ax2.set_title("(2) permutation importance  (drop in test ROC-AUC)")
    _ax2.set_xlabel("AUC lost when this column is shuffled")
    _fig2.tight_layout()
    _fig2
    return


@app.cell
def _(FEATS, Xte, mo, np, pd, shap, rf, time):
    _t0 = time.time()
    tree_explainer = shap.TreeExplainer(rf)
    shap_raw = tree_explainer.shap_values(Xte)  # (500, 12, 2)
    shap_secs = time.time() - _t0

    shap_vals = shap_raw[:, :, 1]  # ← 只要「流失（類別 1）」那一面
    BASE = float(np.atleast_1d(tree_explainer.expected_value)[-1])
    imp_shap = pd.Series(np.abs(shap_vals).mean(0), index=FEATS)

    mo.md(
        f"""
    `TreeExplainer(rf).shap_values(Xte)` 算完 500 位客戶只花 **{shap_secs:.2f} 秒**
    （每列約 {shap_secs / len(Xte) * 1000:.1f} 毫秒）——樹模型有專屬的多項式時間演算法，
    這就是 TreeSHAP 值得單獨存在的理由（第 9 節會看通用版有多慢）。

    回傳的形狀是 **{shap_raw.shape}**：`(列數, 特徵數, 類別數)`。二元分類的兩面是完全對稱的
    （`[:, :, 0] == -[:, :, 1]`：{np.allclose(shap_raw[:, :, 0], -shap_raw[:, :, 1])}），
    我們要的是「往流失推」那一面，所以 **`[:, :, 1]`**。
    **忘了取這一刀是新手最常見的錯**，而且它多半不會噴錯——最後一節有實測。

    `expected_value` = {np.round(tree_explainer.expected_value, 5).tolist()}，
    類別 1 的基準是 **{BASE:.5f}**：這就是「什麼都不知道時的預測」，
    也就是訓練資料的流失比例。所有解釋都是從這個數字出發的。
    """
    )
    return BASE, imp_shap, shap_raw, shap_secs, shap_vals, tree_explainer


@app.cell
def _(imp_shap, plt):
    _s = imp_shap.sort_values()
    plt.close("all")
    _fig3, _ax3 = plt.subplots(figsize=(6.2, 3.2))
    _ax3.barh(_s.index, _s.values, color="#55A868")
    _ax3.set_title("(3) mean |SHAP|  (average push on churn probability)")
    _ax3.set_xlabel("probability units")
    _fig3.tight_layout()
    _fig3
    return


@app.cell
def _(FEATS, imp_builtin, imp_perm, imp_shap, mo, pd):
    rank_tbl = pd.DataFrame(
        {
            "builtin": imp_builtin.reindex(FEATS).rank(ascending=False).astype(int),
            "perm": imp_perm.reindex(FEATS).rank(ascending=False).astype(int),
            "shap": imp_shap.reindex(FEATS).rank(ascending=False).astype(int),
        }
    ).sort_values("shap")

    _rows = "\n".join(
        f"    | {f} | {imp_builtin[f]:.4f} (#{rank_tbl.loc[f, 'builtin']}) "
        f"| {imp_perm[f]:+.4f} (#{rank_tbl.loc[f, 'perm']}) "
        f"| {imp_shap[f]:.4f} (#{rank_tbl.loc[f, 'shap']}) |"
        for f in rank_tbl.index
    )

    mo.md(
        f"""
    ### 三種算法的排名對照

    | 特徵 | 內建（佔比） | permutation（AUC 掉多少） | mean&#124;SHAP&#124;（機率） |
    |---|---|---|---|
{_rows}

    **前三名 f2 → f3 → f9 三種算法完全一致**——這是好消息：三個問法不同的方法都指向同一組主角，
    你可以放心跟業務說「這個模型主要靠這三件事在判斷」。

    **第 4 名開始就分歧了**，而且每一處分歧都有原因：

    - 第 4 名：內建與 SHAP 都選 f4，permutation 選 f1。permutation 問的是「對 AUC 有沒有用」，
      f4 被模型用得多（SHAP 說有）但打亂之後 AUC 只掉 {imp_perm["f4"]:.4f}——**用得多不等於有用**。
    - f11：內建排 #{rank_tbl.loc["f11", "builtin"]}、SHAP 排 #{rank_tbl.loc["f11", "shap"]}。
      內建重要度偏愛「切得動」的特徵，下一格會用一欄純亂數把這個偏誤放到最大。
    - 尾巴那幾欄（f5、f7、f8、f10）permutation 的值是負的或接近 0：
      **負值不代表「有害」，只代表「打亂它反而剛好好一點點」，也就是雜訊**。
      配上前面看到的標準差，這幾名的順序本來就不該解讀。

    **所以該用哪一種？** 三個都用，然後看它們吵架的地方——
    分歧的位置就是你該去理解模型的地方。硬要選一個當預設，選 SHAP：
    它同時給得出全域與局部，而且單位是預測機率，講得出「推動多少」。
    """
    )
    return (rank_tbl,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ### 內建重要度的偏誤：加一欄純亂數看看

    「偏愛高基數／連續特徵」聽起來很抽象。做一次就懂了：在資料裡加一欄
    `customer_id`（**完全隨機的整數，跟流失一點關係都沒有**），重訓，再問三種算法它有多重要。
    """
    )
    return


@app.cell
def _(
    FEATS,
    RandomForestClassifier,
    Xte,
    Xtr,
    imp_builtin,
    mo,
    np,
    pd,
    permutation_importance,
    roc_auc_score,
    shap,
    yte,
    ytr,
):
    _rng = np.random.default_rng(1)
    Xtr_id = Xtr.copy()
    Xte_id = Xte.copy()
    Xtr_id["customer_id"] = _rng.permutation(len(Xtr_id)).astype(float)
    Xte_id["customer_id"] = _rng.permutation(len(Xte_id)).astype(float)

    rf_id = RandomForestClassifier(n_estimators=100, max_depth=8, random_state=0).fit(Xtr_id, ytr)
    auc_id = roc_auc_score(yte, rf_id.predict_proba(Xte_id)[:, 1])

    b_id = pd.Series(rf_id.feature_importances_, index=Xtr_id.columns)
    p_id = pd.Series(
        permutation_importance(
            rf_id, Xte_id, yte, n_repeats=5, random_state=0, scoring="roc_auc"
        ).importances_mean,
        index=Xte_id.columns,
    )
    s_id = pd.Series(
        np.abs(shap.TreeExplainer(rf_id).shap_values(Xte_id)[:, :, 1]).mean(0),
        index=Xte_id.columns,
    )

    mo.md(
        f"""
    加了一欄純亂數之後，模型 AUC 是 {auc_id:.4f}（原本 0.9684，幾乎沒變——它確實沒學到東西）。
    但三種算法對這欄亂數的評價差很多：

    | 算法 | `customer_id` 的分數 | 排名（共 13 欄） |
    |---|---|---|
    | RF 內建 | **{b_id["customer_id"]:.4f}** | 第 {int(b_id.rank(ascending=False)["customer_id"])} 名 |
    | permutation (AUC) | {p_id["customer_id"]:+.4f} | 第 {int(p_id.rank(ascending=False)["customer_id"])} 名 |
    | mean&#124;SHAP&#124; | {s_id["customer_id"]:.4f} | 第 {int(s_id.rank(ascending=False)["customer_id"])} 名 |

    內建重要度給了這欄亂數 **{b_id["customer_id"]:.4f}**，**排在兩個真特徵之上**
    （f10 {b_id["f10"]:.4f}、f5 {b_id["f5"]:.4f}）。原因就是前面說的：連續的流水號可以切出無限多刀，
    每一刀都湊巧讓某個小分支乾淨一點點，加總起來就不是 0 了。

    permutation 給它 {p_id["customer_id"]:+.4f}，**基本上是 0**——打亂它 AUC 一動也不動，
    因為它對「準不準」毫無貢獻。SHAP 給 {s_id["customer_id"]:.4f}，也很小但**不是 0**，
    而這是誠實的：模型確實在用它（樹裡真的有那幾刀），SHAP 就照實說。

    **一句話記住三者的分工**：內建說「建樹時切了幾刀」、permutation 說「有沒有用」、
    SHAP 說「模型實際上怎麼用」。看到「客戶編號很重要」這種結果，
    先別急著寫進報告——換一種算法問一次。
    """
    )
    return Xte_id, Xtr_id, auc_id, b_id, p_id, rf_id, s_id


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 3️⃣ SHAP 值到底是什麼：加總必須對得起來

    前面一直在用「貢獻」這個詞，現在把它變成可以驗算的東西。

    對任何一筆資料，SHAP 保證這條等式成立（這叫 **local accuracy**，是 Shapley value 的定義之一）：

    ```text
    expected_value  +  sum(這一筆 12 個特徵的 SHAP 值)  =  模型對這一筆的預測
        基準                     各自的功過                        最後的機率
    ```

    這條等式讓 SHAP 跟「感覺型」的解釋徹底分開：它不是「大概是這幾個原因」，
    而是**把 0.9860 減 0.4882 這 0.4978 的差距，一分不剩地分完**。下一格拿測試集第 1 位客戶驗算。
    """
    )
    return


@app.cell
def _(BASE, FEATS, Xte, html, mo, np, pd, proba_te, shap_vals):
    _pos = 0
    row0 = pd.Series(shap_vals[_pos], index=FEATS).sort_values(key=abs, ascending=False)
    _lines = [f"客戶 #{Xte.index[_pos]}（測試集第 1 位）", ""]
    _acc = BASE
    _lines.append(f"  基準 expected_value          = {BASE:.5f}   （什麼都不知道時的猜測）")
    for _f in row0.index:
        _acc += row0[_f]
        _lines.append(
            f"  {_f:<3} = {Xte.iloc[_pos][_f]:+7.3f}  →  SHAP {row0[_f]:+.4f}   累積 {_acc:.5f}"
        )
    _lines += [
        "",
        f"  加總結果                     = {_acc:.5f}",
        f"  模型 predict_proba 的答案     = {proba_te[_pos]:.5f}",
        f"  兩者差距                     = {abs(_acc - proba_te[_pos]):.2e}",
        "",
        f"  全部 500 位客戶的最大誤差     = {np.abs(BASE + shap_vals.sum(1) - proba_te).max():.2e}",
    ]
    mo.Html("<pre>" + html.escape("\n".join(_lines)) + "</pre>")
    return (row0,)


@app.cell(hide_code=True)
def _(BASE, mo, proba_te, row0):
    mo.md(
        f"""
    看懂這張表，SHAP 就懂一半了：

    - 從 **{BASE:.4f}**（全體平均）出發，一路走到 **{proba_te[0]:.4f}**（這一位的預測）。
    - `f2` 一個人就推了 **{row0["f2"]:+.4f}**——超過總差距的一半。
    - `f3` 是 **{row0["f3"]:+.4f}**：它在**往回拉**。同一位客戶身上，有的特徵在推、有的在拉，
      SHAP 會把兩邊都算出來，而不是只列「原因」。
    - 誤差是 **{abs(BASE + sum(row0) - proba_te[0]):.0e}** 等級——那是浮點數的捨入誤差，不是近似。

    這條等式也是你**驗證自己沒把 SHAP 用錯**最快的方法：
    算完之後加總一次，對不上就是哪裡錯了（多半是忘了取類別、或欄序跟訓練時不同）。

    > **注意單位**：這裡的 SHAP 值單位是「機率」，因為 sklearn 的樹模型 `TreeExplainer`
    > 預設解釋 `predict_proba` 的輸出。換成 XGBoost／LightGBM 時預設是 **log-odds**，
    > 加總會等於 margin 而不是機率——看到「加起來不等於機率」先確認這件事，
    > 第 9 節的 `LinearExplainer` 就是 log-odds 的例子。
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 4️⃣ 局部解釋：這一位客戶為什麼是這個分數

    全域重要度回答「模型整體靠什麼」，但打電話給客戶的人需要的是**這一位**的理由。
    三張圖各有分工：

    - **waterfall（瀑布圖）**：一位客戶，從基準走到預測值的每一步。給人看的圖。
    - **beeswarm（蜂群圖）**：全部客戶疊在一起，看得出**方向**（這個特徵越大，機率越高還是越低）。
    - **dependence / scatter（依賴圖）**：一個特徵的值 vs 它的 SHAP 值，看形狀與交互作用。

    先挑三位有代表性的客戶：預測機率**最高**、**最接近 0.5**、**最低**的各一位。
    """
    )
    return


@app.cell
def _(Xte, mo, np, proba_te):
    POS_HI = int(np.argmax(proba_te))
    POS_MID = int(np.argmin(np.abs(proba_te - 0.5)))
    POS_LO = int(np.argmin(proba_te))
    CASES = {
        "高風險": POS_HI,
        "說不準": POS_MID,
        "低風險": POS_LO,
    }
    mo.md(
        f"""
    | 代號 | 客戶編號 | 測試集位置 | 預測流失機率 |
    |---|---|---|---|
    | 高風險 | #{Xte.index[POS_HI]} | {POS_HI} | **{proba_te[POS_HI]:.4f}** |
    | 說不準 | #{Xte.index[POS_MID]} | {POS_MID} | {proba_te[POS_MID]:.4f} |
    | 低風險 | #{Xte.index[POS_LO]} | {POS_LO} | {proba_te[POS_LO]:.4f} |
    """
    )
    return CASES, POS_HI, POS_LO, POS_MID


@app.cell
def _(POS_HI, Xte, plt, shap, tree_explainer):
    expl = tree_explainer(Xte)  # Explanation 物件：值、資料、基準都包在一起

    plt.close("all")
    plt.figure()
    shap.plots.waterfall(expl[POS_HI, :, 1], max_display=8, show=False)
    _f = plt.gcf()
    _f.set_size_inches(6.4, 4.0)  # shap 預設 8 吋寬，窄螢幕會爆版
    _f.suptitle("HIGH-RISK customer", y=1.02, fontsize=10)
    _f.tight_layout()
    _f
    return (expl,)


@app.cell
def _(POS_LO, expl, plt, shap):
    plt.close("all")
    plt.figure()
    shap.plots.waterfall(expl[POS_LO, :, 1], max_display=8, show=False)
    _f = plt.gcf()
    _f.set_size_inches(6.4, 4.0)
    _f.suptitle("LOW-RISK customer", y=1.02, fontsize=10)
    _f.tight_layout()
    _f
    return


@app.cell(hide_code=True)
def _(BASE, FEATS, POS_HI, POS_LO, Xte, mo, pd, proba_te, shap_vals):
    _hi = pd.Series(shap_vals[POS_HI], index=FEATS).sort_values(key=abs, ascending=False)
    _lo = pd.Series(shap_vals[POS_LO], index=FEATS).sort_values(key=abs, ascending=False)
    mo.md(
        f"""
    兩張瀑布圖，同一個模型，兩個世界：

    **高風險客戶 #{Xte.index[POS_HI]}（{proba_te[POS_HI]:.3f}）**——
    從 {BASE:.3f} 出發，`f2 = {Xte.iloc[POS_HI]["f2"]:+.2f}` 推了 **{_hi["f2"]:+.3f}**、
    `f3` 再推 {_hi["f3"]:+.3f}、`f4` {_hi["f4"]:+.3f}，一路加到 {proba_te[POS_HI]:.3f}。
    **這位客戶身上幾乎沒有任何一項在往下拉**（最大的負貢獻只有
    {_hi[_hi < 0].min() if (_hi < 0).any() else 0:+.4f}）——所以他不是「某一項特別糟」，而是**全面偏向流失**。

    **低風險客戶 #{Xte.index[POS_LO]}（{proba_te[POS_LO]:.3f}）**——每一項都是負的，
    `f2 = {Xte.iloc[POS_LO]["f2"]:+.2f}` 拉了 **{_lo["f2"]:+.3f}**、
    `f9 = {Xte.iloc[POS_LO]["f9"]:+.2f}` 拉了 {_lo["f9"]:+.3f}。
    注意 `f9` 在全域排名只有第 3，但在**這一位**身上是第 2 大的原因——
    **全域重要度不能拿來解釋個案**，這是可解釋性最常被誤用的地方。

    圖左邊那一欄灰色數字（`{Xte.iloc[POS_HI]["f2"]:.3f} = f2`）是**這位客戶的特徵值**，
    右邊紅／藍條上的數字才是 SHAP 值。給業務看的時候這兩個要分清楚：
    「您的 f2 是 1.45」是事實，「它把機率推高了 0.23」是模型的想法。
    """
    )
    return


@app.cell
def _(expl, plt, shap):
    plt.close("all")
    shap.plots.beeswarm(expl[:, :, 1], max_display=8, show=False, plot_size=(6.2, 4.0))
    plt.gcf()
    return


@app.cell(hide_code=True)
def _(FEATS, Xte, mo, np, shap_vals):
    _dirs = {
        f: float(np.corrcoef(Xte[f].values, shap_vals[:, FEATS.index(f)])[0, 1])
        for f in ["f2", "f3", "f9", "f4", "f0"]
    }
    _rows = "\n".join(
        f"    | {f} | {v:+.3f} | 特徵值越大，流失機率{'越高' if v > 0 else '越低'} |"
        for f, v in _dirs.items()
    )
    mo.md(
        f"""
    **蜂群圖怎麼讀**：每一個點是一位客戶。橫軸是 SHAP 值（往右＝推高流失機率），
    顏色是那位客戶的**特徵值**（紅＝高、藍＝低）。所以：

    - `f2` 那一列：**左邊全藍、右邊全紅** → f2 越大，流失機率越高。
    - `f3` 那一列：**顏色反過來** → f3 越大，流失機率越低。
    - 越下面的列點越擠在 0 附近，那就是「不重要」長的樣子。

    用相關係數把「方向」量化出來（特徵值 vs 它的 SHAP 值）：

    | 特徵 | corr(值, SHAP) | 方向 |
    |---|---|---|
{_rows}

    這張圖是**上線前審核**最好用的一張：把它拿給業務看，問一句
    「照你們的經驗，這個方向對嗎？」——方向跟常識相反的特徵，
    十次有九次是資料處理出了問題（符號寫反、欄位對錯位、缺值被填成 0）。
    """
    )
    return


@app.cell
def _(expl, plt, shap):
    plt.close("all")
    shap.plots.scatter(expl[:, 2, 1], color=expl[:, 3, 1], show=False)
    _f = plt.gcf()
    _f.set_size_inches(6.2, 3.8)
    _f.tight_layout()
    _f
    return


@app.cell(hide_code=True)
def _(FEATS, Xte, mo, np, shap_vals):
    _x2 = Xte["f2"].values
    _s2 = shap_vals[:, FEATS.index("f2")]
    _bins = [(-4, -1), (-1, -0.3), (-0.3, 0.3), (0.3, 1), (1, 4)]
    _rows = []
    for _lo_, _hi_ in _bins:
        _m = (_x2 >= _lo_) & (_x2 < _hi_)
        _rows.append(f"    | [{_lo_}, {_hi_}) | {int(_m.sum())} | {_s2[_m].mean():+.3f} |")
    _near = (_x2 > 0.9) & (_x2 < 1.1)
    mo.md(
        f"""
    **依賴圖怎麼讀**：橫軸是 `f2` 的真實值，縱軸是它在那位客戶身上的 SHAP 值，
    顏色是 `f3`（用來看交互作用）。把它分箱平均看得更清楚：

    | f2 的範圍 | 客戶數 | 平均 SHAP |
    |---|---|---|
{chr(10).join(_rows)}

    形狀是 **S 形**（兩端都會飽和）：中段（−1 到 +1）推力變化最劇烈，
    超過 1 之後再高也就那樣（平均 {_s2[_x2 > 1].mean():+.3f}）——樹模型學到的是「切點」不是直線，
    所以曲線會有平台。這也是為什麼線性模型的一個係數講不出這件事。

    **交互作用怎麼看**：注意 f2 ≈ 1.0 附近那一小群
    （{int(_near.sum())} 位客戶，f2 幾乎一樣），他們的 SHAP 值卻從
    {_s2[_near].min():.3f} 散到 {_s2[_near].max():.3f}——**相差超過兩倍**。
    同樣的 f2 值，在不同客戶身上推力不同，差別來自其他特徵——這就是交互作用。
    一句話：**SHAP 值不是「f2 的效果」，是「f2 在這位客戶身上的效果」。**
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 5️⃣ 上線前審核：把解釋掛進 MLflow，跟 champion 一起版本化

    前面四節都是在 notebook 裡「看」。要變成 MLOps 資產，它必須滿足三個條件：
    **跟模型版本綁在一起、之後查得到、跟當時的數字一模一樣**。

    這正是 MLflow run 的工作。做法只有兩個 API：

    - `mlflow.log_figure(fig, "explain/global_beeswarm.png")`——圖直接進 artifact，不用先存檔。
    - `mlflow.log_dict(obj, "explain/global_importance.json")`——數字進 artifact，之後可以程式化比對。

    重點在**掛到哪一個 run**：解釋是訓練完之後才算的，所以用
    `mlflow.start_run(run_id=訓練那個 run 的 id)` 續掛回去，而不是另開一個 run
    ——否則半年後你會有一堆孤兒解釋報告，對不回是哪一版模型。
    """
    )
    return


@app.cell
def _(AUC, WORK, mlflow):
    mlflow.set_tracking_uri(f"sqlite:///{WORK}/mlflow.db")
    EXP_ID = mlflow.create_experiment(
        "churn-explainability", artifact_location=str(WORK / "artifacts")
    )
    mlflow.set_experiment(experiment_id=EXP_ID)

    with mlflow.start_run(run_name="rf-depth8") as _run:
        mlflow.log_params({"model": "RandomForest", "n_estimators": 100, "max_depth": 8})
        mlflow.log_metric("test_auc", AUC)
        TRAIN_RUN_ID = _run.info.run_id

    print(f"訓練 run 建好了：{TRAIN_RUN_ID}（這就是 Registry 裡 champion 指到的那一個）")
    return EXP_ID, TRAIN_RUN_ID


@app.cell
def _(
    BASE,
    CASES,
    POS_HI,
    POS_LO,
    TRAIN_RUN_ID,
    Xte,
    expl,
    html,
    imp_shap,
    mlflow,
    mo,
    plt,
    proba_te,
    shap,
):
    with mlflow.start_run(run_id=TRAIN_RUN_ID):  # ← 續掛回訓練那個 run
        plt.close("all")
        shap.plots.beeswarm(expl[:, :, 1], max_display=8, show=False, plot_size=(6.2, 4.0))
        mlflow.log_figure(plt.gcf(), "explain/global_beeswarm.png")

        for _name, _pos in [("high_risk", POS_HI), ("low_risk", POS_LO)]:
            plt.close("all")
            plt.figure()
            shap.plots.waterfall(expl[_pos, :, 1], max_display=8, show=False)
            plt.gcf().set_size_inches(6.4, 4.0)
            mlflow.log_figure(plt.gcf(), f"explain/waterfall_{_name}.png")
        plt.close("all")

        mlflow.log_dict(
            {
                "base_value": round(BASE, 5),
                "mean_abs_shap": {k: round(float(v), 5) for k, v in imp_shap.items()},
                "top3": imp_shap.sort_values(ascending=False).index[:3].tolist(),
                "explained_rows": len(Xte),
                "cases": {
                    k: {"customer": int(Xte.index[p]), "prob": round(float(proba_te[p]), 4)}
                    for k, p in CASES.items()
                },
            },
            "explain/global_importance.json",
        )

    _client = mlflow.MlflowClient()
    _files = [a.path for a in _client.list_artifacts(TRAIN_RUN_ID, "explain")]
    mo.Html(
        "<pre>"
        + html.escape("run " + TRAIN_RUN_ID + " 的 artifacts：\n" + "\n".join("  " + f for f in _files))
        + "</pre>"
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ### 審核要看什麼：三個問題，一個真的抓得到的災難

    有了這份報告，模型評審就有東西可以問了。三個問題按殺傷力排序：

    1. **有沒有一枝獨秀的特徵？** 一欄的重要度遠遠壓過其他所有欄，最常見的原因是**資料洩漏**
       ——那一欄裡混進了「當時還不知道的答案」。
    2. **方向合不合常識？**（第 4 節的蜂群圖）方向反了，多半是資料處理錯了。
    3. **有沒有用到不該用的欄位？**（第 7 節）

    第 1 個問題值得當場做一次。假設有人在特徵表加了一欄 `days_since_cancel`
    （「距離上次取消服務幾天」），聽起來很合理，但它其實是**在客戶流失之後才算得出來的**。
    """
    )
    return


@app.cell
def _(
    RandomForestClassifier,
    Xte,
    Xtr,
    imp_shap,
    mo,
    np,
    pd,
    roc_auc_score,
    shap,
    yte,
    ytr,
):
    _rng = np.random.default_rng(0)
    Xtr_leak = Xtr.copy()
    Xte_leak = Xte.copy()
    Xtr_leak["days_since_cancel"] = ytr * 2.0 + _rng.normal(0, 0.5, len(ytr))
    Xte_leak["days_since_cancel"] = yte * 2.0 + _rng.normal(0, 0.5, len(yte))

    rf_leak = RandomForestClassifier(n_estimators=100, max_depth=8, random_state=0).fit(
        Xtr_leak, ytr
    )
    auc_leak = roc_auc_score(yte, rf_leak.predict_proba(Xte_leak)[:, 1])
    imp_leak = pd.Series(
        np.abs(shap.TreeExplainer(rf_leak).shap_values(Xte_leak)[:, :, 1]).mean(0),
        index=Xte_leak.columns,
    ).sort_values(ascending=False)

    share_leak = float(imp_leak.iloc[0] / imp_leak.sum())
    share_ok = float(imp_shap.max() / imp_shap.sum())

    mo.md(
        f"""
    | | 正常模型 | 混進洩漏特徵 |
    |---|---|---|
    | 測試集 AUC | 0.9684 | **{auc_leak:.4f}** |
    | 重要度冠軍 | f2（{imp_shap.max():.4f}） | **days_since_cancel（{imp_leak.iloc[0]:.4f}）** |
    | 冠軍佔全部重要度 | {share_ok:.1%} | **{share_leak:.1%}** |

    AUC {auc_leak:.4f}。如果你只看指標，這是一個**該開香檳的模型**——
    而它上線之後會是一場災難，因為預測時根本拿不到這一欄（客戶還沒走，哪來的「取消後幾天」）。

    **重要度分佈是抓洩漏最便宜的雷達**：正常模型的冠軍佔 {share_ok:.0%}，
    洩漏模型的冠軍佔 {share_leak:.0%}。看到一欄吃掉大半重要度、而且 AUC 好得不像話，
    先問一句「這一欄在預測的那一刻真的存在嗎？」——這個問題救過的專案，比任何演算法都多。

    > 這不是說「重要度集中就一定是洩漏」（真的有主導特徵的問題確實存在）。
    > 它是**一個要求你解釋的訊號**，不是判決。
    """
    )
    return auc_leak, imp_leak, share_leak, share_ok


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 6️⃣ 監控：重要度什麼時候會變、什麼時候不會

    第 7 課（模型監控）看的是「**哪個特徵的分佈變了**」。這一課看的是「**哪個特徵在決定**」。
    兩件事很容易混為一談，做一次實驗就分得清楚了。

    **實驗 A：同一個模型 + 漂移的資料。** 把生產資料的 `f0` 整體平移 +1.5（跟第 7 課同一種漂移），
    丟給**同一個模型**，重算 SHAP。你猜重要度排名會不會變？
    """
    )
    return


@app.cell
def _(FEATS, Xte, imp_shap, mo, np, pd, proba_te, rf, roc_auc_score, shap, tree_explainer, yte):
    Xte_drift = Xte.copy()
    Xte_drift["f0"] = Xte_drift["f0"] + 1.5

    proba_drift = rf.predict_proba(Xte_drift)[:, 1]
    imp_drift = pd.Series(
        np.abs(tree_explainer.shap_values(Xte_drift)[:, :, 1]).mean(0), index=FEATS
    )

    _order = imp_shap.sort_values(ascending=False).index
    _rows = "\n".join(
        f"    | {f} | {imp_shap[f]:.4f} (#{int(imp_shap.rank(ascending=False)[f])}) "
        f"| {imp_drift[f]:.4f} (#{int(imp_drift.rank(ascending=False)[f])}) "
        f"| {imp_drift[f] - imp_shap[f]:+.4f} |"
        for f in _order[:6]
    )
    _same = list(imp_shap.sort_values(ascending=False).index) == list(
        imp_drift.sort_values(ascending=False).index
    )

    mo.md(
        f"""
    | 特徵 | 正常資料 | f0 漂移 +1.5 之後 | 差 |
    |---|---|---|---|
{_rows}

    - 測試集 AUC：0.9684 → **{roc_auc_score(yte, proba_drift):.4f}**
    - 平均預測機率：{proba_te.mean():.4f} → **{proba_drift.mean():.4f}**（這是第 7 課會抓到的**預測漂移**）
    - 12 欄的重要度排名完全一樣：**{_same}**

    **排名一動也沒動。** f0 自己從 {imp_shap["f0"]:.4f} 微升到 {imp_drift["f0"]:.4f}
    （因為更多客戶落在推力較大的區間），但沒有任何一欄換位置。

    這件事其實很合理，只是第一次看到會意外：**模型是同一個模型，樹是同一批樹，
    它的「想法」當然沒變。** 變的是資料，不是模型。

    > **所以：SHAP 重要度不是資料漂移偵測器。** 想知道「輸入變了沒」，
    > 用第 7 課的 PSI／KS；想知道「模型的想法變了沒」，用重要度排名。
    > 兩個問題、兩個工具，混用會讓你在最需要警報的時候什麼都收不到。
    """
    )
    return Xte_drift, imp_drift, proba_drift


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    **實驗 B：重訓之後才是重要度該警報的時候。**

    假設上游改版，某個欄位的計算壞掉了——`f2` 被灌成常數 0（欄位改名、join 失敗、
    預設值填 0，這種事每季都會發生一次）。管線照常跑完、模型照常重訓、
    照常註冊成新版本，**沒有任何一個步驟報錯**。
    """
    )
    return


@app.cell
def _(FEATS, RandomForestClassifier, Xte, Xtr, imp_shap, mo, np, pd, roc_auc_score, shap, yte, ytr):
    Xtr_bug = Xtr.copy()
    Xte_bug = Xte.copy()
    Xtr_bug["f2"] = 0.0
    Xte_bug["f2"] = 0.0

    rf_bug = RandomForestClassifier(n_estimators=100, max_depth=8, random_state=0).fit(
        Xtr_bug, ytr
    )
    auc_bug = roc_auc_score(yte, rf_bug.predict_proba(Xte_bug)[:, 1])
    imp_bug = pd.Series(
        np.abs(shap.TreeExplainer(rf_bug).shap_values(Xte_bug)[:, :, 1]).mean(0), index=FEATS
    )

    top_before = list(imp_shap.sort_values(ascending=False).index[:5])
    top_after = list(imp_bug.sort_values(ascending=False).index[:5])
    moved = sum(
        1
        for f in FEATS
        if int(imp_shap.rank(ascending=False)[f]) != int(imp_bug.rank(ascending=False)[f])
    )

    mo.md(
        f"""
    | | 上一版 champion | 重訓後的新版 |
    |---|---|---|
    | 測試集 AUC | 0.9684 | **{auc_bug:.4f}** |
    | 前五名 | {" → ".join(top_before)} | **{" → ".join(top_after)}** |
    | f2 的 mean&#124;SHAP&#124; | {imp_shap["f2"]:.4f} | **{imp_bug["f2"]:.4f}** |
    | 換過位置的欄位數 | — | **{moved} / 12** |

    AUC 掉到 {auc_bug:.4f}——**掉了，但沒掉到會有人尖叫的程度**。0.89 的模型看起來還行，
    品質閘門若設在 0.85 就會放它過關。而重要度講的是完全不同的故事：
    **原本一個人扛起 {imp_shap["f2"] / imp_shap.sum():.0%} 決策權的 f2，貢獻變成 {imp_bug["f2"]:.4f}**，
    前五名整批換人。

    這就是「重要度排名警報」該長的樣子——實務上的做法：

    ```python
    prev = json.loads(client.download_artifacts(champion_run, "explain/global_importance.json"))
    new_top = imp.sort_values(ascending=False).index[:5].tolist()
    if new_top[:3] != prev["top3"]:
        raise AssertionError(f"重要度前三名變了：{{prev['top3']}} → {{new_top[:3]}}")
    ```

    把它寫成 Dagster 的 `@asset_check`（第 3 課）或 pytest（第 13 課），
    每次重訓都跟上一版的解釋報告比一次。**這是第 5 節那份 artifact 的真正用途**：
    它不是給人看的圖，是給下一次重訓當比較基準的資料。

    > 門檻怎麼定？「前三名有沒有換人」比「數值差多少」穩，因為數值本來就會隨機浮動。
    > 而且警報的動作是**要求人來看一眼**，不是自動擋——重要度變了也可能只是模型真的變好了。
    """
    )
    return Xte_bug, Xtr_bug, auc_bug, imp_bug, moved, rf_bug, top_after, top_before


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 7️⃣ 合規：禁用欄位的 SHAP 必須接近 0

    法遵給你一張清單：「這幾欄是敏感資訊（例如地區、年齡），可以用來統計，
    **不得作為個案決策的依據**。」

    「沒有放進訓練資料」是最乾淨的做法，但真實專案裡特徵表是共用的、
    是別的團隊維護的、上週還多了三欄。所以你需要一個**每次上線都跑一次的檢查**：
    這些欄位對模型輸出的實際影響必須接近 0。

    寫成函式只有幾行——注意它回傳的是報告不是 `True/False`，
    因為出事的時候你需要知道**差多少**：
    """
    )
    return


@app.cell
def _(FEATS, html, mo, np, pd, shap_vals):
    def forbidden_report(shap_matrix, columns, forbidden, threshold=0.01):
        """禁用欄位檢查：每一欄的 mean|SHAP| 必須低於 threshold。"""
        imp = pd.Series(np.abs(shap_matrix).mean(0), index=columns)
        out = []
        for col in forbidden:
            v = float(imp[col])
            out.append((col, v, threshold, "PASS" if v < threshold else "FAIL"))
        return out

    FORBIDDEN = ["f8", "f6"]  # 假設這兩欄是法遵指定的敏感欄位
    _report = forbidden_report(shap_vals, FEATS, FORBIDDEN + ["f2"])

    _lines = [f"{'欄位':<6}{'mean|SHAP|':>12}{'門檻':>10}   結果", "-" * 42]
    _lines += [f"{c:<6}{v:>12.4f}{t:>10.2f}   {r}" for c, v, t, r in _report]
    _lines += [
        "",
        "（f2 不是禁用欄位，放進來只是為了看 FAIL 長什麼樣）",
    ]
    mo.Html("<pre>" + html.escape("\n".join(_lines)) + "</pre>")
    return FORBIDDEN, forbidden_report


@app.cell(hide_code=True)
def _(imp_shap, mo):
    mo.md(
        f"""
    `f8` 的 mean|SHAP| 是 {imp_shap["f8"]:.4f}，過關；
    `f6` 是 **{imp_shap["f6"]:.4f}**，超過 0.01 的門檻，**沒過**。

    這時候該做的**不是把門檻調到 0.02**（雖然那樣報告會變綠色）。正確的處理有三步：

    1. **從訓練資料把它拿掉重訓**，看代價有多大。實測拿掉 `f6` 之後 AUC 是 **0.9699**
       ——比原本的 0.9684 還高一點點。合規要求常常沒有你以為的那麼貴，做過才知道。
    2. **確認沒有代理特徵頂上來**。這一步比第 1 步重要得多，下一格示範。
    3. **把檢查寫進管線**，每次重訓都跑，不是上線前才想起來。

    > 門檻 0.01 怎麼來的？它是**你要跟法遵一起決定的業務參數**，不是統計常數。
    > 一個可以拿去談的講法：「這一欄平均把預測機率推動不到 1 個百分點」。
    > 重點是門檻要寫在程式裡、被版本控制、每次都跑——而不是靠某個人記得檢查。
    """
    )
    return


@app.cell
def _(RandomForestClassifier, Xte, Xtr, mo, np, pd, roc_auc_score, shap, ytr, yte):
    _rng = np.random.default_rng(2)
    Xtr_proxy = Xtr.copy()
    Xte_proxy = Xte.copy()
    # 「地區評分」：跟 f2 高度相關，但名字完全無辜
    Xtr_proxy["region_score"] = Xtr_proxy["f2"] * 0.95 + _rng.normal(0, 0.4, len(Xtr_proxy))
    Xte_proxy["region_score"] = Xte_proxy["f2"] * 0.95 + _rng.normal(0, 0.4, len(Xte_proxy))
    # 依規定把禁用欄位 f2 拿掉——名單上乾乾淨淨
    Xtr_proxy = Xtr_proxy.drop(columns=["f2"])
    Xte_proxy = Xte_proxy.drop(columns=["f2"])

    rf_proxy = RandomForestClassifier(n_estimators=100, max_depth=8, random_state=0).fit(
        Xtr_proxy, ytr
    )
    auc_proxy = roc_auc_score(yte, rf_proxy.predict_proba(Xte_proxy)[:, 1])
    imp_proxy = pd.Series(
        np.abs(shap.TreeExplainer(rf_proxy).shap_values(Xte_proxy)[:, :, 1]).mean(0),
        index=Xte_proxy.columns,
    ).sort_values(ascending=False)
    corr_proxy = float(np.corrcoef(Xte["f2"], Xte_proxy["region_score"])[0, 1])

    mo.md(
        f"""
    現在把 `f2` 當成禁用欄位，**照規定移除**，但特徵表裡另外有一欄
    `region_score`（與 f2 的相關係數 **{corr_proxy:.2f}**）：

    - 禁用欄位檢查：`f2` 不在欄位清單裡 → **PASS**（因為它根本不存在）
    - 模型 AUC：**{auc_proxy:.4f}**（原本 0.9684，幾乎沒損失）
    - 新的重要度冠軍：**`region_score` {imp_proxy.iloc[0]:.4f}**（原本 f2 是 0.2137）

    **模型照樣在用那個資訊，只是換了個名字。** 這叫代理特徵（proxy），
    是所有「禁用欄位」制度共同的漏洞——而且它不需要有人故意，
    只要特徵表裡有任何跟禁用欄位相關的東西就會自然發生。

    SHAP 幫得上忙的地方是**讓它現形**：一個新欄位突然衝上重要度第一名，
    你至少會問一句「這欄是怎麼算出來的？」。真正的解法在資料治理那一層
    ——查代理欄位（跟禁用欄位算相關係數）、要求特徵有來源說明——
    但這一課至少告訴你：**只查名字的合規檢查，是會被繞過去的**。
    """
    )
    return Xte_proxy, Xtr_proxy, auc_proxy, corr_proxy, imp_proxy, rf_proxy


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 8️⃣ 對客戶說明：把 waterfall 變成三句中文

    瀑布圖是給你看的，不是給客戶看的。客服打電話出去需要的是**三句話**：

    1. 你的分數是多少、跟平均比起來如何
    2. 把分數推高的主要原因（＋數字）
    3. 有沒有在幫你加分的項目

    這件事完全可以自動化——SHAP 值本來就是排好序的數字：
    """
    )
    return


@app.cell
def _(BASE, FEATS, POS_HI, POS_LO, Xte, html, mo, pd, proba_te, shap_vals):
    # 真實專案裡這張表會是「近 90 天登入次數」這種人看得懂的名字
    NICE = {
        "f0": "近三個月使用量",
        "f1": "客服接觸次數",
        "f2": "合約剩餘月數指標",
        "f3": "方案滿意度分數",
        "f4": "帳單金額變化",
        "f5": "推薦人數",
        "f6": "服務中斷次數",
        "f7": "付款延遲天數",
        "f8": "裝置數量",
        "f9": "競品優惠曝光度",
        "f10": "客訴紀錄",
        "f11": "續約提醒回應",
    }

    def explain_zh(pos, top_n=3):
        contrib = pd.Series(shap_vals[pos], index=FEATS)
        prob = float(proba_te[pos])
        up = contrib[contrib > 0].sort_values(ascending=False)
        down = contrib[contrib < 0].sort_values()

        def _phrase(s):
            return "、".join(
                f"{NICE[k]}（目前值 {Xte.iloc[pos][k]:+.2f}，推動 {s[k]:+.3f}）" for k in s.index[:top_n]
            )

        s1 = (
            f"這位客戶（編號 {Xte.index[pos]}）未來一季的流失機率我們估計是 {prob:.1%}，"
            f"所有客戶的平均是 {BASE:.1%}。"
        )
        s2 = (
            f"把機率推高最多的是 {_phrase(up)}。"
            if len(up)
            else "沒有任何一項在推高流失機率。"
        )
        s3 = (
            f"往下拉的則有 {_phrase(down)}。"
            if len(down)
            else "而且沒有任何一項在往下拉——每一項都指向流失，建議優先聯繫。"
        )
        return f"{s1}\n{s2}\n{s3}"

    _demo = "\n\n".join(
        f"【{k}】\n{explain_zh(v)}" for k, v in {"高風險": POS_HI, "低風險": POS_LO}.items()
    )
    mo.Html("<pre style='white-space:pre-wrap'>" + html.escape(_demo) + "</pre>")
    return NICE, explain_zh


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    這段模板有三個刻意的設計，每一個都是被投訴教出來的：

    - **先給基準再給分數**：「48.8% 是平均」讓 98.6% 有意義。單獨一個數字客戶只會問「所以呢」。
    - **同時講推高與拉低的**：只講壞消息像在找碴。但**模板一定要有「沒有」的分支**——
      上面那位低風險客戶十二項全是負的，`up` 是空的，沒有這個分支就會印出半句話。
      上線後炸掉的都是這種邊界情況。
    - **把特徵值跟 SHAP 值分開講**：「您的服務中斷次數是 3 次」是事實，
      「這件事把機率推高 0.05」是模型的判斷。混在一起講，客戶會以為你在說「中斷 3 次就會流失」。

    ⚠️ **最後一件事，也是最重要的一件**：這三句話講的是**模型怎麼算的**，
    不是**為什麼會發生**。下一節就講這件事。
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 9️⃣ 限制：SHAP 不是萬能的，誠實比方便重要

    ### ① SHAP 是「模型怎麼想」，不是因果

    這是最常被誤用的一點。`f2` 的 SHAP 是 +0.26，**正確的說法**是
    「這個模型因為 f2 的值而把機率調高了 0.26」；**錯誤的說法**是
    「f2 高導致客戶流失」，更錯的是「把 f2 降下來就能留住客戶」。

    模型只學到相關；相關可能來自因果，也可能來自共同原因、選樣偏誤，或反向因果
    （「客服接觸次數多」不是流失的原因，是**已經想走**的症狀）。
    要談因果得做實驗（A/B）或用因果推論的方法，那是另一門課。

    **實務上的分界線**：SHAP 可以拿來**排優先順序**（先打給誰）與**做審核**（模型有沒有亂來），
    不能拿來**制定干預**（改哪個欄位就會怎樣）。

    ### ② 相關的特徵會分攤貢獻

    如果兩欄講的是同一件事，SHAP 會把功勞拆給兩個人。做一次就看得很清楚：
    """
    )
    return


@app.cell
def _(RandomForestClassifier, Xte, Xtr, imp_shap, mo, np, pd, roc_auc_score, shap, ytr, yte):
    Xtr_dup = Xtr.copy()
    Xte_dup = Xte.copy()
    Xtr_dup["f2_copy"] = Xtr_dup["f2"]  # 一模一樣的一欄（例如同一個指標算了兩種寫法）
    Xte_dup["f2_copy"] = Xte_dup["f2"]

    rf_dup = RandomForestClassifier(n_estimators=100, max_depth=8, random_state=0).fit(
        Xtr_dup, ytr
    )
    imp_dup = pd.Series(
        np.abs(shap.TreeExplainer(rf_dup).shap_values(Xte_dup)[:, :, 1]).mean(0),
        index=Xte_dup.columns,
    )

    mo.md(
        f"""
    | | 原本 | 多了一欄一模一樣的 `f2_copy` |
    |---|---|---|
    | 模型 AUC | 0.9684 | {roc_auc_score(yte, rf_dup.predict_proba(Xte_dup)[:, 1]):.4f} |
    | `f2` 的 mean&#124;SHAP&#124; | **{imp_shap["f2"]:.4f}** | **{imp_dup["f2"]:.4f}** |
    | `f2_copy` 的 mean&#124;SHAP&#124; | — | **{imp_dup["f2_copy"]:.4f}** |
    | 兩者相加 | — | {imp_dup["f2"] + imp_dup["f2_copy"]:.4f} |

    模型一樣強（AUC 幾乎沒動），但 `f2` 的重要度從 {imp_shap["f2"]:.4f} 掉到 {imp_dup["f2"]:.4f}
    ——**腰斬**。它沒有變得比較不重要，只是有人跟它平分功勞。

    這在真實特徵表裡太常見了（「近 30 天訂單數」和「近 30 天訂單金額」高度相關）。
    後果是：**你會低估一整組相關特徵裡每一個成員的重要度**，
    甚至誤以為某個關鍵資訊「模型沒在用」。

    對策不是換工具，是**先看特徵之間的相關係數**，把高度相關的欄位當一組看
    （`shap.plots.bar(..., clustering=...)` 可以自動分群），或乾脆在特徵工程階段就合併。
    """
    )
    return Xte_dup, Xtr_dup, imp_dup, rf_dup


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ### ③ `TreeExplainer` 只吃樹模型——其他模型怎麼辦

    第 2 節那個「500 位客戶不到一秒」的速度是有代價的：`TreeExplainer` 用的是**樹專屬**的演算法。
    餵它一個 `LogisticRegression` 會直接拒絕（錯誤原文在最後一節）。

    SHAP 給了兩條退路：

    - **`KernelExplainer`**：什麼模型都吃（只要能呼叫 `predict`），代價是**慢**。
      它靠反覆遮蔽特徵、重新預測來估計 Shapley value，所以要給它一份**背景資料**
      （被遮掉的特徵用什麼值代替）。下一格量給你看有多慢。
    - **`LinearExplainer`**：線性模型專用，快得像沒算，而且結果有封閉解。
    """
    )
    return


@app.cell
def _(FEATS, Xte, Xtr, mo, np, pd, rf, shap, shap_secs, shap_vals, time):
    _bg = shap.sample(Xtr, 50, random_state=0)  # 背景資料：50 筆代表「一般客戶」
    _t0 = time.time()
    kernel_explainer = shap.KernelExplainer(lambda d: rf.predict_proba(d)[:, 1], _bg)
    kernel_vals = kernel_explainer.shap_values(Xte.head(20), silent=True)
    kernel_secs = time.time() - _t0

    tree20 = shap_vals[:20]  # 同樣這 20 列，TreeSHAP 算過的答案
    corr_kt = float(np.corrcoef(np.asarray(kernel_vals).ravel(), tree20.ravel())[0, 1])

    _k = pd.Series(np.abs(np.asarray(kernel_vals)).mean(0), index=FEATS).sort_values(
        ascending=False
    )

    mo.md(
        f"""
    | | TreeExplainer | KernelExplainer |
    |---|---|---|
    | 適用模型 | 只有樹 | 任何模型 |
    | 這次算了幾列 | 500 | **20** |
    | 花了多久 | {shap_secs:.2f} 秒 | **{kernel_secs:.1f} 秒** |
    | 每列成本 | {shap_secs / 500 * 1000:.1f} 毫秒 | **{kernel_secs / 20 * 1000:.0f} 毫秒** |
    | 基準值 | 0.48824（精確） | {float(kernel_explainer.expected_value):.4f}（背景資料的平均） |
    | 前三名 | f2 / f3 / f9 | {" / ".join(_k.index[:3])} |

    每列差 **{(kernel_secs / 20) / (shap_secs / 500):.0f} 倍**。這 20 列的結果跟 TreeSHAP
    相關係數是 **{corr_kt:.4f}**——答案幾乎一樣，只是貴了兩個數量級。

    所以實務規則很簡單：**能用專用 explainer 就用專用的**
    （樹→`TreeExplainer`、線性→`LinearExplainer`、深度學習→`DeepExplainer`／`GradientExplainer`），
    `KernelExplainer` 是最後手段。要用它就別想全量算：抽樣幾百筆看全域、
    個案來申訴時才現算那一筆。

    > 背景資料大小是 `KernelExplainer` 的主要成本來源（時間大約正比於背景筆數）。
    > 官方建議用 `shap.sample(X, 100)` 或 `shap.kmeans(X, 25)` 壓縮，
    > 不要直接把整個訓練集丟進去——那會跑到天亮。
    """
    )
    return corr_kt, kernel_explainer, kernel_secs, kernel_vals, tree20


@app.cell
def _(FEATS, LogisticRegression, Xte, Xtr, mo, np, pd, roc_auc_score, shap, time, yte, ytr):
    logreg = LogisticRegression(max_iter=1000).fit(Xtr, ytr)
    auc_lr = roc_auc_score(yte, logreg.predict_proba(Xte)[:, 1])

    _t0 = time.time()
    _masker = shap.maskers.Independent(Xtr, max_samples=len(Xtr))
    linear_explainer = shap.LinearExplainer(logreg, _masker)
    linear_vals = np.asarray(linear_explainer.shap_values(Xte))
    linear_secs = time.time() - _t0

    coef = pd.Series(logreg.coef_[0], index=FEATS)
    manual = (Xte - Xtr.mean()).values * coef.values  # coef × (x − 平均)
    imp_linear = pd.Series(np.abs(linear_vals).mean(0), index=FEATS).sort_values(ascending=False)
    base_lr = float(np.atleast_1d(linear_explainer.expected_value)[0])

    _rows = "\n".join(
        f"    | {f} | {coef[f]:+.4f} | {abs(coef[f]) * Xtr[f].std(ddof=0):.4f} | {imp_linear[f]:.4f} |"
        for f in imp_linear.index[:6]
    )

    mo.md(
        f"""
    `LinearExplainer` 花了 **{linear_secs * 1000:.1f} 毫秒**（logreg 測試集 AUC {auc_lr:.4f}）——
    500 列一次算完，比 `TreeExplainer` 還快三個數量級。
    它的結果不是估計，是**封閉解**：

    ```text
    SHAP(第 i 筆, 第 j 欄) = coef[j] × (x[i, j] − 訓練集平均[j])
    ```

    實測 `shap_values` 與手算的最大差距是 **{np.abs(linear_vals - manual).max():.1e}**（完全相等）。
    這也是理解 SHAP 最好的入口：**線性模型的 SHAP 就是「係數 × 這一筆偏離平均多少」**，
    樹模型只是把同一個概念推廣到非線性。

    | 特徵 | 係數 coef | &#124;coef&#124; × 標準差 | mean&#124;SHAP&#124; |
    |---|---|---|---|
{_rows}

    看第二欄與第四欄的關係：**mean&#124;SHAP&#124; 的排名跟 &#124;coef&#124;×標準差 完全一致**，
    但跟「只看係數大小」從第 6 名起就不同（係數排 f8 在 f4 前面，SHAP 反過來）。
    原因很直白：一個係數再大，如果那一欄在資料裡幾乎不變動，它對實際預測就沒有影響力。
    **「係數大 ＝ 重要」是統計課上的簡化，實務上要乘上變異數。**

    ⚠️ 單位陷阱：`expected_value` 是 **{base_lr:.5f}**，不是 0.488——
    因為 `LinearExplainer` 解釋的是 **log-odds**（`decision_function`），不是機率。
    換算回機率是 {1 / (1 + np.exp(-base_lr)):.4f}。跨 explainer 比較數字之前，先確認單位。
    """
    )
    return auc_lr, base_lr, coef, imp_linear, linear_explainer, linear_secs, linear_vals, logreg, manual


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 🎛 互動：挑一位客戶，看他的解釋

    下拉選一位客戶（依預測機率從高到低排），下面會出現他的瀑布圖與三句中文說明。
    建議的玩法：

    - 選最上面幾位（機率 > 0.95）：看看是不是每一項都在推高。
    - 選中間那幾位（機率接近 0.5）：**推力與拉力互相抵消**長什麼樣——
      這種客戶最值得人工看一眼，因為模型自己也沒把握。
    - 選最下面幾位（機率 < 0.05）：注意主要原因跟高風險客戶是不是同一批特徵。
    """
    )
    return


@app.cell
def _(Xte, mo, np, proba_te):
    _order = np.argsort(-proba_te)
    _picks = [int(_order[i]) for i in np.linspace(0, len(_order) - 1, 15).astype(int)]
    _default = _picks[7]  # 預設落在中間那位（推力與拉力互相抵消，最有看頭）
    customer_pick = mo.ui.dropdown(
        options={f"#{Xte.index[p]}　機率 {proba_te[p]:.3f}": p for p in _picks},
        value=f"#{Xte.index[_default]}　機率 {proba_te[_default]:.3f}",
        label="選一位客戶",
    )
    customer_pick
    return (customer_pick,)


@app.cell
def _(customer_pick, expl, mo, plt, shap):
    if customer_pick.value is None:
        _out = mo.md("**請先在上面選一位客戶。**")
    else:
        plt.close("all")
        plt.figure()
        shap.plots.waterfall(expl[int(customer_pick.value), :, 1], max_display=8, show=False)
        _f = plt.gcf()
        _f.set_size_inches(6.4, 4.0)
        _f.tight_layout()
        _out = _f
    _out
    return


@app.cell
def _(customer_pick, explain_zh, html, mo):
    if customer_pick.value is None:
        _card = mo.md("—")
    else:
        _card = mo.Html(
            "<pre style='white-space:pre-wrap;background:#f7f5ef;padding:12px;"
            "border-radius:8px;line-height:1.7'>"
            + html.escape(explain_zh(int(customer_pick.value)))
            + "</pre>"
        )
    _card
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 🏆 延伸挑戰

    1. **LEVEL 1**：找出測試集裡「SHAP 貢獻總和最負」的那位客戶（也就是模型最確定不會流失的人），
       印出他的前三大原因，並用第 8 節的模板產出三句說明。
       想一下：他跟「機率最低」的那位是同一個人嗎？為什麼？
    2. **LEVEL 2**：用 `LinearExplainer` 解釋 logistic regression，把
       mean|SHAP| 排名、|coef| 排名、|coef|×標準差 排名三者並排印出來，
       找出**排名不一致的那一對特徵**，並解釋為什麼。
    3. **LEVEL 3**：寫一個「禁用欄位檢查」的**失敗案例**：把 `f2` 改名成 `is_vip` 訓練一個模型，
       斷言 `is_vip` 的 mean|SHAP| < 0.01 —— 這個斷言**應該要失敗**。
       接著把它修好（提示：修的方法不是調門檻），並回答「修好之後模型損失多少 AUC」。

    先自己試，卡住再展開下面的提示與參考解答。
    帶得走：下載本檔後 `uvx marimo edit --sandbox model-explainability_ext.py`
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
    total = shap_vals.sum(1)                    # 每一位客戶 12 個 SHAP 值的總和
    pos = int(total.argmin())                   # 總和最負的那一位
    print(Xte.index[pos], proba_te[pos], BASE + total[pos])
    print(pd.Series(shap_vals[pos], index=FEATS).sort_values().head(3))
    print(explain_zh(pos))
    ```

    **預期輸出**：客戶 #775、機率 0.0041，前三大原因是
    `f2 -0.2152`、`f9 -0.0968`、`f3 -0.0516`。

    **他跟「機率最低」的那位是同一個人**——而且一定是同一個人：
    因為 `預測 = BASE + 總和`，而 BASE 對每一筆都一樣，所以「總和最小」等價於「預測最小」。
    這就是第 3 節那條加總等式的直接推論。（如果你算出來不是同一位，去檢查是不是忘了取 `[:, :, 1]`。）
    """
            ),
            "💡 LEVEL 2 參考解答": mo.md(
                r"""
    ```python
    masker = shap.maskers.Independent(Xtr, max_samples=len(Xtr))
    lin = shap.LinearExplainer(LogisticRegression(max_iter=1000).fit(Xtr, ytr), masker)
    lv = np.asarray(lin.shap_values(Xte))

    cmp = pd.DataFrame({
        "mean_abs_shap": np.abs(lv).mean(0),
        "abs_coef": np.abs(logreg.coef_[0]),
        "abs_coef_x_std": np.abs(logreg.coef_[0]) * Xtr.std(ddof=0).values,
    }, index=FEATS)
    print(cmp.rank(ascending=False).astype(int).sort_values("mean_abs_shap"))
    ```

    **預期輸出**：`mean_abs_shap` 與 `abs_coef_x_std` 的排名**每一名都一樣**；
    跟 `abs_coef` 則在第 6、第 8 名互換——係數排名是
    f2, f3, f9, f1, f0, **f8**, f4, f11…，SHAP 排名是 f2, f3, f9, f1, f0, **f4**, f11, f8…

    **為什麼**：SHAP 值是 `coef × (x − 平均)`，所以它的大小同時取決於
    「係數多大」與「這一欄實際上會變動多少」。`f8` 的係數比 `f4` 大，
    但它在資料裡的標準差比較小，實際推動預測的力道反而輸給 `f4`。

    延伸：把 `abs_coef` 這一欄拿去跟業務解釋「哪個因素最重要」，
    就是很多統計報告犯的錯——除非所有特徵都先標準化過。
    """
            ),
            "💡 LEVEL 3 提示": mo.md(
                r"""
    **第一步：讓它紅。**

    ```python
    Xtr_v = Xtr.rename(columns={"f2": "is_vip"})
    Xte_v = Xte.rename(columns={"f2": "is_vip"})
    m = RandomForestClassifier(n_estimators=100, max_depth=8, random_state=0).fit(Xtr_v, ytr)
    v = shap.TreeExplainer(m).shap_values(Xte_v)[:, :, 1]
    imp = pd.Series(np.abs(v).mean(0), index=Xte_v.columns)
    assert imp["is_vip"] < 0.01, f"is_vip 的 mean|SHAP| = {imp['is_vip']:.4f}，遠超門檻"
    ```

    你會看到 `AssertionError: is_vip 的 mean|SHAP| = 0.2137，遠超門檻`——
    因為 `is_vip` 就是換了名字的 `f2`，模型最倚重的那一欄。

    **第二步：怎麼修。** 不是調門檻（那只是把警報關掉），而是
    **把欄位從訓練資料裡拿掉重訓**：`Xtr.drop(columns=["f2"])`。
    重訓後 AUC 會從 0.9684 掉到 **0.8937**，新的重要度冠軍變成
    `f3`（0.1208）→ `f9`（0.0729）→ `f4`（0.0629）。

    **怎麼驗證自己做對了**：三個條件同時成立才算修好——
    ① `is_vip` 不在 `model.feature_names_in_` 裡；
    ② 檢查函式對新模型回 PASS；
    ③ **沒有代理欄位頂上來**（把剩下每一欄跟被移除的欄算相關係數，
    最高的那個要遠低於 0.9——第 7 節的 `region_score` 就是這一關沒過的樣子）。

    **然後把 0.9684 → 0.8937 這個數字拿去談**：合規不是技術決定，
    是業務要在「少 0.075 AUC」與「合規風險」之間做的選擇。
    你的工作是把代價量出來，不是替他們決定。
    """
            ),
        }
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## ❓ 常見錯誤原文速查

    下面每一則都是真的跑出來的（shap 0.52.0 ＋ scikit-learn 1.9）。
    **特別注意標成「不報錯」的那幾則**——它們才是會讓你把錯的圖放進評審簡報的原因。
    """
    )
    return


@app.cell(hide_code=True)
def _(html, mo):
    _txt = """
【1】忘了取類別：把 (n, 12, 2) 直接丟給 summary_plot
    shap.summary_plot(shap_raw, Xte)        # shap_raw 是三維的
    → 不報錯。但畫出來的是另一種圖：x 軸標題變成 'SHAP interaction value'、
      只剩 2 個子圖、y 軸剩兩個特徵——12 個特徵的 summary 不見了。
    修法：vals = shap_raw[:, :, 1]

【2】TreeExplainer 餵非樹模型
    shap.TreeExplainer(LogisticRegression().fit(X, y))
    → InvalidModelError: Model type not yet supported by TreeExplainer:
      <class 'sklearn.linear_model._logistic.LogisticRegression'>
    修法：線性模型用 LinearExplainer，其他用 KernelExplainer。

【3】KernelExplainer 忘了給背景資料
    shap.KernelExplainer(model.predict_proba)
    → TypeError: KernelExplainer.__init__() missing 1 required positional argument: 'data'
    修法：第二個參數給背景資料，例如 shap.sample(Xtr, 50)。

【4】waterfall 餵整批而不是單筆
    shap.plots.waterfall(expl[:, :, 1])
    → ValueError: The waterfall plot can currently only plot a single explanation,
      but a matrix of explanations (shape (500, 12)) was passed! Perhaps try
      shap.plots.waterfall(shap_values[0]) or for multi-output models, try
      shap.plots.waterfall(shap_values[0, 0]).
    修法：waterfall 一次只畫一位客戶 → expl[204, :, 1]

【4b】單筆但忘了選類別
    shap.plots.waterfall(expl[0])
    → 同一句 ValueError，只是 shape 變成 (12, 2)——訊息末尾的
      shap_values[0, 0] 就是在提示你「多輸出模型要再選一維」。

【5】欄名跟訓練時不一致
    model.predict_proba(Xte.rename(columns={"f2": "is_vip"}))
    → ValueError: The feature names should match those that were passed during fit.
      Feature names unseen at fit time:
      - is_vip
      Feature names seen at fit time, yet now missing:
      - f2

    但同一份改名資料丟給 shap：
    explainer.shap_values(Xte.rename(columns={"f2": "is_vip"}))
    → 不報錯，照樣回 (5, 12, 2)。SHAP 不檢查欄名，它信任你給的順序。

【5c】欄序被打亂（欄名都在，只是順序不同）
    model.predict_proba(Xte[list(reversed(FEATS))])
    → ValueError: The feature names should match those that were passed during fit.
      Feature names must be in the same order as they were in fit.

    同樣的資料丟給 shap → 一樣不報錯，回 (5, 12, 2)，但每個值都對到錯的欄位。
    這是本課最危險的一種錯：報告畫得出來、數字有小數點、全部是錯的。
    防身法就是第 3 節那條等式——加總對不上就是哪裡錯了。

【6】用 numpy 陣列算 SHAP
    shap.TreeExplainer(rf)(Xte.to_numpy()).feature_names → None
    → 不報錯，但所有圖上的特徵名會變成 Feature 0、Feature 1……
    修法：一律餵 DataFrame，欄名是解釋的一部分。
"""
    mo.Html("<pre>" + html.escape(_txt.strip("\n")) + "</pre>")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 📌 帶走三句話

    1. **AUC 是總分，SHAP 是明細。** 上線前的審核、合規、對客戶說明，全都需要明細。
       基準 ＋ 各特徵貢獻 ＝ 預測值，這條等式讓「解釋」變成可以驗算的東西。
    2. **三種重要度問的是三個問題**：內建說「建樹時切了幾刀」、permutation 說「有沒有用」、
       SHAP 說「模型實際上怎麼用」。前三名一致代表你可以放心引用；分歧的位置就是該去理解的地方。
    3. **解釋要跟模型一起版本化。** 掛成 MLflow artifact、每次重訓比一次前三名、
       禁用欄位每次都檢查——**沒有寫進管線的解釋，就只是一張漂亮的圖。**

    這是這個系列目前的最後一課。回頭再走一遍主線，你會發現每一課都在回答同一個問題的一部分：
    **這個模型現在是什麼樣子，而我怎麼知道？**
    """
    )
    return


if __name__ == "__main__":
    app.run()
