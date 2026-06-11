---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260520-SIM-OBS-M38
artifact_type: investigation
tags: [sim, obs, m38]
---

# Investigation — Historical Event Search API (Milestone 38)

## 1. Existing Query Architecture

The RPG simulation observability platform has two operational modes:
- **Production/Lab (ClickHouse)**: `ClickHouseWarehouseAdapter` provides high-performance telemetry aggregation, ordering, and batch insertions for `runs`, `sweeps`, `simulation_events`, `metric_windows`, `anomalies`, and `hard_law_violations`.
- **Local Developer/CI (Local JSONL/JSON Files)**: `LocalWarehouseAdapter` parses individual run/sweep directories for validation. However, its query methods (`query_runs`, `query_events`, `query_anomalies`) currently return empty lists (`[]`).

### Local Artifact Structure
For local runs, files are saved in `data/runs/{run_id}`:
- `run_manifest.json`: Single dict (schema `RunManifest`)
- `simulation_events.jsonl`: Line-delimited JSON simulation events
- `anomalies.json`: JSON list of anomalies
- `hard_law_violations.jsonl`: Line-delimited JSON violations
- `metric_windows.jsonl` / `run_report.json`: Metrics and reports

---

## 2. In-Memory Query Fallback for Local Adapter

To ensure developers can query run history and debug issues without maintaining a heavy ClickHouse instance, we will implement full local query capabilities inside `LocalWarehouseAdapter`:
- `query_runs`: Scan `data/runs/`, load each run's manifest, apply filter logic (e.g., status, scenario name), sort by health score or ID, and paginate.
- `query_events`: Locate `simulation_events.jsonl` for a given `run_id`, read line-by-line, extract fields (entity_id, tick range, severity), filter matching records, and paginate.
- `query_anomalies`: Resolve `anomalies.json` for a given `run_id`, load lists, filter by rule_id, and paginate.
- `query_metric_windows`: We will also need to support reading metric windows to support the `/observability/search/metric-trend` API. Let's define `query_metric_windows` on `WarehouseAdapter` if needed, or query it directly.

Wait, is there an existing `query_metric_windows` method on `WarehouseAdapter`?
Let's check `base.py`:
```python
    @abstractmethod
    def query_runs(self, filters: Dict[str, Any]) -> List[RunRecord]:
        pass

    @abstractmethod
    def query_events(self, filters: Dict[str, Any]) -> List[EventRecord]:
        pass

    @abstractmethod
    def query_anomalies(self, filters: Dict[str, Any]) -> List[AnomalyRecord]:
        pass
```
It doesn't define `query_metric_windows` or `query_violations` yet! We should add them to `WarehouseAdapter` so both ClickHouse and Local adapters implement them cleanly!
Yes, let's also define:
- `query_metric_windows(filters: Dict[str, Any]) -> List[MetricWindowRecord]`
- `query_violations(filters: Dict[str, Any]) -> List[HardLawViolationRecord]`

---

## 3. Threat Assessment & Path Traversal Mitigations
Any parameter passing `run_id` or `sweep_id` to filesystems must be strictly validated.
We will reuse the proven `sanitize_id` function from `src/observability/reporting/history_query.py` or build a local utility.
Alphanumeric validation using regex `^[a-zA-Z0-9_\-]+$` ensures absolutely no path traversal `../` is possible.
