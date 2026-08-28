---
status: historical
layer: systems
authority: P2
audience: agent
ticket_id: TCK-20260824-AFFECTION-CONTRACT-GATE
artifact_type: investigation
tags: [social, information]
---

# Investigation — TCK-20260824-AFFECTION-CONTRACT-GATE

## Current Behavior

**Note on tool availability:** `mcp__knowledge-search__search_docs` and the
`tools/knowledge_search.py` fallback both returned "index not found" for this session (confirmed
pre-existing environment gap, not retried further). Per the ticket's own Step 0c instruction,
`graphify query "appraise_contract ContractKind ContractStatus SocialAppraisalSystem"` and
`graphify query "PaidInformationTransactionSystem ResourceTransferIntent"` were run first and used
to identify primary file targets (`src/core/strategic.py`, `src/systems/social_systems/appraisal.py`,
`src/engine/pipeline_phases/paid_information.py`, `src/systems/social_systems/contracts.py`,
`src/ai/goals/social_contract_scorer.py`) before any grep/file read.

### `SocialAppraisalSystem.appraise_contract()` — `src/systems/social_systems/appraisal.py:19-72`

The existing shared trust/gate formula, exactly as the ticket describes reusing:

1. **Trust score** (`appraisal.py:39-45`): if `entity.social.bonds.get(source_id)` exists (a
   `SocialBond`), `trust_score = (bond.sentiment + 1.0) / 2.0` — private sentiment takes priority.
   Otherwise, blended fallback: `public_trust * 0.7 + history_trust * 0.3`, where
   `public_trust = source_entity.social.public_reputation / 2.0` and `history_trust =
   entity.social.trust_history.get(source_id, 0.5)`.
2. **Hard-cancel gates** (`appraisal.py:48-54`, shared across ALL kinds before kind dispatch):
   `trust_score < 0.2 OR (bond and bond.sentiment < -0.8)` → `(CANCELLED, TOTAL_DISTRUST, {})`;
   `entity.social.betrayal_count > 0 AND trust_score < 0.4` → `(CANCELLED, BETRAYAL_HISTORY, {})`.
3. **Kind dispatch** (`appraisal.py:56-72`): `if contract.kind == ContractKind.RECRUITMENT:` →
   `_appraise_recruitment`; `elif ContractKind.LOAN:` → `_appraise_loan` (wrapped to
   `(ACCEPTED|CANCELLED, reason, {})`); `elif ContractKind.POSITION_SWAP:` →
   `_appraise_position_swap`. **No branch exists for `ContractKind.PROTECTION` or
   `ContractKind.MERCHANT`** — both fall through to the final `return ContractStatus.CANCELLED,
   ReasonCode.UNKNOWN, {}` at line 72. This is the exact "fallthrough to default CANCELLED/UNKNOWN"
   the ticket's AC forbids for the 3 new consumers, and it is happening *today* for MERCHANT.

### `_appraise_recruitment()` hard-cancel pattern — `appraisal.py:74-142` (the pattern to mirror)

Signature: `_appraise_recruitment(entity: EntityState, contract: ContractState, trust_score: float)
-> Tuple[ContractStatus, ReasonCode, Dict[str, Any]]` (static method, takes the already-computed
`trust_score` from the caller rather than recomputing it).

Concretely, "hard-cancel" means: multiple early `return ContractStatus.<X>, ReasonCode.<Y>, {}`
statements that terminate evaluation immediately once a disqualifying condition is met, *before*
reaching the weighted-score/haggling logic at the bottom. In this function specifically:
- Line 89-90: `trust_score >= 0.9 and fatigue_penalty < 0.2` → immediate `ACCEPTED` (loyalty fast-path).
- Line 111-113: `"GREEDY" in traits and utility < 1.0` → immediate `CANCELLED, INSUFFICIENT_INCENTIVE`.
- Line 119-120: `risk == "HIGH" and hp_pct < 0.5` → immediate `FAILED, LOW_HP_RETREAT`.
- Falls through to a weighted `score = trust*0.4 + utility*0.4 - risk_weight*0.2 - fatigue` at
  line 128, with `>= 0.5` → ACCEPTED, `>= 0.3` (and negotiation budget available) → COUNTERED
  (haggling), else → `CANCELLED, INSUFFICIENT_INCENTIVE`.

