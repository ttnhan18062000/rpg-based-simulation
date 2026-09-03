---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260902-MARRIAGE-PROPOSAL-CONTRACT
artifact_type: test_plan
tags: [lifecycle, social]
---

# Test Plan — TCK-20260902-MARRIAGE-PROPOSAL-CONTRACT

## Regression Surface

**Unit:**
- `tests/unit/social/test_appraisal_logic.py` — the shared prelude (`TOTAL_DISTRUST`/
  `BETRAYAL_HISTORY`), the no-fallthrough parametrization over all `ContractKind` members, and the
  `TEACH` boundary-value test (`0.195` trust score, not exactly `0.2` — see Prior Work in
  investigation.md) must all keep passing unmodified except for the new `MARRIAGE`-kind entries
  this ticket adds to the existing parametrizations.
- `tests/unit/social/test_teach.py` — the direct TEACH precedent; must stay green byte-for-byte,
  untouched by this ticket.
- `tests/unit/social/test_team_up.py` — sibling two-party contract-kind precedent; untouched.
- `tests/unit/ai/goals/test_social_contract_goal_scorer.py` — the `get_project_mapping()`
  tier-5-exclusion parametrization (currently `PROTECTION, MERCHANT, POSITION_SWAP, TEAM_UP,
  PAID_INFORMATION, TEACH`); must keep passing for all existing kinds, plus the new `MARRIAGE`
  entry this ticket adds.
- `tests/unit/social/test_groups.py` — trust pipeline / hard reject gates (SOC-001/008 surface).
- `tests/unit/resource/test_resource_v2_boundary.py::test_class_hall_train_refactor` — confirms no
  accidental cross-contamination between the `TRAIN`/`MARRIAGE` action-router branches.

**Integration:**
- `tests/integration/scenarios/test_phase7_social_cooperation_scenarios.py` — full contract
  lifecycle (offer → appraisal → accept/breach); must keep passing to confirm the shared appraisal
  pipeline is unaffected by the new `MARRIAGE` dispatch branch.

## New Tests Required

Per acceptance criteria (`tickets/inprogress/TCK-20260902-MARRIAGE-PROPOSAL-CONTRACT.md`):

