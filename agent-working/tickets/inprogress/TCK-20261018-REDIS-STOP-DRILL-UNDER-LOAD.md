---
status: active
layer: platform
authority: P1
audience: agent
ticket_id: TCK-20261018-REDIS-STOP-DRILL-UNDER-LOAD
phase: inprogress
date: 2026-10-18
tags: [platform, observability]
---

# TCK-20261018-REDIS-STOP-DRILL-UNDER-LOAD

## Title
The recorded drill: stop Redis under Locust load, follow the runbook, and record detection time, recovery time and a short post-mortem

## Status
INPROGRESS

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
D5's one failure drill, as amended in step 3: stop Redis under load, observe the alert, follow the runbook, and record
the timeline. It is a scripted manual drill, not chaos tooling (ADR exclusion).

## Scope
- **`tools/loadtest/drill_redis_stop.sh`** (or a `run.py` subcommand). It prints a UTC timestamp for each event:
  - Locust starts at a steady step **below** the knee (from the measured record), so the drill tests the failure,
    not overload;
  - T0: `docker compose stop redis`;
  - it waits for the alert to show in the ntfy topic (polling ntfy's JSON endpoint): T1;
  - after a fixed outage window (for example 3 min), `docker compose start redis`: T2;
  - it waits for the alert to resolve: T3;
  - Locust runs on for a fixed tail, then stops.

  It also captures, during the outage:
  - Locust error and latency per 10 s window;
  - backend logs (Loki query, exported);
  - backend `/health`;
  - the stream adapter's behaviour (dropped-event signal if one is exported; log lines otherwise).
- **Hypotheses written down before the run:**
  - the API SLO stays green and the cause alert fires;
  - events published during the outage are lost, not replayed;
  - ai_worker reconnects by itself.
- **Record** `docs/runbooks/records/<date>-drill-redis-stop.md`:
  - the timeline;
  - detection time T1−T0;
  - time to recover T3−T2;
  - user impact (API error and latency during the outage);
  - each hypothesis confirmed or refuted;
  - what the runbook got wrong;
  - follow-up actions, with owners.

  Short blameless post-mortem format. Runbook fixes found here are applied in this PR.

## Out of Scope
- Fixing anything the drill finds in `src` (an fyi to rpg-planner). Repeated or automated chaos runs.

## Acceptance Criteria
- The drill ran once end to end, after asking lead-planner, as one heavy run on its own. The record has real
  timestamps for T0-T3 and the detection and recovery times (**running locally**, a drill record, not a measurement
  of MTTR).
- Each hypothesis is marked confirmed or refuted, with its evidence (a Locust window, a log line, a metric).
- The runbook is updated if the drill showed a gap, or the record says it showed none.
- The stack is back to healthy afterwards, `data/runs` ownership is checked, and only this run's data is cleaned.

## Related Tickets
Epic `TCK-20261018-EPIC-DEVOPS-STEP3-OPERATE-LOCAL`. Needs `TCK-20261018-LOCUST-API-LOAD-TEST`,
`TCK-20261018-API-LOAD-TEST-MEASURED-RUN` (the steady step), `TCK-20261018-API-SLO-ALERT-NTFY-RUNBOOK` and
`TCK-20261018-REDIS-DOWN-CAUSE-ALERT`.

## Related Docs
`docs/architecture/devops_baseline_adr.md` (D5, D7), `docs/runbooks/`

## Related Stored Artifacts
To be created: the drill's raw Locust CSVs and log export.

## Related Code Areas
`tools/loadtest/`, `docs/runbooks/`

## Assumptions / Open Questions
- The record goes to `docs/runbooks/records/` (lead, 2026-10-18).

## Implementation Notes
- `tools/loadtest/drill_redis_stop.sh` is written (syntax checked). It starts Locust headless with `--csv --csv-full-history` at a steady step below the knee (default 10 users), waits HEAD_SECONDS, stops Redis (T0), polls the ntfy topic with a READ token for a `[firing] RedisDown` message (T1), holds the outage for OUTAGE_SECONDS (default 180 s), starts Redis (T2), polls for `[resolved] RedisDown` (T3), runs a tail, then writes captures: `events.txt` (UTC timestamps), `samples.csv` (backend `/health` code, `redis_up`, and the Grafana state of `RedisDown`, `ApiLatencyP95High`, `ApiErrorRateHigh` every 5 s), Locust CSVs (per-second history, to be cut into 10 s windows), the topic's messages with the topic redacted, and the backend's Loki logs for the window. The topic, the reader token and the Grafana password come from gitignored files and are never printed.
- Hypotheses (written before the run, from the ticket): (H1) the API SLO stays green and the cause alert fires; (H2) events published during the outage are lost, not replayed; (H3) ai_worker reconnects by itself.

## Test Summary
- **validated:** `bash -n` on `drill_redis_stop.sh` and `sample_stats.sh`; the sampler was exercised on its own against a probe container and in the re-measure run; the drill script's new lines (sampler start/stop, the Loki WARN) have not run end to end.
- **running locally** (drill run 2026-10-19 17:47Z to 18:00Z; record `docs/runbooks/records/2026-10-19-redis-stop-drill-under-load.md`; evidence `agent-working/stored_artifacts/TCK-20261018-REDIS-STOP-DRILL-UNDER-LOAD/run-2026-10-19/`): Locust 10 users (below the knee), 217,618 requests, 0 failures, 409.9 req/s, p50/p95/p99 18/52/79 ms; Prometheus saw 218,054 responses, all `2xx`; backend `/health` 200 throughout; T0 17:51:29, T1 (ntfy published) 17:52:50, T2 17:54:32, T3 17:57:50; detection 81 s, recovery 3 m 19 s (not a like-for-like speed-up against S4's Loki drill: different rule, `for` and group interval). `ApiErrorRateHigh` and `ApiLatencyP95High` never fired.
- Hypotheses: H1 confirmed (SLO green, cause alert fired); H2 supported, not proven (184 `Redis offline or unreachable` warnings and 1 publish error in the outage window, no replay; the 1000-entry stream cap trimmed the window); H3 confirmed (ai_worker RestartCount 0, consumer group lag 0 afterwards).
- Re-measure (`agent-working/stored_artifacts/TCK-20261018-REDIS-STOP-DRILL-UNDER-LOAD/remeasure-2026-10-19/`, 9 minutes, 10 then 50 users, sampler from before `up`): grafana, promtail and ntfy all below 85 percent on anon (23, 18 and 33 percent) and on anon + active_file (23, 35 and 43 percent); no limit changed; the drill-run `memory.peak` readings at the limits were page cache. The run did not reproduce Grafana's higher use of longer runs.
- Loki finding (read-only snapshot): promtail's Docker discovery finds 0 targets because the `docker-socket-proxy` returns 403 on `GET /networks` (it allows `CONTAINERS=1` only); nothing was sent to Loki. No fix applied.

## Files Changed
(open)

## Completion Summary
(open)
