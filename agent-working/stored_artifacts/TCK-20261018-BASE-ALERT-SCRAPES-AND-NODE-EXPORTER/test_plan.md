---
status: historical
layer: platform
authority: P2
audience: agent
ticket_id: TCK-20261018-BASE-ALERT-SCRAPES-AND-NODE-EXPORTER
artifact_type: test_plan
tags: [platform, observability]
---

# Test plan: TCK-20261018-BASE-ALERT-SCRAPES-AND-NODE-EXPORTER

Written by platform-planner at filing (2026-10-18); the implementer updates it as the work changes.

## Proof Plan
| criterion | level | proof kind | oracle source | expected effect | selected commands |
|---|---|---|---|---|---|
| compose config valid | static | config check | none: criterion from the ticket AC | exit 0 | `docker compose --profile observability config -q` |
| Prometheus config valid | static | promtool from the pinned image | Prometheus' own validator | "SUCCESS" | `promtool check config` inside the pinned prometheus image |
| no backend:8000 target | static | grep | none: criterion from the ticket AC | no match | `grep -n "backend:8000" docker/prometheus.yml` |
| new jobs up, filesystem series present | running locally | targets page / API query | Prometheus API | all new jobs `up == 1`; `node_filesystem_avail_bytes` has `/` and `/data` | `curl -s localhost:9090/api/v1/query?query=up`; query `node_filesystem_avail_bytes{fstype!~"tmpfs|overlay"}` |
| node-exporter fits | running locally | `docker stats` | measured | RSS recorded, mem_limit set from it | `docker stats --no-stream` |

No `tests/**` changes (D-4: tests/** is rpg's).

## Results (2026-10-18)
- validated: `compose config -q` both profiles; YAML parse; `promtool check config` from the pinned image: SUCCESS.
- running locally (8-service subset, two runs): targets `prometheus`, `grafana`, `loki`, `tempo`, `node-exporter`, `ntfy` all `up`; `node_filesystem_avail_bytes` has `mountpoint="/"` and `"/data"` (no `/host` prefix); Grafana `/metrics` answers without auth; no job targets `backend:8000`.
- node-exporter measured peak 11.4 MiB; `mem_limit` set to 32m (about 3x headroom).
