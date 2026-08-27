"""課程頁內容區（純常數）。改完跑：python3 .claude/skills/make-lesson/scripts/page-fill.py content/genai-intro/genai-agents
build.sh 不會部署這個檔；它是 index.html 內容區的正本。"""

TITLE = "AI Agent 與 MCP：模型長出手腳"
DESCRIPTION = "Agent 不是魔法：模型吐一段 JSON、你的程式執行工具、結果塞回對話——用真實互動紀錄一步步播給你看。再看懂 MCP 怎麼把 M×N 配接地獄變成 M+N，以及 Agent Skills、Multi-Agent 這些名詞在講什麼。"

STYLE = r"""
  /* 語義色：藍＝agent/loop、橘＝工具、綠＝MCP、紫＝生態系、紅＝代價 */
  :root { --c1: #4C72B0; --c2: #DD8452; --c3: #55A868; --c4: #8172B2; --cut: #C44E52; }

  .tldr { border-left: 4px solid var(--tc, var(--c1)); background: var(--chip-bg);
    border-radius: 0 10px 10px 0; padding: 10px 14px; margin: 12px 0 16px;
    font-size: 14.5px; line-height: 1.7; }
  .tldr b { color: var(--tc, var(--c1)); }

  /* hero：agent loop step-through 播放器 */
  #agent-demo .tabs { display: flex; gap: 8px; margin-bottom: 10px; }
  #agent-demo .tab { font: inherit; font-size: 13px; font-weight: 700; color: var(--ink);
    background: var(--panel); border: 2px solid var(--grid); border-radius: 999px;
    padding: 5px 14px; cursor: pointer; }
  #agent-demo .tab.on { border-color: var(--c1); background: var(--chip-bg); color: var(--c1); }
  #agent-demo .stage { border: 2px solid var(--ink); border-radius: 12px; padding: 12px 14px;
    min-height: 190px; }
  #agent-demo .bub { border: 2px solid var(--bc); border-radius: 10px; padding: 7px 11px;
    margin: 7px 0; animation: fadeup .25s ease; }
  #agent-demo .bub .who { font-size: 11px; font-weight: 800; letter-spacing: .06em; color: var(--bc); }
  #agent-demo .bub .txt { font-size: 13.5px; line-height: 1.7; white-space: pre-wrap; }
  #agent-demo .bub .txt code { font-family: var(--mono); font-size: 12.5px; }
  @keyframes fadeup { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: none; } }
  #agent-demo .ctrl { display: flex; align-items: center; gap: 10px; margin-top: 10px; }
  #agent-demo .step-btn { font: inherit; font-size: 14px; font-weight: 800; color: #fff;
    background: var(--c1); border: 2px solid var(--c1); border-radius: 10px;
    padding: 7px 18px; cursor: pointer; }
  #agent-demo .step-btn:disabled { opacity: .4; cursor: default; }
  #agent-demo .reset-btn { font: inherit; font-size: 13px; font-weight: 700; color: var(--ink);
    background: var(--panel); border: 2px solid var(--grid); border-radius: 10px;
    padding: 6px 14px; cursor: pointer; }
  #agent-demo .pos { font-family: var(--mono); font-size: 12px; color: var(--ink-soft); }
  #agent-demo .src { font-size: 12px; color: var(--ink-soft); margin-top: 8px; }

  table.cmp { width: 100%; border-collapse: collapse; font-size: 13.5px; margin: 14px 0; }
  table.cmp th, table.cmp td { border-bottom: 1px solid var(--grid); padding: 8px 10px; text-align: left; vertical-align: top; }
  table.cmp th { font-size: 12px; letter-spacing: .04em; color: var(--ink-soft); }
  table.cmp td.n { font-family: var(--mono); font-weight: 800; white-space: nowrap; }
  .kbd { font-family: var(--mono); background: var(--chip-bg); padding: 1px 6px; border-radius: 5px; font-size: 13px; }
  .src { font-size: 12.5px; color: var(--ink-soft); margin-top: -6px; }

  table.cheat { width: 100%; border-collapse: collapse; font-size: 14px; margin: 14px 0; }
  table.cheat td { border-bottom: 1px solid var(--grid); padding: 10px 12px; vertical-align: top; line-height: 1.7; }
  table.cheat td.t { font-weight: 800; white-space: nowrap; width: 11em; }
"""

