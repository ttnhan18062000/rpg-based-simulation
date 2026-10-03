---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260904-TEMPORAL-FANTASY-YEAR-AGING-MIGRATION
artifact_type: plan
tags: [determinism]
---

# Plan — TCK-20260904-TEMPORAL-FANTASY-YEAR-AGING-MIGRATION

1. Add `src/core/calendar.py`: named constants `TICKS_PER_DAY=2400`, `DAYS_PER_SEASON=30`,
   `SEASONS_PER_YEAR=4`, `TICKS_PER_FANTASY_YEAR = TICKS_PER_DAY * DAYS_PER_SEASON * SEASONS_PER_YEAR`
   (`288000`), plus a small `fantasy_years_to_ticks(years: float) -> int` helper. Single source of
   truth — do not hardcode `288000`/`2400` a second time anywhere this ticket touches.
2. Migrate `LifecycleComponent.max_age_ticks` default (`src/core/state.py:156`) from `10000` to
   `70 * TICKS_PER_FANTASY_YEAR` (20,160,000).
3. Migrate `src/domains/demographics/cohort.py::get_age_bracket()`'s `3000`/`7000` literals to
   `12 * TICKS_PER_FANTASY_YEAR` (3,456,000) / `60 * TICKS_PER_FANTASY_YEAR` (17,280,000).
4. Migrate `src/ai/life_stage.py::LifeStageService.get_stage_for_age()`'s literals to the same two
   values, per its own docstring's explicit sync requirement — keep the "intentionally duplicated, not
   imported" comment, update the numbers it points at.
5. Update every test that asserts on the old `3000`/`7000`/`10000` boundary values as a boundary (not
   tests using them merely as arbitrary large numbers) — confirmed file list: `test_lifecycle.py`,
   `test_demographics.py`, `test_coming_of_age_archetype_choice.py`, `test_life_stage_transitions.py`.
6. Run the full scoped regression sweep across lifecycle/demographics/strategic/reproduction tests.
7. Add a parity ledger entry referencing `TCK-20260829-TEMPORAL-CALENDAR-AUTHORITY`'s original decision
   and this ticket's concrete implementation.
