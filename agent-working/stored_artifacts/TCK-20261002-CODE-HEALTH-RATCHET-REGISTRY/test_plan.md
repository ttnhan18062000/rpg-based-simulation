---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261002-CODE-HEALTH-RATCHET-REGISTRY
artifact_type: test_plan
tags: [testing]
---

# Test Plan — TCK-20261002-CODE-HEALTH-RATCHET-REGISTRY

## Proof Plan
- level: unit and end to end in a scratch repository, plus one real run
- proof kind: tests fed with real captured tool output; CLI runs against a scratch `--root`
- oracle source: the ticket's acceptance criteria and the real tools' own output
- expected effect: ratchet fails exactly on new or worse violations and never on line moves, improvements or vanished rows
- selected commands:

| Check | Where | Expected |
|---|---|---|
| Adapters on real output (ruff, complexipy, jscpd, line_count) | `tests/tools/test_code_health_adapters.py` | normalised records with file, symbol or null, tool, rule, value |
| Ratchet: same scan passes; new fails; above ceiling fails; line move passes; improved and gone reported | `tests/tools/test_code_health_ratchet_registry.py` | as stated |
| Registry: missing field, duplicate key, nonexistent file (one test each), bad types, bad JSON | same | rejected |
| Delete, tighten, seed refuse/force, list, validate, unusable input | same (CLI) | exit codes 0/1/2 as documented |
| Same-name-pairs link | same | duplication rows link, nothing else |
| Repeated keys | adapters tests | max or sum, deterministic |
| Real run | `python3 -m tools.code_health seed`, then `make code-health` | 3,617 rows; exit 0 |
| Pinned and neighbouring tests | `pytest tests/static/ tests/tools/test_dashboard_makefile_targets.py tests/tools/test_ci_workflow_test_coverage.py tests/tools/test_tools_orphan_check.py tests/tools/test_search_mcp.py tests/architecture/test_docker_compose_dependency_hygiene.py tests/docs/` and `-k parity` under `tests/tools` | pass |
| Dogfood | `ruff check tools/code_health`; mypy with `--explicit-package-bases` | clean |
| Scope | `git diff --cached HEAD --name-only` | no `src/`, `.claude/`, `CLAUDE.md`, `.github/`; no existing test modified; `# noqa`/`# type: ignore` in `src/` stays 23 |

No test reads the live registry or live `src/`, so another session editing `src/` cannot break the suite.
