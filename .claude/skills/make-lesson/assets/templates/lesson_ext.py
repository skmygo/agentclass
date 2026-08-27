# 外部軌 notebook 模板（Pyodide 跑不了的課：需 GPU / 無 WASM wheel / 需真網路）
# ═══════════════════════════════════════════════════════════════════════════
# 用法：cp 到 content/<topic>/<id>/<id>_ext.py 後改寫（scaffold --external 會代勞）。
#
# 這是課程「唯一」的可執行版本——沒有瀏覽器迷你版。因此它必須自成完整教材：
# - **大量解說寫進 md cells**：每個程式 cell 前都有「為什麼、在做什麼、看什麼」，
#   學員只帶著這份 notebook 也能學完整堂課（左頁是導讀與賣點，不是必要條件）
# - 章節用 emoji 編號（1️⃣2️⃣3️⃣…）：左頁各節指到這裡的同號章節
# - 每個左頁提到的行為與數字，這裡都要真的存在且為真
#
# 工程備忘：
# - PEP 723 inline dependencies（下方 /// script 區塊）：molab / uvx --sandbox 自動安裝。
#   prerelease 套件要把「傳依賴的 prerelease pin」一起釘（如 fastmcp 4 beta 要同時釘
#   fastmcp-slim），否則 uv 解析會卡 prerelease 檢查
# - molab 連結規則（零上傳零回填，git push 即更新）：
#   https://molab.marimo.io/github/{owner}/{repo}/blob/{branch}/content/<topic>/<id>/<id>_ext.py
#   （repo 必須公開；含私人資訊的參考教材放 ref_data/，已 gitignore）
# - 學員自備 API key：mo.ui.text(kind="password") ＋ env var fallback、mo.stop 擋空值；
#   實測 password 初值不進 export 產物，但部署前仍要全文掃描 key 零外洩
# - 驗證：bash .claude/skills/make-lesson/scripts/verify-ext.sh <topic> <id> [左頁要引用的關鍵字]
#   （sandbox 全 cell 執行＋渲染輸出掃描；需要 GPU 的 cell 要能在無 GPU 環境優雅降級
#   ——mo.stop ＋清楚指引，不能 Traceback）
# - 會打外部 API／LLM 的 cell：
#   * 模型名、max_tokens 等「會換」的設定集中在一格常數（CHAT_MODEL = "..."），全 notebook 只引用它
#   * 學員互動觸發的呼叫（按鈕／輸入框）包 try/except → mo.callout 解釋＋「再跑一次」，
#     不要讓 429／5xx 變成 Traceback；主線示範格可以直接呼叫（失敗就該看到錯）
#   * 推理型模型 max_tokens 給足（4096 起跳），輸出數字會飄 → 左頁寫範圍與方向，不寫點估計
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "marimo",
# ]
# ///
import marimo

__generated_with = "0.23.16"
app = marimo.App(width="medium", app_title="課程標題（實戰）")


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    # ⚡ 課程標題：實戰

    一段開場：這份 notebook 要帶你做出什麼、看到什麼。
    （這裡是課程唯一的可執行版本，解說要完整——學員可能只帶著這份檔案學習。）

    本 notebook 在 molab 免費環境從第一格往下全部執行即可
    （首次安裝套件約 1–2 分鐘）。
    """
    )
    return


@app.cell
def _():
    import marimo as mo
    return (mo,)


# --GPU-CELL-START--（scaffold 預設移除整格；--gpu 才保留）
@app.cell
def _(mo):
    # 【GPU 課才需要這格；純 CPU 課整格刪掉】啟用方式：
    #   1. 把 torch 加進頂部 PEP 723 依賴
    #   2. 把下面 except 分支刪掉、改用 mo.stop 擋下後續（無 GPU 時不能讓後面 Traceback）：
    #      mo.stop(not _ok, mo.md("🛑 沒有偵測到 GPU——在 molab 換 **GPU Server** 再往下跑。"))
    try:
        import torch

        _ok = torch.cuda.is_available()
        _msg = (
            f"**GPU**：{torch.cuda.get_device_name(0)}"
            if _ok
            else "🛑 沒有偵測到 GPU——在 molab 把執行環境換成 **GPU Server** 再往下跑。"
        )
    except ModuleNotFoundError:
        _msg = "ℹ️ 這格是 GPU 檢查佔位：GPU 課照上方註解啟用，純 CPU 課整格刪掉。"
    mo.md(_msg)
    return
# --GPU-CELL-END--


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 1️⃣ 第一節標題

    每一節的節奏：先用 md 講清楚「接下來這格程式為什麼存在、會發生什麼、
    你該盯著哪個輸出看」，再放程式。左頁的對應章節用同一個 emoji 編號。
    """
    )
    return


@app.cell
def _():
    # 本節的程式從這裡開始寫
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 🏆 延伸挑戰

    1. **LEVEL 1**：改個參數就看得到效果的挑戰。
    2. **LEVEL 2**：需要理解本課概念才做得對的挑戰。
    3. **LEVEL 3**：開放式挑戰（換資料、換方法、先猜再驗證）。

    先自己試，卡住再展開下面的提示與參考解答。
    帶得走：下載本檔後 `uvx marimo edit --sandbox 檔名.py`
    在自己電腦繼續玩（依賴會自動安裝）。
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    # 挑戰的折疊解答（不變量：挑戰必附解答／自驗方式；三級是預設形式，可換）：學員先做再看。
    # LEVEL 1/2 給完整可貼的程式碼，LEVEL 3 給方向與驗證方法就好
    # （開放式題目沒有唯一解；給「怎麼判斷自己做對了」比給答案更重要）。
    mo.accordion(
        {
            "💡 LEVEL 1 參考解答": mo.md(
                r"""
    ```python
    # 把要改的那行貼在這裡，加一句「你應該看到…」
    ```
    """
            ),
            "💡 LEVEL 2 參考解答": mo.md(r"""（完整程式碼 + 預期輸出）"""),
            "💡 LEVEL 3 提示": mo.md(r"""（方向、陷阱、以及怎麼驗證自己做對了）"""),
        }
    )
    return


if __name__ == "__main__":
    app.run()
