# 工程底線：定軌、管線、WASM 限制、外部軌、驗證、部署

全部出自歷代課程的實測（早期課程可能已從 repo 移除）——
**不要假設 repo 內有現成課可以抄**，起手一律跑本 skill 的 scaffold
（`scripts/new-lesson.sh`，模板已內建所有踩坑修正）。

## 定軌：先寫程式、實測、二選一（不做兩版）

1. 核心程式先在 CPython 跑通（`uv run python` 小腳本）——教學宣稱的數字在這步驗證。
2. `node .claude/skills/make-lesson/scripts/pyodide-spike.mjs <套件...>`：
   headless Chromium 載 CDN Pyodide 真的 `micropip.install`，不靠記憶清單猜。
   （spike 的 Pyodide 版本求接近即可——marimo WASM 實際載的版本由 runtime 動態決定，
   最終把關仍是 WASM 冒煙。）
3. 定軌：
   - **全部套件裝得起＋瀏覽器算力夠 → 純瀏覽器課**（lesson.py，內嵌 notebook）。
   - **任一 FAIL／需 GPU／需真網路 → 外部軌課**（`--external`，`<id>_ext.py` 上 molab）。
     直接放棄瀏覽器版：**不要 mock 依賴鏈硬上**（實測 fastmcp：mock 掉 watchfiles
     還會撞 pydantic-core 精確 pin 對不上 Pyodide 內建版，深不見底）；
     也**不做瀏覽器迷你版**——解說寫進外部 notebook 的 md cells，讓它自成完整教材。

已知的 Pyodide 死路（spike 前可先心裡有數，但仍以 spike 為準）：
torch／unsloth／transformers（無 WASM wheel）、server 框架類（fastmcp、mcp SDK——
watchfiles 等 Rust 擴充無純 wheel）；numpy／pandas／sklearn／matplotlib 都可以。

## 管線

```
content/<topic>/_spikes/spike_*.py    # 先寫程式定軌：PEP 723 檔頭、uv run --script 可跑、不部署、進版控
bash .claude/skills/make-lesson/scripts/new-lesson.sh <id> "<課名>" <topic> "<主題名>" [--external [--gpu]]
                       # ↑ 模板複製＋代換＋CPU/GPU 二選一＋生成自檢＋root uv sync（純瀏覽器課）
→ 寫 notebook（lesson.py 或 <id>_ext.py）＋ page_content.py
→ python3 .claude/skills/make-lesson/scripts/page-fill.py content/<topic>/<id>   # 內容區填進 index.html（可重跑）
→ 驗證：外部軌 verify-ext.sh <topic> <id> [關鍵字]；純瀏覽器 marimo export html（CPython）
→ bash .claude/skills/make-lesson/scripts/smoke-all.sh --build   # build + 起 server + 全站冒煙 + 收 server
→ node .claude/skills/make-lesson/scripts/preview-shots.mjs / /<topic>/ "/<id>/@#按鈕"   # 預覽（可先點 hero）
→ npx wrangler pages deploy dist --project-name=agentclass          # 憑證見 homelab-infra skill
→ smoke-all.sh --base https://agentclass.pages.dev                   # 線上冒煙（CDN 冷資產自動重試）
→ 外部軌課另需 git push（molab 直讀 GitHub main）
```

### skill 內建工具一覽（scripts/）

| 工具 | 做什麼 | 為什麼存在（實測） |
|---|---|---|
| `new-lesson.sh` | scaffold 三件套；`--external` 預設純 CPU，`--gpu` 才留 GPU 步驟與檢查 cell | 以前要手刪 GPU `<li>` 與 cell，常漏 |
| `page-fill.py` | 把 `page_content.py` 的常數填進 index.html 的內容區，骨架自檢 | 六頁一次產時 Edit 太碎；模板註解含 `<style>` 字樣、re.sub 的 `\u` escape 都踩過 |
| `nb-outputs.py` | 印出 export 後的渲染輸出／錯誤（讀 `__marimo__/session/*.json`） | export 的 HTML 只嵌程式碼，看不到輸出 |
| `verify-ext.sh` | 從 repo 根跑 sandbox export ＋ nb-outputs 掃描，有錯 exit 1 | 背景工作 cwd 跑掉會 `Failed to spawn: marimo` 默默失敗 |
| `smoke-all.sh` | 起 dist server → 自動發現每課 smoke-test.mjs 用正確 URL 跑 → 接手機冒煙 → 收 server；`--base` 打線上 | 手動起 server／殺 server／逐課跑 URL 每輪都重做 |
| `mobile-smoke.mjs` | 390×844 逐課結構檢查＋app/edit 抽樣全載（smoke-all 自動呼叫，也可單獨跑） | 桌機冒煙測不到窄螢幕版面與 lazy load |
| `preview-shots.mjs` | 截圖；`path@selector` 先點再截；`--vp WxH` 換 viewport（手機 390x844） | hero 互動要看「按下去之後」；手機版面要能目視 |
| `pyodide-spike.mjs` | 套件裝不裝得進 Pyodide | 定軌依據 |

