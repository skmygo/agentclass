"""課程頁內容區（純常數）。改完跑：python3 .claude/skills/make-lesson/scripts/page-fill.py content/genai-intro/genai-tokens
build.sh 不會部署這個檔；它是 index.html 內容區的正本。"""

TITLE = "Token、Embedding 與上下文窗"
DESCRIPTION = "生成式 AI 第一課：文字怎麼被切成 token（同一句話中文比英文多 70% token）、語意怎麼變成向量、模型一次能看多少、為什麼回答一個字一個字蹦出來——四個地基名詞，全部親手摸過。"

STYLE = r"""
  /* 語義色：藍＝token、橘＝embedding、綠＝context、紫＝autoregressive、紅＝代價 */
  :root { --c1: #4C72B0; --c2: #DD8452; --c3: #55A868; --c4: #8172B2; --cut: #C44E52; }

  /* 每個名詞開頭的一句話重點（講義速查行） */
  .tldr { border-left: 4px solid var(--tc, var(--c1)); background: var(--chip-bg);
    border-radius: 0 10px 10px 0; padding: 10px 14px; margin: 12px 0 16px;
    font-size: 14.5px; line-height: 1.7; }
  .tldr b { color: var(--tc, var(--c1)); }

  /* hero：真實 tokenizer 切片 */
  #tok-demo .picks { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 12px; }
  #tok-demo .pick { font: inherit; font-size: 13.5px; font-weight: 700; color: var(--ink);
    background: var(--panel); border: 2px solid var(--grid); border-radius: 999px;
    padding: 6px 14px; cursor: pointer; transition: border-color .15s, background .15s; }
  #tok-demo .pick:hover { border-color: var(--ink-soft); }
  #tok-demo .pick.on { border-color: var(--c1); background: var(--chip-bg); color: var(--c1); }
  #tok-demo .board { border: 2px solid var(--ink); border-radius: 12px; padding: 14px 16px; }
  #tok-demo .chips { line-height: 2.3; }
  #tok-demo .chip { display: inline-block; font-family: var(--mono); font-size: 14px; font-weight: 700;
    background: #E8F0F7; border: 1.5px solid var(--c1); border-radius: 8px;
    padding: 1px 8px; margin: 2px 3px; white-space: pre; }
  #tok-demo .chip.byte { background: #FBEAEA; border-color: var(--cut); color: var(--cut); }
  #tok-demo .stat { margin-top: 10px; font-size: 14px; line-height: 1.75; }
  #tok-demo .stat b.n { font-family: var(--mono); font-size: 16px; color: var(--c1); }
  #tok-demo .src { font-size: 12px; color: var(--ink-soft); margin-top: 6px; }

  table.cmp { width: 100%; border-collapse: collapse; font-size: 13.5px; margin: 14px 0; }
  table.cmp th, table.cmp td { border-bottom: 1px solid var(--grid); padding: 8px 10px; text-align: left; vertical-align: top; }
  table.cmp th { font-size: 12px; letter-spacing: .04em; color: var(--ink-soft); }
  table.cmp td.n { font-family: var(--mono); font-weight: 800; white-space: nowrap; }
  .kbd { font-family: var(--mono); background: var(--chip-bg); padding: 1px 6px; border-radius: 5px; font-size: 13px; }
  .src { font-size: 12.5px; color: var(--ink-soft); margin-top: -6px; }

  /* 速查卡 */
  table.cheat { width: 100%; border-collapse: collapse; font-size: 14px; margin: 14px 0; }
  table.cheat td { border-bottom: 1px solid var(--grid); padding: 10px 12px; vertical-align: top; line-height: 1.7; }
  table.cheat td.t { font-weight: 800; white-space: nowrap; width: 11em; }
"""

