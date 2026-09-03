# 候選課 spike：MLflow Tracing（GenAI）——@mlflow.trace、手動 span、search_traces、assessments；不打真 LLM（假模型）
# /// script
# requires-python = ">=3.11"
# dependencies = ["mlflow>=3.0", "pandas"]
# ///
import logging, tempfile, time, warnings
from pathlib import Path
import mlflow, pandas as pd
warnings.filterwarnings("ignore"); logging.getLogger("mlflow").setLevel(logging.ERROR)
W = Path(tempfile.mkdtemp()); mlflow.set_tracking_uri(f"sqlite:///{W}/m.db")
mlflow.create_experiment("tracing", artifact_location=str(W/"art")); mlflow.set_experiment("tracing")
DOCS = {"退貨": "退貨期限為 7 天，需保留原包裝。", "運費": "滿 1000 元免運，否則運費 80 元。", "付款": "支援信用卡與超商代碼。"}

@mlflow.trace(span_type="RETRIEVER")
def retrieve(q: str) -> list[dict]:
    time.sleep(0.02)
    hits = [{"doc": k, "text": v} for k, v in DOCS.items() if k in q]
    return hits or [{"doc": "none", "text": ""}]

@mlflow.trace(span_type="LLM")
def fake_llm(prompt: str) -> dict:
    time.sleep(0.05)
    ans = prompt.split("資料：")[-1].split("問題")[0].strip() or "手冊裡沒有寫。"
    return {"content": ans, "usage": {"prompt_tokens": len(prompt), "completion_tokens": len(ans)}}

@mlflow.trace(name="answer", span_type="CHAIN")
def answer(q: str) -> str:
    ctx = retrieve(q)
    span = mlflow.get_current_active_span()
    span.set_attributes({"n_docs": len(ctx), "question_len": len(q)})
    prompt = f"資料：{ctx[0]['text']}\n問題：{q}"
    out = fake_llm(prompt)
    mlflow.update_current_trace(tags={"topic": ctx[0]["doc"]})
    return out["content"]

for q in ["退貨要多久內？", "運費多少？", "可以分期嗎？"]:
    print("Q:", q, "→", answer(q))
mlflow.flush_trace_async_logging()
EXP_ID = mlflow.get_experiment_by_name("tracing").experiment_id
traces = mlflow.search_traces(experiment_ids=[EXP_ID])
print("traces df:", traces.shape, list(traces.columns)[:8])
t = mlflow.get_trace(traces.iloc[0]["trace_id"])
print("trace id:", t.info.trace_id[:12], "ms:", t.info.execution_duration if hasattr(t.info, "execution_duration") else t.info.execution_time_ms, "spans:", [(s.name, s.span_type) for s in t.data.spans])
sp = [s for s in t.data.spans if s.span_type == "LLM"][0]
print("LLM span inputs:", str(sp.inputs)[:80], "| outputs:", str(sp.outputs)[:80], "| attrs keys:", [k for k in sp.attributes if not k.startswith("mlflow.")][:5])
# assessments: feedback + expectation
from mlflow.entities import AssessmentSource, AssessmentSourceType
mlflow.log_feedback(trace_id=t.info.trace_id, name="correct", value=True, rationale="答案含期限", source=AssessmentSource(source_type=AssessmentSourceType.HUMAN, source_id="teacher"))
mlflow.log_expectation(trace_id=t.info.trace_id, name="expected_answer", value="7 天", source=AssessmentSource(source_type=AssessmentSourceType.HUMAN, source_id="teacher"))
t2 = mlflow.get_trace(t.info.trace_id)
print("assessments:", [(a.name, getattr(a, 'feedback', None) and a.feedback.value or getattr(a,'expectation',None) and a.expectation.value) for a in t2.info.assessments])
# search by tag
print("by tag:", len(mlflow.search_traces(experiment_ids=[EXP_ID], filter_string="tags.topic = '退貨'")))
# manual span
with mlflow.start_span(name="batch-eval", span_type="CHAIN") as s:
    s.set_inputs({"n": 3}); s.set_outputs({"ok": 3})
mlflow.flush_trace_async_logging()
print("total traces:", len(mlflow.search_traces(experiment_ids=[EXP_ID])))
# genai evaluate with code-based scorer (no LLM judge)
try:
    from mlflow.genai import evaluate, scorer
    @scorer
    def has_number(outputs) -> bool:
        return any(ch.isdigit() for ch in str(outputs))
    data = [{"inputs": {"q": "退貨要多久內？"}, "outputs": "退貨期限為 7 天，需保留原包裝。"}, {"inputs": {"q": "可以分期嗎？"}, "outputs": "手冊裡沒有寫。"}]
    res = evaluate(data=data, scorers=[has_number])
    print("genai.evaluate metrics:", {k: v for k, v in res.metrics.items()})
except Exception as e:
    print("genai.evaluate err:", type(e).__name__, str(e)[:200])
