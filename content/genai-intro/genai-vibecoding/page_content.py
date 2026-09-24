"""課程頁內容區（純常數）。改完跑：python3 .claude/skills/make-lesson/scripts/page-fill.py content/genai-intro/genai-vibecoding
build.sh 不會部署這個檔；它是 index.html 內容區的正本。
hero 的 `const HERO = ...;` 那一行由 _spikes/spike_genai_vibecoding_pack.py 注入（實測紀錄，不要手改）。"""

TITLE = "Vibe Coding 進階：讓測試當 AI 的眼睛"
DESCRIPTION = "同一個 2B 模型、同一份沒過的第一版：只說「不對」、貼錯誤訊息、開新對話重抽、寫一句診斷，誰救得回來？12 題 × 8 次重跑的實測，加上測試寫太少時的「假綠燈」、幻覺套件與寫死金鑰——vibe coding 能不能成事，看的是回饋迴圈。"

STYLE = r"""
  /* 語義色：紫＝重抽、灰＝只說不對、綠＝貼錯誤原文、紅＝弱測試／代價、藍＝人的診斷 */
  :root { --c1: #4C72B0; --c2: #DD8452; --c3: #55A868; --c4: #8172B2; --cut: #C44E52; --c5: #9AA7AE; }

  .tldr { border-left: 4px solid var(--tc, var(--c1)); background: var(--chip-bg);
    border-radius: 0 10px 10px 0; padding: 10px 14px; margin: 12px 0 16px;
    font-size: 14.5px; line-height: 1.7; }
  .tldr b { color: var(--tc, var(--c1)); }

  /* hero：同一份第一版、五種下一步的重播機 */
  #loop-demo .need { font-size: 13.5px; line-height: 1.7; margin-bottom: 10px; }
  #loop-demo .need code { font-size: 12.5px; }
  #loop-demo .picks { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 12px; }
  #loop-demo .pick { font: inherit; font-size: 13px; font-weight: 700; color: var(--ink);
    background: var(--panel); border: 2px solid var(--grid); border-radius: 999px;
    padding: 6px 12px; cursor: pointer; transition: border-color .15s, background .15s; }
  #loop-demo .pick:hover { border-color: var(--ink-soft); }
  #loop-demo .pick.on { border-color: var(--tc); background: var(--chip-bg); color: var(--ink); box-shadow: inset 0 -3px 0 var(--tc); }
  #loop-demo .stage { border: 2px solid var(--ink); border-radius: 12px; padding: 10px 12px; min-height: 170px; }
  #loop-demo .ver { border: 2px solid var(--grid); border-radius: 10px; padding: 8px 10px; margin: 8px 0;
    animation: fadeup .25s ease; }
  #loop-demo .ver.ok { border-color: var(--c3); }
  #loop-demo .ver .hd { font-size: 12.5px; font-weight: 800; display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }
  #loop-demo .dots { display: inline-flex; flex-wrap: wrap; gap: 3px; align-items: center; }
  #loop-demo .dot { width: 12px; height: 12px; border-radius: 50%; display: inline-block; box-sizing: border-box; }
  #loop-demo .dot.b.y { background: var(--c3); } #loop-demo .dot.b.n { background: var(--cut); }
  #loop-demo .dot.e.y { border: 2.5px solid var(--c3); } #loop-demo .dot.e.n { border: 2.5px solid var(--cut); }
  #loop-demo .dot.e.q { border: 2.5px dashed var(--c5); }
  #loop-demo .gap { width: 6px; display: inline-block; }
  #loop-demo pre { font-family: var(--mono); font-size: 12px; line-height: 1.5; white-space: pre-wrap;
    word-break: break-word; margin: 6px 0 0; padding: 7px 9px; background: var(--chip-bg); border-radius: 8px; }
  #loop-demo pre.fb { border-left: 3px solid var(--c2); border-radius: 0 8px 8px 0; white-space: pre; word-break: normal;
    overflow-x: auto; max-width: 100%; font-size: 11.5px; }
  #loop-demo .lbl { font-size: 11.5px; color: var(--ink-soft); margin-top: 6px; }
  #loop-demo .same { font-size: 12.5px; font-weight: 800; color: var(--cut); margin-top: 6px; }
  #loop-demo .verdict { font-size: 13.5px; line-height: 1.7; border-left: 3px solid var(--tc); padding: 4px 10px; margin-top: 8px; }
  #loop-demo .ctrl { display: flex; flex-wrap: wrap; align-items: center; gap: 10px; margin-top: 10px; }
  #loop-demo .step-btn { font: inherit; font-size: 14px; font-weight: 800; color: #fff;
    background: var(--ink); border: 2px solid var(--ink); border-radius: 10px; padding: 7px 18px; cursor: pointer; }
  #loop-demo .step-btn:disabled { opacity: .4; cursor: default; }
  #loop-demo .reset-btn { font: inherit; font-size: 13px; font-weight: 700; color: var(--ink);
    background: var(--panel); border: 2px solid var(--grid); border-radius: 10px; padding: 6px 14px; cursor: pointer; }
  #loop-demo .pos { font-family: var(--mono); font-size: 12px; color: var(--ink-soft); }
  #loop-demo .legend { font-size: 12px; color: var(--ink-soft); margin-top: 8px; line-height: 1.7; }
  #loop-demo .src { font-size: 12px; color: var(--ink-soft); margin-top: 6px; }
  @keyframes fadeup { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: none; } }

  .tw { overflow-x: auto; }
  table.cmp { width: 100%; border-collapse: collapse; font-size: 13.5px; margin: 14px 0; }
  table.cmp th, table.cmp td { border-bottom: 1px solid var(--grid); padding: 8px 10px; text-align: left; vertical-align: top; }
  table.cmp th { font-size: 12px; letter-spacing: .04em; color: var(--ink-soft); }
  table.cmp td.n { font-family: var(--mono); font-weight: 800; white-space: nowrap; }
  .kbd { font-family: var(--mono); background: var(--chip-bg); padding: 1px 6px; border-radius: 5px; font-size: 13px; }
  .src { font-size: 12.5px; color: var(--ink-soft); margin-top: -6px; }
  .take { border: 2px dashed var(--c1); border-radius: 12px; padding: 12px 14px; margin: 16px 0; font-size: 14px; line-height: 1.75; }
  .take b.hd { color: var(--c1); }

  table.cheat { width: 100%; border-collapse: collapse; font-size: 14px; margin: 14px 0; }
  table.cheat td { border-bottom: 1px solid var(--grid); padding: 10px 12px; vertical-align: top; line-height: 1.7; }
  table.cheat td.t { font-weight: 800; width: 10em; }
"""

