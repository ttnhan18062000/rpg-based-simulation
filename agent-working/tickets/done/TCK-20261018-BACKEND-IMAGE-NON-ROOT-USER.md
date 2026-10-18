---
status: historical
layer: platform
authority: P1
audience: agent
ticket_id: TCK-20261018-BACKEND-IMAGE-NON-ROOT-USER
phase: done
date: 2026-10-18
tags: [platform, security]
---

# TCK-20261018-BACKEND-IMAGE-NON-ROOT-USER

## Title
Backend image: run backend, ai_worker and watchdog as a non-root user, so the bind-mounted ./data is never left root-owned

## Status
DONE

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
- Runtime, 2026-10-18, local (lead CLEAR via planner). Build alone: 54 s. Memory before `up`: available 5.9 GB, swap 2.4 GB; after `down`: 5.9 GB / 2.4 GB.
  - `docker compose exec backend id` and `exec ai_worker id`: `uid=1000(app) gid=1000(app)`. backend `healthy`, ai_worker `Up` (it has no healthcheck), frontend and redis `healthy`.
  - Watchdog: NOT run. It is in the `observability` profile, not the default one, so it was not started (`exec watchdog id` says "not running"). Its image is the same Dockerfile with the same `USER`, but a run proof for it needs an observability start.
  - `ls -ln data/runs` after the run: the new `run_1792267369_...` dir is `1000 1000`; the old `run_1792263138_...` stays `0 0` (the owner's to remove, not touched). Files inside are 1000:1000, and `touch /app/data/x` works in the backend.
  - Logs: no PermissionError and no HOME or cache error in backend or ai_worker. `HOME=/home/app`, which does not exist (`--no-create-home`), and nothing needed it, so no `ENV HOME` change was made.
  - No `src/` writer outside `/app/data` fired in `serve` or in the anomaly worker (it started and wrote its output without error).
  - `down` (no -v) clean. My run dir was removed by run id.
- PASS: tests/architecture/test_docker_compose_dependency_hygiene.py, tests/tools/test_session_platform_domain.py, tests/tools/test_loadtest_summary.py (32 passed); tests/static/test_ci_narrow_path_filtered_jobs.py, tests/codebase/test_repo_root_allowlist.py (22 passed).
- Watchdog (window 2, 2026-10-18, observability start after `docker compose --profile observability build watchdog`): `exec watchdog id` = `uid=1000(app) gid=1000(app)`, watchdog Up. The first observability start earlier the same day showed `uid=0` because `platform-watchdog` was a stale image built before this change (the earlier `docker compose build` ran without the observability profile). `find data -uid 0` after the starts listed only the old pre-existing run dir; the watchdog wrote nothing there.

## Files Changed
`docker/backend.Dockerfile`, `compose.yaml`, this ticket.

## Completion Summary
`docker/backend.Dockerfile` creates user and group `app` (uid/gid from `APP_UID`/`APP_GID`, default 1000), compiles `/app/src` as root, chowns `/app/data` and sets `USER app`; `compose.yaml` passes the build args for backend, ai_worker and watchdog. Proven locally: `id` is uid 1000 in backend, ai_worker and (on the rebuilt image) watchdog; a new `data/runs/<run_id>` and its files are owned by 1000:1000; no PermissionError or HOME/cache error; no `src/` writer outside `/app/data` fired in `serve` or the anomaly worker. `HOME=/home/app` does not exist (`--no-create-home`) and nothing needed it.

For the PR body: `publish-images.yml` builds this Dockerfile, so the GHCR images now run as uid 1000 (intended; no workflow change). Trivy was not run locally. The pre-existing root-owned `data/runs/run_1792263138_5169_1_3e0de9d3` is the owner's to remove. Staging artifacts (plan, investigation, test plan) were written retrospectively at close, on 2026-10-18.
