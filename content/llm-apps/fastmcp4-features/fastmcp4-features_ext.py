# FastMCP 4 專屬功能：背景任務、快取、路由 header、擴充
# 不需要 GPU——molab 免費 CPU 環境即可全程執行（本課不連任何外部服務，全部在本機跑）。
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "marimo",
#     "fastmcp==4.0.0b1",
#     "fastmcp-slim==4.0.0b1",
#     "fastmcp-tasks==4.0.0b1",
#     "httpx",
#     "uvicorn",
# ]
# ///
import marimo

__generated_with = "0.23.16"
app = marimo.App(width="medium", app_title="FastMCP 4 專屬功能：背景任務、快取、路由 header、擴充")


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    # 🧰 FastMCP 4 專屬功能：背景任務、快取、路由 header、擴充

    第 3 課你看過 4.0 的核心改版：協定變**無狀態**，每個請求自帶一切。這堂補充課把 4.0 建在這個地基上的
    **新功能**一個一個拿出來用——而且每一個都用第 3 課的側錄器**看線路上真的發生了什麼**，
    不是只看 API 表面。

    你會看到：

    1. **背景任務**：同樣一行 `call_tool`，新協定變成「投遞 → 輪詢 → 取結果」，舊協定一發等到底
    2. **回應快取提示**：伺服器說「這份工具清單可以快取 300 秒」，客戶端三次 `list_tools()` 只打一次
    3. **Gateway 路由 header**：參數可以升成 HTTP header，負載平衡器不拆 body 就能分流
    4. **參數自動完成**：`@mcp.completion`，客戶端打字時給候選
    5. **自訂 extension**：在協定上加自己的 capability 與方法——背景任務本身就是這樣做出來的
    6. **資源模板路徑安全**：`../` 在進你的函式之前就被擋掉
    7. **工具搜尋 transform**：幾十個工具變成 `search_tools` + `call_tool` 兩個（FastMCP 招牌、非 4.0 新增）
    8. 知道有就好：其他 4.0 改動一覽

    本 notebook 用 `fastmcp==4.0.0b1` ＋ `fastmcp-tasks==4.0.0b1`，與第 3 課同版。
    從第一格往下全部執行即可（首次安裝套件約 1 分鐘）。
    """
    )
    return


@app.cell
def _():
    import asyncio
    import json
    import socket
    import threading
    import time
    from typing import Annotated, Any

    import httpx
    import marimo as mo
    import uvicorn
    from fastmcp import Client, FastMCP
    from fastmcp.dependencies import Progress
    from fastmcp.server.extensions import MethodBinding, ServerExtension
    from fastmcp.server.transforms.search import BM25SearchTransform
    from fastmcp_tasks import TasksExtension
    from mcp.types import PromptReference, RequestParams
    from pydantic import Field
    return (
        Annotated,
        Any,
        BM25SearchTransform,
        Client,
        FastMCP,
        Field,
        MethodBinding,
        Progress,
        PromptReference,
        RequestParams,
        ServerExtension,
        TasksExtension,
        asyncio,
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
    ## 0️⃣ 工具箱：側錄器與「起一台伺服器」

    第 3 課的兩個小工具先準備好，整堂課都靠它們：

    - **`Recorder`**：塞在 ASGI app 前面的中介層，把每個進來的 HTTP 請求記下來——HTTP 方法、
      `mcp-method`／`mcp-name` header、所有 `mcp-param-*` header、JSON-RPC 的 `method`。只側錄不干擾。
    - **`serve(app, port)`**：用 uvicorn 在背景執行緒起伺服器，重跑前先探 port 避免重複啟動。
      本課每一節各起一台（不同 port），互不影響。

    另外兩個小幫手：`summarize()` 把側錄表壓成一行一請求的清單；`raw_post()` 發「裸」JSON-RPC
    請求——第 3 課學過的三要件（`MCP-Protocol-Version` header、`mcp-method` header、`_meta` 信封）
    都包好了，本課幾處要**不用 SDK** 直接看線路時用它。
    """
    )
    return


