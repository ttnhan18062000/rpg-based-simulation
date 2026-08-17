---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260817-STANDARD-SPAWN-OCCUPANCY-COLLISION-RNG-ROOT-CAUSE
artifact_type: investigation
tags: [world, bug, determinism, root-cause, debugging]
---

# Investigation: LAW-SPAWN-OCCUPANCY/LAW-OCCUPANCY-COLLISION root cause

## Context scan performed
1. `mcp__knowledge-search__search_docs` for "LAW-SPAWN-OCCUPANCY entity placement RNG" — surfaced `tickets/done/TCK-20260716-PLACELEGAL-HARDLAW.md`, `stored_artifacts/TCK-20260716-PLACELEGAL-SIMQ-SIGNAL/investigation.md`, `tickets/done/TCK-20260521-OCC-COLLISION.md`, `docs/plans/idea_placement_legality_check.md`.
2. `graphify query "entity placement spawn RNG worldbuilding"` and `graphify query "WorldCompiler entity spawn tile placement"` — located `WorldCompiler` (`src/worldbuilding/compiler.py`), `DeterministicRNG` (`src/platform/rng.py`), `EntityGenerator` (`src/systems/world_systems/generator.py`), `LegalityServiceV2`/`WorldAssemblyResolver` as the relevant community.
3. `tickets/todos/` + `tickets/inprogress/` scanned directly for an existing follow-up (none found before this ticket).
4. Read `tickets/done/TCK-20260716-PLACELEGAL-HARDLAW.md` in full (originating ticket, deferred this exact root cause).
5. Read `tickets/done/TCK-20260817-STANDARD-SPAWN-PLACEMENT-COLLISION-HERO-MONSTER-DIAGONAL.md` — confirmed this is a *different*, already-fixed bug in `V2EngineManager._build()` (API demo scaffolding), not `WorldCompiler.compile()`. Not the same code path.

## Reproduction
Direct compile of `unit_selfmodel_pilot` at seed=42 via `WorldRepository.load_world_with_context()` + `WorldCompiler.compile()`:
```
COLLISION (27, 38) [6, 14]
entity6 (27.0, 38.0) hometown role=4 faction=2
entity14 (27.0, 38.0) hometown role=0 faction=0
region hometown bounds=(10, 10, 40, 40)
total entities 16
```
Matches the ticket's Request Summary exactly (same world, seed, entity IDs, tile).

## Root cause
`src/worldbuilding/compiler.py`, `WorldCompiler.compile()` step 6 (entity population loop, original lines ~278-279):
```python
x = rng.get_int(Domain.WORLD, 0, next_entity_id, min_x, max_x, sub_id=0)
y = rng.get_int(Domain.WORLD, 0, next_entity_id, min_y, max_y, sub_id=1)
```
`DeterministicRNG.get_int()` (`src/platform/rng.py:76-79`) computes a composite seed as a pure function of `(base_seed, domain, tick, entity_id, sub_id)` (`_composite_seed`, lines 50-69) and returns `random.Random(seed).randint(a, b)` — completely stateless, with **no reference to any other object's position**. Each entity's tile is an independent hash of its own ID. Within a bounded region (`hometown` here: 31×31 = 961 tiles, 16 entities), two distinct entity IDs can and do hash to the same tile by chance — a birthday-paradox-style collision, not a logic error in the RNG itself, but a complete absence of occupancy-awareness in the caller.

This confirms the prior ticket's explicitly-unconfirmed hypothesis: "suspected entity-ID-keyed spawn RNG formula, not confirmed." Confirmed here by direct reproduction and code read, not by assumption.

The resource-node loop (step 4, lines ~219-220) and building loop (step 5, lines ~248-249) use the identical unchecked-draw pattern. A full 63-combo corpus sweep via the real `HardLawMonitor.check_initial_placement()` (which checks entities, buildings, resource nodes, and WALL terrain) found zero non-entity-involving violations, before or after the fix — so this pattern has not (yet) produced a reproduced building-vs-building or resource-vs-resource collision, but the same latent gap exists in principle. Flagged out of scope.

## No existing "find nearest free tile" helper
Searched (`grep -rn "nearest_free\|find_free\|free.*tile\|occupied_tiles\|is_tile_free" src/`) — no existing reusable collision-avoidance/free-tile-search helper exists anywhere in the codebase. `LegalityServiceV2.verify_occupancy()` (`src/engine/legality.py`) is a **check**, not a **resolver** — it answers "is this tile legal" for a single candidate, it does not search for an alternative. The fix therefore needed a small new resolver, not a reuse of an existing one; it does reuse `DeterministicRNG`'s existing stateless primitives rather than introducing any new randomness source.

## Why entity 6, not entity 14, keeps its original tile
Entities are placed in ascending `next_entity_id` order (population-authoring order). The fix seeds `occupied_entity_tiles` once before the loop and adds each entity's tile as it's placed. Collision resolution therefore only ever fires on the *later*-placed member of a colliding pair — entity 6 (placed first) is never touched; entity 14 (placed second, after entity 6 already claimed (27,38)) is the one deterministically relocated. This guarantees a previously-non-colliding entity (i.e., one that never triggers the `if (x, y) in occupied_entity_tiles` branch) is bit-identical before and after the fix, satisfying the repo's hard determinism-preservation rule.

## Corpus-wide re-verification (18 worlds × seeds 42/137/999 = 63 combos)
Captured full entity-position maps before the fix (`git stash`) and after, diffed:
- 40 collision-groups (39 combos) existed before — matches the prior ticket's own evidence base almost exactly (it found 3 seed-42 worlds + 17/18 worlds at seed 137; this sweep additionally found seed-999 collisions in the same worlds as seed-137, using the same entity-pair-agnostic detection).
- 0 collision-groups after.
- 0 non-colliding entities changed position.
- Re-run through the real `HardLawMonitor.check_initial_placement()` (covers all object kinds): 0/63 combos produce any `LAW-SPAWN-OCCUPANCY` violation after the fix.

## Live-run confirmation
Constructed a real `Kernel` (same code path as `tools/calibrate_simq.py::_run_engine`) around the fixed `unit_selfmodel_pilot` seed=42 compile, ran 20 real ticks, called `shutdown()`. No `hard_law_violations.jsonl` was produced at all — confirms both `LAW-SPAWN-OCCUPANCY` (init-time) and the downstream `LAW-OCCUPANCY-COLLISION` (originally logged at tick 7 per the ticket's Request Summary) no longer fire for this exact reproduction.
