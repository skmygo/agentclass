# MLflow Tracing：LLM 應用的每一步都留下軌跡
# 不需要 GPU、不需要 API key——molab 免費 CPU 環境即可全程執行。
# 本課用一個「規則式的假 LLM」代替真模型：tracing 的機制與真模型完全一樣，
# 但不花錢、不連外、每次跑出來的內容一致。
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "marimo",
#     "mlflow>=3.0",
#     "pandas",
# ]
# ///
import marimo

__generated_with = "0.23.16"
app = marimo.App(width="medium", app_title="MLflow Tracing：LLM 應用的每一步都留下軌跡（實戰）")


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    # 🔍 MLflow Tracing：LLM 應用的每一步都留下軌跡

    客服機器人回了一句「手冊裡沒有寫。」，客戶投訴了。你手上只有這句話。

    到底是**檢索**沒撈到那份文件？還是撈到了、但 **prompt** 沒把它放進去？
    還是都對，**模型**自己不肯回答？這一次花了幾毫秒、用的是哪一版 prompt？
    ——傳統的 log 只會告訴你「有一個請求進來、有一個回應出去」，中間那段是黑的。

    **Tracing** 就是把中間那段點亮：一次請求＝一棵 **span 樹**，
    每個步驟一個 span，每個 span 都留下 inputs、outputs、耗時、屬性。

    | | **run**（第 1 課） | **trace**（這一課） |
    |---|---|---|
    | 記錄什麼 | 一次**訓練** | 一次**請求** |
    | 一天幾筆 | 幾十筆 | 幾十萬筆 |
    | 裡面有什麼 | params / metrics / artifacts | **span 樹**（每步的 inputs／outputs／耗時） |
    | 好壞怎麼判斷 | 一個 AUC 說了算 | 沒有標準答案，**要人標、要 scorer 打分** |
    | 版本控制什麼 | 模型（Registry） | **prompt**（Prompt Registry） |

    這份 notebook 帶你做完：

    0. 準備：一個假 LLM 客服（三條知識庫）
    1. 第一個 trace：三層 `@mlflow.trace`，跑三個問題
    2. 查回來：`search_traces` 表格、`get_trace` 看 span 樹
    3. `span_type`：那個字串到底有什麼用
    4. 屬性、標籤、搜尋：`set_attributes`、`update_current_trace`、`filter_string`
    5. 誰最慢：把 71 毫秒拆給每個 span
    6. 人工評估：`log_feedback` / `log_expectation` 掛在 trace 上
    7. 自動評估：`@scorer` ＋ `mlflow.genai.evaluate`
    8. Prompt Registry：prompt 也有版本、alias、晉升與回滾
    9. 串起來：v1 vs v2，用 trace 比較兩版 prompt
    10. 你的實驗場：問一題、切一版 prompt、看它的 trace

    從第一格往下全部執行即可（首次安裝套件約 1–2 分鐘）。
    所有紀錄都寫在本機一個暫存資料夾，不會連到任何伺服器、不需要任何金鑰。
    """
    )
    return


@app.cell
def _():
    import contextlib
    import html
    import io
    import json
    import logging
    import shutil
    import tempfile
    import time
    import warnings
    from pathlib import Path

    import marimo as mo
    import mlflow
    import pandas as pd
    from mlflow.entities import AssessmentSource, AssessmentSourceType

    # MLflow 建表提示會蓋掉教學輸出，關小聲；真的出錯還是會噴
    logging.getLogger("mlflow").setLevel(logging.ERROR)
    warnings.filterwarnings("ignore")
    return (
        AssessmentSource,
        AssessmentSourceType,
        Path,
        contextlib,
        html,
        io,
        json,
        mlflow,
        mo,
        pd,
        shutil,
        tempfile,
        time,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 0️⃣ 準備：一個假 LLM 客服

    **這一課不打真的 LLM。**理由很直接：你不需要 API key 就能學會 tracing，
    而且假模型每次回答都一樣，數字才對得起來。

    假 LLM 是**規則式**的——它會讀 prompt 裡的指示照做：

    - prompt 的「資料：」後面有東西 → 就照抄那段當答案（模擬「有引用來源的回答」）
    - 資料是空的、prompt 又**沒有**拒答規則 → 它會**編一個答案**
      （模擬真實 LLM 最常見的失敗：沒人叫它閉嘴，它就開始猜）
    - prompt 有拒答規則 → 回「手冊裡沒有寫。」

    `time.sleep()` 是**刻意加上去的模擬延遲**（檢索 20 毫秒、生成 50 毫秒），
    好讓後面「哪一步最慢」看得出比例——真模型的生成通常是幾百毫秒到幾秒。

    **重點是：換成真模型，這一課的每一行 tracing 程式都不用改。**
    第 9️⃣ 節末尾會告訴你怎麼換（一行 `mlflow.openai.autolog()`）。

    紀錄簿一樣是 sqlite（檔案後端已進維護模式，而且 Prompt Registry 只有 DB 後端才有）。
    """
    )
    return


