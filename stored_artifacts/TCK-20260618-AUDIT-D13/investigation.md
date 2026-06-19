# D13 Investigation — Type Safety & Validation Boundary

## Type Checker Configuration Survey

Checked: `mypy.ini`, `.mypy.ini`, `pyproject.toml [tool.mypy]`, `pyrightconfig.json`, `setup.cfg`.

**Result: None found.** No type checker is configured anywhere in the project. The `pyproject.toml`
references `"strict_matrix"` only in test marker descriptions — no `[tool.mypy]` section exists.
`Makefile` has no `mypy` or `pyright` target.

Annotation work in the codebase is documentation only — no tool enforces it.

## AST Scan Results (src/ only, public functions only)

Scanner counted all functions not starting with `_` (except dunder methods).

```
Total public functions scanned: 2,057
Missing return annotations:       186  (9.0%)
Missing arg annotations:           26  (1.3%)
Any usages in annotations:        455
dict / Dict returns:              163
```

### Top files by annotation gap

| File | fns | !ret | !arg | Any | dict |
|---|---|---|---|---|---|
| api/server.py | 20 | 18 | 0 | 0 | 0 |
| core/state.py | 42 | 11 | 3 | 23 | 22 |
| api/engine_manager.py | 28 | 11 | 0 | 10 | 4 |
| api/ws/stream.py | 8 | 8 | 0 | 0 | 0 |
| api/routes/history.py | 8 | 8 | 0 | 0 | 0 |
| lab/workflows.py | 16 | 7 | 0 | 8 | 7 |
| api/routes/behavior.py | 7 | 7 | 0 | 0 | 0 |
| engine/rpg_depth.py | 26 | 0 | 6 | 1 | 1 |
| engine/patches.py | 56 | 1 | 2 | 20 | 0 |
| lab/validator.py | 18 | 3 | 0 | 9 | 0 |

## Critical Boundary Analysis

### api/server.py (18 missing return annotations)
All core simulation API route handlers lack return type annotations:
- `get_metrics()`, `health_check()`, `get_live_snapshot()`, `get_live_status()`
- `inspect_live_entity()`, `get_state()`, `inspect_state()`, `get_entities()`, `get_entity()`
- `pause_sim()`, `resume_sim()`, `publish_test_event()`, `get_live_health()`

FastAPI only validates response shape if `response_model=` is specified on the decorator.
Without it and without return annotations, the response body is not validated — any dict
or object is serialized as-is with no guarantee of shape or field presence.

### api/engine_manager.py (Dict[str, Any] returns on state-query methods)
- L73: `get_metrics_snapshot() -> Dict[str, Any]`
- L176: `get_state() -> Dict[str, Any]`
- L183: `get_full_snapshot() -> Dict[str, Any]`
- L191: `get_entities_paged() -> Dict[str, Any]`
- L198: `get_entity() -> Optional[Dict[str, Any]]`

These bridge engine state to the API layer. Callers receive dicts with unknown key contracts.
A key rename in the engine (e.g. `health_score` → `health`) silently breaks API consumers —
no static check catches it.

### lab/workflows.py (7 run() methods return dict[str, Any])
All workflow types return `dict[str, Any]`:
- `SweepWorkflow.run()`, `MutationWorkflow.run()`, `SandboxWorkflow.run()` (×4), etc.
Callers in `platform/scenarios.py` and tests must know key names by convention only.

### engine/patches.py (merge() -> Any)
`merge()` at L29 returns `Any`. This is used in the engine patch application path.
A type error in a merged patch value only surfaces at runtime when the downstream
consumer encounters an unexpected type.

### core/state.py (to_canonical_dict() → Dict[str, Any] × 13)
13 dataclass types define `to_canonical_dict()` returning `Dict[str, Any]`.
This is intentional — these methods serialize typed dataclasses to JSON-ready dicts.
The gap is that the dict shape is not validated at the consumption point (callers
accessing specific keys have no type guarantee).

## What Is Well-Typed

### FastAPI input validation (good)
`api/routes/search.py` uses `Query()` with type constraints consistently:
```python
async def search_runs(
    scenario_name: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
```
All query parameters are typed and constrained. `behavior.py` follows the same pattern.

### Content loading boundary (good)
`WorldModuleSpec`, `WorldCompositionSpec`, `SimulationScenarioDefinition` are Pydantic
models with `extra="forbid"`. YAML → Pydantic validation runs at load time and catches
unknown fields, type mismatches, and missing required fields immediately.

### Domain phases (mostly good, confirmed in D12)
5 of 8 domain `phase.py` `execute()` methods have typed return annotations.
`world_emergence`, `perception`, `memory` are the 3 without (noted in D12 F4).
