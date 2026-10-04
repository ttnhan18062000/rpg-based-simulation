---
status: active
layer: performance
authority: P2
audience: agent
ticket_id: TCK-20261004-PERF-M1-DEBT-HARNESS-CORRECTNESS
phase: open
date: 2026-10-04
tags: [performance, testing, bug]
---

# TCK-20261004-PERF-M1-DEBT-HARNESS-CORRECTNESS

## Title
PERF-M1-T02: fix the long-run harness's work-debt accounting and test it with non-empty debt

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Released by the owner's partial lift of the RPG-core entry gate on 2026-10-04
(`performance_optimization_roadmap.md`, "Gate definition and partial lift"), which allows M1 to
edit `src/perf/long_run_harness.py`.

`LongRunStabilityHarness` (`src/perf/long_run_harness.py`, around line 211) computes
`candidate_count = sum(len(q) for q in kernel.state.work_debt.values())`. `work_debt` is
`Dict[str, int]` (`src/core/state.py`; PERF-D3: capacity debt is an integer counter per system), so
`len()` on an `int` raises `TypeError` on the first sample in which any debt exists. The
`if kernel.state.work_debt else 0` guard hides this while debt is empty, which is the case in every
fixture today. This is defect PA-02, found in the M0 audit and confirmed still present on 2026-10-03.
The `work_debt` sum on the line above is correct.

## Scope
- Fix `candidate_count` so it is defined for integer debt. Decide, with a reason written in the
  ticket, whether it means the number of systems with non-zero debt or is removed as a duplicate of
  `work_debt`. Do not keep a field whose meaning nobody can state
- Specification tests with non-zero debt and exact expected counts: one system with debt, several
  systems, a system whose debt returns to zero, and empty debt
- A run of the harness on a short fixture that really accumulates debt (for example a profile
  with a low phase budget, or a seeded `work_debt` in the initial state). Prove the samples report
  exactly the debt the state holds at each sampled tick
- Non-interference: show that sampling reads state only. The proof digest
  (`CanonicalStateHasher.get_hash`) of a run with sampling must equal the same run without
  sampling, at the same ticks
- Update `docs/performance/` text that describes the harness's debt fields, if there is any

## Out of Scope
- `src/engine/governor.py`, `src/engine/kernel.py` and the other gated files: no edit
- Changing what counts as work debt or how the governor consumes it (PERF-D3 is closed)
- Any baseline or capacity claim. Numbers from this harness stay provisional under the entry gate
- Combat-heavy scenarios: `TCK-20261003-COMBAT-TACTICAL-PATH-NONDETERMINISM-SURVIVES-AUDIT-MODE` is open

## Acceptance Criteria
1. With non-zero integer debt, the harness samples without error, and `work_debt` and the chosen
   `candidate_count` meaning match hand-computed values exactly
2. At least one test drives real (not mocked) debt accumulation through the kernel and checks the
   sampled values against `kernel.state.work_debt` at the same tick
3. The sampling-on and sampling-off runs produce equal proof digests at every compared tick
4. Revert test: putting back the old `len()` line makes the new tests fail with `TypeError`
   (record the output)
5. `tests/certification/test_cert_long_run_stability.py` still passes

## Related Tickets
- `TCK-20260913-PERF-M0-SOURCE-AUDIT` (PA-02 finding)
- `TCK-20261003-COMBAT-TACTICAL-PATH-NONDETERMINISM-SURVIVES-AUDIT-MODE` (avoid its path)

## Related Docs
- `docs/plans/design_enhancement/performance_optimization/performance_m1_correctness_prerequisites_epic.md` (PERF-M1-T02)
- `docs/architecture/performance_optimization_decisions.md` (PERF-D3)
- `docs/plans/design_enhancement/performance_optimization/performance_optimization_roadmap.md` (gate section)

## Related Stored Artifacts
- none

## Related Code Areas
- `src/perf/long_run_harness.py` (edit allowed)
- `src/core/state.py` (`work_debt`, read only)
- `tests/certification/test_cert_long_run_stability.py`

## Assumptions / Open Questions
- Any parity ledger entry (`infrastructure.yaml`) that cites the harness's debt fields must be
  updated with the fix
- If accumulating real debt is impossible without editing a gated file, stop and report it.
  Do not edit the gated file

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
