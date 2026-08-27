# /// script
# requires-python = ">=3.11"
# dependencies = ["openai"]
# ///
"""genai-agents 課的定軌 spike：手工 tool loop 的真實 trace（嵌進課程 hero 的來源）。

不靠框架，直接演 function calling 的底層機制：
  1. system prompt 描述工具與 JSON 輸出格式
  2. 模型決定「要不要用工具」——要用就吐 JSON
  3. 我們執行工具（教學用模擬資料的天氣查詢）、把結果塞回對話
  4. 模型整合結果產生最終回答
對照組：不需要工具的問題，模型應直接回答。

需要 env：RELAY_URL、API_KEY。
跑法：uv run --script content/genai-intro/_spikes/spike_genai_agents.py
"""

import json
import os

from openai import OpenAI

MODEL = "qwen3.5-2b"
client = OpenAI(base_url=f"{os.environ['RELAY_URL']}/v1", api_key=os.environ["API_KEY"],
                default_headers={"User-Agent": "gtq-client/1.0"})

SYSTEM = (
    "你是一個助理，可以使用以下工具：\n"
    'get_weather(city)：查詢城市目前天氣，回傳氣溫、天氣狀況與降雨機率。\n\n'
    "規則：需要工具時，只輸出一行 JSON，格式為 "
    '{"tool": "get_weather", "args": {"city": "城市名"}}，不要輸出任何其他文字。\n'
    "不需要工具就直接用繁體中文回答。"
)

# 教學用模擬資料（課程會明講：這是我們自己寫的假天氣查詢函式）
FAKE_WEATHER = {"台北": {"temp_c": 24, "condition": "小雨", "rain_prob": 80}}


def chat(messages, max_tokens=512):
    r = client.chat.completions.create(
        model=MODEL, messages=messages, max_tokens=max_tokens, temperature=0.0,
        extra_body={"chat_template_kwargs": {"enable_thinking": False}})
    return (r.choices[0].message.content or "").strip()


# ── 回合 1：需要工具的問題 ───────────────────────────────────────────
print("== turn 1: tool needed ==")
q1 = "台北現在天氣怎麼樣？出門要帶傘嗎？"
msgs = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": q1}]
call_raw = chat(msgs)
print("MODEL →", call_raw)
call = json.loads(call_raw[call_raw.index("{"): call_raw.rindex("}") + 1])
assert call["tool"] == "get_weather" and "台北" in call["args"]["city"], "應呼叫 get_weather(台北)"

tool_result = FAKE_WEATHER[call["args"]["city"]]
print("TOOL  →", json.dumps(tool_result, ensure_ascii=False))
msgs += [
    {"role": "assistant", "content": call_raw},
    {"role": "user", "content": f"工具回傳結果：{json.dumps(tool_result, ensure_ascii=False)}\n請根據結果回答使用者原本的問題。"},
]
final = chat(msgs)
print("MODEL →", final)
assert ("傘" in final) and ("24" in final or "雨" in final), "最終回答應整合工具結果"

# ── 回合 2：不需要工具的問題 ─────────────────────────────────────────
print("\n== turn 2: no tool needed ==")
q2 = "什麼是光合作用？用一句話說明。"
direct = chat([{"role": "system", "content": SYSTEM}, {"role": "user", "content": q2}])
print("MODEL →", direct)
assert "get_weather" not in direct and "{" not in direct[:5], "不需要工具的問題應直接回答"

print("\n# ---- 貼進課程的常數 ----")
print(json.dumps({
    "q1": q1, "call_raw": call_raw, "tool_result": tool_result,
    "final": final, "q2": q2, "direct": direct,
}, ensure_ascii=False, indent=1))
print("\nSPIKE OK: genai-agents")
