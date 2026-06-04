# Implementation Plan - Phase 28 (Perspective/relation usage and legacy-safe migration)

Provide one clean service to project relationship labels and implement a compatibility wrapper to fallback to legacy bucket-based semantics.

## Proposed Changes

### Content Semantics

#### [NEW] [relation.py](file:///home/vboxuser/Work/rpg-based-simulation/src/content_semantics/relation.py)

- Define Pydantic models:
  - `RelationContext`: optional fields `distance`, `location`, `intruding`, `combat_engaged`, `target_race`.
  - `RelationProjection`: fields `label`, `axes`, `confidence`, `relationship_model`, `source_records`.
- Define class `RelationProjectionService`:
  - Initialize with `CatalogRepository`.
  - Method `project_relation(perspective_id, source_faction_id, target_faction_id, context)`:
    - Resolves perspective ID (or matches faction ID to perspective).
    - Checks if target faction ID matches any projected labels in the perspective (e.g. `ally_groups`, `hostile_groups`, etc.) and determines the label.
    - Resolves relationship definition between source and target factions, mapping axes (e.g. `hostility`) to relationship labels (e.g. `enemy`, `threat`).
    - If neither perspective nor relationship defines the relationship, falls back to legacy FactionSemanticsService-based hostility check to project `enemy` or `neutral`.

#### [MODIFY] [faction.py](file:///home/vboxuser/Work/rpg-based-simulation/src/content_semantics/faction.py)

- Add compatibility wrapper method `is_hostile_compat(self, source: str, target: str, context: Optional[RelationContext] = None) -> bool`:
  - Attempts to call `RelationProjectionService.project_relation`.
  - If clean relationship/perspective data is missing (i.e. perspective doesn't list the target and there is no faction relationship defined), falls back to the legacy `is_hostile` logic and logs fallback usage at `DEBUG` level.

---

### Tests

#### [MODIFY] [test_semantics.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/unit/content_semantics/test_semantics.py)

- Add test cases to verify:
  - Goblin warband projects as `enemy` from hero perspective.
  - Wild beast pack projects as contextual `threat` (or intruder), not enemy-by-race.
  - Merchant league projects as `neutral` or trade.
  - Legacy `is_hostile` wrapper still works.
  - `is_hostile_compat` correctly falls back and logs.

---

## Verification Plan

### Automated Tests
- Run content semantics tests:
  ```bash
  pytest tests/unit/content_semantics/
  ```
- Run arena tests to ensure backward compatibility:
  ```bash
  pytest tests/arena/
  ```
