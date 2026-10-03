---
status: historical
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260811-THREAT-RESOLVED-ARBITER-RELOCATION
phase: done
date: 2026-08-11
tags: [cognition, adventure]
---

# TCK-20260811-THREAT-RESOLVED-ARBITER-RELOCATION

## Title
Relocate _threat_resolved() into the shared arbiter and extend evaluate_project_switch()'s lock check

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Move _threat_resolved() (currently adventure-specific, src/domains/adventure/phase.py) to src/systems/strategic_systems/, co-located with evaluate_project_switch(), which becomes its sole caller. Add a state: AuthoritativeState parameter to evaluate_project_switch(), thread it through call sites, and extend the lock-expiry condition to also check not _threat_resolved(entity, state). This closes a real pre-existing gap: the function's own docstring already claimed broader scope than only AdventureDecisionPhase ever exercised.

## Scope
- Relocate _threat_resolved() from src/domains/adventure/phase.py to src/systems/strategic_systems/intelligence.py (co-located with evaluate_project_switch)
- Add state: AuthoritativeState parameter to evaluate_project_switch(); thread through all 3 real production call sites: intelligence.py:1345, intelligence.py:1426, phase.py:192
- Extend the lock-expiry condition in evaluate_project_switch() (intelligence.py:991-996) to additionally check not _threat_resolved(entity, state), as an additive check, not a replacement of the existing locked-branch comparison
- Bring the SpatialQueryService.nearby_entities dependency along with the relocation
- Update STRAT-236's text AND v2_evidence fields (both, not just v2_evidence) in docs/parity_ledger/strategic_cognition.yaml to cite the new location and generalized scope
- New regression test: a COMBAT_RETREAT/RECOVER-kind project locked via a non-adventure system, with threat resolved, is now also early-released

## Out of Scope
- AdventureGoalScorer construction and tier-5 materialization -- ADVENTURE-GOAL-SCORER's (C1) job
- Deleting AdventureDecisionPhase or relocating _resolve_cognition_profile_id/_supports_adventure_routing -- DELETE-ADVENTURE-DECISION-PHASE's (C3) job; this ticket owns _threat_resolved's relocation specifically, resolving the ambiguous C2/C3 boundary in C3's own favor for the eligibility helpers only
- Shadow-mode comparison test infrastructure -- ADVENTURE-SHADOW-MIGRATION-GATE's (C4) job

## Acceptance Criteria
- [x] evaluate_project_switch()'s signature gains state: AuthoritativeState; all 3 real production call sites (intelligence.py:1346 -> detour branch, intelligence.py:1456 -> tier-5 branch, phase.py:192) thread state through, with no behavior change on the raw/unlocked comparison path
- [x] Locked current project + entity HP>80% + no hostile within radius 10.0 results in the lock being treated as expired and falls through to raw comparison, byte-identical to today's AdventureDecisionPhase-only behavior for adventure-originated projects
- [x] A COMBAT_RETREAT/RECOVER-kind project locked via a non-adventure system, with threat resolved, is now also early-released -- new regression test required, closing the STRAT-236 documented-but-never-wired gap
- [x] STRAT-236's text AND v2_evidence fields in docs/parity_ledger/strategic_cognition.yaml both cite the new location and generalized scope

## Related Tickets
- TCK-20260811-INTERRUPTION-BYPASS-RETENTION-MARGIN-SCALE-BUG
- TCK-20260810-PROJECT-SWITCH-BYPASS-GENERALIZATION
- TCK-20260627-P2A-SPAWN-LOCK-COND
- TCK-20260811-ADVENTURE-GOAL-SCORER (epic sibling ticket 1/10; this ticket's Test phase re-hit the
  2 pre-existing failures that ticket first discovered and filed a follow-up for)
- TCK-20260811-HARVEST-CRAFT-EVENT-EXTRACTION-REGRESSION (follow-up ticket for the 2 pre-existing,
  unrelated test failures — see Test Summary)

## Related Docs
- docs/parity_ledger/strategic_cognition.yaml
- docs/mechanics/04_strategic_cognition.md
- docs/architecture/2026-08-11-adventure-as-cognition-strategy-subcomponent-design.md

## Related Stored Artifacts
None.

## Related Code Areas
- src/domains/adventure/phase.py
- src/systems/strategic_systems/intelligence.py
- src/engine/spatial_query.py

