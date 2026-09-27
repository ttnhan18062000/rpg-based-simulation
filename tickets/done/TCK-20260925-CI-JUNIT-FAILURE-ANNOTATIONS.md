---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260925-CI-JUNIT-FAILURE-ANNOTATIONS
phase: done
date: 2026-09-25
tags: [testing, workflows]
---

# TCK-20260925-CI-JUNIT-FAILURE-ANNOTATIONS

## Title

Emit failed-testcase names as GitHub Actions annotations from `tools/ci_junit_summary.py`

## Status

DONE

## Tier

hotfix

## Type

chore

## Priority

P1

## Request Summary

PR #246's `API / tools / logging` job failure (2026-09-24/25) proved that this sandbox's raw-log
fetch and JUnit-XML artifact download are both TLS-blocked (`*.blob.core.windows.net`), leaving
only job/step-level `conclusion` metadata reachable — a directory name (`Run: tests/tools:
failure`), never a test name. The one channel confirmed to survive the block is
`gh api repos/{o}/{r}/check-runs/{job_id}/annotations` — it is how the generic "Process completed
with exit code 1" message was read at all. Anything emitted as a `::error::` workflow command
during the job becomes an annotation on that same channel.

`tools/ci_junit_summary.py` already parses every testcase in the JUnit XML into a
`TestCaseRecord` with a `status` field (`"passed" | "failed" | "error" | "skipped"`) via
`parse_testcase_records()`, run from an `if: always()` "Job summary" step in every fast-lane job
in `.github/workflows/test.yml`. It only ever aggregates those records into markdown counts for
`$GITHUB_STEP_SUMMARY` — it never emits per-testcase failure detail anywhere. This ticket adds
that emission, reusing the existing parser rather than adding a second one.

## Scope

1. Extract the `message` attribute off each testcase's `<failure>`/`<error>` child (confirmed via
   a real generated JUnit XML: pytest writes a concise one-line `message` attribute distinct from
   the full multi-line `text` body) into a new `message` field on `TestCaseRecord`.
2. Add a function rendering one `::error::` GitHub Actions workflow-command line per
   failed/error testcase, carrying the test ID and its message, with the documented `%`/CR/LF
   escaping applied in the correct order.
3. Wire this into `main()`, printed to **stderr**, not stdout — every call site in `test.yml`
   redirects this script's stdout into `$GITHUB_STEP_SUMMARY` (a plain file the runner does not
   scan for workflow commands), so a line destined to become a real annotation must reach the
   step's actual console output instead.
4. No `.github/workflows/test.yml` change: every "Job summary" step already has `if: always()`
   and already calls this script with the right JUnit XML path — the fix is entirely inside the
   Python module.

## Out of Scope

- Fixing the underlying `tests/tools` CI failure this was built to diagnose. That failure's real
  root cause is still unknown (no local reproduction under any isolation model tried); this
  ticket only makes the next occurrence — on this failure or any future one — immediately
  legible by test name instead of directory name.
- Touching the failing test's assertion or any gate logic to make CI green.
- `file`/`line` annotation properties: this project's JUnit XML (pytest's default `xunit2`
  writer, no `junit_family` override) does not emit `file`/`line` attributes on `<testcase>`, and
  reconstructing a file path from the dotted `classname` is unreliable for nested classes.
  `::error::` without `file`/`line` is valid GitHub Actions syntax; it still surfaces the
  annotation, just without a source-line deep link.
- Splitting `tests/tools` into finer per-file steps (the other option raised alongside this one)
  — superseded by this approach per agent-working-design's explicit call: this gets the test name
  in one round-trip instead of another narrowing step first.

## Acceptance Criteria

