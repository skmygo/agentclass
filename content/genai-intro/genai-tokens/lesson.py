import marimo

__generated_with = "0.23.16"
app = marimo.App(width="medium", app_title="Token、Embedding 與上下文窗（實驗場）")


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    # 🧪 Token、Embedding 與上下文窗（實驗場）

    這是本課的**實驗場**。左側教學讀到哪，就回到這裡動手做——
    每一格程式碼都可以**直接修改、立即重跑**（點格子右上的 ▶，或按 `Ctrl+Enter`）。
    改壞了也沒關係：重新整理頁面就會回到原版。

    這一課要親手摸四個地基名詞：**Token**（文字怎麼被切開）、**Embedding**（語意怎麼變成座標）、
    **Context Window**（模型一次能看多少）、**Autoregressive**（為什麼回答是一個字一個字蹦出來）。
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
    from itertools import pairwise

    import matplotlib.pyplot as plt
    import numpy as np
    return html_mod, np, pairwise, plt


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 1️⃣ Token：文字是怎麼被切開的

    模型看不懂「字」，只看得懂**編號**。Tokenizer 的工作就是把文字切成一小塊一小塊
    （token），每塊給一個編號。主流的切法叫 **BPE（Byte Pair Encoding）**，
    規則簡單到你可以在下面親手訓練一個：

    1. 一開始，每個字元自己是一塊
    2. 統計語料裡「哪兩塊最常相鄰出現」，把它們**黏成一塊**
    3. 重複第 2 步幾千次——常見的字串就變成一整塊，罕見的維持小塊

    下面的語料只有三個單字：`low` ×5、`newest` ×6、`widest` ×3。
    拉動「合併次數」，看 tokenizer 怎麼一步步學會把常見單字黏成一塊；
    再改「要切的詞」試一個**語料裡沒出現過的字**（例如 `lowest`）。
    """
    )
    return


@app.cell
def _(mo):
    n_merges = mo.ui.slider(start=0, stop=10, step=1, value=0, label="BPE 合併次數", show_value=True)
    probe_word = mo.ui.text(value="lowest", label="要切的詞（試試語料裡沒有的）")
    mo.vstack([n_merges, probe_word])
    return n_merges, probe_word


@app.cell
def _(pairwise):
    # ── 迷你 BPE：與經典演算法同款（word → 字元序列 + 詞尾記號，反覆合併最高頻相鄰對）──
    BPE_CORPUS = ("low " * 5 + "newest " * 6 + "widest " * 3).split()

    def bpe_train(words, n):
        vocab = {}
        for w in words:
            key = tuple(w) + ("</w>",)
            vocab[key] = vocab.get(key, 0) + 1
        merges = []
        for _ in range(n):
            pairs = {}
            for sym, freq in vocab.items():
                for a, b in pairwise(sym):
                    pairs[(a, b)] = pairs.get((a, b), 0) + freq
            if not pairs:
                break
            best = max(pairs, key=lambda p: (pairs[p], p))
            merges.append((best, pairs[best]))
            new_vocab = {}
            for sym, freq in vocab.items():
                out, i = [], 0
                while i < len(sym):
                    if i < len(sym) - 1 and (sym[i], sym[i + 1]) == best:
                        out.append(sym[i] + sym[i + 1])
                        i += 2
                    else:
                        out.append(sym[i])
                        i += 1
                new_vocab[tuple(out)] = freq
            vocab = new_vocab
        return merges, vocab

    def bpe_segment(word, merges):
        sym = list(word) + ["</w>"]
        for (a, b), _f in merges:
            out, i = [], 0
            while i < len(sym):
                if i < len(sym) - 1 and sym[i] == a and sym[i + 1] == b:
                    out.append(a + b)
                    i += 2
                else:
                    out.append(sym[i])
                    i += 1
            sym = out
        return sym
    return BPE_CORPUS, bpe_segment, bpe_train


@app.cell
def _(BPE_CORPUS, bpe_segment, bpe_train, html_mod, mo, n_merges, probe_word):
    _merges, _vocab = bpe_train(BPE_CORPUS, n_merges.value)
    _seg = bpe_segment(probe_word.value.strip() or "lowest", _merges)
    _merge_txt = ("、".join(f"`{a}`+`{b}`" for (a, b), _f in _merges) or "（還沒合併，全部是單一字元）")
    _chips = "".join(
        f'<span style="display:inline-block;background:#E8F0F7;border:1.5px solid #4C72B0;'
        f'border-radius:8px;padding:2px 10px;margin:2px;font-family:monospace;font-weight:700">'
        f"{html_mod.escape(s)}</span>"
        for s in _seg
    )
    mo.vstack([
        mo.md(f"**目前學到的合併規則**（依序）：{_merge_txt}"),
        mo.md(f"**「{probe_word.value.strip() or 'lowest'}」被切成 {len(_seg)} 個 token：**"),
        mo.Html(f"<div>{_chips}</div>"),
    ])
    return


@app.cell
def _(BPE_CORPUS, bpe_segment, bpe_train, np, plt):
    # 合併次數 0..10 各訓練一次，數整份語料被切成幾塊——常見字黏起來，總 token 數就下降
    _xs = np.arange(0, 11)
    _totals = []
    for _n in _xs:
        _m, _ = bpe_train(BPE_CORPUS, int(_n))
        _totals.append(sum(len(bpe_segment(w, _m)) for w in BPE_CORPUS))
    _fig, _ax = plt.subplots(figsize=(7.0, 3.6))
    _ax.plot(_xs, _totals, "o-", color="#4C72B0", linewidth=2.4, markersize=6, zorder=3)
    _ax.set_xlabel("BPE merges learned")
    _ax.set_ylabel("total tokens for the corpus")
    _ax.set_title("more merges -> frequent words become single tokens")
    _ax.grid(alpha=0.3)
    _fig.tight_layout()
    _fig
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    真實世界的 tokenizer（例如 GPT-4o 系列用的 `o200k_base`）就是這樣訓練出來的，
    只是語料是整個網路、合併了約 20 萬次。它對不同語言的「刀工」差很多——
    這是左頁開場那個實驗的原理：**同樣一句話，英文平均 4.4 個字元一刀，
    中文平均一個字就要挨 1.1 刀**（實測 `o200k_base`，2026-08）。
    Token 數直接決定 API 帳單與上下文用量，所以這件事跟錢有關。

    ## 2️⃣ Embedding：語意變成座標

    Tokenizer 給每塊文字一個編號，但編號 3421 和 3422 毫無關係。
    **Embedding 模型**把一段文字變成一個**高維向量**（一串浮點數），
    讓「意思相近」的文字在向量空間裡**距離相近**——這是語意搜尋與 RAG 的地基。

    下面 16 個短句的向量是**真的**：用 embedding 模型（jina-embed，1024 維）事先算好、
    壓縮打包進這一課（int8 量化，誤差 < 0.006）。這格把 1024 維用 PCA 壓到 2 維畫成地圖——
    四種顏色是四個語意群組（動物／交通工具／食物／情緒）：
    """
    )
    return


