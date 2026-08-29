"""課程頁內容區（純常數）。改完跑：python3 .claude/skills/make-lesson/scripts/page-fill.py content/genai-intro/genai-training
build.sh 不會部署這個檔；它是 index.html 內容區的正本。"""

TITLE = "模型是怎麼練成的：預訓練到 RLHF"
DESCRIPTION = "生成式 AI 第二課：預訓練、SFT、LoRA、蒸餾、RLHF/GRPO 六個訓練名詞一次看懂——親手算 LoRA 為什麼把 90 GB 的微調壓到 15 GB、蒸餾的溫度在蒸什麼、DeepSeek-R1 的 GRPO 在比什麼。"

STYLE = r"""
  /* 語義色：藍＝預訓練、橘＝微調（SFT/LoRA）、綠＝蒸餾、紫＝RL 對齊、紅＝成本 */
  :root { --c1: #4C72B0; --c2: #DD8452; --c3: #55A868; --c4: #8172B2; --cut: #C44E52; }

  .tldr { border-left: 4px solid var(--tc, var(--c1)); background: var(--chip-bg);
    border-radius: 0 10px 10px 0; padding: 10px 14px; margin: 12px 0 16px;
    font-size: 14.5px; line-height: 1.7; }
  .tldr b { color: var(--tc, var(--c1)); }

  /* hero：一個模型的三段人生 */
  #pipe-demo .stages { display: flex; gap: 8px; margin-bottom: 12px; flex-wrap: wrap; }
  #pipe-demo .stage { flex: 1; min-width: 150px; font: inherit; text-align: left; color: var(--ink);
    background: var(--panel); border: 2px solid var(--grid); border-radius: 12px;
    padding: 10px 12px; cursor: pointer; transition: border-color .15s, background .15s; }
  #pipe-demo .stage:hover { border-color: var(--ink-soft); }
  #pipe-demo .stage.on { border-color: var(--tc); background: var(--chip-bg); }
  #pipe-demo .stage .no { font-family: var(--mono); font-size: 11px; font-weight: 800; color: var(--tc); }
  #pipe-demo .stage .nm { font-weight: 800; font-size: 14.5px; }
  #pipe-demo .stage .arrow { font-size: 11.5px; color: var(--ink-soft); }
  #pipe-demo .board { border: 2px solid var(--ink); border-radius: 12px; padding: 13px 16px;
    font-size: 14px; line-height: 1.8; }
  #pipe-demo .board .row b { color: var(--tc); }
  #pipe-demo .board .lbl { display: inline-block; width: 3.5em; font-size: 12px; font-weight: 800;
    letter-spacing: .06em; color: var(--ink-soft); }

  table.cmp { width: 100%; border-collapse: collapse; font-size: 13.5px; margin: 14px 0; }
  table.cmp th, table.cmp td { border-bottom: 1px solid var(--grid); padding: 8px 10px; text-align: left; vertical-align: top; }
  table.cmp th { font-size: 12px; letter-spacing: .04em; color: var(--ink-soft); }
  table.cmp td.n { font-family: var(--mono); font-weight: 800; white-space: nowrap; }
  .kbd { font-family: var(--mono); background: var(--chip-bg); padding: 1px 6px; border-radius: 5px; font-size: 13px; }
  .src { font-size: 12.5px; color: var(--ink-soft); margin-top: -6px; }

  table.cheat { width: 100%; border-collapse: collapse; font-size: 14px; margin: 14px 0; }
  table.cheat td { border-bottom: 1px solid var(--grid); padding: 10px 12px; vertical-align: top; line-height: 1.7; }
  table.cheat td.t { font-weight: 800; white-space: nowrap; width: 11em; }
"""

