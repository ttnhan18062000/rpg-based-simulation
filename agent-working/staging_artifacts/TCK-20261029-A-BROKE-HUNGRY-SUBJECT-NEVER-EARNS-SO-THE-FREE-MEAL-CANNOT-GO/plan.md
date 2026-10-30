---
status: active
layer: economy
authority: P2
audience: agent
ticket_id: TCK-20261029-A-BROKE-HUNGRY-SUBJECT-NEVER-EARNS-SO-THE-FREE-MEAL-CANNOT-GO
artifact_type: plan
tags: []
---

# Plan (designer rulings 2026-10-29 and 2026-10-30 supersede the ticket Scope where they differ)
1. Failing real-kernel scenario first (owed scenario l.1015): a broke hungry worker beside the inn, payment law ATOMIC, the core EAT free relief off (named fixture `no_free_meal_d73_shape`): red (idle beside the inn, hunger 50 -> 90, gold 0), green after the fix.
2. `building_arrival` derives the action from the building and `admits`: meal -> EAT; a building that offers a shift the subject can take -> WORK with `shift_start`; a present threat only -> nothing dispatched, hunger project untouched; otherwise the existing `_end_project`.
3. `work_shift.shift_takeable` = no present threat (`work_wake.held_work_is_threatened`) AND alive at the meal: ticks_to_meal (`need_pull.step_travel_tiles`) minus ticks_before_line = (STARVING_LINE - hunger)/rate, lost hp = ticks_past_line / `starvation.hp_loss_period`, takeable while hp - lost > 0. Read by `work_in_reach` (open step, `ways_in_reach`) and the arrival.
4. The pull escalates over the whole step (walk + SHIFT_TICKS + walk on): `OpeningStep.ticks_at_target` / `onward_pos`, `step_travel_tiles`.
5. A held WORK is woken by a present threat only (`scheduler._is_need_woken` -> `work_wake`); the wage is forfeited; hunger does not wake it; other held actions unchanged.
6. Import structure: `need_wake.py` (leaf constant), `work_wake.py`, `tactical_threat.perceived_threats` (moved), to satisfy lint-imports and the ruff ceilings.
7. Docs: Bible 04 (designer's text verbatim), divergence 2.151, parity STRAT-291, mechanisms (`town_services`, `goal_hierarchy`, `tactical_decision` listing), completeness pins.
8. Measure: paired run on main (expect identical), D73-shape probe (throwaway flip) for shifts/person-day, crowd-out, N1, outcome split.
