---
status: historical
layer: core
authority: P2
audience: agent
ticket_id: TCK-20260902-REPRODUCTION-BIRTH-RECORD-SCHEMA
artifact_type: plan
tags: [lifecycle, core]
---

# Implementation Plan — TCK-20260902-REPRODUCTION-BIRTH-RECORD-SCHEMA

## Summary

Add five new typed fields (`parent_a_entity_id`, `parent_b_entity_id`, `birth_tick`,
`birth_city_id`, `reproduction_cooldowns`) to `LifecycleComponent`/`LifecycleUpdate`, wire them
through the sole authoritative write path (`LifecyclePatch.apply`), extend
`V2EntityBuilder.lifecycle()` with matching kwargs plus a new `.birth_record()` convenience method
that also seeds the new child's own `SocialBond`s toward its parents, and add a module-level
`build_parent_bond_updates_for_birth()` helper that a future reproduction-trigger ticket can call
to produce the parents' reciprocal `EntityUpdate.social.bond_updates`. No reproduction trigger
logic, no genetics wiring, and no marriage precondition is added anywhere — this ticket is schema
+ builder plumbing only. The per-parent cooldown field is implemented as a `Dict[int, int]`
(partner_entity_id -> cooldown_expiry_tick) with per-key upsert-merge semantics (not the
`CampUpdate.last_raid_tick_set` single-scalar shape, and not a wholesale-replace dict like
`population_cohorts_set`), because that is the only shape that cannot silently clobber one
parent's cooldown entry when both parents are updated independently in the same tick — mirrors
the existing `EntityUpdate.property_updates` per-key-union merge already used in this exact merge
chain (`src/core/updates.py:743`). "High familiarity/sentiment" for AC 4 is set to `0.8`/`0.8`,
grounded in three existing numeric precedents in `src/`: a seeded-bond value of `0.8` in
`src/certification/scenarios.py:248`, the `bond.familiarity > 0.5` "familiar" threshold in
`src/engine/combat.py:100`, and the mirror-image `sentiment < -0.8` extreme-negative threshold in
`src/systems/social_systems/appraisal.py:48`/`:324`/`:335`. No new `RelationshipRole` enum value
is added — seeded bonds keep `role=RelationshipRole.NEUTRAL` (the existing default), since
`src/core/models/social.py` only defines `NEUTRAL`/`FRIEND`/`RIVAL` and is not in this ticket's
Related Code Areas.

## Steps

