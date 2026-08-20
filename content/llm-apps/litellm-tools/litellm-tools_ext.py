# 讓模型做事：Tool calling、結構化輸出與看圖（經 LiteLLM gateway）
# 不需要 GPU——molab 免費 CPU 環境即可全程執行（需要網路：會真的打 gateway）。
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "marimo",
#     "openai>=2.0",
#     "pillow",
# ]
# ///
import marimo

__generated_with = "0.23.16"
app = marimo.App(width="medium", app_title="讓模型做事：Tool calling、結構化輸出與看圖")


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    # 🛠️ 讓模型做事：Tool calling、結構化輸出與看圖

    上一課模型只是「回話」。要把它放進程式裡**做事**，需要三種能力：

    1. **Tool calling**：模型不直接回答，而是回一個「請幫我呼叫 `get_weather(city="台北")`」的
       結構化請求——你執行完把結果餵回去，它再給最終答案。這是所有 Agent 的地基。
    2. **Structured output**：要求模型嚴格照 JSON schema 吐資料，讓 `json.loads` 永遠成功。
    3. **Vision**：把圖片塞進訊息裡，問模型看到什麼。

    三種能力都走同一個 gateway、同一把 key，但**各家支援程度差很多**——
    所以每一節除了示範，都會掃一遍 gateway 上的模型，產出「誰能用」的結論表。

    從第一格往下全部執行即可（首次安裝套件約 1 分鐘）。
    """
    )
    return


@app.cell
def _():
    import base64
    import io
    import json
    import time

    import marimo as mo
    from openai import OpenAI
    from PIL import Image, ImageDraw
    return Image, ImageDraw, OpenAI, base64, io, json, mo, time


@app.cell
def _(OpenAI):
    client = OpenAI(
        base_url="https://litellm.itsmygo.uk/v1",   # 公開端點
        api_key="sk-FiIRnuzLH7ypgf29LTpHNw",        # 教學用 virtual key（只開免費模型，課後撤銷）
    )
    chat_models = sorted(m.id for m in client.models.list() if "embed" not in m.id)
    chat_models
    return chat_models, client


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 1️⃣ 定義一個工具：用 JSON Schema 描述函式

    工具對模型來說就是一份「說明書」：名字、做什麼、參數長什麼樣（JSON Schema）。
    這是 OpenAI 訂的標準格式，gateway 會翻譯給各家供應商。

    先寫真的 Python 函式（這裡假裝查天氣），再寫它的說明書。
    """
    )
    return


@app.cell
def _():
    def get_weather(city: str) -> dict:
        """假的天氣查詢——真實專案這裡會去打氣象 API。"""
        _FAKE = {"台北": {"weather": "晴", "temp_c": 31}, "高雄": {"weather": "多雲", "temp_c": 33}}
        return _FAKE.get(city, {"weather": "未知城市", "temp_c": None})

    TOOLS = [{
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "查詢指定城市的即時天氣",
            "parameters": {
                "type": "object",
                "properties": {"city": {"type": "string", "description": "城市名，例如：台北"}},
                "required": ["city"],
            },
        },
    }]
    return TOOLS, get_weather


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 2️⃣ 第一回合：模型不回答，而是「要求呼叫工具」

    把 `tools=TOOLS` 一起送出去。看回應：`message.content` 是空的（`None` 或 `''`，依供應商），
    `message.tool_calls` 裡有一筆 `get_weather`，`arguments` 是一段 JSON 字串——
    模型自己從「台北現在天氣怎麼樣？」抽出了 `city="台北"`。本課預設模型 `nemotron-3-ultra`
    是推理型，每一發可能要等幾秒到幾十秒。
    """
    )
    return


@app.cell
def _(TOOLS, client, json, mo):
    QUESTION = [{"role": "user", "content": "台北現在天氣怎麼樣？"}]
    round1 = client.chat.completions.create(model="nemotron-3-ultra", messages=QUESTION, tools=TOOLS, max_tokens=512)
    first_call = round1.choices[0].message.tool_calls[0]
    mo.md(
        f"""
    | 欄位 | 值 |
    |---|---|
    | `message.content` | `{round1.choices[0].message.content!r}` |
    | `finish_reason` | `{round1.choices[0].finish_reason}` |
    | `tool_calls[0].id` | `{first_call.id}` |
    | `tool_calls[0].function.name` | `{first_call.function.name}` |
    | `tool_calls[0].function.arguments` | `{first_call.function.arguments}`（字串，要 `json.loads`） |

    解析後的參數：`{json.loads(first_call.function.arguments)}`
    """
    )
    return QUESTION, first_call, round1


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 3️⃣ 第二回合：你執行工具，把結果餵回去

    這是 tool calling 最容易搞錯的地方——對話紀錄要按順序塞三樣東西：

    1. 原本的 user 訊息
    2. 模型的 **assistant 訊息（含 `tool_calls`）**——用手組 dict，別直接塞 SDK 物件
       （序列化後 `content` 是 `null`、欄位齊全度依家而異，有的供應商會 400）
    3. 一則 **`role: "tool"`** 訊息，`tool_call_id` 對上第 2 點的 id，`content` 是你的執行結果

    然後再呼叫一次模型，它就會根據結果寫出最終答案。
    """
    )
    return


