# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy"]
# ///
"""Spike: KV Cache 原理 —— toy attention、重算浪費、記憶體估算。

課程宣稱驗證：
- 無 cache：每步重算前面所有 K/V → 總計算量隨長度平方成長
- 有 cache：每步只算新字 → 線性
- Llama 3 8B (GQA) 每 token KV ≈ 0.128 MB → 各場景需求表（pptx 數字）
"""
import numpy as np

rng = np.random.default_rng(0)

# --- toy attention（單頭、d=8）驗證 Q·K → 權重 → 加權 V 流程 ---
d = 8
n = 4
X = rng.normal(size=(n, d))
Wq, Wk, Wv = (rng.normal(size=(d, d)) for _ in range(3))
Q, K, V = X @ Wq, X @ Wk, X @ Wv
att = Q[-1] @ K.T / np.sqrt(d)          # 新字的 Q 對所有 K
w = np.exp(att - att.max()); w /= w.sum()
out = w @ V
print(f"attention 權重（新字看 4 個位置）: {np.round(w, 3)}，輸出 shape {out.shape}")

# --- 重算 vs 快取的計算量（以「算多少個 token 的 K/V」計）---
def kv_computed(n_tokens, cached):
    total = 0
    for step in range(1, n_tokens + 1):
        total += 1 if cached else step   # 無快取：第 step 步重算 step 個
    return total

for n_tok in (10, 100, 1000):
    a, b = kv_computed(n_tok, False), kv_computed(n_tok, True)
    print(f"{n_tok} tokens: 無快取算 {a} 次 K/V、有快取 {b} 次 → 省 {a/b:.0f}x")
assert kv_computed(1000, False) == 1000 * 1001 // 2

# --- Llama 3 8B GQA 每 token KV 記憶體 ---
layers, kv_heads, head_dim, dtype_bytes = 32, 8, 128, 2
per_tok = layers * kv_heads * head_dim * 2 * dtype_bytes  # K+V
kib = per_tok / 1024
print(f"每 token KV = {per_tok:,} bytes = {kib:.0f} KiB ≈ {per_tok/1e6:.2f} MB（原教材寫 0.128 MB，同一量級的概數）")
assert per_tok == 131_072

# --- 場景需求表（結構同原教材 slide 137，數字用精確 bytes 重算）---
scenarios = [("當前測試", 2_000, 1), ("短文本 RAG", 8_000, 1), ("論文分析", 32_000, 1),
             ("多用戶並發", 8_000, 10), ("整本書籍", 128_000, 1), ("超大 Context", 1_000_000, 1)]
for name, toks, conc in scenarios:
    gb = per_tok * toks * conc / 1e9
    print(f"{name}: {toks}×{conc} → {gb:.2f} GB")
# 方向驗證：>10GB 可用 VRAM 的只有多用戶並發、128k+、1M 場景
assert per_tok * 2_000 / 1e9 < 1 and per_tok * 8_000 * 10 / 1e9 > 10
assert per_tok * 1_000_000 / 1e9 > 100
print("OK")
