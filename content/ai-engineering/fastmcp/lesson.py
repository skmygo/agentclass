import marimo

__generated_with = "0.23.16"
app = marimo.App(width="medium", app_title="FastMCP 4：把函式變成 AI 的工具（實驗場）")


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    # 🧪 FastMCP 4：把函式變成 AI 的工具（實驗場）

    這是本課的**實驗場**。左側教學讀到哪，就回到這裡動手做——
    每一格程式碼都可以**直接修改、立即重跑**（點格子右上的 ▶，或按 `Ctrl+Enter`）。
    改壞了也沒關係：重新整理頁面就會回到原版。

    這一課我們**不裝任何套件**：與其背 API，不如親手蓋一個 60 行的迷你 FastMCP，
    看懂它每一個魔法是怎麼變的。
    """
    )
    return


@app.cell
def _():
    import marimo as mo
    return (mo,)


@app.cell
def _():
    # 這課只用標準函式庫＋matplotlib（畫一張圖）
    import inspect
    import json
    import typing

    import matplotlib.pyplot as plt
    return inspect, json, plt, typing


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 1️⃣ 一間飲料店，兩個好用的函式——但 AI 看不到

    你開了間飲料店，寫好了兩個函式：查菜單、下單。
    **人類**工程師看一眼就會用；但對 AI 來說它們是隱形的——
    AI 不知道你有這些函式、不知道參數要填什麼、更沒有一個標準方式呼叫它們。
    """
    )
    return


@app.cell
def _():
    MENU = {
        "珍珠奶茶": {"M": 50, "L": 60},
        "四季春茶": {"M": 30, "L": 35},
        "芒果冰沙": {"M": 70, "L": 85},
    }

    def search_menu(keyword: str) -> dict:
        """搜尋菜單，回傳名稱含關鍵字的品項與各尺寸價格"""
        return {name: p for name, p in MENU.items() if keyword in name}

    def place_order(item: str, size: str) -> str:
        """下單一杯飲料，回傳訂單確認文字"""
        price = MENU[item][size]
        return f"訂單成立：{item}（{size}）NT${price}"

    # 對 Python 來說它們好好的——問題是 AI 進不來
    print(search_menu("茶"))
    print(place_order("珍珠奶茶", "L"))
    return MENU, place_order, search_menu


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 2️⃣ 第一個魔法：@tool 從型別提示長出「說明書」

    FastMCP 最核心的一招：你在函式上加 `@mcp.tool`，它就**讀你的型別提示和
    docstring**，自動生成一份 AI 看得懂的 JSON Schema 說明書。

    下面是這個魔法的迷你重現——`tool()` 用 `inspect` 讀函式簽名，
    把 `keyword: str` 翻成 `{"type": "string"}`、把 docstring 當工具描述：
    """
    )
    return


@app.cell
def _(inspect, typing):
    TOOLS = {}
    PY2JSON = {int: "integer", float: "number", str: "string",
               bool: "boolean", dict: "object", list: "array"}

    def tool(fn):
        """迷你版 @mcp.tool：讀函式簽名，自動生成 JSON Schema 說明書並註冊"""
        hints = typing.get_type_hints(fn)
        sig = inspect.signature(fn)
        props, required = {}, []
        for pname, param in sig.parameters.items():
            props[pname] = {"type": PY2JSON.get(hints.get(pname, str), "string")}
            if param.default is inspect.Parameter.empty:
                required.append(pname)
        TOOLS[fn.__name__] = {
            "fn": fn,
            "spec": {
                "name": fn.__name__,
                "description": (fn.__doc__ or "").strip(),
                "inputSchema": {"type": "object",
                                "properties": props, "required": required},
            },
        }
        return fn
    return TOOLS, tool


@app.cell
def _(TOOLS, place_order, search_menu, tool):
    # 真的 FastMCP 寫法是在 def 上面加 @mcp.tool；
    # 這裡函式已經活著，直接掛上去——效果一模一樣
    tool(search_menu)
    tool(place_order)
    tool_names = list(TOOLS)
    return (tool_names,)


@app.cell
def _(mo, tool_names):
    tool_picker = mo.ui.dropdown(
        options=tool_names, value="search_menu", label="看哪個工具的自動說明書"
    )
    tool_picker
    return (tool_picker,)


@app.cell
def _(TOOLS, json, mo, tool_picker):
    mo.md(
        "AI 拿到的說明書長這樣（全部從型別提示自動生成，你一個字都沒多寫）：\n\n"
        + "```json\n"
        + json.dumps(TOOLS[tool_picker.value]["spec"], ensure_ascii=False, indent=2)
        + "\n```"
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 3️⃣ 第二個魔法：統一插座——tools/list 與 tools/call

    有了說明書還缺一個**標準呼叫方式**。MCP 協定規定所有工具伺服器都聽同樣兩句話：

    - `tools/list`：「你有哪些工具？」→ 回傳全部說明書
    - `tools/call`：「幫我呼叫某工具、參數在此」→ 執行並回傳結果

    下面的 `handle()` 就是迷你 MCP server 的心臟：收 JSON、查註冊表、
    **用說明書驗參數**、執行、回 JSON。看最後一筆請求——漏了參數，
    說明書直接把它擋下來，函式根本不會被執行。
    """
    )
    return


