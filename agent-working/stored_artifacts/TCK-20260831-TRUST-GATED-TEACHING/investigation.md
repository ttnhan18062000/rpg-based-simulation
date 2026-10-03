---
status: historical
layer: economy
authority: P2
audience: agent
ticket_id: TCK-20260831-TRUST-GATED-TEACHING
artifact_type: investigation
tags: [social, economy]
---

# Investigation — TCK-20260831-TRUST-GATED-TEACHING

## Context-Search Note

Per the mandatory Step 0c: `mcp__knowledge-search__search_docs` was called first with the query
"Gate the teach/train action on trust instead of gold alone" (top hits: `docs/engine/
authoritative_pipeline.md#trust-boundary-002`, `docs/simulation/domains/cooperation_contract.md` —
neither directly about `execute_train`) and a second targeted call "execute_train TRAIN_COST teach
skill recipes_learned" plus "appraise_contract hard-cancel trust_score bond.sentiment shared gate"
(surfaced `docs/simulation/social_systems_contract.md`'s Appraisal/Relationships sections as the
authoritative doc home for the shared gate — used below). `graphify query "teach train action trust
gate"` returned an unrelated `PerceptionGate` community; a follow-up `graphify query "execute_train
core_actions"` correctly located `.execute_train()` at `core_actions.py:327`, `IdentityUpdate` at
`src/core/updates.py:223`, and `SocialAppraisalSystem` at `appraisal.py:13`, all confirmed below by
direct read. Only after these calls were grep/file reads used.

## Current Behavior

### `CoreActions.execute_train()` — `src/engine/domain/core_actions.py:327-361`

Single-entity, single-party action. Signature: `execute_train(entity, payload, current_tick) ->
Dict[int, EntityUpdate]` — **no target/teacher entity concept at all**, confirmed by direct read.
Routed from `ActionRouter.execute_action()` at `src/engine/domain/action_router.py:58-59` (`if
action == "TRAIN": return CoreActions.execute_train(entity, payload, current_tick)`), gated only by
`LegalityServiceV2.verify_readiness()` upstream (line 38-44 of the router — the generic
readiness==100.0 check every routed action gets, nothing TRAIN-specific).

Body: reads `payload.get("skill_id")` (fails `MISSING_SKILL_ID` if absent), then unconditionally
builds:
```python
TRAIN_COST = 50
intent = ResourceTransferIntent(
    source_id="CLASS_HALL", source_kind="TOWN_SERVICE", gold_delta=-TRAIN_COST,
    transfer_kind="TRAIN", is_group_required=True,
    identity_upd=IdentityUpdate(recipes_learned=[skill_id]),
    strategic_upd=StrategicUpdate(blockers_remove=resolved_blockers),
)
```
and returns `{entity.id: EntityUpdate(entity_id=entity.id, readiness_delta=-100.0,
resource_transfers=[intent])}`. `resolved_blockers` is every `BlockerState` in
`entity.strategic.blockers` with `kind == "capability"` and `subject == skill_id`
(`BlockerKind.CAPABILITY = "capability"`, `src/core/strategic.py:101`).

**No trust/social check of any kind exists in `execute_train()` today** — confirmed by full read of
lines 327-361; nothing imports or calls `SocialAppraisalSystem`.

### The 50-gold cost is not actually an enforced affordability gate today (`src/core/conservation.py:254-271`)

