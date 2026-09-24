# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "numpy",
#   "openai",
#   "bm25s==0.3.11",
#   "sentence-transformers==6.1.0",
#   "torch",
# ]
# [tool.uv.sources]
# torch = { index = "pytorch-cpu" }
# [[tool.uv.index]]
# name = "pytorch-cpu"
# url = "https://download.pytorch.org/whl/cpu"
# explicit = true
# ///
"""genai-rag-advanced（補充 A：進階 RAG）的定軌 spike ＋ 課程素材錄製。

語料：虛構咖啡機「拿鐵大師 LM-500／500S／700」的**進階版手冊**——20 節（父塊）、90 句（子塊），
含故障碼表（E01–E20）與長得很像的零件型號（WF-12／WF-21、GS-54／GS-58…）。
問題集：41 題、每題標好標準答案（哪幾個子塊），分四型：
  proc＝多步驟（答案橫跨同一節好幾句）、pin＝單點、kw＝型號／故障碼、para＝換句話說（用詞跟手冊不同）。

各段（--part，可逗號串接；預設全部）：
  embed   子塊／加標題子塊／父塊／五種固定大小切塊＋問題 → 向量（int8 量化並驗證排序不變）
  bm25    numpy 手寫 BM25（字元 bigram＋英數整詞）→ 與 bm25s（lucene）逐分數比對
  rerank  cross-encoder（BAAI/bge-reranker-v2-m3，CPU）對「每題 × 每個子塊」打分 ＋ 計時
  eval    各策略的 hit@k／recall@k／MRR／覆蓋率（課文引用的數字從這裡來）
  llm     hero 三個案例：天真 RAG vs 修好後，qwen3.5-2b 的真實回答（需要 LLM_URL）
  errors  測驗診斷題素材：分數直接相加的混合、父塊沒去重、少了 Query/Document 前綴
  emit    把課程要用的常數寫成 JSON（之後由注入腳本塞進 lesson.py）

向量從哪來（二選一）：
  - 設了 EMBED_URL（OpenAI 相容 /v1，模型名 EMBED_MODEL，預設 jina-embed）→ 打服務
  - 加 --local → 在本機 CPU 用 sentence-transformers 載同一個開源模型
    （jinaai/jina-embeddings-v5-text-small-retrieval，CC BY-NC 4.0），不需要任何服務——
    Colab／Kaggle 免費 CPU 也跑得動。
LLM（只有 llm 段需要）：LLM_URL（OpenAI 相容 /v1）＋ LLM_MODEL（預設 qwen3.5-2b）；
  沒有 LLM 服務可用本機 Ollama（LLM_URL=http://localhost:11434/v1），數字與文字會不同。

跑法（repo 根）：
  EMBED_URL=... LLM_URL=... uv run --script content/genai-intro/_spikes/spike_genai_rag_advanced.py --out <dir>
  uv run --script content/genai-intro/_spikes/spike_genai_rag_advanced.py --local --part embed,bm25,rerank,eval --out <dir>
"""

import argparse
import base64
import json
import os
import re
import time
from pathlib import Path

import numpy as np

