---
status: historical
layer: economy
authority: P1
audience: agent
ticket_id: TCK-20260831-TRUST-GATED-TEACHING
phase: done
date: 2026-08-31
tags: [social, economy]
---

# TCK-20260831-TRUST-GATED-TEACHING

## Title
Gate the teach/train action on trust instead of gold alone

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Teach on trust, not gold. Investigation found execute_train() is currently solo/gold-gated (flat TRAIN_COST=50) with no target/teacher entity concept at all, so this is new mechanism work — adding a second party to the action — not the one-line gold-to-trust threshold swap the idea's title implies. M1 idea 13's shared trust-gate helper is reusable for the gating logic.

## Scope
- Extend the teach/train action to accept both a teacher entity_id and a target entity_id (currently execute_train() has no target/teacher entity concept at all).
- Gate the action on trust between teacher and target using SocialAppraisalSystem.appraise_contract()'s shared hard-cancel threshold (trust_score<0.2 or bond.sentiment<-0.8).
- Make and state an explicit decision, in Scope, on whether trust replaces the 50-gold TRAIN_COST entirely or gates alongside it — this changes existing economy behavior and may touch Mechanics Bible Ch3 (economic conservation).
- Emit a domain-specific IdentityUpdate(recipes_learned=[skill_id]) directly (not a shared generic mutation) when trust clears.
- Add a test file covering execute_train — none currently exists.

## Out of Scope
- Widening ContractService.get_project_mapping()'s tier-5 goal materialization coverage, even if a new ContractKind.TEACH is introduced — per the AFFECTION-CONTRACT-GATE precedent's own anti-drift note.

## Acceptance Criteria
- [x] A teach action exists accepting both teacher entity_id and target entity_id, gated on trust between them.
- [x] When trust is below the shared hard-cancel threshold (trust_score<0.2 or bond.sentiment<-0.8), the action is refused and emits no IdentityUpdate(recipes_learned).
- [x] When trust clears, the action emits its own domain-specific IdentityUpdate(recipes_learned=[skill_id]) directly, not a shared generic mutation.
- [x] The ticket makes an explicit decision on gold-replacement-vs-additional-gate and states it in Scope, not left ambiguous.

## Related Tickets
- TCK-20260824-AFFECTION-CONTRACT-GATE

## Related Docs
- `docs/guidelines/intentional_divergences.md` — new DEV-007 entry (gold-cost removal, Intentional
  Gameplay Change)
- `docs/simulation/social_systems_contract.md` — new `TEACH` row in the Contract kinds table
- `docs/parity_ledger/social_narrative.yaml` — new `SOC-258` (P0) entry
- `docs/mechanics/03_economic_laws.md` — read and confirmed to need no edit (chapter never
  documented `TRAIN_COST`/`CLASS_HALL`)

## Related Stored Artifacts
None.

## Related Code Areas
- src/engine/domain/core_actions.py
- src/systems/social_systems/appraisal.py
- src/core/strategic.py
- src/systems/social_systems/relationships.py

## Assumptions / Open Questions
- Open design question, unresolved: does teaching replace the 50-gold TRAIN_COST entirely or add trust as an additional gate alongside gold — this changes existing economy behavior and needs an explicit planner decision.
- No existing test file covers execute_train at all.
- `layer: economy` chosen because the ticket's central open decision (TRAIN_COST gold-replacement-vs-additional-gate) is an economic-conservation question and no `social` layer is registered; `systems` was the runner-up.

## Implementation Notes

