---
status: active
layer: performance
authority: P1
audience: agent
ticket_id: TCK-20261014-PERF-T08-NOISY-AND-OFF-NORMAL-BASELINES
phase: open
date: 2026-10-14
tags: [performance, benchmarking]
---

# TCK-20261014-PERF-T08-NOISY-AND-OFF-NORMAL-BASELINES

## Title
Finish the baselines PERF-M2-T08 could not promote: diagnose the intrinsic noise first, then re-record the NOISY and off-NORMAL records

## Status
INPROGRESS

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
PERF-M2-T08 (#591) promoted 5 of 15 records. The other 10 remain legacy references:
- **4 PENDING-NOISY:** `idle_100_local`, `movement_100_local`, `combat_10_local`, `simq_corpus_crowded_frontier`. They stayed above 15% spread even in a quiet window (load 0.6-1.3; `combat_10_local` 96.9%), so the noise is likely intrinsic to the run, not host contention.
- **6 off-NORMAL:** they are handled by `TCK-20261014-PERF-TICK-COST-GROWTH-INVESTIGATION` first.
- **2 promoted only on the retry window** after very wide first windows: `combat_10_concurrent` (137% → 9.6%) and `resource_100_concurrent` (74% → 12.5%). A bimodal path is not ruled out.

## Scope
1. **Diagnose before re-measuring.** From the per-tick samples T08 kept under `--keep-samples`, give each NOISY record and the two retry-promoted records:
   - per-run min, median, p95 and max tick ms;
   - whether the first sampled ticks dominate (warm-up);
   - whether the runs are bimodal (two clusters of averages);
   - whether a GC pause lines up with the outliers (`gc.callbacks`, or `PYTHONMALLOC` stats if needed).
   Do not ask for another quiet window until this analysis says the host is the cause.
2. **Fix the protocol, then re-record.** Pick the smallest change the analysis supports: longer sampling, a warm-up drop, or the median of more runs. It must stay comparable with the nightly tripwire lane for the two declared tripwire scenarios (`idle_100_local` and `movement_100_local` use `tripwire.TRIPWIRE_SCENARIOS`; changing that `RunSpec` is a tripwire change that needs testing-planner's agreement). Record the protocol change in `perf_baseline_policy.md` (P1: the owner approves) and the ledger. Then re-record through `tools/perf/rerun_baselines.py` and promote only through `baseline_lifecycle.py promote`.
3. **Retry-promoted pair:** if the analysis shows they are bimodal, demote or replace the v0001 records through the lifecycle tool, with a cause.
4. **Off-NORMAL records** (`strategic_100_*`, `mixed_200_*`, `simq_corpus_frontier_extended`, `simq_corpus_frontier_marches`): re-measure only after the tick-cost investigation and rpg's fixes, or after an owner decision on a larger profile (option i). Until then they stay "not a baseline under canonical" in the ledger. This ticket closes with them PENDING if that work has not landed. Do not hold the ticket open for it.
5. **`mixed_200` naming:** the state built for 200 has 140 entities. Either rename the record (a new name through the lifecycle tool) or document the count in the scenario docstring and the ledger. Do not change `build_mixed_state`'s output silently.

## Out of Scope
- The tick-cost attribution (`TCK-20261014-PERF-TICK-COST-GROWTH-INVESTIGATION`).
- Any `src/` change outside `src/perf/`.
- A/A calibration of the CI tripwire threshold (dispatched separately after #529 merges; it feeds T06).

## Acceptance Criteria
- AC1: The noise diagnosis for the 4 NOISY plus the 2 retry-promoted records is written up, with the per-run distributions and a named cause per record (warm-up, bimodal, GC, host, or unknown, with what was ruled out).
- AC2: Any protocol change is agreed (testing-planner for the tripwire RunSpec; the owner for the policy paragraph) before the re-record.
- AC3: Every record that meets the 15% rule under the agreed protocol is promoted. The rest stay PENDING with the reason in the ledger.
- AC4: The `mixed_200` naming is resolved.
- AC5: The same resource rule as T08 (one at a time, capped, lead-planner told before any run over about 3 GB).

## Related Tickets
- TCK-20261010-PERF-M2-T08-CANONICAL-RERUNS (#591), TCK-20261014-PERF-TICK-COST-GROWTH-INVESTIGATION, TCK-20261011-PERF-M2-T03B-CI-PAIRED-STEP (#529, tripwire)

## Related Docs
- docs/performance/baseline_invalidation_ledger.md, docs/performance/perf_baseline_policy.md

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261010-PERF-M2-T08-CANONICAL-RERUNS/ (evidence.md, investigation.md)

## Related Code Areas
- tools/perf/rerun_baselines.py, tools/perf/baseline_lifecycle.py, tools/perf/tripwire.py, src/perf/scenarios.py

## Assumptions / Open Questions
- Ordering: do not delete idle_100_local.json before TCK-20261016-PERF-CORPUS-BASELINES-ON-LIFECYCLE-RECORDS lands, or in the same PR; tests/tools/test_corpus_perf_baseline.py reads it as a shape reference until then.
- A1: T08's `reports/perf/t08/*/samples/` per-tick data is still on disk in ~/Work/rpg-perf. If it was cleaned, the diagnosis re-runs the 6 records with `--keep-samples` (seconds each).

## Implementation Notes
Status 2026-10-16: **open; the batch ships with two promotions pending.** Done:
- **AC1, diagnosis:** from the kept per-tick samples, named causes per record (investigation.md): GC and warm-up ruled out; idle_100_local bimodal in time; movement_100_local regime steps; combat_10_local two clusters across processes plus a window too short; simq_corpus_crowded_frontier cause unknown (spread survives removing the spikes); the two retry-promoted records not bimodal (host load in the first window), kept. Measured fact: an identical spin varies 4.3x on a quiet host. The host-speed probe shows no consistent relation to the tick averages (18 runs), so the host-regime cause stays inferred.
- **Protocol:** P1 (steal and MHz, flat on this guest) and P1b (5 probes per side) in `rerun_baselines.py`; P3 (`combat_10_local` 20 to 100 sampled ticks); the quiet window (loadavg1 < 1.5 and 2.5 GB available before every run) enforced by the tool, which waits up to 15 minutes and refuses to start outside it; `--cause` is a required argument (a hard-coded cause had named the wrong ticket).
- **P2, owner decision 2026-10-16 "(a) Middle-3 spread":** 5 fresh-process runs, the median run, the 15 % spread over the middle 3, fixed by name for `idle_100_local`, `movement_100_local`, `combat_10_local`; code, tests and the DRAFT `perf_baseline_policy.md` section 2.1 (the owner approves it in the PR). lead-planner had recommended (b).
- **AC4:** `mixed_200` documented (140 entities plus 60 resource nodes for a 200 request), pinned by a test, not renamed.
- **Re-records** (quiet window, all NORMAL): `simq_corpus_crowded_frontier` (3 runs, spread 3.8 %), `combat_10_local` (5 runs, 6.1 % over the middle 3), `idle_100_local` (3.2 %), `movement_100_local` (13.0 %, two clusters at about 95 and 109 ms). An earlier crowded_frontier attempt was discarded (one run started at loadavg1 1.56).
- **Promotion, owner decision 2026-10-16 "(a) Promote all four":** `simq_corpus_crowded_frontier.v0001` and `combat_10_local.v0001` promoted through `baseline_lifecycle.py promote`; `combat_10_local.json` deleted (list 10 to 9); `simq_corpus_crowded_frontier.json` stays because the corpus test and `bench_corpus_world.py --commit` still read it (follow-up `TCK-20261016-PERF-CORPUS-BASELINES-ON-LIFECYCLE-RECORDS`).
- **Not done, waiting on #613 (testing-planner):** promotion of `idle_100_local` and `movement_100_local`. Promoting them makes the nightly slow lane (`test_regression_vs_baseline`, run by slow-regression.yml) start comparing against them; it needs testing-planner's agreement (AC2). Their legacy files stay. The owner decided "(a) Ship, ticket open" (2026-10-16, via lead-planner): the batch ships with these two pending and this ticket stays open.
- Off-NORMAL records (strategic_100_*, mixed_200_*, simq_corpus_frontier_extended, simq_corpus_frontier_marches) stay "not a baseline under canonical" in the ledger, PENDING as the ticket allows.

## Test Summary
tests/unit/perf/test_rerun_baselines.py (probe series and counters, P3, the tripwire RunSpec pin at 10 + 50, the mixed_200 count, the rule by name, the middle-3 spread and its 15 % boundary with two mutation checks, the note listing all five runs, `record` run counts, the quiet-window wait, required `--cause`); test_baseline_lifecycle.py length pin 9. `baseline_lifecycle.py check` rc=0 after the promotions. Batch-level gates (docs checks, paths guard, mypy gate, `codebase.health check`, `tests/unit/perf`, tools perf/baseline/inventory tests) are run once on the merged tree at batch close and their exit codes sent to perf-planner.

## Files Changed
tools/perf/rerun_baselines.py, tools/perf/baseline_lifecycle.py, src/perf/scenarios.py (docstring only), tests/unit/perf/test_rerun_baselines.py, tests/unit/perf/test_baseline_lifecycle.py, tests/perf/baselines/ (two v0001 added, combat_10_local.json deleted), docs/performance/perf_baseline_policy.md (2.1 draft, 4), docs/performance/baseline_invalidation_ledger.md; staging artifacts under agent-working/staging_artifacts/ (investigation.md, plan.md, test_plan.md, an2_reproduce_ac1.py). Commits are on `perf-t08-noisy-baselines`.

## Completion Summary
NOT CLOSED. Open: promotion of `idle_100_local` and `movement_100_local` (owner-approved, waiting for testing-planner's agreement on #613); the ticket closes when they are promoted or the owner decides otherwise. AC1 (diagnosis written) met; AC2 (policy and tripwire agreement) met for P2 (owner) and open for the tripwire lane (testing); AC3 met for two of four records, the two others owner-approved and pending; AC4 met; AC5 followed.
