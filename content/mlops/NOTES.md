# mlops 主題筆記（MLOps 自動化技術）

系列建於 2026-09-04（MLflow 3.15.2、Dagster 1.13.20、marimo 0.23.16；sandbox export 會裝 marimo 0.24.0）。
全系列外部軌（molab 免費 CPU）：`pyodide-spike.mjs mlflow dagster` 實測 FAIL（無純 Python wheel／grpcio），
純瀏覽器課只有規劃中的「為什麼需要 MLOps」漂移模擬（numpy/sklearn，app 模式）。

## 系列規劃（課程順序＝主題頁順序）

| # | id | 狀態 | 一句話 |
|---|---|---|---|
| 01 | mlflow-tracking | 上線 | run 的 params/metrics/tags/artifacts、step 曲線、autolog、nested runs、search_runs |
| 02 | mlflow-registry | 上線 | log_model 資料夾、signature 合約、Registry 版本與 alias、evaluate、自訂 pyfunc、log_input |
| 03 | dagster-assets | 上線 | @asset、依賴成圖、metadata、deps、IO manager、asset check（blocking）、Definitions |
| 04 | dagster-automation | 上線 | resources/Config、partitions、schedules、sensors（cursor）、AutomationCondition、RetryPolicy |
| 05 | mlops-pipeline | 完成待部署 | Dagster 資產管線 × MLflow：訓練→evaluate→asset check 品質閘→通過才移 champion alias |
| 00 | mlops-why | 上線 | 純瀏覽器 app：模型漂移與再訓練模擬（為什麼需要 MLOps） |
| 06 | model-serving | 寫作中 | 批次評分 vs 線上 API：自包 FastAPI、`mlflow models serve`、alias 換版重載 |
| 07 | model-monitoring | 寫作中 | PSI／KS 手算、預測漂移、Evidently 報告、監控結果接回 Dagster check／sensor |
| 08+ | optuna-hpo / data-validation(pandera) / mlflow-tracing / dvc | 候選（spike 已跑通） | 時間允許再加 |

## 共用的教學素材（各課沿用，數字才對得上）

- 資料：`make_classification(n_samples=2000, n_features=12, n_informative=6, random_state=0)`，
  欄位 `f0`–`f11`，`train_test_split(test_size=0.25, random_state=0)` → train 1500 / test 500，流失率 50%。
- baseline LogisticRegression(max_iter=1000)：AUC 0.9508、acc 0.882。
  RandomForest(n_estimators=100, max_depth=8, random_state=0)：AUC 0.9684。
  sweep（60 樹）depth 2/4/8/16 → AUC 0.925/0.956/0.967/0.969。
- Dagster 訂單資料：`rng = np.random.default_rng(0)`，500 筆，3% 金額為負 → clean 後 478 列、丟 22；59 位客戶。

## 工程坑（實測）

### MLflow 3.15

- **檔案後端 `./mlruns` 已進維護模式**：`set_tracking_uri("./mlruns")` 或 `file:` 一用就 `MlflowException: The filesystem
  tracking backend ... is in maintenance mode ...`（可設 `MLFLOW_ALLOW_FILE_STORE=true` 逃生）。課程一律
  `sqlite:///<tmp>/mlflow.db`；Registry 也只有 DB 後端才有。
- **artifact 位置預設落在 cwd 的 `./mlruns`**（即使 tracking 是 sqlite）：`create_experiment(name, artifact_location=...)`
  指到暫存資料夾，否則 sandbox export 會在課程目錄留一坨 `mlruns/`。
- 工作目錄用 `Path(tempfile.gettempdir()) / "<課名>"`，notebook 開頭 `shutil.rmtree` 清掉——重跑數字才一致。
- `log_model(..., name=...)`（3.x 用 `name`，`artifact_path` 已 deprecated）；sklearn 1.9 預設序列化成 `model.skops`。
- `search_model_versions()` 回的 version **不帶 aliases**（`[]`）；要 `client.get_model_version(name, v).aliases`
  或 `get_registered_model(name).aliases`（dict alias→version）。
- `mlflow.models.evaluate(model_uri, df, targets=, model_type="classifier")`：8 個 float 指標＋5 個圖 artifacts
  （roc/pr/lift/calibration/confusion_matrix），confusion_matrix 的 `.uri` 是 `file://` 路徑可用 imread 讀回。
