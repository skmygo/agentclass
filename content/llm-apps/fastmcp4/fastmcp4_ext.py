# FastMCP 4：把函式變成 AI 工具，一發請求不用握手
# 不需要 GPU——molab 免費 CPU 環境即可全程執行（本課不連任何外部服務，全部在本機跑）。
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "marimo",
#     "fastmcp==4.0.0b1",
#     "fastmcp-slim==4.0.0b1",
#     "httpx",
#     "uvicorn",
# ]
# ///
import marimo

__generated_with = "0.23.16"
app = marimo.App(width="medium", app_title="FastMCP 4：把函式變成 AI 工具，一發請求不用握手")


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    # 🔌 FastMCP 4：把函式變成 AI 工具，一發請求不用握手

    上一課你手寫了工具的 JSON Schema 說明書、手組了兩回合對話。**MCP**（Model Context Protocol）
    把這整件事標準化：你蓋一台「工具伺服器」，任何支援 MCP 的 AI 客戶端（Claude Desktop、
    Claude Code、Cursor……）都能直接接上來用你的函式。**FastMCP** 是用 Python 蓋這種伺服器
    最省事的方法——一個裝飾器，說明書自動生成、參數自動把關。

    這份 notebook 用的是 **FastMCP 4.0（beta 1）**。4.0 最大的改版是協定變成**無狀態**
    （sessionless）：以前客戶端要先握手、拿到 session id、之後每個請求都帶著它；
    現在**每個請求自己帶齊所有資訊**，任何一台伺服器副本都能處理。我們會親眼看到
    兩種協定的差別，再學 4.0 怎麼在無狀態協定上做有狀態的應用。

    內容：

    1. 蓋第一台伺服器：`@mcp.tool`，用 in-memory 客戶端連上它
    2. 工具之外：`@mcp.resource`（給 AI 讀的資料）與 `@mcp.prompt`（話術範本）
    3. **無狀態協定**：起一台真的 HTTP 伺服器，對照新舊協定、用一發裸 POST 呼叫工具
    4. 無狀態協定上的有狀態應用：`SessionId` 與 session 工具
    5. 怎麼把伺服器接給真的 AI 客戶端

    從第一格往下全部執行即可（首次安裝套件約 1 分鐘）。
    """
    )
    return


@app.cell
def _():
    import json
    import socket
    import threading
    import time

    import httpx
    import marimo as mo
    import uvicorn
    from fastmcp import Client, FastMCP
    from fastmcp.exceptions import ToolError
    from fastmcp.server.sessions import SessionId, SessionProvider, get_session
    return (
        Client,
        FastMCP,
        SessionId,
        SessionProvider,
        ToolError,
        get_session,
        httpx,
        json,
        mo,
        socket,
        threading,
        time,
        uvicorn,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 1️⃣ 蓋第一台伺服器：一個裝飾器

    `FastMCP("名字")` 建一台伺服器，`@mcp.tool` 把普通函式變成工具。
    注意你**沒有寫任何 schema**：FastMCP 從型別提示（`a: int`）、預設值（`limit: int = 3`）
    與 docstring 自動生成說明書——上一課手寫的那坨 JSON，現在是免費的。
    """
    )
    return


@app.cell
def _(FastMCP):
    mcp = FastMCP("茶飲店")

    MENU = [
        {"name": "珍珠奶茶", "price": 60},
        {"name": "紅茶", "price": 30},
        {"name": "綠茶拿鐵", "price": 70},
        {"name": "滷肉飯", "price": 45},
    ]

    @mcp.tool
    def add(a: int, b: int) -> int:
        """把兩個整數相加。"""
        return a + b

    @mcp.tool
    def search_menu(keyword: str, limit: int = 3) -> list[dict]:
        """依關鍵字搜尋菜單，回傳最多 limit 筆品項（含價格）。"""
        return [m for m in MENU if keyword in m["name"]][:limit]
    return MENU, add, mcp, search_menu


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ### 用 in-memory 客戶端連上它

    `Client(mcp)` 直接連到同一個 process 裡的伺服器實例——不開網路、不起子行程，
    測試與教學最方便。`list_tools()` 拿到的就是自動生成的說明書：
    看 `input_schema`，`limit` 有 `default: 3`、`keyword` 在 `required` 裡，
    全部來自你的函式簽名。
    """
    )
    return


@app.cell
async def _(Client, add, json, mcp, mo, search_menu):
    async with Client(mcp) as _c:
        tool_list = await _c.list_tools()

    _ = (add, search_menu)   # 確保工具註冊在這格之前完成
    mo.vstack([
        mo.md(f"伺服器 `{mcp.name}` 有 **{len(tool_list)} 個工具**："),
        *[
            mo.md(
                f"**`{t.name}`** — {t.description}\n\n```json\n{json.dumps(t.input_schema, ensure_ascii=False, indent=2)}\n```"
            )
            for t in tool_list
        ],
    ])
    return (tool_list,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ### 呼叫工具、以及「餵錯參數會怎樣」

    `call_tool(名字, 參數 dict)` 回傳的 `.data` 是 Python 值（不是字串）。
    第三個呼叫故意把 `a` 給成 `"two"`：FastMCP 在**進你的函式之前**就用 pydantic 擋下，
    回一個 `ToolError` 說明哪個欄位錯——你的函式永遠只會收到合法參數。
    """
    )
    return


