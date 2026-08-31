---
status: historical
layer: systems
authority: P2
audience: agent
ticket_id: TCK-20260824-AFFECTION-CONTRACT-GATE
artifact_type: test_plan
tags: [social, information]
---

# Test Plan — TCK-20260824-AFFECTION-CONTRACT-GATE

## Regression Surface

### Unit — social appraisal / contracts (must keep passing unchanged, since the shared helper is a
generalization of `appraise_contract()`, not a formula change)

- `tests/unit/social/test_appraisal_logic.py` — `test_appraise_recruitment_low_trust_low_pay`,
  `test_appraise_recruitment_haggling`, `test_appraise_recruitment_high_trust`,
  `test_appraise_recruitment_danger_low_hp` — exercise `_appraise_recruitment`'s hard-cancel pattern
  directly; the new helper must not change RECRUITMENT's existing outcomes.
- `tests/unit/social/test_recruitment.py` — `test_recruitment_cost_scaling_with_level`,
  `test_recruitment_cost_discount_with_trust`, `test_recruitment_acceptance_logic`.
- `tests/unit/social/test_social_contracts.py` — `test_social_contract_betrayal_consequences`
  (covers SOC-003/004/006 — `ContractService.resolve_contract_outcome`/`transition_contract`, not
  directly touched by this ticket but shares the `ContractKind`/`ContractStatus` enums being extended).
- `tests/unit/social/test_betrayal_consequence.py::test_betrayal_trauma_blocks_recruitment` — SOC-001/
  SOC-008 P0 parity test; the shared hard-cancel prelude (trust<0.2, betrayal_count>0 and trust<0.4)
  must remain bit-identical for RECRUITMENT.
- `tests/unit/social/test_party_composition.py` — must stay unaffected; confirms Team-Up's new gate
  is not accidentally merged into `PartyCompositionScorer`'s scoring path (Anti-Drift Hazard).

### Unit — social contract goal scorer / materialization

- `tests/unit/ai/goals/test_social_contract_goal_scorer.py` — specifically the parametrized case at
  line 124 (`for kind in (ContractKind.PROTECTION, ContractKind.MERCHANT, ContractKind.POSITION_SWAP):
  ... never spawn a project`) — must keep passing unless a plan.md Design Decision explicitly widens
  `get_project_mapping()`'s coverage to include MERCHANT/new kinds (Anti-Drift Hazard: do not widen
  incidentally).
- `tests/unit/strategic/test_strategic_social_contracts.py`,
  `tests/unit/strategic/test_social_contract_materialization.py` — cover
  `ContractService.accept_contract()`/tier-5 materialization; must not regress from new `ContractKind`
  values being added to the enum.

### Unit / integration — paid information

- `tests/unit/cognition/test_information_seeking.py` — the `TestPaidInformationTransaction` class
  (line ~277+) calling `PaidInformationTransactionSystem.enforce()` directly (lines 352, 362, 383,
  390, 398, 405, 413, 419) — these currently assert unconditional `ResourceTransferIntent` emission;
  once gated, these tests' fixtures (seeker + provider state) must still represent a
  gate-passing scenario, or the plan must explicitly update them as part of the ticket (not a silent
  regression — flag any assertion change in Implementation Notes).
- `tests/integration/scenarios/test_information_seeking_wiring.py` — end-to-end wiring check; must
  keep passing since the gate should not remove the phase from the pipeline, only condition its output.

### Architecture / determinism guards

- Confirm no existing test asserts dict-iteration-order-dependent behavior in
  `PaidInformationTransactionSystem.enforce()`'s provider selection — the existing `sorted(...)` calls
  (lines 92, 112) must remain untouched; any new candidate-selection logic for Team-Up/Trade must use
  the same deterministic-sort pattern, verified by a new test (see below).

## New Tests Required

Per acceptance criteria:

