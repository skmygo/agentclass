# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy"]
# ///
"""genai-training 課的定軌 spike。

四段：
  A. Llama-3-8B 參數帳（真實架構規格逐層算）＋ 預訓練 FLOPs 粗估（6ND）
  B. LoRA 參數帳：r=16 全七投影 vs 全參數（微調課的核心數字）
  C. 蒸餾：溫度軟標籤（dark knowledge 用真 softmax 算給你看）
  D. GRPO：群組相對優勢（DeepSeek-R1 論文公式的最小可跑版）

跑法：uv run --script content/genai-intro/_spikes/spike_genai_training.py
"""

import numpy as np

# ── A. Llama-3-8B 參數帳（config.json 的真實規格）────────────────────
print("== A. Llama-3-8B params ==")
VOCAB, HID, LAYERS, INTER = 128256, 4096, 32, 14336
N_HEADS, N_KV, HEAD_DIM = 32, 8, 128

emb = VOCAB * HID
attn = HID * (N_HEADS * HEAD_DIM) + 2 * HID * (N_KV * HEAD_DIM) + (N_HEADS * HEAD_DIM) * HID
mlp = 2 * HID * INTER + INTER * HID  # gate, up, down
norms = 2 * HID
per_layer = attn + mlp + norms
lm_head = VOCAB * HID  # Llama-3-8B 不綁定（untied）
total = emb + LAYERS * per_layer + HID + lm_head
print(f"embedding {emb/1e6:.0f}M  per-layer {per_layer/1e6:.1f}M  total {total/1e9:.2f}B")
assert abs(total - 8.03e9) / 8.03e9 < 0.01, "應接近官方 8.03B"

# 預訓練 FLOPs 粗估（6·N·D；Llama 3 公開訓練量 15T tokens）
D = 15e12
flops = 6 * total * D
print(f"pretrain FLOPs ≈ 6·N·D = {flops:.2e}")
# 官方公開數字：Llama 3 8B 用了 1.3M GPU-hours（H100）——文案引用這個公開值，不自己推

# ── B. LoRA 參數帳 ───────────────────────────────────────────────────
print("\n== B. LoRA params ==")
R = 16
proj_shapes = {  # (d_in, d_out)，七個投影
    "q_proj": (HID, N_HEADS * HEAD_DIM),
    "k_proj": (HID, N_KV * HEAD_DIM),
    "v_proj": (HID, N_KV * HEAD_DIM),
    "o_proj": (N_HEADS * HEAD_DIM, HID),
    "gate_proj": (HID, INTER),
    "up_proj": (HID, INTER),
    "down_proj": (INTER, HID),
}
lora = sum(R * (di + do) for di, do in proj_shapes.values()) * LAYERS
print(f"LoRA r={R} 全七投影: {lora/1e6:.1f}M  佔全參數 {lora/total*100:.2f}%")
assert lora / total < 0.01, "LoRA 參數應遠小於 1%"

lora_qv8 = sum(8 * (di + do) for k, (di, do) in proj_shapes.items() if k in ("q_proj", "v_proj")) * LAYERS
print(f"LoRA r=8 只掛 q,v: {lora_qv8/1e6:.1f}M  佔 {lora_qv8/total*100:.3f}%")

# 記憶體帳（訓練要存什麼）：全參數 AdamW vs LoRA
# 全參數 bf16 權重 2B/參數 + 梯度 2 + Adam 狀態 fp32 8 → ~12 bytes/參數（不含 activation）
full_gb = total * 12 / 1024**3
lora_gb = (total * 2 + lora * 12) / 1024**3  # 底模凍結只放權重，LoRA 才有梯度與優化器
print(f"全參數微調至少 ~{full_gb:.0f} GB；LoRA ~{lora_gb:.0f} GB（未含 activation；量化底模可再壓）")
assert full_gb > 85 and lora_gb < 20

# ── C. 蒸餾：溫度軟標籤 ──────────────────────────────────────────────
print("\n== C. distillation soft labels ==")


def softmax(z, t=1.0):
    z = np.asarray(z, float) / t
    e = np.exp(z - z.max())
    return e / e.sum()


CLASSES = ["貓", "狗", "老虎", "汽車"]
teacher_logits = [5.0, 2.6, 1.8, -2.0]  # 老師模型看一張貓圖的 logits（教學示例值）
for t in (1.0, 4.0):
    p = softmax(teacher_logits, t)
    print(f"T={t}: " + "  ".join(f"{c}={pi:.3f}" for c, pi in zip(CLASSES, p)))
p1, p4 = softmax(teacher_logits, 1.0), softmax(teacher_logits, 4.0)
assert p1[0] > 0.85, "T=1 幾乎只剩正解"
assert p4[1] / p4[3] > 2, "T=4 仍保留「狗比汽車像貓」的暗知識"
assert p4[0] < p1[0], "溫度拉高，分布變平"

# ── D. GRPO：群組相對優勢 ────────────────────────────────────────────
print("\n== D. GRPO group advantage ==")
rng = np.random.default_rng(7)
rewards = np.array([1.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0])  # 同一題抽 8 個答案的對錯
adv = (rewards - rewards.mean()) / (rewards.std() + 1e-8)
for i, (r, a) in enumerate(zip(rewards, adv)):
    print(f"  答案{i+1}: reward={r:.0f}  advantage={a:+.2f}")
assert abs(adv.mean()) < 1e-6, "群組優勢均值為 0"
assert adv[0] > 0 > adv[1], "答對的被加強、答錯的被壓低"
print("（GRPO 不用 value model：優勢＝組內標準化，這就是它比 PPO 省一半記憶體的原因）")

print("\nSPIKE OK: genai-training")
