# regression 建課筆記

2026-08-19 以 make-lesson skill 建課（基礎機器學習三課系列 02）。

## 踩坑

- **殘差方向寫反過一次**：凸型資料（銷量 ∝ 溫差²）配直線，是「兩端猜太低、
  中段猜太高」（資料在線上方），初版寫成反向，靠人工推導抓到——左頁的物理宣稱
  要先驗證再寫。
- **高次多項式數值爆炸**：直接對原始溫度（14–36）取 15 次方會 overflow →
  pipeline 先 `MinMaxScaler` 再 `PolynomialFeatures`。
- marimo 釘版坑同 classification/NOTES.md。

## 已驗證的教學宣稱（seed=7、split random_state=3）

- 測試誤差最低在次數 2（30），之後回升到 ~43；訓練誤差單調下降 246→54。
- 次數 15 對 40°C 外插給出 **-3930 杯**（LEVEL 1 挑戰的「負銷量」宣稱）；
  次數 2 給 241 杯、次數 12 給 1024 杯（LEVEL 2）。
