"""課程頁內容區（純常數）。改完跑：python3 .claude/skills/make-lesson/scripts/page-fill.py content/local-llm/kv-offload
build.sh 不會部署這個檔；它是 index.html 內容區的正本。"""

TITLE = "KV Cache 分層：LMCache 與 SSD 卸載"
DESCRIPTION = "KV cache 放不下時往 CPU RAM、SSD 一層層丟，划算嗎？用真的算的分層時間模型看懂「拿 IO 換計算」——計算越重越賺，但個人場景多半根本用不到，先確認你真的需要。"

STYLE = r"""
  /* 語義色：藍＝GPU 層、橘＝CPU RAM 層、綠＝SSD 層、紅＝重算（冷啟動） */
  :root { --c1: #4C72B0; --c2: #DD8452; --c3: #55A868; --cut: #C44E52; }

  /* hero：四層儲存互動 */
  #kv-tiers .stack { display: flex; flex-direction: column; gap: 6px; margin-bottom: 12px; }
  #kv-tiers .tier { display: flex; align-items: center; gap: 10px; width: 100%; font: inherit; text-align: left;
    color: var(--ink); background: var(--panel); border: 2px solid var(--grid); border-radius: 10px;
    padding: 9px 12px; cursor: pointer; transition: border-color .15s, background .15s; }
  #kv-tiers .tier:hover { border-color: var(--ink-soft); }
  #kv-tiers .tier.on { border-color: var(--tc); background: var(--chip-bg); }
  #kv-tiers .tier .bar { width: 6px; align-self: stretch; border-radius: 3px; background: var(--tc); }
  #kv-tiers .tier .nm { font-weight: 800; font-size: 14.5px; }
  #kv-tiers .tier .sub { font-family: var(--mono); font-size: 11.5px; color: var(--ink-soft); }
  #kv-tiers .tier .bw { margin-left: auto; font-family: var(--mono); font-size: 12px; font-weight: 700; color: var(--tc); white-space: nowrap; }
  #kv-tiers .detail { border: 2px solid var(--ink); border-radius: 12px; padding: 12px 14px; font-size: 14px; line-height: 1.75; }
  #kv-tiers .detail .lbl { font-size: 11.5px; letter-spacing: .07em; font-weight: 800; color: var(--ink-soft); margin-bottom: 4px; }
  #kv-tiers .detail .t { display: inline-block; font-family: var(--mono); font-weight: 800; background: var(--chip-bg); border-radius: 6px; padding: 2px 8px; }
  #kv-tiers .base { margin-top: 10px; font-size: 13px; line-height: 1.7; color: var(--ink-soft);
    border-left: 3px solid var(--cut); padding-left: 10px; }
  #kv-tiers .base b { color: var(--cut); }

  table.cmp { width: 100%; border-collapse: collapse; font-size: 13.5px; margin: 14px 0; }
  table.cmp th, table.cmp td { border-bottom: 1px solid var(--grid); padding: 8px 10px; text-align: left; vertical-align: top; }
  table.cmp th { font-size: 12px; letter-spacing: .04em; color: var(--ink-soft); }
  table.cmp td.n { font-family: var(--mono); font-weight: 800; white-space: nowrap; }
  .kbd { font-family: var(--mono); background: var(--chip-bg); padding: 1px 6px; border-radius: 5px; font-size: 13px; }
  .src { font-size: 12.5px; color: var(--ink-soft); margin-top: -6px; }
"""

