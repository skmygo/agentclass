"""課程頁內容區（純常數）。改完跑：python3 .claude/skills/make-lesson/scripts/page-fill.py content/mlops/mlflow-tracking
build.sh 不會部署這個檔；它是 index.html 內容區的正本。"""

TITLE = "MLflow 實驗追蹤：每一次訓練都留下證據"
DESCRIPTION = "MLflow Tracking 詳解：run 的 params／metrics／tags／artifacts、有 step 的訓練曲線、一行 autolog 自動記錄、nested runs 掃參數、用 search_runs 像查資料庫一樣查實驗——全部在 molab 免費環境實作。"
NB = "https://molab.marimo.io/github/skmygo/agentclass/blob/main/content/mlops/mlflow-tracking/mlflow-tracking_ext.py"

STYLE = r"""
  /* 語義色：藍＝params（設定）、橘＝metrics（量測）、綠＝tags（標籤）、紅＝artifacts（檔案） */
  :root { --c1: #4C72B0; --c2: #DD8452; --c3: #55A868; --cut: #C44E52; }
  a.golab { text-decoration: none; display: inline-flex; align-items: center; gap: 8px; }

  /* hero：search_runs 模擬器 */
  #sr-demo .q { display: flex; gap: 10px; flex-wrap: wrap; align-items: center; margin-bottom: 10px; }
  #sr-demo .q label { font-size: 12.5px; font-weight: 800; display: flex; flex-direction: column; gap: 4px; }
  #sr-demo input[type=text] { font-family: var(--mono); font-size: 13px; padding: 7px 10px; border: 1.5px solid var(--ink); border-radius: 8px; min-width: 280px; background: #fff; color: var(--ink); }
  #sr-demo select { font-family: var(--mono); font-size: 13px; padding: 7px 10px; border: 1.5px solid var(--ink); border-radius: 8px; background: #fff; color: var(--ink); }
  #sr-demo .chips { display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 10px; }
  #sr-demo .chips button { font-family: var(--mono); font-size: 12px; padding: 4px 9px; border-radius: 7px; border: 1.5px solid var(--grid); background: var(--chip-bg); color: var(--ink); cursor: pointer; }
  #sr-demo .chips button:hover { border-color: var(--ink); }
  #sr-demo table { width: 100%; border-collapse: collapse; font-size: 13px; font-family: var(--mono); }
  #sr-demo th, #sr-demo td { padding: 6px 8px; border-bottom: 1px solid var(--grid); text-align: left; white-space: nowrap; }
  #sr-demo th { font-size: 11.5px; letter-spacing: .04em; color: var(--ink-soft); font-family: var(--sans); }
  #sr-demo th.p { color: var(--c1); } #sr-demo th.m { color: var(--c2); } #sr-demo th.t { color: var(--c3); }
  #sr-demo tr.top td { background: rgba(221,132,82,.12); font-weight: 700; }
  #sr-demo .tbl { overflow-x: auto; }
  #sr-demo .msg { font-size: 13px; margin: 6px 0 0; color: var(--ink-soft); }
  #sr-demo .msg.err { color: var(--cut); font-family: var(--mono); font-size: 12.5px; }

  table.cmp { width: 100%; border-collapse: collapse; font-size: 13.5px; margin: 14px 0; }
  table.cmp th, table.cmp td { border-bottom: 1px solid var(--grid); padding: 8px 10px; text-align: left; vertical-align: top; }
  table.cmp th { font-size: 12px; letter-spacing: .04em; color: var(--ink-soft); }
  .kbd { font-family: var(--mono); background: var(--chip-bg); padding: 1px 6px; border-radius: 5px; font-size: 13px; }
  .four { display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; margin: 14px 0; }
  .four div { border: 1.5px solid var(--grid); border-radius: 10px; padding: 10px 12px; font-size: 13.5px; }
  .four b { display: block; font-family: var(--mono); margin-bottom: 4px; }
  .four .p b { color: var(--c1); } .four .m b { color: var(--c2); } .four .t b { color: var(--c3); } .four .a b { color: var(--cut); }
  @media (max-width: 560px) { .four { grid-template-columns: 1fr; } }
"""

