# TCK-20260420-INTERACT-LOOT

## Title
Channeled Looting and Interruption Recovery

## Status
OPEN

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
- `src_v2/engine/interaction.py`
- `src_v2/core/state.py` (Potential metadata for ground items)
