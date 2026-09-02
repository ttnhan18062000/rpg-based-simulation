---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260902-MARRIAGE-PROPOSAL-CONTRACT
phase: open
date: 2026-09-02
tags: [lifecycle, social]
---

# TCK-20260902-MARRIAGE-PROPOSAL-CONTRACT

## Title
Marriage — new ContractKind.MARRIAGE propose/accept mechanism, following the TEACH precedent

## Status
OPEN

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
- [ ] `ContractKind.MARRIAGE` exists in `src/core/strategic.py`'s enum.
- [ ] `SocialAppraisalSystem._appraise_marriage()` exists and is dispatched correctly, with the shared trust hard-cancel prelude unmodified — a test confirms a proposal below hard-cancel thresholds (trust_score<0.2, or betrayal_count>0 and trust_score<0.4, or bond.sentiment<-0.8) is rejected with no marriage-specific bypass, mirroring `test_teach_refused_below_trust_hard_cancel_threshold`'s assertion shape.
- [ ] Proposing marriage builds a transient `ContractState` and calls the real `appraise_contract()` path; on ACCEPTED, a new typed durable `MarriageState`-equivalent record is written via a typed `EntityUpdate`/`StateUpdate` on both parties.
- [ ] No `reason`/`terms` free-form dict field carries the accepted-marriage outcome — verified as a typed field.
- [ ] No fantasy-year aging or lifecycle-duration numeric threshold is introduced by this ticket.
- [ ] New unit tests added following `tests/unit/social/test_teach.py`'s and `tests/unit/social/test_team_up.py`'s conventions.
- [ ] A new Mechanics Bible entry (likely under `docs/mechanics/04_strategic_cognition.md` or a new social-law section) documents the propose/accept-relationship law, since none currently exists for idea 33 per the compliance table in `docs/brainstorm/rpg_feature_atlas.html`.

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

## Test Summary

## Files Changed

## Completion Summary
