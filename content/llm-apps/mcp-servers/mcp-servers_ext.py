# 常見 MCP 服務：接上別人的伺服器，再合成一台
# 不需要 GPU——molab 免費 CPU 環境即可全程執行。本課需要網路：uvx 會下載官方伺服器套件、
# 並連到兩台公開的遠端 MCP 伺服器（DeepWiki、Context7）。
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "marimo",
#     "fastmcp==4.0.0b1",
#     "fastmcp-slim==4.0.0b1",
#     "httpx",
#     "uvicorn",
# ]
# ///
import marimo

__generated_with = "0.23.16"
app = marimo.App(width="medium", app_title="常見 MCP 服務：接上別人的伺服器，再合成一台")


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    # 🧩 常見 MCP 服務：接上別人的伺服器，再合成一台

    前面每一堂 FastMCP 課都在**自己蓋伺服器**。但 MCP 真正的價值是生態系：查時區、抓網頁、
    讀檔案、操作 git、翻最新文件、開瀏覽器……這些伺服器別人已經寫好、上千個客戶端都在用。
    這堂課換個方向——**接上別人蓋好的**，最後把它們跟你自己的工具合成一台，給 Claude 用。

    你會親眼看到：

    1. 生態系地圖：官方參考伺服器有哪些、哪些已經封存搬家、熱門第三方要不要 token（2026-08 查證）
    2. **stdio**：用 `uvx` 把官方 `mcp-server-time` 當子行程跑起來、呼叫它
    3. 多伺服器設定檔（就是 Claude Desktop／Cursor 用的 `mcp.json` 格式）：工具自動加前綴
    4. **遠端 HTTP 伺服器**：DeepWiki 與 Context7——一台還在舊協定、一台已經是 2026-07-28 新協定
    5. `npx` 類伺服器（filesystem）：有 node 才跑，沒有就告訴你在自己電腦怎麼跑
    6. **合成一台**：自己的工具＋time＋Context7 mount 成一台 HTTP hub（stdio → HTTP 橋接）
    7. 接給 Claude Code／Claude Desktop／Cursor 的設定片段與 CLI

    本課用 `fastmcp==4.0.0b1`（與第 3 課相同）。從第一格往下全部執行即可；
    **首次執行 2️⃣ 時 `uvx` 要下載伺服器套件，多等 10–40 秒是正常的**。
    """
    )
    return


@app.cell
def _():
    import shutil
    import socket
    import tempfile
    import threading
    import time
    from pathlib import Path

    import marimo as mo
    import uvicorn
    from fastmcp import Client, FastMCP
    from fastmcp.server import create_proxy
    return Client, FastMCP, Path, create_proxy, mo, shutil, socket, tempfile, threading, time, uvicorn


@app.cell
def _():
    def text_of(result):
        """工具結果的文字：這些老伺服器多半沒有 structuredContent，`.data` 會是 None 或一個包裝物件，
        直接取第一個文字區塊最保險。"""
        if result.content:
            return result.content[0].text
        return result.data
    return (text_of,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 1️⃣ 生態系地圖（2026-08 查證）

    先有個全貌。MCP 伺服器分兩種接法：

    - **stdio**：客戶端把伺服器當**子行程**拉起來，用 stdin／stdout 的管線講 JSON-RPC。
      安裝即執行（`uvx …`、`npx -y …`），跑在你自己的機器上。
    - **HTTP**：伺服器掛在網路上，你只要一個網址。多半要 OAuth（補充課 A 教過那一套 401 → discovery → token 的流程）。

    ### 官方參考伺服器（`modelcontextprotocol/servers`，目前維護中的 7 個）

    | 名稱 | 做什麼 | 怎麼跑 |
    |---|---|---|
    | `time` | 查時區、換算時間 | `uvx mcp-server-time`（Python） |
    | `fetch` | 抓網頁、轉成 markdown 給模型讀 | `uvx mcp-server-fetch`（Python） |
    | `git` | 讀／搜尋／操作 git repo | `uvx mcp-server-git --repository <path>`（Python） |
    | `filesystem` | 受控目錄內的檔案讀寫 | `npx -y @modelcontextprotocol/server-filesystem <dir>`（Node） |
    | `memory` | 知識圖譜式的長期記憶 | `npx -y @modelcontextprotocol/server-memory`（Node） |
    | `sequentialthinking` | 分步推理的思考紀錄 | `npx -y @modelcontextprotocol/server-sequential-thinking`（Node） |
    | `everything` | 測試用：所有協定功能都有 | `npx -y @modelcontextprotocol/server-everything`（Node） |

    已經**封存搬到 `servers-archived`** 的：GitHub（改由 GitHub 官方維護）、GitLab、Slack（Zencoder 接手）、
    PostgreSQL、SQLite、Redis、Google Drive／Maps、Brave Search（改官方版）、Puppeteer、Sentry 等——
    網路上很多教學還在教 `@modelcontextprotocol/server-github`，那個已經不更新了。

    ### 熱門第三方（本課只實際連前兩台）

    | 名稱 | 做什麼 | 接法 | 要 token 嗎 |
    |---|---|---|---|
    | **DeepWiki** | 問任何公開 GitHub repo 的結構與問題 | HTTP `https://mcp.deepwiki.com/mcp` | 不用 |
    | **Context7** | 查各套件**最新版**文件，解決模型記錯 API | HTTP `https://mcp.context7.com/mcp` | 不用（有 key 額度較高） |
    | Cloudflare Docs | 查 Cloudflare 文件 | HTTP `https://docs.mcp.cloudflare.com/mcp` | 不用 |
    | GitHub 官方 | repo／issue／PR／Actions | HTTP `https://api.githubcopilot.com/mcp/` 或 docker | OAuth 或 PAT |
    | Playwright | 操作真的瀏覽器：導航、點擊、填表 | `npx @playwright/mcp@latest`（stdio） | 不用 |
    | Notion | 讀寫 Notion 頁面 | HTTP `https://mcp.notion.com/mcp` | OAuth |
    | Linear | issue 追蹤 | HTTP `https://mcp.linear.app/mcp` | OAuth |
    | Sentry | 錯誤追蹤 | HTTP `https://mcp.sentry.dev/mcp` | OAuth |
    | Stripe | 金流 | HTTP `https://mcp.stripe.com` | OAuth |
    | Firecrawl | 網站爬取 | `npx -y firecrawl-mcp`（stdio） | API key |
    | Supabase | 資料庫／專案管理 | `npx -y @supabase/mcp-server-supabase`（stdio） | PAT |

    查證方式：2026-08-20 直接對每個 HTTP 網址發一個 `ping`——回 `200` 的不用 token；回 `401` 的
    `WWW-Authenticate` header 都帶著 `resource_metadata=…/.well-known/oauth-protected-resource`，
    也就是補充課 A 那套標準 OAuth 發現流程。完整清單在 [MCP Registry](https://registry.modelcontextprotocol.io)。

    一個安全常識先講：**stdio 伺服器＝在你的機器上執行別人的程式**。只裝信得過的來源、
    filesystem 一定要限制目錄、API key 用 `env` 傳不要寫進設定檔、遠端伺服器看清楚它要什麼權限。
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 2️⃣ stdio：把官方 `mcp-server-time` 當子行程跑起來

    設定長這樣——`command` 是執行檔、`args` 是參數。`Client(設定)` 會**自己把子行程拉起來**、
    用 stdin／stdout 講 MCP、用完關掉。你不用開終端機、不用管 port。

    兩件 stdio 特有的事：

    - **環境變數不會全部繼承**。子行程只拿到一小份白名單（POSIX：`HOME`、`PATH`、`USER`、`SHELL`、`TERM`、`LOGNAME`）。
      API key 這類東西要在設定裡用 `"env": {"API_KEY": "..."}` 明傳，不然伺服器看不到。
    - **首次要安裝**。`uvx` 第一次跑 `mcp-server-time` 會先下載套件（10–40 秒），之後有快取就秒開。

    看輸出的 `protocol_version`：這些官方參考伺服器是用 MCP Python SDK **v1** 寫的，只會握手時代的協定
    `2025-11-25`。FastMCP 4 的 client 會先用新協定探一次（`server/discover`），老伺服器不認得、
    在 stderr 印一串 pydantic validation 警告，client 就自動退回握手協定——**那串警告是正常的**，
    molab 可能會把它顯示在這格下面，不是錯誤。
    """
    )
    return


