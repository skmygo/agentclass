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
| 05 | mlops-pipeline | 上線 | Dagster 資產管線 × MLflow：訓練→evaluate→asset check 品質閘→通過才移 champion alias |
| 00 | mlops-why | 上線 | 純瀏覽器 app：模型漂移與再訓練模擬（為什麼需要 MLOps） |
| 06 | model-serving | 上線 | 批次評分 vs 線上 API：自包 FastAPI、`mlflow models serve`、alias 換版重載 |
| 07 | model-monitoring | 上線 | PSI／KS 手算、預測漂移、Evidently 報告、監控結果接回 Dagster check／sensor |
| 08 | optuna-hpo | 上線 | study/trial/objective、TPE vs Random、重要度、pruning、每 trial 一個 MLflow nested run、sqlite 續跑 |
| 09 | data-validation | 上線 | pandera DataFrameSchema／DataFrameModel、lazy failure_cases、YAML 合約、接 Dagster blocking check |
| 10 | mlflow-tracing | 上線 | @mlflow.trace span 樹、attributes/tags/search、assessments、genai.evaluate code scorer、Prompt Registry |
| 11 | feature-store | 上線 | Feast：Entity/FeatureView、point-in-time join、ttl、materialize、online features、FeatureService |
| 12 | dvc-basics | 上線 | dvc add／指標檔／cache 內容定址、git checkout＋dvc checkout 回溯、dvc.yaml repro／skip、params/metrics diff、remote push/pull |
| 13 | ml-testing | 寫作中 | pytest 在 notebook 內跑：合約／表現／切片／行為（不變性、方向性、最低功能）測試，壞模型讓它紅 |
| 14 | model-explainability | 寫作中 | 三種特徵重要度對照、SHAP TreeExplainer 全域／局部、waterfall、審核 artifact、禁用欄位檢查 |

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

### 模型上線課（06）subagent 實測補充（2026-09-04 03:45，MLflow 3.15.2）

- `/invocations`：`dataframe_split` **帶 index 也回 200**、`inputs`（欄名→值清單）可用、`instances`（無欄名）被 signature 擋；
  少一欄 400 含 `"error_class": "SCHEMA_ENFORCEMENT_FAILED"` ＋ `Model is missing inputs ['f11'].`；型別錯是 `BAD_REQUEST` /
  `Failed to convert column f0 to type 'float64'`；無信封的錯誤訊息列四個信封名但**順序每次不同**（set），別當規格引用。
- `mlflow models serve` 子行程**必須自帶 `MLFLOW_TRACKING_URI`**（不繼承 `set_tracking_uri`），否則 `Registered model alias champion not found.`；
  起來 7–15 秒；`/ping` 200 body `'\n'`。
- 延遲實測：批次 500 列 9–12 ms（每列 0.02 ms）vs 單列 7–11 ms → 差 300–500 倍；API 載一次 14–36 ms vs 每次 load_model 120–310 ms（8–10 倍）；
  `load_model` 本身 100–130 ms。alias 移到新版後**服務不會自動換**，要 `/reload` 或輪詢 `get_model_version_by_alias(...).version`（回 **int**；
  `register_model(...).version` 是 str——跨型別比較會靜默失敗）。`mlflow.models.validate_serving_input` 可用（回 (2,2)）。
- marimo：f-string 的 `mo.md` 內放含 `{}` 的程式範例會 `Invalid format specifier`——程式碼段拆成獨立 `mo.md(r"…")` 用 `mo.vstack` 併。
  未 fit 的 estimator 進 helper 會變成整串 `An ancestor raised an exception`。
- hero 用百分比寬長條＋`white-space:nowrap` 標籤在 390px 會撐破 `#lesson`：長條上限 ~58%、`.track` 加 `overflow:hidden`。
- 錯誤原文在 `_spikes/spike_model_serving_errors.py`（含 port 占用 `OSError(98, 'Address already in use')`）。

