---
status: historical
layer: economy
authority: P2
audience: agent
ticket_id: TCK-20260831-TRUST-GATED-TEACHING
artifact_type: plan
tags: [social, economy]
---

# Implementation Plan — TCK-20260831-TRUST-GATED-TEACHING

## Summary

`CoreActions.execute_train()` (`src/engine/domain/core_actions.py:327-361`) becomes a two-party
action: `entity` is the skill-holding teacher, `payload["target_id"]` is the student. The teach
is gated by routing a transient `ContractState(kind=ContractKind.TEACH)` through
`SocialAppraisalSystem.appraise_contract()` — the **target appraises the teacher**, exactly
mirroring `execute_recruit`/`execute_team_up`/`execute_trade`'s existing `entity`=initiator,
`target`=appraiser convention (`core_actions.py:94,183,258`). The shared hard-cancel prelude
(`trust_score<0.2` or `bond.sentiment<-0.8`, `appraisal.py:48`) is the only new gating logic
added — once it passes, `_appraise_teach` accepts unconditionally, matching the ticket's Scope
text ("gated on trust... using appraise_contract()'s shared hard-cancel threshold", not a new
utility-scoring model). Trust **replaces** the 50-gold `TRAIN_COST` entirely — the gold leg
(`ResourceTransferIntent`/`TRAIN_COST`) is removed from `execute_train()` with no replacement
affordability check. On acceptance, `recipes_learned`/blocker-resolution are emitted directly on
the **target's** `EntityUpdate.identity` (not nested in a `ResourceTransferIntent`), mirroring
`execute_allocate_ap`'s existing direct-`EntityUpdate.identity` pattern (`core_actions.py:319-324`).
`ClassHallAction.train()` (`src/town/class_hall.py`) is explicitly left untouched — it is an
orphaned, unwired duplicate not in this ticket's Related Code Areas, and reconciling it is a
separate architectural cleanup this ticket does not attempt (flagged as a future-ticket
candidate, not planned work here).

## Decisions on the Three Open Questions (resolved, not deferred)

**Decision 1 — trust replaces the 50-gold `TRAIN_COST` entirely (not gate-alongside).**
Evidence: (a) the ticket's own originating design source
(`docs/brainstorm/rpg_feature_atlas.html:2017-2025`, idea 6) explicitly frames this as "gated on
an existing trust threshold **instead of** gold"; (b) `ResourceTransactionResolver.resolve()`'s
`TOWN_SERVICE` branch (`src/core/conservation.py:254-271`, confirmed by investigation) never
enforces the 50-gold cost today — `gold_cost` is never set on the intent
(`ResourceTransferIntent.gold_cost` defaults to `0`, `src/core/update_models/resources.py:24`,
confirmed by direct read), so the affordability check is always `gold < 0` = `False` = always
accepted; (c) `CLASS_HALL` is an untracked abstract sink (confirmed: no `CLASS_HALL`-keyed
balance anywhere in `src/core/state.py`), so removing the gold leg breaks no tracked-object
conservation pairing under Mechanics Bible Ch.3 §1; (d) implementing gate-alongside would require
*adding* a real affordability check that does not exist today (setting `gold_cost=TRAIN_COST` on
the intent) — that is new economic-enforcement scope the ticket's ACs do not ask for. Consequence:
`execute_train()` emits no `ResourceTransferIntent` at all; gold is untouched by teaching. This is
a genuine behavior change (today, gold is deducted-and-clamped even though never blocking) and
must be recorded in `docs/guidelines/intentional_divergences.md` (Step 11).

**Decision 2 — full `appraise_contract()` routing with a new `ContractKind.TEACH` (not an inline
threshold copy).** Evidence: (a) the ticket's own Out of Scope line ("even if a new
`ContractKind.TEACH` is introduced") anticipates this route as the expected outcome; (b)
`ContractService.get_project_mapping()` (`src/systems/social_systems/contracts.py:138-152`,
confirmed by direct read) already returns `None` for any `ContractKind` not explicitly
`RECRUITMENT`/`LOAN` — adding `ContractKind.TEACH` requires **zero code change** to that function
to stay out of its tier-5 materialization coverage; it falls through to `None` by construction.
This makes the "don't widen `get_project_mapping()`" guard free to satisfy under the full-routing
option, removing the main cost that would otherwise favor the inline-threshold alternative. (c)
Full routing reuses the AFFECTION-CONTRACT-GATE precedent's established pattern exactly (one new
`elif` branch + one new `_appraise_<kind>` static method, `appraisal.py:56-81`) rather than
duplicating the two threshold numbers in a second location.

