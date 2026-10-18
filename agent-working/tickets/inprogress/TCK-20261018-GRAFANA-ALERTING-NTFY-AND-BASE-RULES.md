---
status: active
layer: platform
authority: P1
audience: agent
ticket_id: TCK-20261018-GRAFANA-ALERTING-NTFY-AND-BASE-RULES
phase: inprogress
date: 2026-10-18
tags: [platform, observability]
---

# TCK-20261018-GRAFANA-ALERTING-NTFY-AND-BASE-RULES

## Title
Grafana alerting provisioned as files: local ntfy service, ntfy contact point (topic from a gitignored secret), notification policy, and the base rule group

## Status
INPROGRESS

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
- **Provisioning mechanism (lead's note 3), confirmed from the v13.2.4 source before any run:** `pkg/services/provisioning/values` runs every provisioned string through `setting.ExpandVar`, which supports `$__file{path}` (it has a test for it), and alerting contact-point `settings` are `values.JSONValue`, so the expansion applies. So `$__file{/run/secrets/ntfy_topic}` and `$__file{/run/secrets/ntfy_token}` are used; the env-file fallback is not needed unless the live check shows otherwise. A literal `$` in a provisioned value must be written `$$` (summaries use `$$labels`).
- **Webhook fields**, checked against grafana/alerting `receivers/webhook/v1/config.go` (the commit pinned in Grafana 13.2.4's go.mod): `url`, `httpMethod`, `authorization_scheme`, `authorization_credentials`, `payload.template`, `payload.vars` (`.Vars.<key>`). The payload is ntfy's JSON publish body (topic in the body, posted to the root URL), built with `coll.Dict ... | data.ToJSON`. The template functions and the exact JSON are confirmed only at the live check.
- **ntfy** `binwiederhier/ntfy:v2.28.0` (2026-08-27; v2.29-v2.31 are under two weeks old), tag plus index digest from a registry query (no pull). Env config: `NTFY_AUTH_FILE`, `NTFY_AUTH_DEFAULT_ACCESS=deny-all` (lead's note 2), `NTFY_CACHE_FILE`, `NTFY_METRICS_LISTEN_HTTP=:9091` (a dedicated in-network metrics port outside the auth; the `ntfy` scrape job is added to `docker/prometheus.yml`), host port `127.0.0.1:${NTFY_PORT:-2586}`. Healthcheck is the documented `/v1/health` wget. `mem_limit: 128m` is a PLACEHOLDER until the peak is measured. Named volume `ntfy_data`.
- **Credential (lead's note 2):** Grafana sends `Authorization: Bearer <token>` for a regular ntfy user `grafana` that has write-only access to the one topic. The user, the ACL and the token are created with ntfy's own CLI inside the container; the steps are in the `compose.yaml` header (no real values). The topic and the token are gitignored files `docker/secrets/ntfy_topic` and `docker/secrets/ntfy_token`; the grafana entrypoint guard refuses to start on an empty one, like the admin-password guard.
- **Rules** (`docker/grafana/provisioning/alerting/rules-base.yaml`, group `base`, interval 1m): TargetDown (`min by (job) (up) < 1`, for 2m), PrometheusUnreachable (`vector(1)`, `execErrState: Alerting`, for 2m), GrafanaAlertingFailures (increase of `grafana_alerting_rule_evaluation_failures_total` + `grafana_alerting_notifications_failed_total` over 5m; the first name is in the 13.2.4 source, the second is confirmed at the live check), DiskSpaceLow (free % < 15, for 10m, mounts `/` and `/data`), DiskWillFillIn24h (`predict_linear` 6h at +24h < 0, for 30m). `noDataState`/`execErrState` choices are in the file header and go into the runbook. Policy: default route to ntfy, group_by alertname+job, group_wait 30s, group_interval 5m, repeat 4h.

## Test Summary
- **validated:** `docker compose config -q` for both profiles; YAML parse of the four provisioning files; `promtool check config` from the pinned image (SUCCESS, with the `ntfy` job); `git check-ignore` shows `docker/secrets/ntfy_topic` and `ntfy_token` are ignored.
- **running locally** (first stack run, 2026-10-18, 8-service subset; details in the drill record `docs/runbooks/records/2026-10-18-target-down-drill.md`): provisioning loaded with no error; 5 rules, the contact point and the policy read back as provenance `file`; the contact point shows the credential as `[REDACTED]` and no `$__file` text (L2 PASS); ntfy received valid JSON with title, priority 4 and tag `bell` (L3 PASS); node-exporter mountpoints `/` and `/data` without a `/host` prefix (L5 PASS).
- **L1 FAILED** on the first run: the message carried a literal `$$labels` (see investigation.md); fixed to a single `$labels`; re-check pending.
- **L4:** the metric name is right but the series is absent at zero by design (source cited in investigation.md); not exercised with a real failure.
- Delivery was proven by the drill's real firing and resolved messages, not by the test-notification API (the old endpoint is removed in 13.x). Delivery path: Grafana webhook, ntfy deny-all, write-only token.

## Files Changed
(open)

## Completion Summary
(open)
