"""課程頁內容區（純常數）。改完跑：python3 .claude/skills/make-lesson/scripts/page-fill.py content/local-llm/ollama-vs-vllm
build.sh 不會部署這個檔；它是 index.html 內容區的正本。"""

TITLE = "引擎選型：Ollama vs vLLM"
DESCRIPTION = "同一台機器、同一顆模型，兩個引擎的脾氣差在哪？拉一下請求長度分佈，親眼看見 slot 固定分配與 PagedAttention 的記憶體利用率差十倍——順便拆穿「34.2×」那種標題數字。"

STYLE = r"""
  /* 語義色：橘＝Ollama／slot 固定分配、藍＝vLLM／PagedAttention、灰＝被配走卻沒用到、紅＝陷阱 */
  :root { --c1: #4C72B0; --c2: #DD8452; --c3: #55A868; --cut: #C44E52; --waste: #D9DEE2; }

  .kbd { font-family: var(--mono); background: var(--chip-bg); padding: 1px 6px; border-radius: 5px; font-size: 13px; }
  table.cmp { width: 100%; border-collapse: collapse; font-size: 13.5px; margin: 14px 0; }
  table.cmp th, table.cmp td { border-bottom: 1px solid var(--grid); padding: 8px 10px; text-align: left; vertical-align: top; }
  table.cmp th { font-size: 12px; letter-spacing: .04em; color: var(--ink-soft); font-weight: 800; }
  table.cmp th.oll, table.cmp td.oll { color: var(--c2); }
  table.cmp th.vll, table.cmp td.vll { color: var(--c1); }
  table.cmp td:first-child { font-weight: 800; color: var(--ink); white-space: nowrap; }
  table.cmp tr:hover td { background: var(--chip-bg); }

  .punch { border: 2px solid var(--ink); border-radius: 12px; background: var(--panel);
           padding: 14px 16px; margin: 18px 0; font-size: 15px; font-weight: 800; line-height: 1.7; }
  .punch small { display: block; font-weight: 500; font-size: 13px; color: var(--ink-soft); margin-top: 6px; }

  /* ── hero：場景選擇器 ── */
  #pick { margin-top: 4px; }
  #pick .chips { display: grid; grid-template-columns: repeat(3, 1fr); gap: 7px; margin-bottom: 14px; }
  #pick .chip {
    font: inherit; font-size: 12.5px; font-weight: 700; line-height: 1.35;
    color: var(--ink); background: var(--panel);
    border: 1.5px solid var(--grid); border-radius: 10px;
    padding: 9px 8px; cursor: pointer; text-align: left;
    transition: border-color .15s, background .15s, transform .1s;
  }
  #pick .chip:hover { border-color: var(--ink); transform: translateY(-1px); }
  #pick .chip.on { border-color: var(--ink); border-width: 2px; background: var(--chip-bg); }
  #pick .engines { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
  #pick .eng {
    border: 2px solid var(--grid); border-radius: 12px; padding: 11px 12px;
    background: var(--panel); opacity: .42; transition: all .25s;
  }
  #pick .eng b { display: block; font-size: 15px; margin-bottom: 2px; }
  #pick .eng small { font-size: 12px; color: var(--ink-soft); }
  #pick .eng.win { opacity: 1; transform: scale(1.02); }
  #pick .eng.oll.win { border-color: var(--c2); box-shadow: inset 0 0 0 3px rgba(221,132,82,.12); }
  #pick .eng.oll.win b { color: var(--c2); }
  #pick .eng.vll.win { border-color: var(--c1); box-shadow: inset 0 0 0 3px rgba(76,114,176,.12); }
  #pick .eng.vll.win b { color: var(--c1); }
  #pick .why {
    margin-top: 11px; min-height: 42px; font-size: 13.5px; line-height: 1.65;
    border-left: 3px solid var(--grid); padding-left: 11px; color: var(--ink-soft);
  }
  #pick .why.oll { border-left-color: var(--c2); color: var(--ink); }
  #pick .why.vll { border-left-color: var(--c1); color: var(--ink); }
  @media (max-width: 620px) { #pick .chips { grid-template-columns: 1fr 1fr; } }
"""