@app.cell
def _(TOOLS):
    def handle(request: dict) -> dict:
        """迷你 MCP server：收 JSON 請求、回 JSON 回應（真實協定是 JSON-RPC 2.0）"""
        method = request.get("method")
        if method == "tools/list":
            return {"tools": [t["spec"] for t in TOOLS.values()]}
        if method == "tools/call":
            name = request.get("params", {}).get("name")
            args = request.get("params", {}).get("arguments", {})
            if name not in TOOLS:
                return {"error": f"沒有這個工具：{name}"}
            schema = TOOLS[name]["spec"]["inputSchema"]
            missing = [k for k in schema["required"] if k not in args]
            if missing:
                return {"error": f"缺少參數：{missing}"}
            try:
                return {"result": TOOLS[name]["fn"](**args)}
            except Exception as e:  # noqa: BLE001 — server 不能因工具爆炸而死
                return {"error": str(e)}
        return {"error": f"不認識的方法：{method}"}
    return (handle,)


@app.cell
def _(handle, json, mo, tool_names):
    _demo = [
        {"method": "tools/call",
         "params": {"name": "search_menu", "arguments": {"keyword": "奶"}}},
        {"method": "tools/call",
         "params": {"name": "place_order",
                    "arguments": {"item": "珍珠奶茶", "size": "L"}}},
        {"method": "tools/call", "params": {"name": "place_order", "arguments": {}}},
    ]
    _lines = [f"server 目前登記了 {len(tool_names)} 個工具。一個 AI 助理接上之後的三筆請求："]
    for _req in _demo:
        _lines.append("\n**AI →**\n```json\n"
                      + json.dumps(_req, ensure_ascii=False) + "\n```")
        _lines.append("**server ←**\n```json\n"
                      + json.dumps(handle(_req), ensure_ascii=False) + "\n```")
    mo.md("\n".join(_lines))
    return


@app.cell
def _(mo):
    kw_input = mo.ui.text(value="茶", label="換你當 AI：搜尋菜單的關鍵字（試試 奶、冰，或亂打）")
    kw_input
    return (kw_input,)


