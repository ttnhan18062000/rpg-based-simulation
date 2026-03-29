# ADR-004: Persistent Simulation Watchdog

## Status
Proposed

## Context
The RPG simulation is a complex, distributed system with 11+ services. While one-off E2E tests provide initial confidence, we need a persistent way to detect failures (crashes, performance degradation, logic "fraud") during long-running production simulations.

The system already has:
- Structured JSON logging (Loki).
- Prometheus metrics.
- A REST API for health checks.

## Decision
We will implement a standalone **Simulation Watchdog** service (`src/utils/watchdog.py`).

### Key Responsibilities:
1.  **Metric Pulsing**: Periodically poll the `/metrics` endpoint to ensure `sim_current_tick` is incrementing.
2.  **Health Check**: Monitor the `/health` endpoint for 200 OK responses.
3.  **Log Aggregation**: Query Loki for `level="error"` or `level="critical"` across all container jobs.
4.  **Self-Correction/Alerting**: Emit a "SYSTEM_CRITICAL" log when a failure is detected, which can trigger external alerts (PagerDuty, Discord, etc.).

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
