---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260712-SIMQ-INFORMATION-ROUTING-CLOSURE
phase: open
date: 2026-07-12
tags: [cognition, information, self-model, observability, simulation-quality]
---

# TCK-20260712-SIMQ-INFORMATION-ROUTING-CLOSURE

## Title
Fix Branch B query-routing's real-world dead-end: candidate ranking, no-fallback, silent
affordability gate, and missing event-extractor mapping

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
`TCK-20260710-SIMQ-COGNITION-REALWORLD-GENERALIZE` found that `InformationBeliefPhase`'s Branch B
query-routing logic (`src/domains/information/phase.py:83-105`) is mechanically reachable but dead-
ends against `urban_political`'s real compiled state, reproducibly and seed-invariantly (seeds
42/123/456). This ticket fixes the 4 root-caused points so a real entity's information query can
actually resolve, execute, and score under the SimQ pipeline -- closing the gap between
"reachable" (the existing hand-built `test_fused_loop.py` test) and "succeeds against a real
world's actual candidate ranking and actual entity economy" (what this ticket verifies).

## Scope
1. `InformationQueryRouter.route()` (`src/domains/information/router.py:102-103`) currently sorts
   candidates by `(-expected_certainty, cost_gold)` with no regard for affordability -- a paid,
   higher-certainty candidate always outranks a free, lower-certainty one even when the entity
   cannot afford the paid one. Fix point (decide during implementation, per investigation.md's own
   note that this is a 3-way tradeoff, not obviously "the ranking is the bug"): either change the
   ranking to prefer affordable candidates, or leave ranking as-is and rely on fix 2's fallback.
2. `InformationBeliefPhase.apply()` (`src/domains/information/phase.py:92-105`) only ever tries
   `candidates[0]` -- add a fallback to try `candidates[1]`, `candidates[2]`, etc. when resolution
   of the top candidate fails, before giving up for the tick.
3. `InformationIntentResolver.resolve()` (`src/domains/information/resolver.py:65-69`) silently
   returns `None` when `actor_gold < candidate.cost_gold` -- return a structured
   "insufficient_gold"-shaped signal instead, consumable by the fallback in fix 2 and by
   `KnowledgeModelService.assimilate()`'s existing `"insufficient_gold"` `answer_kind` branch
   (`src/cognition/knowledge_model.py:67-70`), which currently has no producer anywhere in `src/`.
4. `src/observability/event_extractor.py:276-299` has no extractor branch for
   `last_routed_query_subject`/`last_routed_query_tick` (Branch B's own property-update keys, set
   at `phase.py:101-104`) -- add one (a `route_new_query`-style event or equivalent) so a
   successful routing action becomes visible and scoreable under the SimQ pipeline at all.
5. Close the `ASK_INFORMATION` intent execution loop (`src/engine/intent/action_intent.py:127-141`)
   -- it currently only deducts gold and appends an internal `IntentTrace`, never producing an
   `InformationResponse`/`pending_information_responses`-equivalent entry that a later tick's
   `InformationBeliefPhase` Branch A could re-assimilate. Without this, even a "successful" routing
   action never resolves the entity's unknown into a known fact.
6. Add the 5 tests scoped in `stored_artifacts/TCK-20260710-SIMQ-COGNITION-REALWORLD-GENERALIZE/test_plan.md`'s
   "New Tests Required" section (verbatim -- do not re-derive):
   `test_branch_b_query_routing_fails_silently_on_real_urban_political_state`,
   `test_information_belief_phase_falls_back_to_next_candidate_on_resolution_failure`,
   `test_intent_resolver_insufficient_gold_produces_signal_not_silent_none`,
   `test_event_extractor_emits_route_new_query_event`,
   `test_ask_information_intent_execution_closes_the_loop`.
7. The parent investigation ticket's probe-file question is now resolved (formalized as a permanent
   fixture, per Decision 3 above) — add `test_urban_political_selfmodel_cognition_isolated_grade_anchor`
   (test_plan.md item 6) unconditionally.
8. Update `docs/parity_ledger/infrastructure.yaml::INFRA-266` (added by
   `TCK-20260710-SIMQ-COGNITION-REALWORLD-GENERALIZE`) to `status: verified` with the fix's
   `test_path` once these tests pass, replacing its current routing-failure framing with a
   routing-fixed framing (or add a new INFRA-26x entry if the split-verdict framing should be
   preserved historically rather than overwritten -- implementer's call, consistent with how
   INFRA-259/260 were kept as separate, narrowly-scoped entries rather than merged).

