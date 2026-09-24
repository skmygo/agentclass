# /// script
# requires-python = ">=3.11"
# dependencies = ["claude-agent-sdk==0.2.159"]
# ///
"""genai-agent-sdk 課（補充 C）的素材錄製 spike：用 Claude Agent SDK 真的跑任務、錄完整訊息串。

每一段都在一個「全新複製」的小專案（shop-demo：一個有 bug 的購物車＋unittest）裡跑，
錄下 SystemMessage(init) → AssistantMessage(ToolUseBlock) → UserMessage(ToolResultBlock) → … → ResultMessage，
跑完再用 `python3 -m unittest` 檢查專案真實狀態（測試過了沒、檔案被改成什麼）。

段落（第一個參數；可多個，all＝全部）：
  hero    同一個任務 × 五種設定：預設／allowed_tools 放行／+PreToolUse hook／plan 模式／can_use_tool 審批
  plan    plan 模式＋can_use_tool：ExitPlanMode 交給你的函式核准，核准後才動手（對照 hero 的 plan 空轉）
  extras  自訂工具（@tool＋create_sdk_mcp_server）、subagent（AgentDefinition）、session resume
  gate    權限閘門的關鍵規則驗證（bypass 也擋得住的 deny 規則與 hook、allowed_tools 不約束 bypass…）
  errors  撞真實錯誤訊息（測驗用）：string prompt＋can_use_tool、resume 不存在的 session、max_turns 用完
  free    免費路徑：ANTHROPIC_BASE_URL 指向 Anthropic 相容端點（Ollama／vLLM）跑開源模型

環境變數（全部可選）：
  SPIKE_OUT         輸出目錄（預設 ./agent_sdk_runs）
  SDK_MODEL         Claude 模型（預設 claude-haiku-4-5）
  FREE_BASE_URL     free 段：Anthropic 相容端點的根網址（預設 http://localhost:11434＝本機 Ollama）
  FREE_MODEL        free 段模型名（預設 qwen3.5:2b）
  FREE_EXTRA_BODY   free 段：塞進每個請求的額外 JSON（CLAUDE_CODE_EXTRA_BODY；vLLM 關 thinking 用）

跑法（在「乾淨」的環境跑：別繼承外層 Claude Code session 的 CLAUDE_* 環境變數）：
  env -i HOME="$HOME" PATH="$PATH" LANG=C.UTF-8 uv run --script spike_genai_agent_sdk.py hero
Claude 段需要本機 claude CLI 已登入或 ANTHROPIC_API_KEY（會真的計費，ResultMessage.total_cost_usd 會印出來）。
"""

import asyncio
import dataclasses
import difflib
import json
import os
import re
import shutil
import subprocess
import sys
import time
import warnings
from pathlib import Path
from urllib.parse import urlparse

from claude_agent_sdk import (
    AgentDefinition,
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    HookMatcher,
    ResultMessage,
    SystemMessage,
    TaskNotificationMessage,
    TaskStartedMessage,
    TextBlock,
    ThinkingBlock,
    ToolResultBlock,
    ToolUseBlock,
    UserMessage,
    create_sdk_mcp_server,
    query,
    tool,
)
from claude_agent_sdk.types import PermissionResultAllow, PermissionResultDeny

OUT = Path(os.environ.get("SPIKE_OUT", "agent_sdk_runs")).resolve()
MODEL = os.environ.get("SDK_MODEL", "claude-haiku-4-5")
SHOW_PATH = "~/shop-demo"  # 錄到的路徑一律換成這個（不把本機路徑寫進課程）
HOME = str(Path.home())
USER = Path.home().name
# free 段：Claude Code 的錯誤訊息會把端點的 host:port 印出來（"check your inference gateway (host:port)"）
FREE_HOST = urlparse(os.environ.get("FREE_BASE_URL", "")).netloc


def sanitize(s: str) -> str:
    """家目錄、使用者名稱一律遮掉（ls -la 的擁有者欄、uv 快取路徑、plan 檔路徑都會帶出來）。"""
    s = s.replace(HOME, "~")
    if FREE_HOST:
        s = s.replace(FREE_HOST, "<你的端點>")
    return re.sub(rf"\b{re.escape(USER)}\b", "me", s)