- pyfunc 的 sklearn flavor `predict` 回類別；要機率用 `mlflow.sklearn.load_model(uri).predict_proba`
  （alias／version URI 兩種 flavor 都吃）。
- 日誌：`logging.getLogger("mlflow").setLevel(logging.ERROR)` ＋ `warnings.filterwarnings("ignore")`，
  `autolog(silent=True)`；否則建表提示與 skops 警告蓋掉教學輸出。
- 真實錯誤訊息（測驗題用）：同 run 改 param → `Changing param values is not allowed. Param with key='max_depth' was
  already logged with value='4' ...`；filter 少引號 → `Parameter value is either not quoted or unidentified quote types
  used for string value rf.`；`==` → `Invalid comparator '=='`；schema 少欄 → `Model is missing inputs ['f11'].`；
  型別錯 → `Failed to convert column f1 from type object to DataType.double.`；壞 alias →
  `Registered model alias nope not found.`；start_run 內再 start_run → `Run with UUID ... is already active ... nested=True`。

### Dagster 1.13

- **`materialize()` 沒有 `asset_checks=` 參數**：檢查跟資產放同一個 list `materialize([a, b, my_check])`。
- **日誌靜音**：`logging.getLogger("dagster").setLevel(...)` 沒用；要 `run_config={"loggers": {"console": {"config":
  {"log_level": "WARNING"}}}}`（課程定義 `QUIET` 常數，跟 op config 合併 `{**QUIET, "ops": {...}}`）。
- blocking check 失敗：run `success=False`、下游不跑，錯誤
  `DagsterAssetCheckFailedError: 1 blocking asset check failed with ERROR severity:\nmodel_metric: good_enough`。
  資產丟例外：`DagsterExecutionStepExecutionError: Error occurred while executing op "bad_asset":`；
  `error.cause` 在 1.13 可能是 None，原始例外文字在 log／`error.message` 後段。
- `evaluate_automation_conditions(defs=, instance=, cursor=)` 回 `EvaluateAutomationConditionsResult`：
  `total_requested`、`get_num_requested(key)`、`get_requested_partitions(key)`、`cursor`——**沒有 `run_requests`**。
- schedule／sensor 在 notebook 內用 `evaluate_tick(build_schedule_context(scheduled_execution_time=...))`／
  `evaluate_tick(build_sensor_context(instance=, cursor=))` 就能看 RunRequest／SkipReason，不用起 daemon。
  `build_schedule_from_partitioned_job(job, hour_of_day=3)` 在 09-04 03:00 tick 產 partition `2026-09-03`（前一天）。
- `RetryPolicy(max_retries=2)`：事件序列 `STEP_UP_FOR_RETRY, STEP_RESTARTED` ×2，`context.retry_number` 可讀。
- **marimo export 收尾卡住**：Dagster 課 sandbox export 全 cell 跑完（session JSON 已寫出）後行程不退出——
  見本檔「export hang」節的隔離測試結果與對策。

### Dagster 1.13 補充（第 03 課 subagent 實測，2026-09-04 02:50）

- **`AssetCheckResult.severity` 預設是 `ERROR`**（不是 WARN）；WARN 要明寫 `severity=dg.AssetCheckSeverity.WARN`。
  擋不擋下游完全由 `@asset_check(blocking=True)` 決定，跟 severity 是兩個獨立旋鈕。
- **`error.cause` 不是 None**：是 `SerializableErrorInfo` 且可能多層，`while node.cause: node = node.cause` 走到底才拿到
  原始例外（`ValueError: boom…`）；`error.message`／`error.stack` 只有外層。
- **`deps=["打錯的字串"]` 不報錯**：字串變成 `is_executable=False` 的外部資產，run success=True，但下游不再等上游
  ——靜默的排序 bug（教學／實務都傳函式物件）。無依賴約束時執行順序看資產名排序，**改資產名要重驗引用順序的文案**。
- `asset_check` 函式的參數名不必等於資產名（按位置傳值）；**檢查沒放進 `materialize` 清單就靜靜不跑**、run 照樣 success。
- `selection="clean_orders*"` 字串萬用選法可用。組圖時參數名找不到上游：`Input asset "[...]" is not produced by any of the
  provided asset ops ... Did you mean one of the following? ["clean_orders"]`；空 instance 只選下游：
  `DagsterExecutionLoadInputError` ＋ `FileNotFoundError: .../storage/<asset>`；同名資產：`Duplicate asset key: AssetKey([...])`。
  錯誤原文都在 `_spikes/spike_dagster_assets_errors.py`。
