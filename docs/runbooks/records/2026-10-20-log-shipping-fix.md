---
status: active
layer: platform
authority: P2
audience: agent
tags: [platform, observability]
---

# Log shipping fix (2026-10-20): promtail discovery was denied by the socket proxy

**Label: running locally** (VM host ubuntu). Ticket: `TCK-20261020-PROMTAIL-DISCOVERY-DENIED-BY-SOCKET-PROXY` (also closes the Grafana fresh-volume gap of `TCK-20261018-OBSERVABILITY-PROFILE-HARDENING`). Runbook: [log-shipping.md](../log-shipping.md). Raw files: `agent-working/stored_artifacts/TCK-20261020-PROMTAIL-DISCOVERY-DENIED-BY-SOCKET-PROXY/` (`fresh-volume-2026-10-20/`, `ab-2026-10-20/`, `proof-2026-10-20/`). Times are UTC and were read from those files.

## 1. The problem
From 2026-10-19 (three runs) Loki had no data: promtail reported healthy, `/targets` showed `docker/tcp://docker-socket-proxy:2375 (0/0 ready)`, `promtail_sent_entries_total` was 0, and every 5 seconds promtail logged `Unable to refresh target groups ... error while computing network labels: ... 403 Forbidden`.

## 2. Cause
Promtail 3.6.8's Docker discovery (`vendor/.../discovery/moby/docker.go` L198-210, `network.go` L36-39 at the loki tag `v3.6.8`) calls the Docker networks API on every refresh to build network labels. The `docker-socket-proxy` allowed `CONTAINERS=1` only, so `GET /networks` returned 403 (`haproxy.cfg` L65 at proxy `v0.4.1` maps `NETWORKS` to the `/networks` path prefix) and every refresh failed before any target was built. A failed refresh sends no update, so the discovery manager never gets a target group (the code path is cited in the ticket's investigation).

## 3. The A/B (2026-10-20, 14:51 to 14:59Z; five containers: redis, backend, loki, proxy, promtail)
| state | targets | entries sent | 403 lines | result |
|---|---|---|---|---|
| A: fresh up, no `NETWORKS` | 0/0 | 0 | 12 in about a minute | reproduces 10-19 |
| B: `NETWORKS=1` (throwaway override) | 5/5 | 325 in 50 s | 0 | logs flow; `container` values are the project's services without loki and promtail; backend lines queryable |
| C: proxy recreated without `NETWORKS`, promtail untouched | 0/0 | rose to 442 in the first seconds, then flat | continues | **does not reproduce the 10-18 observation** |
| C': promtail restarted | 0/0 | 0 | continues | same as A |

In C the five per-container log streams died with the old proxy (`could not transfer logs` at 14:54:58Z) and the targets page fell to 0/0, so **the stale-target hypothesis (old targets keep shipping) is not supported**. The vendored refresh does keep the last good target groups when a refresh fails, but the log streams do not survive the proxy's recreation. The most likely reason 10-18 looked fine is that Loki keeps the lines it already holds: in C and C' the Loki `container` values and recent backend lines stayed visible although nothing new was sent. That is a hypothesis; the 10-18 sequence was not reproduced. Only a rising `promtail_sent_entries_total` or a new line proves current shipping.

Probes through the proxy from inside promtail with `NETWORKS=1` and `POST=0`: `GET /networks` 200, `GET /networks/<id>` 200, `POST /networks/create` 403, `DELETE /networks/<id>` 403, `POST /containers/x/stop` 403, `GET /volumes` 403, `GET /images/json` 403, `GET /info` 403, `GET /containers/json` 200, `GET /version` 200. The widening is `/networks` only.

## 4. The fix and the decision
`NETWORKS=1` on `docker-socket-proxy`, `POST=0` unchanged. Decision: owner via lead-planner, 2026-10-20; the compose comment records what it opens, what it exposes, the reason and the rejected options (a read-only log-file mount in promtail, the Loki Docker driver). The Prometheus job `promtail` (promtail:9080) and the base rule `LogShippingErrors` were added with [log-shipping.md](../log-shipping.md).

## 5. The guard, and two traps found on the way
- **Lead's original design was dropped:** `sum(promtail_targets_active_total) == 0`. That metric is not exported for docker discovery in promtail 3.6.8 (the A and B metric snapshots list every family; none counts targets).
- **Chosen signal:** promtail's own error-level log counter, `sum(rate(loki_internal_log_messages_total{job="promtail",level="error"}[5m]))`, for 10m, `noDataState: Alerting`, `execErrState: OK`. Every failed discovery refresh or push logs one error line, so the counter rises about 12 per minute while discovery is broken and stays flat when healthy, quiet backend or not. `loki_log_messages_total` is a deprecated alias with identical values, so the non-deprecated name is used. The rule fires on errors that recur at least every 5 minutes for 10 minutes; isolated errors further apart do not fire.
- **Trap 1 (noData on a fresh start):** the error series exists at 0 from a fresh promtail (state B, 46 s after its start, showed `level="error"} 0`). Confirmed again on this run's fresh start, section 6.
- **Trap 2 (a comparison inside the PromQL):** the SLO rules embed `> 0.3` and use `noData OK`. Copied here with `noData Alerting`, an embedded `> 0` would make a healthy promtail return an empty result, which is NoData, and fire. So the PromQL has no comparison and the `> 0` is Grafana's threshold step.

