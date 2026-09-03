"""課程頁內容區（純常數）。改完跑：python3 .claude/skills/make-lesson/scripts/page-fill.py content/mlops/dvc-basics
build.sh 不會部署這個檔；它是 index.html 內容區的正本。"""

TITLE = "DVC 資料版本控制：資料與模型也要有 git"
DESCRIPTION = "300 MB 的訓練資料丟進 git 會炸，那要怎麼版本控制？DVC 讓 git 只存一個 89 bytes 的指標檔，資料本身放 cache 與遠端。從 dvc add、切回舊版資料、dvc.yaml 管線「沒變就 skip」、params/metrics diff、dvc push/pull，到跟 MLflow 怎麼分工——molab 免費環境開一個真的 git repo 全程實作。"
NB = "https://molab.marimo.io/github/skmygo/agentclass/blob/main/content/mlops/dvc-basics/dvc-basics_ext.py"

STYLE = r"""
  /* 語義色：藍＝git／指標檔、橘＝DVC cache／內容、綠＝skip（沒變不用跑）、紅＝重跑／改動 */
  :root { --c1: #4C72B0; --c2: #DD8452; --c3: #55A868; --cut: #C44E52; }
  a.golab { text-decoration: none; display: inline-flex; align-items: center; gap: 8px; }

  /* ── hero：資料的時光機 ── */
  #tm { --pane-bg: #fff; }
  #tm .cap { font-size: 11.5px; font-weight: 800; letter-spacing: .07em; color: var(--ink-soft); margin-bottom: 9px; }
  #tm .rail { display: flex; flex-wrap: wrap; gap: 8px; }
  #tm .rail button { flex: 1 1 118px; min-width: 0; text-align: left; cursor: pointer;
    font-family: inherit; color: var(--ink); background: #fff; border: 1.5px solid var(--grid);
    border-radius: 10px; padding: 8px 10px; transition: border-color .15s, background .15s, box-shadow .15s; }
  #tm .rail button:hover { background: var(--chip-bg); }
  #tm .rail button.on { border-color: var(--c1); box-shadow: inset 0 0 0 1px var(--c1); background: var(--chip-bg); }
  #tm .rail b { display: block; font-family: var(--mono); font-size: 13px; color: var(--c1); }
  #tm .rail span { display: block; font-size: 11.5px; line-height: 1.45; color: var(--ink-soft); margin-top: 2px; }
  #tm .panes { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 9px; margin-top: 11px; }
  #tm .pane { border: 1.5px solid var(--grid); border-radius: 10px; padding: 8px 10px 10px; min-width: 0; background: var(--pane-bg); }
  #tm .pane .ptag { display: block; font-size: 10.5px; font-weight: 800; letter-spacing: .07em; margin-bottom: 5px; }
  #tm .pane.git .ptag { color: var(--c1); }
  #tm .pane.cache .ptag { color: var(--c2); }
  #tm .pane.ws .ptag { color: var(--ink-soft); }
  #tm .pane pre { font-family: var(--mono); font-size: 11px; line-height: 1.55; margin: 0;
    white-space: pre-wrap; word-break: normal; overflow-wrap: anywhere; }
  #tm .pane em { font-style: normal; color: var(--c2); }
  #tm .pane i { font-style: normal; color: var(--cut); font-weight: 700; }
  #tm .say { margin-top: 10px; font-size: 13px; line-height: 1.65; border-left: 3px solid var(--c1); padding-left: 10px; }
  #tm .hr { height: 1px; background: var(--grid); margin: 16px 0 13px; }
  #tm .chips { display: flex; flex-wrap: wrap; gap: 6px; }
  #tm .chips button { font-family: var(--mono); font-size: 12px; padding: 5px 10px; border-radius: 999px;
    border: 1.5px solid var(--grid); background: #fff; color: var(--ink); cursor: pointer; }
  #tm .chips button:hover { background: var(--chip-bg); }
  #tm .chips button.on { border-color: var(--ink); background: var(--ink); color: #fff; }
  #tm .out { margin-top: 9px; border: 1.5px solid var(--grid); border-radius: 10px; padding: 9px 11px; background: var(--pane-bg); }
  #tm .out pre { font-family: var(--mono); font-size: 11.5px; line-height: 1.6; margin: 0;
    white-space: pre-wrap; word-break: break-word; overflow-wrap: anywhere; }
  #tm .out .skip { color: var(--c3); }
  #tm .out .run { color: var(--cut); font-weight: 700; }
  #tm .out .dim { color: var(--ink-soft); }
  #tm .tally { margin-top: 8px; font-size: 12.5px; color: var(--ink-soft); }
  @media (max-width: 620px) { #tm .panes { grid-template-columns: 1fr; } }

  table.cmp { width: 100%; border-collapse: collapse; font-size: 13.5px; margin: 14px 0; }
  table.cmp th, table.cmp td { border-bottom: 1px solid var(--grid); padding: 8px 10px; text-align: left; vertical-align: top; }
  table.cmp th { font-size: 12px; letter-spacing: .04em; color: var(--ink-soft); }
  table.cmp td.b { color: var(--c1); font-weight: 700; }
  table.cmp td.o { color: var(--c2); font-weight: 700; }
  table.cmp td.g { color: var(--c3); font-weight: 700; }
  table.cmp td.r { color: var(--cut); font-weight: 700; }
  .kbd { font-family: var(--mono); background: var(--chip-bg); padding: 1px 6px; border-radius: 5px; font-size: 13px; }
"""

