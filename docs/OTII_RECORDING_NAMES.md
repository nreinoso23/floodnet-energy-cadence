# OTII_RECORDING_NAMES.md: proposed names for every recording (2026-08-09)

> **Repository variant, adapted from the project records on 2026-08-12.** Numbers, claims,
> and tables below are unchanged from the original record; only file references and framing
> were adapted so this document stands alone inside the repository. Citations marked "project
> records" name the project's internal working documents, retained by the author and not
> published here; "the Codex report" and "the Claude report" (together "both reports") name
> the two independent AI-assisted verification reports in those records. The four renamed
> projects themselves are in the raw-data record: the raw
> Otii recordings (11.6 GB) are deposited in NYU UltraViolet; the DOI link will be added here
> once the record is published (deposit submitted 2026-08-09).
> <!-- [DATA-DOI-PENDING] -->

> **Verification, final (2026-08-09): 14 of 14 correct.** The one variance from the first pass
> (a leading tab on the combined project's first calibration name) was fixed and re-verified:
> that name now reads exactly "2026-08-05 cal, leads open" with no leading or trailing
> whitespace. The 46-minute recording's canonical name is now **"2026-08-05 1-min run with
> UART, remote-cmd test (46 min)"** (the refined name reflecting its resolved identity),
> verified as applied in the Otii software. The project's second working copy (the Codex copy;
> project records) keeps the
> default timestamp names **by deliberate decision**, not oversight; the divergence between the
> two copies is intentional. See the "Rename verification" section at the end for the verdict
> tables, the data integrity confirmation, and the 46-minute recording's resolved identity. The
> original proposal tables below are kept unchanged for the record.

Copy-paste renaming map for the recordings inside the four `.otii3` projects. Analyzed from the
working copy now deposited as the raw-data record (the project's second copy is identical per
the project folder map; project records); nothing in the projects was modified. Analysis script:
[`../scripts/otii_recording_census.py`](../scripts/otii_recording_census.py) (channel mapping
per the reproduction notes in
`00-PROJECT-RECORD.md`, project records; the recording-4 UART database was copied to a temp
folder before opening). Full numbers:
[`../scripts/otii_recording_census.json`](../scripts/otii_recording_census.json).

How to read the tables: recordings carry no name field in the project data, so the Otii software
shows each one by its start timestamp; the "Current name (start, local)" column gives that
timestamp in America/New_York local time (UTC in parentheses) so you can match rows in the UI.
All mc (main current) channels are 4,000 samples per second. "UART" = an rx log channel is
attached to the recording; content is judged by opening a temp copy of the db together with its
write-ahead log (WAL) and counting rows, never by file size alone: an un-checkpointed events.db
can be a 4 KB shell while the entire log sits in events.db-wal (the WAL trap the project
records warn about, and exactly the case for the 46-minute recording below).

Classification bands, from the signal itself:
- **cal, leads open**: mean current at the instrument noise floor, about 0.6 to 1.2 uA, no
  transients (leads connected to nothing).
- **cal, sensor off**: a steady 6 to 9 uA leakage draw (leads on the sensor, sensor powered off).
- **live run**: 1.6 to 2.9 mA mean with boot transient and the per-minute sensing pattern; peaks
  above 100 mA during transmit.

## Project `1_min_data` (folder 2026-07-31_04_fs5-01177_3v60_boot)

| # | Current name (start, local) | Duration | Samples | Mean / min / max (mA) | UART | Proposed name | Classification and one-line evidence |
|---|---|---|---|---|---|---|---|
| 1 | 2026-07-31 21:05:22 (2026-08-01 01:05 UTC) | 15.4 s | 61,528 | 0.0060 / -0.323 / 5.13 | no | 2026-07-31 cal, sensor off | Sensor-off: ~7.5 uA steady leakage plateau (whole-capture mean 6.0 uA including an open-floor prefix; not the ~0.6 uA open-lead floor), with one brief ~5 mA transient; too short and too small to be a run. |
| 2 | 2026-07-31 21:09:50 (2026-08-01 01:09 UTC) | 62.783 h | 904,080,016 | 2.8299 / -4.70 / 153.08 | no | 2026-07-31 1-min run from boot (62.8 h) | Live run: 2.83 mA whole-capture mean (2.824 mA steady state), transmit peaks >150 mA; this is the 1-minute experiment behind the poster's 2.824 mA. |

