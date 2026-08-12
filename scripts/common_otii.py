# Repo adaptation of the project's original common_otii.py (kept in the
# project records, not published here). Logic and methods unchanged;
# only data and output paths were adapted to this repository layout
# (data root now data/otii or FLOODNET_OTII_DATA; FIGURES output constant added).
"""Shared Otii-data access and analysis methods for the poster figure scripts.

Every method here is reused from an existing analysis script in this project,
cited per function. Nothing is invented: the steady-state rule, the wake
detector, and the UART pairing all reproduce the published definitions.
Citations marked "project records" name documents in the project's internal
analysis records (two independent AI-assisted verification reports and their
artifacts); those records are not published in this repository, and every
number they support is recomputed here at runtime.

Raw data source: the `data/otii/` directory of this repository (the four Otii
Arc projects; see the README for how to obtain them), or any directory set in
the FLOODNET_OTII_DATA environment variable. All reads are read-only; SQLite
logs are copied to a temp directory before opening so the original
database/WAL pair is never touched.
"""
import json
import math
import os
import shutil
import sqlite3
import tempfile

import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OTII = os.environ.get("FLOODNET_OTII_DATA",
                      os.path.join(REPO, "data", "otii"))
FIGURES = os.path.join(REPO, "figures")
FS = 4000          # mc channel sample rate, Hz (verified in every project.json)
CHUNK = 1_000_000  # bounded reduction slices, per poster_claim1_verify.py


def project_json(project_dir):
    """Locate and load the single project.json of an .otii3 project folder.

    Channel-mapping rule from `00-PROJECT-RECORD.md` (project records)
    ("How to reproduce"): iterate recordings[].measurements[], select by
    measurement.source.name, take data.id as the directory name under
    data/data/project/.
    """
    versions = os.path.join(project_dir, "data", "versions")
    for uuid in os.listdir(versions):
        cand = os.path.join(versions, uuid, "data", "project.json")
        if os.path.exists(cand):
            with open(cand, encoding="utf-8") as f:
                return json.load(f)
    raise FileNotFoundError(f"no project.json under {versions}")


def recording_channels(project_dir):
    """Yield (recording, {channel_name: samples_path_or_db_dir}) per recording.

    Guards the sample-rate assumption: any mc channel whose declared
    measurement.source.sample_rate differs from FS aborts loudly (the source
    method, `poster_claim1_verify.py`, reads the rate from this metadata).
    """
    pj = project_json(project_dir)
    for rec in pj.get("recordings", []):
        chans = {}
        for m in rec.get("measurements", []):
            src = m.get("measurement", {}).get("source", {})
            name = src.get("name")
            data_id = m.get("data", {}).get("id")
            if name == "mc":
                rate = src.get("sample_rate")
                assert rate == FS, f"mc sample rate {rate} != {FS} in {project_dir}"
            if name and data_id:
                chans[name] = os.path.join(project_dir, "data", "data",
                                           "project", data_id)
        yield rec, chans


def longest_mc(project_dir):
    """Path to the largest mc samples.dat in a project.

    Selection rule from `poster_claim1_verify.py` (project records; "longest
    recording whose measurement.source.name is mc").
    """
    best = None
    for _rec, chans in recording_channels(project_dir):
        if "mc" in chans:
            p = os.path.join(chans["mc"], "samples.dat")
            if os.path.exists(p):
                sz = os.path.getsize(p)
                if best is None or sz > best[0]:
                    best = (sz, p)
    return best[1]


def steady_state_mean_ma(samples_path):
    """Steady-state mean current in mA: exclude the first hour, keep only
    subsequent complete hours, chunked float64 sums combined with math.fsum.

    Method reproduced from `phase5_steady_state_means.py` (lines 149-171,
    217-274 per its project record) and `poster_claim1_verify.py`; identical
    rule in `findings.md` appendix Step 5 (all project records).
    """
    mc = np.memmap(samples_path, dtype="<f4", mode="r")
    per_hour = 3600 * FS
    total_hours = len(mc) // per_hour
    start = per_hour                     # exclude hour 0
    stop = total_hours * per_hour        # complete hours only
    if stop <= start:
        raise ValueError("capture shorter than two hours")
    sums = []
    for i in range(start, stop, CHUNK):
        seg = np.asarray(mc[i:min(i + CHUNK, stop)], dtype=np.float64)
        assert np.all(np.isfinite(seg)), f"non-finite sample near index {i}"
        sums.append(float(seg.sum()))
    mean_a = math.fsum(sums) / (stop - start)
    return mean_a * 1000.0, total_hours - 1


