# Repo adaptation of the project's original otii_recording_census.py (kept
# in the project records, not published here). Logic and methods unchanged;
# only data and output paths were adapted to this repository layout
# (reads data/otii; census JSON written beside the script).
"""Census of every recording in the four Otii projects, for the renaming map.

Analyzes the Otii projects under `data/otii/` (or FLOODNET_OTII_DATA). Reads project.json per project
(channel-mapping rule from `00-PROJECT-RECORD.md`, project records) and
computes, per recording: start time (UTC and America/New_York local),
channels present, and for the mc (main current, 4,000 sps) channel the
duration, sample count, and chunked mean / min / max current. UART presence =
an rx channel directory containing events.db. Everything is read-only; no
.otii3 content is modified.

Run:  py otii_recording_census.py   (writes otii_recording_census.json here)
"""
import datetime as dt
import json
import os
import shutil
import sqlite3
import tempfile
from zoneinfo import ZoneInfo

import numpy as np

from common_otii import OTII, FS, recording_channels, CHUNK


def uart_stats(rx_dir):
    """UART log stats, WAL-aware. The bare events.db can be a 4 KB
    un-checkpointed shell while the entire log lives in events.db-wal (the
    trap documented in the project records, for example
    `phase2_extract_log.py`), so the db/-wal/-shm trio is copied to a temp dir
    and the copy opened to count rows; originals are never touched.
    """
    db = os.path.join(rx_dir, "events.db")
    if not os.path.exists(db):
        return None
    out = {"db_bytes": os.path.getsize(db), "wal_bytes": 0}
    wal = db + "-wal"
    if os.path.exists(wal):
        out["wal_bytes"] = os.path.getsize(wal)
    tmp = tempfile.mkdtemp(prefix="census_db_")
    try:
        for ext in ("", "-wal", "-shm"):
            p = db + ext
            if os.path.exists(p):
                shutil.copy2(p, tmp)
        con = sqlite3.connect(os.path.join(tmp, "events.db"))
        out["event_rows"] = con.execute("select count(*) from event").fetchone()[0]
        out["nonempty_rows"] = sum(
            1 for (d,) in con.execute("select data from event")
            if bytes(d).decode("utf-8", "replace").strip())
        con.close()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return out

NY = ZoneInfo("America/New_York")
PROJECTS = ["1_min_data", "15_min_data", "30_min_data",
            "1_min_15_min_and_30_min_data_with_logs"]


def mc_stats(path):
    mc = np.memmap(path, dtype="<f4", mode="r")
    n = len(mc)
    total = 0.0
    mn, mx = np.inf, -np.inf
    for i in range(0, n, CHUNK):
        seg = np.asarray(mc[i:i + CHUNK], dtype=np.float64)
        total += float(seg.sum())
        mn = min(mn, float(seg.min()))
        mx = max(mx, float(seg.max()))
    return {"samples": n, "duration_s": n / FS, "mean_ma": total / n * 1000.0,
            "min_ma": mn * 1000.0, "max_ma": mx * 1000.0}


out = []
for proj in PROJECTS:
    pdir = os.path.join(OTII, proj)
    for idx, (rec, chans) in enumerate(recording_channels(pdir), 1):
        start_ms = rec["start_time"]
        utc = dt.datetime.fromtimestamp(start_ms / 1000, dt.timezone.utc)
        loc = utc.astimezone(NY)
        row = {
            "project": proj,
            "recording_index": idx,
            "recording_id": rec["id"],
            "start_utc": utc.isoformat(timespec="seconds"),
            "start_local_NY": loc.isoformat(timespec="seconds"),
            "channels": sorted(chans.keys()),
            "uart_log": False,
            "mc": None,
        }
        if "rx" in chans:
            ustats = uart_stats(chans["rx"])
            if ustats is not None:
                row["uart_log"] = True
                row["uart"] = ustats
        if "mc" in chans:
            p = os.path.join(chans["mc"], "samples.dat")
            if os.path.exists(p):
                print(f"{proj} rec {idx}: mc {os.path.getsize(p)/1e6:.1f} MB ...",
                      flush=True)
                row["mc"] = mc_stats(p)
        out.append(row)

dest = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                    "otii_recording_census.json")
with open(dest, "w", encoding="utf-8") as f:
    json.dump(out, f, indent=1)
print("wrote", dest)
for r in out:
    mc = r["mc"] or {}
    dur = mc.get("duration_s", 0)
    print(f"{r['project']:42s} rec{r['recording_index']} "
          f"{r['start_local_NY']} dur={dur/3600:8.3f}h "
          f"mean={mc.get('mean_ma', float('nan')):9.4f}mA "
          f"min={mc.get('min_ma', float('nan')):8.4f} "
          f"max={mc.get('max_ma', float('nan')):9.3f} "
          f"uart={r['uart_log']} ch={','.join(r['channels'])}")