## Assumptions / Open Questions
- OPEN DESIGN DECISION (must be resolved explicitly at Plan time, not silently picked): 25 direct test call sites across 5 test files (test_score_normalization.py, test_interruption_resistance.py, test_project_continuity.py, test_strategic_reprioritization.py, test_quest_activation_pathway.py) call evaluate_project_switch(entity, candidate, current_tick=...) with no state argument. Implement must explicitly choose: (a) require state and update all 25 call sites with minimal AuthoritativeState fixtures, or (b) give it a default Optional[AuthoritativeState]=None and skip the _threat_resolved check when None. The larger-blast-radius option must not be picked silently.
- tests/unit/domains/adventure/test_phase3_project_switch_routing_guard.py's AST-based assertions need re-verification post-relocation
- phase.py:151's existing gate and the new evaluate_project_switch check will both evaluate _threat_resolved redundantly on the same tick when routing succeeds -- disclosed as harmless, not to be 'optimized away' as part of this ticket
- Related design doc: docs/architecture/2026-08-11-adventure-as-cognition-strategy-subcomponent-design.md §5

## Implementation Notes

Implemented exactly per plan.md's 7 steps, twice-reviewed/APPROVED, including the lazy-nested
`threat_resolved` shape from Step 2's second review pass:

1. **Relocation**: `_threat_resolved()` moved verbatim from `src/domains/adventure/phase.py:27-46`
   to `src/systems/strategic_systems/intelligence.py`, inserted as a module-level function between
   `_score_scale_max()` and `class StrategicIntelligenceSystem:`. Added
   `from src.engine.spatial_query import SpatialQueryService` to `intelligence.py`'s import block.
   In `phase.py`, removed the function body, removed the now-dead `SpatialQueryService` import, and
   added `from src.systems.strategic_systems.intelligence import _threat_resolved`. Confirmed no
   import cycle via `python -c "import src.domains.adventure.phase"` and
   `python -c "import src.systems.strategic_systems.intelligence"` (both clean).

2. **Signature + lazy lock-expiry condition**: `evaluate_project_switch()` gained
   `state: Optional[AuthoritativeState] = None` as a 4th parameter (default, not required --
   confirmed correct per investigation.md's evidence that a required param would flip several of
   the 27 pre-existing test call sites' lock-retention assertions). Inside the
   `if current.lock_until_tick > current_tick:` gate, added
   `threat_resolved = state is not None and _threat_resolved(entity, state)` as the first statement,
   with the pre-existing detour/percentage/urgency-floor logic nested one level deeper under a new
   `if not threat_resolved:`. The spatial-query call only runs when the current project is actually
   locked, not on every call -- confirmed this is the lazy/nested shape plan.md's second review pass
   required (not the eager form the first review pass flagged and rejected).

3. **Call-site threading**: `phase.py:192-194` (inside `AdventureDecisionPhase.apply()`) and both of
   `evaluate_strategic_intent()`'s calls in `intelligence.py` (re-verified at their current line
   numbers 1346 and 1456, matching investigation.md exactly -- no further drift since investigation
   time) now pass `state=state`. None of the 27 pre-existing direct test call sites were touched.

