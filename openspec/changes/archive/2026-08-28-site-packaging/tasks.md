# Tasks

- [x] build.sh：`BASE_URL`／`ANALYTICS_TOKEN` 常數、beacon 注入（僅頁面）、sitemap.xml、robots.txt
- [x] 共用資產：favicon.svg、og-cover.png（1200×630）、topic.css footer 連結色、gate.js 露課名＋簡介
- [x] 首頁＋兩主題頁：meta description、og/twitter、favicon、footer 改 YouTube＋Blog
- [x] 13 堂課：og/twitter/favicon 插入 head、brand 統一「AI 互動教室」、header 加「留言回報」
- [x] 模板同步：page.html／page_ext.html／topic.html；page-fill.py 增填 og:title/description/url
     （scaffold 實測：og:url 代換、brand、留言回報皆正確；page-fill 重跑冪等）
- [x] 驗證：build ＋ 全站冒煙 13 pass / 0 fail；sitemap 16 網址／robots 正確；
     gate 覆蓋層與首頁 footer 截圖確認
- [x] 使用者提供 beacon token → 填入 build.sh `ANALYTICS_TOKEN`（type=module 形式）→ 重 build 部署
