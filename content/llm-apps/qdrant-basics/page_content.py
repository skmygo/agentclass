"""課程頁內容區（純常數）。改完跑：python3 .claude/skills/make-lesson/scripts/page-fill.py content/llm-apps/qdrant-basics
build.sh 不會部署這個檔；它是 index.html 內容區的正本。"""

TITLE = "Qdrant：向量資料庫，記憶體裡就能跑"
DESCRIPTION = "用 QdrantClient(':memory:') 一行起一個向量資料庫：collection／point／payload、最近鄰查詢、過濾、三種距離度量，最後換成 LiteLLM 的真 embedding 用自然語言查菜單。"
NB = "https://molab.marimo.io/github/skmygo/agentclass/blob/main/content/llm-apps/qdrant-basics/qdrant-basics_ext.py"
VIDEO = "https://youtu.be/G0Nm5rbhAbY"  # 課程影片（YouTube；video/upload.py 上傳）

STYLE = r"""
  /* 語義色：藍＝查詢向量、橘＝命中（最近鄰）、綠＝過濾條件、紅＝辣度 */
  :root { --c1: #4C72B0; --c2: #DD8452; --c3: #55A868; --cut: #C44E52; }
  a.golab { text-decoration: none; display: inline-flex; align-items: center; gap: 8px; }

  /* hero：口味空間 */
  #vq-demo .ctrls { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px 16px; margin-bottom: 8px; }
  #vq-demo .ctrls label { font-size: 12.5px; font-weight: 800; display: flex; flex-direction: column; gap: 4px; }
  #vq-demo .ctrls input[type=range] { width: 100%; accent-color: var(--ink); }
  #vq-demo .opts { display: flex; gap: 14px; align-items: center; font-size: 13px; margin: 6px 0 10px; flex-wrap: wrap; }
  #vq-demo .opts label { display: inline-flex; gap: 6px; align-items: center; font-weight: 700; }
  #vq-demo svg text { font-family: var(--sans); font-size: 11px; fill: var(--ink); }
  #vq-demo svg .axis { stroke: var(--ink); stroke-width: 1.2; }
  #vq-demo svg .dish { stroke: var(--ink); stroke-width: 1.5; fill: #fff; transition: r .2s, fill .2s, opacity .2s; }
  #vq-demo svg .dish.hit { fill: var(--c2); }
  #vq-demo svg .dish.dim { opacity: .25; }
  #vq-demo svg .q { fill: var(--c1); stroke: var(--ink); stroke-width: 2; }
  #vq-demo svg .link { stroke: var(--c2); stroke-width: 2; stroke-dasharray: 4 3; }
  #vq-demo .top { display: flex; gap: 8px; flex-wrap: wrap; font-size: 13px; font-family: var(--mono); }
  #vq-demo .top span { background: var(--chip-bg); border-radius: 7px; padding: 4px 10px; border: 1.5px solid var(--c2); }
  #vq-demo .top span:first-child { background: var(--c2); color: #fff; }
  @media (max-width: 560px) { #vq-demo .ctrls { grid-template-columns: 1fr; } }

  table.cmp { width: 100%; border-collapse: collapse; font-size: 13.5px; margin: 14px 0; }
  table.cmp th, table.cmp td { border-bottom: 1px solid var(--grid); padding: 8px 10px; text-align: left; vertical-align: top; }
  table.cmp th { font-size: 12px; letter-spacing: .04em; color: var(--ink-soft); }
  .kbd { font-family: var(--mono); background: var(--chip-bg); padding: 1px 6px; border-radius: 5px; font-size: 13px; }
"""

