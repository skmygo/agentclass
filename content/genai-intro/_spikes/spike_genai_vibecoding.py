# /// script
# requires-python = ">=3.11"
# dependencies = ["openai", "pytest"]
# ///
"""genai-vibecoding 課的定軌 spike：讓測試當 AI 的眼睛——回饋迴圈實驗。

像 vibe coding 一樣只給**一句話需求**（12 道小程式題），細節要求（邊界情況、格式、錯誤處理）
只寫在測試裡——就像真實世界裡，細節只存在你腦中。同一個小模型，比較「第一版沒過之後」的四種下一步：
  第 1 次嘗試（四種條件共用同一份）→ 若沒全過，最多再試 3 次：
    reroll：開新對話重抽一次（不給任何回饋，測試只負責判定哪一版過關）
    bare  ：同一段對話裡只說「測試沒過，請修正」（懶人版 vibe：「不能動，再來」）
    full  ：同一段對話裡貼回 pytest 的失敗輸出原文（完整測試：基本＋邊界）
    weak  ：也貼 pytest 原文，但只跑「基本測試」——邊界測試對 AI 是看不見的，基本全綠就停手
  評分一律用完整測試（基本＋邊界）。

AI 寫的程式在子行程裡執行：暫存目錄、timeout、rlimit（CPU／記憶體／檔案大小）、
conftest 封鎖 socket、環境變數清空。這不是資安等級的隔離（本機 AppArmor 擋掉了
unprivileged user namespace，bwrap／unshare 都不能用），只是讓「跑陌生程式」不碰 repo、不連網、不卡死。

端點從 env 讀（OpenAI 相容 API；預設是本機 Ollama）：
  LLM_URL     預設 http://localhost:11434/v1
  LLM_MODEL   預設 qwen3.5-2b（Ollama 請設 qwen3.5:2b）
  LLM_API_KEY 預設 none
  RUNS        每題重跑幾次（預設 8）
跑法：uv run --script content/genai-intro/_spikes/spike_genai_vibecoding.py [out.json]
輸出：out.json（預設 ./spike_genai_vibecoding_out.json）＋終端機摘要。
"""

import json
import os
import re
import resource
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from openai import OpenAI

LLM_URL = os.environ.get("LLM_URL", "http://localhost:11434/v1")
MODEL = os.environ.get("LLM_MODEL", "qwen3.5-2b")
RUNS = int(os.environ.get("RUNS", "8"))
MAX_ATTEMPTS = 4          # 第 1 次 + 最多修 3 次
TEMPERATURE, TOP_P = 0.7, 0.8
CONCURRENCY = 4           # 區網模型的併發上限
client = OpenAI(base_url=LLM_URL, api_key=os.environ.get("LLM_API_KEY", "none"), timeout=180)

SYSTEM = (
    "你是 Python 程式設計師。依照使用者給的函式規格寫出實作。"
    "只輸出一個 ```python 程式碼區塊（完整的函式，需要的 import 寫在區塊裡），不要輸出任何說明文字。"
)
BARE_MSG = "測試沒有全部通過，請修正程式後重新輸出完整程式碼。"
FULL_MSG = "我跑了測試，結果如下。請根據失敗訊息修正程式，重新輸出完整程式碼。\n```\n{out}\n```"