1. **`test_shared_gate_helper_dispatches_by_kind`**
   - Category: unit
   - Verifies: the new shared threshold-gate helper accepts a `ContractKind` and returns
     `(ContractStatus, ReasonCode, Dict[str, Any])`, correctly dispatching to each of the (at least 3
     new + pre-existing) kind-specific bodies — parametrized over RECRUITMENT (existing, must be
     unchanged), and whatever new kind(s) plan.md assigns to Team-Up/Trade/Paid-Information.
   - Location: `tests/unit/social/test_appraisal_logic.py` (extends existing kind-coverage tests) or a
     new `tests/unit/social/test_contract_gate_helper.py` if plan.md extracts the helper to its own
     module — planner to decide final location; either is consistent with existing test layout.

2. **`test_shared_gate_no_fallthrough_for_gated_kinds`**
   - Category: unit / architecture guard
   - Verifies: none of RECRUITMENT (existing), and the new Team-Up/Trade/Paid-Information kinds ever
     reach the generic `return ContractStatus.CANCELLED, ReasonCode.UNKNOWN, {}` fallthrough at the
     bottom of `appraise_contract()`/the new helper — directly encodes AC "No fallthrough to default
     CANCELLED/UNKNOWN for any of the 3 consumers". Should assert on `ReasonCode` value, not just
     `ContractStatus`, since `CANCELLED` is a legitimate kind-specific outcome too (only `UNKNOWN`
     signals fallthrough).
   - Location: `tests/unit/social/test_appraisal_logic.py` or the new gate-helper test module.

