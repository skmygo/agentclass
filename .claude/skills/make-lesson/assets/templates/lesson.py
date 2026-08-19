# 瀏覽器軌 notebook 模板（marimo 純 .py 格式）
# ═══════════════════════════════════════════
# 用法：cp 到 lessons/<id>/lesson.py 後改寫。骨架示範的是「踩過坑之後的正確寫法」：
# - 每個 md 章節標題帶 1️⃣2️⃣… emoji：左頁 .golab 按鈕靠它捲動錨定，兩邊要一致
# - matplotlib 圖一律當 cell 的「最後運算式」——包在 mo.vstack([...]) 裡不會渲染，
#   說明文字拆到下一個 cell（要共用數值就 return 變數）
# - 圖內文字（標籤/圖例/標題）一律英文：Pyodide 的 matplotlib 沒有 CJK 字型
# - 套件必須有 Pyodide wheel（numpy/pandas/sklearn/matplotlib 可；torch 不可）
# - 別寫 per-sample 的 Python 迴圈，numpy 向量化在 WASM 裡才夠快
# - 課末固定留「你的實驗區」cell ＋下載帶走的說明
import marimo

__generated_with = "0.23.16"
app = marimo.App(width="medium", app_title="課程標題（實驗場）")


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    # 🧪 課程標題（實驗場）

    這是本課的**實驗場**。左側教學讀到哪，就回到這裡動手做——
    每一格程式碼都可以**直接修改、立即重跑**（點格子右上的 ▶，或按 `Ctrl+Enter`）。
    改壞了也沒關係：重新整理頁面就會回到原版。
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
    ## 1️⃣ 第一節標題（emoji 是左頁按鈕的錨點）

    每節的 md 說明寫在 hide_code=True 的 cell；中文解說放這裡（md 可以中文），
    圖表內的文字一律英文。
    """
    )
    return


@app.cell
def _(mo):
    # 互動元件獨立一格（slider/dropdown/switch…），下游 cell 用 .value 讀
    demo_slider = mo.ui.slider(
        start=1, stop=10, step=1, value=3, label="示範參數", show_value=True
    )
    demo_slider
    return (demo_slider,)


@app.cell
def _(demo_slider, np, plt):
    # 計算＋畫圖：圖當「最後運算式」才會渲染（勿包 mo.vstack）
    _x = np.linspace(0, 2 * np.pi, 200)
    _y = np.sin(demo_slider.value * _x)
    _fig, _ax = plt.subplots(figsize=(7, 4))
    _ax.plot(_x, _y, color="#4C72B0")
    _ax.set_xlabel("x")            # 英文標籤
    _ax.set_ylabel("sin(kx)")
    _ax.set_title(f"k = {demo_slider.value}")
    _ax.grid(alpha=0.3)
    _fig.tight_layout()
    _fig
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 2️⃣ 練習：換你動手

    下面這格是你的實驗區，改完按 ▶ 重跑。建議挑戰（由易到難）：

    1. LEVEL 1 挑戰
    2. LEVEL 2 挑戰
    3. LEVEL 3 挑戰

    做完記得：**點右上角下載按鈕（或左側教學頁的「下載 .py」）把你的版本帶走**，
    在自己電腦用 `uvx marimo edit lesson.py` 就能繼續玩。
    """
    )
    return


@app.cell
def _():
    # ===== 你的實驗區 =====
    # 試著修改下面的參數，或整段重寫！
    my_param = 42
    print(f"my_param = {my_param}")
    return


if __name__ == "__main__":
    app.run()
