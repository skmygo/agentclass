import marimo

__generated_with = "0.23.16"
app = marimo.App(width="medium", app_title="MCP 新版協定與 FastMCP 4（實驗場）")


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    # 🧪 MCP 新版協定與 FastMCP 4（實驗場）

    這是本課的**實驗場**。教學頁讀到哪，就回到這裡動手——每個實驗都是**下拉選單與拉桿**，
    選了立刻重算、重畫。

    這裡的每一個封包、每一句錯誤訊息都是**實測側錄**：我們在本機用 **FastMCP 4.0.8**（MCP Python SDK 2.2.0）
    起了真的 HTTP 伺服器，前面掛一個只記錄、不干擾的側錄器，2026-09-24 錄下來嵌進這份 notebook。
    你在這裡看到的 session id、task id 是那一次的紀錄——自己重錄一次，這些亂數會不同，
    但請求的**數量、順序、header 與錯誤訊息**不會變。
    """
    )
    return


@app.cell
def _():
    import marimo as mo
    return (mo,)


@app.cell
def _():
    import html as html_mod
    import json

    import matplotlib.pyplot as plt
    import numpy as np
    return html_mod, json, np, plt


@app.cell
def _(json):
    # ── 實測錄音（FastMCP 4.0.8、mcp 2.2.0、2026-09-24）──
    # 由 content/genai-intro/_spikes/spike_genai_mcp_fastmcp.py --inject 寫入；要更新請重跑 spike，別手改。
    WIRE_JSON = r"""{"meta":{"date":"2026-09-24","fastmcp":"4.0.8","mcp":"2.2.0","fastmcp_tasks":"4.0.8","python":"3.12.13"},"eras":{"2026-07-28":{"protocol":"2026-07-28","tools":["add"],"result":5,"wire":[{"t":10,"m":"POST","path":"/mcp","rh":{"accept":"application/json, text/event-stream","content-type":"application/json","mcp-protocol-version":"2026-07-28","mcp-method":"server/discover"},"st":200,"sh":{"content-type":"application/json"},"rb":"{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"server/discover\",\"params\":{\"_meta\":{\"io.modelcontextprotocol/protocolVersion\":\"2026-07-28\",\"io.modelcontextprotocol/clientInfo\":{\"name\":\"mcp\",\"version\":\"0.1.0\"},\"io.modelcontextprotocol/clientCapabilities\":{}}}}","rbn":245,"sb":"{\"jsonrpc\":\"2.0\",\"id\":1,\"result\":{\"_meta\":{\"io.modelcontextprotocol/serverInfo\":{\"name\":\"calc\",\"version\":\"4.0.8\"}},\"ttlMs\":0,\"cacheScope\":\"private\",\"supportedVersions\":[\"2026-07-28\"],\"capabilities\":{\"logging\":{},\"prompts\":{\"listChanged\":false},\"resources\":{\"subscribe\":false,\"listChanged\":false},\"tools\":{\"listChanged\":false},\"extensions\":{\"io.modelcontextprotocol/ui\":{}}},\"instructions\":\"A tiny calculator.\",\"resultType\":\"complete\"}}","sbn":435},{"t":67,"m":"POST","path":"/mcp","rh":{"accept":"application/json, text/event-stream","content-type":"application/json","mcp-protocol-version":"2026-07-28","mcp-method":"tools/list"},"st":200,"sh":{"content-type":"application/json"},"rb":"{\"jsonrpc\":\"2.0\",\"id\":2,\"method\":\"tools/list\",\"params\":{\"_meta\":{\"io.modelcontextprotocol/protocolVersion\":\"2026-07-28\",\"io.modelcontextprotocol/clientInfo\":{\"name\":\"mcp\",\"version\":\"0.1.0\"},\"io.modelcontextprotocol/clientCapabilities\":{},\"io.modelcontextprotocol/logLevel\":\"debug\"}}}","rbn":283,"sb":"{\"jsonrpc\":\"2.0\",\"id\":2,\"result\":{\"cacheScope\":\"private\",\"resultType\":\"complete\",\"tools\":[{\"_meta\":{\"fastmcp\":{\"tags\":[]}},\"description\":\"Add two integers.\",\"inputSchema\":{\"type\":\"object\",\"additionalProperties\":false,\"properties\":{\"a\":{\"type\":\"integer\"},\"b\":{\"type\":\"integer\"}},\"required\":[\"a\",\"b\"]},\"name\":\"add\",\"outputSchema\":{\"properties\":{\"result\":{\"type\":\"integer\"}},\"required\":[\"result\"],\"type\":\"object\",\"x-fastmcp-wrap-result\":true},\"title\":\"Add\"}],\"ttlMs\":0,\"_meta\":{\"io.modelcontextprotocol/serverInfo\":{\"name\":\"calc\",\"version\":\"4.0.8\"}}}}","sbn":548},{"t":71,"m":"POST","path":"/mcp","rh":{"accept":"application/json, text/event-stream","content-type":"application/json","mcp-protocol-version":"2026-07-28","mcp-method":"tools/call","mcp-name":"add"},"st":200,"sh":{"content-type":"application/json"},"rb":"{\"jsonrpc\":\"2.0\",\"id\":3,\"method\":\"tools/call\",\"params\":{\"name\":\"add\",\"arguments\":{\"a\":2,\"b\":3},\"_meta\":{\"io.modelcontextprotocol/protocolVersion\":\"2026-07-28\",\"io.modelcontextprotocol/clientInfo\":{\"name\":\"mcp\",\"version\":\"0.1.0\"},\"io.modelcontextprotocol/clientCapabilities\":{},\"io.modelcontextprotocol/logLevel\":\"debug\",\"progressToken\":3}}}","rbn":340,"sb":"{\"jsonrpc\":\"2.0\",\"id\":3,\"result\":{\"_meta\":{\"fastmcp\":{\"wrap_result\":true},\"io.modelcontextprotocol/serverInfo\":{\"name\":\"calc\",\"version\":\"4.0.8\"}},\"content\":[{\"text\":\"5\",\"type\":\"text\"}],\"isError\":false,\"resultType\":\"complete\",\"structuredContent\":{\"result\":5}}}","sbn":259}],"client":"FastMCP Client 4.0.8（預設 mode=auto）"},"2025-11-25":{"protocol":"2025-11-25","tools":["add"],"result":5,"wire":[{"t":2,"m":"POST","path":"/mcp","rh":{"accept":"application/json, text/event-stream","content-type":"application/json"},"st":200,"sh":{"content-type":"text/event-stream","mcp-session-id":"223ae1b206344bec917c9a8da5209691"},"rb":"{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"initialize\",\"params\":{\"protocolVersion\":\"2025-11-25\",\"capabilities\":{},\"clientInfo\":{\"name\":\"mcp\",\"version\":\"0.1.0\"},\"_meta\":{}}}","rbn":163,"sb":"event: message\ndata: {\"jsonrpc\":\"2.0\",\"id\":1,\"result\":{\"protocolVersion\":\"2025-11-25\",\"capabilities\":{\"logging\":{},\"prompts\":{\"listChanged\":true},\"resources\":{\"subscribe\":false,\"listChanged\":true},\"tools\":{\"listChanged\":true}},\"serverInfo\":{\"name\":\"calc\",\"version\":\"4.0.8\"},\"instructions\":\"A tiny calculator.\"}}\n\n","sbn":316},{"t":5,"m":"POST","path":"/mcp","rh":{"accept":"application/json, text/event-stream","content-type":"application/json","mcp-session-id":"223ae1b206344bec917c9a8da5209691","mcp-protocol-version":"2025-11-25"},"st":202,"sh":{"content-type":"application/json","mcp-session-id":"223ae1b206344bec917c9a8da5209691"},"rb":"{\"jsonrpc\":\"2.0\",\"method\":\"notifications/initialized\"}","rbn":54,"sb":"","sbn":0},{"t":5,"m":"GET","path":"/mcp","rh":{"accept":"application/json, text/event-stream","content-type":"application/json","mcp-session-id":"223ae1b206344bec917c9a8da5209691","mcp-protocol-version":"2025-11-25"},"st":200,"sh":{"content-type":"text/event-stream","mcp-session-id":"223ae1b206344bec917c9a8da5209691"},"rb":"","rbn":0,"sb":"","sbn":0},{"t":6,"m":"POST","path":"/mcp","rh":{"accept":"application/json, text/event-stream","content-type":"application/json","mcp-session-id":"223ae1b206344bec917c9a8da5209691","mcp-protocol-version":"2025-11-25"},"st":200,"sh":{"content-type":"text/event-stream","mcp-session-id":"223ae1b206344bec917c9a8da5209691"},"rb":"{\"jsonrpc\":\"2.0\",\"id\":2,\"method\":\"tools/list\",\"params\":{\"_meta\":{}}}","rbn":68,"sb":"event: message\ndata: {\"jsonrpc\":\"2.0\",\"id\":2,\"result\":{\"tools\":[{\"_meta\":{\"fastmcp\":{\"tags\":[]}},\"description\":\"Add two integers.\",\"inputSchema\":{\"properties\":{\"a\":{\"type\":\"integer\"},\"b\":{\"type\":\"integer\"}},\"required\":[\"a\",\"b\"],\"type\":\"object\",\"additionalProperties\":false},\"name\":\"add\",\"outputSchema\":{\"properties\":{\"result\":{\"type\":\"integer\"}},\"required\":[\"result\"],\"type\":\"object\",\"x-fastmcp-wrap-result\":true},\"title\":\"Add\"}]}}\n\n","sbn":436},{"t":9,"m":"POST","path":"/mcp","rh":{"accept":"application/json, text/event-stream","content-type":"application/json","mcp-session-id":"223ae1b206344bec917c9a8da5209691","mcp-protocol-version":"2025-11-25"},"st":200,"sh":{"content-type":"text/event-stream","mcp-session-id":"223ae1b206344bec917c9a8da5209691"},"rb":"{\"jsonrpc\":\"2.0\",\"id\":3,\"method\":\"tools/call\",\"params\":{\"name\":\"add\",\"arguments\":{\"a\":2,\"b\":3},\"_meta\":{\"progressToken\":3}}}","rbn":124,"sb":"event: message\ndata: {\"jsonrpc\":\"2.0\",\"id\":3,\"result\":{\"_meta\":{\"fastmcp\":{\"wrap_result\":true}},\"content\":[{\"text\":\"5\",\"type\":\"text\"}],\"isError\":false,\"structuredContent\":{\"result\":5}}}\n\n","sbn":190},{"t":13,"m":"DELETE","path":"/mcp","rh":{"accept":"application/json, text/event-stream","content-type":"application/json","mcp-session-id":"223ae1b206344bec917c9a8da5209691","mcp-protocol-version":"2025-11-25"},"st":200,"sh":{"content-type":"application/json","mcp-session-id":"223ae1b206344bec917c9a8da5209691"},"rb":"","rbn":0,"sb":"","sbn":0}],"client":"FastMCP Client 4.0.8（mode=legacy）"},"2025-06-18":{"protocol":"2025-06-18","result":5,"wire":[{"t":17,"m":"POST","path":"/mcp","rh":{"accept":"application/json, text/event-stream","content-type":"application/json"},"st":200,"sh":{"content-type":"text/event-stream","mcp-session-id":"f9d05eee2542450a983896caeca8f3ba"},"rb":"{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"initialize\",\"params\":{\"protocolVersion\":\"2025-06-18\",\"capabilities\":{},\"clientInfo\":{\"name\":\"raw-2025-06-18\",\"version\":\"0\"}}}","rbn":159,"sb":"event: message\ndata: {\"jsonrpc\":\"2.0\",\"id\":1,\"result\":{\"protocolVersion\":\"2025-06-18\",\"capabilities\":{\"logging\":{},\"prompts\":{\"listChanged\":true},\"resources\":{\"subscribe\":false,\"listChanged\":true},\"tools\":{\"listChanged\":true}},\"serverInfo\":{\"name\":\"calc\",\"version\":\"4.0.8\"},\"instructions\":\"A tiny calculator.\"}}\n\n","sbn":316},{"t":19,"m":"POST","path":"/mcp","rh":{"accept":"application/json, text/event-stream","mcp-session-id":"f9d05eee2542450a983896caeca8f3ba","mcp-protocol-version":"2025-06-18","content-type":"application/json"},"st":202,"sh":{"content-type":"application/json","mcp-session-id":"f9d05eee2542450a983896caeca8f3ba"},"rb":"{\"jsonrpc\":\"2.0\",\"method\":\"notifications/initialized\"}","rbn":54,"sb":"","sbn":0},{"t":20,"m":"POST","path":"/mcp","rh":{"accept":"application/json, text/event-stream","mcp-session-id":"f9d05eee2542450a983896caeca8f3ba","mcp-protocol-version":"2025-06-18","content-type":"application/json"},"st":200,"sh":{"content-type":"text/event-stream","mcp-session-id":"f9d05eee2542450a983896caeca8f3ba"},"rb":"{\"jsonrpc\":\"2.0\",\"id\":2,\"method\":\"tools/list\"}","rbn":46,"sb":"event: message\ndata: {\"jsonrpc\":\"2.0\",\"id\":2,\"result\":{\"tools\":[{\"_meta\":{\"fastmcp\":{\"tags\":[]}},\"description\":\"Add two integers.\",\"inputSchema\":{\"properties\":{\"a\":{\"type\":\"integer\"},\"b\":{\"type\":\"integer\"}},\"required\":[\"a\",\"b\"],\"type\":\"object\",\"additionalProperties\":false},\"name\":\"add\",\"outputSchema\":{\"properties\":{\"result\":{\"type\":\"integer\"}},\"required\":[\"result\"],\"type\":\"object\",\"x-fastmcp-wrap-result\":true},\"title\":\"Add\"}]}}\n\n","sbn":436},{"t":21,"m":"POST","path":"/mcp","rh":{"accept":"application/json, text/event-stream","mcp-session-id":"f9d05eee2542450a983896caeca8f3ba","mcp-protocol-version":"2025-06-18","content-type":"application/json"},"st":200,"sh":{"content-type":"text/event-stream","mcp-session-id":"f9d05eee2542450a983896caeca8f3ba"},"rb":"{\"jsonrpc\":\"2.0\",\"id\":3,\"method\":\"tools/call\",\"params\":{\"name\":\"add\",\"arguments\":{\"a\":2,\"b\":3}}}","rbn":96,"sb":"event: message\ndata: {\"jsonrpc\":\"2.0\",\"id\":3,\"result\":{\"_meta\":{\"fastmcp\":{\"wrap_result\":true}},\"content\":[{\"text\":\"5\",\"type\":\"text\"}],\"isError\":false,\"structuredContent\":{\"result\":5}}}\n\n","sbn":190},{"t":23,"m":"DELETE","path":"/mcp","rh":{"accept":"application/json, text/event-stream","mcp-session-id":"f9d05eee2542450a983896caeca8f3ba","mcp-protocol-version":"2025-06-18"},"st":200,"sh":{"content-type":"application/json","mcp-session-id":"f9d05eee2542450a983896caeca8f3ba"},"rb":"","rbn":0,"sb":"","sbn":0}],"client":"照 2025-06-18 規格手寫的 httpx 客戶端"},"2025-03-26":{"protocol":"2025-03-26","result":5,"wire":[{"t":5,"m":"POST","path":"/mcp","rh":{"accept":"application/json, text/event-stream","content-type":"application/json"},"st":200,"sh":{"content-type":"text/event-stream","mcp-session-id":"88fe8cafdb92436f92d078684882266d"},"rb":"{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"initialize\",\"params\":{\"protocolVersion\":\"2025-03-26\",\"capabilities\":{},\"clientInfo\":{\"name\":\"raw-2025-03-26\",\"version\":\"0\"}}}","rbn":159,"sb":"event: message\ndata: {\"jsonrpc\":\"2.0\",\"id\":1,\"result\":{\"protocolVersion\":\"2025-03-26\",\"capabilities\":{\"logging\":{},\"prompts\":{\"listChanged\":true},\"resources\":{\"subscribe\":false,\"listChanged\":true},\"tools\":{\"listChanged\":true}},\"serverInfo\":{\"name\":\"calc\",\"version\":\"4.0.8\"},\"instructions\":\"A tiny calculator.\"}}\n\n","sbn":316},{"t":7,"m":"POST","path":"/mcp","rh":{"accept":"application/json, text/event-stream","mcp-session-id":"88fe8cafdb92436f92d078684882266d","content-type":"application/json"},"st":202,"sh":{"content-type":"application/json","mcp-session-id":"88fe8cafdb92436f92d078684882266d"},"rb":"{\"jsonrpc\":\"2.0\",\"method\":\"notifications/initialized\"}","rbn":54,"sb":"","sbn":0},{"t":7,"m":"POST","path":"/mcp","rh":{"accept":"application/json, text/event-stream","mcp-session-id":"88fe8cafdb92436f92d078684882266d","content-type":"application/json"},"st":200,"sh":{"content-type":"text/event-stream","mcp-session-id":"88fe8cafdb92436f92d078684882266d"},"rb":"{\"jsonrpc\":\"2.0\",\"id\":2,\"method\":\"tools/list\"}","rbn":46,"sb":"event: message\ndata: {\"jsonrpc\":\"2.0\",\"id\":2,\"result\":{\"tools\":[{\"_meta\":{\"fastmcp\":{\"tags\":[]}},\"description\":\"Add two integers.\",\"inputSchema\":{\"properties\":{\"a\":{\"type\":\"integer\"},\"b\":{\"type\":\"integer\"}},\"required\":[\"a\",\"b\"],\"type\":\"object\",\"additionalProperties\":false},\"name\":\"add\",\"outputSchema\":{\"properties\":{\"result\":{\"type\":\"integer\"}},\"required\":[\"result\"],\"type\":\"object\",\"x-fastmcp-wrap-result\":true},\"title\":\"Add\"}]}}\n\n","sbn":436},{"t":8,"m":"POST","path":"/mcp","rh":{"accept":"application/json, text/event-stream","mcp-session-id":"88fe8cafdb92436f92d078684882266d","content-type":"application/json"},"st":200,"sh":{"content-type":"text/event-stream","mcp-session-id":"88fe8cafdb92436f92d078684882266d"},"rb":"{\"jsonrpc\":\"2.0\",\"id\":3,\"method\":\"tools/call\",\"params\":{\"name\":\"add\",\"arguments\":{\"a\":2,\"b\":3}}}","rbn":96,"sb":"event: message\ndata: {\"jsonrpc\":\"2.0\",\"id\":3,\"result\":{\"_meta\":{\"fastmcp\":{\"wrap_result\":true}},\"content\":[{\"text\":\"5\",\"type\":\"text\"}],\"isError\":false,\"structuredContent\":{\"result\":5}}}\n\n","sbn":190},{"t":10,"m":"DELETE","path":"/mcp","rh":{"accept":"application/json, text/event-stream","mcp-session-id":"88fe8cafdb92436f92d078684882266d"},"st":200,"sh":{"content-type":"application/json","mcp-session-id":"88fe8cafdb92436f92d078684882266d"},"rb":"","rbn":0,"sb":"","sbn":0}],"client":"照 2025-03-26 規格手寫的 httpx 客戶端"},"2024-11-05":{"protocol":"2024-11-05","result":5,"wire":[{"t":5,"m":"GET","path":"/sse","rh":{"accept":"text/event-stream"},"st":200,"sh":{},"rb":"","rbn":0,"sb":"event: endpoint\ndata: /messages/?session_id=c669d903542440d9a943ddb6d8d98a14\n\nevent: message\ndata: {\"jsonrpc\":\"2.0\",\"id\":1,\"result\":{\"protocolVersion\":\"2024-11-05\",\"capabilities\":{\"logging\":{},\"prompts\":{\"listChanged\":true},\"resources\":{\"subscribe\":false,\"listChanged\":true},\"tools\":{\"listChanged\":true}},\"serverInfo\":{\"name\":\"calc\",\"version\":\"4.0.8\"},\"instructions\":\"A tiny calculator.\"}}\n\nevent: message\ndata: {\"jsonrpc\":\"2.0\",\"id\":2,\"result\":{\"tools\":[{\"_meta\":{\"fastmcp\":{\"tags\":[]}},\"description\":\"Add two integers.\",\"inputSchema\":{\"properties\":{\"a\":{\"type\":\"integer\"},\"b\":{\"type\":\"integer\"}},\"required\":[\"a\",\"b\"],\"type\":\"object\",\"additionalProperties\":false},\"name\":\"add\",\"outputSchema\":{\"properties\":{\"result\":{\"type\":\"integer\"}},\"required\":[\"result\"],\"type\":\"object\",\"x-fastmcp-wrap-result\":true},\"title\":\"Add\"}]}}\n\nevent: message\ndata: {\"jsonrpc\":\"2.0\",\"id\":3,\"result\":{\"_meta\":{\"fastmcp\":{\"wrap_result\":true}},\"content\":[{\"text\":\"5\",\"type\":\"text\"}],\"isError\":false,\"structuredContent\":{\"result\":5}}}\n\n","sbn":1023},{"t":54,"m":"POST","path":"/messages/?session_id=c669d903542440d9a943ddb6d8d98a14","rh":{"accept":"*/*","content-type":"application/json"},"st":202,"sh":{},"rb":"{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"initialize\",\"params\":{\"protocolVersion\":\"2024-11-05\",\"capabilities\":{},\"clientInfo\":{\"name\":\"raw-2024-11-05\",\"version\":\"0\"}}}","rbn":159,"sb":"Accepted","sbn":8},{"t":206,"m":"POST","path":"/messages/?session_id=c669d903542440d9a943ddb6d8d98a14","rh":{"accept":"*/*","content-type":"application/json"},"st":202,"sh":{},"rb":"{\"jsonrpc\":\"2.0\",\"method\":\"notifications/initialized\"}","rbn":54,"sb":"Accepted","sbn":8},{"t":357,"m":"POST","path":"/messages/?session_id=c669d903542440d9a943ddb6d8d98a14","rh":{"accept":"*/*","content-type":"application/json"},"st":202,"sh":{},"rb":"{\"jsonrpc\":\"2.0\",\"id\":2,\"method\":\"tools/list\"}","rbn":46,"sb":"Accepted","sbn":8},{"t":508,"m":"POST","path":"/messages/?session_id=c669d903542440d9a943ddb6d8d98a14","rh":{"accept":"*/*","content-type":"application/json"},"st":202,"sh":{},"rb":"{\"jsonrpc\":\"2.0\",\"id\":3,\"method\":\"tools/call\",\"params\":{\"name\":\"add\",\"arguments\":{\"a\":2,\"b\":3}}}","rbn":96,"sb":"Accepted","sbn":8}],"client":"照 2024-11-05 規格手寫的 HTTP+SSE 客戶端（伺服器：http_app(transport=\"sse\")）"}},"scenarios":{"elicit_modern":{"result":"deleted notes.txt","wire":[{"t":2,"m":"POST","path":"/mcp","rh":{"accept":"application/json, text/event-stream","content-type":"application/json","mcp-protocol-version":"2026-07-28","mcp-method":"server/discover"},"st":200,"sh":{"content-type":"application/json"},"rb":"{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"server/discover\",\"params\":{\"_meta\":{\"io.modelcontextprotocol/protocolVersion\":\"2026-07-28\",\"io.modelcontextprotocol/clientInfo\":{\"name\":\"mcp\",\"version\":\"0.1.0\"},\"io.modelcontextprotocol/clientCapabilities\":{\"elicitation\":{\"form\":{},\"url\":{}}}}}}","rbn":279,"sb":"{\"jsonrpc\":\"2.0\",\"id\":1,\"result\":{\"_meta\":{\"io.modelcontextprotocol/serverInfo\":{\"name\":\"files\",\"version\":\"4.0.8\"}},\"ttlMs\":0,\"cacheScope\":\"private\",\"supportedVersions\":[\"2026-07-28\"],\"capabilities\":{\"logging\":{},\"prompts\":{\"listChanged\":false},\"resources\":{\"subscribe\":false,\"listChanged\":false},\"tools\":{\"listChanged\":false},\"extensions\":{\"io.modelcontextprotocol/ui\":{}}},\"resultType\":\"complete\"}}","sbn":400},{"t":3,"m":"POST","path":"/mcp","rh":{"accept":"application/json, text/event-stream","content-type":"application/json","mcp-protocol-version":"2026-07-28","mcp-method":"tools/call","mcp-name":"delete_file"},"st":200,"sh":{"content-type":"application/json"},"rb":"{\"jsonrpc\":\"2.0\",\"id\":2,\"method\":\"tools/call\",\"params\":{\"name\":\"delete_file\",\"arguments\":{\"path\":\"notes.txt\"},\"_meta\":{\"io.modelcontextprotocol/protocolVersion\":\"2026-07-28\",\"io.modelcontextprotocol/clientInfo\":{\"name\":\"mcp\",\"version\":\"0.1.0\"},\"io.modelcontextprotocol/clientCapabilities\":{\"elicitation\":{\"form\":{},\"url\":{}}},\"io.modelcontextprotocol/logLevel\":\"debug\",\"progressToken\":2}}}","rbn":389,"sb":"{\"jsonrpc\":\"2.0\",\"id\":2,\"result\":{\"inputRequests\":{\"confirm\":{\"method\":\"elicitation/create\",\"params\":{\"message\":\"Really delete notes.txt?\",\"mode\":\"form\",\"requestedSchema\":{\"properties\":{\"ok\":{\"type\":\"boolean\"}},\"required\":[\"ok\"],\"type\":\"object\"}}}},\"resultType\":\"input_required\",\"_meta\":{\"io.modelcontextprotocol/serverInfo\":{\"name\":\"files\",\"version\":\"4.0.8\"}}}}","sbn":362},{"t":6,"m":"POST","path":"/mcp","rh":{"accept":"application/json, text/event-stream","content-type":"application/json","mcp-protocol-version":"2026-07-28","mcp-method":"tools/call","mcp-name":"delete_file"},"st":200,"sh":{"content-type":"application/json"},"rb":"{\"jsonrpc\":\"2.0\",\"id\":3,\"method\":\"tools/call\",\"params\":{\"inputResponses\":{\"confirm\":{\"action\":\"accept\",\"content\":{\"ok\":true}}},\"name\":\"delete_file\",\"arguments\":{\"path\":\"notes.txt\"},\"_meta\":{\"io.modelcontextprotocol/protocolVersion\":\"2026-07-28\",\"io.modelcontextprotocol/clientInfo\":{\"name\":\"mcp\",\"version\":\"0.1.0\"},\"io.modelcontextprotocol/clientCapabilities\":{\"elicitation\":{\"form\":{},\"url\":{}}},\"io.modelcontextprotocol/logLevel\":\"debug\",\"progressToken\":3}}}","rbn":460,"sb":"{\"jsonrpc\":\"2.0\",\"id\":3,\"result\":{\"_meta\":{\"fastmcp\":{\"wrap_result\":true},\"io.modelcontextprotocol/serverInfo\":{\"name\":\"files\",\"version\":\"4.0.8\"}},\"content\":[{\"text\":\"deleted notes.txt\",\"type\":\"text\"}],\"isError\":false,\"resultType\":\"complete\",\"structuredContent\":{\"result\":\"deleted notes.txt\"}}}","sbn":294},{"t":8,"m":"POST","path":"/mcp","rh":{"accept":"application/json, text/event-stream","content-type":"application/json","mcp-protocol-version":"2026-07-28","mcp-method":"tools/list"},"st":200,"sh":{"content-type":"application/json"},"rb":"{\"jsonrpc\":\"2.0\",\"id\":4,\"method\":\"tools/list\",\"params\":{\"_meta\":{\"io.modelcontextprotocol/protocolVersion\":\"2026-07-28\",\"io.modelcontextprotocol/clientInfo\":{\"name\":\"mcp\",\"version\":\"0.1.0\"},\"io.modelcontextprotocol/clientCapabilities\":{\"elicitation\":{\"form\":{},\"url\":{}}},\"io.modelcontextprotocol/logLevel\":\"debug\"}}}","rbn":317,"sb":"{\"jsonrpc\":\"2.0\",\"id\":4,\"result\":{\"cacheScope\":\"private\",\"resultType\":\"complete\",\"tools\":[{\"_meta\":{\"fastmcp\":{\"tags\":[]}},\"description\":\"Delete a file after the user confirms.\",\"inputSchema\":{\"type\":\"object\",\"additionalProperties\":false,\"properties\":{\"path\":{\"type\":\"string\"}},\"required\":[\"path\"]},\"name\":\"delete_file\",\"outputSchema\":{\"properties\":{\"result\":{\"type\":\"string\"}},\"required\":[\"result\"],\"type\":\"object\",\"x-fastmcp-wrap-result\":true},\"title\":\"Delete File\"}],\"ttlMs\":0,\"_meta\":{\"io.modelcontextprotocol/serverInfo\":{\"name\":\"files\",\"version\":\"4.0.8\"}}}}","sbn":563}]},"elicit_legacy":{"result":"deleted notes.txt","wire":[{"t":2,"m":"POST","path":"/mcp","rh":{"accept":"application/json, text/event-stream","content-type":"application/json"},"st":200,"sh":{"content-type":"text/event-stream","mcp-session-id":"b1c70a2be90b42f190926156add89544"},"rb":"{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"initialize\",\"params\":{\"protocolVersion\":\"2025-11-25\",\"capabilities\":{\"elicitation\":{\"form\":{},\"url\":{}}},\"clientInfo\":{\"name\":\"mcp\",\"version\":\"0.1.0\"},\"_meta\":{}}}","rbn":197,"sb":"event: message\ndata: {\"jsonrpc\":\"2.0\",\"id\":1,\"result\":{\"protocolVersion\":\"2025-11-25\",\"capabilities\":{\"logging\":{},\"prompts\":{\"listChanged\":true},\"resources\":{\"subscribe\":false,\"listChanged\":true},\"tools\":{\"listChanged\":true}},\"serverInfo\":{\"name\":\"files\",\"version\":\"4.0.8\"}}}\n\n","sbn":281},{"t":6,"m":"POST","path":"/mcp","rh":{"accept":"application/json, text/event-stream","content-type":"application/json","mcp-session-id":"b1c70a2be90b42f190926156add89544","mcp-protocol-version":"2025-11-25"},"st":202,"sh":{"content-type":"application/json","mcp-session-id":"b1c70a2be90b42f190926156add89544"},"rb":"{\"jsonrpc\":\"2.0\",\"method\":\"notifications/initialized\"}","rbn":54,"sb":"","sbn":0},{"t":6,"m":"GET","path":"/mcp","rh":{"accept":"application/json, text/event-stream","content-type":"application/json","mcp-session-id":"b1c70a2be90b42f190926156add89544","mcp-protocol-version":"2025-11-25"},"st":200,"sh":{"content-type":"text/event-stream","mcp-session-id":"b1c70a2be90b42f190926156add89544"},"rb":"","rbn":0,"sb":"","sbn":0},{"t":8,"m":"POST","path":"/mcp","rh":{"accept":"application/json, text/event-stream","content-type":"application/json","mcp-session-id":"b1c70a2be90b42f190926156add89544","mcp-protocol-version":"2025-11-25"},"st":200,"sh":{"content-type":"text/event-stream","mcp-session-id":"b1c70a2be90b42f190926156add89544"},"rb":"{\"jsonrpc\":\"2.0\",\"id\":2,\"method\":\"tools/call\",\"params\":{\"name\":\"delete_file\",\"arguments\":{\"path\":\"notes.txt\"},\"_meta\":{\"progressToken\":2}}}","rbn":139,"sb":"event: message\ndata: {\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"elicitation/create\",\"params\":{\"mode\":\"form\",\"message\":\"Really delete notes.txt?\",\"requestedSchema\":{\"properties\":{\"value\":{\"title\":\"Value\",\"type\":\"boolean\"}},\"required\":[\"value\"],\"type\":\"object\"},\"_meta\":{}}}\n\nevent: message\ndata: {\"jsonrpc\":\"2.0\",\"id\":2,\"result\":{\"_meta\":{\"fastmcp\":{\"wrap_result\":true}},\"content\":[{\"text\":\"deleted notes.txt\",\"type\":\"text\"}],\"isError\":false,\"structuredContent\":{\"result\":\"deleted notes.txt\"}}}\n\n","sbn":492},{"t":12,"m":"POST","path":"/mcp","rh":{"accept":"application/json, text/event-stream","content-type":"application/json","mcp-session-id":"b1c70a2be90b42f190926156add89544","mcp-protocol-version":"2025-11-25"},"st":202,"sh":{"content-type":"application/json","mcp-session-id":"b1c70a2be90b42f190926156add89544"},"rb":"{\"jsonrpc\":\"2.0\",\"id\":1,\"result\":{\"action\":\"accept\",\"content\":{\"value\":true}}}","rbn":78,"sb":"","sbn":0},{"t":15,"m":"POST","path":"/mcp","rh":{"accept":"application/json, text/event-stream","content-type":"application/json","mcp-session-id":"b1c70a2be90b42f190926156add89544","mcp-protocol-version":"2025-11-25"},"st":200,"sh":{"content-type":"text/event-stream","mcp-session-id":"b1c70a2be90b42f190926156add89544"},"rb":"{\"jsonrpc\":\"2.0\",\"id\":3,\"method\":\"tools/list\",\"params\":{\"_meta\":{}}}","rbn":68,"sb":"event: message\ndata: {\"jsonrpc\":\"2.0\",\"id\":3,\"result\":{\"tools\":[{\"_meta\":{\"fastmcp\":{\"tags\":[]}},\"description\":\"Delete a file after the user confirms.\",\"inputSchema\":{\"properties\":{\"path\":{\"type\":\"string\"}},\"required\":[\"path\"],\"type\":\"object\",\"additionalProperties\":false},\"name\":\"delete_file\",\"outputSchema\":{\"properties\":{\"result\":{\"type\":\"string\"}},\"required\":[\"result\"],\"type\":\"object\",\"x-fastmcp-wrap-result\":true},\"title\":\"Delete File\"}]}}\n\n","sbn":450},{"t":19,"m":"DELETE","path":"/mcp","rh":{"accept":"application/json, text/event-stream","content-type":"application/json","mcp-session-id":"b1c70a2be90b42f190926156add89544","mcp-protocol-version":"2025-11-25"},"st":200,"sh":{"content-type":"application/json","mcp-session-id":"b1c70a2be90b42f190926156add89544"},"rb":"","rbn":0,"sb":"","sbn":0}]},"task_modern":{"result":"3 cups ready","seconds":1.28,"wire":[{"t":52,"m":"POST","path":"/mcp","rh":{"accept":"application/json, text/event-stream","content-type":"application/json","mcp-protocol-version":"2026-07-28","mcp-method":"server/discover"},"st":200,"sh":{"content-type":"application/json"},"rb":"{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"server/discover\",\"params\":{\"_meta\":{\"io.modelcontextprotocol/protocolVersion\":\"2026-07-28\",\"io.modelcontextprotocol/clientInfo\":{\"name\":\"mcp\",\"version\":\"0.1.0\"},\"io.modelcontextprotocol/clientCapabilities\":{\"extensions\":{\"io.modelcontextprotocol/tasks\":{}}}}}}","rbn":294,"sb":"{\"jsonrpc\":\"2.0\",\"id\":1,\"result\":{\"_meta\":{\"io.modelcontextprotocol/serverInfo\":{\"name\":\"brewery\",\"version\":\"4.0.8\"}},\"ttlMs\":0,\"cacheScope\":\"private\",\"supportedVersions\":[\"2026-07-28\"],\"capabilities\":{\"logging\":{},\"prompts\":{\"listChanged\":false},\"resources\":{\"subscribe\":false,\"listChanged\":false},\"tools\":{\"listChanged\":false},\"extensions\":{\"io.modelcontextprotocol/ui\":{},\"io.modelcontextprotocol/tasks\":{}}},\"resultType\":\"complete\"}}","sbn":437},{"t":55,"m":"POST","path":"/mcp","rh":{"accept":"application/json, text/event-stream","content-type":"application/json","mcp-protocol-version":"2026-07-28","mcp-method":"tools/call","mcp-name":"brew"},"st":200,"sh":{"content-type":"application/json"},"rb":"{\"jsonrpc\":\"2.0\",\"id\":2,\"method\":\"tools/call\",\"params\":{\"name\":\"brew\",\"arguments\":{\"cups\":3},\"_meta\":{\"io.modelcontextprotocol/protocolVersion\":\"2026-07-28\",\"io.modelcontextprotocol/clientInfo\":{\"name\":\"mcp\",\"version\":\"0.1.0\"},\"io.modelcontextprotocol/clientCapabilities\":{\"extensions\":{\"io.modelcontextprotocol/tasks\":{}}},\"io.modelcontextprotocol/logLevel\":\"debug\",\"progressToken\":2}}}","rbn":387,"sb":"{\"jsonrpc\":\"2.0\",\"id\":2,\"result\":{\"taskId\":\"tEJK0ceho5O3Czaca9HYZDH2hmlGzMSOfAGIVeVuQRc\",\"status\":\"working\",\"createdAt\":\"2026-09-24T10:27:27.272853+00:00\",\"lastUpdatedAt\":\"2026-09-24T10:27:27.272853+00:00\",\"ttlMs\":900000,\"pollIntervalMs\":5000,\"resultType\":\"task\",\"_meta\":{\"io.modelcontextprotocol/serverInfo\":{\"name\":\"brewery\",\"version\":\"4.0.8\"}}}}","sbn":348},{"t":59,"m":"POST","path":"/mcp","rh":{"accept":"application/json, text/event-stream","content-type":"application/json","mcp-protocol-version":"2026-07-28","mcp-method":"tasks/get"},"st":200,"sh":{"content-type":"application/json"},"rb":"{\"jsonrpc\":\"2.0\",\"id\":3,\"method\":\"tasks/get\",\"params\":{\"taskId\":\"tEJK0ceho5O3Czaca9HYZDH2hmlGzMSOfAGIVeVuQRc\",\"_meta\":{\"io.modelcontextprotocol/protocolVersion\":\"2026-07-28\",\"io.modelcontextprotocol/clientInfo\":{\"name\":\"mcp\",\"version\":\"0.1.0\"},\"io.modelcontextprotocol/clientCapabilities\":{\"extensions\":{\"io.modelcontextprotocol/tasks\":{}}},\"io.modelcontextprotocol/logLevel\":\"debug\"}}}","rbn":386,"sb":"{\"jsonrpc\":\"2.0\",\"id\":3,\"result\":{\"taskId\":\"tEJK0ceho5O3Czaca9HYZDH2hmlGzMSOfAGIVeVuQRc\",\"status\":\"working\",\"createdAt\":\"2026-09-24T10:27:27.272853+00:00\",\"lastUpdatedAt\":\"2026-09-24T10:27:27.276140+00:00\",\"ttlMs\":900000,\"statusMessage\":\"cup 1\",\"pollIntervalMs\":5000,\"resultType\":\"complete\",\"_meta\":{\"io.modelcontextprotocol/serverInfo\":{\"name\":\"brewery\",\"version\":\"4.0.8\"}}}}","sbn":376},{"t":80,"m":"POST","path":"/mcp","rh":{"accept":"application/json, text/event-stream","content-type":"application/json","mcp-protocol-version":"2026-07-28","mcp-method":"tasks/get"},"st":200,"sh":{"content-type":"application/json"},"rb":"{\"jsonrpc\":\"2.0\",\"id\":4,\"method\":\"tasks/get\",\"params\":{\"taskId\":\"tEJK0ceho5O3Czaca9HYZDH2hmlGzMSOfAGIVeVuQRc\",\"_meta\":{\"io.modelcontextprotocol/protocolVersion\":\"2026-07-28\",\"io.modelcontextprotocol/clientInfo\":{\"name\":\"mcp\",\"version\":\"0.1.0\"},\"io.modelcontextprotocol/clientCapabilities\":{\"extensions\":{\"io.modelcontextprotocol/tasks\":{}}},\"io.modelcontextprotocol/logLevel\":\"debug\"}}}","rbn":386,"sb":"{\"jsonrpc\":\"2.0\",\"id\":4,\"result\":{\"taskId\":\"tEJK0ceho5O3Czaca9HYZDH2hmlGzMSOfAGIVeVuQRc\",\"status\":\"working\",\"createdAt\":\"2026-09-24T10:27:27.272853+00:00\",\"lastUpdatedAt\":\"2026-09-24T10:27:27.297527+00:00\",\"ttlMs\":900000,\"statusMessage\":\"cup 1\",\"pollIntervalMs\":5000,\"resultType\":\"complete\",\"_meta\":{\"io.modelcontextprotocol/serverInfo\":{\"name\":\"brewery\",\"version\":\"4.0.8\"}}}}","sbn":376},{"t":122,"m":"POST","path":"/mcp","rh":{"accept":"application/json, text/event-stream","content-type":"application/json","mcp-protocol-version":"2026-07-28","mcp-method":"tasks/get"},"st":200,"sh":{"content-type":"application/json"},"rb":"{\"jsonrpc\":\"2.0\",\"id\":5,\"method\":\"tasks/get\",\"params\":{\"taskId\":\"tEJK0ceho5O3Czaca9HYZDH2hmlGzMSOfAGIVeVuQRc\",\"_meta\":{\"io.modelcontextprotocol/protocolVersion\":\"2026-07-28\",\"io.modelcontextprotocol/clientInfo\":{\"name\":\"mcp\",\"version\":\"0.1.0\"},\"io.modelcontextprotocol/clientCapabilities\":{\"extensions\":{\"io.modelcontextprotocol/tasks\":{}}},\"io.modelcontextprotocol/logLevel\":\"debug\"}}}","rbn":386,"sb":"{\"jsonrpc\":\"2.0\",\"id\":5,\"result\":{\"taskId\":\"tEJK0ceho5O3Czaca9HYZDH2hmlGzMSOfAGIVeVuQRc\",\"status\":\"working\",\"createdAt\":\"2026-09-24T10:27:27.272853+00:00\",\"lastUpdatedAt\":\"2026-09-24T10:27:27.339027+00:00\",\"ttlMs\":900000,\"statusMessage\":\"cup 1\",\"pollIntervalMs\":5000,\"resultType\":\"complete\",\"_meta\":{\"io.modelcontextprotocol/serverInfo\":{\"name\":\"brewery\",\"version\":\"4.0.8\"}}}}","sbn":376},{"t":204,"m":"POST","path":"/mcp","rh":{"accept":"application/json, text/event-stream","content-type":"application/json","mcp-protocol-version":"2026-07-28","mcp-method":"tasks/get"},"st":200,"sh":{"content-type":"application/json"},"rb":"{\"jsonrpc\":\"2.0\",\"id\":6,\"method\":\"tasks/get\",\"params\":{\"taskId\":\"tEJK0ceho5O3Czaca9HYZDH2hmlGzMSOfAGIVeVuQRc\",\"_meta\":{\"io.modelcontextprotocol/protocolVersion\":\"2026-07-28\",\"io.modelcontextprotocol/clientInfo\":{\"name\":\"mcp\",\"version\":\"0.1.0\"},\"io.modelcontextprotocol/clientCapabilities\":{\"extensions\":{\"io.modelcontextprotocol/tasks\":{}}},\"io.modelcontextprotocol/logLevel\":\"debug\"}}}","rbn":386,"sb":"{\"jsonrpc\":\"2.0\",\"id\":6,\"result\":{\"taskId\":\"tEJK0ceho5O3Czaca9HYZDH2hmlGzMSOfAGIVeVuQRc\",\"status\":\"working\",\"createdAt\":\"2026-09-24T10:27:27.272853+00:00\",\"lastUpdatedAt\":\"2026-09-24T10:27:27.420763+00:00\",\"ttlMs\":900000,\"statusMessage\":\"cup 1\",\"pollIntervalMs\":5000,\"resultType\":\"complete\",\"_meta\":{\"io.modelcontextprotocol/serverInfo\":{\"name\":\"brewery\",\"version\":\"4.0.8\"}}}}","sbn":376},{"t":366,"m":"POST","path":"/mcp","rh":{"accept":"application/json, text/event-stream","content-type":"application/json","mcp-protocol-version":"2026-07-28","mcp-method":"tasks/get"},"st":200,"sh":{"content-type":"application/json"},"rb":"{\"jsonrpc\":\"2.0\",\"id\":7,\"method\":\"tasks/get\",\"params\":{\"taskId\":\"tEJK0ceho5O3Czaca9HYZDH2hmlGzMSOfAGIVeVuQRc\",\"_meta\":{\"io.modelcontextprotocol/protocolVersion\":\"2026-07-28\",\"io.modelcontextprotocol/clientInfo\":{\"name\":\"mcp\",\"version\":\"0.1.0\"},\"io.modelcontextprotocol/clientCapabilities\":{\"extensions\":{\"io.modelcontextprotocol/tasks\":{}}},\"io.modelcontextprotocol/logLevel\":\"debug\"}}}","rbn":386,"sb":"{\"jsonrpc\":\"2.0\",\"id\":7,\"result\":{\"taskId\":\"tEJK0ceho5O3Czaca9HYZDH2hmlGzMSOfAGIVeVuQRc\",\"status\":\"working\",\"createdAt\":\"2026-09-24T10:27:27.272853+00:00\",\"lastUpdatedAt\":\"2026-09-24T10:27:27.582841+00:00\",\"ttlMs\":900000,\"statusMessage\":\"cup 1\",\"pollIntervalMs\":5000,\"resultType\":\"complete\",\"_meta\":{\"io.modelcontextprotocol/serverInfo\":{\"name\":\"brewery\",\"version\":\"4.0.8\"}}}}","sbn":376},{"t":688,"m":"POST","path":"/mcp","rh":{"accept":"application/json, text/event-stream","content-type":"application/json","mcp-protocol-version":"2026-07-28","mcp-method":"tasks/get"},"st":200,"sh":{"content-type":"application/json"},"rb":"{\"jsonrpc\":\"2.0\",\"id\":8,\"method\":\"tasks/get\",\"params\":{\"taskId\":\"tEJK0ceho5O3Czaca9HYZDH2hmlGzMSOfAGIVeVuQRc\",\"_meta\":{\"io.modelcontextprotocol/protocolVersion\":\"2026-07-28\",\"io.modelcontextprotocol/clientInfo\":{\"name\":\"mcp\",\"version\":\"0.1.0\"},\"io.modelcontextprotocol/clientCapabilities\":{\"extensions\":{\"io.modelcontextprotocol/tasks\":{}}},\"io.modelcontextprotocol/logLevel\":\"debug\"}}}","rbn":386,"sb":"{\"jsonrpc\":\"2.0\",\"id\":8,\"result\":{\"taskId\":\"tEJK0ceho5O3Czaca9HYZDH2hmlGzMSOfAGIVeVuQRc\",\"status\":\"working\",\"createdAt\":\"2026-09-24T10:27:27.272853+00:00\",\"lastUpdatedAt\":\"2026-09-24T10:27:27.904961+00:00\",\"ttlMs\":900000,\"statusMessage\":\"cup 2\",\"pollIntervalMs\":5000,\"resultType\":\"complete\",\"_meta\":{\"io.modelcontextprotocol/serverInfo\":{\"name\":\"brewery\",\"version\":\"4.0.8\"}}}}","sbn":376},{"t":1330,"m":"POST","path":"/mcp","rh":{"accept":"application/json, text/event-stream","content-type":"application/json","mcp-protocol-version":"2026-07-28","mcp-method":"tasks/get"},"st":200,"sh":{"content-type":"application/json"},"rb":"{\"jsonrpc\":\"2.0\",\"id\":9,\"method\":\"tasks/get\",\"params\":{\"taskId\":\"tEJK0ceho5O3Czaca9HYZDH2hmlGzMSOfAGIVeVuQRc\",\"_meta\":{\"io.modelcontextprotocol/protocolVersion\":\"2026-07-28\",\"io.modelcontextprotocol/clientInfo\":{\"name\":\"mcp\",\"version\":\"0.1.0\"},\"io.modelcontextprotocol/clientCapabilities\":{\"extensions\":{\"io.modelcontextprotocol/tasks\":{}}},\"io.modelcontextprotocol/logLevel\":\"debug\"}}}","rbn":386,"sb":"{\"jsonrpc\":\"2.0\",\"id\":9,\"result\":{\"taskId\":\"tEJK0ceho5O3Czaca9HYZDH2hmlGzMSOfAGIVeVuQRc\",\"status\":\"completed\",\"createdAt\":\"2026-09-24T10:27:27.272853+00:00\",\"lastUpdatedAt\":\"2026-09-24T10:27:28.547433+00:00\",\"ttlMs\":900000,\"pollIntervalMs\":5000,\"resultType\":\"complete\",\"result\":{\"_meta\":{\"fastmcp\":{\"wrap_result\":true}},\"content\":[{\"type\":\"text\",\"text\":\"3 cups ready\"}],\"structuredContent\":{\"result\":\"3 cups ready\"},\"isError\":false,\"resultType\":\"complete\"},\"_meta\":{\"io.modelcontextprotocol/serverInfo\":{\"name\":\"brewery\",\"version\":\"4.0.8\"}}}}","sbn":542},{"t":1332,"m":"POST","path":"/mcp","rh":{"accept":"application/json, text/event-stream","content-type":"application/json","mcp-protocol-version":"2026-07-28","mcp-method":"tools/list"},"st":200,"sh":{"content-type":"application/json"},"rb":"{\"jsonrpc\":\"2.0\",\"id\":10,\"method\":\"tools/list\",\"params\":{\"_meta\":{\"io.modelcontextprotocol/protocolVersion\":\"2026-07-28\",\"io.modelcontextprotocol/clientInfo\":{\"name\":\"mcp\",\"version\":\"0.1.0\"},\"io.modelcontextprotocol/clientCapabilities\":{\"extensions\":{\"io.modelcontextprotocol/tasks\":{}}},\"io.modelcontextprotocol/logLevel\":\"debug\"}}}","rbn":333,"sb":"{\"jsonrpc\":\"2.0\",\"id\":10,\"result\":{\"cacheScope\":\"private\",\"resultType\":\"complete\",\"tools\":[{\"_meta\":{\"fastmcp\":{\"tags\":[]}},\"description\":\"Brew some cups of tea (0.4 s each).\",\"inputSchema\":{\"type\":\"object\",\"additionalProperties\":false,\"properties\":{\"cups\":{\"type\":\"integer\"}},\"required\":[\"cups\"]},\"name\":\"brew\",\"outputSchema\":{\"properties\":{\"result\":{\"type\":\"string\"}},\"required\":[\"result\"],\"type\":\"object\",\"x-fastmcp-wrap-result\":true},\"title\":\"Brew\"}],\"ttlMs\":0,\"_meta\":{\"io.modelcontextprotocol/serverInfo\":{\"name\":\"brewery\",\"version\":\"4.0.8\"}}}}","sbn":550}]},"route_cache":{"result":"acme/Taipei: sunny","list_tools_calls":3,"progress":[[1.0,2.0,"fetching"],[2.0,2.0,"done"]],"wire":[{"t":53,"m":"POST","path":"/mcp","rh":{"accept":"application/json, text/event-stream","content-type":"application/json","mcp-protocol-version":"2026-07-28","mcp-method":"server/discover"},"st":200,"sh":{"content-type":"application/json"},"rb":"{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"server/discover\",\"params\":{\"_meta\":{\"io.modelcontextprotocol/protocolVersion\":\"2026-07-28\",\"io.modelcontextprotocol/clientInfo\":{\"name\":\"mcp\",\"version\":\"0.1.0\"},\"io.modelcontextprotocol/clientCapabilities\":{\"extensions\":{\"io.modelcontextprotocol/tasks\":{}}}}}}","rbn":294,"sb":"{\"jsonrpc\":\"2.0\",\"id\":1,\"result\":{\"_meta\":{\"io.modelcontextprotocol/serverInfo\":{\"name\":\"weather\",\"version\":\"4.0.8\"}},\"ttlMs\":300000,\"cacheScope\":\"public\",\"supportedVersions\":[\"2026-07-28\"],\"capabilities\":{\"logging\":{},\"prompts\":{\"listChanged\":false},\"resources\":{\"subscribe\":false,\"listChanged\":false},\"tools\":{\"listChanged\":false},\"extensions\":{\"io.modelcontextprotocol/ui\":{}}},\"resultType\":\"complete\"}}","sbn":406},{"t":55,"m":"POST","path":"/mcp","rh":{"accept":"application/json, text/event-stream","content-type":"application/json","mcp-protocol-version":"2026-07-28","mcp-method":"tools/list"},"st":200,"sh":{"content-type":"application/json"},"rb":"{\"jsonrpc\":\"2.0\",\"id\":2,\"method\":\"tools/list\",\"params\":{\"_meta\":{\"io.modelcontextprotocol/protocolVersion\":\"2026-07-28\",\"io.modelcontextprotocol/clientInfo\":{\"name\":\"mcp\",\"version\":\"0.1.0\"},\"io.modelcontextprotocol/clientCapabilities\":{\"extensions\":{\"io.modelcontextprotocol/tasks\":{}}},\"io.modelcontextprotocol/logLevel\":\"debug\"}}}","rbn":332,"sb":"{\"jsonrpc\":\"2.0\",\"id\":2,\"result\":{\"cacheScope\":\"public\",\"resultType\":\"complete\",\"tools\":[{\"_meta\":{\"fastmcp\":{\"tags\":[]}},\"description\":\"Forecast for one tenant's city.\",\"inputSchema\":{\"type\":\"object\",\"additionalProperties\":false,\"properties\":{\"tenant\":{\"type\":\"string\",\"x-mcp-header\":\"Tenant\"},\"city\":{\"type\":\"string\"}},\"required\":[\"tenant\",\"city\"]},\"name\":\"forecast\",\"outputSchema\":{\"properties\":{\"result\":{\"type\":\"string\"}},\"required\":[\"result\"],\"type\":\"object\",\"x-fastmcp-wrap-result\":true},\"title\":\"Forecast\"}],\"ttlMs\":300000,\"_meta\":{\"io.modelcontextprotocol/serverInfo\":{\"name\":\"weather\",\"version\":\"4.0.8\"}}}}","sbn":616},{"t":57,"m":"POST","path":"/mcp","rh":{"accept":"application/json, text/event-stream","content-type":"application/json","mcp-protocol-version":"2026-07-28","mcp-method":"tools/call","mcp-name":"forecast","mcp-param-tenant":"acme"},"st":200,"sh":{"content-type":"text/event-stream"},"rb":"{\"jsonrpc\":\"2.0\",\"id\":3,\"method\":\"tools/call\",\"params\":{\"name\":\"forecast\",\"arguments\":{\"tenant\":\"acme\",\"city\":\"Taipei\"},\"_meta\":{\"io.modelcontextprotocol/protocolVersion\":\"2026-07-28\",\"io.modelcontextprotocol/clientInfo\":{\"name\":\"mcp\",\"version\":\"0.1.0\"},\"io.modelcontextprotocol/clientCapabilities\":{\"extensions\":{\"io.modelcontextprotocol/tasks\":{}}},\"io.modelcontextprotocol/logLevel\":\"debug\",\"progressToken\":3}}}","rbn":414,"sb":"event: message\ndata: {\"jsonrpc\":\"2.0\",\"method\":\"notifications/progress\",\"params\":{\"progressToken\":3,\"progress\":1.0,\"total\":2.0,\"message\":\"fetching\"}}\n\nevent: message\ndata: {\"jsonrpc\":\"2.0\",\"method\":\"notifications/progress\",\"params\":{\"progressToken\":3,\"progress\":2.0,\"total\":2.0,\"message\":\"done\"}}\n\nevent: message\ndata: {\"jsonrpc\":\"2.0\",\"id\":3,\"result\":{\"_meta\":{\"fastmcp\":{\"wrap_result\":true},\"io.modelcontextprotocol/serverInfo\":{\"name\":\"weather\",\"version\":\"4.0.8\"}},\"content\":[{\"text\":\"acme/Taipei: sunny\",\"type\":\"text\"}],\"isError\":false,\"resultType\":\"complete\",\"structuredContent\":{\"result\":\"acme/Taipei: sunny\"}}}\n\n","sbn":628}]}},"grid":{"responses":[[400,"{\"jsonrpc\":\"2.0\",\"id\":null,\"error\":{\"code\":-32600,\"message\":\"Bad Request: Missing session ID\"}}"],[400,"{\"jsonrpc\":\"2.0\",\"id\":1,\"error\":{\"code\":-32602,\"message\":\"params._meta must be an object carrying the required 'io.modelcontextprotocol/protocolVersion' and 'io.modelcontextprotocol/clientCapabilities' envelope keys\"}}"],[400,"{\"jsonrpc\":\"2.0\",\"id\":1,\"error\":{\"code\":-32020,\"message\":\"mcp-method header does not match the request body's method\"}}"],[400,"{\"jsonrpc\":\"2.0\",\"id\":1,\"error\":{\"code\":-32020,\"message\":\"mcp-protocol-version header does not match the request envelope's protocol version\"}}"],[400,"{\"jsonrpc\":\"2.0\",\"id\":1,\"error\":{\"code\":-32602,\"message\":\"params._meta is missing the required envelope key(s): io.modelcontextprotocol/clientCapabilities\"}}"],[400,"{\"jsonrpc\":\"2.0\",\"id\":1,\"error\":{\"code\":-32020,\"message\":\"mcp-name header does not match the request body's 'name' parameter\"}}"],[200,"{\"jsonrpc\":\"2.0\",\"id\":1,\"result\":{\"_meta\":{\"fastmcp\":{\"wrap_result\":true},\"io.modelcontextprotocol/serverInfo\":{\"name\":\"calc\",\"version\":\"4.0.8\"}},\"content\":[{\"text\":\"5\",\"type\":\"text\"}],\"isError\":false,\"resultType\":\"complete\",\"structuredContent\":{\"result\":5}}}"],[400,"{\"jsonrpc\":\"2.0\",\"id\":1,\"error\":{\"code\":-32022,\"message\":\"Unsupported protocol version\",\"data\":{\"supported\":[\"2026-07-28\"],\"requested\":\"2099-01-01\"}}}"]],"map":{"none|none|none|none":0,"none|none|none|2026":0,"none|none|none|2025":0,"none|none|none|2099":0,"none|none|none|nocaps":0,"none|none|ok|none":0,"none|none|ok|2026":0,"none|none|ok|2025":0,"none|none|ok|2099":0,"none|none|ok|nocaps":0,"none|none|bad|none":0,"none|none|bad|2026":0,"none|none|bad|2025":0,"none|none|bad|2099":0,"none|none|bad|nocaps":0,"none|ok|none|none":0,"none|ok|none|2026":0,"none|ok|none|2025":0,"none|ok|none|2099":0,"none|ok|none|nocaps":0,"none|ok|ok|none":0,"none|ok|ok|2026":0,"none|ok|ok|2025":0,"none|ok|ok|2099":0,"none|ok|ok|nocaps":0,"none|ok|bad|none":0,"none|ok|bad|2026":0,"none|ok|bad|2025":0,"none|ok|bad|2099":0,"none|ok|bad|nocaps":0,"none|bad|none|none":0,"none|bad|none|2026":0,"none|bad|none|2025":0,"none|bad|none|2099":0,"none|bad|none|nocaps":0,"none|bad|ok|none":0,"none|bad|ok|2026":0,"none|bad|ok|2025":0,"none|bad|ok|2099":0,"none|bad|ok|nocaps":0,"none|bad|bad|none":0,"none|bad|bad|2026":0,"none|bad|bad|2025":0,"none|bad|bad|2099":0,"none|bad|bad|nocaps":0,"2026|none|none|none":1,"2026|none|none|2026":2,"2026|none|none|2025":3,"2026|none|none|2099":3,"2026|none|none|nocaps":4,"2026|none|ok|none":1,"2026|none|ok|2026":2,"2026|none|ok|2025":3,"2026|none|ok|2099":3,"2026|none|ok|nocaps":4,"2026|none|bad|none":1,"2026|none|bad|2026":2,"2026|none|bad|2025":3,"2026|none|bad|2099":3,"2026|none|bad|nocaps":4,"2026|ok|none|none":1,"2026|ok|none|2026":5,"2026|ok|none|2025":3,"2026|ok|none|2099":3,"2026|ok|none|nocaps":4,"2026|ok|ok|none":1,"2026|ok|ok|2026":6,"2026|ok|ok|2025":3,"2026|ok|ok|2099":3,"2026|ok|ok|nocaps":4,"2026|ok|bad|none":1,"2026|ok|bad|2026":5,"2026|ok|bad|2025":3,"2026|ok|bad|2099":3,"2026|ok|bad|nocaps":4,"2026|bad|none|none":1,"2026|bad|none|2026":2,"2026|bad|none|2025":3,"2026|bad|none|2099":3,"2026|bad|none|nocaps":4,"2026|bad|ok|none":1,"2026|bad|ok|2026":2,"2026|bad|ok|2025":3,"2026|bad|ok|2099":3,"2026|bad|ok|nocaps":4,"2026|bad|bad|none":1,"2026|bad|bad|2026":2,"2026|bad|bad|2025":3,"2026|bad|bad|2099":3,"2026|bad|bad|nocaps":4,"2025|none|none|none":0,"2025|none|none|2026":0,"2025|none|none|2025":0,"2025|none|none|2099":0,"2025|none|none|nocaps":0,"2025|none|ok|none":0,"2025|none|ok|2026":0,"2025|none|ok|2025":0,"2025|none|ok|2099":0,"2025|none|ok|nocaps":0,"2025|none|bad|none":0,"2025|none|bad|2026":0,"2025|none|bad|2025":0,"2025|none|bad|2099":0,"2025|none|bad|nocaps":0,"2025|ok|none|none":0,"2025|ok|none|2026":0,"2025|ok|none|2025":0,"2025|ok|none|2099":0,"2025|ok|none|nocaps":0,"2025|ok|ok|none":0,"2025|ok|ok|2026":0,"2025|ok|ok|2025":0,"2025|ok|ok|2099":0,"2025|ok|ok|nocaps":0,"2025|ok|bad|none":0,"2025|ok|bad|2026":0,"2025|ok|bad|2025":0,"2025|ok|bad|2099":0,"2025|ok|bad|nocaps":0,"2025|bad|none|none":0,"2025|bad|none|2026":0,"2025|bad|none|2025":0,"2025|bad|none|2099":0,"2025|bad|none|nocaps":0,"2025|bad|ok|none":0,"2025|bad|ok|2026":0,"2025|bad|ok|2025":0,"2025|bad|ok|2099":0,"2025|bad|ok|nocaps":0,"2025|bad|bad|none":0,"2025|bad|bad|2026":0,"2025|bad|bad|2025":0,"2025|bad|bad|2099":0,"2025|bad|bad|nocaps":0,"2099|none|none|none":1,"2099|none|none|2026":3,"2099|none|none|2025":3,"2099|none|none|2099":2,"2099|none|none|nocaps":4,"2099|none|ok|none":1,"2099|none|ok|2026":3,"2099|none|ok|2025":3,"2099|none|ok|2099":2,"2099|none|ok|nocaps":4,"2099|none|bad|none":1,"2099|none|bad|2026":3,"2099|none|bad|2025":3,"2099|none|bad|2099":2,"2099|none|bad|nocaps":4,"2099|ok|none|none":1,"2099|ok|none|2026":3,"2099|ok|none|2025":3,"2099|ok|none|2099":5,"2099|ok|none|nocaps":4,"2099|ok|ok|none":1,"2099|ok|ok|2026":3,"2099|ok|ok|2025":3,"2099|ok|ok|2099":7,"2099|ok|ok|nocaps":4,"2099|ok|bad|none":1,"2099|ok|bad|2026":3,"2099|ok|bad|2025":3,"2099|ok|bad|2099":5,"2099|ok|bad|nocaps":4,"2099|bad|none|none":1,"2099|bad|none|2026":3,"2099|bad|none|2025":3,"2099|bad|none|2099":2,"2099|bad|none|nocaps":4,"2099|bad|ok|none":1,"2099|bad|ok|2026":3,"2099|bad|ok|2025":3,"2099|bad|ok|2099":2,"2099|bad|ok|nocaps":4,"2099|bad|bad|none":1,"2099|bad|bad|2026":3,"2099|bad|bad|2025":3,"2099|bad|bad|2099":2,"2099|bad|bad|nocaps":4},"get_delete":{"GET":[405,"POST"],"DELETE":[405,"POST"]}},"replicas":{"round-robin|modern":{"ok":true,"result":5,"trail":[{"replica":"A","m":"POST","method":"server/discover","session":"","st":200},{"replica":"B","m":"POST","method":"tools/list","session":"","st":200},{"replica":"A","m":"POST","method":"tools/call","session":"","st":200}],"http404_body":""},"round-robin|legacy":{"ok":false,"error":"MCPError: Session not found","trail":[{"replica":"A","m":"POST","method":"initialize","session":"","st":200},{"replica":"B","m":"POST","method":"notifications/initialized","session":"67749a3e","st":404},{"replica":"A","m":"GET","method":"(GET stream)","session":"67749a3e","st":200},{"replica":"B","m":"POST","method":"tools/list","session":"67749a3e","st":404},{"replica":"A","m":"DELETE","method":"DELETE","session":"67749a3e","st":200}],"http404_body":"{\"jsonrpc\":\"2.0\",\"id\":null,\"error\":{\"code\":-32600,\"message\":\"Session not found\"}}"},"sticky|modern":{"ok":true,"result":5,"trail":[{"replica":"A","m":"POST","method":"server/discover","session":"","st":200},{"replica":"B","m":"POST","method":"tools/list","session":"","st":200},{"replica":"A","m":"POST","method":"tools/call","session":"","st":200}],"http404_body":""},"sticky|legacy":{"ok":true,"result":5,"trail":[{"replica":"A","m":"POST","method":"initialize","session":"","st":200},{"replica":"A","m":"POST","method":"notifications/initialized","session":"15122595","st":202},{"replica":"A","m":"GET","method":"(GET stream)","session":"15122595","st":200},{"replica":"A","m":"POST","method":"tools/list","session":"15122595","st":200},{"replica":"A","m":"POST","method":"tools/call","session":"15122595","st":200},{"replica":"A","m":"DELETE","method":"DELETE","session":"15122595","st":200}],"http404_body":""}},"features":{"mount":{"tools":["weather_forecast","calc_add"],"call":"Taipei: sunny"},"proxy":{"tools":["add"],"call":3,"backend_saw":["server/discover","tools/list","tools/call"]},"from_fastapi":{"tools":[["get_item",["item_id"]],["list_items",["max_price"]],["create_order",["item_id","qty"]]],"call":{"result":[{"name":"tea","price":50}]}},"from_openapi":{"tools":["get_item","list_items","create_order"],"call":{"ok":true,"total":240}},"search":{"catalog":30,"listed":["search_tools","call_tool"],"top":[["tool_00","weather forecast for a city"],["tool_10","weather forecast for a city"],["tool_20","weather forecast for a city"]]},"middleware":{"log":["tools/call add 0.6 ms","tools/call add 0.3 ms"]},"auth":{"guest-token":["read_menu"],"admin-token":["read_menu","change_price"],"no_token":[401,"Bearer"]},"sessions":{"tools":["add_to_cart","create_session","end_session"],"new_connection":["tea","cake"],"guess":"ToolError: Invalid or unknown session."},"client_group":{"tools":["calc_add","weather_forecast2"],"call":42},"resources":{"ok":"content of intro","traversal":{"docs://..%2Fsecret":"MCPError: Resource not found: 'docs://..%2Fsecret'","docs://%2Fetc%2Fpasswd":"MCPError: Resource not found: 'docs://%2Fetc%2Fpasswd'"}},"completion":{"typed":"t","values":["tea","taipei","typhoon"]},"apps":{"extensions":{"io.modelcontextprotocol/ui":{}}}},"era_errors":{"confirm|auto":"ToolError: elicitation via server-initiated requests is unavailable on 2026-07-28 connections.","summarize|auto":"ToolError: Error calling tool 'summarize': 'Context' object has no attribute 'sample'","confirm|legacy":"OK: accept","summarize|legacy":"ToolError: Error calling tool 'summarize': 'Context' object has no attribute 'sample'"}}"""
    WIRE = json.loads(WIRE_JSON)
    return (WIRE,)


@app.cell
def _(html_mod, json, plt):
    # ── 共用小工具：把側錄的 HTTP 交換變成看得懂的東西 ──
    C_MODERN, C_LEGACY, C_OLD, C_BAD, C_OK, C_INK = "#4C72B0", "#DD8452", "#8172B2", "#C44E52", "#55A868", "#1C2B33"

    def sse_msgs(text):
        """SSE 回應串流 → JSON-RPC 訊息清單。"""
        out = []
        for line in (text or "").splitlines():
            if line.startswith("data:") and line[5:].strip().startswith("{"):
                try:
                    out.append(json.loads(line[5:].strip()))
                except ValueError:
                    pass
        return out

    def body_json(text):
        if text and text.startswith("{"):
            try:
                return json.loads(text)
            except ValueError:
                return None
        return None

    def pretty(text):
        """JSON 就縮排、SSE 就拆事件；被截斷的就原樣。"""
        if not text:
            return "（空）"
        j = body_json(text)
        if j is not None:
            return json.dumps(j, indent=2, ensure_ascii=False)
        if "data:" in text:
            blocks = []
            for blk in text.split("\n\n"):
                ev, data = None, None
                for line in blk.splitlines():
                    if line.startswith("event:"):
                        ev = line[6:].strip()
                    elif line.startswith("data:"):
                        data = line[5:].strip()
                if data is None:
                    continue
                j2 = body_json(data)
                blocks.append(f"event: {ev}\n" + (json.dumps(j2, indent=2, ensure_ascii=False) if j2 is not None else data))
            return "\n\n".join(blocks)
        return text

    def rpc_label(e):
        """這一發在做什麼：新協定看 header，舊協定只能拆 body。"""
        h = e["rh"]
        if h.get("mcp-method"):
            return h["mcp-method"] + (f" {h['mcp-name']}" if h.get("mcp-name") else "")
        j = body_json(e["rb"])
        if j:
            if "method" in j:
                name = (j.get("params") or {}).get("name")
                return j["method"] + (f" {name}" if j["method"] == "tools/call" and name else "")
            if "result" in j or "error" in j:
                return f"(reply to server request id={j.get('id')})"
        if e["m"] == "GET":
            return "(open SSE stream)"
        if e["m"] == "DELETE":
            return "(end session)"
        return ""

    def server_requests(e):
        """回應串流裡，伺服器反過來發給客戶端的 JSON-RPC request（有 method 也有 id）。"""
        return [m for m in sse_msgs(e["sb"]) if "method" in m and "id" in m]

    def has_session(e):
        return "mcp-session-id" in e["rh"] or "session_id=" in e["path"]

    def has_envelope(e):
        j = body_json(e["rb"]) or {}
        meta = (j.get("params") or {}).get("_meta") or {}
        return "io.modelcontextprotocol/protocolVersion" in meta

    def result_of(e):
        j = body_json(e["sb"])
        if j is None:
            ms = sse_msgs(e["sb"])
            j = ms[-1] if ms else None
        return (j or {}).get("result") or {}

    def packet_notes(e):
        notes = []
        rj = body_json(e["rb"]) or {}
        res = result_of(e)
        if has_session(e):
            notes.append(("session", "帶著 session id——只有發這把 id 的那台伺服器認得它", C_BAD))
        if "mcp-session-id" in e["sh"] and "mcp-session-id" not in e["rh"]:
            notes.append(("發 session", "伺服器在這個回應的 header 裡發下 session id", C_BAD))
        if has_envelope(e):
            notes.append(("_meta", "body 自帶 _meta 信封：協定版本＋客戶端能力＋clientInfo", C_MODERN))
        if e["rh"].get("mcp-method"):
            notes.append(("路由 header", "method 鏡射到 Mcp-Method（tools/call 還有 Mcp-Name）——gateway 不拆 body 也知道這發在幹嘛", C_MODERN))
        if any(k.startswith("mcp-param-") for k in e["rh"]):
            notes.append(("參數 header", "工具參數被鏡射成 Mcp-Param-* header（x-mcp-header）", C_MODERN))
        if server_requests(e):
            notes.append(("伺服器反問", "回應串流裡夾著伺服器發給客戶端的 request——工具停在半路等答案", C_BAD))
        if res.get("resultType") == "input_required":
            notes.append(("input_required", "伺服器回「我需要輸入」，這一回合就正常結束了", C_MODERN))
        if (rj.get("params") or {}).get("inputResponses"):
            notes.append(("帶答案重打", "客戶端帶著 inputResponses 重打同一個工具——可以落到任何一台副本", C_MODERN))
        if "taskId" in res:
            notes.append(("task", f"任務狀態：{res.get('status')}（{res.get('statusMessage') or '—'}）", C_MODERN))
        if e["st"] == 202:
            notes.append(("202", "伺服器收下了；這一發的回應裡沒有答案", C_OLD))
        if "ttlMs" in res:
            notes.append(("快取提示", f"ttlMs={res['ttlMs']}、cacheScope={res.get('cacheScope')}", C_MODERN))
        if e["m"] == "GET" and e["path"].startswith("/sse"):
            notes.append(("長連線", "這條 GET 一直開著：之後每個答案都從這裡流回來", C_OLD))
        return notes

    def packet_html(e, i, n):
        esc = html_mod.escape

        def hdr_table(h):
            if not h:
                return '<div style="color:#8a949b;font-size:12px">（無關鍵 header）</div>'
            rows = "".join(
                f'<tr><td style="padding:2px 10px 2px 0;font-weight:700;white-space:nowrap">{esc(k)}</td>'
                f'<td style="padding:2px 0;word-break:break-all">{esc(v)}</td></tr>' for k, v in h.items())
            return f'<table style="font-family:monospace;font-size:12px;border-collapse:collapse">{rows}</table>'

        pre = ("font-family:monospace;font-size:12px;line-height:1.5;white-space:pre-wrap;word-break:break-all;"
               "background:#f4f1ea;border-radius:8px;padding:8px 10px;margin:6px 0;max-height:320px;overflow:auto")
        chips = "".join(
            f'<div style="margin:3px 0;font-size:13px"><span style="display:inline-block;min-width:5.5em;font-size:11px;'
            f'font-weight:800;color:#fff;background:{c};border-radius:6px;padding:1px 7px;margin-right:8px">{esc(t)}</span>{esc(d)}</div>'
            for t, d, c in packet_notes(e))
        st_color = C_OK if (e["st"] or 0) < 300 else C_BAD
        return f"""
    <div style="border:2px solid {C_INK};border-radius:12px;padding:10px 14px">
      <div style="font-family:monospace;font-size:14px;font-weight:800">#{i}/{n} &nbsp;{esc(e['m'])} {esc(e['path'])}
        <span style="color:{st_color}">→ {e['st']}</span></div>
      <div style="font-size:13px;color:#5b6770;margin:2px 0 6px">這一發在做：<b>{esc(rpc_label(e) or '—')}</b></div>
      {chips}
      <div style="margin-top:10px;font-size:12px;font-weight:800;letter-spacing:.05em;color:{C_MODERN}">▶ 請求 header</div>
      {hdr_table(e['rh'])}
      <div style="margin-top:6px;font-size:12px;font-weight:800;letter-spacing:.05em;color:{C_MODERN}">▶ 請求 body（{e['rbn']} bytes）</div>
      <div style="{pre}">{esc(pretty(e['rb']))}</div>
      <div style="margin-top:10px;font-size:12px;font-weight:800;letter-spacing:.05em;color:{C_LEGACY}">◀ 回應 header</div>
      {hdr_table(e['sh'])}
      <div style="margin-top:6px;font-size:12px;font-weight:800;letter-spacing:.05em;color:{C_LEGACY}">◀ 回應 body（{e['sbn']} bytes）</div>
      <div style="{pre}">{esc(pretty(e['sb']))}</div>
    </div>"""

    def seq_fig(wire, title):
        """把一串側錄畫成循序圖（client ↔ server）。"""
        events = {}
        for e in wire:
            if e["m"] == "GET" and e["path"].startswith("/sse"):
                for m in sse_msgs(e["sb"]):
                    if "id" in m and "result" in m:
                        events[m["id"]] = m
        rows = []
        for e in wire:
            rows.append(("req", f"{e['m']} {rpc_label(e)}"))
            for p in server_requests(e):
                rows.append(("push", f"{p['method']}  (server -> client request)"))
            res = result_of(e)
            extra = ""
            if e["m"] == "GET":
                extra = "  stream open"
            elif res.get("resultType") == "input_required":
                extra = "  input_required"
            elif "taskId" in res:
                extra = f"  task {res.get('status')}"
            elif server_requests(e):
                extra = "  (final result later, same stream)"
            elif "mcp-session-id" in e["sh"] and "mcp-session-id" not in e["rh"]:
                extra = "  + session id"
            rows.append(("resp", f"{e['st']}{extra}"))
            rid = (body_json(e["rb"]) or {}).get("id")
            if e["st"] == 202 and rid in events:
                rows.append(("event", f"SSE event on the GET stream: result id={rid}"))
        n = len(rows)
        fig, ax = plt.subplots(figsize=(6.4, 0.34 * n + 1.0))
        xc, xs = 0.1, 0.9
        ax.set_xlim(0, 1)
        ax.set_ylim(-n - 0.2, 1.1)
        ax.axis("off")
        for x, lab in ((xc, "client"), (xs, "server")):
            ax.plot([x, x], [-n - 0.1, 0.55], color="#9aa3a8", lw=1.2, zorder=1)
            ax.text(x, 0.8, lab, ha="center", va="center", fontsize=10, fontweight="bold",
                    bbox={"boxstyle": "round,pad=0.35", "fc": "#f4f1ea", "ec": C_INK})
        style = {"req": (xc, xs, C_INK, "-"), "resp": (xs, xc, "#7d868c", "--"),
                 "push": (xs, xc, C_BAD, "-"), "event": (xs, xc, C_OLD, "-")}
        for i, (kind, text) in enumerate(rows):
            y = -i - 0.3
            x0, x1, col, ls = style[kind]
            ax.annotate("", xy=(x1, y), xytext=(x0, y),
                        arrowprops={"arrowstyle": "-|>", "color": col, "lw": 1.6 if kind != "resp" else 1.1, "linestyle": ls})
            ax.text(0.5, y + 0.12, text, ha="center", va="bottom", fontsize=8, color=col,
                    fontweight="bold" if kind in ("req", "push") else "normal", family="monospace")
        ax.set_title(title, fontsize=10, fontweight="bold", loc="left")
        fig.tight_layout()
        return fig

    def wire_stats(wire):
        return {
            "HTTP 請求數": len(wire),
            "帶 session id 的請求": sum(1 for e in wire if has_session(e)),
            "自帶 _meta 信封的請求": sum(1 for e in wire if has_envelope(e)),
            "伺服器反向發出的 request": sum(len(server_requests(e)) for e in wire),
            "body 總位元組（雙向）": sum(e["rbn"] + e["sbn"] for e in wire),
        }
    return (
        C_BAD,
        C_INK,
        C_LEGACY,
        C_MODERN,
        C_OK,
        C_OLD,
        packet_html,
        rpc_label,
        seq_fig,
        wire_stats,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 1️⃣ 版本地圖：MCP 兩年改了五版

    MCP 的版本號是**日期**，意思是「最後一次做了不相容改動的那一天」。從 2024-11-05 第一版到現行的
    **2026-07-28**，一共五個版本。下圖把每一版有哪些機制排成一張表（資料來源：modelcontextprotocol.io
    各版 changelog 與 deprecated 登記表，2026-09-24 查閱）——注意最後一欄：**這是第一次一口氣拿掉一整排東西**。
    """
    )
    return


