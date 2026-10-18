---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20261018-BACKEND-SERVES-ITS-METRICS-REGISTRY-ON-INTERNAL-PORT-9109
phase: done
date: 2026-10-18
tags: []
---

# TCK-20261018-BACKEND-SERVES-ITS-METRICS-REGISTRY-ON-INTERNAL-PORT-9109

## Title
The backend serves its metrics registry on an internal, unauthenticated port 9109 (issue #622, R1).

## Status
DONE

## Tier
hotfix

## Type
feature

## Priority
P1

## Request Summary
Nothing can scrape backend metrics: /metrics on 8000 is behind the API key (401). Serve the same registry on a second port (9109, BACKEND_METRICS_PORT), the same pattern as ai_worker's 9108, for the compose network only.

## Scope
- New src/api/metrics_port.py (start_http_server on 0.0.0.0, never raises on a bind failure); started by V2EngineManager.start() from its own metrics_registry and stopped by stop() (so the API lifespan is untouched); tests.

## Out of Scope
- Compose and deploy files (platform's). R2 (histogram) and R3 (OTel). /metrics on 8000 is unchanged.

## Acceptance Criteria
- 9109 serves the registry without auth; /metrics on the API port still returns 401 without a key; the app mounts no route for the port (it belongs to the manager, not to a route); the port is released at shutdown; unbindable port does not stop the API.

## Related Tickets
- Issue #622 (R1), TCK-20261014-AI-WORKER-EXPOSES-STREAM-CONSUMER-LAG-AND-PENDING-METRICS

## Related Docs
- None.

## Related Stored Artifacts
- None (hotfix).

## Related Code Areas
- src/api/metrics_port.py, src/api/engine_manager.py (start/stop, metrics_port property)

## Assumptions / Open Questions
- Compose needs from platform: on the backend service add `expose: ["9109"]` (never under `ports:`); optionally `BACKEND_METRICS_PORT=9109` in its environment (9109 is the default); scrape target backend:9109/metrics. Not edited here.
- Under uvicorn with several workers only one process could bind the port; compose runs one worker.

## Implementation Notes
Mirrors src/observability/stream/lag_metrics.py. No engine imports.

## Test Summary
tests/unit/api/test_metrics_port.py (5) and tests/api/test_backend_metrics_port.py (2) pass; tests/unit/api, tests/api, tests/unit/observability: 1397 passed, 1 skipped; lint-imports 17 kept, 0 broken.

## Files Changed
src/api/metrics_port.py (new), src/api/engine_manager.py, tests/unit/api/test_metrics_port.py (new), tests/api/test_backend_metrics_port.py (new).

## Completion Summary
Done, local branch rpg-metrics-port.
