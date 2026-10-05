---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261005-IMPORT-LINTER-FLIP-AND-TEST-RETIREMENT
phase: blocked
date: 2026-10-05
tags: [architecture, delivery]
---

# TCK-20261005-IMPORT-LINTER-FLIP-AND-TEST-RETIREMENT

## Title
Make the import-linter step blocking and required, then retire the class E tests whose contract is required

## Status
BLOCKED

## Tier
standard

## Type
chore

## Priority
P3

## Request Summary
Follow-up to `TCK-20261004-IMPORT-LINTER-ADOPTION`. BLOCKED until a two-week soak from that batch's merge has passed (import-linter adoption merged 2026-10-05 as PR #351, squash `e9585eb02` at 2026-10-05T13:40:06Z; soak ends 2026-10-19T13:40Z; earliest flip 2026-10-19, after the gates-flip PR #329 merges on or after 2026-10-18). Then the advisory step becomes blocking, the owner makes it a required check, and the class E tests whose contract is required are retired. Testing condition 1 (#322): a class E test is retired only in or after the PR that makes its replacement contract a required check.

## Scope
- Soak review (runs, broken-contract runs, false positives, stale `ignore_imports` alerts) in a soak review doc, as for the gates flip
- Step becomes blocking; the owner adds the check as required on `main` (never before `main` has produced the check name; ruleset change and merge in one sitting)
- Retire the class E tests whose contract is required, with the per-test parity table re-shown; the phase19 hot-path test waits on rpg's decision about `kernel.py`'s function-local imports
- Update the testing handoff and the roadmap

## Out of Scope
- Any file under `src/`
- The 42 rules that stay tests
- Edits to the `or True` assert at `tests/unit/observability/test_decision_trace.py:376` (testing's)

## Acceptance Criteria
- [ ] Soak review finalized; no false-positive class open
- [ ] Owner's yes to the required check recorded (date, who)
- [ ] Each retired test's replacement contract is required in the same or an earlier PR; parity table re-shown
- [ ] `git diff --stat` lists no path under `src/`

## Related Tickets
- TCK-20261004-IMPORT-LINTER-ADOPTION
- TCK-20261004-IMPORT-LINTER-EVALUATION

## Related Docs
- docs/plans/codebase_health/import_linter_adoption_ticket_brief.md
- docs/plans/codebase_health/import_linter_evaluation.md

## Related Stored Artifacts
None.

## Related Code Areas
- tests/architecture/
- codebase/structure/
- pyproject.toml

## Assumptions / Open Questions
- Testing's agreement and four conditions (#322 comment, 2026-10-04; copied from `TCK-20261004-IMPORT-LINTER-ADOPTION`, where they are recorded). They govern this ticket:
  1. a class E test is retired only in or after the PR that makes its replacement contract a required check;
  2. parity is shown per retired test (the injected violation, and the contract failing on it);
  3. phase19 `test_hot_path_does_not_import_heavy_analyzers` is an expectation change, not a retirement: the engine/observability owner first decides whether `kernel.py`'s function-local imports at 149/304/305/316/1241 are allowed (allowlist with a reason) or violations (an engine ticket);
  4. the blind spots and the stale allowlist are covered by contracts. The `or True` assert (`tests/unit/observability/test_decision_trace.py:376`) is testing's, not one of the eight.
- phase19 waits on rpg (`handoff_to_rpg.md`)
- Soak dates are unknown until the adoption batch merges

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
