/* ═══════════════════════════════════════════════════════════════
   課程頁共用行為（全站一份）：
   1. GPU 分頁切換（頁面有 #lab-tabs 才啟用；雙軌課專用）
   2. 「到右邊做」golab：捲動 iframe 到 data-nb 的 emoji 錨點
   3. 右欄狀態列：輪詢 iframe 內圖表數偵測 Pyodide 就緒
      （就緒門檻由 <body data-ready-figures="N"> 提供，N = notebook 的圖表數）
   課程專屬互動（hero 玩具等）寫在各課頁面的 inline <script>，不要放這裡。
   ═══════════════════════════════════════════════════════════════ */

/* 1. GPU 分頁切換（molab 拒絕被 iframe 嵌入，只能導流） */
(function () {
  if (!document.getElementById("lab-tabs")) return; // 純瀏覽器課沒有分頁列
  const nbFrame = document.getElementById("nb-frame");
  const nbStatus = document.getElementById("nb-status");
  const molabPanel = document.getElementById("molab-panel");
  function switchTab(name) {
    const isMolab = name === "molab";
    nbFrame.hidden = isMolab;
    nbStatus.hidden = isMolab;
    molabPanel.hidden = !isMolab;
    document.querySelectorAll(".labtab").forEach(t => {
      const on = t.dataset.tab === name;
      t.classList.toggle("active", on);
      t.setAttribute("aria-selected", String(on));
    });
  }
  document.querySelectorAll(".labtab").forEach(t =>
    t.addEventListener("click", () => switchTab(t.dataset.tab))
  );
  window.switchLabTab = switchTab;
})();

/* 2. golab：同源 iframe 捲動到 data-nb 的 emoji 錨點 */
(function () {
  const frame = document.getElementById("nb-frame");
  document.querySelectorAll(".golab").forEach(btn => {
    btn.addEventListener("click", () => {
      if (window.switchLabTab) window.switchLabTab("wasm"); // GPU 課切回互動實驗分頁
      const mark = btn.dataset.nb;
      try {
        const doc = frame.contentDocument;
        for (const h of doc.querySelectorAll("h1, h2, h3")) {
          if (h.textContent.includes(mark)) {
            h.scrollIntoView({ behavior: "smooth", block: "start" });
            break;
          }
        }
      } catch (e) { /* 未就緒時安靜略過 */ }
      // 窄螢幕（上下疊）時，把視窗帶到實驗場
      if (window.matchMedia("(max-width: 980px)").matches)
        document.getElementById("lab").scrollIntoView({ behavior: "smooth" });
    });
  });
})();

/* 3. 狀態列：輪詢 iframe 內 img/canvas 數量（同源才可行） */
(function () {
  const READY_FIGURES = Number(document.body.dataset.readyFigures || 1);
  const frame = document.getElementById("nb-frame");
  const bar = document.getElementById("nb-status");
  const txt = document.getElementById("nb-status-text");
  const t0 = Date.now();
  const timer = setInterval(() => {
    try {
      const n = frame.contentDocument.querySelectorAll("img, canvas").length;
      if (n >= READY_FIGURES) {
        bar.classList.add("ready");
        txt.textContent = "環境就緒——每一格都能改、能重跑。改壞了重新整理即可復原。";
        clearInterval(timer);
      }
    } catch (e) { /* not ready */ }
    if (Date.now() - t0 > 180000) {
      txt.textContent = "載入比平常久——網路慢或裝置較舊時屬正常，可再等等或重新整理。";
      clearInterval(timer);
    }
  }, 1500);
})();
