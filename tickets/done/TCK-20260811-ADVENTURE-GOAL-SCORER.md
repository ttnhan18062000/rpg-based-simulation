---
status: historical
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260811-ADVENTURE-GOAL-SCORER
phase: done
date: 2026-08-11
tags: [cognition, adventure]
---

# TCK-20260811-ADVENTURE-GOAL-SCORER

## Title
Build AdventureGoalScorer and its materialization path

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Create a new AdventureGoalScorer implementing the existing GoalScorer protocol, registered under a new GoalKind.ADVENTURE_ROUTE enum member, that wraps AdventureDecisionService.decide() unchanged and folds it into GoalRegistry.get_all_scores() as one candidate among many in tier 5 of the strategic hierarchy -- instead of running as a structurally-independent earlier pipeline phase invisible to tiers 1-4. This subjects adventure routing to the same tier-5 arbitration as every other project-switch candidate.

## Scope
- New GoalKind.ADVENTURE_ROUTE member added to src/core/strategic.py
- New AdventureGoalScorer class in src/ai/goals/ implementing GoalScorer.score(entity, state) -> GoalScore, wrapping AdventureDecisionService.decide() unchanged
- Registration via GoalRegistry.register(GoalKind.ADVENTURE_ROUTE, AdventureGoalScorer()) in src/ai/goals/__init__.py
- Utility normalization: utility = (raw_score / _ADVENTURE_ROUTE_SCORE_MAX) * _GOAL_UTILITY_SCORE_MAX, with raw_score of 2.9 normalizing to utility==100.0 exactly
- GoalScore.metadata carries route_family and raw_score
- New materialization branch (tier-5 winner path) calling RouteToProjectMapper.map_to_states(score=metadata["raw_score"], ...) across all 15 mapped route families -- never best_candidate.utility
- Ineligible entities / DEFER_WITH_REASON results produce GoalScore(utility=0, target_id=None) that never clears the 20.0 tier-5 floor
- Dedicated regression test asserting materialized ADVENTURE_ROUTE winner's ProjectState.score equals metadata["raw_score"], never best_candidate.utility

## Out of Scope
- Wiring AdventureGoalScorer into src/engine/pipeline.py or deleting AdventureDecisionPhase -- that is DELETE-ADVENTURE-DECISION-PHASE's (C3) job, gated on this ticket and ADVENTURE-SHADOW-MIGRATION-GATE (C4) landing first
- Shadow-mode comparison test and /simq-audit pre-cutover gate -- ADVENTURE-SHADOW-MIGRATION-GATE's (C4) job
- _threat_resolved() relocation and evaluate_project_switch() signature change -- THREAT-RESOLVED-ARBITER-RELOCATION's (C2) job
- Closing STRAT-185's null test_path is a nice-to-have opportunity, not guaranteed in this ticket's scope

## Acceptance Criteria
- [x] GoalKind.ADVENTURE_ROUTE is a new member in src/core/strategic.py; AdventureGoalScorer (new, in src/ai/goals/) implements GoalScorer.score(entity, state) -> GoalScore and is registered via GoalRegistry.register(GoalKind.ADVENTURE_ROUTE, AdventureGoalScorer()) in src/ai/goals/__init__.py
- [x] AdventureGoalScorer.score() calls AdventureDecisionService.decide() unchanged and returns GoalScore(kind=GoalKind.ADVENTURE_ROUTE, utility=(raw_score/_ADVENTURE_ROUTE_SCORE_MAX)*_GOAL_UTILITY_SCORE_MAX, metadata={"route_family":...,"raw_score":raw_score,...}); a raw_score of 2.9 normalizes to utility==100.0 exactly
- [x] When ADVENTURE_ROUTE wins tier 5, the new materialization branch calls RouteToProjectMapper.map_to_states(score=metadata["raw_score"], ...) -- never best_candidate.utility -- across all 15 mapped route families, preserving the existing (None,None) handling for DEFER_WITH_REASON
- [x] A dedicated regression test asserts the materialized ADVENTURE_ROUTE winner's ProjectState.score equals metadata["raw_score"], never best_candidate.utility
- [x] Ineligible entities and DEFER_WITH_REASON results produce GoalScore(utility=0, target_id=None) that never clears the 20.0 tier-5 floor
- [x] Tie-break ordering (sort by -utility then kind) has a deliberate string-value decision for GoalKind.ADVENTURE_ROUTE, not an arbitrary one

