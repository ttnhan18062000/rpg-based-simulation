---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260904-TEMPORAL-FANTASY-YEAR-AGING-MIGRATION
artifact_type: investigation
tags: [determinism]
---

# Investigation — TCK-20260904-TEMPORAL-FANTASY-YEAR-AGING-MIGRATION

Re-verified against current code before writing a plan (state may have drifted since the ticket was
filed hours earlier in this same session).

**Real scope is larger than the ticket's own initial estimate.** Two independent, *deliberately*
duplicated life-stage classification systems share the same raw-tick boundaries, not one:
- `src/domains/demographics/cohort.py::get_age_bracket()` — cohort-level aggregate demographics.
  `< 3000` young, `< 7000` adult, `>= 7000` elder.
- `src/ai/life_stage.py::LifeStageService.get_stage_for_age()` — per-entity strategic cognition.
  Same three literals, same boundaries. Its own docstring already documents the duplication as
  intentional ("separate vocabularies for separate subsystems... same underlying tick boundaries. If
  `get_age_bracket()`'s thresholds ever change, this function's literals must change too" —
  `TCK-20260824-LIFE-STAGE-TRANSITIONS`).

`LifecycleComponent.max_age_ticks` (`src/core/state.py:156`, default `10000`) is a third, independent
number — the hard death threshold, not a stage boundary.

No `ticks_per_fantasy_year` or equivalent named calendar constant exists anywhere in `src/` — confirmed
via grep, not assumed. The existing `2400`-ticks/day literal is duplicated raw in
`src/api/presenters/state_presenter.py:317` and `src/systems/strategic_systems/intelligence.py:539`
rather than referenced from a shared constant.

**Numeric targets, confirmed with the user before implementation** (per this ticket's own Acceptance
Criteria requiring plan-owner sign-off): sourced directly from the already-accepted temporal-axis
proposal text, not invented.
- 1 fantasy year = 4 seasons x 30 days x 2,400 ticks/day = **288,000 ticks**.
- CHILD -> ADULT at 12 fantasy years = **3,456,000 ticks** (replacing `3000`). Folds the proposal's
  §2.2 Adolescent stage (12-17y) into ADULT, since `LifeStage` has no 4th enum value and the user chose
  not to expand it in this ticket.
- ADULT -> ELDER at 60 fantasy years = **17,280,000 ticks** (replacing `7000`), matching §2.2 exactly.
- `max_age_ticks` = 70 fantasy years = **20,160,000 ticks** (replacing `10000`), matching §1.1's own
  worked example in the proposal's calendar table.

**Test blast radius confirmed via grep**, not estimated: `tests/unit/progression/test_lifecycle.py`,
`tests/unit/world/test_demographics.py`, `tests/unit/strategic/test_coming_of_age_archetype_choice.py`,
`tests/unit/strategic/test_life_stage_transitions.py` all hardcode `3000`/`7000`/`10000` as literal
boundary values. `tests/unit/domains/optimization/`, `tests/integration/optimization/` files also
reference these numbers but mostly as arbitrary large `max_age_ticks` values in builder calls (e.g.
`max_age_ticks=100000`), not asserting on the boundary itself — need per-file judgment at
implementation time, not a blanket assumption either way.

No replay/checkpoint fixture or `world_compile_report.json` baseline was found encoding the old
few-day lifespan as an expected outcome (none of the 21 worlds' entities age far enough within their
compiled/tested tick ranges for this to matter) — confirmed via grep across `data/worlds/`, not
assumed.
