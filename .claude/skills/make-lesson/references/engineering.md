# 工程底線：管線、WASM 限制、GPU 軌道、驗證、部署

全部出自前兩堂課（decision-tree、sft）的實測。那些課程可能已從 repo 移除——
**不要假設 repo 內有現成課可以抄**，起手一律複製本 skill 的 `assets/templates/`
（模板已內建所有踩坑修正）。

## 管線（已走通兩次）

```
bash .claude/skills/make-lesson/scripts/new-lesson.sh <id> "<課名>" <topic> "<主題名>" [--gpu]
                       # ↑ 模板複製＋代換＋GPU 剝除＋build.sh 加課＋uv sync 一次做完
→ 寫 lesson.py（marimo 純 .py 格式）＋ Edit page 內容區
→ 第一層驗證：uv run marimo export html lesson.py -o check.html    # CPython headless 全 cell 執行
→ scripts/build.sh                                                  # export html-wasm + 後處理 + 組裝 dist/
→ 第二層驗證：headless Playwright 開 dist 的 WASM 版（冒煙）
→ npx wrangler pages deploy dist --project-name=agentclass          # 憑證見 homelab-infra skill
```

build.sh 已處理：WASM 匯出、`auto_instantiate` 後處理、698 個 assets 抽共用、教學頁與
lesson.py 複製、site/（首頁＋主題頁＋shared/）併入、404.html、Pages 上限檢核。
新課只需在 build.sh 加一行 `build_lesson <id>`（GPU 課另 cp `<id>_gpu.py`）。

## marimo / 匯出的坑

- **`export html-wasm` 會把 `auto_instantiate: false` 烙進產物**（0.23.16；export 不吃專案
  pyproject 設定）→ build.sh 已用 sed 修。**升版 marimo 必須重驗這行為**。
- **marimo 版本必須全站釘同一版（`marimo==0.23.16`，模板已釘）**：寫 `>=` 會讓新課解到
  更新版（實測解到 0.24.0），export 出的 assets hash 與共用基準不一致 → build.sh 退回
  該課獨立 assets，dist 從 28M 膨脹到 112M（每課多 ~700 檔/27MB）。要升版就全部課
  一起升＋重驗雙層驗證。
- **`mo.vstack([fig, mo.md(...)])` 裡的裸 matplotlib figure 不渲染**：圖一律當 cell 的
  最後運算式，說明文字拆到下一個 cell（要共用數值就 return 變數）。
- 本機 CPython 跑通 ≠ WASM 跑通，**雙層驗證缺一不可**。
- `float(tensor_requires_grad)` 會噴 UserWarning → 用 `float(x.detach())`。
- ruff 對 marimo cell 格式報 B018/PLR1711 是**假警報**（最後運算式＝渲染輸出、
  return 收尾＝marimo 產生），repo 根的 `ruff.toml` 已 per-file ignore——別去「修」格式。

## Pyodide（瀏覽器軌）限制

- **套件必須有 Pyodide wheel**：numpy / pandas / sklearn / matplotlib 皆可；
  **torch、unsloth、transformers 等不行** → 需要它們就是雙軌課的訊號。
- **server 框架類套件（fastmcp、mcp SDK 等）也上不了 Pyodide**（實測：`watchfiles`
  無純 wheel；mock 掉之後撞 `pydantic-core` 精確 pin 對不上 Pyodide 內建版）。
  教框架課的替代模式＝**迷你重現**：用標準函式庫重現核心機制（裝飾器→schema、
  協定分發器…），真框架程式碼放左頁／md code block 不執行。零依賴反而秒載（~14s vs ~20s）。
- **右欄就緒偵測與冒煙都靠 img/canvas 計數**：每課至少要有 1 張圖，
  純文字課的就緒訊號會失效——設計時留一張真的有教學功能的圖。
