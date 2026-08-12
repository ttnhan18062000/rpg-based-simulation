---
status: historical
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260811-REGION-STABILIZATION-GOAL-SCORER
phase: done
date: 2026-08-11
tags: [cognition, world]
---

# TCK-20260811-REGION-STABILIZATION-GOAL-SCORER

## Title
Generalize GoalScorer-wrapper pattern to region stabilization (events.py)

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Apply the same wrapper pattern used for adventure to src/systems/world_systems/events.py:98/stabilize_project (RegionStabilizationGoalScorer), which today unconditionally overwrites current_project_id without going through the arbiter. Part of the design's Goal #4 (generalizing the wrapper pattern to the other confirmed arbiter-bypass sites); explicitly out of scope for direct implementation in the original design but a natural follow-on.

## Scope
- Resolve the missing-enum-member gap first: events.py's stabilize/exploration/investigate project/objective kinds are currently raw strings with no matching ProjectKind/ObjectiveKind enum member -- add ProjectKind.STABILIZE (or explicitly justify reusing an existing member) so _score_scale_max()'s isinstance(kind, ProjectKind) classification does not silently fall through to the wrong scale
- New RegionStabilizationGoalScorer (GoalScorer) wrapping EventInterpreter's existing unchanged internal danger-interpretation logic, producing a GoalScore with raw score in metadata (never utility)
- EventInterpreter.interpret_regional_danger()'s stabilize-project path no longer sets current_project_id_set directly; the resulting GoalScore must clear evaluate_project_switch() too
- tests/unit/strategic/test_event_interpretation.py::TestStrategicPivotOnDanger::test_project_pivot_when_urgency_exceeds_resistance and ::test_no_pivot_when_resistance_high re-run against the new scorer path with equivalent assertions

## Out of Scope
- contracts.py / SocialContractGoalScorer -- structurally independent bypass site, covered by TCK-20260811-SOCIAL-CONTRACT-GOAL-SCORER
- events.py line 179's current_project_id_set=None clear -- that is a clear, not a steal, explicitly out of scope
- AdventureGoalScorer -- TCK-20260811-ADVENTURE-GOAL-SCORER's job

## Acceptance Criteria
- [x] The missing ProjectKind/ObjectiveKind enum-member gap is resolved explicitly (new ProjectKind.STABILIZE added, or an existing member reused with explicit rationale recorded) -- not left as a raw string
- [x] EventInterpreter.interpret_regional_danger()'s stabilize-project path no longer sets current_project_id_set directly
- [x] RegionStabilizationGoalScorer produces a comparable GoalScore that must clear evaluate_project_switch() to become current_project_id
- [x] tests/unit/strategic/test_event_interpretation.py::TestStrategicPivotOnDanger::test_project_pivot_when_urgency_exceeds_resistance and ::test_no_pivot_when_resistance_high pass against the new scorer path with equivalent assertions
- [x] Materialized ProjectState.kind uses a real ProjectKind enum member
- [x] Follows the same raw-score/utility separation requirement as TCK-20260811-SOCIAL-CONTRACT-GOAL-SCORER

## Related Tickets
- TCK-20260810-PROJECT-SWITCH-BYPASS-GENERALIZATION
- TCK-20260811-INTERRUPTION-BYPASS-RETENTION-MARGIN-SCALE-BUG

## Related Docs
- docs/parity_ledger/strategic_cognition.yaml

## Related Stored Artifacts
None.

## Related Code Areas
- src/systems/world_systems/events.py
- src/systems/event_interpreter.py
- src/core/strategic.py
- src/systems/strategic_systems/intelligence.py

