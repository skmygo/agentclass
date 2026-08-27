# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy", "tiktoken", "openai"]
# ///
"""genai-tokens 課的定軌 spike：左頁與 notebook 引用的每個數字都在這裡驗證。

四段：
  A. tiktoken（o200k_base，GPT-4o 系列的真 tokenizer）：中英文 token 數對照、切片展示
  B. 迷你 BPE：純 Python 實作（瀏覽器 demo 的同一份演算法）
  C. 真實 embedding（jina-embed 1024 維，OpenAI 相容端點）：int8 量化後 PCA / cosine 驗證
  D. 自迴歸：字元 bigram LM（瀏覽器 demo 的同一份演算法）

C 段需要 env：RELAY_URL、API_KEY（OpenAI 相容端點）；沒設就跳過 C 段其餘照跑。
跑法：uv run --script content/genai-intro/_spikes/spike_genai_tokens.py
"""

import base64
import os
import sys

import numpy as np

# ── A. tiktoken：真 tokenizer 的真數字 ─────────────────────────────
import tiktoken

enc = tiktoken.get_encoding("o200k_base")  # GPT-4o / o 系列用的編碼

SAMPLES = {
    "en": "The quick brown fox jumps over the lazy dog.",
    "zh": "敏捷的棕色狐狸跳過了那隻懶狗。",
    "en_word": "internationalization",
    "zh_term": "生成式人工智慧",
}
print("== A. tiktoken (o200k_base) ==")
for k, s in SAMPLES.items():
    ids = enc.encode(s)
    pieces = [enc.decode([i]) for i in ids]
    print(f"{k}: {len(s)} chars -> {len(ids)} tokens")
    print("   pieces:", pieces)

en_ids = enc.encode(SAMPLES["en"])
zh_ids = enc.encode(SAMPLES["zh"])
print(f"chars/token  en: {len(SAMPLES['en'])/len(en_ids):.2f}  zh: {len(SAMPLES['zh'])/len(zh_ids):.2f}")
assert len(zh_ids) > len(en_ids) * 0.8, "中文 token 數應與英文同量級或更多"

# ── B. 迷你 BPE（瀏覽器 demo 同款演算法）────────────────────────────
print("\n== B. mini BPE ==")
BPE_CORPUS = "low low low low low lower lower newest newest newest newest newest newest widest widest widest".split()


def bpe_train(words: list[str], n_merges: int):
    """經典 BPE：word -> tuple of symbols（含詞尾 </w>），統計相鄰 pair 頻率、合併最高頻。"""
    vocab: dict[tuple, int] = {}
    for w in words:
        key = tuple(w) + ("</w>",)
        vocab[key] = vocab.get(key, 0) + 1
    merges = []
    for _ in range(n_merges):
        pairs: dict[tuple, int] = {}
        for sym, freq in vocab.items():
            for a, b in zip(sym, sym[1:]):
                pairs[(a, b)] = pairs.get((a, b), 0) + freq
        if not pairs:
            break
        best = max(pairs, key=lambda p: (pairs[p], p))
        merges.append((best, pairs[best]))
        new_vocab = {}
        for sym, freq in vocab.items():
            out, i = [], 0
            while i < len(sym):
                if i < len(sym) - 1 and (sym[i], sym[i + 1]) == best:
                    out.append(sym[i] + sym[i + 1])
                    i += 2
                else:
                    out.append(sym[i])
                    i += 1
            new_vocab[tuple(out)] = freq
        vocab = new_vocab
    return merges, vocab


def bpe_segment(word: str, merges) -> list[str]:
    sym = list(word) + ["</w>"]
    for (a, b), _ in merges:
        out, i = [], 0
        while i < len(sym):
            if i < len(sym) - 1 and sym[i] == a and sym[i + 1] == b:
                out.append(a + b)
                i += 2
            else:
                out.append(sym[i])
                i += 1
        sym = out
    return sym


merges, vocab = bpe_train(BPE_CORPUS, 10)
for m, f in merges:
    print(f"  merge {m[0]!r}+{m[1]!r} (freq {f})")
seg_new = bpe_segment("newest", merges)
seg_low = bpe_segment("lowest", merges)  # 沒看過的詞
print("  segment 'newest':", seg_new)
print("  segment 'lowest' (unseen):", seg_low)
assert len(seg_new) <= 2, "高頻詞應被合成極少 token"
assert 1 < len(seg_low) <= 4, "未見過的詞應拆成子詞而非炸成字元"

# ── C. 真實 embedding + int8 量化驗證 ───────────────────────────────
# 注意：實測（jina-embed，2026-08）1–2 字的超短輸入會回退化向量（小狗×汽車 0.97），
# 片語級輸入語意結構才正常——demo 一律用短片語，不用裸單詞。
WORDS = [
    "一隻可愛的貓", "一隻忠心的狗", "一頭凶猛的老虎", "一隻跳來跳去的兔子",
    "一輛紅色的汽車", "一列高速的火車", "一架起飛的飛機", "一台共享腳踏車",
    "一杯熱拿鐵咖啡", "一塊草莓蛋糕", "一碗熱騰騰的拉麵", "一顆新鮮的蘋果",
    "今天心情很快樂", "今天覺得好悲傷", "氣得不想說話", "嚇得躲在棉被裡",
]
LABELS_EN = [  # matplotlib 無 CJK 字型：圖上用英文標籤
    "cat", "dog", "tiger", "rabbit",
    "car", "train", "plane", "bike",
    "coffee", "cake", "ramen", "apple",
    "happy", "sad", "angry", "scared",
]
GROUPS = [0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3]