- **首次載入 ~25 秒**（含 wheel 下載）：右欄要有載入狀態提示（現行做法＝狀態列輪詢
  iframe 內 img/canvas 數量，就緒變綠；同源 iframe 才可行；已內建在 page 模板，
  記得改 `READY_FIGURES`），左頁開頭安排「等待時正好讀完」的第一節。
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

## GPU 軌道（molab）機制

- **網址零上傳零回填**：repo 公開在 GitHub，molab 直讀
  `https://molab.marimo.io/github/{owner}/{repo}/blob/{branch}/lessons/<id>/<id>_gpu.py`，
  git push 即更新、網址永不變。因此 **`ref_data/` 絕不能入版控**（已 gitignore）。
- GPU notebook 帶 **PEP 723 inline dependencies**，molab 自動裝。骨架照
  `assets/templates/lesson_gpu.py`（含 GPU 檢查 cell）。
- **molab 不能 iframe 嵌入**（登入態被跨站 cookie 保護擋下、唯讀預覽在框架內渲染失敗、
  實測死案）→ 右欄用 GPU 分頁做**站內導流面板**：步驟（登入→取得副本→選 GPU→執行）
  ＋行動按鈕（新分頁開 notebook / 登入 / 下載 .py）。版型在 page 模板的 `[GPU]` 區塊。
- 本機無 GPU：GPU notebook 驗證到「結構層級」（import 驗 marimo 格式）＋盡量做 CPU
  縮小版 FAST 路徑；全量驗證請使用者在 molab 實跑。

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

## 驗證（Playwright）細節

- 使用者的 Chrome 可能在別台機器——**本機驗證一律用主機上的 headless Playwright**，
  不要用 claude-in-chrome 測 localhost。
- **server 一定起在 dist 根目錄**（`python3 -m http.server 8787 -d dist`），
  冒煙 URL 是 `/<id>/nb/index.html`——只 serve nb 目錄會 404（assets 共用後走
  `/shared/assets/` 絕對路徑）。
- 預覽截圖用 `scripts/preview-shots.mjs`（課程頁自動等狀態列變綠）。自寫 node 腳本時
  注意 ESM 從**腳本所在位置**往上找 node_modules——腳本放 repo 樹外（如 /tmp）會
  `ERR_MODULE_NOT_FOUND`，放 repo 內或用絕對路徑 import。
- 冒煙判準：圖表 `<img>/<canvas>` 數量 ≥ 預期、頁面無 Traceback 文字、console 無 error。
  範本：`assets/templates/smoke-test.mjs`（cp 到課程目錄後改頂部 `H1_TEXT` /
  `MIN_FIGURES` 兩個常數）。playwright 是 repo 根目錄的 devDependency
  （`npm install` 即可；瀏覽器二進位在 `~/.cache/ms-playwright` 全使用者共用，
  通常不需重新下載，缺的話 `npx playwright install chromium`）。
- `text=中文` 會撈到隱藏 `<title>` → 用 `h1:has-text(...)` ＋ `state:"visible"`。
- `waitForFunction(fn, arg, options)`：options 是第三參數，放錯位置逾時默默變 30s。
- marimo 在內部容器捲動：驗證捲動量目標元素的 `getBoundingClientRect()`。
- headless 截圖 emoji 是豆腐＝假警報，真瀏覽器正常。

## Cloudflare Pages

- 單檔上限 **25 MiB**、免費版單次部署 **20,000 檔**（build.sh 會先檢核擋下）。
- **影片不放 .mp4**：用 YouTube 非公開＋ `youtube-nocookie.com` iframe 嵌入
  （`loading="lazy"`、16:9 wrapper），版型在 page 模板的 `.video-box` 區塊。
- 部署後 CDN 有冷資產/傳播延遲：**等 30–60 秒再打線上冒煙，或失敗先重試一次**；
  要立即驗證就用該次 deployment 專屬網址（`https://<hash>.agentclass.pages.dev`）。
- 根目錄有 `404.html` 關掉 SPA fallback（缺檔回真 404），build.sh 會生。