@app.cell
def _(Path, mlflow, mo, shutil, tempfile):
    WORK = Path(tempfile.gettempdir()) / "mlflow-tracing-lesson"
    shutil.rmtree(WORK, ignore_errors=True)          # 重跑時先清乾淨，數字才一致
    WORK.mkdir(parents=True, exist_ok=True)

    mlflow.set_tracking_uri(f"sqlite:///{WORK}/mlflow.db")
    mlflow.create_experiment("客服機器人", artifact_location=str(WORK / "artifacts"))
    mlflow.set_experiment("客服機器人")
    EXP_ID = mlflow.get_experiment_by_name("客服機器人").experiment_id

    # 客服知識庫：三條，就三條。檢索邏輯是「問題裡有這個詞就命中」——夠笨，才看得清 trace 在說什麼
    DOCS = {
        "退貨": "退貨期限為 7 天，商品需保留原包裝與吊牌。",
        "運費": "單筆滿 1000 元免運，未滿運費 80 元。",
        "付款": "支援信用卡、超商代碼與貨到付款。",
    }

    mo.md(f"紀錄簿：`{WORK}/mlflow.db`　·　experiment id：`{EXP_ID}`　·　知識庫 {len(DOCS)} 條")
    return DOCS, EXP_ID, WORK


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 1️⃣ 第一個 trace：三個裝飾器，一棵樹

    要讓一個函式被記錄下來，只要在它頭上加一行 `@mlflow.trace`。

    我們的客服有三層，剛好對應真實 RAG 應用的三個步驟：

    - `retrieve()` — 去知識庫找相關文件（`span_type="RETRIEVER"`）
    - `fake_llm()` — 把 prompt 丟給模型（`span_type="LLM"`）
    - `answer()` — 把上面兩步串起來（`span_type="CHAIN"`）

    `answer()` 呼叫另外兩個函式，MLflow 就自動把它們變成**巢狀 span**——
    你不用手動宣告誰是誰的父節點，**呼叫關係就是樹的形狀**。

    另外兩行是這一課後面會反覆用到的：

    - `mlflow.get_current_active_span().set_attributes({...})`：往**這個 span** 掛自訂欄位
    - `mlflow.update_current_trace(tags={...})`：往**整條 trace** 貼標籤（之後用來搜尋）
    """
    )
    return


@app.cell
def _(DOCS, mlflow, time):
    PROMPT_V1 = "你是客服。只根據資料回答。\n資料：{{context}}\n問題：{{question}}"


    @mlflow.trace(span_type="RETRIEVER")
    def retrieve(question: str) -> list[dict]:
        time.sleep(0.02)                                    # 模擬向量檢索的延遲
        return [{"doc": k, "text": v} for k, v in DOCS.items() if k in question]


    @mlflow.trace(span_type="LLM")
    def fake_llm(prompt: str) -> dict:
        time.sleep(0.05)                                    # 模擬生成的延遲
        _ctx = prompt.split("資料：")[-1].split("\n問題：")[0].strip()
        if _ctx:
            _ans = _ctx                                     # 有資料 → 照著資料回答
        elif "不要自己猜" in prompt:
            _ans = "手冊裡沒有寫。"                          # 有拒答規則 → 老實說不知道
        else:
            _ans = "可以分期，通常提供 3 期與 6 期免利息。"   # 沒規則 → 開始編（模擬幻覺）
        if "以「您好，」開頭" in prompt:
            _ans = "您好，" + _ans
        return {
            "content": _ans,
            "usage": {"prompt_tokens": len(prompt), "completion_tokens": len(_ans)},
        }


    @mlflow.trace(name="answer", span_type="CHAIN")
    def answer(question: str) -> str:
        ctx = retrieve(question)
        mlflow.get_current_active_span().set_attributes(
            {"n_docs": len(ctx), "question_len": len(question)}
        )
        text = ctx[0]["text"] if ctx else ""
        prompt = PROMPT_V1.replace("{{context}}", text).replace("{{question}}", question)
        out = fake_llm(prompt)
        mlflow.update_current_trace(tags={"topic": ctx[0]["doc"] if ctx else "none"})
        return out["content"]
    return PROMPT_V1, answer, fake_llm, retrieve


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    三個問題，最後一個故意問一件知識庫裡沒有的事——看它會不會老實說不知道。
    """
    )
    return


@app.cell
def _(answer, mo):
    QUESTIONS = ["退貨要多久內？", "運費怎麼算？", "可以分期嗎？"]
    ANSWERS_V1 = [answer(_q) for _q in QUESTIONS]

    mo.md(
        "\n".join(
            f"- **{_q}**　→　{_a}" for _q, _a in zip(QUESTIONS, ANSWERS_V1, strict=True)
        )
    )
    return ANSWERS_V1, QUESTIONS


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    第三題露餡了：知識庫裡**沒有**分期付款這條，它卻講得斬釘截鐵。
    這就是我們要用 tracing 抓的東西——而且注意：**光看這句回答，你分不出它是猜的還是查到的**。
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 2️⃣ 查回來：先 flush，再 search

    trace 是**非同步寫入**的（不然每個請求都要等資料庫寫完才能回應，太慢了）。
    所以在 notebook 或測試腳本裡查之前，一定要先叫它把緩衝區倒乾淨：

    `mlflow.flush_trace_async_logging()`

    **忘了這一行，你查到的筆數是「不一定」——而且不會有任何錯誤訊息。**
    實測跑完三題馬上查：有時 0 筆、有時 2 筆（背景執行緒可能剛好寫完一部分），
    flush 之後才穩定是 3 筆。**「有時會過、有時不會」的測試比直接壞掉更難查**，
    所以「跑完馬上要查」的場景一律先 flush。正式服務不需要這行（背景執行緒自己會寫完）。

    `search_traces()` 回一張 **DataFrame**，一列一條 trace。
    注意參數名是 **`experiment_ids`（複數、要 id）**——寫成 `experiment_names` 會直接 TypeError。
    """
    )
    return


@app.cell
def _(ANSWERS_V1, EXP_ID, mlflow, mo, pd):
    _n_asked = len(ANSWERS_V1)                              # 上一格問完三題之後才查得到
    _before = len(mlflow.search_traces(experiment_ids=[EXP_ID]))
    mlflow.flush_trace_async_logging()                      # ← 少了這行，下一行查到 0 筆
    traces_df = mlflow.search_traces(experiment_ids=[EXP_ID])

    _view = pd.DataFrame(
        {
            "trace_id": [t[:14] + "…" for t in traces_df["trace_id"]],
            "state": traces_df["state"],
            "ms": traces_df["execution_duration"],
            "request": [str(r) for r in traces_df["request"]],
            "response": [str(r)[:28] for r in traces_df["response"]],
        }
    )
    mo.vstack(
        [
            mo.md(
                f"問了 {_n_asked} 題　·　flush 之前查到 **{_before}** 筆；"
                f"flush 之後 **{len(traces_df)}** 筆。"
            ),
            _view,
            mo.md(f"DataFrame 共 {len(traces_df.columns)} 欄：`{'`、`'.join(traces_df.columns)}`"),
        ]
    )
    return (traces_df,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    表格是「有哪些請求」，看不到中間發生什麼。要看樹，用 `mlflow.get_trace(trace_id)`：

    - `trace.info` — 整條的資訊：`trace_id`、`state`、`execution_duration`（毫秒）、`tags`、`assessments`
    - `trace.data.spans` — 一個 list，每個 span 有 `name`、`span_type`、`inputs`、`outputs`、
      `attributes`、`parent_id`、起訖時間（奈秒）

    下面這個小工具把 span list 畫成樹（`parent_id is None` 的是根節點），
    長條的長度是各 span 的實際耗時比例。
    """
    )
    return


