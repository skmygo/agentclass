"""課程頁內容區（純常數）。改完跑：python3 .claude/skills/make-lesson/scripts/page-fill.py content/mlops/data-validation
build.sh 不會部署這個檔；它是 index.html 內容區的正本。"""

TITLE = "資料驗證：用 pandera 幫資料寫合約"
DESCRIPTION = "管線最常見的故障不是程式 bug，是上游資料悄悄變了——欄位改名、單位變了、多了 NaN、類別多一個新值，模型照樣算、只是算錯。用 pandera 在入口簽一份合約：lazy 驗證一次列出全部違約、coerce 與 strict 各擋什麼、合約進版控的 YAML 陷阱，最後接進 Dagster blocking check 讓壞資料擋住下游。molab 免費環境全程實作。"
NB = "https://molab.marimo.io/github/skmygo/agentclass/blob/main/content/mlops/data-validation/data-validation_ext.py"

STYLE = r"""
  /* 語義色：藍＝合約條文、紅＝違約／擋下、綠＝通過／放行、橘＝上游送來的變化 */
  :root { --c1: #4C72B0; --c2: #DD8452; --c3: #55A868; --cut: #C44E52; }
  a.golab { text-decoration: none; display: inline-flex; align-items: center; gap: 8px; }

  /* hero：合約檢查機 */
  #dv-demo .dv-hint { font-size: 13px; color: var(--ink-soft); margin: 0 0 10px; line-height: 1.7; }
  #dv-demo .dv-scroll { overflow-x: auto; -webkit-overflow-scrolling: touch; margin: 0 -2px; padding: 0 2px 2px; }
  #dv-demo table { border-collapse: collapse; font-family: var(--mono); font-size: 12.5px; min-width: 330px; width: 100%; }
  #dv-demo th { font-size: 11px; letter-spacing: .04em; color: var(--ink-soft); font-weight: 700;
    text-align: left; padding: 4px 6px; border-bottom: 1.5px solid var(--grid); white-space: nowrap; }
  #dv-demo td { padding: 2px; border-bottom: 1px solid var(--grid); }
  #dv-demo button { font-family: var(--mono); color: var(--ink); cursor: pointer; }
  #dv-demo td button { width: 100%; min-width: 62px; text-align: left; font-size: 12.5px; padding: 5px 7px;
    border-radius: 7px; border: 1.5px solid transparent; background: transparent; transition: background .12s, border-color .12s; }
  #dv-demo td button:hover { background: var(--chip-bg); }
  #dv-demo td button.bad { border-color: var(--cut); background: rgba(196, 78, 82, .10); color: var(--cut); font-weight: 700; }
  #dv-demo th button.dv-col { font-size: 11px; letter-spacing: .04em; font-weight: 700; color: var(--ink-soft);
    background: transparent; border: 1.5px dashed var(--grid); border-radius: 6px; padding: 2px 7px; }
  #dv-demo th button.dv-col:hover { background: var(--chip-bg); }
  #dv-demo th button.dv-col.bad { border-color: var(--c2); border-style: solid; color: var(--c2); background: rgba(221, 132, 82, .12); }
  #dv-demo .dv-verdict { margin: 14px 0 10px; padding: 9px 12px; border-radius: 10px; font-size: 13.5px; line-height: 1.6;
    border: 1.5px solid var(--grid); }
  #dv-demo .dv-verdict.pass { border-color: var(--c3); background: rgba(85, 168, 104, .10); }
  #dv-demo .dv-verdict.block { border-color: var(--cut); background: rgba(196, 78, 82, .10); }
  #dv-demo .dv-verdict b { font-weight: 800; }
  #dv-demo .dv-fc th { font-size: 10.5px; }
  #dv-demo .dv-fc td { font-family: var(--mono); font-size: 11.5px; padding: 4px 6px; color: var(--ink); white-space: nowrap; }
  #dv-demo .dv-fc td.chk { color: var(--cut); font-weight: 700; }
  #dv-demo .dv-fc td.ctx { color: var(--ink-soft); }
  #dv-demo .dv-empty { font-size: 12.5px; color: var(--ink-soft); padding: 8px 2px; font-style: italic; }
  #dv-demo .dv-reset { margin-top: 10px; font-size: 12.5px; padding: 4px 11px; border-radius: 8px;
    border: 1.5px solid var(--grid); background: #fff; }
  #dv-demo .dv-reset:hover { background: var(--chip-bg); }

  /* 教學欄在桌機也只有視窗的一半寬——對照表一律包進可橫捲的容器並給下限寬，
     否則多欄表格會被擠成一字一行（視窗層的 media query 擋不住這件事） */
  .tw { overflow-x: auto; -webkit-overflow-scrolling: touch; margin: 14px 0; }
  table.cmp { width: 100%; min-width: 440px; border-collapse: collapse; font-size: 13.5px; margin: 0; }
  table.cmp.w4 { min-width: 520px; }
  table.cmp.w5 { min-width: 540px; }
  table.cmp th, table.cmp td { border-bottom: 1px solid var(--grid); padding: 8px 10px; text-align: left; vertical-align: top; }
  table.cmp th { font-size: 12px; letter-spacing: .04em; color: var(--ink-soft); white-space: nowrap; }
  table.cmp td.ok { color: var(--c3); font-weight: 700; }
  table.cmp td.no { color: var(--cut); font-weight: 700; }
  table.cmp code { font-size: 12.5px; }
  .kbd { font-family: var(--mono); background: var(--chip-bg); padding: 1px 6px; border-radius: 5px; font-size: 13px; }
"""

