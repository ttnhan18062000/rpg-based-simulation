---
status: historical
layer: performance
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261006-PERF-BUDGET-OVERRUN-TELEMETRY-SURFACING
tags: []
---

# test_plan - TCK-20261006-PERF-BUDGET-OVERRUN-TELEMETRY-SURFACING

tests/observability/test_budget_overrun_telemetry.py (3): zero/-1/0 before any overrun on all surfaces; two recorded overruns show on the metrics snapshot, live snapshot, Prometheus and RuntimeSnapshot next to dropped_work_delta; a source scan shows only the recorder and the four surfaces read the new names.
