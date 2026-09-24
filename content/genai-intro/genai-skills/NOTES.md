# genai-skills（補充 E：Agent Skills）NOTES

## 定位

- 延伸主線 genai-agents 第 4 節「生態系名詞」只點名過的 Agent Skills。純瀏覽器 app 模式（主題層 `lesson-mode=app`）。
- 範圍邊界：Agent SDK 程式介面歸補充 C（/genai-agent-sdk/）、MCP 歸補充 D（/genai-mcp-fastmcp/）、
  Claude Code 開發實務歸補充 F（/genai-vibecoding/）。本課只在「選型」表連過去，不展開。
- 觀看者零服務：notebook 只用 numpy／matplotlib／pyyaml（Pyodide 內建；marimo 本身也依賴 pyyaml，CPython 端不用加依賴）。

## 素材來源（全部 2026-09-24 實測）

一支 spike 分段跑：`content/genai-intro/_spikes/spike_genai_skills.py <段名>`，輸出寫 `$SPIKE_OUT`（預設 `./genai_skills_out`），
**在 repo 外的暫存目錄當 cwd 跑**（玩具專案會建在 `$SPIKE_OUT` 底下）。

| 段 | 需要 | 產出 | 課文用在哪 |
|---|---|---|---|
| `tokens` | 無（tiktoken 0.14.0 `o200k_base`） | 本 repo `.claude/skills/` 9 個 skill 每檔 token、字元→token 擬合係數 | 1️⃣ 表格與圖、2️⃣ 計算器、教學頁 s2 表 |
| `validate` | 無（skills-ref 0.1.1） | 官方驗證器對 repo skill 與 11 個範例的真實訊息；課內移植版逐條比對（只有 YAML 錯誤的第 2 行起細節不同） | 5️⃣ 驗證器、quiz Q2 |
| `overhead` | 已登入的 `claude` CLI | 裝 0／1／9 個 skill 的每輪 input tokens、叫 make-lesson 後的增量、`--debug-file` 的 listing 超預算警告、寬容 YAML 測試 | 2️⃣ 表、教學頁 s2、5️⃣ 末段 |
| `trigger` | `claude` CLI | 3 版 description × 12 prompt × 3 次（`TRIG_TURNS=2`，只看前 2 回合） | hero、3️⃣ 熱圖／重播、quiz Q3 |
| `exemplar` | `claude` CLI | 精準版完整跑一次（允許 Skill／Read／Glob／`Bash(python3 *)`） | 4️⃣ 重播 |
| `mental-claude` | `claude` CLI | haiku 不准用工具心算 36 筆 × 5 次 | 4️⃣ 表與圖 |
| `local` | env `LLM_URL`（預設 `http://localhost:11434/v1`）、`LLM_MODEL`（必填）、`LLM_API_KEY`（選填） | 最小 skill loader 的觸發紀錄、完整 loader trace、小模型心算 | hero 的 qwen 組、3️⃣、4️⃣ |
| `inject` | 上面的 JSON | 寫進 `lesson.py` 的 `DATA` 區塊、`page_content.py` 的 `HERO` 區塊（路徑與本機帳號名會被清掉） | — |

- Claude 模型：`claude-haiku-4-5`（env `CLAUDE_MODEL` 可換），Claude Code **2.1.281**，一律
  `--setting-sources project --strict-mcp-config --no-session-persistence --permission-prompts none`，
  使用者自己的 skills／plugins／CLAUDE.md 不會混進來（init 訊息的 skills 清單只剩內建 18 個）。
- 小模型：`qwen3.5-2b`（區網 vLLM，OpenAI 相容；端點只從 env 給，**不寫進任何檔案**）。
  Ollama 路徑是同一個介面、**沒有實測**——教學頁照實這樣寫。
- 花費：claude CLI 全部（含探路、pilot、正式、exemplar、心算）約 **US$3.40 list price**；trigger 正式那組 US$2.64。

## 課文引用的關鍵數字（換模型／改版時要重驗的句子）

- tokens（o200k_base，檔案會隨 repo 演進而變——重跑 `tokens`＋`inject` 後，教學頁 s1／s2 的手寫數字要同步）：
  make-lesson L1 156／L2 4,189／L3 42,028；9 個 skill L1 合計 561（8 個可被模型叫）、SKILL.md 合計 20,695、L3 合計 51,717、全部 72,412；
  make-lesson 有 2 references／9 scripts／8 templates；publish-videos 3 支腳本 7,037 tokens。
- Claude Code 實測（haiku-4-5）：基準 21,012；+make-lesson 198、+publish-videos 212、+9 個 468；叫 make-lesson 後 26,856（+5,376；
  另一次跑是 26,818，差在模型自己講的話）；debug log「Skill listing over budget: 21 skills, 8210 chars > 8000 budget」。