@app.cell
async def _(Client, ToolError, mcp, mo, tool_list):
    _ = tool_list
    async with Client(mcp) as _c:
        _r1 = await _c.call_tool("add", {"a": 2, "b": 3})
        _r2 = await _c.call_tool("search_menu", {"keyword": "茶"})
        try:
            await _c.call_tool("add", {"a": "two", "b": 3})
            _err = "（沒有報錯？）"
        except ToolError as _e:
            _err = str(_e).splitlines()[0:3]
    mo.md(
        f"""
    | 呼叫 | `.data` |
    |---|---|
    | `add(a=2, b=3)` | `{_r1.data}`（型別 `{type(_r1.data).__name__}`） |
    | `search_menu(keyword="茶")` | `{_r2.data}` |
    | `add(a="two", b=3)` | 🛑 `ToolError`：`{_err}` |
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 2️⃣ 工具之外：resources 與 prompts

    MCP 伺服器能給 AI 的不只是「可以呼叫的動作」：

    - **Resource**：給 AI **讀**的資料，用 URI 定址（像 `menu://today`）。
      URI 裡放 `{參數}` 就變成 **template**，例如 `menu://item/{name}`。
    - **Prompt**：可重用的話術範本，帶參數，讓客戶端「一鍵套用」。

    三者的差別：tool 是模型主動呼叫、resource 是應用程式決定要不要餵給模型、
    prompt 是使用者挑選。先都註冊上去：
    """
    )
    return


@app.cell
def _(MENU, mcp):
    @mcp.resource("menu://today")
    def today_menu() -> str:
        """今日完整菜單（純文字）"""
        return " / ".join(f"{m['name']} {m['price']}" for m in MENU)

    @mcp.resource("menu://item/{name}")
    def menu_item(name: str) -> dict:
        """單一品項的詳細資料"""
        return next((m for m in MENU if m["name"] == name), {"name": name, "error": "查無此品項"})

    @mcp.prompt
    def order_helper(budget: int) -> str:
        """產生「點餐助理」的系統提示"""
        return f"你是茶飲店的點餐助理。顧客預算 {budget} 元，請從菜單中推薦不超過預算的組合。"

    extras_ready = ["menu://today", "menu://item/{name}", "order_helper"]
    return extras_ready, menu_item, order_helper, today_menu


@app.cell
async def _(Client, extras_ready, mcp, mo):
    _ = extras_ready
    async with Client(mcp) as _c:
        _res = await _c.list_resources()
        _tpl = await _c.list_resource_templates()
        _today = await _c.read_resource("menu://today")
        _item = await _c.read_resource("menu://item/紅茶")
        _prompts = await _c.list_prompts()
        _p = await _c.get_prompt("order_helper", {"budget": 100})
    mo.md(
        f"""
    | 動作 | 結果 |
    |---|---|
    | `list_resources()` | {[str(r.uri) for r in _res]} |
    | `list_resource_templates()` | {[r.uri_template for r in _tpl]} |
    | `read_resource("menu://today")` | `{_today[0].text}` |
    | `read_resource("menu://item/紅茶")` | `{_item[0].text}` |
    | `list_prompts()` | {[(p.name, [a.name for a in (p.arguments or [])]) for p in _prompts]} |
    | `get_prompt("order_helper", budget=100)` | `{_p.messages[0].content.text}` |
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 3️⃣ 無狀態協定：起一台真的 HTTP 伺服器來看

    in-memory 看不出協定的差別，所以這裡在 notebook 裡**真的起一台 HTTP 伺服器**
    （`mcp.http_app()` 是標準 ASGI app，用 uvicorn 在背景執行緒跑）。
    我們在它前面塞一個小小的側錄器，把每個進來的 HTTP 請求記下來——
    方法、路徑、MCP 專用的 header、以及 JSON-RPC 的 `method`——等一下用來對照兩種協定。
    """
    )
    return


