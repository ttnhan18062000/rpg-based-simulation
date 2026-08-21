---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260821-COMPILER-NOISE-FILL
artifact_type: test_plan
tags: [world, determinism]
---

# Test Plan — TCK-20260821-COMPILER-NOISE-FILL

## Regression Surface

**Unit — `tests/unit/worldbuilding/test_world_compiler.py`** (must all keep passing unmodified):
- `test_compiler_minimal_world`, `test_compiler_entity_mappings`, `test_compiler_placement_bounds`, `test_compiler_report_write`, `test_compiler_quest_referential_warnings` — none of the fixture regions declare `terrain_variants`; entity/resource/building counts, positions-in-bounds, and report shape must be byte-identical.
- `test_compiler_seeds_faction_tension_from_spec`, `test_compiler_seeds_full_faction_roster_at_zero_tension_by_default`, `test_compiler_no_factions_declared_yields_empty_factions_dict` — faction seeding untouched.
- `test_compiler_seeds_information_source_profiles_from_spec`, `test_compiler_no_information_sources_declared_yields_empty_list`, `test_compiler_seeds_pending_information_responses_from_spec`, `test_compiler_pending_information_response_unmatched_population_is_skipped_with_warning`, `test_compiler_no_pending_information_responses_declared_yields_empty_list`, `test_compiler_seeds_pending_self_model_information_events_from_spec`, `test_compiler_pending_self_model_information_event_unmatched_population_is_skipped_with_warning`, `test_compiler_no_pending_self_model_information_events_declared_yields_empty_list` — unrelated compile steps, must be untouched.
- `test_urban_political_resolved_world_seeds_one_pending_self_model_information_event`, `test_urban_political_resolved_world_seeds_one_pending_information_response`, `test_urban_political_resolved_world_seeds_two_information_sources`, `test_urban_political_resolved_world_seeds_bandit_town_council_tension`, `test_urban_political_resolved_bandit_road_hazard_kind_matches_source` — real resolved-world regression; `urban_political`'s regions do not declare `terrain_variants` today, so these are a real-content non-declaring-region regression guard.
- `test_helper_enum_mappers`, `test_compiler_resource_node_regen_rate`, `test_compiler_resource_node_explicit_zero_regen`, `test_quest_location_tag_matches_region_type`, `test_quest_location_tag_matches_region_explicit_tag`, `test_quest_location_tag_warns_on_genuine_mismatch` — unrelated to terrain, must be untouched.
- `test_get_bravery_bias_by_real_alignment_bucket`, `test_compiler_faction_bravery_bias_produces_real_population_skew`, `test_get_action_style_for_bravery_thresholds`, `test_compiler_faction_bravery_bias_produces_real_action_style_skew` — personality/RNG draws under `Domain.WORLD`; these are the most sensitive existing tests to a botched Domain choice (they'd silently start failing if a new draw altered `Domain.WORLD`'s entity_id/sub_id sequence for personality/class draws — they must keep passing exactly, proving `Domain.WORLD`'s own draws are untouched).

**Unit — `tests/unit/worldbuilding/test_compiler_context.py`, `tests/unit/worldbuilding/test_worldbuilding_strategy.py`** — grep-confirmed to assert `state_hash`; scoped run required to confirm no incidental coupling to region-painting internals.

**Certification — `tests/certification/test_world_compile_determinism.py`** (must all keep passing unmodified): `test_compiler_seeding_determinism` (same seed twice ⇒ same `state_hash` + entity/resource coordinates), `test_compiler_layout_variation_under_different_seeds` (different seeds ⇒ different `state_hash`/coordinates), `test_compile_report_contents` (report shape). None of `create_certification_base_spec()`'s two regions declare `terrain_variants`.

**Integration — DeterministicRNG's own domain-enum guard:** `tests/integration/kernel/test_phase2_determinism.py::TestDomainEnum::test_init_domain_exists` (`assert Domain.INIT == 11`) and `::test_all_domains_unique` must keep passing — this ticket does not add a new `Domain` value, it reuses `Domain.INIT`, so no enum-value change is expected; if the implementation adds a new `Domain` member instead of reusing `INIT`, these tests are the tripwire that would (correctly) need updating, which should be treated as a scope flag, not a routine edit.

## New Tests Required

1. **`test_compiler_terrain_variants_declared_produces_per_tile_variation`**
   - Category: unit
   - Verifies: a region with `terrain_variants` containing ≥2 distinct terrain strings, compiled at a fixed seed, produces `state.terrain[(x,y)]` values within that region's bounds that are **not all identical** to a single flat string (i.e. real per-tile variation exists, not degenerate single-value output).
   - Location: `tests/unit/worldbuilding/test_world_compiler.py`

2. **`test_compiler_terrain_variants_deterministic_same_seed`**
   - Category: unit
   - Verifies: compiling the *same* spec (a region with `terrain_variants`) twice with the *same* seed produces an **identical** `state.terrain` dict restricted to that region's tile set (assert full per-tile equality, not just hash equality — see investigation's `state_hash`-blindness finding).
   - Location: `tests/unit/worldbuilding/test_world_compiler.py`

