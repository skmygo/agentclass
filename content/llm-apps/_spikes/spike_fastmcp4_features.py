# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "fastmcp==4.0.0b1",
#     "fastmcp-slim==4.0.0b1",
#     "fastmcp-tasks==4.0.0b1",
#     "httpx",
#     "uvicorn",
# ]
# ///
"""補充課 D（fastmcp4-features）的定軌 spike：FastMCP 4.0 專屬功能，全部本機可跑。

驗證（每項都用側錄器看線路上實際發生什麼）：
1. 背景任務：fastmcp-tasks + @mcp.tool(task=True) + Progress；新協定 client 會變成 task 輪詢、legacy client 同步跑
2. 快取提示：FastMCP(cache_ttl=..., cache_scope=...) + Client(cache=True) → 第二次 list_tools 不打伺服器
3. Gateway 路由 header：x-mcp-header → 請求帶 Mcp-Param-*；每個請求都有 Mcp-Method / Mcp-Name
4. @mcp.completion：prompt 參數自動完成
5. 自訂 extension：宣告 capability、加一個自訂方法、攔截 tools/call
6. 資源模板路徑安全：../ 與絕對路徑在進 handler 之前就被擋
7. 工具搜尋 transform（BM25）：大工具目錄變成 search_tools + call_tool 兩個
"""
import asyncio
import json
import socket
import threading
import time
from typing import Annotated, Any

import uvicorn
from fastmcp import Client, FastMCP
from fastmcp.dependencies import Progress
from fastmcp.exceptions import ToolError
from fastmcp.server.extensions import MethodBinding, ServerExtension
from fastmcp.server.transforms.search import BM25SearchTransform
from fastmcp_tasks import TasksExtension
from mcp.types import PromptReference, RequestParams
from pydantic import Field


class Recorder:
    def __init__(self, app):
        self.app = app
        self.log = []

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        h = {k.decode(): v.decode() for k, v in scope["headers"]}
        entry = {"HTTP": scope["method"], "mcp-method": h.get("mcp-method", "—"), "mcp-name": h.get("mcp-name", "—"),
                 "params": {k: v for k, v in h.items() if k.startswith("mcp-param-")}, "body.method": ""}
        self.log.append(entry)

        async def _recv():
            m = await receive()
            if m.get("body"):
                try:
                    entry["body.method"] = json.loads(m["body"]).get("method", "")
                except Exception:  # noqa: BLE001
                    entry["body.method"] = "(non-JSON)"
            return m

        return await self.app(scope, _recv, send)


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


def summarize(log):
    return [f"{e['HTTP']} {e['mcp-method']}" + (f" {e['mcp-name']}" if e['mcp-name'] != '—' else "") + (f" {e['params']}" if e['params'] else "")
            for e in log]


async def part_tasks():
    print("\n=== 1 背景任務 ===")
    mcp = FastMCP("慢工")
    mcp.add_extension(TasksExtension())

    @mcp.tool(task=True)
    async def brew(cups: int, progress: Progress = Progress()) -> str:
        """泡 cups 杯茶，每杯 0.3 秒。"""
        await progress.set_total(cups)
        for i in range(cups):
            await progress.set_message(f"第 {i + 1} 杯")
            await asyncio.sleep(0.3)
            await progress.increment()
        return f"泡好 {cups} 杯"

    rec = Recorder(mcp.http_app())
    url = serve(rec, 8801)
    updates = []

    async def on_progress(progress, total, message):
        updates.append((progress, total, message))

    t0 = time.perf_counter()
    async with Client(url, progress_handler=on_progress) as c:
        print("protocol", c.protocol_version, "| server capabilities extensions:",
              list((c.server_capabilities.extensions or {}).keys()) if hasattr(c.server_capabilities, "extensions") else c.server_capabilities)
        r = await c.call_tool("brew", {"cups": 3})
    print("result:", r.data, f"({time.perf_counter() - t0:.1f}s)", "| progress updates:", updates)
    print("wire (modern):", summarize(rec.log))
    rec.log.clear()
    updates.clear()
    async with Client(url, mode="legacy", progress_handler=on_progress) as c:
        r = await c.call_tool("brew", {"cups": 2})
    print("legacy result:", r.data, "| progress:", updates, "| wire:", summarize(rec.log))


async def part_cache_headers():
    print("\n=== 2+3 快取提示 + 路由 header ===")
    mcp = FastMCP("天氣", cache_ttl=300, cache_scope="public")

    @mcp.tool
    def forecast(city: Annotated[str, Field(json_schema_extra={"x-mcp-header": "City"})], days: int = 1) -> str:
        """查某城市未來幾天天氣。"""
        return f"{city}: 晴 ×{days}"

    rec = Recorder(mcp.http_app())
    url = serve(rec, 8802)
    async with Client(url, cache=True) as c:
        t1 = await c.list_tools()
        t2 = await c.list_tools()
        t3 = await c.list_tools()
        print("input_schema.city:", t1[0].input_schema["properties"]["city"])
        r = await c.call_tool("forecast", {"city": "taipei", "days": 2})
        r_cjk = await c.call_tool("forecast", {"city": "台北", "days": 1})
    print("cache: 三次 list_tools，伺服器收到的請求：", summarize(rec.log))
    print("forecast ->", r.data, "|", r_cjk.data)
    rec.log.clear()
    async with Client(url) as c:   # 沒開快取
        await c.list_tools()
        await c.list_tools()
    print("no cache: 兩次 list_tools →", summarize(rec.log))
    # raw result cache hints on the wire
    import httpx
    raw = httpx.post(url, json={"jsonrpc": "2.0", "id": 1, "method": "tools/list",
                               "params": {"_meta": {"io.modelcontextprotocol/protocolVersion": "2026-07-28", "io.modelcontextprotocol/clientCapabilities": {}}}},
                     headers={"Accept": "application/json, text/event-stream", "MCP-Protocol-Version": "2026-07-28", "mcp-method": "tools/list"}).json()
    print("tools/list raw ->", {k: v for k, v in raw.items() if k != "jsonrpc"} if "error" in raw else ("keys", list(raw["result"].keys()), "_meta", raw["result"].get("_meta")))


