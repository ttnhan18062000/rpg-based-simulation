---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260702-SIMQ-UPLIFT-DUNGEON-ECON-COG
phase: open
date: 2026-07-02
tags: [simulation_quality, economy, cognition, dungeon_crawl, world_spec, archetype]
---

# TCK-20260702-SIMQ-UPLIFT-DUNGEON-ECON-COG

## Title
Investigate and resolve ECONOMY / COGNITION zero-activation in dungeon_crawl across all tick counts

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
ECONOMY and COGNITION score 0 events in dungeon_crawl at every tick count (200t, 500t, 1000t, 2000t, all 3 seeds). In contrast:
- sandbox_world at 1000t: ECONOMY=B (24 events), COGNITION=B (7 events)  
- urban_political at 1000t: ECONOMY=B (24 events), COGNITION=C (0 events)
- simq_routing_test at 500t: COGNITION=B (ENABLE_ADVENTURE_ROUTING=ON)

Investigation reveals:
1. **ECONOMY gap**: sandbox_world activates ECONOMY via `gold_sink_fired` events (48 score records, src_kind=REPAIR_FEE/SERVICE_FEE/TAX). dungeon_crawl has **0 populations** and no town/service infrastructure — entities in dungeon_crawl have no gold sinks to fire. The 3 resource_nodes in dungeon_crawl's world spec do not produce harvesting events in practice.
2. **COGNITION gap**: dungeon_crawl has 0 populations and no entities appear to update self_model or assimilate beliefs. COGNITION at sandbox_world 1000t (7 events) suggests some entity-level cognitive updating happens there that doesn't happen in dungeon_crawl's pure-combat entity configuration.

The open question is whether this is archetype-intentional (dungeon crawl = combat arena, no economic or cognitive complexity) or a fixable world spec gap.

`data/worlds/dungeon_crawl/resolved/world.resolved.yaml` top-level:
- 16 factions, 4 regions, 3 resource_nodes (resources key), 0 populations, entities defined explicitly

## Scope
1. Inspect `data/worlds/dungeon_crawl/` world spec (source + resolved) to understand entity and resource node configuration:
   - What entity types exist? Do any have economic or cognitive behavioral profiles?
   - What are the 3 resource nodes? Are they wired to any harvesting behavior?
   - Why does dungeon_crawl have 0 populations vs sandbox_world's entity generation?
2. Compare with `data/worlds/sandbox_world/` to identify what enables `gold_sink_fired` events there.
3. Identify the EconomyScorer event types that could plausibly fire in dungeon_crawl: `resource_harvested`, `item_crafted`, `shop_transaction`, `trade_executed`, `quest_reward_dispensed`, `gold_sink_fired`.
4. For COGNITION: identify what drives self_model updates and belief assimilation in sandbox_world at 1000t.
5. **Make an explicit archetype decision**, one of:
   - **DA (Archetype-Intentional)**: dungeon_crawl is a combat-only archetype; ECONOMY=C and COGNITION=C are correct. Document as intended in `docs/simulation_quality/eval_matrix_results.md`. No world spec change.
   - **DB (Fixable Gap)**: dungeon_crawl can and should have some economic and/or cognitive activity. Add minimal world spec extensions (e.g., a repair merchant NPC, loot economy, or lead-bearing quest entities) to activate these pillars.
6. Update parity ledger and eval_matrix_results.md accordingly.

## Out of Scope
- FACTION/SOCIAL/INFORMATION zero-activation (global gap, separate ticket TCK-20260702-SIMQ-UPLIFT-SOCIAL-ZERO)
- The COGNITION gap at urban_political (investigated separately if needed)
- Achieving A/B grade targets for ECONOMY/COGNITION in dungeon_crawl in this ticket — first goal is non-zero activation

## Acceptance Criteria
- [ ] dungeon_crawl world spec (source + resolved) read and entity/resource/population configuration documented in investigation.md
- [ ] sandbox_world world spec read and the configuration that enables `gold_sink_fired` identified (what entity types? what behavioral profiles?)
- [ ] Archetype decision (DA or DB) documented with rationale in investigation.md and `docs/simulation_quality/eval_matrix_results.md`
- [ ] If DA: eval_matrix_results.md updated with explicit statement "dungeon_crawl ECONOMY=C, COGNITION=C are archetype-correct"; grade_anchors.json confirms anchors already reflect this
- [ ] If DB: world spec extension implemented, calibration re-run for dungeon_crawl, ≥1 non-zero ECONOMY or COGNITION event confirmed in quality_scores.jsonl, grade_anchors.json updated
- [ ] `make evaluate --dry-run` exits 0 after any anchor changes

