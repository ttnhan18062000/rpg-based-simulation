---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260919-MECHANISM-WIRING-MAP-CLASSDEF-REGENERATE-MODE-GAP
phase: done
date: 2026-09-19
tags: [architecture, schema]
---

# TCK-20260919-MECHANISM-WIRING-MAP-CLASSDEF-REGENERATE-MODE-GAP

## Title
`mechanism_wiring_map_classdef.py` is report-only — every state correction touching the Entity
Operating Loop diagram needs a hand-edit, unlike its atlas/capabilities siblings

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
Found while closing `TCK-20260918-MECHANISM-UNCLASSIFIABLE-DEPENDS-ON-EDGES-RESOLUTION`'s own
`trauma` state correction (done → orphan, 2026-09-19). `mechanism_atlas_regenerate.py` and
`mechanism_capabilities_regenerate.py` both surgically write their own consumer artifact when the
registry's real state diverges from what's rendered — the state correction just ran clean through
both. `mechanism_wiring_map_classdef.py` (`tools/mechanism_registry/mechanism_wiring_map_
classdef.py`) only *reports* drift for the Entity Operating Loop diagram's own mermaid `classDef`
colouring; there is no equivalent `--fix`/default-write mode, so the `TRM` node needed a manual
`Edit` to the diagram's own mermaid source (moving it from the `class ... live` line to an inline
`:::bug` override) before the drift check would pass.

This is a real parity gap between three structurally similar tools, not a design choice — the
module's own docstring already frames it as "derives... the classDef state colouring," a derivation
the other two tools already perform automatically for their own artifacts.

## Scope
Add a write mode to `mechanism_wiring_map_classdef.py` (default-writes, `--check` reports only,
mirroring `mechanism_atlas_regenerate.py`'s own CLI shape exactly) that surgically edits the
Entity Operating Loop diagram's own node definitions: applies an inline `:::classname` override
when a node's expected classdef disagrees with its current one, removing it from any `class A,B,C
live` line it currently sits in if present. Scope stays to the one diagram this tool already maps
(`OPERATING_LOOP_NODE_TO_MECHANISM_ID`) — no new diagram coverage.

## Out of Scope
- Deriving classdef colouring for the wiring map's other two diagrams (Layer Model, Entity
  Lifecycle Arc) — this tool's own docstring already investigated and rejected a 1:1 mapping for
  those, unrelated to this gap.
- Any change to `mechanism_atlas_regenerate.py`/`mechanism_capabilities_regenerate.py` — both
  already have the write mode this ticket is porting to the third tool.

## Acceptance Criteria
1. Running the tool with no flags writes the diagram file when drift exists, matching
   `mechanism_atlas_regenerate.py`'s own default-write/`--check`-reports-only convention.
2. A real state correction (test fixture or the next real one that lands) requires zero manual
   `Edit` calls to the wiring map HTML.
3. `--check` mode's existing behavior (report-only, exit 1 on drift) is preserved for CI/test use.

## Related Tickets
- `TCK-20260918-MECHANISM-UNCLASSIFIABLE-DEPENDS-ON-EDGES-RESOLUTION` — where this gap was found
  (the `trauma` correction's own hand-edit).

## Related Docs
None new.

## Related Stored Artifacts
None yet — hotfix tier, self-evident scope per the existing `mechanism_atlas_regenerate.py`
precedent to copy the write-mode shape from.

## Related Code Areas
- `tools/mechanism_registry/mechanism_wiring_map_classdef.py`
- `tools/mechanism_registry/mechanism_atlas_regenerate.py` (the pattern to mirror)
- `docs/brainstorm/rpg_simulation_wiring_map.html`

## Assumptions / Open Questions
None — self-evident chore, mirroring an already-proven pattern in the same tool family.

## Implementation Notes
Added `apply_classdef_fix(text, node, expected)`, mirroring `mechanism_atlas_regenerate.py`'s
`apply_diffs()` role: surgically sets one node's classDef, removing it from any `class A,B,C,...
live` line it currently sits in (dropping the whole line if it becomes empty) before applying an
inline `:::expected` override — a node is never left simultaneously inline-overridden AND
class-line-assigned, since mermaid applies the class-line assignment last and would silently
shadow the inline override otherwise. `render(check, wiring_map_path, registry_path)` mirrors
`mechanism_atlas_regenerate.py`'s `render()` exactly: default-write, `--check` reports only and
writes nothing, `--path`/`--registry` overrides for tests (full CLI shape parity, not just the
`--check` flag). `main()` gained matching argparse. Removed `_load_registry()` (dead code once
`render()` inlines its own path-parameterized yaml load).

No live drift existed on `origin/main` at the time of this fix (the earlier `TRM` correction that
motivated this ticket was already hand-applied and committed), so there was nothing real to
regenerate — verified via unit tests with a fully-covered synthetic registry/wiring-map fixture
instead (`_full_coverage_fixture()` in the test file, since `find_drift()`/`render()` iterate the
*entire* real `OPERATING_LOOP_NODE_TO_MECHANISM_ID` mapping regardless of what a minimal fixture
registry defines — a partial fixture reports spurious drift, and a naive write attempt crashes,
for every node the fixture didn't think to cover).

## Test Summary
8 new tests added to `tests/unit/tools/test_mechanism_wiring_map_classdef.py`: 5 for
`apply_classdef_fix()` (insert, replace, remove-from-class-line, drop-now-empty-class-line,
leaves-other-nodes-untouched) and 3 for `render()` (default-write fixes real drift, `--check`
reports and writes nothing, no-drift writes nothing). Confirmed to fail on the pre-fix code
(`ImportError: cannot import name 'apply_classdef_fix'` — the capability itself doesn't exist
pre-fix) via the revert/rerun/restore method, then pass after (AC3). Full suite (15 tests) plus
the sibling `test_mechanism_atlas_regenerate.py`/`test_mechanism_artifact_convergence.py` (28
tests total) pass. `python3 tools/mechanism_registry/mechanism_wiring_map_classdef.py --check`
against the real file: still `OK`, no drift (unaffected, since there was none to begin with).

## Files Changed
- `tools/mechanism_registry/mechanism_wiring_map_classdef.py`
- `tests/unit/tools/test_mechanism_wiring_map_classdef.py`

## Completion Summary
Added the default-write / `--check`-reports-only mode `mechanism_atlas_regenerate.py` and
`mechanism_capabilities_regenerate.py` already had, closing the parity gap: a future Entity
Operating Loop `classDef` correction no longer needs a manual `Edit` to the diagram's mermaid
source. No live drift existed to fix at implementation time; correctness verified via a
full-coverage synthetic fixture instead of the real file.
