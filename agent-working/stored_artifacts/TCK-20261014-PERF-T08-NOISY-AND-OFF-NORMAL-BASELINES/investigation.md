---
status: historical
layer: performance
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261014-PERF-T08-NOISY-AND-OFF-NORMAL-BASELINES
date: 2026-10-15
tags: [performance, benchmarking]
---

# Investigation: TCK-20261014-PERF-T08-NOISY-AND-OFF-NORMAL-BASELINES

AC1, the noise diagnosis. **Nothing was re-measured.** Source: the per-tick `tick_compute_ms` T08 kept (inline in `reports/perf/t08/<name>/run{1,2,3}.json`; the corpus records point at `reports/perf/samples/*.json` by `samples.uri`), plus the `t08_retry/` window for the two retry-promoted records. Analysis script: `an2_reproduce_ac1.py` in this folder (the reproduction script for AC1; it moves to stored_artifacts at close, it is not a `tools/perf/` tool; header says what it reads and that python3 3.13 ran it).

## What the protocol already rules out
- **GC:** every record has `protocol.gc_disabled: true`. A GC pause cannot be the outlier source; `gc.callbacks` instrumentation is unnecessary for these runs.
- **Warm-up:** 10 warm-up ticks (100 for the corpus) are dropped before sampling. Residual first-tick effect appears only in `movement_100_local` run 1 (ticks 233, 154 ms, then 110-137).

## Host state at measurement (from `summary.json`)
- Swap used was **5.7 to 6.8 GB on a 9.9 GB VM in every window** (including the clean retry window, 6.57 GB), so swap alone does not separate noisy from quiet windows.
- 1-min loadavg: local records 2.2 to 2.7; concurrent first window 4.8 to 5.7 (several sessions running); retry window 1.1 to 1.2; corpus 0.62, 1.49, 2.32. **The ticket's "load 0.6-1.3" holds for the corpus record's first run only, not the three local ones.** That weakens "intrinsic to the run": the three local records were measured at load >2.

## Per record (per-run: avg / min / median / p95 / max ms)

| Record | Run 1 | Run 2 | Run 3 | Spread |
|---|---|---|---|---|
| `idle_100_local` (50 ticks) | 62.4 / 49.4 / 63.2 / 71.9 / 74.0 | 61.0 / 49.3 / 61.0 / 70.4 / 72.2 | 46.1 / 31.1 / 44.7 / 60.7 / 67.1 | 35.3 % |
| `movement_100_local` (50) | 126.6 / 92.7 / 125.6 / 154.1 / 232.6 | 108.6 / 62.6 / 108.9 / 165.5 / 177.2 | 109.9 / 65.5 / 117.5 / 148.5 / 171.9 | 16.6 % |
| `combat_10_local` (20) | 47.3 / 31.9 / 40.5 / 73.4 / 97.3 | 67.8 / 49.3 / 67.9 / 80.4 / 93.1 | 64.5 / 51.4 / 65.2 / 72.5 / 81.7 | 43.3 % |
| `simq_corpus_crowded_frontier` (1000) | 69.7 / 25.9 / 61.8 / 119.2 / 570.4 | 58.8 / 20.1 / 52.1 / 99.4 / 564.4 | 51.3 / 22.3 / 40.6 / 113.5 / 866.6 | 35.8 % |
| `combat_10_concurrent` first window | 46.6 / 30.4 / 42.1 / 71.5 / 83.4 | 110.7 / 37.7 / 82.1 / 205.9 / 291.8 | 53.5 / 32.1 / 52.0 / 72.5 / 75.2 | 137.4 % |
| `combat_10_concurrent` retry | 64.6 / 48.5 / 62.2 / 84.8 / 86.3 | 58.9 / 45.6 / 56.6 / 72.1 / 72.9 | 60.7 / 37.3 / 60.5 / 72.2 / 80.4 | 9.6 % |
| `resource_100_concurrent` first window | 233.1 / 190 / 236 / 265 / 305 | 370.0 / 140 / 279 / 754 / 918 | 212.9 / 161 / 204 / 272 / 301 | 73.8 % |
| `resource_100_concurrent` retry | 236.3 / 177 / 238 / 281 / 295 | 218.5 / 124 / 230 / 266 / 267 | 210.0 / 147 / 205 / 259 / 282 | 12.5 % |

