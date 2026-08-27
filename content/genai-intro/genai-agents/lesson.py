import marimo

__generated_with = "0.23.16"
app = marimo.App(width="medium", app_title="AI Agent 與 MCP：模型長出手腳（實驗場）")


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    # 🧪 AI Agent 與 MCP：模型長出手腳（實驗場）

    這是本課的**實驗場**。左側教學讀到哪，就回到這裡動手做——
    每一格程式碼都可以**直接修改、立即重跑**（點格子右上的 ▶，或按 `Ctrl+Enter`）。
    改壞了也沒關係：重新整理頁面就會回到原版。

    這一課把「模型怎麼呼叫工具」的水電工程整套拆開：你會親手執行一次 tool call、
    算一筆 agent loop 的上下文帳、再看懂 MCP 到底解掉了什麼地獄。

    模型的兩句輸出是**實測紀錄**（qwen3.5-2b、temperature=0、2026-08）；
    解析、查表、組訊息的管線則是**真的在你瀏覽器裡跑**——改了就重算。
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
    import json

    import matplotlib.pyplot as plt
    import numpy as np
    return html_mod, json, np, plt


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 1️⃣ Function Calling 的水電工程

    「模型呼叫工具」聽起來很魔法，實際上模型只做一件事：**吐出一段 JSON 文字**。
    剩下的全是你的程式在做：解析 JSON → 執行真的函式 → 把結果塞回對話 → 再問一次模型。

    下面是一次真實互動的完整材料。第一格是當時餵給模型的 system prompt 與
    模型的實際輸出（實測紀錄）；第二格是**你的**工具資料庫——改它，再看下面的管線重跑。
    """
    )
    return


@app.cell
def _():
    # ── 實測紀錄（qwen3.5-2b、temperature=0、2026-08）——這幾個字串是當時的原始輸出 ──
    SYSTEM = (
        "你是一個助理，可以使用以下工具：\n"
        "get_weather(city)：查詢城市目前天氣，回傳氣溫、天氣狀況與降雨機率。\n\n"
        '規則：需要工具時，只輸出一行 JSON，格式為 '
        '{"tool": "get_weather", "args": {"city": "城市名"}}，不要輸出任何其他文字。\n'
        "不需要工具就直接用繁體中文回答。"
    )
    Q1 = "台北現在天氣怎麼樣？出門要帶傘嗎？"
    FINAL = "根據工具回傳的結果，台北目前氣溫為 24 度，天氣狀況為小雨，降雨機率為 80%。因此，您出門時建議攜帶雨傘。"
    ORIG_TAIPEI = {"temp_c": 24, "condition": "小雨", "rain_prob": 80}

    Q2 = "什麼是光合作用？用一句話說明。"
    DIRECT = "光合作用是植物利用陽光將二氧化碳和水轉化為葡萄糖並釋放氧氣的過程。"
    return DIRECT, FINAL, ORIG_TAIPEI, Q1, Q2, SYSTEM


@app.cell
def _():
    # ===== 你的工具資料庫（教學用模擬資料——改我！）=====
    WEATHER_DB = {
        "台北": {"temp_c": 24, "condition": "小雨", "rain_prob": 80},
        "台中": {"temp_c": 31, "condition": "晴", "rain_prob": 10},
    }
    # 也可以改 city 試試資料庫裡沒有的城市，看管線怎麼處理錯誤
    CALL = '{"tool": "get_weather", "args": {"city": "台北"}}'
    return CALL, WEATHER_DB


@app.cell
def _(CALL, FINAL, ORIG_TAIPEI, Q1, SYSTEM, WEATHER_DB, html_mod, json, mo):
    # ── 管線：解析 → 執行 → 組訊息（真的在跑）──
    _s = CALL
    _call = json.loads(_s[_s.index("{"): _s.rindex("}") + 1])  # 防模型在 JSON 外多包字
    _city = _call["args"]["city"]
    if _city in WEATHER_DB:
        _result = WEATHER_DB[_city]
    else:
        _result = {"error": f"查無城市「{_city}」"}  # 錯誤也回給模型，讓它自己修正

    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": Q1},
        {"role": "assistant", "content": _s},
        {"role": "user", "content": f"工具回傳結果：{json.dumps(_result, ensure_ascii=False)}\n請根據結果回答使用者原本的問題。"},
        {"role": "assistant", "content": FINAL},
    ]

    _colors = {"system": "#8172B2", "user": "#4C72B0", "assistant": "#DD8452"}
    _tags = {"system": "system", "user": "user", "assistant": "assistant"}

    def _bubble(m, note=""):
        c = _colors[m["role"]]
        note_html = f'<div style="font-size:11px;color:#8a949b;margin-top:4px">{note}</div>' if note else ""
        return (
            f'<div style="border:2px solid {c};border-radius:12px;padding:8px 12px;margin:6px 0;">'
            f'<div style="font-size:11px;font-weight:800;letter-spacing:.06em;color:{c}">{_tags[m["role"]]}</div>'
            f'<div style="font-size:13.5px;line-height:1.7;white-space:pre-wrap">{html_mod.escape(m["content"])}</div>'
            f"{note_html}</div>"
        )

    _notes = ["工具說明書就寫在這裡", "", "模型輸出（實測紀錄）——就只是一段 JSON 文字",
              "你的程式剛剛執行的查表結果", "模型輸出（實測紀錄，對應原始資料）"]
    _warn = ""
    if WEATHER_DB.get("台北") != ORIG_TAIPEI or _city != "台北":
        _warn = (
            '<div style="border-left:4px solid #C44E52;padding:8px 12px;margin:8px 0;font-size:13px;line-height:1.7">'
            "你改了資料（或城市）——上面第 4 則訊息已經跟著變了；但最後那句回答是<b>當時的實測紀錄</b>，"
            "真實系統會把新的工具結果再送給模型、產生新的回答。</div>"
        )
    mo.Html("<div>" + "".join(_bubble(m, n) for m, n in zip(messages, _notes)) + _warn + "</div>")
    return (messages,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    看清楚第 3 則訊息：所謂「呼叫工具」，就是模型**用嘴巴說**「我要呼叫 get_weather」。
    真正動手的是你的程式——`json.loads` 那行才是水電工程的全部祕密。
    也注意查無城市時我們把**錯誤也回給模型**：這是 agent 能「自我修正」的關鍵習慣。

    對照組：問「什麼是光合作用？」時，同一個模型、同一份 system prompt，
    它判斷**不需要工具**、直接回答——「要不要用工具」本身就是模型的決策：
    """
    )
    return


