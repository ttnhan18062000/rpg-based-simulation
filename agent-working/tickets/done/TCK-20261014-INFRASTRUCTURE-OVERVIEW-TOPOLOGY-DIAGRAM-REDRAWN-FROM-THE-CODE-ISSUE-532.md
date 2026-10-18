---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20261014-INFRASTRUCTURE-OVERVIEW-TOPOLOGY-DIAGRAM-REDRAWN-FROM-THE-CODE-ISSUE-532
phase: done
date: 2026-10-14
tags: []
---

# TCK-20261014-INFRASTRUCTURE-OVERVIEW-TOPOLOGY-DIAGRAM-REDRAWN-FROM-THE-CODE-ISSUE-532

## Title
Redraw the infrastructure overview topology (section 1) from the code, per issue #532.

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P3

## Request Summary
docs/engine/contracts/infrastructure_overview.md section 1 disagreed with the code: a src/workers/ pool that does not exist, Redis feeding Prometheus, Redis feeding a ClickHouse warehouse, and a watchdog under src/utils/.

## Scope
The section 1 diagram and the three stale facts in section 2 that repeat the same errors (the workers/ directory, the 6-phase kernel, apply_pipeline.py).

## Out of Scope
The rest of the document; the other stale statements are not re-audited here.

## Acceptance Criteria
Each node and edge in the diagram is checked against the code and consistent with docs/architecture/system_overview.md and docs/audits/D23_architecture_resilience.md section B.

## Related Tickets
GitHub issue #532; #533 (system_overview.md).

## Related Docs
docs/architecture/system_overview.md; docs/audits/D23_architecture_resilience.md.

## Related Stored Artifacts
None.

## Related Code Areas
compose.yaml; docker/prometheus config; src/observability/watchdog.py; src/observability/anomaly/worker.py; src/observability/analytics/; src/observability/warehouse/clickhouse.py; src/engine/phases.py; src/engine/pipeline.py.

## Assumptions / Open Questions
None.

## Implementation Notes
Checked against main: ai_worker runs python -m src.observability.anomaly.worker and consumes the Redis stream simulation:events; Prometheus scrapes backend:8000 (/metrics) and never reads Redis; analytics run on DuckDB (src/observability/analytics/query.py, mining/dataset.py) and a ClickHouse adapter exists (src/observability/warehouse/clickhouse.py) but is not in compose.yaml; the watchdog is src/observability/watchdog.py polling /health and /metrics and querying Loki; TickPhase has 7 phases; src/engine/apply_pipeline.py does not exist (pipeline.py and pipeline_phases/ do). No rabbitmq, kafka or zookeeper in compose.

## Test Summary
Docs only. The mermaid block was written against the checked facts above; not rendered here.

## Files Changed
docs/engine/contracts/infrastructure_overview.md.

## Completion Summary
Done.
