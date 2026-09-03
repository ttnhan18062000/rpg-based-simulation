---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260902-MARRIAGE-PROPOSAL-CONTRACT
artifact_type: investigation
tags: [lifecycle, social]
---

# Investigation — TCK-20260902-MARRIAGE-PROPOSAL-CONTRACT

## Current Behavior

**`ContractKind` enum** (`src/core/strategic.py:73-86`): `RECRUITMENT`, `LOAN`, `PROTECTION`,
`MERCHANT`, `POSITION_SWAP`, `TEAM_UP`, `PAID_INFORMATION`, `TEACH`. No `MARRIAGE` member exists.
All members are `str, Enum`, uppercase value equal to name — `TEACH = "TEACH"` (line 86) is the most
recently added and the exact style to follow.

**`ContractState`** (`strategic.py:215-229`): `id, kind, source_id, target_id, terms: Dict[str, Any]
= {}, expiry_tick=-1, status: ContractStatus=OFFERED, created_tick=0, negotiation_count=0`. Frozen
dataclass, no `MARRIAGE`-specific fields — any marriage-only data must go in a *separate* typed
durable record, not `ContractState.terms` (Durable State Rule).

**`ContractStatus`** (`strategic.py:59-70`): `OFFERED, ACCEPTED, COUNTERED, ACTIVE, FULFILLED,
COMPLETED(=FULFILLED alias), FAILED, BETRAYED, EXPIRED, CANCELLED`. **There is no `REJECTED`
value.** Schema-33's `MarriageState.status` (`PROPOSED | ACCEPTED | REJECTED`) is therefore
necessarily a brand-new, separate enum from `ContractStatus` — the transient offer still uses
`ContractStatus` (`OFFERED`→ appraisal result), but the durable `MarriageState` record needs its
own status enum with different member names (`PROPOSED` not `OFFERED`, `REJECTED` not `CANCELLED`).

**`SocialAppraisalSystem.appraise_contract()`** (`src/systems/social_systems/appraisal.py:20-84`):
runs the shared trust-evaluation prelude (lines 29-54), then kind-dispatches via `if/elif` chain
(lines 57-84), falling through to `(CANCELLED, ReasonCode.UNKNOWN, {})` for any unhandled kind
(line 84). The shared hard-cancel prelude, confirmed by direct read:
- Line 48: `if trust_score < 0.2 or (bond and bond.sentiment < -0.8): return CANCELLED,
  TOTAL_DISTRUST, {}`
- Lines 52-54: `if entity.social.betrayal_count > 0: if trust_score < 0.4: return CANCELLED,
  BETRAYAL_HISTORY, {}`

This exactly matches the ticket's cited "lines 48-54" and is covered by P0 parity entries
`SOC-001`/`SOC-008`/`SOC-134`. The `TEACH` dispatch branch (`appraisal.py:81-82`) and
`_appraise_teach` (`appraisal.py:330-338`) are the direct precedent: once the prelude passes,
`_appraise_teach` returns `ACCEPTED, TEACH_ACCEPTED, {}` unconditionally — no utility/risk model.

**`CoreActions.execute_train()`** (`src/engine/domain/core_actions.py:327-398`) is the exact
transient-`ContractState`-then-appraise handler shape to follow: resolve target via
`neighbor_view`/`context.entities` (lines 341-355, byte-identical to
`execute_recruit`/`execute_team_up`/`execute_trade`), build `ContractState(id="temp_eval",
kind=ContractKind.TEACH, source_id=entity.id, target_id=target.id, terms={},
status=ContractStatus.OFFERED, created_tick=current_tick)` (lines 361-369), call
`SocialAppraisalSystem.appraise_contract(target, temp_contract, context)` — **target appraises
entity** (line 370) — then branch on `status` (lines 372-398): on `ACCEPTED`, build direct
`EntityUpdate.identity=IdentityUpdate(recipes_learned=[skill_id])` on the target's update (line
384); on any other status, the shared rejection shape
`EntityUpdate(readiness_delta=-50.0, task=replace(...))` / `EntityUpdate(social=SocialUpdate
(rejection_increment=...))` (lines 389-397) that `execute_team_up`/`execute_trade` also use.

