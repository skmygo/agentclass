import marimo

__generated_with = "0.23.16"
app = marimo.App(width="medium", app_title="RAG 與向量資料庫：先查再答（實驗場）")


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    # 🧪 RAG 與向量資料庫：先查再答（實驗場）

    這是本課的**實驗場**。左側教學讀到哪，就回到這裡動手做——
    每個實驗都有**滑桿與選項**可以拉，拉完右邊立刻重算——
    所有數字都是當場算出來的，不是預錄的畫面。

    這一課的素材全是**真的**：一份虛構咖啡機手冊的 12 段文字、
    它們的真向量（embedding 模型 jina-embed 算的 1024 維，打包進課程）、
    以及模型「查手冊前 vs 查手冊後」的真實回答紀錄（qwen3.5-2b，temp=0，2026-08）。
    """
    )
    return


@app.cell
def _():
    import marimo as mo
    return (mo,)


@app.cell
def _():
    # 科學套件集中在這格 import，回傳給全 notebook 用
    import html as html_mod

    import matplotlib.pyplot as plt
    import numpy as np
    return html_mod, np, plt


@app.cell
def _(np):
    import base64

    # ── 虛構「拿鐵大師 LM-500」手冊 12 段 ＋ 4 個問題（與左頁、hero 同一份素材）──
    RAG_CHUNKS = [
        "首次使用：第一次使用前，請先執行兩次空水循環——水箱裝滿冷水、不放咖啡粉，按沖煮鍵讓水流完，以清除管線中的製造殘留。",
        "研磨粗細：LM-500 適用中細研磨度。咖啡粉研磨過細會導致過度萃取、流速變慢，嚴重時觸發防堵塞保護而自動停機。",
        "除垢：除垢燈亮起時，將一包除垢劑與 1 公升清水混合倒入水箱，長按沖煮鍵 5 秒進入除垢模式，全程約 20 分鐘，結束後再跑一次清水循環。",
        "水箱：容量 1.2 公升，可整個拆下清洗；建議每天更換新鮮冷水，不要使用溫水或礦泉水。",
        "保固：本產品自購買日起提供 2 年保固。人為損壞、摔落，以及因未定期除垢造成的水垢堵塞，不在保固範圍內。",
        "奶泡：打奶泡請使用冷藏（約 4°C）鮮奶，奶量不超過鋼杯一半；蒸氣管使用後立即以濕布擦拭並空噴一秒。",
        "日常清潔：沖煮頭每週以溫水沖洗一次，滴水盤與粉渣盒每天清空；機身以擰乾的濕布擦拭，切勿整機沖水。",
        "無法啟動：若機器完全沒有反應，請先確認電源線兩端插緊、插座有電，再檢查機身右側的過熱保護開關是否跳起（按下即復位）。",
        "咖啡豆保存：開封後請裝入不透光密封罐，置於陰涼處，並在兩週內使用完畢；不建議冷凍保存。",
        "沖煮溫度：預設 92°C，可在設定選單中以 1°C 為單位調整（範圍 88–96°C）；溫度越高萃取越強，苦味也越明顯。",
        "自動待機：機器閒置 30 分鐘後自動進入省電待機，按任意鍵喚醒；喚醒後約 40 秒完成預熱。",
        "運轉噪音：內建磨豆機運轉時瞬間噪音約 70 分貝，屬正常現象；若出現金屬摩擦異音，請立即停機檢查豆槽異物。",
    ]
    RAG_QUERIES = [
        "咖啡機第一次使用前要做什麼？",
        "除垢燈亮了該怎麼處理？",
        "咖啡粉磨太細會發生什麼事？",
        "保固期多久？哪些情況不保固？",
    ]

    # 真向量（jina-embed 1024 維，int8 對稱量化打包；已驗證 top-3 排序與 fp32 完全一致）
    RAG_DOC_B64 = "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"
    RAG_DOC_SCALES = [0.000858851, 0.000827314, 0.00112774, 0.00116172, 0.00141103, 0.00102863, 0.000995724, 0.00100769, 0.00132985, 0.0012193, 0.00116325, 0.00108687]
    RAG_Q_B64 = "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"
    RAG_Q_SCALES = [0.000978391, 0.00118615, 0.000982262, 0.00143973]

    def _unpack(b64, scales, n):
        q = np.frombuffer(base64.b64decode(b64), dtype=np.int8).reshape(n, 1024)
        v = q.astype(np.float32) * np.array(scales, dtype=np.float32)[:, None]
        return v / np.linalg.norm(v, axis=1, keepdims=True)

    DOC_N = _unpack(RAG_DOC_B64, RAG_DOC_SCALES, len(RAG_CHUNKS))
    Q_N = _unpack(RAG_Q_B64, RAG_Q_SCALES, len(RAG_QUERIES))
    return DOC_N, Q_N, RAG_CHUNKS, RAG_QUERIES


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 1️⃣ 檢索：整個 RAG 的「查」就是這幾行

    RAG（Retrieval-Augmented Generation）＝**先檢索、再生成**。
    「檢索」聽起來高深，數學上只有一步：**問題的向量和每一段文件的向量算 cosine，
    取最像的前幾名**——跟第 1 課你玩過的最近鄰一模一樣。

    選一個問題，看它對 12 段手冊的相似度怎麼排（向量是真的，cosine 是現場算的）：
    """
    )
    return


