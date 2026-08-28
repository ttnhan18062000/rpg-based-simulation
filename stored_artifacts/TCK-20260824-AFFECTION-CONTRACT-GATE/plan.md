---
status: historical
layer: systems
authority: P2
audience: agent
ticket_id: TCK-20260824-AFFECTION-CONTRACT-GATE
artifact_type: plan
tags: [social, information]
---

# Implementation Plan — TCK-20260824-AFFECTION-CONTRACT-GATE

## Summary

Generalize `SocialAppraisalSystem.appraise_contract()` (`src/systems/social_systems/appraisal.py:19-72`,
read in full) in place — no new module, no new wrapper function — so its existing kind-dispatch
block (currently lines 56-72, handling `RECRUITMENT`/`LOAN`/`POSITION_SWAP` and falling through to
`CANCELLED, ReasonCode.UNKNOWN, {}` for anything else) also handles three new `ContractKind`
members: `MERCHANT` (Trade, already declared but unhandled), `TEAM_UP` (new), and
`PAID_INFORMATION` (new). The shared trust-score prelude and hard-cancel gates (lines 19-54) are
**not touched** — every new kind flows through the identical `bond.sentiment`-priority-else-
`trust_history` formula and the identical `TOTAL_DISTRUST`/`BETRAYAL_HISTORY` hard-cancels already
verified by SOC-001/SOC-008/SOC-134. Each new kind gets its own kind-specific appraiser method
mirroring `_appraise_recruitment`'s hard-cancel-then-score shape (lines 74-142). Team-Up and Trade
get new `CoreActions.execute_team_up()`/`execute_trade()` action handlers in
`src/engine/domain/core_actions.py`, mirroring `execute_recruit()` (lines 55-144) structurally, wired
into `ActionRouter` (`src/engine/domain/action_router.py:44-47` pattern). Paid-Information is gated
by synthesizing a transient `ContractState` inside `PaidInformationTransactionSystem.enforce()`
(`src/engine/pipeline_phases/paid_information.py:74-183`), mirroring `execute_recruit()`'s
`temp_contract` pattern (`core_actions.py:85-93`), and skipping intent emission for that seeker/tick
when the gate does not return `ACCEPTED`. `docs/parity_ledger/social_narrative.yaml` is updated only
for the entries whose text actually describes the now-shared prelude/dispatch behavior (SOC-204,
SOC-207, SOC-217) plus three new sibling entries (SOC-249/250/251) for the three new consumers —
SOC-001/SOC-008/SOC-134 need no edit because their cited evidence (lines 47-54, formula text) is
untouched by this plan.

## Design Decisions

**These four decisions were made by the orchestrator before this plan was written. They are
NON-NEGOTIABLE — do not reopen them.**

**DECISION 1 (sentiment vs. new field).** Reuse `bond.sentiment` as-is for the "affection" concept.
Do NOT introduce a new field. Rationale: `sentiment` is already the exact same value read by
`appraise_contract()`, `PartyCompositionScorer.score_trust_bonds()`, and
`SocialContractGoalScorer._raw_score()` for this same underlying concept; introducing a parallel
"affection" field with no consumer-level differentiation from sentiment would create a
dual-source-of-truth durable-state field with zero semantic justification.

**DECISION 2 (narrow vs. anticipate M6).** Build narrowly for the 3 named consumers
(Team-Up/Trade/Paid-Information) now. Do NOT build any Conversation-adjacent (M6 ideas 39/40)
consumer machinery. "Anticipation" is satisfied structurally: `appraise_contract()`'s signature is
already generic over `ContractKind` (accepts a `ContractState` carrying a `ContractKind`, returns
`(ContractStatus, ReasonCode, terms)`); adding one more `elif contract.kind == ...:` branch for a
future M6 kind is a natural extension of the existing if/elif dispatch, not a rework. A dedicated
dict-based dispatch table is NOT required to satisfy this — see Anti-Drift Notes.

**DECISION 3 (`ContractKind.MERCHANT` for Trade).** Trade reuses the existing declared-but-unhandled
`ContractKind.MERCHANT` value (`src/core/strategic.py:78`) — it is already declared for exactly this
semantic and is currently unhandled everywhere (`contracts.py:142`'s `get_project_mapping()`,
`social_contract_scorer.py:31` both explicitly exclude it). Do not add a new kind for Trade.

