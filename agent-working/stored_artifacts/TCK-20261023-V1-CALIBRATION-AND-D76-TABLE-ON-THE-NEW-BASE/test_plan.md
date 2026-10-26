---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20261023-V1-CALIBRATION-AND-D76-TABLE-ON-THE-NEW-BASE
artifact_type: test_plan
tags: []
---

# Test plan — TCK-20261023-V1-CALIBRATION-AND-D76-TABLE-ON-THE-NEW-BASE

- All 63 calibration dirs have quality_report.run_determinism.json with run_id, audit_mode true, signals_zeroed true, and a run_id containing the run's PID (no stale dir). Result: 63 of 63.
- evaluate_simq verdict recorded as information only (630 pillars, 285 REGRESS, 0 missing).
- The roadmap edit is a one-line docs change; the merge with origin/main kept 12.3 and 12.5 Base consistent.
