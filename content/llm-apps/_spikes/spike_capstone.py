# /// script
# requires-python = ">=3.11"
# dependencies = ["openai>=2.0", "qdrant-client>=1.12", "fastmcp==4.0.0b1", "fastmcp-slim==4.0.0b1", "httpx", "uvicorn", "numpy", "pillow"]
# ///
# 定軌／換模型時的實測腳本（不部署、不進課程）。用法：uv run --script content/llm-apps/_spikes/<檔>.py
# 換模型：先改 spike_model_probe.py 的 M 與 spike_rag.py／spike_capstone.py 的 LLM，跑一遍，
# 再把數字更新到 notebook／page_content.py。
import asyncio, json, time
from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct
from fastmcp import FastMCP, Client
exec(open(__file__.replace("spike_capstone.py","spike_rag.py")).read().split("def chunk_by_heading")[0].split("EMB=")[0])  # imports
EMB="qwen3-embedding-0.6b"; LLM="nemotron-3.5-lightning"
DOC = open(__file__.replace("spike_capstone.py","spike_rag.py")).read().split('DOC = """')[1].split('"""')[0]
chunks = ["## " + b.strip() for b in DOC.split("\n## ")[1:]]
oa = OpenAI(base_url="https://litellm.itsmygo.uk/v1", api_key="sk-FiIRnuzLH7ypgf29LTpHNw")
e = oa.embeddings.create(model=EMB, input=chunks)
q = QdrantClient(":memory:"); q.create_collection("handbook", vectors_config=VectorParams(size=1024, distance=Distance.COSINE))
q.upsert("handbook", points=[PointStruct(id=i, vector=d.embedding, payload={"text":chunks[i], "title":chunks[i].splitlines()[0].lstrip('# ')}) for i,d in enumerate(e.data)])

mcp = FastMCP("山茶屋知識庫", instructions="回答顧客關於山茶屋貓咪咖啡廳的問題前，先用 search_handbook 查手冊。")
@mcp.tool
def search_handbook(query: str, top_k: int = 3) -> list[dict]:
    """在山茶屋店務手冊裡做語意搜尋，回傳最相關的段落（含相似度分數）。回答任何關於店內規定、貓咪、會員、活動的問題前都應先呼叫。query 請用繁體中文、可以放多個關鍵字（手冊是繁體中文寫的）。"""
    qv = oa.embeddings.create(model=EMB, input=query).data[0].embedding
    hits = q.query_points("handbook", query=qv, limit=top_k).points
    return [{"title": h.payload["title"], "score": round(h.score, 3), "text": h.payload["text"]} for h in hits]
@mcp.tool
def list_sections() -> list[str]:
    """列出手冊所有章節標題。"""
    return [c.splitlines()[0].lstrip('# ') for c in chunks]

async def agent(question, log):
    async with Client(mcp) as c:
        tools = await c.list_tools()
        oa_tools = [{"type":"function","function":{"name":t.name,"description":t.description,"parameters":t.input_schema}} for t in tools]
        msgs=[{"role":"system","content":"你是山茶屋貓咪咖啡廳的客服。遇到店務問題先用工具查手冊，只根據查到的內容回答，查不到就說手冊裡沒有寫。用繁體中文簡短回答，並在句尾用（來源：章節名）標注。"},{"role":"user","content":question}]
        for step in range(6):
            r = oa.chat.completions.create(model=LLM, messages=msgs, tools=oa_tools, max_tokens=4096)
            m = r.choices[0].message
            if not m.tool_calls:
                log.append(("answer", m.content)); return m.content
            msgs.append({"role":"assistant","content":m.content or "","tool_calls":[{"id":tc.id,"type":"function","function":{"name":tc.function.name,"arguments":tc.function.arguments}} for tc in m.tool_calls]})
            for tc in m.tool_calls:
                args = json.loads(tc.function.arguments or "{}")
                try:
                    res = await c.call_tool(tc.function.name, args); out = json.dumps(res.data, ensure_ascii=False)
                except Exception as ex:
                    out = f"錯誤：{ex}"
                log.append(("tool", tc.function.name, args, out[:120]))
                msgs.append({"role":"tool","tool_call_id":tc.id,"content":out})
        return "（超過步數上限）"
async def main():
    for qn in ["煤球是什麼樣的貓？可以抱牠嗎？", "我週二中午想去，順便停車，要注意什麼？", "你們手冊有哪些章節？", "1+1 等於多少？"]:
        log=[]; t0=time.perf_counter(); a = await agent(qn, log)
        print(f"\nQ: {qn}  ({time.perf_counter()-t0:.1f}s)")
        for l in log: print("  ", l if l[0]!="answer" else ("answer", l[1][:160].replace("\n"," ")))
asyncio.run(main())
