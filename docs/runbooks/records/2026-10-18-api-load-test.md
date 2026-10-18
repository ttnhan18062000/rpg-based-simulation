---
status: active
layer: platform
authority: P2
audience: agent
tags: [platform, observability, performance]
---

# API load test (2026-10-18): age effect, /entities page cap and proposed SLO

**Label: measured**, running locally (VM host, Locust on the same host). Ticket: `TCK-20261018-API-LOAD-TEST-MEASURED-RUN`.
Raw CSVs, manifests, `profile*.raw` and the speedscope JSON are in
`agent-working/staging_artifacts/TCK-20261018-API-LOAD-TEST-MEASURED-RUN/` (moved to `stored_artifacts/` at ticket close).

**Headline.** The first run looked like a throughput collapse as users rise (410 → 116 req/s). It was not: it was the backend
getting slower with age, because `GET /api/v1/entities` returns a page whose size grows with the entity count until it
holds 100 entities (about 745 KB). Capacity at that cap is a flat ceiling of about 145 req/s at any user count from 10 to 100.
The run was a method finding, not a saturation curve.

## 1. Method and host

- Runner: `tools/loadtest/run.py` (method and flags in [`tools/loadtest/README.md`](../../../tools/loadtest/README.md)). Locust 2.46.7, headless, closed-loop users with no think time.
- Route mix (weight): `/api/v1/observability/live/status` 3, `/api/v1/state` 2, `/api/v1/observability/live/health` 2, `/api/v1/entities` 1, `/health` 2 (no auth). 990 API keys used round-robin per request (ceiling 2970 req/s before per-key 429s).
- Host: 6 vCPU VM (VirtualBox, `oracle`), Intel i5-11400H, about 9.9 GB RAM, 8 GB swap. Default compose profile, observability off, unless stated. Backend `mem_limit` 1 GB.
- Commit `888a0761b` (tree dirty: ticket text only). Backend image `sha256:3e30f117befa…`. Image is non-root (uid 1000).
- Fleet state (from the manifests): 16 `claude` processes plus their MCP servers and 7 github-mcp containers; other seats were asked to hold heavy work. Load average about 2 before the runs.
- The engine runs in the backend process and was running during every step (about 8 ticks/s; see the engine columns).

## 2. Run 1: baseline (5 steps × 3 repeats × 60 s, one backend that ages through the run)

| users | req/s median (min–max) | p50 ms | p95 ms | p99 ms | backend CPU peak | Locust CPU peak | 429 / 5xx |
|---:|---|---:|---:|---:|---:|---:|---|
| 10 | 409.6 (392.1–445.9) | 19 | 51 | 72 | 150% | 55% | 0 / 0 |
| 25 | 227.7 (175.0–321.2) | 93 | 250 | 360 | 152% | 42% | 0 / 0 |
| 50 | 116.1 (108.0–123.5) | 370 | 930 | 1200 | 157% | 27% | 0 / 0 |
| 100 | 125.9 (124.8–145.6) | 630 | 1500 | 1900 | 161% | 30% | 0 / 0 |
| 200 | 134.8 (131.2–141.7) | 640 | 2900 | 14000 | 149% | 30% | 0 / 0 |

The saturation rule printed "host_cpu at 25 users (run queue 14 on 6 vCPUs)". Read with section 3 it does not describe a load limit.
**Why this is not a saturation curve:** the steps ran one after another on the same backend, so user count and backend age moved
together. Throughput fell while users rose, which closed-loop users should not do. The widest spread (25 users, 175–321 req/s) is
the step where the decline was steepest. Locust stayed at 27–55% of one core, so the load generator was not the limit.
Zero 429s and zero 5xx in every step; the 9 pool 429s seen in the smoke run (open item 6b) did not reproduce.

## 3. Age soak (same backend, 50 users, 12 repeats × 60 s)

`--users 50 --duration 60 --repeats 12 --label age-soak`, one fresh backend (started with the profiling overlay, which only adds `SYS_PTRACE`).

