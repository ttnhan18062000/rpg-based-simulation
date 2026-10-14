---
status: active
layer: architecture
authority: P2
audience: agent
tags: [planning]
---

# Repo root layout: ticket brief

**From:** `codebase-planner`, 2026-10-08, at `origin/main` `0d75424dc`. **Owner decisions:** 2026-10-08 (section 4).
**Why:** the repo root holds 27 tracked files and 20 directories that mix five concerns: Python packaging, ops/deploy,
task running, JS, and agent configuration. Some are defects, not clutter: the backend image ignores `uv.lock` and runs
a different Python than CI, and `requirements.txt` has no consumer. Nothing here touches `src/`, so the `src/` freeze
does not apply.

## 1. Evidence: what each root file is used by (origin/main, 2026-10-08)

| Root entry | Consumers | Finding |
|---|---|---|
| `backend.Dockerfile` | `docker-compose.yml:6,41,123` only; no CI build | `python:3.11-slim` + `pip install .`: ignores `uv.lock`, unpinned resolve at build time; CI tests 3.13 |
| `requirements.txt` | no installer; path regexes `test.yml:789-790`; pins in `tests/static/test_ci_narrow_path_filtered_jobs.py:348`, `tests/static/test_ci_requirements_no_ml_stack.py`; human docs (`agent_working_environment.md`, `migration_ci_lanes.md`, `performance_profiling.md`) | a `uv export` nobody installs since all CI jobs run `uv sync --locked` |
| `requirements-knowledge.txt` | separate 3.12 `.venv-knowledge` (agent-working); 4 tests read it | outside uv; torch CPU wheel installed by hand |
| `make.bat` | none (a scan list in one test) | 19 targets vs the Makefile's 145; touched only incidentally since 2026-03 |
| `package.json` / `package-lock.json` | only `tools/graphify_to_html.py:33-34` (reads `node_modules/` relative to cwd) | no Makefile target, no CI, no root `npm install` anywhere |
| `nginx.conf` | `frontend.Dockerfile:21` | ops file at root |
| `prometheus.yml`, `promtail-config.yml`, `grafana/` | `docker-compose.yml`; `tests/logging/test_loki_cardinality.py:22-23` (cwd-relative, "must exist at the root") | ops files at root |
| `.nojekyll` | none; Pages deploys `website/build` via Actions (`deploy-docs.yml`, currently dispatch-only) | inert at root |
| `perf_baselines.json` | `tests/perf/conftest.py:16` (cwd-relative), `Makefile:215`, perf docs | `"entries": {}`; perf domain's file |
| `skills-lock.json` | no repo tool (format matches the external `npx skills` CLI, inferred) | leave |

No `.dockerignore`, no `.python-version`, no Dependabot config exist. `requires-python = ">=3.11"`, mypy
`python_version = "3.11"`, CI 3.13 everywhere.

## 2. External practice (sources opened 2026-10-08)

- **uv in Docker** (docs.astral.sh/uv/guides/integration/docker/): copy a *pinned* uv binary from
  `ghcr.io/astral-sh/uv:<version>`; install deps in their own layer with bind-mounted `uv.lock`/`pyproject.toml` and
  `uv sync --locked --no-install-project`, then copy source and `uv sync --locked`; `UV_COMPILE_BYTECODE=1`,
  `UV_LINK_MODE=copy` with cache mounts, `UV_NO_DEV=1`, `--no-editable`, multi-stage copy of `/app/.venv`,
  `UV_PYTHON_DOWNLOADS=0` so both stages use the base image's Python; `.venv` in `.dockerignore`.
- **Exports** (docs.astral.sh/uv/concepts/projects/export/): "we recommend against using both a `uv.lock` and a
  `requirements.txt` file"; export only for a consumer that cannot read `uv.lock` (formats: requirements, PEP 751
  `pylock.toml`, CycloneDX preview). Renovate and Dependabot read `uv.lock` (Dependabot with caveats).