### 監控課（07）subagent 實測補充（2026-09-04 04:00）

- **page-fill 的 `PANEL_STEPS` 用 `re.sub(r"<ol>.*?</ol>")`**：WRAP 裡的裸 `<ol>` 會被 molab 面板步驟覆蓋；STYLE／WRAP 只要出現字面
  `<ol>`（連 CSS 註解）就會從那裡吃到面板的 `</ol>`、把 `</head>` 骨架吃掉（自檢 exit 1 擋下）。→ 主代理已把 regex 改成只認
  `#molab-panel` 內的 `<ol>`；課程內仍建議 `<ol class="…">`。
- **session JSON 不是原子的**：被 timeout 殺掉的 export，其 kernel（`spawn_main`）可能還活著並在之後補寫 → 新舊混寫。改內容重驗前
  `rm __marimo__/session/*.json`；殺殘留要連 kernel 子程序一起。
- **兩個 Dagster 課的 sandbox export 同時跑會互相拖垮**（30 秒的 notebook 卡 10 分鐘、WORK 目錄都沒建）→ Dagster／MLflow 課的 verify 排隊跑。
- Evidently 0.7.21：`get_html_str(as_iframe)` 位置參數必填；報告 4.3 MB 不嵌 notebook（存檔）；`Report.run()` 直接吃 DataFrame 也行；
  預設 `DataDriftPreset`（Wasserstein normed／0.1）對**沒漂移**的 test 也判 3/12 欄 → `DriftedColumnsCount` 不能當警報；
  `method="psi"` 算法與自寫「參考分位數分箱」不同（0.973 vs 0.558，且自寫版不對稱）。錯誤原文：缺欄 `ValueError: Column (f11) is
  partially present in data`、字串欄 `TypeError: ufunc 'isinf' not supported…`、`Cannot use ClassificationPreset without a
  classification configration`（官方 typo）。
- KS／PSI 的樣本數陷阱（實測）：沒漂移 n=50 p=0.919 → n=10000 p=9.7e-06；小漂移 +0.2 的 PSI n=50 0.243 → n=10000 0.010。
  in-sample 陷阱：拿訓練集預測當參考，預測 PSI 0.183 比真漂移 0.166 還高。
- Dagster sensor 在 notebook 內讀帳本：共用一個 `DagsterInstance.ephemeral()`，`context.instance.get_latest_materialization_event(key)
  .asset_materialization.metadata["max_psi"].value`；`@dg.sensor(target=…)` 的 tick 會留下 `dagster api grpc --heartbeat` 孤兒行程（會自己過期）。

### Optuna 課（08）subagent 實測補充（2026-09-04 04:05，Optuna 4.9）

- **`mo.stop` 的下游 cell 在 export 會被判 error**（`ancestor-stopped`）→ `nb-outputs.py` 記成 error、verify exit 1。
  `mo.stop` 只能放在沒有下游的 cell；「按鈕 → 計算格 → 圖表格」的計算格改用 `if`（未點擊設 `None`＋提示 md），圖表格自己 `mo.stop`。
- `TPESampler(seed=k)` 前 `n_startup_trials=10` 個 trial 與 `RandomSampler(seed=k)` 完全相同。重要度預設評估器不可重現（同 study 連跑差幾個百分點），
  `FanovaImportanceEvaluator(seed=0)` 才穩；`PedAnovaImportanceEvaluator` 排序完全不同——課程數字要釘評估器。
- objective 回傳 None／NaN 不拋錯：trial 標 `FAIL`、`optimize()` 照跑，`study.best_value` 才炸 `ValueError: No trials are completed yet.`
  其他原文：`` `low <= high` must hold, but got (low=16, high=2). ``／`Cannot set different distribution kind to the same parameter name.`／
  `DuplicatedStudyError: Another study with name 'rf-hpo' already exists…`／多目標 `best_trial` → `RuntimeError: A single best trial cannot be
  retrieved from a multi-objective study…`／`load_study` 找不到 → `KeyError: 'Record does not exist.'`（`_spikes/spike_optuna_errors.py`）。
