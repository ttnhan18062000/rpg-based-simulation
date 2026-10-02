---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20261002-CODE-HEALTH-SNAPSHOT-METRICS
artifact_type: investigation
tags: [schema]
---

# Investigation — TCK-20261002-CODE-HEALTH-SNAPSHOT-METRICS

## Context scan
- `search_docs` and `graphify query` (snapshot, `build_report`, `EXPECTED_SNAPSHOT_KEYS`): `tools/codebase_health_snapshot.py`, `tools/codebase_health_baseline.py`, `docs/agent-monitoring/codebase_health_history_schema.md` and the archived observatory epic are the only owners. No second metrics tool exists to reuse or conflict with. No history file exists, so no schema-1 record has ever been written.

## Findings
1. **The conflict the ticket names is real.** The snapshot module states it never computes a metric and enforces `set(build_report().keys()) == EXPECTED_SNAPSHOT_KEYS`; `test_snapshot_payload_built_from_real_build_report_dict_not_reimplemented` asserts the record equals `build_report()` apart from the version.
2. **Existing tests that touch it.** Of 26 tests in `test_codebase_health_snapshot.py` and `test_codebase_health_baseline.py`, with the second-source change in place and no test edited, 25 pass (including the end-to-end `make` tests) and exactly one fails: the "not reimplemented" contract test. That one assertion is the only existing-test edit needed.
3. **Option A (craft metrics inside `build_report()`) is ruled out.** It would make `make codebase-health-baseline` depend on ruff, complexipy and npx, and every test that builds a snapshot of a throwaway repository would have to run the tools there.
4. **Option B (second source), chosen.** `tools/code_health/metrics.py::compute_craft_metrics` is a pure function of findings plus registry rows; the snapshot merges its keys and the baseline target is untouched. Decided with the planner, who took it to the owner.
5. **jscpd stays out of the snapshot.** It needs `npx` (unpinned transitive dependencies), and the planner's review said it must not become a CI dependency; the end-to-end `make codebase-health-snapshot` test runs in CI. Duplication is reported from the registry (`craft_baseline_duplicate_file_pairs`, `craft_baseline_duplicated_lines`), labelled as baselined state, not a live measurement. Planner suggestion, accepted.
6. **No aggregate.** Fourteen separate integer keys; none named score, overall, combined or summary; tested.
7. **Ordering problem from the ticket.** `build_scorecard` indexed `latest[key]` and `previous[key]` directly, so a v2 record after a v1 record would raise. Craft dimensions are now optional per record: missing in `previous` shows "no trend data yet"; missing in `latest` leaves the dimension out. The 14 baseline dimensions remain required. No v1 record exists today; this makes a future mixed history safe.
8. **Found while testing:** complexipy refuses to run with no path when the repository has no `[tool.complexipy]` table. The scan now passes the scan root explicitly, which also makes `measure_craft_metrics` work on a throwaway repository (and fixes `check`/`seed` in the same case).
9. **Import across the two layouts.** The snapshot is a flat script that adds `tools/` to `sys.path`; `tools/code_health/` is a package. The snapshot adds the repository root to `sys.path` for the one `from tools.code_health.metrics import ...`, as its existing `sys.path` pattern does for its other imports. The flat files are not moved.
10. **Live measurement is fast and offline:** about 2 seconds over `src/` for ruff, complexipy and the line-count report.
