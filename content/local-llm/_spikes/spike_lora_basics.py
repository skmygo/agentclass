# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy"]
# ///
"""Spike: LoRA —— 參數量 128x、α/r 縮放力道、B 零初始化、低秩近似直覺。"""
import numpy as np

rng = np.random.default_rng(1)

# --- 參數量：d=4096, r=16 → 縮小 128 倍（pptx 數字）---
d, r = 4096, 16
full = d * d
lora = 2 * d * r
print(f"Full: {full:,} 參數；LoRA(r={r}): {lora:,} 參數 → 縮小 {full // lora} 倍")
assert full == 16_777_216 and lora == 131_072 and full // lora == 128

# --- α/r 縮放：更新力道 ∝ α/r（pptx: alpha 越大越強、rank 越小越強）---
def update_norm(alpha, rank, d=256):
    B = rng.normal(0, 0.02, (d, rank))
    A = rng.normal(0, 0.02, (rank, d))
    return (alpha / rank) * np.linalg.norm(B @ A)


base = update_norm(16, 16)
print(f"‖ΔW‖ α=16,r=16: {base:.4f}")
print(f"‖ΔW‖ α=32,r=16: {update_norm(32, 16):.4f}（α 加倍 → 力道加倍）")
n_r4 = update_norm(16, 4)
print(f"‖ΔW‖ α=16,r=4:  {n_r4:.4f}（r 變小 → α/r 變大 → 力道變強）")
assert update_norm(32, 16) > base * 1.5

# --- B 初始化為零 → 第一步 ΔW=0，行為與原模型一致 ---
B0 = np.zeros((d, r)); A0 = rng.normal(0, 0.02, (r, d))
assert np.allclose(B0 @ A0, 0)
print("B 零初始化 → 掛上 adapter 當下 ΔW=0，模型行為不變 ✓")

# --- 低秩近似直覺：一個結構化矩陣用 r 個奇異值就能還原大半 ---
M = np.outer(np.sin(np.linspace(0, 3, 64)), np.cos(np.linspace(0, 2, 64)))
M += 0.1 * rng.normal(size=M.shape)
U, S, Vt = np.linalg.svd(M)
for rr in (1, 4, 16):
    Mr = (U[:, :rr] * S[:rr]) @ Vt[:rr]
    err = np.linalg.norm(M - Mr) / np.linalg.norm(M)
    print(f"r={rr}: 相對誤差 {err:.1%}")

# --- SFT vs DPO 資料格式（概念展示用）---
sft_row = {"prompt": "什麼是 DPO?", "response": "DPO 是一種偏好最佳化方法…"}
dpo_row = {"prompt": "寫一句問候", "chosen": "早安！祝你有美好的一天", "rejected": "嗯。"}
print("SFT 一問一答:", list(sft_row))
print("DPO 偏好三元組:", list(dpo_row))
print("OK")
