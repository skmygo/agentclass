# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "fastmcp==4.0.0b1",
#     "fastmcp-slim==4.0.0b1",
#     "httpx",
#     "uvicorn",
# ]
# ///
"""補充課 B（fastmcp4-state）的定軌 spike：無狀態協定上的三種狀態，以及「傳來傳去的狀態有沒有加密」。

驗證：
1. 多回合工具（InputRequiredResult）：SDK client 帶 elicitation_handler 自動跑完三回合
2. 線路實況：裸 POST 拿到 resultType=input_required 與 requestState 密文；解碼看它是不是明文
3. 竄改一個字元 → -32602 Invalid or expired requestState；拿到另一台（不同金鑰）→ 被拒；共用 keys → 通過；ttl 過期 → 被拒
4. 伺服器端狀態：兩台 FastMCP 共用同一個 session_state_store → A 建的 session B 讀得到（模擬多副本）
5. ctx.set_state：只活在一個請求內
"""
import asyncio
import base64
import json
import secrets
import socket
import threading
import time

import httpx
import uvicorn
from fastmcp import Client, Context, FastMCP
from fastmcp.client.elicitation import ElicitResult
from fastmcp.server.sessions import SessionId, SessionProvider, get_session
from key_value.aio.stores.memory import MemoryStore
from mcp.server.request_state import RequestStateSecurity
from mcp.types import ElicitRequest, ElicitRequestFormParams, InputRequiredResult


def serve(app, port):
    def busy():
        with socket.socket() as s:
            return s.connect_ex(("127.0.0.1", port)) == 0

    if not busy():
        server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning"))
        threading.Thread(target=server.run, daemon=True).start()
        for _ in range(50):
            if busy():
                break
            time.sleep(0.1)
    return f"http://127.0.0.1:{port}/mcp"


def ask(key, message, field, request_state=None):
    params = ElicitRequestFormParams(
        message=message,
        requested_schema={"type": "object", "properties": {field: {"type": "string"}}, "required": [field]},
    )
    return InputRequiredResult(
        result_type="input_required",
        input_requests={key: ElicitRequest(method="elicitation/create", params=params)},
        request_state=request_state,
    )


def build_booking(name="訂位", security=None):
    kw = {"request_state_security": security} if security else {}
    mcp = FastMCP(name, **kw)

    @mcp.tool
    async def book_table(ctx: Context) -> str | InputRequiredResult:
        """訂位：會分兩回合問你人數與日期。"""
        answers = ctx.input_responses
        if answers is None:
            return ask("people", "幾位？", "people")
        if "people" in answers:
            people = answers["people"].content["people"]
            return ask("date", f"{people} 位，哪一天？", "date", request_state=json.dumps({"people": people, "vip": True}))
        carried = json.loads(ctx.request_state)
        return f"已訂位：{carried['people']} 位，{answers['date'].content['date']}（vip={carried['vip']}）"

    return mcp


HEAD = {"Accept": "application/json, text/event-stream", "Content-Type": "application/json",
        "MCP-Protocol-Version": "2026-07-28", "mcp-method": "tools/call", "mcp-name": "book_table"}
META = {"io.modelcontextprotocol/protocolVersion": "2026-07-28", "io.modelcontextprotocol/clientCapabilities": {}}


def call_raw(url, params, rid=1):
    return httpx.post(url, json={"jsonrpc": "2.0", "id": rid, "method": "tools/call", "params": {**params, "_meta": META}}, headers=HEAD)


async def part_rounds():
    print("\n=== 1 SDK 自動跑完多回合 ===")
    mcp = build_booking()
    rounds = []

    async def handler(message, response_type, params, ctx):
        rounds.append(message)
        if "幾位" in message:
            return ElicitResult(action="accept", content=response_type(people="4"))
        return ElicitResult(action="accept", content=response_type(date="8/30"))

    async with Client(mcp, elicitation_handler=handler) as c:
        r = await c.call_tool("book_table", {})
    print("result:", r.data, "| 問了", len(rounds), "次：", rounds)