# ═════════════════════════════ 語料：20 節 × 子句 ═════════════════════════════
SECTIONS = [
    ("開箱與首次使用", [
        "包裝內含主機、水箱、雙份濾杯把手、蒸氣鋼杯，以及一包 DC-300 除垢劑。",
        "首次使用前，先把濾水芯浸泡在冷水中 5 分鐘，再裝進水箱底部的卡槽。",
        "水箱裝滿冷水、不放咖啡粉，按沖煮鍵讓水流完；這樣的空水循環要連做兩次。",
        "接著打開蒸氣旋鈕空噴 10 秒，把蒸氣管裡的製造殘留排乾淨。",
        "最後在設定選單把水質硬度設成你家的等級（1 到 4 級，出廠值為 3 級）。",
    ]),
    ("機型差異", [
        "LM-500 是單鍋爐機型，同一時間只能沖煮或打奶泡其中一件事。",
        "LM-500S 加裝蒸氣預熱，從沖煮切換到打奶泡只要約 5 秒。",
        "LM-700 是雙鍋爐機型，可以一邊萃取一邊打奶泡。",
        "LM-700 的水箱為 1.8 公升，LM-500 與 LM-500S 為 1.2 公升。",
        "LM-500 與 LM-500S 使用 54 mm 把手，LM-700 使用 58 mm 把手。",
    ]),
    ("沖煮義式濃縮", [
        "單份濃縮用 18 公克咖啡粉，雙份濾杯用 20 公克。",
        "填粉後以約 15 公斤的力道垂直壓粉，粉面要壓平。",
        "把手鎖緊後按單杯鍵，理想萃取時間是 25 到 30 秒，萃取量約 36 毫升。",
        "不到 20 秒就流完，代表研磨太粗或粉量不足。",
        "超過 35 秒還在滴，代表研磨太細或壓粉太用力。",
    ]),
    ("研磨設定", [
        "內建錐刀磨豆機共有 15 段刻度，1 最細、15 最粗。",
        "義式濃縮建議從第 5 段開始，每次只調一格。",
        "調整刻度必須在磨豆機運轉時進行，停機時硬轉會卡住刀盤。",
        "研磨過細會導致過度萃取、流速變慢，嚴重時觸發防堵塞保護而自動停機。",
    ]),
    ("沖煮溫度", [
        "預設沖煮溫度為 92°C，可以 1°C 為單位調整，範圍 88 到 96°C。",
        "淺焙豆適合 93 到 95°C；深焙豆建議 88 到 90°C，可以減少苦味。",
        "溫度越高萃取越強，苦味也越明顯。",
    ]),
    ("奶泡與蒸氣", [
        "請使用冷藏約 4°C 的鮮奶，奶量不超過鋼杯的一半。",
        "蒸氣管先空噴 2 秒排掉冷凝水，再把噴頭埋入奶面下約 1 公分。",
        "聽到嘶嘶的進氣聲約 3 秒後，把噴頭壓深，讓牛奶旋轉加熱到 60 到 65°C。",
        "用完立刻以濕布擦拭蒸氣管並空噴 1 秒，避免奶垢堵住噴孔。",
    ]),
    ("熱水功能", [
        "轉開熱水旋鈕即可出熱水，出水溫度約 85°C。",
        "熱水與蒸氣共用同一支管路，出熱水前請先空噴 2 秒。",
        "泡茶時建議先出 50 毫升熱水溫杯，再倒掉。",
    ]),
    ("除垢", [
        "有裝濾水芯時，除垢週期可以從 3 個月延長到 6 個月。",
        "除垢燈亮起代表累積用水量已達設定值，請在一週內完成除垢。",
        "先取下濾水芯，再把一包 DC-300 除垢劑與 1 公升清水混合倒入水箱。",
        "長按沖煮鍵 5 秒進入除垢模式，機器會分段流出除垢液，全程約 20 分鐘。",
        "除垢液流完後，沖洗水箱並裝滿清水，再按一次沖煮鍵跑完清水循環。",
        "最後裝回濾水芯，除垢燈熄滅即完成；除垢途中請勿關機。",
    ]),
    ("日常清潔", [
        "滴水盤與粉渣盒每天清空，滴水盤的浮標升起時要立刻倒掉。",
        "沖煮頭每週以溫水沖洗一次，並用附贈的刷子刷掉殘粉。",
        "每月逆洗沖煮頭一次：把盲碗裝進把手、放入一錠清潔錠，長按單杯鍵 10 秒。",
        "機身以擰乾的濕布擦拭，切勿整機沖水或放進洗碗機。",
    ]),
    ("零件與耗材型號", [
        "WF-12：濾水芯，LM-500 與 LM-500S 用，每 2 個月或 50 公升更換一次。",
        "WF-21：濾水芯，LM-700 專用，每 3 個月或 80 公升更換一次；與 WF-12 外觀相似，不可混用。",
        "DC-300：除垢劑，一盒 3 包，一包兌 1 公升清水。",
        "CL-10：沖煮頭清潔錠，一盒 8 錠，每月逆洗用一錠。",
        "GS-54：矽膠墊圈，54 mm 把手用，建議每年更換。",
        "GS-58：矽膠墊圈，58 mm 把手用，建議每年更換。",
        "SN-4：四孔蒸氣噴頭，可替換原廠的單孔噴頭 SN-1，奶泡更快更細。",
        "BK-20：20 公克雙份濾杯，另售的 BK-14 為 14 公克單份濾杯。",
    ]),
    ("省電與待機", [
        "機器閒置 30 分鐘後自動進入省電待機，按任意鍵即可喚醒。",
        "喚醒後約 40 秒完成預熱，指示燈由閃爍轉為恆亮。",
        "自動待機時間可在設定選單改成 15、30 或 60 分鐘。",
    ]),
    ("設定選單", [
        "同時長按單杯鍵與雙杯鍵 3 秒進入設定選單。",
        "用單杯鍵往下、雙杯鍵往上切換項目，按沖煮鍵確認。",
        "可設定的項目有沖煮溫度、自動待機時間、水質硬度與單杯萃取量。",
        "長按沖煮鍵 10 秒可恢復出廠設定。",
    ]),
    ("App 連線", [
        "LM-500S 與 LM-700 可用「拿鐵大師」App 連線，LM-500 不支援。",
        "首次配對時長按雙杯鍵 5 秒，指示燈快閃即進入配對模式。",
        "App 可以遠端預熱、記錄每杯萃取時間，並在需要除垢時推播提醒。",
    ]),
    ("安全注意事項", [
        "運轉中的沖煮頭與蒸氣管溫度很高，請勿直接觸碰。",
        "請使用 110V 單獨插座，不要與電暖器共用延長線。",
        "兒童須在大人陪同下使用。",
        "長時間不使用時，請倒空水箱與滴水盤並拔掉插頭。",
    ]),
    ("故障碼 E01–E05：水路", [
        "E01：水箱缺水或沒有放好，請加水並確認水箱卡到底。",
        "E02：水泵抽不到水，多半是水路進了空氣，請跑兩次清水循環排氣。",
        "E03：流量計沒有訊號，請取下濾水芯後重開機；仍出現請送修。",
        "E04：水路壓力過高，通常是沖煮頭堵塞，請做一次逆洗。",
        "E05：除垢程序被中斷，請重新長按沖煮鍵 5 秒完成除垢。",
    ]),
    ("故障碼 E06–E10：研磨與沖煮", [
        "E06：豆槽沒有咖啡豆，請補充咖啡豆。",
        "E07：研磨室堵塞，請關機拔插頭，取下豆槽後用附贈的刷子清出卡住的粉塊。",
        "E08：粉渣盒已滿或沒有裝好，請清空後重新裝回。",
        "E09：把手沒有鎖到定位，請重新鎖緊把手。",
        "E10：萃取流速過慢，請把研磨調粗一格後再試。",
    ]),
    ("故障碼 E11–E15：溫度與蒸氣", [
        "E11：溫度感測器異常，請關機 10 分鐘後重開，持續出現請送修。",
        "E12：加熱器過熱保護啟動，請關機冷卻 30 分鐘。",
        "E13：蒸氣壓力過高，請先關閉蒸氣旋鈕，等待 3 分鐘洩壓。",
        "E14：蒸氣管堵塞，請用通針疏通噴孔後空噴 5 秒。",
        "E15：預熱逾時，請確認室溫高於 5°C，並檢查電壓是否為 110V。",
    ]),
    ("故障碼 E16–E20：電子與連線", [
        "E16：主機板通訊錯誤，請拔插頭 1 分鐘後重開，仍出現請送修。",
        "E17：觸控面板沒有回應，請用乾布擦乾面板後重開機。",
        "E18：App 連線失敗，請確認手機與機器連在同一個 2.4GHz Wi-Fi。",
        "E19：韌體更新失敗，請保持連線並重新執行更新，更新中勿拔插頭。",
        "E20：滴水盤沒有裝好，請推到底直到聽見喀一聲。",
    ]),
    ("常見問題", [
        "咖啡變苦：多半是過度萃取，把研磨調粗一格，或把沖煮溫度調低 2°C。",
        "咖啡偏酸、喝起來水水的：多半是萃取不足，把研磨調細一格，或多加 1 公克粉。",
        "奶泡太粗、泡泡很大：噴頭埋得太淺，或鮮奶不夠冰。",
        "沖煮頭周圍漏水：通常是矽膠墊圈老化，或把手沒有鎖緊。",
        "機器完全沒反應：確認電源線兩端插緊、插座有電，再按下機身背面的過熱保護復位鈕。",
    ]),
    ("保固與送修", [
        "本產品自購買日起提供 2 年保固，送修時需出示發票或電子保卡。",
        "人為損壞、摔落，以及未定期除垢造成的水垢堵塞，不在保固範圍內。",
        "送修前請倒空水箱與滴水盤，並用原廠紙箱或同等級的緩衝材包裝。",
        "保固期外的維修收取檢測費 500 元，維修報價經你同意後才會施工。",
    ]),
]

# 攤平：單位（unit）＝章節標題行或子句；子塊＝子句；父塊＝一整節
UNITS, UNIT_KIND, UNIT_SEC = [], [], []
CHILD_UNIT, CHILD_SEC, CHILDREN = [], [], []
SEC_UNITS = []
for _s, (_title, _sents) in enumerate(SECTIONS):
    _ids = [len(UNITS)]
    UNITS.append(f"【{_title}】")
    UNIT_KIND.append("h")
    UNIT_SEC.append(_s)
    for _t in _sents:
        CHILD_UNIT.append(len(UNITS))
        CHILD_SEC.append(_s)
        CHILDREN.append(_t)
        _ids.append(len(UNITS))
        UNITS.append(_t)
        UNIT_KIND.append("c")
        UNIT_SEC.append(_s)
    SEC_UNITS.append(_ids)
PARENTS = ["".join(UNITS[u] for u in ids) for ids in SEC_UNITS]
TITLES = [t for t, _ in SECTIONS]
CHILDREN_HDR = [f"{TITLES[CHILD_SEC[i]]}｜{c}" for i, c in enumerate(CHILDREN)]

