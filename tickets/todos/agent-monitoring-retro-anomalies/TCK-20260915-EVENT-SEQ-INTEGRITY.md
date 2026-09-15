---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260915-EVENT-SEQ-INTEGRITY
phase: open
date: 2026-09-15
tags: [agent-monitoring, data-quality]
---

# TCK-20260915-EVENT-SEQ-INTEGRITY

## Title
71 runs have duplicate `seq` values and 46 have gaps — the field that orders phases within a run does not reliably order them

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
`seq` is the per-run ordering key for events (1-indexed, in phase order — see
`record_hand_orchestrated_closure.py`'s own docstring, which fills it automatically). Scanning the
corpus:

- **71 runs contain a duplicate `seq`** — most commonly two events both claiming `seq=1`
- **46 runs have gaps** — e.g. `TCK-20260614-CERT-EVIDENCE-LEVELS` missing 1, 2, 3, 4;
  `TCK-20260619-E33C-GOLD-SINK` missing 1–5

A related, separately-confirmed fact bears on this: **345 runs write 5+ events sharing a single
identical timestamp** (up to 34 events at one instant). That was investigated during scoping and is
*not* itself a defect — it is the orchestrator flushing a batch, and the agent mix in those runs is
the normal subagent roster, not hand-orchestration. But it means **timestamps cannot be used to
recover ordering when `seq` is broken**, which is what makes `seq` integrity matter rather than
being cosmetic.

## Scope
- Determine how duplicate `seq` values arise. The `seq=1` concentration suggests either two writers
  both starting a run, or a re-run overlaying the original without offsetting.
- Determine whether gaps mean events were lost, or were never written (a skipped phase that records
  nothing rather than a `skipped` status).
- Establish and document what consumers may assume about `seq` — contiguity, uniqueness, or
  neither. Several readers currently assume more than the data supports.

## Out of Scope
- The 345 bulk-timestamp runs as such; they are documented as expected. Only their consequence
  (timestamps cannot substitute for `seq`) is in scope.
- Duplicate *run* records — `TCK-20260915-DUPLICATE-RUN-RECORDS`, though a shared cause is
  plausible and worth checking.

## Acceptance Criteria
- [ ] The cause of duplicate `seq` is identified, or recorded as not-determinable.
- [ ] Gap semantics are resolved: lost events versus never-written.
- [ ] `docs/agent-monitoring/schema.md` states what `seq` guarantees.
- [ ] Any detector ratchets from the measured baselines (71 duplicate, 46 gapped); it must not
      assert zero.

## Related Tickets
- `TCK-20260915-MONITORING-ANOMALY-DETECTION-EPIC` (parent)
- `TCK-20260915-DUPLICATE-RUN-RECORDS` — possible shared cause

## Related Docs
- `docs/agent-monitoring/schema.md`
- `agent-monitoring/retro/RETRO-LAST14D.md`

## Related Stored Artifacts
- None yet.

## Related Code Areas
- `tools/agent-monitoring/record_events.py`
- `tools/agent-monitoring/record_hand_orchestrated_closure.py` (auto-fills `seq`)
- `.claude/workflows/implement-ticket.js` (`pushEvent` call sites)

## Assumptions / Open Questions
- Whether `seq` is meant to be unique per `(run_id)` or per `(run_id, phase)` is unconfirmed;
  check the schema before treating duplicates as defects.

## Implementation Notes
Derive from the shards directly, not `monitoring.db`.

## Test Summary
_To be completed by the implementer._

## Files Changed
_To be completed by the implementer._

## Completion Summary
_Open._
