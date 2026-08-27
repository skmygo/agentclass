"""課程頁內容區（純常數）。改完跑：python3 .claude/skills/make-lesson/scripts/page-fill.py content/genai-intro/genai-reasoning
build.sh 不會部署這個檔；它是 index.html 內容區的正本。"""

TITLE = "會思考的模型：CoT 與 Reasoning Model"
DESCRIPTION = "同一題、同一顆模型：直接答是錯的 55，「一步一步想」就答對 5——實測紀錄親眼看。CoT、Reasoning Model、Test-time Compute、Overthinking、ToT/GoT，推理範式的五個名詞一次搞懂。"

STYLE = r"""
  /* 語義色：藍＝CoT、橘＝reasoning model、綠＝test-time compute、紫＝ToT/GoT、紅＝錯誤 */
  :root { --c1: #4C72B0; --c2: #DD8452; --c3: #55A868; --c4: #8172B2; --cut: #C44E52; }

  .tldr { border-left: 4px solid var(--tc, var(--c1)); background: var(--chip-bg);
    border-radius: 0 10px 10px 0; padding: 10px 14px; margin: 12px 0 16px;
    font-size: 14.5px; line-height: 1.7; }
  .tldr b { color: var(--tc, var(--c1)); }

  /* hero：實測逐字稿重播 */
  #cot-demo .q { font-size: 14.5px; line-height: 1.75; border: 2px solid var(--ink);
    border-radius: 12px; padding: 10px 14px; margin-bottom: 10px; background: var(--panel); }
  #cot-demo .btns { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 10px; }
  #cot-demo .go { font: inherit; font-size: 13.5px; font-weight: 800; color: var(--ink);
    background: var(--panel); border: 2px solid var(--grid); border-radius: 999px;
    padding: 7px 16px; cursor: pointer; transition: border-color .15s, background .15s; }
  #cot-demo .go:hover { border-color: var(--ink-soft); }
  #cot-demo .go.on-a { border-color: var(--cut); background: #FBEAEA; color: var(--cut); }
  #cot-demo .go.on-b { border-color: var(--c1); background: #E8F0F7; color: var(--c1); }
  #cot-demo .trace { border: 2px solid var(--grid); border-radius: 12px; padding: 12px 14px;
    font-size: 13.5px; line-height: 1.8; white-space: pre-wrap; min-height: 72px;
    max-height: 320px; overflow-y: auto; }
  #cot-demo .trace .ln { opacity: 0; animation: cotln .3s ease forwards; display: block; }
  @keyframes cotln { to { opacity: 1; } }
  @media (prefers-reduced-motion: reduce) { #cot-demo .trace .ln { animation: none; opacity: 1; } }
  #cot-demo .verdict { margin-top: 8px; font-size: 14px; font-weight: 800; }
  #cot-demo .verdict.bad { color: var(--cut); }
  #cot-demo .verdict.good { color: var(--c3); }
  #cot-demo .src { font-size: 12px; color: var(--ink-soft); margin-top: 6px; }

  table.cmp { width: 100%; border-collapse: collapse; font-size: 13.5px; margin: 14px 0; }
  table.cmp th, table.cmp td { border-bottom: 1px solid var(--grid); padding: 8px 10px; text-align: left; vertical-align: top; }
  table.cmp th { font-size: 12px; letter-spacing: .04em; color: var(--ink-soft); }
  table.cmp td.n { font-family: var(--mono); font-weight: 800; white-space: nowrap; }
  .kbd { font-family: var(--mono); background: var(--chip-bg); padding: 1px 6px; border-radius: 5px; font-size: 13px; }
  .src { font-size: 12.5px; color: var(--ink-soft); margin-top: -6px; }

  table.cheat { width: 100%; border-collapse: collapse; font-size: 14px; margin: 14px 0; }
  table.cheat td { border-bottom: 1px solid var(--grid); padding: 10px 12px; vertical-align: top; line-height: 1.7; }
  table.cheat td.t { font-weight: 800; white-space: nowrap; width: 11em; }

  .tot-fig { display: flex; gap: 14px; flex-wrap: wrap; margin: 14px 0; }
  .tot-fig figure { flex: 1 1 150px; margin: 0; text-align: center; }
  .tot-fig figcaption { font-size: 12.5px; color: var(--ink-soft); margin-top: 4px; line-height: 1.6; }
"""

