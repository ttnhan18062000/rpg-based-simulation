---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260829-HOTFIX-INTELLIGENCE-CADENCE-PIN-LINENO-DRIFT
phase: done
date: 2026-08-29
tags: [engine, architecture]
---

# TCK-20260829-HOTFIX-INTELLIGENCE-CADENCE-PIN-LINENO-DRIFT

## Title
`src/systems/strategic_systems/intelligence.py`'s 9 pinned `systems -> engine` import exceptions
in `_SYSTEMS_ENGINE_PINNED` have stale `(file, lineno)` keys, making
`test_systems_do_not_import_engine_outside_pinned_exceptions` fail for real

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
Found live while implementing `TCK-20260829-HOTFIX-REDIRECTION-CADENCE-IMPORT-BOUNDARY-VIOLATION`
(real, direct `pytest` verification, cwd correctly set to the worktree per that ticket's own
documented cwd-sensitivity warning -- not a spurious pass/fail).

After fixing that ticket's own target (`src/systems/strategic_systems/redirection.py`'s new,
unpinned module-level `systems -> engine` import), a real re-run of
`tests/architecture/test_phase18_import_boundaries.py::test_systems_do_not_import_engine_outside_pinned_exceptions`
still FAILS -- now on a completely different file:

```
AssertionError: src/systems/strategic_systems/intelligence.py:70 imports from src.engine
(src.engine.policy) but is not one of the 13 pinned grandfathered exceptions
```

Root cause: `_SYSTEMS_ENGINE_PINNED` in that test file pins 9 import sites in
`intelligence.py` by `(file, lineno)`:

| Pinned lineno (stale) | Actual current lineno | Import |
|---|---|---|
| 69 | 70 | `src.engine.policy` (`GovernorPolicy`) |
| 75 | 76 | `src.engine.spatial_query` (`SpatialQueryService`) |
| 78 | 79 | `src.engine.cadence` (`SystemCadence`, `should_run`) |
| 83 | 84 | `src.engine.domain_logic` (`SimulationDomainLogic`) |
| 664 | 663 | `src.engine.cadence` (`should_run`) |
| 829 | 828 | `src.engine.domain_logic` (`SimulationDomainLogic`) |
| 833 | 832 | `src.engine.cadence` (`SystemCadence as DefaultCadence`, `should_run`) |
| 905 | 904 | `src.engine.cadence` (`SystemCadence as DefaultCadence`, `should_run`) |
| 958 | 957 | `src.engine.cognition` (`AppraisalSystem`) |

None of these 9 import *targets* (module + imported names) changed -- only their line numbers
drifted, so this is purely a stale-metadata bug, not a real new coupling violation.

Confirmed via `git show 94e96218 -- src/systems/strategic_systems/intelligence.py`: commit
`94e96218` (`TCK-20260824-TOWN-CENTER-POINTER-FIX`) added an import line near the top of
`intelligence.py` and made a net-line-count change to its routine-blocker pass mid-file, shifting
every subsequent line number -- without updating `_SYSTEMS_ENGINE_PINNED`'s keys for this file.
That same commit is also what introduced `TCK-20260829-HOTFIX-REDIRECTION-CADENCE-IMPORT-BOUNDARY-VIOLATION`'s
own violation in `redirection.py`.

This drift was invisible to both `TCK-20260824-TOWN-CENTER-POINTER-FIX`'s own Test phase (never
touched `tests/architecture/`) and to `TCK-20260829-HOTFIX-REDIRECTION-CADENCE-IMPORT-BOUNDARY-VIOLATION`'s
own investigation, because
`test_systems_do_not_import_engine_outside_pinned_exceptions`'s single `assert` inside a nested
loop raises on the FIRST violation found per file, and `os.walk`'s file-iteration order happened to
reach `redirection.py`'s (then-unpinned) violation before ever reaching `intelligence.py`'s stale
pins -- so only one failure was ever visible at a time.

## Scope
- Update all 9 `("src/systems/strategic_systems/intelligence.py", <lineno>)` keys in
  `tests/architecture/test_phase18_import_boundaries.py`'s `_SYSTEMS_ENGINE_PINNED` dict to their
  actual current line numbers (see table above) -- same mechanical fix pattern already applied to
  `redirection.py`'s own pin entry by `TCK-20260829-HOTFIX-REDIRECTION-CADENCE-IMPORT-BOUNDARY-VIOLATION`.