The shared helper the ticket asks for should follow this same shape: accept a `ContractKind`, run
the shared trust/hard-cancel prelude (already factored out at the top of `appraise_contract()`),
then dispatch to a kind-specific hard-cancel-then-score body, returning
`(ContractStatus, ReasonCode, Dict[str, Any])` — never falling through to the generic
`UNKNOWN`/`CANCELLED` default for a kind that is supposed to be handled.

### `ContractKind` / `ContractStatus` — `src/core/strategic.py:59-83`

```python
class ContractStatus(str, Enum):
    OFFERED = "OFFERED"; ACCEPTED = "ACCEPTED"; COUNTERED = "COUNTERED"; ACTIVE = "ACTIVE"
    FULFILLED = "FULFILLED"; COMPLETED = "FULFILLED"  # alias
    FAILED = "FAILED"; BETRAYED = "BETRAYED"; EXPIRED = "EXPIRED"; CANCELLED = "CANCELLED"

class ContractKind(str, Enum):
    RECRUITMENT = "RECRUITMENT"
    LOAN = "LOAN"
    PROTECTION = "PROTECTION"
    MERCHANT = "MERCHANT"
    POSITION_SWAP = "POSITION_SWAP"
```

**`ContractKind.MERCHANT` is declared but unhandled today** — confirmed via targeted grep. It is
referenced in exactly three places outside its own declaration, and none of them appraise or act on
it as a live trade contract:
- `src/systems/social_systems/contracts.py:142` — `ContractService.get_project_mapping()`'s
  docstring/logic explicitly excludes it: `"Returns None for PROTECTION/MERCHANT/POSITION_SWAP --
  do not widen this coverage"`.
- `src/ai/goals/social_contract_scorer.py:31` — same 3-of-5 exclusion, mirrored comment.
- `tests/unit/ai/goals/test_social_contract_goal_scorer.py:124` — a regression test asserting
  `PROTECTION, MERCHANT, POSITION_SWAP` never spawn a project via the scorer.

Separately, `InformationProviderArchetype.MERCHANT` (`src/domains/information/providers.py:31`) is
an unrelated enum on a different class (archetype of an information seller, not a contract kind) —
same string value, no code-level relationship to `ContractKind.MERCHANT`. Do not conflate the two
when scoping Trade.

**No `TEAM_UP` or equivalent `ContractKind` exists.** Confirmed via `grep -rn -i "TEAM_UP\|team-up\|
team_up" src/ tests/` returning zero hits in source or test code — every hit is in
`docs/brainstorm/*.html` design-analysis pages describing the gap itself (e.g.
`rpg_simulation_wiring_map.html:479`: `"Team-Up Invite/Accept<br/>DOESN'T EXIST — AI silently
composes groups"` and `:562`: `"GroupPhase.resolve() contains no request/invite/accept step"`).
This is genuinely new mechanism work: there is no existing `execute_team_up`-style action handler,
no `ContractKind.TEAM_UP`, and no wiring anywhere in `src/systems/social_systems/party_composition.py`
(read in full — `PartyCompositionScorer` only *scores* candidate pools for `FORM_PARTY`; it has no
contract/invite/accept surface at all) or `src/engine/domain/core_actions.py` (read in full — no
`execute_team_up`/`execute_recruit_ally`-style handler exists; only `execute_recruit`,
`execute_allocate_ap`, `execute_train`, `execute_repair`, `execute_interact`, `execute_survival`).

