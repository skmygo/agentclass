"""課程頁內容區（純常數）。改完跑：python3 .claude/skills/make-lesson/scripts/page-fill.py content/mlops/mlops-pipeline
build.sh 不會部署這個檔；它是 index.html 內容區的正本。"""

TITLE = "Dagster × MLflow：一條會自己訓練、評估、把關、上線的管線"
DESCRIPTION = "MLOps 系列壓軸：把 MLflow 追蹤與註冊、Dagster 資產與自動化接成一條線——訓練資產記進 MLflow、evaluate 一行評估、blocking 資產檢查當品質閘門、通過才移動 champion alias，還能從線上模型三跳查回是哪一次執行訓的。molab 免費 CPU 環境全程實作。"
NB = "https://molab.marimo.io/github/skmygo/agentclass/blob/main/content/mlops/mlops-pipeline/mlops-pipeline_ext.py"

STYLE = r"""
  /* 語義色：藍＝資料、橘＝模型、綠＝上線／通過、紅＝被閘門擋下 */
  :root { --c1: #4C72B0; --c2: #DD8452; --c3: #55A868; --cut: #C44E52; }
  a.golab { text-decoration: none; display: inline-flex; align-items: center; gap: 8px; }

  /* ── hero：管線重播機 ── */
  #pl-demo .ctl { display: flex; gap: 7px; flex-wrap: wrap; align-items: center; margin-bottom: 12px; }
  #pl-demo .ctl .hint { font-size: 12.5px; color: var(--ink-soft); flex: 1 1 100%; }
  #pl-demo .ctl button { font-family: var(--mono); font-size: 12.5px; padding: 6px 11px; border-radius: 8px;
    border: 1.5px solid var(--grid); background: #fff; color: var(--ink); cursor: pointer; transition: border-color .15s, background .15s; }
  #pl-demo .ctl button:hover { border-color: var(--ink); background: var(--chip-bg); }
  #pl-demo .ctl button.on { border-color: var(--ink); background: var(--ink); color: #fff; }
  #pl-demo .board { display: grid; grid-template-columns: minmax(0, 1.55fr) minmax(0, 1fr); gap: 12px; align-items: start; }
  #pl-demo .step { border: 1.5px solid var(--grid); border-left-width: 4px; border-radius: 9px; padding: 6px 10px;
    margin-bottom: 5px; background: #fff; opacity: .42; transition: opacity .18s, border-color .18s, background .18s; }
  #pl-demo .step b { font-family: var(--mono); font-size: 12.5px; display: block; }
  #pl-demo .step .mt { font-family: var(--mono); font-size: 11px; color: var(--ink-soft); line-height: 1.5; }
  #pl-demo .step.gate { border-style: dashed; border-left-style: solid; }
  #pl-demo .step.on { opacity: 1; }
  #pl-demo .step.data.on { border-left-color: var(--c1); } #pl-demo .step.data.on b { color: var(--c1); }
  #pl-demo .step.model.on { border-left-color: var(--c2); } #pl-demo .step.model.on b { color: var(--c2); }
  #pl-demo .step.deploy.on { border-left-color: var(--c3); background: rgba(85,168,104,.10); }
  #pl-demo .step.deploy.on b { color: var(--c3); }
  #pl-demo .step.pass.on { border-color: var(--c3); border-left-color: var(--c3); background: rgba(85,168,104,.10); }
  #pl-demo .step.pass.on b { color: var(--c3); }
  #pl-demo .step.fail.on { border-color: var(--cut); border-left-color: var(--cut); background: rgba(196,78,82,.10); }
  #pl-demo .step.fail.on b { color: var(--cut); }
  #pl-demo .step.skip.on { opacity: .85; border-style: dashed; border-left-color: var(--grid); background: repeating-linear-gradient(135deg, #fff, #fff 6px, var(--chip-bg) 6px, var(--chip-bg) 12px); }
  #pl-demo .step.skip.on b { color: var(--ink-soft); text-decoration: line-through; }
  #pl-demo .reg { border: 1.5px solid var(--grid); border-radius: 11px; padding: 9px 11px; background: var(--chip-bg); }
  #pl-demo .reg .rt { font-size: 11px; letter-spacing: .05em; color: var(--ink-soft); font-weight: 800; }
  #pl-demo .reg .rn { font-family: var(--mono); font-size: 12.5px; font-weight: 800; margin-bottom: 6px; }
  #pl-demo .ver { background: #fff; border: 1.5px solid var(--grid); border-radius: 8px; padding: 5px 8px; margin-bottom: 5px;
    font-family: var(--mono); font-size: 11.5px; position: relative; }
  #pl-demo .ver.live { border-color: var(--c3); box-shadow: 0 0 0 2.5px rgba(85,168,104,.16); }
  #pl-demo .ver .al { color: var(--c3); font-weight: 800; }
  #pl-demo .reg .empty { font-family: var(--mono); font-size: 11.5px; color: var(--ink-soft); }
  #pl-demo .reg .svc { margin-top: 7px; font-family: var(--mono); font-size: 10.5px; color: var(--ink-soft); line-height: 1.55; overflow-wrap: anywhere; }
  #pl-demo .verdict { margin-top: 10px; border-radius: 9px; padding: 8px 11px; font-size: 13px; font-weight: 800; }
  #pl-demo .verdict.ok { background: rgba(85,168,104,.14); color: #2F6B45; }
  #pl-demo .verdict.no { background: rgba(196,78,82,.13); color: #8E2F32; }
  #pl-demo .log { margin-top: 8px; font-family: var(--mono); font-size: 11.5px; color: var(--ink-soft);
    line-height: 1.75; white-space: pre-wrap; overflow-wrap: anywhere; min-height: 3.4em; }
  #pl-demo .log .ok { color: var(--c3); font-weight: 800; }
  #pl-demo .log .no { color: var(--cut); font-weight: 800; }
  @media (max-width: 640px) { #pl-demo .board { grid-template-columns: 1fr; } }

  table.cmp { width: 100%; border-collapse: collapse; font-size: 13.5px; margin: 14px 0; }
  table.cmp th, table.cmp td { border-bottom: 1px solid var(--grid); padding: 8px 10px; text-align: left; vertical-align: top; }
  table.cmp th { font-size: 12px; letter-spacing: .04em; color: var(--ink-soft); }
  table.cmp td.ok { color: var(--c3); font-weight: 800; } table.cmp td.no { color: var(--cut); font-weight: 800; }
  .kbd { font-family: var(--mono); background: var(--chip-bg); padding: 1px 6px; border-radius: 5px; font-size: 13px; }
  .flow { font-family: var(--mono); font-size: 12px; line-height: 1.9; background: var(--chip-bg); border-radius: 10px;
    padding: 10px 12px; margin: 14px 0; overflow-x: auto; white-space: pre; }
"""