@app.cell
def _(html, json, mo):
    SPAN_COLOR = {
        "CHAIN": "#3b3a36",
        "RETRIEVER": "#4C72B0",
        "LLM": "#DD8452",
        "TOOL": "#55A868",
    }


    def span_rows(trace) -> list[dict]:
        """把 trace.data.spans 整理成畫圖用的 list。"""
        rows = []
        for s in trace.data.spans:
            rows.append(
                {
                    "name": s.name,
                    "type": str(s.span_type),
                    "ms": (s.end_time_ns - s.start_time_ns) / 1e6,
                    "root": s.parent_id is None,
                    "inputs": s.inputs,
                    "outputs": s.outputs,
                    "attrs": {k: v for k, v in s.attributes.items() if not k.startswith("mlflow.")},
                }
            )
        return rows


    def span_tree(trace, show_io: bool = True) -> mo.Html:
        """把一條 trace 畫成縮排的 span 樹，附時間長條與 inputs／outputs 原文。"""
        rows = span_rows(trace)
        widest = max(r["ms"] for r in rows) or 1.0
        own_tags = {k: v for k, v in trace.info.tags.items() if not k.startswith("mlflow.")}
        head = (
            "<div style='font-weight:700;margin-bottom:6px'>"
            f"{html.escape(trace.info.trace_id[:18])}…　state={html.escape(str(trace.info.state))}　"
            f"總計 {trace.info.execution_duration} ms　tags: {html.escape(str(own_tags))}</div>"
        )
        parts = [
            "<div style='font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:12.5px;line-height:1.55'>",
            head,
        ]
        for i, r in enumerate(rows):
            color = SPAN_COLOR.get(r["type"], "#8a8578")
            pad = 0 if r["root"] else 22
            branch = "" if r["root"] else ("└─ " if i == len(rows) - 1 else "├─ ")
            width = max(2.0, r["ms"] / widest * 46.0)
            parts.append(
                f"<div style='padding-left:{pad}px;margin:2px 0;display:flex;align-items:center;gap:8px;overflow:hidden'>"
                f"<span style='min-width:150px'>{branch}<b>{html.escape(r['name'])}</b></span>"
                f"<span style='color:{color};font-weight:700;min-width:88px'>{html.escape(r['type'])}</span>"
                f"<span style='display:inline-block;height:11px;border-radius:3px;background:{color};width:{width:.1f}%;flex:none'></span>"
                f"<span style='color:#8a8578;white-space:nowrap'>{r['ms']:.1f} ms</span>"
                "</div>"
            )
            if r["attrs"]:
                parts.append(
                    f"<div style='padding-left:{pad + 24}px;color:#8a8578'>attributes: "
                    f"{html.escape(json.dumps(r['attrs'], ensure_ascii=False))}</div>"
                )
            if show_io:
                for _label, _val in (("in ", r["inputs"]), ("out", r["outputs"])):
                    parts.append(
                        f"<div style='padding-left:{pad + 24}px;color:#5c5850;white-space:pre-wrap;"
                        f"word-break:break-word'>{_label}: "
                        f"{html.escape(json.dumps(_val, ensure_ascii=False))}</div>"
                    )
        parts.append("</div>")
        return mo.Html("".join(parts))
    return SPAN_COLOR, span_rows, span_tree


@app.cell
def _(mlflow, mo, span_tree, traces_df):
    trace_refund = mlflow.get_trace(
        traces_df[traces_df["request"].astype(str).str.contains("退貨")].iloc[0]["trace_id"]
    )
    trace_guess = mlflow.get_trace(
        traces_df[traces_df["request"].astype(str).str.contains("分期")].iloc[0]["trace_id"]
    )

    mo.vstack(
        [
            mo.md("**「退貨要多久內？」的 span 樹**（檢索命中）"),
            span_tree(trace_refund),
            mo.md("**「可以分期嗎？」的 span 樹**（檢索沒命中，模型自己編）"),
            span_tree(trace_guess),
        ]
    )
    return trace_guess, trace_refund


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    第二棵樹把投訴案件的真相攤開了：

    - `retrieve` 的 outputs 是 **`[]`**——知識庫裡根本沒有這條，檢索沒撈到任何東西
    - `fake_llm` 的 inputs 裡，「資料：」後面是**空的**
    - 但模型還是回了一個聽起來很專業的答案

    **這不是模型壞掉，是 prompt 沒說「查不到就閉嘴」。**
    只看最後那句話，你會以為要換模型；看了 trace，你知道要改的是 prompt——
    第 8️⃣ 節就會改它。

    順帶一提第一棵樹的總計時間會明顯比後兩條長（實測 130–220 ms vs 71–92 ms）：
    那是**第一次呼叫時 tracing 自己的暖機成本**，不是你的程式慢。
    量延遲不要只看第一筆。
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 3️⃣ `span_type`：那個字串到底有什麼用

    `span_type="RETRIEVER"` 不會改變任何執行結果——它是**給人與工具看的分類**。
    但別因此覺得可有可無，它決定了三件事：

    1. **MLflow UI 會照類型渲染**：`RETRIEVER` 的輸出會被畫成一張「找到哪幾份文件」的清單，
       `LLM` 會被畫成對話框並顯示 token 數，`CHAT_MODEL` 會排成訊息串。標錯類型，畫面就變成一坨 JSON。
    2. **內建 scorer 認得它**：像「檢索到的文件跟問題有沒有關係」這類評分器，
       是靠 `RETRIEVER` span 找到「文件」在哪裡的。
    3. **你自己查詢時的分組依據**：「所有 LLM span 的總 token」「TOOL span 的失敗率」。

    `mlflow.entities.SpanType` 提供的常數（3.15.2 實測共 15 個）：

    | 常用 | 意思 |
    |---|---|
    | `CHAIN` | 把好幾步串起來的流程 |
    | `LLM` / `CHAT_MODEL` | 呼叫模型（後者是對話格式） |
    | `RETRIEVER` | 檢索文件 |
    | `TOOL` | 呼叫外部工具／函式（查訂單、發信、算數學） |
    | `AGENT` | 會自己決定下一步的代理 |
    | `EMBEDDING` / `RERANKER` / `PARSER` | 向量化／重排／解析 |
    | `GUARDRAIL` / `EVALUATOR` / `MEMORY` / `TASK` / `WORKFLOW` / `UNKNOWN` | 其餘 |

    傳字串（`"RETRIEVER"`）或傳常數（`SpanType.RETRIEVER`）都可以，值一樣。
    **這個欄位沒有校驗**——打錯字不會報錯，只會讓 UI 不知道怎麼畫，這是最沉默的那種錯。
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 4️⃣ 屬性、標籤、搜尋：讓幾十萬條 trace 找得到

    一天幾十萬條 trace，UI 上一條一條翻是不可能的。你需要能**篩**。
    MLflow 給你兩個掛東西的地方，用途完全不同：

    | | `span.set_attributes({...})` | `mlflow.update_current_trace(tags={...})` |
    |---|---|---|
    | 掛在哪 | **單一 span** | **整條 trace** |
    | 典型內容 | `n_docs`、`top_k`、`model`、`temperature` | `topic`、`user_tier`、`prompt_ver`、`session_id` |
    | 能拿來搜尋嗎 | 不能（要撈回來自己看） | **能**（`filter_string="tags.xxx = '…'"`） |
    | 什麼時候用 | 事後想「那一步當時是什麼設定」 | 事前想「之後我要用什麼條件撈這群請求」 |

    一句話判準：**你想用它來「找出一群 trace」，就放 tag；你想用它來「解釋某一步」，就放 attribute。**

    兩個實測到的坑：

    - `mlflow.get_current_active_span()` 在 trace 外面呼叫**回 `None`**（不是報錯），
      接著 `.set_attributes(...)` 就會變成 `AttributeError: 'NoneType' object has no attribute …`。
    - `mlflow.update_current_trace()` 在 trace 外面呼叫**什麼事都不會發生、也不會報錯**——
      標籤靜靜地掉了，你要等到搜尋不到才發現。
    """
    )
    return


@app.cell
def _(EXP_ID, mlflow, mo, pd, traces_df):
    def count(filter_string=None):
        return len(mlflow.search_traces(experiment_ids=[EXP_ID], filter_string=filter_string))

    _asked = len(traces_df)                                 # 接在上一格之後跑


    search_demo = pd.DataFrame(
        [
            {"filter_string": "（不篩）", "命中": count()},
            {"filter_string": "tags.topic = '退貨'", "命中": count("tags.topic = '退貨'")},
            {"filter_string": "tags.topic = 'none'", "命中": count("tags.topic = 'none'")},
            {"filter_string": "attributes.execution_time_ms > 100", "命中": count("attributes.execution_time_ms > 100")},
            {"filter_string": "attributes.status = 'OK'", "命中": count("attributes.status = 'OK'")},
            {"filter_string": "tags.Topic = '退貨'（大小寫打錯）", "命中": count("tags.Topic = '退貨'")},
            {"filter_string": "tags.topics = '退貨'（多了一個 s）", "命中": count("tags.topics = '退貨'")},
        ]
    )
    mo.vstack(
        [
            search_demo,
            mo.md(
                "最後兩列是**沉默的失敗**：tag 的名字打錯（大小寫、單複數）MLflow 不會報錯，"
                "就是回 0 筆。查不到東西的時候，先懷疑自己的 filter 而不是資料。"
            ),
        ]
    )
    return count, search_demo


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    語法規則跟第 1 課的 `search_runs` 一樣（同一套解析器）。**分界線在這裡：
    「點」前面那一段（entity type）MLflow 會驗，「點」後面那一段（key）不會。**
    所以打錯前綴會被罵，打錯 tag 名字只會靜靜回 0 筆：

    ```
    "tags.topic = 退貨"                    ← 值沒有引號
      → Parameter value is either not quoted or unidentified quote types
        used for string value 退貨.

    "tags.topic == '退貨'"                 ← 用了 ==
      → Invalid comparator '==' not one of
        '{'IS NOT NULL', 'IS NULL', '!=', 'ILIKE', '=', 'LIKE', 'RLIKE'}'

    "attributes.execution_duration > 100"  ← DataFrame 的欄名不是 filter 的欄名
      → Invalid attribute key 'execution_duration' specified. Valid keys are
        '{'execution_time_ms', 'status', 'name', 'timestamp_ms', 'run_id', …}'

    "foo.topic = '退貨'"                   ← entity type 不存在
      → Invalid entity type 'foo'. Valid values are {'attribute',
        'request_metadata', 'attributes', 'metadata', 'span', 'tags',
        'expectation', 'tag', 'trace', 'issue', 'feedback'}

    "tags.Topic = '退貨'"                  ← 只是 tag 名字大小寫錯
      → 不報錯，回 0 筆
    ```

    兩個閱讀提示。第一，上面那份合法清單裡 `tag` 與 `tags` 都在——**兩種寫法都能用**，
    別以為少一個 s 就是 bug；真正要小心的是最後那一種。第二，**大括號裡的順序每次執行都不一樣**
    （那是 Python 的 set），上面是某一次的實測輸出、也做了截斷——**別把順序或長度當成規格**。

    延遲欄位也踩過同一個坑：DataFrame 叫 `execution_duration`，
    filter 要寫 `attributes.execution_time_ms`——同一個東西、兩個名字。

    ### 不是每個 span 都來自裝飾器

    有些程式碼不是函式（一段 for 迴圈、一個批次流程），用 `with mlflow.start_span(...)` 手動開一個：
    """
    )
    return


