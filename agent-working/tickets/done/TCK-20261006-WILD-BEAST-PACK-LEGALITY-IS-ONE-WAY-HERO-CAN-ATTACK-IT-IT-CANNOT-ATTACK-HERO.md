---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20261006-WILD-BEAST-PACK-LEGALITY-IS-ONE-WAY-HERO-CAN-ATTACK-IT-IT-CANNOT-ATTACK-HERO
phase: done
date: 2026-10-06
tags: [world, combat, legality]
---

# TCK-20261006-WILD-BEAST-PACK-LEGALITY-IS-ONE-WAY-HERO-CAN-ATTACK-IT-IT-CANNOT-ATTACK-HERO

## Title
A `wild_beast_pack` entity cannot legally attack a hero (`FRIENDLY_FIRE_ILLEGAL`) while a hero can legally attack it

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Found by `rpg-implementer-2` while mapping runtime-spawned wolves, bears and golems to `wild_beast_pack` (owner ruling 2026-10-06).
`LegalityServiceV2.verify_attack_legality` (`src/engine/legality.py:252-272`) resolves both faction ids from `identity.properties["faction_id"]`. The hero's perspective exists, so the check goes through `is_hostile_compat` and the catalog projection. `wild_beast_pack` is a *contextual threat* (alignment `wild`), hostile only once engaged or intruding.

Measured with the real legality service (`probes/host.py` in the spawn ticket's stored artifacts), hero at (5,5), monster at (6,5):
| monster carries | hero -> monster | monster -> hero |
|---|---|---|
| no `faction_id` (`MONSTER_HORDE` bucket) | legal | legal |
| `wild_beast_pack` | legal | **`FRIENDLY_FIRE_ILLEGAL`** |

**Live behaviour already affected on `main`:** every *compiled* `wild_beast_pack` entity behaves the one-way way today. Across the 24 corpus worlds at tick 0 there are **85** such entities in **13** worlds (`predator_hunter` 69, `alpha` 16; 10 each in `frontier_extended`, `frontier_living_world`, `frontier_marches`, `simq_scale_stress_seed42`; 5 each in `generated_frontier_3_42`, `highland_traverse`, `lifecycle_full_coverage_world`, `resource_dense_basin`, `sandbox_world`, `simq_routing_test`, `swamp_border_world`, `unit_faction_tension`, `wilderness_survival`). The spawn-faction batch holds spawned wolf, slime, bear, harpy and golem out so it does not extend the one-way behaviour (owner decision, option a).

## Scope
1. Open question for the designer and the owner: should a contextual-threat creature be able to start a fight with a hero? If yes, which of the predicate, `contextual_threat_groups` or the relationship rows changes; if no, say so in the catalog.
2. Measure how often compiled wild entities have a legal attack refused in the corpus (`FRIENDLY_FIRE_ILLEGAL` verdicts with a `wild_beast_pack` attacker).
3. Once resolved, map wolf, slime, bear, harpy and golem to `wild_beast_pack` in `SPAWN_KIND_CATALOG_FACTION` (`generator.py`) and give them NATURAL_TERRAIN endurance; the hostility pin test already covers hero<->wolf/bear/golem.

## Out of Scope
Routing spawned-monster hostility through catalog alignment without the above ruling.

## Acceptance Criteria
- [x] Owner/designer ruling recorded (memo row 18, CONFLICT-03 and its three-case resolution clause; planner sign-off 2026-10-07 for the 6 non-wild flips).
- [x] Legality and catalog agree in both directions for wild creatures (and for every faction pair: 108 asymmetric verdicts -> 0).
- [x] Held-out kinds mapped, pin test green.

## Related Tickets
- `TCK-20261005-SPAWN-MONSTER-STRIPS-CATALOG-FACTION-FROM-EVERY-RUNTIME-SPAWNED-MONSTER` (DEV-015 records the held-out kinds)
- `TCK-20261005-TACTICAL-HOSTILE-LIST-AND-LEGALITY-DISAGREE-ABOUT-WHO-IS-HOSTILE`

## Related Code Areas
`src/engine/legality.py:252-272`, `src/content_semantics/faction.py` (`is_hostile_compat`), `data/content/social/perspectives.yaml`, `data/content/social/faction_relationships.yaml`.

## Assumptions / Open Questions
Resolved by the designer under owner delegation (CONFLICT-03).

## Implementation Notes
`LegalityServiceV2._attack_permitted` (with `_declares`) replaces the attacker-only faction check in `verify_attack_legality` under the designer's three-case rule (both declare: either hostile; exactly one declares: its verdict decides both directions; neither: legacy fallback). A first full-union attempt broke the ratified defected-NEUTRAL pin and was replaced. `SPAWN_KIND_CATALOG_FACTION` maps wolf/slime/bear/harpy/golem to `wild_beast_pack`. Divergence DEV-016; parity COMB-334; Bible 02 Friendly-Fire Law rewritten. Perf: the symmetric change adds no per-call cost; the cost step is isolated in the investigation and left to `TCK-20261006-COMBAT-ENGAGEMENT-HOSTILITY-PROJECTION-COST-STEP`.

## Test Summary
236 passed across tests/unit/combat, tests/integration/combat, tests/integration/pipeline/test_combat_legality_matrix.py, test_legality_faction_mutation.py, test_spawn_monster_catalog_faction.py (24), relation/faction coverage tests; the new symmetric tests fail on the old legality (4 failed). Measurements: see the stored investigation.

## Files Changed
src/engine/legality.py, src/systems/world_systems/generator.py, tests/unit/world/test_spawn_monster_catalog_faction.py, docs/mechanics/02_combat_laws.md, docs/guidelines/intentional_divergences.md, docs/parity_ledger/combat_movement.yaml, this ticket, stored artifacts.

## Completion Summary
Permission to attack is symmetric. 16 directed pairs became legal (10 wild_beast_pack, 6 non-wild), 15 became illegal (all exactly-one-declared pairs; neutral may no longer attack a hero). Corpus: deaths 131 -> 130, live neutral -> hero attacks lost 0. Not attributed: hazard-death rise in frontier_marches/swamp_border_world. Open for the planner: movement[5000] bench not run (10-minute pytest timeout).