@app.cell
def _(QUESTION, TOOLS, client, first_call, get_weather, json, mo):
    _args = json.loads(first_call.function.arguments)
    tool_result = get_weather(**_args)          # ← 真的執行你的函式

    messages_round2 = QUESTION + [
        {"role": "assistant", "content": "",     # 模型的 tool call 回合塞回對話（手組 dict）
         "tool_calls": [{"id": first_call.id, "type": "function",
                         "function": {"name": first_call.function.name,
                                      "arguments": first_call.function.arguments}}]},
        {"role": "tool", "tool_call_id": first_call.id,   # 你執行工具後的結果
         "content": json.dumps(tool_result, ensure_ascii=False)},
    ]
    round2 = client.chat.completions.create(model="nemotron-3-ultra", messages=messages_round2, tools=TOOLS, max_tokens=512)
    mo.md(
        f"""
    工具回傳：`{tool_result}`

    **最終答案**：{round2.choices[0].message.content}
    """
    )
    return messages_round2, round2, tool_result


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ### 把兩回合包成一個迴圈：`run_with_tools`

    真實程式不會手動處理回合——寫一個迴圈：只要模型還在要求呼叫工具，就執行、餵回、再問；
    直到它給出純文字答案為止。**不需要工具的問題它會直接回答**（試試「1+1=?」），
    這個判斷是模型自己做的。這個迴圈就是最小的 Agent。
    """
    )
    return


@app.cell
def _(TOOLS, client, get_weather, json):
    AVAILABLE = {"get_weather": get_weather}   # 工具名 → 真的 Python 函式

    def run_with_tools(question: str, model: str = "nemotron-3-ultra", max_rounds: int = 5):
        """回傳 (最終答案, 追蹤紀錄)。追蹤紀錄記每一次工具呼叫。"""
        _msgs = [{"role": "user", "content": question}]
        _trace = []
        for _ in range(max_rounds):
            _r = client.chat.completions.create(model=model, messages=_msgs, tools=TOOLS, max_tokens=512)
            _m = _r.choices[0].message
            if not _m.tool_calls:                       # 沒有工具請求 → 這就是最終答案
                return (_m.content or "").strip(), _trace
            _msgs.append({"role": "assistant", "content": _m.content or "",
                          "tool_calls": [{"id": tc.id, "type": "function",
                                          "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                                         for tc in _m.tool_calls]})
            for tc in _m.tool_calls:
                _args = json.loads(tc.function.arguments or "{}")
                _out = AVAILABLE[tc.function.name](**_args)
                _trace.append((tc.function.name, _args, _out))
                _msgs.append({"role": "tool", "tool_call_id": tc.id, "content": json.dumps(_out, ensure_ascii=False)})
        return "（超過回合上限）", _trace
    return AVAILABLE, run_with_tools


@app.cell
def _(mo, run_with_tools):
    _rows = []
    for _q in ["高雄跟台北哪裡比較熱？", "1+1=?"]:
        _ans, _trace = run_with_tools(_q)
        _rows.append({"問題": _q, "工具呼叫次數": len(_trace),
                      "呼叫了": "、".join(f"{n}({a['city']})" for n, a, _ in _trace) or "（沒用工具）",
                      "答案": _ans[:80]})
    mo.ui.table(_rows, selection=None)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 4️⃣ 跨模型實測：誰能可靠地呼叫工具？

    同一段程式、同一個問題，掃遍教學 key 能用的所有對話模型。三種結果：

    - ✅ 正確發出 `get_weather` 且參數是合法 JSON
    - ⚠️ 沒報錯但也沒呼叫工具（直接用文字瞎掰天氣）——它不支援、或忽略了 `tools`
    - ❌ 供應商報錯
    """
    )
    return