@app.cell
def _(EXP_ID, QUESTIONS, mlflow, mo, search_demo, span_tree):
    _after = len(search_demo)                               # 接在上一格之後跑
    with mlflow.start_span(name="nightly-batch", span_type="CHAIN") as _s:
        _s.set_inputs({"n_questions": len(QUESTIONS)})
        _s.set_attributes({"scheduler": "cron", "hour": 3})
        _s.set_outputs({"ok": len(QUESTIONS), "failed": 0})

    mlflow.flush_trace_async_logging()
    manual_trace = mlflow.get_trace(
        mlflow.search_traces(experiment_ids=[EXP_ID], max_results=1).iloc[0]["trace_id"]
    )
    mo.vstack(
        [
            span_tree(manual_trace),
            mo.md(
                "`with` 區塊結束時 span 自動關閉、trace 自動送出。"
                "手動 span 要自己呼叫 `set_inputs` / `set_outputs`——裝飾器是幫你自動抓函式的參數與回傳值而已。"
                "（總計顯示 0 ms 是對的：這個 span 裡面沒有真的做事，0.3 毫秒進到 `execution_duration` 就被進位成 0。）"
            ),
        ]
    )
    return (manual_trace,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 5️⃣ 誰最慢：把總時間拆給每個 span

    「這個請求要 3 秒」是抱怨，「這 3 秒有 2.7 秒在等模型」才是可以動手的情報。
    trace 天生就有這份資料：每個 span 都記了起訖時間。

    下面把三條 trace 的 span 耗時攤開來看。
    **提醒：本課的耗時來自 `time.sleep` 的模擬值**（檢索 20 ms、生成 50 ms），
    不是真實系統的量測——但比例的方向是對的：真實 RAG 應用裡，
    生成幾乎永遠是最大的一塊（幾百毫秒到幾秒），檢索是幾十毫秒。
    """
    )
    return


@app.cell
def _(manual_trace, mlflow, mo, pd, span_rows, traces_df):
    _rows = []
    _ = manual_trace.info.state                             # 接在上一格之後跑
    for _tid in traces_df["trace_id"]:                      # 就是第 2️⃣ 節那三條 trace
        _t = mlflow.get_trace(_tid)
        _by = {r["name"]: r["ms"] for r in span_rows(_t)}
        _rows.append(
            {
                "問題": str(_t.data.spans[0].inputs.get("question", "")),
                "總計 ms": _t.info.execution_duration,
                "retrieve ms": round(_by.get("retrieve", 0), 1),
                "fake_llm ms": round(_by.get("fake_llm", 0), 1),
                "LLM 佔比": f"{_by.get('fake_llm', 0) / _by.get('answer', 1) * 100:.0f}%",
            }
        )
    latency_df = pd.DataFrame(_rows)

    mo.vstack(
        [
            latency_df,
            mo.md(
                "第一筆的總計時間明顯偏高、佔比也被稀釋——那是暖機。"
                "**看延遲永遠要看分佈（p50／p95），不要看單筆、更不要看第一筆。**"
            ),
        ]
    )
    return (latency_df,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 6️⃣ 人工評估：把「這答案對不對」寫回 trace 上

    訓練模型時有標準答案，AUC 一個數字說了算。
    LLM 應用沒有這種東西——「這個回答好不好」要人看了才知道。

    MLflow 的做法是把人的判斷**掛回那條 trace**，叫 **assessment**，分兩種：

    | | `log_feedback` | `log_expectation` |
    |---|---|---|
    | 記什麼 | 這次的回答**好不好** | 這一題**正確答案應該是什麼** |
    | 誰給的 | 人工標記、線上的讚／倒讚、LLM judge | 人工（領域專家） |
    | 例子 | `correct=False`，理由「手冊沒有分期規定」 | `expected_answer="手冊裡沒有寫。"` |

    `AssessmentSource` 要寫清楚**是誰標的**（`HUMAN` / `LLM_JUDGE` / `CODE`）——
    之後要分「人標的」跟「機器標的」時全靠它。

    這件事的意義比它看起來大：**一批被標記過的 trace，就是你的評估資料集。**
    不用另外維護一份 CSV，線上真實流量本身就是題庫；出問題的那幾條標一標，
    就變成下次改 prompt 的回歸測試。
    """
    )
    return