build.sh **自動發現**：`content/*/*/lesson.py`（純瀏覽器課：WASM 匯出、
`auto_instantiate` 後處理、698 個 assets 抽共用；互動模式讀 `lesson-mode`——
課程層 > 主題層 > 預設 `edit`，`app` 走 `--mode run`）與 `content/*/*/<id>_ext.py`
（外部軌課：只複製教學頁與 .py 原檔），並處理首頁／主題頁／shared/ 併入、404.html、
course id 重複與「一課兩版」防呆、Pages 上限檢核。`<id>_gpu.py` 是舊雙軌課的遺留尾綴
（僅隨附複製，新課不再產生）。純瀏覽器課的 Python 依賴是 **repo 根一個 uv 專案**
（一個 venv、一個 lock，全部課共用）；外部軌課用 notebook 內的 PEP 723。

## marimo / 匯出的坑

- **`export html-wasm` 會把 `auto_instantiate: false` 烙進產物**（0.23.16；export 不吃專案
  pyproject 設定）→ build.sh 已用 sed 修。**升版 marimo 必須重驗這行為**。
  `--mode run` 也一樣要修（兩種模式的產物只差 `"mode": "edit"` / `"read"` 這一個字）。
- **`--mode run`＝app 模式的全部機制**（0.23.16 實測，2026-08）：程式碼與編輯器 UI 完全
  不渲染（`.cm-editor` 數為 0），`mo.ui` 元件、圖表、`mo.md`／`mo.accordion` 照常；
  頁面只剩右上角一個 `⋯`，選單裡**只有 Download as HTML／PNG，沒有顯示程式碼、也沒有下載 .py**
  ——所以 app 模式課的「帶得走」只能靠教學頁的「下載 .py」，notebook 內文案別叫學員點右上角。
  `--show-code` 旗標在 export 產物裡不留痕跡，別靠它。
- **「全 cell `hide_code=True` ＋ edit 模式」不能取代 run 模式**（實測）：程式碼只是摺疊成
  一行灰色預覽（`prompt_tokens = mo.ui.slider(` 這種還是看得見），編輯器外框、左側工具列、
  右下執行鈕、底部狀態列全都在——畫面比 run 模式髒得多。要乾淨就用 `--mode run`。
- **run 模式下 `print()` 的輸出仍會顯示**，但沒有程式碼當上下文，讀起來像天外飛來一行字：
  app 模式課的輸出一律改用 `mo.md` 排版（表格、粗體、單位），不要留 `print` 當主要輸出。
- **marimo 版本必須全站釘同一版（`marimo==0.23.16`，repo 根 pyproject 已釘、全站共用
  一個 venv，結構上不會飄）**：當年每課一個 pyproject 寫 `>=` 時，新課解到 0.24.0，
  export 出的 assets hash 與共用基準不一致 → build.sh 退回該課獨立 assets，dist 從
  28M 膨脹到 112M。要升版就改根 pyproject 一次升全站＋重驗雙層驗證。
- **`mo.vstack([fig, mo.md(...)])` 裡的裸 matplotlib figure 不渲染**：圖一律當 cell 的
  最後運算式，說明文字拆到下一個 cell（要共用數值就 return 變數）。
