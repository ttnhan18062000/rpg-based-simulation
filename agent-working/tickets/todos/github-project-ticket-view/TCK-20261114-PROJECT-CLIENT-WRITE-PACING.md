---
status: active
layer: ticket
authority: P1
audience: agent
ticket_id: TCK-20261114-PROJECT-CLIENT-WRITE-PACING
phase: open
date: 2026-11-14
tags: [planning, delivery]
---

# TCK-20261114-PROJECT-CLIENT-WRITE-PACING

## Title
`project_client.py` paces its writes and honours GitHub's rate-limit answers, so the P3 all-lanes first load can run (P3 prerequisite)

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P3

## Request Summary
This is a P3 prerequisite under TCK-20261112-EPIC-GITHUB-PROJECT-TICKET-VIEW, filed at the owner's direction on #715 6874493351 and
**not dispatched**. It's cut when P3 is approved.

The best-practice study (main-checkout `.claude/handover/drafts/github-project-best-practice-2026-11-14.md`, recommendation 7) found
two things:
- GitHub limits mutations through secondary rate limits, about 2,000 points per minute, with each mutation costing more than a query.
- A P3 first load over all lanes is about 2,200 mutations.

The P1b client (#909) sends every mutation back to back with no pacing, and stops at the first failure.

## Scope
1. Pace mutations at no more than about 1 per second (configurable in `registries/session_project.yaml`). Queries are not paced.
2. On a rate-limit answer (HTTP 403/429, a `retry-after` header, or a GraphQL `RATE_LIMITED` error), wait as told, using
   exponential backoff when no wait time is given, up to a bounded number of tries. Then stop the way P1b does, reporting what was
   done and what wasn't.
3. Print progress every N steps.
4. Running again after a stop reconciles, using the existing full-reconcile plan.
5. Tests with an injected clock and runner, no network, no real sleeps: pacing, `retry-after` honoured, backoff bounded, stop after
   the last try.

## Out of Scope
- Every other part of P3: all lanes, Domain as a single-select, and the timer.
- Parallel writes.

## Acceptance Criteria
1. Scope items 1-5 are built, and the scoped tests pass.
2. A live dry run and an `--apply` on Project 1 still behave as in P1b.
3. Staging artifacts exist, and agent-working-designer-u24 reviews plan.md.

## Related Tickets
- TCK-20261112-EPIC-GITHUB-PROJECT-TICKET-VIEW (parent)
- TCK-20261114-PROJECT-SYNC-INIT-AND-APPLY (P1b, #909)
- TCK-20261114-PROJECT-SYNC-LAYER-EPIC-PRIORITY-TAGS (P1c)

## Related Docs
- docs/guidelines/session_roles/project_sync_dry_run.md

## Related Stored Artifacts
- Study (main checkout): `.claude/handover/drafts/github-project-best-practice-2026-11-14.md`

## Related Code Areas
- tools/sessions/project_client.py, tests/tools/test_project_client.py, registries/session_project.yaml

## Assumptions / Open Questions
- **Simpler-fix check (6698958617).** The other option is to split the P3 first load across several runs by hand. That costs nothing
  in code but makes the operator wait between runs, and any timer run (P3) would hit the limit in the same way. Pacing costs about
  60 lines and 5 tests.
- The exact point costs are unconfirmed in the study. Measure the real cost on the first P3 load.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
