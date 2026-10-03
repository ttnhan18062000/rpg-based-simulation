---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261003-SOCIAL-APPRAISAL-MUTATION-BASELINE
phase: done
date: 2026-10-03
tags: [testing]
---

# TCK-20261003-SOCIAL-APPRAISAL-MUTATION-BASELINE

## Title
Phase 2 social item 4 (Effectiveness): one mutation baseline on `src/systems/social_systems/appraisal.py`

## Status
DONE

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

No test added or changed. Selection (46 files, 313 tests) green before mutation, unforced and under the
G3 forcing (313 passed, about 5 s each). Fresh positive control killed. `mutmut` 2.5.1 run: 345 mutants,
188 killed, 157 survived, 0 timeout, 0 suspicious, 1,791 s. `tests/unit/tools/test_mutation_baseline_records.py`:
9 passed with the new record. All at `origin/main` `9640ff942877cc7264e83309f35d19022a4a3fe6`.

## Files Changed

- `tests/mutation/baselines/src_systems_social_appraisal_v1.json` (new data file, not a test)
- `docs/testing/social_test_report_2026-10-03.md` (sections 4 and 5, plus the section 3.1 path-count correction)

## Completion Summary

Done 2026-10-03. Baseline recorded for `appraisal.py`: 188 of 345 mutants killed (54.5%), 157 survived,
nothing classified equivalent. G3: the kernel runs in 3 selected files (5 `tick_once` calls, `audit_mode`
False and a 100 ms budget as found), so the scratch run forced `audit_mode=True` and a relaxed budget through
a plugin kept outside the repo; the repo is unchanged. `test_multi_hero.py` is not in the selection. The
reputation-read lines (46 and 64) had 7 mutants, all killed, so the CONFLICTING survivor list is empty and
the existing tests pin that current behaviour. Survivors cluster in `_appraise_recruitment` (38),
`_appraise_position_swap` (38 of 38, none killed), module-level constants (17), `_appraise_loan` (15) and
`recalibrate_trust` (13, none killed); recorded as findings, none called a defect. Also folded in from the C3
review: the section 3.1 path count is corrected to 63 distinct cited test files. Batch review (section 5)
written with an empty owner-decision slot.
