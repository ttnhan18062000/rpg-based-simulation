---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260817-STANDARD-SPAWN-OCCUPANCY-COLLISION-RNG-ROOT-CAUSE
artifact_type: plan
tags: [world, bug, determinism, root-cause, debugging]
---

# Plan: fix the entity spawn RNG collision

## Step 1 — collision-avoidance helper
Add `_resolve_entity_spawn_tile(rng, entity_id, min_x, min_y, max_x, max_y, occupied)` to
`src/worldbuilding/compiler.py`, module-level (alongside `_load_class_table`):
- Deterministic reroll: bumped `sub_id` values (base 100, +2 per attempt, x/y pair), up to
  `_ENTITY_SPAWN_COLLISION_MAX_REROLLS` (12) attempts — still a pure function of
  `(seed, entity_id, sub_id)`, fully reproducible.
- Fallback: deterministic row-major raster scan of the region's bounding box for the tiny
  fraction of cases (none observed in the real corpus) where rerolling exhausts its budget.
- Last resort (region fully packed): return the final reroll draw as-is; caller records a
  compile warning.

## Step 2 — wire into `compile()` step 6
- Move `warnings: List[str] = []` earlier (before step 4) so step 6 can append to it.
- Before the population loop, build `occupied_entity_tiles: Set[tuple[int,int]]` seeded from
  `blocked_tiles` (buildings) ∪ resource-node tile positions.
- Inside the loop, after the base `(x, y)` draw: if it's in `occupied_entity_tiles`, call the
  Step 1 resolver; either way, add the final `(x, y)` to `occupied_entity_tiles` before moving
  to the next entity.
- Do not touch the resource-node (step 4) or building (step 5) loops — no reproduced collision
  in either, and touching them expands blast radius without evidence of a real bug there.

## Step 3 — update the invalidated regression test
`tests/engine/test_hard_law_monitor.py::test_seed42_entity6_entity14_tile_27_38_collision`
currently asserts the bug's exact signature exists. Once fixed, that assertion fails (correctly
— the bug is gone). Update it to assert the fix holds: zero `LAW-SPAWN-OCCUPANCY` violations for
`unit_information_density` seed=42, entity 6 still at (27, 38), entity 14 relocated off of it.
Do not touch `test_check_initial_placement_full_population_scan_unit` (synthetic fixture) or
`test_seed137_and_seed999_no_initial_placement_violations` (negative control, `wilderness_survival`,
already collision-free) — both remain valid, independent coverage.

## Step 4 — verification
1. Direct recompile of `unit_selfmodel_pilot` seed=42: confirm 0 collisions, confirm entity 6's
   position unchanged, confirm 3x repeated compile gives identical `state_hash`.
2. Full 63-combo corpus sweep (18 worlds × seeds 42/137/999): before/after position diff (via
   `git stash` to capture "before") — confirm all previously-colliding combos resolved, confirm
   zero previously-non-colliding entities changed position.
3. Same 63-combo sweep, re-run through the real `HardLawMonitor.check_initial_placement()` —
   confirm zero `LAW-SPAWN-OCCUPANCY` violations of any object-kind pairing.
4. Real `Kernel` run (20 ticks) on `unit_selfmodel_pilot` seed=42 — confirm no
   `hard_law_violations.jsonl` is produced (covers both the init-time law and the downstream
   tick-7 `LAW-OCCUPANCY-COLLISION` from the ticket's Request Summary).
5. Run `tests/engine/test_hard_law_monitor.py`, `tests/integration/observability/test_initial_placement_check.py`,
   `tests/unit/worldbuilding/`, `tests/unit/worldassembly/ -m "not slow"`,
   `tests/unit/worldmodules/`, `tests/integration/kernel/` — confirm no regression. Any failure
   found must be independently reproduced on the unmodified base branch (`git stash`) before being
   dismissed as pre-existing/unrelated.

## Step 5 — parity ledger
Flip `docs/parity_ledger/world_dynamics.yaml`'s `WORLD-076` `divergent` → `verified` per its own
prior instruction ("Flip back to verified once a future ticket fixes the underlying collision and
re-verification is possible"). Preserve the historical record in `divergence_note` rather than
deleting it (INFRA-270 lineage convention). Validate the YAML still parses and the entry still
conforms to `docs/parity_ledger/schema.json`.

## Deviations from this plan
None — implemented exactly as planned. No unexpected findings required a scope change; the
building/resource-node collision gap was anticipated in the investigation and confirmed
unreproduced before deciding to leave it out of scope, rather than discovered as a surprise mid-
implementation.
