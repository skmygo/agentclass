# /// script
# requires-python = ">=3.11"
# dependencies = ["openai>=2.0", "qdrant-client>=1.12", "fastmcp==4.0.0b1", "fastmcp-slim==4.0.0b1", "httpx", "uvicorn", "numpy", "pillow"]
# ///
# 定軌／換模型時的實測腳本（不部署、不進課程）。用法：uv run --script content/llm-apps/_spikes/<檔>.py
# 換模型：先改 spike_model_probe.py 的 M 與 spike_rag.py／spike_capstone.py 的 LLM，跑一遍，
# 再把數字更新到 notebook／page_content.py。
import numpy as np, time
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct, Filter, FieldCondition, MatchValue, Range
client = QdrantClient(":memory:")
# toy: taste vectors [sweet, sour, spicy]
DISHES = [("珍珠奶茶", [0.9,0.1,0.0],"drink",60),("檸檬紅茶",[0.5,0.8,0.0],"drink",45),("麻辣鍋",[0.1,0.2,0.95],"food",350),
          ("糖醋排骨",[0.7,0.6,0.1],"food",180),("泰式酸辣湯",[0.2,0.8,0.7],"food",120),("焦糖布丁",[0.95,0.05,0.0],"dessert",80),
          ("酸辣粉",[0.1,0.7,0.8],"food",90),("蜂蜜檸檬",[0.8,0.6,0.0],"drink",55)]
client.create_collection("dishes", vectors_config=VectorParams(size=3, distance=Distance.COSINE))
client.upsert("dishes", points=[PointStruct(id=i, vector=v, payload={"name":n,"kind":k,"price":p}) for i,(n,v,k,p) in enumerate(DISHES)])
print("count", client.count("dishes").count)
res = client.query_points("dishes", query=[0.2,0.7,0.9], limit=3)
print("酸辣 query:", [(p.payload["name"], round(p.score,3)) for p in res.points])
res = client.query_points("dishes", query=[0.2,0.7,0.9], limit=3, query_filter=Filter(must=[FieldCondition(key="kind", match=MatchValue(value="drink"))]))
print("酸辣+drink:", [(p.payload["name"], round(p.score,3)) for p in res.points])
res = client.query_points("dishes", query=[0.9,0.1,0.0], limit=3, query_filter=Filter(must=[FieldCondition(key="price", range=Range(lte=100))]))
print("甜+<=100:", [(p.payload["name"], round(p.score,3)) for p in res.points])
# distance compare
for dist in [Distance.COSINE, Distance.EUCLID, Distance.DOT]:
    client.recreate_collection if False else None
    name=f"d_{dist.value}"; client.create_collection(name, vectors_config=VectorParams(size=3, distance=dist))
    client.upsert(name, points=[PointStruct(id=i, vector=v, payload={"name":n}) for i,(n,v,k,p) in enumerate(DISHES)])
    r = client.query_points(name, query=[0.2,0.7,0.9], limit=3); print(dist.value, [(p.payload["name"], round(p.score,3)) for p in r.points])
# scroll/get
print(client.retrieve("dishes", ids=[0,1]))
print(client.scroll("dishes", limit=2)[0])
# real embeddings
from openai import OpenAI
oa = OpenAI(base_url="https://litellm.itsmygo.uk/v1", api_key="sk-FiIRnuzLH7ypgf29LTpHNw")
texts=[n for n,_,_,_ in DISHES]
e = oa.embeddings.create(model="qwen3-embedding-0.6b", input=texts)
client.create_collection("dishes_real", vectors_config=VectorParams(size=1024, distance=Distance.COSINE))
client.upsert("dishes_real", points=[PointStruct(id=i, vector=d.embedding, payload={"name":texts[i]}) for i,d in enumerate(e.data)])
for q in ["想喝冰冰甜甜的飲料", "辣的湯", "飯後甜點"]:
    qv = oa.embeddings.create(model="qwen3-embedding-0.6b", input=q).data[0].embedding
    r = client.query_points("dishes_real", query=qv, limit=3); print(q, "->", [(p.payload["name"], round(p.score,3)) for p in r.points])
