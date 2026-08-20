"""課程頁內容區（純常數）。改完跑：python .claude/skills/make-lesson/scripts/page-fill.py content/llm-apps/rag-zh
build.sh 不會部署這個檔；它是 index.html 內容區的正本。"""

TITLE = "RAG：讓模型先翻手冊再回答"
DESCRIPTION = "用一份繁體中文店務手冊走完 RAG 每一步：切段、qwen3-embedding 向量化、Qdrant 檢索、提示詞生成，7 題評測量化「沒 RAG 瞎掰 vs 有 RAG 全對」，並學會讓模型說「手冊裡沒有寫」。"
NB = "https://molab.marimo.io/github/skmygo/agentclass/blob/main/content/llm-apps/rag-zh/rag-zh_ext.py"

STYLE = r"""
  /* 語義色：紅＝沒有 RAG（幻覺）、綠＝有 RAG、藍＝檢索到的段落、橘＝提示詞 */
  :root { --c1: #4C72B0; --c2: #DD8452; --c3: #55A868; --cut: #C44E52; }
  a.golab { text-decoration: none; display: inline-flex; align-items: center; gap: 8px; }

  /* hero：問客服 */
  #rg-demo .qs { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 10px; }
  #rg-demo .qs button { font: inherit; font-size: 13px; padding: 6px 12px; border: 1.5px solid var(--ink); border-radius: 999px; background: var(--panel); cursor: pointer; font-weight: 700; }
  #rg-demo .qs button.active { background: var(--ink); color: #fff; }
  #rg-demo .sw { display: flex; align-items: center; gap: 10px; font-size: 13.5px; font-weight: 800; margin-bottom: 10px; }
  #rg-demo .sw .tog { position: relative; width: 48px; height: 26px; border-radius: 999px; background: var(--cut); border: 2px solid var(--ink); cursor: pointer; transition: background .2s; }
  #rg-demo .sw .tog::after { content: ""; position: absolute; top: 2px; left: 2px; width: 18px; height: 18px; border-radius: 50%; background: #fff; transition: left .2s; }
  #rg-demo .sw .tog.on { background: var(--c3); } #rg-demo .sw .tog.on::after { left: 24px; }
  #rg-demo .ctx { display: flex; gap: 6px; flex-wrap: wrap; min-height: 26px; margin-bottom: 8px; }
  #rg-demo .ctx span { font-size: 12px; font-family: var(--mono); background: var(--chip-bg); border: 1.5px solid var(--c1); color: var(--c1); border-radius: 6px; padding: 2px 8px; }
  #rg-demo .ans { border: 2px solid var(--cut); border-radius: 12px; padding: 12px 14px; font-size: 14px; line-height: 1.7; min-height: 54px; transition: border-color .2s; }
  #rg-demo .ans.ok { border-color: var(--c3); }
  #rg-demo .ans .who { font-size: 11.5px; font-weight: 800; letter-spacing: .05em; margin-bottom: 4px; color: var(--cut); }
  #rg-demo .ans.ok .who { color: var(--c3); }

  table.cmp { width: 100%; border-collapse: collapse; font-size: 13.5px; margin: 14px 0; }
  table.cmp th, table.cmp td { border-bottom: 1px solid var(--grid); padding: 8px 10px; text-align: left; vertical-align: top; }
  table.cmp th { font-size: 12px; letter-spacing: .04em; color: var(--ink-soft); }
  .kbd { font-family: var(--mono); background: var(--chip-bg); padding: 1px 6px; border-radius: 5px; font-size: 13px; }
"""

