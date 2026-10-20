---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20261018-CODEBASE-SELF-LINT
phase: done
date: 2026-10-18
tags: [testing]
---

# TCK-20261018-CODEBASE-SELF-LINT

## Title
`codebase/` meets its own Python code standard: clear the 54 ruff findings and pin it at zero

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
`ruff check codebase` on main (013a9f275) reports 55 findings in the package that enforces the standard, and no gate stops the count growing. Clear 54 of them (behaviour-neutral) and add a pin test. The 55th, D103 in `codebase/structure/import_contracts.py`, is already fixed on the `import-linter-flip` branch and is left alone here.

## Scope
- Files: `codebase/reports/{code_health_impact,codebase_health_baseline,audit_unreachable_code,pr_impact_report,codebase_health_snapshot}.py`, `codebase/gates/{staged_ratchet,sarif_feedback,mypy_gate}.py`.
- Breakdown: 33 D103, 9 ANN001, 3 BLE001, 3 PLR0913, 2 N818, 2 I001, 1 C901, 1 PLR0912, 1 PLR1702.
- Docstrings, annotations, sorted imports; narrowed excepts where the caught set is clear (otherwise `noqa BLE001` with a reason); `# noqa: <rule>  # <reason>` for the complexity rules.
- N818: rename `GateCannotRun` and `HookSkipped` (users listed below).
- New pin `tests/codebase/test_codebase_self_lint.py`.

## Out of Scope
`codebase/structure/import_contracts.py`, `importlinter.toml`, `test.yml`, the Makefile, `tests/static`, `docs/`, any test the flip retires, `tests/tools/`.

## Acceptance Criteria
- `ruff check codebase` reports only the `import_contracts.py` D103 finding on this branch, and zero once the flip is merged.
- No behaviour change: `tests/codebase` passes except the new pin.
- The pin prints the findings on failure.

## Related Tickets
- TCK-20261005-IMPORT-LINTER-FLIP-AND-TEST-RETIREMENT (fixes the 55th finding)

## Related Docs
- `docs/guidelines/python_code_standard.md`

## Related Stored Artifacts
None (hotfix).

## Related Code Areas
`codebase/reports/`, `codebase/gates/`, `codebase/hooks/edit_ratchet_hook.py`, `tests/codebase/`.

## Assumptions / Open Questions
- N818 grep (`git grep -n "GateCannotRun\|HookSkipped"`, whole repo, run 2026-10-18 at 013a9f275): users only in `codebase/gates/mypy_gate.py`, `codebase/gates/staged_ratchet.py`, `codebase/hooks/edit_ratchet_hook.py`, `tests/codebase/test_mypy_gate.py`, `tests/codebase/test_edit_ratchet_hook.py`. Nothing in `tools/`, `.claude/` or live `docs/`. The only other hits are the closed ticket `TCK-20261004-EDIT-RATCHET-HOOK` and its stored artifacts, which are history and stay as written. So both are renamed (`GateCannotRunError`, `HookSkippedError`) rather than noqa'd. `edit_ratchet_hook.py` (also ours) needed the rename too.
- Related tidy (codebase-planner's request): the 8.11 notice line in `docs/plans/codebase_health/handoffs/handoff_to_testing.md` now reads "**Sent 2026-10-19 as issue #672** (PR #671)." instead of the DRAFT line.
- The pin fails on this branch with exactly one finding (`import_contracts.py` D103) until the flip merges.

## Implementation Notes
- BLE001: the two `read_text` excepts in `audit_unreachable_code.py` narrowed to `(OSError, UnicodeError)`; the one in `pr_impact_report.py` is a deliberate per-path isolation, so `noqa BLE001` with that reason.
- PLR0913 x3, C901, PLR0912, PLR1702: `noqa` with a reason, no extraction.
- `affected_runner` typed `Callable[[str, int, Path], str]`; `argv` typed `list[str] | None`.

## Test Summary
After the flip (#671, 309715a72) merged and main was merged in: `ruff check codebase --no-cache` (ruff 0.17.0): All checks passed (0 findings). `tests/codebase` and `tests/static` (venv on PATH, MemoryMax 3G): 607 passed, 2 skipped, including the new pin.

## Files Changed
See `git show --stat` of the batch commit.

## Completion Summary
`ruff check codebase` went from 55 findings to 0: 54 cleared here (33 docstrings, 9 annotations, 3 BLE001, 3 PLR0913, 2 N818 renamed, 2 I001, C901, PLR0912, PLR1702 with reasoned noqa) and the last one (import_contracts.py D103) by the flip (#671). `GateCannotRun` and `HookSkipped` are now `GateCannotRunError` and `HookSkippedError` (no user outside codebase/ and tests/codebase/). The pin `tests/codebase/test_codebase_self_lint.py` keeps the package at zero. Tidy: the 8.11 notice line in `handoff_to_testing.md` now says it was sent as #672.
