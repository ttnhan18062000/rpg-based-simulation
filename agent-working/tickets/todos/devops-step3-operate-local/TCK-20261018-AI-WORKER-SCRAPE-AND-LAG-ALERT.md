---
status: active
layer: platform
authority: P1
audience: agent
ticket_id: TCK-20261018-AI-WORKER-SCRAPE-AND-LAG-ALERT
phase: open
date: 2026-10-18
tags: [platform, observability]
---

# TCK-20261018-AI-WORKER-SCRAPE-AND-LAG-ALERT

## Title
Prometheus scrape of ai_worker:9108, an ai_worker healthcheck on its up gauge, and an alert on stream consumer lag/pending

## Status
BLOCKED

## Tier
standard

## Type
feature

## Priority
P3

## Request Summary
#541 item 2 and carry-in 2 on #618. rpg's `TCK-20261014-AI-WORKER-EXPOSES-STREAM-CONSUMER-LAG-AND-PENDING-METRICS`
(commit `ef014783b`, on rpg branches; **not on main** on 2026-10-18) serves:
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
Epic `TCK-20261018-EPIC-DEVOPS-STEP3-OPERATE-LOCAL`. **Blocked on** rpg's ai_worker metrics reaching main (via
rpg-next; lead-planner-u24 relays on #618). If lead picks signal B for `TCK-20261018-REDIS-DOWN-CAUSE-ALERT`, the two
merge.

## Related Docs
`docs/architecture/devops_baseline_adr.md` (D5)

## Related Stored Artifacts
None.

## Related Code Areas
`docker/prometheus.yml`, `compose.yaml`, `docker/grafana/provisioning/alerting/`, `docs/runbooks/`

## Assumptions / Open Questions
- This ticket may stay open in the folder when the step-3 PR lands. The epic doesn't wait for it.

## Implementation Notes
(open)

## Test Summary
(open)

## Files Changed
(open)

## Completion Summary
(open)
