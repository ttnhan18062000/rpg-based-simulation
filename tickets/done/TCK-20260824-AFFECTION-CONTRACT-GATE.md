---
status: historical
layer: systems
authority: P1
audience: agent
ticket_id: TCK-20260824-AFFECTION-CONTRACT-GATE
phase: done
date: 2026-08-24
tags: [social, information]
---

# TCK-20260824-AFFECTION-CONTRACT-GATE

## Title
Build a Shared Affection-Threshold Gate for Team-Up/Trade/Paid-Information

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
The author wants Team-Up, Trade, and Paid-Information actions gated on affection, built as a shared appraise_contract() threshold-gate helper -- a 6-idea, 3-milestone cluster all converging on the identical formula.

## Scope
- Build a shared threshold-gate helper accepting a ContractKind and returning (ContractStatus, ReasonCode, terms), reusing the existing bond.sentiment-priority-else-trust_history formula already implemented in SocialAppraisalSystem.appraise_contract()
- Route Team-Up, Trade, and Paid-Information each through the shared helper, mirroring _appraise_recruitment's existing hard-cancel pattern
- Decide whether Trade reuses the existing declared-but-unhandled ContractKind.MERCHANT value or needs a new kind; add whatever new ContractKind values Team-Up/Paid-Information need -- no fallthrough to default CANCELLED/UNKNOWN
- Gate PaidInformationTransactionSystem.enforce()'s ResourceTransferIntent on the shared helper's outcome (currently emits unconditionally, zero check today)
- Decide whether to reuse sentiment as-is for the 'affection' concept, or introduce a new named field -- no 'affection' field exists anywhere in src/ today
- Update docs/parity_ledger/social_narrative.yaml's existing verified appraise_contract() entries to reflect the change

## Out of Scope
- M6 ideas 39/40 (Conversation-adjacent consumers) -- this ticket must document whether it builds narrowly for the 3 named consumers or anticipates M6, but does not implement M6's consumers
- Idea 25's separate trust ledger (PP-04-adjacent), explicitly excluded from this cluster per the atlas

## Acceptance Criteria
- [x] The shared threshold-gate helper accepts a ContractKind and returns (ContractStatus, ReasonCode, terms) using the existing bond.sentiment-priority-else-trust_history formula
- [x] Team-Up/Trade/Paid-Information each route through the shared helper, mirroring _appraise_recruitment's existing hard-cancel pattern
- [x] No fallthrough to default CANCELLED/UNKNOWN for any of the 3 consumers
- [x] PaidInformationTransactionSystem.enforce() gates its ResourceTransferIntent on the shared helper's outcome

## Related Tickets
- TCK-20260811-RELATIONSHIP-AWARE-FORM-PARTY
- TCK-20260811-SOCIAL-CONTRACT-GOAL-SCORER

## Related Docs
- docs/mechanics/04_strategic_cognition.md
- docs/parity_ledger/social_narrative.yaml
- docs/plans/rpg_design_roadmap/rpg_m1_quick_wins_epic.md
- docs/brainstorm/rpg_feature_atlas.html

## Related Stored Artifacts
None.

## Related Code Areas
- src/systems/social_systems/appraisal.py
- src/engine/domain/core_actions.py
- src/core/strategic.py
- src/core/models/social.py
- src/engine/pipeline_phases/paid_information.py
- src/systems/social_systems/party_composition.py
- src/ai/goals/social_contract_scorer.py

## Assumptions / Open Questions
- Whether to reuse sentiment as-is (cheapest) or introduce a new named 'affection' field (more state, no current consumer justifies it alone) needs an explicit decision
- Whether to build narrowly for the 3 named consumers now or anticipate M6's ideas 39/40 is an unresolved question in the M1 epic's own Open Questions section
- Team-Up has no existing action/contract wiring anywhere (no TEAM_UP kind, no handler) -- this is new mechanism work, unlike Paid-Information which retrofits a live pipeline phase
- `layer: systems` chosen because the primary deliverable (shared appraise_contract() helper) lives in src/systems/social_systems/; no dedicated "social" layer is registered in registries/layer_registry.jsonl

## Implementation Notes

Implemented plan.md Steps 1-6 exactly (Step 7 parity ledger and Step 8 docs are deliberately
deferred to this pipeline's own later Parity and Document-Update phases -- see plan.md
"Deviations" section):

- **Step 1** (`src/core/strategic.py`): added `ContractKind.TEAM_UP` and
  `ContractKind.PAID_INFORMATION`. Extended
  `tests/unit/ai/goals/test_social_contract_goal_scorer.py::test_social_contract_protection_merchant_position_swap_never_spawn_a_project`
  to also parametrize over the two new kinds, locking in that `get_project_mapping()` still
  returns `None` for them (no accidental tier-5 widening).
