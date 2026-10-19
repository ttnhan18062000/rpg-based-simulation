---
status: active
layer: platform
authority: P2
audience: agent
ticket_id: TCK-20261018-REDIS-STOP-DRILL-UNDER-LOAD
artifact_type: investigation
tags: [platform, observability]
---

# Investigation: TCK-20261018-REDIS-STOP-DRILL-UNDER-LOAD

Written by platform-planner at dispatch (2026-10-19); the implementer updates it as the work changes.

## Findings at dispatch
- Steady step below the knee: the aged curve (2026-10-18) gives p95 ~200 ms at 10 users, inside the SLO.
- The cause alert (`RedisDown`) is the expected detector; the SLO alert is expected to stay green.
- #650: the backend publishes the event stream to Redis; events published during the outage are expected to be lost.
