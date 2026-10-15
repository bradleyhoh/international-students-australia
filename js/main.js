// Embeds every Vega-Lite spec in js/specs into its matching <div> on the page,
// then adds entrance animations when each chart scrolls into view.
// A shared config keeps fonts and colours consistent across all charts.

const SANS = "'Source Sans 3', 'Helvetica Neue', Arial, sans-serif";

const theme = {
  font: SANS,
  background: null,
  view: { stroke: null },
  axis: {
    labelFont: SANS,
    titleFont: SANS,
    labelColor: "#4B5563",
    titleColor: "#374151",
    labelFontSize: 12,
    titleFontSize: 12.5,
    titleFontWeight: 600,
    domainColor: "#9CA3AF",
    tickColor: "#9CA3AF",
    gridColor: "#EEEAE3"
  },
  legend: {
    labelFont: SANS,
    titleFont: SANS,
    labelColor: "#374151",
    titleColor: "#374151",
    labelFontSize: 12,
    titleFontSize: 12.5,
    titleFontWeight: 600
  },
  header: { labelFont: SANS, titleFont: SANS },
  text: { font: SANS, fontSize: 12 },
  title: { font: SANS, fontWeight: 700 }
};

// [element, spec, entrance animation]
//   wipe-x  : marks are revealed left to right (time runs left to right)
//   wipe-up : marks grow from the bottom (like bars rising)
//   wipe-down: marks fill from the top (the waffle fills in reading order)
//   fade    : marks fade in (maps)
//   grow    : flow lines grow from each origin towards Australia (Vega param)
//   bubbles : circles fade in one by one, largest first
const charts = [
  ["#vis01", "js/specs/01_national_trend.vl.json", "wipe-x"],
  ["#vis02", "js/specs/02_sector_waffle.vl.json", "wipe-down"],
  ["#vis03", "js/specs/03_sector_trend.vl.json", "wipe-x"],
  ["#vis04", "js/specs/04_flow_map.vl.json", "grow"],
  ["#vis05", "js/specs/05_world_choropleth.vl.json", "fade"],
  ["#vis06", "js/specs/06_bump_chart.vl.json", "wipe-x"],
  ["#vis07", "js/specs/07_new_students_heatmap.vl.json", "wipe-x"],
  ["#vis08", "js/specs/08_state_choropleth.vl.json", "fade"],
  ["#vis09", "js/specs/09_sa4_symbols.vl.json", "bubbles"],
  ["#vis10", "js/specs/10_state_streamgraph.vl.json", "wipe-x"],
  ["#vis11", "js/specs/11_field_heatmap.vl.json", "wipe-x"],
  ["#vis12", "js/specs/12_slope_share.vl.json", "wipe-x"],
  ["#vis13", "js/specs/13_sector_marimekko.vl.json", "wipe-up"]
];

const options = {
  actions: { export: true, source: true, compiled: false, editor: true },
  config: theme,
  renderer: "svg"
};

const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
const canObserve = "IntersectionObserver" in window;
const EASE = "cubic-bezier(0.22, 0.61, 0.36, 1)";

// ---------- chart entrance animations ----------

// Data marks (not axes or legends). Text marks are handled separately so
// annotations appear after the data they describe.
const DATA_MARKS = ["line", "area", "rect", "symbol", "rule", "shape", "trail", "arc"]
  .map((t) => `g.mark-${t}.role-mark`).join(",");

function animateClip(groups, from, duration, delay) {
  groups.forEach((g) => {
    g.animate([{ clipPath: from }, { clipPath: "inset(0 0 0 0)" }],
      { duration, delay, easing: EASE, fill: "backwards" });
  });
}

function fadeTexts(svg, delay) {
  svg.querySelectorAll("g.mark-text.role-mark").forEach((g) => {
    g.animate([{ opacity: 0 }, { opacity: 1 }], { duration: 500, delay, easing: "ease-out", fill: "backwards" });
  });
}

function animateGrow(view) {
  // Flow lines are drawn as short segments; the "grow" param hides segments
  // further along each curve than the current value, so animating it from 0 to 1
  // makes every flow grow from its origin towards Australia.
  const duration = 1800;
  const start = performance.now();
  view.signal("grow", 0).run();
  function step(now) {
    const t = Math.min(1, (now - start) / duration);
    const eased = 1 - Math.pow(1 - t, 3);
    view.signal("grow", eased).run();
    if (t < 1) requestAnimationFrame(step);
  }
  requestAnimationFrame(step);
}