- **`mo.md` 會把 `$…$` 之間的文字當 LaTeX**：講金額的課（兩個錢字號夾中文）會渲染成殘骸，
  md 內錢字號一律寫 `\$`（要插值就 `rf"""…"""`）。冒煙抓不到（無 Traceback、圖照畫），
  只有掃 session JSON 渲染輸出才看得到（local-llm/prompt-caching 實測，2026-08）。
- `mo.md` 會 dedent：`{table}` 插值進多行字串時，插入內容每行縮排要與周圍一致，
  否則共同前綴變空、縮排行被當 code block。
- 本機 CPython 跑通 ≠ WASM 跑通，**雙層驗證缺一不可**。
- `float(tensor_requires_grad)` 會噴 UserWarning → 用 `float(x.detach())`。
- ruff 對 marimo cell 格式報 B018/PLR1711 是**假警報**（最後運算式＝渲染輸出、
  return 收尾＝marimo 產生），repo 根的 `ruff.toml` 已 per-file ignore——別去「修」格式。

## Pyodide（純瀏覽器課）限制

- **右欄就緒偵測與冒煙的訊號（工程機制，非教學要求）**：預設靠 iframe 內 img/canvas
  計數（`<body data-ready-figures="N">`）；無圖課改宣告 `data-ready-selector="<css>"`
  （notebook 全部跑完會出現的元素，例如最後一格輸出的識別元素），該課 smoke-test 的
  `READY_SELECTOR` 常數設同一訊號。**`data-ready-figures` 在 page-fill 替換區之外**
  （模板預設 1）——要自己 Edit `<body>` 那行，寫完 grep 對一次 smoke 的 `MIN_FIGURES`；
  宣告太小冒煙測不出（只是早一步變綠）。有圖的課留一張真的有教學功能的圖仍是好預設——
  但那是教學選擇，不是工程強制。
- **首次載入 ~25 秒**（含 wheel 下載；零依賴課 ~14 秒）——平台物理，無法縮短：
  右欄要有載入狀態提示（狀態列輪詢就緒訊號變綠；同源 iframe 才可行；已內建在
  page 模板）。應對等待的**預設手法**＝左頁開頭安排「等待時正好讀完」的第一節＋
  hero 即時互動；有更好的等待設計就用你的。
- **matplotlib 無 CJK 字型**：圖內文字（標籤/圖例）一律英文，中文解說走 markdown 與左頁。
- **效能**：numpy 向量化可以很快（迷你 LM 1500 步預訓練＋800 步 SFT，拉桿重訓 1–2 秒），
  關鍵是別寫 per-sample Python 迴圈（embedding 梯度用 `np.add.at`）。
- **模型輸出對比別用 markdown 表格**（輸出含換行會把表弄壞）：用 HTML 卡片
  （`mo.Html` + `white-space:pre-wrap` + `html.escape`）。

### 教學用迷你模型的細節坑（sft 課實測；同構於真實訓練的經典錯誤，修好即教學點）

- **生成起點必須落在訓練目標的起點上**：生成 prompt 停在 `a:` 但訓練時 `a: ` 的空格
  被 mask → 第一個字就 OOD 出軌（prompt 要含空格）。
- **上下文窗要裝得下問題關鍵資訊**：CTX=8 裝不下問題關鍵字（cats/dogs 落窗外）
  → 模型分不出問題；CTX=16 解。
- **回合結束符要算 loss**：漏掉它，模型答對但不會「停」——對應真實 SFT 必須把
  `<|im_end|>`（Llama 系 `<|eot_id|>`）納入 loss。

## 外部軌（molab）機制

- **網址零上傳零回填**：repo 公開在 GitHub，molab 直讀
  `https://molab.marimo.io/github/{owner}/{repo}/blob/{branch}/content/<topic>/<id>/<id>_ext.py`，
  git push 即更新、網址永不變。因此 **`ref_data/` 絕不能入版控**（已 gitignore）。
- **外部軌不等於 GPU**：需要 GPU 的課才留模板的 GPU 檢查 cell（molab 執行環境選
  GPU Server）；純粹是套件裝不進 Pyodide 的課（如 fastmcp）用 molab **免費 CPU**
  環境即可全程跑，頁面文案要寫明「不需要 GPU」。
