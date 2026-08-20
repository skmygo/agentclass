# 壓軸：LiteLLM × FastMCP × Qdrant——RAG 變成 AI 的工具
# 不需要 GPU——molab 免費 CPU 環境即可全程執行（需要網路：embedding 與生成都經 LiteLLM gateway）。
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "marimo",
#     "fastmcp==4.0.0b1",
#     "fastmcp-slim==4.0.0b1",
#     "qdrant-client>=1.12",
#     "openai>=2.0",
# ]
# ///
import marimo

__generated_with = "0.23.16"
app = marimo.App(width="medium", app_title="壓軸：RAG 變成 AI 的工具")


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    # 🏁 壓軸：LiteLLM × FastMCP × Qdrant——RAG 變成 AI 的工具

    前五課的零件全部到齊，這一課把它們組成一台會「自己翻手冊」的客服：

    ```
    顧客提問 ──▶ LLM（經 LiteLLM gateway）
                   │  「這題我得查手冊」→ 發出 tool call
                   ▼
               Agent 迴圈 ──▶ MCP Client ──▶ FastMCP 伺服器 ──▶ search_handbook()
                   ▲                                              │  embedding + Qdrant 檢索
                   └────────── 檢索到的段落（tool 結果）◀──────────┘
                   │
                   ▼  「根據查到的內容……」→ 最終回答（附來源）
    ```

    跟上一課的差別只有一個，但很關鍵：上一課是**我們**決定每題都先檢索；
    這一課把檢索包成 MCP 工具，**模型自己決定**要不要查、查什麼關鍵字、查幾段——
    問「1+1」它不查（雖然回答有點太「守規矩」），問「週二想去順便停車」它一次查到兩個章節。

    1. 知識庫就緒（上一課的手冊、切段、向量化、Qdrant，濃縮成一格）
    2. 把檢索包成 FastMCP 工具：`search_handbook`、`list_sections`
    3. 橋接：MCP 的工具說明書 → OpenAI tools 格式
    4. Agent 迴圈：模型呼叫工具、我們轉給 MCP、結果餵回去，直到它給出答案
    5. 觀察它的決策：什麼時候查、什麼時候不查、怎麼合併多個來源
    6. 上線：同一台伺服器怎麼給 Claude Code / Claude Desktop 用

    從第一格往下全部執行即可（首次安裝套件約 1 分鐘）。
    """
    )
    return


@app.cell
def _():
    import html
    import json
    import time

    import marimo as mo
    from fastmcp import Client, FastMCP
    from openai import OpenAI
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, PointStruct, VectorParams
    return (
        Client,
        Distance,
        FastMCP,
        OpenAI,
        PointStruct,
        QdrantClient,
        VectorParams,
        html,
        json,
        mo,
        time,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 1️⃣ 知識庫就緒

    上一課的四個步驟——手冊、切段、批次 embedding、寫進記憶體 Qdrant——濃縮成一格。
    唯一的新東西是把 `embed()` 與 `retrieve()` 準備好給下一節的工具用。
    """
    )
    return