@app.cell
def _(DIRECT, Q2, html_mod, mo):
    mo.Html(
        f'<div style="border:2px solid #4C72B0;border-radius:12px;padding:8px 12px;margin:6px 0">'
        f'<div style="font-size:11px;font-weight:800;color:#4C72B0">user</div>'
        f'<div style="font-size:13.5px;line-height:1.7">{html_mod.escape(Q2)}</div></div>'
        f'<div style="border:2px solid #DD8452;border-radius:12px;padding:8px 12px;margin:6px 0">'
        f'<div style="font-size:11px;font-weight:800;color:#DD8452">assistant（實測紀錄——沒有 JSON，直接回答）</div>'
        f'<div style="font-size:13.5px;line-height:1.7">{html_mod.escape(DIRECT)}</div></div>'
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 2️⃣ Agent Loop 的上下文帳

    API 是無狀態的：每呼叫一次模型，都要把**到目前為止的全部訊息**重送一遍。
    上面那次「查天氣」總共呼叫了模型兩次——把兩次請求實際送出的字元數畫出來：
    """
    )
    return


@app.cell
def _(messages, np, plt):
    # 兩次 API 呼叫實際攜帶的訊息（第 1 次：前 2 則；第 2 次：前 4 則），字元數真算
    _lens = [len(m["content"]) for m in messages]
    _calls = ["API call 1\n(ask)", "API call 2\n(after tool)"]
    _payloads = [sum(_lens[:2]), sum(_lens[:4])]
    _new = [_payloads[0], _payloads[1] - _payloads[0]]
    _fig, _ax = plt.subplots(figsize=(6.8, 3.8))
    _x = np.arange(2)
    _ax.bar(_x, [_payloads[0], _payloads[0]], color="#4C72B0",
            edgecolor="#1C2B33", linewidth=1.1, zorder=3, label="already sent before")
    _ax.bar(_x, [0, _new[1]], bottom=[_payloads[0], _payloads[0]], color="#DD8452",
            edgecolor="#1C2B33", linewidth=1.1, zorder=3, label="new this call")
    for _i, _p in enumerate(_payloads):
        _ax.text(_i, _p + 8, f"{_p} chars", ha="center", fontsize=11, fontweight="bold")
    _ax.set_xticks(_x, _calls)
    _ax.set_ylabel("payload size (characters)")
    _ax.set_title("stateless API: every call resends the whole history")
    _ax.legend(fontsize=9)
    _ax.grid(axis="y", alpha=0.3)
    _fig.tight_layout()
    _fig
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    才一個工具、一輪對話，第二次請求就比第一次大了一截——藍色那塊**每一輪都要重送**。
    真實 agent 動輒幾十個工具說明書、十幾輪呼叫，上下文就是這樣滾大的：
    這正是第 1 課的 context window、第 3 課的 KV cache／prompt caching
    在 agent 時代變成顯學的原因。

    ## 3️⃣ MCP：工具界的 USB 接口

    每家 AI 應用（Claude Desktop、IDE、你的客服系統…）都想接每種工具
    （檔案、資料庫、天氣、行事曆…）。沒有標準的話，M 個應用 × N 個工具＝
    **M×N 份客製配接程式**。MCP（Model Context Protocol）把它變成：
    工具做成 **MCP server**（一次）、應用做成 **MCP client**（一次），合計 M+N 份：
    """
    )
    return