- 離散小空間（8×5 格）別拿來證明 TPE 較強：25 次只造訪 15 個相異格，跑滿時格點掃描反而贏（0.9710 vs 0.9687）——課程正面教「Optuna 的價值在掃不完的空間」。
  數字：25 trial 17–20 s best 0.9683；縮小空間第二輪 10 trial 7 s → 0.9716、測試集 0.9691；MedianPruner 15 trial 砍 8 個省 33–36%。
- hero 熱區色階：資料集中在高分區時用 `t^2` 才拉得開；`.cell.top` 標記用 `outline`（`box-shadow` 會被更高特異度的規則蓋掉）。

### Tracing 課（10）subagent 實測補充（2026-09-04 04:55，MLflow 3.15.2）

- `search_traces` filter：點前的 entity type 會驗（`foo.` → `Invalid entity type 'foo'. Valid values are {…}`），**點後的 key 不驗**
  （`tags.Topic`／`tags.topics` 靜靜回 0 筆）；`tag.` 與 `tags.` 都合法。DataFrame 欄名 `execution_duration` ≠ filter 欄名
  `attributes.execution_time_ms`。**不 flush 的查詢結果不確定**（0 或 2 筆都出現過）——文案別寫「一定 0 筆」。
- `get_trace(不存在)` 回 None 不拋錯；`update_current_trace()`／`get_current_active_span()` 在 trace 外靜默／回 None。
- `@scorer` 參數名只能是 `inputs`/`outputs`/`expectations`/`trace`；寫錯不報錯，`evaluate` 的 `metrics` 回 `{}`。
  `genai.evaluate` 每列會產生一條名為 `root_span` 的 trace。`register_prompt` 同名同 template 仍產生新版本（不去重）。
- 第一條 trace 有暖機成本（130–220 ms vs 之後 71–92 ms）。marimo：多個各自寫 DB 的 cell 要用變數顯式串成鏈，否則拓樸順序可能亂。
- 錯誤原文（`_spikes/spike_tracing_errors.py`）：`search_traces() got an unexpected keyword argument 'experiment_names'. Did you mean
  'experiment_ids'?`、`Trace with ID '…' not found. It may have been deleted.`、`Prompt alias nope not found.`、
  `Prompt (name=support-answer, version=99) not found`、`Missing variables: {'context'}…allow_partial=True`。

### 資料驗證課（09）subagent 實測補充（2026-09-04 05:05，pandera 0.33.1＋pandas 3.0.5）

- **pandas 3 讓時間型別合約變脆**：預設單位 `us`，`pa.DateTime`／`"datetime64[ns, UTC]"` 對 tz-aware 欄一律不過（`expected series 'ts' to have
  type datetime64[ns], got datetime64[us, UTC]`）、`pa.DateTime(unit=, tz=)` 是 TypeError → 只能靠 `coerce=True`。字串欄是 `str`／`string[python]`，
  `category` 欄會被 `pa.Column(str)` 拒。`import pandera as pa` 噴 FutureWarning，用 `pandera.pandas`。
- `schema.to_yaml()` 丟掉表級 `checks`（輸出 `checks: null`），欄位層檢查（含 regex）存得下——合約進版控要兩層。
- 表級 `pa.Check` 回傳 Series ＝逐列判定（failure_cases 把壞掉那列的每個欄位各記一筆，index 相同）；回傳 bool ＝整批判定。
  `field_uniqueness` 重複的兩列都報；`strict="filter"` 砍多餘欄不報錯；`strict=True` 的陷阱其實是**少欄位** `column 'refund' not in dataframe.`
