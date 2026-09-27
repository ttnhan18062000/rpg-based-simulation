---
status: active
layer: ai
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20260924-DELIVERY-CI-TRIAGE-CLASSIFIER
date: 2026-09-24
tags: [delivery, ai, process-improvement]
---

# Test Plan — TCK-20260924-DELIVERY-CI-TRIAGE-CLASSIFIER

`tests/tools/test_delivery_ci_triage_classifier.py`, one test per Acceptance Criterion (AC1–AC9) as
detailed in plan.md's Tests section, using `tmp_path`-based fixture `regression_policy.md`/
`test.yml` files and a `FakeRunner` for `git diff`.

## Regression-prone paths
- `test_unknown_with_tls_reason_is_environment`: `UNKNOWN` verdict with a TLS-keyword reason ->
  category 4.
- `test_unknown_without_tls_reason_is_unclassified`: `UNKNOWN` verdict, generic reason ->
  `UNCLASSIFIED`, never forced into category 4.
- `test_parked_slow_regression_job_flagged_not_new`: a failing job named the known parked job name
  carries a `parked: true`/not-new-finding note regardless of its underlying category.
- `test_no_write_side_effect`: mirrors the other delivery-tool tests.

## Full regression check
`pytest tests/tools/ -m "not slow"` after the new file passes in isolation.

## Recorded in `## Test Summary` once run
Exact commands and pass/fail counts.
