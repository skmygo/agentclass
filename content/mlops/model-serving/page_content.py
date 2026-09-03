"""課程頁內容區（純常數）。改完跑：python3 .claude/skills/make-lesson/scripts/page-fill.py content/mlops/model-serving
build.sh 不會部署這個檔；它是 index.html 內容區的正本。"""

TITLE = "模型上線：從 pyfunc 到 REST API"
DESCRIPTION = "模型上線的三種形態一次做完：批次評分、自己包 FastAPI、mlflow models serve。signature 怎麼變成 REST API 的輸入驗證、/invocations 的四種 payload 寫法與真實 400 原文、模型載一次 vs 每次載差 10 倍、alias 移了 API 何時才知道——molab 免費環境全程實作。"
NB = "https://molab.marimo.io/github/skmygo/agentclass/blob/main/content/mlops/model-serving/model-serving_ext.py"

STYLE = r"""
  /* 語義色：藍＝批次評分、橘＝線上 API、綠＝200／通過、紅＝400／反模式 */
  :root { --c1: #4C72B0; --c2: #DD8452; --c3: #55A868; --cut: #C44E52; }
  a.golab { text-decoration: none; display: inline-flex; align-items: center; gap: 8px; }

  /* hero：請求模擬器 */
  #sv-demo .ctl { display: flex; gap: 7px; flex-wrap: wrap; align-items: center; margin-bottom: 9px; }
  #sv-demo .lbl { font-size: 11.5px; font-weight: 800; letter-spacing: .06em; color: var(--ink-soft); min-width: 54px; }
  #sv-demo .ctl button { font-family: var(--mono); font-size: 12.5px; padding: 5px 11px; border-radius: 8px;
    border: 1.5px solid var(--grid); background: #fff; color: var(--ink); cursor: pointer; transition: border-color .15s, background .15s; }
  #sv-demo .ctl button:hover { background: var(--chip-bg); }
  #sv-demo .ctl button.on { border-color: var(--ink); background: var(--ink); color: #fff; }
  #sv-demo .ctl.dim { opacity: .38; pointer-events: none; }
  #sv-demo .io { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin: 12px 0 4px; }
  #sv-demo .pane { border: 1.5px solid var(--grid); border-radius: 10px; padding: 8px 10px 10px; min-width: 0; }
  #sv-demo .ptag { font-size: 10.5px; font-weight: 800; letter-spacing: .08em; color: var(--ink-soft); display: block; margin-bottom: 5px; }
  #sv-demo pre { font-family: var(--mono); font-size: 11.5px; line-height: 1.5; margin: 0; white-space: pre-wrap;
    word-break: break-word; overflow-wrap: anywhere; max-height: 168px; overflow-y: auto; }
  #sv-demo .stat { font-family: var(--mono); font-size: 12px; font-weight: 800; margin-bottom: 6px; }
  #sv-demo .stat .code { padding: 1px 7px; border-radius: 999px; color: #fff; margin-right: 7px; }
  #sv-demo .stat.ok .code { background: var(--c3); } #sv-demo .stat.bad .code { background: var(--cut); }
  #sv-demo .stat .ms { color: var(--ink-soft); font-weight: 600; }
  #sv-demo .lat { border-top: 1px solid var(--grid); margin-top: 10px; padding-top: 10px; }
  #sv-demo .lat label { font-size: 12.5px; font-weight: 700; display: inline-flex; align-items: center; gap: 7px; cursor: pointer; }
  #sv-demo .bars { margin-top: 8px; display: grid; gap: 5px; }
  #sv-demo .bar { display: grid; grid-template-columns: 128px 1fr; gap: 8px; align-items: center; font-size: 12px; opacity: .5; transition: opacity .15s; }
  #sv-demo .bar.now { opacity: 1; }
  #sv-demo .bar > span { font-family: var(--mono); font-size: 11.5px; color: var(--ink-soft); }
  #sv-demo .track { display: flex; align-items: center; gap: 7px; min-width: 0; overflow: hidden; }
  #sv-demo .bar i { height: 15px; border-radius: 4px; display: block; flex: none; }
  #sv-demo .bar em { font-style: normal; font-family: var(--mono); font-size: 11px; color: var(--ink-soft); white-space: nowrap; }
  #sv-demo .bar.now em { color: var(--ink); font-weight: 700; }
  #sv-demo .bar.fast i { background: var(--c2); } #sv-demo .bar.slow i { background: var(--cut); }
  @media (max-width: 620px) { #sv-demo .io { grid-template-columns: 1fr; } #sv-demo .bar { grid-template-columns: 104px 1fr; } }

  table.cmp { width: 100%; border-collapse: collapse; font-size: 13.5px; margin: 14px 0; }
  table.cmp th, table.cmp td { border-bottom: 1px solid var(--grid); padding: 8px 10px; text-align: left; vertical-align: top; }
  table.cmp th { font-size: 12px; letter-spacing: .04em; color: var(--ink-soft); }
  table.cmp td.b { color: var(--c1); font-weight: 700; } table.cmp td.o { color: var(--c2); font-weight: 700; }
  .kbd { font-family: var(--mono); background: var(--chip-bg); padding: 1px 6px; border-radius: 5px; font-size: 13px; }
"""

