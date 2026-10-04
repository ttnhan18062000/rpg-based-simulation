---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261004-AST-GREP-SARIF-AND-SNAPSHOT
phase: inprogress
date: 2026-10-04
tags: [architecture, delivery]
---

# TCK-20261004-AST-GREP-SARIF-AND-SNAPSHOT

## Title
M5 follow-up: ast-grep in the SARIF feedback and the snapshot metrics

## Status
INPROGRESS

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Add ast-grep to `codebase/gates/sarif_feedback.py` and one count per rule (n3, n4, e3) to the snapshot metrics. Advisory; ast-grep flip (soak ends 2026-10-18) is untouched.

## Scope
- SARIF: also run `ast-grep scan --format sarif` with `codebase/rules/sgconfig.yml` on changed `src/` files; filter findings whose `(file, symbol, rule)` is an `ast_grep` registry row within ceiling; missing binary is exit 2 with a summary line and warning, never a silent pass
- Snapshot: add `ast_grep` to `OFFLINE_TOOLS`; add `n3`, `n4`, `e3` dimensions to `compute_craft_metrics`; existing dimensions unchanged on the same tree (test before/after); check history schema accepts new keys, additive change documented if needed
- Tests: new, grandfathered and missing-binary SARIF cases; metrics with and without findings; existing dimensions unchanged

## Out of Scope
- Making ast-grep blocking
- New rules

## Acceptance Criteria
- [ ] SARIF reports a new ast-grep finding and omits a grandfathered one
- [ ] Missing binary gives exit 2 with a warning
- [ ] Three new snapshot dimensions; existing values identical on the fixture
- [ ] No threshold, tool version or registry row changed
- [ ] `git diff --stat <base>...HEAD` lists no path under src/

## Related Tickets
- TCK-20261004-AST-GREP-RULE-PACK-ADVISORY
- TCK-20261004-AST-GREP-RULE-PACK-FLIP-BLOCKING

## Related Docs
- docs/plans/codebase_health/python_code_craft_m6_agent_integration_ticket_brief.md
- docs/plans/codebase_health/python_code_craft_roadmap.md
- docs/plans/codebase_health/python_code_craft_m5_structure_ticket_brief.md

## Related Stored Artifacts
None.

## Related Code Areas
- codebase/gates/sarif_feedback.py
- codebase/health/scan.py
- codebase/health/metrics.py
- .github/workflows/test.yml

## Assumptions / Open Questions
- Owner decision 8.17 (2026-10-04): codebase implements M6 although `.claude/**` is agent-working's territory; the PR body names agent-working as owner of those paths
- Nothing here blocks a PR or tool call; M4 and M5 soaks are not disturbed

## Implementation Notes
**SARIF:** `_tool_sarif` also runs `ast-grep scan --config codebase/rules/sgconfig.yml <files> --format sarif`; `filter_ast_grep` groups results by (file, enclosing symbol, rule) with the symbol from the new public `adapters.symbol_resolver` (`adapt_ast_grep` now calls it, identical behaviour), drops a group within its row ceiling and keeps an over-ceiling or row-less group whole. A missing binary is a `SarifError` (exit 2, summary line, warning). **Finding:** ast-grep's SARIF has no SARIF `version` of 2.1.0 (it carries its own release, e.g. `0.45.3`), so `parse_sarif` got `check_version=False` for it; only `runs`/`results` are used and the uploaded file is wrapped with `SARIF_VERSION` by `build_sarif`.
**Snapshot:** `ast_grep` joined `OFFLINE_TOOLS`; three live keys added; `SNAPSHOT_SCHEMA_VERSION` 2 to 3 (the schema doc's paired-change rule; the brief's "additive" wording did not hold) with the version-3 row and field rows in `docs/agent-monitoring/codebase_health_history_schema.md`; old history lines untouched; a reader treats a missing key as not measured. `snapshot` now exits 2 with "snapshot not written" if a code-health tool is unavailable, so a missing ast-grep is never recorded as 0.
**Snapshot callers checked (condition 1):** the only callers of `measure_craft_metrics`/`write_snapshot` are `make codebase-health-snapshot` (on demand, not CI; runs `python3 -m codebase.reports.codebase_health_snapshot`, needs the `lint` group like ruff/complexipy already do) and the tests under `tests/codebase/` (CI job `tools-a-e`, which installs the lint group). No CI step, git hook, settings hook or script writes the history file.
`scan._find` was renamed to the public `scan.find_tool` (its three call sites and three test monkeypatches), so no module reaches into another's private name (planner nit, rule N3).
Cost: ast-grep adds about 0.4 s warm to a snapshot (3.5 s craft total; `build_report` alone is about 42 s); the first run after files change was 18 to 27 s cold.

## Test Summary
SARIF, metrics, snapshot-craft and ast-grep rule tests: 83 passed. Full `tests/codebase` (minus the snapshot file): 394 passed, 6 failed; 1 was the stale pin `test_ast_grep_is_in_the_full_scan_but_not_the_snapshot_set` (updated, now passes); the other 5 are the known local failures (3 `test_real_path_*` graph tests, the baseline make-target test, a load-sensitive churn test). `test_make_target_runs_successfully_end_to_end` times out locally at 60 s (it runs three snapshots and `build_report` alone is about 42 s; a known local failure on clean main, not caused by this ticket).

## Files Changed
codebase/gates/sarif_feedback.py, codebase/health/{adapters,metrics,scan}.py, codebase/reports/codebase_health_snapshot.py, docs/agent-monitoring/codebase_health_history_schema.md (agent-working's area), tests/codebase/{test_code_health_sarif_feedback,test_code_health_metrics,test_codebase_health_snapshot,test_codebase_health_snapshot_craft}.py, ticket and staging artifacts

## Completion Summary
