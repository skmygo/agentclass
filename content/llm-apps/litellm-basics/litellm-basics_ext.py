# LiteLLM 基礎：一個網址、一把 key，打遍八家模型
# 不需要 GPU——molab 免費 CPU 環境即可全程執行（需要網路：會真的打 gateway）。
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "marimo",
#     "openai>=2.0",
#     "numpy",
#     "matplotlib",
# ]
# ///
import marimo

__generated_with = "0.23.16"
app = marimo.App(width="medium", app_title="LiteLLM：一個網址、一把 key，打遍八家模型")


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    # 🔑 LiteLLM：一個網址、一把 key，打遍八家模型

    你寫過打 OpenAI API 的程式嗎？那你已經會用 LiteLLM 了——因為
    **LiteLLM gateway 就是一個「長得跟 OpenAI 一模一樣」的入口**，
    背後卻接著 NVIDIA、Google、Groq、Cloudflare……八家供應商。
    換模型只要換一個字串，程式、SDK、金鑰都不用動。

    這份 notebook 會帶你：

    1. 用兩行設定連上 gateway，列出它有哪些模型
    2. 發第一次對話、看懂回應物件裡藏了什麼
    3. 踩一個推理型模型的經典坑（`max_tokens` 給小了回答是空的）
    4. 串流輸出、文字向量（embeddings）
    5. 同時發 12 個請求，親眼看見「同名多來源」在分流

    從第一格往下全部執行即可（首次安裝套件約 1 分鐘；每格都會真的連網打 gateway）。
    """
    )
    return


@app.cell
def _():
    import asyncio
    import time
    from collections import Counter
    from urllib.parse import urlparse

    import marimo as mo
    import matplotlib
    import numpy as np
    from openai import AsyncOpenAI, OpenAI

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    return AsyncOpenAI, Counter, OpenAI, asyncio, mo, np, plt, time, urlparse


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 0️⃣ 兩行設定：網址與 key

    重點只有兩行——`base_url` 指到 gateway、`api_key` 用教學用的 virtual key。
    SDK 用的是官方 `openai` 套件，**一行都沒改**。

    這把 key 是課程專用的子金鑰（只開放免費模型、之後會撤銷），可以直接示人。
    正式專案請自己發一把：gateway 的管理介面可以對每把 key 設預算、限定模型、看用量。
    """
    )
    return


@app.cell
def _(OpenAI):
    BASE_URL = "https://litellm.itsmygo.uk/v1"   # 公開端點（Cloudflare → 自家 gateway）
    API_KEY = "sk-FiIRnuzLH7ypgf29LTpHNw"        # 教學用 virtual key（只開免費模型，課後撤銷）

    client = OpenAI(base_url=BASE_URL, api_key=API_KEY)
    client
    return API_KEY, BASE_URL, client


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 1️⃣ 這個 gateway 有哪些模型？

    `client.models.list()` 問 gateway 「你會哪些模型」。注意每個名字背後可能**不只一家**：
    `nemotron-3.5-lightning` 是同一顆 30B-A3B 輕量推理模型的**兩個來源**（NVIDIA NIM／OpenRouter）
    互相備援，本系列課程全部用它；`nemotron-3-ultra` 是 550B 旗艦的三來源備援；
    `free-chat` 是多家免費模型的輪替群組；名字含 `embed` 的是文字向量模型，其餘是對話模型。

    模型名是**穩定的約定**：之後上游漲價、換家、出新模型，只要 gateway 那邊改設定，
    你的程式裡的 `"nemotron-3.5-lightning"` 一個字都不用動。
    """
    )
    return


@app.cell
def _(client, mo):
    model_names = sorted(m.id for m in client.models.list())

    _KIND = {
        "free-chat": "對話 · 多家免費模型輪替",
        "nemotron-3.5-lightning": "對話 · 30B-A3B 輕快推理型，2 家同名備援（本系列預設）",
        "nemotron-3-ultra": "對話 · 550B 旗艦，3 家同名備援",
        "gemini-3.5-flash": "對話 · Google（唯一看得懂圖的）",
        "gpt-oss-120b": "對話 · Groq（快、tool calling 穩）",
        "cf-gpt-oss-120b": "對話 · Cloudflare Workers AI",
        "deepseek-v4-flash": "對話 · HuggingFace router",
        "qwen3-embedding-0.6b": "向量 · 1024 維（Cloudflare）",
        "nemotron-3-embed-1b": "向量 · 2048 維（NVIDIA）",
    }
    mo.vstack([
        mo.md(f"gateway 回報 **{len(model_names)} 個模型名**："),
        mo.ui.table(
            [{"模型名": n, "類型 · 來源": _KIND.get(n, "embedding" if "embed" in n else "chat")} for n in model_names],
            selection=None,
        ),
    ])
    return (model_names,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 2️⃣ 第一次對話

    `client.chat.completions.create(...)` 是所有 OpenAI 相容 API 的核心呼叫：
    給 `model` 與 `messages`（一串 role/content），拿回一個 `ChatCompletion` 物件。
    回答在 `choices[0].message.content`；`usage` 告訴你這發花了多少 token；
    `model` 是實際回應的模型。

    下面這格用 `nemotron-3.5-lightning`。這顆是**推理型**模型——會先在心裡想再開口，
    而且想得不少（一句自我介紹可能先想 600 多個 token），所以 `max_tokens` 要給足
    （本系列一律 4096）；耗時也跟這一發落到哪個來源有關，第 6 節會把這件事變成看得見的統計。
    """
    )
    return


