# Implementation Sequence — progress-timeline

Tickets must be implemented in this order. Generated automatically from intra-batch
dependency analysis. `implement-epic` reads this file to override alphabetical order.

## Order

1. TCK-20260720-BULK-RUN-TIMELINE  (no deps in this batch)
2. TCK-20260720-ECHARTS-PHASE-PALETTE  (no deps in this batch)
3. TCK-20260720-PROGRESS-TIMELINE-VIEW  (depends on: TCK-20260720-BULK-RUN-TIMELINE, TCK-20260720-ECHARTS-PHASE-PALETTE)
4. TCK-20260720-TIMELINE-RANGE-CONTROL  (depends on: TCK-20260720-BULK-RUN-TIMELINE, TCK-20260720-PROGRESS-TIMELINE-VIEW)

## Why This Order Matters

Running alphabetically would attempt tickets before their dependencies are in place.
Re-run `/implement-epic` with the same folder after any gate failure — already-done
tickets are skipped automatically.

## Known Gap

A 5th concern (C5: update `docs/guides/agent_ops_dashboard.md` and
`docs/observability/agent_ops_dashboard_contract.md` to describe the new Progress
Timeline view, the bulk endpoint, and the retirement of the Gantt-named components) was
extracted from the source proposal but its investigation agent failed due to a session
usage limit during this `create-tickets` run. It is deferred to a follow-up
`/create-tickets source=docs/plans/agent_ops_dashboard/proposal_progress_timeline.md`
run — the proposal document still contains it as concern 5. Every ticket in this batch's
Out of Scope section notes this gap explicitly.
