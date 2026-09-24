# 換機／在別台電腦接手 agentclass

> **這個 repo 是公開的**（molab 直讀 GitHub main）。本檔與 repo 裡任何檔案都不能放金鑰、token、內網 IP、帳密；
> 那些東西的位置寫在這裡，內容放私人的地方。

## 結論先講

- **部署不依賴 homelab**：網站是純靜態，`scripts/build.sh` 組出 `dist/`，`wrangler pages deploy` 直傳
  Cloudflare Pages（project `agentclass`，網域 `class.itsmygo.uk`）。任何電腦登入同一個 Cloudflare 帳號就能部署。
- **Pages 沒連 GitHub**：push 不會觸發部署，deploy 一律手動跑。反過來，molab 課改完**一定要 push**（molab 讀 main）。
- **上線後有 5 堂課依賴 homelab**（見「執行期依賴」），homelab 停機時網站照常、只有那 5 堂的 LLM 呼叫會失敗。

## 新電腦步驟

### 1. 工具與環境

| 工具 | 用途 | 舊機版本（參考） |
|---|---|---|
| git + `gh` | clone／push（GitHub 帳號 `skmygo`） | |
| `uv` | Python 環境；`requires-python >=3.14`，uv 會自己裝 Python | 0.11.7 |
| Node.js + npm | `npx wrangler` 部署、headless Playwright 冒煙 | v24.15.0 |

```bash
git clone https://github.com/skmygo/agentclass.git && cd agentclass
uv sync                              # 依 uv.lock 安裝；marimo 釘 0.23.16，版本一飄 WASM assets 就無法共用
npm install                          # Playwright（冒煙用）
npx playwright install chromium      # 全新 Linux 加 --with-deps
```

### 2. Cloudflare 登入（部署用）

```bash
npx wrangler login                                   # 登入擁有 Pages project「agentclass」的帳號
npx wrangler pages project list | grep agentclass    # 看得到才算成功
```

- 沒桌面的機器：`wrangler login` 授權後會導回 `localhost:8976`，在有瀏覽器的電腦先開
  `ssh -L 8976:localhost:8976 <新機器>` 再登入。
- 或不用 OAuth，改設環境變數 `CLOUDFLARE_API_TOKEN`（權限至少 Account › Cloudflare Pages › Edit）＋ `CLOUDFLARE_ACCOUNT_ID`。
- 舊機的登入存在 `~/.config/.wrangler/`，不用搬，新機器重登即可。

### 3. YouTube 上傳憑證（只有要發影片才需要）

`video/client_secret.json`、`video/token.json` 已 gitignore，**永遠不要 commit 進這個 repo**——
token 的 scope 是 `youtube`，拿到的人可以完整管理頻道（包含刪影片）。

備份在**私人 repo `skmygo/sk-plugins` 的 `secrets/agentclass/video/`**：

```bash
# 裝過 sk-plugins marketplace 的機器（先 claude plugin marketplace update sk-plugins 拉最新）
cp ~/.claude/plugins/marketplaces/sk-plugins/secrets/agentclass/video/*.json video/
# 或直接從私人 repo 拿
gh repo clone skmygo/sk-plugins ~/sk-plugins && cp ~/sk-plugins/secrets/agentclass/video/*.json video/

chmod 600 video/*.json
uv run video/upload.py --check-auth    # exit 0＝可用；exit 3＝要重新登入
```

- 2026-09-24 驗證過：`--check-auth` 通過，refresh token 從 09-10 用到現在沒過期（沒有測試模式的 7 天期限）。
- token 失效時：刪掉 `video/token.json`，跑 `uv run video/upload.py --login`（沒桌面加 `--no-browser`，
  並開 `ssh -L 8090:localhost:8090`，細節見 `video/README.md`），**再把新的 token.json 覆蓋回 sk-plugins 備份並 push**。

### 4. Claude Code 環境