def bin_100ms_ma(samples_path):
    """Whole-capture 0.1-s mean current in mA (memmap, chunked).

    Binning per `figD_midinterval_wake.py` (project records; 0.1-s means
    of the mc channel), extended over the full capture in bounded chunks.
    """
    mc = np.memmap(samples_path, dtype="<f4", mode="r")
    k = FS // 10
    n = len(mc) // k
    out = np.empty(n, dtype=np.float64)
    bins_per_chunk = 25_000                      # 1e7 samples per read
    for b0 in range(0, n, bins_per_chunk):
        b1 = min(b0 + bins_per_chunk, n)
        seg = np.asarray(mc[b0 * k:b1 * k], dtype=np.float64)
        out[b0:b1] = seg.reshape(b1 - b0, k).mean(axis=1)
    return out * 1000.0                          # mA


def detect_wakes(y_ma, bin_s=0.1):
    """Radio-wake detector on 0.1-s means: threshold = median + 2 mA, gaps
    < 5 s merged, wakes >= 5 s kept. Returns [(t_start, t_end, energy_mJ)].

    Detector reproduced from `figD_midinterval_wake.py` (project records;
    its docstring calls it a self-contained implementation of the census
    detector in `00-PROJECT-RECORD.md` section 4); energy classification at
    3.60 V follows the same script (mJ above the median floor). One
    convention difference: wake end is reported at the last bin's right edge
    where figD reports the bin center (a half-bin, 0.05 s); counts, starts,
    and energies are unaffected.
    """
    med = float(np.median(y_ma))
    idx = np.where(y_ma > med + 2.0)[0]
    wakes = []
    if len(idx):
        gap_bins = int(5.0 / bin_s)
        start = prev = idx[0]
        for j in idx[1:]:
            if j - prev > gap_bins:
                wakes.append((start, prev))
                start = j
            prev = j
        wakes.append((start, prev))
    out = []
    for a, b in wakes:
        if (b - a) * bin_s >= 5.0:
            e_mj = float(np.sum(y_ma[a:b + 1] - med)) * bin_s * 3.6  # 3.60 V
            out.append((a * bin_s, (b + 1) * bin_s, e_mj))
    return out


KEEPALIVE_MAX_MJ = 700.0  # upload ~1350 mJ vs keepalive ~250 mJ split,
                          # boundary per figD_midinterval_wake.py (e <= 700)


def kmeans2_1d(values, iters=100):
    """Deterministic two-cluster 1-D k-means (init at min and max), the
    energy-classification method of `poster_verify_mid_interval_wake.py`
    (project records; "deterministic one-dimensional
    k-means on gross 3.60 V event energy"). Returns (lo_center, hi_center).
    """
    v = np.asarray(sorted(values), dtype=np.float64)
    lo, hi = float(v[0]), float(v[-1])
    for _ in range(iters):
        mid = (lo + hi) / 2.0
        lo_new = float(v[v <= mid].mean())
        hi_new = float(v[v > mid].mean())
        if lo_new == lo and hi_new == hi:
            break
        lo, hi = lo_new, hi_new
    return lo, hi


def steady_bins(y_ma, bin_s=0.1):
    """Restrict a binned capture to its steady window: exclude the first hour,
    keep only subsequent complete hours. Same window rule as
    steady_state_mean_ma (from `poster_claim1_verify.py`), and the window both
    censuses used (Claude 00-PROJECT-RECORD.md section 4; Codex
    poster-claim3-verification.json: 15 steady hours of the 30-min capture).
    Returns (sliced_array, offset_seconds_of_slice_start).
    """
    per_hour = int(3600 / bin_s)
    n_complete = (len(y_ma) - per_hour) // per_hour
    if n_complete < 1:
        raise ValueError("capture shorter than two hours")
    return y_ma[per_hour:per_hour + n_complete * per_hour], per_hour * bin_s


