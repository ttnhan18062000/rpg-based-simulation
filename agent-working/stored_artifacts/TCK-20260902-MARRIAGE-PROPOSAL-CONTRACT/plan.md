---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260902-MARRIAGE-PROPOSAL-CONTRACT
artifact_type: plan
tags: [lifecycle, social]
---

# Implementation Plan — TCK-20260902-MARRIAGE-PROPOSAL-CONTRACT

## Summary

Add `ContractKind.MARRIAGE` following the `TEACH` precedent exactly: a new enum member, a new
`_appraise_marriage()` static method that is prelude-only (no additional scoring), a new
`execute_propose_marriage()` handler in `CoreActions` built on the same transient-`ContractState`
shape as `execute_train()`, and a new `"PROPOSE_MARRIAGE"` branch in `ActionRouter`. The one genuine
new-infrastructure piece is durable storage: no `MarriageState`-equivalent field exists anywhere in
`EntityState` today, so this plan adds `StrategicComponent.marriages: Dict[str, MarriageState]` plus
a matching `StrategicUpdate.marriages_add_or_update` / `marriages_remove` pair, threaded through the
same apply/merge/canonicalization/fingerprint machinery that `contracts` already uses — verified by
direct reads of every one of those call sites, not assumed from the `contracts` precedent's shape
alone. `MarriageState.status` is a brand-new three-value enum (`PROPOSED/ACCEPTED/REJECTED`),
confirmed `ContractStatus` has no `REJECTED` member. Bigamy prevention and the "eligibility helper"
are both confirmed out of scope by direct evidence (ticket ACs and schema-33's own field table) and
are explicitly not built. Docs (Mechanics Bible §8, `social_systems_contract.md`, parity ledger) are
updated in the same session per the Authoritative Mechanics Rule.

## Decisions (resolving the four flagged open questions)

**1. Where `MarriageState` durably lives.**
Confirmed by direct read: `StrategicComponent.contracts: Dict[str, ContractState]`
(`src/core/strategic.py:398`) is the exact structural analog. `StrategicUpdate` already carries a
`contracts_add_or_update: list[ContractState]` / `contracts_remove: list[str]` pair
(`src/core/updates.py:533-534`), consumed by:
- `is_noop()` (`updates.py:560`) and `merge()` (`updates.py:596-597`) — both must gain matching
  `marriages_add_or_update`/`marriages_remove` clauses.
- `Patch.apply()`'s `merge_dict(new_strat.contracts, u_strat.contracts_add_or_update,
  u_strat.contracts_remove)` (`src/engine/patches.py:466`) — needs an analogous
  `merge_dict(new_strat.marriages, u_strat.marriages_add_or_update, u_strat.marriages_remove)` line.
- `EntityUpdate.strategic: Optional[StrategicUpdate]` (`src/core/updates.py:681`) is the existing
  attach point — `execute_propose_marriage()` will set `strategic=StrategicUpdate(marriages_add_or_update=[...])`
  on both parties' `EntityUpdate`, exactly how `execute_train()` sets
  `strategic=StrategicUpdate(blockers_remove=resolved_blockers)` (`core_actions.py:385`).

Decision: add `StrategicComponent.marriages: Dict[str, MarriageState] = field(default_factory=dict)`
(keyed by a synthetic marriage-record id, mirroring `contracts`' `id`-keyed dict — not by spouse
entity id, so both parties can hold independent records without collision) and the matching
`StrategicUpdate` add/remove pair, following the `contracts` pattern exactly at every layer it
touches (`is_noop`, `merge`, `Patch.apply`).

**2. New `MarriageStatus` enum + `ContractStatus.REJECTED` gap.**
Confirmed by direct read of `src/core/strategic.py:59-70`: `ContractStatus` members are `OFFERED,
ACCEPTED, COUNTERED, ACTIVE, FULFILLED, COMPLETED(=FULFILLED alias), FAILED, BETRAYED, EXPIRED,
CANCELLED` — no `REJECTED`. Investigation's claim is verified, not assumed.

Decision: add a new `MarriageStatus(str, Enum)` in `src/core/strategic.py`, placed directly above
`class MarriageState`, with exactly `PROPOSED = "PROPOSED"`, `ACCEPTED = "ACCEPTED"`, `REJECTED =
"REJECTED"` — matching schema-33's literal three values and the existing `str, Enum` /
uppercase-value style every other enum in the file uses (e.g. `ContractKind.TEACH = "TEACH"` at
`strategic.py:86`). The transient offer keeps using `ContractStatus` unchanged (still resolves to
`ACCEPTED`/`CANCELLED` from `appraise_contract()`); only the durable `MarriageState.status` field
uses the new enum. No existing `ContractStatus` member is renamed, removed, or reused as a stand-in.

**3. Bigamy/duplicate-marriage prevention — out of scope for this ticket.**
Confirmed by direct read of the ticket's own Acceptance Criteria (`tickets/inprogress/
TCK-20260902-MARRIAGE-PROPOSAL-CONTRACT.md` AC #1-#7): none of the seven ACs mentions checking
whether either party already holds an `ACCEPTED` marriage before a new proposal succeeds. Confirmed
by direct read of schema-33's field table (`docs/brainstorm/rpg_expected_schemas.html:665-669`):
the four listed `MarriageState` fields are `proposer_entity_id, target_entity_id, status,
married_tick`, plus `eligibility_gate` (resolved separately below) — there is no `already_married`
or similar field, and no prose anywhere in the `#schema-33` section states a monogamy rule as a hard
requirement (only that it "implies" one, per investigation.md, which is not a testable requirement).

