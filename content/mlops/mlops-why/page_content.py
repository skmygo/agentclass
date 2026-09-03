"""課程頁內容區（純常數）。改完跑：python3 .claude/skills/make-lesson/scripts/page-fill.py content/mlops/mlops-why
build.sh 不會部署這個檔；它是 index.html 內容區的正本。"""

TITLE = "為什麼需要 MLOps：模型會過期"
DESCRIPTION = "模型不會當機，它會安靜地爛掉。用可拉桿的 24 個月模擬親眼看準確率從 0.94 掉到 0.45，比較不重訓／定期重訓／監控觸發三種策略的成績與成本，再看「標籤遲到」怎麼讓監控輸給最笨的定期重訓——這就是 MLOps 要解決的問題。"

STYLE = r"""
  /* 語義色：紅＝不重訓（放著爛）、藍＝定期重訓、綠＝監控觸發、橘＝標籤遲到、紫＝資料漂移 */
  :root { --c1: #4C72B0; --c2: #DD8452; --c3: #55A868; --cut: #C44E52; --c4: #8172B3; }

  /* hero：重訓時間軸 */
  #mw .ctrl label { font-size: 13.5px; font-weight: 800; min-width: 152px; }
  #mw .ctrl label b { font-family: var(--mono); }
  #mw .btns { display: flex; gap: 10px; flex-wrap: wrap; margin-top: 12px; }
  #mw .btns button {
    font-family: inherit; font-size: 13.5px; font-weight: 800; cursor: pointer;
    padding: 8px 16px; border-radius: 999px; border: 1.5px solid var(--ink);
    background: var(--ink); color: #fff;
  }
  #mw .btns button.ghost { background: var(--panel); color: var(--ink); }
  #mw .btns button:hover { background: var(--c3); border-color: var(--c3); color: #fff; }
  #mw .verdict b { font-size: 20px; font-family: var(--mono); }
  #mw .verdict .bad { color: var(--cut); }
  #mw .verdict .good { color: var(--c3); }
  #mw .fine { font-size: 12.5px; color: var(--ink-soft); margin: 12px 0 0; line-height: 1.7; }
  #mw text { font-family: var(--sans); }

  table.cmp { width: 100%; border-collapse: collapse; font-size: 13.5px; margin: 14px 0; }
  table.cmp th, table.cmp td { border-bottom: 1px solid var(--grid); padding: 8px 10px; text-align: left; vertical-align: top; }
  table.cmp th { font-size: 12px; letter-spacing: .04em; color: var(--ink-soft); }
  table.cmp td.num { font-family: var(--mono); font-weight: 800; text-align: right; white-space: nowrap; }
  table.cmp tr.key td { background: var(--chip-bg); }
  .kbd { font-family: var(--mono); background: var(--chip-bg); padding: 1px 6px; border-radius: 5px; font-size: 13px; }
  .dot { display: inline-block; width: 10px; height: 10px; border-radius: 3px; margin-right: 5px; vertical-align: -1px; }
"""

