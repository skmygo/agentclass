# /// script
# requires-python = ">=3.11"
# dependencies = ["openai>=2.0", "qdrant-client>=1.12", "fastmcp==4.0.0b1", "fastmcp-slim==4.0.0b1", "httpx", "uvicorn", "numpy", "pillow"]
# ///
# 定軌／換模型時的實測腳本（不部署、不進課程）。用法：uv run --script content/llm-apps/_spikes/<檔>.py
# 換模型：先改 spike_model_probe.py 的 M 與 spike_rag.py／spike_capstone.py 的 LLM，跑一遍，
# 再把數字更新到 notebook／page_content.py。
import json, time, base64, io
from openai import OpenAI
client = OpenAI(base_url="https://litellm.itsmygo.uk/v1", api_key="sk-FiIRnuzLH7ypgf29LTpHNw")
TOOLS=[{"type":"function","function":{"name":"get_weather","description":"查詢指定城市的即時天氣","parameters":{"type":"object","properties":{"city":{"type":"string","description":"城市名，例如：台北"}},"required":["city"]}}}]
Q=[{"role":"user","content":"台北現在天氣怎麼樣？"}]
for model in ["gpt-oss-120b","gemini-3.5-flash","nemotron-3-ultra","deepseek-v4-flash","cf-gpt-oss-120b"]:
    t0=time.perf_counter()
    try:
        r=client.chat.completions.create(model=model,messages=Q,tools=TOOLS,max_tokens=512)
        m=r.choices[0].message
        print(model, f"{time.perf_counter()-t0:.1f}s", "tool_calls:", [(c.function.name,c.function.arguments) for c in (m.tool_calls or [])], "content:", repr((m.content or '')[:40]))
    except Exception as e: print(model, "ERR", str(e)[:100])
# two-round with gpt-oss-120b
r1=client.chat.completions.create(model="nemotron-3-ultra",messages=Q,tools=TOOLS,max_tokens=512)
call=r1.choices[0].message.tool_calls[0]
msgs=Q+[{"role":"assistant","content":"","tool_calls":[{"id":call.id,"type":"function","function":{"name":call.function.name,"arguments":call.function.arguments}}]},{"role":"tool","tool_call_id":call.id,"content":json.dumps({"weather":"晴","temp_c":31},ensure_ascii=False)}]
r2=client.chat.completions.create(model="nemotron-3-ultra",messages=msgs,tools=TOOLS,max_tokens=512)
print("final:", r2.choices[0].message.content)
# no-tool question: should answer directly
r3=client.chat.completions.create(model="nemotron-3-ultra",messages=[{"role":"user","content":"1+1=?"}],tools=TOOLS,max_tokens=512)
print("no-tool q ->", r3.choices[0].message.tool_calls, repr(r3.choices[0].message.content))
# structured output
RF={"type":"json_schema","json_schema":{"name":"person_info","strict":True,"schema":{"type":"object","properties":{"name":{"type":"string"},"age":{"type":"integer"},"city":{"type":"string"},"hobbies":{"type":"array","items":{"type":"string"}}},"required":["name","age","city","hobbies"],"additionalProperties":False}}}
P=[{"role":"user","content":"小明今年12歲，住在台北，喜歡籃球跟圍棋。請抽取人物資料。"}]
for model in ["gpt-oss-120b","gemini-3.5-flash","nemotron-3-ultra","deepseek-v4-flash"]:
    t0=time.perf_counter()
    try:
        r=client.chat.completions.create(model=model,messages=P,response_format=RF,max_tokens=512)
        txt=(r.choices[0].message.content or '').strip(); print(model, f"{time.perf_counter()-t0:.1f}s", repr(txt[:100]))
        d=json.loads(txt); print("   parsed:", d)
    except Exception as e: print(model,"ERR",str(e)[:100])
# without response_format for contrast
r=client.chat.completions.create(model="nemotron-3-ultra",messages=P,max_tokens=512); print("no schema:", repr(r.choices[0].message.content[:200]))
# vision
from PIL import Image, ImageDraw
img=Image.new("RGB",(200,200),"white"); ImageDraw.Draw(img).ellipse((50,50,150,150),fill="red")
buf=io.BytesIO(); img.save(buf,format="PNG"); url="data:image/png;base64,"+base64.b64encode(buf.getvalue()).decode()
M=[{"role":"user","content":[{"type":"text","text":"圖片裡是什麼形狀？什麼顏色？用繁體中文一句話回答。"},{"type":"image_url","image_url":{"url":url}}]}]
for model in ["gemini-3.5-flash","gpt-oss-120b","nemotron-3-ultra"]:
    t0=time.perf_counter()
    try:
        r=client.chat.completions.create(model=model,messages=M,max_tokens=512); print(model, f"{time.perf_counter()-t0:.1f}s", repr((r.choices[0].message.content or '')[:80]))
    except Exception as e: print(model,"ERR",str(e)[:120])
