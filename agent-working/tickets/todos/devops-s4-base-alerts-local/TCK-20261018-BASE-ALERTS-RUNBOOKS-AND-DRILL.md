---
status: active
layer: platform
authority: P1
audience: agent
ticket_id: TCK-20261018-BASE-ALERTS-RUNBOOKS-AND-DRILL
phase: open
date: 2026-10-18
tags: [platform, observability]
---

# TCK-20261018-BASE-ALERTS-RUNBOOKS-AND-DRILL

## Title
Runbooks for the base alerts, the docs/runbooks index, and one recorded drill (stop Loki, alert reaches ntfy, recover)

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
D5 ties every alert to a runbook and asks for a recorded drill. The owner's S4 brief asks for a drill that stops a target
and shows the alert firing. Loki is the target: stopping it touches no simulation state, and its absence is visible in
Grafana and in `up`.

## Scope
- `docs/runbooks/README.md`: the index (alerts -> runbook -> drill records). Frontmatter per the docs schema.
- `docs/runbooks/target-down.md`, `docs/runbooks/disk-space.md`, `docs/runbooks/alerting-pipeline.md` (covers
  `PrometheusUnreachable` and `GrafanaAlertingFailures`). Each: what it means, first three checks, known causes,
  mitigation, how to silence (Grafana silence), escalation (the owner), the rule's `for`, thresholds, and its
  `noDataState`/`execErrState` choice.
- **Drill** (one observability stack run, asked of lead-planner first):
  - start the profile; wait for all targets `up`;
  - `docker compose stop loki`, timestamp T0;
  - record T1 (rule pending), T2 (firing), T3 (ntfy received);
  - follow the runbook; `docker compose start loki`, T4; record T5 (resolved notification);
  - capture the ntfy messages (topic redacted) and the Grafana alert state history.
- Record: `docs/runbooks/records/2026-10-18-target-down-drill.md` (or the run date): method, host spec, commit, the
  timeline table, detection time (T3-T0), recovery time (T5-T4), what the runbook got wrong, and a short post-mortem.
- The same stack run also serves `TCK-20261018-BASE-ALERT-SCRAPES-AND-NODE-EXPORTER`'s and `TCK-20261018-GRAFANA-ALERTING-NTFY-AND-BASE-RULES`'s live checks and the epic's `docker stats` peak table.
- Run `make knowledge-index-update` after adding the docs.

## Out of Scope
- The Redis-stop drill under load (step 3, needs the SLO and Redis cause alerts).
- Disk alerts are not drilled by filling a disk; `DiskSpaceLow` is proven by evaluating its query (free % per mount)
  and, if lead agrees, by a temporary env-override threshold, never by editing the committed one.

## Acceptance Criteria
- The drill record exists with all timestamps and the ntfy evidence (**running locally**).
- The runbooks and README pass frontmatter validation and are linked from each rule's `runbook_url`.
- No real ntfy topic appears in the record or any committed file.

## Related Tickets
Epic `TCK-20261018-EPIC-DEVOPS-S4-BASE-ALERTS-LOCAL`. Needs `TCK-20261018-BASE-ALERT-SCRAPES-AND-NODE-EXPORTER`, `TCK-20261018-GRAFANA-ALERTING-NTFY-AND-BASE-RULES`. Step 3: `TCK-20261018-REDIS-STOP-DRILL-UNDER-LOAD` (the later, bigger drill).

## Related Docs
`docs/architecture/devops_baseline_adr.md` (D5, D7), `docs/runbooks/records/2026-10-18-api-load-test.md` (record style)

## Related Stored Artifacts
None.

## Related Code Areas
`docs/runbooks/**`

## Assumptions / Open Questions
- Expected detection: rule evaluation interval (1m) + `for: 2m` + notification group wait; the record states the
  configured values next to the measured times.

## Implementation Notes
(open)

## Test Summary
(open)

## Files Changed
(open)

## Completion Summary
(open)
