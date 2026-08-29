import marimo

__generated_with = "0.23.16"
app = marimo.App(width="medium", app_title="看懂 KV Cache（實驗場）")


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    # 🧪 看懂 KV Cache（實驗場）

    左邊讀到哪，就回到這裡動手。這裡沒有真的大模型——只有一個**十六維的玩具注意力層**，
    但它的算法和真模型一模一樣：Q 查 K、加權取 V、K/V 存起來重複用。
    每個實驗都有滑桿或選單可以拉，拉完立刻重算——數字都是當場算出來的。
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
    import matplotlib.pyplot as plt
    import numpy as np
    return np, plt


@app.cell
def _():
    # 全課共用的語義色：藍＝快取起來的 K/V、橘＝用一次就丟的 Q、綠＝有快取、紅＝重算／爆掉
    C_KV, C_Q, C_CACHE, C_RECOMP = "#4C72B0", "#DD8452", "#55A868", "#C44E52"
    return C_CACHE, C_KV, C_Q, C_RECOMP


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 1️⃣ Prefill 讀題、Decode 寫答案

    模型回答問題分兩步。**Prefill** 把你的提示詞一次全部讀進去——所有 token 的 K、V
    在同一次矩陣乘法裡算完，位置之間沒有先後依賴，所以快。
    **Decode** 一次只生一個字，生完再生下一個，因為下一個字要看前面所有字。

    下面兩根柱子是每一步的兩種工作量：**藍＝這一步要算幾個 token 的 K/V**、
    **橘＝這一步要讀多少格快取**。拉拉看生成長度，注意兩根柱子的走向完全相反。
    """
    )
    return


@app.cell
def _(mo):
    prompt_tokens = mo.ui.slider(
        start=2, stop=16, step=1, value=4,
        label="提示長度（Prefill 一次讀完幾個 token）", show_value=True,
    )
    decode_steps = mo.ui.slider(
        start=1, stop=16, step=1, value=6,
        label="生成長度（Decode 逐字寫幾個 token）", show_value=True,
    )
    mo.vstack([prompt_tokens, decode_steps])
    return decode_steps, prompt_tokens


@app.cell
def _(C_KV, C_Q, decode_steps, np, plt, prompt_tokens):
    _p, _m = prompt_tokens.value, decode_steps.value
    _labels = ["Prefill"] + [f"D{_i}" for _i in range(1, _m + 1)]
    _computed = [_p] + [1] * _m                       # 這一步算幾個 token 的 K/V
    _read = [_p] + [_p + _i for _i in range(1, _m + 1)]  # 這一步要讀多少格快取
    _x = np.arange(len(_labels))

    _fig, _ax = plt.subplots(figsize=(7.4, 3.7))
    _ax.bar(_x - 0.2, _computed, width=0.4, color=C_KV, label="K/V computed this step")
    _ax.bar(_x + 0.2, _read, width=0.4, color=C_Q, label="cache entries read this step")
    _ax.set_xticks(_x)
    _ax.set_xticklabels(_labels, fontsize=9)
    _ax.set_ylabel("tokens")
    _ax.set_title("Prefill does it all at once; every decode step reads more, computes 1")
    _ax.legend(fontsize=9)
    _ax.grid(axis="y", alpha=0.3)
    _fig.tight_layout()
    _fig
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    藍柱在 Decode 階段永遠是 **1**，橘柱卻一路長高——每生一個字，都要把**整個快取**
    從記憶體讀一遍，只換來一個 token 的計算量。算力大量閒著，卡住的是記憶體頻寬。

    （這個「算力閒著等記憶體」的怪現象先記著，第 6 課的投機解碼會回來收割它。）
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 2️⃣ Q、K、V：查表這件事長什麼樣

    每個字都會產生三個向量：**Q**「我想找什麼」、**K**「我是講什麼的」、**V**「我實際的內容」。
    新字拿自己的 Q 去比對前面每個字的 K，得到一組加起來等於 1 的權重，再按權重把 V 加權取出來。

    下面是一個真的算得出來的玩具注意力層：16 維、隨機權重、旋轉式位置編碼。
    權重是隨機的，所以**數字沒有語意**——要看的是「查表」的形狀。
    """
    )
    return


