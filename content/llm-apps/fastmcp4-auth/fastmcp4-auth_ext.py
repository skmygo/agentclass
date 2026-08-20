# FastMCP 4 認證：從一把 token 到完整 OAuth 2.1
# 不需要 GPU——molab 免費 CPU 環境即可全程執行（本課不連任何外部服務：SSO、OAuth 伺服器全部在 notebook 裡本機起）。
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
app = marimo.App(width="medium", app_title="FastMCP 4 認證：從一把 token 到完整 OAuth 2.1")


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    # 🔐 FastMCP 4 認證：從一把 token 到完整 OAuth 2.1

    第 3 課的茶飲店伺服器誰都能連。一旦放到公網、或者工具會動到真的資料（下單、退款、讀顧客資料），
    你需要三件事：**知道是誰在呼叫**（認證）、**決定他能做什麼**（授權）、
    以及讓 Claude Desktop／Claude Code 這類客戶端**自己完成登入**而不用你手把手貼 token（OAuth）。

    FastMCP 4 把這三層都做成可插拔的 `auth=`。本課從最簡單的「一把寫死的 token」開始，
    一路做到**在 notebook 裡起一台真的 OAuth 2.1 授權伺服器**，用裸 HTTP 一步一步走完授權碼流程——
    每一個請求、每一個回應都看得到。全部本機、不連外、不需要任何帳號。

    內容：

    1. 沒認證會怎樣：`StaticTokenVerifier`、401 與 `WWW-Authenticate`
    2. 工具裡知道你是誰：`get_access_token()`
    3. 授權：`require_scopes` 讓工具對沒權限的人**隱形**
    4. 第 3 課的伏筆：`UserSession`——有了身分，每個使用者自動一個狀態桶
    5. 正式做法 JWT：本機簽發、公鑰驗章、三種壞 token
    6. 完整 OAuth 2.1 授權碼流程（discovery → 動態註冊 → PKCE → 換 token → 呼叫）
    7. SDK 三行版：`Client(url, auth=OAuth())`
    8. 接 GitHub／Google／企業 SSO 要改哪裡

    本課用的版本與第 3 課相同：**FastMCP 4.0.0b1**。從第一格往下全部執行即可（首次安裝套件約 1 分鐘）。
    """
    )
    return


@app.cell
def _():
    import base64
    import hashlib
    import json
    import secrets
    import socket
    import threading
    import time
    from urllib.parse import parse_qs, urlencode, urlparse

    import httpx
    import marimo as mo
    import uvicorn
    from fastmcp import Client, FastMCP
    from fastmcp.client.auth import OAuth
    from fastmcp.exceptions import ToolError
    from fastmcp.server.auth import require_scopes
    from fastmcp.server.auth.auth import ClientRegistrationOptions
    from fastmcp.server.auth.providers.in_memory import InMemoryOAuthProvider
    from fastmcp.server.auth.providers.jwt import (
        JWTVerifier,
        RSAKeyPair,
        StaticTokenVerifier,
    )
    from fastmcp.server.dependencies import get_access_token
    from fastmcp.server.sessions import UserSession
    from mcp.shared.auth import AuthorizationCodeResult
    return (
        AuthorizationCodeResult,
        Client,
        ClientRegistrationOptions,
        FastMCP,
        InMemoryOAuthProvider,
        JWTVerifier,
        OAuth,
        RSAKeyPair,
        StaticTokenVerifier,
        ToolError,
        UserSession,
        base64,
        get_access_token,
        hashlib,
        httpx,
        json,
        mo,
        parse_qs,
        require_scopes,
        secrets,
        socket,
        threading,
        time,
        urlencode,
        urlparse,
        uvicorn,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ### 小工具：在背景起一台 HTTP 伺服器

    認證只在 HTTP 傳輸上有意義（stdio 是本機子行程，安全性來自作業系統），所以本課每一節都會
    用第 3 課的方法在背景執行緒起一台真的 uvicorn。`start_server(app, port)` 回傳 `/mcp` 網址；
    重跑 cell 時先探 port，已經在聽就不重起。

    另外準備 `raw_post(url, method, token=None)`：**不用 SDK**、只帶新協定必要的 header 與 `_meta` 信封
    發一個 JSON-RPC 請求——等一下要用它看「伺服器到底回了什麼 HTTP 狀態與 header」，SDK 會把這些包掉。
    """
    )
    return