async def part_wire():
    print("\n=== 2+3 線路實況：requestState 是什麼 ===")
    url_a = serve(build_booking("A").http_app(), 8781)
    r1 = call_raw(url_a, {"name": "book_table", "arguments": {}}).json()["result"]
    print("round1 resultType:", r1.get("resultType"), "| inputRequests keys:", list(r1["inputRequests"]), "| requestState:", r1.get("requestState"))
    r2 = call_raw(url_a, {"name": "book_table", "arguments": {},
                          "inputResponses": {"people": {"action": "accept", "content": {"people": "4"}}}}).json()["result"]
    token = r2["requestState"]
    print("round2 message:", r2["inputRequests"]["date"]["params"]["message"], "| requestState:", token[:24], "… len", len(token))
    raw = base64.urlsafe_b64decode(token[3:] + "=" * (-len(token[3:]) % 4))
    print("  base64 解開後：", raw[:40], "... 可讀？", any(w in raw for w in (b"people", b"vip")))
    print("  結構：prefix=v1. | kid 4B:", raw[:4].hex(), "| nonce 12B:", raw[4:16].hex(), "| ciphertext+tag:", len(raw) - 16, "B")
    # round3 正常
    done = {"name": "book_table", "arguments": {}, "requestState": token,
            "inputResponses": {"date": {"action": "accept", "content": {"date": "8/30"}}}}
    r3 = call_raw(url_a, done).json()
    print("round3 正常 ->", r3["result"]["structuredContent"] if "result" in r3 else r3["error"])
    # 竄改
    bad = token[:-2] + ("A" if token[-2] != "A" else "B") + token[-1]
    r4 = call_raw(url_a, {**done, "requestState": bad}).json()
    print("竄改一個字元 ->", r4.get("error"))
    # 拿到另一台（不同 ephemeral key）
    url_b = serve(build_booking("A").http_app(), 8782)
    r5 = call_raw(url_b, done).json()
    print("同一個 token 打另一台（各自的臨時金鑰）->", r5.get("error"))
    # 綁定：同樣的 token 換 arguments
    r6 = call_raw(url_a, {**done, "arguments": {"x": 1}}).json()
    print("同 token 但 arguments 變了 ->", r6.get("error"))

    print("\n--- 共用 keys：兩台副本 ---")
    key = secrets.token_hex(32)
    url_c = serve(build_booking("訂位", RequestStateSecurity(keys=[key])).http_app(), 8783)
    url_d = serve(build_booking("訂位", RequestStateSecurity(keys=[key])).http_app(), 8784)
    t = call_raw(url_c, {"name": "book_table", "arguments": {},
                         "inputResponses": {"people": {"action": "accept", "content": {"people": "2"}}}}).json()["result"]["requestState"]
    r7 = call_raw(url_d, {**done, "requestState": t}).json()
    print("C 發的 token 拿去 D（共用 key）->", r7.get("result", {}).get("structuredContent") or r7.get("error"))
    # audience: 同 key 但伺服器名不同
    url_e = serve(build_booking("別家店", RequestStateSecurity(keys=[key])).http_app(), 8785)
    r8 = call_raw(url_e, {**done, "requestState": t}).json()
    print("同 key 但伺服器名不同（audience）->", r8.get("error"))

    print("\n--- ttl ---")
    url_f = serve(build_booking("訂位", RequestStateSecurity(keys=[key], ttl=2)).http_app(), 8786)
    t2 = call_raw(url_f, {"name": "book_table", "arguments": {},
                          "inputResponses": {"people": {"action": "accept", "content": {"people": "2"}}}}).json()["result"]["requestState"]
    print("ttl=2 馬上用 ->", call_raw(url_f, {**done, "requestState": t2}).json().get("result", {}).get("structuredContent"))
    t3 = call_raw(url_f, {"name": "book_table", "arguments": {},
                          "inputResponses": {"people": {"action": "accept", "content": {"people": "2"}}}}).json()["result"]["requestState"]
    await asyncio.sleep(2.5)
    print("等 2.5 秒再用 ->", call_raw(url_f, {**done, "requestState": t3}).json().get("error"))


async def part_store():
    print("\n=== 4 伺服器端狀態：兩台共用 store ===")
    store = MemoryStore()

    def build(name):
        mcp = FastMCP(name, session_state_store=store)
        mcp.add_provider(SessionProvider())

        @mcp.tool
        async def add_to_cart(session_id: SessionId, item: str) -> list[str]:
            s = await get_session(session_id)
            items = await s.get("items", default=[])
            items.append(item)
            await s.set("items", items)
            return items

        @mcp.tool
        async def show_cart(session_id: SessionId) -> list[str]:
            return await (await get_session(session_id)).get("items", default=[])

        return mcp

    a, b = build("副本 A"), build("副本 B")
    async with Client(a) as ca:
        sid = (await ca.call_tool("create_session")).data
        await ca.call_tool("add_to_cart", {"session_id": sid, "item": "紅茶"})
    async with Client(b) as cb:
        print("A 建的 session，B 讀到：", (await cb.call_tool("show_cart", {"session_id": sid})).data)
    # 不共用 store 的第三台
    c = FastMCP("副本 C")
    c.add_provider(SessionProvider())

    @c.tool
    async def show_cart(session_id: SessionId) -> list[str]:
        return await (await get_session(session_id)).get("items", default=[])

    async with Client(c) as cc:
        try:
            print("不共用 store 的 C：", (await cc.call_tool("show_cart", {"session_id": sid})).data)
        except Exception as e:  # noqa: BLE001
            print("不共用 store 的 C ->", type(e).__name__, str(e)[:100])
    # 看 store 裡面長什麼樣
    try:
        keys = await store.keys(collection=None) if hasattr(store, "keys") else None
        print("store keys:", keys)
    except Exception as e:  # noqa: BLE001
        print("store keys n/a:", e)


async def part_ctx_state():
    print("\n=== 5 ctx.set_state 只活一個請求 ===")
    mcp = FastMCP("ctx")

    @mcp.tool
    async def tick(ctx: Context) -> dict:
        n = (await ctx.get_state("n")) or 0
        await ctx.set_state("n", n + 1)
        return {"n_before": n, "n_after": await ctx.get_state("n")}

    async with Client(mcp) as c:
        print([(await c.call_tool("tick")).data for _ in range(3)])


async def main():
    import sys
    parts = {"rounds": part_rounds, "wire": part_wire, "store": part_store, "ctx": part_ctx_state}
    for name in (sys.argv[1:] or parts):
        await parts[name]()


if __name__ == "__main__":
    asyncio.run(main())
