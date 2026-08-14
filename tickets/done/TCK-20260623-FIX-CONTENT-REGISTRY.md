---
status: open
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260623-FIX-CONTENT-REGISTRY
phase: open
date: 2026-06-23
tags: [test-repair, content, registry, schema]
---

# TCK-20260623-FIX-CONTENT-REGISTRY

## Title
Fix content registry drift + NormalizedWorldModule schema (~8 failures)

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
Two small, independent schema/registry issues.

**Root Cause 1 — ContentUsageMatrix missing 3 pack YAMLs (D10 F6):**
Three YAML files exist in `data/content/` but are not registered in `ContentUsageMatrix`:
- `compatibility/migration_map.yaml`
- `packs/swamp_border_pack.yaml`
- `packs/frontier_extended_pack.yaml`

`src/content/repository.py:353` raises `ValueError` on strict load when unregistered files are found. Fix: register the 3 families in `ContentUsageMatrix`, OR confirm they are intentionally draft and add them to an exclusion list.

**Root Cause 2 — NormalizedWorldModule schema_version kwarg removed (D10 F9):**
`tests/unit/content/test_reference_graph.py` passes `schema_version` kwarg to `NormalizedWorldModule.__init__` but the field was removed or renamed. Fix: remove the `schema_version` kwarg from the 3 test call sites.

## Scope
- Register `migration_map.yaml`, `swamp_border_pack.yaml`, `frontier_extended_pack.yaml` in `ContentUsageMatrix`
- Remove `schema_version` kwarg from `NormalizedWorldModule` instantiation in `test_reference_graph.py`

## Out of Scope
- ContentUsageMatrix logic changes
- New content authoring
- NormalizedWorldModule logic changes

## Acceptance Criteria
- `tests/unit/content/test_content_usage_matrix.py::test_matrix_covers_all_content_files` passes
- `tests/unit/content/test_content_paths.py::test_strict_load_on_real_content_dir` passes
- `tests/unit/content/test_reference_graph.py` — all 3 tests pass
- `tests/integration/content/test_expansion_gate.py::test_gate_11_world_assembly_resolves` passes

## Related Tickets
- D10 audit F6, F9
- TCK-20260623-FIX-WORLDASSEMBLY (overlapping content domain — coordinate)

## Related Docs
- `docs/audits/D10_test_coverage.md` F6, F9

## Related Code Areas
- `src/content/repository.py:353` (strict load)
- `src/worldassembly/` or `src/content/` (ContentUsageMatrix)
- `src/worldassembly/schemas.py` or `src/worldbuilding/` (NormalizedWorldModule)
- `tests/unit/content/test_reference_graph.py`

## Assumptions / Open Questions
- Are the 3 pack YAMLs production-ready or draft? If draft, they should be excluded from strict load, not registered.

## Implementation Notes
Fast ticket — no staging artifacts required (hotfix tier).
1. Read `ContentUsageMatrix` to find how entries are registered
2. Add 3 entries
3. Find `NormalizedWorldModule.__init__` — remove `schema_version` or add it back with `default=None`
4. Remove kwarg from 3 test call sites

## Test Summary
Run: `pytest tests/unit/content/ tests/integration/content/test_expansion_gate.py -m "not slow" --tb=short`

## Files Changed
- `src/content/matrix.py` — added 3 missing entries: compatibility/migration_map, packs/swamp_border_pack, packs/frontier_extended_pack
- `tests/unit/content/test_reference_graph.py` — removed stale schema_version kwarg; added quest_definitions=[] to NormalizedWorldModule defaults

## Completion Summary
Registered 3 untracked content families in ContentUsageMatrix (all DESIGN_ONLY). Removed schema_version from NormalizedWorldModule test factory (field was removed from the dataclass). Added missing quest_definitions field to defaults. All 5 targeted tests pass.
