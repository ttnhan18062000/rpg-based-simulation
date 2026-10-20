---
status: historical
layer: performance
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261006-PERF-BUDGET-OVERRUN-TELEMETRY-SURFACING
tags: []
---

# investigation - TCK-20261006-PERF-BUDGET-OVERRUN-TELEMETRY-SURFACING

RuntimeStatus already records the overrun (record_budget_overrun). dropped_work_delta is read at engine_manager (metrics snapshot), snapshot_provider (runtime_status dict), prometheus_collector and RuntimeSnapshot.dropped_work_count. src/core/governance.py and src/engine/signal_source.py read dropped_work_delta as an input; they are untouched. Gate: the ticket says these four files were outside the perf partial lift. This change was dispatched to rpg-implementer by rpg-planner, who owns these files on the RPG side; the perf lift is not what authorises it. Recorded here as the ticket asks (acceptance 5).