- notebook 帶 **PEP 723 inline dependencies**，molab 自動裝。骨架照
  `assets/templates/lesson_ext.py`。**prerelease 套件要把傳依賴的 prerelease pin 一起釘**
  （如 fastmcp 4 beta 要同時釘 fastmcp-slim），否則 uv 解析卡 prerelease 檢查。
- **notebook 要自成完整教材**：它是課程唯一的程式版本——每個程式 cell 前用 md 講清楚
  「為什麼、在做什麼、看什麼」，章節用 emoji 編號對齊左頁。學員只帶這份檔案也能學完。
- **molab 不能 iframe 嵌入**（登入態被跨站 cookie 保護擋下、唯讀預覽在框架內渲染失敗、
  實測死案）→ 右欄用常駐導流面板：步驟（登入→取得副本→執行）＋行動按鈕
  （新分頁開 notebook / 登入 / 下載 .py）。版型在 `page_ext.html` 模板。
- **學員自備 API key 的課**：notebook 用 `mo.ui.text(kind="password")` ＋ env var
  fallback（本機驗證時 export 前設 env 即可全跑）；實測 password 初值不會進
  export html 產物，但 repo/dist 仍要全文掃描 key 零外洩才部署。
  NIM key 免費申請（build.nvidia.com）；tool calling 用 `openai/gpt-oss-120b`
  （llama-3.3-70b 會挑爛中文關鍵字）。
- 本機無 GPU 時，GPU 課驗證到「sandbox 全跑＋GPU cell 優雅降級」；
  全量驗證請使用者在 molab 實跑。

### 實測可用的 LLM 微調配方（sft 課在 molab GPU 全程跑通）

- **Unsloth 配方**：`FastLanguageModel.from_pretrained`（4-bit 預量化底模，如
  `unsloth/Llama-3.2-1B-Instruct-bnb-4bit`）→ `get_peft_model`（LoRA r=16，
  q/k/v/o + gate/up/down 七投影，`use_gradient_checkpointing="unsloth"`）→
  trl `SFTTrainer`（60 步級即可看到行為改變，`report_to="none"`）→
  `train_on_responses_only`（一行 loss masking）。
  **`from unsloth import ...` 必須在 transformers/trl 之前**。Unsloth 不支援 CPU。
- **SFT 類課程選 instruct 底模**（模板現成、`<|eot_id|>` 收尾可靠）；教「換身分與風格」
  比教「從續寫到會回話」貼近業界（後者交給瀏覽器內迷你模型演）。
  用 base 模就要手寫 chat template（base tokenizer 常沒附 template，
  `apply_chat_template` 直接 ValueError），且 SFT 後常「亂開幻覺新回合」→
  `generate` 的 `eos_token_id` 給**清單**（如 `[im_end, im_start]`）＋解碼後在第一個
  特殊記號硬切，雙保險。
- 推論前 `FastLanguageModel.for_inference(model)`、續訓前 `for_training(model)`。

### 實測可用的 MCP 課素材（fastmcp 課）

- fastmcp 4 in-memory：`Client(mcp)` 直連 server 實例；`Tool.inputSchema` 已
  deprecated 用 `input_schema`。UserSession 需認證身分；未認證跨請求狀態走
  `mcp.add_provider(SessionProvider())` ＋ `session_id: SessionId` ＋ `get_session()`。
- 工具錯誤要以 tool role message 回饋給 LLM 讓它自我修正，別讓 ToolError 炸掉 loop。

### 實測可用的 LLM 應用課素材（llm-apps 系列：LiteLLM／FastMCP 4／Qdrant／RAG，2026-08-20）

- **軌道**：`openai`、`qdrant-client`、`fastmcp` 三個套件 Pyodide spike 全 FAIL（無純 Python wheel）
  ＋需真網路 → 整個系列外部軌。gateway 有開 CORS，但瀏覽器軌只能用 JS fetch 重寫、學員帶不走，放棄。
- **外部軌 notebook 的輸出怎麼驗**：`export --sandbox` 產的 HTML 只嵌程式碼；渲染結果在
  `content/<topic>/<id>/__marimo__/session/<id>_ext.py.json`（gitignored），grep 那裡看數字最快。
  sandbox 會裝最新 marimo（非全站釘版）——外部軌不共用 assets，無妨。
