"""課程頁內容區（純常數）。改完跑：python3 .claude/skills/make-lesson/scripts/page-fill.py content/genai-intro/genai-agent-sdk
build.sh 不會部署這個檔；它是 index.html 內容區的正本。
SCRIPT 裡 HERO_TRACES 那一段由 _spikes/spike_genai_agent_sdk_payload.py 產生（實測錄影），不要手改。"""

TITLE = "Claude Agent SDK：把 Claude Code 裝進你的程式"
DESCRIPTION = (
    "進階補充 C：用 claude-agent-sdk 把同一個修 bug 任務真的跑六次、只改權限設定——看 SDK 替你做掉的迴圈、"
    "工具與 context，以及你剩下唯一要做的事：設邊界。含 hooks、can_use_tool、自訂工具、子代理、session，"
    "與接本機開源模型的免費跑法（全部是實測錄影）。"
)

STYLE = r"""
  /* 語義色：藍＝你的程式／設定、橘＝模型、綠＝工具結果／放行、紫＝你的守門員（hook／審批函式）、紅＝被擋／錯誤 */
  :root { --c1: #4C72B0; --c2: #DD8452; --c3: #55A868; --c4: #8172B2; --cut: #C44E52; }

  .tldr { border-left: 4px solid var(--tc, var(--c1)); background: var(--chip-bg);
    border-radius: 0 10px 10px 0; padding: 10px 14px; margin: 12px 0 16px;
    font-size: 14.5px; line-height: 1.7; }
  .tldr b { color: var(--tc, var(--c1)); }
  .kbd { font-family: var(--mono); background: var(--chip-bg); padding: 1px 6px; border-radius: 5px; font-size: 13px; }
  .src { font-size: 12.5px; color: var(--ink-soft); }

  /* hero：同一任務、三種設定的錄影播放器 */
  #sdk-demo .tabs { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 10px; }
  #sdk-demo .tab { font: inherit; font-size: 13px; font-weight: 700; color: var(--ink);
    background: var(--panel); border: 2px solid var(--grid); border-radius: 999px;
    padding: 5px 13px; cursor: pointer; }
  #sdk-demo .tab.on { border-color: var(--c1); background: var(--chip-bg); color: var(--c1); }
  #sdk-demo .opts { font-family: var(--mono); font-size: 12px; line-height: 1.55; white-space: pre-wrap;
    word-break: break-word; background: var(--chip-bg); border-left: 4px solid var(--c1);
    border-radius: 0 8px 8px 0; padding: 8px 12px; margin: 0 0 10px; }
  #sdk-demo .stage { border: 2px solid var(--ink); border-radius: 12px; padding: 8px 10px;
    min-height: 160px; max-height: 430px; overflow-y: auto; }
  #sdk-demo .bub { border: 2px solid var(--bc); border-radius: 10px; padding: 5px 10px; margin: 6px 0; }
  #sdk-demo .bub.fresh { animation: sdkup .22s ease; }
  #sdk-demo .bub .who { font-size: 10.5px; font-weight: 800; letter-spacing: .04em; color: var(--bc); }
  #sdk-demo .bub .txt { font-size: 13px; line-height: 1.6; white-space: pre-wrap; word-break: break-word; }
  #sdk-demo .bub .txt.mono { font-family: var(--mono); font-size: 12px; }
  @keyframes sdkup { from { opacity: 0; transform: translateY(5px); } to { opacity: 1; transform: none; } }
  @media (prefers-reduced-motion: reduce) { #sdk-demo .bub.fresh { animation: none; } }
  #sdk-demo .ctrl { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; margin-top: 10px; }
  #sdk-demo .btn { font: inherit; font-size: 13.5px; font-weight: 800; border-radius: 10px;
    padding: 6px 14px; cursor: pointer; border: 2px solid var(--c1); }
  #sdk-demo .btn.go { color: #fff; background: var(--c1); }
  #sdk-demo .btn.alt { color: var(--ink); background: var(--panel); border-color: var(--grid); }
  #sdk-demo .btn:disabled { opacity: .4; cursor: default; }
  #sdk-demo .pos { font-family: var(--mono); font-size: 12px; color: var(--ink-soft); }
  #sdk-demo .outcome { margin-top: 10px; border: 2px solid var(--oc, var(--ink)); border-radius: 10px;
    padding: 7px 12px; font-size: 13.5px; font-weight: 700; color: var(--oc, var(--ink)); }

  .tw { overflow-x: auto; }
  table.cmp { width: 100%; border-collapse: collapse; font-size: 13.5px; margin: 14px 0; }
  table.cmp th, table.cmp td { border-bottom: 1px solid var(--grid); padding: 7px 9px; text-align: left; vertical-align: top; }
  table.cmp th { font-size: 12px; letter-spacing: .04em; color: var(--ink-soft); }
  table.cmp td.n { font-family: var(--mono); font-weight: 800; white-space: nowrap; }

  ol.gates { margin: 10px 0 14px; padding-left: 1.4em; line-height: 1.75; font-size: 14.5px; }
  ol.gates b { color: var(--c4); }

  table.cheat { width: 100%; border-collapse: collapse; font-size: 14px; margin: 14px 0; }
  table.cheat td { border-bottom: 1px solid var(--grid); padding: 9px 11px; vertical-align: top; line-height: 1.7; }
  table.cheat td.t { font-weight: 800; width: 12em; }
"""

