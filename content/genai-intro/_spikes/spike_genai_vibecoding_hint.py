# /// script
# requires-python = ">=3.11"
# dependencies = ["openai", "pytest"]
# ///
"""genai-vibecoding 課的第五種下一步：人親自診斷（接在主實驗後面跑，與主實驗配對）。

讀主實驗（spike_genai_vibecoding.py）的輸出，拿**同一份第 1 版**，在同一段對話裡貼回 pytest 錯誤原文，
外加一句「人看完失敗測試後寫的診斷」（不給程式碼，只講哪裡錯、應該怎樣）。最多再試 3 次，
評分一樣用完整測試。對照組就是主實驗的 full（只貼錯誤原文）——差別只有那一句診斷。

呼應 Olausson et al.（ICLR 2024）"Is Self-Repair a Silver Bullet for Code Generation?"：
自我修復的瓶頸是回饋品質，換成更好的回饋（強模型或人寫的）才有明顯提升。

端點與參數同主實驗（LLM_URL／LLM_MODEL／LLM_API_KEY）。
跑法：uv run --script content/genai-intro/_spikes/spike_genai_vibecoding_hint.py <主實驗.json> [out.json]
輸出：主實驗 JSON 的每個 task 多一個 branches["hint"]（寫到 out.json，預設覆寫主實驗 JSON 的副本）。
"""

import importlib.util
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

_spec = importlib.util.spec_from_file_location("vibe", Path(__file__).with_name("spike_genai_vibecoding.py"))
vibe = importlib.util.module_from_spec(_spec)
sys.modules["vibe"] = vibe
_spec.loader.exec_module(vibe)

# 人看完失敗的測試後，會對 AI 說的一句話（診斷，不是程式碼）
HINTS = {
    "split_bill": "金額加總要剛好等於 total：除不盡的零頭讓排在前面的人各多付 1 元（100 元 3 人是 [34, 33, 33]）；n 小於等於 0 要 raise ValueError。",
    "round_half_up": "負數要遠離 0 進位（-2.5 → -3、-1.6 → -2），所以不能用 int(x + 0.5)；Python 內建的 round() 是銀行家捨入（2.5 → 2），也不能用。",
    "compare_versions": "每一段要轉成整數再比（'1.10' 比 '1.9' 新），段數不同時缺的段當成 0（'1.0' 等於 '1.0.0'）。",
    "parse_duration": "h、m、s 三段都可以省略但順序固定（'1h5s'、'90m' 都合法）；空字串或出現其他字元（像 '5x'）要 raise ValueError。",
    "normalize_tw_mobile": "先拿掉空白、'-'、括號；只有「09 開頭共 10 碼」或「886／+886 開頭再接 9 開頭的 9 碼」合法，其他（市話 02、位數不對）要 raise ValueError。",
    "format_bytes": "小於 1024 寫成 '512 B'（整數、不加小數），其他保留 1 位小數；單位最大到 TB（1024 TB 就寫 '1024.0 TB'）；負數要 raise ValueError。",
    "top_k_words": "只算英文字母、全部轉小寫、標點不算；回傳 list of (字, 次數) 的 tuple，次數相同時照字母順序；空字串回傳 []。",
    "slugify": "所有非英數字元（空白、標點、中文）都當分隔，連續的分隔只留一個 '-'，頭尾不能有 '-'（'C++ & Python' → 'c-python'）。",
    "merge_intervals": "先依起點排序；端點相接（[1,2] 和 [2,3]）也要合併；合併時結尾取兩者較大的（[1,10] 包住 [2,3]）；空清單回傳 []。",
    "business_days": "頭尾兩天都要算進去（週一到週五是 5 天、同一天是週間就算 1 天），開始日晚於結束日回傳 0。",
    "rle_encode": "不相鄰的相同字元要分開算（'aabbaa' → 'a2b2a2'），所以不能用 Counter；空字串回傳 ''。",
    "mask_email": "帳號長度 3 以上保留頭尾各 1 個字、中間全換成 '*'；長度 2 以下只保留第一個字、其餘換成 '*'；沒有 '@' 或有多個 '@' 要 raise ValueError。",
}
HINT_MSG = vibe.FULL_MSG + "\n我看了失敗的測試，問題在：{hint}"


def one(t):
    p = next(q for q in vibe.PROBLEMS if q["name"] == t["problem"])
    first = dict(t["branches"]["full"][0])
    first.pop("feedback", None)
    attempts = [first]
    if first["grade"]["all"]:
        return attempts
    g, out = vibe.grade(first["code"], p)
    msgs = [{"role": "system", "content": vibe.SYSTEM}, {"role": "user", "content": p["prompt"]},
            {"role": "assistant", "content": "```python\n" + first["code"] + "```"}]
    seed0 = 1000 * vibe.PROBLEMS.index(p) + 10 * t["run"]
    for k in range(2, vibe.MAX_ATTEMPTS + 1):
        if g["all"]:
            break
        fb = HINT_MSG.format(out=vibe.trim(out), hint=HINTS[p["name"]])
        attempts[-1]["feedback"] = fb
        msgs = msgs + [{"role": "user", "content": fb}]
        raw, sec, ntok = vibe.chat(msgs, seed0 + k + 500)
        msgs = msgs + [{"role": "assistant", "content": raw}]
        code = vibe.extract_code(raw)
        g, out = vibe.grade(code, p)
        attempts.append({"code": code, "grade": g, "sec": round(sec, 1), "tokens": ntok[0], "finish": ntok[1]})
    print(f"  {p['name']:<20} run{t['run']} full:{len(t['branches']['full'])}"
          f"{'✓' if t['branches']['full'][-1]['grade']['all'] else '✗'} "
          f"hint:{len(attempts)}{'✓' if attempts[-1]['grade']['all'] else '✗'}", flush=True)
    return attempts


def main():
    src = Path(sys.argv[1])
    dst = Path(sys.argv[2]) if len(sys.argv) > 2 else src
    d = json.loads(src.read_text(encoding="utf-8"))
    with ThreadPoolExecutor(vibe.CONCURRENCY) as ex:
        hints = list(ex.map(one, d["tasks"]))
    for t, h in zip(d["tasks"], hints):
        t["branches"]["hint"] = h
    d["meta"]["hint_msg"] = HINT_MSG
    d["meta"]["hints"] = HINTS
    runs = d["meta"]["runs"]
    for cond in ("full", "hint"):
        per = [sum(t["branches"][cond][-1]["grade"]["all"] for t in d["tasks"] if t["run"] == r) for r in range(runs)]
        print(f"{cond:<5} 試到第 4 次全過題數，各 run：{per}（min {min(per)} / max {max(per)}）")
    dst.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"wrote {dst}\n\nSPIKE OK: genai-vibecoding hint")


if __name__ == "__main__":
    main()
