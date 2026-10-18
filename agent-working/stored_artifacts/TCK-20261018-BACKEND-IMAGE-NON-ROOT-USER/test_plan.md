---
status: historical
layer: platform
authority: P2
audience: agent
ticket_id: TCK-20261018-BACKEND-IMAGE-NON-ROOT-USER
artifact_type: test_plan
tags: [platform, observability]
---

# Test plan: TCK-20261018-BACKEND-IMAGE-NON-ROOT-USER

**Written retrospectively at ticket close (2026-10-18).** The plan was given in platform-planner's dispatch messages and the ticket Scope; this file records it after the fact.

## Test plan (what was run)

## Proof Plan
| criterion | level | proof kind | oracle source | expected effect | selected commands |
|---|---|---|---|---|---|
| AC1: `exec backend id` non-root; backend, ai_worker healthy/running; watchdog running | runtime, local | live check | none: platform runtime, criterion from the ticket AC and ADR `docs/architecture/devops_baseline_adr.md` | uid=1000(app) for backend, ai_worker and (later) watchdog | `docker compose build`; `docker compose up -d`; `docker compose exec backend id`; `exec ai_worker id`; `docker compose --profile observability build watchdog`, observability `up -d`, `exec watchdog id` |
| AC2: new `data/runs` dir owned by the host uid | runtime, local | live check | none: platform runtime, criterion from the ticket AC and ADR `docs/architecture/devops_baseline_adr.md` | new run dir 1000:1000, files 1000:1000 | `ls -ln data/runs` after the run |
| AC3: compose hygiene and image static tests pass | static | regression | none: platform runtime, criterion from the ticket AC and ADR `docs/architecture/devops_baseline_adr.md` | green | `pytest tests/architecture/test_docker_compose_dependency_hygiene.py tests/tools/test_session_platform_domain.py tests/static/test_ci_narrow_path_filtered_jobs.py tests/codebase/test_repo_root_allowlist.py` |
| AC4: Trivy not run locally; non-root noted | n/a | note | none: platform runtime, criterion from the ticket AC and ADR `docs/architecture/devops_baseline_adr.md` | the ticket notes it | none: not run |

## Results (from the ticket's Test Summary)
- Build alone: 54 s. Default-profile `up -d`: backend healthy, ai_worker Up, frontend and redis healthy. `id` in backend and ai_worker: `uid=1000(app) gid=1000(app)`.
- `ls -ln data/runs`: the new run dir and its files were 1000:1000; the old root-owned dir stayed 0:0 and was not touched.
- No PermissionError and no HOME or cache error in backend or ai_worker logs. `touch /app/data/x` worked in the backend.
- Static tests: 32 passed (hygiene, platform domain, loadtest summary) and 22 passed (CI narrow-path, repo-root allowlist).
- Watchdog uid proof: `exec watchdog id` = `uid=1000(app) gid=1000(app)` on the rebuilt image in the window-2 observability start; the same start showed uid 0 on the stale image before the rebuild.
- Trivy: not run.
