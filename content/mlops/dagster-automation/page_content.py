"""課程頁內容區（純常數）。改完跑：python3 .claude/skills/make-lesson/scripts/page-fill.py content/mlops/dagster-automation
build.sh 不會部署這個檔；它是 index.html 內容區的正本。"""

TITLE = "Dagster 自動化：誰來按下那個「執行」？"
DESCRIPTION = "Dagster 自動化詳解：resources 與 Config、job、cron 排程與時區陷阱、分割資產與補跑、用 cursor 記憶的感測器、AutomationCondition 宣告式自動化、RetryPolicy 與失敗通知——全部在 molab 免費環境實作，用 evaluate_tick 直接看排程與感測器會發出什麼。"
NB = "https://molab.marimo.io/github/skmygo/agentclass/blob/main/content/mlops/dagster-automation/dagster-automation_ext.py"

STYLE = r"""
  /* 語義色：藍＝排程（時鐘）、橘＝感測器（外界事件）、綠＝自動化條件（資產自己）、紅＝失敗 */
  :root { --c1: #4C72B0; --c2: #DD8452; --c3: #55A868; --cut: #C44E52; }
  a.golab { text-decoration: none; display: inline-flex; align-items: center; gap: 8px; }

  /* hero：cron 排程模擬器 */
  #cron-demo .q { display: flex; gap: 12px; flex-wrap: wrap; align-items: flex-end; margin-bottom: 10px; }
  #cron-demo label { font-size: 12.5px; font-weight: 800; display: flex; flex-direction: column; gap: 4px; }
  #cron-demo input[type=text] { font-family: var(--mono); font-size: 14px; padding: 7px 10px; border: 1.5px solid var(--ink); border-radius: 8px; min-width: 190px; background: #fff; color: var(--ink); }
  #cron-demo input[type=datetime-local] { font-family: var(--mono); font-size: 13px; padding: 6px 9px; border: 1.5px solid var(--ink); border-radius: 8px; background: #fff; color: var(--ink); }
  #cron-demo select { font-family: var(--mono); font-size: 13px; padding: 7px 10px; border: 1.5px solid var(--ink); border-radius: 8px; background: #fff; color: var(--ink); }
  #cron-demo .chips { display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 12px; }
  #cron-demo .chips button { font-family: var(--mono); font-size: 12px; padding: 4px 9px; border-radius: 7px; border: 1.5px solid var(--grid); background: var(--chip-bg); color: var(--ink); cursor: pointer; }
  #cron-demo .chips button:hover { border-color: var(--ink); }
  #cron-demo .chips button.bad { border-color: var(--cut); color: var(--cut); }
  #cron-demo .tbl { overflow-x: auto; }
  #cron-demo table { width: 100%; border-collapse: collapse; font-size: 13px; font-family: var(--mono); }
  #cron-demo th, #cron-demo td { padding: 6px 8px; border-bottom: 1px solid var(--grid); text-align: left; white-space: nowrap; }
  #cron-demo th { font-size: 11.5px; letter-spacing: .04em; color: var(--ink-soft); font-family: var(--sans); }
  #cron-demo th.tz { color: var(--c1); }
  #cron-demo td.diff { color: var(--cut); font-weight: 700; }
  #cron-demo .msg { font-size: 13px; margin: 8px 0 0; color: var(--ink-soft); }
  #cron-demo .msg.err { color: var(--cut); font-family: var(--mono); font-size: 12.5px; white-space: pre-wrap; }

  table.cmp { width: 100%; border-collapse: collapse; font-size: 13.5px; margin: 14px 0; }
  table.cmp th, table.cmp td { border-bottom: 1px solid var(--grid); padding: 8px 10px; text-align: left; vertical-align: top; }
  table.cmp th { font-size: 12px; letter-spacing: .04em; color: var(--ink-soft); }
  .kbd { font-family: var(--mono); background: var(--chip-bg); padding: 1px 6px; border-radius: 5px; font-size: 13px; }
  .three { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin: 14px 0; }
  .three div { border: 1.5px solid var(--grid); border-radius: 10px; padding: 10px 12px; font-size: 13.5px; }
  .three b { display: block; font-family: var(--mono); margin-bottom: 4px; }
  .three .s b { color: var(--c1); } .three .n b { color: var(--c2); } .three .a b { color: var(--c3); }
  @media (max-width: 640px) { .three { grid-template-columns: 1fr; } }
"""

