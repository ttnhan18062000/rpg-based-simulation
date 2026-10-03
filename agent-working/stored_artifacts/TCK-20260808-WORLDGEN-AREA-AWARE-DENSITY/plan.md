---
status: active
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260808-WORLDGEN-AREA-AWARE-DENSITY
artifact_type: plan
tags: [world]
---

# Plan — TCK-20260808-WORLDGEN-AREA-AWARE-DENSITY

## Steps

1. `src/worldgeneration/generator.py`: replace the flat `pop_count_citizen`/`pop_count_monster`
   formula (lines 211-212) with the area/hazard-aware formulas from investigation.md, reusing the
   already-in-scope `regions["town_center"]`/`regions["wilderness_forest"]` `RegionSpec` objects
   for their `.bounds`/`.hazard_level`. Named module-level constants for the reference-point
   values (`_TOWN_REFERENCE_AREA = 900`, `_WILD_REFERENCE_AREA = 3366`,
   `_WILD_REFERENCE_HAZARD = 1.2`), each with a comment deriving them from the default
   `target_world_size=(100,100)`/`danger_level=1.0` case, not bare magic numbers.
2. `src/worldgeneration/generator.py`: harden the faction fallback (lines 126-136) — when
   `defenders`/`invaders` are empty, fall back to any real faction actually present in `factions`
   (`next(iter(factions), None)`) instead of a hardcoded literal with no existence guarantee. If
   `factions` is completely empty (no catalog factions at all), this is a real, harder failure
   the validator should still catch (not silently synthesized) — document this boundary.
3. `tests/unit/worldgeneration/test_generator.py`: the 5 new tests from test_plan.md (test 6 is
   the existing 4 tests, unmodified).

## Acceptance-criteria map

| AC | Disposition |
|---|---|
| investigation.md confirms bug location + region.area/hazard semantics | Done |
| generate() produces a valid WorldSpec for a real, non-trivial combination | Already true + hardened |
| Population factors in target_world_size's area | Step 1 |
| Confirmed density stays under WORLD-WARN-002 threshold | Step 3, test 5 |
| Scoped pytest passes | Step 3 |