## Named cause per record

1. **`idle_100_local`: host-speed regime, bimodal in time (inferred).** Run 3 has a contiguous plateau at 31-32 ms (ticks 8-9, 15-21) next to ~55-65 ms ticks; runs 1 and 2 never leave 49-74. Idle does constant work per tick, so the 2x difference is not the workload. Not warm-up (first-20 % ≈ run avg), not GC (disabled). Cannot say host vs process without more data.
2. **`movement_100_local`: host regime steps (inferred), barely over the rule (16.6 % vs 15 %).** Within-run step changes of about 2x lasting 10-30 ticks (run 2: 63-90 ms, then 165 ms from tick 19; run 3: 125 ms, then 66-80 ms from tick 30, then 129-148 again), lag-1 autocorrelation 0.30 / 0.76 / 0.81. Minor warm-up residue in run 1 only.
3. **`combat_10_local`: two clusters across processes plus a window too short to average them.** Run 1's base is ~33-41 ms (with a 7-tick burst to 97), runs 2 and 3 sit at 57-73. 20 sampled ticks is about 1 s, one regime per process.
4. **`simq_corpus_crowded_frontier`: unknown, with GC, warm-up and periodicity ruled out.** Aperiodic spike bursts (6, 12, 39 ticks above 3x the median; max 570-867 ms) carry only 2-13 % of total ms; **with the spikes removed the three averages are still 68.4 / 56.3 / 46.4 ms (a 47 % spread)**, so the spread is a between-process level shift, not the spikes. Load is not monotone with the avg (run 1: load 0.62, the slowest). Autocorrelation 0.38-0.59, 10-tick block means range 28-102 ms: slow drift.
5. **`combat_10_concurrent` (retry-promoted): host load, NOT bimodal.** First window ran at load 5.2-5.4 (run 2 starts slow: first 20 % of ticks at 192 ms). The retry window at load 1.1 gives three runs in one cluster (58.9-64.6 avg, block means 56-70). The retry values sit inside the first window's range, so the v0001 record is not an outlier. Recommendation: keep it.
6. **`resource_100_concurrent` (retry-promoted): host load in the first window, plus a real within-run drift.** Retry window at load 1.2: one cluster (210-236). **All three retry runs and first-window run 3 rise through the 20 sampled ticks (first 20 % 173-202 ms, last 20 % 256-278 ms, autocorrelation 0.43-0.55).** The avg therefore depends on the window length; this matches the growth in `docs/performance/tick_cost_growth.md`. Keep v0001, and note the drift in the ledger.

## Do steal and cpu MHz show the host regime here? (checked 2026-10-15, read-only)
**No.** `/proc/stat` steal read 0 in three samples a second apart (total jiffies advancing normally); `cpu MHz` read 2687.998 on all 6 vCPUs in every sample; `/sys/devices/system/cpu/cpu0/cpufreq` does not exist. This is a VirtualBox guest with no paravirt steal accounting, so P1 (steal, MHz) is kept as cheap tooling but cannot show the regime. The **fixed host-speed probe (P1b)** can: 40 calls of a 200k-iteration spin, 0.25 s apart, on an otherwise light host (loadavg 1.0) took **23.2 to 99.5 ms (median 27.8, max/min 4.3x)** for byte-identical work, so the guest's effective speed does move on a sub-second scale while steal and MHz stay flat. At 400k iterations (the shipped size) 20 back-to-back calls gave 47.1 to 61.2 ms (median 54.3). Whether the probe tracks the tick average is the open question the re-record will answer (the quiet-host variation above is the separate, already measured fact).