WRAP = r"""
<section id="hero">
  <span class="eyebrow">GENAI BASICS · 01 · 基礎概念</span>
  <h1>Token、Embedding<br>與上下文窗</h1>
  <p style="margin-top:18px">
    所有關於 LLM 的名詞——計費、上下文、RAG、加速——追到最底，都站在四個地基上。
    第一個地基是：<b>模型看到的不是字，是 token</b>。
    點下面四句話，看真實的 tokenizer（GPT-4o 系列的 <span class="kbd">o200k_base</span>）
    怎麼下刀：
  </p>

  <div class="hero-demo" id="tok-demo">
    <div class="picks" id="tok-picks"></div>
    <div class="board">
      <div class="chips" id="tok-chips"></div>
      <div class="stat" id="tok-stat"></div>
      <div class="src" id="tok-src"></div>
    </div>
  </div>

  <p class="note">
    右邊的實驗場是真的 Python（在你的瀏覽器裡跑，不用安裝任何東西）。
    首次載入約需 30–60 秒，正好夠你讀完第 1 節。每個實驗都有滑桿與選項可以拉，
    拉完立刻重算——這是你的沙盒，盡量玩。
  </p>
</section>

<section id="s1">
  <span class="eyebrow">01 · TOKEN / TOKENIZER</span>
  <h2>Token：模型處理文字的最小單位</h2>
  <div class="tldr" style="--tc:var(--c1)">
    <b>一句話重點</b>：token 是模型的最小文字單位，<b>計費照它算、上下文照它數</b>——
    跟 LLM 有關的錢和容量，單位都是 token。
  </div>
  <p>
    Tokenizer 把文字切成 token 的規則叫 <b>BPE（Byte Pair Encoding）</b>，
    訓練方式簡單得驚人：從單一字元開始，反覆把「語料裡最常相鄰的兩塊」黏成一塊，
    黏個幾十萬次。於是常見字串（<span class="kbd">international</span>）變成一整塊，
    罕見字串被切成碎塊。你可以在右邊親手訓練一個迷你 BPE，十次合併就看得到這個過程。
  </p>
  <p>
    開場那個實驗值得再看一眼數字：同樣意思的一句話，
    英文 44 個字元只切成 <b>10 個 token</b>（平均 4.4 字元一塊），
    中文 15 個字卻切成 <b>17 個 token</b>——平均一個字被切成 1.1 塊，
    有的字甚至被剖成兩三塊 byte。實測（<span class="kbd">o200k_base</span>，2026-08）：
    <b>同樣內容，中文大約要多花 70% 的 token</b>。API 按 token 計價、
    上下文按 token 計量，所以這不是冷知識，是成本結構。
  </p>
  <p>想自己數，真實工具長這樣（<span class="kbd">tiktoken</span> 是 OpenAI 的官方 tokenizer 套件）：</p>
  <div class="codeblock">import tiktoken

enc = tiktoken.get_encoding("o200k_base")     # GPT-4o／o 系列用的編碼
ids = enc.encode("敏捷的棕色狐狸跳過了那隻懶狗。")
print(len(ids))                               # 17（同義英文句只要 10）</div>
  <p>開源模型各有各的 tokenizer，用 Hugging Face 的 <span class="kbd">transformers</span> 載：</p>
  <div class="codeblock">from transformers import AutoTokenizer

tok = AutoTokenizer.from_pretrained("meta-llama/Llama-3.1-8B-Instruct")
tok.tokenize("生成式人工智慧")               # 每家模型的刀工都不一樣</div>
  <button class="golab" data-nb="1️⃣">到右邊 1️⃣ 親手訓練一個迷你 BPE</button>
</section>

<section id="s2">
  <span class="eyebrow">02 · EMBEDDING</span>
  <h2>Embedding：把語意變成座標</h2>
  <div class="tldr" style="--tc:var(--c2)">
    <b>一句話重點</b>：embedding 把文字轉成<b>語意向量</b>——意思越近、向量越近，
    是語意搜尋與 RAG 的地基。
  </div>
  <p>
    Token 編號本身沒有意義（編號 3421 和 3422 毫無關係），
    <b>embedding 模型</b>負責把一段文字變成一串浮點數（常見 768～4096 維），
    讓「意思相近」的文字在這個高維空間裡<b>距離相近</b>。
    相似度用 <b>cosine</b>（夾角）量：1.0 是同方向、0 是無關。
  </p>
  <p>
    右邊 2️⃣ 有 16 個短句的<b>真向量</b>（embedding 模型事先算好、打包進課程）。
    你會看到情緒句自成一國；也會看到一個反直覺的事實——
    「熱拿鐵咖啡」的最近鄰不是別的食物，是「熱騰騰的拉麵」（cosine 0.423），
    而同屬食物的「草莓蛋糕」只有 0.143：<b>embedding 量的是語意組合，
    不是你心裡的目錄分類</b>。
  </p>
  <p>真實工具的用法（各家 API 大同小異，都是「文字進、向量出」）：</p>
  <div class="codeblock">from openai import OpenAI

client = OpenAI()
resp = client.embeddings.create(
    model="text-embedding-3-small",
    input=["一隻可愛的貓", "一隻忠心的狗"],
)
vec = resp.data[0].embedding        # 1536 維的浮點數清單

# 相似度＝cosine：夾角越小、語意越近
import numpy as np
a, b = np.array(resp.data[0].embedding), np.array(resp.data[1].embedding)
cos = a @ b / (np.linalg.norm(a) * np.linalg.norm(b))</div>
  <button class="golab" data-nb="2️⃣">到右邊 2️⃣ 看 16 個真向量的語意地圖</button>
</section>

<section id="s3">
  <span class="eyebrow">03 · CONTEXT WINDOW</span>
  <h2>Context Window：模型的工作記憶</h2>
  <div class="tldr" style="--tc:var(--c3)">
    <b>一句話重點</b>：模型一次能看的 token 上限。<b>超過的部分不是記性差，
    是根本沒被送進去</b>；窗越長，推理時的 KV cache 也越大。
  </div>
  <p>
    System prompt ＋ 對話歷史 ＋ 你貼的文件 ＋ 模型的回答，<b>全部</b>擠同一個窗。
    塞不下的時候會發生兩種事之一：API 直接回錯誤（後面驗收那題你會親眼看到真實的錯誤訊息），
    或者應用程式默默把最舊的對話裁掉——這就是「聊久了它忘記開頭」的真相。
  </p>
  <table class="cmp">
    <tr><th>模型（公開規格）</th><th>上下文窗</th><th>大約等於</th></tr>
    <tr><td>Llama 3</td><td class="n">8K</td><td>一篇長文</td></tr>
    <tr><td>Llama 3.1 / GPT-4o</td><td class="n">128K</td><td>一本薄薄的書</td></tr>
    <tr><td>Claude Haiku 4.5</td><td class="n">200K</td><td>一本小說</td></tr>
    <tr><td>Claude Opus 5</td><td class="n">1M</td><td>整套文件庫</td></tr>
  </table>
  <p>
    但「裝得下」不等於「該全塞」：塞一堆無關內容會稀釋重點、拉高成本，
    上下文越長推理要維護的 KV cache 記憶體也暴增——「怎麼塞得聰明」是
    <a href="/genai-devstyle/">第 6 課</a>的 context engineering，
    「為什麼變貴變慢」是<a href="/genai-inference/">第 3 課</a>的主線。
  </p>
  <button class="golab" data-nb="3️⃣">到右邊 3️⃣ 量量你的文件塞不塞得進去</button>
</section>

<section id="s4">
  <span class="eyebrow">04 · AUTOREGRESSIVE</span>
  <h2>Autoregressive：一次吐一個 token</h2>
  <div class="tldr" style="--tc:var(--c4)">
    <b>一句話重點</b>：LLM 是<b>串行生成</b>——看著前文算「下一個 token 的機率分布」、
    抽一個、接上、再算下一個。這是所有推理加速技術要解的瓶頸。
  </div>
  <p>
    你看到 ChatGPT 的回答一個字一個字蹦出來，不是打字動畫，
    是模型<b>真的一次只算一個 token</b>。每一步都是一次完整的前向計算，
    所以：輸出越長越慢（串行，沒法平行）、每一步都要重看整段前文
    （所以要 KV cache 來省重算）、同一題每次答案不完全一樣（因為是**抽樣**，
    不是查表）。右邊 4️⃣ 用一個迷你模型把這個迴圈拆給你看，
    連 <span class="kbd">temperature</span> 在調什麼都一目瞭然。
  </p>
  <p>串流輸出（邊生成邊顯示）就是把這個迴圈的每一步直接推到你眼前：</p>
  <div class="codeblock">from openai import OpenAI

client = OpenAI(base_url="http://localhost:11434/v1",  # Ollama 的本機端點
                api_key="ollama")
stream = client.chat.completions.create(
    model="llama3.1",
    messages=[{"role": "user", "content": "介紹一下台北"}],
    stream=True,                       # 一個 token 一個 token 送回來
)
for chunk in stream:
    print(chunk.choices[0].delta.content or "", end="")</div>
  <button class="golab" data-nb="4️⃣">到右邊 4️⃣ 親手轉一次生成迴圈</button>
</section>

<section id="s5">
  <span class="eyebrow">05 · 速查</span>
  <h2>本課名詞速查卡</h2>
  <p>發講義用的濃縮版——一個名詞一句話：</p>
  <table class="cheat">
    <tr><td class="t" style="color:var(--c1)">Token / Tokenizer</td>
        <td>模型處理文字的最小單位，直接影響<b>計費</b>與<b>上下文長度</b>；中文比英文吃 token（實測同義句 +70%）。</td></tr>
    <tr><td class="t" style="color:var(--c2)">Embedding</td>
        <td>把文字轉成<b>語意向量</b>，意思近＝距離近——RAG 與語意搜尋的地基。</td></tr>
    <tr><td class="t" style="color:var(--c3)">Context Window</td>
        <td>一次能看的 token 上限；超過的內容<b>根本沒進模型</b>，而且窗越長 KV cache 越大。</td></tr>
    <tr><td class="t" style="color:var(--c4)">Autoregressive</td>
        <td>一次吐一個 token 的<b>串行</b>生成——輸出慢的根源，也是所有加速技術要解的瓶頸。</td></tr>
  </table>
</section>

<section id="s6">
  <span class="eyebrow">06 · 實戰</span>
  <h2>換你動手</h2>
  <div class="ex">
    <span class="lv">LEVEL 1</span>
    <p>在右邊 1️⃣ 把「要切的詞」改成 <span class="kbd">wider</span>（語料裡沒有的字），合併次數拉到 10——它會被切成幾塊？為什麼不會「不認識就炸掉」？</p>
  </div>
  <div class="ex">
    <span class="lv">LEVEL 2</span>
    <p>在 4️⃣ 把 temperature 壓到 0.1、再拉到 2.0，各重抽五次。觀察：哪個設定下句子幾乎不變？「天」後面為什麼老是接「氣」？（提示：右邊 5️⃣ 的實驗區可以查任何一個字的下一字計數。）</p>
  </div>
  <div class="ex">
    <span class="lv">LEVEL 3</span>
    <p>在 2️⃣ 挑「一杯熱拿鐵咖啡」看最近鄰。先猜：最近的會是誰？再想：為什麼跟它同組的「草莓蛋糕」輸給不同組的句子？這件事對 RAG 檢索意味著什麼？</p>
  </div>
  <p style="font-size:13.5px;color:var(--ink-soft);margin-top:10px">卡住了？三題在 notebook 最後一格都有折疊解答——先自己做，再打開對照。</p>
  <button class="golab" data-nb="5️⃣">到右邊 5️⃣ 的實驗區開工</button>
</section>

<section id="quiz">
  <span class="eyebrow">07 · 驗收</span>
  <h2>情境測驗</h2>
  <p>離開前試試看：下面的情境都真的會遇到。每題選一個你認為的最佳做法，選了馬上看得到解釋。</p>
  <div data-quiz>

    <div class="quiz-q" data-answer="C">
      <p class="quiz-tag">Q1 <span class="qtype">情境題</span></p>
      <h3>你的客服機器人每月 API 帳單暴增。你發現 system prompt 是一段 3,000 字的中文規範，每一次對話的每一輪都會原封不動送一次。想先降成本，最該做的是？</h3>
      <div class="quiz-opts">
        <button type="button" class="quiz-opt" data-k="A">A. 把 system prompt 翻成英文就好——英文比較省 token</button>
        <button type="button" class="quiz-opt" data-k="B">B. 換一個上下文窗更大的模型，就不會一直重送</button>
        <button type="button" class="quiz-opt" data-k="C">C. 先算 token：3,000 中文字約 3,400 個 token，每輪都在重複計費——精簡規範內容、只留必要規則，再考慮供應商的 prompt caching</button>
        <button type="button" class="quiz-opt" data-k="D">D. 把 max_tokens 調小，限制模型輸出長度</button>
      </div>
      <div class="quiz-fb" aria-live="polite"><p>成本問題先換算成 token 帳：中文約 1 字 1.1 token（實測 o200k_base），3,000 字的 system prompt 每輪重送就是每輪多付 ~3,400 個 input token。正解是先讓要送的東西變少（精簡內容），再用快取讓重複的部分變便宜。A 方向存在但代價是改變行為與維護成本，而且省的是 30–40%，不如直接精簡；B 搞混了兩件事——窗多大跟「每輪要重送整段歷史」無關，API 是無狀態的，換大窗一樣重送；D 管的是輸出端，帳單暴增的主因在每輪重複的輸入端。</p></div>
    </div>

    <div class="quiz-q" data-answer="B">
      <p class="quiz-tag">Q2 <span class="qtype">情境題</span></p>
      <h3>你要幫公司的內部文件做搜尋。同事說：「用關鍵字比對就好，何必搞 embedding？」什麼情況下他是對的、什麼情況下你該堅持用 embedding？</h3>
      <div class="quiz-opts">
        <button type="button" class="quiz-opt" data-k="A">A. 任何情況都該用 embedding——它是新技術，全面比關鍵字強</button>
        <button type="button" class="quiz-opt" data-k="B">B. 查詢用語和文件用語一致（工單編號、專有名詞）時關鍵字就夠；使用者會換說法問（「怎麼退錢」vs 文件寫「退款政策」）時，embedding 才抓得到語意相近</button>
        <button type="button" class="quiz-opt" data-k="C">C. 文件是中文就要用 embedding，英文才適合關鍵字</button>
        <button type="button" class="quiz-opt" data-k="D">D. embedding 只適合圖片搜尋，文字搜尋一律關鍵字</button>
      </div>
      <div class="quiz-fb" aria-live="polite"><p>Embedding 的價值在「換個說法也找得到」：它把語意變成向量，「怎麼退錢」跟「退款政策」向量距離近，關鍵字比對卻一個字都對不上。反過來，查工單編號、精確料號這種一字不差的查詢，關鍵字（或倒排索引）又快又準，embedding 反而可能被語意相近的雜訊干擾——所以成熟的檢索系統常常兩路並用（hybrid search）。A 是把工具當信仰；C 語言跟該不該用向量無關；D 說反了，embedding 是文字檢索的主流地基（也有多模態版本，那是第 7 課的延伸）。</p></div>
    </div>

    <div class="quiz-q" data-answer="C">
      <p class="quiz-tag">Q3 <span class="qtype dx">錯誤診斷</span></p>
      <h3>同事把一整份長文件貼進 prompt 要模型摘要，API 回了下面的錯誤。他說「這模型壞了，昨天問答都正常」。最可能的原因是？</h3>
      <div class="codeblock">HTTP 400
This model's maximum context length is 16384 tokens. However, you
requested 64 output tokens and your prompt contains at least 16321
input tokens, for a total of at least 16385 tokens. Please reduce
the length of the input prompt or the number of requested output tokens.</div>
      <div class="quiz-opts">
        <button type="button" class="quiz-opt" data-k="A">A. API 服務當機了，等一下重試就好</button>
        <button type="button" class="quiz-opt" data-k="B">B. max_tokens 設 64 太小，調大就能解決</button>
        <button type="button" class="quiz-opt" data-k="C">C. 文件加上輸出額度超過了 16384 token 的上下文窗——模型沒壞，是輸入太長；把文件分段摘要，或換上下文窗更大的模型</button>
        <button type="button" class="quiz-opt" data-k="D">D. 文件是中文，模型不支援中文輸入</button>
      </div>
      <div class="quiz-fb" aria-live="polite"><p>錯誤訊息其實把帳算給你看了：輸入 16,321 ＋ 要求的輸出 64 ＝ 16,385，超過 16,384 的窗，一個 token 都不通融——這正是「上下文窗是硬上限」的具體長相（訊息為實測，2026-08）。昨天正常是因為昨天的輸入短。A 認錯症狀，400 是請求本身不合法，重試一萬次都一樣；B 方向剛好相反——調大 max_tokens 是把總帳加得更大，只會錯得更多；D 無中生有，訊息裡寫得清清楚楚是長度問題。正解就是訊息最後一句：減少輸入（分段、先裁剪無關段落），或換更大的窗。</p></div>
    </div>

    <div class="quiz-score" data-score></div>
  </div>
</section>

<div class="endnav">
  <a href="/genai-training/">
    <span class="tag">下一課</span>
    <b>模型是怎麼練成的：預訓練到 RLHF →</b>
  </a>
  <a href="/genai-intro/">
    <span class="tag">主題</span>
    <b>‹ 回「生成式 AI 導論」課程列表</b>
  </a>
</div>
"""

