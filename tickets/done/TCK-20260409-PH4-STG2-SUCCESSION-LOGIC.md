---
status: historical
layer: misc
authority: P1
audience: agent
ticket_id: TCK-20260409-PH4-STG2-SUCCESSION-LOGIC
phase: done
date: 2026-04-09
tags: [ph4, stg2, succession, logic]
---

# Ticket: TCK-20260409-PH4-STG2-SUCCESSION-LOGIC

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Implement the logic for inheritance and succession when an entity (specifically heroes) dies permanently. This includes creating historical records, transferring legacy data, and ensuring successors are linked to the same household.

## Scope
- Update `HeroLifecycleSystem` to handle succession during permadeath.
- Integrate `WorldHistoryRegistry` to record death events and successions.
- Implement `SuccessorRecord` creation and motive transfer.
- Link successors to existing `HouseholdRecord` instances.
- Implement "Heirloom" logic (transferring select items to household storage).

## Out of Scope
- Complex emotional grieving AI for survivors (Phase 5).
- Strategic faction-wide inheritance laws (Stage 3).
- Advanced property management UI.

## Acceptance Criteria
- [ ] Permanent death of a hero creates a `HistoricalEvent` (DEATH).
- [ ] Permanent death creates a `SuccessorRecord` linked to the successor-to-be.
- [ ] Heritage (reputation, select assets) is transferred to the `HouseholdRecord`.
- [ ] Successor hero is born with the same `household_id` and inherits motives from the `SuccessorRecord`.
- [ ] No regressions in standard combat or respawn logic.

## Related Tickets
- TCK-20260409-PH4-STG1-CORE-MODELS (DONE)

## Related Docs
- docs/superpowers/specs/2026-04-09-continuity-and-consequence-design.md

## Status
INPROGRESS
