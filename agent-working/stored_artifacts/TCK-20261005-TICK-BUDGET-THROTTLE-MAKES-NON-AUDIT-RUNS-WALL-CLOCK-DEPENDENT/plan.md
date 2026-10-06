---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20261005-TICK-BUDGET-THROTTLE-MAKES-NON-AUDIT-RUNS-WALL-CLOCK-DEPENDENT
artifact_type: plan
tags: [engine, determinism, measurement]
---

# Plan

None. The owner adopted perf's plan on PR #355: a perf `kernel.py` slice (PERF-M1-T03b) plus the tick-budget throttle made report-only
lands before the salience fix, and perf owns it. This ticket is closed as superseded with its record corrected; `src/engine/kernel.py`
is not edited by rpg until that slice merges.
