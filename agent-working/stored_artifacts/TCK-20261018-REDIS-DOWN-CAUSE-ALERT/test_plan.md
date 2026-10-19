---
status: historical
layer: platform
authority: P2
audience: agent
ticket_id: TCK-20261018-REDIS-DOWN-CAUSE-ALERT
artifact_type: test_plan
tags: [platform, observability]
---

# Test plan: TCK-20261018-REDIS-DOWN-CAUSE-ALERT

Written by platform-planner at dispatch (2026-10-19); the implementer updates it as the work changes.

## Proof Plan
| criterion | level | proof kind | oracle source | expected effect | selected commands |
|---|---|---|---|---|---|
| exporter supports Redis 8.10.2 | static | release notes | redis_exporter project | supported, cited | investigation.md |
| config valid | static | config checks | compose + promtool | exit 0 / SUCCESS | `compose config -q`; `promtool check config` |
| target up, redis_up 1 | running locally | Prometheus API | Prometheus | `up{job="redis"} == 1`, `redis_up == 1` | Prometheus query in slot (b) |
| RedisDown fires | running locally | the drill (slot c) | Grafana + ntfy | firing within 30s + eval + group wait; resolved after start | drill record |
| fits the host | running locally | docker stats | measured | RSS recorded, limit from it | `docker stats --no-stream` |

## Results (2026-10-19)
- Redis 8.10.2 works with redis_exporter v1.93.0 (`redis_up == 1`); RedisDown fired 81 s after `docker compose stop redis` (ntfy 17:52:50Z) and resolved 3 m 19 s after the restart (ntfy 17:57:50Z). The runbook is `docs/runbooks/redis-down.md`; the drill record is `docs/runbooks/records/2026-10-19-redis-stop-drill-under-load.md`.