WRAP = r'''
<section id="hero">
  <span class="eyebrow">GENAI 進階補充 · F · VIBE CODING</span>
  <h1>Vibe Coding 進階：<br>讓測試當 AI 的眼睛</h1>
  <p style="margin-top:18px">
    <a href="/genai-devstyle/">主線第 6 課</a>說 vibe coding 是「講人話讓 AI 寫、人只做測試判斷」。
    進階問題是：<b>第一版沒過的時候，下一步該怎麼走？</b>
    下面是一次真實紀錄——同一個模型、同一份沒過的第一版，五種下一步各自走下去。
    每個圓點是一個測試案例（實心＝基本測試、空心＝需求沒講的邊界測試），選一種下一步、按「下一步」：
  </p>

  <div class="hero-demo" id="loop-demo">
    <div class="need" id="loop-need"></div>
    <div class="picks" id="loop-picks"></div>
    <div class="stage" id="loop-stage"></div>
    <div class="ctrl">
      <button type="button" class="step-btn" id="loop-next">下一步 ▸</button>
      <button type="button" class="reset-btn" id="loop-reset">重播</button>
      <span class="pos" id="loop-pos"></span>
    </div>
    <div class="legend">
      <span class="dots"><span class="dot b y"></span><span class="dot b n"></span></span> 基本測試 過／沒過
      <span class="dots"><span class="dot e y"></span><span class="dot e n"></span></span> 邊界測試 過／沒過
      <span class="dots"><span class="dot e q"></span></span> AI 看不到的測試
    </div>
    <div class="src" id="loop-src"></div>
  </div>

  <p class="note">
    實驗場首次載入約需 30–60 秒，正好夠你讀完第 1 節。裡面有 12 題 × 8 次重跑的完整紀錄，
    每個實驗都用下拉選單與滑桿操作；第 3️⃣ 節會把 AI 寫過的程式在你的瀏覽器裡重跑一遍。
  </p>
</section>

<section id="s1">
  <span class="eyebrow">01 · 回饋迴圈</span>
  <h2>把「人驗收」升級成「迴圈自己驗收」</h2>
  <div class="tldr" style="--tc:var(--c3)">
    <b>一句話重點</b>：vibe coding 能不能成事，看的是<b>回饋迴圈</b>——AI 寫完 → 自動跑檢查 → 結果回到 AI。
    你的角色從「逐行看程式」變成<b>設計檢查</b>：測試寫到哪，AI 就看得到哪。
  </div>
  <p>
    主線那一課的 vibe 迴圈裡，<b>你</b>是唯一的檢查：跑跑看、看順不順眼、再講一次。
    Anthropic 的 Claude Code 官方最佳實務（2026-09 查閱）第一條就是把這件事交出去——
    <b>「給 Claude 一個它自己能跑的檢查：測試、build、截圖比對」</b>，理由很直白：
    沒有能跑的檢查，AI 唯一的停止訊號就是「看起來做完了」，而你就變成了那個迴圈，
    每個錯都要等你發現。
  </p>
  <p>迴圈本身短得驚人。本課實驗用的就是這個骨架（參考程式，不在課內執行；完整可跑版見第 5 節的連結）：</p>
  <div class="codeblock">code = ask_llm(need)                       # 一句話需求 → 第一版
for attempt in range(3):
    result = run_pytest(code, sandbox=True)  # 暫存目錄、timeout、不連網
    if result.all_passed:
        break
    code = ask_llm(need, feedback=result.output)   # 把失敗訊息餵回去
print(result.summary)                        # 人看的是這一行，不是每一行程式</div>
  <p>
    問題在 <span class="kbd">feedback=</span> 那一格要放什麼。實驗設計：<b>需求只給一句話</b>
    （「寫一個 <span class="kbd">round_half_up(x)</span>：把 x 四捨五入成整數」），
    細節——負數怎麼進位、錯誤輸入要不要 raise、輸出格式——<b>只寫在測試裡</b>，
    就像真實世界裡那些細節只存在你腦中。12 道小題、每題重跑 8 次，第一版沒全過時比較五種下一步。
    結果（qwen3.5-2b，2026-09 實測，8 次重跑的範圍）：
  </p>
  <div class="tw"><table class="cmp">
    <tr><th>第一版沒過之後</th><th>救回幾個（共 80 個）</th><th>每輪 12 題最後全過</th></tr>
    <tr><td style="color:var(--c5);font-weight:700">只說「不對，再修」</td><td class="n">6</td><td class="n">1–5 題</td></tr>
    <tr><td style="color:var(--c3);font-weight:700">貼回 pytest 錯誤原文</td><td class="n">6</td><td class="n">2–4 題</td></tr>
    <tr><td style="color:var(--c4);font-weight:700">開新對話重抽（測試當裁判）</td><td class="n">10</td><td class="n">2–5 題</td></tr>
    <tr><td style="color:var(--c1);font-weight:700">錯誤原文＋你的一句診斷</td><td class="n">21</td><td class="n">1–7 題</td></tr>
    <tr><td style="color:var(--cut);font-weight:700">貼錯誤，但只有基本測試</td><td class="n">1</td><td class="n">1–3 題</td></tr>
  </table></div>
  <p class="src">第一版（五種條件共用同一份）：96 個題次（12 題 × 8 次）只有 16 個全過，剩下 80 個交給上表的五種下一步（每種最多再試 3 次）。你自己跑，數字會不同——看方向。</p>
  <button class="golab" data-nb="1️⃣">到實驗場 1️⃣ 看五種下一步的成績曲線</button>
</section>

<section id="s2">
  <span class="eyebrow">02 · 看得見 ≠ 看得懂</span>
  <h2>錯誤訊息只對讀得懂的模型有用</h2>
  <div class="tldr" style="--tc:var(--c4)">
    <b>一句話重點</b>：小模型在同一段對話裡，很常把<b>上一版原封不動再交一次</b>——它看得見錯誤，卻沒拿它去改。
    卡住時別只說「不對」：<b>寫一句診斷</b>、或<b>開新對話重來</b>，讓測試當裁判挑出過關的那一版。
  </div>
  <p>
    數字很難看：80 個沒過的第一版，只說「不對，再修」救回 6 個；貼回完整的 pytest 錯誤原文——也只救回 6 個。
    原因在實驗場 1️⃣ 表格的最後一欄：同一段對話裡，它交回的新版有 <b>72%</b>（只說不對）和 <b>67%</b>（貼錯誤原文）
    跟上一版<b>一字不差</b>。<span class="kbd">round_half_up</span> 最明顯：8 次重跑的第一版全是
    <span class="kbd">return int(x + 0.5)</span>（負數會錯），錯誤訊息清楚寫著 <span class="kbd">assert -2 == -3</span>，
    它 18 次修正裡有 15 次照交不誤。
  </p>
  <p>
    這不是 2B 模型獨有的怪癖。Olausson 等人在 ICLR 2024 的論文
    <i>Is Self-Repair a Silver Bullet for Code Generation?</i> 測了 Code Llama、GPT-3.5、GPT-4：
    把修復的成本算進去之後，自我修復的增益「往往不大、因題而異，有時根本沒有」；
    瓶頸在<b>回饋的品質</b>——換成更強的模型、或由人來寫回饋，提升才明顯。
    我們的迷你實驗是同一個故事的縮小版：同樣那 80 個沒過的第一版，在錯誤原文後面加<b>一句人看完測試會說的話</b>
    （例如「負數要遠離 0 進位，所以不能用 int(x + 0.5)」——只講哪裡錯，不給程式碼），救回 <b>21</b> 個，
    是只貼錯誤原文的 3 倍多；逐題配對看，診斷救回而錯誤原文沒救回的有 17 個，反過來只有 2 個。
    另一條不用模型「讀懂」的路是<b>開新對話重抽</b>，讓測試挑出過關的那一版：救回 10 個，
    但它救不了<b>系統性的誤解</b>——<span class="kbd">round_half_up</span> 重抽 24 次，抽到的全是同一行
    <span class="kbd">int(x + 0.5)</span>。
  </p>
  <p>
    所以「貼錯誤訊息」這條最佳實務要讀完整：它的威力取決於<b>模型讀不讀得懂錯誤</b>
    （本課的 2B 小模型多半讀不懂；論文裡換成更強的模型來寫回饋，提升就明顯），再加上<b>你補的那一句判斷</b>。
    官方最佳實務的另一句也在同一條線上：同一件事糾正兩次還不行，對話裡已經塞滿失敗的嘗試——
    <span class="kbd">/clear</span> 開新對話，把學到的東西寫進更好的第一句提示。
  </p>
  <button class="golab" data-nb="2️⃣">到實驗場 2️⃣ 逐版看 diff：它到底改了什麼</button>
</section>

<section id="s3">
  <span class="eyebrow">03 · 假綠燈</span>
  <h2>測試寫到哪，AI 就看到哪</h2>
  <div class="tldr" style="--tc:var(--cut)">
    <b>一句話重點</b>：AI 的「完成」＝<b>它看得到的檢查全綠</b>。你沒寫進測試的要求，
    對 AI 來說不存在——迴圈會很有效率地停在一個錯的答案上。
  </div>
  <p>
    第五種下一步「貼錯誤，但只有基本測試」模擬一個常見狀況：測試只寫了快樂路徑。
    結果：96 個題次裡有 <b>22 個</b>在「基本測試全綠」時停手、完整測試卻沒過——其中 20 個是<b>第一版就停了</b>，
    AI 根本沒機會看到自己錯在哪。<span class="kbd">round_half_up</span> 8 次全中：<span class="kbd">int(x + 0.5)</span>
    在正數上完美、負數一律錯，而基本測試剛好只有正數。
  </p>
  <p>
    這個網站本身就踩過同一個坑。本站每一課上線前都要過自動冒煙測試（載入、無錯誤、圖表數量、手機版面），
    是 AI 協作開發的「眼睛」；但有一次課程頁的選項按鈕變成<b>白底白字</b>——頁面載入正常、沒有任何錯誤，
    冒煙測試全綠，只有截圖預覽看得出來。所以現在建課流程多了一條：上線前截圖、<b>自己看圖</b>。
    <b>眼睛只看得到你教它看的東西。</b>
  </p>
  <button class="golab" data-nb="3️⃣">到實驗場 3️⃣ 當測試設計師：一個一個加邊界測試，看破口怎麼補上</button>
</section>

<section id="s4">
  <span class="eyebrow">04 · 測試抓不到的地雷</span>
  <h2>不存在的套件、寫死的金鑰</h2>
  <div class="tldr" style="--tc:var(--c2)">
    <b>一句話重點</b>：測試只驗「答得對不對」，驗不到「裝了什麼」與「把什麼寫進程式碼」。
    AI 推薦的套件<b>先查 PyPI 再裝</b>；金鑰<b>一律從環境變數讀</b>。
  </div>
  <p>
    <b>套件幻覺</b>：請同一個模型為 15 個任務各推薦 3 個 pip 套件、每題問 3 次，
    再把每個名字真的拿去查 PyPI。135 次推薦裡有 <b>14 次</b>是 PyPI 上根本不存在的名字（不重複的 9 個，例如中文斷詞推薦的
    <span class="kbd">thefp</span>、<span class="kbd">chinese-jieba</span>）。最有代表性的是
    <span class="kbd">dateutil</span>：那是 import 時的名字，pip 上的套件叫 <span class="kbd">python-dateutil</span>——
    照抄 <span class="kbd">pip install dateutil</span> 只會裝失敗。還有一種更安靜的錯：冷門任務它常推薦<b>存在但無關</b>的套件——
    「驗證台灣身分證字號」推薦了 pytz（時區）、openpyxl（Excel）、lxml（XML），名字都查得到，沒有一個做得到這件事。
  </p>
  <p>
    不存在的名字為什麼危險？攻擊者可以<b>搶先把它註冊成惡意套件</b>，等照著 AI 建議
    <span class="kbd">pip install</span> 的人上門——這叫 <b>slopsquatting</b>。
    USENIX Security 2025 的研究（Spracklen 等人）讓 16 個模型產生 57.6 萬份程式碼，裡面引用的 223 萬個套件名有
    <b>19.7%</b> 不存在（不重複的 20.5 萬個）；同一提示重跑 10 次，43% 的幻覺名字每次都出現——可預測，所以可以被搶註。
    2026 年對新一代模型的重測（Churilov，arXiv 2605.17062）幻覺率降到 4.6%–6.1%，
    但仍找到 127 個五個模型<b>都會</b>編出來的相同名字。
  </p>
  <p>
    <b>寫死金鑰</b>：請它寫「呼叫 OpenAI API 摘要文字」的函式 10 次。3 次把金鑰寫成程式碼裡的字串（<span class="kbd">api_key="YOUR_API_KEY_HERE"</span>，等你把真的 key 貼進去），
    5 次從環境變數讀，2 次交給 SDK 預設。另外 10 份裡有 5 份用了 openai 套件 1.0 版就移除的
    <span class="kbd">openai.ChatCompletion.create</span>，在今天的 SDK（3.19.2 實測）上一呼叫就丟 <span class="kbd">APIRemovedInV1</span>。
    寫死的字串一旦 commit 就進了 git 歷史——下一版刪掉，舊版還在。
  </p>
  <div class="tw"><table class="cmp">
    <tr><th>地雷</th><th>vibe coding 時的最小防線</th></tr>
    <tr><td><b>幻覺／搶註套件</b></td><td>裝之前開 PyPI 頁面看：專案連結、發版歷史、下載量；用 lock 檔（<span class="kbd">uv.lock</span>）鎖版本；AI 給的名字查不到，就回頭問它「官方文件在哪」，別去猜相近的名字</td></tr>
    <tr><td><b>寫死金鑰</b></td><td>金鑰放 <span class="kbd">.env</span>（並列入 <span class="kbd">.gitignore</span>）、程式用 <span class="kbd">os.environ</span> 讀；把這條寫進 CLAUDE.md／AGENTS.md；commit 前跑密鑰掃描</td></tr>
  </table></div>
  <button class="golab" data-nb="4️⃣">到實驗場 4️⃣ 看模型推薦了哪些「不存在」的套件</button>
</section>

<section id="s5">
  <span class="eyebrow">05 · 2026 的工作流</span>
  <h2>把眼睛裝進流程：從提示技巧變成基礎設施</h2>
  <div class="tldr" style="--tc:var(--c1)">
    <b>一句話重點</b>：一次性的提示技巧會忘，<b>寫進流程的檢查不會</b>——
    規劃、規則檔、hook、平行嘗試、獨立審查，每一個都是在替 AI 裝眼睛。
  </div>
  <p>把前面的實驗結論，對照到 2026 年主流 AI coding 工具的實務（以 Claude Code 官方文件為準，2026-09 查閱）：</p>
  <div class="tw"><table class="cmp">
    <tr><th>實務</th><th>它在迴圈裡的角色</th></tr>
    <tr><td><b>Plan mode</b>：先探索、再規劃、才動手（<span class="kbd">Shift+Tab</span> 切換）</td>
        <td>動手前先把「做完長什麼樣」講清楚。官方建議：一句話能描述的小改動就直接做，跨檔案、不熟的改動才先規劃</td></tr>
    <tr><td><b>CLAUDE.md／AGENTS.md</b></td>
        <td>把「每次都要重講的規則」固定下來（主線第 6 課教過）。AGENTS.md 是跨工具的開放格式，現由 Linux Foundation 旗下 Agentic AI Foundation 維護，Claude Code 也讀得到</td></tr>
    <tr><td><b>Hooks</b>：例如每次改檔後自動跑測試、Stop hook 在測試沒過時擋住「收工」</td>
        <td>規則檔是「建議」，hook 是<b>保證</b>——把「跑測試」從你記得提醒變成一定會發生</td></tr>
    <tr><td><b>平行嘗試</b>：多個 worktree 各跑一個 session</td>
        <td>本課「開新對話重抽」的工業版：幾份獨立嘗試，<b>讓測試挑出過關的那一份</b></td></tr>
    <tr><td><b>獨立審查</b>：開一個乾淨 context 的 subagent 只看 diff 挑錯</td>
        <td>寫程式的不該是批改的人——跟第 3 節的「假綠燈」同一個道理</td></tr>
    <tr><td><b>糾正兩次就重來</b>：<span class="kbd">/clear</span> 後寫更好的第一句</td>
        <td>第 2 節的數據版：同一段對話裡越改越原地打轉</td></tr>
    <tr><td><b>小步提交、人看 diff</b></td>
        <td>每一步都小到看得懂，錯了才退得回去（實驗場 2️⃣ 練的就是讀 diff）</td></tr>
  </table></div>
  <p>
    <b>本站就是這樣做出來的</b>：這個網站的 git 歷史（2026-08-06 到 2026-09-24）共 43 個 commit，
    其中 39 個由 Claude 共同署名。每一課都要先過「程式在本機完整跑一次＋瀏覽器冒煙＋手機版面」
    三道自動檢查才上線，規則寫在 repo 根目錄的 CLAUDE.md 與建課流程文件裡——包括你正在讀的這一課。
  </p>
  <div class="take">
    <b class="hd">帶回家自己跑（免費）</b>：本課實驗的完整腳本是公開的——
    <a href="https://github.com/skmygo/agentclass/blob/main/content/genai-intro/_spikes/spike_genai_vibecoding.py" target="_blank" rel="noopener">spike_genai_vibecoding.py</a>
    （12 題、四種下一步、沙盒跑 pytest；第五種「一句診斷」是同目錄的 <code>spike_genai_vibecoding_hint.py</code>，下載時放同一個資料夾）。用本機免費的 Ollama 跑同尺寸模型：
    <div class="codeblock">ollama pull qwen3.5:2b
LLM_URL=http://localhost:11434/v1 LLM_MODEL=qwen3.5:2b RUNS=2 \
  uv run --script spike_genai_vibecoding.py</div>
    誠實說明：本課的數字是在 vLLM 上跑 qwen3.5-2b 錄的；Ollama 這條路徑本課<b>沒有實跑驗證</b>，
    指令照 Ollama 的 OpenAI 相容端點寫，你跑出的數字也一定跟本課不同。
    想學怎麼寫 pytest 測試本身，看 <a href="/ml-testing/">ML 測試那一課</a>。
  </div>
</section>

<section id="s6">
  <span class="eyebrow">06 · 速查</span>
  <h2>本課名詞速查卡</h2>
  <table class="cheat">
    <tr><td class="t" style="color:var(--c3)">回饋迴圈</td>
        <td>AI 寫 → 自動檢查 → 結果回到 AI。vibe coding 能不能成事的關鍵，人從「驗收每一行」變成「設計檢查」。</td></tr>
    <tr><td class="t" style="color:var(--c4)">Self-repair</td>
        <td>模型讀錯誤訊息修自己的程式。增益受限於它<b>讀不讀得懂回饋</b>；小模型在同一段對話裡常原樣重交。</td></tr>
    <tr><td class="t" style="color:var(--c4)">重抽＋測試當裁判</td>
        <td>開新對話獨立生成多份，讓測試挑過關的——平行 worktree 的原理。不需要模型讀懂錯誤。</td></tr>
    <tr><td class="t" style="color:var(--cut)">假綠燈</td>
        <td>測試只蓋快樂路徑，迴圈停在「看得到的測試全綠」的錯答案上。<b>測試寫到哪，AI 看到哪。</b></td></tr>
    <tr><td class="t" style="color:var(--c2)">Slopsquatting</td>
        <td>攻擊者搶註 AI 常幻覺出的套件名。裝之前先查 PyPI、用 lock 檔。</td></tr>
    <tr><td class="t" style="color:var(--c1)">Hook</td>
        <td>在固定時機自動執行的檢查（改檔後跑測試、收工前擋紅燈）——把「記得提醒」變成「一定發生」。</td></tr>
  </table>
</section>

<section id="s7">
  <span class="eyebrow">07 · 實戰</span>
  <h2>換你動手</h2>
  <div class="ex">
    <span class="lv">LEVEL 1</span>
    <p>在實驗場 1️⃣ 的表格比較「只說不對」「貼回錯誤原文」「錯誤原文＋一句診斷」「開新對話重抽」的<b>一字不差</b>比例，排出順序並說出原因。
       再到 2️⃣ 選 <span class="kbd">round_half_up</span>、第 5 次重跑，切換「只說不對」與「貼回 pytest 錯誤原文」——同一份第一版，為什麼一個原地打轉、一個改對了？換幾次重跑看看，這種幸運常見嗎？</p>
  </div>
  <div class="ex">
    <span class="lv">LEVEL 2</span>
    <p>在 3️⃣ 選 <span class="kbd">format_bytes</span>，只留基本測試，記下「放行但錯」有幾份；
       接著<b>一次只加一個</b>邊界案例，找出哪一個案例一口氣擋下最多錯誤版本。換 <span class="kbd">split_bill</span> 再做一次。</p>
  </div>
  <div class="ex">
    <span class="lv">LEVEL 3</span>
    <p>在 5️⃣ 把每種策略從 1 次拉到 4 次，看「每多花一個 token 換到幾題」。
       寫下你會怎麼設計自己的 vibe coding 流程：第一版沒過時先做什麼、第幾次就該換招、哪一步一定要人來？</p>
  </div>
  <p style="font-size:13.5px;color:var(--ink-soft);margin-top:10px">卡住了？三題在實驗場最後一格都有折疊解答——先自己做，再打開對照。</p>
  <button class="golab" data-nb="5️⃣">到實驗場 5️⃣ 的實驗區開工</button>
</section>

<section id="quiz">
  <span class="eyebrow">08 · 驗收</span>
  <h2>情境測驗</h2>
  <p>離開前試試看：下面的情境都真的會遇到。每題選一個你認為的最佳做法，選了馬上看得到解釋。</p>
  <div data-quiz>

    <div class="quiz-q" data-answer="B">
      <p class="quiz-tag">Q1 <span class="qtype">情境題</span></p>
      <h3>你請 AI 寫報帳工具的四捨五入函式，測試沒過。你回了三次「還是不對，再修一下」，它每次交回的程式都一模一樣。最好的下一步是？</h3>
      <div class="quiz-opts">
        <button type="button" class="quiz-opt" data-k="A">A. 再說一次，加上「這很重要，請仔細檢查每一行」</button>
        <button type="button" class="quiz-opt" data-k="B">B. 看一眼失敗的測試，用一句話說出錯在哪（例如「負數要遠離 0 進位：-2.5 → -3」），連同錯誤輸出一起貼；同一件事糾正兩次還不行，就開新對話，把這條規則寫進第一句需求</button>
        <button type="button" class="quiz-opt" data-k="C">C. 把 temperature 調成 0，讓它的輸出更穩定</button>
        <button type="button" class="quiz-opt" data-k="D">D. 請它把整個檔案重寫成更長、更完整的版本</button>
      </div>
      <div class="quiz-fb" aria-live="polite"><p>本課實測（qwen3.5-2b）：只說「不對」時，新版有 72% 跟上一版一字不差——它沒拿到任何新資訊，最省事的回應就是照交。同樣 80 個沒過的第一版，錯誤原文外加一句診斷救回 21 個，只說不對救回 6 個。這也是官方最佳實務的建議：同一件事糾正兩次還不行，對話已經塞滿失敗的嘗試，開新對話、把學到的寫進更好的提示。A 加強語氣但沒加資訊；C 方向相反——問題不是隨機性，而是缺資訊，temperature 0 只會讓它更穩定地交出同一份；D 長不等於對，還讓你更難看 diff。</p></div>
    </div>

    <div class="quiz-q" data-answer="B">
      <p class="quiz-tag">Q2 <span class="qtype dx">錯誤診斷</span></p>
      <h3>AI 寫的 <code>round_half_up</code> 只有一行 <code>return int(x + 0.5)</code>，正數的測試全過，跑完整測試卻出現下面的失敗（本課實測的 pytest 原文節錄）。根本原因是？</h3>
      <div class="codeblock">.....FF
___________________ test_edge_3 ___________________
test_solution.py:20: in test_edge_3
    assert round_half_up(-2.5) == -3
E   assert -2 == -3
E    +  where -2 = round_half_up(-2.5)
___________________ test_edge_4 ___________________
test_solution.py:23: in test_edge_4
    assert round_half_up(-1.6) == -2
E   assert -1 == -2
E    +  where -1 = round_half_up(-1.6)
2 failed, 5 passed in 0.01s</div>
      <div class="quiz-opts">
        <button type="button" class="quiz-opt" data-k="A">A. 浮點數精度誤差：-2.5 在電腦裡存不準</button>
        <button type="button" class="quiz-opt" data-k="B">B. int() 是「往 0 截斷」：-2.5 + 0.5 = -2.0 → -2、-1.6 + 0.5 = -1.1 → -1；負數要往遠離 0 的方向處理（依正負號分開算，或用 decimal 的 ROUND_HALF_UP）</button>
        <button type="button" class="quiz-opt" data-k="C">C. 測試寫錯了：-2.5 四捨五入本來就是 -2</button>
        <button type="button" class="quiz-opt" data-k="D">D. 應該改用 Python 內建的 round()</button>
      </div>
      <div class="quiz-fb" aria-live="polite"><p><code>int()</code> 對負數是往 0 截斷，<code>x + 0.5</code> 的技巧只在正數成立——這正是本課 8 次重跑、8 個第一版全都寫出來的那一行，而基本測試剛好只有正數，所以「只有基本測試」的迴圈 8 次全停在這個錯答案上。修法：依正負號分開處理，或用 <code>decimal</code> 的 <code>ROUND_HALF_UP</code>；並把負數案例留在測試裡，防止再退化。A 不成立：-2.5 在二進位浮點數裡可以精確表示；C 是規格問題而不是 bug——這裡的需求是「遠離 0 進位」，測試就是把你心裡的答案寫下來的地方；D 更糟：Python 的 <code>round()</code> 是銀行家捨入，<code>round(2.5)</code> 是 2，連正數的 .5 都會錯。</p></div>
    </div>

    <div class="quiz-q" data-answer="C">
      <p class="quiz-tag">Q3 <span class="qtype">情境題</span></p>
      <h3>你讓 coding agent 寫手機號碼正規化，它回報「所有測試通過 ✅」。上線第一天，使用者輸入 <code>+886 912 345 678</code> 就出錯。回頭一看，測試只有 <code>0912345678</code> 和 <code>0912-345-678</code> 兩個案例。最該做的是？</h3>
      <div class="quiz-opts">
        <button type="button" class="quiz-opt" data-k="A">A. 換一個更強的模型重寫，強模型不會漏這種情況</button>
        <button type="button" class="quiz-opt" data-k="B">B. 在提示裡要求 agent 以後回報完成前「再自己多檢查一次」</button>
        <button type="button" class="quiz-opt" data-k="C">C. 把出事的輸入連同同類情況（國際寫法、括號、市話、位數不對）寫成測試案例，讓迴圈對著它們修；之後新功能先列邊界案例再開工</button>
        <button type="button" class="quiz-opt" data-k="D">D. 關掉自動測試，改成每次上線前人工點一遍</button>
      </div>
      <div class="quiz-fb" aria-live="polite"><p>agent 的「完成」就是它看得到的檢查全綠——測試只蓋快樂路徑，迴圈就會很有效率地停在錯的答案上。本課實測 96 個題次裡有 22 個「基本測試全綠、完整測試沒過」，其中 20 個第一版就停手。把需求裡沒寫、你心裡有答案的細節寫成測試，是把意圖交給 AI 最可靠的方式。A 的問題是：再強的模型也猜不到你沒說的格式要求（測試才是規格）；B 沒有增加任何新的眼睛，而且讓寫程式的同一個 agent 批改自己，正是官方建議改用獨立審查的原因；D 把眼睛整個拿掉，還把驗收退回「靠人記得」。</p></div>
    </div>

    <div class="quiz-q" data-answer="C">
      <p class="quiz-tag">Q4 <span class="qtype dx">錯誤診斷</span></p>
      <h3>你請 AI 推薦「把民國年日期轉成西元年」的套件，照它的建議執行安裝，出現下面的錯誤（實測，pip 26.2.1）。最可能的原因與正確做法？</h3>
      <div class="codeblock">$ pip install dateutil
ERROR: Could not find a version that satisfies the requirement dateutil (from versions: none)
ERROR: No matching distribution found for dateutil</div>
      <div class="quiz-opts">
        <button type="button" class="quiz-opt" data-k="A">A. 網路或 PyPI 暫時故障，等一下再試就好</button>
        <button type="button" class="quiz-opt" data-k="B">B. Python 版本太新，降到 3.10 就裝得起來</button>
        <button type="button" class="quiz-opt" data-k="C">C. PyPI 上根本沒有叫 dateutil 的套件——那是 import 的名字，套件本名是 python-dateutil；AI 給的名字要先到 PyPI 查證，別憑感覺猜相近的名字，也要提防有人搶註 AI 常編的名字</button>
        <button type="button" class="quiz-opt" data-k="D">D. 權限不足，加 sudo 重跑</button>
      </div>
      <div class="quiz-fb" aria-live="polite"><p>前面沒有任何連線警告、直接 <code>from versions: none</code>，意思是 PyPI 有回應、但這個名字底下<b>一個版本都沒有</b>——不是裝不起來，是這個名字不存在。本課實測模型推薦的 135 個套件名裡有 14 次查無此套件，<code>dateutil</code> 就是其中之一：import 名與 pip 名不同的套件很多（<code>dateutil</code>／<code>python-dateutil</code>、<code>cv2</code>／<code>opencv-python</code>），AI 很容易把兩者混用。危險在於：不存在的名字可以被任何人註冊——slopsquatting 就是搶先註冊這些名字、等人照著 AI 的建議安裝。A：網路不通時結尾也會是 <code>versions: none</code>，但前面會先出現一串 <code>Retrying … NewConnectionError</code> 警告（實測），這裡沒有；B 版本不合時 pip 會列出現有版本；D 權限問題的錯誤訊息完全不同，而且對不存在的套件加 sudo 毫無意義。</p></div>
    </div>

    <div class="quiz-score" data-score></div>
  </div>
</section>

<div class="endnav">
  <a href="/genai-rag-advanced/">
    <span class="tag">全系列完 · 從頭複習</span>
    <b>↺ 回補充 A：進階 RAG →</b>
  </a>
  <a href="/genai-intro/">
    <span class="tag">主題</span>
    <b>‹ 回「生成式 AI 導論」課程列表</b>
  </a>
</div>
'''

