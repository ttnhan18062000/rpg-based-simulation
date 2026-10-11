---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261009-RPG-GATE-SCHEDULED-AND-DISPATCH-WORKFLOW
phase: open
date: 2026-10-09
tags: [testing, regression]
---

# TCK-20261009-RPG-GATE-SCHEDULED-AND-DISPATCH-WORKFLOW

## Title
A daily scheduled job and an on-demand dispatch run the rpg gate report, advisory, with a rolling issue

## Status
INPROGRESS

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Child 5 of TCK-20261009-RPG-GATE-REPORT-TESTING-INFRA-EPIC. Reuse the #464 pattern (a `gate` job that skips a scheduled run when main's head was already reported within 24 h; fail open; pipefail) and the slow suite's rolling issue.

## Scope
1. A new workflow (for example `.github/workflows/rpg-gate-report.yml`): `schedule` once a day at an off-hour minute, plus `workflow_dispatch` with a `ref` input (a batch author runs it on their branch and links the report in the PR).
2. The gate job for scheduled runs only (reuse `tools/test_architecture/slow_regression_gate.py`, parameterised by workflow and suite job name, rather than copy it).
3. A matrix sized from child 3's measured cost (by world, or a shard of (world, seed) pairs); an aggregate job runs child 4's evaluation and writes the step summary.
4. One rolling issue for main's scheduled runs only (dispatch runs on a branch write the step summary and an artifact, never the issue). It records NEW/RESOLVED per metric, as #390 does for tests.
5. Advisory: the workflow is not a required check. The job is red only per child 4's verdict rule.
6. A shape test for the workflow (triggers, gate, permissions, no push/pull_request trigger).

## Out of Scope
- Making it required (principle 8).

## Acceptance Criteria
1. One live scheduled run and one live dispatch run on a branch, with ids recorded in the ticket.
2. The rolling issue was created or updated by the scheduled run, and untouched by the dispatch run.
3. A gate-skip on an unchanged head (live, or unit-tested if main keeps moving for 3 days after merge).
4. Roadmap §4.1/§4.2 updated with the new evidence layer (the epic's AC4).
5. Standard close.

## Related Tickets
- TCK-20261009-RPG-GATE-REPORT-TESTING-INFRA-EPIC; depends on TCK-20261009-RPG-GATE-REPORT-STATES-AND-SAME-SHA-RERUN; reuses TCK-20261009-SLOW-REGRESSION-OFF-HOUR-AND-SKIP-UNCHANGED-MAIN's gate

## Related Docs
None.

## Related Stored Artifacts
None.

## Related Code Areas
- `.github/workflows/slow-regression.yml` (pattern), `tools/test_architecture/slow_regression_gate.py`, `tools/test_architecture/slow_regression_report.py`

## Assumptions / Open Questions
None.

## Implementation Notes
- `.github/workflows/rpg-gate-report.yml` (header comment states the design): triggers are `schedule` (`23 5 * * *`, daily, off the hour, clear of the slow suite's slots) and `workflow_dispatch` with a `ref` input; no push or pull_request trigger; a non-cancelling concurrency group; job-level permissions only (`issues: write` on the report job alone).
- Jobs: `gate` (the #464 decision, scheduled events only, `set -o pipefail`, fail open) -> `plan` (rpg's config present? worlds for the matrix) -> `shard` (one job per world, `fail-fast: false`, 120 min, `--workers 2` for the 2-vCPU runner, uploads `rpg-gate-docs-<world>`) -> `report` (named `RPG gate report`, the job the gate looks for; downloads the documents, runs `rpg_gate_report` with its same-SHA rerun, writes the step summary, uploads the report and any rerun documents, updates the rolling issue on scheduled runs only, and ends on the verdict, red only per child 4's rule).
- Missing config: `plan` says so in the summary; `shard` and `report` are skipped, the run is green and counts as not tested. Missing metric module: every run is `metric_error` / `no-data`, the verdict is green, and the summary and the issue say plainly that rpg's module is absent.
- The gate module is reused, not copied: `slow_regression_gate.py` gained `--workflow` and `--suite-job` (defaults unchanged); `GhClient` in the slow report gained a `label` argument (default unchanged) so the new issue has its own label.
- New `rpg_gate_issue.py` (rolling issue, label `rpg-gate-report`, separate from #390; tracks fail/drift/unstable, run errors and a synthetic `rpg-metric-module-absent` entry; NEW/RESOLVED comments; closes when empty), `rpg_gate_plan.py`, `--only-world` on the harness, and a `module_absent` flag plus banner in the report.
- Cost planning: 3 worlds x 5 seeds x 5000 ticks is about 50-60 min wall on one 2-vCPU runner (testing-planner); sharding by world runs the shards in parallel and bills the same minutes. Measured per-run figures are in the harness ticket.
- Roadmap §4.1/§4.2 gain the rpg gate report evidence layer (epic AC4).

## Test Summary
Before merge: `tests/unit/tools` plus the workflow-reading static and tool tests (`test_ci_slow_workflow_shape`, the new `test_ci_rpg_gate_workflow_shape`, `test_ci_narrow_path_filtered_jobs`, `test_ci_step_summary_reporting`, `test_corpus_diversity_ci_isolation`, `test_ci_workflow_test_coverage`, `test_ci_split_tools_jobs`): 912 passed. New: `test_rpg_gate_workflow_support.py` (13: the gate for a second workflow and suite job, the plan with and without a config, `--only-world`, the absent-module banner, the rolling issue lifecycle and its own label) and `test_ci_rpg_gate_workflow_shape.py` (10: triggers, off-hour daily cron, ref input, non-cancelling group, gate with pipefail and its flags, the suite job name, skip rules, config-missing stop, shard settings, report job order, issue on schedule only, least-privilege permissions, advisory).
Live evidence is OPEN (a workflow can be dispatched only once it is on the default branch): AC1 one scheduled run and one dispatch run on a branch with ids and the measured wall time; AC2 the issue created or updated by the scheduled run and untouched by the dispatch run; AC3 a gate skip on an unchanged head (or the unit test if main keeps moving for 3 days). Until rpg's config and metric module exist, those runs show the absent-config or absent-module path.

## Files Changed
- new: `.github/workflows/rpg-gate-report.yml`, `tools/test_architecture/rpg_gate_issue.py`, `tools/test_architecture/rpg_gate_plan.py`, `tests/static/test_ci_rpg_gate_workflow_shape.py`, `tests/unit/tools/test_rpg_gate_workflow_support.py`
- changed: `tools/test_architecture/slow_regression_gate.py`, `tools/test_architecture/slow_regression_report.py` (`GhClient` label), `tools/test_architecture/rpg_gate_harness.py` (`--only-world`), `tools/test_architecture/rpg_gate_report.py` (`module_absent`), `tests/unit/tools/test_slow_regression_gate.py`, `docs/plans/test_architecture/roadmap.md`

## Completion Summary
(open: live evidence AC1-AC3 after the workflow is on main)