- `mo.md` 多行插值（檔案清單、錯誤原文）要對齊縮排，否則 dedent 失效整段變 code block。

### Dagster 1.13 補充（第 04 課 subagent 實測，2026-09-04 03:10）

- **`evaluate_automation_conditions` 在 marimo cell 內會炸** `RuntimeError: asyncio.run() cannot be called from a running
  event loop`（cell 是 async context）→ 用 `ThreadPoolExecutor` 丟到另一執行緒跑。
- `add_output_metadata` 別用 `"path"` 當 key：會被 IO manager 同名 metadata 蓋掉（值變 pickle 路徑，靜默）。
- `materialize([a, b], selection=[b])` 仍需提供 `a` 的 resources，否則 `resource with key 'store' required by op 'orders' was not provided`。
- `asset_sensor` 的 `asset_event` 是 `EventLogEntry`，沒有 `.storage_id`；用 `asset_event.dagster_event.event_specific_data.materialization`＋`.run_id`。
- `ScheduleDefinition.execution_timezone` 沒設是 `None`（不是 "UTC"）；`build_schedule_from_partitioned_job` 產的是 `'UTC'`，
  對沒分割的 job 也不報錯。cron 寫錯：`DagsterInvalidDefinitionError: Found invalid cron schedule '0 25 * * *' … 5 fields.`
- `on_cron` 語意：cron tick 過了＋上游的新更新在該 tick 之後才被「這次評估」看見才發；`NewlyUpdated` 相對上一次評估——
  demo 要先評估一次再 materialize，可用 `evaluation_time` 捏時鐘。
- partition 上界是「現在（UTC）」：課程「今天」用 `dt.datetime.now(dt.UTC).date()`，本地日期會少一片／`DagsterUnknownPartitionError`。
- 錯誤原文全在 `_spikes/spike_dagster_automation_errors.py`。

## export hang（Dagster 課）

隔離測試（2026-09-04 02:10）：一個只有 `import dagster; dg.materialize([a])` 的 3 行 notebook，
`marimo export html --sandbox` 全 cell 跑完、session JSON 寫出後**行程不退出**（240s timeout 才被殺；
`DagsterInstance.ephemeral()` 有無都一樣）→ 根因在 dagster 本身（推測是背景執行緒），不是課程寫法。
`DAGSTER_TELEMETRY_ENABLED=false` 也一樣卡（02:25 實測）；export log 尾端是 marimo 的
`parent_poller: Parent server appears to have exited, shutting down.`——export 主程序已結束、kernel 子程序不退。

**對策（驗證流程）**：`timeout 900 bash .claude/skills/make-lesson/scripts/verify-ext.sh mlops <id>`；
回傳 124 時以 `nb-outputs.py` 掃 `content/mlops/<id>/__marimo__/session/<id>_ext.py.json`——
全 cell 有輸出且 `errors: 0` 即通過。molab 上學員互動執行不受影響。

## 壓軸課（05 mlops-pipeline）spike 實測（`_spikes/spike_mlops_pipeline.py`）

資產鏈 `churn_data → train_test → trained_model（MLflow run＋log_model）→ model_metrics（mlflow.models.evaluate）
→ quality_gate（blocking check：AUC ≥ 0.95 且 ≥ champion 的 eval_auc）→ registered_champion（register＋移 alias）`，
MLflow 以 `ConfigurableResource` 注入（tracking_uri／experiment）。四次 run：

| run | 設定 | AUC | 結果 |
|---|---|---|---|
| 1 | rf depth 8（尚無 champion） | 0.9684 | 通過 → v1 champion |
| 2 | logreg | 0.9508 | 低於 champion → gate 擋，`registered_champion` 未實體化 |
| 3 | rf depth 16 | 0.9698 | 通過 → v2 champion |
| 4 | rf depth 16 + drift 1.5（特徵加噪音） | 0.8641 | 低於 0.95 → 擋 |

註：gate 失敗時即使 `QUIET`（WARNING）仍會在 stderr 印 `DagsterAssetCheckFailedError` traceback；
想完全安靜把 console log_level 設 `CRITICAL`。champion 的 eval_auc 用 `client.log_metric(run_id, "eval_auc", …)`
補記到訓練 run 上，gate 才比得到。

