---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260904-TEMPORAL-FANTASY-YEAR-AGING-MIGRATION
phase: done
date: 2026-09-04
tags: [determinism]
---

# TCK-20260904-TEMPORAL-FANTASY-YEAR-AGING-MIGRATION

## Title
Migrate entity aging/lifespan to fantasy-year units, per the already-decided calendar authority

## Status
DONE

## Tier
standard

## Type
repair

## Priority
P1

## Request Summary
`TCK-20260829-TEMPORAL-CALENDAR-AUTHORITY` (done) quantified and decided: under the settled
2,400-ticks/day calendar (`docs/mechanics/05_world_evolution.md`), `LifecycleComponent.max_age_ticks
= 10000` (`src/core/state.py:156`) gives every entity a **4.17-day maximum lifespan**, and the elder
threshold (`age_ticks >= 7000`, `src/domains/demographics/cohort.py:66`) triggers at **2.9 days**.
Decision #2 of that ticket: "age representation migrates to fantasy-year units once that migration is
implemented, rather than patching `max_age_ticks`/cohort thresholds under the current regime." That
migration was explicitly deferred to "a dedicated implementation ticket, most likely inside M3" — M3's
reproduction epic (`tickets/done/m3-reproduction-epic/`) has since shipped in full (population cohort
seeding, birth records, marriage, population-pressure closure) without touching `max_age_ticks` or any
fantasy-year aging logic anywhere. Confirmed directly via grep, not assumed: no
`ticks_per_fantasy_year` constant or equivalent exists anywhere in `src/` today. The feature set that
most depends on realistic multi-year lifespans shipped on top of a calendar that still kills every
entity of old age in under 5 in-game days.