WRAP = r"""
<section id="hero">
  <span class="eyebrow">QDRANT · VECTOR DATABASE · IN-MEMORY</span>
  <h1>Qdrant：向量資料庫，<br>記憶體裡就能跑</h1>
  <p style="margin-top:18px">
    一般資料庫回答「<b>等於</b>什麼」：<span class="kbd">WHERE name = '紅茶'</span>。
    向量資料庫回答「<b>最像</b>什麼」：給一個向量，找出最近的幾筆。RAG、推薦、語意搜尋的核心都是這個問題。
    先用人看得懂的 3 維「口味向量」體會一下——拉桿組出你想吃的口味，看它推薦什麼：
  </p>

  <div class="hero-demo" id="vq-demo">
    <div class="ctrls">
      <label>sweet 甜 <span id="vq-sw-v">0.20</span><input type="range" id="vq-sw" min="0" max="1" step="0.05" value="0.2"></label>
      <label>sour 酸 <span id="vq-so-v">0.70</span><input type="range" id="vq-so" min="0" max="1" step="0.05" value="0.7"></label>
      <label>spicy 辣 <span id="vq-sp-v">0.90</span><input type="range" id="vq-sp" min="0" max="1" step="0.05" value="0.9"></label>
    </div>
    <div class="opts">
      <label><input type="checkbox" id="vq-drink"> 只看飲料（payload 過濾）</label>
      <span style="color:var(--ink-soft)">距離：Cosine（只看方向）</span>
    </div>
    <svg id="vq-svg" viewBox="0 0 520 300" role="img" aria-label="taste space"></svg>
    <div class="top" id="vq-top"></div>
  </div>

  <p class="note">
    notebook 裡這八道菜會真的存進 Qdrant——<span class="kbd">QdrantClient(":memory:")</span> 一行起一個完整的向量資料庫，
    API 跟正式伺服器一模一樣；最後一節再把口味向量換成真的 embedding。
  </p>
</section>

<section id="s1">
  <span class="eyebrow">01 · 三個概念</span>
  <h2>Collection、Point、Upsert</h2>
  <div class="codeblock">from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct

qdrant = QdrantClient(":memory:")                      # 整個資料庫在記憶體裡
qdrant.create_collection("dishes",
    vectors_config=VectorParams(size=3, distance=Distance.COSINE))   # 幾維、什麼距離
qdrant.upsert("dishes", points=[
    PointStruct(id=0, vector=[0.9, 0.1, 0.0], payload={"name": "珍珠奶茶", "kind": "drink", "price": 60}),
    ...
])
hits = qdrant.query_points("dishes", query=[0.2, 0.7, 0.9], limit=3).points   # 最近的 3 個</div>
  <p>
    <b>Collection</b> 是一張表，建立時就要說定向量幾維、用什麼距離；<b>Point</b> 是一筆資料＝
    <span class="kbd">id</span>＋<span class="kbd">vector</span>＋<span class="kbd">payload</span>（任意 JSON，放原始資訊）；
    <b>Upsert</b> 寫入、同 id 覆蓋。查詢用 <span class="kbd">query_points</span>，每個命中帶 <span class="kbd">score</span>
    （Cosine 模式 1.0＝方向完全相同）。實測查「酸辣」<span class="kbd">[0.2, 0.7, 0.9]</span>：
    酸辣粉 0.995、泰式酸辣湯 0.982、麻辣鍋 0.898。
    把 <span class="kbd">":memory:"</span> 換成 <span class="kbd">"http://localhost:6333"</span> 就是連正式伺服器，其他一個字不用改。
  </p>
  <a class="golab" href="__NB__" target="_blank" rel="noopener">到 notebook 的 1️⃣–3️⃣ 節：口味向量、建庫、拉桿查詢</a>
</section>

<section id="s2">
  <span class="eyebrow">02 · 過濾與度量</span>
  <h2>相似度＋條件同時成立；三種「像」的算法</h2>
  <p>
    「我想喝酸酸辣辣的<b>飲料</b>」——向量負責酸辣，payload 過濾負責飲料：
    <span class="kbd">query_filter=Filter(must=[FieldCondition(key="kind", match=MatchValue(value="drink"))])</span>。
    Qdrant 是<b>先篩再排</b>，不是撈前 k 名再丟掉不合的（那樣可能一筆都不剩）。
    實測結果：檸檬紅茶 0.60、蜂蜜檸檬 0.50、珍珠奶茶 0.24——沒有飲料真的辣，所以分數都不高，
    但在「飲料」子集合裡檸檬紅茶確實最接近。<b>分數是相對的，門檻要看資料</b>。
  </p>
  <table class="cmp">
    <tr><th>distance</th><th>怎麼算</th><th>查「酸辣」的前 3（實測）</th></tr>
    <tr><td>Cosine</td><td>只看方向、不看長度（文字 embedding 幾乎都用它）</td><td>酸辣粉 0.995 → 泰式酸辣湯 0.982 → 麻辣鍋 0.898</td></tr>
    <tr><td>Euclid</td><td>直線距離，<b>越小越近</b></td><td>酸辣粉 0.141 → 泰式酸辣湯 0.224 → 麻辣鍋 0.512</td></tr>
    <tr><td>Dot</td><td>內積；向量都正規化成長度 1 時等於 Cosine</td><td>酸辣粉 1.23 → 泰式酸辣湯 1.23 → 麻辣鍋 1.02</td></tr>
  </table>
  <a class="golab" href="__NB__" target="_blank" rel="noopener">到 notebook 的 4️⃣–5️⃣ 節：Filter、Range、三種度量並排</a>
</section>

<section id="s3">
  <span class="eyebrow">03 · 換真的向量</span>
  <h2>用自然語言查菜單</h2>
  <p>
    口味向量是手填的，真實應用的向量來自 embedding 模型。用第 1 課的 gateway 呼叫
    <span class="kbd">qwen3-embedding-0.6b</span>，八道菜的<b>名字</b>各變成 1024 維向量，存進一個新 collection（<span class="kbd">size=1024</span>）。
    查詢也要先經過<b>同一個</b>模型變成向量，再丟給 Qdrant。沒有任何關鍵字比對——實測：
  </p>
  <table class="cmp">
    <tr><th>查詢</th><th>top-3（score）</th></tr>
    <tr><td>想喝冰冰甜甜的飲料</td><td>珍珠奶茶 0.59 → 檸檬紅茶 0.56 → 泰式酸辣湯 0.49</td></tr>
    <tr><td>辣的湯</td><td>泰式酸辣湯 0.78 → 麻辣鍋 0.70 → 檸檬紅茶 0.61</td></tr>
    <tr><td>飯後甜點</td><td>焦糖布丁 0.65 → 檸檬紅茶 0.62 → 麻辣鍋 0.61</td></tr>
  </table>
  <p>
    注意尺度變了：真實 embedding 的「相關」大約 0.5–0.8，「不相關」也有 0.3–0.5，不像口味向量那麼極端。
    做 RAG 時門檻要用自己的資料實測。
  </p>
  <a class="golab" href="__NB__" target="_blank" rel="noopener">到 notebook 的 6️⃣ 節：真 embedding、打你自己的句子</a>
</section>

<section id="s4">
  <span class="eyebrow">04 · 實戰</span>
  <h2>換你動手</h2>
  <div class="ex">
    <span class="lv">LEVEL 1</span>
    <p>加兩道你喜歡的菜（自己填口味向量），看拉桿拉到哪裡它們會被推薦。</p>
  </div>
  <div class="ex">
    <span class="lv">LEVEL 2</span>
    <p>複合條件：<span class="kbd">kind == "food"</span> 而且 <span class="kbd">price &lt;= 150</span>，再試 <span class="kbd">should</span> 與 <span class="kbd">must_not</span>。</p>
  </div>
  <div class="ex">
    <span class="lv">LEVEL 3</span>
    <p>把 kind 與 price 也存進真向量的 collection，做「100 元以內、跟『提神』最相關的東西」。想一想：為什麼查詢與資料必須用同一個 embedding 模型？</p>
  </div>
  <p style="font-size:13.5px;color:var(--ink-soft);margin-top:10px">卡住了？每一題在 notebook 末節都有折疊解答——先自己做，再打開對照。</p>
</section>

<section id="quiz">
  <span class="eyebrow">05 · 驗收</span>
  <h2>情境測驗</h2>
  <p>離開前試試看：下面的情境都真的會遇到。每題選一個你認為的最佳做法，選了馬上看得到解釋。</p>
  <div data-quiz>

    <div class="quiz-q" data-answer="B">
      <p class="quiz-tag">Q1 <span class="qtype">情境題</span></p>
      <h3>你用 <span class="kbd">QdrantClient(":memory:")</span> 把菜單搜尋的雛形做完了，現在要上正式環境，Qdrant 伺服器已經用 Docker 起好。程式該怎麼改？</h3>
      <div class="quiz-opts">
        <button type="button" class="quiz-opt" data-k="A">A. 把查詢程式改寫成伺服器版的 API——記憶體模式只是模擬，介面不一樣</button>
        <button type="button" class="quiz-opt" data-k="B">B. 把 <code>":memory:"</code> 換成 <code>"http://localhost:6333"</code>，其他程式一個字不用改</button>
        <button type="button" class="quiz-opt" data-k="C">C. 先把記憶體裡的資料匯出成 JSON，逐筆轉成伺服器格式再匯入</button>
        <button type="button" class="quiz-opt" data-k="D">D. 不用改——<code>":memory:"</code> 在正式環境也能用，把機器記憶體加大就好</button>
      </div>
      <div class="quiz-fb" aria-live="polite"><p>記憶體模式的賣點就是 API 跟正式伺服器一模一樣——換掉連線字串那一行，建庫、upsert、查詢的程式原封不動重跑一次就上線。A 是誤解，不存在「兩套 API」；C 多此一舉，沒有什麼「伺服器格式」要轉，重跑 upsert 就是匯入；D 有致命副作用：記憶體模式的資料活在 Python 行程裡，行程一結束就消失，只適合學習、測試、demo。</p></div>
    </div>

    <div class="quiz-q" data-answer="D">
      <p class="quiz-tag">Q2 <span class="qtype">情境題</span></p>
      <h3>使用者要「酸酸辣辣的<b>飲料</b>」。八道菜已經存在 <span class="kbd">dishes</span> collection，payload 裡有 <span class="kbd">kind</span> 欄位。最佳做法是？</h3>
      <div class="quiz-opts">
        <button type="button" class="quiz-opt" data-k="A">A. 查詢時多撈一點（<code>limit=10</code>），拿回來後自己把不是 drink 的丟掉</button>
        <button type="button" class="quiz-opt" data-k="B">B. 先把所有 <code>kind == "drink"</code> 的點撈出來，自己用 numpy 算 cosine 排序</button>
        <button type="button" class="quiz-opt" data-k="C">C. 飲料和食物分成兩個 collection，要查哪類就查哪個庫</button>
        <button type="button" class="quiz-opt" data-k="D">D. <code>query_points</code> 時同時給 <code>query_filter</code>（<code>must</code> 裡放 <code>kind == "drink"</code> 的條件）——向量管口味、過濾管類別</button>
      </div>
      <div class="quiz-fb" aria-live="polite"><p>向量負責「像不像」、payload 過濾負責「是不是」，而且 Qdrant 是先篩再排——在飲料子集合裡找最接近酸辣的。實測第一名是檸檬紅茶 0.60：沒有飲料真的辣，分數不高，但確實是子集合裡最近的。A 正是「先排再篩」的陷阱：酸辣的前三名（0.995／0.982／0.898）全是食物，撈回來一過濾可能一筆不剩；B 做得到，但把向量資料庫的本職（算距離、排序）搬回自己手上，資料一多就慢；C 能動但有副作用——類別一多 collection 就爆增，跨類別查詢還得自己合併。</p></div>
    </div>

    <div class="quiz-q" data-answer="A">
      <p class="quiz-tag">Q3 <span class="qtype dx">錯誤診斷</span></p>
      <h3>你把 collection 改用 <span class="kbd">Distance.EUCLID</span> 重建，同樣查「酸辣」。Cosine 時酸辣粉是 0.995，現在只剩 0.141——資料壞了嗎？</h3>
      <div class="codeblock">query = [0.2, 0.7, 0.9]
酸辣粉 (0.141) → 泰式酸辣湯 (0.224) → 麻辣鍋 (0.512)</div>
      <div class="quiz-opts">
        <button type="button" class="quiz-opt" data-k="A">A. 沒壞：Euclid 的 score 是「距離」，越小越近，0.141 正代表最近——排序跟 Cosine 一致</button>
        <button type="button" class="quiz-opt" data-k="B">B. upsert 時向量存壞了，重新 upsert 一次就會恢復</button>
        <button type="button" class="quiz-opt" data-k="C">C. 查詢向量忘了正規化成長度 1，分數被壓低了</button>
        <button type="button" class="quiz-opt" data-k="D">D. Euclid 的分數要自己換算成 0–1 才能跟 Cosine 比，0.141 換算後就是 0.99</button>
      </div>
      <div class="quiz-fb" aria-live="polite"><p>建 collection 時選的 <code>distance</code> 決定 score 的意義：Cosine 是相似度（1 ＝ 同方向）、Euclid 是直線距離（0 ＝ 同一點、<b>越小越近</b>）。排序一致、數字方向相反，完全正常。B 症狀不符——向量存壞的話排序也會亂，這裡前三名跟 Cosine 一模一樣；C 想到別的度量去了——正規化是 Dot 的事（向量都正規化成長度 1 時 Dot ＝ Cosine），解釋不了這個數字；D 沒有這種換算，把不同度量的分數拿來互比本身就是誤用。</p></div>
    </div>

    <div class="quiz-q" data-answer="C">
      <p class="quiz-tag">Q4 <span class="qtype dx">錯誤診斷</span></p>
      <h3>你的 <span class="kbd">dishes_real</span> 是用 <span class="kbd">qwen3-embedding-0.6b</span>（1024 維）建的。改用 <span class="kbd">nemotron-3-embed-1b</span> 算查詢向量，一查就炸。最可能的原因與正確修法是？</h3>
      <div class="codeblock">ValueError: shapes (8,1024) and (2048,) not aligned</div>
      <div class="quiz-opts">
        <button type="button" class="quiz-opt" data-k="A">A. 記憶體模式不支援 2048 維的大向量——連正式伺服器就不會炸</button>
        <button type="button" class="quiz-opt" data-k="B">B. 查詢向量截掉後半、留前 1024 維，維度就對上了</button>
        <button type="button" class="quiz-opt" data-k="C">C. 新模型回 2048 維、collection 是 1024 維；要換 embedding 模型，就得用新模型把整個 collection 重建，查詢也全走新模型</button>
        <button type="button" class="quiz-opt" data-k="D">D. 維度不合沒錯——換一個同樣輸出 1024 維的模型來算查詢向量，就能繼續用舊的 collection</button>
      </div>
      <div class="quiz-fb" aria-live="polite"><p>維度對不上只是最先炸出來的症狀（正式伺服器一樣擋，回 400 <code>Wrong input: Vector dimension error</code>）。根本原因是：<b>索引用哪個模型，查詢就必須用同一個模型</b>——不同模型的座標軸意義完全不同。B 截斷後查得動，但距離毫無意義；D 是最危險的陷阱：就算維度剛好相同，兩個模型的向量空間也對不起來，查出來的「最近鄰」等於亂數；A 方向錯了，這不是記憶體模式的限制。換模型的正確代價，就是整個 collection 用新模型重新 embedding 重建。</p></div>
    </div>

    <div class="quiz-q" data-answer="B">
      <p class="quiz-tag">Q5 <span class="qtype">情境題</span></p>
      <h3>你把真 embedding 的菜單搜尋接進客服機器人，想設一個 score 門檻把「不相關」的結果擋掉。最佳做法是？</h3>
      <div class="quiz-opts">
        <button type="button" class="quiz-opt" data-k="A">A. 設 0.9——Cosine 滿分是 1.0，低於 0.9 就當不相關</button>
        <button type="button" class="quiz-opt" data-k="B">B. 拿自己的資料實測：分別看「相關」與「不相關」查詢的分數分佈，把門檻定在兩群之間</button>
        <button type="button" class="quiz-opt" data-k="C">C. 不設門檻，永遠取 top-3——排序對了就好</button>
        <button type="button" class="quiz-opt" data-k="D">D. 改用 Euclid 距離，用「距離」設門檻比「相似度」直覺</button>
      </div>
      <div class="quiz-fb" aria-live="polite"><p>分數尺度跟資料、模型綁在一起：本課實測「相關」約 0.5–0.8、「不相關」也有 0.3–0.5，門檻只能從自己的分數分佈量出來。A 會把所有結果全部擋掉——實測最高分也才 0.78；C 能動但有副作用：庫裡根本沒有相關內容時，top-3 照樣把不相關的端出來（「飯後甜點」的第三名是麻辣鍋 0.61）；D 換度量只是換一把尺，尺度一樣要實測，而且文字 embedding 幾乎都用 Cosine。</p></div>
    </div>

    <div class="quiz-score" data-score></div>
  </div>
</section>

<div class="endnav">
  <a href="/rag-zh/">
    <span class="tag">下一課</span>
    <b>RAG：讓模型先翻手冊再回答 →</b>
  </a>
  <a href="/llm-apps/">
    <span class="tag">主題</span>
    <b>‹ 回「學 LLM 應用開發」課程列表</b>
  </a>
</div>
"""