WRAP = r'''
<section id="hero">
  <span class="eyebrow">DATA VERSIONING · 補充 G · 12</span>
  <h1>DVC 資料版本控制：<br>資料與模型也要有 git</h1>
  <p style="margin-top:18px">
    你的程式碼有 git，每一行改動都查得到。那<b>資料</b>呢？300 MB 的訓練資料丟進 git，clone 一次十分鐘、
    <span class="kbd">git diff</span> 給你看兩百萬行亂碼；500 MB 的模型檔每訓練一次多一份，半年後 repo 變 40 GB。
    於是大家的資料夾裡開始出現 <span class="kbd">raw_final_v2_修正版.csv</span>。
    DVC 的解法只有一句話：<b>git 只存一個小小的指標檔，真正的檔案放在別的地方。</b>
    這台時光機是 notebook 跑出來的四個 commit——點一個版本，看 git 裡到底存了什麼：
  </p>

  <div class="hero-demo" id="tm">
    <div class="cap">四個 COMMIT（點一個看內容）</div>
    <div class="rail" id="tm-rail"></div>
    <div class="panes">
      <div class="pane git"><span class="ptag">GIT 裡存的</span><pre id="tm-git"></pre></div>
      <div class="pane cache"><span class="ptag">.DVC/CACHE 裡存的</span><pre id="tm-cache"></pre></div>
      <div class="pane ws"><span class="ptag">DVC CHECKOUT 之後的工作區</span><pre id="tm-ws"></pre></div>
    </div>
    <p class="say" id="tm-say"></p>

    <div class="hr"></div>
    <div class="cap">那「要不要重跑」呢？改一樣東西，按下 DVC REPRO</div>
    <div class="chips" id="tm-chips"></div>
    <div class="out"><pre id="tm-out"></pre></div>
    <p class="tally" id="tm-tally"></p>
  </div>

  <p class="note">
    md5、檔案大小、AUC、每一行終端機輸出都是 notebook 的實測結果（DVC 3.67.1）；
    你自己跑會拿到一樣的 md5——這正是「內容定址」的意思。
  </p>
</section>

<section id="s1">
  <span class="eyebrow">01 · 為什麼</span>
  <h2>git 不是設計來裝資料的</h2>
  <p>
    git 之所以快，是因為它假設你放的是<b>文字</b>：它會存差異、會壓縮、會讓你看得懂每一次改了什麼。
    二進位大檔完全踩在這些假設的反面——存不了差異（每一版都是完整一份）、壓不動、
    diff 出來沒有意義，而且 <b>git 的歷史是不會縮小的</b>：你今天刪掉那個 800 MB 的檔案，
    它還是躺在每一個人的 <span class="kbd">.git</span> 裡，永遠。
  </p>
  <p>
    DVC 的做法是把「檔案」跟「這是哪一版檔案」拆成兩件事。<b>git 只負責後者</b>——
    存一個記著 md5 的小文字檔；檔案本身交給 DVC 放進 cache 與遠端儲存。本課的實測：
  </p>
  <table class="cmp">
    <tr><th></th><th>大小</th><th>誰在管</th></tr>
    <tr><td>訓練資料 <span class="kbd">data/raw.csv</span></td><td class="o">470,591 bytes（460 KB）</td><td class="o">DVC（cache ＋ 遠端）</td></tr>
    <tr><td>指標檔 <span class="kbd">data/raw.csv.dvc</span></td><td class="b">89 bytes</td><td class="b">git</td></tr>
    <tr><td>跑完四個版本後的 <span class="kbd">.git</span></td><td class="b">348 KB</td><td class="b">git</td></tr>
    <tr><td>同時期的 <span class="kbd">.dvc/cache</span></td><td class="o">2,092 KB</td><td class="o">DVC</td></tr>
  </table>
  <p>
    把 460 KB 換成 460 GB，<span class="kbd">.git</span> 還是那個大小——<b>指標檔的大小跟資料完全無關</b>。
    這就是全部的魔法，剩下的都是這件事的推論。
  </p>
  <p>
    <b>那 Git LFS 呢？</b>LFS 解決的是同一個容量問題，但它到此為止。DVC 多做了兩件事：
    <b>①</b> 遠端可以是你自己的 S3／GCS／NAS，不必買 LFS 的儲存配額；
    <b>②</b> 它還管<b>管線</b>——哪一版資料配哪一版程式產出哪一個模型、以及「這一步到底要不要重跑」。
    後面五節講的全是這一半，而那一半 LFS 沒有。
  </p>
  <a class="golab" href="__NB__" target="_blank" rel="noopener">到 notebook 的 0️⃣ 節：開一個真的 git repo，跑 dvc init</a>
</section>

<section id="s2">
  <span class="eyebrow">02 · DVC ADD</span>
  <h2>一個指令，三件事</h2>
  <div class="codeblock">$ dvc add data/raw.csv
To track the changes with git, run:

	git add data/.gitignore data/raw.csv.dvc</div>
  <p>
    <span class="kbd">dvc add</span> 做完這三件事：算出檔案的 md5 並把<b>檔案本身</b>複製進
    <span class="kbd">.dvc/cache</span>、產生指標檔 <span class="kbd">data/raw.csv.dvc</span>、
    在 <span class="kbd">data/.gitignore</span> 加一行 <span class="kbd">/raw.csv</span>
    <b>叫 git 不要碰這個大檔</b>。指標檔整個就這 5 行：
  </p>
  <div class="codeblock">outs:
- md5: 8445065497d9a2aa59d1ee84e100dc5d
  size: 470591
  hash: md5
  path: raw.csv</div>
  <p>
    然後看 cache 裡那個檔名：<span class="kbd">.dvc/cache/files/md5/84/45065497d9a2aa59d1ee84e100dc5d</span>——
    前兩碼當資料夾、剩下的當檔名，<b>合起來就是指標檔裡那串 md5</b>。這叫<b>內容定址</b>，兩個直接的好處：
    同樣的內容只會存一份（十個人各自 add 同一份資料，cache 裡還是一份）；
    檔案在不在、有沒有被動過，比對 md5 就知道，<b>不需要相信檔名或修改時間</b>。
  </p>
  <p>
    資料改了會怎樣？notebook 裡把 2000 列中的一格標籤翻掉，重新 <span class="kbd">dvc add</span>，
    然後看 <span class="kbd">git diff</span>：
  </p>
  <div class="codeblock">$ git diff data/raw.csv.dvc
@@ -1,5 +1,5 @@
 outs:
-- md5: 8445065497d9a2aa59d1ee84e100dc5d
+- md5: 464179a42e1b28ead96babdf5cdaa79e
   size: 470591
   hash: md5
   path: raw.csv</div>
  <p>
    <b>整個 diff 就是一行。</b>資料的改動在 code review 裡是一行，不是兩百萬行亂碼——
    但那一行足以精確指出「是哪一份資料」。同時 cache 裡變成<b>兩份</b>內容：
    舊的沒有被覆蓋掉，所以下一節回得去。
  </p>
  <a class="golab" href="__NB__" target="_blank" rel="noopener">到 notebook 的 1️⃣ 節：指標檔、.gitignore、cache 一次看完</a>
</section>

<section id="s3">
  <span class="eyebrow">03 · 回溯</span>
  <h2>切版本永遠是兩步</h2>
  <p>
    這是新手最容易掉進去的一個洞，先把規則寫死：
    <b>git 管指標檔，DVC 管檔案本身，所以切版本要兩個動作。</b>
  </p>
  <div class="codeblock">$ git checkout e713732 -- data/raw.csv.dvc     # ← 只有指標檔回到 v1
$ dvc status
data/raw.csv.dvc:
	changed outs:
		modified:           data/raw.csv          # ← DVC 在說：檔案跟指標檔對不上了

$ dvc checkout                                 # ← 資料才真的變回去
M       data/raw.csv</div>
  <p>
    中間那個狀態很危險：指標檔已經是 v1 的，但 <span class="kbd">data/raw.csv</span> 還是新的那一份，
    <b>而 git 一句話都不會說</b>——它根本不知道有這個檔案存在。你會拿舊程式配新資料訓練，
    然後對著一個「重現不出來」的數字抓半天。
  </p>
  <p>
    唯一會告訴你的是 <span class="kbd">dvc status</span>。所以請把它變成肌肉記憶：
    <b>每次 <span class="kbd">git checkout</span> 之後，接一句 <span class="kbd">dvc status</span></b>；
    看到 <span class="kbd">modified</span> 就 <span class="kbd">dvc checkout</span>。
    還原是從 cache 直接複製的，不重算、不連網，大檔案也是一瞬間。
  </p>
  <a class="golab" href="__NB__" target="_blank" rel="noopener">到 notebook 的 2️⃣ 節：把「中間狀態」實際演一次</a>
</section>

<section id="s4">
  <span class="eyebrow">04 · 管線</span>
  <h2><span class="kbd">dvc.yaml</span>：把「模型是怎麼來的」寫下來</h2>
  <p>
    版本控制只解決了一半的問題。另一半是：<b>這個模型是怎麼來的？</b>
    <span class="kbd">dvc.yaml</span> 用很像 Makefile 的方式描述一條管線。一個 <b>stage</b> 要講四件事：
  </p>
  <table class="cmp">
    <tr><th>欄位</th><th>意思</th><th>為什麼重要</th></tr>
    <tr><td class="b">cmd</td><td>要跑的指令</td><td>就是你平常在終端機打的那行，程式完全不用知道 DVC 存在</td></tr>
    <tr><td class="b">deps</td><td>這一步吃什麼（資料、程式）</td><td><b>任何一個變了才需要重跑</b></td></tr>
    <tr><td class="b">params</td><td>從 <span class="kbd">params.yaml</span> 讀哪些設定</td><td>參數變了也要重跑；<b>沒宣告的參數 DVC 看不見</b></td></tr>
    <tr><td class="b">outs / metrics</td><td>這一步吐出什麼</td><td>產物交給 DVC 管：自動進 cache、自動 gitignore</td></tr>
  </table>
  <div class="codeblock">stages:
  train:
    cmd: python train.py
    deps:
      - data/raw.csv
      - train.py
    params:
      - train.max_depth
      - train.n_estimators
    outs:
      - model.pkl        # ← 模型檔也歸 DVC 管，這就是課名的「模型」那一半
    metrics:
      - metrics.json</div>
  <p>
    <span class="kbd">dvc repro</span> 會走過每個 stage，比對 <span class="kbd">deps</span> 與
    <span class="kbd">params</span> 的 md5：<b>對得上就跳過，對不上才跑 <span class="kbd">cmd</span></b>。
    實測第一次 2.2–2.6 秒（真的訓練），第二次 0.5–0.6 秒、什麼都沒跑：
  </p>
  <div class="codeblock">$ dvc repro
'data/raw.csv.dvc' didn't change, skipping
Stage 'train' didn't change, skipping
Data and pipelines are up to date.</div>
  <p>
    跑完會多一個 <span class="kbd">dvc.lock</span>——這次執行的<b>收據</b>：每一個依賴、每一個參數、
    每一個產物的 md5 全部記在裡面。它很小，<b>要進 git</b>；
    <span class="kbd">model.pkl</span> 與 <span class="kbd">metrics.json</span> 則被自動寫進
    <span class="kbd">.gitignore</span>。於是任何一個 commit 都完整回答了
    「這個模型是用哪一版資料、哪些參數、哪一版程式跑出來的」。
  </p>
  <a class="golab" href="__NB__" target="_blank" rel="noopener">到 notebook 的 3️⃣ 節：寫 dvc.yaml、跑 repro、讀 dvc.lock</a>
</section>

<section id="s5">
  <span class="eyebrow">05 · 只重跑該跑的</span>
  <h2>管線的價值不是「一鍵重跑」，是「不跑」</h2>
  <p>
    真實管線不會只有一步。notebook 把它拆成兩個 stage：<span class="kbd">prepare</span>
    讀原始資料切成訓練／測試集（2000 列 → train 1500 / test 500），<span class="kbd">train</span> 讀那兩個檔訓練。
    <b>你不用宣告執行順序</b>——DVC 從「誰吃誰的產物」自己推出來，
    <span class="kbd">dvc dag</span> 畫出來的圖因此永遠跟真正跑的東西一致，不會像投影片上的架構圖那樣過期。
  </p>
  <div class="codeblock">$ dvc dag
+------------------+
| data/raw.csv.dvc |
+------------------+
          *
    +---------+
    | prepare |
    +---------+
          *
      +-------+
      | train |
      +-------+</div>
  <p>拆開之後最有感的一件事：<b>只改參數，切分資料那一步不會重做</b>。</p>
  <div class="codeblock">$ dvc repro                                  # 只把 max_depth 改成 8
'data/raw.csv.dvc' didn't change, skipping
Stage 'prepare' didn't change, skipping      # ← 依賴一個字都沒變
Running stage 'train':
> python train.py
auc = 0.97016</div>
  <p>
    實測：只重跑 <span class="kbd">train</span> 是 1.9 秒；改到資料、兩個 stage 都要跑是 4.9 秒。
    這裡差的是三秒，在真實專案裡是三十秒與三小時的差別——
    而且管線越長、前面的步驟越重（資料清洗、特徵工程、embedding），省下來的越多。
  </p>
  <p>
    還有一個更狠的：把 <span class="kbd">max_depth</span> <b>改回</b>剛剛跑過的值再 repro——
  </p>
  <div class="codeblock">$ dvc repro
Stage 'prepare' didn't change, skipping
Stage 'train' is cached - skipping run, checking out outputs</div>
  <p>
    <b><span class="kbd">is cached</span></b>：這組依賴＋參數的組合 DVC 以前算過，
    它直接把當時的產物從 cache 撈回來，連跑都不用跑。這叫 <b>run cache</b>——
    來回比較兩組參數時，第二次之後都是瞬間完成。
  </p>
  <a class="golab" href="__NB__" target="_blank" rel="noopener">到 notebook 的 5️⃣ 節：兩個 stage、dag、skip 與 run cache</a>
</section>

<section id="s6">
  <span class="eyebrow">06 · 比較</span>
  <h2>這次改動換到了什麼？</h2>
  <p>
    改完參數重跑之後，兩個指令直接告訴你差在哪——比的是<b>工作區</b>與 <b>HEAD（上一個 commit）</b>：
  </p>
  <div class="codeblock">$ dvc params diff
Path         Param            HEAD    workspace
params.yaml  train.max_depth  4       12

$ dvc metrics diff
Path          Metric    HEAD     workspace    Change
metrics.json  auc       0.95318  0.97287      0.01969</div>
  <p>
    <span class="kbd">Change</span> 那一欄是 DVC 幫你算的，可以直接貼進 PR 描述裡。
    注意這一輪<b>沒有任何一份資料被複製</b>——資料的 md5 沒變，DVC 認得出來是同一份。
    <b>參數的版本與資料的版本，是分開追蹤的兩件事。</b>
  </p>
  <p>
    但如果你想試十二組參數呢？照上面那套「改 <span class="kbd">params.yaml</span> → repro → commit」，
    你的 git 歷史會多出十二個沒人想看的 commit。<span class="kbd">dvc exp run</span> 就是為這件事存在的：
  </p>
  <div class="codeblock">$ dvc exp run --set-param train.max_depth=6
$ dvc exp run --set-param train.max_depth=20
$ dvc exp show --only-changed
  Experiment                 Created        auc   train.max_depth
  workspace                  -          0.97063   20
  master                     05:15 AM   0.97287   12
  ├── d4186d7 [blunt-torc]   05:15 AM   0.97063   20
  └── 9285a95 [gaunt-debs]   05:15 AM   0.96376   6</div>
  <p>
    它暫時換掉參數、跑一次管線、把結果存成一個<b>實驗</b>（掛在 git 上但不是 commit），
    <span class="kbd">dvc exp show</span> 再把它們排成一張表（<span class="kbd">--only-changed</span>
    讓表只留有變動的欄位，不然沒動的參數會塞滿畫面）。
    試錯的過程不會弄髒 git 歷史；覺得某一組值得留下來，
    <span class="kbd">dvc exp branch &lt;實驗名&gt;</span> 把它變成真正的分支。
  </p>
  <a class="golab" href="__NB__" target="_blank" rel="noopener">到 notebook 的 4️⃣ 與 6️⃣ 節：diff 與 dvc exp</a>
</section>

<section id="s7">
  <span class="eyebrow">07 · 遠端</span>
  <h2>同事 clone 完之後，資料從哪來</h2>
  <p>
    到這裡為止，資料都只在你這台機器的 <span class="kbd">.dvc/cache</span> 裡。
    同事把 repo clone 下來只會拿到指標檔——這就是 <b>remote</b> 的工作：一個放「內容」的地方。
    它可以是 S3、GCS、Azure、SSH、HTTP，<b>也可以只是一個資料夾</b>（NAS、共用磁碟機都算）。
    對 DVC 來說差別只有那一行網址：
  </p>
  <div class="codeblock">dvc remote add -d storage s3://my-bucket/dvcstore
dvc remote add -d storage gs://my-bucket/dvcstore
dvc remote add -d storage ssh://user@host/path
dvc remote add -d storage /mnt/nas/dvcstore   # 本課用這種，看得見裡面

$ dvc push
5 files pushed</div>
  <p>
    <span class="kbd">-d</span> 是 default 的意思，設定寫進 <span class="kbd">.dvc/config</span>——
    <b>這個檔會進 git</b>，所以團隊裡每個人 clone 完自動吃到同一個遠端。
    打開遠端資料夾看，裡面是跟 cache 一模一樣的
    <span class="kbd">files/md5/46/4179a42e1b28…</span> 結構：<b>遠端就是 cache 的另一份拷貝</b>，
    沒有資料庫、沒有中繼服務。換成 S3 的話，這些就是 bucket 裡的 object key。
  </p>
  <p>
    notebook 接著把 <span class="kbd">.dvc/cache</span> 與所有資料檔<b>整個刪掉</b>，
    模擬「同事剛 clone 完」的狀態，然後：
  </p>
  <div class="codeblock">$ dvc pull
A       data/raw.csv
A       data/test.csv
A       data/train.csv
A       model.pkl
5 files fetched and 4 files added</div>
  <p>
    資料與模型都回來了。所以<b>新同事的完整流程就是三行</b>：
    <span class="kbd">git clone</span> → <span class="kbd">cd</span> → <span class="kbd">dvc pull</span>。
    沒有「請找 Alice 要那份 CSV」，也沒有 <span class="kbd">raw_final_v2_真的最終版.csv</span>。
    <b>但這也代表一件事</b>：<span class="kbd">git push</span> 之後別忘了 <span class="kbd">dvc push</span>——
    只推指標檔不推內容，對方 pull 下來只會拿到一句「檔案不在本機也不在遠端」。
  </p>
  <a class="golab" href="__NB__" target="_blank" rel="noopener">到 notebook 的 7️⃣ 節：push、刪光、pull 回來</a>
</section>

<section id="s8">
  <span class="eyebrow">08 · 分工</span>
  <h2>那 MLflow 呢？兩個一起用，接點只有一行</h2>
  <p>
    這個主題的第 1、2 課你用 MLflow 記過訓練。DVC 跟 MLflow <b>不是二選一</b>——它們管的是不同的東西：
  </p>
  <table class="cmp">
    <tr><th></th><th>DVC</th><th>MLflow</th></tr>
    <tr><td>管什麼</td><td class="b">檔案的版本、管線的可重現</td><td class="o">實驗的紀錄、模型的註冊</td></tr>
    <tr><td>綁在哪</td><td class="b">git commit</td><td class="o">run id</td></tr>
    <tr><td>典型問題</td><td>「上個月那版資料在哪？」「這步要不要重跑？」</td><td>「哪一次跑的 AUC 最高？當時參數是什麼？」</td></tr>
    <tr><td>存什麼</td><td>資料、模型檔、中間產物（內容定址）</td><td>params、metrics、artifacts、模型版本與 alias</td></tr>
    <tr><td>誰在用</td><td>整個團隊共用一份資料</td><td>每個人的每一次訓練</td></tr>
  </table>
  <div class="codeblock">md5 = yaml.safe_load(open("data/raw.csv.dvc"))["outs"][0]["md5"]

with mlflow.start_run():
    mlflow.log_param("data_md5", md5)                 # 用了哪一份資料
    mlflow.log_param("git_commit", git_short_sha())   # 用了哪一版程式
    mlflow.log_metric("auc", metrics["auc"])</div>
  <p>
    就這一行。半年後看到某個 run，你可以 <span class="kbd">git checkout &lt;git_commit&gt;</span> 拿回當時的程式與指標檔、
    <span class="kbd">dvc checkout</span> 拿回當時的資料、<span class="kbd">dvc repro</span> 重跑一次——
    而且因為 md5 對得上，你會拿到<b>一模一樣</b>的模型。
    <b>這就是「可重現」的完整定義</b>：程式、資料、參數、產物四樣都能指名道姓，少一樣都做不到。
  </p>
  <a class="golab" href="__NB__" target="_blank" rel="noopener">到 notebook 的 8️⃣ 節：把 md5 記進 MLflow run</a>
</section>

<section id="s9">
  <span class="eyebrow">09 · 實戰</span>
  <h2>換你動手</h2>
  <p>
    notebook 的 9️⃣ 節有一個小工具：選一種改動、按下去，它會先把工作區還原、套用改動、真的執行一次
    <span class="kbd">dvc repro</span>。<b>按之前先自己猜</b>：哪些 stage 會重跑、哪些會 skip？
    猜完再看三個挑戰：
  </p>
  <div class="ex">
    <span class="lv">LEVEL 1</span>
    <p>把 <span class="kbd">n_estimators</span> 從 50 改成 200，用 <span class="kbd">dvc params diff</span> 與 <span class="kbd">dvc metrics diff</span> 看多花的時間換到多少 AUC。進階：<b>加一個全新的參數</b> <span class="kbd">min_samples_leaf</span>——想清楚要改幾個地方，少改一個會怎樣。</p>
  </div>
  <div class="ex">
    <span class="lv">LEVEL 2</span>
    <p>加第三個 stage <span class="kbd">evaluate</span>：讀 <span class="kbd">model.pkl</span> 與 <span class="kbd">data/test.csv</span>，把 ROC 曲線寫成 <span class="kbd">plots/roc.csv</span>，並在 <span class="kbd">dvc.yaml</span> 用 <span class="kbd">plots:</span> 宣告它。跑完看 <span class="kbd">dvc dag</span> 多了什麼、<span class="kbd">dvc plots show</span> 產出什麼。</p>
  </div>
  <div class="ex">
    <span class="lv">LEVEL 3</span>
    <p>不用自己 clone，直接從別人的 repo 拿一份 DVC 管的資料：研究 <span class="kbd">dvc get</span> 與 <span class="kbd">dvc import</span> 的差別，說明什麼情況該用哪一個，並找出 <span class="kbd">import</span> 產生的檔案裡「記住來源版本」的是哪一個欄位。</p>
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
      <h3>團隊的 repo 裡有一個 800 MB 的訓練資料檔，已經 commit 進 git 半年了，現在 clone 一次要十分鐘。你要怎麼收拾？</h3>
      <div class="quiz-opts">
        <button type="button" class="quiz-opt" data-k="A">A. 把檔案刪掉再 commit 一次，repo 就會瘦回來</button>
        <button type="button" class="quiz-opt" data-k="B">B. 把資料搬到共用磁碟機，README 寫清楚路徑，不要進版本控制</button>
        <button type="button" class="quiz-opt" data-k="C">C. <code>git rm -r --cached</code> 把它從 git 追蹤中移除並 commit，然後 <code>dvc init</code>、<code>dvc add</code>、設一個遠端 <code>dvc push</code>——git 只留 89 bytes 的指標檔</button>
        <button type="button" class="quiz-opt" data-k="D">D. 用 gzip 壓縮後再 commit，順便把歷史上的舊版本壓縮一遍</button>
      </div>
      <div class="quiz-fb" aria-live="polite"><p>A 是最常見的誤解：<b>git 的歷史不會縮小</b>——刪掉只是新增一個「這個檔不見了」的 commit，那 800 MB 還是躺在每個人的 <code>.git</code> 裡（要真的移除得改寫歷史，全團隊重新 clone）。所以 C 的第一步 <code>git rm -r --cached</code> 只是「別再往前疊」，它解決的是未來；而把資料交給 DVC 之後，往後每一版資料在 git 裡都只有一行 md5 的差異。B 確實讓 repo 變小，但也把版本資訊整個丟掉了——半年後沒人答得出「當時那個模型是用哪一版資料訓的」，而這正是這堂課要解決的問題。D 壓縮救不了：CSV 壓完還是幾百 MB，而且壓縮後的二進位每改一格就整個變一份，git 反而更存不動。</p></div>
    </div>

    <div class="quiz-q" data-answer="B">
      <p class="quiz-tag">Q2 <span class="qtype dx">錯誤診斷</span></p>
      <h3>你在一個既有專案裡第一次跑 <span class="kbd">dvc add</span>，得到這個錯誤。最直接的修法是？</h3>
      <div class="codeblock">$ dvc add data/raw.csv
ERROR:  output 'data/raw.csv' is already tracked by SCM (e.g. Git).
    You can remove it from Git, then add to DVC.
        To stop tracking from Git:
            git rm -r --cached 'data/raw.csv'
            git commit -m "stop tracking data/raw.csv"</div>
      <div class="quiz-opts">
        <button type="button" class="quiz-opt" data-k="A">A. 先 <code>dvc init --force</code> 重新初始化，DVC 的設定壞掉了</button>
        <button type="button" class="quiz-opt" data-k="B">B. 照訊息做：<code>git rm -r --cached 'data/raw.csv'</code> 並 commit，把它從 git 的追蹤名單移除，再 <code>dvc add</code> 一次</button>
        <button type="button" class="quiz-opt" data-k="C">C. 手動在 <code>.gitignore</code> 加一行 <code>data/raw.csv</code>，git 就不會管它了</button>
        <button type="button" class="quiz-opt" data-k="D">D. 用 <code>dvc add --force</code> 蓋過去</button>
      </div>
      <div class="quiz-fb" aria-live="polite"><p>DVC 擋下來是有道理的：<b>同一個檔不能同時被 git 和 DVC 追蹤</b>，兩邊都想決定「這個檔該長什麼樣」，一 checkout 就打架。訊息本身已經把解法印出來了——<code>git rm -r --cached</code> 只把它從 git 的索引移除，<b>檔案本身不會被刪</b>（少了 <code>--cached</code> 才會真的刪檔，這是要看清楚的一個字）。C 是很多人的第一反應，但 <code>.gitignore</code> 對<b>已經被追蹤</b>的檔案無效——git 只用它來決定要不要追蹤「新」檔案，所以錯誤照樣出現。A 跟這個錯誤完全無關，DVC 的設定好好的。D 的 <code>--force</code> 在這裡繞不過去，因為衝突在 git 那邊不在 DVC 這邊。</p></div>
    </div>

    <div class="quiz-q" data-answer="D">
      <p class="quiz-tag">Q3 <span class="qtype">情境題</span></p>
      <h3>同事照著 README 做「重現三個月前那次實驗」：<code>git checkout v1.2</code> 之後 <code>python train.py</code>，AUC 卻跟當時記錄的 0.953 差很多。過程中沒有任何錯誤訊息、沒有例外。第一件該做的事是？</h3>
      <div class="quiz-opts">
        <button type="button" class="quiz-opt" data-k="A">A. 檢查 sklearn 版本，一定是套件升級改了預設值</button>
        <button type="button" class="quiz-opt" data-k="B">B. 把 <code>random_state</code> 拿掉多跑幾次取平均，單次結果本來就會晃</button>
        <button type="button" class="quiz-opt" data-k="C">C. 回報這個 tag 標錯了，請當初的人重新確認 commit</button>
        <button type="button" class="quiz-opt" data-k="D">D. 跑 <code>dvc status</code>：多半是只做了 <code>git checkout</code>、忘了 <code>dvc checkout</code>，資料還停在最新版</button>
      </div>
      <div class="quiz-fb" aria-live="polite"><p>「沒有錯誤訊息但數字對不上」是這個坑的招牌症狀。<code>git checkout</code> 只換了指標檔，<code>data/raw.csv</code> 仍然是最新那一份——<b>而 git 不會警告你，因為它根本不知道有這個檔</b>（它被寫在 <code>data/.gitignore</code> 裡）。唯一會講話的是 <code>dvc status</code>，它會印 <code>modified: data/raw.csv</code>；接著 <code>dvc checkout</code> 就從 cache 還原了。A 值得懷疑但排在後面：如果是套件升級，通常整組指標一起變，而且 <code>dvc.lock</code> 已經釘住了資料與參數，先排除便宜的可能性再說。B 是把問題掩蓋掉——本課的訓練有固定 <code>random_state</code>，同樣輸入就該有同樣輸出，「取平均」只會讓你永遠查不出根因。C 沒有根據，tag 指的 commit 本來就對，錯的是「工作區只回去了一半」。</p></div>
    </div>

    <div class="quiz-q" data-answer="A">
      <p class="quiz-tag">Q4 <span class="qtype dx">錯誤診斷</span></p>
      <h3>你把新版資料 commit 完 <code>git push</code>，同事 clone 下來跑 <code>dvc pull</code> 拿到這個。原因與修法是？</h3>
      <div class="codeblock">$ dvc pull
Everything is up to date.
WARNING: Some of the cache files do not exist neither locally nor on remote. Missing cache files:
md5: 65eea634c19580aa1c6fec509f4a181f
ERROR: failed to pull data from the cloud - Checkout failed for following targets:
data/raw.csv
Is your cache up to date?
&lt;https://error.dvc.org/missing-files&gt;</div>
      <div class="quiz-opts">
        <button type="button" class="quiz-opt" data-k="A">A. 你只做了 <code>git push</code>：指標檔上去了、內容還在你的 <code>.dvc/cache</code> 裡——你要補一次 <code>dvc push</code></button>
        <button type="button" class="quiz-opt" data-k="B">B. 同事的 <code>.dvc/config</code> 沒設遠端，請他自己 <code>dvc remote add -d</code> 一個</button>
        <button type="button" class="quiz-opt" data-k="C">C. 指標檔的 md5 算錯了，重新 <code>dvc add</code> 一次再 commit</button>
        <button type="button" class="quiz-opt" data-k="D">D. 同事忘了 <code>dvc checkout</code>，先 checkout 再 pull</button>
      </div>
      <div class="quiz-fb" aria-live="polite"><p>訊息直接說了：「這些 cache 檔在本機和遠端都不存在」，然後指名缺的那個 md5。git 與 DVC 是兩條各自獨立的推送管道——<code>git push</code> 送走的是指標檔與 <code>dvc.lock</code>，<b>460 MB 的內容要靠 <code>dvc push</code> 才會上遠端</b>。把 <code>dvc push</code> 加進你的收工習慣（或做成 pre-push hook / CI 的一步）就不會再犯。B 症狀不符：真的沒設遠端時錯誤是 <code>config file error: no remote specified</code>，而且遠端設定寫在會進 git 的 <code>.dvc/config</code> 裡，同事 clone 完就有了。C 沒有根據——md5 是算出來的不會「算錯」，重新 add 只會產生一模一樣的指標檔。D 順序反了也沒用：<code>dvc checkout</code> 是從<b>本機 cache</b> 還原，同事的 cache 裡根本沒有這份內容。</p></div>
    </div>

    <div class="quiz-q" data-answer="B">
      <p class="quiz-tag">Q5 <span class="qtype">情境題</span></p>
      <h3>你要試 12 組 <code>max_depth</code>，最後只留最好的那一組。前面 4 個 stage（下載、清洗、特徵、切分）跑一輪要 20 分鐘，訓練只要 2 秒。最有效率、又不會弄髒 git 歷史的做法是？</h3>
      <div class="quiz-opts">
        <button type="button" class="quiz-opt" data-k="A">A. 開 12 個 git 分支，每個分支改一次 <code>params.yaml</code> 再 <code>dvc repro</code>，最後 merge 贏的那個</button>
        <button type="button" class="quiz-opt" data-k="B">B. 先 <code>dvc repro</code> 一次讓前 4 個 stage 進 cache，再跑 12 次 <code>dvc exp run --set-param train.max_depth=...</code>，用 <code>dvc exp show</code> 比較，最後 <code>dvc exp branch</code> 留下贏的那個</button>
        <button type="button" class="quiz-opt" data-k="C">C. 寫一個 for 迴圈直接呼叫 <code>train.py</code> 12 次，把結果印出來自己挑</button>
        <button type="button" class="quiz-opt" data-k="D">D. 每試一組就 <code>git commit</code> 一次，之後用 <code>git log</code> 配合 <code>dvc metrics diff</code> 回頭比較</button>
      </div>
      <div class="quiz-fb" aria-live="polite"><p>兩件事同時成立才是好答案。<b>效率</b>：<code>max_depth</code> 只是 <code>train</code> 這一個 stage 的參數，前 4 個 stage 的依賴完全沒變，DVC 會一路印 <code>didn't change, skipping</code>——20 分鐘只付一次，之後每組只花 2 秒。<b>乾淨</b>：<code>dvc exp run</code> 把每次結果存成掛在 git 上的實驗而不是 commit，<code>dvc exp show</code> 一張表比完，只有贏家用 <code>dvc exp branch</code> 變成真正的分支。A 能動但 12 個分支的管理成本遠高於 12 個實驗，而且 merge 一堆 <code>dvc.lock</code> 是自找麻煩。C 最快但把管線繞過去了：這 12 次跑用的是哪一版資料、哪一版特徵程式，沒有任何紀錄，最後你會有一堆對不上來源的數字。D 弄髒歷史，而且 <code>metrics diff</code> 一次只比兩個版本，12 組要比 11 次。</p></div>
    </div>

    <div class="quiz-score" data-score></div>
  </div>
</section>

<div class="endnav">
  <a href="/ml-testing/">
    <span class="tag">下一課</span>
    <b>ML 測試：用 pytest 幫模型寫行為測試 →</b>
  </a>
  <a href="/mlops/">
    <span class="tag">主題</span>
    <b>‹ 回「MLOps 自動化技術」課程列表</b>
  </a>
</div>
'''

