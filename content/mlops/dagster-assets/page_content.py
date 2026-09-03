"""課程頁內容區（純常數）。改完跑：python3 .claude/skills/make-lesson/scripts/page-fill.py content/mlops/dagster-assets
build.sh 不會部署這個檔；它是 index.html 內容區的正本。"""

TITLE = "Dagster 軟體定義資產：管線不是一串任務，是一張資料地圖"
DESCRIPTION = "Dagster 軟體定義資產詳解：@asset 一個函式就是一份資料、參數名自動連成血緣圖、中繼資料留下每次執行的證據、deps 只排順序、IO manager 讓「算什麼」與「存哪裡」分家、blocking 資產檢查擋住壞資料——molab 免費 CPU 環境全程實作。"
NB = "https://molab.marimo.io/github/skmygo/agentclass/blob/main/content/mlops/dagster-assets/dagster-assets_ext.py"

STYLE = r"""
  /* 語義色：藍＝資產與依賴、綠＝剛算好、橘＝過期、紅＝被閘門擋下 */
  :root { --c1: #4C72B0; --c2: #DD8452; --c3: #55A868; --cut: #C44E52; }
  a.golab { text-decoration: none; display: inline-flex; align-items: center; gap: 8px; }

  /* hero：資產地圖 */
  #dg-demo .ctl { display: flex; gap: 10px; flex-wrap: wrap; align-items: center; margin-bottom: 12px; font-size: 12.5px; }
  #dg-demo .ctl .hint { color: var(--ink-soft); }
  #dg-demo .sw { display: inline-flex; align-items: center; gap: 6px; font-weight: 800; border: 1.5px solid var(--grid); border-radius: 8px; padding: 5px 10px; cursor: pointer; font-family: var(--mono); }
  #dg-demo .sw input { accent-color: var(--cut); }
  #dg-demo .ctl button { font-family: var(--mono); font-size: 12.5px; padding: 5px 11px; border-radius: 8px; border: 1.5px solid var(--ink); background: #fff; color: var(--ink); cursor: pointer; }
  #dg-demo .ctl button:hover { background: var(--chip-bg); }
  #dg-demo .map { display: flex; align-items: stretch; gap: 2px; overflow-x: auto; }
  #dg-demo .arrow { display: flex; align-items: center; color: var(--ink-soft); font-size: 12px; flex: 0 0 auto; }
  #dg-demo .node { flex: 1 1 auto; min-width: 0; text-align: left; border: 2px dashed var(--grid); border-radius: 12px; padding: 8px 8px; background: #fff; color: var(--ink); cursor: pointer; font-family: var(--sans); transition: border-color .18s, background .18s; }
  #dg-demo .node:hover { border-color: var(--ink); }
  #dg-demo .node b { display: block; font-family: var(--mono); font-size: 11px; margin-bottom: 3px; color: var(--c1); white-space: nowrap; }
  #dg-demo .node .st { font-size: 11px; font-weight: 800; color: var(--ink-soft); }
  #dg-demo .node .mt { font-size: 11px; color: var(--ink-soft); font-family: var(--mono); margin-top: 3px; line-height: 1.45; }
  #dg-demo .node.fresh { border-style: solid; border-color: var(--c3); background: rgba(85,168,104,.10); }
  #dg-demo .node.fresh .st { color: var(--c3); }
  #dg-demo .node.stale { border-style: solid; border-color: var(--c2); background: rgba(221,132,82,.10); }
  #dg-demo .node.stale .st { color: var(--c2); }
  #dg-demo .node.blocked { border-style: solid; border-color: var(--cut); background: rgba(196,78,82,.10); }
  #dg-demo .node.blocked .st { color: var(--cut); }
  #dg-demo .chk { margin-top: 11px; font-family: var(--mono); font-size: 12px; background: var(--chip-bg); border-radius: 9px; padding: 8px 11px; line-height: 1.75; }
  #dg-demo .chk .bad { color: var(--cut); font-weight: 800; }
  #dg-demo .chk .good { color: var(--c3); font-weight: 800; }
  #dg-demo .log { margin-top: 8px; font-family: var(--mono); font-size: 11.5px; color: var(--ink-soft); line-height: 1.7; white-space: pre-wrap; overflow-wrap: anywhere; }
  #dg-demo .log .err { color: var(--cut); }
  @media (max-width: 620px) {
    #dg-demo .map { flex-direction: column; }
    #dg-demo .arrow { justify-content: center; transform: rotate(90deg); height: 14px; }
    #dg-demo .node { flex: 1 1 auto; }
  }

  table.cmp { width: 100%; border-collapse: collapse; font-size: 13.5px; margin: 14px 0; }
  table.cmp th, table.cmp td { border-bottom: 1px solid var(--grid); padding: 8px 10px; text-align: left; vertical-align: top; }
  table.cmp th { font-size: 12px; letter-spacing: .04em; color: var(--ink-soft); }
  .kbd { font-family: var(--mono); background: var(--chip-bg); padding: 1px 6px; border-radius: 5px; font-size: 13px; }
  .two { display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; margin: 14px 0; }
  .two div { border: 1.5px solid var(--grid); border-radius: 10px; padding: 10px 12px; font-size: 13.5px; }
  .two b { display: block; font-family: var(--mono); margin-bottom: 4px; }
  .two .a b { color: var(--c1); } .two .b b { color: var(--c2); }
  @media (max-width: 560px) { .two { grid-template-columns: 1fr; } }
"""

