---
status: archive
authority: P2
audience: historical
layer: observability
original_date: 2026-03-20
---

# Design Spec: Centralized Logging Aggregation with Grafana Loki

## Goal
Implement a production-grade, centralized logging system for the RPG simulation that aggregates logs from the Main Engine, API, and distributed AI Workers into a single searchable interface (Grafana).

## Architecture: Loki + Promtail
We will use **Approach A** (Sidecar/Agent-based ingestion):
1.  **Loki**: The storage engine. It indexes labels but stores original log lines as compressed targets.
2.  **Promtail**: An agent that runs as a container, reads Docker logs (via the JSON-file driver), and pushes them to Loki with metadata (container name, service type).
3.  **Structured JSON Logging**: The simulation will be updated to emit logs in JSON format instead of plain text, allowing Loki to parse fields like `entity_id` or `faction` automatically.

## Proposed Changes

### 1. Infrastructure (docker-compose.yml)
- **New Service: `loki`**: Basic single-binary configuration.
- **New Service: `promtail`**: Configured to scrape `/var/lib/docker/containers` (or equivalent) to harvest logs from the `backend` and `ai_worker` containers.

### 2. Python Logging (src/utils/logging.py)
- **`JsonFormatter`**: A custom formatter that converts `LogRecord` objects into JSON strings.
- **Context Injection**: Use `logging.LoggerAdapter` or a shared context filter to automatically include `tick`, `faction`, and `component` in log messages.

### 3. Grafana Integration
- **Loki Data Source**: Automatically provisioned to point to the `loki` service.
- **Log Panel**: A specialized panel in the dashboard to view and filter simulation events.

## Data Flow
`Simulation Component` -> `stdout (JSON)` -> `Docker Engine` -> `Promtail` -> `Loki` -> `Grafana`

## Verification Plan
1.  Verify `loki` and `promtail` containers are healthy.
2.  Run the simulation and check Grafana "Explore" view for incoming JSON logs.
3.  Verify that filtering by a custom field (e.g., `component="ai_worker"`) works in LogQL.

---
**Status**: Draft (Awaiting User Review)
