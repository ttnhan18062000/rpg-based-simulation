---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20261009-A-KILL-LEAVES-MEAT-AND-A-CARNIVORE-EATS-IT-RAW-WITH-A-DIET-GATE-DECISION-44
phase: done
date: 2026-10-09
tags: []
---

# TCK-20261009-A-KILL-LEAVES-MEAT-AND-A-CARNIVORE-EATS-IT-RAW-WITH-A-DIET-GATE-DECISION-44

## Title
Hunting: a body leaves raw meat, a hungry meat-eater hunts and scavenges and eats it where it lies, and a diet gate lets each kind eat only what its diet allows, so meat-only kinds stop taking the inn's meal (owner decisions 44 to 49).

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Owner decision 44 (the user decided directly, 2026-10-09): the free-meal removal waits for the animals' own ways. Before: no meat, no carcass food, no eat-corpse action; meat-only kinds ate by walking to an inn. Decisions 46 to 49 bind it: kinds declare properties only (no predator, prey, grazer or hunter label); hunting is derived from diet, edibility and the believed danger of the kind; a kill to eat is not trauma; a wary creature keeps its distance and a threatened one flees.

## Scope
1. Content: coarse size, power and wits bands and diet, edibility and meat yield per kind (commit i). 2. `appraisal.py` and `hostility.relation` (FACTION_HOSTILE > PREDATION > THREATENING > WARY > NONE), the attack permission for PREDATION and for self-defence, the `AVOID_NO_ROUTE` hold (commit ii). 3. Raw meat on the corpse at death, the `raw_meat` item, the diet gate, eat at the carcass (`CORPSE_FOOD`), the `SCAVENGE` and `HUNT` ways to eat inside the leash (commit iii). 4. The kill-to-eat trauma exemption derived at the trauma site, the `FEEDING_KILL` and `MEAT_DECAYED` records, the killing blow ends the held attack (commit iv). 5. LB-S20 kernel scenario, Bible 03 section 3.2, parity `TOWN-205`, divergence 2.104, pinned measurement.

## Out of Scope
- Cooking and the cooked equivalent of raw meat (M3); people hunting for sale; the free-meal removal (landed by batch 2); individual births of game (ECOL-03); the body-signal defaults move (deferred, behaviour-neutral).

## Acceptance Criteria
- [x] A hungry meat-eater kills a creature it appraises as prey, a carcass with meat appears, it eats it and its hunger falls by the meat's value (LB-S20 main); a fed one hunts nothing (control); one beside a kind it believes more dangerous does not (derivation); a meat-only kind forages no berries (diet).
- [x] Meat enters only from a body at death and leaves only by being eaten at the corpse, looted or decayed; the balance residual is 0 in every measured run.
- [x] Hard zeros: wolf and spider inn meals 0 in all three measured worlds (spider 0.4 in one), wolf berry foraging 0. Wolf attacks on people do not rise.
- [x] A kill to eat adds no trauma and leaves a typed `FEEDING_KILL` record; killing a person a faction rates hostile still does.

## Related Tickets
- TCK-20261009-GENERIC-PLANT-EATER-ARCHETYPES-GRAZE-AND-FLEE-DECISIONS-45-50 (same batch). TCK-20261009-CAMPAIGN-EPISODE-DELIBERATE-ATTACKS-STRICT-XFAIL-DEPENDS-ON-TEST-ORDER (pre-existing failure on main).

## Related Docs
- `docs/mechanics/03_economic_laws.md` section 3.2; `docs/guidelines/intentional_divergences.md` 2.104; parity `TOWN-205`.

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261009-A-KILL-LEAVES-MEAT-AND-A-CARNIVORE-EATS-IT-RAW-WITH-A-DIET-GATE-DECISION-44/`

## Related Code Areas
- `src/engine/appraisal.py`, `hostility.py`, `carcass.py`, `tactical_avoid.py`, `tile_distance.py`; `src/ai/goals/opening_steps.py`; `src/core/conservation.py`; `src/engine/domain/core_actions.py`; `src/engine/world_dynamics.py`; `src/engine/pipeline_phases/actions.py`; `data/content/living/*.yaml`, `data/content/world/items.yaml`.

## Assumptions / Open Questions
- **D44's "posture verdict" is implemented as the same KNOW-04 capability prior, read directly rather than through `last_combat_posture`** (planner ruling): `can_overcome` is the subject's own power band strictly above the danger it believes the other's kind poses; a tie is "cannot". M0 shortcut, closed by Milestone 1's one-appraisal child (individual condition and groups come there).
- The kill-to-eat exemption is derived at the single trauma site instead of a new outcome kind (rpg-planner accepted, with the `FEEDING_KILL` record).
- Any death leaves meat (a body is a body); a faction never hunts its own members and a kind never regards its own species as prey or danger (no cannibalism in M0).
- A small-power meat-eater can overcome nothing, so the Cave Spider only scavenges in M0 (disclosed verbatim in 2.104).

## Implementation Notes
Eight local commits over the batch, rebased twice (batch 2, then Phase B). The measurement is at `origin/main` `9f9514ead` against the batch before the final rebase and the one-stride eat reach, so it is indicative of the mechanism, not of the final head.

## Test Summary
See the batch Test Summary in TCK-20261009-GENERIC-PLANT-EATER-ARCHETYPES-GRAZE-AND-FLEE-DECISIONS-45-50 and divergence 2.104: focused suites, the architecture guards, the full sweep, code health, mypy and import contracts all green except the one pre-existing failure.

## Files Changed
See `git diff origin/main --stat` of the batch PR.

## Completion Summary
Landed with TCK-20261009-GENERIC-PLANT-EATER-ARCHETYPES-GRAZE-AND-FLEE-DECISIONS-45-50: properties, appraisal, meat, the diet gate, hunting and scavenging, the feeding-kill record and the measurement.
