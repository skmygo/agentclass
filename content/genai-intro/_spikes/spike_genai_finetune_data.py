# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""genai-finetune 共用：資料集產生器＋評分函式（純標準庫，不需要 GPU、不需要任何服務）。

任務：把「客服訊息」轉成固定 schema 的工單 JSON——SFT 最典型的「教格式、教行為」用途。
資料是程式用模板組出來的虛構訊息（固定 seed，任何人重跑都得到同一份），
標籤由模板直接決定，所以 100% 正確。測試集刻意用**訓練時沒看過的句型與產品**，
考的是「學會規則」而不是「背下答案」。

用法：
  uv run --script content/genai-intro/_spikes/spike_genai_finetune_data.py            # 印統計＋範例
  uv run --script content/genai-intro/_spikes/spike_genai_finetune_data.py --out DIR  # 寫 train/test JSONL

被兩支訓練腳本 import（同目錄）：build_dataset()、SYSTEM_SHORT、SYSTEM_DETAILED、score()。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
from pathlib import Path

SEED = 3407
CATEGORIES = ["repair", "return", "billing", "howto", "shipping"]
KEYS = ["category", "product", "urgent", "summary"]

# 訓練與推論共用的短 system prompt（微調後只靠這一句）
SYSTEM_SHORT = "你是客服工單助理。把使用者訊息轉成 JSON 工單。"
# 「寫清楚的 prompt」對照組：把 schema 與列舉值全寫出來（不微調，只靠 prompt）
SYSTEM_DETAILED = (
    "你是客服工單助理。把使用者訊息轉成 JSON 工單，只輸出 JSON、不要輸出任何其他文字。\n"
    '格式：{"category": 類別, "product": 產品名, "urgent": true 或 false, "summary": 一句話摘要}\n'
    "category 只能是 repair（故障報修）、return（退換貨）、billing（帳務）、"
    "howto（使用諮詢）、shipping（物流）之一。\n"
    "product 照抄訊息裡的產品型號（例如 AirWave 3）。"
    "urgent：訊息表達很急、要求馬上處理時為 true，否則 false。"
)

# 產品：型號 → 品類（決定能套哪些問題）。最後兩個只出現在測試集
TRAIN_PRODUCTS = {
    "AirWave 3": "earbuds",
    "CleanBot S2": "robot",
    "BrewMaster 500": "coffee",
    "FitBand 5": "band",
    "PowerCube 20K": "powerbank",
    "ZoomPad 11": "tablet",
    "SwiftMouse X": "mouse",
    "PureAir 300": "purifier",
}
TEST_ONLY_PRODUCTS = {"NovaWatch 2": "band", "MeshLink AX": "router"}
NOUN = {
    "earbuds": "耳機", "robot": "掃地機器人", "coffee": "咖啡機", "band": "手環",
    "powerbank": "行動電源", "tablet": "平板", "mouse": "滑鼠", "purifier": "清淨機",
    "router": "路由器",
}
FAULTS = {
    "earbuds": ["左耳沒有聲音", "充不進電", "藍牙一直斷線"],
    "robot": ["輪子卡住不會動", "一直原地打轉", "吸力變得很弱"],
    "coffee": ["不出水", "一直漏水", "開不了機"],
    "band": ["螢幕不會亮", "心率一直抓不到", "充電座接觸不良"],
    "powerbank": ["充到一半就斷電", "外殼發燙", "指示燈全部不亮"],
    "tablet": ["觸控失靈", "螢幕有一條綠線", "一直自動重開機"],
    "mouse": ["左鍵連點", "滾輪亂跳", "接收器抓不到"],
    "purifier": ["濾網燈一直閃", "運轉聲音很大", "按鍵沒反應"],
    "router": ["一直斷網", "指示燈閃紅燈", "5G 訊號消失"],
}
HOWTO = {
    "earbuds": ["配對新手機", "切換降噪模式"], "robot": ["設定清掃排程", "連上家裡 Wi-Fi"],
    "coffee": ["調整咖啡濃度", "做除垢"], "band": ["開啟睡眠偵測", "更新韌體"],
    "powerbank": ["開啟快充", "看剩餘電量"], "tablet": ["分割畫面", "備份資料"],
    "mouse": ["調整 DPI", "設定巨集"], "purifier": ["設定定時關機", "重設濾網提醒"],
    "router": ["改 Wi-Fi 密碼", "開訪客網路"],
}
RETURN_WHY = ["顏色跟網頁上差很多", "收到時外盒破損", "買錯型號", "用了三天覺得不適合"]
BILLING_ISSUE = ["被重複扣款兩次", "發票一直沒收到", "退款還沒入帳", "分期期數跟說好的不一樣"]
SHIP_ISSUE = ["訂了五天還沒收到", "物流狀態卡住不動", "想改收件地址", "收到的數量少一個"]

