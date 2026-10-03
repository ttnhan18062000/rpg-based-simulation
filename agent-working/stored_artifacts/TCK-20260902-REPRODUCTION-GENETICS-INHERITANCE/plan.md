---
status: historical
layer: systems
authority: P2
audience: agent
ticket_id: TCK-20260902-REPRODUCTION-GENETICS-INHERITANCE
artifact_type: plan
tags: [lifecycle]
---

# Implementation Plan — TCK-20260902-REPRODUCTION-GENETICS-INHERITANCE

## Summary

This plan wires the orphaned `GeneticsSystem`/`GeneticProfile` (`src/systems/lifecycle_systems/genetics.py`)
into a real, live, non-test call path for the first time. It closes the durable-storage gap the ticket text
does not surface: no field for a `GeneticProfile` exists anywhere on `EntityState` today, so AC4 cannot be
satisfied without extending the same four files (`src/core/state.py`, `src/core/updates.py`,
`src/engine/patches.py`, `src/core/builder.py`) that `TCK-20260902-REPRODUCTION-BIRTH-RECORD-SCHEMA` already
extended for the sibling birth-record fields, following the identical pattern: typed field on
`LifecycleComponent` → matching `*_set` field on `LifecycleUpdate` → `LifecyclePatch.apply()` write logic →
`V2EntityBuilder` wiring. The new field lives on `LifecycleComponent` (not a new component) because the
birth-record fields (`parent_a_entity_id`, `parent_b_entity_id`, `birth_tick`, `birth_city_id`) already
establish that component as the home for construction-time-only, never-mutated-after lineage facts — a
`GeneticProfile` is the same shape of fact (Mechanics Bible: "permanent... do not change during simulation").

A new `GeneticsSystem.combine_profiles()` static method (pure, deterministic, seed-driven, reusing the
existing `generate_profile_from_seed()` machinery for its perturbation term) implements the combination
formula. The occupation-bias signal reads `IdentityComponent.role` (an `EntityRole` int already on live
`EntityState`, `src/core/state.py:496`) rather than `RoleSemanticsService`, because the latter requires a
content-catalog `role_id` string that `IdentityComponent` has no field for (confirmed: `IdentityComponent`
has no `role_id`/catalog-key field anywhere in its definition, `src/core/state.py:494-516`) — using it would
require inventing a new live-entity-to-catalog resolution mechanism, which is out of scope. The real, live
caller (AC1) is `V2EntityBuilder.birth_record()` (`src/core/builder.py:619-651`), extended with four new
optional keyword parameters that default to `None`/preserve current behavior for every existing caller
(`EntityGenerator.spawn_natural_creature_offspring()`, and whatever calls it parentless for magical/demonic
spawns) — no live simulation trigger (`HUMANOID-CADENCE-PHASE`) is required to exist first.

## Steps

### Step 1 — Add `genetic_profile` field to `LifecycleComponent`
**Files:** `src/core/state.py`

**Change:** Add `genetic_profile: Optional[GeneticProfile] = None` as a new field at the end of
`LifecycleComponent` (`src/core/state.py:152-167`, after `active: bool = True`, before the
`_canonical_cache` sentinel field). Import `GeneticProfile` from `src.systems.lifecycle_systems.genetics`
at the top of `state.py` (this is the canonical defining module per
`staging_artifacts/.../investigation.md`'s Current Behavior section, not the `src/systems/genetics.py`
re-export shim). Update `LifecycleComponent.to_canonical_dict()` (`src/core/state.py:170-190`) to add
`"genetic_profile": asdict(self.genetic_profile) if self.genetic_profile else None`, matching the existing
`asdict(...) if x else None` pattern already used for other optional nested dataclass fields in this same
file (`src/core/state.py:357`: `"latest_result": asdict(self.latest_result) if self.latest_result else
None`). `LifecycleComponent` is `@dataclass(frozen=True, slots=True)` (`src/core/state.py:151`) with every
existing field defaulted and constructed exclusively via keyword args (`_component(LifecycleComponent,
**current)`, `src/core/builder.py:616`) — appending a new defaulted field at the end is positionally safe
and cannot break any existing construction call.

