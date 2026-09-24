# genai-mcp-fastmcp（補充 D：MCP 新版協定與 FastMCP 4）NOTES

## 定位與分工（別跟誰重複）

- 延伸主線 `genai-agents` 的 MCP 一節（那課只講「MCP 是 AI 的 USB、M×N → M+N」）。
- llm-apps 的 `fastmcp4`／`fastmcp4-auth`／`fastmcp4-state`／`fastmcp4-features`／`mcp-servers` 是**外部軌動手寫 server** 的深入版（釘 4.0.0b1）。
  本課不教寫 server，只給三樣東西：**規格版本地圖**、**線路上的真相**（真實封包逐發拆解＋兩副本實驗＋手刻請求），
  **FastMCP 4 功能地圖**（問題 → 功能 → 4.0.8 實測證據），每張卡連回 llm-apps 對應課。
- 軌道：純瀏覽器 app 模式（fastmcp 進不了 Pyodide，所以伺服器不在瀏覽器裡跑——**封包是錄好的**，
  圖表、封包解析、兩副本分派模擬、請求組裝都是瀏覽器現場算）。觀看者零安裝、零 key、零服務。

## 素材來源（全部實測，2026-09-24）

- 環境：`fastmcp==4.0.8`、`fastmcp-tasks==4.0.8`、`mcp==2.2.0`（fastmcp 4.0.8 帶進來的 SDK）、Python 3.12.13、Linux。
  **沒有打任何 LLM**、不需要 key、不連外（除了 uv 第一次裝套件）。
- spike：`content/genai-intro/_spikes/spike_genai_mcp_fastmcp.py`（PEP 723）
  - `uv run --script content/genai-intro/_spikes/spike_genai_mcp_fastmcp.py --out /tmp/wire.json`：只錄、寫 JSON
  - `uv run --script …/spike_genai_mcp_fastmcp.py --inject`：重錄並寫回 `lesson.py` 的 `WIRE_JSON` 與
    `page_content.py` 的 `const ERAS = /*ERAS_BEGIN*/…/*ERAS_END*/`，之後跑 page-fill
  - env：`SPIKE_PORT_BASE`（預設 9140，用 base..base+9 十個 port，只綁 127.0.0.1）；任何一個被占用就直接停
    （例如自己的預覽 server 還開在 9140）。
- 錄了什麼：五個協定年代各做一次「列工具＋呼叫 add(2,3)」（2026-07-28／2025-11-25 用 FastMCP Client；
  2025-06-18／2025-03-26 用照規格手寫的 httpx；2024-11-05 用手寫 HTTP+SSE 客戶端打 `http_app(transport="sse")`）、
  伺服器反問使用者（新 MRTR／舊 server→client request）、背景任務、x-mcp-header＋快取、
  手刻 tools/call 四旋鈕 4×3×3×5＝180 組合、兩副本＋round-robin／sticky 負載平衡器、功能地圖 19 張卡的證據、
  新協定連線上 `ctx.elicit()`／`ctx.sample()` 的真實錯誤。
- 規格與版本資訊來源（WebFetch／gh api，2026-09-24）：modelcontextprotocol.io 的
  `/specification/versioning`、各版 `/changelog`、`/specification/2026-07-28/deprecated`、`server/discover`、
  `basic/transports/streamable-http`；FastMCP GitHub releases v4.0.0b1–v4.0.8、gofastmcp.com What's New；PyPI 發布時間。

## 實測數字（課文引用的）

| 事實 | 值 | 會不會變 |
|---|---|---|
| 同一動作的 HTTP 請求數 | 2026-07-28：3；2025-11-25：6；2025-06-18／03-26：5（手寫客戶端沒開 GET）；2024-11-05：5 | 決定性 |
| body 總位元組 | 新 2,110 vs 舊 1,351（新協定反而大） | 決定性（session id 長度固定）；notebook 從資料算，頁面只寫「比較大」 |
| 兩副本 round-robin | 新：A/B/A 全 200；舊：第 2 發落 B → `404 {"code":-32600,"message":"Session not found"}`，client 拋 `MCPError: Session not found` | 分派決定性；GET 與 initialized 的先後在 trail 裡偶爾對調 |
| sticky 舊協定 | 6 發全落 A、成功 | 決定性 |
| 手刻 180 組合 | 只有 1 組 200；-32600 Missing session ID ×90、-32020 版本不符 ×36、-32602 ×18＋18、-32020 method ×12、-32020 name ×4、-32022 ×1 | 決定性 |
| GET／DELETE 帶新協定 header | 405、`Allow: POST` | 決定性 |
| 背景任務 | tools/call 回 taskId → tasks/get 輪詢 7 次左右 → completed，約 1.3 秒 | **輪詢次數會變**（頁面寫「輪幾次看當下」） |
| 快取 | `Client(cache=True)` 呼叫 3 次 list_tools → 線路只有 1 發 tools/list，`ttlMs: 300000` | 決定性 |
| 模擬（3 副本、round-robin） | 舊協定整段成功 ≈0.4%（4000 session 蒙地卡羅，seed=7） | 頁面不寫點值，notebook 現場算 |

