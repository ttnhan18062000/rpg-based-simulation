---
status: active
layer: platform
authority: P2
audience: agent
tags: [platform, observability, performance]
---

# API SLO alert (2026-10-19): scrape on 9109, server-side numbers, and the fire test

**Label: measured**, running locally (VM host ubuntu, Locust on the same host). Tickets: `TCK-20261018-SCRAPE-BACKEND-METRICS-PORT`, `TCK-20261018-API-SLO-ALERT-NTFY-RUNBOOK`. Runbook: [api-latency-slo.md](../api-latency-slo.md). Raw files (steps, samples, events, per-step Locust CSVs) are in `agent-working/stored_artifacts/TCK-20261018-API-SLO-ALERT-NTFY-RUNBOOK/run-2026-10-19/`. Times are UTC. Every figure below was read from those files.

## 1. Method and host
- Host: the VM of [2026-10-18-api-load-test.md](2026-10-18-api-load-test.md) (6 vCPU i5-11400H, 9.7 GiB, KVM). Other sessions were running (load average 1.4 to 3.8, 20 `claude` processes at the manifest).
- Code: branch `platform-implementer-local-slo-alerts` at `305a9761d` (the manifest says dirty only because the monitoring shard was modified), including rpg's R1 (metrics on 9109, #648), R2 (the histogram, #654) and the 0.3 s bucket (#662).
- Stack (the 11-service full profile minus watchdog, ai_worker, frontend): backend, redis, prometheus, grafana, loki, tempo, promtail, docker-socket-proxy, node-exporter, ntfy, redis-exporter. Started with `docker compose -f compose.yaml -f tools/loadtest/compose.loadtest.yaml --profile observability up -d ...`; 990 API keys; Locust 2.46.7 under `systemd-run --user --scope -p MemoryMax=1500M`.
- **The first attempt stopped at the live checks** (2026-10-19 16:29Z): the local backend image dated 2026-10-18 predated R1/R2, so `rpg-backend:9109` was refused and `le="0.3"` was missing. The images were rebuilt (`COMPOSE_PARALLEL_LIMIT=1 docker compose build backend ai_worker`, image created 16:32:14Z), and this record is the second attempt. A preflight now checks the image age and `import src.api.http_metrics` before anything else.
- **Abort watcher, verified:** a dry run with MemAvailable < 99000 MiB printed "WOULD DOWN" and exited without a `down`; the real watcher (PID and stop-file based, thresholds MemAvailable < 1500 MiB or swap > 7500 MiB, runs `down` without `-v` and kills Locust) logged 60 lines, one a minute, from 16:43:51 to 17:42:58 (`guard.log`) and never triggered (MemAvailable 3.88 to 4.02 GB, swap 5.32 to 5.37 GB).

## 2. Live checks (all pass)
- Targets: `grafana`, `loki`, `node-exporter`, `ntfy`, `prometheus`, `redis`, `rpg-backend`, `tempo` all `up`; `sim_current_tick` returns a series; `count by (le) (http_request_duration_seconds_bucket{le="0.3"})` is 1.
- `redis_up` is 1 and `redis_instance_info` reports `redis_version=8.10.2`: the exporter works on Redis 8.
- `GET :8000/metrics` returns 401 (still gated); `:9109` from the host is not reachable (HTTP code 000, connection refused).
- Provisioning loaded: group `base` (5 rules), `cause` (`RedisDown`, `for` 30s) and `slo` (`ApiLatencyP95High`, `ApiErrorRateHigh`, both `for` 2m, `noDataState: OK`, `execErrState: OK`).
- **L-N (Normal while not violated):** the three new rules showed `state=inactive`, `health=ok`, no `lastError`, with their alert instance "Normal (NoData)". Never NoData or Error as a state.

## 3. Age soak and the `/entities` payload (a finding)
`--users 50 --duration 60`, one backend, 20 steps (`soak_table.txt`). The `/entities` response read by curl through the status key:

| steps | `/entities` bytes | req/s (Locust) | p95 ms |
|---|---|---|---|
| 1 to 8 | 11,798 to 11,938 | 373 to 473 | 190 to 240 |
| 9 | 175,379 | 372.8 | 270 |
| 10 | 374,570 | 271.9 | 420 |
| 11 | 558,440 | 202.6 | 580 |
| 12 to 20 | 691,543 to 691,628 | 194 to 260 | 450 to 620 |

The response plateaued at about **691.5 KB**, six consecutive readings within 0.01 percent; my stop test (two equal readings of at least 700,000 B, taken from the 2026-10-18 record) never matched, so the script ran all 20 steps and the plateau was accepted by hand. **The plateau is not the 100-entity page cap**: at the plateau the response held `total 12` entities (`limit 100`), so about 57 KB per entity, against about 7.4 KB per entity in the 2026-10-18 world of 100 entities. What makes the payload grow in the current build was not investigated; the observation is that the payload per entity grows with world age, fast (11.8 KB to 691 KB in about four minutes of 50-user load), and then stops. The 2026-10-18 explanation (growth until the page holds 100 entities) is therefore not the whole story. The SLO text does not change.

## 4. Aged curve: server-side next to Locust (one 60 s repeat per step)
Server numbers come from the R2 histogram over a 55 s window ending at the step end. "SLI" is the alert's selection (`status_class="2xx"`, excluding `route="/health"` and `route="unmatched"`); "all" is every route.

