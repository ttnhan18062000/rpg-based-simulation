---
status: historical
layer: platform
authority: P2
audience: agent
ticket_id: TCK-20261018-REDIS-DOWN-CAUSE-ALERT
artifact_type: plan
tags: [platform, observability]
---

# Plan: TCK-20261018-REDIS-DOWN-CAUSE-ALERT

Written by platform-planner at dispatch (2026-10-19); the implementer updates it as the work changes.

## Steps
1. Investigation: confirm the redis_exporter release supports Redis 8.10.2 (main's image since #646); pick a release at
   least two weeks old; tag + digest; size.
2. `compose.yaml`: `redis-exporter` service, observability profile, pinned, `mem_limit`, no host port,
   `REDIS_ADDR=redis://redis:6379`. depends_on only if it does not pull extra services into a `--no-deps` start.
3. `docker/prometheus.yml`: job `redis` -> `redis-exporter:9121`.
4. `rules-cause.yaml` (or a rule in `rules-slo.yaml`'s file family): `RedisDown`, `redis_up == 0` for 30s, labelled
   "cause alert, added 2026-10-18 by lead review", runbook `docs/runbooks/redis-down.md`.
5. `docs/runbooks/redis-down.md` + README row: what is lost while Redis is down (the event stream published since #650),
   what isn't (the API keeps serving), recovery, backlog check.
6. Slot (a): the exporter pull, alone. Live check in slot (b); the real fire is the drill (slot c).

## Scope guards
No `src/**`. No host port. Note: TargetDown on the `redis` job only fires if the exporter is down; `RedisDown` covers
Redis itself.
