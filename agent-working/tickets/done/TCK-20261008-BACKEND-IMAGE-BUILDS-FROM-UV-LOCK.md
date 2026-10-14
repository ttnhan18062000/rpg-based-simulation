---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20261008-BACKEND-IMAGE-BUILDS-FROM-UV-LOCK
phase: done
date: 2026-10-08
tags: [architecture, delivery]
---

# TCK-20261008-BACKEND-IMAGE-BUILDS-FROM-UV-LOCK

## Title
Build the backend image from uv.lock on the Python CI tests

## Status
DONE

## Tier
standard

## Type
repair

## Priority
P2

## Request Summary
`backend.Dockerfile` uses `python:3.11-slim` and `pip install .`: it ignores `uv.lock`, resolves unpinned at build time, and runs a different Python (3.11) than CI (3.13). Rebuild it as the uv guide describes (brief section 1, 2 and 3 A1). Filed from `docs/plans/codebase_health/repo_root_layout_ticket_brief.md` by codebase-planner (owner-approved 2026-10-08), sequence in `SEQUENCE.md`.

## Scope
- `backend.Dockerfile` follows the uv Docker guide: multi-stage, `python:3.13-slim`, uv copied from a pinned `ghcr.io/astral-sh/uv:<version>` (pin the version CI's setup-uv uses, or the newest, and say which), a `uv sync --locked --no-install-project --no-dev` layer, then `uv sync --locked --no-dev --no-editable`; `UV_COMPILE_BYTECODE=1`, `UV_LINK_MODE=copy` with cache mounts, `UV_NO_DEV=1`, `UV_PYTHON_DOWNLOADS=0`; the runtime stage copies `.venv` plus the files the image needs today (`src/`, `data/`); same CMD
- New `.dockerignore` (`.venv*`, `.git`, `node_modules`, caches, `data/runs/`, `reports/`, `tmp/`, `scratch/`)
- New `.python-version` = `3.13` (matches CI)

## Out of Scope
- A CI image build (brief section 5, owner decision)
- Changing `requires-python` or mypy's `python_version` (owner decision, brief section 5)
- Moving the Dockerfile into `docker/` (B1)
- Tests that pin CI or the Makefile may be edited under owner decision 8.11, with a notice to testing in the batch PR's handoff

## Acceptance Criteria
- [x] `docker build -f backend.Dockerfile .` succeeds locally (run under the memory cap, foreground) and `docker run <img> python -c "import src"` works
- [x] The image's Python is 3.13
- [x] `uv.lock` is unchanged
- [x] The compose services `backend`, `ai_worker` and `watchdog` still reference the image correctly (`docker compose config` passes)
- [x] `git diff --stat` lists no path under `src/`

## Related Tickets
- TCK-20261008-DROP-UNUSED-REQUIREMENTS-EXPORT
- TCK-20261008-NOJEKYLL-TO-DOCS-SITE-STATIC
- TCK-20261008-OPS-FILES-INTO-DOCKER-DIR
- TCK-20261008-DROP-MAKE-BAT
- TCK-20261008-GRAPH-HTML-JS-DEPS-BESIDE-TOOL
- TCK-20261008-REPO-ROOT-ALLOWLIST-GUARD

## Related Docs
- docs/plans/codebase_health/repo_root_layout_ticket_brief.md
- docs/guidelines/repo_tooling_layout.md

## Related Stored Artifacts
None.

## Related Code Areas
- backend.Dockerfile
- docker-compose.yml
- .dockerignore
- .python-version
- pyproject.toml
- uv.lock

## Assumptions / Open Questions
- Evidence and the owner's decisions are in the brief (sections 1 to 5); no open question beyond what the brief lists.

## Implementation Notes
- `backend.Dockerfile` is now three stages: `ghcr.io/astral-sh/uv:0.11.2` (the version CI pins in `test.yml` via setup-uv; the Dockerfile comment says to change both together), a `python:3.13-slim` builder, and a `python:3.13-slim` runtime that copies `/app/.venv` plus `src/` and `data/`. Dependencies install in their own layer from bind-mounted `uv.lock`/`pyproject.toml` (`uv sync --locked --no-install-project`), then the project (`uv sync --locked --no-editable`). Env: `UV_COMPILE_BYTECODE=1`, `UV_LINK_MODE=copy`, `UV_NO_DEV=1`, `UV_PYTHON_DOWNLOADS=0`; cache mounts on `/root/.cache/uv`.
- Deviation from the brief, on purpose: `--no-default-groups` instead of `--no-dev`. The project's `[tool.uv] default-groups` is `["dev", "lint"]`, and `--no-dev` alone would still install the `lint` group (ruff etc.) into the image.
- New `.dockerignore` and `.python-version` (`3.13`). `requires-python` and mypy's `python_version` are untouched (owner decision).
- Not changed: the CMD, EXPOSE, the compose file, and the frontend image.

## Test Summary
- `docker build -f backend.Dockerfile .` succeeded in the foreground (the cgroup cap wraps the docker client only; the build itself runs in dockerd, so the cap does not bound it). Image size 574 MB.
- `docker run <img> python -c "import sys, src"` prints Python 3.13.16 and `/app/src/__init__.py`; `import ruff` fails (no lint group); `python -m src --help` lists the subcommands.
- `sha256sum -c` on `uv.lock` before and after: unchanged.
- `docker compose -f docker-compose.yml config -q` passes; `backend`, `ai_worker` and `watchdog` still use `dockerfile: backend.Dockerfile`.
- No test pins the Dockerfile or `.python-version` (searched `tests/`, `tools/`, `codebase/`, `docs/`). The test image tag was removed afterwards.

## Files Changed
- `backend.Dockerfile` (rewritten)
- `.dockerignore` (new)
- `.python-version` (new)
- the ticket file (todos -> inprogress -> done)

## Completion Summary
The backend image now builds from `uv.lock` on Python 3.13, the version CI tests, instead of an unpinned `pip install .` on 3.11. All acceptance criteria met; the only deviation (`--no-default-groups`) is recorded above. Local `uv sync` now also defaults to Python 3.13 through `.python-version`.