**Decision 3 — `entity` = teacher/initiator, `payload["target_id"]` = student; the student
(target) appraises the teacher (entity).** Evidence: every existing two-party handler in this file
(`execute_recruit:94`, `execute_team_up:183`, `execute_trade:258`, all confirmed by direct read)
calls `appraise_contract(target, temp_contract, context)` — the *target* is always the appraiser
of an offer from `entity`. Applied to Teaching: the student's trust in the teacher gates whether
the student accepts being taught. `recipes_learned` and capability-blocker resolution therefore
apply to the **target's** (student's) `EntityUpdate`, not the teacher's — this is a real
restructuring of the current single-`EntityUpdate` return shape, not a one-line swap.

**Drift hazard decision — `ClassHallAction.train()` (`src/town/class_hall.py:9-44`) is left
untouched.** It is not in this ticket's Related Code Areas, has no caller anywhere in `src/`
(confirmed via investigation's `grep -rn "class_hall\|ClassHall" src/ tests/`), and reconciling or
retiring it is a separate architectural decision no AC requires. Leaving it produces a real but
already-existing drift (a dead gold-only duplicate coexisting with a now-trust-gated live path) —
noted below as a candidate for a future ticket, not absorbed into this one's scope.

**Design decision not covered by investigation's three questions, resolved here — teacher-knows-
skill precondition is explicitly NOT added.** No AC requires validating that `entity` (teacher)
already has `skill_id` in `entity.identity.known_recipes` before teaching it. Today's
`execute_train()` has no such check either (there was no second party to check against). Adding
one would be new validation logic beyond "gated on trust between them" (the ticket's literal AC
#1 wording). Per "never plan more work than ticket scope," this plan does not add it — `skill_id`
continues to come from `payload` with no cross-check against the teacher's own recipes.

## Steps

### Step 1 — Add `ContractKind.TEACH`
**Files:** `src/core/strategic.py`
**Change:** Add `TEACH = "TEACH"` to the `ContractKind` enum (`src/core/strategic.py:73-85`),
placed after `PAID_INFORMATION` (line 85), matching the existing member style (`str, Enum`,
uppercase value equal to name). No other enum in this file needs changes.
**Do NOT touch:** `ProjectKind`, `ObjectiveKind`, `GoalKind`, `DirectiveKind` — none of these are
implicated by adding a contract kind (confirmed: `get_project_mapping()` keys off `ContractKind`
only, per Decision 2 evidence above).
**Verify:** `tests/unit/social/test_appraisal_logic.py` (existing suite still passes; new kind
doesn't collide with any existing value — confirmed via full read of `strategic.py:73-85`, no
`"TEACH"` string collision found).

### Step 2 — Add `ReasonCode.TEACH_ACCEPTED` / `TEACH_DECLINED`
**Files:** `src/core/enums.py`
**Change:** Add `TEACH_ACCEPTED = "teach_accepted"` and `TEACH_DECLINED = "teach_declined"` to
`ReasonCode` (`src/core/enums.py:66`), placed near `TEAM_UP_ACCEPTED`/`TEAM_UP_DECLINED`
(confirmed at lines 157-158), matching that pair's naming/value style exactly.
**Do NOT touch:** Any other `ReasonCode` member, in particular `TOTAL_DISTRUST` /
`BETRAYAL_HISTORY` (the shared prelude's existing codes) and `UNKNOWN` (the fallthrough code) —
these must remain byte-identical.
**Verify:** No dedicated test for the enum itself; covered indirectly by Step 8's new tests
asserting these exact reason codes are returned.

### Step 3 — Add `_appraise_teach` and dispatch branch in `SocialAppraisalSystem`
**Files:** `src/systems/social_systems/appraisal.py`
**Change:** Add a new `elif contract.kind == ContractKind.TEACH:` branch in `appraise_contract()`
(after the `PAID_INFORMATION` branch, `appraisal.py:78-79`) calling a new static method
`_appraise_teach(entity, contract, trust_score)`. The method body mirrors
`_appraise_paid_information` (`appraisal.py:316-324`, confirmed by direct read) exactly — it
performs **no additional scoring**, only `return ContractStatus.ACCEPTED, ReasonCode.TEACH_ACCEPTED, {}`,
with a docstring stating the shared prelude (lines 48-54) is the entire gate this ticket's Scope
asks for ("gated on trust... using appraise_contract()'s shared hard-cancel threshold", ticket
Scope line 2) — no utility/risk model like `_appraise_recruitment` or acceptance-threshold model
like `_appraise_team_up` is introduced, since no AC requires one.
**Do NOT touch:** The shared prelude itself (`appraisal.py:29-54`) — the `0.2`/`-0.8`/`0.4`
threshold values and their ordering must not move or change numerically (P0 parity entries
SOC-001/SOC-008/SOC-134 per investigation). Do not touch `_appraise_recruitment`,
`_appraise_loan`, `_appraise_position_swap`, `_appraise_trade`, `_appraise_team_up`,
`_appraise_paid_information` — copy the pattern, do not refactor the originals.
**Verify:** New test in Step 9 (`test_appraisal_logic.py`) confirming `ContractKind.TEACH` never
falls through to `(CANCELLED, ReasonCode.UNKNOWN, {})` and confirming boundary-value trust score
(exactly `0.2`) produces the same `CANCELLED`/`TOTAL_DISTRUST` outcome as existing
`RECRUITMENT`/`TEAM_UP` paths at that same trust score.

### Step 4 — Rewrite `CoreActions.execute_train()` to a two-party, trust-gated, no-gold action
**Files:** `src/engine/domain/core_actions.py`
**Change:** Replace the body of `execute_train()` (`core_actions.py:327-361`) with a two-party
handler matching `execute_recruit`'s structural shape (`core_actions.py:55-144`, confirmed by
direct read):
1. New signature: `execute_train(entity, payload, current_tick, neighbor_view, context)` — adds
   `neighbor_view: List[tuple[int, EntityState]]` and `context: Any` parameters, matching
   `execute_recruit`/`execute_team_up`/`execute_trade`'s exact parameter list and defaults-free
   style (the router always passes these positionally, per Step 5).
2. Keep the existing `skill_id = payload.get("skill_id")` / `MISSING_SKILL_ID` check first,
   unchanged in shape (`core_actions.py:332-337`), returning `{entity.id: EntityUpdate(...)}` as
   today.
3. Resolve `target_id = payload.get("target_id")` and look up `target` via `neighbor_view` then
   `context.entities`, byte-identical to `execute_recruit`'s target-resolution block
   (`core_actions.py:63-73`). If not found, return
   `{entity.id: EntityUpdate(entity_id=entity.id, navigation=NavigationUpdate(failure_reason="TARGET_NOT_FOUND"))}`,
   matching `execute_recruit:74-78` exactly.
4. Build a transient `ContractState(id="temp_eval", kind=ContractKind.TEACH, source_id=entity.id,
   target_id=target.id, terms={}, status=ContractStatus.OFFERED, created_tick=current_tick)` and
   call `SocialAppraisalSystem.appraise_contract(target, temp_contract, context)` — **target
   appraises entity**, per Decision 3.
5. On `ContractStatus.ACCEPTED`: compute `resolved_blockers` by iterating **`target.strategic
   .blockers.items()`** (not `entity`'s — the student's blockers are what get resolved by
   learning the skill; this is a deliberate change from today's single-party version, which
   iterated `entity.strategic.blockers` because `entity` was both teacher-payer and learner).
   Build:
   - `teacher_up = EntityUpdate(entity_id=entity.id, readiness_delta=-100.0)` — teacher spends
     this tick's action, no `resource_transfers` (no gold leg, per Decision 1).
   - `student_up = EntityUpdate(entity_id=target_id, identity=IdentityUpdate(recipes_learned=[skill_id]),
     strategic=StrategicUpdate(blockers_remove=resolved_blockers))` — `identity` set **directly**
     on `EntityUpdate`, not nested inside a `ResourceTransferIntent.identity_upd`, matching
     `execute_allocate_ap`'s existing direct-assignment pattern (`core_actions.py:319-324`,
     confirmed by direct read) — this satisfies AC #3's literal wording.
   - Return `{entity.id: teacher_up, target_id: student_up}`.
6. On any other status (`CANCELLED` via `TOTAL_DISTRUST`/`BETRAYAL_HISTORY`, or the `UNKNOWN`
   fallthrough which Step 3 makes unreachable for `TEACH`): return
   `{entity.id: EntityUpdate(entity_id=entity.id, readiness_delta=-50.0, task=replace(entity.task,
   payload={**payload, "outcome": "FAILURE", "reason": status.value})), target_id:
   EntityUpdate(entity_id=target_id, social=SocialUpdate(rejection_increment={entity.id: 1},
   last_offer_tick_set=current_tick))}` — byte-for-byte the same rejection shape
   `execute_team_up`/`execute_trade` already use (`core_actions.py:207-217`, `282-292`), applied
   here for consistency. This satisfies AC #2's "the action is refused and emits no
   IdentityUpdate(recipes_learned)" — no `identity` field is set anywhere in this branch.
7. Remove `TRAIN_COST = 50` and the `ResourceTransferIntent(...)` construction entirely — no gold
   leg exists in either the accept or reject path (Decision 1).
**Do NOT touch:** `execute_allocate_ap`, `execute_repair`, `execute_interact`, `execute_survival`,
`execute_recruit`, `execute_team_up`, `execute_trade` — copy their patterns, do not refactor them.
Do not add a teacher-knows-skill precondition (see Decisions section above).
**Verify:** Steps 8's new unit tests (`test_teach.py`) — `test_teach_action_requires_teacher_and_target`,
`test_teach_refused_below_trust_hard_cancel_threshold`,
`test_teach_succeeds_when_trust_clears_emits_direct_identity_update`,
`test_teach_gold_cost_decision_is_enforced_as_scoped`,
`test_teach_target_appraises_teacher_trust_not_vice_versa`.

### Step 5 — Update `ActionRouter`'s TRAIN dispatch to pass `neighbor_view`/`context`
**Files:** `src/engine/domain/action_router.py`
**Change:** Change line 58-59 from
`if action == "TRAIN": return CoreActions.execute_train(entity, payload, current_tick)` to
`if action == "TRAIN": return CoreActions.execute_train(entity, payload, current_tick, neighbor_view, context)`,
matching the `RECRUIT`/`TEAM_UP`/`TRADE` branches immediately above it
(`action_router.py:46-53`, confirmed by direct read — `execute_action()` already receives
`neighbor_view`/`context` as its own parameters, so this is purely a pass-through, no new plumbing
into the router itself).
**Do NOT touch:** Any other branch in `execute_action()` (`REPAIR`, `INTERACT`, `ATTACK`, `SKILL`,
`AOE_ATTACK`, the survival bypass, the readiness check) — only the `TRAIN` line changes.
**Verify:** `test_train_action_still_routes_through_action_router` (new, in `test_teach.py` per
Step 8) plus the existing/updated `test_class_hall_train_refactor` (Step 6) exercising the full
`SimulationDomainLogic.execute_action` → `ActionRouter` → `CoreActions.execute_train` path.

### Step 6 — Update the existing pipeline-level regression test for the two-party signature
**Files:** `tests/unit/resource/test_resource_v2_boundary.py`
**Change:** Rewrite `test_class_hall_train_refactor` (lines 274-303, confirmed by direct read) to
construct two entities — a teacher (id 1, e.g. no gold requirement since Decision 1 removes the
gold leg) and a target/student (id 2) with a pre-set `SocialBond` toward the teacher whose
`sentiment` clears the hard-cancel threshold (e.g. `sentiment=0.8` → `trust_score=(0.8+1)/2=0.9`,
well above `0.2`). Payload becomes `{"action": "TRAIN", "skill_id": "STRIKE", "target_id": 2}`.
Call `SimulationDomainLogic.execute_action(hero, payload=payload, neighbor_view=[(2, target)])`
(mirroring how `execute_recruit`-style tests supply `neighbor_view` elsewhere in this file —
confirm exact pattern via a sibling `RECRUIT`/`TEAM_UP` test in the same file before writing).
Replace the old assertions (`ent_upd.inventory.gold_delta == -50`,
`next_state.entities[1].inventory.gold == 50`) — which no longer apply since teaching has no gold
leg — with: `next_state.entities[2].identity.known_recipes` contains `"STRIKE"` (student learns,
not teacher), and `next_state.entities[1].inventory.gold` is unchanged from its starting value
(proving no gold was deducted from either party). Rename the test only if it materially
clarifies scope (e.g. keep `test_class_hall_train_refactor` as-is per the file's existing naming,
since it still covers "class hall train" conceptually — do not invent a new phase-labeled name
per project convention against embedding process labels in identifiers).
**Do NOT touch:** `test_chest_looting_and_cooldown` (the next test in this file, line 304+) or any
other test in this file.
**Verify:** The test itself, run via the scoped pytest command in Step 10.

### Step 7 — Confirm the orphaned `ClassHallAction.train()` duplicate is unaffected
**Files:** None changed. Verification-only step.
**Change:** No code change. Run `tests/unit/world/test_recovery_class_hall.py::test_class_hall_training`
(lines 60-80, confirmed by direct read — asserts `ClassHallAction.train()`'s existing gold-only
behavior: `gold == 10` from a 60-gold start after a 50-gold train) and confirm it still passes
byte-identical to its pre-ticket behavior. This is the concrete verification of the "leave
`ClassHallAction.train()` untouched" decision above — proves no accidental cross-contamination
from Steps 1-6 (none of `src/town/class_hall.py`, `ContractKind`, or `appraise_contract()`'s
prelude are imported or exercised by this test).
**Do NOT touch:** `src/town/class_hall.py` in any way.
**Verify:** `tests/unit/world/test_recovery_class_hall.py::test_class_hall_training` and
`::test_class_hall_inn_rest_recovery` (same file) both pass unmodified.

### Step 8 — New dedicated test file `tests/unit/social/test_teach.py`
**Files:** `tests/unit/social/test_teach.py` (new)
**Change:** Add the following tests, following `tests/unit/social/test_team_up.py`'s existing
file structure/fixture style (`V2EntityBuilder`, `AuthoritativeState`, `SimulationDomainLogic
.execute_action`) as the location/naming precedent:
1. `test_teach_action_requires_teacher_and_target` — asserts `execute_train()` returns updates
   keyed by both `entity.id` and `target_id` when both are present and trust clears; asserts
   `TARGET_NOT_FOUND` navigation failure when `target_id` cannot be resolved via
   `neighbor_view`/`context.entities` (mirrors `test_team_up.py`'s
   `test_execute_team_up_target_not_found`).
2. `test_teach_refused_below_trust_hard_cancel_threshold` — sets a `SocialBond.sentiment < -0.8`
   (or trust_score `< 0.2` via low `trust_history`/`public_reputation`) from target toward
   teacher; asserts the action is refused (`ContractStatus.CANCELLED`/`ReasonCode.TOTAL_DISTRUST`
   path) and asserts `updates[target_id].identity is None` (no `IdentityUpdate` at all) — this is
   AC #2's literal assertion.
3. `test_teach_succeeds_when_trust_clears_emits_direct_identity_update` — sets a trusting bond;
   asserts `updates[target_id].identity.recipes_learned == [skill_id]` and that
   `updates[target_id].resource_transfers` is empty (proving the identity update is emitted
   directly on `EntityUpdate.identity`, not nested in a `ResourceTransferIntent.identity_upd`) —
   AC #3's literal assertion.
4. `test_teach_no_gold_leg_regardless_of_gold_balance` (renamed from test_plan's
   `test_teach_gold_cost_decision_is_enforced_as_scoped` to state Decision 1's outcome directly) —
   asserts a target/teacher pair with `gold=0` still succeeds (trust replaces gold entirely, per
   Decision 1) and that no `ResourceTransferIntent` appears in either party's `EntityUpdate` on
   success — AC #4's literal assertion of the chosen behavior.
5. `test_teach_target_appraises_teacher_trust_not_vice_versa` — asserts the gate reads from the
   **target's** `social.bonds`/`trust_history` toward the teacher (not the teacher's toward the
   target) — e.g. give the teacher a hostile bond toward the target but a trusting bond from
   target toward teacher, and assert the action still succeeds (proving direction), then invert
   and assert it fails.
6. `test_train_action_still_routes_through_action_router` — confirms `ActionRouter.execute_action()`
   still dispatches `"TRAIN"` correctly with the new `target_id`-bearing payload shape (catches a
   Step 5 regression at the routing layer specifically).
**Do NOT touch:** `test_team_up.py`, `test_trade.py`, `test_recruitment.py` — only add the new
file, do not modify existing sibling test files in this step (Step 9 below is the only step that
touches `test_appraisal_logic.py`).
**Verify:** All 6 tests pass under the Step 10 scoped pytest command.

### Step 9 — Extend `test_appraisal_logic.py` for the new `ContractKind.TEACH`
**Files:** `tests/unit/social/test_appraisal_logic.py`
**Change:** Extend the existing `test_shared_gate_no_fallthrough_for_gated_kinds` parametrization
to include `ContractKind.TEACH`, proving `appraise_contract()` never falls through to
`(CANCELLED, ReasonCode.UNKNOWN, {})` for it (Step 3's dispatch branch is reachable). Add one
boundary-value test asserting a trust score of exactly `0.2` produces the same
`CANCELLED`/`TOTAL_DISTRUST` outcome for `TEACH` as it already does for `RECRUITMENT`/`TEAM_UP` at
that same score — proving no kind-specific threshold drift was introduced in Step 3.
**Do NOT touch:** Any assertion on the existing `RECRUITMENT`/`LOAN`/`POSITION_SWAP`/`MERCHANT`/
`TEAM_UP`/`PAID_INFORMATION` parametrized cases — only add new parametrized entries/tests for
`TEACH`.
**Verify:** The extended/new tests themselves, plus the full existing suite in this file passing
unmodified (proves the shared prelude, SOC-001/SOC-008/SOC-134, is untouched).

### Step 10 — Extend the goal-scorer exclusion test to lock in the `get_project_mapping()` guard
**Files:** `tests/unit/ai/goals/test_social_contract_goal_scorer.py`
**Change:** Add `ContractKind.TEACH` to the existing parametrized list at lines 125-129
(`PROTECTION`, `MERCHANT`, `POSITION_SWAP`, `TEAM_UP`, `PAID_INFORMATION` — confirmed by direct
read) that asserts `ContractService.get_project_mapping()` returns `None`. No production code
change is required for this to pass — `get_project_mapping()` (`contracts.py:138-152`, confirmed
by direct read) already returns `None` for any kind other than `RECRUITMENT`/`LOAN` by
construction — this step only adds the explicit regression lock proving `TEACH` was never wired
into tier-5 materialization, satisfying the ticket's Out of Scope line as a tested guarantee, not
just an unwritten intention.
**Do NOT touch:** `get_project_mapping()` itself, or any other `ContractKind` entry in this
parametrized list.
**Verify:** The extended parametrized test passing for the new `TEACH` case alongside all
existing cases.

### Step 11 — Doc updates
**Files:** `docs/mechanics/03_economic_laws.md`, `docs/simulation/social_systems_contract.md`,
`docs/guidelines/intentional_divergences.md`
**Change:**
- `docs/guidelines/intentional_divergences.md`: add an entry recording that `TRAIN`'s previously
  present (if non-enforcing) 50-gold deduction is removed entirely in favor of a trust gate.
  Rationale class: "Intentional Gameplay Change." Verification: point at
  `tests/unit/social/test_teach.py::test_teach_no_gold_leg_regardless_of_gold_balance` (Step 8).
- `docs/mechanics/03_economic_laws.md`: note that the `TRAIN`/`CLASS_HALL` service fee described
  informally elsewhere is superseded, for the entity-to-entity teaching path, by a trust gate with
  no gold cost — resolve the conditional bullet investigation.md left open (Decision 1 is now
  made, so this is not a Format-1 conditional anymore).
- `docs/simulation/social_systems_contract.md`: add a `TEACH` row to the "Contract kinds" table
  per that doc's own "how to add a kind" checklist (enum member, appraisal method, tests — all
  satisfied by Steps 1/3/8-9).
**Do NOT touch:** `docs/mechanics/01_entity_anatomy.md`, `docs/engine/authoritative_pipeline.md` —
investigation confirmed neither is implicated (no new pipeline phase or entity-attribute concept
is introduced).
**Verify:** No test verifies doc content directly; verified by doc-updater/Finalize-phase review
per project convention.

### Step 12 — Parity ledger entry
**Files:** `docs/parity_ledger/social_narrative.yaml`
**Change:** Add one new P0 entry (no existing entry covers `execute_train`/`TRAIN_COST`/
`ContractKind.TEACH`, confirmed by investigation's targeted grep across all
`docs/parity_ledger/*.yaml`) describing "Teaching is gated on trust via
`SocialAppraisalSystem.appraise_contract(ContractKind.TEACH)`'s shared hard-cancel threshold; no
gold cost is charged." `test_path`: `tests/unit/social/test_teach.py::test_teach_refused_below_trust_hard_cancel_threshold`
(a P0 entry requires a passing `test_path` per the Authoritative Mechanics Rule).
**Do NOT touch:** `TOWN-102` (attribute training, a different mechanism) or `STRAT-253` (route
mapper) — neither is required by this ticket's ACs, per investigation's Parity Ledger Overlap
section.
**Verify:** `python3 tools/parity_ledger_writer.py` (or equivalent sanctioned tool) validates the
new entry's schema; do not hand-edit the YAML file directly for this addition (per project
guidance on parity-ledger YAML rewrite risk).