URGENT_CUES = [
    "明天就要出國了，拜託盡快！", "急！今天一定要處理。", "這已經是第三次了，請馬上處理。",
    "小孩明天考試要用，很急。", "工作要用，拜託越快越好！",
]
CALM_CUES = ["", "", "", "不急，有空再回覆就好。", "麻煩了，謝謝。"]

# 句型：train 用前面幾個，test 用最後一個（訓練時沒看過的說法）
T = {
    "repair": [
        "我的 {p} {x}，可以幫忙修嗎？{u}",
        "{p} 用不到一個月就{x}，請問要怎麼送修？{u}",
        "你好，我買的{n} {p} {x}，保固內能處理嗎？{u}",
        "{u}{p} {x}了，怎麼辦",
        "請問 {p} {x}是正常的嗎？是不是壞掉了？{u}",
    ],
    "return": [
        "我想退貨，{p} {x}。{u}",
        "{p} 可以換貨嗎？因為{x}。{u}",
        "上週收到的{n} {p}，{x}，想申請退換。{u}",
        "{u}請問 {p} {x}的話可以退嗎",
        "{p} 我不想要了，{x}，要怎麼辦理退貨？{u}",
    ],
    "billing": [
        "買 {p} 的時候{x}，請幫我查一下。{u}",
        "你好，我訂的 {p} {x}。{u}",
        "{u}{p} 那筆訂單{x}，怎麼回事？",
        "請問 {p} 的訂單{x}要找誰處理？{u}",
        "關於 {p}：{x}，麻煩確認。{u}",
    ],
    "howto": [
        "請問 {p} 要怎麼{x}？{u}",
        "{p} 的{x}在哪裡設定？{u}",
        "新買的{n} {p}，不知道怎麼{x}。{u}",
        "{u}想問一下 {p} 如何{x}",
        "{p} 有辦法{x}嗎？說明書看不太懂。{u}",
    ],
    "shipping": [
        "我的 {p} {x}，可以幫忙查嗎？{u}",
        "{p} 的包裹{x}。{u}",
        "{u}訂的{n} {p} {x}，請協助。",
        "請問 {p} {x}怎麼處理？{u}",
        "查一下 {p} 的物流，{x}。{u}",
    ],
}
SUMMARY = {
    "repair": "{p} {x}",
    "return": "{p} 申請退換：{x}",
    "billing": "{p} 訂單{x}",
    "howto": "詢問 {p} 如何{x}",
    "shipping": "{p} {x}",
}


def _issues(cat: str, kind: str) -> list[str]:
    return {
        "repair": FAULTS[kind], "howto": HOWTO[kind], "return": RETURN_WHY,
        "billing": BILLING_ISSUE, "shipping": SHIP_ISSUE,
    }[cat]


def _make(rng: random.Random, cat: str, product: str, kind: str, tmpl: str) -> dict:
    x = rng.choice(_issues(cat, kind))
    urgent = rng.random() < 0.35
    cue = rng.choice(URGENT_CUES) if urgent else rng.choice(CALM_CUES)
    user = tmpl.format(p=product, x=x, n=NOUN[kind], u=cue).strip()
    ticket = {"category": cat, "product": product, "urgent": urgent,
              "summary": SUMMARY[cat].format(p=product, x=x)}
    return {
        "messages": [
            {"role": "system", "content": SYSTEM_SHORT},
            {"role": "user", "content": user},
            {"role": "assistant", "content": json.dumps(ticket, ensure_ascii=False)},
        ],
        "label": ticket,
    }


