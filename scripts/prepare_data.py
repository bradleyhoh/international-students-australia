"""
Prepare small, tidy CSV files for the Vega-Lite charts.

Inputs (raw/, downloaded from the original publishers):
  INTED_studentPublic_New_Student.csv  Department of Education - student head count by nationality and state, 2005-2026
  INTED_nationalitySummary.csv         Department of Education - enrolments by nationality, sector, level and field (Dec 2025, Jun 2026)
  INTED_sa4_enrolment.csv              Department of Education - enrolments by ABS SA4 region and sector, 2018-2026
  SA4_centroids.csv                    Centroids computed from the Department's ABS SA4 2021 boundary file
  abs_erp_state_2025Q4.csv             ABS Estimated Resident Population by state, Dec quarter 2025
  worldbank_population_2025.csv        World Bank population (SP.POP.TOTL), 2025
  world50m_centroids.csv               Country centroids from Natural Earth (world-atlas) via d3-geo

Run:  python3 scripts/prepare_data.py
Output: data/*.csv  (each file is only a few KB so the page loads quickly)
"""
from pathlib import Path
import pandas as pd
import pycountry

ROOT = Path(__file__).resolve().parents[1]
RAW, OUT = ROOT / "raw", ROOT / "data"
OUT.mkdir(exist_ok=True)

LATEST = 2025          # latest full calendar year (December year-to-date)
MALAYSIA = "Malaysia"

# Department of Education names -> Natural Earth (world-atlas) names
NAME_FIX = {
    "Antigua and Barbuda": "Antigua and Barb.", "Bosnia and Herzegovina": "Bosnia and Herz.",
    "Brunei Darussalam": "Brunei", "Congo, Democratic Republic of": "Dem. Rep. Congo",
    "Congo, Republic of": "Congo", "Cook Islands": "Cook Is.", "Cote d'Ivoire": "Côte d'Ivoire",
    "Czech Republic": "Czechia", "Dominican Republic": "Dominican Rep.", "Equatorial Guinea": "Eq. Guinea",
    "Falkland Islands": "Falkland Is.", "French Polynesia": "Fr. Polynesia", "Gaza Strip and West Bank": "Palestine",
    "Hong Kong SAR": "Hong Kong", "Korea Republic of (South)": "South Korea",
    "Korea, Democratic People's Republic of (North)": "North Korea", "Macau": "Macao",
    "Marshall Islands": "Marshall Is.", "Micronesia, Federated States of": "Micronesia",
    "North Macedonia": "Macedonia", "Russian Federation": "Russia", "Sao Tome and Principe": "São Tomé and Principe",
    "Solomon Islands": "Solomon Is.", "South Sudan": "S. Sudan", "St Helena": "Saint Helena",
    "St Kitts and Nevis": "St. Kitts and Nevis", "St Lucia": "Saint Lucia", "Turkiye": "Turkey",
    "Virgin Islands, British": "British Virgin Is.", "Swaziland": "eSwatini",
}
# Short display names for labels
SHORT = {"Korea Republic of (South)": "South Korea", "United States of America": "USA",
         "Hong Kong SAR": "Hong Kong", "United Kingdom": "UK"}


def short(n):
    return SHORT.get(n, n)


# ---------- 1. Head count by nationality and state (2005-2025) ----------
st = pd.read_csv(RAW / "INTED_studentPublic_New_Student.csv")
st = st[(st.Month == "Dec") & (st.Year <= LATEST)]

nat = st[(st.State == "_All") & (st.Nationality != "_All")].copy()
nat = nat[~nat.Nationality.isin(["Other", "United Kingdom (Other)", "United States (Territories)"])]
nat["rank"] = nat.groupby("Year").Students.rank(ascending=False, method="first").astype(int)

# national trend
national = st[(st.State == "_All") & (st.Nationality == "_All")][["Year", "Students", "New_Students"]]
national.columns = ["year", "students", "new_students"]
national.to_csv(OUT / "national_trend.csv", index=False)

# bump chart: today's top 10 + Malaysia, ranked against all countries each year
top10 = nat[nat.Year == LATEST].nsmallest(10, "rank").Nationality.tolist()
keep = top10 + ([MALAYSIA] if MALAYSIA not in top10 else [])
bump = nat[nat.Nationality.isin(keep)][["Year", "Nationality", "Students", "rank"]].copy()
bump["country"] = bump.Nationality.map(short)
bump = bump.rename(columns={"Year": "year", "Students": "students"})[["year", "country", "students", "rank"]]
bump.to_csv(OUT / "rank_trend.csv", index=False)

