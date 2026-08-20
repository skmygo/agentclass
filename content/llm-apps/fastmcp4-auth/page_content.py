"""課程頁內容區（純常數）。改完跑：python3 .claude/skills/make-lesson/scripts/page-fill.py content/llm-apps/fastmcp4-auth
build.sh 不會部署這個檔；它是 index.html 內容區的正本。"""

TITLE = "FastMCP 4 認證：從一把 token 到完整 OAuth 2.1"
DESCRIPTION = "FastMCP 4 的認證與授權：StaticTokenVerifier、get_access_token、require_scopes 讓工具隱形、UserSession、本機簽發 JWT，並在 notebook 裡起一台真的 OAuth 2.1 授權伺服器，用裸 HTTP 走完 discovery → 動態註冊 → PKCE → 換 token 六步。"
NB = "https://molab.marimo.io/github/skmygo/agentclass/blob/main/content/llm-apps/fastmcp4-auth/fastmcp4-auth_ext.py"

STYLE = r"""
  /* 語義色：綠＝通過（200／有權限）、紅＝拒絕（401／隱形）、藍＝授權伺服器端點、橘＝客戶端動作 */
  :root { --c1: #55A868; --c2: #C44E52; --c3: #4C72B0; --c4: #DD8452; --cut: #C44E52; }
  a.golab { text-decoration: none; display: inline-flex; align-items: center; gap: 8px; }

  /* hero：選 token → 呼叫 close_shop → 重播實測請求序列 */
  #au-demo .row { display: flex; gap: 10px; flex-wrap: wrap; align-items: center; margin-bottom: 12px; }
  #au-demo button { font: inherit; font-size: 13.5px; padding: 7px 14px; border: 2px solid var(--ink); border-radius: 10px; background: var(--ink); color: #fff; font-weight: 800; cursor: pointer; }
  #au-demo .toks { display: flex; gap: 6px; flex-wrap: wrap; }
  #au-demo .tok { font: inherit; font-family: var(--mono); font-size: 12px; padding: 5px 10px; border: 1.5px solid var(--grid); border-radius: 8px; background: var(--panel); color: var(--ink); font-weight: 600; cursor: pointer; }
  #au-demo .tok.on { border-color: var(--ink); background: var(--chip-bg); font-weight: 800; }
  #au-demo .reqs { display: flex; flex-direction: column; gap: 6px; min-height: 150px; }
  #au-demo .req { display: grid; grid-template-columns: 1fr auto; gap: 10px; align-items: center; font-family: var(--mono); font-size: 12px; padding: 6px 10px; border-radius: 8px; background: var(--chip-bg); opacity: .2; transition: opacity .2s, transform .2s; }
  #au-demo .req.on { opacity: 1; transform: translateX(2px); }
  #au-demo .req .resp { font-weight: 800; padding: 1px 8px; border-radius: 6px; color: #fff; }
  #au-demo .req .ok { background: var(--c1); } #au-demo .req .no { background: var(--c2); } #au-demo .req .info { background: var(--c3); }
  #au-demo .verdict { margin-top: 10px; font-size: 13.5px; font-weight: 800; min-height: 20px; }

  table.cmp { width: 100%; border-collapse: collapse; font-size: 13.5px; margin: 14px 0; }
  table.cmp th, table.cmp td { border-bottom: 1px solid var(--grid); padding: 8px 10px; text-align: left; vertical-align: top; }
  table.cmp th { font-size: 12px; letter-spacing: .04em; color: var(--ink-soft); }
  .kbd { font-family: var(--mono); background: var(--chip-bg); padding: 1px 6px; border-radius: 5px; font-size: 13px; }
  ol.flow { counter-reset: step; list-style: none; padding: 0; margin: 14px 0; }
  ol.flow li { position: relative; padding: 8px 0 8px 38px; border-left: 2px solid var(--grid); margin-left: 12px; font-size: 14px; }
  ol.flow li::before { counter-increment: step; content: counter(step); position: absolute; left: -13px; top: 8px; width: 24px; height: 24px; border-radius: 50%; background: var(--c3); color: #fff; font-family: var(--mono); font-size: 12px; font-weight: 800; display: flex; align-items: center; justify-content: center; }
  ol.flow li:first-child::before { counter-increment: step 0; content: "0"; background: var(--c2); }
  ol.flow li b.ep { font-family: var(--mono); font-weight: 700; font-size: 12.5px; color: var(--c3); }
"""