@app.cell
def _(QUESTION, TOOLS, chat_models, client, json, mo, time):
    tool_scan = []
    for _name in chat_models:
        _t0 = time.perf_counter()
        try:
            _r = client.chat.completions.create(model=_name, messages=QUESTION, tools=TOOLS, max_tokens=512)
            _calls = _r.choices[0].message.tool_calls
            if _calls and _calls[0].function.name == "get_weather":
                _args = json.loads(_calls[0].function.arguments)
                tool_scan.append({"模型": _name, "結果": "✅", "秒": round(time.perf_counter() - _t0, 1),
                                  "說明": f"get_weather({_args})"})
            else:
                tool_scan.append({"模型": _name, "結果": "⚠️", "秒": round(time.perf_counter() - _t0, 1),
                                  "說明": "未呼叫工具，直接回答：" + (_r.choices[0].message.content or "")[:40]})
        except Exception as _e:  # noqa: BLE001  跨供應商掃描：任何錯都要記下來而不是中斷
            tool_scan.append({"模型": _name, "結果": "❌", "秒": round(time.perf_counter() - _t0, 1),
                              "說明": str(_e)[:70]})
    mo.ui.table(tool_scan, selection=None)
    return (tool_scan,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 5️⃣ Structured output：逼模型吐合法 JSON

    Pipeline 要穩定地 `json.loads` 模型輸出，就用 `response_format` 的 `json_schema` 模式。
    先看**沒有**約束時模型怎麼回——通常會包在 markdown 裡、欄位名還自己取：
    """
    )
    return


@app.cell
def _(client, mo):
    PROMPT = [{"role": "user", "content": "小明今年12歲，住在台北，喜歡籃球跟圍棋。請抽取人物資料。"}]
    _free = client.chat.completions.create(model="nemotron-3-ultra", messages=PROMPT, max_tokens=512)
    mo.md("**沒有 schema 時的回答**（漂亮，但程式不好解析）：\n\n" + _free.choices[0].message.content)
    return (PROMPT,)


@app.cell
def _(PROMPT, client, json, mo):
    RESPONSE_FORMAT = {
        "type": "json_schema",
        "json_schema": {
            "name": "person_info",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "age": {"type": "integer"},
                    "city": {"type": "string"},
                    "hobbies": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["name", "age", "city", "hobbies"],
                "additionalProperties": False,
            },
        },
    }
    _strict = client.chat.completions.create(model="nemotron-3-ultra", messages=PROMPT,
                                             response_format=RESPONSE_FORMAT, max_tokens=512)
    _raw = (_strict.choices[0].message.content or "").strip()
    try:
        person = json.loads(_raw)   # 直接解析，不用正則去撈
        _out = mo.md(
            f"""
    **有 schema 時的原始回答**：`{_raw}`

    `json.loads` 之後：`person["name"]` = {person["name"]}、`person["age"]` = {person["age"]}
    （型別是 `{type(person["age"]).__name__}`）、`person["hobbies"]` = {person["hobbies"]}
    """
        )
    except json.JSONDecodeError:
        person = None
        _out = mo.callout(mo.md(
            "這一發**沒有**照 schema 回——原始回答：\n\n" + _raw[:300] +
            "\n\n`nemotron-3-ultra` 有三個上游，其中有的不支援 `response_format`，gateway 的 `drop_params` "
            "會默默拿掉這個參數。重新執行這格通常就會落到遵守 schema 的來源。這正是下一小節要講的陷阱。"
        ), kind="warn")
    _out
    return RESPONSE_FORMAT, person


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ### 陷阱：不支援的供應商會「默默」忽略 schema

    gateway 開了 `drop_params`：某家不認得 `response_format`，這個參數會被**悄悄拿掉**，
    呼叫不報錯、輸出看似正常、實則毫無約束。更麻煩的是像 `nemotron-3-ultra` 這種
    **同一個模型名背後有多個上游**的情況：這一發嚴格遵守、下一發回一張 markdown 表格，
    取決於落到哪家。所以驗收標準不是「有沒有報錯」，而是**逐欄驗證輸出**——
    下面對每個模型都檢查四個欄位的型別（多跑幾次，結果會變）。
    """
    )
    return


