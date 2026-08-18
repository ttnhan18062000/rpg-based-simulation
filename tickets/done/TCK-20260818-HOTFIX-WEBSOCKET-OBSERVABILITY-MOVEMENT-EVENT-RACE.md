---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260818-HOTFIX-WEBSOCKET-OBSERVABILITY-MOVEMENT-EVENT-RACE
phase: done
date: 2026-08-18
tags: []
---

# TCK-20260818-HOTFIX-WEBSOCKET-OBSERVABILITY-MOVEMENT-EVENT-RACE

## Title
Fix race condition in observability websocket test's movement-event filter check

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
After closing TCK-20260818-HOTFIX-KGMCP-STALE-SCOPE-GUARD-TESTS, the real GitHub Actions "API /
tools / logging" job still failed (run 32129863384, commit e917b087) with a different, previously
unseen error. Since the sandbox's Fortinet DNS filter had blocked `gh api .../logs` all session,
retried the raw log fetch and this time it succeeded (`gh api
repos/.../actions/jobs/<id>/logs --include`), revealing the actual failure for the first time
instead of having to reproduce blind:
`AssertionError: assert 'movement' == 'walk'` in
`tests/api/test_observability_websocket.py::test_observability_websocket_suite`.

## Scope
`tests/api/test_observability_websocket.py` step 5 subscribes to a live websocket filtered on
`category=movement`, POSTs a synthetic event with `event_type="walk"`, then loops reading up to
10 messages and breaks on the *first* `type == "event"` message, asserting it has
`event_category == "movement"` AND `event_type == "walk"`. The server under test runs a live,
continuously-ticking simulation (per an existing comment a few lines above, added for the
heartbeat check) that legitimately emits its own real movement-category events concurrently —
any one of those can arrive in the queue before the synthetic "walk" event and has a different
`event_type` (real gameplay movement was categorized `event_type="movement"` in this instance,
not "walk"). The old loop treated arrival of *any* matching-category event as sufficient to
assert-and-break, so a background event with the right category but wrong type failed the
assertion instead of being skipped as noise.

Fixed by folding the `event_type == "walk"` check into the same condition that decides whether to
break the loop, so events that only partially match are skipped and the loop keeps waiting for
the actual synthetic event (up to the existing 10-attempt bound).

## Out of Scope
- No server/production code changes — this is a test-only race condition; the server's live event
  broadcast behavior driving the flake is intentional (documented by the adjacent heartbeat-wait
  comment) and correct.
- Did not touch any other assertions or steps (1-4, 6+) in the same test file — verified passing
  before and after.

## Acceptance Criteria
- [x] `tests/api/test_observability_websocket.py::test_observability_websocket_suite` passes
      reliably — verified 3 consecutive local runs, all passing, after the fix (not just once,
      given the failure was a live-timing race).
- [x] Full API job command
      (`pytest tests/api tests/cli tests/tools tests/logging tests/engine tests/observability -m
      "not slow and not extra_slow" --tb=short -q`) passes clean locally with `CI=true` and the
      venv on `PATH` (matching real CI's subprocess `python3` resolution) — 2428 passed, 11
      skipped, 32 deselected, 1 xfailed, zero failures.

## Related Tickets
- TCK-20260818-HOTFIX-KGMCP-STALE-SCOPE-GUARD-TESTS (prior hotfix in the same investigation
  chain — fixed a different failure in the same CI job; this ticket picks up where that one's
  push still showed red)

## Related Docs
None updated — no behavior/mechanics change, test-only fix.

## Related Stored Artifacts
None (hotfix tier, no staging artifacts required).

## Related Code Areas
- `tests/api/test_observability_websocket.py`

## Assumptions / Open Questions
None.

## Implementation Notes
Log-fetch breakthrough: `gh api repos/<owner>/<repo>/actions/jobs/<job_id>/logs --include` (raw
per-job logs, not `gh run view --log-failed`) succeeded this time where the same class of request
had failed all session due to a Fortinet DNS-filter block on the Azure Blob redirect target.
Worth retrying this exact call in future sessions before falling back to blind local
reproduction — it's strictly more informative when it works.

## Test Summary
Before fix: real CI failure (`assert 'movement' == 'walk'`), reproduced by reading the actual CI
log (not locally reproducible on demand since it's a live-timing race depending on the
background simulation's real event stream).
After fix: 3 consecutive local runs of the target test all pass; full API job command scoped
suite passes clean (2428 passed, 0 failed) in the main working directory with `CI=true` and venv
on `PATH`.

## Files Changed
- `tests/api/test_observability_websocket.py`

## Completion Summary
Fixed a real race condition in a websocket observability test: it asserted on the first
category-matching event instead of the first event matching both category and type, so a
concurrent, legitimate real-simulation movement event could preempt the test's own synthetic
event and fail the assertion. Root-caused via a successful raw CI log fetch (previously blocked
by the sandbox's network filter), fixed, and verified both for immediate correctness and repeated
stability before pushing.
