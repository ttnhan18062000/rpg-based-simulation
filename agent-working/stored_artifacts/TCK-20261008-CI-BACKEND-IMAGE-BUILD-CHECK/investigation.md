---
status: historical
layer: architecture
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261008-CI-BACKEND-IMAGE-BUILD-CHECK
phase: done
date: 2026-10-08
tags: [architecture, delivery]
---

# investigation — TCK-20261008-CI-BACKEND-IMAGE-BUILD-CHECK

Research (planner, with sources): docs.docker.com/engine/release-notes/23.0 (BuildKit is the default builder since Docker 23, so `docker build` supports `# syntax=` and cache/bind mounts, which docker/backend.Dockerfile uses); docs.docker.com/build/ci/github-actions/{test-before-push, cache, checks} (build checks, build-before-push, the type=gha cache option left for later); docs.github.com secure-use (pinning actions and images, left for the owner).

Repo map (planner read of test.yml and the static tests): `frontend` job at the changed-files gate is the model; `resync-gate` skip list is pinned by `test_ci_registry_resync_skip_jobs.py` (SKIP_JOBS); `test_ci_step_summary_reporting.py` pins the job set; `test_ci_uv_install.py` exempts non-Python jobs; `test_ci_narrow_path_filtered_jobs.py` pins gate shape and fail-open branches. The required-check caveat is the comment above `code-health` in test.yml.

Implementer checks: `docker build --check` on the current Dockerfile reports no warnings (exit 0); Docker 29.3.1 with buildx 0.31.1 locally; `actionlint` is not installed but runs through `uvx --from actionlint-py`.
