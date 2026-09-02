# 課程影片：page_content 宣告、hero 標題後自動嵌入

## Why

課程開始錄影（llm-apps 十課已上傳 YouTube）。既有做法是每課手貼一段 `<section id="video">`
到 WRAP，十課十份重複標記，之後改嵌入方式要動十個檔；而且影片放在哪一個位置沒有契約，
每課可能不一樣。影片是課程內容的一部分，來源應該跟標題、簡介一樣宣告在內容正本。

## What Changes

- `page_content.py` 新增選填常數 `VIDEO`（YouTube 網址或 id）；`page-fill.py` 有看到就把
  `.video-box`（youtube-nocookie 嵌入、lazy、16:9，版型與樣式沿用既有共用 CSS）插在 hero 的
  `</h1>` 之後——教學欄開頭：標題先、影片接著。WRAP 已含 `video-box`（手動放別處）則不重複插。
- spec 新增「課程影片（可選）」requirement：位置、嵌入方式、無影片的課不受影響。
- make-lesson skill（page.html／page_ext.html 模板註解、site.md、engineering.md）同步；
  `video/` 新增 YouTube 上傳工具與 README（不部署、不進 build）。
- llm-apps 十課 page_content.py 加 `VIDEO`，重跑 page-fill。

## Impact

- `.claude/skills/make-lesson/scripts/page-fill.py`（管線；未定義 VIDEO 的課輸出完全不變）
- `content/llm-apps/*/page_content.py`、`index.html`（十課）
- `openspec/specs/interactive-lesson/spec.md`、make-lesson references／templates
- 共用 CSS 不動（`.video-box` 既有）