@app.cell
def _(httpx, socket, threading, time, uvicorn):
    def start_server(asgi_app, port: int) -> str:
        """在 daemon thread 跑 uvicorn；port 已在聽就不重起。回傳 MCP 網址。"""
        def _busy():
            with socket.socket() as _s:
                return _s.connect_ex(("127.0.0.1", port)) == 0
        if not _busy():
            _server = uvicorn.Server(uvicorn.Config(asgi_app, host="127.0.0.1", port=port, log_level="warning"))
            threading.Thread(target=_server.run, daemon=True).start()
            for _ in range(50):
                if _busy():
                    break
                time.sleep(0.1)
        return f"http://127.0.0.1:{port}/mcp"

    _META = {"io.modelcontextprotocol/protocolVersion": "2026-07-28",
             "io.modelcontextprotocol/clientCapabilities": {}}

    def raw_post(url: str, method: str, params: dict | None = None, token: str | None = None) -> httpx.Response:
        """裸 JSON-RPC POST（新協定三要件：協定版本 header、mcp-method header、_meta 信封）。"""
        _h = {"Accept": "application/json, text/event-stream", "Content-Type": "application/json",
              "MCP-Protocol-Version": "2026-07-28", "mcp-method": method}
        if token:
            _h["Authorization"] = f"Bearer {token}"
        return httpx.post(url, json={"jsonrpc": "2.0", "id": 1, "method": method,
                                     "params": {**(params or {}), "_meta": _META}}, headers=_h)
    return raw_post, start_server


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 1️⃣ 沒認證會怎樣：`StaticTokenVerifier`

    最小可行的認證：伺服器手上有一張「token → 身分與權限」的表。`StaticTokenVerifier` 就是這張表——
    **只適合開發與教學**（token 明文寫在程式裡），但它把認證的三個概念一次攤開：

    - `client_id`：這把 token 代表誰
    - `scopes`：他被授予哪些權限（字串清單，名字隨你訂）
    - `auth=` 掛到 `FastMCP(...)` 上，整台伺服器的 HTTP 入口就都要驗 token

    我們開一間「會員櫃台」：alice 是店長（`read`／`write`／`admin`），guest 是訪客（只有 `read`）。
    三個工具先註冊好，2️⃣–4️⃣ 會逐一用到。
    """
    )
    return


@app.cell
def _(FastMCP, StaticTokenVerifier, UserSession, get_access_token, require_scopes):
    TOKENS = {
        "alice-token": {"client_id": "alice", "scopes": ["read", "write", "admin"]},
        "guest-token": {"client_id": "guest", "scopes": ["read"]},
    }
    counter = FastMCP("會員櫃台", auth=StaticTokenVerifier(tokens=TOKENS))

    @counter.tool
    def whoami() -> dict:
        """回傳目前呼叫者的身分與權限。"""
        _tok = get_access_token()
        return {"client_id": _tok.client_id, "scopes": _tok.scopes}

    @counter.tool(auth=require_scopes("admin"))
    def close_shop() -> str:
        """打烊（只有 admin 看得到、叫得動）。"""
        return "已打烊"

    @counter.tool
    async def remember(fact: str, session: UserSession) -> list[str]:
        """把一件事記在「這個使用者」自己的記憶裡，回傳他目前記得的全部。"""
        _facts = await session.get("facts", default=[])
        _facts.append(fact)
        await session.set("facts", _facts)
        return _facts

    counter_tools_ready = ["whoami", "close_shop", "remember"]
    return TOKENS, close_shop, counter, counter_tools_ready, remember, whoami


@app.cell
def _(counter, counter_tools_ready, mo, start_server):
    _ = counter_tools_ready
    COUNTER_URL = start_server(counter.http_app(), 8771)
    mo.md(f"會員櫃台在 **`{COUNTER_URL}`** 聽候。")
    return (COUNTER_URL,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ### 不帶 token 敲門

    用裸 POST 送一個 `server/discover`，**不帶** `Authorization`。看 HTTP 狀態與 `WWW-Authenticate` header：
    這是標準的 HTTP 認證挑戰（RFC 6750）——伺服器說「我要 Bearer token」。6️⃣ 會看到有 OAuth 時這個 header
    還會多告訴客戶端**去哪裡拿 token**。
    """
    )
    return


@app.cell
def _(COUNTER_URL, mo, raw_post):
    _no = raw_post(COUNTER_URL, "server/discover")
    _bad = raw_post(COUNTER_URL, "server/discover", token="not-a-real-token")
    _ok = raw_post(COUNTER_URL, "server/discover", token="alice-token")
    mo.md(
        f"""
    | 請求 | HTTP 狀態 | `WWW-Authenticate` |
    |---|---|---|
    | 不帶 token | **{_no.status_code}** | `{_no.headers.get("www-authenticate")}` |
    | 帶一把亂掰的 token | **{_bad.status_code}** | `{_bad.headers.get("www-authenticate", "")[:60]}…` |
    | 帶 `alice-token` | **{_ok.status_code}** | （通過，回 `{_ok.json()["result"].get("_meta", {}).get("io.modelcontextprotocol/serverInfo", {}).get("name")}` 的能力清單） |

    注意亂掰的 token 回應只說 `invalid_token`，**不會說「這把 token 不存在」還是「過期」**——
    真正的原因只寫進伺服器 log。對攻擊者少講一句就少一條線索。
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ### SDK 怎麼帶 token

    `Client(url, auth="alice-token")`：給一個字串，FastMCP 自動加上 `Authorization: Bearer …`。
    之後每個請求都帶，你不用再管。
    """
    )
    return