- **Step 2** (`src/core/enums.py`): added `ReasonCode.TEAM_UP_ACCEPTED`,
  `ReasonCode.TEAM_UP_DECLINED`, `ReasonCode.INFORMATION_SALE_ACCEPTED` to the existing social
  block, immediately before `UNKNOWN`.
- **Step 3** (`src/systems/social_systems/appraisal.py`): generalized
  `appraise_contract()`'s kind-dispatch with three new `elif` branches (`MERCHANT`, `TEAM_UP`,
  `PAID_INFORMATION`), added `_appraise_trade`, `_appraise_team_up`, `_appraise_paid_information`
  static methods mirroring `_appraise_recruitment`'s hard-cancel-then-score shape. The trust-score
  prelude (lines 19-54) was not touched.
- **Step 4/5** (`src/engine/domain/core_actions.py`, `src/engine/domain/action_router.py`): added
  `CoreActions.execute_team_up()` and `CoreActions.execute_trade()`, both structurally mirroring
  `execute_recruit()` (temp_contract -> `appraise_contract()` -> branch on status). Per Design
  Decision 5, neither emits a `ResourceTransferIntent` on `ACCEPTED` -- the `ContractState` is
  attached directly via `EntityUpdate.strategic=StrategicUpdate(contracts_add_or_update=[contract])`
  for both parties. Registered `"TEAM_UP"` and `"TRADE"` in `ActionRouter.execute_action()`
  alongside the existing `"RECRUIT"` branch.
- **Step 6** (`src/engine/pipeline_phases/paid_information.py`): gated `enforce()` by
  synthesizing a transient `ContractState(kind=ContractKind.PAID_INFORMATION, source_id=provider_id,
  target_id=entity.id, ...)` immediately after provider resolution and calling
  `SocialAppraisalSystem.appraise_contract(entity, temp_contract, state)`; `continue` (no intent
  emission, no state mutation) on any non-`ACCEPTED` status. This closes the ticket's AC #4 "zero
  check today" gap. Determinism-critical `sorted(...)` provider-selection calls were left untouched.

No deviations from plan.md's Steps 1-6 mechanics. The rejection branches of `execute_team_up`/
`execute_trade` use `"reason": status.value` (dynamic) rather than `execute_recruit()`'s hardcoded
`"REJECTED"` string, per plan.md Step 4's explicit instruction for the new handlers.

## Test Summary

Added/extended tests, all passing (`.venv/bin/python3 -m pytest`):
- `tests/unit/social/test_appraisal_logic.py`: added
  `test_shared_gate_no_fallthrough_for_gated_kinds`, `test_shared_gate_dispatches_by_kind`,
  `test_trade_merchant_kind_appraisal`, `test_team_up_kind_appraisal`,
  `test_paid_information_kind_appraisal_accepts_once_prelude_passes`,
  `test_contract_kind_merchant_does_not_conflate_with_information_provider_archetype`.
- `tests/unit/ai/goals/test_social_contract_goal_scorer.py`: extended the existing
  `test_social_contract_protection_merchant_position_swap_never_spawn_a_project` parametrization
  with `TEAM_UP`/`PAID_INFORMATION`.
- `tests/unit/social/test_team_up.py` (new): `test_execute_team_up_accepts_on_high_trust_bond`,
  `test_execute_team_up_rejects_on_low_trust_bond`, `test_execute_team_up_target_not_found`.
- `tests/unit/social/test_trade.py` (new): `test_execute_trade_accepts_on_fair_price`,
  `test_execute_trade_rejects_on_low_trust_bond`, `test_execute_trade_target_not_found`,
  `test_contract_kind_merchant_is_not_information_provider_archetype_merchant`.
- `tests/unit/cognition/test_information_seeking.py`: added
  `test_paid_information_gated_on_shared_helper`,
  `test_paid_information_enforce_still_decision_only` inside `TestPaidInformationTransaction`.

Scoped run:
`pytest tests/unit/social/ tests/unit/ai/goals/test_social_contract_goal_scorer.py tests/unit/strategic/test_strategic_social_contracts.py tests/unit/strategic/test_social_contract_materialization.py tests/unit/cognition/test_information_seeking.py tests/integration/scenarios/test_information_seeking_wiring.py`
-- 308 passed, 0 failed. Full existing `test_appraise_recruitment_*`/`test_recruitment_*`/
`test_betrayal_consequence`/`test_party_composition` suites confirmed unchanged (byte-identical
RECRUITMENT/LOAN/POSITION_SWAP outcomes; no regression).

## Files Changed

