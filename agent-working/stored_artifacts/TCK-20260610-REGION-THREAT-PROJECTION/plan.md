---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260610-REGION-THREAT-PROJECTION
artifact_type: plan
tags: [region, threat, projection]
---

# TCK-20260610-REGION-THREAT-PROJECTION — Plan

## New File: `src/world/region_threat_classifier.py`

`RegionThreatClassification` — Pydantic BaseModel:
- `label: Literal["safe", "neutral", "contested", "threatened", "hostile", "unknown"]`
- `source: Literal["catalog_projection", "legacy_fallback", "no_faction_data"]`
- `contributing_factions: List[str]`
- `perspective_id: str`

`RegionThreatClassifier` — read-only, catalog-backed:
- `__init__(catalog: CatalogRepository)`
- `classify(perspective_faction_id, controlling_faction_id, population_faction_ids, context)` → `RegionThreatClassification`

Internal:
- `_resolve_perspective_id()` — find perspective for faction
- `_derive_label(ctrl_label, pop_labels)` — priority derivation
- `_classify_legacy()` — fallback using `get_legacy_faction_bucket()`

## No Changes to Existing Files

New classifier stands alone. No mutation paths. Existing `ThreatService`, `RegionService`, `RegionState` unchanged.

## Tests: `tests/unit/world/test_region_threat_classifier.py`

| Test | Expected label |
|---|---|
| `test_town_region_safe_from_hero` | safe |
| `test_goblin_camp_hostile_from_hero` | hostile |
| `test_wolf_den_threatened_from_hero` | threatened (contextual, not hostile) |
| `test_merchant_road_contested_with_bandit` | contested |
| `test_no_factions_unknown` | unknown |
| `test_legacy_fallback_monster_horde` | hostile |
| `test_classification_does_not_mutate_catalog` | catalog unchanged after classify() |
| `test_deterministic_same_inputs` | same label on repeated calls |
