# RAG：讓模型先翻手冊再回答（繁體中文小範例）
# 不需要 GPU——molab 免費 CPU 環境即可全程執行（需要網路：embedding 與生成都經 LiteLLM gateway）。
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "marimo",
#     "qdrant-client>=1.12",
#     "openai>=2.0",
#     "matplotlib",
# ]
# ///
import marimo

__generated_with = "0.23.16"
app = marimo.App(width="medium", app_title="RAG：讓模型先翻手冊再回答")


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    # 📚 RAG：讓模型先翻手冊再回答

    LLM 什麼都懂一點，唯獨**不懂你的資料**——你家公司的規定、你店裡的貓叫什麼名字。
    問它，它不會說「不知道」，它會**自信地編一個**。

    **RAG**（Retrieval-Augmented Generation，檢索增強生成）的解法很樸素：
    回答之前，先從你的資料裡**找出最相關的幾段**，貼進提示詞裡，再請模型「只根據這些回答」。
    它不是微調、不改模型，只是把「翻書」這個步驟接在「回答」前面。

    這份 notebook 用一份虛構的繁體中文文件——「山茶屋貓咪咖啡廳店務手冊」——
    走完 RAG 的每一步，而且每一步都**量化**：

    1. 先看問題：沒有 RAG 的模型怎麼瞎掰
    2. 切段（chunking）：手冊變成 10 個段落
    3. 向量化＋入庫：`qwen3-embedding-0.6b` → Qdrant（記憶體模式）
    4. 檢索：一個問題找回最相關的 3 段
    5. 生成：把段落貼進提示詞，請模型只根據資料回答
    6. 小評測：7 題有標準答案的問題，沒 RAG vs 有 RAG 各答對幾題
    7. 範圍外的問題：好的 RAG 要會說「手冊裡沒有寫」

    從第一格往下全部執行即可（首次安裝套件約 1 分鐘）。
    """
    )
    return


@app.cell
def _():
    import html

    import marimo as mo
    import matplotlib
    from openai import OpenAI
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, PointStruct, VectorParams

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    return Distance, OpenAI, PointStruct, QdrantClient, VectorParams, html, mo, plt


@app.cell
def _(OpenAI):
    client = OpenAI(
        base_url="https://litellm.itsmygo.uk/v1",   # 公開端點
        api_key="sk-FiIRnuzLH7ypgf29LTpHNw",        # 教學用 virtual key（只開免費模型，課後撤銷）
    )
    EMBED_MODEL = "qwen3-embedding-0.6b"   # 1024 維
    CHAT_MODEL = "nemotron-3.5-lightning"  # 30B-A3B 輕量推理型，兩個來源備援
    return CHAT_MODEL, EMBED_MODEL, client


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 1️⃣ 先看問題：沒有 RAG 的模型怎麼回答

    「山茶屋貓咪咖啡廳」是本課虛構的店，世界上任何模型都不可能知道它的 Wi-Fi 密碼。
    問問看——注意它**不會說不知道**。
    """
    )
    return


@app.cell
def _(CHAT_MODEL, client, mo):
    _r = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=[
            {"role": "system", "content": "你是山茶屋貓咪咖啡廳的店員。用繁體中文簡短回答顧客問題。"},
            {"role": "user", "content": "Wi-Fi 密碼是多少？"},
        ],
        max_tokens=4096,
    )
    naive_answer = _r.choices[0].message.content.strip()
    mo.callout(mo.md(f"**沒有 RAG 的回答**：{naive_answer}"), kind="danger")
    return (naive_answer,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 2️⃣ 語料與切段（chunking）

    這是我們的「知識」：一份 Markdown 手冊，十個小節。RAG 的第一個設計決策是**怎麼切**——
    切太大，一段塞進提示詞會帶進太多無關內容；切太小，一句話離開上下文就沒意義。
    這份手冊結構乾淨，就用最自然的切法：**一個 `##` 小標 = 一段**。
    """
    )
    return


@app.cell
def _():
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
    return (HANDBOOK,)


@app.cell
def _(HANDBOOK, mo):
    def chunk_by_heading(text: str) -> list[dict]:
        """以 '## ' 小標切段：每段 = {"title": 小標, "text": 小標＋內文}。"""
        _chunks = []
        for _block in text.split("\n## ")[1:]:          # [0] 是 # 大標，不算一段
            _lines = [ln.strip() for ln in _block.strip().splitlines()]
            _chunks.append({"title": _lines[0], "text": "## " + "\n".join(_lines)})
        return _chunks

    chunks = chunk_by_heading(HANDBOOK)
    mo.vstack([
        mo.md(f"切出 **{len(chunks)} 段**，每段 {min(len(c['text']) for c in chunks)}–{max(len(c['text']) for c in chunks)} 字："),
        mo.ui.table([{"#": i, "title": c["title"], "chars": len(c["text"]), "text": c["text"][len(c["title"]) + 4:][:60] + "…"}
                     for i, c in enumerate(chunks)], selection=None),
    ])
    return chunk_by_heading, chunks


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 3️⃣ 向量化＋入庫

    每一段丟給 embedding 模型變成 1024 維向量（**一次 API 呼叫批次處理**，`input` 給整個 list），
    存進記憶體 Qdrant。payload 放原文與標題——檢索回來要貼進提示詞的是**文字**，向量只是索引。
    """
    )
    return