# 固定大小切塊（天真做法）：整句依序裝箱，裝到 size 字就換下一塊；可跨節、不重疊
WINDOW_SIZES = [60, 150, 300, 600]


def pack_windows(size):
    wins, cur, n = [], [], 0
    for u, t in enumerate(UNITS):
        if cur and n + len(t) > size:
            wins.append(cur)
            cur, n = [], 0
        cur.append(u)
        n += len(t)
    if cur:
        wins.append(cur)
    return wins


WINDOWS = {s: pack_windows(s) for s in WINDOW_SIZES}

# ═════════════════════════════ 問題集（標準答案＝子句的唯一子字串）═════════════════════════════
QUESTIONS = [
    # proc：多步驟，答案橫跨同一節的好幾句
    ("除垢的完整步驟是什麼？", "proc", ["先取下濾水芯，再把", "長按沖煮鍵 5 秒進入除垢", "除垢液流完後", "最後裝回濾水芯"]),
    ("新機第一次使用前要做哪些準備？", "proc", ["浸泡在冷水中 5 分鐘", "空水循環要連做兩次", "空噴 10 秒", "水質硬度設成"]),
    ("怎麼打出綿密的奶泡？", "proc", ["冷藏約 4°C", "埋入奶面下約 1 公分", "嘶嘶的進氣聲"]),
    ("怎麼沖一杯標準的義式濃縮？", "proc", ["單份濃縮用 18", "15 公斤的力道", "理想萃取時間"]),
    ("萃取時間不對，要怎麼判斷問題出在哪？", "proc", ["不到 20 秒就流完", "超過 35 秒還在滴"]),
    ("日常清潔要做哪些事？", "proc", ["滴水盤與粉渣盒每天清空", "沖煮頭每週以溫水", "每月逆洗沖煮頭", "擰乾的濕布"]),
    ("送修要準備什麼？", "proc", ["出示發票或電子保卡", "送修前請倒空水箱"]),
    ("手機 App 要怎麼配對？", "proc", ["可用「拿鐵大師」App 連線", "首次配對時長按雙杯鍵"]),
    # pin：單點事實
    ("奶泡的牛奶要加熱到幾度？", "pin", ["嘶嘶的進氣聲"]),
    ("單份濃縮要放幾公克咖啡粉？", "pin", ["單份濃縮用 18"]),
    ("機器閒置多久會自動待機？", "pin", ["閒置 30 分鐘後"]),
    ("水質硬度出廠設定是幾級？", "pin", ["水質硬度設成"]),
    ("保固期外維修要付多少檢測費？", "pin", ["檢測費 500 元"]),
    ("研磨刻度可以在停機時調整嗎？", "pin", ["停機時硬轉"]),
    ("深焙豆適合用幾度沖煮？", "pin", ["深焙豆建議"]),
    ("熱水出水溫度大約幾度？", "pin", ["出水溫度約 85°C"]),
    # kw：型號／故障碼
    ("螢幕顯示 E07 怎麼辦？", "kw", ["E07："]),
    ("E05 是什麼意思？", "kw", ["E05："]),
    ("出現 E13 要怎麼處理？", "kw", ["E13："]),
    ("E16 錯誤碼代表什麼？", "kw", ["E16："]),
    ("E11 一直出現怎麼辦？", "kw", ["E11："]),
    ("E18 怎麼排除？", "kw", ["E18："]),
    ("E03 需要送修嗎？", "kw", ["E03："]),
    ("E09 怎麼辦？", "kw", ["E09："]),
    ("WF-12 多久要換一次？", "kw", ["WF-12：濾水芯"]),
    ("WF-21 可以裝在 LM-500 上嗎？", "kw", ["WF-21："]),
    ("CL-10 要怎麼用？", "kw", ["CL-10：", "每月逆洗沖煮頭"]),
    ("GS-58 適用哪一台？", "kw", ["GS-58：", "LM-700 使用 58 mm"]),
    ("DC-300 一包要配多少水？", "kw", ["DC-300：除垢劑", "一包 DC-300 除垢劑與 1 公升"]),
    ("LM-700 的水箱多大？", "kw", ["LM-700 的水箱為 1.8"]),
    ("SN-4 是什麼？", "kw", ["SN-4："]),
    # para：換句話說（使用者的用詞跟手冊不同）
    ("咖啡喝起來很苦，該怎麼調？", "para", ["咖啡變苦："]),
    ("打出來的牛奶都是大泡泡，哪裡做錯了？", "para", ["奶泡太粗、泡泡很大"]),
    ("插了電卻完全不會動，怎麼辦？", "para", ["機器完全沒反應"]),
    ("把手旁邊一直滴水是什麼問題？", "para", ["沖煮頭周圍漏水"]),
    ("味道很淡又帶酸，是什麼原因？", "para", ["咖啡偏酸"]),
    ("早上按下去要等多久才能用？", "para", ["喚醒後約 40 秒"]),
    ("摔到地上壞掉可以免費修嗎？", "para", ["人為損壞、摔落"]),
    ("除垢做到一半停電了會怎樣？", "para", ["E05：", "除垢途中請勿關機"]),
    ("出國兩個月不在家，機器要怎麼處理？", "para", ["長時間不使用時"]),
    ("可以一邊萃取一邊打奶泡嗎？", "para", ["LM-500 是單鍋爐", "LM-700 是雙鍋爐"]),
]


def _resolve(key):
    hits = [i for i, c in enumerate(CHILDREN) if key in c]
    assert len(hits) == 1, f"gold 子字串「{key}」對到 {len(hits)} 句"
    return hits[0]


Q_TEXT = [q for q, _, _ in QUESTIONS]
Q_TYPE = [t for _, t, _ in QUESTIONS]
Q_GOLD = [[_resolve(k) for k in keys] for _, _, keys in QUESTIONS]


EMBED_MODEL = os.environ.get("EMBED_MODEL", "jina-embed")
HF_EMBED = "jinaai/jina-embeddings-v5-text-small-retrieval"
HF_RERANK = "BAAI/bge-reranker-v2-m3"
LLM_MODEL = os.environ.get("LLM_MODEL", "qwen3.5-2b")


# ═════════════════════════════ 向量 ═════════════════════════════
class Embedder:
    """jina v5 retrieval 模型要分 query／document 兩種前綴（sentence-transformers 的 prompt_name）。"""

    def __init__(self, local):
        self.local = local
        if local:
            import torch
            from sentence_transformers import SentenceTransformer

            # CPU 上一定要 float32：這個模型預設載成 bfloat16，CPU 上實測慢 5.6 倍（32 句 16.2 s vs 2.9 s，2 執行緒）
            self.m = SentenceTransformer(HF_EMBED, device="cpu", trust_remote_code=True,
                                         model_kwargs={"dtype": torch.float32})
        else:
            from openai import OpenAI

            self.c = OpenAI(base_url=os.environ["EMBED_URL"], api_key=os.environ.get("EMBED_KEY", "none"))

    def __call__(self, texts, kind, prefix=True):
        if self.local:
            kw = {"prompt_name": kind} if prefix else {}
            v = self.m.encode(list(texts), batch_size=16, **kw)
            return np.asarray(v, dtype=np.float32)
        pre = ("Query: " if kind == "query" else "Document: ") if prefix else ""
        out = []
        for i in range(0, len(texts), 32):  # 一批 ≤32
            r = self.c.embeddings.create(model=EMBED_MODEL, input=[pre + t for t in texts[i : i + 32]])
            out += [d.embedding for d in sorted(r.data, key=lambda d: d.index)]
        return np.asarray(out, dtype=np.float32)