**`ActionRouter.execute_action()`** (`src/engine/domain/action_router.py:20-59`): dispatches
`"TRAIN"` (line 58-59) to `CoreActions.execute_train(entity, payload, current_tick, neighbor_view,
context)`, passed through positionally after the readiness check (lines 37-44). No `"MARRIAGE"` /
`"PROPOSE_MARRIAGE"` action string exists yet — a new branch is required.

**No durable storage location for a `MarriageState`-equivalent record exists anywhere in
`EntityState` today** — confirmed by direct full reads of the three candidate components:
- `IdentityComponent` (`state.py:496-519`): `role, faction, known_recipes, craft_target,
  evolution_level, ..., life_stage, group_id, properties, ...` — no spouse/marriage field.
- `SocialComponent` (`src/core/models/social.py:31-57`): `trust_history, familiarity_history,
  debt_history, fear_history, grudge_history, bonds: Dict[int, SocialBond], nemesis_ids,
  place_attachment, betrayal_count, betrayal_records, public_reputation, ...` — no spouse/marriage
  field; `SocialBond` (lines 13-20) has no `role`-style extension point for "spouse" beyond the
  existing `RelationshipRole` (`NEUTRAL/FRIEND/RIVAL`, no `SPOUSE`).
- `StrategicComponent` (`strategic.py:382-416`): `blockers, leads, directives, projects, concerns,
  candidate_zones, hypotheses, source_trust, contracts: Dict[str, ContractState], turning_points,
  beliefs, committed_intentions, ...` — has the closest structural analog (`contracts` dict keyed
  by contract id) but no `marriages` dict.

`EntityUpdate` (`src/core/updates.py:664-699`) and `StrategicUpdate`
(`updates.py:502-608`)/`SocialUpdate` (`updates.py:286-323`)/`IdentityUpdate`
(`updates.py:223-276`) likewise have no field that could carry a typed `MarriageState` record
today — none of them has an `X_add_or_update`/`X_remove` pair for anything marriage-shaped. Adding
one is required work, not something to discover pre-existing.

Also notable: `AuthoritativeState.to_canonical_dict()`'s `"strategic"` sub-dict (`state.py:781-796`)
does **not** include `contracts` at all today, even though `contracts` is a real `StrategicComponent`
field — an existing, pre-ticket canonicalization gap for `ContractState`. Whatever component ends
up hosting `MarriageState` should be checked against this same gap at Plan/Implement time (do not
silently inherit it without a decision).

**`ContractService.get_project_mapping()`** (`src/systems/social_systems/contracts.py:138-152`)
returns `(ProjectKind, ObjectiveKind, prefix)` only for `RECRUITMENT`/`LOAN`; every other kind
(including the newly-added `TEACH`) falls through to `return None` by construction — no code
change is needed for `MARRIAGE` to stay excluded from tier-5 project materialization, matching the
ticket's Out of Scope line. This is already regression-locked for `TEACH` in
`tests/unit/ai/goals/test_social_contract_goal_scorer.py:130`; `MARRIAGE` needs the same lock.

**`ReasonCode`** (`src/core/enums.py:66-161`): `TEAM_UP_ACCEPTED/DECLINED` (157-158),
`TEACH_ACCEPTED/DECLINED` (160-161) exist. `TEACH_DECLINED` is defined but never actually returned
by `_appraise_teach` (which always accepts once the prelude passes) — the same will likely be true
for a `MARRIAGE_DECLINED`-style code if `_appraise_marriage()` follows the TEACH pattern exactly
(prelude-only gate, no additional kind-specific rejection branch). No `MARRIAGE_ACCEPTED`/
`MARRIAGE_DECLINED` (or similar) codes exist yet.

## Mechanics / Engine Constraints

- `docs/simulation/social_systems_contract.md` "Extension rules" (§ Extension rules, line 209):
  "To add a new contract kind: add to `ContractKind` enum, implement an appraisal method in
  `SocialAppraisalSystem`, add breach conditions in `contracts.py`, add tests." This ticket's scope
  maps directly onto steps 1-2 of that checklist; step 3 (breach conditions in `contracts.py`) is
  not addressed by any ticket Scope bullet or AC — flagged below as an open question.
- Shared trust/hard-cancel prelude thresholds (`0.2`, `-0.8`, `0.4`) are P0-parity-covered
  (`SOC-001`/`SOC-008`/`SOC-134`) and must not move numerically or structurally — CLAUDE.md's
  Authoritative Mechanics Rule + the ticket's own explicit Out of Scope line.