WRAP = r'''
<section id="hero">
  <span class="eyebrow">GENAI 進階補充 · C · CLAUDE AGENT SDK</span>
  <h1>Claude Agent SDK：<br>把 Claude Code 裝進你的程式</h1>
  <p style="margin-top:18px">
    主線<a href="/genai-agents/">第 5 課</a>你看過 agent 迴圈的骨架：模型吐一段 JSON、你的程式執行工具、
    結果塞回對話，再問一次。Claude Agent SDK 把這個迴圈——連同 Claude Code 整套的讀檔、改檔、跑指令工具、
    context 管理、權限與 hooks——包成一個 Python 函式 <span class="kbd">query()</span>。
    你不用再寫迴圈；<b>剩下的工作只有一件：設邊界</b>。
  </p>
  <p>
    下面是同一個任務（「測試沒過，找出 bug、修好、跑測試確認」）、同一個模型，
    <b>只改一行設定</b>的三次真實錄影。按「下一步」一則一則播：
  </p>

  <div class="hero-demo" id="sdk-demo">
    <div class="tabs" id="sdk-tabs"></div>
    <div class="opts" id="sdk-opts"></div>
    <div class="stage" id="sdk-stage"></div>
    <div class="ctrl">
      <button type="button" class="btn go" id="sdk-next">下一步 ▸</button>
      <button type="button" class="btn alt" id="sdk-all">播到底</button>
      <button type="button" class="btn alt" id="sdk-reset">重播</button>
      <span class="pos" id="sdk-pos"></span>
    </div>
    <div class="outcome" id="sdk-out" hidden></div>
    <div class="src" style="margin-top:8px">
      實測紀錄：claude-haiku-4-5，claude-agent-sdk 0.2.159（內含 Claude Code 2.1.281），2026-09-24。
      每次都從全新的專案複本開始；「測試結果」是跑完後我們自己再跑一次 unittest 的真實狀態，不是模型的自述。
    </div>
  </div>

  <p class="note">
    實驗場是真的 Python（在你的瀏覽器裡跑，不用安裝任何東西、不需要任何帳號或金鑰）。
    首次載入約需 30–60 秒，正好夠你讀完第 1 節。裡面有六種設定的完整錄影、一台權限閘門模擬器、
    一台帳單計算機——選單、滑桿、開關隨便玩。
  </p>
</section>

<section id="s1">
  <span class="eyebrow">01 · 從迴圈到 HARNESS</span>
  <h2>SDK 替你做掉的事</h2>
  <div class="tldr" style="--tc:var(--c1)">
    <b>一句話重點</b>：Agent SDK ＝把 Claude Code 當函式庫用。迴圈、內建工具、context、權限、hooks、
    子代理、session 全部內建（這整套叫 <b>harness</b>，馬具）；你給的是 prompt 和一份
    <span class="kbd">ClaudeAgentOptions</span>。
  </div>
  <p>
    主線第 5 課手寫的是最小迴圈；本站 <a href="/litellm-tools/">LLM 應用開發系列</a>把它寫成能跑的程式。
    同一件事交給 SDK，分工變成這樣：
  </p>
  <div class="tw"><table class="cmp">
    <tr><th>工作</th><th>手寫 tool loop</th><th>Agent SDK</th></tr>
    <tr><td>迴圈</td><td>自己寫 <span class="kbd">while</span>、自己判斷何時停</td>
        <td><span class="kbd">query()</span> 直接吐出一串訊息，停在 <span class="kbd">ResultMessage</span></td></tr>
    <tr><td>工具</td><td>每個都自己寫 schema、自己執行</td>
        <td>內建 Read／Edit／Write／Bash／WebSearch／WebFetch／Agent…（這次錄影的清單有 29 個）</td></tr>
    <tr><td>context</td><td>自己管 messages、自己算長度</td>
        <td>自動重送、自動開 prompt caching，快滿時自動壓縮（有 <span class="kbd">PreCompact</span> hook 可接）</td></tr>
    <tr><td>權限</td><td>自己寫 if</td>
        <td><span class="kbd">permission_mode</span>、<span class="kbd">allowed_tools</span>、<span class="kbd">disallowed_tools</span>、<span class="kbd">can_use_tool</span></td></tr>
    <tr><td>攔截與稽核</td><td>自己包一層</td><td>hooks：<span class="kbd">PreToolUse</span>、<span class="kbd">PostToolUse</span>、<span class="kbd">Stop</span>…</td></tr>
    <tr><td>帳單</td><td>自己加總 usage</td><td><span class="kbd">ResultMessage</span> 給你 <span class="kbd">num_turns</span>、<span class="kbd">total_cost_usd</span>、逐模型的 <span class="kbd">model_usage</span></td></tr>
  </table></div>
  <p>整支 agent 程式就這麼短（參考程式，不在課內執行；需要 <span class="kbd">pip install claude-agent-sdk</span> 與 API key）：</p>
  <div class="codeblock">import asyncio
from claude_agent_sdk import (query, ClaudeAgentOptions,
                              AssistantMessage, ToolUseBlock, ResultMessage)

async def main():
    options = ClaudeAgentOptions(
        model="claude-haiku-4-5",
        cwd="shop-demo",                         # agent 在哪個資料夾工作
        allowed_tools=["Read", "Edit", "Bash"],  # 這三個工具不用問、直接放行
    )
    async for msg in query(prompt="測試沒過，找出 bug、修好、跑測試確認。", options=options):
        if isinstance(msg, AssistantMessage):
            for block in msg.content:
                if isinstance(block, ToolUseBlock):
                    print("→", block.name, block.input)       # 模型要求的工具呼叫
        elif isinstance(msg, ResultMessage):
            print(msg.subtype, msg.num_turns, msg.total_cost_usd)

asyncio.run(main())</div>
  <p>
    <span class="kbd">query()</span> 吐出來的訊息串，就是 hero 播放器裡那一則一則的卡片：
    <span class="kbd">SystemMessage(init)</span>（這次有哪些工具、什麼模式）→
    <span class="kbd">AssistantMessage</span>（模型說的話 <span class="kbd">TextBlock</span>、要求的呼叫
    <span class="kbd">ToolUseBlock</span>）→ <span class="kbd">UserMessage</span>（工具結果
    <span class="kbd">ToolResultBlock</span>）→ …… → <span class="kbd">ResultMessage</span>（帳單）。
    執行工具、把結果塞回去、再問模型——主線第 5 課你手寫的那幾行，全在 SDK 裡面。
  </p>
  <p>
    兩個預設值要知道：<b>system prompt 預設是空的</b>（SDK 啟動 Claude Code 時傳
    <span class="kbd">--system-prompt ""</span>；要 Claude Code 完整的行為準則，寫
    <span class="kbd">system_prompt={"type": "preset", "preset": "claude_code"}</span>）；
    <b><span class="kbd">setting_sources</span> 預設會載入你電腦上的設定</b>（<span class="kbd">~/.claude</span>、
    專案的 <span class="kbd">CLAUDE.md</span>）。錄影時我們一律設 <span class="kbd">setting_sources=[]</span>，
    讓結果只反映程式本身——正式上線時也建議這樣做，不然換一台機器行為就變。
  </p>
  <button class="golab" data-nb="1️⃣">到實驗場 1️⃣ 看六種設定的完整錄影</button>
</section>

<section id="s2">
  <span class="eyebrow">02 · 權限</span>
  <h2>六道閘門：誰說了算</h2>
  <div class="tldr" style="--tc:var(--c4)">
    <b>一句話重點</b>：模型每要求一次工具，SDK 依固定順序過六道閘門，第一個做出決定的說了算——
    <b>hooks → deny 規則 → ask 規則 → 權限模式 → allow 規則 → can_use_tool</b>。
  </div>
  <ol class="gates">
    <li><b>Hooks</b>：你的 <span class="kbd">PreToolUse</span> 函式最先執行，可以直接擋（hook 的「放行」不會跳過後面的規則）。</li>
    <li><b>deny 規則</b>：<span class="kbd">disallowed_tools</span>。裸名稱（<span class="kbd">"Bash"</span>）乾脆把工具從清單拿掉；有範圍的（<span class="kbd">"Bash(rm *)"</span>）在這裡擋。</li>
    <li><b>ask 規則</b>：settings.json 才能設，符合的一律送去問 <span class="kbd">can_use_tool</span>。</li>
    <li><b>權限模式</b>：<span class="kbd">permission_mode</span>（下表）。</li>
    <li><b>allow 規則</b>：<span class="kbd">allowed_tools</span>。另外，工作目錄內讀檔、<span class="kbd">find</span>／<span class="kbd">ls</span> 這類唯讀指令本來就免審。</li>
    <li><b>can_use_tool</b>：前面都沒決定的，才來問你的函式；沒設函式就沒人可問——拒絕。</li>
  </ol>
  <div class="tw"><table class="cmp">
    <tr><th>permission_mode</th><th>行為（官方文件，2026-09 查證）</th></tr>
    <tr><td class="n">default</td><td>模式本身不放行任何東西；需要核准又沒被 allow 規則放行的，送去問 can_use_tool</td></tr>
    <tr><td class="n">acceptEdits</td><td>工作目錄內的改檔，以及 mkdir／touch／rm／mv／cp／sed 自動放行</td></tr>
    <tr><td class="n">plan</td><td>只看、只規劃：改檔一律送審，連 allow 規則都不算</td></tr>
    <tr><td class="n">dontAsk</td><td>不問人：沒被規則放行的一律拒絕，can_use_tool 永遠不會被叫</td></tr>
    <tr><td class="n">bypassPermissions</td><td>全部放行——但 hooks、deny、ask 規則排在它前面，照樣擋得住</td></tr>
    <tr><td class="n">auto</td><td>由一個模型分類器決定放行或拒絕（可用性見官方文件）</td></tr>
  </table></div>
  <p>錄影裡實際撞到的三件反直覺的事：</p>
  <p>
    <b>① headless 預設＝能看不能動。</b>錄影①什麼都沒設：<span class="kbd">Read</span> 和 <span class="kbd">find</span>
    直接跑，改檔卻被拒——「Claude requested permissions to write to ~/shop-demo/shop/cart.py, but you haven't granted it yet.」
    因為沒有人可以按「允許」。模型最後只能把修法用文字告訴你，測試照樣是紅的——<b>而 <span class="kbd">subtype</span> 仍是 <span class="kbd">success</span></b>。
  </p>
  <p>
    <b>② <span class="kbd">allowed_tools</span> 是放行清單，不是限制清單。</b>設
    <span class="kbd">bypassPermissions</span> 再把 <span class="kbd">allowed_tools</span> 只寫 <span class="kbd">["Read"]</span>，
    Bash 照樣執行（實測：<span class="kbd">python3 -c "print(6*7)"</span> 輸出 42）。沒列到的工具掉到權限模式，
    bypass 一律放行。
  </p>
  <p>
    <b>③ deny 規則和 hook 連 bypass 都擋得住。</b>同樣是 <span class="kbd">bypassPermissions</span>，
    加上 <span class="kbd">disallowed_tools=["Bash(rm *)"]</span>，<span class="kbd">rm -rf build</span> 被擋下：
    「Permission to use Bash with command rm -rf build &amp;&amp; echo "清理完成" has been denied.」——它們排在權限模式前面。
  </p>
  <button class="golab" data-nb="2️⃣">到實驗場 2️⃣ 用模擬器找出是哪一道閘門擋的</button>
</section>

<section id="s3">
  <span class="eyebrow">03 · 你的程式當守門員</span>
  <h2>hooks 與 can_use_tool</h2>
  <div class="tldr" style="--tc:var(--c4)">
    <b>一句話重點</b>：<b>hook</b> 在每一次工具呼叫前都會跑（第一道閘門），適合護欄與稽核；
    <b>can_use_tool</b> 只在「沒有規則放行、需要問人」時才被叫（最後一道），適合人工審批。
  </div>
  <p>錄影③的 hook：一個記錄每次呼叫，一個規定 Bash 只准跑 unittest（參考程式）：</p>
  <div class="codeblock">async def bash_guard(input_data, tool_use_id, context):
    cmd = input_data["tool_input"].get("command", "")
    if not cmd.strip().startswith("python3 -m unittest"):
        return {"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": "這個專案只准用 `python3 -m unittest` 跑測試；其他 shell 指令一律擋下。",
        }}
    return {}          # 回空物件＝不插手

options = ClaudeAgentOptions(
    allowed_tools=["Read", "Edit", "Bash"],
    hooks={"PreToolUse": [HookMatcher(matcher=None, hooks=[audit]),        # 每次呼叫都記一筆
                          HookMatcher(matcher="Bash", hooks=[bash_guard])]},
)</div>
  <p>
    錄影裡它擋了三次：兩個 <span class="kbd">find</span>、一個 <span class="kbd">ls -la</span>——模型只是想<b>找檔案</b>。
    原因：在 Linux／macOS 上 Claude Code 預設不給 Glob、Grep 工具，搜尋走 Bash 的
    <span class="kbd">find</span>／<span class="kbd">grep</span>，所以照樣經過你的 Bash 護欄。
    擋下的理由會回給模型：它讀到之後改用 <span class="kbd">Read</span> 讀檔、用
    <span class="kbd">python3 -m unittest discover -v</span> 跑測試，最後照樣修好。
  </p>
  <p>錄影⑤換成審批函式：</p>
  <div class="codeblock">async def approver(tool_name, tool_input, context):
    path = str(tool_input.get("file_path", ""))
    if tool_name in ("Edit", "Write") and "/shop/" in path:
        return PermissionResultAllow()
    return PermissionResultDeny(message="使用者拒絕：這次只准修改 shop/ 底下的程式碼，不准執行任何指令。")

options = ClaudeAgentOptions(can_use_tool=approver)</div>
  <p>
    函式被問了兩次：一次 <span class="kbd">python -m pytest</span>（拒絕）、一次改 <span class="kbd">shop/cart.py</span>（放行）；
    <span class="kbd">Read</span> 一次都沒來問——它在第⑤道就放行了。
    <b>陷阱</b>：同時設 <span class="kbd">allowed_tools=["Bash"]</span> 和 <span class="kbd">can_use_tool</span>，
    Bash 在第⑤道就被放行，你的函式永遠不會被叫到；SDK 會警告你（實測原文見測驗第 4 題）。
    要「每一次都檢查」，用 hook。
  </p>
  <p>
    <b>plan 模式要配審批函式。</b>錄影④只設了 <span class="kbd">permission_mode="plan"</span>：
    沒接 <span class="kbd">can_use_tool</span> 時，init 的工具清單裡根本沒有 <span class="kbd">ExitPlanMode</span>
    （29 個；接了函式的⑤⑥是 32 個，多了 <span class="kbd">AskUserQuestion</span>、<span class="kbd">EnterPlanMode</span>、
    <span class="kbd">ExitPlanMode</span>）。模型寫好計畫卻交不出去，四處找工具、兩度嘗試改檔被擋，
    <b>繞了 22 輪、花了 $0.198</b>，檔案一個字沒改——plan 模式確實守住了「不動手」，但流程卡死。
    錄影⑥加上審批函式：模型呼叫 <span class="kbd">ExitPlanMode</span> 交出計畫 → 函式核准 → 改檔 → 測試全過，14 輪、$0.107。
  </p>
  <button class="golab" data-nb="1️⃣">到實驗場 1️⃣ 對照④和⑥兩段錄影</button>
</section>

<section id="s4">
  <span class="eyebrow">04 · 帳單與記憶</span>
  <h2>ResultMessage 與 session</h2>
  <div class="tldr" style="--tc:var(--c1)">
    <b>一句話重點</b>：<span class="kbd">ResultMessage</span> 是整趟的收據（輪數、時間、token、花費、被擋清單）；
    <span class="kbd">subtype="success"</span> 只代表迴圈正常結束，<b>不代表任務完成</b>。
  </div>
  <p>
    六段錄影的 <span class="kbd">subtype</span> 全是 <span class="kbd">success</span>，包括檔案一個字沒改的①④。
    判斷有沒有做成要看 <span class="kbd">permission_denials</span>（①有 4 筆），再自己驗證——跑測試、看 diff。
    要設上限：<span class="kbd">max_turns</span> 用完會得到 <span class="kbd">subtype="error_max_turns"</span>
    （實測只給 2 輪：<span class="kbd">errors=["Reached maximum number of turns (2)"]</span>），
    <span class="kbd">max_budget_usd</span> 超過則是 <span class="kbd">error_max_budget_usd</span>。
  </p>
  <p>
    花費的大頭是 context。錄影②的第一次 API 呼叫就送出約 1.46 萬個 token——幾乎全是 29 個工具的說明書；
    之後每一輪重送全部歷史（主線第 5 課的「上下文帳」），但 Claude Code 自動開了 prompt caching：
    整趟送出約 17 萬個輸入 token，其中 16.2 萬是便宜的 <span class="kbd">cache_read</span>（牌價的 0.1 倍）、
    8,504 個是寫入快取（2 倍），完全沒快取的只有 82 個。整趟 $0.0495，用 Haiku 4.5 牌價自己重算對得上。
  </p>
  <p>
    <b>記憶在 session，不在模型。</b>第一次跟它說「專案代號是藍鯨」，拿到 <span class="kbd">ResultMessage.session_id</span>；
    第二次 <span class="kbd">resume=session_id</span> 問「代號是什麼」→「藍鯨」。第三次不帶 resume，它不知道——
    兩次錄影一次回「shop-demo」（拿資料夾名稱瞎猜）、一次回「找不到明確的專案代號」。
    resume 一個不存在的 session 會直接丟例外：「No conversation found with session ID: …」。
  </p>
  <button class="golab" data-nb="3️⃣">到實驗場 3️⃣ 看每一輪的 token 帳，換模型重算</button>
</section>

<section id="s5">
  <span class="eyebrow">05 · 擴充</span>
  <h2>自訂工具、子代理</h2>
  <div class="tldr" style="--tc:var(--c2)">
    <b>一句話重點</b>：<span class="kbd">@tool</span>＋<span class="kbd">create_sdk_mcp_server</span> 把 Python 函式變成工具
    （同一個行程裡的 MCP server，不用另外架伺服器）；<span class="kbd">AgentDefinition</span> 定義專職的子代理。
  </div>
  <div class="codeblock">from claude_agent_sdk import tool, create_sdk_mcp_server

@tool("lookup_order", "查詢訂單狀態。輸入訂單編號（例如 A1023），回傳出貨狀態、物流商與預計到貨日。",
      {"order_id": str})
async def lookup_order(args):
    oid = args["order_id"].strip().upper()
    if oid in ORDERS:
        return {"content": [{"type": "text", "text": json.dumps(ORDERS[oid], ensure_ascii=False)}]}
    return {"content": [{"type": "text", "text": f"查無訂單 {oid}"}], "is_error": True}

shop = create_sdk_mcp_server(name="shop", version="1.0.0", tools=[lookup_order])
options = ClaudeAgentOptions(
    tools=[],                                   # 不給任何內建工具
    mcp_servers={"shop": shop},
    allowed_tools=["mcp__shop__lookup_order"],  # 名字會變成 mcp__伺服器__工具
)</div>
  <p>
    問「A1023 和 B77 的狀態」：模型呼叫兩次 <span class="kbd">mcp__shop__lookup_order</span>，B77 拿到
    <span class="kbd">is_error</span> 的「查無訂單」照樣接得住，3 輪、$0.0058——因為
    <span class="kbd">tools=[]</span> 拿掉了內建工具，第一次呼叫只有 1,339 個 token。
    （訂單資料是教學用的假資料；MCP 協定本身的細節在<a href="/genai-mcp-fastmcp/">補充 D</a>。）
  </p>
  <div class="codeblock">options = ClaudeAgentOptions(
    agents={"test-runner": AgentDefinition(
        description="執行專案的單元測試並回報哪些測試失敗。需要跑測試時使用。",
        prompt="你只負責執行 python3 -m unittest -v，列出失敗的測試……不要修改任何檔案。",
        tools=["Bash", "Read"], model="haiku")},
    allowed_tools=["Read", "Bash", "Agent"],
)</div>
  <p>
    子代理有自己乾淨的 context，只把最終報告交回主代理；它自己的呼叫在串流裡帶
    <span class="kbd">parent_tool_use_id</span>。<b>2.1.281 的坑</b>：子代理預設丟到背景跑——
    第一次錄影主代理回一句「已在後台派遣，請稍候」就結束了（<span class="kbd">ResultMessage</span> 先到）；
    prompt 寫明「等它跑完拿到結果再回答」，模型才以 <span class="kbd">run_in_background: false</span> 前景等待。
    把「怎麼做某件事」打包成可重用知識的 Skills 在<a href="/genai-skills/">補充 E</a>；
    在終端機裡用 Claude Code 開發的實務在<a href="/genai-vibecoding/">補充 F</a>。
  </p>
  <button class="golab" data-nb="4️⃣">到實驗場 4️⃣ 看自訂工具、子代理、session 的錄影</button>
</section>

<section id="s6">
  <span class="eyebrow">06 · 免費跑法</span>
  <h2>SDK 免費，模型要錢——或者換一個</h2>
  <div class="tldr" style="--tc:var(--c3)">
    <b>一句話重點</b>：<span class="kbd">claude-agent-sdk</span> 本身免費（<span class="kbd">pip install</span>），
    花錢的是背後的模型。Claude Code 講的是 Anthropic Messages API：用
    <span class="kbd">ANTHROPIC_BASE_URL</span> 把它指到任何 Anthropic 相容端點，就能接免費的開源模型。
  </div>
  <div class="tw"><table class="cmp">
    <tr><th>跑法</th><th>要錢嗎</th><th>我們驗證了什麼</th></tr>
    <tr><td>Claude API（<span class="kbd">ANTHROPIC_API_KEY</span>）</td>
        <td>按 token 計費；官方定價頁寫新帳號有少量免費試用額度</td>
        <td>本課所有 Claude 錄影（Haiku 4.5，修一次 bug 約 $0.05）</td></tr>
    <tr><td>本機 Ollama（v0.14 起有 <span class="kbd">/v1/messages</span>）</td>
        <td>免費，用自己的電腦</td>
        <td>沒在本機實測；設定照 Ollama 官方文件：<span class="kbd">ANTHROPIC_BASE_URL=http://localhost:11434</span>、
            <span class="kbd">ANTHROPIC_AUTH_TOKEN=ollama</span>，建議模型 context ≥ 32K</td></tr>
    <tr><td>Ollama Cloud 免費方案</td>
        <td>含入門額度、只能用入門模型、同時 1 個請求（ollama.com/pricing，2026-09）</td>
        <td>沒實測</td></tr>
    <tr><td>自架 vLLM（0.26.0 有 <span class="kbd">/v1/messages</span>）</td>
        <td>免費，用自己的 GPU</td>
        <td>✅ 實測 <span class="kbd">qwen3.5-2b</span>：見下文與實驗場 5️⃣</td></tr>
  </table></div>
  <p>
    我們把同一個修 bug 任務接到 vLLM 上的 <span class="kbd">qwen3.5-2b</span>（20 億參數，context 只有 16,384）錄了三次，
    撞到的兩個錯誤就是你自己接小模型時會撞到的：
  </p>
  <p>
    <b>A. 什麼都不調</b>：Claude Code 對不認得的模型預設要 32,000 個輸出 token，伺服器直接回 500
    「max_completion_tokens=32000 cannot be greater than max_model_len…」。
    <b>B. 用 <span class="kbd">CLAUDE_CODE_MAX_OUTPUT_TOKENS=4096</span> 調小</b>：換 prompt 爆掉——
    光內建工具的說明書就「at least 12289 input tokens」。
    <b>C. 只開 3 個工具＋短 system prompt</b>：第一次呼叫降到 2,068 個 token，小模型真的讀檔、改對公式、跑測試全過
    （9 輪、約 3.5 分鐘）。A、B 兩次的 <span class="kbd">subtype</span> 也是 <span class="kbd">success</span>
    （<span class="kbd">is_error=True</span>）：錯誤被包成一句文字，不會丟例外。
  </p>
  <div class="codeblock">options = ClaudeAgentOptions(
    model="你拉下來的模型名",        # 例：Ollama 官方文章建議的 qwen3-coder、gpt-oss:20b
    env={
        "ANTHROPIC_BASE_URL": "http://localhost:11434",   # 本機 Ollama
        "ANTHROPIC_AUTH_TOKEN": "ollama",                 # 要有值，Ollama 不檢查
        "ANTHROPIC_API_KEY": "",
        "CLAUDE_CODE_MAX_OUTPUT_TOKENS": "4096",          # 預設 32000，小 context 模型會 500
    },
    tools=["Read", "Edit", "Bash"],     # 只開需要的：工具說明書越少，prompt 越小
    system_prompt="你是程式助理……先讀檔、再修改，最後用 python3 -m unittest 驗證。",
    allowed_tools=["Read", "Edit", "Bash"],
)</div>
  <p>
    接本機模型時 <span class="kbd">total_cost_usd</span> 沒有意義：錄影 C 報 $0.1306、
    <span class="kbd">costBasis</span> 寫 unknown——剛好是拿 $4／$20（Opus 5.5 的牌價）去乘 token 數算出來的，
    你真正付的是電費。完整可跑的錄製腳本在 GitHub：
    <a href="https://github.com/skmygo/agentclass/blob/main/content/genai-intro/_spikes/spike_genai_agent_sdk.py" target="_blank" rel="noopener">spike_genai_agent_sdk.py</a>
    （<span class="kbd">free</span> 段預設就指向本機 Ollama，用環境變數 <span class="kbd">FREE_BASE_URL</span>／<span class="kbd">FREE_MODEL</span> 改；
    我們實測時指向的是 vLLM）。
  </p>
  <p class="src">
    另一條規則要知道：你把 Agent SDK 做成產品給別人用時，官方要求用 API key（或 Bedrock／Vertex／Foundry）認證；
    除非事先獲准，不能讓你的使用者用 claude.ai 帳號登入、吃他們的訂閱額度（Agent SDK 官方文件，2026-09 查證）。
  </p>
  <button class="golab" data-nb="5️⃣">到實驗場 5️⃣ 看三次錄影與 prompt 大小對照</button>
</section>

<section id="s7">
  <span class="eyebrow">07 · 速查</span>
  <h2>本課速查卡</h2>
  <div class="tw"><table class="cheat">
    <tr><td class="t" style="color:var(--c1)">query() ／ ClaudeSDKClient</td>
        <td>跑一趟 agent，吐出訊息串；<span class="kbd">ClaudeSDKClient</span> 可多輪對話、中途 <span class="kbd">interrupt()</span>、改權限模式。</td></tr>
    <tr><td class="t" style="color:var(--c1)">訊息串</td>
        <td>SystemMessage(init) → AssistantMessage（TextBlock／ToolUseBlock）→ UserMessage（ToolResultBlock）→ … → ResultMessage。</td></tr>
    <tr><td class="t" style="color:var(--c4)">六道閘門</td>
        <td>hooks → deny → ask → 權限模式 → allow → can_use_tool；第一個做決定的說了算。</td></tr>
    <tr><td class="t" style="color:var(--c4)">allowed_tools ／ disallowed_tools</td>
        <td>放行清單 ／ 禁止清單。allowed_tools <b>不限制</b> bypassPermissions；要禁止用 disallowed_tools。</td></tr>
    <tr><td class="t" style="color:var(--c4)">hooks</td>
        <td>每次呼叫前（PreToolUse）／後（PostToolUse）跑你的函式；deny 連 bypass 都擋得住。</td></tr>
    <tr><td class="t" style="color:var(--c4)">can_use_tool</td>
        <td>沒被規則放行、需要問人時才叫你的函式；會被整個工具的 allow 規則遮蔽。</td></tr>
    <tr><td class="t" style="color:var(--c2)">@tool ＋ create_sdk_mcp_server</td>
        <td>Python 函式變工具，同一個行程裡的 MCP server；名字是 <span class="kbd">mcp__server__tool</span>。</td></tr>
    <tr><td class="t" style="color:var(--c2)">AgentDefinition</td>
        <td>專職子代理：自己的 prompt、工具、模型；2.1.281 起預設背景執行。</td></tr>
    <tr><td class="t" style="color:var(--c1)">ResultMessage</td>
        <td>收據：subtype、is_error、num_turns、total_cost_usd、permission_denials、session_id。success ≠ 任務完成。</td></tr>
    <tr><td class="t" style="color:var(--c3)">ANTHROPIC_BASE_URL</td>
        <td>把 harness 接到任何 Anthropic 相容端點（Ollama、vLLM）；小模型記得調輸出上限、少開工具。</td></tr>
  </table></div>
</section>

<section id="s8">
  <span class="eyebrow">08 · 實戰</span>
  <h2>換你動手</h2>
  <div class="ex">
    <span class="lv">LEVEL 1</span>
    <p>在實驗場 1️⃣ 選「③ 放行＋PreToolUse hook」播到底：hook 擋了幾次、擋的是哪些指令？明明只想管「跑什麼測試」，為什麼連找檔案都被擋？模型怎麼繞過去的？</p>
  </div>
  <div class="ex">
    <span class="lv">LEVEL 2</span>
    <p>在 2️⃣ 模擬器選「Bash：rm -rf build」＋ <span class="kbd">bypassPermissions</span>：找出兩種還擋得住它的設定，再找出一種「看起來會擋、其實擋不住」的。</p>
  </div>
  <div class="ex">
    <span class="lv">LEVEL 3</span>
    <p>幫 CI 設計一組設定：可以讀檔、可以改 <span class="kbd">shop/cart.py</span>、可以跑 <span class="kbd">python3 -m unittest</span>，但 <span class="kbd">rm -rf build</span> 一定要被擋，而且沒有人在旁邊按「允許」。用 2️⃣ 把五個呼叫逐一驗過。</p>
  </div>
  <p style="font-size:13.5px;color:var(--ink-soft);margin-top:10px">卡住了？三題在實驗場最後一格都有折疊解答——先自己做，再打開對照。</p>
  <button class="golab" data-nb="6️⃣">到實驗場 6️⃣ 看挑戰與解答</button>
</section>

<section id="quiz">
  <span class="eyebrow">09 · 驗收</span>
  <h2>情境測驗</h2>
  <p>離開前試試看：下面的情境都真的會遇到。每題選一個你認為的最佳做法，選了馬上看得到解釋。</p>
  <div data-quiz>

    <div class="quiz-q" data-answer="B">
      <p class="quiz-tag">Q1 <span class="qtype">情境題</span></p>
      <h3>你要在 CI 上讓 agent 自動修測試：可以讀檔、改程式、跑 <code>python3 -m unittest</code>，但絕對不能刪檔，而且 CI 上沒有人可以按「允許」。哪組設定最合適？</h3>
      <div class="quiz-opts">
        <button type="button" class="quiz-opt" data-k="A">A. permission_mode="bypassPermissions"，allowed_tools 只列 Read、Edit、Bash(python3 -m unittest *)</button>
        <button type="button" class="quiz-opt" data-k="B">B. permission_mode="dontAsk"，allowed_tools=["Read", "Edit", "Bash(python3 -m unittest *)"]，再加 disallowed_tools=["Bash(rm *)"]</button>
        <button type="button" class="quiz-opt" data-k="C">C. 什麼權限都不設，在 prompt 裡寫清楚「不准刪檔」</button>
        <button type="button" class="quiz-opt" data-k="D">D. permission_mode="acceptEdits"，並在 prompt 裡寫「不准刪檔」</button>
      </div>
      <div class="quiz-fb" aria-live="polite"><p><b>B</b>：dontAsk 讓「沒被規則放行的一律拒絕」，不需要有人在場；allowed_tools 精準放行三件事；disallowed_tools 的 <code>Bash(rm *)</code> 是雙保險——deny 規則排在權限模式前面，哪天有人改成 bypass 也擋得住。A 是本課實測過的陷阱：allowed_tools 是放行清單不是限制清單，bypass 底下沒列到的 Bash 照樣執行（錄影 g3）。C 的結果就是錄影①：headless 沒人按允許，改檔被拒、測試還是紅的，而且 prompt 不是護欄。D 最陰險：acceptEdits 會自動放行工作目錄內的 <code>rm</code>、<code>mv</code> 這類檔案操作，「不准刪檔」只剩一句拜託。</p></div>
    </div>

    <div class="quiz-q" data-answer="B">
      <p class="quiz-tag">Q2 <span class="qtype">情境題</span></p>
      <h3>產品需求：「agent 先交修改計畫，主管在網頁上按核准，它才可以動手改檔。」下面哪個設計做得到？</h3>
      <div class="quiz-opts">
        <button type="button" class="quiz-opt" data-k="A">A. 設 permission_mode="plan" 就好，agent 寫完計畫會自己停下來等</button>
        <button type="button" class="quiz-opt" data-k="B">B. permission_mode="plan" 加上 can_use_tool：在函式裡攔下 ExitPlanMode，把計畫送給主管審，核准才回 PermissionResultAllow；之後的改檔也經過同一個函式</button>
        <button type="button" class="quiz-opt" data-k="C">C. 用 bypassPermissions 讓它一次做完，事後再請主管看 diff</button>
        <button type="button" class="quiz-opt" data-k="D">D. 把 ExitPlanMode 放進 allowed_tools，讓計畫可以順利送出</button>
      </div>
      <div class="quiz-fb" aria-live="polite"><p><b>B</b>，這正是錄影⑥：模型呼叫 ExitPlanMode 交出計畫 → 你的函式（這裡可以換成等主管按鈕）核准 → 改檔 → 測試全過，14 輪、$0.107。A 是錄影④：沒接 can_use_tool 時工具清單裡根本沒有 ExitPlanMode，模型寫好計畫交不出去，繞了 22 輪、花了 $0.198，一個字沒改。C 把「先審後做」變成「先做後審」，需求直接不成立。D 看似合理，其實是把主管的核准步驟自動化掉——allow 規則放行的呼叫不會來問任何人。</p></div>
    </div>

    <div class="quiz-q" data-answer="C">
      <p class="quiz-tag">Q3 <span class="qtype">情境題</span></p>
      <h3>同事的 CI 腳本這樣判斷 agent 有沒有修好 bug：<code>if msg.subtype == "success": mark_green()</code>。看過本課錄影後，你會建議怎麼改？</h3>
      <div class="quiz-opts">
        <button type="button" class="quiz-opt" data-k="A">A. 改成檢查 is_error == False 就夠了</button>
        <button type="button" class="quiz-opt" data-k="B">B. 改成檢查 num_turns 大於 1，代表它真的做了事</button>
        <button type="button" class="quiz-opt" data-k="C">C. 檢查 permission_denials 是否為空，並在 agent 跑完後自己跑一次測試（或檢查 diff）當驗收</button>
        <button type="button" class="quiz-opt" data-k="D">D. 檢查 result 文字裡有沒有「測試通過」</button>
      </div>
      <div class="quiz-fb" aria-live="polite"><p><b>C</b>。<code>success</code> 只代表迴圈正常結束：錄影①的 subtype 是 success、is_error 也是 False，但被擋了 4 次（2 次跑測試、2 次改檔）、測試還是紅的。permission_denials 告訴你「它想做卻被擋的事」，而真正的驗收要看世界的狀態——我們每段錄影跑完都重跑 unittest，就是這個原因。A 不夠：①的 is_error 也是 False。B 沒意義：①跑了 10 輪。D 相信模型的自述——模型可能宣稱成功卻沒做到，驗收不能靠它自己說。</p></div>
    </div>

    <div class="quiz-q" data-answer="B">
      <p class="quiz-tag">Q4 <span class="qtype dx">錯誤診斷</span></p>
      <h3>你寫了一個審批函式，想讓每一個 Bash 指令都先經過它，結果它一次都沒被叫到、指令照樣執行。啟動時 SDK 印出這段警告（實測原文）。最可能的原因與修法？</h3>
      <div class="codeblock">options = ClaudeAgentOptions(
    allowed_tools=["Bash"],
    can_use_tool=my_approver,
)

CanUseToolShadowedWarning: can_use_tool will not be invoked for: Bash. An allowed_tools
entry that allows a whole tool auto-approves it before the callback is consulted. To gate
every tool call, use a PreToolUse hook; or narrow the entry so calls fall through to
can_use_tool. Allow rules from settings files can also shadow the callback but are not
visible here.</div>
      <div class="quiz-opts">
        <button type="button" class="quiz-opt" data-k="A">A. my_approver 必須是 async def，同步函式不會被呼叫</button>
        <button type="button" class="quiz-opt" data-k="B">B. allowed_tools 的 "Bash" 在第⑤道就把整個工具放行了，永遠輪不到第⑥道的函式；把 Bash 從 allowed_tools 拿掉（或改成 Bash(python3 -m unittest *) 這種有範圍的），要每次都檢查就改用 PreToolUse hook</button>
        <button type="button" class="quiz-opt" data-k="C">C. can_use_tool 只在 ClaudeSDKClient 裡有效，query() 不支援</button>
        <button type="button" class="quiz-opt" data-k="D">D. 要把 permission_mode 設成 bypassPermissions，函式才會被叫到</button>
      </div>
      <div class="quiz-fb" aria-live="polite"><p><b>B</b>。閘門順序是 hooks → deny → ask → 模式 → <b>allow</b> → can_use_tool：裸名稱的 allow 規則會在第⑤道放行整個工具，第⑥道的函式根本沒機會發言——這正是警告在說的事（本課錄影 g5：函式一次都沒被叫，<code>print(6*7)</code> 照樣執行）。修法二選一：縮小 allow 的範圍，讓其他呼叫掉到函式；或改用 hook，它在第一道、每次都跑。A 是對的好習慣但不是這裡的病因；C 在 0.2.159 不成立，我們實測 query() 搭配 can_use_tool 可以正常執行；D 恰好相反——bypass 會在第④道就全部放行，函式更輪不到。</p></div>
    </div>

    <div class="quiz-q" data-answer="B">
      <p class="quiz-tag">Q5 <span class="qtype dx">錯誤診斷</span></p>
      <h3>你用 ANTHROPIC_BASE_URL 把 Agent SDK 接到本機一個 context 16K 的開源模型，也照教學把 CLAUDE_CODE_MAX_OUTPUT_TOKENS 調成 4096，工具沒特別設定。ResultMessage 回來是這樣（實測原文，端點位址已遮）。下一步該怎麼做？</h3>
      <div class="codeblock">subtype='success'  is_error=True  num_turns=1
result: API Error: 500 This model's maximum context length is 16384 tokens. However, you
requested 4096 output tokens and your prompt contains at least 12289 input tokens, for a
total of at least 16385 tokens. Please reduce the length of the input prompt or the number
of requested output tokens. (parameter=input_tokens, value=12289). This is a server-side
issue, usually temporary — try again in a moment. If it persists, check your inference
gateway (&lt;你的端點&gt;).</div>
      <div class="quiz-opts">
        <button type="button" class="quiz-opt" data-k="A">A. 輸出上限還太大，再調到 1024 就好</button>
        <button type="button" class="quiz-opt" data-k="B">B. 一萬兩千多 token 幾乎都是內建工具的說明書：用 tools=["Read", "Edit", "Bash"] 只開需要的、寫一段短的 system_prompt；或換 context 至少 32K 的模型</button>
        <button type="button" class="quiz-opt" data-k="C">C. 訊息說是暫時性的伺服器問題，加上重試就會好</button>
        <button type="button" class="quiz-opt" data-k="D">D. 開源模型不支援 tool calling，只能換回 Claude</button>
      </div>
      <div class="quiz-fb" aria-live="polite"><p><b>B</b>。任務還沒開始，第一次呼叫就要 12,289 個輸入 token——使用者的 prompt 才幾十字，其餘是 20 個內建工具的說明書。本課實測：只開 3 個工具、配短 system prompt，第一次呼叫降到 2,068 token，qwen3.5-2b 真的把 bug 修好、測試全過；Ollama 官方也建議 context ≥ 32K。A 治標不治本：12,289 + 1,024 塞得下第一輪，但每一輪都重送全部歷史，幾輪之後照樣爆，還讓模型沒空間回答。C 被錯誤訊息的套話誤導：這個 500 是確定性的長度超限，重試一百次結果一樣。D 與實測相反：同一個 2B 模型在精簡設定下完成了讀檔、改檔、跑測試。另外注意 subtype 仍是 success——要看 is_error。</p></div>
    </div>

    <div class="quiz-score" data-score></div>
  </div>
</section>

<div class="endnav">
  <a href="/genai-mcp-fastmcp/">
    <span class="tag">下一課</span>
    <b>補充 D：MCP 新版協定與 FastMCP 4 →</b>
  </a>
  <a href="/genai-intro/">
    <span class="tag">主題</span>
    <b>‹ 回「生成式 AI 導論」課程列表</b>
  </a>
</div>
'''

