---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260930-CORE-RPG-TEST-BASELINE-POST-REPAIR
phase: done
date: 2026-09-30
tags: [testing]
---

# TCK-20260930-CORE-RPG-TEST-BASELINE-POST-REPAIR

## Title
Post-repair core-RPG test baseline: the same report before and after batch 1, differences explained, unknowns listed

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
Epic A criterion A.6. Generate the core-RPG test report (`TCK-20260930-CORE-RPG-TEST-REPORT-V0`) at the
pre-repair SHA `35806b1ed` and at the post-repair SHA `7e250faf7` from real local JUnit (and, for post-repair,
a documented local coverage run), then record the differences with an explanation for each, plus the remaining
unknowns.

## Scope
- Two local full fast-suite runs (`pytest tests/ -m "not slow and not extra_slow"`) with `--junitxml`; the
  post-repair run also under `coverage run --branch --source=src`. Runs are sequential, in disposable worktrees.
- Two reports from the producer, one per SHA (`--repo-root` at each worktree).
- One baseline document: `docs/testing/core_rpg_test_baseline_2026-09-30.md`.

## Out of Scope
- Fixing the pre-existing combined-run failures, the tracked-file writers, or any gate; a CI job.
- Claiming order dependence is gone beyond the verified set.

## Acceptance Criteria
1. The baseline document lists every difference between the two reports with an explanation, and states which were caused by batch 1 and which are input differences (e.g. coverage supplied only post-repair).
2. It lists remaining unknowns: the 11 pre-existing combined-run failures (with node ids and the unverified interference inference), order dependence outside the verified set, the done-checker tracked-file writers (`TCK-20260929-DONE-CHECKER-TESTS-WRITE-TRACKED-FILES`), and `tests/mutation/baselines/` as an Epic B taxonomy input.
3. Every figure cites its input artifact (sha256) and SHA; runtimes are recorded.

## Related Tickets
- `TCK-20260929-EPIC-TEST-BASELINE-RELIABILITY`, `TCK-20260930-CORE-RPG-TEST-REPORT-V0`

## Related Docs
- `docs/plans/test_architecture/roadmap.md` §4.2, §4.7

## Related Stored Artifacts
`stored_artifacts/TCK-20260930-CORE-RPG-TEST-BASELINE-POST-REPAIR/` (after close)

## Related Code Areas
`tools/test_architecture/core_rpg_report.py` (read-only use).

## Assumptions / Open Questions
- The post-repair SHA is batch 1's PR head (`7e250faf7`), not merged `main`; it is recorded as such.

## Implementation Notes
See the staging plan.

## Test Summary
Two real full fast-suite runs (pre 35806b1ed: 11641 passed, 17 failed, 1 error; post 7e250faf7 under coverage: 11649 passed, 14 failed, 1 error). Both reports regenerate byte-identically. The 4 failures that appear only under coverage pass without it (4 passed in 147 s). The 4 not-run candidate files (4 tests) were confirmed fully deselected by the fast marker filter.

## Files Changed
`docs/testing/core_rpg_test_baseline_2026-09-30.md`.

## Completion Summary
Baseline written at `docs/testing/core_rpg_test_baseline_2026-09-30.md`. Batch 1 removed exactly the 7 progression failures and no others; the A.4 tracked-file write is gone at full-suite scale. 4 failures appear only under coverage (3 resource-budget timeouts and one timing assertion) and pass without it. 11 pre-existing combined-run failures are carried over unchanged and listed as unknowns, with the done-checker tracked-file writers and `tests/mutation/baselines/` (an Epic B taxonomy input). Gate note: the bare done_checker_static CLI reports [precheck] and docs_to_update_coverage FAILs after closure; these are known false positives tracked in TCK-20260929-DONE-CHECKER-POST-CLOSURE-FALSE-FAILS. `--part finalize` is the correct post-closure check.