## Measured fact: an identical spin varies 4.3x on a quiet host (independent of our code)
- **What:** `host_speed_probe`-style spin (`x = (x * 1103515245 + 12345) & 0x7FFFFFFF`, 200 000 iterations, pure Python, no allocation, no I/O, no engine code), called 40 times with a 0.25 s sleep between calls, in one python3 3.13 process on the perf worktree.
- **When and under what load:** 2026-10-15 about 23:01, `uptime` loadavg 1.02 / 0.79 / 0.58, VirtualBox guest (6 vCPU, i5-11400H), swap in use about 6 GB.
- **Result:** min 23.2 ms, median 27.8 ms, max 99.5 ms (max/min 4.3x); 36 of 40 calls were within 23 to 38 ms, the rest 47.9 and 99.5 ms. The command is the 6-line loop in the session scratchpad, reproduced by `rerun_baselines.host_speed_series()` (the shipped probe is 400 000 iterations, 47 to 61 ms over 20 back-to-back calls at the same load).
- **Reading:** byte-identical work took 4.3x longer on some calls with the host nearly idle, so the guest's effective speed varies on its own, independent of the engine. This is the evidence the 15 % policy question rests on: it is a property of this host, not of the scenarios. **It does not show that the probe tracks the tick averages** (the open question for the re-record, below); one 50 ms sample is also too short a snapshot of a regime that lasts about 0.5 to 2 s, so the shipped probe takes 5 calls on each side and records all of them.

## What this means for the cause "host"
Common fast floor: `idle_100_local` run 3 (31 ms plateau), `combat_10_local` run 1 (32 ms), and `combat_10_concurrent` first window (30 ms min) share a 30-33 ms minimum although the workloads differ. That points at a host-level speed state (CPU frequency or steal on the VirtualBox guest), not at the scenarios. **It is a hypothesis; the kept samples cannot prove it.** `/proc/stat` steal and `cpu MHz` are not in the meta files.

## `mixed_200` naming (AC4)
`build_mixed_state(entity_count=200)` builds 80 heroes + 60 monsters + 60 nodes; nodes are resource nodes, so the entity dict holds **140**. `baseline_lifecycle.py` has only `promote` and `check` (no rename), neither `mixed_200_*` record is promoted (both leave NORMAL), and the legacy files are the only artefacts that carry the name. Recommendation: **document, do not rename**: the name follows the requested `entity_count` argument like `idle_100`, the ledger already says "140 entities in the state the 200-entity request builds"; add a docstring line to `build_mixed_state` (docstring only, output unchanged) and one ledger line.

## Discarded attempt: `simq_corpus_crowded_frontier`, 2026-10-16 15:28 (current 3-run rule), NOT promoted
`rerun_baselines.py record simq_corpus_crowded_frontier --keep-samples` (output under `reports/perf/t08_noisy/`, git-ignored): averages 59.214 / 53.369 / 54.026 ms, spread 10.9 % (under 15 %), median run 3. **Run 2 started at loadavg1 1.56, above the 1.5 precondition** (runs 1 and 3: 1.25 and 1.38), so the attempt does not meet the quiet-window rule, which applies to every measured run, not only the promoted one. perf-planner decided it is discarded and redone at a quieter moment. Probe medians (before the state build, then after): 36.6 -> 26.3 / 33.9 -> 35.8 / 34.1 -> 39.8 ms; swap used 591 MB in all three. The candidate file is kept as evidence only and must not be promoted.

## Re-records of 2026-10-16 (committed tool 9accca4ad, enforced quiet window); NOTHING promoted, the owner decides
Output `reports/perf/t08_noisy2/<name>/` (git-ignored). Every run started with loadavg1 below 1.5; swap in use 543 MB; all NORMAL, schema 1.2.

| record | rule | runs | averages (ms) | spread (rule) | all-runs spread | candidate |
|---|---|---|---|---|---|---|
| `simq_corpus_crowded_frontier` | all runs | 3 | 57.805 / 56.200 / 55.695 | 3.8 % | 3.8 % | run 2 |
| `combat_10_local` (10 + 100 ticks) | middle 3 of 5 | 5 | 47.906 / 41.162 / 45.793 / 46.961 / 44.276 | 6.1 % | 16.4 % | run 3 |
| `idle_100_local` (10 + 50) | middle 3 of 5 | 5 | 49.072 / 46.622 / 48.156 / 56.511 / 49.703 | 3.2 % | 21.2 % | run 1 |
| `movement_100_local` (10 + 50) | middle 3 of 5 | 5 | 110.603 / 96.060 / 107.863 / 94.471 / 108.498 | 13.0 % | 17.1 % | run 3 |

