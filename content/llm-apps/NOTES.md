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
  20 發約 2 發失敗）。`deepseek-v4-flash` 直打同樣 402。使用者同日已在 gateway 移除 HF 並加
  `fallbacks: free-chat → gpt-oss-120b`。**使用者決定：全系列一律用 `nemotron-3.5-lightning`**
  （第二輪先改 nemotron-3-ultra，第三輪改 lightning；兩者都實測過）。
- **nemotron-3.5-lightning（30B-A3B，NIM＋OpenRouter:free 雙部署）實測特性**：
  想很多（自我介紹 646 reasoning token、1+1 約 100–150）→ **`max_tokens` 一律 4096**；給太小時
  `content` 是被截斷的思考文字（"Here's a thinking process…"），給夠則答案在 `content`、思考在
  `reasoning_content`（非標準欄位，`getattr(message, "reasoning_content", None)`）；`reasoning_tokens`
  OpenRouter 回報、NIM 是 None。延遲多數 2–5 秒、偶爾 10–15 秒，12 發並發牆鐘約 15 秒（序跑 55 秒）。
  tool calling OK 但會把城市名翻成 `"Taipei"`（假天氣函式加英文別名）；agent 的搜尋詞也會變英文
  （`"parking"`）→ 工具 docstring 加「query 請用繁體中文」後就正常；「1+1」多半不查、偶爾字面地先查一次。
  structured output 兩個來源都遵守；不吃圖；RAG 0/7 → 7/7；回答偶有簡體字或 `�` 雜訊。
- **教學 key 白名單**要手動加新模型：`POST /key/update`（master key 在容器 env：
  `docker exec litellm-gw-xkpqch-litellm-1 printenv LITELLM_MASTER_KEY`；.10 的 `.env` 備份已不同步）。
  Dokploy 改 file mount 後 redeploy **不一定會讓 litellm 重讀 config**（container 沒重建）——
  `/model/info` 沒有新模型、`/health?model=` 回 healthy 0／unhealthy 0 就是這個症狀，要重啟容器。
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

## FastMCP 4 補充系列（2026-08-20：fastmcp4-auth / fastmcp4-state / fastmcp4-features / mcp-servers）

四堂外部軌課，全部 `fastmcp==4.0.0b1`（與第 3 課同版；PyPI 當天最新 b3，4.0.0 正式版未出）。
前三堂完全不連外；`mcp-servers` 需要網路（uvx 裝套件、遠端伺服器）。
spike：`_spikes/spike_fastmcp_auth.py`、`spike_fastmcp_state.py`、`spike_fastmcp4_features.py`、`spike_mcp_servers.py`。
同時建課時 port 分段：auth 8771–8775、state 8781–8789、servers 8791、features 8801–8809（並行 verify 不會撞）。

### 「無狀態傳狀態有沒有加密」的答案（fastmcp4-state）

- 三種記憶：`ctx.set_state`（一個請求）、`SessionId`/`UserSession`（伺服器端 store，客戶端只拿鑰匙）、
  `InputRequiredResult.request_state`（真的經過客戶端）。只有第三種有「加密」問題。
- `request_state` 由 MCP SDK `mcp.server.request_state.RequestStateBoundary` 在線路邊界 seal/unseal：
  **AES-256-GCM**（HKDF-SHA256 派生），token 格式 `v1.` + base64url(4B kid | 12B nonce | 密文+tag)，約 270–290 字元；
  密文內是 claims 信封 `{v, iat, exp, m, t, a(參數 sha256 摘要), aud(伺服器名), p(principal 指紋), s(明文)}`。
  預設 ttl 600 秒；預設金鑰 `RequestStateSecurity.ephemeral()`（process 啟動隨機）→ **多副本／重啟都會讓進行中的多回合作廢**，
  要 `FastMCP(request_state_security=RequestStateSecurity(keys=[≥32 bytes]))`；`keys` 是金鑰環（`keys[0]` 加密、全部可解）。
- 實測五種攻擊（竄改一字元／另一台臨時金鑰／同 token 換 arguments／同 key 不同伺服器名／ttl 過期）線路上**一律**
  `-32602 Invalid or expired requestState`，真正原因只在伺服器 log（`seal`／`unknown key`／`request binding`／`audience`／`expired`）。
- `Session` 狀態跨副本：`FastMCP(session_state_store=store)` 給同一個 `key_value.aio.stores.memory.MemoryStore`（正式 RedisStore）
  即可模擬多副本；不共用 store 的副本回 `Invalid or unknown session`（stderr 會印 `Error calling tool 'show_cart'`，屬正常）。
  未認證的 session id 是不記名票（猜不到≠隔離）。