@app.cell
def _(RAG_QUERIES, mo):
    q_pick = mo.ui.dropdown(options=RAG_QUERIES, value=RAG_QUERIES[0], label="使用者的問題")
    top_k = mo.ui.slider(start=1, stop=5, step=1, value=3, label="取前幾段（top-k）", show_value=True)
    mo.vstack([q_pick, top_k])
    return q_pick, top_k


@app.cell
def _(DOC_N, Q_N, RAG_QUERIES, np, plt, q_pick, top_k):
    _qi = RAG_QUERIES.index(q_pick.value)
    _sims = DOC_N @ Q_N[_qi]
    _order = np.argsort(-_sims)
    _topk = {int(i) for i in _order[: top_k.value]}
    _labels = [f"chunk {_i+1}" for _i in range(len(_sims))]
    _colors = ["#55A868" if _i in _topk else "#C9D2D8" for _i in range(len(_sims))]
    _fig, _ax = plt.subplots(figsize=(7.0, 4.4))
    _ax.barh(_labels, _sims, color=_colors, edgecolor="#1C2B33", linewidth=1.0, zorder=3)
    _ax.invert_yaxis()
    _ax.set_xlabel("cosine similarity to the question")
    _ax.set_title(f"retrieval: green = top-{top_k.value} chunks handed to the model")
    _ax.grid(axis="x", alpha=0.3)
    _fig.tight_layout()
    _fig
    return


@app.cell
def _(DOC_N, Q_N, RAG_CHUNKS, RAG_QUERIES, mo, np, q_pick, top_k):
    _qi = RAG_QUERIES.index(q_pick.value)
    _sims = DOC_N @ Q_N[_qi]
    _order = np.argsort(-_sims)[: top_k.value]
    _rows = "\n".join(
        f"    {_rank+1}. （cosine {_sims[_i]:.3f}）{RAG_CHUNKS[_i][:38]}…"
        for _rank, _i in enumerate(int(_x) for _x in _order)
    )
    mo.md(
        f"""
    **檢索結果（top-{top_k.value}）：**

{_rows}

    第一名幾乎總是拉開第二名一段距離（0.6～0.7 vs 0.4～0.5）——
    這就是「檢索有信心」的樣子。把 top-k 拉到 5 再看：後面幾名的相似度
    掉到 0.3 左右，其實已經跟問題沒什麼關係，塞進去只是雜訊。
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 2️⃣ 對照：查手冊前 vs 查手冊後

    下面是**真實紀錄**（qwen3.5-2b，temperature=0，2026-08）：同一個模型、同一個問題，
    唯一的差別是有沒有把檢索到的 top-3 段落塞進 prompt。
    """
    )
    return


