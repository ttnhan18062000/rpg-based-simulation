---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20261008-ENV-08-SETTLED-LAND-AND-THE-NEAR-WILD-CARRY-NO-STANDING-AMBIENT-HAZARD
phase: done
date: 2026-10-08
tags: []
---

# TCK-20261008-ENV-08-SETTLED-LAND-AND-THE-NEAR-WILD-CARRY-NO-STANDING-AMBIENT-HAZARD

## Title
Settled land, camps and the near edge of the wild carry no standing ambient hazard (ENV-08, owner decision 30): `trading_hometown`, `survivor_outpost` and the `wolf_den_near_forest` `near_forest` go to hazard 0.

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Lane B found that `trading_hometown` (hazard 0.5, 5 HP per tick) sits on the only road to the wild-food node and kills a `town_council` worker in 20 ticks, and `near_forest` (1.0) kills in 11, so no broke town worker could ever forage. Owner decision 30 ruled settled land and the near wild survivable.

## Scope
1. Content: three region hazard levels to 0.0 (`trading_company_hub`, `survivor_camp_shelter`, `wolf_den_near_forest`). 2. The derivation of the `near_forest` value. 3. SPC-S16 as a `mechanic_scenario`, and the compile assertion that no settled region carries a standing hazard.

## Out of Scope
Deep and cursed land, calamity, MIASMA, endurance, the drain formula and hazard-aware pathing are unchanged. The second `near_forest` region of the `nomadic_herd` module (hazard 1.5, no settlement near) is not a near edge and stays; its duplicate id is a separate P3 content ticket.

## Acceptance Criteria
- [x] The three values are 0.0 in every resolved world. - [x] SPC-S16: a full-HP `town_council` worker crosses the second town, gathers in `near_forest` and walks home at full HP; the control into `deep_forest` dies of HAZARD inside it. - [x] No TOWN or SETTLEMENT region, nor `survivor_outpost`, carries a standing hazard in any resolved world. - [x] Divergence 2.92 with before and after per region and the derivation.

## Related Tickets
- `TCK-20261007-A-NEED-WITH-NO-OPEN-WAY-PULLS-TOWARD-THE-STEP-THAT-OPENS-ONE-SURV-07-AMENDMENT` (the forage loop this unblocks)
- `TCK-20261007-EAT-BESIDE-THE-INN-FEEDS-A-SUBJECT-THAT-CANNOT-PAY-FREE-MEAL` (parked removal)

## Related Docs
- `docs/guidelines/intentional_divergences.md` 2.92; `docs/mechanics/05_world_evolution.md` Hazard Impacts; `docs/parity_ledger/world_dynamics.yaml` WORLD-129; designer commits b4ead0882, 3458f17d0 (ENV-08).

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261008-ENV-08-SETTLED-LAND-AND-THE-NEAR-WILD-CARRY-NO-STANDING-AMBIENT-HAZARD/` (investigation, plan, test plan); the shared probes and measurement rows are in `agent-working/stored_artifacts/TCK-20261007-EAT-BESIDE-THE-INN-FEEDS-A-SUBJECT-THAT-CANNOT-PAY-FREE-MEAL/probes/`.

## Related Code Areas
- `data/content/world_modules/trading_company_hub.yaml`, `survivor_camp_shelter.yaml`, `wolf_den_near_forest.yaml`; `src/world/environment.py` (read only).

## Assumptions / Open Questions
- By owner ruling (2026-10-08) the batch lands with free meals still on; the free-meal removal is parked on branch `d27-free-meal-removal` under `TCK-20261007-EAT-BESIDE-THE-INN-FEEDS-A-SUBJECT-THAT-CANNOT-PAY-FREE-MEAL` (kept open).
- Decision 31's landing bar (a second way to eat in all three measured worlds) is not met; recorded with numbers in divergence 2.91 and on the parked ticket.

## Implementation Notes
Three `hazard_level` values changed to 0.0 with the derivation as a comment; all 24 resolved worlds regenerated. The derivation: 180 thickets over nine worlds at seeds 42 to 61 stand 1 to 13 steps (median 4) from the nearest tile `near_forest` does not own; a visit is 26 ticks of walking plus 33 for the first gather and 44 for each next; p10 starting HP of a forager is 78; the smallest nonzero drain is 1 HP per tick (`int(level * 10)`), which leaves 19 HP after one gather and kills at two, so no level meets a half-HP margin and the value is 0.

## Test Summary
`tests/mechanic_scenarios/test_near_wild_is_survivable_deep_wild_is_not.py` 4 passed (SPC-S16 on `frontier_extended`, the (2,71) control, the compile assertion over every resolved world). Combined effect in the batch headline of divergence 2.91.

## Files Changed
Content only (three module files, 24 resolved worlds), the SPC-S16 test, parity WORLD-129, divergence 2.92, Bible 05 line, a `regional_hazard_drain` mechanism note.

## Completion Summary
The settled-land and near-wild hazards are 0.0, so a town worker can now walk to the forest and back; the lethal danger is still real in deep land (SPC-S16 control). Effect on the pinned bar is read together with the rest of the batch in divergence 2.91.
