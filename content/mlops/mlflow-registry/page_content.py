"""課程頁內容區（純常數）。改完跑：python3 .claude/skills/make-lesson/scripts/page-fill.py content/mlops/mlflow-registry
build.sh 不會部署這個檔；它是 index.html 內容區的正本。"""

TITLE = "MLflow Models 與 Model Registry：從最好的 run 到線上那一版"
DESCRIPTION = "MLflow Models 與 Model Registry 詳解：log_model 打包了什麼、signature 怎麼擋錯輸入、註冊／版本／alias 一行晉升回滾、mlflow.models.evaluate 一行產 8 指標 5 張圖、自訂 pyfunc 打包前後處理、log_input 記資料指紋——molab 免費環境全程實作。"
NB = "https://molab.marimo.io/github/skmygo/agentclass/blob/main/content/mlops/mlflow-registry/mlflow-registry_ext.py"

STYLE = r"""
  /* 語義色：藍＝v1、橘＝v2、綠＝alias／線上、紅＝被擋下的輸入 */
  :root { --c1: #4C72B0; --c2: #DD8452; --c3: #55A868; --cut: #C44E52; }
  a.golab { text-decoration: none; display: inline-flex; align-items: center; gap: 8px; }

  /* hero：registry 與 alias 切換 */
  #rg-demo .reg { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 12px; }
  #rg-demo .ver { border: 2px solid var(--grid); border-radius: 12px; padding: 10px 12px; font-size: 13px; position: relative; transition: border-color .2s, box-shadow .2s; }
  #rg-demo .ver b { font-family: var(--mono); font-size: 14px; display: block; }
  #rg-demo .ver.v1 b { color: var(--c1); } #rg-demo .ver.v2 b { color: var(--c2); }
  #rg-demo .ver.live { border-color: var(--c3); box-shadow: 0 0 0 3px rgba(85,168,104,.18); }
  #rg-demo .alias { position: absolute; top: -11px; right: 10px; background: var(--c3); color: #fff; font-family: var(--mono); font-size: 11.5px; padding: 2px 8px; border-radius: 999px; display: none; }
  #rg-demo .ver.live .alias { display: inline-block; }
  #rg-demo .metrics { color: var(--ink-soft); font-size: 12.5px; margin-top: 4px; font-family: var(--mono); }
  #rg-demo .ctl { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; margin-bottom: 10px; }
  #rg-demo .ctl button { font-family: var(--mono); font-size: 12.5px; padding: 6px 12px; border-radius: 8px; border: 1.5px solid var(--ink); background: #fff; color: var(--ink); cursor: pointer; }
  #rg-demo .ctl button:hover { background: var(--chip-bg); }
  #rg-demo .ctl label { font-size: 12.5px; font-weight: 800; display: inline-flex; align-items: center; gap: 6px; }
  #rg-demo .ctl input[type=range] { width: 120px; accent-color: var(--ink); }
  #rg-demo .svc { background: var(--chip-bg); border-radius: 10px; padding: 10px 12px; font-family: var(--mono); font-size: 12.5px; margin-bottom: 8px; line-height: 1.6; }
  #rg-demo .svc .hl { color: var(--c3); font-weight: 800; }
  #rg-demo table { width: 100%; border-collapse: collapse; font-size: 13px; font-family: var(--mono); }
  #rg-demo th, #rg-demo td { padding: 5px 8px; border-bottom: 1px solid var(--grid); text-align: left; }
  #rg-demo th { font-size: 11.5px; color: var(--ink-soft); font-family: var(--sans); letter-spacing: .04em; }
  #rg-demo td.hit { color: var(--c3); font-weight: 800; } #rg-demo td.miss { color: var(--cut); font-weight: 800; }
  #rg-demo .tbl { overflow-x: auto; }
  @media (max-width: 560px) { #rg-demo .reg { grid-template-columns: 1fr; } }

  table.cmp { width: 100%; border-collapse: collapse; font-size: 13.5px; margin: 14px 0; }
  table.cmp th, table.cmp td { border-bottom: 1px solid var(--grid); padding: 8px 10px; text-align: left; vertical-align: top; }
  table.cmp th { font-size: 12px; letter-spacing: .04em; color: var(--ink-soft); }
  .kbd { font-family: var(--mono); background: var(--chip-bg); padding: 1px 6px; border-radius: 5px; font-size: 13px; }
"""

