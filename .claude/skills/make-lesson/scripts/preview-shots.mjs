// 預覽截圖：headless 開頁面、課程頁等 notebook 全跑完（狀態列變綠）再截。
// 用法（repo 根目錄執行；dist 的 server 要先開著）：
//   node .claude/skills/make-lesson/scripts/preview-shots.mjs [base] <path...>
//   node .claude/skills/make-lesson/scripts/preview-shots.mjs / /ml-basics/ /clustering/
//   node .claude/skills/make-lesson/scripts/preview-shots.mjs "/litellm-basics/@#gw-burst"   # 截圖前先點 hero 的按鈕
// base 省略時預設 http://127.0.0.1:8787。輸出到 ./preview-shots/<name>.png。
// path 後面接 @<css selector>（可多個，用 @ 串）會依序點擊再截——用來驗證 hero 互動真的會動。
// 注意：這支要在 repo 樹內執行（playwright 從 repo 根的 node_modules 解析）；
// headless 截圖裡 emoji 是豆腐＝已知假警報，真瀏覽器正常。
import { chromium } from "playwright";
import { mkdirSync } from "node:fs";

const args = process.argv.slice(2);
const base = args[0]?.startsWith("http") ? args.shift() : "http://127.0.0.1:8787";
if (!args.length) {
  console.error("用法：node preview-shots.mjs [base] <path...>  例：/ /ml-basics/ /clustering/");
  process.exit(1);
}

mkdirSync("preview-shots", { recursive: true });
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1600, height: 1000 } });

for (const spec of args) {
  const [path, ...clicks] = spec.split("@");
  const name = (path === "/" ? "home" : path.replaceAll("/", "")) + (clicks.length ? "-clicked" : "");
  const errors = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto(base + path, { waitUntil: "domcontentloaded", timeout: 60_000 });
  for (const sel of clicks) {
    await page.click(sel, { timeout: 10_000 });
    await page.waitForTimeout(900);
  }
  const isLesson = await page.locator("#nb-status").count();
  if (isLesson) {
    // 課程頁：等右欄狀態列變綠（= data-ready-figures 張圖都渲染出來）
    await page.waitForSelector("#nb-status.ready", { timeout: 180_000 });
    await page.waitForTimeout(1500);
    await page.screenshot({ path: `preview-shots/${name}.png` });
  } else {
    await page.waitForLoadState("networkidle");
    await page.screenshot({ path: `preview-shots/${name}.png`, fullPage: true });
  }
  console.log(`✓ preview-shots/${name}.png${errors.length ? `  ⚠ pageerror: ${errors[0].slice(0, 120)}` : ""}`);
}
await browser.close();
