/* ═══════════════════════════════════════════════════════════════
   課程頁共用行為（全站一份）：
   1. GPU 分頁切換（頁面有 #lab-tabs 才啟用；雙軌課專用）
   2. 「到右邊做」golab：捲動 iframe 到 data-nb 的 emoji 錨點
   3. 右欄狀態列：輪詢 iframe 內的就緒訊號偵測 Pyodide 就緒
      （預設 <body data-ready-figures="N"> 圖表數門檻；
      無圖課改宣告 <body data-ready-selector="<css>">，元素出現即就緒；
      app 模式課宣告 <body data-nb-mode="app">，就緒文案改成拉滑桿的講法）
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
      // 窄螢幕：切到實作視圖（切換列由 /shared/splitter.js 注入）
      if (window.matchMedia("(max-width: 980px)").matches && window.setLessonView)
        window.setLessonView("lab");
    });
  });
})();

/* 3. notebook 載入與狀態列（同源輪詢才可行）：
   iframe 標記為 <iframe id="nb-frame" data-src="nb/index.html">，由本段決定何時升格為 src——
   ≥981px 進頁即載（桌機行為不變）；≤980px 首次進實作區才載：
   app 課切過去直接載；edit 課先出「建議用電腦」提示卡，確認後載。
   就緒輪詢與 180 秒逾時一律從開始載入起算。
   就緒訊號：預設 img/canvas 數量 ≥ data-ready-figures；
   無圖課宣告 data-ready-selector 後改以「符合元素出現」判定 */
(function () {
  const frame = document.getElementById("nb-frame");
  const bar = document.getElementById("nb-status");
  const txt = document.getElementById("nb-status-text");
  if (!frame || !bar || !txt) return; // 外部軌頁沒有內嵌 notebook
  const READY_SELECTOR = document.body.dataset.readySelector || "";
  const READY_FIGURES = Number(document.body.dataset.readyFigures || 1);
  // app 模式課（<body data-nb-mode="app">）右欄沒有可編輯的格子，就緒文案跟著換
  const isApp = document.body.dataset.nbMode === "app";
  const READY_TEXT = isApp
    ? "實驗場就緒——拉滑桿、換選項，結果立刻重算。玩壞了重新整理即可復原。"
    : "環境就緒——每一格都能改、能重跑。改壞了重新整理即可復原。";

  let started = false;
  function startNotebook() {
    if (started) return;
    started = true;
    const card = document.getElementById("nb-notice");
    if (card) card.remove();
    bar.hidden = false;
    if (frame.dataset.src) frame.src = frame.dataset.src;
    const t0 = Date.now();
    const timer = setInterval(() => {
      try {
        const doc = frame.contentDocument;
        const ready = READY_SELECTOR
          ? !!doc.querySelector(READY_SELECTOR)
          : doc.querySelectorAll("img, canvas").length >= READY_FIGURES;
        if (ready) {
          bar.classList.add("ready");
          txt.textContent = READY_TEXT;
          clearInterval(timer);
        }
      } catch (e) { /* not ready */ }
      if (Date.now() - t0 > 180000) {
        txt.textContent = "載入比平常久——網路慢或裝置較舊時屬正常，可再等等或重新整理。";
        clearInterval(timer);
      }
    }, 1500);
  }

  // edit 課在手機上的預期管理：先講清楚，仍給「載入」的路
  function showNotice() {
    if (started || document.getElementById("nb-notice")) return;
    bar.hidden = true;
    const card = document.createElement("div");
    card.id = "nb-notice";
    card.innerHTML =
      '<div class="inner">' +
      "<p><b>本課的動手部分是直接改程式碼。</b>" +
      "手機上編輯程式不太順手，建議之後用電腦開這一頁動手；" +
      "也可以現在載入環境，先看看每一步的輸出。</p>" +
      '<button type="button" class="golab">我知道了，仍要載入</button>' +
      "</div>";
    card.querySelector("button").addEventListener("click", startNotebook);
    frame.parentElement.insertBefore(card, frame);
  }

  const wide = matchMedia("(min-width: 981px)");
  if (wide.matches || !frame.dataset.src) {
    startNotebook(); // 桌機進頁即載；iframe 已直接帶 src 的舊頁面視同已開載
  } else {
    document.addEventListener("agentclass:lab-shown", () => {
      if (started) return;
      if (isApp) startNotebook();
      else showNotice();
    });
    // 平板轉橫（窄→寬）：回到桌機行為，未載者立即載
    wide.addEventListener("change", (e) => { if (e.matches) startNotebook(); });
  }
})();
