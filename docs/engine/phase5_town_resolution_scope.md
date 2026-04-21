# Phase 5: Town Resource Resolution Scope (Milestone 2)

## Definition
Town Resource Resolution is the process of converting gathered materials and gold into progression state (Gear, Knowledge, Blockers Cleared) within the town boundary.

## Supported Behavior (In-Scope)
1. **Town Passive Healing**:
   - Automated HP recovery for allied entities within the Town grid tiles.
   - Respects `town_passive_heal` and `hero_heal_per_tick` config.
2. **Material/Item Selling**:
   - Conversion of inventory items (specifically Materials and inferior Gear) into Gold.
   - Price calculation based on base value and rarity.
3. **Blacksmith Material Conversion**:
   - Crafting of basic tiered equipment (e.g., `steel_sword`, `iron_plate`) using Gold and Materials (`wood`, `iron_ore`).
   - Resolution of Material Blockers via successful crafting.
4. **Town-Entry Truth**:
   - Progression updates on town arrival (e.g., resetting "Need to Sell" desire).

## Explicitly Excluded (Out-of-Scope)
- **Guild Intel/Quests**: Knowledge resolution is Milestone 4.
- **Class Hall Training**: Skill acquisition is Milestone 4.
- **Dynamic Pricing/Reputation**: Price modifiers from reputation are deferred.
- **Advanced Socials (Inn/Home)**: Home storage and recruitment are deferred.
- **Rich Economy**: Dynamic shop restocks or global market fluctuations.

## Support Boundary
- Supported for all **Hero** entities.
- Supported in **Local** baseline execution. Concurrent resolution is supported if entities do not conflict on the same shop (sequential resolution).
