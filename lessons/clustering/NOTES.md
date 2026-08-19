# clustering 建課筆記

2026-08-19 以 make-lesson skill 建課（基礎機器學習三課系列 03）。

## 踩坑

- **KMeans 特徵尺度**：來店次數（個位數）對消費（百位數）→ 先 `StandardScaler`
  再分群；畫圖時中心用 `scaler.inverse_transform` 換回原單位，圖才對得上散點。
- `KMeans(n_init=10)` 顯式給定，避免不同 sklearn 版本的預設值 warning。
- marimo 釘版坑同 classification/NOTES.md。

## 已驗證的教學宣稱（seed=11）

- inertia：180→95→20→14→12…手肘明顯在 k=3。
- k=3 分出 30/30/30，與生成的三群一致（左頁「跟你眼睛看到的幾乎一樣」）。