## Assumptions / Open Questions
- NEW FINDING undocumented by the design doc: events.py's stabilize/exploration/investigate kinds are raw strings with no matching ProjectKind/ObjectiveKind enum member today -- skipping this fix risks reproducing the exact TCK-20260811-INTERRUPTION-BYPASS-RETENTION-MARGIN-SCALE-BUG defect class; must be resolved as part of this ticket's own scope, not silently deferred
- Same real-behavior-change caveat as TCK-20260811-SOCIAL-CONTRACT-GOAL-SCORER: today stabilize always wins the project slot, post-migration it competes and can lose
- Related design doc: docs/architecture/2026-08-11-adventure-as-cognition-strategy-subcomponent-design.md (Future Extension Patterns / Goal #4)

## Implementation Notes
Implemented per staging_artifacts/TCK-20260811-REGION-STABILIZATION-GOAL-SCORER/plan.md, Steps
1-9 and 11 (Step 10, docs/parity-ledger updates, deliberately deferred to the separate
Document-Update/Parity phase per the orchestrator's explicit instruction for this pass).

- Added `ProjectKind.STABILIZE = "stabilize"` and `GoalKind.REGION_STABILIZATION =
  "region_stabilization"` to `src/core/strategic.py`.
- Extracted `EventInterpreter.compute_danger_urgency(region)` as a new static helper in
  `src/systems/world_systems/events.py`; simplified `interpret_regional_danger()` to
  concern-generation only -- it no longer constructs a stabilize `ProjectState` or writes
  `current_project_id_set`/`projects_add_or_update` at all (AC2). `interpret_scar_detection()`
  and `interpret_near_death()` were not touched.
- Created `RegionStabilizationGoalScorer` in new file
  `src/ai/goals/region_stabilization_scorer.py`, mirroring `SocialContractGoalScorer`'s shape:
  resolves the entity's current region via `LegalityServiceV2.get_region_for_position()`, calls
  `compute_danger_urgency()`, computes `raw_score = urgency * _ADVENTURE_ROUTE_SCORE_MAX` (2.9
  ceiling, NOT the original `urgency * 100`), and sets `target_pos` to the region's centroid
  (fixing the inherited "wins but stalls" defect -- a bare region id was never tactically
  resolvable). Registered in `src/ai/goals/__init__.py`.
- Added the `elif best_candidate.kind == GoalKind.REGION_STABILIZATION:` materialization branch
  in `StrategicIntelligenceSystem.evaluate_strategic_intent()`
  (`src/systems/strategic_systems/intelligence.py`), a "dumb" consumer of `proj_kind`/`obj_kind`
  resolved upstream in the scorer's metadata; `ProjectState.score` is set from
  `metadata["raw_score"]`, never `.utility`. No new imports were needed in `intelligence.py`.
- Added unit tests (`tests/unit/ai/goals/test_region_stabilization_goal_scorer.py`, new;
  `tests/unit/strategic/test_enum_drift.py`, extended with 5 enum-drift/collision/tie-break
  guards) and integration tests
  (`tests/unit/strategic/test_region_stabilization_materialization.py`, new, 8 tests covering
  arbitration win/retain/interrupt, raw-score-not-utility, real-enum-kind, target-position
  resolvability, shared score scale, and dedup-lookup inertness).
- Rewrote `TestStrategicPivotOnDanger::test_project_pivot_when_urgency_exceeds_resistance` and
  `::test_no_pivot_when_resistance_high` in `tests/unit/strategic/test_event_interpretation.py`
  to exercise the new scorer + arbiter path end-to-end, per AC4. Both tests' docstrings
  explicitly disclose the semantic shift: the old direct `urgency > interruption_resistance`
  pre-filter (`should_pivot`) no longer exists anywhere; `evaluate_project_switch()`'s own
  `retention_margin` gate is now the sole arbiter (Design Decision #5). The "exceeds resistance"
  fixture uses `interruption_resistance=0.01` and a low current-project score (1.0) rather than
  the original 0.3/50 -- required because a raw stabilize score capped at 2.9 cannot clear a
  50-point crafting project's effective score under the new unified formula; this is the
  disclosed real-behavior consequence the ticket's own Assumptions section anticipated ("today
  stabilize always wins the project slot, post-migration it competes and can lose").

No deviations from plan.md's Steps 1-9/11. Step 10 (docs + parity ledger) intentionally not
done in this pass per explicit scoping instruction -- left for the Document-Update/Parity
phase to complete using plan.md's already-drafted exact content.

## Test Summary
Ran `pytest tests/unit/strategic/ tests/unit/ai/goals/ -v` (the exact command test_plan.md
specifies): 268 passed, 0 failed. Includes all pre-existing regression-surface tests (unmodified
and green: `test_enum_drift.py`'s original 2 tests, `test_score_normalization.py`'s 5 tests,
`test_adventure_route_materialization.py`-equivalent coverage via
`test_expanded_goals.py`/`test_adventure_goal_scorer.py`, `test_social_contract_materialization.py`,
`test_strategic_social_contracts.py`) plus all new tests for this ticket (scorer unit tests,
enum-drift guards, materialization integration tests, and the 2 rewritten event-interpretation
tests). One minor, non-blocking coverage gap disclosed: `compute_danger_urgency()` has no direct
unit test calling it by name -- it is exercised indirectly through both consumers
(`interpret_regional_danger()` and `RegionStabilizationGoalScorer.score()`), both independently
passing, but no test pins that the two call sites compute the same value for the same region.

## Files Changed
- src/core/strategic.py
- src/systems/world_systems/events.py
- src/ai/goals/region_stabilization_scorer.py (new)
- src/ai/goals/__init__.py
- src/systems/strategic_systems/intelligence.py
- tests/unit/ai/goals/test_region_stabilization_goal_scorer.py (new)
- tests/unit/strategic/test_enum_drift.py
- tests/unit/strategic/test_region_stabilization_materialization.py (new)
- tests/unit/strategic/test_event_interpretation.py
- docs/mechanics/04_strategic_cognition.md (Document-Update: new "2a. Regional Danger and
  Stabilization Projects (LEG-RPG-116)" section, plus a §6.6 fourth-consumer paragraph for
  `_ADVENTURE_ROUTE_SCORE_MAX`)
- docs/architecture/2026-08-11-adventure-as-cognition-strategy-subcomponent-design.md
  (Document-Update: "Future Extension Patterns" Goal #4 marked done, Post-landing note,
  component diagram updated to move `events.py:98` out of the `BYPASS` subgraph)
- docs/parity_ledger/strategic_cognition.yaml (Architecture-Verify round-1 finding, fixed
  directly: new `STRAT-255` entry per plan.md Step 10's specification, plus `STRAT-066`/
  `STRAT-131`'s `test_path` updates; round 2 caught and fixed a wrong line citation
  (`:89`->`:164` for `ProjectKind.STABILIZE`); round 3 re-verified clean. Parity phase
  independently re-confirmed all citations and fixed one further minor line-range citation
  (`:1505-1535`->`:1505-1539`))
- docs/guidelines/intentional_divergences.md (Parity phase: new §2.43 disclosing both the
  accept-always-wins-to-arbitrated-competition change and the first-time-live-reachability
  change, Rationale class Enforced)

## Completion Summary
Generalized the GoalScorer-wrapper pattern to `events.py`'s regional-danger stabilize-project
bypass. Added `ProjectKind.STABILIZE`/`GoalKind.REGION_STABILIZATION`, extracted a shared
`compute_danger_urgency()` helper, simplified `interpret_regional_danger()` to concern-generation
only, and added `RegionStabilizationGoalScorer` + a matching materialization branch in
`evaluate_strategic_intent()` so a regional-danger candidate must clear `evaluate_project_switch()`
like every other tier-5 candidate instead of unconditionally overwriting `current_project_id`.
This also makes LEG-RPG-116 live-reachable in production for the first time (cadence/budget-gated,
same as sibling scorers) -- a disclosed, intentional behavior-availability change, not merely a
bypass-closure. All 6 acceptance criteria satisfied and covered by 30 new/rewritten tests plus the
full specified regression suite (268 passed, 0 failed).

The plan itself went through 2 Review rounds -- round 1 found a real overclaim (reachability
described as "unconditional every tick" when it's actually cadence-gated and work-queue-budgeted,
same throttling as sibling scorers), fixed and re-approved. Architecture-Verify ran 3 rounds:
round 1 found the Document-Update docs cited a parity-ledger entry (`STRAT-255`) as already
recorded before it existed, and left 2 P0 entries (`STRAT-066`/`STRAT-131`) with `test_path: null`
despite the plan's own spec -- fixed directly per plan.md Step 10. Round 2 found a wrong line
citation in `STRAT-255`'s `v2_evidence` (`:89`, actually `DirectiveKind.STABILIZE`, an unrelated
member) -- fixed to the real `:164`. Round 3 APPROVED with no further gaps. The subsequent Parity
phase independently re-confirmed the ledger fixes, corrected one further minor line-range citation
in `STRAT-255`, and added `docs/guidelines/intentional_divergences.md` §2.43 for the two disclosed
behavior changes.
