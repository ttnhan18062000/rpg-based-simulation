# TCK-20260424-PH10-M3-INFRA-ISOLATION

## Title
Phase 10 Milestone 3: Infrastructure and Environment Precedence

## Status
DONE

## Request Summary
Recover environment flags, broker-disabled mode, and infrastructure-isolation behavior for the V2 engine.

## Scope
- [x] Task 1: Audit legacy environment-flag and disabled-mode rows against current `src_v2` infrastructure behavior.
- [x] Task 2: Recover supported environment-flag behavior and explicit disabled-mode semantics.
- [x] Task 3: Recover safe import-time and integration-time isolation behavior for optional infrastructure.
- [x] Task 4: Add direct compatibility tests for environment flags, disabled mode, and infra isolation.
- [x] Task 5: Publish the environment/disabled-mode/infrastructure-isolation contract.

## Out of Scope
- Observability (Logging/Metrics) parity (owned by M4).
- API/Protocol parity (owned by M5).

## Acceptance Criteria
- `BROKER_DISABLED=1` environment variable is respected.
- Engine imports safely even if RabbitMQ/Kafka libraries are missing or broker is down.
- Configuration precedence (YAML -> Env -> CLI) is enforced.
- Infrastructure compatibility contract is published.

## Related Tickets
- [TCK-20260424-PH10-M2-CLI-COMPAT](../done/TCK-20260424-PH10-M2-CLI-COMPAT.md)