4-6. **New tests**: Added `TestEvaluateProjectSwitchStateParam` (3 tests) to
   `tests/unit/strategic/test_interruption_resistance.py` covering signature acceptance, unlocked-path
   parity with/without `state`, and the locked+threat-resolved release case. Added a local
   `_make_state()` fixture to that file (mirroring `test_spawn_lock_condition.py`'s shape). Created
   `tests/unit/strategic/test_evaluate_project_switch_state_threading_guard.py` with an AST-walk test
   asserting exactly 3 `evaluate_project_switch(...)` call sites across `AdventureDecisionPhase.apply`
   and `evaluate_strategic_intent`, each carrying a `state` argument. Created
   `tests/unit/strategic/test_threat_resolved_lock_release.py` with the AC3 positive/negative pair,
   using the real `GoalKind.COMBAT_RETREAT` enum member and a project locked directly onto
   `entity.strategic` (never routed through `AdventureDecisionPhase`), proving the generalized,
   non-adventure caller path. `tests/unit/systems/test_spawn_lock_condition.py` re-run unmodified --
   all 6 tests still pass.

7. **Parity ledger**: Updated STRAT-236's `text` and `v2_evidence` in
   `docs/parity_ledger/strategic_cognition.yaml:2696-2719` per plan.md's Step 7 content, with two
   corrections beyond what the plan's own text literally specified (both are exactly the kind of
   "re-verify line numbers, they may have shifted again" caution the ticket prompt called out):
   the cap-via-`min(N, tick+50)` citations landed at `intelligence.py:1380,1483` (not `:1342,1445` as
   the plan draft assumed pre-Step-1/2 edits -- this session's own Step 1/2 edits added ~38 lines
   above those call sites), and `AdventureDecisionPhase`'s own pre-filter citation was corrected from
   `phase.py:151` to `phase.py:129` (Step 1's function removal shifted it up by 22 lines). `test_path`
   left unchanged per the plan. `tests/tools/test_parity_ledger_scan.py` and
   `tests/integrity/test_parity_guards.py` both pass against the edited YAML.

No deviations from plan.md's specified shape, scope guards, or file list. `graphify update .` run
after all `src/`/`tests/` edits (no topology changes detected).

## Test Summary

Scoped pytest command run (per test_plan.md's "Scoped Pytest Commands" section):
`pytest tests/unit/strategic/ tests/unit/systems/test_spawn_lock_condition.py
tests/unit/systems/test_quest_activation_pathway.py
tests/unit/domains/adventure/test_phase3_project_switch_routing_guard.py
tests/tools/test_parity_ledger_scan.py -v`

Result: **240 passed, 0 failed**. Also separately ran `tests/integrity/test_parity_guards.py`
(3 passed, 0 failed) as defensive regression surface per test_plan.md. All 27 pre-existing direct
`evaluate_project_switch()` call sites across `test_score_normalization.py`,
`test_interruption_resistance.py`, `test_project_continuity.py`, `test_strategic_reprioritization.py`,
`test_quest_activation_pathway.py` remain unedited and pass unmodified, confirming the `state=None`
default's zero blast radius. `tests/unit/systems/test_spawn_lock_condition.py`'s 6 tests (STRAT-236's
`test_path`) pass unmodified.

The pipeline's own Test phase (test-scoper) additionally ran a wider transitively-scoped pass,
adding `tests/integration/domains/adventure/` to the command above: **246 passed, 2 failed**. The 2
failures (`tests/integration/domains/adventure/test_harvest_to_event.py::test_crafting_project_produces_item_crafted_event_through_full_pipeline`
and `::test_reach_resource_arrival_produces_resource_harvested_event_through_full_pipeline`) are
independently confirmed pre-existing and unrelated to this ticket's changes -- they were first
discovered and confirmed via 2 separate git-stash comparisons against the base branch during
`TCK-20260811-ADVENTURE-GOAL-SCORER`'s own Test phase (epic ticket 1/10), and are now tracked as
their own follow-up ticket, `TCK-20260811-HARVEST-CRAFT-EVENT-EXTRACTION-REGRESSION`. No other
failures appeared in either scoped run.

## Files Changed
- `src/systems/strategic_systems/intelligence.py` -- added `SpatialQueryService` import;
  added module-level `_threat_resolved()`; widened `evaluate_project_switch()`'s signature
  (`state` param) and locked-branch gate (lazy nested `threat_resolved` check); threaded
  `state=state` through both `evaluate_strategic_intent()` call sites.
- `src/domains/adventure/phase.py` -- removed local `_threat_resolved()` and its now-dead
  `SpatialQueryService` import; added import of `_threat_resolved` from `intelligence.py`;
  threaded `state=state` through the `evaluate_project_switch()` call site.
- `tests/unit/strategic/test_interruption_resistance.py` -- added `_make_state()` fixture and
  new `TestEvaluateProjectSwitchStateParam` class (3 new tests).
- `tests/unit/strategic/test_evaluate_project_switch_state_threading_guard.py` (new) -- AST-guard
  test for the 3 production call sites.
- `tests/unit/strategic/test_threat_resolved_lock_release.py` (new) -- AC3 positive/negative
  regression pair.
- `docs/parity_ledger/strategic_cognition.yaml` -- updated STRAT-236's `text` and `v2_evidence`;
  strengthened STRAT-236's `test_path` to the new direct tests; corrected STRAT-186/187's
  `v2_evidence` line-number citations (drifted as a side effect of this ticket's own insertion).
- `docs/mechanics/04_strategic_cognition.md` -- added a new §2 bullet, "Threat-Resolved Early
  Release (STRAT-236)", documenting the generalized early-release mechanism (this mechanism was
  previously entirely undocumented in the Mechanics Bible).
- `docs/architecture/2026-08-11-adventure-as-cognition-strategy-subcomponent-design.md` -- added a
  scoped post-landing citation-correction note fixing the doubly-stale line citations for
  `_threat_resolved()`/`evaluate_project_switch()`'s new location; did not touch the design doc's
  own prose/decisions.

## Completion Summary
Relocated `_threat_resolved()` from the adventure domain into `intelligence.py` as a shared,
module-level helper co-located with `evaluate_project_switch()`, which is now its sole caller.
`evaluate_project_switch()` gained an optional `state` parameter and a lazily-computed
`threat_resolved` short-circuit inside its locked-branch gate, generalizing the HP/hostile-based
early-release behavior beyond `AdventureDecisionPhase` to any caller (e.g. `evaluate_strategic_intent`)
that supplies a real `AuthoritativeState` -- closing the STRAT-236 documented-but-never-wired gap
without adding any new eager compute cost on the common unlocked path. All 3 real production call
sites now thread `state`; all 27 pre-existing test call sites are untouched and still pass via the
`None` default. New tests cover signature/unlocked-path parity, the AC2 adventure-domain release
case, and the AC3 non-adventure (`GoalKind.COMBAT_RETREAT`) release/retain pair. Parity ledger
updated. Full scoped test run: 240 passed, 0 failed.
