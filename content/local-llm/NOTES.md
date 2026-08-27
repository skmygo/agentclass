# local-llm 系列 NOTES

## 系列來源與去識別化（重要）

- 本系列改編自一份**私人演講投影片**（`ref_data/localllm/`，已 gitignore，不入版控）。
- **去識別化鐵則**：課程內容不得出現原講者身分、公司、內網資訊——
  公司名／內網 IP（10.*、192.168.*）／機器名／講者 email 與人名／公司政策（合規清單）／
  廠商評估（報價、會議紀錄、一體機）／`itsmygo.uk` 子網域服務。
  重驗或改課時同樣適用；部署前 `grep -rE "cht|中華電信|10\.131|itsmygo" content/local-llm/` 應零命中
  （blog 留言連結與 footer 的既有站台連結除外）。
- 原教材中**刻意跳過**的段落：公司合規政策、AI 工具採購建議、Token 退燒新聞、
  廠商（SSD 方案）商業評估細節、公司間對比。技術中立的結論（KV 記憶體估算、
  SSD 卸載適用場景、ZeRO-Infinity）已融入 kv-cache／kv-offload 課。

## 實測數字的引用約定

- 系列引用的實測數據來自原始教材的量測，文案統一標「實測（RTX 4090、<模型>[、日期]）」：
  - 冷啟動對照表（Ollama 8.3s vs vLLM 0.4s 等）：RTX 4090、Llama 3.1 8B Q4_K_M
  - LMCache TTFT 加速比 1.1x／1.2x／2.3x：RTX 4090、vLLM + LMCache 0.5.0、2026-07
- KV 記憶體數字**不沿用原教材概數**，用 notebook 精確重算（131,072 bytes/token，
  Llama 3 8B GQA）——原教材 0.128 MB/token 混用了 KiB/MB，spike 已釐清。
- 模擬互動（利用率、告警、接受率、計費）都是真計算；示意性參數要讓學員知道是教學模型。

## 定軌與重驗

- 全系列 8 課皆**純瀏覽器課**（numpy＋matplotlib，pyodide spike 通過）。
- `_spikes/spike_<id>.py` 一課一支，重驗起點；全部 `uv run --script` 可跑，含 assert。
- 課程順序：ollama-vs-vllm → sampling-params → kv-cache → prompt-caching →
  kv-offload → speculative-decoding → llm-observability → lora-basics。
- 快取費率（prompt-caching 課）綁 Claude Fable 5 公開定價，官方調價時要重驗三輪實算數字
  （spike 會 assert 失敗提醒）。

## 建課踩坑（2026-08-28 初版，8 課平行建置實錄）

- scaffold 課名不能含 `/`（sed 代換會炸）——「LoRA 與 SFT/DPO」改成「LoRA 與 SFT、DPO」。
- **講金額的課，`$…$` 會被 mo.md 當 LaTeX 吃掉**：md 字串內錢字號一律 `\$`（要插值用 `rf"""…"""`）。
  冒煙抓不到（無 Traceback、圖照畫），只有掃 `__marimo__/session/*.json` 渲染輸出才看得到殘骸。
- **引用簡報金額前先跑一次 Python 格式化**：`f"{0.2375:.3f}"` 是 `0.237` 不是 `0.238`
  （float64 略小於 .2375）——本課全部改 4 位小數，左頁/hero/notebook 三處同步。
- **KV 記憶體單位一開始就選定**：原教材同一張表混用 GiB 與十進位 GB；本系列統一走精確 bytes
  重算（kv-cache 課 GiB、kv-offload 課同一公式），別直接抄簡報數字。
- **教學模擬的指標要先驗「有沒有天花板」**：重複率用「1−相異/總長」會飽和看不出 penalty 效果，
  改「最常出現字佔比＋相異用字數」才分得開（sampling-params）。
- **玩具模型要挑對度量與位置編碼**：非前綴不能重用的演示，加性 PE＋cosine 只掉到 0.92 沒戲；
  RoPE＋相對誤差% 才拉出 0.0%/23%/99% 的對比（kv-cache）。
- **SVD 低秩演示的雜訊量級要先算**：雜訊 Frobenius 範數大過訊號時 r=1 與 r=16 幾乎沒差；
  並記得放一組純亂數對照（lora-basics）。
- **DPO 的 β 演示用封閉解 `π ∝ π_ref·exp(score/β)`**，不要用固定步數梯度下降
  （DPO loss 無有限最佳解，會教出與「β=懲罰強度」相反的結論）。
- **‖ΔW‖ 實際隨 α/√r 走**（縮放 α/r × BA 自身 √r 成長）——「r 減半力道加倍」成立，
  但文案不能寫「力道正比 α/r」。
- **滑桿範圍要涵蓋挑戰題要求的數字**（CPython export 抓不到這種錯）。
- **蒙地卡羅抽樣池要大於理論上限**，否則取樣上限會被誤當成結論（ollama-vs-vllm 併發掃描）。
- 課程頁自訂節內小標**要加 class**（如 `h3.sub`）：`#lesson h3` 裸標籤選擇器會以 ID 特異度
  蓋掉共用 `.quiz-q h3`，把測驗題標題弄壞。
- hero 的 CSS 記得給 inline 元素明寫 `display:block` 再設寬高（span 進度條白條 bug），
  **hero 一定要截圖看過**——冒煙與 DOM 檢查都測不到。