## Related Tickets
- TCK-20260811-INTERRUPTION-BYPASS-RETENTION-MARGIN-SCALE-BUG
- TCK-20260810-PROJECT-SWITCH-BYPASS-GENERALIZATION
- TCK-20260810-COGNITION-PROFILE-ADVENTURE-ELIGIBILITY
- TCK-20260810-COGNITION-ELIGIBILITY-BYPASS-DOCS
- TCK-20260810-D22-DORMANT-WIRING-AUDIT
- TCK-20260810-COMBAT-BRAVERY-QUARTILE-ENGAGEMENT-INVERSION
- TCK-20260811-HARVEST-CRAFT-EVENT-EXTRACTION-REGRESSION (follow-up filed for the 2 pre-existing,
  unrelated test failures discovered during this ticket's Test phase — see Completion Summary)

## Related Docs
- docs/mechanics/04_strategic_cognition.md
- docs/parity_ledger/strategic_cognition.yaml

## Related Stored Artifacts
None.

## Related Code Areas
- src/ai/goals/base.py
- src/ai/goals/scorers.py
- src/ai/goals/__init__.py
- src/core/strategic.py
- src/domains/adventure/service.py
- src/domains/adventure/mapper.py
- src/domains/adventure/phase.py
- src/domains/adventure/schema.py
- src/domains/adventure/scoring.py
- src/systems/strategic_systems/intelligence.py
- src/engine/pipeline.py

## Assumptions / Open Questions
- RouteFamily has 16 members but _MAP covers 15 (DEFER_WITH_REASON excluded, returns (None,None)) -- implementation must preserve this None-handling, not force all 16 through the mapper
- STRAT-185 parity entry still has test_path:null; closing it here is an opportunity, not a guaranteed scope item
- Getting the raw_score-not-utility rule wrong (design doc §4) would independently reproduce the just-fixed TCK-20260811-INTERRUPTION-BYPASS-RETENTION-MARGIN-SCALE-BUG defect class
- Related design doc: docs/architecture/2026-08-11-adventure-as-cognition-strategy-subcomponent-design.md

## Implementation Notes

Implemented exactly per `staging_artifacts/TCK-20260811-ADVENTURE-GOAL-SCORER/plan.md`'s 7 steps
(twice-reviewed, APPROVED). No deviations from the plan's approach or code shape; all Do-NOT-touch
guards were respected (`phase.py`, `pipeline.py`, `evaluate_project_switch()`'s signature,
`RouteToProjectMapper._MAP`, `tactical.py` were all left unmodified — verified by diff review).

1. Added `GoalKind.ADVENTURE_ROUTE = "z_adventure_route"` to `src/core/strategic.py`, immediately
   after `GUILD`, with the plan's inline tie-break rationale comment.
2. Created `src/ai/goals/adventure_scorer.py` with `AdventureGoalScorer`, matching plan.md's Step 2
   code block verbatim: lazy/function-local imports throughout (the eligibility helper import and
   the `intelligence.py` constants import), the corrected transitive circular-import comment
   (crediting the lazy-import pattern for keeping the real `phase.py -> src.systems.strategic ->
   intelligence.py -> src.ai.goals` path safe, not claiming no path exists), the
   opportunities -> generate -> decide replication, and `_resolve_placeholder_target_pos()` for the
   3 route families (`RECOVER`/`ASK_INFORMATION`/`FORM_PARTY`) that never carry
   `target_node_id`/`source_opportunity_ids` -- nearest inn else `town_center` for forced RECOVER,
   `town_center` for forced ASK_INFORMATION, nearest real ally position else the entity's own
   position for FORM_PARTY.
3. Registered `AdventureGoalScorer` in `src/ai/goals/__init__.py`, import placed after
   `from src.ai.goals.base import GoalRegistry` per plan.md's ordering rationale, and the
   `GoalRegistry.register(GoalKind.ADVENTURE_ROUTE, AdventureGoalScorer())` call added after the
   10 existing registrations.
4. Added the `ADVENTURE_ROUTE` materialization branch in
   `src/systems/strategic_systems/intelligence.py`'s tier-5 winner-construction site
   (`if best_candidate.kind == GoalKind.ADVENTURE_ROUTE: ... else: <original generic path
   unchanged>`), calling `RouteToProjectMapper.map_to_states(score=best_candidate.metadata.get(
   "raw_score", 0.0), ...)` -- never `best_candidate.utility` -- with a defensive `(None, None)`
   no-op matching the mapper's existing `DEFER_WITH_REASON` contract. Added `GoalKind` to the
   existing `src.core.strategic` import block and a new top-level
   `from src.domains.adventure.mapper import RouteToProjectMapper` import (confirmed non-circular
   by reading `mapper.py` directly).
5. Wrote 14 unit tests in the new `tests/unit/ai/goals/test_adventure_goal_scorer.py` (new
   directory, no `__init__.py`, matching the existing `tests/unit/ai/` layout) covering AC1, AC2,
   AC5, AC6, and the 4 Risk #1 target_pos-resolution cases plan.md's Step 5 added (replacing
   test_plan.md's original placeholder test, which was pending plan.md's resolution).
