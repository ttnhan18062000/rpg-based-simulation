---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260520-SIM-OBS-M35
artifact_type: test_plan
tags: [sim, obs, m35]
---

# Test Plan: ClickHouse Event Warehouse (Milestone 35)

We will verify both abstract mapping logic (via mock tests) and physical data mutations (via containerized integration tests).

---

## 1. Test Taxonomy

### A. Unit Tests (Strict Isolation)
*   **Location**: `tests/unit/observability/test_clickhouse_record_mapping.py`
*   **Objective**: Test mapping of record lists into ClickHouse-compatible insertion payloads. Verify schema validations and database-independent conversions.

### B. Integration Tests (Physical DB Validation)
*   **Location**: `tests/integration/observability/test_clickhouse_ingestion.py` and `tests/integration/observability/test_clickhouse_queries.py`
*   **Objective**: Verify table generation, batch insertion, checksum-based idempotency, and analytical queries.
*   **Handling Offline State**:
    If a local ClickHouse container is not reachable, these integration tests will automatically skip cleanly (`pytest.skip("ClickHouse server is unreachable")`) to guarantee CI pipeline robustness.

---

## 2. Specific Test Scenarios

1.  **Schema Creation**: Verify table layout matches expected types (e.g. `String`, `UInt32`, `Float32`, `Nullable(String)`).
2.  **Bulk Ingestion**: Verify bulk inserting 100 simulation events completes without timeouts or syntax errors.
3.  **Idempotency Skipping**: Ingest same run twice; verify the second attempt skips successfully with `SKIPPED` status.
4.  **Idempotency Forced Update**: Ingest run, change artifact manifest, attempt ingestion (expects rejection), re-run with `--force` (expects successful re-insertion).
5.  **Worst Runs Query**: Insert three runs with health scores of 100.0, 45.0, and 72.0; query worst runs and assert the sorted result sequence.
6.  **Entity Events Query**: Insert events containing target `entity_id`; query and verify sequence ordering.
