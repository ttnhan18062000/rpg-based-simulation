---
status: active
layer: platform
authority: P1
audience: agent
ticket_id: TCK-20261018-EPIC-DEVOPS-STEP3-OPERATE-LOCAL
phase: open
date: 2026-10-18
tags: [platform, observability, performance]
---

# TCK-20261018-EPIC-DEVOPS-STEP3-OPERATE-LOCAL

## Title
DevOps step 3 (host ubuntu): a measured Locust API load test, one SLO alert to a local ntfy, a runbook, and a recorded Redis-stop drill

## Status
EPIC_SCOPED

## Tier
epic

## Type
feature

## Priority
P2

## Request Summary
Step 3 of `docs/architecture/devops_plan_amendment_proposal.md` (ADR D5 + D9, Locust instead of k6), moved to host
ubuntu on 2026-10-16 (#618). Method inputs accepted on #541 item 1:
- the USE checklist, naming the resource that saturated first;
- p50/p95/p99 with the run-to-run spread;
- the hardware spec, and whether the session fleet was idle;
- a flame graph through perf-planner's existing py-spy toolkit, labelled separately from the measured run.

The ai_worker lag alert (#541 item 2) waits for rpg's ai_worker `/metrics` on main.

## Scope
Children, in the order in `SEQUENCE.md`:

1. `TCK-20261018-LOCUST-API-LOAD-TEST`: the Locust scenario, a runner that records method and environment, a
   `loadtest` dependency group; registers `tools/loadtest/**` to platform.
2. `TCK-20261018-API-LOAD-TEST-MEASURED-RUN`: the measured run on a quiet host, the dated record, and the profiled
   run through perf-planner.
3. `TCK-20261018-API-SLO-ALERT-NTFY-RUNBOOK`: one Grafana-provisioned SLO alert (threshold from 2), a local ntfy
   container as the contact point, and the runbook; registers `docs/runbooks/**` to platform.
4. `TCK-20261018-REDIS-DOWN-CAUSE-ALERT`: a Redis-down alert that fires when Redis stops, since the API SLO likely
   won't (see Assumptions). **Pending lead's choice of signal.**
5. `TCK-20261018-REDIS-STOP-DRILL-UNDER-LOAD`: stop Redis under Locust load, record detection time, recovery time and
   a short post-mortem.
6. `TCK-20261018-AI-WORKER-SCRAPE-AND-LAG-ALERT`: **BLOCKED** on rpg's ai_worker `:9108/metrics` reaching main.

## Out of Scope
- Any `src/**` change (rpg). New profiling tools (perf's py-spy toolkit is reused, through perf-planner).
- Load tests in CI (D9: never; shared runners are noisy). Driving the simulation tick from the load test (API only).
- A public ntfy topic: the owner hasn't picked one yet, so the contact point is a local container.
- Chaos tooling (ADR exclusion): the drill is a manual, scripted `docker compose stop redis`.

## Acceptance Criteria
- Children 1-5 DONE in one PR from a `platform-implementer-local-*` branch; child 6 may stay open in this folder.
- Evidence uses only D7 labels:
  - **measured**: req/s and p50/p95/p99, with spread, hardware spec, fleet state and commit;
  - **running locally**: alert, ntfy, drill.
- The SLO alert threshold cites the measured run's record, not a guess.
- The drill record gives detection time and recovery time from timestamps (alert fired, ntfy received, Redis
  restarted, alert resolved), not estimates.

## Related Tickets
- Step 2: `TCK-20261018-EPIC-DEVOPS-STEP2-OBSERVABILITY-LOCAL`. Children 2-5 need its dashboard queries and the
  scrape of rpg's request histogram.
- rpg: `TCK-20261014-AI-WORKER-EXPOSES-STREAM-CONSUMER-LAG-AND-PENDING-METRICS` (child 6).
- Issues #541 (method), #618 (host split), #561 (Trivy baseline, used for the runbook's risk notes).

## Related Docs
`docs/architecture/devops_plan_amendment_proposal.md` (step 3), `docs/architecture/devops_baseline_adr.md` (D5, D7, D9),
`docs/engine/performance_contract.md` (measurement vocabulary)

## Related Stored Artifacts
None.

## Related Code Areas
`tools/loadtest/**` (new), `docs/runbooks/**` (new), `compose.yaml`, `docker/grafana/provisioning/alerting/` (new),
`pyproject.toml` + `uv.lock` (lead-owned: a `loadtest` dependency group), `registries/session_roles.yaml` (two globs)

## Assumptions / Open Questions
- **Stopping Redis probably doesn't break the API.** From the code (2026-10-18):
  - `/health` reports engine-thread liveness only;
  - `RedisStreamAdapter` publishes from a background queue with 1 s socket timeouts and counts dropped events;
  - the read routes don't read Redis.

  So the API SLO alert likely stays green during the drill, which is a fair result, but then nothing fires. Child 4
  adds a cause alert. The drill confirms or refutes this hypothesis rather than assuming it.
- **Admission control rate-limits each API key:** a token bucket of 30, refilled at 3/s
  (`src/api/admission_control.py`). One key caps sustained load at about 3 req/s, so the load test would measure the
  limiter. The load test configures many load-test keys (`api_key_hashes` accepts a list) and reports 429s
  separately from 5xx. No `src` change.
- Where the dated load-test and drill records live: proposed `docs/runbooks/records/` (one registered glob). For lead to confirm.
- Host rules: the load runs and the drill are heavy. Ask lead-planner first and run one at a time; lead quiets the fleet for the measured run.

## Implementation Notes
Epic tier: the children carry the implementation.

## Test Summary
See the child tickets.

## Files Changed
See the child tickets.

## Completion Summary
(open)