6. Wrote 3 tests in the new `tests/unit/strategic/test_adventure_route_materialization.py`
   covering AC3/AC4 (raw-score-not-utility materialization, `(None, None)` DEFER_WITH_REASON
   defensive handling) plus the reviewer-added
   `test_form_party_materialized_objective_is_tactically_resolvable_not_a_stall`, which runs
   `evaluate_strategic_intent()` end-to-end and calls
   `TacticalDecisionSystem._resolve_target_position()` directly on the materialized objective,
   including the negative check reproducing the old "wins but stalls forever" failure mode.
7. Ran the exact scoped pytest command from plan.md/test_plan.md.

**Notable mid-session incident (recovered, no data lost):** while isolating a suspected
regression, a `git stash` / `git stash pop` cycle used to temporarily diff against the base branch
did not cleanly restore 3 already-tracked files (`src/core/strategic.py`,
`src/ai/goals/__init__.py`, `src/systems/strategic_systems/intelligence.py`) even though the pop
reported success. Recovered by extracting those 3 files directly from the still-present stash
entry (`git checkout stash@{0} -- <paths>`) and diffing them against the intended changes to
confirm byte-for-byte correctness before proceeding; the stash itself was left untouched (not
dropped) since it also contained unrelated pre-existing working-tree state from outside this
ticket's scope (agent-monitoring files) that this session has no authority to discard.

**Pre-existing, unrelated test failures noted, not fixed (out of scope):**
`tests/integration/domains/adventure/test_harvest_to_event.py::
test_crafting_project_produces_item_crafted_event_through_full_pipeline` and
`::test_reach_resource_arrival_produces_resource_harvested_event_through_full_pipeline` both fail
identically on the unmodified base branch (confirmed via `git stash` to revert to base and
re-running just that file). They exercise event-extraction for crafting/harvest intents, not
`GoalKind`/`AdventureGoalScorer`/tier-5 arbitration, and neither investigation.md's nor
test_plan.md's regression-surface listing names this file -- it was only swept in incidentally by
the `tests/integration/domains/adventure/` directory glob in the Step 7 command. Left unfixed per
the ticket's scope guards (touching `event_extractor.py`/`tactical.py`/`service.py` to chase this
would itself be undisclosed scope creep) and per CLAUDE.md's rule against routing around a
failing check instead of reporting it truthfully.

