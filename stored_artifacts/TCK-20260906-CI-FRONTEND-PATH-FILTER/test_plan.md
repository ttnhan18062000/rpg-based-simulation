---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260906-CI-FRONTEND-PATH-FILTER
artifact_type: test_plan
tags: [testing]
---

# Test Plan — TCK-20260906-CI-FRONTEND-PATH-FILTER

## Normal flow
- `frontend` job carries a truthy `if:` condition referencing `run_frontend`.
- `run_frontend` regex includes `frontend/` and `.github/workflows/test.yml`.
- Gate job's `outputs:` map includes `run_frontend`.

## Edge cases
- Non-`pull_request` event (push to main, schedule, workflow_dispatch): `run_frontend` forced
  `true` before any diff attempt.
- `git diff` command itself fails: `run_frontend` forced `true`, gate job still exits 0.
- Gate job errors/cancels entirely (not just a clean `false` result): `frontend`'s `if:` still
  evaluates true via the `needs.changed-files.result != 'success'` OR-clause + `!cancelled()`.

## Failure modes
- None of the 9 explicitly out-of-scope jobs (`_OUT_OF_SCOPE_JOBS`) gain an `if:` condition.
- `slow` job's `if:`/`needs:` stay byte-identical (frontend already listed in `needs:`, unchanged).
- `perf-cert-arena`/`migration-lanes`'s own `if:` conditions and `PERF_RE`/`MIG_RE` patterns are
  untouched.

## Regression-prone paths
- Test 8/9's live-derived import-coverage checks (`test_perf_cert_arena_path_set_covers_all_...`,
  `test_migration_lanes_path_set_covers_all_...`) must still pass unmodified — this ticket doesn't
  touch `PERF_RE`/`MIG_RE`.
- The new `frontend`-coverage test must not be derived from a live import-scan (unlike 8/9) since
  `frontend/`'s own dependency set is definitionally itself, not something to re-derive from
  imports — a literal substring check on `FRONTEND_RE` is correct here, not a false weakening of
  rigor relative to 8/9's approach (their derivation exists specifically because Python's import
  graph is not self-evident from directory structure; `frontend/`'s is).

## Commands
- `pytest tests/static/test_ci_narrow_path_filtered_jobs.py -v`
- `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/test.yml'))"` (parses cleanly)
- `git diff --stat -- .github/workflows/test.yml` (confirm only additive `frontend`-related lines,
  no changes to `perf-cert-arena`/`migration-lanes`/`slow`/the 9 out-of-scope jobs)

## Manual / CI-Observed Verification (not executable from pytest)
- This PR itself touches `.github/workflows/test.yml`, so `frontend` must run in full on its own
  CI run (real positive-trigger observation).
- A real "skip" observation (a PR touching only an unrelated file, e.g. a docs-only change)
  requires a separate follow-up PR — left as a follow-up observation, matching the parent
  ticket's own precedent of leaving live-CI-observed skip confirmation pending beyond static
  verification.
