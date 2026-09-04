---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260904-LAIR-ENTITY-ANCHOR
artifact_type: test_plan
tags: [content, world, determinism]
---

# Test Plan — TCK-20260904-LAIR-ENTITY-ANCHOR

## Regression Surface

**Unit — world dynamics / boss:**
- `tests/unit/world/test_world_dynamics.py` (all tests, especially
  `test_boss_spawn_is_idempotent_even_if_existing_boss_left_region`,
  `test_calamity_boss_spawn`, `test_world_dynamics_maturity_advancement`,
  `test_world_dynamics_folds_camp_and_calamity_world_updates_into_final_update`) — the region-scoped
  idempotency test must keep passing unmodified in behavior (single-boss-per-region case), even as
  Place-scoped coverage is added alongside it.

**Unit — Place/state schema:**
- `tests/unit/core/test_place_state.py` (all tests, especially
  `test_place_state_construction_minimal`, `test_place_state_all_kinds_constructible`,
  `test_place_state_participates_in_canonical_hash`,
  `test_place_state_field_divergence_participates_in_canonical_hash`) — confirms
  `occupant_entity_id`'s default-`None` behavior and canonical-hash participation are unaffected by
  whichever option (A or B) is chosen, unless Option B is chosen, in which case these tests define the
  serialization contract any new write path must not silently violate.
- `tests/unit/worldbuilding/test_place_wiring.py` (all tests) — especially
  `test_hero_guild_routing_real_content_produces_expected_non_uniform_place_kinds` (locks
  `mountain_pass_zone` to zero Places today — must be deliberately updated, not silently broken, if
  the real-content-migration path is chosen for LAIR fixture content; must pass unmodified if the
  synthetic-fixture path is chosen instead) and the CAMPSTATE-PLACE-BRIDGE tests
  (`test_camp_kind_place_compiles_to_companion_campstate`,
  `test_non_camp_nest_place_kinds_do_not_construct_campstate` — the latter explicitly asserts LAIR-kind
  Places never produce a `CampState`, a direct C2-scope-boundary regression guard this ticket must not
  break).

**Integration/observability (only if a new entity `kind` string is introduced for Lair occupants):**
- `tests/unit/observability/` — any test covering `event_extractor.py`'s `spawn_cadence_fired`
  exclusion list (line 1357) or `_BOSS_KINDS` (line 1461); locate via `grep -rl "_BOSS_KINDS\|spawn_cadence_fired"
  tests/` at implementation time and scope precisely, since a new unrecognized `kind` string would
  silently mis-classify Lair spawns as cadence spawns.

**If real-content migration is chosen (mountain_pass_zone / hero_guild_routing path):**
- `tests/unit/worldbuilding/` (broader) and any world-compile smoke test that asserts fixed
  `place_count`/entity counts for `hero_guild_routing` specifically — locate via
  `grep -rl "hero_guild_routing" tests/` before touching the content, to catch every locked assertion,
  not just the one already found in `test_place_wiring.py`.

## New Tests Required