## Scope Guards

- **Do not widen `ContractService.get_project_mapping()`'s tier-5 goal materialization coverage**
  (`src/systems/social_systems/contracts.py:138-152`) for `ContractKind.TEACH` or any other kind —
  explicit ticket Out of Scope line, inherited from the AFFECTION-CONTRACT-GATE precedent. Step 10
  adds a test *proving* this, but no code change to `get_project_mapping()` is made or needed.
- **Do not modify the shared trust-score prelude** (`appraisal.py:29-54`) — thresholds `0.2`,
  `-0.8`, `0.4` (betrayal) must stay numerically and structurally identical; P0 parity entries
  SOC-001/SOC-008/SOC-134 depend on this.
- **Do not touch `src/town/class_hall.py`'s `ClassHallAction.train()`** — explicit decision above;
  Step 7 only verifies it, never modifies it.
- **Do not touch `ProjectKind.TRAINING`** (`src/core/strategic.py:174`) or any `RouteFamily`/
  `TRAIN_SKILL` AI-goal-routing logic — that is the strategic-intent layer, a different layer from
  this ticket's domain-action-execution scope (Related Code Areas explicitly excludes it).
- **Do not add a teacher-knows-skill precondition** to `execute_train()` — not required by any AC;
  see Decisions section.
- **Do not touch** `execute_allocate_ap`, `execute_repair`, `execute_interact`,
  `execute_survival`, `execute_recruit`, `execute_team_up`, `execute_trade`, or any branch of
  `ActionRouter.execute_action()` other than the `TRAIN` line.
