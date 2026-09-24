# genai-vibecoding NOTES（補充 F：Vibe Coding 進階：讓測試當 AI 的眼睛）

延伸主線 `genai-devstyle`（那一課教過：Vibe Coding 定義、Agentic／Context／Spec-Driven）。
本課不重教那些，主軸是**回饋迴圈**：第一版沒過之後的五種下一步、假綠燈、測試抓不到的兩顆地雷、
2026 工具實務。純瀏覽器 app 模式；右欄全部是實測紀錄的重播／重算，零服務。

## 素材來源（全部實測，2026-09-24）

| 素材 | 來源 | 跑法 |
|---|---|---|
| 12 題 × 8 次重跑 × 4 種下一步（reroll／bare／full／weak） | `_spikes/spike_genai_vibecoding.py` | `LLM_URL=… RUNS=8 uv run --script …/spike_genai_vibecoding.py out.json`（約 15 分鐘，視 vLLM 負載） |
| 第 5 種下一步「錯誤原文＋一句診斷」（與上面配對，同一份第 1 版） | `_spikes/spike_genai_vibecoding_hint.py` | `uv run --script …_hint.py out.json out_hint.json` |
| 套件幻覺（15 任務 × 3 次、真查 PyPI JSON API）、寫死金鑰（10 次） | `_spikes/spike_genai_vibecoding_risks.py` | `uv run --script …_risks.py risks.json` |
| 打包注入（lesson.py 的 `VIBE_B64`／`RISK_B64`、page_content.py 的 `const HERO`） | `_spikes/spike_genai_vibecoding_pack.py` | `uv run --script …_pack.py out_hint.json risks.json round_half_up:4` |

- 模型：區網 vLLM `qwen3.5-2b`（`enable_thinking=False`、temperature 0.7、top_p 0.8、max_tokens 1536、每請求帶 seed、併發 4）。
- env：`LLM_URL`（預設 `http://localhost:11434/v1`＝本機 Ollama）、`LLM_MODEL`（預設 `qwen3.5-2b`）、`LLM_API_KEY`、`RUNS`。
  **端點不寫進 repo**。
- spike 環境：pytest 9.1.1、Python 3.14.5、openai 3.19.2（uv 依 PEP 723 解的版本）。
- 打包時會用瀏覽器同款判定（`safe_exec`＋`check_one`，import 白名單）把 1537 份程式**逐測試案例**重跑一次，
  與 pytest 的基本／邊界通過數完全一致才注入（不一致直接 exit）。所以 notebook 3️⃣ 在瀏覽器裡重算的結果＝實測紀錄。
- pytest traceback 裡的本機路徑（含使用者名稱）在打包時換成 `<site-packages>/`、`<python-lib>/`、`~/`，其餘原文不動。
- 一句診斷（`HINTS`）是課程作者看過 pilot 的典型失敗後寫的，每題一句、8 次重跑都用同一句；notebook 2️⃣ 看得到原文。

## 課文引用的數字（換模型／重跑時逐條重驗）

- 第 1 版：96 題次只有 16 個全過（每輪 0–3 題）→ 80 個進入五種下一步。
- 救回數（共 80）：reroll 10、bare 6、full 6、hint 21、weak 1；每輪 12 題最後全過：reroll 2–5、bare 1–5、full 2–4、hint 1–7、weak 1–3。
- 一字不差重交：bare 164/228（72%）、full 153/228（67%）、hint 85/200（42%）、weak 140/175（80%）、reroll 31/226（14%）。
- 配對：hint 救回而 full 沒救回 17 個，反過來 2 個。
- `round_half_up`：8 個第 1 版全是 `return int(x + 0.5)`；bare／full 各救回 3/8、hint 8/8、reroll 0/8（24 次重抽全是同一行）；
  bare 修正 18 次中 14 次一字不差、full 15/18（頁面引用 full 的 15/18）。
- 假綠燈：96 題次中 22 個「基本全綠、完整沒過」，其中 20 個第 1 版就停手；`round_half_up` 8/8。
- 輸出 token（每輪 12 題平均）：reroll 6380、bare 7273、full 7918、hint 9382、weak 6910；第 1 版平均 163 tokens、2.5 秒。
  每多救回 1 題：hint ≈ 2.8k、reroll ≈ 3.5k、bare ≈ 7.1k、full ≈ 8.0k 輸出 token（只算輸出）。
- 3️⃣ 測試設計師（accordion 引用）：`format_bytes` 51 份去重程式，只留基本測試放行 15 份錯的＋1 份對的；
  單加 `1024**5` 剩 1、`-1` 剩 4、`512` 剩 5、`1024` 剩 12。`split_bill` 26 份，基本測試放行 7 份錯的，任一金額邊界全擋、只加 `n=0` 剩 5。
