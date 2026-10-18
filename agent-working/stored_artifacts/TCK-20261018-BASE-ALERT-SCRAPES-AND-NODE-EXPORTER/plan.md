---
status: historical
layer: platform
authority: P2
audience: agent
ticket_id: TCK-20261018-BASE-ALERT-SCRAPES-AND-NODE-EXPORTER
artifact_type: plan
tags: [platform, observability]
---

# Plan: TCK-20261018-BASE-ALERT-SCRAPES-AND-NODE-EXPORTER

Written by platform-planner at filing (2026-10-18); the implementer updates it as the work changes.

## Steps
1. Edit `docker/prometheus.yml`: remove `rpg-backend`; add `prometheus`, `grafana`, `loki`, `tempo`, `node-exporter` jobs.
2. Add the `node-exporter` service to `compose.yaml` (pinned, mem_limit, read-only rootfs mount, no privileges, no ports).
3. Ask platform-planner for the pull (relayed to lead-planner), pull it alone.
4. `docker compose --profile observability config -q`; `promtool check config` via the pinned Prometheus image
   (`docker compose run --rm --entrypoint promtool prometheus check config /etc/prometheus/prometheus.yml` or equivalent).
5. The live check runs inside `TCK-20261018-BASE-ALERTS-RUNBOOKS-AND-DRILL`'s drill start if lead-planner prefers one stack run for the whole folder; otherwise
   one short start here (ask first).

## Scope guards
No `src/**`, no `tests/**`, no Alertmanager, no host network/PID/privileged for node-exporter.

## Update (implementer, 2026-10-18)
- Steps 1, 2 and 4 done (config checks green). Lead's notes: record node-exporter RSS before setting `mem_limit` (placeholder 64m now), confirm `/` and `/data` series. The pull (step 3) and the live check wait for platform-planner's relay; the single stack run covers C1's, C2's and C3's live checks.
- The `ntfy` scrape job moves to C2 (ntfy does not exist yet).
