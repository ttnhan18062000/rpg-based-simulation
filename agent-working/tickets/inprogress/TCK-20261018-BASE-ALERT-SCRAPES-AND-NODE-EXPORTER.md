---
status: active
layer: platform
authority: P1
audience: agent
ticket_id: TCK-20261018-BASE-ALERT-SCRAPES-AND-NODE-EXPORTER
phase: inprogress
date: 2026-10-18
tags: [platform, observability]
---

# TCK-20261018-BASE-ALERT-SCRAPES-AND-NODE-EXPORTER

## Title
Prometheus: scrape the observability services and a new node-exporter; drop the always-401 backend:8000 job

## Status
INPROGRESS

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
S4's base alerts need series that exist today without rpg work. `docker/prometheus.yml` has one job, `rpg-backend` on
`backend:8000`, which returns 401 (admission-gated `/metrics`, carry-in 1 on #618). A target-down rule would fire on it
forever, so it goes. Disk alerts need host filesystem metrics, so a node-exporter joins the observability profile.

## Scope
- `docker/prometheus.yml`:
  - remove the `rpg-backend` `backend:8000` job (step-2 `TCK-20261018-SCRAPE-BACKEND-METRICS-PORT` adds `backend:9109`
    when rpg's R1 lands);
  - add jobs: `prometheus` (self), `grafana` (`grafana:3000/metrics`), `loki` (`loki:3100/metrics`), `tempo`
    (`tempo:3200/metrics`), `node-exporter`, and `ntfy` if `TCK-20261018-GRAFANA-ALERTING-NTFY-AND-BASE-RULES` enables its metrics (coordinate in order: add the job in
    `TCK-20261018-GRAFANA-ALERTING-NTFY-AND-BASE-RULES` if it isn't up yet).
  - Each job's `job` label is the name the runbooks use.
- `compose.yaml`: `node-exporter` service:
  - `profiles: ["observability"]`, image pinned by tag plus digest, a `mem_limit`;
  - read-only host mount `/:/host:ro,rslave` with `--path.rootfs=/host`; no `privileged`, no host network, no host PID;
    no host port (Prometheus reaches it by service name);
  - collectors limited to what the rules need if that is simple (filesystem, plus the defaults otherwise); exclude
    pseudo filesystems (tmpfs, overlay, squashfs) by flag.
- Check that Grafana exposes `/metrics` without auth in the pinned version (it does by default; record the check).

## Out of Scope
- Alert rules (`TCK-20261018-GRAFANA-ALERTING-NTFY-AND-BASE-RULES`), runbooks (`TCK-20261018-BASE-ALERTS-RUNBOOKS-AND-DRILL`).
- `backend:9109` (step-2 scrape ticket, blocked on #622 R1).
- cAdvisor or per-container metrics.

## Acceptance Criteria
- `docker compose --profile observability config -q` passes; `promtool check config` from the pinned Prometheus image
  passes (**validated**).
- After an observability start (asked of lead-planner): every new job is `up` in the targets page, and
  `node_filesystem_avail_bytes` returns series for the host's `/` and `/data` mounts (**running locally**).
- No job targets `backend:8000`.
- node-exporter's measured RSS is recorded and its `mem_limit` set from it.

## Related Tickets
Epic `TCK-20261018-EPIC-DEVOPS-S4-BASE-ALERTS-LOCAL`. Next: `TCK-20261018-GRAFANA-ALERTING-NTFY-AND-BASE-RULES`. Step 2: `TCK-20261018-SCRAPE-BACKEND-METRICS-PORT`.

## Related Docs
`docs/architecture/devops_baseline_adr.md` (D1, D5)

## Related Stored Artifacts
None.

## Related Code Areas
`docker/prometheus.yml`, `compose.yaml`

## Assumptions / Open Questions
- The host mounts to watch are `/` and `/data` (both about 70 % used on 2026-10-18).

## Implementation Notes
- `docker/prometheus.yml`: the `rpg-backend` `backend:8000` job is removed (a comment says why and where `backend:9109` comes back). New jobs: `prometheus` (localhost:9090), `grafana` (grafana:3000/metrics), `loki` (loki:3100/metrics), `tempo` (tempo:3200/metrics), `node-exporter` (node-exporter:9100). The `ntfy` job is added in `TCK-20261018-GRAFANA-ALERTING-NTFY-AND-BASE-RULES` (ntfy is not defined yet).
- `compose.yaml`: `node-exporter` service, `prom/node-exporter:v1.12.1` (2026-07-14, latest stable at least two weeks old) with the multi-arch index digest from a registry query (no pull). Observability profile, `mem_limit: 64m` as a PLACEHOLDER until the RSS is measured, `/:/host:ro,rslave`, `--path.rootfs=/host`, only the filesystem collector (`--collector.disable-defaults`), pseudo filesystem types excluded by `fs-types-exclude`. No privileged, host network, host PID or host port. No healthcheck (static binary); `up{job="node-exporter"}` is the probe.
- Lead's note 4: record the RSS before fixing `mem_limit`, and confirm series for both `/` and `/data`.

## Test Summary
- **validated:** `docker compose config -q` for the default and the observability profile; YAML parse; `promtool check config` from the pinned Prometheus image (`SUCCESS: valid prometheus config file syntax`).
- Not yet run (needs the node-exporter pull and the single stack run, both asked of platform-planner/lead): targets `up`, `node_filesystem_avail_bytes` for `/` and `/data`, node-exporter RSS and the `mem_limit`, Grafana `/metrics` without auth.

## Files Changed
(open)

## Completion Summary
(open)
