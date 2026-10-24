---
status: active
layer: architecture
authority: P1
audience: developer
---

# Persistent Simulation Watchdog

## Status
Active

## Context
The RPG simulation is a complex, distributed system with 11+ services. While one-off E2E tests provide initial confidence, we need a persistent way to detect failures (crashes, performance degradation, logic "fraud") during long-running production simulations.

The system already has:
- Structured JSON logging (Loki).
- Prometheus metrics.
- A REST API for health checks.

## Decision
We will implement a standalone **Simulation Watchdog** service (`src/observability/watchdog.py`).

### Key Responsibilities:
1.  **Metric Pulsing**: Periodically poll the backend's **internal metrics port** (`METRICS_URL`, default `http://backend:9109/metrics`, the same registry the API's `/metrics` serves, unauthenticated, compose network only: `src/api/metrics_port.py`) to ensure `sim_current_tick` is incrementing. `/metrics` on the API port is behind the API key and answers 401 to this poller, so it is not used. A 401/403 from the metrics endpoint means the watchdog is misconfigured and blind, not that the simulation stalled: it is reported as `Metrics gated (HTTP 401)`, is NOT counted toward `consecutive_failures`, and raises its own `WatchdogBlind` alert (severity ERROR, once per the router's dedup window, `SIM_ALERTS_DEDUP_WINDOW_SECONDS`, default 60 s). A refused connection, a timeout, any other non-200 status and a tick that does not advance stay failures.
2.  **Health Check**: Monitor the `/health` endpoint for 200 OK responses.
3.  **Log Aggregation**: Query Loki for `level="error"` or `level="critical"` across all container jobs.
4.  **Self-Correction/Alerting**: Emit a "SYSTEM_CRITICAL" log when a failure is detected, and
    route a `WatchdogTrip` `AlertEvent` through `AlertsManager`'s `AlertRouter`
    (`src/observability/alerts/`). The router always logs the alert (`LogAlertSink`) and
    additionally posts it to a webhook (`WebhookAlertSink`) **only if**
    `SIM_ALERTS_WEBHOOK_URL`/`SIM_ALERTS_WEBHOOK_ENABLED` are configured on the `watchdog`
    service (disabled by default in `compose.yaml`). No PagerDuty/Discord integration
    exists — the only real external sink type is a generic webhook POST, and it stays
    effectively log-only until an operator supplies those environment variables.

## Rationale
- **Decoupling**: A standalone service ensures that even if the Backend or AI Workers crash, the Monitor remains alive to report the failure.
- **Extensibility**: It allows for game-specific logic checks (e.g., "economy inflation detected") that are too complex for standard Prometheus Alertmanager rules.
- **Visibility**: By emitting its own logs back into Loki, the Watchdog becomes part of the unified observability stream.

## Trade-offs
- **Overhead**: Adds a new container to the stack.
- **Maintenance**: Requires updating if API endpoints or metric names change.

## Consequences
- **Positive**: Real-time visibility into system failures; significantly reduced Time-to-Detection (TTD).
- **Negative**: Adds 1-2% resource overhead for polling.
- **Mitigation**: Use long polling or reasonable intervals (5-10s) to minimize impact.

## Revisit Trigger
- If the simulation scales to 1,000+ workers, the polling overhead might become significant, requiring a push-based alerting system.
