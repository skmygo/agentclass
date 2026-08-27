# /// script
# requires-python = ">=3.11"
# dependencies = ["openai"]
# ///
"""genai-reasoning 課的定軌 spike：所有 LLM 輸出都在這裡實測捕捉（嵌進課程的 trace 來源）。

需要 env：RELAY_URL、API_KEY（OpenAI 相容端點，模型 qwen3.5-2b）。
四段：
  A. 同一題（球棒與球）：直接答 vs 要求一步一步想（CoT）——temp=0
  B. 思考模式（reasoning model 行為）：思考軌跡與最終答案分離
  C. Overthinking：「1+1=?」開思考模式，看它想了多少字
  D. Test-time compute：47×38 直接答、temp=1 抽 9 次多數決

跑法：uv run --script content/genai-intro/_spikes/spike_genai_reasoning.py
"""

import json
import os
from collections import Counter

from openai import OpenAI

MODEL = "qwen3.5-2b"
client = OpenAI(base_url=f"{os.environ['RELAY_URL']}/v1", api_key=os.environ["API_KEY"],
                default_headers={"User-Agent": "gtq-client/1.0"})


def ask(prompt, thinking=False, max_tokens=1024, temperature=0.0):
    kwargs = {} if thinking else {"extra_body": {"chat_template_kwargs": {"enable_thinking": False}}}
    r = client.chat.completions.create(
        model=MODEL, messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens, temperature=temperature, **kwargs)
    m = r.choices[0].message
    reasoning = getattr(m, "reasoning", None) or getattr(m, "reasoning_content", None) or ""
    return (m.content or "").strip(), (reasoning or "").strip()


BALL_Q = "一根球棒和一顆球總共 110 元，球棒比球貴 100 元。球多少錢？"

# ── A. 直接答 vs CoT ────────────────────────────────────────────────
print("== A. direct vs CoT ==")
direct, _ = ask(BALL_Q + "請直接回答，只給一個數字，不要解釋。", max_tokens=64)
print("DIRECT:", direct)
cot, _ = ask(BALL_Q + "請一步一步推理，把每一步寫出來，最後一行寫「答案：X 元」。", max_tokens=512)
print("COT:\n", cot)
assert "5" in cot.splitlines()[-1] and "55" not in cot.splitlines()[-1], "CoT 最後一行應為 5 元"

# ── B. 思考模式 ─────────────────────────────────────────────────────
# 實測發現（2026-08-28）：relay 的 reasoning parser 會把整段輸出塞進 reasoning、
# content 永遠是空字串（finish=stop）——thinking 模式的素材「不能」拿去課程當
# reasoning model 示範。課程只用 A（CoT 對照）與 D（多數決）兩段實測。
print("\n== B. thinking mode ==")
content, reasoning = ask(BALL_Q, thinking=True, max_tokens=2048)
print(f"reasoning {len(reasoning)} chars / content {len(content)} chars")
print("REASONING (head):", reasoning[:300].replace("\n", " "))
print("CONTENT:", content[:300].replace("\n", " "))
assert reasoning, "思考模式應有 reasoning 軌跡"

# ── C. overthinking ─────────────────────────────────────────────────
print("\n== C. overthinking on 1+1 ==")
c2, r2 = ask("1+1=?", thinking=True, max_tokens=2048)
c3, _ = ask("1+1=? 只回答數字。", max_tokens=16)
print(f"thinking 模式：想了 {len(r2)} 字才回「{c2[:40]}」；直接答：「{c3}」")

# ── D. test-time compute：多數決 ─────────────────────────────────────
print("\n== D. majority vote on 47×38 ==")
MUL_Q = "47 × 38 = ? 請直接回答，只給一個數字，不要列直式、不要解釋。"
answers = []
for i in range(9):
    a, _ = ask(MUL_Q, max_tokens=32, temperature=1.0)
    digits = "".join(ch for ch in a if ch.isdigit())
    answers.append(digits or a)
tally = Counter(answers)
print("9 次抽樣：", dict(tally))
top, n = tally.most_common(1)[0]
print(f"多數決 → {top}（{n}/9 票）；正解 1786，單次答對率 {tally.get('1786', 0)}/9")

# 供課程嵌入的 trace 常數
print("\n# ---- 貼進課程的常數 ----")
print(json.dumps({
    "ball_direct": direct, "ball_cot": cot,
    "think_reasoning": reasoning, "think_content": content,
    "one_plus_one_reasoning_chars": len(r2), "one_plus_one_answer": c2,
    "vote_tally": dict(tally),
}, ensure_ascii=False, indent=1))
print("\nSPIKE OK: genai-reasoning")
