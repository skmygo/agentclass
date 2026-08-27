# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy"]
# ///
"""Spike: slot 固定分配 vs PagedAttention 分頁 —— 記憶體利用率模擬。

課程宣稱驗證：
- slot 制：請求短時整格浪費，利用率可能很低
- paged 制：以小 block 分配，利用率接近實際用量
"""
import numpy as np

rng = np.random.default_rng(42)

CTX = 4096          # 每 slot 容量（tokens）
N_SLOTS = 3
BLOCK = 16          # PagedAttention block 大小（tokens）

# 模擬一批請求的實際 token 長度（多數請求遠短於 context 上限）
reqs = rng.integers(50, 2000, size=N_SLOTS)
print("請求實際長度:", reqs.tolist())

# slot 制：每請求佔滿一格 CTX
slot_alloc = N_SLOTS * CTX
slot_used = int(reqs.sum())
slot_util = slot_used / slot_alloc
print(f"slot 制:   配置 {slot_alloc} tokens、實用 {slot_used} → 利用率 {slot_util:.1%}")

# paged 制：按 block 進位分配
paged_alloc = int(sum(int(np.ceil(r / BLOCK)) * BLOCK for r in reqs))
paged_util = slot_used / paged_alloc
print(f"paged 制:  配置 {paged_alloc} tokens、實用 {slot_used} → 利用率 {paged_util:.1%}")

assert slot_util < 0.35, "slot 制利用率應顯著偏低"
assert paged_util > 0.95, "paged 制利用率應接近 100%"

# 極端例：pptx 說「一個請求只用 50 tokens、slot 佔 4096 → 利用率約 10%」
one = 50 / 4096
print(f"單請求 50/4096 → slot 利用率 {one:.1%}（pptx 說法：可能只有 ~1–10% 量級）")
print("OK")