檢查順序（4️⃣ 與頁面 s4 表）是**從 180 組合回推**的：版本 header 分流 → `_meta` 完整 → header 版本＝`_meta` 版本
→ Mcp-Method → Mcp-Name → 版本支援。規格沒規定順序，換 SDK 版本要重看。

## 踩到的坑

- **注入標記別寫進 docstring**：第一版 inject 的 regex 用 `/*ERAS_BEGIN*/…/*ERAS_END*/`，結果先匹配到
  page_content.py 檔頭 docstring 裡描述標記的那句，把 16KB JSON 塞進了說明文字、SCRIPT 反而空的
  （`const ERAS = ;`）。現在 regex 錨定 `const ERAS = /*ERAS_BEGIN*/`，docstring 也改寫成不含標記原文。
- **Python 3.14 收尾 double free**：uvicorn 背景執行緒＋直譯器 finalize 偶發 `double free or corruption`。
  spike 釘 `requires-python >=3.12,<3.14`，結尾 `os._exit(0)`。
- **FastMCP elicitation_handler 的回傳**：`response_type` 是從 schema 生成的型別；用 `mcp.types.ElicitResult(content=response_type(...))`
  包起來回傳會驗證失敗（`5 validation errors for ElicitResult`，content 被當成巢狀物件）。直接回 `response_type(**fields)`
  （隱含 accept；官方範例若要包就用 `fastmcp.client.elicitation.ElicitResult`），
  fields 取 `params.requested_schema["properties"]` 的 key（新協定守衛模式的 schema 是我們自己的 `ok`，
  舊協定 `ctx.elicit(response_type=bool)` 是 `value`）。
- **同一個工具要同時服務兩個年代**：`ctx.request_context.protocol_version == "2026-07-28"` 分支——
  新協定回 `InputRequiredResult`、舊協定用 `ctx.elicit()`。在新協定上呼叫 `ctx.elicit()` 的實測錯誤：
  `elicitation via server-initiated requests is unavailable on 2026-07-28 connections.`（quiz Q3 用這句）。
- **FastMCP 新協定客戶端沒先 list_tools 就 call_tool，會在 call 之後補一發 tools/list**（拿 output schema）；
  所以 hero 的動作固定是「先列工具再呼叫」，兩個年代才可比。
- **封包序號別寫死在文案**：兩副本 trail 的 GET 與 initialized 先後偶爾對調；notebook 裡「⑤ 的第 N 發」
  這類句子全部從 WIRE 算出來。頁面上只寫決定性的事實。
- marimo session JSON 的圖在 `application/vnd.marimo+mimebundle`（字串裡才有 `image/png`），
  數圖要搜整個 output 的 JSON 字串，不能只看 `data` 的 key。
- ruff：本機沒有全域 ruff，用 `uvx ruff check`。FastMCP 的依賴注入寫法 `progress: Progress = Progress()`
  會中 B008（加 noqa）；async 函式裡用同步 httpx 會中 ASYNC210（改 AsyncClient）。

## 換版本／重驗時要重看的句子

1. `uv run --script …spike_genai_mcp_fastmcp.py --inject` → page-fill → `marimo export html`（3 張圖、0 error）
   → mini-dist＋smoke-test。notebook 的數字與序號會自己跟上。
2. **頁面靜態文字**（page_content.py）要人工對：
   - s2 的 tools/call 原文（clientInfo 目前是 `{"name":"mcp","version":"0.1.0"}`、`logLevel: debug`、`progressToken`）——SDK 一升版就可能變。
   - s3 兩副本表格與 quiz Q1 的說法（A:initialize → 第 2 發落 B → 404）。
   - s4 檢查順序表與 quiz Q2 的錯誤原文。
   - s5 的「4.0.0b1 → 正式版」對照框、quiz Q3 的錯誤原文、Q4 的「30 個工具 → 只看到 2 個」。
   - hero 的 INFO 說明（例如「FastMCP 客戶端多開一條 GET 長連線」是 4.0.8 legacy client 的行為）。
   - s1 版本表：規格若出新版（查 `/specification/versioning` 的 current），表格、1️⃣ 的矩陣圖與 CHANGELOG 常數都要加一欄。
3. 若 FastMCP 拿掉對 2024-11-05／HTTP+SSE 的支援（`http_app(transport="sse")`），hero 第一個年代就錄不到了，要改成只錄四個年代並改文案。
