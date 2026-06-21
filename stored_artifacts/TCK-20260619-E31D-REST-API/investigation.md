---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260619-E31D-REST-API
phase: investigation
date: 2026-06-21
---

# Investigation — TCK-20260619-E31D-REST-API

## Current Behavior

### What exists

`ScenarioRuntimeService` (`src/engine/scenario_runtime.py`) and `ScenarioCheckpointer` (`src/engine/scenario_checkpoint.py`) are fully implemented by E31A/B/C but are not reachable from any HTTP surface. No scenario-scoped routes exist in `src/api/routes/`.

**`ScenarioRuntimeService` public API surface available to the REST layer:**
- `svc.tick` → `int` — completed tick count (line 211)
- `svc.objective_state` → `ScenarioObjectiveState` (str enum: `RUNNING / OBJECTIVE_MET / OBJECTIVE_FAILED / STALLED / ABORTED`) (line 216)
- `svc.alive_entity_count` → `int` — `len(kernel.state.entities)`, 0 when not started (line 226)
- `svc.start(tick_limit)`, `svc.pause()`, `svc.resume(tick_limit)`, `svc.step()`, `svc.abort()`

**`ScenarioCheckpointer` API:**
- `ScenarioCheckpointer.save(svc, path)` — raises `RuntimeError` if kernel not started (line 26–43 of scenario_checkpoint.py)
- `ScenarioCheckpointer.restore(path, spec)` → fresh `ScenarioRuntimeService` — raises `FileNotFoundError` or `ValueError` (spec_id mismatch) (line 51–114)

**Ticket-defined response shapes:**
```
GET  /api/v1/scenarios/{id}/status
     → {tick, objective_state, alive_entity_count, key_metrics: {...}}

POST /api/v1/scenarios/{id}/checkpoint
     body: {name: "checkpoint_name"}
     → {path: "checkpoints/...", tick: N}

POST /api/v1/scenarios/{id}/restore/{checkpoint_name}
     → {tick: N, objective_state: "RUNNING"}
```

`key_metrics` is not defined on `ScenarioRuntimeService` — it is not a current property. This must be introduced or defined as a fixed empty/minimal dict. **See Open Questions.**

### Existing API infrastructure

- `src/api/server.py` — `create_v2_app()` registers routers via `app.include_router(...)` with `prefix="/api/v1"` (lines 63–75). New scenarios router must be registered here.
- `src/api/dependencies.py` — `get_engine_manager()` / `set_engine_manager()` returns a `V2EngineManager`. The scenario runtime service is NOT managed by `V2EngineManager` — it is standalone. The routes need their own scenario registry or must accept the service as injected state. **See Open Questions.**
- `src/api/routes/behavior.py` — reference route file. Uses `APIRouter(prefix="/behavior", tags=["Behavior"])`, Pydantic `BaseModel` for `ErrorResponse`, `HTTPException` for 400/500, `sanitize_id()` for inputs.
- `src/api/routes/decisions.py` — reference for routes that combine path params and query params; uses `Query(...)` for required query params.
- `src/api/presenters/state_presenter.py` — reference presenter: pure static methods returning `Dict[str, Any]`, compliance IDs in module header comment.

### Files that do NOT yet exist (will be created)
- `src/api/routes/scenarios.py`
- `src/api/presenters/scenarios.py`
- `tests/api/test_scenario_runtime_api.py`
- `docs/engine/scenario_runtime_contract.md`

### Existing tests
- `tests/api/` — 11 files. Relevant: `test_rest_parity.py` (subprocess-style integration), `test_live_observability_status.py`, `test_paged_logic.py`. No scenario API tests yet.
- `tests/unit/engine/test_scenario_runtime_service.py` — E31A/B unit tests (must still pass).
- `tests/unit/engine/test_scenario_checkpointer.py` — E31C unit tests (must still pass).
- `tests/integration/scenarios/test_scenario_runtime_service.py` — E31B/C integration tests.


## Mechanics / Engine Constraints