@app.cell
def _(C_BAD, C_INK, C_MODERN, np, plt):
    VERSIONS = ["2024-11-05", "2025-03-26", "2025-06-18", "2025-11-25", "2026-07-28"]
    # 狀態：0 無、1 有、2 這一版新增、3 棄用（還在但排定移除）、4 這一版移除
    MATRIX = [
        ("initialize handshake", [1, 1, 1, 1, 4]),
        ("transport-level session", [1, 1, 1, 1, 4]),
        ("HTTP+SSE transport", [1, 3, 3, 3, 3]),
        ("Streamable HTTP", [0, 2, 1, 1, 1]),
        ("JSON-RPC batching", [0, 2, 4, 0, 0]),
        ("OAuth 2.1 authorization", [0, 2, 1, 1, 1]),
        ("MCP-Protocol-Version header", [0, 0, 2, 1, 1]),
        ("structured tool output", [0, 0, 2, 1, 1]),
        ("elicitation (ask the user)", [0, 0, 2, 1, 1]),
        ("tasks (long-running work)", [0, 0, 0, 2, 1]),
        ("server -> client requests", [1, 1, 1, 1, 4]),
        ("sampling / roots / logging", [1, 1, 1, 1, 3]),
        ("GET stream + resumability", [0, 2, 1, 1, 4]),
        ("ping", [1, 1, 1, 1, 4]),
        ("server/discover", [0, 0, 0, 0, 2]),
        ("per-request _meta envelope", [0, 0, 0, 0, 2]),
        ("Mcp-Method / Mcp-Name headers", [0, 0, 0, 0, 2]),
        ("multi round-trip (input_required)", [0, 0, 0, 0, 2]),
        ("cache hints ttlMs / cacheScope", [0, 0, 0, 0, 2]),
        ("subscriptions/listen", [0, 0, 0, 0, 2]),
    ]
    _fig, _ax = plt.subplots(figsize=(6.4, 6.6))
    _face = {0: "#ffffff", 1: "#c9d6ea", 2: C_MODERN, 3: "#e6e1d6", 4: "#ffffff"}
    for _r, (_name, _st) in enumerate(MATRIX):
        for _c, _s in enumerate(_st):
            _ax.add_patch(plt.Rectangle((_c, _r), 0.94, 0.86, facecolor=_face[_s], edgecolor="#d5d0c5",
                                        hatch="////" if _s == 3 else None, lw=0.8))
            if _s == 4:
                _ax.text(_c + 0.47, _r + 0.45, "removed", ha="center", va="center", fontsize=7,
                         color=C_BAD, fontweight="bold")
            elif _s == 2:
                _ax.text(_c + 0.47, _r + 0.45, "new", ha="center", va="center", fontsize=7, color="#fff",
                         fontweight="bold")
            elif _s == 3:
                _ax.text(_c + 0.47, _r + 0.45, "deprecated", ha="center", va="center", fontsize=6.5, color="#6b6457")
    _ax.set_xlim(0, len(VERSIONS))
    _ax.set_ylim(len(MATRIX), -0.2)
    _ax.set_xticks(np.arange(len(VERSIONS)) + 0.47, [v.replace("-", "-\n", 1) for v in VERSIONS], fontsize=8.5)
    _ax.xaxis.tick_top()
    _ax.set_yticks(np.arange(len(MATRIX)) + 0.43, [m[0] for m in MATRIX], fontsize=8.5)
    _ax.tick_params(length=0)
    for _sp in _ax.spines.values():
        _sp.set_visible(False)
    _ax.axvline(4 - 0.03, color=C_INK, lw=1.4)
    _ax.set_title("MCP spec revisions: what exists in each (source: official changelogs)", fontsize=9.5,
                  fontweight="bold", pad=34)
    _fig.tight_layout()
    _fig
    return (VERSIONS,)