@app.cell
def _(httpx, json, socket, threading, time, uvicorn):
    class Recorder:
        """ASGI 中介層：只側錄，不改行為。"""

        def __init__(self, app):
            self.app = app
            self.log = []

        async def __call__(self, scope, receive, send):
            if scope["type"] != "http":
                return await self.app(scope, receive, send)
            _h = {k.decode(): v.decode() for k, v in scope["headers"]}
            _entry = {"HTTP": scope["method"], "mcp-method": _h.get("mcp-method", "—"), "mcp-name": _h.get("mcp-name", "—"),
                      "mcp-param-*": {k: v for k, v in _h.items() if k.startswith("mcp-param-")} or "—", "body.method": ""}
            self.log.append(_entry)

            async def _receive():
                _m = await receive()
                if _m.get("body"):
                    try:
                        _entry["body.method"] = json.loads(_m["body"]).get("method", "")
                    except Exception:  # noqa: BLE001  側錄器絕不能干擾正常請求
                        _entry["body.method"] = "(non-JSON)"
                return _m

            return await self.app(scope, _receive, send)

    def _port_busy(port):
        with socket.socket() as _s:
            return _s.connect_ex(("127.0.0.1", port)) == 0

    def serve(app, port):
        """背景執行緒起 uvicorn；port 已開就不重起。回傳 MCP 端點網址。"""
        if not _port_busy(port):
            _server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning"))
            threading.Thread(target=_server.run, daemon=True).start()
            for _ in range(50):
                if _port_busy(port):
                    break
                time.sleep(0.1)
        return f"http://127.0.0.1:{port}/mcp"

    def summarize(log):
        """側錄表 → 一行一請求。"""
        return [f"{e['HTTP']} {e['mcp-method']}"
                + (f" {e['mcp-name']}" if e["mcp-name"] != "—" else "")
                + (f"  {e['mcp-param-*']}" if e["mcp-param-*"] != "—" else "")
                for e in log]

    _META = {"io.modelcontextprotocol/protocolVersion": "2026-07-28",
             "io.modelcontextprotocol/clientCapabilities": {"extensions": {"io.modelcontextprotocol/tasks": {}}}}

    def raw_post(url, method, params, name=None):
        """不用 SDK 的單發 JSON-RPC：三要件（協定 header、mcp-method header、_meta 信封）都帶齊。"""
        _headers = {"Accept": "application/json, text/event-stream", "Content-Type": "application/json",
                    "MCP-Protocol-Version": "2026-07-28", "mcp-method": method}
        if name:
            _headers["mcp-name"] = name          # tools/call 一定要帶，否則伺服器回 -32020
        return httpx.post(url, json={"jsonrpc": "2.0", "id": 1, "method": method, "params": {**params, "_meta": _META}},
                          headers=_headers, timeout=30).json()

    return Recorder, raw_post, serve, summarize


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 1️⃣ 背景任務：投遞 → 輪詢 → 取結果

    一個要跑幾分鐘的工具，如果把 HTTP 請求一直開著等，會撞 timeout、使用者也不知道進度。
    4.0 用 **MCP tasks 擴充**（`io.modelcontextprotocol/tasks`）解決：伺服器先回一張**任務單**
    （`taskId` ＋ `status: working`），客戶端之後用 `tasks/get` 輪詢，完成時結果就在裡面。

    你要做的只有兩件事：

    - `mcp.add_extension(TasksExtension())`（來自 `fastmcp-tasks` 套件，背後是 Docket 任務佇列）
    - `@mcp.tool(task=True)`——工具**必須是 `async def`**；`task=True` 只是「可以」背景跑，
      要不要真的背景跑由客戶端宣告、伺服器決定

    `Progress` 依賴（`progress: Progress = Progress()`）讓工具回報進度：`set_total`／`set_message`／`increment`。
    下面的 `brew(cups)` 每杯 0.3 秒、每杯更新一次訊息。
    """
    )
    return


@app.cell
def _(FastMCP, Progress, Recorder, TasksExtension, asyncio, mo, serve):
    tasks_mcp = FastMCP("慢工茶行")
    tasks_mcp.add_extension(TasksExtension())

    @tasks_mcp.tool(task=True)
    async def brew(cups: int, progress: Progress = Progress()) -> str:  # noqa: B008  FastMCP 依賴注入的慣用寫法
        """泡 cups 杯茶，每杯 0.3 秒。"""
        await progress.set_total(cups)
        for _i in range(cups):
            await progress.set_message(f"第 {_i + 1} 杯")
            await asyncio.sleep(0.3)
            await progress.increment()
        return f"泡好 {cups} 杯"

    tasks_rec = Recorder(tasks_mcp.http_app())
    TASKS_URL = serve(tasks_rec, 8801)
    mo.md(f"`{tasks_mcp.name}` 在 **`{TASKS_URL}`** 聽候。")
    return TASKS_URL, brew, tasks_mcp, tasks_rec


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ### 同一行 `call_tool`，兩種協定走的路不一樣

    FastMCP 的 `Client` 會自己處理任務單與輪詢——所以程式碼看起來跟呼叫普通工具**一模一樣**。
    差別要看側錄表：

    - **新協定**（預設）：`tools/call brew` 立刻回來，接著是**好幾次** `tasks/get`（次數會飄），
      最後一次帶著結果。伺服器的 capabilities 裡也看得到 `io.modelcontextprotocol/tasks`。
    - **舊協定**（`mode="legacy"`）：tasks 是新協定才協商的能力，同一個工具直接**同步跑到底**，
      側錄表裡沒有任何 `tasks/get`（而且如第 3 課所見，舊協定的請求沒有 `mcp-method` header，全是 `—`）。
    """
    )
    return