- **教學頁內容區**：用 `page-fill.py`＋`page_content.py`（上述坑已內建：先移除模板註解、lambda 替換）。
- **背景工作（run_in_background）裡不要 `cd`**：cwd 跑掉後 `uv run marimo` 找不到專案會
  `Failed to spawn: marimo`、exit 2 但沒有明顯錯誤——用 `verify-ext.sh`（自己 cd 到 repo 根）。
- **一次建系列課的順序**：六課全部 spike → 六份 notebook 逐一寫完就丟背景 verify（LLM 課一份要
  1–10 分鐘，nemotron 類更久）→ 同時寫 page_content → 最後 smoke-all 一次。別等一份驗完才寫下一份。
- **換模型的代價很真實**：第一版 gpt-oss → ultra → lightning，每次都要重跑 spike、改四份 notebook
  ＋四頁文案、重驗。所以：模型名只出現在一格常數；左頁不寫點估計；行為宣稱標「實測（模型名）」。
- **LiteLLM gateway**（`https://litellm.itsmygo.uk/v1`，教學 virtual key 課後撤銷）：
  免費池某家 402（月額度用完）LiteLLM **不重試不換家**（已由 gateway 端移除＋fallbacks 修掉）。
  系列預設模型由使用者指定（現為 `nemotron-3.5-lightning`）：**推理型模型 `max_tokens` 一律 4096**
  ——給太小時有的來源會把截斷的思考塞進 `content`（"Here's a thinking process…"），像答案其實不是；
  答案與思考分別在 `content`／`reasoning_content`。小模型會把 tool 參數、搜尋詞翻成英文
  （`"Taipei"`、`"parking"`）→ 假函式加英文別名、工具 docstring 註明「query 請用繁體中文」。
  教學 virtual key 的模型白名單要用 master key `POST /key/update` 加；Dokploy 改 mount 後
  redeploy 不一定重讀 config，`/model/info` 沒看到新模型就要重啟容器。**同一模型名多上游 ⇒ 行為不一致**（structured output 有的家
  遵守有的回 markdown、`reasoning_tokens` 有的家不回報）——示範格要寫成失敗可解釋、不崩潰。
  推理型模型 `max_tokens` 給小 content 會被截斷或空字串（教學點）；回應 `model` 欄位是群組名，
  辨識上游靠 `x-litellm-model-api-base` header；
  `qwen3-embedding-0.6b` 回傳單位向量（內積＝cosine）；structured output 在不支援的家會被
  `drop_params` 默默拿掉（nemotron-3-ultra 回 markdown 表，教學點）；vision 只有 gemini-3.5-flash。
- **FastMCP 4.0.0b1**：新協定 `2026-07-28` 首發 `server/discover`，每發帶 `mcp-method`／`mcp-name`
  header ＋ `params._meta` 信封、零 session id；`mode="legacy"` → `2025-11-25`，呼叫一次工具 6 個 HTTP
  請求（initialize→initialized→GET→call→list→DELETE）。裸 `httpx.post` 單發成功三要件：
  `MCP-Protocol-Version` header、`mcp-method` header、`_meta` 信封。`SessionProvider()` 自動註冊
  `create_session`／`end_session`，`create_session()` 回 **str**。marimo cell 裡 daemon thread 跑
  uvicorn（`mcp.http_app()`）在 sandbox export 正常，重跑前先探 port。
- **RAG 數字會飄**：沒 RAG 的「矇對」題數每次不同（0–2），左頁寫範圍不寫死；有 RAG 7/7 穩定。
- matplotlib 圖內別放 emoji（缺字警告），分類標籤用 ASCII。

### 一次建多堂課（local-llm 八課平行，2026-08-28 補充）

- **smoke 模板的 quiz 斷言曾有 `page.context().newPage()` bug（已修）**：`browser.newPage()`
  建立的隱式 context 不允許再開分頁（Playwright 直接 throw "Please use browser.newContext()"），
  第二頁一律用 `browser.newPage()` 另起 context。症狀＝smoke-all 只顯示「Node.js vXX」尾行。

- **平行子代理的 scratchpad 暫存檔要帶課名前綴**（`calc-<id>.py`）：通用檔名（`calc.py`）
  會被別課的代理整檔覆寫，受害者自己看不出來。
