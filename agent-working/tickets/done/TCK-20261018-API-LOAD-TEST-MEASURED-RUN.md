---
status: historical
layer: platform
authority: P1
audience: agent
ticket_id: TCK-20261018-API-LOAD-TEST-MEASURED-RUN
phase: done
date: 2026-10-18
tags: [platform, performance, benchmarking]
---

# TCK-20261018-API-LOAD-TEST-MEASURED-RUN

## Title
The measured API load-test run on host ubuntu: req/s and p50/p95/p99 with spread, the USE result, and a separately labelled profiled run

## Status
DONE

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
- **Profiled run, labelled separately.** perf parameters, run by platform (lead decision B, 2026-10-18): py-spy 0.4.2 (host static binary, read-only mount) `record --nonblocking --rate 100 --duration 90` against uvicorn at the knee step, via `tools/loadtest/compose.profile.yaml` (`SYS_PTRACE`, profiled hold only; owner-approved 2026-10-18). Output: py-spy raw (folded) plus a speedscope flame graph made with tools/perf's `folded_to_speedscope`, both in this ticket's stored artifacts. No new profiling tool, no SVG converter dependency. perf-planner may send a reading as an fyi; that's optional, not a dependency. The profiled run's numbers are never mixed into the measured table.
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
- Profiling overlay (prep, 2026-10-18): `tools/loadtest/compose.profile.yaml` adds only `cap_add: [SYS_PTRACE]` and a read-only mount of `${PY_SPY_BIN:?...}` at `/opt/py-spy` to the backend. Used for the profiled hold only; the throughput and obs-on runs never load it. Command and the label text ("py-spy nonblocking 100 Hz attached during the hold; latency during the hold is not a measured figure") are in `tools/loadtest/README.md` ("Profiled hold"). The `/proc` PID lookup there has not been run yet.
- PR-body item: SYS_PTRACE in tools/loadtest/compose.profile.yaml only: owner-approved security choice, 2026-10-18.

## Test Summary
- Prep: `compose -f compose.yaml -f tools/loadtest/compose.loadtest.yaml -f tools/loadtest/compose.profile.yaml config -q` passes with PY_SPY_BIN set and fails with 'required variable PY_SPY_BIN is missing a value' without it; the two-file config (no overlay) has no SYS_PTRACE. Loadtest, compose hygiene, platform domain and repo-root tests: 36 passed.
- Window 2026-10-18 (lead CLEAR via planner). Raw data in `agent-working/staging_artifacts/TCK-20261018-API-LOAD-TEST-MEASURED-RUN/` (`run-baseline-…`, `run-profiled-…`, `run-obs-on-…`, `profile.raw`, `profile.speedscope.json`). Fleet (manifest figure): 16 `claude` processes plus their MCP servers and 7 github-mcp containers; other seats held heavy work. Commit 888a0761b, tree dirty (ticket text only). Locust run in a systemd scope (MemoryMax 2G) with its own scratch venv (locust 2.46.7). Memory stayed at about 5.5-5.9 GB available, swap 2.4 GB.
- Baseline (default profile, observability off, 990 keys, ceiling 2970 req/s, 0.0% 429 and 5xx, no failure rows): users 10 / 25 / 50 / 100 / 200 -> req/s median 409.6 / 227.7 / 116.1 / 125.9 / 134.8; p95 51 / 250 / 930 / 1500 / 2900 ms; backend CPU peak 150-161% of one core; Locust CPU peak 55 / 42 / 27 / 30 / 30%; idle baseline host CPU 12%. Saturation flag: host_cpu at 25 users.
- Throughput FALLS with users in the baseline, which closed-loop users should not do. A fresh backend (profiled hold, 25 users) gave 377 req/s, and the obs-on pass (fresh stack, 50 and 100 users) gave 421.5 and 424.0 req/s. So the decline is not an effect of user count; it follows the backend's age or state in the first run. Cause unproven. Open for the next run: one step on a fresh backend, repeated after a soak; check `_prune_idle_clients` with a 990-entry client table (7.8% of samples in the profile). Superseded by windows 2-3: cause shown as /entities payload growth to the page cap (record §3, §6).
- Profiled hold (PROVISIONAL; py-spy nonblocking 100 Hz attached during the hold; latency during the hold is not a measured figure): 9044 samples; by stack about 68% API, 17% engine, 15% other; top leaves `queue._run` 10.6%, pydantic `dump_python` 10.4%, json `iterencode` 6.8%, gzip `_write_raw` 6.4%. Flame graph: speedscope JSON from py-spy raw, via tools/perf.
- Observability on (`--users 50,100 --duration 60 --repeats 1`): 421.5 / 424.0 req/s, p95 220 / 420 ms; peak CPU Grafana 121%, backend 168%, all others under 9%.
- 6b: no 429 in any step (zero failure rows), the 9 pool 429s did not reproduce.
- Whitespace-guard check: PASS (Grafana exits and restart-loops with the guard message on a whitespace-only secret; secret restored, sha256 identical, Grafana healthy).
- Grafana fresh-volume check: still PENDING (the owner has not told the implementer directly).
- Watchdog: in window 1 `id` was uid 0 because `platform-watchdog` was a stale image from before the non-root change (the earlier `docker compose build` ran without `--profile observability`). Fixed in window 2: after `docker compose --profile observability build watchdog` and an observability start, `exec watchdog id` = `uid=1000(app) gid=1000(app)`.
- Engine tick rate per step: not captured in window 1 (the status key was read once per run). From commit `f83cbde54` the runner reads it at the start and end of every repeat; windows 2 and 3 have it (about 7.0-8.7 ticks/s in every step).
- Windows 2 and 3 (age soak, fresh and aged py-spy profiles, fresh-backend curve, aged curve at the `/entities` cap): results are in `docs/runbooks/records/2026-10-18-api-load-test.md` sections 3-6; the raw run dirs are in this ticket's stored artifacts.

