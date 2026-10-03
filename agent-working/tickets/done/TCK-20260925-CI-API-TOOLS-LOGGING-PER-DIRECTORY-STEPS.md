---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260925-CI-API-TOOLS-LOGGING-PER-DIRECTORY-STEPS
phase: done
date: 2026-09-25
tags: [testing, workflows]
---

# TCK-20260925-CI-API-TOOLS-LOGGING-PER-DIRECTORY-STEPS

## Title

Split CI's `API / tools / logging` job into a step per test directory, so a blocked log doesn't hide
which directory failed

## Status

DONE

## Tier

hotfix

## Type

chore

## Priority

P1

## Request Summary

`TCK-20260916-CI-PER-DIRECTORY-STEPS-FOR-BLOCKED-LOGS` established that a CI job running many test
paths in one combined step is far harder to diagnose when raw log fetching is TLS-blocked, and split
`unit-infra` into a step per directory with `if: always()`. **`API / tools / logging` never received
the same treatment.** It still runs six directories in one step, literally named `Run`:

```yaml
- name: Run
  run: |
    pytest tests/api tests/cli tests/tools tests/logging tests/engine tests/observability \
           -m "not slow and not extra_slow" --tb=short -q --junit-xml=reports/junit/api-tools.xml
```

This is no longer hypothetical. On PR #246 (2026-09-24/25) this job failed twice, deterministically,
and diagnosis was blocked at every turn:

- Raw log fetch failed with the documented TLS interception on
  `productionresultssa16.blob.core.windows.net` (`certificate is not valid for any names`).
- `check-runs/{id}/annotations` returned only `Process completed with exit code 1`.
- **No artifacts were uploaded**, so the `--junit-xml` the step already produces was unreachable too.
- Step-level conclusions — the one channel that survives the TLS block — showed only
  `Run: failure`, naming six directories at once.

The result: a local repro of the entire six-directory command was the *only* available signal, it
costs ~7 minutes per attempt, and bisection still did not isolate the trigger. A per-directory split
would have named the failing directory immediately, from metadata alone, at zero log access.

## Scope

1. Split the `Run` step into one step per test directory (`tests/api`, `tests/cli`, `tests/tools`,
   `tests/logging`, `tests/engine`, `tests/observability`), each named for its directory, each with
   `if: always()` so a failure in one does not mask the others — the exact shape
   `TCK-20260916-CI-PER-DIRECTORY-STEPS-FOR-BLOCKED-LOGS` applied to `unit-infra`.
2. Keep `--junit-xml` output per directory, and **upload it as an artifact** with
   `if: always()`. The XML is already generated and currently thrown away; uploading it gives a
   second log-independent diagnosis channel that the TLS block does not touch.
3. Preserve the job's overall pass/fail semantics: if any directory fails, the job fails.

## Out of Scope

- **Changing which tests run, their markers, or their order.** Ordering is load-bearing for the
  failure under investigation in `TCK-20260925-LIVE-HEALTH-NAVIGATION-STUCK-COUNT-CI-REGRESSION`;
  a split must not change it. Steps run sequentially in the listed order, matching today's single
  `pytest` invocation order — confirm that holds rather than assuming it.
- **Fixing the underlying test failure.** That is the sibling ticket's job. This ticket makes the
  failure legible; it does not resolve it.
- Other jobs in `test.yml`. `unit-infra` is already done; the rest are out of scope here.
- Any change to the TLS/network block itself, which is not fixable from this repo.

## Acceptance Criteria

1. `API / tools / logging` runs one named step per test directory, each with `if: always()`.
2. A failure in one directory still lets the remaining directories run and report.
3. The job's own conclusion is `failure` if any directory failed.
4. Per-directory junit XML is uploaded as an artifact with `if: always()`.
5. The set of tests executed and their order are unchanged from the current single invocation —
   verified, not assumed.
