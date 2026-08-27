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