SCRIPT = r"""
/* ═══ hero 互動：真實 tokenizer 切片（資料來自 tiktoken o200k_base 實測，2026-08）═══
   「�」＝一個中文字被 byte-level BPE 剖成好幾塊，單塊解不回完整字元。 */
(function () {
  const SAMPLES = [
    { label: "英文句", text: "The quick brown fox jumps over the lazy dog.",
      pieces: ["The", " quick", " brown", " fox", " jumps", " over", " the", " lazy", " dog", "."],
      take: "44 個字元只切 <b>10 刀</b>——平均 4.4 個字元一塊。英文是 tokenizer 的主場。" },
    { label: "中文同義句", text: "敏捷的棕色狐狸跳過了那隻懶狗。",
      pieces: ["敏", "捷", "的", "�", "�", "色", "狐狸", "跳", "過", "了", "那", "�", "�", "�", "�", "狗", "。"],
      take: "同樣的意思，15 個字被切成 <b>17 塊</b>——紅色的「�」是一個中文字被剖成好幾塊 byte。<b>同內容中文多花約 70% token</b>＝多 70% 的錢與上下文。" },
    { label: "罕見長英文字", text: "internationalization",
      pieces: ["international", "ization"],
      take: "20 個字元只要 <b>2 塊</b>：這個詞夠常見，BPE 早就把它黏成大塊了。" },
    { label: "中文術語", text: "生成式人工智慧",
      pieces: ["生成", "式", "人工", "智慧"],
      take: "常見中文詞也會被黏成雙字塊（「生成」「人工」「智慧」）——<b>常見度決定刀工</b>，語言只是常見度的代理。" },
  ];
  const picks = document.getElementById("tok-picks");
  const chips = document.getElementById("tok-chips");
  const stat = document.getElementById("tok-stat");
  const src = document.getElementById("tok-src");
  if (!picks) return;
  let cur = 0;
  SAMPLES.forEach((s, i) => {
    const b = document.createElement("button");
    b.type = "button";
    b.className = "pick";
    b.textContent = s.label;
    b.addEventListener("click", () => { cur = i; render(); });
    picks.appendChild(b);
  });
  function esc(t) { return t.replace(/&/g, "&amp;").replace(/</g, "&lt;"); }
  function render() {
    const s = SAMPLES[cur];
    picks.querySelectorAll(".pick").forEach((el, i) => el.classList.toggle("on", i === cur));
    chips.innerHTML = s.pieces.map((p) =>
      `<span class="chip${p === "�" ? " byte" : ""}">${esc(p)}</span>`).join("");
    stat.innerHTML = `「${esc(s.text)}」→ <b class="n">${s.pieces.length}</b> 個 token。 ${s.take}`;
    src.textContent = "實測：tiktoken o200k_base（GPT-4o／o 系列），2026-08。";
  }
  render();
})();
"""
