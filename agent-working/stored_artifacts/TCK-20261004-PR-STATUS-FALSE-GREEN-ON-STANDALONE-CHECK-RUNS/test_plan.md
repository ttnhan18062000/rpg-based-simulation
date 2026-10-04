---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261004-PR-STATUS-FALSE-GREEN-ON-STANDALONE-CHECK-RUNS
artifact_type: test_plan
tags: [ai, process-improvement]
---

# Test plan

`tests/tools/test_delivery_pr_status.py` (51 pass): the 32 existing tests unchanged in meaning (the fake runner gained default empty responses for the new calls), plus 19 new:

- AC1: 21-context fixture shaped like #291 -> FAILING naming ruff; positive control: the workflow-runs view alone reads GREEN.
- AC2: required context absent -> UNKNOWN; failure on page 2 of 2 is seen.
- AC3: check-runs fetch error, TLS error, non-JSON, wrong shape, status-endpoint error, short pagination -> UNKNOWN.
- AC4: pending standalone -> PENDING; skipped/neutral do not block GREEN.
- Extras: commit-status failure/pending; gh-only failure not lost; other-workflow check run does not vote even when gh lists it; cross-check unavailable is noted but does not block; failing workflow plus standalone failure keeps both.
- Read-only: no write flag on any `gh api` call (replaces the substring test for api calls only).
- Live (AC6): old vs new against #291's reported head, recorded in the ticket and `investigation.md`.