**DECISION 4 (new `ContractKind` values).** Add `ContractKind.TEAM_UP` for the Team-Up consumer
(confirmed nowhere in `src/` today — `grep -rn -i "TEAM_UP" src/ tests/` returns zero hits outside
this ticket's own new code). Add `ContractKind.PAID_INFORMATION` for the Paid-Information consumer
(`PaidInformationTransactionSystem.enforce()`, `src/engine/pipeline_phases/paid_information.py:74-183`,
read in full, has no `ContractKind`/`ContractState` at all today — driven only by
`ProjectKind.INFORMATION_SEEKING`, a different enum; reusing that name would conflate two distinct
enums).

**DECISION 5 (planner-added — no resource transfer for Team-Up/Trade acceptance).** Team-Up's and
Trade's `ACCEPTED` branch attaches `StrategicUpdate(contracts_add_or_update=[contract])` directly via
`EntityUpdate.strategic` (`src/core/updates.py:641`, confirmed a direct optional field on
`EntityUpdate` — no `ResourceTransferIntent` wrapper needed for a pure contract-state write). Neither
handler emits a `ResourceTransferIntent`/gold movement. Rationale: `src/core/conservation.py:274`'s
`intent.source_kind in ("RECRUIT", "CHEST")` branch is an explicit allowlist of recognized
`source_kind` strings (confirmed by reading `conservation.py:250-300` — `TOWN_SERVICE`/`TAX`/
`REPAIR_FEE`/`SERVICE_FEE`/`INFORMATION_PURCHASE` get one branch, `RECRUIT`/`CHEST` get another,
`HOME_STORAGE` a third); a gold-bearing Team-Up/Trade intent would need a new `source_kind` branch
added there, which is a `conservation.py` change with no ticket AC requiring it and `conservation.py`
is not in the ticket's Related Code Areas. None of the 4 ACs require gold/item exchange — only that
the 3 consumers route through the shared gate and that Paid-Information (whose gold path,
`source_kind="INFORMATION_PURCHASE"`, already has a `conservation.py:255` branch — confirmed, no
change needed there) gates its existing intent. Adding economic side effects for Team-Up/Trade beyond
the appraisal gate itself is out-of-scope scope creep under Decision 2's own YAGNI rationale, applied
consistently. Paid-Information is unaffected by this decision — its existing gold path is untouched,
only gated.

## Steps

### Step 1 — Add `ContractKind.TEAM_UP` and `ContractKind.PAID_INFORMATION`

**Files:** `src/core/strategic.py`

**Change:** In the `ContractKind` enum (`src/core/strategic.py:73-82`, read directly — currently
`RECRUITMENT`, `LOAN`, `PROTECTION`, `MERCHANT`, `POSITION_SWAP`), add two new members:
`TEAM_UP = "TEAM_UP"` and `PAID_INFORMATION = "PAID_INFORMATION"`. `ContractKind` is a plain
append-only `str, Enum` — no registry/migration mechanism gates it (unlike `layer`/`tags`). Confirmed
via `grep -rn "ContractKind\." src/` that no code does an exhaustive/closed-world match over all
`ContractKind` members (every consumer either checks one specific kind, e.g.
`src/systems/social_systems/party.py:31` checking `== ContractKind.RECRUITMENT`,
`src/engine/pipeline_phases/movement.py:386` checking `!= ContractKind.POSITION_SWAP`, or falls
through to a documented `None`/exclusion default, e.g. `contracts.py:136-150`'s
`get_project_mapping()`) — adding two members is additive and does not require touching those files.

**Other writers/readers of `ContractKind` enumerated (per Fact-Verification Requirement 2):**
- `src/systems/social_systems/contracts.py:136-150` (`get_project_mapping()`) — explicit 2-of-5
  match (`RECRUITMENT`/`LOAN`), returns `None` for everything else including the new members. No
  change required; this plan does not widen it (see Scope Guards).
- `src/ai/goals/social_contract_scorer.py:26-33` (`SocialContractGoalScorer.score()`) — skips any
  contract whose `get_project_mapping()` is `None`. New kinds are silently skipped, consistent with
  the exclusion above.
- `src/systems/social_systems/party.py:31` — checks `contract.kind == ContractKind.RECRUITMENT`
  specifically; new members never match, unaffected.
- `src/engine/pipeline_phases/movement.py:386` — checks `contract.kind != ContractKind.POSITION_SWAP`
  to skip non-swap contracts; new members are skipped exactly like `RECRUITMENT`/`LOAN`/`MERCHANT`
  already are, unaffected.
- `src/certification/scenarios.py:65,88` — hardcodes `ContractKind.PROTECTION` for certification
  fixtures; unaffected.
- `src/domains/cooperation/services.py:143-186` (`CooperationIntentBridge.map_decision`) — an
  existing, unrelated mechanism that maps `CooperationPosture.REQUEST_HELP`/`HIRE_SUPPORT` to a
  `ContractKind.RECRUITMENT` contract via `ContractService.create_recruitment_contract()`. This is
  **not** the Team-Up mechanism this ticket builds (see Scope Guards) and is unaffected by adding
  new `ContractKind` members.

**Also in this step:** extend the existing exclusion-parametrization test at
`tests/unit/ai/goals/test_social_contract_goal_scorer.py:124` (currently parametrized over
`ContractKind.PROTECTION, ContractKind.MERCHANT, ContractKind.POSITION_SWAP`) to also include
`ContractKind.TEAM_UP` and `ContractKind.PAID_INFORMATION`, asserting `get_project_mapping()` still
returns `None` and the scorer still spawns no project for them. This is
`test_new_contract_kinds_no_project_mapping_regression` from test_plan.md item 7, and it locks in
that adding the two new enum members did not accidentally widen tier-5 materialization.

**Do NOT touch:** `get_project_mapping()`'s logic itself, `ContractKind.PROTECTION`,
`ContractKind.MERCHANT`'s existing (non-)handling in `contracts.py`/`social_contract_scorer.py`.

**Verify:** `tests/unit/ai/goals/test_social_contract_goal_scorer.py::test_...` (the extended
parametrized exclusion test, per test_plan.md item 7).

---

### Step 2 — Add three new `ReasonCode` members

**Files:** `src/core/enums.py`

**Change:** In the `ReasonCode` enum's existing social-appraisal block
(`src/core/enums.py:147-156`, read directly — `TOTAL_DISTRUST`, `BETRAYAL_HISTORY`,
`LOYALTY_ACCEPTANCE`, `FAIR_COMPENSATION`, `HAGGLING_FOR_PAY`, `INSUFFICIENT_INCENTIVE`,
`USURY_REJECTION`, `DESPERATION_ACCEPTANCE`, `FRIENDLY_LOAN`, `UNNECESSARY_DEBT`, immediately before
the generic `UNKNOWN = "unknown"` at line 165), add three new members:
`TEAM_UP_ACCEPTED = "team_up_accepted"`, `TEAM_UP_DECLINED = "team_up_declined"`,
`INFORMATION_SALE_ACCEPTED = "information_sale_accepted"`. Trade (`MERCHANT`) reuses the existing
`FAIR_COMPENSATION`/`HAGGLING_FOR_PAY`/`INSUFFICIENT_INCENTIVE` codes — a price negotiation is
semantically the same shape as recruitment's pay negotiation, so reuse is accurate, not a stretch.
Team-Up has no pay/utility dimension, so reusing `FAIR_COMPENSATION` for it would misrepresent the
decision driver (`ReasonCode` is itself a typed durable-meaning field per the project's Durable State
Rule — "do not store durable meaning in ... comments" implies the reverse is also true: don't force
an inaccurate existing code onto a new, differently-shaped decision either). Paid-Information's
kind-specific body (Step 3) only ever returns one outcome when reached (the prelude already handles
all rejection paths), so it gets one new code for clarity, not a matching decline code.

**Do NOT touch:** any existing `ReasonCode` member's string value (durable-state stability — reason
codes are read back from persisted contract/appraisal history in tests).

