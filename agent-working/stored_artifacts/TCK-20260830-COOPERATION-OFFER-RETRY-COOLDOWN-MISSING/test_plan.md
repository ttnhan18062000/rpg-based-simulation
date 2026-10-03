---
status: historical
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260830-COOPERATION-OFFER-RETRY-COOLDOWN-MISSING
artifact_type: test_plan
tags: [social, simulation-quality]
---

# Test Plan — TCK-20260830-COOPERATION-OFFER-RETRY-COOLDOWN-MISSING

## Regression Surface

**Unit — cooperation domain** (must all keep passing; the recommended fix touches
`CooperationDecisionService.select()` only inside the existing "Good partner exists" branch, and
`SocialContractSystem.reap_expired_offers()` only for `ContractKind.RECRUITMENT`):
- `tests/unit/domains/cooperation/test_phase7_cooperation_decision_service.py` — exercises
  `CooperationDecisionService.select()` directly; every existing test constructs entities with
  `entity.identity.cooldowns` empty (default `{}`), so `state.tick < cooldowns.get(...)` must
  evaluate `False` for all of them and produce byte-identical postures to today.
- `tests/unit/domains/cooperation/test_phase7_cooperation_intent_bridge.py` — exercises
  `CooperationIntentBridge.map_decision()` directly with hand-built `CooperationDecisionResult`s;
  unaffected by this fix (no changes to `map_decision()` in the recommended design).
- `tests/unit/domains/cooperation/test_cooperation_phase.py` — end-to-end `CooperationPhase.execute()`
  flag-on/flag-off/inactive-entity tests. Must still produce `last_cooperation_decision` for
  eligible entities not on cooldown.
- `tests/unit/domains/cooperation/test_phase7_partner_candidate_provider.py`
- `tests/unit/domains/cooperation/test_phase7_partner_fit_evaluator.py`
- `tests/unit/domains/cooperation/test_phase7_help_need_evaluator.py`
- `tests/unit/domains/cooperation/test_phase7_party_objective_alignment.py`
- `tests/unit/domains/cooperation/test_phase7_party_cohesion_service.py`
- `tests/unit/domains/cooperation/test_phase7_cooperation_learning.py`
- `tests/unit/domains/cooperation/test_phase7_cooperation_postures.py`
- `tests/unit/domains/cooperation/test_phase7_cooperation_boundary.py`
- `tests/unit/domains/cooperation/test_phase7_cooperation_events.py`
- `tests/unit/domains/cooperation/test_role_1_magic_number_disclosure.py`

**Integration — cooperation domain**:
- `tests/integration/domains/cooperation/test_phase7_cooperation_phase.py`
- `tests/integration/scenarios/test_phase7_social_cooperation_scenarios.py`

**Perf budget** (must not regress — the fix adds one dict lookup to `select()` and one conditional
`IdentityUpdate` merge to `reap_expired_offers()`, both O(1)/entity):
- `tests/perf/test_phase7_social_cooperation_budget.py`

**Unit — social contracts** (regression surface for `SocialContractSystem.reap_expired_offers()`
and `ContractService.create_recruitment_contract()`, both touched by the fix):
- `tests/unit/social/test_social_contracts.py`
- `tests/unit/social/test_contract_lifecycle.py`
- `tests/unit/social/test_contract_lifecycle_phase7.py`
- `tests/unit/social/test_contracts.py`
- `tests/unit/social/test_social_phase7.py`
- `tests/unit/social/test_source_trust.py`
- `tests/unit/social/test_reputation_learning.py`
- `tests/unit/strategic/test_strategic_social_contracts.py`

**Observability — contract_expired_offer emission** (must be byte-identical; this fix does not
change contract-expiry state-diff semantics, only offer-creation frequency):
- `tests/unit/observability/test_event_extractor_social_faction.py` (specifically
  `test_contract_expired_offer_on_offered_to_expired`, `test_contract_lapsed_not_on_offered_to_expired`)
- `tests/unit/observability/test_event_shapers_social.py` (specifically
  `test_contract_expired_offer_not_double_fired_when_both_signals_present`)

**Skill-cooldown regression surface** (must keep passing — this fix reuses the same
`identity.cooldowns: Dict[str, int]` field for a different key; must confirm no key collision or
behavioral leakage into skill-cooldown legality checks):
- `tests/unit/progression/test_rpg_advancement.py`
- `tests/integration/pipeline/test_combat_legality_matrix.py`
- `tests/unit/observability/test_event_extractor_identity.py`

**Simulation-quality grade regression** (the acceptance-criteria-named test):
- `tests/simulation_quality/test_grade_regression.py::test_grade_within_anchor_band[highland_traverse_seed42_200t]`

