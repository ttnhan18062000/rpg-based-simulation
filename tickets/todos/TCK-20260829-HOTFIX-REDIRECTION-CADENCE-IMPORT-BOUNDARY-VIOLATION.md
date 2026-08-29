---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260829-HOTFIX-REDIRECTION-CADENCE-IMPORT-BOUNDARY-VIOLATION
phase: open
date: 2026-08-29
tags: [engine, architecture]
---

# TCK-20260829-HOTFIX-REDIRECTION-CADENCE-IMPORT-BOUNDARY-VIOLATION

## Title
`src/systems/strategic_systems/redirection.py` gained a module-level `systems -> engine` import
not in the pinned exceptions list, breaking `test_systems_do_not_import_engine_outside_pinned_exceptions`

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
Found live during a post-batch double-check review of the `m1-quick-wins` batch (real, direct
`pytest` verification, not trusted from any prior self-report).
`TCK-20260824-TOWN-CENTER-POINTER-FIX` (commit `94e96218`) added `from src.engine.cadence import
SystemCadence` at `src/systems/strategic_systems/redirection.py:11` (module level, used for the
`enforce(..., cadence: SystemCadence = None)` parameter's default-instantiation
`cadence = cadence or SystemCadence()` inside the function body) to give `StrategicRedirectionSystem`
an injectable cadence. This is a genuine, real `systems -> engine` import-boundary violation:
`tests/architecture/test_phase18_import_boundaries.py::test_systems_do_not_import_engine_outside_pinned_exceptions`
fails for real (confirmed directly, not assumed -- a naive `pytest` invocation from outside the
worktree can spuriously report this test PASSING because `_iter_py_files`'s relative `src/systems`
path resolves against whatever `cwd` pytest was launched from, silently scanning a different
branch's checkout if run from the wrong directory; always run this test with cwd set to this
worktree). This file already has ONE pinned exception for the same module,
`("src/systems/strategic_systems/redirection.py", 23): ("src.engine.cadence", ("should_run",))`
-- a function-scoped import inside `enforce()`'s own body, not a module-level one. The new
`SystemCadence` import was added at module scope instead of following that same already-accepted,
already-pinned function-scoped pattern for the exact same module.

This slipped past `TCK-20260824-TOWN-CENTER-POINTER-FIX`'s own Test phase because that ticket's
scoped pytest command never included `tests/architecture/` -- its own new/modified files were all
under `src/{worldbuilding,systems/strategic_systems,systems/world_systems}/` and `tests/{unit,integration}/`,
not `tests/architecture/`, so the structural test-scope-coverage backstop had no reason to flag it.

## Scope
- **Recommended fix (restructure, not pin)**: since `src/systems/strategic_systems/redirection.py`
  already has `from __future__ import annotations` (line 1, confirmed), the `cadence: SystemCadence`
  parameter annotation is never evaluated at runtime regardless of whether `SystemCadence` is a real
  importable name at module scope -- move the type name into the existing `if TYPE_CHECKING:` block
  (for IDE/mypy support only) and move the real runtime import into the SAME existing function-scoped
  import statement already present inside `enforce()` for `should_run` (i.e.
  `from src.engine.cadence import SystemCadence, should_run`, replacing the current two separate
  imports with one). This keeps the file's real behavior byte-identical, avoids adding a second
  pinned exception, and follows the file's own already-established pattern instead of diverging from
  it -- confirm this compiles and the `enforce()` default-cadence-instantiation behavior is unchanged
  by a real test run before/after.
- **Alternative (only if the restructure proves non-trivial for some reason not yet found)**: add a
  second pinned exception entry for `("src/systems/strategic_systems/redirection.py", 11):
  ("src.engine.cadence", ("SystemCadence",))` in both
  `tests/architecture/test_phase18_import_boundaries.py`'s `_SYSTEMS_ENGINE_PINNED` dict and
  `docs/audits/D14_coupling_depth.md`, with a real rationale -- do not silently choose this path
  over the restructure without documenting why the restructure wasn't viable.
- Confirm `tests/architecture/test_phase18_import_boundaries.py::test_systems_do_not_import_engine_outside_pinned_exceptions`
  passes for real afterward (run with cwd set to the repo worktree, not the main checkout).

## Out of Scope
- Any other pinned-exception entries in `_SYSTEMS_ENGINE_PINNED` -- this ticket is scoped to the
  one new violation found, not a general audit of all 13+ existing pins
- `TCK-20260824-TOWN-CENTER-POINTER-FIX`'s own broader scope -- already closed, not reopened by
  this ticket; this is a narrow, self-contained follow-up

## Acceptance Criteria
- [ ] `test_systems_do_not_import_engine_outside_pinned_exceptions` passes for real (verified with
      cwd correctly set to the worktree, not a spurious pass from scanning the wrong branch)
- [ ] Either the restructure lands (preferred, no new pinned exception added) or a new pinned
      exception is added to both the test file and `docs/audits/D14_coupling_depth.md` with a
      documented rationale for why the restructure wasn't chosen
- [ ] `StrategicRedirectionSystem.enforce()`'s real behavior (default-cadence instantiation) is
      unchanged, confirmed by a real test run

## Related Tickets
- TCK-20260824-TOWN-CENTER-POINTER-FIX (where this import was introduced)

## Related Docs
- docs/audits/D14_coupling_depth.md

## Related Stored Artifacts
None.

## Related Code Areas
- src/systems/strategic_systems/redirection.py
- tests/architecture/test_phase18_import_boundaries.py

## Assumptions / Open Questions
None -- self-evident intent, minimal targeted fix (a local-import restructure, or a documented pin
as a fallback).

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