@app.cell
async def _(COUNTER_URL, Client, mo):
    async with Client(COUNTER_URL, auth="alice-token") as _c:
        alice_tools = sorted(t.name for t in await _c.list_tools())
    mo.md(f"alice 連上了，看到 **{len(alice_tools)} 個工具**：`{alice_tools}`")
    return (alice_tools,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 2️⃣ 工具裡知道你是誰：`get_access_token()`

    認證過的請求，工具函式裡隨時可以呼叫 `get_access_token()` 拿到 `AccessToken`：
    `client_id`、`scopes`、`claims`（JWT 的原始欄位，5️⃣ 會看到）、`expires_at`。
    這是「個人化」與「稽核」的起點——同一個 `whoami` 工具，兩把 token 得到兩個答案。
    """
    )
    return


@app.cell
async def _(COUNTER_URL, Client, mo):
    _rows = []
    for _tok in ("alice-token", "guest-token"):
        async with Client(COUNTER_URL, auth=_tok) as _c:
            _who = (await _c.call_tool("whoami")).data
            _rows.append({"token": _tok, "client_id": _who["client_id"], "scopes": ", ".join(_who["scopes"])})
    mo.ui.table(_rows, selection=None)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 3️⃣ 授權：沒權限的工具直接隱形

    `@counter.tool(auth=require_scopes("admin"))` 宣告「要有 `admin` scope 才能用」。
    FastMCP 的做法不是回 403，而是**連清單都不給看**：guest 的 `list_tools()` 根本沒有 `close_shop`，
    硬呼叫也只得到 `Unknown tool`——對沒權限的人來說，這個工具不存在。
    （模型看不到就不會試著去叫，少掉一整類「AI 一直撞 403」的問題。）

    `require_scopes("read", "write")` 給多個 scope 是 AND；也有 `require_roles`、自訂檢查函式
    （收一個 `AuthContext`、回 bool）。要讓「拒絕」變成明確錯誤而不是隱形，用伺服器層的
    `AuthMiddleware`——挑戰 LEVEL 2 會做。
    """
    )
    return


@app.cell
async def _(COUNTER_URL, Client, ToolError, mo):
    _rows = []
    for _tok in ("alice-token", "guest-token"):
        async with Client(COUNTER_URL, auth=_tok) as _c:
            _names = sorted(t.name for t in await _c.list_tools())
            try:
                _closed = (await _c.call_tool("close_shop")).data
            except ToolError as _e:
                _closed = f"🛑 {str(_e)[:60]}"
            _rows.append({"token": _tok, "list_tools()": ", ".join(_names), "call_tool('close_shop')": _closed})
    mo.ui.table(_rows, selection=None)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 4️⃣ 第 3 課的伏筆：`UserSession`

    第 3 課的購物車用 `SessionId`——一把要自己保管、每次帶來的鑰匙，因為那時沒有登入機制。
    現在有了：宣告 `session: UserSession`，FastMCP **自動注入**、不進工具的 schema、
    呼叫端什麼都不用傳——因為「你是誰」已經由 token 決定，狀態桶就用身分選。

    看 `remember` 的說明書：只有 `fact` 一個參數。alice 記兩件事、guest 記一件，各自拿回各自的清單。
    """
    )
    return


@app.cell
async def _(COUNTER_URL, Client, json, mo, remember):
    _ = remember
    async with Client(COUNTER_URL, auth="alice-token") as _c:
        _schema = {t.name: t.input_schema for t in await _c.list_tools()}["remember"]
        await _c.call_tool("remember", {"fact": "alice 喜歡烏龍"})
        _alice = (await _c.call_tool("remember", {"fact": "alice 上次點珍奶"})).data
    async with Client(COUNTER_URL, auth="guest-token") as _c:
        _guest = (await _c.call_tool("remember", {"fact": "guest 第一次來"})).data
    mo.md(
        f"""
    `remember` 的 schema（沒有 session 欄位）：`{json.dumps(_schema.get("properties"), ensure_ascii=False)}`

    | 誰 | `remember(...)` 回傳 |
    |---|---|
    | alice 記了兩件 | `{_alice}` |
    | guest 記了一件 | `{_guest}` |

    兩個桶互不相見。換成 Redis 當 `session_state_store` 就能跨副本、跨重啟（下一課細講）。
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ### 沒有身分時 `UserSession` 會怎樣？

    用 in-memory `Client(counter)` 直連伺服器實例——沒有 HTTP、沒有 token、沒有身分。
    FastMCP 不會默默開一個匿名桶，而是**明確報錯**，還告訴你沒登入機制時該改用 `SessionId`：
    """
    )
    return


@app.cell
async def _(Client, ToolError, counter, mo):
    try:
        async with Client(counter) as _c:
            await _c.call_tool("remember", {"fact": "x"})
        _msg = "（居然過了？）"
    except ToolError as _e:
        _msg = str(_e)
    mo.callout(mo.md(f"`ToolError`：{_msg}"), kind="warn")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 5️⃣ 正式做法：JWT，簽發與驗章分開

    正式環境不會有一張明文 token 表。主流做法是 **JWT**：由你的 SSO／身分服務用**私鑰簽發**，
    MCP 伺服器只拿**公鑰驗章**——它不需要連線問任何人，也不需要儲存任何 token。

    這裡為了全程本機，用 `RSAKeyPair.generate()` 當一個迷你 SSO：私鑰簽 token、公鑰交給
    `JWTVerifier(public_key=..., issuer=..., audience=...)`。正式環境把 `public_key=` 換成
    `jwks_uri="https://你的SSO/.well-known/jwks.json"`，其他一個字不用改。

    `issuer`／`audience` 是兩道必檢：token 必須是**這家** SSO 發的、必須是發給**這台**伺服器的——
    同一家 SSO 發給別的 app 的 token 在這裡無效。
    """
    )
    return