WRAP = r"""
<section id="hero">
  <span class="eyebrow">DAGSTER · AUTOMATION · 04</span>
  <h1>Dagster 自動化：<br>誰來按下那個「執行」？</h1>
  <p style="margin-top:18px">
    上一課你宣告了資產、看著 Dagster 從依賴推出一張圖——然後<b>自己呼叫了 <span class="kbd">materialize()</span></b>。
    真實世界不會有人每天凌晨 2 點坐在電腦前按按鈕。這一課補上被留下的那半：<b>誰按、什麼時候按、按下去跑哪一段、壞了誰重試</b>。
    先玩最基本的那個問題——「這個 cron 到底什麼時候會跑」，順便撞一次幾乎每個人都踩過的時區陷阱：
  </p>

  <div class="hero-demo" id="cron-demo">
    <div class="q">
      <label>cron_schedule <input type="text" id="cron-q" value="0 2 * * *" spellcheck="false"></label>
      <label>execution_timezone
        <select id="cron-tz">
          <option value="Asia/Taipei">Asia/Taipei</option>
          <option value="UTC">UTC（沒寫時就是這個）</option>
        </select>
      </label>
      <label>從什麼時候開始算 <input type="datetime-local" id="cron-t0" value="2026-09-08T01:30"></label>
    </div>
    <div class="chips" id="cron-chips">
      <button type="button" data-q="0 2 * * *">0 2 * * *（每天 02:00）</button>
      <button type="button" data-q="*/15 * * * *">*/15 * * * *（每 15 分鐘）</button>
      <button type="button" data-q="30 8 * * 1-5">30 8 * * 1-5（平日 08:30）</button>
      <button type="button" data-q="0 3 * * 1">0 3 * * 1（每週一 03:00）</button>
      <button type="button" class="bad" data-q="0 25 * * *">0 25 * * *（寫錯了）</button>
    </div>
    <div class="tbl"><table id="cron-tbl"></table></div>
    <p class="msg" id="cron-msg"></p>
  </div>

  <p class="note">
    接下來 5 次觸發是在瀏覽器裡照 cron 規則算的；<b>時區欄位的行為與錯誤訊息來自 notebook 實測</b>——
    排程沒寫 <span class="kbd">execution_timezone</span> 時那一欄真的是 <span class="kbd">None</span>（以 UTC 解讀），
    cron 寫錯時 Dagster 在<b>建立排程的當下</b>就丟出那句話。
  </p>
</section>

<section id="s1">
  <span class="eyebrow">01 · 環境、參數、打包</span>
  <h2>資產要被自動觸發，先把三件事分清楚</h2>
  <p>
    自動化不是「把 <span class="kbd">materialize()</span> 塞進 cron」。要讓別人（排程、感測器、daemon）替你按執行，
    程式得先能被<b>從外面設定</b>：連線與路徑歸資源，這一跑的參數歸設定，要一起跑的資產打包成 job。
  </p>
  <div class="codeblock">class FeatureStore(dg.ConfigurableResource):     # resource：外部世界的接點，部署時決定（dev / prod 各一份）
    root: str

class IngestConfig(dg.Config):                   # config：這一次執行的參數，每次觸發都可以不同
    n_rows: int = 500
    seed: int = 0

@dg.asset
def orders(context, config: IngestConfig, store: FeatureStore) -> pd.DataFrame:
    ...                                          # 寫成參數就會被餵進來，跟上游資產一樣

nightly_job = dg.define_asset_job("nightly_job", selection=dg.AssetSelection.assets("orders").downstream())</div>
  <p>
    實測：同一個 <span class="kbd">orders</span> 函式跑兩次，<b>程式碼一個字沒改</b>——第一次配 dev 資源抓 20 筆、
    第二次配 prod 資源抓 500 筆，檔案分別落在兩個目錄。之後排程與感測器要「帶著參數觸發」，帶的就是
    <span class="kbd">{"ops": {"orders": {"config": {…}}}}</span> 這個字典：<b>它們不是呼叫你的函式，是遞一張寫好參數的單子</b>。
  </p>
  <p>
    job 用 <span class="kbd">AssetSelection</span> 選資產的好處是<b>選擇會自己長大</b>：實測跑 <span class="kbd">nightly_job</span>
    實體化了 <span class="kbd">['orders', 'orders_report']</span>——我們沒點過 <span class="kbd">orders_report</span> 的名字，
    是 <span class="kbd">.downstream()</span> 把它帶進來的。之後新增的下游資產也一樣，半夜那一跑自動包含它。
  </p>
  <a class="golab" href="__NB__" target="_blank" rel="noopener">到 notebook 的 1️⃣–2️⃣ 節：資源與設定、job 真的跑一次</a>
</section>

<section id="s2">
  <span class="eyebrow">02 · 排程</span>
  <h2>時間到就跑：cron、時區，以及那張「單子」</h2>
  <div class="codeblock">nightly_schedule = dg.ScheduleDefinition(
    name="nightly_2am", job=nightly_job,
    cron_schedule="0 2 * * *",            # 分 時 日 月 週
    execution_timezone="Asia/Taipei",     # ← 不寫的話這一欄是 None，Dagster 以 UTC 解讀
)

@dg.schedule(job=nightly_job, cron_schedule="0 2 * * *", execution_timezone="Asia/Taipei")
def nightly_sized(context):               # 想「依日期決定參數」就自己寫函式
    day = context.scheduled_execution_time.strftime("%Y-%m-%d")
    return dg.RunRequest(
        run_key=day,                                                   # 同一天只會開一次 run
        run_config={"ops": {"orders": {"config": {"n_rows": 200}}}},   # 帶參數
        tags={"day": day, "trigger": "schedule"},                      # 貼標籤
    )</div>
  <p>
    排程的產出不是「執行」，是一張 <b><span class="kbd">RunRequest</span>（請跑這個 job）</b>。
    在 notebook 裡不用起 daemon 也能看它：<span class="kbd">evaluate_tick(build_schedule_context(scheduled_execution_time=…))</span>
    直接問「這個時刻你會發什麼」。實測最陽春的排程送出 <b>1 張</b>，內容是
    <span class="kbd">run_key=None</span>、<span class="kbd">run_config={}</span>、
    <span class="kbd">tags={'dagster/schedule_name': 'nightly_2am'}</span>（Dagster 自動貼的）。
  </p>
  <p>
    <b><span class="kbd">run_key</span> 是防重複跑的關鍵</b>：同一個排程送出相同 run_key 的單子，Dagster 只開一次 run——
    daemon 重評估、服務重啟、時鐘回撥都不會害你算兩次帳。日期字串是最常見的 run_key。
  </p>
  <p>
    cron 寫錯不會安靜地失敗，<b>建立排程物件的當下</b>就爆（所以 <span class="kbd">dagster dev</span> 一開就會告訴你）。實測原文：
  </p>
  <div class="codeblock">DagsterInvalidDefinitionError: Found invalid cron schedule '0 25 * * *' for schedule 'typo''.
Dagster recognizes standard cron expressions consisting of 5 fields.</div>
  <a class="golab" href="__NB__" target="_blank" rel="noopener">到 notebook 的 3️⃣ 節：兩種排程寫法、tick 送出的單子、cron 驗證</a>
</section>

<section id="s3">
  <span class="eyebrow">03 · 分割與補跑</span>
  <h2>把資產切成一天一片，缺哪幾天看得見</h2>
  <p>
    「一整包」的資產只有兩種狀態：跑過、沒跑過。真實資料是一天一天長出來的，所以你會需要
    <b>只重算昨天那一片</b>、<b>補跑掛掉那三天</b>、<b>分天比較品質</b>——這些在一整包上都做不到。
  </p>
  <div class="codeblock">daily_parts = dg.DailyPartitionsDefinition(start_date="2026-09-01")

@dg.asset(partitions_def=daily_parts)
def daily_orders(context) -> pd.DataFrame:
    day = context.partition_key            # 這一跑負責哪一片
    ...

dg.materialize([daily_orders], partition_key="2026-09-03", instance=inst)
instance.get_materialized_partitions(dg.AssetKey("daily_orders"))   # 哪幾片有了 → 剩下的就是要補的

daily_job = dg.define_asset_job("daily_orders_job", selection=[daily_orders], partitions_def=daily_parts)
daily_schedule = dg.build_schedule_from_partitioned_job(daily_job, hour_of_day=3)   # 每天 03:00 跑「前一天」那片</div>
  <p>
    notebook 用「今天往前 7 天」當分割起點，所以你哪天執行都會有 <b>7 片</b>。故意讓排程只跑了最早 3 片
    （模擬掛掉），<span class="kbd">get_materialized_partitions</span> 立刻列出缺的 4 片，一個迴圈補完變 <b>7 / 7</b>——
    每一片都是獨立的一次 run、各自留下 <span class="kbd">rows</span> 與 <span class="kbd">total</span> 中繼資料，直接拿來畫成每日趨勢。
  </p>
  <p>
    <span class="kbd">build_schedule_from_partitioned_job</span> 實測產出 cron <span class="kbd">0 3 * * *</span>、
    時區 <span class="kbd">UTC</span>（又是那個預設，記得改），而且它送出的單子帶的是
    <b><span class="kbd">partition_key</span></b>：任何一天的 03:00 tick 都指向<b>前一天</b>那一片。
    「每天凌晨結算昨天」不用自己算日期。
  </p>
  <p>
    分割也有專屬的錯誤：忘了給 <span class="kbd">partition_key</span> 是
    <span class="kbd">DagsterInvariantViolationError: Cannot access partition_key for a non-partitioned run</span>，
    給了範圍外的日期是 <span class="kbd">DagsterUnknownPartitionError: Could not find a partition with key ...</span>。
  </p>
  <a class="golab" href="__NB__" target="_blank" rel="noopener">到 notebook 的 4️⃣ 節：補跑、每日趨勢圖、挑日期問排程</a>
</section>

<section id="s4">
  <span class="eyebrow">04 · 感測器</span>
  <h2>有事情發生才跑，靠 cursor 記住看過什麼</h2>
  <p>
    排程回答「時間到了嗎」，但客戶什麼時候上傳檔案、上游什麼時候補完資料，都不看時鐘。
    感測器就是那個「每 30 秒被叫起來問一次」的函式，它只能回答兩件事：
    <b>要跑什麼（<span class="kbd">RunRequest</span>）</b>，或<b>為什麼不跑（<span class="kbd">SkipReason</span>）</b>。
  </p>
  <div class="codeblock">@dg.sensor(job=nightly_job, minimum_interval_seconds=30)
def inbox_sensor(context):
    seen = set(json.loads(context.cursor)) if context.cursor else set()   # cursor 是這個函式唯一的記憶
    files = sorted(p.name for p in INBOX.glob("*.csv"))
    new = [f for f in files if f not in seen]
    for f in new:
        yield dg.RunRequest(run_key=f, tags={"file": f})                 # 同一個檔案只會開一次 run
    if not new:
        yield dg.SkipReason(f"no new files (已看過 {len(seen)} 個)")
    context.update_cursor(json.dumps(sorted(seen | set(new))))           # 把記憶存回去</div>
  <p>
    實測四次 tick：空資料夾 → <b>skip</b>；丟進兩個檔案 → <b>2 張單子</b>，cursor 變成
    <span class="kbd">["batch_a.csv", "batch_b.csv"]</span>；再問一次 → <b>skip</b>（檔案還在，但看過了）；
    再來一個新檔 → <b>1 張</b>。cursor 存什麼由你決定：檔名清單、上次的最大 mtime、上次讀到的資料庫 id。
  </p>
  <p>
    盯自己人則用 <b>資產感測器</b>：<span class="kbd">@dg.asset_sensor(asset_key=…, job=…)</span> 幫你把 cursor 那段寫好了——
    上游資產一有新的 materialization 就觸發。實測它的 cursor 從 <span class="kbd">None</span> 變成一個數字
    （事件的 storage id，也就是「我讀到第幾筆事件」），沒有新事件時的 skip 訊息是
    <span class="kbd">No new materialization events found for asset key AssetKey(['orders'])</span>。
  </p>
  <a class="golab" href="__NB__" target="_blank" rel="noopener">到 notebook 的 5️⃣ 節：三種 tick、資產感測器、自己排一次 tick</a>
</section>

<section id="s5">
  <span class="eyebrow">05 · 宣告式自動化</span>
  <h2>不寫 job，資產自己說什麼時候該更新</h2>
  <p>
    排程與感測器都是<b>由外往內推</b>：這個時刻／這件事發生時，去跑那包資產。管線一大就變成 20 個排程、
    8 個感測器，每加一個資產都要想「它該掛在哪個 job 上」。宣告式自動化反過來：條件寫在資產上。
  </p>
  <div class="codeblock">@dg.asset(automation_condition=dg.AutomationCondition.eager())          # 上游一更新，我就跟著更新
def orders_alert(): ...

@dg.asset(automation_condition=dg.AutomationCondition.on_cron("0 6 * * *"))   # 每天 6 點後、等上游備妥才更新
def daily_report(): ...

result = dg.evaluate_automation_conditions(defs=defs, instance=inst, cursor=前一次的cursor)
result.total_requested, result.get_num_requested(dg.AssetKey("orders_alert"))   # 沒有 run_requests 屬性</div>
  <p>
    實測 <span class="kbd">eager()</span> 的三次評估（每次把上一次的 cursor 傳進去）：
    什麼都還沒實體化 → <b>0</b>；上游 <span class="kbd">orders</span> 剛跑完 → <b>1</b>（下游被請求更新）；
    下游也跑完後再評 → <b>0</b>。<b>全程沒有寫任何 job、任何排程</b>，正式環境那一個「1」會由 daemon 直接變成一個 run。
  </p>
  <p>
    最容易誤會的是 <span class="kbd">on_cron</span>：它<b>不是</b>「每天 6 點跑我」，而是
    <b>「每天 6 點之後，等所有上游在這個週期內更新過了，才跑我」</b>。notebook 把時鐘捏在手上跑了六步，
    只有<b>第五步</b>被請求：cron 時刻早就過了，但上游是在那之後才更新的。
    差別正是資料工程最常見的競態——排程時間到了、上游還沒好，於是你用舊資料算出一份新報表。
    <b>排程不會等上游，<span class="kbd">on_cron</span> 會。</b>
  </p>
  <div class="three">
    <div class="s"><b>schedule</b>時鐘觸發，要 job。適合「每天固定時間」的入口資產。陷阱：時區預設 UTC、不等上游。</div>
    <div class="n"><b>sensor</b>你寫的檢查邏輯，要 job。適合「外面發生了什麼」。陷阱：忘了更新 cursor、忘了給 run_key。</div>
    <div class="a"><b>AutomationCondition</b>資產自己的條件，<b>不用 job</b>。適合中下游那一大片。陷阱：以為 on_cron 是排程。</div>
  </div>
  <p>
    實務上三種混用：入口資產（要去外面撈資料的那幾個）用排程或感測器，中下游用
    <span class="kbd">eager()</span> 自己跟上——要維護的排程只有幾個，不是幾十個。
  </p>
  <a class="golab" href="__NB__" target="_blank" rel="noopener">到 notebook 的 6️⃣ 節：eager 三次評估、on_cron 六步實驗</a>
</section>

<section id="s6">
  <span class="eyebrow">06 · 失敗與收成</span>
  <h2>壞掉會重試、有人被通知，然後交給 daemon</h2>
  <p>
    自動化最現實的一件事：<b>沒有人在看的時候，東西一定會壞</b>。網路抖一下、連線被回收、上游 API 回 503——
    這種「再試一次就好」的失敗，不該讓整條管線停到早上。
  </p>
  <div class="codeblock">@dg.asset(retry_policy=dg.RetryPolicy(max_retries=2, delay=0.2))
def flaky_train(context) -> int:
    if context.retry_number < 2:                  # 第 0、1 次故意失敗
        raise RuntimeError("connection reset")
    return 42

@dg.run_failure_sensor                            # 放進 Definitions 的 sensors，由 daemon 監看
def alert_on_failure(context):
    send_slack(context.failure_event.message)</div>
  <p>
    實測事件序列：<span class="kbd">STEP_START → STEP_UP_FOR_RETRY → STEP_RESTARTED → STEP_UP_FOR_RETRY → STEP_RESTARTED → STEP_SUCCESS</span>，
    run 成功、資產的值是 42——<b>綠燈，但你看得到它抖過</b>。所以不要用 try/except 把暫時性失敗吞掉，那會讓你以為系統很健康。
    重試用完還是失敗時，Dagster 的最後一句話是 <span class="kbd">Exceeded max_retries of 1</span>，這時該被叫起來的是 run failure sensor。
    （資料不對是另一回事：那是上一課的資產檢查，不該重試。）
  </p>
  <div class="codeblock">defs = dg.Definitions(assets=[...], jobs=[...], schedules=[...], sensors=[...], resources={...})

$ dagster dev -f pipeline.py      # 開 http://localhost:3000，同時起 webserver 與 daemon</div>
  <p>
    最後把零件收成<b>一份 <span class="kbd">Definitions</span></b>（實測這一課的成品：4 個資產、3 個 job、3 個排程、3 個感測器，
    Dagster 另外自動補一個涵蓋全部資產的隱含 job <span class="kbd">__ASSET_JOB</span>）。
    <b>daemon 是這一課的隱形主角</b>：它一直醒著，看 cron 到了沒、每 30 秒問一次每個感測器、評估所有資產的自動化條件、
    監看 run 狀態觸發失敗通知。UI 上每個排程與感測器都有一個開關（<b>預設是關的</b>），也看得到每一次 tick 發了幾張單、skip 的理由是什麼——
    本課用 <span class="kbd">evaluate_tick</span> 看到的東西，就是那些 tick 紀錄的內容。
  </p>
  <a class="golab" href="__NB__" target="_blank" rel="noopener">到 notebook 的 7️⃣–8️⃣ 節：重試事件、失敗通知、Definitions 全景圖</a>
</section>

<section id="s7">
  <span class="eyebrow">07 · 實戰</span>
  <h2>換你動手</h2>
  <div class="ex">
    <span class="lv">LEVEL 1</span>
    <p>寫一個「每週一早上 9 點」的排程，帶 <span class="kbd">run_config</span> 把 <span class="kbd">n_rows</span> 設成 1000，用 <span class="kbd">evaluate_tick</span> 確認送出的 <span class="kbd">run_key</span> 與參數是你要的。</p>
  </div>
  <div class="ex">
    <span class="lv">LEVEL 2</span>
    <p>把檔案感測器的 cursor 從「檔名清單」改成「上次看到的最大 mtime」，並限制一次最多送 2 張單子。丟 5 個檔案、連跑三次 tick 驗證行為。</p>
  </div>
  <div class="ex">
    <span class="lv">LEVEL 3</span>
    <p>把分割資產接上 <span class="kbd">AutomationCondition.on_cron("0 3 * * *")</span>，再加一個吃它的下游用 <span class="kbd">eager()</span>，串著 cursor 評估，觀察<b>哪幾片</b>被請求（<span class="kbd">get_requested_partitions</span>）。</p>
  </div>
  <p style="font-size:13.5px;color:var(--ink-soft);margin-top:10px">卡住了？每一題在 notebook 末節都有折疊解答——先自己做，再打開對照。</p>
</section>

<section id="quiz">
  <span class="eyebrow">08 · 驗收</span>
  <h2>情境測驗</h2>
  <p>離開前試試看：下面的情境都真的會遇到。每題選一個你認為的最佳做法，選了馬上看得到解釋。</p>
  <div data-quiz>

    <div class="quiz-q" data-answer="C">
      <p class="quiz-tag">Q1 <span class="qtype">情境題</span></p>
      <h3>客戶會不定時把 CSV 丟進一個共用目錄，一天可能 0 次也可能 20 次，你要在檔案出現後幾分鐘內處理它，而且<b>同一個檔案只能處理一次</b>。最佳做法是？</h3>
      <div class="quiz-opts">
        <button type="button" class="quiz-opt" data-k="A">A. 排一個每 5 分鐘跑的排程，job 把整個目錄的檔案重新處理一遍</button>
        <button type="button" class="quiz-opt" data-k="B">B. 在感測器函式外面用一個全域 <code>set()</code> 記住處理過的檔名，每次 tick 比對</button>
        <button type="button" class="quiz-opt" data-k="C">C. 寫感測器：用 <code>context.cursor</code> 記住看過的檔案，只對新檔 <code>yield RunRequest(run_key=檔名)</code></button>
        <button type="button" class="quiz-opt" data-k="D">D. 用 <code>AutomationCondition.eager()</code> 掛在處理資產上，檔案來了它就會自己更新</button>
      </div>
      <div class="quiz-fb" aria-live="polite"><p>感測器就是為這種「不看時鐘、看事件」的觸發而生的：cursor 記住看過什麼（不用每次重掃全部），<code>run_key</code> 是最後一道保險——同一個 run_key 的單子 Dagster 只會開一次 run。A 每 5 分鐘把整個目錄重跑一次，處理過的檔案會一再被處理，量大時成本很可觀；B 的全域變數活在 daemon 的記憶體裡，daemon 一重啟或換一台機器就全忘了，cursor 存在 Dagster 的儲存體裡才不會；D 誤會了 <code>eager()</code>——它看的是「上游<b>資產</b>有沒有新的實體化」，不會去看目錄裡有沒有新檔案，外部世界的事件還是要靠感測器帶進來。</p></div>
    </div>

    <div class="quiz-q" data-answer="B">
      <p class="quiz-tag">Q2 <span class="qtype dx">錯誤診斷</span></p>
      <h3>你要一個「每天凌晨 2 點」的排程，寫好上線後發現它每天都在<b>早上 10 點</b>才跑。你去 REPL 確認了排程物件：</h3>
      <div class="codeblock">>>> sched = dg.ScheduleDefinition(job=nightly_job, cron_schedule="0 2 * * *")
>>> sched.execution_timezone
None</div>
      <div class="quiz-opts">
        <button type="button" class="quiz-opt" data-k="A">A. cron 欄位順序記錯了，<code>"0 2 * * *"</code> 其實是「每天 10 點」，要改成 <code>"2 0 * * *"</code></button>
        <button type="button" class="quiz-opt" data-k="B">B. 沒指定 <code>execution_timezone</code>，cron 以 UTC 解讀——UTC 02:00 就是台北 10:00；加上 <code>execution_timezone="Asia/Taipei"</code></button>
        <button type="button" class="quiz-opt" data-k="C">C. daemon 被排在早上 10 點才啟動，把 daemon 改成開機自動啟動就會準時</button>
        <button type="button" class="quiz-opt" data-k="D">D. 前一天的 run 還沒結束卡住了，把 <code>max_concurrent_runs</code> 調大就會準時</button>
      </div>
      <div class="quiz-fb" aria-live="polite"><p>差整整 8 小時就是時區的簽名——台北是 UTC+8。<code>execution_timezone</code> 沒設定時實測是 <code>None</code>，Dagster 就以 UTC 解讀那串 cron；同樣的事情也發生在 <code>build_schedule_from_partitioned_job</code> 產生的排程上（它的時區印出來是 <code>UTC</code>）。A 的欄位順序是「分 時 日 月 週」，<code>"0 2 * * *"</code> 沒寫錯；C 不成立，daemon 是持續執行的行程，它啟動時會補評估，不會把每天的時刻整體推遲固定 8 小時；D 是併發限制的症狀（run 排隊），不會讓觸發時間每天穩定晚 8 小時。</p></div>
    </div>

    <div class="quiz-q" data-answer="D">
      <p class="quiz-tag">Q3 <span class="qtype dx">錯誤診斷</span></p>
      <h3>你想要「每小時的第 25 分鐘跑一次」，寫成 <span class="kbd">cron_schedule="0 25 * * *"</span>，結果 <span class="kbd">dagster dev</span> 一開就失敗：</h3>
      <div class="codeblock">DagsterInvalidDefinitionError: Found invalid cron schedule '0 25 * * *' for schedule 'typo''.
Dagster recognizes standard cron expressions consisting of 5 fields.</div>
      <div class="quiz-opts">
        <button type="button" class="quiz-opt" data-k="A">A. 5 個欄位不夠，Dagster 需要含「秒」的 6 欄位 cron：<code>"0 0 25 * * *"</code></button>
        <button type="button" class="quiz-opt" data-k="B">B. 排程沒有指定 <code>name</code>（訊息裡是 <code>'typo'</code>），補上名字就會通過</button>
        <button type="button" class="quiz-opt" data-k="C">C. 這是執行時才會發現的錯，先讓它上線，等 daemon 的 tick 紀錄出現紅字再回頭修</button>
        <button type="button" class="quiz-opt" data-k="D">D. 欄位順序是「分 時 日 月 週」，25 落在「時」上（合法範圍 0–23）；要每小時第 25 分應該寫 <code>"25 * * * *"</code></button>
      </div>
      <div class="quiz-fb" aria-live="polite"><p>把 cron 看成「時 分」是最常見的誤記——第一欄是<b>分</b>、第二欄才是<b>時</b>，所以 <code>0 25 * * *</code> 等於「每天 25 點整」，25 超出 0–23 就被擋下。要「每小時第 25 分」是 <code>25 * * * *</code>。A 方向錯了，訊息說的正是「標準 5 欄位」；B 誤讀了訊息，<code>'typo'</code> 只是那個排程的名字，跟合不合法無關；C 剛好相反——這類錯誤是在<b>建立排程物件的當下</b>就丟出來的，<code>dagster dev</code> 載入定義就會失敗，它根本上不了線。</p></div>
    </div>

    <div class="quiz-q" data-answer="A">
      <p class="quiz-tag">Q4 <span class="qtype">情境題</span></p>
      <h3>你的報表每天早上 6 點要出，但它依賴的訂單資料由另一個團隊的管線在<b>早上 5 點到 7 點之間</b>跑完，時間不固定。你希望報表<b>一定用當天的新資料</b>，而且一天只出一次。最佳做法是？</h3>
      <div class="quiz-opts">
        <button type="button" class="quiz-opt" data-k="A">A. 報表資產掛 <code>AutomationCondition.on_cron("0 6 * * *")</code>：6 點之後、等上游在這個週期內更新完才跑</button>
        <button type="button" class="quiz-opt" data-k="B">B. 排一個 <code>"0 6 * * *"</code> 的排程跑報表 job，準時最重要</button>
        <button type="button" class="quiz-opt" data-k="C">C. 排程改成 <code>"0 8 * * *"</code>，多等兩小時，上游通常都跑完了</button>
        <button type="button" class="quiz-opt" data-k="D">D. 報表資產掛 <code>AutomationCondition.eager()</code>，上游一更新就跟著更新</button>
      </div>
      <div class="quiz-fb" aria-live="polite"><p><code>on_cron</code> 正是為這種情況設計的：它不是「時間到就跑」，而是「這個 cron 週期內、等所有上游都更新過了才跑，而且一個週期最多跑一次」——notebook 的六步實驗看得很清楚，cron 時刻過了但上游還是上一個週期的資料時它不動，上游更新的那一刻才被請求。B 就是最經典的競態：上游 6 點 20 分才好，你 6 點整用昨天的資料出了一份新報表，而且看起來完全正常。C 只是把猜測的等待時間拉長，上游哪天慢了照樣中獎，還每天白等兩小時。D 保證用新資料，但上游一天更新三次它就跑三次，違反「一天一次」，而且完全不受 6 點這個業務時間約束。</p></div>
    </div>

    <div class="quiz-q" data-answer="C">
      <p class="quiz-tag">Q5 <span class="qtype">情境題</span></p>
      <h3>每天凌晨的訂單管線因為上游 API 偶爾回 503 而失敗，重跑一次通常就好了。你不想每天早上手動重跑，也不想失敗被靜靜吞掉。最佳做法是？</h3>
      <div class="quiz-opts">
        <button type="button" class="quiz-opt" data-k="A">A. 在資產函式裡把呼叫包成 <code>try/except</code>，失敗時回傳昨天的資料，讓 run 保持綠燈</button>
        <button type="button" class="quiz-opt" data-k="B">B. 把排程從一天一次改成一小時一次，反正總有一次會成功</button>
        <button type="button" class="quiz-opt" data-k="C">C. 資產加 <code>retry_policy=dg.RetryPolicy(max_retries=2, delay=...)</code>，並把 <code>@run_failure_sensor</code> 放進 <code>Definitions</code> 發通知</button>
        <button type="button" class="quiz-opt" data-k="D">D. 加一個 <code>@asset_check</code> 檢查資料有沒有進來，沒有就讓檢查失敗擋住下游</button>
      </div>
      <div class="quiz-fb" aria-live="polite"><p><code>RetryPolicy</code> 就是為「暫時性故障」設計的：實測事件流會留下 <code>STEP_UP_FOR_RETRY → STEP_RESTARTED</code>，重試成功後 run 是綠的、但你看得到它抖過幾次；真的救不回來時（<code>Exceeded max_retries of ...</code>）run failure sensor 會把人叫起來。A 是最危險的選項——用舊資料冒充新資料，管線永遠綠燈，錯誤要等到有人發現報表不動了才爆；B 讓同一天的資料被算很多次（沒有 run_key 保護時尤其亂），而且沒解決「失敗沒人知道」；D 方向不同：資產檢查管的是「資料對不對」，那種失敗不該重試，而這裡的問題是「連線抖了一下」。</p></div>
    </div>

    <div class="quiz-score" data-score></div>
  </div>
</section>

<div class="endnav">
  <a href="/mlops-pipeline/">
    <span class="tag">下一課</span>
    <b>Dagster × MLflow：一條會自己上線、不合格就自己擋下的訓練管線 →</b>
  </a>
  <a href="/mlops/">
    <span class="tag">主題</span>
    <b>‹ 回「MLOps 自動化技術」課程列表</b>
  </a>
</div>
"""

