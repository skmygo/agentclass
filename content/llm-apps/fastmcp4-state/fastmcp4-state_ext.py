# FastMCP 4 狀態：無狀態協定上的三種記憶
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
app = marimo.App(width="medium", app_title="FastMCP 4 狀態：無狀態協定上的三種記憶")


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    # 🧠 FastMCP 4 狀態：無狀態協定上的三種記憶

    第 3 課你看過：4.0 的協定是**無狀態**的——每個請求自帶一切、落到哪台副本都對。
    然後你用 `SessionId` 做了一個會記得東西的購物車。這堂補充課把「無狀態傳輸上怎麼有狀態」
    講完整，並回答一個所有人都會問的問題：

    > **狀態在客戶端與伺服器之間傳來傳去，它是加密的嗎？客戶端能不能偷看、能不能改？**

    答案不是一句話——因為 FastMCP 4 有**三種**記憶，各自活在不同的地方：

    | 記憶 | 活在哪 | 活多久 | 跨副本要什麼 |
    |---|---|---|---|
    | **請求內狀態** `ctx.set_state` | 伺服器記憶體 | 一個請求 | 不需要（不跨請求） |
    | **Session 狀態** `SessionId`／`UserSession` | 伺服器端的 store | 到 `end_session` 或 store 的 TTL | 副本共用同一個 store |
    | **請求狀態** `request_state`（多回合工具） | **客戶端手上**——伺服器發給它、它下一回合帶回來 | 預設 10 分鐘 | 副本共用同一把**金鑰** |

    前兩種根本不會離開伺服器，客戶端拿到的只是一把鑰匙。第三種會真的經過客戶端——
    這堂課最精彩的部分，就是把它從線路上**截下來拆開看**，然後試著竄改它。

    內容：

    1. 請求內狀態：`ctx.set_state`，活一個請求
    2. Session 狀態跨副本：兩台伺服器共用一個 store
    3. 多回合工具：工具「回傳一個問題」，客戶端答完再來一次
    4. 線路實況：把 `requestState` 截下來——它是密文
    5. 五個攻擊實驗：竄改、換伺服器、換參數、換伺服器名、等它過期
    6. 多副本共用金鑰與輪替
    7. 該用哪一種記憶

    從第一格往下全部執行即可（首次安裝套件約 1 分鐘）。本課用 `fastmcp==4.0.0b1`，與第 3 課相同。
    """
    )
    return


@app.cell
def _():
    import base64
    import json
    import secrets
    import socket
    import threading
    import time

    import httpx
    import marimo as mo
    import uvicorn
    from fastmcp import Client, Context, FastMCP
    from fastmcp.client.elicitation import ElicitResult
    from fastmcp.exceptions import ToolError
    from fastmcp.server.sessions import SessionId, SessionProvider, get_session
    from key_value.aio.stores.memory import MemoryStore
    from mcp.server.request_state import RequestStateSecurity
    from mcp.types import ElicitRequest, ElicitRequestFormParams, InputRequiredResult
    return (
        Client,
        Context,
        ElicitRequest,
        ElicitRequestFormParams,
        ElicitResult,
        FastMCP,
        InputRequiredResult,
        MemoryStore,
        RequestStateSecurity,
        SessionId,
        SessionProvider,
        ToolError,
        base64,
        get_session,
        httpx,
        json,
        mo,
        secrets,
        socket,
        threading,
        time,
        uvicorn,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 1️⃣ 請求內狀態：`ctx.set_state`，活一個請求

    最短命的記憶。`Context` 上的 `set_state`／`get_state` 是給**同一個請求裡**的中介層與工具
    互相傳值用的（例如 middleware 查完權限塞一個旗標、工具再讀）。它不跨請求：
    下面的 `tick` 連叫三次，每次都從 0 開始——**這不是 bug，是設計**。
    要跨請求，得用後面兩種。
    """
    )
    return


