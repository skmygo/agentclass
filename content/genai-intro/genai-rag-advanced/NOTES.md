# genai-rag-advanced（補充 A：進階 RAG）NOTES

延伸主線 `genai-rag`。純瀏覽器課、app 模式（主題層 `lesson-mode=app`），4 張圖（`data-ready-figures="4"`）。

## 素材從哪來（全部實測，2026-09-24）

一支 spike 產生全部素材：`content/genai-intro/_spikes/spike_genai_rag_advanced.py`（PEP 723，`uv run --script`）。

| 素材 | 來源 | 用在哪 |
|---|---|---|
| 手冊 20 節／90 句／2,890 字、41 題考卷（標準答案＝子句的唯一子字串，程式自動對到編號） | spike 內的 `SECTIONS`、`QUESTIONS`（原創虛構教材） | lesson.py DATA 區、所有數字 |
| 問題＋子塊向量（int8＋b64）；加章節標題版、固定 60/150/300/600 字切塊的相似度矩陣（int16 ÷10000） | 區網 jina-embed＝`jinaai/jina-embeddings-v5-text-small-retrieval`（1024 維），**有加 `Query: `／`Document: ` 前綴** | 1️⃣2️⃣3️⃣5️⃣ |
| cross-encoder 分數：41 題 × 90 句全部配對（logit，int16 ÷1000） | 本機 CPU 跑 `BAAI/bge-reranker-v2-m3`（sentence-transformers 6.1.0 `CrossEncoder`，14 執行緒 44.9 ms/對；一題 × 20 候選 916 ms） | 4️⃣5️⃣、課文「約 45 ms 一對」 |
| hero 開關板：3 題 × 8 種開關組合（15 種不同 context，各問兩次）的 top-3、回答、關鍵事實檢查 | 區網 qwen3.5-2b，temperature=0、`enable_thinking=False`、max_tokens 600 | 教學頁 hero（page_content.py 的 HERO_DATA） |
| E07 只取第 1 名的回答（向量 vs 混合） | 同上，`--part llm_extra` | s3 課文引述 |
| 測驗診斷題素材（父塊沒去重的 prompt、分數直接相加、少前綴、bm25s k>語料） | `--part errors` | quiz Q2、Q4、s5 表格 |
| 5️⃣ 格點搜尋（2,050 種組合） | `--part grid` | LEVEL 3 解答、s5 最佳組合列 |

BM25 是 numpy 手寫（字元 bigram＋英數整詞、Lucene 形式 k1=1.5 b=0.75），spike 內已與 `bm25s==0.3.11`
（`method="lucene"`）逐分數比對，max |diff| ≈ 2e-6。瀏覽器裡跑的是同一份程式碼，現場算。

## 重產／重驗

```bash
S=<暫存目錄>
# 1) 向量（服務版；換成 --local 就是免費路徑，見下）
EMBED_URL=<OpenAI 相容 /v1> uv run --script content/genai-intro/_spikes/spike_genai_rag_advanced.py --part embed,bm25 --out $S
# 2) rerank（CPU，約 3 分鐘；別用 GPU）
CUDA_VISIBLE_DEVICES="" uv run --script content/genai-intro/_spikes/spike_genai_rag_advanced.py --part rerank --out $S
# 3) 指標、LLM 紀錄、診斷素材、格點搜尋、payload、注入 lesson.py 與 page_content.py
LLM_URL=<OpenAI 相容 /v1> uv run --script content/genai-intro/_spikes/spike_genai_rag_advanced.py \
  --part eval,llm,llm_extra,errors,grid,emit,inject --out $S
python3 .claude/skills/make-lesson/scripts/page-fill.py content/genai-intro/genai-rag-advanced
```

env：`EMBED_URL`（＋可選 `EMBED_MODEL`，預設 `jina-embed`、`EMBED_KEY`）、`LLM_URL`（＋`LLM_MODEL` 預設 `qwen3.5-2b`、`LLM_KEY`）、
`RERANK_THREADS`。端點一律從 env 讀，**repo 裡沒有任何內網位址**。
`--part inject` 只改 lesson.py 的 `DATA BEGIN/END` 區塊與 page_content.py 的 `HERO_DATA_BEGIN/END` 區塊。

**注入後要手動重驗的句子**（數字寫死在文案裡的地方）：

- page_content.py：s1（35/41、MRR 0.92、步驟題 1/8）、s2 表（1/8·94、7/8·859、7/8·1,734、8/8·327）與「沒叫你加除垢劑」引文、
  s3（E17 0.656／E11 0.528／E07 0.526；13→15、9→5；35/27/33；w=0.25 回到 35；E07 top-1 的回答引文）、
  s4（35→37、N=3 38/41 MRR 0.955、出國兩個月 1→5、45 ms）、s5（最佳組合 38/8/32/237；98% candidate recall@20；
  章節標題 35→36、步驟 5→7、型號 13→12；少前綴 35→30、換句話說 9→6）、quiz Q1–Q5 的每個數字。
