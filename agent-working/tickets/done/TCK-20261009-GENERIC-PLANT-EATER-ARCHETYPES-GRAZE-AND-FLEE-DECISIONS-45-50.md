---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20261009-GENERIC-PLANT-EATER-ARCHETYPES-GRAZE-AND-FLEE-DECISIONS-45-50
phase: done
date: 2026-10-09
tags: []
---

# TCK-20261009-GENERIC-PLANT-EATER-ARCHETYPES-GRAZE-AND-FLEE-DECISIONS-45-50

## Title
A first generic plant-eater (a small creature that grazes the land's plant food and keeps away from or flees what could eat it), so meat-eaters have something to hunt and people have game (owner decisions 45 and 50; no named species).

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
The corpus had 13 kinds and no plant-eater, so a meat-eater had no game. Decision 45 asks for one or two generic plant-eaters; decision 50 forbids named real species and exact figures (coarse bands, tests on stage order and relations); decision 46 forbids a prey label. Part 3 of LB-S21 (individual births, ECOL-03) is split into its own later ticket.

## Scope
1. Content: faction `wild_fauna` (alignment wild, hostile to nobody), species `small_plant_eater` (size small, power small, believed danger low, diet plant, meat yield 1), body model, need, sense and drive profiles, stat, combat and skill profiles, archetype, and a herd of 6 in `wolf_den_near_forest` and its ecology. 2. Behaviour: WARY keep distance (`KEEP_DISTANCE`) and THREATENING flee (`AVOID_HOSTILE`) in the tactical pass; neither enters the hostile list; grazing is the existing forage way with the plant diet. 3. LB-S21 parts 1 and 2 (graze, avoid, sated-wolf and unperceived controls), the positive wolf-PREDATION-from-compiled-content test. 4. The camp spawns the kind it declares (content `camp_spawn_kind`). 5. LB-S18's second-kind arm on the wolf. 6. Regenerated the 24 composed worlds' `resolved/` snapshots.

## Out of Scope
- A second archetype; individual births and deaths of game (ECOL-03); cooking; people hunting for sale.

## Acceptance Criteria
- [x] The plant-eater exists in the worlds that compose the wolf-den module, grazes (gathers and eats plant food), keeps away from a wolf it cannot overcome and flees one coming for it.
- [ ] STOP LINE, reported not tuned: it does not persist. In every seed of every measured world it is gone by tick 1750. Causes found: raiders kill it (FACTION_HOSTILE by goblin and bandit factions), a flee defect in this feature (fixed after the measurement), the sleep-deprivation drain that kills every kind at about tick 2000 (labelled STARVATION), and a food supply of one berry node (grazing the land's plant cover is not modelled). The owner rules.
- [x] A hungry wolf gets PREDATION on it as compiled from content; the plant-eater is WARY of the wolf; a sated wolf does not hunt it and it still keeps its distance (prey never reads hunger).

## Related Tickets
- TCK-20261009-A-KILL-LEAVES-MEAT-AND-A-CARNIVORE-EATS-IT-RAW-WITH-A-DIET-GATE-DECISION-44 (same batch). The next batch holds the held-action fix (a gatherer on a regrowing node holds its INTERACT forever).

## Related Docs
- `docs/guidelines/intentional_divergences.md` 2.104; `docs/world_rules/scenarios/life-body-batch-05.md` LB-S21.

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261009-GENERIC-PLANT-EATER-ARCHETYPES-GRAZE-AND-FLEE-DECISIONS-45-50/`

## Related Code Areas
- `data/content/**` (faction, species, body, profiles, archetype, population, ecology, module), `src/engine/tactical_avoid.py`, `src/engine/tactical.py`, `src/world/camp.py`, `data/worlds/*/resolved/*`.

## Assumptions / Open Questions
- Plant-eaters must not share a faction with the meat-eaters that eat them (the same-faction rule would silently stop every hunt): `wild_fauna` is alignment "wild", so no faction is hostile to it.
- The folk-belief test now lists `small_plant_eater` as declared "low".
- Berry competition between people and plant-eaters is disclosed (people gathered 0 to 4, plant-eaters 3 to 8 per run).

## Implementation Notes
See TCK-20261009-A-KILL-LEAVES-MEAT-AND-A-CARNIVORE-EATS-IT-RAW-WITH-A-DIET-GATE-DECISION-44.

## Test Summary
Focused: `tests/unit/engine/test_appraisal.py`, `test_carcass_and_meat.py`, `tests/unit/ai/test_hunt_steps.py`, `tests/unit/content/test_kind_properties.py`, `tests/unit/world/test_camp_lifecycle.py`, `tests/mechanic_scenarios/test_hunting_kill_to_meat.py`, `test_plant_eater_graze_and_avoid.py`, `test_starvation_over_days.py`; architecture guards; code health, mypy, import contracts; full sweep (results in the PR).

## Files Changed
See `git diff origin/main --stat` of the batch PR.

## Completion Summary
A generic small plant-eater is in the corpus and behaves (graze, keep distance, flee), but its population does not survive 1750 ticks in any measured world: a stop line for the planner.