WRAP = r'''
<section id="hero">
  <span class="eyebrow">FASTMCP 4 · 補充 A · AUTHENTICATION &amp; AUTHORIZATION</span>
  <h1>FastMCP 4 認證：從一把 token 到完整 OAuth 2.1</h1>
  <p style="margin-top:18px">
    第 3 課的茶飲店誰都能連。放到公網、或者工具會動到真的資料，你需要三件事：<b>知道是誰在呼叫</b>、<b>決定他能做什麼</b>、
    讓 Claude Desktop／Cursor 這類客戶端<b>自己完成登入</b>。FastMCP 4 把三層都做成 <span class="kbd">auth=</span> 一行。
    先感受一下「同一個工具、四把 token」——
  </p>

  <div class="hero-demo" id="au-demo">
    <div class="row">
      <div class="toks">
        <button class="tok" data-k="none">（不帶 token）</button>
        <button class="tok on" data-k="guest">guest-token · read</button>
        <button class="tok" data-k="alice">alice-token · read write admin</button>
        <button class="tok" data-k="expired">過期的 JWT</button>
      </div>
      <button id="au-play">▶ 呼叫 close_shop</button>
    </div>
    <div class="reqs" id="au-reqs"></div>
    <div class="verdict" id="au-verdict"></div>
  </div>

  <p class="note">
    上面每一列都是 notebook 的實測紀錄：它在 molab 裡<b>真的起伺服器、真的簽 JWT、真的跑 OAuth</b>，不連任何外部服務、不需要任何帳號。
    本課與第 3 課同版本：<span class="kbd">fastmcp==4.0.0b1</span>。
  </p>
</section>

<section id="s1">
  <span class="eyebrow">01 · 認證</span>
  <h2>一把 token，三個概念：誰、能做什麼、掛在哪</h2>
  <div class="codeblock">from fastmcp.server.auth.providers.jwt import StaticTokenVerifier

counter = FastMCP("會員櫃台", auth=StaticTokenVerifier(tokens={
    "alice-token": {"client_id": "alice", "scopes": ["read", "write", "admin"]},
    "guest-token": {"client_id": "guest", "scopes": ["read"]},
}))

# 客戶端：給一個字串，FastMCP 自動加 Authorization: Bearer …
async with Client(url, auth="alice-token") as c: ...</div>
  <p>
    <span class="kbd">StaticTokenVerifier</span> 只適合開發教學（token 明文），但它把認證攤得最清楚：
    不帶 token 敲門 → <b>401</b> ＋ <span class="kbd">WWW-Authenticate: Bearer</span>；帶一把亂掰的 → 同樣 401、只說 <span class="kbd">invalid_token</span>，
    <b>不會告訴你是不存在還是過期</b>（真正原因只進伺服器 log）。工具裡隨時 <span class="kbd">get_access_token()</span>
    就拿得到 <span class="kbd">client_id</span>／<span class="kbd">scopes</span>／<span class="kbd">claims</span>——個人化與稽核的起點。
  </p>
  <a class="golab" href="__NB__" target="_blank" rel="noopener">到 notebook 的 1️⃣–2️⃣ 節：401 長什麼樣、工具裡知道你是誰</a>
</section>

<section id="s2">
  <span class="eyebrow">02 · 授權</span>
  <h2>沒權限的工具不是 403，是隱形</h2>
  <div class="codeblock">@counter.tool(auth=require_scopes("admin"))
def close_shop() -> str:
    return "已打烊"

@counter.tool
async def remember(fact: str, session: UserSession) -> list[str]:   # 有身分 → 每人一個狀態桶
    facts = await session.get("facts", default=[]); facts.append(fact)
    await session.set("facts", facts); return facts</div>
  <table class="cmp">
    <tr><th>token</th><th><span class="kbd">list_tools()</span></th><th><span class="kbd">call_tool("close_shop")</span></th></tr>
    <tr><td>alice（read write admin）</td><td>close_shop, remember, whoami</td><td>✅ 已打烊</td></tr>
    <tr><td>guest（read）</td><td>remember, whoami</td><td>🛑 <span class="kbd">Unknown tool: 'close_shop'</span></td></tr>
  </table>
  <p>
    對沒權限的人來說那個工具<b>不存在</b>——模型看不到就不會一直撞 403。多個 scope 是 AND；要改成「明確拒絕並說缺哪個 scope」用伺服器層的
    <span class="kbd">AuthMiddleware</span>（4.0 的 <span class="kbd">InsufficientScopeError</span>，挑戰 LEVEL 2）。
    第 3 課留的伏筆也在這裡兌現：<span class="kbd">session: UserSession</span> 自動注入、不進 schema、不用傳任何鑰匙，
    alice 記兩件、guest 記一件，各拿各的；沒有身分時 FastMCP <b>明確報錯</b>而不是默默開匿名桶。
  </p>
  <a class="golab" href="__NB__" target="_blank" rel="noopener">到 notebook 的 3️⃣–4️⃣ 節：隱形的工具、每人一個桶</a>
</section>

<section id="s3">
  <span class="eyebrow">03 · JWT</span>
  <h2>簽發與驗章分開：伺服器只拿公鑰</h2>
  <div class="codeblock">sso = RSAKeyPair.generate()                       # 迷你 SSO：私鑰簽發（本課全程本機）
auth = JWTVerifier(public_key=sso.public_key,     # 正式環境：jwks_uri="https://你的SSO/.well-known/jwks.json"
                   issuer="https://sso.example.com", audience="tea-shop")
token = sso.create_token(subject="alice", issuer=..., audience="tea-shop", scopes=["read", "write"])</div>
  <p>
    JWT 三段 base64：header（<span class="kbd">RS256</span>）、payload（<span class="kbd">sub</span>／<span class="kbd">iss</span>／<span class="kbd">aud</span>／<span class="kbd">exp</span>／<span class="kbd">scope</span>，
    <b>不是加密，任何人都能解開看</b>）、簽章（沒私鑰做不出來）。三種壞 token——audience 給別的 app、簽出來就過期、別組金鑰偽造的 admin——
    線路上長得一模一樣：<b>401 invalid_token</b>。<span class="kbd">issuer</span>／<span class="kbd">audience</span> 是兩道必檢：同一家 SSO 發給別的 app 的 token 在這裡無效。
  </p>
  <a class="golab" href="__NB__" target="_blank" rel="noopener">到 notebook 的 5️⃣ 節：拆開 JWT、三種壞 token</a>
</section>

<section id="s4">
  <span class="eyebrow">04 · OAUTH 2.1</span>
  <h2>六步走完授權碼流程，每一步都是裸 HTTP</h2>
  <p>
    真實的 MCP 客戶端期待的是：連上去被拒 → 自己找到授權伺服器 → 自己註冊 → 跳瀏覽器讓使用者同意 → 自己換 token。
    notebook 用 FastMCP 內建的 <span class="kbd">InMemoryOAuthProvider</span>（完整的 OAuth 2.1 授權伺服器，只是自動按下「同意」）跟 MCP 伺服器掛同一個 port，然後用 <span class="kbd">httpx</span> 一步一步走：
  </p>
  <ol class="flow">
    <li><b class="ep">POST /mcp</b> 不帶 token → <b>401</b>，<span class="kbd">WWW-Authenticate: Bearer resource_metadata="…/.well-known/oauth-protected-resource/mcp"</span>——告訴你去哪裡問</li>
    <li><b class="ep">GET /.well-known/oauth-protected-resource/mcp</b> → 這個資源信任哪些授權伺服器、支援哪些 scope</li>
    <li><b class="ep">GET /.well-known/oauth-authorization-server</b> → <span class="kbd">authorization_endpoint</span>／<span class="kbd">token_endpoint</span>／<span class="kbd">registration_endpoint</span>、PKCE 支援 <span class="kbd">S256</span></li>
    <li><b class="ep">POST /register</b>（動態註冊 DCR，RFC 7591）→ 當場拿 <span class="kbd">client_id</span>；公開客戶端沒有 secret，安全交給 PKCE</li>
    <li><b class="ep">GET /authorize?code_challenge=SHA256(verifier)&amp;state=…</b> → <b>302</b> 回 redirect_uri，query 帶一次性的 <span class="kbd">code</span> 與原封不動的 <span class="kbd">state</span></li>
    <li><b class="ep">POST /token</b>（code ＋ <span class="kbd">code_verifier</span> 原文）→ <span class="kbd">access_token</span>、<span class="kbd">expires_in</span>、<span class="kbd">refresh_token</span></li>
    <li><b class="ep">POST /mcp</b> 帶 Bearer → ✅。反例：新 code 配錯的 verifier → <span class="kbd">invalid_grant: incorrect code_verifier</span>；用過的 code 再換 → <span class="kbd">authorization code does not exist</span></li>
  </ol>
  <p>
    SDK 三行版 <span class="kbd">Client(url, auth=OAuth())</span>（或 <span class="kbd">auth="oauth"</span>）全包上面六步：discovery、註冊、開瀏覽器、本機收 callback、換 token、到期自動 refresh。
    molab 沒瀏覽器，notebook 示範覆寫 <span class="kbd">redirect_handler</span>／<span class="kbd">callback_handler</span> 兩個方法無頭跑完——在你自己電腦上不用覆寫。
  </p>
  <a class="golab" href="__NB__" target="_blank" rel="noopener">到 notebook 的 6️⃣–7️⃣ 節：六步裸 HTTP、SDK 三行版</a>
</section>

<section id="s5">
  <span class="eyebrow">05 · 上線</span>
  <h2>接真的供應商：只有 auth= 那一行不同</h2>
  <div class="codeblock"># 沒有 DCR 的供應商（GitHub / Google / Azure / 多數企業 SSO）：OAuthProxy 家族
auth = GitHubProvider(client_id=..., client_secret=..., base_url="https://your-server.example.com")
# 有 DCR 的身分平台（WorkOS AuthKit / Descope / Keycloak）：RemoteAuthProvider 家族
auth = AuthKitProvider(authkit_domain="https://your-project.authkit.app", base_url=...)
# 沒有人在鍵盤前的客戶端（排程、CI、伺服器對伺服器）：client credentials，不開瀏覽器
Client(url, auth=ClientCredentialsOAuthProvider(client_id=..., client_secret=..., scopes=[...]))</div>
  <table class="cmp">
    <tr><th>情境</th><th>用</th></tr>
    <tr><td>開發、測試、教學</td><td><span class="kbd">StaticTokenVerifier</span>／<span class="kbd">InMemoryOAuthProvider</span></td></tr>
    <tr><td>公司已有 SSO 發 JWT</td><td><span class="kbd">JWTVerifier(jwks_uri=...)</span></td></tr>
    <tr><td>讓使用者用 GitHub／Google 登入</td><td><span class="kbd">GitHubProvider</span>／<span class="kbd">GoogleProvider</span>（<span class="kbd">OAuthProxy</span>：對客戶端假裝支援 DCR、對上游用你的固定憑證）</td></tr>
    <tr><td>身分平台支援 DCR</td><td><span class="kbd">AuthKitProvider</span> 等（<span class="kbd">RemoteAuthProvider</span>）</td></tr>
    <tr><td>互動＋機器兩種客戶端並存</td><td><span class="kbd">MultiAuth(server=..., verifiers=[...])</span></td></tr>
    <tr><td>自己當完整授權伺服器</td><td><span class="kbd">OAuthProvider</span> 子類別——除非有不得不的理由</td></tr>
  </table>
  <a class="golab" href="__NB__" target="_blank" rel="noopener">到 notebook 的 8️⃣ 節：決策表與各家 provider 的寫法</a>
</section>

<section id="s6">
  <span class="eyebrow">06 · 實戰</span>
  <h2>換你動手</h2>
  <div class="ex">
    <span class="lv">LEVEL 1</span>
    <p>加一把 <span class="kbd">bob-token</span>（只有 <span class="kbd">write</span>），重跑授權表：bob 看得到哪些工具？<span class="kbd">remember</span> 呢？</p>
  </div>
  <div class="ex">
    <span class="lv">LEVEL 2</span>
    <p>把「隱形」改成「明確拒絕」：<span class="kbd">FastMCP(middleware=[AuthMiddleware(auth=require_scopes("read"))])</span> ＋ 一個要 <span class="kbd">read</span> 與 <span class="kbd">write</span> 的工具，用三把 token 比較清單與錯誤訊息。</p>
  </div>
  <div class="ex">
    <span class="lv">LEVEL 3</span>
    <p>用 <span class="kbd">grant_type=refresh_token</span> 換一組新 token：新的能用嗎？<b>舊的</b>還能用嗎？舊 refresh_token 再用一次會怎樣？</p>
  </div>
  <p style="font-size:13.5px;color:var(--ink-soft)">卡住了？每一題在 notebook 末節都有折疊解答——先自己做，再打開對照。</p>
</section>

<div class="endnav">
  <a href="/fastmcp4-state/">
    <span class="tag">下一課</span>
    <b>FastMCP 4 狀態：無狀態協定上的三種記憶 →</b>
  </a>
  <a href="/llm-apps/">
    <span class="tag">主題</span>
    <b>‹ 回「學 LLM 應用開發」課程列表</b>
  </a>
</div>
'''

