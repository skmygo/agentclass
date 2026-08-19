# GPU 軌 notebook 模板（雙軌課才需要）
# ═══════════════════════════════════════
# 用法：cp 到 lessons/<id>/<id>_gpu.py 後改寫。
# - PEP 723 inline dependencies（下方 /// script 區塊）：molab / marimo sandbox 自動安裝
# - 課程頁連結規則（零上傳零回填，git push 即更新）：
#   https://molab.marimo.io/github/{owner}/{repo}/blob/{branch}/lessons/<id>/<id>_gpu.py
#   （repo 必須公開；含私人資訊的參考教材放 ref_data/，已 gitignore）
# - 本機無 GPU 時驗證到「結構層級」（import 這個模組驗 marimo 格式與語法），
#   全量驗證請使用者在 molab 實跑
# - 訓練類配方的實測經驗（Unsloth、loss masking、eos 雙保險…）見 skill 的
#   references/engineering.md「GPU 軌道」一節
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "marimo",
#     "torch",
#     "matplotlib",
# ]
# ///
import marimo

__generated_with = "0.23.16"
app = marimo.App(width="medium", app_title="課程標題（GPU 實戰）")


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    # 🚀 課程標題：GPU 實戰

    這是課程的 **GPU 軌道**——瀏覽器概念版教過的每一步，這裡在真實模型上重演一次。

    ⚠️ **本 notebook 需要 NVIDIA GPU**。
    在 molab 請先把執行環境選成 **GPU Server**（例如 RTX Pro 6000）再往下跑，
    全程約 X–Y 分鐘（含首次下載模型與安裝套件）。
    """
    )
    return


@app.cell
def _():
    import marimo as mo
    return (mo,)


@app.cell
def _(mo):
    # GPU 檢查 cell：沒有 CUDA 時給明確指引，保護誤用 CPU 的學員
    import torch

    _ok = torch.cuda.is_available()
    mo.md(
        f"**GPU**：{torch.cuda.get_device_name(0) if _ok else '偵測不到'}"
        + ("" if _ok else "\n\n🛑 沒有 CUDA GPU——請在 molab 把 Server 換成 GPU 再執行，下面的格子才跑得動。")
    )
    return (torch,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 1️⃣ 第一步標題

    每一步都對照瀏覽器概念版的章節，讓學員知道「這裡的真實版對應剛剛學的哪個概念」。
    """
    )
    return


@app.cell
def _():
    # 真實版流程從這裡開始寫
    return


if __name__ == "__main__":
    app.run()