WRAP = r"""
<section id="hero">
  <span class="eyebrow">ENGINE · 01</span>
  <h1>引擎選型：<br>Ollama vs vLLM</h1>
  <p style="margin-top:18px">
    同一台電腦、同一顆 8B 模型，換一個推理引擎，體感差很多——但差的地方常常跟你以為的不一樣。
    先別看規格表，<b>點一個最像你的情境</b>，看看該用哪一個：
  </p>

  <div class="hero-demo" id="pick">
    <div class="chips" id="pick-chips"></div>
    <div class="engines">
      <div class="eng oll" id="eng-oll">
        <b>🍚 Ollama</b>
        <small>家用電鍋 — 插電就能煮，單人份剛好</small>
      </div>
      <div class="eng vll" id="eng-vll">
        <b>🏭 vLLM</b>
        <small>中央廚房 — 設定費工，但同時出百人份</small>
      </div>
    </div>
    <div class="why" id="pick-why">九個情境都點一遍——你會發現右邊那格亮起來的時機有個規律。</div>
  </div>

  <p class="note">
    看出規律了嗎？會亮起 vLLM 的四個情境是：<b>同時很多人、同一段長前綴一直重複、
    想把 KV cache 挪到 SSD 或別台機器，以及由前三者堆出來的「正式產品 API」</b>。
    這不是巧合——三件事其實是同一件事。這一課要證明的就是：
    兩個引擎所有面向的差異，都可以回推到同一個源頭：<b>KV cache 的記憶體怎麼發下去</b>。
    右邊的實驗場會把這件事真的算給你看。首次載入約 30–60 秒，正好夠你讀完第 1 節。
  </p>
</section>

<section id="s1">
  <span class="eyebrow">01 · 定位</span>
  <h2>一個求方便，一個求效能</h2>
  <p>
    先把兩者放回它們被造出來的位置。<b>Ollama</b> 是本地端易用工具，底層是
    <span class="kbd">llama.cpp</span>——純 C/C++ 的單一執行檔，沒有 Python、沒有 CUDA runtime 依賴，
    所以 <span class="kbd">ollama run</span> 下載完模型就能跑，Mac、小顯卡、純 CPU 都吃得下。
  </p>
  <p>
    <b>vLLM</b> 是生產級高吞吐推理引擎，底層是 <b>PagedAttention ＋ continuous batching</b>——
    這兩項技術都是為了榨乾 GPU 而生，離開 GPU 就沒有舞台，所以它幾乎必須要有 NVIDIA 顯卡、
    而且 VRAM 要夠。它是很多開源大模型公司發布前會一起做適配的對象，也是不少推論服務的內部選擇。
  </p>
  <p>
    有兩件事常被誤會，先講清楚，免得你用錯理由做決定：
  </p>
  <ul>
    <li><b>「OpenAI 相容 API 是 vLLM 的專利」——不是。</b>
      Ollama 也有，把 <span class="kbd">base_url</span> 指到
      <span class="kbd">http://localhost:11434/v1/</span>、<span class="kbd">api_key</span> 隨便填一個字串
      （它要求要有、但不檢查），官方 <span class="kbd">openai</span> SDK 就能直接打。</li>
    <li><b>「GGUF 只有 Ollama 能跑」——也不是。</b>
      GGUF 是 llama.cpp 專案自己發明的格式，是 Ollama 的主場沒錯，但 vLLM 也支援載入 GGUF。
      只是那不是它的最佳狀態，它主打的是 GPU 側的 AWQ / GPTQ / FP8。</li>
  </ul>
  <p>
    所以選型的分界線不在「有沒有某個功能」，而在<b>脾氣</b>——同一件事，兩者用完全不同的方式做。
    下一節那張表就是把脾氣攤開來看。
  </p>
</section>

<section id="s2">
  <span class="eyebrow">02 · 對照表</span>
  <h2>八個面向，一眼看完</h2>
  <p>
    這張表值得看兩次。第一次由上往下讀，知道差在哪；
    第二次回頭找：<b>其中有一列是其他七列的原因</b>。
  </p>
  <table class="cmp">
    <tr><th>面向</th><th class="oll">Ollama（llama.cpp）</th><th class="vll">vLLM</th></tr>
    <tr><td>安裝門檻</td><td class="oll">極低，<span class="kbd">ollama run</span> 即用</td><td class="vll">較高，需要 Python / CUDA 配置</td></tr>
    <tr><td>KV Cache 管理</td><td class="oll"><b>Slot 固定分配（包廂制）</b></td><td class="vll"><b>PagedAttention 動態分頁（拼桌制）</b></td></tr>
    <tr><td>Prefix Caching</td><td class="oll">陽春，只在 slot 內找相同前綴</td><td class="vll">完整，自動跨請求重用相同前綴 block</td></tr>
    <tr><td>並發能力</td><td class="oll">低～中，slot 有限又容易浪費</td><td class="vll">高，continuous batching 吞吐強</td></tr>
    <tr><td>量化支援</td><td class="oll">強項，GGUF 各種量化</td><td class="vll">主打 GPU：AWQ / GPTQ / FP8</td></tr>
    <tr><td>硬體需求</td><td class="oll">友善，CPU / 小顯卡 / Mac 皆可</td><td class="vll">幾乎必須 NVIDIA GPU，VRAM 要足</td></tr>
    <tr><td>模型切換</td><td class="oll">極方便，多模型隨叫隨載</td><td class="vll">一個實例綁一個模型，重啟才換</td></tr>
    <tr><td>擴展生態</td><td class="oll">內建即全部，無外掛需求</td><td class="vll">可搭 LMCache、PD 分離（Prefill／Decode 拆節點）</td></tr>
  </table>
  <p>
    找到了嗎？答案是<b>第二列</b>。KV Cache 怎麼管，直接決定了 Prefix Caching 做不做得到、
    並發撐不撐得住、能不能接 LMCache 這類外掛——第 3、4、8 列全是它的下游。
    剩下的差異則來自另一條線：<b>C++ 單檔執行 vs PyTorch/CUDA</b> 決定了第 1、6 列的安裝門檻與硬體需求，
    <b>GGUF vs AWQ/FP8</b> 決定了第 5 列各自的主場。
  </p>
  <p>
    整張表其實只有兩個根：<b>記憶體怎麼發</b>，以及<b>底層用什麼寫的</b>。下一節先挖第一個。
  </p>
</section>

<section id="s3">
  <span class="eyebrow">03 · 核心差異</span>
  <h2>包廂制 vs 拼桌制：KV cache 怎麼發</h2>
  <p>
    模型每生成一個 token，都要把前面所有 token 的 key/value 留在 VRAM 裡（就是 KV cache）。
    這塊記憶體怎麼分給同時進來的請求，兩個引擎的答案完全相反。
  </p>
  <p>
    <b>llama.cpp 是包廂制</b>：服務啟動時就預先切好幾個 slot，每個 slot 綁一個 sequence、
    容量等於模型的 context length。開幾個 slot 是啟動參數決定的：
  </p>
  <div class="codeblock">llama-server -c 1024 -np 2
# -np 2 → 開 2 個 slot（預設只有 1 個！）
# -c    → 總 context，會平分給各個 slot</div>
  <p>
    注意那個預設值：<b><span class="kbd">-np</span> 不給就是 1</b>——一個模型同一時間只服務一個生成請求。
    而且包廂訂了就是你的：一個請求只用了 50 個 token，slot 卻佔著 4096，剩下的<b>整塊空著也沒人能用</b>，
    利用率可能只剩個位數。
  </p>
  <p>
    <b>vLLM 是拼桌制</b>：記憶體切成小 block（一塊 16 個 token），誰要誰拿、用多少拿多少，
    只有最後一塊沒填滿才有零頭。幾乎不浪費，還能讓不同請求<b>共用同一段前綴的 block</b>。
  </p>
  <p>
    到右邊拉「請求平均長度」跟「離散度」，兩制的利用率會當場重算。預設參數下
    （8 個請求、平均 400 tokens、slot context 4096）算出來是
    <b>slot 制 9.1%、paged 制 98.1%</b>——同一批請求，slot 制要多花約 <b>10.8 倍</b>的記憶體才裝得下。
    然後把平均長度拉到最右邊，看差距怎麼塌掉。
  </p>
  <button class="golab" data-nb="1️⃣">到右邊拉拉桿，看兩制的利用率</button>
  <p>
    第二張圖把帳面數字換成人：同一塊 KV 預算（預設 48k tokens），
    <b>slot 制永遠只有 11 個位子</b>——那是一條水平線，請求短不短它一點都不在乎；
    paged 制在平均 400 tokens 時能同時服務約 <b>107 個</b>請求，等請求長到接近 context 上限才掉回來。
  </p>
  <div class="punch">
    Continuous batching 要能隨時插入、移出請求，前提是記憶體能靈活動態分配。
    <small>所以「高並發」不是 vLLM 的另一項功能，而是 PagedAttention 的直接結果——
    先有拼桌，才有隨到隨坐。</small>
  </div>
</section>

<section id="s4">
  <span class="eyebrow">04 · 常駐與卸載</span>
  <h2>VRAM 的兩種脾氣：用完就放 vs 開著就佔</h2>
  <p>
    第二個差異跟記憶體<b>多寡</b>無關，跟<b>什麼時候佔著</b>有關。
  </p>
  <ul>
    <li><b>Ollama：用完就放。</b>第一次推理才把模型載進 GPU，閒置預設 5 分鐘自動卸載、把 VRAM 還給你。
      想讓它別走，設 <span class="kbd">OLLAMA_KEEP_ALIVE=-1</span> 就永久常駐。</li>
    <li><b>vLLM：開著就佔。</b>權重加 KV cache 空間在啟動時全部預配好，之後一直佔著 GPU——
      換來的是穩定可預測的高吞吐。</li>
  </ul>
  <p>這筆交易的價碼，實測（RTX 4090、Llama 3.1 8B Q4_K_M、閒置後第一次請求）長這樣：</p>
  <table class="cmp">
    <tr><th>指標</th><th class="oll">Ollama</th><th class="vll">vLLM</th></tr>
    <tr><td>冷啟動首 token 延遲</td><td class="oll">8.3 秒</td><td class="vll">0.4 秒</td></tr>
    <tr><td>冷啟動 tokens/s</td><td class="oll">31</td><td class="vll">128（約 4.2×）</td></tr>
    <tr><td>暖機後穩態 tokens/s</td><td class="oll">138</td><td class="vll">142（幾乎一樣）</td></tr>
    <tr><td>VRAM 佔用</td><td class="oll">6.4 GB</td><td class="vll">8.2 GB</td></tr>
  </table>
  <p>
    第三列是這張表最容易被跳過、也最重要的一列：<b>暖機之後兩者穩態速度幾乎一樣</b>（138 vs 142）。
    你在自己電腦上「感覺 vLLM 比較快」的那個快，多半來自第一列——<b>差別只在冷啟動</b>。
  </p>
  <p>
    那冷啟動多常發生？取決於你的使用節奏。右邊第三張圖模擬一段時間內零星進來的請求
    （到達時間是抽出來的教學模型，不是實測），畫出誰在什麼時候佔著 GPU。
    預設參數（平均間隔 8 分鐘、卸載門檻 5 分鐘、4 小時）下：27 個請求裡有
    <b>17 個踩到冷啟動（63%）</b>，光等模型上車就多花了 141 秒；
    但同一段時間 Ollama 平均只佔著 <b>2.9 GB</b>，vLLM 從頭到尾佔滿 8.2 GB。
  </p>
  <button class="golab" data-nb="2️⃣">到右邊調你的使用節奏</button>
  <p>
    把「平均間隔」拉到 1 分鐘（像真的有人在用的產品），冷啟動幾乎歸零、Ollama 也一直佔著 VRAM，
    兩邊的差別瞬間變小；拉到 20 分鐘（你自己偶爾問一句），幾乎每一發都是冷啟動，
    但你的 GPU 有八成時間是空的，可以拿去跑別的事。
    <b>沒有誰對誰錯，只有你願不願意用閒置的 VRAM 換那 8 秒。</b>
  </p>
  <p class="note">
    順帶一提，Ollama 另有 Cloud 模式（<span class="kbd">ollama run gemma4:31b-cloud</span>）可以試更大的模型，
    免費額度按 GPU 時間計費、有每 5 小時與每 7 天的雙重上限（社群回報約每 5 小時 135 次請求、
    每週 500 萬 token 的量級，尖峰時段會降速）——夠拿來聊天、試模型，撐不了持續的 agent 工作。
  </p>
</section>

<section id="s5">
  <span class="eyebrow">05 · 讀數字</span>
  <h2>「34.2×」不是快 34 倍</h2>
  <p>
    做完選型你一定會遇到 benchmark 圖：三根柱子、最右邊那根特別高，配一個大大的倍數。
    這一節用一個真實的例子練習怎麼讀它——引用的是一份公開的吞吐對照
    （Ollama 跑 Q4_K_M 4-bit、vLLM 跑 BF16 16-bit，第三根柱子是
    <b>32 個人同時打</b>時整台機器的總吞吐 <b>1606.78 tokens/s</b>，標題倍數 34.2×，
    第 1 對第 2 根是 4.6×）。
  </p>
  <p>兩個陷阱疊在一起：</p>
  <ul>
    <li><b>總量 vs 單人。</b>1606.78 是 32 個人<b>加起來</b>的量。攤到每個人身上是
      50 tokens/s，對上 Ollama 的 47——<b>只有 1.07×</b>。
      標題那個 34.2× 是機器的，不是你的。</li>
    <li><b>精度不同。</b>第 1 根跑 4-bit、第 2 根跑 16-bit，本來就不是同一件事。
      理論上 4-bit 更省記憶體、更該快，實際卻慢了 4.6 倍——那是量化實作與 kernel 的差別，
      不能全記在「引擎比較快」頭上。</li>
  </ul>
  <button class="golab" data-nb="3️⃣">到右邊看兩張圖並排：總量 vs 每人</button>
  <p>
    這不是要戳破 vLLM——<b>吞吐本來就是它的賣點</b>。32 個人同時打還能維持每人 50 tokens/s，
    這正是 slot 制做不到的事（回頭看 03 節那條水平線）。只是它換來的是<b>服務更多人</b>，
    不是「讓你一個人快 34 倍」。
  </p>
  <div class="punch">
    看到大倍數，先問三句：<b>幾個人同時打？兩邊精度一不一樣？倍數是總量還是單人？</b>
    <small>這三句問完，多數 benchmark 圖都會回到它該有的大小——包含別人給你的，和你自己做給老闆看的。</small>
  </div>
</section>

<section id="s6">
  <span class="eyebrow">06 · 決策清單</span>
  <h2>什麼時候選誰</h2>
  <p>
    把前面五節收成一張可以帶去開會的清單。左欄的共同點是<b>少量、間歇、要方便</b>；
    右欄的共同點是<b>很多人、重複前綴、要壓榨 GPU</b>。
  </p>
  <table class="cmp">
    <tr><th class="oll">選 Ollama，當你…</th><th class="vll">選 vLLM，當你…</th></tr>
    <tr>
      <td class="oll">在筆電 / Mac 上本地玩模型（CPU 與 Apple Silicon 都能跑）</td>
      <td class="vll">要做正式產品的後端 API（高吞吐、OpenAI 相容、穩定）</td>
    </tr>
    <tr>
      <td class="oll">做快速原型 / Demo / POC，需要常換模型</td>
      <td class="vll">有高並發（多人同時打），continuous batching 吞吐遠勝</td>
    </tr>
    <tr>
      <td class="oll">要在現場示範，環境穩、指令簡單最重要</td>
      <td class="vll">有很長的 system prompt 一直重複用（自動 prefix caching 大降 TTFT）</td>
    </tr>
    <tr>
      <td class="oll">使用者少、請求間歇，單請求延遲已經夠好</td>
      <td class="vll">想把 KV cache 存到 SSD 或跨實例共享（vLLM + LMCache，Ollama 做不到）</td>
    </tr>
    <tr>
      <td class="oll">顯卡小、想跑量化模型（GGUF ＋ CPU/GPU 混合是它的主場）</td>
      <td class="vll">在意 GPU 利用率與成本（PagedAttention 不浪費記憶體）</td>
    </tr>
  </table>
  <p>
    一條夠用的量尺：<b>有 NVIDIA GPU、並發超過 20～50、而且是要上線的產品 API → vLLM</b>；
    其餘情況先 Ollama。
  </p>
  <h3 style="font-size:16px;margin:22px 0 8px">順帶一提：GGUF 與 MLX</h3>
  <p>
    同一顆模型會有多種打包格式，模型庫（如 <span class="kbd">ollama.com/library</span>）上常常兩種都有：
  </p>
  <ul>
    <li><b>GGUF</b>：跨平台通用，記憶體省、相容性最好、生態最成熟——哪裡都能跑。</li>
    <li><b>MLX（4-bit）</b>：Apple 原生格式，同尺寸模型下更快，但<b>只在 Apple Silicon 有效</b>。</li>
  </ul>
  <p>規則簡單到一句話：<b>在 Mac 上，有 MLX 就選 MLX，沒有再退回 GGUF；其他平台一律 GGUF。</b></p>
  <div class="punch">
    不確定就先用 Ollama 起步；流量與吞吐撐不住時，再換上 vLLM。
    <small>兩者都有 OpenAI 相容 API，換引擎時你的應用程式碼幾乎只要改一行 <span class="kbd">base_url</span>——
    這就是「先起步」之所以安全的原因。</small>
  </div>
</section>

<section id="s7">
  <span class="eyebrow">07 · 部署觀</span>
  <h2>真的要架起來的時候</h2>
  <p>
    決定用 vLLM 之後，別從空白檔案開始寫啟動指令。<b>官方 recipes 才是起點</b>：
    <a href="https://recipes.vllm.ai" target="_blank" rel="noopener">recipes.vllm.ai</a>
    收錄了各個模型的啟動指令與 compose 檔，大部分複製下來直接就能跑。
  </p>
  <p>
    但它偶爾會缺件——最典型的是<b>多模態模型缺依賴</b>。例如語音轉文字的 Qwen3-ASR，
    官方指令跑起來會缺音訊處理的套件，要自己補上 <span class="kbd">ffmpeg</span> 與
    <span class="kbd">librosa / soundfile / av / resampy</span>：
  </p>
  <div class="codeblock">asr:
  image: vllm-asr-audio:local
  build:
    dockerfile_inline: |
      FROM vllm/vllm-openai:latest
      RUN apt-get install -y ffmpeg && \
          pip install librosa soundfile av resampy
  ports: ["18003:8000"]
  command:
    - Qwen/Qwen3-ASR-1.7B
    - --served-model-name qwen3-asr
    - --max-model-len "4096"
    - --gpu-memory-utilization "0.24"
    - --max-num-seqs "4"
    - --enforce-eager</div>
  <p>
    注意那兩個參數：<span class="kbd">--gpu-memory-utilization</span> 就是在講這一課的主題——
    你要撥多少比例的 VRAM 給這個實例預配（權重＋KV cache）；
    <span class="kbd">--max-num-seqs</span> 則是同時最多幾個 sequence。
    <b>同一張卡要塞好幾個模型時，這兩個數字就是你的預算分配表。</b>
  </p>
  <p>
    然後是最務實的一招：<b>整段丟給 AI 執行、讓它自己修到好</b>。
    把 recipe、錯誤訊息、健康檢查一起貼給它，錯了讓它改、改完再測，
    直到服務健康、測試通過為止。部署失敗的訊息通常都很直白（缺套件、port 撞了、VRAM 不夠），
    這正是 AI 最擅長的迴圈。
  </p>
  <h3 style="font-size:16px;margin:22px 0 8px">而在部署之前：先確認模型值得部署</h3>
  <p>
    選模型不要只看參數量。兩個成本很低的動作可以幫你省下整晚的部署時間：
  </p>
  <ul>
    <li><b>去 Hugging Face Spaces 線上試玩。</b>多數熱門模型都有官方 Space，
      不用裝任何東西就能丟輸入進去。中文使用者有個好用的測試句：
      丟「臺灣用繁體字」「台北 101」進去，看它會不會把繁體簡化掉、或把數字辨錯——
      這種毛病部署完才發現最痛。</li>
    <li><b>再看 Arena 的盲測排名。</b>
      <a href="https://arena.ai/leaderboard" target="_blank" rel="noopener">arena.ai</a>
      不是固定題庫，而是網友盲測投票、再用統計模型把幾百萬次投票換算成排名——
      比單一 benchmark 分數更能反映「一般人用起來覺得好不好」。</li>
  </ul>
  <p>
    順序記起來就好：<b>Spaces 試玩 → Arena 對排名 → recipes 抄配方 → AI 陪你除錯</b>。
  </p>
</section>

<section id="s8">
  <span class="eyebrow">08 · 實戰</span>
  <h2>換你動手</h2>
  <p>右邊實驗場最後一節是你的沙盒，三個挑戰由易到難（每個都有折疊解答，卡住就打開）：</p>
  <div class="ex">
    <span class="lv">LEVEL 1</span>
    <p>把「請求平均長度」拉到 3800、「離散度」拉到 0，看兩制的利用率變成幾 %，
      並用一句話解釋<b>為什麼差距不見了</b>。（提示：浪費＝配額減去實際用量。）</p>
  </div>
  <div class="ex">
    <span class="lv">LEVEL 2</span>
    <p>掃描平均長度 200 → 4000，畫出「slot 制要多花幾倍記憶體」的曲線，
      找出這個倍數<b>掉到 2× 以下</b>的平均長度。那個交叉點就是你的選型分水嶺。</p>
  </div>
  <div class="ex">
    <span class="lv">LEVEL 3</span>
    <p>加進 <b>prefix caching</b>：假設每個請求前面都掛著同一段 800 token 的 system prompt，
      PagedAttention 可以讓所有請求共用那幾塊 block，slot 制不行。重算兩制的配置量，
      再回答：請求數從 5 變成 20 時，差距是怎麼變的？</p>
  </div>
  <button class="golab" data-nb="4️⃣">到右邊的實驗區開工</button>
  <p style="margin-top:18px">
    做完這三題，你對「引擎的差異來自記憶體怎麼管」就不只是聽說了，是自己算過。
    <b>下一課我們把鏡頭再往裡推一層</b>：記憶體管好之後，模型每一步到底怎麼從幾萬個字裡挑出下一個字——
    那幾顆你在 API 裡看過卻沒調過的取樣參數，其實各自在做很不一樣的事。
  </p>
</section>

<section id="quiz">
  <span class="eyebrow">09 · 驗收</span>
  <h2>情境測驗</h2>
  <p>離開前試試看：下面的情境都真的會遇到。每題選一個你認為的最佳做法，選了馬上看得到解釋。</p>
  <div data-quiz>

    <div class="quiz-q" data-answer="C">
      <p class="quiz-tag">Q1 <span class="qtype">情境題</span></p>
      <h3>你要把一個內部問答服務上線：尖峰約 30 人同時打，每次請求都掛著同一份 6000 token 的規章當 system prompt，機器上有一張 NVIDIA 顯卡。該用哪個引擎、為什麼？</h3>
      <div class="quiz-opts">
        <button type="button" class="quiz-opt" data-k="A">A. Ollama，因為安裝簡單，先上線再說；不夠快就把機器換好一點的</button>
        <button type="button" class="quiz-opt" data-k="B">B. Ollama，並用 <code>llama-server -np 30</code> 開 30 個 slot 對應 30 個人</button>
        <button type="button" class="quiz-opt" data-k="C">C. vLLM，高並發靠 continuous batching，重複的長前綴還能被 prefix caching 跨請求重用</button>
        <button type="button" class="quiz-opt" data-k="D">D. 兩個都架，用 nginx 隨機分流，哪個活著就用哪個</button>
      </div>
      <div class="quiz-fb" aria-live="polite"><p>這題三個條件全部指向 vLLM：<b>30 人同時打</b>（continuous batching）、<b>長前綴重複</b>（自動 prefix caching 跨請求重用相同 block，大降 TTFT）、<b>有 NVIDIA GPU</b>（vLLM 的前提）。A 的問題是換機器解不了架構問題——slot 制的位子數由啟動參數決定，跟卡多好無關。B 是常見誤解：<code>-c</code> 是總 context，會平分給各 slot，開 30 個 slot 等於每人分到 1/30 的 context，6000 token 的規章根本放不進去；而且 slot 制的前綴共享只在同一個 slot 內找，30 份規章要各存一份。D 沒解決任何問題，只是把兩份維運成本都扛下來。</p></div>
    </div>

    <div class="quiz-q" data-answer="B">
      <p class="quiz-tag">Q2 <span class="qtype">情境題</span></p>
      <h3>你在自己的 MacBook 上做原型，一天大概問十幾次，會在三、四個模型之間比較答案，希望不用時 GPU 記憶體還給系統。該怎麼選？</h3>
      <div class="quiz-opts">
        <button type="button" class="quiz-opt" data-k="A">A. vLLM，效能最好，順便為之後上線做準備</button>
        <button type="button" class="quiz-opt" data-k="B">B. Ollama，多模型隨叫隨載、閒置 5 分鐘自動卸載；Mac 上優先挑 MLX 版，沒有再用 GGUF</button>
        <button type="button" class="quiz-opt" data-k="C">C. Ollama，但設 <code>OLLAMA_KEEP_ALIVE=-1</code> 讓所有模型都常駐，避免每次都等冷啟動</button>
        <button type="button" class="quiz-opt" data-k="D">D. 都不用，直接呼叫雲端 API 比較快</button>
      </div>
      <div class="quiz-fb" aria-live="polite"><p>三個條件（Mac、要常換模型、希望閒置時還記憶體）正好命中 Ollama 的三個強項：Apple Silicon 友善、多模型隨叫隨載、閒置自動卸載。而在 Mac 上同一顆模型若有 MLX 版就選 MLX（同尺寸更快），沒有再退回 GGUF。A 幾乎行不通——vLLM 天生 GPU-bound、實務上綁 NVIDIA，而且一個實例只綁一個模型，「比較三四個模型」要重啟三四次。C 部分正確但方向相反：你明講了希望不用時把記憶體還回來，永久常駐正好違反這個需求（而且四個模型全常駐，VRAM 也未必塞得下）。D 是換題目，不是回答題目——本課的前提就是要在自己機器上跑。</p></div>
    </div>

    <div class="quiz-q" data-answer="D">
      <p class="quiz-tag">Q3 <span class="qtype dx">錯誤診斷</span></p>
      <h3>同事拿一張 benchmark 圖來說服你換引擎：「vLLM 快 34 倍」。圖上的數字如下。這個結論最主要的問題是？</h3>
      <div class="codeblock">bar 1  Ollama  Q4_K_M  單一請求
bar 2  vLLM    BF16    單一請求        (bar1 的 4.6x)
bar 3  vLLM    BF16    32 個請求同時    1606.78 tokens/s  ← 標題寫 34.2x</div>
      <div class="quiz-opts">
        <button type="button" class="quiz-opt" data-k="A">A. 沒問題，34.2× 就是 1606.78 除以第一根柱子，算術是對的</button>
        <button type="button" class="quiz-opt" data-k="B">B. 問題出在 vLLM 沒開 prefix caching，數字被低估了</button>
        <button type="button" class="quiz-opt" data-k="C">C. 問題是這台機器的 GPU 太好，換一般顯卡就沒有 34 倍</button>
        <button type="button" class="quiz-opt" data-k="D">D. 第三根是 32 人的<b>總量</b>，攤到每人只剩約 50 tokens/s（約 1.07×）；而且 bar 1 與 bar 2 精度不同，那 4.6× 也不能全記在引擎頭上</button>
      </div>
      <div class="quiz-fb" aria-live="polite"><p>兩個陷阱疊在一起。第一，<b>總量不是每個人的體感</b>：1606.78 ÷ 32 ≈ 50 tokens/s，對上 Ollama 的約 47，實際只有 1.07×——34.2× 是機器的，不是使用者的。第二，<b>bar 1 與 bar 2 精度不同</b>（Q4_K_M 4-bit vs BF16 16-bit），那是兩件事的比較，4.6× 裡有一部分來自量化實作與 kernel，不是純粹的引擎差異。A 的算術確實沒錯，錯在把「機器總吞吐比」講成「快 34 倍」；B、C 都是症狀相似但方向不對——問題不在數字量錯了，而在<b>拿來比的東西不對等</b>。正確的讀法是問三句：幾個人同時打？兩邊精度一不一樣？倍數是總量還是單人？</p></div>
    </div>

    <div class="quiz-q" data-answer="C">
      <p class="quiz-tag">Q4 <span class="qtype dx">錯誤診斷</span></p>
      <h3>你用 Ollama 架了一個內部小助手，同事回報：「早上第一次問要等快 10 秒才出字，之後就順了；午休回來又變慢。」實測數據如下。最可能的原因與修法是？</h3>
      <div class="codeblock">實測（RTX 4090、Llama 3.1 8B Q4_K_M、閒置後第一次請求）
                    Ollama    vLLM
冷啟動首 token       8.3 秒    0.4 秒
暖機後穩態 tokens/s   138      142</div>
      <div class="quiz-opts">
        <button type="button" class="quiz-opt" data-k="A">A. 模型太大，該換更小的量化版本才不會慢</button>
        <button type="button" class="quiz-opt" data-k="B">B. 網路或反向代理有問題，第一發請求被 DNS／TLS 拖慢</button>
        <button type="button" class="quiz-opt" data-k="C">C. 閒置超過 5 分鐘模型被卸載了，那 8.3 秒是把模型搬回 VRAM 的時間；要它一直待命就設 <code>OLLAMA_KEEP_ALIVE=-1</code>，或接受這個代價換閒置時的 VRAM</button>
        <button type="button" class="quiz-opt" data-k="D">D. slot 不夠用，請求在排隊；把 <code>-np</code> 調大就好</button>
      </div>
      <div class="quiz-fb" aria-live="polite"><p>「第一次慢、之後順、閒一陣子又慢」是 Ollama 閒置卸載的典型指紋：預設 5 分鐘沒人用就把模型從 VRAM 卸掉，下一發請求得重新載入，也就是那 8.3 秒。修法有兩條，取捨在你：<code>OLLAMA_KEEP_ALIVE=-1</code> 讓它常駐（換來 VRAM 一直被佔著），或接受冷啟動、把閒置的 VRAM 留給別的用途。A 沒對上症狀——真是模型太大，<b>每一次</b>都會慢，不會只有第一次；而且穩態 138 tokens/s 已經很好了。B 症狀相似但排除得掉：同一條連線午休後再變慢，指向的是伺服器端的狀態而不是網路交握。D 是排隊症狀（大家<b>同時</b>都慢），跟「第一發慢、後面快」的時間形狀不同。</p></div>
    </div>

    <div class="quiz-q" data-answer="A">
      <p class="quiz-tag">Q5 <span class="qtype">情境題</span></p>
      <h3>你在 vLLM 上跑一個聊天服務，多數請求只有兩三百 token，但 GPU 記憶體一直很吃緊，同時能服務的人數上不去。想先確認「換成 slot 固定分配會不會比較省」，最有效的驗證方式是？</h3>
      <div class="quiz-opts">
        <button type="button" class="quiz-opt" data-k="A">A. 不用驗——請求越短、長度越參差，slot 制賠得越多；短請求正是 PagedAttention 領先最多的場景，該調的是 <code>--gpu-memory-utilization</code> 與 <code>--max-model-len</code></button>
        <button type="button" class="quiz-opt" data-k="B">B. 兩邊各架一套跑一週 A/B，用真實流量比較同時在線人數</button>
        <button type="button" class="quiz-opt" data-k="C">C. 把 vLLM 的 block 大小調到跟 context 一樣大，模擬 slot 制再看記憶體用量</button>
        <button type="button" class="quiz-opt" data-k="D">D. 改用更高的量化等級，記憶體省了並發自然就上去</button>
      </div>
      <div class="quiz-fb" aria-live="polite"><p>這題考的是「知道結論就不用做實驗」。兩制的差距是一條可以直接推的曲線：請求越短、長度越參差，slot 制浪費越多——課裡預設參數（平均 400 tokens）算出來就是 9.1% vs 98.1%。你的請求只有兩三百 token，正是 paged 制領先最多的區間，換過去只會更糟。真正該做的是調 vLLM 自己的旋鈕：撥更高比例的 VRAM 給 KV cache（<code>--gpu-memory-utilization</code>）、把 <code>--max-model-len</code> 收到實際需要的長度。B 能執行但代價極高——花一週驗一件算得出來的事。C 等於自廢武功：把 block 撐到 context 大小，就是把拼桌制改回包廂制。D 部分正確（量化確實省記憶體）但答錯了問題，而且會動到輸出品質，跟「slot 還是 paged」無關。</p></div>
    </div>

    <div class="quiz-score" data-score></div>
  </div>
</section>

<div class="endnav">
  <a href="/sampling-params/">
    <span class="tag">下一課</span>
    <b>取樣參數：模型怎麼挑下一個字 →</b>
  </a>
  <a href="/local-llm/">
    <span class="tag">主題</span>
    <b>‹ 回「個人地端大語言模型實作」課程列表</b>
  </a>
</div>
"""