WRAP = r"""
<section id="hero">
  <span class="eyebrow">MLFLOW · EXPERIMENT TRACKING · 01</span>
  <h1>MLflow 實驗追蹤：<br>每一次訓練都留下證據</h1>
  <p style="margin-top:18px">
    上週訓的模型 AUC 0.95，今天重跑變 0.92——當時 <span class="kbd">max_depth</span> 是多少？哪一版資料？哪個 commit？
    沒人記得。MLflow Tracking 把每一次訓練記成一個 <b>run</b>，幾週後一句查詢就能把當時的設定、指標、圖和模型全部翻出來。
    先體驗「像查資料庫一樣查實驗」：下面是 notebook 實際跑出來的 9 個 run，改條件看它篩：
  </p>

  <div class="hero-demo" id="sr-demo">
    <div class="q">
      <label>filter_string <input type="text" id="sr-q" value="metrics.auc > 0.95" spellcheck="false"></label>
      <label>order_by
        <select id="sr-o">
          <option value="metrics.auc DESC">metrics.auc DESC</option>
          <option value="metrics.auc ASC">metrics.auc ASC</option>
          <option value="metrics.accuracy DESC">metrics.accuracy DESC</option>
          <option value="params.max_depth ASC">params.max_depth ASC</option>
        </select>
      </label>
    </div>
    <div class="chips" id="sr-chips">
      <button type="button" data-q="metrics.auc > 0.95">metrics.auc &gt; 0.95</button>
      <button type="button" data-q="params.model = 'rf' and metrics.auc > 0.96">params.model = 'rf' and metrics.auc &gt; 0.96</button>
      <button type="button" data-q="tags.stage = 'sweep'">tags.stage = 'sweep'</button>
      <button type="button" data-q="params.model = rf">params.model = rf（少引號）</button>
    </div>
    <div class="tbl"><table id="sr-tbl"></table></div>
    <p class="msg" id="sr-msg"></p>
  </div>

  <p class="note">
    表格內容是 notebook 的實測紀錄（同一份程式、同一組亂數種子，你在 molab 跑出來會一樣）。
    notebook 裡的查詢框接的是真的 <span class="kbd">mlflow.search_runs</span>，錯誤訊息也是 MLflow 回的。
  </p>
</section>

<section id="s1">
  <span class="eyebrow">01 · 四種紀錄</span>
  <h2>一個 run 裡有什麼</h2>
  <div class="codeblock">import mlflow
mlflow.set_tracking_uri("sqlite:///mlflow.db")      # 紀錄簿放哪（正式環境換成 http://tracking-server）
mlflow.set_experiment("churn-demo")                  # 之後的 run 都歸這個實驗

with mlflow.start_run(run_name="logreg-baseline"):   # 一次訓練 = 一個 run
    mlflow.log_param("C", 1.0)                       # 設定值
    clf = LogisticRegression(C=1.0).fit(X_train, y_train)
    mlflow.log_metric("auc", roc_auc_score(y_test, clf.predict_proba(X_test)[:, 1]))   # 量測值
    mlflow.set_tag("stage", "baseline")              # 標籤
    mlflow.log_figure(fig, "plots/roc.png")          # 任何檔案</div>
  <div class="four">
    <div class="p"><b>params</b>你設定的：<span class="kbd">C=1.0</span>、<span class="kbd">max_depth=8</span>。同一個 run 內同名<b>只能記一次</b>，改了會報錯——設定就不該中途變。</div>
    <div class="m"><b>metrics</b>你量出來的：<span class="kbd">auc=0.9508</span>。同名可以記很多次，配 <span class="kbd">step</span> 就是曲線。</div>
    <div class="t"><b>tags</b>你貼的標籤，之後拿來篩選；run 結束後還能改。MLflow 也自動貼：誰跑的、哪個檔案、git commit。</div>
    <div class="a"><b>artifacts</b>任何檔案：圖、JSON、混淆矩陣、資料快照、<b>模型本身</b>。中繼資料進 SQLite，檔案落在 artifacts 資料夾（正式環境通常是 S3）。</div>
  </div>
  <p>
    實測 baseline 的 LogisticRegression：AUC 0.9508、accuracy 0.882——這兩個數字之後都會在查詢結果裡再出現。
    notebook 還會把整個目錄樹印出來給你看：MLflow 不神秘，就是<b>一個資料庫檔＋一個檔案夾</b>。
  </p>
  <a class="golab" href="__NB__" target="_blank" rel="noopener">到 notebook 的 1️⃣–2️⃣ 節：第一個 run、artifacts、磁碟目錄樹</a>
</section>

<section id="s2">
  <span class="eyebrow">02 · 曲線與自動記錄</span>
  <h2>有 step 的指標，以及一行 autolog</h2>
  <p>
    <span class="kbd">log_metric("test_logloss", v, step=n)</span> 同一個 key 記很多次就是一條曲線，事後用
    <span class="kbd">get_metric_history</span> 取回來畫。notebook 用 Gradient Boosting 記了 150 輪的 train／test log-loss：
    實測 test loss 在第 <b>116</b> 輪最低（0.239），之後 train 一路掉到 0.097、test 卻回升到 0.242——典型過擬合，
    <b>只看最後一輪的數字看不出來</b>。
  </p>
  <div class="codeblock">mlflow.sklearn.autolog()          # 一行；之後每次 .fit() 自動變成一個 run

with mlflow.start_run(run_name="rf-autolog"):
    rf = RandomForestClassifier(n_estimators=100, max_depth=6).fit(X_train, y_train)
    mlflow.log_metric("auc", roc_auc_score(y_test, rf.predict_proba(X_test)[:, 1]))   # 測試集要自己補</div>
  <p>
    手動 <span class="kbd">log_param</span> 很快就會漏，所以常見框架（scikit-learn、PyTorch、XGBoost、LightGBM、transformers、OpenAI…）都有
    <b>autolog</b>。實測這個 RandomForest 一行 <span class="kbd">log_*</span> 都沒寫，run 裡卻有
    <b>19 個 params</b>（估計器的每個超參數）、<b>7 個 training_ 指標</b>、<b>4 個 artifacts</b>
    （estimator.html、混淆矩陣、ROC、PR 曲線）＋模型本身。
    但 autolog 只看得到 <span class="kbd">fit</span>：它記的 <span class="kbd">training_roc_auc</span> 是訓練集的 0.992，
    測試集的 0.966 是我們自己補的——兩個都在，才看得出差距。
  </p>
  <a class="golab" href="__NB__" target="_blank" rel="noopener">到 notebook 的 3️⃣–4️⃣ 節：曲線重建、autolog 記了什麼</a>
</section>

<section id="s3">
  <span class="eyebrow">03 · 掃參數與查詢</span>
  <h2>nested runs，然後 search_runs 就是你的 UI</h2>
  <div class="codeblock">with mlflow.start_run(run_name="rf-depth-sweep"):              # parent：代表這次掃描
    for depth in [2, 4, 8, 16]:
        with mlflow.start_run(run_name=f"depth={depth}", nested=True):   # child：一組參數
            mlflow.log_params({"model": "rf", "max_depth": depth})
            ...
            mlflow.log_metrics({"auc": auc, "accuracy": acc})

df = mlflow.search_runs(experiment_names=["churn-demo"],
                        filter_string="params.model = 'rf' and metrics.auc > 0.96",
                        order_by=["metrics.auc DESC"])          # 回傳 pandas DataFrame</div>
  <p>
    調參一次跑很多組，用 <b>parent run ＋ nested 子 run</b> 收成一組；查詢時
    <span class="kbd">tags.mlflow.parentRunId = '…'</span> 就能撈出整組。實測 max_depth 掃描：
  </p>
  <table class="cmp">
    <tr><th>max_depth</th><th>2</th><th>4</th><th>8</th><th>16</th></tr>
    <tr><td>test AUC</td><td>0.925</td><td>0.956</td><td>0.967</td><td>0.969</td></tr>
    <tr><td>test accuracy</td><td>0.85</td><td>0.90</td><td>0.91</td><td>0.92</td></tr>
  </table>
  <p>
    <span class="kbd">search_runs</span> 回傳的是 <b>DataFrame</b>：一列一個 run，欄位 <span class="kbd">params.*</span>／<span class="kbd">metrics.*</span>／<span class="kbd">tags.*</span>
    加上狀態與時間——實測 9 個 run、51 欄。之後「比較 run」就是普通的 pandas＋matplotlib。查詢語言很小：
  </p>
  <table class="cmp">
    <tr><th>寫法</th><th>意思</th></tr>
    <tr><td><span class="kbd">metrics.auc &gt; 0.95</span></td><td>數值比較（實測命中 7 個 run）</td></tr>
    <tr><td><span class="kbd">params.model = 'rf'</span></td><td>字串<b>一定要加引號</b>，params 與 tags 的值都是字串</td></tr>
    <tr><td><span class="kbd">tags.stage != 'autolog'</span></td><td>比較子只有 <span class="kbd">= != &lt; &lt;= &gt; &gt;= LIKE ILIKE</span>，沒有 <span class="kbd">==</span></td></tr>
    <tr><td><span class="kbd">attributes.run_name LIKE 'depth%'</span></td><td>run 本身的屬性（名稱、狀態、時間）</td></tr>
    <tr><td><span class="kbd">... and ...</span></td><td>只有 and，沒有 or（要 or 就查兩次再 concat）</td></tr>
  </table>
  <p>
    notebook 最後有一組拉桿＋按鈕：按一下就真的訓練一次、記成你的 run（tag <span class="kbd">stage='yours'</span>），
    多按幾次再回查詢框看紀錄簿長大。
  </p>
  <a class="golab" href="__NB__" target="_blank" rel="noopener">到 notebook 的 5️⃣–7️⃣ 節：nested runs、查詢框、比較圖、你自己的 run</a>
</section>

<section id="s4">
  <span class="eyebrow">04 · 重現與介面</span>
  <h2>誰、用哪份程式、什麼設定——以及網頁 UI</h2>
  <p>
    每個 run 自動帶 <span class="kbd">mlflow.user</span>、<span class="kbd">mlflow.source.name</span>（哪個檔案跑的），在 git repo 內執行還有
    <span class="kbd">mlflow.source.git.commit</span>。加上 params，就是重現的線索；資料版本用 <span class="kbd">log_input</span>（第 2 課）。
  </p>
  <div class="codeblock">mlflow ui --backend-store-uri sqlite:///mlflow.db --port 5000    # 讀同一個 SQLite 檔
# 團隊共用：mlflow server ...，大家 set_tracking_uri("http://那台機器:5000")</div>
  <p>
    本課全程用程式讀紀錄簿，是為了讓你知道 UI 底下沒有魔法——網頁 UI 讀的是同一個檔，點選、並排比較、看曲線、下載 artifacts 都在裡面。
    整理紀錄：<span class="kbd">delete_run</span> 是軟刪除（實測 active 9→8、deleted 1，<span class="kbd">restore_run</span> 又回 9），
    <span class="kbd">mlflow gc</span> 才真的清磁碟。
  </p>
  <a class="golab" href="__NB__" target="_blank" rel="noopener">到 notebook 的 8️⃣ 節：自動標籤、刪除與還原</a>
</section>

<section id="s5">
  <span class="eyebrow">05 · 實戰</span>
  <h2>換你動手</h2>
  <div class="ex">
    <span class="lv">LEVEL 1</span>
    <p>再跑一個 <span class="kbd">class_weight="balanced"</span> 的 LogisticRegression，補記 <span class="kbd">recall</span>，用 <span class="kbd">search_runs</span> 把兩個 logreg run 並排比。</p>
  </div>
  <div class="ex">
    <span class="lv">LEVEL 2</span>
    <p>把「AUC &gt; 0.96 且 model = rf」的 run 全部貼上 <span class="kbd">candidate=true</span>，再用 <span class="kbd">tags.candidate = 'true'</span> 查回來確認。</p>
  </div>
  <div class="ex">
    <span class="lv">LEVEL 3</span>
    <p>把你手上任何一支訓練腳本包成 run：至少一個 param、一個 metric、一個 artifact。驗證：新開一個直譯器 <span class="kbd">search_runs</span> 找得到、<span class="kbd">download_artifacts</span> 拿得到。</p>
  </div>
  <p style="font-size:13.5px;color:var(--ink-soft);margin-top:10px">卡住了？每一題在 notebook 末節都有折疊解答——先自己做，再打開對照。</p>
</section>

<section id="quiz">
  <span class="eyebrow">06 · 驗收</span>
  <h2>情境測驗</h2>
  <p>離開前試試看：下面的情境都真的會遇到。每題選一個你認為的最佳做法，選了馬上看得到解釋。</p>
  <div data-quiz>

    <div class="quiz-q" data-answer="C">
      <p class="quiz-tag">Q1 <span class="qtype">情境題</span></p>
      <h3>你和兩位同事各自在自己筆電上用 MLflow 記錄實驗，現在想把三個人的 run 放在一起比較、找出最好的設定。最佳做法是？</h3>
      <div class="quiz-opts">
        <button type="button" class="quiz-opt" data-k="A">A. 每人把自己的 <code>mlruns</code> 資料夾壓縮傳給一個人，由他手動合併</button>
        <button type="button" class="quiz-opt" data-k="B">B. 用 <code>search_runs</code> 把各自的結果匯出成 CSV，貼進同一張試算表比較</button>
        <button type="button" class="quiz-opt" data-k="C">C. 架一台 <code>mlflow server</code>，三個人的程式都改 <code>set_tracking_uri("http://那台機器:5000")</code>，其餘程式不動</button>
        <button type="button" class="quiz-opt" data-k="D">D. 三個人輪流用同一台電腦跑實驗，紀錄自然就在同一個 SQLite 檔裡</button>
      </div>
      <div class="quiz-fb" aria-live="polite"><p>紀錄簿放哪裡只由 <code>set_tracking_uri</code> 決定——換成 tracking server 的網址，<code>log_*</code>、<code>search_runs</code>、autolog 一個字都不用改，之後的 run 直接落在同一個地方、UI 也是同一個。A 能動但每次都要重做，而且不同機器的 run id 與 artifact 路徑合併起來很痛；B 把 MLflow 最有價值的部分（可查詢、可回溯 artifacts）丟掉，只剩數字；D 沒有解決問題，只是把三個人綁在一台機器上。</p></div>
    </div>

    <div class="quiz-q" data-answer="B">
      <p class="quiz-tag">Q2 <span class="qtype dx">錯誤診斷</span></p>
      <h3>你在一個 run 裡先記了 <span class="kbd">max_depth=4</span>，跑完覺得不好，同一個 run 內又改記 8，結果炸了。最可能的原因與正確做法？</h3>
      <div class="codeblock">MlflowException: Changing param values is not allowed. Param with key='max_depth'
was already logged with value='4' for run ID='cd047f42...'. Attempted logging new value '8'.</div>
      <div class="quiz-opts">
        <button type="button" class="quiz-opt" data-k="A">A. SQLite 後端不支援更新，換成 <code>./mlruns</code> 資料夾模式就能改</button>
        <button type="button" class="quiz-opt" data-k="B">B. param 是「這次訓練的設定」，一個 run 內同名只能記一次；不同設定就是不同 run——用 nested run 或另開一個 run</button>
        <button type="button" class="quiz-opt" data-k="C">C. 先 <code>delete_run</code> 再重新 <code>log_param</code>，刪掉就能重記</button>
        <button type="button" class="quiz-opt" data-k="D">D. 改用 <code>log_metric("max_depth", 8)</code>，metric 可以重複記</button>
      </div>
      <div class="quiz-fb" aria-live="polite"><p>這是 MLflow 刻意的設計：params 代表「這個 run 是用什麼設定跑的」，允許中途改就失去重現的意義。要試另一組設定，就是另一個 run（掃參數時用 parent＋<code>nested=True</code> 的子 run 收成一組）。A 方向錯了，任何後端都擋；C 軟刪除只是把 run 標成 deleted，不會讓你「重記」；D 把設定塞進 metric 雖然不報錯，但之後 <code>params.max_depth</code> 查不到、比較時也對不上——症狀消失、問題還在。</p></div>
    </div>

    <div class="quiz-q" data-answer="A">
      <p class="quiz-tag">Q3 <span class="qtype">情境題</span></p>
      <h3>你要訓練一個跑 200 個 epoch 的模型，想事後看每個 epoch 的 train／val loss 曲線判斷有沒有過擬合。應該怎麼記？</h3>
      <div class="quiz-opts">
        <button type="button" class="quiz-opt" data-k="A">A. 每個 epoch <code>log_metric("val_loss", v, step=epoch)</code>，事後用 <code>get_metric_history</code> 取回整條曲線</button>
        <button type="button" class="quiz-opt" data-k="B">B. 每個 epoch 開一個新的 run，run 名字叫 <code>epoch-<i>n</i></code>，之後用 <code>search_runs</code> 排序</button>
        <button type="button" class="quiz-opt" data-k="C">C. 訓練結束時只記最後一個 epoch 的 <code>val_loss</code>，曲線用 print 印在終端機看</button>
        <button type="button" class="quiz-opt" data-k="D">D. 每個 epoch <code>log_param(f"val_loss_{epoch}", v)</code>，200 個 param 排開就是曲線</button>
      </div>
      <div class="quiz-fb" aria-live="polite"><p>metric 天生可以同名記很多次，配 <code>step</code> 就是曲線；notebook 裡 150 輪的 GBDT 就是這樣記的，事後才看得出 test loss 在第 116 輪之後回升。B 做得到但把一次訓練拆成 200 個 run，parent／child 關係、params 全都要重複記，UI 也塞爆；C 正是本課開頭的悲劇——只剩最後一個數字，過擬合看不見；D 會撞上 params 的設計（同名不能改、而且 200 個 key 沒有順序語義），並且查詢時 <code>params.*</code> 全是字串。</p></div>
    </div>

    <div class="quiz-q" data-answer="D">
      <p class="quiz-tag">Q4 <span class="qtype dx">錯誤診斷</span></p>
      <h3>你想找出所有 RandomForest 的 run，寫了 <span class="kbd">filter_string="params.model = rf"</span>，MLflow 回了下面這句。怎麼修？</h3>
      <div class="codeblock">MlflowException: Parameter value is either not quoted or unidentified quote types
used for string value rf. Use either single or double quotes.</div>
      <div class="quiz-opts">
        <button type="button" class="quiz-opt" data-k="A">A. <code>params.model</code> 這欄不存在——先 <code>search_runs()</code> 看欄位名，可能是 <code>params.estimator</code></button>
        <button type="button" class="quiz-opt" data-k="B">B. 比較子寫錯，字串要用 <code>==</code>：<code>params.model == rf</code></button>
        <button type="button" class="quiz-opt" data-k="C">C. 改用 <code>tags.model = rf</code>，tag 才能用字串比較</button>
        <button type="button" class="quiz-opt" data-k="D">D. 字串值要加引號：<code>params.model = 'rf'</code>——params 與 tags 的值一律是字串</button>
      </div>
      <div class="quiz-fb" aria-live="polite"><p>錯誤訊息已經把答案講白了：「not quoted」。MLflow 的查詢語言裡 params／tags 的值全是字串，比較時必須用單引號或雙引號括起來；數值比較只有 <code>metrics.*</code> 才能裸寫。A 是另一種錯誤（欄位不存在會回 <code>Invalid attribute key</code>），跟這句訊息對不上；B 更糟——<code>==</code> 根本不是合法比較子（實測回 <code>Invalid comparator '=='</code>）；C 換成 tag 一樣要加引號，沒解決問題。</p></div>
    </div>

    <div class="quiz-q" data-answer="B">
      <p class="quiz-tag">Q5 <span class="qtype">情境題</span></p>
      <h3>你開了 <span class="kbd">mlflow.sklearn.autolog()</span> 訓練，UI 上看到 <span class="kbd">training_roc_auc = 0.992</span>，很開心地把模型交出去了。同事問「那測試集呢？」——最佳做法是？</h3>
      <div class="quiz-opts">
        <button type="button" class="quiz-opt" data-k="A">A. autolog 已經評估過了，0.992 就是模型的表現，可以直接上線</button>
        <button type="button" class="quiz-opt" data-k="B">B. autolog 只看得到 <code>fit</code>，<code>training_*</code> 全是訓練集指標；在同一個 run 裡自己補 <code>log_metric("auc", 測試集AUC)</code>，兩個並排看差距</button>
        <button type="button" class="quiz-opt" data-k="C">C. 把測試集也丟進 <code>fit</code>，autolog 就會一起算出來</button>
        <button type="button" class="quiz-opt" data-k="D">D. 關掉 autolog，全部改回手動 <code>log_param</code>，比較可靠</button>
      </div>
      <div class="quiz-fb" aria-live="polite"><p>notebook 實測的 rf-autolog 正是這個情況：<code>training_roc_auc</code> 0.992、自己補的測試集 <code>auc</code> 0.966——差距就是過擬合的程度。autolog 幫你記設定、訓練指標、診斷圖與模型，但它不知道你的測試集在哪。A 會把訓練集分數當成真實表現；C 把測試集混進訓練，之後再也沒有乾淨的評估資料；D 因噎廢食，手寫反而更容易漏掉那 19 個超參數——正確用法是 autolog＋自己補測試集指標。</p></div>
    </div>

    <div class="quiz-score" data-score></div>
  </div>
</section>

<div class="endnav">
  <a href="/mlflow-registry/">
    <span class="tag">下一課</span>
    <b>MLflow Models 與 Model Registry：從「最好的 run」到「線上那一版」 →</b>
  </a>
  <a href="/mlops/">
    <span class="tag">主題</span>
    <b>‹ 回「MLOps 自動化技術」課程列表</b>
  </a>
</div>
"""