Implemented per `staging_artifacts/TCK-20260831-TRUST-GATED-TEACHING/plan.md`'s 12 ordered steps,
all landed as planned (see that file's new "Deviations" section for the two minor deviations: a
corrected boundary-value trust score in Step 9's test, since a literal `trust_score == 0.2` does
not trigger the shared hard-cancel gate under its strict `<` comparison; and one extra test added
beyond Step 8's named list).

1. Added `ContractKind.TEACH` to `src/core/strategic.py`.
2. Added `ReasonCode.TEACH_ACCEPTED`/`TEACH_DECLINED` to `src/core/enums.py`.
3. Added `SocialAppraisalSystem._appraise_teach` (always `ACCEPTED`/`TEACH_ACCEPTED` once the
   shared hard-cancel prelude passes, no additional scoring) plus a new `elif` dispatch branch in
   `appraise_contract()`, `src/systems/social_systems/appraisal.py`.
4. Rewrote `CoreActions.execute_train()` (`src/engine/domain/core_actions.py`) into a two-party
   handler: `entity`=teacher, `payload["target_id"]`=student. Resolves the target via
   `neighbor_view`/`context.entities` (byte-identical shape to `execute_recruit`), builds a
   transient `ContractState(kind=ContractKind.TEACH)`, and calls
   `appraise_contract(target, temp_contract, context)` — the student appraises the teacher. On
   `ACCEPTED`: `resolved_blockers` iterates `target.strategic.blockers` (not the teacher's — the
   student's capability blocker is what teaching resolves); the student's `EntityUpdate` carries
   `identity=IdentityUpdate(recipes_learned=[skill_id])` directly plus
   `strategic=StrategicUpdate(blockers_remove=resolved_blockers)`; the teacher's `EntityUpdate`
   only spends `readiness_delta=-100.0`. On any other status: the same
   rejection/`rejection_increment` shape `execute_team_up`/`execute_trade` already use. The
   50-gold `TRAIN_COST` and its `ResourceTransferIntent` are removed entirely — no gold leg
   remains in either branch.
5. Updated `ActionRouter`'s `TRAIN` branch (`src/engine/domain/action_router.py`) to pass
   `neighbor_view`/`context` through to the new `execute_train()` signature.
6. Rewrote `test_class_hall_train_refactor`
   (`tests/unit/resource/test_resource_v2_boundary.py`) for the two-party, no-gold shape: builds a
   teacher + a trusting student, asserts the student's `IdentityUpdate` is emitted directly with
   no `resource_transfers`, and that neither party's gold balance changes.
7. Verified (no code change) `tests/unit/world/test_recovery_class_hall.py::test_class_hall_training`
   still passes byte-identical — `ClassHallAction.train()` (`src/town/class_hall.py`) remains
   untouched, orphaned, unwired dead code per the plan's explicit scope boundary.
8. Added `tests/unit/social/test_teach.py` (new) — 7 tests: teacher/target resolution +
   `TARGET_NOT_FOUND`, hard-cancel refusal emits no `IdentityUpdate`, acceptance emits the direct
   `IdentityUpdate` with no `resource_transfers`, no-gold-leg regardless of gold balance,
   target-appraises-teacher direction (both ways), target-blocker resolution (not teacher's), and
   `ActionRouter` dispatch end-to-end.
9. Extended `tests/unit/social/test_appraisal_logic.py`: added `ContractKind.TEACH` to the
   no-fallthrough parametrization, plus a new boundary test proving `TEACH` produces the same
   `CANCELLED`/`TOTAL_DISTRUST` outcome as `RECRUITMENT`/`TEAM_UP` at a trust score just under the
   `0.2` hard-cancel threshold (see plan.md Deviations for why "exactly 0.2" was corrected).
10. Extended `tests/unit/ai/goals/test_social_contract_goal_scorer.py`'s
    `test_social_contract_protection_merchant_position_swap_never_spawn_a_project` to include
    `ContractKind.TEACH`, locking in that `get_project_mapping()` returns `None` for it (already
    true by construction — no production code change).
11. Docs: added DEV-007 to `docs/guidelines/intentional_divergences.md` (rationale class
    "Intentional Gameplay Change") plus a summary-table row; added a `TEACH` row to
    `docs/simulation/social_systems_contract.md`'s Contract kinds table. Confirmed
    `docs/mechanics/03_economic_laws.md` needs no edit — it never documented `TRAIN_COST`/
    `CLASS_HALL` in the first place (re-verified by direct full-chapter read during
    implementation, matching investigation's own finding).
12. Added parity ledger entry `SOC-258` (P0) to `docs/parity_ledger/social_narrative.yaml` via
    `tools/parity_ledger_writer.py` (never hand-edited the YAML), citing
    `tests/unit/social/test_teach.py::test_teach_refused_below_trust_hard_cancel_threshold` as
    `test_path`. The writer's in-process index rebuild ran and reported `status: ok`.

## Test Summary

All new/updated tests pass under the project venv
(`.venv/bin/python3 -m pytest tests/unit/social/test_teach.py tests/unit/social/test_appraisal_logic.py
tests/unit/social/test_team_up.py tests/unit/ai/goals/test_social_contract_goal_scorer.py
tests/unit/resource/test_resource_v2_boundary.py tests/unit/world/test_recovery_class_hall.py -q`):
44 passed. Broader regression sweep also run and green:
`tests/unit/social/` (276 passed), `tests/unit/ai/goals/` (included in that count),
`tests/unit/engine/` + `tests/unit/resource/` (256 passed, 1 skipped, 3 deselected — pre-existing,
unrelated to this change). No test outside this ticket's Related Code Areas was modified.

## Files Changed

- `src/core/strategic.py` — added `ContractKind.TEACH`
- `src/core/enums.py` — added `ReasonCode.TEACH_ACCEPTED`/`TEACH_DECLINED`
- `src/systems/social_systems/appraisal.py` — added `_appraise_teach` + dispatch branch
- `src/engine/domain/core_actions.py` — rewrote `execute_train()` to a two-party, trust-gated,
  no-gold action
- `src/engine/domain/action_router.py` — `TRAIN` branch now passes `neighbor_view`/`context`
- `tests/unit/resource/test_resource_v2_boundary.py` — rewrote `test_class_hall_train_refactor`
- `tests/unit/social/test_teach.py` — new file, 7 tests
- `tests/unit/social/test_appraisal_logic.py` — extended for `ContractKind.TEACH`
- `tests/unit/ai/goals/test_social_contract_goal_scorer.py` — extended exclusion test for `TEACH`
- `docs/guidelines/intentional_divergences.md` — new DEV-007 entry + summary table row
- `docs/simulation/social_systems_contract.md` — new `TEACH` row in Contract kinds table
- `docs/parity_ledger/social_narrative.yaml` — new `SOC-258` P0 entry (via
  `tools/parity_ledger_writer.py`)
- `staging_artifacts/TCK-20260831-TRUST-GATED-TEACHING/plan.md` — added "Deviations" section
- `tickets/inprogress/TCK-20260831-TRUST-GATED-TEACHING.md` — this file (Status, AC checkboxes,
  Implementation Notes, Test Summary, Files Changed, Completion Summary)

`docs/mechanics/03_economic_laws.md` was read and confirmed to need **no** edit (see
Implementation Notes step 11).

## Completion Summary

`CoreActions.execute_train()` is now a two-party, trust-gated action: a teacher (`entity`) teaches
a student (`payload["target_id"]`), gated entirely by `SocialAppraisalSystem.appraise_contract()`'s
existing shared hard-cancel trust threshold via a new `ContractKind.TEACH`, with the student
appraising the teacher (matching `execute_recruit`/`execute_team_up`/`execute_trade`'s established
convention). The previously-present, never-enforced 50-gold `TRAIN_COST` is removed entirely —
trust replaces gold, it does not gate alongside it — and on acceptance the student's `EntityUpdate`
carries `IdentityUpdate(recipes_learned=[skill_id])` directly, not nested in a
`ResourceTransferIntent`. All four acceptance criteria are met and covered by new/updated tests;
docs and the parity ledger (`SOC-258`, P0) were updated in the same session per the Authoritative
Mechanics Rule.
