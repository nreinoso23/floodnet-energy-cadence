# Repo adaptation of the project's original fig5_duty_cycle.py (kept in
# the project records, not published here). Logic and methods unchanged;
# only data and output paths were adapted to this repository layout
# (reads data/otii, writes ../figures).
"""Poster Figure 3: radio duty-cycle square waves, computed from raw Otii data.
(Numbered Figure 5 on the original poster layout; the file name keeps fig5.)

Replaces `figB_duty_cycle_no_percent.py` (project records) under the
standing rule. The drawing code reproduces its square-wave style exactly; the
difference is that every measured pulse width and the keepalive offset are
COMPUTED HERE at runtime.

Measured inputs (derived at runtime):
  - wake envelope widths (modem PSM exit-to-enter) from recording 4's UART
    log in `data/otii/
    1_min_15_min_and_30_min_data_with_logs` (copied before opening; pairing
    and class selection per `findings.md` section 3.3 /
    Codex `phase3_log_timing.py`, both project records, implemented in
    common_otii.rec4_wake_envelopes): 1-min uploads (n=13), 15-min uploads
    (n=5), the single 30-min upload, and the single keepalive wake;
  - the keepalive's position inside the 30-minute interval from the
    30-minute long capture (`...\\30_min_data`): wake detection on 0.1-s
    means (detector from `figD_midinterval_wake.py`, project records)
    and the mean upload-start-to-keepalive-start offset.
Nominal (not measured): pulse positions at the schedule times (0/15/30/45
min), exactly as in figB_duty_cycle_no_percent.py; measured spacings differ
sub-second (its source figB_duty_cycle.py documents this).

Consistency gate: widths must round to 19.9 / 23.1 / 26.4 s and the offset
to 15.2 min, matching the current poster figure's geometry. Known accepted
deviation (project decision record): the keepalive pulse width derives to
19.7 s (the recording-4 measured envelope) where the old figure drew 19.9 s;
0.2 s is 0.006% of the hour axis and invisible at poster scale.

Regenerate:  py fig5_duty_cycle.py   (writes fig5_duty_cycle.png)
"""
import os

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from common_otii import (FIGURES, OTII, bin_100ms_ma, detect_wakes,
                         kmeans2_1d, longest_mc, rec4_wake_envelopes,
                         steady_bins)

# ---- measured inputs, computed from the raw recordings ----
env = rec4_wake_envelopes()
n1, n15 = len(env["one_min"]), len(env["fifteen_min"])
W1 = float(np.mean(env["one_min"]))
W15 = float(np.mean(env["fifteen_min"]))
W30U = float(np.mean(env["thirty_min"]))
W30K = float(np.mean(env["keepalive"]))
print(f"envelopes: 1-min {W1:.2f} s (n={n1}); 15-min {W15:.2f} s (n={n15}); "
      f"30-min upload {W30U:.2f} s (n={len(env['thirty_min'])}); "
      f"keepalive {W30K:.2f} s (n={len(env['keepalive'])})")

y30, _ = steady_bins(bin_100ms_ma(longest_mc(os.path.join(OTII, "30_min_data"))))
w30 = detect_wakes(y30)
# upload/keepalive split at the k-means cluster midpoint (same rule as fig4;
# method from poster_verify_mid_interval_wake.py, project records)
lo30, hi30 = kmeans2_1d([w[2] for w in w30])
mid30 = (lo30 + hi30) / 2.0
up_starts = np.array([w[0] for w in w30 if w[2] > mid30])
ka_starts = np.array([w[0] for w in w30 if w[2] <= mid30])
offsets = []
for a, b in zip(up_starts[:-1], up_starts[1:]):
    inside = ka_starts[(ka_starts > a) & (ka_starts < b)]
    if len(inside) == 1:
        offsets.append(float(inside[0] - a))
