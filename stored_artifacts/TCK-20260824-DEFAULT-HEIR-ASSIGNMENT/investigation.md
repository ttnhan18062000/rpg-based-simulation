---
status: historical
layer: systems
authority: P2
audience: agent
ticket_id: TCK-20260824-DEFAULT-HEIR-ASSIGNMENT
artifact_type: investigation
tags: [social]
---

# Investigation — TCK-20260824-DEFAULT-HEIR-ASSIGNMENT

## Current Behavior

**`LifecycleSystem.resolve_lifecycle`** (`src/systems/lifecycle_systems/lifecycle.py:18-114`, re-exported
unchanged via the thin shim `src/systems/lifecycle.py:1-3`):

- Iterates `state.entities.items()` (line 28) — the frozen, pre-tick `AuthoritativeState` passed by
  closure from `AuthoritativeApplyPipeline.refine` (`src/engine/pipeline.py:360`:
  `run_phase("lifecycle", update, lambda u: LifecycleSystem.resolve_lifecycle(state, u))`). `state`
  is the same baseline object closed over by every phase in this refine sequence (`_resolve_groups`,
  `_apply_near_death_hardening`, etc., lines 354-369) — none of these phases re-read
  `update.entity_updates` to get an entity's up-to-date component state; they all read `state.entities`
  directly. This confirms the ticket's premise 1: `entity.social.bonds` used for heir selection would
  be the same pre-tick baseline the existing manual-heir-transfer code already reads.
- Death detection (lines 34-49): `OLD_AGE` from `age_ticks >= max_age_ticks`, or `COMBAT` from
  `ent_upd.combat.outcome_kind in ("KILL", "PERMADEATH")` — the `PERMADEATH` branch was added by
  `TCK-20260826-HOTFIX-PERMADEATH-LIFECYCLE-FIX` earlier this session (comment at lines 42-46). Current
  file state already includes this fix; no further change needed there.
- On death (lines 51-63): builds an `EntityUpdate` with `active=False` and a `LifecycleUpdate` marking
  `is_permadeath_set`, `death_tick_set`, `death_reason_set`. This part is unaffected by this ticket.
- **Existing manual-heir-transfer path (lines 65-88)** — the only heir-related logic that exists today:
  ```python
  if entity.lifecycle.heir_entity_id is not None:
      heir_id = entity.lifecycle.heir_entity_id
      heir = state.entities.get(heir_id)
      if heir:
          ... build ResourceTransferIntent for entity.inventory.items + heirloom ItemStacks ...
          refined_entity_updates[heir_id] = replace(heir_upd, resource_transfers=heir_upd.resource_transfers + [intent])
  ```
  This confirms the ticket's premise 2 precisely: the liveness check here is `if heir:` — i.e. only
  `state.entities.get(heir_id)` truthiness (does the ID exist in the dict at all). It does **not**
  check `heir.lifecycle.active`. A dead-but-still-present entity (e.g. one that died this same tick
  and is present in `state.entities` with `active=True` at read time, since `state` is pre-tick) would
  currently pass this check if manually set as heir. This existing check must not be modified by this
  ticket — the new default-selection logic needs its own, stricter filter (existence AND
  `.lifecycle.active`), per the ticket's explicit instruction.
- **Nothing anywhere assigns `heir_entity_id`.** No default-selection logic exists in this file, in
  `RelationshipService`, or anywhere else in the codebase (confirmed by reading
  `src/systems/social_systems/relationships.py` in full — `RelationshipService` has exactly two
  methods, `process_update` and `prune_low_salience`; neither selects or ranks bonds, both only apply
  deltas/prune). This is exactly the gap the ticket describes: "the transfer mechanic is fully wired
  and confirmed live, but nothing ever assigns a heir."

**`LifecycleUpdate`** (`src/core/updates.py:422-450`): has `heir_entity_id_set: Optional[int] = None`
and `heirlooms_add: list[str]`; `merge()` (line 439-450) prefers the last non-None `heir_entity_id_set`
across merges — safe for a single-writer inline assignment inside `resolve_lifecycle`.

**`LifecycleComponent`** (`src/core/state.py:143-172`): `heir_entity_id: Optional[int] = None`,
`heirlooms: list[str]`, `active: bool = True` — the field this ticket's new logic must read
(`entity.lifecycle.active` on the candidate heir) but must not directly mutate (mutation only via
`LifecycleUpdate.heir_entity_id_set` through `LifecyclePatch.apply`, confirmed below).

