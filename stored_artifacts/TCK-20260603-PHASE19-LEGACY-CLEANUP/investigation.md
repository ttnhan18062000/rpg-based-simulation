# Investigation: Phase 19 Legacy Deprecation and Cleanup

## Context & Findings

1. **Seeding Seeding logic**: Seeding is triggered by `seed_phase1_content()`. In standard import execution, this runs at import time.
2. **Current state**: By default, `seed_phase1_content()` runs without parameters, leading to `runtime_content_source = "legacy_hardcoded"`.
3. **Data Parity**: In Phase 16, we ensured 100% parity between legacy hardcoded data and catalog data. Therefore, switching the default path to catalog mode should result in identical data structures, preserving all execution behaviors.
4. **Allowlisted Legacy Exceptions**:
   - Items: `rusted_sword`, `wooden_staff`, `basic_bow`, `leather_armor`, `iron_sword`, `hunter_blade`, `apprentice_staff`, `small_potion`, `travel_ration`, `repair_kit`, `wood`, `herb`, `iron_ore`, `beast_fang`, `wolf_pelt`, `moon_resin`, `crystal_shard`, `goblin_token`, `ancient_fragment`, `healing_flower`
   - Resources: `node_wood`, `node_herb`, `node_iron`, `node_resin`, `node_flower`
   - Enemies: `rat`, `wolf`, `goblin`, `goblin_archer`, `cave_spider`, `bandit_scout`, `elite_goblin`
   - Recipes: `iron_sword`, `hunter_blade`, `small_potion`
   - Services: `shop_hometown`, `blacksmith_hometown`, `guide_hometown`, `guild_hometown`, `inn_hometown`
   - Regions: `hometown`, `near_forest`, `old_mine`, `wolf_den`, `north_ruin`, `goblin_camp`, `moon_cave`
