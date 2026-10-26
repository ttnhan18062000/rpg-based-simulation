---
status: historical
layer: platform
authority: P1
audience: agent
ticket_id: TCK-20261018-AI-WORKER-SCRAPE-AND-LAG-ALERT
phase: done
date: 2026-10-18
tags: [platform, observability]
---

# TCK-20261018-AI-WORKER-SCRAPE-AND-LAG-ALERT

## Title
Prometheus scrape of ai_worker:9108, an ai_worker healthcheck on its up gauge, and an alert on stream consumer lag/pending

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P3

## Request Summary
#541 item 2 and carry-in 2 on #618. rpg's `TCK-20261014-AI-WORKER-EXPOSES-STREAM-CONSUMER-LAG-AND-PENDING-METRICS`
(PR #645, **on main** since 2026-10-24; was on rpg branches on 2026-10-18) serves:
- `sim_stream_consumer_lag{stream,group}` and `sim_stream_pending_messages{stream,group}`;
- `sim_stream_consumer_up` (1/0);

on `ai_worker:9108/metrics`, via env `AI_WORKER_METRICS_PORT` and `expose` only. Platform owns the scrape job and
the alert.

## Scope
- `docker/prometheus.yml`: job `ai_worker`, target `ai_worker:9108`. If `--scale ai_worker=N` must be scraped per
  replica, use `dns_sd_configs` on `tasks.ai_worker` or the compose DNS name; check which one works with Compose v5.
- An ai_worker healthcheck in `compose.yaml` that reads `sim_stream_consumer_up` from `localhost:9108`. Remove the
  "no healthcheck" comment.
- An alert rule next to the SLO rule:
  - lag or pending above a threshold for N minutes;
  - the threshold comes from a short observation under the step-3 load, not a guess.

  A runbook section in `docs/runbooks/` too.
- Panels for lag and pending, added to the API dashboard or to a small worker row.

## Out of Scope
- The gauges and the port (rpg). A dead-letter stream (owner: not now).

## Acceptance Criteria
- The `ai_worker` target is `up`, and its healthcheck goes `healthy` (**running locally**).
- Stopping ai_worker while the engine publishes makes the lag/pending alert fire to ntfy, and it resolves after the
  restart, with timestamps.

## Related Tickets
Epic `TCK-20261018-EPIC-DEVOPS-STEP3-OPERATE-LOCAL`. Was blocked on rpg's ai_worker metrics reaching main; unblocked by #645. Dispatched by platform-planner 2026-10-26 (#715). If lead picks signal B for `TCK-20261018-REDIS-DOWN-CAUSE-ALERT`, the two
merge.

## Related Docs
`docs/architecture/devops_baseline_adr.md` (D5); `docs/runbooks/ai-worker-lag.md`, `docs/runbooks/README.md`, `docs/runbooks/target-down.md`

## Related Stored Artifacts
None.

## Related Code Areas
`docker/prometheus.yml`, `compose.yaml`, `docker/grafana/provisioning/alerting/`, `docs/runbooks/`

## Assumptions / Open Questions
- This ticket may stay open in the folder when the step-3 PR lands. The epic doesn't wait for it.

## Implementation Notes
Scrape job via `dns_sd_configs`; healthcheck with python urllib; `rules-worker.yaml` (AiWorkerLagHigh noData Alerting, AiWorkerPendingHigh noData OK; no comparison in PromQL, threshold in step C); two dashboard panels; runbook `ai-worker-lag.md`. `stack_guard.sh` gained an optional `MAX_SWAP_GROWTH_MIB` trigger (default off).

## Test Summary
Live run 2026-10-26 (record: `docs/runbooks/records/2026-10-26-ai-worker-lag-alert.md`): target up and container healthy; `--scale ai_worker=2` showed 2 targets up (targets and health only); thresholds lag > 500, pending > 100 from the observation (normal peak lag 7, pending 9; stream trims at 1000); stop at 16:58:00Z, ntfy firing 17:01:00Z, restart 17:01:11Z, ntfy resolved 17:06:00Z; idle worker still serves lag 0; fresh start Normal. Pending above 100 was not provoked. tests/static and repo-root allowlist: 146 passed. Host peaks: MemAvailable low 5237 MiB, swap high 1947 MiB.

## Files Changed
`compose.yaml`, `docker/prometheus.yml`, `docker/grafana/provisioning/alerting/rules-worker.yaml`, `docker/grafana/dashboards/simulation.json`, `docs/runbooks/ai-worker-lag.md`, `docs/runbooks/README.md`, `docs/runbooks/target-down.md` `docs/runbooks/records/2026-10-26-ai-worker-lag-alert.md`, `tools/loadtest/stack_guard.sh`.

## Completion Summary
ai_worker is scraped (per replica), has a healthcheck, and two cause alerts with thresholds from a measured run; the stop/restart fire test reached ntfy and resolved, with timestamps in the record. Gap stated: pending above 100 and the Redis-down NoData path were not provoked.
