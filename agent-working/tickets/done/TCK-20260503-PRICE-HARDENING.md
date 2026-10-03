---
status: historical
layer: misc
authority: P1
audience: agent
ticket_id: TCK-20260503-PRICE-HARDENING
phase: done
date: 2026-05-03
tags: [price, hardening]
---

# TCK-20260503-PRICE-HARDENING

## Title
Price Hardening E5.6: Pressure-Aware Economic Regulation

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Audit and harden the Town Economy (General Store) to prevent economic bankruptcy during Calamity/Survival events. Implement dynamic pricing based on operational pressure signals.

## Scope
- Implement `DynamicPriceService` to calculate item values based on `AuthoritativeState.pressure_signals`.
- Modify `src/town/shop.py` to utilize dynamic pricing in `buy_item`.
- Implement a "Fair Trade Law" (Price Cap) during `SURVIVAL` and `DEGRADED` governor modes.
- Add authoritative audit logging for price deviations in `ResourceTransferIntent`.
- Add contract tests for price caps during simulated stress events.

## Out of Scope
- Dynamic selling prices (stay at 50% of base for now).
- Blacksmith material cost hardening (separate ticket).
- Item stock/inventory replenishment logic.

## Acceptance Criteria
- `ShopService.buy_item` returns a `StateUpdate` with prices scaled by world pressure.
- Prices never exceed 3.0x base value during any event (Price Cap).
- No "Unlimited Arbitrage" possible by hoarding items at static prices.
- Deterministic behavior: same state + same pressure = same price.

## Related Tickets
- TCK-20260502-STRATEGIC-HARDENING

## Related Docs
- `docs/buildings_economy.md`
- `src_v2_principle.md`

## Related Stored Artifacts
- None

## Related Code Areas
- `src/town/shop.py`
- `src/core/updates.py`

## Assumptions / Open Questions
- Assume `pressure_signals` are correctly updated by the Kernel.
- Question: Should the price cap be configurable per `RuntimeProfile`? (Initial: Hardcoded 3.0x).

## Implementation Notes
- Use `state.pressure_signals.get('global_salience', 0.0)` as the primary multiplier source.

## Test Summary
- Added `tests/rpg/test_economy_hardening.py`
- Verified normal pricing (1.0x), pressure scaling (1.5x), and 3.0x caps.
- Verified arbitrage prevention (static sell prices).

## Files Changed
- `src/core/state.py`
- `src/core/updates.py`
- `src/engine/apply.py`
- `src/engine/kernel.py`
- `src/systems/economy.py`
- `src/town/shop.py`
- `src/engine/shop.py`
- `src/core/items.py`

## Completion Summary
Implemented a robust, pressure-aware economic regulation system. The General Store now dynamically adjusts prices based on global simulation stress (work debt + compute pressure), while the "Fair Trade Law" ensures that prices never exceed 3.0x base value. All price calculations are verified at the authoritative pipeline entrance.
