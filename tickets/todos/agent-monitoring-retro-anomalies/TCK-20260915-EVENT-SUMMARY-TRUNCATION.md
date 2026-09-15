---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260915-EVENT-SUMMARY-TRUNCATION
phase: open
date: 2026-09-15
tags: [agent-monitoring, data-quality]
---

# TCK-20260915-EVENT-SUMMARY-TRUNCATION

## Title
47 event summaries land on exactly 200 characters — a hard truncation boundary that silently discards the rest, reported by no mechanism

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P3

## Request Summary
Summary length across the 1,897 events in the 2026-09-01 → 2026-09-15 window:

| Statistic | Value |
|---|---|
| min | 8 |
| p25 | 70 |
| median | 95 |
| p90 | 184 |
| max | 1,055 |
| **exactly 200 chars** | **47** |

A clean spike at exactly 200 in an otherwise smooth distribution is a truncation boundary, not
natural length. `generate_retro.py`'s Summary Quality section already counts these — it reports
"Truncated (>200 chars): 98" — but only as a statistic. Nothing warns at write time, and the
discarded text is gone.

The summaries are the only human-readable record of what a phase actually did; they are what this
very review read to classify Review-phase failures. A summary cut mid-sentence at 200 characters is
a degraded audit trail.

Note the max of 1,055 shows longer summaries *can* be stored — so the 200 boundary is imposed by a
specific writer, not by the schema.

**The short tail is mostly fine and should not be "fixed"**: `'489 passed, 0 failed'`,
`'READY_TO_CLOSE 13/13'`, `'APPROVED'` are legitimately terse. One is not: `'9-step plan'` is the
entire summary for a Plan phase and records nothing about what was planned.

## Scope
- Find which writer imposes the 200-character limit (the schema evidently does not) and decide
  whether to raise it, or to truncate visibly with an explicit marker so a reader knows text was
  cut.
- Do not simply remove the limit without checking why it exists — an unbounded summary field has
  its own costs.

## Out of Scope
- Rewriting historical truncated summaries; the text is not recoverable.
- The short-summary cases, other than noting `'9-step plan'` as a prompt-quality signal rather than
  a bug in this subsystem.

## Acceptance Criteria
- [ ] The writer imposing the 200-char boundary is identified.
- [ ] Truncation is either raised/removed with a recorded reason, or made visible (e.g. a trailing
      marker) so a reader can tell a cut summary from a complete one.
- [ ] `docs/agent-monitoring/schema.md` states the limit, whatever it ends up being.

## Related Tickets
- `TCK-20260915-MONITORING-ANOMALY-DETECTION-EPIC` (parent)

## Related Docs
- `docs/agent-monitoring/schema.md`
- `agent-monitoring/retro/RETRO-LAST14D.md` (Summary Quality section)

## Related Stored Artifacts
- None yet.

## Related Code Areas
- `tools/agent-monitoring/record_events.py`
- `.claude/workflows/implement-ticket.js` (`pushEvent` call sites)
- `tools/agent-monitoring/generate_retro.py` (Summary Quality section)

## Assumptions / Open Questions
- Whether the 200 limit is deliberate (cost, readability) or incidental is unknown. If deliberate,
  visible truncation is the better fix than raising it.

## Implementation Notes
Reproduce by measuring summary lengths across the shards; the spike at exactly 200 is unmistakable.

## Test Summary
_To be completed by the implementer._

## Files Changed
_To be completed by the implementer._

## Completion Summary
_Open._
