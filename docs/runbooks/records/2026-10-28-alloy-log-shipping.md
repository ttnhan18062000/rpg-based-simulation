---
status: active
layer: platform
authority: P2
audience: agent
tags: [platform, observability]
---

# Log shipping moved from Promtail to Grafana Alloy (2026-10-28)

**Label: running locally** (VM host ubuntu). Ticket: `TCK-20261021-PROMTAIL-TO-ALLOY-LOG-SHIPPING`. Runbook: [log-shipping.md](../log-shipping.md). Raw files: `agent-working/stored_artifacts/TCK-20261021-PROMTAIL-TO-ALLOY-LOG-SHIPPING/proof-2026-10-28/` (`events.txt`, `guard.txt` (the abort watcher log), `cases.sh`, `cgroup_mem.csv`). Times are UTC, read from those files. Predecessor: [2026-10-20-log-shipping-fix.md](2026-10-20-log-shipping-fix.md).

## 1. Why
Promtail reached end of life on 2026-03-02 (Grafana's migration guide). It is replaced by Alloy v1.20.1 (released 2026-09-28, the newest release at least 14 days old on 2026-10-28), pinned by multi-arch index digest `sha256:2aa2099a...d13f`. What is shipped and labelled did not change.

## 2. Findings before the run (probes, same day)
- Alloy's Docker discovery needs only `CONTAINERS=1` and `NETWORKS=1` on the proxy; with `NETWORKS=0` it fails with the same `403 Forbidden` on `error while computing network labels`. No further proxy endpoint is needed and Alloy has no socket mount.
- The image has bash but no wget or curl; the `/dev/tcp` healthcheck pattern works. Alloy's readiness is `GET /-/ready` on 12345.
- Alloy has no counterpart to promtail's error-level log counter. `prometheus_sd_refresh_failures_total` exists at 0 from a healthy fresh start and rises with every failed refresh. The rule is now `sum(rate(prometheus_sd_refresh_failures_total{job="alloy"}[5m])) + (sum(rate(loki_write_batch_retries_total{job="alloy"}[5m])) or vector(0)) + sum(rate(loki_write_dropped_entries_total{job="alloy"}[5m]))`, no comparison, `noDataState: Alerting`. The retries series appears only after the first retry, hence `or vector(0)` on that term alone.

## 3. The run (up 17:21:10, down without `-v` 18:29:15; 68 minutes)
Stack: backend, redis, prometheus, grafana, loki, alloy, docker-socket-proxy, node-exporter, ntfy, redis-exporter (no tempo, watchdog, ai_worker or frontend). The abort watcher was proven first (dry run printed WOULD DOWN and two lines; real thresholds MemAvailable < 1500 MiB or swap > 7500 MiB; it never triggered: lowest MemAvailable 3976 MiB, highest swap 3009 MiB). The backend image was rebuilt first (src had changed since 2026-10-26).
`TargetDown` was firing for the whole run because `tempo` was not started (`up{job="tempo"}` 0); it is unrelated, and it means this run cannot show `TargetDown{job="alloy"}` separately. Grafana rule state is the "fires" evidence; **ntfy delivery was not re-proven in this run** (proven in #640 and #688).

**Healthy start:** targets are this project's containers only: Loki `container` values are the eight services plus the probe; a second container labelled `com.docker.compose.project=otherproj` and emitting a line every 5 s never appeared. Backend lines are queryable (`{container="platform-backend-1"}`). The backend writes plain text here, so `level` and `component` were proven with a JSON probe container in this project (`{"level":"INFO","component":"probe","tick":N,"message":...}`): stream labels `container`, `job="varlogs"`, `level`, `component` and no `tick` or `message` label. Loki itself adds `service_name` (and the `detected_level` metadata); Alloy sets only the four. `LogShippingErrors` Normal from the first sample, query 0.

| case | start | Pending (first seen) | Alerting (first seen) | back to Normal (first seen) |
|---|---|---|---|---|
| quiet stack (12 one-minute samples from 17:24:59) | 17:24:58 | none | none | always Normal, query 0 |
| 403: proxy `NETWORKS=0` and alloy recreated (throwaway override, deleted, never committed) | 17:38:39 | 17:40:00 | 17:50:08 | 17:55:48 (restore at 17:50:08) |
| alloy stopped | 17:55:48 | 18:01:56 (NoData; the series left the 5 min window) | 18:12:09 | 18:13:14 (start at 18:12:11) |
| Loki unreachable (`stop loki`) | 18:13:14 | 18:13:47 | 18:23:56 | 18:28:00 (start at 18:23:57) |

Pending to Alerting is the 10 minute `for` window in each case. In the Loki case the query rose to 0.064 per second (retries); the dropped-entries term stayed 0 (no batch exhausted its 10 retries in 10 minutes), so the live proof covers the **retries** term; the dropped-entries term is covered by design only. The 403 case rose from 0.003 to 0.18 per second.

## 4. Recreate with no storage volume
With a probe line every 2 s: before `up -d --force-recreate alloy` (17:37:09) Alloy had sent 5535 entries; 90 s after, the counter of the new process read 6031. A new process starts at 0, so it re-sent about 5.4k retained lines in addition to the new ones (read from one counter value; the old container's logs are gone). Loki kept **no gap and no duplicate**: the probe's 432 lines showed ticks 1 to 432, none missing, none repeated (Loki drops an identical timestamp and line). The recreate costs one burst of re-sent lines and no data loss. Decision: no volume, as Promtail's positions in `/tmp` were also lost on recreate.

## 5. Memory (sampler every 5 s, whole run; MiB)
| service | limit | anon max | anon + active_file max | `memory.peak` (reference) |
|---|---|---|---|---|
| alloy | 192 (first guess) | 71.5 | 186.7 | 192.0 |
| loki | 512 | 94.7 | 187.4 | 249.0 |
Alloy's anon + active_file reached 187 of 192, with no headroom, so the limit is raised to **256m** (about 37% above the measured working set). The raised limit itself was not run.

## 6. Not covered
- ntfy delivery for these cases (see above). `TargetDown{job="alloy"}` as a separate alert (tempo kept `TargetDown` firing).
- The dropped-entries term firing; a pending or restart of Loki longer than the 10 retries.
- A fresh-volume Grafana and the 256m limit under load.
- The `service_name` label is added by Loki, not Alloy: inferred from the config and the stream labels; the Promtail run was not repeated for a side-by-side.