@app.cell
def _(np):
    import base64

    EMB_WORDS = ['一隻可愛的貓', '一隻忠心的狗', '一頭凶猛的老虎', '一隻跳來跳去的兔子', '一輛紅色的汽車', '一列高速的火車', '一架起飛的飛機', '一台共享腳踏車', '一杯熱拿鐵咖啡', '一塊草莓蛋糕', '一碗熱騰騰的拉麵', '一顆新鮮的蘋果', '今天心情很快樂', '今天覺得好悲傷', '氣得不想說話', '嚇得躲在棉被裡']
    EMB_LABELS_EN = ['cat', 'dog', 'tiger', 'rabbit', 'car', 'train', 'plane', 'bike', 'coffee', 'cake', 'ramen', 'apple', 'happy', 'sad', 'angry', 'scared']
    EMB_GROUPS = [0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3]
    EMB_B64 = "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"
    EMB_SCALES = [0.000978397, 0.000907992, 0.00113808, 0.00111761, 0.00136229, 0.000989774, 0.00101956, 0.00122669, 0.000833593, 0.00114878, 0.000968963, 0.00110959, 0.00151749, 0.00129223, 0.00118718, 0.00139872]
    EMB_DIM = 1024

    _q = np.frombuffer(base64.b64decode(EMB_B64), dtype=np.int8).reshape(len(EMB_WORDS), EMB_DIM)
    EMB_V = _q.astype(np.float32) * np.array(EMB_SCALES, dtype=np.float32)[:, None]
    EMB_N = EMB_V / np.linalg.norm(EMB_V, axis=1, keepdims=True)
    return EMB_GROUPS, EMB_LABELS_EN, EMB_N, EMB_V, EMB_WORDS