- `src/core/strategic.py`
- `src/core/enums.py`
- `src/systems/social_systems/appraisal.py`
- `src/engine/domain/core_actions.py`
- `src/engine/domain/action_router.py`
- `src/engine/pipeline_phases/paid_information.py`
- `tests/unit/ai/goals/test_social_contract_goal_scorer.py`
- `tests/unit/social/test_appraisal_logic.py`
- `tests/unit/social/test_team_up.py` (new)
- `tests/unit/social/test_trade.py` (new)
- `tests/unit/cognition/test_information_seeking.py`
- `docs/parity_ledger/social_narrative.yaml` (SOC-204/207/217/249/250/251 entries added/updated to
  reflect the generalized `appraise_contract()` — Parity phase)
- `docs/parity_ledger/town_resource.yaml` (TOWN-182 entry updated to describe the new
  Paid-Information appraisal gate — Parity phase; remainder of the diff is YAML re-serialization
  noise from the ledger writer tooling, not a second semantic change)
- `docs/simulation/social_systems_contract.md` (Contract-kinds table extended with
  MERCHANT/TEAM_UP/PAID_INFORMATION rows — Document-Update phase)
- `staging_artifacts/TCK-20260824-AFFECTION-CONTRACT-GATE/investigation.md` (pre-existing from
  this pipeline's Investigate phase, not modified by Implement)
- `staging_artifacts/TCK-20260824-AFFECTION-CONTRACT-GATE/plan.md` (Deviations section added by
  Implement)
- `staging_artifacts/TCK-20260824-AFFECTION-CONTRACT-GATE/test_plan.md` (pre-existing from this
  pipeline's Investigate phase, not modified by Implement)
- `tickets/inprogress/TCK-20260824-AFFECTION-CONTRACT-GATE.md` (this file)

## Completion Summary

Generalized `SocialAppraisalSystem.appraise_contract()`'s kind-dispatch to cover `MERCHANT`
(Trade), and two new `ContractKind` values, `TEAM_UP` and `PAID_INFORMATION`, each with a
dedicated hard-cancel-then-score appraiser reusing the existing untouched trust/hard-cancel
prelude (`bond.sentiment`-priority-else-`trust_history`, 0.2/-0.8/betrayal thresholds unchanged).
Added `CoreActions.execute_team_up()`/`execute_trade()` action handlers (mirroring
`execute_recruit()`, no gold transfer per Design Decision 5) wired into `ActionRouter`, and gated
`PaidInformationTransactionSystem.enforce()`'s previously-unconditional `ResourceTransferIntent`
emission on the same shared helper via a transient `ContractState`, closing the ticket's core
zero-check-today gap. All 4 acceptance criteria are satisfied and covered by new/extended tests
(308 tests passing in the scoped suite, no regressions to RECRUITMENT/LOAN/POSITION_SWAP
appraisal or to `PartyCompositionScorer`). Parity ledger (`docs/parity_ledger/social_narrative.yaml`,
`docs/parity_ledger/town_resource.yaml`) and doc updates (`docs/simulation/social_systems_contract.md`)
were deferred past this Implement phase as planned, and have since been completed by this same
pipeline run's later Parity and Document-Update phases -- both are done as of this Verify pass (see
Files Changed).

**Human override recorded at Verify (top-level orchestrator, not the implementer):** the static
`docs_to_update_coverage` check (`tools/gate_checks/done_checker_static.py`) blocked on
`investigation.md`'s conditional bullet for `docs/mechanics/04_strategic_cognition.md`
("only if the implementer chooses to route Team-Up through tier-5 `GoalRegistry` materialization").
The condition was genuinely never met -- confirmed independently, twice, by two different parties
(the top-level orchestrator via direct `git diff ... | grep -i "GoalRegistry|tier.5"`, zero matches;
and a separately-dispatched `done-checker` agent's own fresh re-verification of the same command)
-- so the doc correctly did not need touching. The checker is a pure path-presence regex match
(`_DOCS_BULLET_RE`) with no ability to recognize a conditional bullet resolved as not-applicable,
regardless of what prose follows the path -- confirmed structurally unpassable as currently written,
not a one-off oversight. Filed as its own tooling ticket,
`TCK-20260829-DOC-COVERAGE-CONDITIONAL-BULLET-BLIND-DOD-BLOCKED`, for the real fix. This ticket was
finalized with the `docs_to_update_coverage` FAIL treated as a confirmed-false-positive human
override rather than routed around by editing `investigation.md`'s bullet further or deleting it --
the artifact's prose was left as the accurate "Resolved during implementation, condition not met"
record from the Verify attempt, since that is the honest state of the investigation regardless of
whether the checker can parse it.
