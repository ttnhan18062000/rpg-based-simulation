---
status: active
layer: platform
authority: P2
audience: agent
ticket_id: TCK-20261020-PROMTAIL-DISCOVERY-DENIED-BY-SOCKET-PROXY
artifact_type: investigation
tags: [platform, observability]
---

# Investigation: TCK-20261020-PROMTAIL-DISCOVERY-DENIED-BY-SOCKET-PROXY

## Symptom (measured 2026-10-19, three runs)
- Loki is empty: `/loki/api/v1/labels` returns nothing, and `loki_ingester_chunks_created_total` and `promtail_sent_entries_total` are both 0.
- Promtail `/targets`: `docker/tcp://docker-socket-proxy:2375 (0/0 ready)`.
- Promtail logs, every 5 s: `Unable to refresh target groups ... error while computing network labels: ... 403 Forbidden`.
- A probe from inside promtail: `GET /containers/json` with the project filter returns 200, and `GET /networks` returns 403.
- Evidence: `docs/runbooks/records/2026-10-19-redis-stop-drill-under-load.md` §7, and `agent-working/stored_artifacts/TCK-20261018-REDIS-STOP-DRILL-UNDER-LOAD/remeasure-2026-10-19/loki/`.

## Config on main
- `docker/promtail-config.yml`: one `docker_sd_configs` job against `tcp://docker-socket-proxy:2375`, refresh every 5 s, filtered by the label `com.docker.compose.project=${COMPOSE_PROJECT_NAME}`. Its relabels drop loki and promtail and set `container` and `job`.
- `compose.yaml` docker-socket-proxy (tecnativa v0.4.1, digest-pinned): `CONTAINERS=1`, `POST=0`, the socket mounted `:ro`, internal network only. The comment already states the residual risk: `GET /containers/*/json` exposes every container's env.
- `git log -S NETWORKS -- compose.yaml` is empty: NETWORKS was never committed.

