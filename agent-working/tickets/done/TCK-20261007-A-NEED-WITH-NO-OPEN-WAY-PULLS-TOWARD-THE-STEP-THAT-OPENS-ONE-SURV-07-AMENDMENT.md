---
status: historical
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20261007-A-NEED-WITH-NO-OPEN-WAY-PULLS-TOWARD-THE-STEP-THAT-OPENS-ONE-SURV-07-AMENDMENT
phase: done
date: 2026-10-07
tags: []
---

# TCK-20261007-A-NEED-WITH-NO-OPEN-WAY-PULLS-TOWARD-THE-STEP-THAT-OPENS-ONE-SURV-07-AMENDMENT

## Title
When none of a hungry subject's ways is open to it now (for example, it cannot pay for the inn meal), its escalated pull goes to the step that opens one: forage or harvest where its kind can, earn and then buy, or ask where a social path exists (decision 27, SURV-07 amendment).

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Found in Lane A's SURV-07 trace on urban_political, seed 42. All 5 hunger-goal defeat deaths were walking to the inn without the 5 gold for a meal; 4 of them had 0 gold. SURV-07 (`TCK-20261007-BIOLOGICAL-NEEDS-ESCALATE-ABOVE-ORDINARY-GOALS-BEFORE-THE-CONSEQUENCE-LINE-SURV-07`) fixed the futile walk: the inn is offered only to a subject that can pay, per subject (AGENCY-03), and the need is reported as unmet. That leaves a poor subject's need as a countdown timer. The economy never feels hunger.

**Decision 27** (rpg-designer under owner delegation, 2026-10-07) amends SURV-07: "The pull is toward meeting the need, not toward one building. When none of the subject's ways is open to it now, the pull goes to the step that opens one: foraging or harvesting where its kind can, earning where it has paid work and then buying, or asking where a social path exists. Only ways SURV-06 declares for its kind count, and only steps the subject can actually take. A present threat still outranks it. Opening a way is attempted, not guaranteed: a subject with no step it can take stays honestly hungry, and that is SURV-06's poverty outcome."

## Scope
1. The FIRST commit is the designer's decision-27 patch (SURV-07 amendment plus memo row 27). It is cut from this branch's base.
2. With the hunger pull escalated and no open way, score the opening steps the subject can actually take: forage or harvest (where its kind can and a node is reachable), paid work toward the meal price followed by buying, and asking where a social path exists. A present threat gates the pull, as in SURV-07.
3. Make "need pressing, no step available" a typed, inspectable state (durable-state rule), never only a reason string.
4. Measure on the 5-seed bar (seeds 42-46, all three corpus worlds, 1500 ticks) against SURV-07's landed main. Report starvation, total deaths, alive at t=1000 and t=1100, and the counts of each opening step taken.

## Out of Scope
- Any new acquisition mode: theft, raiding, coercive begging, or looting the living. Each would need its own declared Rule.
- Engine charity.
- Changing SURV-06's world-integrity check, which stays per kind and must never become "every subject can afford it".

## Acceptance Criteria
- [x] Decision-27 patch is the first commit.
- [x] A subject with no way within reach pursues an available opening step (forage), and a constructed test covers it; the earn and ask steps are stubs that report why they are closed. A subject that merely cannot pay still reaches the inn while free meals stay on (owner ruling 2026-10-08); the typed `NO_AFFORDABLE_WAY` is defined and produced by the parked removal.
- [x] The no-step case is a typed state (`no_open_step`, `NeedAccess`) that shows in the funnel (`need_paths` report).
- [x] The 5-seed measurement is reported (divergence 2.91, 5000 ticks, free meals on): no collapse, survivors at tick 5000 equal to main within 1 SD. The forage step is dormant in the three measured worlds (a subject with an inn goes to the inn), so the starvation-goes-down claim could not be shown there; the starvation effect with the removal on is parked evidence and the Decision 31 bar was not met.

