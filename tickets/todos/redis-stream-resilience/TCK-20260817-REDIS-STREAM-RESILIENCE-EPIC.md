---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260817-REDIS-STREAM-RESILIENCE-EPIC
phase: open
date: 2026-08-17
tags: [observability]
---

# TCK-20260817-REDIS-STREAM-RESILIENCE-EPIC

## Title
Redis Stream consumer: differentiate failure handling, add DLQ + PEL reclaim + reconnect backoff

## Status
EPIC_SCOPED

## Tier
epic

## Type
repair

## Priority
P1

## Request Summary
`src/observability/stream/consumer.py:79-102` ACKs malformed payloads and transient handler
failures identically — no dead-letter stream, no retry budget. A message whose handler succeeds
but whose process dies before the ACK call sits orphaned in the consumer group's PEL forever, with
no `XCLAIM`/`XPENDING` reclaim logic. On a sustained Redis outage the reconnect loop retries
roughly every ~100ms with no backoff or jitter. Blast radius is bounded — this stream is
downstream of, not part of, the authoritative gameplay pipeline (Tier 3, observability/
anomaly-detection only) — but the data loss is real and currently invisible beyond a single
`logger.error` line.

## Scope
- Scope-only epic: full findings and proposed remediation steps are in
  `docs/plans/redis_stream_resilience_epic.md`. Detailed, investigated child tickets are not
  created yet.
- When work begins: run `create-tickets` against a proposal document scoped to this epic's items
  (failure-type differentiation + DLQ, PEL reclaim, reconnect backoff+jitter), producing
  investigated child tickets in `tickets/todos/redis-stream-resilience/`.

## Out of Scope
- Any change to the authoritative gameplay pipeline.
- Introducing a different message broker or a generic retry framework.

## Acceptance Criteria
- [ ] `docs/plans/redis_stream_resilience_epic.md` is reviewed and its scope confirmed accurate.
- [ ] Child tickets are created via `create-tickets` once this epic is chosen for action.
- [ ] This epic is not closed until its child tickets (once created) reach `tickets/done/`.

## Related Tickets
- TCK-20260817-CODEBASE-HEALTH-RESILIENCE-EPIC (parent tracking epic)

## Related Docs
- docs/plans/redis_stream_resilience_epic.md
- docs/plans/architecture_resilience_remediation_roadmap.md
- docs/audits/D23_architecture_resilience.md

## Related Stored Artifacts
None yet.

## Related Code Areas
- src/observability/stream/consumer.py
- src/observability/stream/adapters.py

## Assumptions / Open Questions
- Exact DLQ stream naming/retention convention is an open decision for whoever scopes the child
  ticket.

## Implementation Notes
(pending — scope-only epic)

## Test Summary
(pending — no direct tests; each future child ticket will carry its own)

## Files Changed
(pending)

## Completion Summary
(pending)