@app.cell
async def _(Client, Context, FastMCP, mo):
    ctx_demo = FastMCP("請求內狀態")

    @ctx_demo.tool
    async def tick(ctx: Context) -> dict:
        """把 n 加一，回傳加之前與加之後的值。"""
        _n = (await ctx.get_state("n")) or 0
        await ctx.set_state("n", _n + 1)
        return {"n_before": _n, "n_after": await ctx.get_state("n")}

    async with Client(ctx_demo) as _c:
        tick_results = [(await _c.call_tool("tick")).data for _ in range(3)]
    mo.md(f"`tick` 連叫三次：`{tick_results}` ← 每次都從 0 開始，狀態只活在一個請求裡。")
    return ctx_demo, tick, tick_results


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 2️⃣ Session 狀態跨副本：兩台伺服器共用一個 store

    第 3 課的購物車用 `SessionId`：狀態存在**伺服器端**、客戶端只拿一把鑰匙。
    那「10 個副本放在負載平衡器後面」怎麼辦？鑰匙帶到別台，那台的記憶體裡沒有這個 session。

    答案是 **store**：`FastMCP(..., session_state_store=store)`。預設是 process 內的記憶體，
    換成所有副本都連得到的 store（正式環境是 Redis／Valkey，FastMCP 用的是 `key-value` 這個
    抽象層），狀態就跟著 store 走、不跟著副本走。

    下面用同一個 `MemoryStore` 物件餵給兩台 FastMCP 來**模擬**兩個副本：
    在副本 A 建 session、加紅茶，到副本 B 用同一把鑰匙看購物車。
    第三台副本 C 故意不共用 store，拿同一把鑰匙會被拒。
    """
    )
    return


@app.cell
def _(FastMCP, MemoryStore, SessionId, SessionProvider, get_session):
    shared_store = MemoryStore()   # 正式環境：RedisStore(url="redis://...")

    def build_replica(name: str, store=None) -> FastMCP:
        """蓋一台帶購物車工具的副本；store 給了就共用。"""
        _kw = {"session_state_store": store} if store is not None else {}
        _m = FastMCP(name, **_kw)
        _m.add_provider(SessionProvider())   # 提供 create_session / end_session

        @_m.tool
        async def add_to_cart(session_id: SessionId, item: str) -> list[str]:
            """把品項加進這個 session 的購物車。"""
            _s = await get_session(session_id)
            _items = await _s.get("items", default=[])
            _items.append(item)
            await _s.set("items", _items)
            return _items

        @_m.tool
        async def show_cart(session_id: SessionId) -> list[str]:
            """查看這個 session 的購物車。"""
            return await (await get_session(session_id)).get("items", default=[])

        return _m

    replica_a = build_replica("副本 A", shared_store)
    replica_b = build_replica("副本 B", shared_store)
    replica_c = build_replica("副本 C")            # 沒共用 store
    return build_replica, replica_a, replica_b, replica_c, shared_store


@app.cell
async def _(Client, ToolError, mo, replica_a, replica_b, replica_c):
    async with Client(replica_a) as _ca:
        cart_key = (await _ca.call_tool("create_session")).data
        await _ca.call_tool("add_to_cart", {"session_id": cart_key, "item": "紅茶"})
        await _ca.call_tool("add_to_cart", {"session_id": cart_key, "item": "滷肉飯"})
    async with Client(replica_b) as _cb:
        _seen_by_b = (await _cb.call_tool("show_cart", {"session_id": cart_key})).data
    async with Client(replica_c) as _cc:
        try:
            _seen_by_c = (await _cc.call_tool("show_cart", {"session_id": cart_key})).data
        except ToolError as _e:
            _seen_by_c = f"🛑 {str(_e).splitlines()[0]}"
    mo.md(
        f"""
    | 步驟 | 結果 |
    |---|---|
    | 副本 A：`create_session()`、加紅茶、加滷肉飯 | 鑰匙 `{cart_key}` |
    | **副本 B**（共用 store）：`show_cart(鑰匙)` | `{_seen_by_b}` ← A 存的，B 讀得到 |
    | **副本 C**（不共用）：`show_cart(鑰匙)` | {_seen_by_c} |

    鑰匙本身沒有任何資料，只是 store 裡的一個 key。所以這一種記憶**不存在「傳來傳去要不要加密」的問題**：
    資料從頭到尾沒離開伺服器端。

    ⚠️ 但要知道它的安全模型：**沒有認證時，session id 就是一張不記名票**——誰拿到鑰匙誰就能讀寫。
    `create_session` 發的 uuid 猜不到，但「猜不到」不等於「隔離」。多租戶的隔離要靠認證：有了登入身分，
    FastMCP 會把 session 放在「使用者 → session id」兩層命名空間下，別人拿到你的鑰匙也打不開（補充課 A 有教）。
    """
    )
    return (cart_key,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 3️⃣ 多回合工具：工具「回傳一個問題」，客戶端答完再來一次

    第三種記憶來自 4.0 的新招。以前工具想問使用者問題（「幾位？」「確定要刪嗎？」）要靠
    `ctx.elicit()`——那需要一條活著的雙向連線，無狀態協定沒有。4.0 的做法是 **guard 模式**：

    1. 工具被呼叫，發現還沒拿到答案 → **回傳** 一個 `InputRequiredResult`（「我需要這些輸入」），請求就此結束。
    2. 客戶端問完使用者，**重新呼叫同一個工具**，把答案放在 `inputResponses` 帶上。
    3. 工具從頭再跑一次，這次 `ctx.input_responses` 有值了，繼續做或再問下一題。

    每一回合都是獨立完整的請求。那「第一回合問到的人數」怎麼帶到第三回合？工具可以把任何小字串
    放進 `InputRequiredResult.request_state`，客戶端下一回合會原封不動帶回來，讀 `ctx.request_state` 就有。
    **這就是第三種記憶：它真的經過客戶端。**

    下面的 `book_table` 分兩回合問人數與日期；人數用 `request_state` 帶到最後一回合。
    """
    )
    return