- Update the corresponding table row in `docs/audits/D14_coupling_depth.md`
  (`systems/strategic_systems/intelligence.py` row's `Lines` column) to match.
- No source-code change to `intelligence.py` itself -- this is a test/doc metadata correction only,
  not a behavior change.
- Confirm `test_systems_do_not_import_engine_outside_pinned_exceptions` passes for real afterward
  (cwd set to the repo worktree, per the same cwd-sensitivity note documented in the sibling
  ticket).

## Out of Scope
- Any change to `intelligence.py`'s actual import behavior or the other 3 files' pins
  (`detour.py`, `market.py`, `routine.py`) -- their pins were not found stale by this
  investigation.
- Re-litigating whether these 9 imports should still be pinned exceptions at all (a broader
  coupling-depth audit, not this ticket's job).

## Acceptance Criteria
- [x] `test_systems_do_not_import_engine_outside_pinned_exceptions` passes for real, verified with
      cwd set to the worktree
- [x] All 9 stale `intelligence.py` pin keys corrected in both
      `tests/architecture/test_phase18_import_boundaries.py` and `docs/audits/D14_coupling_depth.md`
- [x] No behavior change to `intelligence.py` itself

## Related Tickets
- TCK-20260829-HOTFIX-REDIRECTION-CADENCE-IMPORT-BOUNDARY-VIOLATION (where this was discovered;
  blocked on this ticket landing first, or on an explicit scope-widening decision)
- TCK-20260824-TOWN-CENTER-POINTER-FIX (the commit that caused the line-number drift)

## Related Docs
- docs/audits/D14_coupling_depth.md

## Related Stored Artifacts
None.

## Related Code Areas
- src/systems/strategic_systems/intelligence.py
- tests/architecture/test_phase18_import_boundaries.py

## Assumptions / Open Questions
None -- self-evident intent, minimal targeted metadata fix, same pattern as the sibling ticket's
own already-completed pin correction.

## Implementation Notes
Independently re-derived all 9 `("src/systems/strategic_systems/intelligence.py", <lineno>)` keys
in `_SYSTEMS_ENGINE_PINNED` by grepping the real file for every `from src.engine...` import
(`grep -n "from src\.engine" src/systems/strategic_systems/intelligence.py`), which returned 10
hits. One (line 62, `from src.engine.cadence import SystemCadence`) sits inside an
`if TYPE_CHECKING:` block (confirmed by reading lines 55-89) and is correctly excluded by the
test's own `_type_checking_lines()` skip-set, so it is not a 10th pinned entry. The remaining 9
hits — lines 70, 76, 79, 84, 663, 828, 832, 904, 957 — match the ticket's own table exactly
(one line lower than each stale pin, consistent with commit `94e96218` adding a single net new
line near the top of the file). Import module + imported-name set at each of the 9 sites was also
confirmed unchanged from the stale pin's recorded target (only the lineno key needed correction);
`_names_as_written()` sorts the imported-name tuple, so the on-disk source order of
`should_run, SystemCadence` vs. the pin's `("SystemCadence", "should_run")` is not itself a
mismatch. Updated all 9 keys in `_SYSTEMS_ENGINE_PINNED`
(`tests/architecture/test_phase18_import_boundaries.py`) and the corresponding `Lines` column in
`docs/audits/D14_coupling_depth.md`'s `systems/strategic_systems/intelligence.py` row. No change
to `src/systems/strategic_systems/intelligence.py` itself. Built on top of the already-uncommitted
`redirection.py` pin fix (line 25) from the sibling ticket
`TCK-20260829-HOTFIX-REDIRECTION-CADENCE-IMPORT-BOUNDARY-VIOLATION` in both shared files without
reverting or altering that ticket's own changes.

## Test Summary
`/home/u24desktop/Working/rpg-based-simulation/.venv/bin/python3 -m pytest tests/architecture/ -v`
run with cwd explicitly set to this worktree (`.claude/worktrees/docs-build-lastupdate-metadata-overhead`):
70 passed, 0 failed. Specifically confirmed
`tests/architecture/test_phase18_import_boundaries.py::test_systems_do_not_import_engine_outside_pinned_exceptions`
PASSED (previously failing on `intelligence.py:70` per this ticket's Request Summary). No new
tests required — this is a metadata-only correction to an existing, already-passing-when-accurate
architecture guard test; no new behavior to cover.

## Files Changed
- `tests/architecture/test_phase18_import_boundaries.py` — corrected all 9
  `intelligence.py` pin linenos in `_SYSTEMS_ENGINE_PINNED`
- `docs/audits/D14_coupling_depth.md` — corrected the `intelligence.py` row's `Lines` column to match

## Completion Summary
Fixed 9 stale `(file, lineno)` pin keys for `intelligence.py` in
`_SYSTEMS_ENGINE_PINNED`, all drifted by the same net-line-count shift as commit `94e96218`
(`TCK-20260824-TOWN-CENTER-POINTER-FIX`). Each of the 9 was independently re-verified against the
real file (not copied blind from the ticket's own table, though it matched exactly). No import
targets changed, no source-code behavior change. `test_systems_do_not_import_engine_outside_pinned_exceptions`
now passes for real. `docs/audits/D14_coupling_depth.md`'s corresponding row updated to match.
