#!/usr/bin/env python3
"""publish-videos 第 2 步：照 video/.plan.json 逐支上傳 → 寫入該課 page_content.py 的 VIDEO → 重跑 page-fill → 播放清單。

用法（repo 根執行，先跑 plan.py 且 show 通過）：
    python3 .claude/skills/publish-videos/scripts/publish.py

可重跑：已完成的課（page_content.py 有 VIDEO）在下一次 plan 會變成 skip，所以中途失敗直接從 plan.py 重來。
dry-run（plan 時給 --dry-run）：不碰 YouTube，用假 id DRYRUN00001…，其餘步驟照跑——只在測試用的 worktree 裡做，
因為假 id 會寫進 page_content.py。
"""

from __future__ import annotations

import ast
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
VIDEO_DIR = ROOT / "video"
CONFIG = VIDEO_DIR / "config.json"
PLAN = VIDEO_DIR / ".plan.json"
RESULT = VIDEO_DIR / ".publish-result.json"
UPLOAD = VIDEO_DIR / "upload.py"
PAGE_FILL = ROOT / ".claude/skills/make-lesson/scripts/page-fill.py"
sys.path.insert(0, str(Path(__file__).resolve().parent))
from plan import load_site, page_consts


def set_video_constant(pc: Path, url: str) -> None:
    """VIDEO 已存在就換掉那一行；沒有就插在 DESCRIPTION 的下一行（用 ast 找結尾行，多行字串也對）。"""
    src = pc.read_text(encoding="utf-8")
    lines = src.splitlines(keepends=True)
    video_node = desc_node = None
    for node in ast.parse(src).body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            if node.targets[0].id == "VIDEO":
                video_node = node
            elif node.targets[0].id == "DESCRIPTION":
                desc_node = node
    new_line = f'VIDEO = "{url}"  # 課程影片（YouTube；publish-videos skill 上傳）\n'
    if video_node:
        lines[video_node.lineno - 1 : video_node.end_lineno] = [new_line]
    elif desc_node:
        lines.insert(desc_node.end_lineno, new_line)
    else:
        sys.exit(f"✗ {pc} 沒有 DESCRIPTION，不知道 VIDEO 要插哪")
    pc.write_text("".join(lines), encoding="utf-8")


def course_order_ids(topic: str, lessons: dict, topics: dict, new_lesson: str) -> list[str]:
    """這個主題全部影片的課程順序（YouTube id），這一課用 NEW 佔位——給 upload.py 算播放清單插入位置。"""
    out = []
    for lid in topics[topic]["order"]:
        if lid == new_lesson:
            out.append("NEW")
            continue
        pc = lessons[lid]["dir"] / "page_content.py"
        vid = page_consts(pc).get("VIDEO") if pc.exists() else None
        if vid:
            out.append(vid.rsplit("/", 1)[-1])
    return out