# ── 題目：vibe 風格的一句話需求（給 AI 看）＋測試資料（細節要求都在測試裡）──
# basic＝快樂路徑（跟需求裡的例子同一類）；edge＝需求沒講、但你心裡其實有答案的細節。
# 測試資料是 (參數 tuple, 期望值) 或 (參數 tuple, {"raises": "ValueError"})
R = {"raises": "ValueError"}
PROBLEMS = [
    {"name": "split_bill", "prompt": "寫一個 Python 函式 split_bill(total: int, n: int) -> list[int]："
         "把 total 元平分給 n 個人，回傳每個人要付的金額（整數元）。",
         "basic": [((300, 3), [100, 100, 100]), ((10, 2), [5, 5])],
         "edge": [((100, 3), [34, 33, 33]), ((5, 3), [2, 2, 1]), ((2, 4), [1, 1, 0, 0]), ((10, 0), R)]},
    {"name": "round_half_up", "prompt": "寫一個 Python 函式 round_half_up(x: float) -> int：把 x 四捨五入成整數。",
         "basic": [((1.4,), 1), ((1.6,), 2), ((3.0,), 3)],
         "edge": [((2.5,), 3), ((0.5,), 1), ((-2.5,), -3), ((-1.6,), -2)]},
    {"name": "compare_versions", "prompt": "寫一個 Python 函式 compare_versions(a: str, b: str) -> int："
         "比較兩個版本號字串（像 '1.2.3'），a 比較新回傳 1、比較舊回傳 -1、一樣回傳 0。",
         "basic": [(("1.2", "1.3"), -1), (("2.0", "1.9"), 1), (("1.0", "1.0"), 0)],
         "edge": [(("1.10", "1.9"), 1), (("1.0", "1.0.0"), 0), (("1.0.1", "1"), 1), (("1.2.10", "1.2.9"), 1)]},
    {"name": "parse_duration", "prompt": "寫一個 Python 函式 parse_duration(s: str) -> int："
         "把像 '1h30m'、'45s' 這種時間長度字串轉成秒數。",
         "basic": [(("1h30m",), 5400), (("45s",), 45), (("2h",), 7200)],
         "edge": [(("1h5s",), 3605), (("90m",), 5400), (("",), R), (("5x",), R)]},
    {"name": "normalize_tw_mobile", "prompt": "寫一個 Python 函式 normalize_tw_mobile(s: str) -> str："
         "把台灣手機號碼轉成國際格式，例如 '0912-345-678' → '+886912345678'。",
         "basic": [(("0912345678",), "+886912345678"), (("0912-345-678",), "+886912345678")],
         "edge": [(("+886 912 345 678",), "+886912345678"), (("886-912-345-678",), "+886912345678"),
               (("(0912) 345 678",), "+886912345678"), (("0212345678",), R), (("091234567",), R)]},
    {"name": "format_bytes", "prompt": "寫一個 Python 函式 format_bytes(n: int) -> str："
         "把位元組數轉成人類好讀的字串，例如 1536 → '1.5 KB'。",
         "basic": [((1536,), "1.5 KB"), ((3 * 1024**2,), "3.0 MB")],
         "edge": [((512,), "512 B"), ((1024,), "1.0 KB"), ((1024**5,), "1024.0 TB"), ((-1,), R)]},
    {"name": "top_k_words", "prompt": "寫一個 Python 函式 top_k_words(text: str, k: int) -> list[tuple[str, int]]："
         "回傳一段英文裡出現最多次的 k 個字和它們的次數。",
         "basic": [(("dog dog cat", 2), [("dog", 2), ("cat", 1)]), (("the cat and the hat", 1), [("the", 2)])],
         "edge": [(("b a b a c", 2), [("a", 2), ("b", 2)]), (("Hello, hello! HELLO world.", 2), [("hello", 3), ("world", 1)]),
               (("", 3), [])]},
    {"name": "slugify", "prompt": "寫一個 Python 函式 slugify(title: str) -> str："
         "把文章標題轉成網址用的 slug，例如 'Hello World' → 'hello-world'。",
         "basic": [(("Hello World",), "hello-world"), (("AI 101",), "ai-101")],
         "edge": [(("Hello,  World!!",), "hello-world"), (("  --Vibe Coding--  ",), "vibe-coding"),
               (("你好 World",), "world"), (("C++ & Python",), "c-python")]},
    {"name": "merge_intervals", "prompt": "寫一個 Python 函式 merge_intervals(intervals: list[list[int]]) -> list[list[int]]："
         "合併重疊的區間。",
         "basic": [(([[1, 3], [2, 6], [8, 10]],), [[1, 6], [8, 10]]), (([[1, 2]],), [[1, 2]])],
         "edge": [(([],), []), (([[8, 10], [1, 3]],), [[1, 3], [8, 10]]), (([[1, 2], [2, 3]],), [[1, 3]]),
               (([[1, 10], [2, 3]],), [[1, 10]])]},
    {"name": "business_days", "prompt": "寫一個 Python 函式 business_days(start: str, end: str) -> int："
         "計算兩個日期（'YYYY-MM-DD'）之間有幾個工作天（週一到週五）。",
         "basic": [(("2026-09-19", "2026-09-26"), 5), (("2026-09-05", "2026-09-13"), 5)],
         "edge": [(("2026-09-21", "2026-09-25"), 5), (("2026-09-21", "2026-09-21"), 1),
               (("2026-09-26", "2026-09-27"), 0), (("2026-09-28", "2026-09-21"), 0)]},
    {"name": "rle_encode", "prompt": "寫一個 Python 函式 rle_encode(s: str) -> str："
         "做連續字元壓縮，例如 'aaabcc' → 'a3b1c2'。",
         "basic": [(("aaabcc",), "a3b1c2"), (("xyz",), "x1y1z1")],
         "edge": [(("",), ""), (("aabbaa",), "a2b2a2"), (("a" * 12,), "a12"), (("哈哈哈嗯",), "哈3嗯1")]},
    {"name": "mask_email", "prompt": "寫一個 Python 函式 mask_email(email: str) -> str："
         "把 email 的帳號部分遮起來保護隱私，例如 'john.doe@example.com' → 'j******e@example.com'。",
         "basic": [(("john.doe@example.com",), "j******e@example.com"), (("alice@test.org",), "a***e@test.org")],
         "edge": [(("bob@x.com",), "b*b@x.com"), (("ab@x.com",), "a*@x.com"), (("no-at-sign",), R),
               (("a@b@c.com",), R)]},
]


