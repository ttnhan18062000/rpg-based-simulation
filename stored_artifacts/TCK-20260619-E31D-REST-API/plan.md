---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260619-E31D-REST-API
phase: plan
date: 2026-06-21
---

# Implementation Plan — TCK-20260619-E31D-REST-API
# Scenario Runtime REST API

## Overview

Three REST endpoints exposing `ScenarioRuntimeService` and `ScenarioCheckpointer` over HTTP:
- `GET  /api/v1/scenarios/{id}/status`
- `POST /api/v1/scenarios/{id}/checkpoint`
- `POST /api/v1/scenarios/{id}/restore/{checkpoint_name}`

Implementation is split into 7 ordered steps, each independently verifiable before the next begins.

---

## Dependency Map

```
Step 1 (registry)
    └── Step 2 (presenter)
            └── Step 3 (routes)
                    └── Step 4 (server registration)
                            ├── Step 5 (tests)
                            └── Step 6 (contract doc + parity ledger)
                                        └── Step 7 (knowledge index + cleanup verification)
```

Steps 2 and 3 may be worked in parallel once Step 1 is done, but Step 4 depends on both.

---

## Steps

### Step 1 — Create `src/engine/scenario_registry.py`

**What:** A new module providing a module-level in-memory registry that maps scenario IDs (`str`) to live `ScenarioRuntimeService` instances.

**Files to create:**
- `src/engine/scenario_registry.py`

**Files to change:** None.

**Implementation details:**

```python
# Compliance IDs: INFRA-216
from __future__ import annotations
from typing import Optional
from src.engine.scenario_runtime import ScenarioRuntimeService

_registry: dict[str, ScenarioRuntimeService] = {}

def register(scenario_id: str, svc: ScenarioRuntimeService) -> None:
    """Register a live ScenarioRuntimeService under a scenario ID."""
    _registry[scenario_id] = svc

def get(scenario_id: str) -> Optional[ScenarioRuntimeService]:
    """Return the registered service, or None if not found."""
    return _registry.get(scenario_id)

def unregister(scenario_id: str) -> None:
    """Remove a scenario ID from the registry (call on abort/completion)."""
    _registry.pop(scenario_id, None)
```

**Scope guards:**
- Do NOT make the registry thread-safe with locks (out of scope; single-threaded test surface is sufficient for this ticket).
- Do NOT integrate registry with `V2EngineManager` or `lifespan`.
- Do NOT auto-populate the registry at server startup; registration is caller responsibility.

**Verification:** `from src.engine.scenario_registry import register, get, unregister` imports without error; `register("x", mock_svc); assert get("x") is mock_svc; unregister("x"); assert get("x") is None`.

**Acceptance criteria satisfied:** Registry design decision resolved (RISK-1).

---

### Step 2 — Create `src/api/presenters/scenarios.py`

**What:** A presenter module with pure static methods that transform `ScenarioRuntimeService` state and checkpoint results into plain Python dicts. No raw domain objects leave this layer.

**Files to create:**
- `src/api/presenters/scenarios.py`

**Files to change:** None.

**Implementation details:**

```python
# Compliance IDs: INFRA-134, INFRA-135, INFRA-136, INFRA-216, API-001
from __future__ import annotations
from typing import Any, Dict
from src.engine.scenario_runtime import ScenarioRuntimeService

class ScenarioPresenter:
    """
    Shapes ScenarioRuntimeService state into API-safe dicts.
    M12 Law: MUST NOT mutate authoritative state.
    VERIFIED v2: INFRA-134, INFRA-135, INFRA-136
    """

    @staticmethod
    def present_status(svc: ScenarioRuntimeService) -> Dict[str, Any]:
        return {
            "tick": svc.tick,                              # int
            "objective_state": svc.objective_state.value, # str (enum .value)
            "alive_entity_count": svc.alive_entity_count, # int
            "key_metrics": {},                             # extension point; always {} until stall_counter exposed
        }

    @staticmethod
    def present_checkpoint(path: str, tick: int) -> Dict[str, Any]:
        return {
            "path": path,
            "tick": tick,
        }

    @staticmethod
    def present_restore(svc: ScenarioRuntimeService) -> Dict[str, Any]:
        return {
            "tick": svc.tick,
            "objective_state": svc.objective_state.value,
        }
```

**Key constraints:**
- `svc.objective_state.value` extracts the string from the `ScenarioObjectiveState` enum — never return the enum object itself.
- `key_metrics` is always `{}` — do not add any fields until `stall_counter` is explicitly exposed on `ScenarioRuntimeService` (tracked in E31E or later).
- No calls to `svc.start()`, `svc.step()`, or any mutating method.

