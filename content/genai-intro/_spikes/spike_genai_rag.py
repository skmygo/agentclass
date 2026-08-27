# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy", "openai"]
# ///
"""genai-rag 課的定軌 spike：真向量檢索 ＋ 有無 RAG 的真實對照 trace。

語料：虛構咖啡機「拿鐵大師 LM-500」使用手冊 12 段（原創內容，模型不可能背過）。
  A. jina-embed 全部向量化，int8 量化後驗證 top-3 排序不變（瀏覽器 demo 用 int8 版）
  B. 每個問題：無 RAG 直接問（看它掰不掰）vs 附 top-3 段落再問（正確引用）

需要 env：RELAY_URL、API_KEY。
跑法：uv run --script content/genai-intro/_spikes/spike_genai_rag.py
"""

import base64
import json
import os

import numpy as np
from openai import OpenAI

client = OpenAI(base_url=f"{os.environ['RELAY_URL']}/v1", api_key=os.environ["API_KEY"],
                default_headers={"User-Agent": "gtq-client/1.0"})

CHUNKS = [
    "首次使用：第一次使用前，請先執行兩次空水循環——水箱裝滿冷水、不放咖啡粉，按沖煮鍵讓水流完，以清除管線中的製造殘留。",
    "研磨粗細：LM-500 適用中細研磨度。咖啡粉研磨過細會導致過度萃取、流速變慢，嚴重時觸發防堵塞保護而自動停機。",
    "除垢：除垢燈亮起時，將一包除垢劑與 1 公升清水混合倒入水箱，長按沖煮鍵 5 秒進入除垢模式，全程約 20 分鐘，結束後再跑一次清水循環。",
    "水箱：容量 1.2 公升，可整個拆下清洗；建議每天更換新鮮冷水，不要使用溫水或礦泉水。",
    "保固：本產品自購買日起提供 2 年保固。人為損壞、摔落，以及因未定期除垢造成的水垢堵塞，不在保固範圍內。",
    "奶泡：打奶泡請使用冷藏（約 4°C）鮮奶，奶量不超過鋼杯一半；蒸氣管使用後立即以濕布擦拭並空噴一秒。",
    "日常清潔：沖煮頭每週以溫水沖洗一次，滴水盤與粉渣盒每天清空；機身以擰乾的濕布擦拭，切勿整機沖水。",
    "無法啟動：若機器完全沒有反應，請先確認電源線兩端插緊、插座有電，再檢查機身右側的過熱保護開關是否跳起（按下即復位）。",
    "咖啡豆保存：開封後請裝入不透光密封罐，置於陰涼處，並在兩週內使用完畢；不建議冷凍保存。",
    "沖煮溫度：預設 92°C，可在設定選單中以 1°C 為單位調整（範圍 88–96°C）；溫度越高萃取越強，苦味也越明顯。",
    "自動待機：機器閒置 30 分鐘後自動進入省電待機，按任意鍵喚醒；喚醒後約 40 秒完成預熱。",
    "運轉噪音：內建磨豆機運轉時瞬間噪音約 70 分貝，屬正常現象；若出現金屬摩擦異音，請立即停機檢查豆槽異物。",
]
QUERIES = [
    "咖啡機第一次使用前要做什麼？",
    "除垢燈亮了該怎麼處理？",
    "咖啡粉磨太細會發生什麼事？",
    "保固期多久？哪些情況不保固？",
]
EXPECT_TOP1 = [0, 2, 1, 4]


def embed(texts):
    r = client.embeddings.create(model="jina-embed", input=list(texts))
    return np.array([d.embedding for d in sorted(r.data, key=lambda d: d.index)], dtype=np.float32)


def quant_i8(v):
    s = np.abs(v).max(axis=-1, keepdims=True) / 127.0
    return np.round(v / s).astype(np.int8), s.astype(np.float32)


def top3(qv, dv):
    n_q = qv / np.linalg.norm(qv)
    n_d = dv / np.linalg.norm(dv, axis=1, keepdims=True)
    sims = n_d @ n_q
    idx = np.argsort(-sims)[:3]
    return idx, sims


# ── A. 檢索 ＋ int8 驗證 ─────────────────────────────────────────────
print("== A. retrieval ==")
DV, QV = embed(CHUNKS), embed(QUERIES)
DQ, DS = quant_i8(DV)
QQ, QS = quant_i8(QV)
DVq, QVq = DQ.astype(np.float32) * DS, QQ.astype(np.float32) * QS
for qi, q in enumerate(QUERIES):
    idx_fp, sims_fp = top3(QV[qi], DV)
    idx_q, sims_q = top3(QVq[qi], DVq)
    print(f"Q{qi+1}「{q}」 top3 = {list(idx_q)}  sims = {[f'{sims_q[i]:.3f}' for i in idx_q]}")
    assert idx_q[0] == EXPECT_TOP1[qi], f"Q{qi+1} top1 應為 chunk {EXPECT_TOP1[qi]}"
    assert list(idx_fp) == list(idx_q), f"Q{qi+1} int8 排序應與 fp32 一致"

# ── B. 無 RAG vs 有 RAG ─────────────────────────────────────────────
print("\n== B. no-RAG vs RAG ==")


def ask(messages, max_tokens=512):
    r = client.chat.completions.create(
        model="qwen3.5-2b", messages=messages, max_tokens=max_tokens, temperature=0.0,
        extra_body={"chat_template_kwargs": {"enable_thinking": False}})
    return (r.choices[0].message.content or "").strip()


SYS_BARE = "你是「拿鐵大師 LM-500」咖啡機的客服，請回答使用者的問題。"
SYS_RAG = (SYS_BARE + "只能根據下面提供的手冊段落回答；手冊裡沒有的資訊，要說「手冊中沒有提到」。")

traces = []
for qi, q in enumerate(QUERIES):
    bare = ask([{"role": "system", "content": SYS_BARE}, {"role": "user", "content": q}])
    idx, _ = top3(QVq[qi], DVq)
    ctx = "\n".join(f"【段落{i+1}】{CHUNKS[i]}" for i in idx)
    rag = ask([{"role": "system", "content": SYS_RAG},
               {"role": "user", "content": f"手冊段落：\n{ctx}\n\n問題：{q}"}])
    traces.append({"q": q, "bare": bare, "rag": rag, "top3": [int(i) for i in idx]})
    print(f"\nQ{qi+1}: {q}\n  無RAG: {bare[:120]}\n  有RAG: {rag[:120]}")

# 有 RAG 的回答應含手冊關鍵事實
assert "兩次" in traces[0]["rag"] or "空水" in traces[0]["rag"]
assert "1 公升" in traces[1]["rag"] or "20 分鐘" in traces[1]["rag"] or "除垢模式" in traces[1]["rag"]
assert "2 年" in traces[3]["rag"]

print("\n# ---- 貼進課程的常數 ----")
print(f"RAG_CHUNKS = {CHUNKS!r}")
print(f"RAG_QUERIES = {QUERIES!r}")
print(f'RAG_DOC_B64 = "{base64.b64encode(DQ.tobytes()).decode()}"')
print(f"RAG_DOC_SCALES = [{', '.join(f'{s:.6g}' for s in DS.ravel())}]")
print(f'RAG_Q_B64 = "{base64.b64encode(QQ.tobytes()).decode()}"')
print(f"RAG_Q_SCALES = [{', '.join(f'{s:.6g}' for s in QS.ravel())}]")
print("RAG_TRACES =", json.dumps(traces, ensure_ascii=False, indent=1))
print("\nSPIKE OK: genai-rag")