## 6. Live proof (run 15:06 to 16:05Z, 58 minutes of a 60-minute hard stop; committed config, HEAD `92c4bc93e`)
Stack: backend, redis, prometheus, grafana, loki, tempo, promtail, docker-socket-proxy, node-exporter, ntfy, redis-exporter (no watchdog, ai_worker or frontend). The abort watcher was proven first (a dry run printed WOULD DOWN; real lines every minute; it never triggered: 4.2 to 5.5 GB available, swap 2.4 to 2.9 GB); the memory sampler ran from before `up`. A temporary read-only ntfy user read the `[firing]` and `[resolved]` messages; it was deleted at the end and its token shredded.

**Fresh start (up 15:07:45):** the proxy env shows `NETWORKS=1`, `POST=0`, `CONTAINERS=1`; promtail targets 11/11 ready; sent entries rising (808 at 15:10:45); 0 lines of the 403; Loki `container` values cover the project's containers; a **new** backend line in Loki at 15:10:46, after `up`; `up{job="promtail"}` 1; `LogShippingErrors` provisioned, state **Normal (never NoData)** and its query returning **0** from the first sample, with the raw `level="error"` counter at 0.

**Quiet stack (iii):** no load; from the first Normal at 15:09:51 to 15:20:55, 43 consecutive samples (about 11 minutes) were Normal with a query value of 0. The rule stayed Normal.

**(ii) A fresh promtail against the 403** (throwaway override `NETWORKS=0`, proxy and promtail recreated at 15:21:17; the override file was deleted afterwards and never committed):
| event | UTC |
|---|---|
| promtail up against the 403 (0/0 targets, 12 lines of 403 in the first minute) | 15:21:17 |
| `LogShippingErrors` Pending (first seen) | 15:21:56 |
| Alerting (first seen) | 15:31:59 |
| ntfy `[firing] LogShippingErrors` published | 15:32:14 |
| restore: proxy and promtail recreated from the committed compose, env `NETWORKS=1` confirmed | 15:32:27 |
| rule Normal (first seen; the 5 minute rate window drained) | 15:37:49 |
| ntfy `[resolved] LogShippingErrors` published | 15:42:14 |
Pending to firing took 10 minutes 3 seconds, which is the `for` window; the resolved message waited for the policy's `group_interval`.

**(i) Promtail stopped** (`docker compose stop promtail` at 15:43:00):
| event | UTC |
|---|---|
| `TargetDown{job="promtail"}` Pending (first seen) | 15:43:56 |
| Alerting (first seen) | 15:46:07 |
| ntfy `[firing] TargetDown` published | 15:46:17 |
| `LogShippingErrors` Pending (NoData) (first seen; the series left the 5 minute window) | 15:48:58 |
| `LogShippingErrors` Alerting (NoData) (first seen) | 15:58:51 |
| ntfy `[firing] LogShippingErrors` published | 15:59:14 |
| `docker compose start promtail` | 15:59:50 |
| both rules Normal (first seen) | 16:00:49 |
| ntfy `[resolved] TargetDown` published | 16:01:17 |
| ntfy `[resolved] LogShippingErrors` published | 16:04:14 |
Both alerts reach ntfy for a stopped promtail: `TargetDown` after about 3 minutes, `LogShippingErrors` (the noData path) after about 16 minutes. Thresholds were never edited. Down at 16:05:37Z without `-v`.

## 7. Memory (sampler, whole 58-minute run; MiB; limit; `docker stats` peak; anon; anon + active_file; `memory.peak` is a reference only because it includes page cache)
| service | limit | docker stats | anon | anon + active_file | memory.peak |
|---|---|---|---|---|---|
| grafana | 1024 | 350 | 259 | 338 | 794 |
| backend | 1024 | 200 | 186 | 190 | 404 |
| prometheus | 512 | 168 | 102 | 166 | 241 |
| loki | 512 | 145 | 87 | 143 | 196 |
| tempo | 512 | 129 | 41 | 128 | 151 |
| promtail | 128 | 62 | 46 | 58 | 82 |
| ntfy | 64 | 61 | 26 | 58 | 64 |
| node-exporter | 32 | 23 | 8 | 23 | 29 |
| redis-exporter | 32 | 22 | 11 | 21 | 24 |
| docker-socket-proxy | 64 | 20 | 11 | 18 | 21 |
| redis | 256 | 17 | 8 | 16 | 43 |
No container was OOM-killed (11 of 11 `oom=false`, restarts 0). Promtail with working shipping peaked at 62 MiB (49 percent of 128m), so 128m stays. **ntfy reached 61 of 64 MiB on the `docker stats` basis (95 percent) but only 26 MiB anon**: its message cache and a long run of notifications fill file cache; the kernel reclaims it and nothing was killed, but the headroom on this basis is thin and a limit decision (keep 64m or raise) is left to the planner. Grafana ran at 350 MiB (34 percent of 1024m) over the hour.

## 8. Limits
One local host; promtail was verified on the five-container A/B and on the 11-container proof; the proof used one run per failure case; the resolved messages depend on the policy's `group_interval`; the 10-18 observation was not reproduced and its explanation is a hypothesis.