- `ctx.get_state`/`ctx.set_state` 在 b1 是 **async**（要 await）。
- 裸 POST 的多回合：第 N 回合 `params.inputResponses = {key: {"action": "accept", "content": {...}}}`、`params.requestState = token`；
  `tools/call` 必帶 `mcp-name` header（否則 -32020），`_meta` 要含 `clientCapabilities`（否則 -32602 missing envelope key）。
- SDK：`Client(mcp, elicitation_handler=handler)` 自動跑完多回合（上限 `input_required_max_rounds=10`），handler 簽名
  `(message, response_type, params, ctx)`、回 `ElicitResult(action="accept", content=response_type(**fields))`。
- 工具簽名的 `ctx` **一定要標 `ctx: Context`**，不標會變成 schema 裡的必填參數（寫在函式工廠裡更容易漏）。

### 常見 MCP 服務（mcp-servers，2026-08-20 實測）

- `Client({"mcpServers": {...}})` 接 uvx 的 `mcp-server-time`／`mcp-server-fetch`（SDK v1 老伺服器）→ 協商到 `2025-11-25`；
  多伺服器工具自動加 `<name>_` 前綴、單一伺服器不加。老伺服器收到 `server/discover` 探測會在 stderr 噴一串 pydantic
  validation WARNING 然後 client 退回握手協定——正常。首次 uvx 安裝多花幾十秒。
- 公開遠端：`https://mcp.deepwiki.com/mcp`（2025-11-25）、`https://mcp.context7.com/mcp`（**已是 2026-07-28**）。
- `hub.mount(create_proxy(cfg), namespace=...)`：proxy 預設鏡像前端協定時代；新協定客戶端 → proxy 用新協定敲老 stdio 伺服器
  → `Received request before initialization was complete`、工具消失。**老伺服器要 `create_proxy(cfg, mode="legacy")`**。
- 工具結果沒有 structuredContent 時 `.data` 是 None 或 `Root(content=...)`，用 `result.content[0].text`。
- 本機 npx filesystem 伺服器 OK（14 個工具）；molab 有沒有 node 不確定 → notebook 用 `shutil.which("npx")` 優雅跳過。
- 設定檔的 `tools` 改造區塊（rename／hide 參數）只有 FastMCP Client／`create_proxy` 認得，Claude Desktop 不認得。
- 生態系表查證來源（2026-08-20）：modelcontextprotocol/servers README（維護中 7 個：time/fetch/git 走 uvx、
  filesystem/memory/sequentialthinking/everything 走 npx；GitHub→github/github-mcp-server、Slack／PostgreSQL／SQLite／Redis／
  Puppeteer／Brave 等已封存）、各家 README、對遠端網址發 ping 看 200/401＋`WWW-Authenticate`。換日期重驗時照這套。

### 4.0 專屬功能（fastmcp4-features）

- `fastmcp-tasks==4.0.0b1` + `TasksExtension()` + `@mcp.tool(task=True)`（必須 async）：新協定 client `call_tool` 表面一樣，
  線路是 `tools/call` → 多次 `tasks/get` → 完成；`mode="legacy"` 同步跑。裸 POST：`params.task = {"ttl": 60000}` 立刻回
  `{taskId, status: "working", pollIntervalMs: 5000}`，`tasks/get {taskId}` 回 `statusMessage`（＝`Progress.set_message`）直到
  `status: "completed"` 內嵌 result；`tasks/result` 在 b1 是 Method not found。client 的 `progress_handler` 在兩種模式都沒收到更新。
- `FastMCP(cache_ttl=300, cache_scope="public")` + `Client(url, cache=True)`：三次 `list_tools` 伺服器只收到一次；
  `tools/list` result 多 `ttlMs`／`cacheScope` 欄位。
- `Annotated[str, Field(json_schema_extra={"x-mcp-header": "City"})]` → 請求帶 `mcp-param-city` header；中文值會被編成
  `=?base64?...?=`（RFC 2047 式）。
- `@mcp.completion` 回傳物件直接 `.values`（不是 `.completion.values`）。
- `ServerExtension`：identifier 必須 `vendor/name` 反向 DNS；`settings()` 出現在 `capabilities.extensions`；
  自訂方法用裸 POST（`mcp-method: callCounter/get`＋完整 `_meta`）最簡單。
- 資源模板路徑安全：`docs://{path}` 對 `../`、絕對路徑、`%00` 回 not found，handler 不會被叫；單段 `{path}` 不吃 `/`。
- `BM25SearchTransform()` 後 `list_tools` 只剩 `search_tools`／`call_tool`，隱藏工具仍可直接呼叫。
- **`x-mcp-header` 參數：client 必須先 `list_tools()` 看過 schema 才會把參數鏡射成 header**；直接 `call_tool` 會被伺服器拒
  `Mcp-Param-City header is missing but the request body's 'city' argument is present`。