WRAP = r'''
<section id="hero">
  <span class="eyebrow">SERVING · 補充 A · 06</span>
  <h1>模型上線：<br>從 pyfunc 到 REST API</h1>
  <p style="margin-top:18px">
    Registry 裡有一個 <span class="kbd">models:/churn-clf@champion</span> 了，然後呢？模型待在 Registry 裡不會替公司賺到一塊錢——
    它要被「用」，才叫上線。而「上線」有三種形態，成本差好幾個數量級。先玩最貴的那一種：
    一台 <span class="kbd">mlflow models serve</span> 起來的伺服器，你送什麼、它回什麼——
  </p>

  <div class="hero-demo" id="sv-demo">
    <div class="ctl">
      <span class="lbl">端點</span>
      <button type="button" data-ep="ping">GET /ping</button>
      <button type="button" data-ep="version">GET /version</button>
      <button type="button" data-ep="inv" class="on">POST /invocations</button>
    </div>
    <div class="ctl" id="sv-fmts">
      <span class="lbl">payload</span>
      <button type="button" data-fmt="split" class="on">dataframe_split</button>
      <button type="button" data-fmt="records">dataframe_records</button>
      <button type="button" data-fmt="instances">instances</button>
      <button type="button" data-fmt="missing">少一欄 f11</button>
      <button type="button" data-fmt="raw">沒有信封</button>
    </div>
    <div class="io">
      <div class="pane"><span class="ptag">送出的 REQUEST</span><pre id="sv-req"></pre></div>
      <div class="pane"><span class="ptag">收到的 RESPONSE</span><div class="stat" id="sv-stat"></div><pre id="sv-res"></pre></div>
    </div>
    <div class="lat">
      <label><input type="checkbox" id="sv-slow"> 把 <span class="kbd">load_model</span> 寫進每一個請求裡（很多人第一版都這樣寫）</label>
      <div class="bars">
        <div class="bar fast now"><span>模型載一次</span><div class="track"><i style="width:7%"></i><em>14–36 ms</em></div></div>
        <div class="bar slow"><span>每次請求都載</span><div class="track"><i style="width:58%"></i><em>120–310 ms</em></div></div>
      </div>
    </div>
  </div>

  <p class="note">
    狀態碼、JSON 與錯誤訊息都是 notebook 的實測輸出（MLflow 3.15.2）；毫秒是同一台機器上多次量測的範圍，
    你自己跑會不一樣——看倍數，不要看絕對值。
  </p>
</section>

<section id="s1">
  <span class="eyebrow">01 · 三種形態</span>
  <h2>上線不是一件事，是三個選擇</h2>
  <p>
    很多人一聽到「模型上線」就開始寫 REST API——那是最貴的一種，而且常常沒必要。先問一個問題：<b>答案什麼時候需要？</b>
  </p>
  <table class="cmp">
    <tr><th></th><th>批次評分</th><th>線上 API</th><th>嵌入式</th></tr>
    <tr><td>答案什麼時候要</td><td>明天早上就好</td><td>這一秒</td><td>這一秒，而且不能連網</td></tr>
    <tr><td>怎麼跑</td><td>排程跑一支腳本，結果寫回資料庫</td><td>一台一直開著的伺服器收 HTTP 請求</td><td>模型跟著 App 發佈，同一個行程裡呼叫</td></tr>
    <tr><td>一列的成本</td><td class="b">最低（實測每列約 0.02 ms）</td><td class="o">高（實測每筆 14–36 ms）</td><td>最低（沒有網路）</td></tr>
    <tr><td>要維運什麼</td><td>一個排程</td><td>伺服器、擴縮、健康檢查、監控、版本切換</td><td>App 的發版流程</td></tr>
    <tr><td>換模型多快</td><td>下一次排程就生效</td><td>一行 alias ＋ 重載</td><td>要等使用者更新 App</td></tr>
    <tr><td>典型場景</td><td>每日流失名單、隔夜信用評分</td><td>交易反詐、即時定價、對話系統</td><td>手機相機特效、離線裝置、資料庫 UDF</td></tr>
  </table>
  <p>
    三種不互斥——真實系統常常是「批次算好大部分，線上 API 只補算新客戶」。
    <b>判準只有一條</b>：如果「昨天算好的答案」就夠用，就別為了即時性去付一台伺服器 24 小時的錢；
    那台伺服器要監控、要擴縮、要值班，而排程壞掉只是明天的報表晚一點。
  </p>
  <a class="golab" href="__NB__" target="_blank" rel="noopener">到 notebook 的 1️⃣ 節：三種形態的完整對照</a>
</section>

<section id="s2">
  <span class="eyebrow">02 · 打包</span>
  <h2>signature、input_example、pyfunc_predict_fn：為了上線而存在的三樣東西</h2>
  <div class="codeblock">sig = infer_signature(X_train, rf.predict_proba(X_train))   # 輸出 Tensor('float64', (-1, 2))

with mlflow.start_run(run_name="v2-rf-depth8"):
    info = mlflow.sklearn.log_model(
        rf, name="churn_model",
        signature=sig,                        # → 之後變成 REST API 的輸入驗證
        input_example=X_train.head(2),        # → 資料夾裡多一個 serving_input_example.json
        pyfunc_predict_fn="predict_proba",    # → pyfunc 的 predict 改叫 predict_proba
    )
mlflow.register_model(info.model_uri, "churn-clf")</div>
  <p>
    <b>signature</b> 上一課擋掉了「少一欄」的輸入；這一課它更狠——<span class="kbd">mlflow models serve</span> 會把它
    <b>直接變成 REST API 的輸入驗證</b>：少一欄、型別錯的請求根本進不到模型，伺服器回 400 並指名哪裡錯。你一行驗證程式都不用寫。
  </p>
  <p>
    <b>input_example</b> 會讓模型資料夾多一個 <span class="kbd">serving_input_example.json</span>——那是一份
    <b>可以直接 POST 的 payload</b>（信封就是 <span class="kbd">dataframe_split</span>）。實測 champion 那一版的資料夾共 8 個檔案：
    <span class="kbd">MLmodel</span>、<span class="kbd">model.skops</span>、<span class="kbd">conda.yaml</span>、<span class="kbd">python_env.yaml</span>、
    <span class="kbd">requirements.txt</span>、<span class="kbd">input_example.json</span>、<span class="kbd">serving_input_example.json</span>、<span class="kbd">registered_model_meta</span>。
  </p>
  <p>
    <b>pyfunc_predict_fn</b>：pyfunc 是部署工具唯一認得的介面，但它只有一個 <span class="kbd">predict</span>，而 sklearn 分類器的
    <span class="kbd">predict</span> 回類別（0/1）。流失預測要的是機率——這個參數就是在說「被當成 pyfunc 呼叫時，請去叫 predict_proba」。
    之後不管是 <span class="kbd">pyfunc.predict()</span> 還是 <span class="kbd">/invocations</span>，每列都回兩個數字 <span class="kbd">[P(不流失), P(流失)]</span>。
  </p>
  <a class="golab" href="__NB__" target="_blank" rel="noopener">到 notebook 的 2️⃣ 節：三個參數與模型資料夾</a>
</section>

<section id="s3">
  <span class="eyebrow">03 · 批次評分</span>
  <h2>最便宜的上線方式，只有三行</h2>
  <div class="codeblock">model = mlflow.pyfunc.load_model("models:/churn-clf@champion")
scores = model.predict(all_customers)                      # 一次算完整張表
all_customers.assign(prob=scores[:, 1]).to_csv("today.csv")</div>
  <p>
    沒有伺服器、沒有 API、沒有健康檢查——一支腳本掛到排程上就上線了；模型換版？下一次排程自動載到新的
    <span class="kbd">@champion</span>。這是維運成本最低的一種上線。
  </p>
  <table class="cmp">
    <tr><th>怎麼餵</th><th>總耗時</th><th>每列成本</th></tr>
    <tr><td class="b">一次 500 列</td><td>約 9–12 ms</td><td class="b">約 0.02 ms</td></tr>
    <tr><td>一次 1 列（跑 50 次取平均）</td><td>—</td><td>約 7–11 ms</td></tr>
    <tr><td colspan="3" style="color:var(--ink-soft)">同一個模型、同一台機器，每列成本差 <b>300–500 倍</b>（多次量測）；<span class="kbd">load_model</span> 本身約 100–200 ms。</td></tr>
  </table>
  <p>
    為什麼？推論的固定開銷（建 DataFrame、schema 檢查、走訪 100 棵樹的 Python 呼叫）幾乎跟列數無關，
    一次算越多列就攤得越薄。<b>這就是批次便宜的全部原因</b>——反過來說，一次只算十列的「批次」，跟線上 API 差不了多少。
  </p>
  <a class="golab" href="__NB__" target="_blank" rel="noopener">到 notebook 的 3️⃣ 節：批次計時、寫回 CSV</a>
</section>

<section id="s4">
  <span class="eyebrow">04 · 自己包 FastAPI</span>
  <h2>模型載一次，請求只做推論</h2>
  <div class="codeblock">model = mlflow.pyfunc.load_model("models:/churn-clf@champion")   # ← 啟動時載入，一次

@api.post("/predict")
def api_predict(rows: list[dict]):
    proba = model.predict(pd.DataFrame(rows))
    return {"prob": [round(float(p[1]), 4) for p in proba], "model_version": SERVED["version"]}

@api.get("/health")
def api_health():
    return {"status": "ok", "model_uri": MODEL_URI, "model_version": SERVED["version"]}</div>
  <p>
    自己包的好處是<b>介面完全照你的規矩</b>：欄位名稱、回傳格式、認證、記錄都自己決定。
    伺服器用 uvicorn 跑在背景執行緒，port 現跟作業系統要一個（寫死 port 的下場是
    <span class="kbd">OSError(98, 'Address already in use')</span>）。
  </p>
  <p>
    這裡有一個新手最常犯、而且上線之後才會痛的錯：<b>把 <span class="kbd">load_model</span> 寫進 handler 裡面</b>。
    看起來很合理（「這樣就永遠是最新的模型」），但每一筆請求都要重新讀檔、反序列化、重建模型物件。實測同一台機器、同一個模型：
  </p>
  <table class="cmp">
    <tr><th>端點</th><th>差別</th><th>單筆延遲（多次量測的範圍）</th></tr>
    <tr><td class="o">/predict</td><td>模型載一次</td><td>約 14–36 ms（中位 14–33 ms）</td></tr>
    <tr><td style="color:var(--cut);font-weight:700">/predict_slow</td><td>每次請求都 <span class="kbd">load_model</span></td><td>約 120–310 ms（中位 122–297 ms）</td></tr>
  </table>
  <p>
    同樣的答案，延遲差 <b>8–10 倍</b>——而且這台機器沒有別的負載；正式環境同時有幾十個請求進來時差距只會更大，
    因為每個請求都在重複做同一件昂貴的事，還互相搶 CPU 與磁碟。「換版怎麼辦」是第 6 節的題目，不是把
    <span class="kbd">load_model</span> 搬進 handler 的理由。
  </p>
  <a class="golab" href="__NB__" target="_blank" rel="noopener">到 notebook 的 4️⃣ 節：兩個端點並排實測＋對數刻度成本圖</a>
</section>

<section id="s5">
  <span class="eyebrow">05 · MLFLOW MODELS SERVE</span>
  <h2>不寫服務程式的另一條路</h2>
  <div class="codeblock">mlflow models serve -m models:/churn-clf@champion -p 5001 --env-manager local

GET  /ping          → 200，body 是空的（健康檢查只看狀態碼，別去解析它）
GET  /version       → 3.15.2（MLflow 的版本，不是模型版本）
POST /invocations   → {"predictions": [[0.2540, 0.7460], [0.9286, 0.0714]]}</div>
  <p>
    自己包很自由，但也代表<b>每一個模型都要有人寫一支服務程式</b>。MLflow 內建的伺服器一行指令就把 Registry 裡的模型變成 REST API，
    實測從下指令到 <span class="kbd">/ping</span> 回 200 約 <b>7–15 秒</b>（載模型、建 app、起 WSGI 伺服器）——
    所以<b>正式環境不要靠重啟來換模型</b>。
  </p>
  <p>
    <span class="kbd">--env-manager local</span> 是「直接用目前這個 Python 環境」。不加的話 MLflow 會照模型資料夾裡的
    <span class="kbd">requirements.txt</span> 建一個乾淨的虛擬環境再跑——那才是正式部署該做的（環境跟著模型走，
    不會因為這台機器裝了別的版本而算錯），代價是啟動要多花好幾分鐘。
  </p>
  <p>
    <span class="kbd">/invocations</span> <b>不吃裸的 JSON 陣列</b>，一定要有信封告訴它形狀。四個名字擇一：
    <span class="kbd">dataframe_split</span>（欄名與資料分開，最省頻寬）、<span class="kbd">dataframe_records</span>（每列一個物件，最好讀）、
    <span class="kbd">inputs</span>（欄名對值清單）、<span class="kbd">instances</span>（純 2D 陣列——<b>這個模型不吃</b>，因為 signature 要欄名）。
    實測 <span class="kbd">dataframe_split</span> 帶不帶 <span class="kbd">index</span> 都回 200，慣例是拿掉。
  </p>
  <div class="codeblock">// 少一欄 f11 → HTTP 400
{"error_code": "INVALID_PARAMETER_VALUE", "message": "Failed to predict data ... Error: Failed to enforce
 schema of data ... Error: Model is missing inputs ['f11'].", "sqlstate": "KAM01",
 "error_class": "SCHEMA_ENFORCEMENT_FAILED"}

// 沒有信封（直接送 list）→ HTTP 400
{"error_code": "BAD_REQUEST", "message": "Invalid input. The input must be a JSON dictionary with exactly
 one of the input fields {'dataframe_split', 'inputs', 'dataframe_records', 'instances'}. Received a list.",
 "sqlstate": "KAM00", "error_class": "INVALID_PARAMETER_VALUE"}</div>
  <p>
    看懂這兩段，就懂了這條路的價值：<b>signature 變成了 API 的輸入驗證</b>，呼叫端少送一欄在進到模型之前就被擋下，
    訊息還直接指名缺哪一欄；連信封放錯都講得清清楚楚（那四個名字的順序每次不同，因為它是 Python 的 set）。
    自己包的 FastAPI 要達到同樣品質，schema、400、錯誤訊息都得自己寫。<b>這就是取捨</b>：內建伺服器給你標準與嚴謹，自包給你自由。
  </p>
  <p>
    最後別忘了收：子行程不會跟著 notebook 結束，<span class="kbd">terminate()</span> ＋ <span class="kbd">communicate(timeout=15)</span> 送出結束訊號並等它真的走掉，
    不然它會一直占著那個 port 跑下去。
  </p>
  <a class="golab" href="__NB__" target="_blank" rel="noopener">到 notebook 的 5️⃣ 節：六種請求一次打完、看伺服器怎麼回</a>
</section>

<section id="s6">
  <span class="eyebrow">06 · 換版不停機</span>
  <h2>alias 移了，跑著的 API 什麼時候才知道？</h2>
  <p>
    上一課說「晉升＝把 champion 移到新版本，服務程式一行不用改」。這句話有一個沒說出口的前提：
    <b>服務程式要重新載入模型，才會看到新的 alias。</b>因為第 4 節那條規則——模型在啟動時載入一次——
    跑著的行程裡是一個<b>已經載好的物件</b>，它不會因為資料庫裡一列 alias 改了就自己變身。
    實測：v3 註冊、alias 移過去之後，<span class="kbd">/health</span> 照樣回舊版本、<span class="kbd">/predict</span> 照樣回舊機率。
  </p>
  <div class="codeblock">@api.post("/reload")
def api_reload():
    now = int(client.get_model_version_by_alias("churn-clf", "champion").version)
    if now == SERVED["version"]:
        return {"reloaded": False, "model_version": now}      # ← 版本沒變就別動
    SERVED["model"] = mlflow.pyfunc.load_model(MODEL_URI)     # 換上新的
    SERVED["version"] = now
    return {"reloaded": True, "model_version": now}</div>
  <table class="cmp">
    <tr><th>做法</th><th>怎麼觸發</th><th>停機</th><th>適合</th></tr>
    <tr><td>重啟服務</td><td>部署流程重跑（<span class="kbd">mlflow models serve</span> 只能這樣）</td><td>有（起一次 7–15 秒）</td><td>多台輪流更新時可接受</td></tr>
    <tr><td>主動觸發 <span class="kbd">POST /reload</span></td><td>晉升流程的最後一步去打它</td><td>無</td><td>自己包的 API、換版時機明確</td></tr>
    <tr><td>定時輪詢</td><td>背景每 N 秒問 Registry，版本變了才重載</td><td>無</td><td>多台機器、不想讓晉升流程知道有誰在跑</td></tr>
  </table>
  <p>
    那個 <span class="kbd">if</span> 很重要：重載期間行程會多吃一份記憶體、還有幾百毫秒的延遲尖峰，版本沒變就不該白做。
    另外兩個實務細節：<b>換版要留紀錄</b>（哪一秒從 v2 換到 v3，之後查指標異常時第一個要對的就是它）；
    <b>回滾走同一條路</b>（alias 指回去、再打一次 <span class="kbd">/reload</span>），所以這條路平常就要是通的。
    順帶一提，<span class="kbd">get_model_version_by_alias(...).version</span> 回的是 <b>int</b> 不是字串——拿去跟
    <span class="kbd">"3"</span> 比對會永遠不相等，這種靜默的比較失敗最難查。
  </p>
  <a class="golab" href="__NB__" target="_blank" rel="noopener">到 notebook 的 6️⃣ 節：晉升 → 不重載 → /reload 的完整過程</a>
</section>

<section id="s7">
  <span class="eyebrow">07 · 上線前後</span>
  <h2>檢查清單，與上線之後該記什麼</h2>
  <div class="codeblock">payload = json.loads((model_dir / "serving_input_example.json").read_text())
mlflow.models.validate_serving_input(model_uri, payload)   # 不用起伺服器，完整走一次反序列化＋schema＋推論</div>
  <p>
    模型能載入 ≠ 模型能上線。四件事，每一件都是有人半夜被叫起來換來的：
    <b>①</b> 用模型自己帶的 <span class="kbd">serving_input_example.json</span> 跑
    <span class="kbd">validate_serving_input</span>——別讓 400 在正式環境才出現；
    <b>②</b> 用同一份 payload 打一次真的服務（「模型能載入」跟「服務能回應」中間還隔著 HTTP 與 JSON 序列化）；
    <b>③</b> 對答案：同一批輸入，批次算的機率要跟 API 回的一樣，不一樣就是線上／離線前處理不同步
    （陷阱：對答案前要<b>重新載入</b> champion，拿換版前那份舊模型去比，只會得到一個假的「不一致」警報）；
    <b>④</b> 版本要看得見：<span class="kbd">/health</span> 回目前模型版本，不然出事時你連「當時線上是哪一版」都答不出來。
  </p>
  <table class="cmp">
    <tr><th>上線後記什麼</th><th>為什麼</th><th>出事時的樣子</th></tr>
    <tr><td>延遲 p50 / p95 / p99</td><td>平均值會騙人</td><td>平均 20 ms 很漂亮，p99 是 3 秒</td></tr>
    <tr><td>錯誤率（依狀態碼分）</td><td>400 跟 500 是完全不同的故障</td><td>400 暴增＝上游資料格式變了；500 暴增＝服務壞了</td></tr>
    <tr><td>輸入分佈</td><td>資料會漂移，沒人會通知你</td><td>模型還在回答，只是越答越不準</td></tr>
    <tr><td>預測分佈</td><td>最省事的早期警報</td><td>判為流失的比例從 5% 跳到 30%</td></tr>
  </table>
  <p>
    前兩類是<b>軟體維運</b>，任何 API 都要有；後兩類是<b>機器學習特有</b>的——模型不會拋例外，它只會安靜地越答越爛。
    這正是下一課「模型監控」要處理的事。
  </p>
  <a class="golab" href="__NB__" target="_blank" rel="noopener">到 notebook 的 7️⃣–8️⃣ 節：三項冒煙檢查＋自己拉桿量成本</a>
</section>

<section id="s8">
  <span class="eyebrow">08 · 實戰</span>
  <h2>換你動手</h2>
  <div class="ex">
    <span class="lv">LEVEL 1</span>
    <p>把 <span class="kbd">/health</span> 加上「模型是什麼時候載進來的」與「已經服務幾筆請求」——線上排查時這兩個數字幾乎每次都會用到。</p>
  </div>
  <div class="ex">
    <span class="lv">LEVEL 2</span>
    <p>改用 <span class="kbd">dataframe_records</span> 信封重打 <span class="kbd">/invocations</span>，並故意少送一欄，把狀態碼與錯誤裡的 <span class="kbd">error_class</span> 印出來。</p>
  </div>
  <div class="ex">
    <span class="lv">LEVEL 3</span>
    <p>不用真的 build，自己手寫 <span class="kbd">mlflow models build-docker</span> 會產出的那份 Dockerfile：裝什麼、模型檔怎麼進去、<span class="kbd">CMD</span> 怎麼寫、健康檢查指到哪。想想「環境跟著模型走」具體是哪一行。</p>
  </div>
  <p style="font-size:13.5px;color:var(--ink-soft);margin-top:10px">卡住了？每一題在 notebook 末節都有折疊解答——先自己做，再打開對照。</p>
</section>

<section id="quiz">
  <span class="eyebrow">09 · 驗收</span>
  <h2>情境測驗</h2>
  <p>離開前試試看：下面的情境都真的會遇到。每題選一個你認為的最佳做法，選了馬上看得到解釋。</p>
  <div data-quiz>

    <div class="quiz-q" data-answer="B">
      <p class="quiz-tag">Q1 <span class="qtype">情境題</span></p>
      <h3>客服部門要一份「今天最該打電話的 200 位流失高風險客戶」名單，每天早上九點看；資料半夜三點就備妥。團隊提議先寫一個 REST API 給客服系統即時查。最佳做法是？</h3>
      <div class="quiz-opts">
        <button type="button" class="quiz-opt" data-k="A">A. 照提議寫 FastAPI 服務常駐，客服系統每開一位客戶就打一次</button>
        <button type="button" class="quiz-opt" data-k="B">B. 寫一支批次評分腳本掛排程：三點半 <code>load_model</code> 一次、把整張客戶表算完寫回資料庫，九點客服直接查表</button>
        <button type="button" class="quiz-opt" data-k="C">C. 起一台 <code>mlflow models serve</code>，早上用迴圈一列一列打 <code>/invocations</code> 產出名單</button>
        <button type="button" class="quiz-opt" data-k="D">D. 把模型嵌進客服系統，每台客服電腦各自載一份模型算</button>
      </div>
      <div class="quiz-fb" aria-live="polite"><p>需求裡的關鍵字是「每天早上九點看」——答案<b>不需要即時</b>，那就別去付一台伺服器 24 小時的錢。批次評分只是一支腳本加一個排程：沒有擴縮、沒有健康檢查、沒有值班，換模型下一次排程自動生效；而且每列成本實測差約 300 倍（一次 500 列每列約 0.02 ms，一次一列每列約 7 ms）。A 能動，但為了一個不需要即時的需求引進了伺服器、監控、版本切換一整套維運。C 最糟：既付了伺服器的代價，又用一列一筆的方式打，把批次的成本優勢全丟掉。D 讓每台電腦各自載模型，換版時要等所有客戶端更新，而且模型檔散在各處。</p></div>
    </div>

    <div class="quiz-q" data-answer="B">
      <p class="quiz-tag">Q2 <span class="qtype dx">錯誤診斷</span></p>
      <h3>同事把原本打自家 FastAPI 的程式（<span class="kbd">requests.post(url, json=rows)</span>，<span class="kbd">rows</span> 是一串 dict）直接指向新起的 <span class="kbd">mlflow models serve</span>，每次都回 400。最直接的修法是？</h3>
      <div class="codeblock">{"error_code": "BAD_REQUEST", "message": "Invalid input. The input must be a JSON dictionary with exactly
 one of the input fields {'dataframe_split', 'inputs', 'dataframe_records', 'instances'}. Received a list.",
 "sqlstate": "KAM00", "error_class": "INVALID_PARAMETER_VALUE"}</div>
      <div class="quiz-opts">
        <button type="button" class="quiz-opt" data-k="A">A. 模型的 signature 壞了，重新 <code>log_model</code> 一次再註冊</button>
        <button type="button" class="quiz-opt" data-k="B">B. 少了信封：把整串包成 <code>{"dataframe_records": rows}</code> 再送</button>
        <button type="button" class="quiz-opt" data-k="C">C. 請求沒帶 <code>Content-Type: application/json</code>，伺服器把 body 當成純文字</button>
        <button type="button" class="quiz-opt" data-k="D">D. 端點打錯了，<code>mlflow models serve</code> 的推論端點是 <code>/predict</code> 不是 <code>/invocations</code></button>
      </div>
      <div class="quiz-fb" aria-live="polite"><p>訊息把答案寫在臉上：「必須是一個 JSON 物件，而且剛好含有這四個欄位之一」，「收到的是一個 list」。<code>/invocations</code> 不吃裸陣列，一定要有信封說明形狀——這串 dict 的形狀正好對應 <code>dataframe_records</code>（<code>dataframe_split</code>／<code>inputs</code> 是另外兩種寫法，<code>instances</code> 沒有欄名，這個模型的 signature 不吃）。順帶一提，那四個名字的順序每次執行都不同，因為它是 Python 的 set，別把順序當成規格。A 完全沒有根據，訊息連 schema 都還沒檢查到；C 若真的沒帶 Content-Type，錯誤會長得完全不一樣，而且 <code>requests</code> 的 <code>json=</code> 會自動帶；D 是把自家 API 的習慣套上來，<code>/predict</code> 是第 4 節自己包的那台才有的端點。</p></div>
    </div>

    <div class="quiz-q" data-answer="C">
      <p class="quiz-tag">Q3 <span class="qtype dx">錯誤診斷</span></p>
      <h3>推論服務上線後延遲從 15 ms 掉到 300 ms 上下，錯誤率是 0、機器負載也不高。這次改動只動了這一段。最可能的原因與修法？</h3>
      <div class="codeblock">@api.post("/predict")
def api_predict(rows: list[dict]):
    model = mlflow.pyfunc.load_model("models:/churn-clf@champion")   # 「這樣才會永遠載到最新版」
    return {"prob": [float(p[1]) for p in model.predict(pd.DataFrame(rows))]}</div>
      <div class="quiz-opts">
        <button type="button" class="quiz-opt" data-k="A">A. RandomForest 有 100 棵樹太重，換成 LogisticRegression 就會快回來</button>
        <button type="button" class="quiz-opt" data-k="B">B. 單一 worker 塞住了，把 uvicorn 的 <code>--workers</code> 開到 8</button>
        <button type="button" class="quiz-opt" data-k="C">C. 每個請求都重新 <code>load_model</code>（實測慢 8–10 倍）——改回啟動時載一次，換版改走 <code>/reload</code> 或重啟</button>
        <button type="button" class="quiz-opt" data-k="D">D. payload 改用 <code>dataframe_split</code> 省頻寬，序列化成本就會降下來</button>
      </div>
      <div class="quiz-fb" aria-live="polite"><p>把 <code>load_model</code> 搬進 handler，等於每一筆請求都要重新讀檔、反序列化、重建模型物件；實測同一台機器、同一個模型，載一次是 15–35 ms，每次都載是 120–310 ms，差 8–10 倍——正好對得上症狀（延遲整體上移、錯誤率 0、負載不高，因為瓶頸是每次請求的固定成本而不是流量）。註解裡那個動機是真的需求，但解法不是這個：模型啟動時載一次，換版由 <code>/reload</code>（或定時輪詢版本）處理。A 換模型只會讓推論那幾毫秒變快，占大頭的載入成本一點都沒少；B 多開 worker 只是讓更多份重複的昂貴工作平行做，每台還各自吃一份記憶體；D 序列化在這裡是幾百微秒等級的事，不可能造成 300 ms。</p></div>
    </div>

    <div class="quiz-q" data-answer="A">
      <p class="quiz-tag">Q4 <span class="qtype">情境題</span></p>
      <h3>晉升流程剛把 <span class="kbd">champion</span> 從 v2 移到 v3，Registry 查起來確實是 v3。但線上服務的 <span class="kbd">/health</span> 還是回 <span class="kbd">"model_version": 2</span>，預測值也沒變。你該怎麼處理？</h3>
      <div class="quiz-opts">
        <button type="button" class="quiz-opt" data-k="A">A. 這是預期行為：已載入的模型物件不會自己更新——打 <code>POST /reload</code>（或重啟服務），再確認 <code>/health</code> 變成 v3</button>
        <button type="button" class="quiz-opt" data-k="B">B. alias 沒寫進去，重跑一次 <code>set_registered_model_alias</code> 並清掉 MLflow 的快取</button>
        <button type="button" class="quiz-opt" data-k="C">C. 把 <code>load_model</code> 移進 <code>/predict</code>，這樣每次請求都保證是最新版</button>
        <button type="button" class="quiz-opt" data-k="D">D. 刪掉 v2 這個版本，服務找不到舊模型就會自動改載 v3</button>
      </div>
      <div class="quiz-fb" aria-live="polite"><p>「alias 一行切換」講的是<b>下一次載入</b>會拿到誰；跑著的行程裡是一個早就載好的物件，資料庫改一列不會讓它變身。所以換版流程是兩步：移 alias、再讓服務重載（主動打 <code>/reload</code>、背景輪詢版本、或重啟）——而 <code>/health</code> 回版本號正是為了讓你能確認第二步做完了。B 症狀不符，Registry 已經查到是 v3；C 是把換版問題丟給每一筆請求付錢，延遲會變 8–10 倍；D 很危險：刪版本破壞了可回滾性，而且服務手上那個物件不會因此改變，只會讓你連回滾的路都沒了。</p></div>
    </div>

    <div class="quiz-q" data-answer="D">
      <p class="quiz-tag">Q5 <span class="qtype">情境題</span></p>
      <h3>模型明天要上線。你只有半小時做部署前檢查，想用最少的步驟涵蓋最多的失敗模式。最有效的一組是？</h3>
      <div class="quiz-opts">
        <button type="button" class="quiz-opt" data-k="A">A. 打開 <code>MLmodel</code> 檔確認 flavor 與套件版本，再看一次 <code>requirements.txt</code></button>
        <button type="button" class="quiz-opt" data-k="B">B. 直接小流量上線觀察半小時，有問題再回滾</button>
        <button type="button" class="quiz-opt" data-k="C">C. 把整份 test set 重跑一次確認 AUC 跟訓練時記錄的一致</button>
        <button type="button" class="quiz-opt" data-k="D">D. 用模型自帶的 <code>serving_input_example.json</code> 跑 <code>validate_serving_input</code>，再拿同一份 payload 打一次真的起來的服務，最後跟批次算的機率對答案</button>
      </div>
      <div class="quiz-fb" aria-live="polite"><p>這三步剛好覆蓋三層不同的失敗：<code>validate_serving_input</code> 驗「反序列化＋schema＋模型」這條路（不用起伺服器，最快）；打真的服務多驗了 HTTP 與 JSON 序列化那一層；跟批次結果對答案則抓「線上／離線前處理不同步」——那是機率靜靜算錯、卻沒有任何錯誤訊息的一種故障。而且測資不用自己編，<code>input_example</code> 已經幫你生成現成的 payload。A 是讀檔案，讀對了也不代表跑得起來；B 把驗證成本轉嫁給真實客戶，而且流失機率算錯不會噴錯，小流量觀察半小時多半看不出來；C 驗的是模型品質（訓練時就驗過了），跟「能不能被服務起來」是兩件事。</p></div>
    </div>

    <div class="quiz-score" data-score></div>
  </div>
</section>

<div class="endnav">
  <a href="/model-monitoring/">
    <span class="tag">下一課</span>
    <b>模型監控：資料漂移、預測漂移與什麼時候該重訓 →</b>
  </a>
  <a href="/mlops/">
    <span class="tag">主題</span>
    <b>‹ 回「MLOps 自動化技術」課程列表</b>
  </a>
</div>
'''

