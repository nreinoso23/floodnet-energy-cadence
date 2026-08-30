# Repo adaptation of the project's original fig4_wakes_per_hour.py (kept in
# the project records, not published here). Logic and methods unchanged;
# only data and output paths were adapted to this repository layout
# (reads data/otii, writes ../figures).
"""Poster Figure 4: radio wakes per hour, computed from raw Otii data.
(The number is unchanged by the 2026-08 poster revision.)

Replaces `figE_wakes_per_hour.py` (project records) under the standing
rule. The drawing code reproduces figE's count-diagram style exactly; the
difference is that the wake counts per hour and the upload/keepalive split
are COMPUTED HERE from the two long captures at runtime.

Measured inputs (derived at runtime):
  - the 15-minute capture (`data/otii/15_min_data`,
    largest mc channel): radio wakes detected on 0.1-s means (threshold =
    median + 2 mA, gaps < 5 s merged, wakes >= 5 s kept; detector from
    `figD_midinterval_wake.py` (project records) via
    common_otii.detect_wakes) - all wakes are uploads (no wake below the
    700 mJ upload/keepalive energy boundary), and the median upload spacing
    gives the wakes-per-hour count;
  - the 30-minute capture (`...\\30_min_data`): same detector; wakes split by
    the 700 mJ boundary into uploads (~1.35 J) and keepalives (~0.25 J), with
    exactly one keepalive inside every complete upload-to-upload interval.

Consistency gate: 4 upload wakes/hour at 15-minute reporting and
2 uploads + 2 keepalives = 4 wakes/hour at 30-minute reporting, matching the
poster; anything else aborts (flag, never silently change).

Regenerate:  py fig4_wakes_per_hour.py   (writes fig4_wakes_per_hour.png)
"""
import os

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

from common_otii import (FIGURES, OTII, bin_100ms_ma, detect_wakes,
                         kmeans2_1d, longest_mc, steady_bins)

# A capture has a distinct keepalive population when two-cluster k-means on
# event energy separates well (30-min: ~0.24 vs ~1.33 J, ratio ~5.6, per
# `poster-claim3-verification.json`, project records); a ratio below 3
# means one population (the 15-min capture: all uploads, no keepalives).
SPLIT_RATIO = 3.0

# ---- measured inputs, computed from the raw recordings ----
# Both censuses detect on the steady window (first hour excluded, complete
# hours only); the boot hour contains non-cadence bursts.
y15, _ = steady_bins(bin_100ms_ma(longest_mc(os.path.join(OTII, "15_min_data"))))
w15 = detect_wakes(y15)
lo15, hi15 = kmeans2_1d([w[2] for w in w15])
split15 = hi15 / lo15
starts15 = np.array([w[0] for w in w15])
spacing15 = float(np.median(np.diff(starts15)))
per_hour_15 = 3600.0 / spacing15
print(f"15-min capture: {len(w15)} wakes, energy clusters {lo15:.0f}/{hi15:.0f} mJ "
      f"(ratio {split15:.2f}), median spacing {spacing15:.1f} s "
      f"-> {per_hour_15:.2f} wakes/hour")

y30, _ = steady_bins(bin_100ms_ma(longest_mc(os.path.join(OTII, "30_min_data"))))
w30 = detect_wakes(y30)
lo30, hi30 = kmeans2_1d([w[2] for w in w30])
split30 = hi30 / lo30
mid30 = (lo30 + hi30) / 2.0
up30 = [w for w in w30 if w[2] > mid30]
ka30 = [w for w in w30 if w[2] <= mid30]
up_starts = np.array([w[0] for w in up30])
spacing30 = float(np.median(np.diff(up_starts)))
per_hour_30u = 3600.0 / spacing30
ka_per_interval = []
for a, b in zip(up_starts[:-1], up_starts[1:]):
    ka_per_interval.append(sum(1 for w in ka30 if a < w[0] < b))
print(f"30-min capture: {len(up30)} uploads ({hi30:.0f} mJ cluster) + "
      f"{len(ka30)} keepalives ({lo30:.0f} mJ cluster, ratio {split30:.2f}), "
      f"median upload spacing {spacing30:.1f} s -> {per_hour_30u:.2f} uploads/hour; "
      f"keepalives per complete interval: min {min(ka_per_interval)} / "
      f"max {max(ka_per_interval)} over {len(ka_per_interval)} intervals")

# ---- consistency gate against the poster's stated counts ----
assert split15 < SPLIT_RATIO, \
    f"15-min capture shows two energy populations ({lo15:.0f}/{hi15:.0f} mJ) - FLAG"
assert split30 >= SPLIT_RATIO, \
    f"30-min capture lacks a keepalive population ({lo30:.0f}/{hi30:.0f} mJ) - FLAG"
n15 = round(per_hour_15)
assert n15 == 4, f"15-min uploads/hour {per_hour_15:.2f} != 4 - FLAG"
n30u = round(per_hour_30u)
assert n30u == 2, f"30-min uploads/hour {per_hour_30u:.2f} != 2 - FLAG"
assert min(ka_per_interval) == max(ka_per_interval) == 1, \
    f"keepalives per interval {min(ka_per_interval)}-{max(ka_per_interval)} != 1 - FLAG"
n30k = n30u * 1                       # one keepalive per upload interval
assert n15 == n30u + n30k == 4
print(f"gate passed: {n15} = {n30u} uploads + {n30k} keepalives = 4 wakes/hour")

# ---- drawing: identical style to figE_wakes_per_hour.py ----
NEUTRAL = "#16324f"
ACCENT = "#e07b00"
GREY = "#555555"

fig, ax = plt.subplots(figsize=(11, 4.0), dpi=300)
ax.set_xlim(0, 11.4)
ax.set_ylim(0, 4.0)
ax.axis("off")

BW, BH = 0.78, 0.78
XS = [2.65, 4.05, 5.45, 6.85]

def block(x, yc, color):
    ax.add_patch(FancyBboxPatch((x - BW / 2, yc - BH / 2), BW, BH,
                                boxstyle="round,pad=0.02,rounding_size=0.12",
                                facecolor=color, edgecolor="none"))

row15 = [NEUTRAL] * n15
row30 = [NEUTRAL, ACCENT] * n30u      # alternating upload / keepalive
rows = [(2.95, "15 min", row15), (1.45, "30 min", row30)]
for yc, label, colors in rows:
    ax.text(1.85, yc, label, ha="right", va="center",
            fontsize=28, fontweight="bold", color="#1a1a1a")
    for x, c in zip(XS, colors):
        block(x, yc, c)
    ax.text(7.65, yc, f"=  {len(colors)} wakes/hour", ha="left", va="center",
            fontsize=28, fontweight="bold", color="#1a1a1a")

ax.add_patch(FancyBboxPatch((1.7, 0.28), 0.40, 0.40,
                            boxstyle="round,pad=0.02,rounding_size=0.08",
                            facecolor=NEUTRAL, edgecolor="none"))
ax.text(2.25, 0.48, "upload (sensor data)", ha="left", va="center",
        fontsize=20, color=GREY)
ax.add_patch(FancyBboxPatch((5.85, 0.28), 0.40, 0.40,
                            boxstyle="round,pad=0.02,rounding_size=0.08",
                            facecolor=ACCENT, edgecolor="none"))
ax.text(6.40, 0.48, "keepalive ping (no data)", ha="left", va="center",
        fontsize=20, color=GREY)

fig.subplots_adjust(left=0.02, right=0.98, top=0.98, bottom=0.02)
out = os.path.join(FIGURES, "fig4_wakes_per_hour.png")
fig.savefig(out, dpi=300)
print("wrote", out)
