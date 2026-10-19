---
status: active
layer: platform
authority: P2
audience: agent
tags: [platform, observability]
---

# Redis-stop drill under load (2026-10-19): the cause alert fires while the API SLO stays green

**Label: running locally** (VM host ubuntu, Locust on the same host), a drill record and not a measurement of recovery time. Tickets: `TCK-20261018-REDIS-DOWN-CAUSE-ALERT`, `TCK-20261018-REDIS-STOP-DRILL-UNDER-LOAD`. Runbook: [redis-down.md](../redis-down.md). Raw files: `agent-working/stored_artifacts/TCK-20261018-REDIS-STOP-DRILL-UNDER-LOAD/run-2026-10-19/`. Times are UTC and were read from those files. Method and host: the same VM and stack as [2026-10-19-api-slo-alert-fire-test.md](2026-10-19-api-slo-alert-fire-test.md); this run adds `ai_worker`.

## 1. Setup
- Branch `platform-implementer-local-slo-alerts` (drill script from `tools/loadtest/drill_redis_stop.sh`); images rebuilt 2026-10-19T23:32:14+07:00 (backend and ai_worker); Grafana recreated with `mem_limit` 1024m (`docker inspect` Memory=1073741824).
- Stack: backend, redis, ai_worker, prometheus, grafana, loki, tempo, promtail, docker-socket-proxy, node-exporter, ntfy, redis-exporter (no watchdog, no frontend). Locust: 10 users (a step below the aged knee), 990 keys, under `systemd-run --user --scope -p MemoryMax=1500M`.
- Abort watcher: a dry run printed "WOULD DOWN avail=3731 swap=5303" at 17:47:12; the real watcher (MemAvailable < 1500 MiB or swap > 7500 MiB; `down` without `-v`) logged every minute until 18:00:13 and never triggered (3.2 to 3.7 GB available, swap 5.3 to 5.5 GB).
- Before the outage: `RedisDown`, `ApiLatencyP95High` and `ApiErrorRateHigh` Normal; `redis_up` 1; stream `simulation:events` length 1001; consumer group `observatory:consumers` with 1 consumer, pending 0, lag 0, entries-read 25,888; ai_worker started 17:47:35, 0 restarts.

## 2. Hypotheses, written before the run
H1: the API SLO stays green and the cause alert fires. H2: events published during the outage are lost, not replayed. H3: ai_worker reconnects by itself.

## 3. Timeline (UTC)
| mark | time | event |
|---|---|---|
| Locust start | 17:49:59 | 10 users, no think time |
| T0 | 17:51:29 | `docker compose stop redis`; `redis_up` reads 0 at 17:51:32 |
| - | 17:52:03 | `RedisDown` Pending (first seen) |
| - | 17:52:34 | `RedisDown` Alerting (first seen) |
| ntfy | 17:52:50 | `[firing] RedisDown` published (the script saw it at 17:52:51 = **T1**) |
| T2 | 17:54:32 | `docker compose start redis` (outage 183 s); `redis_up` reads 1 at 17:54:39 |
| - | 17:54:54 | `RedisDown` Normal (first seen) |
| ntfy | 17:57:50 | `[resolved] RedisDown` published (the script saw it at 17:57:51 = **T3**) |
| Locust stop | 17:58:51 | after a 60 s tail |

**Detection T1 - T0 = 81 s.** **Recovery T3 - T2 = 3 m 19 s.** The S4 Loki drill measured 3 m 39 s and 4 m 42 s. **These are not a like-for-like speed-up**: S4 stopped Loki and alerted on `TargetDown` (`for: 2m`, group interval 1 m), while this run alerts on `RedisDown` (`for: 30s`, group interval 30 s); the recovery time is dominated by the notification `group_interval` in both. Messages: title `[firing]` or `[resolved] RedisDown`, priority 4, tag `bell`, "Redis is down (cause alert): events are being lost while the API keeps serving", "Runbook: docs/runbooks/redis-down.md".

