---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260902-MARRIAGE-PROPOSAL-CONTRACT
phase: done
date: 2026-09-02
tags: [lifecycle, social]
---

# TCK-20260902-MARRIAGE-PROPOSAL-CONTRACT

## Title
Marriage — new ContractKind.MARRIAGE propose/accept mechanism, following the TEACH precedent

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P3

## Request Summary
Covers idea 33 (Marriage) from `docs/plans/rpg_design_roadmap/rpg_m3_family_species_epic.md`. No `ContractKind.MARRIAGE` or `MarriageState` exists yet. The exact reusable precedent is `ContractKind.TEACH` (landed in `TCK-20260831-TRUST-GATED-TEACHING`): a new enum member on `ContractKind` (`src/core/strategic.py`), a new `_appraise_marriage()` static method dispatched from `SocialAppraisalSystem.appraise_contract()` (`src/systems/social_systems/appraisal.py`), and a transient `ContractState`-then-appraise handler in `core_actions.py`. Independent of the other M3 concerns — per the 2026-08-29 build-order decision, Marriage is decoupled from Reproduction (idea 32) and does not gate it, and was explicitly investigated and rejected as a shared mechanism with Coming of Age (idea 34) — only a shared eligibility-precondition helper (alive/adult/same-race/not-already-X) is worth extracting, not a merged ticket or handshake state machine. Fantasy-year aging/lifecycle-duration numeric thresholds are out of scope, blocked on a not-yet-landed calendar-authority migration ticket (`TCK-20260829-TEMPORAL-CALENDAR-AUTHORITY` recorded the decision only, no migration code yet).

## Scope
- Add `ContractKind.MARRIAGE` to the enum in `src/core/strategic.py`, following the `docs/simulation/social_systems_contract.md` checklist exactly: enum member, appraisal method, breach conditions, tests.
- Add `SocialAppraisalSystem._appraise_marriage()` (`src/systems/social_systems/appraisal.py`), dispatched from `appraise_contract()`'s kind-branch as one new `elif` + one new method — do not modify the shared trust hard-cancel prelude (lines 48-54: `trust_score<0.2` → `TOTAL_DISTRUST`, `betrayal_count>0 and trust_score<0.4` → `BETRAYAL_HISTORY`, `bond.sentiment<-0.8`), which is covered by P0 parity entries `SOC-001`/`SOC-008`/`SOC-134`.
- Proposing marriage builds a transient (non-persisted) `ContractState(kind=ContractKind.MARRIAGE, source_id=<proposer>, target_id=<target>, status=OFFERED)` and calls `appraise_contract(target, temp_contract, state)`.
- On ACCEPTED, write a new typed durable record (e.g. `MarriageState`: proposer_entity_id, target_entity_id, status enum PROPOSED/ACCEPTED/REJECTED, married_tick) via a typed `EntityUpdate`/`StateUpdate` on both parties — never via `reason`/`terms` free-form dict fields.
- Resolve the "proposal-lifecycle prerequisites" ambiguity explicitly at Plan time: confirm whether the existing Contracts offer/accept machinery (already real and ready per the TEACH/TEAM_UP precedent) is sufficient to unblock Marriage today, or whether a separate not-yet-filed shared-`ProposalState` extraction is actually required first.

## Out of Scope
- Reproduction (idea 32) as a marriage precondition or vice versa — explicitly decoupled per the 2026-08-29 build-order decision; do not gate either on the other.
- Household/family/dependents durable state beyond a bare `MarriageState` record — that belongs to idea 31 (Personal Dependents, TCK-20260902-PERSONAL-DEPENDENTS-ROUTE-BIAS), a separate ticket; draw a hard line between "propose/accept handshake lands" (this ticket) and any dependents/family state model.
- Fantasy-year aging or any lifecycle-duration numeric threshold — blocked on the unmigrated calendar-authority ticket; do not introduce a new duration formula here.
- Any shared/generic `ProposalState` base-class extraction across Marriage/Team-Up/Trade/Clan-entry — aspirational per the schema doc but not built; only build it if Plan explicitly decides it's in scope, otherwise follow the direct TEACH-pattern precedent without it.
- Modifying the shared trust hard-cancel prelude in `appraisal.py` (lines 48-54).

