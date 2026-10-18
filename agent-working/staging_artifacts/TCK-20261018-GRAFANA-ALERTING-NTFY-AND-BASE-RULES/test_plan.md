---
status: active
layer: platform
authority: P2
audience: agent
ticket_id: TCK-20261018-GRAFANA-ALERTING-NTFY-AND-BASE-RULES
artifact_type: test_plan
tags: [platform, observability]
---

# Test plan: TCK-20261018-GRAFANA-ALERTING-NTFY-AND-BASE-RULES

Written by platform-planner at filing (2026-10-18); the implementer updates it as the work changes.

## Proof Plan
| criterion | level | proof kind | oracle source | expected effect | selected commands |
|---|---|---|---|---|---|
| provisioning loads cleanly | running locally | Grafana log + UI/API | Grafana's provisioning loader | no provisioning error; rules, contact point, policy listed as provisioned | `docker compose logs grafana \| grep -i -E "provision\|alerting"`; `GET /api/v1/provisioning/alert-rules` |
| contact point delivers to ntfy | running locally | test notification | ntfy topic history | message received with title and runbook link | Grafana "test" on the contact point or the provisioning API; `curl -s localhost:<ntfy>/<topic>/json?poll=1` |
| topic never in git | static | grep + check-ignore | none: criterion from the ticket AC | no match; file ignored | `git grep -n <local topic>`; `git check-ignore -v docker/secrets/<file>` |
| empty-topic guard | running locally | start with an empty secret | the guard's message | grafana refuses to start, clear message | one short start with an empty file (ask first) or reuse the folder's stack run |
| compose valid, ntfy on 127.0.0.1 | static | config check | none | exit 0; port bound to 127.0.0.1 | `docker compose --profile observability config` |

No `tests/**` changes (D-4).