SCRIPT = r"""
/* ═══ hero 互動：/invocations 請求模擬器 ═══
   狀態碼、回應 JSON、錯誤原文全部來自 notebook 與 _spikes/spike_model_serving_errors.py 的實測輸出
   （MLflow 3.15.2，churn-clf@champion＝RandomForest depth 8，pyfunc_predict_fn="predict_proba"）。 */
(function () {
  const OK = '{"predictions": [[0.2540043554069071, 0.7459956445930929],\n                 [0.9286023928020734, 0.07139760719792652]]}';
  const REQ = {
    split:
      'POST /invocations\n{"dataframe_split": {\n   "columns": ["f0", "f1", ..., "f11"],\n   "data": [[-0.4894, 0.0410, ...],\n            [-1.0730, 1.3642, ...]]\n}}',
    records:
      'POST /invocations\n{"dataframe_records": [\n   {"f0": -0.4894, "f1": 0.0410, ..., "f11": 0.4817},\n   {"f0": -1.0730, "f1": 1.3642, ..., "f11": -0.5279}\n]}',
    instances:
      'POST /invocations\n{"instances": [\n   [-0.4894, 0.0410, ..., 0.4817],\n   [-1.0730, 1.3642, ..., -0.5279]\n]}',
    missing:
      'POST /invocations\n{"dataframe_records": [\n   {"f0": -0.4894, ..., "f10": 1.4862}     // 少了 f11\n]}',
    raw:
      'POST /invocations\n[\n   {"f0": -0.4894, "f1": 0.0410, ..., "f11": 0.4817}\n]                                        // 沒有信封',
  };
  const RES = {
    split: [200, OK],
    records: [200, OK],
    instances: [400, '{"error_code": "INVALID_PARAMETER_VALUE", "message": "Failed to predict data\n \'[[-0.48941625  0.04104379 ... 0.48166258]]\'. \\nError: Failed to enforce schema of\n data \'[[...]]\' with schema \'[\'f0\': double (required), \'f1\': double (required),\n ... \'f11\': double (required)]\'"}'],
    missing: [400, '{"error_code": "INVALID_PARAMETER_VALUE", "message": "Failed to predict data ...\n \\nError: Failed to enforce schema of data ... with schema \'[\'f0\': double (required),\n ... \'f11\': double (required)]\'. Error: Model is missing inputs [\'f11\'].",\n "sqlstate": "KAM01", "error_class": "SCHEMA_ENFORCEMENT_FAILED"}'],
    raw: [400, '{"error_code": "BAD_REQUEST", "message": "Invalid input. The input must be a JSON\n dictionary with exactly one of the input fields {\'dataframe_split\', \'inputs\',\n \'dataframe_records\', \'instances\'}. Received a list.", "sqlstate": "KAM00",\n "error_class": "INVALID_PARAMETER_VALUE"}'],
  };
  const EP = {
    ping: { req: "GET /ping", code: 200, body: '（空的——只有一個換行）\n\n健康檢查只看狀態碼，別去解析 body。' },
    version: { req: "GET /version", code: 200, body: '3.15.2\n\nMLflow 自己的版本，不是模型版本；\n模型版本要自己做一個 /health 回。' },
  };
  const FAST = "14–36 ms", SLOW = "120–310 ms";

  const demo = document.getElementById("sv-demo");
  const fmts = document.getElementById("sv-fmts");
  const req = document.getElementById("sv-req"), res = document.getElementById("sv-res");
  const stat = document.getElementById("sv-stat"), slow = document.getElementById("sv-slow");
  const bars = demo.querySelectorAll(".bar");
  let ep = "inv", fmt = "split";

  function render() {
    fmts.classList.toggle("dim", ep !== "inv");
    let code, body;
    if (ep === "inv") { req.textContent = REQ[fmt]; [code, body] = RES[fmt]; }
    else { req.textContent = EP[ep].req; code = EP[ep].code; body = EP[ep].body; }
    res.textContent = body;
    const ms = slow.checked ? SLOW : FAST;
    stat.className = "stat " + (code === 200 ? "ok" : "bad");
    stat.innerHTML = `<span class="code">HTTP ${code}</span><span class="ms">約 ${ms}</span>`;
    bars[0].classList.toggle("now", !slow.checked);
    bars[1].classList.toggle("now", slow.checked);
  }
  demo.querySelectorAll("[data-ep]").forEach((b) =>
    b.addEventListener("click", () => {
      ep = b.dataset.ep;
      demo.querySelectorAll("[data-ep]").forEach((x) => x.classList.toggle("on", x === b));
      render();
    })
  );
  demo.querySelectorAll("[data-fmt]").forEach((b) =>
    b.addEventListener("click", () => {
      fmt = b.dataset.fmt;
      demo.querySelectorAll("[data-fmt]").forEach((x) => x.classList.toggle("on", x === b));
      render();
    })
  );
  slow.addEventListener("change", render);
  render();
})();
"""

PANEL_STEPS = """
        <li>登入 molab（GitHub / Google）</li>
        <li>開啟課程 notebook，<b>Fork 成自己的副本</b>即可編輯</li>
        <li>從第一格往下全部執行（首次安裝套件約 1–2 分鐘）——<b>免費 CPU 環境即可</b>，不需要 GPU；伺服器都起在 notebook 自己的機器上，不對外</li>
"""
