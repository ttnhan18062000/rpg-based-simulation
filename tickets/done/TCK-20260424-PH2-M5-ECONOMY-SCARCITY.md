# TCK-20260424-PH2-M5-ECONOMY-SCARCITY

## Title
Phase 2 Milestone 5: Economy & Scarcity

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Implement dynamic pricing and resource depletion mechanics to enforce economic scarcity and environmental pressure.

## Scope
- Implement trauma-based price scaling in `ShopSystem`.
- Integrate resource node harvesting into the `TacticalDecisionSystem`.
- Propagate resource node state to workers via `WorkerPacket`.
- Verify authoritative depletion and cooldown logic.

## Acceptance Criteria
- Selling items in high-trauma regions yields more gold (Risk Premium).
- Entities automatically identify, move to, and harvest nearby resource nodes.
- Resource nodes decrement charges upon harvest and enter cooldown when depleted.

## Related Tickets
- TCK-20260424-PH2-M4-SOCIAL-CONTINUITY (Done)

## Completion Summary
- Dynamic pricing implemented: `price = base * (1 + trauma / 10)`.
- Tactical harvesting loop implemented.
- Worker protocol extended with `resource_nodes` context.
- Verified with `test_economy_scarcity.py`.