@app.cell
def _(VERSIONS, mo):
    version_pick = mo.ui.dropdown(options=VERSIONS, value="2026-07-28", label="看哪一版改了什麼")
    version_pick
    return (version_pick,)


@app.cell
def _(C_BAD, C_MODERN, C_OLD, html_mod, mo, version_pick):
    # 摘自官方 changelog（modelcontextprotocol.io/specification/<版本>/changelog，2026-09-24 查閱）
    CHANGELOG = {
        "2024-11-05": ("誕生：有狀態連線", [
            ("基礎", "JSON-RPC 2.0；規格原文列出的基礎協定就是「Stateful connections」＋initialize 握手協商能力"),
            ("傳輸", "stdio 與 HTTP+SSE：先 GET 開一條 SSE 長連線，請求 POST 到另一個 /messages 端點，答案從長連線流回來"),
            ("原語", "伺服器端 tools／resources／prompts；客戶端 sampling、roots"),
            ("工具", "ping、progress、cancellation、logging"),
        ]),
        "2025-03-26": ("上雲：Streamable HTTP＋OAuth", [
            ("新增", "OAuth 2.1 授權框架（PR #133）"),
            ("改變", "Streamable HTTP 取代 HTTP+SSE：單一端點、握手後發 Mcp-Session-Id（PR #206）"),
            ("新增", "JSON-RPC batching（PR #228）"),
            ("新增", "tool annotations：唯讀、破壞性…（PR #185）"),
        ]),
        "2025-06-18": ("收斂與加固", [
            ("移除", "JSON-RPC batching——上一版才加（PR #416）"),
            ("新增", "structured tool output（PR #371）、resource links（PR #603）、title 欄位（PR #663）"),
            ("新增", "elicitation：伺服器可以向使用者要資料（PR #382）"),
            ("改變", "MCP 伺服器定位成 OAuth Resource Server、客戶端必須實作 Resource Indicators（PR #338、#734）"),
            ("改變", "HTTP 後續請求必須帶 MCP-Protocol-Version header（PR #548）"),
        ]),
        "2025-11-25": ("企業化", [
            ("新增", "實驗性 tasks：耐久請求、輪詢、延後取結果（SEP-1686）"),
            ("新增", "URL 模式 elicitation（SEP-1036）、sampling 可帶 tools（SEP-1577）、icons（SEP-973）"),
            ("新增", "OAuth Client ID Metadata Documents 成為建議的註冊方式（SEP-991）"),
            ("改變", "輸入驗證錯誤回成工具執行錯誤，讓模型自己修正（SEP-1303）；JSON Schema 2020-12 為預設（SEP-1613）"),
        ]),
        "2026-07-28": ("無狀態（現行版）", [
            ("移除", "協定層 session 與 Mcp-Session-Id（SEP-2567）"),
            ("移除", "initialize／initialized 握手：每個請求在 _meta 自帶協定版本與客戶端能力（SEP-2575）"),
            ("新增", "server/discover：伺服器必須實作、客戶端可選呼叫（SEP-2575）"),
            ("改變", "GET 端點與 resources/subscribe → 一條 subscriptions/listen 串流；移除 ping、SSE 續傳（SEP-2575）"),
            ("改變", "伺服器不再主動發 request：回 InputRequiredResult、客戶端帶 inputResponses 重打（MRTR，SEP-2322）"),
            ("改變", "tasks 移出核心、成為官方擴充 io.modelcontextprotocol/tasks（SEP-2663）"),
            ("新增", "POST 必帶 Mcp-Method／Mcp-Name header；x-mcp-header 可把工具參數鏡射成 header（SEP-2243）"),
            ("新增", "列表類結果必帶 ttlMs／cacheScope 快取提示（SEP-2549）"),
            ("棄用", "Roots、Sampling、Logging（SEP-2577）；動態註冊讓位給 CIMD（PR #2858）"),
        ]),
    }
    _title, _items = CHANGELOG[version_pick.value]
    _col = {"新增": C_MODERN, "移除": C_BAD, "改變": C_OLD, "棄用": "#8a7f6a"}
    _rows = "".join(
        f'<div style="display:flex;gap:10px;margin:6px 0;align-items:flex-start">'
        f'<span style="flex:none;font-size:11px;font-weight:800;color:#fff;background:{_col.get(t, "#5b6770")};'
        f'border-radius:6px;padding:2px 8px">{html_mod.escape(t)}</span>'
        f'<span style="font-size:14px;line-height:1.6">{html_mod.escape(d)}</span></div>' for t, d in _items)
    mo.Html(
        f'<div style="border-left:4px solid {C_MODERN};padding:6px 14px">'
        f'<div style="font-size:15px;font-weight:800;margin-bottom:4px">{version_pick.value}：{html_mod.escape(_title)}</div>'
        f"{_rows}</div>"
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    讀法：前四版是在**同一條有狀態連線**上一直加東西；2026-07-28 則是把連線本身拆掉——
    握手、session、GET 長連線、ping、伺服器主動反問，全部在同一版消失，換成「每一發請求自帶一切」。
    下一節直接看線路上長什麼樣。

    ## 2️⃣ 封包檢視器：線路上的真相

    選一個情境，下面會畫出**循序圖**（每支箭頭都是一筆真的 HTTP 交換），再用拉桿逐封包打開看
    header 與 body。先比 ① 和 ②，再比 ④ 和 ⑤。
    """
    )
    return


@app.cell
def _(mo):
    SCENARIOS = {
        "① 呼叫工具・新協定 2026-07-28（FastMCP Client）": ("eras", "2026-07-28"),
        "② 呼叫工具・舊協定 2025-11-25（FastMCP Client legacy）": ("eras", "2025-11-25"),
        "③ 呼叫工具・第一版 2024-11-05（HTTP+SSE）": ("eras", "2024-11-05"),
        "④ 伺服器反問使用者・新協定（多回合 MRTR）": ("scenarios", "elicit_modern"),
        "⑤ 伺服器反問使用者・舊協定（伺服器反向發 request）": ("scenarios", "elicit_legacy"),
        "⑥ 背景任務・新協定（tasks 擴充）": ("scenarios", "task_modern"),
        "⑦ 路由 header＋回應快取・新協定": ("scenarios", "route_cache"),
    }
    scenario_pick = mo.ui.dropdown(options=list(SCENARIOS), value=next(iter(SCENARIOS)), label="情境")
    scenario_pick
    return SCENARIOS, scenario_pick


@app.cell
def _(SCENARIOS, WIRE, scenario_pick):
    _grp, _key = SCENARIOS[scenario_pick.value]
    scen_wire = WIRE[_grp][_key]["wire"]
    scen_result = WIRE[_grp][_key]["result"]
    return scen_result, scen_wire


@app.cell
def _(scen_wire, scenario_pick, seq_fig):
    _short = {"①": "call add - modern 2026-07-28", "②": "call add - legacy 2025-11-25",
              "③": "call add - HTTP+SSE 2024-11-05", "④": "ask the user - modern (MRTR)",
              "⑤": "ask the user - legacy (server-initiated)", "⑥": "background task - modern",
              "⑦": "routing header + cache - modern"}[scenario_pick.value[0]]
    seq_fig(scen_wire, _short)
    return


@app.cell
def _(mo, scen_result, scen_wire, wire_stats):
    _s = wire_stats(scen_wire)
    _rows = "\n".join(f"    | {k} | **{v:,}** |" for k, v in _s.items())
    mo.md(
        f"""
    | 這個情境的帳 | 實測 |
    | --- | --- |
{_rows}
    | 最後拿到的結果 | `{scen_result}` |
    """
    )
    return


@app.cell
def _(mo, scen_wire):
    packet = mo.ui.slider(start=1, stop=len(scen_wire), step=1, value=1, label="逐封包看：第幾發", show_value=True,
                          full_width=True)
    packet
    return (packet,)


@app.cell
def _(mo, packet, packet_html, scen_wire):
    mo.Html(packet_html(scen_wire[packet.value - 1], packet.value, len(scen_wire)))
    return


@app.cell
def _(WIRE, mo, rpc_label):
    # 封包序號從側錄算出來（重錄後順序若有變，文字跟著變）
    _el = WIRE["scenarios"]["elicit_legacy"]["wire"]
    _em = WIRE["scenarios"]["elicit_modern"]["wire"]
    _el_call = next(i for i, e in enumerate(_el, 1) if rpc_label(e).startswith("tools/call"))
    _el_reply = next(i for i, e in enumerate(_el, 1) if rpc_label(e).startswith("(reply"))
    _em_retry = [i for i, e in enumerate(_em, 1) if rpc_label(e).startswith("tools/call")][-1]
    _b = {k: sum(e["rbn"] + e["sbn"] for e in WIRE["eras"][k]["wire"]) for k in ("2026-07-28", "2025-11-25")}
    mo.md(
        f"""
    幾個一定要自己看到的細節：

    - ① 的每一發 body 都有 `_meta`（協定版本、客戶端能力、clientInfo），header 有 `mcp-method`；② 則是第一發換到 session id、之後每發都帶著它。
    - ① 的 body 總共 **{_b["2026-07-28"]:,} bytes，比 ② 的 {_b["2025-11-25"]:,} bytes 還多**——無狀態的代價是每一發都自帶身分證。它換到的是下一節的東西：任何一台伺服器都接得住。
    - ⑤ 的第 {_el_call} 發：`tools/call` 的回應串流裡夾著一個**伺服器發給客戶端**的 `elicitation/create`，第 {_el_reply} 發是客戶端回覆那個 request——這段時間工具一直停在半路。④ 則是兩次完全獨立的 `tools/call`，第 {_em_retry} 發帶著 `inputResponses`。
    - ⑥ 的 `tools/call` 立刻回一個 `taskId`，之後是一串 `tasks/get` 輪詢（輪幾次看當下速度）。
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 3️⃣ 為什麼要無狀態：站在負載平衡器的位置

    伺服器一多，前面就會有負載平衡器（gateway）把請求分給各副本。我們真的起了**兩台副本＋一個輪流分派的
    負載平衡器**，讓新舊客戶端各做一次「列工具＋呼叫 add」：
    """
    )
    return


@app.cell
def _(C_BAD, C_LEGACY, C_MODERN, C_OK, WIRE, html_mod, mo):
    def _trail_html(key):
        r = WIRE["replicas"][key]
        chips = "".join(
            f'<span style="display:inline-block;margin:2px 3px;padding:2px 8px;border-radius:7px;font-family:monospace;'
            f'font-size:12px;border:1.5px solid {C_OK if t["st"] < 300 else C_BAD};'
            f'color:{C_OK if t["st"] < 300 else C_BAD}">{t["replica"]}：{html_mod.escape(t["method"])} → {t["st"]}</span>'
            for t in r["trail"])
        verdict = (f'<b style="color:{C_OK}">成功：add(2,3) = {r["result"]}</b>' if r["ok"]
                   else f'<b style="color:{C_BAD}">失敗：{html_mod.escape(r["error"])}</b>')
        return chips, verdict

    _rows = ""
    for _key, _label, _c in (("round-robin|modern", "輪流分派 × 新協定", C_MODERN),
                             ("round-robin|legacy", "輪流分派 × 舊協定", C_LEGACY),
                             ("sticky|legacy", "黏著分派 × 舊協定", C_LEGACY)):
        _chips, _verdict = _trail_html(_key)
        _rows += (f'<div style="border-left:4px solid {_c};padding:6px 12px;margin:8px 0">'
                  f'<div style="font-weight:800;font-size:14px">{_label}</div><div>{_chips}</div>'
                  f'<div style="font-size:13.5px;margin-top:3px">{_verdict}</div></div>')
    _body = WIRE["replicas"]["round-robin|legacy"]["http404_body"]
    mo.Html(
        f"{_rows}<div style='font-size:13px;color:#5b6770'>A、B 是兩台副本。舊協定走錯副本時，那台回的原文："
        f"<code>{html_mod.escape(_body)}</code></div>"
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    舊協定的 session 活在**發它的那一台**的記憶體裡；請求被分到另一台，那台根本不認得這把 id。
    傳統解法是「黏著分派」（sticky：看 session id 把同一個客戶端釘在同一台），上面第三列證明它有效——
    代價是負載平衡器要記住對應表、那台副本一重啟或縮容，上面的 session 全滅。

    把上面這條規則（實測：走錯副本就 404）放大到很多客戶端同時連線，拉拉看：
    """
    )
    return


