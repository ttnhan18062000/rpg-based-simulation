---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260906-AGE-TIER-TIMING-BUG-AND-CORPUS-TEST
phase: open
date: 2026-09-06
tags: [testing, simulation-quality, temporal]
---

# TCK-20260906-AGE-TIER-TIMING-BUG-AND-CORPUS-TEST

## Title
simq_long_run_observation.py's 5000-tick default is now catastrophically short — real elder threshold is ~17.28M ticks, not 7000

## Status
OPEN

## Tier
standard

## Type
repair

## Priority
P1

## Request Summary
M9 epic (`TCK-20260824-EPIC-RPG-M9-CORPUS-TEST-COVERAGE`) child 7 of 8. **Major correction, 2026-09-06,
found while re-verifying this item's own citations, not present in the original doc**: the epic doc's
claim ("`tools/simq_long_run_observation.py` defaults to `--ticks 5000` — below the 7000-tick elder
threshold") is now dramatically more stale than a simple number update. `TCK-20260904-TEMPORAL-FANTASY-
YEAR-AGING-MIGRATION` (DONE) already replaced the original raw 3000/7000-tick literals with real
fantasy-year units: `YOUNG_ADULT_BOUNDARY_TICKS = 12 * TICKS_PER_FANTASY_YEAR`,
`ADULT_ELDER_BOUNDARY_TICKS = 60 * TICKS_PER_FANTASY_YEAR`
(`src/domains/demographics/cohort.py:19-20,69-85`), and `TICKS_PER_FANTASY_YEAR = 288,000`
(`src/core/calendar.py:13`). The real current thresholds are **3,456,000 ticks** (young->adult, 12
fantasy years) and **17,280,000 ticks** (adult->elder, 60 fantasy years) — `tools/
simq_long_run_observation.py`'s `--ticks 5000` default (confirmed still unchanged,
`tools/simq_long_run_observation.py:86`) isn't merely "below the elder threshold," it's roughly
0.03% of the young->adult threshold alone. No calibration run using this tool's default has ever
been capable of observing any age-bracket transition at all, silently proving nothing about idea
20/34's own lifecycle mechanics.

## Scope
- Confirm this finding doesn't already have its own dedicated fix ticket under the Temporal axis
  initiative (`docs/plans/rpg_design_roadmap/rpg_design_roadmap.md`'s "Temporal axis" section) before
  proceeding — if it does, this ticket should defer/cross-reference rather than duplicate.
- If genuinely unowned: raise `tools/simq_long_run_observation.py`'s default tick count to something
  that can actually observe both real thresholds, or add an explicit `--ticks` requirement/warning
  when a caller's value can't reach `ADULT_ELDER_BOUNDARY_TICKS`, so a future silent-no-op run is
  caught rather than repeated.
- Author the idea 20+34 corpus test: same 16-entity world used elsewhere in this epic (`frontier_
  village_core` + `hero_adventurers`), initialize 1-2 entities' `age_ticks` near 0, run long enough to
  observe both the CHILD/young->ADULT/adult transition and the ADULT->ELDER transition at the real
  17,280,000-tick threshold (confirm the real practical run length needed — this may itself require a
  much larger tick budget than any existing calibration convention uses, flag as a real finding if so
  rather than silently picking an inadequate number again).
- Assert `identity.life_stage` flips at the real young->adult threshold, elder attribute deltas apply
  at the real elder threshold, and idea 34's `archetype_locked` flips false->true specifically at that
  same young->adult transition.
- Resolve, or explicitly defer with a written reason, the open question already correctly flagged by
  the original epic doc: whether `get_age_bracket()`'s young/adult/elder string system and
  `IdentityComponent.life_stage: LifeStage` (CHILD/ADULT/ELDER enum) are two overlapping age-tier
  systems that should be reconciled — this question is unaffected by the fantasy-year correction
  above and remains genuinely open.

## Out of Scope
- Re-litigating `TCK-20260904-TEMPORAL-FANTASY-YEAR-AGING-MIGRATION`'s own already-shipped fantasy-year
  migration — that work is done; this ticket only addresses the tooling default that was never updated
  to match it.
- Any other item from M9's scope.

## Acceptance Criteria
- [ ] `simq_long_run_observation.py`'s default (or an explicit guard) prevents a silent no-observation
      run for age-bracket transitions going forward.
- [ ] A real corpus test observes both the young->adult and adult->elder transitions at their real,
      current fantasy-year-scaled thresholds, with `identity.life_stage` and `archetype_locked`
      assertions.
- [ ] The `get_age_bracket()`/`LifeStage` overlap question is either resolved or explicitly deferred
      with a written reason in this ticket — not silently dropped.

## Related Tickets
- `TCK-20260824-EPIC-RPG-M9-CORPUS-TEST-COVERAGE` (parent epic)
- `TCK-20260904-TEMPORAL-FANTASY-YEAR-AGING-MIGRATION` (the already-shipped migration this ticket's
  own tooling gap trails behind)
- `TCK-20260829-TEMPORAL-CALENDAR-AUTHORITY` (the decision precedent for fantasy-year units)

## Related Docs
- `docs/plans/rpg_design_roadmap/rpg_m9_corpus_test_coverage_epic.md`
- `docs/plans/rpg_design_roadmap/rpg_design_roadmap.md` — "Temporal axis" section (check for overlap
  before proceeding)

## Related Stored Artifacts
None yet — created by this ticket's own Investigate/Plan phases once picked up for implementation.

## Related Code Areas
- `tools/simq_long_run_observation.py`
- `src/domains/demographics/cohort.py`
- `src/core/calendar.py`
- `src/core/state.py` (`IdentityComponent.life_stage`)

## Assumptions / Open Questions
- Whether a corpus test can practically run long enough to observe a real 17.28M-tick elder
  transition within this project's normal calibration budget, or whether this needs a
  scaled-down/accelerated test harness instead, is not decided here — real design work for this
  ticket's own Investigate/Plan phases.
- Whether this finding is already tracked under the Temporal axis initiative is not confirmed here —
  check during Investigate before treating this as wholly new scope.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