SCRIPT = r"""
/* ═══ hero 互動：四把 token 呼叫 close_shop（序列來自 notebook 實測）═══ */
(function () {
  const SEQ = {
    none: [
      { m: "POST /mcp  tools/call close_shop  （沒有 Authorization）", r: "401", k: "no" },
      { m: "← WWW-Authenticate: Bearer", r: "認證挑戰", k: "info" },
    ],
    guest: [
      { m: "POST /mcp  tools/list  Authorization: Bearer guest-token", r: "200", k: "ok" },
      { m: "← [remember, whoami]   （沒有 close_shop）", r: "隱形", k: "info" },
      { m: "POST /mcp  tools/call close_shop", r: "Unknown tool", k: "no" },
    ],
    alice: [
      { m: "POST /mcp  tools/list  Authorization: Bearer alice-token", r: "200", k: "ok" },
      { m: "← [close_shop, remember, whoami]", r: "admin", k: "info" },
      { m: "POST /mcp  tools/call close_shop", r: "\"已打烊\"", k: "ok" },
    ],
    expired: [
      { m: "POST /mcp  tools/call close_shop  Authorization: Bearer eyJ…（exp 已過）", r: "401", k: "no" },
      { m: "← WWW-Authenticate: Bearer error=\"invalid_token\"", r: "只說 invalid", k: "info" },
      { m: "（伺服器 log：token expired —— 線路上不講原因）", r: "log only", k: "info" },
    ],
  };
  const VERDICT = {
    none: "沒有身分：整台伺服器的 HTTP 入口都擋下，連工具清單都拿不到。",
    guest: "有身分、沒 admin scope：close_shop 對 guest 來說不存在——不是 403，是隱形。",
    alice: "有 admin scope：看得到、叫得動。",
    expired: "JWT 簽章對、但 exp 已過：401，且線路上只說 invalid_token，原因留在伺服器 log。",
  };
  let cur = "guest", timers = [];
  const reqs = document.getElementById("au-reqs"), verdict = document.getElementById("au-verdict");
  function build() {
    reqs.innerHTML = SEQ[cur].map(s => `<div class="req"><span>${s.m}</span><span class="resp ${s.k}">${s.r}</span></div>`).join("");
    verdict.textContent = "";
  }
  function play() {
    timers.forEach(clearTimeout); timers = []; build();
    const els = reqs.querySelectorAll(".req");
    els.forEach((el, i) => timers.push(setTimeout(() => { el.classList.add("on"); if (i === els.length - 1) verdict.textContent = VERDICT[cur]; }, 260 * (i + 1))));
  }
  document.querySelectorAll("#au-demo .tok").forEach(b => b.addEventListener("click", () => {
    document.querySelectorAll("#au-demo .tok").forEach(x => x.classList.remove("on"));
    b.classList.add("on"); cur = b.dataset.k; play();
  }));
  document.getElementById("au-play").addEventListener("click", play);
  build();
})();
"""

PANEL_STEPS = """
        <li>登入 molab（GitHub / Google）</li>
        <li>開啟課程 notebook，<b>Fork 成自己的副本</b>即可編輯</li>
        <li>從第一格往下全部執行（首次安裝套件約 1 分鐘）——<b>免費 CPU 環境即可</b>，不需要 GPU、不需要任何外部帳號</li>
"""
