---
status: historical
layer: misc
authority: P1
audience: agent
ticket_id: TCK-20260608-RUNTIME-MODE-EXPLICIT
phase: done
date: 2026-06-08
tags: [runtime, mode, explicit]
---

# TCK-20260608-RUNTIME-MODE-EXPLICIT

## Title
Replace RuntimeContentMode MIGRATION/V2 with four explicit modes

## Status
DONE

## Tier
standard

## Type
refactor

## Priority
P1

## Request Summary
The current RuntimeContentMode enum has only MIGRATION and V2, which are too vague to signal exact runtime behavior to future implementers and AI agents. This task replaces both values with four precise modes — CATALOG_STRICT, CATALOG_WITH_COMPATIBILITY, LEGACY_FALLBACK, and TEST_MANUAL — and updates all call sites, adapter constructors, seed_phase1_content(), registry parity tests, and runtime content mode tests to use the new values. CATALOG_STRICT must reject any heuristic projection; CATALOG_WITH_COMPATIBILITY must report heuristic usage; LEGACY_FALLBACK must allow hardcoded fallback; TEST_MANUAL must not require a catalog.

## Scope
- Replace RuntimeContentMode enum values: remove MIGRATION and V2, add CATALOG_STRICT, CATALOG_WITH_COMPATIBILITY, LEGACY_FALLBACK, TEST_MANUAL
- Map old V2 → CATALOG_STRICT, old MIGRATION → CATALOG_WITH_COMPATIBILITY at all call sites
- Update adapter constructors (CatalogToItemRegistryAdapter, CatalogToServiceRegistryAdapter, CatalogToResourceRegistryAdapter, ArchetypeToEnemyRegistryAdapter) to accept new mode values
- Update seed_phase1_content() signature and internal mode branching
- Update or replace tests in tests/unit/content/test_runtime_content_mode.py to cover all four modes
- Update registry parity tests to use new mode constants

## Out of Scope
- Removing legacy fallback logic
- Implementing Phase 29+
- Changing ContentFamilyMatrixEntry states
- Adding new content packs

## Acceptance Criteria
- [x] RuntimeContentMode has exactly four values: CATALOG_STRICT, CATALOG_WITH_COMPATIBILITY, LEGACY_FALLBACK, TEST_MANUAL
- [x] RuntimeContentMode.MIGRATION and RuntimeContentMode.V2 are removed (or kept only as deprecated aliases)
- [x] CATALOG_STRICT mode raises or rejects when heuristic projection is attempted
- [x] CATALOG_WITH_COMPATIBILITY mode allows heuristic projection and reports it
- [x] LEGACY_FALLBACK mode allows hardcoded fallback records
- [x] TEST_MANUAL mode does not require a catalog to be present
- [x] All existing registry parity tests pass with updated mode constants
- [x] test_runtime_content_mode.py asserts exactly four modes and tests each mode's behavior

## Related Tickets
- TCK-20260607-RUNTIME-CONTENT-MODE (predecessor — implemented MIGRATION/V2; this ticket replaces those values)

## Related Docs
- docs/engine/authoritative_pipeline.md
- docs/engine/kernel.md

## Related Stored Artifacts
None.

## Related Code Areas
- src/core/modes.py
- src/core/registries.py
- tests/unit/content/test_runtime_content_mode.py
- tests/integration/content/test_registry_projection_parity.py

## Assumptions / Open Questions
- No external consumer outside the repo depends on the string values 'migration' or 'v2'
- Deprecated aliases for old values are acceptable short-term but not required

## Implementation Notes
- Mapped V2 → CATALOG_STRICT and MIGRATION → CATALOG_WITH_COMPATIBILITY at all call sites.
- Four adapter constructors updated (Item, Service, Resource adapters; Enemy adapter has no mode param).
- seed_phase1_content default param and bottom auto-call updated.
- Integration parity test fixture updated.

## Test Summary
- 7 new tests in tests/unit/content/test_runtime_content_mode.py — all pass.
- 5 existing parity tests still pass with updated mode constant.
- Total: 12/12 passed.

## Files Changed
- src/core/modes.py
- src/core/registries.py
- tests/unit/content/test_runtime_content_mode.py (new)
- tests/integration/content/test_registry_projection_parity.py

## Completion Summary
RuntimeContentMode now has exactly four semantically precise values. All V2 call sites map to CATALOG_STRICT; all MIGRATION call sites map to CATALOG_WITH_COMPATIBILITY. Tests verify each mode's behavior.
