# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "fastmcp==4.0.0b1",
#     "fastmcp-slim==4.0.0b1",
#     "httpx",
#     "uvicorn",
# ]
# ///
"""補充課 A（fastmcp4-auth）的定軌 spike：FastMCP 4 認證與授權，全部本機、零外部服務。

驗證：
1. StaticTokenVerifier：沒帶 token → 401 + WWW-Authenticate；帶 token → 過；get_access_token() 拿身分
2. require_scopes：同一台伺服器，不同 token 看到的工具清單不同（list 過濾＋直接呼叫 not found）
3. JWTVerifier + RSAKeyPair：本機簽 JWT；過期／audience 錯被拒
4. UserSession：有認證後 per-user 狀態桶（alice / guest 互不相見）
5. InMemoryOAuthProvider：完整 OAuth 2.1 授權碼 + PKCE 流程，用裸 httpx 一步一步走，再用 SDK OAuth（無瀏覽器 handler）三行走完
"""
import asyncio
import base64
import hashlib
import json
import secrets
import socket
import threading
import time
from urllib.parse import parse_qs, urlencode, urlparse

import httpx
import uvicorn
from fastmcp import Client, FastMCP
from fastmcp.client.auth import OAuth
from mcp.shared.auth import AuthorizationCodeResult
from fastmcp.exceptions import ToolError
from fastmcp.server.auth import require_scopes
from fastmcp.server.auth.auth import ClientRegistrationOptions
from fastmcp.server.auth.providers.in_memory import InMemoryOAuthProvider
from fastmcp.server.auth.providers.jwt import JWTVerifier, RSAKeyPair, StaticTokenVerifier
from fastmcp.server.dependencies import get_access_token
from fastmcp.server.sessions import UserSession


def serve(app, port):
    def busy():
        with socket.socket() as s:
            return s.connect_ex(("127.0.0.1", port)) == 0

    if not busy():
        server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning"))
        threading.Thread(target=server.run, daemon=True).start()
        for _ in range(50):
            if busy():
                break
            time.sleep(0.1)
    return f"http://127.0.0.1:{port}/mcp"


# ---------- 1+2: StaticTokenVerifier + require_scopes + get_access_token ----------
def build_static_server():
    auth = StaticTokenVerifier(
        tokens={
            "alice-token": {"client_id": "alice", "scopes": ["read", "write", "admin"]},
            "guest-token": {"client_id": "guest", "scopes": ["read"]},
        }
    )
    mcp = FastMCP("會員櫃台", auth=auth)

    @mcp.tool
    def whoami() -> dict:
        """回傳目前呼叫者的身分與權限。"""
        tok = get_access_token()
        return {"client_id": tok.client_id, "scopes": tok.scopes}

    @mcp.tool(auth=require_scopes("admin"))
    def close_shop() -> str:
        """打烊（只有 admin 看得到、叫得動）。"""
        return "已打烊"

    @mcp.tool
    async def remember(fact: str, session: UserSession) -> list[str]:
        """把一件事記在「這個使用者」的記憶裡。"""
        facts = await session.get("facts", default=[])
        facts.append(fact)
        await session.set("facts", facts)
        return facts

    return mcp


async def part_static():
    print("\n=== 1+2 StaticTokenVerifier / require_scopes / get_access_token / UserSession ===")
    mcp = build_static_server()
    url = serve(mcp.http_app(), 8771)

    # 沒帶 token 的裸 POST
    r = httpx.post(url, json={"jsonrpc": "2.0", "id": 1, "method": "server/discover", "params": {}},
                   headers={"Accept": "application/json, text/event-stream", "MCP-Protocol-Version": "2026-07-28",
                            "mcp-method": "server/discover"})
    print("no token ->", r.status_code, "WWW-Authenticate:", r.headers.get("www-authenticate"))
    print("body:", r.text[:200])

    # SDK client 沒帶 token
    try:
        async with Client(url) as c:
            await c.list_tools()
        print("SDK no token -> (passed?!)")
    except Exception as e:  # noqa: BLE001
        print("SDK no token ->", type(e).__name__, str(e)[:160])

    for tok in ("alice-token", "guest-token"):
        async with Client(url, auth=tok) as c:
            names = sorted(t.name for t in await c.list_tools())
            who = (await c.call_tool("whoami")).data
            try:
                closed = (await c.call_tool("close_shop")).data
            except ToolError as e:
                closed = f"ToolError: {str(e)[:80]}"
            facts = (await c.call_tool("remember", {"fact": f"{tok} 來過"})).data
            print(f"{tok}: tools={names} whoami={who} close_shop={closed!r} facts={facts}")

    # in-memory client with auth? (Client(mcp) has no HTTP → no token) → UserSession should error
    try:
        async with Client(mcp) as c:
            await c.call_tool("remember", {"fact": "x"})
        print("in-memory remember -> passed?!")
    except Exception as e:  # noqa: BLE001
        print("in-memory (no auth) remember ->", type(e).__name__, str(e)[:140])