## The 10-18 counter-evidence and how it resolves
- TCK-20261018-OBSERVABILITY-PROFILE-HARDENING's runtime check (2026-10-18, promtail 3.6.8 from #604 on 10-16) recorded: "NETWORKS=1: not needed. Without it the proxy returns 403 on GET /networks (logged every refresh) ... backend logs keep arriving". It also saw Loki `container` values for 9 project containers.
- Leading hypothesis: those were stale targets. Prometheus-style discovery (the code promtail vendors) builds network labels on every refresh. When that call fails, the refresh returns an error, and the discovery manager keeps the last good target groups. If NETWORKS=1 was on when promtail first discovered its targets, and the proxy was then recreated without it, the tailing would carry on while the 403 got logged on every refresh. A fresh promtail against a 403 never gets targets, and that is the 2026-10-19 state.
- So the 10-18 "not needed" verdict was most likely a flawed test, not a later regression. The promtail-version hypothesis (#604) is weak: that version was already in use on 10-18.
- To confirm, the A/B run tests the three states (test_plan.md). The implementer also cites the vendored code path (the moby/docker discovery refresh that calls NetworkList, and the error it returns), with a file and line from the promtail 3.6.8 source tag, read on GitHub. No clone is needed.

## Fix options
1. **Proxy `NETWORKS=1`** (recommended if the A/B confirms the cause). tecnativa/docker-socket-proxy maps each section env var to a path prefix. With `POST=0`, only GET and HEAD go through, so `NETWORKS=1` opens `GET /networks` (list) and `GET /networks/{id}` (inspect), and nothing that writes.
   - What it exposes: network names, IDs, drivers, subnets and gateways, plus each network's attached-container IDs and IPs. promtail's container access already exposes all of that except the IPAM details. That is a small widening next to the existing `/containers/*/json` env exposure.
   - The implementer verifies that `POST /networks/create` and `DELETE /networks/x` return 403, and that `GET /networks` returns 200.
2. **Mount `/var/lib/docker/containers` read-only in promtail** with a static file path (no discovery). It needs no proxy change, but promtail then reads EVERY container's log on the host: other sessions' stacks and the MCP servers. The project filter is lost, so container names would have to be derived from file paths. HARDENING removed this mount for least privilege. It is a wider exposure than option 1. Rejected.
3. **The Loki Docker logging driver** (`grafana/loki-docker-driver`). It needs a host plugin install (`docker plugin install`, owner and host-level, run as root in dockerd), and a `logging:` block on every service. It bypasses promtail entirely, so the relabels, the `json` pipeline stages and the `level`/`component` labels move into driver options or are lost. When Loki is down the driver can block or drop container logs (the documented `mode: non-blocking` caveats). It is a host change outside compose and a bigger blast radius. Rejected for a local stack.
4. **Alloy** (`discovery.docker`). It uses the same discovery code and the same `/networks` call, so it needs option 1 anyway. Out of scope here (a separate Promtail → Alloy follow-up).

## Guard against silent recurrence
- Promtail exposes `promtail_targets_active_total`, but Prometheus has no promtail job today (docker/prometheus.yml). The plan adds a promtail scrape job (`promtail:9080/metrics`) and a `base` rule `LogShippingStalled`: `sum(promtail_targets_active_total) == 0` for 10m (discovery health; noData → Alerting). Not "zero entries sent": an idle stack can log nothing for 10 minutes (lead, 2026-10-20). An optional "stuck" signal: Loki push errors, `sum(rate(promtail_request_duration_seconds_count{status_code!~"2.."}[5m])) > 0`, or dropped entries > 0. Promtail being down is TargetDown's job (the new promtail job), plus noData. It links a runbook section.
- The runbook checks (target-down.md, alerting-pipeline.md) get "promtail targets > 0".

## Step 1: the code path, read on GitHub at the tags (read-only, 2026-10-20; no clone, no stack)
Promtail 3.6.8 is the `grafana/loki` tag `v3.6.8` (object 138c391f..., the revision promtail prints in its own log). Paths below are in that tree, under `vendor/github.com/prometheus/prometheus/discovery/`.
- **The refresh that fails** (`moby/docker.go`): `DockerDiscovery.refresh` is at line 198. It first lists the containers with the project filter (`d.client.ContainerList`, line 203; an error is wrapped at line 205 as `error while listing containers`). It then calls `getNetworksLabels` (line 208) and, if that errors, returns `nil, fmt.Errorf("error while computing network labels: %w", err)` (lines 209 and 210). That is the exact string promtail logged.
- **The call the proxy denies** (`moby/network.go`): `getNetworksLabels` (line 36) starts with `client.NetworkList(ctx, network.ListOptions{})` (line 37) and returns the error unchanged (lines 38 and 39). The networks are used to add `__meta_docker_network_*` labels (the `networkLabels[n.NetworkID]` lookups at `docker.go` lines 293 and 313), so there is no config switch that skips the call: it runs on every refresh, before any target is built. With `CONTAINERS=1` and no `NETWORKS`, `GET /networks` is 403 and every refresh fails after the container list succeeded.
- **What the refresh loop does with a failed refresh** (`refresh/refresh.go`): `Discovery.Run` makes an initial refresh at line 68. On error it only logs `Unable to refresh target groups` (line 71) and sends nothing (the `else` that sends `tgs` on the channel is lines 73 to 78). Inside the ticker loop (line 85 onwards) a failed refresh logs (line 90) and then `continue`s (line 92), skipping the `ch <- tgs` send at lines 95 to 98. **A failed refresh sends no update at all.**
- **What the discovery manager does with silence** (`manager.go`): the updater (line 336) only changes the target set when a message arrives on the provider's channel (`case tgs, ok := <-updates`, line 343), through `updateGroup` (called at line 354; defined at line 408), which replaces a group by its `Source`, or deletes it only when the new group is empty (lines 421 to 426). No code path removes targets because refreshes fail. So: after the first successful refresh, later failed refreshes leave the old groups in place (state C: stale but live targets, the 10-18 observation); and if the first refresh fails, the manager never gets a group (states A and C': 0 targets, which is what 10-19 showed).
- **Conclusion for the hypothesis:** the code supports the stale-target explanation. The 10-18 HARDENING run saw working targets while the proxy had no `NETWORKS`, and that is possible only if promtail had a good refresh earlier (an earlier proxy with `NETWORKS`, or a proxy recreated afterwards) and kept those groups. It does not prove that is what happened on 10-18; the A/B states A, B and C test it.

## Step 1b: the proxy rules at tecnativa/docker-socket-proxy v0.4.1 (tag object a6fbf383...), `haproxy.cfg`
- Line 48: `http-request deny unless METH_GET || { env(POST) -m bool }`. With `POST=0` anything that is not GET (or HEAD, which `METH_GET` includes) is denied for every section: `POST /networks/create` and `DELETE /networks/<id>` would be 403 with or without `NETWORKS`.
- Line 65: `http-request allow if { path,url_dec -m reg -i ^(/v[\d\.]+)?/networks } { env(NETWORKS) -m bool }`. The section variable maps to the **path prefix** `/networks` (optionally with a version prefix), so `NETWORKS=1` opens `GET /networks` (list) and `GET /networks/<id>` (inspect) and nothing else; line 77 is the final `http-request deny`. This matches the ticket's description of option 1. The surface probe in the A/B still confirms it live.

## A/B run, 2026-10-20 (slot 2; running locally; evidence in `ab-2026-10-20/`)
Stack: redis, backend, loki, docker-socket-proxy, promtail (`up -d --no-deps`; Grafana and Prometheus were not started because Loki is queried directly and the A/B does not need them; the only other containers on the host were the github-mcp ones, untouched). Up at 14:51:50Z, down at 14:59:45Z without `-v`; the abort watcher was proven (dry run WOULD DOWN; real lines every minute, 4.6 to 4.9 GB available, swap 2.4 GB, never triggered) and the sampler ran from before `up`. The NETWORKS override file was throwaway, under the run directory, and was deleted afterwards (not committed).