WRAP = r"""
<section id="hero">
  <span class="eyebrow">DAGSTER · SOFTWARE-DEFINED ASSETS · 03</span>
  <h1>Dagster 軟體定義資產：<br>管線不是一串任務，是一張資料地圖</h1>
  <p style="margin-top:18px">
    上一課你把最好的模型放進 Registry；但那份訓練資料是誰在什麼時候算出來的？
    凌晨兩點的 cron 跑了三支腳本，模型今天預測怪怪的——你查不到特徵表是哪一批資料算的、清資料丟掉了幾列，
    也沒辦法「只重算特徵、不重抓原始資料」。Dagster 把主角從<b>任務</b>換成<b>資產</b>：
    每一份資料就是一個函式，依賴自己連成一張圖。先點點看——
  </p>

  <div class="hero-demo" id="dg-demo">
    <div class="ctl">
      <span class="hint">點任何一個資產＝對它按 Materialize</span>
      <label class="sw"><input type="checkbox" id="dg-gate"> min_amount = 800</label>
      <button type="button" id="dg-reset">全部重來</button>
    </div>
    <div class="map" id="dg-map"></div>
    <div class="chk" id="dg-chk"></div>
    <div class="log" id="dg-log"></div>
  </div>

  <p class="note">
    列數、客戶數與錯誤訊息都是 notebook 的實測結果（同一組亂數種子）：清完 478 列、59 位客戶；
    把 <span class="kbd">min_amount</span> 拉到 800 只剩 106 列，低於品質閘門的 400 列底線。
  </p>
</section>

<section id="s1">
  <span class="eyebrow">01 · 資產</span>
  <h2>一個函式，就是一份資料</h2>
  <div class="codeblock">import dagster as dg

@dg.asset(description="模擬的原始訂單（含退款負值）", group_name="raw")
def raw_orders() -> pd.DataFrame:          # 函式名 = 資產名
    ...
    return pd.DataFrame({"order_id": ..., "customer": ..., "amount": ..., "returned": ...})

res = dg.materialize([raw_orders])         # 真的去算、存起來、記下一筆 materialization 事件
res.asset_value("raw_orders")              # 500 列，其中 22 筆金額為負</div>
  <p>
    <b>資產（asset）</b>是這一課唯一要記住的詞：一份「存在於某處、有人會用」的東西
    （一張表、一個模型檔、一份報表、一個向量索引），<b>加上「它是怎麼算出來的」那個函式</b>。
    腳本世界裡這兩件事是分開的——檔案在硬碟上，產生它的程式在某支 <span class="kbd">.py</span> 的某幾行；
    Dagster 要求你把它們綁在一起宣告。
  </p>
  <p>
    宣告不會產生資料，就像寫好食譜不等於做出菜。<b>實體化（materialize）</b>才是真的執行函式、
    把結果交給儲存層、並留下一筆事件（時間、run id、中繼資料）。正式部署時你不會自己呼叫
    <span class="kbd">materialize()</span>——UI 上按 Materialize、排程、感測器都會做這件事；
    notebook 裡直接呼叫，是為了讓每一步看得見。
  </p>
  <a class="golab" href="__NB__" target="_blank" rel="noopener">到 notebook 的 1️⃣ 節：第一個資產與 materialize</a>
</section>

<section id="s2">
  <span class="eyebrow">02 · 依賴成圖</span>
  <h2>參數名就是上游名：管線是推出來的，不是寫出來的</h2>
  <div class="codeblock">@dg.asset(group_name="clean")
def clean_orders(context, config: CleanConfig, raw_orders: pd.DataFrame) -> pd.DataFrame:
    ...                                    # 參數名 raw_orders = 上游資產名

@dg.asset(group_name="features")
def customer_features(clean_orders: pd.DataFrame) -> pd.DataFrame:
    ...

dg.materialize([raw_orders, clean_orders, customer_features])
# 執行順序：raw_orders → clean_orders → customer_features（沒有人寫過這行順序）</div>
  <p>
    Airflow 那類工具要你手寫 <span class="kbd">a &gt;&gt; b &gt;&gt; c</span>。管線小的時候沒問題；
    等到四十張表互相引用，那串箭頭遲早跟真實依賴對不上——有人加了一張表忘了接線，某天它就悄悄用到昨天的資料。
    Dagster 不讓你手寫順序：<b>圖是從程式碼推出來的</b>，程式怎麼寫、圖就長什麼樣，不會分岔。
    實測這條線清完剩 478 列（丟掉 22 筆退款）、彙總出 59 位客戶。
  </p>
  <p>
    既然名字就是契約，打錯一個字會怎樣？故意把 <span class="kbd">clean_orders</span> 寫成
    <span class="kbd">clean_order</span>，Dagster 在<b>組圖的時候</b>就擋下來——還沒有執行任何函式、
    沒有半筆資料被寫出去，而且它會猜你要的是哪個：
  </p>
  <div class="codeblock">DagsterInvalidDefinitionError: Input asset "["clean_order"]" is not produced by any of the
provided asset ops and is not one of the provided sources. Did you mean one of the following?
    ["clean_orders"]</div>
  <a class="golab" href="__NB__" target="_blank" rel="noopener">到 notebook 的 2️⃣ 節：依賴成圖、血緣圖、名字打錯</a>
</section>

<section id="s3">
  <span class="eyebrow">03 · 中繼資料</span>
  <h2>每一次執行都留下隨身紀錄</h2>
  <div class="codeblock">context.log.info(f"kept {len(df)} / {len(raw_orders)} rows")      # 日誌：給人當下讀，事後會被沖掉
context.add_output_metadata({                                    # 中繼資料：永久跟著這次實體化
    "rows": len(df),
    "dropped": len(raw_orders) - len(df),
    "preview": dg.MetadataValue.md(df.head(3).to_markdown(index=False)),
})</div>
  <p>
    「清資料那步是不是把太多列丟掉了？」——要回答這種問題，光有「跑成功了」不夠。
    中繼資料是跟著<b>那一次</b>實體化存下來的小抄：數字、字串、markdown、JSON、URL、檔案路徑都可以。
    數字類在 UI 上會自動畫成時間序列，「今天的列數突然剩一半」一眼就看得到，不用等模型爛掉才回頭查。
    實測這次記下 <span class="kbd">rows=478</span>、<span class="kbd">dropped=22</span> 與前三列預覽。
  </p>
  <a class="golab" href="__NB__" target="_blank" rel="noopener">到 notebook 的 3️⃣ 節：把 materialization 事件讀回來</a>
</section>

<section id="s4">
  <span class="eyebrow">04 · DEPS</span>
  <h2>只排順序、不傳資料——以及它最容易踩的坑</h2>
  <div class="codeblock">@dg.asset(deps=[customer_features], group_name="features")   # 傳函式物件，不是字串
def feature_report() -> dg.MaterializeResult:
    # 真實世界這裡會去讀 warehouse、產 PDF、寄信
    return dg.MaterializeResult(metadata={"recipients": 3, "status": "sent (simulated)"})</div>
  <p>
    寫成參數的依賴同時做了兩件事：<b>排順序</b> ＋ <b>把上游的值搬進來</b>。但「把報表寄出去」只要等
    <span class="kbd">customer_features</span> 算完就好，它自己會去讀資料倉儲；上游是一張 300 GB 的表時，
    你更不會想把它搬進 Python 記憶體。<span class="kbd">deps=[...]</span> 就是這種依賴：<b>有順序、有血緣、不傳值</b>，
    函式簽名裡不會出現上游的名字，通常回傳 <span class="kbd">MaterializeResult</span>——「我做完了，這是我的紀錄」。
  </p>
  <p>
    坑在這裡：<span class="kbd">deps</span> 也吃字串，而字串<b>打錯不會報錯</b>。
    在 Dagster 眼裡 <span class="kbd">"clean_order"</span> 是一個合法的資產名，只是這份定義裡沒人負責算它——
    它變成一個<b>外部資產</b>（別的團隊、別的工具產生的）。實測結果：
  </p>
  <div class="codeblock">@dg.asset(deps=["clean_order"])            # 少一個 s，Dagster 不會擋
def mail_report() -> dg.MaterializeResult: ...

res = dg.materialize([raw_orders, clean_orders, mail_report])
res.success                                # True ← 什麼都沒壞
[ev.asset_key.to_user_string() for ev in res.get_asset_materialization_events()]
# ['mail_report', 'raw_orders', 'clean_orders']   ← 報表比資料還早跑完</div>
  <p>
    這是最難抓的那種 bug：run 是綠的、沒有任何訊息，只是報表用到的資料比你以為的舊。
    <b>能傳函式物件就別傳字串</b>——打錯字時 Python 自己就會 <span class="kbd">NameError</span>，連 Dagster 都不用出手。
    真的要用字串（跨檔案、上游是別人的資產），就在 <span class="kbd">Definitions</span> 建好後檢查圖上有沒有意料之外的外部資產。
  </p>
  <a class="golab" href="__NB__" target="_blank" rel="noopener">到 notebook 的 4️⃣ 節：deps 與打錯字的血緣圖</a>
</section>

<section id="s5">
  <span class="eyebrow">05 · IO MANAGER</span>
  <h2>「算什麼」與「存哪裡」分家</h2>
  <div class="codeblock">class CsvIOManager(dg.ConfigurableIOManager):
    root: str
    def handle_output(self, context, obj):    # 資產算完 → 存
        obj.to_csv(self._path(context), index=False)
    def load_input(self, context):            # 下游要用 → 讀
        return pd.read_csv(self._path(context))

dg.materialize([raw_orders, clean_orders, customer_features],
               resources={"io_manager": CsvIOManager(root=CSV_ROOT)})   # 只換這一行</div>
  <p>
    你的資產函式裡沒有一行 <span class="kbd">to_csv</span>／<span class="kbd">read_csv</span>，
    那 <span class="kbd">clean_orders</span> 的 DataFrame 是誰存的、又是誰讀給下游的？
    答案是 <b>IO manager</b>。預設的 <span class="kbd">fs_io_manager</span> 把每個資產 pickle 成一個檔案
    （檔名＝資產名，沒有副檔名）；換成上面這個 CSV 版之後，落地變成
    <span class="kbd">['clean_orders.csv', 'customer_features.csv', 'raw_orders.csv']</span>——
    <b>三個資產函式一個字都沒改</b>。今天存本機、明天上 S3、後天寫進 Snowflake，都是換這一個元件的事。
  </p>
  <div class="two">
    <div class="a"><b>selection=[customer_features]</b>只算這一個；上游 <span class="kbd">clean_orders</span> 由 IO manager 從上次的結果載回來（事件裡看得到 1 筆 <span class="kbd">LOADED_INPUT</span>）。</div>
    <div class="b"><b>selection="clean_orders*"</b>它自己＋所有下游，實測實體化 <span class="kbd">['clean_orders', 'customer_features']</span>，<span class="kbd">raw_orders</span> 不用重抓。</div>
  </div>
  <p>
    這就是開頭那個「可以嗎」的答案：可以，前提是<b>上游真的在這個 storage 裡算過</b>。
    換一台機器、換一個 storage 目錄、或那個資產從來沒被實體化過，載入就會失敗——
    這是新手最常撞的一堵牆（本課測驗會再考一次）。
  </p>
  <a class="golab" href="__NB__" target="_blank" rel="noopener">到 notebook 的 5️⃣ 節：換 IO manager、只重算下游</a>
</section>

<section id="s6">
  <span class="eyebrow">06 · ASSET CHECK</span>
  <h2>資料不對，就不要拿去訓模型</h2>
  <div class="codeblock">@dg.asset_check(asset=clean_orders, description="清完不該再有負金額")     # 不 blocking
def no_negative_amount(clean_orders: pd.DataFrame) -> dg.AssetCheckResult:
    bad = int((clean_orders["amount"] < 0).sum())
    return dg.AssetCheckResult(passed=bad == 0, severity=dg.AssetCheckSeverity.WARN,
                               metadata={"bad_rows": bad})

@dg.asset_check(asset=clean_orders, blocking=True)                       # 這個會擋下游
def enough_rows(clean_orders: pd.DataFrame) -> dg.AssetCheckResult:
    n = len(clean_orders)
    return dg.AssetCheckResult(passed=n >= 400, severity=dg.AssetCheckSeverity.ERROR,
                               metadata={"rows": n, "min_rows": 400})

dg.materialize([raw_orders, clean_orders, customer_features,
                no_negative_amount, enough_rows])      # 檢查跟資產放同一個清單</div>
  <p>
    上游今天改了一個欄位定義，你的清理邏輯照跑不誤，只是留下的列數掉了一大半。程式沒拋例外、run 是綠的、
    模型照樣訓完上線——三天後才有人發現預測全歪。<b>資產檢查</b>就是把「資料應該長什麼樣」寫成程式碼掛在資產上：
    像單元測試，但測的是資料，而且每次實體化後自動跑，結果跟資產一起記錄。
  </p>
  <p>
    兩個常被混在一起的旋鈕其實是分開的：<span class="kbd">severity</span>（有多嚴重，寫在結果上，<b>預設就是 ERROR</b>，
    想降級寫 <span class="kbd">AssetCheckSeverity.WARN</span>）只影響這筆紀錄長什麼樣；
    <span class="kbd">blocking=True</span>（寫在裝飾器上）才是真的踩煞車。
    實測把 <span class="kbd">min_amount</span> 拉到 800，只剩 106 列（門檻拉到 250 就守不住 400 列底線）：
  </p>
  <div class="codeblock">res.success                # False
[ev.asset_key.to_user_string() for ev in res.get_asset_materialization_events()]
# ['raw_orders', 'clean_orders']        ← 沒有 customer_features，下游真的被擋住了

dagster._core.errors.DagsterAssetCheckFailedError: 1 blocking asset check failed with ERROR severity:
clean_orders: enough_rows</div>
  <p>
    <span class="kbd">no_negative_amount</span> 這次照樣執行、照樣通過——它不 blocking，就算失敗也只是留下一筆紀錄。
    資產函式自己丟例外（上游 schema 變了、API 掛了）則是另一種失敗：Dagster 把你的例外包起來，
    外層是 <span class="kbd">DagsterExecutionStepExecutionError</span>，原始的
    <span class="kbd">ValueError: boom: upstream schema changed</span> 收在 <span class="kbd">error.cause</span> 裡；
    下游一樣不跑，而且該資產在圖上維持「上一次成功的樣子」，不會被半成品覆蓋。
  </p>
  <a class="golab" href="__NB__" target="_blank" rel="noopener">到 notebook 的 6️⃣ 節：閘門關上的那一刻＋拉桿互動</a>
</section>

<section id="s7">
  <span class="eyebrow">07 · DEFINITIONS</span>
  <h2>收成一份，交給 <span class="kbd">dagster dev</span></h2>
  <div class="codeblock">defs = dg.Definitions(
    assets=[raw_orders, clean_orders, customer_features, feature_report],
    asset_checks=[no_negative_amount, enough_rows],
    resources={"io_manager": CsvIOManager(root=CSV_ROOT)},
)
# $ dagster dev -f my_pipeline.py       → http://localhost:3000</div>
  <p>
    <span class="kbd">Definitions</span> 是「這個專案有哪些東西」的唯一入口：資產、檢查、資源，
    還有下一課的排程與感測器。<span class="kbd">dagster dev</span> 起來之後，UI 會畫出你在 notebook 裡看到的同一張圖，
    另外標上每個資產的最近實體化時間、中繼資料趨勢、檢查狀態；你可以點任何一個資產按 Materialize、只重算某個子集、
    翻每次 run 的日誌。
  </p>
  <p>
    它也是整體檢查的地方：資產名<b>全域唯一</b>，撞名不是警告而是錯誤——否則「這份資料是誰算的」會有兩個答案。
    實測訊息：<span class="kbd">DagsterInvalidDefinitionError: Duplicate asset key: AssetKey(['clean_orders'])</span>。
    真實專案常用 <span class="kbd">AssetKey(["marketing", "clean_orders"])</span> 這種多層命名把不同來源分開。
  </p>
  <a class="golab" href="__NB__" target="_blank" rel="noopener">到 notebook 的 7️⃣ 節：Definitions 與撞名</a>
</section>

<section id="s8">
  <span class="eyebrow">08 · 實戰</span>
  <h2>換你動手</h2>
  <div class="ex">
    <span class="lv">LEVEL 1</span>
    <p>加一個資產 <span class="kbd">top_customers</span>：吃 <span class="kbd">customer_features</span>，回傳 <span class="kbd">total</span> 最高的 5 位。實體化整條線，確認它出現在血緣圖上、中繼資料記了 5 列。</p>
  </div>
  <div class="ex">
    <span class="lv">LEVEL 2</span>
    <p>幫 <span class="kbd">customer_features</span> 加一個 <span class="kbd">blocking=True</span> 的檢查：<span class="kbd">return_rate</span> 必須在 0–1 之間且沒有 NaN。故意弄壞一筆資料，看它擋不擋得住下游。</p>
  </div>
  <div class="ex">
    <span class="lv">LEVEL 3</span>
    <p>把 <span class="kbd">CsvIOManager</span> 改成依型別決定格式：DataFrame 存 CSV、其他型別存 pickle。驗證：回傳 <span class="kbd">MaterializeResult</span> 的 <span class="kbd">feature_report</span> 根本不會經過 IO manager。</p>
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
      <h3>目前三支腳本靠 cron 串起來：2:00 抓訂單、2:10 清資料、2:20 算特徵。今天特徵表怪怪的，你想知道它是哪一批資料算的、也想只重算特徵。最該做的第一步是？</h3>
      <div class="quiz-opts">
        <button type="button" class="quiz-opt" data-k="A">A. 把三支腳本合併成一支，中間加 print 印出每一步的列數，日誌收進檔案</button>
        <button type="button" class="quiz-opt" data-k="B">B. 把 cron 換成排程器，讓三個任務用 <code>a &gt;&gt; b &gt;&gt; c</code> 明確宣告先後順序</button>
        <button type="button" class="quiz-opt" data-k="C">C. 把三份產出宣告成三個資產（下游把上游寫成參數），用 <code>add_output_metadata</code> 記列數，之後就能只重算某一個</button>
        <button type="button" class="quiz-opt" data-k="D">D. 每次跑完把中間檔案複製一份到 <code>backup/YYYY-MM-DD/</code>，要查就去翻備份</button>
      </div>
      <div class="quiz-fb" aria-live="polite"><p>問題的根源是「管線記錄的是跑了哪些腳本，不是產出了哪些資料」。宣告成資產之後，三件事一次到位：依賴自動成圖（不用手寫順序）、每次實體化留下時間與中繼資料（列數就在那裡）、可以只選一個資產重算而上游從儲存層載回。A 加了日誌但沒有結構，日誌會被沖掉、也還是不能只重算一段；B 只解決順序，「那張表是什麼時候、用什麼算的」依然無解；D 是手工版的血緣，量一大就沒人維護，而且沒有回答「誰算的」。</p></div>
    </div>

    <div class="quiz-q" data-answer="B">
      <p class="quiz-tag">Q2 <span class="qtype dx">錯誤診斷</span></p>
      <h3>報表資產每天都「成功」，但業務說報表數字比實際慢一天。程式與執行結果如下，最可能的原因是？</h3>
      <div class="codeblock">@dg.asset(deps=["clean_order"])          # 報表：等資料清好再寄
def mail_report() -> dg.MaterializeResult: ...

>>> res = dg.materialize([raw_orders, clean_orders, mail_report])
>>> res.success
True
>>> [ev.asset_key.to_user_string() for ev in res.get_asset_materialization_events()]
['mail_report', 'raw_orders', 'clean_orders']</div>
      <div class="quiz-opts">
        <button type="button" class="quiz-opt" data-k="A">A. <code>deps</code> 只保證順序不保證資料新鮮度，要改成把 <code>clean_orders</code> 寫成參數才會等它</button>
        <button type="button" class="quiz-opt" data-k="B">B. <code>deps</code> 的字串打錯了（少一個 s），Dagster 把 <code>clean_order</code> 當成沒人負責算的外部資產，所以報表沒有等清資料就先跑了</button>
        <button type="button" class="quiz-opt" data-k="C">C. IO manager 讀到了上一次的 <code>clean_orders</code> 快取，要清掉 storage 目錄才會拿到新的</button>
        <button type="button" class="quiz-opt" data-k="D">D. <code>materialize</code> 的清單順序決定執行順序，把 <code>mail_report</code> 移到最後就好</button>
      </div>
      <div class="quiz-fb" aria-live="polite"><p>關鍵線索在執行順序：報表跑在 <code>clean_orders</code> <b>之前</b>（這次甚至是第一個），而 run 完全沒有報錯。<code>deps</code> 接受字串，而任何字串在 Dagster 眼裡都是一個合法的資產名——打錯的 <code>clean_order</code> 變成一個外部資產（圖上有節點、沒人負責算），報表於是「沒有任何上游要等」。修法是傳函式物件 <code>deps=[clean_orders]</code>，打錯字時 Python 直接 <code>NameError</code>。A 說反了：<code>deps</code> 只要名字對就會正確排序，這裡是名字不對；C 症狀相似但原因不同，這次 <code>clean_orders</code> 確實有重算，只是排在報表後面；D 是常見誤解——清單順序不影響執行順序，順序完全由依賴推導。</p></div>
    </div>

    <div class="quiz-q" data-answer="A">
      <p class="quiz-tag">Q3 <span class="qtype">情境題</span></p>
      <h3>上游偶爾會送來只有零星幾列的殘缺資料。你不希望模型拿這種資料去訓練，但也不想因此讓整條管線變得難維護。最佳做法是？</h3>
      <div class="quiz-opts">
        <button type="button" class="quiz-opt" data-k="A">A. 幫 <code>clean_orders</code> 加一個 <code>blocking=True</code> 的 <code>@dg.asset_check</code>，列數不足就讓下游不執行</button>
        <button type="button" class="quiz-opt" data-k="B">B. 在訓練資產的函式開頭寫 <code>assert len(df) >= 400</code>，不夠就丟例外</button>
        <button type="button" class="quiz-opt" data-k="C">C. 加一個非 blocking 的檢查記錄列數，再設一條「列數低於 400 就寄信」的告警規則</button>
        <button type="button" class="quiz-opt" data-k="D">D. 在 <code>clean_orders</code> 裡發現列數不足時，直接回傳上一次的結果，讓下游永遠有資料可用</button>
      </div>
      <div class="quiz-fb" aria-live="polite"><p>blocking 的資產檢查正是為這件事設計的：條件寫在資產旁邊（誰在管這份資料的品質一目了然）、每次實體化自動跑、不合格時下游根本不會開始，而且結果會留在 UI 上有歷史可查。B 能擋住但把資料品質的判斷藏進訓練程式裡，換一個下游就要再寫一次，UI 上也只會看到「訓練失敗」而不是「資料不合格」；C 只是提醒，信件寄出去的時候模型早就用爛資料訓完了；D 最危險——它讓管線「看起來一直是好的」，血緣紀錄還會顯示今天算過，實際上是舊資料，屬於那種三個月後才爆的錯。</p></div>
    </div>

    <div class="quiz-q" data-answer="D">
      <p class="quiz-tag">Q4 <span class="qtype dx">錯誤診斷</span></p>
      <h3>同事在自己電腦第一次跑這個專案，想直接算最下游的特徵表，結果如下。最可能的原因與修法？</h3>
      <div class="codeblock">res = dg.materialize([raw_orders, clean_orders, customer_features],
                     selection=[customer_features], instance=my_instance)

dagster._core.errors.DagsterExecutionLoadInputError: Error occurred while loading input
"clean_orders" of step "customer_features":
FileNotFoundError: [Errno 2] No such file or directory: '/tmp/tmp7ol1w4mr/storage/clean_orders'</div>
      <div class="quiz-opts">
        <button type="button" class="quiz-opt" data-k="A">A. <code>customer_features</code> 的參數名跟上游資產名對不上，Dagster 找不到 <code>clean_orders</code></button>
        <button type="button" class="quiz-opt" data-k="B">B. <code>/tmp</code> 沒有寫入權限，把 storage 目錄換到家目錄就好</button>
        <button type="button" class="quiz-opt" data-k="C">C. <code>clean_orders</code> 的 blocking 檢查失敗了，所以它沒有被寫出去</button>
        <button type="button" class="quiz-opt" data-k="D">D. <code>selection</code> 只選了下游，而 <code>clean_orders</code> 在這個 instance 從來沒被實體化過；先把整條線跑一次（不給 <code>selection</code>），之後才有東西可以載回</button>
      </div>
      <div class="quiz-fb" aria-live="polite"><p>「只重算下游」的前提是上游的結果<b>已經存在這個 instance 的 storage 裡</b>；全新的環境什麼都沒有，IO manager 去讀 <code>storage/clean_orders</code> 自然找不到檔案。訊息的兩層說得很清楚：外層是「載入 <code>customer_features</code> 的輸入 <code>clean_orders</code> 時出錯」，底層是 <code>FileNotFoundError</code>。Dagster 不會自動幫你補跑上游——它只做你叫它做的事。A 的症狀不同：參數名對不上會在組圖時就被擋下，訊息是 <code>Input asset ... is not produced by any of the provided asset ops</code>，而且根本跑不到載入這一步；B 誤讀訊息，是「檔案不存在」不是「不能寫」；C 也錯，檢查失敗的訊息是 <code>DagsterAssetCheckFailedError</code>，長得完全不一樣。</p></div>
    </div>

    <div class="quiz-q" data-answer="B">
      <p class="quiz-tag">Q5 <span class="qtype">情境題</span></p>
      <h3>資料工程團隊要求：所有中間資料從本機 pickle 改存成公司資料湖上的 Parquet。你的專案有 30 個資產。工作量最小、風險最低的做法是？</h3>
      <div class="quiz-opts">
        <button type="button" class="quiz-opt" data-k="A">A. 在每個資產函式最後加一行 <code>df.to_parquet(...)</code>，下游改成自己去讀那個路徑</button>
        <button type="button" class="quiz-opt" data-k="B">B. 寫一個 Parquet 版的 IO manager，在 <code>Definitions</code> 的 <code>resources</code> 換掉 <code>io_manager</code>，30 個資產函式不動</button>
        <button type="button" class="quiz-opt" data-k="C">C. 新增 30 個「上傳」資產，各自用 <code>deps</code> 掛在原資產後面，負責把結果寫成 Parquet</button>
        <button type="button" class="quiz-opt" data-k="D">D. 保留現在的寫法，加一支每天跑的腳本把 storage 目錄裡的 pickle 全部轉成 Parquet</button>
      </div>
      <div class="quiz-fb" aria-live="polite"><p>「算什麼」與「存哪裡」分家就是為了這一天：IO manager 只要回答 <code>handle_output</code>／<code>load_input</code> 兩個問題，換掉它，30 個資產函式一個字都不用改，也不會有人漏改。A 把儲存細節塞回每個函式裡，下游還要自己知道路徑，等於放棄了 Dagster 幫你管的那一層，下次再換格式又要改 30 個地方；C 讓資產數量翻倍、血緣圖被搬運節點灌爆，而且真正的資料還是躺在 pickle 裡；D 是事後補救，管線執行當下用的仍是舊格式，轉檔腳本一失敗就出現「兩份不同步的資料」。</p></div>
    </div>

    <div class="quiz-score" data-score></div>
  </div>
</section>

<div class="endnav">
  <a href="/dagster-automation/">
    <span class="tag">下一課</span>
    <b>Dagster 自動化：排程、感測器、分割與自動化條件 →</b>
  </a>
  <a href="/mlops/">
    <span class="tag">主題</span>
    <b>‹ 回「MLOps 自動化技術」課程列表</b>
  </a>
</div>
"""

