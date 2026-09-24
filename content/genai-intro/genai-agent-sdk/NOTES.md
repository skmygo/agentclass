# genai-agent-sdk（補充 C）NOTES

Claude Agent SDK 課：同一個修 bug 任務、同一個模型，只改 `ClaudeAgentOptions` 的權限設定，錄六次真實訊息串；
瀏覽器端重播錄影＋權限閘門模擬器（依官方文件的評估順序，當場算）＋帳單重算。純瀏覽器 app 模式、2 張圖。

## 素材來源（全部實測，2026-09-24）

- **SDK／CLI**：`claude-agent-sdk==0.2.159`（內含 Claude Code 2.1.281），本機已登入的 claude CLI；
  模型 `claude-haiku-4-5`。錄影與探路全部 list cost 約 US\$0.8（hero 0.41、plan 兩次 0.13、extras 三版合計 0.10、
  gate 0.07、errors 約 0.05、探路 0.03；`total_cost_usd` 加總）。
- **腳本**：`content/genai-intro/_spikes/spike_genai_agent_sdk.py`（錄製）→
  `spike_genai_agent_sdk_payload.py`（截短＋注入 `lesson.py` 的 `TRACES` 與 `page_content.py` 的 `HERO_TRACES`）。
  ```bash
  cd <scratch> && env -i HOME="$HOME" PATH="/usr/local/bin:/usr/bin:/bin:$HOME/.local/bin" LANG=C.UTF-8 \
    SPIKE_OUT="$PWD/runs" uv run --script <repo>/content/genai-intro/_spikes/spike_genai_agent_sdk.py hero plan extras gate errors
  # free 段（開源模型）：FREE_BASE_URL=<Anthropic 相容端點根網址> FREE_MODEL=<模型名>
  #   vLLM 的 qwen3.5 要關 thinking：FREE_EXTRA_BODY='{"chat_template_kwargs":{"enable_thinking":false}}'
  SPIKE_OUT=<scratch>/runs uv run --script content/genai-intro/_spikes/spike_genai_agent_sdk_payload.py
  python3 .claude/skills/make-lesson/scripts/page-fill.py content/genai-intro/genai-agent-sdk
  ```
  payload 腳本另讀 `runs/extras_v1_async.json`（第一版 extras 的 session 第 3 次回答「shop-demo」）——沒有這個檔就只寫一個回答。
- **env 變數**：`SPIKE_OUT`、`SDK_MODEL`、`FREE_BASE_URL`、`FREE_MODEL`、`FREE_EXTRA_BODY`。端點位址只從 env 讀；
  spike 的 `sanitize()` 會把家目錄、使用者名稱、`FREE_BASE_URL` 的 host:port 全部遮掉
  （Claude Code 的 API 錯誤訊息會印出「check your inference gateway (host:port)」，實測踩到）。
- **免費路徑實測**：vLLM 0.26.0 的 `/v1/messages`（Anthropic 相容）＋ `qwen3.5-2b`（max_model_len 16384）。
  Ollama（本機／Cloud）**沒有在本機實測**，課文照官方文件寫並標明。

## 踩到的坑（重驗時先看）

1. **一定要在乾淨環境跑 spike**：從 Claude Code session 裡直接跑，子 CLI 會繼承 `CLAUDECODE`、`CLAUDE_CODE_*`
   環境變數（messaging socket、session id…）。用 `env -i HOME=… PATH=…` 起。`setting_sources=[]`、
   `strict_mcp_config=True` 避免把使用者的 settings／plugins／MCP 混進 trace。
2. **init 工具清單會變**：2.1.281 在 Linux 預設 29 個工具，**沒有 Glob／Grep**（搜尋走 Bash 的 find/grep——所以 Bash hook
   連找檔案都擋，③ 的教學點）；接了 `can_use_tool` 會多出 AskUserQuestion／EnterPlanMode／ExitPlanMode（32 個）；
   `ANTHROPIC_BASE_URL` 指到非官方端點時工具搜尋自動關閉，清單剩 20 個。換 CLI 版本這些數字全要重數。