@app.cell
async def _(Client, mo, text_of, time):
    TIME_SERVER = {"command": "uvx", "args": ["mcp-server-time"]}

    _t0 = time.perf_counter()
    async with Client({"mcpServers": {"time": TIME_SERVER}}) as _c:
        time_protocol = _c.protocol_version
        time_tools = await _c.list_tools()
        _now = text_of(await _c.call_tool("get_current_time", {"timezone": "Asia/Taipei"}))
        _conv = text_of(await _c.call_tool(
            "convert_time", {"source_timezone": "Asia/Taipei", "time": "09:00", "target_timezone": "America/New_York"}))
    time_connect_sec = round(time.perf_counter() - _t0, 1)

    mo.vstack([
        mo.md(f"連上 `mcp-server-time`（含子行程啟動）花了 **{time_connect_sec} 秒**，協定版本 **`{time_protocol}`**。"
              f"它有 {len(time_tools)} 個工具："),
        mo.ui.table([{"tool": t.name, "說明": (t.description or "").splitlines()[0],
                      "參數": ", ".join(t.input_schema.get("properties", {}))} for t in time_tools], selection=None),
        mo.md(f"`get_current_time(timezone=\"Asia/Taipei\")` →\n\n```json\n{_now}\n```\n\n"
              f"`convert_time(Asia/Taipei 09:00 → America/New_York)` →\n\n```json\n{_conv}\n```"),
    ])
    return TIME_SERVER, time_connect_sec, time_protocol, time_tools


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 3️⃣ 多伺服器設定檔：這就是 `mcp.json`

    把多台伺服器放進同一個 `mcpServers` dict——**這個格式就是 Claude Desktop、Cursor、VS Code 的設定檔格式**，
    你在這裡寫好的 dict，原封不動貼進 `claude_desktop_config.json` 就能用。

    多台時 FastMCP 會自動幫工具加**伺服器名前綴**避免撞名：`time` 的 `get_current_time` 變成
    `time_get_current_time`、`fetch` 的 `fetch` 變成 `fetch_fetch`。只有一台時（上一格）就不加。

    `mcp-server-fetch` 是「幫模型讀網頁」的標準工具：抓網址、去掉 HTML 雜訊轉成 markdown、`max_length` 控制長度。
    這裡抓 FastMCP 官方文件的索引當示範。
    """
    )
    return


@app.cell
async def _(Client, TIME_SERVER, mo, text_of):
    SERVERS = {
        "mcpServers": {
            "time": TIME_SERVER,
            "fetch": {"command": "uvx", "args": ["mcp-server-fetch"]},
        }
    }

    async with Client(SERVERS) as _c:
        multi_tool_names = [t.name for t in await _c.list_tools()]
        try:
            _page = text_of(await _c.call_tool("fetch_fetch", {"url": "https://gofastmcp.com/llms.txt", "max_length": 400}))
            _fetch_out = mo.md(f"`fetch_fetch(url=\"https://gofastmcp.com/llms.txt\", max_length=400)` →\n\n```\n{_page}\n```")
        except Exception as _e:  # noqa: BLE001  真網路：抓不到就說明，不要 Traceback
            _fetch_out = mo.callout(mo.md(f"`fetch_fetch` 這次失敗了（網路或對方網站暫時不可用）：`{str(_e)[:160]}`。重新執行這格再試。"), kind="warn")

    mo.vstack([
        mo.md(f"兩台一起連，工具清單自動加前綴：`{multi_tool_names}`"),
        _fetch_out,
    ])
    return SERVERS, multi_tool_names


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 4️⃣ 遠端 HTTP 伺服器：一個網址就好

    不用裝任何東西，`Client("https://…/mcp")`。兩台公開、不用 token 的：

    - **DeepWiki**（Cognition）：問任何公開 GitHub repo——`read_wiki_structure` 列章節、`read_wiki_contents` 讀內容、`ask_question` 直接問。
    - **Context7**（Upstash）：查套件**最新版**文件——先 `resolve-library-id` 把「fastmcp」對應成 `/prefecthq/fastmcp`，
      再 `query-docs` 用自然語言查。模型記錯 API 版本的老問題，就是靠這台解。

    特別看 `protocol_version`：實測 DeepWiki 還是 **`2025-11-25`**（握手協定），Context7 已經是 **`2026-07-28`**
    （第 3 課學的無狀態協定）。真實世界正處在過渡期，而 FastMCP 4 的 client 對兩者都是同一行程式碼——
    這正是 4.0「一台伺服器／一個客戶端同時服務兩個協定時代」的意義。

    遠端服務會變（改網址、加上 OAuth、換工具名），所以這格包了 try/except：失敗會顯示說明而不是整格炸掉。
    """
    )
    return