WRAP = r"""
<section id="hero">
  <span class="eyebrow">MLFLOW · MODELS &amp; REGISTRY · 02</span>
  <h1>MLflow Models 與 Model Registry：<br>從最好的 run 到線上那一版</h1>
  <p style="margin-top:18px">
    上一課找到了最好的 run。但「最好的 run」離「線上那一版」還差三件事：模型要能被<b>別人</b>載入、要有大家都認得的<b>名字與版本</b>、
    上線那一版要能<b>一行切換</b>。先玩最後這件：服務程式永遠載 <span class="kbd">models:/churn-clf@champion</span>，
    按晉升或回滾，看它拿到的模型與預測怎麼變——
  </p>

  <div class="hero-demo" id="rg-demo">
    <div class="reg">
      <div class="ver v1" id="rg-v1"><span class="alias">@champion</span><b>churn-clf · version 1</b>LogisticRegression<div class="metrics">roc_auc 0.951 · recall 0.860 · f1 0.885</div></div>
      <div class="ver v2" id="rg-v2"><span class="alias">@champion</span><b>churn-clf · version 2</b>RandomForest（depth 8）<div class="metrics">roc_auc 0.968 · recall 0.913 · f1 0.920</div></div>
    </div>
    <div class="ctl">
      <button type="button" id="rg-promote">晉升：champion → v2</button>
      <button type="button" id="rg-rollback">回滾：champion → v1</button>
      <label>門檻 <input type="range" id="rg-thr" min="0.1" max="0.9" step="0.05" value="0.5"><span id="rg-thr-v">0.50</span></label>
    </div>
    <div class="svc" id="rg-svc"></div>
    <div class="tbl"><table id="rg-tbl"></table></div>
  </div>

  <p class="note">
    機率與指標都是 notebook 的實測數字（同一組亂數種子）。notebook 裡的 alias 是真的 Registry：
    <span class="kbd">set_registered_model_alias</span> 一行，服務端的載入程式一個字不改。
  </p>
</section>

<section id="s1">
  <span class="eyebrow">01 · MLFLOW MODEL</span>
  <h2>模型＋規格＋環境，一個資料夾</h2>
  <div class="codeblock">from mlflow.models import infer_signature

signature = infer_signature(X_train, model.predict_proba(X_train)[:, 1])   # 輸入 12 欄 double → 輸出 double
with mlflow.start_run(run_name="v1-logreg"):
    info = mlflow.sklearn.log_model(model, name="churn_model",
                                    signature=signature, input_example=X_train.head(3))
info.model_uri          # models:/m-4052…   （MLflow 3 的 LoggedModel，有自己的 id）
info.flavors            # ['python_function', 'sklearn']</div>
  <p>
    <span class="kbd">log_model</span> 不是存 pickle，而是產生一個資料夾：<span class="kbd">MLmodel</span> 說明書（YAML：有哪些 flavor、signature、Python 與套件版本）、
    模型本體（<span class="kbd">model.skops</span>）、<span class="kbd">requirements.txt</span>／<span class="kbd">python_env.yaml</span>／<span class="kbd">conda.yaml</span> 重建環境用、
    <span class="kbd">input_example.json</span> 一筆範例輸入——實測資料夾裡共 8 個檔案，notebook 會把 <span class="kbd">MLmodel</span> 印給你看。
  </p>
  <p>
    <b>flavor</b> 是「可以用哪些方式載入」：<span class="kbd">sklearn</span> flavor 載回原生物件（有 <span class="kbd">feature_importances_</span>、<span class="kbd">predict_proba</span>）；
    <span class="kbd">python_function</span>（pyfunc）是<b>統一介面</b>——不管底層是 sklearn、PyTorch、XGBoost，都是 <span class="kbd">load_model(uri).predict(df)</span>。
    部署工具只認 pyfunc，所以每個 flavor 都附帶它。
  </p>
  <a class="golab" href="__NB__" target="_blank" rel="noopener">到 notebook 的 1️⃣ 節：log_model、資料夾內容、MLmodel 說明書</a>
</section>

<section id="s2">
  <span class="eyebrow">02 · SIGNATURE</span>
  <h2>合約：載回來推論，餵錯資料會怎樣</h2>
  <div class="codeblock">pyfunc = mlflow.pyfunc.load_model(info.model_uri)
pyfunc.predict(X_test.head(3))                        # [1 0 1]
pyfunc.predict(X_test.head(3).drop(columns=["f11"]))  # ✗ Model is missing inputs ['f11'].
pyfunc.predict(X_test.head(3).assign(f1=["a","b","c"]))
# ✗ Failed to convert column f1 from type object to DataType.double.
pyfunc.predict(X_test.head(3).assign(extra=1.0))      # 多一欄：靜靜忽略</div>
  <p>
    有 signature，MLflow 在呼叫模型<b>之前</b>就把關（schema enforcement）：少一欄、型別錯都直接拒絕並說清楚是哪欄；多一欄則忽略。
    沒有 signature 的模型什麼都吃，錯誤延後到 scikit-learn 內部才爆，訊息難懂得多。
    所以 <span class="kbd">log_model</span> 一定要給 signature——它是模型與呼叫端之間的合約。
  </p>
  <a class="golab" href="__NB__" target="_blank" rel="noopener">到 notebook 的 2️⃣ 節：三種錯誤輸入的實際反應</a>
</section>

<section id="s3">
  <span class="eyebrow">03 · REGISTRY</span>
  <h2>名字、版本、alias：晉升與回滾各一行</h2>
  <div class="codeblock">mv1 = mlflow.register_model(v1_info.model_uri, "churn-clf")   # → version 1
mv2 = mlflow.register_model(v2_info.model_uri, "churn-clf")   # → version 2

client = MlflowClient()
client.set_registered_model_alias("churn-clf", "champion", mv1.version)     # 線上：v1
client.set_registered_model_alias("churn-clf", "challenger", mv2.version)   # 候選：v2

model = mlflow.pyfunc.load_model("models:/churn-clf@champion")   # 服務端永遠這一行
client.set_registered_model_alias("churn-clf", "champion", mv2.version)     # 晉升（回滾就指回 1）</div>
  <p>
    Registry 是「有名字的模型」的目錄：一個 registered model（<span class="kbd">churn-clf</span>）底下多個 version，每個 version 指向一個 LoggedModel，
    可以掛 description 與 tag（例如 <span class="kbd">validated=true</span>）。<b>alias</b> 是貼在 version 上的可移動標籤，一個 alias 同時只指一個 version；
    指到不存在的 alias 會報 <span class="kbd">Registered model alias nope not found.</span>
    舊版的 stage（Staging／Production）已 deprecated，現在用 alias，名字自己取。
  </p>
  <p>
    實測：v1 LogisticRegression AUC 0.9508、v2 RandomForest AUC 0.9684。晉升前後同一行載入程式拿到的 run id 不同、預測也換成 v2 的——
    注意 Registry 需要<b>資料庫後端</b>（sqlite 或 server）；MLflow 3.15 起純資料夾模式 <span class="kbd">./mlruns</span> 已進維護模式，預設直接報錯。
  </p>
  <a class="golab" href="__NB__" target="_blank" rel="noopener">到 notebook 的 3️⃣ 節：註冊、alias、晉升、壞 alias</a>
</section>

<section id="s4">
  <span class="eyebrow">04 · EVALUATE</span>
  <h2>晉升不憑感覺：一行評估，兩版並排</h2>
  <div class="codeblock">with mlflow.start_run(run_name="eval-v2-rf"):
    res = mlflow.models.evaluate(v2_info.model_uri, eval_df, targets="label", model_type="classifier")
res.metrics["roc_auc"]     # 0.968
res.artifacts              # roc_curve_plot, precision_recall_curve_plot, lift_curve_plot, calibration_curve_plot, confusion_matrix</div>
  <table class="cmp">
    <tr><th>metric（同一份 test）</th><th>v1 logreg</th><th>v2 rf</th></tr>
    <tr><td>accuracy</td><td>0.882</td><td>0.916</td></tr>
    <tr><td>precision / recall</td><td>0.912 / 0.860</td><td>0.927 / 0.913</td></tr>
    <tr><td>f1</td><td>0.885</td><td>0.920</td></tr>
    <tr><td>log_loss</td><td>0.288</td><td>0.270</td></tr>
    <tr><td>roc_auc / pr_auc</td><td>0.951 / 0.956</td><td>0.968 / 0.975</td></tr>
  </table>
  <p>
    指標與 5 張圖全部記進當前 run，混淆矩陣可以直接讀回來畫。第 5 課會把「roc_auc 必須高於目前 champion」變成管線裡的自動閘門。
  </p>
  <a class="golab" href="__NB__" target="_blank" rel="noopener">到 notebook 的 4️⃣ 節：evaluate 兩個版本、讀回混淆矩陣</a>
</section>

<section id="s5">
  <span class="eyebrow">05 · 自訂 PYFUNC 與資料版本</span>
  <h2>把前後處理跟模型包在一起；讓 run 記得用哪份資料</h2>
  <div class="codeblock">class ChurnWrapper(mlflow.pyfunc.PythonModel):
    def load_context(self, context):                       # 載入時讀回打包的模型檔
        self.model = pickle.load(open(context.artifacts["sk_model"], "rb"))
    def predict(self, context, model_input, params=None):  # 前處理 → 模型 → 後處理
        thr = (params or {}).get("threshold", 0.5)
        proba = self.model.predict_proba(model_input.fillna(0.0))[:, 1]
        return pd.DataFrame({"prob": proba, "churn": (proba >= thr).astype(int)})

mlflow.pyfunc.log_model(name="churn_model", python_model=ChurnWrapper(),
                        artifacts={"sk_model": "rf.pkl"}, signature=sig_with_params)
wrapper.predict(X, params={"threshold": 0.9})              # 門檻由呼叫端決定</div>
  <p>
    真實模型很少「餵 DataFrame 就出機率」：前面要清資料、後面要用門檻轉成決策。這些邏輯散在服務程式裡，換模型就對不上。
    繼承 <span class="kbd">PythonModel</span> 把它們包進同一個部署單位；signature 的 <span class="kbd">params</span> 段宣告可調參數。
    實測同樣 4 筆客戶：門檻 0.5 判流失 2 筆，<span class="kbd">threshold=0.9</span> 剩 0 筆（機率 0.746／0.071／0.843／0.174）。
  </p>
  <p>
    資料版本：<span class="kbd">mlflow.data.from_pandas(df, name=..., targets=...)</span> 自動算內容指紋（digest），
    <span class="kbd">mlflow.log_input(dataset, context="training")</span> 記進 run——兩個 run 指標不同時，先看 digest 是不是變了。
  </p>
  <a class="golab" href="__NB__" target="_blank" rel="noopener">到 notebook 的 5️⃣–7️⃣ 節：ChurnWrapper、log_input、切版本拉門檻</a>
</section>

<section id="s6">
  <span class="eyebrow">06 · 實戰</span>
  <h2>換你動手</h2>
  <div class="ex">
    <span class="lv">LEVEL 1</span>
    <p>用 <span class="kbd">mlflow.sklearn.load_model("models:/churn-clf/2")</span> 以原生 flavor 載回 v2，印出 <span class="kbd">feature_importances_</span> 最高的三個特徵——pyfunc 做不到，想想為什麼還需要它。</p>
  </div>
  <div class="ex">
    <span class="lv">LEVEL 2</span>
    <p>訓一個 GradientBoosting 當 v3 註冊，<span class="kbd">evaluate</span> 之後寫「自動晉升」：只有 roc_auc 高於目前 champion 才移 alias，否則貼 <span class="kbd">rejected=true</span>。</p>
  </div>
  <div class="ex">
    <span class="lv">LEVEL 3</span>
    <p>把 <span class="kbd">ChurnWrapper</span> 改成能吃缺欄位、多欄位、亂序的輸入，仍保有 signature。驗證：三種輸入的 prob 都跟原始輸入一致。</p>
  </div>
  <p style="font-size:13.5px;color:var(--ink-soft);margin-top:10px">卡住了？每一題在 notebook 末節都有折疊解答——先自己做，再打開對照。</p>
</section>

<section id="quiz">
  <span class="eyebrow">07 · 驗收</span>
  <h2>情境測驗</h2>
  <p>離開前試試看：下面的情境都真的會遇到。每題選一個你認為的最佳做法，選了馬上看得到解釋。</p>
  <div data-quiz>

    <div class="quiz-q" data-answer="B">
      <p class="quiz-tag">Q1 <span class="qtype">情境題</span></p>
      <h3>線上服務程式寫死 <span class="kbd">load_model("models:/churn-clf/2")</span>。現在 v3 驗證通過要上線，而且以後每週都會有新版。最佳做法是？</h3>
      <div class="quiz-opts">
        <button type="button" class="quiz-opt" data-k="A">A. 把程式裡的 <code>/2</code> 改成 <code>/3</code>，重新部署服務；以後每週改一次</button>
        <button type="button" class="quiz-opt" data-k="B">B. 服務程式改成載 <code>models:/churn-clf@champion</code>，之後每週只做 <code>set_registered_model_alias("churn-clf", "champion", N)</code></button>
        <button type="button" class="quiz-opt" data-k="C">C. 用 <code>transition_model_version_stage(..., "Production")</code> 把 v3 設成 Production，程式改載 <code>models:/churn-clf/Production</code></button>
        <button type="button" class="quiz-opt" data-k="D">D. 把 v3 的模型檔案覆蓋到 v2 的 artifacts 路徑，程式與版本號都不用動</button>
      </div>
      <div class="quiz-fb" aria-live="polite"><p>alias 就是為了這件事存在：服務端永遠載同一個 URI，「線上是哪一版」由 Registry 裡的一個可移動標籤決定，晉升與回滾都是一行、不重新部署。A 能動但每次都要改程式碼＋部署，回滾也一樣慢；C 是舊做法，stage 已標記 deprecated，而且只有固定的幾個名字；D 是災難：版本 2 的內容被偷換，紀錄與實際不符，永遠回不去。</p></div>
    </div>

    <div class="quiz-q" data-answer="C">
      <p class="quiz-tag">Q2 <span class="qtype dx">錯誤診斷</span></p>
      <h3>模型上線第一天，服務端呼叫 <span class="kbd">pyfunc.predict(df)</span> 就炸。最可能的原因與正確修法？</h3>
      <div class="codeblock">MlflowException: Failed to enforce schema of data '...' with schema
'['f0': double (required), ..., 'f11': double (required)]'. Error: Model is missing inputs ['f11'].</div>
      <div class="quiz-opts">
        <button type="button" class="quiz-opt" data-k="A">A. 重新 <code>log_model</code> 時不要給 signature，就不會有 schema 檢查</button>
        <button type="button" class="quiz-opt" data-k="B">B. Registry 版本指錯了，載到的是舊模型；把 alias 指回正確版本</button>
        <button type="button" class="quiz-opt" data-k="C">C. 呼叫端送來的資料少了 <code>f11</code> 欄——合約沒變、資料變了；修呼叫端的資料管線（或在自訂 pyfunc 裡明確處理缺欄）</button>
        <button type="button" class="quiz-opt" data-k="D">D. 改用 <code>mlflow.sklearn.load_model</code> 原生載入，sklearn 不會檢查欄位名</button>
      </div>
      <div class="quiz-fb" aria-live="polite"><p>訊息說得很清楚：模型要 12 欄、輸入缺 <code>f11</code>。signature 在這裡發揮了它的功能——在進到模型之前就擋下，並指名缺哪欄。A 只是把錯誤延後到 scikit-learn 內部（會變成一個難懂的 shape 錯誤，甚至默默算錯）；B 症狀不符，版本錯不會產生 missing inputs；D 跟 A 一樣是拆掉安全帶，且 RandomForest 對欄位順序敏感，少一欄照樣炸或算錯。</p></div>
    </div>

    <div class="quiz-q" data-answer="A">
      <p class="quiz-tag">Q3 <span class="qtype">情境題</span></p>
      <h3>業務說「機率 ≥ 0.7 才算高風險客戶，而且這個數字每季會調」。你要把這條規則跟模型一起交付。最佳做法是？</h3>
      <div class="quiz-opts">
        <button type="button" class="quiz-opt" data-k="A">A. 寫一個 <code>PythonModel</code> 包住模型，<code>predict</code> 輸出機率與決策，門檻放在 signature 的 <code>params</code>，呼叫時可覆蓋</button>
        <button type="button" class="quiz-opt" data-k="B">B. 訓練時把標籤改成「機率 ≥ 0.7」重新訓一個分類器，模型直接輸出高／低風險</button>
        <button type="button" class="quiz-opt" data-k="C">C. 門檻寫在服務程式的常數裡，每季改一次程式碼重新部署</button>
        <button type="button" class="quiz-opt" data-k="D">D. 把門檻存成 registered model 的 tag <code>threshold=0.7</code>，服務端每次推論前讀 tag</button>
      </div>
      <div class="quiz-fb" aria-live="polite"><p>門檻是業務規則，不是模型的一部分，但又必須跟模型一起版本化與交付——自訂 pyfunc 正是為此：模型與後處理同一個部署單位，<code>params</code> 讓呼叫端調整而不改包裝（notebook 實測 0.5 → 0.9，判流失從 2 筆變 0 筆）。B 把可調的規則烙進模型，每季要重訓；C 能動但規則與模型分家，換模型時容易對不上、改一次要部署一次；D 想法對但用錯地方——tag 是中繼資料，服務端每次推論去查 Registry 既慢又脆弱。</p></div>
    </div>

    <div class="quiz-q" data-answer="D">
      <p class="quiz-tag">Q4 <span class="qtype dx">錯誤診斷</span></p>
      <h3>同事照舊教學寫 <span class="kbd">mlflow.set_tracking_uri("./mlruns")</span>，第一個 run 就炸出下面這段。怎麼修最對？</h3>
      <div class="codeblock">MlflowException: The filesystem tracking backend (e.g., './mlruns') is in maintenance mode and
will not receive further updates. Please migrate to a database backend (e.g., 'sqlite:///mlflow.db')
... set `MLFLOW_ALLOW_FILE_STORE=true` to opt out of this exception.</div>
      <div class="quiz-opts">
        <button type="button" class="quiz-opt" data-k="A">A. 磁碟權限問題，<code>./mlruns</code> 資料夾要先手動建立並開放寫入</button>
        <button type="button" class="quiz-opt" data-k="B">B. 降版到 MLflow 2.x，舊教學都是用那版寫的</button>
        <button type="button" class="quiz-opt" data-k="C">C. 設環境變數 <code>MLFLOW_ALLOW_FILE_STORE=true</code> 就好，之後一直這樣用</button>
        <button type="button" class="quiz-opt" data-k="D">D. 改成 <code>set_tracking_uri("sqlite:///mlflow.db")</code>——一樣零安裝，而且 Registry、alias 這些功能都要資料庫後端才有</button>
      </div>
      <div class="quiz-fb" aria-live="polite"><p>訊息本身就給了答案：檔案後端進入維護模式，請改用資料庫後端。SQLite 是一個檔案、零安裝，跟資料夾模式一樣方便，卻多了 Model Registry（純檔案模式從來不支援註冊與 alias）。A 讀錯訊息，這不是權限錯誤；B 為了舊教學鎖死版本，之後所有新功能都用不到；C 是訊息提供的<b>暫時</b>逃生口——課堂上救急可以，但它明說「不再更新」，而且照樣沒有 Registry。</p></div>
    </div>

    <div class="quiz-q" data-answer="B">
      <p class="quiz-tag">Q5 <span class="qtype">情境題</span></p>
      <h3>同一份訓練程式、同樣的 params、同樣的隨機種子，上週的 run AUC 0.968，今天重跑只有 0.951。第一件該查的事是？</h3>
      <div class="quiz-opts">
        <button type="button" class="quiz-opt" data-k="A">A. 隨機種子沒生效，多跑幾次取平均</button>
        <button type="button" class="quiz-opt" data-k="B">B. 比對兩個 run 的 <code>inputs</code>——<code>log_input</code> 記的 dataset digest 是否相同；不同就是資料變了</button>
        <button type="button" class="quiz-opt" data-k="C">C. 換一個更強的模型，讓它對資料變化沒那麼敏感</button>
        <button type="button" class="quiz-opt" data-k="D">D. 把今天的 run 刪掉，alias 繼續指上週那版就好</button>
      </div>
      <div class="quiz-fb" aria-live="polite"><p>重現 ＝ 同樣的程式＋設定＋<b>資料</b>。程式與設定都有紀錄且相同，剩下的變數就是資料；<code>log_input</code> 記的 digest 是內容指紋，任何一格改了指紋就不同——先看它，一秒排除或確認。A 種子相同的話 sklearn 是決定性的，平均不會揭露原因；C 在沒搞清楚原因前換模型，只是把問題藏起來；D 逃避問題，如果資料真的變了（例如上游欄位定義改了），線上那版可能也已經不適用。</p></div>
    </div>

    <div class="quiz-score" data-score></div>
  </div>
</section>

<div class="endnav">
  <a href="/mlops/">
    <span class="tag">主題</span>
    <b>‹ 回「MLOps 自動化技術」課程列表</b>
  </a>
</div>
"""