@app.cell
def _():
    # 實測紀錄（qwen3.5-2b，temp=0，2026-08）：bare＝無 RAG，rag＝附 top-3 段落
    RAG_TRACES = [
        {
            "q": "咖啡機第一次使用前要做什麼？",
            "bare": "你好！我是「拿鐵大師 LM-500」的客服。歡迎來到我的專屬世界！🌟\n\n在第一次使用前，為了確保您的 LM-500 能發揮最佳性能並延長機器壽命，請務必按照以下步驟進行**「首次啟動與初始化」**：\n\n### 1. 準備清潔與維護液\n*   **檢查液體**：請確認您的咖啡機內已裝滿符合 LM-500 規格的高品質咖啡液體（建議使用專用的「拿鐵大師」專用液體，或符合標準的純水/咖啡液）。\n*   **檢查濾網**：請確保濾網已正確安裝，且濾網孔無堵塞。\n\n### 2. 首次加水與加粉\n*   **加水**：將咖啡機內的水箱加滿水（請參考機身說明書確認水位線）。\n*   **加粉**：將咖啡粉倒入粉碗，並放入濾網。請確保粉量適中，不要過滿。（後略）",
            "rag": "根據手冊段落【段落 1】，咖啡機首次使用前，請先執行兩次空水循環：水箱裝滿冷水、不放咖啡粉，按沖煮鍵讓水流完，以清除管線中的製造殘留。",
        },
        {
            "q": "除垢燈亮了該怎麼處理？",
            "bare": "你好！我是「拿鐵大師 LM-500」的客服 LM-500。看到你的除垢燈亮起，別擔心（中略）\n\n### 1. 準備除垢液\n*   **材料**：你需要準備一杯**除垢液**（通常由白醋或檸檬酸與水按 1:1 比例混合，或者使用專門的咖啡機除垢劑）。\n\n### 2. 執行除垢程序\n*   **關機**：請先將咖啡機完全關機，並拔掉電源線。\n*   **加入除垢液**：將除垢液倒入咖啡機內部的**水箱**中。\n*   **等待**：讓除垢程序運行。通常這需要 **15 到 30 分鐘**（視除垢液濃度和機型而定）。（後略）",
            "rag": "根據手冊段落【段落 3】，除垢燈亮起時，請將一包除垢劑與 1 公升清水混合倒入水箱，然後長按沖煮鍵 5 秒進入除垢模式。全程約需 20 分鐘，除垢結束後，請再跑一次清水循環。",
        },
        {
            "q": "咖啡粉磨太細會發生什麼事？",
            "bare": "你好！我是「拿鐵大師 LM-500」的客服。我很樂意為你解答關於咖啡粉研磨度的問題。\n\n當咖啡粉被磨得太細時：\n\n1.  **萃取過濃（Over-extraction）**\n    這是磨粉太細最常見的問題。細粉比粗粉有更大的比表面积，意味著咖啡粉與水接觸的接觸面積更大。結果就是咖啡液體顏色過深、味道苦澀（中略）\n\n4.  **研磨機負擔加重**\n    對於 LM-500 這樣的研磨機來說，過細的粉粒會增加研磨負荷，導致研磨時間變長，甚至可能因為粉粒過細而堵塞研磨刀頭或溢粉。（後略）",
            "rag": "根據手冊段落【段落 2】，咖啡粉研磨過細會導致**過度萃取**，且**流速變慢**。若情況嚴重，可能會觸發防堵塞保護而**自動停機**。",
        },
        {
            "q": "保固期多久？哪些情況不保固？",
            "bare": "您好！我是「拿鐵大師 LM-500」的專屬客服 LM-500。\n\n### 1. 保固期多久？\n根據我們與您的合約，**「拿鐵大師 LM-500」的保固期為 2 年**。\n*   若發生非人為因素（如電源斷電、水質過鹹、使用不當）造成的損壞，我們將提供免費維修或更換零件服務。\n\n### 2. 哪些情況不保固？\n*   **人為損壞**：例如自行拆卸、修改內部結構（中略）\n*   **自然老化**：例如濾網因長期使用而變黑、密封圈因老化而鬆動（需自行更換）。\n*   **外部損傷**：例如機身被撞擊、受潮、或受到強光直射。（後略）",
            "rag": "根據手冊段落【段落 5】，本產品自購買日起提供 **2 年保固**。\n\n以下為不保固的情況：\n1. 人為損壞。\n2. 摔落。\n3. 因未定期除垢造成的水垢堵塞。",
        },
    ]
    return (RAG_TRACES,)