1. **`test_lair_spawn_is_idempotent_per_place_with_multiple_lairs_in_one_region`**
   - Category: unit
   - Verifies: two LAIR-kind `PlaceState`s in the *same* `RegionState`, each with its own existing
     active/living occupant entity (keyed via whichever mechanism Option A/B lands on — e.g.
     `identity.properties["lair_place_id"]` set to each Place's own `place_id`), produce **no**
     `entities_add` on the next spawn check — proving neither Place's occupant is treated as
     satisfying the other Place's slot. This is the direct AC-mandated proof that per-Place keying
     doesn't collide within one Region, extending (not replacing)
     `test_boss_spawn_is_idempotent_even_if_existing_boss_left_region`'s structure/style.
   - Location: `tests/unit/world/test_world_dynamics.py` (same file as the test it extends, per the
     ticket's own AC wording "extended (not replaced)").

2. **`test_lair_spawn_fills_empty_lair_place_when_no_occupant_exists`**
   - Category: unit
   - Verifies: a LAIR-kind `PlaceState` with no existing occupant (mechanism-appropriate: no entity
     carries a matching `lair_place_id`/`occupant_entity_id` reference) produces a new occupant entity
     in `entities_add` when the spawn gate conditions are met, and that entity carries whatever
     Place-linking metadata Option A/B establishes.
   - Location: `tests/unit/world/test_world_dynamics.py`.

3. **`test_lair_spawn_does_not_double_spawn_when_one_of_two_lairs_already_occupied`**
   - Category: unit
   - Verifies: with two LAIR-kind Places in one Region, one occupied and one empty, exactly one new
     entity is spawned (for the empty Place only) — a stronger mixed-state variant of test #1/#2
     combined, closing the specific "existing per-region map silently treats any occupant as filling
     every LAIR Place in the region" failure mode a naive generalization could introduce.
   - Location: `tests/unit/world/test_world_dynamics.py`.

4. **`test_lair_kind_place_is_schema_constructible_and_participates_in_canonical_hash`** (only if not
   already fully covered by existing `test_place_state_all_kinds_constructible`/
   `test_place_state_field_divergence_participates_in_canonical_hash` — check first, extend only if a
   real gap remains for the LAIR+occupant_entity_id combination specifically)
   - Category: unit
   - Verifies: a `PlaceState(kind=LAIR, occupant_entity_id=<int>)` round-trips and its
     `occupant_entity_id` value participates in `to_canonical_dict()`'s hash — only needed if Option B
     (new write path) is chosen and no existing test already covers a non-`None`
     `occupant_entity_id`.
   - Location: `tests/unit/core/test_place_state.py`.

5. **Architecture guard: `test_lair_dissolution_on_death_is_not_implemented`** (or equivalent negative
   assertion, named to describe intent not process)
   - Category: architecture guard
   - Verifies: killing/removing a Lair occupant entity does not itself mutate `PlaceState.kind`,
     `prior_kind`, or `transformed_tick` — i.e., confirms the Out-of-Scope boundary (idea 48
     dissolution/transformation deferred) is not silently implemented as a side effect of whatever
     spawn-tracking mechanism this ticket builds. Direct anti-scope-creep guard.
   - Location: `tests/unit/world/test_world_dynamics.py` or `tests/unit/core/test_place_state.py`
     (co-locate with whichever file ends up owning the Lair spawn/occupancy logic).

6. **Content/fixture test — shape depends on the real-content-vs-synthetic-fixture decision:**
   - If synthetic fixture: a test constructing a minimal `WorldSpec` with a `PlaceSpec(kind="LAIR",
     ...)` via `WorldCompiler.compile()` (mirroring `test_place_wiring.py`'s `_minimal_spec()`
     pattern), clearly commented as a synthetic fixture, not real corpus content.
   - If real content: `test_hero_guild_routing_real_content_produces_expected_non_uniform_place_kinds`
     must be **updated** (not left broken) to include the new LAIR Place in `mountain_pass_zone`, with
     the `place_count`/`state.places.keys()` assertions adjusted accordingly, plus a new assertion
     specifically confirming the LAIR Place's `kind == "LAIR"`.
   - Location: `tests/unit/worldbuilding/test_place_wiring.py`.

## Scoped Pytest Commands

```
pytest tests/unit/world/test_world_dynamics.py -q
pytest tests/unit/core/test_place_state.py -q
pytest tests/unit/worldbuilding/test_place_wiring.py -q
```

If a new entity `kind` string is introduced for Lair occupants (Option affecting observability
lists), add:
```
pytest tests/unit/observability/ -k "cadence or boss_kind or spawn" -q
```
(narrow the `-k` expression once the actual test file/names are located via
`grep -rl "_BOSS_KINDS\|spawn_cadence_fired" tests/` at implementation time).

If real-content migration is chosen (`hero_guild_routing`), add:
```
pytest tests/unit/worldbuilding/ -q
```

Never run `pytest tests/` unscoped.

## Anti-Drift Test Guards

- **Region-vs-Place keying regression**: any implementation that reintroduces a single
  `region_boss_map`-style dict keyed by `region_id` alone (rather than per-Place) for LAIR occupancy
  would pass the existing single-boss test but fail test #1/#3 above — this is the direct regression
  the new tests are designed to catch.
- **C1/C2 boundary guard**: `test_non_camp_nest_place_kinds_do_not_construct_campstate` (existing,
  `test_place_wiring.py`) already asserts LAIR-kind Places never produce a `CampState` — this must
  keep passing unmodified; any Lair implementation that accidentally touches `CampService`/`CampState`
  construction would violate both this ticket's own Out of Scope and this existing guard test.
- **Idea-48 boundary guard**: test #5 above exists specifically so that a future accidental
  "convenience" implementation of dissolve-on-death doesn't slip in silently while implementing the
  spawn/occupancy mechanism — it should fail loudly if `PlaceState.kind`/`prior_kind`/`transformed_tick`
  ever gets mutated as a side effect of occupant death in this ticket's code.
- **Locked corpus-content assertion guard**: if the real-content path is chosen,
  `test_hero_guild_routing_real_content_produces_expected_non_uniform_place_kinds`'s pre-ticket
  assertions (`mountain_places == []`, `place_count == 3`) must be found and deliberately updated as
  part of the same change — a CI run showing this test failing unmodified after real content was added
  is the direct signal that this guard was missed, not a flaky/unrelated failure.
- **Canonical-hash guard** (only relevant if Option B is chosen): a new `PlaceUpdate.merge()` or
  `apply_plan.py` block that omits handling `occupant_entity_id` would silently accept the update but
  never commit it — mirroring the exact silent-gap failure mode already named in
  `TCK-20260904-CAMP-NEST-CLASSIFICATION`'s investigation for `CampState`'s totem/stockpile/palisade
  fields. Test #4 (or an equivalent apply-plan round-trip test) exists to catch this specifically if
  Option B is the chosen path.
- **`state.maturity`/`region.trauma_score` gate guard**: no new test should assert on a *changed*
  spawn-trigger condition — the existing `test_calamity_boss_spawn`-style assertions on the gate values
  (`state.maturity >= 50`, `region.trauma_score >= 20`) must remain the authoritative trigger condition
  for Lair spawns too, unless Plan explicitly and separately decides to diverge (out of this ticket's
  stated scope, which is about keying granularity, not trigger conditions).