SCRIPT = r"""
/* ═══ hero：資料的時光機 ═══
   四個 commit 與所有 md5／檔案大小／終端機輸出，全部來自 notebook 的實測
   （DVC 3.67.1；資料＝make_classification 2000 列 12 特徵 random_state=0）。 */
(function () {
  const COMMITS = [
    {
      id: "v1",
      msg: "2000 列訓練資料",
      git:
        "data/raw.csv.dvc  89 B\n" +
        "  outs:\n" +
        "  - md5: <em>84450654…</em>\n" +
        "    size: 470591\n" +
        "    path: raw.csv\n" +
        "data/.gitignore\n" +
        "  /raw.csv\n" +
        ".dvc/config\n" +
        ".dvcignore",
      cache: "files/md5/<em>84/450654…</em>\n\n共 1 份內容\n460 KB 的 CSV 本體",
      ws: "data/raw.csv 2000 列\n  第 0 列 label = 0\n\n.git 目錄  232 KB",
      say:
        "git 裡<b>沒有那份 CSV</b>，只有 89 bytes 的指標檔加一行 <code>.gitignore</code>。" +
        "資料本體躺在 cache 裡，檔名就是它自己的 md5。",
    },
    {
      id: "v2",
      msg: "修掉一筆錯標的資料",
      git:
        "data/raw.csv.dvc  89 B\n" +
        "  outs:\n" +
        "  - md5: <em>464179a4…</em>\n" +
        "      <i>↑ 只有這行變</i>\n" +
        "    size: 470591\n" +
        "      （大小一樣）\n" +
        "    path: raw.csv",
      cache:
        "files/md5/84/450654…\n" +
        "files/md5/<em>46/4179a4…</em>\n\n" +
        "共 2 份內容\n舊的沒被蓋掉",
      ws: "data/raw.csv 2000 列\n  第 0 列 label = 1\n\n資料沒進 git，\n.git 幾乎沒變大",
      say:
        "2000 列裡只改了一格，<code>git diff</code> 就是<b>一行 md5</b>。" +
        "舊那份還在 cache，所以 <code>git checkout</code> ＋ <code>dvc checkout</code> 隨時回得去。",
    },
    {
      id: "v3",
      msg: "建立訓練管線 max_depth=4",
      git:
        "data/raw.csv.dvc\n" +
        "params.yaml\n" +
        "  max_depth: 4\n" +
        "train.py\n" +
        "dvc.yaml\n" +
        "dvc.lock  <i>← 執行收據</i>\n" +
        "  metrics <em>f3cba656…</em>\n" +
        "  model   <em>a60efcb3…</em>\n" +
        ".gitignore\n" +
        "  /model.pkl\n" +
        "  /metrics.json",
      cache:
        "84/450654… v1 資料\n" +
        "46/4179a4… v2 資料\n" +
        "<em>a6/0efcb3…</em> model.pkl\n" +
        "           130,864 B\n" +
        "<em>f3/cba656…</em> metrics\n\n" +
        "共 4 份內容",
      ws:
        'model.pkl  130,864 B\nmetrics.json\n  {"auc": <i>0.95318</i>,\n   "n_rows": 2000}',
      say:
        "模型檔也交給 DVC 了——<b>課名的「模型」那一半就是這樣做的</b>。" +
        "git 多的是 <code>dvc.lock</code>：把資料、程式、參數、產物的 md5 全部釘在一起。",
    },
    {
      id: "v4",
      msg: "調參 max_depth 4 → 12",
      git:
        "params.yaml\n" +
        "  max_depth: <em>12</em> <i>← 一行</i>\n" +
        "dvc.lock\n" +
        "  data/raw.csv\n" +
        "    464179a4…（沒變）\n" +
        "  max_depth: 12\n" +
        "  metrics <em>10c755a9…</em>\n" +
        "  model   <em>9cb77611…</em>",
      cache:
        "84/450654… 46/4179a4…\n" +
        "a6/0efcb3… f3/cba656…\n" +
        "<em>9c/b77611…</em> model.pkl\n" +
        "           992,931 B\n" +
        "<em>10/c755a9…</em> metrics\n\n" +
        "共 6 份內容\n.dvc/cache 2,092 KB",
      ws:
        'model.pkl  992,931 B\nmetrics.json\n  {"auc": <i>0.97287</i>,\n   "n_rows": 2000}\n\n.git 目錄  348 KB',
      say:
        "只改了參數，<b>資料一個 byte 都沒被複製</b>（md5 沒變，DVC 認得出是同一份）。" +
        "四個版本跑完，<code>.git</code> 還是 348 KB。",
    },
  ];

  const REPROS = [
    {
      k: "什麼都不改",
      lines: [
        ["dim", "'data/raw.csv.dvc' didn't change, skipping"],
        ["skip", "Stage 'prepare' didn't change, skipping"],
        ["skip", "Stage 'train' didn't change, skipping"],
        ["dim", "Data and pipelines are up to date."],
      ],
      tally: "0 個 stage 重跑，1.4 秒。<b>dvc repro 不是「重跑」，是「檢查有沒有必要跑」。</b>",
    },
    {
      k: "改 params.yaml",
      lines: [
        ["dim", "'data/raw.csv.dvc' didn't change, skipping"],
        ["skip", "Stage 'prepare' didn't change, skipping"],
        ["run", "Running stage 'train':"],
        ["dim", "> python train.py"],
        ["dim", "auc = 0.95318"],
      ],
      tally: "1 個 stage 重跑，2.9 秒。切分資料那步的依賴沒變，DVC 沒有理由重做。",
    },
    {
      k: "改 data/raw.csv",
      lines: [
        ["dim", "'data/raw.csv.dvc' didn't change, skipping"],
        ["run", "Running stage 'prepare':"],
        ["dim", "> python prepare.py"],
        ["dim", "prepare: 2200 列 -> train 1650 / test 550"],
        ["run", "Running stage 'train':"],
        ["dim", "> python train.py"],
        ["dim", "auc = 0.94527"],
      ],
      tally: "2 個 stage 重跑，4.9 秒。上游的產物變了，整條下游都得重算。",
    },
    {
      k: "改回跑過的參數",
      lines: [
        ["dim", "'data/raw.csv.dvc' didn't change, skipping"],
        ["skip", "Stage 'prepare' didn't change, skipping"],
        ["skip", "Stage 'train' is cached - skipping run, checking out outputs"],
      ],
      tally: "0 個 stage 重跑：這組組合以前算過，產物直接從 cache 撈回來（run cache）。",
    },
  ];

  const rail = document.getElementById("tm-rail");
  const chips = document.getElementById("tm-chips");
  const gitEl = document.getElementById("tm-git");
  const cacheEl = document.getElementById("tm-cache");
  const wsEl = document.getElementById("tm-ws");
  const sayEl = document.getElementById("tm-say");
  const outEl = document.getElementById("tm-out");
  const tallyEl = document.getElementById("tm-tally");

  function showCommit(i) {
    const c = COMMITS[i];
    gitEl.innerHTML = c.git;
    cacheEl.innerHTML = c.cache;
    wsEl.innerHTML = c.ws;
    sayEl.innerHTML = c.say;
    rail.querySelectorAll("button").forEach((b, j) => b.classList.toggle("on", i === j));
  }

  function showRepro(i) {
    const r = REPROS[i];
    outEl.innerHTML =
      '<span class="dim">$ dvc repro</span>\n' +
      r.lines.map((l) => '<span class="' + l[0] + '">' + l[1] + "</span>").join("\n");
    tallyEl.innerHTML = r.tally;
    chips.querySelectorAll("button").forEach((b, j) => b.classList.toggle("on", i === j));
  }

  COMMITS.forEach((c, i) => {
    const b = document.createElement("button");
    b.type = "button";
    b.innerHTML = "<b>" + c.id + "</b><span>" + c.msg + "</span>";
    b.addEventListener("click", () => showCommit(i));
    rail.appendChild(b);
  });
  REPROS.forEach((r, i) => {
    const b = document.createElement("button");
    b.type = "button";
    b.textContent = r.k;
    b.addEventListener("click", () => showRepro(i));
    chips.appendChild(b);
  });

  showCommit(0);
  showRepro(1);
})();
"""

PANEL_STEPS = """
        <li>登入 molab（GitHub / Google）</li>
        <li>開啟課程 notebook，<b>Fork 成自己的副本</b>即可編輯</li>
        <li>從第一格往下全部執行（首次安裝套件約 1–2 分鐘）——<b>免費 CPU 環境即可</b>，不需要 GPU；整份跑完約 40–60 秒，所有檔案都寫在暫存資料夾裡</li>
"""
