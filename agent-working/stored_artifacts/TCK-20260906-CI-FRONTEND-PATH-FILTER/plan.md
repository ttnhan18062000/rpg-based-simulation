---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260906-CI-FRONTEND-PATH-FILTER
artifact_type: plan
tags: [testing]
---

# Plan — TCK-20260906-CI-FRONTEND-PATH-FILTER

## Steps

1. **`.github/workflows/test.yml` — gate job.** Add `FRONTEND_RE='^(frontend/|\.github/workflows/test\.yml$)'`
   and a `run_frontend` output, following the exact existing `PERF_RE`/`MIG_RE` pattern:
   - Non-`pull_request` event branch: add `echo "run_frontend=true" >> "$GITHUB_OUTPUT"` alongside
     the 2 existing lines.
   - Failed-diff branch: same addition.
   - Real-diff branch: add `echo "run_frontend=$(echo "$CHANGED" | grep -qE "$FRONTEND_RE" && echo true || echo false)" >> "$GITHUB_OUTPUT"`.
   - Add `run_frontend: ${{ steps.diff.outputs.run_frontend }}` to the gate job's `outputs:` map.

2. **`.github/workflows/test.yml` — `frontend` job.** Add `needs: [changed-files]` and
   `if: ${{ !cancelled() && (needs.changed-files.result != 'success' || needs.changed-files.outputs.run_frontend == 'true') }}`,
   byte-identical in shape to `perf-cert-arena`'s/`migration-lanes`' own `if:` (only the output
   name differs).

3. **`tests/static/test_ci_narrow_path_filtered_jobs.py`.** Generalize the existing per-job
   test pairs to also cover `frontend`, without touching `_OUT_OF_SCOPE_JOBS` (frontend was never
   in it) or `_EXPECTED_SLOW_NEEDS`/`_EXPECTED_SLOW_IF` (unaffected — `frontend` is already in
   `slow`'s `needs:` list and stays there unmodified):
   - Test 1 (`..._have_if_conditions`): add a `frontend` assertion.
   - Tests 5a/5b (`..._if_references_changed_files_gate_output`): add a `frontend` case checking
     for `run_frontend` in its condition.
   - Test 6/7 (fail-open branches): extend the branch-text assertions to also expect
     `run_frontend=true` in both the non-PR and diff-failure branches.
   - Test 10 (`test_gated_jobs_fail_open_on_gate_job_non_success`): add `("frontend", "run_frontend")`
     to its existing 2-tuple loop.
   - New test mirroring 8/9's spirit but simpler (no marker-tagged-test derivation needed, since
     `frontend`'s dependency set is just `frontend/` itself, not derived from imports): assert
     `FRONTEND_RE` contains the literal substring `frontend/`.
   - Update the module docstring's `TCK-20260819` reference to also cite this ticket.

4. **`docs/testing/migration_ci_lanes.md`.** Extend the "Path-Based Skip Condition (CI)" section
   with a third bullet describing the `frontend` gate, citing this ticket.

5. **Verification.** Run the extended static guard file; confirm all pass. Run a scoped
   `git diff --name-only` simulation locally (or via a real PR touching only a `docs/` file, once
   pushed) to observe a real live-CI skip. Confirm no other job's `if:`/`needs:` changed via
   `git diff --stat -- .github/workflows/test.yml`.

## Rejected alternative

Using `dorny/paths-filter` (a third-party GitHub Action) instead of extending the existing
hand-rolled gate — rejected: the parent ticket already made and documented this choice
(hand-rolled `git diff` + regex, no new third-party action dependency), and this ticket only
extends an existing mechanism, it does not re-litigate that choice.

## Acceptance-criteria map

| AC | Verified by |
|---|---|
| `frontend` skips on unrelated changes | `test_perf_cert_arena_and_migration_lanes_have_if_conditions`-equivalent (extended) + live-CI observation via this ticket's own PR |
| `frontend` still runs on `frontend/`/workflow changes | Same PR's own CI run, since this PR itself touches both `.github/workflows/test.yml` and `tests/static/` — `frontend` must run in full on it |
| No other job's trigger behavior changed | `test_no_other_fast_lane_job_gained_an_if_condition`, `test_slow_job_if_condition_is_unchanged` (unmodified, must still pass) |
| Fails safe on ambiguity/error | Extended tests 6/7/10 |