WRAP = r"""
<section id="hero">
  <span class="eyebrow">WHY MLOPS · 前導 · 00</span>
  <h1>為什麼需要 MLOps：<br>模型會過期</h1>
  <p style="margin-top:18px">
    模型很少「壞掉」。它不會當機、不會噴錯誤、不會在半夜叫醒你。
    它只是<b>每天照常回答</b>，而答案越來越常是錯的——因為<b>世界變了，模型沒變</b>。
  </p>
  <p>
    下面是一顆真的模型的 24 個月：第 0 個月訓練好上線，之後沒人動它。
    你可以在任何一個月按下「重訓」，看曲線怎麼跳回去、又怎麼開始往下掉。
    多按幾次，你就會問出這堂課要回答的問題：<b>到底該什麼時候按？</b>
  </p>

  <div class="hero-demo" id="mw">
    <svg id="mw-svg" viewBox="0 0 440 214" role="img"
         aria-label="模型準確率隨月份下降的折線圖，可加入重訓">
      <g id="mw-grid"></g>
      <path id="mw-base" fill="none" stroke="var(--cut)" stroke-width="1.4"
            stroke-dasharray="4 4" opacity="0.55"></path>
      <path id="mw-line" fill="none" stroke="var(--c3)" stroke-width="2.6"
            stroke-linejoin="round"></path>
      <g id="mw-marks"></g>
    </svg>

    <div class="ctrl">
      <label for="mw-month">在第 <b id="mw-month-val">6</b> 個月重訓</label>
      <input type="range" id="mw-month" min="1" max="22" step="1" value="6">
    </div>
    <div class="btns">
      <button type="button" id="hero-retrain">重訓一次</button>
      <button type="button" id="mw-reset" class="ghost">全部清掉</button>
    </div>

    <div class="verdict" id="mw-verdict"></div>

    <p class="fine">
      每一個點都是實驗場模擬跑出來的實測值（每月 300 位新客戶、6 個特徵，
      每次重訓都真的重新訓練一次）。虛線是完全不重訓的下場。
    </p>
  </div>

  <p class="note">
    這一課的實驗場是真的 Python（在你的瀏覽器裡跑，不用安裝任何東西）。
    首次載入約需 30–60 秒，正好夠你讀完第 1 節。裡面沒有程式碼要讀——
    每一段都有滑桿，拉一下，整整 24 個月的模擬就會重跑一次。
  </p>
</section>

<section id="s1">
  <span class="eyebrow">01 · 安靜地爛掉</span>
  <h2>模型上線那天，就開始過期</h2>
  <p>
    這個模擬裡有一間公司在做「客戶會不會流失」的預測。第 0 個月訓練好模型、上線，
    每個月有 300 位新客戶進來，模型逐一判斷，月底對答案，得到那個月的準確率。
    模型完全沒有變——變的是<b>世界</b>：客戶的組成、競爭對手、什麼樣的人會走。
  </p>
  <table class="cmp">
    <tr><th>上線後</th><th style="text-align:right">那個月的準確率</th><th>感覺</th></tr>
    <tr><td>第 1 個月</td><td class="num">0.94</td><td>驗收通過，大家很開心</td></tr>
    <tr><td>第 6 個月</td><td class="num">0.79</td><td>有人覺得怪怪的，但說不上來</td></tr>
    <tr><td>第 12 個月</td><td class="num">0.68</td><td>業務開始抱怨名單不準</td></tr>
    <tr class="key"><td>第 23 個月</td><td class="num">0.45</td><td>比丟銅板還差</td></tr>
  </table>
  <p>
    24 個月平均 <b>0.660</b>。而這段期間，系統監控是全綠的：沒有當機、沒有錯誤、
    沒有告警。<b>這是機器學習系統最危險的失敗方式——它會安靜地爛掉</b>，
    而且通常是業務先發現，不是工程師。
  </p>
  <p class="note">
    傳統軟體壞掉會噴例外，你馬上知道。模型「壞掉」的樣子是準確率慢慢滑落，
    你只有在<b>持續量它</b>的時候才看得見。這句話就是整個 MLOps 的起點。
  </p>
  <button class="golab" data-nb="1️⃣">到實驗場看這條下墜曲線</button>
</section>

<section id="s2">
  <span class="eyebrow">02 · 兩種漂移</span>
  <h2>世界有兩種變法，只有一種會讓準確率掉</h2>
  <p>
    「世界變了」其實包含兩件完全不同的事，分清楚它們，你才知道要監控什麼：
  </p>
  <table class="cmp">
    <tr><th>名字</th><th>變的是什麼</th><th>比喻</th></tr>
    <tr><td><span class="dot" style="background:var(--c4)"></span><b>資料漂移</b></td>
        <td>進來的<b>資料</b>變了，但「什麼答案才對」的規則沒變</td>
        <td>考卷的題型分佈變了（以前一半代數一半幾何，現在九成幾何），解法還是同一套</td></tr>
    <tr><td><span class="dot" style="background:var(--cut)"></span><b>概念漂移</b></td>
        <td><b>規則本身</b>變了</td>
        <td>同一題，標準答案改了</td></tr>
  </table>
  <p>
    實驗場的第 2️⃣ 節讓三個世界跑同一件事——訓練一次、之後不重訓——結果很反直覺：
  </p>
  <table class="cmp">
    <tr><th>世界</th><th style="text-align:right">24 個月平均準確率</th><th>進來的資料有沒有變</th></tr>
    <tr><td>完全不變</td><td class="num">0.926</td><td>沒有</td></tr>
    <tr><td><b>只有資料漂移</b></td><td class="num" style="color:var(--c4)">0.945</td>
        <td>變很多（某特徵月均值 -0.08 → +1.56，流失比例 48% → 95%）</td></tr>
    <tr class="key"><td><b>概念漂移</b></td><td class="num" style="color:var(--cut)">0.660</td>
        <td>幾乎沒變</td></tr>
  </table>
  <ul>
    <li><b>只有資料漂移時，準確率沒掉</b>（0.945，甚至比世界完全不變的 0.926 還高一點點）。
      規則沒變，模型學到的那條界線還是對的，只是進來的人整批移到了它的一側。
      <b>準確率沒掉不代表沒事</b>——這個模型正在服務一群訓練時沒見過的客戶。</li>
    <li><b>概念漂移時，資料看起來一切正常。</b>你盯著輸入資料看到天亮也看不出異狀，
      準確率卻已經腰斬。</li>
  </ul>
  <p>
    這兩件事合起來，決定了監控要怎麼做：<b>資料漂移不需要標籤就看得見</b>
    （比對輸入分佈，今天就能算），它是早期警訊；而<b>概念漂移只有拿到標籤、
    算出準確率才會現形</b>——所以你必須有一個地方，持續記錄每個月的成績。
    沒有那份紀錄，你連「什麼時候開始掉的」都答不出來。
  </p>
  <button class="golab" data-nb="2️⃣">到實驗場比較三個世界</button>
</section>

<section id="s3">
  <span class="eyebrow">03 · 什麼時候重訓</span>
  <h2>三種策略：不重訓、定期重訓、監控觸發</h2>
  <p>
    知道模型會過期之後，只剩一個問題：<b>什麼時候重訓？</b>三種做法，
    在實驗場的 3️⃣ 節可以用滑桿即時比較（世界變化速度 0.12 時的實測）：
  </p>
  <table class="cmp">
    <tr><th>策略</th><th>做法</th><th style="text-align:right">平均準確率</th><th style="text-align:right">重訓次數</th></tr>
    <tr><td><span class="dot" style="background:var(--cut)"></span><b>不重訓</b></td>
        <td>訓練一次，永遠不動</td><td class="num">0.660</td><td class="num">0</td></tr>
    <tr><td><span class="dot" style="background:var(--c1)"></span><b>定期重訓</b></td>
        <td>每 3 個月重訓一次，不管準不準</td><td class="num">0.900</td><td class="num">7</td></tr>
    <tr class="key"><td><span class="dot" style="background:var(--c3)"></span><b>監控觸發</b></td>
        <td>準確率掉到 0.85 以下才重訓</td><td class="num">0.889</td><td class="num">4</td></tr>
  </table>
  <p>
    定期重訓的成績最高，但監控觸發<b>只用了 4 次重訓就拿到幾乎一樣的結果</b>。
    這就是這張表要一起看兩欄的原因：<b>重訓次數就是成本</b>——算力、工程師的時間、
    每一次上線都要承擔的風險。
  </p>
  <p>
    門檻該設多少？把實驗場的滑桿從 0.95 拉到 0.70，你會看到一條很清楚的取捨線：
  </p>
  <div class="codeblock">門檻 0.95  →  平均 0.916，重訓 23 次   ← 等於每個月都重訓
門檻 0.90  →  平均 0.903，重訓  7 次
門檻 0.85  →  平均 0.889，重訓  4 次
門檻 0.80  →  平均 0.870，重訓  3 次
門檻 0.70  →  平均 0.829，重訓  2 次</div>
  <p>
    從 0.85 拉到 0.95，多花 <b>19 次</b>重訓，平均準確率只多買到 <b>2.7 個百分點</b>。
    <b>門檻太高＝天天重訓，太低＝掉到很慘才救</b>——中間那個甜蜜點不在這堂課裡，
    在你自己的成本表：一次重訓要花多少錢，準確率掉一個百分點你要賠多少。
  </p>
  <p class="note">
    順帶一提，門檻拉到 0.95 的成績（0.916）跟「每 1 個月定期重訓」一模一樣——
    <b>門檻拉到極限，監控觸發就退化成定期重訓</b>，還多花了監控的力氣。
  </p>
  <button class="golab" data-nb="3️⃣">到實驗場拉三根滑桿比較策略</button>
</section>

<section id="s4">
  <span class="eyebrow">04 · 標籤總是遲到</span>
  <h2>你不會馬上知道自己錯了</h2>
  <p>
    上面的「監控觸發」偷藏了一個很甜的假設：<b>這個月準不準，這個月月底就知道</b>。
    真實世界很少這樣。你要等客戶真的解約、等帳單真的逾期、等病人真的回診，
    答案才會揭曉——<b>標籤晚幾個月是常態</b>。
  </p>
  <p>而標籤遲到會同時造成兩件事，第二件比第一件更傷：</p>
  <ol>
    <li><b>警報遲到</b>：第 12 個月的準確率，你第 15 個月才知道，那時已經爛了三個月。</li>
    <li><b>連教材都過期</b>：要重訓，只有「已經有標籤」的資料能用。你手上最新的有標籤資料
      也是三個月前的——<b>重訓出來的模型一出生就落後三個月</b>，很快又跌破門檻，
      於是再重訓一次。追著自己的影子跑。</li>
  </ol>
  <table class="cmp">
    <tr><th>標籤延遲</th><th style="text-align:right">平均準確率</th><th style="text-align:right">重訓次數</th></tr>
    <tr><td>當月就知道</td><td class="num">0.889</td><td class="num">4</td></tr>
    <tr><td>晚 3 個月</td><td class="num">0.851</td><td class="num">11</td></tr>
    <tr class="key"><td>晚 6 個月</td><td class="num" style="color:var(--c2)">0.796</td><td class="num" style="color:var(--c2)">14</td></tr>
  </table>
  <p>
    <b>又慢又忙</b>：準確率掉了 9 個百分點，重訓次數變成 3.5 倍。
    更難堪的是最後一列——延遲 6 個月的監控觸發（0.796），
    <b>已經輸給什麼都不看、每 6 個月固定重訓一次的 0.867</b>，而後者只重訓了 3 次。
  </p>
  <p class="note">
    所以真實專案的第一個問題往往不是「要用什麼演算法」，而是
    <b>「我的標籤多久會到？」</b>——這個數字決定了監控值不值得做、
    決定了你是不是該乾脆改用定期重訓，也決定了值不值得花錢買更快的標籤
    （人工抽樣標註、找一個提早看得到的代理指標）。
  </p>
  <button class="golab" data-nb="4️⃣">到實驗場拉標籤延遲</button>
</section>

<section id="s5">
  <span class="eyebrow">05 · 這個系列在做什麼</span>
  <h2>「監控觸發」要真的跑起來，需要五個零件</h2>
  <p>
    到這裡，正確答案已經浮出來了：<b>持續看著準確率，該重訓的時候重訓，
    而且要確定新模型真的比舊的好</b>。這句話講起來一秒，做起來需要五樣東西——
    每一樣正好是這個系列的一課：
  </p>
  <table class="cmp">
    <tr><th>你需要</th><th>沒有它會發生什麼</th><th>哪一課</th></tr>
    <tr><td>每次訓練的設定與指標<b>留得下紀錄、查得回來</b></td>
        <td>你不知道是第幾個月開始掉的，也不知道當時用了什麼參數</td>
        <td><a href="/mlflow-tracking/">01 MLflow 實驗追蹤</a></td></tr>
    <tr><td>模型有<b>版本</b>，新舊能比較，能一行換上去、換錯能退回</td>
        <td>重訓出一顆新模型，卻不敢換，因為不知道它比舊的好還壞</td>
        <td><a href="/mlflow-registry/">02 Models 與 Registry</a></td></tr>
    <tr><td>「取資料 → 訓練 → 評估」是一張<b>看得懂的圖</b>，不是散落的腳本</td>
        <td>誰先誰後靠人腦記，換人接手就斷掉</td>
        <td><a href="/dagster-assets/">03 Dagster 軟體定義資產</a></td></tr>
    <tr><td>有東西會在<b>對的時間按下重訓</b>（排程，或偵測到就觸發）</td>
        <td>監控會響，但沒有人按</td>
        <td><a href="/dagster-automation/">04 Dagster 自動化</a></td></tr>
    <tr class="key"><td>上線前有<b>品質閘</b>，比舊版差就擋下來</td>
        <td>重訓反而把線上弄壞——<b>重訓不保證變好</b></td>
        <td>05 Dagster × MLflow 管線</td></tr>
  </table>
  <p>
    最後一列特別值得留意，因為<b>這堂課的模擬對重訓太仁慈了</b>：這裡的重訓永遠成功、
    永遠拿得到乾淨的新資料、訓出來永遠不比舊的差。真實世界三件事都不保證——
    你在第 6️⃣ 節把世界變化速度拉到 0 就會親眼看到，重訓有時候是純成本，
    有時候還會讓成績變差一點。所以完整的自動重訓，最後一步一定是
    「<b>先擋下來，通過才換上去</b>」。
  </p>
  <p>
    「MLOps」這個詞聽起來很大，但它要解決的就是上面這五件事。
    接下來五堂課，你會親手把它們一個一個做出來。
  </p>
  <button class="golab" data-nb="5️⃣">到實驗場看這張對照表</button>
</section>

<section id="s6">
  <span class="eyebrow">06 · 實戰</span>
  <h2>換你動手</h2>
  <p>
    實驗場的 6️⃣ 節有四根滑桿，把前面所有旋鈕放在一起：世界變化速度、定期重訓的週期、
    監控觸發的門檻、標籤延遲。三個挑戰，全部都是「拉到某個值，看表格怎麼變」：
  </p>
  <div class="ex">
    <span class="lv">LEVEL 1</span>
    <p>把「<b>世界變得多快</b>」拉到 <span class="kbd">0</span>（世界完全不變），其他不動。
      三條線會變成什麼樣子？三種策略各重訓了幾次、平均準確率是多少？
      誰做了白工？</p>
  </div>
  <div class="ex">
    <span class="lv">LEVEL 2</span>
    <p>世界變化速度放回 <span class="kbd">0.12</span>、標籤延遲 <span class="kbd">0</span>，
      把「監控觸發門檻」從 <span class="kbd">0.95</span> 一格一格拉到 <span class="kbd">0.70</span>，
      記下每一格的平均準確率與重訓次數。多花 19 次重訓，平均準確率買到幾個百分點？</p>
  </div>
  <div class="ex">
    <span class="lv">LEVEL 3</span>
    <p>把「標籤晚幾個月」拉到 <span class="kbd">6</span>，然後<b>只調「每幾個月定期重訓」</b>，
      找出一個能贏過這個監控觸發的設定。怎麼知道你贏了？看表格的兩欄——
      平均準確率更高、重訓次數更少，兩件事要同時成立。
      做完再回答自己一個問題：你手上的專案，標籤多久會到？</p>
  </div>
  <p style="font-size:13.5px;color:var(--ink-soft);margin-top:10px">
    卡住了？每一題在實驗場末節都有折疊解答——先自己拉一遍，再打開對照。
  </p>
  <button class="golab" data-nb="6️⃣">到實驗場的實驗區開工</button>
</section>

<section id="quiz">
  <span class="eyebrow">07 · 驗收</span>
  <h2>情境測驗</h2>
  <p>離開前試試看：下面的情境都真的會遇到。每題選一個你認為的最佳做法，選了馬上看得到解釋。</p>
  <div data-quiz>

    <div class="quiz-q" data-answer="B">
      <p class="quiz-tag">Q1 <span class="qtype">情境題</span></p>
      <h3>模型上線 8 個月，每月準確率都在 0.93 上下、一點都沒掉；但你發現進來的客戶跟訓練時很不一樣（某個特徵的月平均從 -0.08 一路走到 +1.5，正類比例從 48% 變成 95%）。最合理的處置是？</h3>
      <div class="quiz-opts">
        <button type="button" class="quiz-opt" data-k="A">A. 準確率沒掉就是沒事，這種分佈變化不用理會</button>
        <button type="button" class="quiz-opt" data-k="B">B. 這是資料漂移：規則還沒變所以先不重訓，但要把它當早期警訊留著看，並確認新客群上的準確率也還在水準內</button>
        <button type="button" class="quiz-opt" data-k="C">C. 客群都變了，立刻重訓一次比較保險</button>
        <button type="button" class="quiz-opt" data-k="D">D. 把監控門檻從 0.85 提高到 0.95，讓它更敏感一點</button>
      </div>
      <div class="quiz-fb" aria-live="polite"><p>本課實測：只有資料漂移的世界，24 個月平均準確率是 <b>0.945</b>，甚至比「世界完全不變」的 0.926 還高一點——因為決定答案的規則沒變，模型學到的界線還是對的。所以 C 是過度反應：重訓要花錢、要承擔上線風險，而這裡沒有東西需要被修。但 A 也不對——資料漂移是你<b>不用等標籤就看得到</b>的唯一訊號，而且模型正在服務一群訓練時沒見過的客戶，值得繼續盯。D 更糟：實測把門檻拉到 0.95，重訓次數會從 4 次暴增到 23 次（等於每個月都重訓），平均只多 2.7 個百分點。<b>正確的心態是：資料漂移＝多看一眼；概念漂移（準確率真的掉）＝該動手了。</b></p></div>
    </div>

    <div class="quiz-q" data-answer="C">
      <p class="quiz-tag">Q2 <span class="qtype">情境題</span></p>
      <h3>你的專案要等客戶真的解約才知道答案，標籤大約晚 6 個月。團隊提議做「準確率低於門檻就自動重訓」。你的建議是？</h3>
      <div class="quiz-opts">
        <button type="button" class="quiz-opt" data-k="A">A. 照做，監控觸發一定比定期重訓省，只是效果會打點折</button>
        <button type="button" class="quiz-opt" data-k="B">B. 照做，但把門檻拉高到 0.95 來補償延遲</button>
        <button type="button" class="quiz-opt" data-k="C">C. 先用簡單的定期重訓，把力氣花在讓標籤更快到位（人工抽樣標註、找代理指標）；等標籤夠快了再上監控觸發</button>
        <button type="button" class="quiz-opt" data-k="D">D. 標籤這麼慢，重訓沒有意義，維持現在的模型就好</button>
      </div>
      <div class="quiz-fb" aria-live="polite"><p>實測數字站在 C 這邊：標籤晚 6 個月時，監控觸發的平均準確率是 <b>0.796、重訓 14 次</b>，而「每 6 個月固定重訓一次」是 <b>0.867、只重訓 3 次</b>——又準又便宜。原因是延遲同時傷了兩件事：警報晚 6 個月響，而且重訓只能用 6 個月前的舊資料，模型一出生就落後，很快又跌破門檻。A 的直覺（監控一定比較省）在標籤夠快時成立，在這裡剛好相反。B 會讓情況更糟：門檻越高觸發越頻繁，等於用過期教材一直重訓。D 則是放棄治療——本課第 1 節那條掉到 0.45 的曲線就是它的結局。</p></div>
    </div>

    <div class="quiz-q" data-answer="B">
      <p class="quiz-tag">Q3 <span class="qtype dx">錯誤診斷</span></p>
      <h3>你把「世界變得多快」拉到 0（世界完全不變），實驗場給出這張表。為什麼定期重訓做了 7 次，平均準確率反而比完全不重訓低一點？</h3>
      <div class="codeblock">世界變化速度 0.00
不重訓                 平均 0.926   最低 0.900   重訓 0 次
定期重訓（每 3 個月）   平均 0.922   最低 0.880   重訓 7 次
監控觸發（門檻 0.85）   平均 0.926   最低 0.900   重訓 0 次</div>
      <div class="quiz-opts">
        <button type="button" class="quiz-opt" data-k="A">A. 模擬有 bug——重訓用的是更新的資料，訓出來一定不會比舊的差</button>
        <button type="button" class="quiz-opt" data-k="B">B. 世界沒變，重訓學不到任何新東西；而每次重訓只用當月那 300 筆資料，抽樣運氣不同，成績自然會上下抖一點——這 7 次是純成本</button>
        <button type="button" class="quiz-opt" data-k="C">C. 重訓會讓模型忘掉舊資料學到的東西，所以越訓越差</button>
        <button type="button" class="quiz-opt" data-k="D">D. 因為門檻 0.85 設得太低，監控觸發沒被觸發，把平均拉低了</button>
      </div>
      <div class="quiz-fb" aria-live="polite"><p>A 正是這堂課要打破的直覺：<b>重訓不保證變好</b>。世界沒變的時候，新資料裡沒有任何新資訊，重訓只是拿另外 300 筆樣本重擲一次骰子，運氣不好就略差一點（0.922 對 0.926）。C 說的災難性遺忘是持續學習的問題，這裡每次都是從頭訓練，不適用。D 把因果說反了——監控觸發沒被觸發，正是它做對了：它的成績跟不重訓一樣好，而且省下 7 次重訓。<b>真正的教訓有兩個</b>：定期重訓在穩定的世界裡是純成本（這就是監控觸發存在的理由），而「重訓可能更差」也正是每條自動重訓管線都必須有品質閘的原因——新模型要先跟舊的比過，贏了才准上線。</p></div>
    </div>

    <div class="quiz-q" data-answer="C">
      <p class="quiz-tag">Q4 <span class="qtype dx">錯誤診斷</span></p>
      <h3>同樣的門檻 0.85、同樣的世界，只有「標籤延遲」不同。標籤越晚到，重訓次數為什麼反而<b>變多</b>？</h3>
      <div class="codeblock">標籤延遲    平均準確率   重訓次數
晚 0 個月     0.889        4 次
晚 3 個月     0.851       11 次
晚 6 個月     0.796       14 次</div>
      <div class="quiz-opts">
        <button type="button" class="quiz-opt" data-k="A">A. 標籤晚到會累積成一大批資料，資料變多所以重訓也變多</button>
        <button type="button" class="quiz-opt" data-k="B">B. 延遲讓每個月的準確率被低估，等於偷偷把門檻調嚴了</button>
        <button type="button" class="quiz-opt" data-k="C">C. 重訓只能用「已經有標籤」的舊資料，訓出來的模型一出生就落後 N 個月，很快又跌破門檻，於是再重訓一次</button>
        <button type="button" class="quiz-opt" data-k="D">D. 監控把同一個月的成績重複判斷了好幾次，觸發了重複的重訓</button>
      </div>
      <div class="quiz-fb" aria-live="polite"><p>關鍵在於<b>延遲同時弄慢了警報和教材</b>，而後者才是次數暴增的原因：第 m 個月要重訓，手上最新的有標籤資料是第 m-N 個月的，訓出來的模型等於「N 個月前的最佳解」，放到今天的世界馬上又不夠好，於是很快再觸發一次——追著自己的影子跑。A 不成立，這個模擬每次重訓都只用一個月份的資料，資料量固定。B 說反了：延遲不會改變任何一個月算出來的準確率數值，它只改變你<b>什麼時候看到</b>那個數字。D 是想像出來的 bug，每個月只判斷一次。<b>帶得走的結論：先問標籤多久會到，再決定監控策略。</b></p></div>
    </div>

    <div class="quiz-score" data-score></div>
  </div>
</section>

<div class="endnav">
  <a href="/mlflow-tracking/">
    <span class="tag">下一課</span>
    <b>MLflow 實驗追蹤：每一次訓練都留下證據 →</b>
  </a>
  <a href="/mlops/">
    <span class="tag">主題</span>
    <b>‹ 回「MLOps 自動化技術」課程列表</b>
  </a>
</div>
"""