@app.cell
def _(AssessmentSource, AssessmentSourceType, latency_df, mlflow, mo, trace_guess):
    _ = len(latency_df)                                     # 接在上一格之後跑
    TEACHER = AssessmentSource(source_type=AssessmentSourceType.HUMAN, source_id="teacher")

    mlflow.log_feedback(
        trace_id=trace_guess.info.trace_id,
        name="correct",
        value=False,
        rationale="知識庫沒有分期付款這條，模型自己編了一個答案",
        source=TEACHER,
    )
    mlflow.log_expectation(
        trace_id=trace_guess.info.trace_id,
        name="expected_answer",
        value="手冊裡沒有寫。",
        source=TEACHER,
    )

    _reread = mlflow.get_trace(trace_guess.info.trace_id)      # 要重新讀才看得到
    _lines = []
    for _a in _reread.info.assessments:
        _v = getattr(getattr(_a, "feedback", None), "value", None)
        if _v is None:
            _v = getattr(getattr(_a, "expectation", None), "value", None)
        _lines.append(
            f"- `{type(_a).__name__}` **{_a.name}** = `{_v}`　"
            f"（{_a.source.source_type} / {_a.source.source_id}）"
            + (f"　理由：{_a.rationale}" if _a.rationale else "")
        )
    mo.md("\n".join(_lines))
    return (TEACHER,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    注意最後一行的 `mlflow.get_trace(...)` ——**assessment 是掛上去之後才存在的，
    手上那個舊的 trace 物件不會自己更新**，要重新讀一次。

    還有一個實測會踩的：`log_feedback` 給一個不存在的 trace_id，會噴
    `MlflowException: Trace with ID 'tr-…' not found. It may have been deleted.`
    ——這通常代表你忘了 flush（trace 還在緩衝區裡，資料庫裡當然找不到）。
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 7️⃣ 自動評估：寫一個 scorer，讓機器幫你標

    人工標記很準，但一天標不了一百條。所以真實的做法是**兩層**：

    - **code-based scorer**：純 Python 規則。快、免費、100% 可重現。
      「回答有沒有引用來源」「有沒有超過長度上限」「該拒答的時候有沒有拒答」——這些用規則就抓得到。
    - **LLM-as-judge scorer**：拿另一個模型當評審，判斷「語氣夠不夠禮貌」「有沒有答非所問」這類
      規則寫不出來的事。準，但要錢、要 API key、而且**評審本身也會出錯**。

    **這一課只跑第一種**（不需要任何金鑰）。`@scorer` 裝飾器把一個普通函式變成評分器，
    `mlflow.genai.evaluate(data=..., scorers=[...])` 對一批資料跑完，回傳每個 scorer 的平均。

    這裡有一個**必須記住的規則**：scorer 的參數名只能從
    `inputs` / `outputs` / `expectations` / `trace` 這幾個裡挑。
    參數名寫錯**不會報錯**——`evaluate` 照跑，`metrics` 回一個 `{}` 空字典（實測），
    你會以為「怎麼沒有分數」而不是「我打錯字了」。
    """
    )
    return


@app.cell
def _(DOCS, PROMPT_V1, QUESTIONS, TEACHER, contextlib, io, mo, pd):
    from mlflow.genai import evaluate, scorer

    _ = TEACHER.source_id                                   # 接在上一格之後跑

    PROMPT_V2 = (
        "你是客服，語氣親切：每則回答都以「您好，」開頭。\n"
        "只根據資料回答；資料是空的就回「手冊裡沒有寫。」，不要自己猜。\n"
        "資料：{{context}}\n問題：{{question}}"
    )


    @scorer
    def has_number(outputs) -> bool:
        """天真版：回答裡要有數字（期限幾天、運費幾元）。"""
        return any(ch.isdigit() for ch in str(outputs))


    @scorer
    def refuses_when_empty(inputs, outputs) -> bool:
        """檢索沒撈到文件時，必須老實說「手冊裡沒有寫」，不准猜。"""
        if inputs.get("context"):
            return True
        return "手冊裡沒有寫" in str(outputs)


    @scorer
    def short_enough(outputs) -> bool:
        """客服回答不要超過 40 個字。"""
        return len(str(outputs)) <= 40


    def build_eval_data(template: str, questions: list[str]) -> list[dict]:
        """離線重放：同一批問題、換一個 prompt 樣板，收集 (inputs, outputs)。"""
        data = []
        for q in questions:
            hits = [v for k, v in DOCS.items() if k in q]
            text = hits[0] if hits else ""
            prompt = template.replace("{{context}}", text).replace("{{question}}", q)
            if text:
                a = text
            elif "不要自己猜" in prompt:
                a = "手冊裡沒有寫。"
            else:
                a = "可以分期，通常提供 3 期與 6 期免利息。"
            if "以「您好，」開頭" in prompt:
                a = "您好，" + a
            data.append({"inputs": {"question": q, "context": text}, "outputs": a})
        return data


    SCORERS = [has_number, refuses_when_empty, short_enough]
    _scores = {}
    for _name, _tpl in [("prompt v1", PROMPT_V1), ("prompt v2", PROMPT_V2)]:
        with contextlib.redirect_stdout(io.StringIO()):      # evaluate 會印一段廣告，收起來
            _res = evaluate(data=build_eval_data(_tpl, QUESTIONS), scorers=SCORERS)
        _scores[_name] = {k.replace("/mean", ""): round(float(v), 3) for k, v in _res.metrics.items()}

    scores_df = pd.DataFrame(_scores).T[["has_number", "refuses_when_empty", "short_enough"]]
    mo.vstack([scores_df, mo.md("（每格是三題的平均；1.000 ＝ 三題都通過）")])
    return (
        PROMPT_V2,
        SCORERS,
        build_eval_data,
        evaluate,
        has_number,
        refuses_when_empty,
        scorer,
        scores_df,
        short_enough,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    這張表值得盯久一點，因為它示範了 **scorer 設計最常見的錯誤**：

    - `refuses_when_empty`：v1 0.667 → v2 **1.000**。v2 加的拒答規則生效了，幻覺被修掉。✅
    - `has_number`：v1 1.000 → v2 **0.667**。**變差了？**

    沒有變差。v2 那一題答的是「手冊裡沒有寫。」——**正確的拒答裡本來就不會有數字**，
    是這個 scorer 誤殺了它。（更諷刺的是：v1 那句幻覺「3 期與 6 期」裡有數字，
    所以 `has_number` 給它滿分。）

    **教訓：一個指標會騙人，一組指標才看得出真相。**
    而且 scorer 要把「合法的例外」寫進規則裡——像 `refuses_when_empty` 那樣先判斷
    「這一題本來就該有答案嗎」，而不是無條件套同一條規則。

    想加 LLM judge 的話（本課不跑，需要模型與金鑰）：

    ```python
    from mlflow.genai.scorers import Guidelines
    polite = Guidelines(name="polite", guidelines=["回答必須有禮貌，且不得承諾手冊沒寫的條件"])
    mlflow.genai.evaluate(data=data, scorers=[*SCORERS, polite])
    ```

    做法是一樣的，只是那個 scorer 內部會去呼叫一個模型。
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 8️⃣ Prompt Registry：prompt 也要版本控制

    第 2 課你把**模型**放進 Registry：一個名字、很多版本、一個 `@champion` alias 指向線上那版。
    LLM 應用有一個東西跟模型一樣重要、卻更常被改動——**prompt**。

    想想它的日常：產品經理說「語氣太硬」，有人在 Slack 貼了一段新的 prompt，
    工程師複製貼上進程式碼，deploy。三天後客訴變多了。**上週那版 prompt 長什麼樣？**
    翻 git log 嗎——如果 prompt 是寫在程式碼裡，也許可以；
    如果它在資料庫、在設定檔、在某人的筆記本裡，就沒救了。

    `mlflow.genai.register_prompt()` 給 prompt 一套跟模型一樣的規矩：

    - **名字＋版本**：同一個名字每註冊一次就 +1 版，`commit_message` 說明改了什麼
    - **alias**：`production` 指向現在線上那版，換版＝把 alias 移過去
    - **變數**：樣板用 `{{變數名}}` 佔位，`.format(**kw)` 填值，`.variables` 列出有哪些

    先註冊我們的兩版：
    """
    )
    return