@app.cell
def _(FastMCP, JWTVerifier, RSAKeyPair, get_access_token, start_server):
    sso = RSAKeyPair.generate()   # 迷你 SSO：私鑰簽發
    ISSUER, AUDIENCE = "https://sso.example.com", "tea-shop"

    jwt_shop = FastMCP("JWT 櫃台", auth=JWTVerifier(public_key=sso.public_key, issuer=ISSUER, audience=AUDIENCE))

    @jwt_shop.tool
    def jwt_whoami() -> dict:
        """回傳 JWT 裡的身分欄位。"""
        _tok = get_access_token()
        return {"client_id": _tok.client_id, "sub": _tok.claims.get("sub"), "scopes": _tok.scopes, "exp": _tok.expires_at}

    JWT_URL = start_server(jwt_shop.http_app(), 8772)
    return AUDIENCE, ISSUER, JWT_URL, jwt_shop, jwt_whoami, sso


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ### 簽一把、拆開看

    `sso.create_token(subject=..., issuer=..., audience=..., scopes=[...])` 簽出一個 JWT：三段 base64、用 `.` 接起來。
    前兩段**不是加密**、只是編碼——任何人都能解開看 header（演算法）與 payload（`sub`、`iss`、`aud`、`exp`、`scope`）；
    第三段是簽章，沒有私鑰做不出來、改動前兩段任何一個字元就對不上。
    """
    )
    return


@app.cell
async def _(AUDIENCE, Client, ISSUER, JWT_URL, base64, json, jwt_whoami, mo, sso):
    _ = jwt_whoami
    alice_jwt = sso.create_token(subject="alice", issuer=ISSUER, audience=AUDIENCE, scopes=["read", "write"])
    _h, _p, _sig = alice_jwt.split(".")
    _decode = lambda s: json.loads(base64.urlsafe_b64decode(s + "=" * (-len(s) % 4)))
    async with Client(JWT_URL, auth=alice_jwt) as _c:
        _who = (await _c.call_tool("jwt_whoami")).data
    mo.md(
        f"""
    JWT（{len(alice_jwt)} 字元）：`{alice_jwt[:28]}…{alice_jwt[-12:]}`

    | 段 | 解開後 |
    |---|---|
    | header | `{json.dumps(_decode(_h))}` |
    | payload | `{json.dumps(_decode(_p))}` |
    | signature | `{_sig[:24]}…`（{len(_sig)} 字元，RS256 簽章） |

    帶著它呼叫 `jwt_whoami` → `{_who}`（`scope` 字串被拆成清單、`exp` 變成 `expires_at`）。
    """
    )
    return (alice_jwt,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ### 三種壞 token

    1. **audience 錯**：同一家 SSO 簽的、但 `aud` 是別的 app
    2. **過期**：`expires_in_seconds=-60`，簽出來就已經過期一分鐘
    3. **偽造**：另一組金鑰簽的、內容寫 `admin`——簽章對不上公鑰

    三個在線路上長得一模一樣：`401` ＋ `invalid_token`。原因（`audience mismatch`／`token expired`／簽章不符）
    只出現在伺服器 log。
    """
    )
    return


@app.cell
def _(AUDIENCE, ISSUER, JWT_URL, RSAKeyPair, mo, raw_post, sso):
    _bad = {
        "audience 錯（aud=other-app）": sso.create_token(subject="alice", issuer=ISSUER, audience="other-app", scopes=["read"]),
        "過期（簽出來就過期 60 秒）": sso.create_token(subject="alice", issuer=ISSUER, audience=AUDIENCE, scopes=["read"], expires_in_seconds=-60),
        "偽造（別組金鑰簽的 admin）": RSAKeyPair.generate().create_token(subject="mallory", issuer=ISSUER, audience=AUDIENCE, scopes=["admin"]),
    }
    _rows = []
    for _label, _tok in _bad.items():
        _r = raw_post(JWT_URL, "tools/list", token=_tok)
        _rows.append({"token": _label, "HTTP": _r.status_code,
                      "WWW-Authenticate": _r.headers.get("www-authenticate", "")[:34] + "…"})
    mo.ui.table(_rows, selection=None)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 6️⃣ 完整 OAuth 2.1 授權碼流程，一步一步走

    到目前為止 token 都是「你先弄到手、再貼給 client」。真實的 MCP 客戶端（Claude Desktop、Cursor、
    `fastmcp.Client(auth="oauth")`）期待的是：**連上去被拒絕 → 自己找到授權伺服器 → 自己註冊 →
    跳瀏覽器讓使用者同意 → 自己換到 token**，全程不用人手貼任何東西。這就是 OAuth 2.1 在 MCP 裡的樣子。

    為了全程本機，用 FastMCP 內建的測試用授權伺服器 `InMemoryOAuthProvider`：它是一個完整的
    OAuth 2.1 authorization server（discovery、動態註冊 DCR、PKCE、token、refresh 都有），
    只是「使用者同意」那一步自動按下同意。**跟 MCP 伺服器掛在同一個 port 上**，
    `base_url` 要填伺服器對外的網址。

    下面每一步都用裸 `httpx`，沒有任何魔法。
    """
    )
    return


@app.cell
def _(ClientRegistrationOptions, FastMCP, InMemoryOAuthProvider, get_access_token, start_server):
    OAUTH_PORT = 8773
    OAUTH_BASE = f"http://127.0.0.1:{OAUTH_PORT}"
    oauth_provider = InMemoryOAuthProvider(
        base_url=OAUTH_BASE,
        client_registration_options=ClientRegistrationOptions(enabled=True, valid_scopes=["read", "write"], default_scopes=["read"]),
    )
    oauth_shop = FastMCP("OAuth 櫃台", auth=oauth_provider)

    @oauth_shop.tool
    def oauth_whoami() -> dict:
        """回傳 OAuth token 代表的客戶端與 scopes。"""
        _tok = get_access_token()
        return {"client_id": _tok.client_id, "scopes": _tok.scopes}

    OAUTH_URL = start_server(oauth_shop.http_app(), OAUTH_PORT)
    return OAUTH_BASE, OAUTH_URL, oauth_provider, oauth_shop, oauth_whoami


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ### 步驟 0–2：被拒絕，然後「自己找路」（discovery）

    - **步驟 0**：不帶 token 敲 `/mcp` → `401`。但這次 `WWW-Authenticate` 多了 `resource_metadata="…"`——
      一個網址，告訴客戶端「我的保護資源說明在這裡」。
    - **步驟 1**：GET 那個網址（`/.well-known/oauth-protected-resource/mcp`）→ 這個資源信任哪些授權伺服器、支援哪些 scope。
    - **步驟 2**：GET 授權伺服器的 `/.well-known/oauth-authorization-server` → 三個關鍵端點：
      `authorization_endpoint`、`token_endpoint`、`registration_endpoint`，以及它支援 PKCE 的 `S256`。

    客戶端靠這兩份 metadata 就知道接下來每一步要打哪裡——**沒有任何東西是寫死的**。
    """
    )
    return


