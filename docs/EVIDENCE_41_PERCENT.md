# EVIDENCE_41_PERCENT.md: the proof chain for the poster's headline claim (2026-08-09)

> **Repository variant, adapted from the project records on 2026-08-12.** Every number,
> claim, and table below is unchanged from the original record; only file references and
> framing were adapted so this document stands alone inside the repository. Citations marked
> "project records" name documents in the project's internal analysis records (two
> independent AI-assisted verification reports and their machine-checkable artifacts); those
> records are retained by the author and are not published here, and every number they
> support is recomputed at runtime by the scripts in [`../scripts/`](../scripts/), whose
> consistency gates fail loudly if a published number stops matching the raw data.

## 1. The claim, as the poster states it

Subtitle: "15-Minute Reporting Cuts Sensor Energy Use 41% and Extends Battery Life from 49 to
84 Days". Results, first clause of its opening sentence: "Slowing reporting from 1-minute to
15-minute intervals cut average current draw by 41%, from 2.82 to 1.66 mA". Both captures ran
at the same fixed 3.60 V bench supply, so
the relative reduction in average current equals the relative reduction in average power and
energy use (Codex `poster-package.md`, claims table row 3; project records).

## 2. The raw sources: two Otii Arc recordings of FloodNet node FS5-01177

The recordings themselves live in the raw-data record, not in this repository: the raw Otii
recordings (11.6 GB) are deposited in NYU UltraViolet; the DOI link will be added here once
the record is published (deposit submitted 2026-08-09). See
[`../data/otii/README.md`](../data/otii/README.md) for the layout.
<!-- [DATA-DOI-PENDING] -->

| Recording (name as now labeled in the Otii software) | Project | Start | Duration |
|---|---|---|---|
| "2026-07-31 1-min run from boot (62.8 h)" | `1_min_data` | 2026-07-31 21:09:50 EDT (2026-08-01 01:09:50 UTC) | 62.783 h (904,080,016 samples) |
| "2026-08-04 15-min run from boot (23.4 h)" | `15_min_data` | 2026-08-04 10:21:21 EDT (2026-08-04 14:21:21 UTC) | 23.402 h (336,990,192 samples) |

The measured channel is mc (main current), headerless little-endian float32 amperes at 4,000
samples per second. The project's second working copy (project records) holds the identical
data under the recordings' original timestamp names. SHA-256 hashes of both raw files are
pinned in `poster_claim1_verification.json` (project records).

## 3. The method, in plain terms

The first hour of each capture is excluded as warm-up (boot, network attach, and settling), and
only subsequent complete capture-clock hours are kept: 61 hours for the 1-minute run, 22 for
the 15-minute run. The steady-state mean is the arithmetic mean of every current sample in that
window, accumulated in float64 over bounded slices and combined exactly. Implementations:
`phase5_steady_state_means.py` and
`poster_claim1_verify.py` (the originals; project records), and
[`../scripts/common_otii.py`](../scripts/common_otii.py) (steady_state_mean_ma, the runtime
re-implementation this repository's Figure 2 is drawn from).

## 4. The numbers and the arithmetic

- 1-minute reporting: **2.824229 mA** (61 complete steady hours)
- 15-minute reporting: **1.660821 mA** (22 complete steady hours)
- Reduction: 100 x (1 - 1.660821 / 2.824229) = **41.1938%**, rounded on the poster to **41%**

## 5. Independent reproductions of the same numbers

1. `poster_claim1_verification.json` (project records): an independent
   bounded-memmap computation recording the raw-file identities, SHA-256 hashes, window indices,
   and results 2.8242289628 / 1.6608214821 mA, reduction 41.19380885915067%.
2. `phase5_steady_state_means.py` with its outputs
   (`phase5_steady_state_summary.csv`; both project records): the same means,
   plus agreement within 0.08% with the earlier, previously unreproduced catalog values
   (2.823621 / 1.659648 mA, differences +0.022% and +0.071%; see
   `findings.md`, appendix Step 5; project records).
3. The claims-to-evidence tables: Claude `poster-package.md` section 7, rows 1, 2,
   and 4; Codex `poster-package.md`, claims table rows 1-3 (both project records).
4. `findings.md` section 4.3 (project records): the hourly energy budget built from
   independent per-wake measurements predicts the same means within 1-5%, and its measured row
   carries the same 2.824 / 1.661 mA values.
5. [`../scripts/fig2_state_of_charge.py`](../scripts/fig2_state_of_charge.py): recomputes both
   means from the raw files at
   every run and refuses to draw the poster's Figure 2 unless they still round to
   2.824 / 1.661 mA and a 41% reduction (last run 2026-08-09: derived 2.824229 / 1.660821 mA,
   gate passed).

## 6. Uncertainty, so nothing is overstated

The approximate 95% interval on the reduction, from autocorrelation-adjusted hourly variation
within the two captures, is **41.19 plus or minus 0.86 percentage points**; it does not include
between-day or network effects, which were not separately measured (the two runs are one capture
day each). Source: Codex `poster-package.md`, "Verified result" item 1, and
`poster_claim1_verification.json` (AR(1) delta-method
half-width 0.8617; both project records).