# ── 示範專案：一個有 bug 的購物車 ─────────────────────────────────────
CART_PY = '''\
def subtotal(items):
    """items 是 (單價, 數量) 的清單，回傳小計。"""
    return sum(price * qty for price, qty in items)


def total(items, coupon_pct=0):
    """套用折扣券後的應付金額（coupon_pct=10 代表打九折），四捨五入到整數。"""
    s = subtotal(items)
    return round(s * coupon_pct / 100)
'''

TEST_PY = '''\
import unittest

from shop.cart import subtotal, total

ITEMS = [(100, 2), (50, 1)]


class TestCart(unittest.TestCase):
    def test_subtotal(self):
        self.assertEqual(subtotal(ITEMS), 250)

    def test_no_coupon(self):
        self.assertEqual(total(ITEMS), 250)

    def test_coupon_10(self):
        self.assertEqual(total(ITEMS, coupon_pct=10), 225)


if __name__ == "__main__":
    unittest.main()
'''

TASK = "這個專案的測試沒過。找出 bug、修好它，然後跑測試確認全部通過。最後用繁體中文一句話告訴我你改了什麼。"


def make_project(name: str) -> Path:
    d = OUT / "work" / name / "shop-demo"
    if d.exists():
        shutil.rmtree(d)
    (d / "shop").mkdir(parents=True)
    (d / "tests").mkdir()
    (d / "shop" / "__init__.py").write_text("")
    (d / "tests" / "__init__.py").write_text("")
    (d / "shop" / "cart.py").write_text(CART_PY)
    (d / "tests" / "test_cart.py").write_text(TEST_PY)
    (d / "build").mkdir()
    (d / "build" / "tmp.txt").write_text("build artifact\n")
    return d


def project_state(d: Path) -> dict:
    """跑完之後的真實狀態：測試結果與 cart.py 的 diff（不信模型的自述）。"""
    r = subprocess.run(["python3", "-m", "unittest", "discover", "-q"],
                       cwd=d, capture_output=True, text=True, timeout=60, check=False)
    new = (d / "shop" / "cart.py").read_text()
    diff = "".join(difflib.unified_diff(CART_PY.splitlines(True), new.splitlines(True),
                                        "a/shop/cart.py", "b/shop/cart.py"))
    tail = (r.stderr or r.stdout).strip().splitlines()[-1:] or [""]
    return {"tests_pass": r.returncode == 0, "unittest_tail": tail[0], "diff": diff,
            "build_exists": (d / "build").exists()}


def clean(s, d: Path | None):
    if not isinstance(s, str):
        s = json.dumps(s, ensure_ascii=False, default=str)
    if d is not None:
        s = s.replace(str(d), SHOW_PATH)
    s = s.replace(str(OUT), "~")
    return sanitize(s)


def tool_result_text(content) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    parts = []
    for c in content:
        if isinstance(c, dict) and c.get("type") == "text":
            parts.append(c.get("text", ""))
        else:
            parts.append(json.dumps(c, ensure_ascii=False, default=str))
    return "\n".join(parts)