**Verify:** no standalone test required for the enum addition itself; exercised transitively by
Step 3's new appraisal tests (`test_trade_merchant_kind_appraisal`, `test_team_up_kind_appraisal`,
`test_paid_information_gated_on_shared_helper`), which assert on these exact reason codes.

---

### Step 3 — Generalize `appraise_contract()`'s dispatch and add three kind-specific appraisers

**Files:** `src/systems/social_systems/appraisal.py`

**Change:** In `appraise_contract()`'s kind-dispatch block (`appraisal.py:56-72`, read directly — the
`if RECRUITMENT / if LOAN / elif POSITION_SWAP / return CANCELLED, UNKNOWN, {}` chain), add three new
branches **before** the final fallthrough at line 72:

```python
elif contract.kind == ContractKind.MERCHANT:
    return SocialAppraisalSystem._appraise_trade(entity, contract, trust_score)

elif contract.kind == ContractKind.TEAM_UP:
    return SocialAppraisalSystem._appraise_team_up(entity, contract, trust_score)

elif contract.kind == ContractKind.PAID_INFORMATION:
    return SocialAppraisalSystem._appraise_paid_information(entity, contract, trust_score)
```

Do not touch lines 19-54 (trust computation + hard-cancel prelude) or the existing
`RECRUITMENT`/`LOAN`/`POSITION_SWAP` branches at all — every new kind flows through the identical,
unmodified prelude before reaching its kind-specific body. This is why SOC-001 (cites exact lines
47-54), SOC-008, and SOC-134 (cite the formula/threshold by name, not by line number — confirmed by
reading their current `v2_evidence` text) need no update in Step 7: nothing in the cited region moves.

