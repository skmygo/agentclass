# 站級包裝：訊號、回報入口、分享門面（SEO/OG）

## Why

課內教學品質高，但站級包裝近乎零：全站無 analytics（教學決策盲飛）、無回報入口
（學員遇到問題只能默默離開）、無 og/meta/favicon（分享連結是裸的）、無 sitemap/robots
（搜尋引擎半盲）、13 堂課 brand 全寫死「AI 互動教室 · 機器學習」（含 10 堂 LLM 課）、
上鎖課的密碼牆不露任何課程資訊（招牌菜不在櫥窗裡）。

## What Changes

- **Cloudflare Web Analytics（免 cookie）**：build.sh 統一注入 beacon（`ANALYTICS_TOKEN`
  常數，留空不注入；只注入頁面、不注入 nb iframe 避免重複計數）。content 原始碼保持乾淨。
- **回報入口**：13 堂課 header 加「留言回報」tool 連結 → blog 留言板。
- **footer**：首頁與主題頁的「本站不收集任何資料」改為 YouTube 頻道＋部落格連結。
- **分享門面**：全站 og:title/og:description/og:url/og:image + twitter:card + favicon.svg；
  共用 og 封面圖 `/shared/og-cover.png`；首頁補 meta description。
- **SEO**：build.sh 產 sitemap.xml + robots.txt（正準網址 agentclass.pages.dev）。
- **brand 修正**：課程頁 header 品牌文字統一「AI 互動教室」（去掉錯掛的「· 機器學習」）。
- **gate 覆蓋層**：露出課名與課程簡介（來自頁面 title/meta），密碼牆同時是櫥窗。
- **管線同步**：page.html／page_ext.html／topic.html 模板同步；page-fill.py 增填 og 三欄
  （TITLE/DESCRIPTION 改了 og 跟著改）。

## Impact

- `scripts/build.sh`、`content/shared/`（gate.js、topic.css、favicon.svg、og-cover.png）
- `content/index.html`、兩主題頁、13 堂課 index.html（head＋header，皆在 page-fill 替換區之外）
- make-lesson 模板 ×3、`page-fill.py`
- spec 不變：密碼閘「看不到底下內容」仍成立（課名／簡介顯示在覆蓋層上，非底下內容）
