---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261004-CODE-HEALTH-IMPACT-TESTS-LOCAL-ENV
phase: inprogress
date: 2026-10-04
tags: [testing, determinism]
---

# TCK-20261004-CODE-HEALTH-IMPACT-TESTS-LOCAL-ENV

## Title
Make tests/codebase/test_code_health_impact.py independent of the local graphify graph and of full git history

## Status
INPROGRESS

## Tier
hotfix

## Type
bug

## Priority
P3

## Request Summary
4 tests in `tests/codebase/test_code_health_impact.py` pass or skip in CI but fail locally under `.venv` python. That
cost perf-implementer an investigation on 2026-10-04 (PR #320), and it will mislead the done-gate's scoped test runs.
Reproduced by codebase-planner on `main` 474ebdcc (`.venv/bin/python3 -m pytest tests/codebase/test_code_health_impact.py`:
4 failed, 20 passed, 101 s):
- `test_real_path_pipeline_includes_kernel_as_dependent`
- `test_real_path_pipeline_kernel_visible_in_formatted_output_not_just_internal_data`
- `test_real_path_low_centrality_profile_generalizes` (`assert 'high' == 'low'`)
- `test_compute_churn_target_pathspec_defaults_to_repo_wide` (conftest `TimeoutError`: the 60 s "medium" budget)

Causes:
1. The three `real_path` tests are gated by `_requires_graphify`, which only checks that the `graphify` binary and
   `graphify-out/graph.json` exist. CI has neither, so they skip. Locally each worktree has its own gitignored graph in
   an unknown state (2026-10-04: main checkout 505 MB, rpg-perf 46 MB, both rewritten that day; the handover notes the
   main graph is stale because a full rebuild OOMs at the 2 GB cap). Dependents and centrality then vary per worktree.
2. The churn test runs `compute_churn_lines_changed(_REPO_ROOT)` twice over the real repository. CI checks out with
   shallow history, so it is fast there; on a full local clone it exceeds the 60 s budget.

## Scope
- Churn test: run it against a small temporary git repository built in the test (the file already has a `_git`
  helper and tmp-repo tests for the scoped case). Keep its assertion: default pathspec == explicit `"."`.
- `real_path` tests: choose one of these and record the choice. (a) Replace them with tests over a committed
  graph.json-shaped fixture (the file already has fixture data) that pins the same properties (kernel among
  pipeline.py's dependents and visible in the formatted output; low-centrality profile). (b) Keep them on the real
  graph, but mark them `local_graph` (a registered marker, deselected by default) so a scoped run never picks them
  up by accident. (a) is preferred if the fixture can express the regression the formatted-output test guards.
- Run the file under `.venv/bin/python3` in the main checkout and in a second worktree: same result in both, and no
  test above 60 s.

## Out of Scope
- `codebase/reports/code_health_impact.py` and `codebase_health_baseline.py` behaviour
- graphify itself, or making graphify a CI dependency
- The system-python failures of `tests/codebase` (missing complexipy, mypy_baseline, ast-grep, prek): expected,
  because tests/codebase runs under uv only

## Acceptance Criteria
- [ ] The 4 named tests no longer fail locally in either worktree, and no test or property is silently dropped
      (each property is still asserted somewhere that runs in CI, or the opt-in marker is documented in the file header)
- [ ] The churn test runs in under 5 s and its assertion is unchanged
- [ ] CI's tools/codebase job pass/skip totals compared with main's latest run; any difference is explained
- [ ] `git diff --stat <base>...HEAD` lists no path under src/

## Related Tickets
- TCK-20261004-PERF-VALIDATOR-COMPLEXITY-RATCHET (where the failures were reported)
- TCK-20260823-HOTFIX-CODE-HEALTH-IMPACT-APPLY-PY-STALE-DEPENDENT (earlier drift in the same real-graph tests)

## Related Docs
- docs/plans/codebase_health/python_code_craft_gates_flip_ticket_brief.md

## Related Stored Artifacts
None.

## Related Code Areas
- tests/codebase/test_code_health_impact.py
- tests/conftest.py (resource budget; read only)

## Assumptions / Open Questions
- Carried in the gates-flip batch (branch `python-code-craft-gates-flip`) as an extra hotfix ticket, filed in the
  planning commit. It touches only tests/codebase, the codebase domain's own tests.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