## Related Tickets
- `TCK-20261007-BIOLOGICAL-NEEDS-ESCALATE-ABOVE-ORDINARY-GOALS-BEFORE-THE-CONSEQUENCE-LINE-SURV-07` (prerequisite)
- `TCK-20261007-SHOP-AND-BLACKSMITH-TOWN-PATHS-NEVER-RAN-IN-A-COMPILED-WORLD` (the buy path)
- `TCK-20261007-EPIC-DECISION-CORE-LIVE-MOTIVATION-AND-HONEST-FIGHT-OR-FLEE-INPUTS` (parent epic)
- `TCK-20261007-EAT-BESIDE-THE-INN-FEEDS-A-SUBJECT-THAT-CANNOT-PAY-FREE-MEAL` (the parked free-meal removal)
- `TCK-20261008-ENV-08-SETTLED-LAND-AND-THE-NEAR-WILD-CARRY-NO-STANDING-AMBIENT-HAZARD`, `TCK-20261008-LIGHT-BALANCE-PASS-HUMAN-HUNGER-IS-LOW-DECISION-33` (same batch)

## Related Docs
- `docs/world_rules/life-body/survival-needs.md` (SURV-03, SURV-06, SURV-07); AGENCY-03; memo rows 23, 24 and 27.

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261007-EAT-BESIDE-THE-INN-FEEDS-A-SUBJECT-THAT-CANNOT-PAY-FREE-MEAL/probes/` (forage probe, pinned rows, traces, 5000-tick rows); `agent-working/stored_artifacts/TCK-20261007-A-NEED-WITH-NO-OPEN-WAY-PULLS-TOWARD-THE-STEP-THAT-OPENS-ONE-SURV-07-AMENDMENT/` (investigation, plan, test plan).

## Related Code Areas
- `src/ai/goals/scorers.py`, `src/engine/need_pull.py`, `src/engine/town_resolution.py`, harvest and work scorers.

## Assumptions / Open Questions
- Engineering decisions: how far ahead "in time" allows for a multi-step way, the order among steps, how earning is scored against the escalated need, and when the subject gives up.

## Implementation Notes
Opening steps (`src/ai/goals/opening_steps.py`: forage open when a food node with charges and room to carry exists; earn-then-buy and ask are stubs with a reason), typed `NeedAccess` and `no_open_step` on `GoalScore`, `EatScorer` routes a subject with no inn within reach to the step, the hunger pull (`need_pull`) escalates by the hunger on arrival; `need_paths` counts food nodes. Carried food: core `EAT` with food in the bag consumes one item through a `CARRIED_FOOD` transfer, and a hungry subject with food eats it in place (`tactical_rest`). Decision 29 wild food: `berry_thicket` kind and `wild_berries` item, declared per wild module (near forest and sacred grove 10 charges, swamp border 8), `placement: owned_by_declared_region` resolved at compile by region ownership. Helpers extracted to keep the ratchet clean (`_reward_result`, `_carried_food_result`, `_resource_profile`, `_draw_tile_owned_by`, `_widen`). The free-meal removal was split out by owner ruling and is parked on `d27-free-meal-removal`.

## Test Summary
New or updated: `tests/unit/ai/test_opening_steps.py`, `tests/unit/ai/test_need_scorers.py`, `tests/unit/engine/test_biological_needs.py`, `tests/unit/engine/test_eat_carried_before_travel.py`, `tests/unit/resource/test_conservation_rejection_paths.py`, `tests/unit/worldbuilding/test_wild_food_node.py` (88), `tests/mechanic_scenarios/test_forage_loop_wild_food.py` (LB-S17, 5), plus the shared SPC-S16. Gates: ratchet 0 new 0 worse, mypy clean, import-linter 17/0. Placement rule proof: 24 resolved worlds at seeds 42 and 43 identical apart from the food node. 5000-tick pinned 5x3 in divergence 2.91.

## Files Changed
`src/ai/goals/{base,opening_steps,scorers}.py`, `src/engine/{need_paths,tactical_rest,tactical}.py`, `src/engine/domain/core_actions.py`, `src/core/{conservation,items}.py`, `src/content/schema.py`, `src/worldassembly/{context,models,resolver}.py`, `src/worldbuilding/compiler.py`, data (`items.yaml`, `materials.yaml`, `resources.yaml`, `ecologies.yaml`, three world modules), 24 resolved worlds, tests listed above, divergence 2.91, parity TOWN-198, TOWN-199, STRAT-281, Bible 03, mechanism notes.

## Completion Summary
The opening-step framework, carried-food eating and Decision 29 wild food landed with free meals still on (owner ruling 2026-10-08). 5000-tick pinned result: no collapse against main; the forage mechanism is dormant in the three measured worlds and pinned by LB-S17, the node tests and inn-less worlds. The free-meal removal is parked; Decision 31's bar (a second way to eat in all three worlds) is not met and goes to the owner with the parked evidence.