**Apply-path wiring — `src/engine/patches.py:69-88` (`LifecyclePatch.apply`)**: confirms the ticket's
premise that the transfer/assignment mechanic is fully live:
```python
heir_entity_id=u_life.heir_entity_id_set if u_life.heir_entity_id_set is not None else new_lifecycle.heir_entity_id,
```
`heir_entity_id_set`, when non-None, authoritatively overwrites `entity.lifecycle.heir_entity_id`;
when `None` (the no-op sentinel), the prior value is preserved. So a default-selection branch inside
`resolve_lifecycle` that populates `LifecycleUpdate(heir_entity_id_set=selected_id)` on the *dying*
entity's own `EntityUpdate` (not the heir's) would apply correctly through the existing path with zero
changes needed to `patches.py`. Note: this only matters if the selection needs to be visible on the
dying entity's own record before it goes `active=False` — in practice, since heirloom transfer already
reads `entity.lifecycle.heir_entity_id` (the *baseline*, pre-update value) directly at line 66, a
newly-selected default heir must be read from the **local selection result within the same
`resolve_lifecycle` call**, not from `refined_entity_updates`, to affect the same-tick heirloom
transfer per AC 1. Setting `heir_entity_id_set` on the dying entity's `LifecycleUpdate` records the
choice durably for future ticks/observability, but the same-tick transfer logic (lines 65-88) must be
extended to also branch on the freshly-selected ID, not only `entity.lifecycle.heir_entity_id`.

**`SocialBond`** (`src/core/models/social.py:6-11`): `target_id: int`, `familiarity: float` (0.0-1.0),
`sentiment: float` (-1.0 to 1.0), `last_interaction_tick: int`. **No kinship field exists anywhere in
this codebase** — confirmed by reading this file in full and grepping the broader `src/core/` and
`src/systems/social_systems/` trees; "heir" and "kinship" never co-occur. Bonds are stored per-entity
in `SocialComponent.bonds: Dict[int, SocialBond]` (`src/core/state.py:143` region, actually line 34 of
`social.py`), keyed by `target_id`.

**`V2EntityBuilder`** (`src/core/builder.py`): imports `SocialBond` (line 27) and exposes `.social(...)`
and `.lifecycle(heir_entity_id=..., heirlooms=...)` builder methods (confirmed present via import list;
full method bodies not re-quoted here as they are used unchanged by this ticket's new tests, matching
the existing `test_succession_and_heirloom_transfer` fixture pattern).

**`tests/unit/progression/test_lifecycle.py`** (all 6 existing tests read in full):
- `test_aging_per_tick`, `test_death_by_old_age`, `test_combat_death_classification`,
  `test_permadeath_death_classification` — unrelated to heir logic, must keep passing unchanged.
- `test_succession_and_heirloom_transfer` (lines 78-110) — the proven **manual**-heir-set +
  heirloom-transfer behavior this ticket's new default-selection path must also satisfy: builds a
  parent with `heir_entity_id=2` and `heirlooms=["Excalibur"]`, a live heir entity 2, calls
  `resolve_lifecycle`, and asserts `heir_upd.resource_transfers` contains a transfer intent with the
  `Excalibur` item. A new default-selection test must produce an equivalent assertion when
  `heir_entity_id is None` but a live bonded candidate exists.
- `test_permadeath_death_classification` (lines 58-76) — shows the current PERMADEATH hotfix shape:
  asserts `active is False`, `death_reason_set == "COMBAT"`, `is_permadeath_set is True` for a
  `CombatUpdate(outcome_kind="PERMADEATH")`. Confirms the death branch this ticket's new heir-selection
  logic must sit alongside (inside the same `if is_dead:` block, after the death record is built,
  where the existing manual-heir check already lives).

## Mechanics / Engine Constraints

- **`docs/engine/authoritative_mutation_pipeline_contract.md` §1-3** ("Proposal -> Refine -> Apply"):
  `resolve_lifecycle` runs in the **Refine** stage (`AuthoritativeApplyPipeline.refine`,
  `src/engine/pipeline.py:360`). Refine's job is to "consolidate deltas and tie-break conflicts" against
  the frozen baseline `state` — a deterministic, pure function of `(state, update)` with no direct
  mutation. Default-heir selection must be implemented as a pure computation over `state.entities` that
  produces a `LifecycleUpdate`/`ResourceTransferIntent`, never a direct `entity.lifecycle.heir_entity_id`
  assignment. This matches the ticket's Scope instruction ("via `LifecycleUpdate.heir_entity_id_set`,
  never direct field mutation") and is already the pattern the surrounding file follows throughout.
