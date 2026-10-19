---
status: historical
layer: platform
authority: P2
audience: agent
ticket_id: TCK-20261018-REDIS-DOWN-CAUSE-ALERT
artifact_type: investigation
tags: [platform, observability]
---

# Investigation: TCK-20261018-REDIS-DOWN-CAUSE-ALERT

Written by platform-planner at dispatch (2026-10-19); the implementer updates it as the work changes.

## Findings at dispatch
- Lead review 2026-10-18 chose option A (redis_exporter, `redis_up == 0` for 30s).
- Redis image on main: `redis:8.10.2-alpine` (#646). redis-py 8 on the client side.
- #650 (u24 platform): the default stack publishes the event stream to Redis; the runbook states what that loses during
  an outage.
- Redis has no auth and binds its host port to 127.0.0.1 only (compose header).
