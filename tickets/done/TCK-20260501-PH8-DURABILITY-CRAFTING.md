---
status: historical
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20260501-PH8-DURABILITY-CRAFTING
phase: done
date: 2026-05-01
tags: [ph8, durability, crafting]
---

# TCK-20260501-PH8-DURABILITY-CRAFTING

## Title
Phase 8: Implementing Equipment Durability and Hardening Crafting

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Implement equipment durability decay during combat, a repair mechanism at the blacksmith, and ensure crafting consumes materials only upon successful output delivery.

## Scope
- Add durability tracking to `EquipmentComponent`.
- Implement durability decay in `CombatResolutionSystem`.
- Implement `REPAIR` action in `BlacksmithSystem`.
- Harden crafting to ensure atomic material consumption (already mostly done, but needs verification).
- Add regression tests for durability and repair.

## Out of Scope
- Detailed item prefixes/suffixes or quality tiers (unless required for durability).
- Item destruction on zero durability (broken items will just provide no stats).

## Acceptance Criteria
- [ ] Equipment has durability and it decreases when hit.
- [ ] Broken equipment (0 durability) provides no stat bonuses.
- [ ] Blacksmith can repair equipment for gold.
- [ ] Crafting materials are consumed only if the item is added to inventory.
- [ ] Tests prove durability decay and repair work deterministically.

## Related Tickets
None

## Related Docs
- [resource_v2_e3_phases_enhanced.md](file:///home/vboxuser/Work/rpg-based-simulation/resource_v2_e3_phases_enhanced.md)

## Related Code Areas
- `src/core/state.py`
- `src/core/updates.py`
- `src/engine/combat.py`
- `src/engine/blacksmith.py`
- `src/engine/pipeline.py`

## Implementation Plan
1.  **State & Updates**: Add `durability` to `EquipmentComponent` and `EquipmentUpdate`.
2.  **Combat Decay**: Modify `CombatResolutionSystem` to emit `EquipmentUpdate` with durability loss.
3.  **Repair Action**: Add `REPAIR` logic to `BlacksmithSystem` and `pipeline.py`.
4.  **Verification**: Create `tests/rpg/test_durability_repair.py`.