@app.cell
def _(Distance, EMBED_MODEL, PointStruct, QdrantClient, VectorParams, chunks, client, mo):
    def embed(texts: list[str]) -> list[list[float]]:
        _resp = client.embeddings.create(model=EMBED_MODEL, input=texts)
        return [d.embedding for d in _resp.data]

    chunk_vectors = embed([c["text"] for c in chunks])

    qdrant = QdrantClient(":memory:")
    qdrant.create_collection("handbook", vectors_config=VectorParams(size=len(chunk_vectors[0]), distance=Distance.COSINE))
    qdrant.upsert("handbook", points=[
        PointStruct(id=i, vector=vec, payload=chunks[i]) for i, vec in enumerate(chunk_vectors)
    ])
    mo.md(f"**{qdrant.count('handbook').count} 段** × **{len(chunk_vectors[0])} 維**，已入庫 `handbook`。")
    return chunk_vectors, embed, qdrant


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 4️⃣ 檢索：一個問題找回最相關的幾段

    問題也要經過**同一個** embedding 模型變成向量，再問 Qdrant 最近的 `top_k` 段。
    看 score：命中的那段通常明顯高於其他段，這個「落差」就是檢索有沒有抓對的訊號。
    換幾個問題試試——也試試一個手冊裡根本沒有的問題（例如「有賣牛排嗎」），看分數怎麼塌。
    """
    )
    return


@app.cell
def _(embed, qdrant):
    def retrieve(question: str, top_k: int = 3):
        """回傳 Qdrant 的命中點（含 score 與 payload）。"""
        return qdrant.query_points("handbook", query=embed([question])[0], limit=top_k).points
    return (retrieve,)


@app.cell
def _(mo):
    q_input = mo.ui.text(value="哪一隻貓最怕生？", label="問題", full_width=True)
    k_input = mo.ui.slider(1, 5, value=3, label="top_k", show_value=True)
    mo.hstack([q_input, k_input], widths=[3, 1])
    return k_input, q_input


@app.cell
def _(k_input, mo, q_input, retrieve):
    mo.stop(not q_input.value.strip(), mo.md("_輸入一個問題。_"))
    retrieved = retrieve(q_input.value, k_input.value)
    mo.ui.table([{"rank": i + 1, "score": round(h.score, 3), "title": h.payload["title"],
                  "text": h.payload["text"][len(h.payload["title"]) + 4:][:70] + "…"} for i, h in enumerate(retrieved)],
                selection=None)
    return (retrieved,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 5️⃣ 生成：把段落貼進提示詞

    把檢索到的段落編號後放進 system prompt，並下三條規矩：**只根據參考資料**、
    **沒有就說「手冊裡沒有寫」**、**不要編造**。這三句話是 RAG 提示詞的精髓——
    少了它們，模型會把參考資料和自己的想像混著講。

    下面 `answer()` 可以切換有沒有 RAG，方便對照。
    """
    )
    return


