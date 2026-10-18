---
status: active
layer: platform
authority: P2
audience: agent
ticket_id: TCK-20261018-GRAFANA-ALERTING-NTFY-AND-BASE-RULES
artifact_type: plan
tags: [platform, observability]
---

# Plan: TCK-20261018-GRAFANA-ALERTING-NTFY-AND-BASE-RULES

Written by platform-planner at filing (2026-10-18); the implementer updates it as the work changes.

## Steps
1. Investigation first: confirm file-provisioned alerting in Grafana 13.2.4, the secret interpolation form, and the
   webhook custom-payload syntax; confirm ntfy's JSON publish fields. Record sources in investigation.md.
2. Add the `ntfy` service (pinned, mem_limit, healthcheck, 127.0.0.1 port); ask for the pull, pull alone.
3. Add the secret file mechanism (gitignored) and the empty-topic guard; document setup in the compose header.
4. Write `contact-points.yaml`, `policies.yaml`, `rules-base.yaml` under `docker/grafana/provisioning/alerting/`.
5. Config checks; the live load check and the test notification run in the folder's stack run (asked of lead-planner).

## Scope guards
No Alertmanager. No real topic in git. No `tests/**`. Datasources by uid only.

## Update (implementer, 2026-10-18)
Lead's notes applied: deny-all plus a write-only token for the topic via the gitignored secrets mechanism, created with ntfy's CLI (steps in the compose header); `$__file{}` confirmed from the Grafana 13.2.4 source and used first; node-exporter RSS and `/` + `/data` series are C1's live check. Config validated; the live checks wait for the pull and the single stack run.