@app.cell
def _(mo):
    n_replicas = mo.ui.slider(start=1, stop=6, step=1, value=3, label="副本數", show_value=True)
    lb_policy = mo.ui.dropdown(options=["輪流分派（round-robin）", "隨機分派（random）", "黏著分派（sticky）"],
                               value="輪流分派（round-robin）", label="負載平衡策略")
    mo.hstack([n_replicas, lb_policy], wrap=True, justify="start", gap=2)
    return lb_policy, n_replicas


@app.cell
def _(np):
    def simulate(n_rep, policy, seq_len, n_sess=4000, seed=7):
        """模擬很多客戶端同時連線：每個 session 發 seq_len 發請求，彼此交錯，負載平衡器依策略分派。
        舊協定規則（實測）：握手之後的每一發都必須落在發 session 的那一台，否則 404 Session not found。
        回傳「整段操作全部成功」的 session 比例。"""
        rng = np.random.default_rng(seed)
        times = rng.uniform(0, 1, (n_sess, 1)) + np.cumsum(rng.uniform(0.001, 0.01, (n_sess, seq_len)), axis=1)
        flat = np.argsort(times, axis=None)
        rep = np.empty(n_sess * seq_len, dtype=int)
        if policy.startswith("輪流"):
            rep[flat] = np.arange(flat.size) % n_rep
        else:
            rep[:] = rng.integers(0, n_rep, flat.size)
        rep = rep.reshape(n_sess, seq_len)
        if policy.startswith("黏著"):
            return 1.0
        return float((rep == rep[:, :1]).all(axis=1).mean())
    return (simulate,)