- **Durable State Rule (project CLAUDE.md)**: `heir_entity_id` is durable, typed state
  (`LifecycleComponent.heir_entity_id`) with a defined lifecycle and apply path — the selection *result*
  must flow through this existing typed field, not a new ad hoc mechanism. No new durable field is
  needed; the existing `heir_entity_id_set`/`heirlooms_add` vocabulary is sufficient.
- **Determinism**: The Kernel's 7-phase deterministic loop (`docs/engine/kernel.md`) and this project's
  "Do not break determinism" hard rule both require the selection rule to be a deterministic function of
  `entity.social.bonds` — no `set`/dict-iteration-order dependence, no `random` calls, explicit numeric
  tie-break. `SocialComponent.bonds` is a `Dict[int, SocialBond]`; Python 3.7+ dict iteration order is
  insertion-order-stable within a single run, but relying on insertion order for a gameplay-visible
  tie-break is fragile and implicit (violates "Do not create hidden or implicit durable behavior") —
  the rule must explicitly sort/select rather than rely on dict order.
- **No kinship model**: `docs/parity_ledger/social_narrative.yaml` and `docs/mechanics/04_strategic_cognition.md`
  both confirm bonds are the only per-pair relationship signal; "strongest bond" must be defined purely
  in terms of `familiarity`/`sentiment`/`last_interaction_tick`, as the ticket's own Open Questions
  section already states.
- **Precedent formula shape** — `docs/mechanics/04_strategic_cognition.md` §7.2 "Trust/Bonds-Aware
  Adjustment" (lines 629-652, TCK-20260811-RELATIONSHIP-AWARE-FORM-PARTY) is the only existing
  Mechanics Bible precedent for a documented weighted formula combining `SocialBond.familiarity`/
  `sentiment` into a single score (`TRUST_BONUS_WEIGHT=0.15`, `score_trust_bonds()`). Useful strictly as
  a *documentation formatting* precedent (named constant + cited function + clamp range + source
  file/line), **not** as a formula to reuse verbatim — that formula computes a trust-bonus overlay for
  `FORM_PARTY` generation-time confidence/expected-benefit, an unrelated use case with a different base
  score to add to. The planner must define a new, self-contained scoring/tie-break formula for heir
  selection.

## Docs Requiring Update

- `docs/mechanics/05_world_evolution.md`: no chapter currently documents lifecycle death/succession
  mechanics at all (confirmed by grepping all six `docs/mechanics/*.md` chapters for
  "heir|succession|heirloom|LifecycleSystem|resolve_lifecycle" — zero hits anywhere in the Mechanics
  Bible). This ticket adds a brand-new mechanic (default-heir selection with an explicit weighted/
  tie-break formula) per its own Scope requirement ("Add a new Mechanics Bible subsection or
  `docs/guidelines/intentional_divergences.md` entry documenting the default-selection rule and exact
  tie-break formula"). REVISED per architecture-review (Review phase, TCK-20260824-DEFAULT-HEIR-ASSIGNMENT):
  target `05_world_evolution.md`'s `## 5. Demographic Cohort Cycle` section (a new `### Succession —
  Default Heir Assignment` subsection immediately after the existing `### Birth/Death Law`
  subsection), not `04_strategic_cognition.md` as this investigation originally suggested — chapter 04
  is scoped to agent cognition (decisions computed by an actor for itself), while default heir
  selection is unconditional engine bookkeeping computed about a dead entity with no agent decision
  involved; `05_world_evolution.md` already owns entity death/age content (`Birth/Death Law`,
  `Age Bracket Thresholds (Entity-Level)`) and is the correct home. This is not
  a divergence from a pre-existing documented legacy/V2 behavior — it is wholly new behavior filling a
  previously-undocumented gap. `04_strategic_cognition.md` §7.2 remains useful only as a
  documentation-format template (named weight constant + cited scoring function + explicit range) —
  it is a cognition-layer mechanic computed by an acting entity for its own decisions, an unrelated
  use case to this ticket's engine-level, no-agent-decision-involved default-heir bookkeeping, so it
  is not a reason to co-locate the new subsection in chapter 04. Per CLAUDE.md's Authoritative
  Mechanics Rule, this doc addition must land in the same session as the code change, and the parity
  ledger entry below in the same pass.
- `docs/parity_ledger/social_narrative.yaml`: no existing entry (`SOC-001` through `SOC-244`, the
  current max ID, confirmed by listing all `SOC-\d+` ids) covers default-heir-selection; grep hits for
  "heir" in this file are all false positives (substring of "their"). A new `P1` entry (next available
  ID is `SOC-245`, since `SOC-243` is absent/reserved elsewhere and `SOC-244` is the current max) must
  be added recording the new selection rule, `v2_evidence` citing the implementation, and a `test_path`
  pointing at the new determinism/regression test — following the `SOC-244` entry's own format
  (lines 3349-3379) as the most recent precedent for documenting a brand-new bond-derived mechanic.

