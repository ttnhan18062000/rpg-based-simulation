---
status: historical
layer: architecture
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20261008-BACKEND-IMAGE-BUILDS-FROM-UV-LOCK
phase: done
date: 2026-10-08
tags: [architecture, delivery]
---

# plan — TCK-20261008-BACKEND-IMAGE-BUILDS-FROM-UV-LOCK

1. Rewrite `backend.Dockerfile` as uv builder + runtime stages on `python:3.13-slim`, uv 0.11.2 copied from `ghcr.io/astral-sh/uv:0.11.2` (CI pins 0.11.2).
2. Add `.dockerignore` and `.python-version` (`3.13`).
3. Build and run the image in the foreground, check `uv.lock` and `docker compose config`.

Scope guard: no `src/`, no compose change, no CI image build, `requires-python`/mypy untouched. Use `--no-default-groups` rather than `--no-dev` (default groups are `dev` and `lint`).
