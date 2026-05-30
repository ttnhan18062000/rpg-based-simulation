# TCK-20260529-OBS-PHASE24-BEHAVIOR-METRICS

## Title

Semantic Behavior Metrics (Phase 24)

## Status

INPROGRESS

## Request Summary

Add semantic counters that explain entity behavior, entirely separate and decoupled from existing runtime/performance metrics.

## Scope

- Create a immutable versioned `BehaviorMetricWindow` dataclass
- Create `BehaviorMetricsAggregator` to count categories, families, route families, and activity in bounded tick windows
- Implement schema versioned `behavior_metric_windows.jsonl` post-run artifact support
- Keep behavior metrics strictly separated from existing `MetricWindowRecord`

## Out of Scope

- Live runtime database schema migrations (handled via dry-runs and versioned files)
- Episode detection (this is Phase 23)

## Acceptance Criteria

- Fully covered by unit, integration, and performance/artifact tests
- All tests pass cleanly under the `not slow` marker
- Documentation in `docs/entity/entity_base.md` updated with Section 35

## Related Tickets

- None

## Related Docs

- `docs/entity/entity_base.md`

## Related Stored Artifacts

- None

## Related Code Areas

- `src/observability/behavior/`
- `src/observability/warehouse/`

## Assumptions / Open Questions

- None

## Implementation Notes

- Aggregator counts categories using the `/` delimiter: `category/family`
- Integrates cleanly with subsequent episode detectors

## Test Summary

- Pending execution

## Files Changed

- Pending modification