@app.cell
async def _(Client, TASKS_URL, brew, mo, summarize, tasks_rec, time):
    _ = brew
    tasks_rec.log.clear()
    _t0 = time.perf_counter()
    async with Client(TASKS_URL) as _c:
        task_caps = list((getattr(_c.server_capabilities, "extensions", None) or {}).keys())
        _modern = (await _c.call_tool("brew", {"cups": 3})).data
    modern_wire = summarize(tasks_rec.log)
    _modern_sec = time.perf_counter() - _t0

    tasks_rec.log.clear()
    _t0 = time.perf_counter()
    async with Client(TASKS_URL, mode="legacy") as _c:
        _legacy = (await _c.call_tool("brew", {"cups": 3})).data
    legacy_wire = summarize(tasks_rec.log)
    _legacy_sec = time.perf_counter() - _t0
    _modern_txt = "<br>".join(f"`{w}`" for w in modern_wire)
    _legacy_txt = "<br>".join(f"`{w}`" for w in legacy_wire)
    _n_get = sum("tasks/get" in w for w in modern_wire)

    mo.md(
        f"""
    伺服器宣告的 extensions：`{task_caps}`

    | | 新協定（預設） | 舊協定 `mode="legacy"` |
    |---|---|---|
    | `call_tool("brew", cups=3)` 回傳 | `{_modern}`（{_modern_sec:.1f}s） | `{_legacy}`（{_legacy_sec:.1f}s） |
    | 側錄到的請求 | {_modern_txt} | {_legacy_txt} |
    | `tasks/get` 次數 | **{_n_get}** | 0 |
    """
    )
    return legacy_wire, modern_wire, task_caps


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ### 自己輪詢一次：Progress 的訊息去了哪裡

    SDK 把輪詢藏起來了，這裡用裸 POST 自己走一遍看清楚：

    1. `tools/call` 的 `params` 多一個 `"task": {"ttl": 60000}`——這就是客戶端「我要背景跑」的宣告
    2. 回應**不是結果**，是任務單：`taskId`、`status: "working"`、`pollIntervalMs`（伺服器建議多久問一次）
    3. 之後每 0.35 秒 `tasks/get` 一次：`statusMessage` 就是工具裡 `progress.set_message()` 寫的「第 N 杯」，
       `status` 變成 `completed` 時 `result` 就在同一個回應裡

    正式環境的選項：`@mcp.tool(task=TaskConfig(mode="required"))` 強制背景跑（沒宣告的客戶端會收到錯誤）、
    `mode="forbidden"` 永不背景跑；`TasksExtension()` 預設是單 process 記憶體佇列，
    多副本／要撐過重啟就換 Redis／Valkey backend。
    """
    )
    return


@app.cell
def _(TASKS_URL, brew, mo, raw_post, time):
    _ = brew
    _ticket = raw_post(TASKS_URL, "tools/call", {"name": "brew", "arguments": {"cups": 3}, "task": {"ttl": 60000}}, name="brew")["result"]
    task_rows = [{"步驟": "tools/call（帶 task）", "status": _ticket["status"], "statusMessage": "—",
                  "其他": f"taskId={_ticket['taskId'][:12]}… pollIntervalMs={_ticket.get('pollIntervalMs')}"}]
    for _i in range(12):
        time.sleep(0.35)
        _g = raw_post(TASKS_URL, "tasks/get", {"taskId": _ticket["taskId"]})["result"]
        task_rows.append({"步驟": f"tasks/get #{_i + 1}", "status": _g["status"], "statusMessage": _g.get("statusMessage", "—"),
                          "其他": f"result={_g.get('result', {}).get('structuredContent')}" if _g["status"] == "completed" else ""})
        if _g["status"] in ("completed", "failed"):
            break
    mo.ui.table(task_rows, selection=None)
    return (task_rows,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 2️⃣ 回應快取提示：伺服器說「這份可以留 300 秒」

    因為新協定的請求自帶一切、不綁連線，**回應才快取得起來**。4.0 讓伺服器在 `tools/list`、
    `resources/list`、`prompts/list` 的結果附上 `ttlMs` 與 `cacheScope`；客戶端開 `cache=True`
    就會尊重這個提示——在 TTL 內重複呼叫**不再打伺服器**。

    這一節的伺服器用 `FastMCP("天氣", cache_ttl=300, cache_scope="public")`；同時先埋一個
    3️⃣ 要用的參數標註（`x-mcp-header`），下一節再解釋。
    """
    )
    return


