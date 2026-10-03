---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260517-FULL-SCAN-COMPLIANCE
artifact_type: test_plan
tags: [full, scan, compliance]
---

# Milestone 2: Full-Scan Phase Compliance Test Plan

## 1. Automated Test Execution

Execute the newly created integration test file:
```bash
pytest tests/integration/optimization/test_force_full_scan_phase_compliance.py -v
```

## 2. Parity & Regression Guards

Run the existing dirty parity test to ensure no side effects:
```bash
pytest tests/perf/test_dirty_parity.py -v
```

Run the full fast test suite:
```bash
pytest tests/unit/ -m "not slow" -v
```

Verify zero regressions.
