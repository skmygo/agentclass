# genai-intro 系列 NOTES

## 系列來源與定位

- 來源：使用者提供的「LLM 常見名詞速查總表」（7 大類 30 個名詞），目標客群是新手——
  每個名詞一句話重點（左頁 `.tldr` 格）＋真實工具程式碼範例（標示為參考程式、不在課內執行）
  ＋瀏覽器互動實驗。課末的「名詞速查卡」`.cheat` 表就是講義的濃縮版。
- 課程順序照速查表的 7 大類：tokens → training → inference → reasoning → agents → devstyle → rag。
- 全系列 7 課皆**純瀏覽器課**（numpy＋matplotlib，pyodide spike 通過）。
- 深入導流：inference 課連到 local-llm 系列、agents/rag 課連到 llm-apps 系列。

## 實測素材的來源與約定（重驗必讀）

- **LLM 逐字稿與向量都是真的**：來自自家 OpenAI 相容端點（spike 從 env 讀
  `RELAY_URL`＋`API_KEY`，**端點網址與 key 不入 repo**；部署前
  `grep -rE "itsmygo|RELAY_URL=" content/genai-intro/ --include='*.py' --include='*.html'`
  除 footer/留言連結外應零命中）。
- 課程文案標註：「實測（qwen3.5-2b，2026-08）」「jina-embed（1024 維）」。
- 逐字稿嵌進 lesson/page_content 當常數；重驗＝重跑 `_spikes/spike_genai_*.py`
  再同步常數。換模型時 reasoning／agents／rag 三課的 trace 全部要重抓。
- 向量以 **int8 對稱量化＋base64** 打包進 lesson.py（每向量一個 scale），
  spike 已 assert int8 與 fp32 的檢索排序一致、cosine 誤差 < 0.01。

## 踩過的坑（2026-08-28 初版）

- **relay 的 LLM 模型名會變**：skill 文件寫 qwen3-4b，實際已換 `qwen3.5-2b`
  （404 的 available 清單會講）。spike 開頭就 `models.list` 或直接試打。
- **jina-embed 對 1–2 字的超短輸入會回退化向量**（「小狗」×「汽車」cosine 0.97、
  「貓」×「車」0.997），片語級輸入才正常——embedding demo 一律用短片語不用裸單詞。
- **relay 的 thinking 模式不能當教材**：reasoning parser 把整段輸出塞進 `reasoning`、
  `content` 恆為空字串（finish=stop）。reasoning 課的「思考模式」段落改用概念＋
  真 API 程式範例，不用 relay 的 thinking 輸出。
- **context 超限的真實錯誤已實測**（quiz 素材）：對 16384 上限的模型塞 16321 input
  tokens ＋ 64 max_tokens → HTTP 400 "This model's maximum context length is 16384
  tokens. However, you requested 64 output tokens and your prompt contains at least
  16321 input tokens…"。
- **tiktoken o200k_base 中英文刀工實測**：同義句英文 44 字元→10 tokens、
  中文 15 字→17 tokens（~1.14 token/字；同內容中文多 ~70%）。左頁多處引用這組數字，
  換 tokenizer 要全部重驗。
- bat-and-ball 對照（qwen3.5-2b、temp=0）：直接答「55」錯、CoT 推導答 5 對；
  47×38 temp=1 抽 9 次 tally {'1786': 6, '1451': 1, '1466': 1, '1446': 1}。
  這些是 hero／quiz 的素材，模型換了幾乎一定變，重驗優先跑 spike_genai_reasoning。
- marimo cell 內別重複 `import numpy as np`（共用 import cell 已定義，重定義直接炸）；
  子 cell 一律從參數拿。
- CoT 逐字稿含 `$x$`／`$$…$$`：hero 走純 JS pre-wrap 原文呈現（mo.md 會當 LaTeX 吃掉）。
- 左頁文案數字「先跑再寫」：兩個 fork 都發生過先寫估算值、實跑對不上再回頭改
  （94.3%→94.4%、「約六萬」→54,138）——accordion 解答的數字也是宣稱。

## 改成 app 模式（2026-08-28）

- 全系列 7 課改成 **app 互動模式**（`content/genai-intro/lesson-mode`）：右欄隱藏程式碼，
  只留說明／互動元件／輸出。理由同 local-llm——右欄是教學模擬（BPE 玩具、計費估算、
  多數決機率、檢索 cosine），程式碼不是教學標的。
- 7 課原本都有「你的實驗區」自由編碼格，全部改成互動元件，並且**不再與主體重複**：
  - genai-tokens＝任一個字的下一字計數表（補 4️⃣ 的 temperature 觀察）
  - genai-inference＝模型／量化／VRAM 三選一的裝得下試算
  - genai-training＝1️⃣2️⃣ 拉桿的總結卡（含蒸餾軟標籤與狗÷車倍數）
  - genai-reasoning＝「9 次抽樣答對幾次」→ 各投票數的多數決答對率
  - genai-rag＝1️⃣ 選定問題後 top-1…5 的字數與 token 帳
  - genai-agents＝工具呼叫 JSON 的即時驗證器（含 JSONDecodeError 訊息）
  - genai-devstyle＝四個零件的 token 帳與每日總量
