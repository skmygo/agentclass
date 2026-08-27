# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Spike: Prompt Caching 計費 —— 重現 pptx「連續聊 3 輪」全部數字。

費率（Claude Fable 5，每 MTok）：Base $10 / Write(5m) $12.5 / Hit $1 / Output $50
情境：系統提示 10K、每輪問題 1K、每輪回答 2K
"""
BASE, WRITE, HIT, OUT = 10.0, 12.5, 1.0, 50.0
M = 1_000_000
SYS, Q, A = 10_000, 1_000, 2_000


def cached_rounds(n):
    hist = 0  # 已快取的對話歷史（前綴）
    rounds = []
    for i in range(1, n + 1):
        write = (SYS + Q) if i == 1 else Q   # 第一次出現的新內容
        hit = hist                            # 歷史前綴全部命中
        cost = write / M * WRITE + hit / M * HIT + A / M * OUT
        rounds.append((hit, write, cost))
        hist += write + A                     # 這輪的新內容與回答併入歷史
    return rounds


rounds = cached_rounds(3)
for i, (hit, write, cost) in enumerate(rounds, 1):
    print(f"第 {i} 輪: 命中 {hit//1000}K、寫入 {write//1000}K → ${cost:.3f}")
total_cached = sum(c for _, _, c in rounds)
print(f"3 輪總計（用快取）: ${total_cached:.3f}")

# 不用快取：每輪全部歷史都是 base input
def nocache_rounds(n):
    total = 0
    hist = 0
    for i in range(1, n + 1):
        inp = SYS + Q if i == 1 else hist + Q
        total += inp / M * BASE + A / M * OUT
        hist = (SYS + Q + A) if i == 1 else hist + Q + A
    return total


total_plain = nocache_rounds(3)
print(f"3 輪總計（不用快取）: ${total_plain:.3f}")
save = 1 - total_cached / total_plain
print(f"省 {save:.0%}")

# 驗 pptx 數字
assert abs(rounds[0][2] - 0.238) < 0.001, rounds[0]
assert abs(rounds[1][2] - 0.126) < 0.001, rounds[1]
assert abs(rounds[2][2] - 0.129) < 0.001, rounds[2]
assert abs(total_cached - 0.492) < 0.001
assert abs(total_plain - 0.720) < 0.001
assert abs(save - 0.32) < 0.01
print("OK — pptx 全部數字重現")