3. **`test_trade_merchant_kind_appraisal`** (or equivalent name matching whichever `ContractKind` the
   plan assigns to Trade)
   - Category: unit
   - Verifies: Trade's contract kind (either `ContractKind.MERCHANT` reused, or a new kind, per
     plan.md's Decision) is appraised through the shared helper using the
     `bond.sentiment`-priority-else-`trust_history` formula, with at least one accept, one hard-cancel
     (low trust), and one kind-specific-terms case (whatever Trade's terms schema ends up being).
   - Location: `tests/unit/social/test_appraisal_logic.py` (new `MERCHANT`/Trade-kind test functions,
     alongside the existing `test_appraise_recruitment_*` functions).

4. **`test_team_up_kind_appraisal`**
   - Category: unit
   - Verifies: the new `TEAM_UP` (or equivalent) `ContractKind` is appraised through the shared
     helper with the same trust/hard-cancel prelude, plus whatever Team-Up-specific terms/threshold
     logic plan.md defines; explicitly covers the "no existing wiring" gap this investigation
     confirmed (i.e. this is genuinely new coverage, not a regression guard).
   - Location: `tests/unit/social/test_appraisal_logic.py` (new test functions) — or
     `tests/unit/social/test_team_up.py` if plan.md gives Team-Up its own action-handler module
     (mirroring `test_recruitment.py`'s pattern for `execute_recruit`).

5. **`test_paid_information_gated_on_shared_helper`**
   - Category: unit
   - Verifies: `PaidInformationTransactionSystem.enforce()` now calls the shared helper (or an
     equivalent gate) before emitting `ResourceTransferIntent`; asserts (a) a gate-passing
     seeker/provider bond emits the intent exactly as before, (b) a gate-failing bond (e.g. seeker's
     `bond.sentiment < -0.8` toward the provider, or `trust_score < 0.2`) suppresses the intent
     entirely — directly encodes AC "PaidInformationTransactionSystem.enforce() gates its
     ResourceTransferIntent on the shared helper's outcome". Must cover the "provider not gated at
     all today" gap this investigation found (zero eligibility check currently exists).
   - Location: `tests/unit/cognition/test_information_seeking.py` (extends the existing
     `TestPaidInformationTransaction` class) since that class already owns `enforce()` coverage.

6. **`test_paid_information_enforce_still_decision_only`**
   - Category: architecture guard
   - Verifies: `enforce()` continues to return a `StateUpdate`/intent-only result and does not mutate
     `AuthoritativeState` directly — guards the Durable State Rule / "decision-only phase" contract
     this module's own docstring asserts, now that new gating logic is added to the function.
   - Location: `tests/unit/cognition/test_information_seeking.py` or
     `tests/integration/scenarios/test_information_seeking_wiring.py`.

7. **`test_new_contract_kinds_no_project_mapping_regression`**
   - Category: architecture guard / anti-drift
   - Verifies: unless plan.md explicitly widens `ContractService.get_project_mapping()`, the new
     Team-Up/Trade/Paid-Information `ContractKind` values continue to return `None` from
     `get_project_mapping()` (mirroring the existing PROTECTION/MERCHANT/POSITION_SWAP exclusion) —
     prevents accidental tier-5 materialization scope creep.
   - Location: `tests/unit/ai/goals/test_social_contract_goal_scorer.py` (extends the existing
     parametrized exclusion test at line 124 with the new kinds, if plan.md does not explicitly
     include them in a widened mapping).

8. **`test_affection_field_decision_consistency`** (name depends on plan.md's Decision 1 outcome)
   - Category: unit
   - Verifies: whichever of "reuse `sentiment`" or "new `affection` field" plan.md chooses, all 3 new
     consumers (Team-Up/Trade/Paid-Information) and the shared helper read the *same* field
     consistently with each other and with the pre-existing `appraise_contract()`/
     `PartyCompositionScorer.score_trust_bonds()`/`SocialContractGoalScorer._raw_score()` precedent —
     guards against one consumer reading `sentiment` while another reads a newly-added field by
     mistake.
   - Location: `tests/unit/social/test_appraisal_logic.py`.

## Scoped Pytest Commands

```
pytest tests/unit/social/ tests/unit/ai/goals/test_social_contract_goal_scorer.py tests/unit/strategic/test_strategic_social_contracts.py tests/unit/strategic/test_social_contract_materialization.py tests/unit/cognition/test_information_seeking.py tests/integration/scenarios/test_information_seeking_wiring.py -v
```

Never `pytest tests/`. If plan.md relocates the shared helper out of `appraisal.py` into a new
module, add that module's test path explicitly to the command above rather than widening the scope
further (e.g. do not fold in unrelated `tests/unit/strategic/` files beyond the two named here).

## Anti-Drift Test Guards

- **RECRUITMENT/LOAN/POSITION_SWAP outcome stability**: every existing `test_appraise_recruitment_*`
  and `test_recruitment_*` test must produce byte-identical `(ContractStatus, ReasonCode, terms)`
  results after the helper generalization — any diff here is a parity regression against SOC-001/
  SOC-008/SOC-134, not an accepted side effect of adding new kinds.
- **`get_project_mapping()` 2-of-5 (soon-to-be N-of-M) coverage stays intentional, not accidental**:
  `test_social_contract_goal_scorer.py:124`'s exclusion parametrization must be updated deliberately
  (adding new kinds to the excluded tuple, or explicitly moving them to an included path with a
  plan.md-documented reason) — never left silently stale where the new kinds are untested either way.
- **`PaidInformationTransactionSystem.enforce()` remains decision-only**: no test should observe a
  direct `AuthoritativeState` mutation from `enforce()`; all state changes must continue to flow
  through the returned `StateUpdate`'s `resource_transfers`/`strategic_upd` — verified by the same
  pattern `test_information_seeking.py`'s existing tests already use (call `enforce()`, inspect the
  returned `StateUpdate`, never inspect `state` for a mutation).
- **`ContractKind.MERCHANT` vs. `InformationProviderArchetype.MERCHANT` non-conflation**: a guard
  test should confirm Trade's contract-kind logic and Paid-Information's provider-archetype logic key
  off genuinely distinct enum values in code (not just distinct by class), preventing a future
  accidental `==` comparison across the two unrelated `MERCHANT` members.
- **Determinism**: any new provider/candidate selection added for Team-Up or Trade must be covered by
  a test that runs the same scenario twice with the same seed/entity-id ordering and asserts identical
  output — mirroring the existing `sorted(...)`-based determinism the paid-information phase already
  relies on.
- **`PartyCompositionScorer`/`FORM_PARTY` untouched**: `test_party_composition.py`'s full suite must
  pass unmodified — a regression here would indicate Team-Up's new gate mechanism was incorrectly
  merged into the existing trust-bonds scoring term instead of being built as a separate contract gate.
