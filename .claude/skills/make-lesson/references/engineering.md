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
bash .claude/skills/make-lesson/scripts/new-lesson.sh <id> "<課名>" <topic> "<主題名>" [--external]
                       # ↑ 模板複製＋代換＋生成自檢＋root uv sync（純瀏覽器課）一次做完
→ 純瀏覽器課：寫 lesson.py ＋ Edit index.html 內容區
  外部軌課  ：寫 <id>_ext.py ＋ Edit index.html 內容區（左頁教學＋右欄 molab 面板）
→ 驗證（見下方「驗證」一節，兩軌不同）
→ scripts/build.sh                    # 自動發現兩種課：WASM 匯出／教學頁複製 + 組裝 dist/
→ npx wrangler pages deploy dist --project-name=agentclass          # 憑證見 homelab-infra skill
→ 外部軌課另需 git push（molab 直讀 GitHub main）
```

build.sh **自動發現**：`content/*/*/lesson.py`（純瀏覽器課：WASM 匯出、
`auto_instantiate` 後處理、698 個 assets 抽共用）與 `content/*/*/<id>_ext.py`
（外部軌課：只複製教學頁與 .py 原檔），並處理首頁／主題頁／shared/ 併入、404.html、
course id 重複與「一課兩版」防呆、Pages 上限檢核。`<id>_gpu.py` 是舊雙軌課的遺留尾綴
（僅隨附複製，新課不再產生）。純瀏覽器課的 Python 依賴是 **repo 根一個 uv 專案**
（一個 venv、一個 lock，全部課共用）；外部軌課用 notebook 內的 PEP 723。

## marimo / 匯出的坑

- **`export html-wasm` 會把 `auto_instantiate: false` 烙進產物**（0.23.16；export 不吃專案
  pyproject 設定）→ build.sh 已用 sed 修。**升版 marimo 必須重驗這行為**。
- **marimo 版本必須全站釘同一版（`marimo==0.23.16`，repo 根 pyproject 已釘、全站共用
  一個 venv，結構上不會飄）**：當年每課一個 pyproject 寫 `>=` 時，新課解到 0.24.0，
  export 出的 assets hash 與共用基準不一致 → build.sh 退回該課獨立 assets，dist 從
  28M 膨脹到 112M。要升版就改根 pyproject 一次升全站＋重驗雙層驗證。
- **`mo.vstack([fig, mo.md(...)])` 裡的裸 matplotlib figure 不渲染**：圖一律當 cell 的
  最後運算式，說明文字拆到下一個 cell（要共用數值就 return 變數）。
- 本機 CPython 跑通 ≠ WASM 跑通，**雙層驗證缺一不可**。
- `float(tensor_requires_grad)` 會噴 UserWarning → 用 `float(x.detach())`。
- ruff 對 marimo cell 格式報 B018/PLR1711 是**假警報**（最後運算式＝渲染輸出、
  return 收尾＝marimo 產生），repo 根的 `ruff.toml` 已 per-file ignore——別去「修」格式。

## Pyodide（純瀏覽器課）限制

- **右欄就緒偵測與冒煙都靠 img/canvas 計數**：每課至少要有 1 張圖，
  純文字課的就緒訊號會失效——設計時留一張真的有教學功能的圖。
- **首次載入 ~25 秒**（含 wheel 下載；零依賴課 ~14 秒）：右欄要有載入狀態提示
  （現行做法＝狀態列輪詢 iframe 內 img/canvas 數量，就緒變綠；同源 iframe 才可行；
  已內建在 page 模板，記得改 `<body data-ready-figures>`），
  左頁開頭安排「等待時正好讀完」的第一節。
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
- **教學頁用 regex 只換內容區時**：先拿掉 page_ext 模板頂部的說明註解（含 `<style>`、`#molab-panel`
  字樣會干擾比對）；`re.sub` 替換字串用 lambda（內容含 `\u` 會被當 escape 炸掉）。
- **LiteLLM gateway**（`https://litellm.itsmygo.uk/v1`，教學 virtual key 課後撤銷）：
  免費池某家 402（月額度用完）LiteLLM **不重試不換家**，`free-chat` 約 1/7 機率失敗——使用者決定
  系列一律用 `nemotron-3-ultra`（三來源備援，但延遲 2–60 秒很飄，agent 每題 10–50 秒；
  `gpt-oss-120b` 快 10 倍，作對照組）。**同一模型名多上游 ⇒ 行為不一致**（structured output 有的家
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

## 驗證細節

### 兩軌的驗證矩陣

- **純瀏覽器課（雙層，缺一不可）**：
  1. `uv run marimo export html content/<topic>/<id>/lesson.py -o check.html`（CPython 全 cell）
  2. build 後 headless Playwright 冒煙（`smoke-test.mjs`：等圖表數、驗錯誤文字、console）
- **外部軌課**：
  1. `uv run marimo export html --sandbox content/<topic>/<id>/<id>_ext.py -o check_ext.html`
     ——自動建 PEP 723 環境、全 cell 執行。**GPU cell 與 key-gated cell 要能在
     無 GPU／無 key 環境優雅降級（mo.stop ＋指引），不能 Traceback**。
     帶 key 全跑：export 前設對應 env var。
  2. build 後頁面冒煙（`smoke-test-ext.mjs`：h1 可見、molab 連結指對檔、.py fetch 200、
     console 乾淨）。
  3. 部署後 git push，請使用者在 molab 實跑一次（molab 環境本機碰不到）。

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
- **影片不放 .mp4**：用 YouTube 非公開＋ `youtube-nocookie.com` iframe 嵌入
  （`loading="lazy"`、16:9 wrapper），版型在 page 模板的 `.video-box` 區塊。
- 部署後 CDN 有冷資產/傳播延遲：**等 30–60 秒再打線上冒煙，或失敗先重試一次**；
  要立即驗證就用該次 deployment 專屬網址（`https://<hash>.agentclass.pages.dev`）。
- 根目錄有 `404.html` 關掉 SPA fallback（缺檔回真 404），build.sh 會生。
