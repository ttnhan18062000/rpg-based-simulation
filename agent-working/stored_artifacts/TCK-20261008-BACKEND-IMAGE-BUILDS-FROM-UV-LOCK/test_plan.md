---
status: historical
layer: architecture
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261008-BACKEND-IMAGE-BUILDS-FROM-UV-LOCK
phase: done
date: 2026-10-08
tags: [architecture, delivery]
---

# test_plan — TCK-20261008-BACKEND-IMAGE-BUILDS-FROM-UV-LOCK

Normal flow: `docker build -f backend.Dockerfile .` succeeds (foreground); `docker run <img> python -c "import sys, src"` works and reports Python 3.13.
Edge: `import ruff` must fail (lint group excluded); `python -m src --help` lists subcommands (CMD target imports).
Regression: `sha256sum -c` on `uv.lock` unchanged; `docker compose -f docker-compose.yml config -q` passes and the three services still use `backend.Dockerfile`.
No automated test is added: the image build is too heavy for CI and the brief's section 5 leaves a CI image job to the owner.

## Proof Plan
- level: integration (real image build and run)
- proof kind: manual commands, run once and recorded in the ticket's Test Summary
- oracle source: docker's own build and run results; `sha256sum -c` on `uv.lock`; `docker compose config`
- expected effect: image builds on python:3.13-slim, `import src` works, no lint tooling, `uv.lock` unchanged, compose services still resolve
- selected commands: `docker build -f backend.Dockerfile .`, `docker run --rm <img> python -c "import sys, src"`, `docker compose -f docker-compose.yml config -q`