@app.cell
def _(client, mo, time):
    _t0 = time.perf_counter()
    first_reply = client.chat.completions.create(
        model="nemotron-3.5-lightning",
        messages=[{"role": "user", "content": "用一句話介紹你自己，說明你是什麼模型。"}],
        max_tokens=4096,
    )
    _dt = time.perf_counter() - _t0
    mo.md(
        f"""
    **回答**：{first_reply.choices[0].message.content}

    | 欄位 | 值 |
    |---|---|
    | `model` | `{first_reply.model}` |
    | `usage.prompt_tokens` | {first_reply.usage.prompt_tokens} |
    | `usage.completion_tokens` | {first_reply.usage.completion_tokens} |
    | `finish_reason` | `{first_reply.choices[0].finish_reason}` |
    | 耗時 | {_dt:.1f} s |
    """
    )
    return (first_reply,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ### 換你問：挑模型、改問題

    選一個模型、打一句話、按執行。同一段程式碼，換的只是 `model` 字串。
    """
    )
    return


@app.cell
def _(mo, model_names):
    pick_model = mo.ui.dropdown(
        options=[n for n in model_names if "embed" not in n],
        value="nemotron-3.5-lightning",
        label="模型",
    )
    ask_text = mo.ui.text(value="台灣最高的山是哪一座？一句話回答。", label="問題", full_width=True)
    ask_btn = mo.ui.run_button(label="送出")
    mo.hstack([pick_model, ask_text, ask_btn], widths=[1, 3, 0.6])
    return ask_btn, ask_text, pick_model


@app.cell
def _(ask_btn, ask_text, client, mo, pick_model, time):
    mo.stop(not ask_btn.value, mo.md("_按「送出」才會真的打 API。_"))
    _t0 = time.perf_counter()
    try:
        _r = client.chat.completions.create(
            model=pick_model.value,
            messages=[{"role": "user", "content": ask_text.value}],
            max_tokens=4096,
        )
        _out = mo.md(
            f"**[{pick_model.value}]** {_r.choices[0].message.content}\n\n"
            f"_{_r.usage.completion_tokens} tokens · {time.perf_counter() - _t0:.1f}s_"
        )
    except Exception as _e:  # noqa: BLE001  429＝限流、400＝參數不合、5xx＝上游掛了
        _out = mo.callout(mo.md(f"這一發失敗了（再按一次通常就輪到別的來源）：\n\n`{str(_e)[:200]}`"), kind="warn")
    _out
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 3️⃣ 經典坑：推理型模型的 `max_tokens`

    這個 gateway 上的免費模型多數是**推理型**（reasoning model）：它們先在心裡「想」，
    想的過程也算 completion token。`max_tokens` 給太小，token 全花在思考上就被切斷——
    `finish_reason` 是 `length`，而且有的來源會**把切到一半的思考當 content 吐給你**
    （開頭是 "Here's a thinking process…"），看起來像答案其實不是。

    給夠的話，答案在 `content`，思考過程在一個非標準欄位 `reasoning_content`
    （`getattr(message, "reasoning_content", None)` 拿得到）。下面兩格對照 20 與 4096。
    `reasoning_tokens` 不是每個來源都回報（OpenRouter 會、NIM 是 `None`），
    這也是「同一模型名、不同上游」的痕跡。
    """
    )
    return


