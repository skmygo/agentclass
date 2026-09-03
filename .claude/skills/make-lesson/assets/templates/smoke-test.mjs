// WASM 冒煙測試模板：cp 到 content/<topic>/<id>/smoke-test.mjs（scaffold 會代勞），改頂部兩個常數。
// 開啟匯出的 marimo notebook，等 Pyodide 載入 + 全部 cell 執行，
// 驗證無錯誤輸出、圖表有渲染。用法：node smoke-test.mjs <url>
// （playwright 是 repo 根目錄的 devDependency：npm install 即得）
import { chromium } from "playwright";

const H1_TEXT = "課程標題（實驗場）"; // 【必改】notebook 第一個 md cell 的 h1 文字（可只取片段）
const MIN_FIGURES = 1;               // 【必改】全部 cell 跑完至少會出現的 img/canvas 數量
const READY_SELECTOR = "";           // 無圖課用：全部跑完會出現的元素 selector（設了就取代圖表計數；
                                     // 與課程頁 <body data-ready-selector> 宣告同一訊號）

const url = process.argv[2] ?? "http://127.0.0.1:8787/index.html";
const TIMEOUT_MS = 240_000;

const t0 = Date.now();
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 900, height: 1400 } });

const consoleErrors = [];
// analytics beacon 從本機 origin 打 RUM 會被 CORS 擋——環境噪音，不是課程缺陷（正式網域不會發生）
const isBeaconNoise = (msg) =>
  /cloudflareinsights/.test(msg.text() + (((msg.location() || {}).url) || ""));
page.on("console", (msg) => {
  if (msg.type() !== "error" || isBeaconNoise(msg)) return;
  consoleErrors.push(msg.text().slice(0, 300));
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

// 2) 等 Python cell 真正跑完：預設等 matplotlib 圖以 <img>/<canvas> 出現在輸出區；
//    無圖課改等 READY_SELECTOR 元素出現（與課程頁 data-ready-selector 同一訊號）
//    （waitForFunction 的 options 是第三參數——放錯位置逾時會默默變 30s）
if (READY_SELECTOR) {
  await page.waitForSelector(READY_SELECTOR, { timeout: TIMEOUT_MS, state: "attached" });
} else {
  await page.waitForFunction(
    (min) => document.querySelectorAll("img, canvas").length >= min,
    MIN_FIGURES,
    { timeout: TIMEOUT_MS },
  );
}
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

// 4) 課末測驗在「教學頁」不在 nb 頁——從 nb URL 推回課程頁再驗：
//    題數 2–5、點第一題任一選項會出現回饋（gate 課用 DOM click() 繞過覆蓋層）
const lessonUrl = url.replace(/nb\/(index\.html)?$/, "");
const lp = await browser.newPage();
lp.on("console", (msg) => {
  if (msg.type() !== "error" || isBeaconNoise(msg)) return;
  consoleErrors.push(`lesson-page: ${msg.text().slice(0, 300)}`);
});
lp.on("pageerror", (err) => consoleErrors.push(`lesson-page pageerror: ${err.message}`));
await lp.goto(lessonUrl, { waitUntil: "load", timeout: 60_000 }); // 不用 networkidle：頁面有 YouTube 等第三方 iframe 時永遠不會 idle；後面自己輪詢就緒
const quiz = await lp.evaluate(() => {
  const count = document.querySelectorAll("#quiz .quiz-q").length;
  const btn = document.querySelector("#quiz .quiz-q .quiz-opt");
  if (btn) btn.click();
  const fb = document.querySelector("#quiz .quiz-q .quiz-fb");
  const fbShown = !!fb && getComputedStyle(fb).display !== "none";
  return { count, fbShown };
});
const quizOk = quiz.count >= 2 && quiz.count <= 5 && quiz.fbShown;

// 5) 手機 viewport（390×844）：版面結構 + 本課在手機上完整載入
//    結構＝無橫向溢出（頁面與教學 pane 兩層）、底部切換列存在、教學區不預載 notebook；
//    切到實作後：app 課直接開載、edit 課先出提示卡（確認後才載），最後等到就緒。
const mctx = await browser.newContext({
  viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true,
});
const mp = await mctx.newPage();
mp.on("pageerror", (err) => consoleErrors.push(`mobile pageerror: ${err.message}`));
await mp.goto(lessonUrl, { waitUntil: "domcontentloaded", timeout: 60_000 });
await mp.waitForSelector("#view-tabs", { timeout: 15_000 });
const mStruct = await mp.evaluate(() => {
  const lesson = document.querySelector("#lesson");
  return {
    pageOverflow: document.scrollingElement.scrollWidth - innerWidth,
    lessonOverflow: lesson.scrollWidth - lesson.clientWidth,
    tabsShown: getComputedStyle(document.querySelector("#view-tabs")).display !== "none",
    preloaded: !!document.querySelector("#nb-frame").getAttribute("src"),
    isApp: document.body.dataset.nbMode === "app",
  };
});
const mProblems = [];
if (mStruct.pageOverflow > 0) mProblems.push(`頁面橫向溢出 +${mStruct.pageOverflow}px`);
if (mStruct.lessonOverflow > 1) mProblems.push(`教學區內橫向溢出 +${mStruct.lessonOverflow}px`);
if (!mStruct.tabsShown) mProblems.push("底部切換列不可見");
if (mStruct.preloaded) mProblems.push("教學區就預載了 notebook（lazy load 失效）");
// gate 課有覆蓋層——用 DOM click() 繞過命中測試
await mp.evaluate(() => document.querySelector('#view-tabs button[data-view="lab"]').click());
if (!mStruct.isApp) {
  try {
    await mp.waitForSelector("#nb-notice button", { timeout: 10_000 });
    await mp.evaluate(() => document.querySelector("#nb-notice button").click());
  } catch { mProblems.push("edit 課切實作沒出提示卡"); }
}
if (mProblems.length === 0) {
  try {
    await mp.waitForSelector("#nb-status.ready", { timeout: TIMEOUT_MS });
  } catch { mProblems.push("手機上載入未達就緒"); }
}
const mobileOk = mProblems.length === 0;
await browser.close();

console.log("---- smoke result ----");
console.log(`ready in           : ${tReady}s`);
console.log(`figure outputs     : ${imgCount}`);
console.log(`error text hits    : ${hits.length ? hits.join(" | ") : "none"}`);
console.log(`quiz               : ${quizOk ? `ok (${quiz.count} 題)` : `BAD (count=${quiz.count}, feedback=${quiz.fbShown})`}`);
console.log(`mobile (390x844)   : ${mobileOk ? "ok" : `BAD（${mProblems.join("；")}）`}`);
console.log(`console errors     : ${consoleErrors.length}`);
consoleErrors.slice(0, 5).forEach((e) => console.log(`  · ${e}`));

if (hits.length > 0 || !quizOk || !mobileOk) {
  console.log("RESULT: FAIL");
  process.exit(1);
}
console.log("RESULT: PASS");