@app.cell
def _(CHAT_MODEL, client, retrieve):
    SYSTEM_RAG = (
        "你是山茶屋貓咪咖啡廳的店員。只能根據下面的「參考資料」回答顧客問題，"
        "資料裡沒有的就說「手冊裡沒有寫」，不要編造。用繁體中文簡短回答。\n\n參考資料：\n{context}"
    )
    SYSTEM_PLAIN = "你是山茶屋貓咪咖啡廳的店員。用繁體中文簡短回答顧客問題。"

    def answer(question: str, use_rag: bool = True, top_k: int = 3):
        """回傳 (回答, 用到的段落)。"""
        _hits = retrieve(question, top_k) if use_rag else []
        if use_rag:
            _context = "\n\n".join(f"[{i + 1}] {h.payload['text']}" for i, h in enumerate(_hits))
            _system = SYSTEM_RAG.format(context=_context)
        else:
            _system = SYSTEM_PLAIN
        _r = client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[{"role": "system", "content": _system}, {"role": "user", "content": question}],
            max_tokens=4096,
        )
        return _r.choices[0].message.content.strip(), _hits
    return SYSTEM_PLAIN, SYSTEM_RAG, answer


@app.cell
def _(answer, html, mo, q_input):
    mo.stop(not q_input.value.strip())
    _plain, _ = answer(q_input.value, use_rag=False)
    _rag, _hits = answer(q_input.value, use_rag=True)

    def _card(title, body, color):
        return (f"<div style='flex:1;min-width:240px;border:2px solid {color};border-radius:12px;padding:12px 14px'>"
                f"<div style='font-weight:800;color:{color};margin-bottom:6px'>{title}</div>"
                f"<div style='white-space:pre-wrap;line-height:1.7'>{html.escape(body)}</div></div>")

    mo.Html(
        "<div style='display:flex;gap:12px;flex-wrap:wrap'>"
        + _card("沒有 RAG", _plain, "#C44E52")
        + _card("有 RAG（參考：" + "、".join(h.payload["title"] for h in _hits) + "）", _rag, "#55A868")
        + "</div>"
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 6️⃣ 小評測：數字說話

    一個例子不算證據。準備 7 題**有標準答案**的問題，每題用一個關鍵字判斷答對與否
    （答案裡有沒有出現它），沒 RAG 與有 RAG 各跑一輪。這種「關鍵字命中」是最陽春的 RAG 評測，
    但它便宜、客觀、改一行就能重跑——每次動了切段方式、`top_k`、提示詞，都該重跑一次。
    """
    )
    return


@app.cell
def _(answer, mo):
    EVAL_SET = [   # (問題, 答案裡應該出現的關鍵字)
        ("山茶屋週日幾點打烊？", "21:00"),
        ("Wi-Fi 密碼是多少？", "meow2026"),
        ("哪一隻貓最怕生？", "煤球"),
        ("我可以帶我家的狗一起來嗎？", "禁止"),
        ("會員集滿幾點可以換拿鐵？", "10"),
        ("領養一隻貓要多少錢？", "1500"),
        ("貓咪讀書會什麼時候？", "第一個週六"),
    ]
    eval_rows = []
    for _q, _gold in EVAL_SET:
        _a0, _ = answer(_q, use_rag=False)
        _a1, _hits = answer(_q, use_rag=True)
        eval_rows.append({
            "問題": _q, "關鍵字": _gold,
            "沒 RAG": ("✅ " if _gold in _a0 else "❌ ") + _a0[:40].replace("\n", " "),
            "有 RAG": ("✅ " if _gold in _a1 else "❌ ") + _a1[:40].replace("\n", " "),
            "top-1 段落": f"{_hits[0].payload['title']} ({_hits[0].score:.2f})",
        })
    score_plain = sum(r["沒 RAG"].startswith("✅") for r in eval_rows)
    score_rag = sum(r["有 RAG"].startswith("✅") for r in eval_rows)
    mo.vstack([
        mo.md(f"沒 RAG **{score_plain}／{len(EVAL_SET)}**，有 RAG **{score_rag}／{len(EVAL_SET)}**。"),
        mo.ui.table(eval_rows, selection=None),
    ])
    return EVAL_SET, eval_rows, score_plain, score_rag


@app.cell
def _(EVAL_SET, plt, score_plain, score_rag):
    _fig, _ax = plt.subplots(figsize=(5.5, 3.2))
    _bars = _ax.bar(["without RAG", "with RAG"], [score_plain, score_rag], color=["#C44E52", "#55A868"], width=0.55)
    for _b in _bars:
        _ax.text(_b.get_x() + _b.get_width() / 2, _b.get_height() + 0.1, f"{int(_b.get_height())}/{len(EVAL_SET)}",
                 ha="center", fontweight="bold")
    _ax.set_ylim(0, len(EVAL_SET) + 1)
    _ax.set_ylabel("correct answers")
    _ax.set_title("Same model, same questions: retrieval is the difference")
    _ax.spines[["top", "right"]].set_visible(False)
    _fig.tight_layout()
    _fig
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 7️⃣ 範圍外的問題：會說「不知道」才是好 RAG

    RAG 最被低估的價值不是「答對」，是「**知道自己不知道**」。問一個手冊裡完全沒有的問題：
    檢索一樣會回來 3 段（它永遠回最近的，哪怕都不相關——看 score 全部偏低），
    但提示詞裡的規矩讓模型老實說沒寫，而不是拿不相關的段落硬湊。
    """
    )
    return