## Project `15_min_data` (folder 2026-08-04_06_fs5-01177_3v60_sync15)

| # | Current name (start, local) | Duration | Samples | Mean / min / max (mA) | UART | Proposed name | Classification and one-line evidence |
|---|---|---|---|---|---|---|---|
| 1 | 2026-08-04 10:09:14 (14:09 UTC) | 20.7 s | 82,824 | 0.0012 / 0.0004 / 0.002 | no | 2026-08-04 cal, leads open | Open leads: ~1.2 uA floor, no transients. Note: about 2x the ~0.6 uA floor of the other open-lead checks; this is the "anomalously high 15-minute pre-zero" the Codex report flags. |
| 2 | 2026-08-04 10:18:02 (14:18 UTC) | 20.8 s | 83,360 | 0.0085 / 0.0077 / 0.009 | no | 2026-08-04 cal, sensor off | Sensor-off: steady 8.5 uA leakage, no transients. |
| 3 | 2026-08-04 10:21:21 (14:21 UTC) | 23.402 h | 336,990,192 | 1.6675 / -2.09 / 158.12 | no | 2026-08-04 15-min run from boot (23.4 h) | Live run: the 15-minute experiment (1.661 mA steady state; 88 uploads at 899 s median spacing in the steady window). |
| 4 | 2026-08-05 09:46:10 (13:46 UTC) | 30.9 s | 123,548 | 0.0006 / -0.0002 / 0.001 | no | 2026-08-05 cal, leads open (post-run) | Open leads: 0.6 uA floor, taken the morning after the run ended. |

## Project `30_min_data` (folder 2026-08-03_05_fs5-01177_3v60_sync30)

| # | Current name (start, local) | Duration | Samples | Mean / min / max (mA) | UART | Proposed name | Classification and one-line evidence |
|---|---|---|---|---|---|---|---|
| 1 | 2026-08-03 16:54:51 (20:54 UTC) | 30.5 s | 122,180 | 0.0006 / -0.0001 / 0.001 | no | 2026-08-03 cal, leads open | Open leads: 0.6 uA floor, no transients. |
| 2 | 2026-08-03 17:12:08 (21:12 UTC) | 22.1 s | 88,436 | 0.0075 / -0.323 / 4.47 | no | 2026-08-03 cal, sensor off | Sensor-off: steady ~7.5 uA leakage with one brief ~4.5 mA transient. |
| 3 | 2026-08-03 17:18:58 (21:18 UTC) | 16.364 h | 235,645,388 | 1.6890 / -2.90 / 128.71 | no | 2026-08-03 30-min run from boot (16.4 h) | Live run: the 30-minute experiment (1.668 mA steady state; 30 uploads + 30 mid-interval keepalive wakes in the steady window). |
| 4 | 2026-08-04 09:52:49 (13:52 UTC) | 32.6 s | 130,356 | 0.0006 / -0.0001 / 0.001 | no | 2026-08-04 cal, leads open (post-run) | Open leads: 0.6 uA floor, taken the morning after the run ended. |

## Project `1_min_15_min_and_30_min_data_with_logs` (folder 2026-08-05_07_fs5-01177_3v60_sync1_uart)