Add three new `@staticmethod`s to `SocialAppraisalSystem`, placed after `_appraise_position_swap`
(currently ends at `appraisal.py:255`), each following `_appraise_recruitment`'s
hard-cancel-then-score shape (lines 74-142, the pattern to mirror per the ticket's own AC):

```python
@staticmethod
def _appraise_trade(
    entity: EntityState, contract: ContractState, trust_score: float
) -> Tuple[ContractStatus, ReasonCode, Dict[str, Any]]:
    """Terms schema: {"price": int, "item_value": int}. Mirrors _appraise_recruitment's
    utility-vs-risk-then-haggle shape, using price/item_value in place of pay/expected_pay."""
    price = contract.terms.get("price", 0)
    item_value = contract.terms.get("item_value", price)
    if item_value <= 0:
        return ContractStatus.CANCELLED, ReasonCode.INSUFFICIENT_INCENTIVE, {}
    utility = price / max(1, item_value)
    if utility < 0.5:
        return ContractStatus.CANCELLED, ReasonCode.INSUFFICIENT_INCENTIVE, {}
    score = (trust_score * 0.4) + (min(1.0, utility) * 0.6)
    if score >= 0.6:
        return ContractStatus.ACCEPTED, ReasonCode.FAIR_COMPENSATION, {}
    if score >= 0.4 and contract.negotiation_count < 2:
        counter_terms = dict(contract.terms)
        counter_terms["price"] = int(item_value)
        return ContractStatus.COUNTERED, ReasonCode.HAGGLING_FOR_PAY, counter_terms
    return ContractStatus.CANCELLED, ReasonCode.INSUFFICIENT_INCENTIVE, {}

@staticmethod
def _appraise_team_up(
    entity: EntityState, contract: ContractState, trust_score: float
) -> Tuple[ContractStatus, ReasonCode, Dict[str, Any]]:
    """No pay/utility dimension -- pure trust gate plus the same HIGH-risk/low-HP hard
    rejection _appraise_recruitment uses (lines 119-120)."""
    risk = contract.terms.get("risk_level", "NORMAL")
    hp_pct = entity.combat.hp / entity.combat.max_hp
    if risk == "HIGH" and hp_pct < 0.5:
        return ContractStatus.FAILED, ReasonCode.LOW_HP_RETREAT, {}
    if trust_score >= 0.6:
        return ContractStatus.ACCEPTED, ReasonCode.TEAM_UP_ACCEPTED, {}
    return ContractStatus.CANCELLED, ReasonCode.TEAM_UP_DECLINED, {}

@staticmethod
def _appraise_paid_information(
    entity: EntityState, contract: ContractState, trust_score: float
) -> Tuple[ContractStatus, ReasonCode, Dict[str, Any]]:
    """The shared prelude (trust<0.2, sentiment<-0.8, betrayal-history) already expresses
    the entire gate PaidInformationTransactionSystem.enforce() needs; reaching this method
    means the prelude already passed, so it always accepts."""
    return ContractStatus.ACCEPTED, ReasonCode.INFORMATION_SALE_ACCEPTED, {}
```

`entity.combat.hp`/`entity.combat.max_hp` and `entity.social.bonds`/`trust_history` field names are
confirmed by direct reads of `_appraise_recruitment` (`appraisal.py:116`) and the prelude
(`appraisal.py:32,44`) respectively — not inferred.

**Do NOT touch:** `_appraise_recruitment`, `_appraise_loan`, `_appraise_position_swap`,
`recalibrate_trust`, `update_familiarity`, `calculate_recruitment_cost`, `process_betrayal`,
`recalibrate_source_trust`, or `RecruitmentAppraiser.evaluate` (`appraisal.py:393-400`) — none of
these are in scope and none reference the new kinds.

**Verify:**
- `test_shared_gate_dispatches_by_kind` (test_plan.md item 1) — `tests/unit/social/test_appraisal_logic.py`.
- `test_shared_gate_no_fallthrough_for_gated_kinds` (test_plan.md item 2) — same file; assert
  `ReasonCode.UNKNOWN` is never returned for `RECRUITMENT`/`LOAN`/`POSITION_SWAP`/`MERCHANT`/
  `TEAM_UP`/`PAID_INFORMATION`.
- `test_trade_merchant_kind_appraisal` (test_plan.md item 3) — one accept, one hard-cancel (low
  trust, via the untouched prelude), one COUNTERED case.
- `test_team_up_kind_appraisal` (test_plan.md item 4) — one accept (trust >= 0.6), one decline
  (trust < 0.6), one FAILED (HIGH risk + low HP).
- Full existing `tests/unit/social/test_appraisal_logic.py` and `tests/unit/social/test_recruitment.py`
  suites must still pass unchanged (RECRUITMENT/LOAN/POSITION_SWAP outcome stability, per test_plan.md
  Anti-Drift Test Guards).

---

### Step 4 — Route Team-Up through the shared helper: `execute_team_up()`

**Files:** `src/engine/domain/core_actions.py`, `src/engine/domain/action_router.py`

**Change:** Add `CoreActions.execute_team_up()`, structurally mirroring `execute_recruit()`
(`core_actions.py:55-144`, read in full):
1. Resolve `target` from `neighbor_view`/`context.entities` exactly as `execute_recruit()` does
   (lines 63-78) — same `TARGET_NOT_FOUND` failure shape on miss.
2. Build a `temp_contract = ContractState(id="temp_eval", kind=ContractKind.TEAM_UP,
   source_id=entity.id, target_id=target.id, terms={"risk_level": payload.get("risk_level",
   "NORMAL")}, status=ContractStatus.OFFERED, created_tick=current_tick)` and call
   `SocialAppraisalSystem.appraise_contract(target, temp_contract, context)` (mirrors
   `core_actions.py:84-94`).
3. On `ACCEPTED`: build a real `ContractState(kind=ContractKind.TEAM_UP, status=ContractStatus.ACTIVE,
   ...)` and return
   `{entity.id: EntityUpdate(entity_id=entity.id, readiness_delta=-100.0,
   strategic=StrategicUpdate(contracts_add_or_update=[contract])),
   target_id: EntityUpdate(entity_id=target_id, social=SocialUpdate(last_offer_tick_set=current_tick),
   strategic=StrategicUpdate(contracts_add_or_update=[contract]))}`. Per **Design Decision 5**, no
   `ResourceTransferIntent` is emitted — the `StrategicUpdate` is attached directly via
   `EntityUpdate.strategic` (confirmed a real field, `src/core/updates.py:641`).
4. On anything else: mirror the rejection branch exactly (`core_actions.py:134-144`) —
   `rejection_increment`, `last_offer_tick_set`, `task=replace(entity.task, payload={**payload,
   "outcome": "FAILURE", "reason": status.value})`.

Register the action in `ActionRouter.execute_action()` (`action_router.py:44-47`, the `if action ==
"RECRUIT": return CoreActions.execute_recruit(...)` pattern): add
`if action == "TEAM_UP": return CoreActions.execute_team_up(entity, payload, current_tick,
neighbor_view, context)`.

**Other writers/readers enumerated:** `LegalityServiceV2.verify_readiness()`
(`action_router.py:36-37`) already gates every routed action on `entity.combat.readiness == 100.0`
before dispatch — `execute_team_up` inherits this for free, no change needed.
`LegalityServiceV2.get_region_for_position()`'s regional-suppression check
(`src/engine/legality.py:138`) only special-cases `["SABOTAGE", "RECRUIT", "THEFT"]` — `TEAM_UP` is
not added to that list (not requested by any AC; Team-Up is not a hostile action like the three
listed, so suppression-gating it the same way is not an obvious analog and is left for a future
ticket if needed — do not add it here).

**Do NOT touch:** `execute_recruit()` itself, `execute_allocate_ap`/`execute_train`/`execute_repair`/
`execute_interact`/`execute_survival`, `LegalityServiceV2.verify_readiness()`,
`src/core/conservation.py` (per Design Decision 5, no new `source_kind` branch needed since no
`ResourceTransferIntent` is emitted).

**Verify:** new `tests/unit/social/test_team_up.py` (mirroring `test_recruitment.py`'s pattern for
`execute_recruit`, per investigation's own suggested precedent) — asserts `execute_team_up()`
produces `ACTIVE` `ContractState`s for both parties on a high-trust bond, and the rejection
bookkeeping on a low-trust bond. This is additive to test_plan.md item 4, using its own stated
fallback location (`tests/unit/social/test_team_up.py`, "if plan.md gives Team-Up its own
action-handler module").

---

### Step 5 — Route Trade through the shared helper: `execute_trade()`

**Files:** `src/engine/domain/core_actions.py`, `src/engine/domain/action_router.py`

**Change:** Add `CoreActions.execute_trade()`, same structural mirror as Step 4 but with
`kind=ContractKind.MERCHANT` and `terms={"price": payload.get("price", 0), "item_value":
payload.get("item_value", payload.get("price", 0))}`. On `ACCEPTED`, attach the `ContractState` via
`EntityUpdate.strategic` for both parties exactly as Step 4 (no `ResourceTransferIntent`, per Design
Decision 5). On `COUNTERED`, the caller (not built here — out of scope, no AC requires an automatic
re-offer loop) receives the countered `terms` in the appraisal result; this handler only needs to
surface `COUNTERED` as a non-`ACCEPTED` outcome via the same rejection-bookkeeping branch Step 4 uses
(haggling re-offer flow is future work, not required by any AC). Register `if action == "TRADE":
return CoreActions.execute_trade(entity, payload, current_tick, neighbor_view, context)` in
`action_router.py`, next to Step 4's registration.

**Other writers/readers enumerated:** same as Step 4 (`LegalityServiceV2.verify_readiness()`
inherited for free; regional-suppression list not extended — Trade is not analogous to
SABOTAGE/RECRUIT/THEFT). `InformationProviderArchetype.MERCHANT`
(`src/domains/information/providers.py:31`, confirmed a distinct enum on a distinct class, same
string value, no code-level relationship) must not be imported or compared against
`ContractKind.MERCHANT` anywhere in this handler — the test in Step 5's Verify includes an explicit
non-conflation assertion (test_plan.md's dedicated Anti-Drift Test Guard).

**Do NOT touch:** `execute_recruit()`, `execute_team_up()` (Step 4), `src/domains/information/`
(archetype enum untouched), `src/core/conservation.py`.

**Verify:** new `tests/unit/social/test_trade.py` (same rationale as Step 4) plus the
`ContractKind.MERCHANT` vs `InformationProviderArchetype.MERCHANT` non-conflation guard test named in
test_plan.md's Anti-Drift Test Guards section.

---

### Step 6 — Gate `PaidInformationTransactionSystem.enforce()` on the shared helper

**Files:** `src/engine/pipeline_phases/paid_information.py`

**Change:** In `enforce()` (`paid_information.py:74-183`, read in full), immediately after the
provider is resolved (`provider_record`/`provider_id`/`reliability` computed at lines 111-122) and
before building the `intent`/`lead` (lines 137-158), synthesize a transient contract and gate on it,
mirroring `execute_recruit()`'s `temp_contract` pattern (`core_actions.py:85-93`):

```python
from src.core.strategic import ContractState, ContractKind, ContractStatus
from src.systems.social_systems.appraisal import SocialAppraisalSystem

temp_contract = ContractState(
    id=f"temp_info_gate_{entity.id}_{provider_id}",
    kind=ContractKind.PAID_INFORMATION,
    source_id=provider_id,
    target_id=entity.id,
    terms={},
    status=ContractStatus.OFFERED,
    created_tick=state.tick,
)
gate_status, _gate_reason, _gate_terms = SocialAppraisalSystem.appraise_contract(
    entity, temp_contract, state
)
if gate_status != ContractStatus.ACCEPTED:
    continue
```

`entity` here is the seeker (the function's outer loop variable, `state.entities` sorted by id —
confirmed the loop var name at `paid_information.py:92`); `source_id=provider_id` puts the provider
in the `contract.source_id` slot the prelude reads (`appraisal.py:30-32`: `bond =
entity.social.bonds.get(source_id)`) — meaning the gate checks the **seeker's** trust/bond toward the
provider, matching test_plan.md item 5's stated scenario ("seeker's `bond.sentiment < -0.8` toward
the provider ... suppresses the intent"). On gate failure, `continue` to the next seeker in the outer
loop — no fallback to a different provider (the existing single-deterministic-provider selection at
lines 111-116 is unchanged), no state mutation, no project removal: the seeker's `INFORMATION_SEEKING`
project stays `ACTIVE` and will be re-evaluated next tick (this is why no cleanup/durable write is
needed on the failure path — `enforce()` remains fully decision-only, unchanged from its current
"append or don't append to `entity_updates`" shape at line 180-183).

**Other writers to `AuthoritativeState.information_providers`/the `entity_updates` dict enumerated:**
`enforce()` is the sole writer of `entity_updates[entity.id].resource_transfers` for
`INFORMATION_PURCHASE`-kind intents (confirmed by reading the full file — no other function in this
module or a sibling pipeline phase constructs an `INFORMATION_PURCHASE` intent). The `existing_upd =
entity_updates.get(entity.id, EntityUpdate(entity_id=entity.id))` read-modify-write at lines 160-166
already assumes a prior phase in the same tick may have populated `entity_updates[entity.id]` —
unchanged by this gate, since the gate check happens strictly before that block and either lets
execution reach it unchanged or skips the entity entirely via `continue`. `src/core/conservation.py`
(the downstream resolver) already has a branch for `source_kind == "INFORMATION_PURCHASE"`
(`conservation.py:255`, confirmed by direct read) — unaffected, since this step does not change the
intent's shape, only whether it is constructed at all.

**Do NOT touch:** the provider-selection logic (lines 92, 109-116, both `sorted(...)` calls — the
Anti-Drift Hazard on determinism), the `_transaction_cost`/`_lead_certainty_for_reliability` helper
functions, the `LeadState`/`StrategicUpdate` construction shape, or `conservation.py`.

**Verify:**
- `test_paid_information_gated_on_shared_helper` (test_plan.md item 5) — gate-passing bond emits the
  intent exactly as before; gate-failing bond (`sentiment < -0.8` or `trust_score < 0.2`) suppresses
  it entirely.
- `test_paid_information_enforce_still_decision_only` (test_plan.md item 6) — confirms `enforce()`
  still returns a `StateUpdate`/intent-only result, no direct `AuthoritativeState` mutation, now that
  the gate check is added.
- Existing `tests/unit/cognition/test_information_seeking.py::TestPaidInformationTransaction` and
  `tests/integration/scenarios/test_information_seeking_wiring.py` must still pass; per test_plan.md,
  if any existing fixture's seeker/provider bond does not gate-pass by default, that fixture must be
  updated to represent a gate-passing scenario (default `SocialBond`/`trust_history` absence yields
  `trust_score = 0.5` via the prelude's blended fallback, `appraisal.py:43-45` — above the 0.2
  hard-cancel threshold — so a fixture with no bond configured passes the gate by default; only a
  fixture that deliberately configures a hostile bond would need updating, and none of the existing
  `TestPaidInformationTransaction` tests configure `entity.social.bonds`/`trust_history` toward the
  provider, confirmed by the test file's fixture setup pattern referenced in test_plan.md).

---

### Step 7 — Update `docs/parity_ledger/social_narrative.yaml`

**Files:** `docs/parity_ledger/social_narrative.yaml` (via `tools/parity_ledger_writer.py`'s
`write_entry()` only — never a raw ad-hoc `Edit`)

**Change:** `write_entry(shard_filename, entry, ...)` (`tools/parity_ledger_writer.py:88-117`, read in
full) validates one entry against `validate_entry()` then **upserts it by `id`** into the shard,
rewriting the whole YAML file's bytes and rebuilding the derived SQLite index in-process — it is not
a bulk multi-entry API, so call it once per entry id touched:

1. **Amend SOC-204** ("Contract appraisal uses trust/private bond") — its text describes the shared
   prelude, which now genuinely covers 6 kinds instead of effectively 1 (RECRUITMENT was the only
   kind whose appraisal was exercised by a real test before this ticket). Update `v2_evidence` to
   state the prelude at `appraisal.py:19-54` is shared across `RECRUITMENT`/`LOAN`/`POSITION_SWAP`/
   `MERCHANT`/`TEAM_UP`/`PAID_INFORMATION` dispatch (`appraisal.py:56-`, post-Step-3 line numbers).
   Set `test_path` to a real value (currently `null` despite `priority: P0` — this already violates
   `validate_entry()`'s own rule that P0 requires non-null `test_path`, confirmed by reading
   `parity_ledger_writer.py:82-85`; this ticket's change is the first opportunity to fix it) —
   e.g. `tests/unit/social/test_appraisal_logic.py::test_shared_gate_no_fallthrough_for_gated_kinds`.
2. **Amend SOC-207** ("Contract appraisal uses prior trauma/betrayal") — same rationale: this is the
   betrayal-history hard-cancel at `appraisal.py:51-54`, part of the shared prelude, now exercised
   for all 6 kinds. Same `test_path` fix required (currently `null` + P0, same pre-existing schema
   violation).
3. **Amend SOC-217** ("Social updates are authoritative updates, not direct mutation during
   appraisal") — add that `PaidInformationTransactionSystem.enforce()`'s new gate check (Step 6) also
   remains decision-only. Set `test_path` to
   `tests/unit/cognition/test_information_seeking.py::test_paid_information_enforce_still_decision_only`.
4. **Add three new entries** (next available ids, confirmed max existing id is `SOC-248` via
   `grep -oE "^- id: SOC-[0-9]+" docs/parity_ledger/social_narrative.yaml | sort -n | tail -1`):
   - `SOC-249`: "Trade (MERCHANT) contract appraisal is gated through the shared trust/hard-cancel
     threshold formula." `priority: P0`, `test_path`:
     `tests/unit/social/test_appraisal_logic.py::test_trade_merchant_kind_appraisal`.
   - `SOC-250`: "Team-Up (TEAM_UP) contract appraisal is gated through the shared trust/hard-cancel
     threshold formula." `priority: P0`, `test_path`: `tests/unit/social/test_team_up.py`.
   - `SOC-251`: "PaidInformationTransactionSystem.enforce() gates ResourceTransferIntent emission on
     the shared appraisal helper's outcome." `priority: P0`, `test_path`:
     `tests/unit/cognition/test_information_seeking.py::test_paid_information_gated_on_shared_helper`.

**Do NOT touch:** SOC-001, SOC-002, SOC-008, SOC-134 (no update needed — their cited evidence, lines
47-54 and the formula text, is untouched by Step 3, confirmed above). SOC-141, SOC-199-203, SOC-205,
SOC-206, SOC-208-216, SOC-218, SOC-244 (not about the shared prelude/dispatch specifically — SOC-205
"greed or reward preference" and SOC-206 "capability/role fit" describe `_appraise_recruitment`'s own
trait logic, lines 102-114, which this plan does not touch; SOC-215/216 describe post-acceptance
effects, not the appraisal gate itself; SOC-141's pre-existing `test_path: null` gap is a separate,
already-flagged issue, not this ticket's to fix). `combat_movement.yaml`, `strategic_cognition.yaml`,
`town_resource.yaml`, `world_dynamics.yaml`, `infrastructure.yaml` — no overlap identified.

**Verify:** each `write_entry()` call returns `{"status": "ok", ...}` (raises `EntryValidationError`
on schema violation, per `parity_ledger_writer.py:64-86`) and the in-process index rebuild succeeds
(`build_report` in the return value). Per `.claude/agents/parity-updater.md`'s stated convention, also
run `python3 tools/parity_index.py build` as a second, visible Bash call so the retro metric
(`tools/agent-monitoring/generate_retro.py`'s `_is_parity_index_build_call`) picks it up.

---

### Step 8 — Update `docs/simulation/social_systems_contract.md`

**Files:** `docs/simulation/social_systems_contract.md`

**Change:** Extend the "Contract kinds" table (`social_systems_contract.md:39-43`, currently listing
special logic only for RECRUITMENT/LOAN/POSITION_SWAP) with rows for `MERCHANT`, `TEAM_UP`, and
`PAID_INFORMATION`, describing each one's appraisal shape (per Step 3's concrete bodies). Extend the
"Breach conditions" table (`social_systems_contract.md:97-106`, confirmed by direct read to be a
markdown table only — `grep -rn -i breach src/systems/social_systems/contracts.py` returns zero code
hits, so "breach conditions" is doc-only guidance today, not an enforced mechanism for any existing
kind either) with an explicit note that MERCHANT/TEAM_UP/PAID_INFORMATION have no breach-transition
code path yet (honest parity — do not imply enforcement that doesn't exist). Follow the doc's own
checklist at line 191 ("add to `ContractKind` enum [Step 1], implement an appraisal method in
`SocialAppraisalSystem` [Step 3], add breach conditions in `contracts.py` [explicitly deferred, see
Scope Guards], add tests [Steps 3-6]").

**Do NOT touch:** `docs/mechanics/04_strategic_cognition.md` (per investigation, Team-Up is scoped as
appraisal-gate-only, not tier-5 `GoalRegistry` materialization — no new tier-5-candidate row is
needed since `get_project_mapping()` is not widened, Step 1's Scope Guard); `docs/engine/
authoritative_pipeline.md` (37-phase sequence/ordering unchanged — Step 6 changes *when* an intent is
emitted, not the pipeline shape); `docs/mechanics/01_entity_anatomy.md`.

**Verify:** no automated test — doc-only change; `make knowledge-index-update` must be run at ticket
close per CLAUDE.md's "After Work" rule since files under `docs/` changed.

## Scope Guards

- Do not widen `ContractService.get_project_mapping()` (`contracts.py:136-150`) to include `MERCHANT`/
  `TEAM_UP`/`PAID_INFORMATION` — no AC requires tier-5 project materialization for these kinds; Step
  1's new test locks in that they keep returning `None`.
- Do not modify the shared trust-score prelude's hard-cancel thresholds (0.2 `TOTAL_DISTRUST`, 0.4
  `BETRAYAL_HISTORY`, -0.8 sentiment) at `appraisal.py:19-54` — covered by P0 parity entries SOC-001/
  SOC-008/SOC-134 with real passing tests; any numeric drift is a parity break, not a refactor.
- Do not conflate `InformationProviderArchetype.MERCHANT` (`src/domains/information/providers.py:31`)
  with `ContractKind.MERCHANT` — same string value, unrelated enums on unrelated classes.
- Do not add a `source_kind` branch to `src/core/conservation.py` — per Design Decision 5, Team-Up and
  Trade emit no `ResourceTransferIntent`; Paid-Information's existing `INFORMATION_PURCHASE` branch
  (`conservation.py:255`) is untouched.
- Do not route Team-Up through `src/domains/cooperation/services.py`'s
  `CooperationIntentBridge.map_decision()` (`REQUEST_HELP`/`HIRE_SUPPORT` postures) — that is existing,
  unrelated cooperation-posture machinery that already produces `ContractKind.RECRUITMENT` contracts;
  it must not be merged with or repurposed for the new `ContractKind.TEAM_UP` mechanism.
- Do not change `PartyCompositionScorer`/`FORM_PARTY`'s existing trust-bonds *scoring* term
  (`party_composition.py:112-140`) — Team-Up's *gating* mechanism is a separate concern; the full
  `tests/unit/social/test_party_composition.py` suite must pass unmodified.
- Do not add `"TEAM_UP"`/`"TRADE"` to `LegalityServiceV2.check_action_legality()`'s regional-suppression
  list (`legality.py:138`, currently `["SABOTAGE", "RECRUIT", "THEFT"]`) — not requested by any AC.
- No M6 Conversation-adjacent (ideas 39/40) consumer code, and no idea-25 separate trust ledger — both
  explicitly Out of Scope on the ticket.
- Do not implement automatic haggling re-offer loops for Trade's `COUNTERED` outcome — surfacing the
  countered terms in the appraisal result is sufficient; a re-offer action handler is future work.

## Dependency Map

- Step 1 and Step 2 are independent of each other; both are prerequisites for Step 3.
- Step 3 depends on Steps 1 and 2 (needs the new `ContractKind`/`ReasonCode` members to exist).
- Step 4 and Step 5 both depend on Step 3; they are independent of each other (different handler
  methods, same two files — implement sequentially to avoid edit conflicts, but neither blocks the
  other logically).
- Step 6 depends on Step 3 only (does not depend on Steps 4/5).
- Step 7 depends on Steps 3, 4, 5, 6 (needs their real `test_path` values to satisfy `validate_entry()`'s
  P0-requires-`test_path` rule).
- Step 8 depends on Steps 1, 3, 4, 5, 6 (describes the final shape of all of them).

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| The shared threshold-gate helper accepts a `ContractKind` and returns `(ContractStatus, ReasonCode, terms)` using the existing bond.sentiment-priority-else-trust_history formula | Step 3 | `test_shared_gate_dispatches_by_kind` |
| Team-Up/Trade/Paid-Information each route through the shared helper, mirroring `_appraise_recruitment`'s existing hard-cancel pattern | Steps 3, 4, 5, 6 | `test_team_up_kind_appraisal`, `test_trade_merchant_kind_appraisal`, `test_paid_information_gated_on_shared_helper`, plus `tests/unit/social/test_team_up.py`/`test_trade.py` |
| No fallthrough to default CANCELLED/UNKNOWN for any of the 3 consumers | Step 3 | `test_shared_gate_no_fallthrough_for_gated_kinds` |
| `PaidInformationTransactionSystem.enforce()` gates its `ResourceTransferIntent` on the shared helper's outcome | Step 6 | `test_paid_information_gated_on_shared_helper`, `test_paid_information_enforce_still_decision_only` |

## Anti-Drift Notes

- **Decision 2's "structural genericity" is satisfied by the existing if/elif chain** — investigation
  raised a dict-based dispatch-table rewrite as one option for "anticipating M6," but that is not
  required: a future M6 `ContractKind` branch is exactly as easy to add to an if/elif chain (one more
  `elif`) as to a dict (one more key). Do not rewrite the dispatch mechanism speculatively; that would
  be unrequested abstraction work Decision 2 explicitly warns against.
- **`appraisal.py:19-54` (the prelude) must not move or change** — this is what keeps SOC-001/SOC-008/
  SOC-134 accurate without any edit in Step 7. If an implementer feels tempted to "clean up" the
  prelude while adding the new branches, that is out of scope and risks a real parity break.
- **`PaidInformationTransactionSystem.enforce()`'s determinism must be preserved** — the two existing
  `sorted(...)` calls (lines 92, 112) are unchanged by Step 6; the new gate check does not introduce
  any dict-iteration-order-dependent selection, and does not add a fallback-to-next-provider retry
  (a single deterministic provider is still selected before the gate is checked).
- **Two pre-existing schema violations in `social_narrative.yaml`** (SOC-204, SOC-207: `priority: P0`
  + `status: verified` + `test_path: null`, which already contradicts `validate_entry()`'s own P0
  rule) are fixed as a side effect of Step 7's amendment — this is a welcome correction, not a
  new bug introduced by this ticket, but the implementer should not be surprised if
  `write_entry()` behaves as if these entries were previously invalid; they were.
- **`CooperationIntentBridge`** (`src/domains/cooperation/services.py:135-186`) looks
  superficially like a "team up" mechanism (`REQUEST_HELP`/`HIRE_SUPPORT` postures) but is not in the
  ticket's Related Code Areas and uses `ContractKind.RECRUITMENT`, not a Team-Up-specific kind — see
  Scope Guards. Do not "consolidate" it with the new `execute_team_up()` handler.

## Unresolved Questions

None. All four investigation-flagged decisions were pre-resolved by the orchestrator (Decisions 1-4
above) and are non-negotiable. The one additional implementation-shape choice this plan had to make
(whether Team-Up/Trade acceptance emits a gold-bearing `ResourceTransferIntent`) is resolved as
Design Decision 5, grounded in a direct read of `conservation.py`'s existing `source_kind` allowlist
and the absence of any AC requiring economic side effects — not a coin-flip fork requiring human
input.

## Deviations

Steps 1-6 (the `src/` code) were implemented exactly as specified in this plan — no logic
deviation. Two sequencing-only deviations from this plan's own step ordering, both directed by the
orchestrator for this specific pipeline run (not a scope cut):

- **Step 7 (`docs/parity_ledger/social_narrative.yaml` update)** was deliberately deferred to this
  pipeline's own later, dedicated Parity phase rather than executed inline during Implement — the
  Implement phase was explicitly instructed not to touch the parity ledger to avoid two different
  agents racing on the same YAML file. The Parity phase will use `tools/parity_ledger_writer.py`'s
  `write_entry()`/full-shard-rewrite convention as this plan's Step 7 already specifies; no change
  to Step 7's own content/entry-id plan.
- **Step 8 (`docs/simulation/social_systems_contract.md` update)** was deliberately deferred to
  this pipeline's own dedicated Document-Update phase, which runs immediately after Implement, for
  the same reason — Implement was scoped purely to `src/` code changes (Steps 1-6).

All new test file locations, kind-specific formulas (Trade's price/item_value utility, Team-Up's
pure trust gate, Paid-Information's always-accept-once-prelude-passes body), and the
`EntityUpdate.strategic`-only (no `ResourceTransferIntent`) acceptance shape for Team-Up/Trade
match this plan's Steps 3-6 verbatim.
