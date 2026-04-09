# TCK-20260325-RPG_DEPTH

## Description
Implement refined attribute depth and systemic RPG mechanics identified in the simulation review investigation. This includes making underutilized stats (CHA, Luck, PER) meaningful, ensuring gear appraisal is class-aware, and distinguishing between field rests and town lodging.

## Scope
- **Attribute Depth**:
  - CHA: Influence party formation and familiarity gain.
  - Luck: Influence loot rarity and rare skill proc rates.
  - PER: Influence trap detection and hidden cache discovery.
- **Class-Aware Items**:
  - Implement class-weighting for `auto_equip_best` and `_item_power`.
- **Lodging Tiers**:
  - Implement `Well-Rested` buff for Town Inns vs generic Field Rests.

## Acceptance Criteria
- [ ] CHA increases familiarity gain rate by `1% per point`.
- [ ] Luck increases `is_crit` and `loot_rarity` rolls.
- [ ] PER allows discovery of items with `HIDDEN` tag in `SpatialIndex`.
- [ ] `auto_equip_best` prioritizes stats matching the `HeroClass`.
- [ ] Town Inn gives a +10% Max HP buff for 100 ticks.
- [ ] Unit tests for all new mechanics pass.

## Related Tickets
- TCK-20260325-RPG_SIMULATION_REVIEW (Done)
