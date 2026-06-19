---
status: open
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260619-P0-HUNGER-SATIATION
phase: open
date: 2026-06-19
tags: [hunger, satiation, world-content, balance, phase-0, p0-foundation]
---

# TCK-20260619-P0-HUNGER-SATIATION

## Title
P0-3 · Hunger Satiation Gap — Add food resource node and verify need resolution

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P0

## Request Summary
No food-kind resource node exists in any tested world. Entities generate `proj_hunger_N` every ~30 ticks but hunger urgency never resolves because there is nothing in the opportunity pipeline that provides food. Hunger permanently outscores all economic goals, making economic balance measurement, crafting validation, quest execution, and personality-driven route diversity unobservable.

Source: `docs/audits/D06_economic_cycle.md` F1; `docs/audits/D04_balance_tuning.md` § Hunger Calibration.

## Scope
- Add a `food_provision` resource node type to `sandbox_world` and `urban_political` world definitions (likely in `data/` world content files)
- Verify the hunger `need` reduction: completing a food-provision project must reduce `BiologicalComponent.hunger` durably (inspect `src/core/state.py:BiologicalComponent`)
- If hunger urgency does not drop after food consumption due to threshold calibration, adjust the urgency threshold so that a satisfied hunger scores below a typical economic goal
- Run a 400-tick `urban_political` simulation and verify ≥10% of active ticks per entity produce non-hunger project kinds

## Out of Scope
- Crafting recipes involving food (Epic 1.3)
- Faction food supply chains (Phase 5)
- Nutritional variation / food quality mechanics

## Acceptance Criteria
- In a 400-tick `urban_political` run, at least 10% of active ticks per entity produce non-hunger project kinds (verified in metric windows or event count)
- At least one `proj_hunger_N` project reaches COMPLETED (not SUSPENDED/REPLACED) in the run
- Hunger urgency drops measurably after food-provision completion (inspect scoring trace)

## Related Tickets
- TCK-20260618-AUDIT-EPIC (source: D06 F1 finding)
- TCK-20260619-P0-ENTITY-INIT (prerequisite: personality seeding; entity differentiation cannot be measured until both are fixed)
- TCK-20260619-E12-BALANCE-BASELINE (blocked by this ticket)

## Related Docs
- `docs/audits/D06_economic_cycle.md`
- `docs/audits/D04_balance_tuning.md`
- `docs/mechanics/01_entity_anatomy.md` § Biological Pressures (hunger trigger threshold — verify against values being fixed in P0-5 before changing)
- `docs/mechanics/03_economic_laws.md` § 3 (Resource Harvesting — update if satiation mechanic changes)
- `docs/plans/long_term_development_roadmap.md` § P0-3
- `docs/parity_ledger/town_resource.yaml` (resource node / harvesting entries — update status)
- `docs/parity_ledger/strategic_cognition.yaml` (need urgency entries — update if threshold changes)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260618-AUDIT-EPIC/`

## Related Code Areas
- `src/core/state.py:L114` (BiologicalComponent — hunger field)
- `src/domains/adventure/scoring.py` (urgency term, hunger urgency function)
- `data/` world content files: sandbox_world, urban_political definitions
- `src/systems/world_systems/` (opportunity providers that return food-kind opportunities)

## Assumptions / Open Questions
- Is the gap pure content (no food node) or also mechanic (hunger satiation code broken)? D06 F1 says the opportunity pipeline has no food-kind node — assume content gap first, fix mechanic only if food node addition doesn't resolve hunger projects
- Which file/schema defines world resource nodes? Check `data/` for existing node patterns before adding new type

## Implementation Notes
D04 identifies two possible causes: urgency threshold too low, or no food node. Try food node first (content-only change). If hunger projects still don't complete after the node is available, check that completing a harvesting/provision project decrements BiologicalComponent.hunger and re-evaluates the urgency term.

After implementation: update `docs/parity_ledger/town_resource.yaml` — set relevant hunger/food entry `status: verified`, add `v2_evidence` and `test_path`. If the urgency threshold changes, also update the corresponding entry in `docs/parity_ledger/strategic_cognition.yaml`. If `docs/mechanics/03_economic_laws.md` is changed, run `make knowledge-index-update`.

## Test Summary
- New file `tests/integration/scenarios/test_hunger_satiation.py`:
  - `test_hunger_satiation_resolves_in_food_world()` — 400-tick `urban_political` run; assert ≥10% of entity ticks produce non-hunger project kinds
  - `test_hunger_project_reaches_completed_status()` — assert at least one `proj_hunger_N` event reaches COMPLETED (not SUSPENDED/REPLACED) in run events
- Regression: rerun existing scenario tests to verify no regressions in other need types

## Files Changed
_To be filled on completion._

## Completion Summary
_To be filled on completion._
