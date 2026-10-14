---
status: historical
layer: architecture
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261008-BACKEND-IMAGE-BUILDS-FROM-UV-LOCK
phase: done
date: 2026-10-08
tags: [architecture, delivery]
---

# investigation — TCK-20261008-BACKEND-IMAGE-BUILDS-FROM-UV-LOCK

Source: `docs/plans/codebase_health/repo_root_layout_ticket_brief.md` section 1 and 3 A1.

- Old image: `python:3.11-slim`, `pip install .` from `pyproject.toml` only; it ignored `uv.lock` and CI tests 3.13.
- Consumers: `docker-compose.yml` services `backend`, `ai_worker`, `watchdog` (`dockerfile: backend.Dockerfile`); no CI image build; no test pins the Dockerfile text (searched `tests/`, `tools/`, `codebase/`, `docs/`).
- `pyproject.toml`: setuptools backend, `packages.find include src*`, `[tool.uv] default-groups = [dev, lint]`, no `readme` field. CI pins uv `0.11.2` in `test.yml` (setup-uv v10.2.0).
- Docker 29.3.1 is available locally; other sessions' containers are running (not touched).