### Step 1 — Add new fields to `LifecycleComponent`
**Files:** `src/core/state.py`
**Change:** In the `LifecycleComponent` dataclass (`src/core/state.py:151-180`, confirmed by direct
read: current fields are `age_ticks, max_age_ticks, is_permadeath, death_tick, death_reason,
generation, heir_entity_id, heirlooms, active, _canonical_cache`), add five new fields directly
after `heirlooms: list[str] = field(default_factory=list)` and before `active: bool = True`:
```python
parent_a_entity_id: Optional[int] = None
parent_b_entity_id: Optional[int] = None
birth_tick: int = 0
birth_city_id: Optional[int] = None
reproduction_cooldowns: Dict[int, int] = field(default_factory=dict)  # partner_entity_id -> cooldown_expiry_tick
```
`birth_tick` is a plain `int` defaulting to `0` (matching the ticket Scope's explicit `(int)`
typing, and matching this dataclass's existing convention of plain-int defaults for
always-populated fields — `age_ticks: int = 0`, `generation: int = 1` — rather than introducing an
Optional wrapper the ticket didn't ask for); `0` doubles as "no birth record" for
world-assembled/pre-existing entities exactly the way `heir_entity_id: Optional[int] = None`
already doubles as "no heir set." `parent_a_entity_id`/`parent_b_entity_id`/`birth_city_id` are
`Optional[int]` per the ticket Scope's explicit parenthetical, `None` for parentless
natural-creature/magical spawns.
Extend `to_canonical_dict()` (`src/core/state.py:165-180`) to include all five new fields, sorting
the new dict field the same way `heirlooms` is already sorted at line 176
(`sorted(list(self.heirlooms))`) and the same way `LocalScarState.to_canonical_dict()` sorts
`behavioral_modifiers` (`src/core/state.py:208`, `dict(sorted(self.behavioral_modifiers.items()))`)
and `RegionState.to_canonical_dict()` sorts `price_modifiers` (`src/core/state.py:289`) — use
`"reproduction_cooldowns": dict(sorted(self.reproduction_cooldowns.items()))` to avoid a
non-deterministic canonicalization source.
**Other writers of `LifecycleComponent` (enumerated):** grepped `LifecycleComponent(` and
`replace(entity.lifecycle` / `dc_replace(entity.lifecycle` across `src/` — exactly two writers
exist today: (1) `LifecyclePatch.apply` (`src/engine/patches.py:69-88`, see Step 3) — the sole
mid-tick authoritative writer; (2) `src/entities/archetype_factory.py:157-160`
(`_replace_lifecycle`), a world-assembly-time helper that does
`dc_replace(entity.lifecycle, active=active)` to flip only the `active` field before the
simulation's first tick. Because `dataclasses.replace()` copies every unspecified field verbatim,
this second writer cannot clobber the five new fields — no change to `archetype_factory.py` is
needed or in scope. `V2EntityBuilder` (`src/core/builder.py:103`,
`self._lifecycle = LifecycleComponent()`) constructs a fresh instance at entity-construction time,
which is not "mutation" of an existing durable entity and is covered separately in Step 4.
**Do NOT touch:** `heirlooms`'s existing `list`/`tuple` looseness (do not "fix" it as part of this
ticket — see `TCK-20260829-LIFECYCLE-HEIRLOOM-INVENTORY-TUPLE-TYPEERROR`); `active`,
`heir_entity_id`, `death_tick`, or any other pre-existing field; `archetype_factory.py`.
**Verify:** `test_lifecycle_component_canonical_dict_round_trip_includes_birth_fields`.

### Step 2 — Add matching `*_set` fields to `LifecycleUpdate`
**Files:** `src/core/updates.py`
**Change:** In `LifecycleUpdate` (`src/core/updates.py:434-462`, confirmed by direct read: current
fields are `age_delta, generation_delta, is_permadeath_set, death_tick_set, death_reason_set,
heir_entity_id_set, heirlooms_add`), add:
```python
parent_a_entity_id_set: Optional[int] = None
parent_b_entity_id_set: Optional[int] = None
birth_tick_set: Optional[int] = None
birth_city_id_set: Optional[int] = None
reproduction_cooldowns_add: Dict[int, int] = field(default_factory=dict)  # per-key upsert, NOT wholesale replace
```
Extend `is_noop()` (lines 445-449) to also require all four new `_set` fields are `None` and
`not self.reproduction_cooldowns_add`. Extend `merge()` (lines 451-462) with last-non-None-wins for
the four `_set` fields (identical pattern to the existing `heir_entity_id_set` line 460) and a
per-key dict-union merge for `reproduction_cooldowns_add` where `other` wins on key conflicts:
`if other.reproduction_cooldowns_add: changes["reproduction_cooldowns_add"] =
{**self.reproduction_cooldowns_add, **other.reproduction_cooldowns_add}`. This exact per-key-union
shape already exists one class up the call chain at `EntityUpdate.merge()`
(`src/core/updates.py:743`, `changes["property_updates"] = {**self.property_updates,
**other.property_updates}`) — reusing a proven pattern rather than inventing a new merge shape.
**Other writers of `LifecycleUpdate` fields (enumerated):** the only current producer of
`LifecycleUpdate` instances with non-default fields is `LifecycleSystem.resolve_lifecycle()`
(`src/systems/lifecycle_systems/lifecycle.py`), which sets `age_delta`, `is_permadeath_set`,
`death_tick_set`, `death_reason_set`, and `heir_entity_id_set` on death/aging ticks. Because the
five new fields all default to `None`/`{}` (no-op values), `resolve_lifecycle()`'s existing
`LifecycleUpdate(...)` construction calls are unaffected — they simply never populate the new
fields, and `is_noop()`/`merge()` treat their absence as a no-op exactly like every other untouched
field today. `EntityUpdate.merge()` (`src/core/updates.py:731`,
`self.lifecycle.merge(other.lifecycle)`) is the caller that invokes `LifecycleUpdate.merge()` when
two same-tick systems both write to the same entity's lifecycle — this is the exact scenario the
per-key dict-union on `reproduction_cooldowns_add` is designed to survive (two different
reproduction-trigger calls in the same tick each updating a different partner's cooldown must not
clobber each other).
**Do NOT touch:** `EntityUpdate.merge()`/`is_noop()` themselves (lines 684-744) — `EntityUpdate`
already treats `lifecycle` as an opaque sub-object via `self.lifecycle.merge(other.lifecycle)` /
`self.lifecycle.is_noop()`, so no change is needed there; any new field lives entirely inside
`LifecycleUpdate`.
**Verify:** `test_lifecycle_update_merges_birth_fields`.

