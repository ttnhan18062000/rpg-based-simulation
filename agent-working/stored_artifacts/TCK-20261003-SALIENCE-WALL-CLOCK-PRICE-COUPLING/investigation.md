---
status: active
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20261003-SALIENCE-WALL-CLOCK-PRICE-COUPLING
artifact_type: investigation
tags: [determinism, economy, engine]
---

# Investigation

- Readers of `pressure_signals` in `src/`: `kernel.py` (writer), `apply.py` (stores the update's dict, keeps the prior one when unset), `pipeline.py` (keys starting `ENABLE_` are feature flags), `economy.py` (the price), `observability/reporting/metric_recorder.py`, `testing/scenario_runner.py` (builds its own state, no kernel). Nothing else reads a salience-derived value.
- In production `state.pressure_signals` was always `{global_salience, debt_ratio, compute_ratio}` written by the kernel each tick. After the change it stays the initial `{}`. A state built with `ENABLE_*` flags used to have them wiped after tick 1 by the kernel's dict and now keeps them; only `scenario_runner.py` and `tests/integration/domains/test_fused_loop.py` build such a state.
- `debt_ratio` was always 0 (`work_debt` never accumulates, `TCK-20261004-WORK-DEBT-NEVER-ACCUMULATES-IN-PRODUCTION`), so salience was `min(2.0, compute_ratio)`, `compute_ratio = tick_compute_ms / max_tick_budget_ms`; `audit_mode` zeroed `tick_compute_ms`.
- PERF-D5 finding (recorded, not changed): `pressure_signals` is outside the proof digest. With the kernel no longer writing it, no live value hides there.
- SimQ economy calibration drift: not measured. `tests/simulation_quality/test_grade_regression.py` skips 82 of 89 tests without its calibration reports; `grade_anchors.json` not re-measured. Expected small (compute term near zero on fast hosts).