@app.cell
async def _(Client, mo, text_of, time):
    REMOTE = {
        "DeepWiki": "https://mcp.deepwiki.com/mcp",
        "Context7": "https://mcp.context7.com/mcp",
    }
    remote_rows = []
    _demos = []
    for _name, _url in REMOTE.items():
        _t0 = time.perf_counter()
        try:
            async with Client(_url) as _c:
                _tools = [t.name for t in await _c.list_tools()]
                remote_rows.append({"伺服器": _name, "網址": _url, "protocol_version": _c.protocol_version,
                                    "工具": ", ".join(_tools), "連線秒數": round(time.perf_counter() - _t0, 1)})
                if _name == "DeepWiki":
                    _r = text_of(await _c.call_tool("read_wiki_structure", {"repoName": "PrefectHQ/fastmcp"}))
                    _demos.append(mo.md(f"**DeepWiki** `read_wiki_structure(repoName=\"PrefectHQ/fastmcp\")` →\n\n```\n{_r[:500]}\n…\n```"))
                else:
                    _lib = text_of(await _c.call_tool("resolve-library-id", {"libraryName": "fastmcp", "query": "mount a proxy with namespace"}))
                    _doc = text_of(await _c.call_tool("query-docs", {"libraryId": "/prefecthq/fastmcp", "query": "mount a proxy with namespace"}))
                    _demos.append(mo.md(f"**Context7** `resolve-library-id(libraryName=\"fastmcp\", …)` →\n\n```\n{_lib[:300]}\n…\n```\n\n"
                                        f"`query-docs(libraryId=\"/prefecthq/fastmcp\", query=\"mount a proxy with namespace\")` →\n\n```\n{_doc[:600]}\n…\n```"))
        except Exception as _e:  # noqa: BLE001  遠端服務可能變動
            remote_rows.append({"伺服器": _name, "網址": _url, "protocol_version": "—", "工具": f"連不上：{str(_e)[:80]}",
                                "連線秒數": round(time.perf_counter() - _t0, 1)})
            _demos.append(mo.callout(mo.md(f"**{_name}** 這次連不上（遠端服務可能改版或暫停）。重新執行這格，或查它的官網看最新網址。"), kind="warn"))

    mo.vstack([mo.ui.table(remote_rows, selection=None), *_demos])
    return REMOTE, remote_rows


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 5️⃣ `npx` 類伺服器：filesystem

    Node 生態的伺服器用 `npx -y <套件>` 啟動，機制跟 `uvx` 一模一樣（子行程＋stdio）。
    最常用的是官方 **filesystem**：讓模型在**你指定的目錄內**讀寫檔案——目錄是用啟動參數鎖死的，
    模型碰不到外面。

    這格先檢查環境有沒有 `npx`：有就開一個暫存目錄、寫一個檔、讓伺服器讀回來；沒有（molab 的免費環境不一定有 Node）
    就顯示在自己電腦上怎麼跑。
    """
    )
    return


@app.cell
async def _(Client, Path, mo, shutil, tempfile, text_of):
    FS_CMD = ["npx", "-y", "@modelcontextprotocol/server-filesystem"]
    if shutil.which("npx") is None:
        fs_tool_names = []
        _out = mo.callout(mo.md(
            "這個環境沒有 `npx`（Node.js），跳過。在自己電腦上（裝好 Node）把這格的程式碼原樣跑即可：\n\n"
            "```python\ncfg = {\"mcpServers\": {\"fs\": {\"command\": \"npx\", \"args\": [\"-y\", \"@modelcontextprotocol/server-filesystem\", \"/你允許的目錄\"]}}}\n"
            "async with Client(cfg) as c:\n    print([t.name for t in await c.list_tools()])\n```\n\n"
            "實測（2026-08）它有 14 個工具：`read_file`、`read_text_file`、`read_media_file`、`read_multiple_files`、`write_file`、`edit_file`、"
            "`create_directory`、`list_directory`、`list_directory_with_sizes`、`directory_tree`、`move_file`、`search_files`、`get_file_info`、`list_allowed_directories`。"
        ), kind="info")
    else:
        _dir = Path(tempfile.mkdtemp())
        (_dir / "note.txt").write_text("hello from the filesystem server")
        try:
            async with Client({"mcpServers": {"fs": {"command": FS_CMD[0], "args": FS_CMD[1:] + [str(_dir)]}}}) as _c:
                fs_tool_names = [t.name for t in await _c.list_tools()]
                _read = text_of(await _c.call_tool("read_text_file", {"path": str(_dir / "note.txt")}))
                _ls = text_of(await _c.call_tool("list_directory", {"path": str(_dir)}))
            _out = mo.md(
                f"filesystem 伺服器有 **{len(fs_tool_names)} 個工具**：`{fs_tool_names}`\n\n"
                f"允許目錄：`{_dir}`\n\n`read_text_file(note.txt)` → `{_read}`\n\n`list_directory` → `{_ls}`"
            )
        except Exception as _e:  # noqa: BLE001  npx 下載失敗等
            fs_tool_names = []
            _out = mo.callout(mo.md(f"npx 啟動失敗：`{str(_e)[:160]}`（多半是網路或 Node 版本）。重新執行這格再試。"), kind="warn")
    _out
    return FS_CMD, fs_tool_names


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 6️⃣ 合成一台：自己的工具＋time＋Context7，一個網址對外

    到目前為止都是「客戶端直接連三台」。實務上更常見的是**你蓋一台 hub**，把別人的伺服器 mount 進來，
    加上自己的工具，對外只有一個網址——客戶端只要設定一次。`create_proxy(目標)` 把任何 MCP 伺服器
    （網址、設定 dict、檔案路徑）變成一個可以 mount 的代理；`namespace` 決定前綴：

    | 元件 | 沒有 namespace | `namespace="time"` |
    |---|---|---|
    | tool `get_current_time` | `get_current_time` | `time_get_current_time` |
    | prompt `p` | `p` | `time_p` |
    | resource `data://info` | `data://info` | `data://time/info` |

    **一個實測踩到的坑**：hub 對外是新協定，proxy 預設會「鏡像」客戶端的協定時代去連後端——
    新協定客戶端 → proxy 用新協定去敲 `mcp-server-time` → 老伺服器不會 → `tools/list` 失敗、工具消失。
    對只會握手協定的老伺服器要 **`create_proxy(..., mode="legacy")`** 釘住。Context7 本身就是新協定，不用釘。

    這也是 **stdio → HTTP 橋接**：`mcp-server-time` 原本只能被同一台機器的客戶端當子行程拉起來，
    經過 hub 之後，任何能連 HTTP 的遠端客戶端都用得到它。
    """
    )
    return