`ResourceTransactionResolver.resolve()`'s `TOWN_SERVICE` branch (which handles `CLASS_HALL`/`TRAIN`):
```python
if intent.source_kind in ("TOWN_SERVICE", "TAX", "REPAIR_FEE", "SERVICE_FEE", "INFORMATION_PURCHASE"):
    if target_inventory.gold < intent.gold_cost:
        return TransactionResult(accepted=False, reason=ReasonCode.ACTION_EXHAUSTION)
    return TransactionResult(accepted=True, inventory_update=InventoryUpdate(
        items_add=intent.items_add, gold_delta=intent.gold_delta - intent.gold_cost), ...)
```
`execute_train()`'s intent sets `gold_delta=-TRAIN_COST` but **never sets `gold_cost`** (defaults to
`0` on `ResourceTransferIntent`, `src/core/update_models/resources.py:24`). The affordability check
is therefore `target_inventory.gold < 0`, always `False` — the transaction is **always accepted**
regardless of the entity's gold balance. Downstream, `InventoryService.apply_update()`
(`src/core/inventory.py:143,217`) clamps `gold=max(0, inventory.gold + update.gold_delta)`. Net
effect: training today never rejects on insufficient gold — an entity with less than 50 gold still
learns the recipe and has its gold floored at 0, it just doesn't pay the full nominal cost. This is
existing (pre-ticket) behavior, not something this ticket introduces, but it materially weakens the
"removing TRAIN_COST breaks an enforced economic gate" argument on one side of the ticket's central
open question — see Risks and Open Questions.

### A second, unwired, near-duplicate implementation exists: `src/town/class_hall.py`

`ClassHallAction.train(entity, skill_id, state) -> Optional[StateUpdate]` (`src/town/class_hall.py:9-44`,
read in full) implements the *same* mechanic — 50-gold cost, capability-blocker resolution,
`IdentityUpdate(recipes_learned=[skill_id])` via an identical `ResourceTransferIntent` shape — but
**does** perform a real affordability check up front: `if entity.inventory.gold < 50 or skill_id in
entity.identity.known_recipes: return None`. Confirmed via `grep -rn "class_hall\|ClassHall" src/
tests/` that this module has **no caller anywhere in `src/`** — it is exercised only by its own
dedicated test, `tests/unit/world/test_recovery_class_hall.py::test_class_hall_training` (line
59-80). It is not wired into `ActionRouter`. This is a pre-existing, orphaned duplicate — not in the
ticket's Related Code Areas, and not touched by this ticket's scope, but it is a live drift hazard:
if this ticket trust-gates `CoreActions.execute_train()` only, the two implementations diverge
further (one trust+gold-gated, one gold-only and dead-but-present). Flagged for the planner to make
an explicit decision (touch it / explicitly declare out of scope) rather than leave unaddressed by
accident.

### `IdentityUpdate(recipes_learned=...)` already exists and is fully wired end-to-end — no new durable-state field required

Refuting the ticket's own flagged concern: `IdentityUpdate.recipes_learned: list[str]` already exists
(`src/core/updates.py:227`), with `merge()` logic at line 259 (`list(set(self.recipes_learned +
other.recipes_learned))`). The durable target field is `IdentityComponent.known_recipes: Set[str]`
(`src/core/state.py:488`). The apply-path merge is already wired: `src/engine/patches.py:179,198`
(`rec = set(new_id.known_recipes); ...; rec |= set(u_id.recipes_learned)`) folds
`recipes_learned` deltas into `known_recipes` on every apply pass — confirmed by the existing passing
test `tests/unit/resource/test_resource_v2_boundary.py::test_class_hall_train_refactor` (line
274-299), which drives `execute_train()` through the full pipeline
(`SimulationDomainLogic.execute_action` → `AuthoritativeApplyPipeline.refine` → `ApplyPath.apply_generation`)
and asserts `"STRIKE" in next_state.entities[1].identity.known_recipes` and
`next_state.entities[1].inventory.gold == 50` (100 - 50). **No new field, no new component
reconstruction/`apply.py` wiring is needed** — the "silent-drop-trap" concern this batch has
established as a pattern does not apply here; this is a genuinely pre-existing, tested path.

### "Emit directly, not via a shared generic mutation" — precedent already exists in the same file

