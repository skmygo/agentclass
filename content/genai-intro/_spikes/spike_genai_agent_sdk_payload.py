# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""把 spike_genai_agent_sdk.py 錄到的訊息串整理成課程用的 payload，注入 lesson.py 與 page_content.py。

用法（spike 跑完之後）：
  SPIKE_OUT=<spike 的輸出目錄> uv run --script content/genai-intro/_spikes/spike_genai_agent_sdk_payload.py
只做「挑選＋截短＋換成課程用的中文標籤」，不改任何內容：訊息、數字都是 spike 當次的原始紀錄。
lesson.py 裡 `# >>> TRACES` 與 `# <<< TRACES` 之間、page_content.py 裡 `/* >>> HERO_TRACES */` 與
`/* <<< HERO_TRACES */` 之間會被整段覆寫。
"""

import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "genai-agent-sdk"
OUT = Path(os.environ.get("SPIKE_OUT", "agent_sdk_runs")).resolve()

LABELS = {
    "h1_default": "① 什麼都沒允許（預設）",
    "h2_allowed": "② allowed_tools 放行",
    "h3_hook": "③ 放行＋PreToolUse hook",
    "h4_plan": "④ plan 模式（沒接審批函式）",
    "h5_callback": "⑤ can_use_tool 審批函式",
    "h6_plan_approve": "⑥ plan 模式＋審批函式",
    "x1_custom_tool": "自訂工具：@tool＋create_sdk_mcp_server",
    "x2_subagent": "子代理：AgentDefinition",
    "x3_session_1": "session 第 1 次：交代代號",
    "x3_session_2_resume": "session 第 2 次：resume=同一個 session_id",
    "x3_session_3_fresh": "session 第 3 次：不帶 resume",
    "f0_free_as_is": "A. 什麼都不調",
    "f1_free_default_tools": "B. 輸出上限調到 4096，工具全開",
    "f2_free_trimmed": "C. 只開 3 個工具＋短 system prompt",
    "g1_bypass_deny_rule": "bypassPermissions ＋ disallowed_tools=['Bash(rm *)']",
    "g2_bypass_hook": "bypassPermissions ＋ PreToolUse hook 拒絕 Bash",
    "g3_bypass_allowed_read": "bypassPermissions ＋ allowed_tools=['Read']",
    "g4_dontask_edit": "dontAsk ＋ allowed_tools=['Read']，叫它改檔",
    "g5_shadowed_callback": "allowed_tools=['Bash'] ＋ can_use_tool",
}

OPTS = {  # 每一次錄影「跟共同設定不一樣」的那幾行（共同設定見 lesson.py 的 COMMON_OPTS）
    "h1_default": "ClaudeAgentOptions(**COMMON)",
    "h2_allowed": 'ClaudeAgentOptions(**COMMON,\n    allowed_tools=["Read", "Edit", "Bash"])',
    "h3_hook": ('ClaudeAgentOptions(**COMMON,\n    allowed_tools=["Read", "Edit", "Bash"],\n'
                '    hooks={"PreToolUse": [\n        HookMatcher(matcher=None, hooks=[audit]),        # 每次呼叫都記一筆\n'
                '        HookMatcher(matcher="Bash", hooks=[bash_guard]),  # 只准 python3 -m unittest\n    ]})'),
    "h4_plan": 'ClaudeAgentOptions(**COMMON,\n    permission_mode="plan")',
    "h5_callback": "ClaudeAgentOptions(**COMMON,\n    can_use_tool=approver)   # 只准改 shop/ 底下，其餘一律拒絕",
    "h6_plan_approve": ('ClaudeAgentOptions(**COMMON,\n    permission_mode="plan",\n'
                        "    can_use_tool=reviewer)   # 核准計畫、只准改 shop/、只准跑 unittest"),
    "x1_custom_tool": ('shop = create_sdk_mcp_server(name="shop", tools=[lookup_order])\n'
                       'ClaudeAgentOptions(**COMMON,\n    tools=[],                      # 不給任何內建工具\n'
                       '    mcp_servers={"shop": shop},\n    allowed_tools=["mcp__shop__lookup_order"])'),
    "x2_subagent": ('ClaudeAgentOptions(**COMMON,\n    agents={"test-runner": AgentDefinition(\n'
                    '        description="執行專案的單元測試並回報哪些測試失敗。需要跑測試時使用。",\n'
                    '        prompt="你只負責執行 python3 -m unittest -v，列出失敗的測試…不要修改任何檔案。",\n'
                    '        tools=["Bash", "Read"], model="haiku")},\n'
                    '    allowed_tools=["Read", "Bash", "Agent"])'),
    "x3_session_1": "ClaudeAgentOptions(**COMMON, tools=[])",
    "x3_session_2_resume": "ClaudeAgentOptions(**COMMON, tools=[],\n    resume=<第 1 次 ResultMessage 的 session_id>)",
    "x3_session_3_fresh": "ClaudeAgentOptions(**COMMON, tools=[])   # 沒帶 resume＝全新 session",
    "f0_free_as_is": ('env={"ANTHROPIC_BASE_URL": "<Anthropic 相容端點>", "ANTHROPIC_AUTH_TOKEN": "local",\n'
                      '     "ANTHROPIC_API_KEY": ""}\nClaudeAgentOptions(**COMMON, model="qwen3.5-2b", env=env,\n'
                      '    allowed_tools=["Read", "Edit", "Bash"])'),
    "f1_free_default_tools": ('env = {..., "CLAUDE_CODE_MAX_OUTPUT_TOKENS": "4096"}\n'
                              'ClaudeAgentOptions(**COMMON, model="qwen3.5-2b", env=env,\n'
                              '    allowed_tools=["Read", "Edit", "Bash"])'),
    "f2_free_trimmed": ('env = {..., "CLAUDE_CODE_MAX_OUTPUT_TOKENS": "4096"}\n'
                        'ClaudeAgentOptions(**COMMON, model="qwen3.5-2b", env=env,\n'
                        '    tools=["Read", "Edit", "Bash"],        # 只開這三個\n'
                        '    system_prompt="你是程式助理…先讀、再改、最後用 python3 -m unittest 驗證。",\n'
                        '    allowed_tools=["Read", "Edit", "Bash"])'),
}


def short(s, n):
    s = str(s)
    return s if len(s) <= n else s[:n] + f"…（後略 {len(s) - n} 字）"


def slim_input(name, inp):
    if name == "Bash":
        return {"command": short(inp.get("command", ""), 300)}
    if name == "Read":
        return {"file_path": inp.get("file_path", "")}
    if name == "Edit":
        return {"file_path": inp.get("file_path", ""), "old_string": short(inp.get("old_string", ""), 260),
                "new_string": short(inp.get("new_string", ""), 260)}
    if name == "Write":
        return {"file_path": inp.get("file_path", ""), "content": short(inp.get("content", ""), 200)}
    if name == "ExitPlanMode":
        return {"plan": short(inp.get("plan", ""), 520)}
    if name == "Agent":
        d = {k: inp[k] for k in ("subagent_type", "description") if k in inp}
        d["prompt"] = short(inp.get("prompt", ""), 160)
        if "run_in_background" in inp:
            d["run_in_background"] = inp["run_in_background"]
        return d
    if name == "SendMessage":
        return {"to": inp.get("to"), "message": short(inp.get("message", ""), 140)}
    if name == "TaskCreate":
        return {"subject": inp.get("subject", "")}
    return json.loads(json.dumps(inp, ensure_ascii=False)) if len(json.dumps(inp)) < 400 else {"…": short(json.dumps(inp, ensure_ascii=False), 300)}


def slim_events(evs, text_n=900, res_n=600):
    out = []
    for e in evs:
        k = e["kind"]
        if k == "init":
            out.append({"k": "init", "model": e["model"], "mode": e["permissionMode"], "tools": e["tools"],
                        "mcp": [m.get("name") for m in e.get("mcp_servers", [])],
                        "agents": e.get("agents") or []})
        elif k == "text":
            out.append({"k": "text", "text": short(e["text"], text_n), "sub": e.get("sub", False)})
        elif k == "tool_use":
            out.append({"k": "use", "name": e["name"], "input": slim_input(e["name"], e["input"]),
                        "sub": e.get("sub", False)})
        elif k == "tool_result":
            out.append({"k": "res", "err": e["is_error"], "text": short(e["text"], res_n), "sub": e.get("sub", False)})
        elif k == "hook":
            out.append({"k": "hook", "hook": e["hook"], "tool": e["tool"], "command": e.get("command"),
                        "decision": e["decision"], "reason": e.get("reason")})
        elif k == "callback":
            out.append({"k": "cb", "tool": e["tool"], "target": e.get("target"), "decision": e["decision"],
                        "message": e.get("message")})
        elif k == "task":
            out.append({"k": "task", "phase": e["phase"],
                        "text": short(e.get("description") or e.get("summary") or "", 200)})
        elif k == "result":
            u = e.get("usage") or {}
            out.append({"k": "result", "subtype": e["subtype"], "is_error": e["is_error"],
                        "num_turns": e["num_turns"], "duration_ms": e["duration_ms"],
                        "cost": e["total_cost_usd"], "stop_reason": e.get("stop_reason"),
                        "terminal_reason": e.get("terminal_reason"), "errors": e.get("errors"),
                        "result": short(e.get("result") or "", 500),
                        "denials": [{"tool": d.get("tool_name"),
                                     "input": short(d.get("tool_input", {}).get("command")
                                                    or d.get("tool_input", {}).get("file_path") or "", 120)}
                                    for d in e.get("permission_denials") or []],
                        "usage": {"input": u.get("input_tokens", 0), "cache_read": u.get("cache_read_input_tokens", 0),
                                  "cache_write": u.get("cache_creation_input_tokens", 0),
                                  "output": u.get("output_tokens", 0)},
                        "model_usage": {m: {"in": v.get("inputTokens"), "out": v.get("outputTokens"),
                                            "cache_read": v.get("cacheReadInputTokens"),
                                            "cache_write": v.get("cacheCreationInputTokens"),
                                            "cost": v.get("costUSD"), "basis": v.get("costBasis")}
                                        for m, v in (e.get("model_usage") or {}).items()},
                        "session_id": e.get("session_id")})
        elif k == "exception":
            out.append({"k": "exc", "etype": e["etype"], "text": e["text"]})
    return out


def pack(r, **kw):
    d = {"label": LABELS.get(r["name"], r["name"]), "opts": OPTS.get(r["name"], ""), "prompt": r["prompt"],
         "events": slim_events(r["events"], **kw),
         "calls": [{"input": c["input"], "cache_read": c["cache_read"], "cache_write": c["cache_write"],
                    "sub": c["parent"], "model": c["model"]} for c in r["calls"]]}
    if "state" in r:
        d["state"] = {"tests_pass": r["state"]["tests_pass"], "tail": r["state"]["unittest_tail"],
                      "diff": r["state"]["diff"]}
    if r.get("warnings"):
        d["warnings"] = r["warnings"]
    return d


def load(name):
    return json.loads((OUT / f"{name}.json").read_text())


def main():
    hero = {r["name"]: r for r in load("hero") + load("plan")}
    extras = {r["name"]: r for r in load("extras")}
    gate = {r["name"]: r for r in load("gate")}
    errors = load("errors")
    free = {r["name"]: r for r in load("free")}

    data = {
        "meta": {"model": "claude-haiku-4-5", "sdk": "claude-agent-sdk 0.2.159", "cli": "Claude Code 2.1.281",
                 "date": "2026-09-24", "free_model": "qwen3.5-2b（vLLM 0.26.0 的 Anthropic 相容端點）"},
        "hero": {k: pack(hero[k]) for k in ("h1_default", "h2_allowed", "h3_hook", "h4_plan", "h5_callback",
                                             "h6_plan_approve")},
        "extras": {k: pack(extras[k]) for k in ("x1_custom_tool", "x2_subagent", "x3_session_1",
                                                 "x3_session_2_resume", "x3_session_3_fresh")},  # state 下面拿掉
        "gate": {k: pack(v, text_n=300, res_n=300) for k, v in gate.items()},
        "free": {k: pack(free[k]) for k in ("f0_free_as_is", "f1_free_default_tools", "f2_free_trimmed")},
        "errors": {"resume_missing": next(e["text"] for r in errors if isinstance(r, dict) and r.get("name") == "e2_resume_missing"
                                          for e in r["events"] if e["kind"] == "exception"),
                   "max_turns": next(slim_events([e])[0] for r in errors if isinstance(r, dict) and r.get("name") == "e3_max_turns"
                                     for e in r["events"] if e["kind"] == "result")},
    }
    for v in data["extras"].values():  # 這幾段不是修 bug 任務（專案只是當工作目錄），測試狀態與它們無關
        v.pop("state", None)
    # session 第 3 次（不帶 resume）的回答每次不同：把另一次錄影的回答也收進來，課文寫範圍
    v1 = OUT / "extras_v1_async.json"
    if v1.exists():
        for r in json.loads(v1.read_text()):
            if r["name"] == "x3_session_3_fresh":
                data["extras"]["x3_session_3_fresh"]["other_answer"] = next(
                    e["result"] for e in r["events"] if e["kind"] == "result")

    blob = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    assert "'''" not in blob and not blob.endswith("\\")
    private_ip = r"\b(?:10|192\.168|172\.(?:1[6-9]|2\d|3[01]))(?:\.\d{1,3}){2,3}\b"
    assert not re.search(private_ip, blob), "payload 含私有網段 IP"
    assert str(Path.home()) not in blob and Path.home().name not in blob, "payload 含本機家目錄／使用者名稱"
    lesson = ROOT / "lesson.py"
    src = lesson.read_text()
    new = f"# >>> TRACES（spike_genai_agent_sdk_payload.py 產生，勿手改）\n    TRACES = json.loads(r'''{blob}''')\n    # <<< TRACES"
    src2 = re.sub(r"# >>> TRACES.*?# <<< TRACES", lambda m: new, src, flags=re.DOTALL)
    assert src2 != src or new in src, "lesson.py 找不到 TRACES 標記"
    lesson.write_text(src2)
    print("lesson.py TRACES:", len(blob), "bytes")

    # hero（教學頁 JS）：三種設定、截更短
    hero_js = {k: {"label": LABELS[k], "opts": OPTS[k], "events": slim_events(hero[k]["events"], text_n=320, res_n=220),
                   "state": {"tests_pass": hero[k]["state"]["tests_pass"], "tail": hero[k]["state"]["unittest_tail"]}}
               for k in ("h1_default", "h2_allowed", "h3_hook")}
    for v in hero_js.values():  # 教學頁 hero 不需要 init 的完整工具清單與 model_usage
        for e in v["events"]:
            if e["k"] == "init":
                e["tools"] = len(e["tools"])
            if e["k"] == "result":
                e.pop("model_usage", None)
                e.pop("session_id", None)
    js = json.dumps(hero_js, ensure_ascii=False, separators=(",", ":"))
    # 物件字面值裡的反引號、*/ 都無害；會壞的是 page_content.py 的 r''' 定界與 HTML 的 </script>
    assert "'''" not in js and "</script" not in js.lower() and "<!--" not in js
    pc = ROOT / "page_content.py"
    s = pc.read_text()
    newjs = f"/* >>> HERO_TRACES（spike_genai_agent_sdk_payload.py 產生，勿手改）*/\n  const RUNS = {js};\n  /* <<< HERO_TRACES */"
    s2 = re.sub(r"/\* >>> HERO_TRACES.*?/\* <<< HERO_TRACES \*/", lambda m: newjs, s, flags=re.DOTALL)
    pc.write_text(s2)
    print("page_content.py HERO_TRACES:", len(js), "bytes")


if __name__ == "__main__":
    main()
