---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260824-LIFE-STAGE-TRANSITIONS
artifact_type: plan
tags: [cognition]
---

# Implementation Plan — TCK-20260824-LIFE-STAGE-TRANSITIONS

## Summary

Make the already-live `LifeStageService.get_goal_multipliers()` consumer reachable by giving
`IdentityComponent.life_stage` a real typed writer path, then wiring a deterministic, monotonic
forward-only age-based trigger that actually sets it. The work is five narrow, independently
verifiable steps: (1) add `IdentityUpdate.life_stage_set` following the `role_set` precedent
exactly, including the `is_noop()`/`merge()` updates the investigation flagged as the easiest way
to ship an inert no-op; (2) fix `IdentityPatch.apply()`'s `replace()` call to thread the new field
through so it isn't silently dropped; (3) add a new pure `LifeStageService.get_stage_for_age()`
function that duplicates `get_age_bracket()`'s numeric boundaries (3000/7000) without importing
`cohort.py`, per Design Decision 1 (already resolved, not re-litigated here); (4) wire the trigger
into `LifecycleSystem.resolve_lifecycle()` — the precedent-matched, lowest-blast-radius call site —
with an explicit ordinal-based forward-only guard so no world-generated entity (which all start at
`age_ticks=0`/`life_stage=ADULT`) gets misclassified as `CHILD`; (5) add the mandatory boundary-flip
test plus the smaller unit tests from `test_plan.md`, and update the two flagged docs
(`combat_movement.yaml` new entry, roadmap "Known open items" resolution note). Design Decision 2
(`compute_elder_attribute_update()` stays unwired) is followed as given — no step wires it, and
Step 4's implementation explicitly avoids any shared call path with it.

## Steps

### Step 1 — Add `IdentityUpdate.life_stage_set` typed field, fix `is_noop()`/`merge()`

**Files:** `src/core/updates.py`

**Change:**
- `IdentityUpdate` is a frozen dataclass at `src/core/updates.py:219-263` (read directly; confirmed
  no `life_stage_set` field exists among `role_set`/`faction_set`/`evolution_level_set`/etc.,
  lines 222-235). Add a new field immediately after `evolution_level_set: Optional[int] = None`
  (line 226), following the exact `role_set`/`evolution_level_set` shape (a bare
  `Optional[...] = None`, not a delta, not a dict entry in `property_updates`):
  ```python
  life_stage_set: Optional[LifeStage] = None
  ```
- `LifeStage` is not currently imported into `src/core/updates.py` — confirmed at
  `src/core/updates.py:17`, which imports `ItemStack, EquipSlot, AttributeComponent` from
  `src.core.state` but not `LifeStage`. Add `LifeStage` to that same import line (it already
  imports from `src.core.state`, so this is a one-token addition, not a new import line).
- `is_noop()` (`src/core/updates.py:237-243`) enumerates every other field with `and` clauses.
  Add `and self.life_stage_set is None` to the boolean chain. This is the fix for silent-drop trap
  #3 from `investigation.md` (Current Behavior #6 / Risks bullet 2): without this,
  `extract_patches()` (`src/engine/patches.py:698-700`) discards an `IdentityUpdate` containing
  only `life_stage_set` before `apply()` ever runs, because `IdentityPatch.is_noop()`
  (`patches.py:154-156`) delegates straight to `self.identity.is_noop()`.
- `merge()` (`src/core/updates.py:245-263`) follows a uniform `if other.X is not None:
  changes["X"] = other.X` last-write-wins pattern for every `*_set` field (see `role_set` at line
  249, `faction_set` at line 250, `evolution_level_set` at line 253). Add the matching line:
  `if other.life_stage_set is not None: changes["life_stage_set"] = other.life_stage_set`.
  Do not use the `recipes_learned`/`breakthroughs_add`-style set-union pattern — `life_stage_set`
  is a single terminal value, not an accumulating collection, exactly like `role_set`.

**Do NOT touch:** any other field in `IdentityUpdate`; `SocialBondUpdate`/`SocialUpdate` or any
other `*Update` dataclass in this file; `recipes_learned`/`breakthroughs_add`/`traits_add`/
`traits_remove` merge logic (these use union semantics deliberately — `life_stage_set` must not).

