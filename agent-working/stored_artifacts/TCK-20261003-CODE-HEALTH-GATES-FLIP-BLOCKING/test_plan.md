---
status: active
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261003-CODE-HEALTH-GATES-FLIP-BLOCKING
artifact_type: test_plan
tags: [architecture, delivery]
---

# Test plan — TCK-20261003-CODE-HEALTH-GATES-FLIP-BLOCKING

New tests (in `tests/codebase/`, in the existing `test_code_health_ci_summary.py` and `test_code_health_ratchet*.py` style with the scratch-repo fixtures):
1. New jscpd finding and new ast_grep finding: exit 0, both listed and labelled report-only; summary names them.
2. New ruff, complexipy and line_count finding: exit 1 (one per tool).
3. `SKIPPABLE_TOOLS <= REPORT_ONLY_TOOLS`; `REPORT_ONLY_TOOLS == {"jscpd", "ast_grep"}` (ticket 3 flips this pin).
4. jscpd unavailable: exit 0, summary line "jscpd could not run (report-only); its findings were not measured", exactly one `::warning::` naming jscpd.
5. jscpd unavailable plus existing jscpd rows: 0 gone, rows untouched, other tools still compared (a new ruff finding still gives exit 1).
6. ruff, complexipy, line_count and ast_grep unavailable: exit 2 each; unusable registry: exit 2.
7. `seed --force` and `tighten --yes` with jscpd unavailable: exit 2, registry file byte-identical.
8. `RatchetResult.failed` unchanged (edit hook / staged ratchet tests stay green); `blocking_failed` per side.
9. Summary text: no "(advisory)", no "Advisory only" sentence; report-only block present.

Existing tests to update (they pin advisory status or old names; edit only what pins advisory behaviour): `tests/codebase/test_mypy_gate.py`, `test_typecheck_gate_configured.py`, `test_code_health_ci_summary.py`, `test_package_registry.py` (job name only), `test_ci_code_health_sarif.py`, `test_code_health_sarif_feedback.py`, `test_edit_ratchet_hook.py` (only if it pins wording), `tests/static/test_ci_uv_install.py`, `test_ci_step_summary_reporting.py`; `tests/unit/tools/test_scenario_lane_paths.py` runs unchanged as a guard.

Run before the first push: `tests/codebase` (two chunks of 12 files, under the 2G cap), `tests/static`, `tests/tools/test_*guard*.py`, `tests/unit/tools/test_scenario_lane_paths.py`; compare pass/skip counts with main.

Mutation proof for the new policy: remove `jscpd` from `REPORT_ONLY_TOOLS` (test 1 must fail), add `ruff` to `SKIPPABLE_TOOLS` (test 3 must fail), drop the `skipped` row filter (test 5 must fail).
