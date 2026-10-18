---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20261018-API-RECORDS-REQUEST-DURATION-BY-ROUTE-TEMPLATE
phase: done
date: 2026-10-18
tags: []
---

# TCK-20261018-API-RECORDS-REQUEST-DURATION-BY-ROUTE-TEMPLATE

## Title
The API records a request-duration histogram labelled by method, route template and status class (issue #622, R2).

## Status
DONE

## Tier
hotfix

## Type
feature

## Priority
P1

## Request Summary
There are no HTTP request metrics, so no API dashboard or latency SLO. Add http_request_duration_seconds to the manager's metrics registry with bounded labels.

## Scope
- New src/api/http_metrics.py (HttpRequestMetrics, a pure ASGI RequestDurationMiddleware that records into the active histogram); the manager registers the histogram on its registry and activates it in start() / deactivates it in stop(); create_v2_app adds the middleware (outermost); tests.

## Out of Scope
- The metrics port (R1, its own branch), OTel (R3), websocket timing, dashboards.

## Acceptance Criteria
- Labels are method (fixed set, else OTHER), route template (matched route path, never the raw path), status_class (1xx..5xx). A parameterised path is one series; an unmatched route gets the fixed label "unmatched"; many distinct raw paths do not grow the series count; a request never fails because of metrics.

## Related Tickets
- Issue #622 (R2), TCK-20261018-BACKEND-SERVES-ITS-METRICS-REGISTRY-ON-INTERNAL-PORT-9109 (R1)

## Related Docs
- None.

## Related Stored Artifacts
- None (hotfix).

## Related Code Areas
- src/api/http_metrics.py, src/api/engine_manager.py, src/api/server.py

## Assumptions / Open Questions
- The histogram is on the manager's registry: visible on /metrics (API key) and, once R1 lands, on port 9109. Buckets 5 ms to 10 s are a first guess for platform to tune.
- A mounted sub-app would label by its mount prefix (still bounded).

## Implementation Notes
No engine imports. Websocket scopes pass through untimed.

## Test Summary
tests/unit/api/test_http_metrics.py (6) and tests/api/test_request_duration_histogram.py (1) pass; tests/unit/api + tests/api: 234 passed; tests/unit/observability: all pass except test_event_stream_adapters::test_redis_adapter_resilient_missing_library, which fails identically on rpg-next b23e78128 (pre-existing, unrelated); code-health 0 new / 0 worse; lint-imports 17 kept, 0 broken.

## Files Changed
src/api/http_metrics.py (new), src/api/engine_manager.py, src/api/server.py, tests/unit/api/test_http_metrics.py (new), tests/api/test_request_duration_histogram.py (new).

## Completion Summary
Done, local branch rpg-request-histogram.
