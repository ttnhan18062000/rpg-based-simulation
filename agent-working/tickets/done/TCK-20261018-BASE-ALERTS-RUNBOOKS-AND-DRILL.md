---
status: historical
layer: platform
authority: P1
audience: agent
ticket_id: TCK-20261018-BASE-ALERTS-RUNBOOKS-AND-DRILL
phase: done
date: 2026-10-18
tags: [platform, observability]
---

# TCK-20261018-BASE-ALERTS-RUNBOOKS-AND-DRILL

## Title
Runbooks for the base alerts, the docs/runbooks index, and one recorded drill (stop Loki, alert reaches ntfy, recover)

## Status
DONE

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
- Disk alerts are not drilled by filling a disk. `DiskSpaceLow` is proven by query only (lead decision, 2026-10-18): run the
  rule expression in Explore or the Prometheus API with a threshold above the current free %, and record the output. No
  env-override threshold exists; the committed value stays 15 %.

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
- Written before the stack run: `docs/runbooks/README.md` (index with the alert -> runbook -> drill table, silence, escalation), `target-down.md`, `disk-space.md`, `alerting-pipeline.md`. Each states what the alert means, the first three checks, known causes, mitigation, silence and escalation, the rule's `for`, thresholds with the reason, and its `noDataState`/`execErrState`. Frontmatter validated. The rules' `runbook_url` values (`docs/runbooks/target-down.md`, `disk-space.md`, `alerting-pipeline.md`) match these paths.
- Lead's note 1: `DiskSpaceLow` is proven by query only (the expression run in Explore or the Prometheus API with a threshold above the current free percent, output recorded). No override threshold; the committed 15 percent stays. The Out of Scope line was edited to match, in the C1 commit.
- The drill record (`docs/runbooks/records/<run date>-target-down-drill.md`), the `docker stats` peak table and `make knowledge-index-update` come after the single stack run.

## Test Summary
- **validated:** frontmatter of the four runbook docs and the drill record (`validate_frontmatter.py`: no violations); each rule's `runbook_url` points at an existing runbook.
- **running locally** (two stack runs on 2026-10-18, 8-service subset): the target-down drill with timestamps (T0 12:47:19Z stop loki; firing message 12:50:58Z, about 3 m 39 s; recovery message 12:55:58Z, about 4 m 42 s after the restart); the second run proved the rendered summary ("Scrape target loki is down") and the failed-notification path (counter, `GrafanaAlertingFailures` firing, delivery after ntfy returned). Record: `docs/runbooks/records/2026-10-18-target-down-drill.md`.
- Disk rule proven by query only (the expression with a threshold above the current free percent, output recorded); the committed 15 percent stays, no override.
- `docker stats` peak table recorded for the 8-service subset (grafana 559 MiB of 768 m is the driver).
- Gaps: the `[resolved] GrafanaAlertingFailures` message was not seen before `down`; the table is the subset, not the full profile; `make knowledge-index-update` is run by lead-planner in the main checkout after merge.

## Files Changed
`docs/runbooks/README.md`, `target-down.md`, `disk-space.md`, `alerting-pipeline.md`, `docs/runbooks/records/2026-10-18-target-down-drill.md` (new), this ticket and its staging artifacts, `TCK-20261018-GRAFANA-ALERTING-NTFY-AND-BASE-RULES` is the rule source.

## Completion Summary
Runbooks for TargetDown, the disk alerts and the alerting pipeline, a runbook index, and the recorded drill (stop Loki). Running locally on 2026-10-18 (two runs): TargetDown fired 3 m 39 s after the stop and reached ntfy; the resolved message arrived about 4 m 42 s after the restart (group_interval); the second run proved the rendered summary and the failed-notification path. DiskSpaceLow is proven by query only (lead decision), committed threshold 15 percent. The record lists what the rules and runbook got wrong on the first run and how it was fixed, plus the docker stats table.
Gaps: the `[resolved] GrafanaAlertingFailures` message was not seen before the stack was taken down (resolved delivery itself is shown by TargetDown); the stats table is the 8-service subset, not the full profile; one local host. Staging artifacts were written by platform-planner at filing and updated at close. Knowledge index refreshed by lead-planner in the main checkout after merge.
