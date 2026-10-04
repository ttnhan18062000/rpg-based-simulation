---
status: active
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261003-CODE-HEALTH-GATES-FLIP-BLOCKING
artifact_type: plan
tags: [architecture, delivery]
---

# Plan — TCK-20261003-CODE-HEALTH-GATES-FLIP-BLOCKING

## Approach
Policy lives in code, not in flags or workflow YAML. Two named constants in `codebase/health/ratchet.py`:
- `REPORT_ONLY_TOOLS = frozenset({"jscpd", "ast_grep"})`: tools whose new/worse findings are listed and labelled "report-only" but do not set the exit code. Ticket 3 removes `ast_grep`.
- `SKIPPABLE_TOOLS = frozenset({"jscpd"})` (comment: network/npx dependency): tools whose failure to run is tolerated. Planner decision 2026-10-04: a separate constant, not derived from `REPORT_ONLY_TOOLS`. Ticket 3 leaves it alone.
A test asserts `SKIPPABLE_TOOLS <= REPORT_ONLY_TOOLS`, so a blocking tool can never be skippable.

**Ratchet.** `RatchetResult` keeps `failed` (any new/worse; the edit hook and the staged ratchet use it and must not change) and gains `blocking_failed` (a new/worse finding whose tool is not in `REPORT_ONLY_TOOLS`) and `report_only` (the new/worse findings of report-only tools). `format_report` labels report-only lines "(report-only)" and the verdict line says "OK ... (N report-only)". `format_summary` uses `blocking_failed`, drops "(advisory)" and the closing "Advisory only" sentence, and lists report-only findings in their own block. `compare` itself is unchanged.

**Skipped tools ("not measured", never "gone").** `scan.run_scan(..., skippable=frozenset())` returns the tuple of tools that raised `ToolUnavailableError` and were in `skippable`; a skipped tool's partial output is not read. `_cmd_check` passes `ratchet.SKIPPABLE_TOOLS`, collects findings for `tools - skipped`, and compares against rows with `row.tool not in skipped`, so the skipped tool's rows are neither "gone" nor touched. Output: a summary line "jscpd could not run (report-only); its findings were not measured" and a `::warning::` annotation (with `--annotate`) naming it. Exit stays 0/1 from `blocking_failed`; exit 2 (cannot run) is unchanged for ruff, complexipy, line_count, ast_grep and any registry error. With `--from DIR` nothing is skipped (an explicit source must be complete).

**`seed` and `tighten` refuse on a skipped tool** (my choice, planner's default): both call `run_scan` with an empty `skippable`, so any tool failure is `ToolUnavailableError` and exit 2, exactly as today. `snapshot` uses `OFFLINE_TOOLS` (no jscpd) and is untouched. The `.jscpd` rows can therefore only be deleted by an explicit full scan.

**CI.** Remove `continue-on-error` from the `Code health ratchet` step, the `mypy` step, and the `code-health` job (default; a broken setup must not read as a pass for a required check). Rename jobs "Code health (advisory)" to "Code health" and "Type check (informational)" to "Type check". `Package registry` keeps its step-level one (removed in ticket 2). The SARIF job changes only its comment (advisory permanently, decision 8.19). Comments rewritten. Keep the `scenario-lane` `PERF_RE` and the job list in sync and run `tests/unit/tools/test_scenario_lane_paths.py`.

**Makefile.** Drop `|| true` from `typecheck-py`; fix the `##` help of `typecheck-py` and `code-health`.

**Registry rows.** Tighten the 6 improved rows and delete the 4 gone rows (evidence: the ratchet output of 2026-10-04 on `053f459e4`), then re-check for "0 improved, 0 gone". Via `tighten --yes` after reading its list; no other row changes.

## Steps
1. Tests first (test_plan.md): ratchet policy, skip behaviour, seed/tighten refusal, summary text.
2. `ratchet.py`, `scan.py`, `__main__.py` changes; docstrings (the "advisory in CI" wording in `ratchet.py` and `__main__.py`).
3. Workflow, Makefile, then the tests that pin the old names and text (list in test_plan.md).
4. Tighten/delete the 10 rows; re-run `python3 -m codebase.health check`.
5. Docs and ledger: INFRA-TYPE-001 (text and `v2_evidence`), environment guide section retitled and rewritten (including one sentence on the skippable jscpd), standard Enforcement cells.
6. Soak review draft `python_code_craft_gates_soak_review.md` (window 2026-10-03 to 2026-10-17), with the exit-2 decision and reason; finalized after the window.
7. Re-run ratchet and mypy gate on fresh `origin/main` at the end and report to the planner.
8. Later, each with an AskUserQuestion: push, draft PR, the two live demos, the ruleset change (owner action).

## Scope guards
No `src/` file. No threshold, tool version or registry row change except the 10 above. jscpd stays report-only. SARIF job untouched except its comment. `failed`, `compare` and the edit/staged hooks keep today's behaviour.

## Acceptance-criteria map
- Soak review: step 6. Gates fail/pass on real PR runs: step 8 demos. Owner confirmed required checks: step 8. Green PR run link: step 8. No `src/` in diff: `git diff --stat origin/main...HEAD`.
