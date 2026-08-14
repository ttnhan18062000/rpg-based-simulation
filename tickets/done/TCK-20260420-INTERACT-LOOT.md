---
status: historical
layer: misc
authority: P1
audience: agent
ticket_id: TCK-20260420-INTERACT-LOOT
phase: done
date: 2026-04-20
tags: [interact, loot]
---

# TCK-20260420-INTERACT-LOOT

## Title
Channeled Looting and Interruption Recovery

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Recover the original RPG-core interaction behavior for looting ground items and ensuring all channeled interactions are reset by movement or target changes.

## Scope
- Implement ground-item detection and looting in `InteractionSystem`.
- Harden the 'Channeling Law' (reset on movement/target change).
- Verify abort semantics (InteractionUpdate.reset).

## Acceptance Criteria
- [ ] Ground items can be harvested/looted with channeling ticks.
- [ ] Any movement (`moved_this_tick`) properly clears `InteractionComponent.progress`.

## Files Changed
- `src/engine/interaction.py`
- `src/core/state.py` (Potential metadata for ground items)
