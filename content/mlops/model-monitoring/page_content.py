"""課程頁內容區（純常數）。改完跑：python3 .claude/skills/make-lesson/scripts/page-fill.py content/mlops/model-monitoring
build.sh 不會部署這個檔；它是 index.html 內容區的正本。"""

TITLE = "模型監控：資料漂移、預測漂移，與什麼時候該重訓"
DESCRIPTION = "模型上線後最危險的不是壞掉，是默默變差。手算 PSI 與 KS 檢定、看沒有標籤也算得出來的預測漂移、用 Evidently 出報告（以及它的預設門檻怎麼騙你），最後把漂移分數變成 retrain／watch／ok 的決策，接成 Dagster 的資產檢查與觸發重訓的 sensor——molab 免費環境全程實作。"
NB = "https://molab.marimo.io/github/skmygo/agentclass/blob/main/content/mlops/model-monitoring/model-monitoring_ext.py"

STYLE = r"""
  /* 語義色：藍＝參考視窗、橘＝當前（漂移）視窗、綠＝通過／ok、紅＝警報／重訓 */
  :root { --c1: #4C72B0; --c2: #DD8452; --c3: #55A868; --cut: #C44E52; }
  a.golab { text-decoration: none; display: inline-flex; align-items: center; gap: 8px; }

  /* hero：漂移儀表板 */
  #dm .ctl { display: flex; flex-wrap: wrap; gap: 14px; align-items: center; margin-bottom: 14px; }
  #dm .ctl label { font-size: 12.5px; font-weight: 800; display: inline-flex; align-items: center; gap: 8px; }
  #dm .ctl input[type=range] { width: 132px; accent-color: var(--c2); }
  #dm .ctl .val { font-family: var(--mono); font-size: 12.5px; color: var(--c2); min-width: 34px; }
  #dm .ctl button { font-family: var(--mono); font-size: 12px; padding: 5px 10px; border-radius: 8px; border: 1.5px solid var(--ink); background: #fff; color: var(--ink); cursor: pointer; }
  #dm .ctl button:hover { background: var(--chip-bg); }

  #dm .bars { display: grid; grid-template-columns: repeat(12, 1fr); gap: 4px; align-items: end; height: 116px; margin-bottom: 6px; position: relative; }
  #dm .bar { background: var(--c1); border-radius: 3px 3px 0 0; min-height: 2px; transition: height .18s ease, background .18s ease; }
  #dm .bar.over { background: var(--c2); }
  #dm .bar.alarm { background: var(--cut); }
  #dm .names { display: grid; grid-template-columns: repeat(12, 1fr); gap: 4px; font-family: var(--mono); font-size: 9.5px; color: var(--ink-soft); text-align: center; margin-bottom: 12px; }
  #dm .thr { position: absolute; left: 0; right: 0; border-top: 1.5px dashed var(--c3); }
  #dm .thr span { position: absolute; right: 0; top: -13px; font-family: var(--mono); font-size: 9.5px; color: var(--c3); background: var(--paper); padding: 0 3px; }
  #dm .thr.a { border-top-color: var(--cut); }
  #dm .thr.a span { color: var(--cut); }

  #dm .out { display: grid; grid-template-columns: repeat(auto-fit, minmax(122px, 1fr)); gap: 8px; margin-bottom: 10px; }
  #dm .cell { background: var(--chip-bg); border-radius: 10px; padding: 8px 10px; }
  #dm .cell .k { font-size: 11px; color: var(--ink-soft); letter-spacing: .03em; }
  #dm .cell .v { font-family: var(--mono); font-size: 17px; font-weight: 800; }
  #dm .cell .s { font-family: var(--mono); font-size: 11px; color: var(--ink-soft); }
  #dm .verdict { border-radius: 10px; padding: 9px 12px; font-size: 13.5px; font-weight: 800; border: 2px solid var(--c3); color: var(--c3); }
  #dm .verdict.watch { border-color: var(--c2); color: var(--c2); }
  #dm .verdict.retrain { border-color: var(--cut); color: var(--cut); }
  @media (max-width: 560px) { #dm .names { font-size: 8px; } #dm .bars { height: 92px; } }

  /* 節內小標（加 class，別用裸 h3——會蓋掉共用的測驗版型） */
  #lesson h3.sub {
    font-size: 17px; font-weight: 900; letter-spacing: -.01em;
    margin: 30px 0 10px; padding-left: 11px; border-left: 4px solid var(--ink);
  }

  /* 教學欄的編號清單（class 不可省：page-fill 會把沒有 class 的編號清單換成 molab 面板步驟） */
  #lesson ol.parts { padding-left: 22px; margin: 12px 0; }
  #lesson ol.parts li { font-size: 15px; line-height: 1.95; margin: 4px 0; }

  table.cmp { width: 100%; border-collapse: collapse; font-size: 13.5px; margin: 14px 0; }
  table.cmp th, table.cmp td { border-bottom: 1px solid var(--grid); padding: 8px 10px; text-align: left; vertical-align: top; }
  table.cmp th { font-size: 12px; letter-spacing: .04em; color: var(--ink-soft); }
  .kbd { font-family: var(--mono); background: var(--chip-bg); padding: 1px 6px; border-radius: 5px; font-size: 13px; }
"""

