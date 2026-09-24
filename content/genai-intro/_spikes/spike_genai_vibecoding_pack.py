# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""把兩支 spike 的實測輸出打包、注入 genai-vibecoding/lesson.py（大 payload 不手抄）。

  1. 讀 spike_genai_vibecoding.py 與 spike_genai_vibecoding_risks.py 產出的 JSON
  2. 程式碼與測試輸出去重成字串表（「一字不差重交」在這裡直接看得出來）
  3. 用**瀏覽器 notebook 同一套**判定邏輯（safe_exec＋check_one，import 白名單）重跑每一份程式，
     對照 pytest 的結論——不一致就停下來，確保學員在瀏覽器裡重算的結果＝實測紀錄
  4. zlib＋base64 塞進 lesson.py 的 VIBE_B64／RISK_B64 兩行

  5. 挑一題一次重跑當 hero，把它五種下一步的逐版紀錄寫進 page_content.py 的 `const HERO = ...;` 那一行

跑法：uv run --script content/genai-intro/_spikes/spike_genai_vibecoding_pack.py <vibe.json> <risks.json> <題目>:<run>
（vibe.json 用 spike_genai_vibecoding_hint.py 補過 hint 分支的版本；沒補也能打包，只是少一種下一步）
"""

import base64
import builtins
import contextlib
import io
import json
import re
import sys
import zlib
from pathlib import Path

LESSON = Path(__file__).resolve().parents[1] / "genai-vibecoding" / "lesson.py"
PAGE = LESSON.with_name("page_content.py")
CONDS = ["reroll", "bare", "full", "hint", "weak"]

# ── 以下三個函式與 lesson.py 裡的同名函式邏輯相同（改一邊就要改另一邊）──
ALLOWED = {"re", "math", "datetime", "collections", "decimal", "itertools", "functools", "string",
           "typing", "calendar", "fractions", "operator", "unicodedata", "bisect", "heapq", "enum", "numbers"}


def safe_exec(code, name):
    def guarded_import(mod, globals=None, locals=None, fromlist=(), level=0):
        if mod == "pytest":  # 有的版本多 import 了測試框架卻沒用到：給一個空模組，行為與沙盒一致
            return type(builtins)("pytest")
        if mod.split(".")[0] not in ALLOWED and not mod.startswith("_"):  # _strptime 等標準庫內部模組放行
            raise ImportError(f"blocked import: {mod}")
        return __import__(mod, globals, locals, fromlist, level)

    def blocked(*a, **k):
        raise RuntimeError("blocked in sandbox")

    safe_builtins = dict(vars(builtins), __import__=guarded_import, input=blocked, open=blocked,
                         exit=blocked, quit=blocked)
    ns = {"__builtins__": safe_builtins, "__name__": "ai_solution"}
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            exec(compile(code, "solution.py", "exec"), ns)
        return ns.get(name)
    except BaseException:  # noqa: BLE001 — 語法錯、import 被擋、模組層程式出錯都算這份程式不能用
        return None


def check_one(fn, args, expected):
    if fn is None:
        return False
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            got = fn(*[json.loads(json.dumps(a)) for a in args])
    except Exception as e:  # noqa: BLE001
        return isinstance(expected, dict) and type(e).__name__ == expected["raises"]
    if isinstance(expected, dict):
        return False
    return got == (tuple_fix(expected) if isinstance(expected, list) else expected)


def tuple_fix(expected):
    """JSON 沒有 tuple：top_k_words 的期望值是 list[tuple]，還原回 tuple 才能與 pytest 的判定一致。"""
    return [tuple(x) if isinstance(x, list) and len(x) == 2 and isinstance(x[0], str) else x for x in expected]
# ── 以上三個函式與 lesson.py 同步 ──


def scrub(text):
    """pytest 的 traceback 會帶出本機路徑（含使用者名稱）：公開前換成中性佔位字，其餘原文不動。"""
    text = re.sub(r"/home/[^/\s]+/\.cache/uv/environments-v2/[^/\s]+/lib/python3\.\d+/site-packages/", "<site-packages>/", text)
    text = re.sub(r"/home/[^/\s]+/\.local/share/uv/python/[^/\s]+/lib/python3\.\d+/", "<python-lib>/", text)
    return re.sub(r"/home/[^/\s]+/", "~/", text)


def main():
    vibe = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    risks = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
    P = {p["name"]: p for p in vibe["problems"]}
    codes, outs = [], []
    ci, oi = {}, {}

    def cid(c):
        if c not in ci:
            ci[c] = len(codes)
            codes.append(c)
        return ci[c]

    def oid(o):
        o = scrub(o)
        if o not in oi:
            oi[o] = len(outs)
            outs.append(o)
        return oi[o]

    # 每一份（去重後的）程式，用瀏覽器同款判定逐案例重跑；逾時過的程式不重跑（bits=None）
    timed_out = {a["code"] for t in vibe["tasks"] for atts in t["branches"].values() for a in atts if a["grade"]["timeout"]}
    bits_of = {}

    def bits(code, name):
        if code in timed_out:
            return None
        if (code, name) not in bits_of:
            p = P[name]
            fn = safe_exec(code, name)
            bits_of[(code, name)] = [int(check_one(fn, a, e)) for a, e in p["basic"] + p["edge"]]
        return bits_of[(code, name)]

    tasks = []
    mismatch = checked = 0
    for t in vibe["tasks"]:
        p = P[t["problem"]]
        nb = len(p["basic"])
        br = {}
        for cond in [c for c in CONDS if c in t["branches"]]:
            rows = []
            for a in t["branches"][cond]:
                g = a["grade"]
                fb = a.get("feedback")
                b = bits(a["code"], p["name"])
                rows.append([cid(a["code"]), g["basic"], g["edge"], int(g["timeout"]),
                             oid(fb) if fb else -1, a["sec"], a["tokens"]])
                if b is not None:
                    checked += 1
                    if (sum(b[:nb]), sum(b[nb:])) != (g["basic"], g["edge"]):
                        mismatch += 1
                        print(f"MISMATCH {t['problem']} run{t['run']} {cond}: pytest=({g['basic']},{g['edge']}) "
                              f"browser=({sum(b[:nb])},{sum(b[nb:])})")
            br[cond] = rows
        tasks.append({"p": t["problem"], "r": t["run"], "b": br, "fo": oid(t["first_output"])})
    print(f"browser re-check (per test case): {checked} attempts, {mismatch} mismatches")
    if mismatch:
        sys.exit("✗ 瀏覽器判定與 pytest 不一致，先修 safe_exec／check_one 再打包")
    code_bits = [bits(c, next(t["p"] for t in tasks for rows in t["b"].values() for r in rows if r[0] == i))
                 for i, c in enumerate(codes)]

    meta = {k: vibe["meta"][k] for k in ("model", "runs", "temperature", "top_p", "max_attempts", "date",
                                         "system", "bare_msg", "full_msg")}
    meta["hints"] = vibe["meta"].get("hints", {})
    vpack = {"meta": meta, "problems": vibe["problems"], "tasks": tasks, "codes": codes, "outs": outs, "bits": code_bits}
    rpack = {"meta": risks["meta"], "pkg": risks["pkg"], "secrets": risks["secrets"]}
    enc = {k: base64.b64encode(zlib.compress(json.dumps(v, ensure_ascii=False, separators=(",", ":")).encode(), 9)).decode()
           for k, v in (("VIBE_B64", vpack), ("RISK_B64", rpack))}
    src = LESSON.read_text(encoding="utf-8")
    for k, v in enc.items():
        src, n = re.subn(rf'^(\s*){k} = ".*"$', lambda m, k=k, v=v: f'{m.group(1)}{k} = "{v}"', src, flags=re.MULTILINE)
        assert n == 1, f"lesson.py 裡找不到唯一的 {k} = \"...\" 行"
        print(f"{k}: {len(v):,} chars")
    LESSON.write_text(src, encoding="utf-8")
    print(f"✓ injected into {LESSON}（{len(codes)} unique programs, {len(outs)} unique test outputs）")

    # ── hero：一題一次重跑的五種下一步 ──
    name, run = sys.argv[3].split(":")
    t = next(x for x in vibe["tasks"] if x["problem"] == name and x["run"] == int(run))
    p = P[name]

    def short(text, n):
        lines = text.rstrip().splitlines()
        return "\n".join(lines[:n]) + ("\n…（以下略）" if len(lines) > n else "")

    hero = {"prompt": p["prompt"], "name": name, "nb": len(p["basic"]), "run": int(run), "model": meta["model"],
                "temperature": meta["temperature"], "date": meta["date"], "branches": {}}
    for cond in [c for c in CONDS if c in t["branches"]]:
        rows, prev = [], None
        for a in t["branches"][cond]:
            fb = a.get("feedback")
            rows.append({"code": short(a["code"], 18), "bits": bits(a["code"], name), "same": a["code"] == prev,
                         "fb": short(scrub(fb), 16) if fb else None})
            prev = a["code"]
        hero["branches"][cond] = rows
    page = PAGE.read_text(encoding="utf-8")
    js = json.dumps(hero, ensure_ascii=False)
    page, n = re.subn(r"^const HERO = .*;$", lambda m: f"const HERO = {js};", page, flags=re.MULTILINE)
    assert n == 1, "page_content.py 裡找不到唯一的 const HERO = ...; 行"
    PAGE.write_text(page, encoding="utf-8")
    print(f"✓ hero（{name} run{run}）injected into {PAGE}（{len(js):,} chars）")


if __name__ == "__main__":
    main()