**Verify:** `test_identity_update_life_stage_set_not_noop`,
`test_identity_update_life_stage_set_merge_last_write_wins` (test_plan.md items 1–2).

---

### Step 2 — Fix `IdentityPatch.apply()`'s `replace()` call to thread `life_stage` through

**Files:** `src/engine/patches.py`

**Change:**
- `IdentityPatch.apply()` (`src/engine/patches.py:170-226`, read directly) builds local variables
  from `new_id` (lines 176-188: `rl`, `fac`, `rec`, `tgt`, `lvl`, `ep`, `vp`, `vrank`, `ap`, `sk`,
  `tr`, `brk`, `cds` — no `life_stage` local exists today). Add a new local immediately after
  `cds = dict(new_id.cooldowns)` (line 188):
  ```python
  ls = new_id.life_stage
  ```
- Inside the `if self.identity:` block (lines 190-207, which applies each `u_id.*_set`/`*_delta`
  onto the locals), add, following the same one-line-per-field pattern used for `role_set`
  (line 192) and `evolution_level_set` (line 196):
  ```python
  if u_id.life_stage_set is not None: ls = u_id.life_stage_set
  ```
- **This is the real silent-drop fix (trap #2 from investigation.md).** The final `replace()` call
  at lines 221-226 currently omits `life_stage=...` entirely — confirmed by direct read, it lists
  `role=rl, faction=fac, known_recipes=..., craft_target=tgt, evolution_level=lvl,
  evolution_points=ep, veterancy_points=vp, veterancy_rank=vrank, unspent_ap=ap,
  learned_skills=frozenset(sk), traits=frozenset(tr), active_breakthroughs=frozenset(brk),
  cooldowns=ReadOnlyDict(cds), group_id=gid, properties=ReadOnlyDict(props),
  latest_intent_results=intents` and stops — no `life_stage`. Because `dataclasses.replace()`
  preserves any field not passed as a kwarg, `new_id.life_stage` (the OLD value) would silently
  survive unchanged even after Step 1 adds `life_stage_set`, unless this call is fixed. Add
  `life_stage=ls` to the kwarg list (placement anywhere in the list is fine; the current file's
  Do NOT touch note below governs sequencing preference).
- **`_fast_replace_identity` is out of scope for this step and does not need fixing.** Confirmed by
  direct read of the branch condition at `src/engine/patches.py:218`:
  `if not self.identity and self.group_id_set is None and not self.property_updates and
  self.intent_results:`. `self.identity` holds an `IdentityUpdate` dataclass instance (or `None`);
  a populated dataclass instance has no custom `__bool__`, so it is always truthy regardless of
  which fields are set — `not self.identity` is `False` whenever `self.identity` is a non-`None`
  `IdentityUpdate`, including a `life_stage_set`-only one. This branch is therefore provably
  unreachable whenever `life_stage_set` is populated; it always forces the `else` branch (the
  `replace()` call this step fixes). `ApplyPath._fast_replace_identity`'s existing
  `life_stage=id_comp.life_stage` passthrough (`src/engine/apply.py:529`, cited in
  `investigation.md` Current Behavior #5) is a correct, unrelated passthrough for the
  no-`IdentityUpdate` case and requires no change — but the ticket's AC #2 explicitly asks this to
  be *verified*, not silently skipped, so this step's test (below) must assert the `replace()`
  branch is the one actually exercised for a `life_stage_set` update, closing that AC honestly.

**Do NOT touch:** `_fast_replace_identity` itself (`src/engine/apply.py:529`) — no code change
needed there, only verification via the test below; the `VeterancyService.process_points` call
(lines 198-201); `group_id`/`properties`/`latest_intent_results` handling (lines 209-217).

**Verify:** `test_identity_patch_apply_sets_life_stage` (test_plan.md item 3) — must assert the
result comes from the `replace()` branch (e.g. by also setting `intent_results=[]` and
`property_updates={}` so the fast-path guard condition is trivially false regardless, making the
test unambiguous about which branch ran). `test_life_stage_set_survives_full_apply_pipeline`
(test_plan.md item 4) is the full-pipeline confirmation and must also pass.

**Dependency:** requires Step 1 (uses `life_stage_set`).

---

### Step 3 — Add `LifeStageService.get_stage_for_age()` (Design Decision 1, already resolved)

**Files:** `src/ai/life_stage.py`

**Change:**
- `src/ai/life_stage.py` (read directly, 33 lines total) currently contains only
  `LifeStageService.get_goal_multipliers()` (lines 8-32). Add two new pieces to the same class,
  without modifying `get_goal_multipliers()` at all:
  1. A module-level ordinal map (needed for Step 4's monotonic check):
     ```python
     _STAGE_ORDINAL: Dict[LifeStage, int] = {
         LifeStage.CHILD: 0,
         LifeStage.ADULT: 1,
         LifeStage.ELDER: 2,
     }
     ```
  2. Two new static methods on `LifeStageService`:
     ```python
     @staticmethod
     def get_stage_for_age(age_ticks: int) -> LifeStage:
         """
         Pure per-entity age->LifeStage mapping. Numeric boundaries (3000/7000) are
         intentionally duplicated from get_age_bracket() (src/domains/demographics/cohort.py,
         WORLD-DEMO-003 in docs/parity_ledger/world_dynamics.yaml) rather than imported --
         separate vocabularies for separate subsystems (per-entity strategic cognition vs.
         cohort-level aggregate demographics; see TCK-20260824-LIFE-STAGE-TRANSITIONS
         investigation.md Design Decision 1), same underlying tick boundaries. If
         get_age_bracket()'s thresholds ever change, this function's literals must change too.
         """
         if age_ticks < 3000:
             return LifeStage.CHILD
         if age_ticks < 7000:
             return LifeStage.ADULT
         return LifeStage.ELDER

     @staticmethod
     def is_forward_transition(current: LifeStage, target: LifeStage) -> bool:
         """True only if target has a strictly higher ordinal than current -- enforces the
         monotonic forward-only rule (never demote), since every world-generated entity starts
         at age_ticks=0 with life_stage=ADULT already set as a construction default, not a
         literal newborn fact (src/core/builder.py:164-214's V2EntityBuilder.identity(),
         confirmed by direct read: life_stage defaults via IdentityComponent's own
         LifeStage.ADULT default, src/core/state.py:488, whenever the builder's life_stage=
         kwarg is left None)."""
         return _STAGE_ORDINAL[target] > _STAGE_ORDINAL[current]
     ```
  3. Add `Dict` is already imported (line 2: `from typing import Dict`); no new typing import
     needed. `LifeStage` is already imported (line 3: `from src.core.state import LifeStage`).

**Do NOT touch:** `get_goal_multipliers()` (lines 8-32) — its multiplier dict values are the
subject of `test_life_stage_multipliers`, which must keep passing unchanged (test_plan.md
Anti-Drift). Do NOT import anything from `src/domains/demographics/cohort.py` here — that would
violate the Out of Scope constraint and create the backwards `src/ai` → `src/domains/demographics`
dependency Design Decision 1 explicitly rejected.

**Verify:** `test_get_stage_for_age_matches_get_age_bracket_numeric_boundaries` (test_plan.md item
7) — this is the regression guard for the duplicated-literal drift risk; it may import
`get_age_bracket` read-only for comparison in the *test file* only (permitted per test_plan.md item
7's own note — reading, not modifying, `cohort.py`).

**Dependency:** independent of Steps 1-2; can be implemented in parallel with them.

---

### Step 4 — Wire the age-based trigger into `LifecycleSystem.resolve_lifecycle()`

**Files:** `src/systems/lifecycle_systems/lifecycle.py`

**Call-site confirmation (per plan requirement to verify, not just follow the recommendation):**
Read `src/systems/lifecycle_systems/lifecycle.py` directly. `resolve_lifecycle()` (lines 34-137) is
called exactly once per tick, unconditionally, from `src/engine/pipeline.py:361`
(`run_phase("lifecycle", update, lambda u: LifecycleSystem.resolve_lifecycle(state, u))`) — it is
not itself cadence-gated. It already loops over every entity (`for e_id, entity in
state.entities.items():`, line 44), skips inactive entities (`if not entity.lifecycle.active:
continue`, line 45), reads `entity.lifecycle.age_ticks` (line 54, durable state) directly, and
builds a `refined_entity_updates: Dict[int, EntityUpdate]` dict that gets merged with the
tick's `StateUpdate` at the end (line 137) — the exact typed-update shape the Architecture Rule
requires. No cadence/ordering conflict exists with where `age_ticks` is incremented
(`ApplyPath._compute_entity_changes`, per investigation.md Current Behavior #7): that increment
happens during the same tick's apply phase, so `resolve_lifecycle()` always reads the
already-current `age_ticks` for that tick's own StateUpdate refinement. Confirmed: this is the
correct site — no reason found to place it elsewhere.

**Change:**
- Add two imports: `from src.core.updates import ... IdentityUpdate` (add `IdentityUpdate` to the
  existing import list at line 4, which currently reads `from src.core.updates import StateUpdate,
  EntityUpdate, LifecycleUpdate, InventoryUpdate`) and `from src.ai.life_stage import
  LifeStageService` (new import line). This direction (`src/systems/lifecycle_systems` →
  `src/ai`) is an existing, accepted pattern elsewhere in the codebase — confirmed by grep:
  `src/systems/social_systems/party.py` and `src/systems/strategic_systems/intelligence.py`
  already import from `src.ai.*`.
- Inside the main loop (after `ent_upd = refined_entity_updates.get(e_id)` at line 48, before the
  `is_dead` checks starting line 51), insert the life-stage check:
  ```python
  # Age-based life-stage transition (TCK-20260824-LIFE-STAGE-TRANSITIONS). Monotonic
  # forward-only: every world-generated entity starts at age_ticks=0 with life_stage=ADULT
  # already correct (construction default, not a "just born" fact) -- an unconditional
  # recompute-and-overwrite would misclassify every entity as CHILD at tick 1.
  target_stage = LifeStageService.get_stage_for_age(entity.lifecycle.age_ticks)
  if LifeStageService.is_forward_transition(entity.identity.life_stage, target_stage):
      ent_upd = ent_upd or EntityUpdate(entity_id=e_id)
      existing_identity = ent_upd.identity or IdentityUpdate()
      ent_upd = replace(ent_upd, identity=replace(existing_identity, life_stage_set=target_stage))
      refined_entity_updates[e_id] = ent_upd
  ```
  This uses the identical `ent_upd = ent_upd or EntityUpdate(entity_id=e_id)` idiom already used
  later in the same function (line 68) — a populated dataclass instance is always truthy, so this
  is safe regardless of `ent_upd`'s field values, consistent with existing file style.
- **Ordering/idempotency interaction with the rest of `resolve_lifecycle()`:** the existing death
  branch (`if is_dead:`, lines 67-79) does `refined_entity_updates[e_id] = replace(ent_upd,
  active=False, lifecycle=replace(life_upd, ...))` — `dataclasses.replace()` preserves every field
  not explicitly passed, so if this step's life-stage block already set `ent_upd.identity` earlier
  in the same loop iteration, the death branch's `replace()` call preserves it unchanged. Both
  updates coexist correctly in the same tick without one clobbering the other. No other writer
  in this file touches `ent_upd.identity` (the only other field-writers in this function are the
  death/heir/heirloom blocks, which write `active`, `lifecycle`, and `resource_transfers` — never
  `identity`), so there is no collision to resolve beyond this.
- **Why running every tick unconditionally is safe (no separate cadence gate needed):** once an
  entity reaches its target stage, `is_forward_transition()` returns `False` on every subsequent
  tick (ordinal comparison, not a repeat-write), so the check is a no-op read after the one tick it
  actually fires — no runaway re-application risk, unlike `compute_elder_attribute_update()`
  (Design Decision 2's rejected-wiring concern, which is about a *delta*-based mechanism, not this
  ordinal-gated *set* mechanism).

**Do NOT touch:** the `is_dead`/`death_reason` block (lines 51-65), the succession/heir block
(lines 81-111), the influence/conquest block (lines 113-135), or `_select_default_heir()` (lines
18-32) — none of these are part of this ticket's scope. Do NOT gate this new block behind
`cadence.lifecycle` or any other cadence check — `resolve_lifecycle()` itself is not cadence-gated
today and this addition must not introduce new cadence-dependent behavior not requested by the
ticket. Do NOT wire `compute_elder_attribute_update()` here or anywhere else (Design Decision 2).

**Verify:** `test_life_stage_flips_at_age_boundary`,
`test_life_stage_transition_is_monotonic_forward_only` (test_plan.md items 5-6) — both must be
added to `tests/unit/progression/test_lifecycle.py` per the recommended location (this step's
chosen call site). Also re-run `test_aging_per_tick`, `test_death_by_old_age`,
`test_combat_death_classification`, `test_permadeath_death_classification`,
`test_succession_and_heirloom_transfer`, and the `test_default_heir_*` family unchanged
(test_plan.md Regression Surface) to confirm no perturbation of existing `resolve_lifecycle()`
behavior.

**Dependency:** requires Steps 1-3 (`life_stage_set` must exist and apply correctly; `LifeStageService.get_stage_for_age`/`is_forward_transition` must exist).

---

### Step 5 — Docs: parity ledger entry + roadmap resolution note

**Files:** `docs/parity_ledger/combat_movement.yaml`, `docs/plans/rpg_design_roadmap/rpg_design_roadmap.md`

**Change:**
- `docs/parity_ledger/combat_movement.yaml`: add one new entry (next sequential `COMB-3xx` ID —
  check the highest existing `COMB-` ID in the file immediately before writing, since concurrent
  tickets may have added entries since `investigation.md` was written; confirmed precedent format
  via direct read of `COMB-311` — `id`, `text` (mechanism + ticket ID + numeric thresholds), `status:
  verified`, `priority: P1` (matching COMB-311's priority; this is a new mechanism, not a `P0`
  combat-legality law, so `P1` not `P0`), `legacy_evidence: null`, `v2_evidence:
  src/systems/lifecycle_systems/lifecycle.py (resolve_lifecycle's life-stage transition check)`,
  `proof_type: regression`, `test_path:
  tests/unit/progression/test_lifecycle.py::test_life_stage_flips_at_age_boundary`,
  `divergence_note: null`). The entry's `text` must state the 3000/7000 boundaries and the
  monotonic-forward-only rule explicitly, and cross-reference `WORLD-DEMO-003` per Decision 1's
  paper-trail requirement (investigation.md Design Decisions section).
- `docs/plans/rpg_design_roadmap/rpg_design_roadmap.md`: the "Known open items" bullet at line 284
  (`- **One possible duplicate system, not yet reconciled.** ... Whoever scopes idea 20 should
  settle this first, not discover it mid-ticket.`) must be rewritten to record the resolution:
  state that `TCK-20260824-LIFE-STAGE-TRANSITIONS` resolved this by keeping the two vocabularies
  separate (different consumers/aggregation levels) while aligning their numeric boundaries
  (`LifeStageService.get_stage_for_age()` in `src/ai/life_stage.py` duplicates `get_age_bracket()`'s
  3000/7000 literals) — do not delete the bullet outright (it documents real history), convert its
  language from open-question framing to resolved-with-link-to-ticket framing.

**Do NOT touch:** any other `COMB-*` entry in `combat_movement.yaml` (in particular, do not modify
`COMB-095`'s existing `legacy_verified`/`test_path: null` state — that P0 gap is explicitly
out of scope per investigation.md's Parity Ledger Overlap section, flagged only as a future
follow-up); `docs/parity_ledger/world_dynamics.yaml` (`WORLD-DEMO-003`/`WORLD-DEMO-004` are
explicitly not touched per investigation.md); any other section of the roadmap doc besides the one
named bullet; `docs/mechanics/04_strategic_cognition.md` or `docs/mechanics/01_entity_anatomy.md`
(investigation.md explicitly found both out of scope — pre-existing gaps this ticket doesn't
create and shouldn't partially patch).

**Verify:** no automated test — verify manually that the new parity entry's `test_path` points at
a real, passing test (from Step 4) and that `docs/REGISTRY.yaml` regenerates cleanly at Finalize
(per CLAUDE.md's unconditional post-migration self-check). Run `make knowledge-index-update` since
`docs/` files changed.

**Dependency:** requires Step 4 (the parity entry's `test_path` must reference a test that exists
and passes).

## Scope Guards

- Never modify `src/domains/demographics/cohort.py`'s `get_age_bracket()` or
  `compute_elder_attribute_update()` themselves, and never modify
  `tests/unit/world/test_demographics.py` — explicitly Out of Scope per the ticket. Read-only
  cross-check imports from a *new test file* are the sole permitted exception (test_plan.md item 7).
- Never wire `compute_elder_attribute_update()` into `resolve_lifecycle()`, any tick loop, or any
  other production call path — Design Decision 2 is resolved as "leave orphaned," not deferred for
  Plan to reconsider.
- Never add `life_stage` to the `stats_dirty` recompute block in
  `ApplyPath._apply_entity_update_to_dict` (`src/engine/apply.py:460-509`) — `life_stage` does not
  feed `SkillScalingService.get_effective_stats`; only `ScoreModifierSystem`/`LifeStageService`
  consume it, downstream of derived-stat recalculation.
- Never implement the trigger as an unconditional "recompute `get_stage_for_age(age_ticks)` and
  always overwrite `life_stage`" — must always go through `LifeStageService.is_forward_transition()`
  (ordinal comparison), never a bare inequality on raw enum/string values.
- Never change `LifeStageService.get_goal_multipliers()`'s multiplier dict values (Step 3 adds new
  methods to the same class but must not touch the existing method's body).
- Never modify `WORLD-DEMO-003`/`WORLD-DEMO-004` entries in `docs/parity_ledger/world_dynamics.yaml`.
- Never modify `docs/mechanics/04_strategic_cognition.md` or `docs/mechanics/01_entity_anatomy.md`
  as part of this ticket (investigation.md found both out of scope for this ticket specifically).
- Never gate the new life-stage check in `resolve_lifecycle()` behind `cadence.lifecycle` or
  introduce any new cadence mechanism — out of scope, and unnecessary given the monotonic guard
  already makes repeated per-tick evaluation safe.

## Dependency Map

```
Step 1 (IdentityUpdate.life_stage_set) ──┐
                                          ├──> Step 2 (IdentityPatch.apply() replace() fix)
Step 3 (LifeStageService.get_stage_for_age /   │
        is_forward_transition) ──────────┼─────┴──> Step 4 (wire into resolve_lifecycle()) ──> Step 5 (docs)
```

Step 1 and Step 3 are independent of each other and can be implemented in either order (or in
parallel). Step 2 depends only on Step 1. Step 4 depends on Steps 1-3 (needs both the field/apply
path and the age→stage/ordinal helpers). Step 5 depends on Step 4 (needs a real, passing test path
to cite in the parity entry).

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| `IdentityUpdate` gains `life_stage_set: Optional[LifeStage]=None` following the `role_set`/`faction_set` precedent exactly | Step 1 | `test_identity_update_life_stage_set_not_noop`, `test_identity_update_life_stage_set_merge_last_write_wins` |
| `IdentityPatch.apply()` applies `life_stage_set` into `IdentityComponent.life_stage`, and `ApplyPath._fast_replace_identity` is verified not to silently drop it on the fast path | Step 2 | `test_identity_patch_apply_sets_life_stage`, `test_life_stage_set_survives_full_apply_pipeline` |
| A concrete age-based transition trigger fires deterministically; a test asserts `identity.life_stage` flips at the defined boundary | Steps 3, 4 | `test_life_stage_flips_at_age_boundary` |
| The investigation/plan explicitly resolves (or explicitly defers with rationale) whether the trigger reuses/aligns with `cohort.py`'s `get_age_bracket()` thresholds | Step 3 (implements Design Decision 1, already resolved in investigation.md) | `test_get_stage_for_age_matches_get_age_bracket_numeric_boundaries` |
| (Ticket Scope) Decide whether `compute_elder_attribute_update()` should be wired to the same age signal | Not implemented anywhere — deliberately (Design Decision 2, already resolved in investigation.md) | `test_elder_modifier_reduces_combat_effectiveness` / `test_non_elder_returns_none` (existing, unchanged — confirm no accidental wiring) |
| (Implicit, monotonic-forward-only hazard) | Step 4 | `test_life_stage_transition_is_monotonic_forward_only` |

## Anti-Drift Notes

- **The single highest-risk mistake in this ticket** is implementing Step 4 as a bare "if
  `get_stage_for_age(age_ticks) != current: overwrite`" instead of routing through
  `is_forward_transition()`'s ordinal check. Every world-generated entity starts at `age_ticks=0`
  (a construction-time bookkeeping default) with `life_stage=ADULT` already correct
  (`src/core/state.py:488`'s own default, confirmed independent of `age_ticks`) — a naive
  recompute-and-overwrite would silently reclassify every entity in the simulation as `CHILD` at
  tick 1. This is not a hypothetical; it is the literal behavior of the wrong implementation.
- **The second highest-risk mistake** is fixing `IdentityPatch.apply()`'s `replace()` call (Step 2)
  while forgetting `IdentityUpdate.is_noop()` (Step 1) — a correct `apply()` is functionally
  invisible if `extract_patches()` never reaches it because `is_noop()` reports `True` for a
  `life_stage_set`-only update. Both steps must land together before either is meaningfully
  testable end-to-end (Step 2's own unit test can pass in isolation while the full pipeline test,
  `test_life_stage_set_survives_full_apply_pipeline`, would still fail if Step 1's `is_noop()` fix
  is missing — that integration test is the one that actually catches this).
- **Do not confuse `_fast_replace_identity` with the real drop risk.** The ticket's own AC text
  says to "verify `ApplyPath._fast_replace_identity` is [...] not silently drop[ping] it" — this
  phrasing could lead an implementer to go fix `_fast_replace_identity` itself. Per investigation.md
  Current Behavior #5 (confirmed independently in this plan's own read of `patches.py:218`), that
  function is provably unreachable whenever `life_stage_set` is populated (a populated
  `IdentityUpdate` instance is always truthy). The real fix is the `replace()` call inside the
  `else` branch (Step 2). Satisfy the AC by adding a test that demonstrates the `else`/`replace()`
  branch is what actually runs for a `life_stage_set` update, not by editing
  `_fast_replace_identity`.
- **Both ticket-charged design questions (representation alignment, `compute_elder_attribute_update`
  wiring) are already resolved in `investigation.md`.** Do not re-open either as part of
  implementation; Steps 3 and 5 exist specifically to *record* those resolutions in code/docs, not
  to make a fresh decision.
- **`resolve_lifecycle()` is shared by three other concerns** (old-age death, combat/permadeath
  death, succession/heirloom transfer) that this ticket must not perturb. The new life-stage block
  in Step 4 is inserted as an independent, additive check that writes only `ent_upd.identity`
  before any of those other blocks run; those other blocks' own `replace()` calls preserve
  whatever `ent_upd.identity` already holds (`dataclasses.replace()` semantics), so there is no
  overwrite race between this new block and the existing death/succession logic — but any future
  edit to those blocks must be checked against this invariant (they must keep using `replace()`
  with only their own fields named, never reconstructing `ent_upd` from scratch).

## Deviations (Implementer, 2026-08-27)

- All five steps were implemented exactly as specified; no plan step was skipped, reordered, or
  functionally altered. Test locations matched the plan's own first-choice options exactly:
  `tests/unit/core/test_identity_update.py` (new, for tests 1-2), `test_component_patches.py`
  (test 3), `test_component_patch_apply_parity.py` (test 4), `tests/unit/progression/
  test_lifecycle.py` (tests 5-6), and a new `tests/unit/strategic/test_life_stage_transitions.py`
  (test 7, plus supplementary direct-boundary and monotonicity unit tests for
  `LifeStageService.get_stage_for_age()`/`is_forward_transition()` beyond the minimum required by
  test_plan.md item 7).
- Live-confirmed the parity ledger's highest `COMB-` ID as `COMB-312` (matching the plan's stated
  review-time value) immediately before writing; added the new entry as `COMB-313`.
- **Environment-only deviation, not a code/scope deviation:** `make knowledge-index-update` (the
  plan's Step 5 verification instruction, "Run `make knowledge-index-update` since `docs/` files
  changed") failed in this sandbox — `tools/knowledge_search.py` lacks the executable bit
  (`-rw-rw-r--`), and running it directly via `python3` instead fails downstream trying to
  download a HuggingFace sentence-transformers model with no network access. This matches the
  pre-existing, already-documented environment gap this same investigation.md's Context Search
  Note hit at the start of this ticket ("index not found" / "fallback ... already confirmed
  unavailable"). Not fixed as part of this ticket (out of scope: unrelated sandbox/tooling
  permissions and network access, not this ticket's implementation). `graphify update .` was run
  successfully as the available substitute code-graph refresh.
