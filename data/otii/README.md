# data/otii: the raw Otii Arc recordings (not stored in this repository)

The four Otii Arc projects behind Figures 2 through 5 total about 11.6 GB, and the largest
single file (the 62.8-hour capture's current channel) is about 3.6 GB, far over GitHub's
100 MB per-file limit, so the raw data lives outside this repository. The raw Otii recordings
(11.6 GB) are deposited in NYU UltraViolet; the DOI link will be added here once the record
is published (deposit submitted 2026-08-09).
<!-- [DATA-DOI-PENDING] -->

The UltraViolet record contains one zip per Otii project (named after the project folders
below), a `SHA256SUMS.txt` covering every zip, and a zip of this repository as deposited.
To reproduce the figures: download the four project zips, verify them against
`SHA256SUMS.txt`, and unzip them into this directory so the tree reads:

```
data/otii/1_min_data/
data/otii/15_min_data/
data/otii/30_min_data/
data/otii/1_min_15_min_and_30_min_data_with_logs/
```

Alternatively, point the scripts at any location by setting the environment variable
`FLOODNET_OTII_DATA` to the directory that contains those four project folders.

What the projects contain, per recording (names, start times, durations, sample counts,
mean/min/max currents, UART log presence, and classifications) is documented in
`docs/OTII_RECORDING_NAMES.md`. The file format: an Otii project stores each recording's
channels under `data/data/project/<uuid>/`; the `mc` (main current) channel is headerless
little-endian float32 amperes at 4,000 samples per second, and the mapping from channel name
to uuid lives in `data/versions/<version>/data/project.json`. The scripts in `scripts/`
resolve channels through that mapping; none of them modify the projects.
