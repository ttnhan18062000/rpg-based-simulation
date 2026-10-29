---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20261028-OBSERVABILITY-GUIDE-NAMES-EVENT-FIELD-CATEGORY-NOT-EVENT-CATEGORY
phase: done
date: 2026-10-28
tags: []
---

# TCK-20261028-OBSERVABILITY-GUIDE-NAMES-EVENT-FIELD-CATEGORY-NOT-EVENT-CATEGORY

## Title
docs/guides/observability.md calls the event-log field `category`, but simulation_events.jsonl writes `event_category`

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P3

## Request Summary
Reported by lead-planner-u24 (2026-10-28) while answering questions about reading the event log. The "Reading the event log" example in `docs/guides/observability.md` (line 79) shows `"category": "combat"`, but `src/observability/event_recorder.py` (around lines 120-140) writes the key `event_category`. Anyone reading the log from the guide looks for a key that does not exist.

## Scope
- Change the example key at line 79 to `event_category`, and check the rest of the guide for the same name used as a log key. Line 170 ("optional `category`") refers to the `EventCategory` in events.py: check whether that is the field name on the event definition and leave it if it is correct.

## Out of Scope
- Renaming anything in code.

## Acceptance Criteria
- Every log key the guide names matches what event_recorder.py writes.
- `make knowledge-index-update` has been run.

## Related Tickets
## Related Docs
- docs/guides/observability.md
## Related Stored Artifacts
## Related Code Areas
- src/observability/event_recorder.py
- src/observability/events.py
## Assumptions / Open Questions
- Small enough to ride with the next rpg docs PR. Not dispatched yet.
## Implementation Notes
docs/guides/observability.md line 79 example key and line 170 field name changed to event_category (matches event_recorder.py and the EventCategory-typed field on events.py definitions). make knowledge-index-update run.
## Test Summary
Docs only.
## Files Changed
docs/guides/observability.md
## Completion Summary
Done in the observability hotfix batch (one PR).