@app.cell
def _(PROMPT_V1, PROMPT_V2, mlflow, mo):
    prompt_v1 = mlflow.genai.register_prompt(
        name="support-answer",
        template=PROMPT_V1,
        commit_message="v1 初版：只根據資料回答",
        tags={"lang": "zh-Hant", "owner": "cs-team"},
    )
    prompt_v2 = mlflow.genai.register_prompt(
        name="support-answer",
        template=PROMPT_V2,
        commit_message="v2 加上拒答規則與問候語（修掉分期付款的幻覺）",
    )
    mlflow.genai.set_prompt_alias("support-answer", alias="production", version=1)

    _prod = mlflow.genai.load_prompt("prompts:/support-answer@production")
    _vars = "、".join(f"`{v}`" for v in sorted(_prod.variables))
    _filled = _prod.format(context="退貨期限為 7 天", question="可以退嗎？")
    mo.md(
        f"""
    - 註冊了 **{prompt_v1.name}** 的 v{prompt_v1.version} 與 v{prompt_v2.version}
    - `@production` 目前指向 **v{_prod.version}**
    - 這個樣板需要的變數：{_vars}
    - `format()` 填完值之後的前 30 字：`{_filled[:30]!r}`
    """
    )
    return prompt_v1, prompt_v2


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ### 晉升與回滾

    `load_prompt` 吃兩種 URI，差別就是「要不要跟著換版」：

    - `prompts:/support-answer@production` — **跟著 alias 走**，晉升之後下一次載入自動變新版
    - `prompts:/support-answer/1` — **釘死第 1 版**，之後怎麼晉升都不會變（重現舊結果時要這個）

    晉升就是一行 `set_prompt_alias(..., version=2)`；回滾就是把它指回去。
    """
    )
    return


@app.cell
def _(mlflow, mo, pd, prompt_v1, prompt_v2):
    _registered = (prompt_v1.version, prompt_v2.version)    # 接在註冊完之後跑
    _log = []
    for _action, _v in [("目前", None), ("晉升到 v2", 2), ("回滾到 v1", 1), ("再晉升到 v2", 2)]:
        if _v is not None:
            mlflow.genai.set_prompt_alias("support-answer", alias="production", version=_v)
        _log.append(
            {
                "動作": _action,
                "@production 載到": f"v{mlflow.genai.load_prompt('prompts:/support-answer@production').version}",
                "prompts:/support-answer/1 載到": f"v{mlflow.genai.load_prompt('prompts:/support-answer/1').version}",
            }
        )
    promote_df = pd.DataFrame(_log)

    _all = mlflow.genai.search_prompts(filter_string="name = 'support-answer'")
    mo.vstack(
        [
            promote_df,
            mo.md(
                f"`search_prompts` 找到 **{len(_all)}** 個 prompt："
                f"`{'`、`'.join(p.name for p in _all)}`（tags：`{_all[0].tags.get('lang')}` / `{_all[0].tags.get('owner')}`）"
            ),
        ]
    )
    return (promote_df,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    四個實測到的行為，寫程式前先知道比較不會受傷：

    - **同名同內容再註冊一次，會產生一個新版本**（不會偵測重複）——實測拿 v1 的 template
      再註冊一次，得到的是 v3。所以別把 `register_prompt` 放在會重複執行的迴圈裡。
    - **壞 alias 跟壞版本的錯誤訊息不一樣**——看到前者是 alias 沒建，看到後者是版本號打錯。
    - **URI 一定要有 `prompts:/` 前綴**，否則它會把整串當成 prompt 的名字。
    - **`format()` 少給變數會擋下來**；多給沒用到的變數則不會報錯，直接忽略。

    四段實測原文（`_spikes/spike_tracing_errors.py` 撞出來的）：

    ```
    load_prompt("prompts:/support-answer@nope")
      → MlflowException: Prompt alias nope not found.

    load_prompt("prompts:/support-answer/99")
      → MlflowException: Prompt (name=support-answer, version=99) not found

    load_prompt("support-answer@production")          # 少了 prompts:/ 前綴
      → MlflowException: Prompt with name=support-answer@production not found

    prod.format(question="可以退嗎？")                 # 少給 context
      → MlflowException: Missing variables: {'context'}.
        To partially format the prompt, set `allow_partial=True`.
    ```
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 9️⃣ 串起來：哪個回答是哪一版 prompt 生的？

    現在把三件事接在一起：**從 Registry 載 prompt → 跑一次請求 → 在 trace 上留下版本**。

    關鍵在這行：只要 `load_prompt()` 是在 `@mlflow.trace` 的函式**裡面**呼叫的，
    MLflow 會自動幫這條 trace 加一個 `mlflow.linkedPrompts` 標籤，內容是
    `[{"name": "support-answer", "version": "2"}]`。

    **你不用自己記錄「這次用了哪版 prompt」——它自己就在 trace 上。**
    再加一個自訂 tag `prompt_ver`，就能用 `search_traces` 把兩版的請求分開比。
    """
    )
    return