WRAP = r"""
<section id="hero">
  <span class="eyebrow">GENAI REASONING · 04 · 推理範式</span>
  <h1>會思考的模型：<br>CoT 與 Reasoning Model</h1>
  <p style="margin-top:18px">
    同一題、同一顆模型、同樣 temperature=0——只差<b>一句話的問法</b>，
    答案一個錯一個對。這是真實紀錄（qwen3.5-2b，2026-08 實測；你跑同一題結果可能不同），
    自己按按看：
  </p>

  <div class="hero-demo" id="cot-demo">
    <div class="q">❓ 一根球棒和一顆球總共 110 元，球棒比球貴 100 元。球多少錢？</div>
    <div class="btns">
      <button type="button" class="go" id="cot-a">問法 A：「請直接回答，只給數字」</button>
      <button type="button" class="go" id="cot-b">問法 B：「請一步一步推理」</button>
    </div>
    <div class="trace" id="cot-trace">（點上面任一種問法，看模型的真實回答）</div>
    <div class="verdict" id="cot-verdict"></div>
    <div class="src">實測紀錄：qwen3.5-2b、temperature=0、2026-08。正解是 5 元。</div>
  </div>

  <p class="note">
    右邊的實驗場是真的 Python（在你的瀏覽器裡跑，不用安裝任何東西）。
    首次載入約需 30–60 秒，正好夠你讀完第 1 節。每一格程式碼都能改、能重跑，
    改壞了重新整理就復原——這是你的沙盒，盡量玩。
  </p>
</section>

<section id="s1">
  <span class="eyebrow">01 · CHAIN-OF-THOUGHT</span>
  <h2>CoT：讓模型把步驟寫出來</h2>
  <div class="tldr" style="--tc:var(--c1)">
    <b>一句話重點</b>：Chain-of-Thought＝要求模型<b>先寫推理過程再給答案</b>——
    一句提示詞的成本，數學與邏輯題的正確率大幅提升。
  </div>
  <p>
    為什麼有效？回想<a href="/genai-tokens/">第 1 課</a>：模型是自迴歸的，
    一次吐一個 token、吐出去就不能回頭改。問法 A 逼它「一口氣直接吐答案」，
    等於要它憑直覺搶答——它抓了 110÷2 的直覺就輸出 55。
    問法 B 讓它把中間步驟寫出來，<b>寫下的每一步都成為後面步驟的輸入</b>
    （前文越完整、下一個 token 越有依據）——紙上談兵的「紙」本身就是工作記憶。
  </p>
  <p>你在 hero 看到的就是這兩種問法的完整原文，程式上只差一行：</p>
  <div class="codeblock">q = "一根球棒和一顆球總共 110 元，球棒比球貴 100 元。球多少錢？"

# 問法 A：直接答（實測輸出：55，錯）
ask(q + "請直接回答，只給一個數字，不要解釋。")

# 問法 B：CoT（實測輸出：四步推導，答案 5 元，對）
ask(q + "請一步一步推理，把每一步寫出來，最後一行寫「答案：X 元」。")</div>
  <p>
    這招 2022 年被命名為 Chain-of-Thought prompting，現在已經是基本功——
    連「把答案抽出來」都有慣用款式（要求固定格式的最後一行，方便程式解析）。
  </p>
</section>

<section id="s2">
  <span class="eyebrow">02 · REASONING MODEL</span>
  <h2>Reasoning Model：把「先想再答」內建進模型</h2>
  <div class="tldr" style="--tc:var(--c2)">
    <b>一句話重點</b>：reasoning model（OpenAI o 系列、DeepSeek-R1、Claude 的
    extended thinking）把 CoT <b>內建成模型行為</b>——回答前先產生一段思考軌跡，
    思考與答案分開回傳。
  </div>
  <p>
    你不用再手寫「請一步一步想」，模型自己會想，而且想多深是<b>訓練出來的</b>——
    用強化學習獎勵「想了之後答對」（<a href="/genai-training/">第 2 課</a>的 GRPO
    正是 DeepSeek-R1 用的配方；訓練中模型自發長出檢查、回溯的行為，
    論文稱之為「aha moment」）。API 的介面也跟著變：思考和答案是兩個欄位。
  </p>
  <p>Claude 的 extended thinking（真實 API，2026-08 規格）：</p>
  <div class="codeblock">import anthropic

client = anthropic.Anthropic()
resp = client.messages.create(
    model="claude-opus-5",
    max_tokens=16000,
    thinking={"type": "adaptive", "display": "summarized"},  # 模型自己決定想多深
    messages=[{"role": "user", "content": "一根球棒和一顆球總共 110 元…球多少錢？"}],
)
for block in resp.content:
    if block.type == "thinking":
        print("思考軌跡：", block.thinking)
    elif block.type == "text":
        print("最終回答：", block.text)</div>
  <p>DeepSeek-R1 這一系開源模型走同樣的介面慣例（思考在 <span class="kbd">reasoning_content</span>）：</p>
  <div class="codeblock">from openai import OpenAI

client = OpenAI(base_url="https://api.deepseek.com", api_key="...")
resp = client.chat.completions.create(
    model="deepseek-reasoner",
    messages=[{"role": "user", "content": "……"}],
)
print(resp.choices[0].message.reasoning_content)  # 思考軌跡
print(resp.choices[0].message.content)            # 最終答案</div>
  <p class="src">
    工程備忘：reasoning model 的 max_tokens 要給足（思考也算 token）——
    給太小，思考還沒想完就被截斷，有的服務會回空答案。
  </p>
</section>

<section id="s3">
  <span class="eyebrow">03 · TEST-TIME COMPUTE</span>
  <h2>Test-time Compute：拿算力換正確率</h2>
  <div class="tldr" style="--tc:var(--c3)">
    <b>一句話重點</b>：不改模型，在<b>回答的當下</b>多花算力（想更久、抽多次投票）
    換更高正確率——但效益遞減，簡單題想太多就是 <b>overthinking</b>。
  </div>
  <p>
    「想更久」是一條路，「多抽幾次、投票表決」是另一條。實測：
    問 qwen3.5-2b「47 × 38 = ?」只准直接答，temperature=1 抽 9 次——
    單次答對率只有 6/9，但 9 個答案投票，正解 1786 以 6 票勝出
    （錯誤答案 1451、1466、1446 各自只有 1 票：<b>對的答案只有一種，
    錯的各錯各的</b>）。到右邊看真實開票結果，再用二項分布算清楚
    「該投幾票」。
  </p>
  <p>
    反面是 <b>overthinking</b>：簡單題也長篇思考，多付延遲與 token 費用、
    正確率卻沒得漲，深度思考甚至可能把原本對的直覺推翻。所以現代 API 把
    「想多深」做成可調參數（Claude 的 adaptive thinking 讓模型自己判斷、
    OpenAI o 系列的 reasoning effort 檔位）——<b>難題才值得深思，
    簡單題直答就好</b>，這個判斷本身成了工程決策。
  </p>
  <button class="golab" data-nb="1️⃣">到右邊 1️⃣ 看 9 次抽樣的真實開票</button>
  <button class="golab" data-nb="2️⃣">到右邊 2️⃣ 算「該投幾票」的數學</button>
</section>

<section id="s4">
  <span class="eyebrow">04 · TOT / GOT</span>
  <h2>ToT／GoT：從一條鏈到一棵樹（進階閱讀）</h2>
  <div class="tldr" style="--tc:var(--c4)">
    <b>一句話重點</b>：Tree-of-Thoughts／Graph-of-Thoughts 是 CoT 的結構化進階——
    推理可以<b>分支、回溯、合併、投票</b>，不再是一條直線。
  </div>
  <div class="tot-fig">
    <figure>
      <svg viewBox="0 0 120 90" width="100%" height="84" aria-label="CoT: linear chain">
        <g stroke="#4C72B0" stroke-width="2.5" fill="none">
          <line x1="20" y1="45" x2="52" y2="45"/><line x1="68" y1="45" x2="100" y2="45"/>
        </g>
        <g fill="#4C72B0"><circle cx="14" cy="45" r="7"/><circle cx="60" cy="45" r="7"/><circle cx="106" cy="45" r="7"/></g>
      </svg>
      <figcaption><b>CoT</b>：一條直線想到底，走錯就錯到底</figcaption>
    </figure>
    <figure>
      <svg viewBox="0 0 120 90" width="100%" height="84" aria-label="ToT: branching tree">
        <g stroke="#8172B2" stroke-width="2.5" fill="none">
          <line x1="18" y1="45" x2="55" y2="20"/><line x1="18" y1="45" x2="55" y2="70"/>
          <line x1="62" y1="20" x2="99" y2="10"/><line x1="62" y1="20" x2="99" y2="34"/>
          <line x1="62" y1="70" x2="99" y2="70"/>
        </g>
        <g fill="#8172B2"><circle cx="14" cy="45" r="7"/><circle cx="60" cy="20" r="6"/><circle cx="60" cy="70" r="6"/>
        <circle cx="104" cy="10" r="5"/><circle cx="104" cy="34" r="5"/></g>
        <circle cx="104" cy="70" r="5" fill="none" stroke="#C44E52" stroke-width="2"/>
      </svg>
      <figcaption><b>ToT</b>：分支探索、評分、剪掉死路（紅圈）、可回溯</figcaption>
    </figure>
    <figure>
      <svg viewBox="0 0 120 90" width="100%" height="84" aria-label="GoT: graph with merges">
        <g stroke="#8172B2" stroke-width="2.5" fill="none">
          <line x1="18" y1="45" x2="55" y2="20"/><line x1="18" y1="45" x2="55" y2="70"/>
          <line x1="62" y1="20" x2="99" y2="45"/><line x1="62" y1="70" x2="99" y2="45"/>
        </g>
        <g fill="#8172B2"><circle cx="14" cy="45" r="7"/><circle cx="60" cy="20" r="6"/><circle cx="60" cy="70" r="6"/></g>
        <circle cx="104" cy="45" r="7" fill="#55A868"/>
      </svg>
      <figcaption><b>GoT</b>：分支再<b>合併</b>（綠點）——部分解可以彙整</figcaption>
    </figure>
  </div>
  <p>
    知道有這回事就好：ToT 適合「走錯要能回頭」的搜尋型問題（解謎、規劃），
    GoT 再加上「把幾條思路的成果合併」。代價都是<b>多很多次</b>模型呼叫——
    它們是 test-time compute 的重型版本，日常任務用不到；
    你在 3️⃣ 玩的多數決（self-consistency）就是這家族裡最便宜實用的一招。
  </p>
</section>

<section id="s5">
  <span class="eyebrow">05 · 速查</span>
  <h2>本課名詞速查卡</h2>
  <p>發講義用的濃縮版——一個名詞一句話：</p>
  <table class="cheat">
    <tr><td class="t" style="color:var(--c1)">Chain-of-Thought</td>
        <td>要求模型<b>先寫步驟再答</b>——一句提示詞，數學正確率大增（實測：直接答 55 錯、CoT 答 5 對）。</td></tr>
    <tr><td class="t" style="color:var(--c2)">Reasoning Model</td>
        <td>把「先想再答」<b>內建</b>的模型（o 系列、R1、Claude extended thinking）；思考與答案分欄回傳。</td></tr>
    <tr><td class="t" style="color:var(--c3)">Test-time Compute</td>
        <td>回答當下多花算力（想久、多抽投票）換正確率；<b>效益遞減</b>，且單次答對率須過半投票才有用。</td></tr>
    <tr><td class="t" style="color:var(--cut)">Overthinking</td>
        <td>簡單題想太多——多付延遲與費用、正確率不漲反跌的反效果；「想多深」因此成為可調參數。</td></tr>
    <tr><td class="t" style="color:var(--c4)">ToT / GoT</td>
        <td>CoT 的樹狀／圖狀進階：分支、回溯、合併、投票——重型 test-time compute，特定搜尋型問題才划算。</td></tr>
  </table>
</section>

<section id="s6">
  <span class="eyebrow">06 · 實戰</span>
  <h2>換你動手</h2>
  <div class="ex">
    <span class="lv">LEVEL 1</span>
    <p>在右邊 2️⃣ 把單次答對率 p 拉到 0.45（低於一半），看多數決曲線發生什麼事。投越多票越準的前提是什麼？</p>
  </div>
  <div class="ex">
    <span class="lv">LEVEL 2</span>
    <p>用 1️⃣ 的實測答對率（6/9）算：投 3、9、21、41 次的多數決答對率各是多少？從哪裡開始「加倍算力買不到幾個百分點」？（實驗區已備好起點程式。）</p>
  </div>
  <div class="ex">
    <span class="lv">LEVEL 3</span>
    <p>二項分布模型假設「每次抽樣獨立」。看 1️⃣ 的三個錯誤答案（1451、1466、1446），找出它們共同的規律——這個規律說明真實模型的錯誤哪裡不獨立？什麼情況下投票會整組翻車、反而該用 CoT？</p>
  </div>
  <p style="font-size:13.5px;color:var(--ink-soft);margin-top:10px">卡住了？三題在 notebook 最後一格都有折疊解答——先自己做，再打開對照。</p>
  <button class="golab" data-nb="3️⃣">到右邊 3️⃣ 的實驗區開工</button>
</section>

<section id="quiz">
  <span class="eyebrow">07 · 驗收</span>
  <h2>情境測驗</h2>
  <p>離開前試試看：下面的情境都真的會遇到。每題選一個你認為的最佳做法，選了馬上看得到解釋。</p>
  <div data-quiz>

    <div class="quiz-q" data-answer="B">
      <p class="quiz-tag">Q1 <span class="qtype">情境題</span></p>
      <h3>你的產品有兩條 LLM 功能線：(1) 客服 FAQ 快答（一天十萬次、使用者等在線上）、(2) 每晚跑一次的財務對帳異常分析（複雜、錯了很貴）。reasoning model 該用在哪？</h3>
      <div class="quiz-opts">
        <button type="button" class="quiz-opt" data-k="A">A. 兩條都用——會思考的模型一定比不會思考的好</button>
        <button type="button" class="quiz-opt" data-k="B">B. 對帳分析用 reasoning model（難題、離線、錯誤成本高）；FAQ 用一般模型直答（簡單、量大、延遲敏感），必要時開低檔思考</button>
        <button type="button" class="quiz-opt" data-k="C">C. 兩條都不用——reasoning model 還不成熟，等技術穩定再說</button>
        <button type="button" class="quiz-opt" data-k="D">D. FAQ 用 reasoning model 提升品質，對帳用一般模型省成本</button>
      </div>
      <div class="quiz-fb" aria-live="polite"><p>套本課的判斷式：<b>難題才值得深思</b>。對帳分析是多步推理、離線執行（延遲無感）、錯誤成本高——多花的思考 token 都買在刀口上。FAQ 是簡單題＋大流量＋使用者在線等：reasoning model 的思考時間直接變成使用者的等待，token 費用乘十萬倍，正確率卻沒得漲——教科書級的 overthinking 場景。A 忽略成本與延遲是真實約束；C 因噎廢食，o 系列與 R1 已在生產環境大量使用；D 剛好把兩邊都放錯位置。</p></div>
    </div>

    <div class="quiz-q" data-answer="C">
      <p class="quiz-tag">Q2 <span class="qtype">情境題</span></p>
      <h3>你的報表工具用 LLM 把自然語言轉成 SQL，複雜查詢常轉錯。老闆說「換最貴的模型」。在那之前，最便宜、最該先試的一步是？</h3>
      <div class="quiz-opts">
        <button type="button" class="quiz-opt" data-k="A">A. 收集轉錯的例子，微調一個專屬模型</button>
        <button type="button" class="quiz-opt" data-k="B">B. 把 temperature 調成 0，輸出就會穩定正確</button>
        <button type="button" class="quiz-opt" data-k="C">C. 改提示詞：要求模型先寫出「要查哪些表、怎麼 join、篩選條件是什麼」的推理步驟，再輸出 SQL——CoT 是一行提示詞的成本</button>
        <button type="button" class="quiz-opt" data-k="D">D. 同一題抽 20 次、挑出現最多次的 SQL</button>
      </div>
      <div class="quiz-fb" aria-live="polite"><p>成本階梯由低到高：改提示詞 → 多抽投票 → 換模型 → 微調。CoT 站在階梯最底層：一行話的成本，對「多步推理型」錯誤（join 邏輯、條件遺漏）常有立竿見影的改善——本課 hero 就是活例子。B 混淆了穩定與正確：temperature=0 只是每次錯得一樣（hero 實測就是 temp=0 照樣答 55）。D 可行但比 C 貴 20 倍，而且 SQL 字串比對「同一答案」不容易，該在 C 之後才考慮。A 是最後手段：貴、慢，且 CoT 沒試過之前你根本不知道需不需要。</p></div>
    </div>

    <div class="quiz-q" data-answer="C">
      <p class="quiz-tag">Q3 <span class="qtype dx">錯誤診斷</span></p>
      <h3>同事的自動閱卷程式用下面的問法呼叫模型（temperature=0），球棒與球那題模型回了「55」。他說「temperature 已經是 0 了，輸出最穩定的答案還是錯，這模型數學不行，只能換模型」。他的診斷哪裡有問題？</h3>
      <div class="codeblock">prompt = 題目 + "請直接回答，只給一個數字，不要解釋。"
# 模型輸出：55        （正解：5）</div>
      <div class="quiz-opts">
        <button type="button" class="quiz-opt" data-k="A">A. 沒問題，2B 小模型本來就不會算術，換大模型是唯一解</button>
        <button type="button" class="quiz-opt" data-k="B">B. temperature=0 才是錯誤根源，調高就有機會抽到正解</button>
        <button type="button" class="quiz-opt" data-k="C">C. 問法禁止了推理：「只給數字、不要解釋」逼模型一步輸出直覺答案。同一模型改要求「一步一步推理」就答對 5——先修問法，再談換模型</button>
        <button type="button" class="quiz-opt" data-k="D">D. 題目描述有歧義，模型理解成另一種題意才答 55</button>
      </div>
      <div class="quiz-fb" aria-live="polite"><p>這正是本課 hero 的實測：同一顆 qwen3.5-2b、同樣 temperature=0，禁止解釋→ 55（錯）、要求逐步推理→ 5（對）。「只給數字」不是無害的格式要求，它剝奪了自迴歸模型唯一的工作記憶——寫在紙上的中間步驟。B 說反了：temp=0 與對錯無關，調高只是讓錯法多樣化（想穩定又想推理，就 CoT＋temp=0）；D 無中生有，題目數學上沒有歧義；A 下結論太早——換模型可能也有幫助，但一行提示詞就能修好的問題，先用一行提示詞修。診斷順序：先檢查「問法是否允許模型推理」，再懷疑模型能力。</p></div>
    </div>

    <div class="quiz-score" data-score></div>
  </div>
</section>

<div class="endnav">
  <a href="/genai-agents/">
    <span class="tag">下一課</span>
    <b>AI Agent 與 MCP：模型長出手腳 →</b>
  </a>
  <a href="/genai-intro/">
    <span class="tag">主題</span>
    <b>‹ 回「生成式 AI 導論」課程列表</b>
  </a>
</div>
"""