- **Do not add a gold affordability check** (`gold_cost` on any `ResourceTransferIntent`) to
  `execute_train()` — Decision 1 removes the gold leg entirely; do not partially implement
  gate-alongside.

## Dependency Map

- Step 1 (ContractKind.TEACH) → prerequisite for Steps 3, 4, 9, 10 (all reference the new enum
  member).
- Step 2 (ReasonCode) → prerequisite for Step 3 (references the new reason codes).
- Step 3 (`_appraise_teach`) → prerequisite for Step 4 (`execute_train()` calls
  `appraise_contract()`, which must dispatch `TEACH` correctly) and Step 9.
- Step 4 (`execute_train()` rewrite) → prerequisite for Step 5 (router must pass the new params
  the rewritten signature needs), Step 6, and Step 8.
- Step 5 (router dispatch) → prerequisite for Step 6 and Step 8's
  `test_train_action_still_routes_through_action_router`.
- Step 7 is independent of all others (verification-only, no code change) — can run any time after
  Step 4 lands, to confirm no cross-contamination occurred.
- Steps 6, 8, 9, 10 are independent of each other once their respective prerequisite steps (4/5,
  4/5, 1/3, 1) are done — can be implemented/run in any order relative to one another.
- Steps 11, 12 (docs/parity) depend on Decisions 1-3 being implemented (Steps 1-10 complete) since
  they describe the landed behavior, not a proposal.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC #1: A teach action exists accepting both teacher entity_id and target entity_id, gated on trust between them. | Steps 1, 3, 4, 5 | `test_teach_action_requires_teacher_and_target`, `test_teach_target_appraises_teacher_trust_not_vice_versa` (Step 8); `test_class_hall_train_refactor` (Step 6) |