- repo 內的 skill（`make-lesson`、`publish-videos`）與 OpenSpec 指令都在 `.claude/`，跟著 git 走。
- CLAUDE.md 裡「憑證見 homelab-infra skill」指的是 user scope 的 homelab plugin，要另外裝：

  ```bash
  claude plugin marketplace add skmygo/sk-plugins
  claude plugin install homelab@sk-plugins
  ```

- fastmcp4-auth 課示範用的 `banqiao-weather` MCP 註冊在舊機 `~/.claude.json` 的 local scope，不會跟 repo 走；
  要用就重跑 `claude mcp add`（指令與 token 見 homelab-infra skill 的 `mcp.itsmygo.uk` 條目）。

### 5. 驗證後才部署

```bash
git pull                                                         # ⚠️ 先確認是最新 main
bash .claude/skills/make-lesson/scripts/smoke-all.sh --build     # build + 起 server + 全站冒煙
npx wrangler pages deploy dist --project-name=agentclass
bash .claude/skills/make-lesson/scripts/smoke-all.sh --base https://agentclass.pages.dev
```

**部署是拿本機 `dist/` 整包覆蓋線上**：在舊的 checkout 上 deploy 會把線上退回舊內容。
兩台電腦都能部署的期間，deploy 前一律先 `git pull`，改完一律 push。

## 只在舊電腦、不在任何 repo 的東西

| 路徑 | 內容 | 要怎麼處理 |
|---|---|---|
| `ref_data/`（約 24 MB，gitignore） | 私人參考教材；`mcp/` 是 `mcp.itsmygo.uk` 的 server 程式正本（含 `.env` token）；`litellm/` 是 gateway 的 config 正本 | **目前沒有任何備份**。換機前用 scp／rsync 搬走，或放進私人 repo；絕不能進這個公開 repo |
| `video/data/*.mp4`（約 192 MB） | 原始影片 | 已上傳 YouTube；要留原檔就另存 |
| `video/client_secret.json`、`video/token.json` | YouTube 憑證 | 已備份到 sk-plugins（見上面第 3 步） |
| `.venv/`、`node_modules/`、`dist/`、`.wrangler/`、`__marimo__/`、`.hypothesis/`、`preview-shots/` | 產物與快取 | 不用搬，重建即可 |

## 執行期依賴（網站上線之後）

- **純瀏覽器課（19 堂）**：在學員瀏覽器內用 Pyodide 執行，不依賴任何伺服器。
- **molab 課（25 堂）**：「在 molab 開啟」連到 `molab.marimo.io/github/skmygo/agentclass/blob/main/...`，
  **repo 必須維持公開**；轉私人，這 25 堂的 molab 連結就會失效。
- **5 堂 LLM 課依賴 homelab**：`litellm-basics`、`litellm-tools`、`qdrant-basics`、`rag-zh`、`rag-mcp-agent`
  寫死了 `https://litellm.itsmygo.uk/v1` 和教學用 virtual key。這個 gateway 跑在 homelab（Dokploy），
  homelab 停機或搬家時，這 5 堂的 LLM 呼叫會失敗。要脫鉤就改這幾課的 `BASE_URL`／`API_KEY`
  （`grep -rn litellm.itsmygo.uk content --exclude-dir=__marimo__`），`litellm-basics` 的 `page_content.py`
  改完要重跑 page-fill，然後 build、deploy、**push**（molab 課讀的是 GitHub 上的版本）。

## 如果連 Cloudflare 帳號也要換

- 新帳號建 Pages project；名稱不是 `agentclass` 的話，要改 `video/config.json` 的 `pages_project`、
  CLAUDE.md 與 make-lesson skill 裡的 `--project-name`。
- `class.itsmygo.uk` 要先從舊 project 移除，再加到新 project（`itsmygo.uk` 的 DNS zone 若也在舊帳號，要一起處理）。
- `scripts/build.sh` 的 `ANALYTICS_TOKEN`（Web Analytics，公開值、不是秘密）要換成新帳號的。
