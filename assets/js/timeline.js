/* The Value Forge — Evidence Timeline
   Renders signals, syntheses, and VF-Patterns onto five domain lanes.
   Data is inlined by Hugo at build time (#tl-data), so every weekly
   pipeline commit updates this view automatically. No dependencies. */
(function () {
  "use strict";

  var root = document.getElementById("tvf-timeline");
  var dataEl = document.getElementById("tl-data");
  if (!root || !dataEl) return;

  var data;
  try { data = JSON.parse(dataEl.textContent); } catch (e) { return; }

  var DOMAINS = [
    { id: "d01", code: "D01", name: "Acute Frailty" },
    { id: "d02", code: "D02", name: "Clinical Psychology" },
    { id: "d03", code: "D03", name: "Palliative Care" },
    { id: "d04", code: "D04", name: "Therapies & AHPs" },
    { id: "d05", code: "D05", name: "OPAT" }
  ];
  var EV_RADIUS = {
    "Meta-analysis": 9, "Primary Study": 7, "Synthesis": 6.5,
    "Guidance": 6, "Audit/Data": 5.5, "Unverified": 4.5
  };
  var STATUS_BADGE = {
    "NEW": "badge--established", "CONFIRMED": "badge--established",
    "UPDATED": "badge--provisional", "DISCARDED": "badge--status",
    "established": "badge--established", "provisional": "badge--provisional",
    "contested": "badge--contested"
  };

  // Geometry — must match the .tl-lane-label heights in CSS.
  var AXIS_H = 36, PAT_H = 64, LANE_H = 56, PAD_X = 28, PX_PER_WEEK = 44;
  var HEIGHT = AXIS_H + PAT_H + DOMAINS.length * LANE_H + 8;

  function parseDate(s) {
    if (!s) return null;
    var p = String(s).split("-");
    if (p.length === 2) return new Date(+p[0], +p[1] - 1, 15); // "YYYY-MM" → mid-month
    return new Date(+p[0], +p[1] - 1, +p[2]);
  }
  function fmtDate(d) {
    return d.toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" });
  }
  function laneY(i) { return AXIS_H + PAT_H + i * LANE_H + LANE_H / 2; }
  function laneIndex(id) {
    var key = String(id).toLowerCase();
    for (var i = 0; i < DOMAINS.length; i++) if (DOMAINS[i].id === key) return i;
    return -1;
  }
  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }
  // Pipeline fields have drifted between scalar and array; never trust the shape.
  function asArray(v) {
    if (v == null || v === "") return [];
    return Array.isArray(v) ? v : [v];
  }

  // ---- Assemble events ----------------------------------------------------
  var findings = (data.findings || []).map(function (f) {
    return {
      kind: f.type === "synthesis" ? "synthesis" : "signal",
      title: f.title, url: f.url, date: parseDate(f.date),
      domains: asArray(f.domains).map(function (d) { return String(d).toLowerCase(); })
        .filter(function (d) { return laneIndex(d) >= 0; }),
      evidence: asArray(f.evidence)[0] || "",
      status: asArray(f.status)[0] || "",
      summary: f.summary || ""
    };
  }).filter(function (f) { return f.date && f.domains.length; });

  var patterns = (data.patterns || []).map(function (p) {
    // first_appeared is in the translator schema but the live pipeline has
    // omitted it; fall back to the earliest history entry's date.
    var history = asArray(p.history);
    var since = p.first_appeared || (history[0] && history[0].date);
    return {
      kind: "pattern",
      id: p.id, title: p.title, status: p.status || "",
      date: parseDate(since),
      domains: asArray(p.domains).map(function (d) { return String(d).toLowerCase(); })
        .filter(function (d) { return laneIndex(d) >= 0; }),
      confirmation: p.confirmation_level || "",
      history: history,
      url: "/patterns/#" + String(p.id || "").toLowerCase()
    };
  }).filter(function (p) { return p.date; });

  var all = findings.concat(patterns);
  if (!all.length) {
    root.querySelector(".tl-board").innerHTML =
      '<p class="empty-state">Timeline entries will appear here as the weekly pipeline publishes content.</p>';
    return;
  }

  // ---- Time scale ----------------------------------------------------------
  var DAY = 86400000, today = new Date();
  var min = new Date(Math.min.apply(null, all.map(function (e) { return e.date; })) - 12 * DAY);
  var max = new Date(Math.max(today.getTime(), Math.max.apply(null, all.map(function (e) { return e.date; }))) + 12 * DAY);
  var weeks = Math.max(8, Math.ceil((max - min) / (7 * DAY)));
  var WIDTH = PAD_X * 2 + weeks * PX_PER_WEEK;
  function x(d) { return PAD_X + ((d - min) / (max - min)) * (WIDTH - PAD_X * 2); }

  // ---- Build SVG -----------------------------------------------------------
  var NS = "http://www.w3.org/2000/svg";
  function el(tag, attrs, parent) {
    var n = document.createElementNS(NS, tag);
    for (var k in attrs) n.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(n);
    return n;
  }
  var svg = root.querySelector(".tl-svg");
  svg.setAttribute("viewBox", "0 0 " + WIDTH + " " + HEIGHT);
  svg.setAttribute("width", WIDTH);
  svg.setAttribute("height", HEIGHT);

  var gGrid = el("g", { "class": "tl-grid" }, svg);
  var gThreads = el("g", {}, svg);
  var gMarks = el("g", {}, svg);

  // Month gridlines + labels
  var cursor = new Date(min.getFullYear(), min.getMonth() + 1, 1);
  while (cursor < max) {
    var mx = x(cursor);
    el("line", { x1: mx, y1: AXIS_H - 10, x2: mx, y2: HEIGHT - 4, "class": "tl-gridline" }, gGrid);
    var lbl = el("text", { x: mx + 5, y: AXIS_H - 14, "class": "tl-month" }, gGrid);
    lbl.textContent = cursor.toLocaleDateString("en-GB", { month: "short" }).toUpperCase() +
      " ’" + String(cursor.getFullYear()).slice(2);
    cursor = new Date(cursor.getFullYear(), cursor.getMonth() + 1, 1);
  }
  // Lane hairlines + patterns band separator
  el("line", { x1: PAD_X / 2, y1: AXIS_H + PAT_H, x2: WIDTH - PAD_X / 2, y2: AXIS_H + PAT_H, "class": "tl-bandrule" }, gGrid);
  DOMAINS.forEach(function (d, i) {
    el("line", { x1: PAD_X / 2, y1: laneY(i), x2: WIDTH - PAD_X / 2, y2: laneY(i), "class": "tl-lanerule" }, gGrid);
  });
  // Now marker
  if (today > min && today < max) {
    var nx = x(today);
    el("line", { x1: nx, y1: AXIS_H - 6, x2: nx, y2: HEIGHT - 4, "class": "tl-now" }, gGrid);
    var nt = el("text", { x: nx, y: AXIS_H - 14, "class": "tl-nowlabel", "text-anchor": "middle" }, gGrid);
    nt.textContent = "NOW";
  }

  // Collision offsets: events sharing a lane and week get jittered on x.
  var slots = {};
  function slotOffset(laneIdx, date) {
    var key = laneIdx + ":" + Math.round((date - min) / (7 * DAY));
    var n = slots[key] = (slots[key] || 0) + 1;
    return (n - 1) % 2 === 0 ? Math.floor((n - 1) / 2) * 16 : -Math.ceil((n - 1) / 2) * 16;
  }

  var tip = root.querySelector(".tl-tip");
  var seq = 0;

  function makeMarker(ev, draw) {
    var a = el("a", {
      href: ev.url || "#", "class": "tl-mark tl-mark--" + ev.kind,
      "data-type": ev.kind, "data-cross": ev.domains.length > 1 ? "1" : "0"
    }, gMarks);
    a.setAttribute("aria-label", ariaFor(ev));
    draw(a);
    a.addEventListener("mouseenter", function () { showTip(ev, a); });
    a.addEventListener("focus", function () { showTip(ev, a); });
    a.addEventListener("mouseleave", hideTip);
    a.addEventListener("blur", hideTip);
    return a;
  }
  function ariaFor(ev) {
    var codes = ev.domains.map(function (d) { return d.toUpperCase(); }).join(", ");
    if (ev.kind === "pattern") return ev.id + " pattern, " + ev.status + ", domains " + codes + ": " + ev.title;
    return ev.kind + ", " + fmtDate(ev.date) + ", domains " + codes + ": " + ev.title;
  }

  // Findings: one dot per domain lane, threaded vertically when cross-domain.
  findings.sort(function (a, b) { return a.date - b.date || (a.title < b.title ? -1 : 1); });
  findings.forEach(function (f) {
    var r = EV_RADIUS[f.evidence] || 5.5;
    makeMarker(f, function (a) {
      var pts = f.domains.map(function (d) {
        var i = laneIndex(d);
        return { x: x(f.date) + slotOffset(i, f.date), y: laneY(i) };
      }).sort(function (p, q) { return p.y - q.y; });
      if (pts.length > 1) {
        var path = "M" + pts[0].x + " " + pts[0].y;
        for (var i = 1; i < pts.length; i++) {
          var mid = (pts[i - 1].y + pts[i].y) / 2;
          path += " C" + (pts[i - 1].x + 8) + " " + mid + " " + (pts[i].x + 8) + " " + mid +
                  " " + pts[i].x + " " + pts[i].y;
        }
        el("path", { d: path, "class": "tl-thread", "data-type": f.kind,
                     "data-cross": "1" }, gThreads).style.animationDelay = (seq * 45) + "ms";
      }
      pts.forEach(function (p) {
        var dot = el("circle", { cx: p.x, cy: p.y, r: r, "class": "tl-dot tl-dot--" + f.kind }, a);
        dot.style.animationDelay = (seq++ * 45) + "ms";
      });
    });
  });

  // Patterns: diamonds stacked within the patterns band by month.
  var patSlots = {};
  patterns.sort(function (a, b) { return a.date - b.date; });
  patterns.forEach(function (p) {
    var key = p.date.getFullYear() + "-" + p.date.getMonth();
    var row = patSlots[key] = (patSlots[key] || 0) + 1;
    var py = AXIS_H + 12 + ((row - 1) % 4) * 13;
    var px = x(p.date) + Math.floor((row - 1) / 4) * 18;
    makeMarker(p, function (a) {
      // Drop-lines to the involved domain lanes — revealed on hover/focus.
      p.domains.forEach(function (d) {
        el("line", { x1: px, y1: py, x2: px, y2: laneY(laneIndex(d)), "class": "tl-drop" }, a);
        el("circle", { cx: px, cy: laneY(laneIndex(d)), r: 3, "class": "tl-drop-end" }, a);
      });
      var dia = el("path", {
        d: "M" + px + " " + (py - 7) + " L" + (px + 7) + " " + py +
           " L" + px + " " + (py + 7) + " L" + (px - 7) + " " + py + " Z",
        "class": "tl-dia" + (p.status === "provisional" ? " tl-dia--prov" : "")
      }, a);
      dia.style.animationDelay = (seq++ * 45) + "ms";
    });
  });

  // ---- Tooltip --------------------------------------------------------------
  function showTip(ev, mark) {
    var codes = ev.domains.map(function (d) { return d.toUpperCase(); }).join(" · ");
    var badges = "";
    if (ev.kind === "pattern") {
      badges = '<span class="badge ' + (STATUS_BADGE[ev.status] || "badge--status") + '">' + esc(ev.status) + "</span>";
    } else {
      if (ev.evidence) badges += '<span class="badge badge--status">' + esc(ev.evidence) + "</span> ";
      if (ev.status) badges += '<span class="badge ' + (STATUS_BADGE[ev.status] || "badge--status") + '">' + esc(ev.status) + "</span>";
    }
    var kicker = ev.kind === "pattern"
      ? esc(ev.id) + " · since " + fmtDate(ev.date) + " · " + codes
      : esc(ev.kind).toUpperCase() + " · " + fmtDate(ev.date) + " · " + codes;
    var body = ev.kind === "pattern" ? ev.confirmation : ev.summary;
    tip.innerHTML =
      '<p class="tl-tip-kicker">' + kicker + "</p>" +
      '<p class="tl-tip-title">' + esc(ev.title) + "</p>" +
      '<p class="tl-tip-badges">' + badges + "</p>" +
      (body ? '<p class="tl-tip-body">' + esc(body) + "</p>" : "") +
      '<p class="tl-tip-cta">Read →</p>';
    tip.hidden = false;
    var board = root.querySelector(".tl-board").getBoundingClientRect();
    var m = mark.getBoundingClientRect();
    var left = m.left - board.left + m.width / 2 - tip.offsetWidth / 2;
    left = Math.max(8, Math.min(left, board.width - tip.offsetWidth - 8));
    var top = m.top - board.top - tip.offsetHeight - 10;
    if (top < 4) top = m.bottom - board.top + 10;
    tip.style.left = left + "px";
    tip.style.top = top + "px";
    mark.classList.add("is-hot");
  }
  function hideTip() {
    tip.hidden = true;
    var hot = root.querySelector(".is-hot");
    if (hot) hot.classList.remove("is-hot");
  }

  // ---- Filters ----------------------------------------------------------------
  var state = { filter: "all", cross: false };
  function applyFilters() {
    root.querySelectorAll("[data-type]").forEach(function (n) {
      var dim = (state.filter !== "all" && n.getAttribute("data-type") !== state.filter) ||
                (state.cross && n.getAttribute("data-cross") !== "1");
      n.classList.toggle("is-dim", dim);
      if (n.classList.contains("tl-mark")) n.setAttribute("tabindex", dim ? "-1" : "0");
    });
  }
  root.querySelectorAll(".tl-chip[data-filter]").forEach(function (chip) {
    chip.addEventListener("click", function () {
      root.querySelectorAll(".tl-chip[data-filter]").forEach(function (c) { c.classList.remove("is-active"); });
      chip.classList.add("is-active");
      state.filter = chip.getAttribute("data-filter");
      applyFilters(); hideTip();
    });
  });
  var crossChip = root.querySelector('[data-toggle="cross"]');
  crossChip.addEventListener("click", function () {
    state.cross = !state.cross;
    crossChip.setAttribute("aria-pressed", String(state.cross));
    crossChip.classList.toggle("is-active", state.cross);
    applyFilters(); hideTip();
  });

  // Scroll the latest activity into view.
  var scroller = root.querySelector(".tl-scroll");
  scroller.scrollLeft = scroller.scrollWidth;
})();
