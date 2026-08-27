import marimo

__generated_with = "0.23.16"
app = marimo.App(width="medium", app_title="新開發範式：Vibe Coding 到 Spec-Driven（實驗場）")


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    # 🧪 新開發範式：Vibe Coding 到 Spec-Driven（實驗場）

    這是本課的**實驗場**。左側教學讀到哪，就回到這裡動手做——
    每一格程式碼都可以**直接修改、立即重跑**（點格子右上的 ▶，或按 `Ctrl+Enter`）。
    改壞了也沒關係：重新整理頁面就會回到原版。

    這一課的兩個實驗：**範式光譜**（你的專案該站在哪一格）、
    **context 組裝計算機**（context engineering 到底省下什麼——用真實 token 帳算給你看）。
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


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 1️⃣ 範式光譜：你的專案該站哪一格

    四個名詞不是四個門派，是**同一條光譜上的四個站**：
    越往右，你交給 AI 的東西越結構化、人的驗收點越密，
    改壞的代價越能被擋下來——但前期要寫的東西也越多。

    這張圖是**教學定位圖**（幫助你選站的心智模型，不是量測數據）。
    挑一個情境，看建議站位怎麼移動：
    """
    )
    return


@app.cell
def _(mo):
    scenario = mo.ui.dropdown(
        options=[
            "週末自用小工具（只有你會用）",
            "團隊內部工具（幾個同事天天用）",
            "多人維護的正式產品（有客戶）",
            "合規要求高的系統（金融／醫療）",
        ],
        value="週末自用小工具（只有你會用）",
        label="你的專案情境",
    )
    scenario
    return (scenario,)


@app.cell
def _(np, plt, scenario):
    _stations = ["Vibe\nCoding", "Agentic\nEngineering", "Context\nEngineering", "Spec-Driven\nDevelopment"]
    _x = np.array([0.0, 1.0, 2.0, 3.0])
    _zones = {
        "週末自用小工具（只有你會用）": (0.0, 0.8),
        "團隊內部工具（幾個同事天天用）": (0.7, 2.2),
        "多人維護的正式產品（有客戶）": (1.6, 3.0),
        "合規要求高的系統（金融／醫療）": (2.4, 3.0),
    }
    _lo, _hi = _zones[scenario.value]
    _fig, _ax = plt.subplots(figsize=(7.2, 3.2))
    _ax.axvspan(_lo, _hi, color="#55A868", alpha=0.18, zorder=1)
    _ax.hlines(0, -0.3, 3.3, color="#1C2B33", linewidth=2.0, zorder=2)
    for _xi, _s in zip(_x, _stations):
        _in = _lo - 0.01 <= _xi <= _hi + 0.01
        _ax.plot(_xi, 0, "o", markersize=14 if _in else 10,
                 color="#55A868" if _in else "#9AA7AE",
                 markeredgecolor="#1C2B33", markeredgewidth=1.2, zorder=3)
        _ax.annotate(_s, (_xi, 0), xytext=(0, 14), textcoords="offset points",
                     ha="center", fontsize=9.5,
                     fontweight="bold" if _in else "normal",
                     color="#1C2B33" if _in else "#9AA7AE")
    _ax.annotate("freeform ->", (-0.28, 0), xytext=(0, -26), textcoords="offset points",
                 fontsize=9, color="#9AA7AE")
    _ax.annotate("-> structured, more checkpoints", (3.28, 0), xytext=(0, -26),
                 textcoords="offset points", fontsize=9, ha="right", color="#9AA7AE")
    _ax.set_xlim(-0.4, 3.4)
    _ax.set_ylim(-0.7, 0.9)
    _ax.axis("off")
    _ax.set_title("paradigm spectrum (teaching map, not a measurement)", fontsize=10)
    _fig.tight_layout()
    _fig
    return


@app.cell(hide_code=True)
def _(mo, scenario):
    _why = {
        "週末自用小工具（只有你會用）": (
            "**Vibe 就夠了。**改壞的代價是你自己重跑一次，最貴的成本是你的週末時間——"
            "寫 spec 的時間比重寫整個工具還久。用自然語言描述、跑跑看、不對就再講一次。"
        ),
        "團隊內部工具（幾個同事天天用）": (
            "**開始需要驗收點。**別人會用你的東西，「能動」不夠，要「別人改得動」。"
            "至少：任務拆成可驗收的小步、AI 產出要過你的測試、關鍵決策寫進 CLAUDE.md "
            "讓下一次對話不用重講。"
        ),
        "多人維護的正式產品（有客戶）": (
            "**context 與 spec 都要上。**多人共事時，「AI 憑什麼這樣改」必須有可追溯的依據——"
            "餵對脈絡（相關模組、規範、測試）、行為變更走 spec 提案，代碼審查看 diff 是否符合 spec。"
        ),
        "合規要求高的系統（金融／醫療）": (
            "**Spec 是唯一真相源。**每個行為都要能回答「規格哪一條允許」。"
            "spec 先行、實作對 spec 驗收、變更走提案流程——AI 是高速實作引擎，"
            "但方向盤與煞車在規格手上。"
        ),
    }
    mo.md(f"""**為什麼：**{_why[scenario.value]}""")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 2️⃣ Context 組裝計算機：省下的是真金白銀

    Context engineering 的核心動作只有一個：**按需組裝最小的正確資訊**。
    下面的帳是真的——同一個客服問題（「我剛買的保溫瓶可以退嗎？運費誰出？」），
    用 tiktoken（`o200k_base`）實測四個零件的 token 數（2026-08）：

    | 零件 | 全塞版 | 工程化版 |
    |---|---|---|
    | system prompt | 31 | 31 |
    | 知識（FAQ） | 整份 420 | 檢索後只留退貨段 **140** |
    | 對話歷史 | 10 輪完整 280 | 摘要成一句 **39** |
    | 這一輪的問題 | 26 | 26 |

    勾勾看兩個開關的四種組合，帳單差多少：
    """
    )
    return