SCRIPT = r"""
/* ═══ hero 互動：重訓時間軸 ═══
   TRI[m][i] = 第 m 個月訓練的模型，在第 (m+1+i) 個月的準確率。
   全部來自實驗場同一份模擬的實測值（24 個月、每月 300 筆、6 維、概念漂移 0.12）。 */
(function () {
  var TRI = [[0.94,0.91,0.923,0.793,0.833,0.787,0.817,0.7,0.687,0.703,0.713,0.677,0.653,0.66,0.583,0.503,0.483,0.53,0.46,0.477,0.473,0.42,0.453],[0.923,0.923,0.827,0.863,0.807,0.823,0.733,0.717,0.723,0.743,0.697,0.677,0.677,0.607,0.517,0.5,0.557,0.48,0.487,0.49,0.46,0.46],[0.943,0.85,0.89,0.83,0.857,0.763,0.753,0.783,0.757,0.723,0.703,0.7,0.633,0.56,0.523,0.583,0.517,0.5,0.513,0.467,0.453],[0.857,0.89,0.847,0.877,0.793,0.777,0.77,0.783,0.743,0.737,0.723,0.63,0.56,0.527,0.577,0.537,0.51,0.51,0.477,0.45],[0.93,0.907,0.927,0.87,0.847,0.86,0.83,0.79,0.803,0.76,0.713,0.663,0.61,0.683,0.59,0.593,0.577,0.537,0.513],[0.9,0.927,0.853,0.843,0.833,0.84,0.777,0.793,0.753,0.7,0.65,0.593,0.67,0.587,0.56,0.557,0.533,0.503],[0.933,0.89,0.88,0.873,0.863,0.823,0.813,0.777,0.733,0.687,0.633,0.7,0.617,0.59,0.597,0.54,0.527],[0.9,0.897,0.877,0.873,0.837,0.813,0.79,0.747,0.697,0.65,0.71,0.633,0.597,0.6,0.553,0.54],[0.923,0.903,0.91,0.887,0.84,0.833,0.79,0.753,0.703,0.73,0.683,0.657,0.637,0.577,0.58],[0.937,0.907,0.897,0.863,0.863,0.81,0.773,0.737,0.753,0.713,0.693,0.663,0.6,0.61],[0.897,0.917,0.873,0.867,0.823,0.787,0.763,0.773,0.727,0.713,0.673,0.633,0.627],[0.933,0.887,0.863,0.823,0.79,0.76,0.783,0.727,0.71,0.683,0.633,0.657],[0.903,0.897,0.867,0.833,0.803,0.817,0.79,0.747,0.717,0.673,0.693],[0.92,0.873,0.853,0.83,0.843,0.793,0.777,0.717,0.697,0.73],[0.89,0.887,0.843,0.87,0.823,0.773,0.723,0.733,0.75],[0.92,0.883,0.893,0.88,0.817,0.773,0.787,0.773],[0.917,0.917,0.9,0.837,0.83,0.8,0.827],[0.93,0.93,0.863,0.873,0.833,0.857],[0.923,0.873,0.88,0.847,0.85],[0.887,0.903,0.893,0.893],[0.91,0.92,0.9],[0.92,0.92],[0.937]];
  var LAST = 23, BASE_MEAN = 0.660, THR = 0.85;
  var X0 = 40, X1 = 428, Y0 = 16, Y1 = 168, LO = 0.35, HI = 1.0;

  var svg = document.getElementById("mw-svg");
  if (!svg) return;
  var gGrid = document.getElementById("mw-grid");
  var pBase = document.getElementById("mw-base");
  var pLine = document.getElementById("mw-line");
  var gMark = document.getElementById("mw-marks");
  var elMonth = document.getElementById("mw-month");
  var elMonthVal = document.getElementById("mw-month-val");
  var elVerdict = document.getElementById("mw-verdict");
  var retrains = [];

  function px(t) { return X0 + (t - 1) / (LAST - 1) * (X1 - X0); }
  function py(a) { return Y0 + (HI - a) / (HI - LO) * (Y1 - Y0); }

  function curve(rs) {
    var out = [];
    for (var t = 1; t <= LAST; t++) {
      var m = 0;
      for (var i = 0; i < rs.length; i++) { if (rs[i] < t) m = rs[i]; }
      out.push(TRI[m][t - m - 1]);
    }
    return out;
  }

  function path(vals) {
    var d = "";
    for (var i = 0; i < vals.length; i++) {
      d += (i ? "L" : "M") + px(i + 1).toFixed(1) + " " + py(vals[i]).toFixed(1) + " ";
    }
    return d;
  }

  function mean(vals) {
    var s = 0;
    for (var i = 0; i < vals.length; i++) { s += vals[i]; }
    return s / vals.length;
  }

  function grid() {
    var h = "";
    [0.4, 0.6, 0.8, 1.0].forEach(function (a) {
      h += '<line x1="' + X0 + '" y1="' + py(a).toFixed(1) + '" x2="' + X1 +
           '" y2="' + py(a).toFixed(1) + '" stroke="var(--grid)" stroke-width="1"></line>';
      h += '<text x="' + (X0 - 7) + '" y="' + (py(a) + 4).toFixed(1) +
           '" font-size="11.5" fill="var(--ink-soft)" text-anchor="end">' + a.toFixed(1) + "</text>";
    });
    h += '<line x1="' + X0 + '" y1="' + py(THR).toFixed(1) + '" x2="' + X1 + '" y2="' +
         py(THR).toFixed(1) + '" stroke="var(--ink-soft)" stroke-width="1.2" stroke-dasharray="5 5"></line>';
    h += '<text x="' + (X0 + 5) + '" y="' + (py(THR) + 14).toFixed(1) +
         '" font-size="11.5" fill="var(--ink-soft)">可接受底線 0.85</text>';
    [1, 6, 12, 18, 23].forEach(function (t) {
      h += '<text x="' + px(t).toFixed(1) + '" y="' + (Y1 + 17) +
           '" font-size="11.5" fill="var(--ink-soft)" text-anchor="middle">' + t + "</text>";
    });
    h += '<text x="' + ((X0 + X1) / 2) + '" y="' + (Y1 + 36) +
         '" font-size="11.5" fill="var(--ink-soft)" text-anchor="middle">上線後第幾個月</text>';
    gGrid.innerHTML = h;
  }

  function marks() {
    var h = "";
    retrains.forEach(function (m) {
      var x = px(m).toFixed(1);
      h += '<line x1="' + x + '" y1="' + Y0 + '" x2="' + x + '" y2="' + Y1 +
           '" stroke="var(--c3)" stroke-width="1" stroke-dasharray="3 4" opacity="0.7"></line>';
      h += '<polygon points="' + x + "," + (Y0 + 9) + " " + (px(m) - 5).toFixed(1) + "," + Y0 +
           " " + (px(m) + 5).toFixed(1) + "," + Y0 + '" fill="var(--c3)"></polygon>';
    });
    gMark.innerHTML = h;
  }

  function render() {
    var vals = curve(retrains);
    var m = mean(vals);
    pLine.setAttribute("d", path(vals));
    marks();
    var msg;
    if (!retrains.length) {
      msg = '沒有重訓：24 個月平均 <b class="bad">' + m.toFixed(3) +
            "</b>，最後一個月只剩 0.45。按一次「重訓一次」看看。";
    } else {
      msg = "重訓 <b>" + retrains.length + '</b> 次：平均 <b class="good">' + m.toFixed(3) +
            "</b>（放著不管是 " + BASE_MEAN.toFixed(3) + "）";
      if (m < 0.85) {
        msg += "——還沒穩住，再多按幾次、或換個月份試試。";
      } else {
        msg += "——穩住了。代價是這 " + retrains.length + " 次重訓，每一次都是成本。";
      }
    }
    elVerdict.innerHTML = msg;
  }

  elMonth.addEventListener("input", function () {
    elMonthVal.textContent = elMonth.value;
  });
  document.getElementById("hero-retrain").addEventListener("click", function () {
    var m = +elMonth.value;
    if (retrains.indexOf(m) < 0) { retrains.push(m); retrains.sort(function (a, b) { return a - b; }); }
    render();
  });
  document.getElementById("mw-reset").addEventListener("click", function () {
    retrains = [];
    render();
  });

  grid();
  pBase.setAttribute("d", path(curve([])));
  render();
})();
"""
