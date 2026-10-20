---
status: active
layer: platform
authority: P1
audience: agent
ticket_id: TCK-20261018-OBSERVABILITY-PROFILE-HARDENING
phase: open
date: 2026-10-18
tags: [platform, observability, security]
---

# TCK-20261018-OBSERVABILITY-PROFILE-HARDENING

## Title
Compose: Grafana admin password from a secret file (no `admin` default), host ports bound to 127.0.0.1, Promtail's Docker socket behind a read-only proxy

## Status
INPROGRESS

## Tier
standard

## Type
repair

## Priority
P2

## Request Summary
Carry-ins 3-5 from the u24 platform-planner on #618. Grafana falls back to the password `admin`. Prometheus, Grafana,
Loki (and Redis, which has no auth) publish their ports on all interfaces. Promtail mounts `/var/run/docker.sock`
with full API access. These need fixing before step 2 adds more services, and before the step-3 drill. Promtail is
deprecated (Grafana Alloy replaces it), but migrating it is out of scope here.

## Scope
- **Grafana password, without breaking the default profile.** The carry-in suggested `${GRAFANA_ADMIN_PASSWORD:?…}`.
  Checked by platform-planner on 2026-10-18 with Compose v5.1.1: a required variable fails **every** profile, so
  `docker compose up` (default, no Grafana) would fail too. Use a compose secret instead:
  - top-level `secrets: grafana_admin_password: file: ./docker/secrets/grafana_admin_password`, `.gitignore`d;
  - grafana gets `secrets: [grafana_admin_password]` and `GF_SECURITY_ADMIN_PASSWORD__FILE=/run/secrets/grafana_admin_password`;
  - remove `GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD:-admin}`.

  Checked the same way: a missing secret file leaves `config -q` and the default `up` working, and makes
  `--profile observability up` fail at Grafana's start ("bind source path does not exist"). That is the fail-fast we
  want. Add a one-line note at the top of `compose.yaml` on how to create the file (for example
  `openssl rand -base64 24 > docker/secrets/grafana_admin_password`). Grafana must refuse to start, or the stack must
  fail, when the file is empty. Check which one happens and record it.
- **Bind host ports to loopback:** `127.0.0.1:${PROMETHEUS_PORT:-9090}:9090`, the same for Grafana 3000, Loki 3100 and
  **Redis 6379** (Redis has no password; the carry-in didn't list it). backend 8000 and frontend 8080 stay as they
  are: they are the app's own ports.
- **Promtail's socket.** Mounting the socket `:ro` does **not** make the Docker API read-only (a client can still
  connect to the socket and POST). Put a socket proxy in front of it, allowing only the read calls
  `docker_sd_configs` needs (container list, inspect and logs; no POST, no exec). One pinned image, for example
  `tecnativa/docker-socket-proxy` with `CONTAINERS=1`, `POST=0`, by digest, with a `mem_limit`, in the
  `observability` profile, on the internal network only. Point promtail at `host: tcp://docker-socket-proxy:2375`.
  The proxy is now the only service that mounts the socket, read-only. Record the remaining risk in a compose comment.
- While in `docker/promtail-config.yml`: the drop rule matches `/rpg-sim-e2e-(loki|promtail)-1`, a project name this
  compose file no longer produces. Match on the compose service label instead
  (`__meta_docker_container_label_com_docker_compose_service`), so the rule doesn't depend on the project name.
  Drop the `/var/lib/docker/containers` mount if `docker_sd` doesn't need it (show that logs still arrive in Loki
  without it).

## Out of Scope
- Migrating Promtail to Grafana Alloy (follow-up ticket; Alloy needs the same socket proxy, so this work carries over).
- Grafana auth beyond the admin password (anonymous access, OAuth).
- The backend/frontend ports and the `BACKEND_PORT`/`FRONTEND_PORT` variables.

## Acceptance Criteria
- `docker compose config -q` and `docker compose --profile observability config -q` succeed **with and without** the
  secret file present.
- With the file missing, `docker compose --profile observability up -d` does not start Grafana (show the error).
  With the file present, Grafana reaches `healthy` and logs in with that password; `admin`/`admin` is refused.
