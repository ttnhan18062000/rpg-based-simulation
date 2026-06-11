---
status: historical
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260502-STRATEGIC-HARDENING
phase: done
date: 2026-05-02
tags: [strategic, hardening]
---

# TCK-20260502-STRATEGIC-HARDENING

## Title
Hardening Strategic Limits and Pipeline Integrity (Phase E5.5)

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Implement and verify missing logic laws from `logic_checklist_exhaustive.md` as specified in `tmp/msg1.txt`. Focus on strategic bandwidth, reason code refactoring, interaction stability, and pipeline budget enforcement.

## Scope
- Refactor `ReasonCode` enums and replace legacy strings in authoritative logic.
- Enforce strategic bandwidth limits (max_leads, max_concerns) during intake.
- Implement interaction cancellation on significant damage.
- Formalize group objective priority over individual projects.
- Implement hard tick-budget abort and frame-pacing.
- Audit and mark attribute scaling semantics (239).

## Out of Scope
- Major combat rebalancing.
- Adding new world zones or regions.

## Acceptance Criteria
- [x] `ReasonCode` enum used in `LegalityServiceV2` and `Pipeline`.
- [x] `max_concerns` and `max_leads` enforced via `enforce_bandwidth`.
- [x] Interaction resets when damage > 5% HP in a single tick.
- [x] Group members prioritize group shared targets over personal projects.
- [x] `Kernel.tick_once` aborts if budget is exceeded.
- [x] All laws (83, 120, 121, 128, 159, 194, 195, 196, 197, 239) marked in `logic_checklist_exhaustive.md`.

## Related Tickets
None

## Related Docs
- `logic_checklist_exhaustive.md`

## Related Code Areas
- `src/core/enums.py`
- `src/engine/pipeline.py`
- `src/engine/kernel.py`
- `src/engine/interaction.py`
- `src/engine/tactical.py`
- `src/systems/strategic.py`
- `src/systems/detour.py`

## Implementation Plan
1. **Refactor Enums**: Update `ReasonCode` in `src/core/enums.py`.
2. **Harden Interaction**: Add damage-based reset in `src/engine/interaction.py`.
3. **Strategic Bandwidth**: Call `enforce_bandwidth` in `StrategicIntelligenceSystem`.
4. **Group Priority**: Update `TacticalDecisionSystem` to respect group shared targets.
5. **Pipeline Safety**: Add budget check in `Kernel` and pacing in runner.
6. **Verification**: Run tests and manually mark the checklist.