- 觸發（haiku-4-5）：模糊版 12/18 命中、0 誤觸發（s4 英文 0/3、s2 1/3、s6 2/3）；精準版 18/18、0；太寬版 18/18、1/18（n2 請假信）。
  沒載入 skill 時自己寫的總工時：128.5（vague s2 #3）、141（vague s4 #2）、138（vague s4 #3），正解 141。
- 觸發（qwen3.5-2b 最小 loader）：模糊版與太寬版 36/36 全叫；精準版 17/18 命中、10/18 誤觸發。
- 心算：qwen3.5-2b 15 次 0 次四專案全對；haiku 5 次 3 次全對（錯的兩次：內部維運 11、會員 51／客服 37.5）。
- exemplar：haiku 照 SOP 跑 hours.py、讀 timesheet、讀 template，**沒讀** style-guide（第 4 步）；qwen loader 跑了腳本但跳過讀 note 欄。
  這兩句寫死在 lesson.py 4️⃣ 的 md 與教學頁 s4——重跑 exemplar／local 後要重看 trace 再改。
- 3️⃣ 的「幾個值得停下來看的格子」與教學頁 s3 的表、quiz Q3 都是照上面 trigger 結果手寫的——**trigger 重跑後必改**。
- 規格與生態（2026-09-24 查）：agentskills.io 規格欄位與上限；client showcase 46 個產品；Claude Code listing 預算＝context 的 1%、
  description＋when_to_use 截在 1,536；Gemini CLI 免費使用 2026-06-18 停止（Google Developers Blog 2026-05-19 公告，改 Antigravity CLI）。

## 踩到的坑

- **PyPI 的 skills-ref 0.1.1 執行檔叫 `agentskills`**，不是文件寫的 `skills-ref`（`uvx --from skills-ref skills-ref ...` 會報
  「An executable named `skills-ref` is not provided」）。
- **官方驗證器 vs Claude Code 解析差很多**：`description: Use when: ...`／`用途: 產生週報: 每週五用`（未加引號的冒號＋空格）
  skills-ref 判 `Invalid YAML`，Claude Code 2.1.281 照樣把整串字當 description；連 `[unclosed list` 都吃。
  `claude plugin validate .claude/skills` 對這兩種也回 `✔ Validation passed`——想抓 YAML 錯請用 skills-ref。
- 官方驗證器允許 Unicode 字母當 name（`週報` 會過），但規格文字寫 a-z／0-9、Claude API 要求小寫英數——驗證器的「跨產品提醒」有寫。
- 本 repo 的 grill-me 用了 `disable-model-invocation`（Claude Code 擴充）→ 官方驗證器不過；它不會出現在模型的 listing（`all9` 只多 8 個描述）。
- `--permission-prompts none` 下 Bash／Write／Edit 會被自動拒絕，但 `ls -la` 這類唯讀指令照跑——trace 會印出本機帳號名，
  `inject` 的 `clean()` 用 `getpass.getuser()` 換成 `user`（不要把帳號名硬寫進 spike）。
- 小模型 loader 的兩個真實坑（已修，留作教材）：模型在 JSON 前後多講幾句話 → 要從整段輸出裡找 JSON；
  工具結果回給它之後會**連續 5 次要求同一個 run** → 加「做過的動作不再執行」護欄＋「請照 SOP 繼續下一步」提示。
- trigger 用 `--max-turns 2` 省額度：決定叫不叫 skill 幾乎都在第一個動作；少數是先 `Read` 才叫（vague s2 #1、vague s6 #3），2 回合內都抓得到。
- 教學頁的 hero 資料與 lesson.py 的 DATA 都由 spike `inject` 寫入；手改會在下次 inject 被蓋掉。

## 重驗流程

```bash
cd <repo 外的暫存目錄>
export SPIKE_OUT=$PWD/out
uv run --script <repo>/content/genai-intro/_spikes/spike_genai_skills.py tokens
uv run --script <repo>/content/genai-intro/_spikes/spike_genai_skills.py validate
uv run --script <repo>/content/genai-intro/_spikes/spike_genai_skills.py overhead        # claude CLI，約 US$0.05
REPS=3 PAR=4 uv run --script <repo>/content/genai-intro/_spikes/spike_genai_skills.py trigger   # 約 US$2.6，15 分鐘
uv run --script <repo>/content/genai-intro/_spikes/spike_genai_skills.py exemplar
uv run --script <repo>/content/genai-intro/_spikes/spike_genai_skills.py mental-claude
LLM_URL=... LLM_MODEL=... uv run --script <repo>/content/genai-intro/_spikes/spike_genai_skills.py local
uv run --script <repo>/content/genai-intro/_spikes/spike_genai_skills.py inject
python3 .claude/skills/make-lesson/scripts/page-fill.py content/genai-intro/genai-skills
```

然後對照上面「關鍵數字」逐句改 page_content.py 與 lesson.py 的手寫觀察。
