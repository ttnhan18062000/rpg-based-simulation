---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260904-LAIR-ENTITY-ANCHOR
artifact_type: plan
tags: [content, world, determinism]
---

# Implementation Plan — TCK-20260904-LAIR-ENTITY-ANCHOR

## Summary

Add a new, parallel `BossService.check_for_lair_spawn` static method in `src/world/boss.py` that
generalizes the *structure* of `check_for_boss_spawn`'s entity-property idempotency pattern
(`identity.properties["boss_region_id"]`) to be keyed by `place_id` instead of `region_id`, using a
new `identity.properties["lair_place_id"]` entity-side property — **Option A** from the
investigation's open question, decided below. `check_for_boss_spawn` itself is left byte-for-byte
untouched: the existing region-scoped `world_boss`/`ancient_sentinel` mechanism and its idempotency
test keep passing unmodified, exactly as the ticket's AC requires ("extended, not replaced").
`PlaceState.occupant_entity_id` remains unwritten (a schema-only field, as it is today) — the plan
explicitly documents why this still satisfies the AC's "keyed via `PlaceState.occupant_entity_id`"
wording in spirit. Content is added via a synthetic fixture (not real `hero_guild_routing` corpus
migration), matching the investigation's recommendation and the sibling CAMPSTATE-PLACE-BRIDGE
ticket's precedent. Lair occupants use a new entity `kind="dragonkin"`, which requires two small,
directly-necessitated edits to `src/observability/event_extractor.py`'s exclusion lists to avoid a
real event-misclassification bug. Docs and the WORLD-085 parity ledger entry are updated to reflect
the new Place-scoped mechanism.

## Decisions on Open Questions (resolved here, per planner's charter)