- 主體也補了兩個 UI（原本挑戰題要改常數才做得到）：genai-agents 的城市 dropdown、
  local-llm/speculative-decoding 的 `T_FLOP` 滑桿。
- 左頁「換你動手」指向實驗區變數名的句子（`MY_Q`／`MY_K`／`knowledge`）一併改成拉桿講法。

## 進階補充系列 A–F（2026-09-24 起）

- 使用者需求：在 genai-intro 下加 6 堂「進階補充」，不重複主線 7 課；**觀看者不需要任何服務、
  要直接可以運行或用免費資源**。
- 定軌：六課全部**純瀏覽器 app 模式**（沿用主題層 `lesson-mode=app`）。真實素材（LLM 輸出、
  向量、reranker 分數、訓練紀錄、agent trace、MCP 線路側錄、skill 觸發紀錄）由 `_spikes/` 在
  主機 .113 上實測錄製（區網 qwen3.5-2b／jina-embed、本機 RTX 4090、已登入的 claude CLI），
  嵌成常數在瀏覽器重播／重算；文案標「實測（模型名，日期）」。「帶回家自己跑」的路徑只能指向
  免費資源（Colab／Kaggle 免費 GPU、molab 免費 CPU、本機 Ollama、免費 API 額度）。
- 課表（主題頁「進階補充」區，順序即 endnav 鏈；主線 genai-rag → 補充 A）：

  | 補充 | id | 延伸自主線 |
  |---|---|---|
  | A | `genai-rag-advanced` 進階 RAG：父子檢索、混合搜尋與 Rerank | genai-rag |
  | B | `genai-finetune` 微調工具實戰：Unsloth、TRL 與託管微調 | genai-training |
  | C | `genai-agent-sdk` Claude Agent SDK | genai-agents |
  | D | `genai-mcp-fastmcp` MCP 新版協定與 FastMCP 4 | genai-agents（深入版在 llm-apps/fastmcp4*） |
  | E | `genai-skills` Agent Skills | genai-agents |
  | F | `genai-vibecoding` Vibe Coding 進階：讓測試當 AI 的眼睛 | genai-devstyle |

- 寫法：主代理 scaffold＋`.wip`＋分配 port 段（A 9110–、B 9120–、C 9130–、D 9140–、E 9150–、F 9160–；
  88xx 被主機其他服務占滿），六個 subagent 平行各寫一課（只動自己的課程目錄＋自己的 spike），
  單課驗證用新工具 `scripts/mini-dist.sh`（不跑全站 build 也能做完整 WASM＋頁面＋手機冒煙）。
  各課的坑與重驗方式在各自的 `content/genai-intro/<id>/NOTES.md`。

### 補充系列完成紀錄（2026-09-24）

- 六課皆純瀏覽器 app 課、單課 mini-dist 冒煙＋全站 build 通過。各課素材與「換模型／改版要重驗哪些句子」
  寫在各自的 `content/genai-intro/<id>/NOTES.md`；spike 一覽：
  - A `spike_genai_rag_advanced.py`（`--local` 無服務 CPU 模式可完整重現；jina v5 retrieval＋bge-reranker-v2-m3）
  - B `spike_genai_finetune{,_unsloth,_data,_errors,_collect}.py`（4090 實測；Unsloth 與 TRL 1.13 分兩個 PEP 723 環境）
  - C `spike_genai_agent_sdk{,_payload}.py`（claude-agent-sdk 0.2.159＋claude-haiku-4-5；錄影原檔不進 repo，重建要重跑）
  - D `spike_genai_mcp_fastmcp.py`（fastmcp 4.0.8；`--inject` 直接寫回 lesson.py／page_content.py）
  - E `spike_genai_skills.py`（tiktoken 量本 repo skill 三層 token；claude-haiku-4-5 觸發實驗）
  - F `spike_genai_vibecoding{,_hint,_risks,_pack}.py`（qwen3.5-2b 12 題回饋迴圈；PyPI 查套件幻覺）
- **主線 genai-rag 的已知問題**：spike 呼叫 jina-embed 沒加 `Query: `／`Document: ` 前綴（jina v5 retrieval 需要；
  補充 A 實測少了前綴 hit@1 35→30）。主線數字尚未重驗，下次動 genai-rag 時一併修。
- 補充 E 的 token 數字是 2026-09-24 的 repo 快照（make-lesson／publish-videos 等 9 個 skill）；skill 大改後
  頁面手寫數字會與當下檔案不一致，重跑 spike tokens＋inject＋page-fill。
