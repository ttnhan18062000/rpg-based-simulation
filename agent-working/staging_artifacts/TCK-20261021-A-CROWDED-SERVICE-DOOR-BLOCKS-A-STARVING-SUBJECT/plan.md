---
status: active
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20261021-A-CROWDED-SERVICE-DOOR-BLOCKS-A-STARVING-SUBJECT
artifact_type: plan
tags: []
---

# Plan: N14 F1 (2.153 / STRAT-293) and the sleeper threat wake (2.154 / STRAT-294)

Designer rulings 2026-10-30 (seat f1cb479cf, 569103d44, ee2232bd2); owner go #715 6521119624. F2, F3, the nav family and A' are out of scope.

## Design
1. `src/engine/sleep_debt.py`: `REST_MIN_SLEEP_DEBT` (moved from `tactical_rest.py`, re-exported there), `chosen_rest_is_met(debt)` = debt strictly below the floor, `rest_ended_at_the_floor(entity)`.
2. `src/engine/pipeline_phases/actions.py::_survival_action_ends`: a collapse (COLLAPSE_FLAG) keeps `is_rested_enough`; a chosen SLEEP/REST ends at `chosen_rest_is_met`.
3. Floor-end brain wake (folded into 2.153, no new id): `scheduler._critical_item` counts `rest_ended_at_the_floor` as a wake; `fused_strategic_pass` adds such entities to the candidates and evaluates their intents off cadence, so `intelligence.py` completes the fatigue project on the tick after the rest ends.
4. 2.154: `scheduler._threat_wakes_sleeper` in the `is_asleep` branch of `_is_need_woken`: on decision 32's cadence, an unengaged adjacent hostile or `acting_threat_to`; `wake_index` passed as a plain argument.
5. Docs: divergences 2.153 and 2.154, parity STRAT-293 and STRAT-294, mechanisms.yaml bindings and notes (planner's text), Bible 04 line-38 paragraph (designer's final text, committed only after the paired run clears the STOP checks).

## Decisions
- Strictly below 20, not at or below: project completion and the goal exit are both `< 20.0`.
- `acting_threat_to` is not widened (it gates need escalation, row 88); the saliency-cap gap is measured, not closed.
- `evaluate_all_strategic_intents` is not changed: the live pipeline runs `fused_strategic_pass`.
