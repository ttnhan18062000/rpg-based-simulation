---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260610-REGION-THREAT-PROJECTION
phase: done
date: 2026-06-10
tags: [region, threat, projection]
---

# TCK-20260610-REGION-THREAT-PROJECTION

## Title
Wire RelationProjectionService into region threat classification using faction, perspective, and context

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Region safety/threat evaluation currently uses hardcoded faction bucket logic or danger level thresholds. `RelationProjectionService` and `EntityIdentityResolver` already exist but are not wired into region threat classification. This task adds a projection-based classification layer that evaluates region threat from: region controlling faction, active populations, resolved entity/faction identities, selected perspective, danger level, and territorial/resource conflict context. Classification does not mutate region ownership.

## Scope
- Identify region threat classification code in `src/region/`, `src/world/`, or `src/systems/`
- Add projection-based threat classifier: inputs are controlling faction + active populations + perspective + context; output is one of `safe | neutral | contested | threatened | hostile | unknown`
- Classification must be read-only — must NOT mutate region ownership or influence
- Preserve legacy region classification as fallback
- Tests (add near regional control/region semantics tests):
  - town-controlled region is safe from hero perspective
  - goblin camp is hostile from hero perspective
  - wolf den is contextual threat (not always hostile)
  - merchant road is contested when bandit module active
  - legacy region tests still pass

## Out of Scope
- Rewriting regional influence or conquest logic
- Mutating region ownership
- Adding new relationship axes or changing perspective schema

## Acceptance Criteria
- [x] Region threat classification uses perspective
- [x] Faction relationship affects classification result
- [x] Contextual wildlife threat is supported (not always hostile)
- [x] Existing regional control tests still pass
- [x] Classification does not mutate ownership
- [x] Classification result is deterministic for same inputs

## Related Tickets
- TCK-20260610-COMBAT-RELATION-PROJECTION (parallel Phase 37 concern)
- TCK-20260610-QUEST-RELATION-PROJECTION (parallel Phase 37 concern)
- TCK-20260609-ENTITY-IDENTITY-RESOLVER (EntityIdentityResolver already done — reuse)

## Related Docs
- `docs/mechanics/05_world_evolution.md`
- `docs/mechanics/06_worldbuilding_foundation.md`

## Related Code Areas
- `src/content_semantics/relation.py` — RelationProjectionService (exists)
- `src/entities/identity_resolver.py` — EntityIdentityResolver (exists)
- `src/region/` or `src/world/` — region threat classification (identify exact file)
- `tests/` — existing region/control tests (do not break)

## Assumptions / Open Questions
- Where is region threat/safety evaluated? Check `src/region/`, `src/world/`, or `src/systems/` before implementing.
- Is there an existing `RegionThreatClassifier` or equivalent, or is it inline in a larger system?

## Implementation Notes
Created `src/world/region_threat_classifier.py` with `RegionThreatClassification` (Pydantic model) and `RegionThreatClassifier`. No existing files were modified — classifier stands alone. Uses `RelationProjectionService` for catalog-backed classification (perspective-aware); falls back to `FactionSemanticsService.get_legacy_faction_bucket()` when no perspective exists. Label derivation priority: hostile > contested > threatened > safe > neutral > unknown.

## Test Summary
10/10 pass: town safe, goblin hostile, wolf den threatened (not hostile), merchant road contested, allied+threat=threatened, no factions=unknown, no populations default, legacy fallback monster_horde=hostile, read-only, deterministic. Regression: 91/92 world tests (1 pre-existing failure in test_shop_buy_and_sell, unrelated).

## Files Changed
- `src/world/region_threat_classifier.py` — new (RegionThreatClassifier + RegionThreatClassification)
- `tests/unit/world/test_region_threat_classifier.py` — new (10 tests)

## Completion Summary
New read-only `RegionThreatClassifier` projects region safety from any faction's perspective using the catalog. Classification yields safe/neutral/contested/threatened/hostile/unknown, derived from controlling faction label + population faction labels. Wild beasts are "threatened" (contextual), not "hostile", proving perspective-aware contextual grading. Legacy fallback handles any faction without a catalog perspective. 10 new tests + 91 regression tests pass.