- **`ContractKind.MARRIAGE` exists** (AC #1, enum presence)
  - Category: unit (implicit, exercised by every other new test below constructing
    `ContractState(kind=ContractKind.MARRIAGE, ...)`)
  - Verifies: the enum member exists and round-trips through `ContractState`/appraisal without
    raising.
  - Location: `tests/unit/social/test_appraisal_logic.py` (extend
    `test_shared_gate_no_fallthrough_for_gated_kinds`'s `kind_terms` dict with
    `ContractKind.MARRIAGE: {}`, mirroring the existing `TEACH` entry).

- **`test_marriage_dispatch_no_fallthrough`**
  - Category: unit
  - Verifies: `appraise_contract()` never falls through to `(CANCELLED, ReasonCode.UNKNOWN, {})`
    for `MARRIAGE` — the new `elif` branch is reachable (mirrors the existing
    `test_shared_gate_no_fallthrough_for_gated_kinds` extension above; same test, new
    parametrization entry, not a separate function).
  - Location: `tests/unit/social/test_appraisal_logic.py`

- **`test_marriage_refused_below_trust_hard_cancel_threshold`** (AC #2, literal wording)
  - Category: unit
  - Verifies: a proposal below the shared hard-cancel thresholds (`trust_score<0.2`,
    `betrayal_count>0 and trust_score<0.4`, or `bond.sentiment<-0.8`) is rejected with **no
    marriage-specific bypass** — asserts `ContractStatus.CANCELLED`/`ReasonCode.TOTAL_DISTRUST` (or
    `BETRAYAL_HISTORY`), mirroring `test_teach_refused_below_trust_hard_cancel_threshold`'s exact
    assertion shape (`updates[target_id].<marriage field> is None`/unset, no durable
    `MarriageState` written).
  - Location: `tests/unit/social/test_marriage.py` (new file, following `test_teach.py`'s
    structure/fixture style: `V2EntityBuilder`, `AuthoritativeState`,
    `SimulationDomainLogic.execute_action`/`ActionRouter.execute_action`).

- **`test_marriage_boundary_trust_score_matches_recruitment_and_team_up_and_teach_just_below_0_2`**
  - Category: unit (architecture/parity guard)
  - Verifies: a trust score just under the `0.2` hard-cancel threshold (e.g. `0.195`, per the
    documented correction from `TCK-20260831-TRUST-GATED-TEACHING`'s Deviations — a literal `0.2`
    does **not** trigger the gate under the strict `<` comparison) produces the same
    `CANCELLED`/`TOTAL_DISTRUST` outcome for `MARRIAGE` as it already does for
    `RECRUITMENT`/`TEAM_UP`/`TEACH` — proves no marriage-specific threshold drift was introduced.
  - Location: `tests/unit/social/test_appraisal_logic.py`

- **`test_marriage_proposal_builds_transient_contract_and_calls_real_appraise_contract`** (AC #3,
  first half)
  - Category: unit
  - Verifies: proposing marriage constructs a transient (non-persisted)
    `ContractState(kind=ContractKind.MARRIAGE, source_id=<proposer>, target_id=<target>,
    status=ContractStatus.OFFERED)` and routes it through the real
    `SocialAppraisalSystem.appraise_contract()` — not a bespoke inline threshold check.
  - Location: `tests/unit/social/test_marriage.py`

- **`test_marriage_accepted_writes_typed_marriagestate_on_both_parties`** (AC #3, second half)
  - Category: unit
  - Verifies: on `ACCEPTED`, a new typed durable `MarriageState`-equivalent record
    (`proposer_entity_id, target_entity_id, status, married_tick`) is written via a typed
    `EntityUpdate`/`StateUpdate` field on **both** the proposer's and the target's update — not
    just one side.
  - Location: `tests/unit/social/test_marriage.py`

- **`test_marriage_no_free_form_dict_carries_accepted_outcome`** (AC #4, literal assertion)
  - Category: unit (architecture guard)
  - Verifies: neither `ContractState.terms` nor any `EntityUpdate.task.payload["reason"]`-style
    free-form field carries the accepted-marriage outcome — the outcome is reachable only through
    the new typed field(s) added in this ticket. Mirrors the Durable State Rule check pattern
    (typed field presence, free-form field absence).
  - Location: `tests/unit/social/test_marriage.py`

- **`test_marriage_no_duration_or_aging_threshold_introduced`** (AC #5)
  - Category: architecture guard
  - Verifies: the new `MarriageState`-equivalent record has no age/duration/expiry-style numeric
    field beyond `married_tick` (a plain tick timestamp) — a lightweight introspection test over the
    record's dataclass fields, asserting the field set matches exactly `{proposer_entity_id,
    target_entity_id, status, married_tick}` (plus an `id` if the implementation needs one for
    dict-keying, consistent with `ContractState.id`).
  - Location: `tests/unit/social/test_marriage.py`

- **`test_marriage_target_appraises_proposer_not_vice_versa`**
  - Category: unit
  - Verifies: the gate reads from the **target's** `social.bonds`/`trust_history` toward the
    proposer (not the proposer's toward the target) — mirrors
    `test_teach_target_appraises_teacher_trust_not_vice_versa`'s two-way assertion (give the
    proposer a hostile bond toward the target but a trusting bond from target toward proposer;
    assert success; then invert and assert failure).
  - Location: `tests/unit/social/test_marriage.py`

- **`test_marriage_action_requires_proposer_and_target`**
  - Category: unit
  - Verifies: `TARGET_NOT_FOUND` navigation failure when the target cannot be resolved via
    `neighbor_view`/`context.entities`, mirroring `test_teach_action_requires_teacher_and_target`.
  - Location: `tests/unit/social/test_marriage.py`

- **`test_marriage_action_routes_through_action_router`**
  - Category: unit (architecture guard)
  - Verifies: `ActionRouter.execute_action()` correctly dispatches the new marriage-proposal action
    string to the new `CoreActions` handler, catching a router-wiring regression specifically
    (mirrors `test_train_action_still_routes_through_action_router`).
  - Location: `tests/unit/social/test_marriage.py`

- **`test_marriage_kind_excluded_from_project_materialization`**
  - Category: unit (architecture/parity guard)
  - Verifies: `ContractService.get_project_mapping()` returns `None` for `ContractKind.MARRIAGE`,
    locking in the Out of Scope guard against widening tier-5 project materialization (no
    production code change required — already true by construction; this only adds the regression
    lock, mirroring `TCK-20260831-TRUST-GATED-TEACHING`'s Step 10).
  - Location: extend the existing parametrized list in
    `tests/unit/ai/goals/test_social_contract_goal_scorer.py` (currently `PROTECTION, MERCHANT,
    POSITION_SWAP, TEAM_UP, PAID_INFORMATION, TEACH` — add `MARRIAGE`).

**Deferred to Plan, not pre-committed here** (per investigation.md's Risks and Open Questions —
these depend on decisions not yet made): a bigamy/duplicate-marriage-prevention test, and an
eligibility-precondition-helper test (alive/adult/same-race/not-already-married). Do not write
these speculatively; add them only if Plan explicitly scopes the underlying behavior in.

## Scoped Pytest Commands

```
.venv/bin/python3 -m pytest tests/unit/social/ tests/unit/ai/goals/test_social_contract_goal_scorer.py -q
```

Broader regression sweep (matches the TEACH precedent's own verification breadth, since this
ticket dispatches through the same shared appraisal pipeline and action-router surface):

```
.venv/bin/python3 -m pytest tests/unit/social/ tests/unit/ai/goals/ tests/unit/resource/test_resource_v2_boundary.py tests/integration/scenarios/test_phase7_social_cooperation_scenarios.py -q
```

Never: `pytest tests/` (unscoped).

## Anti-Drift Test Guards

- `test_shared_gate_no_fallthrough_for_gated_kinds`'s existing per-kind assertions (all kinds other
  than `MARRIAGE`) must remain unmodified and green — proves the shared prelude and every other
  kind's dispatch branch is untouched.
- `test_teach_*` suite in `test_teach.py` must remain green, unmodified — proves no cross-
  contamination between the `TEACH` and `MARRIAGE` two-party handlers sharing the same
  `core_actions.py`/`action_router.py` files.
- The extended `get_project_mapping()` exclusion parametrization in
  `test_social_contract_goal_scorer.py` catches any accidental widening of tier-5 project
  materialization to `MARRIAGE` — this is the concrete, machine-checked form of the ticket's Out of
  Scope line about `ProposalState`/project-spawning creep.
- `test_marriage_no_duration_or_aging_threshold_introduced`'s exact-field-set assertion catches any
  accidental introduction of a fantasy-year/duration numeric field on the new record — the concrete,
  machine-checked form of AC #5.
- `test_marriage_no_free_form_dict_carries_accepted_outcome` catches any regression toward stuffing
  the accepted outcome into `ContractState.terms` or a `reason` string instead of a typed field —
  the concrete, machine-checked form of AC #4 and the Durable State Rule.
- Full `tests/unit/social/` and `tests/unit/ai/goals/` sweeps (not just the new/touched files) catch
  any unintended change to the shared `appraisal.py`/`contracts.py` surface that a narrower run
  would miss, consistent with the TEACH precedent's own verification breadth (44+256 tests run).
