# /// script
# requires-python = ">=3.11"
# dependencies = ["openai>=2.0", "qdrant-client>=1.12", "fastmcp==4.0.0b1", "fastmcp-slim==4.0.0b1", "httpx", "uvicorn", "numpy", "pillow"]
# ///
# 定軌／換模型時的實測腳本（不部署、不進課程）。用法：uv run --script content/llm-apps/_spikes/<檔>.py
# 換模型：先改 spike_model_probe.py 的 M 與 spike_rag.py／spike_capstone.py 的 LLM，跑一遍，
# 再把數字更新到 notebook／page_content.py。
import threading, time, json, httpx, uvicorn
from fastmcp import FastMCP
mcp = FastMCP("Raw")
@mcp.tool
def add(a: int, b: int) -> int:
    """相加"""
    return a + b
app = mcp.http_app()
server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=8766, log_level="warning"))
threading.Thread(target=server.run, daemon=True).start(); time.sleep(1.5)
hdr = {"Accept": "application/json, text/event-stream", "Content-Type": "application/json", "MCP-Protocol-Version": "2026-07-28"}
meta = {"io.modelcontextprotocol/protocolVersion": "2026-07-28", "io.modelcontextprotocol/clientCapabilities": {}}
body = {"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"add","arguments":{"a":40,"b":2},"_meta":meta}}
for i in range(2):
    r = httpx.post("http://127.0.0.1:8766/mcp", json=body, headers={**hdr, "mcp-method": "tools/call", "mcp-name": "add"})
    print("raw POST:", r.status_code, {k:v for k,v in r.headers.items() if 'session' in k or 'content-type' in k}, r.text[:400])
r = httpx.post("http://127.0.0.1:8766/mcp", json={"jsonrpc":"2.0","id":2,"method":"tools/list","params":{"_meta":meta}}, headers={**hdr, "mcp-method": "tools/list"})
print("tools/list:", r.status_code, r.text[:300])
# legacy: need initialize first
r = httpx.post("http://127.0.0.1:8766/mcp", json={"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"x","version":"1"}}}, headers={"Accept": "application/json, text/event-stream", "Content-Type": "application/json"})
print("legacy init:", r.status_code, r.headers.get("mcp-session-id"), r.text[:200])
server.should_exit = True