@app.cell
def _(np, plt):
    _m, _n = 4, 6  # 4 個應用、6 種工具
    _fig, (_ax1, _ax2) = plt.subplots(1, 2, figsize=(7.6, 4.0))
    _apps_y = np.linspace(0.15, 0.85, _m)
    _tools_y = np.linspace(0.05, 0.95, _n)
    for _ax, _title in ((_ax1, f"without MCP: {_m}x{_n} = {_m*_n} adapters"),
                        (_ax2, f"with MCP: {_m}+{_n} = {_m+_n} adapters")):
        _ax.set_xlim(0, 1)
        _ax.set_ylim(0, 1)
        _ax.axis("off")
        _ax.set_title(_title, fontsize=10, fontweight="bold")
    for _ay in _apps_y:
        for _ty in _tools_y:
            _ax1.plot([0.12, 0.88], [_ay, _ty], color="#C44E52", alpha=0.45, linewidth=1.2, zorder=1)
    _mid = 0.5
    for _ay in _apps_y:
        _ax2.plot([0.12, 0.5], [_ay, _mid], color="#55A868", linewidth=1.6, zorder=1)
    for _ty in _tools_y:
        _ax2.plot([0.5, 0.88], [_mid, _ty], color="#55A868", linewidth=1.6, zorder=1)
    for _ax in (_ax1, _ax2):
        _ax.scatter([0.12] * _m, _apps_y, s=220, color="#4C72B0", edgecolor="#1C2B33", zorder=3)
        _ax.scatter([0.88] * _n, _tools_y, s=220, color="#DD8452", edgecolor="#1C2B33", zorder=3)
        _ax.text(0.12, 0.97, "apps", ha="center", fontsize=9, fontweight="bold", color="#4C72B0")
        _ax.text(0.88, 0.99, "tools", ha="center", fontsize=9, fontweight="bold", color="#DD8452")
    _ax2.scatter([0.5], [_mid], s=340, color="#55A868", edgecolor="#1C2B33", zorder=3)
    _ax2.text(0.5, 0.58, "MCP", ha="center", fontsize=9, fontweight="bold", color="#55A868")
    _fig.tight_layout()
    _fig
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r'''
    寫一個 MCP server 有多簡單？用 FastMCP 就是幫函式掛個修飾器
    （參考程式——需要安裝 `fastmcp` 套件，本站
    [MCP 系列課](/mcp-servers/)有完整實作）：

    ```python
    from fastmcp import FastMCP

    mcp = FastMCP("weather")

    @mcp.tool
    def get_weather(city: str) -> dict:
        """查詢城市目前天氣，回傳氣溫、天氣狀況與降雨機率。"""
        return weather_db[city]

    mcp.run()   # 任何 MCP client（Claude Desktop、IDE…）都能接上來
    ```

    注意 docstring：**工具說明書就是給模型看的教材**——它寫得好不好，
    直接決定模型會不會用、用得對不對。

    ## 4️⃣ 你的實驗區

    下面這格是你的，改完按 ▶ 重跑。挑戰在左頁「換你動手」，做完再開解答對照。
    '''
    )
    return