- CLAUDE.md's Durable State Rule: "Do not store durable meaning in `reason` strings, free-form
  `metadata`, comments, or temporary local variables" — directly governs AC #4 (no `reason`/`terms`
  free-form dict carries the accepted-marriage outcome); the accepted record must be a typed
  dataclass field reachable through `EntityUpdate`/`StateUpdate`, applied via the authoritative
  apply path only (CLAUDE.md Core Boundaries).
- CLAUDE.md Architecture Rule: "Shared world behavior should go through systems/registries, not
  scattered local hacks" — reinforces following the `_appraise_teach`/`execute_train` shape exactly
  rather than inventing a parallel mechanism.
- No Mechanics Bible chapter currently documents any propose/accept relationship law for idea 33 —
  confirmed by reading `docs/mechanics/04_strategic_cognition.md`'s full section list (§§1-7,
  through "7.3 Role-Affinity Adjustment"); the closest existing section is "§7 Party Composition &
  Formation Scoring," which documents a *scoring* function, not a contract/appraisal law, so a new
  numbered subsection (e.g. "§8") is the natural fit, not a rewrite of §7.

## Docs Requiring Update

- `docs/mechanics/04_strategic_cognition.md`: AC #7 explicitly requires a new Mechanics Bible
  entry documenting the propose/accept-relationship law for idea 33 — none currently exists;
  confirmed by reading the chapter's full section list (§§1-7).
- `docs/simulation/social_systems_contract.md`: add a `MARRIAGE` row to the "Contract kinds" table
  (§ Appraisal — `appraisal.py`), following the exact precedent of the `TEACH` row added by
  `TCK-20260831-TRUST-GATED-TEACHING` — required by that doc's own "Extension rules" checklist.
- `docs/parity_ledger/social_narrative.yaml`: add a new P0 entry describing the `MARRIAGE`
  contract-kind trust gate (mirroring `SOC-258`'s shape for `TEACH`) and, separately, the new
  `MarriageState` durable record's write path — no existing entry in this file covers `MARRIAGE`,
  `MarriageState`, or idea 33 (confirmed by grep across `docs/parity_ledger/*.yaml`; the only other
  hit was an unrelated `world_dynamics.yaml` match). Required per the Authoritative Mechanics Rule
  ("If logic changes, update ... the parity ledger entry in the same session") and because a P0
  entry requires a passing `test_path`.

The `docs/guidelines/intentional_divergences.md` doc (path:
`docs/guidelines/intentional_divergences.md`, under `docs/`) is not required to change for this
ticket: unlike `TCK-20260831-TRUST-GATED-TEACHING`'s DEV-007 (which recorded the *removal* of a
pre-existing, if non-enforcing, gold cost — a genuine behavior change from documented legacy
behavior), Marriage introduces no prior legacy mechanism to diverge from; it is wholly new. Add an
entry here only if Plan/Implement discovers a genuine legacy-behavior conflict, not preemptively.

The `docs/plans/rpg_design_roadmap/rpg_m3_family_species_epic.md` doc (path:
`docs/plans/rpg_design_roadmap/rpg_m3_family_species_epic.md`, under `docs/`) is not required to
change for this ticket: it is a scope-only epic-planning doc with no per-idea completion
checkboxes — its own "Acceptance Signal" section only checks that "all 5 ideas exist as child
tickets," which is already true (this ticket itself is that child ticket for idea 33), not that
each idea's implementation status is tracked inline in this file.

## Parity Ledger Overlap

- `SOC-001` (P0, verified) — "Private betrayal history can override public recruiter reputation,"
  `v2_evidence` cites `appraisal.py` lines 47-54 directly — the shared prelude this ticket must not
  touch. `test_path` exists and must keep passing unmodified.
- `SOC-008` (P0, verified) — "Recruitment evaluates trust, debt, greed, capability fit, and prior
  trauma" — covers the same prelude/appraisal machinery this ticket dispatches into.
- `SOC-134` (P0, verified) — "public_reputation... informs contract appraisal trust... below the
  trust threshold (0.2) and is rejected" — directly covers the same `0.2` threshold cited in AC #2.
- `SOC-258` (P0, verified) — the `TEACH` precedent's own entry; not directly overlapping
  `MARRIAGE`'s scope but the exact template to mirror for a new `MARRIAGE` entry (same shape:
  contract-kind trust gate description, `test_path` pointing at the new hard-cancel-refusal test).