@app.cell
def _(Context, ElicitRequest, ElicitRequestFormParams, InputRequiredResult, json):
    def ask(key: str, message: str, field: str, request_state: str | None = None) -> InputRequiredResult:
        """組一個「請客戶端問使用者一個文字欄位」的 InputRequiredResult。"""
        _params = ElicitRequestFormParams(
            message=message,
            requested_schema={"type": "object", "properties": {field: {"type": "string"}}, "required": [field]},
        )
        return InputRequiredResult(
            result_type="input_required",
            input_requests={key: ElicitRequest(method="elicitation/create", params=_params)},
            request_state=request_state,
        )

    def add_booking_tool(server):
        """把 book_table 工具裝到一台伺服器上（後面會蓋好幾台，所以寫成函式）。"""

        @server.tool
        async def book_table(ctx: Context) -> str | InputRequiredResult:
            """訂位：會分兩回合問你人數與日期。"""
            _answers = ctx.input_responses
            if _answers is None:                                   # 第 1 回合：什麼都還沒問
                return ask("people", "幾位？", "people")
            if "people" in _answers:                               # 第 2 回合：拿到人數，問日期，人數塞進 request_state
                _people = _answers["people"].content["people"]
                return ask("date", f"{_people} 位，哪一天？", "date",
                           request_state=json.dumps({"people": _people, "vip": True}))
            _carried = json.loads(ctx.request_state)               # 第 3 回合：人數從 request_state 拿回來
            return f"已訂位：{_carried['people']} 位，{_answers['date'].content['date']}（vip={_carried['vip']}）"

        return server
    return add_booking_tool, ask


