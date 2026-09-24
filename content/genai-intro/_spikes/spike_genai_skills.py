# /// script
# requires-python = ">=3.11"
# dependencies = ["tiktoken==0.14.0", "skills-ref==0.1.1", "openai", "pyyaml", "numpy"]
# ///
"""genai-skills 課（補充 E：Agent Skills）的定軌 spike——課文引用的每個數字都從這裡來。

分段跑（輸出寫進 $SPIKE_OUT，預設 ./genai_skills_out）：

  uv run --script spike_genai_skills.py tokens     # 量本 repo 的真 skill 三層各多少 token（tiktoken o200k_base）
  uv run --script spike_genai_skills.py validate   # 官方 skills-ref 驗證器：repo skill＋壞範例的真實錯誤訊息，並與課內移植版逐條比對
  uv run --script spike_genai_skills.py overhead   # claude CLI：裝 0／1／9 個 skill 時每輪多付多少 token（Claude 真 tokenizer）
  uv run --script spike_genai_skills.py trigger    # claude CLI：同一個 skill 三版 description × 12 句 prompt × 3 次
  uv run --script spike_genai_skills.py exemplar   # claude CLI：精準版完整跑一次，看 SOP 有沒有被照做
  uv run --script spike_genai_skills.py mental-claude  # claude CLI：不准用工具、心算 36 列工時加總 × 5 次
  uv run --script spike_genai_skills.py local      # 任何 OpenAI 相容端點（本機 Ollama 也行）：最小 skill loader＋心算 vs 腳本
  uv run --script spike_genai_skills.py inject     # 把上面各段的 JSON 注入 content/genai-intro/genai-skills/lesson.py

需要的東西：
- overhead／trigger／exemplar：已登入的 `claude` CLI（會花訂閱額度；本課實測總計見 NOTES）。
  一律在 $SPIKE_OUT 底下的玩具專案當 cwd 跑、`--setting-sources project`，
  不讓使用者自己的 skills／plugins／CLAUDE.md 混進 trace。
- local：env `LLM_URL`（OpenAI 相容 /v1，預設 http://localhost:11434/v1＝本機 Ollama）、
  `LLM_MODEL`（必填，例如你 `ollama pull` 過的模型名）、`LLM_API_KEY`（選填）。
  本課實測用的是 qwen3.5-2b（vLLM）；**Ollama 路徑沒有實測過**，只是同一個 OpenAI 相容介面。
"""

import getpass
import json
import os
import re
import shutil
import subprocess
import sys
import time
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
SKILLS_DIR = REPO / ".claude" / "skills"
OUT = Path(os.environ.get("SPIKE_OUT", "genai_skills_out")).resolve()
OUT.mkdir(parents=True, exist_ok=True)
LESSON = REPO / "content" / "genai-intro" / "genai-skills" / "lesson.py"
CLAUDE_MODEL = os.environ.get("CLAUDE_MODEL", "claude-haiku-4-5")


def save(name, obj):
    (OUT / f"{name}.json").write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"→ {OUT / (name + '.json')}")


# ══════════════════════════════════════════════════════════════════════
# 玩具專案：ACME 小團隊的 timesheet ＋ 一個「週報 SOP」skill
# ══════════════════════════════════════════════════════════════════════
TIMESHEET = """date,member,project,hours,note
2026-09-14,小林,會員系統改版,3.5,登入頁改用新版 API
2026-09-14,小林,客服機器人,2,FAQ 資料清理
2026-09-14,小林,內部維運,1.5,CI 失敗排查
2026-09-14,阿哲,官網改版,6,首頁 RWD 切版
2026-09-14,阿哲,內部維運,1,升級 Node 版本
2026-09-14,Mei,客服機器人,4.5,意圖分類標註
2026-09-14,Mei,會員系統改版,2.5,會員等級規則訪談
2026-09-14,志明,會員系統改版,7,點數折抵 API
2026-09-15,小林,會員系統改版,5,登入頁 E2E 測試
2026-09-15,小林,內部維運,2.5,資料庫備份演練
2026-09-15,阿哲,官網改版,4,產品頁元件化
2026-09-15,阿哲,客服機器人,3,聊天視窗前端
2026-09-15,Mei,客服機器人,6.5,FAQ 向量索引建置
2026-09-15,志明,會員系統改版,5.5,點數折抵 API 單元測試
2026-09-15,志明,內部維運,1.5,監控告警調整
2026-09-16,小林,客服機器人,4,串接工單系統
2026-09-16,小林,會員系統改版,3,修正登入逾時 bug
2026-09-16,阿哲,官網改版,7.5,部落格頁與 SEO 標籤
2026-09-16,Mei,會員系統改版,3.5,等級規則文件
2026-09-16,Mei,客服機器人,3,回覆語氣測試
2026-09-16,志明,會員系統改版,6,會員等級計算批次
2026-09-16,志明,官網改版,1.5,協助首頁效能調校
2026-09-17,小林,會員系統改版,6.5,會員中心頁面串接
2026-09-17,小林,內部維運,1,憑證更新
2026-09-17,阿哲,官網改版,5,多語系切換
2026-09-17,阿哲,內部維運,2.5,CDN 設定調整
2026-09-17,Mei,客服機器人,7,轉真人客服流程
2026-09-17,志明,會員系統改版,4.5,等級計算批次效能優化
2026-09-17,志明,客服機器人,3,會員查詢 API 給機器人用
2026-09-18,小林,會員系統改版,4,上線前回歸測試
2026-09-18,小林,客服機器人,2.5,工單串接錯誤處理
2026-09-18,阿哲,官網改版,6.5,上線前跨瀏覽器測試
2026-09-18,Mei,客服機器人,5,內部試用回饋整理
2026-09-18,Mei,內部維運,1.5,週報工具需求整理
2026-09-18,志明,會員系統改版,7,等級計算上線
2026-09-18,志明,內部維運,0.5,值班交接
"""