SCRIPT = r"""
/* ═══ hero 互動：實測逐字稿重播（qwen3.5-2b、temperature=0、2026-08）═══
   內容為真實 API 回應原文，僅把 **粗體** 轉成 <b>、逐行進場。 */
(function () {
  const DIRECT = ["55"];
  const COT = [
    "我們來一步步解決這個問題。",
    "",
    "**第一步：定義變數**",
    "假設球的價格為 $x$ 元。",
    "因為球棒比球貴 100 元，所以球棒的價格可以表示為 $(x + 100)$ 元。",
    "",
    "**第二步：建立方程**",
    "根據題目中的總金額條件：「一根球棒和一顆球總共 110 元」。",
    "我們可以將球棒和球的價格相加，並等於 110。",
    "方程如下：",
    "$$x + (x + 100) = 110$$",
    "",
    "**第三步：解方程**",
    "1. 先展開括號（這裡已經展開了）：",
    "   $$2x + 100 = 110$$",
    "",
    "2. 將 100 移到等號右邊（兩邊同時減去 100）：",
    "   $$2x = 110 - 100$$",
    "   $$2x = 10$$",
    "",
    "3. 將等式兩邊同時除以 2，求出 $x$：",
    "   $$x = 10 / 2$$",
    "   $$x = 5$$",
    "",
    "所以，球的價格是 5 元。",
    "",
    "**第四步：驗證**",
    "如果球是 5 元，球棒就是 $5 + 100 = 105$ 元。",
    "球棒 + 球 = $105 + 5 = 110$ 元。",
    "符合題目條件。",
    "",
    "答案：5 元",
  ];
  const btnA = document.getElementById("cot-a");
  const btnB = document.getElementById("cot-b");
  const trace = document.getElementById("cot-trace");
  const verdict = document.getElementById("cot-verdict");
  if (!btnA) return;
  function esc(t) { return t.replace(/&/g, "&amp;").replace(/</g, "&lt;"); }
  function md(t) { return esc(t).replace(/\*\*([^*]+)\*\*/g, "<b>$1</b>"); }
  function play(lines, cls) {
    btnA.classList.toggle("on-a", cls === "bad");
    btnB.classList.toggle("on-b", cls === "good");
    trace.innerHTML = lines.map((ln, i) =>
      `<span class="ln" style="animation-delay:${Math.min(i * 90, 2600)}ms">${md(ln) || "&nbsp;"}</span>`).join("");
    trace.scrollTop = 0;
    verdict.className = "verdict " + cls;
    verdict.textContent = cls === "bad"
      ? "✗ 答 55——錯（憑直覺搶答：110 ÷ 2）"
      : "✓ 答 5 元——對（四步推導＋自我驗證）";
  }
  btnA.addEventListener("click", () => play(DIRECT, "bad"));
  btnB.addEventListener("click", () => play(COT, "good"));
})();
"""
