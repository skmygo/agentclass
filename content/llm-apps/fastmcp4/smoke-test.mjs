// 外部軌課冒煙測試模板：cp 到 content/<topic>/<id>/smoke-test.mjs（scaffold --external 會代勞）。
// 外部課沒有內嵌 notebook——冒煙驗的是「頁面完整、入口都活著」：
// h1 可見、molab 連結格式正確、.py 下載連結真的拿得到檔案、console 無錯誤。
// notebook 本體的驗證另走 `uv run marimo export html --sandbox`（見 engineering.md）。
// 用法：node smoke-test.mjs <課程頁 url>（server 起在 dist 根目錄）
import { chromium } from "playwright";

const H1_TEXT = "FastMCP 4：把函式變成 AI 工具，一發請求不用握手";        // 【必改】課程頁 hero 的 h1 文字（可只取片段）
const EXT_FILE = "fastmcp4_ext.py"; // 【scaffold 代換】外部 notebook 檔名

const url = process.argv[2] ?? "http://127.0.0.1:8787/index.html";
const t0 = Date.now();
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1400, height: 1000 } });

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
await page.goto(url, { waitUntil: "load", timeout: 60_000 }); // 不用 networkidle：頁面有 YouTube 等第三方 iframe 時永遠不會 idle；後面自己輪詢就緒

// 1) h1 可見（text=中文 會撈到隱藏 <title>，要等「可見的 h1」）
await page.waitForSelector(`h1:has-text("${H1_TEXT}")`, {
  timeout: 30_000,
  state: "visible",
});

// 2) molab 入口存在且指向本課的外部 notebook
const molabHref = await page.evaluate(() => {
  const a = document.querySelector('a[href*="molab.marimo.io/github/"]');
  return a ? a.href : null;
});
const molabOk = molabHref !== null && molabHref.endsWith(EXT_FILE);

// 3) 下載連結真的拿得到檔案（相對 dist 的實際 fetch）
const dlStatus = await page.evaluate(async (f) => {
  const r = await fetch(f);
  return r.status;
}, EXT_FILE);

// 4) 課末測驗：題數 2–5、點第一題任一選項會出現回饋
//    （gate 上鎖的課有覆蓋層——用 DOM click() 繞過命中測試，斷言照常有效）
const quiz = await page.evaluate(() => {
  const count = document.querySelectorAll("#quiz .quiz-q").length;
  const btn = document.querySelector("#quiz .quiz-q .quiz-opt");
  if (btn) btn.click();
  const fb = document.querySelector("#quiz .quiz-q .quiz-fb");
  const fbShown = !!fb && getComputedStyle(fb).display !== "none";
  return { count, fbShown };
});
const quizOk = quiz.count >= 2 && quiz.count <= 5 && quiz.fbShown;

await page.screenshot({ path: "smoke-screenshot.png", fullPage: false });
await browser.close();

console.log("---- smoke result ----");
console.log(`page ready in      : ${((Date.now() - t0) / 1000).toFixed(1)}s`);
console.log(`molab link         : ${molabOk ? "ok" : `BAD (${molabHref})`}`);
console.log(`${EXT_FILE} fetch  : ${dlStatus}`);
console.log(`quiz               : ${quizOk ? `ok (${quiz.count} 題)` : `BAD (count=${quiz.count}, feedback=${quiz.fbShown})`}`);
console.log(`console errors     : ${consoleErrors.length}`);
consoleErrors.slice(0, 5).forEach((e) => console.log(`  · ${e}`));

if (!molabOk || dlStatus !== 200 || !quizOk || consoleErrors.length > 0) {
  console.log("RESULT: FAIL");
  process.exit(1);
}
console.log("RESULT: PASS");
