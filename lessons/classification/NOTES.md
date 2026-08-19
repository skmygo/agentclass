# classification 建課筆記

2026-08-19 以 make-lesson skill 建課（基礎機器學習三課系列 01）。

## 踩坑

- **marimo 版本飄移害 assets 無法共用**：pyproject 寫 `marimo>=0.23.16` 會解到
  0.24.0，export 出的 assets hash 與全站共用基準（decision-tree 的 0.23.16）不一致，
  build.sh 退回獨立 assets，dist 從 28M 膨脹到 112M。修法：釘 `marimo==0.23.16`
  （skill 模板已同步改為釘版）。
- **kNN 特徵尺度**：重量（百位數）對直徑（個位數）會讓距離被重量一人說了算，
  分界線變垂直條紋 → pipeline 加 `StandardScaler`，nb 文案用一句自然話帶過。

## 已驗證的教學宣稱

- k=1 訓練準確率 100%（最近鄰是自己）；k=5 為 99.2%（頁面未引用此數字）。
