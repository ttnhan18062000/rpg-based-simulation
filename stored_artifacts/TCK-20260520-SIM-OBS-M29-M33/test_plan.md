---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260520-SIM-OBS-M29-M33
artifact_type: test_plan
tags: [sim, obs, m29, m33]
---

# Test Plan: Observability Event Streaming, Standalone Workers, Historical APIs, and Retention

This document lists the tests we will write and run to formally certify Milestones 29 through 33.

## 1. Unit Tests

### Milestone 29: Event Stream Adapters
- File: `tests/unit/observability/test_event_stream_adapter.py`
- Test cases:
  - Test `NullEventStreamAdapter` executes no-ops safely.
  - Test `InProcessEventStreamAdapter` successfully broadcasts to subscriber streams.
  - Test `RedisStreamAdapter` handles connection failure gracefully, returning connection state in `.health()`.

### Milestone 30: Standalone Worker
- File: `tests/unit/observability/test_external_anomaly_worker.py`
- Test cases:
  - Test that worker reads run `.jsonl` files, runs rule checks, and outputs `anomalies.json`.
  - Test that worker writes a valid `worker_status.json` and updates heartbeat time.

### Milestone 31: Historical Query API
- File: `tests/unit/observability/test_historical_query_service.py`
- Test cases:
  - Test `HistoricalRunQueryService` fetches list of past runs with pagination limits.
  - Test path traversal checks reject malicious run IDs.

### Milestone 32: Data Retention
- File: `tests/unit/observability/test_retention_policy.py`
- Test cases:
  - Test classifying recent vs old runs.
  - Test protecting failed or critical runs.
  - Test dry-run generates accurate plans.
  - Test explicit confirm deletes files, leaving baseline source runs.

### Milestone 33: Deployment Profiles
- File: `tests/unit/observability/test_deployment_profiles.py`
- Test cases:
  - Test resolving profiles (`local`, `ci`, `long_run`).
  - Test rejecting invalid profile names.

## 2. Integration / CLI Tests
- File: `tests/integration/observability/test_observability_scale_retention_flow.py`
- Test cases:
  - Test CLI routing for `rpg-observe worker analyze-run`.
  - Test CLI routing for `rpg-observe retention plan` and `rpg-observe retention clean --confirm`.
  - Test historical query API server responses over HTTP client.
