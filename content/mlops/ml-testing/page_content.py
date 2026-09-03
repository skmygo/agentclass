"""課程頁內容區（純常數）。改完跑：python3 .claude/skills/make-lesson/scripts/page-fill.py content/mlops/ml-testing
build.sh 不會部署這個檔；它是 index.html 內容區的正本。"""

TITLE = "ML 測試：用 pytest 幫模型寫行為測試"
DESCRIPTION = "AUC 0.968 不是驗收。把「我相信模型應該怎樣」寫成 10 條會跑的 pytest：合約測試（介面沒變）、表現測試（不退步、沒有哪群特別慘）、行為測試（不變性／方向性／黃金樣本）。同一套測試撞三個模型，看紅的為什麼不是同一組——molab 免費環境全程實作。"
NB = "https://molab.marimo.io/github/skmygo/agentclass/blob/main/content/mlops/ml-testing/ml-testing_ext.py"

STYLE = r"""
  /* 語義色：藍＝合約、橘＝表現、紫＝行為、綠＝通過、紅＝失敗 */
  :root { --c1: #4C72B0; --c2: #DD8452; --c3: #8172B3; --ok: #55A868; --cut: #C44E52; }
  a.golab { text-decoration: none; display: inline-flex; align-items: center; gap: 8px; }

  /* hero：測試面板 */
  #mt-panel .ctl { display: flex; gap: 7px; flex-wrap: wrap; align-items: center; margin-bottom: 12px; }
  #mt-panel .lbl { font-size: 11.5px; font-weight: 800; letter-spacing: .06em; color: var(--ink-soft); }
  #mt-panel .ctl button { font-family: var(--mono); font-size: 12.5px; padding: 5px 11px; border-radius: 8px;
    border: 1.5px solid var(--grid); background: #fff; color: var(--ink); cursor: pointer;
    transition: border-color .15s, background .15s, color .15s; }
  #mt-panel .ctl button:hover { background: var(--chip-bg); }
  #mt-panel .ctl button.on { border-color: var(--ink); background: var(--ink); color: #fff; }
  #mt-panel .grp { font-size: 10.5px; font-weight: 800; letter-spacing: .09em; margin: 11px 0 5px;
    padding-left: 2px; }
  #mt-panel .grp.g1 { color: var(--c1); } #mt-panel .grp.g2 { color: var(--c2); } #mt-panel .grp.g3 { color: var(--c3); }
  #mt-panel .row { display: grid; grid-template-columns: 20px 1fr auto; gap: 8px; align-items: center;
    padding: 4px 6px; border-radius: 7px; opacity: .22; transition: opacity .12s, background .12s; min-width: 0; }
  #mt-panel .row.lit { opacity: 1; }
  #mt-panel .row.fail { background: rgba(196, 78, 82, .07); }
  #mt-panel .row .dot { width: 15px; height: 15px; border-radius: 50%; display: block; background: var(--grid);
    font-size: 10px; line-height: 15px; text-align: center; color: #fff; font-weight: 800; }
  #mt-panel .row.lit.pass .dot { background: var(--ok); } #mt-panel .row.lit.fail .dot { background: var(--cut); }
  #mt-panel .row .nm { font-family: var(--mono); font-size: 11.5px; overflow-wrap: anywhere; min-width: 0; }
  #mt-panel .row.fail .nm { color: var(--cut); font-weight: 700; }
  #mt-panel .row .more { font-size: 10.5px; font-family: var(--mono); border: 1px solid var(--grid);
    background: #fff; color: var(--ink-soft); border-radius: 6px; padding: 1px 7px; cursor: pointer; white-space: nowrap; }
  #mt-panel .row .more:hover { border-color: var(--cut); color: var(--cut); }
  #mt-panel .why { display: none; margin: 2px 0 8px 28px; }
  #mt-panel .why.open { display: block; }
  #mt-panel .why pre { font-family: var(--mono); font-size: 11px; line-height: 1.55; margin: 0;
    white-space: pre-wrap; overflow-wrap: anywhere; border-left: 2.5px solid var(--cut);
    padding: 5px 0 5px 9px; color: var(--ink); }
  #mt-panel .foot { border-top: 1px solid var(--grid); margin-top: 12px; padding-top: 10px;
    display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }
  #mt-panel .code { font-family: var(--mono); font-size: 12px; font-weight: 800; color: #fff;
    padding: 2px 9px; border-radius: 999px; }
  #mt-panel .code.ok { background: var(--ok); } #mt-panel .code.bad { background: var(--cut); }
  #mt-panel .verdict { font-size: 13px; font-weight: 700; }
  #mt-panel .verdict.ok { color: var(--ok); } #mt-panel .verdict.bad { color: var(--cut); }

  table.cmp { width: 100%; border-collapse: collapse; font-size: 13.5px; margin: 14px 0; }
  table.cmp th, table.cmp td { border-bottom: 1px solid var(--grid); padding: 8px 10px; text-align: left; vertical-align: top; }
  table.cmp th { font-size: 12px; letter-spacing: .04em; color: var(--ink-soft); }
  table.cmp td.p { color: var(--ok); font-weight: 700; } table.cmp td.f { color: var(--cut); font-weight: 700; }
  table.cmp td.g1 { color: var(--c1); font-weight: 700; } table.cmp td.g2 { color: var(--c2); font-weight: 700; }
  table.cmp td.g3 { color: var(--c3); font-weight: 700; }
  table.cmp td.lv { white-space: nowrap; font-size: 12.5px; color: var(--ink-soft); font-weight: 700; }
  .tw { overflow-x: auto; }
  .tw table.cmp { min-width: 480px; }
  .kbd { font-family: var(--mono); background: var(--chip-bg); padding: 1px 6px; border-radius: 5px; font-size: 13px; }
  h3.sub { font-size: 15px; margin: 18px 0 6px; }
"""