# ── 參考解答：只用來確認測試資料本身沒寫錯（不給 AI 看）──
def _ref_solutions():
    import datetime as dt
    import re as _re

    def split_bill(total, n):
        if n <= 0:
            raise ValueError
        q, r = divmod(total, n)
        return [q + 1] * r + [q] * (n - r)

    def round_half_up(x):
        from decimal import ROUND_HALF_UP, Decimal
        return int(Decimal(str(x)).quantize(Decimal(1), rounding=ROUND_HALF_UP))

    def compare_versions(a, b):
        pa, pb = [int(p) for p in a.split(".")], [int(p) for p in b.split(".")]
        m = max(len(pa), len(pb))
        pa += [0] * (m - len(pa))
        pb += [0] * (m - len(pb))
        return (pa > pb) - (pa < pb)

    def parse_duration(s):
        mm = _re.fullmatch(r"(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?", s)
        if not s or not mm:
            raise ValueError
        h, m_, sec = (int(g) if g else 0 for g in mm.groups())
        return h * 3600 + m_ * 60 + sec

    def normalize_tw_mobile(s):
        d = _re.sub(r"[\s\-()]", "", s).lstrip("+")
        if _re.fullmatch(r"09\d{8}", d):
            return "+886" + d[1:]
        if _re.fullmatch(r"8869\d{8}", d):
            return "+" + d
        raise ValueError

    def business_days(start, end):
        a, b = dt.date.fromisoformat(start), dt.date.fromisoformat(end)
        return sum((a + dt.timedelta(i)).weekday() < 5 for i in range((b - a).days + 1)) if a <= b else 0

    def rle_encode(s):
        out, i = [], 0
        while i < len(s):
            j = i
            while j < len(s) and s[j] == s[i]:
                j += 1
            out.append(f"{s[i]}{j - i}")
            i = j
        return "".join(out)

    def top_k_words(text, k):
        from collections import Counter
        c = Counter(_re.findall(r"[a-z]+", text.lower()))
        return sorted(c.items(), key=lambda t: (-t[1], t[0]))[:k]

    def mask_email(email):
        if email.count("@") != 1:
            raise ValueError
        local, domain = email.split("@")
        if len(local) <= 2:
            return local[0] + "*" * (len(local) - 1) + "@" + domain
        return local[0] + "*" * (len(local) - 2) + local[-1] + "@" + domain

    def slugify(title):
        return "-".join(_re.findall(r"[a-z0-9]+", title.lower()))

    def format_bytes(n):
        if n < 0:
            raise ValueError
        if n < 1024:
            return f"{n} B"
        v = float(n)
        for u in ["KB", "MB", "GB", "TB"]:
            v /= 1024
            if v < 1024 or u == "TB":
                return f"{v:.1f} {u}"

    def merge_intervals(iv):
        out = []
        for s, e in sorted(iv):
            if out and s <= out[-1][1]:
                out[-1][1] = max(out[-1][1], e)
            else:
                out.append([s, e])
        return out

    return locals()