@app.cell
def _(handle, json, kw_input, mo):
    _req = {"method": "tools/call",
            "params": {"name": "search_menu",
                       "arguments": {"keyword": kw_input.value}}}
    mo.md(
        "**你送出的請求**\n```json\n"
        + json.dumps(_req, ensure_ascii=False, indent=2)
        + "\n```\n**server 回應**\n```json\n"
        + json.dumps(handle(_req), ensure_ascii=False, indent=2)
        + "\n```"
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 4️⃣ FastMCP 4 的招牌：斷線也記得你

    新版 MCP 協定是 **sessionless**：每個請求各自獨立，沒有「保持連線」這回事。
    那伺服器要怎麼記住「小明點過什麼」？FastMCP 4 的答案是 `UserSession`——
    伺服器端幫**每個使用者**留一個置物櫃，用認證身分當鑰匙。

    下面用迷你版重演這個概念（沒有帳號系統，用 session id 代替認證身分）。
    拉動滑桿重播請求：小明和小美的請求**交錯抵達、各自獨立**，
    但伺服器的置物櫃始終分得清清楚楚。
    """
    )
    return


@app.cell
def _(mo):
    SCRIPT = [
        ("ming", "四季春茶"),
        ("mei", "珍珠奶茶"),
        ("ming", "珍珠奶茶"),
        ("mei", "芒果冰沙"),
        ("ming", "四季春茶"),
        ("mei", "珍珠奶茶"),
    ]
    step_slider = mo.ui.slider(start=0, stop=len(SCRIPT), step=1, value=3,
                               label="重播請求到第幾筆", show_value=True)
    step_slider
    return SCRIPT, step_slider


@app.cell
def _(SCRIPT, mo, step_slider):
    # 每筆請求獨立進來，伺服器只憑 session id 開對置物櫃
    sessions = {}
    for _sid, _item in SCRIPT[: step_slider.value]:
        sessions.setdefault(_sid, []).append(_item)
    _who = {"ming": "小明", "mei": "小美"}
    _lines = [f"重播到第 **{step_slider.value}** 筆，伺服器端的置物櫃："]
    for _sid in ("ming", "mei"):
        _items = sessions.get(_sid, [])
        _lines.append(f"- 🧋 **{_who[_sid]}**（session `{_sid}`）："
                      + ("、".join(_items) if _items else "（還沒點過東西）"))
    mo.md("\n".join(_lines))
    return (sessions,)


@app.cell
def _(MENU, plt, sessions):
    # 各 session 的累計消費（M 杯價格）——狀態分離的視覺證據
    _totals = {sid: sum(MENU[i]["M"] for i in items) for sid, items in sessions.items()}
    _names = ["ming", "mei"]
    _vals = [_totals.get(n, 0) for n in _names]
    _fig, _ax = plt.subplots(figsize=(6, 3.2))
    _bars = _ax.bar(["Ming", "Mei"], _vals, color=["#4C72B0", "#DD8452"], width=0.5)
    _ax.bar_label(_bars, fmt="NT$%g")
    _ax.set_ylabel("total spend (NT$)")
    _ax.set_ylim(0, 200)
    _ax.set_title("one server, separate session buckets")
    _fig.tight_layout()
    _fig
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    真的 FastMCP 4 裡，這件事長這樣（`session` 由框架自動注入、
    **不會出現在工具說明書裡**，鑰匙是使用者的認證身分）：

    ```python
    from fastmcp import FastMCP
    from fastmcp.server.sessions import UserSession

    mcp = FastMCP("Assistant")

    @mcp.tool
    async def remember(fact: str, session: UserSession) -> str:
        facts = await session.get("facts", default=[])
        facts.append(fact)
        await session.set("facts", facts)
        return f"Remembered {len(facts)} facts."
    ```
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 5️⃣ 你的實驗區

    下面這格是你的，改完按 ▶ 重跑。建議挑戰（由易到難）：

    1. **LEVEL 1**：在 1️⃣ 的 `MENU` 加一款你愛喝的，回到 3️⃣ 的搜尋框搜搜看。
    2. **LEVEL 2**：下面已經幫你開了頭——寫一個 `recommend(budget: int)` 工具並
       註冊，用 `handle()` 呼叫它。注意說明書是自動長出來的：改型別提示看 schema 跟著變。
    3. **LEVEL 3**：讓 `handle()` 多聽一句 `resources/list`，回傳
       `{"resources": [{"uri": "menu://all", "name": "完整菜單"}]}`——
       這就是 MCP 的第二種能力「資源」的雛形。

    做完記得：**點左側教學頁的「下載 .py」把你的版本帶走**，
    在自己電腦用 `uvx marimo edit lesson.py` 就能繼續玩。
    """
    )
    return


@app.cell
def _(MENU, handle, json, tool):
    # ===== 你的實驗區 =====
    def recommend(budget: int) -> list:
        """推薦所有 M 杯價格不超過預算的品項"""
        return [name for name, p in MENU.items() if p["M"] <= budget]

    tool(recommend)
    _resp = handle({"method": "tools/call",
                    "params": {"name": "recommend", "arguments": {"budget": 60}}})
    print(json.dumps(_resp, ensure_ascii=False))
    return


if __name__ == "__main__":
    app.run()
