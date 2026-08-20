# Qdrant：向量資料庫，記憶體裡就能跑
# 不需要 GPU——molab 免費 CPU 環境即可全程執行（只有最後一節會連網打 gateway 拿真的 embedding）。
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "marimo",
#     "qdrant-client>=1.12",
#     "openai>=2.0",
#     "numpy",
#     "matplotlib",
# ]
# ///
import marimo

__generated_with = "0.23.16"
app = marimo.App(width="medium", app_title="Qdrant：向量資料庫，記憶體裡就能跑")


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    # 🧭 Qdrant：向量資料庫，記憶體裡就能跑

    一般資料庫回答「**等於**什麼」：`WHERE name = '紅茶'`。向量資料庫回答「**最像**什麼」：
    給一個向量，找出距離最近的幾筆。LLM 應用（RAG、推薦、去重、語意搜尋）的核心都是這個問題。

    **Qdrant** 是現在最常用的向量資料庫之一。它通常跑成一個伺服器（Docker 一行），
    但 Python 客戶端有個超方便的模式：`QdrantClient(":memory:")`——**整個資料庫在記憶體裡跑**，
    不裝任何東西、API 跟正式伺服器一模一樣。學習、測試、小型 demo 都用它。

    為了讓你**看得見**向量在做什麼，前半段用人看得懂的 3 維「口味向量」（甜／酸／辣）
    代替 1024 維的 embedding；概念通了，最後一節再換成真的。

    1. 向量是什麼：八道菜的口味向量
    2. 起一個記憶體 Qdrant：collection、點、payload
    3. 最近鄰查詢：拉桿調口味，看它推薦什麼
    4. 過濾：向量相似 + 條件篩選同時成立
    5. 距離度量：Cosine、Euclid、Dot 差在哪
    6. 換真的向量：LiteLLM 的 `qwen3-embedding-0.6b`，用自然語言查菜單

    從第一格往下全部執行即可（首次安裝套件約 1 分鐘）。
    """
    )
    return


@app.cell
def _():
    import marimo as mo
    import matplotlib
    import numpy as np
    from openai import OpenAI
    from qdrant_client import QdrantClient
    from qdrant_client.models import (
        Distance,
        FieldCondition,
        Filter,
        MatchValue,
        PointStruct,
        Range,
        VectorParams,
    )

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    return (
        Distance,
        FieldCondition,
        Filter,
        MatchValue,
        OpenAI,
        PointStruct,
        QdrantClient,
        Range,
        VectorParams,
        mo,
        np,
        plt,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 1️⃣ 向量是什麼：八道菜的口味向量

    每道菜用三個 0–1 的數字描述：`[甜, 酸, 辣]`。這就是一個向量——
    「珍珠奶茶 = [0.9, 0.1, 0.0]」很甜、微酸、不辣。兩道菜的向量越接近，口味越像。
    真實世界的 embedding 模型做的是一樣的事，只是維度從 3 變成 1024、
    而且每一維的意義是模型自己學出來的、人看不懂。
    """
    )
    return


@app.cell
def _(mo):
    DISHES = [   # (名稱, [甜, 酸, 辣], 類別, 價格)
        ("珍珠奶茶", [0.90, 0.10, 0.00], "drink", 60),
        ("檸檬紅茶", [0.50, 0.80, 0.00], "drink", 45),
        ("蜂蜜檸檬", [0.80, 0.60, 0.00], "drink", 55),
        ("焦糖布丁", [0.95, 0.05, 0.00], "dessert", 80),
        ("糖醋排骨", [0.70, 0.60, 0.10], "food", 180),
        ("泰式酸辣湯", [0.20, 0.80, 0.70], "food", 120),
        ("酸辣粉", [0.10, 0.70, 0.80], "food", 90),
        ("麻辣鍋", [0.10, 0.20, 0.95], "food", 350),
    ]
    mo.ui.table(
        [{"id": i, "name": n, "sweet": v[0], "sour": v[1], "spicy": v[2], "kind": k, "price": p}
         for i, (n, v, k, p) in enumerate(DISHES)],
        selection=None,
    )
    return (DISHES,)