WRAP = r"""
<section id="hero">
  <span class="eyebrow">MONITORING · 補充 B · 07</span>
  <h1>模型監控：資料漂移、預測漂移，<br>與什麼時候該重訓</h1>
  <p style="margin-top:18px">
    模型上線後最危險的事不是壞掉——壞掉會噴 500、警報會響、有人會被叫起來。危險的是<b>它還在回答，只是答得越來越爛</b>：
    沒有例外、儀表板一片綠，準確率卻從 0.916 滑到 0.864，你要等季末業務抱怨才知道。
    先玩玩看：把兩個特徵推歪，看監控指標怎麼反應——
  </p>

  <div class="hero-demo" id="dm">
    <div class="ctl">
      <label>f0 平移 <input type="range" id="dm-shift" min="0" max="2" step="0.25" value="1.5"><span class="val" id="dm-shift-v">1.50</span></label>
      <label>f3 放大 <input type="range" id="dm-scale" min="1" max="3" step="0.25" value="2"><span class="val" id="dm-scale-v">2.00</span></label>
      <button type="button" id="dm-reset">一切正常</button>
      <button type="button" id="dm-bad">壞掉的那一週</button>
    </div>
    <div class="bars" id="dm-bars"></div>
    <div class="names" id="dm-names"></div>
    <div class="out" id="dm-out"></div>
    <div class="verdict" id="dm-verdict"></div>
  </div>

  <p class="note">
    每一根柱子都是 notebook 真的算出來的 PSI（12 個特徵 × 81 種漂移組合全部實跑過），
    accuracy 那一格在真實世界要等標籤回來才看得到——這堂課大半的功夫，就花在「還看不到它」的那段時間裡。
  </p>
</section>

<section id="s1">
  <span class="eyebrow">01 · 三種漂移</span>
  <h2>症狀看得到，病因要等</h2>
  <table class="cmp">
    <tr><th>漂移</th><th>變的是什麼</th><th>什麼時候看得到</th></tr>
    <tr><td><b>資料漂移</b><br>data / covariate drift</td><td>輸入 <span class="kbd">X</span> 的分佈變了</td><td><b>馬上</b>——有輸入就算得出來</td></tr>
    <tr><td><b>預測漂移</b><br>prediction drift</td><td>模型輸出的機率分佈變了</td><td><b>馬上</b>——模型有在跑就算得出來</td></tr>
    <tr><td><b>概念漂移</b><br>concept drift</td><td>輸入與標籤的關係變了</td><td><b>要等標籤</b>——可能好幾週</td></tr>
  </table>
  <p>
    前兩種是<b>症狀</b>（免費、即時、不需要標籤），第三種是<b>病因</b>（要等，而且常常等很久）。
    監控的全部藝術就在這句話裡：<b>用看得到的症狀，去猜看不到的病因，而且要在損失擴大之前決定要不要重訓。</b>
  </p>
  <p>
    這堂課的前導課用模擬曲線給你看過那條下滑的準確率（<a href="/mlops-why/">為什麼需要 MLOps</a>），
    而且做過一個很重要的對照：<b>只有資料漂移時準確率 0.945 幾乎不掉，概念漂移時卻掉到 0.660</b>——
    輸入變了不一定有事，輸入沒變也不一定沒事。這一課是它的工具版：同一件事，換成正式環境真的會用的指標與自動化。
  </p>
  <p>
    素材沿用整個系列：2000 筆客戶流失資料、12 個特徵、RandomForest champion（accuracy <b>0.916</b>、AUC <b>0.9684</b>）。
    我們刻意造一份漂移過的生產資料：<span class="kbd">f0</span> 整欄平移 +1.5、<span class="kbd">f3</span> 整欄放大 2 倍。
    真實世界的漂移長這樣：上游把公分換成公尺、行銷把客群從 25 歲拉到 45 歲、某個欄位的預設值從 0 改成 NaN。
    <b>列數一樣、欄位一樣、沒有缺值，程式一個錯都不會報。</b>
  </p>
  <a class="golab" href="__NB__" target="_blank" rel="noopener">到 notebook 的 0️⃣ 節：champion 模型與那批怪怪的生產資料</a>
</section>

<section id="s2">
  <span class="eyebrow">02 · PSI 與 KS</span>
  <h2>先自己算，才知道工具在算什麼</h2>
  <div class="codeblock">def psi(ref, cur, bins=10):
    edges = np.quantile(ref, np.linspace(0, 1, bins + 1))
    edges[0], edges[-1] = -np.inf, np.inf          # 兩端開放，平移出去的資料才不會掉光
    r = np.histogram(ref, edges)[0] / len(ref) + 1e-6   # 1e-6：空箱時不要 log(0)
    c = np.histogram(cur, edges)[0] / len(cur) + 1e-6
    return float(np.sum((c - r) * np.log(c / r)))      # PSI = Σ (c−r) × ln(c/r)</div>
  <p>
    <b>PSI</b>（Population Stability Index）只有三步：用<b>參考視窗</b>的十分位數分箱、算兩邊落在每箱的比例、
    把「比例差 × 比例的倍數變化」加總。兩個細節是血淚換來的：<b>兩端要開放</b>，
    否則平移過的資料落不進任何箱子；<b>比例要加一個極小值</b>，否則只要有一箱是空的，
    <span class="kbd">log(0)</span> 會讓整個 PSI 變成 <span class="kbd">inf</span>（實測：<span class="kbd">f0</span> 平移 8 不加 <span class="kbd">1e-6</span> 就是 <span class="kbd">inf</span>，加了是 12.434）。
  </p>
  <h3 class="sub">最重要的一步：跑一組對照</h3>
  <table class="cmp">
    <tr><th>參考視窗 → 當前視窗</th><th>最大 PSI</th><th>超過 0.1 的欄數</th></tr>
    <tr><td>訓練集 1500 → <b>沒動過的</b> test 500（對照組）</td><td>0.082（<span class="kbd">f4</span>）</td><td><b>0 / 12</b></td></tr>
    <tr><td>訓練集 1500 → 漂移過的生產資料 500</td><td><b>0.558</b>（<span class="kbd">f3</span>）、0.487（<span class="kbd">f0</span>）</td><td><b>2 / 12</b></td></tr>
  </table>
  <p>
    對照組的 PSI <b>不會是 0</b>——兩份資料本來就是不同抽樣。這個「雜訊底線」（這裡是 0.082）
    才是門檻該訂在哪裡的依據。業界慣例的 0.1／0.25 是起點，不是定理：
    <b>PSI 會隨視窗大小變動</b>（實測同一個小漂移，視窗 10000 筆時 PSI 0.010、縮到 50 筆時衝到 0.243），
    所以視窗大小一改，門檻全部要重新校準。
  </p>
  <h3 class="sub">KS 檢定：問錯問題的好工具</h3>
  <div class="codeblock">stats.ks_2samp(X_train["f3"], prod["f3"]).pvalue     # 7.7e-20  ← 漂移過的，方向跟 PSI 一致
stats.ks_2samp(X_train["f3"], X_test["f3"]).pvalue   # 0.0400   ← 對照組，什麼都沒發生也 < 0.05</div>
  <p>
    KS 檢定量的是兩條累積分佈曲線的最大垂直距離，p 值回答「假設兩邊來自同一個分佈，看到這麼大差距的機率」。
    問題是<b>它回答的不是你想問的問題</b>：它問「有沒有差異」，你想知道的是「差異大不大、要不要管」。
    實測對照組裡 <span class="kbd">f3</span>（p 0.0400）與 <span class="kbd">f7</span>（p 0.0429）兩欄都低於 0.05——
    照「p &lt; 0.05 就警報」寫，這兩欄今天就會叫你起床。更糟的是<b>樣本越多它越吵</b>：
    完全沒漂移的資料，視窗 50 筆時 p = 0.92，10000 筆時 p 已經到 1e-05。
  </p>
  <p>
    實務結論：<b>用效果量（PSI／Wasserstein）當主判準、統計檢定當輔助</b>，而且兩者一起看——
    p 值小<b>而且</b> PSI 大，才值得處理。
  </p>
  <a class="golab" href="__NB__" target="_blank" rel="noopener">到 notebook 的 1️⃣2️⃣ 節：分箱表、對照組、視窗大小實驗</a>
</section>

<section id="s3">
  <span class="eyebrow">03 · 預測漂移</span>
  <h2>沒有標籤，也有東西可以看</h2>
  <div class="codeblock">p_ref  = champion.predict_proba(X_test)[:, 1]   # 上線第一週：模型沒看過、表現正常
p_prod = champion.predict_proba(prod)[:, 1]

p_ref.mean(), p_prod.mean()                     # 0.507 → 0.471   平均機率
(p_ref > .5).mean(), (p_prod > .5).mean()       # 0.520 → 0.444   判正率
psi(p_ref, p_prod)                              # 0.166           預測分佈 PSI</div>
  <p>
    輸入有 12 欄，實務上可能有 300 欄，逐欄看很吵。<b>預測漂移直接看模型的輸出</b>：一欄就好、
    不需要標籤、而且直接對應到業務影響（判為流失的比例掉了 15%，行銷名單就短了 15%）。
    實測模型變得<b>沒那麼有把握</b>：高信心（&gt;0.8）的客戶從 34% 掉到 26%。
  </p>
  <p>
    ⚠️ <b>參考分佈不能用訓練集的預測</b>。模型看過訓練集，在上面的機率會過度自信。
    實測拿訓練集預測當參考、測試集預測當當前，PSI 是 <b>0.183</b>——資料一個字都沒漂移，
    分數卻比真的漂移（0.166）還高。<b>參考視窗選錯，整套監控就是白做的。</b>
  </p>
  <table class="cmp">
    <tr><th>訊號</th><th>這次的數字</th><th>什麼時候拿得到</th></tr>
    <tr><td>資料漂移（最大 PSI）</td><td>0.558（<span class="kbd">f3</span>）</td><td>立刻</td></tr>
    <tr><td>預測漂移（PSI）</td><td>0.166</td><td>立刻</td></tr>
    <tr><td>accuracy</td><td>0.916 → <b>0.864</b></td><td>等標籤，可能好幾週</td></tr>
  </table>
  <p>
    標籤回來之後才看得到的那一列：accuracy 掉了 5.2 個百分點，500 個客戶裡多判錯 26 個。
    但注意 <b>AUC 只從 0.9684 掉到 0.9575</b>——<b>排序能力幾乎沒壞，壞的是校準</b>：
    模型還是知道誰比較可能流失，只是「多少機率算高」那條線跑掉了。這種情況調門檻常常就能救回大半，
    不一定要重訓——也就是為什麼警報之後還要有一個人去看一眼。
  </p>
  <a class="golab" href="__NB__" target="_blank" rel="noopener">到 notebook 的 3️⃣ 節：預測分佈疊圖與 in-sample 陷阱</a>
</section>

<section id="s4">
  <span class="eyebrow">04 · EVIDENTLY</span>
  <h2>三行出報告，但預設值不是真理</h2>
  <div class="codeblock">from evidently import Dataset, DataDefinition, Report
from evidently.presets import DataDriftPreset

definition = DataDefinition(numerical_columns=FEATURES)      # 型別宣告錯，方法就換掉
ref_ds = Dataset.from_pandas(X_train, data_definition=definition)
cur_ds = Dataset.from_pandas(prod,    data_definition=definition)

snapshot = Report([DataDriftPreset()]).run(cur_ds, ref_ds)   # 當前在前、參考在後
snapshot.dict()["metrics"]        # 每項有 metric_name / config / value</div>
  <p>
    Evidently 是目前最常見的開源漂移監控套件，它幫你做三件事：<b>依欄位型別自動挑方法</b>、
    <b>產出可以拿去開會的 HTML 報告</b>、<b>把結果變成可程式判讀的字典</b>。
    預設方法是 Wasserstein distance（normed）、門檻 0.1。
  </p>
  <table class="cmp">
    <tr><th></th><th>被判漂移的欄數</th><th>最高分</th><th>第二高</th></tr>
    <tr><td>實驗組（真的漂移了）</td><td><b>3 / 12</b></td><td><span class="kbd">f3</span> 0.813</td><td><span class="kbd">f0</span> 0.695</td></tr>
    <tr><td>對照組（什麼都沒發生）</td><td><b>3 / 12</b></td><td><span class="kbd">f0</span> 0.114</td><td><span class="kbd">f2</span> 0.111</td></tr>
  </table>
  <p>
    <b>兩組的「被判漂移欄數」一模一樣。</b>用預設門檻，一份完全沒漂移的資料照樣被判 3 欄漂移。
    差別完全在<b>分數的量級</b>（0.813 vs 0.114）。三句話帶走：
    <b>「幾欄超標」是資訊量最低的指標</b>，卻是最多人拿來當警報條件的那一個；
    <b>任何工具的預設門檻都要用自己的「已知正常」資料校準過</b>；<b>對照組不是可選的</b>。
  </p>
  <p>
    Wasserstein 量的是「把一堆土從參考分佈搬成當前分佈平均要搬多遠」，PSI 量的是「分箱後每箱比例變了幾倍」。
    整欄平移兩者都抓得到；某一小群客戶忽然消失，PSI 反應大、Wasserstein 幾乎不動。
    換方法只要 <span class="kbd">ValueDrift(column="f3", method="psi")</span>——但實測它算出 0.973，
    我們自己算是 0.558（<b>分箱策略不同</b>）：<b>門檻永遠綁在某一個實作上</b>，換工具就要重新校準。
  </p>
  <p>
    那份 HTML 報告實測 <b>4.3 MB</b>（互動圖表全部內嵌，所以打開不用網路）——這個大小塞進 notebook 會讓頁面明顯變重，
    所以 notebook 裡是<b>存成檔案、用瀏覽器開</b>。
  </p>
  <a class="golab" href="__NB__" target="_blank" rel="noopener">到 notebook 的 4️⃣ 節：Evidently 報告、對照組誤判、換方法</a>
</section>

<section id="s5">
  <span class="eyebrow">05 · 決策</span>
  <h2>監控的產出不是數字，是一個動作</h2>
  <div class="codeblock">def decide(max_psi, streak, watch=0.10, alarm=0.25, need=3):
    if max_psi >= alarm and streak >= need:
        return "retrain"     # 開工單 → 人確認 → 觸發重訓管線
    if max_psi >= watch:
        return "watch"       # 記錄下來、盯著，先不動模型
    return "ok"</div>
  <p>三個零件缺一不可：</p>
  <ol class="parts">
    <li><b>分數門檻</b>兩級（watch / alarm），而且要用自己的對照組校準過</li>
    <li><b>連續 N 次</b>——單一視窗超標很可能只是雜訊</li>
    <li><b>人工確認</b>——<span class="kbd">retrain</span> 是開工單，不是自動開始重訓</li>
  </ol>
  <p>
    第三點最常被跳過。重訓要算力、要驗證、要重走一次上線流程；而且<b>有些漂移的正確處理方式根本不是重訓</b>——
    是去修上游那個把公分改成公尺的服務。
  </p>
  <h3 class="sub">跑 8 個星期看看</h3>
  <table class="cmp">
    <tr><th>週</th><th>最大 PSI</th><th>最吵的欄</th><th>連續超標</th><th>決策</th></tr>
    <tr><td>1</td><td>0.108</td><td><span class="kbd">f4</span></td><td>0</td><td>watch</td></tr>
    <tr><td>2</td><td>0.130</td><td><span class="kbd">f4</span></td><td>0</td><td>watch</td></tr>
    <tr><td>3</td><td>0.086</td><td><span class="kbd">f4</span></td><td>0</td><td>ok</td></tr>
    <tr><td>4–5</td><td>0.156 / 0.150</td><td><span class="kbd">f4</span> / <span class="kbd">f3</span></td><td>0</td><td>watch</td></tr>
    <tr><td>6</td><td>0.352</td><td><span class="kbd">f3</span></td><td>1</td><td>watch</td></tr>
    <tr><td>7</td><td>0.431</td><td><span class="kbd">f3</span></td><td>2</td><td>watch</td></tr>
    <tr><td>8</td><td><b>0.526</b></td><td><span class="kbd">f3</span></td><td><b>3</b></td><td><b>retrain</b></td></tr>
  </table>
  <p>
    第 1 週就出現 <span class="kbd">watch</span>，但那一週<b>一點漂移都還沒注入</b>（最吵的是我們從頭到尾沒碰過的 <span class="kbd">f4</span>）——
    純粹是重抽樣的雜訊。規則若是「超過 0.1 就重訓」，第一週就白重訓一次。
    第 6 週首次越過 0.25，但要到第 8 週連續第 3 次才觸發：<b>代價是晚了兩週動手</b>。
    這就是監控的核心取捨——<b>靈敏度 vs 誤報率，沒有免費的午餐</b>。
    你能做的是把它寫成明確的參數（<span class="kbd">alarm</span>、<span class="kbd">need</span>、視窗大小），而不是留在某個人的直覺裡。
  </p>
  <a class="golab" href="__NB__" target="_blank" rel="noopener">到 notebook 的 5️⃣ 節：decide()、8 週模擬、決策曲線</a>
</section>

<section id="s6">
  <span class="eyebrow">06 · 接回管線</span>
  <h2>WARN 提醒、ERROR 擋路、sensor 叫人</h2>
  <div class="codeblock">@dg.asset_check(asset=drift_report, blocking=False)
def psi_watch(drift_report) -> dg.AssetCheckResult:
    return dg.AssetCheckResult(passed=drift_report["max_psi"] < 0.10,
                               severity=dg.AssetCheckSeverity.WARN)     # 預設是 ERROR，要 WARN 得明寫

@dg.asset_check(asset=drift_report, blocking=True)
def psi_alarm(drift_report) -> dg.AssetCheckResult:
    return dg.AssetCheckResult(passed=drift_report["max_psi"] < 0.25,
                               severity=dg.AssetCheckSeverity.ERROR)    # ERROR ＋ blocking＝擋死下游</div>
  <p>
    監控寫成 notebook 只是分析，寫進管線才是維運。用第 3、4 課的 Dagster，監控就是
    <span class="kbd">production_batch → drift_report → scored_output</span> 三個資產，加上掛在中間那個資產上的<b>兩個檢查</b>。
    兩個檢查對應監控的兩種語氣：
  </p>
  <table class="cmp">
    <tr><th></th><th><span class="kbd">psi_watch</span></th><th><span class="kbd">psi_alarm</span></th></tr>
    <tr><td>severity / blocking</td><td>WARN / False</td><td>ERROR / True</td></tr>
    <tr><td>沒過的時候</td><td>run 仍然成功，帳本留一筆黃色紀錄</td><td>run <b>失敗</b>、下游<b>不執行</b></td></tr>
    <tr><td>用來表達</td><td>「有點怪，之後查」</td><td>「這批分數不能用」</td></tr>
  </table>
  <p>
    實測兩次執行：乾淨資料 → run 成功、三個資產全出（max_psi 0.082）；漂移資料 → run 失敗、
    <b><span class="kbd">scored_output</span> 沒有產出</b>（max_psi 0.558）。這正是你要的行為：
    <b>輸入已經不可信時，寧可今天沒有分數，也不要一批錯的分數流進業務系統</b>。錯誤原文是
    <span class="kbd">DagsterAssetCheckFailedError: 1 blocking asset check failed with ERROR severity: drift_report: psi_alarm</span>。
  </p>
  <div class="codeblock">@dg.sensor(target=MONITORING, minimum_interval_seconds=3600)
def retrain_sensor(context):
    event = context.instance.get_latest_materialization_event(dg.AssetKey("drift_report"))
    max_psi = float(event.asset_materialization.metadata["max_psi"].value)
    streak = int(context.cursor or 0) + 1 if max_psi >= 0.25 else 0
    context.update_cursor(str(streak))                       # 「連續 N 次」就存在 cursor 裡
    if streak >= 3:
        return dg.RunRequest(run_key=..., tags={"max_psi": str(max_psi)})
    return dg.SkipReason(f"max_psi={max_psi}，連續超標 {streak}/3——先不重訓")</div>
  <p>
    資產檢查會擋、會叫人，但不會<b>觸發重訓</b>——那是 sensor 的工作。notebook 裡用
    <span class="kbd">evaluate_tick</span> 直接跑五次 tick（不用起 daemon），漂移一次比一次嚴重，
    到第 5 次才送出帶著 <span class="kbd">max_psi</span> 標籤的 <span class="kbd">RunRequest</span>。
    把它的目標換成第 5 課那條訓練管線，就是完整閉環：
    <b>監控發現漂移 → 送出重訓請求 → 訓練 → 評估 → 品質閘 → 通過才移動 @champion</b>。
    品質閘還在——<b>重訓出來的模型一樣要通過檢查</b>，否則你只是把「模型變差」自動化了。
  </p>
  <p>
    監控結果也要留下來：每個視窗的分數用 <span class="kbd">mlflow.log_metric("max_psi", v, step=週)</span> 記成一條時間序列，
    <span class="kbd">client.get_metric_history()</span> 讀回來就能問「最近 3 個視窗是不是都超標」——
    <span class="kbd">decide()</span> 要的 <span class="kbd">streak</span> 不必自己另外存一份狀態。
  </p>
  <a class="golab" href="__NB__" target="_blank" rel="noopener">到 notebook 的 6️⃣ 節：兩個檢查、五次 sensor tick、MLflow 漂移曲線</a>
</section>

<section id="s7">
  <span class="eyebrow">07 · 線上服務</span>
  <h2>API 上線之後，儀表板上要有哪四類數字</h2>
  <table class="cmp">
    <tr><th>記什麼</th><th>為什麼</th><th>出事時的樣子</th></tr>
    <tr><td><b>延遲</b> p50 / p95 / p99</td><td>平均值會騙人</td><td>平均 7 ms 很漂亮，p99 是 3 秒</td></tr>
    <tr><td><b>錯誤率</b>（依狀態碼）</td><td>400 跟 500 是不同故障</td><td>400 暴增＝上游格式變了；500 暴增＝服務壞了</td></tr>
    <tr><td><b>輸入摘要</b>（每欄筆數／平均／缺值率）</td><td>原始輸入不能全存</td><td>存摘要就夠算 PSI，而且不必留客戶原始資料</td></tr>
    <tr><td><b>預測摘要</b>（平均機率、判正率）</td><td>最省事的早期警報</td><td>判正率 52% → 44%，不用等標籤就知道有事</td></tr>
  </table>
  <p>
    前兩類是<b>軟體維運</b>，任何 API 都要有；後兩類是<b>機器學習特有</b>的——模型不會拋例外，它只會安靜地越答越爛。
    重點是後兩類要<b>每個視窗存一列</b>：監控要的不是原始請求，是<b>可以跟參考視窗比較的摘要</b>。
    一天一列、每列幾十個數字，存一年也只是幾百 KB。
  </p>
  <p>
    notebook 不起伺服器，直接量模型本身的延遲（這是 API 延遲的下限，真正的 API 還要加上 HTTP 與 schema 驗證）：
    單筆請求實測 <b>p50 約 7 ms、p99 約 7–12 ms</b>；同樣 500 列改成批次一次算完，<b>每列只要 0.02–0.03 ms</b>——
    差了兩百倍以上。這個比例就是上一課「批次評分 vs 線上 API」那個取捨的來源：
    <b>線上 API 買的是即時性，代價是每列成本高得多</b>（你的機器數字會不同，看的是量級）。
  </p>
  <a class="golab" href="__NB__" target="_blank" rel="noopener">到 notebook 的 7️⃣ 節：量延遲、組出一列監控紀錄</a>
</section>

<section id="s8">
  <span class="eyebrow">08 · 實戰</span>
  <h2>換你動手</h2>
  <div class="ex">
    <span class="lv">LEVEL 1</span>
    <p>換一欄注入漂移：把 <span class="kbd">f7</span> 乘 0.4（把變異壓扁），重算整張漂移表。<span class="kbd">f7</span> 會被指出來嗎？accuracy 掉多少？跟動 <span class="kbd">f0</span>／<span class="kbd">f3</span> 比，哪一欄比較「重要」？</p>
  </div>
  <div class="ex">
    <span class="lv">LEVEL 2</span>
    <p>把「連續 3 次」換成「最近 4 個視窗裡有 3 次超標」（k-of-n），用 8 週模擬比較兩種規則各在第幾週觸發。在 0.25 門檻下結果一樣，把門檻降到 0.1 再比一次——差別就出來了。</p>
  </div>
  <div class="ex">
    <span class="lv">LEVEL 3</span>
    <p>換掉 Evidently 的預設：用 <span class="kbd">ValueDrift(method="psi")</span> 自組一份 12 欄報告、門檻用你從對照組校準出來的數字；或加一個 <span class="kbd">ClassificationPreset()</span> 產生「有標籤之後」的品質報告。</p>
  </div>
  <p style="font-size:13.5px;color:var(--ink-soft);margin-top:10px">卡住了？每一題在 notebook 末節都有折疊解答——先自己做，再打開對照。</p>
</section>

<section id="quiz">
  <span class="eyebrow">09 · 驗收</span>
  <h2>情境測驗</h2>
  <p>離開前試試看：下面的情境都真的會遇到。每題選一個你認為的最佳做法，選了馬上看得到解釋。</p>
  <div data-quiz>

    <div class="quiz-q" data-answer="C">
      <p class="quiz-tag">Q1 <span class="qtype">情境題</span></p>
      <h3>模型上線第一週，你用 Evidently 預設設定跑漂移報告，結果說 12 欄裡有 3 欄漂移。第一件該做的事是？</h3>
      <div class="quiz-opts">
        <button type="button" class="quiz-opt" data-k="A">A. 3 欄漂移已經是四分之一，立刻排重訓</button>
        <button type="button" class="quiz-opt" data-k="B">B. 把門檻從 0.1 調到 0.5，讓警報安靜下來再說</button>
        <button type="button" class="quiz-opt" data-k="C">C. 先拿一段「已知正常」的資料（例如訓練集 vs 沒動過的測試集）跑同一份報告當對照組，看雜訊底線在哪，再決定門檻</button>
        <button type="button" class="quiz-opt" data-k="D">D. 改用 KS 檢定，p &lt; 0.05 才算漂移，比較嚴謹</button>
      </div>
      <div class="quiz-fb" aria-live="polite"><p>本課實測：一份<b>完全沒有漂移</b>的資料（訓練集 vs 沒動過的測試集），用 Evidently 預設值照樣被判 3/12 欄漂移（f0 0.114、f2 0.111、f3 0.105）——跟真的漂移時「欄數」一模一樣，差別只在分數量級（真漂移是 0.813／0.695）。所以看到「3 欄漂移」的第一件事永遠是建立對照組、校準門檻。A 是拿一個沒有校準過的警報去花真金白銀；B 方向對但做法反了——調門檻要有依據，隨手調高只是把眼睛蒙起來；D 更糟，KS 在大樣本下更敏感，實測對照組裡就有兩欄 p &lt; 0.05。</p></div>
    </div>

    <div class="quiz-q" data-answer="B">
      <p class="quiz-tag">Q2 <span class="qtype dx">錯誤診斷</span></p>
      <h3>同事的監控報告每天都說「12 欄全部漂移」，而且每一欄的分數都一模一樣。程式沒有拋任何錯誤。最可能的原因是？</h3>
      <div class="codeblock">DriftedColumnsCount(drift_share=0.5) -> {'count': 12.0, 'share': 1.0}
ValueDrift(column=f0,method=Jensen-Shannon distance,threshold=0.1) -> 0.8325546111576977
ValueDrift(column=f1,method=Jensen-Shannon distance,threshold=0.1) -> 0.8325546111576977</div>
      <div class="quiz-opts">
        <button type="button" class="quiz-opt" data-k="A">A. 參考資料與當前資料的筆數差太多，要先抽樣成一樣多</button>
        <button type="button" class="quiz-opt" data-k="B">B. <code>DataDefinition</code> 把數值欄宣告成 <code>categorical_columns</code>——每個浮點數被當成一個獨立類別，方法自動換成 Jensen-Shannon</button>
        <button type="button" class="quiz-opt" data-k="C">C. <code>run()</code> 的參考與當前寫反了</button>
        <button type="button" class="quiz-opt" data-k="D">D. 資料真的全面漂移了，上游整批換掉了</button>
      </div>
      <div class="quiz-fb" aria-live="polite"><p>證據就在方法名稱上：預設的數值欄方法是 <code>Wasserstein distance (normed)</code>，這裡卻是 <code>Jensen-Shannon distance</code>——那是類別欄的方法。把連續數值宣告成類別後，每個浮點數都是獨一無二的「類別」，兩份資料的類別集合幾乎不重疊，於是每一欄都得到同一個接近上限的分數（實測 0.8326）。<b>型別宣告錯不會報錯，只會讓報告很有自信地騙你。</b>A 不會產生一模一樣的分數；C 就本課實測而言 PSI／Wasserstein 是對稱的，寫反不會有這種結果（但自己用參考分位數分箱的 PSI 會變：0.558 → 0.837，所以寫反仍然是壞習慣）；D 的話分數不會每欄都相同到小數點後十位。</p></div>
    </div>

    <div class="quiz-q" data-answer="D">
      <p class="quiz-tag">Q3 <span class="qtype">情境題</span></p>
      <h3>客戶是不是真的流失，要 4 週後才會知道。老闆今天問「模型還能用嗎」。你手上有什麼、該怎麼回答？</h3>
      <div class="quiz-opts">
        <button type="button" class="quiz-opt" data-k="A">A. 老實說要等 4 週，在那之前沒有任何客觀根據</button>
        <button type="button" class="quiz-opt" data-k="B">B. 拿訓練集的預測當參考分佈，算預測漂移 PSI</button>
        <button type="button" class="quiz-opt" data-k="C">C. 看 API 的錯誤率與 p99 延遲，都正常就代表模型正常</button>
        <button type="button" class="quiz-opt" data-k="D">D. 同時看輸入端的逐欄 PSI 與輸出端的預測漂移（平均機率、判正率、預測 PSI），兩邊一致亮燈才算證據</button>
      </div>
      <div class="quiz-fb" aria-live="polite"><p>沒有標籤的期間，你有兩類即時訊號：輸入分佈與輸出分佈。本課實測兩者方向一致（最大 PSI 0.558、預測 PSI 0.166、判正率 0.520 → 0.444），而事後才拿得到的 accuracy 確實從 0.916 掉到 0.864——症狀猜對了病因。A 放棄了兩個免費且即時的訊號；B 是本課特別點名的陷阱，模型看過訓練集、機率過度自信，實測會算出 0.183 的假漂移；C 混淆了兩種故障模式，模型變爛時 API 照樣 200、延遲照樣漂亮——那正是它危險的地方。</p></div>
    </div>

    <div class="quiz-q" data-answer="B">
      <p class="quiz-tag">Q4 <span class="qtype dx">錯誤診斷</span></p>
      <h3>自己寫的 PSI 函式平常都正常，某天某一欄回傳 <span class="kbd">inf</span>，同時噴出這行警告。怎麼修最對？</h3>
      <div class="codeblock">RuntimeWarning: divide by zero encountered in log
  return float(np.sum((c - r) * np.log(c / r)))
psi(X_train["f0"], window["f0"]) -> inf</div>
      <div class="quiz-opts">
        <button type="button" class="quiz-opt" data-k="A">A. 當前視窗有缺值，先 <code>dropna()</code> 再算</button>
        <button type="button" class="quiz-opt" data-k="B">B. 當前視窗在某些箱子裡一筆都沒有，比例是 0 → <code>log(0)</code>；兩邊比例各加一個極小值（<code>1e-6</code>），並確認分箱兩端是開放的</button>
        <button type="button" class="quiz-opt" data-k="C">C. 分箱數 10 太少，改成 50 個箱子就不會有空箱</button>
        <button type="button" class="quiz-opt" data-k="D">D. <code>inf</code> 是正確答案，代表漂移無限大，直接當成最高等級警報即可</button>
      </div>
      <div class="quiz-fb" aria-live="polite"><p><code>divide by zero encountered in log</code> 指的就是 <code>c/r</code> 裡有 0：整欄被推得離參考分佈很遠時，靠近參考低端的那幾個箱子在當前視窗一筆都沒有。實測同一份資料（<code>f0</code> 平移 8），不加極小值得到 <code>inf</code>、加了 <code>1e-6</code> 得到 12.434——一個沒法比較大小、一個可以排序與畫趨勢。A 症狀不符，缺值會讓 <code>np.histogram</code> 少算而不是產生 0 比例的 log；C 方向完全相反，箱子越多每箱越稀疏、空箱只會更多；D 很危險——<code>inf</code> 一旦進了平均、趨勢圖或門檻比較就會污染整條監控管線，而且它掩蓋了「到底漂多遠」這個你真正需要的資訊。</p></div>
    </div>

    <div class="quiz-q" data-answer="A">
      <p class="quiz-tag">Q5 <span class="qtype">情境題</span></p>
      <h3>監控連續三週警報 → 重訓 → 新模型通過品質閘 → <span class="kbd">@champion</span> 已移到新版本。接下來最該做、卻最常被忘記的一件事是？</h3>
      <div class="quiz-opts">
        <button type="button" class="quiz-opt" data-k="A">A. 把監控的<b>參考視窗</b>換成新模型的訓練資料，並重新校準門檻</button>
        <button type="button" class="quiz-opt" data-k="B">B. 把警報門檻調高，免得剛上線就一直叫</button>
        <button type="button" class="quiz-opt" data-k="C">C. 刪掉舊的模型版本，Registry 才不會越積越多</button>
        <button type="button" class="quiz-opt" data-k="D">D. 把 <code>psi_alarm</code> 改成 <code>blocking=False</code>，避免新模型上線期間擋住下游</button>
      </div>
      <div class="quiz-fb" aria-live="polite"><p>參考視窗代表「模型認識的世界」。模型換了，那個世界也換了——不更新參考視窗，新模型上線第一天就會對你發出「嚴重漂移」的警報，因為它本來就是照著漂移後的資料訓練的。這種每次重訓後都會出現的假警報，是團隊開始無視監控的頭號原因。B 是用調高門檻掩蓋設定錯誤，真的漂移來的時候你也看不到了；C 把回滾的退路砍了——舊版本留著，alias 一行就能指回去；D 等於在最需要把關的時候拆掉煞車，而且下游拿到的會是用未經驗證的新模型算出來的分數。</p></div>
    </div>

    <div class="quiz-score" data-score></div>
  </div>
</section>

<div class="endnav">
  <a href="/optuna-hpo/">
    <span class="tag">下一課</span>
    <b>Optuna 自動調參：讓超參數搜尋自己跑，每個 trial 都留在 MLflow →</b>
  </a>
  <a href="/mlops/">
    <span class="tag">主題</span>
    <b>‹ 回「MLOps 自動化技術」課程列表</b>
  </a>
</div>
"""