**Paid-Information currently has no `ContractKind` at all** — `PaidInformationTransactionSystem`
(`src/engine/pipeline_phases/paid_information.py:74-183`) is driven entirely by
`ProjectKind.INFORMATION_SEEKING` + `AuthoritativeState.information_providers`, never by a
`ContractState`. `enforce()` iterates alive entities with an active `INFORMATION_SEEKING` project,
finds the lowest-`entity_id` non-self provider (line 109-116, **zero eligibility/willingness
check** on the provider side), computes `cost = 10 / max(0.1, reliability)`, and unconditionally
appends a `ResourceTransferIntent(source_kind="INFORMATION_PURCHASE", gold_cost=cost, ...)` to the
seeker's entity update (line 151-166) — exactly the "emits unconditionally, zero check today" the
ticket describes. Gating this on the shared helper therefore requires either (a) synthesizing a
transient `ContractState(kind=ContractKind.PAID_INFORMATION or similar, ...)` inline (mirroring how
`CoreActions.execute_recruit()` builds a `temp_contract` at `core_actions.py:85-93` purely to call
`appraise_contract()`, never persisting it), or (b) calling the new helper's underlying scoring logic
directly without a `ContractState` wrapper. Either way this is new `ContractKind` surface — no
existing kind fits.

### `SocialBond` / affection field — `src/core/models/social.py:13-20`

```python
@dataclass(frozen=True, slots=True)
class SocialBond:
    target_id: int
    familiarity: float = 0.0   # 0.0 to 1.0
    sentiment: float = 0.0     # -1.0 to 1.0  (Bias/Liking)
    last_interaction_tick: int = 0
    role: RelationshipRole = RelationshipRole.NEUTRAL  # NEUTRAL/FRIEND/RIVAL
```

**No field named `affection` exists anywhere in `src/` or `tests/`** — confirmed via
`grep -rn -i "affection" src/ tests/` returning zero hits (the word appears only in
`docs/brainstorm/*.html` design pages, e.g. `rpg_simulation_wiring_map.html:541`: "Affection &
Relationship Bonds ... Directed `SocialBond` per target entity: sentiment and familiarity ... Live",
already treating `sentiment`/`familiarity` as the de facto affection concept). `sentiment` is the
closest existing field: range -1.0 to 1.0 ("Bias/Liking"), already the exact quantity
`appraise_contract()` reads as `trust_score` via `(bond.sentiment + 1.0) / 2.0`, and already the field
every downstream consumer (`PartyCompositionScorer.score_trust_bonds()`,
`SocialContractGoalScorer._raw_score()`) treats as the "how much does this entity like that entity"
signal. `familiarity` (0.0-1.0, "interaction depth") is a distinct concept — not a candidate
substitute for affection. No other `SocialComponent`/`SocialBond` field carries an "affection"-shaped
meaning; the realistic choices are (1) reuse `sentiment` as-is, or (2) add a new named field. See
Risks and Open Questions — this investigation surfaces the evidence but does not decide.

### `PartyCompositionScorer` — `src/systems/social_systems/party_composition.py` (read in full)

