---
status: active
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20261002-CODE-HEALTH-SNAPSHOT-METRICS
artifact_type: plan
tags: [schema]
---

# Plan — TCK-20261002-CODE-HEALTH-SNAPSHOT-METRICS

1. `tools/code_health/metrics.py`: key lists, labels, pure `compute_craft_metrics(findings, rows)`, `measure_craft_metrics(root)` (offline tools plus the registry). `scan.py`: `run_scan` and `collect_findings` take a tool subset (`OFFLINE_TOOLS` excludes jscpd); complexipy gets the scan root explicitly.
2. `tools/codebase_health_snapshot.py`: `EXPECTED_BASELINE_KEYS` plus craft keys give `EXPECTED_SNAPSHOT_KEYS`; `SNAPSHOT_SCHEMA_VERSION` 2; `build_snapshot_record` and `write_snapshot` take an optional prepared `craft_metrics`; the scorecard tolerates records without craft keys; labels and order include the craft dimensions; docstring states the second source.
3. `docs/agent-monitoring/codebase_health_history_schema.md`: field tables, version table, mixed-version reading rule, in the same commit as step 2.
4. New tests (new files only); one assertion in an existing test edited, as the owner decides.
5. Commit; then take the first snapshot with `make codebase-health-snapshot` and commit the one-record history file.

## Scope guards
No `src/`, `.claude/`, `CLAUDE.md`, CI, `build_report()`, baseline target, or second metrics tool; no combined score; no real `agent-monitoring/` path in any test.

## Acceptance-criteria map
| Criterion | Step |
|---|---|
| Craft metrics in the record; keys, version and doc updated in one commit | 2, 3 |
| `build_report()` key check or contract updated, choice recorded | 2; ticket notes |
| No aggregate key; the no-aggregate test passes | 1, 4 |
| Existing snapshot and baseline tests pass, edits listed | 4 |
| New tests: each craft key numeric on a fixture; none writes under real `agent-monitoring/` | 4 |
| History file with exactly one v2 record | 5 |
| Make targets exit 0 end to end | 4, 5 |
| No `src/`, `.claude/`, `CLAUDE.md` | all |
