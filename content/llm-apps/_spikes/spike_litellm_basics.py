# /// script
# requires-python = ">=3.11"
# dependencies = ["openai>=2.0", "qdrant-client>=1.12", "fastmcp==4.0.0b1", "fastmcp-slim==4.0.0b1", "httpx", "uvicorn", "numpy", "pillow"]
# ///
# 定軌／換模型時的實測腳本（不部署、不進課程）。用法：uv run --script content/llm-apps/_spikes/<檔>.py
# 換模型：先改 spike_model_probe.py 的 M 與 spike_rag.py／spike_capstone.py 的 LLM，跑一遍，
# 再把數字更新到 notebook／page_content.py。
import time, asyncio, json
from collections import Counter
from urllib.parse import urlparse
from openai import OpenAI, AsyncOpenAI
BASE_URL = "https://litellm.itsmygo.uk/v1"; API_KEY = "sk-FiIRnuzLH7ypgf29LTpHNw"
client = OpenAI(base_url=BASE_URL, api_key=API_KEY)
models = sorted(m.id for m in client.models.list()); print(len(models), models)
# chat
t0=time.perf_counter()
r = client.chat.completions.create(model="gpt-oss-120b", messages=[{"role":"user","content":"用一句話介紹你自己，說明你是什麼模型。"}], max_tokens=512)
print("chat:", repr(r.choices[0].message.content[:120]), r.model, r.usage, f"{time.perf_counter()-t0:.1f}s")
# small max_tokens reasoning trap
r = client.chat.completions.create(model="gpt-oss-120b", messages=[{"role":"user","content":"1+1=?"}], max_tokens=20)
print("max_tokens=20 ->", repr(r.choices[0].message.content), r.choices[0].finish_reason, r.usage)
# stream
t0=time.perf_counter(); first=None; n=0
for ch in client.chat.completions.create(model="gpt-oss-120b", messages=[{"role":"user","content":"用三句話介紹台北"}], max_tokens=512, stream=True):
    if ch.choices and ch.choices[0].delta.content:
        n+=1; first = first or time.perf_counter()-t0
print(f"stream chunks={n} first={first:.2f}s total={time.perf_counter()-t0:.1f}s")
# embeddings
e = client.embeddings.create(model="qwen3-embedding-0.6b", input=["貓咪喜歡曬太陽", "小貓在窗邊打盹", "今天股市大跌"])
import numpy as np
V = np.array([d.embedding for d in e.data]); print("emb dims", V.shape, "norms", np.linalg.norm(V,axis=1).round(3))
print("cos 0-1", float(V[0]@V[1]/np.linalg.norm(V[0])/np.linalg.norm(V[1])), "cos 0-2", float(V[0]@V[2]/np.linalg.norm(V[0])/np.linalg.norm(V[2])))
e2 = client.embeddings.create(model="nemotron-3-embed-1b", input="hello"); print("nemotron dims", len(e2.data[0].embedding))
# batch + rotation
aclient = AsyncOpenAI(base_url=BASE_URL, api_key=API_KEY)
async def one(i):
    t0=time.perf_counter()
    raw = await aclient.chat.completions.with_raw_response.create(model="free-chat", messages=[{"role":"user","content":f"只回一個數字：{i}+{i}=?"}], max_tokens=512)
    host = urlparse(raw.headers.get("x-litellm-model-api-base","")).netloc
    return host, raw.parse().model, time.perf_counter()-t0, dict((k,v) for k,v in raw.headers.items() if k.startswith("x-litellm"))
async def main():
    t0=time.perf_counter(); res = await asyncio.gather(*(one(i) for i in range(1,11))); wall=time.perf_counter()-t0
    for h,m,dt,hd in res: print(f"  {dt:5.1f}s host={h!r} model={m!r}")
    print("wall", round(wall,1), "sum", round(sum(r[2] for r in res),1)); print(res[0][3])
asyncio.run(main())
