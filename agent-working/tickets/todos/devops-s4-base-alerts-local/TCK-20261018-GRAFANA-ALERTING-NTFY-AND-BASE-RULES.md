---
status: active
layer: platform
authority: P1
audience: agent
ticket_id: TCK-20261018-GRAFANA-ALERTING-NTFY-AND-BASE-RULES
phase: open
date: 2026-10-18
tags: [platform, observability]
---

# TCK-20261018-GRAFANA-ALERTING-NTFY-AND-BASE-RULES

## Title
Grafana alerting provisioned as files: local ntfy service, ntfy contact point (topic from a gitignored secret), notification policy, and the base rule group

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
ADR D5 as kept by the owner (D-1, 2026-10-18): Grafana alert rules provisioned as files under `docker/grafana/`, an ntfy
contact point, no Alertmanager. This ticket builds the alerting path once; step-3 `TCK-20261018-API-SLO-ALERT-NTFY-RUNBOOK` later adds only its rule group.

## Scope
- **Confirm first** (investigation): the pinned Grafana 13.2.4 loads alert rules, contact points and notification
  policies from `provisioning/alerting/*.yaml` (`apiVersion: 1`). Grafana's file-provisioning docs list rules
  (`groups`), `contactPoints` and `policies`, with `$VAR` environment interpolation. Grafana has **no native ntfy
  integration**: use the `webhook` contact point with a custom payload template (templateable payloads exist in the 13.x
  webhook notifier docs), posting ntfy's JSON publish format to the ntfy root URL. Verify the field names against ntfy's
  own docs.
- **`ntfy` service** in `compose.yaml`: `profiles: ["observability"]`, pinned by tag plus digest, a `mem_limit`, a
  healthcheck on its health endpoint, host port on `127.0.0.1` only (the owner subscribes from this host), metrics on if
  the image supports it (then add its scrape job).
- **Secret:** the ntfy topic (and URL if needed) lives in a gitignored file under `docker/secrets/` (already ignored).
  Grafana reads it through provisioning interpolation: use `$__file{...}` if the pinned version supports it in
  provisioning files; otherwise a gitignored env file passed to the grafana service and `$NTFY_TOPIC` in the contact
  point. Add a fail-fast guard like the admin-password one (refuse to start on an empty topic). Never commit a topic;
  never put a real topic in any file in git. Document the one-line setup in the compose header comment.
- **Provisioning files** under `docker/grafana/provisioning/alerting/`: the contact point, the notification policy
  (default route to ntfy; group_wait/interval/repeat stated), and the rule group `base`. Datasources by uid. Each rule
  has `runbook_url` and `summary` annotations pointing at `TCK-20261018-BASE-ALERTS-RUNBOOKS-AND-DRILL`'s runbooks (relative repo paths are fine until a
  docs host exists).
- **Rules** (Grafana-managed, on the `prometheus` datasource unless noted):
  - `TargetDown`: `up == 0` for 2m, per `job`.
  - `PrometheusUnreachable`: the datasource query errors; set `execErrState: Alerting` on one rule so a dead Prometheus
    is not silent. State the choice of `noDataState`/`execErrState` for every rule in the runbook.
  - `GrafanaAlertingFailures`: Grafana's own alerting self-metrics (rule evaluation failures, notification failures),
    scraped by `TCK-20261018-BASE-ALERT-SCRAPES-AND-NODE-EXPORTER`'s `grafana` job. Confirm the exact metric names from the live `/metrics`. Known limit: if the
    notifier itself is broken, this alert can't reach ntfy; the runbook says so.
  - `DiskSpaceLow`: host filesystem free < 15 % for 10m (`/` and `/data`).
  - `DiskWillFillIn24h`: `predict_linear` over 6h of free bytes < 0 at +24h, for 30m.
  Thresholds are stated in the runbook with why.

## Out of Scope
- The API SLO rule and the Redis cause alert (step 3). Alertmanager. A public ntfy.sh topic.
- Any `tests/**` (D-4).

## Acceptance Criteria
- After a fresh observability start, Grafana's log shows the alerting provisioning loaded with no error, and the rules,
  contact point and policy appear as provisioned (read-only) (**running locally**).
- A test notification through the provisioned contact point reaches the local ntfy topic (record the time and payload).
- `git grep` for the local topic value finds nothing; the secret file is ignored (`git check-ignore`).
- `docker compose --profile observability config -q` passes; ntfy is bound to `127.0.0.1` only.

## Related Tickets
Epic `TCK-20261018-EPIC-DEVOPS-S4-BASE-ALERTS-LOCAL`. Needs `TCK-20261018-BASE-ALERT-SCRAPES-AND-NODE-EXPORTER`. Step 3: `TCK-20261018-API-SLO-ALERT-NTFY-RUNBOOK` (reuses this contact point and policy).

## Related Docs
`docs/architecture/devops_baseline_adr.md` (D5)

## Related Stored Artifacts
None.

## Related Code Areas
`docker/grafana/provisioning/alerting/` (new), `compose.yaml`, `.gitignore`

## Assumptions / Open Questions
- If neither `$__file{}` nor env interpolation works for the contact point in 13.2.4, stop and report to
  platform-planner before choosing another mechanism.

## Implementation Notes
(open)

## Test Summary
(open)

## Files Changed
(open)

## Completion Summary
(open)
