---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260907-DORMANT-CLOSURE-CI-REGRESSION-FIXUP
phase: done
date: 2026-09-07
tags: [testing, simulation-quality]
---

# TCK-20260907-DORMANT-CLOSURE-CI-REGRESSION-FIXUP

## Title
Fix 3 real CI regressions surfaced by PR #144 (Dormant Mechanism Closure) — regression-scope gaps, not architectural bugs

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
An independent review of PR #144 (`rpg-feature-planning` session, requested by the repo owner)
reproduced 3 real, currently-failing CI clusters, all sharing one root cause: two Dormant
Mechanism Closure tickets (`TCK-20260907-CHRONICLE-BELIEF-CONSUMER-WIRING`,
`TCK-20260907-INFORMATION-SOURCE-PROFILES-PERSISTENCE-DECISION`) changed a widely-shared function
signature and a field's persistence semantics, but their own Test phases only verified against
tests they already knew were directly relevant — missing sibling files elsewhere in the repo with
their own hand-rolled mocks or hardcoded assumptions about the exact behavior that changed.
Independently reproduced and confirmed by the orchestrating session before filing this ticket.

## Scope
- **Cluster A** (7 tests): `AdventureDecisionService.decide()` gained a new `belief_institutions`
  kwarg (`src/ai/goals/adventure_scorer.py:165`, unconditionally passed). 5 test files have their
  own local `_fake_decide()` stub; 1 (`tests/unit/ai/goals/test_adventure_goal_scorer.py`) was
  already updated correctly, the other 4 were not:
  `tests/unit/strategic/test_adventure_route_materialization.py`,
  `tests/unit/strategic/test_evaluate_all_strategic_intents_routing_family.py`,
  `tests/unit/strategic/test_fused_strategic_pass_routing_family.py`,
  `tests/unit/observability/test_event_shapers_strategy.py`.
- **Cluster B** (2 tests): `tests/integration/test_world_profile_feature_flag_guardrail.py`'s own
  hand-maintained world-fixture list never got `unit_information_routing_pilot` added.
- **Cluster C** (1 test): `tests/integration/domains/test_fused_loop.py::
  test_branch_b_fires_across_real_tick_boundary_after_self_model_patch_materialization` hardcodes
  the *old* Bounded/tick-1-only value for `information_source_profiles`
  (`assert next_state.information_source_profiles == []`) — the exact behavior
  `TCK-20260907-INFORMATION-SOURCE-PROFILES-PERSISTENCE-DECISION` intentionally changed to
  persistent. Update the assertion to the real new expected value, not a design revert.

## Out of Scope
- Any other item from the Dormant Mechanism Closure epic's scope.
- Re-litigating whether decisions 6(i) (persistence reclassification) or 9(ii) (belief-institution
  wiring) were the right calls — that is tracked separately (see Related Tickets).

## Acceptance Criteria
- [x] All 3 clusters (10 tests total) pass.
- [x] No new regression introduced in the broader touched-area suite.

## Related Tickets
- `TCK-20260907-EPIC-RPG-DORMANT-MECHANISM-CLOSURE` (parent epic)
- `TCK-20260907-CHRONICLE-BELIEF-CONSUMER-WIRING` (`tickets/done/` — source of Cluster A)
- `TCK-20260907-INFORMATION-SOURCE-PROFILES-PERSISTENCE-DECISION` (`tickets/done/` — source of
  Clusters B and C)

## Related Docs
None — pure test/fixture fixups, no behavior or doc change.

## Related Stored Artifacts
None — hotfix tier, no staging artifacts required.

## Related Code Areas
- `tests/unit/strategic/`, `tests/unit/observability/test_event_shapers_strategy.py`
- `tests/integration/test_world_profile_feature_flag_guardrail.py`
- `tests/integration/domains/test_fused_loop.py`

## Assumptions / Open Questions
- Reviewer's own suggested structural fix (replace hand-rolled `_fake_decide` functions with
  `unittest.mock.create_autospec(AdventureDecisionService.decide)` so future signature drift is
  caught at collection time) is a real, valuable follow-up but out of this hotfix's own minimal
  scope — noted here for a future ticket, not actioned.

## Implementation Notes
Fixed all 3 clusters directly:
1. **Cluster A**: added `belief_institutions=()` (matching the real default/no-op value) to each
   of the 4 `_fake_decide` stub signatures, and to each stub's own `return`/body where it forwards
   kwargs, mirroring exactly how `test_adventure_goal_scorer.py`'s own already-correct stub handles
   it.
2. **Cluster B**: added `unit_information_routing_pilot` to
   `test_world_profile_feature_flag_guardrail.py`'s fixture, matching its sibling
   `unit_information_source`/`unit_information_density` entries' exact shape (uses the default
   `information` profile resolution path, no world-specific override needed).
3. **Cluster C**: updated the assertion in `test_fused_loop.py` from
   `assert next_state.information_source_profiles == []` to assert the real persisted value
   (the same `InformationSourceProfile` the fixture seeds, still present after the tick boundary) —
   this is the exact intended behavior change, not a regression.

## Test Summary
Before fix: 10 tests failing across 3 clusters (7 + 2 + 1), independently reproduced by both the
reviewing session and the orchestrator. After fix: all 10 pass.
`pytest tests/unit/strategic/ tests/unit/observability/test_event_shapers_strategy.py
tests/integration/test_world_profile_feature_flag_guardrail.py
tests/integration/domains/test_fused_loop.py -q` — full pass, 0 failed.
Broader regression: `pytest tests/unit/ai/goals/ tests/unit/domains/adventure/
tests/unit/domains/campaigns/ tests/architecture/ -q -m "not slow"` — no new failures.

## Files Changed
- `tests/unit/strategic/test_adventure_route_materialization.py`
- `tests/unit/strategic/test_evaluate_all_strategic_intents_routing_family.py`
- `tests/unit/strategic/test_fused_strategic_pass_routing_family.py`
- `tests/unit/observability/test_event_shapers_strategy.py`
- `tests/integration/test_world_profile_feature_flag_guardrail.py`
- `tests/integration/domains/test_fused_loop.py`

## Completion Summary
All 3 CI failure clusters an independent review (`rpg-feature-planning` session) reproduced and
root-caused were confirmed real by the orchestrator (reproduced independently before writing this
ticket) and fixed — all mechanical regression-scope gaps from the two Dormant Mechanism Closure
tickets that changed a shared signature and a field's persistence semantics, not architectural
bugs. PR #144 CI should now be green.
