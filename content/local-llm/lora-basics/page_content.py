"""lora-basics 教學頁內容正本。

改完跑：python3 .claude/skills/make-lesson/scripts/page-fill.py content/local-llm/lora-basics
左頁引用的每個數字都來自 lesson.py 的實際執行（CPython export 驗過）。
"""

TITLE = "微調入門：LoRA 與 SFT、DPO"

DESCRIPTION = "凍結整顆模型，只練兩個小矩陣：參數量縮小 128 倍，效果幾乎一樣好。動手算 r、alpha、target_modules，看懂 SFT 與 DPO 差在哪。"

STYLE = r"""
  /* 課程語義色：W（凍結的教科書）藍、adapter（便利貼）橘黃、好的綠、差的紅 */
  :root { --c1: #3D6B8F; --c2: #E0913C; --c3: #55A868; --cut: #C44E52; }

  /* hero：便利貼拉桿 */
  .hero-demo .ctrl + .ctrl { margin-top: 8px; }
  .hero-demo .ctrl label { font-size: 13px; font-weight: 800; white-space: nowrap; min-width: 92px; }
  .hero-demo .verdict { line-height: 1.9; }
  .hero-demo .verdict b { color: var(--c1); font-variant-numeric: tabular-nums; }
  .hero-demo .verdict .hot { color: var(--c2); }

  /* 四步拆解卡 */
  .steps { list-style: none; padding-left: 0; margin: 18px 0; counter-reset: st; }
  .steps li {
    position: relative; padding: 10px 0 10px 46px; margin: 0;
    border-top: 1px solid var(--grid); counter-increment: st;
  }
  .steps li:last-child { border-bottom: 1px solid var(--grid); }
  .steps li::before {
    content: counter(st); position: absolute; left: 0; top: 12px;
    width: 28px; height: 28px; border-radius: 50%; background: var(--c1); color: #fff;
    font-family: var(--mono); font-size: 13px; font-weight: 700;
    display: flex; align-items: center; justify-content: center;
  }

  /* SFT / DPO 對照雙欄 */
  .duo { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin: 18px 0; }
  .duo > div {
    border: 2px solid var(--ink); border-radius: 12px; padding: 14px 16px;
    background: var(--panel); box-shadow: 4px 4px 0 var(--grid);
  }
  .duo h3 { font-size: 15px; margin-bottom: 4px; }
  .duo .sub { font-family: var(--mono); font-size: 11px; letter-spacing: .06em; color: var(--ink-soft); }
  .duo p { font-size: 14px; margin-top: 8px; }
  .duo.sft h3 { color: var(--c3); }
  .duo.dpo h3 { color: var(--c2); }
  @media (max-width: 620px) { .duo { grid-template-columns: 1fr; } }
"""

SCRIPT = r"""
/* ═══ hero 互動：拉 r 看便利貼縮多小、拉 α 看力道 ═══ */
(function () {
  const D = 4096;
  const RANKS = [1, 2, 4, 8, 16, 32, 64];
  const svgNS = "http://www.w3.org/2000/svg";
  const rIn = document.getElementById("lora-r");
  const aIn = document.getElementById("lora-a");
  const bRect = document.getElementById("lora-b");
  const aRect = document.getElementById("lora-a-rect");
  const bLab = document.getElementById("lora-b-lab");
  const aLab = document.getElementById("lora-a-lab");
  const mulT = document.getElementById("lora-mul");
  const capT = document.getElementById("lora-cap");
  const verdict = document.getElementById("lora-verdict");
  if (!rIn || !bRect) return;

  const fmt = (n) => n.toLocaleString("en-US");
  const BOX = 150, TOP = 30, BX = 228;

  function render() {
    const r = RANKS[+rIn.value];
    const alpha = +aIn.value;
    const size = Math.max(4, (BOX * r) / 64);
    const full = D * D;
    const lora = 2 * D * r;
    const scale = alpha / r;

    // B 是 d×r（細長），A 是 r×d（扁寬）
    bRect.setAttribute("x", BX);
    bRect.setAttribute("width", size);
    bLab.setAttribute("x", BX + size / 2);
    const mulX = BX + size + 13;
    mulT.setAttribute("x", mulX);
    const ax = mulX + 13;
    aRect.setAttribute("x", ax);
    aRect.setAttribute("width", BOX);
    aRect.setAttribute("y", TOP + (BOX - size) / 2);
    aRect.setAttribute("height", size);
    aLab.setAttribute("x", ax + BOX / 2);
    capT.setAttribute("x", (BX + ax + BOX) / 2);

    // 便利貼的濃度＝更新力道 α/r（純視覺提示）
    const ink = Math.max(0.22, Math.min(1, 0.22 + scale / 3));
    bRect.setAttribute("fill-opacity", ink);
    aRect.setAttribute("fill-opacity", ink);

    verdict.innerHTML =
      "r = <b>" + r + "</b>：只訓練 <b>" + fmt(lora) + "</b> 個參數，" +
      "整個 W 是 <b>" + fmt(full) + "</b> 個 —— 小 <b>" + Math.round(full / lora) + "</b> 倍<br>" +
      "α = <b>" + alpha + "</b> → 縮放係數 α/r = <span class='hot'><b>" + scale.toFixed(2) +
      "</b></span>（α 越大越強、r 越小越強）";
  }
  rIn.addEventListener("input", render);
  aIn.addEventListener("input", render);
  render();
})();
"""

