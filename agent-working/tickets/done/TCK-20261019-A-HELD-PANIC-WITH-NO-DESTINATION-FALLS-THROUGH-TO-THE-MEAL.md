---
status: historical
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20261019-A-HELD-PANIC-WITH-NO-DESTINATION-FALLS-THROUGH-TO-THE-MEAL
phase: done
date: 2026-10-19
tags: []
---

# TCK-20261019-A-HELD-PANIC-WITH-NO-DESTINATION-FALLS-THROUGH-TO-THE-MEAL

## Title
A panic whose destination resolves to the subject's own tile is not taken: the tick falls through the existing order (in-place survival, then the arrival at a building) (V3 pre-v1 step, designer ruling "a flight with no destination is not flight").

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
The v1 gate's V3 (frontier_living_world seed 42): merchant 37 starved beside inn 20003 for 1900 ticks. Its panic (low hp, a perceived one-sided hostile adjacent) resolved to a PANIC_RETREAT with its own tile as the target (a hold), returned at src/engine/tactical.py before any survival branch, so neither in_place_survival_update nor the arrival at the inn (`if not hostiles`) was reached. `retreat_destination` returned None because the tile lies in no region (frontier x 41-44 around y 31 is unclaimed space) and the merchant has no home_region_id.

## Scope
- tactical.py: the `emotion.is_fleeing and threats` panic is taken only when `retreat_destination` yields a destination, or when the tactical pass has a real hostile (`_has_tactical_hostiles`, which keeps the old freeze so the fall-through never turns a held panic into a fight).
- Tests: tests/unit/tactical/test_held_panic_falls_through.py (merchant-37 case eats; a wounded subject with a real destination still flees; a held panic beside a real tactical hostile still freezes and does not attack).
- Measured as its own step: paired 3 worlds x seeds 42-46 against origin/main, plus V3 on frontier 42.

## Out of Scope
- Region-independent flight (TCK-20261019-RETREAT-DESTINATION-NEEDS-A-REGION-WOUNDED-SUBJECTS-IN-UNCLAIMED-SPACE-CANNOT-FLEE, after v1).
- The SURV-07 (ii) threat-weighing step, only if V3 stays red.
- The other two retreat sites (tactical.py safety-pressure retreat, and the engaged hp<0.15 retreat): they need a hostile and are unchanged.
- The merchants' missing home_region_id (M1 home-range item).

## Acceptance Criteria
- Merchant-37 case: a hp 10/85, gold 0, hunger 100 subject in an inn's reach in unclaimed space eats (test 1).
- A panic with a real destination is unchanged; a held panic beside a real tactical hostile is unchanged (tests 2, 3).
- Paired 3 x 42-46 reported; crowded_frontier at the stop edge: if people deaths rise past 2 SE plus the floor, report a STOP to the owner.

## Related Tickets
- TCK-20261019-RETREAT-DESTINATION-NEEDS-A-REGION-WOUNDED-SUBJECTS-IN-UNCLAIMED-SPACE-CANNOT-FLEE
- docs/guidelines/intentional_divergences.md 2.78 (arrival beside a building tile) and 2.114 (panic needs a threat in sight)

## Related Docs
- /mnt/data/scratch-rpg-implementer-3/v1_gate_fails_C.md (Lane C trace), /mnt/data/scratch-rpg-implementer/v3_pin.py (scenario)

## Related Stored Artifacts
- agent-working/staging_artifacts/TCK-20261019-A-HELD-PANIC-WITH-NO-DESTINATION-FALLS-THROUGH-TO-THE-MEAL/

## Related Code Areas
src/engine/tactical.py, src/engine/tactical_destinations.py, src/engine/tactical_rest.py

## Assumptions / Open Questions
- Whether V3 turns green on frontier 42 is measured, not assumed; if merchant 37 still starves the report names what holds it next.

## Implementation Notes
tactical.py: panic_destination computed once; the panic branch requires a destination or a real tactical hostile (new helper _has_tactical_hostiles).

## Test Summary
tests/unit/tactical/test_held_panic_falls_through.py (merchant-37 case, a panic with a real destination, a held panic beside a real tactical hostile) and tests/integration/observability/test_starving_wounded_merchant_eats_through_the_real_kernel.py pass on the combined pre-v1 branch (with tests/unit/ai and tests/unit/tactical: 1421 passed, 6 skipped across the observability, rpg_gate and V3 suites). Paired 3 worlds x seeds 42-46 x 5000t reported in divergence 2.135: (b) alone and (b)+(ii) moved no stop rule (D76).

## Files Changed
src/engine/tactical.py; tests/unit/tactical/test_held_panic_falls_through.py; the todo ticket TCK-20261019-RETREAT-DESTINATION-NEEDS-A-REGION-WOUNDED-SUBJECTS-IN-UNCLAIMED-SPACE-CANNOT-FLEE; staging artifacts; docs/REGISTRY.yaml.

## Completion Summary
Landed as part of the combined pre-v1 PR with the (ii) ticket (rpg-v3-starvation-threat 29d4d3d07, (b) a49896e1c). Closed by hand-orchestration at the fold.