@app.cell
def _(client, mo):
    tiny = client.chat.completions.create(
        model="nemotron-3.5-lightning",
        messages=[{"role": "user", "content": "1+1=?"}],
        max_tokens=20,
    )
    enough = client.chat.completions.create(
        model="nemotron-3.5-lightning",
        messages=[{"role": "user", "content": "1+1=?"}],
        max_tokens=4096,
    )

    def _row(r):
        _m = r.choices[0].message
        _d = r.usage.completion_tokens_details
        return (repr((_m.content or "")[:60]), r.choices[0].finish_reason, r.usage.completion_tokens,
                getattr(_d, "reasoning_tokens", None) if _d else None,
                repr((getattr(_m, "reasoning_content", None) or "")[:40]))

    _a, _b = _row(tiny), _row(enough)
    mo.md(
        f"""
    | 欄位 | `max_tokens=20` | `max_tokens=4096` |
    |---|---|---|
    | `content` | `{_a[0]}` | `{_b[0]}` |
    | `finish_reason` | `{_a[1]}` | `{_b[1]}` |
    | `completion_tokens` | {_a[2]} | {_b[2]} |
    | `reasoning_tokens` | {_a[3]} | {_b[3]} |
    | `reasoning_content` | `{_a[4]}` | `{_b[4]}` |

    → 結論：對推理型模型，`max_tokens` 要給到思考＋答案都裝得下（本系列一律 4096）。
    """
    )
    return enough, tiny


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 4️⃣ 串流：邊生成邊收

    加上 `stream=True`，回傳的不是一個物件而是一串 chunk；每個 chunk 的
    `choices[0].delta.content` 是新增的幾個字。聊天介面「一個字一個字跳出來」就是這樣做的。

    下面把每個 chunk 到達的時間記下來畫成圖。推理型模型的串流常有個特徵：
    **前面一段空白是它在想**（思考過程不會串流出來），想完之後文字才一口氣湧出——
    「首字延遲」主要是思考時間（幾秒到不到一秒都有，看落到哪個來源），首字到全文完成反而很快。
    做聊天介面時，這段空白就是該放「思考中…」提示的地方。
    """
    )
    return


@app.cell
def _(client, time):
    _t0 = time.perf_counter()
    stream_chunks = []   # (到達秒數, 這一塊的文字)
    for _chunk in client.chat.completions.create(
        model="nemotron-3.5-lightning",
        messages=[{"role": "user", "content": "用三句話介紹台北。"}],
        max_tokens=4096,
        stream=True,
    ):
        if _chunk.choices and _chunk.choices[0].delta.content:
            stream_chunks.append((time.perf_counter() - _t0, _chunk.choices[0].delta.content))
    stream_text = "".join(_c for _, _c in stream_chunks)
    return stream_chunks, stream_text


@app.cell
def _(mo, stream_chunks, stream_text):
    mo.md(
        f"""
    **串流結果**（{len(stream_chunks)} 個 chunk）：{stream_text}

    首字到達：**{stream_chunks[0][0]:.2f}s** ／ 全部完成：**{stream_chunks[-1][0]:.2f}s**
    """
    )
    return


@app.cell
def _(np, plt, stream_chunks):
    _t = [t for t, _ in stream_chunks]
    _chars = np.cumsum([len(c) for _, c in stream_chunks])
    _fig, _ax = plt.subplots(figsize=(7, 3))
    _ax.step(_t, _chars, where="post", color="#4C72B0", lw=2)
    _ax.axvline(_t[0], color="#DD8452", ls="--", lw=1.5, label=f"first chunk {_t[0]:.2f}s")
    _ax.axvline(_t[-1], color="#55A868", ls="--", lw=1.5, label=f"done {_t[-1]:.2f}s")
    _ax.set_xlabel("seconds since request")
    _ax.set_ylabel("characters received")
    _ax.set_title("Streaming: characters arrive over time")
    _ax.legend(frameon=False)
    _ax.spines[["top", "right"]].set_visible(False)
    _fig.tight_layout()
    _fig
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 5️⃣ Embeddings：把文字變成向量

    `client.embeddings.create(...)` 走的是**同一個入口、同一把 key**，只是換成向量模型。
    `qwen3-embedding-0.6b` 把任何一段文字變成 **1024 個數字**；意思相近的句子，
    向量的方向也相近——用餘弦相似度（cosine）就能量。

    注意：這個模型回傳的向量**長度已經是 1**（單位向量），所以內積＝餘弦相似度。
    下面四句話：兩句講貓、一句講股市、一句講天氣——看熱圖就知道模型懂不懂中文。
    這也是後面 Qdrant 與 RAG 兩課的地基。
    """
    )
    return


