/* 簡易主題密碼閘——擋路人、不擋有心人（repo 公開，只放 SHA-256 不放明碼）。
   用法：要上鎖的頁面在 <head> 加一行
     <script src="/shared/gate.js" data-gate="<群組>" data-hash="<sha256(密碼) 的 hex>"></script>
   同群組（通常＝同主題）輸入一次即解鎖（localStorage 記住這台瀏覽器）。
   刻意做成「不透明覆蓋層」而非隱藏內容：內容照常載入（notebook 順便暖機）、
   冒煙測試的可見性檢查不受影響；devtools 刪掉覆蓋層就能看——設計如此，不是漏洞。 */
(() => {
  const tag = document.currentScript;
  if (!tag) return;
  const group = tag.dataset.gate;
  const want = tag.dataset.hash;
  if (!group || !want) return;
  const KEY = "gate:" + group;
  try { if (localStorage.getItem(KEY) === want) return; } catch { return; }
  if (!(window.crypto && crypto.subtle)) return; // 非 https 算不了 hash → 放行（本來就不是真防護）

  const sha256 = async (s) => {
    const buf = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(s));
    return [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, "0")).join("");
  };

  const show = () => {
    // 密碼牆同時是櫥窗：露出課名與課程簡介（來自本頁 title / meta description），
    // 分享連結被擋下的人至少知道這門課在教什麼
    const courseTitle = (document.title || "").replace(/\s*·\s*AI 互動教室\s*$/, "");
    const courseDesc =
      (document.querySelector('meta[name="description"]') || {}).content || "";
    const ov = document.createElement("div");
    ov.id = "gate-overlay";
    ov.style.cssText =
      "position:fixed;inset:0;z-index:2147483647;display:flex;align-items:center;justify-content:center;" +
      "background:linear-gradient(#E4E9E2 1px,transparent 1px) 0 0/100% 28px,#FAFBF8;" +
      'font-family:"Noto Sans TC","PingFang TC","Microsoft JhengHei",system-ui,sans-serif;color:#1C2B33;';
    ov.innerHTML =
      '<form style="background:#fff;border:2px solid #1C2B33;border-radius:14px;box-shadow:6px 6px 0 #E4E9E2;' +
      'padding:30px 34px;max-width:380px;width:calc(100% - 48px);text-align:center;">' +
      '<div style="font-family:ui-monospace,Menlo,Consolas,monospace;font-size:12px;font-weight:700;' +
      'letter-spacing:.14em;color:#C44E52;">PRIVATE</div>' +
      '<div class="gate-title" style="font-size:19px;font-weight:900;margin:10px 0 6px;">這門課需要密碼</div>' +
      '<div class="gate-desc" style="font-size:13px;color:#5A6B73;line-height:1.7;text-align:left;margin:0 0 14px;"></div>' +
      '<div style="font-size:13px;font-weight:700;margin-bottom:8px;">輸入密碼進入</div>' +
      '<input type="password" autocomplete="off" aria-label="密碼" style="width:100%;box-sizing:border-box;' +
      'font-size:18px;text-align:center;letter-spacing:.3em;padding:10px 12px;border:2px solid #1C2B33;' +
      'border-radius:10px;outline-offset:2px;">' +
      '<div class="gate-msg" style="min-height:20px;font-size:13px;color:#C44E52;margin-top:8px;"></div>' +
      '<button type="submit" style="font-size:15px;font-weight:800;padding:9px 26px;margin-top:4px;' +
      'background:#1C2B33;color:#fff;border:0;border-radius:10px;cursor:pointer;">進入</button>' +
      "</form>";
    if (courseTitle) ov.querySelector(".gate-title").textContent = courseTitle;
    const descEl = ov.querySelector(".gate-desc");
    if (courseDesc) descEl.textContent = courseDesc;
    else descEl.remove();
    document.body.appendChild(ov);
    const prevOverflow = document.documentElement.style.overflow;
    document.documentElement.style.overflow = "hidden";
    const input = ov.querySelector("input");
    const msg = ov.querySelector(".gate-msg");
    ov.querySelector("form").addEventListener("submit", async (e) => {
      e.preventDefault();
      if ((await sha256(input.value)) === want) {
        try { localStorage.setItem(KEY, want); } catch { /* 無痕模式存不了：本次分頁放行 */ }
        document.documentElement.style.overflow = prevOverflow;
        ov.remove();
      } else {
        msg.textContent = "密碼不對，再試一次";
        input.select();
      }
    });
    input.focus();
  };

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", show);
  else show();
})();