WRAP = r'''
<section id="hero">
  <span class="eyebrow">DATA VALIDATION · 補充 D · 09</span>
  <h1>資料驗證：<br>用 pandera 幫資料寫合約</h1>
  <p style="margin-top:18px">
    管線最貴的故障，通常沒有錯誤訊息：上游把金額的單位從元改成分、把 <span class="kbd">amount</span> 改名成
    <span class="kbd">total</span>、多送一個沒見過的國家代碼——你的程式照樣跑完，報表照樣寄出，只是全錯。
    <b>資料驗證就是在入口簽一份合約</b>：這批資料應該長什麼樣，寫成程式碼，每一批都對一次。
    下面這台檢查機就是一份合約——點格子把值弄壞，看它怎麼回應：
  </p>

  <div class="hero-demo" id="dv-demo">
    <p class="dv-hint">
      點任何一格，把值換成「上游可能送來的意外」（再點一次換下一種、繞回乾淨值）；
      點欄名 <b>amount</b> 可以模擬上游把它改名成 <b>total</b>。
    </p>
    <div class="dv-scroll">
      <table>
        <thead>
          <tr>
            <th>order_id</th>
            <th>customer</th>
            <th><button type="button" id="dv-rename" class="dv-col">amount</button></th>
            <th>country</th>
          </tr>
        </thead>
        <tbody id="dv-rows"></tbody>
      </table>
    </div>
    <div class="dv-verdict" id="dv-verdict"></div>
    <div class="dv-scroll">
      <table class="dv-fc">
        <thead>
          <tr><th>schema_context</th><th>column</th><th>check</th><th>failure_case</th><th>index</th></tr>
        </thead>
        <tbody id="dv-fc"></tbody>
      </table>
    </div>
    <div id="dv-none" class="dv-empty"></div>
    <button type="button" class="dv-reset" id="dv-reset">回到乾淨資料</button>
  </div>

  <p class="note">
    表格是 notebook 那份訂單資料的前 6 列；<span class="kbd">check</span> 欄位的字串
    （<span class="kbd">greater_than(0)</span>、<span class="kbd">isin(['TW', 'JP', 'US'])</span>、
    <span class="kbd">not_nullable</span>、<span class="kbd">field_uniqueness</span>…）
    全部是 notebook 的實測輸出（pandera 0.33）——你在自己的管線上看到的就是這些字。
  </p>
</section>

<section id="s1">
  <span class="eyebrow">01 · 為什麼</span>
  <h2>不會拋例外的那種壞掉</h2>
  <p>
    上一課的模型監控處理「模型上線之後」——用統計量看輸入分佈有沒有慢慢飄走。這一課處理更前面的一步：
    <b>資料剛進管線的那一刻</b>。因為大部分的資料事故，在監控看到之前就已經污染了下游。
  </p>
  <div class="tw">
    <table class="cmp">
      <tr><th>上游做了什麼</th><th>你的程式會怎樣</th><th>你什麼時候會知道</th></tr>
      <tr><td>欄位改名（<code>amount</code> → <code>total</code>）</td><td class="no">KeyError，會炸</td><td>馬上（這是最幸運的一種）</td></tr>
      <tr><td>單位變了（元 → 分）</td><td>照算，答案全錯</td><td>有人覺得數字怪怪的時候</td></tr>
      <tr><td>多了一批 <code>NaN</code></td><td>平均值悄悄偏移，或某些列被靜靜丟掉</td><td>可能永遠不會</td></tr>
      <tr><td>類別欄多一個新值</td><td>one-hot 多出沒見過的欄，或被當成未知值</td><td>模型準確率慢慢掉</td></tr>
      <tr><td>主鍵重複（抓了兩次）</td><td>每個客戶被算兩次，指標整體膨脹</td><td>季報對不起來的時候</td></tr>
    </table>
  </div>
  <p>
    第一列以外，<b>全部都不會拋例外</b>。管線很開心地把錯的答案算完、存好、發出去——這才是最貴的失敗，
    因為它會一路傳到報表、模型與決策，而且很久以後才被發現。
  </p>
  <p>
    資料驗證換掉的就是這件事：<b>把安靜的錯誤變成吵鬧的錯誤</b>。做法不是統計，是合約——
    把「這份資料應該長什麼樣」寫成程式碼，每一批進來都對一次；不合約就擋下來，
    而且說清楚是哪一列、哪一欄、違反哪一條。<span class="kbd">pandera</span> 就是做這件事的套件：
    語法像 pydantic，但主角是 DataFrame。
  </p>
  <a class="golab" href="__NB__" target="_blank" rel="noopener">到 notebook 的 1️⃣ 節：500 筆假訂單與它的合約</a>
</section>

<section id="s2">
  <span class="eyebrow">02 · 第一份合約</span>
  <h2>一本字典：欄位名 → 這一欄的規矩</h2>
  <div class="codeblock">import pandera.pandas as pa      # 注意這個路徑：pandas 後端在子模組裡（實測 pandera 0.33.1）

order_schema = pa.DataFrameSchema(
    {
        "order_id": pa.Column(int,   pa.Check.ge(0), unique=True),
        "customer": pa.Column(int,   pa.Check.between(1, 59)),
        "amount":   pa.Column(float, pa.Check.gt(0), nullable=False),
        "returned": pa.Column(bool),
        "country":  pa.Column(str,   pa.Check.isin(["TW", "JP", "US"])),
    },
    checks=pa.Check(lambda d: len(d) >= 400, error="at least 400 rows"),   # ← 表級：整張表的規矩
)

orders = order_schema.validate(orders)      # 通過就原樣回傳，可以直接串在管道裡</div>
  <p>
    每一欄用 <span class="kbd">pa.Column</span> 宣告：第一個參數是型別，後面接檢查
    （<span class="kbd">ge</span>／<span class="kbd">gt</span>／<span class="kbd">between</span>／<span class="kbd">isin</span>）、
    <span class="kbd">unique=True</span>（主鍵不可重複）、<span class="kbd">nullable=False</span>（不可以有空值）。
    最後那個 <span class="kbd">checks=</span>（複數、放在整張表那一層）拿到的是整個 DataFrame——
    這裡放的是最實用的一條：<b>至少要有 400 列</b>。上游只回傳一半資料是非常常見的故障，
    而且單看每一欄都完全正常。
  </p>
  <p>
    <b>通過的話 <span class="kbd">validate()</span> 把資料原樣回傳</b>（內容一模一樣，只是新物件）。
    這個設計讓驗證變成資料流的一站，而不是額外一句 if：<span class="kbd">df = schema.validate(load_orders())</span>。
    實測 500 列全部通過。
  </p>
  <p>
    順帶一提第一行的 <span class="kbd">import pandera.pandas as pa</span>：網路上很多範例寫的是
    <span class="kbd">import pandera as pa</span>——實測還能用，但會噴
    <span class="kbd">FutureWarning: Importing pandas-specific classes and functions from the top-level
    pandera module will be removed in a future version of pandera.</span>
    新程式一律用子模組那條路徑。
  </p>
  <a class="golab" href="__NB__" target="_blank" rel="noopener">到 notebook 的 1️⃣ 節：把腦袋裡的規矩寫成程式碼</a>
</section>

<section id="s3">
  <span class="eyebrow">03 · 讓它失敗</span>
  <h2><code>SchemaError</code> 與 <code>SchemaErrors</code>：差一個 s，差很多</h2>
  <p>
    合約寫得對不對，看它「通過」是看不出來的——<b>要看它擋不擋得住壞資料</b>。
    把四筆資料弄壞（第 0 列金額 −50、第 1 列國家 <code>XX</code>、第 2 列客戶 99、第 3 列金額 <code>NaN</code>）之後，
    直接 <span class="kbd">validate()</span> 的結果是：
  </p>
  <div class="codeblock">Column 'customer' failed element-wise validator number 0: in_range(1, 59) failure cases: 99</div>
  <p>
    <b>只講了一個。</b>另外三個問題還在資料裡，但你得先修好這一個、再跑一次才會看到下一個——
    四個問題就是四輪。開發時這樣很方便（訊息短），生產環境則是災難：每一輪都要重跑一次上游、
    重等一次 ETL。
  </p>
  <div class="codeblock">try:
    order_schema.validate(bad_orders, lazy=True)          # ← 只多這一個參數
except pa.errors.SchemaErrors as e:                       # ← 複數！
    print(e.failure_cases)

  schema_context    column                     check failure_case  index
0         Column  customer           in_range(1, 59)           99      2
1         Column    amount              not_nullable          NaN      3
2         Column    amount           greater_than(0)        -50.0      0
3         Column   country  isin(['TW', 'JP', 'US'])           XX      1</div>
  <p>
    <span class="kbd">e.failure_cases</span> 是這一課最該記住的東西——<b>一張 DataFrame，每一列是一筆違約</b>：
    <span class="kbd">column</span>（哪一欄）、<span class="kbd">check</span>（違反哪一條）、
    <span class="kbd">failure_case</span>（壞掉的那個值本身）、<span class="kbd">index</span>（<b>哪一列</b>，
    可以直接拿去 <span class="kbd">df.loc[...]</span> 撈出來看）。
    有了它，你能做三件單一錯誤訊息做不到的事：<b>一次修完</b>、<b>把表寄給上游</b>（對方不用問「你說的壞資料是哪一筆」）、
    以及第 8 節要做的——<b>把它掛在管線的檢查結果上</b>。
  </p>
  <p>
    <b>生產環境一律 <span class="kbd">lazy=True</span></b>。這是本課最實用的一條規則。
  </p>
  <div class="tw">
    <table class="cmp w4">
      <tr><th>上游做了什麼</th><th>check</th><th>failure_case</th><th>index</th></tr>
      <tr><td>型別變了（int → float）</td><td><code>dtype('int64')</code></td><td>float64</td><td class="no">None</td></tr>
      <tr><td>主鍵重複（抓了兩次）</td><td><code>field_uniqueness</code></td><td>0</td><td>0 與 10（<b>兩列都報</b>）</td></tr>
      <tr><td>多了缺值</td><td><code>not_nullable</code></td><td>NaN</td><td>5</td></tr>
      <tr><td>類別多一個新值</td><td><code>isin(['TW', 'JP', 'US'])</code></td><td>KR</td><td>7</td></tr>
      <tr><td>欄位改名 <code>amount</code> → <code>total</code></td><td><code>column_in_dataframe</code></td><td>amount</td><td class="no">None</td></tr>
      <tr><td>只回傳 100 列</td><td><code>at least 400 rows</code></td><td>False</td><td class="no">None</td></tr>
    </table>
  </div>
  <p>
    看最後兩列：它們的 <span class="kbd">schema_context</span> 是 <span class="kbd">DataFrameSchema</span> 而不是
    <span class="kbd">Column</span>，<span class="kbd">index</span> 是空的——因為問題不在某一列的值，
    是<b>整張表的形狀</b>。順帶一提，欄位改名是唯一一種「不驗證也會炸」的變化，
    但合約讓它在入口就炸、而且指名道姓，而不是在第 40 行的 <span class="kbd">df["amount"] * 1.05</span> 才炸。
  </p>
  <a class="golab" href="__NB__" target="_blank" rel="noopener">到 notebook 的 2️⃣–3️⃣ 節：六種變化，一次撞完</a>
</section>

<section id="s4">
  <span class="eyebrow">04 · 自訂檢查</span>
  <h2>一欄看不出來的規矩：跨欄、分組、格式</h2>
  <p>
    真實的資料規則常常跨欄：退款不可以超過訂單金額、每個國家至少要有 100 筆（不然這批八成只抓到一部分）、
    訂單編號要符合 <code>國碼-四位數</code>、日期不可以是未來。這些都靠
    <span class="kbd">pa.Check</span> 加一個你自己寫的函式，放在欄裡（拿到那一欄的 Series）或放在表那一層（拿到整張表）。
  </p>
  <div class="codeblock">rich_schema = pa.DataFrameSchema(
    {
        "sku":        pa.Column(str, pa.Check.str_matches(r"^[A-Z]{2}-\d{4}$")),
        "ordered_at": pa.Column(pa.DateTime, pa.Check.le(pd.Timestamp("2026-09-30"))),
        # …其餘欄位
    },
    checks=[
        pa.Check(lambda d: d["refund"] <= d["amount"], error="refund 不可超過 amount"),          # 回傳 Series
        pa.Check(lambda d: d.groupby("country").size().min() >= 100, error="每個國家至少 100 筆"),  # 回傳 bool
    ],
)</div>
  <p>
    <b>這裡有一個決定「錯誤訊息有多好用」的細節</b>：你的函式回傳什麼，決定 pandera 能不能告訴你「哪一列壞掉」。
  </p>
  <div class="tw">
    <table class="cmp">
      <tr><th>函式回傳</th><th>pandera 怎麼判</th><th>出事時你知道什麼</th></tr>
      <tr><td class="ok">布林 Series（每列一個）</td><td>逐列判定</td><td class="ok">哪一列、那一列長什麼樣</td></tr>
      <tr><td>單一 bool（<code>.all()</code>、比大小）</td><td>整批判定</td><td class="no">只知道「這批不合格」</td></tr>
    </table>
  </div>
  <div class="codeblock">// 回傳 Series（refund 超過 amount）——連壞掉那一列的每個欄位值都印出來
DataFrameSchema 'None' failed element-wise validator number 0: &lt;Check &lt;lambda&gt;: refund 不可超過
 amount&gt; failure cases: 0, 51, 581.0, False, US, 582.0, US-1000, 2026-08-27 00:00:00

// 回傳 bool（每國至少 100 筆）——只有一句「這批不合格」
DataFrameSchema 'None' failed series or dataframe validator 1: &lt;Check &lt;lambda&gt;: 每個國家至少 100 筆&gt;</div>
  <p>
    第一段訊息把<b>壞掉那一列的每一個欄位值</b>都印出來了（實測 8 欄的表就是 8 個值，
    <span class="kbd">failure_cases</span> 也會是 8 列、<span class="kbd">index</span> 全是 0——講的是同一列，
    <b>看 index 不要看筆數</b>）；第二列只有一句「這批不合格」。兩種都對，
    但<b>能寫成 Series 就寫成 Series</b>：出事時你會很感謝當初多想了那三秒。
  </p>
  <p>
    還有一個 <span class="kbd">element_wise=True</span>：讓你的函式一次只拿到一個值，寫起來最直覺，
    代價是它是 Python 迴圈、比向量化慢。留給真的沒辦法向量化的邏輯就好。
    另外，每一條自訂檢查都要給 <span class="kbd">error=</span>——不然訊息裡只會有一個
    <span class="kbd">&lt;lambda&gt;</span> 和它在清單裡的編號。
  </p>
  <a class="golab" href="__NB__" target="_blank" rel="noopener">到 notebook 的 4️⃣ 節：五種跨欄規則各弄壞一次</a>
</section>

<section id="s5">
  <span class="eyebrow">05 · class 寫法</span>
  <h2><code>DataFrameModel</code>、<code>coerce</code>、<code>strict</code></h2>
  <div class="codeblock">class Orders(pa.DataFrameModel):
    order_id: int  = pa.Field(ge=0, unique=True)
    customer: int  = pa.Field(in_range={"min_value": 1, "max_value": 59})
    amount:   float = pa.Field(gt=0, nullable=False)
    returned: bool
    country:  str  = pa.Field(isin=["TW", "JP", "US"])

    class Config:
        coerce = True     # 字串數字自動轉型
        strict = True     # 多出來的欄位一律擋下

    @pa.check("amount", name="整數元")
    def amount_is_whole(cls, s):
        return s % 1 == 0

    @pa.dataframe_check(error="退貨率不可超過 30%")
    def return_rate(cls, df):
        return df["returned"].mean() <= 0.30</div>
  <p>
    同一份合約的第二種寫法：用<b>型別註記</b>宣告欄位，用過 pydantic 就會覺得很熟。實測驗同一份髒資料，
    結果與字典版一模一樣（4 筆違約、同樣的 <span class="kbd">check</span> 名稱）——
    <b>它們是同一個東西的兩張臉</b>，<span class="kbd">Orders.to_schema()</span> 隨時能轉回字典版。
  </p>
  <div class="tw">
    <table class="cmp">
      <tr><th></th><th><code>DataFrameSchema</code>（字典）</th><th><code>DataFrameModel</code>（class）</th></tr>
      <tr><td>形狀</td><td>一個物件，可以在執行時組出來</td><td>一個類別，寫死在程式碼裡</td></tr>
      <tr><td>適合</td><td>欄位是動態的（設定檔、依日期生成）</td><td>欄位固定，全公司共用同一份定義</td></tr>
      <tr><td>好處</td><td>可以塞進 dict、迴圈、<code>to_yaml()</code></td><td>型別註記能當函式簽名 <code>DataFrame[Orders]</code>，編輯器會補全</td></tr>
    </table>
  </div>
  <p>團隊裡選一種寫，別兩種混著用。至於 <span class="kbd">Config</span> 那兩個開關，它們解決的是完全不同的問題：</p>
  <div class="tw">
    <table class="cmp">
      <tr><th>開關</th><th>擋掉什麼</th></tr>
      <tr><td><code>coerce = True</code></td><td>CSV 讀進來整欄是字串——先轉再驗，<b>轉不動才報錯</b>，而且指名是哪個值</td></tr>
      <tr><td>（沒開 coerce）</td><td>字串欄對上 <code>int</code> 宣告直接被拒</td></tr>
      <tr><td><code>strict = True</code></td><td>上游偷偷多送一欄（多半沒事，直到有人寫 <code>get_dummies</code> 或 <code>to_sql</code>）</td></tr>
      <tr><td><code>strict = "filter"</code></td><td>更務實的第三條路：<b>把不在合約裡的欄位直接砍掉</b>（不報錯，回傳只剩宣告過的欄位）</td></tr>
    </table>
  </div>
  <div class="codeblock">// coerce=True，但某一格是 "abc"
Error while coercing 'order_id' to type int64: Could not coerce &lt;class 'pandas.Series'&gt;
 data_container into type int64:   index failure_case  0      1          abc

// 沒開 coerce，整欄字串對上 int 宣告
expected series 'order_id' to have type int64, got str

// strict=True，資料多了一欄 internal_debug_flag
column 'internal_debug_flag' not in DataFrameSchema {'order_id': ..., 'country': ...}</div>
  <p>
    <b>一個很多人搞錯的地方</b>：<span class="kbd">strict</span> 只管一個方向——「資料多送了合約沒有的欄位」。
    「資料少了合約要求的欄位」不管你開不開 strict，本來就會被
    <span class="kbd">column_in_dataframe</span> 擋下來。
  </p>
  <a class="golab" href="__NB__" target="_blank" rel="noopener">到 notebook 的 5️⃣ 節：class 版與兩個開關的實測</a>
</section>

<section id="s6">
  <span class="eyebrow">06 · 型別與時間</span>
  <h2>最容易寫錯的一節</h2>
  <p>
    型別是合約裡最基本的一條，也是最常寫不對的一條。三個一定會撞到的坑，實測結果都在這裡：
  </p>
  <div class="tw">
    <table class="cmp">
      <tr><th>資料是</th><th>合約寫</th><th>結果</th></tr>
      <tr><td>沒有時區的時間</td><td><code>pa.Column(pa.DateTime)</code></td><td class="ok">✅ 通過</td></tr>
      <tr><td>帶時區的時間（資料庫撈出來的）</td><td><code>pa.Column(pa.DateTime)</code></td><td class="no">❌ 型別不符</td></tr>
      <tr><td>帶時區的時間</td><td><code>pa.Column("datetime64[ns, UTC]")</code></td><td class="no">❌ 還是不過——單位也要對</td></tr>
      <tr><td>帶時區的時間</td><td><code>pa.Column("datetime64[ns, UTC]", coerce=True)</code></td><td class="ok">✅ 通過</td></tr>
      <tr><td>字串日期（CSV 讀進來的）</td><td><code>pa.Column(pa.DateTime)</code></td><td class="no">❌ 型別不符</td></tr>
      <tr><td>字串日期</td><td><code>pa.Column(pa.DateTime, coerce=True)</code></td><td class="ok">✅ 通過</td></tr>
      <tr><td><code>category</code> 欄（省記憶體）</td><td><code>pa.Column(str)</code></td><td class="no">❌ 型別不符</td></tr>
      <tr><td><code>category</code> 欄</td><td><code>pa.Column(pa.Category, pa.Check.isin([...]))</code></td><td class="ok">✅ 通過（同時管住型別與允許值）</td></tr>
    </table>
  </div>
  <div class="codeblock">expected series 'ts' to have type datetime64[ns], got datetime64[us, UTC]        // 帶時區
expected series 'ts' to have type datetime64[ns, UTC], got datetime64[us, UTC]   // 連單位都寫死也不過
expected series 'ts' to have type datetime64[ns], got str                        // 字串日期
expected series 'country' to have type string[python], got category             // 分類欄</div>
  <p>
    看第 3 列與第 4 列：同樣的資料、同樣的宣告，差別只有 <span class="kbd">coerce=True</span>。
    這就是本節的結論——<b>型別宣告是給人看的意圖，<span class="kbd">coerce</span> 才是務實的執行策略</b>。
    把宣告寫死成某個精確 dtype，等於把合約綁死在某個 pandas 版本上；開 <span class="kbd">coerce</span> 之後，
    轉不動的值（<code>"2026-13-45"</code>、<code>"N/A"</code>）反而會在入口就被指名，
    而不是變成 <span class="kbd">NaT</span> 之後靜靜影響統計。
  </p>
  <a class="golab" href="__NB__" target="_blank" rel="noopener">到 notebook 的 6️⃣ 節：八種型別組合的對照表</a>
</section>

<section id="s7">
  <span class="eyebrow">07 · 合約進版控</span>
  <h2>先讓資料寫草稿，再把合約存成設定檔</h2>
  <p>
    一張三十欄的表要一欄一欄想「型別是什麼、範圍多少」，會寫到放棄。
    <span class="kbd">pa.infer_schema(df)</span> 看一眼資料就生一份草稿——但<b>它產出的東西不能直接用</b>：
  </p>
  <div class="codeblock">pa.infer_schema(orders).to_yaml()

columns:
  order_id:
    dtype: int64
    greater_than_or_equal_to: 0.0
    less_than_or_equal_to: 499.0      # ← 這批剛好 500 筆，所以最大編號是 499
  amount:
    dtype: float64
    greater_than_or_equal_to: 6.0     # ← 「今天最小的一筆訂單是 6 元」不是業務規則
    less_than_or_equal_to: 2644.0</div>
  <p>
    它把「這批資料剛好的樣子」寫成了規矩：明天第 501 筆訂單進來就違約了。
    正確用法是<b>用它省下打字的力氣，然後人工把每一條改成業務上真正的規矩</b>——
    無意義的界線刪掉，真正的界線寫進去（金額必須大於 0、國家只有那三個）。
  </p>
  <p>
    改完之後，<span class="kbd">schema.to_yaml()</span> 把合約變成一份設定檔：PR 上看得到
    「這次把 <code>country</code> 多加了一個 <code>KR</code>」、資料工程與後端可以共用同一份定義、
    不同環境可以載不同的合約。<span class="kbd">from_yaml()</span> 載回來驗證行為一模一樣——
    <b>但有一半沒被存進去</b>：
  </p>
  <div class="codeblock">order_schema.to_yaml()

columns:
  order_id: {dtype: int64, unique: true, greater_than_or_equal_to: 0}
  customer: {dtype: int64, in_range: {min_value: 1, max_value: 59}}
  ...
checks: null          # ← 那條「至少 400 列」不見了</div>
  <div class="tw">
    <table class="cmp">
      <tr><th>拿什麼去驗</th><th>原本的 schema</th><th>YAML 載回來的</th></tr>
      <tr><td>四筆壞資料的 500 列（全是欄位規則）</td><td>4 筆違約</td><td class="ok">4 筆——完全一致</td></tr>
      <tr><td>乾淨、但只回傳 100 列（只違反表級規則）</td><td>1 筆違約</td><td class="no">0 筆——直接放行</td></tr>
    </table>
  </div>
  <p>
    原因不難理解：表級的 <span class="kbd">checks=</span> 是 Python lambda，沒辦法用 YAML 表達
    （欄位層的內建檢查——連 <span class="kbd">str_matches</span> 的正規表達式——都存得下來）。
    所以真實專案的合約通常是<b>兩層</b>：欄位規則走 YAML，跨欄與整批的規則留在程式碼裡。
    <b>知道哪一半沒被存進去，比記住這個限制更重要。</b>
  </p>
  <a class="golab" href="__NB__" target="_blank" rel="noopener">到 notebook 的 7️⃣ 節：YAML 來回一趟，親手比對違約數</a>
</section>

<section id="s8">
  <span class="eyebrow">08 · 接進管線</span>
  <h2>合約變成擋得住下游的閘門</h2>
  <p>
    到這裡合約已經很完整了，但它還只是「你手動跑的一個函式」。最後一步是接進管線，
    讓它在每一批資料進來時自動執行，而且——<b>不合格的資料，下游根本不准開始跑</b>。
    第 3 課的 Dagster <span class="kbd">@asset_check(blocking=True)</span> 就是為這件事存在的：
  </p>
  <div class="codeblock">@dg.asset_check(asset=raw_orders, blocking=True, description="訂單必須符合 pandera 合約")
def orders_contract(raw_orders: pd.DataFrame) -> dg.AssetCheckResult:
    try:
        order_schema.validate(raw_orders, lazy=True)
        return dg.AssetCheckResult(passed=True, metadata={"violations": 0})
    except pa.errors.SchemaErrors as e:
        fc = e.failure_cases
        return dg.AssetCheckResult(passed=False, metadata={
            "violations": len(fc),
            "failures": dg.MetadataValue.md(fc.to_markdown(index=False)),   # ← UI 直接畫成表格
        })</div>
  <p>
    同一條管線（<code>raw_orders</code> → 檢查 → <code>customer_summary</code>）跑兩次，實測結果：
  </p>
  <div class="tw">
    <table class="cmp w5">
      <tr><th>這一批</th><th>run.success</th><th>檢查</th><th>violations</th><th>實體化的資產</th></tr>
      <tr><td>乾淨資料</td><td class="ok">True</td><td class="ok">✅ 通過</td><td>0</td><td><code>raw_orders</code>, <code>customer_summary</code></td></tr>
      <tr><td>四筆壞資料</td><td class="no">False</td><td class="no">❌ 沒過</td><td>4</td><td><code>raw_orders</code> <b>只有它</b></td></tr>
    </table>
  </div>
  <div class="codeblock">dagster._core.errors.DagsterAssetCheckFailedError: 1 blocking asset check failed with ERROR severity:
raw_orders: orders_contract</div>
  <p>
    <code>customer_summary</code> 不在清單裡——<b>閘門關上了，下游一步都沒跑</b>。
    這就是 <span class="kbd">blocking=True</span> 的全部意義：壞資料不會變成壞報表、壞模型、壞決策。
    改成 <span class="kbd">blocking=False</span> 的話，檢查照樣變紅、但下游照跑——那叫警告，不叫閘門。
    另外兩個細節：這裡<b>一定要 <span class="kbd">lazy=True</span></b>（維運的人要的是「這批有哪些問題」），
    而 <span class="kbd">MetadataValue.md</span> 讓半夜看板的人不用開 notebook 就知道哪一欄壞了。
  </p>
  <p>
    <b>擋下來之後呢？</b>管線停在那裡沒人管，就只是換一種方式壞掉。三種收尾，選一種寫進你的管線：
  </p>
  <div class="tw">
    <table class="cmp">
      <tr><th>做法</th><th>怎麼做</th><th>適合</th></tr>
      <tr><td>擋住＋通知</td><td><code>blocking=True</code>，檢查失敗觸發通知，人工判斷</td><td>資料錯了會出人命（金流、醫療）</td></tr>
      <tr><td>丟掉壞的列</td><td><code>DataFrameSchema(..., drop_invalid_rows=True)</code> ＋ <code>lazy=True</code>（實測本課資料丟 1 列剩 499 列）</td><td>壞資料比例低、少幾列不影響結論</td></tr>
      <tr><td>隔離區</td><td>檢查改 <code>blocking=False</code>，壞的列寫進另一張表，好的列繼續走</td><td>每天都有一點髒資料，但不能停線</td></tr>
    </table>
  </div>
  <p>
    沒有標準答案，但<b>一定要選一個</b>——最糟的是沒想過，然後在半夜臨時決定。
    而這三種都建立在同一件事上：你知道確切是哪幾列、違反哪一條。這就是前面花那麼多篇幅講
    <span class="kbd">failure_cases</span> 的原因。
  </p>
  <a class="golab" href="__NB__" target="_blank" rel="noopener">到 notebook 的 8️⃣–9️⃣ 節：閘門實跑兩次＋自己挑一種破壞方式</a>
</section>

<section id="s9">
  <span class="eyebrow">09 · 實戰</span>
  <h2>換你動手</h2>
  <div class="ex">
    <span class="lv">LEVEL 1</span>
    <p>在表級 <span class="kbd">checks=</span> 再加一條「退貨率不可超過 15%」（本課資料實測 8.4%，乾淨資料要能通過），再把 <span class="kbd">returned</span> 整欄設成 <span class="kbd">True</span>，確認它擋得下來。</p>
  </div>
  <div class="ex">
    <span class="lv">LEVEL 2</span>
    <p>用 <span class="kbd">DataFrameModel</span> 把 8 欄的完整合約整份重寫，<span class="kbd">Config</span> 加上 <span class="kbd">strict = True</span>，然後拿只有 5 欄的那份資料去驗——先猜猜看，會是「多欄位」還是「少欄位」的錯？</p>
  </div>
  <div class="ex">
    <span class="lv">LEVEL 3</span>
    <p>把合約存成 YAML、在另一個 cell <span class="kbd">from_yaml</span> 載回來驗同一份資料，比對兩邊的 <span class="kbd">failure_cases</span>。要比兩次：一次只違反欄位規則、一次只違反表級規則——兩次的結論不一樣才算做完。</p>
  </div>
  <p style="font-size:13.5px;color:var(--ink-soft);margin-top:10px">卡住了？每一題在 notebook 末節都有折疊解答——先自己做，再打開對照。</p>
</section>

<section id="quiz">
  <span class="eyebrow">10 · 驗收</span>
  <h2>情境測驗</h2>
  <p>離開前試試看：下面的情境都真的會遇到。每題選一個你認為的最佳做法，選了馬上看得到解釋。</p>
  <div data-quiz>

    <div class="quiz-q" data-answer="C">
      <p class="quiz-tag">Q1 <span class="qtype">情境題</span></p>
      <h3>每天凌晨從交易系統撈訂單、清資料、算特徵、重訓模型。上個月上游改版把金額單位從元換成分，模型連續三天算錯才被發現——當時管線全綠、零錯誤。要怎麼做才不會再發生？</h3>
      <div class="quiz-opts">
        <button type="button" class="quiz-opt" data-k="A">A. 在訓練那一步加一個 try/except，抓到例外就寄信通知</button>
        <button type="button" class="quiz-opt" data-k="B">B. 在報表最後加一段檢查，發現當日營收比昨天多 100 倍就示警</button>
        <button type="button" class="quiz-opt" data-k="C">C. 在資料進管線的第一站放一份 schema（金額範圍、欄位、型別、允許值），用 <code>blocking=True</code> 的 asset check 跑 <code>lazy=True</code> 驗證，不合格就擋住下游</button>
        <button type="button" class="quiz-opt" data-k="D">D. 把上游資料表的權限鎖起來，任何欄位變更都要先通知你</button>
      </div>
      <div class="quiz-fb" aria-live="polite"><p>關鍵在「管線全綠、零錯誤」——這種故障<b>不會拋例外</b>，所以任何靠 try/except 的方案都接不到它（A 的問題）。B 的方向是對的（它其實就是一種驗證），但位置太後面：錯的資料已經走過清洗、特徵、訓練，模型已經被污染了，而且「比昨天多 100 倍」這種手寫規則只擋得住這一種變化。D 是組織流程，值得做，但你擋不住別的團隊改自己的系統，而且忘記通知一次就破功。C 把規矩寫在<b>資料的入口</b>：金額範圍一條就擋住單位變更，欄位與型別擋住改名，<code>isin</code> 擋住新類別；<code>lazy=True</code> 讓你一次看到全部問題，<code>blocking=True</code> 讓下游一步都不跑。合約寫一次，之後每一批資料都受保護。</p></div>
    </div>

    <div class="quiz-q" data-answer="B">
      <p class="quiz-tag">Q2 <span class="qtype dx">錯誤診斷</span></p>
      <h3>同事回報：早上那批資料驗不過，他照著訊息修好 <code>customer</code>、重跑一次，又冒出 <code>amount</code> 的問題；修完再跑，又冒出 <code>country</code>。每一輪都要重等 40 分鐘的 ETL。最直接的修法是？</h3>
      <div class="codeblock">Column 'customer' failed element-wise validator number 0: in_range(1, 59) failure cases: 99</div>
      <div class="quiz-opts">
        <button type="button" class="quiz-opt" data-k="A">A. 這是 pandera 的正常行為，改用迴圈逐欄呼叫 <code>schema.columns[c].validate(df)</code> 自己收集全部錯誤</button>
        <button type="button" class="quiz-opt" data-k="B">B. 驗證時加上 <code>lazy=True</code>，改接 <code>SchemaErrors</code>（複數），從 <code>e.failure_cases</code> 一次拿到全部違約</button>
        <button type="button" class="quiz-opt" data-k="C">C. 把每一條 <code>Check</code> 都加上 <code>raise_warning=True</code>，讓它們只警告不中斷</button>
        <button type="button" class="quiz-opt" data-k="D">D. 資料太髒了，先用 <code>dropna()</code> 與 <code>drop_duplicates()</code> 清一輪再驗</button>
      </div>
      <div class="quiz-fb" aria-live="polite"><p>預設的 <code>validate()</code>（<code>lazy=False</code>）遇到第一個問題就拋 <code>SchemaError</code>——所以才會「修一個、炸一個」。加上 <code>lazy=True</code>，pandera 會把所有欄位都驗完再一起報 <code>SchemaErrors</code>（複數，差一個 s），<code>e.failure_cases</code> 是一張 DataFrame：哪一欄、違反哪一條、壞掉的值、<b>哪一列</b>。本課實測同一份資料，不 lazy 只看到 <code>customer</code> 那一筆，lazy 一次拿到 4 筆——一輪就修完。A 能勉強做到，但要自己重寫 pandera 已經提供的東西，而且拿不到表級檢查的結果；C 是把錯誤降級成警告，資料照樣進下游，等於沒驗；D 更糟：<code>dropna</code> 會把該被指名的問題悄悄刪掉，正好回到「安靜的錯誤」。</p></div>
    </div>

    <div class="quiz-q" data-answer="A">
      <p class="quiz-tag">Q3 <span class="qtype dx">錯誤診斷</span></p>
      <h3>合約在資料庫來源上跑得好好的，換成讀每日 CSV 之後第一欄就掛了。資料本身沒問題，打開 CSV 看到的就是 <code>1,2,3</code>。最合適的修法是？</h3>
      <div class="codeblock">SchemaError: expected series 'order_id' to have type int64, got str</div>
      <div class="quiz-opts">
        <button type="button" class="quiz-opt" data-k="A">A. 在欄位或 <code>Config</code> 開 <code>coerce=True</code>，讓 pandera 先轉型再驗——轉不動的值會被指名</button>
        <button type="button" class="quiz-opt" data-k="B">B. 把合約裡的 <code>order_id</code> 改宣告成 <code>str</code>，反正 CSV 讀進來就是字串</button>
        <button type="button" class="quiz-opt" data-k="C">C. 在 <code>read_csv</code> 之後、驗證之前加一句 <code>df = df.astype({"order_id": int})</code></button>
        <button type="button" class="quiz-opt" data-k="D">D. 這是 pandas 版本差異，把 <code>pa.Column(int)</code> 改成 <code>pa.Column("int64")</code></button>
      </div>
      <div class="quiz-fb" aria-live="polite"><p>訊息說得很直白：合約要 <code>int64</code>，拿到的是 <code>str</code>。<code>coerce=True</code> 就是為這種「來源格式不同、語意相同」的情況設計的：pandera 先把欄位轉成宣告的型別再驗，<b>轉不動才報錯，而且告訴你是哪個值</b>（實測把某格改成 <code>"abc"</code> 會得到 <code>Error while coercing 'order_id' to type int64 ... failure_case 0 1 abc</code>）——這比自己轉型多了一層保護。B 是為了讓驗證通過而放棄合約：<code>order_id</code> 變成字串之後，<code>ge(0)</code> 這類數值檢查就不再成立，等於把規矩改鬆來配合資料。C 能動，但 <code>astype(int)</code> 遇到壞值直接拋 <code>ValueError</code>，錯誤訊息裡沒有欄名、沒有列號，也不會出現在 <code>failure_cases</code> 裡——你把驗證搬到了合約外面。D 沒有解決任何事，<code>pa.Column(int)</code> 本來就對應 <code>int64</code>。</p></div>
    </div>

    <div class="quiz-q" data-answer="D">
      <p class="quiz-tag">Q4 <span class="qtype">情境題</span></p>
      <h3>團隊決定把合約 <code>to_yaml()</code> 存進 repo，讓後端與分析同事也能讀。有人提議「既然 YAML 是正本，程式碼裡就只留 <code>from_yaml</code>，其他刪掉」。你該說什麼？</h3>
      <div class="quiz-opts">
        <button type="button" class="quiz-opt" data-k="A">A. 可以，YAML 是完整的合約，<code>from_yaml</code> 載回來驗證行為一模一樣</button>
        <button type="button" class="quiz-opt" data-k="B">B. 不行，YAML 存不下正規表達式與範圍檢查，只有型別能存</button>
        <button type="button" class="quiz-opt" data-k="C">C. 可以，但要記得 YAML 每次載入都會重新推論型別，效能會變差</button>
        <button type="button" class="quiz-opt" data-k="D">D. 不行：表級的 <code>checks=</code>（列數、跨欄關係那些 lambda）不會被寫進 YAML（存出來是 <code>checks: null</code>），刪掉程式碼等於默默拿掉那半份合約</button>
      </div>
      <div class="quiz-fb" aria-live="polite"><p>實測：同一份合約存成 YAML 再載回來，拿「四筆欄位違約」的資料去驗，兩邊都抓到 4 筆、完全一致；但拿「乾淨、只是列數不足」的資料去驗，原本的 schema 擋得下來（1 筆違約：<code>at least 400 rows</code>），YAML 版 <b>0 筆直接放行</b>——因為表級 <code>checks=</code> 是 Python 函式，YAML 表達不了，存出來的最後一行就是 <code>checks: null</code>。這種「刪掉之後測試還是綠的、但保護少了一半」的改動最危險。B 說錯了方向：欄位層的檢查（<code>isin</code>、<code>in_range</code>、<code>unique</code>，連 <code>str_matches</code> 的正規表達式）都存得下來。C 是編造的行為。實務做法是兩層並存：欄位規則走 YAML 好 review 好共用，跨欄與整批規則留在程式碼裡，並在文件裡寫清楚哪一半在哪裡。</p></div>
    </div>

    <div class="quiz-q" data-answer="B">
      <p class="quiz-tag">Q5 <span class="qtype">情境題</span></p>
      <h3>使用者行為日誌每天有 0.1%–0.3% 的列因為前端埋點問題而缺欄，這個比例三個月沒變過。目前 <code>blocking=True</code> 的合約每天早上擋住整條管線，值班的人手動放行已經變成例行公事。最合適的調整是？</h3>
      <div class="quiz-opts">
        <button type="button" class="quiz-opt" data-k="A">A. 把那幾欄的 <code>nullable</code> 改成 <code>True</code>，讓缺欄的列合法通過</button>
        <button type="button" class="quiz-opt" data-k="B">B. 這一批改走「丟掉壞的列」：<code>drop_invalid_rows=True</code> ＋ <code>lazy=True</code>，把當日丟掉的列數記成 metadata，數字異常時才通知人</button>
        <button type="button" class="quiz-opt" data-k="C">C. 把整份合約的檢查都改成 <code>blocking=False</code>，讓管線永遠不會被擋住</button>
        <button type="button" class="quiz-opt" data-k="D">D. 維持現狀，寫一支腳本每天早上自動點「放行」，省下值班的時間</button>
      </div>
      <div class="quiz-fb" aria-live="polite"><p>「每天都會有一點髒資料、比例穩定、但不能停線」正是<b>丟掉壞的列</b>那一格的場景：<code>drop_invalid_rows=True</code> 搭 <code>lazy=True</code> 會把違約的列直接不要（實測 500 列丟 1 列剩 499 列），下游拿到的是一份乾淨資料。關鍵是 B 的後半句——<b>把丟掉的列數記成 metadata</b>：合約還在、資料品質仍然被量化，比例從 0.3% 跳到 8% 的那天你會知道。A 是把規矩改鬆去配合現況，之後真正的缺值故障也一起被放行了，而且那幾欄的下游計算並沒有因此變得能處理空值。C 一次拿掉全部閘門，連「金額變成負的」這種真的該停線的問題也不擋了。D 最糟：它保留了警報的成本卻拿掉了警報的意義，而且訓練所有人忽略紅燈——真正的事故發生那天，沒有人會多看一眼。</p></div>
    </div>

    <div class="quiz-score" data-score></div>
  </div>
</section>

<div class="endnav">
  <a href="/mlflow-tracing/">
    <span class="tag">下一課</span>
    <b>MLflow Tracing：LLM 應用的每一步都留下軌跡 →</b>
  </a>
  <a href="/mlops/">
    <span class="tag">主題</span>
    <b>‹ 回「MLOps 自動化技術」課程列表</b>
  </a>
</div>
'''

