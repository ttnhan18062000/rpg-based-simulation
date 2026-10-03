---
status: historical
layer: economy
authority: P2
audience: agent
ticket_id: TCK-20260831-TRUST-GATED-TEACHING
artifact_type: test_plan
tags: [social, economy]
---

# Test Plan — TCK-20260831-TRUST-GATED-TEACHING

## Regression Surface

Existing tests that must keep passing (or be deliberately, explicitly updated if the two-party
signature change requires it — never silently broken):

**Integration / pipeline (direct regression surface for `execute_train()`):**
- `tests/unit/resource/test_resource_v2_boundary.py::test_class_hall_train_refactor` — the **only**
  existing test exercising `CoreActions.execute_train()` today (via `SimulationDomainLogic.
  execute_action` → `AuthoritativeApplyPipeline.refine` → `ApplyPath.apply_generation`), asserting
  `gold == 50` (from 100) and `"STRIKE" in ... known_recipes`. This test's call shape (single entity,
  no `target_id`) will not match a two-party signature — it must be updated (two entities, a
  `target_id` in payload, a pre-set trusting bond) rather than left broken, per this ticket's own AC
  #1.

**Unaffected but must be confirmed unchanged (orphaned duplicate, same underlying mechanic, different
code path):**
- `tests/unit/world/test_recovery_class_hall.py::test_class_hall_training` — exercises
  `ClassHallAction.train()` (`src/town/class_hall.py`), not `CoreActions.execute_train()`. Not in this
  ticket's Related Code Areas; must still pass unmodified as evidence the orphaned duplicate was not
  incidentally touched.
- `tests/unit/world/test_recovery_class_hall.py::test_class_hall_inn_rest_recovery` — same file,
  unrelated inn-recovery mechanic; confirms no accidental cross-contamination in that file.

**Shared trust/hard-cancel gate — must not regress if Teaching reuses/routes through it:**
- `tests/unit/social/test_appraisal_logic.py` — full suite, in particular
  `test_shared_gate_no_fallthrough_for_gated_kinds`, `test_shared_gate_dispatches_by_kind`, and the
  existing `RECRUITMENT`/`LOAN`/`POSITION_SWAP`/`MERCHANT`/`TEAM_UP`/`PAID_INFORMATION` appraisal
  tests — byte-identical outcomes required; the shared prelude (`appraisal.py:19-54`) must not move
  or change numerically.
- `tests/unit/social/test_recruitment.py`, `tests/unit/social/test_betrayal_consequence.py`,
  `tests/unit/social/test_team_up.py`, `tests/unit/social/test_trade.py` — other consumers of the
  same shared prelude; must show no outcome drift.
- `tests/unit/social/test_social_bonds.py`, `tests/unit/social/test_source_trust.py` — trust/bond
  read-path regression surface (`entity.social.bonds`/`trust_history` semantics must stay exactly as
  read by the reused threshold formula).

**Durable-state / apply-path regression surface (`recipes_learned`/`known_recipes`, unrelated to
Teaching specifically but touched by any change to how `IdentityUpdate` is emitted from
`execute_train`):**
- Any existing test asserting `IdentityComponent.known_recipes` behavior via
  `src/engine/patches.py`'s merge logic — confirm via `grep -rln "known_recipes" tests/` before
  implementation and re-run that scoped set; `execute_allocate_ap`'s own direct-`EntityUpdate.identity`
  pattern (the shape this ticket adopts) has no dedicated test file of its own found in this
  investigation, so no separate regression surface beyond the general `IdentityUpdate.merge()`
  unit-level coverage (if any exists — not confirmed in this investigation; test-scoper/implementer
  should re-check `tests/unit/core/` or `tests/unit/engine/` for `IdentityUpdate` merge tests before
  implementation).

**Economy / conservation regression surface (only if the planner's AC #4 decision changes or removes
the gold leg):**
- `src/core/conservation.py`'s `TOWN_SERVICE` branch — no dedicated unit test found isolating this
  branch by name in this investigation; `test_class_hall_train_refactor` above is the closest
  end-to-end coverage. If the gold leg is removed, this branch's `TOWN_SERVICE` handling for other
  consumers (`TAX`, `REPAIR_FEE`, `SERVICE_FEE`, `INFORMATION_PURCHASE`) must remain byte-identical —
  scope any conservation.py-adjacent test run broadly enough to catch a shared-branch regression
  (`tests/unit/resource/`, `tests/unit/economy/` if it exists — confirm directory name before running).

## New Tests Required

