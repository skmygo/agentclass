# interactive-lesson — delta（topic-order-and-topic-gate）

## MODIFIED Requirements

### Requirement: 網站導覽結構

排序規則由「主題列表與主題頁內的排序 SHALL 為越新越上」改為：
首頁主題列表 SHALL 越新越上；主題頁內的課程卡 SHALL 依課程順序排列（第 1 課在最上），
補充系列 SHALL 獨立成區、排在主線之後並依系列順序排列。

## ADDED Requirements

### Requirement: 主題密碼閘（可選）

主題 MAY 設定進入密碼。設定後，該主題頁與該主題所有課程頁 SHALL 在未解鎖狀態以不透明覆蓋層要求輸入密碼，輸入正確後 SHALL 於同一瀏覽器對整個主題保持解鎖。密碼閘 SHALL 為純前端輕量防護（無帳號、無後端、不收集資料，公開 repo 中僅存密碼雜湊、不存明碼），其目的為「不主動曝光」而非安全防護。密碼閘 SHALL NOT 阻斷頁面內容與 notebook 的載入（僅視覺遮蓋）。

#### Scenario: 未解鎖的訪客

- **WHEN** 訪客首次開啟已設密碼主題的主題頁或其任一課程頁
- **THEN** 看到覆蓋整個視窗的密碼輸入層；輸入錯誤密碼得到提示並可重試

#### Scenario: 解鎖一次全主題通行

- **WHEN** 訪客在該主題任一頁輸入正確密碼
- **THEN** 覆蓋層消失；同一瀏覽器再開該主題其他課程頁不再詢問

#### Scenario: 未設密碼的主題不受影響

- **WHEN** 訪客開啟未設密碼主題的頁面
- **THEN** 行為與密碼閘功能存在前完全相同
