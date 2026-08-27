import marimo

__generated_with = "0.23.16"
app = marimo.App(width="medium", app_title="會思考的模型：CoT 與 Reasoning Model（實驗場）")


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    # 🧪 會思考的模型：CoT 與 Reasoning Model（實驗場）

    這是本課的**實驗場**。左側教學讀到哪，就回到這裡動手做——
    每一格程式碼都可以**直接修改、立即重跑**（點格子右上的 ▶，或按 `Ctrl+Enter`）。
    改壞了也沒關係：重新整理頁面就會回到原版。

    左頁你已經看過「一步一步想」讓答案從錯變對；這裡要看第二招：
    **多想幾次、投票表決**（test-time compute），以及它背後簡單得驚人的數學。
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
    from math import comb

    import matplotlib.pyplot as plt
    import numpy as np
    return comb, np, plt


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 1️⃣ 多數決實測：同一題抽 9 次、投票

    左頁的第二個實驗：問 qwen3.5-2b「47 × 38 = ?」，**只准直接回答數字**（不准列式），
    temperature=1 讓它每次抽樣不同，連問 9 次（實測，2026-08）。

    單次直接答，這顆 2B 小模型的答對率只有 **6/9**——但把 9 個答案拿來投票，
    正確答案 1786 以 6 票壓倒性勝出。下面就是那 9 次的真實開票結果：
    """
    )
    return


@app.cell
def _(np, plt):
    # 實測 tally（qwen3.5-2b、temp=1、9 次抽樣、2026-08）——正解 1786
    VOTE_TALLY = {"1786": 6, "1451": 1, "1466": 1, "1446": 1}
    CORRECT = "1786"

    _labels = list(VOTE_TALLY)
    _votes = np.array([VOTE_TALLY[k] for k in _labels])
    _colors = ["#55A868" if _k == CORRECT else "#C44E52" for _k in _labels]
    _fig, _ax = plt.subplots(figsize=(7.0, 3.8))
    _bars = _ax.bar(_labels, _votes, color=_colors, edgecolor="#1C2B33", linewidth=1.2, zorder=3)
    for _b, _v in zip(_bars, _votes):
        _ax.text(_b.get_x() + _b.get_width() / 2, _v + 0.12, str(_v),
                 ha="center", fontsize=12, fontweight="bold", zorder=4)
    _ax.set_ylim(0, 7.2)
    _ax.set_xlabel("sampled answer for 47 x 38 (green = correct)")
    _ax.set_ylabel("votes (out of 9 samples)")
    _ax.set_title("majority voting: 6/9 single-shot accuracy -> vote picks 1786")
    _ax.grid(axis="y", alpha=0.3, zorder=0)
    _fig.tight_layout()
    _fig
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    注意錯誤答案的長相：1451、1466、1446——都「長得像」正解 1786 的量級，
    但彼此**不一致**。這就是多數決能贏的關鍵：**對的答案只有一種，錯的答案各錯各的**，
    票會集中在正解上。你重跑同一實驗，票數分布會不同（抽樣本來就會變），
    看方向：單次不可靠、投票穩得多。

    ## 2️⃣ 投票為什麼有效：二項分布算給你看

    把「答一次」當成一枚不公平的硬幣：答對機率 $p$。
    抽 $n$ 次取多數決，答對機率就是二項分布的尾和：

    $$P(\text{多數對}) = \sum_{k > n/2} \binom{n}{k} p^k (1-p)^{n-k}$$

    這是**教學模型**（假設每次抽樣獨立、答錯不集中在同一個錯誤答案上）——
    真實模型的錯誤有相關性，曲線沒這麼漂亮，但方向一致。拉拉看：
    """
    )
    return


@app.cell
def _(mo):
    p_single = mo.ui.slider(start=0.30, stop=0.95, step=0.05, value=0.65,
                            label="單次答對率 p", show_value=True)
    n_max = mo.ui.slider(start=9, stop=81, step=2, value=41,
                         label="最多抽幾次（奇數，避免平手）", show_value=True)
    mo.vstack([p_single, n_max])
    return n_max, p_single