@app.cell
def _(OAUTH_URL, httpx, json, mo, oauth_whoami, raw_post):
    _ = oauth_whoami
    _r0 = raw_post(OAUTH_URL, "tools/list")
    _www = _r0.headers.get("www-authenticate", "")
    _prm_url = _www.split('resource_metadata="')[1].rstrip('"') if "resource_metadata=" in _www else ""
    prm = httpx.get(_prm_url).json()
    as_meta = httpx.get(prm["authorization_servers"][0].rstrip("/") + "/.well-known/oauth-authorization-server").json()
    mo.md(
        f"""
    | 步驟 | 請求 | 回應重點 |
    |---|---|---|
    | 0 | `POST /mcp`（不帶 token） | **{_r0.status_code}**，`WWW-Authenticate: {_www}` |
    | 1 | `GET {_prm_url.replace("http://127.0.0.1:8773", "")}` | `authorization_servers`: `{prm["authorization_servers"]}`、`scopes_supported`: `{prm["scopes_supported"]}` |
    | 2 | `GET /.well-known/oauth-authorization-server` | `{json.dumps({k: as_meta[k].replace("http://127.0.0.1:8773", "") if isinstance(as_meta[k], str) else as_meta[k] for k in ("authorization_endpoint", "token_endpoint", "registration_endpoint", "code_challenge_methods_supported")})}` |
    """
    )
    return as_meta, prm


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ### 步驟 3：動態註冊（DCR）

    傳統 OAuth 要你先去供應商後台手動建一個 app、拿 client_id／secret。MCP 客戶端來自四面八方，
    不可能每個都手動建——所以 MCP 要求授權伺服器支援 **Dynamic Client Registration**（RFC 7591）：
    客戶端 `POST /register` 自報名字、redirect URI、要的 scope，當場拿到 `client_id`。
    公開客戶端（桌面 app、CLI）沒有 secret（`token_endpoint_auth_method: none`），安全性交給下一步的 PKCE。
    """
    )
    return


@app.cell
def _(as_meta, httpx, mo):
    REDIRECT_URI = "http://127.0.0.1:9/callback"   # 真實客戶端會在本機臨時開一個 port 收 callback
    _reg = httpx.post(as_meta["registration_endpoint"], json={
        "client_name": "notebook 客戶端",
        "redirect_uris": [REDIRECT_URI],
        "grant_types": ["authorization_code", "refresh_token"],
        "token_endpoint_auth_method": "none",
        "scope": "read write",
    })
    registration = _reg.json()
    CLIENT_ID = registration["client_id"]
    mo.md(
        f"""
    `POST /register` → **{_reg.status_code}**

    | 欄位 | 值 |
    |---|---|
    | `client_id` | `{CLIENT_ID}` |
    | `client_secret` | `{registration.get("client_secret")}`（公開客戶端，沒有 secret） |
    | `redirect_uris` | `{registration.get("redirect_uris")}` |
    | `scope` | `{registration.get("scope")}` |
    """
    )
    return CLIENT_ID, REDIRECT_URI, registration


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ### 步驟 4：授權請求＋PKCE，拿到一次性的 code

    客戶端產生一個隨機的 `code_verifier`，把它的 SHA-256 當 `code_challenge` 放進授權網址；
    瀏覽器開這個網址讓使用者登入、同意後，授權伺服器 **302** 回 `redirect_uri`，query 裡帶著 `code` 與 `state`。

    這裡沒有瀏覽器，就用 `httpx.get(..., follow_redirects=False)` 敲一下、從 `Location` header 撿 code
    （`InMemoryOAuthProvider` 會自動「同意」）。注意 `state` 原封不動回來——客戶端要比對它防 CSRF。
    """
    )
    return


