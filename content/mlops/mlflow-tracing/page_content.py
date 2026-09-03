"""課程頁內容區（純常數）。改完跑：python3 .claude/skills/make-lesson/scripts/page-fill.py content/mlops/mlflow-tracing
build.sh 不會部署這個檔；它是 index.html 內容區的正本。"""

TITLE = "MLflow Tracing：LLM 應用的每一步都留下軌跡"
DESCRIPTION = "LLM 應用出錯時你只看得到最後一句話。Tracing 把一次請求拆成 span 樹：檢索到什麼、prompt 長什麼樣、模型回了什麼、花了幾毫秒。@mlflow.trace、tag 與搜尋、人工標記、code scorer、Prompt Registry 的版本與 alias——不打真 LLM、不需要 API key，molab 免費環境全程實作。"
NB = "https://molab.marimo.io/github/skmygo/agentclass/blob/main/content/mlops/mlflow-tracing/mlflow-tracing_ext.py"

STYLE = r"""
  /* 語義色：藍＝檢索、橘＝模型、綠＝工具／通過、紅＝幻覺／未通過 */
  :root { --c1: #4C72B0; --c2: #DD8452; --c3: #55A868; --cut: #C44E52; }
  a.golab { text-decoration: none; display: inline-flex; align-items: center; gap: 8px; }

  /* hero：trace 瀏覽器 */
  #tr-demo .ctl { display: flex; gap: 7px; flex-wrap: wrap; align-items: center; margin-bottom: 9px; }
  #tr-demo .lbl { font-size: 11.5px; font-weight: 800; letter-spacing: .06em; color: var(--ink-soft); min-width: 60px; }
  #tr-demo .ctl button { font-family: var(--mono); font-size: 12.5px; padding: 5px 11px; border-radius: 8px;
    border: 1.5px solid var(--grid); background: #fff; color: var(--ink); cursor: pointer;
    transition: border-color .15s, background .15s, color .15s; }
  #tr-demo .ctl button:hover { background: var(--chip-bg); }
  #tr-demo .ctl button.on { border-color: var(--ink); background: var(--ink); color: #fff; }

  #tr-demo .card { border: 1.5px solid var(--grid); border-radius: 10px; padding: 10px 11px 11px; margin-top: 12px; }
  #tr-demo .hd { font-family: var(--mono); font-size: 11.5px; color: var(--ink-soft); line-height: 1.7;
    word-break: break-word; border-bottom: 1px solid var(--grid); padding-bottom: 7px; margin-bottom: 8px; }
  #tr-demo .hd b { color: var(--ink); }
  #tr-demo .sp { border-radius: 7px; padding: 3px 5px; margin: 1px 0; cursor: pointer; transition: background .12s; }
  #tr-demo .sp:hover { background: var(--chip-bg); }
  #tr-demo .sp.kid { margin-left: 16px; }
  #tr-demo .sp.open { background: var(--chip-bg); }
  #tr-demo .sp-h { display: flex; align-items: center; gap: 8px; flex-wrap: wrap;
    font-family: var(--mono); font-size: 12.5px; }
  #tr-demo .nm { font-weight: 700; min-width: 0; }
  #tr-demo .ty { font-size: 10.5px; font-weight: 800; letter-spacing: .05em; padding: 1px 7px;
    border-radius: 999px; color: #fff; white-space: nowrap; }
  #tr-demo .ty.CHAIN { background: #3b3a36; }
  #tr-demo .ty.RETRIEVER { background: var(--c1); }
  #tr-demo .ty.LLM { background: var(--c2); }
  #tr-demo .track { flex: 1 1 90px; min-width: 60px; overflow: hidden; display: flex; align-items: center; }
  #tr-demo .track i { display: block; height: 10px; border-radius: 3px; flex: none; }
  #tr-demo .track i.CHAIN { background: #3b3a36; }
  #tr-demo .track i.RETRIEVER { background: var(--c1); }
  #tr-demo .track i.LLM { background: var(--c2); }
  #tr-demo .ms { font-size: 11.5px; color: var(--ink-soft); white-space: nowrap; }
  #tr-demo .sp-io { display: none; font-family: var(--mono); font-size: 11.5px; line-height: 1.55;
    margin: 6px 0 4px 6px; padding-left: 9px; border-left: 2px solid var(--grid); }
  #tr-demo .sp.open .sp-io { display: block; }
  #tr-demo .sp-io pre { margin: 2px 0 7px; white-space: pre-wrap; word-break: break-word;
    overflow-wrap: anywhere; color: var(--ink); }
  #tr-demo .sp-io .k { font-size: 10.5px; font-weight: 800; letter-spacing: .07em; color: var(--ink-soft); }
  #tr-demo .hint { font-size: 11.5px; color: var(--ink-soft); margin-top: 8px; }
  #tr-demo .verdict { font-size: 13px; margin-top: 9px; padding: 7px 10px; border-radius: 8px;
    border-left: 3px solid var(--c3); background: var(--chip-bg); }
  #tr-demo .verdict.bad { border-left-color: var(--cut); }

  table.cmp { width: 100%; border-collapse: collapse; font-size: 13.5px; margin: 14px 0; }
  table.cmp th, table.cmp td { border-bottom: 1px solid var(--grid); padding: 8px 10px; text-align: left; vertical-align: top; }
  table.cmp th { font-size: 12px; letter-spacing: .04em; color: var(--ink-soft); }
  table.cmp td.b { color: var(--c1); font-weight: 700; }
  table.cmp td.o { color: var(--c2); font-weight: 700; }
  table.cmp td.g { color: var(--c3); font-weight: 700; }
  table.cmp td.r { color: var(--cut); font-weight: 700; }
  .kbd { font-family: var(--mono); background: var(--chip-bg); padding: 1px 6px; border-radius: 5px; font-size: 13px; }
"""

