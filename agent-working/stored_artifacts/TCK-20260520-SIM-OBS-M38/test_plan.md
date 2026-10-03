---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260520-SIM-OBS-M38
artifact_type: test_plan
tags: [sim, obs, m38]
---

# Test Plan — Historical Event Search API (Milestone 38)

To guarantee reliability, performance, and security across both Local Fallback and ClickHouse backends, we will implement a multi-tiered test suite.

---

## 1. Unit Testing

We will implement `tests/unit/observability/test_historical_search_service.py` to cover:
- **Input Validation & Security**:
  - Assert that malicious strings containing path traversal sequences (e.g., `../`, `..\\`, `/etc/passwd`) are rejected with `ValueError`.
  - Assert that tick ranges (`tick_start > tick_end`) are rejected clearly.
- **Local Fallback Querying**:
  - Generate fake run directories with mock manifest, event logs, metric logs, and anomaly JSON files.
  - Test `query_runs` with filters (`scenario_name`, `status`), sorting, and pagination.
  - Test `query_events` filtering by tick ranges, entity IDs, severities, and pagination.
  - Test `query_anomalies` filtering by rule IDs.
  - Test `query_metric_windows` parsing and returning metric window structures.

---

## 2. Integration Testing

We will implement `tests/api/test_historical_event_search_api.py` to cover the FastAPI search routes:
- **Server Mount Verification**: Confirm the new search router is correctly registered under the application server.
- **FastAPI Endpoints**:
  - `GET /api/v1/observability/search/runs`: Test querying runs, sorting by health, and validating schema structures.
  - `GET /api/v1/observability/search/events`: Querying events, filtering by entity, tick bounds, and validating pagination response envelopes.
  - `GET /api/v1/observability/search/anomalies`: Querying rules, and validating payload structures.
  - `GET /api/v1/observability/search/entity-timeline`: Verifying timelines.
  - `GET /api/v1/observability/search/metric-trend`: Verifying trends.
- **Backend Swapping**:
  - Verify that when `SIM_WAREHOUSE_BACKEND=clickhouse` is configured but ClickHouse is disconnected, the endpoints degrade or handle the exception cleanly.
  - Verify that when `SIM_WAREHOUSE_BACKEND=local`, all queries execute successfully on file-based JSONL records.

---

## 3. Regression Safeguards
- Ensure all 125 existing observability module unit tests continue to pass with 100% success rate.