@app.cell
def _(Distance, OpenAI, PointStruct, QdrantClient, VectorParams, mo):
    client = OpenAI(
        base_url="https://litellm.itsmygo.uk/v1",   # 公開端點
        api_key="sk-FiIRnuzLH7ypgf29LTpHNw",        # 教學用 virtual key（只開免費模型，課後撤銷）
    )
    EMBED_MODEL = "qwen3-embedding-0.6b"
    CHAT_MODEL = "nemotron-3-ultra"   # 本系列預設；推理型，每一步可能要等幾秒到幾十秒

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

    chunks = []
    for _block in HANDBOOK.split("\n## ")[1:]:
        _lines = [ln.strip() for ln in _block.strip().splitlines()]
        chunks.append({"title": _lines[0], "text": "## " + "\n".join(_lines)})

    def embed(texts):
        return [d.embedding for d in client.embeddings.create(model=EMBED_MODEL, input=texts).data]

    qdrant = QdrantClient(":memory:")
    _vectors = embed([c["text"] for c in chunks])
    qdrant.create_collection("handbook", vectors_config=VectorParams(size=len(_vectors[0]), distance=Distance.COSINE))
    qdrant.upsert("handbook", points=[PointStruct(id=i, vector=v, payload=chunks[i]) for i, v in enumerate(_vectors)])

    def retrieve(question, top_k=3):
        return qdrant.query_points("handbook", query=embed([question])[0], limit=top_k).points

    mo.md(f"知識庫就緒：**{qdrant.count('handbook').count} 段 × {len(_vectors[0])} 維**")
    return CHAT_MODEL, EMBED_MODEL, HANDBOOK, chunks, client, embed, qdrant, retrieve


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 2️⃣ 把檢索包成 FastMCP 工具

    兩個工具：

    - `search_handbook(query, top_k)`：語意搜尋，回傳段落＋分數。
    - `list_sections()`：列出所有章節標題（讓模型知道手冊涵蓋什麼）。

    **docstring 就是給模型看的使用說明**——寫清楚「什麼情況該呼叫」，模型的決策品質差很多。
    `FastMCP(..., instructions=...)` 則是整台伺服器的使用說明，客戶端可以拿去當 system prompt 的一部分。
    """
    )
    return


@app.cell
def _(FastMCP, chunks, retrieve):
    mcp = FastMCP(
        "山茶屋知識庫",
        instructions="回答顧客關於山茶屋貓咪咖啡廳的任何問題之前，先用 search_handbook 查手冊。",
    )

    @mcp.tool
    def search_handbook(query: str, top_k: int = 3) -> list[dict]:
        """在山茶屋店務手冊裡做語意搜尋，回傳最相關的段落（含相似度分數 0–1）。
        回答任何關於營業時間、規定、貓咪、會員、停車、活動的問題前都應先呼叫。"""
        return [{"title": h.payload["title"], "score": round(h.score, 3), "text": h.payload["text"]}
                for h in retrieve(query, top_k)]

    @mcp.tool
    def list_sections() -> list[str]:
        """列出手冊的所有章節標題。想知道手冊涵蓋哪些主題時呼叫。"""
        return [c["title"] for c in chunks]
    return list_sections, mcp, search_handbook


@app.cell
async def _(Client, json, list_sections, mcp, mo, search_handbook):
    _ = (search_handbook, list_sections)
    async with Client(mcp) as _c:
        mcp_tools = await _c.list_tools()
        _demo = await _c.call_tool("search_handbook", {"query": "停車", "top_k": 1})
    mo.vstack([
        mo.md(f"`{mcp.name}` 有 {len(mcp_tools)} 個工具，FastMCP 自動生成的說明書："),
        *[mo.md(f"**`{t.name}`** — {t.description}\n\n```json\n{json.dumps(t.input_schema, ensure_ascii=False)}\n```") for t in mcp_tools],
        mo.md(f"先手動呼叫一次確認能動：`search_handbook(\"停車\", top_k=1)` → `{_demo.data}`"),
    ])
    return (mcp_tools,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 3️⃣ 橋接：MCP 說明書 → OpenAI tools 格式

    第 2 課你手寫 tools 的 JSON；第 3 課 FastMCP 幫你生成了 `input_schema`。
    兩者格式幾乎一樣，只差一層包裝——三行就能把 MCP 的工具清單轉成 `chat.completions` 要的 `tools`。
    這座橋讓**任何** MCP 伺服器的工具都能給**任何** OpenAI 相容的模型用。
    """
    )
    return