@app.cell
async def _(Client, ElicitResult, FastMCP, add_booking_tool, mo):
    booking = add_booking_tool(FastMCP("訂位"))
    asked = []   # 客戶端被問了哪些問題

    async def answer_questions(message, response_type, params, ctx):
        """客戶端的 elicitation handler：這裡假裝使用者回答。真實客戶端會跳出表單。"""
        asked.append(message)
        if "幾位" in message:
            return ElicitResult(action="accept", content=response_type(people="4"))
        return ElicitResult(action="accept", content=response_type(date="8/30"))

    async with Client(booking, elicitation_handler=answer_questions) as _c:
        booking_result = (await _c.call_tool("book_table", {})).data
    mo.md(
        f"""
    `call_tool("book_table")` 對呼叫端看起來**就是一次呼叫**，回傳 `{booking_result!r}`——
    但中間客戶端被問了 **{len(asked)} 次**：`{asked}`。SDK 自動跑完了三個回合（上限 `input_required_max_rounds=10`，防止壞掉的 guard 無限迴圈）。
    `ctx.request_state` 把人數從第 2 回合帶到第 3 回合——接下來我們看它在線路上長什麼樣。
    """
    )
    return answer_questions, asked, booking, booking_result


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 4️⃣ 線路實況：把 `requestState` 截下來——它是密文

    起一台真的 HTTP 伺服器（第 3 課的寫法：uvicorn 在背景執行緒），**不用 SDK**，自己用 `httpx.post`
    一回合一回合發 `tools/call`，把伺服器回給客戶端的 `requestState` 原封不動印出來。
    """
    )
    return


@app.cell
def _(socket, threading, time, uvicorn):
    def serve(app, port: int) -> str:
        """在背景執行緒起一台 uvicorn；port 已開就不重起。回傳 MCP 網址。"""

        def _busy():
            with socket.socket() as _s:
                return _s.connect_ex(("127.0.0.1", port)) == 0

        if not _busy():
            _server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning"))
            threading.Thread(target=_server.run, daemon=True).start()
            for _ in range(50):
                if _busy():
                    break
                time.sleep(0.1)
        return f"http://127.0.0.1:{port}/mcp"
    return (serve,)


@app.cell
def _(httpx):
    WIRE_HEADERS = {"Accept": "application/json, text/event-stream", "Content-Type": "application/json",
                    "MCP-Protocol-Version": "2026-07-28", "mcp-method": "tools/call", "mcp-name": "book_table"}
    WIRE_META = {"io.modelcontextprotocol/protocolVersion": "2026-07-28", "io.modelcontextprotocol/clientCapabilities": {}}

    def call_raw(url: str, params: dict) -> dict:
        """一發裸 POST 的 tools/call（新協定三要件：版本 header、mcp-method header、_meta 信封）。"""
        _body = {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {**params, "_meta": WIRE_META}}
        return httpx.post(url, json=_body, headers=WIRE_HEADERS).json()
    return WIRE_HEADERS, WIRE_META, call_raw


@app.cell
def _(FastMCP, add_booking_tool, base64, call_raw, json, mo, serve):
    url_a = serve(add_booking_tool(FastMCP("訂位")).http_app(), 8781)

    round1 = call_raw(url_a, {"name": "book_table", "arguments": {}})["result"]
    round2 = call_raw(url_a, {"name": "book_table", "arguments": {},
                              "inputResponses": {"people": {"action": "accept", "content": {"people": "4"}}}})["result"]
    sealed = round2["requestState"]                    # ← 伺服器發給客戶端、要它下回合帶回來的東西
    sealed_raw = base64.urlsafe_b64decode(sealed[3:] + "=" * (-len(sealed[3:]) % 4))   # 去掉 "v1." 前綴再解 base64
    looks_readable = any(_w in sealed_raw for _w in (b"people", b"vip"))

    mo.md(
        f"""
    **第 1 回合**（沒帶答案）→ `resultType = {round1["resultType"]}`，`inputRequests` 的 key：`{list(round1["inputRequests"])}`，
    `requestState = {round1.get("requestState")}`（工具第一回合沒放東西）。

    **第 2 回合**（帶人數）→ 問「{round2["inputRequests"]["date"]["params"]["message"]}」，並附上 `requestState`：

    ```
    {sealed}
    ```

    {len(sealed)} 個字元。我們的工具放進去的明文是 `{json.dumps({"people": "4", "vip": True})}`——
    去掉 `v1.` 前綴、解 base64 之後：

    ```
    {sealed_raw[:48]!r} …
    ```

    裡面找得到 `people` 或 `vip` 這幾個字嗎？**{"找得到" if looks_readable else "找不到"}**。
    它不是 base64 包起來的 JSON，是**密文**。

    結構是 `v1.` ＋ base64url（**4 bytes 金鑰指紋** `{sealed_raw[:4].hex()}` ｜ **12 bytes nonce** `{sealed_raw[4:16].hex()}` ｜
    **{len(sealed_raw) - 16} bytes AES-256-GCM 密文＋驗證標籤**）。金鑰由伺服器的祕密經 HKDF-SHA256 派生；
    密文裡除了你的明文，還有一個 claims 信封：`iat`／`exp`（預設 10 分鐘）、綁定的 `method`、目標工具名、
    **參數摘要**、`aud`（伺服器名）、以及有認證時的使用者指紋。這些在下一節全部用實驗證明。
    """
    )
    return looks_readable, round1, round2, sealed, sealed_raw, url_a


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ### 正常把它帶回去：第 3 回合

    客戶端該做的事很簡單：把 `requestState` 原封不動放進下一回合的 `params`，附上日期的答案。
    伺服器會先**解密＋驗證**，通過才把明文交給工具（工具看到的 `ctx.request_state` 永遠是它自己放進去的明文）。
    """
    )
    return