class Recorder:
    """把訊息串轉成課程要用的精簡事件列（同時留一份原始 dump）。"""

    def __init__(self, name: str, d: Path | None):
        self.name, self.d = name, d
        self.events: list[dict] = []
        self.raw: list[dict] = []
        self.t0 = time.time()
        self.seen_usage: set[str] = set()
        self.calls: list[dict] = []  # 每次 API 呼叫一筆 usage（以 message_id 去重）
        self.tasks_active: set[str] = set()  # 背景子代理（2.1.281 起 Agent 工具預設丟背景）
        self.last_task_done = -1.0
        self.last_result = -1.0

    def waiting_for_tasks(self) -> bool:
        """還有背景任務沒回報，或回報後還沒跑完接著的那一輪 → 要繼續收訊息。"""
        return bool(self.tasks_active) or self.last_task_done > self.last_result

    def note(self, kind: str, **kw):
        kw = {k: (clean(v, self.d) if isinstance(v, str) else v) for k, v in kw.items()}
        self.events.append({"kind": kind, "t": round(time.time() - self.t0, 2), **kw})

    def add(self, m):
        d = dataclasses.asdict(m) if dataclasses.is_dataclass(m) else {"repr": repr(m)}
        d["_type"] = type(m).__name__
        self.raw.append(d)
        t = round(time.time() - self.t0, 2)
        if isinstance(m, TaskStartedMessage):
            self.tasks_active.add(m.task_id)
            self.events.append({"kind": "task", "t": t, "phase": "started", "description": m.description,
                                "task_type": m.task_type})
            return
        if isinstance(m, TaskNotificationMessage):
            self.tasks_active.discard(m.task_id)
            self.last_task_done = t
            self.events.append({"kind": "task", "t": t, "phase": m.status,
                                "summary": clean(m.summary or "", self.d)[:600]})
            return
        if isinstance(m, SystemMessage):
            if m.subtype == "init":
                data = m.data
                self.events.append({"kind": "init", "t": t, "model": data.get("model"),
                                    "permissionMode": data.get("permissionMode"),
                                    "tools": data.get("tools", []),
                                    "mcp_servers": data.get("mcp_servers", []),
                                    "agents": data.get("agents", []),
                                    "session_id": data.get("session_id"),
                                    "cwd": clean(data.get("cwd", ""), self.d),
                                    "claude_code_version": data.get("claude_code_version")})
            return
        if isinstance(m, AssistantMessage):
            mid = m.message_id or ""
            if m.usage and mid and mid not in self.seen_usage:
                self.seen_usage.add(mid)
                u = m.usage
                self.calls.append({"message_id": mid[-8:], "model": m.model,
                                   "parent": bool(m.parent_tool_use_id),
                                   "input": u.get("input_tokens", 0),
                                   "cache_read": u.get("cache_read_input_tokens", 0),
                                   "cache_write": u.get("cache_creation_input_tokens", 0),
                                   "output": u.get("output_tokens", 0)})
            for b in m.content:
                if isinstance(b, TextBlock) and b.text.strip():
                    self.events.append({"kind": "text", "t": t, "text": clean(b.text, self.d),
                                        "sub": bool(m.parent_tool_use_id)})
                elif isinstance(b, ToolUseBlock):
                    self.events.append({"kind": "tool_use", "t": t, "id": b.id[-6:], "name": b.name,
                                        "input": json.loads(clean(b.input, self.d)),
                                        "sub": bool(m.parent_tool_use_id)})
                elif isinstance(b, ThinkingBlock):
                    pass  # 思考內容預設不回傳（空字串），不錄
            if m.error:
                self.events.append({"kind": "assistant_error", "t": t, "error": m.error})
            return
        if isinstance(m, UserMessage):
            if isinstance(m.content, list):
                for b in m.content:
                    if isinstance(b, ToolResultBlock):
                        txt = clean(tool_result_text(b.content), self.d)
                        if len(txt) > 1500:
                            txt = txt[:1500] + f"\n…（以下省略 {len(txt) - 1500} 字）"
                        self.events.append({"kind": "tool_result", "t": t, "id": b.tool_use_id[-6:],
                                            "is_error": bool(b.is_error), "text": txt,
                                            "sub": bool(m.parent_tool_use_id)})
            return
        if isinstance(m, ResultMessage):
            self.last_result = t
            self.events.append({"kind": "result", "t": t, "subtype": m.subtype, "is_error": m.is_error,
                                "num_turns": m.num_turns, "duration_ms": m.duration_ms,
                                "duration_api_ms": m.duration_api_ms,
                                "total_cost_usd": m.total_cost_usd, "stop_reason": m.stop_reason,
                                "terminal_reason": m.terminal_reason,
                                "result": clean(m.result or "", self.d),
                                "permission_denials": json.loads(clean(m.permission_denials or [], self.d)),
                                "errors": m.errors, "usage": m.usage, "model_usage": m.model_usage,
                                "session_id": m.session_id})
            return
        # RateLimitEvent（訂閱用量，私人資訊）與其他事件不錄進課程


