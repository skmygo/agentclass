# /// script
# requires-python = ">=3.11"
# dependencies = ["openai>=2.0", "qdrant-client>=1.12", "fastmcp==4.0.0b1", "fastmcp-slim==4.0.0b1", "httpx", "uvicorn", "numpy"]
# ///
# 六門課「🏆 延伸挑戰」折疊解答的實測腳本（不部署、不進課程）。
# 用法：uv run --script content/llm-apps/_spikes/spike_solutions.py [--lesson <id>] [--repeat N]
#   id ∈ litellm-basics | litellm-tools | fastmcp4 | qdrant-basics | rag-zh | rag-mcp-agent（不給就全跑）
# 每題 LEVEL 1/2 的解答程式碼在這裡「真的跑一遍」，LLM 題預設跑 2 次看變異；
# 換模型時改 LLM 常數重跑，再把 notebook 解答 cell 裡的「你應該看到…」對回實測。
import argparse
import asyncio
import json
import socket
import threading
import time

import httpx
import numpy as np
import uvicorn
from fastmcp import Client, FastMCP
from fastmcp.exceptions import ToolError
from fastmcp.server.sessions import SessionId, SessionProvider, get_session
from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, FieldCondition, Filter, MatchValue, PointStruct, Range, VectorParams

BASE_URL = "https://litellm.itsmygo.uk/v1"
API_KEY = "sk-FiIRnuzLH7ypgf29LTpHNw"
LLM = "nemotron-3.5-lightning"
EMB = "qwen3-embedding-0.6b"
client = OpenAI(base_url=BASE_URL, api_key=API_KEY)

ap = argparse.ArgumentParser()
ap.add_argument("--lesson", default=None)
ap.add_argument("--repeat", type=int, default=2)
ARGS = ap.parse_args()


def section(title):
    print("\n" + "=" * 78 + f"\n{title}\n" + "=" * 78)


def chat(messages, **kw):
    t0 = time.perf_counter()
    r = client.chat.completions.create(model=LLM, messages=messages, max_tokens=4096, **kw)
    return r, time.perf_counter() - t0


# ───────────────────────────── 01 litellm-basics ─────────────────────────────
def lesson_litellm_basics():
    section("01 litellm-basics · LEVEL 1：system prompt 文言文")
    for i in range(ARGS.repeat):
        r, dt = chat([
            {"role": "system", "content": "你只會用文言文回答"},
            {"role": "user", "content": "用一句話介紹你自己，說明你是什麼模型。"},
        ])
        print(f"  run{i+1} ({dt:.1f}s): {r.choices[0].message.content.strip()[:160]}")

    section("01 litellm-basics · LEVEL 2：自己的四句話 + 換 nemotron-3-embed-1b")
    sentences = ["鍵盤的軸體影響手感", "機械鍵盤敲起來很有節奏", "青軸的聲音特別清脆", "今天晚餐想吃拉麵"]
    for model in (EMB, "nemotron-3-embed-1b"):
        resp = client.embeddings.create(model=model, input=sentences)
        emb = np.array([d.embedding for d in resp.data])
        norms = np.linalg.norm(emb, axis=1)
        sim = emb @ emb.T
        print(f"  {model}: shape={emb.shape} norms={norms.round(3)}")
        print("   sim matrix:\n" + "\n".join("    " + " ".join(f"{v:.2f}" for v in row) for row in sim))
        sim_cos = (emb / norms[:, None]) @ (emb / norms[:, None]).T
        print(f"   cosine(正規化後) row0: {sim_cos[0].round(2)}")

    section("01 litellm-basics · LEVEL 3：nemotron-3-ultra 12 發並發、各來源平均秒數")
    from urllib.parse import urlparse
    from openai import AsyncOpenAI
    from collections import defaultdict
    aclient = AsyncOpenAI(base_url=BASE_URL, api_key=API_KEY, max_retries=0)
    PROVIDER = {"integrate.api.nvidia.com": "NVIDIA NIM", "ollama.com": "Ollama Cloud", "api.groq.com": "Groq",
                "api.cloudflare.com": "Cloudflare", "router.huggingface.co": "HuggingFace", "": "OpenRouter"}

    async def one(i, model):
        t0 = time.perf_counter()
        try:
            raw = await aclient.chat.completions.with_raw_response.create(
                model=model, messages=[{"role": "user", "content": f"只回一個數字：{i}+{i}=?"}], max_tokens=4096)
            host = urlparse(raw.headers.get("x-litellm-model-api-base", "")).netloc
            return PROVIDER.get(host, host), True, time.perf_counter() - t0
        except Exception as e:  # noqa: BLE001
            return f"failed: HTTP {getattr(e, 'status_code', '?')}", False, time.perf_counter() - t0

    async def batch(model, n=12):
        t0 = time.perf_counter()
        rows = await asyncio.gather(*(one(i, model) for i in range(1, n + 1)))
        return rows, time.perf_counter() - t0

    for model in ("nemotron-3-ultra",):
        rows, wall = asyncio.run(batch(model))
        by = defaultdict(list)
        for p, ok, sec in rows:
            by[p].append(sec)
        print(f"  {model}: wall={wall:.1f}s ok={sum(ok for _, ok, _ in rows)}/12")
        for p, secs in sorted(by.items(), key=lambda kv: np.mean(kv[1])):
            print(f"    {p:18s} n={len(secs):2d} mean={np.mean(secs):5.1f}s  min={min(secs):5.1f}  max={max(secs):5.1f}  std={np.std(secs):4.1f}")


