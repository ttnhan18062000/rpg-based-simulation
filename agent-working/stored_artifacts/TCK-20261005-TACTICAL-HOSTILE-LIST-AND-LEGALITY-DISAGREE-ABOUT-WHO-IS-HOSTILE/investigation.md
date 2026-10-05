---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20261005-TACTICAL-HOSTILE-LIST-AND-LEGALITY-DISAGREE-ABOUT-WHO-IS-HOSTILE
artifact_type: investigation
tags: [engine, combat]
---

# Investigation: do tactics and legality disagree about who is hostile?

Tree: `lane-a-sticky-attack-and-hostile-list` (`origin/main` `7a9f302db` + the router fix of
`TCK-20261005-SILENT-NO-OP-RETURNS-...`; it contains #344 and #347). Settings: real `Kernel.tick_once()`, seed 42, 2000 ticks,
`audit_mode=True`, `max_tick_budget_ms=1e9`, one simulation at a time, each world run twice. Every pair matched exactly, so the
figures are **values**. Probes: `probes/hostility_probe.py` + `measure.sh` (predicates), `probes/ff_origin.py` (who calls).

## What the code does (read, then measured)
- `tactical.py:243-249`: faction ids come from `EntityIdentityResolver` (catalog `faction_id`, then `runtime_faction_id`, then a
  legacy-enum projection), then `semantics_service.is_hostile_compat(src, tgt, context)`.
- `legality.py:223-272`: faction ids come from `get_faction_id_str`; a local `has_clean` probe (perspective of the attacker, or a
  relationship edge source->target) decides between `is_hostile_compat` and raw `attacker.identity.faction == target.identity.faction`.
- `is_hostile_compat` itself repeats the same probe and, when there is no clean data, falls back to the legacy bucket predicate
  `is_hostile`. So the no-clean fallbacks differ: tactics gets legacy-bucket semantics, legality gets raw enum equality.

## Result 1: the predicates do not disagree on corpus content (value)
| world | legality calls | FRIENDLY_FIRE_ILLEGAL | distinct entity pairs | pairs where tactical and legality predicates disagree | `has_clean` false (forward) | `has_clean` asymmetric |
|---|---|---|---|---|---|---|
| crowded_frontier | 291 | 211 (2 distinct pairs) | 11 | **0** | 0 | 0 |
| frontier_living_world | 429 | 372 (3 distinct pairs) | 14 | **0** | 0 | 1 call (predicates agreed) |
| urban_political | 76 | 0 | 5 | **0** | 0 | 0 |
| dungeon_crawl | 30 | 0 | 4 | **0** | 0 | 0 |
Scope 3 answered: **`has_clean` was never false on corpus content, so the raw-equality fallback is dead code on this corpus.** The
asymmetry is real in the code (the edge probe matches source->target only) and fired once in 4 x 2000 ticks, in a call where both
predicates agreed. My first-run counter `legality_pred_differs_by_direction` compared the reverse direction's hostility, which
differs by design; it is not the asymmetry test and is ignored.

## Result 2: the friendly-fire verdicts are not a hostility disagreement
The dominant row (372 calls, `frontier_living_world`) is `wild_beast_pack -> merchant_league`: both sides carry a catalog
`faction_id` (`clean_metadata`), `has_clean` is true both ways, and **both predicates say not hostile**. Legality is refusing a pair
that tactics also considers non-hostile. The planner's runtime-spawned-monster hypothesis (`MONSTER_HORDE` bucket equality) does not
explain it: those entities are not spawned monsters.

## Result 3: who asks (value; `ff_origin.py`, single run per world, matching the counting runs)
Every friendly-fire verdict (372 of 372 in `frontier_living_world`, 211 of 211 in `crowded_frontier`) is requested by
`CombatResolutionSystem.resolve_multi_attack` called from `resolve_move` / `route_movement_intent`: the **opportunity-attack scan during
movement resolution**. The attacker's task is `ENTITY_MOVE` (367 of 372 with reason `REGROUP`; 210 of 211 with none) or an idle
`ENTITY_ACT`. In none of them does an objective target the entity (`objective_targets_it = none`), and none comes from
`TacticalDecisionSystem` target selection. So the ticket's premise, "tactics selects a target that legality then refuses", is **not
what produces these verdicts**: a mover passing a non-hostile neighbour has its opportunity-attack candidates checked and legality
answers "not hostile", which is the filter doing its job. The same pair repeats (3 and 2 distinct pairs) because the same two
entities stay adjacent for many ticks.

## Result 4: the 751 (scope 2)
The original 751 was one pre-#344 run. On this tree the figure is 211 + 372 = **583** `FRIENDLY_FIRE_ILLEGAL` calls across the four
worlds (values), from 5 distinct entity pairs in total. Not a like-for-like comparison with 751 (different tree, different
trajectory). The figure counts a routine filter, not failed attacks.

## What the Bible says (scope 4)
Not needed for a decision, because no unification is proposed and no disagreement was found. **To cite if the question is reopened**:
`docs/mechanics/02_combat_laws.md` section 7 (the Friendly-Fire Law and the species-hostility escalation that feeds
`verify_attack_legality`) is the stated authority; the planner owns whether the two no-clean fallbacks should converge.

## Residual, honest
- The raw-equality fallback in `legality.py` is dead on this corpus but live in the code. It would diverge from tactics for a faction
  with no perspective and no edge (tactics: legacy-bucket `is_hostile`; legality: enum equality). That is a latent hazard, not a
  measured defect, and unifying it needs the planner's ratification per the ticket.
- The opportunity-attack scan asks legality for every adjacent neighbour every tick; 583 refusals is cost, not a correctness issue.
  Not measured: the cost.
- Runtime-spawned monsters carry only `compatibility_projection` identity (planner/Lane B's finding); one call in the sample had such a
  target (`monster_horde`), and the predicates agreed. The spawn defect is Lane B's ticket.
