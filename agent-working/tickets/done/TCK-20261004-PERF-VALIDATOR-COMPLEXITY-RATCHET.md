---
status: historical
layer: performance
authority: P2
audience: agent
ticket_id: TCK-20261004-PERF-VALIDATOR-COMPLEXITY-RATCHET
phase: done
date: 2026-10-04
tags: [performance]
---

# TCK-20261004-PERF-VALIDATOR-COMPLEXITY-RATCHET

## Title
Bring `ProtocolValidator.validate_result_batch` back under the code-health ratchet that #319 broke

## Status
DONE

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
4. (Added by codebase-planner via perf-planner, 2026-10-04) The PR's Code health summary reads
   "0 new, 0 worse"
5. (Added) Each new helper stays at or under ruff C901 10 and complexipy's default limit, so the helpers
   add no rows of their own
6. (Added) `codebase/baselines/` is untouched: no ceiling or row edits. Lowering ceilings and removing
   gone rows is the codebase flip batch's job

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
- `validate_result_batch` keeps its signature and now only loops and calls three private static helpers, in the original order: `_check_source_traceability` (source packet match, entity and work id match, orphan result), `_check_one_result_per_entity` (Option A uniqueness, system result needs a subsystem) and `_check_one_debt_update_per_subsystem` (PERF-M1-T04 rule). Same checks, same order, same exception type, same messages.
- The `# 4. Success invariant` branch was `if result.status == FAILURE: pass`, a no-op. It is replaced by a comment stating the contract (delta enforcement happens at apply). That left `ResultStatus` unused, so the import is removed (no module in `src/`, `tests/` or `tools/` imports it from here) to avoid a new unused-import finding.
- Complexity before: `validate_result_batch` ruff C901 12 > 10 and complexipy 24 > ceiling 18. After: ruff C901 passes; complexipy `validate_result_batch` 1, `_check_one_debt_update_per_subsystem` 3, `_check_one_result_per_entity` 4, `_check_source_traceability` 6 (`validate_packet_batch` unchanged at 10).
- The two remaining ruff findings on the file (missing module docstring, unsorted imports) are pre-existing on `origin/main` and out of scope ("other debt"). Nothing under `codebase/baselines/` was touched; `make code-health` lists one row as "gone" and one as "improved" for the flip batch.
- The package registry row for `core` has no exemplar modules, so the code follows `docs/guidelines/python_code_standard.md` (F1: one responsibility per function).

## Test Summary
- `uv run ruff check --select C901 src/core/protocol_validator.py`: passed.
- `uv run complexipy src/core/protocol_validator.py`: every function at most 10 (limit 18).
- `uv run make code-health`: "OK: 0 new, 0 worse, 1 improved, 2 gone, 3725 unchanged". The improved row is `LongRunStabilityHarness.execute_run` (47 < ceiling 50) and the gone rows are `validate_result_batch` and a stale `checkpoint.py` I001 row; both are for the flip batch.
- `uv run make typecheck-py`: no output from the baseline filter, i.e. no new mypy error. The target ends in `|| true`, so the exit code alone proves nothing; the empty filtered output is the evidence.
- Validator, T04, worker integrity/harden/determinism, executor determinism and concurrency parity tests (the files named in the ticket): all pass, unchanged.
- `tests/codebase` run with the system Python gave 46 failures and 3 errors because that interpreter lacks `complexipy`, `mypy_baseline`, `ast-grep` and `prek`; none is in a file this change touches. Re-run under `uv run` on a subset (staged ratchet, edit hook, ast-grep rules, mypy gate, impact): 84 passed, 2 failed. The 2 failures (`test_real_path_pipeline_includes_kernel_as_dependent` and `..._kernel_visible_in_formatted_output_not_just_internal_data`, in `test_code_health_impact.py`) fail identically with my change stashed, so they are pre-existing and unrelated.
- AC3/AC4 (the PR's Code health job summary) can only be checked on the PR; perf-planner owns the PR.

## Files Changed
- `src/core/protocol_validator.py`
- `docs/REGISTRY.yaml` (regenerated at close)

## Completion Summary
`validate_result_batch` is split into three small private helpers with no behaviour change, so ruff C901 passes and complexipy is at most 10 for every function. `make code-health` reports 0 new, 0 worse. The PR's Code health summary (ACs 3 and 4) is checked by perf-planner on the PR.