SCRIPT = r"""
/* ═══ hero 互動：資產地圖（列數、客戶數、錯誤訊息＝notebook 實測）═══ */
(function () {
  const NODES = [
    { k: "raw_orders",        role: "從交易系統撈訂單", ok: "500 列 · 22 筆負值", gate: "500 列 · 22 筆負值" },
    { k: "clean_orders",      role: "丟掉負值與太小的單", ok: "478 列 · 丟掉 22",  gate: "106 列 · 丟掉 394" },
    { k: "customer_features", role: "每位客戶一列",     ok: "59 位客戶",          gate: "" },
    { k: "feature_report",    role: "寄報表（deps）",   ok: "recipients 3",       gate: "" },
  ];
  const LABEL = { idle: "未實體化", fresh: "剛算好 ✓", stale: "過期（上游變了）", blocked: "被閘門擋下" };
  const map = document.getElementById("dg-map");
  const chk = document.getElementById("dg-chk");
  const log = document.getElementById("dg-log");
  const gateEl = document.getElementById("dg-gate");
  let state = NODES.map(() => "idle");
  let check = null;

  NODES.forEach((n, i) => {
    if (i > 0) { const a = document.createElement("span"); a.className = "arrow"; a.textContent = "▸"; map.appendChild(a); }
    const b = document.createElement("button");
    b.type = "button"; b.className = "node"; b.dataset.i = i;
    b.addEventListener("click", () => run(i));
    map.appendChild(b);
  });

  function paint() {
    const gate = gateEl.checked;
    map.querySelectorAll(".node").forEach((el) => {
      const i = +el.dataset.i, n = NODES[i], st = state[i];
      el.className = "node " + (st === "idle" ? "" : st);
      const meta = st === "fresh" ? (gate ? n.gate : n.ok) : "";
      el.innerHTML = `<b>${n.k}</b><span class="st">${LABEL[st]}</span><div class="mt">${meta || n.role}</div>`;
    });
    if (!check) {
      chk.innerHTML = "檢查還沒跑過——實體化 <b>clean_orders</b> 或它的下游，兩個 asset check 就會跟著執行。";
    } else {
      const pass = check.rows >= 400;
      chk.innerHTML =
        `no_negative_amount　bad_rows = 0　<span class="good">✓ 通過</span>（WARN，不擋路）<br>` +
        `enough_rows　　　　rows = ${check.rows}（min 400）　` +
        (pass ? `<span class="good">✓ 通過</span>` : `<span class="bad">✗ 失敗</span>`) +
        `（ERROR，blocking）`;
    }
  }

  function run(i) {
    const gate = gateEl.checked;
    const ran = [], blocked = [];
    let failed = false;
    for (let j = 0; j <= i; j++) {
      if (failed) { state[j] = "blocked"; blocked.push(NODES[j].k); continue; }
      state[j] = "fresh"; ran.push(NODES[j].k);
      if (NODES[j].k === "clean_orders") {
        check = { rows: gate ? 106 : 478 };
        if (gate) failed = true;
      }
    }
    const staled = [];
    for (let j = i + 1; j < NODES.length; j++) {
      if (state[j] === "fresh") { state[j] = "stale"; staled.push(NODES[j].k); }
    }
    let out = `materialize([${NODES.slice(0, i + 1).map((n) => n.k).join(", ")}])\n`;
    out += `→ success = ${failed ? "False" : "True"}　實體化：[${ran.join(", ")}]`;
    if (failed) {
      out += `\n<span class="err">DagsterAssetCheckFailedError: 1 blocking asset check failed with ERROR severity:\nclean_orders: enough_rows</span>`;
      if (blocked.length) out += `\n${blocked.join("、")} 沒有執行——上游的品質閘門沒過。`;
    }
    if (staled.length) out += `\n${staled.join("、")} 變成「過期」：它們的上游剛剛重算了。`;
    log.innerHTML = out;
    paint();
  }

  gateEl.addEventListener("change", () => {
    for (let j = 1; j < NODES.length; j++) if (state[j] !== "idle") state[j] = "stale";
    check = null;
    log.innerHTML = gateEl.checked
      ? "min_amount 從 0 改成 800——設定變了，清資料以後的每一份資料都不算數了。\n再點 feature_report 跑一次整條線看看。"
      : "min_amount 改回 0。再跑一次，閘門就會放行。";
    paint();
  });

  document.getElementById("dg-reset").addEventListener("click", () => {
    state = NODES.map(() => "idle"); check = null;
    log.innerHTML = "點任何一個資產，Dagster 會把它需要的上游一起算出來。";
    paint();
  });

  log.innerHTML = "點任何一個資產，Dagster 會把它需要的上游一起算出來。";
  paint();
})();
"""

PANEL_STEPS = """
        <li>登入 molab（GitHub / Google）</li>
        <li>開啟課程 notebook，<b>Fork 成自己的副本</b>即可編輯</li>
        <li>從第一格往下全部執行（首次安裝套件約 1–2 分鐘）——<b>免費 CPU 環境即可</b>，不需要 GPU；全部在暫存資料夾裡跑，不連任何伺服器</li>
"""
