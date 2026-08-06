# interactive-lesson — delta（add-sft-lesson）

## ADDED Requirements

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
