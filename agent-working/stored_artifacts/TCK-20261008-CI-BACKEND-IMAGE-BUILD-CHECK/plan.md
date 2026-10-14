---
status: historical
layer: architecture
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20261008-CI-BACKEND-IMAGE-BUILD-CHECK
phase: done
date: 2026-10-08
tags: [architecture, delivery]
---

# plan — TCK-20261008-CI-BACKEND-IMAGE-BUILD-CHECK

Planner decisions (codebase-planner, owner-approved 2026-10-08):
1. New job `docker-build` named "Backend image build" in test.yml, copying `frontend`'s shape: `needs: [changed-files, resync-gate]`, the `!cancelled()` + fail-open condition on a new output `run_docker_build`, honouring `pr_content_unchanged`, `timeout-minutes: 15`.
2. `changed-files` gains `DOCKER_RE='^(docker/backend\.Dockerfile$|\.dockerignore$|pyproject\.toml$|uv\.lock$|\.github/workflows/test\.yml$)'` and `run_docker_build`, true in both fail-open branches. Backend image only.
3. Steps: checkout@v5 (already allowlisted), `docker build --check`, `docker build -t rpg-backend:ci`, `docker run` asserting Python 3.13, a step-summary size line. No docker/* actions, no cache, no push, no login.
4. Not a required check (a path-skipped required check stays expected).
5. Update the four static pins deliberately and the migration_ci_lanes doc; testing notice in the handoff.
If `--check` warns on the current Dockerfile, report it, do not silence it.
Scope guard: no `src/`, no frontend image, no cache/Dependabot/ubuntu pinning.
