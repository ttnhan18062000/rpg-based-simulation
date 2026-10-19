---
status: active
layer: architecture
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261019-D80B-ENGINE-STOPS-IMPORTING-SIMQ-POST-APPLY-OBSERVER-HOOK
date: 2026-10-19
---

# Test plan: D80 B

## New tests (tests/unit/engine/test_run_observers.py)
- A kernel built with no observers runs ticks and shuts down; `kernel.observers == ()`; no `src.simulation_quality` module is imported by the run (assert via `sys.modules` in a subprocess).
- Fan-out: two fake observers receive every envelope in registration order; one raising does not stop the other nor the recorder.
- Lifecycle order: a recording fake logs `start`, `on_envelope`..., `stop_intake`, recorder shutdown, `finish` in that order (the drain-ordering hazard).
- Factory returning `None`, or raising, is skipped and logged; the kernel still runs.
- Observability OFF: factories are not called, nothing is started.

## Moved/updated tests
- `tests/simulation_quality/test_kernel_simq_integration.py` and `test_traceability_path.py`: pass `default_observer_factories()`; read the hub via the observer; same assertions (hub wired, no second drain worker, report fields, QUALITY_SCORING_DISABLED and broker mode give no hub).
- `tests/perf/test_simq_isolation_overhead.py:128`: "mode (a) builds zero in-engine QualityHub" asserts no `QualityRunObserver` in `kernel.observers`.
- `tests/simulation_quality/test_api_routes.py` and the API server wiring: the quality routes still resolve the hub from a kernel built through the engine manager.

## Guards
- `lint-imports`: the new contract fails on 864f7b281 and passes after.
- `tests/architecture` suite and codebase health ratchet (kernel.py shrinks; no new debt).
- `tests/unit/kernel`, `tests/simulation_quality`, `tests/unit/observability`, `tests/api`, mypy gate.

## Measurement (not unit tests)
- Hash: 3 gate worlds x seed 42 x 5000 ticks, audit_mode, PYTHONHASHSEED=0, observability ON and OFF; base 864f7b281 vs branch; final_hash and the whole result JSON equal.
- SimQ: one calibration run (`tools/calibrate_simq.py`) on both, diff report and scores file.
- Paired step recorded as "D80 B" (memo row 82), report-only.
- Light runs only while Lane B and testing hold the host: hash check needs 6 five-thousand-tick runs (3 worlds x ON/OFF, per arm cached), jobs=2.

## Failure modes covered
Hub build failure, broker mode, scoring disabled, observer exception on the drain thread, shutdown ordering.
