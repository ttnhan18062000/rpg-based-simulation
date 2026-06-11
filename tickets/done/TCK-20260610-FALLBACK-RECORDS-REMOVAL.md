---
status: historical
layer: misc
authority: P1
audience: agent
ticket_id: TCK-20260610-FALLBACK-RECORDS-REMOVAL
phase: done
date: 2026-06-10
tags: [fallback, records, removal]
---

# TCK-20260610-FALLBACK-RECORDS-REMOVAL

## Title
Graduated removal of fallback records by family after catalog equivalents verified

## Status
DONE

## Tier
standard

## Type
refactor

## Priority
P2

## Request Summary
Phase 44.3. Graduated quarantine of hardcoded fallback records in seed_phase1_content after verifying catalog equivalents. Families with full catalog coverage are quarantined (QUARANTINED markers added). Families without full catalog coverage are documented with fallback_only migration map entries.

## Scope
- Verified per-family catalog coverage for all 6 families
- Added QUARANTINED markers to 5 families in registries.py fallback block
- Added rat enemy as fallback_only to migration_map.yaml
- Added hometown service entries as quarantined to migration_map.yaml
- Added region entries as quarantined to migration_map.yaml
- Updated resource and recipe entries from compat_projected → quarantined
- Added quarantined status to migration map schema + test

## Out of Scope
- Hard deleting quarantined records (next step once consumers are verified)
- Adding catalog equivalent for "rat"

## Acceptance Criteria
- [x] Each family verified: catalog coverage documented per family
- [x] Items, recipes, regions, resources, services: quarantined with QUARANTINED markers
- [x] Enemies: fallback records retained (rat has no catalog equivalent)
- [x] Migration map updated: quarantined families marked, rat added as fallback_only
- [x] Parity tests pass after quarantine (8 tests)
- [x] Strict matrix passes after quarantine (63 tests, 9 modules × 7 assertions)
- [x] No test breakage: LEGACY_FALLBACK data still present (quarantined ≠ deleted)

## Related Tickets
- TCK-20260610-FALLBACK-RESTRICT-MODES (prerequisite)
- TCK-20260610-FALLBACK-RETIREMENT-CRITERIA (prerequisite)

## Related Docs
- `docs/guidelines/fallback_retirement_criteria.md`
- `data/content/compatibility/migration_map.yaml`

## Related Code Areas
- `src/core/registries.py` — fallback block QUARANTINED markers
- `data/content/compatibility/migration_map.yaml` — quarantined/fallback_only status updates
- `tests/unit/content/test_migration_map_schema.py` — quarantined added to VALID_STATUSES

## Assumptions / Open Questions
- "rat" remains a fallback_only blocker until a rat archetype is added to data/content

## Implementation Notes
Per-family catalog coverage verified:
- items: 20/20 covered (catalog world/items.yaml) ✅
- recipes: 3/3 covered (catalog world/recipes.yaml) ✅
- regions: 7/7 covered (catalog world/runtime_regions.yaml) ✅
- resources: 5/5 covered (catalog world/resources.yaml) ✅
- services: 5/5 adapts in catalog path (CatalogToServiceRegistryAdapter prepopulates legacy IDs) ✅
- enemies: 6/7 covered — rat missing (capability_estimate.py:60 hardwires "rat") ❌

QUARANTINED = records retained for LEGACY_FALLBACK debugging only; catalog is authoritative.
fallback_only = no catalog equivalent; must remain in fallback block.

## Test Summary
109 tests run: 10 migration map schema, 8 parity, 63 strict matrix, 18 runtime + fallback-restrict. All pass.

## Files Changed
- `src/core/registries.py` — QUARANTINED markers on 5 families in seed_phase1_content else branch
- `data/content/compatibility/migration_map.yaml` — quarantined status added; 5 resources updated; 3 recipes updated; 7 regions added; 5 services added; rat added as fallback_only
- `tests/unit/content/test_migration_map_schema.py` — quarantined added to VALID_STATUSES

## Completion Summary
Five of six fallback families quarantined with clear markers (catalog is authoritative). Enemy family stays with fallback_only for "rat". Migration map updated with 18 new/updated entries and quarantined status. All 109 tests pass.
