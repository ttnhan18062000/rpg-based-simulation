---
status: active
layer: platform
authority: P2
audience: agent
ticket_id: TCK-20261018-AI-WORKER-SCRAPE-AND-LAG-ALERT
artifact_type: plan
tags: [platform, observability]
---

# Plan: TCK-20261018-AI-WORKER-SCRAPE-AND-LAG-ALERT

1. `docker/prometheus.yml`: job `ai_worker`, `dns_sd_configs` on the compose name, port 9108, so every replica is scraped.
2. `compose.yaml`: ai_worker healthcheck with python urllib (no curl in the image) on `sim_stream_consumer_up 1.0`, `start_period` 15s.
3. `rules-worker.yaml`: `AiWorkerLagHigh` (noData Alerting: a stopped worker serves no series) and `AiWorkerPendingHigh` (noData OK); no comparison in PromQL, threshold in step C, set from the observation.
4. Dashboard: two panels (lag, pending) above the logs panel. Runbook `docs/runbooks/ai-worker-lag.md`, index rows, target-down job list.
5. Stack run (slot from platform-planner via lead): observe lag and pending under load, set thresholds; idle worker still serves lag 0; `--scale ai_worker=2` shows 2 targets up; fire test with timestamps. Record in `docs/runbooks/records/`.
6. Close the epic folder once this is done.