@app.cell
def _(call_raw, mo, sealed, url_a):
    round3_params = {"name": "book_table", "arguments": {}, "requestState": sealed,
                     "inputResponses": {"date": {"action": "accept", "content": {"date": "8/30"}}}}
    round3 = call_raw(url_a, round3_params)
    mo.md(f"第 3 回合 → `{round3['result']['structuredContent']}`")
    return round3, round3_params


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 5️⃣ 五個攻擊實驗

    現在扮演一個不懷好意的客戶端（或中間人）。同一個第 3 回合請求，每次動一個地方：

    | # | 實驗 | 在測什麼 |
    |---|---|---|
    | 1 | 把密文改掉**一個字元** | 完整性：GCM 的驗證標籤 |
    | 2 | 同一個 token 拿去打**另一台**伺服器（各自的臨時金鑰） | 金鑰不同就解不開 |
    | 3 | 同一個 token，但把 `arguments` 改掉 | 綁定：token 只對「同一個工具＋同樣參數」有效 |
    | 4 | 同一把金鑰，但伺服器**名字不同** | `aud`：同公司共用金鑰的兩個服務也不能互換 token |
    | 5 | 把 `ttl` 設成 2 秒，等 2.5 秒再用 | 過期 |

    注意回應：**五個全部回同一句** `-32602 Invalid or expired requestState`——伺服器故意不告訴你是哪裡錯
    （真正原因只寫進伺服器 log：`seal`／`unknown key`／`request binding`／`audience`／`expired`）。
    這是刻意的：不給攻擊者任何可以逐步修正的線索。
    """
    )
    return


@app.cell
def _(FastMCP, RequestStateSecurity, add_booking_tool, call_raw, mo, round3_params, sealed, secrets, serve, time, url_a):
    def _outcome(resp):
        if "error" in resp:
            return f"🛑 {resp['error']['code']} {resp['error']['message']}"
        return f"✅ {resp['result']['structuredContent']}"

    # 1. 竄改一個字元
    _tampered = sealed[:-2] + ("A" if sealed[-2] != "A" else "B") + sealed[-1]
    attack_tamper = call_raw(url_a, {**round3_params, "requestState": _tampered})
    # 2. 另一台伺服器（各自的臨時金鑰）
    url_other = serve(add_booking_tool(FastMCP("訂位")).http_app(), 8782)
    attack_other_server = call_raw(url_other, round3_params)
    # 3. 同 token 換 arguments
    attack_args = call_raw(url_a, {**round3_params, "arguments": {"note": "靠窗"}})
    # 4. 同金鑰、不同伺服器名（audience）
    shared_key = secrets.token_hex(32)    # 正式環境放環境變數：python -c "import secrets; print(secrets.token_hex(32))"
    url_c = serve(add_booking_tool(FastMCP("訂位", request_state_security=RequestStateSecurity(keys=[shared_key]))).http_app(), 8783)
    url_e = serve(add_booking_tool(FastMCP("別家店", request_state_security=RequestStateSecurity(keys=[shared_key]))).http_app(), 8785)
    token_from_c = call_raw(url_c, {"name": "book_table", "arguments": {},
                                    "inputResponses": {"people": {"action": "accept", "content": {"people": "2"}}}})["result"]["requestState"]
    attack_audience = call_raw(url_e, {**round3_params, "requestState": token_from_c})
    # 5. ttl=2 秒
    url_f = serve(add_booking_tool(FastMCP("訂位", request_state_security=RequestStateSecurity(keys=[shared_key], ttl=2))).http_app(), 8786)
    _short = call_raw(url_f, {"name": "book_table", "arguments": {},
                              "inputResponses": {"people": {"action": "accept", "content": {"people": "2"}}}})["result"]["requestState"]
    time.sleep(2.5)
    attack_expired = call_raw(url_f, {**round3_params, "requestState": _short})

    mo.md(
        f"""
    | # | 實驗 | 伺服器回應 |
    |---|---|---|
    | 1 | 竄改一個字元 | {_outcome(attack_tamper)} |
    | 2 | 拿去另一台（不同臨時金鑰） | {_outcome(attack_other_server)} |
    | 3 | 同 token，`arguments` 改成 `{{"note": "靠窗"}}` | {_outcome(attack_args)} |
    | 4 | 同金鑰、伺服器名「別家店」 | {_outcome(attack_audience)} |
    | 5 | `ttl=2`，等 2.5 秒 | {_outcome(attack_expired)} |

    五個實驗、同一句錯誤。回到開頭的問題——**傳來傳去的狀態是加密的嗎？** 是：AES-256-GCM，
    客戶端**讀不到**內容、**改不了**內容、**換不了**用途、**放不久**。你在工具裡寫 `request_state=...` 時
    完全沒碰任何密碼學——這一切是 `RequestStateBoundary` 中介層在線路邊界自動做的。
    """
    )
    return (
        attack_args,
        attack_audience,
        attack_expired,
        attack_other_server,
        attack_tamper,
        shared_key,
        token_from_c,
        url_c,
        url_e,
        url_f,
        url_other,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 6️⃣ 多副本共用金鑰與輪替

    實驗 2 同時揭露了一個部署陷阱：**預設金鑰是每個 process 啟動時隨機產生的**（`RequestStateSecurity.ephemeral()`）。
    單一 process 沒問題；但多回合工具的第 2 回合若落到另一台副本，那台解不開第 1 回合發的 token，
    使用者就會莫名其妙拿到 `Invalid or expired requestState`。**重啟伺服器也一樣**——正在進行的多回合對話全部作廢。

    解法就是實驗 4 用過的：所有副本給同一把金鑰（至少 32 bytes 的祕密，放環境變數）：

    ```python
    mcp = FastMCP("訂位", request_state_security=RequestStateSecurity(
        keys=[os.environ["REQUEST_STATE_KEY"]],   # 所有副本相同
        ttl=600,                                  # 預設 10 分鐘
    ))
    ```

    `keys` 是一個**金鑰環**：`keys[0]` 負責加密，環上每一把都能解密。所以換金鑰不用停機：
    `keys=[舊, 新]` 全部佈署完 → `keys=[新, 舊]` → 等一個 ttl 之後 `keys=[新]`。
    密文開頭那 4 bytes 金鑰指紋就是讓伺服器 O(1) 找到該用環上哪一把。

    下面證明：副本 C 與 D 共用 `shared_key`，C 發的 token 到 D 照樣能完成訂位。
    """
    )
    return


