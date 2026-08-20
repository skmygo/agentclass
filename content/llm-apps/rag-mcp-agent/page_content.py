"""課程頁內容區（純常數）。改完跑：python3 .claude/skills/make-lesson/scripts/page-fill.py content/llm-apps/rag-mcp-agent
build.sh 不會部署這個檔；它是 index.html 內容區的正本。"""

TITLE = "壓軸：RAG 變成 AI 的工具"
DESCRIPTION = "LiteLLM × FastMCP × Qdrant 壓軸：把 RAG 檢索包成 MCP 工具，讓模型自己決定何時查手冊、查什麼、查幾段；agent 迴圈透過 MCP Client 呼叫工具，trace 畫成時間軸。"
NB = "https://molab.marimo.io/github/skmygo/agentclass/blob/main/content/llm-apps/rag-mcp-agent/rag-mcp-agent_ext.py"

STYLE = r"""
  /* 語義色：藍＝LLM／agent 迴圈、橘＝MCP 工具呼叫、綠＝Qdrant 與檢索結果、紅＝錯誤 */
  :root { --c1: #4C72B0; --c2: #DD8452; --c3: #55A868; --cut: #C44E52; }
  a.golab { text-decoration: none; display: inline-flex; align-items: center; gap: 8px; }

  /* hero：一條請求走完整條管線 */
  #ag-demo .qs { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 12px; }
  #ag-demo .qs button { font: inherit; font-size: 13px; padding: 6px 12px; border: 2px solid var(--ink); border-radius: 10px; background: var(--panel); cursor: pointer; font-weight: 700; }
  #ag-demo .qs button:hover { background: var(--chip-bg); }
  #ag-demo .pipe { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; margin-bottom: 10px; }
  #ag-demo .box { border: 2px solid var(--grid); border-radius: 10px; padding: 8px 6px; text-align: center; font-size: 12px; font-weight: 800; background: var(--panel); transition: all .2s; }
  #ag-demo .box small { display: block; font-weight: 400; color: var(--ink-soft); font-size: 11px; margin-top: 2px; }
  #ag-demo .box.lit.llm { border-color: var(--c1); background: var(--c1); color: #fff; }
  #ag-demo .box.lit.mcp { border-color: var(--c2); background: var(--c2); color: #fff; }
  #ag-demo .box.lit.qd { border-color: var(--c3); background: var(--c3); color: #fff; }
  #ag-demo .box.lit small { color: rgba(255,255,255,.85); }
  #ag-demo .trace { display: flex; flex-direction: column; gap: 6px; min-height: 150px; }
  #ag-demo .step { border-left: 4px solid var(--c2); background: var(--chip-bg); border-radius: 0 8px 8px 0; padding: 6px 10px; font-size: 13px; line-height: 1.6; animation: ag-in .25s ease; }
  #ag-demo .step.llm { border-color: var(--c1); } #ag-demo .step.qd { border-color: var(--c3); }
  #ag-demo .step.final { border: 1.5px solid var(--ink); border-left-width: 4px; background: var(--panel); }
  #ag-demo .step .k { font-size: 11px; font-weight: 800; letter-spacing: .05em; color: var(--ink-soft); }
  #ag-demo code { font-family: var(--mono); font-size: 12px; }
  @keyframes ag-in { from { opacity: 0; transform: translateY(4px); } to { opacity: 1; transform: none; } }
  @media (prefers-reduced-motion: reduce) { #ag-demo .step { animation: none; } }
  @media (max-width: 560px) { #ag-demo .pipe { grid-template-columns: repeat(2, 1fr); } }

  .kbd { font-family: var(--mono); background: var(--chip-bg); padding: 1px 6px; border-radius: 5px; font-size: 13px; }
  .recap { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin: 16px 0; }
  .recap div { border: 1.5px solid var(--ink); border-radius: 10px; padding: 10px 12px; font-size: 13px; background: var(--panel); }
  .recap b { display: block; font-size: 12px; letter-spacing: .04em; margin-bottom: 4px; }
  @media (max-width: 560px) { .recap { grid-template-columns: 1fr; } }
"""