### Step 3 — Extend `LifecyclePatch.apply` to write the new fields
**Files:** `src/engine/patches.py`
**Change:** In `LifecyclePatch.apply()` (`src/engine/patches.py:69-88`, confirmed by direct read:
currently applies `age_ticks`, `generation`, `is_permadeath`, `death_tick`, `death_reason`,
`heir_entity_id`, `heirlooms` inside the `if self.lifecycle:` block at lines 74-86), add the five
new fields to the same `replace(new_lifecycle, ...)` call:
```python
parent_a_entity_id=u_life.parent_a_entity_id_set if u_life.parent_a_entity_id_set is not None else new_lifecycle.parent_a_entity_id,
parent_b_entity_id=u_life.parent_b_entity_id_set if u_life.parent_b_entity_id_set is not None else new_lifecycle.parent_b_entity_id,
birth_tick=u_life.birth_tick_set if u_life.birth_tick_set is not None else new_lifecycle.birth_tick,
birth_city_id=u_life.birth_city_id_set if u_life.birth_city_id_set is not None else new_lifecycle.birth_city_id,
reproduction_cooldowns=(
    {**new_lifecycle.reproduction_cooldowns, **u_life.reproduction_cooldowns_add}
    if u_life.reproduction_cooldowns_add else new_lifecycle.reproduction_cooldowns
),
```
This is invoked via `AuthoritativeApplyPipeline`/`ApplyPath`
(`src/engine/apply_plan.py:725-726`, confirmed cited in investigation.md: `if update.lifecycle is
not None or update.active is not None: p = LifecyclePatch(...)`) — no change needed to
`apply_plan.py` itself since it already dispatches on `update.lifecycle is not None`, which is
already true whenever any `LifecycleUpdate` field (including the new ones) is set.
**Other writers of the apply-path's `changes["lifecycle"]` key:** `LifecyclePatch.apply` is the
only `ComponentPatch` subclass that writes the `"lifecycle"` key into the shared `changes` dict
passed through `AuthoritativeState.apply()` (confirmed: no other `ComponentPatch.apply()` method
in `src/engine/patches.py` touches `changes["lifecycle"]`). No collision risk from other patch
types.
**Do NOT touch:** the `active` handling at lines 72-73, or any other field's apply logic.
**Verify:** `test_lifecycle_patch_apply_writes_birth_fields_through_authoritative_path`.

### Step 4 — Extend `V2EntityBuilder.lifecycle()` with the new kwargs
**Files:** `src/core/builder.py`
**Change:** In `V2EntityBuilder.lifecycle()` (`src/core/builder.py:574-606`, confirmed by direct
read: currently accepts `active, age_ticks, max_age_ticks, is_permadeath, death_tick,
death_reason, generation, heir_entity_id, heirlooms`), add five new keyword-only parameters
mirroring the existing pattern exactly:
```python
parent_a_entity_id: Optional[int] = None,
parent_b_entity_id: Optional[int] = None,
birth_tick: Optional[int] = None,
birth_city_id: Optional[int] = None,
reproduction_cooldowns: Optional[Dict[int, int]] = None,
```
and add corresponding entries to the `updates` dict (line 589-599) following the existing
`if value is not None: current[key] = value` filter at lines 601-603 (`_copy_dict(...)` for
`reproduction_cooldowns`, matching how `heirlooms` uses `_copy_list(...)` at line 598). Because
`_component()` (`src/systems/social_systems/relationships.py:55-64` — confirmed this is the
`_component` helper `builder.py` imports/uses, it filters kwargs to `{f.name for f in
fields(cls) if f.init}`) only keeps kwargs matching real dataclass fields, this is safe even before
Step 1 lands, but must be implemented after Step 1 so the fields actually exist on
`LifecycleComponent`.
**Do NOT touch:** the existing `active`/`age_ticks`/.../`heirlooms` kwargs or their filter logic.
**Verify:** covered jointly with Step 5 below (`test_builder_birth_record_path_two_parent_case`,
`test_builder_birth_record_path_parentless_case`).

