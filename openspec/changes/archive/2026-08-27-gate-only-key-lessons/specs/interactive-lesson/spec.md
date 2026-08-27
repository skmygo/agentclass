# interactive-lesson — delta（gate-only-key-lessons）

## MODIFIED Requirements

### Requirement: 主題密碼閘（可選）→ 課程密碼閘（可選）

由主題層級改為課程層級：個別課程 MAY 設定進入密碼，原則是**程式或教學頁含教學 API key 的課才鎖**，
無敏感內容的課程與主題頁不鎖。同一密碼群組（通常＝同主題）任一頁解鎖後全群組通行。
其餘（純前端輕量防護、只遮不擋、明碼不進 repo）不變；Scenario 對象由「主題頁＋全部課程頁」
改為「已設密碼的課程頁」。