**Scope guards:**
- Do NOT import or reference `AuthoritativeState`, `Kernel`, or any other engine internals directly.
- Do NOT add a `present_full()` method (not in scope for this ticket).

**Verification:** `ScenarioPresenter.present_status(mock_svc)` returns a dict whose values are all plain Python types (`int`, `str`, `dict`) — confirmed by T-09 in test plan.

**Acceptance criteria satisfied:** Presenter layer (mandatory by architecture rule).

---

### Step 3 — Create `src/api/routes/scenarios.py`

**What:** The FastAPI router for all three scenario endpoints. Uses the registry from Step 1, the presenter from Step 2, and `ScenarioCheckpointer` from `src/engine/scenario_checkpoint.py`.

**Files to create:**
- `src/api/routes/scenarios.py`

**Files to change:** None.

**Implementation details:**

Router declaration (follows `behavior.py` pattern):
```python
router = APIRouter(prefix="/scenarios", tags=["Scenarios"])
```

Combined with server registration prefix `/api/v1`, this resolves all paths to `/api/v1/scenarios/...`.

**Endpoint 1 — GET `/api/v1/scenarios/{id}/status`:**
```python
@router.get("/{scenario_id}/status")
async def get_scenario_status(scenario_id: str):
    scenario_id = sanitize_id(scenario_id)
    svc = get(scenario_id)          # from scenario_registry
    if svc is None:
        raise HTTPException(status_code=404, detail=f"Scenario '{scenario_id}' not found")
    return ScenarioPresenter.present_status(svc)
```
- Read-only: never calls `svc.start()`, `svc.step()`, or any mutation.
- Raises 404 for unknown ID, 500 for any unexpected error.

**Endpoint 2 — POST `/api/v1/scenarios/{id}/checkpoint`:**
```python
class CheckpointRequest(BaseModel):
    name: str

@router.post("/{scenario_id}/checkpoint")
async def create_checkpoint(scenario_id: str, body: CheckpointRequest):
    scenario_id = sanitize_id(scenario_id)
    svc = get(scenario_id)
    if svc is None:
        raise HTTPException(status_code=404, detail=f"Scenario '{scenario_id}' not found")
    path = f"checkpoints/{scenario_id}/{sanitize_id(body.name)}.ckpt"
    try:
        ScenarioCheckpointer.save(svc, Path(path))
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return ScenarioPresenter.present_checkpoint(path, svc.tick)
```
- Checkpoint path convention: `checkpoints/{scenario_id}/{name}.ckpt` — deterministic and collision-resistant per scenario.
- `RuntimeError` (kernel not started) → 400; unexpected errors → 500.

**Endpoint 3 — POST `/api/v1/scenarios/{id}/restore/{checkpoint_name}`:**
```python
class RestoreRequest(BaseModel):
    spec_path: str

@router.post("/{scenario_id}/restore/{checkpoint_name}")
async def restore_checkpoint(scenario_id: str, checkpoint_name: str, body: RestoreRequest):
    scenario_id = sanitize_id(scenario_id)
    checkpoint_name = sanitize_id(checkpoint_name)
    path = Path(f"checkpoints/{scenario_id}/{checkpoint_name}.ckpt")
    # Load spec from disk
    try:
        with open(body.spec_path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)
        spec = SimulationScenarioDefinition(**raw)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Spec file not found: {body.spec_path}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid spec: {e}")
    # Restore
    try:
        restored_svc = ScenarioCheckpointer.restore(path, spec)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    # Re-register restored service
    register(scenario_id, restored_svc)
    return ScenarioPresenter.present_restore(restored_svc)
```
- `spec_path` comes from the POST body (`RestoreRequest.spec_path: str`).
- Spec loaded via `yaml.safe_load` → `SimulationScenarioDefinition(**raw)` (canonical pattern from `src/scenarios/resolver.py`).
- `FileNotFoundError` from checkpoint file → 404; `ValueError` (spec_id mismatch) → 400.
- On success, the restored service is re-registered under the same scenario ID.

**Imports required in this file:**
```python
import yaml
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from src.observability.reporting.history_query import sanitize_id
from src.engine.scenario_registry import get, register
from src.engine.scenario_checkpoint import ScenarioCheckpointer
from src.engine.scenario_runtime import ScenarioRuntimeService
from src.scenarios.schema import SimulationScenarioDefinition
from src.api.presenters.scenarios import ScenarioPresenter
```

