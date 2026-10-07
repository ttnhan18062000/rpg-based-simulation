---
status: historical
layer: world
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261006-WILD-BEAST-PACK-LEGALITY-IS-ONE-WAY-HERO-CAN-ATTACK-IT-IT-CANNOT-ATTACK-HERO
phase: done
date: 2026-10-07
tags: [world, combat, legality]
---

# Investigation

## Cause
`verify_attack_legality` computed `has_clean` from the *attacker's* data and asked `is_hostile_compat(attacker, target)` only, so `wild_beast_pack` (a contextual threat, label `threat`, hostile only when engaged or within 5 tiles) could not attack a hero that could attack it, and an undeclared attacker could attack any faction of a different legacy bucket regardless of hostility.

## Rule implemented
Designer's three-case rule (CONFLICT-03 resolution): both declare -> either hostile; exactly one declares -> its verdict decides both directions; neither -> legacy fallback. A full union (any direction legal) was tried first and rejected: it made hero -> defected NEUTRAL legal and broke the ratified `test_legality_faction_mutation` pin.

## Matrix (`probes/matrix.py`, 16 catalog factions x engaged/not = 512 verdicts, real legality service)
Before: 108 asymmetric verdicts. After: 0. 16 directed illegal -> legal, 15 directed legal -> illegal, 0 unexplained.
- illegal -> legal, wild: wild_beast_pack -> hero_guild, town_council, merchant_league, bandit_company, orc_clan; dragon_cult, moon_cult, swamp_tribe, undead_remnants -> wild_beast_pack; goblin_warband -> wild_beast_pack (engaged only).
- illegal -> legal, non-wild (sign-off 2026-10-07): goblin_warband -> bandit_company, goblin_warband -> merchant_league, merchant_league -> swamp_tribe (engaged only), swamp_tribe -> hero_guild, dragon_cult -> swamp_tribe, moon_cult -> swamp_tribe.
- legal -> illegal (every one exactly-one-declared; the undeclared side was attacking by the legacy different-bucket rule): arcane_circle -> hero_guild, swamp_tribe, wild_beast_pack; dwarven_mine_clan -> merchant_league, swamp_tribe, wild_beast_pack; spirit_court -> hero_guild, swamp_tribe, wild_beast_pack; neutral -> hero_guild, swamp_tribe, wild_beast_pack; forest_wardens -> swamp_tribe; town_council -> neutral, swamp_tribe.

## Corpus (`probes/combat_ab.py`, 24 worlds, seed 42, 10,000 ticks, audit_mode, budget off; before = `BEFORE=1` forward-only legality and the five wild kinds unmapped; tree `origin/main` `7254a558c`)
Totals before -> after: deaths 131 -> 130, combat deaths 81 -> 76, hazard deaths 50 -> 54, damaging attacks 1,278 -> 1,237, attacks by a wild_beast_pack attacker 81 -> 184, wild deaths 24 -> 23. Determinism: `frontier_marches` and `swamp_border_world` re-run in both arms reproduce run 1 exactly (a second full corpus run was not taken; seeded and deterministic).
Neutral-faction attacker: 0 damaging attacks in either arm, so 0 live neutral -> hero attacks lost. The one lost direction with events: town_council -> swamp_tribe, `swamp_border_world` 8 -> 0.
Non-wild newly legal pairs meeting: goblin_warband -> merchant_league 0 -> 30 (crowded_frontier 4, frontier_extended 7, frontier_living_world 6, frontier_marches 4, generated_frontier_3_42 4, hero_guild_routing 1, simq_scale_stress_seed42 4); goblin_warband -> bandit_company 127 -> 100 (6 worlds); merchant_league -> swamp_tribe 9 -> 20 (`swamp_border_world`). Per-pair counts are indications; trajectories diverge.
Not attributed: hazard deaths `frontier_marches` 10 -> 15 (town_council victims 2 -> 8) and `swamp_border_world` 0 -> 2 (town_council 2). Possibly trajectory divergence; not isolated.

## Perf (item 6; `probes/bench.py`, `probes/prof.py`)
Symmetric change adds no per-call cost to the hot path: `combat_engagement` at 1,000 entities (`build_movement_state`, PERF_2GB_LOCAL, 8 sample ticks) 1,793 and 1,875 ms/tick before vs 1,803 and 1,861 after. `_attack_permitted` runs only from `verify_attack_legality`, not from `_consider`. The movement[5000] pytest bench was not run: it hits the 10-minute pytest timeout locally (one run, "1 failed in 601s", no p95).
Isolated step (cProfile, 1 tick, 1,000 entities): 133,036 `are_entities_hostile` calls -> 304,230 `is_hostile_compat` (4.7 s cumulative) -> 304,230 `project_relation` (2.9 s) plus 271k `_resolve_faction_id`/`EntityIdentityResolver.resolve` (2.3 s), reached from `combat_engagement/phase.py::_consider` (170,694 calls, 3.7 s) and the strategic scorers (`filter_saliency`). The calls are pairwise per entity (quadratic in N); each does linear scans over all perspectives and relationship rows. A local fix would be a catalog index or a per-tick pair cache, which has a lifecycle and invalidation and is not behaviour-neutral by inspection, so no fix is included; this belongs to `TCK-20261006-COMBAT-ENGAGEMENT-HOSTILITY-PROJECTION-COST-STEP` (test-arch, not on main when written).