WRAP = r'''
<section id="hero">
  <span class="eyebrow">ML TESTING · 補充 H · 13</span>
  <h1>ML 測試：<br>用 pytest 幫模型寫行為測試</h1>
  <p style="margin-top:18px">
    「這一版 AUC 0.968，比上一版好，可以上線了嗎？」——大多數團隊的模型驗收就停在這一句。
    但那個數字測不到：加一點雜訊預測會不會翻掉、哪一群客戶特別不準、把某個特徵推高機率是不是往<b>反方向</b>跑、
    少送一欄會炸還是默默算錯。這一課把那些「我相信模型應該怎樣」寫成 10 條會自己跑的斷言。
    先挑一個模型，看同一套測試怎麼判它——
  </p>

  <div class="hero-demo" id="mt-panel">
    <div class="ctl">
      <span class="lbl">要測哪一版</span>
      <button type="button" data-m="champion">champion</button>
      <button type="button" data-m="shallow" class="on">shallow（深度 1）</button>
      <button type="button" data-m="shuffled">shuffled（標籤打亂）</button>
    </div>
    <div id="mt-list"></div>
    <div class="foot">
      <span class="code bad" id="mt-code">exit 1</span>
      <span class="verdict bad" id="mt-verdict">不會註冊</span>
    </div>
  </div>

  <p class="note">
    每一條的判定、每一句 <span class="kbd">E&nbsp;&nbsp;&nbsp;AssertionError</span> 都是 notebook 跑同一份測試檔的實測輸出
    （pytest 9.1.1、scikit-learn 1.9）；點紅色那條的「看訊息」就是 pytest 印出來的原文。
  </p>
</section>

<section id="s1">
  <span class="eyebrow">01 · 為什麼</span>
  <h2>軟體有單元測試，模型呢？</h2>
  <p>
    寫程式的人不會說「這支程式我跑過一次沒噴錯，可以上線了」——他們寫測試。
    測試不是為了證明程式對，而是<b>把「我相信它應該怎樣」寫成會自動跑的斷言</b>：
    以後任何人改任何一行，這些信念都被重新檢查一次。模型完全一樣，只是「應該怎樣」的內容不同。
  </p>
  <div class="tw"><table class="cmp">
    <tr><th></th><th>軟體單元測試</th><th>模型行為測試</th></tr>
    <tr><td>測什麼</td><td>函式的輸入 → 輸出</td><td>模型的輸入 → 預測</td></tr>
    <tr><td>誰會讓它變</td><td>有人改了程式碼</td><td>有人<b>重訓</b>了模型（換資料也算）</td></tr>
    <tr><td>通過的意思</td><td>這些行為還在</td><td>這些信念還成立</td></tr>
    <tr><td>沒過怎麼辦</td><td>不准 merge</td><td><b>不准註冊、不准晉升 champion</b></td></tr>
  </table></div>
  <p>
    ML 的測試金字塔跟軟體同一個形狀，只是每一層換了主角：底層是<b>資料測試</b>（第 9 課的 pandera 合約，
    壞資料進不了管線）、中層是<b>模型行為測試</b>（本課）、上層是<b>管線／整合測試</b>（第 5 課，
    訓練→評估→閘門→註冊真的跑得完）。第 5 課那個 <span class="kbd">quality_gate</span> 是「一個數字的門檻」；
    這一課把它擴成一整套 10 條測試。
  </p>
  <a class="golab" href="__NB__" target="_blank" rel="noopener">到 notebook 的 1️⃣ 節：準備 champion 與兩個壞模型</a>
</section>

<section id="s2">
  <span class="eyebrow">02 · 合約測試</span>
  <h2>第一組：介面沒變</h2>
  <div class="codeblock">def test_output_shape_and_range(model, X):
    p = model.predict_proba(X)
    assert p.shape == (len(X), 2), f"形狀是 {p.shape}，期待 {(len(X), 2)}"
    assert ((p >= 0) &amp; (p &lt;= 1)).all(), "有機率跑出 [0, 1] 之外"
    assert np.allclose(p.sum(axis=1), 1.0), "每列兩個機率相加不等於 1"

def test_missing_column_raises(model, X):
    with pytest.raises(ValueError, match="feature names"):   # 少一欄要「炸」，不是默默算
        model.predict(X.drop(columns="f11"))</div>
  <p>
    最基本、也最常被跳過的一組：形狀與範圍、少一欄要炸、同樣輸入跑兩次要一樣。
    第二條特別值得說——<b>吵鬧的失敗永遠好過安靜的錯誤</b>。如果模型少一欄還能算出答案，那答案一定是錯的，
    而且沒有人會發現。sklearn 對欄位很嚴格，實測三種破壞都會拋 <span class="kbd">ValueError</span>，
    但訊息不一樣：
  </p>
  <div class="codeblock">少一欄  → ValueError: The feature names should match those that were passed during fit.
          Feature names seen at fit time, yet now missing:
          - f11
多一欄  → Feature names unseen at fit time:
          - extra
順序不同 → Feature names must be in the same order as they were in fit.</div>
  <p>
    所以 <span class="kbd">pytest.raises</span> 一定要加 <span class="kbd">match=</span>，
    不然任何一種 <span class="kbd">ValueError</span>（包括你自己寫錯測試造成的）都算它過。
  </p>
  <h3 class="sub">這跟第 2 課的 signature 是什麼關係？</h3>
  <div class="tw"><table class="cmp">
    <tr><th></th><th>signature（第 2 課）</th><th>合約測試（本課）</th></tr>
    <tr><td>誰寫的</td><td>MLflow 在 <span class="kbd">log_model</span> 時自動推論</td><td>你自己決定要承諾什麼</td></tr>
    <tr><td>管什麼</td><td>欄位名稱與型別</td><td>任何介面性質：範圍、決定性、要不要炸</td></tr>
    <tr><td>什麼時候擋</td><td>呼叫模型的當下</td><td><b>重訓完、還沒註冊之前</b></td></tr>
  </table></div>
  <p><b>一句話：signature 是自動的合約，測試是你額外的承諾。</b></p>
  <a class="golab" href="__NB__" target="_blank" rel="noopener">到 notebook 的 2️⃣ 節：三條合約測試與 conftest.py</a>
</section>

<section id="s3">
  <span class="eyebrow">03 · 表現測試</span>
  <h2>第二組：把品質閘寫成一組測試</h2>
  <div class="codeblock">def test_min_auc(model, X, y):                       # ① 夠不夠好
    auc = roc_auc_score(y, model.predict_proba(X)[:, 1])
    assert auc >= 0.95, f"AUC {auc:.4f} 低於上線門檻 0.95"

def test_no_regression_vs_baseline(model, X, y):     # ② 有沒有退步
    prev = json.loads((HERE / "baseline.json").read_text())
    acc = accuracy_score(y, model.predict(X))
    assert acc >= prev["accuracy"] - 0.02, ...

def test_slice_not_much_worse(model, X, y):          # ③ 有沒有哪一群特別慘
    mask = (X["f3"] > 1).to_numpy()
    assert accuracy_score(y[mask], model.predict(X[mask])) >= overall - 0.05, ...</div>
  <p>
    第二條比第一條重要得多。<b>絕對門檻只保證「不會爛到不能用」</b>，
    但真正常見的事故是「這一版比上一版差一點，卻因為還在門檻之上而被放行」——
    連續三次各退 1%，半年後你換了一個明顯更差的模型，而且每一次都合規。
  </p>
  <p>
    第三條最容易被忽略、也最容易上新聞。<b>整體 accuracy 是平均數，平均數會把某一群人的災難藏起來。</b>
    門檻要<b>先實測再寫</b>：把測試集切成幾群，看誰跟整體差最多。這份資料實測——
  </p>
  <div class="tw"><table class="cmp">
    <tr><th>切片</th><th>客戶數</th><th>champion 的 accuracy</th><th>跟整體 0.9160 的落差</th></tr>
    <tr><td><span class="kbd">f1 &gt; 1</span></td><td>258</td><td>0.8837</td><td class="f">低 0.0323（最慘的一群）</td></tr>
    <tr><td><span class="kbd">f0 &lt; -1</span></td><td>270</td><td>0.9000</td><td>低 0.0160</td></tr>
    <tr><td><span class="kbd">f3 &gt; 1</span></td><td>208</td><td>0.9038</td><td>低 0.0122</td></tr>
    <tr><td><span class="kbd">f0 &gt; 1</span></td><td>64</td><td>0.9844</td><td class="p">高 0.0684（最好的一群）</td></tr>
  </table></div>
  <p>
    切片要挑「<b>你會被追究責任</b>」的那些群：不同地區、不同方案、新客戶 vs 老客戶、樣本最少的那一群。
    門檻通常比整體寬鬆（子群樣本少、波動大），但<b>必須有</b>——沒有它，你永遠不知道自己的平均數是誰在扛。
  </p>
  <a class="golab" href="__NB__" target="_blank" rel="noopener">到 notebook 的 3️⃣ 節：三條表現測試與切片實測</a>
</section>

<section id="s4">
  <span class="eyebrow">04 · 行為測試</span>
  <h2>第三組：CheckList 的三件事</h2>
  <p>
    2020 年 Ribeiro 等人的論文《Beyond Accuracy: Behavioral Testing of NLP Models with CheckList》
    提出一組到今天還在用的分類。原本講 NLP，換個主角完全成立：
  </p>
  <div class="tw"><table class="cmp">
    <tr><th>類型</th><th>白話</th><th>這份資料的寫法</th></tr>
    <tr><td class="g3">不變性 invariance</td><td>改了<b>不該影響結果</b>的東西，預測就不該變</td><td>每欄加 <span class="kbd">sigma=0.01</span> 的雜訊，98% 的預測要不變（champion 實測 0.9980）</td></tr>
    <tr><td class="g3">方向性 directional</td><td>改了<b>該往某方向影響</b>的東西，預測要往那個方向動</td><td><span class="kbd">f2</span> 調高 → 流失機率上升；<span class="kbd">f3</span> 調高 → 下降</td></tr>
    <tr><td class="g3">最低功能 minimum functionality</td><td>幾筆「連新人都不會答錯」的樣本，一定要對</td><td>14 位教科書等級的流失客戶，機率不得低於 0.70</td></tr>
  </table></div>
  <h3 class="sub">方向性：先看曲線，再寫斷言</h3>
  <p>
    「<span class="kbd">f2</span> 調高，流失機率應該上升」這句話從哪來？<b>不能用猜的。</b>
    做法是畫<b>部分依賴</b>：把整欄換成訓練分佈的 P05/P25/P50/P75/P95，看平均預測機率怎麼走。實測：
  </p>
  <div class="tw"><table class="cmp">
    <tr><th>模型</th><th>f2 的曲線（P05 → P95）</th><th>總變化</th><th>判定</th></tr>
    <tr><td>champion</td><td>0.141 → 0.197 → 0.553 → 0.716 → 0.751</td><td>+0.610</td><td class="p">單調上升、幅度夠</td></tr>
    <tr><td>shallow</td><td>0.414 → 0.414 → 0.530 → 0.537 → 0.537</td><td>+0.122</td><td class="f">方向對，但幾乎沒反應</td></tr>
    <tr><td>shuffled</td><td>0.484 → 0.490 → 0.478 → 0.490 → 0.501</td><td>+0.017</td><td class="f">上上下下，中途反轉</td></tr>
  </table></div>
  <div class="codeblock">@pytest.mark.parametrize("col,sign", [("f2", +1), ("f3", -1)])
def test_directional(model, X, col, sign):
    grid = json.loads((HERE / "quantiles.json").read_text())[col]
    curve = np.array([model.predict_proba(X.assign(**{col: q})[X.columns])[:, 1].mean() for q in grid])
    monotone = bool((np.diff(curve) * sign >= 0).all())
    assert monotone, f"{col} 往預期方向動時，機率中途反轉：{curve.round(3)}"     # 抓 shuffled
    move = float((curve[-1] - curve[0]) * sign)
    assert move >= 0.20, f"{col} 從 P05 拉到 P95，流失機率只動了 {move:.3f}"    # 抓 shallow</div>
  <p>
    <b>兩個斷言缺一不可</b>：只檢查方向，抓不到「方向沒錯但根本沒反應」的 shallow；
    只檢查幅度，抓不到「總量有動但中途亂走」的 shuffled。
  </p>
  <h3 class="sub">黃金樣本：用領域規則挑，不要用模型挑</h3>
  <p>
    最低功能測試最像人工驗收：挑幾筆「一定要對」的樣本，每次重訓都問一次。<b>挑法決定了它有沒有用</b>——
    如果拿「模型最有把握的那幾筆」當黃金樣本，那測試只是讓模型同意自己，永遠會過。
    這一課用領域規則挑：<b>真的流失了，而且兩個主訊號都站在同一邊</b>（<span class="kbd">f2</span> 在 P80 以上、
    <span class="kbd">f3</span> 在 P20 以下）——實測挑出 14 位典型流失客戶、11 位典型續約客戶。
    門檻不是「分類對就好」：機率不得低於 0.70，因為一個把所有人都猜 0.51 的模型分類全對，但它其實什麼都不知道。
  </p>
  <a class="golab" href="__NB__" target="_blank" rel="noopener">到 notebook 的 4️⃣ 節：部分依賴曲線圖與三條行為測試</a>
</section>

<section id="s5">
  <span class="eyebrow">05 · 讓它紅</span>
  <h2>一套從來沒紅過的測試，你不知道它會不會紅</h2>
  <p>
    綠燈很好看，但沒有意義——除非你看過它紅。把 <span class="kbd">MODEL_UNDER_TEST</span> 換成兩個故意做壞的模型：
    <b>shallow</b>（深度 1 的樹，有點笨但正常，AUC 0.8903）與 <b>shuffled</b>（訓練前把標籤打亂，
    看起來正常但完全沒學到東西，AUC 0.4637）。兩個都是 6 條紅、4 條綠——<b>但紅的不是同一組</b>：
  </p>
  <div class="tw"><table class="cmp">
    <tr><th>測試</th><th>shallow</th><th>shuffled</th><th>為什麼</th></tr>
    <tr><td class="g1">三條合約測試</td><td class="p">通過</td><td class="p">通過</td><td><b>合約測試抓不到爛模型</b>——介面對不代表答案對</td></tr>
    <tr><td class="g2">test_min_auc</td><td class="f">失敗</td><td class="f">失敗</td><td>0.8903 / 0.4637 都低於 0.95</td></tr>
    <tr><td class="g2">test_no_regression</td><td class="f">失敗</td><td class="f">失敗</td><td>比上一版 logreg 的 0.8820 退步太多</td></tr>
    <tr><td class="g2">test_slice_not_much_worse</td><td class="f">失敗</td><td class="p">通過</td><td>shuffled <b>對每一群都一樣爛</b>，切片跟整體沒有落差</td></tr>
    <tr><td class="g3">test_invariance_to_noise</td><td class="p">通過</td><td class="f">失敗</td><td>shallow 幾乎不隨輸入變（一致率 <b>1.0000</b>），shuffled 的決策邊界是噪音（0.9740）</td></tr>
    <tr><td class="g3">test_directional ×2</td><td class="f">失敗（幅度不足）</td><td class="f">失敗（中途反轉）</td><td>同一條測試，兩種不同的失敗訊息</td></tr>
    <tr><td class="g3">test_golden_samples</td><td class="f">失敗</td><td class="f">失敗</td><td>兩個都對「教科書客戶」沒有把握（0.4569 / 0.4005）</td></tr>
  </table></div>
  <p>
    這張表就是本課最重要的一句話：<b>沒有任何一種測試能單獨守住模型。</b>
    合約測試放過了兩個垃圾模型；切片測試放過了 shuffled；不變性測試放過了 shallow，還給了它<b>滿分</b>
    ——一個什麼都不學的模型，本來就最「穩定」。要靠<b>一整組彼此互補的測試</b>，
    才會在不同的故障模式下各自亮紅燈。
  </p>
  <p>
    換個說法：<b>測試就是把 code review 的直覺自動化。</b>資深同事看模型時腦子裡跑的就是這幾條——
    「這數字比上一版好嗎」「哪一群比較差」「把這個特徵推高會怎樣」「我隨手挑幾個案例看看」。
    寫成 pytest 之後，這些直覺就不再依賴那位同事今天有沒有空。
  </p>
  <a class="golab" href="__NB__" target="_blank" rel="noopener">到 notebook 的 5️⃣–6️⃣ 節：10 條全綠，再換兩個壞模型撞一次</a>
</section>

<section id="s6">
  <span class="eyebrow">06 · 放進流程</span>
  <h2>exit code 就是那道閘門</h2>
  <p>測試寫完只是一半，它要<b>擋得住東西</b>才算上線。pytest 的 exit code 實測有四種你會遇到：</p>
  <div class="tw"><table class="cmp">
    <tr><th>code</th><th>意思</th><th>什麼時候出現</th></tr>
    <tr><td class="p">0</td><td>全部通過</td><td>正常</td></tr>
    <tr><td class="f">1</td><td>有測試失敗</td><td>你希望它擋下來的那種</td></tr>
    <tr><td class="f">2</td><td>收集階段就出錯、直接中斷</td><td><span class="kbd">parametrize</span> 的參數對不上、import 失敗</td></tr>
    <tr><td class="f">5</td><td><b>一條測試都沒跑到</b></td><td>檔名沒有 <span class="kbd">test_</span> 前綴、<span class="kbd">-k</span> 打錯字</td></tr>
  </table></div>
  <p>
    <b>5 是最危險的一個。</b>CI 腳本如果寫「失敗＝回傳 1」來判斷，那「一條都沒跑」會被當成成功放行——
    判準一律寫「不等於 0」。實測掃一個只有 <span class="kbd">checks_model.py</span> 的資料夾，
    pytest 回的是 <span class="kbd">no tests ran in 0.00s</span> 加 exit code 5；
    <span class="kbd">-k</span> 打錯字則是 <span class="kbd">2 deselected</span>，一樣 exit 5。
  </p>
  <h3 class="sub">選測試：-k 與 mark</h3>
  <div class="codeblock">pytest -q -k "directional or golden"    # 名字比對，只跑幾條
pytest -q -m "not slow"                 # 依 mark 過濾，跳過慢的（要在 pytest.ini 註冊 slow）
pytest -q --collect-only                # 只列出會跑哪些，不執行
pytest -q --tb=line                     # 每個失敗只印一行（CI log 最好讀）</div>
  <p>
    慢的測試（例如「用完整資料重訓一次再比較」）掛 <span class="kbd">@pytest.mark.slow</span>，
    平常 PR 只跑快的、每晚跑全部。mark 沒在 <span class="kbd">pytest.ini</span> 註冊時，
    打錯字只會得到一行 <span class="kbd">PytestUnknownMarkWarning: Unknown pytest.mark.slwo - is this a typo?</span>
    ——而且<b>測試照跑、照過</b>，你不會發現自己少跑了東西。
  </p>
  <h3 class="sub">接進 CI：測試綠了才准註冊</h3>
  <div class="codeblock">name: model-tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
      - name: 跑模型測試（慢的留給夜間排程）
        env:
          MODEL_UNDER_TEST: candidate
        run: uv run pytest tests/ -q --tb=short -m "not slow"
      - name: 只有全綠才註冊並移動 champion alias
        run: uv run python scripts/promote.py</div>
  <p>
    GitHub Actions 的預設行為就是「前一步非 0 就中斷」，所以不用自己寫判斷——
    <span class="kbd">pytest</span> 的 exit code 直接變成閘門。這跟第 5 課 Dagster 的
    <span class="kbd">@asset_check(blocking=True)</span> 是同一件事的兩種寫法：
    <b>一個在管線裡擋、一個在 CI 裡擋，通常兩個都要有</b>（管線擋排程重訓，CI 擋人為改動）。
  </p>
  <h3 class="sub">測試結果要跟著 run 走</h3>
  <div class="codeblock">mlflow.log_metric("tests_passed", 4)
mlflow.log_metric("tests_failed", 6)
mlflow.set_tag("tests_green", "False")
mlflow.log_dict({"exit_code": 1, "failed": ["test_min_auc", "test_golden_samples", ...]},
                "tests/summary.json")</div>
  <p>
    通過與否跟 AUC 一樣，是這一版模型的性質。寫進 run 之後，半年後有人問
    「上線那一版當時測試過了嗎、哪幾條沒過」，答案在 Registry 裡，不在誰的記憶裡。
  </p>
  <a class="golab" href="__NB__" target="_blank" rel="noopener">到 notebook 的 7️⃣–8️⃣ 節：exit code、-k、MLflow，與可以自己按的測試面板</a>
</section>

<section id="s7">
  <span class="eyebrow">07 · 系列收尾</span>
  <h2>補充系列走完了</h2>
  <p>
    這是 MLOps 補充系列的最後一堂。主線五課（第 1–5 課）把訓練變成有紀錄、有版本、會自動跑、有品質閘的東西；
    補充八課各補上一塊：
  </p>
  <div class="tw"><table class="cmp">
    <tr><th></th><th>課</th><th>一句話</th></tr>
    <tr><td class="lv">補充 A</td><td><a href="/model-serving/">模型上線</a></td><td>批次評分、自包 FastAPI、<span class="kbd">mlflow models serve</span>：模型要被「用」才叫上線</td></tr>
    <tr><td class="lv">補充 B</td><td><a href="/model-monitoring/">模型監控</a></td><td>PSI／KS 看資料漂移、預測漂移是最省事的早期警報</td></tr>
    <tr><td class="lv">補充 C</td><td><a href="/optuna-hpo/">Optuna 調參</a></td><td>超參數搜尋自己跑，價值在「掃不完的空間」</td></tr>
    <tr><td class="lv">補充 D</td><td><a href="/data-validation/">資料驗證</a></td><td>pandera 合約：把安靜的錯誤變成吵鬧的錯誤</td></tr>
    <tr><td class="lv">補充 E</td><td><a href="/mlflow-tracing/">MLflow Tracing</a></td><td>LLM 應用的每一步都留下 span，出事看得到中間</td></tr>
    <tr><td class="lv">補充 F</td><td><a href="/feature-store/">Feast 特徵倉</a></td><td>訓練與上線用同一份特徵，point-in-time join 防穿越</td></tr>
    <tr><td class="lv">補充 G</td><td><a href="/dvc-basics/">DVC 資料版控</a></td><td>資料與模型也要有 git：內容定址、<span class="kbd">repro</span> 只重跑改過的</td></tr>
    <tr><td class="lv">補充 H</td><td><b>ML 測試</b>（本課）</td><td>把「模型應該怎樣」寫成 10 條 pytest，exit code 就是閘門</td></tr>
  </table></div>
  <p>
    八堂課合起來是同一句話：<b>讓「這個模型可以上線」變成一件有人能檢查、機器能重跑的事。</b>
  </p>
</section>

<section id="s8">
  <span class="eyebrow">08 · 實戰</span>
  <h2>換你動手</h2>
  <div class="ex">
    <span class="lv">LEVEL 1</span>
    <p>加一條<b>校準測試</b>：平均預測機率與實際正例比率不得差超過 0.05。寫完先對 champion 跑（實測差 0.0210），再對另外兩個模型跑跑看——想一想，這條測試分辨得出好壞模型嗎？</p>
  </div>
  <div class="ex">
    <span class="lv">LEVEL 2</span>
    <p>把切片測試改成 <span class="kbd">parametrize</span> 三個切片（<span class="kbd">f1&gt;1</span>、<span class="kbd">f0&lt;-1</span>、<span class="kbd">f3&gt;1</span>），讓報告一眼看出是哪一群客戶出事。champion 應該三條全綠，shallow 只有一條紅。</p>
  </div>
  <div class="ex">
    <span class="lv">LEVEL 3</span>
    <p>用 <span class="kbd">hypothesis</span> 寫一條<b>屬性測試</b>：在訓練資料的值域內隨機生成幾百筆客戶，每一筆的機率都要合法。200 個例子應該 2 秒內跑完——但先別急著讓它綠，看看它第一個抓到的問題是什麼。</p>
  </div>
  <p style="font-size:13.5px;color:var(--ink-soft);margin-top:10px">卡住了？每一題在 notebook 末節都有折疊解答與實測數字——先自己做，再打開對照。</p>
</section>

<section id="quiz">
  <span class="eyebrow">09 · 驗收</span>
  <h2>情境測驗</h2>
  <p>離開前試試看：下面的情境都真的會遇到。每題選一個你認為的最佳做法，選了馬上看得到解釋。</p>
  <div data-quiz>

    <div class="quiz-q" data-answer="C">
      <p class="quiz-tag">Q1 <span class="qtype">情境題</span></p>
      <h3>新版模型整體 accuracy 從 0.912 升到 0.916，順利通過「AUC ≥ 0.95」的閘門上線。兩週後客服反映：某個方案的客戶被大量誤判。你要在測試裡加什麼，讓下次不會再發生？</h3>
      <div class="quiz-opts">
        <button type="button" class="quiz-opt" data-k="A">A. 把 AUC 門檻從 0.95 提高到 0.97，標準嚴一點就不會出事</button>
        <button type="button" class="quiz-opt" data-k="B">B. 加一條不變性測試：對那些客戶的特徵加雜訊，確認預測不會亂跳</button>
        <button type="button" class="quiz-opt" data-k="C">C. 加切片測試：把測試集依方案切群，每一群的 accuracy 不得比整體低超過某個幅度，並讓測試名字帶上群名</button>
        <button type="button" class="quiz-opt" data-k="D">D. 加一條 <code>test_no_regression</code>，確認新版不比上一版差</button>
      </div>
      <div class="quiz-fb" aria-live="polite"><p>症狀是「<b>整體變好、某一群變壞</b>」——這是平均數把子群災難藏起來的典型樣子，只有切片測試看得到。實測這份資料就有這種落差：整體 0.9160，但 <code>f1&gt;1</code> 那 258 位客戶只有 0.8837（低 0.0323），而 <code>f0&gt;1</code> 那群反而有 0.9844。切片門檻通常比整體寬鬆（子群樣本少、波動大），重點是<b>要有</b>，而且用 <code>parametrize</code> 讓測試名字帶上群名，報告才會直接說出是哪一群出事。A 把門檻拉高只是讓整體平均更難過關，子群落差照樣看不見（一個 AUC 0.98 但對某群特別差的模型仍然過關）；B 不變性測的是「對雜訊穩不穩」，跟「某群特別不準」是兩件事——實測連什麼都沒學到的模型都能拿到 0.974 的一致率；D 是好測試但也只比整體數字，這一版整體確實變好了，它會是綠的。</p></div>
    </div>

    <div class="quiz-q" data-answer="B">
      <p class="quiz-tag">Q2 <span class="qtype dx">錯誤診斷</span></p>
      <h3>同事把模型測試接上 CI，之後每次都是綠燈、非常快。你手動跑了一次，看到下面的輸出。發生了什麼、怎麼修？</h3>
      <div class="codeblock">$ pytest -q tests/
no tests ran in 0.00s
$ echo $?
5</div>
      <div class="quiz-opts">
        <button type="button" class="quiz-opt" data-k="A">A. 測試檔裡的 <code>assert</code> 全被 <code>@pytest.mark.skip</code> 標掉了，拿掉標記即可</button>
        <button type="button" class="quiz-opt" data-k="B">B. 一條測試都沒被收集到（檔名或函式名沒有 <code>test_</code> 前綴）——改名，並且把 CI 的成功判準改成「exit code 等於 0」而不是「不等於 1」</button>
        <button type="button" class="quiz-opt" data-k="C">C. <code>conftest.py</code> 的 fixture 壞了，pytest 靜靜跳過所有測試，修 fixture 就好</button>
        <button type="button" class="quiz-opt" data-k="D">D. 缺 <code>pytest.ini</code>，pytest 找不到 rootdir 所以不跑，補一個設定檔即可</button>
      </div>
      <div class="quiz-fb" aria-live="polite"><p><code>no tests ran</code> ＋ exit code <b>5</b> 是 pytest 專門用來說「我一條都沒收集到」的組合。最常見的原因是命名：掃資料夾時 pytest 只收 <code>test_*.py</code>，一個叫 <code>checks_model.py</code> 的檔案會被完全忽略（實測就是這個輸出）；函式名沒有 <code>test_</code> 前綴也一樣，而且那種更陰險——檔案裡其他測試照跑照過，你只是少跑了幾條。<b>但真正要修的是 CI 的判準</b>：很多腳本寫「exit code 是 1 就算失敗」，於是 5 被當成成功，綠燈連續好幾個月都是假的。判準一律寫「不等於 0」。A 若真被 skip，輸出會是 <code>3 skipped</code> 而不是 <code>no tests ran</code>；C 的 fixture 出錯會是 <code>ERROR at setup</code> ＋ exit 1，例如 <code>fixture 'modle' not found</code>；D 沒有 <code>pytest.ini</code> 也照跑，它只影響 rootdir 與 mark 註冊。</p></div>
    </div>

    <div class="quiz-q" data-answer="D">
      <p class="quiz-tag">Q3 <span class="qtype">情境題</span></p>
      <h3>你的模型測試只有一組不變性測試（加雜訊後預測不變）。這次重訓後它拿到 <span class="kbd">1.0000</span> 的完美一致率，比上一版的 0.9980 還高。團隊想直接上線。你的判斷是？</h3>
      <div class="quiz-opts">
        <button type="button" class="quiz-opt" data-k="A">A. 一致率變高代表模型更穩定，可以上線，並把門檻從 0.98 提高到 0.999</button>
        <button type="button" class="quiz-opt" data-k="B">B. 一致率 1.0000 太完美，一定是測試寫錯了（雜訊沒真的加進去），先去修測試</button>
        <button type="button" class="quiz-opt" data-k="C">C. 改用更大的雜訊（<code>sigma=0.3</code>）重測，看它還能不能維持 0.98</button>
        <button type="button" class="quiz-opt" data-k="D">D. 擋下來：不變性滿分很可能代表模型<b>對輸入根本沒反應</b>——先補上表現測試與方向性測試，看它是不是退化了</button>
      </div>
      <div class="quiz-fb" aria-live="polite"><p>這是本課實測過的陷阱：深度 1 的 <code>shallow</code> 模型一致率正好是 <b>1.0000</b>，比正常的 champion（0.9980）還「穩」——因為它幾乎對所有人都給同一個答案。<b>一個什麼都不學的模型，不變性必然滿分。</b>所以不變性不能單獨當驗收；它只有跟表現測試（AUC 0.8903，低於門檻）與方向性測試（<code>f2</code> 從 P05 拉到 P95 只動了 0.122）放在一起，才會顯示出這一版其實退化了。A 把門檻拉高只會讓「越呆越容易過」；B 這個數字是真的，不是測試壞掉——真相比 bug 更糟；C 加大雜訊是有用的補充實驗（champion 在 <code>sigma=0.3</code> 是 0.9540），但它仍然只在同一個軸上量，答不出「這個模型還會不會分辨客戶」。本課的核心結論就是這句：<b>沒有任何一種測試能單獨守住模型。</b></p></div>
    </div>

    <div class="quiz-q" data-answer="A">
      <p class="quiz-tag">Q4 <span class="qtype dx">錯誤診斷</span></p>
      <h3>你在 notebook 裡用 <code>pytest.main()</code> 反覆跑測試。剛剛把 <code>test_model.py</code> 裡的門檻從 0.90 改成 0.99（應該要失敗才對），重跑卻還是 <code>1 passed</code>、exit code 0。最可能的原因是？</h3>
      <div class="quiz-opts">
        <button type="button" class="quiz-opt" data-k="A">A. 測試模組被 <code>sys.modules</code> 快取了——同名檔案改了內容，同一個行程再跑會拿到舊的那一份；跑之前要把它從 <code>sys.modules</code> 刪掉</button>
        <button type="button" class="quiz-opt" data-k="B">B. <code>.pytest_cache</code> 記住了上次的結果，加 <code>-p no:cacheprovider</code> 或刪掉那個資料夾就好</button>
        <button type="button" class="quiz-opt" data-k="C">C. 檔案沒有真的寫進磁碟，要在寫入後呼叫 <code>flush()</code></button>
        <button type="button" class="quiz-opt" data-k="D">D. <code>pytest.main()</code> 回傳的 exit code 在 notebook 裡不準，要改看輸出文字判斷</button>
      </div>
      <div class="quiz-fb" aria-live="polite"><p>Python 匯入過的模組會留在 <code>sys.modules</code>，而 <code>pytest.main()</code> 是在<b>同一個行程</b>裡跑的——所以第二次執行時，pytest 拿到的是上一次匯入的那份舊程式碼。實測非常明確：把一個必過的測試改成必敗的測試，不清快取重跑仍然是 <code>1 passed</code>、exit 0；把模組從 <code>sys.modules</code> 刪掉之後再跑，立刻變成 <code>1 failed</code>。修法就是在每次 <code>pytest.main()</code> 之前掃一遍 <code>sys.modules</code>，把 <code>__file__</code> 落在測試資料夾裡的模組（包括 <code>conftest.py</code>）刪掉。B 的 <code>.pytest_cache</code> 只存「上次哪些失敗」給 <code>--lf</code> 用，不會改變測試結果（不過 <code>-p no:cacheprovider</code> 仍值得加，避免在工作目錄留垃圾）；C 用 <code>write_text()</code> 寫檔會自己關檔，磁碟上的內容是新的——這正是最迷惑的地方，你打開檔案看是新的，跑起來卻是舊的；D exit code 完全準確，它只是誠實地回報了那份舊程式碼的結果。</p></div>
    </div>

    <div class="quiz-q" data-answer="B">
      <p class="quiz-tag">Q5 <span class="qtype">情境題</span></p>
      <h3>你要幫流失模型建一組「黃金樣本」測試（幾筆一定要答對的客戶）。手上有訓練集、測試集與現在的 champion。最好的挑法是？</h3>
      <div class="quiz-opts">
        <button type="button" class="quiz-opt" data-k="A">A. 拿 champion 預測機率最高的 10 位與最低的 10 位，斷言下一版也要給出同方向的高／低機率</button>
        <button type="button" class="quiz-opt" data-k="B">B. 用領域規則挑：真實標籤是流失、而且已知的主要訊號都指向流失的那幾位（反向亦然），斷言機率不得低於 0.70 ／高於 0.30</button>
        <button type="button" class="quiz-opt" data-k="C">C. 從測試集隨機抽 20 位，斷言分類結果與真實標籤一致</button>
        <button type="button" class="quiz-opt" data-k="D">D. 拿 champion 預測錯的那幾位當黃金樣本，要求下一版一定要答對</button>
      </div>
      <div class="quiz-fb" aria-live="polite"><p>黃金樣本的意義是「<b>連新人都不會答錯的案例</b>」，所以挑選標準必須<b>獨立於模型</b>——用真實標籤加上領域知識（本課實測：真的流失了，且 <code>f2</code> 在 P80 以上、<code>f3</code> 在 P20 以下，挑出 14 位典型流失客戶）。門檻也不只是「分類對」而是「要有把握」（機率 ≥ 0.70）：一個把所有人都猜 0.51 的模型分類全對，卻什麼都不知道——實測 <code>shallow</code> 對這 14 位的最低機率只有 0.4569，就這樣被抓出來。A 是最常見的錯誤：用模型自己最有把握的樣本當標準，等於讓模型同意自己，換一版只要行為相近就過，測不到任何東西。C 隨機抽會混進本來就模稜兩可的邊界案例，那些案例答錯很正常，測試會變得又脆弱又沒說服力（然後大家開始習慣性忽略它）。D 方向相反：模型答錯的通常正是最難的案例，把它們變成硬性門檻，會逼著下一版去過擬合這幾筆。</p></div>
    </div>

    <div class="quiz-score" data-score></div>
  </div>
</section>

<div class="endnav">
  <a href="/model-explainability/">
    <span class="tag">下一課</span>
    <b>補充 I · 模型可解釋性：上線前要能說出為什麼 →</b>
  </a>
  <a href="/mlflow-tracking/">
    <span class="tag">從頭複習</span>
    <b>回主線第 1 課：MLflow 實驗追蹤 →</b>
  </a>
  <a href="/mlops/">
    <span class="tag">主題</span>
    <b>‹ 回「MLOps 自動化技術」課程列表</b>
  </a>
</div>
'''