@app.cell
def _(C_INK, C_LEGACY, C_MODERN, WIRE, lb_policy, n_replicas, np, plt, simulate):
    _leg_len = len(WIRE["eras"]["2025-11-25"]["wire"])  # 舊協定一次「列工具＋呼叫」＝ 6 發（實測）
    _ns = np.arange(1, 7)
    _leg = [100 * simulate(n, lb_policy.value, _leg_len) for n in _ns]
    _mod = [100.0 for _ in _ns]  # 新協定：每一發自帶一切，任何一台都能答（實測：3 發落在 A、B、A 全部 200）
    _fig, _ax = plt.subplots(figsize=(6.4, 3.6))
    _w = 0.38
    _ax.bar(_ns - _w / 2, _leg, _w, color=C_LEGACY, edgecolor=C_INK, lw=0.8, label="legacy 2025-11-25 (session)", zorder=3)
    _ax.bar(_ns + _w / 2, _mod, _w, color=C_MODERN, edgecolor=C_INK, lw=0.8, label="modern 2026-07-28 (stateless)", zorder=3)
    for _x, _v in zip(_ns, _leg):
        _ax.text(_x - _w / 2, _v + 2, f"{_v:.0f}%" if _v >= 1 else f"{_v:.1f}%", ha="center", fontsize=8, color=C_LEGACY,
                 fontweight="bold")
    _k = n_replicas.value
    _ax.axvspan(_k - 0.5, _k + 0.5, color="#f4e3b5", alpha=0.6, zorder=1)
    _ax.set_xticks(_ns, [f"{n}" for n in _ns])
    _ax.set_xlabel("number of replicas behind the load balancer")
    _ax.set_ylabel("sessions fully successful (%)")
    _pol = {"輪": "round-robin", "隨": "random", "黏": "sticky"}[lb_policy.value[0]]
    _ax.set_title(f"policy: {_pol}  (simulated, rule measured on 2 real replicas)", fontsize=9.5, fontweight="bold")
    _ax.set_ylim(0, 132)
    _ax.set_yticks([0, 20, 40, 60, 80, 100])
    _ax.legend(fontsize=8, loc="upper center", ncol=2, frameon=False)
    _ax.grid(axis="y", alpha=0.3, zorder=0)
    _fig.tight_layout()
    _fig
    return