SCRIPT = r"""
/* ═══ hero 互動：口味空間的最近鄰（純 JS，跟 notebook 同一組資料）═══ */
(function () {
  const DISHES = [
    ["珍珠奶茶", [0.90, 0.10, 0.00], "drink"], ["檸檬紅茶", [0.50, 0.80, 0.00], "drink"],
    ["蜂蜜檸檬", [0.80, 0.60, 0.00], "drink"], ["焦糖布丁", [0.95, 0.05, 0.00], "dessert"],
    ["糖醋排骨", [0.70, 0.60, 0.10], "food"], ["泰式酸辣湯", [0.20, 0.80, 0.70], "food"],
    ["酸辣粉", [0.10, 0.70, 0.80], "food"], ["麻辣鍋", [0.10, 0.20, 0.95], "food"],
  ];
  const svg = document.getElementById("vq-svg");
  const ids = ["sw", "so", "sp"].map(k => document.getElementById("vq-" + k));
  const vals = ["sw", "so", "sp"].map(k => document.getElementById("vq-" + k + "-v"));
  const drink = document.getElementById("vq-drink");
  const top = document.getElementById("vq-top");
  const X = v => 40 + v * 440, Y = v => 270 - v * 240;
  const cos = (a, b) => { const d = a[0]*b[0]+a[1]*b[1]+a[2]*b[2]; const na = Math.hypot(...a), nb = Math.hypot(...b); return na && nb ? d / (na * nb) : 0; };
  function render() {
    const q = ids.map(i => +i.value);
    vals.forEach((el, i) => el.textContent = q[i].toFixed(2));
    const pool = DISHES.map((d, i) => ({ i, name: d[0], v: d[1], kind: d[2], s: cos(q, d[1]) }))
      .filter(d => !drink.checked || d.kind === "drink").sort((a, b) => b.s - a.s).slice(0, 3);
    const hit = new Set(pool.map(p => p.i));
    let out = `<line class="axis" x1="40" y1="270" x2="490" y2="270"/><line class="axis" x1="40" y1="270" x2="40" y2="20"/>
      <text x="480" y="290" text-anchor="end">sweet →</text><text x="10" y="24">sour ↑</text>
      <text x="300" y="16" text-anchor="middle" style="font-size:10.5px;fill:var(--ink-soft)">circle size = spicy · orange = top-3 by cosine</text>`;
    pool.forEach(p => { out += `<line class="link" x1="${X(q[0])}" y1="${Y(q[1])}" x2="${X(p.v[0])}" y2="${Y(p.v[1])}"/>`; });
    DISHES.forEach((d, i) => {
      const dim = drink.checked && d[2] !== "drink";
      out += `<circle class="dish ${hit.has(i) ? "hit" : ""} ${dim ? "dim" : ""}" cx="${X(d[1][0])}" cy="${Y(d[1][1])}" r="${6 + d[1][2] * 12}"/>
        <text x="${X(d[1][0]) + 10}" y="${Y(d[1][1]) - 8}" ${dim ? 'opacity=".35"' : ""}>${d[0]}</text>`;
    });
    out += `<circle class="q" cx="${X(q[0])}" cy="${Y(q[1])}" r="7"/><text x="${X(q[0]) + 10}" y="${Y(q[1]) + 16}" style="fill:var(--c1);font-weight:800">query</text>`;
    svg.innerHTML = out;
    top.innerHTML = pool.map((p, k) => `<span>#${k + 1} ${p.name} ${p.s.toFixed(3)}</span>`).join("");
  }
  ids.forEach(i => i.addEventListener("input", render));
  drink.addEventListener("change", render);
  render();
})();
"""

PANEL_STEPS = """
        <li>登入 molab（GitHub / Google）</li>
        <li>開啟課程 notebook，<b>Fork 成自己的副本</b>即可編輯</li>
        <li>從第一格往下全部執行（首次安裝套件約 1 分鐘）——<b>免費 CPU 環境即可</b>，不需要 GPU</li>
"""