- `mo.ui.table` 當 cell 最後運算式時 `nb-outputs.py` 掃不到輸出 → 關鍵數字另用 `mo.md` 寫一句。教學欄比視窗窄（1400px 視窗時 pane 只有 644px），
  多欄對照表要包 `.tw { overflow-x:auto }`＋`min-width`，視窗層 media query 擋不住。
- `_spikes/` 與 scratchpad 是跨 agent 共享的：背景 log 檔名要帶課程 id。Dagster 課 export 依賴快取命中時 cell 全跑完約 15–40 秒，其餘全是 hang。
- 驗證成本：500 列 2.4 ms、5 萬列 ~9 ms、50 萬列 60–107 ms；`drop_invalid_rows=True` 丟壞列。錯誤原文在 `_spikes/spike_pandera_errors.py`。

### Feast 課（11）subagent 實測補充（2026-09-04 05:45，Feast 0.66）

- **ttl 到期是整列丟掉不是 NaN**（360→356、`isna()` 全 0）——查完必比對筆數。`get_historical_features` 回傳列順序 ≠ entity_df 順序，用 join key 對齊。
- tz-naive 時間戳完全不報錯（都當 UTC），台北時間誤讀 → 59/360 列拿到不同特徵。`entity_df` 時間欄叫 `timestamp` 只印一行提示。
- 加欄位後 `materialize_incremental` 一列都不補（水位已到現在）→ 線上 `None`；要全量 `materialize(start, end)`。
- **on-demand feature view 在 Python 3.14 直接炸**（dill `_Pickler._batch_setitems() missing 1 required positional argument`）→ 本課 PEP 723 釘
  `requires-python = ">=3.11,<3.14"`；ODFV 宣告 dtype 必須等於函式推論 dtype（float64 宣告 Float32 → `SpecifiedFeaturesNotPresentError`）。
- `get_online_features` 對不存在 entity／未 materialize 回 `None` 不報錯；`materialize*` 印帶 ANSI 色碼的進度 → `redirect_stdout`＋去色碼。
- 教學：這份資料上「洩漏」不會讓離線分數變漂亮（PIT 0.8757 vs 洩漏 0.8629），課程把差距小本身當教學點。實測 naive「拿最新一筆」
  有 68% 列拿到不同值、最遠偷看未來 7.9 天；離線 vs 線上 20 位客戶三個特徵全等；online 熱查 0.13–0.25 ms。
- 頁面：`table.cmp` 數字欄要 `white-space:nowrap`；codeblock 單行視覺寬（CJK 算 2 欄）>~70 欄會被雙欄版面截掉。

### DVC 課（12）subagent 實測補充（2026-09-04 05:50，DVC 3.67.1、marimo 0.24 sandbox）

- **`mo.md` 會把程式碼區塊裡以 `- ` 開頭的行當 markdown 清單重排**（YAML／dvc.lock 縮排 6→8、項目間插空行），fence 有無縮排都一樣壞，
  export／冒煙 `errors: 0` 看不出來——只有挖 session JSON 的 `text/html` 才看得到。**檔案內容與終端機輸出一律走
  `mo.Html("<pre>" + html.escape(text) + "</pre>")` 或 `mo.plain_text`**。（```text 圍欄內 `$` 不會被當 LaTeX。）
- DVC 最沉默的坑：改了 `params.yaml` 但沒把 key 加進 `dvc.yaml` 的 `params:` → `dvc status` 回 up to date、`repro` skip、零警告。
- `dvc.yaml` 的 `cmd: python train.py` 需要 `python` 在 PATH → subprocess 的 `env` 併入 `Path(sys.executable).parent`；設 `DVC_NO_ANALYTICS=1`。
  `dvc exp run` 跑完會 apply 到工作區，要 `git checkout -- params.yaml dvc.lock`＋`dvc repro` 收回。`dvc metrics diff` 需要 HEAD 的 metrics 在 cache
  （刪 cache→pull 後立刻 commit）。`dvc checkout` 遇未 add 修改 → `Can't remove the following unsaved files without confirmation. Use --force.`
