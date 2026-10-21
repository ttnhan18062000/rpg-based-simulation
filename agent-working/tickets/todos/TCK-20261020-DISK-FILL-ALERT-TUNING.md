---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20261020-DISK-FILL-ALERT-TUNING
phase: open
date: 2026-10-20
tags: []
---

# TCK-20261020-DISK-FILL-ALERT-TUNING

## Title
Tune DiskWillFillIn24h so short bursts of heavy local work don't trip it

## Status
OPEN

## Tier
hotfix

## Type
chore

## Priority
P3

## Request Summary
In the 2026-10-19 SLO run (slot b, R1/R2 batch), the `base` rule DiskWillFillIn24h fired for `/` from 17:14:51 to 17:29:51 UTC. An image rebuild, CI downloads and the load-test soak had moved free space on `/` enough for `predict_linear(node_filesystem_avail_bytes[6h], 86400)` to project a fill. The alert worked on a real trend, but heavy local work makes it noisy. Lead decision (2026-10-20): add a runbook note in the R1/R2 batch, file this follow-up, and change nothing until there is evidence.

## Scope
- Collect evidence first: the `/` and `/data` free-space series around heavy runs (builds, load tests, CI downloads), from at least two more occurrences or a stated observation window.
- Then choose one, or both if the evidence supports it:
  - a longer prediction window;
  - a minimum-free-space guard, so it only fires when the projection crosses zero and current free space is below N GB or N %.
- Edit `docker/grafana/provisioning/alerting/rules-base.yaml` and `docs/runbooks/disk-space.md`.
- Re-prove the rule: the provisioning loads, a query shows the new expression, and it stays Normal during a heavy run.

## Out of Scope
- DiskSpaceLow thresholds.
- Other alert rules.
- Any host disk cleanup.

## Acceptance Criteria
- The decision cites the measured series (dates, free-space deltas).
- The rule no longer fires on the 2026-10-19 pattern: the query is replayed over that range, or the next heavy run is observed.
- A real fill trend still fires: proven by query (no env override, the same approach as the S4 disk proof).
- The runbook section is updated.

## Related Tickets
- devops-s4-base-alerts-local (DiskWillFillIn24h origin)
- TCK-20261018-API-SLO-ALERT-NTFY-RUNBOOK (the run that observed it)

## Related Docs
- docs/runbooks/disk-space.md
- docs/runbooks/records/2026-10-18-target-down-drill.md

## Related Stored Artifacts
None.

## Related Code Areas
- docker/grafana/provisioning/alerting/rules-base.yaml

## Assumptions / Open Questions
- `/` had 13 GB free (74 % used) on 2026-10-20. Was the 10-19 trend transient? Evidence decides.

## Implementation Notes
Not started.

## Test Summary
Not started.

## Files Changed
None yet.

## Completion Summary
Not started.