Per acceptance criteria (AC #1-4 from the ticket):

1. **`test_teach_action_requires_teacher_and_target`**
   - Category: unit
   - Verifies: the teach/train action's payload now requires (or defaults sensibly and is exercised
     with) both a teacher entity and a target entity — asserts `execute_train()` (or its renamed
     equivalent, per plan.md) returns updates keyed by both party ids when both are present, and a
     clear failure (e.g. `TARGET_NOT_FOUND`, mirroring `execute_recruit`'s existing failure shape) when
     the target cannot be resolved via `neighbor_view`/`context.entities` — mirroring
     `test_team_up.py::test_execute_team_up_target_not_found`'s pattern.
   - Location: `tests/unit/social/test_teach.py` (new file, following the `test_team_up.py`/
     `test_trade.py` naming/location precedent from AFFECTION-CONTRACT-GATE) — or
     `tests/unit/resource/test_resource_v2_boundary.py` if plan.md keeps Teaching adjacent to the
     existing `test_class_hall_train_refactor` test instead of giving it a dedicated social-domain
     test file; planner must pick one location explicitly.

2. **`test_teach_refused_below_trust_hard_cancel_threshold`**
   - Category: unit
   - Verifies: when trust between teacher and target is below the shared hard-cancel threshold
     (`trust_score < 0.2` or `bond.sentiment < -0.8`, per `appraisal.py:48`), the action is refused
     and **emits no `IdentityUpdate(recipes_learned=...)`** anywhere in either party's returned
     `EntityUpdate` — this is AC #2's explicit assertion, so the test must inspect
     `updates[target_id].identity` (or equivalent) and assert it is `None`/a no-op `IdentityUpdate`,
     not merely assert an "outcome: FAILURE" marker.
   - Location: same file as test 1.

3. **`test_teach_succeeds_when_trust_clears_emits_direct_identity_update`**
   - Category: unit
   - Verifies AC #3: when trust clears the threshold, the action emits its own domain-specific
     `IdentityUpdate(recipes_learned=[skill_id])` **set directly on `EntityUpdate.identity`**, not
     nested inside a `ResourceTransferIntent.identity_upd` — assert
     `updates[target_id].identity.recipes_learned == [skill_id]` (or the assigned target of the
     learned recipe per plan.md's teacher/target mapping) and, separately, assert
     `updates[target_id].resource_transfers` either does not carry the identity mutation or (if AC #4
     resolves to gate-alongside-gold) carries only the gold leg with no `identity_upd` set on the
     intent itself — this distinguishes "direct emission" from "still nested but now also
     trust-checked," which would fail AC #3's literal wording.
   - Location: same file as test 1.

4. **`test_teach_gold_cost_decision_is_enforced_as_scoped`**
   - Category: unit
   - Verifies AC #4's chosen behavior explicitly: if the planner decides trust *replaces* gold, assert
     a successful teach with `target.inventory.gold == 0` (or any gold amount) still succeeds and no
     `ResourceTransferIntent`/gold deduction occurs. If the planner decides trust *gates alongside*
     gold, assert both (a) a trusting-but-poor target/teacher still fails on insufficient gold with the
     existing `ACTION_EXHAUSTION`-style rejection (**this requires actually setting `gold_cost` on the
     `ResourceTransferIntent`, unlike today's no-op check — see investigation's affordability-check
     gap finding**), and (b) a trusting-and-affording pair succeeds with gold correctly deducted. This
     test's exact shape depends entirely on the planner's AC #4 decision and must be written to match
     plan.md, not to a guess.
   - Location: same file as test 1.

5. **`test_teach_target_appraises_teacher_trust_not_vice_versa`** (or the reverse, per whichever
   direction plan.md settles on — see investigation Open Question 3)
   - Category: unit
   - Verifies the specific appraisal direction chosen (student appraises teacher, or teacher appraises
     student) is what's actually implemented — guards against an accidental direction-flip bug that
     would silently gate on the wrong party's bonds.
   - Location: same file as test 1.

6. **`test_teach_does_not_regress_shared_appraisal_prelude`** (architecture guard)
   - Category: architecture guard / integration
   - Verifies: if the planner routes Teaching through `SocialAppraisalSystem.appraise_contract()` with
     a new `ContractKind.TEACH`, the shared prelude thresholds (`0.2`/`-0.8`/betrayal `0.4`) are
     reused unmodified — assert identical `ReasonCode`/`ContractStatus` behavior for a
     boundary-value trust score (e.g. exactly `0.2`) as the existing `RECRUITMENT`/`TEAM_UP` paths
     produce for the same trust score, proving no kind-specific threshold drift was introduced.
   - Location: `tests/unit/social/test_appraisal_logic.py` if a new `ContractKind.TEACH` branch is
     added there; otherwise this guard is not applicable and should be replaced with an equivalent
     inline-formula-consistency test in `test_teach.py` if the inline-threshold-reuse route is chosen
     instead (per investigation Open Question 2).

7. **`test_teach_no_fallthrough_to_unknown_reason_code`** (only if routed via `ContractKind.TEACH`)
   - Category: unit
   - Verifies: `appraise_contract()` never falls through to `(CANCELLED, ReasonCode.UNKNOWN, {})` for
     `ContractKind.TEACH` — mirrors `test_shared_gate_no_fallthrough_for_gated_kinds`'s existing
     pattern, extended to include the new kind.
   - Location: `tests/unit/social/test_appraisal_logic.py`.

8. **`test_class_hall_train_refactor_updated_for_two_party_signature`** (regression-surface update,
   not strictly "new" but requires substantive rewrite)
   - Category: integration
   - Verifies: the existing pipeline-level test is updated to construct a teacher and a target entity
     with a pre-set trusting bond, and still asserts the full pipeline
     (`SimulationDomainLogic.execute_action` → `AuthoritativeApplyPipeline.refine` →
     `ApplyPath.apply_generation`) produces the expected `known_recipes` and gold-balance outcome per
     the AC #4 decision.
   - Location: `tests/unit/resource/test_resource_v2_boundary.py` (in place, same test name or a
     clearly-named successor — planner/implementer should decide whether to rename or keep the name
     given it still exercises the "class hall train" concept).

## Scoped Pytest Commands

```
pytest tests/unit/social/ tests/unit/resource/test_resource_v2_boundary.py tests/unit/world/test_recovery_class_hall.py tests/unit/ai/goals/test_social_contract_goal_scorer.py -v
```

If the planner routes Teaching through a new `ContractKind.TEACH`, also include:
```
pytest tests/unit/strategic/test_strategic_social_contracts.py tests/unit/strategic/test_social_contract_materialization.py -v
```
(these cover `ContractState`/`ContractKind` construction and materialization broadly, per the
AFFECTION-CONTRACT-GATE precedent's own scoped-run selection — confirm these paths still exist before
running, they were the precedent ticket's stated scoped command).

Never run the bare `pytest tests/` per project convention — always scoped to the social/economy
domains above plus the one integration file directly exercising `execute_train()`.

## Anti-Drift Test Guards

- **`test_teach_does_not_widen_get_project_mapping`**: if `ContractKind.TEACH` is introduced, extend
  `tests/unit/ai/goals/test_social_contract_goal_scorer.py`'s existing parametrized exclusion test
  (already covering `PROTECTION`/`MERCHANT`/`POSITION_SWAP`/`TEAM_UP`/`PAID_INFORMATION`) to include
  `TEACH`, asserting `ContractService.get_project_mapping()` still returns `None` for it — locks in
  the ticket's own Out of Scope line.
- **`test_execute_allocate_ap_unchanged`**: run the existing `execute_allocate_ap` tests (if any exist
  — confirm location) unmodified, to prove the direct-`EntityUpdate.identity` pattern this ticket
  copies from that function was reused, not refactored, in the source function itself.
- **`test_class_hall_action_train_unaffected`**: `tests/unit/world/test_recovery_class_hall.py::
  test_class_hall_training` must pass byte-identical to its pre-ticket behavior — proves the orphaned
  `ClassHallAction.train()` duplicate was not silently touched (per the investigation's explicit
  Anti-Drift Hazard against doing so without a planner decision).
- **`test_shared_prelude_thresholds_unchanged`**: any test in `test_appraisal_logic.py` asserting the
  exact `0.2`/`-0.8`/`0.4` threshold values must still pass — a numeric drift here would silently
  change every other consumer of `appraise_contract()` (`RECRUITMENT`, `LOAN`, `POSITION_SWAP`,
  `MERCHANT`, `TEAM_UP`, `PAID_INFORMATION`), not just Teaching.
- **`test_train_action_still_routes_through_action_router`**: confirm `ActionRouter.execute_action()`'s
  `"TRAIN"` branch (`action_router.py:58-59`) still dispatches correctly after any payload-shape
  change (e.g. an added `target_id`) — catches a signature-mismatch regression at the routing layer,
  not just inside `core_actions.py`.
- **`test_project_kind_training_unaffected`**: no test in this ticket's scope should touch
  `ProjectKind.TRAINING`/`RouteFamily` "TRAIN_SKILL" materialization logic — if a test accidentally
  starts asserting on strategic-project selection instead of the domain action, that is scope creep
  into the AI goal-routing layer explicitly flagged as out of this ticket's Related Code Areas.