WRAP = r"""
<section id="hero">
  <span class="eyebrow">RAG · RETRIEVAL-AUGMENTED GENERATION · 繁體中文</span>
  <h1>RAG：讓模型<br>先翻手冊再回答</h1>
  <p style="margin-top:18px">
    LLM 什麼都懂一點，唯獨<b>不懂你的資料</b>。問它你店裡的 Wi-Fi 密碼，它不會說不知道——
    它會<b>自信地編一個</b>。RAG 的解法很樸素：回答前先從你的資料找出最相關的幾段，貼進提示詞，
    再請模型只根據這些回答。下面是一間虛構的貓咪咖啡廳，切換開關看差別（內容是 notebook 的實測紀錄）：
  </p>

  <div class="hero-demo" id="rg-demo">
    <div class="qs" id="rg-qs"></div>
    <div class="sw"><span>RAG</span><div class="tog" id="rg-tog" role="switch" aria-checked="false" tabindex="0"></div><span id="rg-state">關——模型只靠自己</span></div>
    <div class="ctx" id="rg-ctx"></div>
    <div class="ans" id="rg-ans"></div>
  </div>

  <p class="note">
    資料是一份十小節的繁體中文店務手冊；向量用第 1 課 gateway 的 <span class="kbd">qwen3-embedding-0.6b</span>，
    索引用上一課的記憶體 Qdrant，生成用 <span class="kbd">nemotron-3.5-lightning</span>。notebook 從切段到評測每一步都量化。
  </p>
</section>

<section id="s1">
  <span class="eyebrow">01 · 問題與切段</span>
  <h2>先看它怎麼瞎掰，再決定怎麼切</h2>
  <p>
    notebook 第一格就問「Wi-Fi 密碼是多少？」——模型會給一個煞有介事的密碼（實測拿過 <span class="kbd">sakura2024</span>、
    <span class="kbd">camelliahouse</span>），問「哪隻貓最怕生」要嘛發明一隻叫「豆漿」的貓、要嘛打太極說每隻貓都有個性。
    這不是模型壞，是它<b>沒有你的資料</b>。
  </p>
  <p>
    RAG 的第一個設計決策是<b>怎麼切</b>：切太大帶進無關內容，切太小失去上下文。
    這份手冊結構乾淨，用最自然的切法——一個 <span class="kbd">##</span> 小標＝一段，切出 10 段、每段 59–91 字：
  </p>
  <div class="codeblock">def chunk_by_heading(text):
    chunks = []
    for block in text.split("\n## ")[1:]:            # [0] 是 # 大標，不算一段
        lines = [ln.strip() for ln in block.strip().splitlines()]
        chunks.append({"title": lines[0], "text": "## " + "\n".join(lines)})
    return chunks</div>
  <a class="golab" href="__NB__" target="_blank" rel="noopener">到 notebook 的 1️⃣–2️⃣ 節：瞎掰現場、切段</a>
</section>

<section id="s2">
  <span class="eyebrow">02 · 向量化、入庫、檢索</span>
  <h2>十段變十個向量，問題也走同一條路</h2>
  <p>
    十段文字<b>一次 API 呼叫</b>批次變成 1024 維向量（<span class="kbd">input</span> 給整個 list），
    存進記憶體 Qdrant，payload 放原文與標題——檢索回來要貼進提示詞的是<b>文字</b>，向量只是索引。
    問題也經過<b>同一個</b> embedding 模型變向量，問 Qdrant 最近的 <span class="kbd">top_k</span> 段。
  </p>
  <p>
    看 score 的<b>落差</b>：「哪一隻貓最怕生？」命中「店貓介紹：煤球」0.53，但另兩隻貓的段落也有 0.51——
    三段都在講貓，檢索分不太開，<b>靠模型讀內文判斷</b>；「Wi-Fi 密碼」則是 0.70 對 0.31，一段獨大。
    notebook 有輸入框與 <span class="kbd">top_k</span> 拉桿，多試幾個問題感受分數的意義。
  </p>
  <a class="golab" href="__NB__" target="_blank" rel="noopener">到 notebook 的 3️⃣–4️⃣ 節：入庫、互動檢索</a>
</section>

<section id="s3">
  <span class="eyebrow">03 · 生成</span>
  <h2>三條規矩，少一條都不行</h2>
  <div class="codeblock">SYSTEM_RAG = (
    "你是山茶屋貓咪咖啡廳的店員。只能根據下面的「參考資料」回答顧客問題，"
    "資料裡沒有的就說「手冊裡沒有寫」，不要編造。用繁體中文簡短回答。\n\n參考資料：\n{context}"
)
context = "\n\n".join(f"[{i+1}] {h.payload['text']}" for i, h in enumerate(hits))</div>
  <p>
    <b>只根據參考資料</b>、<b>沒有就說沒寫</b>、<b>不要編造</b>——少了它們，模型會把參考資料和自己的想像混著講。
    notebook 的 <span class="kbd">answer(question, use_rag=True/False)</span> 一個開關切換兩種模式，
    並排顯示同一題的兩個回答。
  </p>
  <a class="golab" href="__NB__" target="_blank" rel="noopener">到 notebook 的 5️⃣ 節：提示詞、並排對照</a>
</section>

<section id="s4">
  <span class="eyebrow">04 · 評測與邊界</span>
  <h2>數字說話，以及「會說不知道」才是好 RAG</h2>
  <p>
    一個例子不算證據。7 題有標準答案的問題，每題用一個關鍵字判斷答對與否，兩種模式各跑一輪。實測多次：
    <b>沒 RAG 只矇對 0–2 題</b>（例如「可以帶狗嗎」偶爾猜中「禁止」），<b>有 RAG 7 題全對</b>。
    這種關鍵字命中是最陽春的評測，但它便宜、客觀——每次動了切段、<span class="kbd">top_k</span>、提示詞，都該重跑。
  </p>
  <table class="cmp">
    <tr><th>問題</th><th>沒 RAG（實測節錄）</th><th>有 RAG</th></tr>
    <tr><td>Wi-Fi 密碼是多少？</td><td>❌ 山茶屋的 Wi-Fi 密碼是：sakura2024</td><td>✅ meow2026</td></tr>
    <tr><td>山茶屋週日幾點打烊？</td><td>❌ 週日 18:00 打烊</td><td>✅ 21:00</td></tr>
    <tr><td>領養一隻貓要多少錢？</td><td>❌ 約新臺幣 2,000~5,000 元，已包含疫苗…</td><td>✅ 1500 元</td></tr>
    <tr><td>你們有賣牛排嗎？（手冊沒有）</td><td>沒有販售牛排（矇對，但無從分辨是知道還是猜）</td><td>✅ 手冊裡沒有寫（檢索分數全部 &lt; 0.4）</td></tr>
  </table>
  <p>
    最後一列是 RAG 最被低估的價值：檢索永遠會回最近的幾段（哪怕都不相關），
    但提示詞的規矩讓模型老實說沒寫，而不是拿不相關的段落硬湊。
  </p>
  <a class="golab" href="__NB__" target="_blank" rel="noopener">到 notebook 的 6️⃣–7️⃣ 節：評測表、長條圖、範圍外問題</a>
</section>

<section id="s5">
  <span class="eyebrow">05 · 實戰</span>
  <h2>換你動手</h2>
  <div class="ex">
    <span class="lv">LEVEL 1</span>
    <p><span class="kbd">top_k</span> 改 1 再跑評測——哪一題最先出錯、為什麼？改 5 會不會因雜訊變差？</p>
  </div>
  <div class="ex">
    <span class="lv">LEVEL 2</span>
    <p>在手冊加一個新小節（例如「外送服務」），不改其他程式重跑——新知識立刻可用，這是 RAG 相對微調的最大優勢。</p>
  </div>
  <div class="ex">
    <span class="lv">LEVEL 3</span>
    <p>刪掉「手冊裡沒有寫」那句看牛排問題怎麼答；再加一個分數門檻，top-1 太低就不送模型。用評測找出不誤殺的門檻。</p>
  </div>
</section>

<div class="endnav">
  <a href="/rag-mcp-agent/">
    <span class="tag">下一課（壓軸）</span>
    <b>RAG 變成 AI 的工具：LiteLLM × FastMCP × Qdrant →</b>
  </a>
  <a href="/llm-apps/">
    <span class="tag">主題</span>
    <b>‹ 回「學 LLM 應用開發」課程列表</b>
  </a>
</div>
"""

