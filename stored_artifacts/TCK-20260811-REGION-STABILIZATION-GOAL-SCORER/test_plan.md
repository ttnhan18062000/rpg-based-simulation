---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260811-REGION-STABILIZATION-GOAL-SCORER
artifact_type: test_plan
tags: [cognition, world]
---

# Test Plan — TCK-20260811-REGION-STABILIZATION-GOAL-SCORER

## Regression Surface

Existing tests that must keep passing, grouped by domain:

**Unit — event interpretation (direct target of this ticket's rewrite)**
- `tests/unit/strategic/test_event_interpretation.py` — `TestStrategicPivotOnDanger::test_no_pivot_when_hazard_low`,
  `::test_concern_generated_on_high_hazard` (both unaffected — concern generation and the
  `hazard_level <= 0.7` early-return are untouched by this ticket's scope); `TestScarDetection` (both
  tests, untouched — `interpret_scar_detection()` is out of scope); `TestDirectiveEvent` (all 3 tests,
  untouched); `TestNearDeath` (both tests, untouched — `interpret_near_death()` is a different method,
  explicitly out of scope per the ticket's Out of Scope on line 179's clear).
  `TestStrategicPivotOnDanger::test_project_pivot_when_urgency_exceeds_resistance` and
  `::test_no_pivot_when_resistance_high` are **rewritten**, not merely re-run unchanged — see New
  Tests Required.

**Unit — enum/registry drift guards**
- `tests/unit/strategic/test_enum_drift.py::test_goal_registry_strict_validation` — must keep passing
  with a 13th `GoalKind` member (assuming a new member is added per this ticket's scope).
- `tests/unit/strategic/test_enum_drift.py::test_all_registered_scorers_are_canonical` — must keep
  passing once the new scorer is registered.

**Unit — score normalization / lock-bypass arbitration**
- `tests/unit/strategic/test_score_normalization.py` (all 5 tests) — must keep passing unmodified;
  proves `_score_scale_max()`/the lock-bypass gate are untouched by this ticket, only fed a new kind
  of `ProjectKind`-typed candidate.

**Unit — sibling materialization branches (must stay unaffected by the new `elif`)**
- `tests/unit/strategic/test_adventure_route_materialization.py` (all tests) — proves the new branch
  is additive, not a restructure of `ADVENTURE_ROUTE`'s branch.
- `tests/unit/strategic/test_social_contract_materialization.py` (all tests) — same, for
  `SOCIAL_CONTRACT`'s branch.
- `tests/unit/ai/goals/test_adventure_goal_scorer.py`, `tests/unit/ai/goals/test_social_contract_goal_scorer.py`
  — must keep passing unmodified, proving the new scorer module is a sibling, not a shared-state
  hazard.
- `tests/unit/strategic/test_strategic_social_contracts.py` — must keep passing unmodified (ticket 5's
  own rewrite target; untouched by this ticket).

**Unit — interruption resistance / retention (general laws this ticket's candidate now flows through)**
- Any existing test file directly exercising `evaluate_project_switch()`'s STRAT-185/186/187 laws
  (`test_score_normalization.py` above is the primary one; confirm no other file duplicates this
  coverage before assuming it's covered elsewhere).

**Integration / arena-combat**
- None identified as directly affected — `EventInterpreter` has no production caller (see
  investigation.md), so no arena-combat or full-pipeline integration test currently exercises
  `interpret_regional_danger()`. If Plan chooses Risk #1's option (a) (scorer reads `state.regions`
  directly, making the mechanic live-reachable for the first time), this section must be revisited —
  flagged here, not assumed.

## New Tests Required

Per acceptance criteria:

**AC1 — missing enum-member gap resolved explicitly**
- `test_project_kind_stabilize_is_registered_member` — unit — verifies `ProjectKind.STABILIZE` exists
  (or, if Plan reuses an existing member instead, an equivalent test asserting the chosen member and a
  code comment/docstring recording the explicit rationale, mirroring this ticket's own AC wording) —
  lives in `tests/unit/strategic/test_enum_drift.py` or a new `tests/unit/strategic/test_stabilize_enum.py`
  (Plan to decide placement, matching whichever sibling ticket's convention is closest once the exact
  member name is fixed).
- `test_stabilize_kind_value_does_not_collide_with_existing_project_kind_or_goal_kind` — unit —
  checks the new `ProjectKind` value against all existing `ProjectKind`/`GoalKind` values for
  unintended collisions, mirroring `test_social_contract_kind_value_does_not_collide_with_project_kind_or_existing_goal_kind`'s
  style from ticket 5 — same file.

**AC2 — `interpret_regional_danger()`'s stabilize-project path no longer sets `current_project_id_set` directly**
- `test_interpret_regional_danger_no_longer_sets_current_project_id_directly` — unit — calls
  `EventInterpreter.interpret_regional_danger()` under the same high-urgency/low-resistance conditions
  `test_project_pivot_when_urgency_exceeds_resistance` used to exercise, asserts
  `result.current_project_id_set is None` — mirrors ticket 5's
  `test_accept_contract_no_longer_sets_current_project_id_directly`. Lives in
  `tests/unit/strategic/test_event_interpretation.py` (extends/replaces the rewritten class — see AC4
  below for the exact rewrite shape) or a new dedicated file, Plan to decide.

**AC3 — `RegionStabilizationGoalScorer` produces a comparable `GoalScore` that must clear `evaluate_project_switch()`**
- `test_region_stabilization_goal_scorer_implements_goal_scorer_protocol` — unit — same shape as
  `test_social_contract_goal_scorer_implements_goal_scorer_protocol`.
- `test_region_stabilization_goal_scorer_metadata_carries_raw_score` — unit — asserts
  `metadata["raw_score"]` is populated and the metadata key set is exact (shape-exactness, mirroring
  ticket 5's `test_social_contract_goal_scorer_metadata_carries_raw_score_and_contract_identity`) —
  exact key set depends on Plan's chosen raw-score formula/target-resolution design (Risk #1), not
  prescribed here.
- `test_region_stabilization_goal_scorer_low_hazard_returns_zero_utility_no_target` — unit — hazard at
  or below 0.7 produces `GoalScore(utility=0.0, target_id=None)`, mirroring the existing
  `test_no_pivot_when_hazard_low` semantics in scorer form.
- `test_region_stabilization_winner_materializes_with_raw_score_not_utility` — integration — force a
  known raw score via a controlled high-hazard region fixture, run
  `evaluate_strategic_intent(state, entity, force=True)` end-to-end, assert
  `ProjectState.score == <the hand-computed raw score>`, plus a negative check
  (`project.score != <utility value>`) — mirrors ticket 5's identically-named-pattern test.
- `test_active_region_stabilization_wins_arbitration_with_no_current_project` — integration — entity
  has no current project, region hazard > 0.7; assert `current_project_id` becomes the materialized
  stabilize project's id via `evaluate_project_switch()`'s unconditional-adopt path.
- `test_high_lock_current_project_retains_against_low_urgency_regional_danger` — integration — entity
  has a locked, high-score current project plus a region just above the 0.7 threshold (low urgency);
  assert `current_project_id` unchanged — worked arithmetic in the docstring, mirroring
  `test_locked_system_a_current_still_blocks_low_urgency_system_b_candidate`'s existing style.
- `test_high_urgency_regional_danger_interrupts_locked_current_project` — integration — locked current
  project + a region near `hazard_level = 1.0` (urgency near 1.0); assert both
  `candidate_pct > normalized_effective_current_pct` and the `0.8` floor clear, and
  `current_project_id` switches to the materialized stabilize project.
  These three integration tests live in a new `tests/unit/strategic/test_region_stabilization_materialization.py`,
  mirroring `test_social_contract_materialization.py`'s file structure exactly.

**AC4 — `test_project_pivot_when_urgency_exceeds_resistance`/`test_no_pivot_when_resistance_high` pass with equivalent assertions**
- Both tests in `tests/unit/strategic/test_event_interpretation.py::TestStrategicPivotOnDanger` are
  **rewritten**, per the ticket's own AC wording ("pass against the new scorer path with equivalent
  assertions" — not necessarily unchanged), following ticket 5's Step 8 discipline for
  `test_accepted_contract_spawns_project_and_objective`:
  - `test_project_pivot_when_urgency_exceeds_resistance` — equivalent assertions become: (1)
    `EventInterpreter.interpret_regional_danger()` still returns a concern and no longer sets
    `current_project_id_set` (AC2); (2) `RegionStabilizationGoalScorer().score(...)` on an entity/state
    with the same high-hazard region returns a non-zero-utility `GoalScore` whose `metadata["raw_score"]`
    is populated; (3) `StrategicIntelligenceSystem.evaluate_strategic_intent(state, entity, force=True)`
    end-to-end produces a suspended `proj_craft` (same assertion as today) and a new active project
    whose id contains `"stabilize"` and whose `kind == ProjectKind.STABILIZE` (the enum member, not
    the string — same AC1/AC5 upgrade ticket 5's Step 8 applied for `ProjectKind.COMBAT`). Exact
    reachability path (does the scorer read `state.regions` directly, or is there another route into
    this end-to-end call) depends on Plan's resolution of investigation.md Risk #1 — not fixed here.
  - `test_no_pivot_when_resistance_high` — equivalent assertions become: (1) concern still generated,
    `current_project_id_set is None` at the `interpret_regional_danger()` level (unchanged from
    today, now also true simply because the method never sets it at all per AC2, not only because
    resistance was high — this is itself a semantic shift worth calling out in the test docstring);
    (2) the scorer/arbiter path, when exercised end-to-end with the same low-urgency/high-resistance
    fixture, does **not** switch `current_project_id` away from `proj_craft` — asserted via
    `evaluate_strategic_intent()`, not by calling `interpret_regional_danger()` alone (since that
    method's own output no longer encodes the pivot decision).

**AC5 — Materialized `ProjectState.kind` uses a real `ProjectKind` enum member**
- Covered by `test_region_stabilization_winner_materializes_with_raw_score_not_utility` and the
  rewritten `test_project_pivot_when_urgency_exceeds_resistance` (both assert
  `project.kind == ProjectKind.STABILIZE`, the enum member).

**AC6 — Follows the same raw-score/utility separation requirement as ticket 5**
- `test_region_stabilization_materialization_never_uses_utility_for_score` — unit/integration —
  direct regression guard: construct a fixture where `raw_score` and normalized `utility` are
  provably different values, assert `ProjectState.score` equals the former, never the latter — mirrors
  ticket 5's own explicit negative-check pattern in `test_social_contract_winner_materializes_with_raw_score_not_utility`.

**Anti-drift / architecture guard**
- `test_interpret_scar_detection_unaffected` (if not already implicitly covered by
  `TestScarDetection`'s existing 2 tests continuing to pass unmodified) — confirms
  `interpret_scar_detection()`'s raw `"exploration"`/`"investigate"` strings are untouched by this
  ticket, guarding against scope creep into LEG-RPG-117.
- `test_interpret_near_death_unaffected` — same, for `interpret_near_death()`'s line-179 clear,
  guarding against scope creep into the explicitly-out-of-scope clear-not-steal site.
- `test_region_stabilization_goal_kind_value_does_not_break_existing_tie_break_ordering` — unit —
  asserts the new `GoalKind` member's value does not silently change `ADVENTURE_ROUTE`'s or
  `SOCIAL_CONTRACT`'s existing sort position relative to the 10 original members (guards against
  Risk #3's tie-break value being picked in a way that regresses ticket 1/5's already-verified
  ordering behavior).

## Scoped Pytest Commands

```
pytest tests/unit/strategic/ tests/unit/ai/goals/ -v
```

Rationale: covers `test_event_interpretation.py` (direct target), `test_enum_drift.py`,
`test_score_normalization.py`, `test_adventure_route_materialization.py`,
`test_social_contract_materialization.py`, `test_strategic_social_contracts.py`, the new
`test_region_stabilization_materialization.py`, and `tests/unit/ai/goals/` (both existing scorer
test files plus the new `test_region_stabilization_goal_scorer.py`) — the full set of files this
ticket's own investigation identified as in the regression surface or as new-test targets. Do not
run `pytest tests/` — out of scope per CLAUDE.md's Testing Rule.

If Plan's resolution of Risk #1 makes the mechanic live-reachable via `state.regions` (option (a)),
add a second scoped run once the exact touched pipeline module is known:
```
pytest tests/unit/systems/ -k "region or danger or stabiliz" -v
```
(placeholder pattern — Plan/Implement to confirm the real path once the reachability design is fixed).

## Anti-Drift Test Guards

- `test_interpret_scar_detection_unaffected` / `test_interpret_near_death_unaffected` (above) — catch
  any accidental spillover into the two explicitly out-of-scope methods in the same file.
- `test_adventure_route_materialization.py` and `test_social_contract_materialization.py` passing
  unmodified — catch any accidental restructuring of the existing two `elif` branches when inserting
  the third.
- `test_score_normalization.py`'s 5 tests passing unmodified — catch any accidental change to
  `_score_scale_max()`/`_ADVENTURE_ROUTE_SCORE_MAX`/`_GOAL_UTILITY_SCORE_MAX`, which both prior
  tickets' calibrations depend on.
- `test_region_stabilization_materialization_never_uses_utility_for_score` — catches the specific
  scale-mismatch defect class (`TCK-20260811-INTERRUPTION-BYPASS-RETENTION-MARGIN-SCALE-BUG`) a
  third time, for the third system now sharing the 2.9-ceiling scale.
- `test_stabilize_kind_value_does_not_collide_with_existing_project_kind_or_goal_kind` — catches an
  accidental enum-value collision that would silently misroute `_score_scale_max()`'s classification
  or the `existing = next(...)` resume/dedup lookup in an unintended way (as opposed to the
  deliberate collision choice flagged in investigation.md Risk #4, which — if chosen — must be
  covered by a *positive* test asserting the resume behavior instead, not this negative guard).
