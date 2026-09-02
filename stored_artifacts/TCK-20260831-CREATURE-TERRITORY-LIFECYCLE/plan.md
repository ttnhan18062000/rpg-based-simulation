---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260831-CREATURE-TERRITORY-LIFECYCLE
artifact_type: plan
tags: [world, ecology]
---

# Implementation Plan — TCK-20260831-CREATURE-TERRITORY-LIFECYCLE

## Summary

Build a new, parallel `CreatureTerritoryService` (mirroring `CampService`'s shape, not its code)
that gives monster-kind entities anchored (by proximity, not a new durable link) to an existing
camp a per-tick `territory_maturity` growth value, scaled 1.5x when the camp's region has
`trauma_score > 50.0` (reusing `CampService`'s exact multiplier shape at `src/world/camp.py:34-40`).
When an entity's `territory_maturity` crosses a fixed threshold, the service spawns a new
territory-occupant monster (reusing `EntityGenerator.spawn_monster`, `src/systems/world_systems/
generator.py:59-83`) and resets that entity's maturity to zero — not a life-stage transition,
since `LifeStageService`/`identity.life_stage` is explicitly off-limits per
`TCK-20260824-LIFE-STAGE-TRANSITIONS`'s Design Decision 1 and the investigation's Anti-Drift
Hazards. The new field lives on `IdentityComponent`/`IdentityUpdate` as a delta-accumulating float
(`territory_maturity` / `territory_maturity_delta`), following `CampState.maturity`/
`CampUpdate.maturity_delta`'s exact precedent, and is wired through all three silent-drop points
`TCK-20260824-LIFE-STAGE-TRANSITIONS` documented: `IdentityUpdate.is_noop()`/`.merge()`, and
`IdentityPatch.apply()`'s `replace()` kwargs (`src/engine/patches.py:226-232`). The new service is
called from `world_dynamics.py`'s existing cadence-gated macro-dynamics block, directly behind a
new `ENABLE_CREATURE_TERRITORY_LIFECYCLE` flag (default OFF) read off `state.feature_flags`
(mirroring `ENABLE_GUILD_QUEST_GENERATION`'s pattern at `src/ai/goals/scorers.py:253-254`), and its
`StateUpdate` is merged into the accumulating `update` via `update.merge(...)` — the same pattern
`demo_update`/`seasonal_update` already use at `src/engine/world_dynamics.py:184-185,190-191` —
because the block's own `update.replace(...)` call at lines 174-182 does **not** include
`entity_updates` in its kwargs and would silently discard anything not merged in that way.

**AC #3 resolution (stated explicitly, not left open):** `BiologicalSystem.update()`
(`src/systems/lifecycle_systems/biological.py:9-43`) is confirmed dead code (investigation.md
Current Behavior #2 — zero production callers). This ticket does not touch it, does not touch
`ApplyPath._compute_entity_changes` (`src/engine/apply.py:70-127`, the real live per-tick hunger/
sleep/age path, which already has no kind gate and is out of scope per the ticket's own Out of
Scope), and does not add any new kind-based gating. AC #3 is satisfied because the new
`territory_maturity` field is purely additive state on a service that never emits a
`BiologicalUpdate` — it does not repurpose, gate, or interact with the hunger/sleep/age accrual
path at all. No `intentional_divergences.md` entry is needed, since nothing is being superseded
(the named "existing" gate was never live in the first place).

## Steps

### Step 1 — Add `territory_maturity` durable field to `IdentityComponent`/`IdentityUpdate`
**Files:** `src/core/state.py`, `src/core/updates.py`, `src/engine/patches.py`

**Change:**
1. `src/core/state.py:471-491` (`IdentityComponent` dataclass, `frozen=True, slots=True`) — add
   `territory_maturity: float = 0.0` as a new field, parallel to the existing `evolution_level: int
   = 1` / `veterancy_points: int = 0` growth fields already on this class (confirmed at
   `src/core/state.py:477-479`).
2. `src/core/state.py:494-512` (`IdentityComponent.to_canonical_dict()`) — add
   `"territory_maturity": self.territory_maturity` to the `res` dict. Note: this canonical dict is
   already a curated subset (it omits `group_id`, `properties`, `cooldowns`, `traits`, `craft_target`
   — confirmed by reading lines 494-512) but *does* include other numeric growth fields
   (`evolution_level`, `evolution_points`, `veterancy_rank`, `unspent_ap`). `to_canonical_dict()`
   feeds `src/engine/checkpoint.py:81` (`state.entities[eid].to_canonical_dict()`), which is used for
   checkpoint/replay fingerprinting — include the new field here so it participates in
   inspection/debug visibility per CLAUDE.md's Durable State Rule.
3. `src/core/updates.py:221-247` (`IdentityUpdate` dataclass) — add
   `territory_maturity_delta: float = 0.0` as a new field, mirroring `CampUpdate.maturity_delta`
   (`src/core/updates.py:836-850`, confirmed delta-based, not last-write-wins) rather than a `_set`
   field, since maturity accrues incrementally every tick the same way `CampState.maturity` does.
4. `src/core/updates.py:240-247` (`IdentityUpdate.is_noop()`) — add
   `self.territory_maturity_delta == 0.0` to the `and`-chain of conditions. **Confirmed this method
   currently omits any check for a field not explicitly listed** — every other numeric delta field
   (`evolution_points_delta`, `veterancy_points_delta`, `unspent_ap_delta`) is explicitly checked;
   the new field must follow the same pattern or a non-zero delta will be silently treated as a
   noop by any caller that checks `is_noop()` before merging (e.g.
   `src/engine/world_dynamics.py:184`'s `if not demo_update.is_noop(): update = update.merge(...)`
   pattern this ticket's Step 4 reuses).
5. `src/core/updates.py:249-269` (`IdentityUpdate.merge()`) — add
   `if other.territory_maturity_delta != 0: changes["territory_maturity_delta"] =
   self.territory_maturity_delta + other.territory_maturity_delta` to the `changes` dict, matching
   the existing `evolution_points_delta`/`veterancy_points_delta` accumulation pattern at
   `src/core/updates.py:260-261`.
6. `src/engine/patches.py:170-232` (`IdentityPatch.apply()`) — **the critical silent-drop point**,
   confirmed by reading the method body: line 180 sets `ep = new_id.evolution_points` (read current
   value), then inside `if self.identity:` (lines 192-208) `ep += u_id.evolution_points_delta`
   applies the delta, and finally the `replace(new_id, role=rl, ..., evolution_points=ep, ...)` call
   at lines 226-232 **explicitly passes `ep` as a kwarg** — any field not passed as a kwarg here
   silently keeps `new_id`'s pre-update value via `dataclasses.replace()`, exactly the trap
   `TCK-20260824-LIFE-STAGE-TRANSITIONS` documented. Add: `tm = new_id.territory_maturity` (read,
   alongside line 180's other reads), `if self.identity: ... tm += u_id.territory_maturity_delta`
   (inside the `if self.identity:` block, alongside line 201's `ep += ...`), and
   `territory_maturity=tm` as an explicit kwarg in the `replace(...)` call at line 226-232.
   Also check the fast-path branch at line 222 (`if not self.identity and ... : changes["identity"]
   = ApplyPath._fast_replace_identity(new_id, intents)`) — this path is only taken when
   `self.identity` is falsy, so it never needs to apply a `territory_maturity_delta` and is
   unaffected.

**Do NOT touch:** `evolution_points`/`veterancy_points`/`unspent_ap` handling in the same methods
(read-adjacent only, do not alter their logic); `IdentityComponent.properties` (free-form dict,
explicitly disallowed for durable meaning per CLAUDE.md Hard Rules — do not store maturity there
instead); `LifeStage` enum or `life_stage`/`life_stage_set` fields (untouched, different concept).

**Verify:** `test_new_maturity_field_survives_apply_generation_round_trip` — extend
`tests/integration/optimization/test_component_patch_apply_parity.py`, following its existing
`IdentityUpdate(role_set=...)` pattern at line 41, substituting
`IdentityUpdate(territory_maturity_delta=5.0)` and asserting the resulting
`AuthoritativeState.entities[id].identity.territory_maturity == 5.0` after a full
`apply_generation()` call (not just `.apply()` in isolation).

---

### Step 2 — Register `ENABLE_CREATURE_TERRITORY_LIFECYCLE` feature flag, default OFF
**Files:** `src/domains/optimization/feature_flags.py`

**Change:** Add `"ENABLE_CREATURE_TERRITORY_LIFECYCLE": FeatureMode.OFF,` to the `self._flags` dict
inside `FeatureFlagManager.__init__` (`src/domains/optimization/feature_flags.py:12-115`),
alongside the other `ENABLE_*` entries (e.g. `ENABLE_GUILD_QUEST_GENERATION` at line 91). This is
not strictly required for `get_flag_mode()` to return `FeatureMode.OFF` for an unregistered flag —
confirmed `get_flag_mode()` at line 125-126 does `return self._flags.get(flag, FeatureMode.OFF)`,
so an absent key already defaults to OFF — but explicit registration matches the DEV-002 policy
convention every other flag in this file follows and keeps the flag discoverable/inspectable
(CLAUDE.md Durable State Rule: durable/config toggles need real, visible declarations, not implicit
absence).

**Do NOT touch:** Any other flag's default value in this file, including `ENABLE_PUSH_EVENT_SHAPERS*`
(confirmed `FeatureMode.ON` — pre-existing, unrelated cutover flags, not to be touched).

**Verify:** `test_creature_territory_lifecycle_flag_default_off_no_behavior_change` (registry-default
half) — assert `FeatureFlagManager().get_flag_mode("ENABLE_CREATURE_TERRITORY_LIFECYCLE") ==
FeatureMode.OFF` on a fresh instance with no overrides.

---

### Step 3 — New `CreatureTerritoryService`: per-species pacing table + trauma-scaled maturity delta
**Files:** `src/world/creature_territory.py` (new file)

**Change:** Create `CreatureTerritoryService`, a static-method service class parallel to (not
importing internals from) `CampService` (`src/world/camp.py:12-19`). Contents:
1. `TERRITORY_MATURITY_RATES: Dict[str, float]` — a real, named, inspectable per-species base
   per-tick maturity rate table, e.g. `{"goblin_warrior": 0.04, "orc_warrior": 0.03}`, with a
   `DEFAULT_TERRITORY_MATURITY_RATE: float = 0.03` fallback for any `entity.kind` not in the table
   (satisfies AC #4's "real inspectable content" requirement — at least 2 distinct species, distinct
   values, confirmed no existing per-species table exists anywhere in `src/world/` per
   investigation.md Risks section).
2. `TERRITORY_MATURITY_THRESHOLD: float = 100.0` — the spawn/reset threshold (see Step 4).
3. `process_territories(state: AuthoritativeState, generator: EntityGenerator) -> StateUpdate`:
   - Iterate `state.camps.items()`, skip inactive camps — mirrors `camp.py:30-32`.
   - For each active camp, resolve its region exactly as `camp.py:37-39` does:
     `from src.engine.legality import LegalityServiceV2; region =
     LegalityServiceV2.get_region_for_position(camp.position, state)` (signature confirmed at
     `src/engine/legality.py:44-46`), and compute `trauma_multiplier = 1.5 if region and
     region.trauma_score > 50.0 else 1.0` — same `> 50.0` threshold, same shape, as
     `src/world/camp.py:38-40`.
   - Find anchored monsters via the **same proximity box-check** as `camp.py:47-50`:
     `e.identity.role == EntityRole.MONSTER and e.combat.alive and abs(e.navigation.position[0] -
     camp.position[0]) < 10 and abs(e.navigation.position[1] - camp.position[1]) < 10`. Use
     `entity.identity.role == EntityRole.MONSTER` (`EntityRole.MONSTER = 2`, confirmed
     `src/core/enums.py:9`) — never `entity.kind` string matching (kind is free-form per
     investigation.md Current Behavior #6).
   - For each anchored monster: `base_rate =
     CreatureTerritoryService.TERRITORY_MATURITY_RATES.get(entity.kind,
     DEFAULT_TERRITORY_MATURITY_RATE)`; `delta = base_rate * trauma_multiplier`; emit
     `EntityUpdate(entity_id=e_id, identity=IdentityUpdate(territory_maturity_delta=delta))`
     into a `Dict[int, EntityUpdate]`.
   - Return `StateUpdate(entity_updates=<that dict>)`.

**Do NOT touch:** `src/world/camp.py` itself — no edits, no shared helper extraction; reuse the
*shape* only, per the ticket's explicit Out of Scope ("Any change to CampService's existing
trauma-to-maturity multiplier for camps themselves — reused, not modified"). Do not import or call
`CampService.process_camps` from the new service — they run independently, called separately from
`world_dynamics.py`.

**Verify:**
- `test_creature_maturity_delta_scales_with_region_trauma` — two otherwise-identical monster
  entities anchored to camps in `trauma_score <= 50.0` vs `trauma_score > 50.0` regions; assert the
  higher-trauma delta equals the lower-trauma delta × 1.5.
- `test_per_species_pacing_constants_are_inspectable` — assert `TERRITORY_MATURITY_RATES` has >= 2
  entries with distinct values.
- `test_region_trauma_increase_never_decreases_maturity_growth_rate` — see dedicated Metamorphic
  Directional Check Design section below.

---

### Step 4 — Maturity-threshold spawn logic (AC #2)
**Files:** `src/world/creature_territory.py` (extends Step 3's file)

**Change:** Within `process_territories` (after computing each anchored monster's `delta` in Step
3), check the crossing condition using the entity's **current, pre-tick** maturity value:
`new_maturity = entity.identity.territory_maturity + delta`. If `new_maturity >=
TERRITORY_MATURITY_THRESHOLD` **and** `entity.identity.territory_maturity <
TERRITORY_MATURITY_THRESHOLD` (the second clause enforces monotonic, exactly-once crossing — the
same "not crossed prematurely" boundary discipline `TCK-20260824-LIFE-STAGE-TRANSITIONS` used, and
what `test_creature_reaches_maturity_threshold_spawns_or_transitions`'s boundary assertion checks):
   - Spawn a new territory occupant via `generator.spawn_monster(entity.navigation.position,
     state=state, kind=entity.kind, difficulty_tier=1)` (reusing `EntityGenerator.spawn_monster`'s
     existing signature, confirmed `src/systems/world_systems/generator.py:59-83` — same call shape
     `camp.py:55-60` already uses), append to `entities_add`.
   - **Reset, do not merely cap, the delta**: override this entity's emitted delta to
     `territory_maturity_delta = -entity.identity.territory_maturity` (i.e. the delta that brings
     the post-apply value to exactly `0.0`, computed from the known pre-tick value — this is a pure
     function of already-read state, no extra read). This intentionally replaces (not adds to) the
     `delta` computed in Step 3 for this entity on the tick it crosses the threshold — document this
     inline in the code as "reset overrides growth on the crossing tick" so a future reader does not
     mistake it for a bug.
   - This resolves the ticket's AC #2 "life-stage transition or spawn a new territory occupant" via
     **spawn**, not a life-stage transition — chosen because it reuses `CampService`'s own
     `CAMP_SPAWN_INTERVAL`-based spawn precedent (`camp.py:44-61`) almost directly, while a
     life-stage transition would require inventing a new creature-specific stage enum (since
     `LifeStage`/`LifeStageService` is explicitly off-limits — see Anti-Drift Hazards). Lower risk,
     concretely one path, per the investigation's own instruction to pick one.

**Do NOT touch:** `IdentityComponent.life_stage` / `LifeStage` enum / `LifeStageService` — no new
life-stage machinery is added; `generator.spawn_monster`'s own implementation (call only, do not
modify its signature or body).

**Verify:** `test_creature_reaches_maturity_threshold_spawns_or_transitions` — construct a monster
just below `TERRITORY_MATURITY_THRESHOLD`, call `process_territories` once, assert no spawn and
maturity still below threshold; construct one at/above the pre-tick value such that `new_maturity >=
threshold`, call once, assert a new entity appears in `entities_add` with matching `kind`, and assert
the emitted `territory_maturity_delta` for the crossing entity equals `-entity.identity.
territory_maturity` (i.e. resulting maturity resolves to `0.0` after apply).

---

### Step 5 — Wire the flag-gated call into `world_dynamics.py`
**Files:** `src/engine/world_dynamics.py`

**Change:** Inside the existing cadence-gated macro-dynamics block (`if should_run(state.tick, None,
cadence.world_dynamics):`, `src/engine/world_dynamics.py:131-192`), add a new numbered sub-step
(`# 3.9 Creature Territory Lifecycle`) directly after `# 3.8 Seasonal calamity pressure propagation`
(lines 187-191), reading the flag the same way `src/ai/goals/scorers.py:253-254` does:
```python
flags = getattr(state, "feature_flags", None) or {}
if flags.get("ENABLE_CREATURE_TERRITORY_LIFECYCLE", "OFF") == "ON":
    from src.world.creature_territory import CreatureTerritoryService
    territory_update = CreatureTerritoryService.process_territories(state, generator)
    if not territory_update.is_noop():
        update = update.merge(territory_update)
```
**Enumeration of other writers to `update` in this function, and why `.merge()` is the only safe
integration point (Fact-Verification Requirement #2):**
- Section 1 (`src/engine/world_dynamics.py:29-41`, hazard drain) and section 2.3 (lines 118-125,
  trauma concern injection) both mutate `update.entity_updates` **in place** (it is a plain mutable
  `dict` held by the frozen `StateUpdate` dataclass — confirmed by `refined_entity_updates[e_id] =
  ...` / `update.entity_updates[eid] = ...` assignments at lines 40 and 125). These run *before*
  section 3 and are unaffected by this step (this step only adds a new sub-block after 3.8, does not
  touch entity_updates written earlier).
- Inside section 3 itself, the `update = update.replace(...)` call at lines 174-182 sets
  `entities_add`, `nodes_add`, `camp_updates`, `maturity_set`, `last_calamity_tick_set`,
  `next_node_id_set`, `next_entity_id_set` — **it does not list `entity_updates` as a kwarg**, so
  `dataclasses.replace()` (via `StateUpdate.replace()`) preserves the existing `update.entity_updates`
  dict reference unchanged. Confirmed by reading the call: no `entity_updates=` kwarg present.
- `demo_update` (line 172, `DemographicCycleService.process_demographics`) and `seasonal_update`
  (line 189, `CalamityPressurePropagator.propagate_seasonal`) are each merged in via `update =
  update.merge(demo_update)` / `update = update.merge(seasonal_update)` (lines 184-185, 190-191) —
  **not** folded into the `.replace()` call — precisely because `.merge()` (via
  `StateUpdate.merge_many`, `src/core/updates.py:968-985`) is the mechanism that correctly combines
  `entity_updates` dicts (merging per-key `EntityUpdate.merge()`) and `entities_add` lists. This
  step's new sub-block follows the exact same `demo_update`/`seasonal_update` pattern for the same
  reason: `CreatureTerritoryService.process_territories()` returns `entity_updates` (Step 3) and
  `entities_add` (Step 4), and only `.merge()` — not `.replace()` — combines those correctly with
  what section 1/2.3 and the earlier `.replace()` call already produced.
- `CampService.process_camps` (line 168, `camp_state_update`) writes only into `camp_updates` and
  `entities_add`, both of which the `.replace()` call at 174-182 folds in explicitly — this step's
  new service is a fully separate, later write and does not race with or overwrite `camp_state_update`'s
  output; `entities_add` is additive (list concatenation via `.replace()`/`.merge()`), so both
  services' spawned monsters coexist correctly regardless of ordering.

**Do NOT touch:** The existing `update.replace(...)` call's kwarg list (lines 174-182) — do not add
`entity_updates=` there; the earlier hazard-drain/trauma-concern-injection blocks (sections 1, 2.1,
2.3); `CampService.process_camps`'s own call at line 168; the `should_run(...)` cadence gate itself
(reuse it, do not add a second, redundant cadence check).

**Verify:**
- `test_creature_territory_lifecycle_flag_on_activates_maturity_processing` — flag ON, qualifying
  monster present, assert non-noop `StateUpdate` output from `WorldDynamicsSystem.resolve_dynamics`.
- `test_creature_territory_lifecycle_flag_default_off_no_behavior_change` (full-pipeline half) —
  flag absent/OFF, assert byte-identical `StateUpdate` output vs. a run where the new service is
  never called at all (no new `entity_updates`/`entities_add` beyond what `CampService` alone
  produces).
- Regression: `tests/unit/world/test_camp_lifecycle.py::test_camp_maturity_and_spawn` must keep
  asserting `maturity_delta == pytest.approx(0.075)` unchanged — confirms this step did not touch
  `CampService`'s own output.

---

### Step 6 — Architecture guard: monster-kind entities stay outside generic biological needs (AC #3)
**Files:** `tests/unit/world/test_creature_territory_lifecycle.py` (new file, no production code
change — this step is test-only, verifying Step 3-5's design decision)

**Change:** Add `test_monster_kind_entities_remain_outside_generic_biological_needs`: run
`CreatureTerritoryService.process_territories` (flag ON, via the full `world_dynamics.py` path) for
a monster-kind entity, and assert the returned `StateUpdate`'s `entity_updates[entity_id].biological`
is `None` for every entity the new service touches — i.e. the new service never constructs or emits
a `BiologicalUpdate`. This is the concrete, executable form of the AC #3 resolution stated in the
Summary above: no new code touches `BiologicalComponent`/`BiologicalUpdate`/`ApplyPath.
_compute_entity_changes` at all, so this assertion should hold by construction; the test exists to
catch any future regression where someone folds hunger/sleep into this service.

**Do NOT touch:** `tests/unit/core/test_biological.py` (must keep exercising the dead-but-tested
`BiologicalSystem.update()` unchanged) or `src/systems/lifecycle_systems/biological.py` itself.

**Verify:** the test itself, run via `python3 -m pytest
tests/unit/world/test_creature_territory_lifecycle.py -v`.

---

### Step 7 — Documentation and parity ledger
**Files:** `docs/mechanics/05_world_evolution.md`, `docs/parity_ledger/world_dynamics.yaml`

**Change:**
1. `docs/mechanics/05_world_evolution.md` — add a new subsection under/adjacent to §6 ("Calamities
   & World Threats") documenting: the per-tick `territory_maturity` delta formula (species base rate
   × trauma multiplier), the reused `trauma_score > 50.0 → ×1.5` rule (cite it as shared with §2's
   existing Regional Trauma & Hazards threshold, not a new threshold), and the
   `TERRITORY_MATURITY_THRESHOLD`-crossing spawn behavior.
2. `docs/parity_ledger/world_dynamics.yaml` — append two new entries after the existing `WORLD-117`
   entry (confirmed the current last entry by reading the file tail), following its exact schema
   (`id`, `text`, `status`, `priority`, `v2_evidence`, `test_path`, `divergence_note`,
   `support_boundary`):
   - `WORLD-118` — text: the trauma-scaled maturity accrual mechanism (AC #1), `status: verified`,
     `priority: P2` (new, non-P0 mechanic — no existing P0 precedent claims this), `v2_evidence`
     citing `src/world/creature_territory.py`, `test_path:
     tests/unit/world/test_creature_territory_lifecycle.py::test_creature_maturity_delta_scales_with_region_trauma`.
   - `WORLD-119` — text: the maturity-threshold spawn mechanism (AC #2), `status: verified`,
     `priority: P2`, `v2_evidence` citing `src/world/creature_territory.py`, `test_path:
     tests/unit/world/test_creature_territory_lifecycle.py::test_creature_reaches_maturity_threshold_spawns_or_transitions`.
3. `docs/guidelines/intentional_divergences.md` — **not touched**, per the AC #3 resolution in the
   Summary (nothing is being superseded).

**Do NOT touch:** Any other parity ledger file or entry, including `WORLD-030`/`WORLD-031`
(`CampService`'s own P0 entries, pre-existing gap, not this ticket's to fix) or `WORLD-023`
(the unrelated global `AuthoritativeState.maturity` field).

**Verify:** No automated test — verified by `validate_frontmatter.py`/parity-ledger schema
validation (run as part of the standard-tier pipeline's Parity phase) and by re-reading the two new
entries against the schema in `docs/parity_ledger/schema.json`.

## Scope Guards

- `src/world/camp.py` is **not modified** at all — no shared-helper extraction, no import of its
  internals beyond reading `region.trauma_score` and `camp.position`/`camp.maturity` fields already
  public on `CampState`. `CampService.MATURITY_PER_TICK` (0.05), `RAID_MATURITY_THRESHOLD` (80.0),
  `CAMP_SPAWN_INTERVAL` (30) stay byte-identical.
- `src/systems/lifecycle_systems/biological.py` (`BiologicalSystem`) is **not touched** — stays dead
  code, stays tested by its own unchanged unit test.
- `src/engine/apply.py` (`ApplyPath._compute_entity_changes`) is **not touched** — the shared,
  performance-sensitive fused-apply hot path for every entity. No new hunger/sleep/age logic is
  added anywhere for monster-kind entities.
- No new field is added to `EntityState`/`NavigationComponent` for camp anchoring. "Anchored to a
  camp/territory" is proximity-inferred every processing tick via the same 10×10 box check
  `camp.py:47-50` already uses — reused as a formula in the new service, not extracted into a shared
  function, not stored durably.
- `IdentityComponent.life_stage` / `LifeStage` enum / `LifeStageService.get_stage_for_age()` /
  `LifecycleSystem.resolve_lifecycle()` are **not touched or reused** for the new mechanic — a
  deliberately separate, third vocabulary per `TCK-20260824-LIFE-STAGE-TRANSITIONS`'s Design
  Decision 1.
- `AuthoritativeState.maturity` (the unrelated global world-level field, consumed by
  `calamity.py`/`raid.py`/`boss.py`/`generator.py`/`checkpoint.py`/`state_presenter.py`/
  `fingerprint.py`) is **never read or written** by any new code in this ticket.
- No RNG is introduced. The maturity delta and threshold check are pure functions of
  `(region.trauma_score, entity.kind, entity.identity.territory_maturity)` — deterministic, per
  CLAUDE.md's Determinism Hard Rule. The spawn call reuses `generator.spawn_monster`'s own existing
  `DeterministicRNG` usage (`src/systems/world_systems/generator.py:67`) unchanged.
- No change to `evolution_points`/`veterancy_points`/`unspent_ap` handling anywhere they are touched
  incidentally while editing `IdentityPatch.apply()` in Step 1.

## Dependency Map

- **Step 1** (durable field) has no dependencies — can be implemented and verified first, in
  isolation, via the integration test alone.
- **Step 2** (feature flag registration) has no dependencies — independent of Step 1.
- **Step 3** (service: base delta + species table) depends on **Step 1** (needs
  `IdentityUpdate.territory_maturity_delta` to exist to construct its `EntityUpdate` output) but not
  on Step 2.
- **Step 4** (threshold spawn logic) depends on **Step 3** (extends the same file/function).
- **Step 5** (wiring into `world_dynamics.py`) depends on **Step 2** (flag must exist to gate on)
  and **Step 3+4** (the service being called must exist and be complete, including spawn logic, so
  the wiring step's regression/activation tests are meaningful).
- **Step 6** (AC #3 architecture guard test) depends on **Step 5** (needs the full wired path to run
  the assertion against real `StateUpdate` output).
- **Step 7** (docs/parity) depends on **Steps 3-5** being complete (needs real file paths and test
  names to cite as `v2_evidence`/`test_path`).

Steps 1 and 2 can be done in parallel by different implementers if desired; everything else is
sequential.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC #1 — trauma-scaled per-tick maturity delta, reusing CampService's 1.5x shape | Step 1 (field), Step 3 (delta logic), Step 5 (wiring) | `test_creature_maturity_delta_scales_with_region_trauma` |
| AC #2 — maturity/age threshold triggers life-stage transition or new-occupant spawn | Step 4 (spawn logic) | `test_creature_reaches_maturity_threshold_spawns_or_transitions` |
| AC #3 — HERO/VILLAGER-only biological gate respected or superseded (with divergence entry) | Steps 1, 3-5 (additive-only design — no touch to biological path) | `test_monster_kind_entities_remain_outside_generic_biological_needs` (Step 6) |
| AC #4 — per-species pacing constants as real content + metamorphic directional check | Step 3 (`TERRITORY_MATURITY_RATES` table) | `test_per_species_pacing_constants_are_inspectable`, `test_region_trauma_increase_never_decreases_maturity_growth_rate` |
| AC #5 — ships behind FeatureMode flag, default OFF | Step 2 (registration), Step 5 (gating) | `test_creature_territory_lifecycle_flag_default_off_no_behavior_change`, `test_creature_territory_lifecycle_flag_on_activates_maturity_processing` |

## Anti-Drift Notes

- **Silent-drop traps (highest-risk item in this plan):** Step 1's three wiring points
  (`IdentityUpdate.is_noop()`, `.merge()`, `IdentityPatch.apply()`'s `replace()` kwargs) must all be
  updated together. `TCK-20260824-LIFE-STAGE-TRANSITIONS` and the same session's
  `TCK-20260831-CLASS-TIER-BRANCHING` both independently hit exactly this trap (the latter omitting
  `class_id` from the `replace()` call). The Step 1 integration test
  (`test_new_maturity_field_survives_apply_generation_round_trip`) must call full
  `apply_generation()`, not just `IdentityPatch.apply()` in isolation, or it will not catch the
  `replace()`-kwarg-omission variant of this trap.
- **`update.entity_updates` merge ordering in `world_dynamics.py` (Step 5):** the `.replace()` call
  at lines 174-182 does not carry `entity_updates` as a kwarg — this is easy to misread as "safe to
  ignore" since the dict reference survives untouched, but any code that instead tries to build its
  own `entity_updates` dict and assign it via `.replace(entity_updates=...)` would **wipe out**
  section 1's hazard-drain and section 2.3's trauma-concern-injection entity updates that ran
  earlier in the same function. Always use `.merge()`, matching `demo_update`/`seasonal_update`.
- **Three distinct "maturity" fields coexist in this codebase after this ticket lands**:
  `AuthoritativeState.maturity` (global int), `CampState.maturity` (per-camp float), and the new
  `IdentityComponent.territory_maturity` (per-entity float). Do not let variable names or log/debug
  strings collapse these into a bare `maturity` reference inside the new service — always
  `territory_maturity` in code, comments, and test names.
- **Pre-existing monster starvation/old-age risk** (investigation.md Risks): monsters already
  accrue `hunger`/`sleep_debt`/`age_ticks` via `ApplyPath._compute_entity_changes` with no relief
  mechanism, and may die of "starvation"/old age independent of this ticket. Do not let the new
  spawn logic (Step 4) try to compensate for this or interact with it — it is explicitly out of
  scope to fix, and doing so here would silently expand this ticket's blast radius.
- **`CampService.process_camps`'s own spawn (`camp.py:44-61`) and this ticket's threshold spawn
  (Step 4) are independent and additive** — both may spawn monsters near the same camp on the same
  tick; this is intentional and matches the existing `entities_add` list-concatenation semantics
  already used for `calamity_update`/`raid_update`/`spawn_update`/`boss_spawn_update`/
  `camp_state_update` at `world_dynamics.py:177`. Do not add cross-service caps or coordination
  logic — out of scope, not requested by any AC.

## Metamorphic Directional Check Design (AC #4)

**Test name:** `test_region_trauma_increase_never_decreases_maturity_growth_rate`
**Location:** `tests/unit/world/test_creature_territory_lifecycle.py`
**Category:** unit, plain pytest (per test_plan.md: wiring into the `src/simulation_quality` lab
metamorphic tooling is explicitly deferred to "once proven working by the pilot ticket" — not
required here).

**Design (concrete, executable):**

```python
import pytest
from dataclasses import replace
from src.world.creature_territory import CreatureTerritoryService

TRAUMA_SAMPLES = [0.0, 40.0, 50.0, 50.01, 51.0, 80.0, 100.0]  # spans the 50.0 threshold exactly

def _delta_for_trauma(trauma_score: float, species: str = "goblin_warrior") -> float:
    """
    Builds a minimal deterministic state: one active camp, one region with the given
    trauma_score, one monster-kind entity of `species` anchored within the camp's 10x10
    proximity box, territory_maturity=0.0. Calls CreatureTerritoryService.process_territories
    directly (no multi-tick simulation) and returns the resulting territory_maturity_delta
    for that entity from the returned StateUpdate's entity_updates.
    """
    ...  # construct AuthoritativeState fixture, call process_territories, extract the delta

@pytest.mark.parametrize("i", range(len(TRAUMA_SAMPLES) - 1))
def test_region_trauma_increase_never_decreases_maturity_growth_rate(i):
    t1, t2 = TRAUMA_SAMPLES[i], TRAUMA_SAMPLES[i + 1]
    assert t2 > t1
    delta_t1 = _delta_for_trauma(t1)
    delta_t2 = _delta_for_trauma(t2)
    # Metamorphic directional relation: increasing trauma must never DECREASE the delta.
    # (It may stay flat below/above the 50.0 threshold, or jump up crossing it.)
    assert delta_t2 >= delta_t1, (
        f"trauma {t1}->{t2} decreased maturity delta: {delta_t1} -> {delta_t2}"
    )
```

This directly encodes the AC #4 requirement ("region trauma increase does not decrease maturity
growth rate") as a real, sampled, parametrized assertion across the threshold boundary (0, 40, 50,
50.01, 51, 80, 100 — chosen to bracket `> 50.0` exactly on both sides, per the mechanics rule's
strict-greater-than semantics confirmed at `docs/mechanics/05_world_evolution.md` §2 and
`camp.py:39`'s `region.trauma_score > 50.0` check, not `>=`). Because the underlying formula is a
step function (`base_rate * (1.5 if trauma > 50.0 else 1.0)`), this test is expected to assert
equality below/above the threshold and a jump at the crossing pair (50.0 -> 50.01) — never a
decrease anywhere in the sampled range, which is what the directional property actually claims.

## Deviations

**Found during Test, 2026-09-01 — a fourth silent-drop point Step 1 missed.**

Step 1's Change note 6 explicitly considered `ApplyPath._fast_replace_identity`
(`src/engine/apply.py:515-537`, referred to there as "the fast-path branch at line 222") and
concluded: *"this path is only taken when `self.identity` is falsy, so it never needs to apply a
`territory_maturity_delta` and is unaffected."* That reasoning is wrong in a way the plan did not
anticipate: the fast path doesn't apply a delta on top of an existing component (true, there's no
`IdentityUpdate` on that path to read a delta from) — but it **reconstructs the entire
`IdentityComponent` from scratch**, field by field, via `object.__new__` + `object.__setattr__`,
completely bypassing `dataclasses.replace()`. `territory_maturity` was never added to that
reconstruction's field list, so it was silently dropped outright (not merely "not incremented") on
every update whose `EntityUpdate` carries only `intent_results` — exactly the shape produced by a
shop buy/sell or quest-reward-grant intent (see `src/engine/patches.py:224-225` for the exact
routing condition). The Step 1 verification test
(`test_new_maturity_field_survives_apply_generation_round_trip`) drove an
`IdentityUpdate(territory_maturity_delta=5.0)`, which takes the *normal* `replace()` path (patches.py
line 227's `else` branch), never the fast path — so it structurally could not have caught this.

Two real tests failed downstream because of this, surfaced only in the Test phase:
`tests/unit/world/test_economy_contract.py::test_shop_buy_and_sell` and
`tests/integration/pipeline/test_transaction_completion.py::TestQuestRewardAtomicity::test_quest_reward_retry_after_freeing_inventory`,
both with `AttributeError: 'IdentityComponent' object has no attribute 'territory_maturity'`.

**Fix (out-of-band from this plan's Step 1, applied directly to `src/engine/apply.py`):** added
`object.__setattr__(res, "territory_maturity", id_comp.territory_maturity)` to
`_fast_replace_identity`, positioned identically to the field's declaration order in
`IdentityComponent` (between `unspent_ap` and `class_id`), carrying the source component's value
through unchanged — consistent with every other field on this path, none of which are
delta-applied here either.

**New test added** (not in the original plan):
`tests/unit/world/test_creature_territory_lifecycle.py::test_fast_replace_identity_preserves_territory_maturity_on_intent_only_update`
— builds an `EntityUpdate` with only `intent_results` set (no `identity`/`group_id_set`/
`property_updates`), runs it through `ApplyPath.apply_generation()` directly, and asserts
`territory_maturity` survives. Verified (via `git stash` of the fix) that this test reproduces the
exact reported `AttributeError` when the fix is absent.

**Lesson for future silent-drop audits:** when a component has more than one construction path
(the normal `replace()`-based path and a hand-built `object.__new__` fast path), each new field
must be checked against *every* construction path independently — "this path doesn't apply a
delta" is not the same claim as "this path preserves the field."