def base_opts(d: Path | None, **kw) -> ClaudeAgentOptions:
    """共同設定：不載入本機任何 settings／CLAUDE.md／外部 MCP，讓 trace 只反映這支程式的設定。"""
    o = {"model": MODEL, "cwd": str(d) if d else None, "setting_sources": [], "strict_mcp_config": True,
         "max_turns": 20, "max_budget_usd": 0.6}
    o.update(kw)
    return ClaudeAgentOptions(**o)


async def run(name: str, prompt: str, opts: ClaudeAgentOptions, d: Path | None, rec: Recorder | None = None):
    rec = rec or Recorder(name, d)
    print(f"\n=== {name} ===", flush=True)
    try:
        async with ClaudeSDKClient(options=opts) as client:
            await client.query(prompt)
            async for m in client.receive_response():
                rec.add(m)
            # 背景子代理：主代理那一輪先收工（ResultMessage 先到），子代理跑完才注入通知、再跑一輪
            for _ in range(4):
                if not rec.waiting_for_tasks():
                    break
                async with asyncio.timeout(300):
                    async for m in client.receive_response():
                        rec.add(m)
    except Exception as e:  # 錯誤也是素材
        rec.note("exception", etype=type(e).__name__, text=str(e)[:800])
        print("  EXC", type(e).__name__, str(e)[:300])
    for ev in rec.events:
        k = ev["kind"]
        if k == "tool_use":
            print(f"  → {ev['name']} {json.dumps(ev['input'], ensure_ascii=False)[:160]}")
        elif k == "tool_result":
            print(f"  ← {'ERR ' if ev['is_error'] else ''}{ev['text'][:160]!r}")
        elif k in ("hook", "callback"):
            print(f"  ⚑ {k}: {json.dumps(ev, ensure_ascii=False)[:200]}")
        elif k == "text":
            print(f"  💬 {ev['text'][:200]!r}")
        elif k == "result":
            print(f"  ■ {ev['subtype']} turns={ev['num_turns']} cost=${ev['total_cost_usd']} "
                  f"{ev['duration_ms']}ms denials={len(ev['permission_denials'])}")
    out = {"name": name, "model": MODEL, "prompt": prompt, "events": rec.events, "calls": rec.calls}
    if d is not None:
        out["state"] = project_state(d)
        print("  state:", out["state"]["tests_pass"], out["state"]["unittest_tail"])
    (OUT / "raw").mkdir(parents=True, exist_ok=True)
    (OUT / "raw" / f"{name}.json").write_text(json.dumps(rec.raw, ensure_ascii=False, indent=1, default=str))
    return out


# ═══ hero：同一個任務 × 五種設定 ═══════════════════════════════════
async def part_hero():
    runs = []
    # 1) 預設：什麼都沒允許（headless 沒有人可以按「允許」）
    d = make_project("h1_default")
    runs.append(await run("h1_default", TASK, base_opts(d), d))

    # 2) allowed_tools 放行 Read／Edit／Bash
    d = make_project("h2_allowed")
    runs.append(await run("h2_allowed", TASK, base_opts(d, allowed_tools=["Read", "Edit", "Bash"]), d))

    # 3) 同 2，再加 PreToolUse hook：稽核每一次工具呼叫＋Bash 只准跑 unittest
    d = make_project("h3_hook")
    rec = Recorder("h3_hook", d)

    async def audit(inp, tool_use_id, ctx):
        rec.note("hook", hook="audit", tool=inp.get("tool_name"), decision="pass")
        return {}

    async def bash_guard(inp, tool_use_id, ctx):
        cmd = inp["tool_input"].get("command", "")
        if not cmd.strip().startswith("python3 -m unittest"):
            reason = "這個專案只准用 `python3 -m unittest` 跑測試；其他 shell 指令一律擋下。"
            rec.note("hook", hook="bash_guard", tool="Bash", command=cmd, decision="deny", reason=reason)
            return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                           "permissionDecisionReason": reason}}
        rec.note("hook", hook="bash_guard", tool="Bash", command=cmd, decision="pass")
        return {}

    hooks = {"PreToolUse": [HookMatcher(matcher=None, hooks=[audit]),
                            HookMatcher(matcher="Bash", hooks=[bash_guard])]}
    runs.append(await run("h3_hook", TASK, base_opts(d, allowed_tools=["Read", "Edit", "Bash"], hooks=hooks), d, rec))

    # 4) plan 模式：只看、只規劃
    d = make_project("h4_plan")
    runs.append(await run("h4_plan", TASK, base_opts(d, permission_mode="plan"), d))

    # 5) can_use_tool：沒被規則放行的呼叫都來問你的函式
    d = make_project("h5_callback")
    rec5 = Recorder("h5_callback", d)

    async def approver(tool_name, tool_input, ctx):
        path = str(tool_input.get("file_path", ""))
        if tool_name in ("Edit", "Write") and "/shop/" in path:
            rec5.note("callback", tool=tool_name, target=path, decision="allow")
            return PermissionResultAllow()
        msg = "使用者拒絕：這次只准修改 shop/ 底下的程式碼，不准執行任何指令。"
        rec5.note("callback", tool=tool_name, target=tool_input.get("command", path), decision="deny", message=msg)
        return PermissionResultDeny(message=msg)

    runs.append(await run("h5_callback", TASK, base_opts(d, can_use_tool=approver), d, rec5))
    return runs


