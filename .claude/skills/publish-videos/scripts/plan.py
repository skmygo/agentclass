#!/usr/bin/env python3
"""publish-videos 第 1 步：掃 video/ 的影片 → 對到課程 → 依 skill 的 config.json 產 metadata → 前置檢查 → 寫 video/.plan.json

用法（repo 根執行）：
    python3 .claude/skills/publish-videos/scripts/plan.py                 # 建計畫＋前置檢查（git 乾淨、token 可用）
    python3 .claude/skills/publish-videos/scripts/plan.py --topic <主題>  # 簡稱檔名（L00-why.mp4）只在這個主題裡找課
    python3 .claude/skills/publish-videos/scripts/plan.py --replace <id>  # 該課已有 VIDEO 也要重傳（重錄）
    python3 .claude/skills/publish-videos/scripts/plan.py --dry-run       # 測試管線用：不查 token，publish 會用假 id
    python3 .claude/skills/publish-videos/scripts/plan.py tags <id> <tag> [<tag>...]   # 寫入某課的 tags
    python3 .claude/skills/publish-videos/scripts/plan.py show            # 印出完整計畫表（給使用者確認）
    python3 .claude/skills/publish-videos/scripts/plan.py uploader        # 印出上傳核心 upload.py 的路徑

影片放 video/（video/data/ 也掃）。檔名規則：<課程id>.mp4、NN-<課程id>.mp4 或 LNN-<課程id>.mp4
（前置的「一個字母＋數字＋分隔符」會被去掉；NN 只用來排上傳順序）。去掉前綴後：
  1. 完全等於 content/<topic>/<id>/ 的目錄名 → 就是那一課；
  2. 否則當成簡稱：剛好只有一課的 id 以「-<簡稱>」結尾（why → mlops-why）→ 就是那一課。
對不到、或簡稱對到不只一課，就整批停下，什麼都不上傳——規則是確定性的，不做相似度猜測。

上傳核心是 youtube-upload plugin 的 upload.py（憑證跟著它，在 ~/.config/youtube-upload/），repo 裡不再放一份。

為什麼 tags 留空給人／模型填：標題與說明是課程正本（page_content.py）的固定轉換，tags 需要理解內容；
但 tags 一定會出現在計畫表裡、經使用者確認才上傳，而且基底 tags（config 的 base_tags＋topic_tags）由程式補齊。
"""

from __future__ import annotations

import argparse
import ast
import difflib
import json
import os
import re
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
SKILL_DIR = Path(__file__).resolve().parents[1]
VIDEO_DIR = ROOT / "video"  # 只放影片與本次流程的暫存：整個清空也不會弄丟設定
SCAN_DIRS = (VIDEO_DIR, VIDEO_DIR / "data")
CONFIG = SKILL_DIR / "config.json"
PLAN = VIDEO_DIR / ".plan.json"
UPLOAD_GLOB = ".claude/plugins/cache/*/youtube-upload/*/skills/youtube-upload/scripts/upload.py"

VIDEO_EXTS = (".mp4", ".mov", ".mkv", ".webm")
FILENAME_RE = re.compile(r"^(?:[A-Za-z]?\d+[-_ ]?)?(.+)$")
TITLE_MAX, DESC_MAX = 100, 5000
TAG_MAX, TAGS_MIN, TAGS_MAX, TAGS_TOTAL_MAX = 30, 3, 8, 500


def find_upload() -> Path | None:
    """youtube-upload plugin 的 upload.py：YT_UPLOAD 指定的路徑，否則 plugin 快取裡版號最大的那份。"""
    env = os.environ.get("YT_UPLOAD")
    if env:
        return Path(env) if Path(env).is_file() else None

    def version(p: Path) -> tuple[int, ...]:
        return tuple(int(x) if x.isdigit() else 0 for x in p.parents[3].name.split("."))

    return max(Path.home().glob(UPLOAD_GLOB), key=version, default=None)


def load_config() -> dict:
    if not CONFIG.exists():
        sys.exit(f"✗ 找不到 {CONFIG}")
    return json.loads(CONFIG.read_text(encoding="utf-8"))


