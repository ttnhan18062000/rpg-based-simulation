# Test Plan: RPG Core Hardening

## Scenario PROGRESSION
- Kill monster -> Check XP/Gold gain -> Check Corpse spawning with items.

## Scenario MORTALITY
- Hero dies (Gen 1) -> Check Rebirth (Gen 2, No items).
- Hero dies (Gen 4) -> Check Permadeath (is_permadeath=True).

## Scenario TACTICAL
- High Ground at (10,9) vs (10,10) -> Verify +20% damage.
- Flanking (North/South) vs Center -> Verify +15% damage.

## Scenario SOCIAL
- Adjacent bonded ally -> Verify +10% synergy bonus.

## Scenario ATTRITION
- 100% Hunger -> Check 5 HP decay.
- >80 Sleep Debt -> Check 20% Atk penalty and 50% Readiness penalty.
- Frozen status -> Check 1.5x Shatter damage.