@app.cell
def _(FastMCP, TIME_SERVER, create_proxy, mo, socket, threading, time, uvicorn):
    hub = FastMCP("我的工具 hub", instructions="查時間用 time_*，查套件文件用 c7_*。")

    @hub.tool
    def hello(name: str) -> str:
        """打招呼（hub 自己的工具）。"""
        return f"哈囉 {name}，這裡是 hub。"

    hub.mount(create_proxy({"mcpServers": {"default": TIME_SERVER}}, mode="legacy"), namespace="time")   # 老伺服器：釘 legacy
    hub.mount(create_proxy("https://mcp.context7.com/mcp"), namespace="c7")                             # 新協定：直接 mount

    HUB_PORT = 8791
    HUB_URL = f"http://127.0.0.1:{HUB_PORT}/mcp"

    def _port_busy(port):
        with socket.socket() as _s:
            return _s.connect_ex(("127.0.0.1", port)) == 0

    if not _port_busy(HUB_PORT):
        _server = uvicorn.Server(uvicorn.Config(hub.http_app(), host="127.0.0.1", port=HUB_PORT, log_level="warning"))
        threading.Thread(target=_server.run, daemon=True).start()
        for _ in range(50):
            if _port_busy(HUB_PORT):
                break
            time.sleep(0.1)
    mo.md(f"hub 在 **`{HUB_URL}`** 聽候（{'已啟動' if _port_busy(HUB_PORT) else '⚠️ 沒起來'}）。")
    return HUB_PORT, HUB_URL, hello, hub


