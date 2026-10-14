---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261012-MYPY-DEV-PIN
phase: done
date: 2026-10-12
tags: [delivery]
---

# TCK-20261012-MYPY-DEV-PIN

## Title
The dev group pins mypy exactly, equal to the version uv.lock resolves

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P3

## Request Summary
`pyproject.toml`'s dev group listed `"mypy"` unpinned, so a new mypy release could add errors and move the mypy baseline without a code change (the code-health tools are already pinned exactly for the same reason). Pin `mypy==2.1.0`, the version `uv.lock` already resolves. Moved here from the import-linter flip batch (T2) by lead-planner and the owner. `pyproject.toml` and `uv.lock` are lead-owned; lead approved the edit, and the single `uv.lock` metadata line, as path owner.

## Scope
- `pyproject.toml` dev group: `"mypy==2.1.0"` plus a short pin comment.
- `uv.lock`: only the regenerated `requires-dev` specifier line, produced by `uv lock`.
- `tests/codebase/test_typecheck_gate_configured.py`: the assertion that named the bare `"mypy"` line now asserts an exact pin.
- Carried from the stray launcher worktree (cfad712cf) at lead's decision: the two 2026-W41 monitoring shard changes.

## Out of Scope
- Bumping mypy; any baseline change.

## Acceptance Criteria
1. `uv lock --check` passes; the `uv.lock` diff is exactly one line (the specifier), 127 packages, mypy 2.1.0, no hash change.
2. `git diff origin/main -- codebase/baselines/` is empty.
3. tests/static and tests/codebase pass (apart from the environmental snapshot-budget failure present on clean main).

## Related Tickets
- TCK-20261005-IMPORT-LINTER-FLIP-AND-TEST-RETIREMENT (the pin was its T2; now landed standalone)

## Related Docs
- docs/plans/codebase_health/mypy_pin_and_search_shared_model_brief.md

## Related Stored Artifacts
None (hotfix).

## Related Code Areas
- pyproject.toml
- uv.lock
- tests/codebase/test_typecheck_gate_configured.py

## Assumptions / Open Questions
The brief expected `uv.lock` to stay byte-identical; it records the dev-group specifier, so one metadata line changes. Lead approved that (2026-10-12).

## Implementation Notes
Lock generated with `uv lock`, not by hand. The lock diff: `{ name = "mypy" },` becomes `{ name = "mypy", specifier = "==2.1.0" },`.

## Test Summary
`uv lock --check` passes (127 packages). `tests/static` and `tests/codebase`: 562 passed plus the fix below; the two failures were `test_codebase_health_snapshot::test_make_target_runs_successfully_end_to_end` (60 s budget, environmental, identical on clean main) and `test_typecheck_gate_configured::test_typecheck_job_gets_mypy_from_the_lockfile_not_a_separate_pip_install`, which asserted the bare `"mypy"` line; it now asserts an exact pin (red on the unpinned pyproject, green with the pin; 7 passed in that file).

## Files Changed
- pyproject.toml
- uv.lock (one line)
- tests/codebase/test_typecheck_gate_configured.py
- docs/plans/codebase_health/mypy_pin_and_search_shared_model_brief.md
- agent-working/agent-monitoring/data/2026-W41/ (two shard changes carried from the stray worktree)

## Completion Summary
mypy is pinned `==2.1.0` in the dev group and the lock's specifier line follows; resolution unchanged. The one test that named the bare line now requires an exact pin.
