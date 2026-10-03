---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260520-SIM-OBS-M29-M33
artifact_type: investigation
tags: [sim, obs, m29, m33]
---

# Investigation: Observability Scaling & Retention Integration Points

This document records the results of code research and dependency evaluation for integrating Milestones 29 through 33 of Phase 6.

## 1. Event Streaming & EventRecorder
- `src/observability/event_recorder.py`:
  Currently uses:
  ```python
  from src.observability.live.event_publisher import LiveEventPublisher
  LiveEventPublisher.get_instance().publish(event)
  ```
  We will replace this call with a generic event stream adapter invocation:
  ```python
  from src.observability.stream.factory import get_event_stream_adapter
  adapter = get_event_stream_adapter()
  adapter.publish(event)
  ```

## 2. Configuration Resolvers
- `src/observability/config.py`:
  We will add additional methods to resolve environment configurations:
  ```python
  # Backend config
  SIM_STREAM_BACKEND = os.environ.get("SIM_STREAM_BACKEND", "in_process")
  SIM_REDIS_URL = os.environ.get("SIM_REDIS_URL", "redis://localhost:6379/0")
  SIM_STREAM_NAME = os.environ.get("SIM_STREAM_NAME", "simulation:events")
  ```

## 3. External Anomaly Worker
- The standalone worker needs to reuse:
  - `src/observability/anomaly/rule_engine.py`: Contains the `RuleEngine` class.
  - `src/observability/anomaly/analyzers.py` or similar analyzers.
  - `src/observability/reporting/artifact_repository.py`: For loading run data.
  We will implement this in `src/observability/anomaly/worker.py`.

## 4. Historical API Mounts
- `src/api/server.py` hosts the FastAPI server.
  We can create a clean FastAPI router in `src/api/routes/history.py` (or mount directly in `server.py` to keep it clean and robust).
  Let's check the current API endpoints in `src/api/server.py`.

## 5. File Cleanup Paths
- Stored run artifacts live under `data/runs/`.
  Each run contains:
  ```text
  simulation_events.jsonl
  metric_windows.jsonl
  hard_law_violations.jsonl
  anomalies.json
  run_report.json
  run_report.md
  run_manifest.json
  ```
  We will implement `RetentionManager` in `src/observability/reporting/retention.py` doing safe classified file purging.
