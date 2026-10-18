---
status: historical
layer: platform
authority: P2
audience: agent
ticket_id: TCK-20261018-API-LOAD-TEST-MEASURED-RUN
artifact_type: plan
tags: [platform, observability]
---

# Plan: TCK-20261018-API-LOAD-TEST-MEASURED-RUN

**Written retrospectively at ticket close (2026-10-18).** The plan was given in platform-planner's dispatch messages and the ticket Scope; this file records it after the fact.

## Plan (from the ticket Scope and the dispatch)
1. Pre-flight (lead clears each window): available memory >= 2.5 GB, swap <= 7.5 GB, fleet state recorded, default profile only with observability off for the throughput run.
2. Measured run with the runner from `TCK-20261018-LOCUST-API-LOAD-TEST`: users 10/25/50/100/200, 60 s, 3 repeats.
3. Profiled run labelled separately (lead decision B, 2026-10-18): py-spy 0.4.2 `record --nonblocking --rate 100 --duration 90` at the knee step through `tools/loadtest/compose.profile.yaml` (`SYS_PTRACE` for the profiled hold only; owner-approved 2026-10-18); flame graph via `tools/perf`'s `folded_to_speedscope`.
4. A shorter pass with observability on for the overhead figure.
5. Write the dated record `docs/runbooks/records/2026-10-18-api-load-test.md` with the proposed SLO text.
6. Windows 2 and 3 were added after the first run showed a throughput decline that follows backend age: an age soak and aged profile, a fresh-backend curve, and an aged curve at the `/entities` page cap.
7. Clean run data by run id and check `data/runs` ownership afterwards.

Commits: e6d71be4c, 888a0761b, c043472ca, 10d04ed24, f3a1a8cfc. Raw data: `agent-working/staging_artifacts/TCK-20261018-API-LOAD-TEST-MEASURED-RUN/`.