async def part_completion():
    print("\n=== 4 completion ===")
    mcp = FastMCP("詩")

    @mcp.prompt
    def write_poem(theme: str, style: str = "俳句") -> str:
        """寫一首詩。"""
        return f"用{style}寫一首關於{theme}的詩"

    @mcp.completion
    def complete(ref, argument, context):
        if isinstance(ref, PromptReference) and ref.name == "write_poem":
            opts = {"theme": ["貓", "貓咪咖啡廳", "茶", "颱風"], "style": ["俳句", "五言絕句", "七言律詩"]}[argument.name]
            return [o for o in opts if o.startswith(argument.value)]
        return None

    async with Client(mcp) as c:
        for partial in ("", "貓", "颱"):
            r = await c.complete(ref=PromptReference(type="ref/prompt", name="write_poem"), argument={"name": "theme", "value": partial})
            print(f"theme={partial!r} ->", r.values)


class CallCounter(ServerExtension):
    identifier = "tw.agentclass/call-counter"

    def __init__(self):
        self.count = 0

    def settings(self) -> dict[str, Any]:
        return {"unit": "calls"}

    def methods(self):
        class P(RequestParams):
            pass
        return [MethodBinding(method="callCounter/get", params_type=P, handler=self.get_count)]

    async def get_count(self, ctx, params):
        return {"count": self.count}

    async def intercept_tool_call(self, params, context, call_next):
        self.count += 1
        return await call_next()


async def part_extension():
    print("\n=== 5 自訂 extension ===")
    mcp = FastMCP("計數")
    counter = CallCounter()
    mcp.add_extension(counter)

    @mcp.tool
    def ping() -> str:
        return "pong"

    rec = Recorder(mcp.http_app())
    url = serve(rec, 8803)
    async with Client(url) as c:
        caps = c.server_capabilities
        ext = getattr(caps, "extensions", None)
        print("capabilities.extensions:", ext)
        for _ in range(3):
            await c.call_tool("ping")
        # 自訂方法：用 session 直接送
        try:
            r = await c.session.send_request({"method": "callCounter/get", "params": {}}, dict) if hasattr(c, "session") else None
            print("callCounter/get ->", r)
        except Exception as e:  # noqa: BLE001
            print("session send_request n/a:", type(e).__name__, str(e)[:100])
    import httpx
    raw = httpx.post(url, json={"jsonrpc": "2.0", "id": 9, "method": "callCounter/get",
                               "params": {"_meta": {"io.modelcontextprotocol/protocolVersion": "2026-07-28", "io.modelcontextprotocol/clientCapabilities": {}}}},
                     headers={"Accept": "application/json, text/event-stream", "MCP-Protocol-Version": "2026-07-28", "mcp-method": "callCounter/get"}).json()
    print("raw callCounter/get ->", raw.get("result") or raw.get("error"), "| counter.count =", counter.count)


async def part_path_security():
    print("\n=== 6 資源模板路徑安全 ===")
    mcp = FastMCP("檔案")
    seen = []

    @mcp.resource("docs://{path}")
    def read_doc(path: str) -> str:
        seen.append(path)
        return f"content of {path}"

    async with Client(mcp) as c:
        for p in ("guide", "a/b", "../etc/passwd", "/etc/passwd", "x%00y"):
            try:
                r = await c.read_resource(f"docs://{p}")
                print(f"{p!r} -> OK {r[0].text!r}")
            except Exception as e:  # noqa: BLE001
                print(f"{p!r} -> {type(e).__name__}: {str(e)[:90]}")
    print("handler 實際收到的 path：", seen)


async def part_search():
    print("\n=== 7 BM25 tool search ===")
    mcp = FastMCP("大目錄", transforms=[BM25SearchTransform()])
    for name, desc in [("send_email", "寄電子郵件給某人 email"), ("delete_record", "從資料庫刪除一筆紀錄 database delete"),
                       ("search_database", "在資料庫搜尋 database search"), ("resize_image", "縮放圖片 image"),
                       ("translate_text", "翻譯文字 translate")]:
        def make(n, d):
            def f(x: str) -> str:
                return f"{n}({x})"
            f.__name__ = n
            f.__doc__ = d
            return f
        mcp.tool(make(name, desc))
    async with Client(mcp) as c:
        print("list_tools ->", [t.name for t in await c.list_tools()])
        r = await c.call_tool("search_tools", {"query": "delete something from the database"})
        found = r.data if r.data is not None else r.content[0].text
        print("search_tools ->", str(found)[:300])
        r = await c.call_tool("delete_record", {"x": "row-1"})
        print("直接呼叫隱藏的 delete_record ->", r.data)
        try:
            r = await c.call_tool("call_tool", {"name": "resize_image", "arguments": {"x": "cat.png"}})
            print("call_tool proxy ->", r.data or r.content[0].text)
        except ToolError as e:
            print("call_tool proxy ->", str(e)[:120])


async def main():
    import sys
    parts = {"tasks": part_tasks, "cache": part_cache_headers, "completion": part_completion,
             "extension": part_extension, "path": part_path_security, "search": part_search}
    for name in (sys.argv[1:] or parts):
        await parts[name]()


if __name__ == "__main__":
    asyncio.run(main())
