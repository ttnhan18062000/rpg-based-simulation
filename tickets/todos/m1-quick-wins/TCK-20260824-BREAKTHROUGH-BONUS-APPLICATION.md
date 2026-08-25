---
status: active
layer: core
authority: P1
audience: agent
ticket_id: TCK-20260824-BREAKTHROUGH-BONUS-APPLICATION
phase: open
date: 2026-08-24
tags: [progression]
---

# TCK-20260824-BREAKTHROUGH-BONUS-APPLICATION

## Title
Finish BreakthroughService.apply_bonuses()

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
BreakthroughService.apply_bonuses() is a literal pass stub even though three real breakthroughs with real attribute bonuses already sit in the registry, earned but never applied. The author wants this stub actually finished so the bonuses take effect.

## Scope
- Implement BreakthroughService.apply_bonuses() so apply_bonuses({'iron_will'}, base_attributes) returns spirit+2/wisdom+2 matching the REGISTRY, correctly summing bonuses when multiple breakthrough_ids are passed
- Ensure empty/unknown breakthrough ids return unchanged attributes with no raise
- Wire active_breakthroughs into the effective-stats recompute path (apply.py -> rpg_depth.py -> leveling.py's SkillScalingService.get_effective_stats) so an entity with populated active_breakthroughs shows the bonus in recomputed combat stats, not just isolated calls
- Decide a concrete typed signature for apply_bonuses (bonus-delta dict vs new AttributeComponent), following leveling.py:143-149's existing trait pattern
- Decide whether fleet_foot's non-attribute evasion_flat bonus type is in scope for this pass
- Correct docs/parity_ledger/progression.yaml PROG-024 (currently claims verified/P0 with test_path=null despite the pass-stub) and add a docs/mechanics/ chapter section documenting breakthroughs

## Out of Scope
- Building a system that actually grants breakthroughs to entities in gameplay -- TCK-20260808-TRAIT-EXPRESSED-PRODUCER-INVESTIGATION already found breakthroughs_add is constructed nowhere in production code; that is a separate, larger gap

## Acceptance Criteria
- [ ] apply_bonuses({'iron_will'}, base_attributes) returns spirit+2/wisdom+2 matching REGISTRY
- [ ] apply_bonuses correctly sums bonuses when multiple breakthrough_ids are passed
- [ ] Empty/unknown id returns attributes unchanged with no raise
- [ ] After wiring active_breakthroughs into the effective-stats recompute path, an entity with populated active_breakthroughs shows the bonus in recomputed combat stats

## Related Tickets
- TCK-20260808-TRAIT-EXPRESSED-PRODUCER-INVESTIGATION

## Related Docs
- docs/parity_ledger/progression.yaml

## Related Stored Artifacts
None.

## Related Code Areas
- src/progression/breakthroughs.py
- src/engine/apply.py
- src/engine/rpg_depth.py
- src/progression/leveling.py
- src/core/state.py
- src/engine/patches.py
- src/core/updates.py

## Assumptions / Open Questions
- apply_bonuses' signature (bonus-delta dict vs new AttributeComponent) is an open decision this ticket must make concrete
- Whether fleet_foot's non-attribute evasion_flat bonus is in scope is an open decision
- layer registered as `core` — no `progression` layer exists in registries/layer_registry.jsonl; `core` was chosen because the scope centers on entity attribute/state primitives (src/core/state.py, src/core/updates.py) rather than a dedicated progression layer

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
