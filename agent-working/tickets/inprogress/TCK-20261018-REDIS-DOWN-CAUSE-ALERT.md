---
status: active
layer: platform
authority: P1
audience: agent
ticket_id: TCK-20261018-REDIS-DOWN-CAUSE-ALERT
phase: inprogress
date: 2026-10-18
tags: [platform, observability]
---

# TCK-20261018-REDIS-DOWN-CAUSE-ALERT

## Title
A Redis-down cause alert, so the Redis-stop drill has something that fires when the API SLO stays green

## Status
INPROGRESS

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
**Decided by lead review, 2026-10-18: option A** (redis_exporter, `redis_up == 0`). B and C are kept below as the record of what was weighed; rpg is not asked for R4. Label the alert and its runbook section "cause alert, added 2026-10-18 by lead review", never as the step-3 SLO alert.
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
- Signal A chosen by lead review (2026-10-18). Lead confirmed a cause alert beside the one SLO alert is in scope:
  it is what makes the drill meaningful. Lead tells the owner.

## Implementation Notes
- Option A (lead review, 2026-10-18): `redis-exporter` service in `compose.yaml`: `oliver006/redis_exporter:v1.93.0@sha256:6ca518a7...` (2026-10-01, over two weeks old; v1.94.0 from 10-15 is too new; scratch image, about 4.5 MB compressed), observability profile, `--redis.addr=redis://redis:6379`, no host port, no shell so no healthcheck (`up{job="redis"}` is the probe), `mem_limit: 32m` as a PLACEHOLDER until the peak is measured.
- Redis 8 compatibility: the exporter README says "Valkey 7.x, 8.x, 9.x (and Redis)" and never names Redis 8, but main's image is `redis:8.10.2-alpine`; this is not confirmed by the docs and is proven or refuted by the live run (`redis_up == 1` and the INFO metrics). A failure there means stop and report.
- `docker/prometheus.yml`: job `redis` -> `redis-exporter:9121`.
- `docker/grafana/provisioning/alerting/rules-redis.yaml`: group `cause` (folder "Cause alerts", interval 30s), rule `RedisDown`: `redis_up == 0`, `for: 30s`, noData/execErr OK, labelled a cause alert in its summary and labels (`alert_kind: cause`), runbook_url `docs/runbooks/redis-down.md`. It uses S4's contact point and policy.
- `docs/runbooks/redis-down.md` + a README row; the runbook states the drill hypotheses as hypotheses.

## Test Summary
- **validated:** YAML parse of `rules-redis.yaml`; `docker compose --profile observability config -q`; `promtool check config` (with the `redis` job): SUCCESS; frontmatter of the new runbook and README.
- Not yet run (needs the exporter pull and the stack run): `redis_up == 1` on Redis 8.10.2, the `redis` target `up`, the exporter's peak memory, the alert firing within its `for` window and resolving, with timestamps (the drill ticket records them).

## Files Changed
(open)

## Completion Summary
(open)