1. `TestCaseRecord` carries a `message` field populated from the JUnit XML's `<failure
   message="...">`/`<error message="...">` attribute; `""` for passed/skipped records.
2. A new function returns one `::error::<test_id> - <message>` line per failed/error record
   (using the two existing fixture fail/error shapes and a new fixture with `%`/newline
   characters in the message), with none emitted for passed/skipped records.
3. Escaping order is `%` → `%25` first, then CR → `%0D`, then LF → `%0A` — verified by a test
   asserting the escaped output, not just that escaping "happened".
4. `main()` emits these lines to `sys.stderr`, never `sys.stdout` — verified via `capsys`,
   asserting `::error::` appears in `captured.err` and not in `captured.out`.
5. `main()`'s existing "always returns 0, never raises" contract is unchanged.
6. All existing `tests/tools/test_ci_junit_summary.py` tests still pass unmodified except where
   `TestCaseRecord`'s new field required an update.
7. No `.github/workflows/test.yml` change — confirmed by `git diff` scoped to that file being
   empty for this ticket's commit.

## Related Tickets

- `TCK-20260925-CI-API-TOOLS-LOGGING-PER-DIRECTORY-STEPS` — the per-directory split that first
  surfaced `tests/tools` (not `tests/api`) as the real failing directory on PR #246; this ticket
  is the next diagnostic layer on top of it.
- `TCK-20260916-CI-PER-DIRECTORY-STEPS-FOR-BLOCKED-LOGS` — established the step-level-metadata
  survives-TLS-block pattern this ticket extends to the annotations channel.
- `TCK-20260823-CI-STEP-SUMMARY-REPORTING` — built `tools/ci_junit_summary.py` and its
  per-testcase parsing this ticket reuses.

## Related Docs

- `docs/guides/delivery_process.md` — "CI Failure Triage" (TLS-block diagnostic, step-conclusions
  channel, partial-log-fetch trap).

## Related Stored Artifacts

None — hotfix tier, no staging artifacts.

## Related Code Areas

- `tools/ci_junit_summary.py`
- `tests/tools/test_ci_junit_summary.py`
- `tests/tools/fixtures/ci_junit_summary/`

## Assumptions / Open Questions

1. Assumed GitHub Actions scans a step's combined stdout+stderr console output for workflow
   commands, not only stdout — this is the load-bearing assumption for stderr-vs-stdout routing.
   Not independently verifiable from this sandbox (no way to trigger a real annotation and read
   it back before landing); the real CI run on the next push is the actual verification. If wrong,
   the fallback is a small workflow-level change (e.g. `2>&1 | tee` splitting the streams, or a
   separate un-redirected step) — out of scope here unless the first attempt proves it necessary.
2. Whether the true `tests/tools` CI failure is a loaded-runner concurrency issue in
   `writer.py`'s lock-retry protocol is an **unverified hypothesis**, not a finding — recorded
   here for traceability only, not as scope for this ticket.

## Implementation Notes

Generated a real JUnit XML locally (via a deliberately failing/erroring throwaway test file, not
just the existing fixtures) to confirm the exact `<failure>`/`<error>` element shape before
writing any code: pytest's `xunit2` writer puts a concise one-line summary in the `message`
attribute (e.g. `"AssertionError: deliberate failure for shape inspection\nassert 1 == 2"` — note
this can itself contain embedded newlines) and the full traceback in the element's `text` body.
Used `message` for the annotation, not `text` — a full traceback is too long for a single
annotation line and duplicates what the (blocked) raw log would have shown anyway; the goal is a
test *name*, which `message` combined with `test_id` already gives fully.

Confirmed no `file`/`line` attributes exist on `<testcase>` in this project's real output (checked
both a passing and a failing locally-generated sample) — ruled out attempting a `file=`/`line=`
annotation property per the Out of Scope note above, rather than shipping an attempt that would
silently be wrong for nested-class test IDs.

Confirmed via `grep` (after `search_docs`/`graphify query` per Context Scan) that every
`ci_junit_summary.py` call site in `.github/workflows/test.yml` redirects only stdout
(`>> "$GITHUB_STEP_SUMMARY"`), leaving stderr attached to the step's real console output — this
is what makes the stderr-routing fix work without any workflow-file change, and why AC7 (no
`test.yml` diff) is achievable at all.

## Test Summary

- `python3 -m pytest tests/tools/test_ci_junit_summary.py -v` — **34 passed** (26 pre-existing +
  8 new), covering: message extraction from `<failure>`/`<error>` (AC1), one-annotation-per-
  failed/error record with none for passed/skipped (AC2), the exact `%` → CR → LF escaping order
  including an end-to-end fixture with a real `%` and embedded newline (AC3), `main()` emitting
  annotations to `stderr` and never `stdout` via `capsys` (AC4), and the pre-existing
  "always exits 0" test unmodified and still passing (AC5).
- `python3 -m pytest tests/tools/test_ci_workflow_test_coverage.py
  tests/static/test_ci_step_summary_reporting.py -q` — 44 passed (workflow-parsing gate and
  step-summary static checks unaffected — expected, since this ticket makes no `test.yml` change).
- Full regression: `python3 -m pytest tests/tools/ tests/static/ -m "not slow and not extra_slow"
  -q` — **3075 passed** (3067 baseline + 8 new), 25 skipped, 28 deselected, 1 xfailed, 0 failed.
- `git diff --stat -- .github/workflows/test.yml` — empty (AC7).
- Not verifiable locally: whether GitHub Actions actually reads a `::error::` line from a step's
  stderr as a real annotation (Assumption 1) — no local Actions runner available. Confirmed on the
  next real CI run instead, same as the per-directory split before it.
- While this ticket was in flight, re-ran the exact failing job from PR #246's original run
  (`gh run rerun 36089375587 --failed`) as a genuinely separate, unrelated data point (design's
  "option 2", pursued in parallel per their explicit request, not as verification of this
  ticket's own change): attempt 2 (job id 107937150826) failed again, in the same directory
  (`Run: tests/tools: failure`), with every other directory passing — identical shape to attempt
  1. Two-for-two on CI with zero local reproduction under any isolation model tried argues against
  simple runner-load flakiness and for a real, CI-environment-specific defect; recorded here for
  traceability, not as evidence this ticket's own change caused or fixed anything.

## Files Changed

- `tools/ci_junit_summary.py` — `TestCaseRecord.message` field, `_testcase_message()`,
  `format_failure_annotations()`, `_escape_annotation_message()`, wired into `main()` via
  `print(..., file=sys.stderr)`.
- `tests/tools/test_ci_junit_summary.py` — new tests for message extraction, annotation
  formatting, escaping, and stderr-vs-stdout routing.
- `tests/tools/fixtures/ci_junit_summary/has_failure_with_special_chars.xml` — new fixture with
  `%` and embedded newline in the failure message, for the escaping test.
- `docs/REGISTRY.yaml` — regenerated as part of ticket close (routine, unconditional per the
  Finalize rule), picking up this ticket's own `tickets/done/` entry.

## Completion Summary

Added per-testcase GitHub Actions `::error::` annotation emission to `tools/ci_junit_summary.py`,
reusing its existing `parse_testcase_records()` parser rather than writing a second one. Confirmed
the exact `<failure>`/`<error>` element shape (concise `message` attribute vs. a full multi-line
`text` body) against a real, locally-generated JUnit XML before writing any code, rather than
assuming the shape from the existing fixtures alone. Routed the new annotation lines to `stderr`
specifically because every call site of this script in `.github/workflows/test.yml` redirects its
stdout into `$GITHUB_STEP_SUMMARY` (a plain file the runner does not scan for workflow commands) —
confirmed via `grep` after the mandatory `search_docs`/`graphify query` context scan, not assumed —
which is also why this ticket needed zero `.github/workflows/test.yml` changes (AC7): every
"Job summary" step already has `if: always()` and already points at the right JUnit XML path.

No `file`/`line` annotation properties: confirmed via a real generated sample that this project's
pytest JUnit output carries neither attribute on `<testcase>`, and reconstructing a file path from
the dotted `classname` would be unreliable for nested classes — documented as an explicit
Out-of-Scope decision rather than a silent omission.

While this ticket was in progress, also re-ran (per agent-working-design's explicit "option 2, in
parallel" request) the same CI job that originally exposed the `tests/tools` failure. It failed
again, in the same directory, on the second independent attempt — this is unrelated to whether
this ticket's own change works, but is separately reported to design as it bears on whether the
underlying failure is flaky or deterministic.

One known, explicitly-flagged gap: whether GitHub Actions actually reads a workflow command off a
step's stderr (as opposed to only stdout) is an assumption (Assumption 1), not something
verifiable from this sandbox — no local Actions runner exists to confirm it before landing. The
real CI run on the next push is the actual test of that assumption, exactly as it was for the
prior per-directory-split ticket's own workflow-only changes. If it proves wrong, the fix is a
small, separate follow-up (splitting stdout/stderr differently at the workflow-step level), not a
reason to withhold this change — the markdown summary output is unaffected either way.

No known material gap otherwise. Did not touch the actual failing test or `.github/workflows/test.yml`.
