# interactive-lesson — delta（ready-signal-selector）

## ADDED Requirements

### Requirement: 載入就緒提示（純瀏覽器課）

純瀏覽器課的課程頁 SHALL 在 notebook 載入期間顯示載入中提示，並於 notebook 全部 cell
執行完成後轉為就緒狀態。就緒判定 SHALL 依課程宣告的訊號：預設為圖表數門檻，
無圖表輸出的課程 MAY 改宣告 DOM 訊號（元素 selector）。就緒機制 SHALL NOT
強制課程內容包含特定型態的輸出（如圖表）。

#### Scenario: 有圖課就緒

- **WHEN** 學員開啟純瀏覽器課，notebook 渲染出達宣告門檻數量的圖表
- **THEN** 載入提示轉為就緒狀態

#### Scenario: 無圖課就緒

- **WHEN** 一堂無圖表輸出的純瀏覽器課宣告了就緒 selector，notebook 執行完成後該元素出現
- **THEN** 載入提示轉為就緒狀態，體驗與有圖課一致