def norm(v):
    return v / np.linalg.norm(v, axis=-1, keepdims=True)


def quant_i8(v):
    s = np.abs(v).max(axis=-1, keepdims=True) / 127.0
    return np.round(v / s).astype(np.int8), s.astype(np.float32)


def dequant(q, s):
    return norm(q.astype(np.float32) * s)


def part_embed(out, local):
    emb = Embedder(local)
    t0 = time.time()
    vec = {
        "q": emb(Q_TEXT, "query"),
        "child": emb(CHILDREN, "document"),
        "child_hdr": emb(CHILDREN_HDR, "document"),
        "parent": emb(PARENTS, "document"),
        # 少了前綴的對照組（測驗診斷題素材）
        "q_nopre": emb(Q_TEXT, "query", prefix=False),
        "child_nopre": emb(CHILDREN, "document", prefix=False),
    }
    for s in WINDOW_SIZES:
        vec[f"win{s}"] = emb(["".join(UNITS[u] for u in w) for w in WINDOWS[s]], "document")
    print(f"embedded {sum(len(v) for v in vec.values())} texts in {time.time() - t0:.1f}s "
          f"({'local ' + HF_EMBED if local else 'service ' + EMBED_MODEL}), dim={vec['q'].shape[1]}")
    # int8 驗證：每題對每個索引的前 3 名、以及標準答案的名次，int8 與 fp32 完全一致
    worst = 0.0
    for name, v in vec.items():
        if name.startswith("q"):
            continue
        qv = vec["q_nopre"] if name.endswith("nopre") else vec["q"]
        s_fp = norm(qv) @ norm(v).T
        s_q = dequant(*quant_i8(qv)) @ dequant(*quant_i8(v)).T
        worst = max(worst, float(np.abs(s_fp - s_q).max()))
        top3 = sum(set(np.argsort(-s_fp[i])[:3]) == set(np.argsort(-s_q[i])[:3]) for i in range(len(Q_TEXT)))
        msg = f"  {name:12s} n={v.shape[0]:3d}  int8 top-3 set identical: {top3}/{len(Q_TEXT)} questions"
        if name in ("child", "child_hdr", "child_nopre"):
            same_rank = all(rank_of_first(list(np.argsort(-s_fp[i])), set(Q_GOLD[i]))
                            == rank_of_first(list(np.argsort(-s_q[i])), set(Q_GOLD[i])) for i in range(len(Q_TEXT)))
            msg += f"  gold ranks identical: {same_rank}"
            assert same_rank
        print(msg)
    print(f"  max |cos_fp32 - cos_int8| = {worst:.4f}")
    np.savez(out / f"vectors_{'local' if local else 'service'}.npz", **vec)
    return vec


# ═════════════════════════════ BM25（numpy，與瀏覽器同一份演算法）═════════════════════════════
TOKEN_RE = re.compile(r"[a-z0-9]+(?:[-.][a-z0-9]+)*|[一-鿿]+")


def tokenize(text):
    """英數整詞（e07、wf-12、1.2）＋中文字元 bigram（單字詞保留原字）。"""
    toks = []
    for m in TOKEN_RE.findall(text.lower()):
        if "一" <= m[0] <= "鿿":
            toks += [m] if len(m) == 1 else [m[i : i + 2] for i in range(len(m) - 1)]
        else:
            toks.append(m)
    return toks


def bm25_scores(docs, queries, k1=1.5, b=0.75):
    dt = [tokenize(d) for d in docs]
    vocab = {t: i for i, t in enumerate(sorted({t for d in dt for t in d}))}
    tf = np.zeros((len(docs), len(vocab)), dtype=np.float32)
    for i, d in enumerate(dt):
        for t in d:
            tf[i, vocab[t]] += 1
    dl = tf.sum(1)
    n = len(docs)
    df = (tf > 0).sum(0)
    idf = np.log(1 + (n - df + 0.5) / (df + 0.5))
    w = tf / (tf + k1 * (1 - b + b * dl[:, None] / dl.mean()))  # Lucene 形式（省略常數 k1+1，排序不變）
    out = np.zeros((len(queries), n), dtype=np.float32)
    for qi, q in enumerate(queries):
        ids = [vocab[t] for t in tokenize(q) if t in vocab]  # 重複詞照算（與 bm25s 一致）
        if ids:
            out[qi] = (w[:, ids] * idf[ids]).sum(1)
    return out


def part_bm25():
    import bm25s

    ours = bm25_scores(CHILDREN, Q_TEXT)
    r = bm25s.BM25(method="lucene", k1=1.5, b=0.75)
    r.index([tokenize(c) for c in CHILDREN])
    ref = np.stack([r.get_scores(tokenize(q)) for q in Q_TEXT])
    diff = float(np.abs(ours - ref).max())
    print(f"BM25 numpy vs bm25s {bm25s.__version__} (lucene): max |diff| = {diff:.2e}")
    assert diff < 1e-3
    print("  tokenize('螢幕顯示 E07 怎麼辦？') =", tokenize("螢幕顯示 E07 怎麼辦？"))
    return ours


