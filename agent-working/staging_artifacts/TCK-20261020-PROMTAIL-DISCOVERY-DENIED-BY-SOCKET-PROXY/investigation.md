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
- Promtail exposes `promtail_targets_active_total`, but Prometheus has no promtail job today (docker/prometheus.yml). The plan adds a promtail scrape job (`promtail:9080/metrics`) and a `base` rule `LogShippingStalled`: `sum(promtail_targets_active_total) == 0` for 10m, OR (with the stack up) `sum(rate(promtail_sent_entries_total[15m])) == 0`. noData maps to Alerting, because the metric missing means promtail is gone. It links a runbook section.
- The runbook checks (target-down.md, alerting-pipeline.md) get "promtail targets > 0".