### Step 5 — Add `.birth_record()` builder method and parent-side bond-update helper
**Files:** `src/core/builder.py`
**Change:** Add a new `V2EntityBuilder` method, `birth_record()`, that wraps `.lifecycle(...)` (from
Step 4) and `.social(bonds=...)` (`src/core/builder.py:496-544`, unmodified — confirmed it already
accepts `bonds: Optional[Dict[int, SocialBond]]` and applies it wholesale via `_copy_dict`) to seed
the new child's own bonds toward its parents in one call:
```python
def birth_record(
    self,
    *,
    parent_a_entity_id: Optional[int] = None,
    parent_b_entity_id: Optional[int] = None,
    birth_tick: int = 0,
    birth_city_id: Optional[int] = None,
    seed_familiarity: float = 0.8,
    seed_sentiment: float = 0.8,
) -> V2EntityBuilder:
    self.lifecycle(
        parent_a_entity_id=parent_a_entity_id,
        parent_b_entity_id=parent_b_entity_id,
        birth_tick=birth_tick,
        birth_city_id=birth_city_id,
    )
    bonds = {}
    for pid in (parent_a_entity_id, parent_b_entity_id):
        if pid is not None:
            bonds[pid] = SocialBond(
                target_id=pid, familiarity=seed_familiarity, sentiment=seed_sentiment,
                last_interaction_tick=birth_tick,
            )
    if bonds:
        self.social(bonds=bonds)
    return self
```
`role` is deliberately left at its dataclass default (`RelationshipRole.NEUTRAL`,
`src/core/models/social.py:20`) — no new `RelationshipRole` enum value is introduced (see Summary).
`seed_familiarity`/`seed_sentiment` default to `0.8`/`0.8` per the Summary's cited precedents.
Also add a module-level function (not a builder method, since it targets the two *existing* parent
entities, not the entity under construction) that produces the parents' reciprocal
`EntityUpdate`s for a future reproduction-trigger ticket to consume:
```python
def build_parent_bond_updates_for_birth(
    parent_ids: List[int], child_entity_id: int, birth_tick: int,
    familiarity: float = 0.8, sentiment: float = 0.8,
) -> List[EntityUpdate]:
    return [
        EntityUpdate(
            entity_id=pid,
            social=SocialUpdate(bond_updates=[
                SocialBondUpdate(
                    target_id=child_entity_id, familiarity_delta=familiarity,
                    sentiment_delta=sentiment, last_interaction_tick_set=birth_tick,
                )
            ]),
        )
        for pid in parent_ids
    ]
```
This targets `RelationshipService.process_update()`'s existing bond-merge path
(`src/systems/social_systems/relationships.py:51-62`, confirmed by direct read: `bond =
new_bonds.get(tid, SocialBond(target_id=tid)); new_bonds[tid] = replace(bond, familiarity=max(0.0,
min(1.0, bond.familiarity + b_upd.familiarity_delta)), sentiment=max(-1.0, min(1.0, bond.sentiment
+ b_upd.sentiment_delta)), ...)`) — because a brand-new parent-child pair starts from
`SocialBond(target_id=tid)` (familiarity=0.0, sentiment=0.0 defaults,
`src/core/models/social.py:14-20`), passing `familiarity_delta=0.8, sentiment_delta=0.8` lands the
parent's bond at exactly `0.8`/`0.8`, matching the child-side seed values for symmetry. This
function does **not** decide when reproduction happens or set any cooldown — it only builds the
typed `EntityUpdate`s a caller (a future reproduction-trigger ticket, out of scope here) must apply
through the normal authoritative pipeline. `SocialBondUpdate`/`SocialUpdate` are pre-existing,
unmodified classes (`src/core/updates.py:277-283`, `:286-...` — confirmed the class is named
`SocialBondUpdate`, not `BondUpdate` as informally referenced in investigation.md).
**Other writers of `SocialComponent.bonds`:** confirmed via direct read of
`src/systems/social_systems/relationships.py` that `RelationshipService.process_update()` is the
sole authoritative writer of `SocialComponent.bonds` for already-existing entities — the child's
own initial `bonds` dict is set once at construction via `.social(bonds=...)` inside
`birth_record()` (the entity does not exist yet to have an "update" applied to it), never through
`RelationshipService`. This matches investigation.md's Anti-Drift Hazards note explicitly warning
not to conflate the two paths.
**Do NOT touch:** `RelationshipService.process_update()` itself, `SocialBond`/`SocialComponent`
field definitions in `src/core/models/social.py`, or add any `RelationshipRole` enum value.
**Verify:** `test_builder_birth_record_path_two_parent_case`,
`test_builder_birth_record_path_parentless_case`,
`test_builder_birth_record_seeds_child_social_bonds_toward_parents`.