@app.cell
def _(mcp, mo, socket, threading, time, uvicorn):
    request_log = []   # 每個進來的 HTTP 請求一筆：(標籤, HTTP 方法, mcp-method header, session header, body method)

    class Recorder:
        """ASGI 中介層：只側錄，不改行為。"""

        def __init__(self, app):
            self.app = app
            self.label = ""

        async def __call__(self, scope, receive, send):
            if scope["type"] != "http":
                return await self.app(scope, receive, send)
            _h = {k.decode(): v.decode() for k, v in scope["headers"]}
            _entry = {"階段": self.label, "HTTP": scope["method"], "mcp-method header": _h.get("mcp-method", "—"),
                      "mcp-session-id header": "有" if "mcp-session-id" in _h else "—", "body.method": ""}
            request_log.append(_entry)

            async def _receive():
                _m = await receive()
                if _m.get("body"):
                    import json as _json
                    try:
                        _entry["body.method"] = _json.loads(_m["body"]).get("method", "")
                    except Exception:  # noqa: BLE001  側錄器絕不能干擾正常請求
                        _entry["body.method"] = "(non-JSON)"
                return _m

            return await self.app(scope, _receive, send)

    recorder = Recorder(mcp.http_app())
    PORT = 8765
    MCP_URL = f"http://127.0.0.1:{PORT}/mcp"

    def _port_busy(port):
        with socket.socket() as _s:
            return _s.connect_ex(("127.0.0.1", port)) == 0

    if not _port_busy(PORT):
        _server = uvicorn.Server(uvicorn.Config(recorder, host="127.0.0.1", port=PORT, log_level="warning"))
        threading.Thread(target=_server.run, daemon=True).start()
        for _ in range(50):          # 最多等 5 秒讓它開始聽
            if _port_busy(PORT):
                break
            time.sleep(0.1)
    mo.md(f"HTTP 伺服器在 **`{MCP_URL}`** 聽候（{'已啟動' if _port_busy(PORT) else '⚠️ 沒起來'}）。")
    return MCP_URL, PORT, Recorder, recorder, request_log


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ### 同一台伺服器，兩種協定

    `Client(網址)` 預設會**自動協商**最新協定；加 `mode="legacy"` 則強制用握手時代的協定。
    兩種都連一次、各呼叫一次 `add`，然後看側錄表：

    - **新協定**：第一個請求是 `server/discover`（一發問清楚伺服器會什麼），之後每個請求
      都帶 `mcp-method` header、**沒有任何 session id**。每個請求自己帶齊資訊。
    - **舊協定**：先 `initialize` 握手，伺服器發一個 `mcp-session-id`，之後每個請求都要帶著它
      （還多一條 GET 長連線收通知、結束時 DELETE 銷毀 session）——伺服器得「記得你」，
      請求也就只能回到同一台伺服器。同樣是「呼叫一次 add」，數數看兩邊各花了幾個 HTTP 請求。
    """
    )
    return


@app.cell
async def _(Client, MCP_URL, mo, recorder, request_log):
    request_log.clear()

    recorder.label = "新協定（auto）"
    async with Client(MCP_URL) as _c:
        modern_version = _c.protocol_version
        _r_modern = (await _c.call_tool("add", {"a": 1, "b": 2})).data

    recorder.label = "舊協定（legacy）"
    async with Client(MCP_URL, mode="legacy") as _c:
        legacy_version = _c.protocol_version
        _r_legacy = (await _c.call_tool("add", {"a": 1, "b": 2})).data

    protocol_rows = list(request_log)
    mo.vstack([
        mo.md(f"新協定版本 **`{modern_version}`**（add → {_r_modern}）；舊協定版本 **`{legacy_version}`**（add → {_r_legacy}）。"
              "下表是伺服器側錄到的每一個 HTTP 請求："),
        mo.ui.table(protocol_rows, selection=None),
    ])
    return legacy_version, modern_version, protocol_rows


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ### 最有感的證明：一發裸 POST 就能呼叫工具

    既然新協定每個請求都自帶資訊，那**不用 SDK、不握手**，直接用 `httpx.post` 發一個
    JSON-RPC 請求應該就能呼叫工具。需要帶齊三樣：

    1. header `MCP-Protocol-Version`（宣告用新協定）與 `mcp-method`（讓 gateway 不用拆 body 就能路由）
    2. body 的 `params._meta` 信封：協定版本＋客戶端能力——這就是以前握手時才交換的東西，現在**每個請求都帶**
    3. 正常的 JSON-RPC `method` / `params`

    對照組：用舊協定發同一個請求，伺服器會回 `Missing session ID`——你得先 `initialize`。
    """
    )
    return


