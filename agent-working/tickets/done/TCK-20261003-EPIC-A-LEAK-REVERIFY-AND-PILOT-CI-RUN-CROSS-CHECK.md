---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261003-EPIC-A-LEAK-REVERIFY-AND-PILOT-CI-RUN-CROSS-CHECK
phase: done
date: 2026-10-03
tags: [testing]
---

# TCK-20261003-EPIC-A-LEAK-REVERIFY-AND-PILOT-CI-RUN-CROSS-CHECK

## Title
Re-verify the Epic A known-leak fix in scope at the current main, check whether the done-checker tests write a tracked file, and cross-check the pilot report's cited CI run id

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P3

## Request Summary
Optional scope shipped with the test-architecture closure (approved by test-architecture-reviewer 2026-10-03). Turn the audit's "not re-run" caveat on Epic A criterion 3 and the "not cross-checked" caveat on pilot criterion D1 into evidence (or a real finding), and answer, verify-only, whether `tests/tools/test_done_checker_static.py` writes a tracked file in a clean checkout.

## Scope
- (a) Re-run, at the merge of `origin/main` 243e798ad, scoped: each of the 8 polluter files followed by the progression directory; combined `tests/unit/content tests/unit/core tests/unit/domains/progression`; `tests/unit/domains` alone; a seeded random-order run of the affected set, seeds 1-10, with the plugin committed this time; a positive control with the fix disabled in a scratch copy. A failure would be filed as a finding, not fixed.
- (b) Cross-check the CI run id the pilot report cites (36810173881, PR #271) against the Actions API.
- (c) Verify only: run `tests/tools/test_done_checker_static.py` in a clean worktree and read `git status --porcelain`. Building a guard is not in scope.
- Record the results in `docs/testing/core_rpg_test_baseline_2026-09-30.md`, the pilot report and the INDEX audit rows.

## Out of Scope
- Re-running the whole fast suite, widening the verified set, fixing any failure, building the tracked-file guard, any edit to `tests/tools/test_done_checker_static.py` (another team's file).

## Acceptance Criteria
1. Every re-run result and the positive control are recorded with the SHA, the Python version and the exact command; the shuffle plugin is committed.
2. The full fast suite is stated as not re-run, and the 11 other combined-run failures as standing.
3. The CI run id is confirmed or contradicted from the API, with the head SHA and job outcomes.
4. The tracked-file check is answered yes or no with the exact `git status --porcelain` result.

## Related Tickets
TCK-20260929-CATALOG-REGISTRY-TEST-LEAK, TCK-20260929-EPIC-TEST-BASELINE-RELIABILITY, TCK-20260929-DONE-CHECKER-TESTS-WRITE-TRACKED-FILES, TCK-20261003-EPIC-B-ROWS-279-288-AND-CLOSURE-READINESS-AUDIT

## Related Docs
docs/testing/core_rpg_test_baseline_2026-09-30.md, docs/testing/core_rpg_test_pilot_2026-09-30.md

## Related Stored Artifacts
agent-working/stored_artifacts/TCK-20261003-EPIC-A-LEAK-REVERIFY-AND-PILOT-CI-RUN-CROSS-CHECK/seeded_shuffle_plugin.py

## Related Code Areas
- tests/conftest.py (read only)
- tests/unit/domains/progression, tests/unit/core, tests/unit/content (run only)

## Assumptions / Open Questions
- Route: hand-orchestrated hotfix.
- The worktree is the merge of `origin/main` 243e798ad with this branch's docs/ticket edits; no tracked `src/` or `tests/` file differs from that commit.

## Implementation Notes
Results: 8 of 8 polluter-then-progression runs pass; combined content + core + progression 532 passed; `tests/unit/domains` alone 1058 passed; seeds 1-10 each 78 passed; the positive control (reset disabled in a scratch copy of `c0980e27a`) fails 11 and 7 tests. Run 36810173881 is a `Tests` run for head `369acbac3b2f1b35f094c5ab913df965e0fb05c0` with `Scenario lane` success (51 s) and `Perf / cert / arena` skipped; the workflow as a whole failed on another job, as the pilot report already states. `tests/tools/test_done_checker_static.py`: 164 passed and no tracked-file write (only the session's own monitoring shard changed).

## Test Summary
All runs are scoped pytest runs listed above; no new test was added. The shuffle plugin is evidence, not a project tool.

## Files Changed
docs/testing/core_rpg_test_baseline_2026-09-30.md; docs/testing/core_rpg_test_pilot_2026-09-30.md; agent-working/tickets/done/test-architecture/INDEX.md; agent-working/stored_artifacts/TCK-20261003-EPIC-A-LEAK-REVERIFY-AND-PILOT-CI-RUN-CROSS-CHECK/seeded_shuffle_plugin.py; docs/REGISTRY.yaml.

## Completion Summary
The known-leak fix still holds in scope at 243e798ad (polluters, combined, `domains` alone and ten shuffled orders all pass, and the control shows the check can see the leak); the full fast suite was not re-run and unknowns 1 and 2 stand. The pilot's cited CI run is real and matches its record. The done-checker tests did not write a tracked file when run alone, so that attribution is not reproduced; no finding was filed because nothing was written.