@app.cell
def _(np):
    # ── 玩具注意力層（全 notebook 共用）────────────────────────────
    D_MODEL = 16
    _w = np.random.default_rng(7)
    W_Q = _w.normal(size=(D_MODEL, D_MODEL)) / np.sqrt(D_MODEL)
    W_K = _w.normal(size=(D_MODEL, D_MODEL)) / np.sqrt(D_MODEL)
    W_V = _w.normal(size=(D_MODEL, D_MODEL)) / np.sqrt(D_MODEL)
    W_O = _w.normal(size=(D_MODEL, D_MODEL)) / np.sqrt(D_MODEL)
    W_K2 = _w.normal(size=(D_MODEL, D_MODEL)) / np.sqrt(D_MODEL)

    def char_vec(ch):
        """每個字一個固定的隨機向量（用字碼當種子，所以任何字都能用、而且每次都一樣）。"""
        return np.random.default_rng(ord(ch)).normal(size=D_MODEL)

    def embed(text):
        return np.stack([char_vec(_c) for _c in text])

    def rope(x, pos):
        """把位置混進向量：每兩維一組，轉一個和位置成正比的角度。"""
        _theta = np.power(10000.0, -2.0 * np.arange(D_MODEL // 2) / D_MODEL)
        _ang = np.asarray(pos, dtype=float)[:, None] * _theta[None, :]
        _c, _s = np.cos(_ang), np.sin(_ang)
        out = np.empty_like(x)
        out[:, 0::2] = x[:, 0::2] * _c - x[:, 1::2] * _s
        out[:, 1::2] = x[:, 0::2] * _s + x[:, 1::2] * _c
        return out

    def causal_softmax(scores):
        _m = np.max(scores, axis=-1, keepdims=True)
        _e = np.exp(scores - _m)
        return _e / _e.sum(axis=-1, keepdims=True)

    def attn_parts(text, offset=0):
        """回傳這段文字的 Q/K/V、注意力權重，以及「深一層」的 K。"""
        _h0 = embed(text)
        _pos = np.arange(offset, offset + len(text))
        _q = rope(_h0 @ W_Q, _pos)
        _k = rope(_h0 @ W_K, _pos)          # 淺層 K：位置已經混進去了
        _v = _h0 @ W_V
        _s = _q @ _k.T / np.sqrt(D_MODEL)
        _s = np.where(np.triu(np.ones((len(text), len(text))), 1).astype(bool), -np.inf, _s)
        _a = causal_softmax(_s)
        _h1 = _h0 + (_a @ _v) @ W_O         # 殘差：每個位置都混進了「前面所有字」
        return {"q": _q, "k": _k, "v": _v, "attn": _a, "k_deep": rope(_h1 @ W_K2, _pos)}

    def rel_err(a, b):
        """相對誤差（%）：兩個向量差多少。0 就是一模一樣。"""
        return float(np.linalg.norm(a - b) / np.linalg.norm(b) * 100)

    SEQ = "今天氣很熱"
    return D_MODEL, SEQ, W_K, W_Q, W_V, attn_parts, embed, rel_err, rope


@app.cell
def _(SEQ, mo):
    new_token = mo.ui.dropdown(
        options={f"t{_i}（{_c}）": _i for _i, _c in enumerate(SEQ)},
        value=f"t{len(SEQ) - 1}（{SEQ[-1]}）",
        label=f"把哪一個字當成「正在生成的新字」（序列＝{SEQ}）",
    )
    new_token
    return (new_token,)


@app.cell
def _(C_KV, C_RECOMP, SEQ, attn_parts, new_token, np, plt):
    _i = new_token.value
    _w = attn_parts(SEQ)["attn"][_i]
    _top = int(_w.argmax())
    _colors = [C_RECOMP if _j == _top else C_KV for _j in range(len(SEQ))]

    _fig, _ax = plt.subplots(figsize=(7.4, 3.4))
    _ax.bar(np.arange(len(SEQ)), _w, color=_colors)
    _ax.set_xticks(np.arange(len(SEQ)))
    _ax.set_xticklabels([f"t{_j}" for _j in range(len(SEQ))])
    _ax.set_ylim(0, 1)
    _ax.set_ylabel("attention weight")
    _ax.set_xlabel(f"K of each earlier token   (query = t{_i})")
    _ax.set_title(f"t{_i} asks with its Q, gets weights over t0..t{_i} (sum = 1.00)")
    _ax.grid(axis="y", alpha=0.3)
    _fig.tight_layout()
    _fig
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    往前拉這個下拉選單，你會看到權重的長度跟著變短：**新字只看得到自己和前面的字**，
    後面的位置一律是 0。這就是為什麼 K、V 一旦算好就不會再變——
    後來的字影響不到前面的字。

    注意誰是誰的：**Q 是「當下這個新字」的**，只有一個；**K 和 V 是「前面每一個字」的**，
    是被查的那張表。
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 3️⃣ 沒有快取：每生一個字，前面全部重算一遍

    如果不存 K、V，那每生一個新字，都得把整串重新跑一次才拿得到前面所有字的 K、V。
    第 1 步算 p+1 個、第 2 步算 p+2 個……**總計算量隨長度平方成長**。
    有快取則是每步只算 1 個，線性。

    拉拉看兩根滑桿，看紅線怎麼把綠線甩開：
    """
    )
    return


@app.cell
def _(mo):
    prompt_len = mo.ui.slider(
        start=0, stop=2000, step=50, value=200, label="提示長度（token）", show_value=True
    )
    gen_len = mo.ui.slider(
        start=10, stop=2000, step=10, value=300, label="生成長度（token）", show_value=True
    )
    mo.vstack([prompt_len, gen_len])
    return gen_len, prompt_len


@app.cell
def _(np):
    def kv_computed(prompt_len_, gen_len_, cached):
        """整趟生成總共算了幾個 token 的 K/V。"""
        if cached:
            return prompt_len_ + gen_len_
        _steps = np.arange(1, gen_len_ + 1)
        return int(prompt_len_ + np.sum(prompt_len_ + _steps))
    return (kv_computed,)


@app.cell
def _(C_CACHE, C_RECOMP, gen_len, np, plt, prompt_len):
    _p, _m = prompt_len.value, gen_len.value
    _t = np.arange(1, _m + 1)
    _no_cache = _p + np.cumsum(_p + _t)
    _with_cache = _p + _t

    _fig, _ax = plt.subplots(figsize=(7.4, 3.9))
    _ax.plot(_t, _no_cache, color=C_RECOMP, lw=2.5, label="no cache (recompute everything)")
    _ax.plot(_t, _with_cache, color=C_CACHE, lw=2.5, label="KV cache (new token only)")
    _ax.fill_between(_t, _with_cache, _no_cache, color=C_RECOMP, alpha=0.10)
    _ax.set_xlabel("tokens generated")
    _ax.set_ylabel("total token K/V computations")
    _ax.set_title(f"prompt {_p} + generate {_m}: {_no_cache[-1] / _with_cache[-1]:.0f}x more work without a cache")
    _ax.legend(fontsize=9)
    _ax.grid(alpha=0.3)
    _fig.tight_layout()
    _fig
    return


@app.cell
def _(gen_len, kv_computed, mo, prompt_len):
    _p, _m = prompt_len.value, gen_len.value
    _a = kv_computed(_p, _m, cached=False)
    _b = kv_computed(_p, _m, cached=True)
    mo.md(
        f"""
    提示 **{_p}** 個 token、再生成 **{_m}** 個：

    - 沒有快取：總共要算 **{_a:,}** 個 token 的 K/V
    - 有快取：**{_b:,}** 個
    - 多做了 **{_a / _b:.0f} 倍**的工

    把生成長度拉長一格，紅線的成長速度就明顯不一樣——那是平方項在動。
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 4️⃣ 有快取：存起來，而且答案一模一樣

    快取不是近似、不是壓縮、不會掉品質——**它算出來的東西和重算完全相同**。
    下面真的跑兩遍：一遍每步重算整串，一遍只算新字、其餘查快取，然後比對兩邊的輸出。
    """
    )
    return


@app.cell
def _(D_MODEL, SEQ, W_K, W_Q, W_V, attn_parts, embed, mo, np, rope):
    _p = 3  # 前 3 個字當 prefill，後面逐字生成

    # (A) 沒有快取：每一步把整串重跑一次
    _outs_slow, _slow_steps = [], []
    for _t in range(_p, len(SEQ) + 1):
        _part = attn_parts(SEQ[:_t])
        _outs_slow.append((_part["attn"] @ _part["v"])[-1])
        _slow_steps.append(_t)

    # (B) 有快取：Prefill 一次算完前 p 個的 K、V 存進快取；之後每步只算新字的 Q/K/V
    _h0 = embed(SEQ)
    _K_cache = list(rope(_h0[:_p] @ W_K, np.arange(_p)))
    _V_cache = list(_h0[:_p] @ W_V)
    _outs_fast, _fast_steps = [], [_p]
    for _t in range(_p - 1, len(SEQ)):
        if _t >= _p:  # decode：這一步才輪到新字進快取
            _hi = _h0[_t : _t + 1]
            _K_cache.append(rope(_hi @ W_K, [_t])[0])
            _V_cache.append((_hi @ W_V)[0])
            _fast_steps.append(1)
        _q = rope(_h0[_t : _t + 1] @ W_Q, [_t])[0]
        _s = _q @ np.stack(_K_cache).T / np.sqrt(D_MODEL)
        _wgt = np.exp(_s - _s.max())
        _wgt /= _wgt.sum()
        _outs_fast.append(_wgt @ np.stack(_V_cache))

    _same = np.allclose(np.stack(_outs_slow), np.stack(_outs_fast))
    _maxdiff = float(np.abs(np.stack(_outs_slow) - np.stack(_outs_fast)).max())
    mo.md(
        f"""
    | | 每步算幾個 token 的 K/V | 全程合計 |
    |---|---|---|
    | 沒有快取 | {" → ".join(str(_s) for _s in _slow_steps)} | **{sum(_slow_steps)}** |
    | 有快取 | {" → ".join(str(_s) for _s in _fast_steps)} | **{sum(_fast_steps)}** |

    兩邊的輸出向量是否完全相同：**{"是" if _same else "否"}**（最大差 {_maxdiff:.1e}——
    這是浮點數的捨入誤差，不是演算法的差別）。

    快取只是「同一件事不做第二次」，換來的是一模一樣的答案。
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ### 那為什麼只存 K、V，不存 Q？

    看誰會被重複讀就好。下面統計整趟生成裡，每個 token 的 K/V 被查了幾次、Q 被用了幾次
    （用 1️⃣ 的那兩根滑桿）：
    """
    )
    return


@app.cell
def _(C_KV, C_Q, decode_steps, np, plt, prompt_tokens):
    _p, _m = prompt_tokens.value, decode_steps.value
    _n = _p + _m
    # 提示裡的 token：每個 decode 步都被查一次；第 j 個生出來的 token：從第 j 步起被查
    _kv_reads = [_m] * _p + [_m - _j + 1 for _j in range(1, _m + 1)]
    _q_uses = [1] * _n
    _x = np.arange(_n)

    _fig, _ax = plt.subplots(figsize=(7.4, 3.7))
    _ax.bar(_x - 0.2, _kv_reads, width=0.4, color=C_KV, label="times its K/V is read")
    _ax.bar(_x + 0.2, _q_uses, width=0.4, color=C_Q, label="times its Q is used")
    _ax.axvline(_p - 0.5, color="#52646E", ls="--", lw=1)
    _ax.text(_p - 0.45, max(_kv_reads) * 0.92, "  decode starts", fontsize=9, color="#52646E")
    _ax.set_xticks(_x)
    _ax.set_xticklabels([f"t{_i}" for _i in range(_n)], fontsize=8)
    _ax.set_ylabel("reads over the whole generation")
    _ax.set_title("K/V get read again and again; every Q is used exactly once")
    _ax.legend(fontsize=9)
    _ax.grid(axis="y", alpha=0.3)
    _fig.tight_layout()
    _fig
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    橘柱永遠是 1：**Q 問完就沒事了**，之後每個新字都是自己重新提問，不會回頭用舊的 Q。
    藍柱則堆得老高：只要對話還在繼續，舊字的 K、V 就一直被查。

    快取的意義就是「存會被重複讀的東西」——這條原則到這裡就講完了，
    剩下兩節是它的兩個推論。
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 5️⃣ 跨請求重用：為什麼只有「前綴」可以

    把 KV Cache 留到下一個請求繼續用，就是 **Prefix Caching**——同一個技術，
    範圍從「單次請求內」擴大到「跨請求」。但它有個硬條件：
    只有**從第一個 token 起完全相同**的前綴才能重用。

    下面用兩段話驗證：上圖比較「你好，天氣如何」和「你好，明天天氣如何」逐格的 K
    差多少；下圖是三種情況的總結。
    """
    )
    return


@app.cell
def _(C_CACHE, C_RECOMP, attn_parts, np, plt, rel_err):
    TXT_A = "你好，天氣如何"
    TXT_B = "你好，明天天氣如何"     # 前 3 個字相同，第 4 個字起分岔
    TXT_A_LONG = "你好，天氣如何嗎"  # A 的前綴 + 多一個字
    TXT_C = "請問台北，天氣如何"     # 開頭就不同

    _pa, _pb = attn_parts(TXT_A), attn_parts(TXT_B)
    _n = min(len(TXT_A), len(TXT_B))
    per_index_err = [rel_err(_pb["k_deep"][_i], _pa["k_deep"][_i]) for _i in range(_n)]

    # 三種情況：同前綴／前文相同但整段往後移 2 格／完全不同的前文
    _ia, _ic = TXT_A.index("天"), TXT_C.index("天")
    err_same = rel_err(attn_parts(TXT_A_LONG)["k_deep"][_ia], _pa["k_deep"][_ia])
    err_shift = rel_err(attn_parts(TXT_A, offset=2)["k"][_ia], _pa["k"][_ia])
    err_other = rel_err(attn_parts(TXT_C)["k_deep"][_ic], _pa["k_deep"][_ia])

    _shared = sum(1 for _e in per_index_err if _e < 1e-6)
    _fig, (_ax1, _ax2) = plt.subplots(2, 1, figsize=(6.4, 6.4))
    _ax1.axvspan(-0.5, _shared - 0.5, color=C_CACHE, alpha=0.14)
    _ax1.bar(np.arange(_n), per_index_err, color=C_RECOMP)
    _ax1.text((_shared - 1) / 2, max(per_index_err) * 0.5, "reusable\n(0.0%)",
              ha="center", fontsize=9, color="#2F6B45", fontweight="bold")
    _ax1.set_xticks(np.arange(_n))
    _ax1.set_xticklabels([f"t{_i}" for _i in range(_n)], fontsize=9)
    _ax1.set_ylabel("K difference (%)")
    _ax1.set_title("shared prefix is free; from the first\ndifferent token on, nothing is reusable", fontsize=10)
    _ax1.grid(axis="y", alpha=0.3)

    _vals = [err_same, err_shift, err_other]
    _bars = _ax2.bar([0, 1, 2], _vals, color=[C_CACHE, C_RECOMP, C_RECOMP])
    for _b, _v in zip(_bars, _vals):
        _ax2.text(_b.get_x() + _b.get_width() / 2, _v + 3, f"{_v:.1f}%", ha="center", fontsize=9)
    _ax2.set_xticks([0, 1, 2])
    _ax2.set_xticklabels(["same\nprefix", "same text,\nshifted +2", "different\nprefix"], fontsize=9)
    _ax2.set_ylim(0, max(_vals) * 1.2)
    _ax2.set_ylabel("K difference (%)")
    _ax2.set_title("position alone is already enough\nto make K a different vector", fontsize=10)
    _ax2.grid(axis="y", alpha=0.3)
    _fig.tight_layout()
    _fig
    return TXT_A, TXT_B, err_other, err_same, err_shift, per_index_err


@app.cell
def _(TXT_A, TXT_B, err_other, err_same, err_shift, mo, per_index_err):
    _shared = sum(1 for _e in per_index_err if _e < 1e-6)
    mo.md(
        f"""
    - 「{TXT_A}」對「{TXT_B}」：前 **{_shared}** 格的 K 差 **{err_same:.1f}%**——
      逐位元完全相同，這幾格的 Prefill 可以整段跳過。第 {_shared + 1} 格起就衝到
      {max(per_index_err):.0f}% 上下，一個字都救不回來。
    - 同一段話**原封不動往後移 2 格**：K 差 **{err_shift:.0f}%**。前文一模一樣，
      只有位置變了——位置編碼在算 K 之前就混進去了。
    - 換一段不同開頭的前文再看同一個字：K 差 **{err_other:.0f}%**。
      深層的 K 是「看過前面所有字」之後算出來的。

    所以「天氣如何」這四個字，在兩個開頭不同的請求裡是**兩組不同的 K、V**。
    看起來一樣的字，搬過去就會算錯。
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 6️⃣ 代價：拿記憶體換計算

    快取要放在顯示卡記憶體裡，而且**會隨對話變長一直長大**。每個 token 要多少？
    把 K 和 V 兩份、每一層、每個 KV 頭、每個維度的數字加起來乘上位元組數就是了：

    ```
    每 token bytes = 層數 × KV 頭數 × 每頭維度 × 2（K 和 V） × 2（fp16 每個數 2 bytes）
    ```

    預設值是 Llama 3 8B（GQA）的配置：32 層、8 個 KV 頭、每頭 128 維。
    """
    )
    return


@app.cell
def _(mo):
    n_layers = mo.ui.slider(start=8, stop=80, step=4, value=32, label="層數", show_value=True)
    n_kv_heads = mo.ui.slider(start=1, stop=32, step=1, value=8, label="KV 頭數", show_value=True)
    ctx_len = mo.ui.dropdown(
        options={"2k": 2000, "8k": 8000, "32k": 32000, "128k": 128000, "1M": 1000000},
        value="8k", label="你的上下文長度",
    )
    concurrency = mo.ui.slider(start=1, stop=32, step=1, value=10, label="同時上線人數", show_value=True)
    vram_free = mo.ui.slider(start=2, stop=80, step=2, value=10, label="權重載入後還剩多少 VRAM（GB）", show_value=True)
    mo.vstack([n_layers, n_kv_heads, ctx_len, concurrency, vram_free])
    return concurrency, ctx_len, n_kv_heads, n_layers, vram_free


@app.cell
def _():
    HEAD_DIM, DTYPE_BYTES = 128, 2

    def bytes_per_token(layers, kv_heads):
        return layers * kv_heads * HEAD_DIM * 2 * DTYPE_BYTES

    SCENARIOS = [
        ("2k x1", 2_000, 1),
        ("8k x1", 8_000, 1),
        ("32k x1", 32_000, 1),
        ("8k x10", 8_000, 10),
        ("128k x1", 128_000, 1),
        ("1M x1", 1_000_000, 1),
    ]
    return SCENARIOS, bytes_per_token


@app.cell
def _(
    C_CACHE,
    C_RECOMP,
    SCENARIOS,
    bytes_per_token,
    concurrency,
    ctx_len,
    n_kv_heads,
    n_layers,
    np,
    plt,
    vram_free,
):
    _per = bytes_per_token(n_layers.value, n_kv_heads.value)
    _limit = vram_free.value
    _names = [_s[0] for _s in SCENARIOS] + ["yours"]
    _gb = [_per * _t * _c / 1e9 for _n, _t, _c in SCENARIOS]
    _gb.append(_per * ctx_len.value * concurrency.value / 1e9)
    _cols = [C_CACHE if _g <= _limit else C_RECOMP for _g in _gb]
    _cols[-1] = "#1C2B33" if _gb[-1] <= _limit else C_RECOMP

    _fig, _ax = plt.subplots(figsize=(7.6, 3.9))
    _bars = _ax.bar(np.arange(len(_names)), _gb, color=_cols)
    _ax.axhline(_limit, color="#52646E", ls="--", lw=1.5)
    _ax.text(-0.4, _limit * 1.12, f"free VRAM {_limit} GB", fontsize=9, color="#52646E")
    _ax.set_yscale("log")
    _ax.set_xticks(np.arange(len(_names)))
    _ax.set_xticklabels(_names, fontsize=9)
    _ax.set_ylabel("KV cache (GB, log scale)")
    _ax.set_title(f"{_per / 1024:.0f} KiB per token  ({n_layers.value} layers x {n_kv_heads.value} KV heads)")
    for _b, _g in zip(_bars, _gb):
        _ax.text(_b.get_x() + _b.get_width() / 2, _g * 1.15, f"{_g:.2f}", ha="center", fontsize=8)
    _ax.grid(axis="y", alpha=0.3)
    _fig.tight_layout()
    _fig
    return


@app.cell
def _(
    bytes_per_token,
    concurrency,
    ctx_len,
    mo,
    n_kv_heads,
    n_layers,
    vram_free,
):
    _per = bytes_per_token(n_layers.value, n_kv_heads.value)
    _need = _per * ctx_len.value * concurrency.value / 1e9
    _ok = _need <= vram_free.value
    mo.md(
        f"""
    每 token 的 KV = **{_per:,} bytes**（{_per / 1024:.0f} KiB ≈ {_per / 1e6:.2f} MB）

    你的設定：{ctx_len.selected_key} 上下文 × {concurrency.value} 人
    → 需要 **{_need:.2f} GB**，可用 **{vram_free.value} GB**
    → **{"放得下" if _ok else f"放不下，差 {_need - vram_free.value:.2f} GB"}**

    {"" if _ok else "放不下時，要嘛砍上下文、砍並發，要嘛把快取放到別的地方去——那是第 5 課的題目。"}
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 7️⃣ 換你動手

    三個挑戰，由易到難。做完記得**點左側教學頁的「下載 .py」把這份 notebook 帶走**，
    在自己電腦用 `uvx marimo edit lesson.py` 打開，每一格程式碼都能改。

    1. **LEVEL 1**：回到 6️⃣ 把「KV 頭數」從 8 拉到 32（等於不共用 KV 頭），
       看 `1M x1` 那根柱子變成幾 GB。
    2. **LEVEL 2**：回到 3️⃣ 試兩組設定——提示 2000／生成 100，和提示 100／生成 2000。
       兩組的 token 總數差不多，但「省下的倍數」差很多。哪一種情況快取更划算？為什麼？
    3. **LEVEL 3**：用下面的實驗區換一組你自己的 A／B 句子，找出「從第幾個字開始 K 就不一樣了」。
       試著讓它們共用越長越好的前綴——然後想想：這件事對你寫 prompt 的順序有什麼啟示？
    """
    )
    return


@app.cell
def _(mo):
    my_a = mo.ui.text(value="你好，天氣如何", label="句子 A", full_width=True)
    my_b = mo.ui.text(value="你好，明天天氣如何", label="句子 B", full_width=True)
    mo.vstack(
        [
            mo.md("**你的實驗區**——換兩句自己的話，看逐格的 K 差多少（0.0 ＝ 完全一樣 ＝ 這個 token 可以直接重用）"),
            my_a,
            my_b,
        ]
    )
    return my_a, my_b


@app.cell
def _(attn_parts, mo, my_a, my_b, rel_err):
    _a, _b = my_a.value, my_b.value
    _n = min(len(_a), len(_b))
    if _n == 0:
        _out = mo.md("兩句話都填點字，這裡就會逐格比對。")
    else:
        _ka = attn_parts(_a)["k_deep"]
        _kb = attn_parts(_b)["k_deep"]
        _errs = [rel_err(_kb[_i], _ka[_i]) for _i in range(_n)]
        _shared = 0
        for _e in _errs:
            if _e >= 1e-6:
                break
            _shared += 1
        _out = mo.md(
            f"""
    逐格 K 相對誤差（%）：`{[round(_e, 1) for _e in _errs]}`

    共用前綴長度：**{_shared} 個 token**（「{_a[:_shared]}」）
    """
        )
    _out
    return


@app.cell(hide_code=True)
def _(mo):
    mo.accordion(
        {
            "💡 LEVEL 1 參考解答": mo.md(
                r"""
    KV 頭數 8 → 32 是 4 倍，每 token 從 128 KiB 變成 512 KiB，
    `1M x1` 從 **131.07 GB** 變成 **524.29 GB**。

    GQA（多個 query 頭共用一組 KV 頭）省下來的就是這 4 倍。
    上下文一長，這個係數是「放得下」和「放不下」的差別。
    """
            ),
            "💡 LEVEL 2 參考解答": mo.md(
                r"""
    用 3️⃣ 的兩根滑桿各拉一次，看下面那句「多做了幾倍的工」：

    | 3️⃣ 的設定 | 沒有快取 | 有快取 | 多做的工 |
    | --- | --- | --- | --- |
    | 提示 2000 ＋ 生成 100 | 207,050 | 2,100 | **99 倍** |
    | 提示 100 ＋ 生成 2000 | 2,201,100 | 2,100 | **1048 倍** |

    **生成越長，快取越划算。**因為平方項長在「生成長度」上：
    每多生一個字，就多一整輪重算。提示再長也只是被重算的那個基數，
    真正把計算量炸開的是生成的步數。

    （反過來說，提示很長、只生幾個字的場景——例如長文件問答——
    痛的不是重算，是那一大段 Prefill 本身。那就是 Prefix Caching 的主場。）
    """
            ),
            "💡 LEVEL 3 提示": mo.md(
                r"""
    怎麼驗證自己做對了：實驗區顯示的「逐格 K 相對誤差」，
    共用前綴的部分應該是一整排 `0.0`，而且**第一個非 0 的位置，
    就是兩句話第一個不同的字**。試試看把不同的字往後挪，那排 0 會跟著變長。

    對寫 prompt 的啟示：**把所有請求共用的東西放到最前面**
    （系統提示、規則、範例、固定的文件），把每次都不一樣的東西
    （使用者的問題、時間戳、隨機 ID）放到最後面。開頭放一個
    「今天是 2026-08-28」，後面幾千字的共用前綴就全部作廢了。

    這件事怎麼變成帳單上的數字，下一課算給你看。
    """
            ),
        }
    )
    return


if __name__ == "__main__":
    app.run()
