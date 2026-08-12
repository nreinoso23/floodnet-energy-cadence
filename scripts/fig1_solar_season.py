# Repo adaptation of the project's original fig1_solar_season.py (kept in
# the project records, not published here). Logic and methods unchanged;
# only data and output paths were adapted to this repository layout
# (reads data/openmeteo, writes ../figures; PDF output dropped, PNG kept).
#!/usr/bin/env python3
"""Build fig1_solar_season from the cached Open-Meteo pull.

Follows `RUNBOOK-openmeteo-seasonal-figure.md` (project records, not published
here; the archived pull and its provenance are in data/openmeteo/).
Top panel: computed daylight hours
(NOAA, zenith 90.833 deg). Bottom panel: daily global horizontal irradiation in
kWh/m2 from Open-Meteo hourly shortwave_radiation. Sized 9.58 x 2.90 in to drop
into the poster's Figure 1 frame at 100 % scale.
"""
import csv, json, math, sys
import datetime as dt
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

import os
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(REPO, "data", "openmeteo",
                    "open_meteo_2025-07-01_2026-07-01.json")
FIGURES = os.path.join(REPO, "figures")

SURFACE   = "#fcfcfb"
INK       = "#0b0b0b"
INK2      = "#52514e"
MUTED     = "#898781"
GRID      = "#e1e0d9"
AXIS      = "#c3c2b7"
C_DAY     = "#2a78d6"
C_IRR     = "#eb6834"

# ---------------------------------------------------------------- load + gates
with open(DATA, encoding="utf-8") as f:
    payload = json.load(f)

h = payload["hourly"]
lat = payload["latitude"]          # grid-cell latitude the API returned

times = h["time"]
sw = h["shortwave_radiation"]

assert len(times) == 8784, f"hour count {len(times)} != 8784"
ts = [dt.datetime.fromisoformat(x) for x in times]
steps = {(b - a).total_seconds() for a, b in zip(ts, ts[1:])}
assert steps == {3600.0}, f"non-hourly steps: {sorted(steps)[:5]}"
assert all(v is not None for v in sw), "nulls in shortwave_radiation"
assert payload["hourly_units"]["shortwave_radiation"] == "W/m²", \
    payload["hourly_units"]["shortwave_radiation"]
assert all(v >= 0 for v in sw), "negative irradiance"
midnight_bad = sum(1 for t, v in zip(times, sw)
                   if int(t[11:13]) in (0, 1, 22, 23) and v > 0)
assert midnight_bad == 0, f"{midnight_bad} irradiant hours near midnight"

# ------------------------------------------------------------- daily reduction
daily = {}                                    # date -> [hourly W/m2]
for t, v in zip(ts, sw):
    daily.setdefault(t.date(), []).append(v)
days = sorted(d for d, vals in daily.items() if len(vals) == 24)
days = days[:365]                             # trim: inclusive range spans 366
assert len(days) == 365, len(days)
ghi = [sum(daily[d]) / 1000.0 for d in days]  # kWh/m2/day

annual_mean = sum(ghi) / len(ghi)
assert 3.5 <= annual_mean <= 4.8, f"annual mean {annual_mean:.3f} implausible"

WIN = 15                                      # centred rolling mean, ends None
half = WIN // 2
roll = [None] * len(ghi)
for i in range(half, len(ghi) - half):
    roll[i] = sum(ghi[i - half:i + half + 1]) / WIN

# ------------------------------------------------------- daylight (NOAA, calc)
def declination_deg(date):
    """Solar declination at local solar noon, NOAA algorithm."""
    jd = date.toordinal() + 1721424.5 + 0.5   # JD at local noon-ish (JD + 0.5)
    T = (jd - 2451545.0) / 36525.0
    L0 = (280.46646 + T * (36000.76983 + 0.0003032 * T)) % 360
    M = 357.52911 + T * (35999.05029 - 0.0001537 * T)
    Mr = math.radians(M)
    C = (math.sin(Mr) * (1.914602 - T * (0.004817 + 0.000014 * T))
         + math.sin(2 * Mr) * (0.019993 - 0.000101 * T)
         + math.sin(3 * Mr) * 0.000289)
    true_long = L0 + C
    omega = math.radians(125.04 - 1934.136 * T)
    app_long = true_long - 0.00569 - 0.00478 * math.sin(omega)
    eps0 = 23 + (26 + (21.448 - T * (46.8150 + T * (0.00059 - T * 0.001813))) / 60) / 60
    eps = eps0 + 0.00256 * math.cos(omega)
    return math.degrees(math.asin(math.sin(math.radians(eps))
                                  * math.sin(math.radians(app_long))))

def daylight_hours(date, lat_deg):
    decl = math.radians(declination_deg(date))
    la = math.radians(lat_deg)
    cosH = (math.cos(math.radians(90.833)) / (math.cos(la) * math.cos(decl))
            - math.tan(la) * math.tan(decl))
    if cosH >= 1:
        return 0.0
    if cosH <= -1:
        return 24.0
    return 2 * math.degrees(math.acos(cosH)) / 15