def main() -> None:
    if not PLAN.exists():
        sys.exit(f"✗ 沒有 {PLAN}，先跑 plan.py")
    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    if plan["errors"]:
        sys.exit("✗ 計畫有錯誤，先修再跑 plan.py：\n  - " + "\n  - ".join(plan["errors"]))
    todo = [it for it in plan["items"] if it["status"] != "skip"]
    missing = [it["lesson_id"] for it in todo if not it["tags"]]
    if missing:
        sys.exit(f"✗ 還沒填 tags：{', '.join(missing)}")
    if not todo:
        print("沒有要上傳的影片（全部已有 VIDEO）。")
        RESULT.write_text(json.dumps({"dry_run": plan["dry_run"], "items": []}, ensure_ascii=False, indent=2), encoding="utf-8")
        return

    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    lessons, topics = load_site()
    dry = plan["dry_run"]
    results: list[dict] = []
    if RESULT.exists():
        RESULT.unlink()

    for n, it in enumerate(todo, 1):
        lid, topic = it["lesson_id"], it["topic"]
        pc = lessons[lid]["dir"] / "page_content.py"
        tags = list(it["tags"]) + list(it["fixed_tags"])
        print(f"\n━━ {n}/{len(todo)}  {it['file']} → {lid}")
        if dry:
            video_id = f"DRYRUN{n:05d}"
            playlist_id = cfg["playlists"].get(topic) or "PLDRYRUN"
            print(f"  【dry-run】略過上傳，假 id {video_id}")
        else:
            playlist_id = cfg["playlists"].get(topic)
            playlist_title = cfg["playlist_title_template"].format(topic_name=it["topic_name"], site_name=cfg["site_name"])
            out = VIDEO_DIR / ".upload-result.json"
            cmd = [
                "uv", "run", str(UPLOAD), str(VIDEO_DIR / "data" / it["file"]),
                "--title", it["title"], "--description", it["description"], "--tags", ",".join(tags),
                "--category", cfg["category"], "--language", cfg["language"], "--privacy", cfg["privacy"],
                "--playlist-order", ",".join(course_order_ids(topic, lessons, topics, lid)),
                "--playlist-privacy", cfg["playlist_privacy"], "--no-browser", "--json-out", str(out),
            ]
            cmd += ["--playlist-id", playlist_id] if playlist_id else ["--playlist-title", playlist_title]
            if it["status"] == "replace":
                cmd.append("--force")
            r = subprocess.run(cmd, cwd=ROOT, check=False)
            if r.returncode != 0 or not out.exists():
                write_result(plan, results)
                sys.exit(f"✗ 上傳失敗（{it['file']}）。已完成 {len(results)} 支；修好後重跑 plan.py → publish.py，已完成的會自動跳過。")
            res = json.loads(out.read_text(encoding="utf-8"))
            out.unlink()
            video_id, playlist_id = res["video_id"], res.get("playlist_id")
            if playlist_id and cfg["playlists"].get(topic) != playlist_id:
                cfg["playlists"][topic] = playlist_id
                CONFIG.write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                print(f"  播放清單 id 已記到 config.json：{topic} → {playlist_id}")

        url = f"https://youtu.be/{video_id}"
        set_video_constant(pc, url)
        r = subprocess.run([sys.executable, str(PAGE_FILL), str(lessons[lid]["dir"])], cwd=ROOT, check=False)
        if r.returncode != 0:
            write_result(plan, results)
            sys.exit(f"✗ page-fill 失敗（{lid}）。VIDEO 已寫進 {pc}，修好 page_content.py 後重跑 page-fill 與 ship.sh。")
        results.append({
            "lesson_id": lid, "topic": topic, "file": it["file"], "video_id": video_id, "url": url,
            "playlist_id": playlist_id, "title": it["title"], "status": it["status"],
            "page_content": str(pc.relative_to(ROOT)), "index_html": str((lessons[lid]["dir"] / "index.html").relative_to(ROOT)),
        })
        print(f"  ✓ {lid}：{url}  已寫 VIDEO 並重填 index.html")

    if not dry:
        # 連續加入時 YouTube 的清單查詢有幾秒延遲，位置可能算錯；每個主題整理一次就確定了
        for topic in sorted({r["topic"] for r in results}):
            pid = cfg["playlists"].get(topic)
            if not pid:
                continue
            order = ",".join(v for v in course_order_ids(topic, lessons, topics, "") if v != "NEW")
            subprocess.run(["uv", "run", str(UPLOAD), "--playlist-sort", "--playlist-id", pid, "--playlist-order", order, "--no-browser"], cwd=ROOT, check=False)
    write_result(plan, results)
    print(f"\n✓ 完成 {len(results)} 支。結果在 {RESULT}，接著跑 ship.sh。")


def write_result(plan: dict, results: list[dict]) -> None:
    RESULT.write_text(json.dumps({
        "dry_run": plan["dry_run"], "finished": datetime.now(UTC).isoformat(timespec="seconds"), "items": results,
    }, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