### Step 6 — Add the no-marriage-precondition architecture guard test
**Files:** `tests/unit/progression/test_lifecycle.py` (test only, no source change)
**Change:** Add `test_no_marriage_precondition_in_birth_record_schema_or_apply_path`, asserting
that `birth_record()`/`LifecyclePatch.apply` succeed with no `ContractState`/`ContractStatus`
present anywhere in the touched call path, per test_plan.md's "behavioral form" guidance. Confirmed
via grep (cited in investigation.md) that none of `LifecycleComponent`, `LifecycleUpdate`,
`LifecyclePatch`, `V2EntityBuilder.lifecycle()`, or `RelationshipService` reference
`ContractState`/`ContractStatus`/marriage today — this test locks that in as a regression guard for
every sibling Reproduction-epic child ticket that builds on this schema next.
**Do NOT touch:** `src/core/strategic.py`'s `ContractState`/`ContractStatus` definitions, or add any
marriage-shaped read/precondition to Steps 1-5's code.
**Verify:** `test_no_marriage_precondition_in_birth_record_schema_or_apply_path` itself (it is its
own verification).

### Step 7 — Update docs and parity ledger
**Files:** `docs/core/entities.md`, `docs/mechanics/01_entity_anatomy.md`,
`docs/parity_ledger/social_narrative.yaml`
**Change:**
1. `docs/core/entities.md:52` (confirmed by direct read: the Lifecycle row currently reads `|
   **lifecycle** | LifecycleComponent, state.py:151-180 | age_ticks, max_age_ticks, is_permadeath,
   death_tick, death_reason, generation, heir_entity_id, heirlooms, active |`) — append
   `parent_a_entity_id, parent_b_entity_id, birth_tick, birth_city_id, reproduction_cooldowns` to
   the Key Fields cell, and update the `state.py:151-180` line reference if the new fields shift
   the line range.
2. `docs/mechanics/01_entity_anatomy.md` — add a short new subsection near the existing
   Lifecycle-adjacent elder-bracket content (lines 121-126) documenting: the five new fields, that
   they are populated only at entity-construction time via `V2EntityBuilder.birth_record()` (never
   mutated afterward except `reproduction_cooldowns`, which future reproduction-trigger tickets
   update), and the `0.8`/`0.8` seeded-bond convention.
3. `docs/parity_ledger/social_narrative.yaml` — add a new entry with `id: SOC-259` (verify this is
   still the next-available ID at implementation time — confirmed `SOC-258` is the current max as
   of this Plan phase read), `status: verified`, `priority: P2`, `v2_evidence` citing
   `src/core/state.py` (LifecycleComponent), `src/core/updates.py` (LifecycleUpdate),
   `src/engine/patches.py` (LifecyclePatch), `src/core/builder.py` (`V2EntityBuilder.birth_record`,
   `build_parent_bond_updates_for_birth`), and `test_path` pointing at
   `tests/unit/progression/test_lifecycle.py::test_lifecycle_component_canonical_dict_round_trip_includes_birth_fields`.
   Use `tools/parity_ledger_writer.py` (the sanctioned schema-validating tool) rather than a raw
   YAML edit — per project convention this file is append-only across many tickets over time and a
   raw full-file rewrite risks corrupting concurrent entries.
