# 錯誤原文 spike（第 10 課 mlflow-tracing 測驗題用）：撞出 MLflow Tracing／Prompt Registry 的真實錯誤訊息。
# 不打真 LLM、不需要網路。跑法：uv run --script content/mlops/_spikes/spike_tracing_errors.py
# /// script
# requires-python = ">=3.11"
# dependencies = ["mlflow>=3.0", "pandas"]
# ///
import logging
import tempfile
import time
import warnings
from pathlib import Path

import mlflow

warnings.filterwarnings("ignore")
logging.getLogger("mlflow").setLevel(logging.ERROR)

W = Path(tempfile.mkdtemp())
mlflow.set_tracking_uri(f"sqlite:///{W}/m.db")
mlflow.create_experiment("err", artifact_location=str(W / "art"))
mlflow.set_experiment("err")
EXP = mlflow.get_experiment_by_name("err").experiment_id


def show(label, fn):
    try:
        out = fn()
        print(f"[OK ] {label}: {out}")
    except Exception as e:  # noqa: BLE001
        print(f"[ERR] {label}: {type(e).__name__}: {str(e)[:400]}")
    print("-" * 100)


DOCS = {"退貨": "退貨期限為 7 天，需保留原包裝。"}


@mlflow.trace(span_type="LLM")
def fake_llm(prompt: str) -> str:
    time.sleep(0.01)
    return "退貨期限為 7 天，需保留原包裝。"


@mlflow.trace(name="answer", span_type="CHAIN")
def answer(q: str) -> str:
    return fake_llm(f"問題：{q}")


# ── 1. search_traces 的參數名寫錯（沒有 experiment_names）
show("1 search_traces(experiment_names=)", lambda: mlflow.search_traces(experiment_names=["err"]))

# ── 2. 忘了 flush 就查（非同步寫入）
answer("退貨要多久內？")
imm = mlflow.search_traces(experiment_ids=[EXP])
print(f"[OK ] 2a 沒 flush 就 search_traces → {len(imm)} 筆")
mlflow.flush_trace_async_logging()
after = mlflow.search_traces(experiment_ids=[EXP])
print(f"[OK ] 2b flush 之後 → {len(after)} 筆")
print("-" * 100)

TID = after.iloc[0]["trace_id"]

# ── 2c. get_trace 給不存在的 trace_id
show("2c get_trace(不存在的 id)", lambda: mlflow.get_trace("tr-0000000000000000000000000000dead"))

# ── 3. log_feedback 給不存在的 trace_id
from mlflow.entities import AssessmentSource, AssessmentSourceType  # noqa: E402

SRC = AssessmentSource(source_type=AssessmentSourceType.HUMAN, source_id="teacher")
show(
    "3 log_feedback(不存在的 trace_id)",
    lambda: mlflow.log_feedback(
        trace_id="tr-0000000000000000000000000000dead", name="correct", value=True, source=SRC
    ),
)

# ── 3b. log_feedback 正常（對照）
show("3b log_feedback(正確的 trace_id)", lambda: mlflow.log_feedback(trace_id=TID, name="correct", value=True, source=SRC).name)

# ── 4. Prompt Registry
p1 = mlflow.genai.register_prompt(
    name="support-answer",
    template="你是客服。只根據資料回答：{{context}}\n問題：{{question}}",
    commit_message="v1 初版",
)
print(f"[OK ] 4a register_prompt v1 → version {p1.version}")
p2 = mlflow.genai.register_prompt(
    name="support-answer",
    template="你是客服，語氣親切。資料沒有就說「手冊裡沒有寫」。\n資料：{{context}}\n問題：{{question}}",
    commit_message="v2 加拒答規則",
)
print(f"[OK ] 4b register_prompt v2 → version {p2.version}")
p3 = mlflow.genai.register_prompt(
    name="support-answer",
    template="你是客服。只根據資料回答：{{context}}\n問題：{{question}}",
    commit_message="v3 跟 v1 一模一樣的 template",
)
print(f"[OK ] 4c 同名同 template 再註冊一次 → version {p3.version}（v1 的內容又變成一個新版本）")
print("-" * 100)

mlflow.genai.set_prompt_alias("support-answer", alias="production", version=2)

# ── 5. load_prompt 壞 alias
show("5a load_prompt(@nope)", lambda: mlflow.genai.load_prompt("prompts:/support-answer@nope").version)
# ── 5b. load_prompt 壞版本
show("5b load_prompt(/99)", lambda: mlflow.genai.load_prompt("prompts:/support-answer/99").version)
# ── 5c. load_prompt 壞名字
show("5c load_prompt(不存在的名字)", lambda: mlflow.genai.load_prompt("prompts:/nope@production").version)
# ── 5d. URI 少了 prompts:/ 前綴
show("5d load_prompt('support-answer@production')", lambda: mlflow.genai.load_prompt("support-answer@production").version)