WRAP = r"""
<section id="hero">
  <span class="eyebrow">FINETUNE · 08</span>
  <h1>微調入門：<br>LoRA 與 SFT、DPO</h1>
  <p style="margin-top:18px">
    上一課你把服務的每個數字攤到儀表板上——延遲、吞吐、佇列，看得見了。
    這一課換個方向：不調服務，<b>改模型本身</b>。
    想讓模型學你的語氣、你的領域知識，難道要重訓一顆幾十億參數的模型？不用。
    <b>把教科書凍起來，只在旁邊貼便利貼</b>——參數量立刻縮小 128 倍，效果幾乎一樣好。
    先拉拉看那張便利貼有多小：
  </p>

  <div class="hero-demo">
    <svg id="lora-svg" viewBox="0 0 560 232" role="img" aria-label="LoRA 參數量與力道示意">
      <rect x="30" y="30" width="150" height="150" rx="6"
            fill="#EAEFF4" stroke="#3D6B8F" stroke-width="3"></rect>
      <text x="105" y="99" text-anchor="middle" font-size="17" font-weight="800" fill="#3D6B8F">W</text>
      <text x="105" y="121" text-anchor="middle" font-size="12" fill="#52646E">4096 × 4096</text>
      <text x="105" y="145" text-anchor="middle" font-size="13">🔒</text>
      <text x="105" y="200" text-anchor="middle" font-size="12.5" font-weight="700" fill="#3D6B8F">教科書（凍結不動）</text>
      <text x="203" y="114" text-anchor="middle" font-size="22" font-weight="800" fill="#1C2B33">+</text>
      <rect id="lora-b" y="30" width="37" height="150" rx="4"
            fill="#E0913C" stroke="#1C2B33" stroke-width="2"></rect>
      <text id="lora-b-lab" x="246" y="200" text-anchor="middle" font-size="12" font-weight="700" fill="#9A5F17">B（4096×r）</text>
      <text id="lora-mul" x="278" y="114" text-anchor="middle" font-size="17" font-weight="800" fill="#1C2B33">×</text>
      <rect id="lora-a-rect" y="86" width="150" height="37" rx="4"
            fill="#E0913C" stroke="#1C2B33" stroke-width="2"></rect>
      <text id="lora-a-lab" x="366" y="200" text-anchor="middle" font-size="12" font-weight="700" fill="#9A5F17">A（r×4096）</text>
      <text id="lora-cap" x="330" y="222" text-anchor="middle" font-size="12.5" font-weight="700" fill="#9A5F17">便利貼：只訓練這兩張</text>
    </svg>
    <div class="ctrl">
      <label for="lora-r">rank r</label>
      <input id="lora-r" type="range" min="0" max="6" step="1" value="4" aria-label="調整 LoRA rank">
    </div>
    <div class="ctrl">
      <label for="lora-a">alpha α</label>
      <input id="lora-a" type="range" min="1" max="64" step="1" value="16" aria-label="調整 lora_alpha">
    </div>
    <div class="verdict" id="lora-verdict"></div>
  </div>

  <p class="note">
    右邊的實驗場是真的 Python（在你的瀏覽器裡跑，不用安裝任何東西）。
    首次載入約需 30–60 秒，正好夠你讀完第 1 節。每個實驗都有滑桿與選項可以拉，
    拉完立刻重算——這是你的沙盒，盡量玩。
  </p>
</section>

<section id="s1">
  <span class="eyebrow">01 · 比喻</span>
  <h2>凍結教科書，只貼便利貼</h2>
  <p>
    你想教模型一件新事情，但不想（也沒本錢）重印整本教科書。
    LoRA 的做法是：<b>教科書一個字都不改，只在旁邊貼便利貼</b>。
  </p>
  <ul>
    <li><b>原始模型＝教科書</b>：整顆凍結，訓練過程完全不更新。</li>
    <li><b>LoRA adapter＝便利貼</b>：新增的兩個小矩陣，存下來只有幾 MB。</li>
    <li><b>推論時教科書 ＋ 便利貼一起看</b>：兩者合起來才是最終的權重。</li>
    <li><b>可以備很多張便利貼</b>：客服語氣一張、法遵摘要一張、寫程式一張——
      同一顆底模掛不同 adapter，像換手機殼一樣隨時切換。</li>
  </ul>
  <p>
    便利貼幾乎不輸重印整本書：多數任務上，LoRA 與全參數微調的落差在 5% 以內。
    而它帶來的兩個好處在實務上更關鍵——
  </p>
  <ul>
    <li><b>記憶體可控</b>：全參數微調除了權重，還要為<em class="cut">每一個</em>可訓練參數
      多帶梯度與優化器狀態，記憶體直接爆炸。LoRA 只要調 <code>r</code>
      就能把需求壓到現有的卡裝得下——<b>用「換方法」取代「換硬體」</b>。
      （硬要在小記憶體的卡上靠 SSD 卸載撐全參數微調？實測（RTX 4090 24GB）的估計是慢 5–10 倍。）</li>
    <li><b>不容易把模型練壞</b>：全參數微調容易造成<em class="cut">災難性遺忘</em>——
      學會新任務，原本會的事情忘了一半，而且參數要調到剛好非常難。
      LoRA 動的部分小，模型的底子還在。</li>
  </ul>
  <button class="golab" data-nb="1️⃣">到右邊算算便利貼有多小</button>
</section>

<section id="s2">
  <span class="eyebrow">02 · 原理</span>
  <h2>四步看懂，不用數學</h2>
  <ol class="steps">
    <li><b>W 太大，我們不更新它。</b>Transformer 每層都有 <code>d×d</code> 的方陣，
      d=4096 就是 <b>16,777,216</b> 個參數——訓練時 W 完全凍結。</li>
    <li><b>加一個低秩分解。</b>把「要改多少」寫成 <code>ΔW = B × A</code>：
      B 是 <code>d×r</code>、A 是 <code>r×d</code>，r 遠小於 d（常見 4~16）。</li>
    <li><b>參數立刻縮小。</b>d=4096、r=16 時，可訓練參數從 16,777,216 掉到
      <b>131,072</b>——<b>小 128 倍</b>。連帶梯度與優化器狀態，一層從 192 MiB 變成 1.5 MiB。</li>
    <li><b>推論零負擔。</b>訓練只更新 A 和 B；上線時把 <code>B×A</code> 加回 W
      合成一個矩陣，<b>不增加任何推論延遲</b>。</li>
  </ol>

  <h3 style="margin-top:26px">ΔW 不是「裸加」回去的</h3>
  <p>
    真正加回去的式子長這樣，前面有一個<b>縮放係數</b>在控制力道：
  </p>
  <div class="codeblock">W′ = W + (α / r) × B·A</div>
  <ul>
    <li><b>α 越大 → 越強</b>（分子）；<b>r 越小 → 越強</b>（分母）。
      α 常見 16 或 32。<b>怕把模型練壞就 α 小、r 大</b>，更新最溫和。</li>
    <li>係數裡有 r，意思是<b>「參數多」不等於「更新猛」</b>——rank 改變時幅度會自動調回來。
      右邊那格會用真的矩陣算給你看：α 加倍力道就加倍，r 從 16 降到 4 力道也剛好加倍。</li>
    <li><b>B 初始化為零</b>：所以掛上 adapter 的第一步 ΔW 每一格都是 0，
      模型行為與原本<b>完全一致</b>，不會一掛上就跑掉。</li>
    <li><b>不需要額外的正規化層</b>：W 已經帶著預訓練時的正規化，更新量又小，α/r 就足以控制。</li>
  </ul>
  <p>
    這些參數在程式裡就是這幾行（訓練要在有 GPU 的機器上跑，這堂課的重點是<b>每個參數你都看得懂</b>）：
  </p>
  <div class="codeblock">model = FastLanguageModel.get_peft_model(
    model,
    r=16, lora_alpha=16, lora_dropout=0,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                    "gate_proj", "up_proj", "down_proj"],
    use_gradient_checkpointing="unsloth",
    random_state=3407,
)</div>
  <button class="golab" data-nb="2️⃣">到右邊拉 α 和 r 感受力道</button>
</section>

<section id="s3">
  <span class="eyebrow">03 · 直覺</span>
  <h2>ΔW 憑什麼是低秩的</h2>
  <p>
    上一節有個沒說破的賭注：<b>把 ΔW 硬拆成 B×A，資訊不會掉太多嗎？</b>
    LoRA 的關鍵洞察就是這句——<b>微調帶來的更新是低秩的</b>：
    它只往少數幾個方向動，所以「r 個方向」的形狀描述得完。
  </p>
  <p>
    右邊把兩個 64×64 的矩陣擺在一起讓你看差別：一個是<b>有結構的更新</b>
    （少數幾個方向疊起來加一點雜訊），一個是<b>純亂數矩陣</b>。
    只留前 4 個方向重建時——
  </p>
  <ul>
    <li>有結構的更新：相對誤差只有 <b>4.6%</b>（前 4 個方向就吃下 <b>99.8%</b> 的能量）。</li>
    <li>純亂數矩陣：還有 <b>88.9%</b> 的誤差，你留多少個方向都還原不了它。</li>
  </ul>
  <p>
    這就是為什麼 <code>r</code> 用 <b>8 或 16</b> 通常就夠，不必給到幾百。
    反過來說：任務越是要模型學一整套新東西，這個假設就越吃緊，r 才需要往上加。
  </p>
  <button class="golab" data-nb="3️⃣">到右邊拉 r 看還原誤差</button>
</section>

<section id="s4">
  <span class="eyebrow">04 · 選擇</span>
  <h2>target_modules：便利貼貼在哪幾頁</h2>
  <p>
    一個 layer 裡不只一個線性層。<code>target_modules</code> 決定你在哪幾個矩陣上掛 adapter，
    這一行差很多。用 d=4096、MLP 中間層 4d、r=16 來算<b>一層</b>的帳
    （該層所有線性層權重合計 268,435,456）：
  </p>
  <ul>
    <li><code>["q_proj","v_proj"]</code>：<b>262,144</b>／層（0.10%）——
      原論文做法，最少修改、最省資源。</li>
    <li><b>attention 全掛</b>（q,k,v,o）：<b>524,288</b>／層（0.20%）——效果好一些，但 MLP 完全沒動。</li>
    <li><code>"all-linear"</code>：<b>1,507,328</b>／層（0.56%）——主流做法，
      <b>MLP 對知識儲存很重要</b>，可調空間最大。</li>
  </ul>
  <p>
    注意 <code>gate_proj</code>／<code>up_proj</code> 是 <code>d → 4d</code> 的大矩陣、
    <code>down_proj</code> 是 <code>4d → d</code>——光是 MLP 這三個投影就佔 <b>983,040</b>，
    比 attention 四個投影加起來（524,288）還多。所以「多掛三個模組」不是多 75%，
    是<b>將近三倍</b>。
  </p>
  <p>
    <b>直覺選擇邏輯</b>：資料多、要學新知識 → <code>all-linear</code>；
    資料少、只想調語氣風格 → <code>q_proj, v_proj</code> 就夠。
  </p>
  <button class="golab" data-nb="4️⃣">到右邊比較三種掛法</button>
</section>

<section id="s5">
  <span class="eyebrow">05 · 資料</span>
  <h2>SFT 一問一答，DPO 一好一壞</h2>
  <p>
    LoRA 決定<b>改哪些權重</b>，資料決定<b>往哪個方向改</b>。微調有兩條主線路：
  </p>

  <div class="duo">
    <div class="sft">
      <span class="sub">SUPERVISED FINE-TUNING</span>
      <h3>SFT</h3>
      <p>給<b>標準答案</b>，讓模型模仿。把（指令, 標準回覆）成對餵進去，
        最大化標準回覆的機率。教格式、語氣、領域知識、指令跟隨的基礎能力。</p>
      <p><em class="cut">限制</em>：模型只知道「什麼是對的」，
        不知道「A 比 B 好在哪」——風格偏好、安全性這類<b>相對性</b>目標它學不到。</p>
    </div>
    <div class="dpo">
      <span class="sub">DIRECT PREFERENCE OPTIMIZATION</span>
      <h3>DPO</h3>
      <p>給<b>好壞對比</b>，讓模型偏向較好的。同一個 prompt 兩個回覆：
        chosen（較好）與 rejected（較差），直接用偏好對訓練。</p>
      <p>拉高 chosen、壓低 rejected 的相對機率，並用<b>參考模型</b>防止偏離太遠。
        一個損失函數就取代了 RLHF 的 Reward Model ＋ PPO 兩階段。</p>
    </div>
  </div>

  <table>
    <thead>
      <tr><th>比較面向</th><th>SFT</th><th>DPO</th></tr>
    </thead>
    <tbody>
      <tr><td>資料格式</td><td>prompt + response（單一標準答案）</td><td>prompt + chosen + rejected（偏好對）</td></tr>
      <tr><td>訓練目標</td><td>交叉熵：模仿參考答案</td><td>DPO loss：拉開 chosen / rejected 差距</td></tr>
      <tr><td>學到什麼</td><td>「正確答案長什麼樣」</td><td>「哪種回答比較好」</td></tr>
      <tr><td>額外需求</td><td>無，單一模型即可</td><td>需要參考模型（通常是 SFT 後的模型）</td></tr>
      <tr><td>標註成本</td><td>要寫出完整好答案，較貴</td><td>只需比較兩個回覆，較便宜且一致性高</td></tr>
      <tr><td>訓練階段</td><td>對齊流程的第一步</td><td>通常接在 SFT 之後，做偏好對齊</td></tr>
    </tbody>
  </table>

  <p>資料就是 JSONL，一行一筆，差別只在欄位：</p>
  <div class="codeblock">// train_sft.jsonl
{"prompt": "用一句話介紹台北", "response": "台北是融合傳統與現代的臺灣首都。"}

// train_dpo.jsonl
{"prompt": "用一句話介紹台北",
 "chosen": "台北是融合傳統與現代的臺灣首都。",
 "rejected": "台北就是個城市。"}</div>

  <p>
    DPO 用 TRL 大約 15 行就能開跑，<code>beta</code> 是<b>偏離參考模型的懲罰強度</b>——
    右邊那格會讓你拉著它看分布怎麼被拉走、又怎麼被拉回來：
  </p>
  <div class="codeblock">from trl import DPOConfig, DPOTrainer

config = DPOConfig(output_dir="dpo-out", beta=0.1)
trainer = DPOTrainer(model=model, args=config,
                     train_dataset=dataset, processing_class=tokenizer)
trainer.train()   # 沒指定 ref model 時，TRL 會自動複製一份當參考模型</div>

  <p>
    <b>建議流程</b>：先用高品質示範資料做 <b>SFT</b> 教會基本能力與格式 →
    由人工或模型比較，<b>收集偏好對</b>（chosen / rejected）→
    在 SFT 模型上做 <b>DPO</b>，調風格、安全性、有用性。
    兩者是互補不是取代；DPO 幾乎都建立在 SFT 之上——沒有基本能力，偏好對齊也調不出好結果。
    最少幾百筆偏好對就看得到效果，<b>重點是 chosen / rejected 的差距要反映你在意的品質面向</b>。
  </p>
  <button class="golab" data-nb="5️⃣">到右邊看兩種資料與 β 的效果</button>
</section>

<section id="s6">
  <span class="eyebrow">06 · 實戰</span>
  <h2>換你動手</h2>
  <p>右邊最下面有一格「你的實驗區」。三個挑戰，由易到難（每題都有折疊解答）：</p>
  <div class="ex">
    <span class="lv">LEVEL 1</span>
    <p>把 1️⃣ 的 <code>r</code> 從 16 拉到 8，看縮小倍數變成幾倍；
       再把 <code>d</code> 拉到 8192，看全參數微調那根柱子跑到哪裡去。</p>
  </div>
  <div class="ex">
    <span class="lv">LEVEL 2</span>
    <p>在 2️⃣ 找出一組 <code>(α, r)</code>，讓<b>力道跟基準（α=16, r=16）幾乎一樣</b>，
       但<b>可訓練參數是基準的 4 倍</b>。這題做完，你就真的懂 α/r 了。</p>
  </div>
  <div class="ex">
    <span class="lv">LEVEL 3</span>
    <p>把 3️⃣ 那個「有結構的更新」改得更難壓縮（權重全改成 1.0，或把雜訊加大十倍），
       再看 r=4 的誤差怎麼變——這對「該用多大的 r」意味著什麼？先猜，再驗證。</p>
  </div>
  <button class="golab" data-nb="6️⃣">到右邊的實驗區開工</button>
</section>

<section id="quiz">
  <span class="eyebrow">07 · 驗收</span>
  <h2>情境測驗</h2>
  <p>離開前試試看：下面的情境都真的會遇到。每題選一個你認為的最佳做法，選了馬上看得到解釋。</p>
  <div data-quiz>

    <div class="quiz-q" data-answer="B">
      <p class="quiz-tag">Q1 <span class="qtype">情境題</span></p>
      <h3>你手上有 300 筆客服對話，想讓一顆 8B 模型講話更像你們公司的客服（稱呼、格式、收尾語）。機器只有一張 24GB 的卡，還得同時跑推論服務。最合理的做法是？</h3>
      <div class="quiz-opts">
        <button type="button" class="quiz-opt" data-k="A">A. 全參數微調——資料才 300 筆，很快就跑完</button>
        <button type="button" class="quiz-opt" data-k="B">B. LoRA，target_modules 只掛 q_proj、v_proj，r 用 8</button>
        <button type="button" class="quiz-opt" data-k="C">C. LoRA，但 target_modules 用 all-linear、r 開到 128，讓它學得更完整</button>
        <button type="button" class="quiz-opt" data-k="D">D. 先收集 chosen / rejected 偏好對做 DPO，直接教它什麼叫「像我們的客服」</button>
      </div>
      <div class="quiz-fb" aria-live="polite"><p>解釋：這是典型的「資料少、只調語氣風格」——原論文的 <code>q_proj, v_proj</code> 正是為此而生，最少修改、最省資源，r=8 一層只有 131,072 個可訓練參數。A 的問題不是時間而是記憶體：全參數微調要為每個參數多帶梯度與優化器狀態，一層一個矩陣就吃掉約 192 MiB，24GB 還要分給推論服務，而且全參數微調容易造成災難性遺忘。C 方向對但過頭：all-linear + r=128 一層就有 12,058,624 個可訓練參數（是 B 的 92 倍），用 300 筆資料去撐這個量只會過擬合。D 順序反了——DPO 需要一個已經會做這件事的參考模型，沒有 SFT 打底，偏好對齊調不出好結果。</p></div>
    </div>

    <div class="quiz-q" data-answer="B">
      <p class="quiz-tag">Q2 <span class="qtype dx">錯誤診斷</span></p>
      <h3>同事想讓 adapter「學得更用力」，把 r 從 16 開到 64、α 保持 16。實驗場算出來的更新力道卻只剩一半：</h3>
      <div class="codeblock">α=16, r=16  →  ‖ΔW‖ = 0.4109   ← 基準
α=16, r=64  →  ‖ΔW‖ = 0.2039   （0.50 倍）</div>
      <div class="quiz-opts">
        <button type="button" class="quiz-opt" data-k="A">A. r 開太大導致過擬合，力道被 LoRA 的正規化層壓掉了</button>
        <button type="button" class="quiz-opt" data-k="B">B. 縮放係數是 α/r，r 變大分母就變大；想更用力該調大 α</button>
        <button type="button" class="quiz-opt" data-k="C">C. B 初始化為零，r 越大被歸零的部分越多</button>
        <button type="button" class="quiz-opt" data-k="D">D. 可訓練參數變成 4 倍，梯度被平均掉了</button>
      </div>
      <div class="quiz-fb" aria-live="polite"><p>解釋：加回去的是 <code>W′ = W + (α/r)·B·A</code>，r 在分母。r 從 16 變 64、α 不動，力道就掉一半——這正是「參數多不等於更新猛」的設計：rank 改變時幅度會自動調回來。想更用力，把 α 調大（α=32、r=64 就回到基準的 0.99 倍，而且參數量是 4 倍）。A 描述的機制不存在：LoRA <b>不需要</b>額外的正規化層，W 已經帶著預訓練時的正規化。C 說反了——B 零初始化只影響第一步（那一刻 ΔW 每一格都是 0），訓練開始後 B 就不再是零，跟 r 大小無關。D 的「梯度被平均」在這裡沒有發生：力道差異完全來自 α/r 這個係數，不是梯度計算。</p></div>
    </div>

    <div class="quiz-q" data-answer="B">
      <p class="quiz-tag">Q3 <span class="qtype dx">錯誤診斷</span></p>
      <h3>把 target_modules 從 attention 四個投影換成 all-linear，只是想「多掛三張便利貼」，可訓練參數卻跳了將近三倍：</h3>
      <div class="codeblock">d = 4096,  r = 16,  32 層
attention 全掛（q,k,v,o）：  524,288 / 層
all-linear（再加 gate,up,down）：1,507,328 / 層   ← 2.875 倍</div>
      <div class="quiz-opts">
        <button type="button" class="quiz-opt" data-k="A">A. LoRA 的參數量與 rank 的平方成正比，掛越多層放大越快</button>
        <button type="button" class="quiz-opt" data-k="B">B. gate/up 是 d→4d、down 是 4d→d 的大矩陣，MLP 三個投影就佔 983,040</button>
        <button type="button" class="quiz-opt" data-k="C">C. all-linear 會解除 W 的凍結，連原始權重一起訓練</button>
        <button type="button" class="quiz-opt" data-k="D">D. 模組數從 4 個變 7 個，所以大約是 7/4 = 1.75 倍，數字算錯了</button>
      </div>
      <div class="quiz-fb" aria-live="polite"><p>解釋：關鍵在<b>矩陣的形狀</b>，不在模組數量。attention 的四個投影都是 d×d，每個掛 LoRA 是 2·d·r，四個合計 524,288；而 gate/up 是 d→4d、down 是 4d→d，每個要 5·d·r，三個合計 983,040——比 attention 四個加起來還多。所以 all-linear = 1,507,328，是 attention-only 的 2.875 倍。D 的算法（模組數比例）看起來合理，正是這題要破的迷思。A 錯在次方：參數量是 2·d·r，跟 r 成<b>正比</b>不是平方。C 完全相反——LoRA 的前提就是 W 全程凍結，掛再多模組也不會解凍；真要訓練 W 本身，那叫全參數微調。</p></div>
    </div>

    <div class="quiz-q" data-answer="B">
      <p class="quiz-tag">Q4 <span class="qtype">情境題</span></p>
      <h3>你已經用 800 筆高品質示範資料做完 SFT，模型現在會照你要的格式回答了。但抽查發現它常給出「技術上正確卻很敷衍」的回覆——你說不出完美答案長怎樣，卻一眼分得出哪個比較好。下一步最合適的是？</h3>
      <div class="quiz-opts">
        <button type="button" class="quiz-opt" data-k="A">A. 再收 2000 筆 SFT 資料，把好答案寫得更完整</button>
        <button type="button" class="quiz-opt" data-k="B">B. 針對抽查到的 prompt 各準備 chosen / rejected 兩個回覆，做 DPO</button>
        <button type="button" class="quiz-opt" data-k="C">C. 改用全參數微調，讓模型學得更徹底</button>
        <button type="button" class="quiz-opt" data-k="D">D. 把 lora_alpha 從 16 調到 32，讓 SFT 學得更用力</button>
      </div>
      <div class="quiz-fb" aria-live="polite"><p>解釋：「說不出完美答案、但分得出高下」就是 DPO 的守備範圍——SFT 只教得了「什麼是對的」，教不了「A 比 B 好在哪」，而敷衍程度、風格偏好正是相對性目標。資料只要 prompt / chosen / rejected 三欄，最少幾百筆就看得到效果，而且「比較兩個回覆」比「寫出完整好答案」便宜、標註一致性也更高。你剛做完的 SFT 模型正好可以當參考模型，順序完全對得上。A 不是不行，但要寫出 2000 筆完整好答案成本高，而且模型仍然不知道「比較起來哪個好」。C 換掉的是「改哪些權重」，解決不了「資料教不了相對好壞」這個問題，還多了災難性遺忘的風險。D 只是把同一個學習目標學得更用力（更容易過擬合），方向沒變。</p></div>
    </div>

    <div class="quiz-score" data-score></div>
  </div>
</section>

<div class="endnav">
  <a href="/local-llm/">
    <span class="tag">主題</span>
    <b>‹ 回「個人地端大語言模型實作」課程列表</b>
  </a>
</div>
"""