SCRIPT = r"""
/* ═══ hero 互動：合約檢查機 ═══
   資料是 notebook 那份 500 筆假訂單的前 6 列；check 名稱、failure_case 的呈現方式
   全部取自 notebook 與 _spikes/spike_pandera_errors.py 的實測輸出（pandera 0.33.1）。
   驗證邏輯照 pandera 的 lazy 模式重現：欄位照 schema 宣告順序報，
   欄位不見時（改名）該欄的值檢查不執行，改由 DataFrameSchema 層的 column_in_dataframe 報。 */
(function () {
  const BASE = [
    { order_id: 0, customer: 51, amount: 581, country: "US" },
    { order_id: 1, customer: 38, amount: 2283, country: "US" },
    { order_id: 2, customer: 31, amount: 160, country: "US" },
    { order_id: 3, customer: 16, amount: 485, country: "US" },
    { order_id: 4, customer: 19, amount: 221, country: "TW" },
    { order_id: 5, customer: 3, amount: 908, country: "TW" },
  ];
  const COLS = ["order_id", "customer", "amount", "country"];
  // 每一格的循環：第 0 個永遠是乾淨值
  function variants(col, row, i) {
    if (col === "order_id") return [String(row.order_id), i === 0 ? "-1" : "0"];
    if (col === "customer") return [String(row.customer), "99"];
    if (col === "amount") return [String(row.amount), "-50", "NaN"];
    return [row.country, "XX"];
  }

  const state = BASE.map(() => ({ order_id: 0, customer: 0, amount: 0, country: 0 }));
  let renamed = false;

  const tbody = document.getElementById("dv-rows");
  const fcBody = document.getElementById("dv-fc");
  const verdict = document.getElementById("dv-verdict");
  const empty = document.getElementById("dv-none");
  const renameBtn = document.getElementById("dv-rename");

  function value(col, i) {
    return variants(col, BASE[i], i)[state[i][col]];
  }

  function failures() {
    const out = [];
    // order_id：先唯一性、再 >= 0（照 schema 宣告順序，一欄一欄報）
    const ids = BASE.map((_, i) => value("order_id", i));
    const dup = new Set(ids.filter((v, i) => ids.indexOf(v) !== i));
    ids.forEach((v, i) => {
      if (dup.has(v)) out.push(["Column", "order_id", "field_uniqueness", v, String(i)]);
    });
    ids.forEach((v, i) => {
      if (Number(v) < 0) out.push(["Column", "order_id", "greater_than_or_equal_to(0)", v, String(i)]);
    });
    BASE.forEach((_, i) => {
      const v = value("customer", i);
      if (Number(v) < 1 || Number(v) > 59) out.push(["Column", "customer", "in_range(1, 59)", v, String(i)]);
    });
    if (renamed) {
      // 欄位不見了：pandera 在 DataFrameSchema 這一層報，該欄的值檢查不會跑
      out.push(["DataFrameSchema", "None", "column_in_dataframe", "amount", "None"]);
    } else {
      BASE.forEach((_, i) => {
        if (value("amount", i) === "NaN") out.push(["Column", "amount", "not_nullable", "NaN", String(i)]);
      });
      BASE.forEach((_, i) => {
        const v = value("amount", i);
        if (v !== "NaN" && Number(v) <= 0) out.push(["Column", "amount", "greater_than(0)", Number(v).toFixed(1), String(i)]);
      });
    }
    BASE.forEach((_, i) => {
      const v = value("country", i);
      if (!["TW", "JP", "US"].includes(v)) out.push(["Column", "country", "isin(['TW', 'JP', 'US'])", v, String(i)]);
    });
    return out;
  }

  function render() {
    tbody.innerHTML = "";
    BASE.forEach((row, i) => {
      const tr = document.createElement("tr");
      COLS.forEach((col) => {
        const td = document.createElement("td");
        const b = document.createElement("button");
        b.type = "button";
        b.textContent = value(col, i);
        if (state[i][col] !== 0) b.classList.add("bad");
        if (col === "amount" && renamed) b.classList.add("bad");
        b.addEventListener("click", () => {
          const n = variants(col, row, i).length;
          state[i][col] = (state[i][col] + 1) % n;
          render();
        });
        td.appendChild(b);
        tr.appendChild(td);
      });
      tbody.appendChild(tr);
    });

    renameBtn.textContent = renamed ? "total" : "amount";
    renameBtn.classList.toggle("bad", renamed);

    const fails = failures();
    fcBody.innerHTML = "";
    fails.forEach((f) => {
      const tr = document.createElement("tr");
      f.forEach((cell, k) => {
        const td = document.createElement("td");
        td.textContent = cell;
        if (k === 0 || k === 1) td.className = "ctx";
        if (k === 2) td.className = "chk";
        tr.appendChild(td);
      });
      fcBody.appendChild(tr);
    });
    empty.textContent = fails.length ? "" : "failure_cases 是空的。";
    empty.style.display = fails.length ? "none" : "block";
    fcBody.parentElement.style.display = fails.length ? "" : "none";

    if (fails.length) {
      verdict.className = "dv-verdict block";
      verdict.innerHTML =
        "⛔ <b>擋下</b>：" + fails.length + " 筆違約——" +
        "<code>validate(df, lazy=True)</code> 拋 <code>SchemaErrors</code>，管線在這裡停住，下游一步都不跑。";
    } else {
      verdict.className = "dv-verdict pass";
      verdict.innerHTML = "✅ <b>放行</b>：6 列全部符合合約，<code>validate()</code> 把資料原樣回傳，下游可以開始跑。";
    }
  }

  renameBtn.addEventListener("click", () => {
    renamed = !renamed;
    render();
  });
  document.getElementById("dv-reset").addEventListener("click", () => {
    state.forEach((s) => COLS.forEach((c) => (s[c] = 0)));
    renamed = false;
    render();
  });
  render();
})();
"""

PANEL_STEPS = """
        <li>登入 molab（GitHub / Google）</li>
        <li>開啟課程 notebook，<b>Fork 成自己的副本</b>即可編輯</li>
        <li>從第一格往下全部執行（首次安裝套件約 1–2 分鐘）——<b>免費 CPU 環境即可</b>，不需要 GPU；全部在記憶體裡跑，不連任何伺服器</li>
"""