WRAP = r'''
<section id="hero">
  <span class="eyebrow">CAPSTONE · LITELLM × FASTMCP × QDRANT</span>
  <h1>壓軸：RAG 變成 AI 的工具</h1>
  <p style="margin-top:18px">
    前五課的零件全部到齊，組成一台會<b>自己翻手冊</b>的客服。跟上一課的差別只有一個但很關鍵：
    上一課是<b>我們</b>決定每題都先檢索；這一課把檢索包成 MCP 工具，<b>模型自己決定</b>要不要查、查什麼、查幾段。
    選一個問題，看請求怎麼走完整條管線（內容是 notebook 的實測紀錄）：
  </p>

  <div class="hero-demo" id="ag-demo">
    <div class="qs" id="ag-qs"></div>
    <div class="pipe">
      <div class="box llm" data-b="llm">LLM<small>nemotron-3.5-lightning · 經 LiteLLM</small></div>
      <div class="box mcp" data-b="client">MCP Client<small>agent 迴圈</small></div>
      <div class="box mcp" data-b="server">FastMCP 伺服器<small>search_handbook()</small></div>
      <div class="box qd" data-b="qd">Qdrant<small>embedding + 最近鄰</small></div>
    </div>
    <div class="trace" id="ag-trace"><div class="step" style="border-color:var(--grid);color:var(--ink-soft)">選一個問題開始。</div></div>
  </div>

  <p class="note">
    這堂課用到第 1 課的 gateway、第 2 課的 tool calling 迴圈、第 3 課的 FastMCP、第 4 課的 Qdrant、第 5 課的 RAG——
    沒看過前面也能跑，但每一節會指回對應的課。
  </p>
</section>

<section id="s1">
  <span class="eyebrow">01 · 架構</span>
  <h2>把檢索包成工具，說明書寫給模型看</h2>
  <div class="codeblock">mcp = FastMCP("山茶屋知識庫",
    instructions="回答顧客關於山茶屋貓咪咖啡廳的任何問題之前，先用 search_handbook 查手冊。")

@mcp.tool
def search_handbook(query: str, top_k: int = 3) -> list[dict]:
    """在山茶屋店務手冊裡做語意搜尋，回傳最相關的段落（含相似度分數 0–1）。
    回答任何關於營業時間、規定、貓咪、會員、停車、活動的問題前都應先呼叫。"""
    return [{"title": h.payload["title"], "score": round(h.score, 3), "text": h.payload["text"]}
            for h in retrieve(query, top_k)]

@mcp.tool
def list_sections() -> list[str]:
    """列出手冊的所有章節標題。想知道手冊涵蓋哪些主題時呼叫。"""
    return [c["title"] for c in chunks]</div>
  <p>
    <b>docstring 就是給模型看的使用說明</b>——寫清楚「什麼情況該呼叫」，模型的決策品質差很多。
    <span class="kbd">instructions</span> 則是整台伺服器的說明，客戶端可以拿去當 system prompt 的一部分。
    知識庫本身（手冊、切段、批次 embedding、記憶體 Qdrant）是上一課的四步濃縮成一格。
  </p>
  <a class="golab" href="__NB__" target="_blank" rel="noopener">到 notebook 的 1️⃣–2️⃣ 節：知識庫、兩個工具</a>
</section>

<section id="s2">
  <span class="eyebrow">02 · 橋接與迴圈</span>
  <h2>三行把 MCP 說明書變成 OpenAI tools，迴圈照第 2 課</h2>
  <div class="codeblock">def mcp_to_openai_tools(tools):
    return [{"type": "function",
             "function": {"name": t.name, "description": t.description, "parameters": t.input_schema}}
            for t in tools]

# agent 迴圈裡唯一的改動：工具透過 MCP Client 呼叫
res = await c.call_tool(tc.function.name, json.loads(tc.function.arguments))
msgs.append({"role": "tool", "tool_call_id": tc.id, "content": json.dumps(res.data, ensure_ascii=False)})</div>
  <p>
    這座橋讓<b>任何</b> MCP 伺服器的工具都能給<b>任何</b> OpenAI 相容的模型用。兩個實務細節：
    工具出錯要把錯誤訊息當 tool 結果<b>餵回去</b>（模型會自我修正），不要讓例外炸掉迴圈；
    每一步記進 <span class="kbd">trace</span>——那是你 debug agent 唯一的眼睛，notebook 把它畫成時間軸。
  </p>
  <a class="golab" href="__NB__" target="_blank" rel="noopener">到 notebook 的 3️⃣–4️⃣ 節：橋接、ask_agent、第一個問題</a>
</section>

<section id="s3">
  <span class="eyebrow">03 · 觀察決策</span>
  <h2>它什麼時候查、查什麼、怎麼合併</h2>
  <div class="recap">
    <div><b>合併兩個章節</b>「週二中午想去順便停車」→ 一次查 <span class="kbd">query="週二 中午 停車"</span>，答案引「營業時間」＋「交通與停車」兩個來源。</div>
    <div><b>換一個工具</b>「手冊有哪些章節？」→ 不做語意搜尋，改呼叫 <span class="kbd">list_sections</span>。</div>
    <div><b>不用工具</b>「1+1 等於多少？」→ 多半零次工具呼叫直接答 2；偶爾會字面地先查一次 <span class="kbd">1+1</span> 再說手冊裡沒有。</div>
  </div>
  <p>
    這三個行為都不是我們寫的 if-else，是模型讀了說明書與 system prompt 之後的判斷。說明書是有用的：
    沒加「query 請用繁體中文」那句之前，它會用英文 <span class="kbd">"parking"</span> 去搜繁中手冊、漏掉週二公休；
    加一句就改掉了。第三個問題則示範小模型對規矩更字面，LEVEL 3 讓你調它。notebook 末尾有輸入框，換你問客服。
  </p>
  <a class="golab" href="__NB__" target="_blank" rel="noopener">到 notebook 的 5️⃣ 節：三個問題的時間軸、換你問</a>
</section>

<section id="s4">
  <span class="eyebrow">04 · 上線</span>
  <h2>同一台伺服器，交給 Claude Code 當 agent</h2>
  <div class="codeblock">if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=8000)

# 然後
claude mcp add --transport http shancha http://localhost:8000/mcp</div>
  <p style="font-size:13.5px;color:var(--ink-soft);margin-top:10px">卡住了？每一題在 notebook 末節都有折疊解答——先自己做，再打開對照。</p>
  <p>
    Claude Code 會看到 <span class="kbd">search_handbook</span> 與 <span class="kbd">list_sections</span>，問它山茶屋的事它會自己查——
    <b>不用寫任何 agent 迴圈</b>，客戶端本身就是 agent。第 3 課的無狀態協定在這裡兌現：
    每個請求自帶一切，跑 3 個副本放在負載平衡器後面，Qdrant 換成正式伺服器讓副本共用同一份索引，
    程式碼其他地方一個字不用改。
  </p>
  <a class="golab" href="__NB__" target="_blank" rel="noopener">到 notebook 的 6️⃣ 節：部署與 4.0 的兌現</a>
</section>

<section id="s5">
  <span class="eyebrow">05 · 實戰</span>
  <h2>換你動手</h2>
  <div class="ex">
    <span class="lv">LEVEL 1</span>
    <p>加第三個工具 <span class="kbd">get_section(title)</span> 回傳整段原文，問「把會員制度完整念給我聽」——模型會改用它嗎？說明書的措辭會影響它的選擇。</p>
  </div>
  <div class="ex">
    <span class="lv">LEVEL 2</span>
    <p>給 <span class="kbd">search_handbook</span> 加門檻：最高分低於 0.4 回傳「手冊裡沒有相關內容」而不是硬湊三段。問「有賣牛排嗎」驗證。</p>
  </div>
  <div class="ex">
    <span class="lv">LEVEL 3</span>
    <p>刪掉 system prompt 裡「先用工具查手冊」那句重跑——模型還會主動查嗎？比較 <span class="kbd">mcp.instructions</span>（伺服器方）與 system prompt（客戶端方）誰該負責提醒，想想在 Claude Code 那條路線上你能控制哪一個。</p>
  </div>
  <p class="note">
    六堂課到此完結：一個網址一把 key（LiteLLM）、讓模型做事（tool calling）、把函式變工具（FastMCP）、
    最像什麼（Qdrant）、先翻書再回答（RAG）——然後把它們接成一台會自己查資料的客服。
  </p>
</section>

<div class="endnav">
  <a href="/fastmcp4-auth/">
    <span class="tag">下一步 · FastMCP 4 補充系列</span>
    <b>補充 A：認證與授權——從一把 token 到完整 OAuth 2.1 →</b>
  </a>
  <a href="/litellm-basics/">
    <span class="tag">從頭複習</span>
    <b>‹ 第 1 課：LiteLLM：一個網址、一把 key，打遍八家模型</b>
  </a>
  <a href="/llm-apps/">
    <span class="tag">主題</span>
    <b>‹ 回「學 LLM 應用開發」課程列表</b>
  </a>
</div>
'''