WRAP = r'''
<section id="hero">
  <span class="eyebrow">GENAI BASICS · 05 · AGENT 與協定生態</span>
  <h1>AI Agent 與 MCP：<br>模型長出手腳</h1>
  <p style="margin-top:18px">
    上一課的模型只會「想」，這一課它長出手腳。但「Agent 呼叫工具」不是魔法——
    模型只是<b>吐出一段 JSON 文字</b>，動手的從頭到尾是你的程式。
    按「下一步」把一次真實互動一步步播出來（模型輸出為實測紀錄，天氣是教學用模擬資料）：
  </p>

  <div class="hero-demo" id="agent-demo">
    <div class="tabs" id="agent-tabs"></div>
    <div class="stage" id="agent-stage"></div>
    <div class="ctrl">
      <button type="button" class="step-btn" id="agent-next">下一步 ▸</button>
      <button type="button" class="reset-btn" id="agent-reset">重播</button>
      <span class="pos" id="agent-pos"></span>
    </div>
    <div class="src">實測紀錄：qwen3.5-2b、temperature=0、2026-08。</div>
  </div>

  <p class="note">
    右邊的實驗場是真的 Python（在你的瀏覽器裡跑，不用安裝任何東西）。
    首次載入約需 30–60 秒，正好夠你讀完第 1 節。每一格程式碼都能改、能重跑，
    改壞了重新整理就復原——這是你的沙盒，盡量玩。
  </p>
</section>

<section id="s1">
  <span class="eyebrow">01 · AI AGENT</span>
  <h2>Agent：會拆任務、用工具、看回饋的迴圈</h2>
  <div class="tldr" style="--tc:var(--c1)">
    <b>一句話重點</b>：AI Agent ＝ 模型（大腦）＋ 工具（手腳）＋ <b>迴圈</b>（身體）——
    能自主拆任務、呼叫工具、根據執行結果決定下一步的系統。
  </div>
  <p>
    純聊天模型只能靠訓練時背下來的知識答題；Agent 多了三件事：
    <b>決策</b>（這個問題需不需要查工具？）、<b>行動</b>（發出工具呼叫）、
    <b>回饋</b>（拿到結果後修正或收尾）。開場那個播放器就是最小的完整迴圈——
    連「什麼是光合作用」它判斷不用查工具、直接回答，也是決策的一部分。
  </p>
  <p>
    整個迴圈的骨架用虛擬碼寫出來只有五行——注意<b>模型從沒真的「執行」任何東西</b>：
  </p>
  <div class="codeblock">while True:
    reply = 呼叫模型(messages)            # 模型只會產生文字
    if 不是工具呼叫(reply): break          # 沒有 JSON → 它決定直接回答
    result = 執行工具(解析JSON(reply))     # 動手的是你的程式
    messages += [reply, result]           # 結果塞回對話，讓模型看到</div>
  <button class="golab" data-nb="1️⃣">到右邊 1️⃣ 親手跑一次這個管線</button>
</section>

<section id="s2">
  <span class="eyebrow">02 · TOOL / FUNCTION CALLING</span>
  <h2>Tool Calling：模型用嘴巴呼叫、你用程式執行</h2>
  <div class="tldr" style="--tc:var(--c2)">
    <b>一句話重點</b>：模型呼叫外部工具的機制——模型輸出結構化的呼叫請求（JSON），
    <b>執行與回填結果都是你的程式的事</b>。
  </div>
  <p>
    我們在開場用的是「手工版」：system prompt 裡寫規則、要模型只輸出一行 JSON。
    正式的 API 把這件事標準化了——你用 schema 宣告工具，模型回專門的 tool-call 欄位。
    兩大家的寫法（真實 API）：
  </p>
  <div class="codeblock"># OpenAI：tools 是 function 清單
resp = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "台北天氣如何？"}],
    tools=[{
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "查詢城市目前天氣",
            "parameters": {
                "type": "object",
                "properties": {"city": {"type": "string"}},
                "required": ["city"],
            },
        },
    }],
)
resp.choices[0].message.tool_calls   # 模型的呼叫請求在這</div>
  <div class="codeblock"># Anthropic：input_schema 直接放頂層
resp = client.messages.create(
    model="claude-opus-5",
    max_tokens=1024,
    messages=[{"role": "user", "content": "台北天氣如何？"}],
    tools=[{
        "name": "get_weather",
        "description": "查詢城市目前天氣",
        "input_schema": {
            "type": "object",
            "properties": {"city": {"type": "string"}},
            "required": ["city"],
        },
    }],
)   # 回應裡 type=="tool_use" 的區塊就是呼叫請求</div>
  <p>
    不管哪一家，水電工程都一樣：<b>解析 → 執行 → 把結果塞回 messages → 再呼叫模型</b>。
    右邊 2️⃣ 還會算給你看：因為 API 無狀態，每一輪都要重送全部歷史——
    agent 的上下文帳就是這樣滾大的。
  </p>
  <button class="golab" data-nb="2️⃣">到右邊 2️⃣ 看 agent loop 的上下文帳</button>
</section>

<section id="s3">
  <span class="eyebrow">03 · MCP</span>
  <h2>MCP：AI 工具界的 USB 接口</h2>
  <div class="tldr" style="--tc:var(--c3)">
    <b>一句話重點</b>：MCP（Model Context Protocol）是工具接入的<b>開放標準</b>——
    把「M 個應用 × N 個工具」的客製配接地獄，變成「M＋N」份標準接口。
  </div>
  <p>
    上一節的 <span class="kbd">get_weather</span> 只活在你自己的程式裡；
    想讓 Claude Desktop、IDE、別人的 agent 也能用它，難道每家都寫一次配接？
    MCP 的答案：工具包成 <b>MCP server</b>（寫一次，誰都能接），
    應用實作 <b>MCP client</b>（寫一次，什麼工具都能接）。
    右邊 3️⃣ 把 4×6＝24 條客製配接線 vs 4＋6＝10 條標準線畫給你看。
  </p>
  <p>
    用 FastMCP 把函式包成 server 只要一個修飾器——docstring 就是給模型看的說明書，
    寫得好不好直接決定模型用不用得對：
  </p>
  <div class="codeblock">from fastmcp import FastMCP

mcp = FastMCP("weather")

@mcp.tool
def get_weather(city: str) -> dict:
    """查詢城市目前天氣，回傳氣溫、天氣狀況與降雨機率。"""
    return weather_db[city]

mcp.run()</div>
  <p class="src">
    想真的動手架一個？本站的 <a href="/mcp-servers/">MCP server 實作課</a>（LLM 應用開發系列）從零寫到部署。
  </p>
  <button class="golab" data-nb="3️⃣">到右邊 3️⃣ 看 M×N 地獄怎麼被解掉</button>
</section>

<section id="s4">
  <span class="eyebrow">04 · 生態系</span>
  <h2>生態系名詞一次看：A2A、AG-UI、Skills、Multi-Agent</h2>
  <div class="tldr" style="--tc:var(--c4)">
    <b>一句話重點</b>：MCP 管「Agent 連工具」；<b>A2A</b> 管「Agent 連 Agent」、
    <b>AG-UI</b> 管「Agent 連使用者介面」——各管一段線路的協定。
  </div>
  <p>
    <b>Agent Skills</b> 是另一種打包能力的方式：把「怎麼做某件事」的知識寫成
    <span class="kbd">SKILL.md</span>（說明文件＋腳本），agent 需要時才載入全文——
    這叫<b>漸進式披露</b>，工具說明書不用一開始全塞進上下文：
  </p>
  <div class="codeblock">---
name: brand-guidelines
description: 產出行銷素材時套用公司的品牌規範（何時用：寫文案、做簡報）
---

# 品牌規範
主色 #1A73E8、標語一律「...」、禁用詞清單如下…</div>
  <p>
    模型平常只看得到 <span class="kbd">name</span> 和 <span class="kbd">description</span>
    兩行；判斷用得上，才把整份文件讀進來。
  </p>
  <p>
    <b>Multi-Agent</b> 則是讓多個 agent 分工協作（一個查資料、一個寫報告、一個審稿）。
    常見框架的長相（真實 API）：
  </p>
  <div class="codeblock"># CrewAI：用角色描述定義 agent
from crewai import Agent
researcher = Agent(
    role="研究員",
    goal="蒐集主題的最新資料",
    backstory="你是嚴謹的產業分析師",
)

# LangGraph：把 agent 流程畫成狀態圖
from langgraph.graph import StateGraph
graph = StateGraph(State)
graph.add_node("research", research_node)
graph.add_edge("research", "write")</div>
  <p>
    新手判斷準則：<b>一個 agent＋多個工具能解的，就別急著上 multi-agent</b>——
    多 agent 代表多倍的上下文成本與更難除錯的訊息流，是「需要才加」的架構。
  </p>
</section>

<section id="s5">
  <span class="eyebrow">05 · 速查</span>
  <h2>本課名詞速查卡</h2>
  <p>發講義用的濃縮版——一個名詞一句話：</p>
  <table class="cheat">
    <tr><td class="t" style="color:var(--c1)">AI Agent</td>
        <td>能自主拆任務、呼叫工具、根據執行回饋決定下一步的系統——模型是大腦，<b>迴圈是身體</b>。</td></tr>
    <tr><td class="t" style="color:var(--c2)">Tool / Function Calling</td>
        <td>模型呼叫外部工具的機制：模型輸出 JSON 呼叫請求，<b>執行與回填是你的程式</b>。</td></tr>
    <tr><td class="t" style="color:var(--c3)">MCP</td>
        <td>AI 工具界的「USB 接口」：工具包成 server、應用實作 client，<b>M×N 配接變 M+N</b>。</td></tr>
    <tr><td class="t" style="color:var(--c4)">A2A / AG-UI</td>
        <td>分別管「Agent 連 Agent」與「Agent 連 UI」的協定——跟 MCP 各管一段線路。</td></tr>
    <tr><td class="t" style="color:var(--c4)">Agent Skills</td>
        <td>用 SKILL.md 打包可重用能力，靠<b>漸進式披露</b>（先看兩行摘要、用到才載全文）省上下文。</td></tr>
    <tr><td class="t" style="color:var(--c4)">Multi-Agent</td>
        <td>多智能體分工協作（CrewAI／LangGraph／AutoGen）——威力大、成本與除錯難度也大，<b>需要才加</b>。</td></tr>
  </table>
</section>

<section id="s6">
  <span class="eyebrow">06 · 實戰</span>
  <h2>換你動手</h2>
  <div class="ex">
    <span class="lv">LEVEL 1</span>
    <p>在右邊 1️⃣ 把 <span class="kbd">CALL</span> 的城市改成「台中」，看管線查到不同資料；再改成資料庫沒有的城市——管線怎麼處理？為什麼錯誤也要回給模型？</p>
  </div>
  <div class="ex">
    <span class="lv">LEVEL 2</span>
    <p>看 2️⃣ 的上下文帳，回答：如果你的 agent loop 忘了把工具結果塞回 messages，模型第二次呼叫時會看到什麼？會發生什麼事？</p>
  </div>
  <div class="ex">
    <span class="lv">LEVEL 3</span>
    <p>設計一個計算機工具 <span class="kbd">calc(expr)</span>：寫出它的說明書（給模型看的）、呼叫 JSON 格式（在實驗區用 json.loads 驗證），並想清楚哪些問題「該」與「不該」觸發它。</p>
  </div>
  <p style="font-size:13.5px;color:var(--ink-soft);margin-top:10px">卡住了？三題在 notebook 最後一格都有折疊解答——先自己做，再打開對照。</p>
  <button class="golab" data-nb="4️⃣">到右邊 4️⃣ 的實驗區開工</button>
</section>

<section id="quiz">
  <span class="eyebrow">07 · 驗收</span>
  <h2>情境測驗</h2>
  <p>離開前試試看：下面的情境都真的會遇到。每題選一個你認為的最佳做法，選了馬上看得到解釋。</p>
  <div data-quiz>

    <div class="quiz-q" data-answer="B">
      <p class="quiz-tag">Q1 <span class="qtype">情境題</span></p>
      <h3>公司有 3 套 AI 助理（客服、內部知識庫、IDE 外掛），要接進 5 個內部系統（訂單、庫存、HR、行事曆、監控）。工程師報告：「每套助理對每個系統都要寫一次串接，共 15 份配接程式，維護不動了。」最合適的方向是？</h3>
      <div class="quiz-opts">
        <button type="button" class="quiz-opt" data-k="A">A. 挑一套最重要的助理，其他兩套下線，減少配接數量</button>
        <button type="button" class="quiz-opt" data-k="B">B. 把 5 個系統各包成 MCP server、3 套助理各實作 MCP client——配接從 3×5=15 份變 3+5=8 份，之後每加一個系統只要多寫一份 server</button>
        <button type="button" class="quiz-opt" data-k="C">C. 把 15 份配接程式集中到同一個 repo，統一 code review</button>
        <button type="button" class="quiz-opt" data-k="D">D. 訓練一個懂全部內部系統的專屬模型，就不需要工具串接了</button>
      </div>
      <div class="quiz-fb" aria-live="polite"><p>這就是 MCP 要解的 N×M 配接地獄：讓「工具端寫一次、應用端寫一次」取代「每對組合寫一次」。關鍵收益在<b>增量成本</b>——第 6 個系統上線時，MCP 架構只要多一份 server，舊架構要多寫 3 份配接。A 是砍需求不是解問題；C 只是把 15 份程式放整齊，維護量沒變；D 方向錯得深——模型「知道」系統規格也拿不到即時資料（今天的庫存、現在的訂單），存取即時／私有資料正是工具存在的理由，何況重訓模型的成本遠高於寫接口。</p></div>
    </div>

    <div class="quiz-q" data-answer="C">
      <p class="quiz-tag">Q2 <span class="qtype dx">錯誤診斷</span></p>
      <h3>同事寫的 agent loop 如下。實測時模型第一輪正確輸出了工具呼叫 JSON、工具也成功執行，但模型接下來不是又喊一次要呼叫同一個工具，就是憑空編一個天氣。bug 在哪？</h3>
      <div class="codeblock">while True:
    reply = call_model(messages)
    if not is_tool_call(reply):
        break
    result = run_tool(parse_json(reply))   # 有執行、有拿到結果
    messages.append({"role": "assistant", "content": reply})
    # 然後直接進下一輪…</div>
      <div class="quiz-opts">
        <button type="button" class="quiz-opt" data-k="A">A. while True 沒有次數上限，模型陷入無窮迴圈</button>
        <button type="button" class="quiz-opt" data-k="B">B. parse_json 沒有處理模型輸出多包文字的情況</button>
        <button type="button" class="quiz-opt" data-k="C">C. 工具結果 result 從來沒被塞回 messages——模型下一輪看到的對話停在「我要呼叫工具」，根本不知道結果，只能重呼叫或瞎編</button>
        <button type="button" class="quiz-opt" data-k="D">D. assistant 訊息不該由程式 append，API 會自己記住</button>
      </div>
      <div class="quiz-fb" aria-live="polite"><p>順著訊息流走一遍就看到了：loop 把模型的呼叫（assistant）塞回去了，卻沒把 <code>result</code> 塞回去。模型是無狀態的——它只知道 messages 裡有什麼，工具在你程式裡跑得再成功，沒寫進對話就等於沒發生，於是它只能再喊一次（重複呼叫）或硬答（幻覺）。修法：append 完 assistant 後，再 append 一則帶工具結果的訊息。A 描述的是症狀不是病因（加上限只會讓它「早點失敗」）；B 是真實世界該防的另一個坑，但題目說了第一輪解析成功；D 恰好說反——API 無狀態，正因為它不會自己記住，你才要把每一則都塞回去。</p></div>
    </div>

    <div class="quiz-q" data-answer="B">
      <p class="quiz-tag">Q3 <span class="qtype">情境題</span></p>
      <h3>你要做一個「查訂單狀態、查退貨政策、算運費」的客服 agent。同事提議：「上 Multi-Agent 架構吧——訂單 agent、政策 agent、運費 agent，再加一個總指揮 agent 分派任務。」你該怎麼判斷？</h3>
      <div class="quiz-opts">
        <button type="button" class="quiz-opt" data-k="A">A. 同意——多 agent 分工明確，一定比單一 agent 強</button>
        <button type="button" class="quiz-opt" data-k="B">B. 先做「一個 agent＋三個工具」：這三件事本質是三次工具呼叫，單一 agent 就能決策；multi-agent 的多倍上下文成本與除錯難度，等單一 agent 真的不夠用再上</button>
        <button type="button" class="quiz-opt" data-k="C">C. 都不用——把三種問題的答案寫成 FAQ 讓模型背下來就好</button>
        <button type="button" class="quiz-opt" data-k="D">D. 用 A2A 協定把三個外部 agent 接起來，不用自己寫</button>
      </div>
      <div class="quiz-fb" aria-live="polite"><p>架構選型的原則是從簡單的開始：這三個能力都是「一次工具呼叫拿結果」的形狀，一個 agent 配三個工具就能決策要用哪個——正是本課播放器示範的迴圈。Multi-agent 才有的代價：每個 agent 各自維護一份滾大的 messages（上下文成本翻倍）、agent 之間的訊息流更難追蹤除錯。它的主場是「子任務本身就需要多輪推理與各自的長上下文」（例如一個查資料、一個寫長報告）。A 是把架構當信仰；C 答不了「我的訂單到哪了」——即時資料必須查工具；D 拿協定當架構——A2A 解的是「agent 之間怎麼講話」，不解「該不該拆成多個 agent」。</p></div>
    </div>

    <div class="quiz-q" data-answer="D">
      <p class="quiz-tag">Q4 <span class="qtype dx">錯誤診斷</span></p>
      <h3>你把天氣工具包成了 MCP server，模型卻常常在該查天氣時不查、直接瞎猜。檢查程式發現工具長這樣。最該修的是什麼？</h3>
      <div class="codeblock">@mcp.tool
def gw(c: str) -> dict:
    """util v2"""
    return weather_db[c]</div>
      <div class="quiz-opts">
        <button type="button" class="quiz-opt" data-k="A">A. 回傳型別要改成 str，模型看不懂 dict</button>
        <button type="button" class="quiz-opt" data-k="B">B. MCP server 要換成 OpenAI function calling 才穩定</button>
        <button type="button" class="quiz-opt" data-k="C">C. weather_db 查詢要加上 try/except</button>
        <button type="button" class="quiz-opt" data-k="D">D. 函式名 gw、參數名 c、docstring「util v2」對模型全是謎語——工具說明書是給模型看的教材，改成 get_weather(city) 並把「做什麼、參數是什麼、何時該用」寫進 docstring</button>
      </div>
      <div class="quiz-fb" aria-live="polite"><p>模型決定「要不要用工具」的唯一依據，就是工具的名字、參數名與說明文字——它看不到你的程式碼實作。<code>gw(c)</code>＋「util v2」提供的資訊量是零，模型自然不知道這工具能查天氣，只好用背下來的知識瞎猜。命名清楚、docstring 寫明「查詢城市目前天氣，回傳氣溫、天氣狀況與降雨機率」，行為立刻改變——「改一句說明書、模型行為就變」是 agent 開發最划算的一根槓桿。A 無中生有，結構化的 dict 對模型完全可讀；B 搞錯層次，OpenAI 與 MCP 的工具一樣靠 description 決策，換協定救不了空白說明書；C 是好習慣，但解的是執行期錯誤，不是「模型不來呼叫」。</p></div>
    </div>

    <div class="quiz-score" data-score></div>
  </div>
</section>

<div class="endnav">
  <a href="/genai-devstyle/">
    <span class="tag">下一課</span>
    <b>新開發範式：Vibe Coding 到 Spec-Driven →</b>
  </a>
  <a href="/genai-intro/">
    <span class="tag">主題</span>
    <b>‹ 回「生成式 AI 導論」課程列表</b>
  </a>
</div>
'''

