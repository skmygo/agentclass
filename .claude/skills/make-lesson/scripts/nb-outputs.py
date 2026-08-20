#!/usr/bin/env python3
"""把 marimo export 後的「渲染結果」印成純文字——驗證外部軌 notebook 的輸出用。

用法（repo 根目錄）：
    python .claude/skills/make-lesson/scripts/nb-outputs.py content/<topic>/<id>/<id>_ext.py [關鍵字 ...]
    # 不給關鍵字：列出每個 cell 的輸出摘要（前 160 字）＋ 錯誤
    # 給關鍵字：只印含任一關鍵字的輸出（每則前 600 字），方便核對左頁要引用的數字

為什麼需要它：`marimo export html` 產的 HTML 只嵌程式碼，渲染結果存在
content/<topic>/<id>/__marimo__/session/<檔名>.json（gitignored）；之前每次驗證都要
手寫一段 json 解析——現在一行。有任何 error 輸出時 exit 1（給 verify-ext.sh 擋部署）。
"""
import html
import json
import re
import sys
from pathlib import Path


def text_of(value: str) -> str:
    value = html.unescape(value)
    value = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def main() -> int:
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    nb = Path(sys.argv[1]).resolve()
    keywords = sys.argv[2:]
    session = nb.parent / "__marimo__" / "session" / f"{nb.name}.json"
    if not session.exists():
        sys.exit(f"✗ 沒有 {session}——先跑 uv run marimo export html --sandbox {nb} -o check.html")
    data = json.loads(session.read_text(encoding="utf-8"))
    cells = data.get("cells", [])
    errors = 0
    print(f"{nb.name}: {len(cells)} cells（marimo {data.get('metadata', {}).get('marimo_version', '?')}）")
    for i, cell in enumerate(cells, 1):
        for out in cell.get("outputs", []):
            raw = json.dumps(out, ensure_ascii=False)
            if out.get("type") == "error" or "Traceback" in raw or "marimo-traceback" in raw:
                errors += 1
                print(f"✗ cell {i}: ERROR {raw[:400]}")
                continue
            payload = out.get("data")
            if not isinstance(payload, dict):
                continue
            for mime, value in payload.items():
                if not isinstance(value, str):
                    continue
                txt = text_of(value)
                if not txt:
                    continue
                if keywords:
                    if any(k in txt for k in keywords):
                        print(f"— cell {i} [{mime}]\n  {txt[:600]}")
                else:
                    print(f"— cell {i} [{mime}] {txt[:160]}")
        for con in cell.get("console", []) or []:
            s = json.dumps(con, ensure_ascii=False)
            if "Traceback" in s or '"stderr"' in s and "Error" in s:
                print(f"  (console) {text_of(s)[:200]}")
    print(f"{'✗' if errors else '✓'} errors: {errors}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