HOURS_PY = '''#!/usr/bin/env python3
"""週報 SOP 第 1 步：加總 timesheet 工時。用法：python3 hours.py <timesheet.csv>"""
import csv
import sys
from collections import defaultdict

rows = list(csv.DictReader(open(sys.argv[1], encoding="utf-8")))
by_project = defaultdict(float)
for r in rows:
    by_project[r["project"]] += float(r["hours"])
print("| 專案 | 工時 (h) |")
print("|---|---:|")
for p, h in sorted(by_project.items(), key=lambda x: -x[1]):
    print(f"| {p} | {h:g} |")
print(f"| 合計 | {sum(by_project.values()):g} |")
'''

TEMPLATE_MD = """# ACME 週報 {週次}

## 本週完成
### {專案}
- {完成事項，每條 25 字內}

## 工時統計（由 scripts/hours.py 產生，勿手算）
{貼上腳本輸出的表格}

## 下週計畫
- {每個專案 1 條}

## 風險與需要協助
- {沒有就寫「無」}
"""

STYLE_MD = """# 週報文風

## 主管版（使用者說要給主管／老闆看時才套用）
- 每個專案先寫一句結論（進度正常／有風險），再列完成事項
- 不寫技術細節（API 名稱、框架版本）
- 風險要附「需要誰在何時決定什麼」

## 週會版（預設）
- 可以保留技術細節，方便同事接手
"""

SKILL_BODY = """
# ACME 週報 SOP

1. 先執行 `python3 <本 skill 目錄>/scripts/hours.py timesheet.csv`。
   工時數字一律照抄腳本輸出，**不要自己加總**。
2. 讀 timesheet.csv 的 note 欄，每個專案歸納 2–4 條「本週完成」，每條 25 字內。
3. 套 `assets/template.md` 的格式輸出，標題固定「ACME 週報 2026-W38」。
4. 使用者說要給主管／老闆看時，再讀 `references/style-guide.md` 的「主管版」規則。
"""

DESCRIPTIONS = {
    "vague": "協助處理報告。",
    "precise": (
        "產生 ACME 團隊的每週工作週報：用 scripts/hours.py 精確加總 timesheet.csv 的工時，"
        "套公司固定的週報格式。當使用者要寫週報、本週工作摘要、status report、進度彙整，"
        "或要把本週做了什麼整理成給主管／週會看的報告時使用——即使他沒說出「週報」兩個字。"
        "不用於修改或檢查工時資料、一般書信、寫程式。"
    ),
    "broad": "只要任務跟 timesheet.csv、工時、主管或撰寫文件有任何關係，就使用這個技能。",
}

# 12 句：6 句該觸發（措辭、明示程度、中英文都變化）＋ 6 句「差一點」不該觸發（共用關鍵字但要的不是週報）
QUERIES = [
    ("s1", True, "幫我寫這週的週報"),
    ("s2", True, "主管說週五前要交本週工作摘要，幫我根據 timesheet 整理一份"),
    ("s3", True, "這週各專案花了多少時間、做了什麼，整理成可以直接貼給老闆的東西"),
    ("s4", True, "write up this week's status update for the team lead from timesheet.csv"),
    ("s5", True, "週會要用，幫我彙整一下這週大家的進度"),
    ("s6", True, "下週一要跟 PM 報告，先把本週的工作整理成固定格式給我"),
    ("n1", False, "timesheet.csv 裡 9/17 小林那筆憑證更新的工時打錯了，應該是 1.5，幫我改"),
    ("n2", False, "幫我寫一封信給主管，說我下週三要請假一天"),
    ("n3", False, "寫一個 Python 腳本把 timesheet.csv 轉成 Excel 檔"),
    ("n4", False, "timesheet.csv 每個欄位代表什麼意思？"),
    ("n5", False, "什麼是 OKR？跟 KPI 差在哪？"),
    ("n6", False, "幫我檢查 timesheet.csv 有沒有重複或格式錯誤的紀錄"),
]