- 臨時預覽 server 也要分 port（同 verify 的 port 分段邏輯）；且**同一個 Bash 呼叫裡
  起背景 server 再接著跑 node 不可靠**——工具呼叫結束 server 會被收掉，改用
  run_in_background 另起，`curl` 確認 200 再跑 Playwright。
- **純瀏覽器課「零錯誤＋圖數」最快驗法**：讀 `content/<topic>/<id>/__marimo__/session/lesson.py.json`
  數 `cells[].outputs`（複數）裡的 `image/png`；`nb-outputs.py` 走的是 `--sandbox` 的路徑，
  對純瀏覽器課的 export 位置不適用。要看圖的真實構圖就把 base64 解出來看
  （element screenshot 會被 viewport 裁切造成假警報）。
- **課程頁自訂節內小標要加 class**（如 `h3.sub`）：`#lesson h3` 裸標籤選擇器以 ID 特異度
  蓋掉共用 `.quiz-q h3`，把全站測驗版型弄壞；修字串時用完整縮排比對，避免子字串誤中 quiz 區。

### 一次建多堂課（genai-intro 七課平行，2026-08-28 補充）

- **背景 Bash 有 ~10 分鐘上限**：全站 build（18 課 WASM export，~10 分鐘以上）與全站線上冒煙
  丟 run_in_background 會在半路被 killed（且子行程可能殘留，重跑前先 `pgrep -af "build.sh|marimo export"`）。
  長工改用 `setsid nohup bash -c '<cmd>; echo DONE_EXIT=$?' > log &` 脫離行程群組，
  再用 Monitor `until grep -q DONE_EXIT log` 等完成標記。本機 dist server 同理用 setsid 起、
  記 PID 收尾 kill。分批跑 smoke（每批 3–4 課）則可留在前景 600s 限內。
- **WRAP／md cell 裡要放含 `"""` docstring 的程式範例**：外層字串一律 `r'''` 定界
  （page-fill.py 檔頭有預警；`WRAP = r"""` 會被範例裡的三引號截斷，ruff 立刻抓到）。
- **中文文案可能混入同形異碼字元**（實錄：西里爾字母混進中文段落，肉眼不可見）：
  收尾對 content/<topic>/ 掃一次非 ASCII 且非 CJK 的字元
  （unicodedata.name 含 CYRILLIC/GREEK/HANGUL/KANA 者列出人工過目；α、・這類刻意用字放行）。
- **嵌真實 LLM 逐字稿當 hero**：模型輸出常含 `$x$`、`$$…$$`（LaTeX 記號）——進 `mo.md`
  會被吃掉，hero 用純 JS `white-space:pre-wrap` 原文呈現最穩（也最誠實）。
- **大 payload（如 int8 向量 b64）不要手抄**：spike 印出 → 佔位符 → python 腳本注入 lesson.py。

### 一次建多堂課：fork 平行＋port 分段（FastMCP 4 補充系列，2026-08-20）

- **四堂課平行寫**：主代理先把每課的 spike 跑通（`_spikes/spike_*.py`，一課一支、`--部分名` 可只跑一段），
  再 fork 子代理各寫一課（notebook＋page_content＋page-fill＋verify），自己寫最核心的一堂；fork 只准動自己的課程目錄，
  主題頁／首頁／NOTES／skill 由主代理收尾。六門舊課補解答也是一個 fork。牆鐘約 10 分鐘完成四堂課。
- **並行 verify 會同時起很多 uvicorn**：每課指定不重疊的 port 區段（auth 8771–、state 8781–、servers 8791、features 8801–），
  解答格再各留一段；撞 port 的症狀是 JSON decode error（打到別人的伺服器）。
- **本機沒有 `python` 只有 `python3`**：用 `python` 跑 page-fill 會靜默失敗、index.html 不更新（看 `__NB__` 還在不在）。
  skill 內指令已全改 `python3`。
- hero 互動用 `<button>` 做選項時，別讓 `#hero button { color:#fff; background:ink }` 這種通用規則蓋到選項鈕——
  選項鈕要自己宣告 `color`，否則白底白字（截圖預覽才看得出來，冒煙測不到）。
- 補充系列接在既有主題下：主題頁加一個 `.eyebrow` 分隔＋第二個 `.lessons` 區塊（用 inline `margin-top`，不動 topic.css），
  首頁課數加總；補充課的 eyebrow 統一「補充 A/B/C/D」對齊課卡 tag。