SCRIPT = r"""
/* ═══ hero 互動：一條請求走完整條管線（純 JS；步驟與文字來自 notebook 實測 trace）═══ */
(function () {
  const RUNS = [
    { q: "我週二中午想去，順便停車，要注意什麼？", steps: [
      { b: "llm", cls: "llm", k: "STEP 1 · LLM 決定呼叫工具", t: "<code>search_handbook(query=\"週二 中午 停車\", top_k=3)</code>" },
      { b: "client", cls: "", k: "MCP CLIENT · 轉給伺服器", t: "<code>await c.call_tool(\"search_handbook\", {...})</code>" },
      { b: "server", cls: "", k: "FASTMCP · 執行工具", t: "query 先經 embedding 模型變向量，再問 Qdrant" },
      { b: "qd", cls: "qd", k: "QDRANT · 最近鄰", t: "營業時間 0.38 → 交通與停車 → …（3 段）" },
      { b: "llm", cls: "final", k: "STEP 2 · 最終回答", t: "山茶屋每週二公休，週二中午無法前往（來源：營業時間）。若改日前往，請注意店內無附設停車場，建議停在對面的饒河停車場，消費滿 500 元可折抵一小時停車費（來源：交通與停車）。" },
    ]},
    { q: "你們手冊有哪些章節？", steps: [
      { b: "llm", cls: "llm", k: "STEP 1 · LLM 改選另一個工具", t: "<code>list_sections()</code>" },
      { b: "client", cls: "", k: "MCP CLIENT → FASTMCP", t: "不做語意搜尋，直接回傳 10 個標題" },
      { b: "llm", cls: "final", k: "STEP 2 · 最終回答", t: "手冊中的章節有：營業時間、入場規定、Wi-Fi、店貓介紹：麻糬、店貓介紹：煤球、店貓介紹：奶蓋、會員制度、交通與停車、貓咪領養、特殊活動（來源：章節列表）" },
    ]},
    { q: "1+1 等於多少？", steps: [
      { b: "llm", cls: "final", k: "STEP 1 · 零次工具呼叫", t: "1+1 等於 2。（來源：手冊中未找到相關章節）　← 沒查手冊、直接回答；偶爾它會字面地先搜一次 1+1 再說沒有——LEVEL 3 挑戰就是調這裡" },
    ]},
  ];
  const qs = document.getElementById("ag-qs"), trace = document.getElementById("ag-trace");
  const boxes = document.querySelectorAll("#ag-demo .box");
  let timers = [];
  RUNS.forEach(r => { const b = document.createElement("button"); b.textContent = r.q; b.addEventListener("click", () => play(r)); qs.appendChild(b); });
  function play(r) {
    timers.forEach(clearTimeout); timers = [];
    boxes.forEach(b => b.classList.remove("lit"));
    trace.innerHTML = `<div class="step llm"><span class="k">USER</span><br>${r.q}</div>`;
    r.steps.forEach((s, i) => timers.push(setTimeout(() => {
      boxes.forEach(b => b.classList.toggle("lit", b.dataset.b === s.b));
      trace.insertAdjacentHTML("beforeend", `<div class="step ${s.cls}"><span class="k">${s.k}</span><br>${s.t}</div>`);
    }, 550 * (i + 1))));
  }
})();
"""

PANEL_STEPS = """
        <li>登入 molab（GitHub / Google）</li>
        <li>開啟課程 notebook，<b>Fork 成自己的副本</b>即可編輯</li>
        <li>從第一格往下全部執行（首次安裝套件約 1 分鐘）——<b>免費 CPU 環境即可</b>，不需要 GPU</li>
"""