- lesson.py：1️⃣–5️⃣ 的表格都是現場算的，不用改；**6️⃣ accordion 解答是寫死的**（25/33、18/33、23/33、28/33、5/8；
  w=0.25–0.30 → 35/41、7/10；N=3 k=2 242 字、標題＋N=5 237 字、N=20/40 掉到 37）。
- 驗法：CPython export 後讀 `__marimo__/session/lesson.py.json` 的 text/markdown 輸出逐一對照 spike 印出的數字。

## 免費路徑（帶回家）的驗證範圍

- `--local`：不用任何服務，sentence-transformers 在 CPU 載同一個開源嵌入模型（CC BY-NC 4.0）＋ bge-reranker-v2-m3（Apache-2.0），
  模型下載約 3.5 GB（1.19 GB＋2.27 GB）。本機用「只有 pip 套件」的乾淨環境模擬 Colab
  （`uv run --no-project --with numpy --with bm25s==0.3.11 --with sentence-transformers==6.1.0 --with torch`、CPU、`RERANK_THREADS=2`）
  實跑（2026-09-24，`--part embed,bm25,rerank,eval,grid`，模型已在快取）：嵌入 471 句 98 s、rerank 3,690 對 332 s（89.9 ms/對）、
  全程 7 分 30 秒、記憶體峰值 4.7 GB；**所有課文引用的分數與服務版完全相同**（35/41、27/41、33/41、37、38、格點最佳 237 字），
  只有「章節標題版 recall@3」0.60→0.57、一組格點 277→279 字這種課文沒引用的小數點差異（本機 fp32 vs 服務端推論的浮點差）。
  這個環境沒有 `openai` 套件也跑得完——證明 `--local` 不碰任何服務。
- **沒驗證**：Colab／Kaggle 本身、GPU 路徑、Ollama 當 `LLM_URL`（hero 的回答只用 qwen3.5-2b 錄過）。
- **CPU 上一定要 fp32**：jina v5 small 預設載成 bf16，CPU 上 32 句要 16.2 s，fp32 只要 2.9 s（2 執行緒）。
  spike 的 `--local` 與課文參考程式都已加 `model_kwargs={"dtype": torch.float32}`。

## 踩到的坑

- **現代 embedding 模型比「民間說法」強**：第一版語料（13 節 57 句、E01–E12）上向量的 hit@3 是 32/32 全對，
  「向量抓不到型號」根本不成立。擴成 20 節 90 句、E01–E20、長得像的零件型號（WF-12／WF-21、GS-54／GS-58）後，
  向量型號題 13/15（E07 被 E17 擠到第 3、WF-21 被 WF-12 擠到第 2）——課文照實寫「差距不大、但錯得很危險」，不誇大。
- **RRF 的 BM25 清單只能列「有命中詞」的文件**：一開始把 BM25 分數 0 的文件也照 index 順序排名次，
  0 分的前幾號文件（首次使用那節）平白拿到 RRF 分數，換句話說題被拖垮得更慘（hit@1 0.40）。真實 BM25 檢索器只回有命中的文件；修正後 0.50。
- **jina v5 retrieval 模型要加 `Query: `／`Document: ` 前綴**（vLLM 服務不會自動加；sentence-transformers 用 `prompt_name`）。
  主線 genai-rag 的 spike 沒加。少了前綴：hit@1 35→30。已做成 s5 表格的一列。
- **qwen3.5-2b 的「手冊中沒有提到」老毛病**：兩種 system prompt 都會先說「沒提到」再給答案（hedge）。
  hero 用字串比對的「關鍵事實」＋「開頭先說沒提到」標記客觀呈現，不做人工打分。
- **temperature=0 也不保證逐字相同**：15 種 context 各問兩次，有 3 種兩次措辭不同（都在第 ① 題；vLLM 批次運算的非決定性），
  hero 顯示第一次並標註。重錄後引文（s2 的「準備：除垢液流完後…」、s3 E07 top-1 的回答）要重新對照。
- **父子檢索對單點題可能是雜訊**：E07 只開父子 → 三整節 15 個故障碼 → 2B 模型回「手冊中沒有提到。」（實測，課文有寫）。
- **int8 量化**：top-3 集合 41/41 題一致、標準答案名次完全一致，cosine 最大誤差 0.0018；
  dense 前 30 名相鄰分數最小間距 2.7e-6（遠大於 CPython／WASM 浮點差），WASM 版數字已 scrape 比對一致。
- rerank 用 logit 存（sigmoid 分數在 0 附近擠成一團，四捨五入會製造平手）；payload 解回來的名次 spike 內 assert 過。
- matplotlib 的兩顆 ★ 會重疊（1.00 與 0.97），左右錯開 0.12。
