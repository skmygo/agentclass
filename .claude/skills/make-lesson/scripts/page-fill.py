#!/usr/bin/env python3
"""把課程頁的「內容區」從 page_content.py 填進 scaffold 出來的 index.html，骨架不動、可重複執行。

用法（repo 根目錄）：
    python3 .claude/skills/make-lesson/scripts/page-fill.py content/<topic>/<id>

讀 content/<topic>/<id>/page_content.py（純字串常數的 Python 模組，不會被 build.sh 部署）：
    TITLE        課名（不含「· AI 互動教室」後綴）
    DESCRIPTION  meta description 一句話
    STYLE        <style> 內容（語義色、hero 樣式、頁內小元件）
    WRAP         <div class="wrap"> 內的全部內容（hero、各 section、endnav）
    SCRIPT       hero 互動 JS（不含 <script> 標籤）；可省略
    PANEL_STEPS  外部軌課右欄 molab 面板的 <li> 列表；可省略（沿用模板）
    NB           （慣例）molab notebook 網址——WRAP 裡用 __NB__ 佔位，這裡會代換
    VIDEO        課程影片：YouTube 網址（youtu.be/<id>、watch?v=<id>）或 11 字 id；可省略。
                 有就自動把 .video-box（youtube-nocookie 嵌入、lazy、16:9）插在 hero 的 </h1> 之後
                 （標題先、影片接著）；WRAP 已含 video-box（手動放別處）則不再插。

為什麼不直接整檔重寫 index.html：骨架（header 連結、面板按鈕、共用 css/js 引用、
data-ready-figures）是全站一致的契約，只換內容區才不會不小心弄掉。
為什麼不用 Edit 一段一段改：一次產六頁時，內容放在可重跑的 page_content.py 比散落在
對話裡可靠——模型換了、數字變了，改常數重跑一次就好。

實測踩過的坑（都已內建）：
- 模板頂部的說明註解含 <style>、#molab-panel 等字樣，會干擾 regex 比對 → 先移除註解
- re.sub 的替換字串會解讀 \\u、\\n 等 escape → 一律用 lambda 回傳
- 內容含 Python 三引號（docstring 範例）→ page_content.py 用 r''' 或 r\"\"\" 擇一避開
"""
import html
import importlib.util
import re
import sys
from pathlib import Path

YT_ID = re.compile(r"^[A-Za-z0-9_-]{11}$")


def youtube_id(value: str) -> str:
    """接受 youtu.be/<id>、youtube.com/watch?v=<id>、/embed/<id>、/shorts/<id> 或裸 id。"""
    v = value.strip()
    m = re.search(r"(?:youtu\.be/|[?&]v=|/embed/|/shorts/|/live/)([A-Za-z0-9_-]{11})", v)
    vid = m.group(1) if m else v
    if not YT_ID.match(vid):
        sys.exit(f"✗ VIDEO 不是 YouTube 網址或 11 字影片 id：{value!r}")
    return vid


def video_block(vid: str, title: str) -> str:
    """與 page.html 模板的 .video-box 同版型（樣式在 /shared/lesson.css）。"""
    t = html.escape(f"課程影片：{title}", quote=True)
    return f'''  <div class="video-box" id="video">
    <div class="video-frame">
      <iframe src="https://www.youtube-nocookie.com/embed/{vid}"
        title="{t}" loading="lazy" allowfullscreen
        referrerpolicy="strict-origin-when-cross-origin"
        allow="accelerometer; clipboard-write; encrypted-media; gyroscope; picture-in-picture"></iframe>
    </div>
  </div>
'''


def load_content(lesson_dir: Path):
    src = lesson_dir / "page_content.py"
    if not src.exists():
        sys.exit(f"✗ 找不到 {src}（先寫 page_content.py，欄位見本檔說明）")
    spec = importlib.util.spec_from_file_location("page_content", src)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    for must in ("TITLE", "DESCRIPTION", "STYLE", "WRAP"):
        if not hasattr(mod, must):
            sys.exit(f"✗ page_content.py 缺 {must}")
    return mod


