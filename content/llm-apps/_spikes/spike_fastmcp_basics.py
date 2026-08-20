# /// script
# requires-python = ">=3.11"
# dependencies = ["openai>=2.0", "qdrant-client>=1.12", "fastmcp==4.0.0b1", "fastmcp-slim==4.0.0b1", "httpx", "uvicorn", "numpy", "pillow"]
# ///
# 定軌／換模型時的實測腳本（不部署、不進課程）。用法：uv run --script content/llm-apps/_spikes/<檔>.py
# 換模型：先改 spike_model_probe.py 的 M 與 spike_rag.py／spike_capstone.py 的 LLM，跑一遍，
# 再把數字更新到 notebook／page_content.py。
import asyncio, json
from fastmcp import FastMCP, Client
from fastmcp.server.sessions import SessionProvider, SessionId, get_session, create_session, UserSession

mcp = FastMCP("Demo")

@mcp.tool
def add(a: int, b: int) -> int:
    """把兩個整數相加。"""
    return a + b

@mcp.tool
def search_menu(keyword: str, limit: int = 3) -> list[dict]:
    """依關鍵字搜尋菜單，回傳最多 limit 筆品項。"""
    MENU=[{"name":"珍珠奶茶","price":60},{"name":"紅茶","price":30},{"name":"綠茶拿鐵","price":70},{"name":"滷肉飯","price":45}]
    return [m for m in MENU if keyword in m["name"]][:limit]

@mcp.resource("menu://today")
def today_menu() -> str:
    """今日菜單（純文字）"""
    return "珍珠奶茶 60 / 紅茶 30 / 綠茶拿鐵 70 / 滷肉飯 45"

@mcp.resource("menu://item/{name}")
def item(name: str) -> dict:
    return {"name": name, "price": 60}

@mcp.prompt
def order_helper(budget: int) -> str:
    """產生點餐助理的提示詞"""
    return f"你是點餐助理。顧客預算 {budget} 元，請推薦組合。"

async def main():
    async with Client(mcp) as c:
        tools = await c.list_tools()
        for t in tools: print("TOOL", t.name, "|", t.description, "|", json.dumps(t.input_schema, ensure_ascii=False))
        r = await c.call_tool("add", {"a": 2, "b": 3}); print("add ->", r.data, r.content, r.structured_content)
        r = await c.call_tool("search_menu", {"keyword": "茶"}); print("search ->", r.data)
        try:
            await c.call_tool("add", {"a": "two", "b": 3})
        except Exception as e: print("bad args ->", type(e).__name__, str(e)[:150])
        res = await c.list_resources(); print("RES", [(str(x.uri), x.name) for x in res])
        tpl = await c.list_resource_templates(); print("TPL", [(x.uri_template, x.name) for x in tpl])
        r = await c.read_resource("menu://today"); print("read ->", r[0].text)
        r = await c.read_resource("menu://item/紅茶"); print("read tpl ->", r[0].text)
        ps = await c.list_prompts(); print("PROMPTS", [(p.name, [a.name for a in p.arguments or []]) for p in ps])
        p = await c.get_prompt("order_helper", {"budget": 100}); print("prompt ->", p.messages[0].role, p.messages[0].content)
        print("proto:", c.protocol_version, c.server_info, "instr:", c.instructions)
asyncio.run(main())