@app.cell
def _(DOCS, mlflow, retrieve, time):
    @mlflow.trace(span_type="LLM")
    def llm_v(prompt: str) -> dict:
        time.sleep(0.05)
        _ctx = prompt.split("資料：")[-1].split("\n問題：")[0].strip()
        if _ctx:
            _a = _ctx
        elif "不要自己猜" in prompt:
            _a = "手冊裡沒有寫。"
        else:
            _a = "可以分期，通常提供 3 期與 6 期免利息。"
        if "以「您好，」開頭" in prompt:
            _a = "您好，" + _a
        return {"content": _a, "usage": {"prompt_tokens": len(prompt), "completion_tokens": len(_a)}}


    @mlflow.trace(name="answer_v", span_type="CHAIN")
    def answer_versioned(question: str, uri: str = "prompts:/support-answer@production") -> str:
        pr = mlflow.genai.load_prompt(uri)                 # ← 在 trace 內載入 → 自動掛 linkedPrompts
        ctx = retrieve(question)
        mlflow.get_current_active_span().set_attributes(
            {"n_docs": len(ctx), "prompt_version": pr.version}
        )
        out = llm_v(pr.format(context=ctx[0]["text"] if ctx else "", question=question))
        mlflow.update_current_trace(
            tags={"prompt_ver": f"v{pr.version}", "topic": ctx[0]["doc"] if ctx else "none"}
        )
        return out["content"]
    return answer_versioned, llm_v


@app.cell
def _(EXP_ID, QUESTIONS, answer_versioned, mlflow, mo, pd, promote_df):
    _ready = len(promote_df)                                # 接在 alias 定案（v2 上線）之後
    for _q in QUESTIONS:
        answer_versioned(_q, "prompts:/support-answer/1")   # 舊版：釘死 v1
    for _q in QUESTIONS:
        answer_versioned(_q, "prompts:/support-answer@production")   # 現在線上這版（v2）
    mlflow.flush_trace_async_logging()

    _rows = []
    for _v in ["v1", "v2"]:
        _d = mlflow.search_traces(experiment_ids=[EXP_ID], filter_string=f"tags.prompt_ver = '{_v}'")
        for _i in range(len(_d)):
            _rows.append(
                {
                    "prompt": _v,
                    "問題": str(_d.iloc[_i]["request"].get("question", "")),
                    "回答": str(_d.iloc[_i]["response"]),
                    "ms": _d.iloc[_i]["execution_duration"],
                }
            )
    compare_df = pd.DataFrame(_rows).sort_values(["問題", "prompt"]).reset_index(drop=True)
    mo.vstack([compare_df, mo.md("同樣三題、同一個模型，只換了 prompt 的版本。")])
    return (compare_df,)


