# llm-apps 系列建課筆記（2026-08-20）

六堂外部軌課（molab）一次建成：litellm-basics → litellm-tools → fastmcp4 → qdrant-basics → rag-zh → rag-mcp-agent。
每課目錄下沒有個別 NOTES，踩坑集中在這裡。

## 軌道決策

`pyodide-spike.mjs openai qdrant-client fastmcp` 三個全 FAIL（無純 Python wheel），加上整個系列要真網路打
gateway → 全部外部軌。gateway 其實有開 CORS（`access-control-allow-origin: *`），但 openai SDK 進不了
Pyodide，瀏覽器軌道只能用 JS fetch 重寫，不符「課程程式＝學員帶得走的程式」原則，放棄。

## LiteLLM gateway 實測事實（教學 key `sk-FiIR…`，課後撤銷）

- 教學 key 看得到 8 個模型名：free-chat / nemotron-3-ultra / gemini-3.5-flash / gpt-oss-120b /
  cf-gpt-oss-120b / deepseek-v4-flash / qwen3-embedding-0.6b(1024) / nemotron-3-embed-1b(2048)。
- **free-chat 的 HuggingFace 部署月額度用完回 402，LiteLLM 不重試也不換家**（402 不在預設重試清單，
  20 發約 2 發失敗）。`deepseek-v4-flash` 直打同樣 402。**使用者決定：全系列一律用 `nemotron-3-ultra`，
  不用 free-chat**（2026-08-20 第二輪）。gateway 端若要修：從 free-chat 拿掉 HF 部署，或 router_settings
  加 `fallbacks`／對 402 做 cooldown。
- **nemotron-3-ultra 實測特性**：三個來源延遲差很大（NIM 1.6–30 秒、Ollama Cloud 最慢 60 秒；12 發並發
  牆鐘約 60 秒、序跑 200 秒）；`max_tokens=20` 回 `'1 + 1'` 被截斷（不是空字串）、`reasoning_tokens`
  只有 NIM 回報（其他家 None）；串流首 chunk 要等思考完（約 6 秒）再一口氣湧出；tool call 回合的
  `content` 是 `None`；**structured output 看落到哪家**——有的來源嚴格遵守、有的回 markdown 表
  （drop_params），所以 5️⃣ 示範格寫成 json.loads 失敗就 callout 解釋，不崩潰；不吃圖（OpenRouter 404）；
  RAG 與 agent 都 OK，但 agent 每題 10–50 秒；「1+1」零工具呼叫但答「手冊裡沒有寫基本數學運算」
  （system prompt 套用過頭，做成教學點與 LEVEL 3）。偶爾回應開頭有一個 `�` 字元（某上游的雜訊）。
- gpt-oss-120b 作對照：`max_tokens=20` → content `''`、reasoning_tokens 18；agent 每題 1–5 秒。
- 回應的 `model` 欄位是群組名 `free-chat`（不是實際模型），辨識上游只能靠
  `x-litellm-model-api-base` header；OpenRouter 部署沒帶 host（空字串）。
- `qwen3-embedding-0.6b` 回傳已是單位向量（norm=1），內積＝cosine；批次 10 段約 10 秒（CF 較慢）。
- tool calling：gpt-oss-120b / gemini / nemotron-3-ultra / cf-gpt-oss 都 ✅；structured output 只有
  gpt-oss 與 gemini 嚴格遵守，nemotron-3-ultra 被 drop_params 默默拿掉 schema 吐 markdown 表（教學點）；
  vision 只有 gemini-3.5-flash。
- CF zone 曾開「Block AI bots」誤殺 openai SDK UA（已關）；再發生加 `default_headers={"User-Agent": ...}`。

## FastMCP 4.0.0b1 實測事實（使用者指定 b1；PyPI 最新 beta 是 b3）

- 新協定版本 `2026-07-28`：第一發 `server/discover`（取代 initialize），之後每發帶
  `mcp-protocol-version`、`mcp-method`、`mcp-name` header ＋ body `params._meta` 信封
  （`io.modelcontextprotocol/protocolVersion`、`clientCapabilities`），**完全沒有 session id**。
  `Client(url, mode="legacy")` → `2025-11-25`，initialize 回 `mcp-session-id`，呼叫一次 add 共 6 個 HTTP
  請求（含 GET 長連線與 DELETE）。
- 裸 `httpx.post` 單發 tools/call 成功的三要件：`MCP-Protocol-Version` header、`mcp-method` header
  （沒帶會 `-32020 mcp-method header does not match`）、`_meta` 信封（沒帶會 `-32602 params._meta must…`）。
  不宣告協定版本 → `Missing session ID`。
- `SessionProvider()` 自動註冊 `create_session`／`end_session` 兩個工具；`create_session()` 回傳的是 **str**
  （不是物件）。`UserSession` 需認證身分，本系列沒登入機制所以用 `SessionId`。
- 在 marimo cell 裡用 daemon thread 跑 uvicorn（`mcp.http_app()`）在 `export --sandbox` 下正常；
  重跑 cell 前先用 socket 探 port，已開就不重起。
- `Tool.input_schema`（不是 deprecated 的 `inputSchema`）。

## RAG 數字（寫左頁前實測）

- 手冊 10 段、59–91 字；沒 RAG 7 題矇對 0–2 題（跑多次、換模型都不同），有 RAG 7/7；範圍外「牛排」→「手冊裡沒有寫」
  且檢索分數全 < 0.4。左頁寫「0–2 題」不寫死 0。
- 壓軸 agent（gpt-oss-120b 與 nemotron-3-ultra 都驗過）：自己把 top_k 提成 5、一次查詢合併兩章節、「手冊有哪些章節」改用
  list_sections、1+1 不用工具——左頁 hero 的 trace 就是這次實測的紀錄。

## 管線層面

- 教學頁用 scratch 的 splice 腳本以 regex 只替換內容區：**先拿掉模板頂部的說明註解**（它含 `<style>`、
  `#molab-panel` 字樣會干擾比對），`re.sub` 的替換字串要用 lambda（內容含 `\u` 會被當 escape）。
- 驗證外部軌 notebook 的輸出：`export --sandbox` 產的 HTML 只嵌程式碼，**渲染結果在
  `content/<topic>/<id>/__marimo__/session/<id>_ext.py.json`**（gitignored），grep 那裡最快。
- matplotlib 圖內別放 emoji（❌ → 缺字警告），用 ASCII 標籤。
- sandbox 會裝最新 marimo（0.24.0）而非全站釘的 0.23.16——外部軌不共用 assets，無妨。
