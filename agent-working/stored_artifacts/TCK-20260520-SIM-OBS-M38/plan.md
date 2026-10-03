---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260520-SIM-OBS-M38
artifact_type: plan
tags: [sim, obs, m38]
---

# Implementation Plan — Historical Event Search API (Milestone 38)

## 1. Schema & Interfaces

### 1.1 Base Interface Extension
We will extend `WarehouseAdapter` in `src/observability/warehouse/base.py` to include:
- `query_metric_windows(filters: Dict[str, Any]) -> List[MetricWindowRecord]`
- `query_violations(filters: Dict[str, Any]) -> List[HardLawViolationRecord]`

### 1.2 models.py Extension
We will confirm that `models.py` has all required fields for `RunRecord`, `SweepRecord`, `EventRecord`, `MetricWindowRecord`, `AnomalyRecord`, and `HardLawViolationRecord` with robust JSON/dict serialization.

---

## 2. In-Memory Local fallbacks

Inside `LocalWarehouseAdapter` (`src/observability/warehouse/adapters.py`), we will implement:
- `query_runs`:
  - Scan directories in `data/runs/`.
  - Read each manifest.json, validate it, map it to `RunRecord`.
  - Filter by `scenario_name` or `status` if provided.
  - Sort by health score or run ID.
  - Paginate using `limit` and `offset`.
- `query_events`:
  - Enforce `run_id` check (sanitize to block path traversal).
  - Open `simulation_events.jsonl` under `data/runs/{run_id}/`.
  - Read line-by-line, parse, filter by `entity_id`, `tick_start`, `tick_end`, `severity`.
  - Sort by tick asc.
  - Paginate.
- `query_anomalies`:
  - Enforce `run_id` check (sanitize).
  - Read `anomalies.json` under `data/runs/{run_id}/`.
  - Filter by `rule_id`.
  - Paginate.
- `query_metric_windows`:
  - Enforce `run_id` check.
  - Read `metric_windows.jsonl` if it exists.
  - Parse and return.
- `query_violations`:
  - Enforce `run_id` check.
  - Read `hard_law_violations.jsonl`.
  - Filter by `violation_type` or actor/target.

---

## 3. ClickHouse Queries Extension

Inside `ClickHouseWarehouseAdapter` (`src/observability/warehouse/clickhouse.py`), we will implement:
- `query_metric_windows`: Query from ClickHouse's `metric_windows` table.
- `query_violations`: Query from ClickHouse's `hard_law_violations` table.

---

## 4. FastAPI Search Endpoints

We will create a new FastAPI router file `src/api/routes/search.py` containing the 5 specified endpoints:
- `GET /api/v1/observability/search/runs`: Query historical runs using the active warehouse adapter.
- `GET /api/v1/observability/search/events`: Query events with pagination and filters.
- `GET /api/v1/observability/search/anomalies`: Query anomalies.
- `GET /api/v1/observability/search/entity-timeline`:
  - Combine events and anomalies filtered by a specific `entity_id` across a `run_id`.
  - Sort chronologically by tick and timestamp.
- `GET /api/v1/observability/search/metric-trend`:
  - Retrieve and return metric trend data (ticks completed, compute avg, memory RSS avg, and gold totals) for a given run.

---

## 5. Security & Input Sanitization
All ID filters must be passed through a strict sanitization function checking regex `^[a-zA-Z0-9_\-]+$`. Any invalid input will raise `HTTPException(400)`.

---

## 6. Audit Logging
We will log each incoming search query (endpoint, filters, count of results) at the `INFO` level using the system logger:
```python
logger.info("Observability query executed: search_type=%s scenario_name=%s severity=%s count=%d", search_type, scenario_name, severity, count)
```
This avoids Prometheus or Loki label explosion.