`CoreActions.execute_allocate_ap()` (`core_actions.py:319-324`, a few lines above `execute_train`)
already returns `EntityUpdate(entity_id=entity.id, identity=IdentityUpdate(unspent_ap_delta=-amount),
...)` — i.e. sets `EntityUpdate.identity` **directly** at the top level, not nested inside a
`ResourceTransferIntent.identity_upd`. This is the exact shape the ticket's AC #3 asks
`execute_train()` to adopt for `recipes_learned`: today `IdentityUpdate(recipes_learned=[skill_id])`
is nested inside the `ResourceTransferIntent` as a *contingent* update — only applied if
`ResourceTransactionSystem._merge_contingent_updates()` (`src/engine/economy.py:111`) accepts the
transaction (which, per the affordability-check gap above, always happens today). Moving it to
`EntityUpdate.identity` directly decouples recipe-learning from the resource-transaction resolution
path entirely — consistent with `execute_allocate_ap`'s existing pattern in the same class.

### The shared trust hard-cancel gate — `SocialAppraisalSystem.appraise_contract()`, `src/systems/social_systems/appraisal.py:20-80`

Trust computation (lines 30-45): `bond = entity.social.bonds.get(source_id)`; if a `SocialBond`
exists, `trust_score = (bond.sentiment + 1.0) / 2.0` (private sentiment takes priority); else
`trust_score = public_trust*0.7 + history_trust*0.3` where `public_trust =
source_entity.social.public_reputation/2.0` and `history_trust =
entity.social.trust_history.get(source_id, 0.5)`.

Hard-cancel prelude (lines 48-54, shared across **all** kinds before dispatch): `trust_score < 0.2 or
(bond and bond.sentiment < -0.8)` → `(CANCELLED, TOTAL_DISTRUST, {})`; separately
`entity.social.betrayal_count > 0 and trust_score < 0.4` → `(CANCELLED, BETRAYAL_HISTORY, {})`.

Kind dispatch (lines 57-80) currently handles `RECRUITMENT`, `LOAN`, `POSITION_SWAP`, `MERCHANT`,
`TEAM_UP`, `PAID_INFORMATION` (the last three added by the immediately-prior ticket,
TCK-20260824-AFFECTION-CONTRACT-GATE) and falls through to `(CANCELLED, ReasonCode.UNKNOWN, {})` for
any unhandled kind — **`TEACH`/`TRAINING` is not a `ContractKind` member today** (confirmed via
`src/core/strategic.py:73-85`: `RECRUITMENT, LOAN, PROTECTION, MERCHANT, POSITION_SWAP, TEAM_UP,
PAID_INFORMATION`). If this ticket routes through `appraise_contract()` proper (the AFFECTION-CONTRACT-
GATE precedent's own pattern — `execute_recruit()`/`execute_team_up()`/`execute_trade()` all build a
transient `ContractState` and call the full function), a new `ContractKind.TEACH` (or similar) member
must be added or the call will silently fall through to `UNKNOWN`. Alternatively, the ticket's Scope
text ("using ... `appraise_contract()`'s shared hard-cancel threshold") can be read more narrowly as
"reuse the *threshold numbers* (`trust_score<0.2` / `bond.sentiment<-0.8`), not necessarily the full
`ContractState`/`ContractKind` dispatch machinery" — i.e. inline the same formula without adding a new
`ContractKind`. **Both readings are defensible from the ticket text; this investigation does not
decide between them** — see Risks and Open Questions and the ticket's own Out of Scope line, which
already anticipates "even if a new `ContractKind.TEACH` is introduced."

### `entity.social.bonds` / `trust_history` representation — `src/systems/social_systems/relationships.py`, `src/core/state.py`

