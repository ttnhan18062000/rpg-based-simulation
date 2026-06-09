# Investigation: TCK-20260609-FRONTIER-EXTENDED-PACK

## Content Inventory (pre-pack)

### Archetypes without population consumers
- `orc_brute` (STATE: ADDITIONAL) — faction orc_clan; no population references it
- `spirit_guardian` (STATE: ADDITIONAL) — faction spirit_court; no population references it
- `forest_ranger` — consumed by `forest_warden_patrol` population (exists); but population has no module/ecology

### Populations without module/ecology consumers
- `forest_warden_patrol` — references regions `sacred_grove`, `deep_forest`; no module exists for these regions

### Loader architecture
- `CatalogRepository.load_all()` reads from `CANONICAL_FAMILIES` paths only
- `data/content/packs/` is not in CANONICAL_FAMILIES → pack manifests are metadata-only, not loaded as catalog records
- `NON_CATALOG_DIRS` = {world_modules, world_compositions, simulation_scenarios}
- New catalog content must be appended to existing YAML files in canonical paths

### Gate 04 scope
- Only checks STATE: EXISTING-LOGIC, LEGACY-EXPORT, REDESIGNED-CORE records
- STATE: ADDITIONAL records are exempt from consumer-path check
- New pack content using STATE: ADDITIONAL will not trigger gate 04

### WorldModuleSpec
- `relationships` is List[str] — no catalog validation; safe to reference new or existing IDs
- `terrain` in region must match an existing terrain ID (plain, forest, cave, mountain, ruin, road, snow, volcanic, swamp)
- No `hill` terrain type → using `plain` for orc territory

### Existing relationships available
- `forest_wardens_to_wild_beasts` exists — usable in forest_warden_grove module
- No `town_to_orc_clan` relationship — module will omit or list as new (normalizer doesn't validate)

## Decision: Pack Scope

Include 3 existing archetypes (orc_brute, forest_ranger, spirit_guardian):
- 2 new populations: orc_clan_warband, sacred_grove_guardians
- 1 existing population given a module: forest_warden_patrol
- 1 new biome: orc_territory
- 2 new ecologies: orc_territory_ecology, sacred_grove_ecology
- 2 new modules: orc_clan_territory, forest_warden_grove
- 1 new composition: frontier_extended (7 frontier_living_world modules + 2 pack modules)
- 1 new scenario: orc_clan_border_tension
- moon_cult_ruins excluded from composition to avoid CAT-REL-099 propagation

## CAT-REL-099 Interaction
Gate 11 remains xfail: CatalogValidator sweeps entire catalog regardless of composition.
New composition does not include moon_cult_ruins but the bug is catalog-level.
No gate items are expected to regress.