### 實測可用的 FastMCP 4 素材（補充系列；細節與坑全在 `content/llm-apps/NOTES.md`）

- **認證**：`StaticTokenVerifier`（教學）／`JWTVerifier(public_key=RSAKeyPair.generate().public_key, ...)`（本機簽 JWT）／
  `InMemoryOAuthProvider(base_url, client_registration_options=ClientRegistrationOptions(enabled=True, ...))`
  可在 notebook 內跑完**完整 OAuth 2.1 授權碼＋PKCE**（DCR 預設關閉要打開）；SDK `OAuth` 子類別覆寫
  `redirect_handler`／`callback_handler`（回 `AuthorizationCodeResult`）即可無瀏覽器。`require_scopes` 讓工具對沒權限者隱形。
- **狀態**：`request_state` 是 MCP SDK `RequestStateBoundary` 的 **AES-256-GCM** 密文（`v1.`+kid+nonce+密文），綁 ttl／method／
  參數摘要／aud／principal；五種竄改全回同一句 `-32602 Invalid or expired requestState`。預設金鑰 process 隨機 → 多副本要
  `RequestStateSecurity(keys=[...])`；session 跨副本要共用 `session_state_store`。工具的 `ctx` 一定要標 `ctx: Context`。
- **4.0 功能**：`fastmcp-tasks` 同版 pin；新協定 `tools/call`→`tasks/get`×N；`cache_ttl`＋`Client(cache=True)`；`x-mcp-header`
  參數要先 `list_tools` 才會鏡射成 header；`@mcp.completion` 回傳直接 `.values`；extension identifier 要 `vendor/name`。
- **生態系**：uvx 的官方參考伺服器是 SDK v1（握手協定），`create_proxy(cfg, mode="legacy")` 才能 mount 進新協定 hub；
  Context7 已講 2026-07-28、DeepWiki 仍 2025-11-25；老伺服器結果用 `result.content[0].text`。

## 驗證細節

### 兩軌的驗證矩陣

- **純瀏覽器課（雙層，缺一不可）**：
  1. `uv run marimo export html content/<topic>/<id>/lesson.py -o check.html`（CPython 全 cell）
  2. build 後 headless Playwright 冒煙（`smoke-test.mjs`：等圖表數、驗錯誤文字、console，
     **含手機段**——390×844 結構＋該課在手機上載到就緒）
- **外部軌課**：
  1. `bash .claude/skills/make-lesson/scripts/verify-ext.sh <topic> <id> [關鍵字...]`
     ——從 repo 根跑 `marimo export html --sandbox`（自動建 PEP 723 環境、全 cell 執行）
     再用 `nb-outputs.py` 掃渲染輸出，有 error 就 exit 1；關鍵字給了會印出左頁要引用的數字。
     **GPU cell 與 key-gated cell 要能在無 GPU／無 key 環境優雅降級（mo.stop ＋指引），
     不能 Traceback**。帶 key 全跑：export 前設對應 env var。
  2. `bash .claude/skills/make-lesson/scripts/smoke-all.sh --build`（全站頁面冒煙：h1 可見、
     molab 連結指對檔、.py fetch 200、console 乾淨）。
  3. 部署後 `smoke-all.sh --base https://agentclass.pages.dev`、git push，請使用者在 molab
     實跑一次（molab 環境本機碰不到）。

### 手機 viewport 驗證（390×844，發布前必過）

RWD 行為規範見 site.md「RWD 與行動裝置」節；驗證面三件事：

1. **全站**：`smoke-all.sh` 已內建——跑每課 smoke 之後自動接
   `scripts/mobile-smoke.mjs`（390×844 逐課結構檢查＋app/edit 各抽一堂全載）。
   結構檢查＝無橫向溢出（**量兩層**：`document.scrollingElement` 與 `#lesson` 自身——
   教學 pane 是捲動容器，rogue 寬元素只撐大它、不撐大 document）、底部切換列存在、
   教學區不預載 notebook、切到實作後內容符合課程型態（app＝開載／edit＝提示卡／
   ext＝molab 面板＋note）。
