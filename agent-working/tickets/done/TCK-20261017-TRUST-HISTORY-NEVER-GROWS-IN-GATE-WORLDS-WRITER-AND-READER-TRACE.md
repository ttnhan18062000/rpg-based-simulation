---
status: historical
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20261017-TRUST-HISTORY-NEVER-GROWS-IN-GATE-WORLDS-WRITER-AND-READER-TRACE
phase: done
date: 2026-10-17
tags: []
---

# TCK-20261017-TRUST-HISTORY-NEVER-GROWS-IN-GATE-WORLDS-WRITER-AND-READER-TRACE

## Title
Why trust_history never grows in the gate worlds: writer, blocker and reader trace (read-only)

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
rpg-planner dispatch (designer D78 finding), investigation_only: list every trust writer with file:line and wiring, probe seed 42 x 5000t on 3 worlds to name the blocking condition, list every reader, and stop and report first if it is a D7-kind dropped-update bug. No fix.

## Scope
Static trace plus an out-of-src probe on rpg-next a1e4b6f3a.

## Out of Scope
Any change under src/ or tests/; any fix to the missing positive writer.

## Acceptance Criteria
Writers with file:line and wiring; probe counters per writer (calls, reached update, survived apply); blocking condition named; readers with file:line.

## Related Tickets
TCK-20260911-COOPERATION-TRUST-HISTORY-ZERO-ACCUMULATION-INVESTIGATION (earlier trace; its unwired learn() is now called for "abandoned" only); TCK-20261016-GRIEF-AS-STATE-GRIEF-TRIGGERS-ARE-DETECTED-AND-CARRIED-IN-AUTHORITATIVE-STATE-D80.

## Related Docs
agent-working/stored_artifacts/TCK-20261017-TRUST-HISTORY-NEVER-GROWS-IN-GATE-WORLDS-WRITER-AND-READER-TRACE/investigation.md

## Related Stored Artifacts
agent-working/stored_artifacts/TCK-20261017-TRUST-HISTORY-NEVER-GROWS-IN-GATE-WORLDS-WRITER-AND-READER-TRACE/

## Related Code Areas
src/systems/social_systems/relationships.py; src/domains/cooperation/; src/systems/social_systems/appraisal.py; src/engine/domain/combat_actions.py

## Assumptions / Open Questions
The repeated -0.25 per tick under MEMBER_ABANDONING is inferred from counts, not separately probed.

## Implementation Notes
Read-only. No D7-kind bug: every update that reaches process_update survives apply. No wired writer can raise trust; all 411 deltas in the 3 runs are negative.

## Test Summary
No tests; probe results in the artifact folder.

## Files Changed
Ticket and stored artifacts only.

## Completion Summary
See investigation.md: writers table, probe table, readers table.
