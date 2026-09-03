# 第 00 課（純瀏覽器 app）spike：模型漂移與再訓練模擬——訓練一次 vs 定期重訓 vs 監控觸發重訓
# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy", "scikit-learn"]
# ///
import time
import numpy as np
from sklearn.linear_model import LogisticRegression

MONTHS = 24
N = 300
D = 6

def month_data(m, rng, drift_rate=0.12, shift=0.0):
    # 概念漂移：決定邊界的權重向量隨月份旋轉；covariate shift：特徵均值漂移
    theta = drift_rate * m
    w = np.array([np.cos(theta), np.sin(theta), 0.5, -0.5, 0.3, 0.0])
    X = rng.normal(0, 1, (N, D)) + shift * m / MONTHS
    logits = X @ w + 0.3 * rng.normal(0, 1, N)
    y = (logits > 0).astype(int)
    return X, y

def simulate(strategy, k=3, thr=0.85, drift_rate=0.12, seed=0):
    rng = np.random.default_rng(seed)
    data = [month_data(m, rng, drift_rate) for m in range(MONTHS)]
    model = LogisticRegression().fit(*data[0])
    accs, retrains = [], []
    for m in range(1, MONTHS):
        X, y = data[m]
        acc = model.score(X, y)
        accs.append(acc)
        if strategy == "periodic" and m % k == 0:
            model = LogisticRegression().fit(X, y); retrains.append(m)
        elif strategy == "monitor" and acc < thr:
            model = LogisticRegression().fit(X, y); retrains.append(m)
    return np.array(accs), retrains

t0 = time.time()
for s in ["none", "periodic", "monitor"]:
    a, r = simulate(s)
    print(f"{s:9s} mean acc {a.mean():.3f} | min {a.min():.3f} | last {a[-1]:.3f} | retrains {r}")
print("per-month accs (none):", np.round(simulate("none")[0], 2).tolist())
for dr in [0.0, 0.05, 0.12, 0.25]:
    a, _ = simulate("none", drift_rate=dr)
    print(f"drift_rate {dr}: none mean {a.mean():.3f} last {a[-1]:.3f}")
for k in [1, 3, 6]:
    a, r = simulate("periodic", k=k)
    print(f"periodic k={k}: mean {a.mean():.3f} retrains {len(r)}")
for thr in [0.8, 0.9, 0.95]:
    a, r = simulate("monitor", thr=thr)
    print(f"monitor thr={thr}: mean {a.mean():.3f} retrains {len(r)} at {r}")
print("elapsed", round(time.time() - t0, 2), "s")