@app.cell
def _(json):
    # ===== 你的實驗區 =====
    # LEVEL 3 起點：設計你自己的工具呼叫格式，用 json.loads 驗證它合法
    my_call = '{"tool": "calc", "args": {"expr": "3*7"}}'
    parsed = json.loads(my_call)
    print("工具名：", parsed["tool"])
    print("參數：", parsed["args"])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.accordion(
        {
            "💡 LEVEL 1 參考解答": mo.md(
                r"""
    在 1️⃣ 的工具資料庫格把 `CALL` 改成：

    ```python
    CALL = '{"tool": "get_weather", "args": {"city": "台中"}}'
    ```

    管線重跑後，第 4 則訊息變成台中的資料（31 度、晴、降雨 10%）。
    再試資料庫裡沒有的城市（例如「花蓮」）：管線不會炸掉，
    而是把 `{"error": "查無城市「花蓮」"}` 回給模型——
    真實系統裡模型看到錯誤會自己修正（換城市名、或問使用者）。
    """
            ),
            "💡 LEVEL 2 參考解答": mo.md(
                r"""
    第 2 節的圖已經給了證據：第二次呼叫的 payload ＝ 前四則訊息全部。
    如果你的程式忘了把工具結果（第 4 則）塞回去，模型第二次看到的對話
    就停在「我說要呼叫 get_weather」——它**根本不知道結果**，
    只能再喊一次要呼叫工具（無窮迴圈），或憑空編一個答案（幻覺）。

    這是新手寫 agent loop 最常見的 bug：**工具執行了，結果沒有回到對話裡**。
    記住訊息順序：assistant(工具呼叫) → user/tool(工具結果) → assistant(最終回答)。
    """
            ),
            "💡 LEVEL 3 提示": mo.md(
                r"""
    設計計算機工具的三步：

    1. **寫說明書**（給模型看的）：`calc(expr)：計算數學算式，回傳數字。`
       加進 system prompt 的工具清單。
    2. **定格式**：`{"tool": "calc", "args": {"expr": "3*7"}}`——
       在實驗區用 `json.loads` 驗證你寫的格式合法。
    3. **想清楚觸發時機**：哪些問題該用 calc？（「347×892 是多少」該用；
       「畢氏定理是什麼」不該用。）說明書寫得越清楚，模型的判斷越準。

    怎麼驗證自己做對了：把你的工具說明書跟第 1 節的 `SYSTEM` 對照——
    有沒有講清楚「工具做什麼」「參數是什麼」「什麼格式輸出」三件事？
    缺一件，模型就會在那一件上出錯。
    """
            ),
        }
    )
    return


if __name__ == "__main__":
    app.run()