SCRIPT = r"""
/* ═══ hero 互動：agent loop step-through 播放器 ═══
   模型輸出＝實測紀錄（qwen3.5-2b、temp=0、2026-08）；天氣為教學用模擬資料。 */
(function () {
  const SCEN = [
    { label: "要查工具的問題", steps: [
      { who: "user", c: "#4C72B0", txt: "台北現在天氣怎麼樣？出門要帶傘嗎？" },
      { who: "assistant（模型輸出・實測）", c: "#DD8452",
        txt: '{"tool": "get_weather", "args": {"city": "台北"}}',
        note: "模型只做了這件事：吐出一段 JSON 文字" },
      { who: "你的程式（執行工具）", c: "#55A868",
        txt: 'get_weather("台北") → {"temp_c": 24, "condition": "小雨", "rain_prob": 80}',
        note: "動手的是程式，不是模型（天氣為教學用模擬資料）" },
      { who: "assistant（模型輸出・實測）", c: "#DD8452",
        txt: "根據工具回傳的結果，台北目前氣溫為 24 度，天氣狀況為小雨，降雨機率為 80%。因此，您出門時建議攜帶雨傘。",
        note: "工具結果塞回對話後，模型整合出最終回答" },
    ]},
    { label: "不用工具的問題", steps: [
      { who: "user", c: "#4C72B0", txt: "什麼是光合作用？用一句話說明。" },
      { who: "assistant（模型輸出・實測）", c: "#DD8452",
        txt: "光合作用是植物利用陽光將二氧化碳和水轉化為葡萄糖並釋放氧氣的過程。",
        note: "同一份 system prompt——模型自己判斷不需要工具、直接回答" },
    ]},
  ];
  const tabs = document.getElementById("agent-tabs");
  const stage = document.getElementById("agent-stage");
  const next = document.getElementById("agent-next");
  const reset = document.getElementById("agent-reset");
  const pos = document.getElementById("agent-pos");
  if (!tabs) return;
  let cur = 0, shown = 1;
  SCEN.forEach((s, i) => {
    const b = document.createElement("button");
    b.type = "button";
    b.className = "tab";
    b.textContent = s.label;
    b.addEventListener("click", () => { cur = i; shown = 1; render(); });
    tabs.appendChild(b);
  });
  function esc(t) { return t.replace(/&/g, "&amp;").replace(/</g, "&lt;"); }
  function render() {
    const s = SCEN[cur];
    tabs.querySelectorAll(".tab").forEach((el, i) => el.classList.toggle("on", i === cur));
    stage.innerHTML = s.steps.slice(0, shown).map((st) =>
      `<div class="bub" style="--bc:${st.c}"><div class="who">${esc(st.who)}</div>` +
      `<div class="txt">${esc(st.txt)}</div>` +
      (st.note ? `<div style="font-size:11.5px;color:#8a949b;margin-top:4px">${esc(st.note)}</div>` : "") +
      `</div>`).join("");
    next.disabled = shown >= s.steps.length;
    pos.textContent = `${shown} / ${s.steps.length}`;
  }
  next.addEventListener("click", () => { shown = Math.min(shown + 1, SCEN[cur].steps.length); render(); });
  reset.addEventListener("click", () => { shown = 1; render(); });
  render();
})();
"""
