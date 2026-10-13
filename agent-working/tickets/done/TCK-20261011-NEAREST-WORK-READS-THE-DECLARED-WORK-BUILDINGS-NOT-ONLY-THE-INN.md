---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261011-NEAREST-WORK-READS-THE-DECLARED-WORK-BUILDINGS-NOT-ONLY-THE-INN
phase: done
date: 2026-10-11
tags: []
---

# TCK-20261011-NEAREST-WORK-READS-THE-DECLARED-WORK-BUILDINGS-NOT-ONLY-THE-INN

## Title
A subject looking for paid work considers every building that declares a WORK shift, not only the inn, so a treasury building's upkeep pays maintenance wages (D58, memo row 61).

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1 (it must land BEFORE THE M0 GATE RUN: H1 earn-by-SELL-or-WAGE and V7 no-dead-way need the treasury-funded shift reachable; designer 2026-10-11)

## Request Summary
Batch 3 (Lane B) made the WORK action table-driven: building_services.SERVICE_KINDS["WORK"] is a declared set, and work_update pays WAGE_GOLD at any WORK building from that building's purse. The treasury tops up a shortfall, and the period's upkeep amount caps the total. The decision layer still can't reach it: ai/goals/opening_steps.py calls work_shift.nearest_work, which hardcodes kind "inn" and an inn-purse affordability check. So upkeep wages never flow in play (disclosed in batch 3).

## Scope
- Same inn-only shape as the hunger and sleep pulls (D56): work is sought at the nearest declared WORK building IN REACH, read from content, never by a building name (it also counts as a hit for M1's no-name-checks probe).
- nearest_work reads the declared WORK set and the paying building's ability to pay (its purse, plus the owning treasury's ability to top it up, within the period's remaining upkeep cap). It reads only; no new scoring terms are stacked.
- UPKEEP IN WORK, NOT COIN (designer ruling 2026-10-11, extends memo row 61 / D58):
  - Each building declares in content how many maintenance SHIFTS it needs per period: one for an ordinary building, more for large ones (a coarse band, D50).
  - Upkeep is DERIVED as shifts needed x WAGE_GOLD (one shift = 6). MAINTENANCE_COST stops being an independent number; retire it.
  - A typed per-period counter on BuildingState, "maintenance shifts done this period", reset each upkeep period. It is canonical, serialised and inspectable. Shifts beyond what's needed are not offered.
  - The solvency/closure check reads the derived upkeep (building purse plus treasury top-up must cover the needed shifts). Unworked upkeep stays in the purse.
  - Rejected: unlimited shifts (make-work and engine charity, against EXCH-02); paying the upkeep coin as the wage (it breaks D58's same-pay-as-the-inn rule).
- Tests: a subject reaches a treasury building's shift; a building whose needed shifts are done this period is not chosen; the counter resets each period; the derived upkeep drives closure; the inn is unchanged.
- Measure with the free-meal-OFF arm: building purse balances, top-up counts, wages paid per kind of building.

## Out of Scope
- Decay or loss of function from neglect (M3).
- New work kinds beyond the declared set.

## Acceptance Criteria
- Upkeep wages flow in the gate worlds once WORK is live (V7: the earning way is used where its preconditions hold).
- Coin is conserved; no coin is minted.

## Related Tickets
Batch 3 treasury (Lane B); parked free-meal removal (d27-removal-stack-batch2); D58; memo row 61.

## Related Docs
docs/world_rules EXCH-02; designer memo row 61.

## Related Stored Artifacts
None yet.

## Related Code Areas
src/ai/goals/opening_steps.py, work_shift.py::nearest_work, building_services.py.

## Assumptions / Open Questions
None.

## Implementation Notes
Built per the owner ruling (memo row 66) and rpg-planner's answers: content flags maintenance_shifts and hires_for_pay copied into BuildingState; WORK set derived from state (work_shift.offers_work), SERVICE_KINDS[WORK] and TREASURY_WORK_KINDS retired; maintenance first (treasury-backed, counted, capped in conservation._wage_result via ResourceTransferIntent.maintenance_shift), else commercial from the purse; upkeep = needed x WAGE_GOLD (MAINTENANCE_COST retired). Divergence 2.117, TOWN-210.

## Test Summary
Unit: work shift, tax and upkeep, maintenance counter; scenario: treasury upkeep; integration: regional sovereignty; forage scenario restaged. Broad non-slow run on this branch: 9119 passed; 4 failures, 3 fixed above (stale fixtures), 1 order-dependent that passes alone. Paired 5-seed measurement: path dormant while the free meal stands (0 wages).

## Files Changed
See the branch diff (src/content, core, engine, worldassembly, worldbuilding, data/content/world/buildings.yaml, resolved worlds, docs, tests).

## Completion Summary
Done on rpg-nearest-work. In-play wage effect is unmeasurable until the free-meal removal lands (disclosed in 2.117).
