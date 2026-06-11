---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260520-SIM-OBS-M35
artifact_type: investigation
tags: [sim, obs, m35]
---

# Investigation: ClickHouse Event Warehouse Integration (Milestone 35)

We investigated the target environment requirements and capabilities for implementing a production-grade external event warehouse using ClickHouse.

---

## 1. Local Environment Status

*   **Docker Compose**: Active (`Docker Compose version v5.1.1`).
*   **Python Virtual Environment**: Managed via `uv`. No global packages conflict with the virtual environment.
*   **ClickHouse Python Client**:
    Successfully installed `clickhouse-connect==1.0.1` and its dependent compressor libraries (`zstandard`, `lz4`) inside the virtual environment (`.venv`).
    Verified that `clickhouse-connect` imports cleanly into python.
*   **ClickHouse Server**:
    No ClickHouse docker container is currently running. We will launch a lightweight ClickHouse server container locally to certify integration behaviors.

---

## 2. Ingestion Idempotency Logic

We will establish a checksum-based system to satisfy the idempotency requirements:
1.  Read the local run's manifest JSON file.
2.  Compute a stable MD5 or SHA256 checksum of the manifest content.
3.  Store this `checksum` column inside the `runs` table.
4.  When ingesting a run:
    *   Query the ClickHouse database: `SELECT checksum FROM runs WHERE run_id = {run_id}`.
    *   If a row exists:
        *   If existing `checksum` equals new `checksum`, skip ingestion cleanly.
        *   If different, raise a validation error/reject the ingestion unless `force=True` is provided (which deletes the existing run data and re-ingests).
5.  This ensures perfect robustness against duplicate ingestion jobs.

---

## 3. Query Scenarios

The high-performance clickhouse adapter should support highly optimized SQL operations for key telemetry views:
*   **Worst Runs**:
    `SELECT run_id, scenario_name, health_score FROM runs ORDER BY health_score ASC LIMIT {limit}`
*   **Common Anomalies**:
    `SELECT rule_id, count() as cnt FROM anomalies GROUP BY rule_id ORDER BY cnt DESC`
*   **Entity Events**:
    `SELECT tick, event_type, event_category, severity, message, payload_json FROM simulation_events WHERE entity_id = {entity_id} ORDER BY tick ASC`