@app.cell
def _(client, np):
    sentences = [
        "貓咪喜歡曬太陽",
        "小貓在窗邊打盹",
        "今天股市大跌",
        "午後可能有雷陣雨",
    ]
    _resp = client.embeddings.create(model="qwen3-embedding-0.6b", input=sentences)
    emb = np.array([d.embedding for d in _resp.data])
    sim = emb @ emb.T   # 單位向量 → 內積即 cosine
    emb.shape, np.linalg.norm(emb, axis=1).round(3)
    return emb, sentences, sim


@app.cell
def _(np, plt, sim):
    _fig, _ax = plt.subplots(figsize=(5.2, 4.4))
    _im = _ax.imshow(sim, cmap="YlGnBu", vmin=0, vmax=1)
    _labels = ["cat sunbathing", "kitten napping", "stock crash", "thunderstorm"]
    _ax.set_xticks(range(4), _labels, rotation=30, ha="right")
    _ax.set_yticks(range(4), _labels)
    for _i in range(4):
        for _j in range(4):
            _ax.text(_j, _i, f"{sim[_i, _j]:.2f}", ha="center", va="center",
                     color="white" if sim[_i, _j] > 0.6 else "black", fontsize=10)
    _ax.set_title("Cosine similarity (qwen3-embedding-0.6b)")
    _fig.colorbar(_im, fraction=0.046)
    _fig.tight_layout()
    _fig
    return


@app.cell
def _(mo, sentences, sim):
    mo.md(
        f"""
    「{sentences[0]}」vs「{sentences[1]}」＝ **{sim[0, 1]:.2f}**（都在講貓）；
    「{sentences[0]}」vs「{sentences[2]}」＝ **{sim[0, 2]:.2f}**（貓 vs 股市）。
    模型沒看過任何標註，純粹從語意就把兩句貓話拉近了。
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 6️⃣ 並發批次：親眼看見「同名兩來源」在分流

    免費方案的共同特性是**單家限流都很小**。gateway 把 `nemotron-3.5-lightning` 的兩個來源
    （NVIDIA NIM／OpenRouter）掛在同一個名字下，用 `simple-shuffle` 隨機分流、
    撞到 429/5xx 自動重試換家。可是……你怎麼知道它真的在換？

    兩個技巧：

    - **`AsyncOpenAI` + `asyncio.gather`**：12 發同時出去，總耗時 ≈ 最慢那一發，不是 12 倍。
      這是批次推論的標準寫法。
    - **`with_raw_response`**：拿得到 HTTP header。LiteLLM 每個回應都帶
      `x-litellm-model-api-base`，告訴你這一發實際落在哪家上游。

    失敗的也算進統計——**看見失敗本身就是可觀察性**。另外盯著每一發的秒數：
    同一顆模型在不同來源的延遲不一樣（實測多數 2–5 秒，偶爾一發要等 10–30 秒），
    12 發並發牆鐘約 15–20 秒。
    """
    )
    return


@app.cell
async def _(API_KEY, AsyncOpenAI, BASE_URL, asyncio, time, urlparse):
    aclient = AsyncOpenAI(base_url=BASE_URL, api_key=API_KEY, max_retries=0)

    _PROVIDER = {   # api_base 網域 → 供應商（沒帶 host 的是 OpenRouter）
        "integrate.api.nvidia.com": "NVIDIA NIM",
        "ollama.com": "Ollama Cloud",
        "generativelanguage.googleapis.com": "Google Gemini",
        "api.groq.com": "Groq",
        "api.cloudflare.com": "Cloudflare",
        "router.huggingface.co": "HuggingFace",
        "": "OpenRouter",
    }

    async def _one(i):
        _t0 = time.perf_counter()
        try:
            _raw = await aclient.chat.completions.with_raw_response.create(
                model="nemotron-3.5-lightning",
                messages=[{"role": "user", "content": f"只回一個數字：{i}+{i}=?"}],
                max_tokens=4096,
            )
            _host = urlparse(_raw.headers.get("x-litellm-model-api-base", "")).netloc
            return {"#": i, "provider": _PROVIDER.get(_host, _host), "ok": True,
                    "sec": round(time.perf_counter() - _t0, 1),
                    "answer": (_raw.parse().choices[0].message.content or "").strip()[:20]}
        except Exception as _e:  # noqa: BLE001
            _code = getattr(_e, "status_code", "?")
            return {"#": i, "provider": f"failed: HTTP {_code}", "ok": False,
                    "sec": round(time.perf_counter() - _t0, 1), "answer": str(_e)[:60]}

    async def run_batch(n=12):
        _t0 = time.perf_counter()
        _rows = await asyncio.gather(*(_one(i) for i in range(1, n + 1)))
        return list(_rows), time.perf_counter() - _t0

    batch_rows, batch_wall = await run_batch(12)
    return aclient, batch_rows, batch_wall, run_batch