- **CPU torch** (docs.astral.sh/uv/guides/integration/pytorch/): `[[tool.uv.index]] name="pytorch-cpu"
  url="https://download.pytorch.org/whl/cpu" explicit=true` + `[tool.uv.sources] torch=[{index="pytorch-cpu"}]`.
  Sources apply by package name, so a dependency group works (inferred; the docs show no group example). Torch enlarges
  the lock for all platforms unless `tool.uv.environments` narrows it.
- **Task runners** (repo roots checked): Makefile in pydantic, Textual, Dify, Open WebUI, Supabase; justfile in Prefect,
  Dagster; `scripts/` in FastAPI. None keeps a `make.bat`-style Windows duplicate.
- **Compose** (docs.docker.com): `compose.yaml` is the preferred default name; `docker-compose.yml` is backwards
  compatibility. Relative paths resolve from the compose file's directory.
- **Ops folder name**: no standard; `docker/` is the most common in the sample (Dify, Supabase).
- **JS workspaces** (pnpm.io/workspaces): framed for related packages; the three JS apps here are unrelated, so no
  workspace.
- **Docusaurus on GitHub Pages** (docusaurus.io/docs/deployment): `.nojekyll` goes in `static/`.
- **AGENTS.md** (code.claude.com memory docs): Claude Code reads `AGENTS.md` only when no `CLAUDE.md` exists, unless
  `CLAUDE.md` imports it with `@AGENTS.md`.

## 3. Tickets

Folder `agent-working/tickets/todos/repo-root-layout/` with `SEQUENCE.md`. Two batches, one PR each (batch A first).
All tickets: no path under `src/`; tests that pin CI or the Makefile may be edited under owner decision 8.11, with a
notice to testing in the batch PR's handoff.

### Batch A: defects

**A1 `TCK-20261008-BACKEND-IMAGE-BUILDS-FROM-UV-LOCK`** (standard, P2)
- `backend.Dockerfile` follows the uv guide: multi-stage, `python:3.13-slim`, uv copied from a pinned
  `ghcr.io/astral-sh/uv:<version>` (pin the version CI's setup-uv uses, or the newest, and say which),
  `uv sync --locked --no-install-project --no-dev` layer, then `uv sync --locked --no-dev --no-editable`; the env vars
  above; runtime stage copies `.venv` + the files the image needs today (`src/`, `data/`); same CMD.
- New `.dockerignore` (`.venv*`, `.git`, `node_modules`, caches, `data/runs/`, `reports/`, `tmp/`, `scratch/`).
- New `.python-version` = `3.13` (matches CI). `requires-python` and mypy's `python_version` stay (owner decision,
  section 5).
- AC: `docker build -f backend.Dockerfile .` succeeds locally (heavy: under the memory cap, foreground) and
  `docker run <img> python -c "import src"` works; image Python is 3.13; `uv.lock` unchanged; the compose services
  `backend`, `ai_worker`, `watchdog` still reference the image correctly (`docker compose config` passes).
- Not in scope: a CI image build (section 5 option).

**A2 `TCK-20261008-DROP-UNUSED-REQUIREMENTS-EXPORT`** (standard, P2)
- Delete `requirements.txt`. Remove it from the PERF/MIG path regexes in `test.yml` (make sure `pyproject.toml` and
  `uv.lock` are in them) and the pin in `test_ci_narrow_path_filtered_jobs.py`.
- Keep the intent of `test_ci_requirements_no_ml_stack.py` (the ML stack never reaches CI installs) by asserting it on
  the default dependency groups of `pyproject.toml` / `uv.lock`; fix its stale `pip install -r` comment.
- Update the export comments in `pyproject.toml` and the human docs that say to use `requirements.txt`.
- AC: no live reference to `requirements.txt` outside history (done tickets, stored artifacts, monitoring data);
  `tests/static`, `tests/tools` pass; `make knowledge-index-update` or a noted skip.