@app.cell
def _(EXP_ID, compare_df, mlflow, mo, span_tree):
    _n = len(compare_df)                                    # 接在上一格之後跑
    _v2 = mlflow.search_traces(
        experiment_ids=[EXP_ID], filter_string="tags.prompt_ver = 'v2' AND tags.topic = 'none'"
    )
    _t = mlflow.get_trace(_v2.iloc[0]["trace_id"])
    mo.vstack(
        [
            mo.md(
                "**v2 版本、檢索沒命中的那一條**——同一題，v1 會編答案，v2 老實說不知道。"
                f"注意標籤列裡的 `mlflow.linkedPrompts`：`{_t.info.tags.get('mlflow.linkedPrompts')}`"
            ),
            span_tree(_t),
        ]
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    這就是 LLMOps 的閉環：

    **線上請求留下 trace → 有問題的 trace 被人標記 → 標記過的 trace 變成評估資料集 →
    改 prompt、註冊新版 → 用同一批資料重跑 scorer → 分數變好才把 alias 移過去 →
    新的 trace 帶著新版本號回到第一步。**

    跟第 5 課的訓練管線（訓練 → evaluate → 品質閘 → 移 champion）是同一個形狀，
    只是把「模型」換成「prompt」、把「AUC」換成「一組 scorer」。

    ### 換成真的模型要改幾行？一行。

    ```python
    import mlflow, openai
    mlflow.openai.autolog()          # ← 就這一行
    client = openai.OpenAI()
    resp = client.chat.completions.create(model="gpt-4o-mini", messages=[...])
    ```

    加上 `autolog()` 之後，每一次 API 呼叫都會自動變成一個 `CHAT_MODEL` span，
    而且比手寫的還完整：**模型名、temperature、每則訊息、token 用量**都自動記進去
    （支援的供應商還會估算費用）。
    你自己寫的 `@mlflow.trace(span_type="CHAIN")` 照舊——兩者會自動接成同一棵樹。

    LangChain、LlamaIndex、Anthropic、Gemini、DSPy 等等都有各自的 `autolog()`，
    用法一模一樣。**這一課學的 span 樹、tag、assessment、scorer、Prompt Registry，
    在真模型上一個字都不用改。**
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 🔟 你的實驗場：問一題，看它的 trace

    輸入任何問題（知識庫只有**退貨／運費／付款**三條，故意問別的看它怎麼反應），
    選一版 prompt，按下按鈕。下面會出現這一次請求的完整 span 樹。

    值得試的三組對照：

    - 問「**運費怎麼算**」→ 兩版都答得出來，差別只在開頭的問候語
    - 問「**可以分期嗎**」→ v1 開始編、v2 老實拒答（看 `retrieve` 的 outputs 是不是 `[]`）
    - 問「**退貨運費誰付**」→ 兩個關鍵字都命中，看 `n_docs` 變成 2，但只有第一份被放進 prompt
    """
    )
    return


@app.cell
def _(mo):
    q_box = mo.ui.text(
        value="可以分期嗎？",
        label="問題",
        full_width=True,
        placeholder="例如：退貨要多久內？",
    )
    prompt_pick = mo.ui.dropdown(
        options={
            "v1（舊版：沒有拒答規則）": "prompts:/support-answer/1",
            "production（目前線上＝v2）": "prompts:/support-answer@production",
        },
        value="production（目前線上＝v2）",
        label="用哪一版 prompt",
    )
    ask_btn = mo.ui.run_button(label="送出並產生 trace")
    mo.vstack([q_box, mo.hstack([prompt_pick, ask_btn], justify="start", gap=1, wrap=True)])
    return ask_btn, prompt_pick, q_box


@app.cell
def _(
    EXP_ID,
    answer_versioned,
    ask_btn,
    mlflow,
    mo,
    prompt_pick,
    promote_df,
    q_box,
    span_tree,
):
    mo.stop(
        not (ask_btn.value and len(promote_df)),
        mo.callout(mo.md("輸入問題、選一版 prompt，再按 **送出並產生 trace**。"), kind="info"),
    )

    _reply = answer_versioned(q_box.value or "（空的問題）", prompt_pick.value)
    mlflow.flush_trace_async_logging()
    _latest = mlflow.get_trace(
        mlflow.search_traces(experiment_ids=[EXP_ID], max_results=1).iloc[0]["trace_id"]
    )
    mo.vstack([mo.md(f"### 回答：{_reply}"), span_tree(_latest)])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 🏆 延伸挑戰

    1. **LEVEL 1**：客服還要能查訂單。加一個 `@mlflow.trace(span_type="TOOL")` 的
       `order_status(order_id)`（假資料就好），讓 `answer` 在問題含訂單編號時呼叫它，
       然後在 span 樹裡看到那個綠色的 TOOL 節點。
    2. **LEVEL 2**：寫一個 scorer `grounded`，檢查「回答必須引用檢索到的文件」——
       正確拒答要放行，但憑空生出來的答案要被抓到。用它去評 v1 與 v2。
    3. **LEVEL 3**：把這一課接到真模型上。裝 `openai`、加一行 `mlflow.openai.autolog()`，
       把 `fake_llm` 換成真的 API 呼叫，其他一行都不改。

    先自己試，卡住再展開下面的提示與參考解答。
    帶得走：下載本檔後 `uvx marimo edit --sandbox mlflow-tracing_ext.py`
    在自己電腦繼續玩（依賴會自動安裝）。
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.accordion(
        {
            "💡 LEVEL 1 參考解答：加一個 TOOL span": mo.md(
                r"""
    ```python
    ORDERS = {"A1001": "已出貨，預計明天送達", "A1002": "備貨中"}

    @mlflow.trace(span_type="TOOL")
    def order_status(order_id: str) -> str:
        time.sleep(0.01)
        return ORDERS.get(order_id, "查無此訂單")

    @mlflow.trace(name="answer_tool", span_type="CHAIN")
    def answer_with_tool(question: str) -> str:
        ctx = retrieve(question)
        extra = ""
        for tok in question.replace("，", " ").split():
            if tok.startswith("A1"):
                extra = order_status(tok)          # ← 這一步會自己變成一個 TOOL span
        out = llm_v(f"資料：{ctx[0]['text'] if ctx else ''}{extra}\n問題：{question}")
        return out["content"]

    answer_with_tool("訂單 A1001 退貨要多久？")
    mlflow.flush_trace_async_logging()
    ```

    你應該看到四個 span（實測耗時；`order_status` 是新出現的那一個）：

    ```
    answer_tool     CHAIN      約 85 ms（若這是整個 session 的第一條 trace，會是 200 ms 上下——暖機）
    ├─ retrieve     RETRIEVER  約 20 ms
    ├─ order_status TOOL       約 10 ms
    └─ llm_v        LLM        約 50 ms
    ```

    三個子 span 的 `parent_id` 都不是 `None`，所以它們在同一層——
    **呼叫順序就是 span 出現的順序**，不需要你手動排。
    """
            ),
            "💡 LEVEL 2 參考解答：grounded scorer": mo.md(
                r"""
    ```python
    @scorer
    def grounded(inputs, outputs) -> bool:
        # 回答必須引用檢索到的文件；正確的拒答放行
        ctx, ans = str(inputs.get("context", "")), str(outputs)
        if "手冊裡沒有寫" in ans:      # 合法的例外：查不到就該拒答
            return True
        return bool(ctx) and ctx[:8] in ans

    for name, tpl in [("v1", PROMPT_V1), ("v2", PROMPT_V2)]:
        res = evaluate(data=build_eval_data(tpl, QUESTIONS), scorers=[grounded])
        print(name, res.metrics)
    ```

    實測：**v2 得 1.000**（兩題引用了文件、一題正確拒答）。
    把其中一題的答案手動換成「大約一週左右都可以退。」再評一次，分數掉到 **0.667**
    ——那句話沒有引用任何文件，正是要抓的幻覺。

    注意第一行的 `if`：沒有這個例外，正確的拒答會被誤判成「沒有引用」——
    跟第 7️⃣ 節 `has_number` 誤殺拒答是同一個坑。
    """
            ),
            "💡 LEVEL 3 提示：接真模型": mo.md(
                r"""
    步驟只有四步：

    1. PEP 723 依賴加 `"openai"`，環境變數放 `OPENAI_API_KEY`
       （notebook 裡用 `mo.ui.text(kind="password")` 也可以）。
    2. 加一行 `mlflow.openai.autolog()`（放在建立 client 之前）。
    3. 把 `llm_v(prompt)` 換成真的呼叫，其他函式**一行都不改**：

       `client.chat.completions.create(model=…, messages=[{"role": "user", "content": prompt}])`

    4. 一樣 `flush_trace_async_logging()` 之後 `get_trace()` 看樹。

    **怎麼驗證自己做對了**：新的 span 樹裡會多出一個 `CHAT_MODEL` 型別的 span
    （不是你自己標的，是 autolog 加的），而且它的 attributes 裡有
    模型名、每則訊息、以及 token 用量——這些都是你沒寫任何程式就自動出現的。
    你原本的 `answer_v`（CHAIN）會是它的父節點，兩者接在同一棵樹上。

    **會踩到的兩件事**：真模型的回答每次不同（所以 `has_number` 這種嚴格的 scorer
    分數會浮動，寫報告要寫範圍不寫點估計）；以及 LLM span 的耗時會從 50 ms 變成
    幾百毫秒到幾秒——第 5️⃣ 節那張延遲表的比例會整個變樣，那才是真實系統的樣子。
    """
            ),
        }
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 📌 收尾：這一課的七個要點

    1. `@mlflow.trace` 一行就開始記；**呼叫關係自動變成 span 樹**，不用手接父子。
    2. 查之前先 `flush_trace_async_logging()`——**忘了會查到不完整的筆數（時多時少），而且不報錯**。
    3. `set_attributes` 掛在 span 上（解釋這一步），`update_current_trace(tags=)` 掛在整條 trace 上（之後拿來搜尋）。
    4. `span_type` 不影響執行，但決定 UI 怎麼畫、內建 scorer 找不找得到東西。
    5. `log_feedback` / `log_expectation` 把人的判斷寫回 trace——**被標記過的 trace 就是評估資料集**。
    6. code-based `@scorer` 免費又可重現；但**一個指標會騙人**，而且要把合法的例外寫進規則。
    7. Prompt Registry 讓 prompt 有版本與 alias；在 trace 裡 `load_prompt` 會自動留下 `mlflow.linkedPrompts`
       ——**哪個回答是哪一版 prompt 生的，一查就知道**。

    紀錄簿在暫存資料夾，關掉 notebook 就沒了。想在自己機器上留著看 UI：
    `mlflow ui --backend-store-uri sqlite:///<你的路徑>/mlflow.db`，Traces 分頁就是這一課的東西。

    下一課換一個題目：同一份特徵，訓練時算一次、上線時再算一次，兩邊算出來不一樣——
    **Feast 特徵倉**就是來解這個的。
    """
    )
    return


if __name__ == "__main__":
    app.run()