| # | Current name (start, local) | Duration | Samples | Mean / min / max (mA) | UART | Proposed name | Classification and one-line evidence |
|---|---|---|---|---|---|---|---|
| 1 | 2026-08-05 11:31:56 (15:31 UTC) | 31.2 s | 124,784 | 0.0007 / -0.0001 / 0.001 | no | 2026-08-05 cal, leads open | Open leads: 0.7 uA floor, no transients. |
| 2 | 2026-08-05 11:33:14 (15:33 UTC) | 20.7 s | 82,908 | 0.0077 / 0.0064 / 0.009 | yes (0 rows) | 2026-08-05 cal, sensor off, UART armed | Sensor-off: steady 7.7 uA leakage; an rx log channel is attached but a db+WAL replay contains zero event rows (genuinely empty). |
| 3 | 2026-08-05 12:06:25 (16:06 UTC) | 46.4 min | 11,134,184 | 2.7394 / -1.65 / 154.32 | yes (6,473 rows, all in the WAL) | 2026-08-05 1-min run with UART (46 min) | Live run at 1-minute cadence: 31 radio wakes at 60.5 s median spacing, ~0.38 J median upload energy, 1.29 mA floor. Its UART log is complete but hidden: the events.db is a 4 KB un-checkpointed shell whose 3.9 MB WAL holds 6,473 rows (3,523 non-empty lines, boot banner through 2,759 s). This is the "unexplained 46-minute UART recording" the Codex report mentions; the recovered log likely explains it and is worth reading (see "The 46-minute recording, resolved" at the end of this file). |
| 4 | 2026-08-05 13:01:36 (17:01 UTC) | 2.381 h | 34,292,280 | 1.8110 / -2.26 / 160.68 | yes (4,963 rows; 308 KB db + 4.1 MB WAL) | 2026-08-05 1+15+30-min run with UART (2.4 h) | Live run covering all three schedules in one session (segments at 1, 15, then 30 minutes; remote schedule changes visible in the log); the full 4,963-row UART log that anchors the wake-anatomy analysis ("recording 4" in both reports; the db alone holds 4,936 rows, the last six minutes live in the WAL). |

Nothing resisted classification: every recording falls cleanly into one of the three bands. Three
caveats worth knowing when you rename: the 15_min_data open-lead check (rec 1) reads ~2x the
usual noise floor (see its evidence note); the two brief milliampere transients inside the
sensor-off checks (1_min rec 1, 30_min rec 2) look like momentary lead contact or a power blip,
not sensor activity, and both are 15-30 s calibration recordings either way; and the 46-minute
recording's full UART log was recovered from its WAL during this analysis (it had looked empty
by db size alone), so treat that recording as documented, not mysterious.

## Rename verification (2026-08-09)

Verified against fresh reads of the renamed projects (the working copy now deposited as the
raw-data record). Where
names live: each project's current version folder stores an `attributes.db` (SQLite) whose
`value` table holds a `recording.name` row per recording id; the Otii software's default name is
the recording's local start timestamp stored the same way. Names were read from temp copies;
matching to the proposal tables used start timestamp and sample count, never the name itself.

### Verdict tables

**Project `1_min_data`**

| Recording (start, local) | Proposed name | Actual name | Verdict |
|---|---|---|---|
| 2026-07-31 21:05:22 | 2026-07-31 cal, sensor off | 2026-07-31 cal, sensor off | exact match |
| 2026-07-31 21:09:50 | 2026-07-31 1-min run from boot (62.8 h) | 2026-07-31 1-min run from boot (62.8 h) | exact match |

**Project `15_min_data`**

| Recording (start, local) | Proposed name | Actual name | Verdict |
|---|---|---|---|
| 2026-08-04 10:09:14 | 2026-08-04 cal, leads open | 2026-08-04 cal, leads open | exact match |
| 2026-08-04 10:18:02 | 2026-08-04 cal, sensor off | 2026-08-04 cal, sensor off | exact match |
| 2026-08-04 10:21:21 | 2026-08-04 15-min run from boot (23.4 h) | 2026-08-04 15-min run from boot (23.4 h) | exact match |
| 2026-08-05 09:46:10 | 2026-08-05 cal, leads open (post-run) | 2026-08-05 cal, leads open (post-run) | exact match |

**Project `30_min_data`**

| Recording (start, local) | Proposed name | Actual name | Verdict |
|---|---|---|---|
| 2026-08-03 16:54:51 | 2026-08-03 cal, leads open | 2026-08-03 cal, leads open | exact match |
| 2026-08-03 17:12:08 | 2026-08-03 cal, sensor off | 2026-08-03 cal, sensor off | exact match |
| 2026-08-03 17:18:58 | 2026-08-03 30-min run from boot (16.4 h) | 2026-08-03 30-min run from boot (16.4 h) | exact match |
| 2026-08-04 09:52:49 | 2026-08-04 cal, leads open (post-run) | 2026-08-04 cal, leads open (post-run) | exact match |

**Project `1_min_15_min_and_30_min_data_with_logs`**