@app.cell
def _(comb, n_max, np, p_single, plt):
    def maj_acc(p, n):
        # 多數決答對率：超過半數答對的二項分布尾和
        return sum(comb(n, k) * p**k * (1 - p) ** (n - k) for k in range(n // 2 + 1, n + 1))

    _ns = np.arange(1, n_max.value + 1, 2)
    _fig, _ax = plt.subplots(figsize=(7.0, 4.2))
    for _p, _c in [(0.45, "#C44E52"), (p_single.value, "#4C72B0"), (0.85, "#55A868")]:
        _ys = [maj_acc(_p, int(_n)) for _n in _ns]
        _lw = 3.0 if abs(_p - p_single.value) < 1e-9 else 1.6
        _ax.plot(_ns, _ys, "o-", color=_c, linewidth=_lw, markersize=4,
                 label=f"p = {_p:.2f}" + ("  (your slider)" if abs(_p - p_single.value) < 1e-9 else ""))
    _ax.axhline(0.5, color="#9AA7AE", linestyle=":", linewidth=1.2)
    _ax.set_xlabel("number of samples n (majority vote)")
    _ax.set_ylabel("P(majority is correct)")
    _ax.set_ylim(0, 1.02)
    _ax.set_title("teaching model: votes amplify accuracy - unless p < 0.5")
    _ax.legend(fontsize=9)
    _ax.grid(alpha=0.3)
    _fig.tight_layout()
    _fig
    return (maj_acc,)


@app.cell(hide_code=True)
def _(maj_acc, mo, p_single):
    _p = p_single.value
    _n9, _n41 = maj_acc(_p, 9), maj_acc(_p, 41)
    _verdict = (
        "投越多次越準——這就是 test-time compute 的本質：**拿計算換正確率**。"
        if _p > 0.5
        else "**投票反而越投越錯**！p < 0.5 時多數決放大的是錯誤——垃圾進、垃圾出，多想不能救不會。"
    )
    mo.md(
        f"""
    你的設定：單次 {_p:.0%} → 投 9 次 **{_n9:.0%}**、投 41 次 **{_n41:.0%}**。{_verdict}

    也注意曲線的**形狀**：前幾票進步飛快，之後越來越平——第 9 票到第 41 票的進步，
    遠小於第 1 票到第 9 票。算力加倍、效益遞減，這就是為什麼「無限多想」不是免費午餐，
    也是 **overthinking**（簡單題想太多）在工程上要被管住的原因：
    多花的每一秒延遲與每一塊錢，買到的正確率越來越少。

    ## 3️⃣ 你的實驗區

    下面這格是你的，改完按 ▶ 重跑。挑戰在左頁「換你動手」，做完再開解答對照。
    """
    )
    return


@app.cell
def _(maj_acc):
    # ===== 你的實驗區 =====
    # LEVEL 2 起點：用第 1 節的實測答對率 6/9 算「該投幾票」
    p_measured = 6 / 9
    for n in (1, 3, 9, 21, 41):
        print(f"p={p_measured:.2f}  投 {n:>2} 次 → 多數決答對率 {maj_acc(p_measured, n):.1%}")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.accordion(
        {
            "💡 LEVEL 1 參考解答": mo.md(
                r"""
    把 2️⃣ 的 p 拉到 0.45（低於一半），曲線整條往下彎——投 41 次的答對率比投 1 次**更低**。

    多數決不是魔法，是**放大器**：p > 0.5 放大對、p < 0.5 放大錯。
    所以 test-time compute 的前提是模型「單次至少略優於亂猜」；
    對它完全不會的題目（p 很低），正確做法是換更強的模型、給工具，或拆解問題——
    不是加抽樣次數。
    """
            ),
            "💡 LEVEL 2 參考解答": mo.md(
                r"""
    實驗區用實測的 p = 6/9 ≈ 0.67 算出來：

    ```
    投  1 次 → 66.7%
    投  3 次 → 74.1%
    投  9 次 → 85.5%
    投 21 次 → 94.4%
    投 41 次 → 98.6%
    ```

    9 票就把 67% 拉到 85%，但從 21 票到 41 票只多 4 個百分點、算力卻加倍——
    「該投幾票」是成本與正確率的商業決策，不是越多越好。
    實務系統（如數學競賽的 self-consistency）常落在 8–64 次抽樣這個量級。
    """
            ),
            "💡 LEVEL 3 提示": mo.md(
                r"""
    教學模型假設「每次抽樣獨立」，真實模型不滿足：同一個模型會**系統性地**
    在同一種陷阱上跌倒（例如球棒與球那題，直覺錯答 55 不是隨機錯誤，是分布裡的高峰）。

    驗證方向：如果錯誤完全隨機，第 1 節的 3 個錯誤答案應該毫無規律；
    但它們都落在 1400–1500 附近——乘法的進位錯誤有固定模式。
    當錯誤「抱團」時，投票的實際效益會低於二項分布的預測；
    極端情況（直覺陷阱題）錯誤答案反而是多數——這時 CoT（改變**單次**答對率）
    比多數決（重複抽同一個分布）更有效。兩招解的是不同的問題。
    """
            ),
        }
    )
    return


if __name__ == "__main__":
    app.run()