@app.cell
def _(Annotated, FastMCP, Field, Recorder, mo, serve):
    cache_mcp = FastMCP("天氣", cache_ttl=300, cache_scope="public")

    @cache_mcp.tool
    def forecast(city: Annotated[str, Field(json_schema_extra={"x-mcp-header": "City"})], days: int = 1) -> str:
        """查某城市未來幾天的天氣。"""
        return f"{city}: 晴 ×{days}"

    cache_rec = Recorder(cache_mcp.http_app())
    CACHE_URL = serve(cache_rec, 8802)
    mo.md(f"`{cache_mcp.name}` 在 **`{CACHE_URL}`** 聽候（`cache_ttl=300`、`cache_scope=\"public\"`）。")
    return CACHE_URL, cache_mcp, cache_rec, forecast


@app.cell
async def _(CACHE_URL, Client, cache_rec, forecast, mo, summarize):
    _ = forecast
    cache_rec.log.clear()
    async with Client(CACHE_URL, cache=True) as _c:
        for _ in range(3):
            cached_tools = await _c.list_tools()
    cached_wire = summarize(cache_rec.log)

    cache_rec.log.clear()
    async with Client(CACHE_URL) as _c:          # 沒開快取
        for _ in range(3):
            await _c.list_tools()
    uncached_wire = summarize(cache_rec.log)
    _cached_txt = "、".join(f"`{w}`" for w in cached_wire)
    _uncached_txt = "、".join(f"`{w}`" for w in uncached_wire)
    _n_cached = sum("tools/list" in w for w in cached_wire)
    _n_uncached = sum("tools/list" in w for w in uncached_wire)

    mo.md(
        f"""
    | 客戶端 | 三次 `list_tools()`，伺服器收到的請求 | `tools/list` 次數 |
    |---|---|---|
    | `Client(url, cache=True)` | {_cached_txt} | **{_n_cached}** |
    | `Client(url)` | {_uncached_txt} | **{_n_uncached}** |

    工具清單本身一樣（{len(cached_tools)} 個工具）。把 `cache_ttl` 改小、中間 `sleep` 一下再列，就會再打一次——這是 LEVEL 1。
    """
    )
    return cached_tools, cached_wire, uncached_wire


@app.cell
def _(CACHE_URL, forecast, json, mo, raw_post):
    _ = forecast
    _raw = raw_post(CACHE_URL, "tools/list", {})["result"]
    _hints_txt = json.dumps({k: v for k, v in _raw.items() if k != "tools"}, ensure_ascii=False, indent=2)
    mo.md(
        f"""
    裸 POST 一次 `tools/list`，看伺服器回應裡的快取提示欄位（工具清單以外的 key）：

    ```json
    {_hints_txt}
    ```

    `ttlMs` 與 `cacheScope` 就是提示；`"public"` 表示這份回應不含個人資料，連 gateway／一整群客戶端都可以共用同一份快取
    （改 `cache_scope="private"` 就只能各自留）。
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 3️⃣ Gateway 路由 header：不拆 body 就能分流

    第 3 課你看過新協定每個請求都帶 `Mcp-Method`（方法）與 `Mcp-Name`（工具名）兩個 header，
    目的是讓負載平衡器**不用解析 JSON-RPC body** 就能路由。4.0 再進一步：**參數也能升成 header**——
    在參數的 schema 加 `x-mcp-header` 標註，客戶端呼叫時會把那個參數的值鏡射成 `Mcp-Param-<名字>` header。
    例如依「租戶」或「城市」把請求釘到專屬後端。

    兩個實測細節：

    - 客戶端要**先 `list_tools()` 看過 schema** 才知道哪些參數要升成 header；沒看過就直接 `call_tool`，
      伺服器會拒絕：`Mcp-Param-City header is missing but the request body's 'city' argument is present`
      （它會嚴格核對 header 與 body 一致——header 只是路由提示，body 才是真相）。
    - 值若不是 ASCII（例如 `台北`）會被編成 `=?base64?…?=`（RFC 2047 式），gateway 要認得這個格式。
    - 只允許 `string`／`integer`／`boolean` 參數；舊協定完全沒有這些 header。
    """
    )
    return


