# FastMCP 4 實戰軌道：真的 FastMCP + 真的 LLM（NVIDIA NIM）
# 不需要 GPU——molab 免費 CPU 環境即可全程執行。
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "marimo",
#     "fastmcp==4.0.0b3",
#     "fastmcp-slim==4.0.0b3",
#     "openai",
# ]
# ///
import marimo

__generated_with = "0.23.16"
app = marimo.App(width="medium", app_title="FastMCP 4 實戰：真伺服器＋真 LLM")


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    # ⚡ FastMCP 4 實戰：真的伺服器、真的 LLM

    瀏覽器版你親手蓋了 60 行迷你 FastMCP——這裡**全部換成真的**：
    真的 `fastmcp` 套件（4.0 beta）、真的 in-memory 連線、
    最後接上一顆真的雲端 LLM，看 AI 自己查菜單、自己下單。

    本 notebook **不需要 GPU**，molab 的免費環境從第一格往下全部執行即可
    （首次安裝套件約 1–2 分鐘）。
    """
    )
    return


@app.cell
def _():
    import marimo as mo
    return (mo,)


@app.cell
def _(mo):
    import json
    import os

    import fastmcp
    from fastmcp import Client, FastMCP

    mo.md(f"✅ 套件就緒：`fastmcp {fastmcp.__version__}`（4.0 系列，beta）")
    return Client, FastMCP, json, os


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 1️⃣ 真的伺服器：@mcp.tool 一行搞定

    同一間飲料店、同兩個函式——但這次不用自己寫 `inspect` 魔法，
    `@mcp.tool` 就是你在瀏覽器版重現過的那個裝飾器的正牌貨。
    """
    )
    return


@app.cell
def _(FastMCP):
    mcp = FastMCP("DrinkShop")

    MENU = {
        "珍珠奶茶": {"M": 50, "L": 60},
        "四季春茶": {"M": 30, "L": 35},
        "芒果冰沙": {"M": 70, "L": 85},
    }

    @mcp.tool
    def search_menu(keyword: str) -> dict:
        """搜尋菜單，回傳名稱含關鍵字的品項與各尺寸價格（單位：新台幣）"""
        return {name: p for name, p in MENU.items() if keyword in name}

    @mcp.tool
    def place_order(item: str, size: str) -> str:
        """下單一杯飲料。item 必須是菜單上的完整品名，size 只能是 M 或 L"""
        price = MENU[item][size]
        return f"訂單成立：{item}（{size}）NT${price}"
    return MENU, mcp


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 2️⃣ 魔法一驗收：真的說明書

    `Client(mcp)` 是 FastMCP 的 **in-memory 連線**——客戶端直接插在伺服器上，
    不開網路埠、不起子行程，最適合拿來看清楚協定本身。
    下面用它送出真的 `tools/list`，看真框架自動生成的說明書
    （跟你在瀏覽器版親手蓋的那份對照看——同樣從型別提示長出來）：
    """
    )
    return


@app.cell
async def _(Client, json, mcp, mo):
    async with Client(mcp) as _c1:
        real_tools = await _c1.list_tools()

    _blocks = []
    for _t in real_tools:
        _blocks.append(
            f"**`{_t.name}`** — {_t.description}\n```json\n"
            + json.dumps(_t.input_schema, ensure_ascii=False, indent=2)
            + "\n```"
        )
    mo.md("\n\n".join(_blocks))
    return (real_tools,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 3️⃣ 魔法二驗收：tools/call 與自動把關

    `call_tool` 就是真的 `tools/call`。第二筆故意漏掉 `size`——
    瀏覽器版是你自己寫的 `required` 檢查在擋，真框架用 pydantic 擋，
    行為一模一樣：函式根本不會被執行。
    """
    )
    return


