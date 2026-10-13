---
status: active
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20261009-A-STARVATION-DEATH-RECORDS-THE-WAYS-IN-REACH-AND-THE-WAYS-TRIED-M0-GATE-H6
artifact_type: investigation
tags: []
---

# Investigation: what exists today for H6 (2026-10-11, origin/main 9a9058808)

## Answer to the open question: is the per-decision "open and in reach" way set kept anywhere?
No. It is computed and thrown away, and it is not a set.
- `src/ai/goals/scorers.py::EatScorer.score` decides one hunger `GoalScore` per strategic evaluation. The inn way is tested inline (`nearest_building(.., "inn")` then `way_in_range`); when it is not open, `_hunger_without_open_way` calls `opening_steps.first_open_step`, which evaluates FORAGE, EARN_THEN_BUY and ASK (each an `OpeningStep` with `available` and a reason) and keeps only the FIRST open one. The `GoalScore` carries `need_access` (WAY_WITHIN_REACH / NO_WAY_WITHIN_REACH / NO_AFFORDABLE_WAY), `opening_step` and `no_open_step`.
- `GoalRegistry.get_all_scores` returns the scores to `StrategicIntelligenceSystem` (intelligence.py ~1541); the winning score becomes a project/objective with a target; nothing copies `need_access`, `opening_step` or the other open steps into `ObjectiveState`, `ProjectState`, the entity or any event. The only trace of the losers is a `logger.debug` line with `kind:utility`. `need_access` and `opening_step` are read only by tests (`tests/unit/ai/test_need_scorers.py`, `test_opening_steps.py`).
- The evaluation is not per tick: it runs when the strategic layer re-decides (held objectives are not re-scored), so even a log of "the last decision" is a sparse series, not the state at death.
- Not all ways are in the scorer at all. Carried food is eaten by the action layer (`CARRIED_FOOD/EAT`), the inn meal by `TOWN_SERVICE/EAT`, forage is NODE/AUTO harvest, selling is `SHOP_SELL`, a shift is `WAGE`. SURV-06's hunt+eat-raw and receive ways do not exist yet (batch 4 of Lane A, and a social path).

## What is already typed at the death
- `apply.py` (~line 115): the passive death cause is recorded at the writer on the fatal tick as `LifecycleComponent.passive_death_cause = PassiveDeathCause.STARVATION` with `passive_death_cause_tick`. Since decision 41 sleep debt costs no health, hunger is the only passive drain, so the mislabel the ticket warned about (sleep-deprivation deaths labelled STARVATION) cannot occur on main; Lane C's cause fix is already in. The record can key off `passive_death_cause == STARVATION` (the typed source of the last HP loss).
- The "ways tried" side is observable: every attempt that reaches the resolver is an accepted/rejected transfer with a `(source_kind, transfer_kind)` (the same pairs the pinned measurements count: CARRIED_FOOD/EAT, TOWN_SERVICE/EAT, NODE/AUTO, SHOP_SELL, WAGE).

## Consequences for the design
1. Column (a) (what the pull judged open) cannot be read at death from anything kept; it has to be captured at decision time or recomputed.
2. Recomputing at death from the prior state with the current scorers (`opening_steps(entity, state)` plus the inn test) gives the TRUE-MAP answer for the state at the fatal tick. Until M1's honest-perception child lands, column (a) IS the true map (the ticket says so), so recomputation equals (a) today and (b) always; it stops being (a) when perception lands.
3. "Tried" needs history since the last meal (a set that survives many ticks), which is either durable state or derived from the event stream.