@app.cell
async def _(CACHE_URL, Client, cache_rec, cached_tools, mo, summarize):
    cache_rec.log.clear()
    async with Client(CACHE_URL) as _c:
        await _c.list_tools()                                   # 先看過 schema，客戶端才知道 city 要升成 header
        _r1 = (await _c.call_tool("forecast", {"city": "taipei", "days": 2})).data
        _r2 = (await _c.call_tool("forecast", {"city": "台北", "days": 1})).data
    header_wire = summarize(cache_rec.log)

    cache_rec.log.clear()
    async with Client(CACHE_URL, mode="legacy") as _c:
        await _c.list_tools()
        await _c.call_tool("forecast", {"city": "taipei"})
    legacy_header_wire = summarize(cache_rec.log)
    _hw_txt = "<br>".join(f"`{w}`" for w in header_wire)
    _lhw_txt = "<br>".join(f"`{w}`" for w in legacy_header_wire)
    _city_schema = cached_tools[0].input_schema["properties"]["city"]

    mo.md(
        f"""
    `forecast` 的 schema 裡 `city` 長這樣：`{_city_schema}`

    | 協定 | 側錄到的請求 |
    |---|---|
    | 新協定 | {_hw_txt} |
    | 舊協定 | {_lhw_txt} |

    回傳值照常：`{_r1}`、`{_r2}`。注意第二發的 `mcp-param-city` 是 base64 包起來的「台北」。
    """
    )
    return header_wire, legacy_header_wire


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 4️⃣ 參數自動完成：`@mcp.completion`

    MCP 有 `completion/complete` 這個方法：客戶端在使用者填 prompt 參數或 resource template 參數時，
    可以問伺服器「有哪些候選」。4.0 讓 FastMCP 伺服器用**一個 handler** 回答全部的完成請求：
    收到 `ref`（哪個 prompt／template）、`argument`（哪個參數、目前打了什麼）、`context`（已經填好的其他參數），
    回傳候選清單；回 `None` 表示沒意見。

    註冊了 handler，伺服器才會宣告 completions capability；沒註冊的伺服器客戶端根本不會問。
    下面對 `write_poem(theme, style)` 的 `theme` 依序輸入 `""`、`"貓"`、`"颱"`，看候選怎麼縮。
    """
    )
    return


@app.cell
async def _(Client, FastMCP, PromptReference, mo):
    poem_mcp = FastMCP("詩社")

    @poem_mcp.prompt
    def write_poem(theme: str, style: str = "俳句") -> str:
        """寫一首詩。"""
        return f"用{style}寫一首關於{theme}的詩"

    @poem_mcp.completion
    def complete(ref, argument, context):
        if isinstance(ref, PromptReference) and ref.name == "write_poem":
            _opts = {"theme": ["貓", "貓咪咖啡廳", "茶", "颱風"], "style": ["俳句", "五言絕句", "七言律詩"]}
            return [o for o in _opts.get(argument.name, []) if o.startswith(argument.value)]
        return None

    _rows = []
    async with Client(poem_mcp) as _c:
        for _partial in ("", "貓", "颱", "狗"):
            _r = await _c.complete(ref=PromptReference(type="ref/prompt", name="write_poem"),
                                   argument={"name": "theme", "value": _partial})
            _rows.append({"目前輸入": repr(_partial), "候選": _r.values})
    mo.ui.table(_rows, selection=None)
    return complete, poem_mcp, write_poem


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 5️⃣ 自訂 extension：在協定上加自己的東西

    背景任務不是寫死在 FastMCP 核心裡的，它是用 4.0 的 **extension 介面**做出來的一個外掛。
    同一個介面你也能用：繼承 `ServerExtension`，給一個反向 DNS 形式的 `identifier`（`vendor/name`），
    然後挑你需要的覆寫：

    - `settings()`：出現在 `capabilities.extensions[identifier]`，客戶端連上就看得到
    - `methods()`：加**自訂的 JSON-RPC 方法**（只能加新的，不能蓋掉 `tools/call` 這類核心方法）
    - `intercept_tool_call()`：每一次 `tools/call` 進工具本體前的最後一道關卡，可以放行、改寫、或短路
    - `lifespan()`：擁有連線池／背景 worker 這類有生命週期的資源

    下面做一個最小的「呼叫計數器」：數 `tools/call` 次數，並開一個 `callCounter/get` 方法讓人查。
    """
    )
    return


@app.cell
def _(Any, FastMCP, MethodBinding, Recorder, RequestParams, ServerExtension, mo, serve):
    class CallCounter(ServerExtension):
        identifier = "tw.agentclass/call-counter"

        def __init__(self):
            self.count = 0

        def settings(self) -> dict[str, Any]:
            return {"unit": "calls"}

        def methods(self):
            class _GetParams(RequestParams):
                pass
            return [MethodBinding(method="callCounter/get", params_type=_GetParams, handler=self.get_count)]

        async def get_count(self, ctx, params):
            return {"count": self.count}

        async def intercept_tool_call(self, params, context, call_next):
            self.count += 1
            return await call_next()

    counter = CallCounter()
    ext_mcp = FastMCP("計數器")
    ext_mcp.add_extension(counter)

    @ext_mcp.tool
    def ping() -> str:
        """回 pong。"""
        return "pong"

    ext_rec = Recorder(ext_mcp.http_app())
    EXT_URL = serve(ext_rec, 8803)
    mo.md(f"`{ext_mcp.name}` 在 **`{EXT_URL}`** 聽候，extension `{counter.identifier}` 已掛上。")
    return CallCounter, EXT_URL, counter, ext_mcp, ext_rec, ping