@app.cell
async def _(Client, json, mcp, mo):
    from fastmcp.exceptions import ToolError

    async with Client(mcp) as _c2:
        _ok = await _c2.call_tool("search_menu", {"keyword": "茶"})
        try:
            await _c2.call_tool("place_order", {"item": "珍珠奶茶"})
            _err_msg = "（沒被擋下？版本行為變了）"
        except ToolError as _e:
            _err_msg = str(_e)

    mo.md(
        "**`search_menu(keyword=\"茶\")` →**\n```json\n"
        + json.dumps(_ok.structured_content, ensure_ascii=False, indent=2)
        + "\n```\n**`place_order(item=\"珍珠奶茶\")`（漏了 size）→ 被擋下：**\n```\n"
        + _err_msg
        + "\n```"
    )
    return (ToolError,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 4️⃣ 置物櫃真實版：SessionProvider 發鑰匙

    左頁第 4 節的 `UserSession` 用**認證身分**當置物櫃鑰匙——這裡沒有帳號系統，
    所以走 FastMCP 4 給未認證連線的另一條路，跟瀏覽器版的演示同一個邏輯：

    - 掛上 `SessionProvider`，伺服器多出一個 `create_session` 工具，發**猜不到的鑰匙**（uuid）
    - 工具宣告 `session_id: SessionId` 參數，用 `get_session()` 開對應的置物櫃

    下面重演瀏覽器版的劇本：小明和小美的請求交錯抵達，各帶各的鑰匙。
    """
    )
    return


@app.cell
def _(mcp):
    from fastmcp.server.sessions import SessionId, SessionProvider, get_session

    mcp.add_provider(SessionProvider())

    @mcp.tool
    async def order_drink(item: str, session_id: SessionId) -> str:
        """點一杯飲料，伺服器會記在這個 session 的置物櫃裡"""
        _s = await get_session(session_id)
        orders = await _s.get("orders", default=[])
        orders.append(item)
        await _s.set("orders", orders)
        return f"已點 {item}（本 session 累計 {len(orders)} 杯）"

    @mcp.tool
    async def my_orders(session_id: SessionId) -> list:
        """查這個 session 點過的所有飲料"""
        _s = await get_session(session_id)
        return await _s.get("orders", default=[])

    session_tools_ready = True
    return (session_tools_ready,)


@app.cell
async def _(Client, ToolError, mcp, mo, session_tools_ready):
    assert session_tools_ready
    async with Client(mcp) as _c3:
        _sid_ming = (await _c3.call_tool("create_session", {})).data
        _sid_mei = (await _c3.call_tool("create_session", {})).data
        _script = [
            (_sid_ming, "小明", "四季春茶"),
            (_sid_mei, "小美", "珍珠奶茶"),
            (_sid_ming, "小明", "珍珠奶茶"),
            (_sid_mei, "小美", "芒果冰沙"),
        ]
        _lines = [
            f"- 🔑 小明拿到鑰匙 `{_sid_ming[:8]}…`、小美拿到 `{_sid_mei[:8]}…`（uuid，猜不到）"
        ]
        for _sid, _who, _item in _script:
            _r = await _c3.call_tool("order_drink", {"item": _item, "session_id": _sid})
            _lines.append(f"- {_who} → {_r.data}")
        _ming = (await _c3.call_tool("my_orders", {"session_id": _sid_ming})).data
        _mei = (await _c3.call_tool("my_orders", {"session_id": _sid_mei})).data
        _lines.append(f"- 🧋 **小明的置物櫃**：{'、'.join(_ming)}")
        _lines.append(f"- 🧋 **小美的置物櫃**：{'、'.join(_mei)}")
        try:
            await _c3.call_tool("my_orders", {"session_id": "guess-1234"})
        except ToolError as _e2:
            _lines.append(f"- 🚫 亂猜的鑰匙被拒：`{_e2}`")
    mo.md("\n".join(_lines))
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 5️⃣ 壓軸：接上真的 LLM，讓 AI 自己點單

    到目前為止都是**我們**在扮 AI 送請求。現在換真的：
    把工具說明書交給一顆雲端 LLM，它自己決定呼叫哪個工具、帶什麼參數。

    需要一把免費的 NVIDIA NIM 金鑰：到
    [build.nvidia.com](https://build.nvidia.com) 用信箱註冊（免綁卡），
    任一模型頁點 **Get API Key** 就能拿到 `nvapi-` 開頭的金鑰。
    金鑰只存在你這個 notebook 的執行階段，不會上傳到任何地方。
    """
    )
    return