@app.cell
def _(CLIENT_ID, REDIRECT_URI, as_meta, base64, hashlib, httpx, mo, parse_qs, secrets, urlencode, urlparse):
    code_verifier = secrets.token_urlsafe(48)
    _challenge = base64.urlsafe_b64encode(hashlib.sha256(code_verifier.encode()).digest()).rstrip(b"=").decode()
    authorize_query = {
        "response_type": "code", "client_id": CLIENT_ID, "redirect_uri": REDIRECT_URI,
        "state": secrets.token_urlsafe(8), "scope": "read write",
        "code_challenge": _challenge, "code_challenge_method": "S256",
    }
    _a = httpx.get(as_meta["authorization_endpoint"] + "?" + urlencode(authorize_query), follow_redirects=False)
    _loc = _a.headers.get("location", "")
    _q = parse_qs(urlparse(_loc).query)
    auth_code = _q["code"][0]
    mo.md(
        f"""
    `GET /authorize?response_type=code&client_id=…&code_challenge={_challenge[:12]}…&code_challenge_method=S256&state={authorize_query["state"]}`

    → **{_a.status_code}** `Location: {_loc.replace(auth_code, auth_code[:22] + "…")}`

    撿到 `code` = `{auth_code[:22]}…`，`state` 回來是 `{_q.get("state", [""])[0]}`（{"✅ 一致" if _q.get("state", [""])[0] == authorize_query["state"] else "❌ 不一致"}）。
    這個 code **只能用一次、幾分鐘內有效**、而且只有知道 `code_verifier` 原文的人換得到 token。
    """
    )
    return auth_code, authorize_query, code_verifier


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ### 步驟 5：用 code ＋ verifier 換 token

    `POST /token`，帶 `grant_type=authorization_code`、剛才的 `code`、`redirect_uri`、`client_id`，
    以及 **`code_verifier` 原文**。授權伺服器算一次 SHA-256 對上步驟 4 的 `code_challenge` 才發 token。
    回來的東西：`access_token`（之後每個請求帶它）、`expires_in`、`scope`、`refresh_token`（到期後換新的用，挑戰 LEVEL 3）。
    """
    )
    return


@app.cell
def _(CLIENT_ID, REDIRECT_URI, as_meta, auth_code, code_verifier, httpx, mo):
    _t = httpx.post(as_meta["token_endpoint"], data={
        "grant_type": "authorization_code", "code": auth_code, "redirect_uri": REDIRECT_URI,
        "client_id": CLIENT_ID, "code_verifier": code_verifier,
    })
    token_set = _t.json()
    access_token = token_set["access_token"]
    mo.md(
        f"""
    `POST /token` → **{_t.status_code}**

    | 欄位 | 值 |
    |---|---|
    | `access_token` | `{access_token[:24]}…` |
    | `token_type` | `{token_set.get("token_type")}` |
    | `expires_in` | `{token_set.get("expires_in")}` 秒 |
    | `scope` | `{token_set.get("scope")}` |
    | `refresh_token` | `{str(token_set.get("refresh_token"))[:24]}…` |
    """
    )
    return access_token, token_set


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ### 步驟 6：帶著 token 呼叫工具——以及兩個反例

    `Client(OAUTH_URL, auth=access_token)` 就跟 1️⃣ 一樣。反例驗證 PKCE 與一次性：

    - 再要一個新 code，但用**錯的 `code_verifier`** 去換 → `invalid_grant: incorrect code_verifier`
    - 把剛才**已經用過的 code** 再換一次 → `invalid_grant: authorization code does not exist`（用過即銷毀）
    """
    )
    return


@app.cell
async def _(CLIENT_ID, Client, OAUTH_URL, REDIRECT_URI, access_token, as_meta, auth_code, authorize_query, code_verifier, httpx, mo, parse_qs, urlencode, urlparse):
    async with Client(OAUTH_URL, auth=access_token) as _c:
        _who = (await _c.call_tool("oauth_whoami")).data

    _a2 = httpx.get(as_meta["authorization_endpoint"] + "?" + urlencode(authorize_query), follow_redirects=False)
    _code2 = parse_qs(urlparse(_a2.headers["location"]).query)["code"][0]
    _wrong = httpx.post(as_meta["token_endpoint"], data={"grant_type": "authorization_code", "code": _code2, "redirect_uri": REDIRECT_URI,
                                                        "client_id": CLIENT_ID, "code_verifier": "wrong-verifier"})
    _reuse = httpx.post(as_meta["token_endpoint"], data={"grant_type": "authorization_code", "code": auth_code, "redirect_uri": REDIRECT_URI,
                                                        "client_id": CLIENT_ID, "code_verifier": code_verifier})
    mo.md(
        f"""
    | 動作 | 結果 |
    |---|---|
    | 帶 access_token 呼叫 `oauth_whoami` | ✅ `{_who}` |
    | 新 code ＋ 錯的 verifier 換 token | **{_wrong.status_code}** `{_wrong.json().get("error")}: {_wrong.json().get("error_description")}` |
    | 用過的 code 再換一次 | **{_reuse.status_code}** `{_reuse.json().get("error")}: {_reuse.json().get("error_description")}` |

    六個步驟走完。這就是每一個支援 OAuth 的 MCP 客戶端在你按下「連線」之後、背後默默做的事。
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 7️⃣ SDK 三行版：`Client(url, auth=OAuth())`

    上面六步，`fastmcp.Client` 全包：`auth=OAuth(...)`（或更懶的 `auth="oauth"`）會自己 discovery、
    註冊、開瀏覽器、在本機臨時開一個 port 收 callback、換 token、存起來、到期自動 refresh。

    唯一的問題：**molab 沒有瀏覽器**。`OAuth` 把「開瀏覽器」與「等 callback」做成兩個可覆寫的方法，
    所以我們寫一個子類別：`redirect_handler` 用 httpx 去敲授權網址、從 302 撿 code；
    `callback_handler` 把撿到的 code 交回去。**在你自己的電腦上不用覆寫**——預設會自動開瀏覽器。
    """
    )
    return


