---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20261002-UV-DECLARE-AND-LOCK
artifact_type: test_plan
tags: [setup]
---

# Test Plan — TCK-20261002-UV-DECLARE-AND-LOCK

No new test: no new tooling is added, and the existing static tests already pin the outcome.

## Proof Plan

- level: static and environment
- proof kind: existing static tests plus install and resolution commands
- oracle source: the pre-change `requirements.txt` (47 pins) and the ticket's acceptance criteria
- expected effect: same versions for every old pin; newly pinned transitives only; no ML stack
- selected commands:

| Check | Command | Expected |
|---|---|---|
| Lock current | `uv lock --check --system-certs` | exit 0 |
| Export reproducible | re-run the export to a temp file, diff | no diff |
| Name and version sets | script comparing old and new `requirements.txt` | nothing missing, no version changed |
| Clean install | `uv venv --python 3.13 --seed`, then `pip install -r requirements.txt` | exit 0 |
| Pinned tests, run from the clean environment | `pytest tests/static/ tests/tools/test_dashboard_makefile_targets.py tests/tools/test_ci_workflow_test_coverage.py tests/tools/test_search_mcp.py tests/architecture/test_docker_compose_dependency_hygiene.py tests/tools/test_codebase_health_baseline.py tests/tools/test_knowledge_search.py::TestPyprojectDeps` | pass |
| uv sync | `uv sync --frozen --python 3.13 --system-certs` into a scratch environment; import the newly declared packages; torch absent | pass |
| Diff scope | `git diff --stat 7dfd1349` | no `src/`, `.claude/`, `CLAUDE.md`, `tests/` path |

Failure modes covered: ML stack leaking into the export (static test); a stale lock (`--check`); a marker or format pip rejects (clean install).
