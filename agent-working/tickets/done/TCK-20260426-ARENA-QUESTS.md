---
status: historical
layer: misc
authority: P1
audience: agent
ticket_id: TCK-20260426-ARENA-QUESTS
phase: done
date: 2026-04-26
tags: [arena, quests]
---

# TCK-20260426-ARENA-QUESTS

## Title
Extend E2E Arena Testing for Quest Progression

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Extend the End-to-End Arena testing suite to verify that RPG mechanics (specifically Quests) operate correctly under full simulation pressure.

## Scope
- Add `COMBAT_ARENA_QUESTS` scenario to `src/certification/scenarios.py`.
- Implement `tests/arena/test_arena_quests.py` using the `CertificationHarness`.
- Verify quest completion, XP gain, and gold rewards in a multi-tick arena run.

## Acceptance Criteria
- Scenario spawns a hero with an active `HUNT` quest.
- Hero successfully completes the quest after killing the target kind.
- Quest rewards (XP, Gold) are applied to the hero state.
- Harness reports 100% conformance.

## Implementation Notes
- Uses the `AuthoritativeApplyPipeline` via `CertificationHarness`.
- Leverages `ArenaInjector` for team setup.

## Test Summary
- `tests/arena/test_arena_quests.py` (New)
