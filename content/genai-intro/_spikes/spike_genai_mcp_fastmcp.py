# /// script
# requires-python = ">=3.12,<3.14"
# dependencies = [
#     "fastmcp==4.0.8",
#     "fastmcp-tasks==4.0.8",
#     "fastapi",
#     "uvicorn",
#     "httpx",
# ]
# ///
"""genai-mcp-fastmcp（補充 D）的定軌 spike：用 FastMCP 4.0.8 在本機起真的 HTTP 伺服器，側錄線路。

全部在本機跑、不連任何外部服務、不需要 key、純 CPU（第一次跑只有 uv 裝套件要網路）。
課程頁與 notebook 裡的每一筆封包、每一個錯誤訊息、每一段功能證據都來自這支腳本的輸出。

錄什麼（輸出一份 JSON）：
  eras      同一台 FastMCP 4.0.8 伺服器，用五個協定年代各做一次「列工具＋呼叫 add(2,3)」
            2026-07-28 / 2025-11-25：FastMCP Client（mode="auto" / "legacy"）
            2025-06-18 / 2025-03-26：照該版規格手寫的 httpx 客戶端（Streamable HTTP＋握手）
            2024-11-05：照該版規格手寫的 HTTP+SSE 客戶端（GET /sse 長連線＋POST /messages/）
  scenarios 封包檢視器的情境：呼叫工具、伺服器反問使用者（新舊兩種）、背景任務、路由 header＋快取
  grid      手刻一發 tools/call：四個旋鈕（版本 header／Mcp-Method／Mcp-Name／_meta）全組合的真實回應
  replicas  兩台副本＋輪流分派（round-robin）與黏著（sticky）負載平衡，新舊協定各跑一次
  features  FastMCP 4 功能地圖每張卡的實測證據
  era_errors 在新協定連線上呼叫 ctx.elicit()／ctx.sample() 的真實錯誤

跑法（repo 根）：
  uv run --script content/genai-intro/_spikes/spike_genai_mcp_fastmcp.py --out /tmp/wire.json
  uv run --script content/genai-intro/_spikes/spike_genai_mcp_fastmcp.py --inject   # 重錄並寫回 lesson.py／page_content.py
env：SPIKE_PORT_BASE（預設 9140，會用 base..base+9 共 10 個 port，全部只綁 127.0.0.1）
"""

import argparse
import asyncio
import importlib.metadata as md
import itertools
import json
import os
import platform
import re
import socket
import sys
import threading
import time
from pathlib import Path
from typing import Annotated

import httpx
import uvicorn
from fastmcp import Client, Context, FastMCP
from mcp.types import ElicitRequest, ElicitRequestFormParams, InputRequiredResult
from pydantic import Field

BASE = int(os.environ.get("SPIKE_PORT_BASE", "9140"))
HOST = "127.0.0.1"
ACCEPT = "application/json, text/event-stream"
MODERN = "2026-07-28"
KEEP_REQ = ("accept", "content-type", "mcp-protocol-version", "mcp-method", "mcp-name", "mcp-session-id",
            "last-event-id", "authorization")
KEEP_RESP = ("content-type", "mcp-session-id", "www-authenticate", "allow")
CUT = 1400  # 單筆 body 最多保留幾個字元（完整長度另記）


# ─────────────────────────── 側錄器與伺服器 ───────────────────────────
class Recorder:
    """ASGI 中介層：只側錄、不干擾。記下每個 HTTP 請求與回應（含串流回應的 body）。"""

    def __init__(self, app):
        self.app = app
        self.log = []
        self.t0 = time.perf_counter()

    def reset(self):
        self.log.clear()
        self.t0 = time.perf_counter()

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        hdr = {k.decode().lower(): v.decode() for k, v in scope["headers"]}
        q = scope.get("query_string", b"").decode()
        e = {"t": round(1000 * (time.perf_counter() - self.t0)), "m": scope["method"],
             "path": scope["path"] + (("?" + q) if q else ""),
             "rh": {k: v for k, v in hdr.items() if k in KEEP_REQ or k.startswith("mcp-param-")},
             "rb": b"", "st": None, "sh": {}, "sb": b""}
        self.log.append(e)

        async def _recv():
            m = await receive()
            if m.get("body"):
                e["rb"] += m["body"]
            return m

        async def _send(m):
            if m["type"] == "http.response.start":
                e["st"] = m["status"]
                e["sh"] = {k.decode().lower(): v.decode() for k, v in m.get("headers", [])
                           if k.decode().lower() in KEEP_RESP}
            elif m["type"] == "http.response.body":
                e["sb"] += m.get("body", b"")
            await send(m)

        return await self.app(scope, _recv, _send)

    def dump(self):
        out = []
        for e in self.log:
            rb, sb = e["rb"].decode(errors="replace"), e["sb"].decode(errors="replace").replace("\r\n", "\n")
            out.append({**{k: e[k] for k in ("t", "m", "path", "rh", "st", "sh")},
                        "rb": rb[:CUT], "rbn": len(e["rb"]), "sb": sb[:CUT], "sbn": len(e["sb"])})
        return out