Decision: this plan does not add a not-already-married precondition. It is recorded as a candidate
for a future ticket, not added to this plan's scope (planner rule: never plan more than the ticket
requires). `MarriageState` remains a bare per-proposal record; nothing here prevents multiple
`marriages` dict entries per entity — that gap is a deliberate, documented scope boundary, not an
oversight.

**4. `_appraise_marriage()` needs nothing beyond the shared trust prelude.**
Confirmed by direct read of `docs/brainstorm/rpg_expected_schemas.html:669`: the `eligibility_gate`
row's Status column reads **"Reused as the gate; reads existing entity.social state"** (badge class
`done`, not `gated`/new) — this is the schema doc's own explicit statement that `eligibility_gate`
is not new logic to build, it is the existing trust/sentiment prelude
(`src/systems/social_systems/appraisal.py:48` `trust_score < 0.2 or (bond and bond.sentiment <
-0.8)`; `appraisal.py:52-54` betrayal-history check) already reading `entity.social` state. This
matches AC #1's literal wording ("a test confirms a proposal below hard-cancel thresholds... is
rejected with no marriage-specific bypass") and the `_appraise_teach` docstring precedent
(`appraisal.py:335-337`: "the shared prelude already expresses the entire trust gate this contract
kind uses... reaching this method means the prelude already passed, so it always accepts").

Decision: `_appraise_marriage()` is written identically in shape to `_appraise_teach()` — reaching
it means the prelude already passed, so it unconditionally returns `(ContractStatus.ACCEPTED,
ReasonCode.MARRIAGE_ACCEPTED, {})`. No additional scoring, no separate `eligibility_gate` field is
added to `MarriageState` (it is satisfied entirely by the existing prelude, not by a new stored
value) — this is also why the `LifeStage`-"adult" no-op concern from investigation.md is moot: no
alive/adult/same-race check is being built at all, so its current-always-`ADULT` orphaned-ness is
irrelevant to this ticket.

## Steps

### Step 1 — Add `ContractKind.MARRIAGE` enum member
**Files:** `src/core/strategic.py`
**Change:** Add `MARRIAGE = "MARRIAGE"` to `class ContractKind(str, Enum)` (currently
`strategic.py:73-86`, ending with `TEACH = "TEACH"` at line 86) — append directly after `TEACH`,
same style (uppercase value = name).
**Do NOT touch:** `ContractStatus` (lines 59-70) — no member added/removed there; `ContractState`
dataclass (lines 215-229) — no new fields.
**Verify:** `ContractKind.MARRIAGE` importable and constructible in a `ContractState`; exercised
implicitly by every test in Step 8 that constructs `ContractState(kind=ContractKind.MARRIAGE, ...)`.

### Step 2 — Add `MarriageStatus` enum and `MarriageState` dataclass
**Files:** `src/core/strategic.py`
**Change:** Add, near `ContractState` (after its definition, `strategic.py:215-229`):
```python
class MarriageStatus(str, Enum):
    PROPOSED = "PROPOSED"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"

@dataclass(frozen=True)
class MarriageState:
    id: str
    proposer_entity_id: int
    target_entity_id: int
    status: MarriageStatus
    married_tick: Optional[int] = None
```
Field types: `proposer_entity_id`/`target_entity_id` as `int` (matching `ContractState.source_id`/
`target_id`'s actual `int` entity-id type used throughout `core_actions.py`, not `str` as
schema-33's prose loosely states — entity ids are ints everywhere else in this file, e.g.
`ContractState.source_id`/`target_id` at `strategic.py:216-217`). `id: str` added for dict-keying
consistency with `ContractState.id` (per test_plan.md's `test_marriage_no_duration_or_aging_
threshold_introduced`, which explicitly allows an `id` field alongside the four schema fields).
Frozen dataclass, matching `ContractState`'s `@dataclass(frozen=True)` style.
**Do NOT touch:** Do not add an `eligibility_gate` field (Decision 4) or any duration/age/expiry
field beyond `married_tick` (ticket AC #5; test_plan.md's exact-field-set assertion).
**Verify:** `test_marriage_no_duration_or_aging_threshold_introduced` (new, `tests/unit/social/
test_marriage.py`) asserts the dataclass field set is exactly `{id, proposer_entity_id,
target_entity_id, status, married_tick}`.

### Step 3 — Add `StrategicComponent.marriages` field
**Files:** `src/core/state.py` (or wherever `StrategicComponent` is defined — investigation.md
cites `strategic.py:382-416`; confirm exact file at implement time, it is `src/core/strategic.py`
per this session's own read of lines 383-416)
**Change:** Add `marriages: Dict[str, MarriageState] = field(default_factory=dict)` to
`StrategicComponent` directly after `contracts: Dict[str, ContractState] = field(default_factory=dict)`
(`strategic.py:398`), same style.
**Do NOT touch:** No other `StrategicComponent` field (`blockers`, `leads`, `directives`, `projects`,
`concerns`, `candidate_zones`, `hypotheses`, `source_trust`, `turning_points`, `beliefs`,
`committed_intentions`, etc.) is modified.
**Verify:** `StrategicComponent()` constructs with `marriages={}` by default; exercised implicitly
by Step 6/7 tests.

### Step 4 — Add `StrategicUpdate.marriages_add_or_update` / `marriages_remove` and thread through `is_noop()`/`merge()`
**Files:** `src/core/updates.py`
**Change:** In `class StrategicUpdate` (`updates.py:503-608`), add after the existing `# Contracts`
block (`contracts_add_or_update`/`contracts_remove`, lines 532-534):
```python
# Marriages
marriages_add_or_update: list[MarriageState] = field(default_factory=list)
marriages_remove: list[str] = field(default_factory=list)
```
Extend `is_noop()` (`updates.py:550-565`) with `and not self.marriages_add_or_update and not
self.marriages_remove` in the boolean chain (alongside the existing `contracts_add_or_update`/
`contracts_remove` clause at line 560). Extend `merge()` (`updates.py:567-607`) with
`marriages_add_or_update=self.marriages_add_or_update + other.marriages_add_or_update,
marriages_remove=self.marriages_remove + other.marriages_remove,` in the returned `StrategicUpdate(...)`
constructor call, alongside the existing `contracts_add_or_update`/`contracts_remove` lines (596-597).
**Other writers of `StrategicUpdate` this step must not break:** `is_noop()` and `merge()` are called
on every `StrategicUpdate` produced anywhere in the codebase, including sites that never touch
`marriages` at all — `src/systems/social_systems/contracts.py` (lines 47, 78, 204, 285, 338),
`src/engine/domain/core_actions.py` (lines 118, 130, 199, 204, 274, 279 — pre-existing contract
creation sites), `src/engine/pipeline_phases/contracts.py` (line 93/112, contract expiry),
`src/engine/pipeline_phases/movement.py` (line 489, contract fulfillment), and
`src/domains/cooperation/services.py` (line 196). Because both new fields default to an empty list
and the change is purely additive (new `and not ...` clause, new constructor kwargs), none of these
existing call sites is affected — they never set `marriages_add_or_update`/`marriages_remove`, so
the new fields stay empty-list/no-op for them, exactly as `contracts_add_or_update`/`contracts_remove`
already stay empty-list/no-op for update sites unrelated to contracts. No ordering or collision risk:
`marriages` and `contracts` are independent dict fields on `StrategicComponent`, merged independently
in Step 5.
**Do NOT touch:** No other field in `StrategicUpdate` is renamed or restructured.
**Verify:** `StrategicUpdate().is_noop()` still returns `True`; `StrategicUpdate(marriages_add_or_update=[...]).is_noop()`
returns `False`; `merge()` concatenates two `StrategicUpdate`s' `marriages_add_or_update` lists —
covered by a small unit assertion inside `test_marriage_accepted_writes_typed_marriagestate_on_both_parties`
or a dedicated small test, implementer's choice, as long as it is exercised.

### Step 5 — Wire `marriages` into `Patch.apply()`
**Files:** `src/engine/patches.py`
**Change:** In the strategic-merge block (`patches.py:459-468`), add a line following the exact
`ncon = merge_dict(new_strat.contracts, u_strat.contracts_add_or_update, u_strat.contracts_remove)`
pattern (line 466):
```python
nmar = merge_dict(new_strat.marriages, u_strat.marriages_add_or_update, u_strat.marriages_remove)
```
and ensure `nmar` is passed into whatever `replace(new_strat, ...)` call downstream (in the same
function, immediately after this block) already passes `contracts=ncon` — add `marriages=nmar`
alongside it. Read the full function body around lines 459-500 at implement time to find that exact
`replace(...)` call site before editing (not confirmed by this investigation/plan pass; a real
`replace(new_strat, ..., contracts=ncon, ...)` call must exist immediately downstream since `ncon` is
otherwise unused — locate it, do not guess its line number).
**Other writers to this apply path:** `Patch.apply()` is the single authoritative merge point for
every `StrategicUpdate` in the tick (Core Boundaries rule: "Authoritative application is the only
place durable state should be committed") — no other file merges `StrategicComponent.contracts`
into a new `StrategicComponent`, confirmed by the earlier grep across `src/` showing `patches.py:466`
is the only `merge_dict(...contracts...)` call site. `marriages` follows the identical single-writer
shape — no race, since this is a single-threaded, single-pass apply function.
**Do NOT touch:** `nb`, `nl`, `nd`, `np`, `nc`, `ncz`, `nh`, `nbel`, `ntp`, `nbor` merges (lines
459-478) — unrelated fields, must remain byte-identical.
**Verify:** `test_marriage_accepted_writes_typed_marriagestate_on_both_parties` — after applying an
`EntityUpdate(strategic=StrategicUpdate(marriages_add_or_update=[...]))` through the real apply
path (not a hand-rolled dict merge), both parties' `entity.strategic.marriages` contains the new
record.

### Step 6 — Add `MARRIAGE_ACCEPTED` / `MARRIAGE_DECLINED` to `ReasonCode`
**Files:** `src/core/enums.py`
**Change:** Add `MARRIAGE_ACCEPTED = "marriage_accepted"` and `MARRIAGE_DECLINED =
"marriage_declined"` to `class ReasonCode` (confirmed existing precedent at `src/core/enums.py:160-161`:
`TEACH_ACCEPTED = "teach_accepted"` / `TEACH_DECLINED = "teach_declined"`), placed directly after
those two lines, same lowercase-snake-case value style.
**Do NOT touch:** No existing `ReasonCode` member renamed or removed. `MARRIAGE_DECLINED` will, like
`TEACH_DECLINED`, likely never actually be returned by `_appraise_marriage()` (Decision 4: prelude-only
gate, no kind-specific rejection branch) — add it anyway for symmetry/future use, matching the TEACH
precedent's own choice (investigation.md confirms `TEACH_DECLINED` exists but is unused today).
**Verify:** Exercised implicitly wherever tests assert `ReasonCode.MARRIAGE_ACCEPTED` on an accepted
outcome (Step 8 tests).

### Step 7 — Add `SocialAppraisalSystem._appraise_marriage()` and dispatch branch
**Files:** `src/systems/social_systems/appraisal.py`
**Change:** Add one new `elif` branch in `appraise_contract()`'s kind-dispatch chain (currently
`appraisal.py:57-84`, ending with the `TEACH` branch at lines 81-82 and the fallthrough
`return ContractStatus.CANCELLED, ReasonCode.UNKNOWN, {}` at line 84):
```python
elif contract.kind == ContractKind.MARRIAGE:
    return SocialAppraisalSystem._appraise_marriage(entity, contract, trust_score)
```
placed directly after the `TEACH` branch (before the fallthrough return). Add the method itself,
mirroring `_appraise_teach()` exactly (`appraisal.py:329-338`):
```python
@staticmethod
def _appraise_marriage(
    entity: EntityState,
    contract: ContractState,
    trust_score: float
) -> Tuple[ContractStatus, ReasonCode, Dict[str, Any]]:
    """The shared prelude (trust<0.2, sentiment<-0.8, betrayal-history) already expresses
    the entire trust gate this contract kind uses; reaching this method means the prelude
    already passed, so it always accepts. No utility/risk model or eligibility_gate scoring
    is added here — see plan.md Decision 4."""
    return ContractStatus.ACCEPTED, ReasonCode.MARRIAGE_ACCEPTED, {}
```
**Do NOT touch:** The shared trust hard-cancel prelude (`appraisal.py:29-54`, specifically lines 48
and 52-54) — read but never edited. No other kind's `elif` branch (`RECRUITMENT` at 57,
`LOAN` at 60, `POSITION_SWAP` at 65, `MERCHANT` at 72, `TEAM_UP` at 75, `PAID_INFORMATION` at 78,
`TEACH` at 81) is reordered or modified.
**Verify:** `test_marriage_dispatch_no_fallthrough` and `test_marriage_refused_below_trust_hard_cancel_threshold`
(test_plan.md) — the latter proves the prelude still gates `MARRIAGE` identically to every other
kind, with no marriage-specific bypass.

### Step 8 — Add `CoreActions.execute_propose_marriage()` and `ActionRouter` dispatch
**Files:** `src/engine/domain/core_actions.py`, `src/engine/domain/action_router.py`
**Change:** In `core_actions.py`, add `execute_propose_marriage()` mirroring `execute_train()`
exactly (`core_actions.py:327-398`, cited above): resolve `target_id` via
`neighbor_view`/`context.entities` (lines 341-355 shape, `TARGET_NOT_FOUND` on failure per line
352-355), build `temp_contract = ContractState(id="temp_eval", kind=ContractKind.MARRIAGE,
source_id=entity.id, target_id=target.id, terms={}, status=ContractStatus.OFFERED,
created_tick=current_tick)`, call `SocialAppraisalSystem.appraise_contract(target, temp_contract,
context)` — **target appraises proposer**, same direction as every existing two-party handler
(explicit anti-drift hazard from investigation.md). On `ACCEPTED`: build a `MarriageState` with a
fresh id (e.g. `f"marriage_{entity.id}_{target_id}_{current_tick}"`), `status=MarriageStatus.ACCEPTED`,
`married_tick=current_tick`, and write it via `EntityUpdate(entity_id=entity.id,
strategic=StrategicUpdate(marriages_add_or_update=[marriage_record]))` on the proposer's update AND
`EntityUpdate(entity_id=target_id, strategic=StrategicUpdate(marriages_add_or_update=[marriage_record]))`
on the target's update — same record object/id on both sides (AC #3, "written... on both parties").
On any other status: reuse the shared rejection shape from `execute_train()`
(`readiness_delta=-50.0` + `task=replace(...)` on proposer; `social=SocialUpdate(rejection_increment=...)`
on target — `core_actions.py:389-397`). In `action_router.py`, add:
```python
if action == "PROPOSE_MARRIAGE":
    return CoreActions.execute_propose_marriage(entity, payload, current_tick, neighbor_view, context)
```
placed after the existing `"TRAIN"` branch (`action_router.py:58-59`).
**Do NOT touch:** `execute_train()` itself — read as a template only, not modified. No other
`ActionRouter` branch (`RECRUIT`, `TEAM_UP`, `TRADE`, `ALLOCATE_AP`, `TRAIN`, `REPAIR`, `INTERACT`,
lines 46-65) reordered or modified.
**Verify:** `test_marriage_proposal_builds_transient_contract_and_calls_real_appraise_contract`,
`test_marriage_accepted_writes_typed_marriagestate_on_both_parties`,
`test_marriage_target_appraises_proposer_not_vice_versa`,
`test_marriage_action_requires_proposer_and_target`,
`test_marriage_action_routes_through_action_router` (all test_plan.md, new `tests/unit/social/
test_marriage.py`).

### Step 9 — Lock `ContractService.get_project_mapping()` exclusion (test-only, no production change)
**Files:** `tests/unit/ai/goals/test_social_contract_goal_scorer.py`
**Change:** Add `ContractKind.MARRIAGE` to the existing parametrized list currently reading
`ContractKind.PROTECTION, ContractKind.MERCHANT, ContractKind.POSITION_SWAP, ContractKind.TEAM_UP,
ContractKind.PAID_INFORMATION, ContractKind.TEACH` (confirmed at `test_social_contract_goal_scorer.py:125-130`).
No change to `src/systems/social_systems/contracts.py`'s `get_project_mapping()`
(`contracts.py:137-152`, confirmed by direct read: it returns `None` for any kind other than
`RECRUITMENT`/`LOAN` by construction — `MARRIAGE` already falls through correctly).
**Do NOT touch:** `get_project_mapping()` itself — this step is a regression lock only, never a
production code change (explicit anti-drift hazard from investigation.md).
**Verify:** `test_marriage_kind_excluded_from_project_materialization` (test_plan.md).

### Step 10 — Canonicalization and fingerprint parity for the new durable field
**Files:** `src/core/state.py`, `src/replay/fingerprint.py`
**Change:** `AuthoritativeState.to_canonical_dict()`'s `"strategic"` sub-dict (`state.py:781-796`,
confirmed by direct read: it currently includes `current_project_id, current_objective_id, projects,
directives, blockers, leads, concerns, boredom, beliefs` — **not** `contracts`, a pre-existing gap).
Add a `"marriages": {k: asdict(v) for k, v in sorted(self.strategic.marriages.items())}` entry to
this dict. This deliberately does not fix the pre-existing `contracts` omission (out of scope, not
touched) but avoids silently inheriting the same gap for the new field this ticket introduces (per
investigation.md's explicit flag to make this a stated decision, not a silent copy).
Similarly, in `src/replay/fingerprint.py`, add a `marriage_ident` string mirroring the existing
`contract_ident` pattern (confirmed at `fingerprint.py:205-211`, joined into the final fingerprint at
line 234):
```python
marriage_ident = "|".join(
    f"{marriage_id}:{m.status}:{m.target_entity_id}"
    for marriage_id, m in sorted(strategic.marriages.items())
)
```
and add `f"marriages=[{marriage_ident}];"` to the fingerprint f-string alongside the existing
`f"contracts=[{contract_ident}];"` line (`fingerprint.py:234`).
**Do NOT touch:** The existing `contracts` canonicalization gap (`state.py:781-796`) — do not add a
`"contracts"` key as a side-fix; that is out of this ticket's scope and not requested by any AC.
**Verify:** A determinism-focused assertion is optional here (no AC explicitly requires it), but if
added, keep it inside `test_marriage.py` as a light `to_canonical_dict()`/fingerprint round-trip
check — not required by test_plan.md's enumerated list, do not treat as blocking if time-constrained,
but do not skip the code addition itself (Durable State Rule: "inspection/debug visibility" +
CLAUDE.md's "Do not break determinism" hard rule).

### Step 11 — New test file `tests/unit/social/test_marriage.py`
**Files:** `tests/unit/social/test_marriage.py` (new)
**Change:** Add all `MARRIAGE`-specific tests enumerated in test_plan.md's "New Tests Required"
section that are scoped to this file: `test_marriage_refused_below_trust_hard_cancel_threshold`,
`test_marriage_proposal_builds_transient_contract_and_calls_real_appraise_contract`,
`test_marriage_accepted_writes_typed_marriagestate_on_both_parties`,
`test_marriage_no_free_form_dict_carries_accepted_outcome`,
`test_marriage_no_duration_or_aging_threshold_introduced`,
`test_marriage_target_appraises_proposer_not_vice_versa`,
`test_marriage_action_requires_proposer_and_target`,
`test_marriage_action_routes_through_action_router` — following `tests/unit/social/test_teach.py`'s
fixture/structure conventions (`V2EntityBuilder`, `AuthoritativeState`,
`SimulationDomainLogic.execute_action`/`ActionRouter.execute_action`), per test_plan.md.
**Do NOT touch:** `test_teach.py`, `test_team_up.py` — read as structural templates only, never
edited.
**Verify:** All tests pass under
`.venv/bin/python3 -m pytest tests/unit/social/test_marriage.py -q`.

### Step 12 — Extend `test_appraisal_logic.py` parametrizations
**Files:** `tests/unit/social/test_appraisal_logic.py`
**Change:** Add `ContractKind.MARRIAGE: {}` to `test_shared_gate_no_fallthrough_for_gated_kinds`'s
`kind_terms` dict (mirroring the existing `TEACH` entry, per test_plan.md), covering
`test_marriage_dispatch_no_fallthrough`. Add the boundary-value case for `MARRIAGE` at trust score
`0.195` (not `0.2` — documented TEACH-ticket correction, strict `<` comparison at `appraisal.py:48`)
to `test_marriage_boundary_trust_score_matches_recruitment_and_team_up_and_teach_just_below_0_2`
(test_plan.md).
**Do NOT touch:** Existing per-kind entries for `RECRUITMENT`/`LOAN`/`POSITION_SWAP`/`MERCHANT`/
`TEAM_UP`/`PAID_INFORMATION`/`TEACH` in this file — must remain unmodified and green.
**Verify:** `.venv/bin/python3 -m pytest tests/unit/social/test_appraisal_logic.py -q`.

### Step 13 — Docs: Mechanics Bible, social systems contract, parity ledger
**Files:** `docs/mechanics/04_strategic_cognition.md`, `docs/simulation/social_systems_contract.md`,
`docs/parity_ledger/social_narrative.yaml`
**Change:**
- Add a new "§8 Marriage Proposal Law" section to `04_strategic_cognition.md` (confirmed no such
  section exists today — investigation.md read the chapter's full §1-§7 list; §7 is "Party
  Composition & Formation Scoring," a scoring function, not a contract/appraisal law, so §8 is a new
  section, not a rewrite). Document: `ContractKind.MARRIAGE` propose/accept via the shared trust
  prelude (cite the exact thresholds `0.2`/`0.4`/`-0.8`), target-appraises-proposer direction, the
  `MarriageState` record shape, and explicitly state bigamy prevention is out of scope (Decision 3)
  and no aging/duration threshold exists (out of scope, ticket-bound).
- Add a `MARRIAGE` row to `social_systems_contract.md`'s "Contract kinds" table, mirroring the
  `TEACH` row added by `TCK-20260831-TRUST-GATED-TEACHING` (per that doc's own Extension rules
  checklist, confirmed by investigation.md).
- Add a new P0 entry to `docs/parity_ledger/social_narrative.yaml` for the `MARRIAGE` contract-kind
  trust gate (mirroring `SOC-258`'s shape for `TEACH`), with `test_path` pointing at
  `test_marriage_refused_below_trust_hard_cancel_threshold`, plus a second entry (or an extension of
  the same entry) covering the `MarriageState` durable-record write path.
**Do NOT touch:** No other Mechanics Bible chapter, no other `social_systems_contract.md` row, no
other parity ledger entry (including `SOC-001`/`SOC-008`/`SOC-134`/`SOC-258`, which stay unmodified
— they already correctly describe the shared prelude this ticket does not touch).
**Verify:** Doc presence + `test_path` reference resolves to a real, passing test (P0 requirement).
Run `make docs-registry`/`make knowledge-index-update` per CLAUDE.md's After Work rule at Finalize
time (not part of this plan's steps — a workflow-level action).

## Scope Guards

- Do not modify the shared trust hard-cancel prelude in `appraisal.py:29-54` (lines 48, 52-54) —
  P0 parity `SOC-001`/`SOC-008`/`SOC-134` depend on its exact thresholds and structure.
- Do not widen `ContractService.get_project_mapping()` (`contracts.py:137-152`) for `MARRIAGE` — add
  a regression-lock test only (Step 9), never a code change.
- Do not let the accepted-marriage outcome leak into `ContractState.terms` or any `reason` string —
  it must be a typed `MarriageState` field only (AC #4).
- Do not add household/family/dependents state to `MarriageState` — that is
  `TCK-20260902-PERSONAL-DEPENDENTS-ROUTE-BIAS`'s scope (idea 31), a separate ticket.
- Do not introduce any shared generic `ProposalState` base class across
  Marriage/Team-Up/Trade/Clan-entry — explicitly out of scope per the ticket.
- Do not introduce any fantasy-year aging or lifecycle-duration numeric field — `married_tick` is a
  plain tick timestamp with no derived-duration/expiry logic.
- Do not add a not-already-married ("bigamy") precondition — Decision 3, out of scope, no AC
  requires it.
- Do not add an `eligibility_gate` field or any alive/adult/same-race check to `MarriageState` or
  `_appraise_marriage()` — Decision 4, the schema doc's own "Reused as the gate" status confirms this
  is already satisfied by the existing prelude.
- Do not fix the pre-existing `contracts` canonicalization gap (`state.py:781-796` omitting
  `contracts`) as a side-effect of Step 10 — only the new `marriages` field is added to
  `to_canonical_dict()`.
- Do not modify `execute_train()`, `test_teach.py`, or `test_team_up.py` — read as templates only.

## Deviations

- **`MarriageState` dataclass decorator**: Step 2's illustrative code block above shows
  `@dataclass(frozen=True)`. Per the architecture review's explicit style nit (every existing
  dataclass in `src/core/strategic.py` — `ContractState`, `BlockerState`, `LeadState`, etc. — uses
  `@dataclass(frozen=True, slots=True)`), the implemented `MarriageState` uses
  `@dataclass(frozen=True, slots=True)` to match house style exactly. This is a style correction to
  the plan's own snippet, not a scope or behavior change — confirmed by direct read that every one
  of the ~13 other dataclasses in that file already uses the `slots=True` pair.
- No other deviation from this plan's steps or Decisions 1-4. `MarriageState`'s field set is exactly
  `{id, proposer_entity_id, target_entity_id, status, married_tick}`, as decided.

## Dependency Map

- Step 1 (enum member) has no dependencies; must land before any step that constructs
  `ContractState(kind=ContractKind.MARRIAGE, ...)`.
- Step 2 (`MarriageStatus`/`MarriageState`) has no dependencies; must land before Steps 3, 4, 8, 11.
- Step 3 (`StrategicComponent.marriages`) depends on Step 2; must land before Steps 4, 5, 10.
- Step 4 (`StrategicUpdate` fields/`is_noop`/`merge`) depends on Step 2; must land before Steps 5, 8.
- Step 5 (`Patch.apply()` wiring) depends on Steps 3 and 4; must land before Step 8's tests can pass
  end-to-end (the accepted-write test exercises the real apply path).
- Step 6 (`ReasonCode` additions) has no dependencies on other steps; must land before Step 7.
- Step 7 (`_appraise_marriage` + dispatch) depends on Steps 1 and 6.
- Step 8 (`execute_propose_marriage` + router) depends on Steps 1, 2, 4, 5, 7.
- Step 9 (goal-scorer exclusion test) depends on Step 1 only.
- Step 10 (canonicalization/fingerprint) depends on Step 3.
- Step 11 (new test file) depends on Steps 1, 2, 4, 5, 6, 7, 8.
- Step 12 (appraisal_logic.py parametrizations) depends on Steps 1, 6, 7.
- Step 13 (docs) depends on all implementation steps being complete (documents final shape).

Steps 1, 2, 6, 9 are mutually independent and can be done in any relative order before their
respective dependents. Steps 3+4+5 form the durable-storage chain and should be done together in
that order. Steps 11 and 12 are the verification steps that prove Steps 1-10 are correct.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC #1: `ContractKind.MARRIAGE` exists | Step 1 | Implicit in every Step 11/12 test |
| AC #2: `_appraise_marriage()` exists, dispatched correctly, prelude unmodified | Steps 6, 7 | `test_marriage_refused_below_trust_hard_cancel_threshold`, `test_marriage_dispatch_no_fallthrough` |
| AC #3: transient `ContractState` built, real `appraise_contract()` called; ACCEPTED writes typed `MarriageState` on both parties | Steps 2, 3, 4, 5, 8 | `test_marriage_proposal_builds_transient_contract_and_calls_real_appraise_contract`, `test_marriage_accepted_writes_typed_marriagestate_on_both_parties` |
| AC #4: no `reason`/`terms` free-form dict carries accepted-marriage outcome | Steps 2, 8 | `test_marriage_no_free_form_dict_carries_accepted_outcome` |
| AC #5: no fantasy-year aging/duration threshold introduced | Step 2 | `test_marriage_no_duration_or_aging_threshold_introduced` |
| AC #6: new unit tests following `test_teach.py`/`test_team_up.py` conventions | Steps 9, 11, 12 | The full new/extended test suite itself |
| AC #7: new Mechanics Bible entry for idea 33 | Step 13 | Doc presence check (done-checker); parity ledger `test_path` must pass |

## Anti-Drift Notes

- The shared trust hard-cancel prelude (`appraisal.py:29-54`) is P0-parity-covered
  (`SOC-001`/`SOC-008`/`SOC-134`) — copy its pattern into `_appraise_marriage()`, never edit it.
- A literal `trust_score == 0.2` does **not** trigger the hard-cancel gate (strict `<` comparison at
  `appraisal.py:48`) — any boundary test must use `0.195`, not `0.2` exactly (documented TEACH-ticket
  correction, reused verbatim in Step 12).
- Preserve the target-appraises-proposer direction exactly
  (`appraise_contract(target, temp_contract, context)`, not the reverse) — every existing two-party
  handler uses this convention; a direction flip silently inverts who is being trust-gated.
- `ContractService.get_project_mapping()` already returns `None` for `MARRIAGE` by construction — Step
  9 is a regression lock only, never a production code change.
- `MarriageState` stays a bare four-field-plus-id record
  (`id, proposer_entity_id, target_entity_id, status, married_tick`) — do not let household/family/
  dependents fields (idea 31's scope) or an `eligibility_gate` field (Decision 4) creep in.
- `StrategicUpdate.is_noop()`/`merge()` are shared by every other contract-creation call site in the
  codebase (enumerated in Step 4's Change text) — the new `marriages_*` fields must stay purely
  additive (empty-list defaults, appended clauses) so none of those unrelated call sites' behavior
  changes.
- `Patch.apply()` is the single authoritative merge point for `StrategicComponent` — no other file
  merges `contracts` or should merge `marriages`; Step 5 must not introduce a second write path.
- Do not silently inherit the pre-existing `contracts` canonicalization gap for the new `marriages`
  field (Step 10) — but do not fix the `contracts` gap itself either; that is separately out of scope.