SCRIPT = r"""
/* ═══ hero 互動：alias 切換器（機率＝notebook 實測 v1/v2 對 test 前 8 筆；指標＝evaluate 實測）═══ */
(function () {
  const CUST = [405, 1190, 1132, 731, 1754, 1178, 1533, 1303];
  const ACTUAL = [1, 0, 1, 0, 1, 1, 0, 0];
  const PROB = {
    1: [0.918, 0.006, 0.906, 0.039, 0.911, 0.853, 0.017, 0.067],
    2: [0.746, 0.071, 0.843, 0.174, 0.851, 0.734, 0.069, 0.148],
  };
  const NAME = { 1: "LogisticRegression", 2: "RandomForestClassifier" };
  let champion = 1;
  const v1 = document.getElementById("rg-v1"), v2 = document.getElementById("rg-v2");
  const svc = document.getElementById("rg-svc"), tbl = document.getElementById("rg-tbl");
  const thr = document.getElementById("rg-thr"), thrV = document.getElementById("rg-thr-v");
  function render() {
    const t = +thr.value; thrV.textContent = t.toFixed(2);
    v1.classList.toggle("live", champion === 1); v2.classList.toggle("live", champion === 2);
    const p = PROB[champion];
    let hits = 0, flagged = 0;
    const rows = CUST.map((c, i) => { const pred = p[i] >= t ? 1 : 0; const hit = pred === ACTUAL[i]; hits += hit; flagged += pred;
      return `<tr><td>${c}</td><td>${p[i].toFixed(3)}</td><td>${pred}</td><td>${ACTUAL[i]}</td><td class="${hit ? "hit" : "miss"}">${hit ? "✓" : "✗"}</td></tr>`; });
    svc.innerHTML = `model = mlflow.pyfunc.load_model("models:/churn-clf<span class="hl">@champion</span>")<br># → version <span class="hl">${champion}</span>（${NAME[champion]}）· 8 位客戶判流失 ${flagged} 位、答對 ${hits} 位`;
    tbl.innerHTML = "<tr><th>customer</th><th>prob</th><th>pred</th><th>actual</th><th></th></tr>" + rows.join("");
  }
  document.getElementById("rg-promote").addEventListener("click", () => { champion = 2; render(); });
  document.getElementById("rg-rollback").addEventListener("click", () => { champion = 1; render(); });
  thr.addEventListener("input", render);
  render();
})();
"""

PANEL_STEPS = """
        <li>登入 molab（GitHub / Google）</li>
        <li>開啟課程 notebook，<b>Fork 成自己的副本</b>即可編輯</li>
        <li>從第一格往下全部執行（首次安裝套件約 1–2 分鐘）——<b>免費 CPU 環境即可</b>，不需要 GPU；Registry 就是本機一個 SQLite 檔</li>
"""