def load_site() -> tuple[dict, dict]:
    """lessons: id → {topic, dir}；topics: slug → {name, order}（order＝主題頁的課程順序）。"""
    lessons, topics = {}, {}
    for tdir in sorted((ROOT / "content").iterdir()):
        if not tdir.is_dir() or tdir.name == "shared" or not (tdir / "index.html").exists():
            continue
        html = (tdir / "index.html").read_text(encoding="utf-8")
        m = re.search(r"<title>(.*?)</title>", html)
        name = m.group(1).split(" · ")[0].strip() if m else tdir.name
        ids = [d.name for d in sorted(tdir.iterdir()) if d.is_dir() and (d / "index.html").exists()]
        order = [i for i in re.findall(r'href="/([a-z0-9-]+)/"', html) if i in ids]
        order += [i for i in ids if i not in order]  # 主題頁沒列到的排最後
        topics[tdir.name] = {"name": name, "order": order}
        for lid in ids:
            lessons[lid] = {"topic": tdir.name, "dir": tdir / lid}
    return lessons, topics


def page_consts(pc: Path) -> dict:
    out = {}
    for node in ast.parse(pc.read_text(encoding="utf-8")).body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            v = node.value
            if isinstance(v, ast.Constant) and isinstance(v.value, str):
                out[node.targets[0].id] = v.value
            elif isinstance(v, (ast.List, ast.Tuple)) and all(isinstance(e, ast.Constant) for e in v.elts):
                out[node.targets[0].id] = [e.value for e in v.elts]
    return out


def match_lesson(stem: str, lessons: dict, topic: str | None = None) -> tuple[str | None, str]:
    """回傳（課程 id, 錯誤訊息）。topic 有給時只在那個主題裡找。"""
    stripped = FILENAME_RE.match(stem).group(1)
    for cand in (stem, stripped):
        if cand in lessons:
            if topic and lessons[cand]["topic"] != topic:
                return None, f"課程 {cand} 在主題 {lessons[cand]['topic']}，不在 --topic {topic}"
            return cand, ""
    pool = [lid for lid, info in lessons.items() if not topic or info["topic"] == topic]
    where = f"主題 {topic} 的" if topic else "任何"
    hits = [lid for lid in pool if lid.endswith("-" + stripped)]
    if len(hits) == 1:
        return hits[0], ""
    if hits:
        return None, f"簡稱 {stripped!r} 對到不只一課（{', '.join(sorted(hits))}）：檔名改用完整課程 id，或加 --topic 縮小範圍"
    near = difflib.get_close_matches(stripped, pool, n=3, cutoff=0.5)
    hint = f"（相近的課程 id：{', '.join(near)}）" if near else ""
    return None, f"檔名去掉前綴後是 {stripped!r}，不是{where}課程目錄名，也不是哪一課 id 的結尾{hint}"


def probe_duration(path: Path) -> float | None:
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
            capture_output=True, text=True, timeout=30, check=False,
        ).stdout.strip()
        return round(float(out), 1) if out else None
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return None


