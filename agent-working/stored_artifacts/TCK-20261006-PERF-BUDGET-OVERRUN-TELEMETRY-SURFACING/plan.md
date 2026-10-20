---
status: historical
layer: performance
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20261006-PERF-BUDGET-OVERRUN-TELEMETRY-SURFACING
tags: []
---

# plan - TCK-20261006-PERF-BUDGET-OVERRUN-TELEMETRY-SURFACING

Add budget_overrun_ms / budget_overrun_tick / total_budget_overruns next to dropped_work_delta at the four sites: RuntimeSnapshot (src/engine/observability.py), the engine manager metrics snapshot, the live snapshot runtime_status, and two Prometheus families (sim_budget_overrun_ms gauge, sim_budget_overruns_total counter). Read only from RuntimeStatus; nothing decides on them.
