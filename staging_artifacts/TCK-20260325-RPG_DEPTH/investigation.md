# Investigation - TCK-20260325-RPG_DEPTH

## Problem Statement
The current simulation has several "dump stats" (Luck, CHA, PER) that don't meaningfully affect gameplay. Additionally, gear selection is class-agnostic, and resting in a Town Inn is no better than resting in the field.

## Findings from Codebase
- **Attributes**: `effective_crit_rate` in `combat.py` uses Luck but with a very low multiplier (0.003).
- **Social**: `familiarity` is tracked in `MindAspect` but gain is constant.
- **Loot**: `loot_rarity` is currently random, not influenced by attributes.
- **Gear**: `_item_power` in `items.py` is a simple sum of stats.
- **Resting**: `RestingInTownHandler` simply waits; it doesn't apply any persistent effects.

## Proposed Logic
1.  **Luck**: Increase crit multiplier and affect `Domain.LOOT` rolls.
2.  **CHA**: Multiply familiarity gain (Socializing with other heroes).
3.  **PER**: Allow seeing entities with `is_hidden=True` in `SpatialAspect`.
4.  **Class Weights**:
    - `Warrior`: {ATK: 3, HP: 2, DEF: 2, SPD: 1}
    - `Mage`: {MATK: 3, MP: 2, DEF: 0.5, SPD: 1}
5.  **Well-Rested**: New `StatusEffect` in `effects.py`.

## Risks
- **Overpowering Luck**: High luck heroes might get infinite legendaries.
- **Stealth Performance**: QuadTree lookup with PER checks for hidden entities must be efficient.
