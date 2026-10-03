# Investigation: TCK-20260627-P2C-ARCHETYPE-DIST
# Add 6–8 archetypes for underrepresented roles

## Current Behavior (file:line refs)

**Primary file:** `data/content/entities/entity_archetypes.yaml`

21 existing archetypes with the following role distribution:
| Role | Count | IDs |
|---|---|---|
| scout | 4 | goblin_scout, goblin_archer, bandit_scout, lizardfolk_scout |
| predator_hunter | 2 | hungry_wolf, cave_spider |
| leader | 2 | goblin_warlord, dragon_cult_champion |
| raider | 2 | goblin_raider, orc_brute |
| mage | 1 | apprentice_mage |
| alpha | 1 | alpha_wolf |
| worker | 1 | village_worker |
| guard | 1 | frontier_guard |
| merchant | 1 | traveling_merchant |
| blacksmith | 1 | village_blacksmith |
| ranger | 1 | forest_ranger |
| sentinel | 1 | undead_sentinel |
| guardian | 1 | spirit_guardian |
| shaman | 1 | lizardfolk_shaman |
| brute | 1 | swamp_troll |

Scout overrepresentation: 4/21 = 19%. Mage underrepresentation: 1/21 = 5%. Healer: 0. Hunter/rogue concept: 0.

## Mechanics/Engine Constraints

**Validator** (`src/content/validator.py::CatalogValidator._validate_archetype_relations`): every archetype field is checked against the catalog:
- `race` → must exist in `data/content/living/races.yaml`
- `faction` → must exist in `data/content/social/factions.yaml`
- `role` → must exist in `data/content/social/roles.yaml` (no "rogue" role exists; use "hunter")
- `stat_profile` → must exist in `data/content/entities/stat_profiles.yaml`
- `combat_profile` → must exist in `data/content/entities/combat_profiles.yaml`
- `cognition_profile` → must exist in `data/content/living/cognition_profiles.yaml`
- `drive_profile` → must exist in `data/content/living/drive_profiles.yaml`
- `inventory_profile` → must exist in `data/content/entities/inventory_profiles.yaml`
- `skill_profile` → must exist in `data/content/entities/skill_profiles.yaml` (optional field)
- `traits` → each must exist in `data/content/foundation/traits.yaml`
- `themes` → each must exist in `data/content/foundation/themes.yaml`

**Available profiles (pre-verified):**
- Roles with no current archetype: healer, hunter, priest, miner, citizen, shopkeeper
- Stat profiles ready for new use: `healer_base`, `ranger_base`, `warlord_base`, `apprentice_mage_base`
- Combat profiles: `arcane_bolt`, `basic_melee`, `brute_crush`, `ranged_archer`, `opportunist_raider`
- Cognition: `practical_humanoid`, `arcane_scholar`, `opportunistic_humanoid`
- Drive: `cautious_commoner`, `ritual_fixated`, `disciplined_protector`, `opportunistic_raider`
- Inventory: `mage_satchel`, `ranger_pack`, `boss_hoard_token`, `goblin_looter_pouch`
- Skills: `mage_skills`, `warrior_skills`, `rogue_skills`, `ranger_skills`
- Traits: humanoid, tool_user, social_humanoid, magic_sensitive, disciplined, large_body, leader, opportunistic, small_body, ranged_attacker, amphibious
- Themes: village, frontier, forest, sacred, arcane, moon, corrupted, orc, dwarven, mine, mountain, bandit

NOTE: No "rogue" role exists in roles.yaml. The "rogue (1-2)" in the ticket is a conceptual label. Use `hunter` role (which has `rogue_skills` skill profile available and semantically covers stealthy attacker archetypes).

NOTE: No "healer_skills" skill profile. Healers use `mage_skills` (closest available, covers support magic).

## Parity Ledger Overlap (IDs + status)

- `progression.yaml`: references `test_hero_archetypes_cover_combat_mage_rogue` — this tests HERO entity class coverage (player archetypes), not mob archetypes. Adding new mob archetypes does not affect it.
- No parity entry directly tracks mob archetype count distribution — this is pure content addition.
- No behavior change: the validator already checks archetype referential integrity; adding valid entries does not alter any mechanics.

## Prior Work

- `TCK-20260604-PHASE25-ARCHETYPE-POPULATION-RESOLVER` — built PopulationRecipeResolver; archetype catalog feeds it
- `TCK-20260607-ARCHETYPE-METADATA-EXPLICIT` — added archetype_id to PopulationSpec; new archetypes gain this automatically
- `stored_artifacts/TCK-20260610-SWAMP-BORDER-PACK/` — precedent for adding archetypes via content pack; confirms the yaml-only approach works

## Risks and Open Questions

1. **Profile reuse**: Healer archetypes reuse `mage_satchel` (no dedicated healer inventory exists). Acceptable per scope (no new mechanics).
2. **No "rogue" role**: Ticket requests rogue-role archetypes but roles.yaml has no `rogue`. Using `hunter` role with `rogue_skills` satisfies the behavioral intent without requiring new role creation.
3. **CAT-DEAD-001 warning risk**: New archetypes added to the catalog but not immediately referenced by populations/ecologies may trigger a dead-active-data warning from the validator. This is acceptable (WARNING not ERROR); the ticket scope is distribution, not wiring into populations.

## Anti-Drift Hazards

- Validator `_validate_archetype_relations` will catch any typo in referenced IDs immediately — fail-fast protection
- Existing tests that load the full catalog will catch new archetypes referencing non-existent profiles
