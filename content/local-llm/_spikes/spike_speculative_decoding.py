# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy"]
# ///
"""Spike: 投機解碼 —— 先猜後驗的加速模型（理論 + Monte Carlo）。

課程宣稱驗證：
- 每輪期望產出 = E[連續猜對數] + 1（驗證那步大模型自己送一個字，最壞也 +1）
- τ=4（每輪平均 4 個 token）→ 大模型前向次數 1/4 → 約 3.6x（pptx 說法，含 overhead）
- 接受率越高、猜越多步越賺；高併發時算力已滿載，反而擠佔 batch
"""
import numpy as np

rng = np.random.default_rng(7)


def expected_tokens(alpha, k):
    """每輪期望 token 數：前綴連續接受 + 1 個驗證/修正字（理論值）"""
    return sum(alpha**i for i in range(1, k + 1)) + 1


def simulate(alpha, k, n_rounds=200_000):
    draws = rng.random((n_rounds, k)) < alpha
    # 連續接受長度：第一個 False 之前的 True 數
    first_rej = np.where(draws.all(axis=1), k, np.argmin(draws, axis=1))
    return (first_rej + 1).mean()


for alpha in (0.6, 0.8, 0.9):
    for k in (3, 5):
        theo = expected_tokens(alpha, k)
        sim = simulate(alpha, k)
        assert abs(theo - sim) < 0.02, (alpha, k, theo, sim)
        print(f"α={alpha}, K={k}: 每輪期望 {theo:.2f} tokens（模擬 {sim:.2f}）→ 大模型前向省 {theo:.1f}x")

# 最壞情況：第一格就被拒仍拿到 1 個正確 token（等同不加速，不會更差）
assert expected_tokens(0.0, 5) == 1.0

# 草稿也有成本：speedup ≈ E / (1 + K*c)，c = 草稿/大模型單步成本比
def speedup(alpha, k, c):
    return expected_tokens(alpha, k) / (1 + k * c)


print(f"α=0.8, K=5, 草稿成本 5%: 端到端 ≈ {speedup(0.8, 5, 0.05):.1f}x")
print(f"α=0.8, K=5, 草稿成本 30%（draft model 太大）: ≈ {speedup(0.8, 5, 0.30):.1f}x")
assert speedup(0.8, 5, 0.05) > speedup(0.8, 5, 0.30)

# τ=4 → 前向 1/4，pptx 稱實際 ~3.6x（有 overhead，理論上限 4x）
print("τ=4 → 理論上限 4x、pptx 稱實測約 3.6x（overhead 吃掉一點）")
print("OK")