def build_toy(root: Path, variant: str | None) -> Path:
    """建一個乾淨的玩具專案；variant=None 表示不裝 skill。"""
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)
    (root / "timesheet.csv").write_text(TIMESHEET, encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    if variant:
        sk = root / ".claude" / "skills" / "weekly-report"
        (sk / "scripts").mkdir(parents=True)
        (sk / "assets").mkdir()
        (sk / "references").mkdir()
        (sk / "SKILL.md").write_text(
            f"---\nname: weekly-report\ndescription: {DESCRIPTIONS[variant]}\n---\n{SKILL_BODY}", encoding="utf-8")
        (sk / "scripts" / "hours.py").write_text(HOURS_PY, encoding="utf-8")
        (sk / "assets" / "template.md").write_text(TEMPLATE_MD, encoding="utf-8")
        (sk / "references" / "style-guide.md").write_text(STYLE_MD, encoding="utf-8")
    return root


def exact_hours(rows_csv: str) -> dict:
    import csv
    import io
    tot: dict = {}
    for r in csv.DictReader(io.StringIO(rows_csv)):
        tot[r["project"]] = tot.get(r["project"], 0.0) + float(r["hours"])
    return tot


# ══════════════════════════════════════════════════════════════════════
# tokens：本 repo 真的 skill，三層各多少 token
# ══════════════════════════════════════════════════════════════════════
def split_frontmatter(text: str):
    import yaml
    parts = text.split("---", 2)
    return yaml.safe_load(parts[1]), parts[2]


def layer_of(rel: str) -> str:
    if rel == "SKILL.md":
        return "L2"
    top = rel.split("/")[0]
    return {"scripts": "L3-script", "references": "L3-ref", "assets": "L3-asset"}.get(top, "L3-other")


def part_tokens():
    import tiktoken
    enc = tiktoken.get_encoding("o200k_base")
    skills = []
    for d in sorted(SKILLS_DIR.iterdir()):
        real = d.resolve()
        md = real / "SKILL.md"
        if not md.exists():
            continue
        text = md.read_text(encoding="utf-8")
        fm, body = split_frontmatter(text)
        l1_text = f"{fm['name']}: {fm['description']}"
        files = []
        for f in sorted(real.rglob("*")):
            if not f.is_file() or "__pycache__" in f.parts:
                continue
            rel = f.relative_to(real).as_posix()
            t = f.read_text(encoding="utf-8", errors="replace")
            files.append({"path": rel, "layer": layer_of(rel), "chars": len(t), "tokens": len(enc.encode(t)),
                          "lines": t.count("\n") + 1})
        skills.append({
            "name": fm["name"], "dir": d.name, "symlink": d.is_symlink(),
            "model_invocable": not fm.get("disable-model-invocation", False),
            "desc_chars": len(fm["description"]),
            "l1_tokens": len(enc.encode(l1_text)),
            "files": files,
        })
    for s in skills:
        agg = {}
        for f in s["files"]:
            agg[f["layer"]] = agg.get(f["layer"], 0) + f["tokens"]
        s["by_layer"] = agg
        print(f"{s['name']:26s} L1={s['l1_tokens']:4d}  " + "  ".join(f"{k}={v}" for k, v in sorted(agg.items())))
    tot_l1 = sum(s["l1_tokens"] for s in skills if s["model_invocable"])
    tot_all = sum(f["tokens"] for s in skills for f in s["files"])
    tot_l2 = sum(s["by_layer"].get("L2", 0) for s in skills)
    print(f"常駐（L1，可被模型觸發的 skill）合計 {tot_l1} tokens；L2 全部 SKILL.md 合計 {tot_l2}；所有檔案全塞 {tot_all}")

    # 課內瀏覽器估算器用：token ≈ a·CJK字元 + b·其他非空白字元 + c·空白（以段落為樣本最小平方）
    import numpy as np
    X, y = [], []
    for s in skills:
        for f in s["files"]:
            if not f["path"].endswith((".md", ".py", ".sh", ".mjs", ".html", ".json", ".yaml")):
                continue
            t = (SKILLS_DIR / s["dir"]).resolve().joinpath(f["path"]).read_text(encoding="utf-8")
            for para in re.split(r"\n\s*\n", t):
                if len(para) < 40:
                    continue
                X.append(char_features(para))
                y.append(len(enc.encode(para)))
    X, y = np.array(X, float), np.array(y, float)
    coef, *_ = np.linalg.lstsq(X, y, rcond=None)
    pred = X @ coef
    rel_err = np.abs(pred - y) / y
    fit = {"coef_cjk": round(float(coef[0]), 4), "coef_other": round(float(coef[1]), 4),
           "coef_space": round(float(coef[2]), 4), "n_samples": len(y),
           "median_rel_err": round(float(np.median(rel_err)), 4), "p90_rel_err": round(float(np.percentile(rel_err, 90)), 4)}
    print("估算器擬合：", fit)
    # 抽查：整份 SKILL.md 的估算 vs 真值
    checks = []
    for s in skills:
        t = (SKILLS_DIR / s["dir"]).resolve().joinpath("SKILL.md").read_text(encoding="utf-8")
        est = float(np.array(char_features(t)) @ coef)
        checks.append({"name": s["name"], "true": len(enc.encode(t)), "est": round(est)})
    print("整檔抽查：", checks)
    save("tokens", {"tokenizer": "tiktoken o200k_base", "tiktoken": tiktoken.__version__ if hasattr(tiktoken, "__version__") else "0.14.0",
                    "measured": time.strftime("%Y-%m-%d"), "skills": skills,
                    "total_l1": tot_l1, "total_l2": tot_l2, "total_all": tot_all, "fit": fit, "fit_checks": checks})


def char_features(t: str):
    cjk = sum(1 for c in t if "⺀" <= c <= "鿿" or "豈" <= c <= "﫿" or "＀" <= c <= "￯" or "　" <= c <= "〿")
    space = sum(1 for c in t if c.isspace())
    return [cjk, len(t) - cjk - space, space]


# ══════════════════════════════════════════════════════════════════════
# validate：官方 skills-ref 驗證器 vs 課內移植版（PyYAML 解析）
# ══════════════════════════════════════════════════════════════════════
ALLOWED = {"name", "description", "license", "allowed-tools", "metadata", "compatibility"}


def port_validate(text: str, dir_name: str) -> list[str]:
    """與 lesson.py 驗證器同一份邏輯：逐條對齊 skills-ref 0.1.1 validator.py 的訊息。"""
    import yaml
    if not text.startswith("---"):
        return ["SKILL.md must start with YAML frontmatter (---)"]
    parts = text.split("---", 2)
    if len(parts) < 3:
        return ["SKILL.md frontmatter not properly closed with ---"]
    try:
        meta = yaml.safe_load(parts[1])
    except yaml.YAMLError as e:
        return [f"Invalid YAML in frontmatter: {str(e).splitlines()[0]}"]
    if not isinstance(meta, dict):
        return ["SKILL.md frontmatter must be a YAML mapping"]
    errs = []
    extra = set(meta) - ALLOWED
    if extra:
        errs.append(f"Unexpected fields in frontmatter: {', '.join(sorted(extra))}. Only {sorted(ALLOWED)} are allowed.")
    if "name" not in meta:
        errs.append("Missing required field in frontmatter: name")
    else:
        n = meta["name"]
        if not n or not isinstance(n, str) or not n.strip():
            errs.append("Field 'name' must be a non-empty string")
        else:
            n = unicodedata.normalize("NFKC", n.strip())
            if len(n) > 64:
                errs.append(f"Skill name '{n}' exceeds 64 character limit ({len(n)} chars)")
            if n != n.lower():
                errs.append(f"Skill name '{n}' must be lowercase")
            if n.startswith("-") or n.endswith("-"):
                errs.append("Skill name cannot start or end with a hyphen")
            if "--" in n:
                errs.append("Skill name cannot contain consecutive hyphens")
            if not all(c.isalnum() or c == "-" for c in n):
                errs.append(f"Skill name '{n}' contains invalid characters. Only letters, digits, and hyphens are allowed.")
            if unicodedata.normalize("NFKC", dir_name) != n:
                errs.append(f"Directory name '{dir_name}' must match skill name '{n}'")
    if "description" not in meta:
        errs.append("Missing required field in frontmatter: description")
    else:
        d = meta["description"]
        if not d or not isinstance(d, str) or not d.strip():
            errs.append("Field 'description' must be a non-empty string")
        elif len(d) > 1024:
            errs.append(f"Description exceeds 1024 character limit ({len(d)} chars)")
    if "compatibility" in meta:
        c = meta["compatibility"]
        if not isinstance(c, str):
            errs.append("Field 'compatibility' must be a string")
        elif len(c) > 500:
            errs.append(f"Compatibility exceeds 500 character limit ({len(c)} chars)")
    return errs


BAD_CASES = {
    # 目錄名, SKILL.md 內容
    "ok-minimal": ("weekly-report", "---\nname: weekly-report\ndescription: 產生每週工作週報。當使用者要寫週報時使用。\n---\n# SOP\n"),
    "uppercase": ("Weekly-Report", "---\nname: Weekly-Report\ndescription: 產生週報。\n---\n"),
    "dir-mismatch": ("weekly_report", "---\nname: weekly-report\ndescription: 產生週報。\n---\n"),
    "underscore": ("weekly_report", "---\nname: weekly_report\ndescription: 產生週報。\n---\n"),
    "double-hyphen": ("weekly--report", "---\nname: weekly--report\ndescription: 產生週報。\n---\n"),
    "no-description": ("weekly-report", "---\nname: weekly-report\n---\n# SOP\n"),
    "cc-only-field": ("grill-me", "---\nname: grill-me\ndescription: A relentless interview to sharpen a plan or design.\ndisable-model-invocation: true\n---\n"),
    "no-frontmatter": ("weekly-report", "# 週報 SOP\n1. 先跑 hours.py\n"),
    "long-description": ("weekly-report", "---\nname: weekly-report\ndescription: " + "產生週報" * 260 + "\n---\n"),
    "chinese-name": ("週報", "---\nname: 週報\ndescription: 產生週報。\n---\n"),
    "yaml-colon": ("weekly-report", "---\nname: weekly-report\ndescription: 用途: 產生週報: 每週五用\n---\n"),
}


def part_validate():
    from skills_ref import validate as official
    res = {"repo": {}, "cases": {}}
    for d in sorted(SKILLS_DIR.iterdir()):
        if (d / "SKILL.md").exists():
            res["repo"][d.name] = official(d)
            print(f"repo {d.name:26s}", res["repo"][d.name] or "Valid")
    tmp = OUT / "validate_cases"
    parity_ok = True
    for key, (dname, text) in BAD_CASES.items():
        p = tmp / key / dname
        if p.parent.exists():
            shutil.rmtree(p.parent)
        p.mkdir(parents=True)
        (p / "SKILL.md").write_text(text, encoding="utf-8")
        off = official(p)
        mine = port_validate(text, dname)
        same = off == mine
        parity_ok &= same or key == "yaml-colon"
        res["cases"][key] = {"dir": dname, "skill_md": text[:400], "official": off, "port": mine, "same": same}
        print(f"case {key:18s} official={off}\n{'':23s}port    ={mine}  same={same}")
    res["parity_all_but_yaml_edge"] = parity_ok
    save("validate", res)


# ══════════════════════════════════════════════════════════════════════
# claude CLI 共用：跑一次 headless，從 stream-json 抽出「有沒有載入 skill」
# ══════════════════════════════════════════════════════════════════════
def run_claude(cwd: Path, prompt: str, max_turns=4, allowed=None, budget=0.3, debug_file=None):
    cmd = ["claude", "-p", prompt, "--model", CLAUDE_MODEL, "--output-format", "stream-json", "--verbose",
           "--setting-sources", "project", "--strict-mcp-config", "--no-session-persistence",
           "--permission-prompts", "none", "--max-turns", str(max_turns), "--max-budget-usd", str(budget)]
    if allowed:
        cmd += ["--allowedTools", allowed]
    if debug_file:
        cmd += ["--debug-file", str(debug_file)]
    t0 = time.time()
    p = subprocess.run(cmd, cwd=cwd, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=300, check=False)
    steps, result, init_skills = [], None, None
    for line in p.stdout.splitlines():
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue
        if d.get("type") == "system" and d.get("subtype") == "init":
            init_skills = d.get("skills")
        elif d.get("type") == "assistant":
            for c in d["message"].get("content", []):
                if c.get("type") == "tool_use":
                    steps.append({"kind": "tool", "name": c["name"], "input": json.dumps(c["input"], ensure_ascii=False)[:300]})
                elif c.get("type") == "text" and c["text"].strip():
                    steps.append({"kind": "text", "text": c["text"][:1500]})
        elif d.get("type") == "user":
            content = d["message"].get("content")
            if isinstance(content, list):
                for c in content:
                    if c.get("type") == "tool_result":
                        body = c.get("content")
                        if isinstance(body, list):
                            body = " ".join(x.get("text", "") for x in body if isinstance(x, dict))
                        steps.append({"kind": "result", "error": bool(c.get("is_error")), "text": str(body)[:600]})
        elif d.get("type") == "result":
            result = d
    usage = (result or {}).get("usage") or {}
    iters = usage.get("iterations") or []
    ctx = [it.get("input_tokens", 0) + it.get("cache_read_input_tokens", 0) + it.get("cache_creation_input_tokens", 0) for it in iters]
    return {"steps": steps, "cost": (result or {}).get("total_cost_usd"), "subtype": (result or {}).get("subtype"),
            "final": ((result or {}).get("result") or "")[:1500], "ctx_per_call": ctx, "secs": round(time.time() - t0, 1),
            "init_skills": init_skills, "debug": debug_lines(debug_file)}


def debug_lines(path):
    """從 --debug-file 撈出 skill listing 相關的兩行（送幾個 skill、有沒有超過預算）。"""
    if not path or not Path(path).exists():
        return []
    keep = []
    for line in Path(path).read_text(encoding="utf-8", errors="replace").splitlines():
        if "via attachment" in line or "Skill listing over budget" in line:
            keep.append(line.split("] ", 1)[-1][:300])
    return keep


def triggered(run, name="weekly-report"):
    for s in run["steps"]:
        if s["kind"] == "tool" and s["name"] == "Skill" and name in s["input"]:
            return "skill-tool"
        if s["kind"] == "tool" and f"skills/{name}/SKILL.md" in s["input"]:
            return "read-file"
    return None


# ══════════════════════════════════════════════════════════════════════
# overhead：裝 skill 的常駐成本（Claude 真 tokenizer，看 API 回報的 input tokens）
# ══════════════════════════════════════════════════════════════════════
def part_overhead():
    base = OUT / "overhead_proj"
    runs = {}

    def setup(which):
        build_toy(base, None)
        if which:
            dst = base / ".claude" / "skills"
            dst.mkdir(parents=True)
            for d in sorted(SKILLS_DIR.iterdir()):
                if which == "all" or d.name in which:
                    shutil.copytree(d.resolve(), dst / d.name)

    for label, which in [("none", None), ("none_again", None), ("make-lesson", ["make-lesson"]),
                         ("publish-videos", ["publish-videos"]), ("all9", "all")]:
        setup(which)
        dbg = OUT / f"debug_{label}.log"
        dbg.unlink(missing_ok=True)
        r = run_claude(base, "Reply with just: ok", max_turns=1, debug_file=dbg)
        runs[label] = {"ctx": r["ctx_per_call"], "cost": r["cost"], "skills_seen": r["init_skills"], "debug": r["debug"]}
        print(label, r["ctx_per_call"], r["cost"], r["debug"])
    # 載入 make-lesson：第二次 API 呼叫的上下文 − 第一次 ≈ SKILL.md 進場的成本
    setup("all")
    r = run_claude(base, "Invoke the make-lesson skill with the Skill tool (no arguments), then reply with just: ok. Do nothing else.",
                   max_turns=3)
    runs["invoke_make_lesson"] = {"ctx": r["ctx_per_call"], "cost": r["cost"],
                                  "steps": [s for s in r["steps"] if s["kind"] != "text"][:4]}
    print("invoke", r["ctx_per_call"], r["cost"], [s.get("name") for s in r["steps"] if s["kind"] == "tool"])
    # Claude Code 的 frontmatter 解析很寬容：官方驗證器判死的 YAML，它照樣吃（問模型 listing 裡看到什麼）
    build_toy(base, None)
    for nm, desc in [("weekly-report", "Use when: the user asks for a weekly report"),
                     ("broken-yaml", "[unclosed list, Use this for weekly reports")]:
        d = base / ".claude" / "skills" / nm
        d.mkdir(parents=True)
        (d / "SKILL.md").write_text(f"---\nname: {nm}\ndescription: {desc}\n---\n# SOP\n", encoding="utf-8")
    r = run_claude(base, "In your available skills listing, find the entries named weekly-report and broken-yaml. "
                   "Quote each entry's description text exactly as it appears in your listing (or say NONE). Do not call any tools.",
                   max_turns=1)
    runs["lenient_yaml"] = {"answer": r["final"], "cost": r["cost"]}
    print("lenient", r["final"])
    save("overhead", {"model": CLAUDE_MODEL, "measured": time.strftime("%Y-%m-%d"), "runs": runs})


# ══════════════════════════════════════════════════════════════════════
# trigger：description 三版 × 12 句 × 3 次（agentskills.io 建議的做法：每句跑 3 次算觸發率）
# ══════════════════════════════════════════════════════════════════════
def part_trigger():
    reps = int(os.environ.get("REPS", "3"))
    variants = os.environ.get("VARIANTS", "vague,precise,broad").split(",")
    jobs = []
    for v in variants:
        for qid, should, q in QUERIES:
            for k in range(reps):
                jobs.append((v, qid, should, q, k))

    def one(job):
        v, qid, should, q, k = job
        proj = build_toy(OUT / "trig" / f"{v}-{qid}-{k}", v)
        # 只看前 TRIG_TURNS 回合（預設 2）：要不要載入 skill 幾乎都在第一個動作就決定，省額度
        r = run_claude(proj, q, max_turns=int(os.environ.get("TRIG_TURNS", "2")))
        r["trig"] = triggered(r)
        shutil.rmtree(proj, ignore_errors=True)
        print(f"{v:8s} {qid} #{k} trig={r['trig']!s:10s} cost={r['cost']} steps={[s.get('name') for s in r['steps'] if s['kind'] == 'tool']}", flush=True)
        return {"variant": v, "qid": qid, "should": should, "query": q, "rep": k, **r}

    with ThreadPoolExecutor(max_workers=int(os.environ.get("PAR", "3"))) as ex:
        rows = list(ex.map(one, jobs))
    cost = sum(r["cost"] or 0 for r in rows)
    print(f"total list cost ≈ ${cost:.3f}")
    prev = OUT / "trigger.json"
    old = json.loads(prev.read_text(encoding="utf-8"))["rows"] if prev.exists() and os.environ.get("APPEND") else []
    save("trigger", {"model": CLAUDE_MODEL, "measured": time.strftime("%Y-%m-%d"), "descriptions": DESCRIPTIONS,
                     "queries": QUERIES, "rows": old + rows, "cost_usd": cost})


def part_mental_claude():
    """同一題心算，換 Claude（不准用工具）：36 列 timesheet 加總各專案工時，跑 5 次。"""
    proj = build_toy(OUT / "mental_proj", None)
    truth = exact_hours(TIMESHEET)
    rows = []
    q = (f"以下是工時紀錄 CSV：\n{TIMESHEET}\n請加總每個專案的總工時。不要使用任何工具，直接心算。"
         "只輸出 JSON 物件，鍵是專案名、值是數字，不要其他文字。")
    for k in range(int(os.environ.get("REPS", "5"))):
        r = run_claude(proj, q, max_turns=1)
        out = r["final"]
        try:
            got = json.loads(out[out.index("{"): out.rindex("}") + 1])
            n_wrong = sum(1 for p_, h in truth.items() if abs(float(got.get(p_, -999)) - h) > 1e-9)
            err = sum(abs(float(got.get(p_, 0)) - h) for p_, h in truth.items())
        except (ValueError, json.JSONDecodeError):
            got, n_wrong, err = None, None, None
        rows.append({"rep": k, "got": got, "n_wrong": n_wrong, "abs_err": err, "cost": r["cost"], "tools": [x["name"] for x in r["steps"] if x["kind"] == "tool"]})
        print(k, got, n_wrong, err, r["cost"])
    save("mental_claude", {"model": CLAUDE_MODEL, "measured": time.strftime("%Y-%m-%d"), "truth": truth, "rows": rows})


def part_exemplar():
    proj = build_toy(OUT / "exemplar_proj", "precise")
    q = QUERIES[1][2]
    r = run_claude(proj, q, max_turns=8, allowed="Skill Read Glob Bash(python3 *)", budget=0.5)
    r["trig"] = triggered(r)
    print(json.dumps(r, ensure_ascii=False, indent=1)[:6000])
    save("exemplar", {"model": CLAUDE_MODEL, "measured": time.strftime("%Y-%m-%d"), "query": q, **r})


# ══════════════════════════════════════════════════════════════════════
# local：最小 skill loader（任何 OpenAI 相容端點；免費路徑）＋ 心算 vs 腳本
# ══════════════════════════════════════════════════════════════════════
def llm():
    from openai import OpenAI
    url = os.environ.get("LLM_URL", "http://localhost:11434/v1")
    model = os.environ.get("LLM_MODEL")
    if not model:
        sys.exit("請設 LLM_MODEL（例如你用 ollama pull 下載過的模型名）")
    return OpenAI(base_url=url, api_key=os.environ.get("LLM_API_KEY", "none")), model


def chat(client, model, messages, temperature=0.0, max_tokens=700):
    r = client.chat.completions.create(model=model, messages=messages, temperature=temperature, max_tokens=max_tokens,
                                       extra_body={"chat_template_kwargs": {"enable_thinking": False}})
    return (r.choices[0].message.content or "").strip()


def available_skills_block(skill_root: Path) -> str:
    from skills_ref import to_prompt
    return to_prompt([d for d in sorted(skill_root.iterdir()) if (d / "SKILL.md").exists()])


LOADER_SYSTEM = """你是一個助理，工作目錄裡有 timesheet.csv。你有以下技能（skill）可以用，平常只看得到名稱與說明：

{skills}

你可以輸出**一行 JSON** 來要求動作（一次一個，輸出 JSON 時不要有任何其他文字）：
- {{"load_skill": "技能名稱"}}：讀進該技能的完整說明書（SKILL.md）。任務符合某個技能的說明時，先做這一步。
- {{"run": "scripts/檔名"}}：執行已載入技能裡的腳本，系統會回傳輸出。
- {{"read": "檔名"}}：讀檔（工作目錄的 timesheet.csv，或已載入技能裡的 assets/、references/ 檔案）。
不需要任何動作時，直接用繁體中文回答（或完成任務）。"""


def mini_agent(client, model, skill_root: Path, workdir: Path, query: str, max_steps=8):
    """最小 skill loader：listing 放 system prompt（Level 1）→ 模型要求才塞 SKILL.md（Level 2）
    → 模型要求才跑腳本／讀檔（Level 3）。回傳逐步 trace。"""
    msgs = [{"role": "system", "content": LOADER_SYSTEM.format(skills=available_skills_block(skill_root))},
            {"role": "user", "content": query}]
    trace = [{"role": "user", "content": query}]
    loaded = None
    done = set()
    for _ in range(max_steps):
        out = chat(client, model, msgs, max_tokens=1200)
        trace.append({"role": "assistant", "content": out})
        m = re.search(r"\{[^{}]*\}", out)
        req = None
        if m:
            try:
                req = json.loads(m.group(0))
            except json.JSONDecodeError:
                req = None
        if not isinstance(req, dict) or not ({"load_skill", "run", "read"} & set(req)):
            break  # 沒有動作要求＝最終回答（小模型常在 JSON 前後多講幾句，照樣當動作處理）
        if "load_skill" in req:
            sk = skill_root / str(req["load_skill"])
            if (sk / "SKILL.md").exists():
                loaded = sk
                body = (sk / "SKILL.md").read_text(encoding="utf-8").split("---", 2)[2].strip()
                feedback = f"【{sk.name} 的 SKILL.md】\n{body}"
                trace.append({"role": "loader", "content": f"Level 2：塞進 SKILL.md 本文（{len(body)} 字）"})
            else:
                feedback = f"錯誤：沒有叫 {req['load_skill']} 的技能"
        elif "run" in req and loaded:
            target = (loaded / str(req["run"]).split()[0]).resolve()  # 模型常把參數一起寫進來
            if target.parent == (loaded / "scripts").resolve() and target.exists():
                r = subprocess.run([sys.executable, str(target), str(workdir / "timesheet.csv")], capture_output=True, text=True, check=False)
                feedback = f"【{req['run']} 輸出】\n{r.stdout or r.stderr}"
                trace.append({"role": "loader", "content": f"Level 3：執行 {req['run']}（程式碼不進上下文，只回傳輸出 {len(r.stdout)} 字）"})
            else:
                feedback = f"錯誤：找不到腳本 {req['run']}"
        elif "read" in req:
            name = str(req["read"])
            target = (workdir / name).resolve() if name == "timesheet.csv" else ((loaded or workdir) / name).resolve()
            ok_skill = loaded is not None and loaded.resolve() in target.parents
            if (ok_skill or target == (workdir / "timesheet.csv").resolve()) and target.exists():
                feedback = f"【{req['read']}】\n{target.read_text(encoding='utf-8')}"
                trace.append({"role": "loader", "content": f"Level 3：讀 {req['read']}（{len(feedback)} 字）"})
            else:
                feedback = f"錯誤：找不到檔案 {req['read']}"
        else:
            feedback = "錯誤：要先 load_skill 才能 run／read"
        key = json.dumps(req, ensure_ascii=False, sort_keys=True)
        if key in done:  # 小模型常重複同一個動作（實測 qwen3.5-2b 會連跑 5 次 hours.py）→ 迴圈護欄
            feedback = "你已經做過這個動作，結果在上面。"
        done.add(key)
        feedback += "\n\n（以上是動作結果。請照 SOP 繼續下一步；全部完成就直接輸出最終內容，不要再輸出 JSON。）"
        msgs += [{"role": "assistant", "content": out}, {"role": "user", "content": feedback}]
        trace.append({"role": "tool", "content": feedback[:1500]})
    return trace


def local_trigger(client, model):
    reps = int(os.environ.get("REPS", "3"))
    rows = []
    for v in ["vague", "precise", "broad"]:
        proj = build_toy(OUT / "local_proj", v)
        sys_prompt = LOADER_SYSTEM.format(skills=available_skills_block(proj / ".claude" / "skills"))
        for qid, should, q in QUERIES:
            for k in range(reps):
                out = chat(client, model, [{"role": "system", "content": sys_prompt}, {"role": "user", "content": q}],
                           temperature=0.7 if k else 0.0, max_tokens=200)
                trig = bool(re.search(r'"load_skill"\s*:\s*"weekly-report"', out))
                rows.append({"variant": v, "qid": qid, "should": should, "rep": k, "trig": trig, "out": out[:200]})
                print(f"{v:8s} {qid} #{k} trig={trig} {out[:60]!r}", flush=True)
    return {"trigger_rows": rows}


def local_loader(client, model):
    proj = build_toy(OUT / "local_proj", "precise")
    trace = mini_agent(client, model, proj / ".claude" / "skills", proj, QUERIES[1][2])
    for t in trace:
        print(f"[{t['role']}] {t['content'][:400]}\n")
    return {"loader_trace": trace}


def local_mental(client, model):
    """心算 vs 腳本：把 N 列 timesheet 貼給模型，要它加總各專案工時。"""
    lines = TIMESHEET.strip().splitlines()
    mental = []
    for n in (12, 24, 36):
        sub = "\n".join(lines[: n + 1])
        truth = exact_hours(sub)
        for k in range(5):
            out = chat(client, model, [{"role": "user", "content":
                        f"以下是工時紀錄 CSV：\n{sub}\n\n請加總每個專案的總工時。只輸出 JSON 物件，鍵是專案名、值是數字，不要其他文字。"}],
                       temperature=0.0 if k == 0 else 0.7, max_tokens=300)
            try:
                got = json.loads(out[out.index("{"): out.rindex("}") + 1])
                err = sum(abs(float(got.get(p, 0)) - h) for p, h in truth.items())
                n_wrong = sum(1 for p, h in truth.items() if abs(float(got.get(p, -999)) - h) > 1e-9)
            except (ValueError, json.JSONDecodeError):
                got, err, n_wrong = None, None, None
            mental.append({"rows": n, "rep": k, "truth": truth, "got": got, "abs_err": err, "n_wrong": n_wrong, "raw": out[:300]})
            print(f"rows={n} #{k} abs_err={err} wrong={n_wrong} got={got}", flush=True)
    return {"mental": mental}


def part_local():
    """LOCAL_ONLY=trigger,loader,mental 可只跑其中幾段；結果併進既有的 local.json。"""
    client, model = llm()
    only = os.environ.get("LOCAL_ONLY", "trigger,loader,mental").split(",")
    f = OUT / "local.json"
    res = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
    for name, fn in [("trigger", local_trigger), ("loader", local_loader), ("mental", local_mental)]:
        if name in only:
            res.update(fn(client, model))
    res.update({"model": model, "measured": time.strftime("%Y-%m-%d")})
    save("local", res)


# ══════════════════════════════════════════════════════════════════════
# inject：把各段 JSON 精簡後寫進 lesson.py 的 DATA 區塊
# ══════════════════════════════════════════════════════════════════════
PROJ_PATH = re.compile(r"/[^\s\"']*?/(?:trig/[^/\s\"']+|exemplar_proj|overhead_proj|local_proj|mental_proj)/")


def clean(t: str) -> str:
    """trace 裡的絕對路徑（本機 scratchpad）換成專案相對路徑，不把主機目錄結構寫進 repo。"""
    t = PROJ_PATH.sub("", t or "")
    t = re.sub(r"/tmp/[^\s\"']+", "…", t)
    t = re.sub(r"/home/[^/\s]+", "~", t)
    return re.sub(rf"\b{re.escape(getpass.getuser())}\b", "user", t)  # ls -la 會印出本機帳號名


def compact_steps(steps, n=12, width=260):
    out = []
    for st in steps[:n]:
        if st["kind"] == "tool":
            out.append({"k": "tool", "name": st["name"], "t": clean(st["input"])[:width]})
        elif st["kind"] == "result":
            out.append({"k": "res", "err": st["error"], "t": clean(st["text"])[:width]})
        else:
            out.append({"k": "text", "t": clean(st["text"])[:width]})
    return out


def part_inject():
    data = {}
    for k in ("tokens", "validate", "overhead", "trigger", "exemplar", "local", "mental_claude"):
        f = OUT / f"{k}.json"
        if f.exists():
            data[k] = json.loads(f.read_text(encoding="utf-8"))
    tok = data["tokens"]
    ov = data["overhead"]
    payload = {
        "tokens": {"tokenizer": tok["tokenizer"], "measured": tok["measured"], "fit": tok["fit"],
                   "skills": [{k: v for k, v in sk.items() if k != "dir"} for sk in tok["skills"]]},
        "overhead": {"model": ov["model"], "measured": ov["measured"],
                     "runs": {k: {"ctx": v.get("ctx"), "debug": v.get("debug", []), "answer": clean(v.get("answer", ""))}
                              for k, v in ov["runs"].items()}},
        "validate_cases": {k: {"dir": v["dir"], "skill_md": v["skill_md"], "official": v["official"]}
                           for k, v in data["validate"]["cases"].items()},
        "validate_repo": data["validate"]["repo"],
        "timesheet": TIMESHEET, "descriptions": DESCRIPTIONS, "queries": QUERIES,
    }
    t = data["trigger"]
    payload["trigger"] = {"model": t["model"], "measured": t["measured"], "cost_usd": round(t["cost_usd"], 3),
                          "rows": [{"v": r["variant"], "q": r["qid"], "k": r["rep"], "trig": bool(r["trig"]),
                                    "steps": compact_steps(r["steps"], n=6, width=220)} for r in t["rows"]]}
    lo = data["local"]
    payload["local"] = {"model": lo["model"], "measured": lo["measured"],
                        "rows": [{"v": r["variant"], "q": r["qid"], "k": r["rep"], "trig": r["trig"], "out": clean(r["out"])[:160]}
                                 for r in lo["trigger_rows"]],
                        "mental": [{"rows": m["rows"], "rep": m["rep"], "got": m["got"], "abs_err": m["abs_err"],
                                    "n_wrong": m["n_wrong"]} for m in lo["mental"]],
                        "trace": [{"role": x["role"], "content": clean(x["content"])[:1600]} for x in lo["loader_trace"]]}
    mc = data["mental_claude"]
    payload["mental_claude"] = {"model": mc["model"], "measured": mc["measured"],
                                "rows": [{"rep": r["rep"], "got": r["got"], "n_wrong": r["n_wrong"], "abs_err": r["abs_err"]} for r in mc["rows"]]}
    e = data["exemplar"]
    payload["exemplar"] = {"model": e["model"], "measured": e["measured"], "query": e["query"],
                           "steps": compact_steps(e["steps"], n=14, width=300), "final": clean(e["final"])}
    blob = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    assert "/tmp/" not in blob and "/home/" not in blob and "10.131" not in blob, "payload 裡還有本機路徑或內網位址"
    src = LESSON.read_text(encoding="utf-8")
    new, n = re.subn(r"(# === DATA:BEGIN ===\n).*?(\n\s*# === DATA:END ===)",
                     lambda m: m.group(1) + "    DATA = json.loads(" + repr(blob) + ")" + m.group(2), src, flags=re.DOTALL)
    if n != 1:
        sys.exit("lesson.py 找不到 DATA 標記")
    LESSON.write_text(new, encoding="utf-8")
    print(f"注入 {len(blob)} 字元 → {LESSON}")
    inject_hero(data)


def summarize(steps):
    """hero 用：一次執行濃縮成一行「做了什麼」。"""
    acts = []
    for st in steps:
        if st["kind"] != "tool":
            continue
        try:
            inp = json.loads(st["input"]) if st["input"].endswith("}") else {}
        except json.JSONDecodeError:
            inp = {}
        name = st["name"]
        if name == "Skill":
            acts.append(f"Skill({inp.get('skill', '?')})")
        elif name in ("Read", "Write", "Edit"):
            acts.append(f"{name}({Path(str(inp.get('file_path', '?'))).name})")
        elif name == "Bash":
            cmd = clean(str(inp.get("command", "")))
            acts.append("Bash(" + ("hours.py" if "hours.py" in cmd else cmd[:24]) + ")")
        else:
            acts.append(name)
        if len(acts) == 3:
            break
    if acts:
        return " → ".join(acts)
    txt = next((st["text"] for st in steps if st["kind"] == "text"), "")
    return "直接回答：「" + clean(txt).replace("\n", " ")[:28] + "…」"


def inject_hero(data):
    page = LESSON.parent / "page_content.py"
    if not page.exists():
        return
    hero = {"q": QUERIES, "desc": DESCRIPTIONS, "m": {}}
    t = data["trigger"]
    runs = {}
    for r in sorted(t["rows"], key=lambda r: r["rep"]):
        runs.setdefault(f"{r['variant']}|{r['qid']}", []).append([1 if r["trig"] else 0, summarize(r["steps"])])
    hero["m"]["claude"] = {"label": f"{t['model']} × Claude Code 2.1.281", "runs": runs}
    lo = data["local"]
    runs = {}
    for r in sorted(lo["trigger_rows"], key=lambda r: r["rep"]):
        out = clean(r["out"]).replace("\n", " ")
        runs.setdefault(f"{r['variant']}|{r['qid']}", []).append([1 if r["trig"] else 0, out[:40] + ("…" if len(out) > 40 else "")])
    hero["m"]["qwen"] = {"label": f"{lo['model']} × 本課最小 loader", "runs": runs}
    blob = json.dumps(hero, ensure_ascii=False, separators=(",", ":"))
    assert "/tmp/" not in blob and "10.131" not in blob
    src = page.read_text(encoding="utf-8")
    new, n = re.subn(r"(/\* HERO:BEGIN \*/).*?(/\* HERO:END \*/)", lambda m: m.group(1) + "const HERO = " + blob + ";" + m.group(2),
                     src, flags=re.DOTALL)
    if n != 1:
        print("page_content.py 沒有 HERO 標記，略過")
        return
    page.write_text(new, encoding="utf-8")
    print(f"hero 注入 {len(blob)} 字元 → {page}")


if __name__ == "__main__":
    part = sys.argv[1] if len(sys.argv) > 1 else "tokens"
    {"tokens": part_tokens, "validate": part_validate, "overhead": part_overhead, "trigger": part_trigger,
     "exemplar": part_exemplar, "mental-claude": part_mental_claude, "local": part_local, "inject": part_inject}[part]()
