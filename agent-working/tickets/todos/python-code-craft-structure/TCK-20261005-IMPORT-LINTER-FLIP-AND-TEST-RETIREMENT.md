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
Follow-up to `TCK-20261004-IMPORT-LINTER-ADOPTION`. BLOCKED until a two-week soak from that batch's merge has passed (write the dates at merge: merge date ____, soak ends ____). Then the advisory step becomes blocking, the owner makes it a required check, and the class E tests whose contract is required are retired. Testing condition 1 (#322): a class E test is retired only in or after the PR that makes its replacement contract a required check.

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
- phase19 waits on rpg (`handoff_to_rpg.md`)
- Soak dates are unknown until the adoption batch merges

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