WRAP = r"""
<section id="hero">
  <span class="eyebrow">GENAI BASICS · 02 · 訓練與後訓練</span>
  <h1>模型是怎麼練成的：<br>預訓練到 RLHF</h1>
  <p style="margin-top:18px">
    「預訓練」「微調」「對齊」不是三個獨立技術，是<b>同一個模型的三段人生</b>——
    每一段的資料量差好幾個數量級，教的東西也完全不同。點點看：
  </p>

  <div class="hero-demo" id="pipe-demo">
    <div class="stages" id="pipe-stages"></div>
    <div class="board" id="pipe-board"></div>
  </div>

  <p class="note">
    右邊的實驗場是真的 Python（在你的瀏覽器裡跑，不用安裝任何東西）。
    首次載入約需 30–60 秒，正好夠你讀完第 1 節。這一課有三筆帳要親手算：
    LoRA 的參數帳、蒸餾的溫度、GRPO 的優勢——全部是真公式真計算。
  </p>
</section>

<section id="s1">
  <span class="eyebrow">01 · PRE-TRAINING</span>
  <h2>預訓練：海量語料學通識</h2>
  <div class="tldr" style="--tc:var(--c1)">
    <b>一句話重點</b>：拿<b>兆級 token</b> 的語料玩「接龍猜下一個字」，
    把語言、知識、推理能力壓進參數——整條管線<b>成本最高</b>的一段。
  </div>
  <p>
    訓練目標簡單到不可思議：就是第 1 課那個自迴歸——給前文、猜下一個 token，
    猜錯就調參數。神奇的是規模夠大之後，「為了把下一個字猜準」這個目標
    逼著模型把文法、事實、甚至推理模式全都學起來。代價也很誠實：
  </p>
  <table class="cmp">
    <tr><th>項目</th><th>Llama 3 8B（公開數字）</th></tr>
    <tr><td>訓練語料</td><td class="n">15T tokens</td></tr>
    <tr><td>GPU 時數</td><td class="n">130 萬 H100-hours</td></tr>
    <tr><td>計算量粗估（6·N·D 公式）</td><td class="n">≈ 7.2 × 10²³ FLOPs</td></tr>
  </table>
  <p class="src">量級來自 Meta 公開的模型卡與通用估算公式；右邊 1️⃣ 的參數帳會算出這顆 8.03B 從哪來。</p>
  <p>
    預訓練的產物叫 <b>base model</b>——它只會「接龍」，你問它問題，
    它很可能回你另一個問題（因為網路上問題後面常常接著更多問題）。
    要讓它「好好回話」，得靠後面兩段。
  </p>
</section>

<section id="s2">
  <span class="eyebrow">02 · FINE-TUNING / SFT</span>
  <h2>微調（SFT）：少量資料教特定行為</h2>
  <div class="tldr" style="--tc:var(--c2)">
    <b>一句話重點</b>：用<b>幾千到幾十萬筆</b>「指令 → 理想回答」示範，
    教會模型任務格式、語氣與領域行為——資料量是預訓練的百萬分之一。
  </div>
  <p>
    SFT（Supervised Fine-Tuning）跟預訓練用一模一樣的「猜下一個字」目標，
    差別只在資料：從「整個網路」換成「你準備的示範對話」。
    幾千筆高品質示範就能明顯改變行為——教格式、教語氣、教「遇到 X 要先問 Y」。
    真實工具是 Hugging Face 的 <span class="kbd">trl</span>：
  </p>
  <div class="codeblock">from trl import SFTTrainer, SFTConfig

trainer = SFTTrainer(
    model=model,                    # 底模（通常掛好 LoRA，見下一節）
    train_dataset=dataset,          # 幾千~幾萬筆「指令→理想回答」
    args=SFTConfig(output_dir="out"),
)
trainer.train()</div>
  <p>
    SFT 學的是「照著示範演」；它不會讓模型長出新知識，
    塞事實進模型該用第 7 課的 RAG——先記住這個分工，之後會一直用到。
  </p>
</section>

<section id="s3">
  <span class="eyebrow">03 · LORA / PEFT</span>
  <h2>LoRA：只調 0.5% 的參數</h2>
  <div class="tldr" style="--tc:var(--c2)">
    <b>一句話重點</b>：凍結底模，只在每層旁邊掛<b>低秩小矩陣</b>來學——
    可訓練參數壓到 1% 以下，<b>消費級 GPU 也能微調</b>。是 PEFT
    （參數高效微調）家族最紅的成員。
  </div>
  <p>
    全參數微調 8B 模型要多少記憶體？權重＋梯度＋Adam 優化器狀態，
    約 12 bytes/參數——<b>90 GB 起跳</b>，一張 24 GB 的 RTX 4090 連零頭都裝不下。
    LoRA 把可訓練參數壓到 <b>41.9M（0.52%）</b>，記憶體掉到<b>約 15 GB</b>
    （右邊 1️⃣ 用真公式算給你看；底模再用 4-bit 量化——QLoRA——還能再砍）。
  </p>
  <div class="codeblock">from peft import LoraConfig, get_peft_model

config = LoraConfig(
    r=16, lora_alpha=32, lora_dropout=0.05,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                    "gate_proj", "up_proj", "down_proj"],
)
model = get_peft_model(base_model, config)
model.print_trainable_parameters()   # → 可訓練 41.9M（0.52%）</div>
  <p>
    別被 0.52% 騙了：低秩更新疊在<b>每一層</b>的注意力與 MLP 上，
    改風格、學格式綽綽有餘——這是業界微調的預設起手式，
    練完的 LoRA 權重檔只有幾十 MB，發佈與切換都輕。
  </p>
  <button class="golab" data-nb="1️⃣">到右邊 1️⃣ 拉出 90 GB → 15 GB 的參數帳</button>
</section>

<section id="s4">
  <span class="eyebrow">04 · DISTILLATION</span>
  <h2>知識蒸餾：大模型當老師</h2>
  <div class="tldr" style="--tc:var(--c3)">
    <b>一句話重點</b>：讓小模型學<b>大模型的輸出分布</b>（不只是答案），
    把能力濃縮進小體積——手機、邊緣裝置上的模型多半這樣來的。
  </div>
  <p>
    關鍵是「軟標籤」：老師模型看一張貓圖，輸出的不是「貓」一個字，
    是「貓 88%、狗 8%、老虎 4%、汽車 0.1%」——<b>「狗比汽車像貓 80 倍」
    這件事 one-hot 標籤裡完全沒有</b>，這叫暗知識（dark knowledge）。
    把 softmax 除以溫度 T，分布蒸軟，暗知識才浮出來（右邊 2️⃣ 拉給你看）：
  </p>
  <div class="codeblock">import torch.nn.functional as F

T = 4.0                                             # 蒸餾溫度
soft_teacher = F.softmax(teacher_logits / T, dim=-1)
log_student  = F.log_softmax(student_logits / T, dim=-1)
loss_kd = F.kl_div(log_student, soft_teacher,
                   reduction="batchmean") * T * T   # 抄老師的「分布」
loss = 0.7 * loss_kd + 0.3 * F.cross_entropy(student_logits, labels)</div>
  <p>
    LLM 時代的蒸餾還有更粗暴的版本：直接讓老師模型<b>生成一大堆高品質問答</b>，
    拿去 SFT 小模型（DeepSeek-R1 就公開釋出了一整組這樣蒸出來的小模型）。
    分布蒸餾與資料蒸餾，本質都是「老師教學生」。
  </p>
  <button class="golab" data-nb="2️⃣">到右邊 2️⃣ 拉溫度，把暗知識蒸出來</button>
</section>

<section id="s5">
  <span class="eyebrow">05 · RLHF / GRPO</span>
  <h2>RLHF 與 GRPO：用強化學習對齊</h2>
  <div class="tldr" style="--tc:var(--c4)">
    <b>一句話重點</b>：SFT 之後用<b>強化學習</b>把模型往「人類覺得好」的方向推。
    GRPO 是 DeepSeek-R1 走紅的關鍵——砍掉 value model，用<b>組內相對比較</b>算優勢。
  </div>
  <p>
    RLHF 的經典流程：收集人類偏好（同一題兩個回答，哪個好？）→ 練一個 reward model
    → 用 RL（傳統上是 PPO）讓模型最大化 reward。痛點是 PPO 要多養一個
    跟模型一樣大的 value model 來估基準線，記憶體與工程都翻倍。
  </p>
  <p>
    <b>GRPO</b>（Group Relative Policy Optimization）的解法漂亮得很：同一題抽一<b>組</b>答案
    （例如 8 個），優勢＝<span class="kbd">(reward − 組平均) / 組標準差</span>——
    基準線直接用「同組其他答案」充當，value model 整個不用了。
    右邊 3️⃣ 可以勾答案對錯，親眼看優勢怎麼算、以及「全對的題什麼都教不了」。
  </p>
  <div class="codeblock">from trl import GRPOTrainer, GRPOConfig

def reward_correct(completions, **kwargs):          # 可驗證的獎勵：對就是對
    return [1.0 if check_answer(c) else 0.0 for c in completions]

trainer = GRPOTrainer(
    model="Qwen/Qwen2.5-1.5B-Instruct",
    reward_funcs=reward_correct,
    train_dataset=math_dataset,
    args=GRPOConfig(num_generations=8),             # 一題抽 8 個答案成一組
)
trainer.train()</div>
  <p>
    <b>RL Reasoning 與 Aha Moment</b>：DeepSeek-R1 的實驗展示了一件事——
    不給任何「怎麼推理」的人類示範，只用「答案對不對」的 RL 訊號，
    模型自己長出「等等，我重新檢查一遍」的反思與回溯行為，
    論文把那個湧現時刻稱為 <b>Aha Moment</b>。這條純 RL 路線，
    就是<a href="/genai-reasoning/">第 4 課</a> reasoning model 的出身。
  </p>
  <button class="golab" data-nb="3️⃣">到右邊 3️⃣ 勾答案，看 GRPO 的優勢怎麼算</button>
</section>

<section id="s6">
  <span class="eyebrow">06 · 速查</span>
  <h2>本課名詞速查卡</h2>
  <p>發講義用的濃縮版——一個名詞一句話：</p>
  <table class="cheat">
    <tr><td class="t" style="color:var(--c1)">預訓練 Pre-training</td>
        <td>兆級 token 玩接龍學通識，<b>成本最高</b>（Llama 3 8B：15T tokens、130 萬 H100-hours）。</td></tr>
    <tr><td class="t" style="color:var(--c2)">微調 Fine-tuning / SFT</td>
        <td>幾千~幾十萬筆示範教<b>特定任務或風格</b>；教行為，不塞新知識。</td></tr>
    <tr><td class="t" style="color:var(--c2)">LoRA / PEFT</td>
        <td>凍結底模、只調低秩小矩陣（0.5% 參數）——<b>消費級 GPU 也能微調</b>。</td></tr>
    <tr><td class="t" style="color:var(--c3)">知識蒸餾 Distillation</td>
        <td>大模型當老師教小模型（軟標籤或生成資料），能力濃縮進小體積。</td></tr>
    <tr><td class="t" style="color:var(--c4)">RLHF / GRPO</td>
        <td>強化學習對齊人類偏好；GRPO 用組內相對比較砍掉 value model，是 DeepSeek-R1 走紅關鍵。</td></tr>
    <tr><td class="t" style="color:var(--c4)">RL Reasoning / Aha Moment</td>
        <td>純 RL（只獎勵答對）讓模型<b>湧現</b>反思與回溯——不用人教怎麼想。</td></tr>
  </table>
</section>

<section id="s7">
  <span class="eyebrow">07 · 實戰</span>
  <h2>換你動手</h2>
  <div class="ex">
    <span class="lv">LEVEL 1</span>
    <p>在右邊 1️⃣ 把 LoRA 的 r 從 16 改成 64——可訓練參數變幾倍？訓練記憶體為什麼幾乎沒動？</p>
  </div>
  <div class="ex">
    <span class="lv">LEVEL 2</span>
    <p>在 2️⃣ 找出「暗知識剛好浮出來、又還沒被蒸糊」的溫度區間。T=1 學生學到什麼？T=10 又失去什麼？（右邊 4️⃣ 的實驗區會同步顯示狗 ÷ 車的倍數。）</p>
  </div>
  <div class="ex">
    <span class="lv">LEVEL 3</span>
    <p>在 3️⃣ 把 8 個答案<b>全部勾對</b>。優勢發生什麼事？這對「RL 訓練該配什麼難度的題目」意味著什麼？</p>
  </div>
  <p style="font-size:13.5px;color:var(--ink-soft);margin-top:10px">卡住了？三題在 notebook 最後一格都有折疊解答——先自己做，再打開對照。</p>
  <button class="golab" data-nb="4️⃣">到右邊 4️⃣ 的實驗區開工</button>
</section>

<section id="quiz">
  <span class="eyebrow">08 · 驗收</span>
  <h2>情境測驗</h2>
  <p>離開前試試看：下面的情境都真的會遇到。每題選一個你認為的最佳做法，選了馬上看得到解釋。</p>
  <div data-quiz>

    <div class="quiz-q" data-answer="C">
      <p class="quiz-tag">Q1 <span class="qtype">情境題</span></p>
      <h3>公司要讓一個 8B 開源模型學會客服部的回覆語氣與格式，手上有 5,000 筆歷史對話、一張 RTX 4090（24 GB）。最務實的做法是？</h3>
      <div class="quiz-opts">
        <button type="button" class="quiz-opt" data-k="A">A. 收集公司所有文件重新預訓練一個自己的模型</button>
        <button type="button" class="quiz-opt" data-k="B">B. 全參數微調 8B 模型，資料少所以應該跑得動</button>
        <button type="button" class="quiz-opt" data-k="C">C. 底模 4-bit 量化＋掛 LoRA 做 SFT——記憶體壓進 24 GB，5,000 筆教語氣綽綽有餘</button>
        <button type="button" class="quiz-opt" data-k="D">D. 先做知識蒸餾，把 8B 蒸成 1B 再全參數微調</button>
      </div>
      <div class="quiz-fb" aria-live="polite"><p>「教語氣與格式」正是 SFT 的主場，5,000 筆是很健康的量；記憶體才是真門檻——全參數微調 8B 要權重＋梯度＋Adam 狀態約 90 GB（本課算過的帳），24 GB 遠遠不夠，所以 B 直接卡死：跑不跑得動看的是記憶體帳，不是資料筆數。LoRA 把可訓練參數壓到 0.5%，配 4-bit 底模（QLoRA）就能塞進消費級卡。A 是拿大砲打蚊子——預訓練是兆級 token、百萬 GPU 時的工程，而且教語氣根本不需要動通識。D 多繞一大圈，蒸餾解決的是「部署體積」問題，這裡的目標是行為，而且蒸完還是要面對微調本身。</p></div>
    </div>

    <div class="quiz-q" data-answer="B">
      <p class="quiz-tag">Q2 <span class="qtype">情境題</span></p>
      <h3>你的 App 要在手機上離線跑一個小模型，但希望它在「客訴分類」這個任務上盡量接近雲端大模型的水準。哪條路最對症？</h3>
      <div class="quiz-opts">
        <button type="button" class="quiz-opt" data-k="A">A. 把大模型量化到 2-bit，硬塞進手機</button>
        <button type="button" class="quiz-opt" data-k="B">B. 蒸餾：讓大模型當老師（生成大量標注資料或軟標籤），訓練一個小模型專精這個任務</button>
        <button type="button" class="quiz-opt" data-k="C">C. 給小模型寫更長更詳細的 prompt，能力就會追上大模型</button>
        <button type="button" class="quiz-opt" data-k="D">D. 對小模型做 RLHF，讓它對齊人類偏好</button>
      </div>
      <div class="quiz-fb" aria-live="polite"><p>「大能力、小體積、單一任務」是蒸餾的教科書場景：老師模型生成海量「客訴→分類」示範（或提供軟標籤），小模型在這個窄任務上可以逼近老師——它不需要老師的通識，只需要這一招。A 方向錯在量級：量化能把體積壓 3～4 倍（下一課的主題），但 70B 級的模型再怎麼壓也不是手機等級，而且 2-bit 這種極限壓縮品質掉得兇。C 高估了 prompt：prompt 能引導行為，變不出小模型沒有的能力，而且手機上長 prompt 還變慢。D 用錯工具——RLHF 管「偏好對齊」，不會把分類能力變出來。</p></div>
    </div>

    <div class="quiz-q" data-answer="C">
      <p class="quiz-tag">Q3 <span class="qtype dx">錯誤診斷</span></p>
      <h3>同事跑了右邊實驗場的參數帳，看到下面的輸出後說：「LoRA 只訓練 0.52% 的參數，模型行為最多也只能改變 0.5%，這種微調是安慰劑吧。」他哪裡想錯了？</h3>
      <div class="codeblock">全參數: 8.03B 參數 → 訓練記憶體約 90 GB
LoRA: 41.9M 可訓練參數（佔 0.52%）→ 約 15 GB</div>
      <div class="quiz-opts">
        <button type="button" class="quiz-opt" data-k="A">A. 他是對的，LoRA 效果確實只有全參數微調的 0.5%</button>
        <button type="button" class="quiz-opt" data-k="B">B. 輸出有誤——LoRA 其實會更新全部參數，只是分批更新</button>
        <button type="button" class="quiz-opt" data-k="C">C. 「參數佔比」不等於「行為改變幅度」：低秩更新疊在每一層的注意力與 MLP 上，教風格、格式與任務行為的效果接近全參數微調——省的是梯度與優化器的記憶體，不是效果</button>
        <button type="button" class="quiz-opt" data-k="D">D. 他只需要把 r 調大到 256，佔比變 8% 就跟全參數一樣了</button>
      </div>
      <div class="quiz-fb" aria-live="polite"><p>數字是真的（本課實算），推論錯在把兩個不同的量畫了等號。行為改變幅度取決於「更新作用在哪裡」：LoRA 的低秩矩陣掛在每一層的七個投影上，每個 token 流過模型都會經過這些更新——影響力是全域的，只是參數化很省。大量實務與研究都顯示：在教格式、語氣、領域行為這類任務上，LoRA 與全參數微調的差距很小，而記憶體帳（90 GB → 15 GB）才是它真正要解的問題。B 描述的機制不存在——底模是凍結的，這正是省記憶體的原因；D 方向錯了，r 加大主要是提高表達容量（同時提高過擬合風險），「佔比高」從來不是目標。</p></div>
    </div>

    <div class="quiz-score" data-score></div>
  </div>
</section>

<div class="endnav">
  <a href="/genai-inference/">
    <span class="tag">下一課</span>
    <b>推理加速：KV Cache、量化與 vLLM →</b>
  </a>
  <a href="/genai-intro/">
    <span class="tag">主題</span>
    <b>‹ 回「生成式 AI 導論」課程列表</b>
  </a>
</div>
"""

