---
status: active
layer: performance
authority: P2
audience: agent
ticket_id: TCK-20261004-PERF-VALIDATOR-COMPLEXITY-RATCHET
phase: open
date: 2026-10-04
tags: [performance]
---

# TCK-20261004-PERF-VALIDATOR-COMPLEXITY-RATCHET

## Title
Bring `ProtocolValidator.validate_result_batch` back under the code-health ratchet that #319 broke

## Status
OPEN

## Tier
hotfix

## Type
refactor

## Priority
P1

## Request Summary
PR #319 (`TCK-20261004-PERF-M1-VALIDATOR-ONE-SYSTEM-RESULT-PER-SUBSYSTEM`) added a per-subsystem
duplicate check to `validate_result_batch` (`src/core/protocol_validator.py`). The advisory "Code
health" job on #319 (run 37187996740) reported "FAIL: 1 new, 1 worse". perf-planner merged on a
green check colour without reading the job summary. perf-planner reproduced both findings on
`origin/main` `cf7cbcb08`:
- NEW: ruff C901, `validate_result_batch` too complex (12 > 10);
- WORSE: complexipy `ProtocolValidator::validate_result_batch`, 24 > ceiling 18.

The code-health gates become blocking for `src/` PRs merging on or after 2026-10-18
(codebase-planner). The ratchet reads all of `src/`, so these two findings would fail every
domain's PR. The owner of the change fixes it (codebase-planner's option (a)).

## Scope
- Refactor `validate_result_batch` into small helpers (for example one private method per check:
  source traceability, entity uniqueness, system-result subsystem, debt-subsystem uniqueness,
  failure invariant), so that ruff C901 ≤ 10 and complexipy ≤ 18. No behaviour change: same checks,
  same order, same exception types and messages
- `make code-health` shows no new or worse finding for `src/core/protocol_validator.py`. Confirm
  with `uv run ruff check --select C901 src/core/protocol_validator.py` and
  `uv run complexipy src/core/protocol_validator.py`
- `make typecheck-py` adds no new mypy error

## Out of Scope
- Any change to what the validator accepts or rejects
- Other files' code-health debt

## Acceptance Criteria
1. ruff C901 passes and complexipy is ≤ 18 for `validate_result_batch` and every new helper
2. All existing validator tests and the T04 suite pass unchanged:
   `tests/unit/core/test_protocol_validator_system_results.py`,
   `tests/integration/kernel/test_tied_worker_result_order.py`, and the worker integrity, harden and
   determinism tests
3. Before merge, the "Code health" job summary on the PR (not the check colour) shows no new or
   worse finding

## Related Tickets
- `TCK-20261004-PERF-M1-VALIDATOR-ONE-SYSTEM-RESULT-PER-SUBSYSTEM` (introduced the debt)

## Related Docs
- `docs/guidelines/python_code_standard.md`
- `docs/plans/codebase_health/python_code_craft_gates_flip_ticket_brief.md`

## Related Stored Artifacts
- none

## Related Code Areas
- `src/core/protocol_validator.py` (edit allowed under the partial lift)

## Assumptions / Open Questions
- Must merge before 2026-10-18

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