`SocialComponent.bonds: Dict[int, SocialBond]` and `SocialComponent.trust_history: Dict[int, float]`
are the fields `appraise_contract()` reads (confirmed via `relationships.py:1-80`,
`RelationshipService.process_update()`, and cross-checked against `appraisal.py:30-45`'s exact
attribute access). `SocialBond.sentiment` (-1.0 to 1.0) is the field carrying "trust/affection" per
the immediately-prior ticket's own investigation (`stored_artifacts/TCK-20260824-AFFECTION-CONTRACT-GATE/
investigation.md` Decision 1, adopted as Decision 1 of that ticket's plan: reuse `sentiment`, do not
add a new field). This ticket should reuse the identical formula, not re-derive trust.

### Which party is "entity," which is "target"? — architecture implication of adding a second party

Every existing two-party action in this file (`execute_recruit`, and the AFFECTION-CONTRACT-GATE-added
`execute_team_up`/`execute_trade`) follows the same shape: `entity` is the actor/initiator for this
tick, `payload["target_id"]` names the other party, and the handler returns a `Dict[int, EntityUpdate]`
keyed by **both** ids (e.g. `execute_recruit`: `{entity.id: attacker_up, target_id: target_up}`,
`core_actions.py:132`). Mapping this onto Teaching most naturally means: `entity` = the
skill-holding teacher (the one whose turn/action this is), `payload["target_id"]` = the student. The
recipe-learning `IdentityUpdate(recipes_learned=[skill_id])` and the capability-`BlockerState`
resolution must then apply to the **target's** `EntityUpdate`, not the teacher's — a real
restructuring of `execute_train()`'s current single-`EntityUpdate` return shape, not a one-line
threshold swap. The trust check itself, per `appraise_contract()`'s own signature
(`appraise_contract(entity: EntityState, contract, state)`), evaluates the **entity's** (i.e. the
appraiser's) trust toward `contract.source_id`; precedent (`execute_recruit`,
`core_actions.py:83-94`) calls `appraise_contract(target, temp_contract, context)` — the *target*
appraises the *offer from* `entity`. Applied here: the student (target) appraises the teacher
(entity)'s offer, i.e. the target's `bond`/`trust_history` toward the teacher gates whether the
target accepts being taught. This is the precedent-consistent mapping, but is not stated explicitly
in the ticket — flagged as an open question for the planner to confirm rather than assume silently.

### Zero existing dedicated test file for `execute_train()`, but one existing pipeline-level test exercises it indirectly

Confirmed no `tests/unit/social/test_train.py` or similar exists (`ls tests/unit/social/` — no
`train` match). However, `tests/unit/resource/test_resource_v2_boundary.py::test_class_hall_train_refactor`
(line 274-299) **does** exercise `CoreActions.execute_train()` end-to-end via
`SimulationDomainLogic.execute_action()` → `AuthoritativeApplyPipeline.refine()` →
`ApplyPath.apply_generation()`, asserting the gold deduction (`gold == 50` after a 100-gold start) and
`"STRIKE" in ... known_recipes`. This is real regression surface for this ticket's refactor
(single-entity signature → teacher+target signature): the ticket's own "no test file covers
execute_train at all" claim is accurate for a *dedicated* test file, but this existing integration
test must be identified and updated (its call shape, `SimulationDomainLogic.execute_action(hero,
payload=payload)` with no target, will no longer match a two-party signature) or explicitly reasoned
about as still valid for the no-target/self-training case, if one is kept. A second orphaned
duplicate, `tests/unit/world/test_recovery_class_hall.py::test_class_hall_training`, exercises the
unwired `ClassHallAction.train()` and is unaffected by any change scoped to `core_actions.py`.

### `docs/mechanics/03_economic_laws.md` §1 Atomic Conservation Law

"A resource transfer only succeeds if: 1. The Source has the resource available. 2. The Sink
(Destination) has the capacity to receive it. 3. Both updates happen in a single atomic step." For
`TOWN_SERVICE`-kind transfers (which `TRAIN` uses), the "Source" is the paying entity's own
inventory and the "Sink" is `CLASS_HALL`, an untracked abstract town service — not a real
conservation-tracked entity/object anywhere in `AuthoritativeState`. Removing the gold leg of TRAIN
entirely does not violate the Atomic Conservation Law as documented: no other tracked object's gold
balance depends on `CLASS_HALL` receiving payment (confirmed no `CLASS_HALL`-keyed balance exists
anywhere in `src/core/state.py`). The law's real teeth here are slot/weight limits and item
source/sink pairs (§2-3), neither of which TRAIN touches. This weakens, but does not eliminate, an
argument that removing TRAIN_COST is a Chapter-3 violation — see Risks and Open Questions for the
tradeoffs the planner must weigh explicitly per the ticket's own AC #4.

## Mechanics / Engine Constraints

- **`docs/mechanics/03_economic_laws.md` §1 (Atomic Conservation Law)**: constrains any change to
  how gold moves during training. As shown above, `CLASS_HALL` is an untracked abstract sink, so
  removing the `ResourceTransferIntent`/gold leg does not break atomic source/sink pairing for any
  *tracked* object — but the planner's decision (replace vs. gate-alongside) is still a documented
  economic-law-adjacent decision and must be recorded per the ticket's own AC #4, and per this
  project's Authoritative Mechanics Rule ("Divergence... MUST be recorded in
  `docs/guidelines/intentional_divergences.md`" if the gold cost is dropped, since that is a
  behavior change diverging from the current documented-if-informally cost).
- **`docs/simulation/social_systems_contract.md`'s "Contract kinds" table and its own checklist**
  ("To add a new contract kind: add to `ContractKind` enum, implement an appraisal method in
  `SocialAppraisalSystem`, add breach conditions in `contracts.py`, add tests") governs *if* the
  planner chooses the full-`appraise_contract()`/new-`ContractKind.TEACH` route. If the planner
  instead inlines the threshold formula without a new `ContractKind`, this doc's contract-kinds table
  is not implicated, but the doc's own "Appraisal" section (which currently documents the shared
  prelude formula/thresholds) should still be checked for consistency.
- **Durable State Rule (project CLAUDE.md)**: any new participant relationship (teacher/target) must
  flow through typed `EntityUpdate`/`IdentityUpdate` records via the authoritative apply path — not
  through `payload`/`reason` strings. The existing `IdentityUpdate.recipes_learned` field already
  satisfies this; no new durable field is required per the finding above.
- **Determinism**: `execute_train()` has no iteration-order-dependent logic today (`resolved_blockers`
  loop iterates `entity.strategic.blockers.items()`, a dict — if a two-party version needs to iterate
  target's blockers, the same dict-iteration-order caution documented elsewhere in this codebase for
  `PaidInformationTransactionSystem.enforce()`'s `sorted(...)` calls applies if any new selection
  logic is added; today's single capability-kind filter is a plain filter, not order-sensitive to
  output, since `blockers_remove` is a list of ids, not a first-match selection).

## Docs Requiring Update

- `docs/mechanics/03_economic_laws.md`: the planner's explicit AC #4 decision (gold-replaces-vs-
  gates-alongside) changes documented training-cost economics; whichever way it resolves, the
  chapter's treatment of service-fee-style costs (or the introduction of a trust-gated,
  non-gold-costed action) should be reflected so the doc and code stay in parity per the project's
  Authoritative Mechanics Rule. **Resolved during implementation, condition not met** should be
  written here instead if the planner's decision preserves a gold cost with an identical, undocumented-
  today informal cost of 50 (i.e. no *new* documented law is needed) — this bullet is conditional on
  which side of AC #4 the planner picks and is left in Format 1 per the project's own
  conditional-bullet convention (`TCK-20260829-DOC-COVERAGE-CONDITIONAL-BULLET-BLIND-DOD-BLOCKED`)
  until the implementer resolves it.
- `docs/simulation/social_systems_contract.md`: **only if** the planner routes Teaching through
  `SocialAppraisalSystem.appraise_contract()` with a new `ContractKind.TEACH` (the
  AFFECTION-CONTRACT-GATE precedent's pattern) — the "Contract kinds" table (currently listing
  RECRUITMENT/LOAN/POSITION_SWAP/MERCHANT/TEAM_UP/PAID_INFORMATION) would need a new row per that
  doc's own checklist. If the planner instead inlines the threshold formula without a new
  `ContractKind`, this bullet should be marked "Resolved during implementation, condition not met."
  Left in Format 1 (conditional) per the same convention cited above, since the routing choice is
  explicitly not resolved by this investigation.

The `docs/mechanics/01_entity_anatomy.md` chapter (path: `docs/mechanics/01_entity_anatomy.md`,
under `docs/mechanics/`) is not required to change: it covers core attributes/derived
stats/biological pressures/XP scaling, none of which this ticket touches — `IdentityComponent.
known_recipes`/`SocialBond.sentiment` are documented (to the extent they are) in
`docs/simulation/social_systems_contract.md`/economic-laws territory, not chapter 01.

The `docs/engine/authoritative_pipeline.md` contract (path: `docs/engine/authoritative_pipeline.md`,
under `docs/engine/`) is not required to change: moving `IdentityUpdate(recipes_learned=...)` from a
`ResourceTransferIntent`-nested contingent update to a directly-set `EntityUpdate.identity` field
changes *which existing, already-documented field* carries the mutation, not the pipeline's phase
sequence or the resolver contract itself — `execute_allocate_ap()` already emits `EntityUpdate.identity`
directly today with no dedicated engine-contract callout, confirming this is not a new pipeline
concept requiring documentation.

The `docs/parity_ledger/*.yaml` files are covered separately under Parity Ledger Overlap below —
no entry exists yet for `execute_train`/`TRAIN_COST`/teaching-on-trust, so any update there is a new
entry, not a modification of an existing one; see that section for the specific new-entry
recommendation (not itself a "doc to update," since it's a new addition the planner/parity-updater
will create, consistent with how the AFFECTION-CONTRACT-GATE precedent added SOC-249/250/251 rather
than listing them as pre-existing docs to touch).

## Parity Ledger Overlap

**No existing parity ledger entry covers `execute_train()`, `TRAIN_COST`, or `recipes_learned`/
`known_recipes` via the training action specifically.** Confirmed via targeted grep across all
`docs/parity_ledger/*.yaml`:
- `docs/parity_ledger/town_resource.yaml:1056` (`TOWN-102`, "Training that increments an attribute
  immediately recomputes derived stats") is about **attribute-point** training
  (`execute_allocate_ap`, `core_actions.py:295-324`) — a different mechanism (spending unspent AP on
  strength/vitality), not skill/recipe training via `execute_train`/`CLASS_HALL`. Do not conflate
  the two when checking for existing coverage.
- `docs/parity_ledger/strategic_cognition.yaml:3368` (`STRAT-253`) mentions `TRAIN_SKILL` only as one
  of 9 `RouteFamily` names given mapper-level-only shadow-parity verification for the (now-deleted)
  `AdventureDecisionPhase` migration — an AI-goal-routing concern upstream of `execute_train()`
  itself, not the action's own appraisal/economics. Not directly overlapping this ticket's scope,
  but flagged: if Teaching becomes a genuine two-party mechanism, whatever route-to-project mapping
  currently proposes `TRAIN_SKILL`/`ProjectKind.TRAINING` (`src/core/strategic.py:174`) may need to
  know a target/teacher now exists — out of this ticket's stated scope (no AC requires AI-side
  wiring), but a real downstream consumer to be aware of.
- No `docs/parity_ledger/social_narrative.yaml` entry references `execute_train`, `ClassHallAction`,
  or a teach/train `ContractKind` — confirmed via `grep -in train docs/parity_ledger/social_narrative.yaml`
  returning zero relevant hits (one unrelated substring match on "constraints").

**This ticket will need at least one new P0 parity ledger entry** (not an amendment) once
implemented, e.g. in `docs/parity_ledger/social_narrative.yaml` (if routed through
`appraise_contract()`) or `docs/parity_ledger/town_resource.yaml` (if scoped as an economy-action
change) — the planner should decide which shard based on the routing decision, and it requires a real
`test_path` per the Authoritative Mechanics Rule's P0 requirement. No existing entry is broken by this
ticket unless the planner also chooses to touch `TOWN-102` (attribute training) or `STRAT-253`
(route mapper) — neither is required by the current AC set.

## Prior Work

- **`stored_artifacts/TCK-20260824-AFFECTION-CONTRACT-GATE/`** (read in full) is the ticket the
  Request Summary explicitly cites as reusable precedent. It generalized
  `SocialAppraisalSystem.appraise_contract()`'s kind-dispatch to add `MERCHANT`/`TEAM_UP`/
  `PAID_INFORMATION`, established the "shared prelude untouched, one new `elif` branch + one new
  `_appraise_<kind>` static method per consumer" pattern, and the "transient, non-persisted
  `ContractState` built purely to call `appraise_contract()`" pattern (`execute_recruit`'s
  `temp_contract`, mirrored by `execute_team_up`/`execute_trade`/`PaidInformationTransactionSystem.
  enforce()`). Its own Out of Scope / Anti-Drift Hazards explicitly warn against widening
  `ContractService.get_project_mapping()`'s tier-5 materialization coverage — this ticket's own Out
  of Scope line already inherits that guard verbatim for a hypothetical `ContractKind.TEACH`.
  Its "Docs Requiring Update" section is the direct template for this investigation's own
  conditional-bullet handling (Format 1 + "Resolved during implementation, condition not met") for a
  doc dependent on an implementation-time routing choice.
- `docs/brainstorm/design_merit_scorecard.html:369-377` (idea "6. Teaching on trust") and
  `docs/brainstorm/rpg_feature_atlas.html:2017-2025` (idea 6, "Build teaching on trust, not new
  state") are this ticket's originating design source. The atlas's own framing: "`execute_train` is
  already a real, gold-and-location-gated action that grants a skill... Combine them: let a
  skill-holding entity teach a sufficiently-trusted party member directly, **gated on an existing
  trust threshold instead of gold**." This phrasing ("instead of") leans toward gold-replacement in
  the *original* design intent, but the ticket's own Scope explicitly reopens this as an unresolved
  decision requiring an explicit planner call rather than silently following the atlas's phrasing —
  presented here as evidence for the planner to weigh, not as a resolution. Note the atlas's
  "location-gated" claim was not corroborated by direct code read of `execute_train()` (no location/
  position check exists in the function today) — a minor doc-vs-code inaccuracy in the atlas, not
  this ticket's concern to fix.
- `core_actions.py:55-144` (`execute_recruit`) and the AFFECTION-CONTRACT-GATE-added
  `execute_team_up`/`execute_trade` are the closest structural precedents for a two-party action
  handler returning a `Dict[int, EntityUpdate]` keyed by both `entity.id` and `target_id`.

## Risks and Open Questions

**Open question 1 (ticket's own central open question, not resolved here) — does trust replace
TRAIN_COST entirely, or gate alongside it?** Evidence for replacement: (a) the atlas's originating
design language explicitly says "instead of gold"; (b) the 50-gold check is not actually enforced as
a hard affordability gate today (always accepted, gold merely clamped to 0) — so the *existing*
economic gate is weaker than it appears, undercutting the case that removing it breaks a load-bearing
conservation invariant; (c) `CLASS_HALL` is an untracked abstract sink, so Chapter-3 atomic
conservation for *tracked* objects is not implicated either way. Evidence for gating alongside:
(a) gold is still deducted and clamped correctly when present, so *some* real economic effect exists
today, however weakly enforced; (b) `test_class_hall_train_refactor` and `test_class_hall_training`
both currently assert on the exact gold-delta arithmetic (`100→50`, `60→10`), so a silent removal
without updating those assertions (or without an explicit decision to leave `ClassHallAction.train()`
as the gold-only path and `execute_train()` as the new trust-gated path) is likely to produce a
regression or an inconsistent two-path economy. **This investigation surfaces both sides but does not
decide — the ticket's own AC #4 requires the planner to make and state the explicit decision.**

**Open question 2 — full `appraise_contract()`/new `ContractKind.TEACH` routing vs. inline threshold
reuse.** The ticket's Scope text is compatible with either reading (see Current Behavior section
above). The full-routing option is more consistent with the immediately-cited precedent
(AFFECTION-CONTRACT-GATE) and gets `docs/simulation/social_systems_contract.md`'s own "how to add a
kind" checklist for free, but requires a new `ContractKind` member and a `_appraise_teach`/similar
static method. The inline-formula option is a smaller diff (two thresholds copied, no new enum
member, no `ContractState` construction) but diverges from the precedent's own established pattern
and would leave the shared gate literally duplicated in two places rather than reused through one
function. The ticket's own Out of Scope line ("even if a new `ContractKind.TEACH` is introduced")
suggests the ticket author already anticipated the full-routing option as the likely outcome, but
does not commit to it. **Not resolved here — planner must record the choice explicitly.**

**Open question 3 — which entity is the teacher/actor, which is the target/student?** Not stated
explicitly in the ticket. The precedent-consistent mapping (Current Behavior section above) is:
`entity` = teacher/initiator, `payload["target_id"]` = student, and the student appraises the
teacher's trustworthiness (mirroring `execute_recruit`'s `appraise_contract(target, temp_contract,
context)` call, where the *target* evaluates the *offer*). If a different mapping is intended (e.g.
the student initiates a "request to be taught" action instead), the appraisal call's argument order
and which side's `EntityUpdate` carries `recipes_learned`/blocker-resolution flips accordingly. Must
be made explicit in plan.md, not left implicit in code.

**Risk — regression surface for the existing integration test.** `test_resource_v2_boundary.py::
test_class_hall_train_refactor` calls `SimulationDomainLogic.execute_action(hero, payload={"action":
"TRAIN", "skill_id": "STRIKE"})` with a single entity and no target — this call shape will not
compile/pass against a signature requiring a teacher+target pair unless either (a) a `target_id` is
added to the payload and the test is updated to construct two entities, or (b) the redesigned
`execute_train()` preserves a self-training fallback path when no target is given (not requested by
any AC, and would contradict AC #1's "gated on trust between them" framing for a solo entity with no
counterparty). Planner should treat this test as required regression surface to explicitly update, not
silently leave broken.

**Risk — orphaned duplicate `ClassHallAction.train()`.** Not in the ticket's Related Code Areas.
Left untouched, it will describe an economically-inconsistent, ungated (gold-only, no trust) "shadow"
version of training that no code path currently invokes but that a future re-wiring attempt could
resurrect with stale semantics. Flagged as a real but explicitly out-of-scope-unless-the-planner-says-
otherwise risk, not something this investigation resolves.

## Anti-Drift Hazards

- **Do not modify the shared trust-score prelude's hard-cancel thresholds** (`0.2` `TOTAL_DISTRUST`,
  `0.4`-with-betrayal `BETRAYAL_HISTORY`, `-0.8` sentiment) in `appraisal.py:19-54` while adding
  Teaching's consumer — these are covered by P0 parity entries (SOC-001/SOC-008/SOC-134) with real
  passing tests, per the AFFECTION-CONTRACT-GATE precedent's own Anti-Drift Hazards, which apply
  identically here.
- **Do not widen `ContractService.get_project_mapping()`'s tier-5 goal materialization coverage**
  even if `ContractKind.TEACH` is introduced — explicit ticket Out of Scope line, inherited verbatim
  from the AFFECTION-CONTRACT-GATE precedent's own guard.
- **Do not silently touch `src/town/class_hall.py`'s `ClassHallAction.train()`** as a shortcut to
  "fixing" the affordability-check gap noted above, unless the planner explicitly decides this ticket
  also consolidates or retires the duplicate — that is a separate architectural cleanup, not implied
  by any AC.
- **Do not conflate `ProjectKind.TRAINING`** (`src/core/strategic.py:174`, the strategic-project kind
  that may lead an entity to *choose* to pursue training as a goal) **with the `execute_train()`
  action itself** — they are different layers (strategic intent vs. domain action execution); this
  ticket's scope is the action layer only, per its Related Code Areas.
- **Preserve `execute_allocate_ap`/`execute_repair`/`execute_interact`/`execute_survival`/
  `execute_recruit` unchanged** — none are in scope; only `execute_train()` (and possibly
  `action_router.py`'s TRAIN dispatch line, if the payload shape gains a `target_id`) should change.
- **Determinism**: if any new logic iterates `target.strategic.blockers` or `target.social.bonds`,
  preserve the existing plain-filter (non-selection) pattern `execute_train()` already uses — do not
  introduce dict-iteration-order-dependent behavior where none exists today.
