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
The drill script of this first run did not sample `docker stats`. At the end of the run `docker stats` showed Grafana at 713 MiB of 1 GiB. The cgroup `memory.peak` since container start read exactly the limit for Grafana (1024 MiB), promtail (128 MiB) and ntfy (64 MiB), but **`memory.peak` includes page cache, which the kernel reclaims, so it does not show real use and is not comparable with the `docker stats` figures of the earlier records**. No container was OOM-killed (all `OOMKilled=false`, restarts 0). The headroom of Grafana's new 1024m limit (the 2026-10-19 SLO record measured 654 MiB, 85 percent of the old 768m) was therefore **not measured here**. A re-measure with a memory sampler (anon, active and inactive file, peak) is pending; its result goes in section 8.

## 7. Loki had no data in this run
`/loki/api/v1/labels` returned no labels and the backend-log export was empty (0 streams) although promtail reported healthy. The log evidence in section 5 comes from `docker compose logs`. The cause is not investigated here; a snapshot of promtail and Loki is pending (section 8).

## 8. Pending re-measure
Grafana, promtail and ntfy memory with the anon and file split, and the promtail and Loki ingestion snapshot: to be filled after the re-measure run.

## 9. What the runbook got wrong, and follow-ups
- The runbook said the ai_worker is "expected to reconnect by itself"; it did, and the record now marks it confirmed.
- The runbook's first check names Loki logs; in this stack Loki had no data (section 7), so the `docker compose logs backend` form should be given as the fallback once the cause is known.
- Follow-ups: the Loki ingestion ticket (planner), the memory limits decision after the re-measure, and an rpg question (not a platform fix): the stream publish error is logged per attempt (184 warnings in 5 minutes) and there is no drop counter, so the loss is visible only in logs.

## 10. Limits
One local host with Locust on it; one drill run at one load step; the outage was 183 s; H2 is supported by logs only; the memory headroom and the Loki state are pending.
