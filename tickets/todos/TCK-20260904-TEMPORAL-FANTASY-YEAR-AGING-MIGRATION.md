---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260904-TEMPORAL-FANTASY-YEAR-AGING-MIGRATION
phase: open
date: 2026-09-04
tags: [determinism]
---

# TCK-20260904-TEMPORAL-FANTASY-YEAR-AGING-MIGRATION

## Title
Migrate entity aging/lifespan to fantasy-year units, per the already-decided calendar authority

## Status
OPEN

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
- [ ] A named, single-source-of-truth fantasy-year/season/day conversion exists, reused by both the
      aging migration and the existing `2400`-tick-per-day call sites (no second incompatible
      constant introduced).
- [ ] `max_age_ticks` and the demographic age-bracket thresholds migrate off the current few-day
      values to fantasy-year-derived ones, with the actual target ages confirmed by a plan-owner
      numeric review before being hardcoded.
- [ ] All 4 real consumer call sites verified to behave correctly at the new scale (existing tests
      updated/added as needed).
- [ ] Any replay/checkpoint/world-compile fixture that encoded the old lifespan is identified and
      updated, or confirmed none exist.
- [ ] Parity ledger entry added recording the migration, referencing
      `TCK-20260829-TEMPORAL-CALENDAR-AUTHORITY`'s original decision.

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
None yet.

## Related Code Areas
- `src/core/state.py` (`LifecycleComponent.max_age_ticks`)
- `src/core/builder.py` (`max_age_ticks` default/parameter)
- `src/domains/demographics/cohort.py` (age-bracket thresholds)
- `src/engine/apply.py`, `src/systems/world_systems/routine.py`,
  `src/systems/lifecycle_systems/lifecycle.py` (consumers)

## Assumptions / Open Questions
- Exact target lifespan/life-stage-boundary numbers are not decided here — a plan-owner review is a
  prerequisite before this ticket picks real values, per the temporal proposal's own §17.
- Whether any existing replay/checkpoint/world-compile fixture encodes the old few-day lifespan as an
  expected outcome is not yet confirmed — must be checked at pickup, not assumed either way.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
