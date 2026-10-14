---
status: historical
layer: performance
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20261010-PERF-M2-T08-CANONICAL-RERUNS
date: 2026-10-13
tags: [performance, benchmarking, regression]
---

# Plan: TCK-20261010-PERF-M2-T08-CANONICAL-RERUNS

Branch `perf-m2-t08-canonical-reruns` from `origin/main` 06aa3a20c (RPG's hunting batch is on main as #536, so tactical and combat-heavy records are **post-hunting** with no pre-hunting label; `combat_10_*` and the fighting corpus worlds are still labelled `WORK_MODEL_V1`). Every record: provisional, `runner.controlled=false`, claims none, host and CPU in `identity.runtime`, the measured main sha in `identity.engine.commit` plus a `promotion.note` that names it.

## Revisions on perf-planner's go (2026-10-13)
- **Load-noise control (condition 1):** the committed protocol (ticks) is unchanged for comparability, but every record is measured **3 times, each in a fresh process**, one at a time; the run with the **median avg tick ms** is promoted, all 3 candidate files stay under `reports/perf/t08/` (uncommitted). `promotion.note` carries the 1-minute loadavg and swap used at the start of each of the 3 runs and the three avg values. **Spread** = max/min avg over the 3: above **15 %** the record is **not promoted**, the old file stays, the ledger marks it **NOISY**, and the PR body lists it for a re-run on a quieter host.
- **Step 6 is a deviation from the ticket text** ("T03-format records"): `src gate` and `compare-sweep` validate `BaselineConfig`, so `latest.json` becomes a generated `BaselineConfig`. Recorded in the ticket's Assumptions and Implementation Notes. The deletion list (14 matrix files, `matrix_full.json`, `test_perf_idle_baseline.json`) rests on the grep evidence in investigation.md section A; the PR body lists the deletions under the owner gate.
- **Run table:** the number of processes is 3 per record (so 10 x 3 + 3 x 3 = 39 short runs); wall estimates below are per process. Profiles are read from each old file's `profile` field (investigation.md section C), the combat call shape is `team_a_count=team_b_count=10, seed=42` (section B), and the RSS/wall sources are named in section D.
- **evaluate_simq (step 5):** cap 2.5 GB, its first run's peak RSS reported before anything else runs; OOM-kill or cap blown means stop and report to perf-planner and lead-planner, the cap is not raised. Lead-planner is told before the first corpus run.
- **PR before/after table columns:** record, run count, spread %, loadavg (start of each run), profile, ticks (warmup+sampled), host/CPU, old avg ms, new avg ms.

## Order (one process at a time; nothing runs before perf-planner approves this file)
0. **Dry check, no heavy run:** old-file slow test (policy 2.2 step 4): `pytest tests/perf/test_perf_regression_baseline.py -m slow -s` against the files as they are now; keep the output in `reports/perf/t08/old_file_slow_test.txt` and in the PR body. Expected: INCONCLUSIVE "legacy tripwire reference" for both declared scenarios (the 15 files are identity-less), so it executes no head run.
1. **Step 1, the three `simq_corpus_*` records** (`crowded_frontier`, `frontier_extended`, `frontier_marches`), canonical variant of `PERF_512MB_LOCAL`, 100 warmup + 1000 sampled ticks (the committed protocol).
2. **Steps 2 and 3, the 10 non-mixed `*_local` / `*_concurrent` records**, profile = the one named in each old file's `profile` field, canonical variant, 10 warmup + 20 sampled ticks (the committed protocol).
3. **Step 5**, `python3 tools/evaluate_simq.py` diff against the grade anchors; commit nothing when the diff is empty, record the result in the ledger.
4. **Step 6**, the sweep-gate baseline (see below).
5. `mixed_200_local` / `mixed_200_concurrent`: **PENDING** in the ledger. #544 (spawn-collision) is approved and waits on #546; if it merges before this PR, merge main and record them here, otherwise a small follow-up ticket.
6. Docs: ledger section 3 and 5 status columns, DEV-020 consequences (1) and (3), `perf_baseline_policy.md` pointer if needed; `make knowledge-index-update`; `make docs-registry` runs in Finalize.

## How a record is made (new tool, `tools/perf/rerun_baselines.py`, perf-owned)
`capacity_run.run_once` only builds `SCENARIO_BUILDERS` states; corpus worlds need `calibrate_simq._load_world_state`. The new tool has two sub-commands, `scenario <name>` and `corpus <world>`, each one fresh process that builds the state, runs `BenchHarness` under `PERF_CANONICAL_PROFILES[<profile>]` with a `RecordOptions(gate_tier=TRIPWIRE, projection="tripwire_baseline", runner=Runner(controlled=False, name=<host>))`, and writes the schema record to `reports/perf/t08/<name>.json` (uncommitted). Promotion is only `tools/perf/baseline_lifecycle.py promote --candidate ... --name <name> --cause TCK-20261010-PERF-M2-T08-CANONICAL-RERUNS --note "..."`; it refuses a dirty `src/` tree, a non-NORMAL mode sequence and a missing cause. Each promoted file is `tests/perf/baselines/<name>.v0001.json`; the old `<name>.json` is then deleted and dropped from `LEGACY_TRIPWIRE_REFERENCES`, so `baseline_lifecycle check` stays green. The `combat` adapter (old `combat_10_*` used `team_a=team_b=10`) is an open item for the investigation: the tool follows `run_benchmarks.py`'s own call shape, not a guess.

## Step 6 (sweep gate), proposed
`src gate` and `compare-sweep` read a `BaselineConfig` (`baseline_v1`, written by `generate-baseline` from a sweep), not a schema-1.1 `BenchmarkRecord`; a record cannot be parsed by them (they model-validate `BaselineConfig`). So the replacement for `latest.json` is **a `BaselineConfig` produced by `python3 -m src generate-baseline` from a real sweep**, carrying `cost_accounting_version` so it is comparable. Proposed: scenario `idle`, sandbox, seeds 1..5, small tick count, then a second sweep compared with `compare-sweep` and `gate`; both must exit 0 on `docs/observability/baselines/latest.json`, output kept. The 14 per-profile matrix files and `matrix_full.json` / `test_perf_idle_baseline.json` have no code consumer and are incomparable: **delete them** (history stays in git) and leave `docs/observability/baselines/README.md` pointing at the promoted records under `tests/perf/baselines/` and at `latest.json`. The guide commands in `docs/guides/observability.md` and `simulation.md` keep their path (it is the same path) and gain a note on what the file is. No `src/cli/entry.py` edit is expected; if one turns out to be needed I stop and ask for the lift.

## Run list: expected peak RSS and duration (from the old records' `mem_rss_mb.max` and `wall_clock_s`, see investigation.md section D; each row is run 3 times; machine is lead-planner's: 9 sessions, ~5 GB swap)
Every run in the **foreground**, one at a time, `systemd-run --user --scope -p MemoryMax=<cap> -p MemorySwapMax=0 ...`. No run is expected to exceed 3 GB, so no lead-planner go is needed; I tell lead-planner before the first corpus run anyway. A run that is OOM-killed or blows its cap stops the plan and is reported; I do not raise the cap.

| # | run | profile (canonical) | ticks | expected peak RSS | expected wall | cap |
|---|---|---|---|---|---|---|
| 1 | corpus crowded_frontier | PERF_512MB_LOCAL | 100+1000 | 0.7 GB | 10-20 s | 2.5 GB |
| 2 | corpus frontier_extended | PERF_512MB_LOCAL | 100+1000 | 1.5 GB | 15-30 s | 2.5 GB |
| 3 | corpus frontier_marches | PERF_512MB_LOCAL | 100+1000 | 1.4 GB | 15-30 s | 2.5 GB |
| 4-8 | idle_100 (512MB), movement_100 (1GB), resource_100 (1GB), combat_10 (2GB), strategic_100 (2GB) `_local` | per old file `profile` | 10+20 | 0.15 GB | 3-5 s each | 1 GB |
| 9-13 | the same five `_concurrent` | idle 1GB CONC, the other four 2GB CONC (per old file `profile`) | 10+20 | 0.15 GB | 3-5 s each | 1 GB |
| 14 | step 5 `evaluate_simq.py` | n/a | n/a | measured on its first run, reported before more | unknown | 2.5 GB |
| 15 | step 6 two sweeps (`idle`, 5 seeds, few ticks) | n/a | small | 0.3 GB | under 1 min | 1 GB |

Max-RSS and wall of each run are recorded next to its record (`/usr/bin/time -v` or the harness's own `mem_rss_mb`), so the next rerun cites measured numbers.

## Owner gate
New baselines need the owner's approval. The PR body carries the before/after table (old avg tick ms, new avg tick ms, profile, ticks, host) for lead-planner to take to the owner. No push without the owner's yes.

## Out of scope
Step 4 (`baseline_5k.json`, RPG) is only marked in the ledger. No `src/` edit outside the OD-8 lift list. No A/A calibration (lead-planner dispatches those after #529 merges).
