# FIG1_PROVENANCE — fig1_solar_season

Produced 2026-08-08 by a Claude Code session following
`RUNBOOK-openmeteo-seasonal-figure.md` (project records, not published in this
repository). Build script: `scripts/fig1_solar_season.py`.
Every plotted value is in `fig1_solar_season_data.csv`, one row per day.
(Adapted for this repository: file paths updated; content otherwise unchanged.)

## What each panel is, and its source

| Panel | Quantity | Source |
|---|---|---|
| Top | Daylight hours, sunrise to sunset | **Computed**, NOAA solar-position algorithm at zenith 90.833° (refraction + solar semidiameter convention). No API data involved. |
| Bottom | Daily global horizontal irradiation (GHI), kWh/m²/day | **Open-Meteo Historical Weather (archive) API**, hourly `shortwave_radiation` (mean W/m² per hour) summed per calendar day ÷ 1000. |

The two panels are different sources and must be credited separately.

## Data pull

- Endpoint: `https://archive-api.open-meteo.com/v1/archive`
- Requested point: 40.7381, −74.0425; requested range 2025-07-01 → 2026-07-01,
  timezone America/New_York
- **Returned grid cell: 40.738136, −74.04254, elevation 2.0 m** — cite these
  coordinates, not a city name. The cell centre is ~3.1 km west of the Manhattan
  shoreline (Hoboken side).
- Model: **best_match (not pinned)** — the model name is unknown. Do not credit
  ERA5 or Copernicus.
- Retrieved: **2026-08-08T22:45:30Z** (UTC)
- Raw response: `data/openmeteo/open_meteo_2025-07-01_2026-07-01.json`, 296045 bytes,
  sha256 `7bbcb62da82d591069d8bcd07626fe8dc6a43baba348ffdaee179ba94d4baf5e`
- Manifest: `data/openmeteo/open_meteo_2025-07-01_2026-07-01.manifest.json`
- Note (matches runbook Trap 6): this pull returned `elevation: 2.0` where a
  July 2026 pull of the same cell returned `32.0`. The cached JSON is the
  archival object.

## Integrity gates run, with results

| Gate | Result |
|---|---|
| `scripts/fetch_openmeteo_archive.py --self-test` | PASSED (all cases) |
| Hour count = (366 days) × 24 = 8784 | PASS (8784) |
| All inter-sample steps exactly 1.0 h | PASS |
| Zero nulls in `shortwave_radiation` | PASS |
| Unit is `W/m²` | PASS |
| No negative irradiance | PASS |
| No irradiance in hours stamped 22/23/00/01 (midnight boundary check) | PASS → daily sums are frame-independent |
| Annual mean plausible for latitude 40.7 | PASS (4.27 kWh/m²/day, expected ~4.0–4.3) |
| Daylight asserts: 2025-06-20 = 15.083 h, 2025-12-21 = 9.250 h, 2026-03-20 = 12.133 h, tol 0.05 h | PASS (computed at the returned grid-cell latitude 40.738136) |
| Only complete 24-hour days kept; trimmed to exactly 365 days plotted | PASS (2025-07-01 → 2026-06-30) |
| Rolling mean is 15-day **centred**, ends left as gaps (no `min_periods` fill) | PASS |
| Palette `#2a78d6` / `#eb6834` on `#fcfcfb` | Validated per runbook record (CVD ΔE 24.7 protan, normal-vision ΔE 33.6, both ≥ 3:1 contrast). Node.js is not installed on this machine so the validator was not re-run; the palette is unchanged from the validated pair. |
| Rendered PNG opened and inspected against the Step 6 checklist | PASS (labels clear of data line, nothing clipped or in the gutter, rolling mean visibly stops short of both ends) |

## Numbers, each with its definition

All from the 365 plotted days (2025-07-01 → 2026-06-30), grid cell 40.738136, −74.04254.

| Number | Definition |
|---|---|
| 4.273 kWh/m²/day | annual mean daily GHI |
| 1559.8 kWh/m² | annual total GHI |
| 0.215 / 8.468 kWh/m²/day | minimum / maximum single-day GHI |
| 1.833 kWh/m²/day | December monthly-mean daily GHI |
| 6.929 kWh/m²/day | June monthly-mean daily GHI |
| **26.5 %** | December monthly mean ÷ June monthly mean (GHI) |
| 1.666 kWh/m²/day (2025-12-30) | minimum of the 15-day centred rolling mean |
| 7.641 kWh/m²/day (2026-06-10) | maximum of the 15-day centred rolling mean |
| **21.8 %** | rolling-mean minimum ÷ rolling-mean maximum (GHI) |
| 9.248 h / 15.096 h | daylight on 2025-12-21 / 2026-06-21 (solstices) |
| **61.3 %** | winter-solstice daylight ÷ summer-solstice daylight |
| 9.307 h / 15.044 h | December / June monthly-mean daylight |
| **61.9 %** | December monthly-mean daylight ÷ June monthly-mean daylight |

These match the values recorded in the runbook from the 2026-08-06 reproduction.
**Pick one definition per claim, state it, and use it everywhere.** Do not let
26.5 % and 21.8 % (or 61.9 % and 61.3 %) circulate as if they were the same
number. No ratio appears inside the figure itself.

## What this figure does not support

- It is **open-sky modelled irradiance for one grid cell**, not energy any
  sensor or panel collected. It says nothing about panel tilt, orientation,
  conversion efficiency, or battery charging.
- It contains **no shading** — no buildings, trees, or mounting geometry.
- **n = 1 year.** It is one specific July-to-July window, not a climatology;
  a different year will differ.
- The model behind the values is **unknown** (best_match, not pinned).
- The grid cell is ~3 km from the Manhattan shoreline; it is not a
  point measurement at any specific sensor site.
- Hourly timestamps from this API are not trustworthy as local clock time
  (runbook Trap 5); only the daily sums, protected by the midnight boundary
  check, are used here.

## Licence and attribution

- **Bottom panel:** Weather data by [Open-Meteo.com](https://open-meteo.com/),
  licensed [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)
  (Open-Meteo licence page: https://open-meteo.com/en/licence). **The data was
  changed:** hourly shortwave radiation was integrated to daily totals.
  Citation as given on the licence page (retrieved 2026-08-08):
  Zippenfenig, P. (2023). *Open-Meteo.com Weather API* [Computer software].
  Zenodo. https://doi.org/10.5281/ZENODO.7970649
- **Top panel:** computed daylight duration (NOAA solar-position algorithm,
  zenith 90.833°); no external data source, no licence obligation.

## AI-use record

Data retrieval (via the provenance-recording fetch script), integrity
validation, daylight computation, daily aggregation, figure rendering, and this
provenance note were produced with AI assistance (Claude Code, 2026-08-08).
No caption, title, or interpretive poster prose was drafted by AI.