@app.cell
def _(DISHES, plt):
    _fig, _ax = plt.subplots(figsize=(6.4, 4.6))
    _EN = {"珍珠奶茶": "bubble tea", "檸檬紅茶": "lemon tea", "蜂蜜檸檬": "honey lemon", "焦糖布丁": "pudding",
           "糖醋排骨": "sweet-sour ribs", "泰式酸辣湯": "tom yum", "酸辣粉": "hot-sour noodles", "麻辣鍋": "mala hotpot"}
    _sc = _ax.scatter([v[0] for _, v, _, _ in DISHES], [v[1] for _, v, _, _ in DISHES],
                      c=[v[2] for _, v, _, _ in DISHES], cmap="Reds", vmin=0, vmax=1,
                      s=[80 + 400 * v[2] for _, v, _, _ in DISHES], edgecolor="#1C2B33")
    for n, v, _, _ in DISHES:
        _ax.annotate(_EN[n], (v[0], v[1]), textcoords="offset points", xytext=(8, 6), fontsize=9)
    _ax.set_xlabel("sweet")
    _ax.set_ylabel("sour")
    _ax.set_xlim(-0.05, 1.15)
    _ax.set_ylim(-0.05, 1.0)
    _ax.set_title("Taste space: 8 dishes as vectors (size & color = spicy)")
    _fig.colorbar(_sc, label="spicy")
    _ax.spines[["top", "right"]].set_visible(False)
    _fig.tight_layout()
    _fig
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 2️⃣ 起一個記憶體 Qdrant

    三個概念：

    - **Collection**：一張「表」，建立時就要說定向量幾維、用什麼距離（`VectorParams`）。
    - **Point**：一筆資料 = `id` + `vector` + `payload`（任意 JSON，放名稱、類別、價格等原始資訊）。
    - **Upsert**：寫入（同 id 則覆蓋）。

    `QdrantClient(":memory:")` 換成 `QdrantClient("http://localhost:6333")` 就是連正式伺服器，
    下面所有程式碼一個字都不用改。
    """
    )
    return


@app.cell
def _(DISHES, Distance, PointStruct, QdrantClient, VectorParams, mo):
    qdrant = QdrantClient(":memory:")

    qdrant.create_collection(
        collection_name="dishes",
        vectors_config=VectorParams(size=3, distance=Distance.COSINE),   # 3 維、餘弦距離
    )
    qdrant.upsert(
        collection_name="dishes",
        points=[
            PointStruct(id=i, vector=vec, payload={"name": name, "kind": kind, "price": price})
            for i, (name, vec, kind, price) in enumerate(DISHES)
        ],
    )
    dishes_count = qdrant.count("dishes").count
    mo.md(f"collection `dishes` 建好了，裡面有 **{dishes_count} 個點**。用 id 取回兩筆看看：\n\n"
          + "\n".join(f"- `{r.id}` → `{r.payload}`" for r in qdrant.retrieve("dishes", ids=[0, 7])))
    return dishes_count, qdrant


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 3️⃣ 最近鄰查詢：「我想吃這種口味的」

    `query_points(collection, query=向量, limit=k)` 回傳最相似的 k 個點，每個帶 `score`
    （Cosine 模式下 1.0 = 方向完全相同）。拉動三支拉桿組出你的口味向量，
    看推薦怎麼變——試試「酸辣」`[0.2, 0.7, 0.9]`、「純甜」`[1, 0, 0]`。
    """
    )
    return


@app.cell
def _(mo):
    sweet = mo.ui.slider(0, 1, step=0.05, value=0.2, label="sweet 甜", show_value=True)
    sour = mo.ui.slider(0, 1, step=0.05, value=0.7, label="sour 酸", show_value=True)
    spicy = mo.ui.slider(0, 1, step=0.05, value=0.9, label="spicy 辣", show_value=True)
    mo.hstack([sweet, sour, spicy])
    return sour, spicy, sweet