SCRIPT = r"""
/* ═══ hero：同一份第一版、五種下一步的重播機 ═══
   HERO＝實測紀錄（spike_genai_vibecoding*.py 錄製、_pack.py 注入；不要手改） */
const HERO = {"prompt": "寫一個 Python 函式 round_half_up(x: float) -> int：把 x 四捨五入成整數。", "name": "round_half_up", "nb": 3, "run": 4, "model": "qwen3.5-2b", "temperature": 0.7, "date": "2026-09-24", "branches": {"reroll": [{"code": "def round_half_up(x: float) -> int:\n    return int(x + 0.5)", "bits": [1, 1, 1, 1, 1, 0, 0], "same": false, "fb": null}, {"code": "def round_half_up(x: float) -> int:\n    return int(x + 0.5)", "bits": [1, 1, 1, 1, 1, 0, 0], "same": true, "fb": null}, {"code": "def round_half_up(x: float) -> int:\n    return int(x + 0.5)", "bits": [1, 1, 1, 1, 1, 0, 0], "same": true, "fb": null}, {"code": "def round_half_up(x: float) -> int:\n    return int(x + 0.5)", "bits": [1, 1, 1, 1, 1, 0, 0], "same": true, "fb": null}], "bare": [{"code": "def round_half_up(x: float) -> int:\n    return int(x + 0.5)", "bits": [1, 1, 1, 1, 1, 0, 0], "same": false, "fb": "測試沒有全部通過，請修正程式後重新輸出完整程式碼。"}, {"code": "def round_half_up(x: float) -> int:\n    return int(x + 0.5)", "bits": [1, 1, 1, 1, 1, 0, 0], "same": true, "fb": "測試沒有全部通過，請修正程式後重新輸出完整程式碼。"}, {"code": "def round_half_up(x: float) -> int:\n    return int(x + 0.5)", "bits": [1, 1, 1, 1, 1, 0, 0], "same": true, "fb": "測試沒有全部通過，請修正程式後重新輸出完整程式碼。"}, {"code": "def round_half_up(x: float) -> int:\n    return int(x + 0.5)", "bits": [1, 1, 1, 1, 1, 0, 0], "same": true, "fb": null}], "full": [{"code": "def round_half_up(x: float) -> int:\n    return int(x + 0.5)", "bits": [1, 1, 1, 1, 1, 0, 0], "same": false, "fb": "我跑了測試，結果如下。請根據失敗訊息修正程式，重新輸出完整程式碼。\n```\n.....FF                                                                  [100%]\n=================================== FAILURES ===================================\n_________________________________ test_edge_3 __________________________________\ntest_solution.py:20: in test_edge_3\n    assert round_half_up(-2.5) == -3\nE   assert -2 == -3\nE    +  where -2 = round_half_up(-2.5)\n_________________________________ test_edge_4 __________________________________\ntest_solution.py:23: in test_edge_4\n    assert round_half_up(-1.6) == -2\nE   assert -1 == -2\nE    +  where -1 = round_half_up(-1.6)\n=========================== short test summary info ============================\nFAILED test_solution.py::test_edge_3 - assert -2 == -3\n…（以下略）"}, {"code": "def round_half_up(x: float) -> int:\n    if x >= 0:\n        return int(x + 0.5)\n    else:\n        return int(x - 0.5)", "bits": [1, 1, 1, 1, 1, 1, 1], "same": false, "fb": null}], "hint": [{"code": "def round_half_up(x: float) -> int:\n    return int(x + 0.5)", "bits": [1, 1, 1, 1, 1, 0, 0], "same": false, "fb": "我跑了測試，結果如下。請根據失敗訊息修正程式，重新輸出完整程式碼。\n```\n.....FF                                                                  [100%]\n=================================== FAILURES ===================================\n_________________________________ test_edge_3 __________________________________\ntest_solution.py:20: in test_edge_3\n    assert round_half_up(-2.5) == -3\nE   assert -2 == -3\nE    +  where -2 = round_half_up(-2.5)\n_________________________________ test_edge_4 __________________________________\ntest_solution.py:23: in test_edge_4\n    assert round_half_up(-1.6) == -2\nE   assert -1 == -2\nE    +  where -1 = round_half_up(-1.6)\n=========================== short test summary info ============================\nFAILED test_solution.py::test_edge_3 - assert -2 == -3\n…（以下略）"}, {"code": "def round_half_up(x: float) -> int:\n    if x >= 0:\n        return int(x + 0.5)\n    else:\n        return int(x - 0.5)", "bits": [1, 1, 1, 1, 1, 1, 1], "same": false, "fb": null}], "weak": [{"code": "def round_half_up(x: float) -> int:\n    return int(x + 0.5)", "bits": [1, 1, 1, 1, 1, 0, 0], "same": false, "fb": null}]}};
(function () {
  if (!HERO) return;
  const COND = [
    { k: "bare", label: "只說「不對，再修」", c: "#9AA7AE" },
    { k: "full", label: "貼回錯誤原文", c: "#55A868" },
    { k: "hint", label: "錯誤＋你的一句診斷", c: "#4C72B0" },
    { k: "reroll", label: "開新對話重抽", c: "#8172B2" },
    { k: "weak", label: "只有基本測試", c: "#C44E52" },
  ].filter((x) => HERO.branches[x.k]);
  const VERDICT = {
    bare: "它沒拿到任何新資訊，最省事的回應就是把同一份再交一次。",
    full: "錯誤原文裡寫著 assert -2 == -3——這一次它讀懂了（8 次重跑裡有 3 次）。",
    hint: "加一句「負數要遠離 0 進位」，第 2 版就改對（8 次重跑 8 次都改對）。",
    reroll: "開新對話重抽也沒用：這不是運氣問題，是模型的系統性誤解（24 次重抽全是同一行）。",
  };
  const picks = document.getElementById("loop-picks");
  const stage = document.getElementById("loop-stage");
  const next = document.getElementById("loop-next");
  const reset = document.getElementById("loop-reset");
  const pos = document.getElementById("loop-pos");
  if (!picks) return;
  document.getElementById("loop-need").innerHTML = "<b>一句話需求：</b>" + esc(HERO.prompt);
  document.getElementById("loop-src").textContent =
    `實測紀錄：${HERO.model}、temperature ${HERO.temperature}、${HERO.date}（第 ${HERO.run + 1} 次重跑）。每一版都在沙盒裡跑過 pytest；其他重跑在實驗場 2️⃣ 都看得到。`;
  let cur = 0, shown = 1;
  COND.forEach((m, i) => {
    const b = document.createElement("button");
    b.type = "button";
    b.className = "pick";
    b.style.setProperty("--tc", m.c);
    b.textContent = m.label;
    b.addEventListener("click", () => { cur = i; shown = 1; render(); });
    picks.appendChild(b);
  });
  function esc(t) { return String(t).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;"); }
  function steps(m) { return HERO.branches[m.k].length + (m.k === "weak" ? 1 : 0); }
  function dots(bits, hideEdge) {
    let s = '<span class="dots">';
    bits.forEach((ok, i) => {
      if (i === HERO.nb) s += '<span class="gap"></span>';
      const kind = i < HERO.nb ? "b" : "e";
      const st = kind === "e" && hideEdge ? "q" : (ok ? "y" : "n");
      s += `<span class="dot ${kind} ${st}"></span>`;
    });
    return s + "</span>";
  }
  function render() {
    const m = COND[cur];
    const rows = HERO.branches[m.k];
    const weak = m.k === "weak";
    const reveal = weak && shown > rows.length;
    picks.querySelectorAll(".pick").forEach((el, i) => el.classList.toggle("on", i === cur));
    let html = "";
    rows.slice(0, Math.min(shown, rows.length)).forEach((r, i) => {
      const all = r.bits.every(Boolean);
      const hide = weak && !reveal;
      const nbOk = r.bits.slice(0, HERO.nb).filter(Boolean).length;
      const neOk = r.bits.slice(HERO.nb).filter(Boolean).length;
      const tag = all ? "✅ 完整測試全過" :
        (hide ? `基本 ${nbOk}/${HERO.nb} ✅（邊界測試 AI 看不到）` :
         `❌ 基本 ${nbOk}/${HERO.nb}、邊界 ${neOk}/${r.bits.length - HERO.nb}`);
      html += `<div class="ver${all ? " ok" : ""}"><div class="hd">第 ${i + 1} 版 ${dots(r.bits, hide)} <span>${tag}</span></div>`;
      if (i > 0 && r.same) {
        html += `<div class="same">${m.k === "reroll" ? "↺ 開新對話重抽，抽到的還是一字不差的同一份" : "↺ 跟上一版一字不差"}</div>`;
      } else {
        html += `<pre>${esc(r.code)}</pre>`;
      }
      if (i + 1 < Math.min(shown, rows.length)) {
        if (r.fb) html += `<div class="lbl">AI 接著收到：</div><pre class="fb">${esc(r.fb)}</pre>`;
        else if (m.k === "reroll") html += '<div class="lbl">（沒有回饋：開新對話，同一句需求再生成一次）</div>';
      }
      html += "</div>";
    });
    if (weak && shown === rows.length) {
      html += '<div class="verdict" style="--tc:#C44E52">AI 看得到的測試全綠，迴圈停了。按「下一步」揭曉它看不到的邊界測試。</div>';
    } else if (shown === steps(m)) {
      const last = rows[rows.length - 1];
      let v;
      if (weak) v = "空心的邊界測試是紅的：負數全錯。在 AI 眼裡它早就「做完了」——8 次重跑，8 次都停在這裡。";
      else v = (last.bits.every(Boolean) ? `第 ${rows.length} 版全過。` : `試了 ${rows.length} 版，還是沒過。`) + (VERDICT[m.k] || "");
      html += `<div class="verdict" style="--tc:${m.c}">${v}</div>`;
    }
    stage.innerHTML = html;
    next.disabled = shown >= steps(m);
    pos.textContent = `${shown} / ${steps(m)}`;
  }
  next.addEventListener("click", () => { shown = Math.min(shown + 1, steps(COND[cur])); render(); });
  reset.addEventListener("click", () => { shown = 1; render(); });
  render();
})();
"""