def _with_history(rng: random.Random, row: dict, pool: list[str], long_ctx: int) -> dict:
    """長序列情境：在最新訊息前面墊一段「這位客戶先前的對話紀錄」（約 long_ctx 個字）。
    標籤不變（只看最新訊息）——用來量「序列變長時，工具之間的 VRAM／速度差」。"""
    hist, n = [], 0
    while n < long_ctx:
        line = f"客戶：{rng.choice(pool)}\n客服：已收到，我們會盡快為您處理。"
        hist.append(line)
        n += len(line)
    user = "以下是這位客戶先前的對話紀錄：\n" + "\n".join(hist) + "\n\n最新訊息：" + row["messages"][1]["content"]
    msgs = [row["messages"][0], {"role": "user", "content": user}, row["messages"][2]]
    return {"messages": msgs, "label": row["label"]}


def build_dataset(n_train: int = 480, n_test: int = 40, long_ctx: int = 0) -> tuple[list[dict], list[dict]]:
    """回傳 (train, test)。train 只用前 4 種句型＋8 個產品；test 用第 5 種句型，一半是沒看過的產品。
    long_ctx>0 時每筆前面墊約 long_ctx 字的歷史對話（長序列情境，同一組標籤）。"""
    rng = random.Random(SEED)
    train = []
    prods = list(TRAIN_PRODUCTS.items())
    for i in range(n_train):
        cat = CATEGORIES[i % len(CATEGORIES)]
        product, kind = rng.choice(prods)
        train.append(_make(rng, cat, product, kind, rng.choice(T[cat][:4])))
    rng.shuffle(train)
    test = []
    unseen = list(TEST_ONLY_PRODUCTS.items())
    for i in range(n_test):
        cat = CATEGORIES[i % len(CATEGORIES)]
        product, kind = rng.choice(unseen if i % 2 else prods)
        test.append(_make(rng, cat, product, kind, T[cat][4]))
    if long_ctx:
        pool = [r["messages"][1]["content"] for r in train]
        hrng = random.Random(SEED + 1)
        train = [_with_history(hrng, r, pool, long_ctx) for r in train]
        test = [_with_history(hrng, r, pool, long_ctx) for r in test]
    return train, test


def dataset_fingerprint(rows: list[dict]) -> str:
    blob = "\n".join(json.dumps(r["messages"], ensure_ascii=False) for r in rows)
    return hashlib.sha256(blob.encode()).hexdigest()[:12]


def score(output: str, label: dict) -> dict:
    """嚴格評分：輸出必須「整段就是 JSON」（生產管線 json.loads 直接吃的那種）。"""
    out = output.strip()
    res = {"json_ok": False, "schema_ok": False, "category": False, "product": False,
           "urgent": False, "all": False}
    try:
        obj = json.loads(out)
    except Exception:
        return res
    res["json_ok"] = isinstance(obj, dict)
    if not res["json_ok"]:
        return res
    res["schema_ok"] = (sorted(obj) == sorted(KEYS) and obj.get("category") in CATEGORIES
                        and isinstance(obj.get("urgent"), bool))
    res["category"] = obj.get("category") == label["category"]
    res["product"] = obj.get("product") == label["product"]
    res["urgent"] = obj.get("urgent") is label["urgent"]
    res["all"] = res["schema_ok"] and res["category"] and res["product"] and res["urgent"]
    return res


def summarize(scores: list[dict]) -> dict:
    n = len(scores)
    return {k: sum(s[k] for s in scores) for k in scores[0]} | {"n": n}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", help="寫出 train.jsonl / test.jsonl 的目錄")
    a = ap.parse_args()
    train, test = build_dataset()
    print(f"train={len(train)} test={len(test)} fp(train)={dataset_fingerprint(train)} "
          f"fp(test)={dataset_fingerprint(test)}")
    from collections import Counter
    print("train categories:", Counter(r["label"]["category"] for r in train))
    print("train urgent:", sum(r["label"]["urgent"] for r in train))
    print("test urgent:", sum(r["label"]["urgent"] for r in test))
    print("test unseen products:", sum(r["label"]["product"] in TEST_ONLY_PRODUCTS for r in test))
    for r in train[:3] + test[:3]:
        print(json.dumps(r["messages"][1:], ensure_ascii=False))
    if a.out:
        d = Path(a.out)
        d.mkdir(parents=True, exist_ok=True)
        for name, rows in (("train", train), ("test", test)):
            with open(d / f"{name}.jsonl", "w", encoding="utf-8") as f:
                for r in rows:
                    f.write(json.dumps({"messages": r["messages"]}, ensure_ascii=False) + "\n")
        print("wrote", d)


if __name__ == "__main__":
    main()
