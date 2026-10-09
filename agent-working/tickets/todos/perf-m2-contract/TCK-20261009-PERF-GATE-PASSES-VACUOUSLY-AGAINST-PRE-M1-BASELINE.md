---
status: active
layer: performance
authority: P2
audience: agent
ticket_id: TCK-20261009-PERF-GATE-PASSES-VACUOUSLY-AGAINST-PRE-M1-BASELINE
phase: open
date: 2026-10-09
tags: [performance, observability, testing]
---

# TCK-20261009-PERF-GATE-PASSES-VACUOUSLY-AGAINST-PRE-M1-BASELINE

## Title
`src gate` and `compare-sweep` compare tick costs against docs/observability/baselines/latest.json, whose costs were inflated by the double count, so a cost regression can pass the gate

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Found by PERF-M1-T05 (`TCK-20261009-PERF-M1-T05-BASELINE-INVALIDATION-LEDGER`, the ledger row for
`docs/observability/baselines/latest.json`). The guides tell people to run
`python3 -m src gate <sweep_id> --baseline docs/observability/baselines/latest.json`
(`docs/guides/simulation.md:98`) and the same for `compare-sweep` (`docs/guides/observability.md:161`). Both read
the file through `src/cli/entry.py` (`_run_gate`, `_run_compare_sweep`), then
`SweepReportGenerator.generate` and `BaselineComparator.compare_sweep` under `src/observability/reporting/`.

`latest.json` was captured before DEV-017 (#448). Its tick and phase totals counted the unlisted refine
sub-phases twice. A sweep measured on current `main` therefore looks cheaper than the baseline even when it has
regressed: the tick-cost check passes **vacuously**. The ledger marks the file **incomparable**.

No CI job passes this baseline (the gate is a manual, documented command), so the false assurance needs someone
to follow the guide. That is why this is P2, not P1.

## Scope
1. Make the comparison refuse to give a tick-cost verdict against an incomparable baseline. For example, the
   baseline records a cost-accounting or identity version, and the comparator reports
   "baseline incomparable: <reason>" instead of PASS when the version predates DEV-017 or is absent. Prefer the
   M2 benchmark-identity schema field if it exists by then (`docs/performance/benchmark_identity_schema.md`). If not,
   use a minimal version key, and say so.
2. Update the two guides so they don't present `latest.json` as a valid tick-cost baseline until it is replaced
   (the ledger's re-measurement plan, step 6).
3. A test: a sweep compared against a baseline without the version key gets the "incomparable" verdict, not PASS.
   A baseline with the current version still compares as before.

## Out of Scope
- Regenerating `docs/observability/baselines/*` (M2, per the ledger).
- Non-cost checks the gate performs (behaviour, balance envelope), which DEV-017 does not affect.

## Acceptance Criteria
1. `src gate` and `compare-sweep` cannot report a tick-cost PASS against a pre-DEV-017 baseline. A test proves it,
   and it fails on `main` today.
2. The guides no longer present `latest.json` as a current cost baseline.
3. `uv run make code-health` and `uv run make typecheck-py` report no new or worse finding.

## Related Tickets
- `TCK-20261009-PERF-M1-T05-BASELINE-INVALIDATION-LEDGER` (found it)
- `TCK-20261008-PERF-KERNEL-RESOLUTION-OVERHEAD-DOUBLE-COUNTS-SUB-PHASES` (DEV-017)

## Related Docs
- `docs/performance/baseline_invalidation_ledger.md`, `docs/performance/benchmark_identity_schema.md`
- `docs/guides/simulation.md`, `docs/guides/observability.md`

## Related Stored Artifacts
- The T05 ticket's stored artifacts

## Related Code Areas
- `src/cli/entry.py`, `src/observability/reporting/baseline_comparator.py`,
  `src/observability/reporting/sweep_report.py`

## Assumptions / Open Questions
- Filed as M2 plan item X1 (2026-10-10). Use T02b's `cost_accounting_version` identity field (`TCK-20261010-PERF-M2-T02B-RECORD`) as the version key, so it depends on T02b. Scope item 1's "minimal version key" fallback no longer applies.
- Lift boundary (roadmap RPG-core gate item 8): edit only `src/observability/reporting/baseline_comparator.py` and `sweep_report.py`. `src/cli/entry.py` is read-only here.
- **Gate:** these `src/` files are outside every perf lift so far. The fix needs an owner lift for
  `src/observability/reporting/` and `src/cli/entry.py`, or routing to their owner.
- Is the guide edit alone (scope 2) acceptable as an interim measure? It needs no `src/` change.

## Implementation Notes
- 2026-10-09: scope 2 (guides) done as an interim, owner decision; scopes 1 and 3 (code) wait for a lift.

## Test Summary

## Files Changed

## Completion Summary