Pure static scorer, no contract/appraisal surface. `score_trust_bonds()` (line 128-140) already
reads `actor.social.bonds.get(candidate.id).sentiment` (bond-priority-else-`trust_history`, same
precedence rule as `appraise_contract()` — explicitly cross-referenced in its own docstring at
line 118-121). This is precedent for reusing `sentiment`, but it is a *scoring* term, not a
threshold *gate* — it never hard-cancels a FORM_PARTY action the way `appraise_contract()`
hard-cancels a contract. Team-Up (per the ticket's scope) is understood as a distinct mechanism from
`FORM_PARTY`/`PartyCompositionScorer` — the ticket asks for a new contract-based gate, not a change
to this scorer.

### `SocialContractGoalScorer` — `src/ai/goals/social_contract_scorer.py` (read in full)

Scores `ACTIVE` contracts (post-acceptance) for tier-5 `GoalRegistry` competition — a downstream
consumer of *already-accepted* contracts, not part of the OFFERED→ACCEPTED gate this ticket builds.
`get_project_mapping()` in `contracts.py:136-150` explicitly returns `None` (no project spawned) for
PROTECTION/MERCHANT/POSITION_SWAP — "do not widen this coverage" per its own docstring, referencing
`plan.md Scope Guards` from TCK-20260811-SOCIAL-CONTRACT-GOAL-SCORER. **This scorer's exclusion list
is a separate, downstream concern from this ticket's appraisal-gate scope** — adding new
`ContractKind` values for Team-Up/Paid-Information does not by itself require widening
`get_project_mapping()`; that is out of scope unless a new AC requires it (none currently does).

### `ContractService` (`src/systems/social_systems/contracts.py`, read in full)

`get_project_mapping()` (line 136-150) is the "2 of 5 kinds spawn a project" boundary — orthogonal
to appraisal but documents the existing 5-member `ContractKind` enum's asymmetric handling
elsewhere in the codebase (a second place where MERCHANT/PROTECTION/POSITION_SWAP are deliberately
excluded, distinct from `appraise_contract()`'s fallthrough gap). `create_loan_contract()` /
`create_recruitment_contract()` are the existing factory-method pattern for constructing a
`ContractState` — no equivalent factory exists for MERCHANT/PROTECTION/POSITION_SWAP or any new kind.

## Mechanics / Engine Constraints

- **`docs/mechanics/04_strategic_cognition.md`** governs goal hierarchy/interruption resistance —
  read for tier-5 `GoalRegistry` context. It documents `SocialContractGoalScorer` as one of four live
  tier-5 candidates (line 30) and the `§7.2 Trust/Bonds-Aware Adjustment` formula for
  `PartyCompositionScorer` (line 734-754), including the exact "bond takes priority over
  trust_history" rule this ticket's shared helper must preserve. It does **not** currently document
  `SocialAppraisalSystem.appraise_contract()`'s own trust/hard-cancel formula as a chapter-level law
  — that formula's authoritative doc home is `docs/simulation/social_systems_contract.md` (a
  `docs/simulation/` contract doc, not a Mechanics Bible chapter). No chapter-04 law is violated by
  generalizing `appraise_contract()`; the ticket's helper must continue to honor the existing
  "private sentiment overrides public, hard-reject below 0.2 trust or -0.8 sentiment, betrayal
  history compounds distrust" law wherever it fires for the 3 new consumers.
- **Determinism / Durable State Rule** (project CLAUDE.md): the shared helper must stay a pure,
  read-only appraisal function (mirrors `appraise_contract()`'s existing shape — reads `EntityState`/
  `AuthoritativeState`, returns a status/reason/terms tuple, never mutates). Any new durable
  `ContractKind` value is a typed enum addition (already the correct durable-state shape — no ad hoc
  string/dict encoding needed). Gating `PaidInformationTransactionSystem.enforce()` must not begin
  authoritatively mutating state inside the decision-only pipeline phase — it must continue emitting
  `ResourceTransferIntent`/`StateUpdate` objects for the authoritative apply path to resolve, exactly
  as it does today (`paid_information.py`'s own docstring: "No durable state is mutated here").

## Docs Requiring Update

- `docs/simulation/social_systems_contract.md`: its "Contract kinds" table (lines 39-43) lists only
  RECRUITMENT/LOAN/POSITION_SWAP special logic and is silent on MERCHANT (already declared) and any
  new TEAM_UP/PAID_INFORMATION-equivalent kind this ticket adds; its own guidance at line 191
  ("To add a new contract kind: add to `ContractKind` enum, implement an appraisal method in
  `SocialAppraisalSystem`, add breach conditions in `contracts.py`, add tests") is the exact checklist
  this ticket's implementation must follow, and the table must be extended to describe the new
  helper's generalized shape.
- `docs/parity_ledger/social_narrative.yaml`: ticket scope explicitly requires updating "existing
  verified appraise_contract() entries" — see Parity Ledger Overlap below for the specific IDs
  (SOC-001, SOC-002, SOC-008, SOC-134, SOC-141, SOC-199, SOC-204/205/206/207, SOC-217, SOC-244) whose
  `v2_evidence` describes `appraise_contract()`'s current (pre-generalization) behavior/kind coverage
  and will no longer accurately describe the function once it dispatches through a shared
  multi-consumer helper with new kinds.
- `docs/mechanics/04_strategic_cognition.md`: **Resolved during implementation, condition not met —
  this doc does not need updating.** plan.md scoped Team-Up as appraisal-only, mirroring
  `execute_recruit()`'s pattern: `CoreActions.execute_team_up()` builds and appraises a
  `ContractKind.TEAM_UP` contract directly (verified in the real diff of
  `src/engine/domain/core_actions.py`/`action_router.py` — no `GoalRegistry`/tier-5 reference
  anywhere in it). No new tier-5-candidate row was needed, so this doc was correctly left untouched.
  (Confirmed independently by the top-level orchestrator, not just the implementer, before closing
  this ticket — see `TCK-20260827-PLAN-GATE-HEADING-CONTENT-BLIND-FALSEPOS`'s sibling tooling gap:
  `docs_to_update_coverage`'s static checker does literal path-diff matching and has no way to know a
  conditional bullet like this one was evaluated and resolved as "not applicable" rather than simply
  forgotten — worth its own small follow-up tooling ticket alongside that one.)

The `docs/mechanics/01_entity_anatomy.md` chapter (path: `docs/mechanics/01_entity_anatomy.md`,
under `docs/mechanics/`) is not required to change for this ticket: `SocialBond`/`SocialComponent`
are documented (if at all) as part of the social systems contract doc above, not chapter 01's
entity-anatomy scope (core attributes/derived stats/biological pressures/XP), and this ticket does
not touch attribute or XP formulas regardless of whether `sentiment` is reused or a new `affection`
field is added.

The `docs/engine/authoritative_pipeline.md` contract (path: `docs/engine/authoritative_pipeline.md`,
under `docs/engine/`) is not required to change: gating `PaidInformationTransactionSystem.enforce()`
on the shared helper's outcome changes *when* a `ResourceTransferIntent` is emitted, not the
37-phase pipeline sequence, phase ordering, or the resolver contract itself — the phase remains
decision-only, still emits the same intent shape through the same apply path.

## Parity Ledger Overlap

All entries below are `docs/parity_ledger/social_narrative.yaml` — the only parity ledger file this
ticket's scope overlaps (no `combat_movement.yaml`/`strategic_cognition.yaml`/`town_resource.yaml`
overlap identified; Team-Up/Trade route through social contracts, not combat/town resource systems,
and Paid-Information's own parity entry, if any, would be in `infrastructure.yaml` for the
information-seeking pipeline rather than here — not found by name in this investigation, flag for
planner to re-check `infrastructure.yaml`/`strategic_cognition.yaml` for an `INFORMATION_PURCHASE`-
specific entry beyond what's covered below).

Entries whose `v2_evidence` cites `appraise_contract()`/`_appraise_recruitment` directly (all
`status: verified`, `priority: P0` — **P0 requires a passing `test_path` after this ticket's
changes**):
- **SOC-001** (line 1-14): "Private betrayal history can override public recruiter reputation" —
  cites `appraisal.py` lines 47-54 by exact line number. `test_path`:
  `tests/unit/social/test_betrayal_consequence.py::test_betrayal_trauma_blocks_recruitment`.
- **SOC-002** (line 15-26): "Social learning updates familiarity/trust-like bonds" — cites
  `recalibrate_trust`/`update_familiarity`. `test_path`: `tests/unit/social/test_source_trust.py`,
  `tests/unit/social/test_social_bonds.py`.
- **SOC-008** (line 93-105): "Recruitment evaluates trust, debt, greed, capability fit, and prior
  trauma" — cites `appraise_contract`/`_appraise_recruitment` directly. `test_path`:
  `tests/unit/social/test_recruitment.py`,
  `tests/unit/social/test_betrayal_consequence.py::test_betrayal_trauma_blocks_recruitment`.
- **SOC-134**: "public_reputation ... informs contract appraisal trust" — cites `appraise_contract`'s
  exact trust-blend formula and the 0.2 TOTAL_DISTRUST threshold by name.
- **SOC-141**: "narrative-informed social appraisal" (`test_social_appraisal_with_narrative`) — no
  `test_path` recorded (null) despite `status: verified`; flag as a pre-existing parity-ledger gap,
  not introduced by this ticket.
- **SOC-199-SOC-218 block** (lines 2102-2306, `Contract offer has recruiter/founder` through
  `Social appraisal is bounded by social bandwidth/cognition`): all `status: verified`,
  `priority: P0`, mostly `v2_evidence: "Implementation proven via exhaustive checklist audit
  Phase 1-11"` with no `test_path`. Of particular relevance: **SOC-204** "Contract appraisal uses
  trust/private bond", **SOC-205** "uses greed or reward preference", **SOC-206** "uses
  capability/role fit", **SOC-207** "uses prior trauma/betrayal", **SOC-217** "Social updates are
  authoritative updates, not direct mutation during appraisal" (a durable-state-rule constraint the
  new helper must also satisfy), **SOC-215** "Contract outcome can affect future recruitment
  decisions", **SOC-216** "Contract outcome can affect strategic directives". None currently name
  MERCHANT/TEAM_UP/PAID_INFORMATION — this ticket either needs new entries for the 3 new consumers'
  appraisal coverage, or an update to these existing entries' scope language to state they now cover
  a shared multi-kind helper, not recruitment-only.
- **SOC-244**: `PartyCompositionScorer.score()`'s trust/bonds term — explicitly cross-references
  "the same rule documented for `SocialAppraisalSystem.appraise_contract()`". Should be checked for
  consistency if the shared helper changes the bond-priority-else-trust_history precedence in any way
  (ticket scope says reuse the formula as-is, so likely unaffected, but flag for the planner to
  confirm no incidental formula drift).

No `test_path` currently exercises MERCHANT/TEAM_UP/PAID_INFORMATION contract appraisal — new P0
entries (or amended existing ones) will need a real `test_path` once this ticket implements them,
per the Authoritative Mechanics Rule's "P0 entries require a passing test_path" requirement.

## Prior Work

- **`stored_artifacts/TCK-20260811-RELATIONSHIP-AWARE-FORM-PARTY/`**: added the
  `score_trust_bonds`/`TRUST_BONUS_WEIGHT` term to `PartyCompositionScorer`, establishing the
  "bond.sentiment-priority-else-trust_history.get(id, 0.0)" precedent explicitly cross-referenced by
  both `party_composition.py`'s own docstring and `docs/mechanics/04_strategic_cognition.md §7.2`.
  Directly relevant precedent for how to reuse `sentiment` consistently across a new consumer without
  re-deriving the formula.
- **`stored_artifacts/TCK-20260811-SOCIAL-CONTRACT-GOAL-SCORER/`**: added `GoalKind.SOCIAL_CONTRACT`
  and `SocialContractGoalScorer`, and is the most directly relevant prior-work precedent for this
  ticket's own Design Decisions: (a) it explicitly chose calibration onto the existing `2.9`
  (`_ADVENTURE_ROUTE_SCORE_MAX`) ceiling rather than extending `_score_scale_max()`/`ProjectState`
  with new provenance fields — the same "reuse the existing scale, don't add new durable-state
  classification fields" instinct likely applies to this ticket's helper; (b) it discovered and
  disclosed that `CoreActions.execute_recruit()` is a live production path bypassing
  `ContractService.accept_contract()` entirely — directly relevant since `execute_recruit()` is the
  existing pattern for "construct a temp `ContractState`, call `appraise_contract()`, branch on the
  result" that Team-Up/Trade will likely need to mirror; (c) `plan.md`'s "Design Decision #7"
  (avoiding a duplicate-project hazard) is a cautionary precedent if this ticket's helper is wired
  into tier-5 materialization for any of the 3 new consumers.
- `core_actions.py:80-144` (`execute_recruit`) is itself the closest existing end-to-end example of
  "gate an action on `appraise_contract()`'s outcome, branch ACCEPTED vs. else" — the pattern the
  ticket's Team-Up (and possibly Trade) consumer should structurally mirror, including the
  `resource_transfers`/`group_id`/`StrategicUpdate(contracts_add_or_update=[contract])` bundling
  shape for the ACCEPTED branch and the `rejection_increment`/`last_offer_tick_set` bookkeeping for
  the rejected branch.

## Risks and Open Questions

**Decision 1 — `affection` field: reuse `sentiment` vs. new field (ticket AC, unresolved).**
Confirmed no `affection` field exists in `src/` today. `SocialBond.sentiment` (-1.0 to 1.0,
"Bias/Liking") is the only existing field carrying that meaning, already read by
`appraise_contract()`, `PartyCompositionScorer.score_trust_bonds()`, and
`SocialContractGoalScorer._raw_score()` for materially the same "how much does this entity like that
one" purpose. No other `SocialBond`/`SocialComponent` field is a plausible alternate carrier.
Evidence favors reuse (cheapest, zero new durable-state surface, consistent with 3 existing
consumers already treating `sentiment` this way) — but this investigation does not decide; the
planner must record this as an explicit Design Decision. If a new named field is chosen instead, it
requires: a new `SocialBond` dataclass field, a new `SocialBondUpdate` delta field
(`src/core/updates.py`), an apply-path write in `RelationshipService.process_update()` (referenced at
`party_composition.py:117-121` but not itself read this session — planner must confirm its exact
location/shape before committing to this option), and update-model tests. This is materially more
work than reuse and no ticket-referenced consumer requires a value distinct from `sentiment`.

**Decision 2 — narrow-3-consumers vs. anticipate M6 ideas 39/40 (ticket AC, unresolved, explicitly
flagged open in the epic itself).** `docs/plans/rpg_design_roadmap/rpg_m1_quick_wins_epic.md`'s own
"Open Questions" section (line 150-153) states verbatim: *"Should idea 13's shared threshold-gate
helper be built to already anticipate M6's ideas 39/40 consumers, or built minimally for its own
three consumers (Team-Up/Trade/Paid-Info) and extended later? Leaning toward anticipating it, since
the shape is already fully specified in Shared Implementation Opportunities — but not decided here."*
`docs/brainstorm/rpg_feature_atlas.html`'s "Shared Implementation Opportunities" section names this a
**6-idea, 3-milestone cluster**: `appraise_contract()`'s threshold formula is "already named as a
shared precedent for Conversation, idea 40 (Clan), and idea 39 (affiliation fealty) — idea 13
(Team-Up/Trade/Paid-Info) is a 4th/5th consumer of the same mechanism" (i.e. the 6 consumers are:
Conversation, Clan-succession(40), affiliation-fealty(39), Team-Up, Trade, Paid-Information — the
last 3 all under idea 13/this ticket). **Idea 25 (a structurally separate trust ledger) was
explicitly checked and rejected as part of this cluster** — confirming the ticket's Out of Scope
line. The atlas gives **no further shape detail** for idea 39/40's own eventual consumer beyond
"uses the same `appraise_contract()` threshold formula precedent" — no `ContractKind` names, no
`ReasonCode` values, no terms schema are specified anywhere in the atlas or epic doc for ideas 39/40.
This means "anticipating M6" can only mean designing the shared helper's *signature/extension shape*
generically enough (e.g. accept any `ContractKind`, dispatch via a lookup rather than an if/elif
chain hardcoded to exactly 3 new kinds) — there is no concrete M6 consumer behavior to build against
yet, and none should be speculatively implemented (ticket's own Out of Scope line: "does not
implement M6's consumers"). Planner must record which of the two postures is chosen and why; either
is defensible given the epic's own "leaning toward, not decided" framing.

**Open question — Team-Up materialization scope.** Unlike Paid-Information (retrofits a live
pipeline phase) and Trade (reuses a declared `ContractKind`), Team-Up has zero existing wiring of any
kind. The ticket's AC only requires the shared helper + routing through it + no-fallthrough — it does
not explicitly require a new `execute_team_up` action handler, a tier-5 goal-scorer, or pipeline
wiring into `GroupPhase.resolve()` (the actual group-formation pipeline phase referenced by the atlas
as where "AI silently composes groups" today — not read this session, out of the ticket's named
Related Code Areas, flag for planner). If Team-Up is scoped as "appraisal method + `ContractKind`
value exist and are exercised by unit tests" without a live call site, that mirrors
`ContractService.accept_contract()`'s own pre-TCK-20260811 state (defined, tested, not production-
wired) — a defensible, narrower interpretation the planner should make explicit rather than silently
assume either way.

**Open question — Paid-Information's contract-shape integration.** Because
`PaidInformationTransactionSystem.enforce()` has no `ContractState` today, gating it requires either
synthesizing a transient contract (mirroring `execute_recruit()`'s `temp_contract` pattern) or
exposing the helper's dispatch logic in a form callable without a `ContractState` wrapper (e.g. a
kind-parameterized appraisal function that accepts raw trust/terms inputs). The ticket's own Scope
line says the helper "accept[s] a ContractKind and return[s] (ContractStatus, ReasonCode, terms)" —
implying a `ContractState`-shaped call is expected, favoring the synthesize-a-transient-contract
approach for consistency with Team-Up/Trade, but this is a planner-level implementation decision, not
resolved here.

**Risk — parity ledger update precision.** The SOC-199 through SOC-218 block (20 entries) mostly
carries `v2_evidence: "Implementation proven via exhaustive checklist audit Phase 1-11"` with no
`test_path` and language written for recruitment-only appraisal ("Contract appraisal uses trust/
private bond" etc., singular framing). Updating these to reflect a generalized multi-kind helper
risks either under-updating (leaving stale recruitment-only language) or over-widening (claiming
verified coverage for MERCHANT/TEAM_UP/PAID_INFORMATION before real tests exist). Planner should
scope exactly which entries get amended vs. which get new sibling entries.

## Anti-Drift Hazards

- **Do not widen `ContractService.get_project_mapping()`'s coverage** (currently 2-of-5:
  RECRUITMENT/LOAN only) to include the new kinds unless a specific AC requires tier-5 project
  materialization for Team-Up/Trade/Paid-Information — its docstring and
  `test_social_contract_goal_scorer.py:124` both explicitly pin the PROTECTION/MERCHANT/POSITION_SWAP
  exclusion as intentional (TCK-20260811-SOCIAL-CONTRACT-GOAL-SCORER's own Scope Guards). Widening it
  incidentally would resurrect the exact duplicate-project/bandwidth hazard that ticket's Design
  Decision #7 fixed.
- **Do not modify the shared trust-score prelude's hard-cancel thresholds** (0.2 TOTAL_DISTRUST,
  0.4-with-betrayal BETRAYAL_HISTORY, -0.8 sentiment) while generalizing `appraise_contract()` — these
  are covered by P0 parity entries (SOC-001, SOC-008, SOC-134) with real passing tests; any numeric
  drift here is a parity break, not a refactor.
- **Do not conflate `InformationProviderArchetype.MERCHANT` with `ContractKind.MERCHANT`** — same
  string value, unrelated enums on unrelated classes. Trade's `ContractKind.MERCHANT` decision must
  not be confused with or accidentally coupled to the information-provider archetype system.
  Paid-Information gating logic must not accidentally key off `ContractKind.MERCHANT` — it needs its
  own kind (or an explicit decision that it reuses MERCHANT is out of scope per the ticket's own
  framing of Trade vs. Paid-Information as separate consumers).
- **`PaidInformationTransactionSystem.enforce()` remains decision-only** — do not introduce direct
  state mutation while adding the gate check; continue returning a `StateUpdate` with intents
  appended, exactly as today, so `ResourceTransactionResolver`/the authoritative apply path stays the
  sole mutation point (Chapter 03 conservation law, cited in the module's own docstring).
- **Do not change `PartyCompositionScorer`/`FORM_PARTY`'s existing trust-bonds *scoring* term** while
  building Team-Up's *gating* mechanism — they are different mechanisms (continuous scoring bias vs.
  hard threshold gate) per this investigation's own reading of `party_composition.py`, and the atlas's
  cluster analysis for a different pairing ("life-stage-gated eligibility", ideas 20/34) explicitly
  warns against merging structurally different mechanisms just because they sound similar.
- **Determinism**: any new provider/candidate selection logic added for Team-Up or Trade must
  preserve the existing deterministic-ordering pattern `PaidInformationTransactionSystem.enforce()`
  already uses (`sorted(state.entities.values(), key=lambda e: e.id)`,
  `sorted(providers.keys())`) — do not introduce dict-iteration-order-dependent selection.