# ═════════════════════════════ rerank（cross-encoder，CPU）═════════════════════════════
def part_rerank(out):
    import torch
    from sentence_transformers import CrossEncoder

    torch.set_num_threads(int(os.environ.get("RERANK_THREADS", max(1, (os.cpu_count() or 4) // 2))))
    ce = CrossEncoder(HF_RERANK, device="cpu")
    pairs = [(q, c) for q in Q_TEXT for c in CHILDREN]
    ce.predict(pairs[:8])  # 暖機
    t0 = time.time()
    sc = ce.predict(pairs, batch_size=32, show_progress_bar=False)
    dt = time.time() - t0
    sc = np.asarray(sc, dtype=np.float32).reshape(len(Q_TEXT), len(CHILDREN))
    t1 = time.time()
    ce.predict([(Q_TEXT[0], c) for c in CHILDREN[:20]], batch_size=32, show_progress_bar=False)
    dt20 = time.time() - t1
    print(f"rerank {len(pairs)} pairs with {HF_RERANK} on CPU ({torch.get_num_threads()} threads): "
          f"{dt:.1f}s = {dt / len(pairs) * 1000:.1f} ms/pair; one query × 20 candidates = {dt20 * 1000:.0f} ms")
    np.save(out / "rerank.npy", sc)
    return sc


# ═════════════════════════════ 評估：一律用「排好名的結果清單」═════════════════════════════
# 與瀏覽器同一份邏輯：每個檢索器吐一張清單（BM25 只列出有命中字詞的文件，分數 0 的不算被檢索到），
# 融合、重排、指標都在清單上算。
def dense_lists(sim):
    return [[int(i) for i in np.argsort(-row, kind="stable")] for row in sim]


def bm25_lists(bm):
    return [[int(i) for i in np.argsort(-row, kind="stable") if row[i] > 0] for row in bm]


def rrf_lists(a, b, k=60, wa=1.0, wb=1.0):
    """Reciprocal Rank Fusion：score(d) = Σ w / (k + 名次)；沒出現在某張清單就不拿那一份。"""
    out = []
    for la, lb in zip(a, b):
        sc = {}
        for w, lst in ((wa, la), (wb, lb)):
            for r, d in enumerate(lst, 1):
                sc[d] = sc.get(d, 0.0) + w / (k + r)
        out.append(sorted(sc, key=lambda d: -sc[d]))
    return out


def sum_lists(sim, bm):
    """（錯誤示範）把 cosine 與 BM25 原始分數直接相加。"""
    return dense_lists(sim + bm)


def rerank_lists(lists, ce, n):
    """第一階段清單的前 n 名交給 cross-encoder 重排，其餘照原順序接在後面。"""
    return [sorted(lst[:n], key=lambda d: -ce[qi][d]) + lst[n:] for qi, lst in enumerate(lists)]


def rank_of_first(order, gold):
    for r, i in enumerate(order, 1):
        if i in gold:
            return r
    return None


def list_metrics(lists, k=3):
    rows = []
    for qi, lst in enumerate(lists):
        g = set(Q_GOLD[qi])
        r = rank_of_first(lst, g)
        rows.append({"hit1": float(bool(lst) and lst[0] in g), "reck": len(g & set(lst[:k])) / len(g),
                     "mrr": 1.0 / r if r else 0.0, "rank": r})
    return rows


def summarize(rows, label):
    out = []
    for t in ["proc", "pin", "kw", "para", "all"]:
        sel = [r for r, qt in zip(rows, Q_TYPE) if t == "all" or qt == t]
        out.append(f"{t}:h1={np.mean([r['hit1'] for r in sel]):.2f} r3={np.mean([r['reck'] for r in sel]):.2f} "
                   f"mrr={np.mean([r['mrr'] for r in sel]):.2f}")
    print(f"  {label:24s} " + " | ".join(out))


def context_units(kind, lst, k, win_size=None):
    """回傳塞進 prompt 的單位（unit）集合。kind: child／parent（父子）／win（固定大小切塊，lst 是切塊名次）。"""
    if kind == "child":
        return {CHILD_UNIT[i] for i in lst[:k]}
    if kind == "parent":  # 父子檢索：前 k 個子塊 → 換成它們所在的整節（去重）
        return {u for i in lst[:k] for u in SEC_UNITS[CHILD_SEC[i]]}
    return {u for i in lst[:k] for u in WINDOWS[win_size][i]}


def coverage_rows(kind, lists, k, win_size=None):
    rows = []
    for qi, lst in enumerate(lists):
        u = context_units(kind, lst, k, win_size)
        g = [CHILD_UNIT[c] for c in Q_GOLD[qi]]
        c = sum(x in u for x in g) / len(g)
        rows.append({"cov": c, "full": float(c == 1.0), "chars": sum(len(UNITS[x]) for x in u)})
    return rows


def coverage_summary(rows, label):
    def m(t, key):
        return np.mean([r[key] for r, qt in zip(rows, Q_TYPE) if t == "all" or qt == t])

    single = [r["full"] for r, qt in zip(rows, Q_TYPE) if qt != "proc"]
    print(f"  {label:14s} proc: cov={m('proc', 'cov'):.2f} full={m('proc', 'full'):.2f} | "
          f"single-fact found={np.mean(single):.2f} | avg chars={m('all', 'chars'):.0f}")


def load_all(out, local):
    """讀向量與 rerank 分數，並換成「瀏覽器實際拿到的版本」（int8 還原、四捨五入後的矩陣）。"""
    vec = dict(np.load(out / f"vectors_{'local' if local else 'service'}.npz"))
    qn = dequant(*quant_i8(vec["q"]))
    d = {"dense": qn @ dequant(*quant_i8(vec["child"])).T,
         "hdr": np.round(qn @ dequant(*quant_i8(vec["child_hdr"])).T, 4),
         "nopre": dequant(*quant_i8(vec["q_nopre"])) @ dequant(*quant_i8(vec["child_nopre"])).T,
         "bm25": bm25_scores(CHILDREN, Q_TEXT)}
    for s in WINDOW_SIZES:
        d[f"win{s}"] = np.round(qn @ dequant(*quant_i8(vec[f"win{s}"])).T, 4)
    rr = out / "rerank.npy"
    if rr.exists():
        p = np.clip(np.load(rr).astype(np.float64), 1e-9, 1 - 1e-9)
        d["ce"] = np.round(np.log(p / (1 - p)), 3)  # logit，瀏覽器收到的版本
    return vec, d


def part_eval(out, local):
    vec, d = load_all(out, local)
    L = {"dense": dense_lists(d["dense"]), "bm25": bm25_lists(d["bm25"]), "hdr": dense_lists(d["hdr"]),
         "nopre": dense_lists(d["nopre"])}
    L["rrf"] = rrf_lists(L["dense"], L["bm25"])
    print("\n== 子塊層級檢索（h1＝第一名就對、r3＝recall@3、MRR）==")
    summarize(list_metrics(L["dense"]), "dense")
    summarize(list_metrics(L["hdr"]), "dense + 章節標題")
    summarize(list_metrics(L["nopre"]), "dense 少了前綴 (bug)")
    summarize(list_metrics(L["bm25"]), "BM25")
    summarize(list_metrics(L["rrf"]), "hybrid RRF k=60")
    for wb in [0.25, 0.5]:
        summarize(list_metrics(rrf_lists(L["dense"], L["bm25"], wb=wb)), f"hybrid RRF w_bm25={wb}")
    summarize(list_metrics(sum_lists(d["dense"], d["bm25"])), "cos+BM25 直接相加 (bug)")
    if "ce" in d:
        ce = d["ce"]
        summarize(list_metrics(dense_lists(ce)), "cross-encoder 全部 90")
        for n in [3, 5, 10, 20, 30]:
            summarize(list_metrics(rerank_lists(L["dense"], ce, n)), f"dense → rerank@{n}")
            summarize(list_metrics(rerank_lists(L["rrf"], ce, n)), f"hybrid → rerank@{n}")
        L["rr"] = rerank_lists(L["rrf"], ce, 20)
        L["ce"] = ce
    for n in [5, 10, 20]:
        for x in ["dense", "bm25", "rrf"]:
            rec = np.mean([len(set(Q_GOLD[qi]) & set(L[x][qi][:n])) / len(Q_GOLD[qi]) for qi in range(len(Q_TEXT))])
            print(f"  candidate recall@{n} {x}: {rec:.3f}", end=";")
        print()
    print("\n== 每題標準答案的名次（dense / bm25 / rrf / rrf→rerank@20）==")
    keys = [x for x in ["dense", "bm25", "rrf", "rr"] if x in L]
    rows = {x: list_metrics(L[x]) for x in keys}
    for qi in range(len(Q_TEXT)):
        print(f"  Q{qi:02d} {Q_TYPE[qi]:4s} {Q_TEXT[qi]:22s} " + " ".join(f"{rows[x][qi]['rank']!s:>4}" for x in keys))
    for k in [1, 3]:
        print(f"\n== 切塊兩難（top-{k}；proc full＝步驟全部進到 prompt 的比例）==")
        coverage_summary(coverage_rows("child", L["dense"], k), "小塊（子句）")
        for s in WINDOW_SIZES:
            coverage_summary(coverage_rows("win", dense_lists(d[f"win{s}"]), k, s), f"固定 {s} 字")
        coverage_summary(coverage_rows("parent", L["dense"], k), "父子檢索")
        if "rr" in L:
            coverage_summary(coverage_rows("parent", L["rr"], k), "父子＋混合＋rerank")
    return vec, d, L


# ═════════════════════════════ LLM：hero 三個案例的真實回答 ═════════════════════════════
SYS_RAG = ("你是「拿鐵大師」咖啡機（LM-500／LM-500S／LM-700）的客服。請只根據下面提供的手冊段落回答使用者的問題；"
           "段落裡有相關內容就直接回答，完全找不到相關資訊時，才回答「手冊中沒有提到」。")


def build_context(kind, lst, k=3):
    """kind＝child：前 k 個子塊各成一段；parent：前 k 個子塊換成所在的整節（去重、保留先後）。"""
    if kind == "child":
        return [CHILDREN[i] for i in lst[:k]]
    secs = []
    for i in lst[:k]:
        if CHILD_SEC[i] not in secs:
            secs.append(CHILD_SEC[i])
    return [PARENTS[x] for x in secs]


def ask_llm(client, ctx, q):
    user = "手冊段落：\n" + "\n".join(f"【段落{j + 1}】{c}" for j, c in enumerate(ctx)) + f"\n\n問題：{q}"
    r = client.chat.completions.create(
        model=LLM_MODEL, temperature=0.0, max_tokens=600,
        messages=[{"role": "system", "content": SYS_RAG}, {"role": "user", "content": user}],
        extra_body={"chat_template_kwargs": {"enable_thinking": False}})
    return (r.choices[0].message.content or "").strip()


# hero「管線開關板」：3 題 × 父子／混合／rerank 三個開關的 8 種組合，每種組合的回答都真的問過一次
HERO_QS = [0, 16, 37]  # 除垢完整步驟（切塊兩難）、E07（型號）、摔到地上（換句話說）


def hero_list(L, hybrid, rerank):
    base = L["rrf"] if hybrid else L["dense"]
    return rerank_lists(base, L["ce"], 20) if rerank else base


# 每題的關鍵事實：回答裡出現任一個子字串就算「有講到」（客觀、可重現的檢查，不靠人工打分）
HERO_FACTS = {
    0: [("加一包 DC-300＋1 公升水", ["DC-300", "1 公升"]), ("長按沖煮鍵 5 秒進除垢模式", ["5 秒"]),
        ("除垢後跑清水循環", ["清水循環"]), ("裝回濾水芯", ["裝回濾水芯"])],
    16: [("E07＝研磨室堵塞", ["研磨室堵塞"]), ("拔插頭、用刷子清粉塊", ["刷子"])],
    37: [("摔落不在保固範圍", ["不在保固", "無法免費", "不保固", "不能免費"])],
}


def fact_check(qi, answer):
    return [any(v in answer for v in variants) for _, variants in HERO_FACTS[qi]]


def part_llm(out, L):
    from openai import OpenAI

    client = OpenAI(base_url=os.environ["LLM_URL"], api_key=os.environ.get("LLM_KEY", "none"))
    cache, traces = {}, []
    for qi in HERO_QS:
        combos = {}
        for parent in (0, 1):
            for hybrid in (0, 1):
                for rerank in (0, 1):
                    lst = hero_list(L, hybrid, rerank)[qi]
                    ctx = build_context("parent" if parent else "child", lst)
                    key = (qi, tuple(ctx))
                    if key not in cache:
                        a1, a2 = ask_llm(client, ctx, Q_TEXT[qi]), ask_llm(client, ctx, Q_TEXT[qi])
                        cache[key] = (a1, a1 == a2, a2)
                        print(f"\nQ{qi} p{parent}h{hybrid}r{rerank} top3={lst[:3]} same_twice={a1 == a2}")
                        print("  ctx:", " ／ ".join(c[:24] for c in ctx))
                        print("  ans:", a1.replace("\n", " ⏎ "))
                        if a1 != a2:
                            print("  ans2:", a2.replace("\n", " ⏎ "))
                    a1, same, _ = cache[key]
                    combos[f"{parent}{hybrid}{rerank}"] = {
                        "top3": lst[:3], "answer": a1, "stable": same, "facts": fact_check(qi, a1),
                        "hedge": a1.startswith("手冊中沒有提到"),
                        "ctx_chars": sum(len(c) for c in build_context("parent" if parent else "child", lst))}
        traces.append({"qi": qi, "q": Q_TEXT[qi], "gold": Q_GOLD[qi], "facts": [f for f, _ in HERO_FACTS[qi]],
                       "combos": combos})
        for k, v in combos.items():
            print(f"  Q{qi} {k} top3={v['top3']} facts={v['facts']} hedge={v['hedge']} stable={v['stable']}")
    (out / "hero_traces.json").write_text(json.dumps(traces, ensure_ascii=False, indent=1))
    print(f"\n{len(cache)} unique contexts asked (each twice)")
    return traces


# 課文引用的額外一問：E07 只取第 1 名時（向量 vs 混合），模型拿到什麼、回答什麼
EXTRA_CASES = [(16, "dense", 1), (16, "rrf", 1)]


def part_llm_extra(out, L):
    from openai import OpenAI

    client = OpenAI(base_url=os.environ["LLM_URL"], api_key=os.environ.get("LLM_KEY", "none"))
    rows = []
    for qi, lname, k in EXTRA_CASES:
        ctx = build_context("child", L[lname][qi], k)
        a1, a2 = ask_llm(client, ctx, Q_TEXT[qi]), ask_llm(client, ctx, Q_TEXT[qi])
        rows.append({"qi": qi, "list": lname, "k": k, "ctx": ctx, "answer": a1, "stable": a1 == a2})
        print(f"Q{qi} {lname} top-{k} ctx={[c[:20] for c in ctx]} same_twice={a1 == a2}\n  {a1!r}")
    (out / "llm_extra.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1))


# ═════════════════════════════ 測驗診斷題素材（真的跑出來的錯誤輸出）═════════════════════════════
def part_errors(out, d, L):
    print("\n== bug 1：父子檢索忘了去重 ==")
    lst = L["dense"][0][:3]
    buggy = [PARENTS[CHILD_SEC[i]] for i in lst]  # 沒去重
    user = "手冊段落：\n" + "\n".join(f"【段落{j + 1}】{c[:22]}…" for j, c in enumerate(buggy))
    print(user)
    print(f"  context chars: buggy={sum(len(x) for x in buggy)}  dedup={len(PARENTS[CHILD_SEC[lst[0]]])}")

    print("\n== bug 2：cosine 與 BM25 原始分數直接相加 ==")
    cos, bm = d["dense"], d["bm25"]
    print(f"  cosine range {cos.min():.2f}–{cos.max():.2f}；BM25 range {bm.min():.2f}–{bm.max():.2f}")
    raw = sum_lists(cos, bm)
    has = [qi for qi in range(len(Q_TEXT)) if L["bm25"][qi]]
    same1 = sum(raw[qi][0] == L["bm25"][qi][0] for qi in has)
    same3 = sum(raw[qi][:3] == L["bm25"][qi][:3] for qi in has if len(L["bm25"][qi]) >= 3)
    n3 = sum(len(L["bm25"][qi]) >= 3 for qi in has)
    print(f"  questions with BM25 hits: {len(has)}；raw-sum top-1 == BM25 top-1: {same1}/{len(has)}；"
          f"top-3 identical: {same3}/{n3}")
    qi = 31
    print(f"  例：{Q_TEXT[qi]}")
    for name, lst in (("dense", L["dense"][qi]), ("bm25", L["bm25"][qi]), ("raw-sum", raw[qi]), ("rrf", L["rrf"][qi])):
        print(f"    {name:8s}", " | ".join(("*" if i in Q_GOLD[qi] else "") + CHILDREN[i][:12] for i in lst[:3]))
    for name, lst in (("dense", L["dense"]), ("raw-sum", raw), ("rrf", L["rrf"])):
        summarize(list_metrics(lst), name)

    print("\n== bug 3：jina v5 沒加 Query:/Document: 前綴 ==")
    summarize(list_metrics(L["dense"]), "with prefixes")
    summarize(list_metrics(L["nopre"]), "without prefixes")

    print("\n== bug 4：bm25s 的 k 比語料還大 ==")
    import bm25s

    r = bm25s.BM25(method="lucene")
    r.index([tokenize(c) for c in CHILDREN], show_progress=False)
    try:
        r.retrieve([tokenize(Q_TEXT[16])], k=100, show_progress=False)
    except Exception as e:  # noqa: BLE001 — 就是要看真實錯誤訊息
        print(f"  {type(e).__name__}: {e}")


# ═════════════════════════════ grid：實驗場 5️⃣ 全部組合的格點搜尋（LEVEL 3 解答從這裡來）═════════════════════════════
def part_grid(d, L, min_hit1=38, min_single=31):
    hdr = dense_lists(d["hdr"])
    res = []
    for hd in (0, 1):
        dl = hdr if hd else L["dense"]
        for ret in ("dense", "bm25", "hybrid"):
            if ret == "bm25" and hd:
                continue
            base = {"dense": dl, "bm25": L["bm25"], "hybrid": rrf_lists(dl, L["bm25"])}[ret]
            for n in range(41):  # 0＝不 rerank
                lst = rerank_lists(base, L["ce"], n) if n else base
                h1 = sum(r["hit1"] for r in list_metrics(lst))
                for kind in ("child", "parent"):
                    for k in range(1, 6):
                        cov = coverage_rows(kind, lst, k)
                        pf = sum(r["full"] for r, t in zip(cov, Q_TYPE) if t == "proc")
                        sf = sum(r["full"] for r, t in zip(cov, Q_TYPE) if t != "proc")
                        res.append((hd, ret, n, kind, k, int(h1), int(pf), int(sf), float(np.mean([r["chars"] for r in cov]))))
    print(f"\n== 5️⃣ 格點搜尋：{len(res)} 種組合；最高 hit@1 = {max(r[5] for r in res)}/41 ==")
    ok = sorted([r for r in res if r[5] >= min_hit1 and r[6] == 8 and r[7] >= min_single], key=lambda r: r[8])
    print(f"  條件：hit@1 ≥ {min_hit1}、步驟題 8/8、其他題 ≥ {min_single}/33 → {len(ok)} 組；字數最少的前 8 組：")
    print("  (章節標題, 第一階段, rerank N, 交給模型, k) | hit@1 步驟 其他 平均字數")
    for r in ok[:8]:
        print(f"  {r[:5]} | {r[5]} {r[6]} {r[7]} {r[8]:.0f}")
    return res


# ═════════════════════════════ emit：課程要用的常數 ═════════════════════════════
def b64_i8(v):
    q, sc = quant_i8(v)
    return base64.b64encode(q.tobytes()).decode(), [float(f"{x:.6g}") for x in sc.ravel()]


def b64_i16(m, scale):
    return base64.b64encode(np.round(m * scale).astype(np.int16).tobytes()).decode()


def part_emit(out, vec, d, L, local):
    qb, qs = b64_i8(vec["q"])
    cb, cs = b64_i8(vec["child"])
    payload = {
        "sections": [[t, list(ss)] for t, ss in SECTIONS],
        "questions": [[q, t, g] for q, t, g in zip(Q_TEXT, Q_TYPE, Q_GOLD)],
        "q_b64": qb, "q_scales": qs, "c_b64": cb, "c_scales": cs,
        "hdr_b64": b64_i16(d["hdr"], 10000),
        "win_sizes": WINDOW_SIZES,
        "windows": {str(k): v for k, v in WINDOWS.items()},
        "win_b64": {str(k): b64_i16(d[f"win{k}"], 10000) for k in WINDOW_SIZES},
        "ce_b64": b64_i16(d["ce"], 1000),
        "embed_model": HF_EMBED if local else f"{EMBED_MODEL} ({HF_EMBED})",
        "rerank_model": HF_RERANK,
    }
    # 自我驗證：從 payload 解回來的矩陣，算出的指標與 spike 完全一致（瀏覽器拿到的就是這份）
    def i16(b, n, m, sc):
        return np.frombuffer(base64.b64decode(b), dtype=np.int16).reshape(n, m).astype(np.float64) / sc

    nq, nc = len(Q_TEXT), len(CHILDREN)
    assert np.array_equal(i16(payload["ce_b64"], nq, nc, 1000), d["ce"] * 1.0) or \
        np.abs(i16(payload["ce_b64"], nq, nc, 1000) - d["ce"]).max() < 1e-9
    ce2 = i16(payload["ce_b64"], nq, nc, 1000)
    assert [r["rank"] for r in list_metrics(rerank_lists(L["rrf"], ce2, 20))] == \
        [r["rank"] for r in list_metrics(rerank_lists(L["rrf"], d["ce"], 20))]
    hero = out / "hero_traces.json"
    if hero.exists():
        payload["hero"] = json.loads(hero.read_text())
    (out / "payload.json").write_text(json.dumps(payload, ensure_ascii=False))
    print(f"payload.json: {len(json.dumps(payload)) / 1024:.0f} KB（q/c 向量 b64 {(len(qb) + len(cb)) / 1024:.0f} KB）")


# ═════════════════════════════ inject：把 payload 寫進課程檔 ═════════════════════════════
def part_inject(out):
    """payload.json → lesson.py 的 DATA BEGIN/END 區塊、page_content.py 的 HERO_DATA 區塊（可重跑）。"""
    root = Path(__file__).resolve().parent.parent / "genai-rag-advanced"
    p = json.loads((out / "payload.json").read_text())

    def chunks(s, n=96):
        return [s[i : i + n] for i in range(0, len(s), n)]

    def b64_lit(name, s, ind="    "):
        parts = "\n".join(f'{ind}    "{c}"' for c in chunks(s))
        return f"{ind}{name} = (\n{parts}\n{ind})"

    I = "    "
    lines = [f"{I}# ── DATA BEGIN（由 _spikes/spike_genai_rag_advanced.py --part emit 產生；勿手改，重產方式見 NOTES.md）──"]
    lines.append(f"{I}# 手冊：20 節（父塊）× 每節幾句（子塊）。虛構教材，模型不可能背過。")
    lines.append(f"{I}SECTIONS = [")
    for title, sents in p["sections"]:
        lines.append(f"{I}    ({title!r}, [")
        for s in sents:
            lines.append(f"{I}        {s!r},")
        lines.append(f"{I}    ]),")
    lines.append(f"{I}]")
    lines.append(f"{I}# 考卷：(問題, 題型, 標準答案＝第幾個子塊)；proc＝步驟題 pin＝單點題 kw＝型號／故障碼 para＝換句話說")
    lines.append(f"{I}QUESTIONS = [")
    for q, t, g in p["questions"]:
        lines.append(f"{I}    ({q!r}, {t!r}, {g!r}),")
    lines.append(f"{I}]")
    lines.append(f"{I}# 真向量：{p['embed_model']}，1024 維，int8 對稱量化（每向量一個 scale）")
    lines.append(b64_lit("Q_B64", p["q_b64"]))
    lines.append(f"{I}Q_SCALES = {p['q_scales']!r}")
    lines.append(b64_lit("C_B64", p["c_b64"]))
    lines.append(f"{I}C_SCALES = {p['c_scales']!r}")
    lines.append(f"{I}# 預先算好的相似度矩陣（int16，÷10000）：子塊前面加上章節標題再算向量的版本、固定大小切塊的版本")
    lines.append(b64_lit("HDR_B64", p["hdr_b64"]))
    lines.append(f"{I}WIN_SIZES = {p['win_sizes']!r}")
    lines.append(f"{I}WINDOWS = {{")
    for k, v in p["windows"].items():
        lines.append(f"{I}    {int(k)}: {v!r},")
    lines.append(f"{I}}}")
    lines.append(f"{I}WIN_B64 = {{")
    for k, v in p["win_b64"].items():
        parts = "\n".join(f'{I}        "{c}"' for c in chunks(v))
        lines.append(f"{I}    {int(k)}: (\n{parts}\n{I}    ),")
    lines.append(f"{I}}}")
    lines.append(f"{I}# cross-encoder（{p['rerank_model']}）對「每題 × 每個子塊」的實測分數（logit，int16 ÷1000），CPU 上事先算好")
    lines.append(b64_lit("CE_B64", p["ce_b64"]))
    lines.append(f"{I}# ── DATA END ──")
    block = "\n".join(lines)

    lp = root / "lesson.py"
    src = lp.read_text()
    pat = re.compile(r"    # ── DATA BEGIN.*?    # ── DATA END ──", re.DOTALL)
    assert pat.search(src), "lesson.py 找不到 DATA BEGIN/END 標記"
    src = pat.sub(lambda _m: block, src)
    lp.write_text(src)
    print(f"lesson.py: data block {len(block) / 1024:.0f} KB")

    # ── hero 資料：只留頁面要顯示的欄位 ──
    children, titles, csec = [], [], []
    for s, (title, sents) in enumerate(p["sections"]):
        titles.append(title)
        for t in sents:
            children.append(t)
            csec.append(s)
    hero = []
    for c in p.get("hero", []):
        gold = set(c["gold"])
        combos = {}
        for key, v in c["combos"].items():
            secs = []
            for i in v["top3"]:
                if csec[i] not in secs:
                    secs.append(csec[i])
            parent_on = key[0] == "1"
            got = [g for g in c["gold"] if (csec[g] in secs if parent_on else g in v["top3"])]
            combos[key] = {
                "gin": len(got), "gn": len(gold), "miss": [children[g] for g in c["gold"] if g not in got],
                "top3": [[children[i], i in gold, titles[csec[i]]] for i in v["top3"]],
                "secs": [titles[x] for x in secs],
                "chars": v["ctx_chars"],
                "ans": v["answer"],
                "facts": v["facts"],
                "hedge": v["hedge"],
                "stable": v["stable"],
            }
        hero.append({"q": c["q"], "facts": c["facts"], "combos": combos})
    pp = root / "page_content.py"
    if pp.exists():
        t = pp.read_text()
        pat2 = re.compile(r"/\* HERO_DATA_BEGIN \*/.*?/\* HERO_DATA_END \*/", re.DOTALL)
        if pat2.search(t):
            t = pat2.sub(lambda _m: "/* HERO_DATA_BEGIN */\n  const HERO = " + json.dumps(hero, ensure_ascii=False)
                         + ";\n  /* HERO_DATA_END */", t)
            pp.write_text(t)
            print(f"page_content.py: hero data {len(json.dumps(hero, ensure_ascii=False)) / 1024:.0f} KB")
        else:
            print("page_content.py 沒有 HERO_DATA 標記，略過")


# ═════════════════════════════ main ═════════════════════════════
if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--part", default="embed,bm25,rerank,eval,llm,llm_extra,errors,grid,emit,inject")
    ap.add_argument("--local", action="store_true", help="用本機 CPU 的開源模型算向量（不需要任何服務）")
    ap.add_argument("--out", default="rag_adv_out")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    parts = a.part.split(",")
    print(f"corpus: {len(SECTIONS)} sections, {len(CHILDREN)} children, {len(UNITS)} units, "
          f"{sum(len(u) for u in UNITS)} chars; windows: "
          + ", ".join(f"{s}->{len(w)}" for s, w in WINDOWS.items()) + f"; questions: {len(QUESTIONS)}")
    if "embed" in parts:
        part_embed(out, a.local)
    if "bm25" in parts:
        part_bm25()
    if "rerank" in parts:
        part_rerank(out)
    L = None
    if any(x in parts for x in ("eval", "llm", "llm_extra", "errors", "grid", "emit")):
        _vec, _d, L = part_eval(out, a.local)
    if "llm" in parts:
        part_llm(out, L)
    if "llm_extra" in parts:
        part_llm_extra(out, L)
    if "errors" in parts:
        part_errors(out, _d, L)
    if "grid" in parts:
        part_grid(_d, L)
    if "emit" in parts:
        part_emit(out, _vec, _d, L, a.local)
    if "inject" in parts:
        part_inject(out)
