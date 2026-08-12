# Repo adaptation of the project's original figA_report_cycles.py (kept in
# the project records, not published here). Logic and methods unchanged;
# only data and output paths were adapted to this repository layout
# (reads data/otii (channel path unchanged), writes ../figures/fig3_report_cycles.png).
"""Poster Figure 3 - one measured report cycle at each schedule.
Source: Otii recording 4 (project '1_min_15_min_and_30_min_data_with_logs'),
main-current channel samples.dat (UUID 7d0169a0-729c-4657-bc25-5a6509cddbfc),
4000 sps float32 amperes, 10-ms plotting bins.
Cycle windows (seconds into the recording, from the serial-log event times):
  1-min 385.0-446.5 | 15-min 2612.0-3516.0 | 30-min 6209.0-8043.0.
The 30-min panel's single in-plot marker sits at the mid-interval keepalive
wake (log time 7122.2 s). All explanation lives in the numbered caption in
`poster-package.md` (project records) - nothing but data, axes and that one
marker in the frame.
Duty-cycle figures in the titles: 60x19.9 s = 1194 s/h (33.2%); 4x23.1 s =
92.4 s/h (2.57%); 2x26.4 + 2x19.9 s = 92.2 s/h (2.56%).
Regenerate:  py fig3_report_cycles.py   (writes ../figures/fig3_report_cycles.png)
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import os
from common_otii import FIGURES, OTII, FS
MC = os.path.join(OTII, "1_min_15_min_and_30_min_data_with_logs", "data",
                  "data", "project",
                  "7d0169a0-729c-4657-bc25-5a6509cddbfc", "samples.dat")
assert os.path.exists(MC), (
    "raw Otii data not found - place the projects under data/otii/ or set "
    "FLOODNET_OTII_DATA (see data/otii/README.md)")
assert os.path.getsize(MC) == 137169120, (
    f"recording-4 mc channel size {os.path.getsize(MC)} != 137,169,120 bytes "
    "- wrong or modified data - FLAG")
mc = np.memmap(MC, dtype="<f4", mode="r")

def window(t0, t1, bin_ms=10):
    i0, i1 = int(t0 * FS), int(t1 * FS)
    seg = np.asarray(mc[i0:i1], dtype=np.float32)
    k = int(bin_ms * FS / 1000)
    n = len(seg) // k
    y = seg[: n * k].reshape(n, k).mean(axis=1) * 1000.0  # mA
    t = (np.arange(n) + 0.5) * (k / FS) / 60.0            # minutes from t0
    return t, y

TRACE = "#16324f"   # dark navy - darkest element in the frame
ACCENT = "#e07b00"  # single accent, used once (keepalive marker)
GREY = "#666666"
plt.rcParams.update({
    "font.size": 16, "axes.labelsize": 20,
    "xtick.labelsize": 16, "ytick.labelsize": 16,
    "axes.edgecolor": "#999999", "axes.linewidth": 0.8,
    "xtick.color": GREY, "ytick.color": GREY,
    "xtick.labelcolor": GREY, "ytick.labelcolor": GREY,
})

fig, axes = plt.subplots(3, 1, figsize=(8, 5.4), dpi=300)
panels = [
    (385.0, 446.5, "1-minute reporting"),
    (2612.0, 3516.0, "15-minute reporting"),
    (6209.0, 8043.0, "30-minute reporting"),
]
for ax, (t0, t1, title) in zip(axes, panels):
    t, y = window(t0, t1)
    ax.plot(t, y, lw=0.6, color=TRACE)
    ax.set_yscale("log")
    ax.set_ylim(0.8, 400)
    ax.set_yticks([1, 10, 100])
    ax.set_yticklabels(["1", "10", "100"])
    ax.set_xlim(0, (t1 - t0) / 60.0)
    ax.set_title(title, loc="center", fontweight="bold", fontsize=17,
                 color="#1a1a1a", pad=4)
    ax.grid(True, which="major", axis="y", color="#cccccc", lw=0.5)

# the one permitted in-plot marker: the mid-interval keepalive wake (t=7122.2 s)
axes[2].plot([(7122.2 - 6209.0) / 60.0], [140], "v", ms=11, color=ACCENT,
             markeredgecolor="none", clip_on=False)

axes[2].set_xlabel("minutes into cycle", fontsize=20, color="#1a1a1a")
fig.text(0.008, 0.5, "current (mA, log scale)", va="center",
         rotation="vertical", fontsize=20, color="#1a1a1a")
fig.subplots_adjust(left=0.115, right=0.985, top=0.935, bottom=0.115, hspace=0.75)
out = os.path.join(FIGURES, "fig3_report_cycles.png")
fig.savefig(out, dpi=300)
print("wrote", out)