@app.cell
def _(EMB_GROUPS, EMB_LABELS_EN, EMB_V, np, plt):
    # PCA：中心化 + SVD 取前兩個主成分（真的算，不是示意圖）
    _Xc = EMB_V - EMB_V.mean(axis=0)
    _U, _S, _Vt = np.linalg.svd(_Xc, full_matrices=False)
    _P = _Xc @ _Vt[:2].T
    _palette = ["#4C72B0", "#DD8452", "#55A868", "#8172B2"]
    _names = ["animals", "transport", "food", "emotions"]
    _fig, _ax = plt.subplots(figsize=(7.0, 5.2))
    for _g in range(4):
        _idx = [_i for _i, _gg in enumerate(EMB_GROUPS) if _gg == _g]
        _ax.scatter(_P[_idx, 0], _P[_idx, 1], s=90, color=_palette[_g],
                    edgecolor="#1C2B33", linewidth=1.1, zorder=3, label=_names[_g])
    for _i, _lab in enumerate(EMB_LABELS_EN):
        _ax.annotate(_lab, (_P[_i, 0], _P[_i, 1]), xytext=(6, 5),
                     textcoords="offset points", fontsize=9, fontweight="bold")
    _ax.set_title("16 real 1024-d embeddings, PCA to 2-D")
    _ax.set_xlabel("PC1")
    _ax.set_ylabel("PC2")
    _ax.grid(alpha=0.25)
    _ax.legend(fontsize=9, loc="best")
    _fig.tight_layout()
    _fig
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    情緒句自成一國、動物擠在一起——但注意：**2 維地圖是被壓扁的世界**
    （1024 維硬壓到 2 維，交通和食物就擠在一塊了）。
    真正的相似度要回到原始向量算 **cosine 相似度**（夾角有多小）。
    挑兩句比比看，再看看誰是誰的最近鄰：
    """
    )
    return


@app.cell
def _(EMB_WORDS, mo):
    pick_a = mo.ui.dropdown(options=EMB_WORDS, value=EMB_WORDS[0], label="句子 A")
    pick_b = mo.ui.dropdown(options=EMB_WORDS, value=EMB_WORDS[1], label="句子 B")
    mo.hstack([pick_a, pick_b], justify="start", gap=2)
    return pick_a, pick_b


@app.cell
def _(EMB_N, EMB_WORDS, mo, np, pick_a, pick_b):
    _ia, _ib = EMB_WORDS.index(pick_a.value), EMB_WORDS.index(pick_b.value)
    _cos = float(EMB_N[_ia] @ EMB_N[_ib])
    _sims = EMB_N @ EMB_N[_ia]
    _order = np.argsort(-_sims)
    _nn = [(EMB_WORDS[_j], float(_sims[_j])) for _j in _order if _j != _ia][:3]
    _nn_rows = "\n".join(f"    {_k+1}. 「{_w}」 cosine = {_s:.3f}" for _k, (_w, _s) in enumerate(_nn))
    _hint = ("——很像！" if _cos > 0.35 else "——普通接近。" if _cos > 0.2 else "——不太相干。")
    mo.md(
        f"""
    **cosine(「{pick_a.value}」, 「{pick_b.value}」) = {_cos:.3f}**{_hint}

    「{pick_a.value}」的最近鄰（全語料排序）：

