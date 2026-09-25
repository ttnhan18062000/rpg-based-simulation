---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260925-CI-API-TOOLS-LOGGING-PER-DIRECTORY-STEPS
phase: open
date: 2026-09-25
tags: [testing, workflows]
---

# TCK-20260925-CI-API-TOOLS-LOGGING-PER-DIRECTORY-STEPS

## Title

Split CI's `API / tools / logging` job into a step per test directory, so a blocked log doesn't hide
which directory failed

## Status

OPEN

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

_To be filled during implementation._

## Test Summary

_To be filled during implementation._

## Files Changed

_To be filled during implementation._

## Completion Summary

_To be filled during implementation._
