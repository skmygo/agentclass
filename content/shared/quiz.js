/* ═══════════════════════════════════════════════════════════════
   課末情境測驗（全站一份）——標記格式見 make-lesson skill 的
   assets/templates/quiz-section.html。每題 .quiz-q[data-answer=字母]、
   選項 button.quiz-opt[data-k=字母]、解釋在 .quiz-fb。
   行為：點選即判、答後鎖定並標示正解、逐題顯示解釋、全部答完出總分。
   狀態不落地：重新整理即可重測。頁面沒有 [data-quiz] 時本檔是 no-op。
   ═══════════════════════════════════════════════════════════════ */
(function () {
  document.querySelectorAll("[data-quiz]").forEach(function (quiz) {
    var qs = Array.prototype.slice.call(quiz.querySelectorAll(".quiz-q"));
    var score = quiz.querySelector("[data-score]");
    var answered = 0;
    var correct = 0;

    qs.forEach(function (q) {
      var ans = q.getAttribute("data-answer");
      var opts = Array.prototype.slice.call(q.querySelectorAll(".quiz-opt"));
      var fb = q.querySelector(".quiz-fb");

      opts.forEach(function (btn) {
        btn.addEventListener("click", function () {
          if (q.hasAttribute("data-done")) return;
          q.setAttribute("data-done", "1");
          answered += 1;

          var hit = btn.getAttribute("data-k") === ans;
          if (hit) correct += 1;

          opts.forEach(function (o) {
            o.disabled = true;
            if (o.getAttribute("data-k") === ans) o.classList.add("is-correct");
          });
          if (!hit) btn.classList.add("is-wrong");

          if (fb) {
            fb.classList.add("show");
            if (!hit) fb.classList.add("no");
            fb.insertAdjacentHTML(
              "afterbegin",
              hit
                ? '<b class="q-verdict">✓ 答對了。</b>'
                : '<b class="q-verdict">✗ 最佳答案是 ' + ans + '。</b>'
            );
          }

          if (answered === qs.length && score) {
            var miss = qs.length - correct;
            var msg, tip;
            if (miss === 0) {
              msg = "🎯 " + correct + " / " + qs.length + " 全對！這課的判斷你已經帶走了。";
              tip = "";
            } else if (miss === 1) {
              msg = "💪 " + correct + " / " + qs.length + "——只差一題。";
              tip = "回頭看看答錯那題的解釋，對應章節再掃一眼就補上了。";
            } else {
              msg = "📖 " + correct + " / " + qs.length + "。";
              tip = "建議回到對應章節重讀一次；重新整理頁面就能重測。";
            }
            score.innerHTML =
              "<span>" + msg + "</span>" + (tip ? "<small>" + tip + "</small>" : "");
            score.classList.add("show");
          }
        });
      });
    });
  });
})();