## New Tests Required

1. **Test name**: `test_cooperation_offer_retry_blocked_within_cooldown_window`
   **Category**: unit
   **What it verifies**: `CooperationDecisionService.select()` does not return
   `REQUEST_HELP`/`HIRE_SUPPORT` for an entity whose `identity.cooldowns["cooperation_offer_retry"]`
   is set to a tick greater than `state.tick`, even when a high-fit, high-trust candidate exists
   that would otherwise be selected (construct the exact same fixture as
   `test_risky_objective_selects_request_help_when_good_partner_exists()` in
   `tests/unit/domains/cooperation/test_phase7_cooperation_decision_service.py`, but set
   `entity.identity.cooldowns = {"cooperation_offer_retry": state.tick + 5}` and assert the
   resulting posture is `SOLO` or `DEFER_NO_PARTNER`, matching the existing "no suitable partner"
   fallback branches, never `REQUEST_HELP`/`HIRE_SUPPORT`).
   **Where it lives**: `tests/unit/domains/cooperation/test_phase7_cooperation_decision_service.py`

2. **Test name**: `test_cooperation_offer_retry_allowed_after_cooldown_expires`
   **Category**: unit
   **What it verifies**: same fixture as test 1, but `entity.identity.cooldowns["cooperation_offer_retry"]
   <= state.tick` (cooldown already elapsed) — the entity CAN select `REQUEST_HELP`/`HIRE_SUPPORT`
   again, confirming the gate is not a permanent block and correctly reads the tick comparison
   direction (`state.tick < ready_tick`, not `<=` or inverted).
   **Where it lives**: `tests/unit/domains/cooperation/test_phase7_cooperation_decision_service.py`

