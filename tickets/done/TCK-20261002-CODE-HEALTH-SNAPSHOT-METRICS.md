---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20261002-CODE-HEALTH-SNAPSHOT-METRICS
phase: done
date: 2026-10-02
tags: [schema]
---

# TCK-20261002-CODE-HEALTH-SNAPSHOT-METRICS

## Title
M3c: Add craft metrics to the codebase health snapshot and take the first snapshot

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Last part of measuring and baselining code health: the author wants craft metrics added to the existing tools/codebase_health_snapshot.py and the first snapshot taken, rather than a second metrics tool being built (roadmap Section 4 reuse rule). No codebase health snapshot has ever been taken, so this also produces the first trend record. The shared constraints apply: no src/ edits, no simulation behaviour change, tests/ changes limited to tests for the new tooling, no edits to governing files or the agent-working domain.

## Scope
- Decide and record where craft metrics are computed: added to tools/codebase_health_baseline.py::build_report(), or supplied to the snapshot as a second metric source with its documented contract updated
- Add per-dimension craft metric keys (from the tools/code_health/ outputs) to the snapshot record, with no aggregate or combined score
- Update EXPECTED_SNAPSHOT_KEYS, bump SNAPSHOT_SCHEMA_VERSION from 1, and update docs/agent-monitoring/codebase_health_history_schema.md in the same commit
- Add tests for the new metric keys, never targeting the real agent-monitoring/codebase_health_history.jsonl
- Take the first snapshot after the schema bump has landed, producing the history file with one record

## Out of Scope
- A second metrics tool or a combined health score (D24 sections J/M)
- Tool configuration, adapters, ratchet and exceptions registry (the other two M3 tickets)
- Moving the flat tools/codebase_health_*.py scripts into a package
- Backward-compatibility handling for schema v1 history rows (none exist; the history file does not exist yet)
- Changing tools/code_health_impact.py or tools/pr_impact_report.py behaviour
- CI gating of snapshot values (M4)
- Any file under src/, CLAUDE.md, .claude/settings.json, hooks, .claude/agents/, .claude/workflows/, .claude/skills/

## Acceptance Criteria
- [x] Craft metrics appear in the snapshot record, and EXPECTED_SNAPSHOT_KEYS, SNAPSHOT_SCHEMA_VERSION (bumped from 1) and docs/agent-monitoring/codebase_health_history_schema.md are updated together in one commit
- [x] set(build_report().keys()) == EXPECTED_SNAPSHOT_KEYS still holds, or the snapshot's documented contract and module docstring are updated to describe the second metric source; the choice is recorded in the ticket
- [x] No aggregate or combined score key is added: tests/tools/test_codebase_health_snapshot.py::test_scorecard_output_has_no_aggregate_or_combined_score_field passes
- [x] pytest tests/tools/test_codebase_health_snapshot.py tests/tools/test_codebase_health_baseline.py passes, and any edit to an existing test in those files is limited to what the schema bump itself requires and is listed in the ticket
- [x] New tests assert each craft metric key is present with a numeric value on a fixture, and none writes under the real agent-monitoring/ directory (test_no_test_target_path_resolves_under_real_agent_monitoring_dir passes)
- [x] agent-monitoring/codebase_health_history.jsonl exists with exactly one record (the first snapshot ever taken) containing the new craft metric keys and the bumped schema version
- [x] The existing snapshot and baseline make targets still exit 0 end to end (test_make_target_runs_successfully_end_to_end and test_make_target_runs_successfully_with_plausible_values pass)
- [x] 'git diff --stat <base>...HEAD' lists no path under src/, no path under .claude/ and not CLAUDE.md

## Related Tickets
- TCK-20261002-PYTHON-CODE-CRAFT-EPIC
- TCK-20261002-CODE-HEALTH-TOOL-CONFIG
- TCK-20261002-CODE-HEALTH-RATCHET-REGISTRY
- TCK-20260822-CODEBASE-HEALTH-SNAPSHOT-SCORECARD
- TCK-20260819-STANDARD-CODEBASE-HEALTH-BASELINE-TARGET
- TCK-20260817-CODEBASE-HEALTH-OBSERVATORY-TOOLING-EPIC
- TCK-20260819-STANDARD-CODE-HEALTH-IMPACT-COMMAND