- `ss -ltnp` (or `docker port`) shows 9090, 3000, 3100 and 6379 bound on `127.0.0.1` only (**running locally**).
- backend and ai_worker still reach Redis by service name (`redis:6379`) on the compose network after the rebinding:
  show it (for example `redis-cli -h redis ping` from a container on that network, and the backend's stream adapter
  connecting without errors in its log).
- No service except the socket proxy mounts `/var/run/docker.sock`. A POST through the proxy (for example
  `curl -X POST http://docker-socket-proxy:2375/containers/x/stop` from a throwaway container on that network) is
  refused, and backend log lines still arrive in Loki.
- `tests/architecture/test_docker_compose_dependency_hygiene.py` and `tests/tools/test_session_platform_domain.py` pass.
  Any test that pinned the old port strings is updated, not skipped.

## Related Tickets
Epic `TCK-20261018-EPIC-DEVOPS-STEP2-OBSERVABILITY-LOCAL`. Origin: #618 (u24 carry-ins 3, 4, 5).
`TCK-20261014-COMPOSE-OBSERVABILITY-PROFILE-AND-LIMITS` (added the `:-admin` fallback and recorded the socket risk).

## Related Docs
`docs/architecture/devops_baseline_adr.md` (D1)

## Related Stored Artifacts
None.

## Related Code Areas
`compose.yaml`, `docker/promtail-config.yml`, `docker/secrets/` (new, gitignored), `.gitignore`

## Assumptions / Open Questions
- `.gitignore` is not a platform path. The added line `docker/secrets/` is approved by lead (2026-10-18), who reviews it in the PR.
- Lead review 2026-10-18 approved: secret file, socket proxy now (Alloy is a follow-up ticket), loopback binding of 6379/9090/3000/3100.
- The `make` targets that start the observability profile may need a pre-check for the secret file. If the Makefile
  needs editing, run all of `tests/tools` (memory: Makefile edits).
- Pull the new image only after asking lead-planner (host rules).

## Implementation Notes
- Grafana: `GF_SECURITY_ADMIN_PASSWORD__FILE` from compose secret `grafana_admin_password` (`./docker/secrets/grafana_admin_password`, gitignored); `:-admin` fallback removed.
- Ports 6379/9090/3000/3100 now `127.0.0.1:${VAR:-port}:port`.
- New `docker-socket-proxy` (tecnativa v0.4.1, digest-pinned from a registry query, not pulled; CONTAINERS=1, POST=0; mem_limit 64m) is the only service mounting the socket (`:ro`). Promtail uses `tcp://docker-socket-proxy:2375`; `/var/lib/docker/containers` mount removed. NETWORKS=1 was dropped after the runtime check (see Test Summary).
- Promtail drop rule matches the compose service label (`loki|promtail`).
- Added after planner review: promtail `docker_sd_configs.filters` label `com.docker.compose.project=${COMPOSE_PROJECT_NAME}`; compose passes `COMPOSE_PROJECT_NAME` into promtail's env and promtail runs with `-config.expand-env=true`.
- Added after the runtime check: a grafana entrypoint guard (exits when the secret file is empty or `admin`), because Grafana otherwise starts with `admin`/`admin` on an empty file.
- No Makefile edit was needed.