3. **Test name**: `test_reap_expired_recruitment_offer_sets_retry_cooldown`
   **Category**: unit
   **What it verifies**: `SocialContractSystem.reap_expired_offers()` (or
   `ContractService.reap_expired_offers()` — confirm exact call site used in production, both
   names appear in the codebase for related functions per `contracts.py:304` and
   `pipeline.py:368`), given an entity with an `OFFERED` `ContractKind.RECRUITMENT` contract whose
   `expiry_tick <= current_tick`, produces an `EntityUpdate.identity.cooldown_updates` containing
   `"cooperation_offer_retry": current_tick + COOPERATION_OFFER_COOLDOWN_TICKS` (or the actual
   constant name/value chosen at implementation time) for that entity, **in addition to** the
   existing `strategic.contracts_remove` entry (do not regress the existing removal behavior).
   **Where it lives**: `tests/unit/social/test_contract_lifecycle.py` or
   `tests/unit/social/test_contract_lifecycle_phase7.py` (match whichever file already covers
   `reap_expired_offers()`'s current behavior — confirm at implementation time).

4. **Test name**: `test_reap_expired_loan_offer_does_not_set_cooperation_cooldown`
   **Category**: unit — anti-drift guard
   **What it verifies**: reaping an expired `OFFERED` `ContractKind.LOAN` (or any non-`RECRUITMENT`
   kind) contract does **not** write a `"cooperation_offer_retry"` cooldown entry — confirms the
   fix is correctly scoped to `RECRUITMENT` only and does not leak into unrelated contract-kind
   retry cadence (per ticket's Out of Scope).
   **Where it lives**: same file as test 3.

5. **Test name**: `test_cooperation_phase_no_immediate_reoffer_after_expiry_tick`
   **Category**: integration
   **What it verifies**: the acceptance criterion's literal wording — "an entity does not
   re-propose a cooperation offer on the tick immediately following a prior expiry." Drive two
   consecutive ticks through the real pipeline path (`CooperationPhase.execute()` +
   `ContractService.reap_expired_offers()`, or the full `AuthoritativeApplyPipeline` if that is
   the established integration-test pattern in
   `tests/integration/domains/cooperation/test_phase7_cooperation_phase.py`): tick T has an
   entity's `RECRUITMENT` offer expire and get reaped; tick T+1 re-runs `CooperationDecisionService.select()`
   (via `CooperationPhase.execute()`) for the same entity with the same eligible partner still
   available, and asserts no new `RECRUITMENT` contract appears in that entity's
   `strategic.contracts_add_or_update` for tick T+1.
   **Where it lives**: `tests/integration/domains/cooperation/test_phase7_cooperation_phase.py`

6. **Test name**: `test_grade_within_anchor_band[highland_traverse_seed42_200t]` (existing
   parametrized test, re-verified not newly written)
   **Category**: simulation-quality / grade regression
   **What it verifies**: post-fix, a real `python3 tools/evaluate_simq.py` corpus re-run against
   `highland_traverse_seed42_200t` produces a SOCIAL score that passes both the ±1-letter-grade
   band check and the score-tolerance check against the **updated** `grade_anchors.json` entry.
   This is not a new test file — it is the existing parametrized case in
   `tests/simulation_quality/test_grade_regression.py`, which will only pass once (a) the fix
   measurably reduces `offer_dead`-weighted `contract_expired_offer` density for this run_key, and
   (b) the anchor is updated to the fresh, real post-fix score (never guessed).
   **Where it lives**: `tests/simulation_quality/test_grade_regression.py` (parametrized,
   `FAST_ANCHOR_KEYS`); `tests/simulation_quality/fixtures/grade_anchors.json` (data update, this
   run_key's `SOCIAL` block only).

## Scoped Pytest Commands

```
# Cooperation domain (unit + integration), the primary change surface
pytest tests/unit/domains/cooperation/ tests/integration/domains/cooperation/ tests/integration/scenarios/test_phase7_social_cooperation_scenarios.py -v

# Social contracts (reap_expired_offers / create_recruitment_contract change surface)
pytest tests/unit/social/ tests/unit/strategic/test_strategic_social_contracts.py -v

# Skill-cooldown regression surface (shared identity.cooldowns field)
pytest tests/unit/progression/test_rpg_advancement.py tests/integration/pipeline/test_combat_legality_matrix.py tests/unit/observability/test_event_extractor_identity.py -v

# Observability parity for contract_expired_offer (must be unchanged)
pytest tests/unit/observability/test_event_extractor_social_faction.py tests/unit/observability/test_event_shapers_social.py -v

# Perf budget (must not regress)
pytest tests/perf/test_phase7_social_cooperation_budget.py -v

# Grade regression, scoped to this one run_key only (not the full fast-tier corpus)
pytest "tests/simulation_quality/test_grade_regression.py::test_grade_within_anchor_band[highland_traverse_seed42_200t]" -v -m "not slow"
```

Never: `pytest tests/`. Never: `pytest tests/simulation_quality/` unscoped (that would re-run all
61 `FAST_ANCHOR_KEYS`, most of which are already-known-failing/out-of-scope per the filing
ticket's own investigation — see this ticket's Prior Work section).

## Anti-Drift Test Guards

- **Test 4 above (`test_reap_expired_loan_offer_does_not_set_cooperation_cooldown`) is the primary
  scope-creep guard**: it fails loudly if the implementer widens the cooldown-set logic to all
  `ContractKind`s instead of scoping to `RECRUITMENT`, which would silently change `LOAN` offer
  retry cadence — explicitly out of scope.
- **Skill-cooldown regression surface (`test_rpg_advancement.py`,
  `test_combat_legality_matrix.py`) guards against key-collision or leakage**: since the fix reuses
  `identity.cooldowns` for a new synthetic key, any accidental change to how
  `IdentityUpdate.cooldown_updates` merges (e.g., accidentally clearing other keys instead of
  merging) would be caught by these tests, which construct entities with real skill cooldowns set.
- **`test_event_extractor_social_faction.py`/`test_event_shapers_social.py`'s existing
  `contract_expired_offer` tests guard against accidentally changing contract-expiry event
  semantics** — this fix must only change offer-creation *frequency*, never the state-diff logic
  that derives `contract_expired_offer`/`contract_lapsed`/`contract_completed`.
- **Test 1 vs. Test 2 pairing guards against an off-by-one/inverted comparison** (`<` vs. `<=`, or
  checking the wrong operand order) in the cooldown-active check — a common class of bug for this
  shape of fix, and exactly the kind of thing `tests/unit/domains/time/test_phase13_temporal_pressure_service.py::test_active_cooldown_prevents_immediate_retry`
  already guards for the (unused) `TemporalModel.cooldowns` mechanism; this pairing gives the same
  guarantee for the mechanism actually being wired up here.
- **`test_phase7_social_cooperation_budget.py` guards against perf regression** from the added
  per-entity dict lookup — should be a no-op at this scale, but any accidental O(n) scan (e.g.,
  iterating all `identity.cooldowns` entries instead of a direct key lookup) would be visible here.
- **Do not treat a passing `test_grade_within_anchor_band[highland_traverse_seed42_200t]` from a
  hand-edited anchor as sufficient** — the anchor value must come from an actual fresh
  `tools/evaluate_simq.py` run's `data/calibration/*/quality_report.json` output, per this ticket's
  investigation.md Risks section and the filing ticket's own Anti-Drift Hazards about
  `quality_scores.jsonl` being unsafe/append-only. A hand-computed or guessed anchor value that
  happens to make the test pass would defeat the purpose of the acceptance criterion.
