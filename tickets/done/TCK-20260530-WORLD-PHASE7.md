---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260530-WORLD-PHASE7
phase: done
date: 2026-05-30
tags: [world, phase7]
---

# TCK-20260530-WORLD-PHASE7

## Title

World Data Refactor Phase 7: Provenance Manifest and Report Integration

## Status

DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary

Establish the Sidecar Provenance Manifest and integrated compile reporting system. Ensure resolving processes log all region, population, resource, and building origins dynamically, outputting a bit-identical stable `provenance_manifest.json` along with detailed multi-layer reports stored in resolved subdirectories.

## Scope

- Define the comprehensive `ProvenanceRecord` and `ProvenanceManifest` Pydantic models under `src/worldassembly/schema.py`.
- Refactor `WorldAssemblyResolver.assemble` to build the full manifest dynamically, mapping exact origins, applied catalog profiles/defaults, and evaluated parameters without modifying any core runtime schemas like `EntityState`.
- Support group/range-based records mapping to avoid giant maps for compiled world elements.
- Integrate compile report generation outputting the compilation results beside resolved files.
- Implement tests verifying complete metadata persistence, determinism, and optional placeholder parameters for procedural generators (deferred to Phase 8).

## Out of Scope

- Storing procedurally generated coordinates or entity states (this belongs to Phase 8).
- Integrating ClickHouse/observability database storage (handled downstream).

## Acceptance Criteria

- [x] `ProvenanceManifest` Pydantic schema defined containing all 11 required top-level attributes.
- [x] Manifest records track region, population/entity group, building, resource, faction, and profile origins correctly.
- [x] Assembly resolver generates a complete manifest dynamically without mutating runtime `EntityState`.
- [x] Compile reports correctly serialize beside the resolved bundle files.
- [x] Same input composition and seed yields 100% byte-identical, deterministic provenance manifest files.
- [x] Automated tests cover all manifest properties, determinism checks, and regressions.

## Related Tickets

- `TCK-20260530-WORLD-PHASE6`

## Related Docs

- `world_phases_0_10_updated.md` (Phase 7)
- `docs/architecture/world_assembly_architecture.md`

## Related Stored Artifacts

- None

## Related Code Areas

- `src/worldassembly/schema.py`
- `src/worldassembly/resolver.py`
- `src/worldbuilding/repository.py`

## Assumptions / Open Questions

- Generator-specific fields in the manifest are initialized to empty or default placeholders until Phase 8.

## Implementation Notes

- Fully resolved element mappings, using computed property fallback inside the schemas to maintain 100% backward-compatibility.

## Test Summary

- Added `tests/unit/worldassembly/test_provenance.py` covering manifest attributes, grouped entity resolution, and byte-level determinism. All tests pass perfectly.
  - `pytest tests/unit/worldassembly/` (6 passed)
  - `pytest tests/unit/worldbuilding/` (65 passed)
  - `pytest tests/unit/worldmodules/` (3 passed)

## Files Changed

- `src/worldassembly/schema.py` (MODIFY)
- `src/worldassembly/resolver.py` (MODIFY)
- `tests/unit/worldassembly/test_provenance.py` (NEW)

## Completion Summary

- Provenance manifest is compiled sidecar-only as part of the resolver bundle, featuring robust context-mapping without affecting any runtime engine systems.