@app.cell
def _(MCP_URL, httpx, json, mo, protocol_rows):
    _ = protocol_rows
    _meta = {"io.modelcontextprotocol/protocolVersion": "2026-07-28",
             "io.modelcontextprotocol/clientCapabilities": {}}
    _body = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
             "params": {"name": "add", "arguments": {"a": 40, "b": 2}, "_meta": _meta}}
    _base_headers = {"Accept": "application/json, text/event-stream", "Content-Type": "application/json"}

    raw_modern = httpx.post(MCP_URL, json=_body,
                            headers={**_base_headers, "MCP-Protocol-Version": "2026-07-28",
                                     "mcp-method": "tools/call", "mcp-name": "add"})
    raw_legacy = httpx.post(MCP_URL, json=_body, headers=_base_headers)   # 沒宣告新協定 → 走舊的

    _modern_result = raw_modern.json().get("result", {}).get("structuredContent") if raw_modern.status_code == 200 else raw_modern.text[:200]
    mo.md(
        f"""
    | 方式 | HTTP 狀態 | 回應 |
    |---|---|---|
    | 新協定：一發 POST，無握手 | **{raw_modern.status_code}** | `{json.dumps(_modern_result, ensure_ascii=False)}` |
    | 舊協定：同樣一發 POST | **{raw_legacy.status_code}** | `{raw_legacy.json().get("error", {}).get("message", raw_legacy.text[:120])}` |

    新協定的伺服器**不需要記得任何人**：你可以把它部署成 10 個副本放在負載平衡器後面，
    任何請求落到任何一台都對。這就是 4.0 說的「stateless transport」。
    """
    )
    return raw_legacy, raw_modern


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 4️⃣ 無狀態協定上的有狀態應用：`SessionId`

    問題來了：購物車、多步驟流程這種**需要記住東西**的應用怎麼辦？4.0 的答案是
    「stateless transport, stateful application」——狀態不綁在連線上，而是綁在一把**鑰匙**上：

    - 裝上 `SessionProvider()`，伺服器自動多出兩個工具：`create_session()` 發一把
      猜不到的 uuid 鑰匙、`end_session(session_id)` 銷毀它。
    - 你的工具宣告一個 `session_id: SessionId` 參數，用 `get_session(session_id)` 拿到
      一個可 `get`/`set` 的小儲存格。
    - 鑰匙由呼叫端保管、每次帶來——**換一條連線、換一台副本，帶同一把鑰匙就拿回同樣的狀態**。

    （另一個選項 `session: UserSession` 會自動注入、不進 schema，但需要認證身分——
    它把狀態綁在「登入的使用者」上。本課沒有登入機制，所以用 `SessionId`。）
    """
    )
    return


@app.cell
def _(SessionId, SessionProvider, get_session, mcp):
    mcp.add_provider(SessionProvider())   # 提供 create_session / end_session 兩個工具

    @mcp.tool
    async def add_to_cart(session_id: SessionId, item: str) -> list[str]:
        """把品項加進這個 session 的購物車，回傳目前購物車內容。"""
        _s = await get_session(session_id)
        _items = await _s.get("items", default=[])
        _items.append(item)
        await _s.set("items", _items)
        return _items

    @mcp.tool
    async def show_cart(session_id: SessionId) -> list[str]:
        """查看這個 session 的購物車內容。"""
        _s = await get_session(session_id)
        return await _s.get("items", default=[])

    cart_tools_ready = ["create_session", "end_session", "add_to_cart", "show_cart"]
    return add_to_cart, cart_tools_ready, show_cart


@app.cell
async def _(Client, ToolError, cart_tools_ready, json, mcp, mo):
    _ = cart_tools_ready
    async with Client(mcp) as _c:
        _tools = {t.name: t for t in await _c.list_tools()}
        cart_key = (await _c.call_tool("create_session")).data          # 第一把鑰匙
        await _c.call_tool("add_to_cart", {"session_id": cart_key, "item": "紅茶"})
        _after_two = (await _c.call_tool("add_to_cart", {"session_id": cart_key, "item": "滷肉飯"})).data

    # 全新的一條連線：只要帶同一把鑰匙，購物車還在
    async with Client(mcp) as _c2:
        _new_conn = (await _c2.call_tool("show_cart", {"session_id": cart_key})).data
        try:
            await _c2.call_tool("show_cart", {"session_id": "guess-1234"})
            _guess = "（居然過了？）"
        except ToolError as _e:
            _guess = str(_e)

    mo.md(
        f"""
    `add_to_cart` 的說明書（注意 `session_id` 的描述是 FastMCP 自動寫給 AI 看的）：

    ```json
    {json.dumps(_tools["add_to_cart"].input_schema, ensure_ascii=False, indent=2)}
    ```

    | 步驟 | 結果 |
    |---|---|
    | `create_session()` | 鑰匙 `{cart_key}` |
    | 加「紅茶」、加「滷肉飯」 | `{_after_two}` |
    | **換一條全新連線**，`show_cart(鑰匙)` | `{_new_conn}` ← 狀態還在 |
    | 亂猜一把鑰匙 `guess-1234` | 🛑 `{_guess}` |
    """
    )
    return (cart_key,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 5️⃣ 把伺服器接給真的 AI 客戶端

    把本 notebook 1️⃣ 與 4️⃣ 的程式碼存成 `server.py`，最後加上：

    ```python
    if __name__ == "__main__":
        mcp.run(transport="http", host="0.0.0.0", port=8000)   # 或 transport="stdio" 給本機客戶端
    ```

    然後：

    ```bash
    uv run --with "fastmcp==4.0.0b1" --with "fastmcp-slim==4.0.0b1" python server.py
    # 另一個終端機，接給 Claude Code：
    claude mcp add --transport http tea http://localhost:8000/mcp
    ```

    Claude Desktop 則在設定檔的 `mcpServers` 加一筆 `{"tea": {"url": "http://localhost:8000/mcp"}}`。
    接上之後，對 AI 說「幫我找有茶的飲料」，它會自己呼叫 `search_menu`——
    說明書是你的函式簽名自動生成的，你一行 schema 都沒寫。

    ### 4.0 還改了什麼（知道就好）

    - 多回合互動工具：工具可以回傳 `InputRequiredResult` 向使用者追問，下一個請求再接著做
      （不靠連線記住進度，靠簽章過的 request state）。
    - 背景任務：`@mcp.tool(task=True)` 搭配 `fastmcp-tasks` 擴充，長工作交給客戶端輪詢。
    - 拿掉了 `ctx.sample()`、`ctx.list_roots()` 這類「伺服器反過來呼叫客戶端」的 API——
      它們需要一條活著的雙向連線，跟無狀態互斥。
    - 回應可宣告快取（`FastMCP(..., cache_ttl=300, cache_scope="public")`），
      因為請求自帶一切，gateway 才快取得起來。

    ## 🏆 延伸挑戰

    1. **LEVEL 1**：在 1️⃣ 加一個工具 `place_order(item: str, qty: int = 1) -> dict`，
       重新執行下方的 `list_tools()` 那格，確認說明書自動更新（`qty` 有 default）。
    2. **LEVEL 2**：4️⃣ 的購物車加一個 `checkout(session_id)` 工具：算總價（查 `MENU`）、
       清空購物車（`await _s.set("items", [])`）並回傳收據。
    3. **LEVEL 3**：改 3️⃣ 的裸 POST，改呼叫 `tools/list`（`mcp-method` header 也要改），
       再試著呼叫 `resources/read` 讀 `menu://today`——查 MCP 規格找出 `params` 的格式。

    帶得走：下載本檔後 `uvx marimo edit --sandbox fastmcp4_ext.py` 在自己電腦繼續玩。
    下一課：**Qdrant 向量資料庫**——為壓軸的「RAG 變成 MCP 工具」準備地基。
    """
    )
    return


if __name__ == "__main__":
    app.run()
