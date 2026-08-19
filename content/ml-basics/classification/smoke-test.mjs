// WASM 冒煙測試模板：cp 到 lessons/<id>/smoke-test.mjs，改頂部兩個常數。
// 開啟匯出的 marimo notebook，等 Pyodide 載入 + 全部 cell 執行，
// 驗證無錯誤輸出、圖表有渲染。用法：node smoke-test.mjs <url>
// （playwright 是 repo 根目錄的 devDependency：npm install 即得）
import { chromium } from "playwright";

const H1_TEXT = "分類：教機器做判斷"; // notebook 第一個 md cell 的 h1 片段
const MIN_FIGURES = 3;               // 全部 cell 跑完的 matplotlib 圖數

const url = process.argv[2] ?? "http://127.0.0.1:8787/index.html";
const TIMEOUT_MS = 240_000;

const t0 = Date.now();
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 900, height: 1400 } });

const consoleErrors = [];
page.on("console", (msg) => {
  if (msg.type() === "error") consoleErrors.push(msg.text().slice(0, 300));
});
page.on("pageerror", (err) => consoleErrors.push(`pageerror: ${err.message}`));

console.log(`opening ${url} ...`);
await page.goto(url, { waitUntil: "domcontentloaded", timeout: 60_000 });

// 1) 等 marimo 前端出現（text=中文 會撈到隱藏 <title>，要等「可見的 h1」）
await page.waitForSelector(`h1:has-text("${H1_TEXT}")`, {
  timeout: TIMEOUT_MS,
  state: "visible",
});
console.log(`markdown rendered at +${((Date.now() - t0) / 1000).toFixed(1)}s`);

// 2) 等 Python cell 真正跑完：matplotlib 圖以 <img>/<canvas> 出現在輸出區
//    （waitForFunction 的 options 是第三參數——放錯位置逾時會默默變 30s）
await page.waitForFunction(
  (min) => document.querySelectorAll("img, canvas").length >= min,
  MIN_FIGURES,
  { timeout: TIMEOUT_MS },
);
const tReady = ((Date.now() - t0) / 1000).toFixed(1);
console.log(`figures rendered at +${tReady}s`);

// 3) 額外緩衝讓尾端 cell 收尾，再抓錯誤狀態
await page.waitForTimeout(5000);

const bodyText = await page.evaluate(() => document.body.innerText);
const errSignals = ["Traceback (most recent call last)", "ModuleNotFoundError", "This cell raised an exception"];
const hits = errSignals.filter((s) => bodyText.includes(s));

const imgCount = await page.evaluate(
  () => document.querySelectorAll("marimo-cell-output img, .output-area img, marimo-cell-output canvas").length,
);

await page.screenshot({ path: "smoke-screenshot.png", fullPage: false });
await browser.close();

console.log("---- smoke result ----");
console.log(`ready in           : ${tReady}s`);
console.log(`figure outputs     : ${imgCount}`);
console.log(`error text hits    : ${hits.length ? hits.join(" | ") : "none"}`);
console.log(`console errors     : ${consoleErrors.length}`);
consoleErrors.slice(0, 5).forEach((e) => console.log(`  · ${e}`));

if (hits.length > 0) {
  console.log("RESULT: FAIL");
  process.exit(1);
}
console.log("RESULT: PASS");