## Files Changed
`tools/loadtest/compose.profile.yaml`, `tools/loadtest/README.md` (profiled-hold prep).
`docs/runbooks/records/2026-10-18-api-load-test.md` (new), `registries/session_roles.yaml` and `.claude/agents/session-platform-{implementer,planner}.md` (`docs/runbooks/**` owned by platform), `tools/loadtest/run.py`, `tools/loadtest/summary.py` and `tests/tools/test_loadtest_summary.py` (per-step engine reading, commit `f83cbde54`), the stored artifacts of this ticket, this ticket.

## Completion Summary
The measured run, the age soak, the fresh and aged py-spy profiles, the fresh-backend curve and the aged curve at the `/entities` page cap were run on 2026-10-18 and are recorded in `docs/runbooks/records/2026-10-18-api-load-test.md` (label: measured, running locally). Raw CSVs, manifests, `profile*.raw` and the speedscope JSON are in this ticket's stored artifacts (the `.json` files are force-added because `.gitignore` hides `stored_artifacts/**/*.json`).

Main result: the baseline's throughput fall (409.6 -> 116-135 req/s) follows backend age, not user count. `GET /api/v1/entities` (default `limit=100`, `src/api/server.py` lines 241-248) grows from about 69 KB to 744,977 B; at that cap the ceiling is about 145-152 req/s at every user count from 10 to 100. Proposed SLO (accepted by lead-planner as proposed; the owner approves the text at PR time): API p95 <= 300 ms over 5 min and 5xx < 1%, at the `/entities` page cap, on this host spec, load-test route mix, concurrency <= 10 clients (about 145 req/s ceiling). The SLO is not wired until rpg R2 (#622).

Gaps: the Grafana fresh-volume check was not run (needs the owner's direct yes to remove `platform_grafana_data`); the profiles are PROVISIONAL (py-spy nonblocking errors 1164/9044 and 518/9821); the fresh curve is comparison only; `make knowledge-index-update` was not run (on hold). Run dirs written by this session were removed by run id. PR-body items: SYS_PTRACE only in `tools/loadtest/compose.profile.yaml`, owner-approved 2026-10-18; staging artifacts for the closed tickets were written at close, not before implementation.
