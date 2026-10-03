---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260520-SIM-OBS-M41
artifact_type: test_plan
tags: [sim, obs, m41]
---

# Test Plan — Milestone 41

## Tests
1. `tests/perf/test_production_observatory_overhead.py` — Observatory overhead measurement
2. `tests/integration/test_observatory_stream_outage.py` — Stream outage resilience 
3. `tests/integration/test_observatory_warehouse_outage.py` — Warehouse outage resilience
4. `tests/integration/test_anomaly_worker_failure.py` — Worker crash resilience

## Execution
```bash
python3 -m pytest tests/perf/test_production_observatory_overhead.py tests/integration/test_observatory_stream_outage.py tests/integration/test_observatory_warehouse_outage.py tests/integration/test_anomaly_worker_failure.py -v
```
