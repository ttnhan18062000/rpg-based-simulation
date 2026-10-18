---
status: active
layer: platform
authority: P2
audience: agent
ticket_id: TCK-20261018-BASE-ALERT-SCRAPES-AND-NODE-EXPORTER
artifact_type: investigation
tags: [platform, observability]
---

# Investigation: TCK-20261018-BASE-ALERT-SCRAPES-AND-NODE-EXPORTER

Written by platform-planner at filing (2026-10-18); the implementer updates it as the work changes.

## Findings at filing
- `docker/prometheus.yml` on main (760f5ac9d) has one job, `rpg-backend` -> `backend:8000`, which answers 401 because
  `/metrics` sits behind `require_admission` (#618 carry-in 1). A target-down rule would fire on it permanently.
- Datasource uids are `prometheus`, `loki`, `tempo` (`docker/grafana/provisioning/datasources/datasource.yml`).
- Service ports on main: loki 3100, tempo 3200, grafana 3000, prometheus 9090.
- Host disks: `/` and `/data`, both ~70 % used (2026-10-18).

## To confirm during the work
- node-exporter's current release and digest; the flag names for rootfs and filesystem exclusion in that release.
- Grafana 13.2.4 serves `/metrics` unauthenticated by default.