# ───────────────────────────── 02 litellm-tools ─────────────────────────────
def lesson_litellm_tools():
    def get_weather(city: str) -> dict:
        FAKE = {"台北": {"weather": "晴", "temp_c": 31}, "高雄": {"weather": "多雲", "temp_c": 33}}
        ALIAS = {"taipei": "台北", "kaohsiung": "高雄"}
        return FAKE.get(ALIAS.get(city.strip().lower(), city), {"weather": "未知城市", "temp_c": None})

    TOOLS = [{"type": "function", "function": {"name": "get_weather", "description": "查詢指定城市的即時天氣",
              "parameters": {"type": "object", "properties": {"city": {"type": "string", "description": "城市名，例如：台北"}},
                             "required": ["city"]}}}]

    section("02 litellm-tools · LEVEL 1：第二個工具 convert_currency")

    def convert_currency(amount: float, from_currency: str, to_currency: str) -> dict:
        RATE = {("USD", "TWD"): 32.5, ("TWD", "USD"): 1 / 32.5, ("JPY", "TWD"): 0.21, ("TWD", "JPY"): 1 / 0.21}
        rate = RATE.get((from_currency.upper(), to_currency.upper()))
        if rate is None:
            return {"error": f"不支援 {from_currency}->{to_currency}"}
        return {"amount": amount, "from": from_currency.upper(), "to": to_currency.upper(), "result": round(amount * rate, 2), "rate": rate}

    TOOLS2 = TOOLS + [{"type": "function", "function": {
        "name": "convert_currency", "description": "匯率換算：把某個金額從一種貨幣換成另一種貨幣",
        "parameters": {"type": "object", "properties": {
            "amount": {"type": "number", "description": "金額"},
            "from_currency": {"type": "string", "description": "原幣別代碼，例如 USD"},
            "to_currency": {"type": "string", "description": "目標幣別代碼，例如 TWD"}},
            "required": ["amount", "from_currency", "to_currency"]}}}]
    AVAILABLE = {"get_weather": get_weather, "convert_currency": convert_currency}

    def run_with_tools(question, tools, avail, max_rounds=5, feed_errors=False):
        msgs = [{"role": "user", "content": question}]
        trace = []
        for _ in range(max_rounds):
            r, _dt = chat(msgs, tools=tools)
            m = r.choices[0].message
            if not m.tool_calls:
                return (m.content or "").strip(), trace
            msgs.append({"role": "assistant", "content": m.content or "",
                         "tool_calls": [{"id": tc.id, "type": "function",
                                         "function": {"name": tc.function.name, "arguments": tc.function.arguments}} for tc in m.tool_calls]})
            for tc in m.tool_calls:
                args = json.loads(tc.function.arguments or "{}")
                if feed_errors:
                    try:
                        out = avail[tc.function.name](**args)
                    except Exception as e:  # noqa: BLE001
                        out = {"error": f"{type(e).__name__}: {e}"}
                else:
                    out = avail[tc.function.name](**args)
                trace.append((tc.function.name, args, out))
                msgs.append({"role": "tool", "tool_call_id": tc.id, "content": json.dumps(out, ensure_ascii=False)})
        return "（超過回合上限）", trace

    for i in range(ARGS.repeat):
        for q in ["100 美元換台幣多少？", "台北現在天氣怎麼樣？"]:
            ans, tr = run_with_tools(q, TOOLS2, AVAILABLE)
            print(f"  run{i+1} Q={q} → calls={[(n, a) for n, a, _ in tr]} ans={ans[:80]!r}")

    section("02 litellm-tools · LEVEL 2：age 加 min/max、多一個原文沒有的 email（strict）")
    PROMPT = [{"role": "user", "content": "小明今年12歲，住在台北，喜歡籃球跟圍棋。請抽取人物資料。"}]
    RF = {"type": "json_schema", "json_schema": {"name": "person_info", "strict": True, "schema": {
        "type": "object", "properties": {
            "name": {"type": "string"}, "age": {"type": "integer", "minimum": 0, "maximum": 150},
            "city": {"type": "string"}, "hobbies": {"type": "array", "items": {"type": "string"}},
            "email": {"type": "string"}},
        "required": ["name", "age", "city", "hobbies", "email"], "additionalProperties": False}}}
    for i in range(ARGS.repeat + 1):
        r, dt = chat(PROMPT, response_format=RF)
        raw = (r.choices[0].message.content or "").strip()
        try:
            d = json.loads(raw)
            print(f"  run{i+1} ({dt:.1f}s) email={d.get('email')!r} age={d.get('age')!r} full={json.dumps(d, ensure_ascii=False)[:120]}")
        except Exception:  # noqa: BLE001
            print(f"  run{i+1} ({dt:.1f}s) 非 JSON: {raw[:120]!r}")
    RF_NULL = json.loads(json.dumps(RF))
    RF_NULL["json_schema"]["schema"]["properties"]["email"] = {"type": ["string", "null"]}
    r, dt = chat(PROMPT, response_format=RF_NULL)
    print(f"  email 允許 null 版 ({dt:.1f}s): {(r.choices[0].message.content or '').strip()[:140]}")

    section("02 litellm-tools · LEVEL 3：工具出錯把錯誤餵回去")

    def get_weather_strict(city: str) -> dict:
        FAKE = {"台北": {"weather": "晴", "temp_c": 31}, "高雄": {"weather": "多雲", "temp_c": 33}}
        ALIAS = {"taipei": "台北", "kaohsiung": "高雄"}
        key = ALIAS.get(city.strip().lower(), city)
        if key not in FAKE:
            raise KeyError(f"查無城市「{city}」，目前只支援：{list(FAKE)}")
        return FAKE[key]

    for i in range(ARGS.repeat):
        ans, tr = run_with_tools("東京現在天氣怎麼樣？", TOOLS, {"get_weather": get_weather_strict}, feed_errors=True)
        print(f"  run{i+1}: calls={[(n, a, str(o)[:60]) for n, a, o in tr]}\n        ans={ans[:160]!r}")