@app.cell
def _(batch_rows, batch_wall, mo):
    _sum = sum(r["sec"] for r in batch_rows)
    mo.vstack([
        mo.md(
            f"12 發同時出去：牆鐘時間 **{batch_wall:.1f}s**；若一發一發序跑要 **{_sum:.1f}s**"
            f"（並發省下 {_sum - batch_wall:.0f}s）。成功 {sum(r['ok'] for r in batch_rows)}／12。"
        ),
        mo.ui.table(batch_rows, selection=None),
    ])
    return


@app.cell
def _(Counter, batch_rows, plt):
    _cnt = Counter(r["provider"] for r in batch_rows).most_common()
    _fig, _ax = plt.subplots(figsize=(7, 0.5 * len(_cnt) + 1.2))
    _names = [p for p, _ in _cnt][::-1]
    _vals = [c for _, c in _cnt][::-1]
    _colors = ["#C44E52" if n.startswith("failed") else "#4C72B0" for n in _names]
    _ax.barh(_names, _vals, color=_colors)
    _ax.set_xlabel("requests")
    _ax.set_title("nemotron-3.5-lightning: where did 12 concurrent requests land?")
    _ax.spines[["top", "right"]].set_visible(False)
    _fig.tight_layout()
    _fig
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    `simple-shuffle` 是隨機分流不是輪盤，單次分佈不均勻是正常的；多跑幾次（重新執行上面
    那格）分佈會攤平。表格裡同一個來源的秒數也會差很多——這正是 gateway 存在的理由：
    一家慢了、限流了、倒了，另一家照跑，你的程式碼一個字都不用改。

    ## 7️⃣ 零程式碼整合：任何 OpenAI 相容工具都能用

    因為介面跟 OpenAI 完全相同，任何認得 OpenAI 環境變數的工具兩個變數指過來就能用：

    ```bash
    export OPENAI_BASE_URL="https://litellm.itsmygo.uk/v1"   # 有的工具叫 OPENAI_API_BASE
    export OPENAI_API_KEY="<你的 virtual key>"
    ```

    - **curl**：`curl $OPENAI_BASE_URL/chat/completions -H "Authorization: Bearer $OPENAI_API_KEY" -H "Content-Type: application/json" -d '{"model":"nemotron-3.5-lightning","messages":[{"role":"user","content":"hi"}]}'`
    - **LangChain**：`ChatOpenAI(base_url=..., api_key=..., model="nemotron-3.5-lightning")`
    - **Open WebUI / aider / Cursor**：設定裡填 base URL 與 key，模型清單自動出現

    ## 🏆 延伸挑戰

    1. **LEVEL 1**：把 2️⃣ 的 `messages` 加一則 `{"role": "system", "content": "你只會用文言文回答"}`，
       看 system prompt 怎麼改變回答風格。
    2. **LEVEL 2**：把 5️⃣ 的四句話換成你自己的（例如三句同主題、一句離題），先猜熱圖長相再跑。
       再把模型換成 `nemotron-3-embed-1b`（2048 維）比較結果。
    3. **LEVEL 3**：修改 6️⃣ 的 `run_batch`，對 `nemotron-3-ultra`（550B、三個來源）發 12 發，
       比較延遲與分佈跟 lightning 的差別；再算各來源的平均秒數，哪家最快、哪家最飄？

    帶得走：下載本檔後 `uvx marimo edit --sandbox litellm-basics_ext.py`
    在自己電腦繼續玩（依賴會自動安裝）。下一課：讓模型**做事**——tool calling、
    結構化輸出與看圖。
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    # 挑戰的折疊解答：先自己做再打開。LEVEL 1/2 是可直接貼進新 cell 的完整程式碼，LEVEL 3 給方向與驗證方法。
    mo.accordion(
        {
            "💡 LEVEL 1 參考解答：system prompt": mo.md(
                r"""
    `messages` 是一個依序排列的對話：`system` 擺最前面，是「給模型的工作守則」，使用者看不到。
    新開一格貼上：

    ```python
    _r = client.chat.completions.create(
        model="nemotron-3.5-lightning",
        messages=[
            {"role": "system", "content": "你只會用文言文回答"},
            {"role": "user", "content": "用一句話介紹你自己，說明你是什麼模型。"},
        ],
        max_tokens=4096,
    )
    _r.choices[0].message.content
    ```

    你應該看到：同一個問題，回答變成「吾乃一巨大之語言模型，能通文理，應問能答。」這類句子
    （實測（nemotron-3.5-lightning）每次措辭都不同，但一定是文言文；耗時 15–35 秒，因為它還是會先推理）。
    system prompt 是最便宜的「改行為」手段——之後 RAG 課的「只能根據參考資料回答」也是寫在這裡。
    """
            ),
            "💡 LEVEL 2 參考解答：自己的句子 + 換 embedding 模型": mo.md(
                r"""
    把 5️⃣ 那格的 `sentences` 直接改掉（例如三句講鍵盤、一句講晚餐），存檔後熱圖會自動重畫。
    要同時比較兩個模型，新開一格：

    ```python
    _my = ["鍵盤的軸體影響手感", "機械鍵盤敲起來很有節奏", "青軸的聲音特別清脆", "今天晚餐想吃拉麵"]
    _rows = []
    for _m in ["qwen3-embedding-0.6b", "nemotron-3-embed-1b"]:
        _e = np.array([d.embedding for d in client.embeddings.create(model=_m, input=_my).data])
        _e = _e / np.linalg.norm(_e, axis=1, keepdims=True)   # 保險：先正規化再內積
        _s = _e @ _e.T
        _rows.append({"model": _m, "dims": _e.shape[1],
                      "鍵盤 vs 鍵盤": f"{_s[0, 1]:.2f} / {_s[0, 2]:.2f} / {_s[1, 2]:.2f}",
                      "鍵盤 vs 拉麵": f"{_s[0, 3]:.2f} / {_s[1, 3]:.2f} / {_s[2, 3]:.2f}"})
    mo.ui.table(_rows, selection=None)
    ```

    你應該看到（實測）：`qwen3-embedding-0.6b` 1024 維，同主題 0.58–0.70、離題 0.27–0.38，落差明顯；
    `nemotron-3-embed-1b` 2048 維，同主題 0.47–0.63、離題卻也有 0.53–0.58——**分數尺度跟模型綁定**，
    兩個模型的 0.5 意義完全不同，做 RAG 的門檻只能用自己的資料實測，不能跨模型沿用。
    兩個模型回傳的都是單位向量（norm = 1），所以上面的正規化只是保險。
    """
            ),
            "💡 LEVEL 3 提示：換 nemotron-3-ultra 看三來源的延遲": mo.md(
                r"""
    `run_batch` 裡寫死了模型名，最小改法是複製 6️⃣ 那格、把 `_one` 裡的 `model=` 換成 `"nemotron-3-ultra"`、
    函式名改成 `run_batch_ultra`（marimo 同一個名字不能在兩格定義）。然後分組統計：

    ```python
    from collections import defaultdict
    _by = defaultdict(list)
    for _r in ultra_rows:                    # 你的新 run_batch 回傳的列
        _by[_r["provider"]].append(_r["sec"])
    mo.ui.table([{"provider": p, "n": len(s), "mean_sec": round(np.mean(s), 1),
                  "min": min(s), "max": max(s), "std": round(np.std(s), 1)}
                 for p, s in sorted(_by.items(), key=lambda kv: np.mean(kv[1]))], selection=None)
    ```

    怎麼驗證：表格要出現 **三個來源名**（NVIDIA NIM／OpenRouter／Ollama Cloud），而 lightning 只有兩個。
    實測一次：牆鐘 31 秒、12/12 成功，OpenRouter 平均 1.9 秒最快最穩（std 0.4）、NIM 平均 7.8 秒但 std 10.5
    （最慢一發 30 秒）、Ollama Cloud 平均 8 秒。**「哪家最飄」看 std 不看 mean**。
    550B 比 30B 慢是預期內的；但同一家的 1.3 秒到 30 秒落差，才是 gateway 要自動換家的理由。
    分佈每次都不同——`simple-shuffle` 是隨機的，多跑幾次再下結論。
    """
            ),
        }
    )
    return


if __name__ == "__main__":
    app.run()