def build_plan(replace: set[str], dry_run: bool, skip_auth: bool, topic_filter: str | None = None) -> dict:
    cfg = load_config()
    lessons, topics = load_site()
    site, site_name = cfg["site_url"].rstrip("/"), cfg["site_name"]
    errors: list[str] = []
    items: list[dict] = []
    seen: dict[str, str] = {}

    if topic_filter and topic_filter not in topics:
        sys.exit(f"✗ --topic {topic_filter}：沒有這個主題（有：{', '.join(topics)}）")
    files = sorted(
        (p for d in SCAN_DIRS if d.is_dir() for p in d.iterdir() if p.is_file() and p.suffix.lower() in VIDEO_EXTS),
        key=lambda p: p.name,
    )
    if not files:
        errors.append(f"{VIDEO_DIR} 裡沒有影片檔（{'/'.join(VIDEO_EXTS)}）")

    for f in files:
        lid, why = match_lesson(f.stem, lessons, topic_filter)
        if not lid:
            errors.append(f"{f.name}：{why}")
            continue
        if lid in seen:
            errors.append(f"{f.name} 與 {seen[lid]} 都對到課程 {lid}，一課只能一支")
            continue
        seen[lid] = f.name
        ldir, topic = lessons[lid]["dir"], lessons[lid]["topic"]
        pc = ldir / "page_content.py"
        if not pc.exists():
            errors.append(f"{f.name}：課程 {lid} 沒有 page_content.py（舊式手寫頁），無法自動嵌入——請先把這課遷到 page_content.py")
            continue
        consts = page_consts(pc)
        if "TITLE" not in consts or "DESCRIPTION" not in consts:
            errors.append(f"{f.name}：{pc} 缺 TITLE 或 DESCRIPTION")
            continue
        tname = topics[topic]["name"]
        title = cfg["title_template"].format(title=consts["TITLE"], site_name=site_name)
        description = cfg["description_template"].format(
            description=consts["DESCRIPTION"], lesson_url=f"{site}/{lid}/", topic_name=tname,
            topic_url=f"{site}/{topic}/", site_url=site, site_name=site_name,
        )
        problems = []
        if len(title) > TITLE_MAX:
            problems.append(f"標題 {len(title)} 字超過 {TITLE_MAX}")
        if len(description) > DESC_MAX:
            problems.append(f"說明 {len(description)} 字超過 {DESC_MAX}")
        if any(c in title + description for c in "<>"):
            problems.append("標題或說明含 < >（YouTube 拒收）")
        if problems:
            errors.append(f"{f.name}：" + "；".join(problems))
            continue
        existing = consts.get("VIDEO")
        if existing and lid not in replace:
            status = "skip"
        elif existing:
            status = "replace"
        else:
            status = "new"
        items.append({
            "file": f.name, "path": str(f.relative_to(ROOT)), "short_name": lid not in (f.stem, FILENAME_RE.match(f.stem).group(1)),
            "lesson_id": lid, "topic": topic, "topic_name": tname,
            "order_index": topics[topic]["order"].index(lid),
            "status": status, "existing_video": existing,
            "title": title, "description": description,
            "fixed_tags": list(cfg.get("base_tags", [])) + list(cfg.get("topic_tags", {}).get(topic, [])),
            "tags": consts.get("VIDEO_TAGS") or None,
            "size_mb": round(f.stat().st_size / 1048576, 1), "duration_s": probe_duration(f),
        })

    for lid in replace:
        if lid not in seen:
            errors.append(f"--replace {lid}：video/ 裡沒有這課的影片")

    if not dry_run:
        dirty = subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"], cwd=ROOT, capture_output=True, text=True, check=False).stdout.strip()
        if dirty:
            errors.append("git 工作樹有未 commit 的改動（會混進自動 commit）：先 commit 或 stash\n    " + dirty.replace("\n", "\n    "))
        if not skip_auth and any(i["status"] != "skip" for i in items):
            upload = find_upload()
            if not upload:
                errors.append("找不到 youtube-upload plugin 的 upload.py：先裝 sk-work-plugins 的 youtube-upload plugin，或用 YT_UPLOAD 指定路徑")
            else:
                r = subprocess.run(["uv", "run", str(upload), "--check-auth"], cwd=ROOT, capture_output=True, text=True, check=False)
                if r.returncode != 0:
                    errors.append("YouTube 授權不可用：" + (r.stderr.strip().splitlines() or ["?"])[-1])

    return {
        "created": datetime.now(UTC).isoformat(timespec="seconds"),
        "dry_run": dry_run,
        "config": {k: cfg[k] for k in ("privacy", "category", "language", "playlist_privacy", "playlist_title_template", "site_name")},
        "items": items,
        "errors": errors,
    }


def fmt_duration(s: float | None) -> str:
    return f"{int(s // 60)}:{int(s % 60):02d}" if s else "?"


def show(plan: dict, *, full: bool) -> None:
    print(f"計畫（{plan['created']}）{'【dry-run】' if plan['dry_run'] else ''}  隱私={plan['config']['privacy']}")
    for i, it in enumerate(plan["items"], 1):
        mark = {"new": "上傳", "replace": "重傳", "skip": "跳過（已有 VIDEO）"}[it["status"]]
        short = "（簡稱對應）" if it.get("short_name") else ""
        print(f"\n{i:2d}. {it['file']}  →  {it['topic']}/{it['lesson_id']}{short}  [{mark}]  {it['size_mb']} MB, {fmt_duration(it['duration_s'])}")
        print(f"    標題：{it['title']}")
        if full:
            first = it["description"].split("\n")[0]
            print(f"    說明：{first[:80]}{'…' if len(first) > 80 else ''}  ＋課程／主題／首頁連結")
            tags = (it["tags"] or []) + it["fixed_tags"]
            print(f"    tags：{', '.join(tags) if it['tags'] else '（未填）'}")
        if it["status"] == "replace":
            print(f"    既有影片 {it['existing_video']} 會被新影片取代（舊影片留在 YouTube，需要的話自己刪）")
    todo = [it for it in plan["items"] if it["status"] != "skip"]
    missing = [it["lesson_id"] for it in todo if not it["tags"]]
    print(f"\n要上傳 {len(todo)} 支，跳過 {len(plan['items']) - len(todo)} 支。")
    if plan["errors"]:
        print("\n✗ 有問題，不能上傳：")
        for e in plan["errors"]:
            print(f"  - {e}")
    if full and missing:
        print(f"✗ 還沒填 tags：{', '.join(missing)}（用 plan.py tags <id> <tag>...）")