**Do NOT touch:** `age_ticks`, `max_age_ticks`, `is_permadeath`, `death_tick`, `death_reason`, `generation`,
`heir_entity_id`, `heirlooms`, `reproduction_cooldowns`, `active` — none of these are part of this ticket's
scope. Do not add a new component class.

**Verify:** `test_canonical_dict_round_trip_includes_genetic_profile` (test_plan.md #6).

---

### Step 2 — Add `genetic_profile_set` field to `LifecycleUpdate`
**Files:** `src/core/updates.py`

**Change:** Add `genetic_profile_set: Optional[GeneticProfile] = None` as a new field at the end of
`LifecycleUpdate` (`src/core/updates.py:435-448`, after `reproduction_cooldowns_add`). Update
`is_noop()` (`src/core/updates.py:450-456`) to add `and self.genetic_profile_set is None` to the returned
boolean expression. Update `merge()` (`src/core/updates.py:458-475`) to add:
`if other.genetic_profile_set is not None: changes["genetic_profile_set"] = other.genetic_profile_set`,
matching the exact pattern used for every other `*_set` field in this method (e.g.
`if other.parent_a_entity_id_set is not None: changes["parent_a_entity_id_set"] =
other.parent_a_entity_id_set`, `src/core/updates.py:469`).

**Other writers of `LifecycleUpdate` (enumerated, confirmed by grep across `src/`):**
- `src/engine/domain/combat_actions.py:103` — constructs `LifecycleUpdate(age_delta=0,
  generation_delta=..., is_permadeath_set=...)` on defender death/generation change.
- `src/engine/domain/aoe_actions.py:74` — constructs `LifecycleUpdate(generation_delta=...,
  is_permadeath_set=...)` on AoE victim mortality.
- `src/systems/lifecycle_systems/lifecycle.py:93,108` — `LifecycleSystem` aging/death sweep; only ever
  sets `is_permadeath_set`, `death_tick_set`, `death_reason_set`, `heir_entity_id_set` via `replace(life_upd,
  ...)`.
- `src/engine/movement.py:240` — opportunity-attack lifecycle lift; only sets `age_delta`,
  `generation_delta`, `is_permadeath_set`.
- `src/engine/domain/skill_actions.py:124` — only sets `generation_delta`, `is_permadeath_set`.

None of these five writers reference `parent_a_entity_id_set`/`parent_b_entity_id_set`/`birth_tick_set`
today (confirmed by the same grep — only `V2EntityBuilder.birth_record()` sets those), and a new
`genetic_profile_set` field defaults to `None` in every one of their `LifecycleUpdate(...)` constructor
calls (none pass it positionally — all five use keyword-only construction with a strict subset of fields).
There is no ordering/race/collision risk: `merge()`'s `other.genetic_profile_set is not None` guard means a
death/combat/movement-triggered `LifecycleUpdate` that never touches genetics silently leaves the field
unset, identical to how `parent_a_entity_id_set` already coexists with these five writers today.

**Do NOT touch:** `age_delta`, `generation_delta`, `is_permadeath_set`, `death_tick_set`,
`death_reason_set`, `heir_entity_id_set`, `heirlooms_add`, `reproduction_cooldowns_add` — no change to
their semantics or merge order.

**Verify:** No standalone test required for this step in isolation; covered end-to-end by Step 3's and
Step 5's tests (`is_noop`/`merge` correctness is exercised transitively by the integration round-trip test).

---

### Step 3 — Write `genetic_profile` in `LifecyclePatch.apply()`
**Files:** `src/engine/patches.py`

**Change:** In `LifecyclePatch.apply()` (`src/engine/patches.py:69-96`), inside the `if self.lifecycle:`
block, add `genetic_profile` to the `replace(new_lifecycle, ...)` call:
`genetic_profile=u_life.genetic_profile_set if u_life.genetic_profile_set is not None else
new_lifecycle.genetic_profile`, matching the exact pattern already used for every other `*_set` field in
this same `replace(...)` call (e.g. `parent_a_entity_id=u_life.parent_a_entity_id_set if
u_life.parent_a_entity_id_set is not None else new_lifecycle.parent_a_entity_id`,
`src/engine/patches.py:86`). Also update `LifecyclePatch.is_noop()` (`src/engine/patches.py:60-61`) — no
change needed there, since it already delegates to `self.lifecycle is None or self.lifecycle.is_noop()`,
which Step 2 already extended correctly.

**Other writers of `LifecyclePatch`:** none construct it directly outside `src/engine/patches.py` itself
(confirmed by grep — `LifecyclePatch(` has zero hits elsewhere in `src/`); it is assembled generically from
`EntityUpdate.lifecycle` by the existing patch-dispatch machinery the birth-record-schema ticket already
relied on without modification. No `src/engine/apply_plan.py` changes are needed — the birth-record-schema
ticket's own file list (`investigation.md` Prior Work) confirms this same file was untouched for its
equivalent field additions.

**Do NOT touch:** the `active` handling in `LifecyclePatch.apply()` (`src/engine/patches.py:72-73`), or any
other field in the `replace(...)` call.

**Verify:** `test_birth_record_writes_genetic_profile_via_authoritative_apply_path` (test_plan.md #5).

---

### Step 4 — Add `GeneticsSystem.combine_profiles()` combination function
**Files:** `src/systems/lifecycle_systems/genetics.py`

**Change:** Add a new `@staticmethod combine_profiles(parent_a: GeneticProfile, parent_b: GeneticProfile,
*, combat_lean: bool, seed: int) -> GeneticProfile` on `GeneticsSystem`, alongside the two existing static
methods (`apply_genetic_profile` at `:53-75`, `generate_profile_from_seed` at `:77-97`). Implementation,
per-attribute, for each of the six `GeneticProfile` fields (`strength_mult`, `agility_mult`,
`intelligence_mult`, `wisdom_mult`, `constitution_mult`, `charisma_mult`, all `float` bounded `0.8-1.3` per
`src/systems/lifecycle_systems/genetics.py:22-33`):

```python
COMBAT_ATTRS = {"strength_mult", "agility_mult", "constitution_mult"}

perturbation = GeneticsSystem.generate_profile_from_seed(seed)  # existing method, already 0.8-1.3
for attr in (six field names):
    avg = (getattr(parent_a, attr) + getattr(parent_b, attr)) / 2.0   # convex combo of two [0.8,1.3]
                                                                        # values stays in [0.8,1.3]
    blended = 0.6 * avg + 0.4 * getattr(perturbation, attr)            # convex combo, still [0.8,1.3]
    if combat_lean and attr in COMBAT_ATTRS:
        blended = blended + (1.3 - blended) * 0.35                     # pull 35% toward ceiling, <= 1.3
    result[attr] = round(min(1.3, max(0.8, blended)), 3)                # explicit clamp, defense-in-depth
return GeneticProfile(**result)
```

This stays within `0.8-1.3` by construction (every step is a convex combination of two values already in
that range, or an explicit `min`/`max` clamp) — satisfying the lifecycle-systems-contract's hard multiplier
range law (Extension rule #2, cited in `investigation.md` Mechanics/Engine Constraints) without needing an
`intentional_divergences.md` entry. It is deterministic: identical `parent_a`, `parent_b`, `combat_lean`,
`seed` inputs always produce an identical output (pure function, no engine RNG service call, reuses the
already-independently-tested `generate_profile_from_seed()` for its perturbation term without modifying
it).

**Do NOT touch:** `apply_genetic_profile()` (`:53-75`), `generate_profile_from_seed()` (`:77-97`) — must
remain byte-for-byte unchanged (existing `test_deterministic_profile_from_seed`,
`test_different_seeds_different_profiles`, `test_profile_multipliers_in_range` guard this). Do not touch
`SkillType`, `SkillDefinition`, `SkillScalingSystem.compute_skill_power()` — unrelated (LEG-RPG-145).

**Verify:** `test_combine_genetic_profiles_stays_within_multiplier_range`,
`test_combine_genetic_profiles_is_deterministic` (test_plan.md #1, #2).

---

### Step 5 — Wire occupation-bias + combination into `V2EntityBuilder.birth_record()`
**Files:** `src/core/builder.py`

**Change:** Extend `V2EntityBuilder.lifecycle()` (`src/core/builder.py:575-617`) with a new
`genetic_profile: Optional[GeneticProfile] = None` keyword parameter, added to the `updates` dict
(`src/core/builder.py:595-610`) exactly like every other field there (`if value is not None: current[key]
= value`, `:612-614`).

Extend `V2EntityBuilder.birth_record()` (`src/core/builder.py:619-651`) with four new optional keyword
parameters: `parent_a_genetic_profile: Optional[GeneticProfile] = None`,
`parent_b_genetic_profile: Optional[GeneticProfile] = None`, `parent_a_role: Optional[int] = None`,
`parent_b_role: Optional[int] = None` (the last two are raw `EntityRole` int values — `birth_record()`
already takes every other parent fact as a primitive, e.g. `parent_a_entity_id: Optional[int]`, never a
live `EntityState`/component object — `src/core/builder.py:622-627` — so this matches the builder's
established "primitives only, no state lookups" convention; the builder's own `__init__`
(`src/core/builder.py:91-` onward) never holds a reference to any entity registry or `AuthoritativeState`).

Inside `birth_record()`, after the existing `self.lifecycle(parent_a_entity_id=..., ...)` call
(`src/core/builder.py:634-639`), add:

```python
if parent_a_genetic_profile is not None or parent_b_genetic_profile is not None:
    combat_lean = (parent_a_role == EntityRole.HERO and parent_b_role == EntityRole.HERO)
    a_profile = parent_a_genetic_profile or GeneticsSystem.generate_profile_from_seed(parent_a_entity_id or 0)
    b_profile = parent_b_genetic_profile or GeneticsSystem.generate_profile_from_seed(parent_b_entity_id or 0)
    combo_seed = (parent_a_entity_id or 0) * 1_000_003 + (parent_b_entity_id or 0) * 97 + birth_tick
    combined = GeneticsSystem.combine_profiles(a_profile, b_profile, combat_lean=combat_lean, seed=combo_seed)
    self.lifecycle(genetic_profile=combined)
```

Import `GeneticsSystem`, `GeneticProfile` from `src.systems.lifecycle_systems.genetics`, and `EntityRole`
(already imported in `builder.py` per `spawn_hero()`'s usage pattern in `generator.py` — confirm/add the
import in `builder.py` if not already present) at the top of `builder.py`. The combination only runs when a
caller explicitly passes at least one parent profile — every existing caller (natural-creature/magical
paths, which never pass these new parameters) is completely unaffected, satisfying the "no positional-arg
breakage, no new required kwargs" requirement in `test_plan.md`.

**Other writers of `V2EntityBuilder.lifecycle()`/`birth_record()`:** `src/worldbuilding/compiler.py:535`,
`src/certification/scenarios.py` (×6), `src/systems/world_systems/generator.py:118`, `src/perf/scenarios.py`
(×6) all call `.lifecycle(...)` with only `active=`/`generation=`/`age_ticks=` kwargs — none pass
`genetic_profile`, so the new parameter's `None` default leaves them unaffected. `birth_record()` itself
has one existing real caller today, `EntityGenerator.spawn_natural_creature_offspring()`
(`src/systems/world_systems/generator.py`), which calls it with both parent ids `None` and will not pass
any of the four new parameters — its behavior (parentless, genetics-free) is unchanged.

**Do NOT touch:** the existing `SocialBond` seeding logic in `birth_record()` (`:640-650`) — unrelated to
this ticket. Do not modify `spawn_natural_creature_offspring()` or any magical/demonic spawn function to
pass the new parameters — that would violate the "human/humanoid-only" scope boundary (Anti-Drift Hazards).

**Verify:** `test_genetics_system_has_real_non_test_non_shim_caller` (test_plan.md #4) — `birth_record()` is
this real, live, non-test, non-shim call site. `test_adventurer_parents_bias_toward_combat_attributes`,
`test_civilian_parents_produce_flatter_neutral_spread` (test_plan.md #3).

---

### Step 6 — Anti-drift guard: natural-creature/magical-demonic paths never attach a `GeneticProfile`
**Files:** `tests/unit/world/test_natural_creature_reproduction.py` (extend)

**Change:** Add `test_natural_creature_and_magical_demonic_paths_never_attach_genetic_profile` (test_plan.md
#7), asserting `EntityGenerator.spawn_natural_creature_offspring()` and
`EntityGenerator.spawn_magical_demonic_entity()` produce entities whose
`entity.lifecycle.genetic_profile is None`. This is a test-only step (no production code change) — it locks
in the human/humanoid-only scope boundary as a permanent regression guard.

**Do NOT touch:** `spawn_natural_creature_offspring()`, `spawn_magical_demonic_entity()`, or any other
function in `src/systems/world_systems/generator.py` — this step only adds an assertion, never modifies
those spawn functions (they already never call the new `birth_record()` parameters per Step 5, so this test
should pass with zero production changes).

**Verify:** the new test itself, plus the existing 9 tests in
`tests/unit/world/test_natural_creature_reproduction.py` staying green.

---

### Step 7 — Documentation: Mechanics Bible + lifecycle-systems contract + parity ledger
**Files:** `docs/mechanics/01_entity_anatomy.md`, `docs/simulation/lifecycle_systems_contract.md`,
`docs/parity_ledger/social_narrative.yaml`, `docs/core/entities.md` (conditional)

**Change:**
- `docs/mechanics/01_entity_anatomy.md`: add a new subsection near the existing §5 "Birth Record
  (Reproduction Schema)" documenting the combination formula (convex-combination + occupation-bias pull,
  per Step 4), the `0.8-1.3` range law, and the occupation-bias direction rule (`EntityRole.HERO`-pair vs
  `EntityRole.CITIZEN`/`SHOPKEEPER`-pair), mirroring the birth-record-schema ticket's own subsection.
- `docs/simulation/lifecycle_systems_contract.md`: add a subsection for the new
  `GeneticsSystem.combine_profiles()` assignment mechanism, parallel to the existing "Assignment at spawn"
  subsection, noting this is `GeneticsSystem`'s first real live caller.
- `docs/parity_ledger/social_narrative.yaml`: add a new entry (matches this epic's sibling entries `SOC-259`
  and `WORLD-120` in file choice) documenting the combination mechanism, cross-referencing `SOC-259`, with a
  `test_path` pointing at the new tests from Steps 4-6.
- `docs/core/entities.md`: **only if** `LifecycleComponent`'s field table is already documented in this
  file — update its Key Fields cell to add `genetic_profile` and the new line-range citation from Step 1.
  If the table entry doesn't already exist for `LifecycleComponent`, skip this file (do not add a new table
  row for a component not already documented there — that is a separate, broader doc-structure decision
  outside this ticket's scope).

**Do NOT touch:** `docs/parity_ledger/progression.yaml` (`PROG-028`) — see Scope Guards below. Do not touch
`docs/mechanics/02_combat_laws.md` or any file outside the four listed here.

**Verify:** no automated test; verified by `doc-updater`/`parity-updater` review and the Finalize phase's
doc-consistency checks.

## Scope Guards

- Do not implement the human/humanoid reproduction trigger/cadence logic (cooldown checks, entity pairing)
  — belongs to `TCK-20260902-REPRODUCTION-HUMANOID-CADENCE-PHASE`.
- Do not add genetics involvement to `spawn_natural_creature_offspring()` or
  `spawn_magical_demonic_entity()` — both confirmed genetics-free by their own shipped tickets.
- Do not store the combined `GeneticProfile` (or its component values) inside
  `IdentityComponent.properties: Dict[str, Any]` — forbidden by CLAUDE.md's Durable State Rule.
- Do not add a marriage-contract precondition anywhere in this call path.
- Do not touch `SkillScalingSystem.compute_skill_power()` or `SkillType`/`SkillDefinition` in
  `genetics.py` — unrelated (LEG-RPG-145).
- Do not modify `GeneticsSystem.generate_profile_from_seed()`'s existing behavior — it must coexist
  unchanged alongside the new `combine_profiles()` method.
- Do not let the occupation-bias skew push any resulting multiplier outside `0.8-1.3` — the Step 4 formula
  is designed to make this structurally impossible (convex combinations + explicit clamp); do not remove
  the clamp "for simplicity."
- Do not fix `PROG-028` (`docs/parity_ledger/progression.yaml:281-301`, pre-existing P0 entry with
  `test_path: null`) — flagged by investigation as a pre-existing gap on the same compliance ID
  (LEG-RPG-144) this ticket touches, but out of scope; not in this ticket's Related Code Areas.
- Do not build a live-entity-to-catalog `role_id` resolution mechanism to make `RoleSemanticsService`
  usable against live `EntityState` — `IdentityComponent` has no field for it (Step 5's rationale); that is
  a separate, unscoped piece of work if ever needed.
- Do not wire any downstream consumer of the stored `GeneticProfile` into
  `SkillScalingService.get_effective_stats()` or any other effective-stats pipeline — no consumer exists
  yet and none is required by this ticket's ACs (investigation Risk 4); the profile is standalone/testable,
  not yet visibly affecting combat output.
- Do not add a feature flag for this wiring — per investigation's Prior Work reading, no live
  tick-processing path invokes this function yet (`HUMANOID-CADENCE-PHASE` doesn't exist), so a flag
  provides no rollback value the way `ENABLE_REPRODUCTION_NATURAL_CREATURE_PATH` did for an every-tick
  branch; the flag (if any) belongs to whichever ticket wires a live trigger.
- Do not touch `src/engine/apply_plan.py` — the existing generic `EntityUpdate` → `ComponentPatch`
  dispatch already handles `LifecycleUpdate`/`LifecyclePatch` without per-field registration, confirmed by
  the birth-record-schema ticket's own unchanged file list for its equivalent additions.

## Dependency Map

- Step 1 (state field) has no dependencies — do first.
- Step 2 (`LifecycleUpdate` field) depends on Step 1 only for the imported `GeneticProfile` type being
  available; otherwise independent.
- Step 3 (`LifecyclePatch.apply()`) depends on Step 1 and Step 2 both landing (reads
  `new_lifecycle.genetic_profile` from Step 1, `u_life.genetic_profile_set` from Step 2).
- Step 4 (`combine_profiles()`) has no dependency on Steps 1-3 — pure function, can be implemented and
  unit-tested in isolation, in parallel with Steps 1-3.
- Step 5 (`birth_record()` wiring) depends on Steps 1, 2, 3 (needs the storage/write path to exist to be
  meaningfully testable end-to-end) and Step 4 (calls `combine_profiles()`).
- Step 6 (anti-drift test) depends on Step 5 landing (asserts the new params are never used by the other
  spawn paths — needs the params to exist first to assert their absence meaningfully, though it would also
  pass trivially before Step 5).
- Step 7 (docs) depends on Steps 1-6 all landing — documents the final, implemented behavior.

Suggested order: Step 1 → Step 2 → Step 3 → Step 4 (parallelizable with 1-3) → Step 5 → Step 6 → Step 7.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC1: real, live caller for the first time | Step 5 | `test_genetics_system_has_real_non_test_non_shim_caller` |
| AC2: combined from both parents' profiles, 0.8-1.3 range | Step 4, Step 5 | `test_combine_genetic_profiles_stays_within_multiplier_range`, `test_combine_genetic_profiles_is_deterministic` |
| AC3: measurably different bias for Adventurer-pair vs civilian-pair | Step 4, Step 5 | `test_adventurer_parents_bias_toward_combat_attributes`, `test_civilian_parents_produce_flatter_neutral_spread` |
| AC4: written via typed `EntityUpdate` through authoritative apply path | Step 1, Step 2, Step 3 | `test_birth_record_writes_genetic_profile_via_authoritative_apply_path` |
| AC5: new unit tests following `tests/unit/` conventions | Steps 4, 5, 6 | all new tests listed in test_plan.md |
| AC6: `docs/mechanics/01_entity_anatomy.md` + parity ledger entry | Step 7 | doc-updater/parity-updater review (no pytest) |

## Anti-Drift Notes

- **Determinism boundary:** `combine_profiles()` (Step 4) must remain a pure function with no dependency on
  the engine's `RngService`/`Domain` scoping — it reuses `generate_profile_from_seed()`'s own
  self-contained MD5 mechanism for its perturbation term. Do not refactor it to pull from
  `Domain.SPAWN`/`rng.get_int(...)` — that would change its determinism contract and is unnecessary scope
  expansion.
- **Two-source-of-truth risk avoided:** the new `combine_profiles()` and the existing
  `generate_profile_from_seed()` are two independent, coexisting construction-time assignment mechanisms
  (bred vs spawned entities) per the lifecycle-systems-contract's Extension rule #2 reading in
  investigation.md — this is not a conflict, but do not let one silently call or depend on the other's
  internal seed derivation beyond `combine_profiles()`'s explicit reuse of
  `generate_profile_from_seed()` as its perturbation term.
- **Missing parent-profile fallback:** because no live spawn path (not even `spawn_hero()`) currently calls
  `generate_profile_from_seed()` to populate a parent's own `genetic_profile`, first-generation parents
  will typically have `parent_a_genetic_profile=None`/`parent_b_genetic_profile=None` when
  `HUMANOID-CADENCE-PHASE` eventually calls this path. Step 5's fallback
  (`GeneticsSystem.generate_profile_from_seed(parent_a_entity_id or 0)`) covers this deterministically
  without requiring a backfill of historical entities — do not treat this as a defect requiring a broader
  fix; it is intentionally self-contained.
- **`EntityRole.HERO` as "Adventurer":** this is the closest legacy analog (`spawn_hero()` sets
  `identity.role=EntityRole.HERO`), not a literal enum value — if a future ticket ever introduces a real
  `ADVENTURER` role or a live-entity role-family resolution mechanism, this bias check should be revisited,
  but do not preemptively build that resolution mechanism now (see Scope Guards).
- **Civilian pair definition:** `EntityRole.CITIZEN`/`EntityRole.SHOPKEEPER` only (matching
  `RoleSemanticsService.is_civilian()`'s own legacy fallback set exactly, `src/content_semantics/role.py:71-72`)
  — deliberately excludes `WORKER` and `GUARD`, which `RoleSemanticsService` itself treats as separate
  families (`is_worker`, and `is_combatant` respectively). Any parent-role combination other than
  HERO-HERO or CITIZEN/SHOPKEEPER-CITIZEN/SHOPKEEPER falls through to the same neutral (`combat_lean=False`)
  path as the civilian case — this is intentional (AC3 only requires the two named cases to differ
  measurably, not a full role taxonomy) and should not be expanded without a new ticket.
