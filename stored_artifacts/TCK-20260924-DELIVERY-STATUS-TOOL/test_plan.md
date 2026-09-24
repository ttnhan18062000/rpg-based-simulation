---
status: active
layer: ai
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20260924-DELIVERY-STATUS-TOOL
date: 2026-09-24
tags: [delivery, ai]
---

# Test Plan — TCK-20260924-DELIVERY-STATUS-TOOL

## Location
`tests/tools/test_delivery_pr_status.py` (new file — `tests/tools/` is where the closest existing
shapes, `test_done_checker_static.py`-style tests, already live).

## Fixture strategy
A `FakeRunner` class recording every `cmd: list[str]` it was called with (for the "no log-fetch"
and "no mutating command" assertions) and returning a canned `(returncode, stdout, stderr)` keyed
by matching against the command's leading tokens (`gh pr view`, `gh api .../actions/runs`, `gh api
.../actions/runs/{id}/jobs`, `gh api .../actions/jobs/{id}`, `git ls-remote`). No real subprocess,
no real network — fully deterministic and instant, satisfying the Testing Rule's determinism
requirement and Assumption 4 (no live smoke test).

## Cases (one section per Acceptance Criterion; failure modes and edge cases folded in)

### Normal flow
- `test_green_when_all_applicable_runs_succeed_against_current_head` (AC1)
- `test_pending_when_applicable_run_in_progress` (design decision 5's PENDING branch, not itself an
  AC but load-bearing for AC2's parenthetical)
- `test_json_output_contains_verdict_head_sha_reason` (AC6)
- `test_json_output_and_human_output_agree_on_verdict` (regression guard: the two output modes must
  never disagree, since they're computed from one shared function)

### Edge cases
- `test_stale_sha_run_present_yields_unknown_not_green` (AC2, primary shape)
- `test_stale_sha_plus_current_sha_in_progress_yields_pending` (AC2, parenthetical shape)
- `test_absent_conflicting_pull_request_only_trigger` (AC3)
- `test_absent_push_not_landed_disambiguator` (design decision 7a — ls-remote mismatch)
- `test_absent_no_known_cause_still_reports_absent_not_unknown` (design decision 7c fallback)
- `test_workflow_covers_branch_via_push_true_when_no_push_key`
- `test_workflow_covers_branch_via_push_true_when_push_has_no_branches_filter`
- `test_workflow_covers_branch_via_push_false_when_branch_not_listed`

### Failure modes (the incidents this ticket exists to encode — highest priority tests)
- `test_unknown_when_runs_fetch_returns_nonzero_exit` (AC4, primary — the exact TLS-block shape)
- `test_unknown_when_runs_fetch_returns_unparseable_stdout` (AC4, second variant — exit 0 but not
  JSON, the "looked fine but wasn't" shape that is arguably more dangerous than a loud failure)
- `test_unknown_when_pr_view_fetch_fails`
- `test_unknown_when_ls_remote_fails_during_absent_disambiguation` (design decision 7a's own
  failure-of-the-failure-check path — must not silently fall through to 7b/7c)
- `test_ls_remote_disambiguator_never_called_when_runs_exist` (a passing/failing/pending run should
  short-circuit before ever reaching the ABSENT-only disambiguation branch)

### Regression-prone paths
- `test_failing_verdict_never_fetches_a_log_endpoint` (AC5 — asserts the `FakeRunner`'s call log
  contains no `/logs` substring in any recorded command, across the whole run)
- `test_failing_verdict_includes_step_name_and_conclusion_per_failing_job` (AC5)
- `test_no_git_or_gh_mutating_command_ever_issued` (AC7's unit half — scans `FakeRunner`'s call log
  for `git commit`, `git push`, `gh pr create`, `gh pr merge`, `gh run rerun`, `gh run watch`; none
  may appear)
- `test_working_tree_and_index_unchanged_after_run` (AC7's integration half — real subprocess against
  a disposable fixture repo/branch state, or against this repo's own worktree with a `git status
  --short` snapshot diff before/after a real (fixture-backed, no live network) invocation)
- `test_exit_code_zero_for_every_verdict` (AC8 — parametrized over GREEN/PENDING/FAILING/ABSENT/
  UNKNOWN fixtures)
- `test_exit_code_nonzero_only_on_internal_error` (AC8 — a `FakeRunner` returning a malformed
  shape that the module cannot handle, e.g. missing expected key, asserting this is the *only*
  path that exits non-zero)
- `test_no_sleep_or_retry_loop_present` (static source-scan test: `pr_status.py` contains no
  `time.sleep`, `while True`, or retry-decorator import — guards the Out-of-Scope "no polling loop"
  requirement structurally, not just by convention)

## Full-suite regression check
After the new test file passes in isolation, run the surrounding directory
(`pytest tests/tools/ -k "not slow"` or the narrower set covering `tools/gate_checks/` and any
existing `tools/delivery`-adjacent tests, whichever the actual directory size warrants at
implementation time) to confirm no existing test imports or execution-order assumption breaks from
adding `tools/delivery/__init__.py`.

## Recorded in ticket's `## Test Summary` once run
- Exact `pytest` command(s) invoked.
- Pass/fail count.
- Any skipped/xfailed test, with reason.