SCRIPT = r'''
/* ═══ hero 互動：同一任務 × 三種設定的錄影播放器 ═══
   內容＝實測紀錄（claude-haiku-4-5、claude-agent-sdk 0.2.159、2026-09-24），只截短過長的輸出。 */
(function () {
  /* >>> HERO_TRACES（spike_genai_agent_sdk_payload.py 產生，勿手改）*/
  const RUNS = {"h1_default":{"label":"① 什麼都沒允許（預設）","opts":"ClaudeAgentOptions(**COMMON)","events":[{"k":"init","model":"claude-haiku-4-5","mode":"default","tools":29,"mcp":[],"agents":["claude","Explore","general-purpose","Plan","statusline-setup"]},{"k":"text","text":"我來幫你找出並修復 bug。首先讓我探索專案結構並執行測試看看問題在哪裡。","sub":false},{"k":"use","name":"Bash","input":{"command":"find ~/shop-demo -type f -name \"*.json\" -o -name \"*.js\" -o -name \"*.ts\" -o -name \"*.py\" -o -name \"*.test.*\" -o -name \"*.spec.*\" | head -20"},"sub":false},{"k":"res","err":false,"text":"~/shop-demo/tests/test_cart.py\n~/shop-demo/tests/__init__.py\n~/shop-demo/shop/__init__.py\n~/shop-demo/shop/cart.py","sub":false},{"k":"use","name":"Read","input":{"file_path":"~/shop-demo"},"sub":false},{"k":"res","err":true,"text":"EISDIR: illegal operation on a directory, read '~/shop-demo'","sub":false},{"k":"use","name":"Bash","input":{"command":"ls -la"},"sub":false},{"k":"res","err":false,"text":"total 20\ndrwxrwxr-x 5 me me 4096 Sep 24 18:09 .\ndrwxrwxr-x 3 me me 4096 Sep 24 18:09 ..\ndrwxrwxr-x 2 me me 4096 Sep 24 18:09 build\ndrwxrwxr-x 2 me me 4096 Sep 24 18:09 shop\ndrwxrwxr-x 2 me me 4096 Sep 24 18:09 tests","sub":false},{"k":"use","name":"Read","input":{"file_path":"~/shop-demo/tests/test_cart.py"},"sub":false},{"k":"res","err":false,"text":"1\timport unittest\n2\t\n3\tfrom shop.cart import subtotal, total\n4\t\n5\tITEMS = [(100, 2), (50, 1)]\n6\t\n7\t\n8\tclass TestCart(unittest.TestCase):\n9\t    def test_subtotal(self):\n10\t        self.assertEqual(subtotal(ITEMS), 250)\n11…（後略 245 字）","sub":false},{"k":"use","name":"Read","input":{"file_path":"~/shop-demo/shop/cart.py"},"sub":false},{"k":"res","err":false,"text":"1\tdef subtotal(items):\n2\t    \"\"\"items 是 (單價, 數量) 的清單，回傳小計。\"\"\"\n3\t    return sum(price * qty for price, qty in items)\n4\t\n5\t\n6\tdef total(items, coupon_pct=0):\n7\t    \"\"\"套用折扣券後的應付金額（coupon_pct=10 代表打九折），四捨五入到整數。\"\"\"\n8\t    s = …（後略 60 字）","sub":false},{"k":"use","name":"Bash","input":{"command":"python -m pytest tests/test_cart.py -v"},"sub":false},{"k":"res","err":true,"text":"This command requires approval","sub":false},{"k":"use","name":"Bash","input":{"command":"python tests/test_cart.py -v"},"sub":false},{"k":"res","err":true,"text":"This command requires approval","sub":false},{"k":"text","text":"我已經看出問題了。在 `cart.py` 中，`total` 函數的計算邏輯有誤。讓我分析一下：\n\n- 當 `coupon_pct=0`（無折扣）時，應該回傳 250，但目前計算 `round(250 * 0 / 100) = 0` ❌\n- 當 `coupon_pct=10`（打九折，即10%折扣）時，應該回傳 225（250 * 0.9），但目前計算 `round(250 * 10 / 100) = 25` ❌\n\n問題是公式缺少 `(100 - coupon_pct)` 的邏輯。讓我修正它：","sub":false},{"k":"use","name":"Edit","input":{"file_path":"~/shop-demo/shop/cart.py","old_string":"def total(items, coupon_pct=0):\n    \"\"\"套用折扣券後的應付金額（coupon_pct=10 代表打九折），四捨五入到整數。\"\"\"\n    s = subtotal(items)\n    return round(s * coupon_pct / 100)","new_string":"def total(items, coupon_pct=0):\n    \"\"\"套用折扣券後的應付金額（coupon_pct=10 代表打九折），四捨五入到整數。\"\"\"\n    s = subtotal(items)\n    return round(s * (100 - coupon_pct) / 100)"},"sub":false},{"k":"res","err":true,"text":"Claude requested permissions to write to ~/shop-demo/shop/cart.py, but you haven't granted it yet.","sub":false},{"k":"text","text":"看起來需要權限才能編輯文件。但我已經識別出問題所在。讓我嘗試修改文件：\n\n根據我的代碼分析，問題在於 `total()` 函數的計算邏輯。當 `coupon_pct=10` 時應該打九折（即 `(100-10)% = 90%`），但目前的公式 `s * coupon_pct / 100` 是錯誤的。\n\n正確的公式應該是：`s * (100 - coupon_pct) / 100`\n\n讓我寫出修正後的文件：","sub":false},{"k":"use","name":"Write","input":{"file_path":"~/shop-demo/shop/cart.py","content":"def subtotal(items):\n    \"\"\"items 是 (單價, 數量) 的清單，回傳小計。\"\"\"\n    return sum(price * qty for price, qty in items)\n\n\ndef total(items, coupon_pct=0):\n    \"\"\"套用折扣券後的應付金額（coupon_pct=10 代表打九折），四捨五入到整數。\"\"\"\n    …（後略 67 字）"},"sub":false},{"k":"res","err":true,"text":"Claude requested permissions to write to ~/shop-demo/shop/cart.py, but you haven't granted it yet.","sub":false},{"k":"text","text":"我需要權限來修改檔案。但根據代碼分析，我已經找到問題：\n\n**Bug 位置**：`shop/cart.py` 第 9 行的 `total()` 函數\n\n**問題**：公式 `s * coupon_pct / 100` 錯誤\n- 當 `coupon_pct=0` 時：應回傳 250，但目前回傳 0\n- 當 `coupon_pct=10` 時（打九折）：應回傳 225，但目前回傳 25\n\n**正確公式**：`s * (100 - coupon_pct) / 100`\n\n請允許我修改檔案以便修復 bug 並運行測試。","sub":false},{"k":"result","subtype":"success","is_error":false,"num_turns":10,"duration_ms":37343,"cost":0.0500325,"stop_reason":"end_turn","terminal_reason":"completed","errors":null,"result":"我需要權限來修改檔案。但根據代碼分析，我已經找到問題：\n\n**Bug 位置**：`shop/cart.py` 第 9 行的 `total()` 函數\n\n**問題**：公式 `s * coupon_pct / 100` 錯誤\n- 當 `coupon_pct=0` 時：應回傳 250，但目前回傳 0\n- 當 `coupon_pct=10` 時（打九折）：應回傳 225，但目前回傳 25\n\n**正確公式**：`s * (100 - coupon_pct) / 100`\n\n請允許我修改檔案以便修復 bug 並運行測試。","denials":[{"tool":"Bash","input":"python -m pytest tests/test_cart.py -v"},{"tool":"Bash","input":"python tests/test_cart.py -v"},{"tool":"Edit","input":"~/shop-demo/shop/cart.py"},{"tool":"Write","input":"~/shop-demo/shop/cart.py"}],"usage":{"input":74,"cache_read":143975,"cache_write":8382,"output":3556}}],"state":{"tests_pass":false,"tail":"FAILED (failures=2)"}},"h2_allowed":{"label":"② allowed_tools 放行","opts":"ClaudeAgentOptions(**COMMON,\n    allowed_tools=[\"Read\", \"Edit\", \"Bash\"])","events":[{"k":"init","model":"claude-haiku-4-5","mode":"default","tools":29,"mcp":[],"agents":["claude","Explore","general-purpose","Plan","statusline-setup"]},{"k":"text","text":"我來幫你找出並修復 bug。先探索一下這個專案的結構。","sub":false},{"k":"use","name":"Bash","input":{"command":"find ~/shop-demo -type f -name \"*.json\" -o -name \"*.js\" -o -name \"*.ts\" -o -name \"*.tsx\" | head -20"},"sub":false},{"k":"res","err":false,"text":"(Bash completed with no output)","sub":false},{"k":"use","name":"Bash","input":{"command":"ls -la ~/shop-demo 2>&1"},"sub":false},{"k":"res","err":false,"text":"total 20\ndrwxrwxr-x 5 me me 4096 Sep 24 18:09 .\ndrwxrwxr-x 3 me me 4096 Sep 24 18:09 ..\ndrwxrwxr-x 2 me me 4096 Sep 24 18:09 build\ndrwxrwxr-x 2 me me 4096 Sep 24 18:09 shop\ndrwxrwxr-x 2 me me 4096 Sep 24 18:09 tests","sub":false},{"k":"use","name":"Bash","input":{"command":"find ~/shop-demo -type f"},"sub":false},{"k":"res","err":false,"text":"~/shop-demo/build/tmp.txt\n~/shop-demo/tests/test_cart.py\n~/shop-demo/tests/__init__.py\n~/shop-demo/shop/__init__.py\n~/shop-demo/shop/cart.py","sub":false},{"k":"use","name":"Read","input":{"file_path":"~/shop-demo/tests/test_cart.py"},"sub":false},{"k":"res","err":false,"text":"1\timport unittest\n2\t\n3\tfrom shop.cart import subtotal, total\n4\t\n5\tITEMS = [(100, 2), (50, 1)]\n6\t\n7\t\n8\tclass TestCart(unittest.TestCase):\n9\t    def test_subtotal(self):\n10\t        self.assertEqual(subtotal(ITEMS), 250)\n11…（後略 245 字）","sub":false},{"k":"use","name":"Read","input":{"file_path":"~/shop-demo/shop/cart.py"},"sub":false},{"k":"res","err":false,"text":"1\tdef subtotal(items):\n2\t    \"\"\"items 是 (單價, 數量) 的清單，回傳小計。\"\"\"\n3\t    return sum(price * qty for price, qty in items)\n4\t\n5\t\n6\tdef total(items, coupon_pct=0):\n7\t    \"\"\"套用折扣券後的應付金額（coupon_pct=10 代表打九折），四捨五入到整數。\"\"\"\n8\t    s = …（後略 60 字）","sub":false},{"k":"use","name":"Bash","input":{"command":"python -m pytest tests/test_cart.py -v"},"sub":false},{"k":"res","err":true,"text":"Exit code 1\n~/.cache/uv/environments-v2/spike-genai-agent-sdk-0e4ce3f78c598da0/bin/python: No module named pytest","sub":false},{"k":"use","name":"Bash","input":{"command":"python -m unittest tests.test_cart -v"},"sub":false},{"k":"res","err":true,"text":"Exit code 1\ntest_coupon_10 (tests.test_cart.TestCart.test_coupon_10) ... FAIL\ntest_no_coupon (tests.test_cart.TestCart.test_no_coupon) ... FAIL\ntest_subtotal (tests.test_cart.TestCart.test_subtotal) ... ok\n\n=============…（後略 959 字）","sub":false},{"k":"text","text":"完美！我找到 bug 了。問題在 `shop/cart.py` 的第 9 行。`total()` 函數的計算邏輯不對。\n\n根據註釋，`coupon_pct=10` 代表打九折（也就是折扣 10%），但目前的公式計算的是折扣金額本身，而不是應付金額。\n\n讓我修復它：","sub":false},{"k":"use","name":"Edit","input":{"file_path":"~/shop-demo/shop/cart.py","old_string":"def total(items, coupon_pct=0):\n    \"\"\"套用折扣券後的應付金額（coupon_pct=10 代表打九折），四捨五入到整數。\"\"\"\n    s = subtotal(items)\n    return round(s * coupon_pct / 100)","new_string":"def total(items, coupon_pct=0):\n    \"\"\"套用折扣券後的應付金額（coupon_pct=10 代表打九折），四捨五入到整數。\"\"\"\n    s = subtotal(items)\n    return round(s * (100 - coupon_pct) / 100)"},"sub":false},{"k":"res","err":false,"text":"The file ~/shop-demo/shop/cart.py has been updated successfully. (file state is current in your context — no need to Read it back)","sub":false},{"k":"use","name":"Bash","input":{"command":"python -m unittest tests.test_cart -v"},"sub":false},{"k":"res","err":false,"text":"test_coupon_10 (tests.test_cart.TestCart.test_coupon_10) ... ok\ntest_no_coupon (tests.test_cart.TestCart.test_no_coupon) ... ok\ntest_subtotal (tests.test_cart.TestCart.test_subtotal) ... ok\n\n-----------------------------…（後略 67 字）","sub":false},{"k":"text","text":"✅ 全部測試通過！\n\n**修改說明（繁體中文）：**\n修正 `total()` 函數的計算公式，將 `s * coupon_pct / 100` 改為 `s * (100 - coupon_pct) / 100`，以正確計算打折後的應付金額。","sub":false},{"k":"result","subtype":"success","is_error":false,"num_turns":10,"duration_ms":33219,"cost":0.04952069999999999,"stop_reason":"end_turn","terminal_reason":"completed","errors":null,"result":"✅ 全部測試通過！\n\n**修改說明（繁體中文）：**\n修正 `total()` 函數的計算公式，將 `s * coupon_pct / 100` 改為 `s * (100 - coupon_pct) / 100`，以正確計算打折後的應付金額。","denials":[],"usage":{"input":82,"cache_read":161887,"cache_write":8504,"output":3044}}],"state":{"tests_pass":true,"tail":"OK"}},"h3_hook":{"label":"③ 放行＋PreToolUse hook","opts":"ClaudeAgentOptions(**COMMON,\n    allowed_tools=[\"Read\", \"Edit\", \"Bash\"],\n    hooks={\"PreToolUse\": [\n        HookMatcher(matcher=None, hooks=[audit]),        # 每次呼叫都記一筆\n        HookMatcher(matcher=\"Bash\", hooks=[bash_guard]),  # 只准 python3 -m unittest\n    ]})","events":[{"k":"init","model":"claude-haiku-4-5","mode":"default","tools":29,"mcp":[],"agents":["claude","Explore","general-purpose","Plan","statusline-setup"]},{"k":"text","text":"我來幫你找出並修復這個問題。首先探索專案結構並執行測試。","sub":false},{"k":"use","name":"Bash","input":{"command":"find ~/shop-demo -type f -name \"*.json\" -o -name \"*.js\" -o -name \"*.ts\" -o -name \"*.tsx\" | head -20"},"sub":false},{"k":"hook","hook":"audit","tool":"Bash","command":null,"decision":"pass","reason":null},{"k":"hook","hook":"bash_guard","tool":"Bash","command":"find ~/shop-demo -type f -name \"*.json\" -o -name \"*.js\" -o -name \"*.ts\" -o -name \"*.tsx\" | head -20","decision":"deny","reason":"這個專案只准用 `python3 -m unittest` 跑測試；其他 shell 指令一律擋下。"},{"k":"res","err":true,"text":"PreToolUse:Bash hook error: 這個專案只准用 `python3 -m unittest` 跑測試；其他 shell 指令一律擋下。","sub":false},{"k":"use","name":"Bash","input":{"command":"ls -la"},"sub":false},{"k":"hook","hook":"audit","tool":"Bash","command":null,"decision":"pass","reason":null},{"k":"hook","hook":"bash_guard","tool":"Bash","command":"ls -la","decision":"deny","reason":"這個專案只准用 `python3 -m unittest` 跑測試；其他 shell 指令一律擋下。"},{"k":"res","err":true,"text":"PreToolUse:Bash hook error: 這個專案只准用 `python3 -m unittest` 跑測試；其他 shell 指令一律擋下。","sub":false},{"k":"use","name":"Bash","input":{"command":"python3 -m unittest discover -v"},"sub":false},{"k":"hook","hook":"audit","tool":"Bash","command":null,"decision":"pass","reason":null},{"k":"hook","hook":"bash_guard","tool":"Bash","command":"python3 -m unittest discover -v","decision":"pass","reason":null},{"k":"res","err":true,"text":"Exit code 1\ntest_coupon_10 (tests.test_cart.TestCart.test_coupon_10) ... FAIL\ntest_no_coupon (tests.test_cart.TestCart.test_no_coupon) ... FAIL\ntest_subtotal (tests.test_cart.TestCart.test_subtotal) ... ok\n\n=============…（後略 959 字）","sub":false},{"k":"use","name":"Read","input":{"file_path":"~/shop-demo"},"sub":false},{"k":"hook","hook":"audit","tool":"Read","command":null,"decision":"pass","reason":null},{"k":"res","err":true,"text":"EISDIR: illegal operation on a directory, read '~/shop-demo'","sub":false},{"k":"use","name":"Bash","input":{"command":"find . -type f | head -20"},"sub":false},{"k":"hook","hook":"audit","tool":"Bash","command":null,"decision":"pass","reason":null},{"k":"hook","hook":"bash_guard","tool":"Bash","command":"find . -type f | head -20","decision":"deny","reason":"這個專案只准用 `python3 -m unittest` 跑測試；其他 shell 指令一律擋下。"},{"k":"res","err":true,"text":"PreToolUse:Bash hook error: 這個專案只准用 `python3 -m unittest` 跑測試；其他 shell 指令一律擋下。","sub":false},{"k":"use","name":"Read","input":{"file_path":"~/shop-demo/tests/test_cart.py"},"sub":false},{"k":"hook","hook":"audit","tool":"Read","command":null,"decision":"pass","reason":null},{"k":"res","err":false,"text":"1\timport unittest\n2\t\n3\tfrom shop.cart import subtotal, total\n4\t\n5\tITEMS = [(100, 2), (50, 1)]\n6\t\n7\t\n8\tclass TestCart(unittest.TestCase):\n9\t    def test_subtotal(self):\n10\t        self.assertEqual(subtotal(ITEMS), 250)\n11…（後略 245 字）","sub":false},{"k":"use","name":"Read","input":{"file_path":"~/shop-demo/shop/cart.py"},"sub":false},{"k":"hook","hook":"audit","tool":"Read","command":null,"decision":"pass","reason":null},{"k":"res","err":false,"text":"1\tdef subtotal(items):\n2\t    \"\"\"items 是 (單價, 數量) 的清單，回傳小計。\"\"\"\n3\t    return sum(price * qty for price, qty in items)\n4\t\n5\t\n6\tdef total(items, coupon_pct=0):\n7\t    \"\"\"套用折扣券後的應付金額（coupon_pct=10 代表打九折），四捨五入到整數。\"\"\"\n8\t    s = …（後略 60 字）","sub":false},{"k":"use","name":"Edit","input":{"file_path":"~/shop-demo/shop/cart.py","old_string":"def total(items, coupon_pct=0):\n    \"\"\"套用折扣券後的應付金額（coupon_pct=10 代表打九折），四捨五入到整數。\"\"\"\n    s = subtotal(items)\n    return round(s * coupon_pct / 100)","new_string":"def total(items, coupon_pct=0):\n    \"\"\"套用折扣券後的應付金額（coupon_pct=10 代表打九折），四捨五入到整數。\"\"\"\n    s = subtotal(items)\n    return round(s * (100 - coupon_pct) / 100)"},"sub":false},{"k":"hook","hook":"audit","tool":"Edit","command":null,"decision":"pass","reason":null},{"k":"res","err":false,"text":"The file ~/shop-demo/shop/cart.py has been updated successfully. (file state is current in your context — no need to Read it back)","sub":false},{"k":"use","name":"Bash","input":{"command":"python3 -m unittest discover -v"},"sub":false},{"k":"hook","hook":"audit","tool":"Bash","command":null,"decision":"pass","reason":null},{"k":"hook","hook":"bash_guard","tool":"Bash","command":"python3 -m unittest discover -v","decision":"pass","reason":null},{"k":"res","err":false,"text":"test_coupon_10 (tests.test_cart.TestCart.test_coupon_10) ... ok\ntest_no_coupon (tests.test_cart.TestCart.test_no_coupon) ... ok\ntest_subtotal (tests.test_cart.TestCart.test_subtotal) ... ok\n\n-----------------------------…（後略 67 字）","sub":false},{"k":"text","text":"完成！✅ 所有測試都通過了。\n\n**修改說明：**\n我修正了 `shop/cart.py` 中的 `total()` 函數，將計算公式從 `s * coupon_pct / 100`（只算折扣金額）改為 `s * (100 - coupon_pct) / 100`（計算實際應付金額）。","sub":false},{"k":"result","subtype":"success","is_error":false,"num_turns":10,"duration_ms":29099,"cost":0.04491439999999999,"stop_reason":"end_turn","terminal_reason":"completed","errors":null,"result":"完成！✅ 所有測試都通過了。\n\n**修改說明：**\n我修正了 `shop/cart.py` 中的 `total()` 函數，將計算公式從 `s * coupon_pct / 100`（只算折扣金額）改為 `s * (100 - coupon_pct) / 100`（計算實際應付金額）。","denials":[{"tool":"Bash","input":"find ~/shop-demo -type f -name \"*.json\" -o -name \"*.js\" -o -name \"*.ts\" -o -name \"*.tsx\" | head -20"},{"tool":"Bash","input":"ls -la"},{"tool":"Bash","input":"find . -type f | head -20"}],"usage":{"input":74,"cache_read":144134,"cache_write":7850,"output":2741}}],"state":{"tests_pass":true,"tail":"OK"}}};
  /* <<< HERO_TRACES */
  const ORDER = ["h1_default", "h2_allowed", "h3_hook"];
  const C = { model: "#DD8452", tool: "#55A868", guard: "#8172B2", bad: "#C44E52", sys: "#8a949b", ink: "#1C2B33" };
  const tabs = document.getElementById("sdk-tabs");
  const opts = document.getElementById("sdk-opts");
  const stage = document.getElementById("sdk-stage");
  const next = document.getElementById("sdk-next");
  const all = document.getElementById("sdk-all");
  const reset = document.getElementById("sdk-reset");
  const pos = document.getElementById("sdk-pos");
  const out = document.getElementById("sdk-out");
  if (!tabs || !RUNS.h1_default) return;
  let cur = ORDER[0], shown = 2, lastShown = 0;

  function esc(t) { return String(t == null ? "" : t).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;"); }
  function events(k) { return RUNS[k].events.filter((e) => !(e.k === "hook" && e.hook === "audit")); }
  function brief(name, inp) {
    if (name === "Bash") return inp.command;
    if (name === "Read") return inp.file_path;
    if (name === "Edit") return inp.file_path + "\n－ " + inp.old_string + "\n＋ " + inp.new_string;
    if (name === "Write") return inp.file_path;
    return JSON.stringify(inp);
  }
  function bub(color, who, txt, mono) {
    return `<div class="bub" style="--bc:${color}"><div class="who">${who}</div>` +
      `<div class="txt${mono ? " mono" : ""}">${esc(txt)}</div></div>`;
  }
  function card(e) {
    switch (e.k) {
      case "init": return bub(C.sys, "SystemMessage · init", `model=${e.model}　permissionMode=${e.mode}　這次給模型的工具：${e.tools} 個`);
      case "text": return bub(C.model, "模型說（TextBlock）", e.text);
      case "use": return bub(C.model, `模型要求呼叫工具（ToolUseBlock）→ ${esc(e.name)}`, brief(e.name, e.input), true);
      case "res": return bub(e.err ? C.bad : C.tool, e.err ? "被擋／出錯（ToolResultBlock, is_error）" : "工具結果（ToolResultBlock）", e.text, true);
      case "hook": return bub(C.guard, "你的 PreToolUse hook",
        (e.decision === "deny" ? "⛔ 擋下：" : "放行：") + (e.command || e.tool) + (e.reason ? "\n理由（回給模型）：" + e.reason : ""));
      case "result": return bub(C.ink, "ResultMessage",
        `subtype=${e.subtype}　num_turns=${e.num_turns}　total_cost_usd=$${e.cost.toFixed(4)}\n` +
        `permission_denials：${e.denials.length} 筆` + (e.denials.length ? "（" + e.denials.map((d) => d.tool).join("、") + "）" : ""));
      default: return "";
    }
  }
  function render() {
    const evs = events(cur);
    tabs.querySelectorAll(".tab").forEach((el) => el.classList.toggle("on", el.dataset.k === cur));
    opts.textContent = "# 三段共用的 COMMON：model=\"claude-haiku-4-5\"、cwd=專案資料夾、setting_sources=[]\n" + RUNS[cur].opts;
    stage.innerHTML = evs.slice(0, shown).map(card).join("");
    stage.querySelectorAll(".bub").forEach((el, i) => el.classList.toggle("fresh", i >= lastShown));
    lastShown = shown;
    stage.scrollTop = stage.scrollHeight;
    const done = shown >= evs.length;
    next.disabled = done;
    all.disabled = done;
    pos.textContent = `${shown} / ${evs.length} 則`;
    out.hidden = !done;
    if (done) {
      const st = RUNS[cur].state;
      out.style.setProperty("--oc", st.tests_pass ? C.tool : C.bad);
      out.textContent = (st.tests_pass ? "✅ 跑完後我們自己跑 unittest：全過（" : "❌ 跑完後我們自己跑 unittest：還是沒過（") + st.tail + "）";
    }
  }
  ORDER.forEach((k) => {
    const b = document.createElement("button");
    b.type = "button";
    b.className = "tab";
    b.dataset.k = k;
    b.textContent = RUNS[k].label;
    b.addEventListener("click", () => { cur = k; shown = 2; lastShown = 0; render(); });
    tabs.appendChild(b);
  });
  next.addEventListener("click", () => { shown = Math.min(shown + 1, events(cur).length); render(); });
  all.addEventListener("click", () => { shown = events(cur).length; render(); });
  reset.addEventListener("click", () => { shown = 2; lastShown = 0; render(); });
  render();
})();
'''