off_s = float(np.mean(offsets))
off_sd = float(np.std(offsets, ddof=1))
print(f"keepalive offset after upload: {off_s:.1f} +/- {off_sd:.1f} s "
      f"(n={len(offsets)}) = {off_s / 60:.2f} min")

# ---- consistency gate against the current poster figure's geometry ----
assert (n1, n15) == (13, 5), f"clean-wake counts (n1={n1}, n15={n15}) != (13, 5) - FLAG"
assert len(env["keepalive"]) == 1 and len(env["thirty_min"]) == 1, \
    f"expected single keepalive/30-min wakes, got " \
    f"{len(env['keepalive'])}/{len(env['thirty_min'])} - FLAG"
assert round(W1, 1) == 19.9, f"1-min width {W1:.2f} != 19.9 - FLAG"
assert round(W15, 1) == 23.1, f"15-min width {W15:.2f} != 23.1 - FLAG"
assert round(W30U, 1) == 26.4, f"30-min width {W30U:.2f} != 26.4 - FLAG"
assert round(W30K, 1) == 19.7, \
    f"keepalive width {W30K:.2f} != 19.7 (old figure drew 19.9; accepted deviation) - FLAG"
off_min = round(off_s / 60.0, 1)
assert off_min == 15.2, f"keepalive offset {off_min} min != 15.2 - FLAG"
print(f"gate passed: widths {W1:.1f}/{W15:.1f}/{W30U:.1f}/{W30K:.1f} s, "
      f"offset {off_min} min")

# ---- drawing: identical style to figB_duty_cycle_no_percent.py ----
NEUTRAL = "#16324f"
ACCENT = "#e07b00"
LW = 3.0
H = 1.2
SPAN = 60.0

w1, w15, w30u, w30k = W1 / 60, W15 / 60, W30U / 60, W30K / 60
off_draw = off_s / 60.0                # draw at the measured offset itself
rows = [
    ("1 min", 4.0, [(i * 1.0, w1, False) for i in range(60)]),
    ("15 min", 2.0, [(i * 15.0, w15, False) for i in range(4)]),
    ("30 min", 0.0, [(0.0, w30u, False), (off_draw, w30k, True),
                     (30.0, w30u, False), (30.0 + off_draw, w30k, True)]),
]

plt.rcParams.update({
    "axes.edgecolor": "#999999", "axes.linewidth": 0.8,
    "xtick.color": "#666666", "xtick.labelcolor": "#666666", "xtick.labelsize": 24,
})
fig, ax = plt.subplots(figsize=(11, 4.5), dpi=300)
for name, y0, pulses in rows:
    px, py = [0.0], [y0]
    for s, w, is_ka in pulses:
        if is_ka:
            px.append(s); py.append(y0)
            ax.plot(px, py, color=NEUTRAL, lw=LW, solid_joinstyle="miter")
            ax.plot([s, s, s + w, s + w], [y0, y0 + H, y0 + H, y0],
                    color=ACCENT, lw=LW, solid_joinstyle="miter")
            px, py = [s + w], [y0]
        else:
            px += [s, s, s + w, s + w]
            py += [y0, y0 + H, y0 + H, y0]
    px.append(SPAN); py.append(y0)
    ax.plot(px, py, color=NEUTRAL, lw=LW, solid_joinstyle="miter")
    ax.text(-1.8, y0 + H / 2, name, ha="right", va="center",
            fontsize=30, fontweight="bold", color="#1a1a1a")

ax.set_xlim(0, SPAN)
ax.set_ylim(-0.5, 4.0 + H + 0.4)
ax.set_xticks([0, 15, 30, 45, 60])
ax.set_xlabel("time (minutes)", fontsize=28, color="#333333")
ax.set_yticks([])
for side in ("left", "top", "right"):
    ax.spines[side].set_visible(False)
fig.subplots_adjust(left=0.21, right=0.965, top=0.97, bottom=0.21)
out = os.path.join(FIGURES, "fig5_duty_cycle.png")
fig.savefig(out, dpi=300)
print("wrote", out)
