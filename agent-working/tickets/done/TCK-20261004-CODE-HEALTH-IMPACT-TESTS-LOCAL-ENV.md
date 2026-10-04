---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261004-CODE-HEALTH-IMPACT-TESTS-LOCAL-ENV
phase: done
date: 2026-10-04
tags: [testing, determinism]
---

# TCK-20261004-CODE-HEALTH-IMPACT-TESTS-LOCAL-ENV

## Title
Make tests/codebase/test_code_health_impact.py independent of the local graphify graph and of full git history

## Status
DONE

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
- [x] The 4 named tests no longer fail locally in either worktree, and no test or property is silently dropped
      (each property is still asserted somewhere that runs in CI, or the opt-in marker is documented in the file header)
- [x] The churn test runs in under 5 s and its assertion is unchanged
- [ ] CI's tools/codebase job pass/skip totals compared with main's latest run; any difference is explained
- [x] `git diff --stat <base>...HEAD` lists no path under src/

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
Option (a), recorded. The three `real_path` tests became fixture tests (`test_fixture_pipeline_includes_kernel_as_dependent`, `test_fixture_pipeline_kernel_visible_in_formatted_output_not_just_internal_data`, `test_fixture_low_centrality_profile_generalizes`): a graph.json-shaped fixture plus a fake `affected_runner`, run against a tiny temporary git repo so churn is also deterministic. The formatted-output regression is expressible in a fixture: 120 dependents under `src/aaa_other/` sort before `src/engine/` alphabetically, so a plain sort pushes kernel.py to position 150 outside the 40-entry display window.
Mutation proof: changing the sort key in `sort_dependents_src_first` to `(0, path)` makes exactly `test_fixture_pipeline_kernel_visible_in_formatted_output...` fail (`assert 'src/engine/kernel.py' in ...`); reverted.
The churn test now builds a 2-commit temporary repo and asserts default == explicit `"."` (and == 11). `test_make_target_runs_successfully_against_real_repo` is unchanged (still `_requires_graphify`; passes in the main checkout, skips in worktrees without a graph).

## Test Summary
`.venv/bin/python3 -m pytest tests/codebase/test_code_health_impact.py`, own `--basetemp`, `systemd-run MemoryMax=2G`:
- Before, main checkout: 4 failed, 20 passed, 107 s (3 real-path, churn at the 60 s budget).
- Before, rpg-code-craft: 1 failed (churn, 60 s), 19 passed, 4 skipped (no local graph there).
- After, rpg-code-craft: 23 passed, 1 skipped, 0.5 s.
- After, main checkout (new file copied in temporarily, removed): 24 passed, 8.8 s; the slowest test is the make-target one (8.3 s); the churn test is 0.06 s.
CI pass/skip totals vs main's latest run: to be compared on the PR run (not pushed yet); expected difference: 3 fewer skips in tools-a-e, 3 more passes, since the fixture tests run in CI.

## Files Changed
- tests/codebase/test_code_health_impact.py
- agent-working/tickets/ (this ticket), agent-working/tickets/working_log.csv, agent-monitoring shard

## Completion Summary
Done: the 4 named tests no longer fail locally in either worktree and the file runs in 0.5 s there; every property is still asserted, now in CI too. Known gap: the CI totals comparison happens on the PR run. No src/ path touched.