# ═══ plan：plan 模式＋can_use_tool——計畫交給「人」審，核准後才動手 ═══════
async def part_plan():
    d = make_project("h6_plan_approve")
    rec = Recorder("h6_plan_approve", d)

    async def reviewer(tool_name, tool_input, ctx):
        if tool_name == "ExitPlanMode":
            rec.note("callback", tool=tool_name, target="（計畫全文見上一則 tool_use）", decision="allow",
                     message="人類審過計畫：核准")
            return PermissionResultAllow()
        path = str(tool_input.get("file_path", ""))
        if tool_name in ("Edit", "Write") and "/shop/" in path:
            rec.note("callback", tool=tool_name, target=path, decision="allow")
            return PermissionResultAllow()
        cmd = str(tool_input.get("command", ""))
        if tool_name == "Bash" and cmd.strip().startswith("python3 -m unittest"):
            rec.note("callback", tool=tool_name, target=cmd, decision="allow")
            return PermissionResultAllow()
        msg = "不核准：只准改 shop/ 底下的檔案、只准跑 python3 -m unittest。"
        rec.note("callback", tool=tool_name, target=cmd or path, decision="deny", message=msg)
        return PermissionResultDeny(message=msg)

    return [await run("h6_plan_approve", TASK, base_opts(d, permission_mode="plan", can_use_tool=reviewer), d, rec)]


# ═══ extras：自訂工具、subagent、session ══════════════════════════
ORDERS = {"A1023": {"status": "已出貨", "carrier": "黑貓", "eta": "2026-09-26"}}


@tool("lookup_order", "查詢訂單狀態。輸入訂單編號（例如 A1023），回傳出貨狀態、物流商與預計到貨日。",
      {"order_id": str})
async def lookup_order(args):
    oid = str(args["order_id"]).strip().upper()
    if oid in ORDERS:
        return {"content": [{"type": "text", "text": json.dumps({"order_id": oid, **ORDERS[oid]}, ensure_ascii=False)}]}
    return {"content": [{"type": "text", "text": f"查無訂單 {oid}"}], "is_error": True}