1. **API presenters MUST NOT mutate authoritative state** (INFRA-134, INFRA-135, M12 Law in `state_presenter.py` line 9). The status endpoint reads `svc.tick`, `svc.objective_state`, `svc.alive_entity_count` — all are read-only properties. Compliant by design.

2. **API exposes supported gameplay state only** (INFRA-136). `key_metrics` field must only contain values derivable from existing properties; no speculative or stub fields.

3. **Presenter layer required** — the ticket explicitly states "do not return raw domain objects." `ScenarioObjectiveState` is a `str` enum — serializes safely — but the full response must be shaped in `src/api/presenters/scenarios.py`.

4. **No raw domain models from APIs** (Hard Rule). Presenter is mandatory for all 3 endpoints.

5. **Checkpoint path convention** — `ScenarioCheckpointer.save()` takes an arbitrary `path`. The POST checkpoint endpoint must choose a deterministic path convention: `checkpoints/{scenario_id}_{name}.ckpt` (matching E31C ticket scope text) or the binary format extension `.bin`. The checkpoint path is returned in the response — callers depend on it for restore.

6. **Restore POST endpoint** — `ScenarioCheckpointer.restore(path, spec)` needs a `SimulationScenarioDefinition` spec. The REST layer must have access to the scenario spec by ID. This requires either a scenario registry or a mechanism to look up/reconstruct the spec from `{id}`. **This is the highest-risk design gap — see Open Questions.**

7. **`scenario_runtime_contract.md` required by AC** — The ticket requires `docs/engine/scenario_runtime_contract.md` to be created and `make knowledge-index-update` to be run after.


## Parity Ledger Overlap

The following `docs/parity_ledger/infrastructure.yaml` entries are touched by or relevant to this ticket:

| ID | Text summary | Current status | Action required |
|----|-------------|----------------|-----------------|
| INFRA-133 | Replay tests include save/load continuation | `verified` | No change — E31C already satisfies |
| INFRA-134 | API state view is derived from authoritative state | `verified` | Verify new endpoints comply (read-only presenter) |
| INFRA-135 | API state view does not mutate authoritative state | `verified` | Verify presenter compliance |
| INFRA-136 | API exposes supported gameplay state only | `verified` | Verify `key_metrics` content |
| INFRA-214 | ScenarioRuntimeService lifecycle (E31A+B) | `verified` | No change — entries for A/B already closed |
| INFRA-215 | ScenarioCheckpointer (E31C) | `verified` | **Update**: add REST API test path as additional evidence; update `test_path` to include new `tests/api/test_scenario_runtime_api.py` test(s) that exercise checkpoint/restore via HTTP |

Additionally, a **new entry INFRA-216** should be added at completion to cover the scenario REST API surface:
- Text: "Scenario runtime REST API (Epic 3.1D): three endpoints — GET /api/v1/scenarios/{id}/status, POST checkpoint, POST restore/{checkpoint_name}. Status returns tick/objective_state/alive_entity_count/key_metrics. Presenter shapes all responses; no raw domain models returned."
- `status: verified` upon passing tests
- `test_path: tests/api/test_scenario_runtime_api.py::test_status_endpoint_returns_live_state`


## Prior Work

| Ticket | Key deliverable | Relevant to E31D |
|--------|----------------|-----------------|
| TCK-20260619-E31A-SCENARIO-SERVICE | `ScenarioRuntimeService` — tick, objective_state, alive_entity_count | Direct data source for status endpoint |
| TCK-20260619-E31B-OBJECTIVE-FSM | `ObjectiveEvaluator`, stall detector, `ScenarioObjectiveState` enum | Status response `objective_state` field |
| TCK-20260619-E31C-CHECKPOINT | `ScenarioCheckpointer.save()/restore()`, binary format, spec_id validation | Direct implementation of checkpoint + restore endpoints |

Checkpoint binary format (from E31C): 4-byte LE uint32 header length + JSON `{tick, spec_id, rng_checkpoint}` + pickle blob of `AuthoritativeState`. The path returned by the POST checkpoint endpoint must be usable as input to POST restore.

