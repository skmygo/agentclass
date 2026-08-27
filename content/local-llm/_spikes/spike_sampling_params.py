# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy"]
# ///
"""Spike: 取樣參數 —— temperature / top_p / frequency & presence penalty 真算。

範例沿用 pptx：「今天天氣真___」候選字 好/不錯/熱/冷/量子。
"""
import numpy as np

TOKENS = ["好", "不錯", "熱", "冷", "量子"]
# 設一組 logits，softmax(T=1) 後接近 pptx 範例機率 0.45/0.25/0.15/0.10/0.005
logits = np.log(np.array([0.45, 0.25, 0.15, 0.10, 0.005]))


def softmax_t(lg, t):
    z = lg / t
    z = z - z.max()
    p = np.exp(z)
    return p / p.sum()


for t in (0.2, 1.0, 1.2, 2.0):
    p = softmax_t(logits, t)
    print(f"T={t}: " + "  ".join(f"{tok}={pi:.3f}" for tok, pi in zip(TOKENS, p)))

p_low = softmax_t(logits, 0.2)
p_high = softmax_t(logits, 2.0)
assert p_low[0] > 0.9, "T 低時第一名應近乎壟斷"
assert p_high[0] < 0.5, "T 高時分佈應攤平"

# top_p = 0.9 核採樣：照機率排序累積，超過 p 截斷
p1 = softmax_t(logits, 1.0)
order = np.argsort(p1)[::-1]
cum = np.cumsum(p1[order])
keep = cum < 0.9
keep[np.argmax(cum >= 0.9)] = True  # 含第一個跨過門檻的
kept = [TOKENS[i] for i in order[keep]]
print(f"top_p=0.9 保留: {kept}（量子被丟棄）")
assert "量子" not in kept and "好" in kept

# penalty: logit' = logit - freq_pen*count - pres_pen*seen
counts = np.array([3, 0, 0, 0, 0])  # 「好」已出現 3 次
freq_pen, pres_pen = 0.5, 0.5
lg2 = logits - freq_pen * counts - pres_pen * (counts > 0)
p2 = softmax_t(lg2, 1.0)
print("penalty 後: " + "  ".join(f"{tok}={pi:.3f}" for tok, pi in zip(TOKENS, p2)))
assert p2[0] < p1[0], "被罰的字機率應下降"
print("OK")