{_nn_rows}

    這個「算相似、排名次」的動作，就是第 7 課 RAG 檢索的全部數學。
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 3️⃣ Context Window：模型的工作記憶

    模型一次能「看到」的 token 上限叫**上下文窗（context window）**。
    prompt ＋ 對話歷史 ＋ 塞進去的文件 ＋ 模型的回答，**全部**要擠在這個窗裡；
    超過的部分不是「記性變差」，是**根本沒被送進模型**。

    拉一下你要塞的文件量，看它跟常見模型的窗有多大差距
    （中文 token 估算用第 1 節的實測刀工：平均 1 字 ≈ 1.14 token）：
    """
    )
    return


@app.cell
def _(mo):
    doc_pages = mo.ui.slider(start=1, stop=2000, step=1, value=40,
                             label="你要塞進去的中文文件（頁，每頁約 600 字）", show_value=True)
    doc_pages
    return (doc_pages,)


@app.cell
def _(doc_pages, np, plt):
    # 模型上下文窗（公開規格）；文件 token 估算：600 字/頁 × 1.14 token/字（o200k 實測比率）
    _models = ["Llama 3 (8K)", "Qwen3 32K", "Llama 3.1 (128K)", "GPT-4o (128K)",
               "Claude Haiku 4.5 (200K)", "Claude Opus 5 (1M)"]
    _windows = np.array([8_192, 32_768, 131_072, 128_000, 200_000, 1_000_000])
    _doc_tokens = doc_pages.value * 600 * 1.14
    _fits = _windows >= _doc_tokens
    _colors = ["#55A868" if _f else "#C44E52" for _f in _fits]
    _fig, _ax = plt.subplots(figsize=(7.2, 4.2))
    _ax.barh(_models, _windows, color=_colors, edgecolor="#1C2B33", linewidth=1.1, zorder=3)
    _ax.axvline(_doc_tokens, color="#1C2B33", linestyle="--", linewidth=2.0, zorder=4)
    _ax.text(_doc_tokens * 1.06, -0.42, f"your doc ~{_doc_tokens/1000:.0f}K tokens",
             fontsize=10, fontweight="bold", color="#1C2B33")
    _ax.set_xscale("log")
    _ax.set_xlabel("context window (tokens, log scale)")
    _ax.set_title("green = your document fits, red = it does not")
    _ax.grid(axis="x", alpha=0.3)
    _fig.tight_layout()
    _fig
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    兩件值得記住的事：

    - **窗越大不等於越聰明**——塞一堆無關內容反而稀釋重點（第 6 課的 context engineering
      就在管這件事）。
    - **窗越大，代價越重**——上下文一長，推理時要維護的 KV cache 記憶體暴增
      （這是第 3 課的主線）。

    ## 4️⃣ Autoregressive：一次吐一個 token

    LLM 生成文字的方式是**自迴歸**：看著前面所有 token，算出「下一個 token 的機率分布」，
    抽一個出來，接到句尾，再算下一個……你看到回答一個字一個字蹦出來，不是動畫效果，
    是它**真的一次只算一個**。

    下面用 12 句小語料訓練一個「看前一個字、猜下一個字」的迷你模型
    （真的統計、真的抽樣——當然，它比 LLM 笨十億倍，但生成迴圈一模一樣）：
    """
    )
    return


@app.cell
def _(pairwise):
    # 迷你自迴歸模型：字元 bigram 計數（P(下一字 | 前一字)）
    AR_CORPUS = [
        "今天天氣很好", "今天天氣不好", "今天心情很好", "明天天氣很好",
        "我今天很開心", "我明天要上班", "我今天要上學", "天氣好就出去玩",
        "心情不好就吃蛋糕", "我很喜歡吃蛋糕", "我很喜歡貓", "貓很可愛",
    ]
    AR_COUNTS = {}
    for _s in AR_CORPUS:
        _seq = "^" + _s + "$"
        for _a, _b in pairwise(_seq):
            AR_COUNTS.setdefault(_a, {}).setdefault(_b, 0)
            AR_COUNTS[_a][_b] += 1
    return (AR_COUNTS,)


@app.cell
def _(mo):
    ar_temp = mo.ui.slider(start=0.1, stop=2.0, step=0.1, value=1.0,
                           label="temperature（越低越保守、越高越狂野）", show_value=True)
    ar_seed = mo.ui.slider(start=1, stop=30, step=1, value=1, label="抽樣批次（拉一下＝重抽）", show_value=True)
    mo.vstack([ar_temp, ar_seed])
    return ar_seed, ar_temp