SCRIPT = r"""
/* ═══ hero 互動：search_runs 模擬器（資料＝notebook 實測的 9 個 run；查詢語法比照 MLflow）═══ */
(function () {
  const RUNS = [
    {runName:"logreg-baseline",       model:"logreg", max_depth:"",   auc:0.9508, accuracy:0.882, stage:"baseline"},
    {runName:"logreg-with-artifacts", model:"logreg", max_depth:"",   auc:0.9508, accuracy:"",    stage:"baseline"},
    {runName:"gbdt-curve",            model:"gbdt",   max_depth:"3",  auc:0.9641, accuracy:"",    stage:"curve"},
    {runName:"rf-autolog",            model:"",       max_depth:"6",  auc:0.9656, accuracy:0.906, stage:"autolog"},
    {runName:"rf-depth-sweep",        model:"",       max_depth:"",   auc:"",     accuracy:"",    stage:"sweep"},
    {runName:"depth=2",               model:"rf",     max_depth:"2",  auc:0.9252, accuracy:0.85,  stage:"sweep"},
    {runName:"depth=4",               model:"rf",     max_depth:"4",  auc:0.9564, accuracy:0.90,  stage:"sweep"},
    {runName:"depth=8",               model:"rf",     max_depth:"8",  auc:0.9674, accuracy:0.91,  stage:"sweep"},
    {runName:"depth=16",              model:"rf",     max_depth:"16", auc:0.9685, accuracy:0.92,  stage:"sweep"},
  ];
  const q = document.getElementById("sr-q"), o = document.getElementById("sr-o");
  const tbl = document.getElementById("sr-tbl"), msg = document.getElementById("sr-msg");
  const ATTR = { run_name: "runName", status: () => "FINISHED" };
  function field(r, key) {
    const [ns, name] = key.split(".");
    if (ns === "metrics") return r[name] === "" || r[name] === undefined ? null : Number(r[name]);
    if (ns === "params" || ns === "tags") { const v = r[name]; return v === undefined || v === "" ? null : String(v); }
    if (ns === "attributes" && name === "run_name") return r.runName;
    throw new Error(`Invalid attribute key '${key}' specified. Valid keys are 'metrics.*', 'params.*', 'tags.*', 'attributes.run_name'`);
  }
  function parse(s) {
    const clauses = s.trim() ? s.split(/\s+and\s+/i) : [];
    return clauses.map(c => {
      const m = c.trim().match(/^([a-z]+\.[A-Za-z_.]+)\s*(>=|<=|!=|==|=|>|<|LIKE|ILIKE)\s*(.+)$/i);
      if (!m) throw new Error(`Invalid clause(s) in filter string: '${c.trim()}'`);
      let [, key, op, val] = m; op = op.toUpperCase();
      if (op === "==") throw new Error(`Invalid comparator '==' not one of '{'ILIKE', 'LIKE', '!=', 'IS NOT NULL', 'IS NULL', '='}'`);
      const ns = key.split(".")[0];
      const quoted = /^(['"]).*\1$/.test(val.trim());
      if (ns === "metrics") { if (isNaN(Number(val))) throw new Error(`Expected numeric value type for metric. Found ${val}`); return {key, op, val: Number(val)}; }
      if (!quoted) throw new Error(`Parameter value is either not quoted or unidentified quote types used for string value ${val}. Use either single or double quotes.`);
      return {key, op, val: val.trim().slice(1, -1)};
    });
  }
  function test(r, {key, op, val}) {
    const v = field(r, key); if (v === null) return false;
    switch (op) {
      case ">": return v > val; case ">=": return v >= val; case "<": return v < val; case "<=": return v <= val;
      case "=": return v === val; case "!=": return v !== val;
      case "LIKE": return new RegExp("^" + String(val).replace(/[.*+?^${}()|[\]\\]/g, "\\$&").replace(/%/g, ".*") + "$").test(String(v));
      case "ILIKE": return new RegExp("^" + String(val).replace(/[.*+?^${}()|[\]\\]/g, "\\$&").replace(/%/g, ".*") + "$", "i").test(String(v));
    }
    return false;
  }
  function render() {
    let rows;
    try {
      const cl = parse(q.value);
      rows = RUNS.filter(r => cl.every(c => test(r, c)));
      msg.className = "msg";
    } catch (e) { msg.className = "msg err"; msg.textContent = "MlflowException: " + e.message; tbl.innerHTML = ""; return; }
    const [okey, dir] = o.value.split(" ");
    rows.sort((a, b) => { const x = field(a, okey), y = field(b, okey); if (x === null) return 1; if (y === null) return -1;
      const c = typeof x === "number" ? x - y : (Number(x) - Number(y)); return dir === "DESC" ? -c : c; });
    const cols = [["runName","run_name","a"],["model","params.model","p"],["max_depth","params.max_depth","p"],["auc","metrics.auc","m"],["accuracy","metrics.accuracy","m"],["stage","tags.stage","t"]];
    tbl.innerHTML = "<tr>" + cols.map(c => `<th class="${c[2]}">${c[1]}</th>`).join("") + "</tr>" +
      rows.map((r, i) => `<tr class="${i === 0 && okey.startsWith("metrics") ? "top" : ""}">` + cols.map(c => `<td>${r[c[0]] === "" ? "<span style='color:var(--ink-soft)'>NaN</span>" : r[c[0]]}</td>`).join("") + "</tr>").join("");
    msg.textContent = `search_runs(filter_string="${q.value}", order_by=["${o.value}"]) → ${rows.length} 個 run（共 ${RUNS.length} 個）`;
  }
  q.addEventListener("input", render); o.addEventListener("change", render);
  document.getElementById("sr-chips").addEventListener("click", e => { const b = e.target.closest("button[data-q]"); if (!b) return; q.value = b.dataset.q; render(); });
  render();
})();
"""

PANEL_STEPS = """
        <li>登入 molab（GitHub / Google）</li>
        <li>開啟課程 notebook，<b>Fork 成自己的副本</b>即可編輯</li>
        <li>從第一格往下全部執行（首次安裝套件約 1–2 分鐘）——<b>免費 CPU 環境即可</b>，不需要 GPU；紀錄簿全在暫存資料夾，不連任何伺服器</li>
"""