SCRIPT = r"""
/* ═══ hero 互動：漂移儀表板（全部數字來自 notebook 實測的查表）═══ */
(function () {
  const FEATS = ["f0","f1","f2","f3","f4","f5","f6","f7","f8","f9","f10","f11"];
  const BASE = {"f0": 0.025, "f1": 0.017, "f2": 0.025, "f3": 0.023, "f4": 0.082, "f5": 0.031, "f6": 0.017, "f7": 0.059, "f8": 0.022, "f9": 0.022, "f10": 0.023, "f11": 0.037};
  const PSI_F0 = {"0.0": 0.025, "0.25": 0.011, "0.5": 0.029, "0.75": 0.097, "1.0": 0.186, "1.25": 0.327, "1.5": 0.487, "1.75": 0.656, "2.0": 1.037};
  const PSI_F3 = {"1.0": 0.023, "1.25": 0.097, "1.5": 0.246, "1.75": 0.407, "2.0": 0.558, "2.25": 0.713, "2.5": 0.932, "2.75": 1.099, "3.0": 1.207};
  /* key "平移|放大" → [預測漂移 PSI, 判正率, accuracy]（notebook 實測，81 組全部真算過）*/
  const GRID = {"0.0|1.0":[0.0,0.52,0.916],"0.0|1.25":[0.024,0.506,0.918],"0.0|1.5":[0.038,0.464,0.884],"0.0|1.75":[0.064,0.436,0.864],"0.0|2.0":[0.099,0.43,0.854],"0.0|2.25":[0.141,0.408,0.832],"0.0|2.5":[0.173,0.388,0.812],"0.0|2.75":[0.197,0.37,0.798],"0.0|3.0":[0.223,0.368,0.796],"0.25|1.0":[0.004,0.524,0.92],"0.25|1.25":[0.023,0.51,0.918],"0.25|1.5":[0.036,0.464,0.884],"0.25|1.75":[0.06,0.442,0.866],"0.25|2.0":[0.081,0.432,0.852],"0.25|2.25":[0.118,0.408,0.828],"0.25|2.5":[0.17,0.392,0.812],"0.25|2.75":[0.191,0.372,0.796],"0.25|3.0":[0.208,0.37,0.794],"0.5|1.0":[0.002,0.526,0.922],"0.5|1.25":[0.017,0.518,0.926],"0.5|1.5":[0.035,0.472,0.884],"0.5|1.75":[0.065,0.444,0.864],"0.5|2.0":[0.091,0.432,0.852],"0.5|2.25":[0.118,0.41,0.83],"0.5|2.5":[0.178,0.388,0.808],"0.5|2.75":[0.191,0.368,0.792],"0.5|3.0":[0.223,0.366,0.79],"0.75|1.0":[0.004,0.524,0.92],"0.75|1.25":[0.023,0.514,0.922],"0.75|1.5":[0.043,0.466,0.882],"0.75|1.75":[0.076,0.446,0.862],"0.75|2.0":[0.098,0.434,0.85],"0.75|2.25":[0.131,0.412,0.828],"0.75|2.5":[0.184,0.39,0.806],"0.75|2.75":[0.198,0.372,0.792],"0.75|3.0":[0.236,0.37,0.79],"1.0|1.0":[0.014,0.534,0.922],"1.0|1.25":[0.039,0.526,0.918],"1.0|1.5":[0.07,0.472,0.888],"1.0|1.75":[0.092,0.454,0.87],"1.0|2.0":[0.116,0.442,0.858],"1.0|2.25":[0.16,0.42,0.836],"1.0|2.5":[0.206,0.396,0.812],"1.0|2.75":[0.235,0.376,0.796],"1.0|3.0":[0.269,0.372,0.796],"1.25|1.0":[0.021,0.536,0.924],"1.25|1.25":[0.059,0.518,0.91],"1.25|1.5":[0.093,0.482,0.894],"1.25|1.75":[0.108,0.458,0.874],"1.25|2.0":[0.138,0.444,0.86],"1.25|2.25":[0.19,0.42,0.84],"1.25|2.5":[0.268,0.396,0.816],"1.25|2.75":[0.304,0.384,0.804],"1.25|3.0":[0.335,0.382,0.802],"1.5|1.0":[0.036,0.536,0.924],"1.5|1.25":[0.078,0.52,0.912],"1.5|1.5":[0.113,0.484,0.892],"1.5|1.75":[0.123,0.458,0.87],"1.5|2.0":[0.166,0.444,0.864],"1.5|2.25":[0.21,0.422,0.842],"1.5|2.5":[0.278,0.396,0.816],"1.5|2.75":[0.319,0.384,0.804],"1.5|3.0":[0.351,0.382,0.802],"1.75|1.0":[0.06,0.538,0.922],"1.75|1.25":[0.112,0.52,0.916],"1.75|1.5":[0.145,0.484,0.892],"1.75|1.75":[0.156,0.46,0.872],"1.75|2.0":[0.2,0.448,0.864],"1.75|2.25":[0.236,0.426,0.846],"1.75|2.5":[0.343,0.406,0.826],"1.75|2.75":[0.375,0.384,0.804],"1.75|3.0":[0.409,0.38,0.804],"2.0|1.0":[0.128,0.544,0.916],"2.0|1.25":[0.182,0.524,0.908],"2.0|1.5":[0.215,0.488,0.888],"2.0|1.75":[0.25,0.464,0.872],"2.0|2.0":[0.285,0.454,0.862],"2.0|2.25":[0.354,0.434,0.846],"2.0|2.5":[0.464,0.406,0.818],"2.0|2.75":[0.483,0.388,0.8],"2.0|3.0":[0.546,0.386,0.798]};
  const WATCH = 0.10, ALARM = 0.25, MAXBAR = 1.25;
  const REF_POS = 0.520, REF_ACC = 0.916;

  const shift = document.getElementById("dm-shift");
  const scale = document.getElementById("dm-scale");
  const shiftV = document.getElementById("dm-shift-v");
  const scaleV = document.getElementById("dm-scale-v");
  const bars = document.getElementById("dm-bars");
  const names = document.getElementById("dm-names");
  const out = document.getElementById("dm-out");
  const verdict = document.getElementById("dm-verdict");

  names.innerHTML = FEATS.map((f) => `<div>${f}</div>`).join("");

  /* 查表的 key 跟 Python 的 str(float) 一致：整數要有 .0（0 → "0.0"），其餘照原樣 */
  const kf = (v) => (v % 1 === 0 ? v.toFixed(1) : String(v));
  function key(s, k) { return `${kf(s)}|${kf(k)}`; }

  function render() {
    const s = +shift.value, k = +scale.value;
    shiftV.textContent = s.toFixed(2);
    scaleV.textContent = k.toFixed(2);
    const psi = Object.assign({}, BASE);
    psi.f0 = PSI_F0[kf(s)];
    psi.f3 = PSI_F3[kf(k)];
    const g = GRID[key(s, k)] || [0, REF_POS, REF_ACC];
    const over = FEATS.filter((f) => psi[f] >= WATCH);
    const maxPsi = Math.max.apply(null, FEATS.map((f) => psi[f]));

    bars.innerHTML =
      FEATS.map((f) => {
        const v = psi[f];
        const h = Math.max(2, Math.min(1, v / MAXBAR) * 112);
        const cls = v >= ALARM ? "bar alarm" : v >= WATCH ? "bar over" : "bar";
        return `<div class="${cls}" style="height:${h}px" title="${f} PSI ${v.toFixed(3)}"></div>`;
      }).join("") +
      `<div class="thr" style="bottom:${(WATCH / MAXBAR) * 112}px"><span>watch 0.10</span></div>` +
      `<div class="thr a" style="bottom:${(ALARM / MAXBAR) * 112}px"><span>alarm 0.25</span></div>`;

    out.innerHTML = [
      ["最大 PSI", maxPsi.toFixed(3), "沒漂移時 0.082"],
      ["被判漂移的欄", `${over.length} / 12`, over.length ? over.join(" ") : "—"],
      ["預測漂移 PSI", g[0].toFixed(3), "沒漂移時 0"],
      ["判正率", g[1].toFixed(3), `參考 ${REF_POS.toFixed(3)}`],
      ["accuracy（要等標籤）", g[2].toFixed(3), `參考 ${REF_ACC.toFixed(3)}`],
    ].map(([kk, v, sub]) => `<div class="cell"><div class="k">${kk}</div><div class="v">${v}</div><div class="s">${sub}</div></div>`).join("");

    let cls = "verdict", txt;
    if (maxPsi >= ALARM) { cls += " retrain"; txt = `🔴 retrain — 最大 PSI ${maxPsi.toFixed(3)} 超過警報線，連續 3 個視窗都這樣就開重訓工單`; }
    else if (maxPsi >= WATCH) { cls += " watch"; txt = `🟡 watch — 有東西在動，記錄下來盯著，先不動模型`; }
    else { txt = `🟢 ok — 分佈穩定，什麼都不用做`; }
    verdict.className = cls;
    verdict.textContent = txt;
  }

  shift.addEventListener("input", render);
  scale.addEventListener("input", render);
  document.getElementById("dm-reset").addEventListener("click", () => { shift.value = 0; scale.value = 1; render(); });
  document.getElementById("dm-bad").addEventListener("click", () => { shift.value = 1.5; scale.value = 2; render(); });
  render();
})();
"""

PANEL_STEPS = """
        <li>登入 molab（GitHub / Google）</li>
        <li>開啟課程 notebook，<b>Fork 成自己的副本</b>即可編輯</li>
        <li>從第一格往下全部執行（首次安裝套件約 1–2 分鐘）——<b>免費 CPU 環境即可</b>，不需要 GPU；整份跑完約 1–2 分鐘</li>
"""