## Acceptance Criteria
- [x] `ContractKind.MARRIAGE` exists in `src/core/strategic.py`'s enum.
- [x] `SocialAppraisalSystem._appraise_marriage()` exists and is dispatched correctly, with the shared trust hard-cancel prelude unmodified — a test confirms a proposal below hard-cancel thresholds (trust_score<0.2, or betrayal_count>0 and trust_score<0.4, or bond.sentiment<-0.8) is rejected with no marriage-specific bypass, mirroring `test_teach_refused_below_trust_hard_cancel_threshold`'s assertion shape.
- [x] Proposing marriage builds a transient `ContractState` and calls the real `appraise_contract()` path; on ACCEPTED, a new typed durable `MarriageState`-equivalent record is written via a typed `EntityUpdate`/`StateUpdate` on both parties.
- [x] No `reason`/`terms` free-form dict field carries the accepted-marriage outcome — verified as a typed field.
- [x] No fantasy-year aging or lifecycle-duration numeric threshold is introduced by this ticket.
- [x] New unit tests added following `tests/unit/social/test_teach.py`'s and `tests/unit/social/test_team_up.py`'s conventions.
- [x] A new Mechanics Bible entry (likely under `docs/mechanics/04_strategic_cognition.md` or a new social-law section) documents the propose/accept-relationship law, since none currently exists for idea 33 per the compliance table in `docs/brainstorm/rpg_feature_atlas.html`.

## Related Tickets
- TCK-20260831-TRUST-GATED-TEACHING (direct precedent — `ContractKind.TEACH` pattern)
- TCK-20260824-AFFECTION-CONTRACT-GATE
- TCK-20260829-TEMPORAL-CALENDAR-AUTHORITY (decision-record only; fantasy-year aging blocked on its still-pending migration)
- TCK-20260902-PERSONAL-DEPENDENTS-ROUTE-BIAS (adjacent, hard scope boundary — household/family state belongs there, not here)

## Related Docs
- docs/plans/rpg_design_roadmap/rpg_m3_family_species_epic.md
- docs/simulation/social_systems_contract.md (the exact checklist to follow)
- docs/brainstorm/rpg_expected_schemas.html (schema-33 card — the actual descriptive card; the live atlas HTML has no `id="idea-33"` anchor despite idea_index.json pointing to it)
- docs/brainstorm/design_merit_scorecard.html (score-33)
- docs/guidelines/intentional_divergences.md

## Related Stored Artifacts
None.

## Related Code Areas
- src/core/strategic.py
- src/systems/social_systems/appraisal.py
- src/engine/domain/core_actions.py
- src/engine/domain/action_router.py