6. `tools/gate_checks/ci_workflow_test_coverage.py` (which reasons about this workflow's test paths)
   still passes, and is checked *before* claiming completion — it parses the workflow's pytest
   invocations and a restructure is exactly what could break it.

## Related Tickets

- `TCK-20260916-CI-PER-DIRECTORY-STEPS-FOR-BLOCKED-LOGS` — did this for `unit-infra`; this is the
  same fix for the job it missed.
- `TCK-20260925-LIVE-HEALTH-NAVIGATION-STUCK-COUNT-CI-REGRESSION` — the failure that exposed this.
- `TCK-20260924-DELIVERY-CI-TRIAGE-CLASSIFIER` — consumes step conclusions; a per-directory split
  makes its output materially more specific.

## Related Docs

- `docs/guides/delivery_process.md` — "CI Failure Triage", including the TLS-block diagnostic and
  the step-conclusions channel.

## Related Stored Artifacts

- `stored_artifacts/TCK-20260916-CI-PER-DIRECTORY-STEPS-FOR-BLOCKED-LOGS/` — the reference
  implementation for `unit-infra`.

## Related Code Areas

- `.github/workflows/test.yml` — the `API / tools / logging` job (~lines 329–360)
- `tools/gate_checks/ci_workflow_test_coverage.py`

## Assumptions / Open Questions

1. Whether to use `actions/upload-artifact` per directory or one upload of the whole
   `reports/junit/` directory at the end with `if: always()`. The latter is one step and likely
   simpler; confirm it still captures XML from a directory whose step failed.
2. Whether `ci_workflow_test_coverage.py` parses a single combined `pytest` invocation in a way that
   a multi-step split breaks. Check this **first** — it is the most likely source of an unexpected
   failure in this ticket, and finding it after the workflow edit costs a CI round-trip.

## Implementation Notes
Checked `tools/gate_checks/ci_workflow_test_coverage.py` first, per Assumption 2's explicit
instruction. `parse_job_pytest_paths` scans an entire job's body text for every line starting with
`pytest` (handling backslash-continuation), keyed only by the top-level job name — not by which
step a `pytest` invocation lives in. A per-directory split therefore produces the same set of
`tests/...` path tokens the check already expects, just spread across six separate `pytest`
statements instead of one; confirmed by running the check's own 32-test suite both before and
after the edit (identical: 32 passed both times), not just by reading the parser.

Reused `tools/ci_junit_merge.py` (already generic — takes shard paths as CLI args, `unit-infra`'s
own defaults are just its fallback) rather than writing a second merge implementation, mirroring
`unit-infra`'s exact reference shape from `TCK-20260916-CI-PER-DIRECTORY-STEPS-FOR-BLOCKED-LOGS`.
The merged output still lands at `reports/junit/api-tools.xml` — the same path the existing "Job
summary" step already reads — so no downstream step changes.

The artifact upload (Scope item 2, genuinely new — `unit-infra`'s own reference implementation
never added one) follows the one existing precedent in this workflow, the certification job's
"Upload certification report" step: `actions/upload-artifact@v4`, `if: always()`, a `${{
github.sha }}`-suffixed name, `retention-days: 30`. Uploads the whole `reports/junit/api-tools*.xml`
glob (all six per-directory shards plus the merged file) in one step rather than one upload per
directory (Assumption 1) — simpler, and `if: always()` on both the per-directory `Run` steps and
this upload step means a shard from a failed directory is captured too, not just a passing one.

The "Fetch base branch"/"Base branch test collection" steps (a separate mechanism computing a
new/existing test-count diff for the PR summary, not part of the actual test execution) were left
as a single combined `--collect-only` invocation — out of this ticket's scope, which named "the
`Run` step" specifically.

AC5 ("verified, not assumed") was checked directly: `pytest --collect-only -q` for the combined
six-directory invocation vs. the six separate per-directory invocations produced the **exact same
3247 test IDs in the exact same order** (`diff` against the two raw collection outputs: zero
lines of difference).

## Test Summary
- `python3 -m pytest tests/tools/test_ci_workflow_test_coverage.py -q` — **32 passed**, run before
  and after the workflow edit (AC6): identical result both times.
- `python3 -m pytest tests/tools/test_ci_junit_merge.py -q` — 6 passed (module reused unchanged).
- AC5 verification: `pytest tests/api tests/cli tests/tools tests/logging tests/engine
  tests/observability -m "not slow and not extra_slow" --collect-only -q` vs. the same six
  directories run individually and concatenated — **3247 test IDs in both, zero-line `diff`**.
- Every test file referencing `api-tools`/`api_tools` (`tests/tools/test_ci_workflow_test_coverage.py`,
  `tests/tools/test_parity_index.py`, `tests/static/test_ci_narrow_path_filtered_jobs.py`,
  `tests/static/test_ci_step_summary_reporting.py`) run together: **67 passed**.
- Full regression: `python3 -m pytest tests/tools/ tests/static/ -m "not slow"` — **3067 passed,
  25 skipped, 28 deselected, 1 xfailed**, 0 failed.
- `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/test.yml'))"` — valid YAML.
- Not run: the actual GitHub Actions workflow itself (no local Actions runner available). This
  ticket's own scope is diagnosability, not the underlying test failure — the real CI run on the
  next push is the genuine verification of the split itself; local checks here verify the parts
  that can be verified locally (coverage-check parseability, YAML validity, identical test set).

## Files Changed
- `.github/workflows/test.yml` — `api-tools` job's single `Run` step replaced by six per-directory
  steps (`tests/api`, `tests/cli`, `tests/tools`, `tests/logging`, `tests/engine`,
  `tests/observability`), each `if: always()`; new "Merge JUnit XML" step (reusing
  `tools/ci_junit_merge.py`); new "Upload JUnit XML" step (`actions/upload-artifact@v4`).

## Completion Summary
Split the `API / tools / logging` CI job's single combined `Run` step into one step per test
directory, the same treatment `TCK-20260916-CI-PER-DIRECTORY-STEPS-FOR-BLOCKED-LOGS` already gave
`unit-infra` — this job never received it, and PR #246's deterministic, twice-reproduced failure
with every log/annotation channel blocked (TLS-blocked raw logs, no artifacts, step conclusions
naming all six directories at once) made the gap concrete rather than hypothetical. Reused
`tools/ci_junit_merge.py` unchanged rather than writing a second merge implementation, and added
the JUnit-XML artifact upload this job never had (a genuinely new capability, not copied from the
`unit-infra` reference, since that job never added one either) — a second, log-independent
diagnosis channel, following the one existing upload-artifact precedent in this workflow.

Checked `tools/gate_checks/ci_workflow_test_coverage.py` before editing the workflow, per the
ticket's own explicit warning, and verified its 32-test suite unchanged before and after — the
parser scans a whole job body for `pytest` statements regardless of which step they're in, so a
per-directory split was never at risk of breaking it, confirmed rather than assumed. AC5 (test set
and order unchanged) was verified directly via a zero-diff comparison of `--collect-only` output
between the old combined invocation and the new six separate ones (3247 identical test IDs, same
order), not inferred from the edit looking mechanically equivalent.

No known material gap. The actual fix for the failure this split was built to diagnose is a
separate ticket (`TCK-20260925-LIVE-HEALTH-NAVIGATION-STUCK-COUNT-CI-REGRESSION`, scoped
separately per design's instruction) — this ticket's own job is done once the split lands and is
verifiable in a real CI run.