@app.cell
def _(RAG_QUERIES, RAG_TRACES, html_mod, mo, q_pick):
    _t = RAG_TRACES[RAG_QUERIES.index(q_pick.value)]

    def _card(title, color, text):
        return (
            f'<div style="flex:1;min-width:260px;border:2px solid {color};border-radius:12px;'
            f'padding:12px 14px;font-family:system-ui,sans-serif">'
            f'<div style="font-size:12px;letter-spacing:.06em;font-weight:800;color:{color};'
            f'margin-bottom:8px">{title}</div>'
            f'<div style="font-size:13px;line-height:1.8;white-space:pre-wrap">{html_mod.escape(text)}</div></div>'
        )

    mo.Html(
        '<div style="display:flex;gap:12px;flex-wrap:wrap">'
        + _card("❌ 無 RAG（自由發揮）", "#C44E52", _t["bare"])
        + _card("✅ 有 RAG（附 top-3 段落）", "#55A868", _t["rag"])
        + "</div>"
        + '<div style="font-size:12px;color:#5A6A72;margin-top:8px">實測紀錄（qwen3.5-2b，temperature=0，2026-08）；'
        "手冊是虛構教材，模型不可能在訓練時看過——沒查手冊的每一句細節都只能是編的。長回答有節錄，完整版在左頁開場互動。</div>"
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    看懂這組對照的三個層次：

    - **Q1／Q2**：無 RAG 版一本正經地教你「裝咖啡液體」「倒白醋、跑 15–30 分鐘」——
      **流程是編的、數字是編的**，但語氣自信到你不會起疑。這叫**幻覺（hallucination）**。
    - **Q3**：無 RAG 版講的咖啡通識大多是對的（磨太細→過度萃取）——
      但它答不出「防堵塞保護自動停機」這種**只在手冊裡的規格**。
    - **Q4**：保固「2 年」矇對了（常見值），細節（合約、水質過鹹、強光直射）全是編的——
      **矇對的部分和編造的部分長得一模一樣**，你無法分辨哪句可信。這就是要 RAG 的理由。

    ## 3️⃣ 拆開管線：檢索到的段落是怎麼「塞」進去的

    沒有魔法——就是把段落**貼進 prompt** 再問一次。下面印出的是實測時
    真正送給模型的完整內容（Q2 為例）：
    """
    )
    return


@app.cell
def _(DOC_N, Q_N, RAG_CHUNKS, RAG_QUERIES, np):
    # 與實測 spike 同一份組裝邏輯：system 規則 ＋ top-3 段落 ＋ 問題
    SYS_RAG = (
        "你是「拿鐵大師 LM-500」咖啡機的客服，請回答使用者的問題。"
        "只能根據下面提供的手冊段落回答；手冊裡沒有的資訊，要說「手冊中沒有提到」。"
    )
    _qi = 1  # Q2 除垢
    _idx = np.argsort(-(DOC_N @ Q_N[_qi]))[:3]
    _ctx = "\n".join(f"【段落{_i+1}】{RAG_CHUNKS[_i]}" for _i in (int(_x) for _x in _idx))
    rag_user_prompt = f"手冊段落：\n{_ctx}\n\n問題：{RAG_QUERIES[_qi]}"
    print("=== system ===")
    print(SYS_RAG)
    print("\n=== user ===")
    print(rag_user_prompt)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    整條 RAG 管線就是五步，每一步你在這一課都摸過了：

    1. **切塊（chunking）**：手冊切成 12 段——一段講一件事
    2. **向量化（embed）**：每段算一個 1024 維向量，存進向量資料庫
    3. **檢索（retrieve）**：問題也算向量，cosine 排序取 top-k（1️⃣）
    4. **組裝（augment）**：把 top-k 段落貼進 prompt，加上「只能根據段落回答」的規則（3️⃣）
    5. **生成（generate）**：模型照著段落回答，答不了的說「手冊中沒有提到」（2️⃣）

    system prompt 那句「手冊裡沒有的資訊，要說『手冊中沒有提到』」不是裝飾——
    它把模型從「編一個答案」的預設行為，扳成「承認查不到」。

    ## 4️⃣ 你的實驗區

    下面是你的實驗區。挑戰在左頁「換你動手」，做完再開解答對照。
    """
    )
    return


