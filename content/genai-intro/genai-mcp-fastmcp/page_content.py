"""課程頁內容區（純常數）。改完跑：python3 .claude/skills/make-lesson/scripts/page-fill.py content/genai-intro/genai-mcp-fastmcp
build.sh 不會部署這個檔；它是 index.html 內容區的正本。
hero 的封包資料在 SCRIPT 的 ERAS 常數（ERAS_BEGIN／ERAS_END 註解標記之間），由
content/genai-intro/_spikes/spike_genai_mcp_fastmcp.py --inject 寫入（別手改）。"""

TITLE = "MCP 新版協定與 FastMCP 4：線路上的真相"
DESCRIPTION = "MCP 兩年改了五版，2026-07-28 一口氣拿掉握手與 session。同一台 FastMCP 4.0.8 伺服器用五個年代各呼叫一次工具，真實 HTTP 封包逐發拆給你看；再站到負載平衡器的位置看無狀態解了什麼，最後是 FastMCP 4「遇到什麼問題用哪個功能」的地圖。"

STYLE = r"""
  /* 語義色：藍＝新協定（無狀態）、橘＝握手年代、紫＝最早的 HTTP+SSE、紅＝session／錯誤、綠＝成功 */
  :root { --c1: #4C72B0; --c2: #DD8452; --c3: #55A868; --c4: #8172B2; --cut: #C44E52; }

  .tldr { border-left: 4px solid var(--tc, var(--c1)); background: var(--chip-bg);
    border-radius: 0 10px 10px 0; padding: 10px 14px; margin: 12px 0 16px;
    font-size: 14.5px; line-height: 1.7; }
  .tldr b { color: var(--tc, var(--c1)); }

  /* hero：同一個動作、五個年代的真實封包 */
  #era-demo .pills { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 10px; }
  #era-demo .pill { font: inherit; font-size: 12.5px; font-weight: 800; font-family: var(--mono);
    color: var(--ink); background: var(--panel); border: 2px solid var(--grid); border-radius: 999px;
    padding: 5px 11px; cursor: pointer; }
  #era-demo .pill.on { color: #fff; background: var(--ec, var(--c1)); border-color: var(--ec, var(--c1)); }
  #era-demo .cap { border-left: 4px solid var(--ec, var(--c1)); padding: 4px 12px; margin-bottom: 10px; }
  #era-demo .cap b { font-size: 15px; }
  #era-demo .cap .who { font-size: 12px; color: var(--ink-soft); margin-top: 2px; }
  #era-demo .rows { display: flex; flex-direction: column; gap: 5px; }
  #era-demo .row { font: inherit; text-align: left; width: 100%; color: var(--ink);
    background: var(--panel); border: 1.5px solid var(--grid); border-radius: 9px; padding: 6px 9px;
    cursor: pointer; display: flex; flex-wrap: wrap; align-items: center; gap: 6px;
    animation: fadeup .22s ease both; }
  #era-demo .row:hover { border-color: var(--ink-soft); }
  #era-demo .row.open { border-color: var(--ec, var(--c1)); }
  #era-demo .row .no { font-family: var(--mono); font-size: 11px; color: var(--ink-soft); width: 1.8em; }
  #era-demo .row .verb { font-family: var(--mono); font-size: 12px; font-weight: 800; }
  #era-demo .row .what { font-family: var(--mono); font-size: 12.5px; flex: 1; min-width: 8em; }
  #era-demo .tag { font-size: 10.5px; font-weight: 800; color: #fff; border-radius: 5px; padding: 1px 6px; }
  #era-demo .tag.sid { background: var(--cut); }
  #era-demo .tag.meta { background: var(--c1); }
  #era-demo .tag.acc { background: var(--c4); }
  #era-demo .tag.st { background: var(--c3); }
  #era-demo .tag.st.bad { background: var(--cut); }
  #era-demo .detail { border: 1.5px dashed var(--grid); border-radius: 9px; padding: 8px 10px; margin: -2px 0 4px;
    font-size: 12px; }
  #era-demo .detail .lab { font-size: 11px; font-weight: 800; letter-spacing: .05em; color: var(--ink-soft); margin-top: 6px; }
  #era-demo .detail pre { font-family: var(--mono); font-size: 11.5px; line-height: 1.5; white-space: pre-wrap;
    word-break: break-all; background: var(--chip-bg); border-radius: 7px; padding: 6px 8px; margin: 3px 0;
    max-height: 260px; overflow: auto; }
  #era-demo .sum { margin-top: 10px; font-size: 13.5px; font-weight: 700; line-height: 1.7; }
  #era-demo .ctrl { display: flex; gap: 8px; margin-top: 10px; flex-wrap: wrap; }
  #era-demo .ctrl button { font: inherit; font-size: 13.5px; font-weight: 800; color: #fff;
    background: var(--ink); border: 2px solid var(--ink); border-radius: 10px; padding: 6px 14px; cursor: pointer; }
  #era-demo .ctrl button:disabled { opacity: .35; cursor: default; }
  #era-demo .src { font-size: 12px; color: var(--ink-soft); margin-top: 8px; }
  @keyframes fadeup { from { opacity: 0; transform: translateY(5px); } to { opacity: 1; transform: none; } }

  table.cmp { width: 100%; border-collapse: collapse; font-size: 13.5px; margin: 14px 0; min-width: 520px; }
  table.cmp th, table.cmp td { border-bottom: 1px solid var(--grid); padding: 8px 10px; text-align: left; vertical-align: top; }
  table.cmp th { font-size: 12px; letter-spacing: .04em; color: var(--ink-soft); }
  table.cmp td.v { font-family: var(--mono); font-weight: 800; white-space: nowrap; }
  .tw { overflow-x: auto; }
  .kbd { font-family: var(--mono); background: var(--chip-bg); padding: 1px 6px; border-radius: 5px; font-size: 13px; }
  .src { font-size: 12.5px; color: var(--ink-soft); }
  .box { border: 2px solid var(--grid); border-radius: 12px; padding: 10px 14px; margin: 14px 0; font-size: 14px; line-height: 1.75; }
  .box h3.sub { margin: 0 0 6px; font-size: 15px; }

  table.cheat { width: 100%; border-collapse: collapse; font-size: 14px; margin: 14px 0; }
  table.cheat td { border-bottom: 1px solid var(--grid); padding: 10px 12px; vertical-align: top; line-height: 1.7; }
  table.cheat td.t { font-weight: 800; white-space: nowrap; width: 10em; }
"""