@app.cell
async def _(Client, EXT_URL, counter, json, mo, ping, raw_post):
    _ = ping
    async with Client(EXT_URL) as _c:
        ext_caps = dict(getattr(_c.server_capabilities, "extensions", None) or {})
        for _ in range(3):
            await _c.call_tool("ping")
    _via_raw = raw_post(EXT_URL, "callCounter/get", {})
    _caps_txt = json.dumps(ext_caps, ensure_ascii=False, indent=2, default=str)
    _raw_txt = json.dumps(_via_raw.get("result") or _via_raw.get("error"), ensure_ascii=False, default=str)
    mo.md(
        f"""
    客戶端連上時看到的 `capabilities.extensions`：

    ```json
    {_caps_txt}
    ```

    （`io.modelcontextprotocol/ui` 是 FastMCP 內建的；我們的 `tw.agentclass/call-counter` 帶著 `settings()` 的內容。
    1️⃣ 那台還多了 `io.modelcontextprotocol/tasks`——tasks 就是這樣宣告自己的。）

    呼叫 3 次 `ping` 後，用裸 POST 打自訂方法 `callCounter/get`（`mcp-method` header 也要填它）：

    ```json
    {_raw_txt}
    ```

    伺服器端的 `counter.count` = **{counter.count}**。SDK 這邊沒有現成的 `client.call_counter()`——
    自訂方法的客戶端半邊通常也要自己寫一個 `ClientExtension`（LEVEL 3 會碰到）。
    """
    )
    return (ext_caps,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 6️⃣ 資源模板路徑安全：`../` 進不了你的函式

    第 3 課的 `menu://item/{name}` 這種 resource template，參數常常會被拿去拼檔案路徑。
    4.0 **預設**在進 handler 之前就篩掉路徑穿越（`../`、編碼過的 `%2e%2e`）、絕對路徑（開頭 `/`）與 null byte。
    被擋的請求回 `Resource not found`——對外看起來就像這個資源不存在，handler **完全沒被呼叫**。

    下面用 `docs://{path*}`（`*` 是萬用字元，允許 `a/b` 這種多段路徑）測六個輸入，並用一個 list 記錄
    handler 實際收到了什麼。合法的值要放行（例如 git ref `HEAD~3..HEAD`）時，用
    `security=ResourceSecurity(exempt_params={"ref"})` 逐參數豁免，或 `security=None` 整個關掉。
    """
    )
    return


@app.cell
async def _(Client, FastMCP, mo):
    docs_mcp = FastMCP("文件庫")
    handler_saw = []

    @docs_mcp.resource("docs://{path*}")
    def read_doc(path: str) -> str:
        """讀一份文件（示範用，回傳假內容）。"""
        handler_saw.append(path)
        return f"content of {path}"

    _rows = []
    async with Client(docs_mcp) as _c:
        for _p in ("guide", "a/b", "../etc/passwd", "%2e%2e/x", "/etc/passwd", "x%00y"):
            try:
                _r = await _c.read_resource(f"docs://{_p}")
                _rows.append({"請求的 path": _p, "結果": f"✅ {_r[0].text}"})
            except Exception as _e:  # noqa: BLE001  被擋的請求就是要看錯誤長什麼樣
                _rows.append({"請求的 path": _p, "結果": f"🛑 {type(_e).__name__}: {str(_e)[:60]}"})
    mo.vstack([
        mo.ui.table(_rows, selection=None),
        mo.md(f"handler 實際收到的 path：`{handler_saw}`——被擋的四個，函式根本沒執行。"),
    ])
    return docs_mcp, handler_saw, read_doc


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 7️⃣ 工具搜尋 transform：幾十個工具變兩個

    這不是 4.0 新增（transforms 從 3.0 就有），但跟 4.0 的「大伺服器」場景常一起出現：
    當一台伺服器有 50 個工具，全部塞進模型的 context 既貴又讓它挑錯。
    `BM25SearchTransform` 讓 `list_tools()` 只剩 **`search_tools`** 與 **`call_tool`** 兩個合成工具——
    模型先用自然語言搜（BM25 依相關度排序），拿到完整 schema 後再呼叫。
    原本的工具**只是從清單裡隱形**，直接指名呼叫仍然可以。
    """
    )
    return