function animateChart(el, kind, view) {
  const svg = el.querySelector("svg");
  if (!svg) return;
  const groups = [...svg.querySelectorAll(DATA_MARKS)];
  switch (kind) {
    case "wipe-x":
      animateClip(groups, "inset(0 100% 0 0)", 1400, 100);
      fadeTexts(svg, 1100);
      break;
    case "wipe-up":
      animateClip(groups, "inset(100% 0 0 0)", 1100, 100);
      fadeTexts(svg, 900);
      break;
    case "wipe-down":
      animateClip(groups, "inset(0 0 100% 0)", 1100, 100);
      fadeTexts(svg, 900);
      break;
    case "fade":
      groups.forEach((g) => g.animate([{ opacity: 0 }, { opacity: 1 }],
        { duration: 900, delay: 100, easing: "ease-out", fill: "backwards" }));
      fadeTexts(svg, 800);
      break;
    case "bubbles": {
      // the circles are the only symbol mark; fade them in one by one, largest first
      const circles = [...svg.querySelectorAll("g.mark-symbol.role-mark path")];
      circles.forEach((c, i) => {
        const target = getComputedStyle(c).opacity;
        c.animate([{ opacity: 0 }, { opacity: target }],
          { duration: 500, delay: 200 + i * 35, easing: "ease-out", fill: "backwards" });
      });
      fadeTexts(svg, 200 + circles.length * 35);
      break;
    }
    case "grow":
      animateGrow(view);
      fadeTexts(svg, 1500);
      break;
  }
}

const pendingReveals = new Set();

function whenVisible(el, callback) {
  if (!canObserve) { callback(); return; }
  let done = false;
  const run = () => {
    if (done) return;
    done = true;
    io.disconnect();
    pendingReveals.delete(run);
    callback();
  };
  const io = new IntersectionObserver((entries) => {
    entries.forEach((entry) => { if (entry.isIntersecting) run(); });
  }, { threshold: 0.3 });
  io.observe(el);
  // backup check on scroll, in case the observer misses a fast jump (e.g. a nav link)
  run.check = () => {
    const r = el.getBoundingClientRect();
    if (r.top < window.innerHeight * 0.85 && r.bottom > window.innerHeight * 0.15) run();
  };
  pendingReveals.add(run);
}

let scrollTick = false;
function checkPending() {
  scrollTick = false;
  pendingReveals.forEach((run) => run.check());
}
window.addEventListener("scroll", () => {
  if (!scrollTick) { scrollTick = true; requestAnimationFrame(checkPending); }
}, { passive: true });
window.addEventListener("resize", checkPending);
// when printing, show every chart straight away
window.addEventListener("beforeprint", () => pendingReveals.forEach((run) => run()));

// ---------- play button for the flow map ----------

function setUpPlay(view) {
  const btn = document.getElementById("play04");
  if (!btn) return;
  let timer = null;
  const stop = () => {
    clearInterval(timer);
    timer = null;
    btn.textContent = "▶ Play 2005–2025";
    btn.setAttribute("aria-pressed", "false");
  };
  btn.addEventListener("click", () => {
    if (timer) { stop(); return; }
    let year = view.signal("year");
    if (year >= 2025) year = 2004;          // start again from the beginning
    view.signal("grow", 1);
    btn.textContent = "❚❚ Pause";
    btn.setAttribute("aria-pressed", "true");
    timer = setInterval(() => {
      year += 1;
      view.signal("year", year).run();
      if (year >= 2025) stop();
    }, reduceMotion ? 1200 : 650);
  });
}

// ---------- embed every chart ----------

// Wait for the web fonts first, so Vega measures label widths with the real font
// (otherwise legends and labels can overlap once the font arrives).
const fontsReady = Promise.race([
  document.fonts ? document.fonts.ready : Promise.resolve(),
  new Promise((resolve) => setTimeout(resolve, 2500))
]);

fontsReady.then(() => charts.forEach(([sel, spec, kind]) => {
  const el = document.querySelector(sel);
  vegaEmbed(el, spec, options)
    .then((result) => {
      if (sel === "#vis04") setUpPlay(result.view);
      if (reduceMotion) return;
      // hide data marks until the chart is on screen, so the animation is seen
      if (canObserve) {
        if (kind === "grow") result.view.signal("grow", 0).run();
        else el.style.visibility = "hidden";
      }
      whenVisible(el, () => {
        el.style.visibility = "";
        animateChart(el, kind, result.view);
      });
    })
    .catch((err) => {
      console.error(spec, err);
      el.innerHTML = '<p style="color:#B3202E">This chart failed to load: ' + spec + "</p>";
    });
}));

// ---------- page-level motion: count-up numbers and fade-up cards ----------

function countUp(node) {
  const target = Number(node.dataset.count);
  const suffix = node.dataset.suffix || "";
  const duration = 1400;
  const start = performance.now();
  function step(now) {
    const t = Math.min(1, (now - start) / duration);
    const eased = 1 - Math.pow(1 - t, 3);
    node.textContent = Math.round(target * eased).toLocaleString("en-AU") + (t === 1 ? suffix : "");
    if (t < 1) requestAnimationFrame(step);
  }
  requestAnimationFrame(step);
}

if (!reduceMotion) {
  document.querySelectorAll(".stat .num[data-count]").forEach(countUp);
}

const revealTargets = document.querySelectorAll(".card, .side-text, .note, .takeaways li");
if (reduceMotion || !canObserve) {
  revealTargets.forEach((n) => n.classList.remove("reveal"));
} else {
  const io = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) { entry.target.classList.add("in"); io.unobserve(entry.target); }
    });
  }, { threshold: 0.12 });
  revealTargets.forEach((n) => { n.classList.add("reveal"); io.observe(n); });
}
