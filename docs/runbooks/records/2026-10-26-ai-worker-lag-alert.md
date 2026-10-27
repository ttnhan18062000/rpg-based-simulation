---
status: active
layer: platform
authority: P2
audience: agent
tags: [platform, observability]
---

# ai_worker scrape and lag alerts: observation and fire test (2026-10-26)

Ticket `TCK-20261018-AI-WORKER-SCRAPE-AND-LAG-ALERT`. One stack run on the ubuntu host, 16:31:53Z to 17:06:33Z (slot from lead-planner, one heavy run at a time), images rebuilt first (image age 58 s, `lag_metrics` imported inside the container). Raw output: `tools/loadtest/runs/20261026T163228Z-ai-worker-lag/` (gitignored). Abort watcher `stack_guard.sh` real mode before `up` (MemAvailable < 1500 MiB, swap used > 3500 MiB); it never triggered. Host: MemAvailable low 5237 MiB, swap high 1947 MiB (baseline 1892). No Locust load: the engine publishes to `simulation:events` by itself (the stream stays near its 1000-entry maxlen) and that is the load the consumer sees.

## 1. Scrape, healthcheck, scale
- Target `ai_worker` up, container `healthy` (python urllib check of `sim_stream_consumer_up 1.0`, `start_period` 15 s) about 1 minute after `up`.
- `--scale ai_worker=2` (16:56Z): **two** `ai_worker` targets up (two container IPs on 9108, from `dns_sd_configs`), both containers healthy. Scaled back to 1. Checked for targets and health only; alerting was not exercised with two replicas.
- Labels: `instance` is a container IP; the rules aggregate `max by (stream, group)` (group `observatory:consumers`, stream `simulation:events`).

## 2. Observation, thresholds
- Baseline 5 minutes (16:36 to 16:41Z, 46 samples): lag 0, pending 0. Over the whole 30-minute window (including the scale test and the drain after the restart): lag peaked at 7, pending at 9.
- Stream trim point: the adapter writes with `maxlen=self.max_queue_size, approximate=True`, default `max_queue_size=1000` (`src/observability/stream/adapters.py` lines 99 and 198). Stream length read 1000 to 1003 throughout; during the outage redis' own lag read 1000 to 1006 within 20 s of the stop, so a stopped consumer reaches the trim point (entries lost) in seconds.
- `AiWorkerLagHigh` > 500: half of the trim point, about 70 times the normal peak of 7. It warns while half the stream is still undelivered.
- `AiWorkerPendingHigh` > 100, on its own reasoning: pending counts entries delivered to a consumer and not acknowledged. The consumer reads 50 entries per `xreadgroup` call (`src/observability/stream/consumer.py` line 184), so a healthy worker holds at most about one batch (normal peak 9 over 30 min, 0 at baseline); above 100 is two full batches unacknowledged, which means it is not finishing what it takes (a hang or crash mid-processing). That is about 10 times the normal peak and 10 percent of the stream. Not provoked in this run (see section 5), so this one is the weakest-evidenced number.
- `for` 2 m, interval 30 s. Based on this one 30-minute window, not a long-run distribution; revisit if a heavier engine load shows higher normal peaks.

## 3. Fire test (ai_worker stopped while the engine publishes)
| Event | UTC |
|---|---|
| T0: `docker compose stop ai_worker` (both rules Normal) | 16:58:00 |
| `AiWorkerLagHigh` Pending (no lag series, noData Alerting) | within the first evaluation |
| `AiWorkerLagHigh` Firing in Grafana | 17:00:40 |
| ntfy `[firing] AiWorkerLagHigh` | 17:01:00 (3 m 00 s after the stop) |
| ntfy `[firing] TargetDown` (job `ai_worker`) | 17:01:17 |
| T2: `docker compose start ai_worker` (redis lag 1003) | 17:01:11 |
| lag back to 0 (first reads after the restart) | within 10 s |
| `AiWorkerLagHigh` Normal in Grafana | by 17:01:35 |
| ntfy `[resolved] AiWorkerLagHigh` | 17:06:00 (4 m 49 s after the restart) |

`AiWorkerPendingHigh` stayed Normal (noData OK).

Latency: firing took 3 m 00 s (30 s evaluation interval + the 2 m `for` + the policy's group wait). Resolving took 4 m 49 s although the rule was Normal by 17:01:35: Grafana sends the resolved message at the notification group's next flush, and that is the policy's group interval (about 5 minutes), not the evaluation interval, the same shape as the TargetDown drill (resolved about 4 m 42 s after the restart). So a fire takes about 3 minutes and a resolve up to about 5.

Side effect observed: `GrafanaAlertingFailures` fired at 16:37:13Z and resolved at 17:02:17Z. The first provisioning of `rules-worker.yaml` still held the threshold placeholders, so the threshold node failed to parse and the rules errored on every evaluation; I replaced them with the numbers above before the fire test. This is a second, accidental proof that the failures alert works. The committed rules do not have the fault.

The ntfy topic id was exposed locally in a terminal once during the run (a documented `ntfy access` command echoed it); the value is in no committed file. The temporary ntfy reader user was removed after the run.

## 4. Idle worker and fresh start
- Fresh start: both rules `inactive` (Normal) after the restart of Grafana with the final files.
- Idle worker: backend (engine) stopped 17:03:01 to 17:03:31Z, `simulation:events` length flat (1003 to 1003): `sim_stream_consumer_lag` stays a series with value 0, `sim_stream_consumer_up` 1, both rules Normal. An idle but running worker does not trigger the noData path.

## 5. Not tested
Pending above 100 was not provoked (no crash mid-message was staged); the pending rule is proven only as Normal in all states above. The Redis-down case (collector yields only `up 0`, so the lag rule goes NoData and fires with `RedisDown`) follows from the collector code and was not run here.
