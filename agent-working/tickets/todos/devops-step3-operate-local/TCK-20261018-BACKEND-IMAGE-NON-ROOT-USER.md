---
status: active
layer: platform
authority: P1
audience: agent
ticket_id: TCK-20261018-BACKEND-IMAGE-NON-ROOT-USER
phase: open
date: 2026-10-18
tags: [platform, security]
---

# TCK-20261018-BACKEND-IMAGE-NON-ROOT-USER

## Title
Backend image: run backend, ai_worker and watchdog as a non-root user, so the bind-mounted ./data is never left root-owned

## Status
INPROGRESS

## Tier
standard

## Type
repair

## Priority
P2

## Request Summary
`docker/backend.Dockerfile` has no `USER`, so backend, ai_worker and watchdog run as root. The backend writes
`./data/runs/<run_id>` through the `./data:/app/data` bind mount, so every compose start leaves root-owned run
directories in the checkout. On 2026-10-18 that happened twice in the platform-implementer worktree
(`run_1792259518_*`, `run_1792263138_*`). Each time, engine tests in that checkout failed, and the owner had to
delete the directory with root. This is a known recurring problem (memory: "compose leaves root-owned data/runs").
Step 3's measured run and drill start the stack several more times.

## Scope
- `docker/backend.Dockerfile`:
  - create a non-root user and group (for example `app`, uid/gid from build args `APP_UID`/`APP_GID`, default 1000);
  - `chown` only what must be writable (`/app/data`, any cache dir the app writes);
  - `USER app` in the final stage.
- `compose.yaml`: pass `APP_UID`/`APP_GID` as build args from env (`${APP_UID:-1000}`), so a host user other than
  1000 can match. Document it in the compose header comment.
- Check that nothing in the image needs root at runtime: binding port 8000, writing to `/app`, the Python cache.
  Fix by path, not by running as root.
- `publish-images.yml` builds the same Dockerfile. The published image then runs as uid 1000 too. Note that in the
  ticket; no workflow change is expected.

## Out of Scope
- frontend (nginx) and third-party images.
- Any `src/**` change. If the app writes outside `/app/data`, report it to platform-planner, who routes it to rpg.
- Cleaning existing root-owned directories (the owner's decision, per run id).

## Acceptance Criteria
- `docker compose build` (after asking lead-planner) and a default-profile `up`: `docker compose exec backend id`
  shows a non-root uid; backend, ai_worker and watchdog reach healthy or running.
- After a start that writes a run, `ls -ln data/runs` shows the new run dir owned by the host uid, not 0
  (**running locally**).
- `tests/architecture/test_docker_compose_dependency_hygiene.py` and the image-related static tests pass.
- Trivy (report-only) is not run locally. The ticket notes that non-root removes one class of findings.

## Related Tickets
Epic `TCK-20261018-EPIC-DEVOPS-STEP3-OPERATE-LOCAL`. Lands before `TCK-20261018-API-LOAD-TEST-MEASURED-RUN`
and `TCK-20261018-REDIS-STOP-DRILL-UNDER-LOAD`. Step 1: `TCK-20261008-BACKEND-IMAGE-BUILDS-FROM-UV-LOCK`.

## Related Docs
`docs/architecture/devops_baseline_adr.md` (D1, D2)

## Related Stored Artifacts
None.

## Related Code Areas
`docker/backend.Dockerfile`, `compose.yaml`

## Assumptions / Open Questions
- Host uid is 1000 on both hosts. The build args cover other cases.

## Implementation Notes
- `docker/backend.Dockerfile` (runtime stage, before `EXPOSE`): `ARG APP_UID=1000` / `APP_GID=1000`, `groupadd`/`useradd` (no home, nologin shell), `python -m compileall -q /app/src` as root (the app user cannot write `__pycache__` later; the venv is already byte-compiled by `UV_COMPILE_BYTECODE`), `chown -R app:app /app/data`, `USER app`.
- `compose.yaml`: `args: APP_UID/APP_GID: ${APP_UID:-1000}` on the three builds that use this Dockerfile (backend, ai_worker, watchdog); header comment says how to build for another host user.
- Static check of writes outside `/app/data`: a grep of `src/` finds `mkdir` calls in `src/lab/*` (lab runs), `src/worldassembly/resolve_io.py` and `src/observability/behavior/worker.py`; the lab runs are not started by `serve`, the anomaly worker or the watchdog. NOT proven for those three processes; the runtime check below decides. If the app writes outside `/app/data` at runtime, report it to platform-planner (src/ is rpg's).
- `publish-images.yml` builds the same Dockerfile: the published image now also runs as uid 1000. No workflow change.
- Trivy: not run locally; non-root removes the "runs as root" class of findings.

## Test Summary
- PASS: `compose config -q` (default and observability); tests/architecture/test_docker_compose_dependency_hygiene.py, tests/tools/test_session_platform_domain.py, tests/static/test_ci_narrow_path_filtered_jobs.py, tests/codebase/test_repo_root_allowlist.py.
- PENDING (needs lead clearance): `docker compose build`, default-profile `up`, `id` in backend, ai_worker and watchdog running, `ls -ln data/runs` owner after a run.

## Files Changed
`docker/backend.Dockerfile`, `compose.yaml`, this ticket.

## Completion Summary
(open)
