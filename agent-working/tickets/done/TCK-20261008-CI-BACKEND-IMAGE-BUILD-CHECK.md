---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20261008-CI-BACKEND-IMAGE-BUILD-CHECK
phase: done
date: 2026-10-08
tags: [architecture, delivery]
---

# TCK-20261008-CI-BACKEND-IMAGE-BUILD-CHECK

## Title
Add a path-gated CI job that checks the backend image still builds

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
No CI job builds `docker/backend.Dockerfile`, so the image drifted from CI's Python and `uv.lock` once already (fixed by `TCK-20261008-BACKEND-IMAGE-BUILDS-FROM-UV-LOCK`). Add a `docker-build` job ("Backend image build") to `.github/workflows/test.yml` that runs Docker's own build checks, builds the image, and asserts the image's Python is 3.13. Owner-approved 2026-10-08, design by codebase-planner.

## Scope
- New job `docker-build` (name "Backend image build"), modelled on the `frontend` job: `runs-on: ubuntu-latest`, `needs: [changed-files, resync-gate]`, the `!cancelled()` + fail-open `if` on a new `changed-files` output `run_docker_build`, honouring `resync-gate`'s `pr_content_unchanged`; `timeout-minutes: 15`
- `changed-files`: `DOCKER_RE='^(docker/backend\.Dockerfile$|\.dockerignore$|pyproject\.toml$|uv\.lock$|\.github/workflows/test\.yml$)'` and output `run_docker_build`, `=true` in both fail-open branches; update the comment above the job
- Steps: `actions/checkout@v5` (already allowlisted), then `docker build --check -f docker/backend.Dockerfile .`, `docker build -f docker/backend.Dockerfile -t rpg-backend:ci .`, `docker run --rm rpg-backend:ci python -c "import sys, src; assert sys.version_info[:2] == (3, 13), sys.version"`, and a `$GITHUB_STEP_SUMMARY` line with the image size. No docker/* actions, no cache, no push, no registry login
- Not a required check (a path-skipped required check stays "expected"); say so in the docs
- Update the pin tests deliberately (decision 8.11, testing notice in `handoff_to_testing.md`) and `docs/testing/migration_ci_lanes.md`

## Out of Scope
- Any file under `src/`
- The frontend image
- Options for later (owner decisions): `type=gha` layer caching; Dependabot `docker` and `github-actions` ecosystems with digest/SHA pins; `runs-on: ubuntu-24.04` around the ubuntu-latest -> 26.04 migration (2026-10-19 to 11-19)
- Making the job a required check

## Acceptance Criteria
- [x] `test.yml` has the `docker-build` job and the `run_docker_build` gate as scoped, with no new `uses:` and no allowlist edit
- [x] The job's three docker commands succeed locally, one build, nothing else heavy running; `docker build --check` exits 0 (a warning is reported, not silenced)
- [x] The four static tests are updated deliberately and `tests/static`, `tests/architecture` and `tests/docs` pass
- [x] `docs/testing/migration_ci_lanes.md` documents the gate and the skip-table row
- [x] `actionlint` result recorded (or that it is not installed)
- [x] `git diff --stat` lists no path under `src/`

## Related Tickets
- TCK-20261008-BACKEND-IMAGE-BUILDS-FROM-UV-LOCK
- TCK-20261008-OPS-FILES-INTO-DOCKER-DIR

## Related Docs
- docs/testing/migration_ci_lanes.md
- docs/plans/codebase_health/repo_root_layout_ticket_brief.md

## Related Stored Artifacts
None.

## Related Code Areas
- .github/workflows/test.yml
- docker/backend.Dockerfile
- tests/static/

## Assumptions / Open Questions
- Research (planner): docs.docker.com/engine/release-notes/23.0 (BuildKit is the default builder, so `# syntax=` and cache/bind mounts work with plain `docker build`); docs.docker.com/build/ci/github-actions/{test-before-push,cache,checks}; docs.github.com secure-use (pinning).

## Implementation Notes
- `.github/workflows/test.yml`: new job `docker-build` ("Backend image build") placed after `frontend`, copying its shape: `needs: [changed-files, resync-gate]`, the `!cancelled()` + `needs.changed-files.result != 'success' || ...run_docker_build == 'true'` + `pr_content_unchanged` condition, `timeout-minutes: 15`. Steps: `actions/checkout@v5` (already allowlisted; no new `uses:`), `docker build --check -f docker/backend.Dockerfile .`, `docker build -f docker/backend.Dockerfile -t rpg-backend:ci .`, `docker run --rm rpg-backend:ci python -c "import sys, src; assert sys.version_info[:2] == (3, 13), sys.version"`, and an image-size line appended to `$GITHUB_STEP_SUMMARY` from `docker image inspect`. No docker/* actions, no cache, no push, no login.
- `changed-files`: `DOCKER_RE` and output `run_docker_build`, `=true` in both fail-open branches; header comment updated.
- Tests (decision 8.11): the four static pins listed in the testing handoff; three new tests in `test_ci_narrow_path_filtered_jobs.py`. Docs: `docs/testing/migration_ci_lanes.md` gate paragraph and a skip-table row ("not measured (new)"). Testing notice appended to `handoff_to_testing.md`.
- Not a required check, and why (a path-skipped required check stays "expected"): stated in the workflow comment and the docs.
- Design decisions are the planner's; recorded in `plan.md`. Options left for the owner are in Out of Scope and the docs paragraph.

## Test Summary
- Local run of the job's commands, one build, load about 3 of 6, nothing else heavy: `docker build --check` -> "Check complete, no warnings found", exit 0; `docker build -t rpg-backend:ci` exit 0; `docker run` Python assertion exit 0; size line prints `132 MiB` (`docker image inspect .Size`); the test image was removed afterwards. (`docker build --check` on the current Dockerfile needed no change; there was no warning to report.)
- `tests/static`, `tests/architecture`, `tests/docs`: 266 passed, 2 skipped, 1 xfailed. 23 more test files that read `test.yml` or name the frontend gate (`tests/tools`, `tests/unit/tools`, `tests/codebase`, `tests/integrity`): 647 passed, 3 skipped, with the known local 60 s snapshot make-target test deselected.
- `actionlint` 1.7.12 (run with `uvx --from actionlint-py actionlint .github/workflows/test.yml`): exit 0, no findings; `origin/main`'s workflow also gives no findings.
- Not verified locally: the job on a real runner (runner Docker version, `--check` support there); the first PR run shows it. `make knowledge-index-update` was not run (times out under the cap).

## Files Changed
- `.github/workflows/test.yml`
- tests: `tests/static/test_ci_step_summary_reporting.py`, `tests/static/test_ci_uv_install.py`, `tests/static/test_ci_registry_resync_skip_jobs.py`, `tests/static/test_ci_narrow_path_filtered_jobs.py`
- docs: `docs/testing/migration_ci_lanes.md`, `docs/plans/codebase_health/handoffs/handoff_to_testing.md`

## Completion Summary
CI now builds the backend image on pull requests that touch its inputs and checks it runs the CI Python, without becoming a required check. The pins were updated deliberately, local verification of the three commands and the test suites is recorded, and the job's first real-runner run is the one thing not yet seen.