@app.cell
def _(WIRE, lb_policy, mo, n_replicas, simulate):
    _leg_len = len(WIRE["eras"]["2025-11-25"]["wire"])
    _v = 100 * simulate(n_replicas.value, lb_policy.value, _leg_len)
    mo.md(
        f"""
    **{n_replicas.value} 台副本、{lb_policy.value}**：舊協定整段成功的 session 約 **{_v:.1f}%**
    （{_leg_len} 發請求都要落在同一台）；新協定 **100%**。模擬的是分派規則，規則本身是上面兩台真副本量出來的。
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    無狀態還順便解了 gateway 的另一個麻煩：**它不拆 body 也知道這一發在幹嘛**。下表是 gateway
    在兩種協定下「光看 header」能拿到的東西（取自 ① ② ⑦ 的側錄）：
    """
    )
    return


@app.cell
def _(WIRE, html_mod, mo, rpc_label):
    def _hdrs(e):
        keep = {k: v for k, v in e["rh"].items() if k.startswith("mcp")}
        return "<br>".join(f"<code>{html_mod.escape(k)}: {html_mod.escape(v[:40])}</code>" for k, v in keep.items()) or "（沒有任何 MCP header）"

    _leg = WIRE["eras"]["2025-11-25"]["wire"]
    _mod = WIRE["eras"]["2026-07-28"]["wire"]
    _rc = WIRE["scenarios"]["route_cache"]["wire"]
    _pick = [("舊・initialize", _leg[0]), ("舊・tools/call", next(e for e in _leg if rpc_label(e).startswith("tools/call"))),
             ("新・tools/call", next(e for e in _mod if rpc_label(e).startswith("tools/call"))),
             ("新・tools/call＋x-mcp-header", next(e for e in _rc if rpc_label(e).startswith("tools/call")))]
    _rows = "".join(f"<tr><td style='padding:6px 10px;font-weight:700;white-space:nowrap;vertical-align:top'>{html_mod.escape(n)}</td>"
                    f"<td style='padding:6px 10px;font-size:12px;word-break:break-all'>{_hdrs(e)}</td></tr>" for n, e in _pick)
    mo.Html(f"<div style='overflow-x:auto'><table style='border-collapse:collapse;font-size:13px'>"
            f"<tr><th style='text-align:left;padding:6px 10px'>請求</th><th style='text-align:left;padding:6px 10px'>"
            f"gateway 光看 header 看得到</th></tr>{_rows}</table></div>")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    舊協定的 `tools/call` 只帶一把 session id——想依工具或租戶分流，gateway 得自己解析 JSON-RPC body。
    新協定把 method、工具名（還有你用 `x-mcp-header` 指定的參數，例如租戶 `acme`）都鏡射到 header；
    伺服器則**強制檢查 header 與 body 一致**，免得 gateway 看 header、伺服器看 body，兩邊各說各話。
    那個檢查，下一節你會親手撞到。

    ## 4️⃣ 手刻一發請求：不用 SDK 呼叫工具

    新協定沒有握手，理論上**一發 HTTP POST 就能呼叫工具**。body 固定是
    `tools/call add {a: 2, b: 3}`，你只能轉四個旋鈕——伺服器的回應是我們把 4×3×3×5＝180 種組合
    **全部真的打過一次**錄下來的：
    """
    )
    return


@app.cell
def _(mo):
    k_pv = mo.ui.dropdown(options={"（不帶）": "none", "2026-07-28": "2026", "2025-11-25": "2025", "2099-01-01": "2099"},
                          value="（不帶）", label="header MCP-Protocol-Version")
    k_mm = mo.ui.dropdown(options={"（不帶）": "none", "tools/call": "ok", "tools/list（跟 body 不符）": "bad"},
                          value="（不帶）", label="header Mcp-Method")
    k_mn = mo.ui.dropdown(options={"（不帶）": "none", "add": "ok", "sub（跟 body 不符）": "bad"},
                          value="（不帶）", label="header Mcp-Name")
    k_meta = mo.ui.dropdown(options={"（不帶）": "none", "2026-07-28＋clientCapabilities": "2026",
                                     "2025-11-25＋clientCapabilities": "2025", "2099-01-01＋clientCapabilities": "2099",
                                     "只有 protocolVersion（缺 clientCapabilities）": "nocaps"},
                            value="（不帶）", label="body params._meta")
    mo.vstack([mo.hstack([k_pv, k_mm], wrap=True, justify="start", gap=2),
               mo.hstack([k_mn, k_meta], wrap=True, justify="start", gap=2)])
    return k_meta, k_mm, k_mn, k_pv


@app.cell
def _(C_BAD, C_INK, C_OK, WIRE, html_mod, json, k_meta, k_mm, k_mn, k_pv, mo):
    _g = WIRE["grid"]
    _status, _text = _g["responses"][_g["map"][f"{k_pv.value}|{k_mm.value}|{k_mn.value}|{k_meta.value}"]]
    _ver = {"2026": "2026-07-28", "2025": "2025-11-25", "2099": "2099-01-01"}
    _h = ["POST /mcp HTTP/1.1", "Accept: application/json, text/event-stream", "Content-Type: application/json"]
    if k_pv.value != "none":
        _h.append(f"MCP-Protocol-Version: {_ver[k_pv.value]}")
    if k_mm.value != "none":
        _h.append(f"Mcp-Method: {'tools/call' if k_mm.value == 'ok' else 'tools/list'}")
    if k_mn.value != "none":
        _h.append(f"Mcp-Name: {'add' if k_mn.value == 'ok' else 'sub'}")
    _params = {"name": "add", "arguments": {"a": 2, "b": 3}}
    if k_meta.value == "nocaps":
        _params["_meta"] = {"io.modelcontextprotocol/protocolVersion": "2026-07-28"}
    elif k_meta.value != "none":
        _params["_meta"] = {"io.modelcontextprotocol/protocolVersion": _ver[k_meta.value],
                            "io.modelcontextprotocol/clientCapabilities": {}}
    _req = "\n".join(_h) + "\n\n" + json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": _params},
                                               indent=2, ensure_ascii=False)
    try:
        _j = json.loads(_text)
        _resp = json.dumps(_j, indent=2, ensure_ascii=False)
        _err = _j.get("error") or {}
    except ValueError:
        _resp, _err = _text, {}
    _msg = _err.get("message", "")
    # 檢查順序：從 180 個組合的實測結果回推（FastMCP 4.0.8＋mcp 2.2.0），不是規格硬性規定的順序
    STEPS = [
        ("版本 header 決定走哪個年代", "沒帶、或帶握手年代的版本 → 伺服器當你是舊客戶端 → 沒握手就沒有 session", "Missing session ID"),
        ("_meta 信封要完整", "protocolVersion 與 clientCapabilities 兩把鑰匙都要有", "params._meta"),
        ("header 版本＝信封版本", "MCP-Protocol-Version 必須等於 _meta 裡的版本", "mcp-protocol-version header"),
        ("Mcp-Method 要有、要跟 body 一致", "gateway 看 header、伺服器看 body，不一致一律拒絕", "mcp-method header"),
        ("Mcp-Name 要有、要跟工具名一致", "tools/call 必帶；缺了或對不上都是 -32020", "mcp-name header"),
        ("伺服器支援這個版本", "不支援就回 -32022，並附上它支援的版本清單", "Unsupported protocol version"),
    ]
    _stop = next((i for i, s in enumerate(STEPS) if s[2] in _msg), None) if _status != 200 else len(STEPS)
    _ladder = ""
    for _i, (_t, _d, _k) in enumerate(STEPS):
        if _stop is not None and _i < _stop:
            _mark, _c = "✓", C_OK
        elif _i == _stop:
            _mark, _c = "✗ 卡在這", C_BAD
        else:
            _mark, _c = "…", "#9aa3a8"
        _ladder += (f'<div style="display:flex;gap:10px;margin:4px 0;color:{_c if _i == _stop else C_INK}">'
                    f'<span style="flex:none;width:5.5em;font-weight:800;color:{_c}">{_mark}</span>'
                    f'<span><b>{_i + 1}. {html_mod.escape(_t)}</b>　<span style="color:#5b6770">{html_mod.escape(_d)}</span></span></div>')
    _pre = ("font-family:monospace;font-size:12px;line-height:1.5;white-space:pre-wrap;word-break:break-all;"
            "background:#f4f1ea;border-radius:8px;padding:8px 10px;margin:6px 0")
    _verdict = (f'<b style="color:{C_OK}">200——一發就呼叫成功，沒有握手、沒有 session。</b>' if _status == 200
                else f'<b style="color:{C_BAD}">{_status}　code {_err.get("code")}</b>')
    mo.Html(
        f'<div style="font-size:12px;font-weight:800;color:#5b6770">你送出的請求</div><div style="{_pre}">{html_mod.escape(_req)}</div>'
        f'<div style="font-size:12px;font-weight:800;color:#5b6770;margin-top:8px">伺服器的回應（實測原文）　{_verdict}</div>'
        f'<div style="{_pre}">{html_mod.escape(_resp)}</div>'
        f'<div style="font-size:12px;font-weight:800;color:#5b6770;margin-top:8px">伺服器的檢查順序（從 180 組實測回推）</div>{_ladder}'
    )
    return


@app.cell(hide_code=True)
def _(WIRE, mo):
    _gd = WIRE["grid"]["get_delete"]
    mo.md(
        f"""
    180 種組合裡只有 **1 種**回 200。另外兩個小實驗：對同一個端點送 `GET` 或 `DELETE`（舊協定拿來開長連線、結束 session 的動詞），
    帶著新協定 header 的話伺服器回 **{_gd["GET"][0]}**（`Allow: {_gd["GET"][1]}`）——新協定的端點只收 POST。

    ## 5️⃣ FastMCP 4 功能地圖：我遇到這個問題 → 用哪個功能

    協定變成無狀態，**應用照樣可以有狀態**——這是 FastMCP 4 的主軸（官方文件的說法是
    stateless transport without stateless application code）。挑一個你會遇到的問題，看它對應的功能、
    最小程式，以及我們在 4.0.8 上**實測到的證據**：
    """
    )
    return


@app.cell
def _(WIRE):
    _f = WIRE["features"]
    _sc = WIRE["scenarios"]
    _ee = WIRE["era_errors"]
    _add_schema = next(e for e in WIRE["eras"]["2026-07-28"]["wire"] if e["rh"].get("mcp-method") == "tools/list")["sb"]
    _task_polls = sum(1 for e in _sc["task_modern"]["wire"] if e["rh"].get("mcp-method") == "tasks/get")
    _rc_lists = sum(1 for e in _sc["route_cache"]["wire"] if e["rh"].get("mcp-method") == "tools/list")
    _rc_hdr = next(e for e in _sc["route_cache"]["wire"] if e["rh"].get("mcp-method") == "tools/call")["rh"]
    FEATURES = [
        {"cat": "🔧 蓋", "q": "我想把幾個 Python 函式給 AI 用", "feat": "@mcp.tool",
         "code": 'mcp = FastMCP("calc")\n\n@mcp.tool\ndef add(a: int, b: int) -> int:\n    """Add two integers."""\n    return a + b',
         "ev": "型別提示＋docstring 自動變成說明書。側錄到的 tools/list 回應（節錄）：\n" + _add_schema[:420],
         "spec": "tools 從 2024-11-05 第一版就有；structured output（outputSchema）是 2025-06-18 加的",
         "deep": ("/fastmcp4/", "FastMCP 4：把函式變成 AI 工具")},
        {"cat": "🔧 蓋", "q": "我想提供資料給 AI 讀，由應用決定要不要餵", "feat": "@mcp.resource（URI 模板）",
         "code": '@mcp.resource("docs://{name}")\ndef read_doc(name: str) -> str:\n    """Read one document."""\n    return DOCS[name]',
         "ev": f"讀 docs://intro → {_f['resources']['ok']!r}\n路徑穿越會在進 handler 前被擋（4.0 預設）：\n"
               + "\n".join(f"  {k} → {v}" for k, v in _f["resources"]["traversal"].items()),
         "spec": "resources 從第一版就有；模板參數的路徑安全是 FastMCP 4.0 的預設行為",
         "deep": ("/fastmcp4-features/", "FastMCP 4 專屬功能")},
        {"cat": "🔧 蓋", "q": "使用者填 prompt 參數時，想要自動完成", "feat": "@mcp.completion",
         "code": '@mcp.completion\ndef complete(ref, argument, context):\n    if argument.name == "theme":\n        return [o for o in OPTIONS if o.startswith(argument.value)]',
         "ev": f"打「{_f['completion']['typed']}」→ 建議 {_f['completion']['values']}",
         "spec": "completions 能力 2025-03-26 起明確宣告；FastMCP 4.0 讓伺服器端能回答",
         "deep": ("/fastmcp4-features/", "FastMCP 4 專屬功能")},
        {"cat": "🔧 蓋", "q": "工具跑的時候想回報進度", "feat": "ctx.report_progress",
         "code": "@mcp.tool\nasync def forecast(city: str, ctx: Context) -> str:\n    await ctx.report_progress(1, 2, \"fetching\")\n    ...\n    await ctx.report_progress(2, 2, \"done\")",
         "ev": f"客戶端 progress_handler 收到：{_sc['route_cache']['progress']}\n（新協定：進度走在這個請求自己的回應串流上）",
         "spec": "progress 第一版就有；2026-07-28 規定只能走在所屬請求的回應串流",
         "deep": ("/fastmcp4-features/", "FastMCP 4 專屬功能")},
        {"cat": "🔧 蓋", "q": "工具要回傳一個互動 UI，不只是文字", "feat": "FastMCP Apps（io.modelcontextprotocol/ui 擴充）",
         "code": "# 參考 gofastmcp.com/apps：工具回傳的 UI 由支援的主機渲染在對話裡\n# 伺服器宣告在 capabilities.extensions",
         "ev": f"我們那台最小 calc 伺服器的 server/discover 回應裡就看得到：extensions = {_f['apps']['extensions']}",
         "spec": "extensions 欄位是 2026-07-28 加進 capabilities 的",
         "deep": None},
        {"cat": "🔗 接", "q": "我已經有一套 FastAPI 服務", "feat": "FastMCP.from_fastapi(app)",
         "code": "from fastapi import FastAPI\napp = FastAPI()\n...  # 原本的路由\n\nmcp = FastMCP.from_fastapi(app=app)",
         "ev": "三個路由 → 三個工具（名稱取自 operation_id，參數取自簽名）：\n"
               + "\n".join(f"  {n}({', '.join(p)})" for n, p in _f["from_fastapi"]["tools"])
               + f"\n呼叫 list_items(max_price=60) → {_f['from_fastapi']['call']}",
         "spec": "框架功能（與協定版本無關）", "deep": None},
        {"cat": "🔗 接", "q": "我手上有別家 REST API 的 OpenAPI 規格", "feat": "FastMCP.from_openapi(spec, client)",
         "code": 'api = httpx2.AsyncClient(base_url="https://api.example.com")\nspec = httpx2.get("https://api.example.com/openapi.json").json()\nmcp = FastMCP.from_openapi(openapi_spec=spec, client=api)',
         "ev": f"同一份規格 → 工具 {_f['from_openapi']['tools']}\n呼叫 create_order(item_id=2, qty=3) → {_f['from_openapi']['call']}",
         "spec": "框架功能；FastMCP 4 的 HTTP 客戶端是 SDK v2 帶的 httpx2", "deep": None},
        {"cat": "🔗 接", "q": "好幾台 MCP server，想合成一台給 AI", "feat": "hub.mount(sub, namespace=...)",
         "code": 'hub = FastMCP("hub")\nhub.mount(weather, namespace="weather")\nhub.mount(calc, namespace="calc")',
         "ev": f"合成後的工具清單：{_f['mount']['tools']}\n呼叫 weather_forecast → {_f['mount']['call']!r}",
         "spec": "框架功能", "deep": ("/mcp-servers/", "常見 MCP 服務：接上別人的伺服器，再合成一台")},
        {"cat": "🔗 接", "q": "把別人的 MCP server 轉手出去（換傳輸、加認證、接進 hub）", "feat": "create_proxy(...)",
         "code": 'from fastmcp.server import create_proxy\nfront = create_proxy("http://backend:8000/mcp", name="front")\n# 老伺服器（握手年代）：create_proxy(cfg, mode="legacy")',
         "ev": f"透過 proxy 呼叫 add(1,2) → {_f['proxy']['call']}\n後端實際收到的請求：{_f['proxy']['backend_saw']}",
         "spec": "框架功能；4.0 的 proxy 會鏡像前端的協定年代",
         "deep": ("/mcp-servers/", "常見 MCP 服務")},
        {"cat": "🔗 接", "q": "我的 agent 要同時接很多台 server（客戶端這邊）", "feat": "ClientGroup（4.0.0b5 新增）",
         "code": 'from fastmcp import ClientGroup\ngroup = ClientGroup({"calc": Client(url1), "weather": Client(url2)})\nasync with group:\n    tools = await group.list_tools()',
         "ev": f"工具自動加上伺服器前綴：{_f['client_group']['tools']}\n呼叫 calc_add(20, 22) → {_f['client_group']['call']}",
         "spec": "框架功能；每台各自協商協定年代（新舊可以混在同一組）", "deep": None},
        {"cat": "🛡️ 管", "q": "每次呼叫都要記 log、計時、限流", "feat": "Middleware",
         "code": "class Timing(Middleware):\n    async def on_call_tool(self, context, call_next):\n        t0 = time.perf_counter()\n        result = await call_next(context)\n        log(context.message.name, time.perf_counter() - t0)\n        return result\n\nmcp.add_middleware(Timing())",
         "ev": f"呼叫兩次 add，中介層記下：{_f['middleware']['log']}（毫秒數每次不同）",
         "spec": "框架功能；4.0 起每一則進站訊息都會跑中介層", "deep": None},
        {"cat": "🛡️ 管", "q": "只有管理員能用某些工具", "feat": "auth＋require_scopes",
         "code": 'mcp = FastMCP("shop", auth=verifier)\n\n@mcp.tool(auth=require_scopes("admin"))\ndef change_price(item: str, price: int) -> str: ...',
         "ev": f"guest 看得到：{_f['auth']['guest-token']}\nadmin 看得到：{_f['auth']['admin-token']}\n不帶 token：HTTP {_f['auth']['no_token'][0]}，WWW-Authenticate: {_f['auth']['no_token'][1]}",
         "spec": "OAuth 2.1 從 2025-03-26 進規格；2026-07-28 棄用動態註冊、改推 CIMD",
         "deep": ("/fastmcp4-auth/", "FastMCP 4 認證：從一把 token 到完整 OAuth 2.1")},
        {"cat": "🛡️ 管", "q": "工具有幾十個，模型挑不準、說明書塞爆上下文", "feat": "BM25SearchTransform",
         "code": "from fastmcp.server.transforms.search import BM25SearchTransform\nmcp = FastMCP(\"big\", transforms=[BM25SearchTransform()])",
         "ev": f"{_f['search']['catalog']} 個工具的目錄，模型 list_tools 只看到：{_f['search']['listed']}\n"
               f"search_tools(\"weather in Taipei\") 前三名：" + "; ".join(f"{n}（{d}）" for n, d in _f["search"]["top"]),
         "spec": "框架功能（transform）", "deep": ("/fastmcp4-features/", "FastMCP 4 專屬功能")},
        {"cat": "🛡️ 管", "q": "gateway 要依租戶把請求分到不同叢集", "feat": "x-mcp-header（參數鏡射成 header）",
         "code": 'Tenant = Annotated[str, Field(json_schema_extra={"x-mcp-header": "Tenant"})]\n\n@mcp.tool\nasync def forecast(tenant: Tenant, city: str) -> str: ...',
         "ev": "側錄到的 tools/call header：\n" + "\n".join(f"  {k}: {v}" for k, v in _rc_hdr.items() if k.startswith("mcp")),
         "spec": "2026-07-28（SEP-2243）", "deep": ("/fastmcp4-features/", "FastMCP 4 專屬功能")},
        {"cat": "🛡️ 管", "q": "客戶端一直重複 list_tools", "feat": "cache_ttl＋Client(cache=True)",
         "code": 'mcp = FastMCP("weather", cache_ttl=300, cache_scope="public")\nclient = Client(url, cache=True)',
         "ev": f"客戶端呼叫 list_tools {_sc['route_cache']['list_tools_calls']} 次 → 線路上只有 {_rc_lists} 發 tools/list（回應帶 ttlMs=300000）",
         "spec": "2026-07-28（SEP-2549：列表類結果必帶 ttlMs／cacheScope）", "deep": ("/fastmcp4-features/", "FastMCP 4 專屬功能")},
        {"cat": "🧠 撐", "q": "工具執行到一半要使用者確認", "feat": "回傳 InputRequiredResult（新）／ctx.elicit（僅舊協定）",
         "code": "@mcp.tool\nasync def delete_file(path: str, ctx: Context):\n    if ctx.input_responses is None:          # 第一回合：還沒有答案\n        return InputRequiredResult(result_type=\"input_required\",\n            input_requests={\"confirm\": ElicitRequest(...)})\n    ok = ctx.input_responses[\"confirm\"].content[\"ok\"]   # 第二回合\n    ...",
         "ev": f"新協定：兩次獨立的 tools/call（見 2️⃣ 情境 ④）→ {_sc['elicit_modern']['result']!r}\n"
               f"新協定連線上呼叫 ctx.elicit() 的實測下場：{_ee['confirm|auto']}",
         "spec": "elicitation 2025-06-18 加入；2026-07-28 改成多回合（MRTR，SEP-2322）",
         "deep": ("/fastmcp4-state/", "FastMCP 4 狀態：無狀態協定上的三種記憶")},
        {"cat": "🧠 撐", "q": "工具要跑好幾分鐘", "feat": "@mcp.tool(task=True)＋fastmcp-tasks",
         "code": "from fastmcp_tasks import TasksExtension\nmcp.add_extension(TasksExtension())\n\n@mcp.tool(task=True)\nasync def brew(cups: int, progress: Progress = Progress()) -> str: ...",
         "ev": f"tools/call 立刻回 taskId，接著 {_task_polls} 次 tasks/get 輪詢，{_sc['task_modern']['seconds']} 秒後 → {_sc['task_modern']['result']!r}"
               "（輪詢次數看當下）",
         "spec": "2025-11-25 實驗性進核心 → 2026-07-28 改成官方擴充 io.modelcontextprotocol/tasks（SEP-2663）",
         "deep": ("/fastmcp4-features/", "FastMCP 4 專屬功能")},
        {"cat": "🧠 撐", "q": "要記住購物車（跨呼叫、跨連線）", "feat": "SessionId／UserSession",
         "code": "mcp.add_provider(SessionProvider())\n\n@mcp.tool\nasync def add_to_cart(session_id: SessionId, item: str) -> list[str]:\n    s = await get_session(session_id)\n    ...",
         "ev": f"自動多出的工具：{_f['sessions']['tools']}\n換一條全新連線帶同一把鑰匙 → {_f['sessions']['new_connection']}\n亂猜一把 → {_f['sessions']['guess']}",
         "spec": "協定層 session 在 2026-07-28 移除（SEP-2567）→ 改由應用層發「顯式的鑰匙」",
         "deep": ("/fastmcp4-state/", "FastMCP 4 狀態")},
        {"cat": "🧠 撐", "q": "想借用戶端的 LLM 來生成（sampling）", "feat": "直接呼叫 LLM API（ctx.sample 已移除）",
         "code": "# 4.0 已拿掉 ctx.sample()／ctx.list_roots()\n# 自己的模型：伺服器直接呼叫 LLM API\n# 真的要借客戶端的模型：回傳帶 sampling 請求的 InputRequiredResult",
         "ev": f"在 4.0.8 呼叫 ctx.sample() 的實測下場：{_ee['summarize|auto']}",
         "spec": "Sampling、Roots、Logging 在 2026-07-28 棄用（SEP-2577）", "deep": None},
    ]
    return (FEATURES,)


@app.cell
def _(FEATURES, mo):
    feature_pick = mo.ui.dropdown(options=[f"{f['cat']}｜{f['q']}" for f in FEATURES],
                                  value=f"{FEATURES[0]['cat']}｜{FEATURES[0]['q']}", label="我遇到的問題", full_width=True)
    feature_pick
    return (feature_pick,)


@app.cell
def _(C_INK, C_MODERN, FEATURES, feature_pick, html_mod, mo):
    _f = next(f for f in FEATURES if f"{f['cat']}｜{f['q']}" == feature_pick.value)
    _esc = html_mod.escape
    _pre = ("font-family:monospace;font-size:12px;line-height:1.55;white-space:pre-wrap;word-break:break-all;"
            "background:#f4f1ea;border-radius:8px;padding:8px 10px;margin:6px 0")
    _deep = (f'<div style="font-size:13px;margin-top:8px">深入動手：<a href="{_f["deep"][0]}" target="_blank">{_esc(_f["deep"][1])}</a>'
             f'（LLM 應用開發系列）</div>' if _f["deep"] else "")
    mo.Html(
        f'<div style="border:2px solid {C_INK};border-radius:12px;padding:10px 14px">'
        f'<div style="font-size:12px;font-weight:800;color:#5b6770">{_esc(_f["cat"])}｜{_esc(_f["q"])}</div>'
        f'<div style="font-size:17px;font-weight:800;color:{C_MODERN};margin:4px 0 8px">→ {_esc(_f["feat"])}</div>'
        f'<div style="font-size:12px;font-weight:800;color:#5b6770">最小程式（參考，不在這裡執行）</div><div style="{_pre}">{_esc(_f["code"])}</div>'
        f'<div style="font-size:12px;font-weight:800;color:#5b6770;margin-top:6px">實測證據（FastMCP 4.0.8，2026-09-24）</div><div style="{_pre}">{_esc(_f["ev"])}</div>'
        f'<div style="font-size:13px;margin-top:6px"><b>跟規格的關係：</b>{_esc(_f["spec"])}</div>{_deep}</div>'
    )
    return


@app.cell
def _(FEATURES, mo):
    _rows = "\n".join(f"    | {f['cat']} | {f['q']} | `{f['feat']}` |" for f in FEATURES)
    mo.accordion({"📋 全部對照一覽（19 張卡）": mo.md(
        f"""
    | 類別 | 問題 | 用哪個 |
    | --- | --- | --- |
{_rows}
    """
    )})
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 6️⃣ 換你動手

    三個挑戰都用上面的選單與拉桿就做得到，題目在教學頁的「換你動手」。先自己做，再打開對照：
    """
    )
    return