## Test Summary
- PASS: `compose config -q` default and observability profiles, with and without the secret file.
- PASS: tests/architecture/test_docker_compose_dependency_hygiene.py, tests/tools/test_session_platform_domain.py, tests/logging/test_loki_cardinality.py (12 passed).
- Runtime, 2026-10-18, local (build 4m26s; `up` ran by planner/lead clearance; memory guard: available stayed >= 4.9 GB, swap 2.0-2.5 GB):
  - Missing secret file: `up -d grafana` leaves Grafana "Creating", error `invalid mount config for type "bind": bind source path does not exist: .../docker/secrets/grafana_admin_password`; backend/prometheus/redis were created. PASS (fail-fast).
  - Empty secret file (before the guard): Grafana STARTED and `admin`/`admin` returned 200. FINDING; fixed with the entrypoint guard. With the guard and an empty file Grafana exits with `docker/secrets/grafana_admin_password is empty or admin` (restart loop with that message).
  - Password and the persisted DB: Grafana applies the admin password only when it creates its database. The `grafana_data` volume came from the empty-file test, so the real password gave 401 and `admin`/`admin` 200. I did not delete the volume (data deletion needs the user); `grafana cli admin reset-admin-password "$(cat /run/secrets/...)"` then gave password 200 and `admin`/`admin` 401. NOT shown: a first start on a fresh volume applying `GF_SECURITY_ADMIN_PASSWORD__FILE` by itself. Needs `docker volume rm platform_grafana_data` (user decision) and one more start.
  - Ports: `ss -ltnH` shows 9090, 3000, 3100, 6379 on 127.0.0.1 only; 8000 and 8080 unchanged (0.0.0.0). PASS.
  - Redis by service name: backend and ai_worker both got `+PONG` from `redis:6379` on the compose network; no redis error lines in their logs. PASS.
  - Socket: only `platform-docker-socket-proxy-1` mounts `/var/run/docker.sock` (checked with `docker inspect` on every container of the profile). `POST /containers/x/stop` through the proxy: 403; `GET /containers/json` and `/version`: 200. PASS.
  - Loki without the `/var/lib/docker/containers` mount: backend lines arrive (query `{container="platform-backend-1"}`). PASS.
  - Project filter: Loki `container` label values are exactly this project's 9 containers (ai_worker, backend, docker-socket-proxy, frontend, grafana, prometheus, redis, tempo, watchdog); no `loki`/`promtail` (drop rule works) and none of the other containers on the host. PASS.
  - NETWORKS=1: not needed. Without it the proxy returns 403 on `GET /networks` (logged every refresh), `GET /containers/json` works and backend logs keep arriving. Dropped (least privilege); the 403 line in the proxy log is expected. **[2026-10-20 correction, note only: likely stale targets; see TCK-20261020-PROMTAIL-DISCOVERY-DENIED-BY-SOCKET-PROXY. Promtail's discovery fails on every refresh without NETWORKS but keeps the last good targets, so the 10-18 run most likely saw targets from an earlier good refresh. Three fresh runs on 10-19 found 0 targets and an empty Loki.]**
    - **Fresh-volume check, 2026-10-20 (running locally; the owner removed `platform_grafana_data`, lead confirmed it gone; the volume was created at 2026-10-20T21:46:28+07:00 by `up -d grafana`, which started grafana, prometheus, backend and redis only; abort watcher proven by a dry run printing WOULD DOWN, then 2 real lines; sampler started before `up`; down at 14:48:57Z without `-v`, the new volume stays):** the real password from `docker/secrets/grafana_admin_password` returned 200 on `/api/user`; `admin`/`admin` returned 401; an unauthenticated call returned 401 (all with the secret passed through curl's stdin config, never on argv). That closes the finding of 10-18 (the persisted DB from the empty-file test). Provisioning loaded on the fresh DB: alert-rule groups `base` (5), `cause` (1) and `slo` (2), all provenance `file`; contact point `ntfy` (webhook, credential `[REDACTED]`) and the default policy to `ntfy`; datasources Loki, Prometheus and Tempo. No container was OOM-killed (4 of 4 `oom=false`, restarts 0). Grafana at the first start of a fresh DB: `docker stats` peak 673 MiB (66 % of the 1024m limit; 88 % of the old 768m), anon peak 250 MiB (24 %), anon + active_file 655 MiB (64 %), `memory.peak` 1025 MiB (reference only, includes cache). Evidence: `agent-working/staging_artifacts/TCK-20261020-PROMTAIL-DISCOVERY-DENIED-BY-SOCKET-PROXY/fresh-volume-2026-10-20/`.
- Leftovers: `data/runs` is owned by root after the run (reported to the planner, not cleaned). Named volumes `platform_*` remain after `down`.
- Not run: tests/static and all of tests/tools (separate clearance; this ticket changes no Makefile).
- PASS again after the changes: `compose config -q` (default and observability).

## Files Changed
`compose.yaml`, `docker/promtail-config.yml`, `.gitignore`, this ticket.

## Completion Summary
(open)
