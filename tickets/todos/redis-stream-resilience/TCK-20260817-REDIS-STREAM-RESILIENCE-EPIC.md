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
OPEN

## Tier
standard

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
Full findings are in `docs/plans/redis_stream_resilience_epic.md`. Concrete scope, all in
`src/observability/stream/consumer.py`:
- Separate malformed-payload handling (ack+drop, already correct) from handler-exception handling
  (bounded retry, then a literal DLQ stream on exhaustion).
- Add `XCLAIM`/`XPENDING`-based PEL reclaim for a message orphaned by a process death between
  handler success and ACK.
- Add backoff+jitter to the ~100ms reconnect loop.

## Out of Scope
- Any change to the authoritative gameplay pipeline.
- Introducing a different message broker or a generic retry framework.

## Acceptance Criteria
- [ ] A transient handler failure results in a bounded retry, then a DLQ entry — not silent discard.
- [ ] A malformed payload still results in ack+drop (unchanged, already correct).
- [ ] A simulated process-death-before-ack scenario results in eventual redelivery via PEL
      reclaim, not permanent loss.
- [ ] The reconnect loop backs off with jitter under sustained Redis unavailability.

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
- Exact DLQ stream naming/retention convention is an open decision for Plan phase.
- **Downgraded from epic to standard tier (2026-08-18):** one of 10 sub-epics under
  `TCK-20260817-CODEBASE-HEALTH-RESILIENCE-EPIC`; all three scope items touch one file
  (`consumer.py`) under one coherent theme — a textbook standard ticket, not a multi-ticket
  initiative. `staging_artifacts/TCK-20260817-REDIS-STREAM-RESILIENCE-EPIC/` not yet created.

## Implementation Notes
(pending)

## Test Summary
(pending)

## Files Changed
(pending)

## Completion Summary
(pending)