def check_one(fn, args, expected):
    """瀏覽器 notebook 用同一套判定邏輯（spike 用它對照 pytest，確保兩邊結論一致）。"""
    try:
        got = fn(*args)
    except Exception as e:  # noqa: BLE001
        return isinstance(expected, dict) and type(e).__name__ == expected["raises"]
    if isinstance(expected, dict):
        return False
    return got == expected


def verify_reference():
    ref = _ref_solutions()
    for p in PROBLEMS:
        for kind in ("basic", "edge"):
            for args, exp in p[kind]:
                assert check_one(ref[p["name"]], args, exp), (p["name"], args, exp)
    print(f"reference OK: {len(PROBLEMS)} problems, "
          f"{sum(len(p['basic']) + len(p['edge']) for p in PROBLEMS)} test cases")


# ── 沙盒執行 pytest ─────────────────────────────────────────────────
CONFTEST = '''
import socket
def _no_net(*a, **k):
    raise OSError("network disabled in sandbox")
class _NoSock:
    def __init__(self, *a, **k):
        _no_net()
socket.socket = _NoSock
socket.create_connection = _no_net
socket.getaddrinfo = _no_net
'''


def _limits():
    resource.setrlimit(resource.RLIMIT_CPU, (10, 10))
    resource.setrlimit(resource.RLIMIT_AS, (1 << 30, 1 << 30))
    resource.setrlimit(resource.RLIMIT_FSIZE, (1 << 20, 1 << 20))


def test_file(p, kinds):
    lines = [f"import pytest\nfrom solution import {p['name']}\n"]
    for kind in kinds:
        for i, (args, exp) in enumerate(p[kind], 1):
            call = f"{p['name']}({', '.join(repr(a) for a in args)})"
            if isinstance(exp, dict):
                body = f"    with pytest.raises({exp['raises']}):\n        {call}\n"
            else:
                body = f"    assert {call} == {exp!r}\n"
            lines.append(f"\ndef test_{kind}_{i}():\n{body}")
    return "".join(lines)


def run_pytest(code, p, kinds):
    """回傳 (各測試結果 dict, pytest 輸出原文, 是否逾時)。"""
    with tempfile.TemporaryDirectory(prefix="vibe-sbx-") as tmp:
        Path(tmp, "solution.py").write_text(code, encoding="utf-8")
        Path(tmp, "conftest.py").write_text(CONFTEST, encoding="utf-8")
        Path(tmp, "test_solution.py").write_text(test_file(p, kinds), encoding="utf-8")
        cmd = [sys.executable, "-m", "pytest", "-q", "--tb=short", "-p", "no:cacheprovider",
               "--junitxml=report.xml", "test_solution.py"]
        env = {"PATH": "/usr/bin:/bin", "HOME": tmp, "PYTHONDONTWRITEBYTECODE": "1", "LANG": "C.UTF-8"}
        try:
            r = subprocess.run(cmd, cwd=tmp, env=env, capture_output=True, text=True,
                               timeout=30, preexec_fn=_limits, check=False)
        except subprocess.TimeoutExpired:
            return {}, "TIMEOUT：測試執行超過 30 秒被強制中止", True
        out = (r.stdout + r.stderr).replace(tmp, "sandbox")
        results = {}
        rep = Path(tmp, "report.xml")
        if rep.exists():
            for tc in ET.parse(rep).getroot().iter("testcase"):
                bad = any(ch.tag in ("failure", "error") for ch in tc)
                results[tc.get("name")] = not bad
        return results, out.strip(), False


