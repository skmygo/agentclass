# _spikes：llm-apps 系列的實測腳本

建課第一步「先寫程式定軌」與之後「換模型重驗」用的小腳本，全部可以 `uv run --script` 直接跑
（PEP 723 依賴寫在檔頭）。build.sh 只會部署 `index.html` 與 `<id>_ext.py`，這個目錄不會上線。

| 檔 | 驗什麼 | 對應課 |
|---|---|---|
| spike_model_probe.py | 某個 chat 模型的基本行為：自我介紹、max_tokens 坑、串流首字、12 發並發分佈 | 01 |
| spike_litellm_basics.py | 列模型、chat、串流、embedding 相似度、並發 header | 01 |
| spike_litellm_tools.py | tool calling 兩回合、structured output 掃描、vision 掃描 | 02 |
| spike_fastmcp_basics.py | tools/resources/prompts + in-memory Client | 03 |
| spike_fastmcp_session_http.py | SessionProvider／SessionId、HTTP 新舊協定、裸 POST | 03 |
| spike_fastmcp_raw_post.py | 單發 httpx.post 成功的三要件 | 03 |
| spike_qdrant.py | :memory: 建庫、查詢、過濾、三種距離、真 embedding | 04 |
| spike_rag.py | 切段、入庫、7 題評測（沒 RAG vs 有 RAG）、範圍外 | 05 |
| spike_capstone.py | MCP 工具 + agent 迴圈的四個問題 trace | 06 |
| spike_fastmcp_auth.py | StaticTokenVerifier／require_scopes／UserSession、RSAKeyPair+JWTVerifier、InMemoryOAuthProvider 完整 OAuth 2.1（裸 httpx 六步＋無瀏覽器 SDK）；`static`/`jwt`/`oauth` 分段 | 補充 A |
| spike_fastmcp_state.py | ctx.set_state、共用 store 的兩台副本、InputRequiredResult 多回合、截下 requestState 拆解、五種攻擊、共用 keys／ttl；`rounds`/`wire`/`store`/`ctx` 分段 | 補充 B |
| spike_fastmcp4_features.py | fastmcp-tasks 背景任務側錄、cache_ttl＋Client(cache=True)、x-mcp-header、completion、自訂 extension、路徑安全、BM25 search；`tasks`/`cache`/`completion`/`extension`/`path`/`search` 分段 | 補充 C |
| spike_mcp_servers.py | uvx time／fetch stdio、多伺服器設定、DeepWiki／Context7 遠端、create_proxy 合成 hub（legacy pin）、npx filesystem；`stdio`/`remote`/`gateway`/`npx` 分段（需網路） | 補充 D |
| spike_solutions.py | 六課「延伸挑戰」折疊解答的 LEVEL 1/2 程式碼真跑一遍（`--lesson <id>` 逐課、`--repeat N`），LEVEL 3 的門檻掃描／裸 POST 格式 | 01–06 |

**換模型 SOP**：改 `spike_model_probe.py` 的 `M`、`spike_rag.py`／`spike_capstone.py` 的 `LLM`
→ 三支各跑一次 → 把變動的行為與數字更新到 `<id>_ext.py` 與 `page_content.py`
→ `verify-ext.sh` 重驗 → `page-fill.py` → `smoke-all.sh --build`。
換模型後也跑一次 `spike_solutions.py`，對回各課解答 cell 裡「你應該看到…」的範圍。
