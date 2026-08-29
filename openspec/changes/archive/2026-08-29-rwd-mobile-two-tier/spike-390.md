# task 1.1 風險驗證結論（390×844，現況 dist，kv-cache）

- marimo `width="medium"` 在 390px **無橫向溢出**（scrollWidth 390 = innerWidth 390）；
  內容欄自動貼合、滑桿等互動元件全寬可用。唯一超寬元素是 marimo 的 code 輸出（613px），
  在自己的捲動容器內、不撐頁面。→ **不需要 nb 端 CSS 微調，design 方案照走。**
- matplotlib 圖渲染寬 354px（原生 1459–1819px）：單張長條圖尚可辨識，
  確認密圖（figsize 寬 ≥9、1×2 subplot）為回修對象（D7 範圍不變）。
- 課程頁 header 在 390px 嚴重擠壓裁切（固定 52px 高 × 5 元素），確認 2.3 必要。
- 截圖：/tmp/rwd-spike/（nb-390-top.png、nb-390-mid.png、page-390-top.png）