The `docs/engine/authoritative_mutation_pipeline_contract.md` doc (path:
`docs/engine/authoritative_mutation_pipeline_contract.md`, listed in the ticket's own Related Docs) is
not required to change for this ticket: it documents the general Proposal→Refine→Apply pipeline shape
and phase-ordering law at a level of abstraction that does not enumerate individual phases' internal
logic (it doesn't even name `LifecycleSystem` — that only appears in `src/engine/pipeline.py`). This
ticket's change fits entirely within the existing Refine-stage contract described there (a pure,
deterministic function producing typed updates against the frozen baseline `state`) without altering
that contract, so no edit to this file is needed; it was read only to confirm the constraint above.

## Parity Ledger Overlap

- No existing entry in `docs/parity_ledger/social_narrative.yaml` covers default-heir-selection. Closest
  neighbors by subject: `SOC-002` (bond/trust learning from interaction evidence, `P0`, `verified`) and
  `SOC-244` (`PartyCompositionScorer`'s trust-bonus formula, `P1`, `verified`, TCK-20260811) — neither
  overlaps this ticket's scope; both confirm bonds are the established per-pair signal vocabulary this
  ticket must also use.
- No `P0` entries are directly touched, so no pre-existing `test_path` needs to keep passing as a gate
  condition beyond ordinary regression (see Test Plan). A new `P1` entry (proposed ID `SOC-245`) must be
  added per "Docs Requiring Update" above, with its own `test_path` — since it's a new entry (not
  modifying an existing `P0`), it does not require the "P0 entries require a passing test_path after
  changes" rule to already be satisfied before this ticket lands, but the new entry's own test must
  exist and pass by the time it's added.

## Prior Work

- `TCK-20260409-PH4-STG2-SUCCESSION-LOGIC` (`tickets/done/`, `stored_artifacts/`): the **superseded V1**
  design this ticket's Out of Scope explicitly excludes. Its investigation.md describes
  `HeroLifecycleSystem.process_hero_death`, a `SuccessorRegistry`, `SuccessorRecord`/`HistoricalEvent`
  objects, and household-linked successor spawning — none of which exist in the current `src` tree
  (confirmed: `HeroLifecycleSystem` and `SuccessorRegistry` do not appear anywhere in
  `src/systems/lifecycle_systems/lifecycle.py` or `src/engine/patches.py`). Cited as prior intent only,
  per the ticket's own Out of Scope note — correctly excluded.
- `TCK-20260409-PH1-STG13-14` (`tickets/done/`): not read in depth (no `stored_artifacts/` entry found
  under this exact name), listed only as a Related Ticket; no conflicting live design surfaced.
- `TCK-20260811-RELATIONSHIP-AWARE-FORM-PARTY` (`tickets/done/`, `stored_artifacts/`): the live,
  current-generation precedent for a bond-derived weighted formula (`TRUST_BONUS_WEIGHT=0.15`,
  `score_trust_bonds()`), documented in `docs/mechanics/04_strategic_cognition.md` §7.2 and
  `docs/parity_ledger/social_narrative.yaml` `SOC-244`. Directly useful as a documentation-format
  template for this ticket's new subsection/entry (see "Docs Requiring Update").
- `TCK-20260826-HOTFIX-PERMADEATH-LIFECYCLE-FIX` (this session, hotfix tier, no staging artifacts per
  hotfix convention): already landed the `PERMADEATH` branch in `resolve_lifecycle`'s combat-death
  check (lines 42-49). This ticket's new heir-selection logic must sit downstream of (after) this
  existing death-classification branch, inside the same `if is_dead:` block — it does not need to
  re-touch the death-classification logic itself.

## Risks and Open Questions

- **The exact tie-break/selection formula is a genuine open design decision, not yet answered by this
  investigation** — per the ticket's own Assumptions/Open Questions and the project's Uncertainty Rule
  ("vague leads stay vague until evidence narrows them"). What is established: candidates are
  `entity.social.bonds.values()` (or equivalently keyed by `target_id`), each is a `SocialBond` with
  `familiarity` (0.0-1.0), `sentiment` (-1.0 to 1.0), `last_interaction_tick` (int); candidates must be
  filtered to those live in `state.entities` (existence AND `.lifecycle.active`) before scoring; ties
  must resolve via an explicit, non-hash-order-dependent rule (e.g. lowest/highest `target_id` as final
  tie-break, since entity IDs are stable, monotonically-assigned integers — see
  `AuthoritativeState.next_entity_id`, `src/core/state.py:1203`). The actual weighting between
  `familiarity` and `sentiment` (equal weight? sentiment-only, since "who liked me most" reads more like
  an heir choice than "who I interacted with most"? a combined score?) is not decided here and must be
  resolved at planning time, then documented per "Docs Requiring Update" with the exact formula matching
  code (AC 4). This is flagged, not assumed.
- **Whether a negative-sentiment bond should be eligible at all** is unresolved — the ticket's Scope
  says "at least one bond to a living entity" without excluding hostile bonds. A candidate with
  `sentiment` deeply negative (e.g. a rival/nemesis) being auto-selected as heir may read as a gameplay
  bug even though it satisfies "a bond exists." Flagging for planner decision; do not assume either
  answer.
- **Where the local (same-`resolve_lifecycle`-call) selected heir ID is threaded into the existing
  heirloom-transfer block** (lines 65-88) is an implementation-shape question, not just a data question:
  the transfer block currently branches on `entity.lifecycle.heir_entity_id` (baseline field) directly.
  The new logic must compute the default-selected ID *before* that branch and feed it in when
  `entity.lifecycle.heir_entity_id is None`, without disturbing the manual-set path's existing behavior
  or its (intentionally-unchanged-by-this-ticket) `if heir:` liveness check.
- **Interaction with the influence/conquest lifecycle block (lines 90-112)**: `recent_deaths` is
  collected and later feeds `FactionInfluenceService.process_influence_shift`/
  `process_conquest_lifecycle`. The new heir-selection logic must not alter `recent_deaths` construction
  or ordering, since those two calls are unrelated to succession and must not regress.

## Anti-Drift Hazards

- **Do not modify the existing manual-heir-transfer liveness check** (`if heir:` at line 69) — the
  ticket explicitly requires the new default-selection logic to have its **own**, stricter filter
  (existence AND `.lifecycle.active`), distinct from the pre-existing manual path. Tightening the
  existing check would be an unrequested behavior change to already-proven, tested logic
  (`test_succession_and_heirloom_transfer`).
- **Do not resurrect the V1 `HeroLifecycleSystem`/`SuccessorRegistry` design** (explicitly Out of Scope)
  — no `HistoricalEvent`, `SuccessorRecord`, or household-linkage logic belongs in this ticket.
  Household/history integration was the V1 design's job and is not part of this ticket's Scope.
  `LifecycleComponent` has no `household_id` field today; do not add one.
  `docs/superpowers/specs/2026-04-09-continuity-and-consequence-design.md` (V1's Related Docs) is
  unrelated to this ticket and must not be touched.
  Also don't add motive/grudge-fragment transfer logic — the V1 design's "abstract legacy transfer"
  ("resentment towards the killer") has no equivalent field or requirement in this ticket's AC.
- **Do not touch `RewardUpdate`/XP or the `FactionInfluenceService` conquest/influence block** — heir
  selection must be additive to `resolve_lifecycle`, not a refactor of the surrounding death-handling
  flow (lines 90-112 are unrelated to succession and must produce byte-identical output for scenarios
  with no heir-eligible deaths).
  Note: `EntityUpdate.merge()` (`src/core/updates.py:677-712`) already correctly merges `lifecycle`
  sub-updates (`self.lifecycle.merge(other.lifecycle)` at line 700) — reuse `LifecycleUpdate.merge()`'s
  existing semantics rather than hand-rolling a new merge path.
- **Do not weight `last_interaction_tick` as a primary score component without checking its resolution
  against the tick counter's realistic scale** — `last_interaction_tick` is an absolute tick number, not
  a delta; using it directly (rather than `state.tick - last_interaction_tick`, "recency") in a weighted
  formula would silently favor entities with *later* interaction ticks regardless of true recency,
  which is a subtle correctness trap distinct from the familiarity/sentiment tie-break question above.
- **Keep the new formula self-contained from §7.2's `TRUST_BONUS_WEIGHT`/`score_trust_bonds()`** — do
  not literally re-import or re-use those constants/functions for heir selection; they are scoped to
  `PartyCompositionScorer`/`AdventureRouteGenerator` and computing a *different* base score. Reusing the
  name or constant value without re-deriving it for this use case would misrepresent the parity ledger
  and Mechanics Bible citation trail (SOC-244's `divergence_note` already flags a similar historical
  mis-citation risk in this exact area).