- No existing entry covers `ContractKind.MARRIAGE`, `MarriageState`, or idea 33 — a **new P0
  entry** is required (per Docs Requiring Update above), since this is a trust-gated durable-state
  write path, matching `SOC-258`'s precedent priority.

## Prior Work

- `TCK-20260831-TRUST-GATED-TEACHING` (done) — the exact reusable precedent per this ticket's own
  Request Summary. Full `plan.md`/ticket read: 12 ordered steps (enum member → `ReasonCode` →
  `_appraise_teach` + dispatch → `execute_train()` rewrite → router pass-through → regression test
  update → orphan-verification → new dedicated test file → `test_appraisal_logic.py` extension →
  goal-scorer exclusion lock → docs → parity ledger). Its "Deviations" section is directly relevant:
  a literal `trust_score == 0.2` does **not** trigger the hard-cancel gate (strict `<` comparison),
  so any boundary-value test for `MARRIAGE` must use a value just under `0.2` (e.g. `0.195`), not
  exactly `0.2` — the same correction will apply here.
- `TCK-20260824-AFFECTION-CONTRACT-GATE` — cited by both this ticket and the TEACH plan as the
  originating precedent that established the "full `appraise_contract()` routing over an inline
  threshold copy" pattern (`TEAM_UP`/`MERCHANT` additions); not independently re-investigated in
  full here since TEACH's plan.md already synthesizes its relevant decision (Decision 2).
- `TCK-20260902-PERSONAL-DEPENDENTS-ROUTE-BIAS` (sibling, currently in
  `tickets/todos/m3-family-species/`, not yet started) — owns household/family/dependents durable
  state; this ticket's `MarriageState` must stay a bare propose/accept record with no
  dependents/family fields, per the explicit hard scope boundary in both tickets.
- `TCK-20260829-TEMPORAL-CALENDAR-AUTHORITY` — decision-record only, confirmed no migration code
  landed; fantasy-year aging/duration thresholds remain correctly out of scope.

## Risks and Open Questions

- **No durable storage location for `MarriageState` exists anywhere in `EntityState` today** (see
  Current Behavior). The most structurally consistent option, mirroring `StrategicComponent
  .contracts: Dict[str, ContractState]`, would be a new `StrategicComponent.marriages: Dict[str,
  MarriageState]` plus a corresponding `StrategicUpdate.marriages_add_or_update`/`marriages_remove`
  pair — but this is a genuine architecture decision, not something already settled by any doc or
  precedent read during this investigation. **This must be resolved explicitly at Plan time, not
  assumed.**
- **Bigamy/duplicate-marriage prevention is not covered by any AC.** None of the ticket's
  Acceptance Criteria requires checking whether either party is already in an ACCEPTED marriage
  before a new proposal can succeed. Schema-33's card implies a monogamous propose/accept model (no
  mention of multiple concurrent marriages) but does not state this as a hard rule either. **Flag
  for Plan**: either explicitly scope in a "not-already-married" precondition (consistent with the
  ticket's own Request Summary mention of a shared eligibility-precondition helper covering
  "not-already-X"), or explicitly document that it is deliberately out of scope for this ticket.
  Do not assume either answer.
- **The "proposal-lifecycle prerequisites" ambiguity the ticket itself flags is resolvable now,
  not blocking**: the Contracts offer/accept machinery (`ContractState`/`appraise_contract()`) is
  real, live, and directly reusable today — proven by the `TEACH`/`TEAM_UP`/`TRADE` precedents this
  investigation read in full. No separate `ProposalState` base class exists anywhere in `src/`
  (confirmed independently via the same grep pattern the ticket's own Assumptions section already
  ran: only unrelated similarly-named classes exist). Recommend Plan explicitly state: Marriage is
  unblocked today on the existing Contracts machinery, no new base-class infrastructure required —
  matching the direct-implementation choice `TCK-20260831-TRUST-GATED-TEACHING` made over a
  speculative shared base.
- **The "eligibility-precondition helper (alive/adult/same-race/not-already-X)" mentioned in the
  ticket's Request Summary is not listed as a Scope bullet or AC.** Building it is therefore not
  literally required by this ticket's own acceptance criteria as written. Flag for Plan: either
  explicitly scope it in (since "not-already-X" bears directly on the bigamy question above) or
  explicitly defer it, rather than silently building or silently skipping it.
