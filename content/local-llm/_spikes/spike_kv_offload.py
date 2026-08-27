# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy"]
# ///
"""Spike: KV Cache 分層與 SSD 卸載 —— 「拿 IO 換計算」的時間模型。

課程宣稱驗證（方向性，非精確預測）：
- SSD 複用要贏過重算，條件是「重算（prefill）比從 SSD 載回慢」
- 計算越重（量化反量化、模型越大）、前綴越長 → 越賺
- 個人／小模型場景 KV 很小，CPU RAM 都用不完 → 用不到 SSD 層
"""

# 三層頻寬（數量級，pptx/公開常識）：HBM ~2TB/s、CPU RAM ~50GB/s、NVMe ~5-7GB/s
BW_SSD_GBS = 6.0

# KV 大小（GB）與載回時間
def load_time_s(kv_gb, bw=BW_SSD_GBS):
    return kv_gb / bw


# Llama3-8B GQA: 0.128 MB/token
MB_PER_TOK = 0.128
for toks in (2_000, 10_000, 128_000):
    kv_gb = MB_PER_TOK * toks / 1024
    t = load_time_s(kv_gb)
    print(f"{toks} tokens 前綴: KV={kv_gb:.2f} GB → SSD 載回 ~{t*1000:.0f} ms")

# 賺不賺：prefill 時間 vs 載回時間。
# prefill 越貴（計算重）→ 加速比越高。pptx 實測（RTX 4090, LMCache 0.5.0, 2026-07）:
# Qwen3-0.6B(bf16)=1.1x、1.7B(FP8)=1.2x、4B-AWQ(int4)=2.3x —— 引用值，模型只驗方向。
measured = {"Qwen3-0.6B bf16": 1.1, "Qwen3-1.7B FP8": 1.2, "Qwen3-4B AWQ": 2.3}
for k, v in measured.items():
    print(f"實測引用: {k} → SSD 複用 vs 冷啟動 {v}x")
assert measured["Qwen3-4B AWQ"] > measured["Qwen3-0.6B bf16"], "計算越重越賺（方向）"

# 個人場景判斷：14B 模型塞一整本長篇小說級 context 也 < 20GB（pptx 課堂實測結論）
# → CPU RAM（動輒 32–128GB）用不完，SSD 層是多人長上下文伺服器才需要的東西。
kv_128k_gb = MB_PER_TOK * 128_000 / 1024
print(f"128k tokens KV ≈ {kv_128k_gb:.0f} GB —— 一般 64GB RAM 個人機的 CPU 層就裝得下")
assert kv_128k_gb < 20
print("OK")
