# Investigation - Phase 28 (Perspective/relation usage and legacy-safe migration)

## Factions and Perspectives

The catalog data contains the following:
1. `data/content/social/factions.yaml` defines active factions and their legacy engine bucket:
   - `hero_guild` -> `HERO_GUILD`
   - `town_council` -> `TOWN_COUNCIL`
   - `wild_beast_pack` -> `MONSTER_HORDE`
   - `goblin_warband` -> `MONSTER_HORDE`
   - `merchant_league` -> `NEUTRAL`

2. `data/content/social/perspectives.yaml` defines POINT OF VIEW (perspective) mappings:
   - `hero_guild_perspective` (chosen_faction: `"hero_guild"`) maps `goblin_warband` to `hostile_groups` and `wild_beast_pack` to `contextual_threat_groups`.
   - `wild_beast_pack_perspective` (chosen_faction: `"wild_beast_pack"`) maps `town_council`, `hero_guild`, etc. to `contextual_intruder_groups`.
   - `merchant_league_perspective` (chosen_faction: `"merchant_league"`) maps `town_council`, `hero_guild` etc. to `trade_groups`.

3. `data/content/social/faction_relationships.yaml` defines named relationship models and axes:
   - `town_to_wild_beasts` has `hostility: "medium_contextual"`.
   - `wild_beasts_to_town` has `hostility: "low_base_contextual"` and `territorial_conflict: "high_if_intruding"`.

## Legacy Hostility Mechanics

Legacy hostility logic in `FactionSemanticsService.is_hostile` checks `alignment_bucket`:
- Defenders are hostile to Invaders, Invaders are hostile to all non-invaders.
- `invader` includes `MONSTER_HORDE` (e.g. wild beast pack and goblin warband).
- `defender` includes `HERO_GUILD` and `TOWN_COUNCIL`.

This logic must serve as the fallback when clean perspective or relationship definitions are missing for a given query.
