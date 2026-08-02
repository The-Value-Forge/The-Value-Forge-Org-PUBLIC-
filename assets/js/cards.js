/* TVF card gallery — read-state, infinity scroll-progress, grid/reader toggle.
   No dependencies. Degrades safely: without JS, cards render fully without state.
   Storage: localStorage["tvf:read:v1"] = { "<slug>": { p:0..1, done:bool, t:epochMs } } */
(function () {
  "use strict";
  var KEY = "tvf:read:v1";

  function load() {
    try { return JSON.parse(localStorage.getItem(KEY)) || {}; }
    catch (e) { return {}; }
  }
  function save(store) {
    try { localStorage.setItem(KEY, JSON.stringify(store)); } catch (e) {}
  }
  function get(slug) {
    var s = load();
    return s[slug] || { p: 0, done: false, t: 0 };
  }
  function set(slug, rec) {
    var s = load();
    var prev = s[slug] || { p: 0, done: false };
    // progress and done are monotonic — never regress on a re-read
    rec.p = Math.max(prev.p || 0, rec.p || 0);
    rec.done = prev.done || rec.done || false;
    rec.t = Date.now();
    s[slug] = rec;
    save(s);
  }

  // Set an infinity mark's fill to a 0..1 progress value.
  function setMark(markEl, p) {
    var fill = markEl && markEl.querySelector(".read-mark__fill");
    if (!fill) return;
    var pct = Math.max(0, Math.min(1, p));
    fill.style.strokeDashoffset = String(100 * (1 - pct));
  }

  /* ---- Card gallery ---------------------------------------------------- */
  function initGallery(wrap) {
    var cards = Array.prototype.slice.call(wrap.querySelectorAll(".gallery-card"));
    var unreadEl = wrap.querySelector("[data-unread-count]");

    function paint() {
      var unread = 0;
      cards.forEach(function (card) {
        var rec = get(card.getAttribute("data-slug"));
        var mark = card.querySelector(".read-mark");
        var label = card.querySelector("[data-read-label]");
        setMark(mark, rec.done ? 1 : rec.p);
        card.classList.toggle("is-read", !!rec.done);
        card.classList.toggle("is-reading", !rec.done && rec.p > 0.02);
        if (label) label.textContent = rec.done ? "Read" : (rec.p > 0.02 ? "Reading" : "Unread");
        if (!rec.done) unread++;
      });
      if (unreadEl) unreadEl.textContent = String(unread);
    }
    paint();
    // Repaint when returning from an article (bfcache / tab refocus).
    window.addEventListener("pageshow", paint);
    document.addEventListener("visibilitychange", function () {
      if (!document.hidden) paint();
    });

    // Grid <-> reader mode toggle.
    var modeBtns = Array.prototype.slice.call(wrap.querySelectorAll(".gallery-mode"));
    function setMode(mode, scroll) {
      wrap.classList.toggle("is-reader", mode === "reader");
      modeBtns.forEach(function (b) {
        var on = b.getAttribute("data-mode") === mode;
        b.classList.toggle("is-active", on);
        b.setAttribute("aria-pressed", on ? "true" : "false");
      });
      if (mode === "reader" && scroll !== false) {
        var first = wrap.querySelector(".gallery-card");
        if (first) first.scrollIntoView({ block: "center" });
      }
    }
    // Sync button state to whatever mode the HTML was server-rendered in
    var initMode = wrap.classList.contains("is-reader") ? "reader" : "grid";
    setMode(initMode, false);
    modeBtns.forEach(function (b) {
      b.addEventListener("click", function () { setMode(b.getAttribute("data-mode")); });
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && wrap.classList.contains("is-reader")) setMode("grid");
    });
  }

  /* ---- Article reading progress — the infinity completes itself -------- */
  function initProgress(widget) {
    var article = document.querySelector("[data-slug]");
    if (!article) return;
    var slug = article.getAttribute("data-slug");
    var mark = widget.querySelector(".read-mark");
    var started = false;
    var done = get(slug).done;

    function update() {
      var rect = article.getBoundingClientRect();
      var vh = window.innerHeight || document.documentElement.clientHeight;
      var total = rect.height - vh;            // scroll distance within the article
      var scrolled = -rect.top;                // how far past the top we are
      var p = total > 0 ? scrolled / total : 1;
      p = Math.max(0, Math.min(1, p));
      if (!started && (p > 0.01 || scrolled > 40)) {
        widget.hidden = false; started = true;
      }
      setMark(mark, p);
      var rec = { p: p, done: p >= 0.98 };
      set(slug, rec);
      if (rec.done && !done) {
        done = true;
        widget.classList.add("is-complete");
      }
    }

    var ticking = false;
    function onScroll() {
      if (ticking) return;
      ticking = true;
      window.requestAnimationFrame(function () { update(); ticking = false; });
    }
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onScroll);
    update();
  }

  /* ---- Back button — return to wherever the reader actually came from -- */
  function initBack(link) {
    var ref = document.referrer;
    var sameOrigin = false, refPath = "";
    try {
      if (ref) {
        var u = new URL(ref);
        sameOrigin = u.origin === location.origin && u.pathname !== location.pathname;
        refPath = u.pathname;
      }
    } catch (e) {}

    // If we arrived from another TVF page, relabel to "Back" and use history
    // (this restores the feed/grid scroll position the reader left from).
    if (sameOrigin) {
      var label = link.querySelector("[data-back-label]");
      var isListing = /^\/(feed|signal|synthesis|monthly|archive|domain)\/?/.test(refPath);
      if (label && !isListing) label.textContent = "Back";
      link.addEventListener("click", function (e) {
        e.preventDefault();
        history.back();
      });
    }
    // Otherwise (deep-link / external / direct), the href falls back to the
    // article's parent section — no JS needed.
  }

  function boot() {
    var wrap = document.querySelector("[data-card-gallery]");
    if (wrap) initGallery(wrap);
    var widget = document.querySelector("[data-read-progress]");
    if (widget) initProgress(widget);
    var back = document.querySelector("[data-back]");
    if (back) initBack(back);
  }
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
