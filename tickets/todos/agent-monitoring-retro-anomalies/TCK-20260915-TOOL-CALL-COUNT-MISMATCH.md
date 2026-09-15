---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260915-TOOL-CALL-COUNT-MISMATCH
phase: open
date: 2026-09-15
tags: [agent-monitoring, data-quality]
---

# TCK-20260915-TOOL-CALL-COUNT-MISMATCH

## Title
53 runs record a `tool_call_count` that contradicts their own `tools.jsonl` rows by more than 3x — including runs claiming 0 while 558 real rows exist

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Comparing each run's summed `tool_call_count` (recorded on its events) against the actual number of
`tools.jsonl` rows carrying that `run_id`, **53 runs disagree by more than 3x in either
direction**. Examples:

| Run | claimed | actual |
|---|---|---|
| `TCK-20260718-TICKET-CORPUS-REPORT` | 0 | 558 |
| `TCK-20260626-FIX-DESIGN-PATTERNS` | 146 | 517 |
| `TCK-20260619-E53Ab-DECISION-PHASE` | 0 | 153 |
| `TCK-20260730-SHADOW-PROMOTION-GATE-THRESHOLDS` | 285 | 91 |

Note the last one runs the *other* way — claimed exceeds actual — so this is not simply "rows were
lost". **14 of the 53 record no count at all** (claimed 0 against real rows).

**This is current, not historical**: by month, 2026-06: 3, 2026-07: 6, **2026-08: 35, 2026-09: 9**.
The August concentration is the largest and unexplained.

Two numbers in the same system describing the same thing and disagreeing is exactly the shape this
epic exists to surface: neither value is flagged, and any consumer picking one gets a different
answer than a consumer picking the other.

## Scope
- Establish which side is authoritative — the per-event `tool_call_count` or the raw `tools.jsonl`
  rows — and record it in `docs/agent-monitoring/schema.md`. Consumers currently have no way to
  know.
- Determine the cause of the August concentration specifically; a 35-run cluster in one month
  suggests a change landed then rather than a steady drift.
- Confirm or rule out a shared cause with `TCK-20260915-SIDECAR-ATTRIBUTION-GAP`. The claimed=0
  cases in particular look like the sidecar gap seen from the other side, but that is a hypothesis
  to test, not an assumption to carry.

## Out of Scope
- Backfilling historical counts.
- The unattributed-rows problem itself (its own ticket).

## Acceptance Criteria
- [ ] One side is documented as authoritative, with the reason.
- [ ] The August cluster is explained, or explicitly recorded as not-determinable.
- [ ] The shared-cause hypothesis with the sidecar ticket is confirmed or refuted — not left open.
- [ ] Any detector ratchets from the measured baseline (53); it must not assert zero.

## Related Tickets
- `TCK-20260915-MONITORING-ANOMALY-DETECTION-EPIC` (parent)
- `TCK-20260915-SIDECAR-ATTRIBUTION-GAP` — probable shared cause
- `TCK-20260708-AGENT-COST-OBSERVABILITY` (done)

## Related Docs
- `docs/agent-monitoring/schema.md`
- `agent-monitoring/retro/RETRO-LAST14D.md`

## Related Stored Artifacts
- None yet.

## Related Code Areas
- `tools/agent-monitoring/record_events.py` (`compute_tool_stats`)
- `.claude/settings.json` (`PostToolUse` hook writing `tools.jsonl`)
- `agent-monitoring/data/*/events.jsonl`, `agent-monitoring/data/*/tools.jsonl`

## Assumptions / Open Questions
- The >3x threshold was chosen to surface gross disagreement, not to define acceptable drift. A
  smaller threshold will find more; the real tolerance is a decision this ticket should make.

## Implementation Notes
Derive from the shards, not `monitoring.db`.

## Test Summary
_To be completed by the implementer._

## Files Changed
_To be completed by the implementer._

## Completion Summary
_Open._
