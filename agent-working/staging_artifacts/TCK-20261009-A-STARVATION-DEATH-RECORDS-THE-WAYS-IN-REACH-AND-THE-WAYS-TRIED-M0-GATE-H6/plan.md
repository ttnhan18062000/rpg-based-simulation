---
status: active
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20261009-A-STARVATION-DEATH-RECORDS-THE-WAYS-IN-REACH-AND-THE-WAYS-TRIED-M0-GATE-H6
artifact_type: plan
tags: []
---

# Plan (investigation and plan only; code is cut from origin/main after the folded RPG PR merges)

## Option A (recommended): observational record built in the run output, no new authoritative state
- A typed `StarvationDeathRecord` (frozen dataclass in `src/observability/`, not in state.py): subject id, kind, tick, `cause_tick`, `ways_open_in_reach` (tuple of `WayKind`), `ways_attempted` (tuple of `WayKind`), `last_meal_tick`. `WayKind` is a str Enum: CARRIED_FOOD, INN_MEAL, FORAGE, BUY (shop sale then meal), WORK_SHIFT, HUNT_EAT_RAW, RECEIVE (the last two declared but empty until those ways exist; diet-restricted kinds list only their ways).
- Emitted by the event extractor on the fatal tick (`passive_death_cause == STARVATION` and `passive_death_cause_tick == tick`) as a typed event; deterministic (pure function of the prior state and the tick's updates).
- Column (a)/(b): at the fatal tick the extractor calls the SAME way functions the scorer uses (one new pure helper `ways_in_reach(entity, state) -> tuple[WayKind, ...]` in `src/ai/goals/opening_steps.py` or a sibling, refactored out of the scorer so scorer and record cannot diverge) on the state BEFORE the tick. Today (a) == (b); the record carries both columns and a test pins that they are equal until honest perception exists (then (a) is computed from the perceived set and (b) stays on the world).
- `ways_attempted`: the extractor keeps a bounded, non-authoritative per-subject set since the last meal, fed by the accepted/rejected transfers it already sees each tick (NODE/AUTO, TOWN_SERVICE/EAT, CARRIED_FOOD/EAT, SHOP_SELL, WAGE and the WORK/SELL action starts). It is rebuilt from the event stream, so it is deterministic and costs no state field; it resets on a meal.
- No change to need-pull or way selection (observational only), no state.py, no apply.py edit (apply.py already writes the typed cause), so no Phase B dependency and no field to ask rpg-planner about.
- Aggregator: an `h6_untried_way_in_reach(records, broke_workers)` query in the gate aggregator module runs from the records alone.

## Option B (only if rpg-planner wants it durable): a bounded trail on the entity
A `WayJudgement(tick, open: tuple[WayKind], chosen: Optional[WayKind])` ring buffer (N=8) on `BiologicalComponent` plus `ways_tried: frozenset[WayKind]` reset on a meal. Needs state.py and canonical dict changes, touches the Phase B held files, changes every state hash. Costs more and records only sparse decision-time judgements. Not recommended unless the gate must survive without event output.

## Out of scope / ordering
- The metric module follows H6. SURV-07's hunger-pull fix (Lane A) lands first so the (a) column reflects the fixed pull; Option A reads the same scorer helper so it follows automatically.
- Typed shape needs rpg-planner's yes before building (stated in the message); nothing is built now.