WRAP = r'''
<section id="hero">
  <span class="eyebrow">GENAI 進階補充 · D · MCP × FASTMCP 4</span>
  <h1>MCP 新版協定與 FastMCP&nbsp;4：<br>線路上的真相</h1>
  <p style="margin-top:18px">
    主線 <a href="/genai-agents/">AI Agent 與 MCP</a> 那一課說 MCP 是 AI 工具界的 USB。
    但這個「USB」兩年內改了五版，而現行的 <b>2026-07-28</b> 版一口氣拿掉了握手、session 和長連線。
    下面是同一份 <b>FastMCP 4.0.8</b> 伺服器程式、同一件事（列出工具，再呼叫 <span class="kbd">add(2, 3)</span>），
    用五個年代的協定各做一次的<b>真實 HTTP 封包</b>——切換年代，點任何一列看 header 與 body：
  </p>

  <div class="hero-demo" id="era-demo">
    <div class="pills" id="era-pills"></div>
    <div class="cap" id="era-cap"></div>
    <div class="rows" id="era-rows"></div>
    <div class="sum" id="era-sum"></div>
    <div class="ctrl">
      <button type="button" id="era-prev">‹ 上一版</button>
      <button type="button" id="era-next">下一版 ›</button>
    </div>
    <div class="src">實測側錄：FastMCP 4.0.8＋MCP Python SDK 2.2.0，本機 HTTP 伺服器，2026-09-24。session id 是那一次的亂數。</div>
  </div>

  <p class="note">
    實驗場在你的瀏覽器裡跑，不用安裝任何東西、也不連任何伺服器——封包都是錄好的，圖表與模擬是現場算的。
    首次載入約需 30–60 秒，正好夠你讀完第 1 節。
  </p>
</section>

<section id="s1">
  <span class="eyebrow">01 · 版本地圖</span>
  <h2>五個版本：從「打電話」到「寄信」</h2>
  <div class="tldr" style="--tc:var(--c4)">
    <b>一句話重點</b>：MCP 的版本號是日期（最後一次不相容改動的那天）。前四版都在<b>同一條有狀態連線</b>上加功能；
    2026-07-28 把連線拆掉，改成<b>每一發請求自帶一切</b>。
  </div>
  <p>
    第一版規格的「基礎協定」清單裡白紙黑字寫著 <i>Stateful connections</i>：先握手、協商能力，之後所有對話都在這條線上，
    伺服器還能順著線反過來問客戶端（要 LLM 生成、要使用者輸入）。像打電話——線不斷，雙方隨時能開口。
    現行版把它改成寄信：每封信都寫齊寄件人、版本與能力，哪個郵局收到都能處理，
    代價是伺服器再也不能在你講到一半時插嘴反問。
  </p>
  <div class="tw">
  <table class="cmp">
    <tr><th>版本</th><th>一句話</th><th>重點改動（官方 changelog）</th></tr>
    <tr><td class="v" style="color:var(--c4)">2024-11-05</td><td>誕生</td><td>JSON-RPC＋有狀態連線；stdio 與 HTTP+SSE 兩種傳輸；tools／resources／prompts；sampling、roots</td></tr>
    <tr><td class="v" style="color:var(--c2)">2025-03-26</td><td>上雲</td><td>Streamable HTTP 取代 HTTP+SSE（單一端點＋Mcp-Session-Id）；OAuth 2.1；tool annotations；JSON-RPC batching</td></tr>
    <tr><td class="v" style="color:var(--c2)">2025-06-18</td><td>收斂與加固</td><td>拿掉剛加的 batching；structured output；elicitation；HTTP 請求必帶 MCP-Protocol-Version</td></tr>
    <tr><td class="v" style="color:var(--c2)">2025-11-25</td><td>企業化</td><td>實驗性 tasks；URL elicitation；CIMD 用戶端註冊；icons；sampling 可帶 tools</td></tr>
    <tr><td class="v" style="color:var(--c1)">2026-07-28</td><td>無狀態（現行）</td><td>移除握手、session、GET 長連線、ping；新增 server/discover、_meta 信封、Mcp-Method／Mcp-Name header、多回合請求（MRTR）、快取提示；tasks 改成官方擴充；Roots／Sampling／Logging 棄用</td></tr>
  </table>
  </div>
  <p class="src">來源：modelcontextprotocol.io 各版 changelog 與 deprecated 登記表（2026-09-24 查閱）。棄用的功能至少保留 12 個月才可能移除（SEP-2596）。</p>
  <p>
    同一天（2026-07-28）MCP Python SDK v2 與 FastMCP 4.0.0b1 一起發布；FastMCP <b>4.0.0 正式版</b>在 2026-08-31 推出，
    本課用的 <b>4.0.8</b> 是 2026-09-23 的版本（PyPI）。一台 FastMCP 4 伺服器<b>同時服務新舊年代</b>——開場 2025-03-26 到 2026-07-28
    那四組封包是同一台伺服器接的（2024-11-05 的 HTTP+SSE 是同一份程式改用 <span class="kbd">transport="sse"</span> 起的）。
  </p>
  <button class="golab" data-nb="1️⃣">到實驗場 1️⃣ 看版本×機制對照圖，逐版翻 changelog</button>
</section>

<section id="s2">
  <span class="eyebrow">02 · 線路上的真相</span>
  <h2>新協定的一發請求，身上帶了什麼</h2>
  <div class="tldr" style="--tc:var(--c1)">
    <b>一句話重點</b>：沒有握手之後，每一發都要<b>自我介紹</b>——body 的 <span class="kbd">_meta</span> 帶協定版本與客戶端能力，
    header 鏡射 method 與工具名，給看不懂 JSON-RPC 的中間設備讀。
  </div>
  <p>這是開場 2026-07-28 那組的第 3 發，內容原封不動、只重新排版（FastMCP Client 送出的）：</p>
  <div class="codeblock">POST /mcp
accept: application/json, text/event-stream
content-type: application/json
mcp-protocol-version: 2026-07-28
mcp-method: tools/call
mcp-name: add

{"jsonrpc": "2.0", "id": 3, "method": "tools/call",
 "params": {
   "name": "add",
   "arguments": {"a": 2, "b": 3},
   "_meta": {
     "io.modelcontextprotocol/protocolVersion": "2026-07-28",
     "io.modelcontextprotocol/clientInfo":
         {"name": "mcp", "version": "0.1.0"},
     "io.modelcontextprotocol/clientCapabilities": {},
     "io.modelcontextprotocol/logLevel": "debug",
     "progressToken": 3}}}</div>
  <p>
    對照握手年代（2025-11-25）同一個呼叫，body 只剩 <span class="kbd">{"name": "add", "arguments": {...}}</span>，
    身分全靠 header 裡那把 <span class="kbd">mcp-session-id</span>——伺服器得記得「這把 id 是誰、協商了什麼」。
    回應也多了東西：新協定的每個結果都有 <span class="kbd">resultType</span>（<span class="kbd">complete</span> 或 <span class="kbd">input_required</span>），
    列表類結果帶 <span class="kbd">ttlMs</span>／<span class="kbd">cacheScope</span> 快取提示。
  </p>
  <p>
    一個誠實的細節：無狀態<b>不等於省流量</b>。實測同一個動作，新協定 3 發請求的 body 合計比舊協定 6 發還大
    （數字在實驗場 2️⃣ 的帳本裡）——每一發都自帶身分證是要成本的。它換到的是下一節的東西。
  </p>
  <button class="golab" data-nb="2️⃣">到實驗場 2️⃣ 逐封包拆解七個情境</button>
</section>

<section id="s3">
  <span class="eyebrow">03 · 為什麼要無狀態</span>
  <h2>站在負載平衡器的位置看</h2>
  <div class="tldr" style="--tc:var(--cut)">
    <b>一句話重點</b>：session 活在發它的那台伺服器的記憶體裡。副本一多，請求走錯台就是 <span class="kbd">Session not found</span>；
    無狀態協定讓<b>任何一台都接得住任何一發</b>。
  </div>
  <p>
    我們真的起了兩台副本（A、B）和一個「輪流分派」的負載平衡器，新舊客戶端各做一次「列工具＋呼叫 add」：
  </p>
  <div class="tw">
  <table class="cmp">
    <tr><th>情境</th><th>請求落點（實測）</th><th>結果</th></tr>
    <tr><td>輪流 × 新協定</td><td><span class="kbd">A:discover</span> <span class="kbd">B:tools/list</span> <span class="kbd">A:tools/call</span>，全部 200</td><td style="color:var(--c3);font-weight:800">成功</td></tr>
    <tr><td>輪流 × 舊協定</td><td><span class="kbd">A:initialize</span> 拿到 session，下一發被分到 B → <span class="kbd">404</span></td><td style="color:var(--cut);font-weight:800">MCPError: Session not found</td></tr>
    <tr><td>黏著 × 舊協定</td><td>負載平衡器記住「這把 session 是 A 發的」，6 發全送 A</td><td style="color:var(--c3);font-weight:800">成功</td></tr>
  </table>
  </div>
  <p>
    黏著分派（sticky）救得了路由，救不了「那台不見了」——副本重啟、縮容，上面的 session 全滅。
    新協定還順手解了兩件事：
  </p>
  <p>
    <b>① gateway 不拆 body 也能路由。</b>每發都有 <span class="kbd">Mcp-Method</span>、<span class="kbd">Mcp-Name</span>；
    工具參數標上 <span class="kbd">x-mcp-header</span> 還會鏡射成 <span class="kbd">Mcp-Param-*</span>（實測：租戶參數變成
    <span class="kbd">mcp-param-tenant: acme</span>），按租戶分叢集不用解析 JSON。伺服器則<b>強制檢查 header 與 body 一致</b>，
    免得 gateway 看 header、伺服器看 body、兩邊各說各話。
  </p>
  <p>
    <b>② 伺服器不再「插嘴反問」。</b>舊協定裡工具可以停在半路，順著連線發一個 <span class="kbd">elicitation/create</span> 給客戶端，
    等答案回到<b>同一台、同一條 session</b>。新協定改成多回合請求（MRTR）：工具直接回
    <span class="kbd">resultType: "input_required"</span> 結束這一回合，客戶端問完使用者，帶著
    <span class="kbd">inputResponses</span> 重打同一個工具——第二發落到哪台都行。
    長時間的連線也一起退場：GET 長連線與斷線續傳（Last-Event-ID）移除，要訂閱變更改用
    <span class="kbd">subscriptions/listen</span>，要跑很久的工作改用 tasks 擴充（投遞 → 輪詢）。
  </p>
  <button class="golab" data-nb="3️⃣">到實驗場 3️⃣ 拉副本數、換分派策略</button>
</section>

<section id="s4">
  <span class="eyebrow">04 · 手刻一發請求</span>
  <h2>不用 SDK、不用握手，一發 POST 呼叫工具</h2>
  <div class="tldr" style="--tc:var(--c1)">
    <b>一句話重點</b>：四樣東西一個都不能少、而且要彼此一致——版本 header、<span class="kbd">_meta</span> 信封、
    <span class="kbd">Mcp-Method</span>、<span class="kbd">Mcp-Name</span>。
  </div>
  <p>
    實驗場 4️⃣ 給你四個旋鈕，每一種組合的回應都是真的打過一次錄下來的（4×3×3×5＝180 發）。
    從實測回推出 FastMCP 4.0.8 的檢查順序：
  </p>
  <div class="tw">
  <table class="cmp">
    <tr><th>#</th><th>檢查</th><th>沒過的實測回應</th></tr>
    <tr><td class="v">1</td><td>版本 header 決定走哪個年代（沒帶或帶 2025-11-25 → 當你是舊客戶端）</td><td><span class="kbd">-32600 Bad Request: Missing session ID</span></td></tr>
    <tr><td class="v">2</td><td><span class="kbd">_meta</span> 要有 protocolVersion 與 clientCapabilities</td><td><span class="kbd">-32602 params._meta …</span></td></tr>
    <tr><td class="v">3</td><td>header 版本＝<span class="kbd">_meta</span> 版本</td><td><span class="kbd">-32020 mcp-protocol-version header does not match …</span></td></tr>
    <tr><td class="v">4</td><td>Mcp-Method 要有且等於 body 的 method</td><td><span class="kbd">-32020 mcp-method header does not match …</span></td></tr>
    <tr><td class="v">5</td><td>Mcp-Name 要有且等於工具名</td><td><span class="kbd">-32020 mcp-name header does not match …</span></td></tr>
    <tr><td class="v">6</td><td>伺服器支援這個版本</td><td><span class="kbd">-32022 Unsupported protocol version</span>（附上 supported 清單）</td></tr>
  </table>
  </div>
  <p class="src">順序是從實測回推的（FastMCP 4.0.8＋mcp 2.2.0），不是規格規定的順序；錯誤碼 -32020／-32022 則是 2026-07-28 規格分配的。</p>
  <button class="golab" data-nb="4️⃣">到實驗場 4️⃣ 轉旋鈕，找出唯一回 200 的組合</button>
</section>

<section id="s5">
  <span class="eyebrow">05 · FASTMCP 4 功能地圖</span>
  <h2>我遇到這個問題 → 用哪個功能</h2>
  <div class="tldr" style="--tc:var(--c3)">
    <b>一句話重點</b>：傳輸無狀態，<b>應用照樣可以有狀態</b>——FastMCP 4 把 session、反問、長任務
    改成應用層的顯式零件，一台伺服器同時服務新舊兩個年代。
  </div>
  <div class="tw">
  <table class="cmp">
    <tr><th>遇到的問題</th><th>用這個</th></tr>
    <tr><td>已經有 FastAPI 服務／別家 REST API 的 OpenAPI 規格</td><td><span class="kbd">FastMCP.from_fastapi(app)</span>／<span class="kbd">FastMCP.from_openapi(spec, client)</span></td></tr>
    <tr><td>好幾台 server 想合成一台；要轉手別人的 server</td><td><span class="kbd">hub.mount(sub, namespace=…)</span>／<span class="kbd">create_proxy(…)</span></td></tr>
    <tr><td>agent 要同時接很多台（客戶端）</td><td><span class="kbd">ClientGroup</span>（4.0.0b5 新增）</td></tr>
    <tr><td>工具幾十個，模型挑不準</td><td><span class="kbd">BM25SearchTransform</span>：模型只看到 search_tools＋call_tool</td></tr>
    <tr><td>每次呼叫都要記 log、計時、限流</td><td><span class="kbd">Middleware</span></td></tr>
    <tr><td>只有管理員能用某些工具</td><td><span class="kbd">auth=</span>＋<span class="kbd">require_scopes("admin")</span></td></tr>
    <tr><td>gateway 要依租戶分流；客戶端一直重複 list_tools</td><td><span class="kbd">x-mcp-header</span>；<span class="kbd">cache_ttl</span>＋<span class="kbd">Client(cache=True)</span></td></tr>
    <tr><td>工具跑到一半要使用者確認</td><td>回傳 <span class="kbd">InputRequiredResult</span>（新協定）；<span class="kbd">ctx.elicit()</span> 只剩舊協定能用</td></tr>
    <tr><td>工具要跑好幾分鐘</td><td><span class="kbd">@mcp.tool(task=True)</span>＋<span class="kbd">fastmcp-tasks</span></td></tr>
    <tr><td>要記住購物車（跨呼叫、跨連線）</td><td><span class="kbd">SessionId</span>／<span class="kbd">UserSession</span>＋共用 store</td></tr>
  </table>
  </div>
  <p>
    實驗場 5️⃣ 有 19 張卡，每張附最小程式與<b>在 4.0.8 上實測到的證據</b>（例如 30 個工具的目錄，模型 <span class="kbd">list_tools</span> 只看到 2 個；
    客戶端呼叫 3 次 <span class="kbd">list_tools</span>，線路上只有 1 發）。
  </p>
  <div class="box">
    <h3 class="sub">上過 LLM 應用開發系列的 FastMCP 4 課？那幾課用 4.0.0b1，正式版有這些不同</h3>
    <ul style="margin:4px 0 0;padding-left:1.2em">
      <li>線路形狀沒變：本課用 4.0.8 重測，新協定 3 發、舊協定 6 發，與 b1 的紀錄一致；裸 POST 的必要條件也相同。</li>
      <li>裝法變簡單：正式版直接 <span class="kbd">fastmcp==4.0.8</span>，不必再同時釘 prerelease 的 fastmcp-slim。</li>
      <li>新增 <span class="kbd">ClientGroup</span>（b5）、<span class="kbd">CallArgument</span>／<span class="kbd">Depends</span> 注入（b3）；4.0.2 起可 <span class="kbd">from fastmcp import ClientGroup</span>。</li>
      <li>確定拿掉 <span class="kbd">ctx.sample()</span>、<span class="kbd">ctx.list_roots()</span>；<span class="kbd">ctx.elicit()</span> 只在舊協定連線可用（新協定連線上實測：<span class="kbd">elicitation via server-initiated requests is unavailable on 2026-07-28 connections.</span>）。</li>
      <li><span class="kbd">Client("server.py")</span> 用字串指本機檔案改為棄用，請傳 <span class="kbd">Path</span>（FastMCP 5 移除）。</li>
    </ul>
    <p class="src" style="margin-top:6px">來源：FastMCP GitHub releases v4.0.0–v4.0.8 與官方 What's New（2026-09-24 查閱）。</p>
  </div>
  <p>
    想真的動手寫這些 server，本站有外部軌的深入版：
    <a href="/fastmcp4/">FastMCP 4 入門</a>、<a href="/fastmcp4-auth/">認證</a>、<a href="/fastmcp4-state/">狀態與加密</a>、
    <a href="/fastmcp4-features/">4.0 專屬功能</a>、<a href="/mcp-servers/">常見 MCP 服務</a>（LLM 應用開發系列，在 molab 免費 CPU 環境跑）。
  </p>
  <button class="golab" data-nb="5️⃣">到實驗場 5️⃣ 翻功能卡，看實測證據</button>
</section>

<section id="s6">
  <span class="eyebrow">06 · 速查</span>
  <h2>本課名詞速查卡</h2>
  <table class="cheat">
    <tr><td class="t" style="color:var(--c4)">協定版本（日期）</td>
        <td>最後一次不相容改動的日期；現行 <b>2026-07-28</b>。每個請求自己宣告版本，伺服器逐發接受或拒絕。</td></tr>
    <tr><td class="t" style="color:var(--c1)">server/discover</td>
        <td>取代 initialize 的「自我介紹」RPC：一發拿到支援版本、能力、伺服器身分。伺服器必須實作，客戶端<b>可以不呼叫</b>。</td></tr>
    <tr><td class="t" style="color:var(--c1)">_meta 信封</td>
        <td>每個請求 body 裡的 <span class="kbd">io.modelcontextprotocol/protocolVersion</span>＋<span class="kbd">clientCapabilities</span>（＋clientInfo）——握手搬進了每一發。</td></tr>
    <tr><td class="t" style="color:var(--c1)">Mcp-Method／Mcp-Name</td>
        <td>把 method 與工具名鏡射到 HTTP header，讓 gateway 不拆 body 就能路由；與 body 不一致回 <b>-32020</b>。</td></tr>
    <tr><td class="t" style="color:var(--c1)">MRTR（input_required）</td>
        <td>伺服器不再主動發 request；回 <span class="kbd">input_required</span> 結束回合，客戶端帶 <span class="kbd">inputResponses</span> 重打。</td></tr>
    <tr><td class="t" style="color:var(--cut)">Mcp-Session-Id</td>
        <td>握手年代的 session 鑰匙，只有發它的那台認得；2026-07-28 移除。跨請求狀態改由應用層發「顯式鑰匙」（FastMCP 的 SessionId）。</td></tr>
    <tr><td class="t" style="color:var(--c3)">FastMCP 4</td>
        <td>一台伺服器同時服務新舊年代；stateless transport, stateful application。4.0.0 正式版 2026-08-31。</td></tr>
  </table>
</section>

<section id="s7">
  <span class="eyebrow">07 · 實戰</span>
  <h2>換你動手</h2>
  <div class="ex">
    <span class="lv">LEVEL 1</span>
    <p>在實驗場 4️⃣ 轉出唯一回 200 的組合。接著把版本 header 和 <span class="kbd">_meta</span> 都換成 2025-11-25——錯誤訊息變成什麼？伺服器為什麼跟你要 session？</p>
  </div>
  <div class="ex">
    <span class="lv">LEVEL 2</span>
    <p>在 3️⃣ 把副本拉到 3、策略選「輪流分派」，舊協定大約多少 session 能整段成功？換成「黏著分派」呢？黏著救得了「那台副本重啟」嗎？</p>
  </div>
  <div class="ex">
    <span class="lv">LEVEL 3</span>
    <p>在 2️⃣ 對照情境 ④ 與 ⑤：兩邊各有幾發 HTTP、伺服器有沒有反過來發 request？說明為什麼新協定的「確認刪除」可以跨副本、跨重啟，舊的不行。</p>
  </div>
  <p style="font-size:13.5px;color:var(--ink-soft);margin-top:10px">卡住了？三題在實驗場最後一格都有折疊解答——先自己做，再打開對照。</p>
  <button class="golab" data-nb="6️⃣">到實驗場 6️⃣ 對照解答</button>
  <div class="box">
    <h3 class="sub">帶回家自己跑（免費）</h3>
    <p style="margin:0">
      本課的全部封包出自一支腳本：<a href="https://github.com/skmygo/agentclass/blob/main/content/genai-intro/_spikes/spike_genai_mcp_fastmcp.py" target="_blank" rel="noopener">spike_genai_mcp_fastmcp.py</a>。
      裝好 <a href="https://docs.astral.sh/uv/" target="_blank" rel="noopener">uv</a> 後一行
      <span class="kbd">uv run --script spike_genai_mcp_fastmcp.py</span> 就會在你的電腦起十台小伺服器（只綁 127.0.0.1）、
      把五個年代、180 發手刻請求、兩副本實驗全部重錄一遍，約 10 秒。純 CPU、不需要任何 key、除了第一次下載套件不連外。
      我們在 Linux（Python 3.12）實測過；其他平台與雲端筆記本沒有驗證。
    </p>
  </div>
</section>

<section id="quiz">
  <span class="eyebrow">08 · 驗收</span>
  <h2>情境測驗</h2>
  <p>離開前試試看：下面的情境都真的會遇到。每題選一個你認為的最佳做法，選了馬上看得到解釋。</p>
  <div data-quiz>

    <div class="quiz-q" data-answer="B">
      <p class="quiz-tag">Q1 <span class="qtype">情境題</span></p>
      <h3>你的 MCP 伺服器升級成 FastMCP 4，部署成 3 個副本、前面是一般的輪流分派負載平衡器。新版客戶端一切正常，但還沒升級的舊客戶端（只會握手協定）時不時噴 <code>Session not found</code>。最合適的處理是？</h3>
      <div class="quiz-opts">
        <button type="button" class="quiz-opt" data-k="A">A. 把所有客戶端都設成 <code>mode="legacy"</code>，讓大家行為一致</button>
        <button type="button" class="quiz-opt" data-k="B">B. 負載平衡器對帶 <code>Mcp-Session-Id</code> 的請求做黏著分派（依 header 釘同一台），新協定請求照常輪流；同時推動客戶端升級</button>
        <button type="button" class="quiz-opt" data-k="C">C. 副本縮回 1 台，問題就消失了</button>
        <button type="button" class="quiz-opt" data-k="D">D. 把 session 閒置逾時調長，session 就不會被清掉</button>
      </div>
      <div class="quiz-fb" aria-live="polite"><p>問題的根源是舊協定的 session 只活在發它的那一台（本課兩副本實測：initialize 落在 A 拿到 session，下一發被分到 B，B 回 <code>404 Session not found</code>）。只有「帶 session 的請求」需要回到原來那台，所以對它們做黏著分派就夠了（實測黏著後 6 發全落 A、成功）；新協定請求沒有 session，繼續輪流、享受無狀態的擴展性。A 走回頭路，把能自由分派的新客戶端也綁死；C 能動但放棄了多副本的意義；D 症狀相似但原因不同——session 不是被清掉，是請求根本送到了不認得它的另一台。</p></div>
    </div>

    <div class="quiz-q" data-answer="C">
      <p class="quiz-tag">Q2 <span class="qtype dx">錯誤診斷</span></p>
      <h3>同事想不透過 SDK、用一發 POST 呼叫 <code>add</code> 工具。他的 header 是從上一發 <code>tools/list</code> 請求複製來改的，結果拿到 400。最可能的原因是？</h3>
      <div class="codeblock">POST /mcp
MCP-Protocol-Version: 2026-07-28
Mcp-Method: tools/list
Mcp-Name: add

{"jsonrpc": "2.0", "id": 1, "method": "tools/call",
 "params": {
   "name": "add",
   "arguments": {"a": 2, "b": 3},
   "_meta": {
     "io.modelcontextprotocol/protocolVersion": "2026-07-28",
     "io.modelcontextprotocol/clientCapabilities": {}}}}

→ 400
{"jsonrpc":"2.0","id":1,"error":{"code":-32020,
"message":"mcp-method header does not match the request body's method"}}</div>
      <div class="quiz-opts">
        <button type="button" class="quiz-opt" data-k="A">A. 伺服器不支援 2026-07-28 版</button>
        <button type="button" class="quiz-opt" data-k="B">B. 新協定一定要先打一發 <code>server/discover</code> 才能呼叫工具</button>
        <button type="button" class="quiz-opt" data-k="C">C. header 的 <code>Mcp-Method</code> 還是 <code>tools/list</code>，跟 body 的 <code>tools/call</code> 對不上——改成 <code>tools/call</code> 就好</button>
        <button type="button" class="quiz-opt" data-k="D">D. <code>_meta</code> 少了 <code>clientInfo</code></button>
      </div>
      <div class="quiz-fb" aria-live="polite"><p>這段錯誤訊息是本課實測原文：新協定把 method 鏡射到 <code>Mcp-Method</code> header 讓 gateway 不拆 body 就能路由，伺服器因此<b>強制檢查 header 與 body 一致</b>——否則 gateway 以為是無害的 tools/list、伺服器卻執行了 tools/call，正是規格要防的「兩邊各信各的」。錯誤碼 -32020 就是 HeaderMismatch。A 不對：不支援版本會回 -32022 並附 supported 清單；B 不對：discover 是選用的，本課 180 發手刻請求都沒打 discover，照樣有 1 發成功；D 不對：clientInfo 是 SHOULD 不是必填，實測成功的那發也沒帶。</p></div>
    </div>

    <div class="quiz-q" data-answer="B">
      <p class="quiz-tag">Q3 <span class="qtype dx">錯誤診斷</span></p>
      <h3>你在 FastMCP 4 的刪檔工具裡寫了 <code>await ctx.elicit("確定刪除？", response_type=bool)</code>。舊版 Claude Desktop 接上來一切正常；換成新版客戶端呼叫同一個工具，得到下面的錯誤。該怎麼修？</h3>
      <div class="codeblock">ToolError: elicitation via server-initiated requests is unavailable on 2026-07-28 connections.</div>
      <div class="quiz-opts">
        <button type="button" class="quiz-opt" data-k="A">A. 新版客戶端忘了設 <code>elicitation_handler</code>，請客戶端補上</button>
        <button type="button" class="quiz-opt" data-k="B">B. 新協定拿掉了「伺服器反向發 request」：改成工具直接回傳 <code>InputRequiredResult</code>，下一回合從 <code>ctx.input_responses</code> 讀答案（要同時服務舊客戶端就依 <code>ctx.request_context.protocol_version</code> 分支）</button>
        <button type="button" class="quiz-opt" data-k="C">C. FastMCP 版本太舊，升級到最新版就好</button>
        <button type="button" class="quiz-opt" data-k="D">D. 改用 <code>ctx.sample()</code> 讓客戶端的模型幫忙判斷要不要刪</button>
      </div>
      <div class="quiz-fb" aria-live="polite"><p>錯誤原文（本課在 4.0.8 實測）已經講了原因：2026-07-28 連線上<b>沒有</b>伺服器反向發 request 的通道。舊協定的 <code>ctx.elicit()</code> 是讓工具停在半路、順著 session 問客戶端；新協定改成多回合請求——工具回 <code>input_required</code> 結束這一回合，客戶端問完使用者、帶著 <code>inputResponses</code> 重打（實驗場 2️⃣ 情境 ④ 就是這個線路）。A 症狀相似但原因不同：handler 有沒有設都一樣，這條路在新協定上根本不存在；C 說反了，4.0.8 就是最新版，這是設計不是 bug；D 更糟：<code>ctx.sample()</code> 在 FastMCP 4 已經移除（實測 <code>'Context' object has no attribute 'sample'</code>），Sampling 本身在 2026-07-28 也被棄用。</p></div>
    </div>

    <div class="quiz-q" data-answer="B">
      <p class="quiz-tag">Q4 <span class="qtype">情境題</span></p>
      <h3>公司有一套 40 個端點的訂單系統 REST API（有 OpenAPI 規格），想讓 agent 能用它；你也擔心 40 個工具說明書塞爆上下文、模型挑錯工具。最省力又穩的做法是？</h3>
      <div class="quiz-opts">
        <button type="button" class="quiz-opt" data-k="A">A. 手寫 40 個 <code>@mcp.tool</code> 包裝函式，每個都仔細寫 docstring</button>
        <button type="button" class="quiz-opt" data-k="B">B. <code>FastMCP.from_openapi(spec, client)</code> 直接把規格變成工具，再加 <code>BM25SearchTransform</code>，讓模型先 <code>search_tools</code> 再 <code>call_tool</code></button>
        <button type="button" class="quiz-opt" data-k="C">C. 把整份 OpenAPI 規格塞進 system prompt，讓模型自己組 HTTP 請求</button>
        <button type="button" class="quiz-opt" data-k="D">D. 每個端點各包成一台 MCP server，再用 <code>ClientGroup</code> 全部接起來</button>
      </div>
      <div class="quiz-fb" aria-live="polite"><p>兩個問題各有現成零件：<code>from_openapi</code> 讀規格自動生成工具（實測三個路由 → 三個工具，名稱取自 operationId、參數取自規格），<code>BM25SearchTransform</code> 把大目錄藏在搜尋後面（實測 30 個工具的目錄，模型 <code>list_tools</code> 只看到 <code>search_tools</code> 與 <code>call_tool</code>）。A 能動但 40 份手工包裝要跟著 API 改版一起維護，而且沒解決上下文爆量；C 讓模型直接拼 HTTP，失去 schema 驗證與權限控管，出錯也難追；D 把一個系統拆成 40 台 server，部署與命名都變複雜，而且模型看到的工具數一個也沒少。</p></div>
    </div>

    <div class="quiz-q" data-answer="C">
      <p class="quiz-tag">Q5 <span class="qtype">情境題</span></p>
      <h3>有個「產生月報」工具要跑 8–10 分鐘。伺服器是多副本部署，使用者的網路偶爾會斷。在 2026-07-28 協定下怎麼設計最穩？</h3>
      <div class="quiz-opts">
        <button type="button" class="quiz-opt" data-k="A">A. 把 <code>tools/call</code> 的逾時調到 15 分鐘，讓請求一直開著等結果</button>
        <button type="button" class="quiz-opt" data-k="B">B. 用舊協定連線，斷線時靠 <code>Last-Event-ID</code> 續傳</button>
        <button type="button" class="quiz-opt" data-k="C">C. 做成背景任務：<code>@mcp.tool(task=True)</code>＋<code>fastmcp-tasks</code>（多副本用共用的 Redis 後端），呼叫立刻拿到 taskId，客戶端用 <code>tasks/get</code> 輪詢</button>
        <button type="button" class="quiz-opt" data-k="D">D. 工具先回「請十分鐘後再問我一次」，讓使用者自己記得回來問</button>
      </div>
      <div class="quiz-fb" aria-live="polite"><p>長工作要脫離請求本身：tasks 擴充（2026-07-28 從核心移出、成為官方擴充 <code>io.modelcontextprotocol/tasks</code>）讓 <code>tools/call</code> 立刻回一個 taskId，之後每次 <code>tasks/get</code> 都是獨立的一發（實驗場 2️⃣ 情境 ⑥：投遞後一串輪詢，最後 <code>completed</code>）。多副本時把任務後端放在共用的 Redis，哪一台接到輪詢都查得到。A 很脆弱：新協定下回應串流一斷，這個請求就沒了、只能重打（規格已移除續傳）；B 正是 2026-07-28 拿掉的機制，而且又把你綁回 session；D 沒有任何可追蹤的把手，使用者問第二次時伺服器也不知道是哪一份報表。</p></div>
    </div>

    <div class="quiz-score" data-score></div>
  </div>
</section>

<div class="endnav">
  <a href="/genai-skills/">
    <span class="tag">下一課</span>
    <b>補充 E：Agent Skills →</b>
  </a>
  <a href="/genai-intro/">
    <span class="tag">主題</span>
    <b>‹ 回「生成式 AI 導論」課程列表</b>
  </a>
</div>
'''