@app.cell
async def _(Client, HUB_URL, hello, mo, text_of):
    _ = hello
    async with Client(HUB_URL) as _c:
        hub_protocol = _c.protocol_version
        hub_tool_names = [t.name for t in await _c.list_tools()]
        _hi = text_of(await _c.call_tool("hello", {"name": "MCP"}))
        _rows = [{"呼叫": "hello(name=\"MCP\")", "來源": "hub 自己", "結果": _hi}]
        try:
            _tokyo = text_of(await _c.call_tool("time_get_current_time", {"timezone": "Asia/Tokyo"}))
            _rows.append({"呼叫": "time_get_current_time(Asia/Tokyo)", "來源": "uvx mcp-server-time（stdio，經 hub 橋接成 HTTP）", "結果": _tokyo.replace("\n", " ")[:120]})
        except Exception as _e:  # noqa: BLE001
            _rows.append({"呼叫": "time_get_current_time", "來源": "stdio", "結果": f"失敗：{str(_e)[:100]}"})
        try:
            _c7 = text_of(await _c.call_tool("c7_resolve-library-id", {"libraryName": "qdrant", "query": "python client"}))
            _rows.append({"呼叫": "c7_resolve-library-id(qdrant)", "來源": "Context7（遠端 HTTP，經 hub 轉發）", "結果": _c7.replace("\n", " ")[:120] + "…"})
        except Exception as _e:  # noqa: BLE001
            _rows.append({"呼叫": "c7_resolve-library-id", "來源": "Context7", "結果": f"失敗：{str(_e)[:100]}"})
    mo.vstack([
        mo.md(f"連到 hub：協定 **`{hub_protocol}`**，工具清單（三個來源合在一起）：`{hub_tool_names}`"),
        mo.ui.table(_rows, selection=None),
    ])
    return hub_protocol, hub_tool_names


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 7️⃣ 接給 Claude Code／Claude Desktop／Cursor

    把 6️⃣ 的 hub 存成 `hub.py`，結尾加 `mcp.run(transport="http", host="0.0.0.0", port=8000)`
    （變數名記得是 `hub`），跑起來後：

    **Claude Code**（CLI 一行）：

    ```bash
    claude mcp add --transport http hub http://localhost:8000/mcp        # 接 HTTP 的 hub
    claude mcp add time -- uvx mcp-server-time                           # 或直接接一台 stdio 伺服器
    claude mcp add playwright -- npx @playwright/mcp@latest              # 讓 Claude 操作瀏覽器
    claude mcp add weather -e API_KEY=secret -- uvx my-weather-server    # API key 用 -e 傳
    ```

    **Claude Desktop**：`claude_desktop_config.json`（macOS `~/Library/Application Support/Claude/`、
    Windows `%APPDATA%\Claude\`）——內容就是 3️⃣ 的 dict：

    ```json
    {
      "mcpServers": {
        "time":  {"command": "uvx", "args": ["mcp-server-time"]},
        "fetch": {"command": "uvx", "args": ["mcp-server-fetch"]},
        "hub":   {"url": "http://localhost:8000/mcp"}
      }
    }
    ```

    **Cursor**：專案裡的 `.cursor/mcp.json`，同一個格式。

    **FastMCP 的 CLI** 把這些再包一層：

    ```bash
    fastmcp install claude-code hub.py:hub        # 自動幫你跑 claude mcp add（含依賴）
    fastmcp install claude-desktop hub.py:hub     # 直接寫進 claude_desktop_config.json
    fastmcp install cursor hub.py:hub             # 產 .cursor/mcp.json
    fastmcp list http://localhost:8000/mcp        # 不寫程式就看一台伺服器有哪些工具
    fastmcp call http://localhost:8000/mcp time_get_current_time timezone=Asia/Taipei
    fastmcp list --command "uvx mcp-server-time"  # stdio 的也行
    ```

    接上之後，對 Claude 說「東京現在幾點」它會自己呼叫 `time_get_current_time`；說「Qdrant 的 python client
    怎麼建 collection」它會先 `c7_resolve-library-id` 再 `c7_query-docs`——你一個 agent 迴圈都沒寫。

    最後一次安全提醒：stdio 伺服器是在你機器上跑的程式，只裝信得過的；filesystem 永遠限制目錄；
    公司內部的 hub 對外開放前，掛上補充課 A 的認證（LEVEL 3 挑戰就是這個）。

    ## 🏆 延伸挑戰

    1. **LEVEL 1**：在 3️⃣ 的 `SERVERS` 加第三台官方伺服器 `git`（`uvx mcp-server-git --repository <路徑>`；
       先用 `tempfile` 開個目錄 `git init` 並 commit 一次）。重跑——多出哪些 `git_` 工具？用 `git_git_log` 讀出那個 commit。
    2. **LEVEL 2**：設定檔可以**改造工具**：在 `time` 伺服器的設定加 `"tools"` 區塊，把 `get_current_time`
       改名成 `now`、描述改成中文、`timezone` 參數預設 `Asia/Taipei` 並 `hide`——讓模型看到的是一個零參數的 `now()`。
    3. **LEVEL 3**：6️⃣ 的 hub 目前誰都能連。掛上補充課 A 的 `StaticTokenVerifier`，讓沒帶 token 的客戶端連不上、
       帶 `team-token` 的才看得到 `c7_*`。想一想：Context7 本身不要 token，你的 hub 卻要——這種「在 hub 層加門」的模式
       還能加什麼（限流、審計、把 scope 對應到不同的 namespace）？

    先自己試，卡住再展開下面的參考解答。
    帶得走：下載本檔後 `uvx marimo edit --sandbox mcp-servers_ext.py` 在自己電腦繼續玩（依賴會自動安裝）。
    補充系列到此完結——回到主線壓軸課，你會發現那台 RAG 伺服器現在可以 mount 進 hub、掛上認證、給整個團隊用。
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.accordion(
        {
            "💡 LEVEL 1 參考解答": mo.md(
                r"""
    先準備一個有 commit 的 repo，再把 `git` 加進設定（新 cell，變數名避開 `SERVERS`）：

    ```python
    import subprocess
    _repo = tempfile.mkdtemp()
    subprocess.run(["git", "init", "-q", _repo], check=True)
    Path(_repo, "README.md").write_text("hi")
    subprocess.run(["git", "-C", _repo, "add", "."], check=True)
    subprocess.run(["git", "-C", _repo, "-c", "user.email=a@b", "-c", "user.name=a", "commit", "-q", "-m", "init"], check=True)

    SERVERS_GIT = {"mcpServers": {
        **SERVERS["mcpServers"],
        "git": {"command": "uvx", "args": ["mcp-server-git", "--repository", _repo]},
    }}
    async with Client(SERVERS_GIT) as _c:
        print([t.name for t in await _c.list_tools()])
        print(text_of(await _c.call_tool("git_git_log", {"repo_path": _repo, "max_count": 3})))
        print(text_of(await _c.call_tool("git_git_status", {"repo_path": _repo})))
    ```

    你應該看到：多出 12 個 `git_git_*` 工具（`git_git_status`、`git_git_diff_unstaged`、`git_git_diff_staged`、`git_git_diff`、
    `git_git_commit`、`git_git_add`、`git_git_reset`、`git_git_log`、`git_git_create_branch`、`git_git_checkout`、`git_git_show`、`git_git_branch`——
    前綴 `git_` 是伺服器名、後面的 `git_` 是工具自己的名字）；`git_git_log` 印出 `Commit history:` 與那個 `init` commit；
    `git_git_status` 回 `On branch master / nothing to commit, working tree clean`。首次 `uvx mcp-server-git` 一樣要下載套件。
    """
            ),
            "💡 LEVEL 2 參考解答": mo.md(
                r"""
    `tools` 區塊是 FastMCP 設定檔的擴充（Claude Desktop 不認得，但 `Client(...)` 與 `create_proxy(...)` 認得）：

    ```python
    TIME_RENAMED = {"mcpServers": {"time": {
        "command": "uvx", "args": ["mcp-server-time"],
        "tools": {
            "get_current_time": {
                "name": "now",
                "description": "現在台北幾點",
                "arguments": {"timezone": {"default": "Asia/Taipei", "hide": True}},
            }
        },
    }}}
    async with Client(TIME_RENAMED) as _c:
        print([(t.name, list(t.input_schema.get("properties", {}))) for t in await _c.list_tools()])
        print(text_of(await _c.call_tool("now", {})))
    ```

    你應該看到：`[('now', []), ('convert_time', [...])]`——`now` 的參數清單是**空的**（`timezone` 被藏起來、固定 Asia/Taipei），
    `now()` 回 `"timezone": "Asia/Taipei"` 的現在時間。只有一台伺服器所以沒有 `time_` 前綴。
    這招對「模型老是把參數填錯」的工具特別有用：把它釘死、藏起來，模型就沒機會錯。
    """
            ),
            "💡 LEVEL 3 提示": mo.md(
                r"""
    方向：`FastMCP("受保護的 hub", auth=StaticTokenVerifier(tokens={"team-token": {"client_id": "team", "scopes": ["read"]}}))`，
    其餘跟 6️⃣ 一樣 mount、另開一個 port（例如 8795）。

    驗證自己做對了：`Client(url)` 不帶 token → 連線就失敗（伺服器回 401，SDK 包成 `MCPError`）；
    `Client(url, auth="team-token")` → `list_tools()` 看到 `c7_resolve-library-id`、`c7_query-docs`。
    Context7 端完全不知道你的 token——認證發生在 hub，**後端伺服器不用改一行**。

    陷阱：`import` 要加 `from fastmcp.server.auth.providers.jwt import StaticTokenVerifier`；
    正式環境把 `StaticTokenVerifier` 換成補充課 A 的 `JWTVerifier(jwks_uri=...)` 或 `GitHubProvider`，hub 其他地方不動。

    延伸：hub 層還能做的事都在 FastMCP 的 middleware／transforms——`RateLimitingMiddleware` 限流、`LoggingMiddleware` 審計、
    `@hub.tool(auth=require_scopes("docs"))` 讓不同 scope 看到不同 namespace（把 `c7_*` 留給 `docs` scope）。
    怎麼確認：用兩把不同 scope 的 token 各 `list_tools()` 一次，清單應該不一樣。
    """
            ),
        }
    )
    return


if __name__ == "__main__":
    app.run()