@app.cell
def _(PROMPT, RESPONSE_FORMAT, chat_models, client, json, mo, time):
    def validate(text: str):
        """回 (判定, 說明)。逐欄驗證，不能只看有沒有報錯。"""
        try:
            _d = json.loads(text)
        except Exception:  # noqa: BLE001  不是合法 JSON 就是 ❌，原因不重要
            return "❌", f"不是合法 JSON：{text[:40]!r}"
        _ok = (isinstance(_d.get("name"), str) and isinstance(_d.get("age"), int)
               and isinstance(_d.get("city"), str) and isinstance(_d.get("hobbies"), list))
        return ("✅", json.dumps(_d, ensure_ascii=False)[:60]) if _ok else ("⚠️", f"JSON 合法但欄位/型別不符：{text[:40]}")

    schema_scan = []
    for _name in chat_models:
        _t0 = time.perf_counter()
        try:
            _r = client.chat.completions.create(model=_name, messages=PROMPT, response_format=RESPONSE_FORMAT, max_tokens=512)
            _mark, _detail = validate((_r.choices[0].message.content or "").strip())
        except Exception as _e:  # noqa: BLE001
            _mark, _detail = "❌", str(_e)[:70]
        schema_scan.append({"模型": _name, "結果": _mark, "秒": round(time.perf_counter() - _t0, 1), "說明": _detail})
    mo.vstack([
        mo.ui.table(schema_scan, selection=None),
        mo.md("結論：✅ 的才能放進 pipeline 依賴 schema；❌ 卻沒報 HTTP 錯的那些，就是 `drop_params` 默默拿掉參數的證據。"),
    ])
    return schema_scan, validate


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 6️⃣ Vision：把圖片塞進訊息

    多模態訊息 = `content` 變成**一個陣列**：文字塊 + 圖片塊。圖片用 data URL（base64）
    或公開網址。為了驗證模型「真的看到圖」而不是瞎掰，我們當場畫一張
    **白底紅色圓形**——答案已知，答對才算數。
    """
    )
    return


@app.cell
def _(Image, ImageDraw, base64, io, mo):
    _img = Image.new("RGB", (200, 200), "white")
    ImageDraw.Draw(_img).ellipse((50, 50, 150, 150), fill="red")
    _buf = io.BytesIO()
    _img.save(_buf, format="PNG")
    png_bytes = _buf.getvalue()
    data_url = "data:image/png;base64," + base64.b64encode(png_bytes).decode()

    VISION_MESSAGES = [{
        "role": "user",
        "content": [   # 多模態訊息＝文字塊＋圖片塊
            {"type": "text", "text": "圖片裡是什麼形狀？什麼顏色？用繁體中文一句話回答。"},
            {"type": "image_url", "image_url": {"url": data_url}},
        ],
    }]
    mo.hstack([mo.image(png_bytes, width=120), mo.md(f"data URL 長度：{len(data_url)} 字元")], align="center")
    return VISION_MESSAGES, data_url, png_bytes


@app.cell
def _(VISION_MESSAGES, chat_models, client, mo, time):
    vision_scan = []
    for _name in chat_models:
        _t0 = time.perf_counter()
        try:
            _r = client.chat.completions.create(model=_name, messages=VISION_MESSAGES, max_tokens=512)
            _ans = (_r.choices[0].message.content or "").strip().replace("\n", " ")
            _correct = ("紅" in _ans or "red" in _ans.lower()) and ("圓" in _ans or "circle" in _ans.lower())
            vision_scan.append({"模型": _name, "結果": "✅" if _correct else "⚠️ 沒看到圖在瞎掰",
                                "秒": round(time.perf_counter() - _t0, 1), "回答": _ans[:50]})
        except Exception as _e:  # noqa: BLE001
            vision_scan.append({"模型": _name, "結果": "❌", "秒": round(time.perf_counter() - _t0, 1),
                                "回答": str(_e)[:70]})
    mo.vstack([
        mo.ui.table(vision_scan, selection=None),
        mo.md("結論：圖片任務要**指名**看得懂圖的模型（實測只有 `gemini-3.5-flash`；本系列預設的 "
              "`nemotron-3-ultra` 不吃圖），別丟給多來源的群組名——它會輪到不吃圖的家。"),
    ])
    return (vision_scan,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 🏆 延伸挑戰

    1. **LEVEL 1**：在 1️⃣ 的 `get_weather` 與 `TOOLS` 旁邊加第二個工具 `convert_currency(amount, from, to)`
       （匯率寫死即可），問「100 美元換台幣多少？」——模型會自己挑對工具嗎？
    2. **LEVEL 2**：改 5️⃣ 的 schema，把 `age` 改成 `{"type": "integer", "minimum": 0, "maximum": 150}`，
       再加一個 `"email": {"type": "string"}` 欄位但原文沒有 email——模型會填什麼？
       嚴格模式下它被迫填，這就是 schema 設計要留 `null` 或 optional 的理由。
    3. **LEVEL 3**：把 3️⃣ 的 `run_with_tools` 改成「工具執行失敗時，把錯誤訊息當 tool 結果餵回去」
       （例如查一個不存在的城市），觀察模型會不會自我修正、換個問法或誠實說查不到。

    帶得走：下載本檔後 `uvx marimo edit --sandbox litellm-tools_ext.py`
    在自己電腦繼續玩。下一課：**FastMCP 4**——把「工具說明書」這件事交給框架自動生成，
    還能讓任何 AI 客戶端直接接上你的函式。
    """
    )
    return


if __name__ == "__main__":
    app.run()
