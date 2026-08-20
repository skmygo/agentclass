# fastmcp 建課筆記

2026-08-20 以 make-lesson skill 建課（skill 改版後的端到端驗證回合；新主題 ai-engineering 首課）。

## 軌道決策：為什麼不在瀏覽器跑真的 fastmcp

Pyodide spike 實測（plain Pyodide 0.27.2 + micropip）：

- `micropip.install("fastmcp")` 直接失敗：`watchfiles`（Rust 擴充）無純 Python wheel。
- mock 掉 watchfiles 後，撞第二關：依賴鏈精確 pin `pydantic-core==2.48.0`，
  而 pydantic-core 只有 Pyodide 內建版本可用（版本對不上）。
- 結論：**server 框架類套件（fastmcp / mcp SDK）上不了 Pyodide**，且 hack 鏈太深不宜入課。

改採「迷你重現」設計：零依賴、純標準函式庫重現 @tool（inspect→JSON Schema）與
tools/list、tools/call 分發器；真 FastMCP 程式碼放左頁與 nb 的 md code block（不執行）。
副作用是優點：不裝 wheel，冒煙 13.8s 就緒（sklearn 課約 20s）。

## 版本事實（2026-08-20 查證）

- PyPI 穩定版 3.4.7（2026-08-10）；4.0 是 beta，最新 **4.0.0b3**（2026-08-14），無 4.0.0 final。
- 專案已由 jlowin 個人 repo 移到 **PrefectHQ/fastmcp**。
- 4.0 重點（官方 whats-new）：sessionless 協定上的有狀態應用——UserSession（
  `await session.get/set`、自動注入、不進 schema、綁認證身分）、多輪互動工具
  （InputRequiredResult）、背景任務（fastmcp-tasks）、identity assertion、新舊協定並存；
  移除 `ctx.sample()` / `ctx.list_roots()`。
- 頁面所有 4.0 敘述與 UserSession 範例碼均出自官方 whats-new 頁，非記憶杜撰。

## 本課特殊點

- 全課只有 1 張 matplotlib 圖（4️⃣ 的 session 長條圖）——刻意保留它，
  因為右欄就緒偵測與冒煙測試都靠 img/canvas 計數（READY_FIGURES=1、MIN_FIGURES=1）。
- 跨 cell 註冊表（TOOLS dict）靠 `tool_names` 變數建立資料依賴邊，
  確保 marimo 執行順序（mutation 本身不建邊）。

## 2026-08-20 加開實戰軌道（真 fastmcp 4 + NVIDIA NIM）

瀏覽器跑真 fastmcp 仍是死路（上面的 spike 結論不變）；改加 **molab 實戰軌道**
`fastmcp_gpu.py`（檔名 `_gpu` 只是管線慣例，本課**不需要 GPU**，molab 免費 CPU 可全程跑）。

實測驗證過的事實（全部先在本機 CPython 跑通才寫進課）：

- **in-memory transport**：`Client(mcp)` 直連 server 實例，list_tools / call_tool /
  pydantic 擋缺參數，全部正常。`Tool.inputSchema` 已 deprecated，用 `input_schema`。
- **UserSession 需要認證身分**，未認證連線會 ToolError。未認證的跨請求狀態走
  `mcp.add_provider(SessionProvider())` ＋ 工具參數 `session_id: SessionId` ＋
  `get_session(session_id)`——create_session 發 uuid 鑰匙、亂猜的鑰匙被拒，
  跟瀏覽器迷你版的置物櫃演示完全同構（4️⃣ 的教學呼應成立）。
- **prerelease 解析**：`fastmcp==4.0.0b3` 的傳依賴 `fastmcp-slim==4.0.0b3` 會卡
  uv 的 prerelease 檢查 → PEP 723 裡**兩個都直接釘**就不用任何 flag。
- **NIM tool calling 模型實測**：`openai/gpt-oss-120b` 乾淨兩跳完成
  （search_menu("茶") → place_order）；`meta/llama-3.3-70b-instruct` 會用爛關鍵字
  （搜「菜」）還幻覺品名——課程預設 gpt-oss-120b。
- **工具錯誤要回饋給 LLM**（tool role message 帶「錯誤：…」）讓它自我修正，
  不能讓 ToolError 直接炸掉 loop——這本身做成延伸挑戰 2。
- **金鑰安全**：notebook 用 `mo.ui.text(kind="password")` ＋ `NVIDIA_API_KEY` env
  fallback；實測帶 env 匯出 html，key 不會進產物。repo/dist 全文掃描零外洩。

## 這回合抓到的 scaffold bug（已修進 skill）

- 模板頂部說明註解含字面 `[GPU]` → 剝除邏輯把 `<head>`＋基礎 CSS 整段吃掉。
  已改措辭＋scaffold 加生成後自檢（缺 </head>/<style>/nb-status/… 直接 exit 1）。
- sed 代換 `LESSON_ID` 誤傷 `NEXT_LESSON_ID` → 模板改名 `NEXT_ID`。
