---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261003-SOCIAL-APPRAISAL-MUTATION-BASELINE
phase: open
date: 2026-10-03
tags: [testing]
---

# TCK-20261003-SOCIAL-APPRAISAL-MUTATION-BASELINE

## Title
Phase 2 social item 4 (Effectiveness): one mutation baseline on `src/systems/social_systems/appraisal.py`

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary

Phase 2 plan §6 item 4. Run one mutation baseline on `appraisal.py` (highest P0 ledger density; fallback
`contracts.py`) against the existing social unit tests **unchanged**, and record it in the same shape as
`tests/mutation/baselines/src_core_conservation_v3.json`. Survivors are findings, not fixes.

## Scope

1. A baseline file `tests/mutation/baselines/src_systems_social_appraisal_v1.json` (name provisional,
   fixed at plan review) with: target, selection (the exact test selection), full `origin/main` SHA,
   date, runtime, result categories, `stale_after`, and whether the kernel ran.
2. Determinism (G3): state per the selected tests whether the kernel runs (at `2f520f0dd` only
   `tests/unit/social/test_multi_hero.py` references it). If the kernel runs, the run sets
   `audit_mode=True` and relaxes `max_tick_budget_ms` (`docs/engine/deterministic_execution.md`
   Extension rule 5). If it does not, say so.
3. A survivor list. The mutants on the reputation-read lines (46 and 64) are listed **separately**,
   labelled "current behaviour, catalog-CONFLICTING" (PERC-01 / KNOW-01). Not suggested as test targets.
4. Use the Phase 1 method (scratch copy via `git archive`, mutmut installed with `pip --target`, run
   detached with `setsid`), re-derived, since the helper scripts are gone.

## Out of Scope

- Editing, moving, marking or strengthening any social test to kill a survivor (owner constraint, 2026-10-03).
  Survivors are recorded only.
- Changing `appraisal.py` or any source file.
- party*.py, memory.py, perception, dormant paths; any other target.
- A required check, CI job, or promotion.

## Acceptance Criteria

- [ ] `git diff --name-only` against `origin/main` shows no test file outside
  `tests/mutation/baselines/`.
- [ ] The baseline records every field in Scope item 1, and the numbers match a stated command.
- [ ] A positive control is recorded (a mutant that must be caught is caught, or the run is not
  trusted), and the selection ran green before mutation.
- [ ] G3 is stated; if the kernel ran, `audit_mode=True` and the relaxed budget are recorded.
- [ ] The survivor list and the separate CONFLICTING list are both present.
- [ ] The record carries the RELATIONSHIP-VECTOR staleness line, and `stale_after` is set from it
  (`appraisal.py` measurements go stale when `TCK-20260822-RELATIONSHIP-VECTOR-ADDITIVE-FIELD` lands).
- [ ] If `appraisal.py` changed on `origin/main` between plan and run, the baseline names the SHA used.

## Related Tickets

- Parent: `TCK-20261003-EPIC-TEST-SCALE-OUT-SOCIAL`.
- Template: `TCK-20261003-MUTATION-BASELINE-V3-SUPERSET-SELECTION` (done).

## Related Docs

- `docs/plans/test_architecture/phase2_social_scale_out.md` §5 (G3) and §6 item 4
- `docs/engine/deterministic_execution.md`
- `docs/testing/core_rpg_test_baseline_2026-09-30.md` (re-verification section)

## Related Stored Artifacts

- `tests/mutation/baselines/src_core_conservation_v3.json` (provenance template)

## Related Code Areas

- `src/systems/social_systems/appraisal.py` (read only)
- `tests/unit/social/` (run unchanged)
- `tests/mutation/baselines/`

## Assumptions / Open Questions

- The exact selection (which social tests exercise `appraisal.py`) is derived by import, then
  confirmed green; it is fixed at plan review.
- The long run is detached with `setsid`; runtime is recorded in the file.

## Implementation Notes

All figures re-measured at the then-current `origin/main`, with the full SHA.

## Test Summary

Not run yet.

## Files Changed

None yet.

## Completion Summary

Not complete.