@app.cell
def _(AR_COUNTS, ar_seed, ar_temp, html_mod, mo, np):
    _rng = np.random.default_rng(ar_seed.value)
    _steps = []
    _cur = "^"
    for _t in range(20):
        _dist = AR_COUNTS.get(_cur)
        if not _dist:
            break
        _chars = list(_dist)
        _w = np.array([_dist[_c] for _c in _chars], dtype=float)
        _p = _w ** (1.0 / ar_temp.value)
        _p = _p / _p.sum()
        _ch = str(_rng.choice(_chars, p=_p))
        _steps.append((_cur, _chars, _p, _ch))
        if _ch == "$":
            break
        _cur = _ch

    _out = "".join(_ch for _c, _cs, _p, _ch in _steps if _ch != "$")
    _cur2, _chars2, _p2, _pick2 = _steps[-1]
    _rows = "".join(
        f'<div style="display:flex;align-items:center;gap:8px;margin:3px 0">'
        f'<span style="width:2.2em;font-weight:800;font-family:monospace">'
        f"{html_mod.escape('結束' if _c == '$' else _c)}</span>"
        f'<div style="flex:1;background:#EEF1F4;border-radius:6px;height:18px;overflow:hidden">'
        f'<div style="width:{_pp*100:.1f}%;height:100%;background:{"#DD8452" if _c == _pick2 else "#4C72B0"}"></div></div>'
        f'<span style="font-family:monospace;font-size:12px;width:4em">{_pp:.2f}</span></div>'
        for _c, _pp in sorted(zip(_chars2, _p2), key=lambda x: -x[1])
    )
    mo.vstack([
        mo.md(f"**生成結果：「{_out}」**（從句首記號 `^` 開始，一次抽一個字，抽到結束記號停）"),
        mo.md(f"最後一步：看著「{'句首' if _cur2 == '^' else _cur2}」，下一個字的機率分布（橘色＝這次抽中的）："),
        mo.Html(f"<div style='max-width:420px'>{_rows}</div>"),
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    多拉幾次「抽樣批次」：同一個分布，每次抽出來的句子不一樣——這就是為什麼
    **同一個問題 LLM 每次答得不完全一樣**。把 temperature 壓到 0.1，它幾乎只挑最高機率的字，
    輸出就變穩定（也變無聊）。

    也順便看出了自迴歸的兩個代價：**串行**（第 N 個字一定要等第 N−1 個字）、
    **重複計算**（每一步都要重看整段前文——所以才需要 KV cache，第 3 課見）。

    ## 5️⃣ 你的實驗區

    下面這格是你的，改完按 ▶ 重跑。挑戰在左頁「換你動手」，做完再開解答對照。
    """
    )
    return


@app.cell
def _(AR_COUNTS, BPE_CORPUS, bpe_segment, bpe_train):
    # ===== 你的實驗區 =====
    # LEVEL 1 起點：改 probe，看不同合併次數下它被切成幾塊
    probe = "newest"
    my_merges, _ = bpe_train(BPE_CORPUS, 10)
    print("BPE:", probe, "→", bpe_segment(probe, my_merges))

    # LEVEL 2 起點：語料裡「天」後面接過哪些字？
    print("P(下一字 | 天) 的計數：", AR_COUNTS.get("天"))
    return


@app.cell(hide_code=True)
def _(mo):
    mo.accordion(
        {
            "💡 LEVEL 1 參考解答": mo.md(
                r"""
    把第 1 節的「要切的詞」改成 `wider`，合併次數拉到 10：

    - `widest` 在語料出現過 → 學到 `wi`、`widest</w>` 之類的合併 → 切得很整
    - `wider` 沒出現過 → 只能用學過的碎塊拼：`wi` + `d` + `e` + `r</w>` 一類的組合

    這就是 BPE 的核心性格：**沒看過的詞不會炸掉，只是切得比較碎**（token 數變多、變貴）。
    中文在 `o200k_base` 上平均 1 字 ≈ 1.14 token，就是同一個現象的放大版。
    """
            ),
            "💡 LEVEL 2 參考解答": mo.md(
                r"""
    實驗區印出的計數：「天」後面接過「氣」4 次、「天」3 次、「要」2 次、
    「心」「很」各 1 次——最常接的是「氣」。把 temperature 壓到 0.1 之後，
    每一步幾乎都挑最高機率的字，所以生成幾乎每次都走「天→氣」這條路；
    拉到 2.0 之後低機率的字也常被抽中，句子就開始亂走。

    對應到真的 LLM：`temperature=0` 拿來要穩定輸出（分類、抽欄位），
    高 temperature 拿來要多樣性（brainstorm、寫文案）。
    """
            ),
            "💡 LEVEL 3 提示": mo.md(
                r"""
    在第 2 節挑「一杯熱拿鐵咖啡」，看它的最近鄰——第一名是「一碗熱騰騰的拉麵」
    （cosine 0.423，遠遠甩開其他句子），而同屬「食物組」的「一塊草莓蛋糕」只有 0.143，
    甚至排在「一隻可愛的貓」（0.171）後面。

    這不是 bug：embedding 模型看的是**整句的語意組合**（「熱」「一杯／一碗」這種
    當下情境的相似），不是你心裡的目錄分類標籤。我們畫 2D 地圖時用顏色把它們
    分成四組，但向量空間自己不知道有這回事。

    帶走的判斷：**RAG 檢索到的「相近」是語意相近，不是目錄分類**——
    寫 chunk 與查詢的措辭會直接影響檢索品質，第 7 課會看到這件事的實際後果。
    """
            ),
        }
    )
    return


if __name__ == "__main__":
    app.run()
