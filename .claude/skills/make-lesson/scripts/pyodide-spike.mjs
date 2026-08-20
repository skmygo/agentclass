// Pyodide 可行性 spike：定軌前實測「這些套件裝得進瀏覽器嗎」。
// 在 headless Chromium 載入 CDN Pyodide，逐一 micropip.install 並回報結果——
// 任何一個 FAIL ＝ 這條路走外部軌（--external），不要嘗試 mock/hack 依賴鏈（實測過深不見底）。
//
// 用法（repo 根目錄執行；playwright 是 repo devDependency）：
//   node .claude/skills/make-lesson/scripts/pyodide-spike.mjs <package> [package...]
//   PYODIDE_VERSION=0.27.2 node ... 可覆寫版本
//
// 注意：Pyodide 版本以 marimo WASM 實際載入的為準（marimo runtime 動態決定），
// 這裡的釘版只求接近；spike 是「定軌」用的快篩，最終把關仍是 WASM 冒煙測試。
import { chromium } from "playwright";

const PYODIDE_VERSION = process.env.PYODIDE_VERSION ?? "0.27.2";
const pkgs = process.argv.slice(2);
if (pkgs.length === 0) {
  console.error("用法：node pyodide-spike.mjs <package> [package...]");
  process.exit(2);
}

const browser = await chromium.launch();
const page = await browser.newPage();
page.setDefaultTimeout(180_000);

console.log(`loading Pyodide v${PYODIDE_VERSION} ...`);
await page.setContent(`<script src="https://cdn.jsdelivr.net/pyodide/v${PYODIDE_VERSION}/full/pyodide.js"><\/script>`);
await page.waitForFunction(() => typeof globalThis.loadPyodide === "function");

const results = await page.evaluate(async (names) => {
  const py = await globalThis.loadPyodide();
  await py.loadPackage("micropip");
  const out = [];
  for (const name of names) {
    try {
      await py.runPythonAsync(
        `import micropip\nawait micropip.install(${JSON.stringify(name)})`,
      );
    } catch (e) {
      out.push({ name, ok: false, err: String(e.message || e).slice(-400) });
      continue;
    }
    // import 驗證是 best-effort：套件名 ≠ import 名（scikit-learn → sklearn）時
    // 只提示自行驗證，不判 FAIL——install 成功才是定軌的主訊號
    const guess = name.split("[")[0].split("==")[0].replace(/-/g, "_");
    try {
      await py.runPythonAsync(`import importlib\nimportlib.import_module(${JSON.stringify(guess)})`);
      out.push({ name, ok: true });
    } catch {
      out.push({ name, ok: true, note: `已安裝，但 import ${guess} 失敗——import 名可能不同，請手動驗證` });
    }
  }
  return out;
}, pkgs);

await browser.close();

console.log("---- pyodide spike ----");
let failed = false;
for (const r of results) {
  if (r.ok) {
    console.log(`✓ ${r.name}${r.note ? `（${r.note}）` : ""}`);
  } else {
    failed = true;
    console.log(`✗ ${r.name}\n  ${r.err.split("\n").slice(-3).join("\n  ")}`);
  }
}
console.log(failed
  ? "RESULT: FAIL — 走外部軌（scaffold --external），不要 mock 依賴鏈"
  : "RESULT: OK — 純瀏覽器課可行（最終仍以 WASM 冒煙為準）");
process.exit(failed ? 1 : 0);
