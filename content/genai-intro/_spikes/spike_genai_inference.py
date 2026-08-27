# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy"]
# ///
"""genai-inference 課的定軌 spike。

五段：
  A. KV cache 記憶體帳（與 local-llm 系列同一條公式交叉驗證）
  B. 量化：absmax int8/int4 真量化誤差 ＋ 離群值 → group-wise 修復
  C. 模型檔大小帳：fp16 vs int8 vs int4
  D. 投機解碼：接受率 → 期望輸出長度（封閉式 vs 蒙地卡羅互驗）
  E. Continuous batching：靜態 vs 連續批次的槽位利用率模擬
  F. MoE 參數帳：Mixtral 8x7B 總參數 vs 啟用參數（對公開數字）

跑法：uv run --script content/genai-intro/_spikes/spike_genai_inference.py
"""

import numpy as np

# ── A. KV cache ─────────────────────────────────────────────────────
print("== A. KV cache ==")
kv_per_tok = 2 * 32 * 8 * 128 * 2  # 2(K,V)×層×KV head×head_dim×fp16
print(f"8B 級 GQA fp16: {kv_per_tok/1024:.0f} KB/token")
assert kv_per_tok == 131072
for ctx in (8192, 131072):
    print(f"  {ctx:>6} tokens -> {ctx*kv_per_tok/1024**3:.1f} GB")

# ── B. 量化誤差 ──────────────────────────────────────────────────────
print("\n== B. quantization ==")
rng = np.random.default_rng(0)
w = rng.normal(0, 0.02, 4096).astype(np.float32)


def absmax_quant(x, bits, group=None):
    if group:
        xs = x.reshape(-1, group)
        qmax = 2 ** (bits - 1) - 1
        s = np.abs(xs).max(axis=1, keepdims=True) / qmax
        q = np.round(xs / s)
        return (q * s).ravel()
    qmax = 2 ** (bits - 1) - 1
    s = np.abs(x).max() / qmax
    return np.round(x / s) * s


for bits in (8, 4):
    err = np.abs(absmax_quant(w, bits) - w).mean()
    print(f"int{bits} 全張量: 平均誤差 {err:.6f}（權重尺度 0.02）")

w_out = w.copy()
w_out[100] = 0.5  # 一個離群值（LLM 權重真的有）
e_global = np.abs(absmax_quant(w_out, 4) - w_out).mean()
e_group = np.abs(absmax_quant(w_out, 4, group=128) - w_out).mean()
print(f"int4 有離群值: 全張量誤差 {e_global:.6f}  vs 128/group 誤差 {e_group:.6f}")
assert e_group < e_global / 3, "group-wise 應大幅救回離群值災難"
ratio = e_global / np.abs(absmax_quant(w, 4) - w).mean()
print(f"（一個離群值把 int4 全張量誤差放大 {ratio:.0f} 倍——GPTQ/AWQ/GGUF 都用分組量化的原因）")

# ── C. 模型檔大小 ────────────────────────────────────────────────────
print("\n== C. model size ==")
N = 8.03e9
for name, bytes_per in (("fp16", 2), ("int8", 1), ("int4", 0.5)):
    print(f"  8B {name}: {N*bytes_per/1024**3:.1f} GB")
# int4 實檔會多一點（分組的 scale/zero-point 也要存），文案寫「約 4.5–5 GB」級

# ── D. 投機解碼 ──────────────────────────────────────────────────────
print("\n== D. speculative decoding ==")
K = 4  # 小模型一次猜 4 個


def expected_len(alpha, k):
    # 每個草稿 token 以 α 獨立接受，全收再送一個大模型 token：封閉式期望
    return (1 - alpha ** (k + 1)) / (1 - alpha)


for alpha in (0.6, 0.8, 0.9):
    closed = expected_len(alpha, K)
    acc = rng.random((200_000, K)) < alpha
    stop = np.argmin(acc, axis=1)  # 第一個 False 的位置
    n_acc = np.where(acc.all(axis=1), K, stop)
    mc = (n_acc + 1).mean()  # +1：驗證那步大模型自己也產一個 token
    print(f"  α={alpha}: 每輪期望產出 {closed:.2f} tokens（蒙地卡羅 {mc:.2f}）")
    assert abs(closed - mc) < 0.02
print("（教學模型：α 視為每 token 獨立；真實接受率隨位置與內容波動）")

# ── E. Continuous batching ──────────────────────────────────────────
print("\n== E. continuous batching ==")
SLOTS, STEPS = 8, 400
lengths = rng.integers(20, 200, 1000)  # 每個請求要輸出的 token 數


def run_sim(continuous: bool):
    q = list(lengths)
    slot = [0] * SLOTS  # 剩餘 token 數；0=空
    busy = total_steps = 0
    t = 0
    while t < STEPS:
        if continuous or all(s == 0 for s in slot):
            for i in range(SLOTS):
                if slot[i] == 0 and q:
                    slot[i] = int(q.pop(0))
        busy += sum(1 for s in slot if s > 0)
        total_steps += SLOTS
        slot = [max(0, s - 1) for s in slot]
        t += 1
    return busy / total_steps


for seed_shift in range(3):
    rng2 = np.random.default_rng(seed_shift)
    lengths = rng2.integers(20, 200, 1000)
    u_static, u_cont = run_sim(False), run_sim(True)
    print(f"  seed{seed_shift}: 靜態批次利用率 {u_static:.0%}  連續批次 {u_cont:.0%}")
    assert u_cont > u_static + 0.2

# ── F. MoE 參數帳（Mixtral 8x7B）────────────────────────────────────
print("\n== F. MoE (Mixtral 8x7B) ==")
V2, H2, L2, I2, NKV2 = 32000, 4096, 32, 14336, 8
attn2 = H2 * H2 + 2 * H2 * (NKV2 * 128) + H2 * H2
expert = 3 * H2 * I2
router = H2 * 8
per_layer2 = attn2 + 8 * expert + router + 2 * H2
total2 = V2 * H2 + L2 * per_layer2 + H2 + V2 * H2
active2 = V2 * H2 + L2 * (attn2 + 2 * expert + router + 2 * H2) + H2 + V2 * H2
print(f"總參數 {total2/1e9:.1f}B  每 token 啟用 {active2/1e9:.1f}B")
assert abs(total2 - 46.7e9) / 46.7e9 < 0.01, "對齊公開數字 46.7B"
assert abs(active2 - 12.9e9) / 12.9e9 < 0.02, "對齊公開數字 12.9B"

print("\nSPIKE OK: genai-inference")