@app.cell
def _(json, mcp_tools, mo):
    def mcp_to_openai_tools(tools):
        return [{"type": "function",
                 "function": {"name": t.name, "description": t.description, "parameters": t.input_schema}}
                for t in tools]

    openai_tools = mcp_to_openai_tools(mcp_tools)
    mo.md("轉換後的第一個工具：\n\n```json\n" + json.dumps(openai_tools[0], ensure_ascii=False, indent=2) + "\n```")
    return mcp_to_openai_tools, openai_tools


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 4️⃣ Agent 迴圈

    第 2 課的 `run_with_tools` 加一個改動：工具不再是本地 dict 裡的函式，
    而是透過 MCP Client 呼叫（`await c.call_tool(name, args)`）。其餘一樣——
    模型要求工具 → 執行 → 結果以 `role: "tool"` 餵回 → 再問，直到它給純文字答案。

    兩個實務細節：

    - **工具出錯要餵回去**，不要讓例外炸掉迴圈：把錯誤訊息當 tool 結果給模型，它會自我修正。
    - 每一步都記進 `trace`，這是你 debug agent 唯一的眼睛。
    """
    )
    return


@app.cell
def _(CHAT_MODEL, Client, client, json, mcp, openai_tools, time):
    SYSTEM_PROMPT = (
        "你是山茶屋貓咪咖啡廳的客服。遇到店務問題先用工具查手冊，只根據查到的內容回答，"
        "查不到就說手冊裡沒有寫。用繁體中文簡短回答，並在句尾用（來源：章節名）標注出處。"
    )

    async def ask_agent(question: str, max_steps: int = 6):
        """回傳 (最終回答, trace)。trace 每筆是 dict：step / kind / 內容。"""
        _trace = []
        _msgs = [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": question}]
        async with Client(mcp) as _c:
            for _step in range(1, max_steps + 1):
                _t0 = time.perf_counter()
                _r = client.chat.completions.create(model=CHAT_MODEL, messages=_msgs, tools=openai_tools, max_tokens=800)
                _m = _r.choices[0].message
                if not _m.tool_calls:
                    _trace.append({"step": _step, "kind": "answer", "detail": (_m.content or "").strip(),
                                   "sec": round(time.perf_counter() - _t0, 1)})
                    return (_m.content or "").strip(), _trace
                _msgs.append({"role": "assistant", "content": _m.content or "",
                              "tool_calls": [{"id": tc.id, "type": "function",
                                              "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                                             for tc in _m.tool_calls]})
                for tc in _m.tool_calls:
                    _args = json.loads(tc.function.arguments or "{}")
                    try:
                        _res = await _c.call_tool(tc.function.name, _args)      # ← 轉給 MCP 伺服器
                        _out = json.dumps(_res.data, ensure_ascii=False)
                    except Exception as _e:  # noqa: BLE001  工具錯誤要餵回模型，不能炸掉迴圈
                        _out = f"錯誤：{_e}"
                    _trace.append({"step": _step, "kind": f"tool → {tc.function.name}", "args": _args,
                                   "detail": _out, "sec": round(time.perf_counter() - _t0, 1)})
                    _msgs.append({"role": "tool", "tool_call_id": tc.id, "content": _out})
        return "（超過步數上限）", _trace
    return SYSTEM_PROMPT, ask_agent


@app.cell
def _(html, mo):
    def render_trace(question, answer, trace):
        """把 agent 的每一步畫成時間軸卡片。"""
        _COLOR = {"answer": "#55A868"}
        _parts = [f"<div style='font-weight:800;margin-bottom:8px'>🙋 {html.escape(question)}</div>"]
        for _t in trace:
            _color = _COLOR.get(_t["kind"], "#4C72B0")
            _head = f"step {_t['step']} · {_t['kind']}" + (f" {html.escape(str(_t.get('args')))}" if _t.get("args") else "") + f" · {_t['sec']}s"
            _body = html.escape(_t["detail"][:260] + ("…" if len(_t["detail"]) > 260 else ""))
            _parts.append(
                f"<div style='border-left:4px solid {_color};padding:6px 12px;margin:6px 0;background:#F0F4EE;border-radius:0 8px 8px 0'>"
                f"<div style='font-size:12px;color:{_color};font-weight:800'>{_head}</div>"
                f"<div style='white-space:pre-wrap;font-size:13.5px;line-height:1.6'>{_body}</div></div>"
            )
        return mo.Html("<div style='margin:10px 0 18px'>" + "".join(_parts) + "</div>")
    return (render_trace,)


@app.cell
async def _(ask_agent, render_trace):
    first_q = "煤球是什麼樣的貓？可以抱牠嗎？"
    first_answer, first_trace = await ask_agent(first_q)
    render_trace(first_q, first_answer, first_trace)
    return first_answer, first_q, first_trace


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 5️⃣ 觀察它的決策

    同一個 agent 丟三種問題：

    - **需要合併兩個章節**的問題（週二公休 + 停車）——看它查一次還是兩次、答案有沒有兩個來源。
    - **問手冊結構**的問題——它應該改用 `list_sections` 而不是語意搜尋。
    - **跟店務無關**的問題——它應該**不呼叫任何工具**。實測 `nemotron-3-ultra` 確實沒查手冊，
      但回答是「手冊裡沒有寫基本數學運算」——它把 system prompt 的「查不到就說沒寫」套用過頭了。
      這是提示詞要調的地方，也是 LEVEL 3 挑戰的起點。

    `top_k` 的值也值得注意：說明書裡預設是 3，但模型有時會自己決定給 5。
    """
    )
    return