WRAP = r"""
<section id="hero">
  <span class="eyebrow">CAPSTONE · DAGSTER × MLFLOW · 05</span>
  <h1>Dagster × MLflow：<br>一條會自己訓練、評估、把關、上線的管線</h1>
  <p style="margin-top:18px">
    前四課你各拿到一個零件：訓練有紀錄、最好的版本上得了線、資料查得到來歷、有人會按執行。
    這一課把它們焊成一條線，並且加上最重要的那個零件——<b>一道會說「不」的閘門</b>。
    下面是這條線在 notebook 裡真的跑過的四次，按一顆按鈕看它走一遍：
  </p>

  <div class="hero-demo" id="pl-demo">
    <div class="ctl">
      <span class="hint">四次執行、同一份程式碼，改的只有設定</span>
      <button type="button" data-run="1">run 1 · rf depth 8</button>
      <button type="button" data-run="2">run 2 · logreg</button>
      <button type="button" data-run="3">run 3 · rf depth 16</button>
      <button type="button" data-run="4">run 4 · 資料漂移</button>
    </div>
    <div class="board">
      <div class="map" id="pl-map"></div>
      <div class="reg" id="pl-reg"></div>
    </div>
    <div class="verdict" id="pl-verdict"></div>
    <div class="log" id="pl-log"></div>
  </div>

  <p class="note">
    每一個數字都是 notebook 的實測結果（同一組亂數種子）：AUC 0.9684 → 0.9508 → 0.9698 → 0.8641，
    其中兩次被閘門擋下、沒有任何東西上線。
  </p>
</section>

<section id="s1">
  <span class="eyebrow">01 · RESOURCE</span>
  <h2>先把「MLflow 在哪」變成可以注入的設定</h2>
  <div class="codeblock">class MlflowResource(dg.ConfigurableResource):
    tracking_uri: str
    experiment: str

    def setup(self) -> None:
        mlflow.set_tracking_uri(self.tracking_uri)                       # 帳本記在哪
        if mlflow.get_experiment_by_name(self.experiment) is None:
            mlflow.create_experiment(self.experiment, artifact_location=...)
        mlflow.set_experiment(self.experiment)                           # run 歸到哪個實驗

@dg.asset
def trained_model(context, config: TrainConfig, mlflow_res: MlflowResource, train_test: dict) -> str:
    mlflow_res.setup()          # ← 這一行決定這次訓練被記到哪裡
    ...</div>
  <p>
    第 4 課的 <b>resource</b> 在這裡派上真正的用場。MLflow 的 tracking server 是典型的「環境」：
    筆電上是一個 SQLite 檔、正式環境是內網的伺服器、CI 上又是另一個。
    把它宣告成 <span class="kbd">ConfigurableResource</span>（一個 Pydantic 模型，欄位型別會被檢查），
    資產只要在參數列寫 <span class="kbd">mlflow_res: MlflowResource</span> 就會被注入——
    換環境只改一行 <span class="kbd">Definitions</span>，用得到 MLflow 的那幾個資產與檢查，程式一個字都不用動。
  </p>
  <p>
    <b>忘了 <span class="kbd">setup()</span> 會怎樣？</b>實測的答案很嚇人：Dagster 回報
    <span class="kbd">success = True</span>、沒有任何錯誤，但管線的 tracking 裡<b>一個 run 都沒有</b>，
    工作目錄多出一個誰也不會去看的 <span class="kbd">mlflow.db</span>——訓練確實跑了，只是記到了別的地方。
    這種「安靜地做錯」正是 MLOps 最貴的一類 bug。
  </p>
  <a class="golab" href="__NB__" target="_blank" rel="noopener">到 notebook 的 1️⃣ 節：把 MLflow 做成 resource</a>
</section>

<section id="s2">
  <span class="eyebrow">02 · 資產鏈</span>
  <h2>訓練資產：兩邊互相記下對方的 id</h2>
  <div class="codeblock">with mlflow.start_run(run_name=f"dagster-{context.run_id[:8]}") as run:
    mlflow.log_params({"model": ..., "max_depth": ..., "drift": ...,
                       "dagster_run": context.run_id})            # MLflow 記住 Dagster
    clf.fit(X, y)
    info = mlflow.sklearn.log_model(clf, name="churn_model",
                                    signature=infer_signature(X, clf.predict_proba(X)[:, 1]),
                                    input_example=X.head(3))
    mlflow.set_tag("dagster.asset", "trained_model")

context.add_output_metadata({"mlflow_run": run.info.run_id,       # Dagster 記住 MLflow
                             "model_uri": info.model_uri})
return info.model_uri                                             # 資產的內容是地址，不是模型物件</div>
  <p>
    這一格是整條管線的縫合處：第 1 課的 <span class="kbd">start_run</span> 疊在第 3 課的
    <span class="kbd">@asset</span> 上。真正的關鍵是<b>雙向</b>——只記單向的話，總有一天你會站在錯的那一邊：
    有人看到線上模型怪怪的，是從 Registry 往回查；資料工程師發現某天的資料有問題，是從 Dagster 往前查。
  </p>
  <p>
    資產回傳的是一個字串 <span class="kbd">models:/m-…</span>，不是模型物件。模型檔案已經在 MLflow 那裡了，
    管線裡傳的是它的地址；下游要用就自己載——這也讓「資產」在真實部署裡不必扛著幾百 MB 的東西跑。
  </p>
  <a class="golab" href="__NB__" target="_blank" rel="noopener">到 notebook 的 2️⃣–3️⃣ 節：資料資產與訓練資產</a>
</section>

<section id="s3">
  <span class="eyebrow">03 · 評估</span>
  <h2>一行 evaluate，指標同時進兩本帳</h2>
  <div class="codeblock">with mlflow.start_run(run_name="evaluate"):
    res = mlflow.models.evaluate(trained_model, test_df, targets="label", model_type="classifier")

metrics = {k: float(v) for k, v in res.metrics.items()
           if k in ("roc_auc", "accuracy_score", "f1_score", "recall_score", "precision_score")}
context.add_output_metadata({k: dg.MetadataValue.float(v) for k, v in metrics.items()})
return metrics</div>
  <p>
    第 2 課的 <span class="kbd">evaluate</span> 一行產出 8 個指標與 5 張圖，全部記進當前 run。這裡多做一件事：
    把其中幾個<b>也</b>掛到 Dagster 的中繼資料上。重複記不是浪費——兩本帳的讀者不同：
    MLflow 的指標是拿來<b>比較實驗</b>的（20 個 run 排序找最好的那個），
    Dagster 的中繼資料是拿來<b>看管線</b>的（在資產圖上一眼看到這份指標上次算出來多少，還會畫出歷次趨勢）。
  </p>
  <p>
    這個資產同時吃 <span class="kbd">trained_model</span>（一個 URI 字串）與 <span class="kbd">train_test</span>（切好的資料），
    參數名各自對到上游——評估用的是 test 那一半，訓練資產從來沒看過它。
  </p>
  <a class="golab" href="__NB__" target="_blank" rel="noopener">到 notebook 的 4️⃣ 節：評估資產</a>
</section>

<section id="s4">
  <span class="eyebrow">04 · 品質閘</span>
  <h2>為什麼閘門是 asset check，不是一個 if</h2>
  <div class="codeblock">@dg.asset_check(asset=model_metrics, blocking=True,
                description="品質閘：AUC 必須 ≥ 0.95 而且不輸目前 champion")
def quality_gate(mlflow_res: MlflowResource, model_metrics: dict) -> dg.AssetCheckResult:
    mlflow_res.setup()
    try:
        champ = MlflowClient().get_model_version_by_alias("churn-clf", "champion")
        champion_auc = mlflow.get_run(champ.run_id).data.metrics.get("eval_auc", 0.0)
    except MlflowException:                     # 第一次執行：Registered Model ... not found
        champion_auc = 0.0
    auc = model_metrics["roc_auc"]
    return dg.AssetCheckResult(passed=bool(auc >= 0.95 and auc >= champion_auc),
                               severity=dg.AssetCheckSeverity.ERROR,
                               metadata={"auc": auc, "champion_auc": champion_auc, "min_auc": 0.95})</div>
  <p>
    兩道條件缺一不可：<b>絕對門檻</b>（不管以前多爛，低於 0.95 就是不准上線）
    ＋<b>相對門檻</b>（不能比現在線上那版還差）。你當然可以把這段寫成上線資產開頭的一個
    <span class="kbd">if</span>，但那樣會失去四件事：
  </p>
  <table class="cmp">
    <tr><th></th><th>寫成 if</th><th>寫成 blocking asset check</th></tr>
    <tr><td>這次過了沒</td><td class="no">埋在日誌裡，要翻</td><td class="ok">一筆檢查結果進帳本，紅叉綠勾</td></tr>
    <tr><td>為什麼沒過</td><td class="no">要自己 print</td><td class="ok">metadata 帶著 auc／champion_auc／門檻，永久保存</td></tr>
    <tr><td>下游會不會跑</td><td class="no">每個下游都要再判一次</td><td class="ok">blocking 直接擋住全部下游</td></tr>
    <tr><td>這次執行算成功嗎</td><td class="no">算成功（你自己 return 了）</td><td class="ok">run 標記為失敗，該叫的人會被叫</td></tr>
  </table>
  <p>
    最後一項最關鍵：閘門擋下來時，這次執行<b>必須</b>是失敗的。如果它算成功，你的監控就永遠不會響——
    一條「安靜地什麼都沒做」的管線，比一條會壞掉的管線危險得多。
    另外記得 <span class="kbd">dg.materialize()</span> <b>沒有</b> <span class="kbd">asset_checks=</span> 參數：
    檢查要跟資產放同一個清單，忘了放它就靜靜地不執行，而執行結果照樣顯示成功。
  </p>
  <a class="golab" href="__NB__" target="_blank" rel="noopener">到 notebook 的 5️⃣ 節：品質閘與 blocking 的效果</a>
</section>

<section id="s5">
  <span class="eyebrow">05 · 上線</span>
  <h2>放行之後：註冊、補記、移動 alias</h2>
  <div class="codeblock">mv = mlflow.register_model(trained_model, MODEL_NAME)                      # 1. 註冊成新版本
src_run = client.get_model_version(MODEL_NAME, mv.version).run_id
client.log_metric(src_run, "eval_auc", model_metrics["roc_auc"])          # 2. 補記評估分數
client.set_registered_model_alias(MODEL_NAME, "champion", mv.version)     # 3. 移動 alias ＝ 上線
client.set_model_version_tag(MODEL_NAME, mv.version, "dagster_run", context.run_id)</div>
  <p>
    第 3 步之後，服務端那行 <span class="kbd">load_model("models:/churn-clf@champion")</span> 一個字都不用改，
    下次載入就是新版。這就是第 2 課 alias 的用途，只是現在按下它的不是你的手，是管線。
  </p>
  <p>
    <b>第 2 步是最容易漏掉的一步。</b>評估是在另一個名叫 <span class="kbd">evaluate</span> 的 run 裡做的，
    而下一次執行時，閘門要問的是「現任 champion 當初考幾分」——它讀的是 champion 版本指向的<b>訓練 run</b>。
    沒把 <span class="kbd">eval_auc</span> 補記上去，閘門讀到的永遠是實測的
    <span class="kbd">metrics = {} → .get('eval_auc', 0.0) = 0.0</span>，
    相對門檻形同虛設：任何 AUC ≥ 0.95 的模型都能把 champion 換掉，包含比現任差的那些。
    不報錯、不噴紅字，只是品質閘默默失效。
  </p>
  <a class="golab" href="__NB__" target="_blank" rel="noopener">到 notebook 的 6️⃣ 節：上線資產</a>
</section>

<section id="s6">
  <span class="eyebrow">06 · 四次執行</span>
  <h2>同一份程式碼，四種劇情</h2>
  <table class="cmp">
    <tr><th>執行</th><th>設定</th><th>AUC</th><th>當時 champion</th><th>結果</th></tr>
    <tr><td>run 1</td><td>RandomForest depth 8</td><td>0.9684</td><td>—（Registry 空的）</td><td class="ok">通過 → 成為 v1</td></tr>
    <tr><td>run 2</td><td>LogisticRegression</td><td>0.9508</td><td>0.9684</td><td class="no">過了 0.95，但輸給現任 → 擋</td></tr>
    <tr><td>run 3</td><td>RandomForest depth 16</td><td>0.9698</td><td>0.9684</td><td class="ok">通過 → 晉升 v2</td></tr>
    <tr><td>run 4</td><td>depth 16 ＋ drift 1.5</td><td>0.8641</td><td>0.9698</td><td class="no">低於絕對門檻 → 擋</td></tr>
  </table>
  <p>
    被擋的兩次，<span class="kbd">registered_champion</span> 從實體化清單裡整個消失，執行結果是<b>失敗</b>——
    這正是 <span class="kbd">blocking=True</span> 在做的事。
  </p>
  <p>
    最值得停下來想的是 run 4：它跟 run 3 的模型設定<b>一模一樣</b>，同樣的森林、同樣的深度、同樣的種子。
    程式碼沒動、參數沒動，AUC 卻掉了 0.10。變的只有資料。真實世界最常見的模型事故就是這樣：
    沒有人改壞任何東西，是世界變了。閘門的價值不在於它擋下的那些模型，而在於你不必再靠運氣。
  </p>
  <a class="golab" href="__NB__" target="_blank" rel="noopener">到 notebook 的 7️⃣ 節：連跑四次，看閘門開關</a>
</section>

<section id="s7">
  <span class="eyebrow">07 · 追溯</span>
  <h2>「現在線上那個模型，是怎麼來的？」</h2>
  <div class="flow">Registry @champion ──▶ MLflow run ──▶ dagster_run 參數 ──▶ Dagster 那次執行
                                                                │
       materialization 的 mlflow_run 中繼資料 ◀─────────────────┘</div>
  <div class="codeblock">champ = client.get_model_version_by_alias("churn-clf", "champion")     # v2
run   = mlflow.get_run(champ.run_id)                                  # 參數、指標、tag
dagster_run_id = run.data.params["dagster_run"]                       # → Dagster 那次執行
instance.get_run_by_id(dagster_run_id).status                         # SUCCESS

records = instance.fetch_materializations(dg.AssetKey("trained_model"), limit=10).records
match   = next(r for r in records if r.run_id == dagster_run_id)
match.asset_materialization.metadata["mlflow_run"].value == champ.run_id   # True</div>
  <p>
    半夜有人問「線上跑的模型是誰、什麼時候、用什麼資料訓的」，這題就是三跳到底的查詢：
    從 alias 找到版本、從版本找到 MLflow run、從 run 的參數找到 Dagster 的執行 id；
    反過來也走得通——用那個執行 id 去 Dagster 的帳本裡撈當時的中繼資料，會拿到同一個 MLflow run。
    實測兩個方向指到同一個 run：<span class="kbd">True</span>。
  </p>
  <p>
    在正式環境裡這兩跳都是 UI 上的一個連結。自己用 API 走一遍的意義是：你知道那個連結底下是什麼，
    也知道當初少記一邊的 id，今天就會斷在哪裡。
  </p>
  <a class="golab" href="__NB__" target="_blank" rel="noopener">到 notebook 的 8️⃣ 節：兩個方向各查一次</a>
</section>

<section id="s8">
  <span class="eyebrow">08 · 誰來按執行</span>
  <h2>收尾：把這條線交給排程、感測器與自動化條件</h2>
  <div class="codeblock">train_job = dg.define_asset_job("nightly_train", selection=dg.AssetSelection.all())

nightly = dg.ScheduleDefinition(name="nightly_train_schedule", job=train_job,
                                cron_schedule="0 3 * * *", execution_timezone="Asia/Taipei")

@dg.sensor(name="new_data_sensor", job=train_job, minimum_interval_seconds=30)
def new_data_sensor(context):                       # 收件匣有新檔案就重訓，cursor 記住看過幾個
    seen = int(context.cursor) if context.cursor else 0
    files = sorted(INBOX.glob("*.csv"))
    if len(files) > seen:
        context.update_cursor(str(len(files)))
        yield dg.RunRequest(run_key=f"batch-{len(files)}")
    else:
        yield dg.SkipReason(f"沒有新資料（已處理 {seen} 批）")

@dg.asset(automation_condition=dg.AutomationCondition.eager())   # 上游一更新，我自己就該重算
def data_profile(churn_data: pd.DataFrame) -> dict: ...          # 有新資料就重出資料剖析
@dg.asset(automation_condition=dg.AutomationCondition.eager())
def champion_scorecard(registered_champion: str) -> str: ...     # champion 換人就重出成績單

production_defs = dg.Definitions(assets=[...], asset_checks=[quality_gate], resources=RESOURCES,
                                 jobs=[train_job], schedules=[nightly], sensors=[new_data_sensor])</div>
  <p>
    第 4 課的三種零件，回答的是同一個問題的三種版本：<b>誰來按？</b>
    排程是「時間到了」、感測器是「有事情發生了」、自動化條件是「我的上游更新了，我自己該動了」。
    在 notebook 裡用 <span class="kbd">evaluate_tick()</span> 直接問它們「假設那個時刻到了，你會發什麼單子」——
    不必啟動任何背景服務就看得到答案：排程的 tick 送出 1 張 RunRequest；
    感測器三個 tick 依序是「沒有新資料」→「發出 batch-1」→「不重複觸發」。
  </p>
  <p>
    自動化條件的實測結果更值得看。在一本乾淨的帳本上跑一次會被閘門擋下的管線，然後連問三個 tick：
    第一個 tick 是 <b>0</b>（評估器要先有基準，之後才知道什麼是新的——正式環境的 daemon 一直在跑、基準早就有了）；
    第二個 tick 只有 <span class="kbd">data_profile</span> 舉手，因為它的上游 <span class="kbd">churn_data</span> 剛更新過；
    而 <span class="kbd">champion_scorecard</span> 一動也不動——它的上游被閘門擋住、這次根本沒有產出。
    <b>閘門擋下的不只是這一次執行的下游，連自動化都跟著停在那裡</b>，這是品質閘最容易被低估的一面。
  </p>
  <p>
    最後全部收進一份 <span class="kbd">Definitions</span>：7 個資產、1 個檢查、1 份資源、1 個 job、1 個排程、1 個感測器。
    把它存成專案裡的 <span class="kbd">definitions.py</span>，然後 <span class="kbd">dagster dev</span>——
    瀏覽器打開就是資產圖、實體化歷史、檢查的紅叉綠勾、排程與感測器的開關。到這裡，這條線就不需要你了。
  </p>
  <a class="golab" href="__NB__" target="_blank" rel="noopener">到 notebook 的 9️⃣ 節：job、排程、感測器、Definitions</a>
</section>

<section id="s9">
  <span class="eyebrow">09 · 實戰</span>
  <h2>換你動手</h2>
  <div class="ex">
    <span class="lv">LEVEL 1</span>
    <p>把 <span class="kbd">MIN_AUC</span> 改成 <span class="kbd">0.97</span>、換一個乾淨的模型名字，再跑一次 rf depth 8（AUC 約 0.968）。
       它應該再也上不了線——確認 <span class="kbd">registered_champion</span> 從實體化清單裡消失了。門檻是一個決策，不是一個常識。</p>
  </div>
  <div class="ex">
    <span class="lv">LEVEL 2</span>
    <p>再加一道 blocking 檢查 <span class="kbd">recall_gate</span>（recall ≥ 0.9），跟品質閘掛在同一個資產上，
       用 LogisticRegression（recall 約 0.86）跑一次看它被哪一道擋下來。順便把其中一個檢查從清單裡拿掉再跑一次，
       體會「執行成功，但閘門根本沒跑」。</p>
  </div>
  <div class="ex">
    <span class="lv">LEVEL 3</span>
    <p>把 <span class="kbd">churn_data</span> 改成 <span class="kbd">DailyPartitionsDefinition</span> 的分割資產，讓每天只訓當天的資料，
       再用 <span class="kbd">build_schedule_from_partitioned_job</span> 產生排程。順便想一個沒有標準答案的問題：
       分割之後，每一片各自要跟誰比？</p>
  </div>
  <p style="font-size:13.5px;color:var(--ink-soft);margin-top:10px">卡住了？三題在 notebook 末節都有折疊解答與驗證方式——先自己做，再打開對照。</p>
</section>

<section id="quiz">
  <span class="eyebrow">10 · 驗收</span>
  <h2>情境測驗</h2>
  <p>離開前試試看：下面的情境都真的會遇到。每題選一個你認為的最佳做法，選了馬上看得到解釋。</p>
  <div data-quiz>

    <div class="quiz-q" data-answer="C">
      <p class="quiz-tag">Q1 <span class="qtype">情境題</span></p>
      <h3>你要在自動重訓管線裡加一道「AUC 不到 0.95 就不准上線」的規則。以下哪種做法最好？</h3>
      <div class="quiz-opts">
        <button type="button" class="quiz-opt" data-k="A">A. 在上線資產開頭寫 <code>if auc &lt; 0.95: return "skipped"</code>，這樣執行不會失敗，半夜不用叫人</button>
        <button type="button" class="quiz-opt" data-k="B">B. 訓練完先人工看一眼指標，確認沒問題再手動執行上線那一步</button>
        <button type="button" class="quiz-opt" data-k="C">C. 寫成 <code>@dg.asset_check(asset=model_metrics, blocking=True)</code>，把 auc 與門檻放進 metadata</button>
        <button type="button" class="quiz-opt" data-k="D">D. 在評估資產裡用 <code>raise ValueError("AUC too low")</code> 直接讓整條線炸掉</button>
      </div>
      <div class="quiz-fb" aria-live="polite"><p>blocking 的資產檢查一次給你四件事：判斷結果存成一筆可查詢的紀錄（UI 紅叉綠勾）、判斷依據留在 metadata 裡（auc／champion_auc／門檻）、下游<b>全部</b>自動不跑、而且整次執行標記為失敗——監控才會響。A 的致命傷正是「執行不會失敗」：一條安靜地什麼都沒做的管線，比一條會壞掉的管線危險得多。B 把人放回迴圈裡，規模一大就變成瓶頸，而且沒有紀錄。D 雖然會失敗，但錯誤混在例外堆疊裡、沒有結構化的判斷依據，而且評估資產本身會被標成失敗——它其實算對了，是模型不合格。</p></div>
    </div>

    <div class="quiz-q" data-answer="B">
      <p class="quiz-tag">Q2 <span class="qtype dx">錯誤診斷</span></p>
      <h3>管線跑了三個月都很正常，直到有人發現線上模型比上個月的還差。你去查閘門的中繼資料，看到每一次都長這樣。問題出在哪？</h3>
      <div class="codeblock">quality_gate  passed=True   {"auc": 0.9508, "champion_auc": 0.0, "min_auc": 0.95}
# 而 champion 那個版本的訓練 run：
mlflow.get_run(champ.run_id).data.metrics   # {}   → .get("eval_auc", 0.0) = 0.0</div>
      <div class="quiz-opts">
        <button type="button" class="quiz-opt" data-k="A">A. <code>get_model_version_by_alias</code> 抓錯版本了，應該改用 <code>search_model_versions</code> 自己找最新版</button>
        <button type="button" class="quiz-opt" data-k="B">B. 上線資產漏了 <code>client.log_metric(src_run, "eval_auc", ...)</code>：評估分數記在另一個 run 上，閘門讀訓練 run 永遠讀到 0.0，相對門檻等於沒有</button>
        <button type="button" class="quiz-opt" data-k="C">C. 閘門的 <code>try/except</code> 把例外吃掉了，應該讓它直接拋出來</button>
        <button type="button" class="quiz-opt" data-k="D">D. 門檻設太低，把 <code>min_auc</code> 調到 0.97 就不會有這個問題</button>
      </div>
      <div class="quiz-fb" aria-live="polite"><p><code>champion_auc</code> 一直是 <code>0.0</code> 就是證據：閘門讀的是 champion 版本指向的<b>訓練 run</b>，而評估是在另一個 run（<code>evaluate</code>）裡做的。上線時要用 <code>log_metric</code> 把 <code>eval_auc</code> 補記到訓練 run 上，下一次的閘門才比得到——漏了這一步，只剩絕對門檻，任何過 0.95 的模型都能把更好的 champion 換掉。A 症狀不符：alias 抓的版本是對的，是那個 run 上沒有指標；C 這裡的 try/except 是為了「第一次執行還沒有 champion」而存在的，拿掉只會讓第一次直接爆炸；D 只是把標準拉高，相對門檻依然失效——今天過 0.97 的爛模型照樣能換掉 0.99 的現任。</p></div>
    </div>

    <div class="quiz-q" data-answer="D">
      <p class="quiz-tag">Q3 <span class="qtype dx">錯誤診斷</span></p>
      <h3>同事把訓練資產搬進新專案，執行結果一切正常，但 MLflow 上什麼都沒有。以下是他的資產與執行結果。最可能的原因？</h3>
      <div class="codeblock">@dg.asset
def trained_model(context, mlflow_res: MlflowResource, train_test: dict) -> str:
    with mlflow.start_run(run_name="train") as run:      # 直接就開 run
        ...

# 執行結果
Dagster success = True                        # 沒有任何錯誤
管線的 tracking 裡有幾個 run： 0
工作目錄多出來的東西： ['mlflow.db']</div>
      <div class="quiz-opts">
        <button type="button" class="quiz-opt" data-k="A">A. <code>MlflowResource</code> 沒有被註冊進 <code>Definitions</code>，Dagster 會靜靜地傳 <code>None</code> 進來</button>
        <button type="button" class="quiz-opt" data-k="B">B. SQLite 檔案權限不足，MLflow 靜靜地退回記憶體模式</button>
        <button type="button" class="quiz-opt" data-k="C">C. <code>start_run</code> 沒有指定 <code>experiment_id</code>，run 掉進了 Default 實驗</button>
        <button type="button" class="quiz-opt" data-k="D">D. 資產裡少了 <code>mlflow_res.setup()</code>：注入了資源卻沒有套用，MLflow 用預設位置在工作目錄開了自己的資料庫</button>
      </div>
      <div class="quiz-fb" aria-live="polite"><p>資源被注入只代表「你拿到了設定」，套不套用是你的事——少了 <code>setup()</code>，<code>set_tracking_uri</code> 就沒被呼叫，MLflow 用預設位置在當下的工作目錄開了一個新的 <code>mlflow.db</code>，訓練確實跑了、也真的有記錄，只是記到沒人會看的地方。這是最典型的「安靜地做錯」：Dagster 顯示成功、不會有任何紅字。A 不成立，資源沒註冊會在<b>組圖時</b>就報 <code>DagsterInvalidDefinitionError: resource with key 'mlflow_res' ... was not provided</code>，根本不會執行到；B 是杜撰的行為，MLflow 寫不進去會直接拋例外；C 症狀不符——掉進 Default 實驗的話，run 還是會出現在同一個 tracking 裡，而不是在別的資料庫。</p></div>
    </div>

    <div class="quiz-q" data-answer="A">
      <p class="quiz-tag">Q4 <span class="qtype">情境題</span></p>
      <h3>每天凌晨的重訓連續三天被閘門擋下，AUC 從 0.97 掉到 0.86，而模型設定完全沒動過。線上還是上週那版 champion。你明天早上第一件該做的事是？</h3>
      <div class="quiz-opts">
        <button type="button" class="quiz-opt" data-k="A">A. 去查上游資料：比對這三天與上週訓練資料的分布，先確認是不是資料源頭變了</button>
        <button type="button" class="quiz-opt" data-k="B">B. 把 <code>min_auc</code> 降到 0.85，先讓管線恢復綠燈，再慢慢查</button>
        <button type="button" class="quiz-opt" data-k="C">C. 把閘門的 <code>blocking</code> 改成 <code>False</code>，讓新模型先上線，反正還有監控</button>
        <button type="button" class="quiz-opt" data-k="D">D. 換一個更複雜的模型（例如加深森林或改用梯度提升）把 AUC 拉回 0.95 以上</button>
      </div>
      <div class="quiz-fb" aria-live="polite"><p>設定沒變、分數掉了，變的只可能是資料——這正是課堂上 run 4 的情境（同一組參數，只加了 drift，AUC 就從 0.9698 掉到 0.8641）。閘門已經幫你做完該做的事：擋下爛模型、保住線上那版、而且把「這次考幾分」留在紀錄裡；接下來要修的是資料，不是門檻。B 和 C 都是把警報關掉——問題還在，只是你看不到了，而且爛模型會直接上線。D 更糟：在不知道原因的情況下換模型，等於用更複雜的東西去硬記已經壞掉的資料，上線後會以更難察覺的方式失敗。</p></div>
    </div>

    <div class="quiz-q" data-answer="B">
      <p class="quiz-tag">Q5 <span class="qtype">情境題</span></p>
      <h3>上游團隊每天不定時丟 1～5 批新資料進物件儲存，你希望「有新資料就重訓一次、同一批不要重跑」。最合適的觸發方式是？</h3>
      <div class="quiz-opts">
        <button type="button" class="quiz-opt" data-k="A">A. <code>ScheduleDefinition</code> 設成每 10 分鐘跑一次，反正跑不用錢</button>
        <button type="button" class="quiz-opt" data-k="B">B. <code>@dg.sensor</code> 盯著資料位置，用 <code>cursor</code> 記住看過哪些批次，有新的才發 <code>RunRequest</code>（帶 <code>run_key</code>）</button>
        <button type="button" class="quiz-opt" data-k="C">C. 請上游團隊在丟完檔案後打一支 API 通知你，你再手動執行</button>
        <button type="button" class="quiz-opt" data-k="D">D. 在訓練資產開頭自己寫一個 <code>while True</code> 迴圈輪詢資料位置</button>
      </div>
      <div class="quiz-fb" aria-live="polite"><p>「有事情發生才跑」正是感測器的定義，而 <code>cursor</code> 是它的記憶：記住上次看到哪一批，下一 tick 只處理新的；<code>run_key</code> 再幫你去重，同一批資料不會開出第二次執行。A 每 10 分鐘無條件重訓，一天 144 次訓練＋144 次評估，浪費算力也把 MLflow 灌滿沒人看的 run，而且新資料最壞還是要等 10 分鐘。C 把自動化退回人工，你等於用一支 API 換來一個待辦事項。D 讓資產永遠不會結束，執行卡住、失敗也無法重試——輪詢是感測器的工作，不是資產的。</p></div>
    </div>

    <div class="quiz-score" data-score></div>
  </div>
</section>

<div class="endnav">
  <a href="/mlops/">
    <span class="tag">主題</span>
    <b>‹ 回「MLOps 自動化技術」課程列表</b>
  </a>
  <a href="/mlflow-tracking/">
    <span class="tag">從頭複習</span>
    <b>第 1 課：MLflow 實驗追蹤 →</b>
  </a>
</div>
"""