SCRIPT = r"""
/* ═══ hero 互動：一個模型的三段人生（量級為公開資料：Meta Llama 3 模型卡等）═══ */
(function () {
  const STAGES = [
    { c: "#4C72B0", no: "STAGE 1", nm: "預訓練", arrow: "base model",
      data: "整個網路：15T tokens（Llama 3 8B 公開數字）",
      cost: "130 萬 H100 GPU-hours——整條管線最貴的一段",
      learn: "語言、知識、推理的「通識」，全靠玩接龍（猜下一個 token）壓進參數",
      out: "base model：只會接龍。問它問題，它可能回你更多問題" },
    { c: "#DD8452", no: "STAGE 2", nm: "SFT 微調", arrow: "instruct model",
      data: "幾千～幾十萬筆人工示範（指令 → 理想回答）",
      cost: "單機～小叢集、小時到天級；掛 LoRA 後消費級 GPU 也行",
      learn: "「被問問題要好好回答」的格式、語氣、領域行為",
      out: "instruct model：會回話了，但還分不清「回得好」和「回得爛」" },
    { c: "#8172B2", no: "STAGE 3", nm: "對齊（RLHF）", arrow: "chat model",
      data: "人類偏好比較（同一題兩個回答，哪個好？）＋ RL",
      cost: "介於兩者之間；GRPO 砍掉 value model 後便宜了一大截",
      learn: "把「人類覺得好」變成獎勵訊號，推著模型往有用、無害的方向走",
      out: "chat model：你每天在用的那種——這也是 R1 長出推理的入口" },
  ];
  const stages = document.getElementById("pipe-stages");
  const board = document.getElementById("pipe-board");
  if (!stages) return;
  let cur = 0;
  STAGES.forEach((s, i) => {
    const b = document.createElement("button");
    b.type = "button";
    b.className = "stage";
    b.style.setProperty("--tc", s.c);
    b.innerHTML = `<span class="no">${s.no}</span><br><span class="nm">${s.nm}</span><br><span class="arrow">→ ${s.arrow}</span>`;
    b.addEventListener("click", () => { cur = i; render(); });
    stages.appendChild(b);
  });
  function render() {
    const s = STAGES[cur];
    stages.querySelectorAll(".stage").forEach((el, i) => el.classList.toggle("on", i === cur));
    board.style.borderColor = s.c;
    board.style.setProperty("--tc", s.c);
    board.innerHTML =
      `<div class="row"><span class="lbl">資料</span><b>${s.data}</b></div>` +
      `<div class="row"><span class="lbl">成本</span>${s.cost}</div>` +
      `<div class="row"><span class="lbl">學到</span>${s.learn}</div>` +
      `<div class="row"><span class="lbl">產物</span>${s.out}</div>`;
  }
  render();
})();
"""
