// WASM 冒煙測試：開啟匯出的 marimo notebook，等 Pyodide 載入 + 全部 cell 執行，
// 驗證無錯誤輸出、圖表有渲染。用法：node smoke-test.mjs <url>
// （playwright 暫借既有專案的安裝；skill 化時改為本專案自帶依賴）
import { createRequire } from "node:module";
const require = createRequire(
  "/home/sk/work/demo-videos/2026-07-17-stock-demo/package.json",
);
const { chromium } = require("playwright");

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

// 1) 等 marimo 前端出現（標題 markdown 渲染出來；避開 <title>，等可見的 h1）
await page.waitForSelector('h1:has-text("決策樹互動實驗室")', {
  timeout: TIMEOUT_MS,
  state: "visible",
});
console.log(`markdown rendered at +${((Date.now() - t0) / 1000).toFixed(1)}s`);

// 2) 等 Python cell 真正跑完：matplotlib 圖以 <img>/<canvas> 出現在輸出區
//    lesson.py 有 4 張圖（散佈、直方、樹、邊界、過擬合曲線 = 5 張）
await page.waitForFunction(
  () => document.querySelectorAll("img, canvas").length >= 4,
  null,
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
