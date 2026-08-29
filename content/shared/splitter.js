// 左右欄可拖拉分隔線（全課共用）。
// 課程頁約定：<main> 直下有 #lesson（左，width 由本檔接管）與 #lab（右，flex:1）。
// 頁面只需在 </body> 前加一行：<script src="/shared/splitter.js" defer></script>
// 行為：拖拉改寬；拖到貼邊可把單欄完全收合（分隔線留在邊上，拖回即展開）；
//       雙擊/Home 還原預設、方向鍵微調；比例存 localStorage，跨課共用。
(() => {
  const MIN_LESSON = 380;   // 左欄未收合時的最小寬（與各課 #lesson 的 min-width 一致）
  const MIN_LAB = 480;      // 右欄未收合時的最小寬，notebook 才可用
  const KEY = "agentclass:splitPct";

  const lesson = document.getElementById("lesson");
  const lab = document.getElementById("lab");
  if (!lesson || !lab || lesson.parentElement !== lab.parentElement) return;
  const main = lesson.parentElement;

  const css = document.createElement("style");
  css.textContent = `
    #splitter {
      flex: none; width: 12px; position: relative; z-index: 5;
      display: flex; align-items: center; justify-content: center;
      cursor: col-resize; touch-action: none; background: var(--bg, transparent);
    }
    #splitter::before {
      content: ""; position: absolute; top: 0; bottom: 0;
      left: 50%; width: 2px; margin-left: -1px; background: var(--ink, #1C2B33);
    }
    #splitter .grip {
      position: relative; width: 6px; height: 44px; border-radius: 4px;
      background: var(--ink, #1C2B33); opacity: 0; transition: opacity .15s;
    }
    #splitter:hover .grip, #splitter.dragging .grip, #splitter.edge .grip,
    #splitter:focus-visible .grip { opacity: 1; }
    #splitter:focus-visible { outline: none; }
    #splitter:focus-visible .grip { outline: 3px solid var(--setosa, #4C72B0); outline-offset: 2px; }
    body.splitting { cursor: col-resize; user-select: none; }
    body.splitting iframe { pointer-events: none; }
    @media (min-width: 981px) {
      #lesson.collapsed, #lab.collapsed {
        width: 0 !important; min-width: 0 !important;
        flex: none !important; padding: 0 !important;
        overflow: hidden !important; border: 0 !important;
      }
    }
    @media (max-width: 980px) {
      #splitter { display: none; }
      #lesson { width: 100% !important; }
    }
  `;
  document.head.appendChild(css);

  const splitter = document.createElement("div");
  splitter.id = "splitter";
  splitter.setAttribute("role", "separator");
  splitter.setAttribute("aria-orientation", "vertical");
  splitter.setAttribute("aria-label", "拖拉調整左右欄寬度；拖到貼邊收合單欄；雙擊還原預設");
  splitter.tabIndex = 0;
  splitter.innerHTML = '<div class="grip"></div>';
  main.insertBefore(splitter, lab);
  lab.style.borderLeft = "none"; // 原本的分隔線改由 splitter 畫

  const mq = matchMedia("(min-width: 981px)");
  let state = null; // null（雙欄）| "left"（左欄收合）| "right"（右欄收合）

  const avail = () => main.clientWidth - splitter.offsetWidth;
  const clamp = (px) => {
    const max = avail() - MIN_LAB;
    return Math.min(Math.max(px, MIN_LESSON), Math.max(max, MIN_LESSON));
  };
  const uncollapse = () => {
    state = null;
    lesson.classList.remove("collapsed");
    lab.classList.remove("collapsed");
    splitter.classList.remove("edge");
    lab.style.flex = "";
  };
  const collapse = (side) => {
    uncollapse();
    state = side;
    (side === "left" ? lesson : lab).classList.add("collapsed");
    splitter.classList.add("edge"); // 收合時讓握把常駐，提示還能拖回來
    if (side === "left") lesson.style.width = "0px";
    else { lesson.style.width = avail() + "px"; lab.style.flex = "none"; }
  };
  // 目標寬 px → 貼邊區間內就收合，否則夾在雙欄下限之間
  const setWidth = (px) => {
    if (px < MIN_LESSON / 2) { collapse("left"); return; }
    if (px > avail() - MIN_LAB / 2) { collapse("right"); return; }
    uncollapse();
    lesson.style.width = clamp(px) + "px";
  };
  const save = () => {
    const pct = state === "left" ? 0
      : state === "right" ? 100
      : lesson.getBoundingClientRect().width / main.clientWidth * 100;
    localStorage.setItem(KEY, pct.toFixed(2));
  };
  const reset = () => {
    uncollapse();
    lesson.style.width = "";
    localStorage.removeItem(KEY);
  };
  const applyPct = (pct) => {
    if (pct <= 0) collapse("left");
    else if (pct >= 100) collapse("right");
    else { uncollapse(); lesson.style.width = clamp(main.clientWidth * pct / 100) + "px"; }
  };

  const saved = parseFloat(localStorage.getItem(KEY));
  if (mq.matches && Number.isFinite(saved)) applyPct(saved);
  addEventListener("resize", () => {
    if (!mq.matches) return;
    const pct = parseFloat(localStorage.getItem(KEY));
    if (Number.isFinite(pct)) applyPct(pct); // 視窗改變時維持比例/收合狀態
  });

  let dragging = false, startX = 0, startW = 0;
  splitter.addEventListener("pointerdown", (e) => {
    dragging = true; startX = e.clientX;
    startW = lesson.getBoundingClientRect().width;
    splitter.setPointerCapture(e.pointerId);
    splitter.classList.add("dragging");
    document.body.classList.add("splitting");
  });
  splitter.addEventListener("pointermove", (e) => {
    if (!dragging) return;
    setWidth(startW + e.clientX - startX);
  });
  const end = () => {
    if (!dragging) return;
    dragging = false;
    splitter.classList.remove("dragging");
    document.body.classList.remove("splitting");
    save();
  };
  splitter.addEventListener("pointerup", end);
  splitter.addEventListener("pointercancel", end);
  splitter.addEventListener("dblclick", reset);
  splitter.addEventListener("keydown", (e) => {
    if (e.key === "Home") { reset(); e.preventDefault(); return; }
    if (e.key !== "ArrowLeft" && e.key !== "ArrowRight") return;
    if (state === "left" && e.key === "ArrowRight") setWidth(MIN_LESSON);
    else if (state === "right" && e.key === "ArrowLeft") setWidth(avail() - MIN_LAB);
    else {
      const step = (e.shiftKey ? 120 : 40) * (e.key === "ArrowRight" ? 1 : -1);
      setWidth(lesson.getBoundingClientRect().width + step);
    }
    save();
    e.preventDefault();
  });

  /* ── 窄螢幕（≤980px）視圖管理：底部「教學｜實作」切換列 ──
     樣式在 /shared/lesson.css（桌機隱藏）。切到實作時發
     agentclass:lab-shown 事件，lesson.js 據此決定何時載 notebook。 */
  if (!document.body.dataset.view) document.body.dataset.view = "lesson";
  const tabs = document.createElement("nav");
  tabs.id = "view-tabs";
  tabs.setAttribute("aria-label", "切換教學與實作");
  tabs.innerHTML =
    '<button type="button" data-view="lesson" aria-selected="true">教學</button>' +
    '<button type="button" data-view="lab" aria-selected="false">實作</button>';
  document.body.appendChild(tabs);
  const setView = (name) => {
    if (name !== "lesson" && name !== "lab") return;
    document.body.dataset.view = name;
    tabs.querySelectorAll("button").forEach((b) =>
      b.setAttribute("aria-selected", String(b.dataset.view === name)));
    if (name === "lab")
      document.dispatchEvent(new CustomEvent("agentclass:lab-shown"));
  };
  tabs.addEventListener("click", (e) => {
    const btn = e.target.closest("button[data-view]");
    if (btn) setView(btn.dataset.view);
  });
  window.setLessonView = setView;
})();