2. **單課**：課程目錄的 `smoke-test.mjs`（新模板）自帶手機段，單獨跑即含手機檢查。
3. **人工目視**：`node .claude/skills/make-lesson/scripts/preview-shots.mjs --vp 390x844 /<id>/`
   截教學視圖；要截實作視圖加 `@`：`"/<id>/@#view-tabs button[data-view=lab]"`（會等就緒）。
   notebook 本體直接看 `--vp 390x844 /<id>/nb/index.html` 不適用（無狀態列），
   自寫腳本時注意 marimo 的捲動容器是 `#App` 不是 window。

手動跑 mobile-smoke（偵錯單課用）：
`node .claude/skills/make-lesson/scripts/mobile-smoke.mjs http://127.0.0.1:8787 <id>:app|edit|ext`
（gate 上鎖課的覆蓋層：檢查一律用 DOM `click()` 繞過命中測試，斷言照常有效。）

### Playwright 通則

- 使用者的 Chrome 可能在別台機器——**本機驗證一律用主機上的 headless Playwright**，
  不要用 claude-in-chrome 測 localhost。
- **server 一定起在 dist 根目錄**（`python3 -m http.server 8787 -d dist`），
  純瀏覽器課冒煙 URL 是 `/<id>/nb/index.html`、外部軌課是 `/<id>/`
  ——只 serve 子目錄會 404（assets 走 `/shared/assets/` 絕對路徑）。
- 預覽截圖用 `scripts/preview-shots.mjs`（課程頁自動等狀態列變綠；外部軌課無狀態列，
  直接截）。自寫 node 腳本時注意 ESM 從**腳本所在位置**往上找 node_modules——
  腳本放 repo 樹外（如 /tmp）會 `ERR_MODULE_NOT_FOUND`，放 repo 內或用絕對路徑 import。
- 冒煙判準（純瀏覽器課）：圖表 `<img>/<canvas>` 數量 ≥ 預期、頁面無 Traceback 文字、
  console 無 error。範本：`assets/templates/smoke-test.mjs`（cp 到課程目錄後改頂部
  `H1_TEXT` / `MIN_FIGURES` 兩個常數）。playwright 是 repo 根目錄的 devDependency
  （`npm install` 即可；瀏覽器二進位在 `~/.cache/ms-playwright` 全使用者共用，
  通常不需重新下載，缺的話 `npx playwright install chromium`）。
- `text=中文` 會撈到隱藏 `<title>` → 用 `h1:has-text(...)` ＋ `state:"visible"`。
- `waitForFunction(fn, arg, options)`：options 是第三參數，放錯位置逾時默默變 30s。
- marimo 在內部容器捲動：驗證捲動量目標元素的 `getBoundingClientRect()`。
- headless 截圖 emoji 是豆腐＝假警報，真瀏覽器正常。

## Cloudflare Pages

- 單檔上限 **25 MiB**、免費版單次部署 **20,000 檔**（build.sh 會先檢核擋下）。
- 檔案數 sanity check：純瀏覽器課每課約 +15 檔、外部軌課每課約 +2 檔；
  build 輸出出現「assets 與共用版本不一致」警告＝marimo 版本飄了，
  回頭查根 pyproject 的釘版，別帶著獨立 assets 上線。
- **影片不放 .mp4**：用 `video/upload.py` 傳上 YouTube，`page_content.py` 寫 `VIDEO = "https://youtu.be/<id>"`，
  page-fill 自動以 `youtube-nocookie.com` iframe（`loading="lazy"`、16:9 `.video-box`）嵌在 hero 標題之後。
- **Playwright 別等 `networkidle`**：頁面一有 YouTube 這類第三方 iframe，網路永遠不會 idle，`page.goto` 會 60 秒逾時。
  冒煙／截圖腳本一律 `waitUntil: "load"`，之後靠自己的就緒輪詢（模板已改；2026-09-02 加課程影片時踩到）。
- 部署後 CDN 有冷資產/傳播延遲：**等 30–60 秒再打線上冒煙，或失敗先重試一次**；
  要立即驗證就用該次 deployment 專屬網址（`https://<hash>.agentclass.pages.dev`）。
- 根目錄有 `404.html` 關掉 SPA fallback（缺檔回真 404），build.sh 會生。
