"""課程頁內容區（純常數）。改完跑：python3 .claude/skills/make-lesson/scripts/page-fill.py content/local-llm/prompt-caching
build.sh 不會部署這個檔；它是 index.html 內容區的正本。"""

TITLE = "Prompt Caching：連續對話的錢怎麼算"
DESCRIPTION = "對話歷史只增不改，天然符合快取的前綴條件——舊歷史幾乎不要錢。用可拉桿的計費模型真算一段對話的帳單，看清楚每輪只付三種錢，以及真正貴的其實是讓前綴改變。"

STYLE = r"""
  /* 語義色：綠＝命中（便宜）、橘＝寫入（貴一次）、藍＝輸出（快取管不到）、紅＝完全不用快取 */
  :root { --c1: #4C72B0; --c2: #DD8452; --c3: #55A868; --cut: #C44E52; }

  /* hero：即時計費計算器 */
  #pc-calc .ctrl label { font-size: 13.5px; font-weight: 800; min-width: 138px; }
  #pc-calc .ctrl label b { font-family: var(--mono); }
  #pc-calc .bars { margin-top: 18px; display: grid; gap: 9px; }
  #pc-calc .barrow { display: grid; grid-template-columns: 72px 1fr 88px; align-items: center; gap: 10px; }
  #pc-calc .bl { font-size: 12.5px; font-weight: 800; color: var(--ink-soft); }
  #pc-calc .track { height: 22px; background: var(--chip-bg); border-radius: 6px; overflow: hidden; }
  #pc-calc .fill { height: 100%; width: 0; border-radius: 6px; transition: width .25s ease; }
  #pc-calc .fill.plain { background: var(--cut); }
  #pc-calc .fill.cache { background: var(--c3); }
  #pc-calc .bv { font-family: var(--mono); font-size: 13px; font-weight: 800; text-align: right; }
  #pc-calc .save { font-size: 14.5px; font-weight: 800; margin-top: 14px; line-height: 1.6; }
  #pc-calc .save b { font-size: 21px; }
  #pc-calc .save.bad { color: var(--cut); }
  #pc-calc .strip { margin-top: 16px; border-top: 1px solid var(--grid); padding-top: 12px; }
  #pc-calc .cap { font-size: 11.5px; font-weight: 800; letter-spacing: .05em; color: var(--ink-soft); }
  #pc-calc .striprow { display: flex; align-items: flex-end; gap: 3px; height: 40px; margin: 5px 0 10px; }
  #pc-calc .striprow i { flex: 1; min-width: 3px; border-radius: 2px 2px 0 0; display: block; }
  #pc-calc .fine { font-size: 12.5px; color: var(--ink-soft); margin: 14px 0 0; line-height: 1.7; }

  table.cmp { width: 100%; border-collapse: collapse; font-size: 13.5px; margin: 14px 0; }
  table.cmp th, table.cmp td { border-bottom: 1px solid var(--grid); padding: 8px 10px; text-align: left; vertical-align: top; }
  table.cmp th { font-size: 12px; letter-spacing: .04em; color: var(--ink-soft); }
  table.cmp td.num { font-family: var(--mono); font-weight: 800; text-align: right; white-space: nowrap; }
  table.cmp tr.key td { background: var(--chip-bg); }
  .kbd { font-family: var(--mono); background: var(--chip-bg); padding: 1px 6px; border-radius: 5px; font-size: 13px; }
"""