SCRIPT = r"""
/* ═══ hero 互動：管線重播機（四次執行全部是 notebook 的實測結果）═══ */
(function () {
  const STEPS = [
    { k: "churn_data",          g: "data",   label: "churn_data" },
    { k: "train_test",          g: "data",   label: "train_test" },
    { k: "trained_model",       g: "model",  label: "trained_model" },
    { k: "model_metrics",       g: "model",  label: "model_metrics" },
    { k: "quality_gate",        g: "gate",   label: "quality_gate（blocking）" },
    { k: "registered_champion", g: "deploy", label: "registered_champion" },
  ];
  const RUNS = {
    1: {
      cfg: '{"model": "rf", "max_depth": 8, "drift": 0.0}', auc: 0.9684, champ: 0.0, pass: true,
      mt: { churn_data: "2000 列 · drift 0", train_test: "train 1500 / test 500",
            trained_model: "mlflow run dagster-… · models:/m-…", model_metrics: "roc_auc 0.9684" },
      deployMt: "register → v1 · alias @champion → v1",
      reg: [{ v: 1, m: "rf depth 8", auc: "0.9684", live: true }],
    },
    2: {
      cfg: '{"model": "logreg", "max_depth": 8, "drift": 0.0}', auc: 0.9508, champ: 0.9684, pass: false,
      mt: { churn_data: "2000 列 · drift 0", train_test: "train 1500 / test 500",
            trained_model: "mlflow run dagster-… · models:/m-…", model_metrics: "roc_auc 0.9508" },
      reg: [{ v: 1, m: "rf depth 8", auc: "0.9684", live: true }],
    },
    3: {
      cfg: '{"model": "rf", "max_depth": 16, "drift": 0.0}', auc: 0.9698, champ: 0.9684, pass: true,
      mt: { churn_data: "2000 列 · drift 0", train_test: "train 1500 / test 500",
            trained_model: "mlflow run dagster-… · models:/m-…", model_metrics: "roc_auc 0.9698" },
      deployMt: "register → v2 · alias @champion → v2",
      reg: [{ v: 1, m: "rf depth 8", auc: "0.9684", live: false }, { v: 2, m: "rf depth 16", auc: "0.9698", live: true }],
    },
    4: {
      cfg: '{"model": "rf", "max_depth": 16, "drift": 1.5}', auc: 0.8641, champ: 0.9698, pass: false,
      mt: { churn_data: "2000 列 · drift 1.5（特徵被噪音推走）", train_test: "train 1500 / test 500",
            trained_model: "mlflow run dagster-… · models:/m-…", model_metrics: "roc_auc 0.8641" },
      reg: [{ v: 1, m: "rf depth 8", auc: "0.9684", live: false }, { v: 2, m: "rf depth 16", auc: "0.9698", live: true }],
    },
  };
  const MIN_AUC = 0.95;
  const map = document.getElementById("pl-map");
  const reg = document.getElementById("pl-reg");
  const verdict = document.getElementById("pl-verdict");
  const log = document.getElementById("pl-log");
  const buttons = Array.from(document.querySelectorAll("#pl-demo .ctl button"));
  let timers = [];

  map.innerHTML = STEPS.map(function (s) {
    return '<div class="step ' + s.g + (s.g === "gate" ? " gate" : "") + '" data-k="' + s.k + '">' +
      "<b>" + s.label + "</b><span class=\"mt\"></span></div>";
  }).join("");
  const nodes = {};
  STEPS.forEach(function (s) { nodes[s.k] = map.querySelector('[data-k="' + s.k + '"]'); });

  function drawRegistry(rows) {
    const vers = rows.length
      ? rows.map(function (r) {
          return '<div class="ver' + (r.live ? " live" : "") + '">version ' + r.v + " · " + r.m +
            "<br>eval_auc " + r.auc + (r.live ? ' <span class="al">@champion</span>' : "") + "</div>";
        }).join("")
      : '<div class="empty">（還沒有任何版本）</div>';
    reg.innerHTML = '<div class="rt">MODEL REGISTRY</div><div class="rn">churn-clf</div>' + vers +
      '<div class="svc">服務端永遠載<br>models:/churn-clf@champion</div>';
  }

  function reset() {
    timers.forEach(clearTimeout); timers = [];
    STEPS.forEach(function (s) {
      nodes[s.k].className = "step " + s.g + (s.g === "gate" ? " gate" : "");
      nodes[s.k].querySelector(".mt").textContent = "";
    });
    verdict.className = "verdict"; verdict.textContent = "";
    log.innerHTML = "";
  }

  function play(id) {
    const run = RUNS[id];
    reset();
    buttons.forEach(function (b) { b.classList.toggle("on", b.dataset.run === String(id)); });
    drawRegistry(id === 1 ? [] : RUNS[id - 1].reg);
    log.innerHTML = "materialize(PIPELINE + CHECKS, run_config=" + run.cfg + ")";

    const seq = [];
    ["churn_data", "train_test", "trained_model", "model_metrics"].forEach(function (k) {
      seq.push(function () {
        nodes[k].classList.add("on");
        nodes[k].querySelector(".mt").textContent = run.mt[k];
        log.innerHTML += "\n" + k + ' <span class="ok">✓</span> ' + run.mt[k];
      });
    });
    seq.push(function () {
      const n = nodes.quality_gate;
      n.classList.add("on", run.pass ? "pass" : "fail");
      const cmp = run.auc.toFixed(4) + (run.pass ? " ≥ " : " < ") +
        (run.auc < MIN_AUC ? "min_auc " + MIN_AUC.toFixed(2) : "champion " + run.champ.toFixed(4));
      n.querySelector(".mt").textContent = cmp;
      log.innerHTML += "\nquality_gate " + (run.pass
        ? '<span class="ok">✓ 通過</span>' : '<span class="no">✗ 擋下</span>') +
        " {auc: " + run.auc.toFixed(4) + ", champion_auc: " + run.champ.toFixed(4) + ", min_auc: " + MIN_AUC.toFixed(2) + "}";
    });
    seq.push(function () {
      const n = nodes.registered_champion;
      if (run.pass) {
        n.classList.add("on");
        n.querySelector(".mt").textContent = run.deployMt;
        log.innerHTML += "\nregistered_champion <span class=\"ok\">✓</span> " + run.deployMt +
          '\nsuccess <span class="ok">True</span>';
        drawRegistry(run.reg);
        verdict.className = "verdict ok";
        verdict.textContent = "執行成功 · champion 換成 v" + run.reg[run.reg.length - 1].v;
      } else {
        n.classList.add("on", "skip");
        n.querySelector(".mt").textContent = "被 blocking 檢查擋住，沒有執行";
        log.innerHTML += '\nregistered_champion <span class="no">— 下游被擋，沒有執行</span>' +
          '\nsuccess <span class="no">False</span>';
        drawRegistry(run.reg);
        verdict.className = "verdict no";
        verdict.textContent = "執行失敗 · 沒有任何東西上線，線上仍是 v" +
          run.reg.filter(function (r) { return r.live; }).map(function (r) { return r.v; })[0];
      }
    });
    seq.forEach(function (fn, i) { timers.push(setTimeout(fn, 260 * (i + 1))); });
  }

  buttons.forEach(function (b) {
    b.addEventListener("click", function () { play(Number(b.dataset.run)); });
  });
  drawRegistry([]);
  STEPS.forEach(function (s) { nodes[s.k].classList.add("on"); });
  verdict.className = "verdict";
  verdict.textContent = "";
  log.textContent = "按上面任一次執行，看這條線走一遍。";
})();
"""

PANEL_STEPS = """
        <li>登入 molab（GitHub / Google）</li>
        <li>開啟課程 notebook，<b>Fork 成自己的副本</b>即可編輯</li>
        <li>從第一格往下全部執行（首次安裝套件約 1–2 分鐘，管線本身合計約 1 分鐘上下）——<b>免費 CPU 環境即可</b>，不需要 GPU；MLflow 與 Dagster 的帳本都在暫存資料夾裡</li>
"""