| AC #2: When trust is below the shared hard-cancel threshold, the action is refused and emits no IdentityUpdate(recipes_learned). | Step 4 (rejection branch) | `test_teach_refused_below_trust_hard_cancel_threshold` (Step 8) |
| AC #3: When trust clears, the action emits its own domain-specific IdentityUpdate(recipes_learned=[skill_id]) directly, not a shared generic mutation. | Step 4 (acceptance branch, direct `EntityUpdate.identity` assignment) | `test_teach_succeeds_when_trust_clears_emits_direct_identity_update` (Step 8) |
| AC #4: The ticket makes an explicit decision on gold-replacement-vs-additional-gate and states it in Scope, not left ambiguous. | Decision 1 (this plan) + Step 4 (removes gold leg) + Step 11 (records divergence) | `test_teach_no_gold_leg_regardless_of_gold_balance` (Step 8) |

## Anti-Drift Notes

- **The shared hard-cancel prelude is the entire gate for TEACH** — do not add a utility/risk
  scoring model to `_appraise_teach` (Step 3) beyond `ACCEPTED` once the prelude passes; this
  matches the ticket's literal Scope wording and avoids inventing an ungrounded "teaching
  desirability" formula no AC asks for.
- **`resolved_blockers` must iterate `target.strategic.blockers`, not `entity`'s**, in the
  rewritten `execute_train()` (Step 4) — the student is the one whose capability blocker is
  resolved by learning the skill, not the teacher. This is a genuine behavior change from today's
  single-party version and is easy to get backwards by copy-pasting the old loop unchanged.
