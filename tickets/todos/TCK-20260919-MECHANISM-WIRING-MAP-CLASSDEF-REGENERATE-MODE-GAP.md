---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260919-MECHANISM-WIRING-MAP-CLASSDEF-REGENERATE-MODE-GAP
phase: open
date: 2026-09-19
tags: [architecture, schema]
---

# TCK-20260919-MECHANISM-WIRING-MAP-CLASSDEF-REGENERATE-MODE-GAP

## Title
`mechanism_wiring_map_classdef.py` is report-only — every state correction touching the Entity
Operating Loop diagram needs a hand-edit, unlike its atlas/capabilities siblings

## Status
OPEN

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
Not yet started.

## Test Summary
Not yet started.

## Files Changed
None yet (this ticket file only).

## Completion Summary
Open. Filed 2026-09-19 per peer review after a hand-edit was needed to close
TCK-20260918-MECHANISM-UNCLASSIFIABLE-DEPENDS-ON-EDGES-RESOLUTION's own `trauma` state correction.