WRAP = r"""
<section id="hero">
  <span class="eyebrow">OFFLOAD · 05 · 分層儲存與 SSD 卸載</span>
  <h1>KV Cache 分層：<br>LMCache 與 SSD 卸載</h1>
  <p style="margin-top:18px">
    上一課你算的是「同一段前綴重複送，命中快取就便宜」。這一課把同一筆帳搬回自己的機器：
    快取<b>放不下</b>的時候，能不能往 CPU RAM、甚至往 SSD 一層層丟，下次再撈回來就不用重算？
    先點點看這四層各是什麼角色——右邊那欄是<b>把一段 10k token 的前綴從那一層拿回 GPU</b>要多久。
  </p>

  <div class="hero-demo" id="kv-tiers">
    <div class="stack" id="kv-stack"></div>
    <div class="detail" id="kv-detail"></div>
    <div class="base" id="kv-base"></div>
  </div>

  <p class="note">
    右邊的實驗場是真的 Python（在你的瀏覽器裡跑，不用安裝任何東西）。
    首次載入約需 30–60 秒，正好夠你讀完第 1 節。這一課只有兩筆帳要算：
    <b>KV 有多大</b>、<b>載回來比重算快多少</b>——兩筆都在右邊真的算，
    改壞了重新整理就復原。
  </p>
</section>

<section id="s1">
  <span class="eyebrow">01 · 問題</span>
  <h2>首 token 的延遲，幾乎全是 prefill</h2>
  <p>
    使用者感受到的「它怎麼還不開始講話」＝ TTFT（time to first token），而 TTFT 幾乎等於
    <b>prefill</b>：把整段輸入的 K/V 算出來。長文件、長 system prompt、RAG 的固定知識前綴——
    每來一次就從頭算一次。前綴越長，等越久。
  </p>
  <p>vLLM 內建的 prefix cache 會幫你省掉重複的部分，但它有三個天生的限制：</p>
  <table class="cmp">
    <tr><th>限制</th><th>後果</th></tr>
    <tr><td><b>只活在 GPU 記憶體</b></td><td>容量就是扣掉模型權重之後剩下的那點 VRAM，通常是 GB 級</td></tr>
    <tr><td><b>大家互相擠壓</b></td><td>多使用者、長上下文同時在線，LRU 隨時把你的前綴逐出去</td></tr>
    <tr><td><b>沒有任何持久層</b></td><td>server 一重啟全部歸零，熱門前綴又得從頭 prefill 一輪</td></tr>
  </table>
  <p>
    所以第一件事不是急著裝東西，是<b>先算你的 KV 到底有多大</b>——
    這個數字決定它應該待在哪一層。
    公式就是<a href="/kv-cache/">第 3 課</a>那條：每個 token 的 KV 只跟架構有關，
    跟你問什麼無關。
  </p>
  <button class="golab" data-nb="1️⃣">到右邊 1️⃣ 算你的模型每 token 要多少 KV</button>
</section>

<section id="s2">
  <span class="eyebrow">02 · 分層儲存</span>
  <h2>LMCache：GPU 放不下的 KV，往下收</h2>
  <p>
    <a href="https://github.com/lmcache/lmcache" target="_blank" rel="noopener">LMCache</a>
    以 <b>KV connector</b> 的形式掛進 vLLM engine，把單層的 GPU KV pool 變成一疊：
    GPU 逐出的 KV 先收進 CPU RAM，再往下收進本機 SSD，還可以再往外接遠端後端。
    同一段前綴下次出現時，<b>從下層把算好的 KV 撈回 GPU，直接跳過 prefill</b>。
  </p>
  <p>
    本質很單純：<b>拿 IO 換計算</b>。搬運要花時間，但只要搬運比重算便宜，你就賺。
    所以模型計算越重、前綴越長，這筆交換就越划算——這是全課的主軸，右邊 2️⃣ 會把兩條線畫給你看。
  </p>
  <p>vLLM 自己也做了一部分，分工大致是這樣：</p>
  <table class="cmp">
    <tr><th>能力</th><th>vLLM 原生</th><th>LMCache</th></tr>
    <tr><td>KV 從 prefill 端傳給 decode 端</td><td>✅（靠 connector）</td><td>✅</td></tr>
    <tr><td>CPU RAM KV offload</td><td>✅</td><td>✅</td></tr>
    <tr><td><b>本機 SSD KV offload</b></td><td>❌ 原生沒有</td><td>✅</td></tr>
    <tr><td>Redis / S3 等遠端 KV</td><td>❌</td><td>✅</td></tr>
    <tr><td>KV sharing（跨請求、跨副本共用同一份）</td><td>部分靠 connector</td><td>✅ 核心功能</td></tr>
    <tr><td>快取的持久化層</td><td>❌</td><td>✅</td></tr>
  </table>
  <button class="golab" data-nb="2️⃣">到右邊 2️⃣ 看「載回」與「重算」兩條線怎麼分岔</button>
</section>

<section id="s3">
  <span class="eyebrow">03 · 怎麼開</span>
  <h2>兩件事：掛 connector、選層</h2>
  <p>第一件事在啟動參數，把 LMCache 掛成 KV connector：</p>
  <div class="codeblock">vllm serve &lt;model&gt; \
  --kv-transfer-config '{"kv_connector":"LMCacheConnectorV1","kv_role":"kv_both"}'</div>
  <p><span class="kbd">kv_role=kv_both</span> 是同時「存」與「取」——只存不取或只取不存都是有意義的角色，做 prefill／decode 分離時會用到。</p>
  <p>第二件事在環境變數，決定 KV 往下收到哪一層：</p>
  <table class="cmp">
    <tr><th>環境變數</th><th>作用</th><th>示範值</th></tr>
    <tr><td class="n">LMCACHE_CHUNK_SIZE</td><td>幾個 token 切成一塊（快取的對齊單位）</td><td class="n">256</td></tr>
    <tr><td class="n">LMCACHE_LOCAL_CPU</td><td>開／關 CPU RAM 層</td><td class="n">False</td></tr>
    <tr><td class="n">LMCACHE_LOCAL_DISK</td><td>磁碟層路徑（<span class="kbd">file://</span> URI）</td><td class="n">file:///lmcache-disk/</td></tr>
    <tr><td class="n">LMCACHE_MAX_LOCAL_DISK_SIZE</td><td>磁碟層上限（GB，滿了 LRU 逐出）</td><td class="n">20</td></tr>
    <tr><td class="n">LMCACHE_PRE_CACHING_HASH_ALGORITHM</td><td>chunk 檔名的雜湊，<b>務必固定</b></td><td class="n">sha256</td></tr>
  </table>
  <p class="src">
    上表那組值是一份公開實測的 SSD-only 設定：刻意把 <span class="kbd">LMCACHE_LOCAL_CPU</span> 關掉，
    好讓「從磁碟撈回來」這件事單獨被觀察到。正式服務通常兩層都開。
  </p>
  <p>三個上線前要先想過的地雷：</p>
  <table class="cmp">
    <tr><th>地雷</th><th>怎麼避</th></tr>
    <tr><td><b>雜湊沒固定</b></td><td>chunk 是用內容雜湊當檔名找回來的。演算法一飄，舊 chunk 全部對不上，等於白存——明確釘 <span class="kbd">sha256</span></td></tr>
    <tr><td><b>請求被中途 abort</b></td><td><span class="kbd">stop</span> 參數提早收尾、串流中途斷線，都會走到中止路徑。上線前先壓測這條路徑，別等使用者幫你測</td></tr>
    <tr><td><b>磁碟無限長大</b></td><td>用 <span class="kbd">MAX_LOCAL_DISK_SIZE</span> 給上限，並想好清理策略；快取是高頻寫入，SSD 的 TBW 會被吃掉</td></tr>
  </table>
</section>

<section id="s4">
  <span class="eyebrow">04 · 實測</span>
  <h2>三種情境，一行日誌，三個數字</h2>
  <p>要證明「SSD 真的有救到你」，得設計得讓快取<b>非命中不可</b>。一份公開實測是這樣設計的：
    把 GPU 的 KV pool 壓到只剩約 2.7k tokens（容易觀察逐出），每個情境跑三次取中位數。</p>
  <table class="cmp">
    <tr><th>情境</th><th>做什麼</th><th>意義</th></tr>
    <tr><td class="n">a 冷啟動</td><td>文件第一次出現 → 全量 prefill（同時 LMCache 把 KV 寫進 SSD）</td><td>基準 1.0x</td></tr>
    <tr><td class="n">b GPU 命中</td><td>同一份文件馬上再問一次 → vLLM 自己的 prefix cache 命中</td><td>速度上限</td></tr>
    <tr><td class="n">c SSD 複用</td><td>先灌兩份別的文件把它擠出 GPU pool，再回頭問 → 從 SSD 撈回</td><td>本課重點</td></tr>
  </table>
  <p>
    沒有 LMCache 的話，情境 c 會直接退化成 a——全量重算。那就是磁碟層的全部價值。
    而「真的命中了」不是用感覺判斷的，server 端的日誌會講得很白：
  </p>
  <div class="codeblock">Inference Engine computed tokens: 0, LMCache hit tokens: 1280, need to load: 1280</div>
  <p>
    <span class="kbd">computed tokens: 0</span> ＝ 引擎<b>一個 token 都沒重算</b>；
    <span class="kbd">need to load: 1280</span> ＝ 這 1280 個 token 的 KV 全部是從下層載回來的。
    調參數之後先看這一行，再看碼表。
  </p>
  <p>三個模型跑同一套流程，冷啟動 vs SSD 複用的 TTFT 加速比：</p>
  <table class="cmp">
    <tr><th>模型</th><th>加速比</th><th>為什麼是這個幅度</th></tr>
    <tr><td>Qwen3-0.6B（bf16）</td><td class="n">1.1x</td><td>prefill 太便宜了，重算跟載入一樣快</td></tr>
    <tr><td>Qwen3-1.7B（FP8）</td><td class="n">1.2x</td><td>kernel 很快，計算仍然太便宜</td></tr>
    <tr><td>Qwen3-4B-AWQ（int4）</td><td class="n">2.3x</td><td>反量化讓 prefill 變重、KV 又相對小，分子分母同時往好的方向走</td></tr>
  </table>
  <p class="src">實測（RTX 4090、vLLM + LMCache 0.5.0、2026-07）。</p>
  <p>
    這三個數字最值得記的不是大小，是<b>排序</b>：計算越重越賺。同一個道理往上推——
    4B 級模型配 10k tokens 的前綴，冷 prefill 是<b>秒級</b>的事，
    倍率沒變、但省下的<b>絕對時間</b>整個放大一個數量級。加速比也吃 SSD 的實際頻寬與
    OS page cache（第二次跑常常特別快，因為根本沒碰到碟）。
  </p>
  <p>
    右邊 3️⃣ 用純頻寬算出「上限加速比」，你會發現它比這三個實測數字大得多——
    <b>那個差額就是這一課最該帶走的東西</b>：模型告訴你誰有機會贏，實測告訴你實際贏多少。
  </p>
  <button class="golab" data-nb="3️⃣">到右邊 3️⃣ 看加速比曲線與損益平衡點</button>
</section>

<section id="s5">
  <span class="eyebrow">05 · 判斷</span>
  <h2>先確認你真的需要——多數人不需要</h2>
  <p>
    這一節可能會省下你一筆錢。判斷準則只有一句：
    <b>先看 CPU RAM 是不是已經不夠用；沒到那個門檻，就不需要 SSD 層。</b>
  </p>
  <p>
    把數字擺出來就很清楚。8B 級 GQA 模型每個 token 的 KV 是 128 KB（右邊 1️⃣ 算給你看），於是：
  </p>
  <table class="cmp">
    <tr><th>場景</th><th>KV 需求</th><th>該放哪一層</th></tr>
    <tr><td>單人 32k 上下文（讀論文）</td><td class="n">4 GB</td><td>VRAM 就夠</td></tr>
    <tr><td>10 個人各 8k</td><td class="n">10 GB</td><td>CPU RAM</td></tr>
    <tr><td>單人 128k 上下文（整本書）</td><td class="n">16 GB</td><td>CPU RAM</td></tr>
    <tr><td>單人 1M 上下文</td><td class="n">122 GB</td><td>這才輪到 SSD</td></tr>
  </table>
  <p>
    看出來了嗎——常見的那張「超過可用 VRAM 就需要 SSD」的表，<b>跳過了中間那一層</b>。
    VRAM 和 SSD 之間還有 CPU RAM，而一台 64 GB 記憶體的個人機，
    128k 上下文只用掉它的四分之一。另一份公開實測也是同一個結論：
    14B 級模型即使塞進一整本長篇小說份量的上下文，KV 也<b>不到 20 GB</b>，CPU RAM 根本用不完。
  </p>
  <p>
    <b>SSD 層真正的主場是多人共用的伺服器</b>：大量並發 × 長上下文同時存在，
    把 GPU 和 CPU RAM 一起塞爆，這時候再往下卸載才有意義。
    個人／小模型場景很難觸發到那個門檻。
  </p>
  <p>
    <b>那什麼時候值得開？</b>把兩個條件同時滿足才算：<b>KV 大到 CPU RAM 裝不下</b>，
    而且<b>同一段長前綴會被重複使用</b>。第二個條件常被忽略——每次都是全新的 prompt 時，
    快取層完全無效，每一發都是冷啟動。賺最多的是這三種流量：
  </p>
  <table class="cmp">
    <tr><td>🔁 <b>RAG 的固定知識前綴</b></td><td>同一份文件被反覆檢索、反覆送進來</td></tr>
    <tr><td>🔁 <b>多人共用的長 system prompt</b></td><td>一段幾千 token 的規則，每個人每一發都帶著</td></tr>
    <tr><td>🔁 <b>多輪 agent 對話</b></td><td>歷史越滾越長，而前面那一大段每輪都一樣</td></tr>
  </table>
  <p>
    <b>成本直覺</b>：同樣容量，NVMe SSD 的每 GB 價格比 VRAM 低了兩個數量級，
    功耗差距也是同一個量級（多一顆碟是個位數瓦特，換一張大 VRAM 的卡是幾百瓦）。
    所以「真的需要容量」的時候，SSD 是壓倒性划算的選項——
    但「真的需要」這四個字要先用上面的表確認過，不然買了只會閒置。
  </p>
  <p>
    <b>也別把它當成「反正裝得下就全塞」的許可證。</b>把幾百篇文章整段塞進前綴快取起來，
    雜訊變多反而更容易答錯；精準檢索 top-k 的答案品質通常更好。
    快取層解決的是「同一段前綴重複用的成本」，不是「上下文塞越多越聰明」。
  </p>
  <p>
    最後是<b>定位</b>：這一版的本機 SSD 層是<b>「服務存活期間的擴容」，不是持久化</b>——
    它把 prefix cache 的容量從 GB 級擴到數十 GB，但 server 重啟後別預期它自己認得舊 chunk。
    真的要跨重啟、跨機共享，走遠端後端（Redis / S3 / P2P）。
    還有一個很多人踩的認知落差：<b>這一層只加速 prefill，decode 一點都不會變快</b>——
    長回答慢是記憶體頻寬的問題，快取救不了。
  </p>
  <p class="src">
    decode 那一半怎麼加速？那是下一課的事：讓一個小模型先猜一串 token，大模型一次驗完。
  </p>
  <button class="golab" data-nb="4️⃣">到右邊 4️⃣ 用你自己的數字跑一次判斷器</button>
</section>

<section id="s6">
  <span class="eyebrow">06 · 延伸</span>
  <h2>訓練也能卸載到 SSD：ZeRO-Infinity</h2>
  <p>
    同一個「往下卸載」的想法，在訓練側也有一套：DeepSpeed 的 <b>ZeRO-Infinity</b>。
    訓練時 GPU 上要放的東西比推論多得多——模型參數 ＋ 梯度 ＋ 優化器狀態，
    7B 級模型全參數訓練動輒 100 GB 起跳，單卡 VRAM 完全不夠。
    ZeRO-Infinity 把「這一刻暫時用不到」的狀態卸載到 NVMe，要算的時候才搬回來：
  </p>
  <table class="cmp">
    <tr><th>層</th><th>放什麼</th><th>頻寬量級</th></tr>
    <tr><td><b>GPU VRAM</b>（數十 GB）</td><td>正在計算的參數分片</td><td class="n">~1000 GB/s</td></tr>
    <tr><td><b>CPU RAM</b>（數百 GB）</td><td>優化器狀態、梯度</td><td class="n">~50 GB/s</td></tr>
    <tr><td><b>NVMe SSD</b>（數 TB）</td><td>放不下的全部</td><td class="n">~5–7 GB/s</td></tr>
  </table>
  <p>
    關鍵技巧和 KV 卸載一樣：<b>預先讀取 ＋ 非同步 I/O</b>，把搬運藏在計算後面，讓 GPU 盡量不停等。
    但代價很誠實——<b>會慢 5～20 倍</b>。它是「跑得動 vs 跑不動」的方案，<b>不是加速方案</b>。
    硬體也有條件：必須是 PCIe NVMe（SATA 太慢不可行），而且高頻寫入很吃 SSD 壽命。
  </p>
  <p>
    所以優先順序是固定的：<b>純 GPU → CPU offload → NVMe offload</b>，能停在前面就別往後走。
    而在往後走之前還有一步更划算的：<b>微調先試 LoRA</b>——
    用可調的參數量直接把記憶體需求壓下來，常常整個卸載需求就消失了，
    順便避開全參數微調的災難性遺忘。那是<a href="/lora-basics/">第 8 課</a>的主題。
  </p>
  <p class="src">
    這一節是延伸整理，不是本課的實測——真的要用 ZeRO-Infinity，請以官方文件為準並自己跑過一輪。
  </p>
</section>

<section id="s7">
  <span class="eyebrow">07 · 實戰</span>
  <h2>換你動手</h2>
  <div class="ex">
    <span class="lv">LEVEL 1</span>
    <p>把 1️⃣ 的 KV 型別改成 fp8，看 128k 上下文的需求掉到多少——4️⃣ 的判斷器會不會從「開 CPU 層」翻回「VRAM 就裝得下」？</p>
  </div>
  <div class="ex">
    <span class="lv">LEVEL 2</span>
    <p>算出<b>損益平衡的 prefill 吞吐</b>（頻寬 ÷ 每 token 的 KV）。為什麼這個純頻寬上限幾乎永遠大於 1，實測卻只有 1.1–2.3x？差額跑到哪裡去了？</p>
  </div>
  <div class="ex">
    <span class="lv">LEVEL 3</span>
    <p>換成你自己服務的真實數字（層數與 KV head 數看模型 <span class="kbd">config.json</span>、prefill 吞吐壓一次長 prompt、SSD 頻寬用 <span class="kbd">fio</span> 量），重跑判斷器；再用你量到的加速比回推「你真正吃到了標稱頻寬的幾成」。</p>
  </div>
  <p style="font-size:13.5px;color:var(--ink-soft);margin-top:10px">卡住了？三題在 notebook 最後一格都有折疊解答——先自己做，再打開對照。</p>
  <button class="golab" data-nb="5️⃣">到右邊 5️⃣ 的實驗區開工</button>
</section>

<section id="quiz">
  <span class="eyebrow">08 · 驗收</span>
  <h2>情境測驗</h2>
  <p>離開前試試看：下面的情境都真的會遇到。每題選一個你認為的最佳做法，選了馬上看得到解釋。</p>
  <div data-quiz>

    <div class="quiz-q" data-answer="C">
      <p class="quiz-tag">Q1 <span class="qtype">情境題</span></p>
      <h3>你的服務每週重啟一次做模型更新，重啟後前十分鐘特別慢——熱門的長 system prompt 全部要重新 prefill。你已經開了 <span class="kbd">LMCACHE_LOCAL_DISK</span>，磁碟上也還留著上一輪的 chunk 檔。最合適的做法是？</h3>
      <div class="quiz-opts">
        <button type="button" class="quiz-opt" data-k="A">A. 把 <code>LMCACHE_MAX_LOCAL_DISK_SIZE</code> 調大，讓 chunk 不要被 LRU 清掉</button>
        <button type="button" class="quiz-opt" data-k="B">B. 換一個更快的雜湊演算法，加速重啟後的 chunk 查表</button>
        <button type="button" class="quiz-opt" data-k="C">C. 認清本機 SSD 層是「存活期間擴容」而非持久化：要跨重啟／跨機復用就走遠端後端，或在重啟後主動打幾發熱門前綴把快取暖起來</button>
        <button type="button" class="quiz-opt" data-k="D">D. 重啟前把 chunk 目錄備份，重啟後再複製回原位</button>
      </div>
      <div class="quiz-fb" aria-live="polite"><p>這一版本機磁碟層的定位是「把 prefix cache 的容量從 GB 級擴到數十 GB」，在服務存活期間有效；真的要跨重啟、跨副本共享同一份 KV，是遠端後端（Redis / S3 / P2P）的工作。搞錯定位就會一直去調錯的旋鈕：A 只是讓檔案留在碟上，服務重啟後不會因此就認得它們；B 剛好反了——雜湊要<b>固定</b>成 sha256，chunk 檔名才可重現，換演算法會讓舊 chunk 全部對不上；D 的檔案本來就在原位，問題從來不是檔案在不在。務實的短解是重啟後主動暖機，長解是升級到遠端後端。</p></div>
    </div>

    <div class="quiz-q" data-answer="C">
      <p class="quiz-tag">Q2 <span class="qtype dx">錯誤診斷</span></p>
      <h3>同事說「LMCache 我開好了，但完全沒感覺變快」，並貼出 server 日誌。他的結論是「hit tokens 有數字＝快取沒問題，一定是別的地方慢」。他哪裡看錯了？</h3>
      <div class="codeblock">Inference Engine computed tokens: 0, LMCache hit tokens: 1280, need to load: 1280</div>
      <div class="quiz-opts">
        <button type="button" class="quiz-opt" data-k="A">A. <code>need to load: 1280</code> 表示 1280 個 token 還「等著被載入」，其實沒載成功</button>
        <button type="button" class="quiz-opt" data-k="B">B. 雜湊沒固定，所以每次都重存一份新的 chunk，命中數是假的</button>
        <button type="button" class="quiz-opt" data-k="C">C. 日誌是對的、命中也是真的（<code>computed tokens: 0</code> ＝一個 token 都沒重算）；沒感覺變快是因為他的模型 prefill 太便宜，載回和重算差不多快</button>
        <button type="button" class="quiz-opt" data-k="D">D. <code>LMCACHE_CHUNK_SIZE</code> 設太小，1280 個 token 被切得太碎，查表成本吃掉了收益</button>
      </div>
      <div class="quiz-fb" aria-live="polite"><p>這行日誌是<b>完美命中</b>的樣子：<code>computed tokens: 0</code> 代表引擎一個 token 都沒重算，1280 個 token 的 KV 全部從下層載回。他讀對了日誌，錯在期待——加速比 ＝ 該層頻寬 ÷（prefill 吞吐 × 每 token 的 KV），模型小、計算便宜的時候這個比值本來就接近 1（實測 0.6B bf16 只有 1.1x，4B-AWQ 才有 2.3x）。要有感，得是計算更重的模型或更長的前綴。A 誤讀了欄位語意，<code>need to load</code> 是「需要從下層載回的量」不是待辦；B 若成立，<code>hit tokens</code> 會是 0 而不是 1280；D 是憑空猜參數，日誌裡沒有任何支持它的訊號。</p></div>
    </div>

    <div class="quiz-q" data-answer="B">
      <p class="quiz-tag">Q3 <span class="qtype dx">錯誤診斷</span></p>
      <h3>同事用判斷器算完自己的機器，得到這段輸出，結論是「16 GB 超過我的 10 GB 可用 VRAM，所以要買 SSD 開 <span class="kbd">LMCACHE_LOCAL_DISK</span>」。他的診斷錯在哪？</h3>
      <div class="codeblock">每 token KV = 128 KB
131072 tokens x 1 人 → 16.00 GB → 放在 CPU RAM
損益平衡 prefill 吞吐 = 49,152 tokens/s</div>
      <div class="quiz-opts">
        <button type="button" class="quiz-opt" data-k="A">A. 沒錯，16 GB 確實超過可用 VRAM，SSD 層是唯一解</button>
        <button type="button" class="quiz-opt" data-k="B">B. 輸出已經說了要放在 CPU RAM——VRAM 和 SSD 之間還有一層，64 GB 的 RAM 裝 16 GB 綽綽有餘，而且比 SSD 快一個數量級</button>
        <button type="button" class="quiz-opt" data-k="C">C. 這個數字算錯了，128k 上下文的 KV 不可能到 16 GB</button>
        <button type="button" class="quiz-opt" data-k="D">D. 把 <code>LMCACHE_CHUNK_SIZE</code> 調大就能把 16 GB 壓下來，不用加任何硬體</button>
      </div>
      <div class="quiz-fb" aria-live="polite"><p>這是本課最容易犯的錯：把「超過 VRAM」直接等於「需要 SSD」，跳過了中間的 CPU RAM 層。判斷準則是<b>先確認 CPU RAM 是不是真的不夠用</b>——128k × 1 人 ＝ 16 GB，在一台 64 GB 的機器上連四分之一都不到，開 <code>LMCACHE_LOCAL_CPU</code> 就結束了，還比 SSD 快一個數量級。A 就是那個跳過中間層的錯誤結論；C 的算術沒問題（2 × 32 層 × 8 個 KV head × 128 維 × 2 bytes ＝ 128 KB／token，乘上 131072 個 token 正好是 16 GB）；D 搞混了對象——chunk size 只是快取的對齊單位，改它不會讓 KV 本身變小，真要壓小 KV 得靠 KV 量化或縮短上下文。</p></div>
    </div>

    <div class="quiz-q" data-answer="C">
      <p class="quiz-tag">Q4 <span class="qtype">情境題</span></p>
      <h3>你的 RAG 客服目前把檢索到的 top-5 段落貼進提示詞，效果不錯。你想：「反正 SSD 層裝得下，乾脆把整個知識庫幾百篇文章都做成固定前綴快取起來，一次命中永遠命中。」最好的判斷是？</h3>
      <div class="quiz-opts">
        <button type="button" class="quiz-opt" data-k="A">A. 可行，固定前綴越長，每次命中省下的絕對時間就越多</button>
        <button type="button" class="quiz-opt" data-k="B">B. 可行，但要先把 <code>LMCACHE_MAX_LOCAL_DISK_SIZE</code> 調大到裝得下</button>
        <button type="button" class="quiz-opt" data-k="C">C. 不要——塞進大量無關文章會讓答案品質變差，精準檢索 top-k 通常答得更準；快取解決的是重複前綴的成本，不是「上下文塞越多越聰明」</button>
        <button type="button" class="quiz-opt" data-k="D">D. 不要——SSD 頻寬太慢，幾百篇文章的 KV 載回來會比重算還久</button>
      </div>
      <div class="quiz-fb" aria-live="polite"><p>快取層優化的是<b>成本</b>，不是<b>品質</b>；這兩件事被混在一起就會做出「反正裝得下就全塞」的決定。實務上一直塞文章不是好做法，雜訊變多反而更容易答錯——檢索 top-k 的品質通常更好。A 講的省時是真的，但它只回答了成本、沒回答品質，而品質才是這個決定會壞掉的地方；B 同樣只處理容量；D 的方向反了——載回時間 ＝ KV ÷ 頻寬，通常仍遠快於重算（本課的模型算出來的上限就遠大於 1x），問題不在載得慢。</p></div>
    </div>

    <div class="quiz-score" data-score></div>
  </div>
</section>

<div class="endnav">
  <a href="/speculative-decoding/">
    <span class="tag">下一課</span>
    <b>投機解碼：先猜後驗 →</b>
  </a>
  <a href="/local-llm/">
    <span class="tag">主題</span>
    <b>‹ 回「個人地端大語言模型實作」課程列表</b>
  </a>
</div>
"""