| repeat | req/s | p50 ms | p95 ms | `/entities` avg bytes | engine ticks/s |
|---:|---:|---:|---:|---:|---:|
| 0 | 445.6 | 100 | 200 | 69,427 | 8.46 |
| 1 | 424.1 | 110 | 210 | 83,996 | 8.42 |
| 2 | 354.8 | 130 | 280 | 160,305 | 8.44 |
| 3 | 249.6 | 180 | 400 | 295,109 | 8.31 |
| 4 | 223.7 | 200 | 450 | 386,372 | 8.15 |
| 5 | 192.4 | 240 | 520 | 494,570 | 8.01 |
| 6 | 162.4 | 270 | 630 | 622,050 | 7.76 |
| 7 | 155.5 | 280 | 690 | 734,195 | 7.46 |
| 8 | 145.7 | 310 | 700 | 744,977 | 7.77 |
| 9 | 139.9 | 330 | 750 | 744,977 | 7.91 |
| 10 | 158.7 | 270 | 690 | 744,977 | 7.49 |
| 11 | 143.7 | 310 | 760 | 744,977 | 7.90 |

The other four routes stay flat in every repeat (`live/health` 289–291 B, `live/status` 374–376 B, `/api/v1/state` 72–74 B, `/health` 244 B).
**Mechanism.** `GET /api/v1/entities` takes `limit` with default 100 (`src/api/server.py` lines 241–248, `offset: int = 0, limit: int = 100`).
The locustfile calls it without parameters, so the response grows with the entity count until the page holds 100 entities, then
stops: 744,977 B, about 7.4 KB per entity. That is one request in ten carrying about 99% of the bytes. The engine tick rate is flat
(8.5 → 7.5–7.9 ticks/s) over the soak, so the engine is not what slows down. The 69 KB of repeat 0 is already an averaged
value over a growing world; a first curl on the fresh backend returned 21 KB.
The state of the world at the start of each run is not fixed; that is the confounder in section 2.

## 4. Profiles: fresh and aged (PROVISIONAL)

py-spy 0.4.2 (host static binary, read-only mount), `record --pid 1 --nonblocking --rate 100 --duration 90 --format raw`, attached about 15 s into a
25-user, 120 s hold, with `tools/loadtest/compose.profile.yaml` (`SYS_PTRACE` for the profiled hold only; owner-approved 2026-10-18).
Label: py-spy nonblocking 100 Hz attached during the hold; latency during the hold is not a measured figure.

| | fresh backend | aged backend (after the soak) |
|---|---:|---:|
| req/s during the hold (not a measurement) | 377.0 | 144.4 |
| samples (py-spy nonblocking errors) | 9,044 (1,164) | 9,821 (518) |
| stacks: API / engine / other | 68% / 17% / 15% | 68% / 20% / 11% |
| pydantic `dump_python` | 10.4% | 22.2% |
| gzip `_write_raw` | 6.4% | 11.7% |
| json `iterencode` | 6.8% | 11.6% |
| `admission_control._prune_idle_clients` | 7.8% | not in the top |
| `present_entity` (state_presenter.py:97) | not in the top | 5.2% |

