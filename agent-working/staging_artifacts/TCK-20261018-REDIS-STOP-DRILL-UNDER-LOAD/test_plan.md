---
status: active
layer: platform
authority: P2
audience: agent
ticket_id: TCK-20261018-REDIS-STOP-DRILL-UNDER-LOAD
artifact_type: test_plan
tags: [platform, observability]
---

# Test plan: TCK-20261018-REDIS-STOP-DRILL-UNDER-LOAD

Written by platform-planner at dispatch (2026-10-19); the implementer updates it as the work changes.

## Proof Plan
| criterion | level | proof kind | oracle source | expected effect | selected commands |
|---|---|---|---|---|---|
| timeline T0-T3 | running locally | drill script | timestamps | detection T1-T0 and recovery T3-T2 recorded | the script output |
| user impact | measured | Locust per-10s windows | Locust | error and latency during the outage recorded | Locust CSV |
| hypotheses | running locally | evidence per hypothesis | Locust, Loki, metrics | each confirmed or refuted with evidence | record |
| clean end | running locally | compose ps, alert states | compose + Grafana | all healthy, all rules Normal before down | `docker compose ps`; Grafana alert API |
