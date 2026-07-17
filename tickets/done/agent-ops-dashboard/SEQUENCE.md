# Implementation Sequence — agent-ops-dashboard

Tickets must be implemented in this order. Generated automatically from intra-batch
dependency analysis. `implement-epic` reads this file to override alphabetical order.

## Order

1. TCK-20260716-AGENTOPS-DASHBOARD-BACKEND  (no deps in this batch)
2. TCK-20260716-AGENTOPS-ACTIVITY-GANTT  (depends on: TCK-20260716-AGENTOPS-DASHBOARD-BACKEND)
3. TCK-20260716-AGENTOPS-REPLAY-TIMELINE  (depends on: TCK-20260716-AGENTOPS-DASHBOARD-BACKEND)
4. TCK-20260716-AGENTOPS-TICKETS-VIEW  (depends on: TCK-20260716-AGENTOPS-DASHBOARD-BACKEND)
5. TCK-20260716-AGENTOPS-BUILD-SERVE  (depends on: TCK-20260716-AGENTOPS-TICKETS-VIEW, TCK-20260716-AGENTOPS-ACTIVITY-GANTT, TCK-20260716-AGENTOPS-REPLAY-TIMELINE, TCK-20260716-AGENTOPS-DASHBOARD-BACKEND)

## Why This Order Matters

Running alphabetically would attempt tickets before their dependencies are in place.
Re-run `/implement-epic` with the same folder after any gate failure — already-done
tickets are skipped automatically.

## Note on the companion instrumentation-gap ticket

`TCK-20260716-AGENTOPS-DASHBOARD-BACKEND`'s own scope does not depend on
`docs/plans/agent_ops_dashboard/idea_agent_monitoring_live_phase_label.md`'s fix — that fix,
once ticketed, runs as fully independent, parallel work (decided 2026-07-16), not sequenced
into this batch at all.