async def part_extras():
    runs = []
    shop = create_sdk_mcp_server(name="shop", version="1.0.0", tools=[lookup_order])
    d = make_project("x1_custom_tool")
    runs.append(await run("x1_custom_tool", "我的訂單 A1023 和 B77 現在各是什麼狀態？用繁體中文簡短回答。",
                          base_opts(d, tools=[], mcp_servers={"shop": shop},
                                    allowed_tools=["mcp__shop__lookup_order"]), d))

    d = make_project("x2_subagent")
    agents = {"test-runner": AgentDefinition(
        description="執行專案的單元測試並回報哪些測試失敗。需要跑測試時使用。",
        prompt="你只負責在專案根目錄執行 `python3 -m unittest -v`，用繁體中文列出失敗的測試名稱與一行錯誤摘要。不要修改任何檔案。",
        tools=["Bash", "Read"], model="haiku",
        background=False)}
    # 2.1.281 起子代理預設丟背景跑（Agent 工具省略 run_in_background 時），主代理會先收工、ResultMessage 先到；
    # 實測第一版 prompt 沒說要等 → 主代理回「已在背景派遣，請稍候」就結束。prompt 講明「等它跑完」才會前景等結果。
    runs.append(await run("x2_subagent", "請派 test-runner 子代理跑測試，等它跑完拿到結果，再告訴我哪些測試失敗、可能的原因。不要修改檔案。",
                          base_opts(d, agents=agents, allowed_tools=["Read", "Bash", "Task", "Agent"]), d))

    # session：記住 → resume 問 → 不 resume 再問
    # （cwd 一律給示範專案：cwd 路徑會進模型的環境資訊，實測沒記憶時模型會拿路徑裡的字串當「代號」亂答）
    d = make_project("x3_session")
    r1 = await run("x3_session_1", "我們這個專案的代號是「藍鯨」。請記住，只要回覆「記住了」。",
                   base_opts(d, tools=[]), d)
    sid = next(e["session_id"] for e in r1["events"] if e["kind"] == "result")
    r2 = await run("x3_session_2_resume", "我們的專案代號是什麼？只回答代號。",
                   base_opts(d, tools=[], resume=sid), d)
    r3 = await run("x3_session_3_fresh", "我們的專案代號是什麼？只回答代號。",
                   base_opts(d, tools=[]), d)
    runs += [r1, r2, r3]
    return runs


# ═══ gate：權限閘門的關鍵規則驗證 ═════════════════════════════════
async def part_gate():
    runs = []
    ask_rm = "請在專案根目錄執行這個指令清掉暫存：rm -rf build 。執行完回報結果，不要做其他事。"
    ask_py = "請執行這個指令並回報輸出：python3 -c \"print(6*7)\" 。不要做其他事。"
    ask_edit = "請把 shop/cart.py 第一行的 docstring 改成「計算小計」。不要做其他事。"

    d = make_project("g1_bypass_deny_rule")
    runs.append(await run("g1_bypass_deny_rule", ask_rm,
                          base_opts(d, permission_mode="bypassPermissions", disallowed_tools=["Bash(rm *)"]), d))

    d = make_project("g2_bypass_hook")
    rec = Recorder("g2_bypass_hook", d)

    async def deny_all_bash(inp, tid, ctx):
        rec.note("hook", hook="deny_all_bash", tool="Bash", command=inp["tool_input"].get("command", ""), decision="deny")
        return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                       "permissionDecisionReason": "hook：本環境禁止 shell 指令"}}

    runs.append(await run("g2_bypass_hook", ask_py,
                          base_opts(d, permission_mode="bypassPermissions",
                                    hooks={"PreToolUse": [HookMatcher(matcher="Bash", hooks=[deny_all_bash])]}), d, rec))

    d = make_project("g3_bypass_allowed_read")
    runs.append(await run("g3_bypass_allowed_read", ask_py,
                          base_opts(d, permission_mode="bypassPermissions", allowed_tools=["Read"]), d))

    d = make_project("g4_dontask_edit")
    runs.append(await run("g4_dontask_edit", ask_edit,
                          base_opts(d, permission_mode="dontAsk", allowed_tools=["Read"]), d))

    # g5：can_use_tool 被 allowed_tools 遮蔽——callback 根本不會被叫到（還會發 warning）
    d = make_project("g5_shadowed_callback")
    rec5 = Recorder("g5_shadowed_callback", d)

    async def never_called(tool_name, tool_input, ctx):
        rec5.note("callback", tool=tool_name, decision="deny")
        return PermissionResultDeny(message="callback 拒絕")

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        r = await run("g5_shadowed_callback", ask_py,
                      base_opts(d, allowed_tools=["Bash"], can_use_tool=never_called), d, rec5)
    r["warnings"] = [f"{type(x.message).__name__}: {x.message}" for x in w]
    print("  warnings:", r["warnings"])
    runs.append(r)
    return runs


