---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260817-STANDARD-SPAWN-OCCUPANCY-COLLISION-RNG-ROOT-CAUSE
phase: done
date: 2026-08-17
tags: [world, bug, determinism, root-cause, debugging]
---

# TCK-20260817-STANDARD-SPAWN-OCCUPANCY-COLLISION-RNG-ROOT-CAUSE

## Title
Root-cause and fix the entity-ID-keyed spawn RNG bug behind `LAW-SPAWN-OCCUPANCY`/`LAW-OCCUPANCY-COLLISION` collisions (entities 6 & 14, tile (27, 38), seed 42, and the wider corpus)

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
`tests/unit/worldassembly/test_corpus_diversity.py::test_unit_selfmodel_pilot_seed42_1000t_cognition_economy_narrative_grade_stability -m slow` deterministically logs two `HardLawViolation` alerts for `unit_selfmodel_pilot` at seed 42: `LAW-SPAWN-OCCUPANCY` (entity 6 and entity 14 both spawn on tile (27, 38)) and a downstream `LAW-OCCUPANCY-COLLISION` at tick 7 once one of the two entities moves. `HardLawMonitor` runs in default LIGHT mode (non-blocking) so this only logs — it did not fail the test (a sibling, already-closed ticket fixed that test's real failure cause, an unrelated stale grade anchor).

This is the exact signature `tickets/done/TCK-20260716-PLACELEGAL-HARDLAW.md` (AC #2) already reproduced and explicitly deferred: that ticket added the `LAW-SPAWN-OCCUPANCY` detection law and named `unit_selfmodel_pilot` as one of 3 affected worlds at seed 42, and separately found 17/18 worlds affected at seed 137 — but explicitly scoped out root-causing or fixing the underlying RNG placement bug ("suspected entity-ID-keyed spawn RNG formula, not confirmed"). `tickets/todos/` and `tickets/inprogress/` were checked at the start of this ticket; no follow-up for this root cause existed yet.

Root cause confirmed by direct reproduction (see Implementation Notes): `WorldCompiler.compile()` step 6 (`src/worldbuilding/compiler.py`) draws each entity's spawn tile as `rng.get_int(Domain.WORLD, 0, next_entity_id, min_x, max_x, sub_id=0)` / `sub_id=1` — a pure, stateless hash of `(seed, entity_id, sub_id)` with **no occupancy check against any other object already placed** (not other entities, not buildings' `blocked_tiles`, not resource nodes). Two distinct entity IDs can legitimately hash to the same tile within a region's bounds; this is exactly the "entity-ID-keyed spawn RNG formula" the prior ticket suspected but did not confirm.

## Scope
- Root-cause the entity spawn collision in `WorldCompiler.compile()` (`src/worldbuilding/compiler.py`), confirmed via direct reproduction against `unit_selfmodel_pilot` seed=42 (region `hometown`, bounds `(10, 10, 40, 40)`; entities 6 and 14 both hash to `(27, 38)`).
- Fix the placement algorithm so entity spawn tiles never collide with each other, with building tiles, or with resource-node tiles, **without** changing the position of any entity that did not previously collide (determinism/reproducibility preservation is a hard repo rule).
- Reuse the existing deterministic RNG primitives (`DeterministicRNG.get_int`, stateless/order-independent) rather than inventing a new non-deterministic mechanism.
- Update the now-invalidated real-world regression assertion in `tests/engine/test_hard_law_monitor.py::test_seed42_entity6_entity14_tile_27_38_collision` (it asserted the bug's exact signature *exists*; now that the root cause is fixed, that signature no longer reproduces) — convert it into a "stays fixed" regression guard, without weakening the still-valid synthetic-collision detection coverage elsewhere in the same file.
- Re-verify the full 18-world × 3-seed corpus (63 combos) the prior ticket used as its evidence base, both via direct entity-position diffing (before/after) and via the real `HardLawMonitor.check_initial_placement()` detection call.
- Update `docs/parity_ledger/world_dynamics.yaml`'s `WORLD-076` entry: the prior ticket flipped it to `divergent` and explicitly wrote "Flip back to verified once a future ticket fixes the underlying collision and re-verification is possible" — this is that ticket.

## Out of Scope
- Building-vs-building and resource-node-vs-resource-node spawn collisions — not reproduced or reported by `LAW-SPAWN-OCCUPANCY` in the corpus sweep (0/63 combos had any non-entity-involving violation, before or after this fix); `WorldCompiler.compile()`'s building/resource loops still don't collision-check against their own kind. Flagging as a known, unreproduced gap for a future ticket rather than expanding this one's blast radius.
- `WorldEntitySpawner`'s shared-`default_position` bug in `src/worldassembly/entity_spawner.py` — a separate, structurally different pipeline (`SimulationScenarioDefinition` input, not `WorldSpec`), explicitly excluded by the prior ticket's own scope boundary; not touched here.
- `V2EngineManager._build()`'s diagonal hero/monster placement bug (`src/api/engine_manager.py`) — a different, already-fixed bug from earlier in this same session (`tickets/done/TCK-20260817-STANDARD-SPAWN-PLACEMENT-COLLISION-HERO-MONSTER-DIAGONAL.md`), unrelated code path (demo/API scaffolding, not `WorldCompiler.compile()`). Not touched here.
- `HardLawMonitor.check_initial_placement()`/`LAW-SPAWN-OCCUPANCY` detection mechanism itself — already correctly implemented per the prior ticket; not modified (still fully exercised by its existing synthetic-fixture unit tests).
- Exhaustive re-verification of all 17-18 seed-137-affected worlds via a full 1000-tick engine run each — the full 63-combo corpus was re-verified at the compiler level (both direct position-diffing and the real detection call), which is a stronger and cheaper signal than re-running the slow engine simulation per world; one world (`unit_selfmodel_pilot` seed 42) was additionally re-verified via a real 20-tick `Kernel` run to confirm no `hard_law_violations.jsonl` is produced at all (covers both `LAW-SPAWN-OCCUPANCY` at init and the downstream `LAW-OCCUPANCY-COLLISION` at tick 7 the original alert log showed).

## Acceptance Criteria
- [x] Root cause identified with file:line evidence and confirmed by direct reproduction (not assumed).
- [x] `WorldCompiler.compile()`'s entity placement no longer produces colliding tiles for any of the 63 previously-tested world/seed combinations (18 worlds × seeds 42/137/999), verified via `HardLawMonitor.check_initial_placement()` (the real detection mechanism, covers entity/building/resource-node/WALL-terrain cases) returning zero `LAW-SPAWN-OCCUPANCY` violations.
- [x] Every entity that did NOT previously collide keeps its exact original position (bit-identical) — verified by diffing all 63 combos' full entity-position maps before vs. after the fix.
- [x] Repeated compiles of the same world/seed produce a bit-identical `state_hash` (determinism preserved).
- [x] The real seed-42 `unit_selfmodel_pilot` reproduction from the ticket's Request Summary no longer logs `LAW-SPAWN-OCCUPANCY` or `LAW-OCCUPANCY-COLLISION` — verified via a real 20-tick `Kernel` run producing zero `hard_law_violations.jsonl` records.
- [x] `tests/engine/test_hard_law_monitor.py::test_seed42_entity6_entity14_tile_27_38_collision` updated to assert the fix holds (no violations; entity 6 keeps its original tile; entity 14 is deterministically relocated), and passes.
- [x] All pre-existing tests in `tests/engine/test_hard_law_monitor.py`, `tests/integration/observability/test_initial_placement_check.py`, `tests/unit/worldbuilding/`, `tests/unit/worldassembly/` (`-m "not slow"`) pass unmodified.
- [x] `docs/parity_ledger/world_dynamics.yaml`'s `WORLD-076` entry flipped back to `verified` per its own prior "flip back once fixed" note, with `v2_evidence` describing the fix and `divergence_note` preserving the historical record (INFRA-270 lineage convention).

## Related Tickets
`tickets/done/TCK-20260716-PLACELEGAL-HARDLAW.md` (added detection; deferred this root cause), `tickets/done/placement-legality/TCK-20260716-PLACELEGAL-SIMQ-SIGNAL.md` (SimQ signal wiring for the same law, depends on this law existing, not on the RNG fix), `tickets/done/TCK-20260817-STANDARD-SPAWN-PLACEMENT-COLLISION-HERO-MONSTER-DIAGONAL.md` (a different, unrelated spawn-collision bug in `V2EngineManager`, fixed earlier this session).

## Related Docs
`docs/observability/hard_law_monitor.md` (LAW-SPAWN-OCCUPANCY row, unmodified — still accurately describes the detection mechanism, which remains in place as defense-in-depth), `docs/parity_ledger/world_dynamics.yaml` (`WORLD-076`, updated), `docs/plans/idea_placement_legality_check.md` (originating investigation).

## Related Stored Artifacts
`stored_artifacts/TCK-20260817-STANDARD-SPAWN-OCCUPANCY-COLLISION-RNG-ROOT-CAUSE/`

## Related Code Areas
`src/worldbuilding/compiler.py` (`WorldCompiler.compile()` step 6, new `_resolve_entity_spawn_tile()` helper), `tests/engine/test_hard_law_monitor.py`, `docs/parity_ledger/world_dynamics.yaml`, `src/platform/rng.py` (read-only reference — `DeterministicRNG` primitives reused, not modified), `src/observability/hard_law_monitor.py` (read-only reference — detection mechanism reused via `check_initial_placement()`, not modified).

## Assumptions / Open Questions
- Building-vs-building and resource-vs-resource spawn collisions are a real, unreproduced gap (same missing-collision-check pattern, different object kinds) — flagged in Out of Scope as a candidate for a future ticket, not investigated further here since it never fired in the 63-combo sweep.
- The deterministic reroll's `sub_id` offset base (100) and max-reroll budget (12) before falling back to a raster scan are implementation choices, not load-bearing constants — documented inline in `_resolve_entity_spawn_tile()`'s docstring; no region in the 63-combo corpus needed more than a handful of rerolls.

## Implementation Notes
**Root cause (confirmed by direct reproduction, not guessed):**
```
$ .venv/bin/python3 -c "... WorldCompiler.compile(spec, 42, context=context) ..."
COLLISION (27, 38) [6, 14]
entity6 (27.0, 38.0) hometown ...
entity14 (27.0, 38.0) hometown ...
region hometown (10, 10, 40, 40)
```
`src/worldbuilding/compiler.py`, `WorldCompiler.compile()` step 6 (entity population loop):
```python
x = rng.get_int(Domain.WORLD, 0, next_entity_id, min_x, max_x, sub_id=0)
y = rng.get_int(Domain.WORLD, 0, next_entity_id, min_y, max_y, sub_id=1)
```
`DeterministicRNG.get_int()` (`src/platform/rng.py`) is a **stateless** function of `(base_seed, domain, tick, entity_id, sub_id)` — each entity's tile is drawn independently, with zero awareness of any other object's position. This confirms the prior ticket's "suspected entity-ID-keyed spawn RNG formula" hypothesis exactly: two distinct `entity_id` values can legitimately hash to the same `(x, y)` within a region's bounds, with no mechanism to detect or avoid it. The resource-node loop (step 4) and building loop (step 5) have the identical pattern, but the corpus sweep found no reproduced building/resource-node-vs-same-kind collision (see Out of Scope).

**Fix** (`src/worldbuilding/compiler.py`):
- Added `_resolve_entity_spawn_tile()`: given a colliding draw, deterministically re-rolls using bumped `sub_id` values (still a pure function of `seed`/`entity_id`/`sub_id` — fully reproducible, order-independent within a single entity's own resolution), falling back to a deterministic row-major raster scan of the region's bounding box if rerolling doesn't find a free tile within the attempt budget (handles the rare densely-packed-region case without ever looping unboundedly).
- Step 6 now tracks `occupied_entity_tiles`, seeded once from `blocked_tiles` (buildings) and resource-node tile positions, and updated with each entity's tile as it's placed (in ascending `entity_id`/population-authoring order). The base draw is only ever replaced when it actually collides with something already in this set — so the **earlier**-placed entity of any colliding pair is never perturbed, and any entity that never collided keeps its exact original tile.
- `warnings: List[str] = []` was moved earlier in `compile()` (previously declared at the start of step 7) so step 6 can append a compile warning for the theoretical fully-packed-region fallback case (not hit anywhere in the real corpus).

**Verification:**
1. `unit_selfmodel_pilot` seed=42 direct recompile: entity 6 stays at `(27.0, 38.0)`; entity 14 moves to `(13.0, 18.0)`; `check_initial_placement()` returns zero violations; `report["state_hash"]` identical across 3 repeated compiles (`1c43113b66e8c1a7d902dc3b8fc7deea`).
2. Full corpus sweep (18 worlds × seeds 42/137/999 = 63 combos, matching the prior ticket's own evidence scope exactly): captured entity positions before the fix (`git stash`), recompiled after the fix, diffed. 40 collision-groups existed before (39 world/seed combos affected — matches the prior ticket's "17/18 worlds at seed 137" finding plus the 3 named seed-42 worlds); 0 collision-groups after. **Zero** non-colliding entities changed position across all 63 combos.
3. Full corpus re-run through the real `HardLawMonitor.check_initial_placement()` (covers entities + buildings + resource nodes + WALL terrain, not just entity-vs-entity): 0/63 combos produce any `LAW-SPAWN-OCCUPANCY` violation.
4. Real `Kernel` run: compiled `unit_selfmodel_pilot` seed=42, constructed a real `Kernel` (same code path `tools/calibrate_simq.py::_run_engine` uses), ran 20 real ticks, called `kernel.shutdown()`. No `hard_law_violations.jsonl` file was produced at all — confirms neither `LAW-SPAWN-OCCUPANCY` (init) nor the downstream `LAW-OCCUPANCY-COLLISION` (originally logged at tick 7 in the ticket's Request Summary) fire anymore for this exact reproduction.
5. `tests/engine/test_hard_law_monitor.py::test_seed42_entity6_entity14_tile_27_38_collision` updated: now asserts zero `LAW-SPAWN-OCCUPANCY` violations for `unit_information_density` seed=42 (the world this specific test targets), entity 6 still at `(27, 38)`, entity 14 relocated off of it. `test_check_initial_placement_full_population_scan_unit` (synthetic two-entity collision fixture, same file) continues to independently cover the detection mechanism itself, unaffected by this world/seed no longer reproducing a real collision.
6. `docs/parity_ledger/world_dynamics.yaml`'s `WORLD-076` flipped `divergent` → `verified` per its own prior instruction; `divergence_note` preserves the full historical record rather than deleting it.

## Test Summary
- `tests/engine/test_hard_law_monitor.py`: 12/12 passed (including the updated regression test).
- `tests/integration/observability/test_initial_placement_check.py`: 2/2 passed.
- `tests/unit/worldbuilding/`: 122/122 passed.
- `tests/unit/worldassembly/` (`-m "not slow"`): 120 passed, 33 deselected.
- `tests/unit/worldmodules/` + `tests/integration/kernel/` combined: 145 passed, 1 pre-existing failure (`test_long_run_determinism.py::test_1000_tick_determinism`, a wall-clock watchdog timeout under this machine's tick-budget resource limit during a 1000-tick run) — independently reproduced identically on the unmodified base branch via `git stash` before concluding it's unrelated to this change.
- Determinism: 3 repeated compiles of `unit_selfmodel_pilot` seed=42 produce identical `state_hash` and identical full entity-position maps.
- Corpus regression check (not a pytest run — a direct before/after diff script, see Implementation Notes item 2): 63/63 world/seed combos, 0 non-colliding entities changed, 39/39 previously-colliding combos now collision-free.

## Files Changed
- `src/worldbuilding/compiler.py` — root-cause fix: `_resolve_entity_spawn_tile()` helper, `occupied_entity_tiles` tracking in `compile()` step 6, `warnings` declaration moved earlier.
- `tests/engine/test_hard_law_monitor.py` — updated `test_seed42_entity6_entity14_tile_27_38_collision` to assert the fix holds instead of asserting the original bug's signature.
- `docs/parity_ledger/world_dynamics.yaml` — `WORLD-076` flipped `divergent` → `verified`.
- `tickets/inprogress/TCK-20260817-STANDARD-SPAWN-OCCUPANCY-COLLISION-RNG-ROOT-CAUSE.md` — this file.
- `staging_artifacts/TCK-20260817-STANDARD-SPAWN-OCCUPANCY-COLLISION-RNG-ROOT-CAUSE/{investigation,plan,test_plan}.md`.

## Completion Summary
Confirmed the prior ticket's "suspected entity-ID-keyed spawn RNG formula" hypothesis by direct reproduction: `WorldCompiler.compile()`'s entity-placement loop draws each entity's spawn tile as a stateless hash of `(seed, entity_id, sub_id)` with zero occupancy awareness against any other placed object. Fixed by tracking already-occupied tiles (buildings, resource nodes, previously-placed entities) and deterministically resolving only actual collisions — via bumped-sub_id reroll, falling back to a raster scan — while leaving every non-colliding entity's position bit-identical. Verified across the full 63-combo corpus (18 worlds × 3 seeds) the prior ticket used as its evidence base: all 39 previously-colliding combos are now collision-free (confirmed both by direct position diffing and by the real `HardLawMonitor.check_initial_placement()` detection call), zero non-colliding entities were perturbed, and determinism (`state_hash`) is preserved across repeated compiles. Additionally verified via a real 20-tick `Kernel` run on the exact `unit_selfmodel_pilot` seed=42 reproduction from this ticket's Request Summary that neither `LAW-SPAWN-OCCUPANCY` nor the downstream `LAW-OCCUPANCY-COLLISION` fire anymore. Updated the one test whose premise (the bug existing) was invalidated by the fix, without weakening the still-independent synthetic detection-mechanism coverage. Flipped `docs/parity_ledger/world_dynamics.yaml`'s `WORLD-076` back to `verified` per its own prior "flip back once fixed" instruction. Building-vs-building and resource-vs-resource spawn collisions remain a real but unreproduced gap of the same pattern, explicitly flagged out of scope for a future ticket.