@app.cell
def _(mo, qdrant, sour, spicy, sweet):
    taste_query = [sweet.value, sour.value, spicy.value]
    _hits = qdrant.query_points(collection_name="dishes", query=taste_query, limit=3).points
    mo.vstack([
        mo.md(f"查詢向量 `{taste_query}` 的前 3 名："),
        mo.ui.table([{"rank": i + 1, "name": h.payload["name"], "score": round(h.score, 3),
                      "kind": h.payload["kind"], "price": h.payload["price"]} for i, h in enumerate(_hits)],
                    selection=None),
    ])
    return (taste_query,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 4️⃣ 過濾：相似度 + 條件同時成立

    「我想喝酸酸辣辣的**飲料**」——向量負責「酸辣」，payload 過濾負責「飲料」。
    `query_filter=Filter(must=[...])` 裡可以放等值（`MatchValue`）、範圍（`Range`）等條件，
    Qdrant 會**先篩再排**，不是撈前 k 名再丟掉不合的（那樣可能一筆都不剩）。
    """
    )
    return


@app.cell
def _(FieldCondition, Filter, MatchValue, Range, mo, qdrant):
    _sour_spicy = [0.2, 0.7, 0.9]
    _sweet = [0.9, 0.1, 0.0]

    only_drinks = qdrant.query_points(
        collection_name="dishes", query=_sour_spicy, limit=3,
        query_filter=Filter(must=[FieldCondition(key="kind", match=MatchValue(value="drink"))]),
    ).points
    cheap_sweet = qdrant.query_points(
        collection_name="dishes", query=_sweet, limit=3,
        query_filter=Filter(must=[FieldCondition(key="price", range=Range(lte=100))]),
    ).points

    def _fmt(hits):
        return "、".join(f"{h.payload['name']}（{h.score:.2f}）" for h in hits)

    mo.md(
        f"""
    | 需求 | 向量 | 過濾 | 結果（score） |
    |---|---|---|---|
    | 酸辣的飲料 | `{_sour_spicy}` | `kind == "drink"` | {_fmt(only_drinks)} |
    | 100 元以內的甜食 | `{_sweet}` | `price <= 100` | {_fmt(cheap_sweet)} |

    注意第一列：沒有任何飲料真的「辣」，所以分數都不高（最高 {only_drinks[0].score:.2f}）——
    但在「飲料」這個子集合裡，檸檬紅茶確實是最接近酸辣的。分數是**相對**的，解讀時要看門檻。
    """
    )
    return cheap_sweet, only_drinks


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 5️⃣ 距離度量：Cosine、Euclid、Dot 差在哪

    建 collection 時選的 `distance` 決定「像」怎麼算：

    - **Cosine**：只看**方向**、不看長度。`[0.1, 0.7, 0.8]` 和 `[0.2, 1.4, 1.6]` 分數相同。文字 embedding 幾乎都用它。
    - **Euclid**：直線距離，**越小越近**（所以分數是距離，排序方向相反）。
    - **Dot**：內積，方向對＋長度大分數就高；向量都已正規化成長度 1 時，Dot ＝ Cosine。

    同一組資料、同一個查詢，三種度量各建一個 collection 比比看：
    """
    )
    return