- extension 在 `intercept_tool_call` 短路改寫結果要回 `fastmcp.tools.ToolResult(structured_content=...)`；只回 `CallToolResult(content=...)`
  會被客戶端以「有 output schema 卻沒 structured content」拒絕。
- `{path*}` 萬用字元下 `a/../b` 會被 client 端正規化成 `a/b` 放行，要示範編碼穿越用 `%2e%2e/x`。
- f-string 巢狀同種引號需 Python 3.12；notebook `requires-python >=3.11` 時先把片段算成變數再塞進 `mo.md`。

### 認證（fastmcp4-auth）

- `StaticTokenVerifier(tokens={token: {"client_id", "scopes"}})`；不帶 token → 401 `WWW-Authenticate: Bearer`；
  `require_scopes("admin")` 的工具對沒 scope 的人**隱形**（list 看不到、呼叫回 `Unknown tool`）。
- `UserSession` 在有 token 的 HTTP 連線才能用；in-memory `Client(mcp)` 無身分 → ToolError（訊息會提示改用 `SessionId`）。
- `RSAKeyPair.generate()` + `create_token(subject, issuer, audience, scopes, expires_in_seconds)` 本機簽 JWT；
  `JWTVerifier(public_key=kp.public_key, issuer, audience)`；壞 token 一律 401 `invalid_token`，原因只在 log。
- `InMemoryOAuthProvider(base_url=...)` 預設 **DCR 關閉**（metadata 沒 `registration_endpoint`）→
  `client_registration_options=ClientRegistrationOptions(enabled=True, valid_scopes=[...], default_scopes=[...])`；
  DCR body 帶 `"scope": "read write"` 否則 authorize 回 `invalid_scope`。授權碼流程端點：`/.well-known/oauth-protected-resource/mcp`
  → `/.well-known/oauth-authorization-server` → `/register` → `/authorize`（302 撿 code）→ `/token`（PKCE S256）。
- SDK `OAuth` 無瀏覽器：子類別覆寫 `redirect_handler`（httpx 敲 authorize 撿 302）與 `callback_handler`
  （**必須回 `mcp.shared.auth.AuthorizationCodeResult`**，回 tuple 會 `'tuple' object has no attribute 'state'`）。
- 本機 `python` 指令不存在，page-fill 要用 `python3`（用 `python` 會靜默不更新）。

## 六門主線課補折疊解答（2026-08-20，spike：`_spikes/spike_solutions.py`）

- `resources/read` 裸 POST 的 `mcp-name` header **必須等於 URI**（不是 `mcp-uri`；缺了回 `-32020 … does not match the request body's 'uri' parameter`）；`tools/list` 不帶 `mcp-name`。
- structured output：`["string","null"]` union 型別在某上游（OpenRouter）會讓約束解碼卡住吐滿 4096 token（`finish_reason=length`）——
  驗收一律看 `finish_reason`；非 required 的欄位模型照樣填 placeholder（`未提供`、`generated@example.com`）。
- nemotron-3.5-lightning 即使 `max_tokens=4096` 偶爾仍把思考漏進 `content`（`Here's a thinking process:` 開頭），關鍵字評測會誤判 ✅。
- rag-zh 的 7 題評測 **top_k=1 也 7/7**（每題只對應一節）；要看 top_k 的差別得用跨節題（「週二＋停車」k=3 才撈到營業時間）。
  門檻掃描：範圍內 top-1 最低 0.46、範圍外最高 0.37 → 0.40–0.45 零誤判、0.5 會誤殺帶狗題。
- nemotron-3-embed-1b 同主題 0.47–0.63／離題 0.53–0.58——分數尺度綁模型，換 embedding 模型門檻要重量；2048 維查 1024 維 collection 直接 `ValueError: shapes not aligned`。
- litellm-tools 的工具參數不能叫 `from`（Python 關鍵字）；錯誤餵回去後 lightning 不重試、誠實說只支援台北高雄。
- rag-mcp-agent：拿掉 system prompt「先用工具查手冊」模型**仍會查**（docstring 的「回答任何…前都應先呼叫」在撐）；`mcp.instructions` 在自寫迴圈裡其實沒送給模型。
- shell：`pgrep -f "<字串>"` 在 until-loop 裡會匹配到自己的包裝命令永遠不結束，pattern 要精確到 `bin/python3 <script>`。
