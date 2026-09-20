---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20260919-COMBAT-ENGAGED-HOSTILES-UNIFY-CATALOG-SEMANTICS
artifact_type: test_plan
tags: [combat, faction, root-cause]
---

# Test Plan — TCK-20260919-COMBAT-ENGAGED-HOSTILES-UNIFY-CATALOG-SEMANTICS

## New tests
`tests/unit/engine/test_legality_engaged_hostiles_catalog_semantics.py` — 6 tests, one positive
(catches a real, same-legacy-bucket catalog rivalry) and one negative (clears a real,
different-legacy-bucket non-hostile pair) case per internal implementation path:
- `test_occupancy_snapshot_path_catches_same_bucket_catalog_rivalry` /
  `test_occupancy_snapshot_path_clears_different_bucket_non_hostile_pair`
- `test_spatial_query_fallback_path_catches_same_bucket_catalog_rivalry` /
  `test_spatial_query_fallback_path_clears_different_bucket_non_hostile_pair`
- `test_dict_iteration_fallback_path_catches_same_bucket_catalog_rivalry` /
  `test_dict_iteration_fallback_path_clears_different_bucket_non_hostile_pair`

Test pairs use real, previously-measured catalog data (`bandit_company`/`goblin_warband`:
same legacy bucket, real catalog rivalry via `data/content/social/faction_relationships.yaml`'s
own `bandits_to_goblins` entry; `hero_guild`/`merchant_league`: different legacy buckets, no real
catalog hostility), not synthetic ids — the same pairs the original investigation measured.

**Both cases per path are load-bearing, not redundant**: a fix that only checked the negative
case (does the old false-positive-triggering pair still get cleared) would have passed even
without ever fixing anything, since the fallback logic degrades safely in that direction. Only
the positive case (does a real, same-bucket rivalry now get caught) actually proves the fix
works — and it's exactly the positive case that caught the `_has_hostiles_or_dead_cache` bug
during this ticket's own implementation (see Implementation Notes).

## Regression scope run
- `tests/unit/movement/` — 57/57 passed
- `tests/unit/combat/` — 127/127 passed (combined with `tests/integration/pipeline/test_combat_legality_matrix.py`)
- `tests/unit/tactical/` — 13/13 passed (combined with `tests/unit/engine/test_legality_faction_mutation.py`)
- `tests/unit/core/` — 253/253 passed (covers `src/core/state.py`'s own change)
- `tests/unit/strategic/test_intelligence_routine_blockers.py`,
  `tests/unit/resource/test_resource_intelligence_contract.py` — 5/5 passed (covers
  `src/systems/strategic_systems/intelligence.py`'s own change)

## Real-world verification (not unit-test-only)
- **Zero remaining divergence, measured**: re-ran the original investigation's own instrumented
  divergence probe against the fixed code — `legacy_only`/`catalog_only` counts both `0` across
  `crowded_frontier`, `hero_guild_routing`, `quest_dense_frontier` (previously 34%-97% of
  legacy-triggered pairs disagreed with the catalog; now zero).
- **Real before/after combat volume per world**, via a script that authentically reconstructs the
  pre-fix runtime condition (both the old hostility test and the old, unfixed
  `_has_hostiles_or_dead_cache` value) rather than a partial revert:

| World | Ticks | Before (legacy enum) | After (catalog) | Change |
|---|---|---|---|---|
| `crowded_frontier` | 2000 | 874 | 133 | -84.8% |
| `hero_guild_routing` | 2000 | 1418 | 58 | -95.9% |
| `quest_dense_frontier` | 2000 | 0 | 0 | unchanged |
| `metropolis`† | 30 | 15 | 15 | 0.0% |

†`metropolis` used per instruction, with its own disclosed spawn-collision limitation — 30 ticks
and a known-unreliable control, not treated as a clean measurement; included for directional
completeness only, not weighted in the conclusion.