@app.cell
def _(mo, os):
    nim_key = mo.ui.text(
        kind="password",
        value=os.environ.get("NVIDIA_API_KEY", ""),
        label="NVIDIA NIM API Key（nvapi-…）",
        full_width=True,
    )
    nim_model = mo.ui.dropdown(
        options=[
            "openai/gpt-oss-120b",
            "moonshotai/kimi-k2.6",
            "meta/llama-3.3-70b-instruct",
        ],
        value="openai/gpt-oss-120b",
        label="模型",
    )
    mo.vstack([nim_key, nim_model])
    return nim_key, nim_model


@app.cell
def _(mo):
    question_form = mo.ui.text(
        value="我想喝點跟茶有關的，預算 60 元，幫我直接下單一杯 L 的",
        label="顧客的需求（改成你自己的試試）",
        full_width=True,
    ).form(submit_button_label="🤖 派 AI 去點單")
    question_form
    return (question_form,)


@app.cell
async def _(Client, json, mcp, mo, nim_key, nim_model, question_form):
    mo.stop(
        not nim_key.value,
        mo.md("👆 先貼上 NIM 金鑰（沒有的話上一格有免費申請方式）。"),
    )
    mo.stop(
        question_form.value is None,
        mo.md("👆 寫好需求後按「派 AI 去點單」。"),
    )

    from openai import OpenAI as _OpenAI

    _llm = _OpenAI(
        base_url="https://integrate.api.nvidia.com/v1", api_key=nim_key.value
    )

    _log = [f"**顧客**：{question_form.value}"]
    async with Client(mcp) as _c4:
        _tools = [
            {
                "type": "function",
                "function": {
                    "name": _t.name,
                    "description": _t.description or "",
                    "parameters": _t.input_schema,
                },
            }
            for _t in await _c4.list_tools()
        ]
        _msgs = [{"role": "user", "content": question_form.value}]
        _final = None
        for _hop in range(6):
            try:
                _resp = _llm.chat.completions.create(
                    model=nim_model.value, messages=_msgs,
                    tools=_tools, temperature=0.2,
                )
            except Exception as _api_err:  # noqa: BLE001 — 金鑰錯誤等以訊息呈現
                _log.append(f"🛑 呼叫 LLM 失敗：`{_api_err}`（金鑰貼對了嗎？）")
                break
            _m = _resp.choices[0].message
            if not _m.tool_calls:
                _final = _m.content
                _log.append(f"**🤖 AI 的回覆**：{_final}")
                break
            _msgs.append(
                {"role": "assistant", "content": _m.content or "",
                 "tool_calls": [_tc.model_dump() for _tc in _m.tool_calls]}
            )
            for _tc in _m.tool_calls:
                _args = json.loads(_tc.function.arguments)
                _log.append(
                    f"- 🤖 AI 呼叫 `{_tc.function.name}` "
                    f"`{json.dumps(_args, ensure_ascii=False)}`"
                )
                try:
                    _r4 = await _c4.call_tool(_tc.function.name, _args)
                    _payload = (
                        json.dumps(_r4.structured_content, ensure_ascii=False)
                        if _r4.structured_content is not None
                        else str(_r4.data)
                    )
                except Exception as _tool_err:  # noqa: BLE001 — 錯誤回饋給 LLM 自我修正
                    _payload = f"錯誤：{_tool_err}"
                _log.append(f"  - 🔌 伺服器回 `{_payload}`")
                _msgs.append(
                    {"role": "tool", "tool_call_id": _tc.id, "content": _payload}
                )
    mo.md("\n\n".join(_log))
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 🏆 延伸挑戰

    1. **加工具**：在 1️⃣ 加一個 `recommend(budget: int)` 工具，
       重新提交需求——AI 會自己發現並使用新工具（說明書是自動長的）。
    2. **戳它的極限**：把需求改成菜單上沒有的東西（「來杯咖啡」），
       觀察 AI 怎麼利用工具回傳的錯誤訊息修正自己。
    3. **AI 自己管鑰匙**：把 4️⃣ 的 `order_drink` / `my_orders` 也交給 AI
       （它的工具清單本來就有 `create_session`）——試著讓它「幫小明點兩杯、
       再報告小明點了什麼」，看它會不會自己先領鑰匙。

    帶得走：下載本檔後 `uvx marimo edit --sandbox fastmcp_gpu.py`
    在自己電腦繼續玩（依賴會自動安裝）。
    """
    )
    return


if __name__ == "__main__":
    app.run()
