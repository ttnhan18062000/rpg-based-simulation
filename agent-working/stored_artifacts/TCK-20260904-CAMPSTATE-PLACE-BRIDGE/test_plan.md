---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260904-CAMPSTATE-PLACE-BRIDGE
artifact_type: test_plan
tags: [content, architecture]
---

# Test Plan — TCK-20260904-CAMPSTATE-PLACE-BRIDGE

## Regression Surface

Existing tests that must keep passing, unmodified in their assertions (per this ticket's own
Acceptance Criteria for option (a)):

**Unit — worldbuilding / Place wiring (Direct path):**
- `tests/unit/worldbuilding/test_place_wiring.py` — all 7 existing tests, especially
  `test_non_place_shaped_content_compiles_unchanged`,
  `test_hero_guild_routing_real_content_produces_expected_non_uniform_place_kinds` (the real
  `goblin_camp_place` CAMP-kind content), and `test_place_participates_in_canonical_hash`.

**Unit — worldassembly (Composition path):**
- `tests/unit/worldassembly/test_resolver.py` — especially
  `test_resolve_module_contribution_wires_place_shaped_region` and
  `test_resolve_module_contribution_region_without_places_yields_empty_list`.

**Unit — world / CampService, CreatureTerritoryService:**
- `tests/unit/world/test_camp_lifecycle.py` — all existing tests (maturity evolution, spawn cap, raid
  trigger, Nest-spread fork, typed-field round-trip/merge/apply-plan) must pass with their existing
  assertions unmodified, per this ticket's own AC for option (a).
