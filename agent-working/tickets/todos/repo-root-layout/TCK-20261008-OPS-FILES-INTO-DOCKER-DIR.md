---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20261008-OPS-FILES-INTO-DOCKER-DIR
phase: open
date: 2026-10-08
tags: [architecture, delivery]
---

# TCK-20261008-OPS-FILES-INTO-DOCKER-DIR

## Title
Move the ops files into docker/ and rename the compose file to compose.yaml

## Status
OPEN

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
- [ ] `docker compose config` passes from the root
- [ ] `docker compose build` (or A1's build plus the frontend build) succeeds under the memory cap
- [ ] The changed tests pass
- [ ] `git diff --stat` lists no path under `src/`

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

## Test Summary

## Files Changed

## Completion Summary
