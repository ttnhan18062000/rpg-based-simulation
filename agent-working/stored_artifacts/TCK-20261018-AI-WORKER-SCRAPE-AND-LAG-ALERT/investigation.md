---
status: active
layer: platform
authority: P2
audience: agent
ticket_id: TCK-20261018-AI-WORKER-SCRAPE-AND-LAG-ALERT
artifact_type: investigation
tags: [platform, observability]
---

# Investigation: TCK-20261018-AI-WORKER-SCRAPE-AND-LAG-ALERT

- Metrics source: `src/observability/stream/lag_metrics.py` (#645): `sim_stream_consumer_up`, `_lag`, `_pending_messages` per (stream, group); on a Redis error only `up 0` is yielded, no gauges.
- Conventions: `rules-base.yaml` LogShippingErrors (no comparison in PromQL when noData is Alerting), `rules-slo.yaml`, `rules-redis.yaml` (cause alerts, folder Cause alerts).
- The backend image has python but no curl or wget, hence the urllib healthcheck.
- Open facts to settle in the run: idle worker lag value, per-replica scrape, thresholds.
