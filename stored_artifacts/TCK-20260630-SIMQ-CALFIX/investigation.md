---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260630-SIMQ-CALFIX
artifact_type: investigation
tags: [simq, calibration, tooling, world-loading, occupancy-collision]
---

# Investigation: TCK-20260630-SIMQ-CALFIX

## Current Behavior of `_run_engine()`

`tools/calibrate_simq.py::_run_engine()` completely ignores the `--name` argument.
It always constructs a generic simulation:
- 1 hero at (64.0, 64.0)
- `entity_count - 1` goblins at `(60.0 + i, 60.0 + i)` for i in 0..entity_count-2

With the default `--entities 10`, i=4 produces position (64.0, 64.0) — identical to the
hero's spawn tile — triggering `LAW-OCCUPANCY-COLLISION` on every calibration run.

## World Loading Architecture

### Resolved WorldSpec Location
Pre-compiled WorldSpecs are stored at:
`data/worlds/{name}/resolved/world.resolved.yaml` — schema `worldspec.v1`

These are the output of the WorldAssembly pipeline and can be loaded directly as a
`WorldSpec` Pydantic model, then passed to `WorldCompiler.compile()`.

The top-level `data/worlds/{name}/world.yaml` uses schema `worldcomposition.v1` and
is NOT a WorldSpec — it is an assembly composition directive.

### WorldCompiler.compile() API
Located at `src/worldbuilding/compiler.py` L106.
Signature:
```python
@staticmethod
def compile(
    spec: WorldSpec,
    seed: int,
    output_report_path: Optional[str] = None,
    context: Optional[Any] = None,
) -> tuple[AuthoritativeState, dict]:
```
- Pure static method, no DI container required — safe to call standalone from calibration tool
- Returns a fully populated `AuthoritativeState` with entities, regions, resource_nodes, buildings, terrain, etc.
- Deterministic given same spec + seed

### Profile Loading
`ScoringWeights.load(weights_path, grade_path, detection_path, profile=...)` loads
`config/simulation_quality/profiles/{profile}.yaml` via `_load_profile_weights()`.
Available profiles: `default.yaml`, `dungeon_crawl.yaml`, `urban_political.yaml`.
If a profile file does not exist, it silently returns `{}` (empty overrides, equivalent to default).

### AuthoritativeState Initialization
Currently hardcoded in `_run_engine()`:
```python
state = AuthoritativeState(tick=0, seed=seed, entities=entities)
```
`WorldCompiler.compile()` returns a fully populated `AuthoritativeState` which replaces this.

## Test Coverage
- `tests/simulation_quality/test_kernel_simq_integration.py` — kernel/hub wiring, not world loading
- `tests/simulation_quality/test_grade_regression.py` — grade regression anchors
- `tests/simulation_quality/test_quality_hub_integration.py` — hub integration
- No existing test covers `calibrate_simq.py` behavior directly (it is a CLI tool)

## Risks

1. **WorldCompiler.compile() standalone** — VERIFIED safe. It is a `@staticmethod` with no
   class-level state or DI dependencies. It imports from `src.worldbuilding.schema`,
   `src.core.state`, `src.core.builder`, `src.platform.rng`. All are standalone modules.

2. **Worlds without a resolved spec** — Some worlds may not have `resolved/world.resolved.yaml`
   (e.g. `generated_frontier_3_42`). Fix must fall back to generic behavior gracefully.

3. **Entity count from WorldSpec** — The world spec may spawn fewer entities than the
   `--entities` CLI arg expected. This is intentional: world-specific counts replace
   the generic count when a world is loaded.

4. **Goblin position fix in fallback** — Even without world loading, the generic path
   needs the stagger fix to avoid the i=4 collision.
