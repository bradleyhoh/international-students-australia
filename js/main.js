// Embeds every Vega-Lite spec in js/specs into its matching <div> on the page.
// A shared config keeps fonts and colours consistent across all charts.

const theme = {
  font: "Figtree, system-ui, sans-serif",
  background: null,
  view: { stroke: null },
  axis: {
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
    labelColor: "#374151",
    titleColor: "#374151",
    labelFontSize: 12,
    titleFontSize: 12.5,
    titleFontWeight: 600
  },
  header: { labelFont: "Figtree, sans-serif" },
  text: { font: "Figtree, sans-serif", fontSize: 12 },
  title: { font: "Young Serif, Georgia, serif", fontWeight: 400 }
};

const charts = [
  ["#vis01", "js/specs/01_national_trend.vl.json"],
  ["#vis02", "js/specs/02_sector_waffle.vl.json"],
  ["#vis03", "js/specs/03_sector_trend.vl.json"],
  ["#vis04", "js/specs/04_flow_map.vl.json"],
  ["#vis05", "js/specs/05_world_choropleth.vl.json"],
  ["#vis06", "js/specs/06_bump_chart.vl.json"],
  ["#vis07", "js/specs/07_new_students_heatmap.vl.json"],
  ["#vis08", "js/specs/08_state_choropleth.vl.json"],
  ["#vis09", "js/specs/09_sa4_symbols.vl.json"],
  ["#vis10", "js/specs/10_state_streamgraph.vl.json"],
  ["#vis11", "js/specs/11_field_heatmap.vl.json"],
  ["#vis12", "js/specs/12_slope_share.vl.json"],
  ["#vis13", "js/specs/13_sector_marimekko.vl.json"]
];

const options = {
  actions: { export: true, source: true, compiled: false, editor: true },
  config: theme,
  renderer: "svg"
};

charts.forEach(([el, spec]) => {
  vegaEmbed(el, spec, options).catch((err) => {
    console.error(spec, err);
    document.querySelector(el).innerHTML =
      '<p style="color:#B3202E">This chart failed to load: ' + spec + "</p>";
  });
});