for d, want in [(dt.date(2025, 6, 20), 15.083),
                (dt.date(2025, 12, 21), 9.250),
                (dt.date(2026, 3, 20), 12.133)]:
    got = daylight_hours(d, lat)
    assert abs(got - want) < 0.05, f"daylight {d}: {got:.3f} vs {want}"

daylight = [daylight_hours(d, lat) for d in days]

# ------------------------------------------------------------------------- csv
with open(os.path.join(FIGURES, "fig1_solar_season_data.csv"),
          "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["date", "daylight_hours", "ghi_kwh_m2",
                f"ghi_rolling_mean_{WIN}d_centred"])
    for d, dl, g, r in zip(days, daylight, ghi, roll):
        w.writerow([d.isoformat(), f"{dl:.4f}", f"{g:.4f}",
                    "" if r is None else f"{r:.4f}"])

# ---------------------------------------------------------------------- figure
plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "text.color": INK, "axes.edgecolor": AXIS,
    "axes.labelcolor": INK2, "xtick.color": MUTED, "ytick.color": MUTED,
    "axes.labelsize": 12, "xtick.labelsize": 11, "ytick.labelsize": 11,
})

fig, (ax1, ax2) = plt.subplots(
    2, 1, sharex=True, figsize=(9.58, 2.90),
    gridspec_kw={"height_ratios": [1, 1.56], "hspace": 0.22})
fig.patch.set_facecolor(SURFACE)

x = [dt.datetime.combine(d, dt.time()) for d in days]

for ax in (ax1, ax2):
    ax.set_facecolor(SURFACE)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(AXIS)
    ax.spines["bottom"].set_color(AXIS)
    ax.grid(axis="y", color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)
    ax.tick_params(length=3, width=0.8, color=AXIS)

# top: daylight, line only, truncated axis is fine for a line
ax1.plot(x, daylight, color=C_DAY, linewidth=2.2)
ax1.set_ylim(8, 16)
ax1.set_yticks([8, 10, 12, 14, 16])
ax1.set_ylabel("Daylight\n(hours)", labelpad=8)

i_max = max(range(365), key=lambda i: daylight[i])
i_min = min(range(365), key=lambda i: daylight[i])
ax1.plot([x[i_max]], [daylight[i_max]], "o", color=C_DAY, markersize=4.5)
ax1.plot([x[i_min]], [daylight[i_min]], "o", color=C_DAY, markersize=4.5)
ax1.annotate(f"{daylight[i_max]:.1f} h", (x[i_max], daylight[i_max]),
             xytext=(-10, -18), textcoords="offset points", ha="right",
             fontsize=12, fontweight="bold", color=INK)
ax1.annotate(f"{daylight[i_min]:.1f} h", (x[i_min], daylight[i_min]),
             xytext=(0, 8), textcoords="offset points", ha="center",
             fontsize=12, fontweight="bold", color=INK)

# bottom: daily hairlines from zero + bold centred rolling mean
ax2.vlines(x, 0, ghi, color=C_IRR, alpha=0.38, linewidth=1.2)
rx = [xx for xx, r in zip(x, roll) if r is not None]
ry = [r for r in roll if r is not None]
ax2.plot(rx, ry, color=C_IRR, linewidth=2.5)
ax2.set_ylim(0, 9)
ax2.set_yticks([0, 2, 4, 6, 8])
ax2.set_ylabel("Solar energy\n(kWh/m² per day)", labelpad=8)

j_max = max(range(len(ry)), key=lambda i: ry[i])
j_min = min(range(len(ry)), key=lambda i: ry[i])
ax2.plot([rx[j_max]], [ry[j_max]], "o", color=C_IRR, markersize=4.5)
ax2.plot([rx[j_min]], [ry[j_min]], "o", color=C_IRR, markersize=4.5)
ax2.annotate(f"{ry[j_max]:.1f}", (rx[j_max], ry[j_max]),
             xytext=(-8, 8), textcoords="offset points", ha="right",
             fontsize=12, fontweight="bold", color=INK)
ax2.annotate(f"{ry[j_min]:.1f}", (rx[j_min], ry[j_min]),
             xytext=(0, 8), textcoords="offset points", ha="center",
             fontsize=12, fontweight="bold", color=INK)

ax2.xaxis.set_major_locator(mdates.MonthLocator())
ax2.xaxis.set_major_formatter(mdates.DateFormatter("%b"))
ax2.set_xlim(x[0], x[-1])

fig.align_ylabels((ax1, ax2))
fig.subplots_adjust(left=0.088, right=0.985, top=0.97, bottom=0.14)
fig.savefig(os.path.join(FIGURES, "fig1_solar_season.png"),
            dpi=400, facecolor=SURFACE)

print(f"annual mean GHI : {annual_mean:.3f} kWh/m2/day")
print(f"daylight max/min: {daylight[i_max]:.3f} ({days[i_max]}) / "
      f"{daylight[i_min]:.3f} ({days[i_min]})")
print(f"rolling max/min : {ry[j_max]:.3f} / {ry[j_min]:.3f}")
print("wrote figures/fig1_solar_season.png and _data.csv")
