---
status: active
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260808-LIFECYCLE-FULL-COVERAGE-WORLD
artifact_type: plan
tags: [world, simulation-quality, corpus]
---

# Plan — TCK-20260808-LIFECYCLE-FULL-COVERAGE-WORLD

## World identity
- `world_id`: `lifecycle_full_coverage_world`
- Tier: **Stress** — fills a new named scale-diversity gap (§ below), not a coherent-archetype
  scenario and not isolating one gated mechanic.
- New gap #6 for `corpus_tier_taxonomy.md`'s "Named scale-diversity gaps" section: **"No world
  structurally reaches all reachable `entity_lifecycle_score.py` `lifecycle_phase_buckets`."**
  (9/10 is the honest maximum per investigation.md §1 — `IDENTITY` is a hard engine ceiling.)

## Module composition (8 modules, all real corpus content — no new module authored)
1. `frontier_village_core` — settlement, `town_hall` building (required by `GuildNeedScorer`),
   council/workers/guards/trade/crafting (ECONOMY + SOCIAL gate + STRATEGY_COGNITION baseline)
2. `hero_adventurers` — HERO population (WARRIOR/MAGE/ROGUE), the entities most likely to satisfy
   `GuildNeedScorer`'s spare-project-capacity gate and drive `GROWTH_PROGRESSION`/`COMBAT`
3. `mountain_pass` — terrain/exploration variety (`EXPLORATION`)
4. `ruins_mystery_quest` — undead-themed hostile content + a 2nd FACTION pair
   (`undead_remnants`/`spirit_court`)
5. `goblin_camp_conflict` — hostile population + `goblin_warband` faction (`COMBAT`)
6. `wolf_den_near_forest` — real "wolf"-race archetype population (`hungry_wolf`/`alpha_wolf`) —
   the one guaranteed real HUNT-quest-completion path (`q_wolf_hunt`, `target_kind="wolf"`)
7. `orc_clan_territory` — additional hostile population + `orc_clan` faction (COMBAT/FACTION
   diversity, population scale)
8. `river_crossing` — additional terrain variety (`EXPLORATION`)

Region IDs (verified no collision): `hometown`, `mountain_pass_zone`, `haunted_battlefield`,
`goblin_camp`, `near_forest`, `wolf_den`, `orc_stronghold`, `river_ford`.
Faction IDs (verified no collision): `town_council`, `merchant_league`, `hero_guild`,
`undead_remnants`, `spirit_court`, `goblin_warband`, `wild_beast_pack`, `orc_clan`.

Real compile is the final confirming check (Implement step 1) — if it surfaces a collision this
plan didn't catch, resolve by dropping the offending module (matching `simq_scale_stress_seed42`'s
own precedent), documented in Implementation Notes, not silently worked around.

## Feature flags (`config/simulation_quality/profiles/lifecycle_full_coverage_world.yaml`)
```yaml
feature_flags:
  ENABLE_ADVENTURE_ROUTING: "ON"       # STRATEGY_COGNITION route-specific events (hero_guild_routing precedent)
  ENABLE_SOCIAL_COOPERATION: "ON"      # SOCIAL bucket (highland_traverse/frontier_living_world precedent)
  ENABLE_BELIEF_ASSIMILATION: "ON"     # STRATEGY_COGNITION belief_* events (highland_traverse precedent)
  ENABLE_GUILD_QUEST_GENERATION: "ON"  # NARRATIVE_QUEST — real quest generation via GuildAction.visit()
```

## faction_tension_overrides / information_source_profiles
- `faction_tension_overrides`: real values for all 8 factions above (matching
  `simq_scale_stress_seed42`'s own 0.4-0.6 range for hostile factions; 0.5 for the 2 civilian-side
  factions, matching `highland_traverse`'s own `town_council`/`merchant_league` precedent) —
  authored from inception, per gap #3's own "authored from inception, not retrofit" standard.
- `information_source_profiles`: reuse `highland_traverse`'s exact `route_waystation_guide`
  shape (real, already-calibrated INFORMATION content), pointed at this world's own population.

## Acceptance-criteria map
| AC | How satisfied |
|---|---|
| investigation.md confirms real IDENTITY/NARRATIVE_QUEST reachability | investigation.md §1-2 |
| investigation.md surveys existing corpus precedent | investigation.md §3 |
| plan.md specifies module composition, feature flags, corpus tier | this document |
| World authored, compiled, added to `corpus_registry.yaml` | Implement step 1-3 |
| Real long-run observation run performed, real bucket-count reported honestly | Implement step 4 |
| `corpus_tier_taxonomy.md` updated | Implement step 5 |
| Scoped pytest passes | Test phase |

## Implementation steps
1. Author `data/content/world_compositions/lifecycle_full_coverage_world.yaml` (module_refs, seed,
   `faction_tension_overrides`, `information_source_profiles`).
2. Author `config/simulation_quality/profiles/lifecycle_full_coverage_world.yaml` (feature flags
   above).
3. Compile via the standard world-compile path; resolve any real collision found.
4. Run `python3 -c "from tools.simq_long_run_observation import observe_world; ..."` (or the
   `make` target if one exists) for `lifecycle_full_coverage_world`, seed 42, 5000 ticks — record
   real `phase_coverage`/bucket-count result.
5. Regenerate `config/simulation_quality/corpus_registry.yaml`
   (`make simq-corpus-registry`/`tools/generate_corpus_registry.py`).
6. Update `docs/simulation_quality/corpus_tier_taxonomy.md`: new per-world table row + new gap #6
   entry (or mark it closed if 9/10 is reached, matching the doc's own "closed, not deleted"
   pattern for prior gaps).

## Out of scope (unchanged from ticket)
- Fixing IDENTITY-bucket unreachability or quest GATHER/BOUNTY/LIBERATE dormancy — filed as
  separate follow-ups if not already covered.
- `grade_anchors.json` calibration for this world (long-run observation only, per ticket's own Out
  of Scope).
