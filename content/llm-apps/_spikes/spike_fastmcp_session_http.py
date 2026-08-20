# /// script
# requires-python = ">=3.11"
# dependencies = ["openai>=2.0", "qdrant-client>=1.12", "fastmcp==4.0.0b1", "fastmcp-slim==4.0.0b1", "httpx", "uvicorn", "numpy", "pillow"]
# ///
# 定軌／換模型時的實測腳本（不部署、不進課程）。用法：uv run --script content/llm-apps/_spikes/<檔>.py
# 換模型：先改 spike_model_probe.py 的 M 與 spike_rag.py／spike_capstone.py 的 LLM，跑一遍，
# 再把數字更新到 notebook／page_content.py。
import asyncio, json, threading, time
import httpx, uvicorn
from fastmcp import FastMCP, Client
from fastmcp.server.sessions import SessionProvider, SessionId, get_session, create_session

mcp = FastMCP("Cart")
mcp.add_provider(SessionProvider())

@mcp.tool
def add(a: int, b: int) -> int:
    """相加"""
    return a + b


@mcp.tool
async def add_item(session_id: SessionId, item: str) -> list[str]:
    """把品項加進購物車。"""
    s = await get_session(session_id)
    items = await s.get("items", default=[])
    items.append(item)
    await s.set("items", items)
    return items

async def inmem():
    async with Client(mcp) as c:
        tools = await c.list_tools()
        for t in tools: print("TOOL", t.name, json.dumps(t.input_schema, ensure_ascii=False))
        r0 = await c.call_tool("create_session"); print("create_session ->", r0.data, r0.structured_content); cid = r0.data if isinstance(r0.data,str) else r0.structured_content.get("session_id") or r0.data
        print((await c.call_tool("add_item", {"session_id": cid, "item": "紅茶"})).data)
        print((await c.call_tool("add_item", {"session_id": cid, "item": "滷肉飯"})).data)
    # new client connection, same id → state persists (stateless transport, stateful app)
    async with Client(mcp) as c2:
        print("new conn:", (await c2.call_tool("add_item", {"session_id": cid, "item": "綠茶"})).data)
        try: await c2.call_tool("add_item", {"session_id": "guess-123", "item": "x"})
        except Exception as e: print("guess ->", type(e).__name__, str(e)[:100])
asyncio.run(inmem())

# HTTP
app = mcp.http_app()
cfg = uvicorn.Config(app, host="127.0.0.1", port=8765, log_level="warning")
server = uvicorn.Server(cfg)
threading.Thread(target=server.run, daemon=True).start()
time.sleep(1.5)

async def over_http():
    async with Client("http://127.0.0.1:8765/mcp") as c:
        print("http proto:", c.protocol_version, (await c.call_tool("add", {"a":1,"b":2})).data)
    async with Client("http://127.0.0.1:8765/mcp", mode="legacy") as c:
        print("legacy proto:", c.protocol_version, (await c.call_tool("add", {"a":1,"b":2})).data)
asyncio.run(over_http())

# raw single POST, no handshake
hdr = {"Accept": "application/json, text/event-stream", "Content-Type": "application/json"}
body = {"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"add","arguments":{"a":40,"b":2}}}
r = httpx.post("http://127.0.0.1:8765/mcp", json=body, headers=hdr)
print("raw POST:", r.status_code, dict(r.headers), r.text[:300])
for v in ["2026-07-28", "2025-06-18"]:
    r = httpx.post("http://127.0.0.1:8765/mcp", json=body, headers={**hdr, "MCP-Protocol-Version": v})
    print("raw POST with", v, ":", r.status_code, r.text[:300])
r = httpx.post("http://127.0.0.1:8765/mcp", json={"jsonrpc":"2.0","id":2,"method":"tools/list"}, headers={**hdr, "MCP-Protocol-Version": "2026-07-28"})
print("tools/list:", r.status_code, r.text[:200])
server.should_exit = True