# heatmap: new students by year for the top 12 countries + Malaysia
top12 = nat[nat.Year == LATEST].nsmallest(12, "rank").Nationality.tolist()
keep12 = top12 + ([MALAYSIA] if MALAYSIA not in top12 else [])
hm = nat[nat.Nationality.isin(keep12)][["Year", "Nationality", "New_Students", "Students"]].copy()
hm["country"] = hm.Nationality.map(short)
hm = hm.rename(columns={"Year": "year", "New_Students": "new_students", "Students": "students"})
hm[["year", "country", "new_students", "students"]].to_csv(OUT / "new_students_heatmap.csv", index=False)

# ---------- 2. Country table for world maps ----------
cent = pd.read_csv(RAW / "world50m_centroids.csv", dtype={"id": str})
pop = pd.read_csv(RAW / "worldbank_population_2025.csv")


def iso3_for(numeric_id):
    c = pycountry.countries.get(numeric=numeric_id) if isinstance(numeric_id, str) else None
    return c.alpha_3 if c else None


latest = nat[nat.Year == LATEST][["Nationality", "Students", "New_Students"]].copy()
latest["geo_name"] = latest.Nationality.map(lambda n: NAME_FIX.get(n, n))
latest = latest.merge(cent, left_on="geo_name", right_on="name", how="left")
latest["iso3"] = latest.id.map(iso3_for)
latest.loc[latest.Nationality == "Kosovo", "iso3"] = "XKX"
latest = latest.merge(pop, on="iso3", how="left")
latest["per_100k"] = (latest.Students / latest.population_2025 * 1e5).round(1)
latest["country"] = latest.Nationality.map(short)
latest["id"] = latest.id.map(lambda v: f"{int(v):03d}" if pd.notna(v) else "")
countries = latest[["id", "iso3", "country", "Students", "New_Students", "population_2025", "per_100k", "lon", "lat"]]
countries = countries.rename(columns={"Students": "students", "New_Students": "new_students", "population_2025": "population"})
countries.to_csv(OUT / "countries_2025.csv", index=False)
unmatched = latest[latest.lon.isna()].Nationality.tolist()
print("Countries without geometry (left out of maps):", unmatched)

# flow map: top 30 source countries per year with their centroid
flows = nat.merge(latest[["Nationality", "lon", "lat"]], on="Nationality", how="inner")
flows = flows[flows["rank"] <= 30].dropna(subset=["lon"])
flows["country"] = flows.Nationality.map(short)
flows = flows.rename(columns={"Year": "year", "Students": "students"})
flows[["year", "country", "students", "rank", "lon", "lat"]].to_csv(OUT / "flows.csv", index=False)

# ---------- 3. States ----------
states = st[(st.Nationality == "_All") & (st.State.isin(["NSW", "VIC", "QLD", "SA", "WA", "TAS", "NT", "ACT"]))]
states = states[["Year", "State", "Students"]].rename(columns={"Year": "year", "State": "state", "Students": "students"})
states.to_csv(OUT / "state_trend.csv", index=False)

erp = pd.read_csv(RAW / "abs_erp_state_2025Q4.csv")
s25 = states[states.year == LATEST].merge(erp, left_on="state", right_on="state_code")
s25["per_1000"] = (s25.students / s25.erp * 1000).round(1)
s25 = s25.rename(columns={"state_y": "state_name", "state_x": "state"})
labels = pd.read_csv(RAW / "state_label_points.csv")   # label positions computed from the state boundaries
s25 = s25.merge(labels, on="state_name", how="left")
s25[["state", "state_name", "students", "erp", "per_1000", "label_lon", "label_lat"]].to_csv(OUT / "states_2025.csv", index=False)

# ---------- 4. SA4 regions and sectors (enrolments) ----------
sa = pd.read_csv(RAW / "INTED_sa4_enrolment.csv")
tot = (sa.Nationality == "_Total") & (sa["Level Of Study"] == "_Total") & \
      (sa["Broad Field Of Education"] == "_Total") & (sa.ABSRemotenessArea == "_Total")
dec = sa.Month == "Dec"

