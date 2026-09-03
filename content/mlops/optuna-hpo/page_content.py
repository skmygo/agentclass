"""課程頁內容區（純常數）。改完跑：python3 .claude/skills/make-lesson/scripts/page-fill.py content/mlops/optuna-hpo
build.sh 不會部署這個檔；它是 index.html 內容區的正本。"""

TITLE = "Optuna 自動調參：讓超參數搜尋自己跑"
DESCRIPTION = "四個超參數各試 5 個值就是 625 次訓練——手動掃不完。這一課把搜尋交給 Optuna：study／trial／objective 三個名詞、TPE 對隨機亂猜的誠實對照、參數重要度決定第二輪往哪搜、pruning 砍掉沒希望的 trial，而且每個 trial 都是一個 MLflow nested run。molab 免費環境全程實作。"
NB = "https://molab.marimo.io/github/skmygo/agentclass/blob/main/content/mlops/optuna-hpo/optuna-hpo_ext.py"

STYLE = r"""
  /* 語義色：藍＝Optuna／TPE、橘＝格點或隨機、綠＝目前最佳、紅＝被砍掉的 trial */
  :root { --c1: #4C72B0; --c2: #DD8452; --c3: #55A868; --cut: #C44E52; }
  a.golab { text-decoration: none; display: inline-flex; align-items: center; gap: 8px; }

  /* hero：兩種搜尋策略在同一張真實地形上花掉同樣的 25 次預算 */
  #hpo-demo .panes { display: grid; grid-template-columns: repeat(auto-fit, minmax(215px, 1fr)); gap: 14px; }
  #hpo-demo .pane { min-width: 0; border: 1.5px solid var(--grid); border-radius: 10px; padding: 9px 10px 10px; }
  #hpo-demo .ptag { display: block; font-family: var(--mono); font-size: 11px; font-weight: 800;
    letter-spacing: .07em; margin-bottom: 6px; }
  #hpo-demo .pane.tpe .ptag { color: var(--c1); }
  #hpo-demo .pane.grid .ptag { color: var(--c2); }
  #hpo-demo .board { display: grid; grid-template-columns: repeat(8, 1fr); gap: 2px;
    overflow: hidden; border-radius: 6px; }
  #hpo-demo .cell { aspect-ratio: 1 / 1; border-radius: 3px; position: relative;
    display: flex; align-items: center; justify-content: center;
    font-family: var(--mono); font-size: 9px; font-weight: 800; color: transparent; }
  #hpo-demo .cell.hit { color: #fff; box-shadow: inset 0 0 0 1.5px rgba(255,255,255,.9); }
  #hpo-demo .cell.hit.dark { color: #1C2B33; box-shadow: inset 0 0 0 1.5px rgba(28,43,51,.55); }
  #hpo-demo .cell.top { outline: 2.5px solid var(--c3); outline-offset: -2.5px; }
  #hpo-demo .stat { font-family: var(--mono); font-size: 12px; margin-top: 7px; color: var(--ink-soft); }
  #hpo-demo .stat b { color: var(--ink); font-size: 14px; }
  #hpo-demo .pane.tpe .stat b.v { color: var(--c1); }
  #hpo-demo .pane.grid .stat b.v { color: var(--c2); }
  #hpo-demo .axis { font-size: 11.5px; color: var(--ink-soft); margin-top: 12px; line-height: 1.7; }
  #hpo-demo .btns { display: flex; gap: 9px; flex-wrap: wrap; margin-top: 12px; align-items: center; }
  #hpo-demo button { font-family: inherit; font-size: 13.5px; font-weight: 800; padding: 8px 16px;
    border-radius: 999px; border: 2px solid var(--ink); background: var(--ink); color: #fff; cursor: pointer; }
  #hpo-demo button.ghost { background: #fff; color: var(--ink); }
  #hpo-demo button:disabled { opacity: .35; cursor: default; }
  #hpo-demo .verdict { font-size: 13px; line-height: 1.8; margin-top: 11px; padding-top: 10px;
    border-top: 1px solid var(--grid); color: var(--ink); }
  #hpo-demo .verdict.hidden { display: none; }

  table.cmp { width: 100%; border-collapse: collapse; font-size: 13.5px; margin: 14px 0; }
  table.cmp th, table.cmp td { border-bottom: 1px solid var(--grid); padding: 8px 10px; text-align: left; vertical-align: top; }
  table.cmp th { font-size: 12px; letter-spacing: .04em; color: var(--ink-soft); }
  table.cmp td.b { color: var(--c1); font-weight: 700; }
  table.cmp td.o { color: var(--c2); font-weight: 700; }
  table.cmp td.g { color: var(--c3); font-weight: 700; }
  table.cmp td.cut { color: var(--cut); font-weight: 700; }
  .kbd { font-family: var(--mono); background: var(--chip-bg); padding: 1px 6px; border-radius: 5px; font-size: 13px; }
"""