3. **`test_compiler_terrain_variants_different_seed_differs`**
   - Category: unit
   - Verifies: compiling the same `terrain_variants`-declaring spec with two different seeds produces a **measurably different** per-tile terrain distribution within the same bounds (e.g. assert the two tile→terrain dicts, restricted to the region, are not equal — non-degenerate seed sensitivity, not just "at least one tile differs" if that's too weak; assert a meaningful fraction, e.g. >10%, of tiles differ to rule out a near-degenerate implementation).
   - Location: `tests/unit/worldbuilding/test_world_compiler.py`

4. **`test_compiler_terrain_variants_never_writes_outside_bounds`**
   - Category: unit
   - Verifies: for a region near the topology edge (bounds partially or fully clipped by `spec.topology.width/height`), every noise-filled tile key present in `state.terrain` restricted to that region's nominal bounds is also within `[0, width) x [0, height)` — i.e. the existing `0 <= x < width and 0 <= y < height` clamp still gates the new write path exactly as it does the flat-fill path. Construct a region whose declared `bounds`/`grid_bounds` slightly exceed the topology dimensions to exercise the clamp directly.
   - Location: `tests/unit/worldbuilding/test_world_compiler.py`

5. **`test_compiler_terrain_variants_town_tiles_membership_unaffected_by_terrain_choice`**
   - Category: unit
   - Verifies: a `type: "town"` region declaring `terrain_variants` still produces `town_tiles` (and `town_entity_ids` for any spawned entities) covering exactly the same tile set as an equivalent non-declaring town region — regardless of which terrain string each tile ends up painted with. Assert `state.town_tiles == {(x,y) for x in range(...) for y in range(...)}` (the full bounds set) independent of `state.terrain` values.
   - Location: `tests/unit/worldbuilding/test_world_compiler.py`

6. **`test_compiler_no_terrain_variants_declared_produces_byte_identical_terrain_dict`** (the core anti-regression guard, given the `state_hash`-blindness finding)
   - Category: unit / regression guard
   - Verifies: for a spec whose regions do **not** declare `terrain_variants` (e.g. `create_base_valid_spec()` unmodified), `state.terrain` restricted to each region's bounds equals the flat `r_spec.terrain` string for every in-bounds tile — i.e. directly assert per-tile content, not `state_hash` equality, since `state_hash` (`StateFingerprinter`) does not include terrain at all and cannot detect a terrain regression on its own. This is the single most important new test in this plan.
   - Location: `tests/unit/worldbuilding/test_world_compiler.py`

7. **`test_compiler_terrain_variants_reuses_weighted_choice_respects_weight`**
   - Category: unit
   - Verifies: a region declaring two variants with a heavily skewed `weight` (e.g. 99.0 vs 1.0) produces a per-tile terrain distribution where the heavily-weighted terrain appears in a clear majority of tiles (statistical sanity check on a reasonably large bounds box, not an exact-count assertion, to avoid brittleness) — proves `weight` is actually consumed, not ignored/uniform.
   - Location: `tests/unit/worldbuilding/test_world_compiler.py`

8. **`test_domain_world_entity_resource_building_draws_unaffected_by_terrain_variants_declaration`** (architecture/anti-drift guard)
   - Category: architecture guard
   - Verifies: compile the *same* spec twice — once with a region's `terrain_variants` populated, once with it set to `None` (all other fields, including entity/resource/building populations in that region, identical) — and assert every entity's `navigation.position`, every resource node's `position`, and every building's `position` are **identical** across both compiles at the same seed. This directly proves the new noise-fill draw (regardless of which `Domain` it uses) cannot perturb `Domain.WORLD`'s existing entity/resource/building draw sequence — the exact risk class the ticket exists to eliminate "by construction rather than by draw-order sequencing."
   - Location: `tests/unit/worldbuilding/test_world_compiler.py` (or a new `tests/architecture/test_worldcompiler_noise_fill_domain_isolation.py` if the project convention prefers architecture guards in their own directory — check sibling files in `tests/architecture/` for the prevailing pattern before choosing).

9. **`test_compiler_terrain_variants_empty_list_behaves_as_not_declared`**
   - Category: unit / edge case
   - Verifies: `terrain_variants=[]` (empty list, as opposed to `None`) does not crash and falls back to flat-fill behavior (or is explicitly rejected by schema/compiler with a clear warning) — an edge case the schema's `Optional[List[...]]` type permits but which ticket #1's own investigation may not have exercised. Confirm expected behavior during implementation planning if not already decided; do not assume without checking the plan.md this investigation feeds.
   - Location: `tests/unit/worldbuilding/test_world_compiler.py`

## Scoped Pytest Commands

```
pytest tests/unit/worldbuilding/ tests/certification/test_world_compile_determinism.py -v
```

Additionally, since this ticket touches `DeterministicRNG`/`Domain` usage patterns shared with the `LAW-SPAWN-OCCUPANCY` collision-resolution logic in the same file:

```
pytest tests/unit/worldbuilding/ tests/certification/test_world_compile_determinism.py tests/integration/kernel/test_phase2_determinism.py -v -m "not slow"
```

Never run the bare `pytest tests/` per project convention — the above two commands scope to the worldbuilding/compiler domain plus the RNG determinism guards this change most directly risks.

## Anti-Drift Test Guards

- **Test #6 (`test_compiler_no_terrain_variants_declared_produces_byte_identical_terrain_dict`) is the load-bearing anti-drift guard for this entire ticket.** Because `state_hash` structurally excludes terrain (independently verified in `investigation.md` by reading `StateFingerprinter.get_fingerprint()` in full), no existing test — including the certification determinism tests — would catch a terrain-painting regression for non-declaring regions. This new test closes that gap directly.
- **Test #8 is the anti-drift guard for the Domain-choice decision itself** — it proves empirically (not just by code-reading argument) that adding the new draw path does not perturb `Domain.WORLD`'s existing entity/resource/building coordinate sequence, regardless of which `Domain` value the implementation ultimately picks for the noise-fill draw. If a future change accidentally moves the noise-fill draw to share `Domain.WORLD`'s namespace with a colliding `entity_id`/`sub_id`, this test is the one likely to catch a resulting spurious position shift.
- **Existing personality/action-style tests** (`test_compiler_faction_bravery_bias_produces_real_population_skew`, `test_compiler_faction_bravery_bias_produces_real_action_style_skew`) already assert statistical properties of `Domain.WORLD` sub_id 10-14 draws — keep these in the regression-surface run for every implementation iteration; a regression here would indicate the new draw path leaked into `Domain.WORLD`'s existing sub_id space.
- **Do not accept a green run of `tests/certification/test_world_compile_determinism.py` alone as proof of "no regression."** Per the investigation's `state_hash`-blindness finding, this file's tests are necessary but not sufficient; the scoped command above always pairs it with `tests/unit/worldbuilding/` (which will include the new terrain-content tests) for exactly this reason.