## Related Docs
- docs/plans/codebase_health/python_code_craft_roadmap.md
- docs/plans/codebase_health/python_code_craft_foundation_ticket_brief.md
- docs/agent-monitoring/codebase_health_history_schema.md
- docs/guidelines/repo_tooling_layout.md

## Related Stored Artifacts
- stored_artifacts/TCK-20261002-CODE-HEALTH-SNAPSHOT-METRICS/plan.md
- stored_artifacts/TCK-20261002-CODE-HEALTH-SNAPSHOT-METRICS/investigation.md
- stored_artifacts/TCK-20261002-CODE-HEALTH-SNAPSHOT-METRICS/test_plan.md

## Related Code Areas
- tools/codebase_health_snapshot.py
- tools/codebase_health_baseline.py
- tools/code_health_impact.py
- tools/pr_impact_report.py
- docs/agent-monitoring/codebase_health_history_schema.md
- Makefile
- docs/plans/codebase_health/python_code_craft_roadmap.md

## Assumptions / Open Questions
- Design conflict to resolve in the plan: tools/codebase_health_snapshot.py states it never computes metrics itself and enforces key equality with build_report(). Adding craft metrics to build_report() makes 'make codebase-health-baseline' depend on external tools; a second metric source changes the documented contract and test_snapshot_payload_built_from_real_build_report_dict_not_reimplemented
- That existing test may need an edit under the second-source option; the shared constraint limits tests/ changes to tests for new tooling, so this needs an owner decision before choosing that option
- Ordering: build_scorecard indexes latest[key] and previous[key] directly, so a v2 record after a v1 record would raise KeyError. The history file does not exist today, so the schema bump must land before the first snapshot is taken
- The snapshot tooling uses sys.path.insert and flat modules while tools/code_health/ uses package imports; importing across the two needs care, and the flat files are not moved
- Runs last in M3: depends on the adopted tool list and outputs from the other two M3 tickets
- The first snapshot record is committed data under agent-monitoring/ and is staged with the ticket's commit
- Layer `observability` was inferred: the snapshot history and its schema doc live under agent-monitoring/ (docs/agent-monitoring/, agent-monitoring/codebase_health_history.jsonl)

## Implementation Notes
Hand-orchestrated by the `codebase-implementer` session in worktree `rpg-code-craft`, branch `python-code-craft`.

**Design decision (owner decision 2026-10-02, relayed by codebase-planner): "Second source, offline".** Craft metrics are a second metric source, not part of `build_report()`; duplication is read from the registry; no npx in the snapshot. Reasons and the rejected option are in `investigation.md` (Option A would make `make codebase-health-baseline` depend on ruff, complexipy and npx).

- `tools/code_health/metrics.py` (new): pure `compute_craft_metrics(findings, rows)` and `measure_craft_metrics(root)`. Fourteen integer keys, no aggregate or combined key: ten live (`craft_ruff_findings`, `craft_correctness_findings`, `craft_missing_public_docstrings`, `craft_missing_annotations`, `craft_functions_over_cognitive_limit`, `craft_functions_over_length_limit`, `craft_classes_over_length_limit`, `craft_modules_over_length_limit`, `craft_longest_function_lines`, `craft_highest_cognitive_complexity`) from ruff, complexipy and the line-count report, about 2 s and offline; four registry-derived (`craft_baseline_rows`, `craft_baseline_unreviewed_rows`, `craft_baseline_duplicate_file_pairs`, `craft_baseline_duplicated_lines`), labelled "(registry)" in the scorecard because they describe the baselined state, not a live measurement.
- `tools/codebase_health_snapshot.py`: `EXPECTED_BASELINE_KEYS` (the old set) and `EXPECTED_SNAPSHOT_KEYS` = baseline plus craft keys; `SNAPSHOT_SCHEMA_VERSION` 1 to 2; `build_snapshot_record` and `write_snapshot` take an optional prepared `craft_metrics`; module docstring states the second source. **Contract choice recorded:** `set(build_report().keys()) == EXPECTED_BASELINE_KEYS` still holds, and the snapshot's documented contract now describes the second source; `build_report()` and the baseline target are unchanged.
- `build_scorecard` tolerates a record without craft keys (previous lacks a key: "no trend data yet"; latest lacks it: dimension left out), which removes the KeyError the ticket warned about for a v2 record after a v1 record. The 14 baseline dimensions stay required.
- `tools/code_health/scan.py`: `run_scan` and `collect_findings` take a tool subset (`OFFLINE_TOOLS` excludes jscpd); complexipy is given the scan root explicitly, because it refuses to run with no path in a repository that has no `[tool.complexipy]` table (found when a throwaway-repository test failed).
- `docs/agent-monitoring/codebase_health_history_schema.md`: field tables, version table, mixed-version reading rule; same commit as the key set and version bump (`995b7d6f`).
- The snapshot imports `tools.code_health.metrics`, so it adds the repository root to `sys.path` for that one import, matching its existing `sys.path` pattern; the flat `tools/codebase_health_*.py` files were not moved.