SCRIPT = r"""
/* ═══ hero 互動：測試面板 ═══
   10 條測試、三個模型的判定與 E 行原文，全部來自 notebook 的實測輸出
   （pytest 9.1.1 / scikit-learn 1.9；同一份 conftest.py ＋ 三個測試檔，
    只換環境變數 MODEL_UNDER_TEST）。 */
(function () {
  const TESTS = [
    { g: 1, n: "test_output_shape_and_range" },
    { g: 1, n: "test_missing_column_raises" },
    { g: 1, n: "test_deterministic" },
    { g: 2, n: "test_min_auc" },
    { g: 2, n: "test_no_regression_vs_baseline" },
    { g: 2, n: "test_slice_not_much_worse" },
    { g: 3, n: "test_invariance_to_noise" },
    { g: 3, n: "test_directional[f2-1]" },
    { g: 3, n: "test_directional[f3--1]" },
    { g: 3, n: "test_golden_samples" },
  ];
  const GROUPS = { 1: "合約 · CONTRACT", 2: "表現 · PERFORMANCE", 3: "行為 · BEHAVIOR" };
  const FAIL = {
    shallow: {
      test_min_auc:
        "E   AssertionError: AUC 0.8903 低於上線門檻 0.95\nE   assert 0.8902718926553672 >= 0.95",
      test_no_regression_vs_baseline:
        "E   AssertionError: accuracy 0.8260 比上一版（logreg-v1 0.8820）退步超過 2 個百分點，下限 0.8620\nE   assert 0.826 >= 0.862",
      test_slice_not_much_worse:
        "E   AssertionError: 切片 f3>1（208 位客戶）accuracy 0.7452，比整體 0.8260 低了 0.0808\nE   assert 0.7451923076923077 >= (0.826 - 0.05)",
      "test_directional[f2-1]":
        "E   AssertionError: f2 從 P05 拉到 P95，流失機率只動了 0.122\nE   assert 0.12226129208109127 >= 0.2",
      "test_directional[f3--1]":
        "E   AssertionError: f3 從 P05 拉到 P95，流失機率只動了 0.038\nE   assert 0.0382490237719304 >= 0.2",
      test_golden_samples:
        "E   AssertionError: 14 位典型流失客戶裡，最低機率只有 0.4569\nE   assert 0.4569199542391465 >= 0.7",
    },
    shuffled: {
      test_min_auc:
        "E   AssertionError: AUC 0.4637 低於上線門檻 0.95\nE   assert 0.46374229583975346 >= 0.95",
      test_no_regression_vs_baseline:
        "E   AssertionError: accuracy 0.4540 比上一版（logreg-v1 0.8820）退步超過 2 個百分點，下限 0.8620\nE   assert 0.454 >= 0.862",
      test_invariance_to_noise:
        "E   AssertionError: 加了 sigma=0.01 的雜訊後只有 0.9740 的預測沒變\nE   assert 0.974 >= 0.98",
      "test_directional[f2-1]":
        "E   AssertionError: f2 往預期方向動時，機率中途反轉：[0.484 0.49  0.478 0.49  0.501]\nE   assert False",
      "test_directional[f3--1]":
        "E   AssertionError: f3 往預期方向動時，機率中途反轉：[0.533 0.48  0.485 0.493 0.487]\nE   assert False",
      test_golden_samples:
        "E   AssertionError: 14 位典型流失客戶裡，最低機率只有 0.4005\nE   assert 0.40045890725260797 >= 0.7",
    },
    champion: {},
  };

  const panel = document.getElementById("mt-panel");
  if (!panel) return;
  const list = document.getElementById("mt-list");
  const codeEl = document.getElementById("mt-code");
  const verdictEl = document.getElementById("mt-verdict");
  let timer = null;

  function build(model) {
    if (timer) { clearInterval(timer); timer = null; }
    list.textContent = "";
    let lastGroup = null;
    const rows = [];
    TESTS.forEach((t) => {
      if (t.g !== lastGroup) {
        lastGroup = t.g;
        const h = document.createElement("div");
        h.className = "grp g" + t.g;
        h.textContent = GROUPS[t.g];
        list.appendChild(h);
      }
      const failed = Object.prototype.hasOwnProperty.call(FAIL[model], t.n);
      const row = document.createElement("div");
      row.className = "row " + (failed ? "fail" : "pass");
      const dot = document.createElement("span");
      dot.className = "dot";
      const nm = document.createElement("span");
      nm.className = "nm";
      nm.textContent = t.n;
      row.appendChild(dot);
      row.appendChild(nm);
      if (failed) {
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "more";
        btn.textContent = "看訊息";
        row.appendChild(btn);
        const why = document.createElement("div");
        why.className = "why";
        const pre = document.createElement("pre");
        pre.textContent = FAIL[model][t.n];
        why.appendChild(pre);
        btn.addEventListener("click", () => {
          const open = why.classList.toggle("open");
          btn.textContent = open ? "收起" : "看訊息";
        });
        list.appendChild(row);
        list.appendChild(why);
      } else {
        list.appendChild(row);
      }
      rows.push({ row, dot, failed });
    });

    const nFail = rows.filter((r) => r.failed).length;
    codeEl.className = "code " + (nFail ? "bad" : "ok");
    codeEl.textContent = nFail ? "exit 1" : "exit 0";
    verdictEl.className = "verdict " + (nFail ? "bad" : "ok");
    verdictEl.textContent = "…";

    let i = 0;
    const step = () => {
      if (i >= rows.length) {
        clearInterval(timer);
        timer = null;
        verdictEl.textContent = nFail
          ? nFail + " 條沒過 · 管線停住，不會註冊"
          : "10 條全過 · 可以註冊並晉升 champion";
        return;
      }
      rows[i].dot.textContent = rows[i].failed ? "✕" : "✓";
      rows[i].row.classList.add("lit");
      i += 1;
    };
    const reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduce) { while (i < rows.length) step(); step(); }
    else { timer = setInterval(step, 110); }
  }

  panel.querySelectorAll("[data-m]").forEach((b) =>
    b.addEventListener("click", () => {
      panel.querySelectorAll("[data-m]").forEach((x) => x.classList.toggle("on", x === b));
      build(b.dataset.m);
    })
  );
  build("shallow");
})();
"""

PANEL_STEPS = """
        <li>登入 molab（GitHub / Google）</li>
        <li>開啟課程 notebook，<b>Fork 成自己的副本</b>即可編輯</li>
        <li>從第一格往下全部執行（首次安裝套件約 1–2 分鐘）——<b>免費 CPU 環境即可</b>，不需要 GPU；測試檔都寫在暫存資料夾裡跑，不連任何伺服器</li>
"""