relay, key = os.environ.get("RELAY_URL"), os.environ.get("API_KEY")
if not (relay and key):
    print("\n== C. embeddings: SKIP（未設 RELAY_URL/API_KEY）==")
    sys.exit(0)

from openai import OpenAI

client = OpenAI(base_url=f"{relay}/v1", api_key=key,
                default_headers={"User-Agent": "gtq-client/1.0"})
resp = client.embeddings.create(model="jina-embed", input=WORDS)
V = np.array([d.embedding for d in resp.data], dtype=np.float32)  # (16, 1024)
print(f"\n== C. embeddings ==\nshape: {V.shape}")


def quant_i8(v: np.ndarray):
    """對稱 per-vector int8 量化：v ≈ q * scale。回傳 (q, scale)。"""
    scale = np.abs(v).max(axis=-1, keepdims=True) / 127.0
    q = np.round(v / scale).astype(np.int8)
    return q, scale.astype(np.float32)


def cos_matrix(x: np.ndarray) -> np.ndarray:
    n = x / np.linalg.norm(x, axis=1, keepdims=True)
    return n @ n.T


Q, S = quant_i8(V)
Vq = Q.astype(np.float32) * S
C_fp, C_q = cos_matrix(V), cos_matrix(Vq)
print(f"int8 反量化後 cosine 最大誤差: {np.abs(C_fp - C_q).max():.4f}")
assert np.abs(C_fp - C_q).max() < 0.01, "int8 量化不應改變 cosine 到肉眼可見"

G = np.array(GROUPS)
mask_same = (G[:, None] == G[None, :]) & ~np.eye(16, dtype=bool)
mask_diff = G[:, None] != G[None, :]
within, cross = C_q[mask_same].mean(), C_q[mask_diff].mean()
print(f"組內平均 cosine: {within:.3f}  跨組平均: {cross:.3f}")
assert within > cross + 0.05, "同語意群組的 cosine 應明顯高於跨組"

# PCA（與瀏覽器內同款：中心化 + SVD 取前 2 維）
Xc = Vq - Vq.mean(axis=0)
_, _, Vt = np.linalg.svd(Xc, full_matrices=False)
P2 = Xc @ Vt[:2].T
print("PCA 2D 座標（詞, x, y）：")
for w, (x, y) in zip(WORDS, P2):
    print(f"  {w}: ({x:+.3f}, {y:+.3f})")

pairs = [(0, 1), (0, 4), (12, 13), (8, 9)]
for ia, ib in pairs:
    print(f"cosine({LABELS_EN[ia]},{LABELS_EN[ib]}) = {C_q[ia, ib]:.3f}")
assert C_q[0, 1] > C_q[0, 4], "貓×狗 應高於 貓×汽車"

# 印出 lesson.py 要用的 payload（int8 b64 + scale）
payload = base64.b64encode(Q.tobytes()).decode()
scales = ", ".join(f"{s:.6g}" for s in S.ravel())
print("\n# ---- 貼進 lesson.py 的常數 ----")
print(f"EMB_WORDS = {WORDS!r}")
print(f"EMB_LABELS_EN = {LABELS_EN!r}")
print(f"EMB_GROUPS = {GROUPS!r}")
print(f'EMB_B64 = "{payload}"')
print(f"EMB_SCALES = [{scales}]")
print(f"EMB_DIM = {V.shape[1]}")

# ── D. 自迴歸：字元 bigram LM（瀏覽器 demo 同款）────────────────────
print("\n== D. autoregressive bigram ==")
AR_CORPUS = [
    "今天天氣很好", "今天天氣不好", "今天心情很好", "明天天氣很好",
    "我今天很開心", "我明天要上班", "我今天要上學", "天氣好就出去玩",
    "心情不好就吃蛋糕", "我很喜歡吃蛋糕", "我很喜歡貓", "貓很可愛",
]


def bigram_counts(corpus):
    cnt: dict[str, dict[str, int]] = {}
    for s in corpus:
        seq = "^" + s + "$"
        for a, b in zip(seq, seq[1:]):
            cnt.setdefault(a, {}).setdefault(b, 0)
            cnt[a][b] += 1
    return cnt


cnt = bigram_counts(AR_CORPUS)
probs_after_天 = {k: v / sum(cnt["天"].values()) for k, v in sorted(cnt["天"].items(), key=lambda x: -x[1])}
print("P(next | '天') =", {k: round(v, 3) for k, v in probs_after_天.items()})
assert abs(sum(probs_after_天.values()) - 1) < 1e-9

rng = np.random.default_rng(0)
out = "^"
for _ in range(20):
    dist = cnt.get(out[-1])
    if not dist:
        break
    chars, weights = list(dist), np.array(list(dist.values()), float)
    ch = rng.choice(chars, p=weights / weights.sum())
    if ch == "$":
        break
    out += ch
print("sampled:", out[1:])
print("\nSPIKE OK: genai-tokens")
