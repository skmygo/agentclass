# /// script
# requires-python = ">=3.11"
# dependencies = ["openai>=2.0", "qdrant-client>=1.12", "fastmcp==4.0.0b1", "fastmcp-slim==4.0.0b1", "httpx", "uvicorn", "numpy", "pillow"]
# ///
# 定軌／換模型時的實測腳本（不部署、不進課程）。用法：uv run --script content/llm-apps/_spikes/<檔>.py
# 換模型：先改 spike_model_probe.py 的 M 與 spike_rag.py／spike_capstone.py 的 LLM，跑一遍，
# 再把數字更新到 notebook／page_content.py。
import time, json
from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct
oa = OpenAI(base_url="https://litellm.itsmygo.uk/v1", api_key="sk-FiIRnuzLH7ypgf29LTpHNw")
EMB="qwen3-embedding-0.6b"; LLM="nemotron-3.5-lightning"
DOC = """
# 山茶屋貓咪咖啡廳 店務手冊（2026 版）

## 營業時間
山茶屋每週二公休。平日營業時間為 11:00 到 20:30，週末與國定假日為 10:00 到 21:00。最後點餐時間是打烊前 40 分鐘。

## 入場規定
入場低消為每人一杯飲品。為了貓咪的健康，店內禁止攜帶其他寵物入內，也禁止餵食自備食物。12 歲以下兒童需由成人陪同，且每位成人最多陪同兩名兒童。

## Wi-Fi
店內 Wi-Fi 名稱為 CamelliaCat，密碼是 meow2026，連線後請勿下載大型檔案。

## 店貓介紹：麻糬
麻糬是一隻 4 歲的橘貓，個性親人、最愛討摸，喜歡趴在靠窗的第三張桌子曬太陽。牠對雞肉凍乾沒有抵抗力。

## 店貓介紹：煤球
煤球是 2 歲的黑貓，非常怕生，通常躲在吧台後方的貓窩。請不要主動抱牠，牠願意靠近時再輕摸下巴即可。

## 店貓介紹：奶蓋
奶蓋是 6 歲的白色長毛貓，是店裡的大姐頭。牠每天下午三點準時在櫃檯旁等零食，店員會在那時進行「奶蓋點心時間」，歡迎顧客圍觀但請勿觸碰零食。

## 會員制度
消費滿 300 元可免費辦理山茶會員卡。會員每消費 100 元累積 1 點，集滿 10 點可兌換一杯中杯拿鐵或一包貓咪造型餅乾。會員生日當月贈送一份手作甜點。

## 交通與停車
山茶屋位於捷運松山站 4 號出口步行 6 分鐘處。店內沒有附設停車場，建議停在對面的饒河停車場，消費滿 500 元可折抵一小時停車費。

## 貓咪領養
店內的貓咪皆為中途貓，除了麻糬、煤球與奶蓋三隻店貓之外，其餘貓咪都開放認養。認養需填寫申請表並通過 30 分鐘的面談，領養費用為 1500 元，全數捐給流浪動物協會。

## 特殊活動
每月第一個週六晚上 19:00 舉辦「貓咪讀書會」，由店長帶大家讀一本與貓有關的書，參加費用 200 元含一杯飲品，名額 12 人，需提前一週在店內報名。
"""
def chunk_by_heading(text):
    """以 '## ' 小標切段：每一段＝一個小標＋它底下的內文。"""
    chunks = []
    for block in text.split("\n## ")[1:]:
        chunks.append("## " + block.strip())
    return chunks
chunks = chunk_by_heading(DOC); print(len(chunks), "chunks", [len(c) for c in chunks])
t0=time.perf_counter(); e = oa.embeddings.create(model=EMB, input=chunks); print("embed batch", f"{time.perf_counter()-t0:.1f}s", len(e.data), len(e.data[0].embedding), e.usage)
q = QdrantClient(":memory:"); q.create_collection("handbook", vectors_config=VectorParams(size=1024, distance=Distance.COSINE))
q.upsert("handbook", points=[PointStruct(id=i, vector=d.embedding, payload={"text":chunks[i], "title":chunks[i].splitlines()[0].lstrip('# ')}) for i,d in enumerate(e.data)])
def retrieve(question, k=3):
    qv = oa.embeddings.create(model=EMB, input=question).data[0].embedding
    return q.query_points("handbook", query=qv, limit=k).points
def answer(question, use_rag=True):
    msgs=[]
    if use_rag:
        hits = retrieve(question)
        ctx = "\n\n".join(f"[{i+1}] {h.payload['text']}" for i,h in enumerate(hits))
        msgs.append({"role":"system","content":"你是山茶屋貓咪咖啡廳的店員。只能根據下面的「參考資料」回答顧客問題，資料裡沒有的就說「手冊裡沒有寫」，不要編造。用繁體中文簡短回答。\n\n參考資料：\n"+ctx})
    else:
        msgs.append({"role":"system","content":"你是山茶屋貓咪咖啡廳的店員。用繁體中文簡短回答顧客問題。"})
    msgs.append({"role":"user","content":question})
    r = oa.chat.completions.create(model=LLM, messages=msgs, max_tokens=2048)
    return r.choices[0].message.content.strip(), (hits if use_rag else [])
QS=[("山茶屋週日幾點打烊？","21:00"),("Wi-Fi 密碼是多少？","meow2026"),("哪一隻貓最怕生？","煤球"),("我可以帶我家的狗一起來嗎？","禁止"),("會員集滿幾點可以換拿鐵？","10"),("領養一隻貓要多少錢？","1500"),("貓咪讀書會什麼時候？","第一個週六")]
for question, gold in QS:
    a0,_ = answer(question, use_rag=False)
    a1,hits = answer(question, use_rag=True)
    print("\nQ:", question, "| gold:", gold)
    print("  no-RAG:", ("✅" if gold in a0 else "❌"), a0[:90].replace("\n"," "))
    print("  RAG   :", ("✅" if gold in a1 else "❌"), a1[:90].replace("\n"," "), "| hits:", [(h.payload['title'], round(h.score,3)) for h in hits])
# out-of-scope question
a,hits = answer("你們有賣牛排嗎？"); print("\nOOS:", a, [(h.payload['title'], round(h.score,3)) for h in hits])