### 壓軸課（05）subagent 實測補充（2026-09-04 03:30）

- **MLflow 3.15 預設 tracking uri 是 `sqlite:///<cwd>/mlflow.db`**（不是 `./mlruns`）：資產內忘了 `setup()` → Dagster success=True、
  零錯誤，但管線的 tracking 0 個 run、cwd 多一個 `mlflow.db`（最沉默的錯）。spike／notebook 先 `os.chdir(tmp)` 或一律先 `set_tracking_uri`。
- **AutomationCondition 需要基準 tick**：materialize 之後直接以 `cursor=None` 評估得 0；正確順序 tick0（基準）→ materialize → tick1 → tick2
  ＝ 0 → 1 → 0。上游 blocking check 失敗時，其下游 eager 資產不會被 request（同一 tick：data_profile 1、champion_scorecard 0）。
- `deps=` 可省：只靠參數名宣告依賴，blocking check 照樣擋下游。
- Dagster 課 export 實際耗時：首次含裝套件 3–4 分鐘，之後快取命中約 100 秒（session JSON 寫出即算完），其餘全是 hang。
- 錯誤原文（`_spikes/spike_mlops_pipeline_errors.py`）：`resource with key 'mlflow_res' required by op ... was not provided`；
  `Registered Model with name=churn-clf not found`（未註冊）vs `Registered model alias chapmion not found.` vs
  `Model Version (name=churn-clf, version=99) not found`；`DagsterInvalidConfigError: ... Value "deep" of type "<class 'str'>" is not valid for expected type "Int"`；
  evaluate 的 `The specified pandas DataFrame does not contain the specified targets column 'churn'.`
- 100 棵樹 RF 的 depth→AUC：2/4/6/8/12/16 → 0.9297/0.9551/0.9656/0.9684/0.9725/0.9698（16 以上持平）；drift 0.25/0.5/0.75/1.0/1.5/2.0 →
  0.9739/0.9581/0.9366/0.9209/0.8641/0.8092；recall depth 8 = 0.9129、logreg 0.860。

## 前導課（00 mlops-why，純瀏覽器 app）spike 實測（`_spikes/spike_mlops_why.py`）

24 個月、每月 300 筆、6 維；概念漂移＝決定邊界的權重向量以 `theta = drift_rate * month` 旋轉。
第 0 月訓練 LogisticRegression 後：不重訓 → 平均 acc 0.660、第 23 月 0.453（逐月 0.94→0.42）；
每 3 個月重訓 → 平均 0.900（7 次）；監控觸發（acc<0.85 才重訓）→ 平均 0.889、4 次（第 4/9/15/20 月）。
k=1/3/6 → 0.916/0.900/0.867；thr 0.8/0.9/0.95 → 3/7/23 次重訓。全部模擬 1.2 秒（CPython），Pyodide 可負擔。
**注意 drift_rate 上限 ≈0.13**：旋轉超過 π 會「繞回來」（0.25 時第 23 月 acc 又回到 0.87 是假象）——
拉桿範圍設 0–0.13，或改用不會繞回的漂移形式。

### 前導課（00）subagent 實測補充（2026-09-04 03:00）

- 純瀏覽器模擬課的省算法：`functools.lru_cache` 包「世界（資料）」與「整段模擬」，拉桿回到看過的值 0 ms；
  載入時全部模擬 CPython 468 ms、拉一次 77 ms。
- 兩種漂移對照：只有資料漂移（特徵均值平移 1.5）準確率 **0.945 不掉**（正類比 48%→95%），概念漂移 0.660 但輸入分佈幾乎不動
  ——「準確率沒掉不代表沒事、概念漂移在輸入看不見」。延遲標籤 delay 0→6：平均 0.889→0.796、重訓 4→14 次；
  delay 6 輸給「每 6 個月盲目重訓」（0.867、3 次）。
- 兩條資料重疊的曲線會被上層完全蓋住（像少畫一條）：底層畫粗＋半透明當光暈。
- 圖 5 張（`data-ready-figures="5"`），hero 用 notebook 實測的 23×23 上三角矩陣（第 m 月訓練的模型在第 t 月的準確率）重播。

## 候選課（model-serving）spike 實測（`_spikes/spike_model_serving.py`）

