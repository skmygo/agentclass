# 課程 model-explainability 的「真實錯誤原文」蒐集器（測驗題與 notebook 速查表的來源）
# 用法：uv run --script content/mlops/_spikes/spike_shap_errors.py
# 每一段都是「新手真的會犯」的錯，印出未經修飾的例外類別與訊息。
# /// script
# requires-python = ">=3.11"
# dependencies = ["shap>=0.46", "scikit-learn", "pandas", "numpy", "matplotlib"]
# ///
import warnings

import matplotlib

matplotlib.use("Agg")
import numpy as np
import pandas as pd
import shap
from sklearn.datasets import make_classification
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split

warnings.filterwarnings("ignore")

X, y = make_classification(n_samples=2000, n_features=12, n_informative=6, random_state=0)
COLS = [f"f{i}" for i in range(12)]
Xdf = pd.DataFrame(X, columns=COLS)
Xtr, Xte, ytr, yte = train_test_split(Xdf, y, test_size=0.25, random_state=0)
rf = RandomForestClassifier(n_estimators=100, max_depth=8, random_state=0).fit(Xtr, ytr)
lr = LogisticRegression(max_iter=1000).fit(Xtr, ytr)
explainer = shap.TreeExplainer(rf)
sv3 = explainer.shap_values(Xte.head(100))  # (100, 12, 2)
expl = explainer(Xte.head(100))  # Explanation
print(f"shap {shap.__version__} | shap_values shape {sv3.shape} | Explanation shape {expl.shape}\n")


def show(title, fn):
    print("─" * 78)
    print(f"### {title}")
    try:
        out = fn()
        rep = out if isinstance(out, str) else ("None" if out is None else f"{type(out).__name__} {getattr(out, 'shape', '')}")
        print(f"⚠ 沒有噴錯（回傳 {rep}）——這種才可怕：錯了但沒人告訴你")
    except Exception as e:  # noqa: BLE001 — 這支腳本就是要看原文
        print(f"{type(e).__name__}: {e}")
    print()


# 1. 三維 shap_values 忘了取類別 1 → 直接丟給 summary_plot
import matplotlib.pyplot as plt


def _summary_3d():
    plt.figure()
    shap.summary_plot(sv3, Xte.head(100), show=False)
    fig = plt.gcf()
    fig.savefig("/tmp/shap_err_summary_3d.png", dpi=100, bbox_inches="tight")
    xlabel = fig.axes[-1].get_xlabel() or fig.texts[-1].get_text() if fig.texts else fig.axes[-1].get_xlabel()
    ylabels = [t.get_text() for t in fig.axes[0].get_yticklabels()]
    plt.close("all")
    return (
        f"畫出來了，但畫的是另一種圖：{len(fig.axes)} 個子圖、x 軸標題是 {xlabel!r}、"
        f"y 軸只剩 {ylabels}（12 個特徵的 summary 不見了）"
    )


show("1. summary_plot 吃到三維 shap_values（忘了 [:, :, 1]）", _summary_3d)

# 2. TreeExplainer 餵非樹模型
show("2. TreeExplainer(LogisticRegression)", lambda: shap.TreeExplainer(lr))

# 3. KernelExplainer 沒給 background data
show(
    "3. KernelExplainer 少了 background（只給模型）",
    lambda: shap.KernelExplainer(lambda d: rf.predict_proba(d)[:, 1]),
)

# 4. waterfall 餵整批而不是單筆
show("4. waterfall 餵整批 Explanation", lambda: shap.plots.waterfall(expl[:, :, 1], show=False))

# 4b. waterfall 餵單筆但沒選類別（12×2）
show("4b. waterfall 餵單筆但沒選類別 expl[0]", lambda: shap.plots.waterfall(expl[0], show=False))

# 5. 欄名與訓練時不一致
renamed = Xte.head(5).rename(columns={"f2": "is_vip"})
show("5a. 欄名改掉後直接算 SHAP", lambda: explainer.shap_values(renamed))
show("5b. 欄名改掉後餵模型預測", lambda: rf.predict_proba(renamed))

# 5c. 欄序被打亂（欄名還在，但順序不同）
shuffled = Xte.head(5)[list(reversed(COLS))]
show("5c. 欄序反過來（欄名都在，只是順序不同）", lambda: rf.predict_proba(shuffled))
show("5c-2. 同樣的欄序反轉，但丟給 shap_values", lambda: explainer.shap_values(shuffled))

# 6. numpy 陣列沒有欄名 → 圖上只有 Feature 0、Feature 1
print("─" * 78)
print("### 6. 用 numpy 陣列算 SHAP：不報錯，但圖上沒有欄名")
v_np = shap.TreeExplainer(rf).shap_values(Xte.head(50).to_numpy())[:, :, 1]
e_np = shap.TreeExplainer(rf)(Xte.head(50).to_numpy())
print(f"shap_values 照樣算出來 {v_np.shape}；Explanation.feature_names = {e_np.feature_names}")