## Out of Scope
- Changing `ENABLE_SELF_MODEL_COGNITION`/`ENABLE_BELIEF_ASSIMILATION` defaults in any shipped
  profile -- this ticket fixes the mechanism, it does not activate it anywhere new.
- Widening the fix into "the full belief-assimilation response cycle" beyond the 5 numbered points
  above -- mirrors the existing anti-drift note in
  `docs/plans/idea_information_belief_trigger_wiring.md` and
  `stored_artifacts/TCK-20260710-SIMQ-COGNITION-REALWORLD-GENERALIZE/test_plan.md`'s own
  "partial-fix trap" warning: a single-point fix (e.g. only re-sorting the router) would likely
  still leave routing unscoreable even if resolution succeeds -- all 4 root-cause points (5
  including the intent-closure gap) must land together.
- Any change to `SelfAssessmentService`, `NeedInterpretationService`, or `CapabilityEstimateService`.
- Turning `ENABLE_ADVENTURE_ROUTING`/AGENCY on in combination with self-model flags in the same
  test -- `TCK-20260703-SIMQ-UPLIFT3-BRANCH-B`'s Finding 5 blast-radius sweep already flagged this
  three-way combination as out of scope for Branch B work.

## Acceptance Criteria
- [ ] `InformationQueryRouter`/`InformationBeliefPhase`/`InformationIntentResolver` resolve a real
      `ASK_INFORMATION` query end-to-end against `urban_political`'s real compiled state (entity 23,
      0 gold) for at least one of the two available candidates, across all 3 anchor seeds
- [ ] `event_extractor.py` emits a scoreable event for a successful routing action
- [ ] A successfully executed `ASK_INFORMATION` intent eventually produces an answer that a later
      tick's Branch A can re-assimilate
- [ ] All 6 new tests pass (5 from Scope items 1-6 plus the grade-anchor test from Scope item 7,
      now unconditional per the parent investigation ticket's Decision 3);
      `test_branch_b_fires_across_real_tick_boundary_after_self_model_patch_materialization`
      still passes unmodified
- [ ] `INFRA-266` (or a new successor entry) updated to reflect the fixed state with a passing
      `test_path`
- [ ] `make evaluate --dry-run` shows 0 new regressions attributable to this ticket

## Related Tickets
- `TCK-20260710-SIMQ-COGNITION-REALWORLD-GENERALIZE` (parent investigation -- source of all 4
  root-cause file:line citations this ticket implements against)
- `TCK-20260703-SIMQ-UPLIFT3-BRANCH-B` (done -- the original 3-bug materialization fix chain)
- `TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-SELFMODEL-PILOT` (done -- established the isolated-
  materialization pilot this ticket's fix extends beyond)

## Related Docs
- `docs/parity_ledger/infrastructure.yaml` (`INFRA-259`, `INFRA-260`, `INFRA-266`)
- `stored_artifacts/TCK-20260710-SIMQ-COGNITION-REALWORLD-GENERALIZE/investigation.md` (full root-
  cause evidence chain, file:line citations, seed-invariance confirmation)
- `stored_artifacts/TCK-20260710-SIMQ-COGNITION-REALWORLD-GENERALIZE/test_plan.md` ("New Tests
  Required" section -- the 6 tests this ticket must add, already scoped)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260710-SIMQ-COGNITION-REALWORLD-GENERALIZE/`

## Related Code Areas
- `src/domains/information/router.py:102-103`
- `src/domains/information/phase.py:83-105`
- `src/domains/information/resolver.py:65-69`
- `src/cognition/knowledge_model.py:67-70`
- `src/observability/event_extractor.py:276-299`
- `src/engine/intent/action_intent.py:127-141`

## Assumptions / Open Questions
- Whether to fix the router's ranking heuristic itself or rely solely on the phase-level fallback
  (Scope item 1) is left to the implementer, per investigation.md's own note that the ranking
  heuristic is plausibly intentional design (favor accuracy over price) and only becomes a hard
  failure combined with zero starting gold and no fallback -- decide based on which combination of
  fixes 1-3 produces the cleanest, most minimal diff satisfying the Acceptance Criteria.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
