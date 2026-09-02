# interactive-lesson — delta（lesson-video-hero）

## ADDED Requirements

### Requirement: 課程影片（可選）

課程 MAY 附一支課程影片。影片來源 SHALL 宣告在課程內容正本（`page_content.py` 的 `VIDEO`），
由建頁管線嵌入，頁面骨架不因有無影片而改變。有影片的課程頁 SHALL 在教學欄開頭
（hero 標題之後、導言之前）以 16:9 播放器呈現；嵌入 SHALL 走 `youtube-nocookie.com`
並延遲載入，不得把影片檔本身放進站內。沒有宣告影片的課程 SHALL NOT 出現影片區塊。

#### Scenario: 有影片的課

- **WHEN** 學員開啟一堂宣告了 `VIDEO` 的課程頁
- **THEN** 教學欄標題下方立即是 16:9 的 YouTube 播放器，之後才是導言與各節內容；手機版在「教學」分頁同樣位置

#### Scenario: 沒有影片的課

- **WHEN** 學員開啟一堂沒有宣告 `VIDEO` 的課程頁
- **THEN** 頁面與宣告機制加入前完全一致，沒有任何影片區塊或佔位

#### Scenario: 影片尚未公開

- **WHEN** 影片在 YouTube 仍是私人狀態
- **THEN** 播放器處顯示 YouTube 的不可播放訊息，頁面其餘內容與互動不受影響