### Does the host-speed probe track the tick average? (computed, 18 runs)
Pearson / Spearman of the run's average tick latency against the probe median taken after the run, before the run, and their mean (a slow host should give both a longer probe and a longer tick, so a tracking probe shows a positive correlation). Per record (n = 3 to 5, so each is weak evidence) and pooled over all 18 runs, each probe value and each average expressed relative to its record's median:

| | after-run probe | before-run probe | mean of the two |
|---|---|---|---|
| `simq_corpus_crowded_frontier` (n 3) | r -0.55 | r +0.05 | r -0.38 |
| `combat_10_local` (n 5) | r -0.52 | r +0.68 | r +0.25 |
| `idle_100_local` (n 5) | r -0.61 | r +0.62 | r +0.01 |
| `movement_100_local` (n 5) | r +0.44 | r +0.23 | r +0.29 |
| pooled (n 18) | r -0.37, rho -0.42 | r +0.47, rho +0.35 | r +0.19, rho -0.09 |

**Reading, stated plainly: there is no consistent relation.** The sign flips between records and between the before and the after probe; the after-run probe is negatively correlated with the tick average when pooled, the before-run probe positively (r +0.47 for n 18 is at the edge of p 0.05, and the opposite sign of the other probe argues against reading it as a signal); the mean of the two is r +0.19. So the probe as built does **not** show that the tick-average spread is the host's speed regime. The host-regime cause therefore stays **inferred** (the 4.3x spread of an identical spin on a quiet host is a measured fact; that it is what moves these tick averages is not shown). Possible reasons the probe misses it, none tested: the regime changes faster than the 5 x 50 ms probe window, the probe runs outside the window seconds before and after it, a pure integer spin and an engine tick are bound differently, and 3 to 5 runs per record is little data.

### `movement_100_local`: draft ledger note (for the owner's decision on promotion)
Five fresh-process runs under the owner's middle-3 rule (2026-10-16) gave 94.5, 96.1, 107.9, 108.5, 110.6 ms: **two clusters, about 95 ms and about 109 ms (14 % apart)**, the median (107.9 ms) in the upper one. The middle-3 spread is 13.0 % (all five: 17.1 %), inside the 15 % rule, so the record passes the rule, but another five runs could put the median in the lower cluster and move the baseline by about 12 %. This is the bimodality the T08 diagnosis described for the local records; the probe does not explain it (see above). If promoted, the ledger line says so and the baseline is read as one of two plausible values, not as a point.

### What promoting `idle_100_local` and `movement_100_local` changes for the nightly tripwire lane
- `tripwire.load_baseline(name)` returns the latest promoted `<name>.vNNNN.json`; a legacy `<name>.json` is only a reason string. Today both names resolve to the legacy file, so `tests/perf/test_perf_regression_baseline.py::test_regression_vs_baseline[idle_100_local|movement_100_local]` reports INCONCLUSIVE "legacy tripwire reference" and runs **no head measurement**.
- After a promotion, the same test finds a record, **runs the head** (`run_once` of the declared `RunSpec`, 10 + 50 ticks, unchanged) and `compare`s it with `TRIPWIRE_THRESHOLDS` (relative 0.40, absolute 5 ms). The outcome is PASS, REGRESSION, or INCONCLUSIVE (the identity checks include `cpu_model`, blocking, and `declared_hardware_class`, so a CI runner that is not this VM's i5-11400H gives INCONCLUSIVE). It is still non-blocking: a non-PASS is a `PerformanceThresholdWarning`.
- The test is `slow`, so it runs in `.github/workflows/slow-regression.yml` (`pytest tests/ -m "slow or extra_slow"`, scheduled 4 times a day). **The lane would start executing a head measurement and a comparison for these two scenarios; the RunSpec, the thresholds and the PR lane (`tripwire.py run`, base against head, no stored baseline) do not change.**
- `LEGACY_TRIPWIRE_REFERENCES` only exempts file names from `baseline_lifecycle.py check`. Removing `idle_100_local.json` / `movement_100_local.json` from it requires deleting those legacy files (otherwise `check` rejects them as invalid records); `load_baseline` already prefers a promoted version over the legacy file, so the list change itself does not alter what any lane compares. `tests/unit/perf/test_baseline_lifecycle.py` pins `len(LEGACY_TRIPWIRE_REFERENCES) == 10`, which would change to 8.