WRAP = r"""
<section id="hero">
  <span class="eyebrow">BILLING · 04 · 連續對話的帳單</span>
  <h1>Prompt Caching：<br>連續對話的錢怎麼算</h1>
  <p style="margin-top:18px">
    上一課你看懂了 KV Cache：算過的前綴不用再算第二次。這一課換個角度看同一件事——
    那個「不用再算」，在<b>帳單</b>上長什麼樣子。
  </p>
  <p>
    直覺會說：聊越久越貴，因為每一輪都要把越來越長的歷史整段送回去。
    直覺只對了一半。真相是——<b>那段越來越長的歷史，幾乎不要錢</b>。
    拉拉看下面兩根桿子：
  </p>

  <div class="hero-demo" id="pc-calc">
    <div class="ctrl">
      <label for="pc-n">對話輪數 <b id="pc-n-val">3</b></label>
      <input type="range" id="pc-n" min="1" max="20" step="1" value="3">
    </div>
    <div class="ctrl">
      <label for="pc-s">系統提示 <b id="pc-s-val">10K</b></label>
      <input type="range" id="pc-s" min="0" max="40" step="1" value="10">
    </div>

    <div class="bars">
      <div class="barrow">
        <span class="bl">不用快取</span>
        <div class="track"><div class="fill plain" id="pc-bar-plain"></div></div>
        <span class="bv" id="pc-plain">$0.7200</span>
      </div>
      <div class="barrow">
        <span class="bl">用快取</span>
        <div class="track"><div class="fill cache" id="pc-bar-cache"></div></div>
        <span class="bv" id="pc-cache">$0.4915</span>
      </div>
    </div>

    <div class="save" id="pc-save"></div>

    <div class="strip">
      <span class="cap">每一輪要付多少（兩排共用同一把尺）</span>
      <div class="striprow" id="pc-strip-plain"></div>
      <div class="striprow" id="pc-strip-cache"></div>
      <span class="cap" id="pc-strip-note">上排紅＝不用快取，越聊越貴　　下排綠＝用快取，趨於固定</span>
    </div>

    <p class="fine">
      每一輪固定問 1K、答 2K tokens。費率以官方公開定價的其中一組為例
      （命中 $1、寫入 $12.5、輸出 $50，每百萬 tokens）；價格會調整，實際以官方定價頁為準。
    </p>
  </div>

  <p class="note">
    右邊的實驗場是真的 Python（在你的瀏覽器裡跑，不用安裝任何東西）。
    首次載入約需 30–60 秒，正好夠你讀完第 1 節。這一課沒有任何網路呼叫——
    每一筆金額都是照費率一筆一筆算出來的，所以你可以把費率換成自己方案的數字重算。
  </p>
</section>

<section id="s1">
  <span class="eyebrow">01 · 從延遲到帳單</span>
  <h2>同一件事的兩張臉</h2>
  <p>
    上一課的重點是延遲：<b>TTFT</b>（第一個字多久蹦出來）大約等於「Prefill 時間 ＋ 首 token 生成」。
    prompt 越長，Prefill 越久，第一個字就越慢。開啟 Prefix Caching 之後，
    相同前綴的 KV 直接重用、跳過重複的 Prefill，TTFT 因此大幅下降——共用前綴越長，效果越明顯。
  </p>
  <p>
    這一課看的是同一個「跳過」的另一張臉：<b>被跳過的那段 input，收費也跟著跳水</b>。
    供應商不必重算它，所以按更便宜的價目收——這就是連續對話能省錢的全部祕密。
  </p>
  <p>
    但「相同前綴」四個字很嚴格：它是逐位元組比對，<b>前面任何一個字元變了，後面全部作廢</b>。
    請求的組裝順序是<b>工具定義 → 系統提示 → 對話訊息</b>，越前面的東西一改，波及範圍越大。
    最經典的反例：早年有服務把「今天日期」寫進系統提示的最前面——
    前綴每天（甚至每次請求）都不一樣，快取形同虛設，錢白白多付。
    會變的東西（時間戳、隨機 ID、這次才問的問題）要排在後面，不是前面。
  </p>
  <button class="golab" data-nb="1️⃣">到右邊看費率表：五種價錢長什麼樣</button>
</section>

<section id="s2">
  <span class="eyebrow">02 · 三種錢</span>
  <h2>連續對話，每一輪只付三種錢</h2>
  <p>
    先看價目。連續對話會用到的只有五種，而其中<b>兩個比值決定一切</b>：
  </p>
  <table class="cmp">
    <tr><th>項目</th><th style="text-align:right">每百萬 tokens</th><th>什麼時候付</th></tr>
    <tr><td>Base Input</td><td class="num">$10</td><td>沒被快取的一般輸入</td></tr>
    <tr><td>Cache Write（5 分鐘）</td><td class="num">$12.50</td><td>新內容第一次寫入快取</td></tr>
    <tr><td>Cache Write（1 小時）</td><td class="num">$20</td><td>改用長 TTL 時的寫入</td></tr>
    <tr class="key"><td><b>Cache Hit</b></td><td class="num">$1</td><td>重複讀取已快取的內容</td></tr>
    <tr><td>Output</td><td class="num">$50</td><td>模型產生的回答</td></tr>
  </table>
  <p>
    <b>命中只要一般輸入的 1/10</b>；而寫入比一般輸入貴 25%——貴的那一次，會被之後每一次命中賺回來。
  </p>
  <p>
    有了這張表，連續對話的規則只剩三行：
  </p>
  <table class="cmp">
    <tr><th>這一輪送出去的東西</th><th>走哪一種價</th><th>為什麼</th></tr>
    <tr><td><b>舊內容</b>：之前所有對話歷史</td><td class="num" style="color:var(--c3)">$1</td><td>上一輪已經寫進快取了，直接命中</td></tr>
    <tr><td><b>新內容</b>：這一輪新增的問題</td><td class="num" style="color:var(--c2)">$12.50</td><td>第一次出現，要付寫入</td></tr>
    <tr><td><b>輸出</b>：模型的回答</td><td class="num" style="color:var(--c1)">$50</td><td>跟快取無關，照常計費</td></tr>
  </table>
  <p>
    關鍵在為什麼「舊內容一定命中」：<b>對話歷史只增不改</b>。
    每一輪都是在上一輪後面接東西，前面那一大段一個字都沒動——
    這正好就是「共用前綴」的定義。所以連續對話<b>天然</b>吃得到快取，你什麼設定都不用做。
  </p>
  <p>
    把教材裡的經典情境（系統提示 10K、每輪問 1K、答 2K）算三輪，會長這樣：
  </p>
  <div class="codeblock">第 1 輪  寫入 11K → $0.1375   輸出 2K → $0.100   小計 $0.2375   ← 什麼都還沒快取
第 2 輪  命中 13K → $0.013    寫入 1K → $0.0125  輸出 2K → $0.100   小計 $0.1255   ← 歷史 13K 只花 1 分錢
第 3 輪  命中 16K → $0.016    寫入 1K → $0.0125  輸出 2K → $0.100   小計 $0.1285   ← 每輪成本趨於固定

三輪總計  $0.4915     同一段對話不用快取要  $0.7200     省 32%</div>
  <p>
    第 2 輪和第 3 輪的小計幾乎一樣，這是快取最舒服的地方：<b>聊得再久，下一輪要花多少你都猜得到。</b>
  </p>
  <button class="golab" data-nb="2️⃣">到右邊看這張帳單怎麼被算出來</button>
</section>

<section id="s3">
  <span class="eyebrow">03 · 越聊越省</span>
  <h2>省多少？拉三根桿子就知道</h2>
  <p>
    三輪省 32% 只是一個點。右邊的三根拉桿（系統提示長度、輪數、回答長度）會把兩條累計成本曲線畫出來，
    先猜再拉，看你的直覺準不準。三個方向的答案是：
  </p>
  <ul>
    <li><b>輪數是最猛的變數</b>：3 輪省 32%、10 輪省 57%、20 輪省 68%。
      因為每多一輪，就多一份「被重複計價的歷史」被快取吃掉。</li>
    <li><b>系統提示越長越省，但影響小得多</b>：聊 3 輪時，2K 的系統提示省 22%、40K 省 43%；
      可是只要聊到 20 輪，2K 和 40K 都落在 65–74% 之間。它畢竟只是一段固定長度的前綴。</li>
    <li><b>回答拉長反而讓比例縮水</b>：輸出那 $50/MTok 不受快取影響。
      <b>快取省的是 input，不是 output。</b></li>
  </ul>
  <p>
    還有一個反直覺的角落值得你親手拉一次：把輪數拉到 <b>1</b>。
    畫面會告訴你「反而貴 13%」——問一句就走人，寫入的溢價還沒有任何一次命中把它賺回來。
    <b>快取是為連續對話設計的</b>，一次性的問答用不到它。第 2 輪就轉正（省 19%），之後一路擴大。
  </p>
  <p>
    第 4️⃣ 節把總額拆開，是本課最值得盯著看的一張圖：左邊是每輪的 input <b>token 數量</b>、
    右邊是每輪的<b>花費</b>。同一段對話，兩張圖的形狀完全不一樣——
    左邊那塊代表歷史的綠色越疊越高，右邊卻幾乎貼在地上。
    聊到第 10 輪時，37K 的歷史只花 $0.037（同樣這些 token 走一般輸入要 $0.37），
    而那一輪有 67% 的錢是付給輸出的。
  </p>
  <button class="golab" data-nb="3️⃣">到右邊拉桿：兩條累計成本曲線</button>
  <button class="golab" data-nb="4️⃣">再看 4️⃣：token 很多，錢很少</button>
</section>

<section id="s4">
  <span class="eyebrow">04 · 前綴一改就作廢</span>
  <h2>真正貴的不是聊太久，是讓前綴改變</h2>
  <p>
    既然快取綁在「一模一樣的前綴」上，那麼會讓你痛的就只有一件事：<b>前綴被改掉</b>。
    三種常見狀況會做到這件事，而它們在帳單上的效果<b>完全一樣</b>——整段歷史失效、下一輪重新寫入：
  </p>
  <table class="cmp">
    <tr><th>發生了什麼</th><th>為什麼前綴會變</th></tr>
    <tr><td><b>中途切換模型</b></td><td>快取跟模型綁定，換一顆就是換一個快取空間，整段重讀</td></tr>
    <tr><td><b>對話中增減工具 / MCP</b></td><td>工具定義排在最前面（比系統提示還前面），一變後面全滅，而且內容還變長了</td></tr>
    <tr><td><b>閒置超過 TTL</b></td><td>沒人動它，快取自己過期了</td></tr>
  </table>
  <p>
    差別不在單次代價，在<b>你控不控制得了、會發生幾次</b>：
  </p>
  <ul>
    <li><b>只發生一次 → 一次性代價。</b>在 12 輪的情境裡，第 4 輪過期一次多付 $0.218，
      之後曲線的斜率就跟原本平行了。閒置過期沒那麼可怕。</li>
    <li><b>反覆發生 → 比不用快取還貴。</b>把右邊的選單切到「每輪都換模型比較答案」：
      12 輪要 $5.325，而<b>完全不用快取只要 $4.500</b>——貴了 18%。
      因為每輪都失效的話，你每一輪都在付比一般輸入貴 25% 的寫入價，卻一次命中都沒吃到。</li>
  </ul>
  <p class="note">
    這就是「換來換去比不切還貴」的算式版本。想比較兩顆模型的答案？
    <b>開兩個對話各問各的</b>，而不是在同一個對話裡來回切。
  </p>
  <button class="golab" data-nb="5️⃣">到右邊選一種破壞方式，看曲線怎麼歪</button>
</section>

<section id="s5">
  <span class="eyebrow">05 · 日常怎麼用</span>
  <h2>帶得走的幾個習慣</h2>
  <p>
    這一課的算式適用於任何「輸入分成一般／寫入／命中三種價」的服務。落到日常：
  </p>
  <table class="cmp">
    <tr><th>情境</th><th>你該知道的</th></tr>
    <tr><td><b>訂閱制方案</b></td><td>通常自動用長 TTL（1 小時），用量含在方案內。離開一小時內回來，快取都還在——基本上不用管。</td></tr>
    <tr><td><b>API 按量計費</b></td><td>預設 5 分鐘 TTL。只要下一次請求在 5 分鐘內開始，計時器就重新開始——連續聊天基本上不會過期，會過期的是你離開太久。常常離開比較久的話可以改用 1 小時 TTL，代價是寫入價變兩倍，要多命中幾次才回本。</td></tr>
    <tr><td><b>怎麼知道有沒有命中</b></td><td>回應的 <span class="kbd">usage</span> 裡有 <span class="kbd">cache_read_input_tokens</span>（命中）與 <span class="kbd">cache_creation_input_tokens</span>（寫入）。連續幾次請求都是 0 命中，就代表前綴每次都被改掉了——回頭找那個會變的東西。</td></tr>
    <tr><td><b>其他計費工具</b></td><td>邏輯一模一樣：cached input 都比一般 input 便宜。三個習慣通吃——同一個 session 聊到底、別中途換模型、去帳務頁盯 cached tokens 的佔比。</td></tr>
  </table>
  <p>
    兩則冷知識收尾。第一，助理工具內建的系統提示動輒數千行，
    但那是<b>平台注入</b>的，不會出現在你的 input 帳單上——你付的是自己訊息的 token。
    第二，想知道自己的訊息到底幾個 token，別用第三方分詞器猜：
    官方有 <b>count-tokens</b> 端點，把訊息原封不動傳進去就回你 token 數。
  </p>
  <p class="note">
    最後一個尺度感：快取省的是零頭，<b>選對模型省的是大頭</b>——
    同一個工作流換一顆模型，成本可能差一個數量級。但零頭是你不用動腦就能省下來的，
    而且它同時買到更快的 TTFT。
  </p>
  <p>
    覺得算這些錢小家子氣？2026 年上半年，矽谷掀起一波「<b>Token 退燒潮</b>」：
    特斯拉把員工每週 AI 支出上限設在 200 美元（此前有工程師一週燒掉數千美元）；
    Uber 的年度 AI 預算 4 月就見底，6 月起每人每工具每月上限 1,500 美元；
    Meta 發現員工為了內部用量排行榜競相衝 token、成本指數成長，乾脆撤下排行榜；
    Amazon 警告工程師別「為用而用」，Walmart 給自家開發平台設了 token 上限
    （2026 年 5–7 月 Financial Times、The Information、CNBC 等公開報導）。
    當帳單大到公司得立規矩，「懂計費、讓前綴穩定」就不是零頭，是基本素養。
  </p>
</section>

<section id="s6">
  <span class="eyebrow">06 · 實戰</span>
  <h2>換你動手</h2>
  <p>挑戰在 notebook 的 6️⃣ 節，由淺到深：</p>
  <div class="ex">
    <span class="lv">LEVEL 1</span>
    <p>把實驗區的「寫入 TTL」換成 <span class="kbd">1 小時</span>（$20/MTok），
      看三輪總價變多少、還省不省。長 TTL 是免費的嗎？</p>
  </div>
  <div class="ex">
    <span class="lv">LEVEL 2</span>
    <p>把實驗區的「系統提示長度」從 10K 拉到 2K，再拉到 40K，每次都看 3 輪與 20 輪。
      「省的比例」對哪個參數比較敏感——系統提示長度，還是輪數？</p>
  </div>
  <div class="ex">
    <span class="lv">LEVEL 3</span>
    <p>估一次你自己的用量：平常一個工作階段大概聊幾輪、系統提示（含工具說明）多長？
      用 <span class="kbd">breaks=</span> 算出「乖乖聊完」與「中間換兩次模型」的差額，
      並且說得出那筆差額是怎麼來的。</p>
  </div>
  <p style="font-size:13.5px;color:var(--ink-soft);margin-top:10px">卡住了？每一題在 notebook 末節都有折疊解答——先自己做，再打開對照。</p>
  <button class="golab" data-nb="6️⃣">到右邊的實驗區開工</button>
</section>

<section id="quiz">
  <span class="eyebrow">07 · 驗收</span>
  <h2>情境測驗</h2>
  <p>離開前試試看：下面的情境都真的會遇到。每題選一個你認為的最佳做法，選了馬上看得到解釋。</p>
  <div data-quiz>

    <div class="quiz-q" data-answer="B">
      <p class="quiz-tag">Q1 <span class="qtype">情境題</span></p>
      <h3>你要拿一份 30K tokens 的規格文件做問答，估計會問十幾個問題。哪種做法最省？</h3>
      <div class="quiz-opts">
        <button type="button" class="quiz-opt" data-k="A">A. 每個問題各開一個新對話，每次把整份文件貼進去</button>
        <button type="button" class="quiz-opt" data-k="B">B. 在同一個對話裡把文件放在最前面，十幾個問題一路問到底</button>
        <button type="button" class="quiz-opt" data-k="C">C. 把文件切成小段，每次只貼跟問題相關的那一段</button>
        <button type="button" class="quiz-opt" data-k="D">D. 每問一題就換一顆模型交叉驗證，答案比較可靠</button>
      </div>
      <div class="quiz-fb" aria-live="polite"><p>同一個對話 ＝ 同一段共用前綴。文件只在第一輪付一次寫入，之後每一輪都以命中價（一般輸入的 1/10）重複使用——輪數越多省越兇，十幾輪的量級落在省六成以上。A 是最貴的做法：每次都是全額 input，等於把 30K 付十幾遍。C 直覺上省 token，但每次貼的段落不同 ＝ <b>前綴每次都不一樣</b>，一次命中都吃不到，還可能漏掉關鍵資訊。D 最糟：快取跟模型綁定，換一次就整段重讀，這正是本課算過「比不用快取還貴」的那條路。</p></div>
    </div>

    <div class="quiz-q" data-answer="B">
      <p class="quiz-tag">Q2 <span class="qtype dx">錯誤診斷</span></p>
      <h3>你把 notebook 的「對話輪數」拉到 1，其他不變，結果它說用快取<b>反而比較貴</b>。最可能的原因是？</h3>
      <div class="codeblock">系統提示 10K、聊 1 輪：不用快取 $0.210、用快取 $0.237 → 反而貴 13%</div>
      <div class="quiz-opts">
        <button type="button" class="quiz-opt" data-k="A">A. 系統提示 10K 太短，還沒長到快取生效的長度</button>
        <button type="button" class="quiz-opt" data-k="B">B. 第一輪付的是寫入價（比一般輸入貴 25%），而還沒有任何一次命中把這筆溢價賺回來</button>
        <button type="button" class="quiz-opt" data-k="C">C. 快取要第二輪才會建立，第一輪根本沒寫進去，錢是白付的</button>
        <button type="button" class="quiz-opt" data-k="D">D. 那 2K 的輸出太貴，把快取省下來的錢吃光了</button>
      </div>
      <div class="quiz-fb" aria-live="polite"><p>快取的收支是「先付溢價、再靠命中回本」：第一輪要把 11K 以 $12.50/MTok 寫進去（不用快取只要 $10），多付的部分要等第 2 輪的命中才賺得回來。把輪數改成 2，同一組參數立刻轉為省 19%。C 剛好說反了——寫入就發生在第一輪，只是那一輪還沒人來讀它；D 不成立，兩邊的輸出費用完全一樣，不會造成差異；A 是常見誤解，這裡的差異純粹來自寫入與一般輸入的價差。<b>結論：一次性的問答用不到快取，它是為連續對話設計的。</b></p></div>
    </div>

    <div class="quiz-q" data-answer="C">
      <p class="quiz-tag">Q3 <span class="qtype dx">錯誤診斷</span></p>
      <h3>你習慣在同一個對話裡每輪都換一顆模型比較答案。notebook 跑出這個結果——為什麼會比「完全不用快取」還貴？</h3>
      <div class="codeblock">乖乖聊到底 $1.783 → 每輪都換模型 $5.325（多付 $3.542）
比完全不用快取（$4.500）還貴 18%</div>
      <div class="quiz-opts">
        <button type="button" class="quiz-opt" data-k="A">A. 換模型時整段歷史要再送一次，送出去的 token 變多了</button>
        <button type="button" class="quiz-opt" data-k="B">B. 不同模型費率不一樣，比較貴的那顆把平均拉高了</button>
        <button type="button" class="quiz-opt" data-k="C">C. 快取跟模型綁定，每輪都失效 ＝ 每輪都以「寫入價」重付整段歷史，而寫入比一般輸入貴 25%，卻一次命中都沒吃到</button>
        <button type="button" class="quiz-opt" data-k="D">D. 換模型會讓回答變長，輸出費用跟著上升</button>
      </div>
      <div class="quiz-fb" aria-live="polite"><p>關鍵是<b>單價</b>不是數量。A 說的「token 變多」其實沒發生——不用快取時，每一輪本來就要把整段歷史送回去，兩邊送的 token 一樣多；差別在於那些 token 被算成 $12.50/MTok 的寫入，而不是 $10/MTok 的一般輸入，貴 25%，而且因為下一輪又換模型，這筆寫入永遠等不到人來讀。B 在這個模擬裡不成立（全程同一組費率）；D 跟快取無關。修法：想比較模型就<b>開兩個獨立對話</b>各問各的，讓每個對話各自維持自己的前綴。</p></div>
    </div>

    <div class="quiz-q" data-answer="B">
      <p class="quiz-tag">Q4 <span class="qtype">情境題</span></p>
      <h3>你發現午休離開 40 分鐘後回來，接著問的那一輪特別貴（帳單上多了一大筆寫入）。最合理的處置是？</h3>
      <div class="quiz-opts">
        <button type="button" class="quiz-opt" data-k="A">A. 以後每次離開前先清掉對話，免得快取過期還被收錢</button>
        <button type="button" class="quiz-opt" data-k="B">B. 接受它——閒置過期只是多付一次寫入，是一次性代價；真正該戒掉的是中途換模型、對話中增減工具那類反覆改前綴的習慣</button>
        <button type="button" class="quiz-opt" data-k="C">C. 一律改用 1 小時 TTL，這樣永遠不會過期，一定比較划算</button>
        <button type="button" class="quiz-opt" data-k="D">D. 把系統提示大幅縮短，讓每次重寫都便宜一點</button>
      </div>
      <div class="quiz-fb" aria-live="polite"><p>過期的代價是<b>一次性</b>的：多付那一筆之後，累計成本曲線的斜率就跟原本平行了（本課的 12 輪情境裡是 $0.218）。真正會不斷失血的是反覆改前綴——每改一次就多付一筆「當下歷史 × 價差」，而歷史只會越來越長。A 反而更糟：清掉對話等於主動把前綴丟掉，下一輪從零重寫；C 只在「常常離開超過 5 分鐘還會回來」時划算，寫入價變兩倍，要多命中幾次才回本，一律開反而可能虧；D 治標而且傷害教學品質——本課的數字說得很清楚，省的比例主要由<b>輪數</b>決定，不是系統提示長度。</p></div>
    </div>

    <div class="quiz-score" data-score></div>
  </div>
</section>

<div class="endnav">
  <a href="/kv-offload/">
    <span class="tag">下一課</span>
    <b>KV Cache 分層：LMCache 與 SSD 卸載 →</b>
  </a>
  <a href="/local-llm/">
    <span class="tag">主題</span>
    <b>‹ 回「個人地端大語言模型實作」課程列表</b>
  </a>
</div>
"""