def trim(out, limit=2400):
    return out if len(out) <= limit else out[:limit] + "\n…（輸出過長，已截斷）"


def extract_code(text):
    m = re.search(r"```(?:python|py)?\s*\n(.*?)```", text, re.DOTALL)
    if m:
        return m.group(1).strip() + "\n"
    # 沒有收尾的 ``` （輸出被截斷）：去掉開頭那行 fence，剩下的照交給測試
    return re.sub(r"^\s*```(?:python|py)?\s*\n", "", text).strip() + "\n"


def chat(messages, seed):
    t0 = time.time()
    r = client.chat.completions.create(
        model=MODEL, messages=messages, max_tokens=1536, temperature=TEMPERATURE, top_p=TOP_P, seed=seed,
        extra_body={"chat_template_kwargs": {"enable_thinking": False}})
    c = r.choices[0]
    return (c.message.content or ""), time.time() - t0, (r.usage.completion_tokens, c.finish_reason)


def grade(code, p):
    res, out, to = run_pytest(code, p, ("basic", "edge"))
    nb, ne = len(p["basic"]), len(p["edge"])
    basic_ok = sum(res.get(f"test_basic_{i}", False) for i in range(1, nb + 1))
    edge_ok = sum(res.get(f"test_edge_{i}", False) for i in range(1, ne + 1))
    return {"basic": basic_ok, "edge": edge_ok, "nb": nb, "ne": ne, "all": (basic_ok == nb and edge_ok == ne),
                "timeout": to}, out


def one_task(pi, run):
    p = PROBLEMS[pi]
    user = p["prompt"]
    base = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": user}]
    seed0 = 1000 * pi + 10 * run
    raw, sec, ntok = chat(base, seed0)
    code = extract_code(raw)
    g, full_out = grade(code, p)
    first = {"code": code, "grade": g, "sec": round(sec, 1), "tokens": ntok[0], "finish": ntok[1]}
    task = {"problem": p["name"], "run": run, "first": first, "branches": {}}
    for cond in ("reroll", "bare", "full", "weak"):
        msgs = base + [{"role": "assistant", "content": raw}]
        attempts = [dict(first)]
        cur_g, cur_out = g, full_out
        for k in range(2, MAX_ATTEMPTS + 1):
            if cond == "reroll":
                if cur_g["all"]:
                    break
                raw_k, sec, ntok = chat(base, seed0 + k + 400)  # 全新對話、同一句需求
                code_k = extract_code(raw_k)
                cur_g, cur_out = grade(code_k, p)
                attempts.append({"code": code_k, "grade": cur_g, "sec": round(sec, 1), "tokens": ntok[0], "finish": ntok[1]})
                continue
            if cond == "weak":
                wres, wout, wto = run_pytest(attempts[-1]["code"], p, ("basic",))
                if wres and all(wres.values()) and not wto:
                    break  # AI 看得到的測試全綠 → 停手（不管邊界測試）
                fb = FULL_MSG.format(out=trim(wout))
            else:
                if cur_g["all"]:
                    break
                fb = BARE_MSG if cond == "bare" else FULL_MSG.format(out=trim(cur_out))
            attempts[-1]["feedback"] = fb
            msgs = msgs + [{"role": "user", "content": fb}]
            raw_k, sec, ntok = chat(msgs, seed0 + k + {"bare": 100, "full": 200, "weak": 300}[cond])
            msgs = msgs + [{"role": "assistant", "content": raw_k}]
            code_k = extract_code(raw_k)
            cur_g, cur_out = grade(code_k, p)
            attempts.append({"code": code_k, "grade": cur_g, "sec": round(sec, 1), "tokens": ntok[0], "finish": ntok[1]})
        task["branches"][cond] = attempts
    fo = trim(full_out)
    task["first_output"] = fo
    print(f"  {p['name']:<20} run{run} first={'PASS' if g['all'] else 'fail'} "
          + " ".join(f"{c}:{len(a)}{'✓' if a[-1]['grade']['all'] else '✗'}" for c, a in task["branches"].items()),
          flush=True)
    return task