SCRIPT = r"""
/* ═══ hero 互動：cron 排程模擬器 ═══
   觸發時刻＝在瀏覽器裡照 cron 規則推算（分 時 日 月 週；支援 * , - / 與 dom/dow 的 OR 語意）。
   時區行為與錯誤訊息來自 notebook 實測：不寫 execution_timezone 時該欄是 None（以 UTC 解讀）；
   cron 非法時 Dagster 在建立排程物件當下就丟 DagsterInvalidDefinitionError（下方訊息是實測原文）。 */
(function () {
  const OFFSETS = { "Asia/Taipei": 8 * 60, "UTC": 0 };      // 兩者都是固定偏移，沒有日光節約時間
  const SPECS = [
    { min: 0, max: 59 },   // 分
    { min: 0, max: 23 },   // 時
    { min: 1, max: 31 },   // 日
    { min: 1, max: 12 },   // 月
    { min: 0, max: 7 },    // 週（7 也當星期日）
  ];
  const WD = ["日", "一", "二", "三", "四", "五", "六"];
  const q = document.getElementById("cron-q");
  const tzSel = document.getElementById("cron-tz");
  const t0 = document.getElementById("cron-t0");
  const tbl = document.getElementById("cron-tbl");
  const msg = document.getElementById("cron-msg");

  function parseField(spec, { min, max }) {
    const out = new Set();
    for (const part of spec.split(",")) {
      const m = part.match(/^(\*|\d{1,2}(?:-\d{1,2})?)(?:\/(\d{1,2}))?$/);
      if (!m) throw new Error("bad");
      const step = m[2] ? parseInt(m[2], 10) : 1;
      if (step < 1) throw new Error("bad");
      let lo, hi;
      if (m[1] === "*") { lo = min; hi = max; }
      else if (m[1].includes("-")) { const p = m[1].split("-").map(Number); lo = p[0]; hi = p[1]; }
      else { lo = Number(m[1]); hi = m[2] ? max : lo; }
      if (lo < min || hi > max || lo > hi) throw new Error("bad");
      for (let v = lo; v <= hi; v += step) out.add(v);
    }
    return out;
  }
  function parseCron(text) {
    const parts = text.trim().split(/\s+/);
    if (parts.length !== 5) throw new Error("bad");
    const fields = parts.map((p, i) => parseField(p, SPECS[i]));
    if (fields[4].has(7)) fields[4].add(0);
    return { parts, fields };
  }
  function matches(cron, d) {
    const [mi, ho, dom, mon, dow] = cron.fields;
    if (!mi.has(d.getUTCMinutes()) || !ho.has(d.getUTCHours()) || !mon.has(d.getUTCMonth() + 1)) return false;
    const domStar = cron.parts[2] === "*", dowStar = cron.parts[4] === "*";
    const domOk = dom.has(d.getUTCDate()), dowOk = dow.has(d.getUTCDay());
    if (domStar && dowStar) return true;
    if (domStar) return dowOk;
    if (dowStar) return domOk;
    return domOk || dowOk;                                  // 兩個都限定時是 OR（標準 cron 語意）
  }
  function fmt(ms) {
    const d = new Date(ms);
    const p = (n) => String(n).padStart(2, "0");
    return `${d.getUTCFullYear()}-${p(d.getUTCMonth() + 1)}-${p(d.getUTCDate())} ${p(d.getUTCHours())}:${p(d.getUTCMinutes())}（週${WD[d.getUTCDay()]}）`;
  }
  function render() {
    const tz = tzSel.value;
    const raw = q.value.trim();
    let cron;
    try { cron = parseCron(raw); }
    catch (e) {
      msg.className = "msg err";
      msg.textContent =
        `DagsterInvalidDefinitionError: Found invalid cron schedule '${raw}' for schedule 'typo''.\n` +
        "Dagster recognizes standard cron expressions consisting of 5 fields.";
      tbl.innerHTML = "";
      return;
    }
    const startStr = t0.value || "2026-09-08T01:30";
    const start = Date.parse(startStr + ":00Z");             // 以「排程時區的牆上時間」看待
    let cur = start - (start % 60000) + 60000;               // 從下一分鐘開始找
    const fires = [];
    for (let i = 0; i < 366 * 24 * 60 && fires.length < 5; i++, cur += 60000) {
      if (matches(cron, new Date(cur))) fires.push(cur);
    }
    const off = OFFSETS[tz];
    const other = tz === "Asia/Taipei" ? "UTC" : "Asia/Taipei";     // 對照欄：另一個時區
    const rows = fires.map((wall, i) => {
      const instant = wall - off * 60000;                            // 轉成真正的時間點
      const shown = instant + OFFSETS[other] * 60000;
      const diff = tz !== "Asia/Taipei";                             // 沒寫時區＝UTC，台北要晚 8 小時
      return `<tr><td>第 ${i + 1} 次</td><td>${fmt(wall)}</td><td class="${diff ? "diff" : ""}">${fmt(shown)}</td></tr>`;
    }).join("");
    tbl.innerHTML =
      `<tr><th>觸發</th><th class="tz">排程時區（${tz}）</th><th>${other === "Asia/Taipei" ? "台北的人實際會看到" : "換算成 UTC"}</th></tr>` +
      (rows || `<tr><td colspan="3">一年內都不會觸發（檢查一下日與月的組合）</td></tr>`);
    msg.className = "msg";
    msg.textContent =
      `ScheduleDefinition(cron_schedule="${raw}", execution_timezone=${tz === "UTC" ? "None → UTC" : `"${tz}"`})`
      + `　→　從 ${startStr.replace("T", " ")} 起的接下來 5 次觸發`;
  }
  q.addEventListener("input", render);
  tzSel.addEventListener("change", render);
  t0.addEventListener("input", render);
  document.getElementById("cron-chips").addEventListener("click", (e) => {
    const b = e.target.closest("button[data-q]");
    if (!b) return;
    q.value = b.dataset.q;
    render();
  });
  // 預設起算時刻＝使用者「現在」的整分，讓表格看起來就是接下來會發生的事
  (function initNow() {
    const now = new Date();
    const p = (n) => String(n).padStart(2, "0");
    t0.value = `${now.getFullYear()}-${p(now.getMonth() + 1)}-${p(now.getDate())}T${p(now.getHours())}:${p(now.getMinutes())}`;
  })();
  render();
})();
"""

PANEL_STEPS = """
        <li>登入 molab（GitHub / Google）</li>
        <li>開啟課程 notebook，<b>Fork 成自己的副本</b>即可編輯</li>
        <li>從第一格往下全部執行（首次安裝套件約 1–2 分鐘）——<b>免費 CPU 環境即可</b>，不需要 GPU；排程與感測器全在暫存資料夾裡模擬，不連任何伺服器</li>
"""