# ───────────────────────────── 03 fastmcp4 ─────────────────────────────
def lesson_fastmcp4():
    mcp = FastMCP("茶飲店")
    MENU = [{"name": "珍珠奶茶", "price": 60}, {"name": "紅茶", "price": 30}, {"name": "綠茶拿鐵", "price": 70}, {"name": "滷肉飯", "price": 45}]

    @mcp.tool
    def add(a: int, b: int) -> int:
        """把兩個整數相加。"""
        return a + b

    @mcp.tool
    def search_menu(keyword: str, limit: int = 3) -> list[dict]:
        """依關鍵字搜尋菜單，回傳最多 limit 筆品項（含價格）。"""
        return [m for m in MENU if keyword in m["name"]][:limit]

    @mcp.resource("menu://today")
    def today_menu() -> str:
        """今日完整菜單（純文字）"""
        return " / ".join(f"{m['name']} {m['price']}" for m in MENU)

    section("03 fastmcp4 · LEVEL 1：place_order(item, qty=1)")

    @mcp.tool
    def place_order(item: str, qty: int = 1) -> dict:
        """下單：指定品項與數量，回傳訂單摘要（含小計）。"""
        hit = next((m for m in MENU if m["name"] == item), None)
        if hit is None:
            raise ToolError(f"菜單上沒有「{item}」")
        return {"item": item, "qty": qty, "subtotal": hit["price"] * qty}

    async def l1():
        async with Client(mcp) as c:
            tools = {t.name: t for t in await c.list_tools()}
            print("  tools:", sorted(tools))
            print("  place_order schema:", json.dumps(tools["place_order"].input_schema, ensure_ascii=False))
            print("  call:", (await c.call_tool("place_order", {"item": "紅茶", "qty": 2})).data)
            try:
                await c.call_tool("place_order", {"item": "牛排"})
            except ToolError as e:
                print("  ToolError:", str(e)[:80])
    asyncio.run(l1())

    section("03 fastmcp4 · LEVEL 2：checkout(session_id)")
    mcp.add_provider(SessionProvider())

    @mcp.tool
    async def add_to_cart(session_id: SessionId, item: str) -> list[str]:
        """加進購物車"""
        s = await get_session(session_id)
        items = await s.get("items", default=[])
        items.append(item)
        await s.set("items", items)
        return items

    @mcp.tool
    async def checkout(session_id: SessionId) -> dict:
        """結帳：算總價（查 MENU）、清空購物車、回傳收據。"""
        s = await get_session(session_id)
        items = await s.get("items", default=[])
        price = {m["name"]: m["price"] for m in MENU}
        lines = [{"item": it, "price": price.get(it, 0)} for it in items]
        await s.set("items", [])
        return {"lines": lines, "total": sum(ln["price"] for ln in lines), "count": len(lines)}

    async def l2():
        async with Client(mcp) as c:
            key = (await c.call_tool("create_session")).data
            for it in ["紅茶", "滷肉飯", "珍珠奶茶"]:
                await c.call_tool("add_to_cart", {"session_id": key, "item": it})
            receipt = (await c.call_tool("checkout", {"session_id": key})).data
            print("  receipt:", receipt)
            print("  checkout again (empty):", (await c.call_tool("checkout", {"session_id": key})).data)
    asyncio.run(l2())

    section("03 fastmcp4 · LEVEL 3：裸 POST tools/list 與 resources/read")
    PORT = 8767
    URL = f"http://127.0.0.1:{PORT}/mcp"

    def busy():
        with socket.socket() as s:
            return s.connect_ex(("127.0.0.1", PORT)) == 0

    if not busy():
        srv = uvicorn.Server(uvicorn.Config(mcp.http_app(), host="127.0.0.1", port=PORT, log_level="warning"))
        threading.Thread(target=srv.run, daemon=True).start()
        for _ in range(50):
            if busy():
                break
            time.sleep(0.1)
    META = {"io.modelcontextprotocol/protocolVersion": "2026-07-28", "io.modelcontextprotocol/clientCapabilities": {}}
    H = {"Accept": "application/json, text/event-stream", "Content-Type": "application/json", "MCP-Protocol-Version": "2026-07-28"}
    r = httpx.post(URL, json={"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {"_meta": META}}, headers={**H, "mcp-method": "tools/list"})
    print("  tools/list:", r.status_code, [t["name"] for t in r.json().get("result", {}).get("tools", [])] if r.status_code == 200 else r.text[:200])
    for extra in ({"mcp-method": "resources/read"}, {"mcp-method": "resources/read", "mcp-name": "menu://today"}, {"mcp-method": "resources/read", "mcp-uri": "menu://today"}):
        r = httpx.post(URL, json={"jsonrpc": "2.0", "id": 2, "method": "resources/read", "params": {"uri": "menu://today", "_meta": META}}, headers={**H, **extra})
        print(f"  resources/read headers={extra}: {r.status_code} {r.text[:200]}")
    r = httpx.post(URL, json={"jsonrpc": "2.0", "id": 3, "method": "resources/read", "params": {"uri": "menu://today"}}, headers={**H, "mcp-method": "resources/read"})
    print("  resources/read 沒 _meta:", r.status_code, r.text[:160])
    r = httpx.post(URL, json={"jsonrpc": "2.0", "id": 4, "method": "resources/read", "params": {"uri": "menu://today", "_meta": META}}, headers={**H, "mcp-method": "tools/call"})
    print("  resources/read 但 mcp-method 寫錯:", r.status_code, r.text[:160])


# ───────────────────────────── 04 qdrant-basics ─────────────────────────────
def lesson_qdrant_basics():
    DISHES = [("珍珠奶茶", [0.90, 0.10, 0.00], "drink", 60), ("檸檬紅茶", [0.50, 0.80, 0.00], "drink", 45),
              ("蜂蜜檸檬", [0.80, 0.60, 0.00], "drink", 55), ("焦糖布丁", [0.95, 0.05, 0.00], "dessert", 80),
              ("糖醋排骨", [0.70, 0.60, 0.10], "food", 180), ("泰式酸辣湯", [0.20, 0.80, 0.70], "food", 120),
              ("酸辣粉", [0.10, 0.70, 0.80], "food", 90), ("麻辣鍋", [0.10, 0.20, 0.95], "food", 350)]
    qdrant = QdrantClient(":memory:")
    qdrant.create_collection("dishes", vectors_config=VectorParams(size=3, distance=Distance.COSINE))
    qdrant.upsert("dishes", points=[PointStruct(id=i, vector=v, payload={"name": n, "kind": k, "price": p}) for i, (n, v, k, p) in enumerate(DISHES)])

    section("04 qdrant-basics · LEVEL 1：加兩道菜")
    NEW = [("芒果冰", [0.85, 0.30, 0.00], "dessert", 120), ("宮保雞丁", [0.30, 0.20, 0.75], "food", 160)]
    qdrant.upsert("dishes", points=[PointStruct(id=8 + i, vector=v, payload={"name": n, "kind": k, "price": p}) for i, (n, v, k, p) in enumerate(NEW)])
    print("  count:", qdrant.count("dishes").count)
    for q in ([0.85, 0.3, 0.0], [0.3, 0.2, 0.8], [0.2, 0.7, 0.9]):
        hits = qdrant.query_points("dishes", query=q, limit=3).points
        print(f"  query {q}: " + " → ".join(f"{h.payload['name']}({h.score:.3f})" for h in hits))

    section("04 qdrant-basics · LEVEL 2：must / should / must_not")
    sweet = [0.9, 0.1, 0.0]
    f_must = Filter(must=[FieldCondition(key="kind", match=MatchValue(value="food")), FieldCondition(key="price", range=Range(lte=150))])
    f_should = Filter(should=[FieldCondition(key="kind", match=MatchValue(value="drink")), FieldCondition(key="kind", match=MatchValue(value="dessert"))])
    f_not = Filter(must_not=[FieldCondition(key="kind", match=MatchValue(value="food"))])
    for label, f in (("must food&<=150", f_must), ("should drink|dessert", f_should), ("must_not food", f_not)):
        hits = qdrant.query_points("dishes", query=sweet, limit=3, query_filter=f).points
        print(f"  {label:22s}: " + " → ".join(f"{h.payload['name']}({h.score:.3f},{h.payload['kind']},{h.payload['price']})" for h in hits))

    section("04 qdrant-basics · LEVEL 3：dishes_real 帶 kind/price + 過濾；換 embedding 模型會怎樣")

    def embed(texts, model=EMB):
        return [d.embedding for d in client.embeddings.create(model=model, input=texts).data]

    names = [n for n, _, _, _ in DISHES]
    vecs = embed(names)
    qdrant.create_collection("dishes_real", vectors_config=VectorParams(size=len(vecs[0]), distance=Distance.COSINE))
    qdrant.upsert("dishes_real", points=[PointStruct(id=i, vector=v, payload={"name": names[i], "kind": DISHES[i][2], "price": DISHES[i][3]}) for i, v in enumerate(vecs)])
    q = "提神"
    hits = qdrant.query_points("dishes_real", query=embed([q])[0], limit=3,
                               query_filter=Filter(must=[FieldCondition(key="price", range=Range(lte=100))])).points
    print(f"  「{q}」+ price<=100: " + " → ".join(f"{h.payload['name']}({h.score:.2f},{h.payload['price']})" for h in hits))
    hits = qdrant.query_points("dishes_real", query=embed([q])[0], limit=3).points
    print(f"  「{q}」無過濾: " + " → ".join(f"{h.payload['name']}({h.score:.2f},{h.payload['price']})" for h in hits))
    try:
        other = embed([q], model="nemotron-3-embed-1b")[0]
        print(f"  nemotron-3-embed-1b 維度={len(other)}")
        qdrant.query_points("dishes_real", query=other, limit=3)
        print("  （居然沒報錯）")
    except Exception as e:  # noqa: BLE001
        print("  換模型查詢 →", type(e).__name__, str(e)[:160])


# ───────────────────────────── 05 rag-zh ─────────────────────────────
HANDBOOK = """
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
DELIVERY = """
## 外送服務
山茶屋與喵喵外送平台合作，外送範圍為店面周邊 3 公里，滿 350 元免運費，未滿則酌收 40 元運費。外送時段為 11:30 到 19:30，貓咪造型餅乾因易碎不提供外送。
"""
EVAL_SET = [("山茶屋週日幾點打烊？", "21:00"), ("Wi-Fi 密碼是多少？", "meow2026"), ("哪一隻貓最怕生？", "煤球"),
            ("我可以帶我家的狗一起來嗎？", "禁止"), ("會員集滿幾點可以換拿鐵？", "10"), ("領養一隻貓要多少錢？", "1500"),
            ("貓咪讀書會什麼時候？", "第一個週六")]
SYSTEM_RAG = ("你是山茶屋貓咪咖啡廳的店員。只能根據下面的「參考資料」回答顧客問題，"
              "資料裡沒有的就說「手冊裡沒有寫」，不要編造。用繁體中文簡短回答。\n\n參考資料：\n{context}")


def build_kb(text):
    chunks = []
    for block in text.split("\n## ")[1:]:
        lines = [ln.strip() for ln in block.strip().splitlines()]
        chunks.append({"title": lines[0], "text": "## " + "\n".join(lines)})

    def embed(texts):
        return [d.embedding for d in client.embeddings.create(model=EMB, input=texts).data]

    vecs = embed([c["text"] for c in chunks])
    q = QdrantClient(":memory:")
    q.create_collection("handbook", vectors_config=VectorParams(size=len(vecs[0]), distance=Distance.COSINE))
    q.upsert("handbook", points=[PointStruct(id=i, vector=v, payload=chunks[i]) for i, v in enumerate(vecs)])

    def retrieve(question, top_k=3):
        return q.query_points("handbook", query=embed([question])[0], limit=top_k).points

    def answer(question, top_k=3, system=SYSTEM_RAG, min_score=None):
        hits = retrieve(question, top_k)
        if min_score is not None and hits[0].score < min_score:
            return "手冊裡沒有寫（檢索分數過低，未送模型）", hits
        ctx = "\n\n".join(f"[{i+1}] {h.payload['text']}" for i, h in enumerate(hits))
        r, _ = chat([{"role": "system", "content": system.format(context=ctx)}, {"role": "user", "content": question}])
        return r.choices[0].message.content.strip(), hits
    return chunks, embed, retrieve, answer


def lesson_rag_zh():
    chunks, embed, retrieve, answer = build_kb(HANDBOOK)
    section("05 rag-zh · LEVEL 1：top_k = 1 / 3 / 5 的評測")
    for k in (1, 3, 5):
        for rep in range(ARGS.repeat if k != 3 else 1):
            rows = []
            for q, gold in EVAL_SET:
                a, hits = answer(q, top_k=k)
                rows.append((gold in a, q, hits[0].payload["title"], round(hits[0].score, 2), a[:40].replace("\n", " ")))
            print(f"  top_k={k} run{rep+1}: {sum(r[0] for r in rows)}/7  wrong={[r[1] for r in rows if not r[0]]}")
            if k == 1:
                for r in rows:
                    print("     ", r)

    section("05 rag-zh · LEVEL 2：加一節「外送服務」→ 新知識立刻可用")
    chunks2, _, retrieve2, answer2 = build_kb(HANDBOOK + DELIVERY)
    print("  段數:", len(chunks2), "最後一段:", chunks2[-1]["title"])
    for rep in range(ARGS.repeat):
        a, hits = answer2("外送滿多少免運？")
        print(f"  run{rep+1}: top1={hits[0].payload['title']}({hits[0].score:.2f}) 含350={'350' in a} ans={a[:80]!r}")
    a, hits = answer("外送滿多少免運？")
    print(f"  舊手冊同題: top1={hits[0].payload['title']}({hits[0].score:.2f}) ans={a[:80]!r}")

    section("05 rag-zh · LEVEL 3：刪掉「手冊裡沒有寫」規矩 → 牛排；門檻掃描")
    SYSTEM_LOOSE = "你是山茶屋貓咪咖啡廳的店員。根據下面的「參考資料」回答顧客問題。用繁體中文簡短回答。\n\n參考資料：\n{context}"
    for rep in range(ARGS.repeat):
        a, hits = answer("你們有賣牛排嗎？", system=SYSTEM_LOOSE)
        print(f"  loose run{rep+1}: {a[:120]!r}")
    in_scope = [retrieve(q, 1)[0].score for q, _ in EVAL_SET]
    OUT = ["你們有賣牛排嗎？", "今天台北天氣如何？", "推薦一部科幻電影", "怎麼煮義大利麵？", "比特幣現在多少錢？"]
    out_scope = [retrieve(q, 1)[0].score for q in OUT]
    print(f"  in-scope  top1 scores: {[round(s, 2) for s in in_scope]}  min={min(in_scope):.2f}")
    print(f"  out-scope top1 scores: {[round(s, 2) for s in out_scope]}  max={max(out_scope):.2f}")
    for th in (0.3, 0.35, 0.4, 0.45, 0.5):
        fp = sum(s < th for s in in_scope)
        catch = sum(s < th for s in out_scope)
        print(f"   門檻 {th}: 誤殺 in-scope {fp}/7、攔下 out-scope {catch}/{len(OUT)}")


# ───────────────────────────── 06 rag-mcp-agent ─────────────────────────────
def lesson_rag_mcp_agent():
    chunks, embed, retrieve, _ = build_kb(HANDBOOK)

    def make_server(threshold=None, with_get_section=False):
        mcp = FastMCP("山茶屋知識庫", instructions="回答顧客關於山茶屋貓咪咖啡廳的任何問題之前，先用 search_handbook 查手冊。")

        @mcp.tool
        def search_handbook(query: str, top_k: int = 3) -> list[dict] | dict:
            """在山茶屋店務手冊裡做語意搜尋，回傳最相關的段落（含相似度分數 0–1）。
            回答任何關於營業時間、規定、貓咪、會員、停車、活動的問題前都應先呼叫。
            query 請用繁體中文、可以放多個關鍵字（手冊是繁體中文寫的）。"""
            hits = retrieve(query, top_k)
            if threshold is not None and hits[0].score < threshold:
                return {"note": "手冊裡沒有相關內容", "best_score": round(hits[0].score, 3)}
            return [{"title": h.payload["title"], "score": round(h.score, 3), "text": h.payload["text"]} for h in hits]

        @mcp.tool
        def list_sections() -> list[str]:
            """列出手冊的所有章節標題。想知道手冊涵蓋哪些主題時呼叫。"""
            return [c["title"] for c in chunks]

        if with_get_section:
            @mcp.tool
            def get_section(title: str) -> str:
                """依章節標題取回該節的完整原文。當顧客要求「完整唸出／全文／整段」某個章節時呼叫；
                標題要跟 list_sections 回傳的一模一樣。"""
                for c in chunks:
                    if c["title"] == title:
                        return c["text"]
                raise ToolError(f"沒有「{title}」這個章節，可用 list_sections 查看標題")
        return mcp

    SYSTEM_PROMPT = ("你是山茶屋貓咪咖啡廳的客服。遇到店務問題先用工具查手冊，只根據查到的內容回答，"
                     "查不到就說手冊裡沒有寫。用繁體中文簡短回答，並在句尾用（來源：章節名）標注出處。")
    SYSTEM_NO_HINT = ("你是山茶屋貓咪咖啡廳的客服。只根據查到的內容回答，查不到就說手冊裡沒有寫。"
                      "用繁體中文簡短回答，並在句尾用（來源：章節名）標注出處。")

    async def ask(mcp, question, system=SYSTEM_PROMPT, max_steps=6):
        trace = []
        msgs = [{"role": "system", "content": system}, {"role": "user", "content": question}]
        async with Client(mcp) as c:
            tools = [{"type": "function", "function": {"name": t.name, "description": t.description, "parameters": t.input_schema}}
                     for t in await c.list_tools()]
            for step in range(1, max_steps + 1):
                r, dt = chat(msgs, tools=tools)
                m = r.choices[0].message
                if not m.tool_calls:
                    return (m.content or "").strip(), trace
                msgs.append({"role": "assistant", "content": m.content or "",
                             "tool_calls": [{"id": tc.id, "type": "function", "function": {"name": tc.function.name, "arguments": tc.function.arguments}} for tc in m.tool_calls]})
                for tc in m.tool_calls:
                    args = json.loads(tc.function.arguments or "{}")
                    try:
                        out = json.dumps((await c.call_tool(tc.function.name, args)).data, ensure_ascii=False)
                    except Exception as e:  # noqa: BLE001
                        out = f"錯誤：{e}"
                    trace.append((tc.function.name, args, out[:80]))
                    msgs.append({"role": "tool", "tool_call_id": tc.id, "content": out})
        return "（超過步數上限）", trace

    section("06 rag-mcp-agent · LEVEL 1：get_section")
    mcp1 = make_server(with_get_section=True)
    for rep in range(ARGS.repeat):
        a, tr = asyncio.run(ask(mcp1, "把會員制度完整念給我聽"))
        print(f"  run{rep+1}: calls={[(n, g) for n, g, _ in tr]} ans={a[:100]!r}")

    section("06 rag-mcp-agent · LEVEL 2：search_handbook 門檻 0.4")
    mcp2 = make_server(threshold=0.4)
    for rep in range(ARGS.repeat):
        a, tr = asyncio.run(ask(mcp2, "你們有賣牛排嗎？"))
        print(f"  run{rep+1}: calls={[(n, g, o) for n, g, o in tr]} ans={a[:100]!r}")
    a, tr = asyncio.run(ask(mcp2, "哪一隻貓最怕生？"))
    print(f"  對照（正常問題）: calls={[(n, g) for n, g, _ in tr]} ans={a[:80]!r}")

    section("06 rag-mcp-agent · LEVEL 3：system prompt 拿掉「先用工具查手冊」")
    mcp3 = make_server()
    for rep in range(ARGS.repeat):
        for q in ["我週二中午想去，順便停車，要注意什麼？", "你們手冊有哪些章節？", "1+1 等於多少？"]:
            a, tr = asyncio.run(ask(mcp3, q, system=SYSTEM_NO_HINT))
            print(f"  run{rep+1} Q={q[:14]}… calls={[(n, g) for n, g, _ in tr]} ans={a[:70]!r}")


LESSONS = {"litellm-basics": lesson_litellm_basics, "litellm-tools": lesson_litellm_tools, "fastmcp4": lesson_fastmcp4,
           "qdrant-basics": lesson_qdrant_basics, "rag-zh": lesson_rag_zh, "rag-mcp-agent": lesson_rag_mcp_agent}
for name, fn in LESSONS.items():
    if ARGS.lesson in (None, name):
        t0 = time.perf_counter()
        fn()
        print(f"\n[{name} done in {time.perf_counter() - t0:.0f}s]")