WRAP = r'''
<section id="hero">
  <span class="eyebrow">TRACING · 補充 E · 10</span>
  <h1>MLflow Tracing：<br>LLM 應用的每一步都留下軌跡</h1>
  <p style="margin-top:18px">
    客服機器人回了一句「可以分期，通常提供 3 期與 6 期免利息。」，客戶照做了，然後投訴。
    你手上只有這句話——是<b>檢索</b>沒撈到文件？<b>prompt</b> 沒把文件放進去？還是<b>模型</b>自己編的？
    點下面任何一個問題，把中間那段點亮：
  </p>

  <div class="hero-demo" id="tr-demo">
    <div class="ctl" id="tr-qs">
      <span class="lbl">問題</span>
      <button type="button" data-q="退貨要多久內？">退貨要多久內？</button>
      <button type="button" data-q="運費怎麼算？">運費怎麼算？</button>
      <button type="button" data-q="可以分期嗎？" class="on">可以分期嗎？</button>
    </div>
    <div class="ctl" id="tr-vs">
      <span class="lbl">prompt</span>
      <button type="button" data-v="v1" class="on">v1（舊版）</button>
      <button type="button" data-v="v2">v2（加了拒答規則）</button>
    </div>
    <div class="card">
      <div class="hd" id="tr-hd"></div>
      <div id="tr-tree"></div>
      <p class="hint">點任何一列展開它的 inputs／outputs 原文。</p>
      <div class="verdict" id="tr-verdict"></div>
    </div>
  </div>

  <p class="note">
    六條 trace 都是 notebook 的實測紀錄（MLflow 3.15.2，不打真的 LLM）：trace id、標籤、每個 span 的
    inputs／outputs 全是原文。毫秒是單次量測——這一課的耗時來自刻意加上的模擬延遲，你自己跑會不一樣。
  </p>
</section>

<section id="s1">
  <span class="eyebrow">01 · 從 RUN 到 TRACE</span>
  <h2>訓練記「一次訓練」，上線記「一次請求」</h2>
  <p>
    第 1 課的 <b>run</b> 是訓練的紀錄簿：一次訓練一筆，裡面有 params、metrics、artifacts，
    好壞用一個 AUC 說了算。那套東西到了 LLM 應用就整個不夠用——
    因為你要記的不是「今天訓了一個模型」，而是<b>今天有八萬個人問了問題</b>。
  </p>
  <table class="cmp">
    <tr><th></th><th>run（第 1 課）</th><th>trace（這一課）</th></tr>
    <tr><td>記錄的單位</td><td>一次<b>訓練</b></td><td>一次<b>請求</b></td></tr>
    <tr><td>一天幾筆</td><td>幾十筆</td><td>幾十萬筆</td></tr>
    <tr><td>裡面有什麼</td><td>params / metrics / artifacts</td><td class="o"><b>span 樹</b>：每一步的 inputs、outputs、耗時、屬性</td></tr>
    <tr><td>好壞怎麼判斷</td><td>一個 AUC 說了算</td><td class="r">沒有標準答案——要人標、要 scorer 打分</td></tr>
    <tr><td>版本控制什麼</td><td>模型（Registry）</td><td class="b"><b>prompt</b>（Prompt Registry）</td></tr>
    <tr><td>出事時你要回答</td><td>當時的參數是什麼</td><td>當時<b>檢索到什麼、prompt 長什麼樣、用的哪一版</b></td></tr>
  </table>
  <p>
    <b>span</b> 就是「一步」：一次檢索、一次模型呼叫、一次工具呼叫。
    一次請求裡的每一步各是一個 span，串起來就是一棵樹——這就是 trace。
    你原本的 log 也記得到這些，前提是你想得到要記、而且記得下次也要記；
    tracing 的價值在於<b>它是預設就記完整的</b>，而且結構化到可以搜尋、可以比較、可以打分。
  </p>
  <a class="golab" href="__NB__" target="_blank" rel="noopener">到 notebook 的 0️⃣ 節：假 LLM 客服與三條知識庫</a>
</section>

<section id="s2">
  <span class="eyebrow">02 · 第一個 TRACE</span>
  <h2>三個裝飾器，一棵樹</h2>
  <div class="codeblock">@mlflow.trace(span_type="RETRIEVER")
def retrieve(question): ...          # 去知識庫找文件

@mlflow.trace(span_type="LLM")
def fake_llm(prompt): ...            # 呼叫模型

@mlflow.trace(name="answer", span_type="CHAIN")
def answer(question):                # 把上面兩步串起來
    ctx = retrieve(question)
    return fake_llm(f"資料：{ctx}\n問題：{question}")["content"]</div>
  <p>
    要被記錄，只要加一行 <span class="kbd">@mlflow.trace</span>。
    <b>你不用宣告誰是誰的父節點</b>——<span class="kbd">answer()</span> 呼叫了另外兩個函式，
    MLflow 就把它們變成巢狀 span，<b>呼叫關係就是樹的形狀</b>。
    函式的參數自動變成 span 的 inputs、回傳值自動變成 outputs，你一個字都不用寫。
  </p>
  <p>
    然後是<b>這一課最容易踩的一個坑</b>：trace 是<b>非同步寫入</b>的（不然每個請求都要等資料庫寫完才能回應）。
    在 notebook 或測試腳本裡「跑完馬上查」，你查到幾筆是<b>不一定的，而且沒有任何錯誤訊息</b>：
  </p>
  <div class="codeblock">for q in ["退貨要多久內？", "運費怎麼算？", "可以分期嗎？"]:
    answer(q)

mlflow.search_traces(experiment_ids=[EXP_ID])      # → 實測 0 筆或 2 筆，每次不一定
mlflow.flush_trace_async_logging()                 # ← 少了這行，上面那行就是擲骰子
mlflow.search_traces(experiment_ids=[EXP_ID])      # → 穩定 3 筆</div>
  <p>
    背景執行緒可能剛好寫完一部分，所以結果是隨機的——<b>「有時會過、有時不會」的測試比直接壞掉更難查</b>。
    正式服務不需要 <span class="kbd">flush</span>（背景執行緒自己會寫完），它是給「跑完馬上要查」的場景用的。
    另外注意參數名是 <span class="kbd">experiment_ids</span>（複數、要 id）——
    寫成 <span class="kbd">experiment_names</span> 會直接
    <span class="kbd">TypeError: … Did you mean 'experiment_ids'?</span>。
  </p>
  <p>
    <span class="kbd">search_traces()</span> 回一張 12 欄的 DataFrame（一列一條 trace，
    有 <span class="kbd">trace_id</span>、<span class="kbd">state</span>、<span class="kbd">execution_duration</span>、
    <span class="kbd">request</span>、<span class="kbd">response</span>、<span class="kbd">tags</span>…），
    要看樹則用 <span class="kbd">mlflow.get_trace(trace_id)</span>：
    <span class="kbd">.info</span> 是整條的資訊，<span class="kbd">.data.spans</span> 是每一步。
  </p>
  <a class="golab" href="__NB__" target="_blank" rel="noopener">到 notebook 的 1️⃣–2️⃣ 節：跑三題、把 span 樹畫出來</a>
</section>

<section id="s3">
  <span class="eyebrow">03 · SPAN_TYPE</span>
  <h2>那個字串不影響執行，但決定三件事</h2>
  <p>
    <span class="kbd">span_type="RETRIEVER"</span> 不會改變任何計算結果，很容易讓人覺得可有可無。它決定的是：
  </p>
  <table class="cmp">
    <tr><th>它影響什麼</th><th>標對了</th><th>標錯（或沒標）</th></tr>
    <tr><td>MLflow UI 怎麼畫這一步</td><td class="g"><span class="kbd">RETRIEVER</span> 畫成「找到哪幾份文件」的清單，<span class="kbd">LLM</span> 畫成對話框並顯示 token 數</td><td class="r">畫成一坨看不懂的 JSON</td></tr>
    <tr><td>內建 scorer 找不找得到料</td><td class="g">「檢索到的文件跟問題有沒有關係」這類評分器靠 <span class="kbd">RETRIEVER</span> 找文件</td><td class="r">評分器找不到文件，靜靜跳過</td></tr>
    <tr><td>你自己的查詢與統計</td><td class="g">「所有 LLM span 的總 token」「TOOL span 的失敗率」</td><td class="r">分不了組</td></tr>
  </table>
  <p>
    <span class="kbd">mlflow.entities.SpanType</span> 提供 15 個常數（3.15.2 實測）：
    <span class="kbd">CHAIN</span>、<span class="kbd">LLM</span>、<span class="kbd">CHAT_MODEL</span>、
    <span class="kbd">RETRIEVER</span>、<span class="kbd">TOOL</span>、<span class="kbd">AGENT</span>、
    <span class="kbd">EMBEDDING</span>、<span class="kbd">RERANKER</span>、<span class="kbd">PARSER</span>、
    <span class="kbd">GUARDRAIL</span>、<span class="kbd">EVALUATOR</span>、<span class="kbd">MEMORY</span>、
    <span class="kbd">TASK</span>、<span class="kbd">WORKFLOW</span>、<span class="kbd">UNKNOWN</span>。
    傳字串或傳常數都可以，值一樣。
  </p>
  <p>
    <b>這個欄位沒有校驗</b>——<span class="kbd">span_type="RETREIVER"</span> 打錯字不會報錯，
    程式照跑、trace 照存，只是 UI 不知道怎麼畫、scorer 當作沒看到。這是最沉默的那種錯，
    所以能用常數就別打字串。
  </p>
  <a class="golab" href="__NB__" target="_blank" rel="noopener">到 notebook 的 3️⃣ 節：15 種 span_type 與它們的用途</a>
</section>

<section id="s4">
  <span class="eyebrow">04 · 屬性、標籤、搜尋</span>
  <h2>一天幾十萬條，你需要能篩</h2>
  <div class="codeblock">mlflow.get_current_active_span().set_attributes({"n_docs": len(ctx), "question_len": len(q)})
mlflow.update_current_trace(tags={"topic": "退貨"})

mlflow.search_traces(experiment_ids=[EXP_ID], filter_string="tags.topic = '退貨'")</div>
  <p>MLflow 給你兩個掛東西的地方，很多人混用，但用途完全不同：</p>
  <table class="cmp">
    <tr><th></th><th><span class="kbd">span.set_attributes()</span></th><th><span class="kbd">update_current_trace(tags=)</span></th></tr>
    <tr><td>掛在哪</td><td class="b">單一 <b>span</b></td><td class="o">整條 <b>trace</b></td></tr>
    <tr><td>典型內容</td><td><span class="kbd">n_docs</span>、<span class="kbd">top_k</span>、<span class="kbd">temperature</span></td><td><span class="kbd">topic</span>、<span class="kbd">user_tier</span>、<span class="kbd">prompt_ver</span>、<span class="kbd">session_id</span></td></tr>
    <tr><td>能拿來搜尋嗎</td><td class="r">不能（要撈回來自己看）</td><td class="g">能</td></tr>
    <tr><td>什麼時候用</td><td>事後想「<b>那一步</b>當時是什麼設定」</td><td>事前想「之後我要用什麼條件<b>撈出一群</b>請求」</td></tr>
  </table>
  <p>
    <b>一句話判準：想用它「找出一群 trace」就放 tag；想用它「解釋某一步」就放 attribute。</b>
    這個選擇在寫程式的當下不痛不癢，但等到出事、你想撈「所有 VIP 客戶問退貨而且答錯的請求」時，
    當初放錯地方的欄位就撈不出來了。
  </p>
  <p>
    搜尋語法跟第 1 課的 <span class="kbd">search_runs</span> 是同一套解析器（同樣的坑會再踩一次）。
    有一條分界線值得先記起來：<b>「點」前面那一段（entity type）MLflow 會驗，「點」後面那一段（key）不會</b>——
    所以打錯前綴會被罵，打錯 tag 名字只會靜靜回 0 筆。全部是實測原文：
  </p>
  <div class="codeblock">"tags.topic = 退貨"                     ← 值沒有引號
  → Parameter value is either not quoted or unidentified quote types used for string value 退貨.

"tags.topic == '退貨'"                  ← 用了 ==
  → Invalid comparator '==' not one of '{'IS NOT NULL', 'IS NULL', '!=', 'ILIKE', '=', 'LIKE', 'RLIKE'}'

"attributes.execution_duration > 100"   ← DataFrame 的欄名不是 filter 的欄名
  → Invalid attribute key 'execution_duration' specified. Valid keys are
    '{'execution_time_ms', 'status', 'name', 'timestamp_ms', 'run_id', 'request_id', …}'

"foo.topic = '退貨'"                    ← entity type 不存在
  → Invalid entity type 'foo'. Valid values are {'attribute', 'request_metadata', 'attributes',
    'metadata', 'span', 'tags', 'expectation', 'tag', 'trace', 'issue', 'feedback'}

"tags.Topic = '退貨'"                   ← 只是 tag 名字大小寫錯
  → 不報錯，回 0 筆   ← 唯一不會叫你的那一種</div>
  <p>
    前四個會叫你，第五個不會。<b>查不到東西的時候，先懷疑自己的 filter，不要先懷疑資料。</b>
    兩個閱讀提示：那份合法清單裡 <span class="kbd">tag</span> 與 <span class="kbd">tags</span> 都在，
    兩種寫法都能用——別把少一個 s 當成 bug；還有<b>大括號裡的順序每次執行都不一樣</b>（那是 Python 的 set），
    上面是某一次的輸出、也做了截斷，別把順序或長度當成規格。
    同一組陷阱還有兩個孿生兄弟：<span class="kbd">get_current_active_span()</span> 在 trace 外面呼叫回
    <span class="kbd">None</span>（接著 <span class="kbd">.set_attributes()</span> 就是
    <span class="kbd">AttributeError</span>）；<span class="kbd">update_current_trace()</span> 在 trace 外面呼叫
    <b>什麼都不會發生也不會報錯</b>——標籤靜靜地掉了。
  </p>
  <p>
    不是每個 span 都來自裝飾器：一段 for 迴圈、一個批次流程沒有函式可以掛，就用
    <span class="kbd">with mlflow.start_span(name=…, span_type=…) as s</span> 手動開一個，
    自己呼叫 <span class="kbd">s.set_inputs()</span> / <span class="kbd">s.set_outputs()</span>
    ——裝飾器做的其實就是幫你自動抓參數與回傳值而已。
  </p>
  <p>
    <b>順手就能拿到的第二個好處是延遲分析。</b>「這個請求要 3 秒」是抱怨，
    「這 3 秒有 2.7 秒在等模型」才是可以動手的情報，而 trace 天生就有這份資料。
    本課實測（<b>耗時是刻意加上的模擬延遲</b>：檢索 20 毫秒、生成 50 毫秒）：
  </p>
  <table class="cmp">
    <tr><th>問題</th><th>總計</th><th>retrieve</th><th>fake_llm</th><th>LLM 佔比</th></tr>
    <tr><td>退貨要多久內？（<b>第一筆</b>）</td><td class="r">130–220 ms</td><td>約 20 ms</td><td>約 50 ms</td><td>23–38%</td></tr>
    <tr><td>運費怎麼算？</td><td>71–73 ms</td><td>約 20 ms</td><td class="o">約 50 ms</td><td class="o">約 70%</td></tr>
    <tr><td>可以分期嗎？</td><td>71–92 ms</td><td>約 20–41 ms</td><td class="o">約 50 ms</td><td class="o">55–71%</td></tr>
  </table>
  <p>
    第一筆的總計時間明顯偏高，那是<b>第一次呼叫時 tracing 自己的暖機成本</b>，不是你的程式慢。
    <b>看延遲永遠要看分佈（p50／p95），不要看單筆、更不要看第一筆。</b>
    真實系統裡這張表的比例會更極端：生成通常是幾百毫秒到幾秒，檢索是幾十毫秒。
  </p>
  <a class="golab" href="__NB__" target="_blank" rel="noopener">到 notebook 的 4️⃣–5️⃣ 節：六種 filter 的命中數＋延遲拆解</a>
</section>

<section id="s5">
  <span class="eyebrow">05 · 人工評估</span>
  <h2>沒有 AUC 的世界：把人的判斷寫回 trace</h2>
  <div class="codeblock">TEACHER = AssessmentSource(source_type=AssessmentSourceType.HUMAN, source_id="teacher")

mlflow.log_feedback(trace_id=tid, name="correct", value=False,
                    rationale="知識庫沒有分期付款這條，模型自己編了一個答案", source=TEACHER)
mlflow.log_expectation(trace_id=tid, name="expected_answer",
                       value="手冊裡沒有寫。", source=TEACHER)</div>
  <p>
    訓練模型時有標準答案，AUC 一個數字說了算。LLM 應用沒有這種東西——
    「這個回答好不好」要人看了才知道。MLflow 的做法是把人的判斷<b>掛回那條 trace</b>，叫 <b>assessment</b>：
  </p>
  <table class="cmp">
    <tr><th></th><th><span class="kbd">log_feedback</span></th><th><span class="kbd">log_expectation</span></th></tr>
    <tr><td>記什麼</td><td>這次的回答<b>好不好</b></td><td>這一題<b>正確答案應該是什麼</b></td></tr>
    <tr><td>誰給的</td><td>人工標記、線上的讚／倒讚、LLM judge</td><td>人工（領域專家）</td></tr>
    <tr><td>本課實測</td><td class="r"><span class="kbd">correct = False</span>，理由寫在 <span class="kbd">rationale</span></td><td class="g"><span class="kbd">expected_answer = "手冊裡沒有寫。"</span></td></tr>
  </table>
  <p>
    <span class="kbd">AssessmentSource</span> 要寫清楚<b>是誰標的</b>（<span class="kbd">HUMAN</span> /
    <span class="kbd">LLM_JUDGE</span> / <span class="kbd">CODE</span>）——之後要分「人標的」跟「機器標的」全靠它。
    讀回來用 <span class="kbd">get_trace(tid).info.assessments</span>，但<b>要重新讀一次</b>：
    assessment 是掛上去之後才存在的，手上那個舊的 trace 物件不會自己更新。
  </p>
  <p>
    這件事的意義比它看起來大得多：<b>一批被標記過的 trace，就是你的評估資料集。</b>
    你不用另外維護一份 CSV、不用請人編題目——線上真實流量本身就是題庫，
    出問題的那幾條標一標，下次改 prompt 就有回歸測試可以跑。
    這也是為什麼上一節那些 tag 那麼重要：<b>你要先撈得出「該標的那一群」，才標得動。</b>
  </p>
  <p>
    實測會踩到的一個錯誤：<span class="kbd">log_feedback</span> 給一個不存在的 trace_id 會噴
    <span class="kbd">MlflowException: Trace with ID 'tr-…' not found. It may have been deleted.</span>
    ——這句話八成不是真的被刪了，而是<b>你忘了 flush</b>，trace 還在緩衝區裡沒進資料庫。
  </p>
  <a class="golab" href="__NB__" target="_blank" rel="noopener">到 notebook 的 6️⃣ 節：標記那條幻覺 trace 並讀回來</a>
</section>

<section id="s6">
  <span class="eyebrow">06 · 自動評估</span>
  <h2>寫一個 scorer，讓機器幫你標——然後小心它騙你</h2>
  <div class="codeblock">@scorer
def refuses_when_empty(inputs, outputs) -> bool:
    if inputs.get("context"):          # 這一題本來就該有答案 → 放行
        return True
    return "手冊裡沒有寫" in str(outputs)

mlflow.genai.evaluate(data=[{"inputs": {...}, "outputs": "..."}, ...],
                      scorers=[has_number, refuses_when_empty, short_enough])</div>
  <p>
    人工標記很準，但一天標不了一百條。真實的做法是兩層：
    <b>code-based scorer</b>（純 Python 規則，快、免費、100% 可重現）處理
    「有沒有引用來源」「有沒有超過長度上限」「該拒答時有沒有拒答」；
    <b>LLM-as-judge scorer</b>（拿另一個模型當評審）處理「語氣夠不夠禮貌」「有沒有答非所問」這類寫不出規則的事——
    準，但要錢、要金鑰，而且<b>評審本身也會出錯</b>。這一課只跑第一種，一毛錢都不用花。
  </p>
  <p>
    同樣三題、同一個假模型，只換 prompt 版本（v2 加了拒答規則），三個 scorer 的實測分數：
  </p>
  <table class="cmp">
    <tr><th>scorer</th><th>prompt v1</th><th>prompt v2</th><th>怎麼讀</th></tr>
    <tr><td><span class="kbd">refuses_when_empty</span></td><td>0.667</td><td class="g">1.000</td><td>拒答規則生效了，幻覺被修掉 ✅</td></tr>
    <tr><td><span class="kbd">has_number</span></td><td>1.000</td><td class="r">0.667</td><td><b>看起來變差了</b></td></tr>
    <tr><td><span class="kbd">short_enough</span></td><td>1.000</td><td>1.000</td><td>兩版都沒超過 40 字</td></tr>
  </table>
  <p>
    <b>但 v2 沒有變差。</b>它那一題答的是「手冊裡沒有寫。」——<b>正確的拒答裡本來就不會有數字</b>，
    是這個 scorer 誤殺了它。更諷刺的是：v1 那句幻覺「3 期與 6 期免利息」裡有數字，
    所以 <span class="kbd">has_number</span> 給了它滿分。
  </p>
  <p>
    <b>兩個教訓。</b>第一，<b>一個指標會騙人，一組指標才看得出真相</b>——
    如果團隊只盯 <span class="kbd">has_number</span>，這次修正會被判定為「退步」而回滾。
    第二，scorer 要把<b>合法的例外</b>寫進規則裡：像
    <span class="kbd">refuses_when_empty</span> 那樣先問「這一題本來就該有答案嗎」，
    而不是無條件套同一條規則。
  </p>
  <p>
    最後一個實測到、會讓你找很久的坑：<b>scorer 的參數名只能從
    <span class="kbd">inputs</span> / <span class="kbd">outputs</span> /
    <span class="kbd">expectations</span> / <span class="kbd">trace</span> 裡挑</b>。
    寫成 <span class="kbd">def my_scorer(answer_text)</span> 不會報錯——
    <span class="kbd">evaluate</span> 照跑完，<span class="kbd">metrics</span> 回一個空字典
    <span class="kbd">{}</span>，你會以為是資料有問題而不是自己打錯字。
  </p>
  <a class="golab" href="__NB__" target="_blank" rel="noopener">到 notebook 的 7️⃣ 節：三個 scorer 對 v1／v2 打分</a>
</section>

<section id="s7">
  <span class="eyebrow">07 · PROMPT REGISTRY</span>
  <h2>prompt 也是資產，也要版本與 alias</h2>
  <div class="codeblock">mlflow.genai.register_prompt(name="support-answer", template="…{{context}}…{{question}}…",
                             commit_message="v2 加上拒答規則與問候語")
mlflow.genai.set_prompt_alias("support-answer", alias="production", version=2)

p = mlflow.genai.load_prompt("prompts:/support-answer@production")   # 跟著 alias 走
p.variables                                   # → {'context', 'question'}
p.format(context="退貨期限為 7 天", question="可以退嗎？")</div>
  <p>
    第 2 課你把<b>模型</b>放進 Registry：一個名字、很多版本、一個 <span class="kbd">@champion</span> 指向線上那版。
    LLM 應用有一個東西跟模型一樣重要、卻更常被改動——<b>prompt</b>。
  </p>
  <p>
    想想它的日常：產品經理說「語氣太硬」，有人在群組貼了一段新的 prompt，工程師複製貼上進程式碼，deploy。
    三天後客訴變多了。<b>上週那版 prompt 長什麼樣？</b>如果它寫在程式碼裡，也許翻得到 git log；
    如果它在資料庫、在設定檔、在某個人的筆記本裡，就沒救了。Prompt Registry 給它一套跟模型一樣的規矩：
  </p>
  <table class="cmp">
    <tr><th>URI 寫法</th><th>意思</th><th>什麼時候用</th></tr>
    <tr><td class="b"><span class="kbd">prompts:/support-answer@production</span></td><td>跟著 alias 走，晉升之後下一次載入自動變新版</td><td>服務程式碼裡</td></tr>
    <tr><td class="o"><span class="kbd">prompts:/support-answer/1</span></td><td>釘死第 1 版，之後怎麼晉升都不變</td><td>重現舊結果、A／B 對照</td></tr>
  </table>
  <p>
    晉升就是一行 <span class="kbd">set_prompt_alias(..., version=2)</span>，回滾就是把它指回去——
    跟第 2 課移 <span class="kbd">champion</span> 是同一個動作、同一套心智模型。
    四個實測到的行為，寫程式前知道比較不會受傷：
  </p>
  <table class="cmp">
    <tr><th>你做的事</th><th>實際發生什麼</th></tr>
    <tr><td>同名、<b>同內容</b>再註冊一次</td><td class="r">產生一個<b>新版本</b>（v1 的內容再註冊一次得到 v3）——不會偵測重複，別放在會重跑的迴圈裡</td></tr>
    <tr><td>載入不存在的 alias</td><td><span class="kbd">Prompt alias nope not found.</span></td></tr>
    <tr><td>載入不存在的版本</td><td><span class="kbd">Prompt (name=support-answer, version=99) not found</span></td></tr>
    <tr><td>URI 忘了 <span class="kbd">prompts:/</span> 前綴</td><td class="r"><span class="kbd">Prompt with name=support-answer@production not found</span>（它把整串當成名字了）</td></tr>
    <tr><td><span class="kbd">format()</span> 少給一個變數</td><td><span class="kbd">Missing variables: {'context'}. To partially format the prompt, set `allow_partial=True`.</span></td></tr>
  </table>
  <p>
    第二列與第三列的錯誤訊息長得不一樣，這其實很有用：看到前者是 <b>alias 沒建</b>（或打錯 alias 名），
    看到後者是<b>版本號打錯</b>——訊息本身就告訴你該去查哪裡。
  </p>
  <a class="golab" href="__NB__" target="_blank" rel="noopener">到 notebook 的 8️⃣ 節：註冊、晉升、回滾、再晉升</a>
</section>

<section id="s8">
  <span class="eyebrow">08 · 串起來</span>
  <h2>哪個回答是哪一版 prompt 生的？一查就知道</h2>
  <div class="codeblock">@mlflow.trace(name="answer_v", span_type="CHAIN")
def answer_versioned(question, uri="prompts:/support-answer@production"):
    pr = mlflow.genai.load_prompt(uri)          # ← 在 trace 內載入
    ctx = retrieve(question)
    out = llm_v(pr.format(context=ctx[0]["text"] if ctx else "", question=question))
    mlflow.update_current_trace(tags={"prompt_ver": f"v{pr.version}"})
    return out["content"]</div>
  <p>
    關鍵在那一行的位置：只要 <span class="kbd">load_prompt()</span> 是在
    <span class="kbd">@mlflow.trace</span> 的函式<b>裡面</b>呼叫的，MLflow 會自動幫這條 trace 加一個標籤
    <span class="kbd">mlflow.linkedPrompts</span>，內容是
    <span class="kbd">[{"name": "support-answer", "version": "2"}]</span>。
    <b>你不用自己記「這次用了哪版 prompt」——它自己就在 trace 上。</b>
  </p>
  <p>
    再加一個自訂 tag <span class="kbd">prompt_ver</span>，兩版的請求就分得開了。
    同樣三題、同一個模型，只換 prompt 版本（實測原文）：
  </p>
  <table class="cmp">
    <tr><th>問題</th><th>v1（沒有拒答規則）</th><th>v2（加了拒答規則與問候語）</th></tr>
    <tr><td>退貨要多久內？</td><td>退貨期限為 7 天，商品需保留原包裝與吊牌。</td><td>您好，退貨期限為 7 天，商品需保留原包裝與吊牌。</td></tr>
    <tr><td>運費怎麼算？</td><td>單筆滿 1000 元免運，未滿運費 80 元。</td><td>您好，單筆滿 1000 元免運，未滿運費 80 元。</td></tr>
    <tr><td>可以分期嗎？</td><td class="r">可以分期，通常提供 3 期與 6 期免利息。（<b>知識庫沒有這條</b>）</td><td class="g">您好，手冊裡沒有寫。</td></tr>
  </table>
  <p>
    這就是 LLMOps 的閉環，而且它跟第 5 課的訓練管線是<b>同一個形狀</b>——
    只是把「模型」換成「prompt」、把「AUC」換成「一組 scorer」：
  </p>
  <div class="codeblock">線上請求留下 trace
   → 有問題的 trace 被人標記（feedback / expectation）
   → 標記過的 trace 就是評估資料集
   → 改 prompt、register 新版本
   → 用同一批資料重跑 scorer，分數過了才 set_prompt_alias 晉升
   → 新的 trace 帶著新版本號回到第一步</div>
  <a class="golab" href="__NB__" target="_blank" rel="noopener">到 notebook 的 9️⃣ 節：v1／v2 各跑三題、比較表與 linkedPrompts</a>
</section>

<section id="s9">
  <span class="eyebrow">09 · 接上真模型</span>
  <h2>換成 OpenAI 要改幾行？一行</h2>
  <div class="codeblock">import mlflow, openai

mlflow.openai.autolog()                # ← 就這一行
client = openai.OpenAI()
resp = client.chat.completions.create(model="gpt-4o-mini", messages=[...])</div>
  <p>
    這一課從頭到尾用的是一個<b>規則式的假 LLM</b>：prompt 裡有拒答規則它就拒答，沒有它就開始編。
    這樣設計不是為了省事，是為了讓你在<b>沒有金鑰、沒有帳單、每次結果都一樣</b>的條件下把機制學完。
  </p>
  <p>
    加上 <span class="kbd">autolog()</span> 之後，每一次 API 呼叫都會自動變成一個
    <span class="kbd">CHAT_MODEL</span> span，而且比手寫的還完整：<b>模型名、temperature、每則訊息、token 用量</b>都自動記進去
    （支援的供應商還會估算費用）。你自己寫的
    <span class="kbd">@mlflow.trace(span_type="CHAIN")</span> 照舊——兩者會自動接成同一棵樹，
    因為它們共用同一個「目前的 trace」。
  </p>
  <p>
    LangChain、LlamaIndex、Anthropic、Gemini、DSPy 等等都有各自的
    <span class="kbd">autolog()</span>，用法一模一樣。<b>這一課學的 span 樹、tag、assessment、
    scorer、Prompt Registry，在真模型上一個字都不用改</b>——會變的只有兩件事：
    回答不再每次相同（所以嚴格的 scorer 分數會浮動，寫報告要寫範圍不寫點估計），
    以及 LLM span 的耗時會從 50 毫秒變成幾百毫秒到幾秒，延遲那張表的比例會整個變樣。
  </p>
  <a class="golab" href="__NB__" target="_blank" rel="noopener">到 notebook 的 🔟 節：自己問一題，看它的 span 樹</a>
</section>

<section id="s10">
  <span class="eyebrow">10 · 實戰</span>
  <h2>換你動手</h2>
  <div class="ex">
    <span class="lv">LEVEL 1</span>
    <p>客服還要能查訂單。加一個 <span class="kbd">@mlflow.trace(span_type="TOOL")</span> 的 <span class="kbd">order_status(order_id)</span>（假資料就好），讓流程在問題含訂單編號時呼叫它，然後在 span 樹裡看到那個 TOOL 節點。</p>
  </div>
  <div class="ex">
    <span class="lv">LEVEL 2</span>
    <p>寫一個 scorer <span class="kbd">grounded</span>：回答必須引用檢索到的文件。難的不是規則，是<b>例外</b>——正確的拒答要放行，憑空生出來的答案要被抓到。用它去評 v1 與 v2。</p>
  </div>
  <div class="ex">
    <span class="lv">LEVEL 3</span>
    <p>把這一課接到真模型上：裝 <span class="kbd">openai</span>、加一行 <span class="kbd">mlflow.openai.autolog()</span>、把假 LLM 換成真的 API 呼叫，其他一行都不改。怎麼確認自己做對了？span 樹裡會多出一個你沒有標過的 <span class="kbd">CHAT_MODEL</span> span。</p>
  </div>
  <p style="font-size:13.5px;color:var(--ink-soft);margin-top:10px">卡住了？每一題在 notebook 末節都有折疊解答（含實測輸出）——先自己做，再打開對照。</p>
</section>

<section id="quiz">
  <span class="eyebrow">11 · 驗收</span>
  <h2>情境測驗</h2>
  <p>離開前試試看：下面的情境都真的會遇到。每題選一個你認為的最佳做法，選了馬上看得到解釋。</p>
  <div data-quiz>

    <div class="quiz-q" data-answer="C">
      <p class="quiz-tag">Q1 <span class="qtype">情境題</span></p>
      <h3>客服機器人對「可以分期嗎？」回了一段講得很篤定的分期方案，但公司根本沒有分期。客訴進來了，你手上有這條請求的 trace。第一步該做什麼？</h3>
      <div class="quiz-opts">
        <button type="button" class="quiz-opt" data-k="A">A. 把同一個問題再問十次，看它是不是偶發</button>
        <button type="button" class="quiz-opt" data-k="B">B. 換一個更大的模型，小模型比較容易亂講</button>
        <button type="button" class="quiz-opt" data-k="C">C. 打開那條 trace 的 span 樹，看 <code>RETRIEVER</code> span 的 outputs 是不是空的、<code>LLM</code> span 的 prompt 裡「資料：」後面有沒有東西</button>
        <button type="button" class="quiz-opt" data-k="D">D. 在程式裡多加幾行 log，等下次再發生時就有線索了</button>
      </div>
      <div class="quiz-fb" aria-live="polite"><p>trace 存在的意義就是「不用重現也能查」。span 樹會直接把三種可能分開：<code>RETRIEVER</code> 的 outputs 是 <code>[]</code> ＝ 知識庫裡根本沒這條（本課實測就是這個）；有文件但 <code>LLM</code> span 的 prompt 裡沒有它 ＝ 組 prompt 的程式錯了；兩者都對卻還亂答 ＝ 才輪到模型或 prompt 規則的問題。診斷完才知道要改哪裡——本課這個案例的解法是<b>在 prompt 加拒答規則</b>，換模型或加 log 都沒打到點。A 對非決定性系統有用，但這裡的資訊已經在手上，重現只是浪費時間；B 是最貴又最沒根據的一步，檢索沒撈到文件時再大的模型也變不出資料；D 說明你還沒發現 trace 已經記完了——而且它把診斷延後到「下次再發生」。</p></div>
    </div>

    <div class="quiz-q" data-answer="B">
      <p class="quiz-tag">Q2 <span class="qtype dx">錯誤診斷</span></p>
      <h3>同事寫了一支回歸測試腳本：跑完幾個問題就把結果標記起來。它在 <span class="kbd">log_feedback</span> 這行掛掉，但同一支程式在服務裡跑得好好的。最可能的原因是？</h3>
      <div class="codeblock">for q in QUESTIONS:
    answer(q)
df = mlflow.search_traces(experiment_ids=[EXP_ID])     # 明明跑了 3 題，這裡有時 0 筆有時 2 筆
mlflow.log_feedback(trace_id=known_id, name="correct", value=True, source=SRC)

MlflowException: Trace with ID 'tr-51d4bd5e57a…' not found. It may have been deleted.</div>
      <div class="quiz-opts">
        <button type="button" class="quiz-opt" data-k="A">A. <code>experiment_ids</code> 給錯了，應該用 <code>experiment_names=["客服機器人"]</code></button>
        <button type="button" class="quiz-opt" data-k="B">B. trace 是非同步寫入的，查詢與標記之前要先 <code>mlflow.flush_trace_async_logging()</code></button>
        <button type="button" class="quiz-opt" data-k="C">C. 有人把那條 trace 刪掉了，改用 <code>mlflow.get_trace()</code> 確認它還在不在</button>
        <button type="button" class="quiz-opt" data-k="D">D. <code>log_feedback</code> 必須包在 <code>with mlflow.start_run()</code> 裡才有作用</button>
      </div>
      <div class="quiz-fb" aria-live="polite"><p>兩個症狀合起來只指向一件事：<code>search_traces</code> 回的筆數<b>比實際少、而且每次不一樣</b>，接著 <code>log_feedback</code> 說「找不到」——資料還在記憶體的緩衝區裡，根本沒進資料庫。加一行 <code>mlflow.flush_trace_async_logging()</code> 就好（本課實測：不 flush 時 0 筆或 2 筆，flush 之後穩定 3 筆）。「有時會過、有時不會」正是非同步寫入的招牌症狀。服務裡不會出事，是因為背景執行緒早晚會寫完，而服務不會「跑完馬上查」。A 更慘：<code>experiment_names</code> 這個參數不存在，會直接 <code>TypeError: search_traces() got an unexpected keyword argument 'experiment_names'. Did you mean 'experiment_ids'?</code>；C 被錯誤訊息裡的 “It may have been deleted.” 帶著走了，那只是一句籠統的提示，而且 <code>get_trace()</code> 找不到時是<b>回 <code>None</code></b>、不會拋錯，你會更困惑；D 把 trace 跟 run 搞混了，assessment 掛在 trace 上，跟 run 沒有關係。</p></div>
    </div>

    <div class="quiz-q" data-answer="D">
      <p class="quiz-tag">Q3 <span class="qtype dx">錯誤診斷</span></p>
      <h3>你寫了一個 scorer 想檢查回答有沒有引用來源。<span class="kbd">evaluate</span> 跑完沒有任何錯誤，但 <span class="kbd">metrics</span> 是一個空字典。最直接的修法是？</h3>
      <div class="codeblock">@scorer
def cites_source(answer_text) -> bool:
    return "依據" in str(answer_text)

res = mlflow.genai.evaluate(data=data, scorers=[cites_source])
print(res.metrics)      # → {}</div>
      <div class="quiz-opts">
        <button type="button" class="quiz-opt" data-k="A">A. <code>data</code> 的每一列少了 <code>expectations</code> 欄，補上就會有分數</button>
        <button type="button" class="quiz-opt" data-k="B">B. scorer 不能回傳 <code>bool</code>，要回傳 0／1 的數字才算得出平均</button>
        <button type="button" class="quiz-opt" data-k="C">C. 少了 LLM judge 的設定，<code>evaluate</code> 沒有評審模型就不會產生指標</button>
        <button type="button" class="quiz-opt" data-k="D">D. 參數名不合法：scorer 的參數只能是 <code>inputs</code> / <code>outputs</code> / <code>expectations</code> / <code>trace</code>，把 <code>answer_text</code> 改成 <code>outputs</code></button>
      </div>
      <div class="quiz-fb" aria-live="polite"><p>MLflow 是<b>照參數名</b>把資料餵給 scorer 的，名字不在那四個裡面就沒東西可餵，於是這個 scorer 整個被跳過——<b>而且不報錯</b>，<code>evaluate</code> 照樣印出「完成」，只是 <code>metrics</code> 空空如也（本課實測）。這種靜默失敗最花時間，所以看到空字典的第一個動作就是回頭看參數名。B 是誤解：<code>bool</code> 完全可以，本課三個 scorer 都回 <code>bool</code>，平均就是通過率；C 也是誤解，code-based scorer 不需要任何模型，這一課全程沒有金鑰也跑得出 <code>has_number/mean</code> 這些數字；A 只有在 scorer 真的宣告了 <code>expectations</code> 參數時才需要，這裡的問題出在更前面。</p></div>
    </div>

    <div class="quiz-q" data-answer="A">
      <p class="quiz-tag">Q4 <span class="qtype">情境題</span></p>
      <h3>團隊只盯一個指標「回答要含數字」。你把 prompt 改成 v2 加上拒答規則，修掉了亂編分期方案的問題，但這個指標從 1.000 掉到 0.667。主管說「數字變差就回滾」。你該怎麼做？</h3>
      <div class="quiz-opts">
        <button type="button" class="quiz-opt" data-k="A">A. 先看掉分的是哪一題：正確的拒答本來就沒有數字，是這個 scorer 誤殺了它——補上「拒答不扣分」的例外，並加一個直接量測拒答行為的 scorer，用一組指標再判斷</button>
        <button type="button" class="quiz-opt" data-k="B">B. 照指標回滾到 v1，再想辦法讓 v2 的拒答句裡也帶一個數字</button>
        <button type="button" class="quiz-opt" data-k="C">C. 把這個 scorer 拿掉，只留下不會掉分的指標</button>
        <button type="button" class="quiz-opt" data-k="D">D. 引進 LLM judge 取代所有 code-based scorer，讓評審模型判斷答案好不好</button>
      </div>
      <div class="quiz-fb" aria-live="polite"><p>指標掉了要先問「掉的是哪一筆、為什麼」，而不是直接相信數字。本課實測就是這個情形：v2 唯一掉分的那題答的是「手冊裡沒有寫。」——那是<b>正確行為</b>，只是不含數字；更諷刺的是 v1 那句幻覺「3 期與 6 期免利息」有數字，反而拿滿分。修法有兩層：把合法例外寫進規則（先判斷「這題本來就該有答案嗎」），以及<b>不要只有一個指標</b>——<code>refuses_when_empty</code> 從 0.667 升到 1.000 才是這次改動真正的成果。B 為了配合壞掉的量尺去扭曲產品行為，本末倒置；C 讓指標永遠好看，等於放棄評估；D 太貴也太快：judge 要錢、要金鑰，而且評審自己也會出錯——判斷得出規則的事就該用規則，judge 留給規則寫不出來的（語氣、切題）。</p></div>
    </div>

    <div class="quiz-q" data-answer="C">
      <p class="quiz-tag">Q5 <span class="qtype">情境題</span></p>
      <h3>你們的 prompt 直接寫在服務程式碼裡，每次調整就 deploy 一次。上週改過語氣之後客訴變多，但沒人說得出「上週那版長什麼樣」。要讓這件事下次不再發生，最有效的一組做法是？</h3>
      <div class="quiz-opts">
        <button type="button" class="quiz-opt" data-k="A">A. 把 prompt 搬到設定檔，每次修改在群組公告一次並附上截圖</button>
        <button type="button" class="quiz-opt" data-k="B">B. 每次改 prompt 就在程式碼裡把舊版註解掉留著，並在註解寫上日期</button>
        <button type="button" class="quiz-opt" data-k="C">C. <code>register_prompt</code> 成版本、<code>@production</code> alias 指向線上那版；服務用 <code>load_prompt("prompts:/…@production")</code> 且在 trace 內載入，出事時用 <code>mlflow.linkedPrompts</code> 查是哪一版</button>
        <button type="button" class="quiz-opt" data-k="D">D. 在每則回應的結尾附上 prompt 的 MD5，出事時比對雜湊值</button>
      </div>
      <div class="quiz-fb" aria-live="polite"><p>問題有兩半：<b>找得回舊版</b>，以及<b>知道當時線上是哪一版</b>。Registry 解前半（版本＋<code>commit_message</code>＋alias，晉升與回滾都是一行 <code>set_prompt_alias</code>）；在 <code>@mlflow.trace</code> 的函式內 <code>load_prompt</code> 解後半——MLflow 會自動幫每條 trace 掛上 <code>mlflow.linkedPrompts</code>（實測內容是 <code>[{"name": "support-answer", "version": "2"}]</code>），哪個回答由哪一版生成不用另外記。這跟第 2 課用 <code>@champion</code> 管模型是同一套心智模型。A 靠人的紀律，而且截圖無法程式化比對、也無法回滾；B 讓程式碼越長越髒，還是回答不了「線上跑的是哪一版」；D 事後比得出雜湊，卻換不回 prompt 原文，也不能一行回滾。</p></div>
    </div>

    <div class="quiz-score" data-score></div>
  </div>
</section>

<div class="endnav">
  <a href="/feature-store/">
    <span class="tag">下一課</span>
    <b>Feast 特徵倉：訓練與上線用同一份特徵 →</b>
  </a>
  <a href="/mlops/">
    <span class="tag">主題</span>
    <b>‹ 回「MLOps 自動化技術」課程列表</b>
  </a>
</div>
'''

