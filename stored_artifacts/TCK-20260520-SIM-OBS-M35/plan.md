---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260520-SIM-OBS-M35
artifact_type: plan
tags: [sim, obs, m35]
---

# Implementation Plan: ClickHouse Event Warehouse V1 (Milestone 35)

Introducing a production-grade external database adapter interface for ClickHouse event analytics, an automatic schema creation/verification manager, and new analytical query routes with idempotency gates.

---

## Proposed Changes

### Component 1: ClickHouse Configuration

#### [MODIFY] [config.py](file:///home/vboxuser/Work/rpg-based-simulation/src/observability/config.py)
*   Add configuration methods under `ObservabilityConfig`:
    *   `get_clickhouse_host() -> str`
    *   `get_clickhouse_port() -> int`
    *   `get_clickhouse_database() -> str`
    *   `get_clickhouse_username() -> str`
    *   `get_clickhouse_password() -> str`
    *   `get_clickhouse_secure() -> bool`
    *   `get_clickhouse_batch_size() -> int`
*   Allow environment variable overrides for each.

---

### Component 2: ClickHouse Adapter & Schema Manager

#### [NEW] [clickhouse.py](file:///home/vboxuser/Work/rpg-based-simulation/src/observability/warehouse/clickhouse.py)
*   Create a modular `ClickHouseWarehouseAdapter` subclassing `WarehouseAdapter`:
    *   Initializes `clickhouse_connect` client dynamically.
    *   Checks connectivity inside `health() -> WarehouseHealthStatus`.
    *   Creates tables automatically on initialization or via explicit schema manager call.
    *   Translates local run/sweep artifacts to record models, calculates checksums, and performs batch insertion.
    *   Ensures idempotency checks: check if `run_id` exists in clickhouse and compare `checksum` strings. If force is active, deletes old run data before insertion.
    *   Implements analytical queries (`query_runs`, `query_events`, `query_anomalies`).
*   Implement `ClickHouseSchemaManager` creating required tables with optimized column types:
    *   `runs`
    *   `sweeps`
    *   `simulation_events`
    *   `metric_windows`
    *   `anomalies`
    *   `hard_law_violations`
    *   `baselines`
    *   `comparison_results`

#### [MODIFY] [factory.py](file:///home/vboxuser/Work/rpg-based-simulation/src/observability/warehouse/factory.py)
*   Resolve `backend == "clickhouse"` to instantiate `ClickHouseWarehouseAdapter` dynamically.

---

### Component 3: CLI Subcommand Integration

#### [MODIFY] [entry.py](file:///home/vboxuser/Work/rpg-based-simulation/src/cli/entry.py)
*   Register new warehouse commands:
    *   `rpg-observe warehouse init` (Initialize schemas)
    *   `rpg-observe warehouse query worst-runs` (Fetch runs sorted by ascending health score)
    *   `rpg-observe warehouse query entity-events --entity-id <id>` (Fetch historical events for an entity)
*   Support `--force` options in `ingest-run` and `ingest-sweep` command pathways.

---

## Verification Plan

### Automated Tests
*   **Unit Mocks**: `tests/unit/observability/test_clickhouse_record_mapping.py`
    *   Verify clickhouse record parsing with mock client connection objects.
*   **Integration Tests**: `tests/integration/observability/test_clickhouse_ingestion.py`
    *   Verify schema generation, bulk insert, idempotency guards, and analytical queries.
    *   Skip tests gracefully if clickhouse server is not reachable.
