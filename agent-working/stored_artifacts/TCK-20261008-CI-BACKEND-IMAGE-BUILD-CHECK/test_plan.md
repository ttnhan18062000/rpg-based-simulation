---
status: historical
layer: architecture
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261008-CI-BACKEND-IMAGE-BUILD-CHECK
phase: done
date: 2026-10-08
tags: [architecture, delivery]
---

# test_plan — TCK-20261008-CI-BACKEND-IMAGE-BUILD-CHECK

Normal flow: the job's three docker commands succeed locally (one build, nothing else heavy); size line prints.
Edge: `DOCKER_RE` matches the image inputs and not src/, docs/, the frontend Dockerfile or nginx.conf; both fail-open branches emit `run_docker_build=true`.
Failure mode: the condition runs the job when the gate job fails and honours the re-sync gate; the job uses plain docker commands only (no push, login, cache).
Regression: tests/static, tests/architecture, tests/docs and the 23 other test files reading test.yml pass; actionlint finds nothing.

## Proof Plan
- level: static tests over the workflow plus one local integration run of the job's commands
- proof kind: automated tests, manual docker commands, actionlint
- oracle source: the workflow YAML, docker's own build and run results, actionlint
- expected effect: DOCKER_RE gates correctly and fails open; the three commands pass; no new finding from actionlint
- selected commands: `docker build --check -f docker/backend.Dockerfile .`, `docker build -f docker/backend.Dockerfile -t rpg-backend:ci .`, `docker run --rm rpg-backend:ci python -c "import sys, src; assert sys.version_info[:2] == (3, 13), sys.version"`, `pytest tests/static tests/architecture tests/docs` (266 passed), `uvx --from actionlint-py actionlint .github/workflows/test.yml` (exit 0)