- `log_model(..., pyfunc_predict_fn="predict_proba")` 讓 pyfunc `predict` 回 (n,2) 機率。
- 自包 FastAPI＋uvicorn daemon thread：`POST /predict` 回機率，單筆延遲約 16 ms（本機）。
- `python -m mlflow models serve -m models:/churn-clf@champion -p <port> --env-manager local`（子行程、
  env 帶 `MLFLOW_TRACKING_URI`）約 8 秒起來：`GET /ping` 200、`GET /version` → 3.15.2、
  `POST /invocations` 用 `{"dataframe_split": {"columns": [...], "data": [[...]]}}`（不要帶 `index`），
  少一欄回 400 `{"error_code": "INVALID_PARAMETER_VALUE", "message": "Failed to predict data ... Failed to enforce schema ..."}`。
- 批次：pyfunc 直接 `predict(500 列)` 約 11 ms——線上 API vs 批次評分的取捨可用這兩個數字講。

## 其他候選課 spike（全部跑通，2026-09-04 02:30）

- **optuna-hpo**（`_spikes/spike_optuna_hpo.py`，Optuna 4.9）：RF 四個超參數、3-fold cv_auc，TPE 25 trials 約 18 s，
  best 0.9683（n_estimators 80／max_depth 9／min_samples_leaf 3／sqrt）；`get_param_importances` → max_depth 0.90 獨大；
  MedianPruner 20 trials 砍掉 10 個；每個 trial 一個 MLflow nested run（`trial.set_user_attr("mlflow_run", …)`）；
  study 可存 `sqlite:///optuna.db` 續跑（`load_if_exists=True`）。
- **model-monitoring**（`_spikes/spike_monitoring.py`）：生產資料 f0 平移 +1.5、f3 放大 ×2 → 自寫 PSI：f3 0.558、f0 0.487、
  其餘 <0.1（KS p 值同向）；預測漂移：平均機率 0.507→0.471、判正率 0.520→0.444、PSI 0.166；accuracy 0.916→0.864。
  Evidently 0.7：`Report([DataDriftPreset()]).run(cur_ds, ref_ds)` → `snapshot.dict()["metrics"]` 每項有
  `metric_name`（如 `ValueDrift(column=f0,method=Wasserstein distance (normed),threshold=0.1)`）、`config`、`value`；
  DriftedColumnsCount 3/12（f0 0.69、f3 0.81、f2 0.11）；`get_html_str()` 可嵌 `mo.Html`／iframe（待實測大小）。
- **data-validation**（`_spikes/spike_pandera.py`，pandera 0.33）：`pandera.pandas` 的 `DataFrameSchema`／`DataFrameModel`；
  `validate(lazy=True)` 拋 `SchemaErrors`，`e.failure_cases` 表格列出 column／check／failure_case／index（實測 4 筆：
  customer 99 超出 in_range(1,59)、amount NaN、amount -50、country XX）；不 lazy 只報第一個。與 Dagster blocking
  asset check 結合：failure_cases 轉 `MetadataValue.md` 掛在檢查上。
- **mlflow-tracing**（`_spikes/spike_mlflow_tracing.py`，不打真 LLM）：`@mlflow.trace(span_type=...)` 巢狀 span、
  `mlflow.get_current_active_span().set_attributes`、`update_current_trace(tags=)`；**trace 是非同步寫入，查之前要
  `mlflow.flush_trace_async_logging()`**；`search_traces(experiment_ids=[...])`（沒有 experiment_names）回 DataFrame
  （trace_id／state／execution_duration／request／response）；`log_feedback`／`log_expectation` 掛 assessment；
  `mlflow.genai.evaluate(data=, scorers=[@scorer 函式])` 不需要 LLM judge 也能跑（回 `has_number/mean`）。
- **dvc**（`_spikes/spike_dvc.py`，DVC 3.x）：暫存 git repo 內 `dvc init` → `dvc add data/raw.csv`（產 .dvc 指標檔＋.gitignore）
  → `dvc.yaml` stage（cmd／deps／params／metrics）→ `dvc repro`（沒改就 skip）→ 改 params.yaml 再 repro →
  `dvc params diff`（max_depth 4→12）／`dvc metrics diff`（auc 0.95459→0.97174）／`dvc dag`。全程約 13 s。
  molab 上需要 git 指令；notebook 用 `subprocess` 跑 CLI 並把輸出印成 code block。