## 4. User impact
Locust sent 217,618 requests over the whole run with **0 failures**, 409.9 req/s, p50/p95/p99 18 / 52 / 79 ms. Prometheus saw **218,054 responses, all `status_class="2xx"`: no 4xx and no 5xx**, and none in the outage window. Backend `/health` returned 200 on every 15 s sample, including during the outage. `ApiLatencyP95High` and `ApiErrorRateHigh` never fired; only `RedisDown` did.

## 5. Hypotheses, result
- **H1 confirmed:** the SLO stayed green, and the cause alert fired within its `for` window plus one evaluation.
- **H2 supported, not proven:** the backend logged 184 `Redis offline or unreachable: Error -3 ... name resolution` warnings and 1 `RedisStreamAdapter failed to publish event` error between 17:51 and 17:56, and only 2 such warnings after the restart, with no replay line. The loss could not be read back from the stream: `simulation:events` is capped at about 1000 entries (about 12 seconds of events), so the outage window had already been trimmed.
- **H3 confirmed:** ai_worker was not restarted (RestartCount 0, StartedAt 17:47:35 before and after). It logged `RedisStreamConsumer read error: Connection closed by server` and then repeated `failed to connect/create group ... name resolution` during the outage; afterwards the consumer group had 1 consumer, pending 0, lag 0, entries-read 26,293.

## 6. Memory: what is and is not known
The drill script of this first run did not sample `docker stats`. At the end of the run `docker stats` showed Grafana at 713 MiB of 1 GiB. The cgroup `memory.peak` since container start read exactly the limit for Grafana (1024 MiB), promtail (128 MiB) and ntfy (64 MiB), but **`memory.peak` includes page cache, which the kernel reclaims, so it does not show real use and is not comparable with the `docker stats` figures of the earlier records**. No container was OOM-killed (all `OOMKilled=false`, restarts 0). The headroom of Grafana's new 1024m limit (the 2026-10-19 SLO record measured 654 MiB, 85 percent of the old 768m) was therefore **not measured here**. The re-measure with a memory sampler is in section 8.

