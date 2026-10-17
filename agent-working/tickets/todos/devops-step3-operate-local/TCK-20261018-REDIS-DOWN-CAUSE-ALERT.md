---
status: active
layer: platform
authority: P1
audience: agent
ticket_id: TCK-20261018-REDIS-DOWN-CAUSE-ALERT
phase: open
date: 2026-10-18
tags: [platform, observability]
---

# TCK-20261018-REDIS-DOWN-CAUSE-ALERT

## Title
A Redis-down cause alert, so the Redis-stop drill has something that fires when the API SLO stays green

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
The drill stops Redis under load. From a code read (2026-10-18), the API likely doesn't notice:
- `/health` reports engine liveness only;
- the Redis stream adapter publishes from a background queue with 1 s timeouts and drops events;
- the read routes don't use Redis.

Events still get lost (the anomaly stream, ai_worker input), and nothing alerts on that today. This ticket adds a
cause-side alert on the same ntfy contact point, with a runbook section.

## Scope
The signal is **pending lead-planner's choice** (platform-planner recommends option A):
- **A. `redis_exporter`** (`oliver006/redis_exporter`, pinned by digest, observability profile, `mem_limit`, no host
  port). Prometheus scrapes it; alert on `redis_up == 0` for 30 s.
  - Platform-only, no rpg dependency, a standard exporter.
  - Also gives Redis memory, clients and stream lengths for the dashboard and the runbook.
- **B. ai_worker's `sim_stream_consumer_up == 0`** (rpg's gauge, on rpg branches, not on main).
  - No new image; it shows the consumer's own view.
  - Waits for rpg-next. It merges with `TCK-20261018-AI-WORKER-SCRAPE-AND-LAG-ALERT`.
- **C. A backend stream-publish drop counter**: an rpg request (R4), exported on the 9109 registry. It shows the
  data loss directly, but needs another rpg change.

Common to all options:
- the alert rule is provisioned next to the SLO rule;
- the same contact point;
- `docs/runbooks/redis-down.md`: what is lost while Redis is down, what isn't (the API keeps serving), how to recover,
  and how to check the backlog after recovery.

## Out of Scope
- Any `src` change (options B and C are rpg's side). Redis HA, Sentinel, persistence tuning.

## Acceptance Criteria
- `docker compose stop redis` makes the alert fire within its `for:` window plus one evaluation interval, and the ntfy
  topic receives it. `docker compose start redis` resolves it. Timestamps are recorded (**running locally**).
- The runbook section exists and is linked from the alert message.
- With option A: the exporter is pinned, has a memory limit, has no host port, and the scrape target is `up`.

## Related Tickets
Epic `TCK-20261018-EPIC-DEVOPS-STEP3-OPERATE-LOCAL`. After `TCK-20261018-API-SLO-ALERT-NTFY-RUNBOOK` (the contact
point and the runbooks folder). Feeds `TCK-20261018-REDIS-STOP-DRILL-UNDER-LOAD`.

## Related Docs
`docs/architecture/devops_baseline_adr.md` (D5)

## Related Stored Artifacts
None.

## Related Code Areas
`compose.yaml`, `docker/prometheus.yml`, `docker/grafana/provisioning/alerting/`, `docs/runbooks/redis-down.md`

## Assumptions / Open Questions
- **Open: signal choice A/B/C (lead-planner).**
- The step brief says "one SLO alert". This is a cause alert, not an SLO. It is added only so the drill has a
  detection signal. Lead-planner confirms that this doesn't overstep the step.

## Implementation Notes
(open)

## Test Summary
(open)

## Files Changed
(open)

## Completion Summary
(open)
