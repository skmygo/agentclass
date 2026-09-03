# 候選課 spike：MLflow Prompt Registry（LLMOps）——註冊、版本、alias、format、跟 trace 連結；不打真 LLM
# /// script
# requires-python = ">=3.11"
# dependencies = ["mlflow>=3.0", "pandas"]
# ///
import logging, tempfile, warnings
from pathlib import Path
import mlflow
warnings.filterwarnings("ignore"); logging.getLogger("mlflow").setLevel(logging.ERROR)
W = Path(tempfile.mkdtemp()); mlflow.set_tracking_uri(f"sqlite:///{W}/m.db")
mlflow.create_experiment("prompts", artifact_location=str(W/"art")); mlflow.set_experiment("prompts")
p1 = mlflow.genai.register_prompt(name="support-answer", template="你是客服。只根據資料回答：{{context}}\n問題：{{question}}", commit_message="v1 初版", tags={"lang": "zh-Hant"})
print("v1:", p1.name, p1.version, p1.uri if hasattr(p1, "uri") else "")
p2 = mlflow.genai.register_prompt(name="support-answer", template="你是客服，語氣親切。只根據資料回答，資料沒有就說「手冊裡沒有寫」。\n資料：{{context}}\n問題：{{question}}", commit_message="v2 加上拒答規則")
print("v2:", p2.version)
mlflow.genai.set_prompt_alias("support-answer", alias="production", version=1)
prod = mlflow.genai.load_prompt("prompts:/support-answer@production")
print("loaded @production → version", prod.version, "| vars", prod.variables if hasattr(prod, "variables") else None)
print("format:", prod.format(context="退貨 7 天", question="可以退嗎？")[:60])
mlflow.genai.set_prompt_alias("support-answer", alias="production", version=2)
print("after promote:", mlflow.genai.load_prompt("prompts:/support-answer@production").version)
v1 = mlflow.genai.load_prompt("prompts:/support-answer/1")
print("v1 by version:", v1.version, "| tags", getattr(v1, "tags", None))
# search
try:
    res = mlflow.genai.search_prompts(filter_string="name = 'support-answer'")
    print("search_prompts:", [(r.name, getattr(r, 'latest_version', None)) for r in res][:3])
except Exception as e:
    print("search err:", type(e).__name__, str(e)[:120])
# link to run / trace
with mlflow.start_run(run_name="eval-with-prompt") as r:
    try:
        mlflow.log_param("prompt_uri", f"prompts:/support-answer/{p2.version}")
        mlflow.genai.load_prompt(f"prompts:/support-answer/{p2.version}", link_to_run=True) if "link_to_run" in mlflow.genai.load_prompt.__code__.co_varnames else None
        print("linked to run ok")
    except Exception as e:
        print("link err:", type(e).__name__, str(e)[:160])
@mlflow.trace
def answer(q):
    pr = mlflow.genai.load_prompt("prompts:/support-answer@production")
    return pr.format(context="退貨 7 天", question=q)[:20]
answer("可以退嗎？"); mlflow.flush_trace_async_logging()
exp = mlflow.get_experiment_by_name("prompts").experiment_id
tr = mlflow.search_traces(experiment_ids=[exp])
print("traces:", len(tr), "| tags:", tr.iloc[0]["tags"] if "tags" in tr.columns else list(tr.columns))
# chat-format prompt
try:
    pc = mlflow.genai.register_prompt(name="support-chat", template=[{"role": "system", "content": "你是客服，只根據 {{context}} 回答"}, {"role": "user", "content": "{{question}}"}])
    print("chat prompt:", pc.version, pc.format(context="X", question="Y"))
except Exception as e:
    print("chat prompt err:", type(e).__name__, str(e)[:160])
