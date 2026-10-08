---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20261008-OPS-FILES-INTO-DOCKER-DIR
phase: done
date: 2026-10-08
tags: [architecture, delivery]
---

# TCK-20261008-OPS-FILES-INTO-DOCKER-DIR

## Title
Move the ops files into docker/ and rename the compose file to compose.yaml

## Status
DONE

## Tier
standard

## Type
refactor

## Priority
P2

## Request Summary
Ops files (Dockerfiles, nginx, prometheus, promtail, grafana) sit at the repo root beside Python packaging and agent configuration. Owner decision 2026-10-08: a `docker/` folder; `compose.yaml` stays at the root (brief section 3 B1, section 4). Filed from `docs/plans/codebase_health/repo_root_layout_ticket_brief.md` by codebase-planner (owner-approved 2026-10-08), sequence in `SEQUENCE.md`. Order: after A1 (batch A merged).

## Scope
- `git mv` into `docker/`: `backend.Dockerfile`, `frontend.Dockerfile`, `nginx.conf`, `prometheus.yml`, `promtail-config.yml`, `grafana/`
- `docker-compose.yml` becomes root `compose.yaml` with updated `dockerfile:` and volume paths; the build context stays the repo root
- Update `tests/architecture/test_docker_compose_dependency_hygiene.py`, `tests/logging/test_loki_cardinality.py` (repo-root-anchored path, not cwd), `tools/test_architecture/scenario_lane_paths.py` (grafana exclusion), `codebase/reports/code_health_impact.py:99`, the Makefile docker targets, the README and `docs/engine/contracts/infrastructure_overview.md`

## Out of Scope
- Any file under `src/`
- A CI image build (brief section 5)
- Tests that pin CI or the Makefile may be edited under owner decision 8.11, with a notice to testing in the batch PR's handoff

## Acceptance Criteria
- [x] `docker compose config` passes from the root
- [x] `docker compose build` (or A1's build plus the frontend build) succeeds under the memory cap
- [x] The changed tests pass
- [x] `git diff --stat` lists no path under `src/`

## Related Tickets
- TCK-20261008-BACKEND-IMAGE-BUILDS-FROM-UV-LOCK
- TCK-20261008-DROP-UNUSED-REQUIREMENTS-EXPORT
- TCK-20261008-NOJEKYLL-TO-DOCS-SITE-STATIC
- TCK-20261008-DROP-MAKE-BAT
- TCK-20261008-GRAPH-HTML-JS-DEPS-BESIDE-TOOL
- TCK-20261008-REPO-ROOT-ALLOWLIST-GUARD

## Related Docs
- docs/plans/codebase_health/repo_root_layout_ticket_brief.md
- docs/guidelines/repo_tooling_layout.md

## Related Stored Artifacts
None.

## Related Code Areas
- docker-compose.yml
- backend.Dockerfile
- frontend.Dockerfile
- nginx.conf
- prometheus.yml
- promtail-config.yml
- grafana/
- Makefile
- tests/architecture/
- tests/logging/

## Assumptions / Open Questions
- Evidence and the owner's decisions are in the brief (sections 1 to 5); no open question beyond what the brief lists.

## Implementation Notes
- `git mv` into `docker/`: `backend.Dockerfile`, `frontend.Dockerfile`, `nginx.conf`, `prometheus.yml`, `promtail-config.yml`, `grafana/` (as `docker/grafana/`); `docker-compose.yml` -> root `compose.yaml`. The build context stays the repo root (`context: .`, `dockerfile: docker/<name>.Dockerfile`); volume paths are `./docker/...`. `.dockerignore` stays at the root (it applies to the context).
- `frontend.Dockerfile` now copies `docker/nginx.conf`; every other `COPY` source in both Dockerfiles is a context-root path (`pyproject.toml`, `uv.lock`, `src/`, `data/`, `frontend/`) and still resolves.
- Tests/tools repointed: `tests/architecture/test_docker_compose_dependency_hygiene.py` (repo-root-anchored `compose.yaml` and `pyproject.toml`, not cwd), `tests/logging/test_loki_cardinality.py` (repo-root-anchored `docker/promtail-config.yml`; verified from another cwd), `tools/test_architecture/scenario_lane_paths.py` (`grafana/` -> `docker/` in the irrelevant-paths regex) plus two `docker/` cases in `test_scenario_lane_paths.py`, `codebase/reports/code_health_impact.py` (`docker-compose` -> `compose.yaml`), and `agent-working/reviews/code_exporter.py` (the exporter's infrastructure file list; it belongs to agent-working, paths only). Docs: `infrastructure_overview.md`, `simulation_watchdog.md`, `README.md`.
- planner's A1 note, decided: the runtime stage KEEPS its second `COPY src/`, now with a comment. Evidence: dropping it works for `python -m src serve --help`, but the app then imports from site-packages and several modules locate repo files from their own path (`src/content/validator.py` `parents[2]`, `src/engine/capability.py` reads `docs/engine/capability_registry.yaml`, `src/api/agent_ops_dashboard/*`), which would resolve to the wrong directory. The venv's installed copy contains only `.py` files. Rejected for that reason.
- Left as history: `docs/audits/**`, `docs/assets/**`, `docs/brainstorm/**`, `docs/parity_ledger/**` and `docs/plans/**` still name `docker-compose.yml`; `Makefile` `search-server-*` use `tools/search/docker-compose.yml` (a different file, unchanged).

## Test Summary
- `docker compose config -q` passes from the root; it lists context = repo root for all 4 builds, `docker/backend.Dockerfile` x3, `docker/frontend.Dockerfile` x1, and volume sources under `docker/`.
- Backend image built from `docker/backend.Dockerfile` (twice: once without the second `COPY src/`, then with it): Python 3.13.16, `import src` works, `python -m src serve --help` runs. Frontend image built from `docker/frontend.Dockerfile` once; `/etc/nginx/conf.d/default.conf` is the moved `docker/nginx.conf`. One build at a time; the memory cap does not bound docker builds. Test images were removed afterwards.
- `tests/architecture/test_docker_compose_dependency_hygiene.py`, `tests/logging/test_loki_cardinality.py`, `tests/unit/tools/test_scenario_lane_paths.py`, `tests/codebase/test_code_health_impact.py`, `tests/static`: 169 passed, 1 skipped (the two docker tests also pass from a different working directory).
- `make knowledge-index-update` was not run (times out under the cap).

## Files Changed
- moved: `backend.Dockerfile`, `frontend.Dockerfile`, `nginx.conf`, `prometheus.yml`, `promtail-config.yml`, `grafana/` -> `docker/`; `docker-compose.yml` -> `compose.yaml`
- `docker/backend.Dockerfile` (comment), `docker/frontend.Dockerfile`, `compose.yaml` (paths)
- tests/tools: `tests/architecture/test_docker_compose_dependency_hygiene.py`, `tests/logging/test_loki_cardinality.py`, `tests/unit/tools/test_scenario_lane_paths.py`, `tools/test_architecture/scenario_lane_paths.py`, `codebase/reports/code_health_impact.py`, `agent-working/reviews/code_exporter.py`
- docs: `README.md`, `docs/engine/contracts/infrastructure_overview.md`, `docs/architecture/simulation_watchdog.md`

## Completion Summary
The ops files live in `docker/`, `compose.yaml` is at the root, both images build with the repo root as context, and the tests that read these files no longer depend on the working directory. All acceptance criteria met; the `COPY src/` question is decided and recorded above.