@app.cell
def _(answer, mo):
    _q = "你們有賣牛排嗎？"
    _a, _hits = answer(_q)
    mo.md(
        f"""
    **問**：{_q}

    **檢索回來的段落**（注意分數）：{"、".join(f"{h.payload['title']}（{h.score:.2f}）" for h in _hits)}

    **答**：{_a}
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 🏆 延伸挑戰

    1. **LEVEL 1**：把 4️⃣ 的 `top_k` 改成 1 再跑 6️⃣ 的評測——7 題還全對嗎？哪一題最先出錯、為什麼？
       再把 `top_k` 改成 5 看看會不會因為雜訊太多而變差。
    2. **LEVEL 2**：在 2️⃣ 的 `HANDBOOK` 加一個新小節（例如「外送服務」），**不改其他程式**重跑——
       新知識立刻可用，這就是 RAG 相對微調的最大優勢。然後在 `EVAL_SET` 加一題對應的問題驗證。
    3. **LEVEL 3**：把 5️⃣ 的 system prompt 裡「手冊裡沒有寫」那句刪掉，重跑 7️⃣ 的牛排問題——
       模型會怎麼答？再試著在 `answer()` 加一個門檻：top-1 分數低於某值就直接回「手冊裡沒有寫」，
       不送模型（省一次呼叫）。用 6️⃣ 的評測找出不會誤殺正常問題的門檻。

    帶得走：下載本檔後 `uvx marimo edit --sandbox rag-zh_ext.py` 在自己電腦繼續玩。
    下一課是壓軸：把這套 RAG 包成 **FastMCP 工具**，讓模型**自己決定**什麼時候該翻手冊。
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    # 挑戰的折疊解答：先自己做再打開。LEVEL 1/2 是可直接貼進新 cell 的完整程式碼，LEVEL 3 給方向與驗證方法。
    mo.accordion(
        {
            "💡 LEVEL 1 參考解答：top_k 掃描": mo.md(
                r"""
    不用動拉桿——`answer()` 本來就吃 `top_k` 參數。把 6️⃣ 的評測包成函式，三個 k 各跑一輪（約 21 次呼叫，要等 2–5 分鐘）：

    ```python
    def eval_topk(k):
        _hits_ok = 0
        _wrong = []
        for _q, _gold in EVAL_SET:
            _a, _hits = answer(_q, use_rag=True, top_k=k)
            if _gold in _a:
                _hits_ok += 1
            else:
                _wrong.append(_q)
        return {"top_k": k, "correct": f"{_hits_ok}/{len(EVAL_SET)}", "wrong": "、".join(_wrong) or "—"}

    mo.ui.table([eval_topk(k) for k in (1, 3, 5)], selection=None)
    ```

    你應該看到（實測，nemotron-3.5-lightning，跑了兩輪）：**`top_k=1` 也是 7/7，`top_k=5` 也是 7/7**——跟題目暗示的不一樣。
    原因是這 7 題每一題的答案都只在**一個**小節裡，而 top-1 每次都命中對的那節（分數 0.46–0.79）。
    要看到 `top_k` 的差別，要問**橫跨兩節**的問題，例如「我週二中午想去，順便停車，要注意什麼？」：
    實測 `top_k=1` 只撈到「交通與停車」，答案漏掉週二公休；`top_k=2` 第二名是「入場規定」，還是沒有；
    **`top_k=3` 才把「營業時間」撈進來**，回答同時講到公休與饒河停車場。把這題加進 `EVAL_SET`（關鍵字 `公休`）再跑一次掃描，
    你就會看到 1／3／5 的差別。`top_k=5` 沒有變差，因為 7 題都短、多塞兩段雜訊模型還扛得住——但段落一長、模型一小，雜訊就會開始稀釋答案。

    順便注意一個細節：有一輪「哪一隻貓最怕生」的回答開頭是 `Here's a thinking process:`——推理型模型偶爾會把思考漏進 `content`，
    而我們的關鍵字評測只看「煤球」有沒有出現，照樣判 ✅。**關鍵字評測便宜但粗**，這就是它的代價。
    """
            ),
            "💡 LEVEL 2 參考解答：加一節「外送服務」": mo.md(
                r"""
    直接在 2️⃣ 的 `HANDBOOK` 字串最後面加一節（跟其他小節一樣用 `## ` 開頭）：

    ```markdown
    ## 外送服務
    山茶屋與喵喵外送平台合作，外送範圍為店面周邊 3 公里，滿 350 元免運費，未滿則酌收 40 元運費。外送時段為 11:30 到 19:30，貓咪造型餅乾因易碎不提供外送。
    ```

    存檔後 marimo 自動重跑 3️⃣（切成 11 段、重新 embedding、重建 collection）、4️⃣、6️⃣——**沒有改任何程式**。
    然後在 6️⃣ 的 `EVAL_SET` 加一題 `("外送滿多少免運？", "350")`。

    你應該看到：新題 top-1 是「外送服務」（分數約 0.50），回答「消費滿 350 元即可免運」；原本 7 題照樣全對，變 8/8。
    對照：加小節**之前**問同一題，top-1 是不相干的「會員制度」(0.42)，模型答「手冊裡沒有寫」。
    這就是 RAG 相對微調的最大優勢——知識更新＝改一段文字重建索引，幾秒鐘；微調要重訓、重部署、還可能忘掉舊東西。
    """
            ),
            "💡 LEVEL 3 提示：規矩拿掉會怎樣、門檻怎麼訂": mo.md(
                r"""
    **第一步**：複製 5️⃣ 的 `SYSTEM_RAG` 成 `SYSTEM_LOOSE`，拿掉「資料裡沒有的就說「手冊裡沒有寫」，不要編造」那句，
    用它問牛排。實測（nemotron-3.5-lightning）它還是說沒有牛排，但開始**自己加料**：「菜單主要提供飲品和少量貓友好點心」、
    「每人最低消費一杯飲品，但菜單中未列有牛排」——手冊從頭到尾沒提過菜單內容，這些是它從「咖啡廳」腦補的。
    少了那句規矩，模型會把參考資料和常識混著講，而且講得很像真的。

    **第二步**：在送模型之前先看分數。先量兩組數字：

    ```python
    _in = [retrieve(q, 1)[0].score for q, _ in EVAL_SET]
    _out = [retrieve(q, 1)[0].score for q in ["你們有賣牛排嗎？", "今天台北天氣如何？", "推薦一部科幻電影", "怎麼煮義大利麵？"]]
    mo.md(f"範圍內 top-1 最低 **{min(_in):.2f}**，範圍外 top-1 最高 **{max(_out):.2f}**")
    ```

    實測範圍內最低 0.46（帶狗那題）、範圍外最高 0.37（牛排）——中間有一條縫，門檻訂在 **0.40–0.45** 兩邊都不誤判；
    訂 0.5 就會誤殺「我可以帶狗來嗎」。然後在 `answer()` 的 `_hits = retrieve(...)` 之後加：

    ```python
    if use_rag and _hits[0].score < 0.4:
        return "手冊裡沒有寫", _hits          # 不送模型，省一次呼叫
    ```

    怎麼驗證：6️⃣ 的評測仍是 7/7（沒有誤殺），7️⃣ 的牛排題秒回「手冊裡沒有寫」、耗時從幾秒變 0。
    門檻是**資料＋embedding 模型專屬**的數字：換手冊、換模型都要重量一次，不能抄。
    """
            ),
        }
    )
    return


if __name__ == "__main__":
    app.run()
