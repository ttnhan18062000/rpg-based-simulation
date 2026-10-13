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

## Ruling (rpg-planner, 2026-10-11): Option A accepted, Option B rejected, with four amendments
1. Column (a) is the UNION of `ways_in_reach` over the subject's decisions since its last meal while hunger >= ESCALATION_ONSET x HUNGER_LINE, sampled on the ticks where `should_run(tick, entity_id, cadence.strategic_intelligence)` holds (the strategic re-decision ticks: (tick + id) % 10 == 0 at the default cadence; computable by the extractor, no decision-tick visibility needed; if the profile overrides the cadence the extractor reads it from the kernel profile when reachable). The record carries `ways_open_in_reach_union`, `ways_in_reach_at_death` and `ways_attempted`; all reset on a meal.
2. `ways_in_reach` covers HUNT_EAT_RAW by diet (D42) once Lane A's hunting batch is on main (test with a meat-eater); RECEIVE is a declared enum value never returned until it exists (disclosed).
3. The extractor runs in rpg_gate runs (plain Kernel, audit_mode, default LIGHT observability; events flush to `data/runs/<run_id>/simulation_events.jsonl` = `RunArtifacts.run_dir`). To verify at build: LIGHT's volume policy cannot drop the record; the gate environment does not set SIM_OBS_MODE=OFF.
4. The (a)==(b) pin stays, commented as split only by M1's honest-perception child.
Extractor state (union and attempted sets) is class-level like `_emitted_*`; cleared in `reset_run_state`; deterministic across two runs. Build after the folded RPG PR merges, cut from origin/main.
5. (rpg-planner addition) NO-DATA, never zero: the run writes a typed liveness marker for the starvation-record channel: a `StarvationChannelLive` header event at run start and, at shutdown, a count of starvation deaths the extractor saw (`starvation_deaths_seen`); a run with seen deaths and fewer records, or no header (observability OFF, path missing), is detectable. The metric module maps "channel not live" to the no-data reason `harness_error`. Test: an OFF-mode run and a run with the record path disabled both read as channel-not-live, a normal run reads live with records == deaths seen.