**Do NOT touch:** `docs/parity_ledger/world_dynamics.yaml` (`WORLD-DEMO-005`/`WORLD-DEMO-006`) or
`docs/mechanics/05_world_evolution.md`'s Birth/Death Law subsection — both describe the unrelated
regional/aggregate `PopulationCohort` demographic model, confirmed out of scope by investigation.md.
Do not modify `SOC-245`.
**Verify:** no automated test; `done-checker`'s `frontmatter_valid` condition checks the new ledger
entry's schema validity.

## Scope Guards

- No reproduction trigger logic (natural-creature, magical/demonic, human/humanoid paths) — those
  are separate sibling child tickets.
- No `GeneticsSystem`/`GeneticProfile` wiring — separate child ticket.
- No population-pressure feedback-loop closure (idea 38) — separate child ticket.
- No marriage-contract read or precondition anywhere in `LifecycleComponent`, `LifecycleUpdate`,
  `LifecyclePatch`, `V2EntityBuilder`, or `RelationshipService` — explicit 2026-08-29 build-order
  decision, verified absent today, must stay absent (Step 6 guards this).
- No new `RelationshipRole` enum value (e.g. no `FAMILY`/`KIN`) — `src/core/models/social.py` is
  not in this ticket's Related Code Areas; "high familiarity/sentiment" is expressed purely through
  the existing float fields.
- No referential-integrity validation of `birth_city_id` against a real region/building registry —
  it is a bare typed `Optional[int]`, nothing more.
- Do not touch `RegionState`/`PopulationCohort`/`WorldUpdate.population_cohorts_set` — unrelated
  regional-demographics model, confirmed structurally independent.