# ---------- 3: JWTVerifier + RSAKeyPair ----------
async def part_jwt():
    print("\n=== 3 JWTVerifier + RSAKeyPair ===")
    kp = RSAKeyPair.generate()
    verifier = JWTVerifier(public_key=kp.public_key, issuer="https://sso.example.com", audience="tea-shop")
    mcp = FastMCP("JWT 櫃台", auth=verifier)

    @mcp.tool
    def whoami() -> dict:
        tok = get_access_token()
        return {"client_id": tok.client_id, "scopes": tok.scopes, "sub": tok.claims.get("sub"), "exp": tok.expires_at}

    url = serve(mcp.http_app(), 8772)
    good = kp.create_token(subject="alice", issuer="https://sso.example.com", audience="tea-shop", scopes=["read", "write"])
    print("JWT:", good[:40], "...", "segments:", len(good.split(".")))
    header, payload = (json.loads(base64.urlsafe_b64decode(p + "=" * (-len(p) % 4))) for p in good.split(".")[:2])
    print("header:", header, "payload:", payload)
    async with Client(url, auth=good) as c:
        print("good ->", (await c.call_tool("whoami")).data)

    bad_aud = kp.create_token(subject="alice", issuer="https://sso.example.com", audience="other-app", scopes=["read"])
    expired = kp.create_token(subject="alice", issuer="https://sso.example.com", audience="tea-shop", scopes=["read"], expires_in_seconds=-60)
    other_kp = RSAKeyPair.generate()
    forged = other_kp.create_token(subject="mallory", issuer="https://sso.example.com", audience="tea-shop", scopes=["admin"])
    for label, tok in (("wrong audience", bad_aud), ("expired", expired), ("forged (other key)", forged)):
        try:
            async with Client(url, auth=tok) as c:
                print(label, "-> passed?!", (await c.call_tool("whoami")).data)
        except Exception as e:  # noqa: BLE001
            print(label, "->", type(e).__name__, str(e)[:100])


# ---------- 5: full OAuth 2.1 with InMemoryOAuthProvider ----------
def build_oauth_server(base_url):
    auth = InMemoryOAuthProvider(
        base_url=base_url,
        client_registration_options=ClientRegistrationOptions(enabled=True, valid_scopes=["read", "write"], default_scopes=["read"]),
    )
    mcp = FastMCP("OAuth 櫃台", auth=auth)

    @mcp.tool
    def whoami() -> dict:
        tok = get_access_token()
        return {"client_id": tok.client_id, "scopes": tok.scopes}

    return mcp, auth


class HeadlessOAuth(OAuth):
    """molab／CI 沒有瀏覽器：自己用 httpx 去敲 authorize 端點、從 302 的 Location 撿回 code。"""

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self._result = None

    async def redirect_handler(self, authorization_url: str) -> None:
        r = httpx.get(authorization_url, follow_redirects=False)
        loc = r.headers.get("location", "")
        q = parse_qs(urlparse(loc).query)
        self._result = AuthorizationCodeResult(code=q["code"][0], state=q.get("state", [None])[0])
        print("   headless redirect ->", r.status_code, "code:", q["code"][0][:20], "...")

    async def callback_handler(self):
        return self._result


