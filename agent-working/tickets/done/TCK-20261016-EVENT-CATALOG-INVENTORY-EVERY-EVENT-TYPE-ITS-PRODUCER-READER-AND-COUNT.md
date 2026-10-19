---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20261016-EVENT-CATALOG-INVENTORY-EVERY-EVENT-TYPE-ITS-PRODUCER-READER-AND-COUNT
phase: done
date: 2026-10-16
tags: []
---

# TCK-20261016-EVENT-CATALOG-INVENTORY-EVERY-EVENT-TYPE-ITS-PRODUCER-READER-AND-COUNT

## Title
Event catalog inventory: every event type that exists, with its producer, source record, payload, category and severity, SimQ reader and measured count per world (read-only)

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
Owner decision 80 (i): before v1 the event catalog is read-only, with no code change to events. rpg-planner asked for one stored-artifact table that goes to the designer, and that v1 uses to disclose the dead and never-fired types.

## Scope
- One table of every event type under src/: producer (file:line and which path), the typed record or update field it derives from (or inline / free dict), payload shape, category and severity, the SimQ pillar that reads it (scorer EVENT_TYPES after quality_hub._translate), and its measured count per world on seeds 42-46 x 5000 ticks.
- Flags: SimQ types never emitted; emitted types nobody reads; events built in authoritative code; SimQ-motivated seeds (SIMQ-UPLIFT3, SIMQ-COGNITION-PIPELINE-WIRE and similar) marked "D33 candidate?".
- Counts from lossless runs (observability on, no backpressure sampling), with a note of how that was ensured.

## Out of Scope
- Any change to events, the recorder, the extractor, the shapers or SimQ.
- Deciding which types to keep (designer).

## Acceptance Criteria
1. The table lists every event type with a producer in src/ plus every type measured.
2. Counts come from runs with no drops: the recorder stayed NORMAL, nothing dropped by mode or queue, and the evidence per run is in the artifact.
3. The four flags are separate sections.
4. No source file changed.

## Related Tickets
- TCK-20260806-SIMQ-OBSERVABILITY-PUSH-MIGRATION-EPIC (the push shapers)

## Related Docs
- docs/guidelines/design_patterns.md (Pattern 6, compile-time pillar activation)

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261016-EVENT-CATALOG-INVENTORY-EVERY-EVENT-TYPE-ITS-PRODUCER-READER-AND-COUNT/

## Related Code Areas
- src/observability/event_extractor.py, event_shapers.py, events.py, event_recorder.py; src/simulation_quality/quality_hub.py and scorers/

## Assumptions / Open Questions
- The knowledge index and graph were absent in the worktree; context came from direct reads.
- Runs use FULL observability mode (every flag on) so mode-gated events are reachable; default feature flags otherwise (events gated by OFF-by-default feature flags show a gate in the table).

## Implementation Notes
Artifact: agent-working/stored_artifacts/TCK-20261016-EVENT-CATALOG-INVENTORY-EVERY-EVENT-TYPE-ITS-PRODUCER-READER-AND-COUNT/event_catalog.md (the table and flags), event_counts_per_seed.tsv, probes/ (static scan, run child, builders). 138 event types: 69 measured, 69 with a producer that never fired in the 15 runs. Headline findings (section 0 of the artifact): the event file loses all non-critical events once 5000 CRITICAL biological_state_changed events have accumulated (FULL mode; also the gate's tally events); combat_resolved is emitted; alert events reach neither the recorder nor SimQ; lead_contradiction events are built and discarded; clan, leadership and betrayal events are buffered with no production reader; no InvariantViolation fired; the Economy events never fire in these worlds.

## Test Summary
No source change. 15 runs (3 worlds x seeds 42-46 x 5000 ticks, FULL observability, audit_mode); recorder stayed NORMAL with 0 drops by mode or queue in all of them; evidence table in the artifact.

## Files Changed
Only agent-working/ (this ticket, its stored artifacts).

## Completion Summary
The event catalog inventory is written and measured, with the four flags and the pipeline findings. Nothing in src/ changed. Branch rpg-event-catalog, not pushed.
