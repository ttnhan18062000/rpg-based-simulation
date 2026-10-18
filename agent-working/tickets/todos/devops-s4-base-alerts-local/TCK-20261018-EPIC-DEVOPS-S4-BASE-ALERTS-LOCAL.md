---
status: active
layer: platform
authority: P1
audience: agent
ticket_id: TCK-20261018-EPIC-DEVOPS-S4-BASE-ALERTS-LOCAL
phase: open
date: 2026-10-18
tags: [platform, observability]
---

# TCK-20261018-EPIC-DEVOPS-S4-BASE-ALERTS-LOCAL

## Title
DevOps S4 (host ubuntu): base alerts with no rpg metrics (target down, observability self-health, disk), Grafana alerting to a local ntfy, runbooks and one recorded drill

## Status
EPIC_SCOPED

## Tier
epic

## Type
feature

## Priority
P2

## Request Summary
Owner decision (2026-10-18, relayed by lead-planner, also on #618): while rpg's #622 is pending, the ubuntu platform
seats build the alerts that need no rpg metrics. Lead's review answers (same day) fix the shape:
- **D-1 (owner): ADR D5 stands.** Rules are Grafana alert rules provisioned as files under `docker/grafana/`; the contact
  point is ntfy; **no Alertmanager container**. The step-3 alert tickets keep their shape.
- **D-4:** no new `tests/**` (rpg's). The proof is Grafana provisioning loading cleanly plus the recorded drill, and any
  static check a pinned image already provides. Any CI check goes in a platform-owned, path-gated workflow registered in
  the same PR, never in `test.yml`.
- The ntfy URL/topic comes from a gitignored secret file. It is never committed and never put in a test.
- The API SLO alert still waits on #622 R2 (step-3 `TCK-20261018-API-SLO-ALERT-NTFY-RUNBOOK`).

## Scope
Three children, in `SEQUENCE.md` order:
1. `TCK-20261018-BASE-ALERT-SCRAPES-AND-NODE-EXPORTER`: Prometheus scrapes the observability services and a new node-exporter; the 401 `backend:8000` job goes.
2. `TCK-20261018-GRAFANA-ALERTING-NTFY-AND-BASE-RULES`: ntfy service, Grafana contact point and notification policy, and the base rule group.
3. `TCK-20261018-BASE-ALERTS-RUNBOOKS-AND-DRILL`: runbooks, the runbook index, and the recorded drill (stop Loki, see the alert reach ntfy, recover).

## Out of Scope
- The API SLO rule (step-3 `TCK-20261018-API-SLO-ALERT-NTFY-RUNBOOK`, blocked on #622 R2), the Redis cause alert, the ai_worker lag alert.
- Alertmanager, Prometheus-side rule files, a public ntfy.sh topic, Telegram.
- Any `src/**` or `tests/**` edit.

## Acceptance Criteria
- All three children DONE, one PR from a `platform-implementer-local-*` branch.
- Evidence uses the D7 labels only: "running locally" for the stack, the alerts and the drill; "validated" for config
  checks.
- The observability profile still fits the host: the measured peak `docker stats` table with the new containers.

## Related Tickets
- Step 3: `TCK-20261018-EPIC-DEVOPS-STEP3-OPERATE-LOCAL` (its `TCK-20261018-API-SLO-ALERT-NTFY-RUNBOOK` reuses this epic's contact point and policy; amended
  in the same filing commit).
- Step 2: `TCK-20261018-SCRAPE-BACKEND-METRICS-PORT` (adds `backend:9109` later; its "remove the 8000 target" is done here).
- Issues #618, #622.

## Related Docs
`docs/architecture/devops_baseline_adr.md` (D1, D5, D7), `docs/architecture/devops_plan_amendment_proposal.md` (step 3)

## Related Stored Artifacts
None.

## Related Code Areas
`docker/prometheus.yml`, `docker/grafana/provisioning/alerting/` (new), `compose.yaml`, `docs/runbooks/**`, `.gitignore`

## Assumptions / Open Questions
- Host rules: every image pull and stack run is asked of lead-planner first, one at a time; pulls run alone.

## Implementation Notes
Epic tier: the children carry the implementation.

## Test Summary
See the child tickets.

## Files Changed
See the child tickets.

## Completion Summary
(open)