@app.cell
async def _(BM25SearchTransform, Client, FastMCP, json, mo):
    big_mcp = FastMCP("大目錄", transforms=[BM25SearchTransform()])

    def _make(name, doc):
        def _tool(x: str) -> str:
            return f"{name}({x})"
        _tool.__name__ = name
        _tool.__doc__ = doc
        return _tool

    for _name, _doc in [("send_email", "寄電子郵件給某人 email"), ("delete_record", "從資料庫刪除一筆紀錄 database delete"),
                        ("search_database", "在資料庫搜尋 database search"), ("resize_image", "縮放圖片 image"),
                        ("translate_text", "翻譯文字 translate")]:
        big_mcp.tool(_make(_name, _doc))

    async with Client(big_mcp) as _c:
        visible_tools = [t.name for t in await _c.list_tools()]
        _found = await _c.call_tool("search_tools", {"query": "delete something from the database"})
        _hits = _found.data if _found.data is not None else json.loads(_found.content[0].text)
        _direct = (await _c.call_tool("delete_record", {"x": "row-1"})).data
        _proxied = await _c.call_tool("call_tool", {"name": "resize_image", "arguments": {"x": "cat.png"}})
    _rank_txt = " → ".join(f"`{h['name']}`" for h in _hits)
    _proxied_txt = _proxied.data if _proxied.data is not None else _proxied.content[0].text
    mo.md(
        f"""
    | 動作 | 結果 |
    |---|---|
    | `list_tools()` | `{visible_tools}`（註冊了 5 個，只露出 2 個） |
    | `search_tools("delete something from the database")` | 排序：{_rank_txt} |
    | 直接呼叫隱藏的 `delete_record` | `{_direct}` |
    | 透過 `call_tool` 代呼叫 `resize_image` | `{_proxied_txt}` |
    """
    )
    return big_mcp, visible_tools


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 8️⃣ 知道有就好：其他 4.0 改動

    | 功能 | 一句話 | 哪裡看 |
    |---|---|---|
    | 多回合互動工具 | 工具回傳 `InputRequiredResult` 向使用者追問，下一個請求接著做；`ctx.elicit()` 只剩舊協定能用 | 補充課「狀態」 |
    | 移除 `ctx.sample()`／`ctx.list_roots()` | 它們需要活的雙向連線，與無狀態互斥；改用回傳-再進入的寫法 | 補充課「狀態」 |
    | 協定協商 | `Client(url)` 自動試新協定再退回；`client.protocol_version` 告訴你談到哪一版 | 第 3 課 |
    | Identity assertion | 企業 IdP 簽一張身分斷言，agent 代員工行事不用跳瀏覽器：`OAuthProxy(identity_assertion=IdentityAssertion(trusted_issuers=[...]))` | 補充課「認證」8️⃣ |
    | `InsufficientScopeError` | 授權不足時明確列出**缺哪些 scope**，客戶端可以精準補授權 | 補充課「認證」 |
    | Client credentials | 機器對機器的 OAuth：`ClientCredentialsOAuthProvider(client_id, client_secret)`，無瀏覽器 | 補充課「認證」8️⃣ |
    | 版本化工具 | 同名工具多版本並存，客戶端指定要哪版 | docs: Versioning |
    | OpenAPI → MCP | `FastMCP.from_openapi(spec, client)` 把既有 REST API 整個變成 MCP 伺服器 | docs: OpenAPI Integration |
    | Middleware | rate limiting、timing、logging、error handling 等現成中介層（3.x 已有） | docs: Middleware |
    | Response cache store | `KeyValueResponseCacheStore` 讓一群客戶端／proxy 共用 Redis 快取 | 2️⃣ 的延伸 |

    ## 🏆 延伸挑戰

    1. **LEVEL 1**：把 2️⃣ 的 `cache_ttl` 改成 `1`，開快取連列兩次、`await asyncio.sleep(1.2)` 後再列第三次——
       側錄表會多出一個 `tools/list`（TTL 到期）。
    2. **LEVEL 2**：給 3️⃣ 的 `forecast` 再加一個 `tenant` 參數也標 `x-mcp-header`，呼叫後側錄表要同時出現
       `mcp-param-tenant` 與 `mcp-param-city`。記得先 `list_tools()`，不然會看到那個「header is missing」的錯。
    3. **LEVEL 3**：寫一個 extension 在 `intercept_tool_call` **短路**：沒宣告這個 extension 的客戶端照常拿到結果，
       有宣告的（`Client(url, extensions=[advertise(identifier, {...})])`）拿到被加工過的結果。
       提示：`context.client_extension_settings(self.identifier)` 回 `None` 就代表對方沒宣告。

    先自己試，卡住再展開下面的提示與參考解答。
    帶得走：下載本檔後 `uvx marimo edit --sandbox fastmcp4-features_ext.py` 在自己電腦繼續玩。
    下一課：**常見 MCP 服務**——接上別人寫好的伺服器，再把它們合成一台。
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.accordion(
        {
            "💡 LEVEL 1 參考解答": mo.md(
                r"""
    新起一台 `cache_ttl=1` 的伺服器（別改 2️⃣ 那台，port 換一個）：

    ```python
    short_mcp = FastMCP("短快取", cache_ttl=1, cache_scope="public")

    @short_mcp.tool
    def ping() -> str:
        return "pong"

    short_rec = Recorder(short_mcp.http_app())
    SHORT_URL = serve(short_rec, 8811)

    async with Client(SHORT_URL, cache=True) as _c:
        await _c.list_tools()
        await _c.list_tools()          # 1 秒內：吃快取
        await asyncio.sleep(1.2)
        await _c.list_tools()          # TTL 過了：再打一次
    summarize(short_rec.log)
    ```

    你應該看到 `['POST server/discover', 'POST tools/list', 'POST tools/list']`——兩個 `tools/list`，
    中間那次被快取吃掉了（實測 fastmcp==4.0.0b1）。
    """
            ),
            "💡 LEVEL 2 參考解答": mo.md(
                r"""
    ```python
    tenant_mcp = FastMCP("租戶天氣")

    @tenant_mcp.tool
    def forecast2(
        tenant: Annotated[str, Field(json_schema_extra={"x-mcp-header": "Tenant"})],
        city: Annotated[str, Field(json_schema_extra={"x-mcp-header": "City"})],
        days: int = 1,
    ) -> str:
        return f"{tenant}/{city}: 晴 ×{days}"

    tenant_rec = Recorder(tenant_mcp.http_app())
    TENANT_URL = serve(tenant_rec, 8812)

    async with Client(TENANT_URL) as _c:
        await _c.list_tools()        # ← 少了這行會被拒：Mcp-Param-City header is missing but ... 'city' argument is present
        r = await _c.call_tool("forecast2", {"tenant": "acme", "city": "taipei", "days": 2})
    r.data, summarize(tenant_rec.log)
    ```

    預期：`'acme/taipei: 晴 ×2'`，側錄表最後一筆是
    `POST tools/call forecast2  {'mcp-param-city': 'taipei', 'mcp-param-tenant': 'acme'}`。
    把 `list_tools()` 那行拿掉重跑，就會拿到 `MCPError: Mcp-Param-City header is missing ...`——
    客戶端沒看過 schema 就不知道要升 header，而伺服器會嚴格核對。
    """
            ),
            "💡 LEVEL 3 提示": mo.md(
                r"""
    方向：`intercept_tool_call` 先 `await call_next()` 拿到原本的結果，再依 `context.client_extension_settings(self.identifier)`
    決定原樣放行或改寫。改寫時要回傳 **FastMCP 的 `ToolResult`**（`from fastmcp.tools import ToolResult`）並給
    `structured_content`——因為工具有輸出 schema，只給 `content` 不給結構化內容，客戶端會報
    `Tool hello has an output schema but did not return structured content`。

    ```python
    from fastmcp.tools import ToolResult
    from mcp.client import advertise

    class Stamp(ServerExtension):
        identifier = "tw.agentclass/stamp"

        async def intercept_tool_call(self, params, context, call_next):
            settings = context.client_extension_settings(self.identifier)
            result = await call_next()
            if settings is None:                      # 對方沒宣告：原樣放行
                return result
            text = result.content[0].text if result.content else ""
            return ToolResult(structured_content={"result": f"[{settings.get('who', '?')} 專屬] {text}"})

    stamp_mcp = FastMCP("蓋章")
    stamp_mcp.add_extension(Stamp())

    @stamp_mcp.tool
    def hello() -> str:
        return "hi"

    STAMP_URL = serve(stamp_mcp.http_app(), 8813)
    ```

    怎麼驗證自己做對了——三種客戶端各呼叫一次 `hello`：

    - `Client(STAMP_URL)` → `'hi'`（沒宣告，原樣）
    - `Client(STAMP_URL, extensions=[advertise("tw.agentclass/stamp", {"who": "alice"})])` → `'[alice 專屬] hi'`
    - `Client(STAMP_URL, mode="legacy", extensions=[advertise(...)])` → `'hi'`：extension 宣告是新協定的東西，舊協定上是惰性的

    陷阱：`advertise()` 只是「說我懂」，沒有任何行為；真的要解析自訂結果形狀或收自訂通知，要寫完整的 `ClientExtension`。
    """
            ),
        }
    )
    return


if __name__ == "__main__":
    app.run()