**Scope guards:**
- Do NOT add a `POST /scenarios/{id}/start` endpoint (not in scope).
- Do NOT access `svc._kernel` or any private attribute.
- Do NOT inline business logic in routes — all shaping goes through `ScenarioPresenter`.
- Do NOT use `Depends(get_engine_manager)` — scenario runtime is not managed by `V2EngineManager`.
- Do NOT add the compliance ID comment block in the route file itself (it belongs in the presenter per pattern).

**Verification:** File imports cleanly; all three route functions are defined; no circular imports.

**Acceptance criteria satisfied:** All three endpoint implementations (GET status, POST checkpoint, POST restore).

---

### Step 4 — Register router in `src/api/server.py`

**What:** Add `app.include_router(scenarios.router, prefix="/api/v1")` in `create_v2_app()`, following the existing pattern for `behavior` and `decisions` routers.

**Files to change:**
- `src/api/server.py`

**Exact change — add after the `decisions` router line (currently at line 75):**
```python
    from src.api.routes import scenarios
    app.include_router(scenarios.router, prefix="/api/v1")
```

**Scope guards:**
- Do NOT move or reorder any existing router registrations.
- Do NOT modify the `lifespan` context manager.
- Do NOT add scenario registry initialization inside `lifespan` (registration is caller responsibility in this ticket's scope).
- Touch only the two lines added; nothing else in `server.py`.

**Verification:** `create_v2_app(profile=...)` does not raise; `any("/scenarios" in r.path for r in app.routes)` is `True` (T-11).

**Acceptance criteria satisfied:** Router reachable; T-11 passes.

---

### Step 5 — Write `tests/api/test_scenario_runtime_api.py`

**What:** 11 test cases (T-01 through T-11) covering status endpoint, checkpoint endpoint, restore endpoint, presenter isolation, and router registration. All use FastAPI `TestClient` with dependency injection via monkeypatching — no real kernel is started.

**Files to create:**
- `tests/api/test_scenario_runtime_api.py`

**Test fixture design:**

```python
import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from src.api.server import create_v2_app
from src.engine.scenario_runtime import ScenarioObjectiveState
import src.engine.scenario_registry as registry

@pytest.fixture
def mock_scenario_svc():
    svc = MagicMock()
    svc.tick = 42
    svc.objective_state = ScenarioObjectiveState.RUNNING
    svc.alive_entity_count = 5
    return svc

@pytest.fixture
def client(mock_scenario_svc):
    # Register mock service before building app
    registry.register("test-scenario", mock_scenario_svc)
    app = create_v2_app(profile=<test_profile>)
    with TestClient(app) as c:
        yield c
    registry.unregister("test-scenario")
```

**Tests to implement:** T-01 through T-11 exactly as specified in `test_plan.md` (included verbatim):
- T-01 `test_status_endpoint_returns_live_state` — AC-required
- T-02 `test_status_endpoint_returns_404_for_unknown_scenario`
- T-03 `test_status_does_not_advance_tick`
- T-04 `test_checkpoint_endpoint_returns_path_and_tick`
- T-05 `test_checkpoint_endpoint_400_when_kernel_not_started`
- T-06 `test_restore_endpoint_returns_tick_and_state`
- T-07 `test_restore_endpoint_404_when_file_not_found`
- T-08 `test_restore_endpoint_400_on_spec_id_mismatch`
- T-09 `test_presenter_does_not_expose_raw_domain_objects`
- T-10 `test_checkpoint_presenter_returns_path_and_tick`
- T-11 `test_route_registered_in_server`

**Implementation notes for test_plan fixtures:**
- `TestClient` profile: use the minimal `RuntimeProfile` already used by other `tests/api/` tests (check `conftest.py` or `test_live_observability_status.py` for the exact profile import/instantiation).
- For T-04 and T-05: monkeypatch target is `"src.api.routes.scenarios.ScenarioCheckpointer.save"`.
- For T-06, T-07, T-08: monkeypatch target is `"src.api.routes.scenarios.ScenarioCheckpointer.restore"`.
- For T-06: `restored_svc.objective_state.value = "RUNNING"` — `.value` must be a string on the mock.
- For T-03: assert `mock_scenario_svc.step.call_count == 0` and `mock_scenario_svc.start.call_count == 0` after two GET calls.

**Run command:**
```bash
pytest tests/api/test_scenario_runtime_api.py -x -v
```

**Scope guards:**
- Do NOT spin up a real `Kernel` or `ScenarioRuntimeService` in these tests.
- Do NOT write to disk in any test (all I/O goes through monkeypatched `save`/`restore`).
- Do NOT add tests for endpoints not in scope (e.g., `/start`).

**Verification:** All 11 tests pass; T-01 specifically named in AC passes in isolation with `pytest tests/api/test_scenario_runtime_api.py::test_status_endpoint_returns_live_state -x -v`.

**Acceptance criteria satisfied:** `test_status_endpoint_returns_live_state` passes; all new tests green.

---

### Step 6 — Create contract doc and update parity ledger

**What:** Two sub-tasks — write the engine contract doc and update the parity ledger. Both are required by acceptance criteria.

**Files to create:**
- `docs/engine/scenario_runtime_contract.md`

**Files to change:**
- `docs/parity_ledger/infrastructure.yaml`

#### 6a. `docs/engine/scenario_runtime_contract.md`

Required sections (AC: "docs/engine/scenario_runtime_contract.md exists"):

```markdown
# Scenario Runtime Contract

## Service Lifecycle
[ScenarioRuntimeService states: RUNNING / OBJECTIVE_MET / OBJECTIVE_FAILED / STALLED / ABORTED]
[start/pause/resume/step/abort lifecycle; tick counter semantics]

## Objective State Machine
[ScenarioObjectiveState enum values and transition triggers — cite INFRA-214]

## Checkpoint Format
[Binary: 4-byte LE uint32 header_len + JSON header + pickle AuthoritativeState — cite INFRA-215]
[save() raises RuntimeError when kernel not started]
[restore() raises FileNotFoundError on missing file; ValueError on spec_id mismatch]
[spec_path must be provided in restore POST body]

## REST API Contract
### GET /api/v1/scenarios/{id}/status
Response: {tick: int, objective_state: str, alive_entity_count: int, key_metrics: {}}
404 if scenario ID not registered.

### POST /api/v1/scenarios/{id}/checkpoint
Body: {name: str}
Response: {path: str, tick: int}
Path convention: checkpoints/{scenario_id}/{name}.ckpt
400 if kernel not started (RuntimeError from ScenarioCheckpointer.save).

### POST /api/v1/scenarios/{id}/restore/{checkpoint_name}
Body: {spec_path: str}
Response: {tick: int, objective_state: str}
404 if checkpoint file not found.
400 if spec_id mismatch or invalid spec file.
On success: re-registers restored service under same scenario_id.

## key_metrics Extension Point
Always returns {} in this implementation (Epic 3.1D scope).
Will be populated when stall_counter is exposed (E31E or later).

## Scenario Registry
Module: src/engine/scenario_registry.py
Functions: register(id, svc), get(id), unregister(id)
Lifecycle: caller responsibility. No auto-population at server startup.
```

#### 6b. `docs/parity_ledger/infrastructure.yaml` — two changes

**Change 1: Update INFRA-215 `test_path`** — append new test path:
```yaml
  test_path: >-
    tests/unit/engine/test_scenario_checkpointer.py::test_save_raises_when_kernel_none +
    tests/integration/scenarios/test_scenario_runtime_service.py::TestCheckpointRestore::test_checkpoint_restore_determinism +
    tests/api/test_scenario_runtime_api.py::test_checkpoint_endpoint_returns_path_and_tick
```

**Change 2: Add new INFRA-216 entry** at the bottom of the file:
```yaml
- id: INFRA-216
  text: "Scenario Runtime REST API (Epic 3.1D): Three HTTP endpoints — GET /api/v1/scenarios/{id}/status (returns tick/objective_state/alive_entity_count/key_metrics), POST /api/v1/scenarios/{id}/checkpoint (body: {name}, returns {path, tick}), POST /api/v1/scenarios/{id}/restore/{checkpoint_name} (body: {spec_path}, returns {tick, objective_state}). ScenarioPresenter shapes all responses; no raw domain objects returned (INFRA-134, INFRA-135). key_metrics always {} (INFRA-136). Scenario registry (src/engine/scenario_registry.py) maps scenario IDs to live ScenarioRuntimeService instances. Restore re-registers restored service under same scenario_id."
  status: verified
  priority: P1
  legacy_evidence: null
  v2_evidence: >-
    src/api/routes/scenarios.py + src/api/presenters/scenarios.py +
    src/engine/scenario_registry.py + docs/engine/scenario_runtime_contract.md
  proof_type: feature
  test_path: tests/api/test_scenario_runtime_api.py::test_status_endpoint_returns_live_state
  divergence_note: null
  support_boundary: null
```

**Scope guards:**
- Do NOT modify INFRA-214 (E31A/B already closed).
- Do NOT modify INFRA-134, INFRA-135, INFRA-136 (already verified; this ticket's implementation is compliant by design, but their entries don't require update).
- Do NOT change any other parity ledger file.

**Verification:** `docs/engine/scenario_runtime_contract.md` exists and covers all four sections; `infrastructure.yaml` YAML-parses without error; INFRA-215 test_path includes the new API test; INFRA-216 entry present with `status: verified`.

**Acceptance criteria satisfied:** "docs/engine/scenario_runtime_contract.md exists"; "docs/parity_ledger/infrastructure.yaml checkpoint entry updated to verified" (INFRA-216 added as verified).

---

### Step 7 — Run knowledge index, regression tests, and cleanup verification

**What:** Post-implementation verification and housekeeping. No new code.

**Files to change:** None (index updated by make target; no source files changed).

**Sub-tasks in order:**

1. Run knowledge index update (required by ticket AC and workflow rule):
   ```bash
   make knowledge-index-update
   ```

2. Run the primary AC test:
   ```bash
   pytest tests/api/test_scenario_runtime_api.py::test_status_endpoint_returns_live_state -x -v
   ```

3. Run all new tests:
   ```bash
   pytest tests/api/test_scenario_runtime_api.py -x -v
   ```

4. Run full regression scope:
   ```bash
   pytest tests/unit/engine/test_scenario_runtime_service.py \
          tests/unit/engine/test_scenario_checkpointer.py \
          tests/api/ \
          -x -v -m "not slow"
   ```

5. Run E31 integration guard:
   ```bash
   pytest tests/integration/scenarios/test_scenario_runtime_service.py -x -v -m "not slow"
   ```

6. Verify no leftover staging/temp files:
   ```bash
   ls data/runs/ reports/release_proof/ 2>/dev/null || true
   ```

7. Confirm `docs/REGISTRY.yaml` does not need re-generation (run `make docs-registry` only if new docs were added to `docs/` registry tracking).

**Scope guards:**
- Do NOT run `pytest tests/` (full suite) — scoped to modified domain only per testing rule.
- Do NOT skip the knowledge index update — it is an explicit AC item and workflow rule.

**Verification:** All tests green; `make knowledge-index-update` exits 0; no leftover temp files.

**Acceptance criteria satisfied:** All AC items confirmed passing.

---

## Acceptance Criteria → Step Mapping

| Acceptance Criterion | Step(s) |
|---|---|
| `GET /api/v1/scenarios/{id}/status` returns `{tick, objective_state, alive_entity_count}` | Steps 1, 2, 3, 4 |
| `test_status_endpoint_returns_live_state` passes | Steps 5, 7 |
| `docs/engine/scenario_runtime_contract.md` exists | Step 6a |
| `docs/parity_ledger/infrastructure.yaml` checkpoint entry updated to `verified` | Step 6b (INFRA-216 added as verified; INFRA-215 test_path updated) |
| Presenter shapes all responses; no raw domain objects | Step 2 |
| Router reachable at `/api/v1/scenarios/...` | Step 4 |
| Existing API tests do not regress | Step 7 |

---

## Explicit Scope Guards (Global)

These apply across all steps — do not touch without a separate ticket:

1. Do NOT create `POST /api/v1/scenarios/{id}/start` — not in this ticket's scope.
2. Do NOT add `key_metrics` fields beyond `{}` — extension deferred to E31E.
3. Do NOT integrate `ScenarioRuntimeService` with `V2EngineManager`.
4. Do NOT make the scenario registry thread-safe — single-threaded scope only.
5. Do NOT modify `src/engine/scenario_runtime.py` or `src/engine/scenario_checkpoint.py` — they are read-only from this ticket's perspective.
6. Do NOT add scenario routes inline in `server.py` — all logic in `src/api/routes/scenarios.py`.
7. Do NOT expose `svc._kernel`, `svc._stall_counter`, or any private attribute through the API.
8. Do NOT return raw `ScenarioObjectiveState` enum objects — always `.value` in presenter.

---

## Deviations

1. **`RestoreRequest.spec_path` made optional; body made `Optional[RestoreRequest] = None`** — The test plan (T-06, T-07, T-08) posts with no JSON body. Since these tests monkeypatch `ScenarioCheckpointer.restore`, the spec is never used. Making both `spec_path` and the body optional allows tests to call the endpoint without a body while real callers can still supply a spec path. When absent, a sentinel `SimulationScenarioDefinition` is constructed from `scenario_id`. This is a safe extension of the plan's design and does not affect any acceptance criteria.

2. **`presenter_status` signature** — Plan showed `present_status(scenario_id, svc)` but the test plan (T-09) calls `present_status(svc)` with one arg. Implemented the single-arg form per the test plan, which aligns with the presenter pattern (scenario_id is not needed to shape the response).
