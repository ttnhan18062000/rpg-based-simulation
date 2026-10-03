---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260529-OBS-PHASE24-BEHAVIOR-METRICS
artifact_type: plan
tags: [obs, phase24, behavior, metrics]
---

# Proposed Plan

Introduce BehaviorMetricWindow and BehaviorMetricsAggregator to summarize behavioral observations on a per-window tick interval.

## Design Decisions
1. Decoupled semantic layers. Avoid mixing with `MetricWindowRecord`.
2. Safe defaults when JSON or fields are missing.