def fill(lesson_dir: Path) -> None:
    page = lesson_dir / "index.html"
    if not page.exists():
        sys.exit(f"✗ 找不到 {page}（先跑 scaffold）")
    c = load_content(lesson_dir)
    t = page.read_text(encoding="utf-8")

    # 模板頂部說明註解先拿掉（它提到 <style> 等字樣會干擾後面的比對；已移除則無事）
    t = re.sub(r"<!DOCTYPE html>\n<!--.*?-->\n", "<!DOCTYPE html>\n", t, count=1, flags=re.DOTALL)

    wrap = c.WRAP.replace("__NB__", getattr(c, "NB", "__NB__"))
    if getattr(c, "VIDEO", None) and "video-box" not in wrap:
        if "</h1>" not in wrap:
            sys.exit("✗ 有 VIDEO 但 WRAP 裡沒有 </h1>（影片要插在 hero 標題之後）")
        wrap = wrap.replace("</h1>", "</h1>\n" + video_block(youtube_id(c.VIDEO), c.TITLE), 1)
    subs = [
        (r"<title>.*?</title>", f"<title>{c.TITLE} · AI 互動教室</title>"),
        (r'<meta name="description" content=".*?">', f'<meta name="description" content="{c.DESCRIPTION}">'),
        (r"<style>.*?</style>", "<style>\n" + c.STYLE.strip("\n") + "\n</style>"),
        (r'<div class="wrap">.*?</div><!-- /wrap -->', '<div class="wrap">\n' + wrap.strip("\n") + "\n\n</div><!-- /wrap -->"),
    ]
    # og 三欄跟著 TITLE/DESCRIPTION 同步（骨架有才填；og:url 用課程目錄名＝根層網址）
    if 'property="og:title"' in t:
        subs += [
            (r'<meta property="og:title" content=".*?">',
             f'<meta property="og:title" content="{c.TITLE} · AI 互動教室">'),
            (r'<meta property="og:description" content=".*?">',
             f'<meta property="og:description" content="{c.DESCRIPTION}">'),
            (r'<meta property="og:url" content=".*?">',
             f'<meta property="og:url" content="https://class.itsmygo.uk/{lesson_dir.name}/">'),
        ]
    if getattr(c, "PANEL_STEPS", None):
        # 只認 molab 面板（#molab-panel）內的第一個 <ol>：WRAP／STYLE 裡若有裸 <ol>（甚至 CSS 註解）不能被誤吃
        _steps = "<ol>\n" + c.PANEL_STEPS.strip("\n") + "\n      </ol>"
        subs.append((r'(<div id="molab-panel">.*?)<ol>.*?</ol>', lambda m, _s=_steps: m.group(1) + _s))
    if getattr(c, "SCRIPT", None):
        # 第一個 inline <script>（<script src=…> 不會被 "<script>" 字面匹配到）＝模板的 hero 互動區
        subs.append((r"<script>.*?</script>", "<script>\n" + c.SCRIPT.strip("\n") + "\n</script>"))

    for pattern, repl in subs:
        new, n = re.subn(pattern, lambda m, r=repl: r(m) if callable(r) else r, t, count=1, flags=re.DOTALL)
        if n == 0:
            sys.exit(f"✗ 在 {page} 找不到要替換的區塊：{pattern[:40]}")
        t = new

    # 骨架自檢：這些是全站契約，填完不能少
    musts = ["</head>", "lesson.css", "splitter.js", 'class="brand"', "endnav"]
    if "molab-panel" in t:
        musts += ['id="molab-panel"', "molab.marimo.io"]
    else:
        musts += ["lesson.js", "nb-status", "data-ready-"]  # figures（預設）或 selector（無圖課）擇一即可
    for must in musts:
        if must not in t:
            sys.exit(f"✗ 填完後骨架缺 {must}——page_content.py 的 WRAP/STYLE 可能吃掉了不該動的東西")
    if "__NB__" in t:
        sys.exit("✗ WRAP 裡有 __NB__ 佔位但 page_content.py 沒定義 NB")

    page.write_text(t, encoding="utf-8")
    print(f"✓ {page}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    fill(Path(sys.argv[1]).resolve())
