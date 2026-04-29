# TCK-20260501-PROGRESSION-HARDENING

## Title

Complete Progression, Skills, Equipment, and Crafting Loop

## Status

DONE

## Request Summary

Harden the progression and equipment systems to ensure advancement meaningfully impacts gameplay outcomes, while maintaining transactional integrity for resources and crafting.

## Scope

- [ ] Separate XP/Progression from Inventory: XP must be rewarded even if inventory is full.
- [ ] Enforce Attribute/Level Caps: Validate growth through authoritative updates.
- [ ] Implement Skill Unlock/Effect loop: Skills should influence combat/utility.
- [ ] Implement Equipment Stats & Burden: Gear affects speed, defense, and capacity.
- [ ] Implement Durability & Repair lifecycle: Transactional gear maintenance.
- [ ] Enforce Crafting Gates: Recipe knowledge, materials, and skill requirements.
- [ ] Create regression test suite in `tests/engine/test_progression_lifecycle.py`.

## Out of Scope

- Multi-classing (kept to single class for simplicity).
- Cosmetic equipment variants.

## Acceptance Criteria

- XP is granted atomically regardless of inventory status.
- Attributes cannot exceed defined caps.
- Equipment meaningfully modifies base stats (ATK, DEF, SPD).
- Durability loss reduces gear effectiveness; repair consumes correct resources.
- Crafting fails without correct materials or recipe knowledge.
- Regression tests pass end-to-end.

## Related Tickets

- None

## Related Docs

- `resource_v2_e4_phases.md`

## Related Stored Artifacts

- None

## Related Code Areas

- `src/progression/leveling.py`
- `src/core/equipment_service.py`
- `src/systems/crafting.py`
- `src/core/attributes.py`

## Implementation Notes

- Use `IdentityUpdate` for all progression changes.
- Use `ResourceUpdate` for repair/crafting material consumption.
- Ensure `SkillScalingService` is the source of truth for derived stats.

## Test Summary

- [ ] Unit tests for XP separation.
- [ ] Integration tests for equipment burden.
- [ ] Lifecycle tests for crafting and repair.