## 7. Loki had no data in this run: the cause (snapshot, no fix applied)
`/loki/api/v1/labels` returned no labels and the backend-log export was empty although promtail reported healthy. A read-only snapshot in the re-measure run (section 8; files in `remeasure-2026-10-19/loki/`) shows why:
- Promtail `/targets`: `docker/tcp://docker-socket-proxy:2375:80 (0/0 ready)`, so discovery found **0 targets**. `promtail_sent_entries_total` and `promtail_sent_bytes_total` are 0 (nothing dropped, nothing sent); Loki is `ready`, its labels list is empty and `loki_ingester_chunks_created_total` is 0.
- Promtail's log repeats every 5 s (13 times in its last 50 lines): `msg="Unable to refresh target groups" discovery=docker ... err="error while computing network labels: Error response from daemon: <html><body><h1>403 Forbidden</h1> Request forbidden by administrative rules."`.
- Reading it: promtail's `docker_sd_configs` calls the Docker **networks** API to build network labels on every refresh. The `docker-socket-proxy` allows `CONTAINERS=1` and `POST=0` only (the `NETWORKS` section defaults to off), so `GET /networks` returns 403 and the whole refresh fails. A direct probe from inside the promtail container confirmed it: `GET /containers/json` through the proxy returns 200 (the project filter works, `COMPOSE_PROJECT_NAME` is `platform` inside the container), `GET /networks` returns 403.
- It is therefore neither a starved promtail nor a wrong project filter: it is the proxy allow-list missing `NETWORKS`. Whether this changed with a newer promtail or proxy, or never worked, was not checked. No fix was applied (a `NETWORKS=1` change widens the proxy's read surface and is a decision, filed as a follow-up by the planner).

## 8. Re-measure: memory (sampler on from before `up`) and the load
Run `remeasure`, 2026-10-19 18:03:50Z to 18:12:46Z, the same 12-service stack as the drill, **9 minutes**. Load: 10 users for 180 s (65,812 requests, 0 failures, 366.5 req/s, p50/p95/p99 20/61/96 ms) then 50 users for 240 s (104,501 requests, 0 failures, 436.6 req/s, 100/220/320 ms). The abort watcher (dry run printed WOULD DOWN; 2+ real lines before any load; never triggered, 3.2 to 3.9 GB available, swap 5.5 GB) and the sampler (docker stats every 5 s; cgroup memory.current, anon, active and inactive file, file and peak) ran throughout; the sampler started before `up`, so first-start peaks are included. No container was OOM-killed (12 of 12 `oom=false`, restarts 0). The drill script's new lines (the sampler start and stop, the Loki WARN) have **not** been run end to end; here the sampler ran on its own.

Peaks over the whole run, MiB (limit; `docker stats` already leaves out inactive file cache; "anon + active_file" is the figure to judge a limit on; `memory.peak` is for reference only because it includes cache):

| service | limit | docker stats | anon | anon + active_file | anon % | anon + active % | memory.peak (ref) |
|---|---|---|---|---|---|---|---|
| grafana | 1024 | 247 | 234 | 239 | 23 | 23 | 351 |
| backend | 1024 | 157 | 134 | 151 | 13 | 15 | 196 |
| prometheus | 512 | 119 | 93 | 117 | 18 | 23 | 130 |
| loki | 512 | 102 | 71 | 100 | 14 | 20 | 118 |
| promtail | 128 | 46 | 23 | 45 | 18 | 35 | 58 |
| ai_worker | 512 | 45 | 37 | 42 | 7 | 8 | 52 |
| tempo | 512 | 40 | 38 | 38 | 8 | 8 | 40 |
| ntfy | 64 | 29 | 21 | 27 | 33 | 43 | 44 |
| redis | 256 | 25 | 7 | 23 | 3 | 9 | 32 |
| docker-socket-proxy | 64 | 14 | 11 | 12 | 17 | 19 | 15 |
| node-exporter | 32 | 13 | 7 | 12 | 22 | 38 | 15 |
| redis-exporter | 32 | 12 | 10 | 12 | 32 | 36 | 14 |

**Limit verdicts (no limit was changed):** grafana, promtail and ntfy are all far below the 85 percent line on anon alone (23, 18 and 33 percent) and on anon + active_file (23, 35 and 43 percent). The `memory.peak` readings at exactly 1024, 128 and 64 MiB in the drill run were page cache and file cache, not use. **Caveat for Grafana:** this run lasted 9 minutes with no alert firing and no notification sent; Grafana's higher figures (654 MiB `docker stats` under the old 768m limit in the SLO record, 713 MiB at the end of the drill) came from runs of an hour or more with alert evaluation and firing. So this run does not reproduce the highest Grafana use, and it says nothing about what it grows to over a long session. The 1024m limit stays; a longer observation is the open question.

## 9. What the runbook got wrong, and follow-ups
- The runbook said the ai_worker is "expected to reconnect by itself"; it did, and the record now marks it confirmed.
- The runbook's first check names Loki logs; in this stack Loki had no data (section 7: promtail's discovery is denied by the proxy), so `docker compose logs backend` is the working fallback until that is fixed.
- Follow-ups: the Loki ingestion ticket (planner; the `NETWORKS` allow-list decision), a longer Grafana observation, and an rpg question (not a platform fix): the stream publish error is logged per attempt (184 warnings in 5 minutes) and there is no drop counter, so the loss is visible only in logs.

## 10. Limits
One local host with Locust on it; one drill run at one load step; the outage was 183 s; H2 is supported by logs only; the memory re-measure was 9 minutes and did not reproduce Grafana's higher use of longer runs.