sa4 = sa[tot & dec & (sa.Year == LATEST) & (sa.Sector == "_Total")]
sa4 = sa4.groupby(["State", "SA4_NAME21"], as_index=False)[["Enrolment", "Commencement"]].sum()
c4 = pd.read_csv(RAW / "SA4_centroids.csv")
sa4 = sa4.merge(c4[["SA4_NAME21", "GCC_NAME21", "lon", "lat"]], on="SA4_NAME21", how="left")
sa4["area_type"] = sa4.GCC_NAME21.str.startswith("Greater").map({True: "Capital city", False: "Regional"})
sa4.loc[sa4.GCC_NAME21 == "Australian Capital Territory", "area_type"] = "Capital city"
sa4 = sa4.rename(columns={"State": "state", "SA4_NAME21": "region", "Enrolment": "enrolments", "Commencement": "commencements"})
sa4 = sa4[sa4.enrolments > 0].dropna(subset=["lon"])
sa4[["state", "region", "area_type", "enrolments", "commencements", "lon", "lat"]].to_csv(OUT / "sa4_2025.csv", index=False)

sector = sa[tot & dec & (sa.Year <= LATEST) & (sa.Sector != "_Total")]
sector = sector.groupby(["Year", "Sector"], as_index=False).Enrolment.sum()
sector.columns = ["year", "sector", "enrolments"]
sector.to_csv(OUT / "sector_trend.csv", index=False)

# waffle: 100 squares for 2025 sector shares (largest-remainder rounding)
s = sector[sector.year == LATEST].set_index("sector").enrolments
share = s / s.sum() * 100
cells = share.astype(int)
for k in (share - cells).sort_values(ascending=False).index[: 100 - cells.sum()]:
    cells[k] += 1
order = ["Higher Education", "VET", "ELICOS", "Non-award", "Schools"]
rows, i = [], 0
for sec in order:
    for _ in range(int(cells[sec])):
        rows.append({"cell": i, "col": i % 10, "row": i // 10, "sector": sec,
                     "sector_share": round(share[sec], 1), "sector_enrolments": int(s[sec])})
        i += 1
pd.DataFrame(rows).to_csv(OUT / "sector_waffle_2025.csv", index=False)

# ---------- 5. Field of study by nationality (universities, Dec 2025) ----------
ns = pd.read_csv(RAW / "INTED_nationalitySummary.csv")
he = ns[(ns.Year == LATEST) & (ns.Month == "Dec") & (ns.Sector == "Higher Education") &
        (ns["Level Of Study"] == "_All") & (ns.Nationality != "_All")]
he_tot = he[he["Broad Field Of Education"] == "_All"][["Nationality", "Enrolments"]].rename(columns={"Enrolments": "total"})
field = he[~he["Broad Field Of Education"].isin(["_All", "_Dual Qualification", "Mixed Field Programmes"])]
top_he = he_tot.nlargest(12, "total").Nationality.tolist()
if MALAYSIA not in top_he:
    top_he.append(MALAYSIA)
field = field[field.Nationality.isin(top_he)].merge(he_tot, on="Nationality")
field["share"] = (field.Enrolments / field.total * 100).round(1)
field["country"] = field.Nationality.map(short)
FIELD_SHORT = {"Management and Commerce": "Business", "Information Technology": "IT",
               "Engineering and Related Technologies": "Engineering", "Health": "Health",
               "Society and Culture": "Society & culture", "Natural and Physical Sciences": "Science",
               "Architecture and Building": "Architecture", "Creative Arts": "Creative arts",
               "Education": "Education", "Agriculture, Environmental and Related Studies": "Agriculture & environment",
               "Food, Hospitality and Personal Services": "Hospitality"}
field["field_short"] = field["Broad Field Of Education"].map(FIELD_SHORT)
field = field.rename(columns={"Broad Field Of Education": "field", "Enrolments": "enrolments"})
field[["country", "field", "field_short", "enrolments", "total", "share"]].to_csv(OUT / "field_by_country_2025.csv", index=False)

# ---------- 6. Slope chart: share of all students, 2015 vs 2025 ----------
total = national.set_index("year").students
# the top 6 sources in 2015 and in 2025, plus Malaysia (9 countries), so a linear scale stays readable
top6 = lambda y: nat[nat.Year == y].nsmallest(6, "rank").Nationality.tolist()
slope_keep = list(dict.fromkeys(top6(2015) + top6(LATEST) + [MALAYSIA]))
slope = nat[nat.Year.isin([2015, LATEST]) & nat.Nationality.isin(slope_keep)][["Year", "Nationality", "Students"]].copy()
slope["share"] = (slope.Students / slope.Year.map(total) * 100).round(1)
slope["country"] = slope.Nationality.map(short)