## Scope
- Add the calendar/fantasy-year conversion (120-day fantasy year: 4 seasons x 30 days, per the
  temporal-axis proposal's already-accepted §1.1 calendar and the roadmap's own "Accepted in this
  brainstorm pass" list) as an explicit, named constant/helper — not a second raw tick literal
  alongside the existing `2400` day constant already used in `state_presenter.py`/
  `intelligence.py`/`docs/mechanics/05_world_evolution.md`.
- Migrate `LifecycleComponent.max_age_ticks` (and its `src/core/builder.py` default/parameter) and
  the demographic elder/adult/young age-bracket thresholds (`src/domains/demographics/cohort.py`'s
  `3000`/`7000` literals) to fantasy-year-derived values, replacing the current few-day lifespans with
  balance-reviewed multi-year ones (exact life-stage boundaries/lifespan distribution remain their own
  open decision per the temporal proposal's §17 — this ticket migrates the *representation*, a
  plan-owner numeric review of the *actual* target ages is a prerequisite before picking real numbers,
  not something to guess here).
- Verify every real consumer of `max_age_ticks`/`age_ticks` still behaves correctly under the new
  scale: `src/engine/apply.py:109` (`active=`), `src/systems/world_systems/routine.py:108`,
  `src/systems/lifecycle_systems/lifecycle.py:96`, `src/domains/demographics/cohort.py`'s bracket
  functions.
- Confirm whether any existing recorded replay/checkpoint fixture or `world_compile_report.json`
  baseline encodes the old few-day lifespan as an expected outcome (would need updating, not silently
  left stale) — check before assuming none do.

## Out of Scope
- The full universal duration/rate formula (Decision #3 of `TCK-20260829-TEMPORAL-CALENDAR-AUTHORITY`,
  generalizing movement's `move_cost`/`readiness_speed` pattern) — a separate, larger P1 item in the
  temporal proposal's own priority table, not bundled into this aging-specific migration.
- The metamorphic-lab pilot (Decision #4) validating the new numbers as balanced — a follow-up step
  once this migration lands, not part of landing it.
- Sustained-activity/instantaneous-routine fixes (§9.3 of the temporal proposal — `SLEEP`/`EAT`
  handlers) — a separate, already-disclosed gap, not this ticket's concern.
- Pregnancy/apprenticeship/other long-activity duration calibration — the temporal proposal's own §17
  lists these as still-open, separate decisions.

## Acceptance Criteria
- [x] A named, single-source-of-truth fantasy-year/season/day conversion exists, reused by both the
      aging migration and the existing `2400`-tick-per-day call sites (no second incompatible
      constant introduced). `src/core/calendar.py` added (`TICKS_PER_FANTASY_YEAR=288000`).
- [x] `max_age_ticks` and the demographic age-bracket thresholds migrate off the current few-day
      values to fantasy-year-derived ones, with the actual target ages confirmed by a plan-owner
      numeric review before being hardcoded. Confirmed with the user before implementation: 70y max
      lifespan, 12y CHILD->ADULT, 60y ADULT->ELDER — all three sourced directly from the temporal-axis
      proposal's own accepted text, not invented.
- [x] All 4 real consumer call sites verified to behave correctly at the new scale (existing tests
      updated/added as needed). Also found and fixed a 5th real consumer the original scope missed:
      `EntityGenerator.spawn_natural_creature_offspring()`'s maturation-clock computation
      (`src/systems/world_systems/generator.py`).
- [x] Any replay/checkpoint/world-compile fixture that encoded the old lifespan is identified and
      updated, or confirmed none exist. Confirmed via direct grep across `data/worlds/` — none exist.
- [x] Parity ledger entry added recording the migration, referencing
      `TCK-20260829-TEMPORAL-CALENDAR-AUTHORITY`'s original decision. `PROG-124` added via
      `tools/parity_ledger_writer.py`.

## Related Tickets
- TCK-20260829-TEMPORAL-CALENDAR-AUTHORITY (the decision this ticket implements)
- m3-reproduction-epic (tickets/done/) — shipped on top of the still-unmigrated calendar this ticket
  fixes

## Related Docs
- `docs/plans/rpg_design_roadmap/rpg_design_roadmap.md` ("Temporal axis" section)
- `docs/brainstorm/codex/2026-08-28-core-rpg-temporal-axis-proposal.md` (§1.1 calendar, §2.2 human
  lifecycle, §9.2 aging conflict)
- `docs/mechanics/05_world_evolution.md`

## Related Stored Artifacts
(staging artifacts in `staging_artifacts/TCK-20260904-TEMPORAL-FANTASY-YEAR-AGING-MIGRATION/`)

## Related Code Areas
- `src/core/calendar.py` (new)
- `src/core/state.py` (`LifecycleComponent.max_age_ticks`)
- `src/domains/demographics/cohort.py` (age-bracket thresholds)
- `src/ai/life_stage.py` (`LifeStageService.get_stage_for_age()`)
- `src/systems/world_systems/generator.py` (`spawn_natural_creature_offspring()`)
- `src/engine/apply.py`, `src/systems/world_systems/routine.py`,
  `src/systems/lifecycle_systems/lifecycle.py` (consumers)

## Assumptions / Open Questions
- Exact target lifespan/life-stage-boundary numbers are not decided here — a plan-owner review is a
  prerequisite before this ticket picks real values, per the temporal proposal's own §17.
- Whether any existing replay/checkpoint/world-compile fixture encodes the old few-day lifespan as an
  expected outcome is not yet confirmed — must be checked at pickup, not assumed either way.

## Implementation Notes
Numeric targets confirmed with the user before writing any code (per this ticket's own Acceptance
Criteria requiring plan-owner sign-off): sourced directly from the already-accepted temporal-axis
proposal, not invented — `max_age_ticks` = 70 fantasy years (20,160,000 ticks, §1.1's own worked
example), CHILD->ADULT at 12 fantasy years (3,456,000 ticks, folding the proposal's §2.2 Adolescent
stage into ADULT since `LifeStage` has no 4th enum value — the user chose not to expand the enum in
this pass), ADULT->ELDER at 60 fantasy years (17,280,000 ticks, matching §2.2 exactly).

Re-investigated real scope at pickup (state had drifted since the ticket was filed hours earlier in
this same session): found **two** independent, *deliberately* duplicated life-stage classification
systems sharing the same raw boundaries, not one — `src/domains/demographics/cohort.py::get_age_bracket()`
and `src/ai/life_stage.py::LifeStageService.get_stage_for_age()`. The latter's own docstring already
documents the duplication as intentional (`TCK-20260824-LIFE-STAGE-TRANSITIONS`: "separate vocabularies
for separate subsystems... If `get_age_bracket()`'s thresholds ever change, this function's literals
must change too") — kept that pattern intact (updated the numbers, did not collapse into an import,
which would have silently reversed a previously-made, explicitly-recorded architectural decision).

Added `src/core/calendar.py` as the single named source of truth (`TICKS_PER_DAY=2400`,
`DAYS_PER_SEASON=30`, `SEASONS_PER_YEAR=4`, `TICKS_PER_FANTASY_YEAR=288000`,
`fantasy_years_to_ticks()`). `cohort.py` gained two named module constants
(`YOUNG_ADULT_BOUNDARY_TICKS`, `ADULT_ELDER_BOUNDARY_TICKS`) derived from it; `life_stage.py` keeps its
own raw literals per the deliberate-duplication design, updated to match.

**Found a real production consumer the original ticket scope missed**: `EntityGenerator.
spawn_natural_creature_offspring()` (`src/systems/world_systems/generator.py`) computed newly-spawned
creatures' "short maturation clock" age directly from the raw `3000`-tick literal
(`short_clock_age = 3000 - CampService.CAMP_SPAWN_INTERVAL`), spawning them just shy of the CHILD/ADULT
boundary so they mature to ADULT after roughly one camp-spawn cycle. Migrated to import
`YOUNG_ADULT_BOUNDARY_TICKS` from `cohort.py` (a normal consumer, not the deliberate-duplication case
`life_stage.py` is). Two test files independently asserted on the old literal value
(`tests/integration/optimization/test_component_patch_apply_parity.py`,
`tests/unit/world/test_natural_creature_reproduction.py`) — the second was found only via the full
regression sweep, not the initial grep.

No replay/checkpoint fixture or `world_compile_report.json` baseline encoded the old few-day lifespan —
confirmed via direct grep across `data/worlds/`, not assumed.

## Test Summary
- 3 new tests in `tests/unit/core/test_calendar.py` locking in the calendar module's arithmetic.
- Updated boundary-value assertions in `tests/unit/progression/test_lifecycle.py`,
  `tests/unit/world/test_demographics.py`, `tests/unit/strategic/test_coming_of_age_archetype_choice.py`,
  `tests/unit/strategic/test_life_stage_transitions.py`, plus 2 files found only during
  implementation: `tests/integration/optimization/test_component_patch_apply_parity.py`,
  `tests/unit/world/test_natural_creature_reproduction.py`.
- Full regression: `pytest tests/unit/core/ tests/unit/progression/ tests/unit/world/
  tests/unit/strategic/ tests/unit/domains/optimization/ tests/integration/optimization/
  -m "not slow"` → 1087 passed, 2 deselected, 0 failed.
- `pytest tests/unit/engine/ tests/unit/kernel/ tests/certification/ -m "not slow"` → 315 passed,
  2 skipped (pre-existing, unrelated), 0 failed.

## Files Changed
- `src/core/calendar.py` — new, the calendar-authority constants.
- `src/core/state.py` — `LifecycleComponent.max_age_ticks` default.
- `src/domains/demographics/cohort.py` — named boundary constants, `get_age_bracket()`.
- `src/ai/life_stage.py` — `LifeStageService.get_stage_for_age()`'s duplicated literals.
- `src/systems/world_systems/generator.py` — `spawn_natural_creature_offspring()`'s maturation clock
  (the missed consumer found during implementation).
- `tests/unit/core/test_calendar.py` — new.
- `tests/unit/progression/test_lifecycle.py`, `tests/unit/world/test_demographics.py`,
  `tests/unit/strategic/test_coming_of_age_archetype_choice.py`,
  `tests/unit/strategic/test_life_stage_transitions.py`,
  `tests/integration/optimization/test_component_patch_apply_parity.py`,
  `tests/unit/world/test_natural_creature_reproduction.py` — boundary-value assertions updated.
- `docs/parity_ledger/progression.yaml` — new entry `PROG-124`.

## Completion Summary
Implemented `TCK-20260829-TEMPORAL-CALENDAR-AUTHORITY`'s deferred aging migration. Every entity's
maximum lifespan moved from 4.17 days to 70 fantasy years; the elder/adult/young age brackets moved
from 2.9/1.25 days to 60/12 fantasy years — all three numbers sourced directly from the already-accepted
temporal-axis proposal text and confirmed with the user before implementation, not invented. Found and
fixed a real production consumer (`spawn_natural_creature_offspring()`) the original ticket scope
missed, plus a second test file with an independent copy of the stale literal, both caught by running
the full regression sweep rather than trusting the initial grep alone. Full existing test suite passes
unchanged in shape (1087 + 315 tests), with boundary-value assertions updated to the new numbers, not
weakened or skipped. Parity ledger entry `PROG-124` records the migration (originally written as
`PROG-123`, renumbered during a merge-conflict resolution against `origin/main`'s own concurrent
`PROG-123`, the `TCK-20260904-MATERIAL-POSSESSION-PREDICATE` entry).