SCRIPT = r"""
/* hero：場景選擇器——點一個情境，亮出推薦引擎與一句理由 */
const SCENES = [
  ["筆電 / Mac 上自己玩模型", "oll", "裝了就跑，CPU 與 Apple Silicon 都吃得下——vLLM 天生 GPU-bound，離開 NVIDIA 卡就沒有舞台。"],
  ["Demo 給客戶，要常換模型", "oll", "多模型隨叫隨載，切換極方便；vLLM 一個實例綁一個模型，換模型要重啟。"],
  ["上課 / 會議現場示範", "oll", "指令簡單、環境穩，不容易在台上出包——這是「不出事」比「跑得快」重要的場合。"],
  ["顯卡只有 8GB", "oll", "GGUF 各種量化 ＋ CPU/GPU 混合是它的主場；vLLM 需要 VRAM 足夠才有得談。"],
  ["一天只問幾次，GPU 還要做別的", "oll", "閒置 5 分鐘自動卸載、把 VRAM 還你；代價是下一次要等約 8 秒的冷啟動。"],
  ["正式產品的後端 API", "vll", "高吞吐、OpenAI 相容、行為穩定可預測——啟動就預配好資源，不會突然去載模型。"],
  ["30 個人同時打同一台機器", "vll", "continuous batching 讓大家共用 GPU 而不是排隊；slot 制的位子數是啟動時就切死的。"],
  ["同一段長 system prompt 一直重送", "vll", "自動 prefix caching 跨請求重用相同的 block，TTFT 大降；slot 制只能在自己那格內找。"],
  ["KV cache 想存 SSD / 跨機器共享", "vll", "可以搭 LMCache、PD 分離把 prefill 與 decode 拆開——這條路 Ollama 沒有。"],
];

const chipsEl = document.getElementById("pick-chips");
const whyEl = document.getElementById("pick-why");
const engOll = document.getElementById("eng-oll");
const engVll = document.getElementById("eng-vll");

if (chipsEl) {
  SCENES.forEach(([label, who, why], i) => {
    const b = document.createElement("button");
    b.type = "button";
    b.className = "chip";
    b.textContent = label;
    b.addEventListener("click", () => {
      chipsEl.querySelectorAll(".chip").forEach((c) => c.classList.remove("on"));
      b.classList.add("on");
      engOll.classList.toggle("win", who === "oll");
      engVll.classList.toggle("win", who === "vll");
      whyEl.className = "why " + who;
      whyEl.innerHTML =
        "<b>" + (who === "oll" ? "🍚 Ollama" : "🏭 vLLM") + "</b> — " + why;
    });
    chipsEl.appendChild(b);
  });
}
"""