| state | UTC | targets page | `promtail_sent_entries_total` | 403 "network labels" lines (cumulative in `docker logs`) | Loki `container` values | backend lines in the last 5 min |
|---|---|---|---|---|---|---|
| A: fresh up, no NETWORKS | 14:52:49 | 0/0 ready | 0 | 12 | none (labels empty) | 0 |
| B: NETWORKS=1 (override), proxy + promtail recreated | 14:53:49 | 5/5 ready | 325 | 0 | backend, docker-socket-proxy, redis (no loki or promtail) | 5 |
| C: proxy recreated without NETWORKS, promtail untouched | +60 s 14:55:59 | 0/0 ready | 442 (rose in the first seconds, then flat) | 12 in the minute | same (older lines) | 5 (older) |
| C, +3 min | 14:58:00 | 0/0 ready | 442 (flat) | 36 | same | 5 (older) |
| C': promtail restarted | 14:59:21 | 0/0 ready | 0 | continues | same (older) | 5 (older) |

- **A reproduces 10-19:** 0 targets, 0 entries sent, empty Loki labels, one 403 per 5 s.
- **B fixes it:** with `NETWORKS=1` and nothing else, the five project containers become targets, entries flow (325 within 50 s, 20 successful pushes), `container` values are exactly the project's running services minus loki and promtail (the relabel drop works), and backend lines are queryable. Loki's own and promtail's own lines: 0.
- **C does NOT reproduce the 10-18 observation, so the stale-target hypothesis is not supported as stated.** After the proxy was recreated without NETWORKS the targets did not keep shipping: promtail logged `could not transfer logs` for all five docker targets at 14:54:58Z (the long-lived log streams died with the old proxy), the targets page fell to 0/0, and `promtail_sent_entries_total` stayed at 442 for the following minutes. The vendored refresh does keep the last good groups when a refresh fails (Step 1), but the per-container log streams are tied to the proxy connection and do not survive its recreation. So "stale targets that keep shipping" is not what happens when the proxy is recreated.
- **What probably explains 10-18:** the Loki label and line queries do not prove current shipping: the Loki container keeps the lines it already holds (here, `container` values and the "last 5 minutes" backend lines stay visible in C and C' although nothing new was sent). On 10-18 a running Loki that had received logs earlier (from a promtail that did not call `/networks`, or before the proxy change) would answer the same queries. The only reliable live signals are `promtail_sent_entries_total` rising, and the 403 lines. That is a hypothesis; I could not reproduce the 10-18 sequence, and the proxy had been recreated for the hardening change on 10-18 as well.
- **C' (promtail restart without NETWORKS) = A:** 0 targets, 0 entries.

### B-surface probes (from inside promtail, with `NETWORKS=1`, `POST=0`; HTTP/1.0 status lines)
| request | status |
|---|---|
| `GET /networks` | 200 |
| `GET /networks/<platform_default id>` | 200 |
| `POST /networks/create` | 403 |
| `DELETE /networks/ab00000000000000` (a made-up id) | 403 |
| `POST /containers/x/stop` | 403 |
| `GET /volumes` | 403 |
| `GET /images/json` | 403 |
| `GET /containers/json` | 200 |
| `GET /version` | 200 |
| `GET /info` | 403 |
The widening with `NETWORKS=1` is `/networks` only: every write is denied by `POST=0`, and the GET sections for volumes, images and info stay closed.

### Guard finding: `promtail_targets_active_total` does not exist for docker targets
The plan's guard `sum(promtail_targets_active_total) == 0` cannot work: promtail 3.6.8 exports no active-target gauge for the docker discovery. Its metric families are `promtail_docker_target_entries_total`, `promtail_docker_target_parsing_errors_total`, `promtail_sent_entries_total`, `promtail_sent_bytes_total`, `promtail_dropped_*`, `promtail_encoded_bytes_total`, `promtail_request_duration_seconds` and `promtail_batch_retries_total` (the A and B metric files are in the evidence). In state A the docker-target and sent counters exist at 0; in B they count up; no series says how many targets exist. Candidate guards, for the planner to choose: (1) a rule on a Loki query (no lines from any project container for 10 minutes) which also fires on a quiet backend; (2) `rate(promtail_sent_entries_total[10m]) == 0` for 10m, which the plan rejects because an idle stack sends nothing; (3) `promtail_request_duration_seconds_count` rate, same weakness; (4) a log-based rule on promtail's own 403 line, which only works if promtail's logs reach Loki (they are dropped by design); (5) a cheap probe sidecar or a scrape of the proxy's access path (not available: haproxy exposes no counters here). None is exact; (1) with a long window on a stack whose backend logs every tick is the least bad.

### Memory (sampler, whole run)
Peaks, MiB (limit; docker stats; anon; anon + active_file): promtail 128; 127; 28; 126, docker-socket-proxy 64; 29; 11; 27, loki 512; 212; 73; 209, backend 1024; 126; 120; 122, redis 256; 14; 6; 13. No OOM kill (5 of 5 `oom=false`, restarts 0). The promtail 127 MiB is the first sample after creation at 14:51:55Z; it was 16 MiB at 14:53:02Z and 42 to 46 MiB while shipping in B (about 35 percent of its 128m), so it is a startup transient of file cache, not the working set.
