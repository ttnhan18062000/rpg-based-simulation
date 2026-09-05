---
status: active
layer: performance
authority: P1
audience: agent
ticket_id: TCK-20260905-SUB-327-FABRICATED-CITATION-FIX
phase: open
date: 2026-09-05
tags: [performance]
---

# TCK-20260905-SUB-327-FABRICATED-CITATION-FIX

## Title
Fix SUB-327's fabricated citation (docs/compliance/checklist.md) and correct the underlying parity entry

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
`docs/plans/rpg_design_roadmap/rpg_spatial_index_hardening_plan.md` (2026-09-02 hardening backlog
item 2) found that `SUB-327` (spatial index entity-move claim) carries a **fabricated citation**: a
nonexistent file path from a different contributor's local machine, a nonexistent method name, and a
nonexistent test file. Confirmed via direct code read this citation is still live and unfixed as of
2026-09-05 in `docs/compliance/checklist.md`, and the underlying `docs/parity_ledger/substrate.yaml`
entry is a generic legacy-stub placeholder (`v2_evidence: "Implementation proven via exhaustive
checklist audit Phase 1-11"`, `test_path: null`) that never got a real citation either.

## Scope
- `docs/compliance/checklist.md`'s `SUB-327` line (`## Z13. Spatial index and map authority law`):
  replace the fabricated `src/world/spatial.py:15` / `SpatialIndex.move` /
  `tests/unit/world/test_spatial_index.py` citation with the real architecture.
- `docs/parity_ledger/substrate.yaml`'s `SUB-327` entry: replace the generic placeholder
  `v2_evidence`/`test_path` with a real, verified citation, via `tools/parity_ledger_writer.py`
  only (never a raw YAML edit).
- Correct the entry's own *claim*, not just its citation: the real architecture is
  rebuild-from-scratch-when-dirty (`SpatialGrid.__init__`, `src/engine/spatial.py:8`), not an atomic
  `.move()` between cells — `SpatialIndex` (`src/engine/world_index.py:78`) is in fact a **frozen**
  dataclass with no mutator method at all. The original claim ("can move entity/object between
  cells... atomically") misdescribes the design, not just the file path.

## Out of Scope
- Any other `docs/compliance/checklist.md` entry — this ticket fixes only `SUB-327`. Whether other
  entries in `## Z13` (or elsewhere) share the same stale-path root cause is unconfirmed
  (explicitly disclosed as unverified by the investigation that found this one).
- The spatial-index hardening plan's other 4 scope items (unrelated corrections to the same plan doc).

## Acceptance Criteria
- [x] `docs/compliance/checklist.md`'s `SUB-327` line cites real, existing paths only.
- [x] `docs/parity_ledger/substrate.yaml`'s `SUB-327` entry updated via `write_entry()`, with a real
      `test_path` that is directly run and confirmed passing before being cited.
- [x] `tools/parity_index.py build`/`health` both run clean after the edit.

## Related Tickets
None.

## Related Docs
- `docs/plans/rpg_design_roadmap/rpg_spatial_index_hardening_plan.md` (source finding, item 2)
- `docs/compliance/checklist.md`
- `docs/parity_ledger/substrate.yaml`

## Related Stored Artifacts
None yet.

## Related Code Areas
- `src/engine/spatial.py` (`SpatialGrid`)
- `src/engine/world_index.py` (`SpatialIndex`, `WorldIndexes`, `WorldIndexService`)
- `tests/unit/movement/test_spatial_index.py`

## Assumptions / Open Questions
None — self-evident hotfix, confirmed via direct code read before ticketing.

## Implementation Notes
Confirmed the fabrication precisely before fixing, not assumed from the hardening plan's own summary:
`src/world/spatial.py` does not exist anywhere in `src/`; `tests/unit/world/test_spatial_index.py`
does not exist (the real file is `tests/unit/movement/test_spatial_index.py`, a different
directory); `SpatialIndex` (`src/engine/world_index.py:78`) is a **frozen** dataclass with no
`move()` method or any mutator at all — the original claim ("atomic move between cells") describes
an architecture that was never built, not merely mis-cited. The real design, confirmed via the
existing `test_spatial_grid_rebuild_logic` test, is rebuild-from-scratch:
`SpatialGrid.__init__` (`src/engine/spatial.py:8`) re-buckets every entity into its current cell
each time it's constructed; movement is reflected by constructing a new grid, not mutating the old
one. Fixed both the fabricated citation in `docs/compliance/checklist.md` and the underlying
`docs/parity_ledger/substrate.yaml` entry (previously a generic legacy-stub placeholder with
`test_path: null`, same category as the other pre-existing stubs found and left alone earlier this
session — this one was fixable because a real, verified test existed to cite).

## Test Summary
`tests/unit/movement/test_spatial_index.py::test_spatial_grid_rebuild_logic` run directly and
confirmed passing before being cited (never guessed). `tools/parity_index.py build`/`health` both
run clean after the edit.

## Files Changed
- `docs/compliance/checklist.md` (`SUB-327` line corrected)
- `docs/parity_ledger/substrate.yaml` (`SUB-327` entry corrected via `write_entry()`)

## Completion Summary
Fixed the fabricated `SUB-327` citation the 2026-09-02 spatial-index hardening plan found but never
itself corrected. The claim was wrong at the architecture level, not just the file path: `SpatialIndex`
has no mutator method at all, since the real design rebuilds the grid from scratch on each
construction. Both the compliance checklist line and the underlying parity ledger entry now cite the
real, verified test.