- **`IdentityUpdate(recipes_learned=[skill_id])` must land on the target's `EntityUpdate`, not the
  teacher's** — a direction-flip here would silently make the wrong party learn the skill while
  still passing a shallow "an IdentityUpdate was emitted" test.
- **Determinism**: `target.strategic.blockers.items()` iteration for `resolved_blockers` remains a
  plain filter (append every match), not a first-match selection — do not introduce dict-order-
  dependent early-exit logic.
- **`ClassHallAction.train()` reconciliation is real but explicitly out of scope** — flagged here
  as a candidate for a future ticket (e.g. "retire or re-wire the orphaned ClassHallAction.train()
  duplicate now that CoreActions.execute_train() is trust-gated"), not planned work in this ticket.
- **Do not hand-edit `docs/parity_ledger/social_narrative.yaml`'s YAML directly** for Step 12 — use
  the sanctioned `tools/parity_ledger_writer.py` (or equivalent schema-validating tool); a raw
  Edit-tool rewrite of this file carries real corruption risk per prior project experience with
  full-file YAML rewrites.

## Unresolved Questions

None. All three open questions the investigation raised (gold-replace-vs-alongside, full-routing-
vs-inline-threshold, teacher/target and appraisal direction) are resolved above with cited
evidence, as is the `ClassHallAction.train()` drift hazard and the teacher-knows-skill precondition
question that surfaced during planning.

## Deviations

- **Step 9's boundary-value test uses `sentiment=-0.61` (`trust_score=0.195`), not a literal
  `trust_score` of exactly `0.2`.** The plan's own wording ("a trust score of exactly `0.2`
  produces the same `CANCELLED`/`TOTAL_DISTRUST` outcome") does not hold against the real shared
  prelude: `appraisal.py:48`'s comparison is strict `trust_score < 0.2`, so a trust score of
  *exactly* `0.2` does **not** trigger the hard-cancel gate at all — it falls through to
  kind-specific scoring (e.g. `RECRUITMENT` would score `ACCEPTED`/`FAIR_COMPENSATION` at that
  trust level with the test's chosen `daily_pay`, not `CANCELLED`). This was caught by writing and
  running the test, not assumed. Implemented the evidently-intended semantic instead — a trust
  score just under the threshold (`0.195`) that reliably triggers the hard-cancel for
  RECRUITMENT/TEAM_UP/TEACH alike, proving no kind-specific threshold drift — and documented the
  reasoning inline in the test's docstring
  (`tests/unit/social/test_appraisal_logic.py::test_teach_boundary_trust_score_matches_recruitment_and_team_up_just_below_0_2`).
  No production code or shared-prelude threshold was touched; this is a test-value correction only.
- **Added one test beyond Step 8's named list**:
  `tests/unit/social/test_teach.py::test_teach_resolves_target_capability_blocker_not_teacher`.
  The plan's own Anti-Drift Notes flag `resolved_blockers` iterating `target.strategic.blockers`
  (not `entity`'s) as "easy to get backwards by copy-pasting the old loop unchanged," but Step 8's
  6-test list had no test asserting this specific behavior directly. Added the 7th test to close
  that gap with real coverage rather than leaving it asserted only in prose.
- `docs/mechanics/03_economic_laws.md` was read in full and confirmed to contain **zero** mentions
  of `TRAIN_COST`/`CLASS_HALL`/training gold cost anywhere in the chapter (investigation's own
  finding, re-verified directly during implementation) — per Step 11's own conditional framing,
  this is the "confirm no change needed" outcome, not an edit. No change was made to that file.