| Recording (start, local) | Proposed name | Actual name | Verdict |
|---|---|---|---|
| 2026-08-05 11:31:56 | 2026-08-05 cal, leads open | [TAB]2026-08-05 cal, leads open | minor variance: a leading tab character precedes the name (paste artifact); suggested correction: edit the name and delete the leading whitespace. SUPERSEDED: fixed and re-verified exact on 2026-08-09 (header note) |
| 2026-08-05 11:33:14 | 2026-08-05 cal, sensor off, UART armed | 2026-08-05 cal, sensor off, UART armed | exact match |
| 2026-08-05 12:06:25 | 2026-08-05 1-min run with UART (46 min) | 2026-08-05 1-min run with UART (46 min) | exact match. SUPERSEDED: renamed to the canonical "2026-08-05 1-min run with UART, remote-cmd test (46 min)" and re-verified on 2026-08-09 (header note) |
| 2026-08-05 13:01:36 | 2026-08-05 1+15+30-min run with UART (2.4 h) | 2026-08-05 1+15+30-min run with UART (2.4 h) | exact match |

### Data integrity after the renames

Recording counts, sample counts, and durations all match the round-4 census
([`../scripts/otii_recording_census.json`](../scripts/otii_recording_census.json)); the newest
`samples.dat` write time in any
project is 2026-08-05, so no measurement data changed. The three UART database trios are
byte-count-identical to round 4 (no WAL was checkpointed by the renames; the 46-minute
recording's log still lives entirely in its WAL). The changes are the expected rename-session
artifacts: new project version folders holding the updated `attributes.db` name rows, project
meta/session bookkeeping files, and rewritten `events.db-shm` files (transient SQLite
shared-memory indexes rebuilt whenever the database is opened; they hold no log content, and
the paired db and WAL files kept their 2026-08-05 timestamps and exact byte counts).

### Figure pipeline immunity

No script in [`../scripts/`](../scripts/) selects recordings by name. One selection was
positional
(the recording-4 UART source took the last rx-bearing recording) and was rekeyed to a data-based
rule (largest mc channel among rx-bearing recordings, with the 4,963-row assert as backstop).
The full pipeline was re-run against the renamed projects: every consistency gate passed with
identical values (means 2.824229 / 1.660821 / 1.668187 mA; envelopes 19.9 / 23.1 / 26.4 /
19.7 s; offset 15.2 min; 88 wakes at 4.00/hour; 30 + 30 with one keepalive per interval), and
all three regenerated PNGs are byte-identical to the versions embedded in the poster.

### The Codex copy

The project's second working copy (the Codex copy; project records, not published) is
untouched (newest file 2026-08-05): its recordings still
carry the Otii default timestamp names. Its recording ids and start timestamps are identical to
the Claude copy in every project, so the proposal tables above apply to it unchanged if you
choose to repeat the renames there. One quirk to expect: the Otii default name can differ from
the project metadata's start time by one second (e.g. default name "2026-08-05 12:06:24" for the
recording whose metadata start is 12:06:25.000); match rows by the table timestamps, which come
from the metadata.

### The 46-minute recording, resolved (was "unexplained" in the Codex report)

Its full UART log was recovered read-only from a temp copy of its database plus 3.9 MB WAL
(6,473 rows, 3,523 non-empty lines, 3.25 s to 2,758.8 s; dump: `rec3_uart_dump.txt`, project
records). The log shows a complete, healthy session: normal
boot (MCUboot, image v0.1.99), Azure provisioning and RTC sync, MQTT connect to
floodnet-iot-hub.azure-devices.net, steady 1-minute reporting (33 modem wake cycles, 45 records
sent, 45 acknowledged), one remote devicebound command test at t = 936 s (SET then GET
`DATA_SYNC_FREQ_MINUTES`, both answered "1" and persisted to the config files, the same command
path recording 4 later used for its live schedule changes; the modem side also prints cosmetic
"Invalid CELL command" lines for these payloads before forwarding them, exactly as it does in
recording 4), and a clean stop mid-cycle at 46 minutes. In context (it ended nine
minutes before recording 4 began), it reads as a successful dress rehearsal of the recording-4
procedure: UART capture and the remote-command path both proven before the real three-schedule
session. The applied name stays accurate; if you want the distinguishing event in the name, an
optional refinement is "2026-08-05 1-min run with UART, remote-cmd test (46 min)".