@app.cell
def _(mo):
    use_all_faq = mo.ui.switch(value=True, label="知識：塞整份 FAQ（不檢索）")
    use_full_hist = mo.ui.switch(value=True, label="歷史：塞完整 10 輪對話（不摘要）")
    mo.vstack([use_all_faq, use_full_hist])
    return use_all_faq, use_full_hist


@app.cell
def _(np, plt, use_all_faq, use_full_hist):
    # tiktoken o200k_base 實測（spike_genai_devstyle.py，2026-08）：零件 token 數
    T_SYSTEM, T_QUESTION = 31, 26
    T_FAQ_ALL, T_FAQ_REL = 420, 140
    T_HIST_ALL, T_SUMMARY = 280, 39

    _faq = T_FAQ_ALL if use_all_faq.value else T_FAQ_REL
    _hist = T_HIST_ALL if use_full_hist.value else T_SUMMARY
    _now = T_SYSTEM + _faq + _hist + T_QUESTION
    _max = T_SYSTEM + T_FAQ_ALL + T_HIST_ALL + T_QUESTION  # 757

    _parts = [("system", T_SYSTEM, "#8172B2"),
              ("knowledge (FAQ)", _faq, "#4C72B0"),
              ("history", _hist, "#DD8452"),
              ("question", T_QUESTION, "#55A868")]
    _fig, _ax = plt.subplots(figsize=(7.2, 2.9))
    _left = 0
    for _nm, _v, _c in _parts:
        _ax.barh([0], [_v], left=_left, color=_c, edgecolor="#1C2B33",
                 linewidth=1.1, height=0.55, zorder=3)
        if _v >= 35:
            _ax.text(_left + _v / 2, 0, f"{_nm}\n{_v}", ha="center", va="center",
                     fontsize=9, fontweight="bold", color="white", zorder=4)
        _left += _v
    _ax.axvline(_max, color="#C44E52", linestyle="--", linewidth=1.8, zorder=2)
    _ax.text(_max, 0.42, f" stuff-everything = {_max}", color="#C44E52",
             fontsize=9.5, fontweight="bold", ha="right")
    _ax.set_xlim(0, _max * 1.06)
    _ax.set_yticks([])
    _ax.set_xlabel("prompt tokens (measured, o200k_base)")
    _ax.set_title(f"this assembly: {_now} tokens", fontsize=11, fontweight="bold")
    _ax.grid(axis="x", alpha=0.3)
    _fig.tight_layout()
    _fig
    return