**A3 `TCK-20261008-NOJEKYLL-TO-DOCS-SITE-STATIC`** (hotfix, P3)
- `git mv .nojekyll website/static/.nojekyll` (Docusaurus guidance). AC: the docs site build still copies it into
  `website/build/` (check locally if cheap, else state it).

### Batch B: layout

**B1 `TCK-20261008-OPS-FILES-INTO-DOCKER-DIR`** (standard, P2), after A1
- `git mv` into `docker/`: `backend.Dockerfile`, `frontend.Dockerfile`, `nginx.conf`, `prometheus.yml`,
  `promtail-config.yml`, `grafana/`. `docker-compose.yml` → root `compose.yaml` (preferred name) with updated
  `dockerfile:`/volume paths; build context stays the repo root.
- Update: `tests/architecture/test_docker_compose_dependency_hygiene.py`, `tests/logging/test_loki_cardinality.py`
  (repo-root-anchored path, not cwd), `tools/test_architecture/scenario_lane_paths.py` (grafana exclusion),
  `codebase/reports/code_health_impact.py:99`, Makefile docker targets, README, `docs/engine/contracts/infrastructure_overview.md`.
- AC: `docker compose config` passes from the root; `docker compose build` (or A1's build plus the frontend build)
  under the cap; changed tests pass.

**B2 `TCK-20261008-DROP-MAKE-BAT`** (hotfix, P3)
- Delete `make.bat`; drop it from the scan list in `tests/codebase/test_code_health_install_git_hooks.py`; README /
  CONTRIBUTING say Windows runs `make` under WSL or Git Bash.

**B3 `TCK-20261008-GRAPH-HTML-JS-DEPS-BESIDE-TOOL`** (standard, P3)
- Move `package.json` + `package-lock.json` next to the tool (directory name per
  `docs/guidelines/repo_tooling_layout.md`); `graphify_to_html.py` resolves `node_modules/` relative to that
  directory, not cwd, with a clear error if missing; update its usage line and the two docs that mention it.
- AC: a test pins the resolution path (no network, no npm in CI); no root `package.json`.

**B4 `TCK-20261008-REPO-ROOT-ALLOWLIST-GUARD`** (standard, P2), last
- New "Repo root" section in `docs/guidelines/repo_tooling_layout.md`: the tracked root allowlist after A and B, and
  the rule that a new root entry needs an owner decision (like a domain root).
- `tests/codebase/test_repo_root_allowlist.py`: tracked root entries (`git ls-files` top level) equal the allowlist;
  the failure message names the guideline.

## 4. Owner decisions (2026-10-08)
1. Task runner: keep Make, drop `make.bat`.
2. Ops files: `docker/` folder, `compose.yaml` stays at the root.
3. Knowledge deps: proposed to agent-working, not ticketed (section 5).

## 5. Not ticketed (other owners or later decisions)
- **Knowledge deps to a uv `knowledge` group** (agent-working's `.venv-knowledge`, Python 3.12): proposal in the batch A
  handoff to agent-working, with the documented CPU-index pattern and the lock-size caveat. Ticket only on their yes.
- **AGENTS.md vs CLAUDE.md** (agent-working): with both at the root, Claude Code ignores `AGENTS.md` unless `CLAUDE.md`
  has `@AGENTS.md`; worth checking for drift between them. Handoff note only.
- **`perf_baselines.json`** (perf): empty, cwd-relative; perf-planner decides whether it moves (e.g. under `tests/perf/`).
- **`skills-lock.json`**: stays (external CLI's file).
- **Python floor**: `requires-python >=3.11` and mypy `python_version 3.11` vs 3.13 everywhere else; raising the floor
  is an owner decision.
- **CI image build**: a path-filtered `docker build` job (only when `docker/**`, `pyproject.toml`, `uv.lock` change)
  would stop the image drifting again; owner decision, not in A1.
- **Local clutter** (`uvicorn.log`, `replay_v2*`, `tmp/`, `scratch/`, `reports/`, old index dirs): ignored, not tracked;
  no cleanup target (risk of deleting someone's data).