## Assumptions / Open Questions
- Whether "proposal-lifecycle prerequisites" (from the roadmap's decoupling note) refers to the already-ready Contracts machinery (Marriage unblocked today) or a not-yet-filed shared-`ProposalState` extraction is ambiguous — resolve explicitly at Plan time rather than assuming either.
- No generic reusable `ProposalState`/proposal-lifecycle base infrastructure exists anywhere in `src/` today (confirmed by grep — only unrelated similarly-named classes: `AllianceProposal` in faction diplomacy, `ActionProposal` in `core/actions.py`, `ProposeSimulationEnhancementsWorkflow` in `lab/`); the schema-33 doc's shared-base aspiration is not built.

## Implementation Notes

Implemented all 13 plan.md steps exactly, in the ordered dependency sequence the plan specifies
(enum/dataclass -> durable-storage chain -> ReasonCode -> appraisal -> action/router -> test-only
lock -> canonicalization/fingerprint -> new test file -> parametrization extensions -> docs).

- Step 1-2: `ContractKind.MARRIAGE` added after `TEACH`; `MarriageStatus(str, Enum)` (PROPOSED/
  ACCEPTED/REJECTED) and `MarriageState` dataclass added directly after `ContractState` in
  `src/core/strategic.py`. Per the architecture review's style nit, `MarriageState` uses
  `@dataclass(frozen=True, slots=True)` — matching every other dataclass in the file (not just
  `frozen=True` as plan.md's illustrative code snippet showed).
- Step 3-5: `StrategicComponent.marriages: Dict[str, MarriageState]` added after `contracts`;
  `StrategicUpdate.marriages_add_or_update`/`marriages_remove` added and threaded through
  `is_noop()`/`merge()`; `Patch.apply()` (`src/engine/patches.py`) merges `marriages` via the same
  `merge_dict(...)` helper `contracts` uses, passed into the same `replace(new_strat, ...)` call.
- Step 6-7: `ReasonCode.MARRIAGE_ACCEPTED`/`MARRIAGE_DECLINED` added after the `TEACH_*` codes;
  `SocialAppraisalSystem._appraise_marriage()` added, byte-for-byte the same shape as
  `_appraise_teach()` (prelude-only gate, unconditional ACCEPTED once reached), dispatched via a new
  `elif` branch placed after the `TEACH` branch, before the fallthrough.
- Step 8: `CoreActions.execute_propose_marriage()` added after `execute_train()`, mirroring its
  target-resolution/temp-contract/appraise-then-branch shape exactly. Target appraises proposer
  (same direction as every other two-party handler). On ACCEPTED, one `MarriageState` record
  (same id) is attached via `StrategicUpdate.marriages_add_or_update` on both the proposer's and
  the target's `EntityUpdate` — no gold/ResourceTransferIntent involved. On any other status, reuses
  the same rejection shape `execute_train()` uses (`readiness_delta=-50.0` + `task` replace on the
  proposer; `SocialUpdate(rejection_increment=...)` on the target). `ActionRouter` gained a
  `"PROPOSE_MARRIAGE"` branch placed after `"TRAIN"`.
- Step 9: `ContractKind.MARRIAGE` added to the existing exclusion parametrization in
  `test_social_contract_goal_scorer.py` — no production code change, confirmed
  `get_project_mapping()` already returns `None` for any kind other than `RECRUITMENT`/`LOAN`.
- Step 10: `"marriages"` added to `AuthoritativeState.to_canonical_dict()`'s `"strategic"` sub-dict
  (`src/core/state.py`) and a `marriage_ident` string added to `src/replay/fingerprint.py`,
  mirroring `contracts`'/`contract_ident`'s exact shape. The pre-existing `contracts`
  canonicalization gap noted in investigation.md was deliberately left untouched (out of scope).
- Step 11: new `tests/unit/social/test_marriage.py` (8 tests) — mirrors `test_teach.py`'s
  fixture/structure style. The "builds transient contract and calls real appraise_contract" test
  avoids mocking (no `unittest.mock` usage precedent exists anywhere in `tests/unit/social/`) by
  instead constructing an equivalent hand-built `ContractState` and asserting the handler's real
  outcome agrees with a direct `appraise_contract()` call on it — proving equivalence without
  patching. The "accepted writes typed MarriageState on both parties" test round-trips through the
  real `ApplyPath.apply_generation()` authoritative path, not a hand-rolled merge, per plan.md's
  Step 5 verify note.
- Step 12: extended `test_appraisal_logic.py`'s `test_shared_gate_no_fallthrough_for_gated_kinds`
  `kind_terms` dict with `ContractKind.MARRIAGE: {}`, and added a new
  `test_marriage_boundary_trust_score_matches_recruitment_and_team_up_and_teach_just_below_0_2` test
  (trust score 0.195, not 0.2 exactly — strict `<` comparison) as a separate function, leaving the
  existing TEACH-only boundary test unmodified per the plan's anti-drift guard.
- Step 13: added Mechanics Bible `## 8. Marriage Proposal Law` to
  `docs/mechanics/04_strategic_cognition.md` (after the existing `§7.3`); added a `MARRIAGE` row to
  `docs/simulation/social_systems_contract.md`'s Contract kinds table, mirroring the `TEACH` row;
  added parity ledger entry `SOC-261` (P0, `status: verified`) to
  `docs/parity_ledger/social_narrative.yaml` via `tools/parity_ledger_writer.py` (confirmed
  `SOC-260` was the last existing entry at implementation time, so `SOC-261` was the next available
  id), followed by a visible `python3 tools/parity_index.py build` call per the writer module's own
  documented convention.

No deviations from plan.md's architecture decisions (Decisions 1-4). The only deviation is the
`slots=True` style fix called out explicitly in the task brief and now also recorded in plan.md's
Deviations section.

## Test Summary

- `tests/unit/social/test_marriage.py` (new, 8 tests): all pass.
- `tests/unit/social/` + `tests/unit/ai/goals/test_social_contract_goal_scorer.py`: 259 passed.
- Full test-plan-specified sweep (`tests/unit/social/ tests/unit/ai/goals/
  tests/unit/resource/test_resource_v2_boundary.py
  tests/integration/scenarios/test_phase7_social_cooperation_scenarios.py`): 296 passed.
- Additional regression sweeps run to validate the shared-machinery touch points
  (`StrategicUpdate`/`Patch.apply()`/canonicalization/fingerprint): `tests/unit/core/` (233 passed),
  `tests/unit/engine/` (182 passed, 1 skipped, 3 deselected — pre-existing, unrelated), and the
  patch/apply-parity-specific suites (`tests/integration/optimization/test_component_patch_apply_parity.py`,
  `tests/unit/domains/optimization/test_component_patches.py`,
  `tests/architecture/test_role_set_identity_patch_only_guard.py`,
  `tests/integration/kernel/test_p1_replay_fidelity.py`: 30 passed).
- Parity tooling regression: `tests/tools/test_parity_index_baseline.py`,
  `test_parity_ledger_writer.py`, `test_parity_ledger_schema.py`, `test_parity_index.py`: 75 passed
  (no baseline drift from the new `SOC-261` entry).
- All commands run via `.venv/bin/python3 -m pytest ... -q` with scoped paths only, never the full
  `pytest tests/` sweep.

## Files Changed

- `src/core/strategic.py` — `ContractKind.MARRIAGE`; `MarriageStatus`; `MarriageState`;
  `StrategicComponent.marriages`.
- `src/core/updates.py` — `StrategicUpdate.marriages_add_or_update`/`marriages_remove`;
  `is_noop()`/`merge()` extensions; `MarriageState` added to the `TYPE_CHECKING` import.
- `src/engine/patches.py` — `Patch.apply()` marriages merge.
- `src/core/enums.py` — `ReasonCode.MARRIAGE_ACCEPTED`/`MARRIAGE_DECLINED`.
- `src/systems/social_systems/appraisal.py` — `_appraise_marriage()`; `MARRIAGE` dispatch branch.
- `src/engine/domain/core_actions.py` — `CoreActions.execute_propose_marriage()`.
- `src/engine/domain/action_router.py` — `"PROPOSE_MARRIAGE"` branch.
- `src/core/state.py` — `"marriages"` added to `to_canonical_dict()`'s strategic sub-dict.
- `src/replay/fingerprint.py` — `marriage_ident` added to the strategic fingerprint string.
- `tests/unit/ai/goals/test_social_contract_goal_scorer.py` — `ContractKind.MARRIAGE` added to the
  project-materialization exclusion parametrization.
- `tests/unit/social/test_appraisal_logic.py` — `ContractKind.MARRIAGE` added to
  `test_shared_gate_no_fallthrough_for_gated_kinds`'s `kind_terms`; new
  `test_marriage_boundary_trust_score_matches_recruitment_and_team_up_and_teach_just_below_0_2` test.
- `tests/unit/social/test_marriage.py` — new file, 8 tests.
- `docs/mechanics/04_strategic_cognition.md` — new `## 8. Marriage Proposal Law` section.
- `docs/simulation/social_systems_contract.md` — new `MARRIAGE` row in the Contract kinds table.
- `docs/parity_ledger/social_narrative.yaml` — new `SOC-261` entry (via
  `tools/parity_ledger_writer.py`).
- `docs/parity_ledger/strategic_cognition.yaml` — Parity-phase addition: new `STRAT-266` entry (P0,
  verified), documenting `MarriageState`/`StrategicComponent.marriages`'s durable-plumbing thread
  through `StrategicUpdate`, `Patch.apply()`, and `StateFingerprinter` (mirroring the `STRAT-256`
  `CommittedIntention` precedent).
- `docs/parity_ledger/infrastructure.yaml` — Parity-phase fix: `INFRA-260`'s `v2_evidence` line
  citations for `src/core/updates.py` drifted (`946-950`→`952-956`, `663-697`→`669-703`) because
  this ticket's new `marriages` fields shifted nearby code by 6 lines; corrected, no behavioral
  change to the underlying claim.
- `tickets/inprogress/TCK-20260902-MARRIAGE-PROPOSAL-CONTRACT.md` — this file (Status, Acceptance
  Criteria, Implementation Notes, Test Summary, Files Changed, Completion Summary).
- `staging_artifacts/TCK-20260902-MARRIAGE-PROPOSAL-CONTRACT/plan.md` — new "Deviations" section
  documenting the `slots=True` style fix.

## Completion Summary

Implemented `ContractKind.MARRIAGE` end to end following the `TEACH` precedent exactly: a new
`MarriageStatus`/`MarriageState` durable record type (with the requested `slots=True` house-style
fix applied), threaded through `StrategicComponent`/`StrategicUpdate`/`Patch.apply()`/
canonicalization/fingerprint the same way `contracts` already is; a prelude-only
`_appraise_marriage()` dispatch branch in `SocialAppraisalSystem`; a new
`CoreActions.execute_propose_marriage()` action (routed via a new `"PROPOSE_MARRIAGE"`
`ActionRouter` branch) that builds a transient `ContractState`, has the target appraise the
proposer, and on acceptance writes one typed `MarriageState` record onto both parties via the
authoritative apply path — never through a `reason`/`terms` free-form field. Bigamy prevention,
household/family state, and fantasy-year aging/duration thresholds were deliberately left out of
scope per the plan's Decisions 1-4. All 13 plan steps landed with a passing scoped test sweep (296
tests across the test-plan's specified surface, plus broader regression sweeps on the shared
`StrategicUpdate`/`Patch.apply`/canonicalization/fingerprint/parity-tooling touch points, all
green) and the required Mechanics Bible, social-systems-contract, and parity-ledger doc updates.
