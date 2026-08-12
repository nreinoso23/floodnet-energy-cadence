# Repo adaptation of the project's original fig2_state_of_charge.py (kept in
# the project records, not published here). Logic and methods unchanged;
# only data and output paths were adapted to this repository layout
# (reads data/otii, writes ../figures).
"""Poster Figure 2: battery state of charge vs days, computed from raw Otii data.

Replaces `figC_state_of_charge.py` (project records) under the standing
rule that every poster graph is the output of a .py file in this folder
reading datasets in this folder. The drawing code reproduces figC's visual
style exactly; the difference is that the three steady-state currents are
COMPUTED HERE from the raw mc channels at runtime instead of being pasted in
as constants.

Measured inputs (derived at runtime):
  - steady-state mean currents of the three long captures in
    `data/otii/{1,15,30}_min_data` (largest mc channel
    per project), first hour excluded, complete hours only; method from
    `phase5_steady_state_means.py` /
    `poster_claim1_verify.py` (project records) via
    common_otii.steady_state_mean_ma.
Physical constants (not measurements, kept as cited constants):
  - CAP_MAH = 3350.0: minimum standard discharge capacity, Samsung SDI
    INR18650-35E datasheet section 3.1 (v1.1; linked with its SHA-256 in the
    main README); nominal 3.60 V
    equals the bench supply (section 3.3), so no voltage correction applies.

Consistency gate: the derived currents must round to the poster's stated
2.824 / 1.661 / 1.668 mA and give 49 / 84 / 84 day labels and the 41%
reduction, or the script refuses to draw (project rule: discrepancies get
flagged, never silently changed).

Regenerate:  py fig2_state_of_charge.py   (writes fig2_state_of_charge.png)
"""
import os

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from common_otii import FIGURES, OTII, longest_mc, steady_state_mean_ma

CAP_MAH = 3350.0  # INR18650-35E datasheet 3.1, minimum standard capacity

# ---- measured inputs, computed from the raw recordings ----
derived = {}
for label, project in [("1-min", "1_min_data"), ("15-min", "15_min_data"),
                       ("30-min", "30_min_data")]:
    mc_path = longest_mc(os.path.join(OTII, project))
    mean_ma, hours = steady_state_mean_ma(mc_path)
    derived[label] = mean_ma
    print(f"{label}: steady mean {mean_ma:.6f} mA over {hours} complete hours "
          f"({os.path.relpath(mc_path, OTII)})")

# ---- consistency gate against the poster's stated numbers ----
expect = {"1-min": 2.824, "15-min": 1.661, "30-min": 1.668}
for label, want in expect.items():
    got = round(derived[label], 3)
    assert got == want, f"{label}: derived {got} mA != poster {want} mA - FLAG, do not embed"
reduction = 100.0 * (1.0 - derived["15-min"] / derived["1-min"])
assert round(reduction) == 41, f"derived reduction {reduction:.2f}% != poster 41%"
days = {k: CAP_MAH / v / 24.0 for k, v in derived.items()}
assert round(days["1-min"]) == 49 and round(days["15-min"]) == 84 \
    and round(days["30-min"]) == 84, f"day labels changed: {days}"
print(f"gate passed: {reduction:.2f}% reduction; "
      f"days {days['1-min']:.1f} / {days['15-min']:.1f} / {days['30-min']:.1f}")

# ---- drawing: identical style to figC_state_of_charge.py ----
NEUTRAL = "#16324f"
ACCENT = "#e07b00"
GREY = "#666666"

plt.rcParams.update({
    "font.size": 18, "axes.labelsize": 24,
    "xtick.labelsize": 20, "ytick.labelsize": 20,
    "axes.edgecolor": "#999999", "axes.linewidth": 0.8,
    "xtick.color": GREY, "ytick.color": GREY,
    "xtick.labelcolor": GREY, "ytick.labelcolor": GREY,
})
fig, ax = plt.subplots(figsize=(11, 4.5), dpi=300)

series = [
    (derived["1-min"], "#D55E00", "-", 2, f"1-min: {round(days['1-min']):.0f} days"),
    (derived["15-min"], "#16324f", "-", 2, f"15-min: {round(days['15-min']):.0f} days"),
    (derived["30-min"], "#E69F00", (0, (7, 5)), 3,
     f"30-min: {round(days['30-min']):.0f} days (overlaps 15-min)"),
]
for i_ma, color, ls, z, label in series:
    t_empty = CAP_MAH / i_ma / 24.0
    t = np.linspace(0, t_empty, 200)
    ax.plot(t, 100 * (1 - t / t_empty), color=color, ls=ls, lw=3.5, zorder=z,
            solid_capstyle="round", label=label)
ax.legend(loc="upper right", frameon=False, fontsize=19,
          labelcolor="#1a1a1a", handlelength=2.6)

ax.set_xlim(0, 90)
ax.set_ylim(0, 102)
ax.set_xticks([0, 15, 30, 45, 60, 75, 90])
ax.set_yticks([0, 25, 50, 75, 100])
ax.grid(color="#cccccc", lw=0.5)
ax.set_xlabel("days since full charge (no solar input)", color="#1a1a1a")
ax.set_ylabel("battery remaining (%)", color="#1a1a1a")
fig.subplots_adjust(left=0.09, right=0.985, top=0.96, bottom=0.19)
out = os.path.join(FIGURES, "fig2_state_of_charge.png")
fig.savefig(out, dpi=300)
print("wrote", out)