def dodge(values, gap):
    """Spread label positions so neighbouring labels are at least `gap` apart (keeps order)."""
    order = sorted(range(len(values)), key=lambda i: values[i])
    pos = [values[i] for i in order]
    for _ in range(200):                       # relax overlaps from both directions
        for k in range(1, len(pos)):
            if pos[k] - pos[k - 1] < gap:
                mid = (pos[k] + pos[k - 1]) / 2
                pos[k - 1], pos[k] = mid - gap / 2, mid + gap / 2
        pos = [max(p, 0) for p in pos]
    out = [0] * len(values)
    for k, i in enumerate(order):
        out[i] = round(pos[k], 2)
    return out


# Linear scale 0-30% on a 460 px tall chart: 1 percentage point is about 15 px, so labels need 1.0 apart.
slope["label_y"] = 0.0
for y in (2015, LATEST):
    m = slope.Year == y
    slope.loc[m, "label_y"] = dodge(slope.loc[m, "share"].tolist(), 1.0)
slope = slope.rename(columns={"Year": "year", "Students": "students"})
slope[["year", "country", "students", "share", "label_y"]].to_csv(OUT / "slope_share.csv", index=False)

# ---------- 7. Marimekko: education sector mix of the largest source countries, Dec 2025 ----------
sec = ns[(ns.Year == LATEST) & (ns.Month == "Dec") & (ns["Level Of Study"] == "_All") &
         (ns["Broad Field Of Education"] == "_All") & (ns.Nationality != "_All")]
ctot = sec[sec.Sector == "_All"][["Nationality", "Enrolments"]].rename(columns={"Enrolments": "country_total"})
mk_keep = ctot.nlargest(10, "country_total").Nationality.tolist()
if MALAYSIA not in mk_keep:
    mk_keep.append(MALAYSIA)
mk = sec[(sec.Sector != "_All") & sec.Nationality.isin(mk_keep)][["Nationality", "Sector", "Enrolments"]]
mk = mk.merge(ctot, on="Nationality")
mk["country"] = mk.Nationality.map(short)
mk = mk.rename(columns={"Sector": "sector", "Enrolments": "enrolments"})
mk["share"] = (mk.enrolments / mk.country_total * 100).round(1)
mk[["country", "sector", "enrolments", "country_total", "share"]].to_csv(OUT / "sector_by_country_2025.csv", index=False)

# ---------- 8. Malaysia vs all: indexed growth since 2005 ----------
my_trend = nat[nat.Nationality == MALAYSIA][["Year", "Students"]].rename(columns={"Year": "year", "Students": "students"})
my_trend["group"] = "Malaysians"
all_trend = national[["year", "students"]].copy()
all_trend["group"] = "All international students"
idx = pd.concat([all_trend, my_trend])
base = idx[idx.year == 2005].set_index("group").students
idx["index"] = (idx.students / idx.group.map(base) * 100).round(1)
idx[["year", "group", "students", "index"]].to_csv(OUT / "malaysia_index.csv", index=False)

# ---------- 9. Where Malaysians study vs all international students (state shares, 2025) ----------
STATES = ["NSW", "VIC", "QLD", "WA", "SA", "ACT", "TAS", "NT"]
s25_all = st[(st.Year == LATEST) & (st.Nationality == "_All") & st.State.isin(STATES)].set_index("State").Students
s25_my = st[(st.Year == LATEST) & (st.Nationality == MALAYSIA) & st.State.isin(STATES)].set_index("State").Students
rows = []
for code in STATES:
    rows.append({"state": code, "group": "All international students", "students": int(s25_all[code]),
                 "share": round(s25_all[code] / s25_all.sum() * 100, 1)})
    rows.append({"state": code, "group": "Malaysians", "students": int(s25_my[code]),
                 "share": round(s25_my[code] / s25_my.sum() * 100, 1)})
pd.DataFrame(rows).to_csv(OUT / "malaysia_states_2025.csv", index=False)

print("Done. Files written to", OUT)
for f in sorted(OUT.glob("*.csv")):
    print(f"  {f.name:32s} {f.stat().st_size/1024:6.1f} KB")
