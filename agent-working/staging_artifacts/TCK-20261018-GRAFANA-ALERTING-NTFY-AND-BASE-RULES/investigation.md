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
