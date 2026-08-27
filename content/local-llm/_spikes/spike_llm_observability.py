# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy"]
# ///
"""Spike: 監控告警 —— `for:` 濾抖動的效果模擬（教學模擬，非實測數據）。

課程宣稱驗證：
- 沒有 for:（持續時間條件）：VRAM 抖一下就告警 → 告警疲乏
- 有 for: 5 分鐘：只有真正持續的低水位才告警
"""
import numpy as np

rng = np.random.default_rng(3)

# 模擬 24h、每 15s 一點的「剩餘 VRAM」時序（GB）
n = 24 * 60 * 4
vram = np.full(n, 4.0) + rng.normal(0, 0.15, n)
# 三次短暫抖動（1–2 分鐘掉到 1.2GB）
for start in (1000, 3000, 4200):
    vram[start:start + 6] = 1.2
# 一次真事件：持續 30 分鐘低於門檻
vram[5000:5000 + 120] = 1.1

TH = 1.5
below = vram < TH

def count_firings(below, for_points):
    """連續低於門檻達 for_points 個取樣點才算一次告警"""
    firings, run, fired = 0, 0, False
    for b in below:
        run = run + 1 if b else 0
        if not b:
            fired = False
        if run >= for_points and not fired:
            firings += 1
            fired = True
    return firings


no_for = count_firings(below, 1)
with_for = count_firings(below, 5 * 4)  # 5 分鐘 = 20 點
print(f"門檻 <{TH}GB、無 for: → {no_for} 次告警（含 3 次抖動誤報）")
print(f"門檻 <{TH}GB、for: 5m → {with_for} 次告警（只剩真事件）")
assert no_for >= 4 and with_for == 1

# 預留制 vs 動態制：看「剩多少」不是「用多少」
total = 24.0
vllm_used = 8.2        # 預留制：啟動即鎖定，之後不長
dyn_used = np.array([6.0, 9.5, 14.2])  # 動態制：長文本峰值突然要更多
print(f"預留制服務: 固定佔 {vllm_used}GB，跑起來就穩")
print(f"動態制服務: 峰值 {dyn_used.max()}GB —— 判讀規則：盯剩餘 {total - vllm_used - dyn_used.max():.1f}GB 是否夠峰值增量")
print("OK")
