# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""genai-finetune：把 spike 的實測結果（r_*.json）整理成課程素材，注入 lesson.py 與 page_content.py。

  uv run --script content/genai-intro/_spikes/spike_genai_finetune_collect.py --results <dir>          # 只印摘要
  uv run --script content/genai-intro/_spikes/spike_genai_finetune_collect.py --results <dir> --inject

<dir> 裡放 spike_genai_finetune.py／_unsloth.py 用 --out 寫出的 JSON（檔名隨意，靠內容分類）。
注入位置：lesson.py 的 FT_DATA 標記、page_content.py 的 `const HERO = ` 標記與 BA／MASK／CAL 三個 HTML 註解標記。
重跑 spike 之後重跑這支即可同步；課文裡引用的數字要照印出的摘要人工核對（見該課 NOTES.md）。
"""

from __future__ import annotations

import argparse
import html
import json
import re
import statistics as st
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from spike_genai_finetune_data import build_dataset, score  # noqa: E402

LESSON = HERE.parent / "genai-finetune" / "lesson.py"
PAGE = HERE.parent / "genai-finetune" / "page_content.py"
MAIN_MODEL = "unsloth/Qwen3-1.7B-bnb-4bit"
BA_INDEX = 2  # 教學頁第 3 節「訓練前後」展示的那一題（test 集索引；換資料／模型時重挑）
SHORT_NAME = {
    "unsloth/Qwen3-0.6B-bnb-4bit": "Qwen3-0.6B", "Qwen/Qwen3-0.6B": "Qwen3-0.6B",
    "unsloth/Qwen3-1.7B-bnb-4bit": "Qwen3-1.7B", "Qwen/Qwen3-1.7B": "Qwen3-1.7B",
    "unsloth/Qwen3-4B-bnb-4bit": "Qwen3-4B",
}


def load(results: Path) -> list[dict]:
    rows = []
    for f in sorted(results.glob("*.json"), key=lambda p: p.stat().st_mtime):
        try:
            r = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        if isinstance(r, dict) and "loss" in r and "peak_reserved_gib" in r:
            r["_file"] = f.name
            rows.append(r)
    return rows


def tool_of(r) -> str | None:
    return {"trl+peft": "trl", "unsloth": "unsloth"}.get(r["tool"])


def scenario(r) -> str:
    return "long" if r["hp"].get("long_ctx") else "short"


def _sc(out: str, label: dict) -> str:
    r = score(out, label)
    names = [("json_ok", "整段是 JSON"), ("schema_ok", "欄位"), ("category", "類別"), ("product", "產品"), ("urgent", "急件")]
    return "　".join(("✓ " if r[k] else "✗ ") + v for k, v in names)


def render_ba(ev: dict) -> str:
    i = BA_INDEX
    lab = ev["labels"][i]
    cards = [("var(--cut)", "底模＋一句話 prompt", ev["base_short"][i]),
             ("var(--c4)", "底模＋寫滿規則的 prompt", ev["base_detailed"][i]),
             ("var(--c3)", "微調後＋一句話 prompt", ev["trl"][i])]
    assert ev["trl"][i] == ev["unsloth"][i], "BA_INDEX 那題兩個工具的輸出不同，課文說「一字不差」要改"
    body = "".join(f'\n    <div style="--bc:{c}"><div class="hd">{t}</div><pre>{html.escape(o)}</pre>'
                   f'<div class="sc">{_sc(o, lab)}</div></div>' for c, t, o in cards)
    return (f'\n  <p style="font-size:13.5px"><b>客人說：</b>{html.escape(ev["msgs"][i])}</p>'
            f'\n  <div class="ba">{body}\n  </div>\n  ')


def render_mask(spans: list[dict]) -> str:
    return "".join(f'<span class="{"on" if sp["loss"] else "off"}">{html.escape(sp["text"])}</span>' for sp in spans)


def render_cal(cal: list[dict]) -> str:
    label = {"qlora": "QLoRA（4-bit）", "lora16": "LoRA（bf16 底模）", "full": "全參數（bf16＋AdamW）"}
    order = [("Qwen3-0.6B", "qlora", "short"), ("Qwen3-0.6B", "qlora", "long"), ("Qwen3-1.7B", "qlora", "short"),
             ("Qwen3-1.7B", "qlora", "long"), ("Qwen3-4B", "qlora", "short"), ("Qwen3-4B", "qlora", "long"),
             ("Qwen3-1.7B", "lora16", "short"), ("Qwen3-0.6B", "full", "short")]
    rows = []
    for m, meth, sc in order:
        got = {c["tool"]: c["peak"] for c in cal if (c["model"], c["method"], c["scn"]) == (m, meth, sc)}
        if not got:
            continue
        cells = {t: (f"{got[t]:.2f} GiB" if t in got else "—") for t in ("trl", "unsloth")}
        tag = "，長資料" if sc == "long" else ""
        rows.append(f'<tr><td>{m}</td><td>{label[meth]}{tag}</td><td class="n">{cells["trl"]}</td>'
                    f'<td class="n">{cells["unsloth"]}</td></tr>')
    return "\n    " + "\n    ".join(rows) + "\n    "


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", required=True)
    ap.add_argument("--inject", action="store_true")
    a = ap.parse_args()
    rows = [r for r in load(Path(a.results)) if tool_of(r) and r.get("precision") == "bf16"]

    # 每個情境「每筆平均 token 數」：取 TRL 完整 epoch 的 num_tokens（資料的性質，兩個工具吃同一份）
    tok_per_ex = {}
    for r in rows:
        if tool_of(r) == "trl" and r.get("num_tokens") and not r["hp"].get("max_steps"):
            tok_per_ex.setdefault(scenario(r), r["num_tokens"] / r["n_train"])

    main_runs = [r for r in rows if r["model"] == MAIN_MODEL and r["mode"] == "qlora"
                 and not r["hp"].get("max_steps")]
    runs = {"short": {"trl": [], "unsloth": []}, "long": {"trl": [], "unsloth": []}}
    for r in main_runs:
        runs[scenario(r)][tool_of(r)].append({
            "loss": r["loss"], "step_s": r["step_s"], "train_s": r["train_s"],
            "peak": r["peak_reserved_gib"], "load": r["mem_after_load_gib"], "file": r["_file"],
        })

    ev_trl = next(r for r in main_runs if tool_of(r) == "trl" and "eval_base_short" in r)
    ev_uns = next(r for r in main_runs if tool_of(r) == "unsloth" and "eval_ft_short" in r)
    _, test = build_dataset()
    test = test[: ev_trl["n_test"]]
    evald = {
        "msgs": [t["messages"][1]["content"] for t in test],
        "labels": [t["label"] for t in test],
        "answers": [t["messages"][2]["content"] for t in test],
        "base_short": ev_trl["eval_base_short"]["outputs"],
        "base_detailed": ev_trl["eval_base_detailed"]["outputs"],
        "trl": ev_trl["eval_ft_short"]["outputs"],
        "unsloth": ev_uns["eval_ft_short"]["outputs"],
    }
    mask = {"trl": ev_trl["mask_example"]["spans"][:3], "unsloth": ev_uns["mask_example"]["spans"][:4]}

    cal, seen = [], set()
    for r in rows:
        name = SHORT_NAME.get(r["model"])
        sc = scenario(r)
        if not name or sc not in tok_per_ex:
            continue
        key = (name, r["mode"], tool_of(r), sc)
        if key in seen:  # 同組合只取第一次（VRAM 每次都一樣）
            continue
        seen.add(key)
        per = tok_per_ex[sc]
        cal.append({
            "model": name, "method": r["mode"], "tool": tool_of(r), "scn": sc, "seq": round(per),
            "batch": r["hp"]["batch"],
            "batch_tokens": round(per * r["hp"]["batch"]), "peak": r["peak_reserved_gib"],
            "load": r["mem_after_load_gib"],
            # fit＝擬合活化值係數、calib＝校準全參數的狀態係數、check＝沒參與擬合，拿來驗證估算
            "role": ("fit" if r["mode"] == "qlora" and name in ("Qwen3-0.6B", "Qwen3-1.7B")
                     else "calib" if r["mode"] == "full" else "check"),
        })

    first = {k: runs[k] for k in runs}
    ft = {
        "meta": {"date": "2026-09-24", "gpu": ev_trl["gpu"], "model": MAIN_MODEL, "hp": ev_trl["hp"],
                 "versions": {"trl": ev_trl["versions"], "unsloth": ev_uns["versions"]},
                 "n_train": ev_trl["n_train"], "n_test": ev_trl["n_test"],
                 "tok_per_ex": {k: round(v, 1) for k, v in tok_per_ex.items()},
                 "trainable": ev_trl["trainable_params"]},
        "runs": first, "eval": evald, "mask": mask, "cal": cal,
        "sys_tokens": {"short": ev_trl["system_short_tokens"], "detailed": ev_trl["system_detailed_tokens"]},
    }

    # ── 摘要：課文要引用的數字 ──
    print("tokens/example:", {k: round(v, 1) for k, v in tok_per_ex.items()}, "trainable:", ev_trl["trainable_params"])
    for sc in ("short", "long"):
        for tl in ("trl", "unsloth"):
            for x in runs[sc][tl]:
                print(f"{sc:5s} {tl:8s} {x['file']:22s} train={x['train_s']:7.2f}s med={st.median(x['step_s'][3:]):.3f}s/step "
                      f"first={x['step_s'][0]:.2f} peak={x['peak']:.3f} load={x['load']:.3f} loss {x['loss'][0]}→{x['loss'][-1]}")
        pairs = list(zip(runs[sc]["trl"], runs[sc]["unsloth"], strict=False))
        print(f"  {sc} step-median ratio TRL/Unsloth:",
              [round(st.median(t["step_s"][3:]) / st.median(u["step_s"][3:]), 2) for t, u in pairs],
              " wall ratio:", [round(t["train_s"] / u["train_s"], 2) for t, u in pairs])
    for c in cal:
        print("cal", c)
    print("eval summaries:", {k: ev_trl[k]["summary"] for k in ("eval_base_short", "eval_base_detailed", "eval_ft_short")},
          "unsloth:", ev_uns["eval_ft_short"]["summary"])
    print("sys tokens:", ft["sys_tokens"])

    if a.inject:
        blob = json.dumps(ft, ensure_ascii=False, separators=(",", ":"))
        assert '"""' not in blob
        s = LESSON.read_text(encoding="utf-8")
        s, n = re.subn(r"(    # <FT_DATA>\n).*?(\n    # </FT_DATA>)",
                       lambda m: m.group(1) + f'    FT = json.loads(r"""{blob}""")' + m.group(2), s, flags=re.DOTALL)
        assert n == 1, "lesson.py 找不到 <FT_DATA> 標記"
        LESSON.write_text(s, encoding="utf-8")
        hero = {}
        for sc in runs:  # hero 重播「倍數居中」的那一對，不挑最好看的那次
            pairs = list(zip(runs[sc]["trl"], runs[sc]["unsloth"], strict=False))
            ratios = [st.median(t["step_s"][3:]) / st.median(u["step_s"][3:]) for t, u in pairs]
            k = sorted(range(len(pairs)), key=lambda i: ratios[i])[len(pairs) // 2]
            hero[sc] = {tl: {"loss": x["loss"], "step": x["step_s"], "peak": x["peak"], "train": x["train_s"],
                             "run": k + 1}
                        for tl, x in zip(("trl", "unsloth"), pairs[k], strict=True)}
        hero["tok"] = {k: round(v) for k, v in tok_per_ex.items()}
        p = PAGE.read_text(encoding="utf-8")
        p, n = re.subn(r"const HERO = /\*<HERO>\*/.*?/\*</HERO>\*/",
                       lambda m: "const HERO = /*<HERO>*/" + json.dumps(hero, separators=(",", ":")) + "/*</HERO>*/",
                       p, flags=re.DOTALL)
        assert n == 1, "page_content.py 找不到 /*<HERO>*/ 標記"
        for tag, body in (("BA", render_ba(evald)), ("MASK", render_mask(mask["trl"][:2])), ("CAL", render_cal(cal))):
            p, n = re.subn(rf"<!--<{tag}>-->.*?<!--</{tag}>-->",
                           lambda m, t=tag, b=body: f"<!--<{t}>-->{b}<!--</{t}>-->", p, flags=re.DOTALL)
            assert n == 1, f"page_content.py 找不到 <!--<{tag}>--> 標記"
        PAGE.write_text(p, encoding="utf-8")
        print(f"injected: lesson.py FT_DATA {len(blob):,} chars; page_content.py HERO")


if __name__ == "__main__":
    main()
