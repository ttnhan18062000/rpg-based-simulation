---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20261002-CODE-HEALTH-SNAPSHOT-METRICS
artifact_type: test_plan
tags: [schema]
---

# Test Plan — TCK-20261002-CODE-HEALTH-SNAPSHOT-METRICS

## Proof Plan
- level: unit, plus the existing end-to-end `make` tests and one real snapshot
- proof kind: new tests on pure computation and on a prepared fixture; existing suite unmodified except one assertion
- oracle source: the ticket's acceptance criteria and the existing snapshot contract tests
- expected effect: schema v2 record with 14 craft keys; v1 history cannot break the scorecard; baseline target unaffected
- selected commands:

| Check | Command | Expected |
|---|---|---|
| Pure metrics, key sets, no aggregate, offline subset | `pytest tests/tools/test_code_health_metrics.py` | pass (8) |
| Record and scorecard with craft keys, mixed history, loud mismatch, no tool run when a dict is given | `pytest tests/tools/test_codebase_health_snapshot_craft.py` | pass (11) |
| Existing contract and end-to-end tests | `pytest tests/tools/test_codebase_health_snapshot.py tests/tools/test_codebase_health_baseline.py` | pass, with only the one assertion edited |
| Neighbouring code-health tests and orphan check | `pytest tests/tools/test_code_health_*.py tests/tools/test_tools_orphan_check.py` | pass |
| Docs | `pytest tests/docs/`; frontmatter validator on the schema doc | pass |
| Real run | `make codebase-health-snapshot`, then `make codebase-health-scorecard` | exit 0; one-line history file with `snapshot_schema_version` 2 |
| Dogfood | `ruff check tools/code_health`; mypy with `--explicit-package-bases` | clean |
| Scope | `git diff --stat 7dfd1349` | no `src/`, `.claude/`, `CLAUDE.md` |