def rec4_uart_rows():
    """All (t_seconds, text) rows of recording 4's UART log.

    The events.db / -wal / -shm trio is copied to a temp dir first so the
    read-only original is never opened (the .db alone silently loses the last
    six minutes; warning documented in the project records, for example
    `phase2_extract_log.py`). Schema: event(id, time,
    data); time is microseconds from recording start; data is a BLOB.
    """
    # Recording 4 is selected by DATA, not by list position or name (recording
    # names are user-editable in the Otii software): among recordings that
    # carry an rx log channel, take the one with the largest mc channel (the
    # 2.38 h controlled capture; the other rx-bearing recordings are a 21 s
    # calibration and the 46-minute rehearsal run). The 4,963-row assert below
    # remains the backstop.
    src_dir = None
    best_mc = -1
    proj = os.path.join(OTII, "1_min_15_min_and_30_min_data_with_logs")
    for _rec, chans in recording_channels(proj):
        if "rx" in chans and os.path.exists(os.path.join(chans["rx"], "events.db")) \
                and "mc" in chans:
            mc_sz = os.path.getsize(os.path.join(chans["mc"], "samples.dat"))
            if mc_sz > best_mc:
                best_mc = mc_sz
                src_dir = chans["rx"]
    if src_dir is None:
        raise FileNotFoundError("recording-4 rx events.db not found")
    tmp = tempfile.mkdtemp(prefix="rec4db_")
    try:
        for ext in ("", "-wal", "-shm"):
            p = os.path.join(src_dir, "events.db" + ext)
            if os.path.exists(p):
                shutil.copy2(p, tmp)
        con = sqlite3.connect(os.path.join(tmp, "events.db"))
        rows = [(t / 1e6, bytes(d).decode("utf-8", "replace").strip())
                for t, d in con.execute("select time, data from event")]
        con.close()
        assert len(rows) == 4963, f"expected 4,963 UART rows, got {len(rows)}"
        return rows
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def rec4_wake_envelopes():
    """Classified PSM exit-to-enter envelopes from recording 4's UART log.

    Pairing and class definitions reproduce `findings.md` section 3.3
    (log-based wake windows; Codex equivalent: `phase3_log_timing.py`; both
    project records), with objective selection:
      - 1-min wakes: next exit-to-exit spacing 55-65 s (n=13);
      - 15-min wakes: previous spacing > 800 s (not part of the 60-s train,
        which excludes the schedule-transition wake at ~809 s), next spacing
        890-910 s, and no MQTT disconnect line inside the window (n=5; the
        wake containing the 6,211.99 s broker disconnect is excluded, as both
        findings.md files do);
      - keepalive: a wake containing no MQTT send lines (n=1);
      - 30-min upload: the final send-carrying wake (n=1).
    Returns dict with lists of durations (s) per class.
    """
    rows = rec4_uart_rows()
    exits = [t for t, x in rows if x.startswith("Modem sleep exit")]
    enters = [t for t, x in rows if x.startswith("Modem sleep enter")]
    sends = [t for t, x in rows if "MQTT send command" in x or "CMD_CELL_MQTT_SEND" in x]
    disconnects = [t for t, x in rows if "disconnected" in x.lower()]
    wakes = []
    for ex in exits:
        after = [en for en in enters if en > ex]
        if after:
            wakes.append((ex, min(after)))
    out = {"one_min": [], "fifteen_min": [], "keepalive": [], "thirty_min": []}
    for i, (ex, en) in enumerate(wakes):
        prv = ex - wakes[i - 1][0] if i > 0 else None
        nxt = wakes[i + 1][0] - ex if i + 1 < len(wakes) else None
        has_send = any(ex <= t <= en for t in sends)
        has_disc = any(ex <= t <= en for t in disconnects)
        if nxt is not None and 55 <= nxt <= 65:
            out["one_min"].append(en - ex)
        elif not has_send:
            out["keepalive"].append(en - ex)
        elif (prv is not None and prv > 800 and nxt is not None
              and 890 <= nxt <= 910 and not has_disc):
            out["fifteen_min"].append(en - ex)
        elif nxt is None:
            out["thirty_min"].append(en - ex)
    return out
