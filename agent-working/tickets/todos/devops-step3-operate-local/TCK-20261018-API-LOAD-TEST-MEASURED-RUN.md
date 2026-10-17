---
status: active
layer: platform
authority: P1
audience: agent
ticket_id: TCK-20261018-API-LOAD-TEST-MEASURED-RUN
phase: open
date: 2026-10-18
tags: [platform, performance, benchmarking]
---

# TCK-20261018-API-LOAD-TEST-MEASURED-RUN

## Title
The measured API load-test run on host ubuntu: req/s and p50/p95/p99 with spread, the USE result, and a separately labelled profiled run

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
D9: one honestly measured throughput figure, which sets D5's latency SLO threshold. #541 item 1 sets the method. This
is the run itself, on a quiet machine that lead-planner arranges, and its dated record.

## Scope
- **Pre-flight** (ask lead-planner first; lead coordinates the quiet window with perf and the others):
  - ≥ 2.5 GB available and swap ≤ 7.5 GB;
  - the fleet's state recorded (idle, or which sessions are running);
  - the default profile only, observability off. That keeps Grafana, Loki and Tempo off the CPU budget. A second,
    shorter pass with observability on gives the overhead figure.
- **Measured run:** the runner from `TCK-20261018-LOCUST-API-LOAD-TEST` at its fixed user steps, R ≥ 3 repeats. Record:
  - req/s;
  - p50/p95/p99 per step (median and min-max across repeats);
  - 5xx, 429 and timeout rates;
  - the USE table and the first saturated resource;
  - the knee: the last step before p95 or errors climb.
- **Profiled run, labelled separately.** Ask perf-planner to run its existing py-spy toolkit
  (`tools/perf/_profiling_common.py`, `profile_api_payload.py`) against the backend at the knee step, while the load
  runs. This ticket gets back the flame graph and perf's reading. No new profiling tool. The profiled run's numbers
  are never mixed into the measured table.
- **Record:** `docs/runbooks/records/<date>-api-load-test.md` (location confirmed by lead, 2026-10-18), with frontmatter. Contents:
  - the method (link to the README);
  - the manifest values;
  - the tables;
  - the flame graph (or a link to perf's stored artifact);
  - the proposed SLO threshold, derived from the measured p95 at a stated operating load with a stated margin;
  - limits: VM host, Locust on the same host, engine running in the same process.

  Raw CSVs go to this ticket's stored artifacts. Any staged `stored_artifacts/**/*.json` that `.gitignore` hides gets
  force-added or converted (memory: review committed content).

## Out of Scope
- Changing admission limits, the engine or any `src` (rpg). Any optimisation: findings go to perf-planner / rpg-planner as fyi.
- CI. A capacity claim beyond this host (performance_contract vocabulary: this is one host's local measurement).

## Acceptance Criteria
- The record holds every #541 item: the USE checklist with the first saturated resource; p50/p95/p99 with spread;
  the hardware spec; the fleet state; the commit; and the profiled run labelled separately (**measured**).
- Every figure in the record traces to a CSV file in the stored artifacts.
- The proposed SLO threshold, and how it was derived, are stated for `TCK-20261018-API-SLO-ALERT-NTFY-RUNBOOK`.
- Run data is cleaned by run id afterwards. `data/runs` ownership is checked after compose: compose leaves root-owned
  files (memory).

## Related Tickets
Epic `TCK-20261018-EPIC-DEVOPS-STEP3-OPERATE-LOCAL`. Needs `TCK-20261018-LOCUST-API-LOAD-TEST`. Needs step 2's
request histogram only if the record also cites server-side latency (preferred: Locust's client-side numbers
plus the server's p95 from the dashboard side by side).

## Related Docs
`docs/architecture/devops_baseline_adr.md` (D5, D7, D9), `docs/engine/performance_contract.md`

## Related Stored Artifacts
To be created: this ticket's raw CSVs and manifest.

## Related Code Areas
`tools/loadtest/`, `docs/runbooks/records/` (new)

## Assumptions / Open Questions
- If the host can't be made quiet, the run is labelled "measured, fleet active" with the fleet state, not dropped.
  Lead-planner decides whether that is enough to set the SLO.

## Implementation Notes
(open)

## Test Summary
(open)

## Files Changed
(open)

## Completion Summary
(open)
