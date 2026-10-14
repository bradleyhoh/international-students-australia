# Destination Australia: International Students, 2005–2025

FIT3179 Data Visualisation 2, Brendan Hoh, October 2026.

A one-page, scrollable data story about international students in Australia, written for a Malaysian audience. All charts are built with [Vega-Lite 5](https://vega.github.io/vega-lite/).

Live site: https://bradleyhoh.github.io/international-students-australia/

## Repository layout

```
index.html                 the page
css/style.css              layout and typography
js/main.js                 embeds each chart with a shared theme
js/specs/*.vl.json         one Vega-Lite specification per chart (13 charts)
data/*.csv                 cleaned data used by the charts
data/geo/                  TopoJSON boundaries (world, Australian states)
scripts/prepare_data.py    turns the raw downloads into data/*.csv
raw/                       original downloads (kept for reproducibility)
```

## Charts

| # | Spec | Idiom |
|---|------|-------|
| 1 | 01_national_trend | Annotated line and area chart |
| 2 | 02_sector_waffle | Waffle chart |
| 3 | 03_sector_trend | Small multiples (line) |
| 4 | 04_flow_map | Origin-destination flow map (curved flows, year slider) |
| 5 | 05_world_choropleth | Choropleth map (world, standardised) |
| 6 | 06_bump_chart | Bump chart |
| 7 | 07_new_students_heatmap | Heatmap |
| 8 | 08_state_choropleth | Choropleth map (Australia, standardised) |
| 9 | 09_sa4_symbols | Proportional symbol map |
| 10 | 10_state_streamgraph | Streamgraph |
| 11 | 11_field_heatmap | Heatmap |
| 12 | 12_slope_share | Slope chart |
| 13 | 13_sector_marimekko | Marimekko (mosaic) chart |

## Data sources

- Australian Government Department of Education, International Student Data (student numbers by nationality and state, 2005–2025; enrolments by sector, field and SA4 region, 2025).
- Australian Bureau of Statistics, National, state and territory population, December quarter 2025.
- World Bank, World Development Indicators, Population, total (SP.POP.TOTL).
- Natural Earth (via the `world-atlas` npm package) and ABS ASGS state and territory boundaries.

## Rebuilding the data

```
pip install pandas pycountry
python scripts/prepare_data.py
```

## AI acknowledgement

Generative AI (Claude, Anthropic) was used to help locate and process the data, write the Vega-Lite specifications and page code, and draft the text. The author checked the figures against the sources and is responsible for the final design and wording.
