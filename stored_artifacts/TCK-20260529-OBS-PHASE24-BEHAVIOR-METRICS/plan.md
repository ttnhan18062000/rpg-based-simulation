# Proposed Plan

Introduce BehaviorMetricWindow and BehaviorMetricsAggregator to summarize behavioral observations on a per-window tick interval.

## Design Decisions
1. Decoupled semantic layers. Avoid mixing with `MetricWindowRecord`.
2. Safe defaults when JSON or fields are missing.
