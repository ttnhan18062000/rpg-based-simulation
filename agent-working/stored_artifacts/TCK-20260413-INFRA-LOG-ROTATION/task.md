---
content_type: doc
status: historical
layer: engine
authority: P2
audience: agent
tags: [infra, log, rotation]
---

- [ ] Implement Log Rotation Mechanism
    - [ ] Add `max_regression_runs` to `SimulationConfig` in `src/config.py`
    - [ ] Update `HeadlessRunner` in `src/testing/headless_regression_runner.py`
        - [ ] Add `max_runs` to `__init__`
        - [ ] Implement `_rotate_logs` method
        - [ ] Integrate `_rotate_logs` into `run` lifecycle
    - [ ] Update `scripts/test_harness.py` to support pass-through configuration
    - [ ] Verification
        - [ ] Create `tests/integration/test_log_rotation.py`
        - [ ] Run verification tests
        - [ ] Perform manual verification with `test_harness.py`
