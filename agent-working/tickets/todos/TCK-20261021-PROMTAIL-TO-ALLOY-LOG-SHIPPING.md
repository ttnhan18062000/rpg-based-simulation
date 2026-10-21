---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20261021-PROMTAIL-TO-ALLOY-LOG-SHIPPING
phase: open
date: 2026-10-21
tags: [observability, platform]
---

# TCK-20261021-PROMTAIL-TO-ALLOY-LOG-SHIPPING

## Title
Ship container logs to Loki with Grafana Alloy instead of the deprecated Promtail

## Status
OPEN

## Tier
standard

## Type
refactor

## Priority
P3

## Request Summary
Promtail is deprecated upstream, and Grafana Alloy replaces it. Three earlier tickets deferred the migration to a follow-up: TCK-20261014-OBS-STACK-PROMETHEUS3-GRAFANA13, TCK-20261015-LOKI-37-READINESS-VIA-PROMTAIL and TCK-20261018-OBSERVABILITY-PROFILE-HARDENING. TCK-20261020-PROMTAIL-DISCOVERY-DENIED-BY-SOCKET-PROXY (#694) fixed shipping on Promtail 3.6.8 with `NETWORKS=1` on `docker-socket-proxy` and recorded this ticket as still to file. Alloy's Docker discovery calls the same Docker networks API, so it needs that same proxy allow-list. This ticket is the follow-up. Filed 2026-10-21 by platform-planner at the request of lead-planner; it is not dispatched yet.

## Scope
- Replace the `promtail` compose service (observability profile) with an `alloy` service. Pin the image to the latest stable release that is at least two weeks old, by multi-arch index digest, with a dated comment (the same convention as the tempo and loki pins). Set a `mem_limit` and reach it from measured anon + active_file, never `memory.peak`.
- Replace `docker/promtail-config.yml` with an Alloy config (for example `docker/alloy/config.alloy`) that keeps today's behaviour exactly:
  - discovery through `tcp://docker-socket-proxy:2375` only (no socket mount in Alloy, and the proxy keeps `CONTAINERS=1`, `NETWORKS=1`, `POST=0`);
  - the compose-project filter `com.docker.compose.project=${COMPOSE_PROJECT_NAME}`;
  - drop loki's and the shipper's own logs by compose service label;
  - the labels `container` (leading `/` stripped) and `job="varlogs"`;
  - JSON parsing of `level`, `component`, `tick` and `message`, with only `level` and `component` promoted to stream labels (`docs/observability/loki_label_policy.md`);
  - push to `http://loki:3100/loki/api/v1/push`.
- Healthcheck: keep the current meaning, "the shipper's own /ready AND loki:3100/ready both answer 200". Check first which tools the Alloy image has (Promtail's has bash but no wget or curl). If it has no probe tool, document that in the compose comment, the same way loki and tempo do.
- Prometheus: rename the `promtail` scrape job in `docker/prometheus.yml` to the Alloy target and port.
- Alert `LogShippingErrors` (`docker/grafana/provisioning/alerting/rules-base.yaml`): today's expression is `sum(rate(loki_internal_log_messages_total{job="promtail",level="error"}[5m]))`. Find the Alloy metric that counts failed discovery refreshes and failed Loki pushes. Keep the design rules recorded in #694: no comparison inside the PromQL, noData means Alerting, and the series must exist at 0 from a fresh start. Re-prove the rule with the three live cases of the 2026-10-20 record: shipper stopped, a fresh shipper against a proxy without `NETWORKS` (403), and a quiet stack.
- Update `docs/runbooks/log-shipping.md`, `docs/runbooks/target-down.md`, `docs/runbooks/README.md` and the Loki datasource comment in `docker/grafana/provisioning/datasources/datasource.yml`. Write a dated record under `docs/runbooks/records/`.
- Proof run (one heavy slot, lead-cleared, abort watcher first): a fresh `up` of the observability profile; Alloy's targets list this project's containers only; a fresh backend line is queryable in Loki with the expected labels; `LogShippingErrors` stays Normal on a healthy stack.

## Out of Scope
- Changing what is shipped or labelled (no new labels, no new log sources, no host log files).
- Loki, Tempo or Grafana version changes.
- Using Alloy for metrics or traces (OTLP receiving stays with Tempo, ADR D4). That would be a separate decision for lead-planner.
- The socket-proxy allow-list itself, unless Alloy needs an endpoint beyond `CONTAINERS` and `NETWORKS`. If it does, stop and raise it with lead-planner: it is an owner decision, as `NETWORKS=1` was.
- src/** changes.

## Acceptance Criteria
- `docker compose --profile observability config` lists `alloy` and no `promtail`, and `docker/promtail-config.yml` is removed.
- On a fresh stack, Loki holds backend lines with labels `container`, `job="varlogs"`, `level` and `component`, and no `tick` or `message` label. This matches the Promtail behaviour recorded in `docs/runbooks/records/2026-10-20-log-shipping-fix.md`.
- Only this compose project's containers are discovered, shown by the shipper's own targets view with another project's container running.
- `LogShippingErrors` fires on the 403 case and the stopped case and stays Normal on a quiet stack, with the evidence in the dated record.
- The Loki label-safety guard (`tests/logging/test_loki_cardinality.py`, which today reads `docker/promtail-config.yml`) checks the Alloy config instead and still passes. This is a tests/** change, so it routes to testing-planner (see Open Questions).
- Every living doc that names Promtail as the running shipper is updated, or routed to its owner (list below). Archive, audit and dated-record docs stay as written.

## Related Tickets
- TCK-20261020-PROMTAIL-DISCOVERY-DENIED-BY-SOCKET-PROXY (#694; NETWORKS=1 and LogShippingErrors)
- TCK-20261018-OBSERVABILITY-PROFILE-HARDENING (socket proxy; named Alloy as a follow-up)
- TCK-20261014-OBS-STACK-PROMETHEUS3-GRAFANA13, TCK-20261015-LOKI-37-READINESS-VIA-PROMTAIL (deferred the migration)
- TCK-20261018-EPIC-DEVOPS-STEP2-OBSERVABILITY-LOCAL (lists the Alloy migration as out of scope, a follow-up)

## Related Docs
- docs/runbooks/log-shipping.md, docs/runbooks/target-down.md, docs/runbooks/README.md
- docs/runbooks/records/2026-10-20-log-shipping-fix.md
- docs/observability/loki_label_policy.md
- docs/architecture/devops_baseline_adr.md, docs/architecture/system_overview.md (lead-planner)
- docs/engine/contracts/infrastructure_overview.md (rpg-planner)

## Related Stored Artifacts
None.

## Related Code Areas
- compose.yaml (`promtail`, `docker-socket-proxy`)
- docker/promtail-config.yml
- docker/prometheus.yml (job `promtail`)
- docker/grafana/provisioning/alerting/rules-base.yaml (`LogShippingErrors`)
- docker/grafana/provisioning/datasources/datasource.yml
- tests/logging/test_loki_cardinality.py (testing-planner)

## Assumptions / Open Questions
- Cross-domain edits, each routed to its owner and not made by platform: `tests/logging/test_loki_cardinality.py` (testing-planner); `docs/architecture/devops_baseline_adr.md` and `docs/architecture/system_overview.md` (lead-planner); `docs/engine/contracts/infrastructure_overview.md` (rpg-planner; that topology diagram is already reported out of date on #532). Find the owner of `docs/observability/loki_label_policy.md` from `registries/session_roles.yaml` before editing it.
- The Alloy release, its Docker discovery behaviour against the proxy, its image tools and its error metric are all unchecked. The investigation verifies each one from upstream docs and a probe, and does not assume them.
- Promtail's upstream end-of-support date is not recorded in the repo. The investigation cites it from Grafana's docs, since it decides how urgent this ticket is (P3 for now; lead-planner sets the priority).
- Positions: Promtail keeps its positions file in `/tmp` in the container (it is lost when the container is recreated). Decide whether Alloy's storage gets a volume, and record the decision.

## Implementation Notes
Not started.

## Test Summary
Not started.

## Files Changed
None yet.

## Completion Summary
Not started.