SCRIPT = r"""
/* ═══ hero：同一個動作、五個年代的真實封包（FastMCP 4.0.8 側錄，2026-09-24）═══ */
(function () {
  const ERAS = /*ERAS_BEGIN*/{"2026-07-28":{"client":"FastMCP Client 4.0.8（預設 mode=auto）","protocol":"2026-07-28","result":5,"wire":[{"t":10,"m":"POST","path":"/mcp","rh":{"accept":"application/json, text/event-stream","content-type":"application/json","mcp-protocol-version":"2026-07-28","mcp-method":"server/discover"},"st":200,"sh":{"content-type":"application/json"},"rb":"{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"server/discover\",\"params\":{\"_meta\":{\"io.modelcontextprotocol/protocolVersion\":\"2026-07-28\",\"io.modelcontextprotocol/clientInfo\":{\"name\":\"mcp\",\"version\":\"0.1.0\"},\"io.modelcontextprotocol/clientCapabilities\":{}}}}","rbn":245,"sb":"{\"jsonrpc\":\"2.0\",\"id\":1,\"result\":{\"_meta\":{\"io.modelcontextprotocol/serverInfo\":{\"name\":\"calc\",\"version\":\"4.0.8\"}},\"ttlMs\":0,\"cacheScope\":\"private\",\"supportedVersions\":[\"2026-07-28\"],\"capabilities\":{\"logging\":{},\"prompts\":{\"listChanged\":false},\"resources\":{\"subscribe\":false,\"listChanged\":false},\"tools\":{\"listChanged\":false},\"extensions\":{\"io.modelcontextprotocol/ui\":{}}},\"instructions\":\"A tiny calculator.\",\"resultType\":\"complete\"}}","sbn":435},{"t":67,"m":"POST","path":"/mcp","rh":{"accept":"application/json, text/event-stream","content-type":"application/json","mcp-protocol-version":"2026-07-28","mcp-method":"tools/list"},"st":200,"sh":{"content-type":"application/json"},"rb":"{\"jsonrpc\":\"2.0\",\"id\":2,\"method\":\"tools/list\",\"params\":{\"_meta\":{\"io.modelcontextprotocol/protocolVersion\":\"2026-07-28\",\"io.modelcontextprotocol/clientInfo\":{\"name\":\"mcp\",\"version\":\"0.1.0\"},\"io.modelcontextprotocol/clientCapabilities\":{},\"io.modelcontextprotocol/logLevel\":\"debug\"}}}","rbn":283,"sb":"{\"jsonrpc\":\"2.0\",\"id\":2,\"result\":{\"cacheScope\":\"private\",\"resultType\":\"complete\",\"tools\":[{\"_meta\":{\"fastmcp\":{\"tags\":[]}},\"description\":\"Add two integers.\",\"inputSchema\":{\"type\":\"object\",\"additionalProperties\":false,\"properties\":{\"a\":{\"type\":\"integer\"},\"b\":{\"type\":\"integer\"}},\"required\":[\"a\",\"b\"]},\"name\":\"add\",\"outputSchema\":{\"properties\":{\"result\":{\"type\":\"integer\"}},\"required\":[\"result\"],\"type\":\"object\",\"x-fastmcp-wrap-result\":true},\"title\":\"Add\"}],\"ttlMs\":0,\"_meta\":{\"io.modelcontextprotocol/serverInfo\":{\"name\":\"calc\",\"version\":\"4.0.8\"}}}}","sbn":548},{"t":71,"m":"POST","path":"/mcp","rh":{"accept":"application/json, text/event-stream","content-type":"application/json","mcp-protocol-version":"2026-07-28","mcp-method":"tools/call","mcp-name":"add"},"st":200,"sh":{"content-type":"application/json"},"rb":"{\"jsonrpc\":\"2.0\",\"id\":3,\"method\":\"tools/call\",\"params\":{\"name\":\"add\",\"arguments\":{\"a\":2,\"b\":3},\"_meta\":{\"io.modelcontextprotocol/protocolVersion\":\"2026-07-28\",\"io.modelcontextprotocol/clientInfo\":{\"name\":\"mcp\",\"version\":\"0.1.0\"},\"io.modelcontextprotocol/clientCapabilities\":{},\"io.modelcontextprotocol/logLevel\":\"debug\",\"progressToken\":3}}}","rbn":340,"sb":"{\"jsonrpc\":\"2.0\",\"id\":3,\"result\":{\"_meta\":{\"fastmcp\":{\"wrap_result\":true},\"io.modelcontextprotocol/serverInfo\":{\"name\":\"calc\",\"version\":\"4.0.8\"}},\"content\":[{\"text\":\"5\",\"type\":\"text\"}],\"isError\":false,\"resultType\":\"complete\",\"structuredContent\":{\"result\":5}}}","sbn":259}]},"2025-11-25":{"client":"FastMCP Client 4.0.8（mode=legacy）","protocol":"2025-11-25","result":5,"wire":[{"t":2,"m":"POST","path":"/mcp","rh":{"accept":"application/json, text/event-stream","content-type":"application/json"},"st":200,"sh":{"content-type":"text/event-stream","mcp-session-id":"223ae1b206344bec917c9a8da5209691"},"rb":"{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"initialize\",\"params\":{\"protocolVersion\":\"2025-11-25\",\"capabilities\":{},\"clientInfo\":{\"name\":\"mcp\",\"version\":\"0.1.0\"},\"_meta\":{}}}","rbn":163,"sb":"event: message\ndata: {\"jsonrpc\":\"2.0\",\"id\":1,\"result\":{\"protocolVersion\":\"2025-11-25\",\"capabilities\":{\"logging\":{},\"prompts\":{\"listChanged\":true},\"resources\":{\"subscribe\":false,\"listChanged\":true},\"tools\":{\"listChanged\":true}},\"serverInfo\":{\"name\":\"calc\",\"version\":\"4.0.8\"},\"instructions\":\"A tiny calculator.\"}}\n\n","sbn":316},{"t":5,"m":"POST","path":"/mcp","rh":{"accept":"application/json, text/event-stream","content-type":"application/json","mcp-session-id":"223ae1b206344bec917c9a8da5209691","mcp-protocol-version":"2025-11-25"},"st":202,"sh":{"content-type":"application/json","mcp-session-id":"223ae1b206344bec917c9a8da5209691"},"rb":"{\"jsonrpc\":\"2.0\",\"method\":\"notifications/initialized\"}","rbn":54,"sb":"","sbn":0},{"t":5,"m":"GET","path":"/mcp","rh":{"accept":"application/json, text/event-stream","content-type":"application/json","mcp-session-id":"223ae1b206344bec917c9a8da5209691","mcp-protocol-version":"2025-11-25"},"st":200,"sh":{"content-type":"text/event-stream","mcp-session-id":"223ae1b206344bec917c9a8da5209691"},"rb":"","rbn":0,"sb":"","sbn":0},{"t":6,"m":"POST","path":"/mcp","rh":{"accept":"application/json, text/event-stream","content-type":"application/json","mcp-session-id":"223ae1b206344bec917c9a8da5209691","mcp-protocol-version":"2025-11-25"},"st":200,"sh":{"content-type":"text/event-stream","mcp-session-id":"223ae1b206344bec917c9a8da5209691"},"rb":"{\"jsonrpc\":\"2.0\",\"id\":2,\"method\":\"tools/list\",\"params\":{\"_meta\":{}}}","rbn":68,"sb":"event: message\ndata: {\"jsonrpc\":\"2.0\",\"id\":2,\"result\":{\"tools\":[{\"_meta\":{\"fastmcp\":{\"tags\":[]}},\"description\":\"Add two integers.\",\"inputSchema\":{\"properties\":{\"a\":{\"type\":\"integer\"},\"b\":{\"type\":\"integer\"}},\"required\":[\"a\",\"b\"],\"type\":\"object\",\"additionalProperties\":false},\"name\":\"add\",\"outputSchema\":{\"properties\":{\"result\":{\"type\":\"integer\"}},\"required\":[\"result\"],\"type\":\"object\",\"x-fastmcp-wrap-result\":true},\"title\":\"Add\"}]}}\n\n","sbn":436},{"t":9,"m":"POST","path":"/mcp","rh":{"accept":"application/json, text/event-stream","content-type":"application/json","mcp-session-id":"223ae1b206344bec917c9a8da5209691","mcp-protocol-version":"2025-11-25"},"st":200,"sh":{"content-type":"text/event-stream","mcp-session-id":"223ae1b206344bec917c9a8da5209691"},"rb":"{\"jsonrpc\":\"2.0\",\"id\":3,\"method\":\"tools/call\",\"params\":{\"name\":\"add\",\"arguments\":{\"a\":2,\"b\":3},\"_meta\":{\"progressToken\":3}}}","rbn":124,"sb":"event: message\ndata: {\"jsonrpc\":\"2.0\",\"id\":3,\"result\":{\"_meta\":{\"fastmcp\":{\"wrap_result\":true}},\"content\":[{\"text\":\"5\",\"type\":\"text\"}],\"isError\":false,\"structuredContent\":{\"result\":5}}}\n\n","sbn":190},{"t":13,"m":"DELETE","path":"/mcp","rh":{"accept":"application/json, text/event-stream","content-type":"application/json","mcp-session-id":"223ae1b206344bec917c9a8da5209691","mcp-protocol-version":"2025-11-25"},"st":200,"sh":{"content-type":"application/json","mcp-session-id":"223ae1b206344bec917c9a8da5209691"},"rb":"","rbn":0,"sb":"","sbn":0}]},"2025-06-18":{"client":"照 2025-06-18 規格手寫的 httpx 客戶端","protocol":"2025-06-18","result":5,"wire":[{"t":17,"m":"POST","path":"/mcp","rh":{"accept":"application/json, text/event-stream","content-type":"application/json"},"st":200,"sh":{"content-type":"text/event-stream","mcp-session-id":"f9d05eee2542450a983896caeca8f3ba"},"rb":"{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"initialize\",\"params\":{\"protocolVersion\":\"2025-06-18\",\"capabilities\":{},\"clientInfo\":{\"name\":\"raw-2025-06-18\",\"version\":\"0\"}}}","rbn":159,"sb":"event: message\ndata: {\"jsonrpc\":\"2.0\",\"id\":1,\"result\":{\"protocolVersion\":\"2025-06-18\",\"capabilities\":{\"logging\":{},\"prompts\":{\"listChanged\":true},\"resources\":{\"subscribe\":false,\"listChanged\":true},\"tools\":{\"listChanged\":true}},\"serverInfo\":{\"name\":\"calc\",\"version\":\"4.0.8\"},\"instructions\":\"A tiny calculator.\"}}\n\n","sbn":316},{"t":19,"m":"POST","path":"/mcp","rh":{"accept":"application/json, text/event-stream","mcp-session-id":"f9d05eee2542450a983896caeca8f3ba","mcp-protocol-version":"2025-06-18","content-type":"application/json"},"st":202,"sh":{"content-type":"application/json","mcp-session-id":"f9d05eee2542450a983896caeca8f3ba"},"rb":"{\"jsonrpc\":\"2.0\",\"method\":\"notifications/initialized\"}","rbn":54,"sb":"","sbn":0},{"t":20,"m":"POST","path":"/mcp","rh":{"accept":"application/json, text/event-stream","mcp-session-id":"f9d05eee2542450a983896caeca8f3ba","mcp-protocol-version":"2025-06-18","content-type":"application/json"},"st":200,"sh":{"content-type":"text/event-stream","mcp-session-id":"f9d05eee2542450a983896caeca8f3ba"},"rb":"{\"jsonrpc\":\"2.0\",\"id\":2,\"method\":\"tools/list\"}","rbn":46,"sb":"event: message\ndata: {\"jsonrpc\":\"2.0\",\"id\":2,\"result\":{\"tools\":[{\"_meta\":{\"fastmcp\":{\"tags\":[]}},\"description\":\"Add two integers.\",\"inputSchema\":{\"properties\":{\"a\":{\"type\":\"integer\"},\"b\":{\"type\":\"integer\"}},\"required\":[\"a\",\"b\"],\"type\":\"object\",\"additionalProperties\":false},\"name\":\"add\",\"outputSchema\":{\"properties\":{\"result\":{\"type\":\"integer\"}},\"required\":[\"result\"],\"type\":\"object\",\"x-fastmcp-wrap-result\":true},\"title\":\"Add\"}]}}\n\n","sbn":436},{"t":21,"m":"POST","path":"/mcp","rh":{"accept":"application/json, text/event-stream","mcp-session-id":"f9d05eee2542450a983896caeca8f3ba","mcp-protocol-version":"2025-06-18","content-type":"application/json"},"st":200,"sh":{"content-type":"text/event-stream","mcp-session-id":"f9d05eee2542450a983896caeca8f3ba"},"rb":"{\"jsonrpc\":\"2.0\",\"id\":3,\"method\":\"tools/call\",\"params\":{\"name\":\"add\",\"arguments\":{\"a\":2,\"b\":3}}}","rbn":96,"sb":"event: message\ndata: {\"jsonrpc\":\"2.0\",\"id\":3,\"result\":{\"_meta\":{\"fastmcp\":{\"wrap_result\":true}},\"content\":[{\"text\":\"5\",\"type\":\"text\"}],\"isError\":false,\"structuredContent\":{\"result\":5}}}\n\n","sbn":190},{"t":23,"m":"DELETE","path":"/mcp","rh":{"accept":"application/json, text/event-stream","mcp-session-id":"f9d05eee2542450a983896caeca8f3ba","mcp-protocol-version":"2025-06-18"},"st":200,"sh":{"content-type":"application/json","mcp-session-id":"f9d05eee2542450a983896caeca8f3ba"},"rb":"","rbn":0,"sb":"","sbn":0}]},"2025-03-26":{"client":"照 2025-03-26 規格手寫的 httpx 客戶端","protocol":"2025-03-26","result":5,"wire":[{"t":5,"m":"POST","path":"/mcp","rh":{"accept":"application/json, text/event-stream","content-type":"application/json"},"st":200,"sh":{"content-type":"text/event-stream","mcp-session-id":"88fe8cafdb92436f92d078684882266d"},"rb":"{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"initialize\",\"params\":{\"protocolVersion\":\"2025-03-26\",\"capabilities\":{},\"clientInfo\":{\"name\":\"raw-2025-03-26\",\"version\":\"0\"}}}","rbn":159,"sb":"event: message\ndata: {\"jsonrpc\":\"2.0\",\"id\":1,\"result\":{\"protocolVersion\":\"2025-03-26\",\"capabilities\":{\"logging\":{},\"prompts\":{\"listChanged\":true},\"resources\":{\"subscribe\":false,\"listChanged\":true},\"tools\":{\"listChanged\":true}},\"serverInfo\":{\"name\":\"calc\",\"version\":\"4.0.8\"},\"instructions\":\"A tiny calculator.\"}}\n\n","sbn":316},{"t":7,"m":"POST","path":"/mcp","rh":{"accept":"application/json, text/event-stream","mcp-session-id":"88fe8cafdb92436f92d078684882266d","content-type":"application/json"},"st":202,"sh":{"content-type":"application/json","mcp-session-id":"88fe8cafdb92436f92d078684882266d"},"rb":"{\"jsonrpc\":\"2.0\",\"method\":\"notifications/initialized\"}","rbn":54,"sb":"","sbn":0},{"t":7,"m":"POST","path":"/mcp","rh":{"accept":"application/json, text/event-stream","mcp-session-id":"88fe8cafdb92436f92d078684882266d","content-type":"application/json"},"st":200,"sh":{"content-type":"text/event-stream","mcp-session-id":"88fe8cafdb92436f92d078684882266d"},"rb":"{\"jsonrpc\":\"2.0\",\"id\":2,\"method\":\"tools/list\"}","rbn":46,"sb":"event: message\ndata: {\"jsonrpc\":\"2.0\",\"id\":2,\"result\":{\"tools\":[{\"_meta\":{\"fastmcp\":{\"tags\":[]}},\"description\":\"Add two integers.\",\"inputSchema\":{\"properties\":{\"a\":{\"type\":\"integer\"},\"b\":{\"type\":\"integer\"}},\"required\":[\"a\",\"b\"],\"type\":\"object\",\"additionalProperties\":false},\"name\":\"add\",\"outputSchema\":{\"properties\":{\"result\":{\"type\":\"integer\"}},\"required\":[\"result\"],\"type\":\"object\",\"x-fastmcp-wrap-result\":true},\"title\":\"Add\"}]}}\n\n","sbn":436},{"t":8,"m":"POST","path":"/mcp","rh":{"accept":"application/json, text/event-stream","mcp-session-id":"88fe8cafdb92436f92d078684882266d","content-type":"application/json"},"st":200,"sh":{"content-type":"text/event-stream","mcp-session-id":"88fe8cafdb92436f92d078684882266d"},"rb":"{\"jsonrpc\":\"2.0\",\"id\":3,\"method\":\"tools/call\",\"params\":{\"name\":\"add\",\"arguments\":{\"a\":2,\"b\":3}}}","rbn":96,"sb":"event: message\ndata: {\"jsonrpc\":\"2.0\",\"id\":3,\"result\":{\"_meta\":{\"fastmcp\":{\"wrap_result\":true}},\"content\":[{\"text\":\"5\",\"type\":\"text\"}],\"isError\":false,\"structuredContent\":{\"result\":5}}}\n\n","sbn":190},{"t":10,"m":"DELETE","path":"/mcp","rh":{"accept":"application/json, text/event-stream","mcp-session-id":"88fe8cafdb92436f92d078684882266d"},"st":200,"sh":{"content-type":"application/json","mcp-session-id":"88fe8cafdb92436f92d078684882266d"},"rb":"","rbn":0,"sb":"","sbn":0}]},"2024-11-05":{"client":"照 2024-11-05 規格手寫的 HTTP+SSE 客戶端（伺服器：http_app(transport=\"sse\")）","protocol":"2024-11-05","result":5,"wire":[{"t":5,"m":"GET","path":"/sse","rh":{"accept":"text/event-stream"},"st":200,"sh":{},"rb":"","rbn":0,"sb":"event: endpoint\ndata: /messages/?session_id=c669d903542440d9a943ddb6d8d98a14\n\nevent: message\ndata: {\"jsonrpc\":\"2.0\",\"id\":1,\"result\":{\"protocolVersion\":\"2024-11-05\",\"capabilities\":{\"logging\":{},\"prompts\":{\"listChanged\":true},\"resources\":{\"subscribe\":false,\"listChanged\":true},\"tools\":{\"listChanged\":true}},\"serverInfo\":{\"name\":\"calc\",\"version\":\"4.0.8\"},\"instructions\":\"A tiny calculator.\"}}\n\nevent: message\ndata: {\"jsonrpc\":\"2.0\",\"id\":2,\"result\":{\"tools\":[{\"_meta\":{\"fastmcp\":{\"tags\":[]}},\"description\":\"Add two integers.\",\"inputSchema\":{\"properties\":{\"a\":{\"type\":\"integer\"},\"b\":{\"type\":\"integer\"}},\"required\":[\"a\",\"b\"],\"type\":\"object\",\"additionalProperties\":false},\"name\":\"add\",\"outputSchema\":{\"properties\":{\"result\":{\"type\":\"integer\"}},\"required\":[\"result\"],\"type\":\"object\",\"x-fastmcp-wrap-result\":true},\"title\":\"Add\"}]}}\n\nevent: message\ndata: {\"jsonrpc\":\"2.0\",\"id\":3,\"result\":{\"_meta\":{\"fastmcp\":{\"wrap_result\":true}},\"content\":[{\"text\":\"5\",\"type\":\"text\"}],\"isError\":false,\"structuredContent\":{\"result\":5}}}\n\n","sbn":1023},{"t":54,"m":"POST","path":"/messages/?session_id=c669d903542440d9a943ddb6d8d98a14","rh":{"accept":"*/*","content-type":"application/json"},"st":202,"sh":{},"rb":"{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"initialize\",\"params\":{\"protocolVersion\":\"2024-11-05\",\"capabilities\":{},\"clientInfo\":{\"name\":\"raw-2024-11-05\",\"version\":\"0\"}}}","rbn":159,"sb":"Accepted","sbn":8},{"t":206,"m":"POST","path":"/messages/?session_id=c669d903542440d9a943ddb6d8d98a14","rh":{"accept":"*/*","content-type":"application/json"},"st":202,"sh":{},"rb":"{\"jsonrpc\":\"2.0\",\"method\":\"notifications/initialized\"}","rbn":54,"sb":"Accepted","sbn":8},{"t":357,"m":"POST","path":"/messages/?session_id=c669d903542440d9a943ddb6d8d98a14","rh":{"accept":"*/*","content-type":"application/json"},"st":202,"sh":{},"rb":"{\"jsonrpc\":\"2.0\",\"id\":2,\"method\":\"tools/list\"}","rbn":46,"sb":"Accepted","sbn":8},{"t":508,"m":"POST","path":"/messages/?session_id=c669d903542440d9a943ddb6d8d98a14","rh":{"accept":"*/*","content-type":"application/json"},"st":202,"sh":{},"rb":"{\"jsonrpc\":\"2.0\",\"id\":3,\"method\":\"tools/call\",\"params\":{\"name\":\"add\",\"arguments\":{\"a\":2,\"b\":3}}}","rbn":96,"sb":"Accepted","sbn":8}]}}/*ERAS_END*/;
  const ORDER = ["2024-11-05", "2025-03-26", "2025-06-18", "2025-11-25", "2026-07-28"];
  const INFO = {
    "2024-11-05": { c: "#8172B2", t: "第一版：HTTP+SSE", d: "先開一條 GET 長連線；之後每個 POST 都只回 202，答案全從那條長連線流回來。" },
    "2025-03-26": { c: "#DD8452", t: "Streamable HTTP＋session", d: "單一端點 /mcp。握手（initialize）換到一把 mcp-session-id，之後每發都得帶著它。" },
    "2025-06-18": { c: "#DD8452", t: "多了版本 header", d: "線路形狀同上一版，但握手後的每一發都要帶 MCP-Protocol-Version。" },
    "2025-11-25": { c: "#DD8452", t: "握手年代的最後一版", d: "線路形狀不變（新東西在 tasks、URL elicitation 這些功能）。FastMCP 客戶端還多開一條 GET 長連線收通知。" },
    "2026-07-28": { c: "#4C72B0", t: "無狀態（現行版）", d: "沒有握手、沒有 session、沒有長連線。每一發都自帶 _meta 信封，header 還鏡射了 method 與工具名。" },
  };
  const pills = document.getElementById("era-pills");
  const cap = document.getElementById("era-cap");
  const rows = document.getElementById("era-rows");
  const sum = document.getElementById("era-sum");
  const prev = document.getElementById("era-prev");
  const next = document.getElementById("era-next");
  const demo = document.getElementById("era-demo");
  if (!pills || !ERAS[ORDER[0]]) return;
  let cur = 0, open = -1;
  const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;");
  function j(s) { if (!s || s[0] !== "{") return null; try { return JSON.parse(s); } catch (e) { return null; } }
  function sse(s) {
    return (s || "").split("\n").filter((l) => l.startsWith("data:")).map((l) => l.slice(5).trim())
      .map((d) => j(d) || d);
  }
  function pretty(s) {
    if (!s) return "（空）";
    const o = j(s);
    if (o) return JSON.stringify(o, null, 2);
    if (s.includes("data:")) {
      return s.split("\n\n").filter((b) => b.includes("data:")).map((b) => {
        const ev = (b.match(/event:\s*(.*)/) || [])[1] || "";
        const d = (b.match(/data:\s*(.*)/) || [])[1] || "";
        const o2 = j(d);
        return "event: " + ev + "\n" + (o2 ? JSON.stringify(o2, null, 2) : d);
      }).join("\n\n");
    }
    return s;
  }
  function label(e) {
    if (e.rh["mcp-method"]) return e.rh["mcp-method"] + (e.rh["mcp-name"] ? " " + e.rh["mcp-name"] : "");
    const o = j(e.rb);
    if (o && o.method) return o.method + (o.method === "tools/call" && o.params ? " " + o.params.name : "");
    if (e.m === "GET") return e.path.startsWith("/sse") ? "開一條 SSE 長連線" : "開一條長連線收通知";
    if (e.m === "DELETE") return "結束 session";
    return "";
  }
  const hasSid = (e) => "mcp-session-id" in e.rh || e.path.includes("session_id=");
  const hasMeta = (e) => { const o = j(e.rb); return !!(o && o.params && o.params._meta && o.params._meta["io.modelcontextprotocol/protocolVersion"]); };
  function hdrs(h) {
    const ks = Object.keys(h);
    return ks.length ? ks.map((k) => k + ": " + h[k]).join("\n") : "（無關鍵 header）";
  }
  function render() {
    const v = ORDER[cur], era = ERAS[v], info = INFO[v];
    demo.style.setProperty("--ec", info.c);
    pills.querySelectorAll(".pill").forEach((p, i) => p.classList.toggle("on", i === cur));
    cap.innerHTML = "<b>" + v + "｜" + esc(info.t) + "</b><div>" + esc(info.d) + "</div><div class='who'>客戶端：" + esc(era.client) + "</div>";
    rows.innerHTML = "";
    era.wire.forEach((e, i) => {
      const b = document.createElement("button");
      b.type = "button";
      b.className = "row" + (i === open ? " open" : "");
      b.style.animationDelay = (i * 60) + "ms";
      const bad = e.st >= 400;
      b.innerHTML = "<span class='no'>#" + (i + 1) + "</span><span class='verb'>" + esc(e.m) + "</span>" +
        "<span class='what'>" + esc(label(e)) + "</span>" +
        (hasSid(e) ? "<span class='tag sid'>session</span>" : "") +
        ("mcp-session-id" in e.sh && !("mcp-session-id" in e.rh) ? "<span class='tag sid'>發 session</span>" : "") +
        (hasMeta(e) ? "<span class='tag meta'>_meta</span>" : "") +
        (e.st === 202 ? "<span class='tag acc'>202 答案不在這</span>" : "") +
        "<span class='tag st" + (bad ? " bad" : "") + "'>" + e.st + "</span>";
      b.addEventListener("click", () => { open = (open === i ? -1 : i); render(); });
      rows.appendChild(b);
      if (i === open) {
        const d = document.createElement("div");
        d.className = "detail";
        d.innerHTML = "<div class='lab'>▶ 請求 " + esc(e.m + " " + e.path) + "</div><pre>" + esc(hdrs(e.rh)) + "</pre>" +
          "<pre>" + esc(pretty(e.rb)) + "</pre>" +
          "<div class='lab'>◀ 回應 " + e.st + "（" + e.sbn + " bytes）</div><pre>" + esc(hdrs(e.sh)) + "</pre>" +
          "<pre>" + esc(pretty(e.sb)) + "</pre>";
        rows.appendChild(d);
      }
    });
    const n = era.wire.length, sid = era.wire.filter(hasSid).length;
    const bytes = era.wire.reduce((a, e) => a + e.rbn + e.sbn, 0);
    sum.innerHTML = n + " 發 HTTP 請求｜" + (sid ? "<span style='color:var(--cut)'>" + sid + " 發帶著 session</span>" : "<span style='color:var(--c1)'>0 發帶 session</span>") +
      "｜body 共 " + bytes.toLocaleString() + " bytes｜add(2, 3) = " + esc(era.result);
    prev.disabled = cur === 0;
    next.disabled = cur === ORDER.length - 1;
  }
  ORDER.forEach((v, i) => {
    const p = document.createElement("button");
    p.type = "button";
    p.className = "pill";
    p.textContent = v;
    p.addEventListener("click", () => { cur = i; open = -1; render(); });
    pills.appendChild(p);
  });
  prev.addEventListener("click", () => { if (cur > 0) { cur--; open = -1; render(); } });
  next.addEventListener("click", () => { if (cur < ORDER.length - 1) { cur++; open = -1; render(); } });
  render();
})();
"""