WRAP = r'''
<section id="hero">
  <span class="eyebrow">HPO · 補充 C · 08</span>
  <h1>Optuna 自動調參：<br>讓超參數搜尋自己跑</h1>
  <p style="margin-top:18px">
    第 1 課你用一個 <span class="kbd">for</span> 迴圈掃了 <span class="kbd">max_depth</span> 的四個值。
    問題是模型從來不只有一個旋鈕——四個超參數、每個試 5 個值，就是 625 次訓練。
    下面是一張<b>真實的分數地形</b>（40 格全部訓練過），
    兩種搜尋策略在上面花掉同樣的 25 次預算。按按鈕，看它們各自跑去哪裡——
  </p>

  <div class="hero-demo" id="hpo-demo">
    <div class="panes">
      <div class="pane tpe">
        <span class="ptag">OPTUNA（TPE）</span>
        <div class="board" id="hpo-board-tpe"></div>
        <div class="stat">試了 <b id="hpo-n-tpe">0</b> 次 · 最佳 <b class="v" id="hpo-b-tpe">—</b></div>
      </div>
      <div class="pane grid">
        <span class="ptag">格點：照順序掃</span>
        <div class="board" id="hpo-board-grid"></div>
        <div class="stat">試了 <b id="hpo-n-grid">0</b> 次 · 最佳 <b class="v" id="hpo-b-grid">—</b></div>
      </div>
    </div>
    <p class="axis">
      橫軸 <span class="kbd">max_depth</span> 2 → 16（左到右）、縱軸 <span class="kbd">min_samples_leaf</span> 1 → 10（上到下）；
      顏色越深＝交叉驗證 AUC 越高，綠框是全場最高的那一格。格子裡的數字是第幾次試到它。
    </p>
    <div class="btns">
      <button type="button" id="hpo-more">再試 5 次</button>
      <button type="button" class="ghost" id="hpo-reset">重來</button>
    </div>
    <p class="verdict hidden" id="hpo-verdict"></p>
  </div>

  <p class="note">
    40 格的分數、Optuna 那 25 次的落點順序，都是 notebook 的實測輸出
    （scikit-learn RandomForest、3 折交叉驗證、<span class="kbd">TPESampler(seed=0)</span>）——不是示意圖。
    本頁提到的「幾秒」都是同一台機器上的實測，你自己跑會不一樣——<b>看比例，不要看絕對值</b>。
    這一課的實作在 molab 執行，不需要 GPU。
  </p>
</section>

<section id="s1">
  <span class="eyebrow">01 · 組合爆炸</span>
  <h2>手動掃參數，掃到第幾個旋鈕會斷掉？</h2>
  <p>
    先算一筆很簡單的帳。假設一次訓練＋評估要 3 秒：
  </p>
  <table class="cmp">
    <tr><th>超參數的數量</th><th>每個試 5 個值</th><th>總共要跑多久</th></tr>
    <tr><td>1 個</td><td>5 種組合</td><td class="g">15 秒</td></tr>
    <tr><td>2 個</td><td>25 種</td><td class="g">1 分鐘多</td></tr>
    <tr><td>4 個</td><td>625 種</td><td class="o">半小時</td></tr>
    <tr><td>6 個</td><td>15625 種</td><td style="color:var(--cut);font-weight:700">13 小時</td></tr>
  </table>
  <p>
    真實的訓練不會只有 3 秒。而且更氣人的是：那 15625 次裡，一大半在第一眼就看得出沒希望——
    <span class="kbd">max_depth=2</span> 那一整排怎麼配都不會贏，你卻還是老老實實跑完了。
  </p>
  <p>
    notebook 第 1️⃣ 節就先把這件事做給你看：<span class="kbd">max_depth</span> 取 8 個值、
    <span class="kbd">min_samples_leaf</span> 取 5 個值，<b>40 次訓練、實測約 13–15 秒</b>，
    畫出開場那張地形圖。三個數字值得記住：最高的一格 <b>0.9710</b>（深度 10、葉子 1）、
    最低的一格 <b>0.9320</b>、而<b>最左邊那兩排 10 格，怎麼配都追不上</b>——四分之一的預算丟進水裡。
  </p>
  <p>
    地形圖還告訴你兩件事。第一，<b>兩個軸的份量差很多</b>：橫著走（換深度）最好與最差差 0.0386，
    在夠深的那半邊直著走（換葉子大小）只差 0.0079，大約五分之一。
    第二，也是最關鍵的一件：<b>格點沒有記憶</b>——它跑第 40 格的時候，知道的跟跑第 1 格時一樣多。
    前面 39 次的結果，完全沒有拿來決定下一格去哪裡。
  </p>
  <a class="golab" href="__NB__" target="_blank" rel="noopener">到 notebook 的 1️⃣ 節：把 40 格的地形跑出來</a>
</section>

<section id="s2">
  <span class="eyebrow">02 · 三個名詞</span>
  <h2>study、trial、objective：Optuna 的全部語彙</h2>
  <div class="codeblock">def objective(trial):
    x = trial.suggest_float("x", -10, 10)   # 「x 可以在 -10 到 10 之間挑」
    return (x - 2) ** 2                     # 回傳分數（這一題越小越好）

study = optuna.create_study(direction="minimize")
study.optimize(objective, n_trials=20)
study.best_params        # → {'x': 接近 2 的某個數}</div>
  <p>
    <b>objective</b> 是你寫的函式，收一個 <span class="kbd">trial</span>、回傳一個分數。
    <b>trial</b> 既是「這次用了哪組參數」的紀錄，也是你向 Optuna <b>索取</b>參數的入口——
    <span class="kbd">trial.suggest_float(...)</span> 就是在問「這次給我什麼值？」
    <b>study</b> 是一整輪搜尋：記著所有 trial、決定下一個試什麼、最後告訴你 <span class="kbd">best_params</span>。
    描述搜尋空間的方式有三種，選錯會白白浪費一半的預算：
  </p>
  <table class="cmp">
    <tr><th>寫法</th><th>什麼時候用</th><th>不這樣寫會怎樣</th></tr>
    <tr><td class="b"><span class="kbd">suggest_int("n_estimators", 20, 200, step=20)</span></td><td>整數，而且差 1 沒有意義</td><td>沒有 <span class="kbd">step</span> 就是 181 個值——搜尋空間大 10 倍，換不到任何東西</td></tr>
    <tr><td class="b"><span class="kbd">suggest_float("lr", 1e-5, 1e-1, log=True)</span></td><td>跨數量級的連續值（學習率、正規化強度）</td><td>不加 <span class="kbd">log</span>，九成的取樣會落在 0.01 以上，小的那一頭等於沒搜</td></tr>
    <tr><td class="b"><span class="kbd">suggest_categorical("max_features", ["sqrt", "log2", None])</span></td><td>選項之間沒有大小順序</td><td>硬編成 0/1/2 的整數，等於騙 Optuna 說「log2 在 sqrt 和 None 中間」</td></tr>
  </table>
  <p>
    notebook 第 2️⃣ 節用 20 個 trial 找 (x−2)² 的最小值，畫出每一次落在哪裡。
    <b>你會看到一件跟直覺相反的事：點並沒有一路收斂到 2</b>，後半段照樣有點跑到 −8、+9 去。
    這不是壞掉，是兩個設計：TPE <b>不是梯度下降</b>（它刻意保留探索，不然遇到有兩個谷的地形會死在第一個谷裡），
    而且<b>預設前 10 個 trial 是純隨機暖身</b>（<span class="kbd">n_startup_trials=10</span>，沒有資料就沒得學）。
    所以看搜尋有沒有進展，要看的是「目前為止的最佳」那條線，不是單一個點的位置。
  </p>
  <a class="golab" href="__NB__" target="_blank" rel="noopener">到 notebook 的 2️⃣ 節：20 個 trial 各落在哪裡</a>
</section>

<section id="s3">
  <span class="eyebrow">03 · 真實任務</span>
  <h2>一個 trial ＝ 一個 MLflow nested run</h2>
  <div class="codeblock">def objective(trial):
    params = {
        "n_estimators": trial.suggest_int("n_estimators", 20, 200, step=20),
        "max_depth": trial.suggest_int("max_depth", 2, 16),
        "min_samples_leaf": trial.suggest_int("min_samples_leaf", 1, 10),
        "max_features": trial.suggest_categorical("max_features", ["sqrt", "log2", None]),
    }
    with mlflow.start_run(run_name=f"trial-{trial.number}", nested=True):
        mlflow.log_params(params)
        score = cv_auc(**params)                 # 3 折交叉驗證，只用訓練集
        mlflow.log_metric("cv_auc", score)
        trial.set_user_attr("mlflow_run_id", mlflow.active_run().info.run_id)
    return score                                  # ← Optuna 只看這一個數字

with mlflow.start_run(run_name="optuna-tpe-25"):  # ← 整輪搜尋是 parent run
    study.optimize(objective, n_trials=25)</div>
  <p>
    第 1 課的 parent／nested 結構，在這裡剛好就是「<b>一次搜尋／一個 trial</b>」。
    實測 25 個 trial 約 <b>17–20 秒</b>，最佳 <b>cv_auc 0.9683</b>
    （<span class="kbd">n_estimators=80, max_depth=9, min_samples_leaf=3, max_features='sqrt'</span>），
    出現在第 16 號 trial。
  </p>
  <p>
    有一件事一定要先講清楚：<b>調參的分數要用交叉驗證，不能用測試集</b>。
    測試集只准在最後看一次。你如果拿測試集當搜尋目標，跑幾十個 trial 之後選出來的「最佳參數」，
    其實是「最會迎合那幾百筆的參數」——那個好看的分數不會出現在正式環境。
    這是調參最常見、也最貴的一個錯，而且它<b>不會報錯</b>。
  </p>
  <p>
    notebook 那張「每個 trial 的分數（點）＋目前最佳（階梯線）」的圖有兩層資訊。
    階梯線只會往上，而且越走越平——那就是「什麼時候可以停」的依據。
    但真正好看的是<b>點的分佈</b>：實測第 10 號之後最差的一次是 <b>0.9619</b>，
    而前 10 個裡最差的是 <b>0.9277</b>。<b>TPE 不是每一發都更好，它是不再往爛區丟。</b>
  </p>
  <a class="golab" href="__NB__" target="_blank" rel="noopener">到 notebook 的 3️⃣ 節：25 個 trial、25 個 nested run</a>
</section>

<section id="s4">
  <span class="eyebrow">04 · 誠實的對照</span>
  <h2>TPE 真的比亂猜好嗎？答案沒那麼漂亮</h2>
  <p>
    「聰明地挑下一組」聽起來很棒，但值得懷疑。所以直接量：同一個 objective、同一個空間、同樣 25 個 trial，
    只把取樣器換成 <span class="kbd">RandomSampler(seed=0)</span>（純隨機亂挑）。實測：
  </p>
  <table class="cmp">
    <tr><th></th><th>TPESampler</th><th>RandomSampler</th></tr>
    <tr><td>最佳 cv_auc</td><td class="b">0.9683</td><td class="o">0.9694 ←贏</td></tr>
    <tr><td>25 個 trial 的平均</td><td class="b">0.9640</td><td class="o">0.9590</td></tr>
    <tr><td>第 10 號之後最差的一次</td><td class="b">0.9619</td><td class="o">0.9280</td></tr>
    <tr><td>前 10 個 trial</td><td colspan="2" style="color:var(--ink-soft)">兩邊<b>一模一樣</b>——TPE 的暖身期就是隨機取樣器，種子也相同</td></tr>
  </table>
  <p>
    <b>這一局，最佳值是隨機贏的。</b>隨機在第 17 號 trial 矇到一個好組合——這種事很常發生，
    25 個 trial 對四維空間來說太少，運氣的份量還很重。
    （另外用 seed 1／2／3 各重跑一輪：TPE 0.9716／0.9720／0.9717，隨機 0.9716／0.9704／0.9684，
    <b>TPE 兩勝一平一敗</b>。這才是誠實的比數。）
  </p>
  <p>
    但看第二、三列：TPE 的 trial <b>品質</b>高得多。第 10 號之後隨機還在往
    <span class="kbd">max_depth=2</span> 那種爛區丟，TPE 已經不去了。
    <b>TPE 的價值不是「保證找到更好的答案」，是「同樣的預算，浪費得比較少」</b>——
    而這件事在 trial 數多（幾百次以上）、空間大（十幾個超參數）、單次評估很貴（訓練要好幾小時）
    的時候會被放大到無法忽視。你的問題如果是「四個參數、跑 20 次就夠」，老實說隨機搜尋也很好用。
  </p>
  <p>
    開場那個互動就是 notebook 第 4️⃣ 節的另一半：地形已經算好了，
    取樣器的比較就變成<b>零成本</b>（毫秒級，而且分數全是真的）。結果同樣不客氣：
    第 5 次 TPE 已經站在 0.9681、格點還在 0.9324；第 15 次 TPE 0.9687、格點 0.9656；
    <b>但第 25 次格點反而贏了</b>（0.9710 對 0.9687）。
    這句話才是重點：<b>空間小到掃得完的時候，格點最後一定會贏，因為它會把每一格都看過。</b>
    Optuna 的價值不在終點，在「同樣的預算下，你現在手上有多好的答案」——
    真實任務動輒幾萬、幾百萬格，你永遠掃不到終點。
  </p>
  <a class="golab" href="__NB__" target="_blank" rel="noopener">到 notebook 的 4️⃣ 節：對照跑一次，順便把地形當免費模擬器</a>
</section>

<section id="s5">
  <span class="eyebrow">05 · 重要度與第二輪</span>
  <h2>跑完一輪，最值錢的不是那組參數</h2>
  <div class="codeblock">evaluator = optuna.importance.FanovaImportanceEvaluator(seed=0)
optuna.importance.get_param_importances(study, evaluator=evaluator)
# → {'max_depth': 0.88, 'min_samples_leaf': 0.07, 'n_estimators': 0.03, 'max_features': 0.02}</div>
  <p>
    做法（fANOVA）是：拿你跑過的所有 trial 當訓練資料，訓練一個「參數 → 分數」的小模型，
    再問它「分數的變異，有多少可以歸給每個參數」，加起來是 1。
    <span class="kbd">seed=0</span> 別省——這個評估器本身是隨機的，不給種子同一個 study 每次算出來會差幾個百分點。
  </p>
  <p>
    實測 <span class="kbd">max_depth</span> 一個人吃掉約 <b>0.88</b>，其餘三個加起來不到 0.12。
    這正是第 1️⃣ 節那張地形圖的數字版。重要度的用途不是拿來炫耀，是<b>決定下一輪怎麼搜</b>：
  </p>
  <table class="cmp">
    <tr><th>重要度告訴你</th><th>下一輪就</th></tr>
    <tr><td>某個參數獨大</td><td class="g">把它的範圍縮到最佳值附近、取樣密一點</td></tr>
    <tr><td>某個參數幾乎是 0</td><td class="g">固定成常數，把省下來的預算讓給重要的那個</td></tr>
    <tr><td>最佳值<b>貼在範圍邊界</b></td><td class="g">把邊界往外推——真正的最佳可能在你的範圍之外</td></tr>
  </table>
  <p>
    照著做一次，效果大得有點誇張。第二輪：<span class="kbd">max_features</span> 固定成
    <span class="kbd">"sqrt"</span>、<span class="kbd">max_depth</span> 縮到 8–14、
    <span class="kbd">min_samples_leaf</span> 縮到 1–4、<span class="kbd">n_estimators</span> 下限拉到 40，
    <b>只跑 10 個 trial、約 7 秒</b>：
  </p>
  <table class="cmp">
    <tr><th></th><th>trial 數</th><th>耗時</th><th>最佳 cv_auc</th></tr>
    <tr><td>第一輪（大空間）</td><td>25</td><td>約 17–20 秒</td><td class="b">0.9683</td></tr>
    <tr><td><b>第二輪（縮小後）</b></td><td><b>10</b></td><td><b>約 7 秒</b></td><td class="g"><b>0.9716</b></td></tr>
  </table>
  <p>
    少了 15 個 trial、少花一半以上的時間，分數卻更高。更值得看的是<b>分佈</b>：
    第二輪 10 個 trial 裡有 <b>7 個</b>比第一輪跑 25 次的最佳（0.9683）還高，
    最差的一個也有 0.9661——因為它們全落在好區裡。
    <b>調參是一個迴圈，不是一次跑很多</b>：大範圍粗搜 → 看重要度與最佳值的位置 →
    縮小／平移範圍、固定不重要的參數 → 再搜一輪。<b>兩輪各 25 次，幾乎永遠贏過一輪 50 次。</b>
  </p>
  <p>
    最後兩個必要的警告。<b>重要度是估計，不是物理常數</b>：它是從你跑過的 trial 推出來的，
    而那些 trial 又是 TPE 挑的（集中在高分區），所以它回答的是「在我搜過的那一帶，哪個參數影響大」。
    實測第二輪再算一次重要度，三個參數變成幾乎平手（各約 0.32–0.35）——
    <span class="kbd">max_depth</span> 不再獨大，因為它的範圍已經全在平坦區了。
    而且<b>換一個評估器答案可能完全不同</b>：同一個 study 改用
    <span class="kbd">PedAnovaImportanceEvaluator()</span>，排第一的會變成
    <span class="kbd">min_samples_leaf</span>。把它當方向盤，不要當排行榜。
  </p>
  <p>
    最後，整堂課只有一個地方會動到<b>測試集</b>：拿第二輪的最佳參數在完整訓練集上訓練一次、
    在測試集上評一次分。這個數字不是拿來繼續調參的（一調就作廢了），它只回答一個問題：
    <b>我在交叉驗證上看到的分數，可信嗎？</b>兩個數字接近就是好消息；
    實測：交叉驗證 0.9716、測試集 <b>0.9691</b>，只差 0.0025——可信。
    如果測試分數低很多（差 0.02 以上），通常代表搜尋已經擬合了交叉驗證切分裡的雜訊——
    這時候該做的不是再多跑幾百個 trial，而是換更穩的評估（折數多一點、或重複幾次不同切分取平均）。
  </p>
  <a class="golab" href="__NB__" target="_blank" rel="noopener">到 notebook 的 5️⃣ 節：算重要度、縮小空間、跑第二輪、最後看一次測試集</a>
</section>

<section id="s6">
  <span class="eyebrow">06 · PRUNING</span>
  <h2>沒希望的 trial，不用跑完</h2>
  <div class="codeblock">for step in (1, 2, 3):          # 先長 1/3 的樹、再 2/3、再全部
    ...訓練到這個階段、算出 score...
    trial.report(score, step)          # ① 回報「我現在幾分」
    if trial.should_prune():           # ② 問 pruner「我還有救嗎」
        raise optuna.TrialPruned()     #    沒救就自首，這個 trial 標成 PRUNED</div>
  <p>
    很多模型可以<b>邊訓練邊報分數</b>：GBDT 每加一輪樹、神經網路每跑完一個 epoch、
    隨機森林每多長一批樹——中間都有暫時的成績。有了中間分數，就能做一件很划算的事：
    <b>跟別人比，比輸太多就直接放棄</b>。<span class="kbd">MedianPruner</span> 的判準很直白：
    <b>在同一個階段，你比其他 trial 的中位數還差，就砍</b>
    （<span class="kbd">n_startup_trials=5</span> 是「前 5 個一律跑完」，沒有樣本就沒有中位數可比）。
  </p>
  <table class="cmp">
    <tr><th>15 個 trial</th><th>耗時</th><th>被砍掉</th><th>最佳驗證 AUC</th></tr>
    <tr><td><span class="kbd">NopPruner()</span>（不砍）</td><td>約 9.7–9.9 秒</td><td>0</td><td>0.9564</td></tr>
    <tr><td><b><span class="kbd">MedianPruner()</span></b></td><td class="g"><b>約 6.3–6.6 秒</b></td><td class="cut"><b>8 個</b></td><td class="g"><b>0.9564</b></td></tr>
  </table>
  <p>
    <b>省下約 33–36% 的時間，最佳值一模一樣。</b>被砍的那些 trial 在只長了 1/3 棵樹的時候
    就已經落在中位數之下，再長完剩下 2/3 也追不回來。
    （這一節的分數用的是從訓練集再切出來的 375 列驗證集，跟前面幾節的交叉驗證分數是<b>兩把不同的尺</b>，
    不要互相比大小。）
  </p>
  <p>
    三件實務上會咬人的事：<b>①</b> pruning 只對「能分段回報」的模型有意義——你的 objective
    如果是一個 <span class="kbd">cross_val_score(...)</span> 就結束，中間沒有任何可回報的分數，
    掛上 pruner 也不會砍到任何東西；要嘛改成「一折報一次」，要嘛就別用。
    <b>②</b> pruning 不是免費的，它在賭「現在落後的最後也贏不了」——遇到<b>先慢後快</b>的訓練曲線
    這個賭注會輸，這時候把 <span class="kbd">n_warmup_steps</span> 調大，讓每個 trial 至少跑幾步再評判。
    <b>③</b> 被砍掉的 trial 不是白跑的：它照樣進 study，TPE 也會參考它的中間分數，
    只是 <span class="kbd">state</span> 是 <span class="kbd">PRUNED</span>、<span class="kbd">value</span> 是空的。
  </p>
  <a class="golab" href="__NB__" target="_blank" rel="noopener">到 notebook 的 6️⃣ 節：有／無 pruner 並排跑一次</a>
</section>

<section id="s7">
  <span class="eyebrow">07 · 對帳</span>
  <h2>Optuna 負責找，MLflow 負責記</h2>
  <div class="codeblock">mlflow.search_runs(
    experiment_names=["churn-hpo"],
    filter_string=f"tags.mlflow.parentRunId = '{parent_run_id}'",
    order_by=["metrics.cv_auc DESC"],
)   # → 25 列，排第一的是 trial-16，跟 study.best_trial.number 對得上</div>
  <p>
    兩邊都記，是不是多此一舉？不是——它們記的東西不一樣，缺一個都會痛：
  </p>
  <table class="cmp">
    <tr><th></th><th>Optuna 的 study</th><th>MLflow 的 run</th></tr>
    <tr><td>記什麼</td><td class="b">參數、分數、狀態、取樣器要用的分佈資訊</td><td class="o">參數、指標、標籤、<b>任何檔案</b>（模型、圖、資料快照）</td></tr>
    <tr><td>給誰看</td><td class="b">演算法（決定下一個 trial 試什麼）</td><td class="o">人（比較、翻舊帳、交接）</td></tr>
    <tr><td>跨次搜尋</td><td class="b">一個 study ＝ 一次搜尋</td><td class="o">同一個 experiment 裡，這個月的搜尋跟上個月的並排</td></tr>
    <tr><td>能不能存模型</td><td class="b">不能</td><td class="o">能——第 2 課的 <span class="kbd">log_model</span> 直接接到 Registry</td></tr>
  </table>
  <p>
    分工很清楚：<b>Optuna 負責找，MLflow 負責記</b>。最佳那組參數在 MLflow 裡有一個 run id，
    你可以順手把冠軍模型也 <span class="kbd">log_model</span> 進去，
    第 2 課的 Registry、第 6 課的上線流程就全部接得上了。
  </p>
  <p>
    官方另有 <span class="kbd">optuna-integration</span> 套件，
    裡面的 <span class="kbd">MLflowCallback</span> 一行掛上去就自動記
    （<span class="kbd">study.optimize(objective, callbacks=[MLflowCallback(metric_name="cv_auc")])</span>）。
    這一課故意手寫，因為手寫你會親眼看見「一個 trial ＝ 一個 nested run」，
    而且要記什麼、run 叫什麼名字、要不要順便存模型，全部由你決定。知道有這個 callback 就好，
    等記錄需求穩定下來再換過去。
  </p>
  <a class="golab" href="__NB__" target="_blank" rel="noopener">到 notebook 的 7️⃣ 節：撈出 25 個子 run 跟 Optuna 對答案</a>
</section>

<section id="s8">
  <span class="eyebrow">08 · 續跑與分散式</span>
  <h2>兩個參數，讓搜尋活過 notebook 關掉</h2>
  <div class="codeblock">study = optuna.create_study(
    study_name="rf-hpo",
    storage="sqlite:///optuna.db",   # ← 每個 trial 一存檔
    direction="maximize",
    load_if_exists=True,             # ← 已經有同名的就接著跑，沒有就新建
)
study.optimize(objective, n_trials=5)   # 「這一次再跑 5 個」，不是「總共要有 5 個」</div>
  <p>
    到目前為止的 study 都活在記憶體裡——<b>notebook 一關就沒了</b>。調參動輒跑幾小時，這顯然不行。
    notebook 第 8️⃣ 節示範「先跑 5 個 → 關掉 → 重新開一個 study 物件接著跑 5 個」：
    第二次是<b>全新的</b> <span class="kbd">create_study</span> 呼叫，卻看得到前 5 個 trial，
    最後累積成 10 個。整個資料庫檔案只有一百多 KB。
  </p>
  <p>
    三件相關的事：<b>①</b> <span class="kbd">load_if_exists=True</span> 一定要加，
    不加的話同名 study 撞上去會直接 <span class="kbd">DuplicatedStudyError</span>；
    而寫個 <span class="kbd">optuna.delete_study()</span> 去「解決」它，等於把昨天跑了三小時的結果刪光。
    <b>②</b> <b>這就是分散式搜尋</b>——多台機器（或多個行程）用同一個 storage、同一個
    <span class="kbd">study_name</span> 各自 <span class="kbd">optimize()</span>，
    每台都把結果寫回同一個資料庫、也都讀得到別台的結果，TPE 的建議因此越來越準；
    正式一點的做法是把 sqlite 換成 PostgreSQL／MySQL（sqlite 的檔案鎖在多寫入者下會卡住）。
    <b>③</b> <span class="kbd">optuna-dashboard</span> 讀的就是這個檔——
    <span class="kbd">optuna-dashboard sqlite:///optuna.db</span> 就有互動式的重要度圖、
    平行座標圖、等高線圖可以看。
  </p>
  <a class="golab" href="__NB__" target="_blank" rel="noopener">到 notebook 的 8️⃣–9️⃣ 節：續跑，然後自己拉桿跑一輪</a>
</section>

<section id="s9">
  <span class="eyebrow">09 · 實戰</span>
  <h2>換你動手</h2>
  <div class="ex">
    <span class="lv">LEVEL 1</span>
    <p>把 <span class="kbd">criterion</span>（<span class="kbd">"gini"</span> / <span class="kbd">"entropy"</span>）加進搜尋空間重跑 25 個 trial，再算一次重要度——它會排到第幾名？兩種 criterion 的平均分數可以直接拿來比嗎？</p>
  </div>
  <div class="ex">
    <span class="lv">LEVEL 2</span>
    <p>改成<b>多目標</b>搜尋：AUC 越高越好、樹越少越好（<span class="kbd">directions=["maximize", "minimize"]</span>）。這時候 <span class="kbd">study.best_trial</span> 會炸掉，要改用 <span class="kbd">study.best_trials</span>——找出「AUC 只掉一點點、樹卻少很多」的那一組。</p>
  </div>
  <div class="ex">
    <span class="lv">LEVEL 3</span>
    <p>把這一課的搜尋包成第 5 課那條 Dagster 管線裡的<b>一個資產</b>：<span class="kbd">best_params</span> 成為下游訓練資產的輸入，品質閘照舊。不用真的裝 dagster，先把資產的邊界、metadata 與「重跑會發生什麼」設計出來。</p>
  </div>
  <p style="font-size:13.5px;color:var(--ink-soft);margin-top:10px">卡住了？每一題在 notebook 末節都有折疊解答（含實測輸出）——先自己做，再打開對照。</p>
</section>

<section id="quiz">
  <span class="eyebrow">10 · 驗收</span>
  <h2>情境測驗</h2>
  <p>離開前試試看：下面的情境都真的會遇到。每題選一個你認為的最佳做法，選了馬上看得到解釋。</p>
  <div data-quiz>

    <div class="quiz-q" data-answer="C">
      <p class="quiz-tag">Q1 <span class="qtype">情境題</span></p>
      <h3>你要調一個模型的 4 個超參數，一次評估約 40 秒，總預算只夠跑 50 次。同事說「那就一次跑 50 個 trial 的 TPE，讓它自己找」。最佳做法是？</h3>
      <div class="quiz-opts">
        <button type="button" class="quiz-opt" data-k="A">A. 照做：50 個 trial 一次跑完，trial 越多 TPE 學得越準</button>
        <button type="button" class="quiz-opt" data-k="B">B. 改用格點搜尋，每個參數取 3 個值（81 種）裡挑 50 種來跑，至少覆蓋均勻</button>
        <button type="button" class="quiz-opt" data-k="C">C. 拆成兩輪：第一輪 25 個 trial 大範圍粗搜，看參數重要度與最佳值的位置，把不重要的參數固定、重要的範圍縮小，第二輪再跑 25 個</button>
        <button type="button" class="quiz-opt" data-k="D">D. 先跑 10 個 trial 看趨勢，如果沒有明顯變好就換模型，把預算省下來</button>
      </div>
      <div class="quiz-fb" aria-live="polite"><p>調參是一個<b>迴圈</b>，不是一次跑很多。實測就是這樣：第一輪 25 個 trial 在四維空間裡拿到 0.9683，看完重要度（<code>max_depth</code> 獨吃約 0.88）之後固定 <code>max_features</code>、把 <code>max_depth</code> 縮到 8–14、<code>min_samples_leaf</code> 縮到 1–4，第二輪<b>只跑 10 個 trial 就到 0.9716</b>，而且那 10 個裡最差的一個都比第一輪的最佳高。原因很簡單：第二輪的每一次都花在對的地方。A 不是錯，只是把一半的預算浪費在已經知道沒希望的區域（例如 <code>max_depth=2</code> 那一帶）；B 格點在小空間終究會贏，但 4 個參數各 3 個值只有 3 段解析度，而且它沒有記憶，前面 49 次的結果不會影響第 50 次；D 把「還沒縮小範圍就看不出進步」當成模型不行，很容易在第一輪的雜訊裡誤判——第一輪本來就有一半 trial 是隨機暖身。</p></div>
    </div>

    <div class="quiz-q" data-answer="B">
      <p class="quiz-tag">Q2 <span class="qtype">情境題</span></p>
      <h3>同事的 objective 寫成下面這樣，跑了 200 個 trial 拿到 AUC 0.991，開心地把那組參數送上線。兩週後線上實際表現只有 0.94。最可能的問題與修法是？</h3>
      <div class="codeblock">def objective(trial):
    model = RandomForestClassifier(**suggest_params(trial)).fit(X_train, y_train)
    return roc_auc_score(y_test, model.predict_proba(X_test)[:, 1])   # 用測試集當分數</div>
      <div class="quiz-opts">
        <button type="button" class="quiz-opt" data-k="A">A. 200 個 trial 太多導致過擬合，把 trial 數降到 30 就好</button>
        <button type="button" class="quiz-opt" data-k="B">B. objective 拿測試集當搜尋目標，選出來的是「最會迎合這批測試資料的參數」——改成只用訓練集的交叉驗證分數，測試集留到最後看一次</button>
        <button type="button" class="quiz-opt" data-k="C">C. RandomForest 本來就容易過擬合，換成梯度提升樹會比較穩</button>
        <button type="button" class="quiz-opt" data-k="D">D. 少了 <code>random_state</code>，每個 trial 的分數都有隨機性，重新固定種子再跑一次</button>
      </div>
      <div class="quiz-fb" aria-live="polite"><p>這是調參最貴、也最常見的錯，而且它<b>完全不會報錯</b>：測試集被搜尋看過 200 次之後就不再是「沒看過的資料」了，那個 0.991 是對這批測試資料的最佳擬合，不是模型的真實能力。正確做法是 objective 只用訓練集（例如 <code>cross_val_score(..., cv=3, scoring="roc_auc").mean()</code>），測試集在整輪搜尋結束後只評一次，當作最後的體檢。A 方向反了：trial 少只是「洩漏得少一點」，錯的是分數的來源不是數量；C 換模型不會改變「用測試集調參」這件事，新模型照樣會過擬合到同一批測試資料；D 固定種子讓數字可重現，但可重現的偏誤還是偏誤。</p></div>
    </div>

    <div class="quiz-q" data-answer="D">
      <p class="quiz-tag">Q3 <span class="qtype">情境題</span></p>
      <h3>你的 objective 是「訓練一個 RandomForest → 回傳 <span class="kbd">cross_val_score(...).mean()</span>」，一個 trial 要 3 分鐘。同事建議掛上 <span class="kbd">MedianPruner</span> 省時間。會發生什麼？</h3>
      <div class="quiz-opts">
        <button type="button" class="quiz-opt" data-k="A">A. 會省下大約三分之一的時間，因為 pruner 會自動在交叉驗證的第一折就判斷</button>
        <button type="button" class="quiz-opt" data-k="B">B. 會報錯，因為沒有設定 <code>n_warmup_steps</code></button>
        <button type="button" class="quiz-opt" data-k="C">C. 會砍掉太多 trial，最佳值明顯變差</button>
        <button type="button" class="quiz-opt" data-k="D">D. 什麼都不會發生——objective 中間沒有 <code>trial.report()</code>，pruner 沒有東西可以判斷；要省時間得先把交叉驗證改成「一折報一次」</button>
      </div>
      <div class="quiz-fb" aria-live="polite"><p>pruning 是「回報中間分數 ＋ 問還有沒有救」兩步組成的：<code>trial.report(score, step)</code> 之後 <code>trial.should_prune()</code> 才有東西可比。objective 如果一路算到底才回傳，pruner 從頭到尾拿不到任何中間值，掛上去也只是靜靜地什麼都不做（實測：一個沒有 report 的 objective 配上 <code>MedianPruner</code>，5 個 trial 全部 <code>COMPLETE</code>）。要在這個情境省時間，得把 <code>cross_val_score</code> 拆開自己跑迴圈，每算完一折就 report 一次——前兩折就明顯落後的組合，第三折不用算了。A 是把「pruner 很聰明」想像成它會自己拆你的函式；B 不設 <code>n_warmup_steps</code> 只是用預設值，不會報錯；C 描述的是 pruning 太積極的症狀，但前提是它真的有在砍。</p></div>
    </div>

    <div class="quiz-q" data-answer="B">
      <p class="quiz-tag">Q4 <span class="qtype dx">錯誤診斷</span></p>
      <h3>搜尋跑完 25 個 trial 都沒有報錯，但最後一行炸了。最可能的原因是？</h3>
      <div class="codeblock">def objective(trial):
    params = {...}
    with mlflow.start_run(run_name=f"trial-{trial.number}", nested=True):
        mlflow.log_params(params)
        score = cv_auc(**params)
        mlflow.log_metric("cv_auc", score)

study.optimize(objective, n_trials=25)
print(study.best_value)

ValueError: No trials are completed yet.</div>
      <div class="quiz-opts">
        <button type="button" class="quiz-opt" data-k="A">A. <code>n_trials=25</code> 太少，TPE 的暖身期是 10 個 trial，至少要跑 30 次才會有 completed 的 trial</button>
        <button type="button" class="quiz-opt" data-k="B">B. objective 沒有 <code>return score</code>——回傳 <code>None</code> 的 trial 會被標成 <code>FAIL</code> 而<b>不會拋錯</b>，25 個全掛，所以沒有任何 completed 的 trial</button>
        <button type="button" class="quiz-opt" data-k="C">C. MLflow 的 <code>start_run</code> 把 objective 的回傳值吃掉了，要改成先關掉 run 再 return</button>
        <button type="button" class="quiz-opt" data-k="D">D. <code>create_study</code> 忘了寫 <code>direction="maximize"</code>，沒有方向就無法決定 best</button>
      </div>
      <div class="quiz-fb" aria-live="polite"><p>這是 Optuna 最沉默的一種失敗：objective 回傳 <code>None</code>（或 NaN、或值的個數對不上目標數）時，Optuna <b>不會拋例外</b>，只會把該 trial 標成 <code>FAIL</code> 並記一行 warning，<code>optimize()</code> 照樣「順利」跑完 25 次。等到你去拿 <code>best_value</code>，才會撞上 <code>ValueError: No trials are completed yet.</code>。在這段程式裡，<code>score</code> 算完只餵給了 <code>log_metric</code>，函式結尾沒有 <code>return score</code>——加回去就好。事前的自保方式是跑完看一眼 <code>[t.state.name for t in study.trials]</code>，全是 <code>FAIL</code> 就知道出事了。A 完全沒有根據：暖身期的 trial 一樣會 complete；C 是憑空想像，<code>with</code> 區塊不會影響回傳值（真正的問題是根本沒有 return）；D <code>direction</code> 不寫預設是 <code>minimize</code>，會照樣算出一個 best，錯誤訊息也會完全不同。</p></div>
    </div>

    <div class="quiz-q" data-answer="C">
      <p class="quiz-tag">Q5 <span class="qtype dx">錯誤診斷</span></p>
      <h3>昨天的搜尋跑了三小時、存在 <span class="kbd">optuna.db</span> 裡。今天想接著再跑 20 個 trial，執行同一支腳本卻直接失敗。最好的修法是？</h3>
      <div class="codeblock">study = optuna.create_study(study_name="rf-hpo", storage="sqlite:///optuna.db",
                            direction="maximize")

optuna.exceptions.DuplicatedStudyError: Another study with name 'rf-hpo' already exists.
Please specify a different name, or reuse the existing one by setting `load_if_exists`
(for Python API) or `--skip-if-exists` flag (for CLI).</div>
      <div class="quiz-opts">
        <button type="button" class="quiz-opt" data-k="A">A. 先 <code>optuna.delete_study(study_name="rf-hpo", storage=...)</code> 再建，名字就不會撞了</button>
        <button type="button" class="quiz-opt" data-k="B">B. 改成 <code>study_name="rf-hpo-2"</code>，每天換一個新名字最乾淨</button>
        <button type="button" class="quiz-opt" data-k="C">C. 加 <code>load_if_exists=True</code>：同名就載入既有的 study 接著跑，<code>optimize(n_trials=20)</code> 是「再跑 20 個」，昨天的 trial 全部留著</button>
        <button type="button" class="quiz-opt" data-k="D">D. 改用 <code>optuna.load_study(...)</code>，但這樣第一次執行（資料庫還沒有這個 study）會失敗，所以要包 try/except</button>
      </div>
      <div class="quiz-fb" aria-live="polite"><p>錯誤訊息自己就寫了答案：「reuse the existing one by setting <code>load_if_exists</code>」。加上 <code>load_if_exists=True</code> 之後，這支腳本第一次跑會建立 study、之後每次跑都會接續——<code>n_trials</code> 是「<b>這一次再跑幾個</b>」而不是「總共要有幾個」，所以昨天三小時的 trial 全部保留，TPE 還會拿它們來決定接下來試什麼。A 是最貴的一個選項：<code>delete_study</code> 會把昨天的結果整個刪掉，而且完全沒有警告。B 能跑，但每天一個新 study 等於每天從零開始暖身（前 10 個 trial 又是隨機），也失去了跨天累積的意義。D 方向對但繞遠路：<code>load_study</code> 在 study 不存在時會丟 <code>KeyError: 'Record does not exist.'</code>，用 try/except 去補一個 <code>load_if_exists=True</code> 一行就能做到的事。</p></div>
    </div>

    <div class="quiz-score" data-score></div>
  </div>
</section>

<div class="endnav">
  <a href="/data-validation/">
    <span class="tag">下一課</span>
    <b>資料驗證：pandera 幫資料寫合約，壞資料進不了管線 →</b>
  </a>
  <a href="/mlops/">
    <span class="tag">主題</span>
    <b>‹ 回「MLOps 自動化技術」課程列表</b>
  </a>
</div>
'''

