---
status: historical
layer: architecture
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261008-OPS-FILES-INTO-DOCKER-DIR
phase: done
date: 2026-10-08
tags: [architecture, delivery]
---

# test_plan — TCK-20261008-OPS-FILES-INTO-DOCKER-DIR

Normal flow: `docker compose config -q` from the root; backend image builds from `docker/backend.Dockerfile` and runs `python -m src serve --help`; frontend image builds and contains the moved nginx.conf.
Edge: the two tests run from a different cwd (repo-root anchoring); `docker/` paths classified irrelevant by the scenario-lane gate.
Failure mode: a COPY source that no longer resolves would fail the frontend build (nginx.conf) - covered by the build.
Regression: scoped tests under tests/static, tests/architecture, tests/logging, tests/codebase impact, scenario-lane paths.

## Proof Plan
- level: integration (real image builds) plus unit/static tests
- proof kind: manual commands recorded in the ticket, and automated tests
- oracle source: docker's build/run results; `docker compose config`; pytest
- expected effect: both images build with the repo root as context, nginx.conf lands in the frontend image, tests pass independent of cwd
- selected commands: `docker compose config -q`, `docker build -f docker/backend.Dockerfile .`, `docker build -f docker/frontend.Dockerfile .`, `pytest tests/architecture/test_docker_compose_dependency_hygiene.py tests/logging/test_loki_cardinality.py tests/unit/tools/test_scenario_lane_paths.py tests/codebase/test_code_health_impact.py tests/static` (169 passed, 1 skipped)
