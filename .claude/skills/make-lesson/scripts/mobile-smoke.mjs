// 全站手機 viewport（390×844）冒煙：由 smoke-all.sh 呼叫，也可手動跑。
// 用法：node mobile-smoke.mjs <base-url> <id:type> [<id:type> ...]   type ∈ app|edit|ext
//
// 每課「結構檢查」（快）：無橫向溢出、底部切換列存在、切到實作區後內容符合課程型態
//   app  → iframe 立即開載（data-src 升格為 src）
//   edit → 出現「建議用電腦」提示卡、notebook 尚未開載
//   ext  → molab 導流面板（含手機體驗 note），無提示卡
// 「抽樣全載」（慢）：app、edit 各取清單中第一堂，走完 切tab → 載入 → 就緒 全程，
//   覆蓋 lazy load 端到端（WASM cell 執行結果與 viewport 無關，故不必每課全載）。
// gate 上鎖的課有覆蓋層——一律用 DOM click() 繞過命中測試，斷言照常有效。
import { chromium } from "playwright";

const [base, ...specs] = process.argv.slice(2);
if (!base || specs.length === 0) {
  console.error("用法：node mobile-smoke.mjs <base-url> <id:type> ...");
  process.exit(2);
}

const browser = await chromium.launch();
const ctx = await browser.newContext({
  viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true,
});

let fail = 0;
const fullLoadDone = { app: false, edit: false };
const isBeaconNoise = (t) => /cloudflareinsights/.test(t);

for (const spec of specs) {
  const [id, type] = spec.split(":");
  const page = await ctx.newPage();
  const errs = [];
  page.on("pageerror", (e) => { if (!isBeaconNoise(String(e))) errs.push(String(e).slice(0, 200)); });
  const bad = [];
  try {
    await page.goto(`${base}/${id}/`, { waitUntil: "domcontentloaded", timeout: 60_000 });
    await page.waitForSelector("#view-tabs", { timeout: 15_000 });
    const s = await page.evaluate(() => {
      const lesson = document.querySelector("#lesson");
      return {
        overflowW: document.scrollingElement.scrollWidth,
        innerW: innerWidth,
        // 教學 pane 自己有捲動容器，rogue 寬元素只會撐大它、不會撐大 document——兩層都量
        lessonOverflow: lesson ? lesson.scrollWidth - lesson.clientWidth : 0,
        tabsShown: getComputedStyle(document.querySelector("#view-tabs")).display !== "none",
        frameSrc: document.querySelector("#nb-frame")?.getAttribute("src") || "",
      };
    });
    if (s.overflowW > s.innerW) bad.push(`橫向溢出 ${s.overflowW}>${s.innerW}`);
    if (s.lessonOverflow > 1) bad.push(`教學區內橫向溢出 +${s.lessonOverflow}px`);
    if (!s.tabsShown) bad.push("切換列不可見");
    if (type !== "ext" && s.frameSrc) bad.push("教學區就預載了 notebook");
    await page.evaluate(() =>
      document.querySelector('#view-tabs button[data-view="lab"]').click());
    await page.waitForTimeout(400);
    if (type === "app") {
      const src = await page.evaluate(() =>
        document.querySelector("#nb-frame").getAttribute("src"));
      if (!src) bad.push("app 課切實作未開載");
    } else if (type === "edit") {
      const st = await page.evaluate(() => ({
        notice: !!document.querySelector("#nb-notice"),
        src: document.querySelector("#nb-frame").getAttribute("src"),
      }));
      if (!st.notice) bad.push("edit 課切實作沒出提示卡");
      if (st.src) bad.push("edit 課未確認就開載");
    } else {
      const st = await page.evaluate(() => ({
        panel: !!document.querySelector("#molab-panel"),
        note: document.body.innerText.includes("手機上體驗有限"),
        notice: !!document.querySelector("#nb-notice"),
      }));
      if (!st.panel) bad.push("ext 課切實作沒看到 molab 面板");
      if (!st.note) bad.push("ext 課缺手機體驗 note");
      if (st.notice) bad.push("ext 課不該有提示卡");
    }
    // 抽樣全載：app / edit 各一堂走到就緒
    if ((type === "app" || type === "edit") && !fullLoadDone[type] && bad.length === 0) {
      if (type === "edit")
        await page.evaluate(() => document.querySelector("#nb-notice button").click());
      await page.waitForSelector("#nb-status.ready", { timeout: 240_000 });
      fullLoadDone[type] = true;
      console.log(`✓ ${id} [${type}]（含全載至就緒）`);
    } else if (bad.length === 0) {
      console.log(`✓ ${id} [${type}]`);
    }
  } catch (e) {
    bad.push(String(e).split("\n")[0].slice(0, 160));
  }
  if (errs.length) bad.push(`pageerror×${errs.length}: ${errs[0]}`);
  if (bad.length) { fail++; console.log(`✗ ${id} [${type}] — ${bad.join("；")}`); }
  await page.close();
}

await browser.close();
console.log(`── mobile smoke: ${specs.length - fail} pass / ${fail} fail`);
console.log(fail === 0 ? "RESULT: PASS" : "RESULT: FAIL");
process.exit(fail === 0 ? 0 : 1);