## Related Tickets
- TCK-20260702-SIMQ-EVAL-MATRIX — established the multi-world calibration corpus that surfaced this gap
- TCK-20260702-SIMQ-UPLIFT-SOCIAL-ZERO — sibling: global FACTION/SOCIAL/INFORMATION zero-activation
- TCK-20260702-SIMQ-UPLIFT-GRADE-DECAY — sibling: COMBAT/WORLD grade decay in dungeon_crawl multi-tick

## Related Docs
- `docs/simulation_quality/eval_matrix_results.md` — grade distribution matrix
- `docs/simulation_quality/event_type_coverage.md` — §1.1: `resource_harvested`, `item_crafted`, `gold_sink_fired` all show calibration_hits=0 (based on 200t audit)
- `docs/simulation_quality/quality_scoring_contract.md` — §6 EconomyScorer, §8 CognitionScorer contracts
- `docs/mechanics/03_economic_laws.md` — atomic conservation, harvesting, trade laws
- `docs/mechanics/04_strategic_cognition.md` — lead/belief/self-model mechanics

## Related Stored Artifacts
- (none yet)

## Related Code Areas
- `data/worlds/dungeon_crawl/` — world spec source files
- `data/worlds/dungeon_crawl/resolved/world.resolved.yaml` — resolved spec (16 factions, 4 regions, 3 resource_nodes, 0 populations)
- `data/worlds/sandbox_world/` — comparison world spec
- `src/simulation_quality/scorers/economy.py` — EconomyScorer, EVENT_TYPES: resource_harvested, item_crafted, shop_transaction, trade_executed, quest_reward_dispensed, gold_sink_fired
- `src/simulation_quality/scorers/cognition.py` — CognitionScorer, EVENT_TYPES: self_model_updated, belief_updated, etc.
- `data/calibration/dungeon_crawl_seed42_2000t/quality_scores.jsonl` — confirmed 0 ECONOMY events
- `data/calibration/sandbox_world_seed42_1000t/quality_scores.jsonl` — 48 `gold_sink_fired` records → 24 ECONOMY events

## Assumptions / Open Questions
- **AQ1**: dungeon_crawl has 0 populations but explicit `entities` — what entity types are they? Do they have economic behavioral profiles enabled?
- **AQ2**: What is the difference in world spec between sandbox_world (activates ECONOMY at 1000t via gold_sink) and dungeon_crawl (never activates ECONOMY)? Is it entity types, building types (repair/service buildings), or behavioral flags?
- **AQ3**: Is 0 populations in dungeon_crawl intentional (dungeon is a static generated environment with discrete named entities, no emergent NPC groups)?
- **AQ4**: For COGNITION, does sandbox_world 1000t cognitive activity come from self_model updates, belief assimilation, or time-gate penalties? Check quality_scores.jsonl for sandbox_world_seed42_1000t COGNITION event_types.

## Implementation Notes
- The `gold_sink_fired` event fires from `intent_results` where `src_kind in (REPAIR_FEE, SERVICE_FEE, TAX)`. These require service buildings or tax mechanics in the world. dungeon_crawl as a combat dungeon likely has none of these.
- If DA is chosen, the archetype distinction should be documented: dungeon_crawl is "combat + world" world (COMBAT and WORLD activate); sandbox/urban are "economy + cognition" worlds (ECONOMY and COGNITION activate at 1000t+).
- The 3 resource_nodes in dungeon_crawl show `resource_harvested` calibration_hits=0 even at 2000t. Either entities don't harvest them (no harvesting behavioral profile), or the harvesting events aren't emitted. This is a separate data point worth documenting.

## Test Summary
- Read dungeon_crawl and sandbox_world world specs; diff entity configurations
- Check `data/calibration/sandbox_world_seed42_1000t/quality_scores.jsonl` for COGNITION event_types (to understand what drives sandbox COGNITION)
- If DB: run calibration post-fix, verify ≥1 ECONOMY or COGNITION event in quality_scores.jsonl
- `make evaluate --dry-run` must exit 0 after any anchor updates

## Files Changed
(to be filled during implementation)

## Completion Summary
(to be filled on completion)