3. **plan 模式不接 can_use_tool 會空轉**（④：22 輪、$0.198，找不到 ExitPlanMode）；接了才走得完（⑥）。
4. **子代理預設背景執行**（2.1.281）：主代理那一輪先收工、ResultMessage 先到。spike 的 `run()` 會追
   `TaskStartedMessage`／`TaskNotificationMessage`，背景任務沒回報就繼續 `receive_response()`；
   x2 的 prompt 要寫「等它跑完拿到結果再回答」，模型才會 `run_in_background: false`。
5. **`subtype="success"` 不等於做成**：六段 hero 全是 success；free 的 A、B 是 `success`＋`is_error=True`（錯誤包成文字）。
6. **per-message usage 的 output_tokens 不可靠**（message_start 時的值，多半是 1）：圖只畫輸入側；花費用
   `ResultMessage.model_usage` 重算（Haiku 牌價重算與 `total_cost_usd` 對得上）。model_usage 裡另有一筆約 950 tokens 的
   `claude-haiku-4-5-20251001` 呼叫不在訊息串裡（streaming client 才有；用 `query()` 的單發探測沒有），課文只說「harness 自己發的」。
7. **本機模型的 `total_cost_usd` 是假的**：costBasis=unknown，數字＝token 數 × \$4／\$20（Opus 5.5 牌價）。
8. **小 context 模型**：CLI 對不認得的模型預設 max_tokens 32000（vLLM 直接 500）→ `CLAUDE_CODE_MAX_OUTPUT_TOKENS=4096`；
   預設工具說明書 ≥12,289 tokens（qwen tokenizer）→ `tools=[…]` 只開 3 個＋短 system prompt 降到 2,068。
   錯誤會重試（`CLAUDE_CODE_MAX_RETRIES`：env-vars 文件寫預設 5、SDK 文件寫 10），一次錯誤可等 3 分鐘，spike 設 2。
9. query() 字串 prompt＋`can_use_tool` 在 0.2.159 **可以**跑（舊版要 streaming prompt），測驗 Q4 的 C 選項據此判錯。
10. 1 小時快取：Claude Code 寫的是 `ephemeral_1h`（寫入 ×2）；同一小時內重跑，工具說明書前綴會命中上一次的快取
    （hero 第一次呼叫 cache_read 11,303 就是這樣來的），換工具組合（⑤）就 miss。

## 換模型／改版要重驗的句子

- 教學頁與 notebook 裡所有「N 輪、\$X、N 秒、被擋 N 次」都來自 payload（notebook 表格與圖是從 TRACES 算的，
  會自動跟著變）；**寫死在 page_content.py 的**要手改：hero 下方說明、s2 的三個反直覺例子（原文引號）、
  s3「擋了三次：兩個 find、一個 ls -la」「22 輪 \$0.198」「14 輪 \$0.107」、s4「1.46 萬／17 萬／16.2 萬／8,504／82／\$0.0495」、
  s5「3 輪 \$0.0058、1,339 token」、s6「\$0.05、9 輪 3.5 分鐘、2,068、12,289、\$0.1306」、測驗五題的解釋。
- 權限評估順序、模式說明、Glob/Grep 缺席、子代理背景預設：2026-09 查證自 code.claude.com/docs/en/agent-sdk/*，改版要重查。
- 牌價（Haiku 4.5 \$1/\$5、Sonnet 5 \$2/\$10、Opus 5 \$5/\$25，1h 快取寫入 ×2、讀取 ×0.1）：platform.claude.com pricing，2026-09-24。
- Ollama：v0.14+ 支援 `/v1/messages`（官方 blog 2026-01-16）；Cloud 免費方案「入門額度＋入門模型＋1 個並行」（ollama.com/pricing，2026-09）。