SCRIPT = r"""
/* ═══ hero 互動：四層儲存（點一層看角色與「拿回 10k 前綴」要多久）═══
   時間＝ KV 大小 ÷ 該層頻寬，用的是右邊實驗場同一組數字：
   8B 級 GQA、fp16 → 每 token 128 KB；10,000 tokens ≈ 1.22 GB。 */
(function () {
  const TIERS = [
    { id: "gpu", c: "#4C72B0", nm: "GPU KV pool", sub: "vLLM 內建 prefix cache", bw: "~1–2 TB/s",
      cap: "GB 級——跟模型權重搶同一塊 VRAM",
      role: "最快，也最小。多使用者、長上下文彼此擠壓，LRU 隨時把你的前綴逐出去。",
      t: "0 ms（本來就在 GPU 上，命中直接用）" },
    { id: "cpu", c: "#DD8452", nm: "CPU RAM", sub: "LMCACHE_LOCAL_CPU", bw: "~50 GB/s",
      cap: "數十～數百 GB",
      role: "從 GPU 逐出的 KV 先收在這裡。個人／單機場景多半停在這一站——裝得下就沒有理由再往下丟。",
      t: "約 24 ms" },
    { id: "ssd", c: "#55A868", nm: "本機 SSD", sub: "LMCACHE_LOCAL_DISK", bw: "~6 GB/s",
      cap: "數百 GB ～ TB 級",
      role: "本課主角：把 prefix cache 的容量從 GB 級擴到數十 GB 以上。vLLM 原生沒有這一層。",
      t: "約 200 ms" },
    { id: "rmt", c: "#8172B2", nm: "遠端後端", sub: "Redis / S3 / P2P", bw: "看網路",
      cap: "幾乎沒有上限",
      role: "換到的是跨機共享與真正的持久化——多副本、跨重啟都認得同一份 KV。",
      t: "看網路，通常再慢一個數量級" },
  ];
  const stack = document.getElementById("kv-stack");
  const detail = document.getElementById("kv-detail");
  const base = document.getElementById("kv-base");
  if (!stack) return;
  let cur = 2;
  TIERS.forEach((t, i) => {
    const b = document.createElement("button");
    b.type = "button";
    b.className = "tier";
    b.style.setProperty("--tc", t.c);
    b.innerHTML = `<span class="bar"></span><span><span class="nm">${t.nm}</span><br><span class="sub">${t.sub}</span></span><span class="bw">${t.bw}</span>`;
    b.addEventListener("click", () => { cur = i; render(); });
    stack.appendChild(b);
  });
  function render() {
    const t = TIERS[cur];
    stack.querySelectorAll(".tier").forEach((el, i) => el.classList.toggle("on", i === cur));
    detail.style.borderColor = t.c;
    detail.innerHTML =
      `<div class="lbl" style="color:${t.c}">${t.nm} · 容量 ${t.cap}</div>` +
      `<div>${t.role}</div>` +
      `<div style="margin-top:8px">拿回 10k token 的前綴：<span class="t" style="color:${t.c}">${t.t}</span></div>`;
  }
  base.innerHTML =
    "對照組——<b>不用快取，全部重算</b>：時間 ＝ 前綴長度 ÷ prefill 吞吐。" +
    "以每秒 2,000 個 token 的 prefill 算，同樣這段 10k 前綴要 <b>5 秒</b>。" +
    "整堂課就在比這兩個數字：搬運，還是重算？";
  render();
})();
"""