@app.cell
def _(DOC_N, Q_N, RAG_CHUNKS, RAG_QUERIES, mo, np, q_pick, top_k):
    # 1️⃣ 選的問題與 top-k，換算成「塞進 prompt 要多少錢」
    _qi = RAG_QUERIES.index(q_pick.value)
    _sims = DOC_N @ Q_N[_qi]
    _order = [int(_x) for _x in np.argsort(-_sims)]
    _rows = []
    for _k in range(1, 6):
        _chars = sum(len(RAG_CHUNKS[_i]) for _i in _order[:_k])
        _mark = " ←你現在的設定" if _k == top_k.value else ""
        _rows.append(
            f"| top-{_k} | chunk {_order[_k - 1] + 1}（{_sims[_order[_k - 1]]:.3f}） "
            f"| {_chars} 字 | {_chars * 1.14:.0f} tokens{_mark} |"
        )
    _table = "\n    ".join(_rows)
    mo.md(
        f"""
    **你的實驗區**——1️⃣ 選的是「{q_pick.value}」。多塞一段，prompt 就多這麼多：

    | 取到第幾名 | 第 k 名（cosine） | 段落總字數 | 估算 token |
    | --- | --- | --- | --- |
    {_table}

    往下走，cosine 一路掉、token 一路漲。**多塞的段落＝多花的 token ＋ 多給模型的干擾**——
    夠用就好，不是越多越好。（token 粗估：中文 1 字 ≈ 1.14 token。）
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.accordion(
        {
            "💡 LEVEL 1 參考解答": mo.md(
                r"""
    在 1️⃣ 把 top-k 從 3 拉到 5：第一個問題的第 4、5 名相似度掉到 **0.44 / 0.40**
    （前三名是 0.67 / 0.53 / 0.51），內容跟「第一次使用」也搭不上邊。
    右邊 4️⃣ 的表格把這件事換算成錢：從 top-3 走到 top-5，字數與 token 一路往上漲，
    新增的內容卻答不了問題——**top-k 不是越大越好，是「夠用就好」**。
    多塞的段落＝多花的 token ＋ 多給模型的干擾。
    """
            ),
            "💡 LEVEL 2 參考解答": mo.md(
                r"""
    把 1️⃣ 的問題換成「保固期多久？哪些情況不保固？」、top-k 拉到 1：
    top-1 是 chunk 5（保固），cosine 0.644——這題只靠一段就答得全對，因為答案集中在一段裡。

    再換回「咖啡機第一次使用前要做什麼？」、top-k 一樣是 1：top-1 是 chunk 1，也夠。
    但想像問題是「除垢完成後要不要再洗一次？」——答案橫跨「除垢」與
    「日常清潔」兩段，top-1 就可能漏。**k 的選擇取決於答案散佈在幾段裡**；
    工程上常見起點是 3–5，再依實際問題分布調。

    （誠實提醒：右邊只能離線分析「檢索會選哪幾段」；模型的回答是預錄的
    實測紀錄，改 k 不會重新生成回答——要看新組合的回答，得拿左頁的程式
    範例接上你自己的模型跑。）
    """
            ),
            "💡 LEVEL 3 提示": mo.md(
                r"""
    設計一個「一定檢索失敗」的問題：問一件手冊**沒寫**的事，
    例如「LM-500 可以做冰滴咖啡嗎？」。

    預期會發生什麼：檢索照樣回傳 top-3（cosine 排序永遠有前三名，
    也許 0.3 左右——**檢索不會說「查無此事」，它只會給你「最不無關」的段落**）；
    這時就靠 system prompt 那句「手冊裡沒有的資訊，要說『手冊中沒有提到』」擋住編造。

    怎麼驗證自己想對了：看 2️⃣ 的 system 規則——把「相似度低於門檻就不回答」
    做成程式（例如 top-1 < 0.4 直接回「手冊沒提到」），是實務上常見的第二道保險。
    兩道保險（檢索門檻＋prompt 規則）都做，幻覺才難鑽出來。
    """
            ),
        }
    )
    return


if __name__ == "__main__":
    app.run()
