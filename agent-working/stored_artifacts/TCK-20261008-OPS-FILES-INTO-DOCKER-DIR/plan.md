---
status: historical
layer: architecture
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20261008-OPS-FILES-INTO-DOCKER-DIR
phase: done
date: 2026-10-08
tags: [architecture, delivery]
---

# plan — TCK-20261008-OPS-FILES-INTO-DOCKER-DIR

1. `git mv` the six ops entries into `docker/`; `docker-compose.yml` -> `compose.yaml`; update `dockerfile:` and volume paths, keep `context: .`.
2. Frontend Dockerfile copies `docker/nginx.conf`.
3. Repoint tests/tools/exporter/docs found by `git grep` (not only the brief's list); anchor the two tests on the repo root.
4. Decide the A1 note (second `COPY src/`) by building both ways.
5. `docker compose config`, one backend build, one frontend build, scoped tests.

Scope guard: no `src/`; Makefile `search-server-*` (tools/search/docker-compose.yml) untouched; history docs untouched.