- `mo.ui.dropdown(...).form()` export 時 `.value is None` → 用 `if` 分支渲染提示（不要 `mo.stop`）。
- hero 三欄 `<pre>` 桌機各約 200px：每行壓在 ~24 字元、md5 留 8 碼；`word-break: normal; overflow-wrap: anywhere`。
- 數字：raw.csv 470,591 B vs 指標檔 89 B；第一次 repro 2.2–2.6 s、skip 0.5–0.6 s；auc 0.95318→0.97287；`dvc exp` depth 6/20 → 0.96376/0.97063。

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

## 更多候選課 spike（2026-09-04 03:35）

- **mlflow-prompts**（`_spikes/spike_mlflow_prompts.py`，LLMOps）：`mlflow.genai.register_prompt(name, template="…{{var}}…", commit_message, tags)`
  → version 1/2；`set_prompt_alias(name, alias="production", version=)`；`load_prompt("prompts:/name@production")`／`"prompts:/name/1"`，
  `.variables`＝`{'question','context'}`、`.format(**kw)`；`search_prompts(filter_string="name = '…'")`；在 `@mlflow.trace` 內 `load_prompt`
  會把 `mlflow.linkedPrompts` tag 掛到 trace（`[{"name": "support-answer", "version": "2"}]`）；chat 格式 template（list of role/content）也可。
  全部離線、不需要 LLM。
- **feast**（`_spikes/spike_feast.py`，Feast 0.66）：`feature_store.yaml`（provider local、registry `data/registry.db`、online sqlite、
  `entity_key_serialization_version: 3`）＋ `features.py`（`Entity`、`FileSource(parquet, timestamp_field)`、`FeatureView(ttl=3d, schema=[Field…])`）；
  **`python -m feast` 不能跑**（沒有 `__main__`），notebook 用 Python API `FeatureStore(repo_path=".").apply([entity, fv])`；
  `get_historical_features(entity_df, features=[...]).to_df()` 做 point-in-time join（每列拿到「當時」最新的特徵）；
  `materialize_incremental(end_date=now)` 推進 online store；`get_online_features(features, entity_rows).to_dict()`。全程 0.5 秒。
  parquet 的 `event_timestamp` 要 tz-aware（UTC）。

- **ml-testing**（`_spikes/spike_ml_testing.py`，候選）：notebook 內用 `pytest.main(["-q", "-p", "no:cacheprovider", path])`＋
  `contextlib.redirect_stdout` 抓輸出；測試檔寫到暫存目錄（model.pkl＋test.csv 用 fixture 載）。八種模型測試（最低表現、輸出形狀與範圍、
  雜訊不變性、方向性、缺欄要炸、決定性、parametrize 特徵洗牌）8 passed 0.12 s；失敗輸出格式
  `E       AssertionError: accuracy 0.916 below gate 0.95`＋`FAILED …::test_min_perf_strict`、exit code 1。

- **model-explainability**（`_spikes/spike_shap.py`，SHAP 0.52.0）：`TreeExplainer(rf).shap_values(300 列)` 0.41 s，回 ndarray (300, 12, 2)
  （取 `[:, :, 1]`）；mean|SHAP| 前五 f2 0.2128／f3 0.1006／f9 0.0513／f4 0.0377／f0 0.0245；`expected_value` [0.512, 0.488]；
  第 0 筆 0.746 ＝ 0.488 ＋ Σ 貢獻（加總對得起來）。permutation_importance（roc_auc, 5 次）0.7 s 前五 f2 0.2424／f3 0.0862／f9 0.0218；
  RF 內建 f2 0.4078／f3 0.1608／f9 0.0868——三種方法前二名一致、之後順序不同。`summary_plot(show=False, plot_size=)`、
  `plots.waterfall(expl[0, :, 1], show=False)` 都可存 png。