| users | Locust req/s | Locust p50 / p95 / p99 ms | server SLI p50 / p95 / p99 ms | server all p50 / p95 / p99 ms | server req/s |
|---|---|---|---|---|---|
| 10 | 228.3 | 29 / 130 / 190 | 4 / 125 / 228 | 5 / 100 / 223 | 231.1 |
| 25 | 170.4 | 84 / 290 / 400 | 4 / 241 / 393 | 10 / 237 / 372 | 176.9 |
| 50 | 234.5 | 170 / 510 / 680 | 4 / 434 / 706 | 20 / 417 / 635 | 236.6 |

**Server versus client:** the server p95 is 3.8 percent below the client p95 at 10 users (125 vs 130 ms), 17 percent below at 25 users (241 vs 290) and 15 percent below at 50 (434 vs 510). The server p50 is about 4 ms on the SLI routes at every step, against 29 to 170 ms on the client: the server measures handler time, while the client also includes queueing in the one process, the loopback and the Locust loop. **The server SLI is the SLO input; the client number is a conservative bound.**

## 5. Fire test (the committed 0.3 and 0.01 were never edited, no override)
- **Incidental fire during the soak (50 users):** ntfy `[firing] ApiLatencyP95High` at 17:01:05. The load ended at 17:10:31; the rule went Normal at 17:15:52 and the ntfy `[resolved]` arrived at 17:16:17, **about 15 minutes after the load stopped**. That is the 5 minute rate window that must drain from the histogram, plus the policy's 5 minute `group_interval` before the resolved notification is sent.
- **25 users, 9 minutes (17:18:54 to 17:28:05): did not fire.** The server p95 over the 5 minute window sat between 0.222 and 0.239 s, under 0.3, even though Locust's own p95 at 25 users is about 290 ms.
- **50 users (from 17:28:05):** server p95 0.295 s at 17:30:02, 0.373 at 17:31:18 (rule Pending), firing first seen at 17:32:55 (Alerting), ntfy `[firing] ApiLatencyP95High` stamped 17:33:05, **about 5 minutes from the start of the 50-user step to the ntfy message**. The load was stopped at 17:32:58. The rule was Normal at 17:42:52 (window drained) and the ntfy `[resolved]` arrived at 17:43:05.
- ntfy messages (topic redacted): title `[firing]` or `[resolved] ApiLatencyP95High`, priority 4, tag `bell`, text "API p95 latency above 300 ms (2xx, excluding /health and unmatched)" and "Runbook: docs/runbooks/api-latency-slo.md".
- `ApiErrorRateHigh` stayed Normal (NoData) throughout (no 5xx).
- **Side finding:** `DiskWillFillIn24h` (group `base`) fired for `/` at 17:14:51 ("predicted to fill within 24 hours") and resolved at 17:29:51. The image build, the soak and downloads moved free space on `/` enough for `predict_linear` over 6 hours to project a fill. The alert worked as written and is noisy during heavy local work; no rule was changed, and the threshold question goes to lead.

## 6. docker stats (peak over the 24 soak, curve and fire samples; `run.py` USE files)
| service | peak MiB | mem_limit MiB | peak % of limit | peak CPU % of one core |
|---|---|---|---|---|
| grafana | 654 | 768 | 85 | 26 |
| backend | 177 | 1024 | 17 | 191 |
| prometheus | 106 | 512 | 21 | 12 |
| loki | 95 | 512 | 19 | 8 |
| tempo | 50 | 512 | 10 | 4 |
| ntfy | 39 | 64 | 61 | 7 |
| promtail | 34 | 128 | 26 | 11 |
| redis-exporter | 16 | 32 | 51 | 6 |
| docker-socket-proxy | 14 | 64 | 23 | 0 |
| node-exporter | 11 | 32 | 36 | 1 |
| redis | 9 | 256 | 3 | 9 |

Sum of per-service peaks 1,206 MiB; Locust peaked at 58 percent of one core. Grafana at 85 percent of its limit is the one to watch. ntfy never passed 55 MiB under load (one idle reading of 46 MiB right after start was an outlier). The idle readings before and after the load are in `stats_idle.txt` and `stats_final_idle.txt`.

## 7. `simulation.json` panels (a finding for the dashboard ticket)
Instant queries one minute after a fresh start (a young world; some empty panels may fill later). **With data:** World Age, Difficulty Mult, Active Entities, TPS, Calamity Status, Global Gold Circulation, Blacksmith & Shop Volume (both queries), Raw Events (both queries), Technical Errors (`sim_errors_total`). **No series:** Faction Populations, Entity Level Distribution, Total Combat Casualties (`sim_total_deaths_total`), Detailed Phase Profiling (`sim_tick_duration_seconds`), Redis & Kafka Latency Distribution (`sim_redis_latency_seconds`, `sim_kafka_publish_seconds`), Worker Health (`sim_worker_health`) and the invalid-actions query. The two Loki panels were not evaluated. No dashboard was edited; the dashboard ticket waits on R3.

## 8. Limits
One local host with Locust on it; the second attempt of the run (the first stopped at the checks); one 60 s repeat per curve step; the fire test is one run; the soak plateau is a stated acceptance, not an investigated cause; the failure-notification path is covered by the S4 drill record, not here.
