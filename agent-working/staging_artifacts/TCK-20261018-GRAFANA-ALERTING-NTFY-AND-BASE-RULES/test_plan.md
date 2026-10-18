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

## Live-check rows (added at planner review; proven in the single stack run)
| # | check | oracle | expected |
|---|---|---|---|
| L1 | `$$labels` is an escape, not a literal | one firing ntfy message | the summary shows the job name, not `$labels` or `$$labels` |
| L2 | `$__file{}` expands inside nested `payload.vars.topic` and `authorization_credentials` | `GET /api/v1/provisioning/contact-points` | the token shows as redacted or set, never the literal `$__file{...}`; the token itself is never printed |
| L3 | the `coll.Dict` / `data.ToJSON` template makes valid ntfy JSON | the message arrives | title, priority and tags are present |
| L4 | `grafana_alerting_notifications_failed_total` exists | Grafana `/metrics` | present; otherwise fix the rule |
| L5 | node-exporter mountpoints read `/` and `/data` with no `/host` prefix | `node_filesystem_avail_bytes` series labels | both mounts present, so the disk regex matches |