- 套件：135 次推薦 14 次 404（不重複 9 個：chinese-jieba, dateutil, iqrst, pytaxi, python-chinese, python-pyzod, python-qi, thefine, thefp）；
  「驗證台灣身分證字號」推薦 pytz／openpyxl／lxml 等存在但無關的套件。
- 金鑰：10 次中 hardcoded 3（都是 `YOUR_API_KEY_HERE` 類佔位字串）、env 5、none 2；5 份用 `openai.ChatCompletion.create`。
- Hero 固定用 `round_half_up` 第 5 次重跑（index 4）。**page_content.py 的 `VERDICT` 文字是針對這一題寫的**
  （「8 次重跑裡有 3 次」「24 次重抽」），換 hero 題目要一起改。

## 外部事實（2026-09-24 查證）

- Claude Code 官方最佳實務 <https://code.claude.com/docs/en/best-practices>：第一條「Give Claude a way to verify its work」、
  plan mode（Shift+Tab）、hooks 是 deterministic（Stop hook 擋收工；連續擋 8 次會被覆蓋）、worktrees 平行、
  subagent 獨立審查、「corrected more than twice → /clear」。
- AGENTS.md：<https://agents.md/>，Agentic AI Foundation（Linux Foundation）維護；Claude Code 文件 memory 頁寫明可讀 AGENTS.md。
- Olausson et al., *Is Self-Repair a Silver Bullet for Code Generation?*, ICLR 2024（arXiv 2306.09896）。
- Spracklen et al., USENIX Security 2025（arXiv 2406.10279 v3 全文）：16 模型、57.6 萬份程式碼樣本、引用 223 萬個套件名其中 440,445 個（19.7%）不存在、不重複 205,474 個；重跑 10 次 43% 每次重現、58% 重現超過一次。
  注意：不少二手文章寫成「223 萬份樣本、19.7% 的樣本含幻覺」，是誤讀，以論文原文為準。
- Churilov, arXiv 2605.17062（2026-05／08）：新一代模型 4.62%–6.10%，127 個五模型共同幻覺名。
- `pip install dateutil`（pip 26.2.1）與斷網時的輸出都實跑過：斷網也以 `from versions: none` 收尾，但前面有 `Retrying … NewConnectionError`。
- openai 3.19.2：`openai.ChatCompletion` → `APIRemovedInV1`（實跑）。
- Ollama library 有 `qwen3.5:2b`（2.7GB）。**帶回家路徑（Ollama＋spike）沒有實跑驗證**，頁面已寫明。
- 本站 git 歷史：2026-08-06 至 2026-09-24 共 43 commit、39 個含 `Co-Authored-By: Claude`（本課寫作當下，之後會變）。

## 踩到的坑

- **第一版設計失敗**：題目給完整規格 docstring 時，qwen3.5-2b 失敗的都是「演算法寫不出來」，錯誤訊息幫不上，
  四種條件全部 0 救回。改成「一句話需求＋細節只在測試裡」（真實 vibe coding 的樣子）後，回饋才有資訊量可用。
- **thinking 模式不能當修復條件**：2B 模型開 thinking 常跑到 8192 token 上限（`finish=length`，每次約 118 秒），content 為空。
- **本機沙盒**：AppArmor `kernel.apparmor_restrict_unprivileged_userns=1` → `unshare -rn`、`bwrap --unshare-net` 都失敗。
  改用子行程＋暫存目錄＋timeout 30s＋rlimit（CPU 10s／AS 1GB／FSIZE 1MB）＋conftest 封 socket＋清空 env。不是資安邊界。
- **瀏覽器重算與 pytest 對不上的兩個原因**（已修，pack 會擋）：`datetime.strptime` 會延遲 import `_strptime`（白名單要放行 `_` 開頭的標準庫內部模組）；
  有的 AI 程式多 `import pytest` 卻沒用（給空模組）。另外 JSON 沒有 tuple（`top_k_words` 期望值要 `tuple_fix`）、
  有的程式在模組層 `print`（`redirect_stdout` 吞掉）。
- 51/1537 次生成 `finish=length`（1536 token 截斷）；`extract_code` 會處理沒收尾的 ``` fence，截斷的程式照樣交給測試。
- 區網 vLLM 同時被其他課的 spike 使用，同一批請求的耗時從 1 分鐘到 15 分鐘不等；重跑前確認併發總量 ≤4。
- 實驗場的「秒數」是當時的生成時間，受共用負載影響，只當相對參考。
