# interactive-lesson

## Purpose

定義「AI 生成互動教學課」的可觀察行為：一個純網址分享的教學頁，左側是教學解說、右側是學員可即改即跑的 marimo notebook，全程無帳號、無後端、無安裝。

## Requirements

### Requirement: 純網址分享，無後端依賴

課程頁 SHALL 以純靜態資產組成，透過單一公開網址開啟後即完整可用；除靜態檔案託管與 Pyodide/套件 CDN 之外，SHALL NOT 依賴任何自建後端服務或登入機制。

#### Scenario: 學員首次開啟

- **WHEN** 學員在現代桌面瀏覽器開啟課程網址
- **THEN** 頁面載入左側教學內容與右側 notebook，無任何登入或安裝步驟

### Requirement: 左右對照版面

課程頁 SHALL 同時呈現左側教學解說與右側可執行 notebook，讓學員可以邊讀解說邊操作程式碼。

#### Scenario: 桌面瀏覽

- **WHEN** 學員以桌面寬度視窗開啟課程頁
- **THEN** 左側為可捲動的教學解說、右側為內嵌的 marimo notebook，兩側各自獨立捲動

### Requirement: 學員可改可跑且互相隔離

右側 notebook SHALL 允許學員直接編輯程式碼並重新執行（瀏覽器內執行）；任一學員的修改 SHALL NOT 影響其他學員或原版課程內容。

#### Scenario: 學員修改參數重跑

- **WHEN** 學員修改某個 cell 的程式碼（例如決策樹深度）並重新執行
- **THEN** 該學員的瀏覽器內即時反映新結果，其他人開啟同一網址仍看到原版

#### Scenario: 重新整理回到原版

- **WHEN** 學員做了任意修改後以全新分頁重新開啟課程網址
- **THEN** 看到的是原版 notebook 內容

### Requirement: 學員可下載 notebook 帶走

課程頁 SHALL 提供學員取得 notebook 原始 `.py` 檔的途徑，讓學員能在自己的環境（本機 marimo 或雲端服務）延續修改。

#### Scenario: 下載原始碼

- **WHEN** 學員操作下載入口
- **THEN** 取得可直接以 marimo 開啟的 `.py` 檔案

### Requirement: 教學內容與程式碼一致

左側教學解說中對程式行為的描述 SHALL 與右側 notebook 實際可執行的內容一致；解說 SHALL NOT 描述 notebook 中不存在或不會發生的行為。

#### Scenario: 對照學習

- **WHEN** 學員依左側解說指示到右側操作對應的 cell 或互動元件
- **THEN** 右側確實存在該 cell 或元件，且執行結果與解說描述相符

### Requirement: 發布前雙層驗證

每一課發布前 SHALL 通過兩層驗證：notebook 在本機 Python 環境完整執行無錯，且匯出後的瀏覽器（WASM）版本在實際瀏覽器中載入並執行無錯。

#### Scenario: WASM 版驗證失敗即擋下發布

- **WHEN** 匯出後的 WASM 版在瀏覽器中有 cell 執行錯誤（例如套件不相容）
- **THEN** 該課不得發布，需修正後重新驗證

### Requirement: GPU 延伸軌道

當課程內容需要瀏覽器無法提供的算力（例如 GPU 訓練）時，課程頁 SHALL 提供外部 GPU 執行路徑：學員以自己的帳號在外部 marimo 雲端服務（molab）開啟指定 notebook、選擇 GPU 伺服器執行。課程頁 SHALL 清楚標示 GPU 軌道的入口與操作步驟（登入 → 取得自己的副本 → 選擇 GPU → 執行），並 SHALL 提供該 notebook 的 `.py` 原始檔下載作為替代途徑。GPU 軌道為延伸而非前提：課程的核心概念教學仍 SHALL 完整維持於瀏覽器內可跑的軌道。

#### Scenario: 學員走 GPU 軌道

- **WHEN** 學員在課程頁點擊 GPU 軌道入口
- **THEN** 於新分頁開啟外部 marimo 雲端服務上的指定 notebook，學員登入自己的帳號後可取得自己的副本並選擇 GPU 伺服器執行；本課程站不經手學員帳號與執行狀態

#### Scenario: 學員不使用 GPU 軌道

- **WHEN** 學員只在瀏覽器內完成課程、不開啟 GPU 軌道
- **THEN** 課程的概念教學與所有瀏覽器內互動實驗仍完整可用，學員可理解本課全部核心概念

#### Scenario: 外部服務不可用

- **WHEN** 外部 marimo 雲端服務無法連線或學員無法登入
- **THEN** 課程頁的教學內容與瀏覽器軌道不受影響，且學員仍可下載 GPU notebook 的 `.py` 檔於任何有 GPU 的環境自行執行

#### Scenario: 右欄 GPU 分頁

- **WHEN** 學員於課程頁右欄切換到 GPU 分頁
- **THEN** 右欄顯示 GPU 軌道導流面板——操作步驟（登入 → 取得副本 → 選 GPU → 執行）與行動入口（新分頁開啟課程 notebook、登入、下載 `.py`）——且切換分頁不影響瀏覽器軌道 notebook 的既有狀態（外部服務以新分頁開啟：實測其登入狀態與內容渲染均無法在內嵌框架中運作）