def validate_tags(tags: list[str], fixed: list[str]) -> list[str]:
    tags = [t.strip() for t in tags if t.strip()]
    probs = []
    if not TAGS_MIN <= len(tags) <= TAGS_MAX:
        probs.append(f"要 {TAGS_MIN}–{TAGS_MAX} 個（目前 {len(tags)}）")
    for t in tags:
        if len(t) > TAG_MAX:
            probs.append(f"{t!r} 超過 {TAG_MAX} 字")
        if any(c in t for c in "<>,"):
            probs.append(f"{t!r} 含 < > 或逗號")
    low = {t.lower() for t in fixed}
    dup = [t for t in tags if t.lower() in low]
    if dup:
        probs.append(f"與固定 tags 重複：{', '.join(dup)}")
    if len({t.lower() for t in tags}) != len(tags):
        probs.append("有重複")
    total = sum(len(t) for t in tags + fixed) + len(tags) + len(fixed)
    if total > TAGS_TOTAL_MAX:
        probs.append(f"總長度 {total} 超過 {TAGS_TOTAL_MAX}")
    if probs:
        sys.exit("✗ tags 不合規：" + "；".join(probs))
    return tags


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd")
    b = sub.add_parser("build", help="建計畫（預設）")
    b.add_argument("--replace", action="append", default=[], help="課程 id；已有 VIDEO 也要重傳，可重複")
    b.add_argument("--topic", help="主題目錄名（如 mlops）：只在這個主題裡對課，簡稱檔名建議加")
    b.add_argument("--dry-run", action="store_true")
    b.add_argument("--no-auth-check", action="store_true")
    t = sub.add_parser("tags")
    t.add_argument("lesson_id")
    t.add_argument("tags", nargs="+")
    sub.add_parser("show")
    sub.add_parser("uploader", help="印出上傳核心 upload.py 的路徑")
    # 沒給子命令＝build
    if argv is None:
        argv = sys.argv[1:]
    if not argv or argv[0].startswith("-"):
        argv = ["build", *argv]
    a = p.parse_args(argv)

    if a.cmd == "uploader":
        upload = find_upload()
        if not upload:
            sys.exit("✗ 找不到 youtube-upload plugin 的 upload.py（裝 plugin，或用 YT_UPLOAD 指定路徑）")
        print(upload)
        return

    if a.cmd == "build":
        replace = {x.strip() for r in a.replace for x in r.split(",") if x.strip()}
        plan = build_plan(replace, a.dry_run, a.no_auth_check, a.topic)
        VIDEO_DIR.mkdir(exist_ok=True)
        PLAN.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
        show(plan, full=False)
        print(f"\n計畫已寫到 {PLAN}")
        sys.exit(1 if plan["errors"] else 0)

    if not PLAN.exists():
        sys.exit(f"✗ 沒有 {PLAN}，先跑 plan.py 建計畫")
    plan = json.loads(PLAN.read_text(encoding="utf-8"))

    if a.cmd == "tags":
        for it in plan["items"]:
            if it["lesson_id"] == a.lesson_id:
                it["tags"] = validate_tags(a.tags, it["fixed_tags"])
                PLAN.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
                print(f"✓ {a.lesson_id} tags：{', '.join(it['tags'])}  ＋固定：{', '.join(it['fixed_tags'])}")
                return
        sys.exit(f"✗ 計畫裡沒有課程 {a.lesson_id}")

    if a.cmd == "show":
        show(plan, full=True)
        todo = [it for it in plan["items"] if it["status"] != "skip"]
        sys.exit(1 if plan["errors"] or any(not it["tags"] for it in todo) else 0)


if __name__ == "__main__":
    main()