@app.cell
async def _(ask_agent, mo, render_trace):
    _qs = ["我週二中午想去，順便停車，要注意什麼？", "你們手冊有哪些章節？", "1+1 等於多少？"]
    _blocks = []
    for _q in _qs:
        _a, _tr = await ask_agent(_q)
        _blocks.append(render_trace(_q, _a, _tr))
    mo.vstack(_blocks)
    return


@app.cell
def _(mo):
    agent_q = mo.ui.text(value="會員生日有什麼優惠？另外麻糬喜歡吃什麼？", label="換你問客服", full_width=True)
    agent_btn = mo.ui.run_button(label="問")
    mo.hstack([agent_q, agent_btn], widths=[4, 0.6])
    return agent_btn, agent_q


@app.cell
async def _(agent_btn, agent_q, ask_agent, mo, render_trace):
    mo.stop(not agent_btn.value, mo.md("_輸入問題後按「問」。_"))
    _a, _tr = await ask_agent(agent_q.value)
    render_trace(agent_q.value, _a, _tr)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 6️⃣ 上線：同一台伺服器給真的 AI 客戶端用

    本 notebook 的 agent 迴圈是「自己寫客戶端」的路線。另一條路線更省事：
    把 1️⃣ 與 2️⃣ 存成 `server.py`，結尾加

    ```python
    if __name__ == "__main__":
        mcp.run(transport="http", host="0.0.0.0", port=8000)
    ```

    跑起來後 `claude mcp add --transport http shancha http://localhost:8000/mcp`，
    Claude Code 就會看到 `search_handbook` 與 `list_sections`，問它山茶屋的事它會自己查——
    **不用寫任何 agent 迴圈**，因為客戶端本身就是 agent。

    第 3 課學到的無狀態協定在這裡兌現：這台伺服器每個請求自帶一切，
    你可以跑 3 個副本放在負載平衡器後面，Qdrant 換成正式伺服器（`QdrantClient("http://qdrant:6333")`）
    讓副本共用同一份索引——程式碼其他地方一個字都不用改。

    ## 🏆 延伸挑戰

    1. **LEVEL 1**：在 2️⃣ 加第三個工具 `get_section(title: str) -> str`（回傳整段原文），
       問「把會員制度完整念給我聽」——模型會改用它嗎？說明書的措辭會影響它的選擇。
    2. **LEVEL 2**：把 `search_handbook` 加一個門檻：最高分低於 0.4 時回傳
       `{"note": "手冊裡沒有相關內容"}` 而不是硬湊三段。問「有賣牛排嗎」驗證模型會老實說沒有。
    3. **LEVEL 3**：把 4️⃣ 的 `SYSTEM_PROMPT` 裡「先用工具查手冊」那句刪掉，重跑 5️⃣ 的三個問題——
       模型還會主動查嗎？比較 `mcp.instructions`（伺服器方的說明）與 system prompt（客戶端方的說明）
       誰該負責「提醒模型用工具」，想一想在 Claude Code 那條路線上你能控制哪一個。

    帶得走：下載本檔後 `uvx marimo edit --sandbox rag-mcp-agent_ext.py` 在自己電腦繼續玩。
    六堂課到此完結：一個網址一把 key（LiteLLM）、讓模型做事（tool calling）、
    把函式變工具（FastMCP）、最像什麼（Qdrant）、先翻書再回答（RAG）、然後把它們接成一台會自己查資料的客服。
    """
    )
    return


if __name__ == "__main__":
    app.run()