@app.cell
def _(mo, use_all_faq, use_full_hist):
    _faq = 420 if use_all_faq.value else 140
    _hist = 280 if use_full_hist.value else 39
    _now = 31 + _faq + _hist + 26
    _save = (757 - _now) / 757
    _msg = (
        "全塞版：757 個 token 的 prompt，其中真正回答這題需要的知識只有退貨那一段。"
        if _now == 757
        else f"目前組裝 **{_now} tokens**，比全塞版省 **{_save:.0%}**。"
        "省的不只是錢：無關內容變少，模型也更不容易被雜訊帶偏。"
    )
    mo.md(
        f"""
    {_msg}

    這個帳每一輪對話都要付一次——乘上流量，就是 context engineering 的商業價值。
    但別忘了它的另一半：**「最小」的前提是「正確」**。把該給的規格砍掉，
    省下的 token 會用十倍的 debug 時間還回來。
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 3️⃣ 你的實驗區

    下面這格是你的，改完按 ▶ 重跑。挑戰在左頁「換你動手」，做完再開解答對照。
    """
    )
    return


@app.cell
def _():
    # ===== 你的實驗區 =====
    # 用零件帳試算你自己的應用：改成你的 prompt 結構
    my_parts = {
        "system": 31,          # 你的 system prompt
        "knowledge": 420,      # 你塞的文件／FAQ／規格
        "history": 280,        # 對話歷史
        "question": 26,        # 這一輪的問題
    }
    total = sum(my_parts.values())
    print(f"單輪 prompt：{total} tokens")
    print(f"1 天 1 萬輪：{total * 10_000:,} tokens/天")
    print("提示：中文粗估 1 字 ≈ 1.1 token（o200k_base 實測）")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.accordion(
        {
            "💡 LEVEL 1 參考解答": mo.md(
                r"""
    兩個開關全關（檢索後段落＋歷史摘要）＝ **236 tokens**，對全塞版 757 省 **69%**。

    只動知識那個開關（FAQ 整份→相關段）省 280 tokens；
    只動歷史（完整→摘要）省 241 tokens——**兩個都要動**，單靠一邊只省一半。
    """
            ),
            "💡 LEVEL 2 參考解答": mo.md(
                r"""
    在實驗區把 `knowledge` 改成 3000（塞一份大文件）、`history` 改成 1200（長對話）：

    ```python
    my_parts = {"system": 31, "knowledge": 3000, "history": 1200, "question": 26}
    ```

    單輪 4,257 tokens，一天一萬輪就是 **4,257 萬 tokens/天**——
    這時候「省 69%」不再是百分比遊戲，是每天幾千萬 token 的帳。
    規模越大，context engineering 的投資報酬越高；
    反過來說，一天十輪的小工具，全塞也沒人會怪你。
    """
            ),
            "💡 LEVEL 3 提示": mo.md(
                r"""
    「摘要歷史」不是免費的午餐——想清楚三件事再上：

    1. **摘要由誰產生？**通常是再叫一次便宜的模型做摘要——這本身也花 token，
       要算進總帳（流量大時仍然划算，因為摘要一次、複用很多輪）。
    2. **摘掉的資訊回得來嗎？**客服場景裡「顧客三輪前說過的訂單編號」被摘掉，
       後面就答不出來——所以實務上常是「摘要＋保留最近 N 輪原文」的混合。
    3. **怎麼驗證沒摘壞？**拿歷史對話回放測試：摘要版跟完整版的回答是否一致。
       不一致的那些 case，就是你的摘要規則要保留的欄位清單。

    驗證自己做對了：把你的應用最常見的 10 個問題各跑一次「全塞 vs 工程化」，
    答案品質沒掉、token 帳有感下降，才算成立。
    """
            ),
        }
    )
    return


if __name__ == "__main__":
    app.run()