- `tests/unit/world/test_creature_territory_lifecycle.py` — must keep passing; this service starts
  receiving real (non-empty) `state.camps` data for the first time as a side effect of this ticket
  (see investigation.md Risks #4), so this file's existing assertions are the load-bearing regression
  guard that its behavior doesn't break once fed real camps.
- `tests/unit/world/test_world_dynamics.py` — camp-adjacent assertions (`camp = CampState(...)`
  fixtures at line 156).
- `tests/unit/world/test_natural_creature_reproduction.py` — camp-fixture-adjacent (`_make_camp`
  helper).
- `tests/unit/domains/optimization/test_apply_plan_builder.py` — `CampState`/`CampUpdate` apply-path
  tests, including the sibling ticket's new
  `test_apply_plan_builder_camp_totem_stockpile_palisade`.

**Unit — content (schema-adjacent, only if `PlaceRecipeSpec`/`PlaceSpec` gain a new field):**
- `tests/unit/content/test_catalog.py`, `tests/unit/content/test_layered_catalog.py`,
  `tests/unit/content/test_resolvers.py` — confirm no `races.yaml`/resolver schema drift from any new
  field addition.

**Determinism / canonical hash:**
- Any test exercising `CanonicalStateHasher.get_hash()` against a compiled world with Place/Camp
  content (`test_place_participates_in_canonical_hash` above is the direct one) — a newly-constructed
  companion `CampState` must not silently change the hash of worlds that don't declare Camp/Nest
  content, and must deterministically change it for worlds that do.

## New Tests Required

Per acceptance criteria and the architecture decision Plan will record:

1. **`test_camp_kind_place_compiles_to_companion_campstate`** (assuming option (a) is chosen)
   - Category: unit
   - Verifies: a `RegionSpec` declaring a `PlaceSpec(kind="CAMP", ...)` with the new creature-race
     field set (e.g. `"goblin"`) produces both a `PlaceState` in `state.places` **and** a linked
     `CampState` in `state.camps`, correctly populated (`kind` matches the race field,
     `position` matches, `id`/`place_id` linkage as decided by plan.md).
   - Location: `tests/unit/worldbuilding/test_place_wiring.py` (mirrors existing structure/imports).

2. **`test_nest_kind_place_compiles_to_companion_campstate`**
   - Category: unit
   - Verifies: same as above for `kind="NEST"` with a Nest-classified race (e.g. `"wolf"`), confirming
     `CampService.NEST_RACE_KINDS` membership is preserved end-to-end from content through to the
     constructed `CampState.kind`.
   - Location: `tests/unit/worldbuilding/test_place_wiring.py`.

3. **`test_non_camp_nest_place_kinds_do_not_construct_campstate`** (regression/negative case)
   - Category: unit
   - Verifies: `PlaceSpec(kind="CITY"/"RUIN"/"DUNGEON"/"LANDMARK"/"LAIR", ...)` never produces an
     entry in `state.camps` — the bridge is strictly scoped to CAMP/NEST kinds.
   - Location: `tests/unit/worldbuilding/test_place_wiring.py`.

4. **`test_non_place_shaped_content_compiles_unchanged_with_camp_bridge`** (ticket's own explicit AC)
   - Category: unit / regression
   - Verifies: a world module with only City/Ruin/Dungeon content (no Camp/Nest Places at all)
     compiles with `state.camps == {}` exactly as before this ticket — proves the bridge is additive,
     not a behavior change for existing non-Camp worlds.
   - Location: `tests/unit/worldbuilding/test_place_wiring.py` (extends/parallels the existing
     `test_non_place_shaped_content_compiles_unchanged`).

5. **`test_resolve_module_contribution_wires_camp_kind_place_with_race_field`**
   - Category: unit / integration (Composition path)
   - Verifies: the Composition path (`WorldModuleSpec` → `WorldAssemblyResolver` → `WorldSpec`) carries
     the new creature-race field through `resolve_module_contribution()` unchanged, namespaced
     correctly alongside `place_id`, matching the existing
     `test_resolve_module_contribution_wires_place_shaped_region` pattern.
   - Location: `tests/unit/worldassembly/test_resolver.py`.

6. **`test_campstate_place_linkage_round_trips_via_place_id`** (or whatever id-linkage scheme plan.md
   picks)
   - Category: unit
   - Verifies: the `CampState`↔`PlaceState` linkage decided in plan.md (e.g. shared id / `place_id`
     match) actually resolves both directions — given a `place_id`, both `state.places[place_id]` and
     `state.camps[<linked_id>]` refer to the same conceptual Camp/Nest.
   - Location: `tests/unit/worldbuilding/test_place_wiring.py`.

7. **`test_campstate_place_bridge_participates_in_canonical_hash`**
   - Category: unit / determinism
   - Verifies: two otherwise-identical worlds, one with a Camp-kind Place and one without, produce
     different `CanonicalStateHasher.get_hash()` values — mirrors
     `test_place_participates_in_canonical_hash`'s pattern, extended to cover the new `CampState` side.
   - Location: `tests/unit/worldbuilding/test_place_wiring.py`.

8. **`test_campservice_process_camps_operates_on_world_gen_seeded_camp`** (architecture guard /
   integration)
   - Category: integration
   - Verifies: a `CampState` constructed via the new bridge is a fully valid input to
     `CampService.process_camps()` (maturity accrual, spawn-cap, raid-trigger logic) — i.e., the
     companion `CampState` isn't just structurally present but functionally usable by the existing,
     unmodified `CampService` code path. This is the direct evidence for option (a)'s AC ("existing
     CampService tests continue to pass unmodified in their assertions about CampService behavior")
     extended to real world-gen-seeded data, not just hand-built test fixtures.
   - Location: `tests/unit/world/test_camp_lifecycle.py` or a new
     `tests/integration/worldbuilding/test_camp_place_bridge_integration.py` if plan.md judges the
     cross-module (compiler → camp service) scope warrants integration-tier placement.

9. **`test_invalid_creature_race_rejected_at_schema_level`** (if a new typed field is added)
   - Category: unit
   - Verifies: the new `PlaceRecipeSpec`/`PlaceSpec` creature-race field rejects a race string outside
     the documented Camp+Nest set (`{goblin, orc, wolf, spider, troll, slime}`) at schema-validation
     time — mirrors the existing `test_invalid_place_kind_rejected_at_schema_level` pattern.
   - Location: `tests/unit/worldbuilding/test_place_wiring.py`.

10. **`test_creature_kind_field_is_none_for_non_camp_nest_place_kinds`** (if a new typed field is
    added)
    - Category: unit
    - Verifies: the new field stays `Optional`/unset for City/Ruin/Dungeon/Landmark/Lair `PlaceSpec`s,
      confirming it doesn't become an accidental required field breaking existing non-Camp/Nest content
      (direct guard against the Anti-Drift Hazard in investigation.md).
    - Location: `tests/unit/worldbuilding/test_place_wiring.py`.

If option (b) is chosen instead, replace tests 1-2/6/8 above with the option-(b)-specific tests named
in this ticket's own AC: all existing `CampService`/`CampState` call sites
(`src/world/camp.py`, `src/world/creature_territory.py`, `src/engine/apply.py`,
`src/engine/apply_plan.py`) updated consistently, with their existing test suites passing — this would
require substantially rewriting `test_camp_lifecycle.py`,
`test_creature_territory_lifecycle.py`, `test_world_dynamics.py`, and
`test_apply_plan_builder.py`'s camp-related tests to construct/assert against `PlaceState` fields
instead of `CampState` fields, which is exactly the larger blast radius flagged in investigation.md
Risk #1.

## Scoped Pytest Commands

```
pytest tests/unit/worldbuilding/ -q
pytest tests/unit/worldassembly/ -q
pytest tests/unit/world/ -q
pytest tests/unit/domains/optimization/test_apply_plan_builder.py -q
```

If a new content-schema field is added to `PlaceRecipeSpec`/`PlaceSpec`:

```
pytest tests/unit/content/test_catalog.py tests/unit/content/test_layered_catalog.py tests/unit/content/test_resolvers.py -q
```

If an integration-tier test is added (item 8 above, if placed at integration tier):

```
pytest tests/integration/worldbuilding/ -q
```

Never `pytest tests/` — always scoped to the domains above.

## Anti-Drift Test Guards

- A test asserting `state.camps == {}` for every existing (pre-this-ticket) real compiled world's
  `WorldSpec` **except** any that already declare Camp/Nest content (currently only
  `hero_guild_routing`'s `goblin_camp_place`, and even that produces no `CampState` until this ticket's
  new field is populated) — guards against the bridge accidentally firing for content it shouldn't.
- A test confirming `CreatureTerritoryService`'s existing test suite
  (`test_creature_territory_lifecycle.py`) still passes byte-for-byte once fed a real, non-empty
  `state.camps` from a compiled test world — this is the concrete regression guard for the "silent
  activation" risk flagged in investigation.md (the code isn't touched, but its formerly-dead input is
  no longer dead).
- A test confirming `CampService.process_camps()`'s raid-trigger and monster-spawn branches are **not**
  newly flag-gated by this ticket (i.e., no accidental new `if flags.get(...)` wrapper was added around
  the whole function) — this ticket's job is to seed real data into an already-unconditional service,
  not to change its gating.
- A test confirming the `totem_tier`/`stockpile`/`palisade_integrity` fields on any newly-constructed
  companion `CampState` remain at their dataclass defaults (`0`/`0.0`/`0.0`) unless a real value is
  explicitly available from content — guards against silently inventing accrual/effect logic that the
  sibling ticket explicitly scoped out.
- A test confirming `AuthoritativeState.to_readonly()`'s `camps=ReadOnlyDict(self.camps)` wrapping still
  applies to camps constructed via this new bridge (not just hand-built test fixtures) — guards against
  copy-pasting the new construction logic in a way that bypasses the existing immutability wrapping (see
  investigation.md's `places`-is-unwrapped finding — the bridge must not replicate that gap onto
  `camps`, which is currently correctly wrapped).
- A test confirming `docs/parity_ledger/world_dynamics.yaml`'s schema still validates after `WORLD-109`
  is edited (run via `tools/parity_ledger_writer.py`'s validating write path, not a raw YAML edit, per
  the sibling ticket's own precedent and CLAUDE.md's Parity Ledger rule).
