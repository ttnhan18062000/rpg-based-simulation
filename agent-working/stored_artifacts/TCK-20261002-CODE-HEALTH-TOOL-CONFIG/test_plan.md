---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20261002-CODE-HEALTH-TOOL-CONFIG
artifact_type: test_plan
tags: [setup]
---

# Test Plan — TCK-20261002-CODE-HEALTH-TOOL-CONFIG

## Proof Plan
- level: unit plus tool runs over the real repository
- proof kind: new unit tests for `line_count`; configuration-agreement tests; each tool run over `src/`
- oracle source: roadmap section 6.1 thresholds and the roadmap's own scan counts
- expected effect: every tool runs and reports on `src/`; thresholds in config equal 6.1; nothing under `src/` changes
- selected commands:

| Check | Command | Expected |
|---|---|---|
| New tests | `pytest tests/tools/test_code_health_line_count.py` | pass (22) |
| Nested and same-name symbols | in the file above | `Worker.step`, `step`, `step.<locals>.step` distinct |
| Boundaries | in the file above | function 50 ok / 51 warn / 80 warn / 81 fail; class 500/501; module 1000/1001 |
| Config agreement | in the file above | ruff 50/10/5/12/5, complexipy 15, size 50/80/500/1000, no formatter, `lint-py` check-only |
| Pinned tests unmodified | `pytest tests/static/ tests/tools/test_dashboard_makefile_targets.py tests/tools/test_ci_workflow_test_coverage.py tests/tools/test_tools_orphan_check.py tests/tools/test_search_mcp.py tests/architecture/test_docker_compose_dependency_hygiene.py tests/tools/test_knowledge_search.py::TestPyprojectDeps` | pass |
| Orphan live reference | `python3 tools/gate_checks/tools_orphan_check.py` after `git add` | `line_count.py` LIVE |
| Lock and export | `uv lock --check`; re-export; clean 3.13 `pip install -r requirements.txt` | 0; no diff; ok |
| Real runs | `make lint-py`, `code-health-complexity`, `code-health-size`, `code-health-dup` | each runs on 744 files |
| Dogfood | `ruff check tools/code_health`; mypy on `line_count.py` | clean |
| Scope | `git diff --stat 7dfd1349`; count of `# noqa`/`# type: ignore` in `src/` | no `src/`; 23 |