- Do not touch `src/entities/archetype_factory.py` — its `_replace_lifecycle` helper is unaffected
  by the new fields (see Step 1's "Other writers" note) and needs no change.
- Do not "fix" `heirlooms`'s existing `list`/`tuple` type looseness as part of this ticket.
- Do not decide reproduction-cooldown *values* or *when* a cooldown gets written — this ticket only
  builds the field and its typed write path; a future reproduction-trigger ticket decides cooldown
  durations and calls `LifecycleUpdate(reproduction_cooldowns_add=...)` itself.

## Dependency Map

- Step 1 (component fields) has no dependencies — do first.
- Step 2 (update fields) is independent of Step 1 at the Python-file level but must land alongside
  it conceptually since Step 3 needs both.
- Step 3 (patch apply) depends on Steps 1 and 2.
- Step 4 (builder kwargs) depends on Step 1 only (constructs `LifecycleComponent` directly, not
  through the update/patch path).
- Step 5 (`birth_record()` + `build_parent_bond_updates_for_birth()`) depends on Step 4.
- Step 6 (marriage guard test) depends on Steps 1-5 existing to have something to assert about, but
  is otherwise independent (test-only).
- Step 7 (docs/parity) depends on Steps 1-6 being finalized (field names/values must be final before
  documenting them); typically executed by the doc-updater/parity-updater agents in the pipeline's
  Docs/Parity phases rather than by the implementer directly, but is listed here so the
  Acceptance-Criteria Map has a home for AC 6.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC1: `parent_a_entity_id`, `parent_b_entity_id`, `birth_tick`, `birth_city_id`, and a per-parent cooldown field exist as new typed fields, following `heir_entity_id`/`heir_entity_id_set` pattern | Steps 1, 2 | `test_lifecycle_component_canonical_dict_round_trip_includes_birth_fields`, `test_lifecycle_update_merges_birth_fields` |
| AC2: fields written only through typed `EntityUpdate`/`StateUpdate` applied via authoritative apply path, no direct mutation | Step 3 | `test_lifecycle_patch_apply_writes_birth_fields_through_authoritative_path` |
| AC3: `src/core/builder.py` gains a birth-record construction path populating all new fields at creation time | Steps 4, 5 | `test_builder_birth_record_path_two_parent_case`, `test_builder_birth_record_path_parentless_case` |
| AC4: a `SocialBond` is seeded between each parent and the new child at high familiarity/sentiment when built via the new builder path | Step 5 | `test_builder_birth_record_seeds_child_social_bonds_toward_parents` |
| AC5: new unit tests cover canonical-dict round-trip and two-parent/parentless builder cases | Steps 1-5 | all new tests listed in test_plan.md |
| AC6: `docs/core/entities.md`/`01_entity_anatomy.md` documents new fields; new parity ledger entry cites this schema | Step 7 | none (doc/ledger review + `frontmatter_valid`) |
| AC7: no marriage-contract precondition exists anywhere in the new schema or write path | Steps 1-6 (by omission) | `test_no_marriage_precondition_in_birth_record_schema_or_apply_path` |

## Anti-Drift Notes

- `LifecycleUpdate.is_noop()`/`merge()` hand-enumerate every field (`src/core/updates.py:445-462`)
  — a forgotten field here silently fails to merge across same-tick writers with no error. Steps 1-3
  must add every new field to both methods; Step 6's test does not itself catch a missing
  `is_noop()`/`merge()` entry, so this must be reviewed by inspection, not just test-passing.
- The `reproduction_cooldowns_add` merge is a per-key dict union, not a wholesale replace — a
  caller passing an empty `{}` must be indistinguishable from "no cooldown change this tick"
  (`is_noop()` correctly treats `not self.reproduction_cooldowns_add` as no-op for both).
- `birth_tick` uses `0` as the "no birth record" sentinel (matching the ticket's explicit `(int)`
  typing), not `None` — do not silently change this to `Optional[int]` mid-implementation; it would
  contradict the Scope bullet's literal typing and would require re-deciding `to_canonical_dict()`
  and the builder default together.
- `V2EntityBuilder.social(bonds=...)` replaces the **entire** `bonds` dict wholesale
  (`_copy_dict`), not a per-key merge — `birth_record()` must pass a dict containing only the new
  parent entries (which is safe here since the entity is brand-new and has no pre-existing bonds),
  never call `.social(bonds=...)` on an already-constructed entity's builder state without first
  merging in whatever bonds already exist.
- Do not confuse the child's own bond-seeding path (builder-time, `.social(bonds=...)`) with the
  parents' reciprocal bond-seeding path (`SocialUpdate.bond_updates` through
  `RelationshipService.process_update`, only usable on already-existing entities) — the two use
  structurally different mechanisms for a reason described in investigation.md's Anti-Drift Hazards.
- `SOC-258` is the current max parity ledger ID as of this Plan phase read (2026-09-02); confirm it
  has not advanced before assigning `SOC-259` at implementation time, since other concurrent tickets
  in this worktree/session set may land first.

## Deviations

- **Step 4 citation correction (architecture-review finding, not a design change):** Step 4 above
  attributes the `_component()` helper to `src/systems/social_systems/relationships.py:55-64`. This
  is incorrect — `_component()` is actually defined in `src/core/builder.py:55-64` (the file being
  edited in this same step). The implementer used the correct location; no behavior or design was
  affected, this is purely a citation fix in this plan document.
- `SOC-258` was still the current max parity ledger ID at implementation time, so `SOC-259` was
  assigned as planned — no renumbering was needed.
- `LifecycleComponent`'s line range shifted from `state.py:151-180` to `state.py:151-190` after
  adding the five new fields; `docs/core/entities.md`'s citation was updated accordingly (already
  anticipated by Step 7).
- One additional test beyond the plan's enumerated list was added:
  `test_parent_bond_updates_for_birth_apply_through_authoritative_path`, verifying
  `build_parent_bond_updates_for_birth()`'s output round-trips correctly through
  `ApplyPath.apply_generation()` onto the two existing parent entities. This directly exercises the
  Step 5 helper function, which the plan's Acceptance-Criteria Map did not otherwise assign a
  dedicated test to.