The `V2EngineManager` (`src/api/engine_manager.py`) manages the simulation loop for the general API. The `ScenarioRuntimeService` is **not** managed by `V2EngineManager` — it is a standalone object. The REST routes cannot use `Depends(get_engine_manager)` to access it.


## Risks and Open Questions

### RISK-1 (HIGH): Scenario registry / service lookup
The three endpoints take `{id}` as path param (scenario ID), but there is no in-process registry that maps scenario IDs to live `ScenarioRuntimeService` instances. Two viable designs:
- **Option A (in-memory registry)**: A module-level `Dict[str, ScenarioRuntimeService]` injected or initialized at startup — simple but requires lifecycle management. Scenarios must be started before being queried.
- **Option B (stateless, file-backed)**: Status reads from checkpoint files only; no live service concept. Does not support a running scenario.

The ticket implies a **live** service (status returns live state: alive_entity_count from running kernel). Option A (or a thread-safe singleton registry) is the right fit. Implementer must decide: how is a `ScenarioRuntimeService` registered? Does `POST /scenarios/{id}/start` exist (not in scope), or is registration done at startup?

**Decision required**: How is the service registered for `{id}` before `GET /status` can return live data?

### RISK-2 (MEDIUM): `key_metrics` field content
The ticket spec includes `key_metrics: {...}` in the status response but `ScenarioRuntimeService` has no `key_metrics` property. Options:
- Return `{}` always (empty dict) for now — safe and honest
- Add `key_metrics` property to service returning e.g. `{"stall_counter": self._stall_counter}` — expands footprint into E31E territory
- Document as `{}` in contract, leaving extension point

Returning `{}` is the safest option; the contract doc should note it is an extension point.

### RISK-3 (MEDIUM): Restore endpoint needs a spec
`ScenarioCheckpointer.restore(path, spec)` requires a `SimulationScenarioDefinition`. The checkpoint file header has `spec_id` but not the full spec. The restore endpoint cannot reconstruct the spec from just `spec_id` without a spec loader or registry. The checkpoint header's `spec_id` field can be extracted from the binary file without full deserialization to validate match, but the spec itself must come from somewhere.

**Decision required**: Should restore use a spec from a request body, or derive it from a scenario spec file system path?

### RISK-4 (LOW): Route prefix vs. existing server.py pattern
`server.py` uses `app.include_router(router, prefix="/api/v1")`. The scenarios router itself should use `prefix="/scenarios"` so the combined path resolves to `/api/v1/scenarios/{id}/...`. Confirmed by inspection of `behavior.py` (prefix="/behavior") and `decisions.py` (prefix="/observability").

### RISK-5 (LOW): Checkpoint path collisions
`POST /scenarios/{id}/checkpoint` with `body.name` must produce a stable, collision-resistant path. Suggested: `checkpoints/{scenario_id}/{name}.ckpt`. The directory is created by `ScenarioCheckpointer.save()` (line 43: `path.parent.mkdir(parents=True, exist_ok=True)`).


## Anti-Drift Hazards

1. **Do not return `ScenarioRuntimeService` or `ScenarioObjectiveState` directly** — shape through `ScenarioPresenter`. Enum's `.value` serializes to string automatically but the response model must be explicit.
2. **Do not call `svc.start()` or `svc.step()` inside a GET handler** — read-only surface. The status endpoint must never advance the tick.
3. **Do not access `svc._kernel` directly in the route layer** — all access through public properties (`tick`, `objective_state`, `alive_entity_count`).
4. **Do not add scenario routes inline in `server.py`** — follow the router registration pattern; place logic in `src/api/routes/scenarios.py`.
5. **Compliance ID comment is required** in new source files — follow pattern in `state_presenter.py` line 1 and `scenario_runtime.py` line 1.
6. **`make knowledge-index-update` must be run** after `docs/engine/scenario_runtime_contract.md` is created — this is in the AC and the workflow rule.
7. **INFRA-215 test_path must be updated** in `docs/parity_ledger/infrastructure.yaml` to reference the new API tests, and INFRA-216 must be added as a new entry.