SCRIPT = r"""
/* ═══ hero 互動：trace 瀏覽器 ═══
   六條 trace（3 個問題 × 2 版 prompt）全部是 notebook 第 9️⃣ 節的實測紀錄：
   MLflow 3.15.2、假 LLM（不打真模型）、trace id／tags／每個 span 的 inputs 與 outputs 都是原文。
   毫秒是單次量測；retrieve 20 ms、llm 50 ms 是課程刻意加上的模擬延遲。 */
(function () {
  const T = {
    "退貨要多久內？|v1": {
      id: "tr-7da28426ff7cf4f1b7c0…", ms: 150, topic: "退貨", link: '[{"name": "support-answer", "version": "1"}]',
      spans: [
        { n: "answer_v", t: "CHAIN", ms: 150.3, root: true, at: '{"n_docs": 1, "prompt_version": 1}',
          i: '{"question": "退貨要多久內？", "uri": "prompts:/support-answer/1"}',
          o: '"退貨期限為 7 天，商品需保留原包裝與吊牌。"' },
        { n: "retrieve", t: "RETRIEVER", ms: 20.4,
          i: '{"question": "退貨要多久內？"}',
          o: '[{"doc": "退貨", "text": "退貨期限為 7 天，商品需保留原包裝與吊牌。"}]' },
        { n: "llm_v", t: "LLM", ms: 50.4,
          i: '{"prompt": "你是客服。只根據資料回答。\n資料：退貨期限為 7 天，商品需保留原包裝與吊牌。\n問題：退貨要多久內？"}',
          o: '{"content": "退貨期限為 7 天，商品需保留原包裝與吊牌。",\n "usage": {"prompt_tokens": 50, "completion_tokens": 22}}' },
      ],
      ok: true, say: "檢索命中了「退貨」這份文件，模型照著資料回答——這一條沒問題。（總計 150 ms 偏高是第一次呼叫的暖機成本。）",
    },
    "退貨要多久內？|v2": {
      id: "tr-c1031b79bfe0c6d8c1a4…", ms: 84, topic: "退貨", link: '[{"name": "support-answer", "version": "2"}]',
      spans: [
        { n: "answer_v", t: "CHAIN", ms: 84.9, root: true, at: '{"n_docs": 1, "prompt_version": 2}',
          i: '{"question": "退貨要多久內？", "uri": "prompts:/support-answer@production"}',
          o: '"您好，退貨期限為 7 天，商品需保留原包裝與吊牌。"' },
        { n: "retrieve", t: "RETRIEVER", ms: 20.3,
          i: '{"question": "退貨要多久內？"}',
          o: '[{"doc": "退貨", "text": "退貨期限為 7 天，商品需保留原包裝與吊牌。"}]' },
        { n: "llm_v", t: "LLM", ms: 50.5,
          i: '{"prompt": "你是客服，語氣親切：每則回答都以「您好，」開頭。\n只根據資料回答；資料是空的就回「手冊裡沒有寫。」，不要自己猜。\n資料：退貨期限為 7 天，商品需保留原包裝與吊牌。\n問題：退貨要多久內？"}',
          o: '{"content": "您好，退貨期限為 7 天，商品需保留原包裝與吊牌。",\n "usage": {"prompt_tokens": 93, "completion_tokens": 25}}' },
      ],
      ok: true, say: "同一份文件、同一個模型，只有開頭多了問候語——差別全在 LLM span 的 prompt 那一段。",
    },
    "運費怎麼算？|v1": {
      id: "tr-a8fd88d0b26acc7cae31…", ms: 71, topic: "運費", link: '[{"name": "support-answer", "version": "1"}]',
      spans: [
        { n: "answer_v", t: "CHAIN", ms: 71.6, root: true, at: '{"n_docs": 1, "prompt_version": 1}',
          i: '{"question": "運費怎麼算？", "uri": "prompts:/support-answer/1"}',
          o: '"單筆滿 1000 元免運，未滿運費 80 元。"' },
        { n: "retrieve", t: "RETRIEVER", ms: 20.3,
          i: '{"question": "運費怎麼算？"}',
          o: '[{"doc": "運費", "text": "單筆滿 1000 元免運，未滿運費 80 元。"}]' },
        { n: "llm_v", t: "LLM", ms: 50.3,
          i: '{"prompt": "你是客服。只根據資料回答。\n資料：單筆滿 1000 元免運，未滿運費 80 元。\n問題：運費怎麼算？"}',
          o: '{"content": "單筆滿 1000 元免運，未滿運費 80 元。",\n "usage": {"prompt_tokens": 50, "completion_tokens": 23}}' },
      ],
      ok: true, say: "71 毫秒裡有 50 毫秒在等模型（70%）——延遲的大頭幾乎永遠在 LLM span 上。",
    },
    "運費怎麼算？|v2": {
      id: "tr-bd223f6b62ff02135106…", ms: 71, topic: "運費", link: '[{"name": "support-answer", "version": "2"}]',
      spans: [
        { n: "answer_v", t: "CHAIN", ms: 71.9, root: true, at: '{"n_docs": 1, "prompt_version": 2}',
          i: '{"question": "運費怎麼算？", "uri": "prompts:/support-answer@production"}',
          o: '"您好，單筆滿 1000 元免運，未滿運費 80 元。"' },
        { n: "retrieve", t: "RETRIEVER", ms: 20.3,
          i: '{"question": "運費怎麼算？"}',
          o: '[{"doc": "運費", "text": "單筆滿 1000 元免運，未滿運費 80 元。"}]' },
        { n: "llm_v", t: "LLM", ms: 50.4,
          i: '{"prompt": "你是客服，語氣親切：每則回答都以「您好，」開頭。\n只根據資料回答；資料是空的就回「手冊裡沒有寫。」，不要自己猜。\n資料：單筆滿 1000 元免運，未滿運費 80 元。\n問題：運費怎麼算？"}',
          o: '{"content": "您好，單筆滿 1000 元免運，未滿運費 80 元。",\n "usage": {"prompt_tokens": 93, "completion_tokens": 26}}' },
      ],
      ok: true, say: "prompt 長了（prompt_tokens 從 50 變 93），答案多了問候語，耗時幾乎沒差——這就是換版之後該確認的事。",
    },
    "可以分期嗎？|v1": {
      id: "tr-acf3676db215ca1389d7…", ms: 73, topic: "none", link: '[{"name": "support-answer", "version": "1"}]',
      spans: [
        { n: "answer_v", t: "CHAIN", ms: 72.7, root: true, at: '{"n_docs": 0, "prompt_version": 1}',
          i: '{"question": "可以分期嗎？", "uri": "prompts:/support-answer/1"}',
          o: '"可以分期，通常提供 3 期與 6 期免利息。"' },
        { n: "retrieve", t: "RETRIEVER", ms: 21.1,
          i: '{"question": "可以分期嗎？"}',
          o: "[]" },
        { n: "llm_v", t: "LLM", ms: 50.4,
          i: '{"prompt": "你是客服。只根據資料回答。\n資料：\n問題：可以分期嗎？"}',
          o: '{"content": "可以分期，通常提供 3 期與 6 期免利息。",\n "usage": {"prompt_tokens": 27, "completion_tokens": 22}}' },
      ],
      ok: false, say: "真相：retrieve 回 []、prompt 裡「資料：」後面是空的——知識庫根本沒有分期這條，模型自己編了。不是模型壞掉，是 prompt 沒說「查不到就閉嘴」。",
    },
    "可以分期嗎？|v2": {
      id: "tr-ee55ab999c913b64c5f9…", ms: 92, topic: "none", link: '[{"name": "support-answer", "version": "2"}]',
      spans: [
        { n: "answer_v", t: "CHAIN", ms: 92.3, root: true, at: '{"n_docs": 0, "prompt_version": 2}',
          i: '{"question": "可以分期嗎？", "uri": "prompts:/support-answer@production"}',
          o: '"您好，手冊裡沒有寫。"' },
        { n: "retrieve", t: "RETRIEVER", ms: 40.6,
          i: '{"question": "可以分期嗎？"}',
          o: "[]" },
        { n: "llm_v", t: "LLM", ms: 50.4,
          i: '{"prompt": "你是客服，語氣親切：每則回答都以「您好，」開頭。\n只根據資料回答；資料是空的就回「手冊裡沒有寫。」，不要自己猜。\n資料：\n問題：可以分期嗎？"}',
          o: '{"content": "您好，手冊裡沒有寫。",\n "usage": {"prompt_tokens": 70, "completion_tokens": 10}}' },
      ],
      ok: true, say: "檢索一樣沒撈到（retrieve 還是 []），但 prompt 多了一句「資料是空的就回手冊裡沒有寫，不要自己猜」——幻覺就沒了。改的是 prompt，不是模型。",
    },
  };

  const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  const demo = document.getElementById("tr-demo");
  const hd = document.getElementById("tr-hd");
  const tree = document.getElementById("tr-tree");
  const verdict = document.getElementById("tr-verdict");
  let q = "可以分期嗎？", v = "v1", open = -1;

  function render() {
    const t = T[q + "|" + v];
    hd.innerHTML =
      `<b>${esc(t.id)}</b>　state=<b>OK</b>　總計 <b>${t.ms} ms</b><br>` +
      `tags: {'prompt_ver': '${v}', 'topic': '${esc(t.topic)}',<br>` +
      `&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'mlflow.linkedPrompts': '${esc(t.link)}'}`;
    const widest = Math.max.apply(null, t.spans.map((s) => s.ms));
    tree.innerHTML = t.spans
      .map((s, i) => {
        const w = Math.max(3, (s.ms / widest) * 100);
        const branch = s.root ? "" : (i === t.spans.length - 1 ? "└─ " : "├─ ");
        const io =
          (s.at ? `<span class="k">ATTRIBUTES</span><pre>${esc(s.at)}</pre>` : "") +
          `<span class="k">INPUTS</span><pre>${esc(s.i)}</pre>` +
          `<span class="k">OUTPUTS</span><pre>${esc(s.o)}</pre>`;
        return (
          `<div class="sp${s.root ? "" : " kid"}${open === i ? " open" : ""}" data-i="${i}">` +
          `<div class="sp-h"><span class="nm">${branch}${esc(s.n)}</span>` +
          `<span class="ty ${s.t}">${s.t}</span>` +
          `<span class="track"><i class="${s.t}" style="width:${w.toFixed(0)}%"></i></span>` +
          `<span class="ms">${s.ms.toFixed(1)} ms</span></div>` +
          `<div class="sp-io">${io}</div></div>`
        );
      })
      .join("");
    verdict.className = "verdict" + (t.ok ? "" : " bad");
    verdict.textContent = t.say;
    tree.querySelectorAll(".sp").forEach((el) =>
      el.addEventListener("click", () => {
        const i = Number(el.dataset.i);
        open = open === i ? -1 : i;
        render();
      })
    );
  }
  document.querySelectorAll("#tr-qs button").forEach((b) =>
    b.addEventListener("click", () => {
      q = b.dataset.q;
      open = -1;
      document.querySelectorAll("#tr-qs button").forEach((x) => x.classList.toggle("on", x === b));
      render();
    })
  );
  document.querySelectorAll("#tr-vs button").forEach((b) =>
    b.addEventListener("click", () => {
      v = b.dataset.v;
      open = -1;
      document.querySelectorAll("#tr-vs button").forEach((x) => x.classList.toggle("on", x === b));
      render();
    })
  );
  render();
})();
"""

PANEL_STEPS = """
        <li>登入 molab（GitHub / Google）</li>
        <li>開啟課程 notebook，<b>Fork 成自己的副本</b>即可編輯</li>
        <li>從第一格往下全部執行（首次安裝套件約 1–2 分鐘）——<b>免費 CPU 環境即可</b>，不需要 GPU，也<b>不需要任何 API key</b>：這一課用規則式的假 LLM，機制與真模型完全一樣</li>
"""