prod = mlflow.genai.load_prompt("prompts:/support-answer@production")
print(f"[OK ] 5e @production → version {prod.version}, variables={sorted(prod.variables)}")
print("-" * 100)

# ── 6. format 缺變數 / 多變數
show("6a format(只給 question)", lambda: prod.format(question="可以退嗎？")[:80])
show("6b format(多給一個沒用到的變數)", lambda: prod.format(context="退貨 7 天", question="可以退嗎？", extra="x")[:40])
show("6c format(全給)", lambda: prod.format(context="退貨 7 天", question="可以退嗎？")[:40].replace("\n", "\\n"))

# ── 7. update_current_trace 在沒有 active trace 時
show("7 update_current_trace(沒有 active trace)", lambda: mlflow.update_current_trace(tags={"a": "b"}))

# ── 8. get_current_active_span 在 trace 外
show("8 get_current_active_span() 在 trace 外", lambda: repr(mlflow.get_current_active_span()))

# ── 9. search_traces filter 語法：什麼會報錯、什麼會靜靜回 0
#     實測結論：「點」前面的 entity type 會驗，「點」後面的 key 不驗。
#     tag 與 tags 都是合法 entity type（少一個 s 不是 bug）；tag 名字大小寫／單複數打錯才是沉默的失敗。
with mlflow.start_span(name="tagged") as _sp:   # 先造一條帶 topic 標籤的 trace 來搜
    _sp.set_inputs({"q": "退貨"})
    mlflow.update_current_trace(tags={"topic": "退貨"})
mlflow.flush_trace_async_logging()

show("9a filter 少引號", lambda: len(mlflow.search_traces(experiment_ids=[EXP], filter_string="tags.topic = 退貨")))
show("9b filter 用 ==", lambda: len(mlflow.search_traces(experiment_ids=[EXP], filter_string="tags.topic == '退貨'")))
show("9c tags.topic（正確）", lambda: len(mlflow.search_traces(experiment_ids=[EXP], filter_string="tags.topic = '退貨'")))
show("9d tag.topic（少一個 s：也合法）", lambda: len(mlflow.search_traces(experiment_ids=[EXP], filter_string="tag.topic = '退貨'")))
show("9e tags.Topic（大小寫錯：沉默回 0）", lambda: len(mlflow.search_traces(experiment_ids=[EXP], filter_string="tags.Topic = '退貨'")))
show("9f tags.topics（多一個 s：沉默回 0）", lambda: len(mlflow.search_traces(experiment_ids=[EXP], filter_string="tags.topics = '退貨'")))
show("9g foo.topic（entity type 不存在）", lambda: len(mlflow.search_traces(experiment_ids=[EXP], filter_string="foo.topic = '退貨'")))
show("9h attributes.execution_duration（欄名錯）", lambda: len(mlflow.search_traces(experiment_ids=[EXP], filter_string="attributes.execution_duration > 100")))
show("9i attributes.execution_time_ms（正確）", lambda: len(mlflow.search_traces(experiment_ids=[EXP], filter_string="attributes.execution_time_ms > 0")))

# ── 10. genai.evaluate 的 scorer 簽章寫錯
from mlflow.genai import evaluate, scorer  # noqa: E402

DATA = [
    {"inputs": {"q": "退貨要多久內？"}, "outputs": "退貨期限為 7 天，需保留原包裝。"},
    {"inputs": {"q": "可以分期嗎？"}, "outputs": "手冊裡沒有寫。"},
]


@scorer
def bad_arg(answer_text) -> bool:  # 參數名不是 inputs/outputs/expectations/trace
    return True


show("10a scorer 參數名不在允許清單", lambda: evaluate(data=DATA, scorers=[bad_arg]).metrics)


@scorer
def has_number(outputs) -> bool:
    return any(ch.isdigit() for ch in str(outputs))


show("10b scorer 正常", lambda: dict(evaluate(data=DATA, scorers=[has_number]).metrics))

# ── 11. evaluate 資料缺 outputs 欄
show("11 evaluate(data 只有 inputs、沒有 outputs 也沒有 predict_fn)", lambda: dict(evaluate(data=[{"inputs": {"q": "x"}}], scorers=[has_number]).metrics))

# ── 12. 巢狀 span 的計時：execution_duration
t = mlflow.get_trace(TID)
print(f"[OK ] 12 trace {t.info.trace_id[:14]}… duration={t.info.execution_duration} ms, state={t.info.state}")
print("     spans:", [(s.name, s.span_type, round((s.end_time_ns - s.start_time_ns) / 1e6, 1)) for s in t.data.spans])
print("=" * 100)
print("done, workdir:", W)
