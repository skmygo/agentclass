# /// script
# requires-python = ">=3.11"
# dependencies = ["openai>=2.0", "qdrant-client>=1.12", "fastmcp==4.0.0b1", "fastmcp-slim==4.0.0b1", "httpx", "uvicorn", "numpy", "pillow"]
# ///
# 定軌／換模型時的實測腳本（不部署、不進課程）。用法：uv run --script content/llm-apps/_spikes/<檔>.py
# 換模型：先改 spike_model_probe.py 的 M 與 spike_rag.py／spike_capstone.py 的 LLM，跑一遍，
# 再把數字更新到 notebook／page_content.py。
import time, json, asyncio
from urllib.parse import urlparse
from openai import OpenAI, AsyncOpenAI
oa = OpenAI(base_url="https://litellm.itsmygo.uk/v1", api_key="sk-FiIRnuzLH7ypgf29LTpHNw")
M="nemotron-3.5-lightning"
r = oa.chat.completions.create(model=M, messages=[{"role":"user","content":"用一句話介紹你自己，說明你是什麼模型。"}], max_tokens=512)
print("intro:", repr(r.choices[0].message.content[:100]), r.model, r.usage.completion_tokens, r.usage.completion_tokens_details)
for mt in [20, 64]:
    r = oa.chat.completions.create(model=M, messages=[{"role":"user","content":"1+1=?"}], max_tokens=mt)
    print(f"max_tokens={mt}:", repr(r.choices[0].message.content), r.choices[0].finish_reason, r.usage.completion_tokens, getattr(r.usage.completion_tokens_details,'reasoning_tokens',None) if r.usage.completion_tokens_details else None)
t0=time.perf_counter(); n=0; first=None
for ch in oa.chat.completions.create(model=M, messages=[{"role":"user","content":"用三句話介紹台北。"}], max_tokens=512, stream=True):
    if ch.choices and ch.choices[0].delta.content:
        n+=1; first = first or time.perf_counter()-t0
print(f"stream chunks={n} first={first} total={time.perf_counter()-t0:.1f}")
# batch rotation
ac = AsyncOpenAI(base_url="https://litellm.itsmygo.uk/v1", api_key="sk-FiIRnuzLH7ypgf29LTpHNw", max_retries=0)
async def one(i):
    t0=time.perf_counter()
    try:
        raw = await ac.chat.completions.with_raw_response.create(model=M, messages=[{"role":"user","content":f"只回一個數字：{i}+{i}=?"}], max_tokens=512)
        return urlparse(raw.headers.get("x-litellm-model-api-base","")).netloc, round(time.perf_counter()-t0,1), (raw.parse().choices[0].message.content or '')[:10]
    except Exception as e: return "ERR "+str(e)[:60], round(time.perf_counter()-t0,1), ""
async def main():
    t0=time.perf_counter(); res=await asyncio.gather(*(one(i) for i in range(1,13))); print("wall", round(time.perf_counter()-t0,1), "sum", round(sum(r[1] for r in res),1))
    for r in res: print("  ", r)
asyncio.run(main())
