---
status: active
layer: engine
authority: P1
audience: developer
---

# Scenario Runtime Contract

**Compliance IDs:** INFRA-214, INFRA-215, INFRA-216  
**Epic:** 3.1 (E31A through E31D)  
**Authority:** P1

---

## Service Lifecycle

`ScenarioRuntimeService` owns a `Kernel` for the duration of one scenario run. The tick loop is synchronous — no threads. Lifecycle methods:

| Method | Effect |
|--------|--------|
| `start(tick_limit)` | Build kernel (first call) and run tick loop up to `tick_limit` ticks. Idempotent if called while paused. Raises `RuntimeError` if already ABORTED. |
| `pause()` | Cooperative flag: halts loop after current tick. Safe to call multiple times. |
| `resume(tick_limit)` | Clear pause flag, continue tick loop. Raises `RuntimeError` if kernel not started or ABORTED. |
| `step()` | Advance exactly one tick. Builds kernel on first call. Raises `RuntimeError` in any terminal state. |
| `abort()` | Set ABORTED, call `kernel.shutdown()`. Idempotent. |

Tick counter (`svc.tick`) is the count of completed ticks. It starts at 0 and is not reset by `abort()`.

---

## Objective State Machine

`ScenarioObjectiveState` is a `str` enum. Values:

| State | Meaning |
|-------|---------|
| `RUNNING` | Scenario is active; no terminal condition reached. |
| `OBJECTIVE_MET` | A `tick_limit` victory condition was satisfied. |
| `OBJECTIVE_FAILED` | An `entity_count` failure condition was satisfied. |
| `STALLED` | `STALL_THRESHOLD` (50) consecutive zero-event ticks elapsed without an objective condition firing. |
| `ABORTED` | `abort()` was called explicitly. |

Evaluation order per tick (cite INFRA-214): objective conditions are checked before the stall detector. Once any terminal state is reached, `_paused` is set to `True` to break `_run_loop()`.

---

## Checkpoint Format

Binary format (cite INFRA-215):

```
[4 bytes] little-endian uint32: length of JSON header in bytes
[N bytes] UTF-8 JSON header: {"tick": <int>, "spec_id": "<str>", "rng_checkpoint": <any>}
[rest]    pickle blob of AuthoritativeState
```

Behaviour:

- `ScenarioCheckpointer.save(svc, path)` raises `RuntimeError` when kernel not started.
- `ScenarioCheckpointer.restore(path, spec)` raises `FileNotFoundError` if the checkpoint file does not exist.
- `ScenarioCheckpointer.restore(path, spec)` raises `ValueError` if `checkpoint.spec_id != spec.id`.
- The restored service's `_tick` counter is set to the checkpoint tick.
- RNG stream is restored via `DeterministicRNG.set_state(rng_checkpoint)`.
- `spec_path` must be provided in the restore POST body when calling via REST (see below). If omitted, a sentinel spec is constructed from the `scenario_id` path parameter.

---

## REST API Contract

### GET `/api/v1/scenarios/{id}/status`

Returns the current live state of a registered `ScenarioRuntimeService`.

**Response (200):**
```json
{
  "tick": 42,
  "objective_state": "RUNNING",
  "alive_entity_count": 5,
  "key_metrics": {}
}
```

**Errors:**
- `404` — Scenario ID not registered in the scenario registry.

**Constraints:** Read-only. Never calls `svc.start()`, `svc.step()`, or any mutating method.

---

### POST `/api/v1/scenarios/{id}/checkpoint`

Saves a checkpoint of the running scenario to disk.

**Request body:**
```json
{"name": "my-save"}
```

**Response (200):**
```json
{
  "path": "checkpoints/{scenario_id}/my-save.ckpt",
  "tick": 42
}
```

**Errors:**
- `400` — Kernel not started (`RuntimeError` from `ScenarioCheckpointer.save`).
- `404` — Scenario ID not registered.
- `500` — Unexpected I/O error.

**Path convention:** `checkpoints/{scenario_id}/{name}.ckpt`. Parent directories are created automatically by `ScenarioCheckpointer.save`.

---

### POST `/api/v1/scenarios/{id}/restore/{checkpoint_name}`

Restores a scenario from a checkpoint file and re-registers the restored service.

**Request body (optional):**
```json
{"spec_path": "/path/to/scenario.yaml"}
```

If `spec_path` is omitted or body is absent, a sentinel `SimulationScenarioDefinition` is constructed from the `scenario_id` path parameter.

**Response (200):**
```json
{
  "tick": 25,
  "objective_state": "RUNNING"
}
```

**Errors:**
- `400` — Spec file invalid or `spec_id` mismatch (`ValueError` from `ScenarioCheckpointer.restore`).
- `404` — Spec file not found, or checkpoint file not found (`FileNotFoundError`).

**Post-restore behaviour:** On success, the restored service is re-registered under the same `scenario_id` via `scenario_registry.register()`.

---

## key_metrics Extension Point

`key_metrics` in the status response is always `{}` in this implementation (Epic 3.1D scope). The field is reserved for future population when `stall_counter` and other runtime metrics are explicitly exposed on `ScenarioRuntimeService` (tracked in E31E or later).

---

## Scenario Registry

Module: `src/engine/scenario_registry.py`

| Function | Signature | Effect |
|----------|-----------|--------|
| `register` | `(scenario_id: str, svc: ScenarioRuntimeService) -> None` | Store `svc` under `scenario_id`. |
| `get` | `(scenario_id: str) -> ScenarioRuntimeService \| None` | Return registered service or `None`. |
| `unregister` | `(scenario_id: str) -> None` | Remove entry. Safe if ID absent. |

**Lifecycle:** Caller responsibility. No auto-population at server startup. No thread safety (single-threaded scope; see E31E for threading considerations). The registry is module-level state — tests must call `unregister` in teardown to avoid cross-test pollution.