async def part_oauth():
    print("\n=== 5 InMemoryOAuthProvider: full OAuth 2.1 by hand, then SDK ===")
    port = 8773
    base = f"http://127.0.0.1:{port}"
    mcp, auth = build_oauth_server(base)
    url = serve(mcp.http_app(), port)

    h = {"Accept": "application/json, text/event-stream", "MCP-Protocol-Version": "2026-07-28", "mcp-method": "tools/list"}
    r = httpx.post(url, json={"jsonrpc": "2.0", "id": 1, "method": "tools/list",
                              "params": {"_meta": {"io.modelcontextprotocol/protocolVersion": "2026-07-28"}}}, headers=h)
    print("step0 no token ->", r.status_code, r.headers.get("www-authenticate"))

    # step1 protected resource metadata
    prm = httpx.get(f"{base}/.well-known/oauth-protected-resource/mcp")
    if prm.status_code != 200:
        prm = httpx.get(f"{base}/.well-known/oauth-protected-resource")
    print("step1 PRM", prm.status_code, prm.json())
    as_url = prm.json()["authorization_servers"][0].rstrip("/")
    asm = httpx.get(f"{as_url}/.well-known/oauth-authorization-server").json()
    print("step2 AS metadata keys:", {k: asm[k] for k in ("authorization_endpoint", "token_endpoint", "registration_endpoint", "code_challenge_methods_supported") if k in asm})

    # step3 DCR
    redirect_uri = "http://127.0.0.1:9/callback"
    reg = httpx.post(asm["registration_endpoint"], json={"client_name": "spike", "redirect_uris": [redirect_uri],
                                                        "grant_types": ["authorization_code", "refresh_token"],
                                                        "token_endpoint_auth_method": "none", "scope": "read write"})
    print("step3 DCR", reg.status_code, {k: reg.json().get(k) for k in ("client_id", "client_secret", "token_endpoint_auth_method")})
    client_id = reg.json()["client_id"]

    # step4 authorize with PKCE
    verifier = secrets.token_urlsafe(48)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    q = {"response_type": "code", "client_id": client_id, "redirect_uri": redirect_uri, "state": "xyz",
         "code_challenge": challenge, "code_challenge_method": "S256", "scope": "read write"}
    a = httpx.get(asm["authorization_endpoint"] + "?" + urlencode(q), follow_redirects=False)
    loc = a.headers.get("location", "")
    print("step4 authorize ->", a.status_code, "Location:", loc[:90])
    code = parse_qs(urlparse(loc).query)["code"][0]

    # step5 token
    t = httpx.post(asm["token_endpoint"], data={"grant_type": "authorization_code", "code": code, "redirect_uri": redirect_uri,
                                                "client_id": client_id, "code_verifier": verifier})
    print("step5 token ->", t.status_code, {k: (str(v)[:18] + "…" if isinstance(v, str) else v) for k, v in t.json().items()})
    access = t.json()["access_token"]

    # PKCE：拿一個新的 code，先用錯的 verifier 換 → 被拒；同一個 code 再用對的 → 也被拒（code 單次有效且已作廢）
    a2 = httpx.get(asm["authorization_endpoint"] + "?" + urlencode(q), follow_redirects=False)
    code2 = parse_qs(urlparse(a2.headers["location"]).query)["code"][0]
    t2 = httpx.post(asm["token_endpoint"], data={"grant_type": "authorization_code", "code": code2, "redirect_uri": redirect_uri,
                                                 "client_id": client_id, "code_verifier": "wrong-verifier"})
    print("step5b fresh code + wrong verifier ->", t2.status_code, t2.text[:120])
    t3 = httpx.post(asm["token_endpoint"], data={"grant_type": "authorization_code", "code": code, "redirect_uri": redirect_uri,
                                                 "client_id": client_id, "code_verifier": verifier})
    print("step5c reuse consumed code ->", t3.status_code, t3.text[:120])

    # step6 call with token
    async with Client(url, auth=access) as c:
        print("step6 whoami ->", (await c.call_tool("whoami")).data)

    # SDK route
    print("-- SDK OAuth (headless handlers) --")
    oauth = HeadlessOAuth(mcp_url=url, client_name="notebook", scopes=["read"])
    async with Client(url, auth=oauth) as c:
        print("SDK whoami ->", (await c.call_tool("whoami")).data)
    print("registered clients on server:", len(auth.clients), "access tokens:", len(auth.access_tokens))


async def main():
    import sys
    parts = {"static": part_static, "jwt": part_jwt, "oauth": part_oauth}
    for name in (sys.argv[1:] or parts):
        await parts[name]()


if __name__ == "__main__":
    asyncio.run(main())
