---
status: historical
layer: systems
authority: P2
audience: agent
ticket_id: TCK-20260824-DEFAULT-HEIR-ASSIGNMENT
artifact_type: plan
tags: [social]
---

# Implementation Plan — TCK-20260824-DEFAULT-HEIR-ASSIGNMENT

## Summary

Add a deterministic default-heir-selection step inside `LifecycleSystem.resolve_lifecycle`'s
existing death branch (`src/systems/lifecycle_systems/lifecycle.py:51-88`), gated to run only when
`entity.lifecycle.heir_entity_id is None`, scoring the dying entity's live bonded candidates
(`entity.social.bonds`, filtered to targets that exist in `state.entities` AND have
`.lifecycle.active is True`) with `score = 0.6 * familiarity + 0.4 * ((sentiment + 1.0) / 2.0)`,
breaking ties by highest `last_interaction_tick` then lowest `target_id`. The selected id is (a)
recorded durably via `LifecycleUpdate.heir_entity_id_set` on the dying entity's own `EntityUpdate`
and (b) fed directly into the existing heirloom-transfer block so the transfer still happens in the
same tick, exactly matching the proven manual-heir-set behavior. The existing manual-heir-transfer
branch (`if entity.lifecycle.heir_entity_id is not None: ... if heir:`) is left untouched — the new
logic is strictly additive, running only in the `else` (no manual heir) case, with its own stricter
liveness filter. Six new unit tests are added to `tests/unit/progression/test_lifecycle.py`, one new
`### Succession — Default Heir Assignment` subsection is appended to `docs/mechanics/05_world_evolution.md`
under `## 5. Demographic Cohort Cycle`, immediately after the existing `### Birth/Death Law`
subsection (chosen over `docs/mechanics/04_strategic_cognition.md` and over
`intentional_divergences.md` — see rationale below), and one new `P1` entry `SOC-245` is added to
`docs/parity_ledger/social_narrative.yaml`.