def port_busy(port):
    with socket.socket() as s:
        return s.connect_ex((HOST, port)) == 0


def serve(app, port):
    if port_busy(port):
        raise SystemExit(f"port {port} 已被占用——換 SPIKE_PORT_BASE 再跑")
    server = uvicorn.Server(uvicorn.Config(app, host=HOST, port=port, log_level="error"))
    threading.Thread(target=server.run, daemon=True).start()
    for _ in range(100):
        if port_busy(port):
            break
        time.sleep(0.05)
    return f"http://{HOST}:{port}"


def make_calc():
    """所有情境共用的最小伺服器：一個 add 工具。"""
    mcp = FastMCP("calc", instructions="A tiny calculator.")

    @mcp.tool
    def add(a: int, b: int) -> int:
        """Add two integers."""
        return a + b

    return mcp


def sse_events(text):
    return [json.loads(line[5:].strip()) for line in text.replace("\r\n", "\n").splitlines()
            if line.startswith("data:") and line[5:].strip().startswith("{")]


# ─────────────────────────── 1. 五個年代 ───────────────────────────
def raw_streamable(url, version, send_version_header):
    """照 2025-03-26／2025-06-18 規格手寫：initialize → initialized → tools/list → tools/call → DELETE。"""
    with httpx.Client(timeout=10) as h:
        r = h.post(url, headers={"Accept": ACCEPT}, json={
            "jsonrpc": "2.0", "id": 1, "method": "initialize",
            "params": {"protocolVersion": version, "capabilities": {},
                       "clientInfo": {"name": f"raw-{version}", "version": "0"}}})
        sid = r.headers["mcp-session-id"]
        hd = {"Accept": ACCEPT, "Mcp-Session-Id": sid}
        if send_version_header:
            hd["MCP-Protocol-Version"] = version
        h.post(url, headers=hd, json={"jsonrpc": "2.0", "method": "notifications/initialized"})
        h.post(url, headers=hd, json={"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
        r = h.post(url, headers=hd, json={"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                                          "params": {"name": "add", "arguments": {"a": 2, "b": 3}}})
        result = sse_events(r.text)[-1]["result"]["structuredContent"]["result"]
        h.delete(url, headers=hd)
    return result


def raw_http_sse(base):
    """照 2024-11-05 規格手寫的 HTTP+SSE：先開 GET /sse，拿到 endpoint 事件，之後 POST 都只回 202，答案從 SSE 流回來。"""
    got = {"endpoint": None, "answers": {}}
    done = threading.Event()

    def reader():
        with httpx.Client(timeout=None) as h, h.stream("GET", base + "/sse", headers={"Accept": "text/event-stream"}) as r:
            ev = None
            for line in r.iter_lines():
                if line.startswith("event:"):
                    ev = line[6:].strip()
                elif line.startswith("data:"):
                    data = line[5:].strip()
                    if ev == "endpoint":
                        got["endpoint"] = data
                    else:
                        msg = json.loads(data)
                        got["answers"][msg.get("id")] = msg
                        if msg.get("id") == 3:
                            done.set()
                            return

    threading.Thread(target=reader, daemon=True).start()
    for _ in range(100):
        if got["endpoint"]:
            break
        time.sleep(0.05)
    ep = base + got["endpoint"]
    with httpx.Client(timeout=10) as h:
        for msg in (
            {"jsonrpc": "2.0", "id": 1, "method": "initialize",
             "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "raw-2024-11-05", "version": "0"}}},
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
            {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "add", "arguments": {"a": 2, "b": 3}}},
        ):
            h.post(ep, json=msg)
            time.sleep(0.15)  # 讓 SSE 事件依序流回來（側錄的時間軸比較好讀）
    done.wait(5)
    time.sleep(0.2)
    return got["answers"][3]["result"]["structuredContent"]["result"]


async def record_eras():
    rec = Recorder(make_calc().http_app())
    url = serve(rec, BASE) + "/mcp"
    sse_rec = Recorder(make_calc().http_app(transport="sse"))
    sse_base = serve(sse_rec, BASE + 1)
    eras = {}

    async def via_client(mode):
        rec.reset()
        async with Client(url, mode=mode) as c:
            names = [t.name for t in await c.list_tools()]
            r = await c.call_tool("add", {"a": 2, "b": 3})
            pv = c.protocol_version
        await asyncio.sleep(0.3)
        return {"protocol": pv, "tools": names, "result": r.data, "wire": rec.dump()}

    eras["2026-07-28"] = {**await via_client("auto"), "client": "FastMCP Client 4.0.8（預設 mode=auto）"}
    eras["2025-11-25"] = {**await via_client("legacy"), "client": "FastMCP Client 4.0.8（mode=legacy）"}
    for v, hdr in (("2025-06-18", True), ("2025-03-26", False)):
        rec.reset()
        res = await asyncio.to_thread(raw_streamable, url, v, hdr)
        await asyncio.sleep(0.2)
        eras[v] = {"protocol": v, "result": res, "wire": rec.dump(), "client": f"照 {v} 規格手寫的 httpx 客戶端"}
    sse_rec.reset()
    res = await asyncio.to_thread(raw_http_sse, sse_base)
    await asyncio.sleep(0.3)
    eras["2024-11-05"] = {"protocol": "2024-11-05", "result": res, "wire": sse_rec.dump(),
                          "client": "照 2024-11-05 規格手寫的 HTTP+SSE 客戶端（伺服器：http_app(transport=\"sse\")）"}
    for v, e in eras.items():
        w = e["wire"]
        print(f"[era {v}] result={e['result']} requests={len(w)} "
              f"with-session={sum(1 for x in w if 'mcp-session-id' in x['rh'] or 'session_id=' in x['path'])} "
              f"bytes={sum(x['rbn'] + x['sbn'] for x in w)} :: " + " | ".join(
                  f"{x['m']} {x['rh'].get('mcp-method') or (json.loads(x['rb']).get('method') if x['rb'].startswith('{') else '')} {x['st']}" for x in w))
    return eras, rec, url


# ─────────────────────────── 2. 封包檢視器的情境 ───────────────────────────
def make_files():
    mcp = FastMCP("files")

    @mcp.tool
    async def delete_file(path: str, ctx: Context) -> str | InputRequiredResult:
        """Delete a file after the user confirms."""
        if ctx.request_context.protocol_version == MODERN:
            # 新協定（守衛模式）：第一次進來還沒有答案 → 回傳「我需要輸入」，這一回合就結束了
            answers = ctx.input_responses
            if answers is None:
                return InputRequiredResult(result_type="input_required", input_requests={
                    "confirm": ElicitRequest(method="elicitation/create", params=ElicitRequestFormParams(
                        message=f"Really delete {path}?",
                        requested_schema={"type": "object", "properties": {"ok": {"type": "boolean"}}, "required": ["ok"]}))})
            resp = answers["confirm"]
            ok = resp.action == "accept" and bool(resp.content and resp.content.get("ok"))
        else:
            # 舊協定：工具停在這行，伺服器沿著連線反過來問客戶端
            r = await ctx.elicit(f"Really delete {path}?", response_type=bool)
            ok = r.action == "accept" and bool(r.data)
        return f"deleted {path}" if ok else "kept"

    return mcp


async def record_scenarios():
    sc = {}
    # 伺服器反問使用者：新（MRTR）vs 舊（server→client request）
    rec = Recorder(make_files().http_app())
    url = serve(rec, BASE + 2) + "/mcp"
    asked = []

    async def yes(message, response_type, params, ctx):
        asked.append(message)
        return response_type(**{k: True for k in params.requested_schema["properties"]})

    for key, mode in (("elicit_modern", "auto"), ("elicit_legacy", "legacy")):
        rec.reset()
        async with Client(url, mode=mode, elicitation_handler=yes) as c:
            r = await c.call_tool("delete_file", {"path": "notes.txt"})
        await asyncio.sleep(0.3)
        sc[key] = {"result": r.data, "wire": rec.dump()}
        print(f"[{key}] result={r.data} wire=" + " | ".join(f"{x['m']} {x['rh'].get('mcp-method', '')} {x['st']}" for x in sc[key]["wire"]))

    # 背景任務（io.modelcontextprotocol/tasks 擴充）
    from fastmcp.dependencies import Progress
    from fastmcp_tasks import TasksExtension
    slow = FastMCP("brewery")
    slow.add_extension(TasksExtension())

    @slow.tool(task=True)
    async def brew(cups: int, progress: Progress = Progress()) -> str:  # noqa: B008 -- FastMCP 的依賴注入寫法
        """Brew some cups of tea (0.4 s each)."""
        await progress.set_total(cups)
        for i in range(cups):
            await progress.set_message(f"cup {i + 1}")
            await asyncio.sleep(0.4)
            await progress.increment()
        return f"{cups} cups ready"

    trec = Recorder(slow.http_app())
    turl = serve(trec, BASE + 6) + "/mcp"
    t0 = time.perf_counter()
    async with Client(turl) as c:
        r = await c.call_tool("brew", {"cups": 3})
    sc["task_modern"] = {"result": r.data, "seconds": round(time.perf_counter() - t0, 2), "wire": trec.dump()}
    print(f"[task_modern] {r.data} in {sc['task_modern']['seconds']}s wire=" + " | ".join(x["rh"].get("mcp-method", "") for x in sc["task_modern"]["wire"]))

    # 路由 header（x-mcp-header）＋回應快取（cache_ttl）＋進度回報
    wx = FastMCP("weather", cache_ttl=300, cache_scope="public")

    @wx.tool
    async def forecast(tenant: Annotated[str, Field(json_schema_extra={"x-mcp-header": "Tenant"})],
                       city: str, ctx: Context) -> str:
        """Forecast for one tenant's city."""
        await ctx.report_progress(1, 2, "fetching")
        await ctx.report_progress(2, 2, "done")
        return f"{tenant}/{city}: sunny"

    wrec = Recorder(wx.http_app())
    wurl = serve(wrec, BASE + 7) + "/mcp"
    prog = []

    async def ph(p, total, msg):
        prog.append([p, total, msg])

    async with Client(wurl, cache=True, progress_handler=ph) as c:
        for _ in range(3):
            await c.list_tools()
        r = await c.call_tool("forecast", {"tenant": "acme", "city": "Taipei"})
    await asyncio.sleep(0.2)
    sc["route_cache"] = {"result": r.data, "list_tools_calls": 3, "progress": prog, "wire": wrec.dump()}
    print(f"[route_cache] {r.data} progress={prog} wire=" + " | ".join(
        f"{x['rh'].get('mcp-method')} {[k for k in x['rh'] if k.startswith('mcp-param')]}" for x in sc["route_cache"]["wire"]))
    return sc


# ─────────────────────────── 3. 手刻一發請求：四旋鈕全組合 ───────────────────────────
GRID_KNOBS = {
    "pv": {"none": None, "2026": MODERN, "2025": "2025-11-25", "2099": "2099-01-01"},
    "mm": {"none": None, "ok": "tools/call", "bad": "tools/list"},
    "mn": {"none": None, "ok": "add", "bad": "sub"},
    "meta": {"none": None, "2026": MODERN, "2025": "2025-11-25", "2099": "2099-01-01", "nocaps": "nocaps"},
}


def record_grid(url):
    out = {}
    with httpx.Client(timeout=10) as h:
        for pv, mm, mn, me in itertools.product(*(GRID_KNOBS[k] for k in ("pv", "mm", "mn", "meta"))):
            hd = {"Accept": ACCEPT}
            if GRID_KNOBS["pv"][pv]:
                hd["MCP-Protocol-Version"] = GRID_KNOBS["pv"][pv]
            if GRID_KNOBS["mm"][mm]:
                hd["Mcp-Method"] = GRID_KNOBS["mm"][mm]
            if GRID_KNOBS["mn"][mn]:
                hd["Mcp-Name"] = GRID_KNOBS["mn"][mn]
            params = {"name": "add", "arguments": {"a": 2, "b": 3}}
            if me == "nocaps":
                params["_meta"] = {"io.modelcontextprotocol/protocolVersion": MODERN}
            elif GRID_KNOBS["meta"][me]:
                params["_meta"] = {"io.modelcontextprotocol/protocolVersion": GRID_KNOBS["meta"][me],
                                   "io.modelcontextprotocol/clientCapabilities": {}}
            r = h.post(url, json={"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": params}, headers=hd)
            out[f"{pv}|{mm}|{mn}|{me}"] = [r.status_code, r.text[:360]]
        # 同一個端點，舊協定用的 GET／DELETE（沒有 session）
        extra = {}
        for m in ("GET", "DELETE"):
            r = h.request(m, url, headers={"Accept": ACCEPT, "MCP-Protocol-Version": MODERN})
            extra[m] = [r.status_code, r.headers.get("allow", "")]
    from collections import Counter
    for (st, msg), n in Counter((v[0], v[1][:110]) for v in out.values()).most_common():
        print(f"[grid] {n:3d} × {st} {msg}")
    # 壓縮：相同回應只存一次（180 組合只有個位數種回應）
    uniq = []
    idx = {}
    for k, v in out.items():
        key = json.dumps(v)
        if key not in idx:
            idx[key] = len(uniq)
            uniq.append(v)
        out[k] = idx[key]
    print(f"[grid] GET/DELETE with modern header → {extra}")
    return {"responses": uniq, "map": out, "get_delete": extra}


# ─────────────────────────── 4. 兩台副本＋負載平衡 ───────────────────────────
async def record_replicas():
    ra, rb = Recorder(make_calc().http_app()), Recorder(make_calc().http_app())
    ups = [serve(ra, BASE + 4), serve(rb, BASE + 5)]
    state = {"n": 0, "policy": "round-robin", "sticky": {}, "trail": []}

    async def lb(scope, receive, send):
        if scope["type"] != "http":
            return
        hdr = {k.decode().lower(): v.decode() for k, v in scope["headers"]}
        sid = hdr.get("mcp-session-id")
        if state["policy"] == "sticky" and sid in state["sticky"]:
            i = state["sticky"][sid]
        else:
            i = state["n"] % 2
            state["n"] += 1
        body = b""
        while True:
            m = await receive()
            body += m.get("body", b"")
            if not m.get("more_body"):
                break
        fwd = [(k, v) for k, v in hdr.items() if k not in ("host", "content-length")]
        async with httpx.AsyncClient(timeout=None) as client:
            req = client.build_request(scope["method"], ups[i] + scope["path"], headers=fwd, content=body)
            resp = await client.send(req, stream=True)
            new_sid = resp.headers.get("mcp-session-id")
            if new_sid and state["policy"] == "sticky":
                state["sticky"][new_sid] = i  # 黏著：記住這把 session 是哪一台發的
            mm = hdr.get("mcp-method") or ""
            if not mm and body.startswith(b"{"):
                mm = json.loads(body).get("method", "")
            state["trail"].append({"replica": "AB"[i], "m": scope["method"], "method": mm or ("(GET stream)" if scope["method"] == "GET" else scope["method"]),
                                   "session": (sid or "")[:8], "st": resp.status_code})
            await send({"type": "http.response.start", "status": resp.status_code,
                        "headers": [(k.encode(), v.encode()) for k, v in resp.headers.items()
                                    if k not in ("content-length", "transfer-encoding")]})
            async for chunk in resp.aiter_raw():
                await send({"type": "http.response.body", "body": chunk, "more_body": True})
            await send({"type": "http.response.body", "body": b"", "more_body": False})
            await resp.aclose()

    url = serve(lb, BASE + 3) + "/mcp"
    out = {}
    for policy in ("round-robin", "sticky"):
        for mode in ("auto", "legacy"):
            state.update(n=0, policy=policy, sticky={}, trail=[])
            ra.reset()
            rb.reset()
            key = f"{policy}|{'modern' if mode == 'auto' else 'legacy'}"
            try:
                async with Client(url, mode=mode, timeout=5, init_timeout=5) as c:
                    await c.list_tools()
                    r = await c.call_tool("add", {"a": 2, "b": 3})
                res = {"ok": True, "result": r.data}
            except Exception as e:
                res = {"ok": False, "error": f"{type(e).__name__}: {str(e)[:200]}"}
            await asyncio.sleep(0.3)
            wrong = [x for x in (ra.dump() + rb.dump()) if x["st"] == 404]
            res["trail"] = list(state["trail"])
            res["http404_body"] = wrong[0]["sb"][:200] if wrong else ""
            out[key] = res
            print(f"[replicas {key}] {res.get('result', res.get('error'))} :: " + " | ".join(
                f"{t['replica']}:{t['method']}→{t['st']}" for t in res["trail"]) + (f" :: 404 body={res['http404_body']}" if wrong else ""))
    return out


# ─────────────────────────── 5. 功能地圖的證據 ───────────────────────────
async def record_features(calc_url):
    ev = {}

    # mount：多台合成一台，工具名自動加命名空間
    hub, w, c = FastMCP("hub"), FastMCP("weather"), make_calc()

    @w.tool
    def forecast(city: str) -> str:
        """Weather forecast for a city."""
        return f"{city}: sunny"

    hub.mount(w, namespace="weather")
    hub.mount(c, namespace="calc")
    async with Client(hub) as cl:
        ev["mount"] = {"tools": [t.name for t in await cl.list_tools()],
                       "call": (await cl.call_tool("weather_forecast", {"city": "Taipei"})).data}

    # create_proxy：把別台（這裡是 calc HTTP 伺服器）轉成自己的工具
    from fastmcp.server import create_proxy
    back = Recorder(make_calc().http_app())
    back_url = serve(back, BASE + 8) + "/mcp"
    front = create_proxy(back_url, name="front")
    async with Client(front) as cl:
        ev["proxy"] = {"tools": [t.name for t in await cl.list_tools()],
                       "call": (await cl.call_tool("add", {"a": 1, "b": 2})).data}
    ev["proxy"]["backend_saw"] = [x["rh"].get("mcp-method", x["m"]) for x in back.dump()]

    # from_fastapi / from_openapi：現成 REST API 直接變工具
    import httpx2
    from fastapi import FastAPI
    app = FastAPI(title="shop")
    items = {1: {"name": "tea", "price": 50}, 2: {"name": "coffee", "price": 80}}

    @app.get("/items/{item_id}", operation_id="get_item")
    def get_item(item_id: int):
        return items[item_id]

    @app.get("/items", operation_id="list_items")
    def list_items(max_price: int = 100):
        return [v for v in items.values() if v["price"] <= max_price]

    @app.post("/orders", operation_id="create_order")
    def create_order(item_id: int, qty: int = 1):
        return {"ok": True, "total": items[item_id]["price"] * qty}

    async with Client(FastMCP.from_fastapi(app=app)) as cl:
        ev["from_fastapi"] = {"tools": [[t.name, sorted(t.input_schema.get("properties", {}))] for t in await cl.list_tools()],
                              "call": (await cl.call_tool("list_items", {"max_price": 60})).data}
    api = httpx2.AsyncClient(transport=httpx2.ASGITransport(app=app), base_url="http://shop")
    async with Client(FastMCP.from_openapi(openapi_spec=app.openapi(), client=api, name="shop")) as cl:
        ev["from_openapi"] = {"tools": [t.name for t in await cl.list_tools()],
                              "call": (await cl.call_tool("create_order", {"item_id": 2, "qty": 3})).data}

    # BM25SearchTransform：30 個工具的目錄 → 模型只看到兩個
    from fastmcp.server.transforms.search import BM25SearchTransform
    big = FastMCP("big", transforms=[BM25SearchTransform()])
    topics = ["weather forecast for a city", "convert currency", "send an email", "translate text",
              "book a meeting room", "search the product catalog", "create an invoice",
              "delete a database record", "list calendar events", "get stock price"]
    for i, d in enumerate(topics * 3):
        def f(q: str) -> str:
            return q
        big.tool(f, name=f"tool_{i:02d}", description=d)
    async with Client(big) as cl:
        listed = [t.name for t in await cl.list_tools()]
        r = await cl.call_tool("search_tools", {"query": "weather in Taipei"})
        hits = r.data if isinstance(r.data, list) else json.loads(r.content[0].text)
        ev["search"] = {"catalog": 30, "listed": listed,
                        "top": [[h["name"], h["description"]] for h in hits[:3]]}

    # Middleware：每次呼叫都記一筆（這裡記耗時）
    from fastmcp.server.middleware import Middleware, MiddlewareContext
    logs = []

    class Timing(Middleware):
        async def on_call_tool(self, context: MiddlewareContext, call_next):
            t0 = time.perf_counter()
            result = await call_next(context)
            logs.append(f"{context.method} {context.message.name} {1000 * (time.perf_counter() - t0):.1f} ms")
            return result

    mw = make_calc()
    mw.add_middleware(Timing())
    async with Client(mw) as cl:
        await cl.call_tool("add", {"a": 1, "b": 2})
        await cl.call_tool("add", {"a": 3, "b": 4})
    ev["middleware"] = {"log": logs}

    # 認證＋scope：沒權限的人看不到工具
    from fastmcp.server.auth import StaticTokenVerifier, require_scopes
    verifier = StaticTokenVerifier(tokens={"guest-token": {"client_id": "guest", "scopes": ["read"]},
                                           "admin-token": {"client_id": "admin", "scopes": ["read", "admin"]}})
    sec = FastMCP("shop-admin", auth=verifier)

    @sec.tool
    def read_menu() -> str:
        """Read today's menu."""
        return "menu"

    @sec.tool(auth=require_scopes("admin"))
    def change_price(item: str, price: int) -> str:
        """Change an item's price (admin only)."""
        return f"{item}={price}"

    sec_url = serve(sec.http_app(), BASE + 9) + "/mcp"
    ev["auth"] = {}
    for tok in ("guest-token", "admin-token"):
        async with Client(sec_url, auth=tok) as cl:
            ev["auth"][tok] = [t.name for t in await cl.list_tools()]
    async with httpx.AsyncClient() as h:
        r = await h.post(sec_url, json={}, headers={"Accept": ACCEPT})
    ev["auth"]["no_token"] = [r.status_code, r.headers.get("www-authenticate", "")]

    # SessionId：傳輸無狀態，應用照樣記得（換一條連線購物車還在）
    from fastmcp.server.sessions import SessionId, SessionProvider, get_session
    cart = FastMCP("cart")
    cart.add_provider(SessionProvider())

    @cart.tool
    async def add_to_cart(session_id: SessionId, item: str) -> list[str]:
        """Add an item to this session's cart."""
        s = await get_session(session_id)
        got = await s.get("items", default=[])
        got.append(item)
        await s.set("items", got)
        return got

    async with Client(cart) as cl:
        names = [t.name for t in await cl.list_tools()]
        sid = (await cl.call_tool("create_session", {})).data
        await cl.call_tool("add_to_cart", {"session_id": sid, "item": "tea"})
    async with Client(cart) as cl2:
        again = (await cl2.call_tool("add_to_cart", {"session_id": sid, "item": "cake"})).data
        try:
            await cl2.call_tool("add_to_cart", {"session_id": "guess-1234", "item": "x"})
            guess = "（沒有報錯）"
        except Exception as e:
            guess = f"{type(e).__name__}: {e}"
    ev["sessions"] = {"tools": names, "new_connection": again, "guess": guess}

    # ClientGroup：一個 client 同時接多台，工具名自動分流
    from fastmcp import ClientGroup
    a, b = make_calc(), FastMCP("weather")

    @b.tool
    def forecast2(city: str) -> str:
        """Weather forecast."""
        return f"{city}: rain"

    async with ClientGroup({"calc": Client(a), "weather": Client(b)}) as g:
        ev["client_group"] = {"tools": [t.name for t in await g.list_tools()],
                              "call": (await g.call_tool("calc_add", {"a": 20, "b": 22})).data}

    # 資源模板的路徑安全（4.0 預設開）＋參數自動完成
    docs = FastMCP("docs")

    @docs.resource("docs://{name}")
    def read_doc(name: str) -> str:
        """Read one document."""
        return f"content of {name}"

    from mcp.types import PromptReference

    @docs.prompt
    def write_poem(theme: str) -> str:
        """Write a poem."""
        return f"Write a poem about {theme}"

    @docs.completion
    def complete(ref, argument, context):
        if isinstance(ref, PromptReference) and argument.name == "theme":
            return [o for o in ("tea", "taipei", "typhoon", "cat") if o.startswith(argument.value)]
        return None

    async with Client(docs) as cl:
        ok = (await cl.read_resource("docs://intro"))[0].text
        probes = {}
        for bad in ("docs://..%2Fsecret", "docs://%2Fetc%2Fpasswd"):
            try:
                await cl.read_resource(bad)
                probes[bad] = "（讀到了）"
            except Exception as e:
                probes[bad] = f"{type(e).__name__}: {str(e)[:120]}"
        comp = await cl.complete(ref=PromptReference(type="ref/prompt", name="write_poem"),
                                 argument={"name": "theme", "value": "t"})
    ev["resources"] = {"ok": ok, "traversal": probes}
    ev["completion"] = {"typed": "t", "values": list(comp.values)}

    # FastMCP Apps：discover 回應裡看得到 UI 擴充的宣告
    async with httpx.AsyncClient() as h:
        r = await h.post(calc_url, json={"jsonrpc": "2.0", "id": 1, "method": "server/discover", "params": {"_meta": {
            "io.modelcontextprotocol/protocolVersion": MODERN, "io.modelcontextprotocol/clientCapabilities": {}}}},
            headers={"Accept": ACCEPT, "MCP-Protocol-Version": MODERN, "Mcp-Method": "server/discover"})
    ev["apps"] = {"extensions": r.json()["result"]["capabilities"].get("extensions", {})}
    for k, v in ev.items():
        print(f"[feature {k}] {json.dumps(v, ensure_ascii=False)[:300]}")
    return ev


async def record_era_errors():
    """新協定連線上沒有「伺服器反過來問客戶端」的通道：ctx.elicit() 與 ctx.sample() 的真實下場。"""
    m = FastMCP("era")

    @m.tool
    async def confirm(ctx: Context) -> str:
        """Ask the user for a yes/no."""
        r = await ctx.elicit("ok?", response_type=bool)
        return str(r.action)

    @m.tool
    async def summarize(text: str, ctx: Context) -> str:
        """Summarize with the client's LLM."""
        r = await ctx.sample(text)
        return str(r)

    async def yes(message, response_type, params, ctx):
        return response_type(value=True)

    out = {}
    for mode in ("auto", "legacy"):
        async with Client(m, mode=mode, elicitation_handler=yes) as c:
            for name, args in (("confirm", {}), ("summarize", {"text": "hi"})):
                try:
                    r = await c.call_tool(name, args)
                    out[f"{name}|{mode}"] = f"OK: {r.data}"
                except Exception as e:
                    out[f"{name}|{mode}"] = f"{type(e).__name__}: {e}"
    for k, v in out.items():
        print(f"[era_errors {k}] {v}")
    return out


# ─────────────────────────── 主程式 ───────────────────────────
async def main(args):
    t0 = time.perf_counter()
    eras, _rec, calc_url = await record_eras()
    grid = await asyncio.to_thread(record_grid, calc_url)
    data = {
        "meta": {"date": time.strftime("%Y-%m-%d"), "fastmcp": md.version("fastmcp"), "mcp": md.version("mcp"),
                 "fastmcp_tasks": md.version("fastmcp-tasks"), "python": platform.python_version()},
        "eras": eras,
        "scenarios": await record_scenarios(),
        "grid": grid,
        "replicas": await record_replicas(),
        "features": await record_features(calc_url),
        "era_errors": await record_era_errors(),
    }
    print(f"[meta] {data['meta']} in {time.perf_counter() - t0:.1f}s")
    blob = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    assert '"""' not in blob, "錄音裡出現三引號，lesson.py 的 r-string 會被截斷"
    assert not re.search(r"\b(10|192\.168|172\.(1[6-9]|2\d|3[01]))\.\d+\.\d+", blob), "錄音裡混進內網位址"
    if args.out:
        Path(args.out).write_text(json.dumps(data, ensure_ascii=False, indent=1))
        print("wrote", args.out, len(blob), "bytes (compact)")
    if args.inject:
        inject(data)


def inject(data):
    """把錄音寫回課程：lesson.py 的 WIRE_JSON 常數、page_content.py 的 hero 資料。"""
    lesson_dir = Path(__file__).resolve().parents[1] / "genai-mcp-fastmcp"
    lp = lesson_dir / "lesson.py"
    blob = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    s = lp.read_text()
    s2, n = re.subn(r'WIRE_JSON = r"""(.*?)"""', lambda _m: f'WIRE_JSON = r"""{blob}"""', s, count=1, flags=re.DOTALL)
    assert n == 1, "lesson.py 找不到 WIRE_JSON 佔位"
    lp.write_text(s2)
    hero = {v: {"client": e["client"], "protocol": e["protocol"], "result": e["result"], "wire": e["wire"]}
            for v, e in data["eras"].items()}
    pp = lesson_dir / "page_content.py"
    s = pp.read_text()
    js = json.dumps(hero, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    s2, n = re.subn(r"const ERAS = /\*ERAS_BEGIN\*/.*?/\*ERAS_END\*/", lambda _m: f"const ERAS = /*ERAS_BEGIN*/{js}/*ERAS_END*/", s, count=1, flags=re.DOTALL)
    assert n == 1, "page_content.py 找不到 const ERAS = /*ERAS_BEGIN*/ 佔位"
    pp.write_text(s2)
    print("injected into", lp, "and", pp)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="")
    ap.add_argument("--inject", action="store_true")
    a = ap.parse_args()
    if not (a.out or a.inject):
        a.out = "spike_genai_mcp_fastmcp.json"
    asyncio.run(main(a))
    sys.stdout.flush()
    os._exit(0)  # uvicorn 背景執行緒＋直譯器收尾偶發 double free（3.14 實測），直接離開