SCRIPT = r"""
/* ═══ hero 互動：問客服（純 JS；回答與分數是 notebook 的實測紀錄）═══ */
(function () {
  const QA = [
    { q: "Wi-Fi 密碼是多少？", plain: "山茶屋的 Wi-Fi 密碼是：sakura2024，歡迎使用！", rag: "CamelliaCat，密碼是 meow2026。", ctx: ["Wi-Fi 0.70", "會員制度 0.31", "店貓介紹：奶蓋 0.26"] },
    { q: "哪一隻貓最怕生？", plain: "每隻貓都有自己的性格，歡迎您來山茶屋認識他們！（打太極——它根本不知道店裡有哪些貓）", rag: "最怕生的貓是煤球。", ctx: ["店貓介紹：煤球 0.53", "店貓介紹：麻糬 0.51", "店貓介紹：奶蓋 0.51"] },
    { q: "領養一隻貓要多少錢？", plain: "領養費用視貓貓年齡與健康狀況而定，通常約新臺幣 2,000~5,000 元，已包含疫苗及體檢費用。", rag: "認養費用為 1500 元。", ctx: ["貓咪領養 0.72", "特殊活動 0.53", "店貓介紹：煤球 0.47"] },
    { q: "你們有賣牛排嗎？", plain: "很抱歉，我們目前沒有販售牛排，主要提供飲料與點心。（這題它矇對了——但你無從分辨它是知道還是在猜）", rag: "手冊裡沒有寫。", ctx: ["店貓介紹：麻糬 0.37", "店貓介紹：奶蓋 0.35", "入場規定 0.32"] },
  ];
  const qs = document.getElementById("rg-qs"), tog = document.getElementById("rg-tog"), state = document.getElementById("rg-state");
  const ctx = document.getElementById("rg-ctx"), ans = document.getElementById("rg-ans");
  let cur = 0, on = false;
  QA.forEach((x, i) => { const b = document.createElement("button"); b.textContent = x.q; b.className = i === 0 ? "active" : ""; b.addEventListener("click", () => { cur = i; qs.querySelectorAll("button").forEach((y, j) => y.classList.toggle("active", j === i)); render(); }); qs.appendChild(b); });
  function render() {
    const x = QA[cur];
    tog.classList.toggle("on", on); tog.setAttribute("aria-checked", on);
    state.textContent = on ? "開——先檢索，再只根據資料回答" : "關——模型只靠自己";
    ctx.innerHTML = on ? x.ctx.map(c => `<span>${c}</span>`).join("") : `<span style="border-color:var(--grid);color:var(--ink-soft)">（沒有檢索）</span>`;
    ans.className = "ans" + (on ? " ok" : "");
    ans.innerHTML = `<div class="who">${on ? "有 RAG · 店員" : "沒有 RAG · 店員"}</div>${on ? x.rag : x.plain}`;
  }
  const flip = () => { on = !on; render(); };
  tog.addEventListener("click", flip);
  tog.addEventListener("keydown", e => { if (e.key === " " || e.key === "Enter") { e.preventDefault(); flip(); } });
  render();
})();
"""

PANEL_STEPS = """
        <li>登入 molab（GitHub / Google）</li>
        <li>開啟課程 notebook，<b>Fork 成自己的副本</b>即可編輯</li>
        <li>從第一格往下全部執行（首次安裝套件約 1 分鐘）——<b>免費 CPU 環境即可</b>，不需要 GPU</li>
"""
