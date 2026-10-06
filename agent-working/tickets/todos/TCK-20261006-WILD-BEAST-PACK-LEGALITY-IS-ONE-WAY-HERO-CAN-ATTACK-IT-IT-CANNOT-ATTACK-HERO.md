---
status: active
layer: world
authority: P2
audience: agent
ticket_id: TCK-20261006-WILD-BEAST-PACK-LEGALITY-IS-ONE-WAY-HERO-CAN-ATTACK-IT-IT-CANNOT-ATTACK-HERO
phase: open
date: 2026-10-06
tags: [world, combat, legality]
---

# TCK-20261006-WILD-BEAST-PACK-LEGALITY-IS-ONE-WAY-HERO-CAN-ATTACK-IT-IT-CANNOT-ATTACK-HERO

## Title
A `wild_beast_pack` entity cannot legally attack a hero (`FRIENDLY_FIRE_ILLEGAL`) while a hero can legally attack it

## Status
OPEN

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
- [ ] Owner/designer ruling recorded.
- [ ] Legality and catalog agree in both directions for wild creatures.
- [ ] Held-out kinds mapped, pin test green.

## Related Tickets
- `TCK-20261005-SPAWN-MONSTER-STRIPS-CATALOG-FACTION-FROM-EVERY-RUNTIME-SPAWNED-MONSTER` (DEV-014 records the held-out kinds)
- `TCK-20261005-TACTICAL-HOSTILE-LIST-AND-LEGALITY-DISAGREE-ABOUT-WHO-IS-HOSTILE`

## Related Code Areas
`src/engine/legality.py:252-272`, `src/content_semantics/faction.py` (`is_hostile_compat`), `data/content/social/perspectives.yaml`, `data/content/social/faction_relationships.yaml`.

## Assumptions / Open Questions
Lane B with the designer. World-rule question, not mine to rule.

## Implementation Notes
(to be filled by the implementer)

## Test Summary
(to be filled by the implementer)

## Files Changed
(to be filled by the implementer)

## Completion Summary
(to be filled by the implementer)
