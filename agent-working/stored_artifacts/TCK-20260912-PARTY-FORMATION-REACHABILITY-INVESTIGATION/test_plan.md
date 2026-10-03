# Test Plan — TCK-20260912-PARTY-FORMATION-REACHABILITY-INVESTIGATION

## New unit tests (`tests/unit/domains/cooperation/test_phase7_cooperation_decision_service.py`)
- `test_find_pending_incoming_offer_finds_real_offer_targeting_entity` — a real OFFERED
  RECRUITMENT contract on the offerer's own record, targeting the entity under test, is found.
- `test_find_pending_incoming_offer_none_when_target_already_grouped` — disqualifier: entity
  already in a group.
- `test_find_pending_incoming_offer_none_when_offer_expired` — expired offers are not returned.
- `test_find_pending_incoming_offer_none_when_offerer_dead` — disqualifier: offering entity dead.
- `test_select_returns_join_party_when_pending_offer_exists_even_with_no_help_needs` — proves
  JOIN_PARTY takes priority over the entity's own help-needs evaluation, and that an entity with
  zero help needs still gets a real decision rather than being skipped.

## New integration test (`tests/integration/domains/cooperation/test_phase7_cooperation_phase.py`)
- `test_join_party_promotes_offerers_contract_to_active_with_extended_expiry` — real
  `CooperationPhase.execute()` call with a real pending OFFERED contract; asserts the offerer's
  contract is promoted to ACTIVE with `expiry_tick == tick + duration`, not the original
  OFFER-stage expiry. This is the direct regression guard for the real bug found and fixed within
  this same implementation (see investigation.md/plan.md).

## Real 500-tick instrumented reproduction (primary evidence, not a substitute for the tests above)
Same scenario/seed/tick-count throughout this entire investigation arc for a controlled comparison:
`frontier_living_world`, seed 7, 500 ticks.

| | Entities | `state.groups` @ tick 500 | Non-empty `trust_history` |
|---|---|---|---|
| Before count expansion | 16 | 0 | 0 / 16 |
| After count expansion, before this fix | 49 | 0 | 0 / 49 |
| After this fix (first pass, expiry bug present) | 49 | 0 (formed then dissolved) | 0 / 49 |
| After this fix (expiry bug fixed) | 49 | 1 (12 distinct ever formed, up to 16 concurrent) | 3 / 49 |

Additional real counters from the final instrumented run: `PartyCohesionService.evaluate()` status
distribution 859 STABLE / 5 MEMBER_ABANDONING / 1 LEADER_LOST / 4 NEEDS_REGROUP (the full lifecycle,
not just one status); `CooperationLearningService.learn()` fired 6 times;
`SocialPatch.apply()` carried a non-empty `trust_delta` 7 times.

## Regression suites
- `pytest tests/unit/domains/cooperation/ tests/integration/domains/cooperation/ tests/unit/social/
  tests/unit/domains/optimization/test_strategic_work_queue.py tests/unit/world/ -q` — 671 passed.
- `pytest tests/unit/social/ tests/unit/strategic/test_strategic_social_contracts.py
  tests/unit/ai/goals/test_social_contract_goal_scorer.py
  tests/integration/campaigns/test_loyalty_pressure_campaign_bridge.py
  tests/architecture/test_adventure_route_score_max_unchanged.py -q` — 304 passed (broader sweep
  for anything touching `accept_contract`/`GroupSystem`/`SocialContractGoalScorer`).
- `pytest tests/refactor/test_import_compatibility.py tests/refactor/test_public_facades.py -q` —
  6 passed.

## Acceptance criteria mapping
- Real instrumentation determines reachability (not code-reading alone) → the before/after table
  above, both the density re-measurement and the fix verification.
- Real root cause confirmed → investigation.md's evidence chain (accept_contract 0 callers,
  execute_recruit's RECRUIT intent 0 construction sites, JOIN_PARTY's own declared intent_mapping).
- Blast radius enumerated → investigation.md.
- Fix-approach decided via peer review before implementation → reported and approved before any
  code was written; the expiry-tick bug found mid-implementation was fixed and disclosed, not
  silently patched around.
- Trust-accumulation acceptance bar (transferred from the trust ticket) → satisfied: 3/49 entities
  with non-empty `trust_history` in the final real run.