@app.cell
def _(WIRE, mo, rpc_label, simulate):
    _leg_len = len(WIRE["eras"]["2025-11-25"]["wire"])
    _rr3 = 100 * simulate(3, "輪流分派（round-robin）", _leg_len)
    _rn3 = 100 * simulate(3, "隨機分派（random）", _leg_len)
    _g = WIRE["grid"]
    _msg25 = _g["responses"][_g["map"]["2025|ok|ok|2025"]][1]
    _el = WIRE["scenarios"]["elicit_legacy"]["wire"]
    _em = WIRE["scenarios"]["elicit_modern"]["wire"]
    _el_call = next(i for i, e in enumerate(_el, 1) if rpc_label(e).startswith("tools/call"))
    _el_reply = next(i for i, e in enumerate(_el, 1) if rpc_label(e).startswith("(reply"))
    _em_retry = [i for i, e in enumerate(_em, 1) if rpc_label(e).startswith("tools/call")][-1]
    mo.accordion(
        {
            "💡 LEVEL 1 參考解答": mo.md(
                rf"""
    唯一回 200 的組合：`MCP-Protocol-Version: 2026-07-28`、`Mcp-Method: tools/call`、`Mcp-Name: add`、
    `_meta` 選「2026-07-28＋clientCapabilities」。

    把版本 header 與 `_meta` 都換成 **2025-11-25**，回應變成：

    `{_msg25}`

    伺服器看到握手年代的版本，就當你是舊客戶端——舊協定的規矩是先 `initialize` 拿 session id，
    你沒握手，自然「缺 session ID」。**版本 header 是分流開關**，不是裝飾。
    """
            ),
            "💡 LEVEL 2 參考解答": mo.md(
                rf"""
    3 台副本、輪流分派：舊協定整段成功約 **{_rr3:.1f}%**（隨機分派約 {_rn3:.1f}%；理論上隨機是 (1/3)^5 ≈ 0.4%，
    因為握手後還有 5 發都得落在同一台）。換成黏著分派 → 100%。

    黏著救得了「分派」，救不了「那台不見了」：副本重啟、縮容、當機，釘在它上面的 session 全部作廢，
    客戶端得重新握手。新協定把這個問題整個拿掉——沒有 session 可以丟。要跨請求記東西，就用應用層的
    `SessionId`／`UserSession`，並把 store 放在共用的地方（例如 Redis），任何一台都讀得到。
    """
            ),
            "💡 LEVEL 3 提示": mo.md(
                rf"""
    ④（新）有 **{len(_em)}** 發 HTTP、伺服器反向發出的 request **0** 個；
    ⑤（舊）有 **{len(_el)}** 發 HTTP，其中第 {_el_call} 發的回應串流夾著 **1** 個 `elicitation/create`，第 {_el_reply} 發是客戶端的回覆。

    ⑤ 的工具在伺服器記憶體裡**停在半路**等答案，答案必須回到同一台、同一條 session——跨副本、跨重啟都不行。
    ④ 的第一次 `tools/call` 已經正常結束（`resultType: input_required`），第二次 `tools/call` 的 body 帶著
    `inputResponses`（答案本身），任何一台副本拿到都能從頭跑一次工具、讀到答案。

    怎麼驗證自己想對了：在 2️⃣ 選 ④、拉到第 {_em_retry} 發，看 body 裡的 `inputResponses`；再選 ⑤、拉到第 {_el_call} 發，
    看回應串流裡的 `"method": "elicitation/create"`——一個是「客戶端帶著答案來」，一個是「伺服器拉著客戶端問」。
    """
            ),
        }
    )
    return


if __name__ == "__main__":
    app.run()