def main():
    out_path = Path(sys.argv[1] if len(sys.argv) > 1 else "spike_genai_vibecoding_out.json")
    verify_reference()
    print(f"model={MODEL} runs={RUNS} temp={TEMPERATURE} top_p={TOP_P} max_attempts={MAX_ATTEMPTS}")
    jobs = [(pi, run) for run in range(RUNS) for pi in range(len(PROBLEMS))]
    t0 = time.time()
    with ThreadPoolExecutor(CONCURRENCY) as ex:
        tasks = list(ex.map(lambda a: one_task(*a), jobs))
    print(f"done in {time.time() - t0:.0f}s")

    # ── 摘要：每次 run（12 題）在第 k 次嘗試時的完整測試通過率 ──
    def solved_at(attempts, k):
        return attempts[min(k, len(attempts)) - 1]["grade"]["all"]

    print("\n完整測試（基本＋邊界）通過題數，各 run：")
    for cond in ("reroll", "bare", "full", "weak"):
        for k in range(1, MAX_ATTEMPTS + 1):
            per_run = [sum(solved_at(t["branches"][cond], k) for t in tasks if t["run"] == r) for r in range(RUNS)]
            print(f"  {cond:<5} k={k}: {per_run}  (min {min(per_run)} / max {max(per_run)} of {len(PROBLEMS)})")
    weak_green_wrong = sum(1 for t in tasks
                           if (g := t["branches"]["weak"][-1]["grade"])["basic"] == g["nb"] and not g["all"])
    print(f"weak：基本測試全綠就停手、但完整測試沒過的 task 數 = {weak_green_wrong} / {len(tasks)}")
    for cond in ("reroll", "bare", "full", "weak"):
        same = sum(1 for t in tasks for a, b in zip(t["branches"][cond], t["branches"][cond][1:])
                   if a["code"].strip() == b["code"].strip())
        rep = sum(len(t["branches"][cond]) - 1 for t in tasks)
        print(f"{cond}：新版程式與上一版一字不差的次數 = {same} / {rep}")

    # 用瀏覽器同款判定邏輯重跑每一份程式，對照 pytest 結論（確保 notebook 重算結果一致）
    mismatch = 0
    for t in tasks:
        p = next(q for q in PROBLEMS if q["name"] == t["problem"])
        for cond, atts in t["branches"].items():
            for a in atts:
                if a["grade"]["timeout"]:
                    continue
                ns = {}
                try:
                    exec(a["code"], ns)  # noqa: S102 — spike 本機重算，程式已在沙盒跑過
                    fn = ns[p["name"]]
                    ok_all = all(check_one(fn, args, e) for args, e in p["basic"] + p["edge"])
                except Exception:  # noqa: BLE001
                    ok_all = False
                if ok_all != a["grade"]["all"]:
                    mismatch += 1
                    print(f"  MISMATCH {t['problem']} run{t['run']} {cond}")
    print(f"browser-style re-check mismatches: {mismatch}")

    meta = {"model": MODEL, "runs": RUNS, "temperature": TEMPERATURE, "top_p": TOP_P, "max_attempts": MAX_ATTEMPTS,
                "date": time.strftime("%Y-%m-%d"), "system": SYSTEM, "bare_msg": BARE_MSG, "full_msg": FULL_MSG}
    problems = [{"name": p["name"], "prompt": p["prompt"],
                     "basic": [[list(a), e] for a, e in p["basic"]], "edge": [[list(a), e] for a, e in p["edge"]]}
                for p in PROBLEMS]
    out_path.write_text(json.dumps({"meta": meta, "problems": problems, "tasks": tasks}, ensure_ascii=False, indent=1),
                        encoding="utf-8")
    print(f"wrote {out_path}")
    print("\nSPIKE OK: genai-vibecoding")


if __name__ == "__main__":
    main()
