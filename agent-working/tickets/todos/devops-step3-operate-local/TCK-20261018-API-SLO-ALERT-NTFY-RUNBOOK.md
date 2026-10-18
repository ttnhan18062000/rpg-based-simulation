---
status: active
layer: platform
authority: P1
audience: agent
ticket_id: TCK-20261018-API-SLO-ALERT-NTFY-RUNBOOK
phase: open
date: 2026-10-18
tags: [platform, observability]
---

# TCK-20261018-API-SLO-ALERT-NTFY-RUNBOOK

## Title
One API SLO alert as a provisioned Grafana alert rule, a local ntfy container as its contact point, and the runbook it links to

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
ADR D5 as amended: one SLO alert, Grafana alerting, ntfy. The owner hasn't picked a public ntfy topic, so the contact
point is a local ntfy container for now; switching to ntfy.sh later is a one-line URL change. Every alert links to a
runbook in `docs/runbooks/`.

## Scope
- **SLO:** API p95 latency over 5 minutes, above the threshold from the measured run's record, for a set `for:`
  window. Excluded from the SLI: `/health`, `/metrics` and 429s (429s are admission, not a fault).
  - The PromQL is the same expression as the dashboard's "SLO" row (`TCK-20261018-API-DASHBOARD-AND-TRACE-PROOF`). The
    rule file and the dashboard must not drift apart: a small test compares the two expressions.
  - D5's availability SLO (/health ≥ 99 % over 1 h) is written into the runbook as an SLO without an alert. Step 3
    asks for one alert.
- **Provisioning files** under `docker/grafana/provisioning/alerting/`: the rule group, the contact point, and the
  notification policy. Datasources are referenced by uid. `noDataState` and `execErrState` are chosen and stated in
  the runbook.
- **`ntfy` service:**
  - `profiles: ["observability"]`, pinned by digest, with a `mem_limit`, a healthcheck if the image can probe itself;
  - a host port on `127.0.0.1` only, so the owner can open the web UI or subscribe on this host;
  - the topic name from env with a local default (for example `rpg-alerts-local`).

  The Grafana contact point is the webhook or ntfy integration to `http://ntfy/<topic>`, with the runbook URL in the
  message.
- **`docs/runbooks/api-latency-slo.md`** (frontmatter per the docs schema):
  - what the alert means;
  - the first three checks (the dashboard panels, the Loki query, a Tempo search for slow traces);
  - known causes (engine tick contention in the same process, admission pressure mode, host saturation);
  - mitigations;
  - how to silence it;
  - escalation (the owner);
  - the Trivy baseline note from #561 under risks.

  Also `docs/runbooks/README.md`, the index.
- **Register `docs/runbooks/**`** to the platform domain's `owns` in this PR (D8 route, as in the Locust ticket).
- Run `make knowledge-index-update` after adding the docs.

## Out of Scope
- The Redis-down cause alert (`TCK-20261018-REDIS-DOWN-CAUSE-ALERT`), the ai_worker lag alert (blocked ticket).
- A public ntfy.sh topic or Telegram: an owner choice, later.
- Prometheus-side alerting rules or Alertmanager (D5 says Grafana alert rules).

## Acceptance Criteria
- After a fresh `--profile observability` start, the rule, contact point and policy appear as provisioned (read-only)
  in Grafana (**running locally**).
- **Fire test:** a short Locust step above the knee, or a lowered threshold via an env override (never by editing the
  committed threshold), makes the alert fire. The ntfy topic receives it with the runbook link, and it resolves after
  the load stops. Timestamps are recorded.
- `docker compose --profile observability config -q` passes. ntfy is bound to `127.0.0.1` only.
- The new docs pass frontmatter validation. `tools/sessions/validate.py` passes with the new glob.

## Related Tickets
Epic `TCK-20261018-EPIC-DEVOPS-STEP3-OPERATE-LOCAL`. Needs `TCK-20261018-API-LOAD-TEST-MEASURED-RUN` (the threshold)
and step 2's `TCK-20261018-API-DASHBOARD-AND-TRACE-PROOF` (the shared PromQL).

## Related Docs
`docs/architecture/devops_baseline_adr.md` (D5), `docs/runbooks/` (new)

## Related Stored Artifacts
None.

## Related Code Areas
`compose.yaml`, `docker/grafana/provisioning/alerting/` (new), `docs/runbooks/` (new), `registries/session_roles.yaml`

## Assumptions / Open Questions
- If Grafana 13's file provisioning for alerting differs from the documented schema, follow the 13.x docs and
  record the version used.

## Implementation Notes
(open)

## Test Summary
(open)

## Files Changed
(open)

## Completion Summary
(open)