Flame graphs (speedscope JSON from py-spy raw, via `tools/perf`'s `folded_to_speedscope`; open at speedscope.app):
`profile.speedscope.json` (fresh) and `profile-aged.speedscope.json` (aged), next to `profile.raw` and `profile-aged.raw`.
The stack split (API/engine/other) comes from simple path matching, not a call-graph analysis. The shift toward serializing and compressing
the response fits the payload growth in section 3.

## 5. Fresh-backend curve (comparison only, small world)

A fresh backend per user step (`up -d --force-recreate backend`, wait healthy), `--duration 60 --repeats 3`, default warm-up, no profiling overlay.
This measures a small world and is not the SLO source. Limit: each step still ages the backend during its three repeats, so the step is
not strictly fresh (the 50-user spread of 322–448 shows it).

| users | req/s median (min–max) | p50 | p95 | p99 | backend CPU peak | Locust CPU peak | ticks/s per repeat |
|---:|---|---:|---:|---:|---:|---:|---|
| 10 | 415.6 (401.5–464.4) | 19 | 49 | 67 | 173% | 53% | 8.61, 8.59, 8.30 |
| 25 | 511.4 (493.0–513.4) | 40 | 89 | 120 | 151% | 56% | 8.53, 8.48, 8.47 |
| 50 | 430.2 (322.0–447.6) | 100 | 210 | 300 | 159% | 51% | 8.38, 8.31, 8.60 |
| 100 | 509.6 (499.6–535.0) | 180 | 350 | 410 | 155% | 58% | 8.26, 8.31, 8.22 |
| 200 | 482.0 (444.6–510.0) | 210 | 790 | 920 | 142% | 60% | 8.42, 8.74, 8.61 |

Flat at about 415–510 req/s with the backend at 140–175% of one core, close to what one process can do with the GIL plus native work. Latency is the only knee (p95 49 ms at 10 users, 790 ms at 200). 0 429 and 0 5xx.

## 6. Aged curve (the SLO source)

Method: a fresh backend (default profile, observability off, no profiling overlay), then `--users 50 --duration 60 --repeats 1 --warmup 0 --baseline-seconds 0 --label pre-age`
in a loop, measuring the `/entities` size after each pass with `curl` through the status key (the key is never printed). Stop when two consecutive readings are equal and at least 700,000 B.
curl readings: 21,179 (fresh), 71,406; 71,274; 108,629; 191,822; 297,609; 367,255; 446,854; 551,135; 658,935; 744,599; 744,599 (11 passes).
Then `--users 10,25,50,100 --duration 60 --repeats 3 --label aged-curve` on the same backend. **Cap proof:** `/entities` is 744,599 B by curl
before the curve and 744,599 B after it; Locust's average content size is 744,977 B (the 378 B difference is not investigated). The curve ran entirely at the cap.

| users | req/s median (min–max) | p50 | p95 | p99 | backend CPU peak | Locust CPU peak | ticks/s per repeat |
|---:|---|---:|---:|---:|---:|---:|---|
| 10 | 144.9 (139.7–145.1) | 56 | 200 | 280 | 147% | 25% | 7.68, 7.80, 7.85 |
| 25 | 146.1 (143.7–147.9) | 140 | 410 | 510 | 155% | 26% | 7.87, 7.30, 7.60 |
| 50 | 151.9 (146.5–164.3) | 280 | 680 | 840 | 156% | 30% | 7.01, 7.83, 7.63 |
| 100 | 146.1 (139.3–146.3) | 570 | 1400 | 1700 | 153% | 31% | 7.62, 7.61, 7.92 |

0 429 and 0 5xx. Engine: ticks 5,938 → 12,787 over the curve; governor and health DEGRADED at the start and end of each step (SURVIVAL at the start of the 50-user step).
**Reading.** Throughput is a flat ceiling of about 145–152 req/s at every user count, and latency grows in proportion to users (a closed loop: users ≈ req/s × latency).
The soak at 50 users at the cap gives about 140–160 req/s with p95 690–760 ms: the provisional plateau.
**Saturation-rule caveat.** The runner printed "host_cpu at 25 users (run queue 17)". The rule fires on the first step where throughput does not grow while p95 rises,
and on a flat curve that is the second step; it does not mean a CPU limit appears at 25 users. The knee of the aged backend with this mix is at or below 10 users.

Per-route latency at 10 users (aged, context only; three repeats, ms; p95 median in brackets):

| route | p50 | p95 | p99 | req/s |
|---|---:|---:|---:|---:|
| `/api/v1/entities` | 120–130 | 270–280 (280) | 350–360 | 13.8–14.1 |
| `/api/v1/state` | 77–83 | 220–230 (220) | 290–310 | 27.8–28.4 |
| `/health` | 77–79 | 220–230 (220) | 290–320 | 27.8–29.4 |
| `/api/v1/observability/live/status` | 15 | 100–110 (100) | 170–190 | 42.1–44.5 |
| `/api/v1/observability/live/health` | 14–15 | 99–110 (110) | 170 | 27.8–30.7 |
| all (aggregated) | 56–57 | 190–200 (200) | 280 | 139.7–145.1 |

`/health` and `/api/v1/state` are tiny yet show p95 220 ms: at the cap, cheap routes queue behind `/entities` in the one process.

## 7. Proposed SLO (accepted by lead-planner 2026-10-18 as proposed; the owner approves the text at PR time)

> API p95 ≤ 300 ms over 5 min and 5xx < 1%, at the `/entities` page cap (100 entities, about 745 KB), on this host spec, load-test route mix,
> concurrency ≤ 10 clients (about 145 req/s ceiling).

Basis: p95 200 ms at 10 users (median of 3) × 1.5 margin; p95 410 ms at 25 users, so an alert on this SLO would fire beyond about 15 concurrent clients at the cap.
The alert ticket stays BLOCKED until `rpg` R2 (#622); this record wires nothing.

## 8. Other stack checks (running locally)

- **Observability on** (fresh stack, `--users 50,100 --duration 60 --repeats 1`): 421.5 and 424.0 req/s, p95 220 and 420 ms. Peak CPU: Grafana 121%, backend 168%, everything else under 9%. Throughput is within the fresh curve's spread (415–510 req/s); this is not a paired comparison (the runs were taken at different times). The visible cost is the Grafana CPU and the extra memory of the stack.
- **Grafana whitespace guard:** PASS. A whitespace-only secret makes Grafana exit with `docker/secrets/grafana_admin_password is empty or admin` and restart-loop; the secret was restored (sha256 identical) and Grafana returned healthy.
- **Grafana fresh-volume check:** PENDING, it needs the owner's direct yes to remove `platform_grafana_data`.
- **Watchdog:** `exec watchdog id` is `uid=1000(app) gid=1000(app)` on the rebuilt image. The first observability start in this window showed uid 0 because the `platform-watchdog` image was stale (built before the non-root change; an earlier build ran without the observability profile).
- `find data -uid 0` after the observability starts lists only the old run dir from before the watchdog ran; the watchdog wrote nothing there.

## 9. Side findings

- **Access-log volume.** One uvicorn access line per request; the lines carry no timestamps, so the per-minute rate is derived from req/s: about 26.7k lines/min at the start of the soak (445.6 req/s) and 8.4–9.5k lines/min at the plateau. The profiled-aged backend container held 233,381 log lines, of which 231,929 were `GET` access lines. Logging is `rpg`'s; not changed here.
- **Idle-client prune loop.** `admission_control._prune_idle_clients` was 7.8% of samples on the fresh backend with the 990-key pool. It is a candidate for `rpg`, not proven to matter at a smaller pool.
- **Engine budget warnings.** The profiled fresh backend logged 186 `exceeded budget` warnings (181 at `end_of_tick`, 5 at `mid_tick`) and one non-fatal "SimQ hub construction failed"; no ERROR, no traceback, no timeout.
- **Item 6b** (the 9 pool 429s at 5 users in the smoke run): not reproduced; no failure rows in any step of any run here.
- A per-step engine reading exists from commit `f83cbde54` onwards; run 1 (baseline) and the first fresh/profiled holds predate it, so only the start-of-run engine state is recorded for them.

## 10. Limits

- VM host (VirtualBox), 6 vCPUs shared with Locust and with the other Claude sessions on the machine; the numbers are for this host spec only.
- Locust runs on the same host as the backend (it used 25–60% of one core).
- The engine runs in the same process (and under the same GIL) as the API; there is no way to separate them in this setup.
- One route (`/api/v1/entities`, weight 1 of 10) carries about 99% of the bytes at the cap; the mix is a load-test mix, not a production mix.
- The fresh curve is not strictly fresh within a step. The aged curve is at the page cap only because `limit` defaults to 100; a different default changes the ceiling.
- The age effect has a mechanism with evidence (payload growth, profile shift, engine ticks flat) but the entity count itself was not read directly; the SLO is for the capped state.
- The SLO is not wired until `rpg` R2 (#622); this is a proposal.