SCRIPT = r"""
/* ═══ hero 互動：連續對話計費計算器（純 JS，公式與右邊 notebook 的 run_chat() 一致）═══ */
(function () {
  var M = 1e6, BASE = 10, WRITE = 12.5, HIT = 1, OUT = 50;
  var Q = 1000, A = 2000;   // 每輪固定：問 1K、答 2K

  function sim(n, sysTok, cached) {
    var hist = 0, per = [], total = 0;
    for (var i = 1; i <= n; i++) {
      var nw = (i === 1) ? (sysTok + Q) : Q;
      var c = cached
        ? nw / M * WRITE + hist / M * HIT + A / M * OUT
        : (hist + nw) / M * BASE + A / M * OUT;
      per.push(c);
      total += c;
      hist += nw + A;
    }
    return { total: total, per: per };
  }

  var elN = document.getElementById("pc-n");
  var elS = document.getElementById("pc-s");
  var nVal = document.getElementById("pc-n-val");
  var sVal = document.getElementById("pc-s-val");
  var barP = document.getElementById("pc-bar-plain");
  var barC = document.getElementById("pc-bar-cache");
  var outP = document.getElementById("pc-plain");
  var outC = document.getElementById("pc-cache");
  var save = document.getElementById("pc-save");
  var stripP = document.getElementById("pc-strip-plain");
  var stripC = document.getElementById("pc-strip-cache");
  if (!elN) return;

  function bars(box, per, top, color) {
    var html = "";
    for (var i = 0; i < per.length; i++) {
      var h = Math.max(3, Math.round(per[i] / top * 100));
      html += '<i style="height:' + h + '%;background:' + color + '"></i>';
    }
    box.innerHTML = html;
  }

  function render() {
    var n = +elN.value, s = +elS.value * 1000;
    nVal.textContent = n;
    sVal.textContent = (s / 1000) + "K";

    var c = sim(n, s, true), p = sim(n, s, false);
    var max = Math.max(c.total, p.total);
    barP.style.width = (p.total / max * 100) + "%";
    barC.style.width = (c.total / max * 100) + "%";
    outP.textContent = "$" + p.total.toFixed(4);
    outC.textContent = "$" + c.total.toFixed(4);

    var pct = 1 - c.total / p.total;
    if (pct >= 0) {
      save.className = "save";
      save.innerHTML = "聊 " + n + " 輪省下 <b>" + Math.round(pct * 100) + "%</b>"
        + (n >= 10 ? "——長對話後期，input 幾乎全是命中價。" : "——而且對話越長省越多，往右拉拉看。");
    } else {
      save.className = "save bad";
      save.innerHTML = "只聊 " + n + " 輪：<b>反而貴 " + Math.round(-pct * 100) + "%</b>"
        + "——第一輪的寫入溢價還沒被任何一次命中賺回來。";
    }

    var top = Math.max.apply(null, p.per.concat(c.per));
    bars(stripP, p.per, top, "var(--cut)");
    bars(stripC, c.per, top, "var(--c3)");
  }

  elN.addEventListener("input", render);
  elS.addEventListener("input", render);
  render();
})();
"""
