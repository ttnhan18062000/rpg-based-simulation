---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260609-STRICT-WORLD-MATRIX
artifact_type: investigation
tags: [strict, world, matrix]
---


# Investigation

## Pre-existing block: CAT-REL-099

`moon_cult_ruins` references population `apprentice_mage` which doesn't exist in the catalog.
`CatalogValidator` runs on ALL modules in the catalog — not just the ones in the composition
being assembled. This means even a single-module composition (frontier_village_core alone)
fails during the assembly validation stage.

**Impact**: All full-assembly matrix tests (WorldSpec, CompileContext, blocking errors,
fingerprint, no-legacy-fallback) are xfail. Pre-assembly tests (load, normalize, fingerprint,
registry seeding) pass unconditionally.

## Module inventory

All 7 modules exist in `data/content/world_modules/`:
- frontier_village_core, wolf_den_near_forest, goblin_camp_conflict, old_mine_resource_loop,
  bandit_road_trade_pressure, undead_battlefield, moon_cult_ruins

## Registry seeding

`seed_phase1_content(repo, mode=CATALOG_WITH_COMPATIBILITY)` populates ItemRegistry,
ResourceRegistry, etc. from catalog data. This is catalog-level, not assembly-dependent,
so it can be tested unconditionally.