**Revision note (post architecture-review, addressed before re-submitting for Review):** the
original draft of this plan placed the new doc subsection in `docs/mechanics/04_strategic_cognition.md`
(reasoning: it is the only existing precedent for a `SocialBond`-derived weighted formula). The
architecture-reviewer correctly identified this as the wrong chapter: chapter 04 is scoped to
*agent cognition* (goal hierarchy, interruption resistance, knowledge management, perception) — a
process computed *by* an acting entity to inform *its own* decisions (§7.2's trust-bonus term is
exactly this: computed by `PartyCompositionScorer`/`AdventureRouteGenerator` for FORM_PARTY
generation). Default heir selection is the opposite shape: computed *about* a dead entity, *by* the
engine (`LifecycleSystem.resolve_lifecycle`, unconditional Refine-stage bookkeeping), with no agent
decision involved anywhere in the call path. `docs/mechanics/05_world_evolution.md` already owns
"what happens when an entity dies" (§5 Demographic Cohort Cycle's `### Birth/Death Law` subsection,
plus its `### Age Bracket Thresholds (Entity-Level)` subsection, which is keyed off the same
`age_ticks`/`LifecycleComponent` field this ticket's death branch reads) — it is the correct,
already-established home. This revision moves the target file only; the formula, weights,
tie-break, and all code changes are unaffected.

**Design decision on negative-sentiment bonds (resolving the investigation's flagged open question):**
negative-sentiment bonds remain eligible candidates — they are not hard-excluded — because the
scoring formula already down-weights them structurally: `sentiment` is normalized from its native
`-1.0..1.0` range into `0.0..1.0` before being multiplied by its `0.4` weight, so a deeply negative
bond (`sentiment=-1.0`) contributes `0.0` to that term rather than being excluded outright, while a
candidate with high `familiarity` can still outscore a low-familiarity/neutral-sentiment candidate.
This is the more conservative reading of the ticket's Scope line ("at least one bond to a living
entity" — no sentiment-based exclusion is stated), avoids introducing a second, undocumented
eligibility gate beyond the liveness filter the ticket explicitly asks for, and keeps the rule
expressible as a single continuous formula rather than a formula-plus-exception. This is treated as
a planning decision, not an unresolved question, since only one reading is consistent with the
ticket's literal Scope text and the "no exception, no exclusion beyond liveness" spirit of AC 2.

## Steps

### Step 1 — Implement `_select_default_heir` as a new private staticmethod

**Files:** `src/systems/lifecycle_systems/lifecycle.py`

**Change:** Add a new `@staticmethod` `_select_default_heir(state: AuthoritativeState, deceased:
EntityState) -> Optional[int]` on `LifecycleSystem` (defined above `resolve_lifecycle`, e.g.
immediately after the class docstring at `src/systems/lifecycle_systems/lifecycle.py:12-17`, before
line 18's `resolve_lifecycle`). Logic:

```python
@staticmethod
def _select_default_heir(state: AuthoritativeState, deceased: EntityState) -> Optional[int]:
    candidates = []
    for target_id, bond in deceased.social.bonds.items():
        if target_id == deceased.id:
            continue
        candidate = state.entities.get(target_id)
        if candidate is None or not candidate.lifecycle.active:
            continue
        score = 0.6 * bond.familiarity + 0.4 * ((bond.sentiment + 1.0) / 2.0)
        candidates.append((score, bond.last_interaction_tick, target_id))
    if not candidates:
        return None
    candidates.sort(key=lambda c: (-c[0], -c[1], c[2]))
    return candidates[0][2]
```

- `deceased.social.bonds` is confirmed `Dict[int, SocialBond]` at `src/core/models/social.py:34`
  (`SocialComponent.bonds`), reached via `EntityState.social: SocialComponent`
  (`src/core/state.py:678`).
- `SocialBond.familiarity` (0.0-1.0), `SocialBond.sentiment` (-1.0-1.0), `SocialBond.last_interaction_tick`
  (int), `SocialBond.target_id` (int) are confirmed at `src/core/models/social.py:6-11`.
- `state.entities` is `Dict[int, EntityState]`, confirmed by existing usage at
  `src/systems/lifecycle_systems/lifecycle.py:28` (`state.entities.items()`) and
  `src/systems/lifecycle_systems/lifecycle.py:68` (`state.entities.get(heir_id)`).
- `EntityState.lifecycle.active` (bool) is confirmed at `src/core/state.py:153`
  (`LifecycleComponent.active: bool = True`).
- Sort key uses only `score`, `last_interaction_tick`, `target_id` — no `hash()`, no `set`, no dict
  iteration order dependence in the *comparison*; `.items()` iteration order only affects which
  order candidates are appended to the list, which the explicit `sort()` normalizes away regardless
  of insertion order.
- This method has no other writers to worry about — it is a pure function reading only `state`
  (frozen baseline, read-only everywhere else in this file) and `deceased` (a single `EntityState`
  passed by the caller), and returns a value with no side effects. It does not mutate
  `refined_entity_updates` or any shared structure itself.

**Do NOT touch:** `resolve_lifecycle`'s existing manual-heir-transfer block (lines 65-88) — this
step only adds a new method; Step 2 wires it in without modifying that block's own logic.

**Verify:** No standalone test for this step alone (it has no death-branch wiring yet); verified
transitively by Step 2's tests. If run in isolation, `python3 -c "from src.systems.lifecycle_systems.lifecycle import LifecycleSystem"` must import cleanly with no syntax errors.

---

### Step 2 — Wire `_select_default_heir` into `resolve_lifecycle`'s death branch

**Files:** `src/systems/lifecycle_systems/lifecycle.py`

**Change:** Modify the existing succession block at
`src/systems/lifecycle_systems/lifecycle.py:65-88`:

```python
# Process Succession / Heirlooms
heir_id = entity.lifecycle.heir_entity_id
if heir_id is None:
    heir_id = LifecycleSystem._select_default_heir(state, entity)
    if heir_id is not None:
        life_upd2 = refined_entity_updates[e_id].lifecycle or LifecycleUpdate()
        refined_entity_updates[e_id] = replace(refined_entity_updates[e_id],
            lifecycle=replace(life_upd2, heir_entity_id_set=heir_id)
        )
if heir_id is not None:
    heir = state.entities.get(heir_id)
    if heir:
        heir_upd = refined_entity_updates.get(heir_id, EntityUpdate(entity_id=heir_id))
        # Transactional Heirloom Transfer
        from src.core.updates import ResourceTransferIntent
        from src.core.state import ItemStack

        heirloom_stacks = [ItemStack(item_id=hid, quantity=1) for hid in entity.lifecycle.heirlooms]
        all_transfer_items = entity.inventory.items + heirloom_stacks

        if all_transfer_items:
            intent = ResourceTransferIntent(
                source_id=entity.id,
                source_kind="CHEST",
                items_add=all_transfer_items,
                transfer_kind="AUTO"
            )
            refined_entity_updates[heir_id] = replace(heir_upd,
                resource_transfers=heir_upd.resource_transfers + [intent]
            )
```

Key points:
- `if entity.lifecycle.heir_entity_id is not None:` (line 66) is replaced by reading it into a local
  `heir_id` variable first, so the **manual path's exact existing behavior is preserved
  byte-for-byte** when `heir_entity_id` is already set (same `if heir:` liveness check at the
  original line 69, unchanged, now reached via `if heir:` inside the merged `if heir_id is not
  None:` block).
- When `heir_entity_id is None`, `_select_default_heir` runs. If it returns a candidate, the
  dying entity's own `LifecycleUpdate.heir_entity_id_set` is populated (durable record) on
  `refined_entity_updates[e_id]` — the SAME `EntityUpdate` already built for this death at lines
  51-63, merged via `replace()`, never a second separate `EntityUpdate` for `e_id`. This is
  consistent with `LifecycleUpdate.merge()` semantics (`src/core/updates.py:439-450`) though no
  actual merge call is needed here since this is a single direct `replace()` within the same
  refine pass, before any cross-update merge would occur.
- The heirloom-transfer block below is now reached via the merged `heir_id` local variable
  (covers both manual-set and freshly-selected-default cases) instead of re-reading
  `entity.lifecycle.heir_entity_id` directly — this satisfies the investigation's finding
  (`investigation.md` lines 76-80) that the transfer code must branch on the locally-selected ID,
  not only the baseline field, for the same-tick transfer to fire for a newly-selected default
  heir.
- The **existing `if heir:` liveness check (only existence, not `.lifecycle.active`) is preserved
  unchanged** for both paths — this is intentional per the ticket's Scope and investigation's
  Anti-Drift Hazards: `_select_default_heir` already applied its own **stricter** filter
  (existence AND `.lifecycle.active`) before returning a candidate, so by the time a
  default-selected `heir_id` reaches this `if heir:` check, it has already passed the stricter
  test; the check is simply never false for a default-selected heir. For a manually-set heir, the
  looser check's existing behavior (accepting a present-but-inactive entity) is untouched, per
  `test_plan.md`'s explicit anti-drift test guard.
- **Other writers to `refined_entity_updates[e_id]` in this same function**: the only other writer
  to this same dict key within `resolve_lifecycle` is the death-classification block immediately
  above (lines 52-63), which runs once per dying entity before this block and is not re-entered.
  No other phase in `AuthoritativeApplyPipeline.refine` (`src/engine/pipeline.py:354-369`) writes to
  `entity_updates[e_id].lifecycle` for the same entity in the same call — `resolve_lifecycle` is the
  sole writer of `LifecycleUpdate.heir_entity_id_set` in the pipeline (confirmed: grep of
  `heir_entity_id_set` across `src/` shows only this file writing it and `src/engine/patches.py:84`
  reading/applying it). No ordering race exists because this is a single sequential function call
  over `state.entities.items()`, not concurrent execution.
- **`refined_entity_updates[heir_id]`** (the heir's own update, not the dying entity's) can already
  be written by an earlier iteration of this same `for e_id, entity in state.entities.items()` loop
  if the heir itself is unrelated to another death this tick, or by a prior phase's update passed in
  via `update.entity_updates` (captured into `refined_entity_updates = dict(update.entity_updates)`
  at line 23) — this is pre-existing behavior handled by the existing
  `refined_entity_updates.get(heir_id, EntityUpdate(entity_id=heir_id))` pattern (line 70,
  unchanged), which this step reuses verbatim; no new collision risk introduced.

**Do NOT touch:** the death-classification block (lines 51-63), the `recent_deaths`/
`FactionInfluenceService` block (lines 90-112), or the `if heir:` liveness check's condition itself.

**Verify:**
- `tests/unit/progression/test_lifecycle.py::test_succession_and_heirloom_transfer` (manual path
  unaffected)
- `tests/unit/progression/test_lifecycle.py::test_default_heir_selected_from_strongest_bond`
- `tests/unit/progression/test_lifecycle.py::test_default_heir_does_not_override_manual_heir_entity_id`

---

### Step 3 — Add new unit tests to `tests/unit/progression/test_lifecycle.py`

**Files:** `tests/unit/progression/test_lifecycle.py`

**Change:** Add the following test functions, following the existing `V2EntityBuilder` /
`AuthoritativeState` / `LifecycleSystem.resolve_lifecycle` pattern already used by
`test_succession_and_heirloom_transfer` (lines 78-110, read in full). Candidates' bonds are set via
`replace(entity, social=replace(entity.social, bonds={target_id: SocialBond(...)}))` since
`V2EntityBuilder.social(...)` accepts `bonds: Optional[Dict[int, SocialBond]] = None`
(`src/core/builder.py:496-505`).

1. `test_default_heir_selected_from_strongest_bond` — dying entity, `heir_entity_id=None`,
   `heirlooms=["Excalibur"]`, one live bonded candidate (`familiarity=0.8, sentiment=0.5`). Assert
   `refined.entity_updates[1].lifecycle.heir_entity_id_set == 2` and
   `refined.entity_updates[2].resource_transfers` contains the Excalibur transfer, mirroring
   `test_succession_and_heirloom_transfer`'s assertion shape.
2. `test_default_heir_prefers_strongest_bond_among_multiple_candidates` — two live candidates with
   different scores (e.g. candidate A `familiarity=0.9, sentiment=0.0` scoring `0.6*0.9+0.4*0.5=0.74`;
   candidate B `familiarity=0.2, sentiment=1.0` scoring `0.6*0.2+0.4*1.0=0.52`); assert A is selected.
3. `test_default_heir_zero_bonds_no_heir_assigned` — `heir_entity_id=None`, `social.bonds={}`; assert
   `refined.entity_updates[1].lifecycle.heir_entity_id_set is None` and no `resource_transfers`
   anywhere in `refined.entity_updates`, no exception raised.
4. `test_default_heir_all_bonded_targets_dead_or_missing_no_heir_assigned` — `heir_entity_id=None`,
   one bond to a `target_id` present in `state.entities` with `lifecycle.active=False`, and one bond
   to a `target_id` absent from `state.entities` entirely; assert no heir assigned, no exception.
5. `test_default_heir_selection_deterministic_across_repeated_calls` — build the same
   `{target_id: SocialBond}` pairs into two separate `bonds` dicts with reversed insertion order;
   call `resolve_lifecycle` once per dict against otherwise-identical state; assert both selections
   equal the same `heir_id`.
6. `test_default_heir_tie_break_deterministic` — two live candidates with identical
   `familiarity`/`sentiment` but different `last_interaction_tick` (assert higher tick wins); a
   second variant with identical `familiarity`/`sentiment`/`last_interaction_tick` but different
   `target_id` (assert lower `target_id` wins).
7. `test_default_heir_does_not_override_manual_heir_entity_id` —
   `test_succession_and_heirloom_transfer`'s exact scenario (`heir_entity_id=2`) plus an additional
   live bonded candidate (entity 3, high score) added to the dying entity's `social.bonds`; assert
   entity 2 (not 3) still receives the transfer and `heir_entity_id_set` is either `None` (default
   logic never ran) or `2` (never `3`).

Additionally, confirm (add if missing, per `test_plan.md`'s Anti-Drift Test Guards) a test that a
manually-set `heir_entity_id` pointing at a present-but-`lifecycle.active=False` entity still
receives the transfer — proving the pre-existing `if heir:` check was not tightened as a side
effect of Step 2. If `test_succession_and_heirloom_transfer` or an existing test already covers
this, no new test is needed; verify by reading current coverage before adding.

**Do NOT touch:** `test_aging_per_tick`, `test_death_by_old_age`, `test_combat_death_classification`,
`test_permadeath_death_classification`, `test_near_death_hardening_logic` — must remain byte-for-byte
unchanged.

**Verify:** `pytest tests/unit/progression/test_lifecycle.py -v` — all tests (existing 6 + new 7-8)
pass.

---

### Step 4 — Run adjacent regression suites

**Files:** none (verification-only step)

**Change:** No code change. Run the regression surface identified in `test_plan.md`:
```
pytest tests/unit/progression/test_lifecycle.py -v
pytest tests/unit/social/test_social_bonds.py tests/unit/social/test_relationships.py tests/unit/social/test_party_composition.py -v
pytest tests/unit/progression/ tests/unit/social/ -v -m "not slow"
```
This confirms `test_party_composition.py::test_party_composition_score_reflects_candidate_trust_history`
(the `SOC-244`/`score_trust_bonds()` precedent) is untouched — Step 1's formula is self-contained
and does not import or reference `TRUST_BONUS_WEIGHT`/`score_trust_bonds` from
`src/systems/social_systems/party_composition.py`, per the investigation's explicit hazard.

**Do NOT touch:** `src/systems/social_systems/relationships.py` (`RelationshipService.process_update`/
`prune_low_salience`), `src/systems/social_systems/party_composition.py`
(`score_trust_bonds`/`TRUST_BONUS_WEIGHT`).

**Verify:** All listed pytest commands exit 0.

---

### Step 5 — Document the default-heir-selection rule in the Mechanics Bible

**Files:** `docs/mechanics/05_world_evolution.md`

**Change:** Insert a new `###`-level subsection under the existing `## 5. Demographic Cohort Cycle`
section, immediately after the existing `### Birth/Death Law` subsection (lines 153-158) and before
`### Migration Law` (line 160) — the natural adjacent slot for entity-death-triggered succession
logic, next to the chapter's other death/age-bracket content:

```markdown

### Succession — Default Heir Assignment (TCK-20260824-DEFAULT-HEIR-ASSIGNMENT)

`LifecycleSystem.resolve_lifecycle()` (`src/systems/lifecycle_systems/lifecycle.py`). When an active
entity dies (`OLD_AGE` or `COMBAT`) with `heir_entity_id is None`, a default heir is selected from
the deceased's `SocialComponent.bonds` before the same-tick heirloom-transfer step runs.

**Candidate filter:** every `target_id` in `deceased.social.bonds` where `target_id != deceased.id`,
`state.entities.get(target_id)` exists, AND `target.lifecycle.active is True`. This filter is
strictly stricter than the pre-existing manual-heir-transfer path's liveness check (existence only,
not `.active`) — the manual path is unchanged by this mechanic.

**Score:**

score = 0.6 × familiarity + 0.4 × ((sentiment + 1.0) / 2.0)

- `familiarity` (native range 0.0–1.0) is weighted 0.6 — the primary signal, since how much the
  deceased actually knew/interacted with a candidate is the more direct proxy for "who they would
  leave things to" than bare positive regard.
- `sentiment` (native range −1.0–1.0) is normalized to 0.0–1.0 before weighting at 0.4 — a
  secondary signal. Negative-sentiment bonds are not excluded, only down-weighted: a hostile bond
  contributes 0.0 to this term rather than disqualifying the candidate outright.
- Combined score range: 0.0–1.0.

**Tie-break (explicit total order, no hash/dict-iteration-order dependence):** candidates are
ordered by `(-score, -last_interaction_tick, target_id)` — highest score wins; ties broken by most
recent `last_interaction_tick` (higher tick = more recent, since it is an absolute tick number, not
a delta); remaining ties broken by lowest `target_id`.

**No-candidate case:** if the candidate set is empty (zero bonds, or every bonded target is dead or
missing), no heir is assigned and no exception is raised — inventory/heirlooms remain untransferred,
identical to today's `heir_entity_id is None` behavior.

**Selection result flow:** the selected id is recorded via `LifecycleUpdate.heir_entity_id_set` on
the dying entity's own `EntityUpdate` (never a direct field mutation), applied authoritatively by
`LifecyclePatch.apply()` (`src/engine/patches.py:84`). The same selected id is used locally within
the same `resolve_lifecycle` call to drive the same-tick heirloom-transfer `ResourceTransferIntent`,
matching the pre-existing manual-heir-set + same-tick-transfer behavior.

This is unrelated to §7.2's `TRUST_BONUS_WEIGHT`/`score_trust_bonds()` in
`docs/mechanics/04_strategic_cognition.md` — that mechanic computes a trust-bonus overlay for
`PartyCompositionScorer`/`AdventureRouteGenerator` FORM_PARTY generation confidence, a
cognition-layer use case with a different base score and a different chapter; no constant or
function is shared between the two.

**Source:** `src/systems/lifecycle_systems/lifecycle.py` (`LifecycleSystem._select_default_heir`,
`LifecycleSystem.resolve_lifecycle`) (TCK-20260824-DEFAULT-HEIR-ASSIGNMENT, 2026-08-26)
```

**Rationale for placing this in the Mechanics Bible rather than `intentional_divergences.md`:** per
`docs/guidelines/intentional_divergences.md`'s stated purpose (recording *behavior shifts from
documented legacy behavior*), this ticket introduces wholly new behavior filling a previously
undocumented gap — the investigation confirmed zero existing hits for
"heir|succession|heirloom|LifecycleSystem|resolve_lifecycle" anywhere in the Mechanics Bible
(`investigation.md` lines 146-158), so there is no prior documented legacy behavior to diverge
from. A new subsection is the correct home.

**Rationale for `05_world_evolution.md` §5 over `04_strategic_cognition.md`:** chapter 04 is scoped
to agent cognition — decisions computed *by* an acting entity for *itself* (goal hierarchy,
interruption resistance, knowledge management, perception; §7.2's trust-bonus term fits this shape
exactly, computed by an actor's own party-formation scoring). Default heir selection is
unconditional engine bookkeeping computed *about* a dead entity *by* `LifecycleSystem`, with no
agent decision anywhere in the call path — it belongs with the chapter that already documents
entity death and age (`§5 Demographic Cohort Cycle`'s `Birth/Death Law` and
`Age Bracket Thresholds (Entity-Level)` subsections, the latter keyed off the same
`LifecycleComponent`/`age_ticks` field this ticket's death branch reads), not the chapter that
happens to share a data type (`SocialBond`) with an unrelated cognition mechanic.

**Do NOT touch:** any existing section of `05_world_evolution.md` (§1-§7) or
`04_strategic_cognition.md` (§1-§7.2) — this is a pure insertion into `05_world_evolution.md`. Do
not add or modify anything in `docs/guidelines/intentional_divergences.md`.

**Verify:** No automated test directly checks doc prose; correctness is verified indirectly by
Step 6's parity ledger entry citing this section, and manually by confirming the formula text
matches Step 1's code exactly (same weights, same tie-break order).

---

### Step 6 — Add parity ledger entry `SOC-245`

**Files:** `docs/parity_ledger/social_narrative.yaml`

**Change:** Append a new entry after the existing `SOC-244` entry (confirmed as the current max id,
ending at line 3383 with `support_boundary: null`; no `SOC-243` exists in the file, consistent with
the investigation's finding), following `SOC-244`'s exact field shape (`docs/parity_ledger/social_narrative.yaml:3349-3383`):

```yaml
- id: SOC-245
  text: >
    LifecycleSystem.resolve_lifecycle() (src/systems/lifecycle_systems/lifecycle.py) now assigns a
    default heir when an active entity dies with heir_entity_id is None and at least one live bonded
    candidate exists in SocialComponent.bonds. Candidates are filtered to targets present in
    state.entities with lifecycle.active is True (stricter than the pre-existing manual-heir-transfer
    path's existence-only check, which is unchanged). Score = 0.6 * familiarity + 0.4 *
    ((sentiment + 1.0) / 2.0); ties broken by highest last_interaction_tick then lowest target_id.
    Zero eligible candidates results in no heir assigned, no exception. Selected heir is recorded via
    LifecycleUpdate.heir_entity_id_set and used locally within the same tick to drive the existing
    heirloom-transfer ResourceTransferIntent. Full formula documented in
    docs/mechanics/05_world_evolution.md §5 (Succession — Default Heir Assignment subsection).
  status: verified
  priority: P1
  legacy_evidence: null
  v2_evidence: >
    src/systems/lifecycle_systems/lifecycle.py — LifecycleSystem._select_default_heir(),
    LifecycleSystem.resolve_lifecycle(). Verified by TCK-20260824-DEFAULT-HEIR-ASSIGNMENT.
  proof_type: parity
  test_path: tests/unit/progression/test_lifecycle.py::test_default_heir_tie_break_deterministic
  divergence_note: >
    New mechanic added by TCK-20260824-DEFAULT-HEIR-ASSIGNMENT. Prior to this ticket, no default-heir
    selection existed anywhere in the codebase; heir_entity_id was only ever set manually, and the
    transfer mechanic (src/engine/patches.py:84) had no writer for the unassigned case.
  support_boundary: null
```

**Do NOT touch:** `SOC-001` through `SOC-244` or any other existing entry in this file.

**Verify:** the cited `test_path` (`test_default_heir_tie_break_deterministic`) exists and passes
after Step 3; YAML parses (`python3 -c "import yaml; yaml.safe_load(open('docs/parity_ledger/social_narrative.yaml'))"`).

---

## Scope Guards

- Do not modify `src/engine/patches.py` (`LifecyclePatch.apply`) — the apply-path wiring for
  `heir_entity_id_set` already works correctly and needs zero changes (confirmed in investigation).
- Do not modify the existing manual-heir-transfer liveness check's condition (`if heir:` — existence
  only) — it must remain exactly as-is for the manually-set-heir path.
- Do not modify `src/systems/social_systems/relationships.py` (`RelationshipService.process_update`,
  `prune_low_salience`) — unrelated to this ticket, no ranking/selection logic belongs there.
- Do not modify `src/systems/social_systems/party_composition.py`
  (`TRUST_BONUS_WEIGHT`/`score_trust_bonds()`) or import/reuse those constants/functions for heir
  selection — the new formula is self-contained per the investigation's explicit anti-drift hazard.
- Do not revive V1 `HeroLifecycleSystem`/`SuccessorRegistry`, `SuccessorRecord`, `HistoricalEvent`,
  or any household-linkage/`household_id` field — confirmed Out of Scope.
- Do not modify the death-classification block (lines 51-63) or the `PERMADEATH`/`KILL` outcome
  check (lines 42-49) — the new logic sits strictly downstream, additive only.
- Do not modify the `recent_deaths`/`FactionInfluenceService.process_influence_shift`/
  `process_conquest_lifecycle` block (lines 90-112) — unrelated to succession.
- Do not touch `docs/guidelines/intentional_divergences.md` — this is new behavior, not a divergence
  from documented legacy behavior (see Step 5 rationale).
- Do not add a new durable field to `LifecycleComponent` or `SocialBond` — the existing
  `heir_entity_id_set`/`heirlooms_add` vocabulary and existing `SocialBond` fields are sufficient.
- Do not weight `last_interaction_tick` as a primary score component — it is used only as a
  secondary tie-break, per the investigation's explicit hazard about absolute-tick-vs-recency traps.
- Do not touch `docs/engine/authoritative_mutation_pipeline_contract.md` — confirmed no edit needed
  (investigation.md lines 167-174).

## Dependency Map

- Step 1 (implement `_select_default_heir`) must land before Step 2 (wiring), since Step 2 calls it.
- Step 2 must land before Step 3's tests can pass (tests exercise the wired behavior).
- Step 3 must land before Step 4 (regression run includes the new tests).
- Step 5 and Step 6 are independent of each other and of Steps 1-4 in terms of file conflicts, but
  Step 6's `test_path` reference requires Step 3's test to exist and pass first, and Step 5's
  documented formula must match Step 1's actual code — so Steps 5 and 6 should be finalized last,
  after Steps 1-4 are verified, to guarantee doc/code/ledger parity.
- Steps 1, 2, 5, and 6 all touch different files and can be authored in any order relative to each
  other, but the dependency chain above governs verification order.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC 1: active entity dies, `heir_entity_id==None`, ≥1 live bond → heir assigned + same-tick `resource_transfers` | Step 1, Step 2 | `test_default_heir_selected_from_strongest_bond`, `test_default_heir_prefers_strongest_bond_among_multiple_candidates` |
| AC 2: zero bonds or all bonded targets dead/missing → no heir, no exception | Step 1 (candidate filter + empty-list guard), Step 2 | `test_default_heir_zero_bonds_no_heir_assigned`, `test_default_heir_all_bonded_targets_dead_or_missing_no_heir_assigned` |
| AC 3: deterministic selection, explicit documented tie-break, regression test | Step 1 (sort key), Step 5 (documented formula) | `test_default_heir_selection_deterministic_across_repeated_calls`, `test_default_heir_tie_break_deterministic` |
| AC 4: default-selection rule documented in `docs/mechanics/` or `intentional_divergences.md` with exact tie-break formula matching code | Step 5 | Manual cross-check (Step 5's Verify) that doc formula text matches Step 1's code exactly |

## Anti-Drift Notes

- The existing manual-heir-transfer `if heir:` liveness check (existence-only, not `.active`) must
  survive Step 2's refactor unchanged in behavior — Step 2's Change text shows the exact mechanism
  (a single `heir_id` local variable feeding into the same unmodified `if heir:` block) that
  preserves this. `test_default_heir_does_not_override_manual_heir_entity_id` and the existing
  `test_succession_and_heirloom_transfer` are the guards.
- `last_interaction_tick` is an absolute tick number, not a recency delta — it is used only as a
  tie-break (comparing two candidates' absolute ticks directly is valid for "which happened more
  recently," since both candidates are evaluated at the same current tick), never as a primary
  weighted score term. Do not later "simplify" this into a primary-score component without
  converting to `state.tick - last_interaction_tick`.
- The new formula must stay self-contained from `TRUST_BONUS_WEIGHT`/`score_trust_bonds()`
  (§7.2/`SOC-244`) — same chapter, adjacent section, easy to accidentally conflate; they compute
  different things for different call sites.
- `resolve_lifecycle` operates on the frozen pre-tick `state` baseline throughout — `_select_default_heir`
  must never read from `refined_entity_updates`/`update.entity_updates` (pending, in-progress
  updates from earlier in the same tick); it reads only `state.entities` and `deceased.social.bonds`,
  consistent with every other read in this file.
- `SOC-245`'s `test_path` must point at a test that actually exists and passes before the entry is
  added — do not add the ledger entry speculatively ahead of Step 3 landing.

## Deviations

None. All 6 steps were implemented exactly as specified:

- Step 1: `_select_default_heir` added verbatim as specified.
- Step 2: succession block rewired exactly per the plan's replacement code (`heir_id` local variable
  pattern, `LifecycleUpdate.heir_entity_id_set` via `replace()` on the same `EntityUpdate`, unmodified
  `if heir:` liveness check).
- Step 3: all 7 listed tests added, plus the anti-drift regression test for a manually-set heir
  pointing at a present-but-inactive entity (`test_manual_heir_entity_id_transfers_even_if_heir_inactive`)
  — confirmed absent from existing coverage before adding, per the plan's "add if missing" instruction.
  8 new tests total; the 5 pre-existing unrelated tests plus `test_succession_and_heirloom_transfer`
  are byte-for-byte unchanged.
- Step 4: full regression surface run (`tests/unit/progression/test_lifecycle.py`,
  `tests/unit/social/test_social_bonds.py`, `test_relationships.py`, `test_party_composition.py`, and
  `tests/unit/progression/ tests/unit/social/ -m "not slow"`) — all green (258 passed, 1 deselected;
  14/14 in `test_lifecycle.py`).
- Step 5: doc subsection inserted verbatim between `Birth/Death Law` and `Migration Law`.
- Step 6: `SOC-245` entry appended verbatim after `SOC-244`; YAML parses (266 total entries).
