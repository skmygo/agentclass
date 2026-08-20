# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "fastmcp==4.0.0b1",
#     "fastmcp-slim==4.0.0b1",
#     "httpx",
#     "uvicorn",
# ]
# ///
"""補充課 C（mcp-servers-tour）的定軌 spike：接上「別人寫好的」MCP 伺服器。

驗證：
1. 用 uvx 以 stdio 起官方參考伺服器 mcp-server-time / mcp-server-fetch，list_tools、call_tool
2. 多伺服器設定檔（mcpServers dict）→ 工具自動加前綴
3. 公開的遠端 HTTP 伺服器：DeepWiki（舊協定）、Context7（已是 2026-07-28 新協定）
4. 把它們 mount 進自己的 FastMCP（create_proxy + namespace）→ 一台 HTTP 伺服器對外（stdio→HTTP 橋接）
5. npx 類伺服器（filesystem）有 node 才跑，沒有就優雅跳過
"""
import asyncio
import shutil
import socket
import tempfile
import threading
import time
from pathlib import Path

import uvicorn
from fastmcp import Client, FastMCP
from fastmcp.server import create_proxy


def text_of(result):
    """工具結果：有 structuredContent 用 .data，否則取第一個文字區塊。"""
    if result.data is not None:
        return result.data
    return result.content[0].text if result.content else None


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


SERVERS = {
    "mcpServers": {
        "time": {"command": "uvx", "args": ["mcp-server-time"]},
        "fetch": {"command": "uvx", "args": ["mcp-server-fetch"]},
    }
}


async def part_stdio():
    print("\n=== 1+2 uvx stdio 伺服器 + 多伺服器設定 ===")
    t0 = time.perf_counter()
    async with Client(SERVERS) as c:
        print(f"connected {time.perf_counter() - t0:.1f}s, protocol {c.protocol_version}")
        for t in await c.list_tools():
            print(" ", t.name, "|", (t.description or "").splitlines()[0][:70], "|", list(t.input_schema.get("properties", {})))
        r = await c.call_tool("time_get_current_time", {"timezone": "Asia/Taipei"})
        print("time ->", text_of(r))
        r = await c.call_tool("time_convert_time", {"source_timezone": "Asia/Taipei", "time": "09:00", "target_timezone": "America/New_York"})
        print("convert ->", str(text_of(r))[:160])
        r = await c.call_tool("fetch_fetch", {"url": "https://gofastmcp.com/llms.txt", "max_length": 400})
        print("fetch ->", str(text_of(r))[:200].replace("\n", " "))
    # 單一伺服器不加前綴
    async with Client({"mcpServers": {"time": SERVERS["mcpServers"]["time"]}}) as c:
        print("single server tool names:", [t.name for t in await c.list_tools()])


async def part_remote():
    print("\n=== 3 公開遠端 HTTP 伺服器 ===")
    for url in ("https://mcp.deepwiki.com/mcp", "https://mcp.context7.com/mcp"):
        try:
            t0 = time.perf_counter()
            async with Client(url) as c:
                tools = await c.list_tools()
                print(url, "| protocol", c.protocol_version, "|", [t.name for t in tools], f"| {time.perf_counter() - t0:.1f}s")
                if "context7" in url:
                    r = await c.call_tool("resolve-library-id", {"libraryName": "fastmcp", "query": "how to add a tool"})
                    print("   resolve-library-id ->", str(text_of(r))[:300].replace("\n", " "))
                else:
                    r = await c.call_tool("read_wiki_structure", {"repoName": "PrefectHQ/fastmcp"})
                    print("   read_wiki_structure ->", str(text_of(r))[:200].replace("\n", " "))
        except Exception as e:  # noqa: BLE001
            print(url, "FAIL", type(e).__name__, str(e)[:140])


async def part_gateway():
    print("\n=== 4 mount 成一台：stdio → HTTP 橋接 ===")
    hub = FastMCP("我的工具集")

    @hub.tool
    def hello(name: str) -> str:
        """自己的工具。"""
        return f"hi {name}"

    # mcp-server-time 是 SDK v1 的老伺服器，只會握手協定：pin mode="legacy"，不然新協定的 hub 客戶端會讓 proxy 用新協定去敲它
    hub.mount(create_proxy({"mcpServers": {"default": SERVERS["mcpServers"]["time"]}}, mode="legacy"), namespace="time")
    hub.mount(create_proxy("https://mcp.context7.com/mcp"), namespace="c7")
    url = serve(hub.http_app(), 8791)
    async with Client(url) as c:
        print("hub protocol", c.protocol_version, "tools:", [t.name for t in await c.list_tools()])
        print("time via hub ->", text_of(await c.call_tool("time_get_current_time", {"timezone": "Asia/Tokyo"})))
        print("hello ->", text_of(await c.call_tool("hello", {"name": "mcp"})))


async def part_npx():
    print("\n=== 5 npx 類伺服器（filesystem）===")
    if not shutil.which("npx"):
        print("no npx → skip")
        return
    d = Path(tempfile.mkdtemp())
    (d / "note.txt").write_text("hello from filesystem server")
    cfg = {"mcpServers": {"fs": {"command": "npx", "args": ["-y", "@modelcontextprotocol/server-filesystem", str(d)]}}}
    t0 = time.perf_counter()
    try:
        async with Client(cfg) as c:
            names = [t.name for t in await c.list_tools()]
            print(f"connected {time.perf_counter() - t0:.1f}s; {len(names)} tools:", names[:8], "...")
            r = await c.call_tool("read_text_file", {"path": str(d / "note.txt")})
            print("read_text_file ->", text_of(r))
            r = await c.call_tool("list_directory", {"path": str(d)})
            print("list_directory ->", str(text_of(r))[:100])
    except Exception as e:  # noqa: BLE001
        print("npx FAIL", type(e).__name__, str(e)[:200])


async def main():
    import sys
    parts = {"stdio": part_stdio, "remote": part_remote, "gateway": part_gateway, "npx": part_npx}
    for name in (sys.argv[1:] or parts):
        await parts[name]()


if __name__ == "__main__":
    asyncio.run(main())