**Existing test edited (the only one, as the owner approved):** `tests/tools/test_codebase_health_snapshot.py::test_snapshot_payload_built_from_real_build_report_dict_not_reimplemented` now compares the record minus `snapshot_schema_version` and minus the craft keys with `build_report()`; the non-craft part must still equal `build_report()` exactly. No other existing test was touched; the other 25 tests in that file and `test_codebase_health_baseline.py` pass unmodified.

**First snapshot:** taken with `make codebase-health-snapshot` after the schema bump was committed. `agent-monitoring/codebase_health_history.jsonl` has exactly one record, `snapshot_schema_version` 2, with ruff 6,472; correctness 1,050; missing docstrings 1,908; missing annotations 378; functions over cognitive limit 384; over length limit 251; classes over 21; modules over 11; longest function 2,409 lines; highest cognitive complexity 789; baseline rows 3,617 (all unreviewed); duplicated file pairs 58; duplicated lines 1,392. The baseline dimensions in that record (for example 338 commits) are what `build_report()` returned in this worktree.

**Not done:** `make knowledge-index-update` (worktree has no `knowledge-index/`; post-merge step is in the epic).

## Test Summary
- New: `tests/tools/test_code_health_metrics.py` (8) and `tests/tools/test_codebase_health_snapshot_craft.py` (11): pure computation per key, key sets disjoint and labelled with no aggregate word, registry-derived keys come from rows only, offline subset needs no jscpd output, record and scorecard with craft keys, v1-then-v2 and v2-then-v1 history, loud mismatch on missing or extra craft keys, no tool run when a prepared dict is given, first-snapshot round trip. All history paths are under `tmp_path`.
- `pytest tests/tools/test_codebase_health_snapshot.py tests/tools/test_codebase_health_baseline.py tests/tools/test_codebase_health_snapshot_craft.py tests/tools/test_code_health_metrics.py tests/static tests/docs tests/tools/test_tools_orphan_check.py tests/tools/test_dashboard_makefile_targets.py`: 185 passed, 2 skipped, 1 xfailed. This includes `test_scorecard_output_has_no_aggregate_or_combined_score_field`, `test_no_test_target_path_resolves_under_real_agent_monitoring_dir`, and both end-to-end `make` tests.
- `make codebase-health-snapshot` and `make codebase-health-scorecard` against the real repository: exit 0; history file has one record.
- `python3 -m tools.code_health check`: 0 new, 0 worse, 3,617 unchanged. `ruff check tools/code_health` and mypy are clean.
- This ticket's diff has no path under `src/`, `.claude/`, `.github/` or `CLAUDE.md`; `# noqa` / `# type: ignore` under `src/` unchanged at 23.
- Not run: the wider test suite.

## Files Changed
- tools/code_health/metrics.py (new); tools/code_health/scan.py; tools/codebase_health_snapshot.py
- tests/tools/test_code_health_metrics.py, tests/tools/test_codebase_health_snapshot_craft.py (new); tests/tools/test_codebase_health_snapshot.py (one assertion)
- docs/agent-monitoring/codebase_health_history_schema.md
- agent-monitoring/codebase_health_history.jsonl (new, one record)
- docs/REGISTRY.yaml (regenerated); stored_artifacts/TCK-20261002-CODE-HEALTH-SNAPSHOT-METRICS/

## Completion Summary
Each codebase health snapshot now carries 14 separate craft metrics from a second, offline source, under schema version 2, and the first snapshot is recorded. There is no combined score, `build_report()` and the baseline target are unchanged, and nothing in `src/` was touched.