- **`LifeStage`'s "adult" concept is orphaned today.** Per the prior M2-era investigation (schema-20
  in `docs/brainstorm/rpg_expected_schemas.html`, independently re-confirmed relevant here): no
  entity anywhere is ever constructed with `LifeStage.CHILD` or `LifeStage.ELDER` — every entity
  defaults to `ADULT` and stays there. Any "must be adult to marry" precondition, if built, would be
  a no-op today (always true) — worth noting so it is not mistaken for real enforcement if the
  eligibility helper is ever built.
- **`ContractStatus` has no `REJECTED` value.** `MarriageState`'s own status enum (schema-33:
  `PROPOSED | ACCEPTED | REJECTED`) must be a new, separate enum from `ContractStatus` — do not
  attempt to reuse `ContractStatus.CANCELLED` as a stand-in for `REJECTED` on the durable record (the
  transient `ContractState.status` can still legitimately resolve to `CANCELLED` per
  `appraise_contract()`'s existing return contract; only the *durable* `MarriageState.status` needs
  the new three-value enum).
- **Whether `_appraise_marriage()` needs any logic beyond the shared prelude is not fully settled
  by the ticket's own Scope wording**, even though it says "following the TEACH pattern exactly."
  Schema-33's card separately names an `eligibility_gate: float` field ("Minimum
  SocialBond.sentiment/familiarity required before a proposal can even be attempted") as "Reused as
  the gate; reads existing entity.social state" — this could be read as identical to the existing
  hard-cancel prelude (already reads `bond.sentiment`) or as an *additional* named threshold. Given
  AC #1's literal wording ("a test confirms a proposal below hard-cancel thresholds... is rejected
  with no marriage-specific bypass"), the evidence favors the TEACH-identical reading (prelude-only
  gate, no additional scoring) — but this should be stated as an explicit Plan decision, not left
  implicit.

## Anti-Drift Hazards

- **Do not modify the shared trust hard-cancel prelude** (`appraisal.py:29-54`) — P0 parity
  `SOC-001`/`SOC-008`/`SOC-134` depend on its exact thresholds and structure; copy the pattern into
  a new `_appraise_marriage()` method, never edit the prelude itself.
- **Do not widen `ContractService.get_project_mapping()`** for `MARRIAGE` — it already returns
  `None` for any kind other than `RECRUITMENT`/`LOAN` by construction; only add a regression test
  locking this in (mirroring `TCK-20260831-TRUST-GATED-TEACHING`'s Step 10), never a code change.
- **Do not let the accepted-marriage outcome leak into `ContractState.terms` or any `reason`
  string** — AC #4 is explicit and machine-checkable (a typed field, not a free-form dict entry).
- **Do not conflate `MarriageState` with household/family/dependents state** — that is
  `TCK-20260902-PERSONAL-DEPENDENTS-ROUTE-BIAS`'s scope (idea 31), a separate ticket; keep
  `MarriageState` to the four schema-33 fields (`proposer_entity_id, target_entity_id, status,
  married_tick`) plus whatever minimal fields the appraisal path itself needs, nothing more.
- **Do not introduce any shared generic `ProposalState` base class** across Marriage/Team-Up/Trade/
  Clan-entry — explicitly Out of Scope; the schema doc's "worth a single shared base" aspiration is
  not built anywhere and this ticket should not be the one to start it unless Plan explicitly
  decides otherwise.
- **Do not introduce any fantasy-year aging or lifecycle-duration numeric threshold** — blocked on
  the unmigrated `TCK-20260829-TEMPORAL-CALENDAR-AUTHORITY`; `married_tick` should record a tick
  timestamp only, with no derived-duration/expiry logic built on top of it.
- **Preserve the target-appraises-proposer direction exactly** (`appraise_contract(target,
  temp_contract, context)`, not the reverse) — every existing two-party handler
  (`execute_recruit`/`execute_team_up`/`execute_trade`/`execute_train`) uses this convention; a
  direction flip would silently invert who is being trust-gated.
- **Watch the `AuthoritativeState.to_canonical_dict()` gap**: `contracts` is not included in the
  `"strategic"` canonical sub-dict today (a pre-existing, pre-ticket gap). Whichever component ends
  up hosting `MarriageState` should have this addressed as an explicit Plan/Implement decision
  (include it in canonicalization, or knowingly inherit the same gap) rather than silently copying
  the omission without noticing it.
