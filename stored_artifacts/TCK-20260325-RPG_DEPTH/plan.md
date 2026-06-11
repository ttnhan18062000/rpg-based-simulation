---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260325-RPG_DEPTH
artifact_type: plan
tags: [rpg_depth]
---

# Implementation Plan - TCK-20260325-RPG_DEPTH

## Proposed Changes

### [Component] Attribute Scaling
- **Luck**: Modify `effective_crit_rate` for 5x impact. Implement `loot_rarity` bonus.
- **CHA**: Multiply familiarity gain by `(1 + CHA/100)`.
- **PER**: Hidden entity discovery logic in `SpatialIndex`.

### [Component] Class Awareness
- Refactor `_item_power` to use a `WeightMap` per `HeroClass`.

### [Component] Lodging
- Add `WellRestedEffect` to `src/core/effects.py`.
- Update `RestingInTownHandler` to apply effect.
