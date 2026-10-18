---
status: active
layer: platform
authority: P2
audience: agent
ticket_id: TCK-20261018-GRAFANA-ALERTING-NTFY-AND-BASE-RULES
artifact_type: investigation
tags: [platform, observability]
---

# Investigation: TCK-20261018-GRAFANA-ALERTING-NTFY-AND-BASE-RULES

Written by platform-planner at filing (2026-10-18); the implementer updates it as the work changes.

## Findings at filing (platform-planner, 2026-10-18)
- Grafana file provisioning covers alert rules (`groups`), `contactPoints` and `policies`, from
  `provisioning/alerting` with `apiVersion: 1`, and interpolates environment variables with `$variable`
  (https://grafana.com/docs/grafana/latest/alerting/set-up/provision-alerting-resources/file-provisioning/). The page
  does not mention `$__file{}`; confirm against 13.2.4.
- No native ntfy contact point type in that list; the webhook notifier supports a custom payload template
  (https://grafana.com/docs/grafana/v13.1/alerting/configure-notifications/manage-contact-points/integrations/webhook-notifier/).
  A community setup posts to the ntfy root URL with topic/message/title/tags/priority fields
  (https://forum.yunohost.org/t/get-grafana-alerts-over-ntfy/41868); verify against ntfy's docs.
- `docker/secrets/` is gitignored on main (`.gitignore`, TCK-20261018-OBSERVABILITY-PROFILE-HARDENING); the grafana
  service already uses a compose secret for the admin password, with a fail-fast guard in its entrypoint.
- Step-3 `TCK-20261018-API-SLO-ALERT-NTFY-RUNBOOK` originally scoped the ntfy service, contact point and policy; amended at filing to reuse this ticket's.

## To confirm during the work
- Grafana self-alerting metric names in 13.2.4 (from the live `/metrics`).
- ntfy image tag/digest, health endpoint, metrics flag.

## First stack run, 2026-10-18 (8-service subset, running locally) - findings
- **`$$` is not an escape.** The firing/resolved ntfy messages carried the literal text `Scrape target {{ $$labels.job }} is down`. The first drill therefore refuted my earlier note that `$$` escapes a dollar in provisioned values. Fix: single `$labels`. Whether a single `$labels` survives the provisioning env expansion is proven in the re-check; if it is eaten, the fallback is a provisioned notification template under `provisioning/alerting` (`templates:`) referenced by name. Result of the re-check: (recorded below after the run).
- **`grafana_alerting_notifications_failed_total` is the real name** (L4). Source: `pkg/services/ngalert/metrics/multi_org_alertmanager.go` at v13.2.4: the `numFailedNotifications` desc `grafana_alerting_notifications_failed_total` with labels `org`, `integration` (and the request-level `notification_requests_failed_total`), sent with `WithSkipZeroValueMetrics`. So the series is absent until a first failure, which is why the live `/metrics` showed only `grafana_alerting_notifications_total{integration="webhook",org="1"} 2` and `grafana_alerting_rule_evaluation_failures_total{org="1"} 0`. The rule's `or vector(0)` keeps it evaluating. A failure was not induced, so detection of a failed notification is validated by source only.
- **Secret files:** 0600 files were unreadable by Grafana's container user (uid 472); the guard looped until they were 0644. 0644 is accepted for this single-user host (lead, 2026-10-18); the compose header says so and names the multi-user limit.
- **Test-notification API:** the old `receivers/test` endpoint is removed in 13.x; the new `/apis/notifications.alerting.grafana.app/v1beta1/.../receivers/{uid}/test` returned a 400 for the body I tried. Delivery was proven by the drill's real firing and resolved messages instead.