@app.cell
def _(FastMCP, RequestStateSecurity, add_booking_tool, call_raw, mo, round3_params, serve, shared_key, token_from_c, url_c):
    url_d = serve(add_booking_tool(FastMCP("訂位", request_state_security=RequestStateSecurity(keys=[shared_key]))).http_app(), 8784)
    cross_replica = call_raw(url_d, {**round3_params, "requestState": token_from_c})
    mo.md(
        f"""
    副本 C（`{url_c}`）發的 token → 副本 D（`{url_d}`）完成第 3 回合：`{cross_replica.get("result", {}).get("structuredContent") or cross_replica.get("error")}`

    三種記憶「跨副本」各要什麼，現在可以收斂成一句話：**請求內狀態不用、session 狀態共用 store、請求狀態共用金鑰。**
    """
    )
    return cross_replica, url_d


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 7️⃣ 該用哪一種記憶

    | 你的需求 | 用 | 理由 |
    |---|---|---|
    | middleware 算好的東西要給工具用 | `ctx.set_state` | 同一個請求內，最便宜 |
    | 購物車、對話串、進行中的流程，要跨很多次呼叫 | `SessionId`（＋`SessionProvider`） | 資料留在伺服器端、可以很大、可以設 TTL；一個使用者可以有多個 |
    | 「這個使用者」的偏好與記憶，一人一桶 | `UserSession` | 不進 schema、由認證身分選桶——需要認證（補充課 A） |
    | 工具要問使用者一兩個問題再繼續 | `InputRequiredResult` ＋ `request_state` | 不用 session、不用 store；狀態小、短命、自動加密 |
    | 上面任何一種要跨副本 | 共用 store ／ 共用金鑰 | 見 2️⃣ 與 6️⃣ |

    兩個常見誤用：

    - 把一大包資料塞進 `request_state`——它每回合都經過客戶端來回，請放**小**的東西（id、幾個欄位）；大的放 session。
    - 拿 `request_state` 當長期記憶——它預設 10 分鐘過期，是為「一段對話」設計的。

    ### 知道有就好

    - 有認證時，`requestState` 還會綁**使用者指紋**：A 的 token 就算沒過期，B 帶著也會被拒（`principal`）。
    - 背景任務（`@mcp.tool(task=True)`）裡問問題用的是**同一套** guard 模式，補充課 C 會看到。
    - 想自己管金鑰（KMS）：`RequestStateSecurity(codec=你的實作)`，只要提供 `seal`／`unseal` 兩個方法。
    - Session 的 store 換成 Redis 時，用 `TTLClampWrapper(store, missing_ttl=3600)` 給每個 session 預設壽命，
      因為 FastMCP 寫 session 時不自帶 TTL，壽命由 store 決定。

    ## 🏆 延伸挑戰

    1. **LEVEL 1**：把 5️⃣ 實驗 5 的 `ttl=2` 改成 `ttl=60`，等 2.5 秒再用——這次應該成功。再把 2️⃣ 的副本 C 也接上 `shared_store`，
       確認它也讀得到購物車。
    2. **LEVEL 2**：給 3️⃣ 的 `book_table` 加第三回合：問完日期再問「要不要靠窗？」，把人數**與日期**都放進 `request_state`
       帶到第四回合。用 4️⃣ 的 `call_raw` 一回合一回合發，觀察每一回合的 `requestState` 都不一樣（nonce 每次重抽）。
    3. **LEVEL 3**：做金鑰輪替：起兩台副本，一台 `keys=[新, 舊]`、一台 `keys=[舊]`，用舊金鑰那台發 token、到新舊並存那台完成；
       反過來（新金鑰發的 token 到只有舊金鑰的那台）應該被拒。想一想正式環境三個階段的佈署順序為什麼不能跳步。

    帶得走：下載本檔後 `uvx marimo edit --sandbox fastmcp4-state_ext.py` 在自己電腦繼續玩。
    下一課：**FastMCP 4 專屬功能**——背景任務、快取提示、gateway 路由 header、自訂擴充。
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.accordion(
        {
            "💡 LEVEL 1 參考解答": mo.md(
                r"""
    **ttl 改長**——新的一格（port 換一個，避免撞到 5️⃣ 那台）：

    ```python
    _url = serve(add_booking_tool(FastMCP("訂位", request_state_security=RequestStateSecurity(keys=[shared_key], ttl=60))).http_app(), 8787)
    _t = call_raw(_url, {"name": "book_table", "arguments": {},
                         "inputResponses": {"people": {"action": "accept", "content": {"people": "2"}}}})["result"]["requestState"]
    time.sleep(2.5)
    call_raw(_url, {**round3_params, "requestState": _t})
    ```

    你應該看到 `{'result': {'result': '已訂位：2 位，8/30（vip=True）'}}`——同樣等 2.5 秒，ttl=60 就還在有效期內。

    **副本 C 接上 store**——把 2️⃣ 那格的 `replica_c = build_replica("副本 C")` 改成
    `replica_c = build_replica("副本 C", shared_store)`，重跑下一格：表格第三列會從 🛑 變成 `['紅茶', '滷肉飯']`。
    """
            ),
            "💡 LEVEL 2 參考解答": mo.md(
                r"""
    新的一格，另外蓋一台（不要改 3️⃣ 的 `add_booking_tool`，其他格還在用）：

    ```python
    def add_booking_tool_v2(server):
        @server.tool
        async def book_table(ctx: Context) -> str | InputRequiredResult:
            _a = ctx.input_responses
            if _a is None:
                return ask("people", "幾位？", "people")
            if "people" in _a:
                _people = _a["people"].content["people"]
                return ask("date", f"{_people} 位，哪一天？", "date", request_state=json.dumps({"people": _people}))
            _carried = json.loads(ctx.request_state)
            if "date" in _a:
                _carried["date"] = _a["date"].content["date"]
                return ask("window", "要不要靠窗？", "window", request_state=json.dumps(_carried))
            return f"已訂位：{_carried['people']} 位，{_carried['date']}，靠窗={_a['window'].content['window']}"
        return server

    _url = serve(add_booking_tool_v2(FastMCP("訂位v2")).http_app(), 8788)
    _r2 = call_raw(_url, {"name": "book_table", "arguments": {},
                          "inputResponses": {"people": {"action": "accept", "content": {"people": "3"}}}})["result"]
    _r3 = call_raw(_url, {"name": "book_table", "arguments": {}, "requestState": _r2["requestState"],
                          "inputResponses": {"date": {"action": "accept", "content": {"date": "9/1"}}}})["result"]
    _r4 = call_raw(_url, {"name": "book_table", "arguments": {}, "requestState": _r3["requestState"],
                          "inputResponses": {"window": {"action": "accept", "content": {"window": "要"}}}})["result"]
    (_r2["requestState"][:30], _r3["requestState"][:30], _r4["structuredContent"])
    ```

    你應該看到第 2、3 回合的 `requestState` 開頭相同（`v1.` ＋同一個金鑰指紋）、後面完全不同（nonce 每次重抽、明文也不同），
    第 4 回合回 `{'result': '已訂位：3 位，9/1，靠窗=要'}`。
    注意第 3 回合的明文 `{"people": "3", "date": "9/1"}` 比第 2 回合長，密文也跟著變長——密文長度＝明文長度＋固定額外負擔，
    這是 GCM 的特性（所以別放大東西）。
    """
            ),
            "💡 LEVEL 3 提示": mo.md(
                r"""
    - 兩把金鑰：`old = secrets.token_hex(32)`、`new = secrets.token_hex(32)`。
    - 副本「只有舊」：`RequestStateSecurity(keys=[old])`；副本「新舊並存、新的加密」：`RequestStateSecurity(keys=[new, old])`。
    - 用「只有舊」那台發 token（第 2 回合），拿到「新舊並存」那台完成第 3 回合 → 應該 ✅（環上有舊金鑰能解）。
    - 反過來用「新舊並存」發（它用 `keys[0]=new` 加密），拿到「只有舊」那台 → 應該 🛑 `Invalid or expired requestState`（log 會寫 `unknown key`）。
    - 這就是為什麼三階段不能跳：直接從 `[old]` 跳到 `[new]`，過渡期間新副本發的 token 舊副本解不開、舊副本發的新副本也解不開；
      先 `[old, new]`（大家都能解兩種、仍用舊的加密）→ `[new, old]`（開始用新的加密）→ 等一個 ttl 沒有舊 token 在飛了才 `[new]`。
    - 驗證自己做對了：把密文前 4 bytes（金鑰指紋）印出來——兩把金鑰發的 token 指紋不同，你能從指紋看出是哪把金鑰加密的。
    """
            ),
        }
    )
    return


if __name__ == "__main__":
    app.run()