# ═══ errors：撞真實錯誤訊息（測驗素材）═════════════════════════════
async def part_errors():
    out = []

    async def cb(tool_name, tool_input, ctx):
        return PermissionResultAllow()

    # e1：query() 給字串 prompt 卻設了 can_use_tool
    try:
        async for _ in query(prompt="hi", options=base_opts(None, can_use_tool=cb)):
            pass
        out.append({"name": "e1_string_prompt_callback", "error": None})
    except Exception as e:
        out.append({"name": "e1_string_prompt_callback", "etype": type(e).__name__, "error": str(e)})
    print(out[-1])

    # e2：resume 一個不存在的 session
    r = await run("e2_resume_missing", "繼續剛才的工作。",
                  base_opts(None, tools=[], resume="00000000-0000-4000-8000-000000000000"), None)
    out.append(r)

    # e3：max_turns 太小——修 bug 任務只給 2 輪
    d = make_project("e3_max_turns")
    r = await run("e3_max_turns", TASK, base_opts(d, allowed_tools=["Read", "Edit", "Bash"], max_turns=2), d)
    out.append(r)
    return out


# ═══ free：ANTHROPIC_BASE_URL → 開源模型 ═════════════════════════
async def part_free():
    base = os.environ.get("FREE_BASE_URL", "http://localhost:11434")
    fmodel = os.environ.get("FREE_MODEL", "qwen3.5:2b")
    env = {"ANTHROPIC_BASE_URL": base, "ANTHROPIC_AUTH_TOKEN": "local", "ANTHROPIC_API_KEY": "",
           "ANTHROPIC_DEFAULT_HAIKU_MODEL": fmodel, "ANTHROPIC_SMALL_FAST_MODEL": fmodel,
           "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1"}
    if os.environ.get("FREE_EXTRA_BODY"):
        env["CLAUDE_CODE_EXTRA_BODY"] = os.environ["FREE_EXTRA_BODY"]
    runs = []
    env["CLAUDE_CODE_MAX_RETRIES"] = "2"  # 錯誤會重試（預設 10 次，一次錯誤要等 3 分鐘）
    # f0：什麼都不調——CLI 對不認得的模型預設要 32000 個輸出 token（實測：16K context 的模型直接 500）
    d = make_project("f0_free_as_is")
    runs.append(await run("f0_free_as_is", TASK,
                          base_opts(d, model=fmodel, env=dict(env), allowed_tools=["Read", "Edit", "Bash"],
                                    max_budget_usd=None), d))
    # f1：輸出上限調小，但工具全開——光工具說明書就把小模型的 context 塞爆
    env["CLAUDE_CODE_MAX_OUTPUT_TOKENS"] = "4096"
    d = make_project("f1_free_default_tools")
    runs.append(await run("f1_free_default_tools", TASK,
                          base_opts(d, model=fmodel, env=dict(env), allowed_tools=["Read", "Edit", "Bash"],
                                    max_budget_usd=None), d))
    # f2：只開三個工具＋短 system prompt
    d = make_project("f2_free_trimmed")
    sp = ("你是程式助理，在目前目錄的專案裡工作。可用工具：Read（讀檔）、Edit（改檔）、Bash（跑指令）。"
          "先讀相關檔案，再修改，最後用 `python3 -m unittest` 驗證。用繁體中文回答。")
    runs.append(await run("f2_free_trimmed", TASK,
                          base_opts(d, model=fmodel, env=dict(env), tools=["Read", "Edit", "Bash"], system_prompt=sp,
                                    allowed_tools=["Read", "Edit", "Bash"], max_budget_usd=None), d))
    for r in runs:
        r["base_url"] = "（本機 Anthropic 相容端點）"
    return runs


PARTS = {"hero": part_hero, "plan": part_plan, "extras": part_extras, "gate": part_gate, "errors": part_errors, "free": part_free}


async def main():
    want = sys.argv[1:] or ["hero"]
    if want == ["all"]:
        want = list(PARTS)
    OUT.mkdir(parents=True, exist_ok=True)
    for p in want:
        res = await PARTS[p]()
        (OUT / f"{p}.json").write_text(sanitize(json.dumps(res, ensure_ascii=False, indent=1, default=str)))
        cost = sum((e.get("total_cost_usd") or 0) for r in res if isinstance(r, dict)
                   for e in r.get("events", []) if e.get("kind") == "result")
        print(f"\n### part {p}: list cost ≈ ${cost:.4f} → {OUT / (p + '.json')}")


if __name__ == "__main__":
    asyncio.run(main())
