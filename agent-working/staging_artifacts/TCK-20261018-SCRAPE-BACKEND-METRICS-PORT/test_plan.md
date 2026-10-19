---
status: active
layer: platform
authority: P2
audience: agent
ticket_id: TCK-20261018-SCRAPE-BACKEND-METRICS-PORT
artifact_type: test_plan
tags: [platform, observability]
---

# Test plan: TCK-20261018-SCRAPE-BACKEND-METRICS-PORT

Written by platform-planner at dispatch (2026-10-19); the implementer updates it as the work changes.

## Proof Plan
| criterion | level | proof kind | oracle source | expected effect | selected commands |
|---|---|---|---|---|---|
| compose valid, no host port for 9109 | static | config check | none: ticket AC | exit 0; `9109` only under `expose` | `docker compose --profile observability config` |
| Prometheus config valid | static | promtool | Prometheus validator | SUCCESS | `promtool check config` in the pinned image |
| target up with series | running locally | Prometheus API | Prometheus | `up{job="rpg-backend"} == 1`; `sim_current_tick` and `http_request_duration_seconds_bucket` non-empty | `curl -s localhost:9090/api/v1/query?query=...` |
| public port still gated | running locally | curl | the API's admission | 401 | `curl -s -o /dev/null -w '%{http_code}' localhost:8000/metrics` |
| 9109 not on the host | running locally | curl | none | connection refused | `curl -s -m 3 localhost:9109/metrics` |
| simulation.json panel list | running locally | dashboard read | Grafana | list recorded in Test Summary | Grafana UI or API |