`test_plan.md`'s AC3/AC4 and AC5 sections were stale relative to plan.md's revised Step 5/Step 6
(the placeholder test for Risk #1, and the missing third materialization test) -- updated in the
same session to match what was actually implemented (see that file's edited sections; no separate
"Deviations" section was needed in `plan.md` itself since Implement followed plan.md exactly, the
staleness was only in test_plan.md, which plan.md's own Step 5/6 text says supersedes it).

## Test Summary

Scoped regression command (from plan.md/test_plan.md) run twice: once during isolated development
of each new test file, and once as the final Step 7 full-suite pass:

```
pytest tests/unit/ai/goals/ tests/unit/strategic/test_expanded_goals.py tests/unit/strategic/test_score_normalization.py tests/unit/strategic/test_enum_drift.py tests/unit/strategic/test_adventure_route_materialization.py tests/unit/domains/adventure/ tests/integration/domains/adventure/ -v
```

Result: **107 passed, 2 failed** (0 errors). The 2 failures
(`tests/integration/domains/adventure/test_harvest_to_event.py`, both tests) are pre-existing and
unrelated to this ticket -- confirmed identical on the base branch via `git stash` before any of
this ticket's changes were applied (see Implementation Notes). All 17 new tests added by this
ticket (14 in `test_adventure_goal_scorer.py`, 3 in `test_adventure_route_materialization.py`)
pass, and the full pre-existing regression surface named by investigation.md/test_plan.md
(`test_expanded_goals.py`, `test_score_normalization.py`, `test_enum_drift.py`,
`test_phase3_adventure_decision_service.py`, `test_phase3_adventure_decision_boundary.py`,
`test_phase3_adventure_decision_phase.py`, and all other files under `tests/unit/domains/adventure/`)
passes unmodified -- no existing test required an edit, confirming `decide()`/`generate()`/
`AdventureDecisionPhase` were not disturbed.

## Files Changed

- `src/core/strategic.py` -- added `GoalKind.ADVENTURE_ROUTE = "z_adventure_route"`
- `src/ai/goals/adventure_scorer.py` -- new file, `AdventureGoalScorer` class
- `src/ai/goals/__init__.py` -- registered `AdventureGoalScorer`
- `src/systems/strategic_systems/intelligence.py` -- new `ADVENTURE_ROUTE` materialization branch,
  2 new imports (`GoalKind` added to existing `src.core.strategic` import, new
  `RouteToProjectMapper` import)
- `tests/unit/ai/goals/test_adventure_goal_scorer.py` -- new file, new directory
  (`tests/unit/ai/goals/`), 14 unit tests
- `tests/unit/strategic/test_adventure_route_materialization.py` -- new file, 3 integration tests
- `docs/mechanics/04_strategic_cognition.md` -- new tier-5-candidate note in §2, and a note on
  `_ADVENTURE_ROUTE_SCORE_MAX`'s second consumer in §6.8, both explicitly stating the scorer is
  registered but not yet wired/live
- `docs/mechanics/adventure_routing_contract.md` -- `last_verified` bump + new paragraph noting a
  second entry point (`AdventureGoalScorer`) now exists as code, not yet wired
- `docs/parity_ledger/strategic_cognition.yaml` -- new `STRAT-252` entry (`status: verified`),
  documenting the scorer as real/tested/registered but not yet reachable in a live tick
- `staging_artifacts/TCK-20260811-ADVENTURE-GOAL-SCORER/test_plan.md` -- synced AC3/AC4/AC5
  sections (stale placeholder text) to match plan.md's revised Step 5/Step 6 and what was actually
  implemented
- `tickets/inprogress/TCK-20260811-ADVENTURE-GOAL-SCORER.md` -- this file (Status, Acceptance
  Criteria, Implementation Notes, Test Summary, Files Changed, Completion Summary)

## Completion Summary

Implemented `AdventureGoalScorer` (new `src/ai/goals/adventure_scorer.py`) as a `GoalScorer`
registered under the new `GoalKind.ADVENTURE_ROUTE` (`src/core/strategic.py`), wrapping the
unchanged opportunities -> generate -> decide adventure-routing sequence and folding it into
`GoalRegistry.get_all_scores()` as one tier-5 candidate among 11. Added a matching materialization
branch in `StrategicIntelligenceSystem.evaluate_strategic_intent()`
(`src/systems/strategic_systems/intelligence.py`) that maps a winning `ADVENTURE_ROUTE` candidate
through `RouteToProjectMapper` using the raw route score (never the normalized utility), and
resolved the reviewer-flagged "wins but stalls forever" gap for the 3 route families
(`RECOVER`/`ASK_INFORMATION`/`FORM_PARTY`) that lack a real target by synthesizing a real,
resolvable `target_pos` alongside the placeholder `target_id`. All 6 acceptance criteria are met
and verified by 17 new tests; the full scoped regression suite passes except 2 pre-existing,
unrelated failures (`tests/integration/domains/adventure/test_harvest_to_event.py`) independently
confirmed present on the base branch before this ticket's changes via 2 separate git-stash
comparisons, tracked as follow-up ticket TCK-20260811-HARVEST-CRAFT-EVENT-EXTRACTION-REGRESSION.
`AdventureGoalScorer` is registered but intentionally not yet wired into `src/engine/pipeline.py`
(that is a later, separately-gated ticket's job per this ticket's Out of Scope section).
