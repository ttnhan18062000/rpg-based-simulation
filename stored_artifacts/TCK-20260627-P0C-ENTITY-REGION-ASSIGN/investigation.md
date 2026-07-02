---
ticket_id: TCK-20260627-P0C-ENTITY-REGION-ASSIGN
phase: investigation
---

# Investigation: Fix navigation.region_id assignment at world compile

## Current Behavior (file:line refs)

**Pipeline (for `make world-compile WORLD=urban_political`):**

1. `WorldAssemblyResolver.assemble()` (resolver.py) produces `ResolvedWorldBundle(world_spec, compile_context)`
   - `world_spec.entities` = list of `PopulationSpec` objects, each with `spawn_region` set (e.g. `"hometown"`, `"bandit_road"`, `"trading_hometown"`)
2. `WorldCompiler.compile(bundle.world_spec, seed=..., context=bundle.compile_context)` (compiler.py L113)
3. At compiler.py L253-340, for each `pop_spec` in `spec.entities`:
   - L254: `region_id = pop_spec.spawn_region`  ← spawn region IS known
   - L255: `region = regions.get(region_id)`  ← looked up to get bounds for position RNG
   - L258-340: each entity spawned, but the builder chain at L315-337 NEVER calls `.navigation(region_id=region_id)`
   - Result: all entities get `navigation.region_id = None` (default from `NavigationComponent`)

**BUG**: Line 254 has `region_id`, line 315 starts builder, but `.navigation(region_id=region_id)` is missing from the chain.

**Supporting infrastructure (confirmed exists):**
- `V2EntityBuilder.navigation(region_id=...)` method exists at builder.py L353-401, accepts `region_id: Optional[str]`
- `NavigationComponent.region_id: Optional[str] = None` at state.py L373
- `region_id` stored in `ent_properties["spawn_region"]` at compiler.py L304 (identity.properties), but NOT in navigation component

## Why WorldEntitySpawner is NOT the fix path

`WorldEntitySpawner.spawn_from_context()` (entity_spawner.py) is a SEPARATE pipeline that takes a `CompileContext` directly (used in `world-resolve` / module-only flows). The `world-compile` path goes through `WorldCompiler.compile()` which uses `WorldSpec.entities` directly. These are two distinct paths.

The `WorldEntitySpawner` also has a latent bug (`spawn_region=None` hardcoded at entity_spawner.py L52), but fixing it is OUT OF SCOPE — it is not in the reported failure path and the ticket explicitly excludes it.

## Mechanics/Engine Constraints

- No Mechanics Bible constraint on region_id assignment (this is assembly-time bookkeeping, not a simulation law).
- Engine contract `docs/engine/kernel.md`: `NavigationComponent.region_id` is cached at spawn time to avoid O(N) region scans per tick.
- `docs/world/compiler_contract.md` (WORLD-050): entities are compiled in step 6; spawn region drives position randomization. The contract does not explicitly mandate `navigation.region_id` assignment, but the Phase 3 Hardening comment at state.py L372 establishes the intent.

## Parity Ledger Overlap

- `substrate.yaml` entry near L916: `'test_default_region_id': default region identifier is preserved` — this is the closest relevant entry. No specific entry for entity `navigation.region_id` assignment at compile time.
- `combat_movement.yaml` L3776: WorldEntitySpawner path (not in scope here).

## Prior Work

- TCK-20260614-WORLDMOD-UNIFY (working_log): fixed `spawn_region` empty-string bug in the resolver — `spawn_region` IS now correctly set on `PopulationSpec` objects going into `WorldSpec.entities`. This means the upstream data is correct; only the final assignment to `NavigationComponent` is missing.
- TCK-20260627-P0B: added resource nodes to urban_political. No entity spawn changes.

## Risks and Open Questions

1. None: `region_id` is already available in scope at the fix location. No schema changes needed.
2. Determinism: `.navigation(region_id=region_id)` is a pure assignment — no RNG, no side effects. Does not break determinism.
3. Entities that fall through (region not found, `if region:` is False): these are NOT spawned at all. No risk of None-region entities surviving.

## Anti-Drift Hazards

- The `WorldEntitySpawner` path (`entity_spawner.py`) has a separate latent bug (hardcoded `spawn_region=None`). Do not confuse the two paths.
- The fix must be inside `if region:` block (line 256) so that `region_id` is guaranteed non-empty.
