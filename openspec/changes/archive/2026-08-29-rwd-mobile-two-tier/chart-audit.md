# task 4.1 app 課超標圖盤點（回修對象：figsize 寬 ≥9 或 1×2 並排 subplot）

grep 基準：`grep -rn 'figsize' content/genai-intro content/local-llm --include=lesson.py`

| 課 | 行 | 現況 | 回修 |
|---|---|---|---|
| local-llm/kv-cache | 450 | subplots(1,2, 9.2×3.6) | 2×1 堆疊、寬 ≤6.5 |
| local-llm/prompt-caching | 219 | subplots(1,2, 9.6×4.0) | 同上 |
| local-llm/prompt-caching | 292 | subplots(1,2, 9.6×4.0) | 同上 |
| local-llm/sampling-params | 240 | subplots(1,2, 9.6×4.0) | 同上 |
| local-llm/sampling-params | 351 | 單軸 9.6×4.2 | 寬壓 ≤6.5 |
| local-llm/sampling-params | 461 | subplots(1,2, 9.6×4.0) | 2×1 堆疊 |
| local-llm/sampling-params | 517 | subplots(1,2, 9.6×3.9) | 2×1 堆疊 |
| local-llm/ollama-vs-vllm | 129 | subplots(1,2, 9.2×3.9, sharey) | 2×1 堆疊 |
| local-llm/ollama-vs-vllm | 223 | 單軸 9.2×3.9 | 寬壓 ≤6.5 |
| local-llm/ollama-vs-vllm | 333 | 單軸 9.2×3.9 | 寬壓 ≤6.5 |
| local-llm/ollama-vs-vllm | 450 | subplots(1,2, 9.2×4.1) | 2×1 堆疊 |
| local-llm/speculative-decoding | 388 | subplots(1,2, 9.4×4.1) | 2×1 堆疊 |
| local-llm/lora-basics | 90 | subplots(1,2, 8.2×3.5) | 2×1 堆疊 |
| local-llm/lora-basics | 193 | subplots(1,2, 8.2×3.5) | 2×1 堆疊 |
| local-llm/lora-basics | 333 | subplots(1,2, 8.2×3.5) | 2×1 堆疊 |
| local-llm/lora-basics | 583 | subplots(1,2, 8.2×3.5) | 2×1 堆疊 |
| local-llm/llm-observability | 312 | subplots(1,2, 8.2×動態高) | 2×1 堆疊（高度×2） |
| genai-intro/genai-training | 99 | subplots(1,2, 7.4×3.9) | 2×1 堆疊 |
| genai-intro/genai-agents | 229 | subplots(1,2, 7.6×4.0) | 2×1 堆疊 |

需重驗課程（9）：kv-cache、prompt-caching、sampling-params、ollama-vs-vllm、
speculative-decoding、lora-basics、llm-observability、genai-training、genai-agents。
不動：edit 課（ml-basics 等）與寬 6.5–9 之單軸圖（無——單軸超標三處皆 ≥9 已列入）。