@app.cell
def _(DISHES, Distance, PointStruct, QdrantClient, VectorParams, mo):
    _q = [0.2, 0.7, 0.9]
    _rows = []
    for _dist in (Distance.COSINE, Distance.EUCLID, Distance.DOT):
        _c = QdrantClient(":memory:")   # 每種度量各自一個小庫
        _c.create_collection("d", vectors_config=VectorParams(size=3, distance=_dist))
        _c.upsert("d", points=[PointStruct(id=i, vector=v, payload={"name": n}) for i, (n, v, _, _) in enumerate(DISHES)])
        _hits = _c.query_points("d", query=_q, limit=3).points
        _rows.append({"distance": _dist.value,
                      "top-3": " → ".join(f"{h.payload['name']} ({h.score:.3f})" for h in _hits),
                      "score 意義": {"Cosine": "1 = 同方向", "Euclid": "0 = 同一點（越小越近）", "Dot": "內積（越大越像）"}[_dist.value]})
    mo.vstack([mo.md(f"查詢 `{_q}`（酸辣）在三種度量下的前 3 名："), mo.ui.table(_rows, selection=None)])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 6️⃣ 換真的向量：用自然語言查菜單

    口味向量是我們手填的，真實應用的向量來自 **embedding 模型**。這裡用上一課的 LiteLLM gateway
    呼叫 `qwen3-embedding-0.6b`，把八道菜的**名字**各變成 1024 維向量，存進一個新的 collection
    （`size=1024`）。然後用一句話當查詢——查詢本身也要先經過**同一個**模型變成向量，
    再丟給 Qdrant 找最近鄰。

    這就是語意搜尋：沒有任何關鍵字比對，「想喝冰冰甜甜的飲料」找得到「珍珠奶茶」。
    """
    )
    return


@app.cell
def _(DISHES, Distance, OpenAI, PointStruct, VectorParams, mo, qdrant):
    llm_gateway = OpenAI(
        base_url="https://litellm.itsmygo.uk/v1",   # 公開端點
        api_key="sk-FiIRnuzLH7ypgf29LTpHNw",        # 教學用 virtual key（只開免費模型，課後撤銷）
    )
    EMBED_MODEL = "qwen3-embedding-0.6b"

    def embed(texts):
        """把一串文字變成向量（一次 API 呼叫，批次處理）。"""
        _resp = llm_gateway.embeddings.create(model=EMBED_MODEL, input=texts)
        return [d.embedding for d in _resp.data]

    dish_names = [n for n, _, _, _ in DISHES]
    dish_vectors = embed(dish_names)

    qdrant.create_collection("dishes_real", vectors_config=VectorParams(size=len(dish_vectors[0]), distance=Distance.COSINE))
    qdrant.upsert("dishes_real", points=[
        PointStruct(id=i, vector=vec, payload={"name": dish_names[i]}) for i, vec in enumerate(dish_vectors)
    ])
    mo.md(f"八道菜名 → 八個 **{len(dish_vectors[0])} 維**向量，已存進 `dishes_real`。")
    return EMBED_MODEL, dish_names, dish_vectors, embed, llm_gateway


@app.cell
def _(embed, mo, qdrant):
    _rows = []
    for _q in ["想喝冰冰甜甜的飲料", "辣的湯", "飯後甜點", "酸的東西"]:
        _hits = qdrant.query_points("dishes_real", query=embed([_q])[0], limit=3).points
        _rows.append({"查詢": _q, "top-3": " → ".join(f"{h.payload['name']} ({h.score:.2f})" for h in _hits)})
    mo.ui.table(_rows, selection=None)
    return


@app.cell
def _(mo):
    free_query = mo.ui.text(value="下雨天想吃熱呼呼的", label="用你的話查菜單", full_width=True)
    free_query
    return (free_query,)


@app.cell
def _(embed, free_query, mo, qdrant):
    mo.stop(not free_query.value.strip(), mo.md("_輸入一句話試試。_"))
    _hits = qdrant.query_points("dishes_real", query=embed([free_query.value])[0], limit=3).points
    mo.md("「" + free_query.value + "」→ " + " → ".join(f"**{h.payload['name']}**（{h.score:.2f}）" for h in _hits))
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    注意分數的尺度變了：真實 embedding 的「相關」大約落在 0.5–0.8，「不相關」也有 0.3–0.5，
    不像口味向量那麼極端。做 RAG 時門檻要用自己的資料實測，不能憑感覺設 0.9。

    ## 🏆 延伸挑戰

    1. **LEVEL 1**：在 1️⃣ 的 `DISHES` 加兩道你喜歡的菜（自己填口味向量），重跑 2️⃣，
       再用 3️⃣ 的拉桿看它們什麼時候會被推薦。
    2. **LEVEL 2**：4️⃣ 加一個複合條件：`kind == "food"` **而且** `price <= 150`
       （`Filter(must=[條件A, 條件B])`），查「甜的」。再試 `should`（任一成立）與 `must_not`。
    3. **LEVEL 3**：6️⃣ 的 payload 只存了名字。把 `kind` 與 `price` 也存進 `dishes_real`，
       然後用自然語言查詢 + payload 過濾做「100 元以內、跟『提神』最相關的東西」。
       想一想：為什麼查詢與資料必須用同一個 embedding 模型？換成 `nemotron-3-embed-1b` 查會怎樣？

    帶得走：下載本檔後 `uvx marimo edit --sandbox qdrant-basics_ext.py` 在自己電腦繼續玩。
    下一課：**RAG**——把一份繁體中文手冊切段、向量化、存進 Qdrant，讓模型「先翻手冊再回答」。
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    # 挑戰的折疊解答：先自己做再打開。LEVEL 1/2 是可直接貼進新 cell 的完整程式碼，LEVEL 3 給方向與驗證方法。
    mo.accordion(
        {
            "💡 LEVEL 1 參考解答：加兩道菜": mo.md(
                r"""
    最省事的做法是直接改 1️⃣ 那格的 `DISHES`——marimo 會自動重跑所有依賴它的格子（建庫、拉桿查詢、散佈圖）。
    例如加一道甜甜的冰品、一道偏辣的菜：

    ```python
    ("芒果冰", [0.85, 0.30, 0.00], "dessert", 120),
    ("宮保雞丁", [0.30, 0.20, 0.75], "food", 160),
    ```

    不想動原格也可以新開一格、用 `upsert` 直接加點（id 接著排 8、9）：

    ```python
    _NEW = [("芒果冰", [0.85, 0.30, 0.00], "dessert", 120), ("宮保雞丁", [0.30, 0.20, 0.75], "food", 160)]
    qdrant.upsert("dishes", points=[
        PointStruct(id=8 + i, vector=v, payload={"name": n, "kind": k, "price": p})
        for i, (n, v, k, p) in enumerate(_NEW)
    ])
    qdrant.count("dishes").count, qdrant.query_points("dishes", query=[0.85, 0.3, 0.0], limit=3).points
    ```

    你應該看到：`count` 變 10；拉桿拉到甜 0.85／酸 0.3／辣 0 時芒果冰以 1.000 登頂、珍珠奶茶 0.974 第二；
    拉到辣 0.8／甜 0.3 時宮保雞丁第一、麻辣鍋 0.969 第二（實測）。Cosine 只看方向——
    你填的向量跟查詢向量「比例」一樣，分數就是 1.0，跟數值大小無關。
    """
            ),
            "💡 LEVEL 2 參考解答：must／should／must_not": mo.md(
                r"""
    ```python
    _sweet = [0.9, 0.1, 0.0]
    _f_must = Filter(must=[                                   # 兩個條件都要成立
        FieldCondition(key="kind", match=MatchValue(value="food")),
        FieldCondition(key="price", range=Range(lte=150)),
    ])
    _f_should = Filter(should=[                               # 任一成立即可
        FieldCondition(key="kind", match=MatchValue(value="drink")),
        FieldCondition(key="kind", match=MatchValue(value="dessert")),
    ])
    _f_not = Filter(must_not=[FieldCondition(key="kind", match=MatchValue(value="food"))])   # 排除

    def _show(f):
        return " → ".join(f"{h.payload['name']}({h.score:.2f}, {h.payload['kind']}, {h.payload['price']})"
                          for h in qdrant.query_points("dishes", query=_sweet, limit=3, query_filter=f).points)

    mo.md(f"- must：{_show(_f_must)}\n- should：{_show(_f_should)}\n- must_not：{_show(_f_not)}")
    ```

    你應該看到（原始八道菜）：

    - **must**（`food` 且 `<= 150`）：只回 **2 筆**——泰式酸辣湯 (0.27)、酸辣粉 (0.17)。`limit=3` 卻只有 2 筆，
      因為符合條件的食物只有兩道；分數都很低，因為沒有任何「甜的食物」在 150 元以內。這就是「先篩再排」。
    - **should**（飲料或甜點）：珍珠奶茶 (1.00) → 焦糖布丁 (1.00) → 蜂蜜檸檬。
    - **must_not**（不要食物）：在這組資料裡跟 should 的結果一樣——兩種寫法的集合剛好相同，但語意不同：
      資料多一個 `kind="soup"` 時 must_not 會把它納入、should 不會。
    """
            ),
            "💡 LEVEL 3 提示：真實向量 + payload 過濾、以及為什麼不能換模型": mo.md(
                r"""
    把 6️⃣ 那格的 payload 改成 `{"name": dish_names[i], "kind": DISHES[i][2], "price": DISHES[i][3]}` 存檔即可
    （整格會重跑，重新 embedding 一次）。然後：

    ```python
    _hits = qdrant.query_points(
        "dishes_real", query=embed(["提神"])[0], limit=3,
        query_filter=Filter(must=[FieldCondition(key="price", range=Range(lte=100))]),
    ).points
    [(h.payload["name"], round(h.score, 2), h.payload["price"]) for h in _hits]
    ```

    怎麼驗證：實測「提神」＋ `price <= 100` 回珍珠奶茶 (0.40)、檸檬紅茶 (0.39)、酸辣粉 (0.39)；不加過濾時
    第二名會是 350 元的麻辣鍋——過濾確實生效。注意分數擠在 0.39–0.40：菜名只有三四個字，
    「提神」跟任何一道菜都不算強相關，真實應用要給 payload 放更多描述文字（下一課的 RAG 就是這樣做）。

    **換模型查詢**：`llm_gateway.embeddings.create(model="nemotron-3-embed-1b", input=["提神"]).data[0].embedding`
    回 **2048 維**，丟進 1024 維的 collection 會直接炸
    `ValueError: shapes (8,1024) and (2048,) not aligned`（記憶體模式；正式伺服器回 400 `Wrong input: Vector dimension error`）。
    就算維度剛好相同也不行——兩個模型的座標軸意義完全不同，距離毫無意義。
    **索引用哪個模型，查詢就必須用同一個模型**；換模型＝整個 collection 重建。
    """
            ),
        }
    )
    return


if __name__ == "__main__":
    app.run()