@app.cell
async def _(AuthorizationCodeResult, Client, OAUTH_URL, OAuth, httpx, mo, oauth_provider, parse_qs, urlparse):
    class HeadlessOAuth(OAuth):
        """沒有瀏覽器的環境：自己敲 authorize 端點撿 code。"""

        def __init__(self, *a, **kw):
            super().__init__(*a, **kw)
            self._result = None

        async def redirect_handler(self, authorization_url: str) -> None:   # 預設是 webbrowser.open(...)
            async with httpx.AsyncClient() as _h:
                _r = await _h.get(authorization_url, follow_redirects=False)
            _q = parse_qs(urlparse(_r.headers["location"]).query)
            self._result = AuthorizationCodeResult(code=_q["code"][0], state=_q.get("state", [None])[0])

        async def callback_handler(self) -> AuthorizationCodeResult:       # 預設是本機起 callback server 等瀏覽器跳回來
            return self._result

    async with Client(OAUTH_URL, auth=HeadlessOAuth(mcp_url=OAUTH_URL, client_name="SDK 客戶端", scopes=["read"])) as _c:
        _who = (await _c.call_tool("oauth_whoami")).data
    mo.md(
        f"""
    SDK 走完整個流程後呼叫 `oauth_whoami` → `{_who}`

    授權伺服器這邊現在有 **{len(oauth_provider.clients)} 個註冊的客戶端**（6️⃣ 手動一個、7️⃣ SDK 一個）、
    **{len(oauth_provider.access_tokens)} 個 access token**。在自己電腦上把 `HeadlessOAuth(...)` 換成 `OAuth()`，
    或乾脆 `Client(url, auth="oauth")`，其餘一樣。
    """
    )
    return (HeadlessOAuth,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 8️⃣ 接真的供應商要改哪裡

    `InMemoryOAuthProvider` 是教學用的；正式環境你**不會自己當授權伺服器**，而是接現成的身分供應商。
    FastMCP 依「供應商支不支援 DCR」分成兩條路，程式碼都只有 `auth=` 那一行不同：

    ```python
    # (a) 沒有 DCR 的供應商（GitHub、Google、Azure、AWS、多數企業 SSO）：OAuthProxy
    #     你先去供應商後台建一個 OAuth App 拿固定的 client_id/secret；FastMCP 對 MCP 客戶端
    #     假裝自己支援 DCR、對上游用你的固定憑證，還處理 callback 轉發。
    from fastmcp.server.auth.providers.github import GitHubProvider
    auth = GitHubProvider(client_id=os.environ["GITHUB_CLIENT_ID"],
                          client_secret=os.environ["GITHUB_CLIENT_SECRET"],
                          base_url="https://your-server.example.com")   # 也有 GoogleProvider、AzureProvider…

    # (b) 有 DCR 的供應商（WorkOS AuthKit、Descope、Keycloak…）：RemoteAuthProvider
    from fastmcp.server.auth.providers.workos import AuthKitProvider
    auth = AuthKitProvider(authkit_domain="https://your-project.authkit.app",
                           base_url="https://your-server.example.com")

    # (c) 已經有 JWT 基礎建設、不需要 OAuth 流程：JWTVerifier（5️⃣），jwks_uri 指到 SSO
    # (d) 多來源並存（互動客戶端走 OAuth、內部服務帶 JWT）：MultiAuth(server=..., verifiers=[...])

    mcp = FastMCP("正式伺服器", auth=auth)
    ```

    客戶端這邊，沒有人在鍵盤前的程式（排程、CI、伺服器對伺服器）用 **client credentials**：
    `Client(url, auth=ClientCredentialsOAuthProvider(client_id=..., client_secret=..., scopes=[...]))`，
    不開瀏覽器、不跳轉。

    | 情境 | 用 |
    |---|---|
    | 開發、測試、教學 | `StaticTokenVerifier`／`InMemoryOAuthProvider` |
    | 公司已有 SSO 發 JWT | `JWTVerifier(jwks_uri=...)` |
    | 讓使用者用 GitHub／Google 登入 | `GitHubProvider`／`GoogleProvider`（`OAuthProxy`） |
    | 身分平台支援 DCR | `AuthKitProvider` 等（`RemoteAuthProvider`） |
    | 互動＋機器兩種客戶端 | `MultiAuth` |
    | 自己當完整授權伺服器 | `OAuthProvider` 子類別——除非有不得不的理由 |

    ## 🏆 延伸挑戰

    1. **LEVEL 1**：在 1️⃣ 的 `TOKENS` 加一把 `bob-token`（`client_id: "bob"`、只有 `write`），重跑 3️⃣ 的表：
       bob 看得到哪些工具？`remember` 呢？
    2. **LEVEL 2**：把授權從「隱形」改成「明確拒絕」：建一台新伺服器，`FastMCP(..., middleware=[AuthMiddleware(auth=require_scopes("read"))])`，
       再加一個 `@tool(auth=require_scopes("read", "write"))` 的工具。用 alice／guest／bob 各連一次，
       觀察 `list_tools()` 與直接呼叫的錯誤訊息有什麼不同（提示：錯誤會寫出**缺哪個 scope**）。
    3. **LEVEL 3**：6️⃣ 的 `token_set` 裡有 `refresh_token`。用 `grant_type=refresh_token` 去 `POST /token` 換一組新的，
       然後驗證：新 access_token 能用嗎？**舊的**還能用嗎？舊的 refresh_token 再用一次會怎樣？

    帶得走：下載本檔後 `uvx marimo edit --sandbox fastmcp4-auth_ext.py` 在自己電腦繼續玩。
    下一課：**FastMCP 4 狀態**——無狀態協定上的三種記憶，以及「傳來傳去的狀態到底有沒有加密」。
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.accordion(
        {
            "💡 LEVEL 1 參考解答": mo.md(
                r"""
    把 1️⃣ 定義 `TOKENS` 的那格改成三把：

    ```python
    TOKENS = {
        "alice-token": {"client_id": "alice", "scopes": ["read", "write", "admin"]},
        "guest-token": {"client_id": "guest", "scopes": ["read"]},
        "bob-token":   {"client_id": "bob",   "scopes": ["write"]},
    }
    ```

    然後在 3️⃣ 的表格那格把 `for _tok in ("alice-token", "guest-token")` 改成三把（或貼一個新 cell）：

    ```python
    async with Client(COUNTER_URL, auth="bob-token") as _c:
        print(sorted(t.name for t in await _c.list_tools()))
        print((await _c.call_tool("remember", {"fact": "bob 來過"})).data)
    ```

    你應該看到：bob 看得到 `remember` 與 `whoami`（它們沒有宣告 `auth=`，任何**認證過**的人都能用），
    看不到 `close_shop`（要 `admin`）；`remember` 回 `['bob 來過']`——他有自己的桶。
    結論：工具沒寫 `auth=` ＝「登入即可」，不是「要有 read」。
    """
            ),
            "💡 LEVEL 2 參考解答": mo.md(
                r"""
    ```python
    from fastmcp.server.middleware import AuthMiddleware

    strict = FastMCP(
        "嚴格櫃台",
        auth=StaticTokenVerifier(tokens={**TOKENS, "bob-token": {"client_id": "bob", "scopes": ["write"]}}),
        middleware=[AuthMiddleware(auth=require_scopes("read"))],   # 整台伺服器：至少要有 read
    )

    @strict.tool
    def menu() -> str:
        return "今日菜單"

    @strict.tool(auth=require_scopes("read", "write"))              # 兩個 scope 都要（AND）
    def update_menu() -> str:
        return "菜單已更新"

    STRICT_URL = start_server(strict.http_app(), 8774)

    for _tok in ("alice-token", "guest-token", "bob-token"):
        async with Client(STRICT_URL, auth=_tok) as _c:
            _names = sorted(t.name for t in await _c.list_tools())
            try:
                _r = (await _c.call_tool("menu")).data
            except ToolError as _e:
                _r = str(_e)
            print(_tok, _names, _r)
    ```

    實測結果：

    - `alice-token`：`['menu', 'update_menu']`，`menu` → `今日菜單`
    - `guest-token`：`['menu']`（沒有 `write`，`update_menu` 隱形），`menu` → `今日菜單`
    - `bob-token`：`[]`（伺服器層要求 `read`，他一個都看不到），直接呼叫 `menu` →
      `Authorization failed for tool 'menu': insufficient scope (required: read)`

    差別在最後一列：元件層的 `auth=` 只會讓工具**隱形**；伺服器層的 `AuthMiddleware` 會在執行時丟出
    `InsufficientScopeError`，**明確寫出缺哪個 scope**——4.0 新增，讓客戶端知道該回去多要哪個權限（step-up）。
    """
            ),
            "💡 LEVEL 3 提示": mo.md(
                r"""
    ```python
    _new = httpx.post(as_meta["token_endpoint"], data={
        "grant_type": "refresh_token",
        "refresh_token": token_set["refresh_token"],
        "client_id": CLIENT_ID,
    }).json()
    ```

    怎麼驗證你做對了（實測 `InMemoryOAuthProvider`）：

    1. `_new["access_token"] != access_token`，而且 `_new` 裡**還有一個新的** `refresh_token`——這叫 refresh token rotation。
    2. 用新 token `Client(OAUTH_URL, auth=_new["access_token"])` 呼叫 `oauth_whoami` 正常。
    3. 用**舊的** `access_token` 連線 → 連 `Client` 都進不去（401 `invalid_token`）：refresh 的同時舊 token 被撤銷。
    4. 把**舊的** `refresh_token` 再送一次 → `invalid_grant`。

    陷阱：refresh 之後一定要把新的 access／refresh 兩把都存起來；只存 access 的話下次到期就回不來了。
    `fastmcp.Client` 的 `OAuth` 會自動處理這件事（`token_storage` 可換成加密檔案或 Redis）。
    """
            ),
        }
    )
    return


if __name__ == "__main__":
    app.run()
