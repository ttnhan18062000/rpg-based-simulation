---
status: historical
layer: misc
authority: P1
audience: agent
ticket_id: TCK-20260405-PROD-STACK-STABILIZE
phase: done
date: 2026-04-05
tags: [prod, stack, stabilize]
---

# TCK-20260405-PROD-STACK-STABILIZE: E2E Production Stack Stabilization

## Description
The `tests/e2e/test_production_stack.py` which verifies the full Docker-Compose stack (Backend, Loki, Prometheus, Grafana, Redis, RabbitMQ, Kafka) is currently entirely commented out. The simulation stabilization mission is not complete until the end-to-end telemetry and infrastructure ingestion is verified.

## Scope
- Uncomment and restore `tests/e2e/test_production_stack.py` tests.
- Resolve any regressions in Loki ingestion, Prometheus scraping, or Backend status.
- Ensure the production stack is isolated and stable for E2E runs.
- Harden the `engine_stack` fixture in `conftest.py`.

## Acceptance Criteria
- [x] `tests/e2e/test_production_stack.py` passes 100%.
- [x] Loki ingestion verified with trace-backed logs.
- [x] Prometheus metrics verified with simulation gauges.
- [x] No residual containers or volumes left after cleanup.

## Completion Notes
- **ActionSystem Fix**: Restored missing `_update_combat_visualization` method that was accidentally removed during RPG logic audit.
- **EventPresenter Fix**: Handled `SimEvent` object serialization for compact WebSocket/Kafka payloads.
- **Infrastructure Hardening**: Increased RabbitMQ/Kafka healthcheck tolerances in `docker-compose.yml` to prevent premature failures on slow test environments.
- **Verified**: 5/5 E2E tests passed in production-grade stack.

## Status
DONE

**Tier:** standard
**Type:** chore
**Priority:** P1