SCRIPT = r"""
/* ═══ hero 互動：兩種搜尋策略，同一張真實地形，同樣 25 次預算 ═══
   GRID    = notebook 1️⃣ 節實測的 8×5 cv_auc 格點（RandomForest 60 棵樹、3 折交叉驗證）
   TPE_SEQ = notebook 4️⃣ 節 TPESampler(seed=0) 在這張表上 25 個 trial 的落點順序
   格點那一側是 for max_depth: for min_samples_leaf: 的掃描順序（列優先）。 */
(function () {
  const DEPTHS = [2, 4, 6, 8, 10, 12, 14, 16];
  const LEAVES = [1, 3, 5, 7, 10];
  const GRID = [
    [0.9324, 0.9321, 0.9322, 0.9324, 0.9320],
    [0.9565, 0.9574, 0.9582, 0.9561, 0.9573],
    [0.9656, 0.9655, 0.9655, 0.9641, 0.9620],
    [0.9700, 0.9673, 0.9666, 0.9658, 0.9626],
    [0.9710, 0.9680, 0.9667, 0.9663, 0.9628],
    [0.9695, 0.9683, 0.9672, 0.9663, 0.9629],
    [0.9687, 0.9682, 0.9674, 0.9665, 0.9631],
    [0.9681, 0.9681, 0.9674, 0.9665, 0.9631],
  ];
  const TPE_SEQ = [[7,0],[7,0],[1,4],[3,3],[0,2],[7,1],[5,3],[7,4],[5,4],[5,3],
                   [2,1],[7,0],[4,1],[6,0],[6,1],[6,2],[6,0],[6,0],[6,0],[6,0],
                   [2,0],[6,0],[6,0],[6,0],[0,0]];
  const GRID_SEQ = [];
  for (let d = 0; d < DEPTHS.length; d++) for (let l = 0; l < LEAVES.length; l++) GRID_SEQ.push([d, l]);
  const TOTAL = TPE_SEQ.length;

  let lo = Infinity, hi = -Infinity;
  GRID.forEach((row) => row.forEach((v) => { if (v < lo) lo = v; if (v > hi) hi = v; }));
  let bestD = 0, bestL = 0;
  GRID.forEach((row, d) => row.forEach((v, l) => { if (v === hi) { bestD = d; bestL = l; } }));

  /* 淺米 → 深藍的色階（越深＝分數越高）；t 用平方根拉開高分區的差異 */
  function shade(v) {
    const t = Math.pow((v - lo) / (hi - lo), 2.0);
    const c0 = [247, 251, 238], c1 = [26, 66, 110];
    const c = c0.map((a, i) => Math.round(a + (c1[i] - a) * t));
    return { css: `rgb(${c[0]},${c[1]},${c[2]})`, dark: t < 0.42 };
  }

  function buildBoard(el) {
    el.innerHTML = "";
    const cells = [];
    for (let l = 0; l < LEAVES.length; l++) {
      for (let d = 0; d < DEPTHS.length; d++) {
        const cell = document.createElement("div");
        const sh = shade(GRID[d][l]);
        cell.className = "cell" + (sh.dark ? " dark" : "");
        cell.style.background = sh.css;
        cell.title = `max_depth=${DEPTHS[d]}, min_samples_leaf=${LEAVES[l]} → cv_auc ${GRID[d][l].toFixed(4)}`;
        el.appendChild(cell);
        cells[d * LEAVES.length + l] = cell;
      }
    }
    return cells;
  }

  const boards = {
    tpe: { cells: buildBoard(document.getElementById("hpo-board-tpe")), seq: TPE_SEQ,
           n: document.getElementById("hpo-n-tpe"), b: document.getElementById("hpo-b-tpe") },
    grid: { cells: buildBoard(document.getElementById("hpo-board-grid")), seq: GRID_SEQ,
            n: document.getElementById("hpo-n-grid"), b: document.getElementById("hpo-b-grid") },
  };
  const moreBtn = document.getElementById("hpo-more");
  const resetBtn = document.getElementById("hpo-reset");
  const verdict = document.getElementById("hpo-verdict");
  let shown = 0;

  function render() {
    Object.keys(boards).forEach((k) => {
      const bd = boards[k];
      let best = -Infinity;
      const first = {};
      bd.cells.forEach((c) => {
        c.className = c.className.replace(/ hit| top/g, "");
        c.textContent = "";
      });
      for (let i = 0; i < shown; i++) {
        const [d, l] = bd.seq[i];
        const v = GRID[d][l];
        if (v > best) best = v;
        const key = d * LEAVES.length + l;
        if (first[key] === undefined) first[key] = i + 1;
      }
      Object.keys(first).forEach((key) => {
        const c = bd.cells[key];
        c.className += " hit";
        c.textContent = first[key];
      });
      bd.cells[bestD * LEAVES.length + bestL].className += " top";
      bd.n.textContent = shown;
      bd.b.textContent = shown ? best.toFixed(4) : "—";
    });
    moreBtn.disabled = shown >= TOTAL;
    moreBtn.textContent = shown >= TOTAL ? "25 次用完了" : "再試 5 次";
    if (shown >= TOTAL) {
      verdict.classList.remove("hidden");
      verdict.innerHTML =
        "25 次用完：格點 <b>0.9710</b>、Optuna <b>0.9687</b>——<b>空間小到掃得完的時候，格點終究會贏</b>，" +
        "因為它會把每一格都看過。但一路上 Optuna 都遙遙領先（第 5 次就 0.9681，格點還在 0.9324）。" +
        "真實任務有幾萬、幾百萬格，你永遠掃不到終點——能拿到的只有「預算用完那一刻手上的最佳」。";
    } else {
      verdict.classList.add("hidden");
    }
  }

  moreBtn.addEventListener("click", () => { shown = Math.min(TOTAL, shown + 5); render(); });
  resetBtn.addEventListener("click", () => { shown = 0; render(); });
  render();
})();
"""

PANEL_STEPS = """
        <li>登入 molab（GitHub / Google）</li>
        <li>開啟課程 notebook，<b>Fork 成自己的副本</b>即可編輯</li>
        <li>從第一格往下全部執行（首次安裝套件約 1–2 分鐘）——<b>免費 CPU 環境即可</b>，不需要 GPU；整份跑完約 2 分鐘，因為它真的在訓練幾百棵森林</li>
"""