1. **Central architecture decision — Option A chosen.** Generalize the *pattern* (entity-property
   keying), not the field. `PlaceState.occupant_entity_id` stays write-never in this ticket; no
   `PlaceUpdate` dataclass, no `StateUpdate.place_updates` collection, no `apply_plan.py` insertion
   point is added. Justification: (a) the ticket's own Request Summary frames this as "generalizes...
   the pattern," not "wires up occupant_entity_id"; (b) `src/core/updates.py:969-1026` (confirmed read
   directly) has zero place-related update fields today and `src/engine/apply_plan.py` has zero
   Place-handling code at all — building that plumbing from scratch is real, non-trivial new scope the
   ticket's Scope section does not describe; (c) CAMPSTATE-PLACE-BRIDGE's own discipline ("don't add
   new apply-pipeline plumbing unless truly required") directly applies, since nothing downstream
   *reads* `occupant_entity_id` today — a future ticket (plausibly idea 48's dissolution mechanism,
   which needs to look up "who occupies this Place") is the natural, evidence-backed place to add
   Option B's plumbing, when there is an actual reader to justify it.
   **AC wording resolution, stated explicitly per the ticket's own Risk note**: AC #1 says "keyed via
   `PlaceState.occupant_entity_id` / `place_id`" — this plan satisfies the **`place_id`** half
   literally (the new lock keys off `place.place_id`, closing the exact multi-Lair-per-Region collision
   the AC describes) and satisfies the **`occupant_entity_id`** half only in spirit: the new
   `identity.properties["lair_place_id"]` entity-side field plays the structurally identical role
   `occupant_entity_id` would have played, without literally writing that field. This is a deliberate,
   documented reinterpretation, not a silent one — Verify/Review should treat "not double-spawning
   across multiple LAIR Places in one Region" (the AC's actual observable requirement) as the pass/fail
   bar, not whether `PlaceState.occupant_entity_id` itself is ever non-`None`.

2. **Occupant race/kind — `kind="dragonkin"`, new string, exclusion lists extended.** Dragonkin is the
   best-evidenced race (confirmed: `data/content/entities/entity_archetypes.yaml:256-263`'s
   `dragon_cult_champion` archetype, `data/content/social/factions.yaml:151-154`'s `dragon_cult`
   faction, and `docs/mechanics/05_world_evolution.md:412`'s explicit "Lair-adjacent... owned by
   TCK-20260904-LAIR-ENTITY-ANCHOR" pointer). `EntityGenerator.spawn_monster`/`V2EntityBuilder.kind()`
   treats `kind` as a free-form string with no archetype-catalog lookup (confirmed:
   `src/systems/world_systems/generator.py:60-84`, no `entity_archetypes.yaml` consumption) — using
   `kind="dragonkin"` requires no new resolution machinery. Because this is a genuinely new `kind`
   string (not a reuse of `"world_boss"`/`"ancient_sentinel"`), `src/observability/event_extractor.py`'s
   two exclusion lists — the `spawn_cadence_fired` tuple at line 1357
   (`... not in (None, "world_boss", "ancient_sentinel", "goblin_raider")`) and `_BOSS_KINDS` at line
   1461 (`frozenset(("world_boss", "ancient_sentinel"))`) — must both be extended to include
   `"dragonkin"`. This is not scope creep: it is a directly-necessitated correctness fix for the new
   code path this ticket adds (Step 3 below), not an unrelated improvement to existing behavior.

3. **Content — synthetic fixture chosen, not real `hero_guild_routing` migration.** Confirmed
   (`tests/unit/worldbuilding/test_place_wiring.py:130-164`) that
   `test_hero_guild_routing_real_content_produces_expected_non_uniform_place_kinds` locks
   `mountain_pass_zone` to zero Places (`mountain_places == []`, `report["place_count"] == 3`,
   `set(state.places.keys()) == {"hometown_city", "goblin_camp_place", "haunted_battlefield_ruin"}`).
   Migrating real content would require editing `data/worlds/hero_guild_routing/world.yaml`,
   regenerating `resolved/world.resolved.yaml` via the compile CLI, and deliberately updating this
   locked assertion plus re-auditing any other test asserting fixed `hero_guild_routing` counts.
   CAMPSTATE-PLACE-BRIDGE deliberately avoided this exact kind of real-corpus churn to keep
   `state.camps == {}` stable for every CI-tested world; this ticket follows the same discipline. A
   synthetic fixture (mirroring `test_place_wiring.py`'s own `_minimal_spec()` pattern) is lower-risk,
   AC-acceptable (AC #3 explicitly allows "a synthetic fixture... clearly labeled as such"), and is
   what this plan builds (Step 5).

4. **Out-of-scope guard — dedicated negative test specified.** See Step 6 below.

5. **Parity ledger — WORLD-085 updated, `test_path` supplied.** See Step 8 below.

6. **`difficulty_tier=5` fallback gap — acknowledged, not fixed, and reused as-is.** The Lair spawn
   call reuses the exact same `difficulty_tier=5` convention `check_for_boss_spawn` already uses
   (`boss.py:114`), for consistency (a Lair guardian is a boss-tier encounter). This means it inherits
   the same pre-existing silent fallback (`spawn_config.py`'s `DIFFICULTY_TIERS` only has entries 1-4;
   `generator.py:65`'s `DIFFICULTY_TIERS.get(difficulty_tier, DIFFICULTY_TIERS[1])` silently produces
   tier-1 stats for `difficulty_tier=5`). This is not fixed by this ticket — it is a pre-existing gap
   in a code path (`spawn_monster`) this ticket calls but does not modify, and fixing it would change
   the existing world boss's stats too, which is out of this ticket's scope. Noted in Anti-Drift Notes
   below so Verify does not mistake it for new-ticket behavior.

## Steps

### Step 1 — Add `check_for_lair_spawn` idempotency helper functions to `BossService`

**Files:** `src/world/boss.py`

**Change:** Inside `BossService` (same class as `check_for_boss_spawn`, `boss.py:13-154`), add a new
`@staticmethod check_for_lair_spawn(state: AuthoritativeState, generator: EntityGenerator) ->
StateUpdate`. Structure it as a direct sibling of `check_for_boss_spawn`, reusing its exact
docstring/LAW-comment convention but scoped to Places:

```
LAW:
    At most one active living Lair occupant may exist per LAIR-kind Place.

Lair occupancy source:
    identity.properties["lair_place_id"]
```

Internal helpers (local closures, mirroring `_is_active_living_boss`/`_boss_region_id` at
`boss.py:47-71`):
- `_is_active_living_lair_occupant(entity) -> bool`: `entity.kind == "dragonkin" and
  entity.lifecycle.active and entity.combat.alive`.
- `_lair_place_id(entity) -> str | None`: `entity.identity.properties.get("lair_place_id")`. Unlike
  `_boss_region_id`, this has **no** secondary/fallback lookup layer (no `strategic.home_region_id`
  equivalent, no position-based fallback) — deliberately simpler than the boss helper, because there
  are no pre-existing Lair occupants without this metadata to support (Lair occupancy is entirely new;
  `boss_region_id`'s fallback layers exist specifically for "old bosses that do not have metadata yet,"
  a legacy-compatibility need that does not apply here). Document this simplification in a one-line
  comment so a future reader doesn't assume the omission is an oversight.

Build `place_occupant_map: Dict[str, EntityState]` by scanning `state.entities.values()` exactly like
`region_boss_map` (`boss.py:73-83`), keyed by `_lair_place_id(entity)` instead of `_boss_region_id(entity)`.

**Do NOT touch:** `check_for_boss_spawn` itself, `_is_active_living_boss`, `_boss_region_id`, or
`region_boss_map` — these must remain byte-identical so
`test_boss_spawn_is_idempotent_even_if_existing_boss_left_region` keeps passing unmodified in
behavior, per the ticket's own Scope wording.

**Verify:** No standalone test yet (helpers are private closures) — proven via Step 2's full-function
tests.

### Step 2 — Implement the spawn loop and gate inside `check_for_lair_spawn`

**Files:** `src/world/boss.py`

**Change:** Continuing the same method body from Step 1:

```python
entities_add = []
for place_id, place in state.places.items():
    if place.kind != PlaceKind.LAIR:
        continue
    if place_id in place_occupant_map:
        continue

    region = state.regions.get(place.region_id)
    if region is None:
        continue

    if not (
        state.maturity >= BossService.BOSS_SPAWN_THRESHOLD
        and region.trauma_score >= 20.0
    ):
        continue

    occupant = generator.spawn_monster(
        place.position,
        state=state,
        kind="dragonkin",
        difficulty_tier=5,
    )
    occupant = replace(
        occupant,
        lifecycle=replace(occupant.lifecycle, active=True),
        identity=replace(
            occupant.identity,
            properties={
                **occupant.identity.properties,
                "lair_place_id": place_id,
                "lair_spawn_tick": state.tick,
            },
        ),
    )
    entities_add.append(occupant)
    place_occupant_map[place_id] = occupant

return StateUpdate(entities_add=entities_add)
```

Key deliberate differences from `check_for_boss_spawn`'s spawn block (`boss.py:96-150`), both
intentional and in-scope:
- **Spawn position**: use `place.position` directly (already a content-authored point within the
  parent Region), not a computed region-center with the "never inside town/sanctuary" `abs(cx) < 20`
  adjustment (`boss.py:100-103`) — that adjustment exists because Boss spawns at Region-center with no
  finer-grained position available; a Place already has its own explicit position, so recreating that
  heuristic would be redundant scope, not required by the AC.
- **Gate values unchanged**: reuses the exact same `state.maturity >= BossService.BOSS_SPAWN_THRESHOLD
  and region.trauma_score >= 20.0` gate, reading the *parent Region's* `trauma_score` (via
  `state.regions.get(place.region_id)`), per the investigation's explicit anti-drift instruction not to
  invent a new Place-local trigger condition (e.g. `hazard_level`) — this ticket is about keying
  granularity, not trigger conditions.
- **No `ancient_core` item stack, no `strategic.home_region_id` set, no kind-relabeling `replace()`
  step**: Boss's spawn block sets `inventory.items=[ItemStack(item_id="ancient_core", ...)]` and
  `strategic.home_region_id` (`boss.py:132-144`) — these are Boss-specific narrative/inventory details
  with no Lair equivalent specified anywhere in the ticket; omit them rather than inventing new
  behavior. `kind="dragonkin"` is set directly by `spawn_monster`'s `kind` argument, so no post-hoc
  `replace(kind=...)` step is needed (unlike Boss, which spawns as `"ancient_sentinel"` then relabels to
  `"world_boss"`).

Add `from src.core.state import PlaceKind` to the existing `TYPE_CHECKING`-guarded imports at the top
of `boss.py` if not already available at runtime (currently `PlaceKind` is not imported in this file —
confirmed via `boss.py:1-11`; `AuthoritativeState`/`RegionState` are only under `TYPE_CHECKING`, so
`PlaceKind` needs a real (non-`TYPE_CHECKING`) import since it's used in a runtime comparison
`place.kind != PlaceKind.LAIR`).

**Do NOT touch:** `check_for_boss_spawn`'s spawn block, the `abs(cx) < 20` town-avoidance heuristic, or
`BOSS_SPAWN_THRESHOLD`'s value (`50.0`, `boss.py:18`) — reused, not redefined.

**Verify:**
- `test_lair_spawn_fills_empty_lair_place_when_no_occupant_exists` (new, per test_plan.md #2)
- `test_lair_spawn_is_idempotent_per_place_with_multiple_lairs_in_one_region` (new, per test_plan.md #1)
- `test_lair_spawn_does_not_double_spawn_when_one_of_two_lairs_already_occupied` (new, per test_plan.md #3)

### Step 3 — Extend `event_extractor.py`'s two boss-kind exclusion lists to include `"dragonkin"`

**Files:** `src/observability/event_extractor.py`

**Change:** Two edits, both directly necessitated by Step 2's new `kind="dragonkin"` entities:
1. Line 1357 (`spawn_cadence_fired` exclusion tuple): change
   `not in (None, "world_boss", "ancient_sentinel", "goblin_raider")` to
   `not in (None, "world_boss", "ancient_sentinel", "goblin_raider", "dragonkin")`.
2. Line 1461 (`_BOSS_KINDS`): change `frozenset(("world_boss", "ancient_sentinel"))` to
   `frozenset(("world_boss", "ancient_sentinel", "dragonkin"))` — note this means newly-spawned Lair
   occupants will now also emit `boss_spawned` events (the block immediately following, `1462-1469`),
   which is the correct classification for a Lair-guardian-tier spawn, not a side effect to avoid.

**Other writers to these two lists, enumerated (per Fact-Verification Requirement #2):** both lists are
read-only at these two call sites within `event_extractor.py`'s single `extract_events`-style function;
no other file constructs or mutates `_BOSS_KINDS` or the `spawn_cadence_fired` tuple (confirmed:
`grep -rn "_BOSS_KINDS" src/` and `grep -rn "spawn_cadence_fired" src/` return only these definitions
and this one usage site each within `event_extractor.py` — no cross-module writers exist). This means
the two edits are safe, local, single-file changes with no ordering/race concern — the only interaction
to verify is that `"dragonkin"` was not already present under a different guise (it wasn't) and that no
other exclusion/inclusion list elsewhere in the same file also enumerates boss-like kinds and was
missed — confirmed via the same `_BOSS_KINDS`/kind-tuple grep that only these two sites exist.

**Do NOT touch:** the `_push_shapers_phase2_active` flag-gating around these blocks (both are the
"rollback path" per their own comments; the live `ENABLE_PUSH_EVENT_SHAPERS_PHASE2` path is a
separate shaper system not touched by this ticket — out of scope, unrelated to Lair spawning).

**Verify:** locate the relevant test file via `grep -rl "_BOSS_KINDS\|spawn_cadence_fired" tests/` at
implementation time (test_plan.md's own instruction) and add/extend a narrow assertion confirming a
`kind="dragonkin"` entity in `entities_add` is excluded from `spawn_cadence_fired` and included in
`_BOSS_KINDS`'s `boss_spawned` classification — scope the pytest command precisely per test_plan.md's
`pytest tests/unit/observability/ -k "cadence or boss_kind or spawn" -q` starting point, narrowed once
the exact file/test names are found.

### Step 4 — Wire `check_for_lair_spawn` into `WorldDynamicsSystem.resolve_dynamics`

**Files:** `src/engine/world_dynamics.py`

**Change:** Immediately after the existing "3.4 Boss Spawning" block (`world_dynamics.py:154-160`),
add a new "3.4b Lair Spawning (Deterministic & Idempotent)" block using the *same* cadence gate as Boss
Spawning (`cadence.boss_spawn`, no new `SystemCadence` field) — deliberate reuse, not a new gate,
since the ticket's scope is about keying granularity, not cadence:

```python
# 3.4b Lair Spawning (Deterministic & Idempotent)
if should_run(state.tick, None, cadence.boss_spawn):
    lair_spawn_update = BossService.check_for_lair_spawn(state, generator)
else:
    from src.core.updates import StateUpdate as NewStateUpdate
    lair_spawn_update = NewStateUpdate()
```

**Other writers to `entities_add` at the fold-in site, enumerated (per Fact-Verification Requirement
#2):** the `update.replace(...)` call at `world_dynamics.py:174-182` currently sums `entities_add` from
five sources into one list: `update.entities_add` (pre-existing, from callers before
`resolve_dynamics`), `calamity_update.entities_add`, `raid_update.entities_add`,
`spawn_update.entities_add`, `boss_spawn_update.entities_add`, and `camp_state_update.entities_add`
(confirmed, `world_dynamics.py:177`, single line, all five explicitly listed via `+` concatenation of
lists — no dict-merge collision risk since `entities_add` is a plain list, not a dict keyed by id, so
simple list-concatenation is safe and order-preserving). This step adds a sixth term:
`+ lair_spawn_update.entities_add`, appended at the end of that same `+`-chain, preserving the exact
same "list concatenation, no id-collision possible" safety property the other five sources already
rely on — Lair-spawned entities get fresh ids via `generator.get_next_id()` (same generator instance
already used by every other spawn source in this call, so id allocation is already serialized/ordered
correctly with no ticket-specific change needed).

**Do NOT touch:** any other field in the `update.replace(...)` call (`maturity_set`,
`last_calamity_tick_set`, `nodes_add`, `camp_updates`, `next_node_id_set`, `next_entity_id_set`) — Lair
spawning only contributes to `entities_add`, nothing else.

**Verify:** covered transitively by Step 2's three new tests calling `BossService.check_for_lair_spawn`
directly (unit-level, not through `resolve_dynamics`), plus a spot-check that
`test_world_dynamics_folds_camp_and_calamity_world_updates_into_final_update` and
`test_calamity_boss_spawn` still pass unmodified (they exercise the same `update.replace(...)` call
site and would catch a fold-in regression).

### Step 5 — Add a synthetic LAIR-kind fixture + compile-time coverage test

**Files:** `tests/unit/worldbuilding/test_place_wiring.py`

**Change:** Add one new test, `test_lair_kind_place_compiles_via_worldcompiler` (or similar,
named for what it proves, not for the ticket), mirroring
`test_place_shaped_region_compiles_to_real_place_state` (`test_place_wiring.py:26-44`) exactly but with
`kind="lair"`:

```python
def test_lair_kind_place_compiles_via_worldcompiler():
    """Synthetic fixture (not real corpus content, per this ticket's Option-A/content
    decision) proving a LAIR-kind PlaceSpec compiles to a real PlaceState with
    occupant_entity_id defaulting to None (unwritten in this ticket, see plan.md)."""
    spec = _minimal_spec([
        RegionSpec(
            id="r1", type="wilderness", bounds=(0, 0, 10, 10),
            places=[PlaceSpec(id="p1", kind="lair", position=(5, 5))],
        ),
    ])
    state, _ = WorldCompiler.compile(spec, seed=42)
    place = state.places["p1"]
    assert place.kind == PlaceKind.LAIR
    assert place.occupant_entity_id is None
```

This does **not** touch `data/worlds/hero_guild_routing/` or its `resolved/world.resolved.yaml` — it
uses the same in-memory `_minimal_spec()` construction every other test in this file already uses.
`PlaceKind.LAIR` requires no schema change (already present in `PLACE_SPEC_KINDS`,
`src/worldbuilding/schema.py:34`, confirmed) and `PlaceSpec.kind`'s validator uppercases freely
(`schema.py:65-70`, confirmed — `"lair"` → `"LAIR"`), consistent with every other kind string already
used lowercase in this file's existing tests (`kind="city"`, `kind="ruin"`, `kind="camp"`).

**Do NOT touch:** `test_hero_guild_routing_real_content_produces_expected_non_uniform_place_kinds`
(`test_place_wiring.py:130-164`) — its `mountain_places == []` / `place_count == 3` /
`state.places.keys() == {...}` assertions must remain exactly as they are today, since the
synthetic-fixture path (not real-content migration) was chosen in this plan.

**Verify:** the new test itself; `pytest tests/unit/worldbuilding/test_place_wiring.py -q` (full file)
to confirm no existing assertion in this file was disturbed.

### Step 6 — Add the idempotency tests in `test_world_dynamics.py` (test_plan.md #1–#3)

**Files:** `tests/unit/world/test_world_dynamics.py`

**Change:** Add three new tests directly below
`test_boss_spawn_is_idempotent_even_if_existing_boss_left_region` (`test_world_dynamics.py:75-146`),
constructing `PlaceState`/`RegionState` objects directly (not via `WorldCompiler`), mirroring that
test's own construction style:

1. `test_lair_spawn_fills_empty_lair_place_when_no_occupant_exists` — one `RegionState` (trauma_score
   ≥ 20), one `PlaceState(kind=PlaceKind.LAIR, region_id=<region>, position=...)`, `state.maturity ≥
   50`, no entities. Assert `BossService.check_for_lair_spawn(state, generator).entities_add` has
   exactly one entity with `kind == "dragonkin"` and
   `identity.properties["lair_place_id"] == <place_id>`.
2. `test_lair_spawn_is_idempotent_per_place_with_multiple_lairs_in_one_region` — one `RegionState`,
   two `PlaceState`s (both `kind=PlaceKind.LAIR`, same `region_id`, distinct `place_id`s), two existing
   `kind="dragonkin"` entities each tagged `identity.properties["lair_place_id"]` to its own Place's
   `place_id`. Assert `entities_add == []` — the direct AC-mandated proof neither Place's occupant is
   treated as satisfying the other Place's slot.
3. `test_lair_spawn_does_not_double_spawn_when_one_of_two_lairs_already_occupied` — same two-Place
   setup as #2, but only one Place has an existing occupant entity. Assert exactly one new entity is
   spawned, and that its `identity.properties["lair_place_id"]` equals the *empty* Place's `place_id`,
   not the occupied one's.

All three use `EntityGenerator(42)` and a fresh `AuthoritativeState`, matching
`test_boss_spawn_is_idempotent_even_if_existing_boss_left_region`'s existing construction idiom
(`V2EntityBuilder`/`dataclasses.replace` for tagging `identity.properties`).

**Do NOT touch:** `test_boss_spawn_is_idempotent_even_if_existing_boss_left_region` itself, or any
other existing test in this file — all three are net-new additions below the existing tests.

**Verify:** the three new tests themselves; `pytest tests/unit/world/test_world_dynamics.py -q` (full
file) to confirm `test_boss_spawn_is_idempotent_even_if_existing_boss_left_region`,
`test_calamity_boss_spawn`, `test_world_dynamics_maturity_advancement`, and
`test_world_dynamics_folds_camp_and_calamity_world_updates_into_final_update` all still pass unmodified.

### Step 7 — Add the idea-48 anti-drift guard test

**Files:** `tests/unit/world/test_world_dynamics.py`

**Change:** Add `test_lair_occupant_death_does_not_dissolve_or_transform_the_lair_place` (named to
describe intent, not process). Construct a `RegionState` + one `PlaceState(kind=PlaceKind.LAIR)` +
one active/living `kind="dragonkin"` occupant entity tagged with the matching `lair_place_id`. Kill the
occupant (construct an `EntityUpdate`/`CombatUpdate` marking it dead, or directly build the entity as
already dead/inactive — whichever matches this file's existing death-simulation idiom, check
`test_regional_transformation`/nearby tests in this file for the established pattern before choosing).
Then assert, directly on the unchanged `PlaceState` object (or on a fresh `check_for_lair_spawn` call
against the post-death state): `place.kind == PlaceKind.LAIR` (never mutated to a different
`PlaceKind`), `place.prior_kind is None`, `place.transformed_tick is None` — i.e., nothing in this
ticket's code path ever touches `PlaceState.kind`/`prior_kind`/`transformed_tick` as a side effect of
occupant death. This is a pure negative/architecture guard: it should pass trivially today (nothing in
Steps 1-6 writes those fields), and its purpose is to fail loudly if a future edit accidentally
introduces dissolution-on-death logic inside this ticket's own code.

**Do NOT touch:** do not implement any actual dissolution/transformation logic to make this test
"more meaningful" — the test asserts the absence of behavior, not partial presence of it. Idea 48
(place-type transitions) has no ticket yet and must not be half-built here.

**Verify:** the new test itself, run alongside the rest of `test_world_dynamics.py`.

### Step 8 — Update `docs/world/raid_boss_camp_contract.md`

**Files:** `docs/world/raid_boss_camp_contract.md`

**Change:** Extend the "Boss — `boss.py`" §"Idempotency" subsection (lines 136-140) with a new
paragraph or sub-bullet describing `check_for_lair_spawn`'s parallel, Place-scoped locking mechanism
(`identity.properties["lair_place_id"]`, keyed per `place_id` instead of `region_id`), following the
same structural pattern CAMPSTATE-PLACE-BRIDGE used to add its own "World-gen construction" subsection
to this same doc (lines 76-101). Update "Extension rules" §3 (line 193) — which currently states *"The
idempotency lock is per `region_id` — if multiple boss types should coexist in one region, the locking
mechanism needs extending"* — to note that this limitation is now addressed for LAIR-kind Places
specifically via the new per-`place_id` mechanism (`check_for_lair_spawn`), while the original
`world_boss`/`ancient_sentinel` per-`region_id` mechanism (`check_for_boss_spawn`) is unchanged and
still region-scoped by design (a Region should still have at most one `world_boss`).

**Do NOT touch:** any other section of this doc (e.g. anything describing `CampService`/Camp-Nest
classification, which is explicitly out of scope for this ticket).

**Verify:** doc-only change, no test — reviewed for accuracy against Steps 1-2's actual implementation
during the Doc-Update pipeline phase.

### Step 9 — Update parity ledger `WORLD-085`

**Files:** `docs/parity_ledger/world_dynamics.yaml` (via `tools/parity_ledger_writer.py::write_entry`
— never a raw YAML edit)

**Change:** Confirmed current entry (`world_dynamics.yaml:930-938`):
```yaml
- id: WORLD-085
  text: World boss spawn rule is deterministic.
  status: verified
  priority: P0
  legacy_evidence: null
  v2_evidence: Implementation proven via exhaustive checklist audit Phase 1-11
  proof_type: parity
  test_path: null
  divergence_note: null
```
Call `write_entry("world_dynamics.yaml", entry, ...)` with `id: WORLD-085` unchanged, `status:
verified` unchanged (the `world_boss` rule itself did not change — `check_for_boss_spawn` is untouched
per Step 1's "Do NOT touch"), and:
- `v2_evidence`: updated to note the region-scoped `world_boss` mechanism is unchanged and that a
  parallel Place-scoped idempotency mechanism (`check_for_lair_spawn`, `src/world/boss.py`) was added
  alongside it for LAIR-kind Places, closing the "if multiple boss types should coexist in one region"
  gap `raid_boss_camp_contract.md`'s own Extension-rules §3 previously flagged as open.
- `test_path`: set to
  `tests/unit/world/test_world_dynamics.py::test_boss_spawn_is_idempotent_even_if_existing_boss_left_region`
  — this is the single most directly on-point *passing* test for WORLD-085's literal text ("World
  **boss** spawn rule is deterministic"), which this ticket does not change. (The three new Lair tests
  from Step 6 prove a related but textually distinct rule — Lair spawn determinism — and do not need
  their own new WORLD-08x entry per this ticket's scope; if Verify/Review judges a dedicated Lair
  parity entry is warranted, that is a call for the parity-updater/Verify phase to make explicitly, not
  a silent omission here.)
- Leave `WORLD-086` untouched (per investigation, unaffected — it concerns replay/fingerprint hashing,
  not the locking mechanism).

**Do NOT touch:** `WORLD-086`, or any entry in `substrate.yaml`/`combat_movement.yaml` — investigation
confirmed no other P0 entry references boss/Place/Lair mechanics.

**Verify:** `write_entry`'s own `validate_entry()` call (raises on malformed entry) plus its
in-process parity-index rebuild — no separate test file to run.

### Step 10 — Conditional doc bullet resolution

**Files:** `staging_artifacts/TCK-20260904-LAIR-ENTITY-ANCHOR/investigation.md` (annotation only, not a
code change)

**Change:** Per the investigation's own Format-1-conditional-bullet convention
(`TCK-20260829-DOC-COVERAGE-CONDITIONAL-BULLET-BLIND-DOD-BLOCKED`), since Option A was chosen (no new
`PlaceUpdate`/`StateUpdate.place_updates` apply-path mechanism), the implementer or doc-updater should
append the phrase "Resolved during implementation, condition not met" to the
`docs/world/compiler_contract.md` conditional bullet in investigation.md's "Docs Requiring Update"
section, confirming `compiler_contract.md` does **not** need a new field-list line for a new
update-collection kind, since none was built.

**Do NOT touch:** `docs/world/compiler_contract.md` itself — no edit needed there under Option A.

**Verify:** `done-checker`'s `frontmatter_valid`/doc-coverage condition should see the resolved marker
and not block on this bullet.

## Scope Guards

- Do not modify `check_for_boss_spawn`, `_is_active_living_boss`, `_boss_region_id`, or
  `region_boss_map` in `src/world/boss.py` — the existing region-scoped `world_boss` mechanism and its
  idempotency test (`test_boss_spawn_is_idempotent_even_if_existing_boss_left_region`) must remain
  byte-identical in behavior.
- Do not add a `PlaceUpdate` dataclass, a `StateUpdate.place_updates` collection, or any
  `apply_plan.py` Place-handling code — Option A was chosen; `PlaceState.occupant_entity_id` stays
  write-never in this ticket.
- Do not touch `CampService`, `CampState`, Camp/Nest classification (C1), or `CampState`/`PlaceState`
  bridging (C2) — confirmed unrelated to every file this ticket touches.
- Do not build any dissolution/transformation-on-death logic (`PlaceState.kind`/`prior_kind`/
  `transformed_tick` mutation on entity death) — idea 48, no ticket yet, guarded by Step 7's negative
  test.
- Do not migrate real corpus content (`data/worlds/hero_guild_routing/world.yaml` or its
  `resolved/world.resolved.yaml`) or touch
  `test_hero_guild_routing_real_content_produces_expected_non_uniform_place_kinds`'s assertions —
  synthetic fixture path chosen.
- Do not change the spawn gate values (`state.maturity >= 50.0`, `region.trauma_score >= 20.0`) or
  introduce a new Place-local trigger condition (e.g. `hazard_level`) — reuse the existing gate exactly.
- Do not add a new `SystemCadence` field for Lair spawning — reuse `cadence.boss_spawn`.
- Do not fix the pre-existing `difficulty_tier=5` → tier-1-fallback gap in
  `spawn_config.py`/`generator.py` — reused as-is, not this ticket's job (see Decision #6).
- Do not touch the `_push_shapers_phase2_active`-guarded "live" event-shaping path in
  `event_extractor.py` — only the two named rollback-path exclusion lists are edited.

## Dependency Map

- Step 1 → Step 2 (same function, sequential edits to the same file).
- Step 2 → Step 3 (Step 3's edits are only correct once Step 2 establishes `kind="dragonkin"` as the
  occupant kind).
- Step 2 → Step 4 (Step 4 wires the function Step 2 completes into the engine call site).
- Step 5 and Step 6 are independent of each other and of Steps 1-4's internals, but Step 6's tests
  exercise `BossService.check_for_lair_spawn`, so Step 6 must follow Step 2.
- Step 7 is independent, can be done any time after Step 2 (needs `check_for_lair_spawn` to exist for
  its optional verification call, though the core assertion is on `PlaceState` fields directly and
  could stand alone).
- Step 8 and Step 9 (docs/parity) depend on Steps 1-7 being complete and stable, so the described
  mechanism is accurate.
- Step 10 depends on Step 8/9 confirming Option A was actually the final implemented choice.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| Lair spawn idempotency is keyed per-Place (via `PlaceState.occupant_entity_id` / `place_id`), not per-Region, proven not to double-spawn across multiple LAIR Places in one Region | Step 1, Step 2 (place_id-keyed `identity.properties["lair_place_id"]` lock, per Decision #1's documented AC reinterpretation) | `test_lair_spawn_is_idempotent_per_place_with_multiple_lairs_in_one_region`, `test_lair_spawn_does_not_double_spawn_when_one_of_two_lairs_already_occupied` (Step 6) |
| `test_boss_spawn_is_idempotent_even_if_existing_boss_left_region`-style coverage extended (not replaced) to the Place-scoped case | Step 6 | `test_lair_spawn_fills_empty_lair_place_when_no_occupant_exists`, `test_lair_spawn_is_idempotent_per_place_with_multiple_lairs_in_one_region`, `test_lair_spawn_does_not_double_spawn_when_one_of_two_lairs_already_occupied` (all new, added alongside the unmodified original) |
| At least one real LAIR-kind Place exists in a chosen corpus world OR a clearly-labeled synthetic fixture is added, sufficient to exercise the new logic | Step 5 (synthetic fixture, explicitly labeled in its docstring/comment) | `test_lair_kind_place_compiles_via_worldcompiler` (Step 5) |
| Dissolution/transformation on occupant death explicitly listed in Out of Scope, idea 48 named as deferred owner, not silently omitted | Already present in the ticket's own Out of Scope section (no plan action needed); Step 7 adds the enforcing test | `test_lair_occupant_death_does_not_dissolve_or_transform_the_lair_place` (Step 7) |

## Anti-Drift Notes

- **`kind` string discipline**: `_is_active_living_lair_occupant` checks `entity.kind == "dragonkin"`
  exactly — do not accidentally spawn Lair occupants with `kind="world_boss"` or a typo'd string, which
  would silently merge Lair occupancy tracking into the unrelated Boss `region_boss_map` idempotency
  path (they are separate maps/functions by design, but a wrong `kind` string would cause the
  *observability* lists from Step 3 to misclassify the entity even if the spawn logic itself still
  worked).
- **`entities_add` fold-in is a plain list concatenation** (`world_dynamics.py:177`), not a dict merge
  — Step 4 must append `lair_spawn_update.entities_add`, not replace or reorder the existing five
  sources. Losing this line silently drops Lair spawns from the final `StateUpdate` with no error.
- **`difficulty_tier=5` tier-1 fallback is pre-existing and out of scope** (Decision #6) — if Verify
  notices a newly-spawned `dragonkin` entity has suspiciously low (tier-1) stats despite
  `difficulty_tier=5`, this is the same known gap `check_for_boss_spawn`'s own `world_boss` spawns
  already have today, not a regression introduced by this ticket.
- **`PlaceState.occupant_entity_id` stays `None` after this ticket** — this is intentional (Option A,
  Decision #1), not a bug. Do not "helpfully" add a write to it without also building the full
  `PlaceUpdate`/apply-path plumbing Option B would require; a partial write (e.g. directly mutating a
  local `PlaceState` object outside the authoritative apply pipeline) would violate CLAUDE.md's
  Architecture Rule ("Authoritative application is the only place durable state should be committed").
- **C1/C2 boundary**: `test_non_camp_nest_place_kinds_do_not_construct_campstate`
  (`tests/unit/worldbuilding/test_place_wiring.py`, existing) already asserts LAIR-kind Places never
  produce a `CampState` — this must keep passing unmodified; nothing in Steps 1-7 touches
  `CampService`/`CampState` construction, so this should hold automatically, but is worth a final
  spot-check during Verify.
- **`region.trauma_score`/`state.maturity` gate must stay exactly as-is** for both Boss and Lair — do
  not let a "seems more correct" Place-local hazard gate creep in; that is a trigger-condition change
  explicitly out of this ticket's stated scope (keying granularity only).
